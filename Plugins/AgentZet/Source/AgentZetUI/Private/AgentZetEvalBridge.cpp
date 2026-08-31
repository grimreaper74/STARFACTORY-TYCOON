// Copyright AgentZet. All Rights Reserved.

#include "AgentZetEvalBridge.h"
#include "AgentZetChatSession.h"
#include "AgentZetCoreModule.h"
#include "AgentZetTypes.h"
#include "Widgets/SAgentZetMainPanel.h"
#include "Dom/JsonObject.h"
#include "Framework/Docking/TabManager.h"
#include "HAL/FileManager.h"
#include "Misc/CommandLine.h"
#include "Misc/DateTime.h"
#include "Misc/FileHelper.h"
#include "Misc/Guid.h"
#include "Misc/Parse.h"
#include "Misc/Paths.h"
#include "Policies/CondensedJsonPrintPolicy.h"
#include "Serialization/JsonSerializer.h"
#include "Serialization/JsonWriter.h"
#include "ShaderCompiler.h" // GShaderCompilingManager - quiescence gate
#include "AssetRegistry/IAssetRegistry.h" // registry scan state - quiescence gate

namespace AgentZetEvalBridgePrivate
{
	const TCHAR* RoleToString(EAgentZetMessageRole Role)
	{
		switch (Role)
		{
		case EAgentZetMessageRole::User:       return TEXT("user");
		case EAgentZetMessageRole::Assistant:  return TEXT("assistant");
		case EAgentZetMessageRole::System:     return TEXT("system");
		case EAgentZetMessageRole::ToolResult: return TEXT("tool_result");
		case EAgentZetMessageRole::Error:      return TEXT("error");
		default:                               return TEXT("none");
		}
	}
}

FAgentZetEvalBridge::~FAgentZetEvalBridge()
{
	Stop();
}

bool FAgentZetEvalBridge::IsEnabledOnCommandLine()
{
	return FParse::Param(FCommandLine::Get(), TEXT("AgentZetEvalBridge"));
}

void FAgentZetEvalBridge::Start()
{
	RootDir = FPaths::Combine(FPaths::ProjectSavedDir(), TEXT("AgentZetEval"));
	InboxDir = FPaths::Combine(RootDir, TEXT("inbox"));
	OutboxDir = FPaths::Combine(RootDir, TEXT("outbox"));
	IFileManager::Get().MakeDirectory(*InboxDir, /*Tree=*/true);
	IFileManager::Get().MakeDirectory(*OutboxDir, /*Tree=*/true);

	// Readiness marker: a fresh timestamp tells the outside harness this
	// editor boot has the bridge alive (a stale file from a previous run
	// is distinguishable by startedUtc).
	{
		TSharedRef<FJsonObject> Ready = MakeShared<FJsonObject>();
		Ready->SetStringField(TEXT("session"),
			FGuid::NewGuid().ToString(EGuidFormats::Digits).Left(12));
		Ready->SetStringField(TEXT("startedUtc"),
			FDateTime::UtcNow().ToIso8601());
		FString ReadyStr;
		TSharedRef<TJsonWriter<>> Writer =
			TJsonWriterFactory<>::Create(&ReadyStr);
		FJsonSerializer::Serialize(Ready, Writer);
		FFileHelper::SaveStringToFile(ReadyStr,
			*FPaths::Combine(RootDir, TEXT("bridge.ready")));
	}

	TickerHandle = FTSTicker::GetCoreTicker().AddTicker(
		FTickerDelegate::CreateSP(this, &FAgentZetEvalBridge::Tick), 0.25f);

	UE_LOG(LogAgentZet, Display,
		TEXT("EvalBridge: ACTIVE. Inbox: %s"), *InboxDir);
}

void FAgentZetEvalBridge::Stop()
{
	if (TickerHandle.IsValid())
	{
		FTSTicker::GetCoreTicker().RemoveTicker(TickerHandle);
		TickerHandle.Reset();
	}
	UnbindFromSession();
}

bool FAgentZetEvalBridge::Tick(float)
{
	if (ActiveEvalId.IsEmpty())
	{
		TryPickupPrompt();
	}
	else
	{
		// BRIDGE-SIDE TIMEOUT (2026-08-31). The HTTP client's own 600s
		// timeout does not fire OnAgentFinished, so without this an
		// eval whose request dies would never write its .done marker
		// and the outside harness would hang to ITS timeout knowing
		// nothing - discovered on the very first live eval, where a
		// VRAM-contended prefill outran the client budget. Slightly
		// longer than the client's timeout so a real response always
		// wins the race when one is coming. The client's local-provider
		// minimum is 1200s (AgentZetOpenAICompatClient), so this must
		// sit above THAT - at 660s the bridge undercut the client and
		// abandoned eval step4g while its request was still live.
		constexpr double MaxEvalSeconds = 1260.0;
		if (FPlatformTime::Seconds() - EvalStartSeconds > MaxEvalSeconds)
		{
			UE_LOG(LogAgentZet, Warning,
				TEXT("EvalBridge: eval '%s' exceeded %.0fs - finishing as bridge_timeout."),
				*ActiveEvalId, MaxEvalSeconds);
			FinishEval(TEXT("bridge_timeout"));
		}
	}
	return true; // keep ticking
}

void FAgentZetEvalBridge::TryPickupPrompt()
{
	TArray<FString> PromptFiles;
	IFileManager::Get().FindFiles(PromptFiles,
		*FPaths::Combine(InboxDir, TEXT("*.prompt.txt")), true, false);
	if (PromptFiles.Num() == 0)
	{
		return;
	}
	PromptFiles.Sort(); // deterministic pickup order

	// EDITOR QUIESCENCE GATE (2026-08-31). The Ollama model is half
	// CPU-offloaded on this machine; during editor boot the shader
	// workers and asset-registry scan starve inference to ~3 tok/s
	// (measured idle: 43 tok/s), and eval step4f timed out at 600 s on
	// a request that runs in 57 s on a quiet editor. Hold prompts until
	// the boot storm is over rather than launching evals into it.
	const bool bShadersBusy =
		GShaderCompilingManager && GShaderCompilingManager->IsCompiling();
	const bool bRegistryBusy =
		IAssetRegistry::Get() && IAssetRegistry::Get()->IsLoadingAssets();
	if (bShadersBusy || bRegistryBusy)
	{
		QuiescentSinceSeconds = 0.0;
		const double Now = FPlatformTime::Seconds();
		if (Now - LastQuiescenceLogSeconds > 15.0)
		{
			LastQuiescenceLogSeconds = Now;
			UE_LOG(LogAgentZet, Log,
				TEXT("EvalBridge: prompt waiting - editor busy (shaders=%d, registry scan=%d)."),
				bShadersBusy ? GShaderCompilingManager->GetNumRemainingJobs() : 0,
				bRegistryBusy ? 1 : 0);
		}
		return;
	}
	{
		// Require sustained quiet - shader batches arrive in waves, and
		// a momentary empty queue between waves is not quiescence. 30 s
		// because the shader/registry signals do not cover everything
		// the boot storm does (DDC churn, map load, first-frame stalls):
		// eval step4g cleared both signals 8 s after editor start and
		// still starved the CPU-offloaded model.
		const double Now = FPlatformTime::Seconds();
		if (QuiescentSinceSeconds <= 0.0)
		{
			QuiescentSinceSeconds = Now;
		}
		if (Now - QuiescentSinceSeconds < 30.0)
		{
			return;
		}
	}

	// A live panel is required - it owns the prompt path (system prompt,
	// toolset selection, session). Summon the tab if none exists yet,
	// throttled so a failing spawner does not spam.
	TSharedPtr<SAgentZetMainPanel> Panel =
		SAgentZetMainPanel::GetLiveInstanceForEval();
	if (!Panel.IsValid())
	{
		const double Now = FPlatformTime::Seconds();
		if (Now - LastTabInvokeSeconds > 2.0)
		{
			LastTabInvokeSeconds = Now;
			FGlobalTabmanager::Get()->TryInvokeTab(FName(TEXT("AgentZetPanel")));
			UE_LOG(LogAgentZet, Log,
				TEXT("EvalBridge: prompt waiting - summoning the AgentZet tab."));
		}
		return;
	}

	TSharedPtr<FAgentZetChatSession> Session =
		Panel->GetActiveChatSessionForEval();
	if (!Session.IsValid() || Session->IsProcessing())
	{
		return; // wait for idle
	}

	// FRESH TAB PER EVAL (2026-08-31). The panel restores prior task
	// tabs at startup, and the first live eval inherited a 35-message
	// stale history - tens of thousands of prefill tokens on a
	// VRAM-contended GPU, plus behavioral contamination from
	// conversations that predate the tool-calling repairs. Each eval
	// gets a clean conversation; the fresh tab's session becomes the
	// one we bind and submit to.
	const FString FreshEvalId = FPaths::GetBaseFilename(PromptFiles[0]);
	Panel->BeginFreshTabForEval(FString::Printf(TEXT("Eval %s"), *FreshEvalId));
	Session = Panel->GetActiveChatSessionForEval();
	if (!Session.IsValid())
	{
		UE_LOG(LogAgentZet, Warning,
			TEXT("EvalBridge: fresh eval tab has no chat session - waiting."));
		return;
	}

	const FString PromptPath = FPaths::Combine(InboxDir, PromptFiles[0]);
	FString PromptText;
	if (!FFileHelper::LoadFileToString(PromptText, *PromptPath))
	{
		UE_LOG(LogAgentZet, Warning,
			TEXT("EvalBridge: could not read %s - skipping."), *PromptPath);
		IFileManager::Get().Delete(*PromptPath);
		return;
	}
	IFileManager::Get().Delete(*PromptPath);
	PromptText.TrimStartAndEndInline();
	if (PromptText.IsEmpty())
	{
		return;
	}

	ActiveEvalId = FPaths::GetBaseFilename(PromptFiles[0]); // strips .txt
	ActiveEvalId.RemoveFromEnd(TEXT(".prompt"));
	EvalStartSeconds = FPlatformTime::Seconds();
	MessageCount = 0;
	// Truncate any stale transcript from an earlier run of the same id.
	IFileManager::Get().Delete(
		*FPaths::Combine(OutboxDir, ActiveEvalId + TEXT(".jsonl")));
	IFileManager::Get().Delete(
		*FPaths::Combine(OutboxDir, ActiveEvalId + TEXT(".done")));

	BindToSession(Session);

	{
		TSharedRef<FJsonObject> Line = MakeShared<FJsonObject>();
		Line->SetStringField(TEXT("type"), TEXT("prompt"));
		Line->SetStringField(TEXT("text"), PromptText);
		Line->SetStringField(TEXT("utc"), FDateTime::UtcNow().ToIso8601());
		WriteTranscriptLine(Line);
	}

	UE_LOG(LogAgentZet, Display,
		TEXT("EvalBridge: running eval '%s' (%d chars)."),
		*ActiveEvalId, PromptText.Len());
	Panel->SubmitPromptForEval(PromptText);
}

void FAgentZetEvalBridge::BindToSession(
	const TSharedPtr<FAgentZetChatSession>& Session)
{
	UnbindFromSession();
	BoundSession = Session;
	MessageAddedHandle = Session->GetOnMessageAdded().AddSP(
		this, &FAgentZetEvalBridge::HandleMessageAdded);
	AgentFinishedHandle = Session->GetOnAgentFinished().AddSP(
		this, &FAgentZetEvalBridge::HandleAgentFinished);
	ApprovalHandle = Session->GetOnToolRequiresApproval().AddSP(
		this, &FAgentZetEvalBridge::HandleToolRequiresApproval);
	ToolResultHandle = Session->GetOnToolResultRecorded().AddSP(
		this, &FAgentZetEvalBridge::HandleToolResultRecorded);
}

void FAgentZetEvalBridge::UnbindFromSession()
{
	if (TSharedPtr<FAgentZetChatSession> Session = BoundSession.Pin())
	{
		Session->GetOnMessageAdded().Remove(MessageAddedHandle);
		Session->GetOnAgentFinished().Remove(AgentFinishedHandle);
		Session->GetOnToolRequiresApproval().Remove(ApprovalHandle);
		Session->GetOnToolResultRecorded().Remove(ToolResultHandle);
	}
	BoundSession.Reset();
	MessageAddedHandle.Reset();
	AgentFinishedHandle.Reset();
	ApprovalHandle.Reset();
	ToolResultHandle.Reset();
}

void FAgentZetEvalBridge::HandleMessageAdded(const FAgentZetMessage& Message)
{
	if (ActiveEvalId.IsEmpty())
	{
		return;
	}
	++MessageCount;
	TSharedRef<FJsonObject> Line = MakeShared<FJsonObject>();
	Line->SetStringField(TEXT("type"), TEXT("message"));
	Line->SetStringField(TEXT("role"),
		AgentZetEvalBridgePrivate::RoleToString(Message.Role));
	Line->SetStringField(TEXT("content"), Message.Content);
	Line->SetStringField(TEXT("utc"), FDateTime::UtcNow().ToIso8601());
	WriteTranscriptLine(Line);
}

void FAgentZetEvalBridge::HandleAgentFinished(const FString& Reason)
{
	if (ActiveEvalId.IsEmpty())
	{
		return;
	}
	FinishEval(Reason);
}

void FAgentZetEvalBridge::HandleToolResultRecorded(const FString& ToolName,
	const FString& ResultContent, bool bIsError)
{
	if (ActiveEvalId.IsEmpty())
	{
		return;
	}
	TSharedRef<FJsonObject> Line = MakeShared<FJsonObject>();
	Line->SetStringField(TEXT("type"), TEXT("tool_result"));
	Line->SetStringField(TEXT("tool"), ToolName);
	Line->SetStringField(TEXT("content"), ResultContent);
	Line->SetBoolField(TEXT("error"), bIsError);
	Line->SetStringField(TEXT("utc"), FDateTime::UtcNow().ToIso8601());
	WriteTranscriptLine(Line);
}

void FAgentZetEvalBridge::HandleToolRequiresApproval(const FAgentZetActionPlan&)
{
	if (ActiveEvalId.IsEmpty())
	{
		return;
	}
	// Unattended run: approve and continue, on the same path the UI's
	// approve button takes (ProcessToolCallQueue). Recorded so the
	// transcript shows exactly where human judgment was bypassed.
	{
		TSharedRef<FJsonObject> Line = MakeShared<FJsonObject>();
		Line->SetStringField(TEXT("type"), TEXT("auto_approved"));
		Line->SetStringField(TEXT("utc"), FDateTime::UtcNow().ToIso8601());
		WriteTranscriptLine(Line);
	}
	UE_LOG(LogAgentZet, Display,
		TEXT("EvalBridge: auto-approving tool batch for eval '%s'."),
		*ActiveEvalId);
	if (TSharedPtr<FAgentZetChatSession> Session = BoundSession.Pin())
	{
		Session->ProcessToolCallQueue();
	}
}

void FAgentZetEvalBridge::WriteTranscriptLine(
	const TSharedRef<FJsonObject>& Line)
{
	// Condensed policy: the default TJsonWriter pretty-prints across
	// multiple lines, which breaks one-object-per-line JSONL consumers
	// (found the hard way by the first harness parse).
	FString LineStr;
	TSharedRef<TJsonWriter<TCHAR, TCondensedJsonPrintPolicy<TCHAR>>> Writer =
		TJsonWriterFactory<TCHAR, TCondensedJsonPrintPolicy<TCHAR>>::Create(&LineStr);
	FJsonSerializer::Serialize(Line, Writer);
	LineStr += LINE_TERMINATOR;
	FFileHelper::SaveStringToFile(LineStr,
		*FPaths::Combine(OutboxDir, ActiveEvalId + TEXT(".jsonl")),
		FFileHelper::EEncodingOptions::ForceUTF8WithoutBOM,
		&IFileManager::Get(), FILEWRITE_Append);
}

void FAgentZetEvalBridge::FinishEval(const FString& Reason)
{
	const double Seconds = FPlatformTime::Seconds() - EvalStartSeconds;
	{
		TSharedRef<FJsonObject> Line = MakeShared<FJsonObject>();
		Line->SetStringField(TEXT("type"), TEXT("finished"));
		Line->SetStringField(TEXT("reason"), Reason);
		Line->SetNumberField(TEXT("messages"), MessageCount);
		Line->SetNumberField(TEXT("seconds"), Seconds);
		WriteTranscriptLine(Line);
	}

	TSharedRef<FJsonObject> Done = MakeShared<FJsonObject>();
	Done->SetStringField(TEXT("reason"), Reason);
	Done->SetNumberField(TEXT("messages"), MessageCount);
	Done->SetNumberField(TEXT("seconds"), Seconds);
	FString DoneStr;
	TSharedRef<TJsonWriter<>> Writer = TJsonWriterFactory<>::Create(&DoneStr);
	FJsonSerializer::Serialize(Done, Writer);
	// .done is written LAST, after the transcript's finished line - the
	// outside harness polls for it and then reads a complete transcript.
	FFileHelper::SaveStringToFile(DoneStr,
		*FPaths::Combine(OutboxDir, ActiveEvalId + TEXT(".done")));

	UE_LOG(LogAgentZet, Display,
		TEXT("EvalBridge: eval '%s' finished (%s) - %d messages, %.1fs."),
		*ActiveEvalId, *Reason, MessageCount, Seconds);

	UnbindFromSession();
	ActiveEvalId.Reset();
}
