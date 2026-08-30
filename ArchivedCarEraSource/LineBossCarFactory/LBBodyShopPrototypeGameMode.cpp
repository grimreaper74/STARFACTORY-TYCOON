#include "LBBodyShopPrototypeGameMode.h"

#include "Camera/CameraComponent.h"
#include "Components/PrimitiveComponent.h"
#include "Components/StaticMeshComponent.h"
#include "Dom/JsonObject.h"
#include "Engine/Engine.h"
#include "Engine/GameViewportClient.h"
#include "Engine/LocalPlayer.h"
#include "Engine/StaticMesh.h"
#include "Engine/World.h"
#include "EngineUtils.h"
#include "GameFramework/PlayerController.h"
#include "HAL/FileManager.h"
#include "HAL/IConsoleManager.h"
#include "HAL/PlatformMisc.h"
#include "LBBodyShopCellActor.h"
#include "LBBodyShopServiceDressingActor.h"
#include "LBBodyShopManagementPawn.h"
#include "LBBodyShopExperimentalSaveGame.h"
#include "LBBodyShopPrototypeHUD.h"
#include "LBBodyShopPrototypeRuntime.h"
#include "LBBodyShopPrototypeWorldBootstrap.h"
#include "LBBodyShopRobotActor.h"
#include "Misc/App.h"
#include "Misc/CommandLine.h"
#include "Misc/FileHelper.h"
#include "Misc/OutputDeviceRedirector.h"
#include "Misc/Parse.h"
#include "Misc/Paths.h"
#include "PrimitiveSceneProxy.h"
#include "SceneView.h"
#include "Serialization/JsonSerializer.h"
#include "Serialization/JsonWriter.h"
#include "StaticMeshResources.h"
#include "UnrealClient.h"

namespace LBBodyShopPrototypeGameModePrivate
{
    constexpr float PackagedValidationTimeoutSeconds = 20.0f;
    constexpr float PackagedPerformanceTimeoutSeconds = 120.0f;
    constexpr int32 PackagedPerformanceWarmupFrames = 120;
    constexpr int32 PackagedPerformanceCaptureFrames = 300;
    constexpr int32 PackagedPerformanceFinaliseMarginFrames = 90;
    constexpr int32 PackagedPerformanceFileStableFrames = 30;
    constexpr int32 ExpectedPerformanceRobotCount = 3;
    constexpr int32 ExpectedPerformanceTargetComponentCount = 25;
    constexpr int32 ExpectedPerformanceUniqueMeshCount = 10;
    constexpr int32 ExpectedPerformanceViewportWidth = 1920;
    constexpr int32 ExpectedPerformanceViewportHeight = 1080;

    FName GetServiceDressingActorName()
    {
        static const FName ActorName(TEXT("LB_BodyShop_ServiceDressing_v002"));
        return ActorName;
    }

    ALBBodyShopServiceDressingActor* TrySpawnServiceDressing(
        UWorld* World, AActor* Owner, FString& OutReason)
    {
        OutReason.Reset();
        if (!World || !IsValid(Owner) || Owner->IsActorBeingDestroyed()
            || Owner->GetWorld() != World)
        {
            OutReason = TEXT(
                "BODY SHOP SERVICE DRESSING REQUIRES A VALID SAME-WORLD OWNER");
            return nullptr;
        }

        FActorSpawnParameters SpawnParameters;
        SpawnParameters.Owner = Owner;
        SpawnParameters.Name = GetServiceDressingActorName();
        SpawnParameters.NameMode =
            FActorSpawnParameters::ESpawnActorNameMode::Required_ReturnNull;
        SpawnParameters.ObjectFlags |= RF_Transient;
        SpawnParameters.SpawnCollisionHandlingOverride =
            ESpawnActorCollisionHandlingMethod::AlwaysSpawn;
        ALBBodyShopServiceDressingActor* Dressing =
            World->SpawnActor<ALBBodyShopServiceDressingActor>(
                ALBBodyShopServiceDressingActor::StaticClass(), FTransform::Identity,
                SpawnParameters);
        if (!IsValid(Dressing) || Dressing->IsActorBeingDestroyed())
        {
            OutReason = TEXT("BODY SHOP SERVICE DRESSING V002 SPAWN FAILED");
            return nullptr;
        }

        const auto RejectDressing = [&OutReason](ALBBodyShopServiceDressingActor* Actor,
            const FString& Reason) -> ALBBodyShopServiceDressingActor*
        {
            OutReason = Reason;
            if (IsValid(Actor) && !Actor->IsActorBeingDestroyed()) Actor->Destroy();
            return nullptr;
        };

        if (Dressing->GetFName() != GetServiceDressingActorName()
            || Dressing->GetOwner() != Owner
            || !Dressing->GetActorTransform().Equals(FTransform::Identity)
            || !Dressing->HasAnyFlags(RF_Transient)
            || Dressing->RepresentsProcessWIP())
        {
            return RejectDressing(Dressing,
                TEXT("BODY SHOP SERVICE DRESSING V002 SPAWN CONTRACT FAILED"));
        }
        if (!Dressing->ActivatePresentation())
        {
            FString ActivationReason = Dressing->GetPresentationContractFailureReason();
            if (ActivationReason.IsEmpty())
            {
                ActivationReason = TEXT(
                    "BODY SHOP SERVICE DRESSING V002 PRESENTATION FAILED");
            }
            return RejectDressing(Dressing, ActivationReason);
        }
        if (!Dressing->IsPresentationActive()
            || !Dressing->HasValidPresentationContract()
            || Dressing->GetVisibleInstanceCount() != 12
            || Dressing->RepresentsProcessWIP())
        {
            return RejectDressing(Dressing,
                TEXT("BODY SHOP SERVICE DRESSING V002 ACTIVATION CONTRACT FAILED"));
        }
        return Dressing;
    }

    const TSet<FName>& ExpectedPerformanceSlots()
    {
        static const TSet<FName> Slots = {
            TEXT("ROBOT_HND_01"), TEXT("ROBOT_WELD_LEFT"), TEXT("ROBOT_WELD_RIGHT")
        };
        return Slots;
    }

    const TSet<FName>& ExpectedRobotPresentationComponents()
    {
        static const TSet<FName> Components = {
            TEXT("BasePresentation"), TEXT("J1Presentation"), TEXT("J2Presentation"),
            TEXT("J3Presentation"), TEXT("J4Presentation"), TEXT("J5Presentation"),
            TEXT("J6Presentation"), TEXT("ToolPresentation")
        };
        return Components;
    }

    const TSet<FString>& ExpectedPerformanceMeshes()
    {
        static const TSet<FString> Meshes = {
            TEXT("/Game/LineBoss/Candidates/WeldShop/BodyShopRobotNative_v001/Robot/SM_LB_BodyShopRobotNative_Base_v001.SM_LB_BodyShopRobotNative_Base_v001"),
            TEXT("/Game/LineBoss/Candidates/WeldShop/BodyShopRobotNative_v001/Robot/SM_LB_BodyShopRobotNative_J1_v001.SM_LB_BodyShopRobotNative_J1_v001"),
            TEXT("/Game/LineBoss/Candidates/WeldShop/BodyShopRobotNative_v001/Robot/SM_LB_BodyShopRobotNative_J2_v001.SM_LB_BodyShopRobotNative_J2_v001"),
            TEXT("/Game/LineBoss/Candidates/WeldShop/BodyShopRobotNative_v001/Robot/SM_LB_BodyShopRobotNative_J3_v001.SM_LB_BodyShopRobotNative_J3_v001"),
            TEXT("/Game/LineBoss/Candidates/WeldShop/BodyShopRobotNative_v001/Robot/SM_LB_BodyShopRobotNative_J4_v001.SM_LB_BodyShopRobotNative_J4_v001"),
            TEXT("/Game/LineBoss/Candidates/WeldShop/BodyShopRobotNative_v001/Robot/SM_LB_BodyShopRobotNative_J5_v001.SM_LB_BodyShopRobotNative_J5_v001"),
            TEXT("/Game/LineBoss/Candidates/WeldShop/BodyShopRobotNative_v001/Robot/SM_LB_BodyShopRobotNative_J6_v001.SM_LB_BodyShopRobotNative_J6_v001"),
            TEXT("/Game/LineBoss/Candidates/WeldShop/BodyShopUnderbodySlice_v001/Tools/SM_LB_BodyShopTool_PanelPick8Cup_v001.SM_LB_BodyShopTool_PanelPick8Cup_v001"),
            TEXT("/Game/LineBoss/Candidates/WeldShop/BodyShopRobotNative_v001/Tools/SM_LB_BodyShopToolNative_OpenCGun_v001.SM_LB_BodyShopToolNative_OpenCGun_v001"),
            TEXT("/Game/LineBoss/Candidates/WeldShop/BodyShopUnderbodySlice_v001/Vision/SM_LB_BodyShop_VisionGate_v001.SM_LB_BodyShop_VisionGate_v001")
        };
        return Meshes;
    }

    FString PerformanceViewName(const ELBBodyShopPackagedPerformanceView View, const bool bUppercase)
    {
        FString Name;
        switch (View)
        {
        case ELBBodyShopPackagedPerformanceView::Management: Name = TEXT("management"); break;
        case ELBBodyShopPackagedPerformanceView::Focus: Name = TEXT("focus"); break;
        default: Name = TEXT("none"); break;
        }
        return bUppercase ? Name.ToUpper() : Name;
    }

    FString SanitizeMarkerToken(FString Value)
    {
        for (TCHAR& Character : Value)
        {
            if (!FChar::IsAlnum(Character) && Character != TEXT('-')
                && Character != TEXT('_') && Character != TEXT('.'))
            {
                Character = TEXT('_');
            }
        }
        return Value.Left(240);
    }

    TArray<TSharedPtr<FJsonValue>> JsonVector(const FVector& Value)
    {
        return {
            MakeShared<FJsonValueNumber>(Value.X), MakeShared<FJsonValueNumber>(Value.Y),
            MakeShared<FJsonValueNumber>(Value.Z)
        };
    }

    TSharedPtr<FJsonObject> JsonRotator(const FRotator& Value)
    {
        TSharedPtr<FJsonObject> Result = MakeShared<FJsonObject>();
        Result->SetNumberField(TEXT("pitch"), Value.Pitch);
        Result->SetNumberField(TEXT("yaw"), Value.Yaw);
        Result->SetNumberField(TEXT("roll"), Value.Roll);
        return Result;
    }

    TArray<FString> FindProfilingFiles(const FString& Pattern)
    {
        TArray<FString> Files;
        IFileManager::Get().FindFilesRecursive(Files, *FPaths::ProfilingDir(), *Pattern,
            true, false, true);
        for (FString& Path : Files)
        {
            Path = FPaths::ConvertRelativePathToFull(Path);
            FPaths::NormalizeFilename(Path);
        }
        Files.Sort();
        return Files;
    }

    ALBBodyShopManagementPawn* FindManagementPawn(UWorld* World)
    {
        if (!World) return nullptr;
        if (APlayerController* Controller = World->GetFirstPlayerController())
        {
            if (ALBBodyShopManagementPawn* Pawn = Cast<ALBBodyShopManagementPawn>(Controller->GetPawn()))
                return Pawn;
        }
        for (TActorIterator<ALBBodyShopManagementPawn> It(World); It; ++It)
        {
            if (IsValid(*It) && !It->IsActorBeingDestroyed()) return *It;
        }
        return nullptr;
    }

    bool BuildPackagedPerformanceTargetManifest(UWorld* World, const FSceneView* SceneView,
        const float MinimumLastRenderTimeOnScreen, const float SnapshotWorldTime,
        TArray<TSharedPtr<FJsonValue>>& OutTargets, TSet<FString>& OutMeshPaths,
        bool& bOutAnyForcedLOD, FString& OutReason)
    {
        // This focused renderer gate intentionally targets only the 24 robot-link/tool
        // components plus the vision gate (25 components / 10 unique meshes). Native
        // service-apron HISM props are environmental dressing and do not alter this target.
        OutTargets.Reset();
        OutMeshPaths.Reset();
        bOutAnyForcedLOD = false;
        OutReason.Reset();
        if (!World)
        {
            OutReason = TEXT("PERFORMANCE TARGET MANIFEST REQUIRES A WORLD");
            return false;
        }

        auto AddTarget = [&](AActor* Actor, UStaticMeshComponent* Component,
            const FString& Category, const FString& Identity) -> bool
        {
            if (!IsValid(Actor) || !IsValid(Component) || !IsValid(Component->GetStaticMesh()))
            {
                OutReason = FString::Printf(TEXT("PERFORMANCE TARGET IS INVALID: %s"),
                    *Identity);
                return false;
            }
            UStaticMesh* Mesh = Component->GetStaticMesh();
            const FString MeshPath = Mesh->GetPathName();
            const int32 LODCount = Mesh->GetNumLODs();
            const FStaticMeshRenderData* RenderData = Mesh->GetRenderData();
            if (LODCount < 1 || !RenderData || RenderData->LODResources.Num() != LODCount)
            {
                OutReason = FString::Printf(TEXT("PERFORMANCE TARGET HAS INVALID RUNTIME LODS: %s"),
                    *MeshPath);
                return false;
            }

            TArray<TSharedPtr<FJsonValue>> ScreenSizes;
            TArray<TSharedPtr<FJsonValue>> Sections;
            TArray<TSharedPtr<FJsonValue>> Triangles;
            TArray<TSharedPtr<FJsonValue>> Vertices;
            for (int32 LODIndex = 0; LODIndex < LODCount; ++LODIndex)
            {
                const int32 SectionCount = RenderData->LODResources[LODIndex].Sections.Num();
                const int32 TriangleCount = Mesh->GetNumTriangles(LODIndex);
                const int32 VertexCount = Mesh->GetNumVertices(LODIndex);
                if (SectionCount <= 0 || TriangleCount <= 0 || VertexCount <= 0)
                {
                    OutReason = FString::Printf(TEXT("PERFORMANCE TARGET HAS EMPTY LOD %d: %s"),
                        LODIndex, *MeshPath);
                    return false;
                }
                ScreenSizes.Add(MakeShared<FJsonValueNumber>(
                    RenderData->ScreenSize[LODIndex].GetValue()));
                Sections.Add(MakeShared<FJsonValueNumber>(SectionCount));
                Triangles.Add(MakeShared<FJsonValueNumber>(TriangleCount));
                Vertices.Add(MakeShared<FJsonValueNumber>(VertexCount));
            }

            const int32 ForcedLOD = Component->GetForcedLodModel();
            bOutAnyForcedLOD |= ForcedLOD != 0;
            OutMeshPaths.Add(MeshPath);
            TSharedPtr<FJsonObject> Record = MakeShared<FJsonObject>();
            Record->SetStringField(TEXT("key"), Identity + TEXT(":") + Component->GetName());
            Record->SetStringField(TEXT("category"), Category);
            Record->SetStringField(TEXT("identity"), Identity);
            Record->SetStringField(TEXT("actor_full_name"), Actor->GetFullName());
            Record->SetStringField(TEXT("actor_name"), Actor->GetName());
            Record->SetStringField(TEXT("component_name"), Component->GetName());
            Record->SetStringField(TEXT("mesh_path"), MeshPath);
            Record->SetNumberField(TEXT("lod_count"), LODCount);
            Record->SetArrayField(TEXT("lod_screen_sizes"), ScreenSizes);
            Record->SetArrayField(TEXT("lod_sections"), Sections);
            Record->SetArrayField(TEXT("lod_triangles"), Triangles);
            Record->SetArrayField(TEXT("lod_vertices"), Vertices);
            Record->SetStringField(TEXT("lod_metadata_source"),
                TEXT("packaged_runtime_static_mesh_render_data"));
            Record->SetNumberField(TEXT("forced_lod_model"), ForcedLOD);
            if (SceneView)
            {
                if (!Component->IsRegistered() || !Component->GetSceneProxy())
                {
                    OutReason = FString::Printf(
                        TEXT("PERFORMANCE TARGET HAS NO REGISTERED SCENE PROXY: %s"),
                        *Record->GetStringField(TEXT("key")));
                    return false;
                }
                const int32 SelectedLOD = Component->GetSceneProxy()->GetLOD(SceneView);
                if (SelectedLOD < 0 || SelectedLOD >= LODCount)
                {
                    OutReason = FString::Printf(
                        TEXT("RENDERER SELECTED INVALID LOD %d OF %d: %s"),
                        SelectedLOD, LODCount, *Record->GetStringField(TEXT("key")));
                    return false;
                }
                const float LastRenderTimeOnScreen = Component->GetLastRenderTimeOnScreen();
                const float LastRenderAge = SnapshotWorldTime - LastRenderTimeOnScreen;
                if (!FMath::IsFinite(LastRenderTimeOnScreen)
                    || !FMath::IsFinite(LastRenderAge)
                    || Component->IsAlwaysVisible()
                    || LastRenderTimeOnScreen <= 0.0f
                    || LastRenderTimeOnScreen < MinimumLastRenderTimeOnScreen
                    || LastRenderAge < -0.1f || LastRenderAge > 0.5f)
                {
                    OutReason = FString::Printf(
                        TEXT("PERFORMANCE TARGET LACKS A FRESH ON-SCREEN RENDER: %s"),
                        *Record->GetStringField(TEXT("key")));
                    return false;
                }
                Record->SetNumberField(TEXT("selected_lod"), SelectedLOD);
                Record->SetNumberField(TEXT("selected_lod_sections"),
                    RenderData->LODResources[SelectedLOD].Sections.Num());
                Record->SetNumberField(TEXT("selected_lod_triangles"),
                    Mesh->GetNumTriangles(SelectedLOD));
                Record->SetNumberField(TEXT("selected_lod_vertices"),
                    Mesh->GetNumVertices(SelectedLOD));
                Record->SetStringField(TEXT("selected_lod_source"),
                    TEXT("FPrimitiveSceneProxy::GetLOD(FSceneView)"));
                Record->SetNumberField(TEXT("last_render_time_on_screen_seconds"),
                    LastRenderTimeOnScreen);
                Record->SetNumberField(TEXT("last_render_age_seconds"), LastRenderAge);
                Record->SetNumberField(TEXT("snapshot_world_time_seconds"), SnapshotWorldTime);
                Record->SetBoolField(TEXT("rendered_since_view_configured"), true);
            }
            OutTargets.Add(MakeShared<FJsonValueObject>(Record));
            return true;
        };

        TArray<ALBBodyShopRobotActor*> Robots;
        for (TActorIterator<ALBBodyShopRobotActor> It(World); It; ++It)
        {
            if (IsValid(*It) && !It->IsActorBeingDestroyed()) Robots.Add(*It);
        }
        Robots.Sort([](const ALBBodyShopRobotActor& Left, const ALBBodyShopRobotActor& Right)
        {
            return Left.GetSlotId().ToString() < Right.GetSlotId().ToString();
        });
        if (Robots.Num() != ExpectedPerformanceRobotCount)
        {
            OutReason = FString::Printf(TEXT("EXPECTED %d PERFORMANCE ROBOTS, FOUND %d"),
                ExpectedPerformanceRobotCount, Robots.Num());
            return false;
        }

        TSet<FName> FoundSlots;
        for (ALBBodyShopRobotActor* Robot : Robots)
        {
            if (!Robot->IsConfiguredForAuthoredSlot() || !Robot->HasCompleteArtPresentation())
            {
                OutReason = TEXT("PERFORMANCE ROBOT IS NOT A COMPLETE AUTHORED-SLOT PRESENTATION");
                return false;
            }
            FoundSlots.Add(Robot->GetSlotId());
            TArray<UStaticMeshComponent*> Components;
            Robot->GetComponents<UStaticMeshComponent>(Components);
            Components.RemoveAll([](const UStaticMeshComponent* Component)
            {
                return !IsValid(Component)
                    || !ExpectedRobotPresentationComponents().Contains(Component->GetFName());
            });
            Components.Sort([](const UStaticMeshComponent& Left, const UStaticMeshComponent& Right)
            {
                return Left.GetName() < Right.GetName();
            });
            TSet<FName> FoundComponents;
            for (UStaticMeshComponent* Component : Components)
                FoundComponents.Add(Component->GetFName());
            const TSet<FName> ExpectedComponents = ExpectedRobotPresentationComponents();
            if (FoundComponents.Num() != ExpectedComponents.Num()
                || !FoundComponents.Includes(ExpectedComponents))
            {
                OutReason = FString::Printf(TEXT("ROBOT PRESENTATION COMPONENT SET DRIFTED: %s"),
                    *Robot->GetSlotId().ToString());
                return false;
            }
            for (UStaticMeshComponent* Component : Components)
            {
                const FString Category = Component->GetFName() == TEXT("ToolPresentation")
                    ? TEXT("robot_tool") : TEXT("robot_link");
                if (!AddTarget(Robot, Component, Category, Robot->GetSlotId().ToString()))
                    return false;
            }
        }
        const TSet<FName> ExpectedSlots = ExpectedPerformanceSlots();
        if (FoundSlots.Num() != ExpectedSlots.Num() || !FoundSlots.Includes(ExpectedSlots))
        {
            OutReason = TEXT("PERFORMANCE ROBOT SLOT SET DRIFTED");
            return false;
        }

        int32 UnderbodyFixtureCount = 0;
        int32 VisionCellCount = 0;
        for (TActorIterator<ALBBodyShopCellActor> It(World); It; ++It)
        {
            ALBBodyShopCellActor* Cell = *It;
            if (!IsValid(Cell) || Cell->IsActorBeingDestroyed())
                continue;
            if (Cell->GetDefinitionId() == TEXT("BW003_UNDERBODY_FIXTURE_BASIC"))
            {
                ++UnderbodyFixtureCount;
                if (!Cell->GetMainPresentationAssetPath().IsEmpty())
                {
                    OutReason = TEXT("UNDERBODY FIXTURE MAIN PRESENTATION MUST REMAIN ABSENT");
                    return false;
                }
                continue;
            }
            if (Cell->GetDefinitionId() != TEXT("BW012_VISION_GATE_BASIC")) continue;
            ++VisionCellCount;
            TArray<UStaticMeshComponent*> Components;
            Cell->GetComponents<UStaticMeshComponent>(Components);
            Components.RemoveAll([](const UStaticMeshComponent* Component)
            {
                return !IsValid(Component) || Component->GetFName() != TEXT("MainPresentation");
            });
            if (Components.Num() != 1 || !AddTarget(Cell, Components[0], TEXT("vision_gate"),
                TEXT("BW012_VISION_GATE_BASIC")))
            {
                if (OutReason.IsEmpty()) OutReason = TEXT("VISION GATE PRESENTATION CONTRACT DRIFTED");
                return false;
            }
        }
        if (UnderbodyFixtureCount != 1)
        {
            OutReason = FString::Printf(TEXT("EXPECTED ONE OPEN UNDERBODY FIXTURE, FOUND %d"),
                UnderbodyFixtureCount);
            return false;
        }
        if (VisionCellCount != 1)
        {
            OutReason = FString::Printf(TEXT("EXPECTED ONE VISION GATE, FOUND %d"), VisionCellCount);
            return false;
        }
        const TSet<FString> ExpectedMeshes = ExpectedPerformanceMeshes();
        if (OutMeshPaths.Num() != ExpectedMeshes.Num() || !OutMeshPaths.Includes(ExpectedMeshes))
        {
            OutReason = TEXT("PACKAGED ROBOT TOOL VISION MESH FAMILY DRIFTED");
            return false;
        }
        return true;
    }

    bool SnapshotPackagedPerformanceRendererLODs(UWorld* World,
        TArray<TSharedPtr<FJsonValue>>& OutTargets, TSet<FString>& OutMeshPaths,
        bool& bOutAnyForcedLOD, int32& OutViewWidth, int32& OutViewHeight,
        int32& OutGlobalForcedLOD, int32& OutRegisteredSceneProxyCount,
        const float ViewConfiguredWorldSeconds, float& OutSnapshotWorldSeconds,
        FString& OutReason)
    {
        OutTargets.Reset();
        OutMeshPaths.Reset();
        bOutAnyForcedLOD = false;
        OutViewWidth = -1;
        OutViewHeight = -1;
        OutGlobalForcedLOD = INDEX_NONE;
        OutRegisteredSceneProxyCount = -1;
        OutSnapshotWorldSeconds = -1.0f;
        OutReason.Reset();
        if (!IsInGameThread())
        {
            OutReason = TEXT("RENDERER LOD SNAPSHOT MUST RUN ON THE GAME THREAD");
            return false;
        }
        if (!World || !World->Scene)
        {
            OutReason = TEXT("RENDERER LOD SNAPSHOT REQUIRES A LIVE WORLD SCENE");
            return false;
        }
        OutSnapshotWorldSeconds = World->GetTimeSeconds();
        if (!FMath::IsFinite(OutSnapshotWorldSeconds)
            || OutSnapshotWorldSeconds < ViewConfiguredWorldSeconds)
        {
            OutReason = TEXT("RENDERER LOD SNAPSHOT WORLD TIME IS INVALID");
            return false;
        }

        const IConsoleVariable* ForceLOD =
            IConsoleManager::Get().FindConsoleVariable(TEXT("r.ForceLOD"));
        if (!ForceLOD)
        {
            OutReason = TEXT("RENDERER LOD SNAPSHOT CANNOT VERIFY GLOBAL FORCED LOD STATE");
            return false;
        }
        OutGlobalForcedLOD = ForceLOD->GetInt();
        if (OutGlobalForcedLOD >= 0)
        {
            bOutAnyForcedLOD = true;
            OutReason = FString::Printf(TEXT("GLOBAL RENDERER LOD IS FORCED TO %d"),
                OutGlobalForcedLOD);
            return false;
        }

        APlayerController* Controller = World->GetFirstPlayerController();
        ULocalPlayer* LocalPlayer = Controller ? Cast<ULocalPlayer>(Controller->Player) : nullptr;
        UGameViewportClient* ViewportClient = LocalPlayer ? LocalPlayer->ViewportClient : nullptr;
        FViewport* Viewport = ViewportClient ? ViewportClient->Viewport : nullptr;
        if (!Controller || !LocalPlayer || !ViewportClient || !Viewport)
        {
            OutReason = TEXT("RENDERER LOD SNAPSHOT REQUIRES THE LOCAL GAME VIEWPORT");
            return false;
        }

        OutRegisteredSceneProxyCount = 0;
        for (TActorIterator<AActor> It(World); It; ++It)
        {
            AActor* Actor = *It;
            if (!IsValid(Actor) || Actor->IsActorBeingDestroyed()) continue;
            TArray<UPrimitiveComponent*> PrimitiveComponents;
            Actor->GetComponents<UPrimitiveComponent>(PrimitiveComponents);
            for (UPrimitiveComponent* Component : PrimitiveComponents)
            {
                if (IsValid(Component) && Component->IsRegistered()
                    && Component->GetSceneProxy())
                {
                    ++OutRegisteredSceneProxyCount;
                }
            }
        }
        if (OutRegisteredSceneProxyCount < ExpectedPerformanceTargetComponentCount)
        {
            OutReason = TEXT("REGISTERED SCENE PROXY COUNT CANNOT COVER ALL LOD TARGETS");
            return false;
        }

        FSceneViewFamilyContext ViewFamily(FSceneViewFamily::ConstructionValues(
            Viewport, World->Scene, ViewportClient->EngineShowFlags).SetRealtimeUpdate(false));
        FVector ViewLocation;
        FRotator ViewRotation;
        const FSceneView* SceneView = LocalPlayer->CalcSceneView(
            &ViewFamily, ViewLocation, ViewRotation, Viewport);
        if (!SceneView)
        {
            OutReason = TEXT("LOCAL PLAYER COULD NOT BUILD THE RENDERER LOD SCENE VIEW");
            return false;
        }
        OutViewWidth = SceneView->UnscaledViewRect.Width();
        OutViewHeight = SceneView->UnscaledViewRect.Height();
        if (OutViewWidth != ExpectedPerformanceViewportWidth
            || OutViewHeight != ExpectedPerformanceViewportHeight)
        {
            OutReason = FString::Printf(
                TEXT("RENDERER LOD SCENE VIEW IS %dx%d NOT 1920X1080"),
                OutViewWidth, OutViewHeight);
            return false;
        }
        return BuildPackagedPerformanceTargetManifest(World, SceneView,
            ViewConfiguredWorldSeconds, OutSnapshotWorldSeconds,
            OutTargets, OutMeshPaths, bOutAnyForcedLOD, OutReason);
    }

    bool IsSafeValidationToken(const FString& Token)
    {
        if (Token.Len() < 16 || Token.Len() > 96) return false;
        for (const TCHAR Character : Token)
        {
            if (!FChar::IsAlnum(Character) && Character != TEXT('-') && Character != TEXT('_'))
                return false;
        }
        return true;
    }

    FString RuntimeStageName(const ELBBodyShopRuntimeStage Stage)
    {
        switch (Stage)
        {
        case ELBBodyShopRuntimeStage::Offline: return TEXT("OFFLINE");
        case ELBBodyShopRuntimeStage::Ready: return TEXT("READY");
        case ELBBodyShopRuntimeStage::AwaitingPanelStillage: return TEXT("AWAITING_PANEL_STILLAGE");
        case ELBBodyShopRuntimeStage::TransferringStillage: return TEXT("TRANSFERRING_STILLAGE");
        case ELBBodyShopRuntimeStage::PresentingPanel: return TEXT("PRESENTING_PANEL");
        case ELBBodyShopRuntimeStage::WeldingUnderbody: return TEXT("WELDING_UNDERBODY");
        case ELBBodyShopRuntimeStage::ConveyingSkid: return TEXT("CONVEYING_SKID");
        case ELBBodyShopRuntimeStage::Inspecting: return TEXT("INSPECTING");
        case ELBBodyShopRuntimeStage::OutputBlocked: return TEXT("OUTPUT_BLOCKED");
        case ELBBodyShopRuntimeStage::QualityHold: return TEXT("QUALITY_HOLD");
        case ELBBodyShopRuntimeStage::Complete: return TEXT("COMPLETE");
        case ELBBodyShopRuntimeStage::Faulted: return TEXT("FAULTED");
        default: return TEXT("UNKNOWN");
        }
    }

    FString SanitizeMarkerValue(FString Value)
    {
        Value.ReplaceInline(TEXT("\r"), TEXT(" "));
        Value.ReplaceInline(TEXT("\n"), TEXT(" "));
        Value.ReplaceInline(TEXT("="), TEXT("-"));
        return Value.Left(240);
    }
}

ALBBodyShopPrototypeGameMode::ALBBodyShopPrototypeGameMode()
{
    DefaultPawnClass = ALBBodyShopManagementPawn::StaticClass();
    HUDClass = ALBBodyShopPrototypeHUD::StaticClass();
    bUseSeamlessTravel = false;
    PrimaryActorTick.bCanEverTick = true;
    PrimaryActorTick.bStartWithTickEnabled = false;
}

void ALBBodyShopPrototypeGameMode::BeginPlay()
{
    Super::BeginPlay();

    PrototypeBootstrap.Reset();
    bPrototypeBootstrapValid = false;
    PrototypeIsolationStatus = TEXT("BODY SHOP PROTOTYPE BOOTSTRAP MISSING");

    UWorld* World = GetWorld();
    if (!World)
    {
        UE_LOG(LogTemp, Error, TEXT("LINE_BOSS_BODY_SHOP_PROTOTYPE no_world"));
        return;
    }

    for (TActorIterator<ALBBodyShopPrototypeWorldBootstrap> It(World); It; ++It)
    {
        if (!IsValid(*It) || It->IsActorBeingDestroyed()) continue;
        if (PrototypeBootstrap.IsValid())
        {
            PrototypeIsolationStatus = TEXT("BODY SHOP PROTOTYPE HAS MULTIPLE BOOTSTRAPS");
            UE_LOG(LogTemp, Error,
                TEXT("LINE_BOSS_BODY_SHOP_PROTOTYPE multiple_bootstraps first=%s duplicate=%s"),
                *PrototypeBootstrap->GetName(), *It->GetName());
            return;
        }
        PrototypeBootstrap = *It;
    }

    if (!PrototypeBootstrap.IsValid())
    {
        UE_LOG(LogTemp, Error, TEXT("LINE_BOSS_BODY_SHOP_PROTOTYPE bootstrap_missing"));
        return;
    }

    PrototypeBootstrap->RefreshBootstrapState();
    FString Reason;
    const bool bIsolationPreflightValid = PrototypeBootstrap->IsBootstrapConfigurationValid()
        && PrototypeBootstrap->IsWorldIsolationValid()
        && !PrototypeBootstrap->HasDetectedLegacyAuthority();
    if (!bIsolationPreflightValid)
    {
        bPrototypeBootstrapValid = ValidatePrototypeWorldContract(true,
            PrototypeBootstrap->IsBootstrapConfigurationValid(),
            PrototypeBootstrap->IsWorldIsolationValid(),
            PrototypeBootstrap->HasDetectedLegacyAuthority(), false, false, Reason);
        PrototypeIsolationStatus = Reason;
        UE_LOG(LogTemp, Error,
            TEXT("LINE_BOSS_BODY_SHOP_PROTOTYPE bootstrap=%s valid=0 status=%s"),
            *PrototypeBootstrap->GetName(), *PrototypeIsolationStatus);
        return;
    }

    // The saved map contains only the bootstrap. This one BeginPlay call is
    // the sole authority that may create the isolated build/runtime pair.
    if (!PrototypeBootstrap->InitialiseRuntimeAuthorities(Reason))
    {
        bPrototypeBootstrapValid = false;
        PrototypeIsolationStatus = Reason;
        UE_LOG(LogTemp, Error,
            TEXT("LINE_BOSS_BODY_SHOP_PROTOTYPE bootstrap=%s runtime_init=0 status=%s"),
            *PrototypeBootstrap->GetName(), *PrototypeIsolationStatus);
        return;
    }

    bPrototypeBootstrapValid = ValidatePrototypeWorldContract(true,
        PrototypeBootstrap->IsBootstrapConfigurationValid(),
        PrototypeBootstrap->IsWorldIsolationValid(),
        PrototypeBootstrap->HasDetectedLegacyAuthority(),
        PrototypeBootstrap->ArePrototypeAuthoritiesBound(),
        PrototypeBootstrap->HasCommissionedInitialUnderbodySlice(), Reason);
    PrototypeIsolationStatus = bPrototypeBootstrapValid
        ? PrototypeBootstrap->GetBootstrapStatusText() : Reason;
    if (!bPrototypeBootstrapValid)
    {
        UE_LOG(LogTemp, Error,
            TEXT("LINE_BOSS_BODY_SHOP_PROTOTYPE bootstrap=%s valid=0 status=%s"),
            *PrototypeBootstrap->GetName(), *PrototypeIsolationStatus);
        return;
    }

    // Native v002 environment dressing is always transient and remains deliberately
    // outside the bootstrap/build/runtime/save authority graph. It is attempted only
    // after the isolated runtime has been commissioned; failure leaves that authority
    // pair and its state untouched.
    FString ServiceDressingReason;
    ALBBodyShopServiceDressingActor* ServiceDressing =
        LBBodyShopPrototypeGameModePrivate::TrySpawnServiceDressing(
            World, this, ServiceDressingReason);
    if (ServiceDressing)
    {
        UE_LOG(LogTemp, Display,
            TEXT("LINE_BOSS_BODY_SHOP_SERVICE_DRESSING_V002 actor=%s instances=%d wip=0"),
            *ServiceDressing->GetName(), ServiceDressing->GetVisibleInstanceCount());
    }
    else
    {
        UE_LOG(LogTemp, Warning,
            TEXT("LINE_BOSS_BODY_SHOP_SERVICE_DRESSING_V002_FAILED status=%s"),
            *ServiceDressingReason);
    }

    // BeginPlay may initially focus the empty map shell. Reframe only after the
    // bootstrap has successfully commissioned the authoritative six-cell slice.
    ALBBodyShopManagementPawn* ManagementPawn = nullptr;
    if (APlayerController* PlayerController = World->GetFirstPlayerController())
    {
        ManagementPawn = Cast<ALBBodyShopManagementPawn>(PlayerController->GetPawn());
    }
    if (!ManagementPawn)
    {
        for (TActorIterator<ALBBodyShopManagementPawn> It(World); It; ++It)
        {
            if (IsValid(*It) && !It->IsActorBeingDestroyed())
            {
                ManagementPawn = *It;
                break;
            }
        }
    }
    if (!ManagementPawn || !ManagementPawn->FocusPrototypeProcess())
    {
        UE_LOG(LogTemp, Warning,
            TEXT("LINE_BOSS_BODY_SHOP_PROTOTYPE commissioned_camera_focus_pending"));
    }
    UE_LOG(LogTemp, Display,
        TEXT("LINE_BOSS_BODY_SHOP_PROTOTYPE bootstrap=%s valid=1 status=%s"),
        *PrototypeBootstrap->GetName(), *PrototypeIsolationStatus);

#if !UE_BUILD_SHIPPING
    InitialisePackagedValidationBridge(FCommandLine::Get());
    InitialisePackagedPerformanceBridge(FCommandLine::Get());
#endif
}

void ALBBodyShopPrototypeGameMode::Tick(const float DeltaSeconds)
{
    Super::Tick(DeltaSeconds);
#if !UE_BUILD_SHIPPING
    TickPackagedValidationBridge(DeltaSeconds);
    TickPackagedPerformanceBridge(DeltaSeconds);
#endif
}

bool ALBBodyShopPrototypeGameMode::ValidatePrototypeWorldContract(
    const bool bHasBootstrap, const bool bBootstrapFlagsValid,
    const bool bWorldIsolationValid, const bool bFoundLegacyAuthority,
    const bool bRuntimeAuthoritiesBound,
    const bool bInitialUnderbodySliceCommissioned, FString& OutReason)
{
    OutReason.Reset();
    if (!bHasBootstrap)
    {
        OutReason = TEXT("BODY SHOP PROTOTYPE REQUIRES EXACTLY ONE MAP BOOTSTRAP");
        return false;
    }
    if (!bBootstrapFlagsValid)
    {
        OutReason = TEXT("BODY SHOP PROTOTYPE MAP BOOTSTRAP FLAGS ARE INVALID");
        return false;
    }
    if (!bWorldIsolationValid)
    {
        OutReason = bFoundLegacyAuthority
            ? TEXT("BODY SHOP PROTOTYPE MAP CONTAINS A LEGACY FACTORY AUTHORITY")
            : TEXT("BODY SHOP PROTOTYPE MAP IS NOT ISOLATED");
        return false;
    }
    if (!bRuntimeAuthoritiesBound)
    {
        OutReason = TEXT("BODY SHOP PROTOTYPE RUNTIME AUTHORITIES ARE NOT BOUND");
        return false;
    }
    if (!bInitialUnderbodySliceCommissioned)
    {
        OutReason = TEXT("BODY SHOP PROTOTYPE UNDERBODY SLICE IS NOT COMMISSIONED");
        return false;
    }
    OutReason = TEXT("BODY SHOP PROTOTYPE IS ISOLATED");
    return true;
}

bool ALBBodyShopPrototypeGameMode::ParsePackagedValidationRequest(const TCHAR* CommandLine,
    FLBBodyShopPackagedValidationRequest& OutRequest, FString& OutReason)
{
    OutRequest = FLBBodyShopPackagedValidationRequest();
    OutReason.Reset();
    if (!CommandLine)
    {
        OutReason = TEXT("BODY SHOP PACKAGE VALIDATION COMMAND LINE IS NULL");
        return false;
    }

    FString ModeValue;
    if (!FParse::Value(CommandLine, TEXT("LineBossBodyShopPackageValidation="), ModeValue))
    {
        OutReason = TEXT("BODY SHOP PACKAGE VALIDATION NOT REQUESTED");
        return true;
    }
    if (ModeValue.Equals(TEXT("Save"), ESearchCase::IgnoreCase))
        OutRequest.Mode = ELBBodyShopPackagedValidationMode::Save;
    else if (ModeValue.Equals(TEXT("Load"), ESearchCase::IgnoreCase))
        OutRequest.Mode = ELBBodyShopPackagedValidationMode::Load;
    else
    {
        OutReason = TEXT("BODY SHOP PACKAGE VALIDATION MODE MUST BE SAVE OR LOAD");
        return false;
    }

    if (!FParse::Value(CommandLine, TEXT("LineBossBodyShopValidationToken="), OutRequest.Token)
        || !LBBodyShopPrototypeGameModePrivate::IsSafeValidationToken(OutRequest.Token))
    {
        OutRequest.Token.Reset();
        OutReason = TEXT("BODY SHOP PACKAGE VALIDATION REQUIRES A 16-96 CHARACTER SAFE TOKEN");
        return false;
    }
    OutReason = TEXT("BODY SHOP PACKAGE VALIDATION REQUEST VALID");
    return true;
}

FString ALBBodyShopPrototypeGameMode::BuildPackagedValidationMarker(
    const ELBBodyShopPackagedValidationMode Mode, const FString& Token,
    const bool bPassed, const FString& StageName, const int32 LogicalWIPCount,
    const int32 VisibleWIPCount, const FString& FailureReason)
{
    const TCHAR* Phase = Mode == ELBBodyShopPackagedValidationMode::Save ? TEXT("SAVE")
        : Mode == ELBBodyShopPackagedValidationMode::Load ? TEXT("LOAD") : TEXT("NONE");
    FString Marker = FString::Printf(
        TEXT("LINE_BOSS_BODY_SHOP_PACKAGE_VALIDATION_V001 phase=%s token=%s result=%s stage=%s logical_wip=%d visible_wip=%d save_slot=%s"),
        Phase, *Token, bPassed ? TEXT("PASS") : TEXT("FAIL"), *StageName,
        LogicalWIPCount, VisibleWIPCount,
        *ULBBodyShopExperimentalSaveGame::GetSlotName().ToString());
    if (!bPassed)
    {
        Marker += TEXT(" reason=")
            + LBBodyShopPrototypeGameModePrivate::SanitizeMarkerValue(FailureReason);
    }
    return Marker;
}

bool ALBBodyShopPrototypeGameMode::ParsePackagedPerformanceRequest(const TCHAR* CommandLine,
    FLBBodyShopPackagedPerformanceRequest& OutRequest, FString& OutReason)
{
    OutRequest = FLBBodyShopPackagedPerformanceRequest();
    OutReason.Reset();
    if (!CommandLine)
    {
        OutReason = TEXT("BODY SHOP PACKAGED PERFORMANCE COMMAND LINE IS NULL");
        return false;
    }

    FString ViewValue;
    if (!FParse::Value(CommandLine, TEXT("LineBossBodyShopPerformanceValidation="), ViewValue))
    {
        OutReason = TEXT("BODY SHOP PACKAGED PERFORMANCE NOT REQUESTED");
        return true;
    }
    if (ViewValue.Equals(TEXT("Management"), ESearchCase::IgnoreCase))
        OutRequest.View = ELBBodyShopPackagedPerformanceView::Management;
    else if (ViewValue.Equals(TEXT("Focus"), ESearchCase::IgnoreCase))
        OutRequest.View = ELBBodyShopPackagedPerformanceView::Focus;
    else
    {
        OutReason = TEXT("BODY SHOP PACKAGED PERFORMANCE VIEW MUST BE MANAGEMENT OR FOCUS");
        return false;
    }

    FString ConflictingPackageMode;
    if (FParse::Value(CommandLine, TEXT("LineBossBodyShopPackageValidation="),
        ConflictingPackageMode))
    {
        OutRequest = FLBBodyShopPackagedPerformanceRequest();
        OutReason = TEXT("BODY SHOP PACKAGED PERFORMANCE CANNOT SHARE A SAVE LOAD PROCESS");
        return false;
    }
    if (!FParse::Value(CommandLine, TEXT("LineBossBodyShopValidationToken="), OutRequest.Token)
        || !LBBodyShopPrototypeGameModePrivate::IsSafeValidationToken(OutRequest.Token))
    {
        OutRequest = FLBBodyShopPackagedPerformanceRequest();
        OutReason = TEXT("BODY SHOP PACKAGED PERFORMANCE REQUIRES A 16-96 CHARACTER SAFE TOKEN");
        return false;
    }
    OutReason = TEXT("BODY SHOP PACKAGED PERFORMANCE REQUEST VALID");
    return true;
}

FString ALBBodyShopPrototypeGameMode::BuildPackagedPerformanceMarker(
    const ELBBodyShopPackagedPerformanceView View, const FString& Token,
    const bool bPassed, const FString& GraphicsRHI, const int32 ViewportWidth,
    const int32 ViewportHeight, const int32 CapturedFrames,
    const int32 TargetComponentCount, const int32 UniqueMeshCount,
    const FString& ReceiptLeaf, const FString& FailureReason)
{
    FString Marker = FString::Printf(
        TEXT("LINE_BOSS_BODY_SHOP_PACKAGED_PERFORMANCE_LOD_V002 view=%s token=%s result=%s viewport=%dx%d frames=%d components=%d meshes=%d rhi=%s receipt=%s"),
        *LBBodyShopPrototypeGameModePrivate::PerformanceViewName(View, true), *Token,
        bPassed ? TEXT("PASS") : TEXT("FAIL"), ViewportWidth, ViewportHeight,
        CapturedFrames, TargetComponentCount, UniqueMeshCount,
        *LBBodyShopPrototypeGameModePrivate::SanitizeMarkerToken(GraphicsRHI),
        *LBBodyShopPrototypeGameModePrivate::SanitizeMarkerToken(ReceiptLeaf));
    if (!bPassed)
    {
        Marker += TEXT(" reason=")
            + LBBodyShopPrototypeGameModePrivate::SanitizeMarkerToken(FailureReason);
    }
    return Marker;
}

bool ALBBodyShopPrototypeGameMode::ValidatePackagedPerformanceTargetCounts(
    const int32 RobotCount, const int32 TargetComponentCount, const int32 UniqueMeshCount,
    const bool bAnyForcedLOD, FString& OutReason)
{
    OutReason.Reset();
    if (RobotCount != LBBodyShopPrototypeGameModePrivate::ExpectedPerformanceRobotCount)
    {
        OutReason = TEXT("PACKAGED PERFORMANCE REQUIRES EXACTLY THREE ROBOTS");
        return false;
    }
    if (TargetComponentCount
        != LBBodyShopPrototypeGameModePrivate::ExpectedPerformanceTargetComponentCount)
    {
        OutReason = TEXT("PACKAGED PERFORMANCE REQUIRES EXACTLY 25 TARGET COMPONENTS");
        return false;
    }
    if (UniqueMeshCount != LBBodyShopPrototypeGameModePrivate::ExpectedPerformanceUniqueMeshCount)
    {
        OutReason = TEXT("PACKAGED PERFORMANCE REQUIRES EXACTLY 10 UNIQUE TARGET MESHES");
        return false;
    }
    if (bAnyForcedLOD)
    {
        OutReason = TEXT("PACKAGED PERFORMANCE TARGETS MUST USE AUTOMATIC RENDERER LOD");
        return false;
    }
    OutReason = TEXT("PACKAGED PERFORMANCE TARGET COUNTS VALID");
    return true;
}

#if !UE_BUILD_SHIPPING
void ALBBodyShopPrototypeGameMode::InitialisePackagedValidationBridge(const TCHAR* CommandLine)
{
    FString Reason;
    if (!ParsePackagedValidationRequest(CommandLine, PackagedValidationRequest, Reason))
    {
        UE_LOG(LogTemp, Error, TEXT("LINE_BOSS_BODY_SHOP_PACKAGE_VALIDATION_V001 request_rejected reason=%s"),
            *LBBodyShopPrototypeGameModePrivate::SanitizeMarkerValue(Reason));
        if (GLog) GLog->Flush();
        FPlatformMisc::RequestExitWithStatus(false, static_cast<uint8>(3),
            TEXT("BodyShopPackageValidationRequestRejected"));
        return;
    }
    if (PackagedValidationRequest.Mode == ELBBodyShopPackagedValidationMode::None) return;

    PackagedValidationElapsedSeconds = 0.0f;
    bPackagedValidationActionIssued = false;
    bPackagedValidationSavePointPaused = false;
    SetActorTickEnabled(true);
    UE_LOG(LogTemp, Display,
        TEXT("LINE_BOSS_BODY_SHOP_PACKAGE_VALIDATION_V001 armed token=%s mode=%s"),
        *PackagedValidationRequest.Token,
        PackagedValidationRequest.Mode == ELBBodyShopPackagedValidationMode::Save
            ? TEXT("SAVE") : TEXT("LOAD"));
}

void ALBBodyShopPrototypeGameMode::TickPackagedValidationBridge(const float DeltaSeconds)
{
    if (PackagedValidationRequest.Mode == ELBBodyShopPackagedValidationMode::None) return;
    PackagedValidationElapsedSeconds += FMath::Max(0.0f, DeltaSeconds);

    ALBBodyShopPrototypeRuntime* Runtime = PrototypeBootstrap.IsValid()
        ? Cast<ALBBodyShopPrototypeRuntime>(PrototypeBootstrap->GetRuntimeActor()) : nullptr;
    if (!Runtime || !Runtime->IsRuntimeInitialised())
    {
        if (PackagedValidationElapsedSeconds >= LBBodyShopPrototypeGameModePrivate::PackagedValidationTimeoutSeconds)
            FinishPackagedValidationBridge(false, TEXT("RUNTIME DID NOT INITIALISE BEFORE TIMEOUT"));
        return;
    }

    FString Reason;
    if (PackagedValidationRequest.Mode == ELBBodyShopPackagedValidationMode::Load)
    {
        if (bPackagedValidationActionIssued) return;
        bPackagedValidationActionIssued = true;
        if (!Runtime->LoadFromExperimentalSlot(Reason))
        {
            FinishPackagedValidationBridge(false, TEXT("EXPERIMENTAL LOAD FAILED: ") + Reason);
            return;
        }
        if (!Runtime->SetSimulationRunning(false, Reason))
        {
            FinishPackagedValidationBridge(false, TEXT("LOADED WIP COULD NOT BE PAUSED: ") + Reason);
            return;
        }
        const bool bExactRestoredState = Runtime->GetRuntimeStage()
                == ELBBodyShopRuntimeStage::WeldingUnderbody
            && Runtime->GetActivePilotWIPCount() == 1
            && Runtime->GetVisibleRuntimeWIPPresentationCount() == 1;
        FinishPackagedValidationBridge(bExactRestoredState,
            bExactRestoredState ? FString() : TEXT("LOAD DID NOT RESTORE EXACTLY ONE VISIBLE WELDING WIP"));
        return;
    }

    if (!bPackagedValidationActionIssued)
    {
        bPackagedValidationActionIssued = true;
        if (!Runtime->StartPilotCycle(Reason))
        {
            FinishPackagedValidationBridge(false, TEXT("PILOT START FAILED: ") + Reason);
        }
        return;
    }
    if (Runtime->GetRuntimeStage() == ELBBodyShopRuntimeStage::Faulted)
    {
        FinishPackagedValidationBridge(false, TEXT("RUNTIME FAULTED BEFORE SAVE"));
        return;
    }
    if (Runtime->GetRuntimeStage() == ELBBodyShopRuntimeStage::WeldingUnderbody)
    {
        if (!bPackagedValidationSavePointPaused)
        {
            if (!Runtime->SetSimulationRunning(false, Reason))
            {
                FinishPackagedValidationBridge(false, TEXT("WELDING WIP COULD NOT BE PAUSED: ") + Reason);
                return;
            }
            bPackagedValidationSavePointPaused = true;
            // Let the runtime's next tick derive the paused presentation before
            // requiring the exact one-logical/one-visible save point.
            return;
        }
        if (Runtime->GetActivePilotWIPCount() != 1
            || Runtime->GetVisibleRuntimeWIPPresentationCount() != 1)
        {
            if (PackagedValidationElapsedSeconds
                >= LBBodyShopPrototypeGameModePrivate::PackagedValidationTimeoutSeconds)
            {
                FinishPackagedValidationBridge(false,
                    TEXT("SAVE POINT DID NOT SETTLE TO EXACTLY ONE VISIBLE WELDING WIP"));
            }
            return;
        }
        if (!Runtime->SaveToExperimentalSlot(Reason))
        {
            FinishPackagedValidationBridge(false, TEXT("EXPERIMENTAL SAVE FAILED: ") + Reason);
            return;
        }
        FinishPackagedValidationBridge(true, FString());
        return;
    }
    if (PackagedValidationElapsedSeconds >= LBBodyShopPrototypeGameModePrivate::PackagedValidationTimeoutSeconds)
        FinishPackagedValidationBridge(false, TEXT("WELDING SAVE POINT WAS NOT REACHED BEFORE TIMEOUT"));
}

void ALBBodyShopPrototypeGameMode::FinishPackagedValidationBridge(const bool bPassed,
    const FString& FailureReason)
{
    ALBBodyShopPrototypeRuntime* Runtime = PrototypeBootstrap.IsValid()
        ? Cast<ALBBodyShopPrototypeRuntime>(PrototypeBootstrap->GetRuntimeActor()) : nullptr;
    const FString StageName = Runtime
        ? LBBodyShopPrototypeGameModePrivate::RuntimeStageName(Runtime->GetRuntimeStage())
        : TEXT("NO_RUNTIME");
    const int32 LogicalWIP = Runtime ? Runtime->GetActivePilotWIPCount() : -1;
    const int32 VisibleWIP = Runtime ? Runtime->GetVisibleRuntimeWIPPresentationCount() : -1;
    const FString Marker = BuildPackagedValidationMarker(PackagedValidationRequest.Mode,
        PackagedValidationRequest.Token, bPassed, StageName, LogicalWIP, VisibleWIP, FailureReason);
    if (bPassed)
    {
        UE_LOG(LogTemp, Display, TEXT("%s"), *Marker);
    }
    else
    {
        UE_LOG(LogTemp, Error, TEXT("%s"), *Marker);
    }

    SetActorTickEnabled(false);
    PackagedValidationRequest.Mode = ELBBodyShopPackagedValidationMode::None;
    if (GLog) GLog->Flush();
    FPlatformMisc::RequestExitWithStatus(false, static_cast<uint8>(bPassed ? 0 : 3),
        TEXT("BodyShopPackagedSaveRestartLoadValidation"));
}

void ALBBodyShopPrototypeGameMode::InitialisePackagedPerformanceBridge(
    const TCHAR* CommandLine)
{
    FString Reason;
    if (!ParsePackagedPerformanceRequest(CommandLine, PackagedPerformanceRequest, Reason))
    {
        UE_LOG(LogTemp, Error,
            TEXT("LINE_BOSS_BODY_SHOP_PACKAGED_PERFORMANCE_LOD_V002 request_rejected reason=%s"),
            *LBBodyShopPrototypeGameModePrivate::SanitizeMarkerToken(Reason));
        if (GLog) GLog->Flush();
        FPlatformMisc::RequestExitWithStatus(false, static_cast<uint8>(3),
            TEXT("BodyShopPackagedPerformanceRequestRejected"));
        return;
    }
    if (PackagedPerformanceRequest.View == ELBBodyShopPackagedPerformanceView::None) return;
    if (PackagedValidationRequest.Mode != ELBBodyShopPackagedValidationMode::None)
    {
        FinishPackagedPerformanceBridge(false,
            TEXT("PACKAGED PERFORMANCE CANNOT SHARE A SAVE LOAD PROCESS"));
        return;
    }

    PackagedPerformancePhase = EPackagedPerformancePhase::WaitRuntime;
    PackagedPerformanceElapsedSeconds = 0.0f;
    PackagedPerformancePhaseFrames = 0;
    PackagedPerformanceStableFrames = 0;
    PackagedPerformanceLastFileSize = -1;
    PackagedPerformanceProfileStem.Reset();
    PackagedPerformanceProfilePath.Reset();
    PackagedPerformanceReceiptPath.Reset();
    PackagedPerformanceTargetSnapshot.Reset();
    PackagedPerformanceTargetMeshPaths.Reset();
    PackagedPerformanceSceneViewWidth = -1;
    PackagedPerformanceSceneViewHeight = -1;
    PackagedPerformanceGlobalForcedLOD = INDEX_NONE;
    PackagedPerformanceRegisteredSceneProxyCount = -1;
    PackagedPerformanceViewConfiguredWorldSeconds = -1.0f;
    PackagedPerformanceLODSnapshotWorldSeconds = -1.0f;
    SetActorTickEnabled(true);
    UE_LOG(LogTemp, Display,
        TEXT("LINE_BOSS_BODY_SHOP_PACKAGED_PERFORMANCE_LOD_V002 armed view=%s token=%s"),
        *LBBodyShopPrototypeGameModePrivate::PerformanceViewName(
            PackagedPerformanceRequest.View, true), *PackagedPerformanceRequest.Token);
}

bool ALBBodyShopPrototypeGameMode::ValidatePackagedPerformanceEnvironment(
    FString& OutReason) const
{
    OutReason.Reset();
    UWorld* World = GetWorld();
    if (!World || World->GetOutermost()->GetName()
        != TEXT("/Game/LineBoss/BodyShop/Experimental/v001/Maps/LB_BodyShop_Prototype_v001"))
    {
        OutReason = TEXT("PACKAGED PERFORMANCE DID NOT LOAD THE EXACT BODY SHOP MAP");
        return false;
    }

    int32 RequestedX = 0;
    int32 RequestedY = 0;
    const TCHAR* CommandLine = FCommandLine::Get();
    if (!FParse::Value(CommandLine, TEXT("ResX="), RequestedX) || RequestedX != 1920
        || !FParse::Value(CommandLine, TEXT("ResY="), RequestedY) || RequestedY != 1080
        || !FParse::Param(CommandLine, TEXT("ForceRes"))
        || !FParse::Param(CommandLine, TEXT("Windowed"))
        || !FParse::Param(CommandLine, TEXT("csvGpuStats"))
        || FParse::Param(CommandLine, TEXT("nullrhi")))
    {
        OutReason = TEXT("PACKAGED PERFORMANCE COMMAND LINE IS NOT EXACT REAL RHI 1920X1080 FORCERES");
        return false;
    }

    const FString GraphicsRHI = FApp::GetGraphicsRHI();
    if (!FApp::CanEverRender() || GraphicsRHI.IsEmpty()
        || GraphicsRHI.Contains(TEXT("NullRHI"), ESearchCase::IgnoreCase))
    {
        OutReason = TEXT("PACKAGED PERFORMANCE REQUIRES A NAMED NON NULL REAL RHI");
        return false;
    }
    const IConsoleVariable* GPUCsvStats = IConsoleManager::Get().FindConsoleVariable(
        TEXT("r.GPUCsvStatsEnabled"));
    if (!GPUCsvStats || GPUCsvStats->GetInt() != 1)
    {
        OutReason = TEXT("PACKAGED PERFORMANCE REQUIRES GPU CSV STATS");
        return false;
    }
    const IConsoleVariable* ForceLOD =
        IConsoleManager::Get().FindConsoleVariable(TEXT("r.ForceLOD"));
    if (!ForceLOD || ForceLOD->GetInt() != INDEX_NONE)
    {
        OutReason = TEXT("PACKAGED PERFORMANCE REQUIRES AUTOMATIC GLOBAL RENDERER LOD");
        return false;
    }

    APlayerController* Controller = World->GetFirstPlayerController();
    int32 ViewportX = 0;
    int32 ViewportY = 0;
    if (!Controller)
    {
        OutReason = TEXT("PACKAGED PERFORMANCE PLAYER CONTROLLER IS MISSING");
        return false;
    }
    Controller->GetViewportSize(ViewportX, ViewportY);
    if (ViewportX != LBBodyShopPrototypeGameModePrivate::ExpectedPerformanceViewportWidth
        || ViewportY != LBBodyShopPrototypeGameModePrivate::ExpectedPerformanceViewportHeight)
    {
        OutReason = FString::Printf(TEXT("PACKAGED PERFORMANCE VIEWPORT IS %dx%d NOT 1920X1080"),
            ViewportX, ViewportY);
        return false;
    }
    if (!LBBodyShopPrototypeGameModePrivate::FindManagementPawn(World))
    {
        OutReason = TEXT("PACKAGED PERFORMANCE MANAGEMENT PAWN IS MISSING");
        return false;
    }

    TArray<TSharedPtr<FJsonValue>> Targets;
    TSet<FString> MeshPaths;
    bool bAnyForcedLOD = false;
    if (!LBBodyShopPrototypeGameModePrivate::BuildPackagedPerformanceTargetManifest(World,
        nullptr, -1.0f, -1.0f,
        Targets, MeshPaths, bAnyForcedLOD, OutReason))
        return false;
    return ValidatePackagedPerformanceTargetCounts(
        LBBodyShopPrototypeGameModePrivate::ExpectedPerformanceRobotCount,
        Targets.Num(), MeshPaths.Num(), bAnyForcedLOD, OutReason);
}

bool ALBBodyShopPrototypeGameMode::WritePackagedPerformanceReceipt(
    FString& OutReceiptPath, FString& OutReason) const
{
    OutReceiptPath.Reset();
    OutReason.Reset();
    UWorld* World = GetWorld();
    APlayerController* Controller = World ? World->GetFirstPlayerController() : nullptr;
    ALBBodyShopManagementPawn* Pawn =
        LBBodyShopPrototypeGameModePrivate::FindManagementPawn(World);
    UCameraComponent* Camera = Pawn ? Pawn->FindComponentByClass<UCameraComponent>() : nullptr;
    if (!World || !Controller || !Pawn || !Camera)
    {
        OutReason = TEXT("PACKAGED PERFORMANCE CAMERA RECEIPT CONTRACT IS UNAVAILABLE");
        return false;
    }
    if (PackagedPerformanceProfilePath.IsEmpty()
        || IFileManager::Get().FileSize(*PackagedPerformanceProfilePath) < 4096)
    {
        OutReason = TEXT("PACKAGED PERFORMANCE RAW CSV EVIDENCE IS INCOMPLETE");
        return false;
    }
    if (PackagedPerformanceTargetSnapshot.Num()
            != LBBodyShopPrototypeGameModePrivate::ExpectedPerformanceTargetComponentCount
        || PackagedPerformanceTargetMeshPaths.Num()
            != LBBodyShopPrototypeGameModePrivate::ExpectedPerformanceUniqueMeshCount
        || PackagedPerformanceSceneViewWidth != 1920
        || PackagedPerformanceSceneViewHeight != 1080
        || PackagedPerformanceGlobalForcedLOD != INDEX_NONE
        || PackagedPerformanceRegisteredSceneProxyCount
            < LBBodyShopPrototypeGameModePrivate::ExpectedPerformanceTargetComponentCount
        || PackagedPerformanceViewConfiguredWorldSeconds < 0.0f
        || PackagedPerformanceLODSnapshotWorldSeconds
            < PackagedPerformanceViewConfiguredWorldSeconds)
    {
        OutReason = TEXT("PACKAGED PERFORMANCE RENDERER LOD SNAPSHOT IS INCOMPLETE");
        return false;
    }

    if (!ValidatePackagedPerformanceTargetCounts(
        LBBodyShopPrototypeGameModePrivate::ExpectedPerformanceRobotCount,
        PackagedPerformanceTargetSnapshot.Num(), PackagedPerformanceTargetMeshPaths.Num(),
        false, OutReason))
        return false;

    int32 ViewportX = 0;
    int32 ViewportY = 0;
    Controller->GetViewportSize(ViewportX, ViewportY);
    if (ViewportX != 1920 || ViewportY != 1080)
    {
        OutReason = TEXT("PACKAGED PERFORMANCE VIEWPORT DRIFTED BEFORE RECEIPT");
        return false;
    }

    TSharedPtr<FJsonObject> Root = MakeShared<FJsonObject>();
    Root->SetStringField(TEXT("$schema"),
        TEXT("cairnwell/body-shop/experimental-v001/packaged-performance-runtime-view/v2"));
    Root->SetStringField(TEXT("generated_utc"), FDateTime::UtcNow().ToIso8601());
    Root->SetStringField(TEXT("status"),
        TEXT("PASS__BODY_SHOP_PACKAGED_PERFORMANCE_LOD_VIEW_V002"));
    Root->SetStringField(TEXT("token"), PackagedPerformanceRequest.Token);
    Root->SetStringField(TEXT("view"),
        LBBodyShopPrototypeGameModePrivate::PerformanceViewName(
            PackagedPerformanceRequest.View, false));
    Root->SetStringField(TEXT("map"), World->GetOutermost()->GetName());
    Root->SetStringField(TEXT("engine_command_line"), FCommandLine::Get());

    TSharedPtr<FJsonObject> CaptureContract = MakeShared<FJsonObject>();
    CaptureContract->SetStringField(TEXT("surface"), TEXT("packaged_development_game"));
    CaptureContract->SetStringField(TEXT("viewport_size_authority"),
        TEXT("APlayerController.GetViewportSize"));
    CaptureContract->SetArrayField(TEXT("viewport"), {
        MakeShared<FJsonValueNumber>(ViewportX), MakeShared<FJsonValueNumber>(ViewportY)
    });
    CaptureContract->SetNumberField(TEXT("warmup_frames"),
        LBBodyShopPrototypeGameModePrivate::PackagedPerformanceWarmupFrames);
    CaptureContract->SetNumberField(TEXT("csv_capture_frames"),
        LBBodyShopPrototypeGameModePrivate::PackagedPerformanceCaptureFrames);
    CaptureContract->SetBoolField(TEXT("force_res"), true);
    CaptureContract->SetBoolField(TEXT("real_rhi_required"), true);
    CaptureContract->SetBoolField(TEXT("null_rhi_forbidden"), true);
    CaptureContract->SetBoolField(TEXT("gpu_csv_stats_required"), true);
    CaptureContract->SetStringField(TEXT("renderer_lod_snapshot_phase"),
        TEXT("game_thread_after_warmup_before_csv"));
    CaptureContract->SetStringField(TEXT("renderer_lod_selection_source"),
        TEXT("FPrimitiveSceneProxy::GetLOD(FSceneView)"));
    CaptureContract->SetBoolField(TEXT("primitive_debug_dump_used"), false);
    CaptureContract->SetStringField(TEXT("visible_primitives_budget_authority"),
        TEXT("registered_scene_proxy_component_upper_bound"));
    Root->SetObjectField(TEXT("capture_contract"), CaptureContract);

    TSharedPtr<FJsonObject> RHI = MakeShared<FJsonObject>();
    RHI->SetStringField(TEXT("graphics_rhi"), FApp::GetGraphicsRHI());
    RHI->SetBoolField(TEXT("can_ever_render"), FApp::CanEverRender());
    RHI->SetBoolField(TEXT("null_rhi_command_line"),
        FParse::Param(FCommandLine::Get(), TEXT("nullrhi")));
    const IConsoleVariable* GPUCsvStats = IConsoleManager::Get().FindConsoleVariable(
        TEXT("r.GPUCsvStatsEnabled"));
    RHI->SetNumberField(TEXT("r.GPUCsvStatsEnabled"), GPUCsvStats ? GPUCsvStats->GetInt() : -1);
    Root->SetObjectField(TEXT("rhi"), RHI);

    TSharedPtr<FJsonObject> CameraJson = MakeShared<FJsonObject>();
    CameraJson->SetArrayField(TEXT("viewport"), {
        MakeShared<FJsonValueNumber>(ViewportX), MakeShared<FJsonValueNumber>(ViewportY)
    });
    CameraJson->SetArrayField(TEXT("pawn_location_cm"),
        LBBodyShopPrototypeGameModePrivate::JsonVector(Pawn->GetActorLocation()));
    CameraJson->SetObjectField(TEXT("control_rotation_degrees"),
        LBBodyShopPrototypeGameModePrivate::JsonRotator(Controller->GetControlRotation()));
    CameraJson->SetArrayField(TEXT("camera_world_location_cm"),
        LBBodyShopPrototypeGameModePrivate::JsonVector(Camera->GetComponentLocation()));
    CameraJson->SetObjectField(TEXT("camera_world_rotation_degrees"),
        LBBodyShopPrototypeGameModePrivate::JsonRotator(Camera->GetComponentRotation()));
    CameraJson->SetNumberField(TEXT("horizontal_fov_degrees"), Camera->FieldOfView);
    CameraJson->SetNumberField(TEXT("zoom_distance_cm"), Pawn->GetPrototypeZoomDistance());
    Root->SetObjectField(TEXT("camera"), CameraJson);

    TArray<FString> SortedMeshes = PackagedPerformanceTargetMeshPaths.Array();
    SortedMeshes.Sort();
    TArray<TSharedPtr<FJsonValue>> MeshValues;
    for (const FString& MeshPath : SortedMeshes)
        MeshValues.Add(MakeShared<FJsonValueString>(MeshPath));
    TSharedPtr<FJsonObject> TargetSummary = MakeShared<FJsonObject>();
    TargetSummary->SetNumberField(TEXT("robot_count"),
        LBBodyShopPrototypeGameModePrivate::ExpectedPerformanceRobotCount);
    TargetSummary->SetNumberField(TEXT("component_count"),
        PackagedPerformanceTargetSnapshot.Num());
    TargetSummary->SetNumberField(TEXT("unique_mesh_count"),
        PackagedPerformanceTargetMeshPaths.Num());
    TargetSummary->SetArrayField(TEXT("unique_mesh_paths"), MeshValues);
    TargetSummary->SetBoolField(TEXT("any_forced_lod"), false);
    TargetSummary->SetNumberField(TEXT("global_forced_lod"),
        PackagedPerformanceGlobalForcedLOD);
    Root->SetObjectField(TEXT("target_summary"), TargetSummary);
    Root->SetArrayField(TEXT("target_components"), PackagedPerformanceTargetSnapshot);

    TSharedPtr<FJsonObject> LODSnapshot = MakeShared<FJsonObject>();
    LODSnapshot->SetStringField(TEXT("thread"), TEXT("game_thread"));
    LODSnapshot->SetStringField(TEXT("phase"), TEXT("after_120_warmup_frames_before_csv"));
    LODSnapshot->SetStringField(TEXT("selection_source"),
        TEXT("FPrimitiveSceneProxy::GetLOD(FSceneView)"));
    LODSnapshot->SetArrayField(TEXT("scene_view_unscaled_size"), {
        MakeShared<FJsonValueNumber>(PackagedPerformanceSceneViewWidth),
        MakeShared<FJsonValueNumber>(PackagedPerformanceSceneViewHeight)
    });
    LODSnapshot->SetNumberField(TEXT("component_count"),
        PackagedPerformanceTargetSnapshot.Num());
    LODSnapshot->SetNumberField(TEXT("unique_mesh_count"),
        PackagedPerformanceTargetMeshPaths.Num());
    LODSnapshot->SetNumberField(TEXT("global_forced_lod"),
        PackagedPerformanceGlobalForcedLOD);
    LODSnapshot->SetNumberField(TEXT("registered_scene_proxy_component_count"),
        PackagedPerformanceRegisteredSceneProxyCount);
    LODSnapshot->SetNumberField(TEXT("view_configured_world_time_seconds"),
        PackagedPerformanceViewConfiguredWorldSeconds);
    LODSnapshot->SetNumberField(TEXT("snapshot_world_time_seconds"),
        PackagedPerformanceLODSnapshotWorldSeconds);
    LODSnapshot->SetBoolField(TEXT("all_targets_rendered_since_view_configured"), true);
    Root->SetObjectField(TEXT("renderer_lod_snapshot"), LODSnapshot);

    TSharedPtr<FJsonObject> Profile = MakeShared<FJsonObject>();
    Profile->SetStringField(TEXT("path"), PackagedPerformanceProfilePath);
    Profile->SetNumberField(TEXT("bytes"),
        static_cast<double>(IFileManager::Get().FileSize(*PackagedPerformanceProfilePath)));
    Profile->SetNumberField(TEXT("requested_frames"),
        LBBodyShopPrototypeGameModePrivate::PackagedPerformanceCaptureFrames);
    Root->SetObjectField(TEXT("raw_csv"), Profile);

    const FString ViewName = LBBodyShopPrototypeGameModePrivate::PerformanceViewName(
        PackagedPerformanceRequest.View, false);
    const FString ReceiptDirectory = FPaths::Combine(FPaths::ProjectSavedDir(), TEXT("Audits"),
        TEXT("BodyShop"), TEXT("Experimental_v001"),
        TEXT("PackagedPerformanceLODValidation"), PackagedPerformanceRequest.Token);
    if (!IFileManager::Get().MakeDirectory(*ReceiptDirectory, true))
    {
        OutReason = TEXT("COULD NOT CREATE PACKAGED PERFORMANCE RECEIPT DIRECTORY");
        return false;
    }
    OutReceiptPath = FPaths::Combine(ReceiptDirectory,
        ViewName + TEXT("_runtime_capture_v002.json"));
    FString JsonText;
    const TSharedRef<TJsonWriter<>> Writer = TJsonWriterFactory<>::Create(&JsonText);
    if (!FJsonSerializer::Serialize(Root.ToSharedRef(), Writer)
        || !FFileHelper::SaveStringToFile(JsonText + TEXT("\n"), *OutReceiptPath,
            FFileHelper::EEncodingOptions::ForceUTF8WithoutBOM))
    {
        OutReason = TEXT("COULD NOT WRITE PACKAGED PERFORMANCE RUNTIME RECEIPT");
        OutReceiptPath.Reset();
        return false;
    }
    OutReceiptPath = FPaths::ConvertRelativePathToFull(OutReceiptPath);
    FPaths::NormalizeFilename(OutReceiptPath);
    return true;
}

void ALBBodyShopPrototypeGameMode::TickPackagedPerformanceBridge(const float DeltaSeconds)
{
    if (PackagedPerformanceRequest.View == ELBBodyShopPackagedPerformanceView::None
        || PackagedPerformancePhase == EPackagedPerformancePhase::None)
        return;
    PackagedPerformanceElapsedSeconds += FMath::Max(0.0f, DeltaSeconds);
    if (PackagedPerformanceElapsedSeconds
        >= LBBodyShopPrototypeGameModePrivate::PackagedPerformanceTimeoutSeconds)
    {
        FinishPackagedPerformanceBridge(false,
            TEXT("PACKAGED PERFORMANCE TIMED OUT BEFORE EVIDENCE FINALISED"));
        return;
    }

    UWorld* World = GetWorld();
    ALBBodyShopPrototypeRuntime* Runtime = PrototypeBootstrap.IsValid()
        ? Cast<ALBBodyShopPrototypeRuntime>(PrototypeBootstrap->GetRuntimeActor()) : nullptr;
    if (PackagedPerformancePhase == EPackagedPerformancePhase::WaitRuntime)
    {
        if (!Runtime || !Runtime->IsRuntimeInitialised()) return;
        FString Reason;
        if (!ValidatePackagedPerformanceEnvironment(Reason))
        {
            FinishPackagedPerformanceBridge(false, Reason);
            return;
        }
        ALBBodyShopManagementPawn* Pawn =
            LBBodyShopPrototypeGameModePrivate::FindManagementPawn(World);
        if (!Pawn || !Pawn->FocusPrototypeProcess())
        {
            FinishPackagedPerformanceBridge(false,
                TEXT("PACKAGED PERFORMANCE COULD NOT FOCUS COMMISSIONED PROCESS"));
            return;
        }
        if (PackagedPerformanceRequest.View
            == ELBBodyShopPackagedPerformanceView::Management)
        {
            Pawn->SetPrototypeZoomInput(-4.0f);
        }
        PackagedPerformanceViewConfiguredWorldSeconds = World->GetTimeSeconds();
        PackagedPerformancePhase = EPackagedPerformancePhase::Warmup;
        PackagedPerformancePhaseFrames = 0;
        return;
    }

    ++PackagedPerformancePhaseFrames;
    if (PackagedPerformancePhase == EPackagedPerformancePhase::Warmup)
    {
        if (PackagedPerformancePhaseFrames
            < LBBodyShopPrototypeGameModePrivate::PackagedPerformanceWarmupFrames)
            return;
        if (!GEngine)
        {
            FinishPackagedPerformanceBridge(false,
                TEXT("PACKAGED PERFORMANCE ENGINE CONSOLE IS UNAVAILABLE"));
            return;
        }
        bool bAnyForcedLOD = false;
        FString Reason;
        if (!LBBodyShopPrototypeGameModePrivate::SnapshotPackagedPerformanceRendererLODs(
            World, PackagedPerformanceTargetSnapshot, PackagedPerformanceTargetMeshPaths,
            bAnyForcedLOD, PackagedPerformanceSceneViewWidth,
            PackagedPerformanceSceneViewHeight, PackagedPerformanceGlobalForcedLOD,
            PackagedPerformanceRegisteredSceneProxyCount,
            PackagedPerformanceViewConfiguredWorldSeconds,
            PackagedPerformanceLODSnapshotWorldSeconds, Reason)
            || !ValidatePackagedPerformanceTargetCounts(
                LBBodyShopPrototypeGameModePrivate::ExpectedPerformanceRobotCount,
                PackagedPerformanceTargetSnapshot.Num(),
                PackagedPerformanceTargetMeshPaths.Num(), bAnyForcedLOD, Reason))
        {
            FinishPackagedPerformanceBridge(false, Reason);
            return;
        }

        PackagedPerformanceProfileStem = FString::Printf(TEXT("LB_BodyShop_PackagedPerf_%s_%s"),
            *PackagedPerformanceRequest.Token,
            *LBBodyShopPrototypeGameModePrivate::PerformanceViewName(
                PackagedPerformanceRequest.View, false));
        GEngine->Exec(World, TEXT("csv.CompressionMode 0"));
        GEngine->Exec(World,
            *FString::Printf(TEXT("CsvProfile STARTFILE=%s"), *PackagedPerformanceProfileStem));
        GEngine->Exec(World, *FString::Printf(TEXT("CsvProfile FRAMES=%d"),
            LBBodyShopPrototypeGameModePrivate::PackagedPerformanceCaptureFrames));
        PackagedPerformancePhase = EPackagedPerformancePhase::CaptureCsv;
        PackagedPerformancePhaseFrames = 0;
        PackagedPerformanceStableFrames = 0;
        PackagedPerformanceLastFileSize = -1;
        return;
    }

    if (PackagedPerformancePhase == EPackagedPerformancePhase::CaptureCsv)
    {
        if (PackagedPerformancePhaseFrames
            < LBBodyShopPrototypeGameModePrivate::PackagedPerformanceCaptureFrames
                + LBBodyShopPrototypeGameModePrivate::PackagedPerformanceFinaliseMarginFrames)
            return;
        PackagedPerformancePhase = EPackagedPerformancePhase::FinaliseCsv;
        PackagedPerformancePhaseFrames = 0;
        return;
    }

    if (PackagedPerformancePhase == EPackagedPerformancePhase::FinaliseCsv)
    {
        const TArray<FString> Profiles = LBBodyShopPrototypeGameModePrivate::FindProfilingFiles(
            PackagedPerformanceProfileStem + TEXT(".csv"));
        if (Profiles.IsEmpty()) return;
        if (Profiles.Num() != 1)
        {
            FinishPackagedPerformanceBridge(false,
                TEXT("PACKAGED PERFORMANCE CSV PROFILE IS AMBIGUOUS"));
            return;
        }
        const int64 Bytes = IFileManager::Get().FileSize(*Profiles[0]);
        if (Bytes < 4096) return;
        if (Profiles[0] != PackagedPerformanceProfilePath
            || Bytes != PackagedPerformanceLastFileSize)
        {
            PackagedPerformanceProfilePath = Profiles[0];
            PackagedPerformanceLastFileSize = Bytes;
            PackagedPerformanceStableFrames = 0;
            return;
        }
        if (++PackagedPerformanceStableFrames
            < LBBodyShopPrototypeGameModePrivate::PackagedPerformanceFileStableFrames)
            return;

        FString Reason;
        if (!ValidatePackagedPerformanceEnvironment(Reason)
            || !WritePackagedPerformanceReceipt(PackagedPerformanceReceiptPath, Reason))
        {
            FinishPackagedPerformanceBridge(false, Reason);
            return;
        }
        FinishPackagedPerformanceBridge(true, FString());
    }
}

void ALBBodyShopPrototypeGameMode::FinishPackagedPerformanceBridge(const bool bPassed,
    const FString& FailureReason)
{
    UWorld* World = GetWorld();
    APlayerController* Controller = World ? World->GetFirstPlayerController() : nullptr;
    int32 ViewportX = -1;
    int32 ViewportY = -1;
    if (Controller) Controller->GetViewportSize(ViewportX, ViewportY);

    TArray<TSharedPtr<FJsonValue>> Targets;
    TSet<FString> MeshPaths;
    bool bAnyForcedLOD = false;
    FString IgnoredReason;
    if (!PackagedPerformanceTargetSnapshot.IsEmpty())
    {
        Targets = PackagedPerformanceTargetSnapshot;
        MeshPaths = PackagedPerformanceTargetMeshPaths;
    }
    else if (World)
    {
        LBBodyShopPrototypeGameModePrivate::BuildPackagedPerformanceTargetManifest(World,
            nullptr, -1.0f, -1.0f, Targets, MeshPaths, bAnyForcedLOD, IgnoredReason);
    }
    const FString ReceiptLeaf = PackagedPerformanceReceiptPath.IsEmpty()
        ? TEXT("none") : FPaths::GetCleanFilename(PackagedPerformanceReceiptPath);
    const FString Marker = BuildPackagedPerformanceMarker(PackagedPerformanceRequest.View,
        PackagedPerformanceRequest.Token, bPassed, FApp::GetGraphicsRHI(), ViewportX, ViewportY,
        bPassed ? LBBodyShopPrototypeGameModePrivate::PackagedPerformanceCaptureFrames : 0,
        Targets.Num(), MeshPaths.Num(), ReceiptLeaf, FailureReason);
    if (bPassed)
    {
        UE_LOG(LogTemp, Display, TEXT("%s"), *Marker);
    }
    else
    {
        UE_LOG(LogTemp, Error, TEXT("%s"), *Marker);
    }

    PackagedPerformancePhase = EPackagedPerformancePhase::None;
    PackagedPerformanceRequest.View = ELBBodyShopPackagedPerformanceView::None;
    if (PackagedValidationRequest.Mode == ELBBodyShopPackagedValidationMode::None)
        SetActorTickEnabled(false);
    if (GLog) GLog->Flush();
    FPlatformMisc::RequestExitWithStatus(false, static_cast<uint8>(bPassed ? 0 : 3),
        TEXT("BodyShopPackagedPerformanceLODValidation"));
}
#endif
