// Copyright AgentZet. All Rights Reserved.

#include "AssetGeneration/AgentZetAssetGenerationActions.h"
#include "AgentZetCoreModule.h"
#include "AssetImportTask.h"
#include "AssetToolsModule.h"
#include "Dom/JsonObject.h"
#include "Engine/StaticMesh.h"
#include "Factories/FbxImportUI.h"
#include "Factories/FbxStaticMeshImportData.h"
#include "HAL/FileManager.h"
#include "HAL/PlatformProcess.h"
#include "Misc/DateTime.h"
#include "Misc/FileHelper.h"
#include "Misc/PackageName.h"
#include "Misc/Paths.h"
#include "Serialization/JsonReader.h"
#include "Serialization/JsonSerializer.h"
#include "Serialization/JsonWriter.h"
#include "UObject/Package.h"
#include "UObject/SavePackage.h"

namespace AgentZetAssetGenPrivate
{
	FString ProjectRoot()
	{
		return FPaths::ConvertRelativePathToFull(FPaths::ProjectDir());
	}

	FString GenRootFor(const FString& Name)
	{
		return FPaths::Combine(ProjectRoot(),
			TEXT("SourceAssets/Spacecraft/TrellisGenerated_v001"), Name);
	}

	FString JobRootFor(const FString& Name)
	{
		return FPaths::Combine(ProjectRoot(),
			TEXT("Saved/AgentZetJobs/AssetGen"), Name);
	}

	bool IsValidAssetName(const FString& Name)
	{
		if (Name.IsEmpty() || Name.Len() > 64) return false;
		for (TCHAR C : Name)
		{
			const bool bOk = (C >= 'a' && C <= 'z') || (C >= 'A' && C <= 'Z')
				|| (C >= '0' && C <= '9') || C == '_';
			if (!bOk) return false;
		}
		return true;
	}

	/** Run a console command synchronously with captured stdout+stderr.
	 *  Same shape as FAgentZetCheckpointManager::RunGitCommand; routed
	 *  through cmd /c with 2>&1 because UE's pipe only captures stdout. */
	bool RunProcessCapture(const FString& Exe, const FString& Args,
		double TimeoutSeconds, FString& OutOutput, int32& OutExitCode)
	{
		OutOutput.Reset();
		OutExitCode = -1;

		void* ReadPipe = nullptr;
		void* WritePipe = nullptr;
		FPlatformProcess::CreatePipe(ReadPipe, WritePipe);

		// cmd /c ""exe" args 2>&1" - the doubled outer quotes are cmd's
		// own rule for commands whose first token is quoted.
		const FString CmdArgs = FString::Printf(TEXT("/c \"\"%s\" %s 2>&1\""), *Exe, *Args);
		uint32 ProcId = 0;
		FProcHandle Proc = FPlatformProcess::CreateProc(
			TEXT("cmd.exe"), *CmdArgs,
			false /*detached*/, true /*hidden*/, true /*really hidden*/,
			&ProcId, 0, nullptr, WritePipe, nullptr);
		if (!Proc.IsValid())
		{
			FPlatformProcess::ClosePipe(ReadPipe, WritePipe);
			OutOutput = TEXT("Failed to launch process.");
			return false;
		}

		const double Start = FPlatformTime::Seconds();
		bool bTimedOut = false;
		while (FPlatformProcess::IsProcRunning(Proc))
		{
			OutOutput += FPlatformProcess::ReadPipe(ReadPipe);
			if (FPlatformTime::Seconds() - Start > TimeoutSeconds)
			{
				bTimedOut = true;
				FPlatformProcess::TerminateProc(Proc, true);
				break;
			}
			FPlatformProcess::Sleep(0.1f);
		}
		OutOutput += FPlatformProcess::ReadPipe(ReadPipe);
		if (!bTimedOut)
		{
			FPlatformProcess::GetProcReturnCode(Proc, &OutExitCode);
		}
		FPlatformProcess::CloseProc(Proc);
		FPlatformProcess::ClosePipe(ReadPipe, WritePipe);
		return !bTimedOut;
	}

	FString Tail(const FString& Text, int32 MaxChars)
	{
		return Text.Len() <= MaxChars ? Text : Text.Right(MaxChars);
	}
}

FAgentZetAssetGenerationActions::FAgentZetAssetGenerationActions() {}
FAgentZetAssetGenerationActions::~FAgentZetAssetGenerationActions() {}
FName FAgentZetAssetGenerationActions::GetActionName() const { return FName(TEXT("AssetGeneration")); }
FText FAgentZetAssetGenerationActions::GetDisplayName() const { return FText::FromString(TEXT("Asset Generation (TRELLIS)")); }
EAgentZetActionCategory FAgentZetAssetGenerationActions::GetCategory() const { return EAgentZetActionCategory::Mesh; }
EAgentZetRiskLevel FAgentZetAssetGenerationActions::GetDefaultRiskLevel() const { return EAgentZetRiskLevel::Low; }
bool FAgentZetAssetGenerationActions::CanUndo() const { return false; }
bool FAgentZetAssetGenerationActions::UndoAction() { return false; }

TArray<FString> FAgentZetAssetGenerationActions::GetSupportedToolNames() const
{
	// These three names must stay in exact sync with
	// Resources/ToolSchemas/asset_generation_tools.json, EssentialToolNames
	// and GetCategoryPatternMap - a mismatch fails SILENTLY (Issue #20).
	return {
		TEXT("generate_3d_asset"),
		TEXT("check_asset_job"),
		TEXT("import_generated_asset")
	};
}

bool FAgentZetAssetGenerationActions::ValidateParams(const TSharedRef<FJsonObject>& Params, TArray<FString>& OutErrors) const
{
	return true; // ExecuteAction reports precise errors itself.
}

FAgentZetActionPlan FAgentZetAssetGenerationActions::PreviewAction(const TSharedRef<FJsonObject>& Params)
{
	FAgentZetActionPlan Plan;
	Plan.Summary = TEXT("TRELLIS 3D asset generation / import");
	FAgentZetAction Action;
	Action.Description = Plan.Summary;
	Action.Category = EAgentZetActionCategory::Mesh;
	Action.RiskLevel = EAgentZetRiskLevel::Low;
	Plan.Actions.Add(Action);
	return Plan;
}

FAgentZetActionResult FAgentZetAssetGenerationActions::ExecuteAction(const TSharedRef<FJsonObject>& Params)
{
	FString ToolName;
	Params->TryGetStringField(TEXT("_tool_name"), ToolName);
	if (ToolName == TEXT("generate_3d_asset")) return ExecuteGenerate(Params);
	if (ToolName == TEXT("check_asset_job"))   return ExecuteCheckJob(Params);
	if (ToolName == TEXT("import_generated_asset")) return ExecuteImport(Params);

	FAgentZetActionResult Result;
	Result.bSuccess = false;
	Result.Errors.Add(FString::Printf(TEXT("Unknown asset-generation tool '%s'."), *ToolName));
	return Result;
}

// ---------------------------------------------------------------------------
// generate_3d_asset - detached launch of the TRELLIS lane script
// ---------------------------------------------------------------------------
FAgentZetActionResult FAgentZetAssetGenerationActions::ExecuteGenerate(const TSharedRef<FJsonObject>& Params)
{
	using namespace AgentZetAssetGenPrivate;
	FAgentZetActionResult Result;
	Result.bSuccess = false;

	FString ImagePath, AssetName;
	Params->TryGetStringField(TEXT("image_path"), ImagePath);
	Params->TryGetStringField(TEXT("asset_name"), AssetName);
	int32 Resolution = 512;
	Params->TryGetNumberField(TEXT("resolution"), Resolution);

	if (!IsValidAssetName(AssetName))
	{
		Result.Errors.Add(TEXT("asset_name must be 1-64 chars of letters, digits and underscores only."));
		return Result;
	}
	if (Resolution != 512 && Resolution != 1024)
	{
		Result.Errors.Add(TEXT("resolution must be 512 (fast, ~60s) or 1024 (final quality, ~5 min)."));
		return Result;
	}
	ImagePath = FPaths::ConvertRelativePathToFull(ImagePath);
	if (!FPaths::FileExists(ImagePath))
	{
		Result.Errors.Add(FString::Printf(TEXT("Reference image not found: %s"), *ImagePath));
		return Result;
	}

	// v002: v001 dies under redirected stderr (PS 5.1 NativeCommandError
	// + ErrorActionPreference Stop) - discovered on this tool's first
	// unattended launch; see the v002 header.
	const FString LaneScript = FPaths::Combine(ProjectRoot(), TEXT("Scripts/trellis_generate_v002.ps1"));
	if (!FPaths::FileExists(LaneScript))
	{
		Result.Errors.Add(TEXT("TRELLIS lane script Scripts/trellis_generate_v002.ps1 is missing."));
		return Result;
	}
	const FString CliExe = FPaths::Combine(
		FPlatformMisc::GetEnvironmentVariable(TEXT("LOCALAPPDATA")),
		TEXT("trellis-studio/runtime/trellis-cli.exe"));
	if (!FPaths::FileExists(CliExe))
	{
		Result.Errors.Add(TEXT("trellis-cli.exe is not installed (expected under %LOCALAPPDATA%\\trellis-studio\\runtime). Install TRELLIS Studio first - this cannot be worked around from here."));
		return Result;
	}

	// Refuse an already-generated name - same fail-closed rule as the lane.
	const FString ExpectedGlb = FPaths::Combine(GenRootFor(AssetName), AssetName + TEXT(".glb"));
	if (FPaths::FileExists(ExpectedGlb))
	{
		Result.Errors.Add(FString::Printf(
			TEXT("An asset named '%s' was already generated (%s). Pick a NEW asset_name - this lane refuses silent replacement."),
			*AssetName, *ExpectedGlb));
		return Result;
	}

	// One generation at a time: the CLI hard-requires the GPU the editor
	// shares. A second concurrent job would starve both.
	const FString JobsRoot = FPaths::Combine(ProjectRoot(), TEXT("Saved/AgentZetJobs/AssetGen"));
	TArray<FString> ExistingJobs;
	IFileManager::Get().FindFiles(ExistingJobs, *FPaths::Combine(JobsRoot, TEXT("*")), false, true);
	for (const FString& JobName : ExistingJobs)
	{
		FString JobJson;
		if (!FFileHelper::LoadFileToString(JobJson, *FPaths::Combine(JobsRoot, JobName, TEXT("job.json")))) continue;
		TSharedPtr<FJsonObject> Job;
		TSharedRef<TJsonReader<>> Reader = TJsonReaderFactory<>::Create(JobJson);
		if (!FJsonSerializer::Deserialize(Reader, Job) || !Job.IsValid()) continue;
		int32 Pid = 0;
		Job->TryGetNumberField(TEXT("pid"), Pid);
		const FString OtherManifest = FPaths::Combine(GenRootFor(JobName), JobName + TEXT(".manifest.json"));
		if (Pid > 0 && !FPaths::FileExists(OtherManifest) && FPlatformProcess::IsApplicationRunning((uint32)Pid))
		{
			Result.Errors.Add(FString::Printf(
				TEXT("A generation job ('%s') is already running - only one runs at a time (shared GPU). Call check_asset_job with asset_name '%s' and wait for it to finish."),
				*JobName, *JobName));
			return Result;
		}
	}

	const FString JobDir = JobRootFor(AssetName);
	IFileManager::Get().MakeDirectory(*JobDir, true);
	const FString RunLog = FPaths::Combine(JobDir, TEXT("run.log"));

	// Detached PowerShell running the lane, all streams into run.log.
	const FString PsExe = TEXT("C:/Windows/System32/WindowsPowerShell/v1.0/powershell.exe");
	const FString PsArgs = FString::Printf(
		TEXT("-NoProfile -ExecutionPolicy Bypass -Command \"& { & '%s' -Image '%s' -Name '%s' -Res %d *> '%s' }\""),
		*LaneScript, *ImagePath, *AssetName, Resolution, *RunLog);
	uint32 ProcId = 0;
	FProcHandle Proc = FPlatformProcess::CreateProc(
		*PsExe, *PsArgs, true /*detached*/, true /*hidden*/, true, &ProcId, 0, nullptr, nullptr, nullptr);
	if (!Proc.IsValid())
	{
		Result.Errors.Add(TEXT("Failed to launch the TRELLIS generation process."));
		return Result;
	}
	FPlatformProcess::CloseProc(Proc);

	// Job record on disk - the executor object does not outlive the panel.
	TSharedRef<FJsonObject> Job = MakeShared<FJsonObject>();
	Job->SetNumberField(TEXT("pid"), (double)ProcId);
	Job->SetStringField(TEXT("image"), ImagePath);
	Job->SetNumberField(TEXT("res"), (double)Resolution);
	Job->SetStringField(TEXT("startedUtc"), FDateTime::UtcNow().ToIso8601());
	FString JobText;
	TSharedRef<TJsonWriter<>> Writer = TJsonWriterFactory<>::Create(&JobText);
	FJsonSerializer::Serialize(Job, Writer);
	FFileHelper::SaveStringToFile(JobText, *FPaths::Combine(JobDir, TEXT("job.json")));

	Result.bSuccess = true;
	Result.ResultMessage = FString::Printf(
		TEXT("TRELLIS generation STARTED for '%s' (res %d, pid %u). It runs in the background and typically takes %s. Call check_asset_job with asset_name '%s' to wait for the result - do NOT assume it succeeded until that reports DONE."),
		*AssetName, Resolution, ProcId,
		Resolution == 512 ? TEXT("about 60 seconds") : TEXT("about 5 minutes"),
		*AssetName);
	Result.ModifiedPaths.Add(RunLog);
	return Result;
}

// ---------------------------------------------------------------------------
// check_asset_job - poll the on-disk job state (bounded in-tool wait)
// ---------------------------------------------------------------------------
FAgentZetActionResult FAgentZetAssetGenerationActions::ExecuteCheckJob(const TSharedRef<FJsonObject>& Params)
{
	using namespace AgentZetAssetGenPrivate;
	FAgentZetActionResult Result;
	Result.bSuccess = false;

	FString AssetName;
	Params->TryGetStringField(TEXT("asset_name"), AssetName);
	if (!IsValidAssetName(AssetName))
	{
		Result.Errors.Add(TEXT("asset_name must be 1-64 chars of letters, digits and underscores only."));
		return Result;
	}

	const FString JobDir = JobRootFor(AssetName);
	const FString JobJsonPath = FPaths::Combine(JobDir, TEXT("job.json"));
	const FString ManifestPath = FPaths::Combine(GenRootFor(AssetName), AssetName + TEXT(".manifest.json"));

	FString JobText;
	if (!FFileHelper::LoadFileToString(JobText, *JobJsonPath))
	{
		// NO JOB RECORD IS NOT THE SAME AS NO ASSET. Generation also runs
		// outside the agent (Scripts/trellis_generate_v002.ps1 is the
		// faster route: polling costs an inference turn, and inference
		// starves the generator on a shared GPU). Those assets have a
		// manifest but no job.json, and telling the model to "generate
		// first" would send it to redo finished work - it did exactly
		// that on 2026-08-31 and stalled. Report the asset as ready.
		if (FPaths::FileExists(ManifestPath))
		{
			Result.bSuccess = true;
			Result.ResultMessage = FString::Printf(
				TEXT("Asset '%s' is already generated and ready (produced outside this session, manifest: %s). There is nothing to wait for - go straight to import_generated_asset."),
				*AssetName, *ManifestPath);
			return Result;
		}
		Result.Errors.Add(FString::Printf(
			TEXT("No generation job and no generated asset exist for '%s'. Call generate_3d_asset first."), *AssetName));
		return Result;
	}
	TSharedPtr<FJsonObject> Job;
	TSharedRef<TJsonReader<>> Reader = TJsonReaderFactory<>::Create(JobText);
	FJsonSerializer::Deserialize(Reader, Job);
	int32 Pid = 0;
	FString StartedUtc;
	if (Job.IsValid())
	{
		Job->TryGetNumberField(TEXT("pid"), Pid);
		Job->TryGetStringField(TEXT("startedUtc"), StartedUtc);
	}

	// NON-BLOCKING BY CONSTRUCTION (2026-08-31). This tool previously
	// waited up to 15 s in-tool to save agentic iterations, sleeping on
	// the GAME THREAD - tool execution is synchronous, so that sleep
	// stops the editor ticking entirely. Eval step8b froze the editor
	// mid-poll (frame counter stuck, no further inference request) and
	// had to be killed. A tool must never sleep here: read the state,
	// answer, return. The model polls a few extra times, which costs
	// seconds of inference instead of risking a dead editor.

	if (FPaths::FileExists(ManifestPath))
	{
		FString ManifestText;
		FFileHelper::LoadFileToString(ManifestText, *ManifestPath);
		TSharedPtr<FJsonObject> Manifest;
		TSharedRef<TJsonReader<>> MReader = TJsonReaderFactory<>::Create(ManifestText);
		FJsonSerializer::Deserialize(MReader, Manifest);
		FString OutGlb, Sha;
		double Bytes = 0, Seconds = 0;
		if (Manifest.IsValid())
		{
			Manifest->TryGetStringField(TEXT("outputGlb"), OutGlb);
			Manifest->TryGetStringField(TEXT("outputSha256"), Sha);
			Manifest->TryGetNumberField(TEXT("outputBytes"), Bytes);
			Manifest->TryGetNumberField(TEXT("seconds"), Seconds);
		}
		Result.bSuccess = true;
		Result.ResultMessage = FString::Printf(
			TEXT("Generation DONE for '%s' in %.0fs: %s (%.1f MB, sha256 %s). Manifest: %s. Next step: import_generated_asset with asset_name '%s', a destination_path under /Game, and the real-world target_size_cm."),
			*AssetName, Seconds, *OutGlb, Bytes / (1024.0 * 1024.0),
			*Sha.Left(12), *ManifestPath, *AssetName);
		Result.ModifiedPaths.Add(OutGlb);
		return Result;
	}

	if (Pid > 0 && FPlatformProcess::IsApplicationRunning((uint32)Pid))
	{
		FDateTime Started;
		FDateTime::ParseIso8601(*StartedUtc, Started);
		const double Elapsed = (FDateTime::UtcNow() - Started).GetTotalSeconds();
		Result.bSuccess = true;
		Result.ResultMessage = FString::Printf(
			TEXT("Job '%s' is STILL RUNNING (%.0fs elapsed; res 512 typically ~60s, res 1024 ~300s). Call check_asset_job again to keep waiting."),
			*AssetName, Elapsed);
		return Result;
	}

	FString RunLog;
	FFileHelper::LoadFileToString(RunLog, *FPaths::Combine(JobDir, TEXT("run.log")));
	Result.Errors.Add(FString::Printf(
		TEXT("Generation FAILED for '%s' - the process ended without producing a manifest. Log tail:\n%s"),
		*AssetName, *Tail(RunLog, 1200)));
	return Result;
}

// ---------------------------------------------------------------------------
// import_generated_asset - Blender prepare + FBX import + verify + receipt
// ---------------------------------------------------------------------------
FAgentZetActionResult FAgentZetAssetGenerationActions::ExecuteImport(const TSharedRef<FJsonObject>& Params)
{
	using namespace AgentZetAssetGenPrivate;
	FAgentZetActionResult Result;
	Result.bSuccess = false;

	FString AssetName, DestinationPath = TEXT("/Game/Spacecraft/Props"), Axis = TEXT("longest");
	double TargetCm = 0.0;
	Params->TryGetStringField(TEXT("asset_name"), AssetName);
	Params->TryGetStringField(TEXT("destination_path"), DestinationPath);
	Params->TryGetStringField(TEXT("defining_axis"), Axis);
	Params->TryGetNumberField(TEXT("target_size_cm"), TargetCm);
	Axis = Axis.ToLower();

	if (!IsValidAssetName(AssetName))
	{
		Result.Errors.Add(TEXT("asset_name must be 1-64 chars of letters, digits and underscores only."));
		return Result;
	}
	if (TargetCm < 1.0 || TargetCm > 100000.0)
	{
		Result.Errors.Add(TEXT("target_size_cm is required: the asset's real-world size in centimetres on the defining axis (1 to 100000)."));
		return Result;
	}
	if (Axis != TEXT("x") && Axis != TEXT("y") && Axis != TEXT("z") && Axis != TEXT("longest"))
	{
		Result.Errors.Add(TEXT("defining_axis must be x, y, z or longest."));
		return Result;
	}
	if (!DestinationPath.StartsWith(TEXT("/Game/")))
	{
		Result.Errors.Add(TEXT("destination_path must start with /Game/."));
		return Result;
	}
	// The game code still carries name-based provenance guards that
	// SILENTLY reject assets under these names (see
	// Docs/MESHY_PROVENANCE_REVERSAL_PLAN_v001.md) - refuse loudly here
	// instead of letting the factory quietly never commission.
	for (const TCHAR* Banned : { TEXT("Meshy"), TEXT("ExternalGenerated"), TEXT("OriginalHighPoly") })
	{
		if (DestinationPath.Contains(Banned))
		{
			Result.Errors.Add(FString::Printf(
				TEXT("destination_path must not contain '%s' - runtime provenance guards silently reject assets under that name. Use a neutral path like /Game/Spacecraft/Props."), Banned));
			return Result;
		}
	}

	const FString Glb = FPaths::Combine(GenRootFor(AssetName), AssetName + TEXT(".glb"));
	if (!FPaths::FileExists(Glb))
	{
		Result.Errors.Add(FString::Printf(
			TEXT("No generated GLB for '%s' (expected %s). Run generate_3d_asset and wait for check_asset_job to report DONE first."),
			*AssetName, *Glb));
		return Result;
	}

	const FString BlenderExe = TEXT("C:/Program Files/Blender Foundation/Blender 5.2/blender.exe");
	if (!FPaths::FileExists(BlenderExe))
	{
		Result.Errors.Add(TEXT("Blender 5.2 not found at the project's standard path - the scale-bake step cannot run."));
		return Result;
	}
	const FString PrepScript = FPaths::Combine(ProjectRoot(), TEXT("Tools/trellis_prepare_import_v001.py"));
	if (!FPaths::FileExists(PrepScript))
	{
		Result.Errors.Add(TEXT("Tools/trellis_prepare_import_v001.py is missing."));
		return Result;
	}

	// 1) Blender: join + scale + ground + FBX. SYNCHRONOUS on the game
	//    thread: the editor is unresponsive for the duration (typically
	//    10-30 s, hard cap 120 s). Accepted here because import is a
	//    single bounded step the user is waiting on anyway - unlike
	//    generation, which is minutes long and therefore detached.
	const FString StageDir = FPaths::Combine(JobRootFor(AssetName), TEXT("Import"));
	IFileManager::Get().MakeDirectory(*StageDir, true);
	const FString BlenderArgs = FString::Printf(
		TEXT("-b --disable-autoexec -P \"%s\" -- \"%s\" \"%s\" %s %s %.1f"),
		*PrepScript, *Glb, *StageDir, *AssetName, *Axis, TargetCm);
	FString BlenderOut;
	int32 BlenderExit = -1;
	const bool bFinished = RunProcessCapture(BlenderExe, BlenderArgs, 120.0, BlenderOut, BlenderExit);
	FFileHelper::SaveStringToFile(BlenderOut, *FPaths::Combine(StageDir, TEXT("blender.log")));
	if (!bFinished || BlenderExit != 0 || !BlenderOut.Contains(TEXT("EXPORT_OK")))
	{
		Result.Errors.Add(FString::Printf(
			TEXT("Blender prepare step FAILED (exit %d%s). Log tail:\n%s"),
			BlenderExit, bFinished ? TEXT("") : TEXT(", timed out"), *Tail(BlenderOut, 1200)));
		return Result;
	}

	const FString Fbx = FPaths::Combine(StageDir, AssetName + TEXT(".fbx"));
	if (!FPaths::FileExists(Fbx))
	{
		Result.Errors.Add(TEXT("Blender reported EXPORT_OK but the FBX is missing - refusing to continue."));
		return Result;
	}

	// 2) Import (combine meshes; no auto collision; no lightmap UVs -
	//    matching the proven import_ground_drones_v001.py settings).
	UFbxImportUI* ImportUI = NewObject<UFbxImportUI>();
	ImportUI->MeshTypeToImport = FBXIT_StaticMesh;
	ImportUI->bAutomatedImportShouldDetectType = false;
	ImportUI->bImportMaterials = true;
	ImportUI->bImportTextures = true;
	ImportUI->bImportAnimations = false;
	ImportUI->StaticMeshImportData->bCombineMeshes = true;
	ImportUI->StaticMeshImportData->bAutoGenerateCollision = false;
	ImportUI->StaticMeshImportData->bGenerateLightmapUVs = false;
	ImportUI->StaticMeshImportData->ImportUniformScale = 1.0f;

	UAssetImportTask* Task = NewObject<UAssetImportTask>();
	Task->Filename = Fbx;
	Task->DestinationPath = DestinationPath;
	Task->bAutomated = true;
	Task->bReplaceExisting = true;
	Task->bSave = true;
	Task->Options = ImportUI;

	IAssetTools& AssetTools = FModuleManager::LoadModuleChecked<FAssetToolsModule>("AssetTools").Get();
	AssetTools.ImportAssetTasks({ Task });

	UStaticMesh* Mesh = nullptr;
	for (const FString& Imported : Task->ImportedObjectPaths)
	{
		Result.ModifiedAssets.Add(Imported);
		if (!Mesh)
		{
			Mesh = LoadObject<UStaticMesh>(nullptr, *Imported);
		}
	}
	if (!Mesh)
	{
		Result.Errors.Add(TEXT("Import produced no StaticMesh - the FBX may be empty or the importer rejected it. Nothing was verified."));
		return Result;
	}

	// 3) Nanite on (project standard for high-poly generated props), then
	//    measure the DEFINING AXIS against the declared size, +/-3%.
	const bool bNaniteWasOn = Mesh->GetNaniteSettings().bEnabled;
	if (!bNaniteWasOn)
	{
		FMeshNaniteSettings Nanite = Mesh->GetNaniteSettings();
		Nanite.bEnabled = true;
		Mesh->SetNaniteSettings(Nanite);
		Mesh->PostEditChange();
		Mesh->MarkPackageDirty();
	}

	const FVector SizeCm = Mesh->GetBoundingBox().GetSize();
	double Measured = 0.0;
	if (Axis == TEXT("x")) Measured = SizeCm.X;
	else if (Axis == TEXT("y")) Measured = SizeCm.Y;
	else if (Axis == TEXT("z")) Measured = SizeCm.Z;
	else Measured = FMath::Max3(SizeCm.X, SizeCm.Y, SizeCm.Z);
	const double Deviation = FMath::Abs(Measured - TargetCm) / TargetCm;
	const bool bSizeOk = Deviation <= 0.03;

	int32 FallbackTris = 0;
	if (Mesh->GetRenderData() && Mesh->GetRenderData()->LODResources.Num() > 0)
	{
		FallbackTris = Mesh->GetRenderData()->LODResources[0].GetNumTriangles();
	}

	// Save the (possibly Nanite-toggled) mesh package.
	UPackage* Package = Mesh->GetOutermost();
	const FString PackageFile = FPackageName::LongPackageNameToFilename(
		Package->GetName(), FPackageName::GetAssetPackageExtension());
	FSavePackageArgs SaveArgs;
	SaveArgs.TopLevelFlags = RF_Public | RF_Standalone;
	UPackage::SavePackage(Package, Mesh, *PackageFile, SaveArgs);

	// 4) Audit receipt - versioned, never overwritten (repo convention).
	const FString AuditDir = FPaths::Combine(ProjectRoot(), TEXT("Saved/Audits/Spacecraft"));
	IFileManager::Get().MakeDirectory(*AuditDir, true);
	FString ReceiptPath;
	for (int32 V = 1; V < 1000; ++V)
	{
		ReceiptPath = FPaths::Combine(AuditDir,
			FString::Printf(TEXT("agentzet_import_%s_v%03d.json"), *AssetName, V));
		if (!FPaths::FileExists(ReceiptPath)) break;
	}
	TSharedRef<FJsonObject> Receipt = MakeShared<FJsonObject>();
	Receipt->SetStringField(TEXT("$schema"), TEXT("lineboss/audit/agentzet-trellis-import/v1"));
	Receipt->SetStringField(TEXT("status"), bSizeOk
		? TEXT("PASS__IMPORT_VERIFIED") : TEXT("FAIL_CLOSED__SIZE_MISMATCH"));
	Receipt->SetStringField(TEXT("asset"), AssetName);
	Receipt->SetStringField(TEXT("sourceGlb"), Glb);
	Receipt->SetStringField(TEXT("fbx"), Fbx);
	Receipt->SetStringField(TEXT("destination"), DestinationPath);
	Receipt->SetStringField(TEXT("definingAxis"), Axis);
	Receipt->SetNumberField(TEXT("declaredCm"), TargetCm);
	Receipt->SetNumberField(TEXT("measuredCm"), Measured);
	Receipt->SetNumberField(TEXT("boundsX"), SizeCm.X);
	Receipt->SetNumberField(TEXT("boundsY"), SizeCm.Y);
	Receipt->SetNumberField(TEXT("boundsZ"), SizeCm.Z);
	Receipt->SetBoolField(TEXT("naniteEnabled"), Mesh->GetNaniteSettings().bEnabled);
	Receipt->SetNumberField(TEXT("fallbackTriangles"), FallbackTris);
	Receipt->SetStringField(TEXT("utc"), FDateTime::UtcNow().ToIso8601());
	FString ReceiptText;
	TSharedRef<TJsonWriter<>> RWriter = TJsonWriterFactory<>::Create(&ReceiptText);
	FJsonSerializer::Serialize(Receipt, RWriter);
	FFileHelper::SaveStringToFile(ReceiptText, *ReceiptPath);
	Result.ModifiedPaths.Add(ReceiptPath);

	if (!bSizeOk)
	{
		Result.Errors.Add(FString::Printf(
			TEXT("Imported, but SIZE VERIFICATION FAILED: %s axis measures %.1f cm vs declared %.1f cm (%.1f%% off, tolerance 3%%). The asset exists but must not be used until this is resolved. Receipt: %s"),
			*Axis, Measured, TargetCm, Deviation * 100.0, *ReceiptPath));
		return Result;
	}

	Result.bSuccess = true;
	Result.ResultMessage = FString::Printf(
		TEXT("Imported and VERIFIED '%s' -> %s. Size on %s axis: %.1f cm (declared %.1f, within 3%%). Bounds %.0fx%.0fx%.0f cm. Nanite: %s (fallback %d tris). Receipt: %s"),
		*AssetName, *Mesh->GetPathName(), *Axis, Measured, TargetCm,
		SizeCm.X, SizeCm.Y, SizeCm.Z,
		Mesh->GetNaniteSettings().bEnabled ? TEXT("ON") : TEXT("OFF"),
		FallbackTris, *ReceiptPath);
	return Result;
}
