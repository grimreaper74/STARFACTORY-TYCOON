// Copyright AgentZet. All Rights Reserved.

#include "AgentZetChatSession.h"
#include "AgentZetConversationManager.h"
#include "AgentZetActionRouter.h"
#include "AgentZetExecutionJournal.h"
#include "AgentZetToolRepetitionDetector.h"
#include "AgentZetFileContextTracker.h"
#include "AgentZetContextManager.h"
#include "AgentZetToolSchemaRegistry.h"
#include "AgentZetCheckpointManager.h"
#include "AgentZetSettings.h"
#include "AgentZetCoreModule.h"
#include "AgentZetAutoApprovalHandler.h"
#include "Misc/MessageDialog.h"
#include "Serialization/JsonSerializer.h"
#include "Serialization/JsonWriter.h"


FAgentZetChatSession::FAgentZetChatSession()
{
}

FAgentZetChatSession::~FAgentZetChatSession()
{
}

void FAgentZetChatSession::SetState(EConversationState NewState)
{
	if (CurrentState == NewState) return;

	UE_LOG(LogAgentZet, Log, TEXT("ChatSession: State %d → %d"), (int32)CurrentState, (int32)NewState);
	CurrentState = NewState;
	OnConversationStateChanged.Broadcast(NewState);
}

void FAgentZetChatSession::Initialize(TSharedPtr<IAgentZetLLMClient> InLLMClient,
									   TSharedPtr<FAgentZetConversationManager> InConvManager,
									   TSharedPtr<FAgentZetActionRouter> InActionRouter,
									   TSharedPtr<FAgentZetExecutionJournal> InExecutionJournal,
									   TSharedPtr<FAgentZetToolRepetitionDetector> InToolRepetitionDetector,
									   TSharedPtr<FAgentZetFileContextTracker> InFileContextTracker,
									   TSharedPtr<FAgentZetContextManager> InContextManager,
									   TSharedPtr<FAgentZetToolSchemaRegistry> InToolSchemaRegistry,
									   TSharedPtr<FAgentZetCheckpointManager> InCheckpointManager)
{
	LLMClient = InLLMClient;
	ConversationManager = InConvManager;
	ActionRouter = InActionRouter;
	ExecutionJournal = InExecutionJournal;
	ToolRepetitionDetector = InToolRepetitionDetector;
	FileContextTracker = InFileContextTracker;
	ContextManager = InContextManager;
	ToolSchemaRegistry = InToolSchemaRegistry;
	CheckpointManager = InCheckpointManager;
}

void FAgentZetChatSession::ProcessToolCallQueue()
{
	// HARD ITERATION CAP (2026-08-31). The previous "Roo Code approach"
	// of NO limit relied on the auto-approval cost gate as its safety
	// net - which is inert for a free local model ($0 per request), so a
	// looping qwen3-coder session was bounded by nothing but the user's
	// patience. 60 tool batches is far beyond any legitimate task this
	// plugin runs today; hitting it means the loop is stuck, and an
	// honest stop with the count beats burning the GPU all night.
	static constexpr int32 MaxAgenticIterations = 60;
	if (AgenticLoopCount >= MaxAgenticIterations)
	{
		UE_LOG(LogAgentZet, Warning,
			TEXT("ChatSession: agentic loop hit the %d-iteration cap - stopping."),
			MaxAgenticIterations);
		ToolCallQueue.Empty();
		bInAgenticLoop = false;
		AgenticLoopCount = 0;
		SetState(EConversationState::Idle);
		FAgentZetMessage CapMsg(EAgentZetMessageRole::System,
			FString::Printf(TEXT("⏹ Task stopped: reached the %d-iteration safety cap without completing. Review the transcript and re-prompt with a narrower instruction."),
				MaxAgenticIterations));
		OnMessageAdded.Broadcast(CapMsg);
		OnAgentFinished.Broadcast(TEXT("Stopped at iteration cap."));
		return;
	}

	// The loop otherwise continues until:
	//   1. Claude responds with text only (no tool_use) — task is done
	//   2. Auto-approval limits (cost + request count) are exceeded — asks user
	//   3. User clicks Stop
	//   4. Context window fills up (handled by context management)

	// Reset consecutive no-tool counter since we have tool calls
	ConsecutiveNoToolCount = 0;

	// Phase 3.1: Check auto-approval limits (request count + cost cap)
	const UAgentZetDeveloperSettings* Settings = UAgentZetDeveloperSettings::Get();
	if (Settings)
	{
		FAgentZetAutoApprovalCheck Check = AutoApprovalHandler.CheckLimits(
			Settings->MaxConsecutiveAutoApprovedRequests,
			Settings->MaxAutoApprovedCostDollars,
			LastRequestCost);

		if (Check.bRequiresApproval)
		{
			// Show prompt to user
			FAgentZetActionPlan DummyPlan;
			OnToolRequiresApproval.Broadcast(DummyPlan);
			return; // Wait for user approval before continuing
		}
	}

	// Phase 5.2: Create a checkpoint snapshot before executing this tool batch
	if (Settings && Settings->bEnableAutoBackup && CheckpointManager.IsValid())
	{
		FAgentZetCheckpoint CP;
		const FString Description = FString::Printf(TEXT("Before tool batch %d"), AgenticLoopCount);
		CheckpointManager->SaveCheckpoint(Description, AgenticLoopCount, CP);
		// Should also do FAgentZetBackupManager things here if implemented
	}

	// FIX (GitHub Issue #28): Guard against late arrivals after StopAgenticLoop().
	// In non-streaming mode (Ollama/LM Studio), the HTTP response arrives 30-60s
	// after Stop was pressed. Without this guard, the stop state gets overwritten.
	if (bStopRequested)
	{
		UE_LOG(LogAgentZet, Log, TEXT("ChatSession: ProcessToolCallQueue() — stop was requested before processing. Aborting."));
		bStopRequested = false;
		bInAgenticLoop = false;
		ToolCallQueue.Empty();
		SetState(EConversationState::Idle);
		OnStatusUpdated.Broadcast(TEXT(""));
		return;
	}

	bInAgenticLoop = true;
	SetState(EConversationState::Streaming);
	AgenticLoopCount++;

	// Record this batch in auto-approval tracking
	AutoApprovalHandler.RecordBatch(LastRequestCost);

	UE_LOG(LogAgentZet, Log, TEXT("MainPanel: Processing %d tool calls (loop %d)"),
		ToolCallQueue.Num(), AgenticLoopCount);

	TArray<FAgentZetToolCall> ActiveToolCalls = MoveTemp(ToolCallQueue);
	ToolCallQueue.Empty();
	for (const FAgentZetToolCall& ToolCall : ActiveToolCalls)
	{
		// Check if stop was requested between tool calls
		if (bStopRequested)
		{
			UE_LOG(LogAgentZet, Log, TEXT("ChatSession: Stop requested — aborting remaining %d tool call(s)."),
				ActiveToolCalls.Num());
			break;
		}

		// Phase 1: Check for tool repetition (identical consecutive calls)
		if (ToolRepetitionDetector.IsValid())
		{
			FAgentZetToolRepetitionCheck RepCheck = ToolRepetitionDetector->Check(ToolCall);
			if (!RepCheck.bAllowExecution)
			{
				// Block this tool call — show warning dialog
				const FText Title = FText::FromString(TEXT("AgentZet — Repetition Loop Detected"));
				const FText Msg = FText::FromString(RepCheck.WarningMessage);
				EAppReturnType::Type UserResponse = FMessageDialog::Open(EAppMsgType::YesNo, Msg, Title);

				if (UserResponse != EAppReturnType::Yes)
				{
					// User chose to stop
					ActiveToolCalls.Empty();
					bInAgenticLoop = false;
					AgenticLoopCount = 0;
					SetState(EConversationState::Idle);
					FAgentZetMessage StopMsg(EAgentZetMessageRole::System,
						TEXT("⏹ Task stopped: AI repetition loop detected."));
					OnMessageAdded.Broadcast(StopMsg);
					// Notify stop
					OnAgentFinished.Broadcast(TEXT("Task stopped: AI repetition loop detected."));
					return;
				}
				// User chose to allow one more try — continue
			}
		}

		bool bIsAttemptCompletion = (ToolCall.ToolName == TEXT("attempt_completion"));

		FAgentZetMessage ToolMsg;

		if (!bIsAttemptCompletion)
		{
			// Add a collapsible "Executing" system message; body will be filled with the result below
			FString ExecutingParamsStr;
			if (ToolCall.InputParams.IsValid())
			{
				TSharedRef<TJsonWriter<>> ParamsWriter = TJsonWriterFactory<>::Create(&ExecutingParamsStr);
				FJsonSerializer::Serialize(ToolCall.InputParams.ToSharedRef(), ParamsWriter);
			}
			ToolMsg = FAgentZetMessage(EAgentZetMessageRole::Assistant,
				FString::Printf(TEXT("🔧 Executing: %s\n%s\n\n"), *ToolCall.ToolName, *ExecutingParamsStr));
			ToolMsg.bIsCollapsible = true;
			OnMessageAdded.Broadcast(ToolMsg);
		}

		bool bIsError = false;
		FString ResultContent = ExecuteToolCall(ToolCall, bIsError);

		FAgentZetMessage& ToolResultMsg = ConversationManager->AddToolResultMessage(
			ToolCall.ToolUseId, ResultContent, bIsError);

		if (bIsError)
		{
			ToolResultMsg.ToolName = TEXT("error");
		}

		if (!bIsAttemptCompletion)
		{
			// Append the full result into the previously added executing message (no truncation)
			FString ResultToAppend = ResultContent;
			if (bIsError)
			{
				ResultToAppend = FString::Printf(TEXT("❌ %s"), *ResultContent);
			}
			else
			{
				ResultToAppend = FString::Printf(TEXT("✅ %s"), *ResultContent);
			}
			OnMessageUpdated.Broadcast(ToolMsg.MessageId, ResultToAppend, EAgentZetMessageRole::Assistant);
		}
	}

	ActiveToolCalls.Empty();
	OnSaveTabsToDisk.ExecuteIfBound();

	if (!bInAgenticLoop || bStopRequested)
	{
		UE_LOG(LogAgentZet, Log, TEXT("MainPanel: Agentic loop was terminated (%s). Not continuing."),
			bStopRequested ? TEXT("stop requested") : TEXT("attempt_completion"));
		bStopRequested = false;
		bInAgenticLoop = false;
		SetState(EConversationState::Idle);
		OnStatusUpdated.Broadcast(TEXT(""));
		return;
	}

	ContinueAgenticLoop();
}

void FAgentZetChatSession::StopAgenticLoop()
{
	UE_LOG(LogAgentZet, Log, TEXT("ChatSession: StopAgenticLoop() called. State=%d, bInAgenticLoop=%d"),
		(int32)CurrentState, bInAgenticLoop);
	
	SetState(EConversationState::Cancelling);

	bStopRequested = true;
	bInAgenticLoop = false;
	AgenticLoopCount = 0;
	ConsecutiveNoToolCount = 0;
	ToolCallQueue.Empty();

	// FIX (GitHub Issue #28): Cancel the in-flight HTTP request.
	// Without this, non-streaming local providers (Ollama/LM Studio) keep the
	// request running for 30-60s after the user clicks Stop. When the response
	// finally arrives, OnToolCallReceived() adds new tool calls, and
	// ProcessToolCallQueue() resets bStopRequested=false — overwriting the stop.
	// CancelRequest() aborts the HTTP request immediately, preventing late callbacks.
	if (LLMClient.IsValid() && LLMClient->IsRequestInFlight())
	{
		UE_LOG(LogAgentZet, Log, TEXT("ChatSession: Cancelling in-flight LLM request."));
		LLMClient->CancelRequest();
	}

	SetState(EConversationState::Idle);
	OnStatusUpdated.Broadcast(TEXT(""));
	OnAgentFinished.Broadcast(TEXT("Stopped by user."));
}

void FAgentZetChatSession::ResumeTask(const FDateTime& InterruptedAt)
{
	if (!ConversationManager.IsValid() || !LLMClient.IsValid())
	{
		UE_LOG(LogAgentZet, Error, TEXT("ChatSession: ResumeTask() — ConversationManager or LLMClient is null."));
		return;
	}

	UE_LOG(LogAgentZet, Log, TEXT("ChatSession: ResumeTask() — Resuming interrupted task."));

	// Step 1: Inject synthetic tool_result messages for orphaned tool_use blocks.
	// This prevents API errors from strict providers (Anthropic requires tool_result
	// for every tool_use; OpenAI rejects orphaned function calls).
	const int32 SyntheticCount = ConversationManager->InjectSyntheticToolResultsForOrphans();
	if (SyntheticCount > 0)
	{
		FAgentZetMessage SyntheticNotice(EAgentZetMessageRole::System,
			FString::Printf(TEXT("🔧 Injected %d synthetic tool result(s) for interrupted tool calls."), SyntheticCount));
		OnMessageAdded.Broadcast(SyntheticNotice);
	}

	// Step 2: Build time-aware resumption prompt.
	// Follows the Discovery Hypothesis Pattern — forces the AI to replan.
	FString TimeAgoStr;
	{
		const FTimespan Elapsed = FDateTime::UtcNow() - InterruptedAt;
		const double TotalMinutes = Elapsed.GetTotalMinutes();

		if (TotalMinutes < 1.0)
		{
			TimeAgoStr = TEXT("moments");
		}
		else if (TotalMinutes < 60.0)
		{
			TimeAgoStr = FString::Printf(TEXT("%.0f minute(s)"), TotalMinutes);
		}
		else if (TotalMinutes < 1440.0) // 24 hours
		{
			const double Hours = TotalMinutes / 60.0;
			TimeAgoStr = FString::Printf(TEXT("%.1f hour(s)"), Hours);
		}
		else
		{
			const double Days = TotalMinutes / 1440.0;
			TimeAgoStr = FString::Printf(TEXT("%.1f day(s)"), Days);
		}
	}

	FString ResumptionPrompt = FString::Printf(
		TEXT("[TASK RESUMPTION] This task was interrupted %s ago. The project state may have changed since your last action.\n")
		TEXT("1. Review your todo list to see remaining items.\n")
		TEXT("2. If your last tool call did not receive a result, assume it failed.\n")
		TEXT("3. Verify the current state of relevant files/assets before making changes.\n")
		TEXT("Continue with the remaining work."),
		*TimeAgoStr);

	// Step 3: Inject the resumption prompt as a USER message (so the AI sees it
	// as a continuation of the conversation, not system-level).
	ConversationManager->AddUserMessage(ResumptionPrompt);

	FAgentZetMessage ResumptionMsg(EAgentZetMessageRole::User, ResumptionPrompt);
	OnMessageAdded.Broadcast(ResumptionMsg);

	// Step 4: Reset loop state and start the agentic loop.
	bInAgenticLoop = false;
	bStopRequested = false;
	AgenticLoopCount = 0;
	ConsecutiveNoToolCount = 0;
	ToolCallQueue.Empty();

	OnSaveTabsToDisk.ExecuteIfBound();

	// Step 5: Send the conversation to the LLM (same as initial prompt submission).
	ContinueAgenticLoop();

	UE_LOG(LogAgentZet, Log,
		TEXT("ChatSession: ResumeTask() — Resumption prompt injected (%s ago). Agentic loop restarted."),
		*TimeAgoStr);
}

void FAgentZetChatSession::ContinueAgenticLoop()
{
	// Check stop flag before making a new API call
	if (bStopRequested)
	{
		UE_LOG(LogAgentZet, Log, TEXT("ChatSession: ContinueAgenticLoop() aborted — stop was requested."));
		bStopRequested = false;
		bInAgenticLoop = false;
		SetState(EConversationState::Idle);
		OnStatusUpdated.Broadcast(TEXT(""));
		return;
	}

	const UAgentZetDeveloperSettings* Settings = UAgentZetDeveloperSettings::Get();
	if (!Settings) return;

	FAgentZetMessage StreamingMsg(EAgentZetMessageRole::Assistant, TEXT(""));
	StreamingMsg.bIsStreaming = true;
	CurrentStreamingMessageId = StreamingMsg.MessageId;
	OnMessageAdded.Broadcast(StreamingMsg);

	// Phase 2: Use mode-filtered schemas (local provider: essential set only)
	const UAgentZetDeveloperSettings* LoopSettings = UAgentZetDeveloperSettings::Get();
	const bool bIsLocalLoop = LoopSettings &&
		(LoopSettings->ActiveProvider == EAgentZetProvider::Ollama ||
			LoopSettings->ActiveProvider == EAgentZetProvider::LMStudio);

	TArray<TSharedPtr<FJsonObject>> ToolSchemas;
	if (ToolSchemaRegistry.IsValid())
	{
		// Phase 3: Two-tier tool loading — Tier 1 for cloud, essential for local
		ToolSchemas = bIsLocalLoop
			? ToolSchemaRegistry->GetEssentialSchemas()
			: ToolSchemaRegistry->GetTier1Schemas();

		// PHASE 1 FIX: Append dynamically discovered tools (from get_tool_info / list_tools_in_category)
		// This ensures strict-mode providers (OpenAI Responses API) can actually CALL the discovered tools.
		if (DynamicallyLoadedTools.Num() > 0)
		{
			// Build a set of already-included tool names to avoid duplicates
			TSet<FString> IncludedNames;
			for (const auto& Schema : ToolSchemas)
			{
				FString Name;
				if (Schema->TryGetStringField(TEXT("name"), Name))
				{
					IncludedNames.Add(Name);
				}
			}

			int32 InjectedCount = 0;
			for (const FString& DynToolName : DynamicallyLoadedTools)
			{
				if (!IncludedNames.Contains(DynToolName))
				{
					TSharedPtr<FJsonObject> DynSchema = ToolSchemaRegistry->GetSchemaByName(DynToolName);
					if (DynSchema.IsValid())
					{
						ToolSchemas.Add(DynSchema);
						InjectedCount++;
					}
				}
			}

			if (InjectedCount > 0)
			{
				UE_LOG(LogAgentZet, Log, TEXT("ChatSession: ContinueAgenticLoop injected %d dynamically-loaded tools (total tools: %d)."),
					InjectedCount, ToolSchemas.Num());
			}
		}
	}

	// Use GetEffectiveHistory() -- respects condense/truncation tags
	TArray<FAgentZetMessage> EffectiveHistory = ConversationManager->GetEffectiveHistory();

	// Phase 2: Build per-message environment details and inject into last message
	// This appends fresh editor state (open files, selected actors, errors, etc.)
	// to each API call without growing the static system prompt.
	FString EnvDetails;
	if (OnGetEnvironmentDetailsString.IsBound())
	{
		EnvDetails = OnGetEnvironmentDetailsString.Execute();
	}
	if (!EnvDetails.IsEmpty() && EffectiveHistory.Num() > 0)
	{
		// Append to the last message in the history
		FAgentZetMessage& LastMsg = EffectiveHistory.Last();
		if (LastMsg.Role == EAgentZetMessageRole::User ||
			LastMsg.Role == EAgentZetMessageRole::ToolResult)
		{
			if (!LastMsg.Content.IsEmpty())
			{
				LastMsg.Content += TEXT("\n\n");
			}
			LastMsg.Content += EnvDetails;
		}
	}

	// Phase 2: Mode-aware system prompt (includes role definition for current mode)
	FString SystemPrompt;
	if (OnGetSystemPromptString.IsBound())
	{
		SystemPrompt = OnGetSystemPromptString.Execute();
	}

	LLMClient->SendMessage(
		EffectiveHistory,
		SystemPrompt,
		ToolSchemas
	);

	UE_LOG(LogAgentZet, Log, TEXT("MainPanel: Agentic loop iteration %d -- re-sending conversation to Claude (%d effective messages, %d schemas)."),
		AgenticLoopCount,
		EffectiveHistory.Num(),
		ToolSchemas.Num());
}

FString FAgentZetChatSession::ExecuteToolCall(const FAgentZetToolCall& ToolCall, bool& bOutIsError)
{
	bOutIsError = false;
	FDateTime StartTime = FDateTime::UtcNow();

	// ---- MALFORMED-ARGUMENTS SHORT-CIRCUIT (2026-08-31) ----
	// The client used to coerce unparseable argument JSON to an empty
	// object silently, so the tool executed with no arguments and the
	// model was never told its own JSON was the problem - it then blamed
	// the tool and retried something else. Nothing runs on bad
	// arguments; the model gets the exact text back and a request to
	// re-emit valid JSON for the same tool.
	if (!ToolCall.ArgsParseError.IsEmpty())
	{
		bOutIsError = true;
		return FString::Printf(
			TEXT("INVALID ARGUMENTS for '%s' - the tool was NOT executed because your arguments were not valid JSON.\n")
			TEXT("Your raw arguments were: %s\n")
			TEXT("Call '%s' again with arguments as a single valid JSON object."),
			*ToolCall.ToolName, *ToolCall.ArgsParseError, *ToolCall.ToolName);
	}

	// Meta tools are temporarily executed locally without UI components hooks
	// or through the ActionRouter directly. Since we don't have the widget ptrs anymore,
	// they should be implemented inside FAgentZetChatSession or registered to ActionRouter

	// ---- Meta-tool: update_todo_list (handled locally, not routed to action executors) ----
	if (ToolCall.ToolName == TEXT("update_todo_list"))
	{
		if (OnHandleUpdateTodoList.IsBound())
		{
			return OnHandleUpdateTodoList.Execute(ToolCall);
		}
		return TEXT("");
	}

	if (ToolCall.ToolName == TEXT("attempt_completion"))
	{
		bInAgenticLoop = false; // Stop the loop
		OnAgentFinished.Broadcast(TEXT("Task completed."));

		if (OnHandleAttemptCompletion.IsBound())
		{
			return OnHandleAttemptCompletion.Execute(ToolCall);
		}

		return TEXT("");
	}

	// ---- Meta-tool: ask_followup_question (pauses the loop, presents question to user) ----
	if (ToolCall.ToolName == TEXT("ask_followup_question"))
	{
		// Stop the agentic loop — the user needs to respond before continuing
		bInAgenticLoop = false;

		FString Question;
		if (ToolCall.InputParams.IsValid())
		{
			ToolCall.InputParams->TryGetStringField(TEXT("question"), Question);
		}

		if (Question.IsEmpty())
		{
			Question = TEXT("The AI wants to ask a follow-up question but didn't provide one.");
		}

		// Build a formatted message with the question and suggested answers
		FString FormattedQuestion = FString::Printf(TEXT("❓ %s"), *Question);

		const TArray<TSharedPtr<FJsonValue>>* FollowUps = nullptr;
		if (ToolCall.InputParams.IsValid() && ToolCall.InputParams->TryGetArrayField(TEXT("follow_up"), FollowUps))
		{
			FormattedQuestion += TEXT("\n\nSuggested answers:");
			int32 Index = 1;
			for (const TSharedPtr<FJsonValue>& FUVal : *FollowUps)
			{
				const TSharedPtr<FJsonObject>* FUObj = nullptr;
				if (FUVal->TryGetObject(FUObj))
				{
					FString Text;
					(*FUObj)->TryGetStringField(TEXT("text"), Text);
					if (!Text.IsEmpty())
					{
						FormattedQuestion += FString::Printf(TEXT("\n  %d. %s"), Index++, *Text);
					}
				}
			}
		}

		// Notify UI that the agent is waiting for user input
		OnAgentFinished.Broadcast(TEXT("Waiting for user response."));

		UE_LOG(LogAgentZet, Log, TEXT("ChatSession: ask_followup_question — pausing loop. Question: %s"), *Question);
		return FormattedQuestion;
	}

	// ---- Phase 2 Meta-tool: switch_mode ----
	if (ToolCall.ToolName == TEXT("switch_mode"))
	{
		if (OnHandleSwitchMode.IsBound())
		{
			return OnHandleSwitchMode.Execute(ToolCall);
		}
		return TEXT("");
	}

	// ---- Phase 3 Meta-tool: new_task (task delegation) ----
	if (ToolCall.ToolName == TEXT("new_task"))
	{
		return TEXT("");
	}

	// ---- Phase 4 Meta-tool: skill ----
	if (ToolCall.ToolName == TEXT("skill"))
	{
		return TEXT("");
	}

	// ---- Discovery Meta-tools: get_tool_info / list_tools_in_category (Phase 3 token optimization) ----
	// PHASE 1 FIX (GitHub Issue #20 discovery loop): When the model calls get_tool_info,
	// we register the discovered tool in DynamicallyLoadedTools so it gets added to the
	// actual tools array on the NEXT API call. This fixes the loop where strict-mode
	// providers (OpenAI Responses API) could see the schema as text but couldn't call
	// the tool because it wasn't in the tools array.
	if (ToolCall.ToolName == TEXT("get_tool_info"))
	{
		if (ToolSchemaRegistry.IsValid() && ToolCall.InputParams.IsValid())
		{
			FString RequestedTool;
			ToolCall.InputParams->TryGetStringField(TEXT("tool_name"), RequestedTool);
			if (RequestedTool.IsEmpty())
			{
				bOutIsError = true;
				return TEXT("Error: 'tool_name' parameter is required. Example: get_tool_info({\"tool_name\": \"create_material\"})");
			}

			// Register this tool for dynamic injection on the next API call
			if (ToolSchemaRegistry->IsToolRegistered(RequestedTool) && ToolSchemaRegistry->IsToolEnabled(RequestedTool))
			{
				DynamicallyLoadedTools.Add(RequestedTool);
				UE_LOG(LogAgentZet, Log, TEXT("ChatSession: Dynamically loaded tool '%s' — will be in tools array on next turn. (%d dynamic tools total)"),
					*RequestedTool, DynamicallyLoadedTools.Num());
			}

			FString Result = ToolSchemaRegistry->GetToolInfoString(RequestedTool);
			// BANNER GATED ON REAL REGISTRATION (2026-08-31). This success
			// line used to be appended UNCONDITIONALLY - so asking about a
			// hallucinated name returned "Tool 'X' not found..." followed
			// immediately by "This tool has been loaded and is now
			// available", actively confirming the invented name to the
			// model. Only a genuinely registered+enabled tool earns it.
			if (ToolSchemaRegistry->IsToolRegistered(RequestedTool)
				&& ToolSchemaRegistry->IsToolEnabled(RequestedTool))
			{
				Result += TEXT("\n\n✅ This tool has been loaded and is now available for you to call directly on your next response. "
					"Do NOT call get_tool_info again for this tool — just call it directly.");
			}
			else
			{
				Result += TEXT("\n\nThat tool was NOT loaded (it does not exist under that name). "
					"Use list_tools_in_category to see real tool names, or call one of the tools already in your list.");
			}
			return Result;
		}
		return TEXT("Error: ToolSchemaRegistry not available.");
	}

	if (ToolCall.ToolName == TEXT("list_tools_in_category"))
	{
		if (ToolSchemaRegistry.IsValid() && ToolCall.InputParams.IsValid())
		{
			FString Category;
			ToolCall.InputParams->TryGetStringField(TEXT("category"), Category);
			if (Category.IsEmpty())
			{
				bOutIsError = true;
				return TEXT("Error: 'category' parameter is required. Example: list_tools_in_category({\"category\": \"material\"})");
			}

			FString Result = ToolSchemaRegistry->ListToolsInCategoryString(Category);

			// LOAD EXACTLY WHAT WAS LISTED (2026-08-31). The old code
			// tried GetSchemasByCategory (filters a "category" JSON field
			// zero schemas define - always empty) and then fell back to a
			// bare ToolName.Contains(Category) substring match, which
			// loaded a DIFFERENT set than the listing above rendered:
			// category "level" listed spawn_actor / place_light /
			// modify_world_settings but substring-loaded only
			// create_level_sequence - then told the model everything was
			// loaded. The model's calls to the listed-but-unloaded names
			// then failed exactly like invented ones. Listing and loading
			// now share one pattern map in the registry.
			TArray<FString> CategoryToolNames =
				ToolSchemaRegistry->GetToolNamesInCategory(Category);
			int32 LoadedCount = 0;
			FString LoadedNames;
			for (const FString& CategoryToolName : CategoryToolNames)
			{
				if (!ToolSchemaRegistry->IsToolEnabled(CategoryToolName)) continue;
				DynamicallyLoadedTools.Add(CategoryToolName);
				LoadedNames += (LoadedNames.IsEmpty() ? TEXT("") : TEXT(", "))
					+ CategoryToolName;
				LoadedCount++;
			}

			if (LoadedCount > 0)
			{
				UE_LOG(LogAgentZet, Log, TEXT("ChatSession: Auto-loaded %d tools from category '%s'. (%d dynamic tools total)"),
					LoadedCount, *Category, DynamicallyLoadedTools.Num());
				// HONEST load report: name exactly what became callable,
				// never "all tools" - if the listing and this line ever
				// disagree again, the message shows it instead of hiding it.
				Result += FString::Printf(TEXT("\n\n✅ Loaded %d tools, callable from your next response: %s. "
					"Do NOT call get_tool_info for these — just call them directly."), LoadedCount, *LoadedNames);
			}

			return Result;
		}
		return TEXT("Error: ToolSchemaRegistry not available.");
	}

	// ---- UNKNOWN-TOOL GUARD (2026-08-31) ----
	// Every meta-tool above returned early, so any name reaching this
	// point must be backed by a real executor or a registered schema.
	// Before this guard, an invented name (list_assets, get_project_info,
	// list_levels - qwen3-coder fills toolset gaps with generic
	// Unreal-MCP names from its training priors) fell through to
	// RouteToolCall and came back as a bare "No executor registered for
	// tool: X" - no valid-name list, no suggestion, nothing a 30B local
	// model can self-correct from. Worse, the failed call was then
	// replayed in history as a legitimate tool_call, reinforcing the
	// invented name. The corrective feedback below names the real
	// toolset, the nearest matches, and the legitimate no-tool exits.
	{
		const bool bHasExecutor =
			ActionRouter.IsValid()
			&& ActionRouter->FindExecutorForTool(ToolCall.ToolName).IsValid();
		const bool bRegisteredSchema =
			ToolSchemaRegistry.IsValid()
			&& ToolSchemaRegistry->IsToolRegistered(ToolCall.ToolName);
		if (!bHasExecutor && !bRegisteredSchema)
		{
			bOutIsError = true;
			// Nearest real names by shared underscore-separated words:
			// substring matching (the registry's own fuzzy path) finds
			// nothing for "list_assets", but word overlap surfaces
			// search_assets and list_directory - exactly the correction
			// the model needs.
			TArray<FString> CallWords;
			ToolCall.ToolName.ToLower().ParseIntoArray(CallWords, TEXT("_"));
			TArray<TPair<int32, FString>> Scored;
			if (ToolSchemaRegistry.IsValid())
			{
				for (const FString& Candidate :
					ToolSchemaRegistry->GetAllToolNames())
				{
					TArray<FString> CandWords;
					Candidate.ToLower().ParseIntoArray(CandWords, TEXT("_"));
					int32 Shared = 0;
					for (const FString& W : CallWords)
					{
						if (CandWords.Contains(W)) ++Shared;
					}
					if (Shared > 0)
					{
						Scored.Add(TPair<int32, FString>(Shared, Candidate));
					}
				}
			}
			Scored.Sort([](const TPair<int32, FString>& A,
				const TPair<int32, FString>& B)
				{ return A.Key > B.Key; });
			FString Nearest;
			for (int32 Idx = 0; Idx < Scored.Num() && Idx < 3; ++Idx)
			{
				Nearest += (Nearest.IsEmpty() ? TEXT("") : TEXT(", "))
					+ Scored[Idx].Value;
			}
			// The names genuinely callable in this conversation: the
			// essential set plus anything discovery has loaded.
			FString CallableNow;
			if (ToolSchemaRegistry.IsValid())
			{
				for (const TSharedPtr<FJsonObject>& Schema :
					ToolSchemaRegistry->GetEssentialSchemas())
				{
					FString SchemaName;
					if (Schema.IsValid()
						&& Schema->TryGetStringField(TEXT("name"), SchemaName))
					{
						CallableNow += (CallableNow.IsEmpty()
							? TEXT("") : TEXT(", ")) + SchemaName;
					}
				}
			}
			for (const FString& DynName : DynamicallyLoadedTools)
			{
				CallableNow += (CallableNow.IsEmpty()
					? TEXT("") : TEXT(", ")) + DynName;
			}
			FString Guidance = FString::Printf(
				TEXT("UNKNOWN TOOL '%s' - this tool does not exist and was NOT executed.\n"),
				*ToolCall.ToolName);
			if (!Nearest.IsEmpty())
			{
				Guidance += FString::Printf(
					TEXT("Closest real tools: %s.\n"), *Nearest);
			}
			Guidance += FString::Printf(
				TEXT("Tools you can call right now: %s.\n")
				TEXT("To find more tools: list_tools_in_category({\"category\": \"...\"}) or get_tool_info({\"tool_name\": \"...\"}).\n")
				TEXT("If no tool fits, reply in plain text or call ask_followup_question or attempt_completion. Never invent tool names."),
				*CallableNow);
			UE_LOG(LogAgentZet, Warning,
				TEXT("ChatSession: rejected unknown tool '%s' (nearest: %s)"),
				*ToolCall.ToolName, *Nearest);
			return Guidance;
		}
		// A REAL tool called by name while its schema is not in the sent
		// set (the broken-discovery case: the category listing showed it,
		// the substring loader failed to load it). Execute it normally -
		// the executor exists and the model's intent is plain - and pin
		// its schema into the dynamic set so every subsequent request
		// carries the real definition instead of leaving the model to
		// work from the one-line listing.
		if (bHasExecutor && bRegisteredSchema
			&& !DynamicallyLoadedTools.Contains(ToolCall.ToolName))
		{
			DynamicallyLoadedTools.Add(ToolCall.ToolName);
		}
	}

	// Check security mode
	const UAgentZetDeveloperSettings* Settings = UAgentZetDeveloperSettings::Get();
	TSharedPtr<IAgentZetActionExecutor> Executor = ActionRouter->FindExecutorForTool(ToolCall.ToolName);
	if (Executor.IsValid() && Settings)
	{
		if (!Settings->IsToolCategoryAllowed(Executor->GetCategory()))
		{
			bOutIsError = true;
			FString ErrorMsg = FString::Printf(
				TEXT("Tool '%s' is blocked by current security mode (%s). Change security mode in settings to use this tool."),
				*ToolCall.ToolName,
				Settings->SecurityMode == EAgentZetSecurityMode::Sandbox ? TEXT("Sandbox") : TEXT("Advanced"));

			FAgentZetActionExecutionRecord Record;
			Record.ToolName = ToolCall.ToolName;
			Record.ToolUseId = ToolCall.ToolUseId;
			Record.bSuccess = false;
			Record.bIsError = true;
			Record.ResultMessage = ErrorMsg;
			if (ExecutionJournal.IsValid()) ExecutionJournal->RecordExecution(Record);

			return ErrorMsg;
		}
	}

	FString PreHash;
	if (ToolCall.InputParams.IsValid())
	{
		FString AssetPath;
		if (ToolCall.InputParams->TryGetStringField(TEXT("asset_path"), AssetPath))
		{
			PreHash = FAgentZetExecutionJournal::ComputeAssetHash(AssetPath);
		}
		else
		{
			FString FilePath;
			if (ToolCall.InputParams->TryGetStringField(TEXT("file_path"), FilePath))
			{
				PreHash = FAgentZetExecutionJournal::ComputeFileHash(FilePath);
			}
		}
	}

	// Route and execute
	FAgentZetActionResult Result = ActionRouter->RouteToolCall(ToolCall);

	FDateTime EndTime = FDateTime::UtcNow();
	float ElapsedSeconds = (EndTime - StartTime).GetTotalSeconds();

	// Compute post-state hash
	FString PostHash;
	if (ToolCall.InputParams.IsValid())
	{
		FString AssetPath;
		if (ToolCall.InputParams->TryGetStringField(TEXT("asset_path"), AssetPath))
		{
			PostHash = FAgentZetExecutionJournal::ComputeAssetHash(AssetPath);
		}
		else
		{
			FString FilePath;
			if (ToolCall.InputParams->TryGetStringField(TEXT("file_path"), FilePath))
			{
				PostHash = FAgentZetExecutionJournal::ComputeFileHash(FilePath);
			}
		}
	}

	// Build result content for Claude
	FString ResultContent;
	if (Result.bSuccess)
	{
		ResultContent = Result.ResultMessage;
		if (Result.ModifiedAssets.Num() > 0)
		{
			ResultContent += TEXT("\nModified assets: ") + FString::Join(Result.ModifiedAssets, TEXT(", "));
		}
		if (Result.ModifiedPaths.Num() > 0)
		{
			ResultContent += TEXT("\nModified files: ") + FString::Join(Result.ModifiedPaths, TEXT(", "));

			// Phase 1: Track files modified by AgentZet (prevents false stale detection)
			if (FileContextTracker.IsValid())
			{
				for (const FString& ModifiedPath : Result.ModifiedPaths)
				{
					// Convert to relative path
					FString RelPath = ModifiedPath;
					FPaths::MakePathRelativeTo(RelPath, *FPaths::ProjectDir());
					FileContextTracker->OnFileEditedByAgentZet(RelPath);
				}
			}
		}
		if (Result.Warnings.Num() > 0)
		{
			ResultContent += TEXT("\nWarnings: ") + FString::Join(Result.Warnings, TEXT("; "));
		}
	}
	else
	{
		bOutIsError = true;
		ResultContent = TEXT("EXECUTION FAILED: ") + FString::Join(Result.Errors, TEXT("; "));
	}

	// Record in execution journal with state hashes
	FAgentZetActionExecutionRecord Record;
	Record.ToolName = ToolCall.ToolName;
	Record.ToolUseId = ToolCall.ToolUseId;
	Record.bSuccess = Result.bSuccess;
	Record.bIsError = !Result.bSuccess;
	Record.ResultMessage = ResultContent;
	Record.ModifiedFiles = Result.ModifiedPaths;
	Record.ModifiedAssets = Result.ModifiedAssets;
	Record.BackupPaths = Result.BackupPaths;
	Record.ExecutionTimeSeconds = ElapsedSeconds;
	Record.PreStateHash = PreHash;
	Record.PostStateHash = PostHash;

	if (ToolCall.InputParams.IsValid())
	{
		FString InputStr;
		TSharedRef<TJsonWriter<>> Writer = TJsonWriterFactory<>::Create(&InputStr);
		FJsonSerializer::Serialize(ToolCall.InputParams.ToSharedRef(), Writer);
		Record.InputJson = InputStr;
	}

	if (ExecutionJournal.IsValid())
	{
		ExecutionJournal->RecordExecution(Record);
	}

	return ResultContent;
}

void FAgentZetChatSession::OnStreamingText(const FGuid& MessageId, const FString& DeltaText)
{
	OnMessageUpdated.Broadcast(MessageId, DeltaText, EAgentZetMessageRole::Assistant);
}

void FAgentZetChatSession::OnToolCallReceived(const FAgentZetToolCall& ToolCall)
{
	ToolCallQueue.Add(ToolCall);
}

void FAgentZetChatSession::OnMessageComplete(const FAgentZetMessage& Message)
{
	if (ConversationManager.IsValid())
	{
		ConversationManager->AddAssistantMessageFull(Message);
	}
}

void FAgentZetChatSession::OnRequestStarted()
{
	SetState(EConversationState::Streaming);
	FString StatusText = bInAgenticLoop
		? FString::Printf(TEXT("Executing tools... (iteration %d)"), AgenticLoopCount)
		: TEXT("Thinking...");
	OnStatusUpdated.Broadcast(StatusText);
	OnRequestStartedDelegate.Broadcast();
}

void FAgentZetChatSession::OnRequestCompleted(bool bSuccess)
{
	OnRequestCompletedDelegate.Broadcast(bSuccess);
	if (!bSuccess)
	{
		bInAgenticLoop = false;
		SetState(EConversationState::Error);

		OnAgentFinished.Broadcast(TEXT("API Request failed."));
		OnStatusUpdated.Broadcast(TEXT("")); // Hide progress
		return;
	}

	// ---- Context Management: Run after each successful API response ----
	// This checks if we need to condense or truncate before processing tool calls.
	// We do this asynchronously and continue when done.
	if (ContextManager.IsValid() && !ContextManager->IsManaging())
	{
		FString SystemPrompt;
		if (OnGetSystemPromptString.IsBound())
		{
			SystemPrompt = OnGetSystemPromptString.Execute();
		}

		ContextManager->ManageContext(SystemPrompt, LastResponseTokenUsage,
			[this](const FAgentZetContextManagementResult& CtxResult)
			{
				if (CtxResult.bDidCondense)
				{
					FAgentZetMessage CtxMsg(EAgentZetMessageRole::System,
						FString::Printf(TEXT("📦 Context condensed (was %.0f%% full). Summary created."),
							CtxResult.ContextPercent));
					OnMessageAdded.Broadcast(CtxMsg);

					UE_LOG(LogAgentZet, Log,
						TEXT("ChatSession: Context condensed. Was %.0f%%, now ~%d tokens."),
						CtxResult.ContextPercent, CtxResult.NewContextTokens);
				}
				else if (CtxResult.bDidTruncate)
				{
					FAgentZetMessage CtxMsg(EAgentZetMessageRole::System,
						FString::Printf(TEXT("✂ Context truncated: %d old messages hidden (was %.0f%% full)."),
							CtxResult.MessagesRemoved, CtxResult.ContextPercent));
					OnMessageAdded.Broadcast(CtxMsg);

					UE_LOG(LogAgentZet, Log,
						TEXT("ChatSession: Context truncated. Removed %d messages. Was %.0f%% full."),
						CtxResult.MessagesRemoved, CtxResult.ContextPercent);
				}

				OnSaveTabsToDisk.ExecuteIfBound();
				OnSessionCompletedContextManagement.Broadcast();
				OnRequestCompletedPostContextManagement();
			});
		return; // Wait for context management to complete
	}

	// No context manager -- proceed directly
	OnRequestCompletedPostContextManagement();
}

void FAgentZetChatSession::OnRequestCompletedPostContextManagement()
{
	// AGENTIC LOOP: If tool calls were received, check approval flow
	if (ToolCallQueue.Num() > 0)
	{
		const UAgentZetDeveloperSettings* Settings = UAgentZetDeveloperSettings::Get();

		// Build a quick action plan from tool calls for display and risk evaluation
		FAgentZetActionPlan Plan;
		Plan.Summary = FString::Printf(TEXT("%d tool(s) pending execution"), ToolCallQueue.Num());

		bool bAllReadOnly = true;
		static const TArray<FString> ReadOnlyToolPrefixes = {
			TEXT("get_"), TEXT("read_"), TEXT("list_"), TEXT("search_"),
			TEXT("find_"), TEXT("query_"), TEXT("show_"), TEXT("describe_")
		};

		for (FAgentZetToolCall& TC : ToolCallQueue)
		{
			if (ActionRouter.IsValid())
			{
				TSharedPtr<IAgentZetActionExecutor> Executor = ActionRouter->FindExecutorForTool(TC.ToolName);
				if (Executor.IsValid())
				{
					TC.Category = Executor->GetCategory();
				}
			}

			FAgentZetAction Action;
			Action.Description = FString::Printf(TEXT("🔧 %s"), *TC.ToolName);
			Action.Category = TC.Category;

			// Assign risk based on category
			switch (TC.Category)
			{
			case EAgentZetActionCategory::Cpp:
			case EAgentZetActionCategory::Build:
			case EAgentZetActionCategory::Settings:
				Action.RiskLevel = EAgentZetRiskLevel::High;
				break;
			case EAgentZetActionCategory::SourceControl:
			case EAgentZetActionCategory::FileSystem:
				Action.RiskLevel = EAgentZetRiskLevel::Medium;
				break;
			default:
				Action.RiskLevel = EAgentZetRiskLevel::Low;
				break;
			}

			Action.ToolCall = TC;
			Plan.Actions.Add(Action);

			if (Action.RiskLevel > Plan.MaxRiskLevel)
			{
				Plan.MaxRiskLevel = Action.RiskLevel;
			}

			// Check Read-Only status
			if (bAllReadOnly)
			{
				bool bIsReadOnly = false;
				for (const FString& Prefix : ReadOnlyToolPrefixes)
				{
					if (TC.ToolName.StartsWith(Prefix, ESearchCase::IgnoreCase))
					{
						bIsReadOnly = true;
						break;
					}
				}
				// Meta-tools are safe
				if (TC.ToolName == TEXT("update_todo_list") || TC.ToolName == TEXT("switch_mode") || TC.ToolName == TEXT("attempt_completion"))
				{
					bIsReadOnly = true;
				}
				if (!bIsReadOnly)
				{
					bAllReadOnly = false;
				}
			}
		}

		bool bAutoApprove = false;

		bool bOnlyMetaTools = true;
		for (const FAgentZetToolCall& TC : ToolCallQueue)
		{
			if (TC.ToolName != TEXT("attempt_completion") && TC.ToolName != TEXT("switch_mode") && TC.ToolName != TEXT("update_todo_list"))
			{
				bOnlyMetaTools = false;
				break;
			}
		}

		if (bOnlyMetaTools)
		{
			UE_LOG(LogAgentZet, Log, TEXT("ChatSession: Auto-approving %d tool calls (only safe meta-tools pending)"), ToolCallQueue.Num());
			bAutoApprove = true;
		}
		else if (Settings)
		{
			if (Settings->bAutoApproveAllTools)
			{
				UE_LOG(LogAgentZet, Log, TEXT("ChatSession: Auto-approving %d tool calls (bAutoApproveAllTools=true)"), ToolCallQueue.Num());
				bAutoApprove = true;
			}
			else if (Settings->bAutoApproveLowRisk && Plan.MaxRiskLevel == EAgentZetRiskLevel::Low)
			{
				UE_LOG(LogAgentZet, Log, TEXT("ChatSession: Auto-approving %d tool calls (bAutoApproveLowRisk=true and MaxRiskLevel=Low)"), ToolCallQueue.Num());
				bAutoApprove = true;
			}
			else if (Settings->bAutoApproveReadOnlyTools && bAllReadOnly)
			{
				UE_LOG(LogAgentZet, Log, TEXT("ChatSession: Auto-approving %d read-only tool calls (bAutoApproveReadOnlyTools=true)"), ToolCallQueue.Num());
				bAutoApprove = true;
			}
		}

		if (bAutoApprove)
		{
			// We will hook this into FAgentZetAutoApprovalHandler limit checking
			if (Settings)
			{
				FAgentZetAutoApprovalCheck Check = AutoApprovalHandler.CheckLimits(
					Settings->MaxConsecutiveAutoApprovedRequests,
					Settings->MaxAutoApprovedCostDollars,
					LastRequestCost);

				if (Check.bRequiresApproval)
				{
					HandleAutoApprovalLimitReached(Check);
					return; // Wait for user approval before continuing
				}
			}

			ProcessToolCallQueue();
			return;
		}

		SetState(EConversationState::WaitingForToolApproval);
		OnToolRequiresApproval.Broadcast(Plan);
	}
	else
	{
		// No tool calls received.
		// Roo Code approach: track consecutive no-tool responses.
		// On the FIRST no-tool response during agentic loop, nudge ONCE.
		// On subsequent no-tool responses, ask user or stop.

		if (bInAgenticLoop)
		{
			ConsecutiveNoToolCount++;

			if (ConsecutiveNoToolCount == 1)
			{
				// First no-tool response: nudge once
				ConversationManager->AddUserMessage(
					TEXT("[AgentZet SYSTEM] You did not use any tools in your last response. ")
					TEXT("IMPORTANT: You MUST use a tool to continue. If the task is complete, ")
					TEXT("call the attempt_completion tool with a summary of what was accomplished. ")
					TEXT("If there is more work to do, use the appropriate tool to continue. ")
					TEXT("Do NOT respond with plain text only — you MUST call a tool."));

				OnSaveTabsToDisk.ExecuteIfBound();
				ContinueAgenticLoop();
				return;
			}

			if (ConsecutiveNoToolCount >= MaxConsecutiveNoToolResponses)
			{
				FText Title = FText::FromString(TEXT("AgentZet — AI Stopped Using Tools"));
				FText Message = FText::FromString(FString::Printf(
					TEXT("The AI has responded %d times without using any tools.\n\n")
					TEXT("This may mean:\n")
					TEXT("  • The task is done (but it forgot to call attempt_completion)\n")
					TEXT("  • The AI is stuck and needs guidance\n\n")
					TEXT("YES — Continue the task\n")
					TEXT("NO — End the task now"),
					ConsecutiveNoToolCount));

				EAppReturnType::Type Result = FMessageDialog::Open(EAppMsgType::YesNo, Message, Title);

				if (Result == EAppReturnType::Yes)
				{
					ConsecutiveNoToolCount = 0;
					ConversationManager->AddUserMessage(
						TEXT("[AgentZet SYSTEM] Please continue the task. If it is complete, ")
						TEXT("you MUST call attempt_completion. Do not respond with text only."));
					OnSaveTabsToDisk.ExecuteIfBound();
					ContinueAgenticLoop();
					return;
				}
			}
		}

		// Task is done (either not in agentic loop, or user chose to end/max nudges)
		bInAgenticLoop = false;
		AgenticLoopCount = 0;
		ConsecutiveNoToolCount = 0;
		SetState(EConversationState::Idle);

		OnStatusUpdated.Broadcast(TEXT(""));
		OnAgentFinished.Broadcast(TEXT("Task ended (no tools returned)."));
		OnSaveTabsToDisk.ExecuteIfBound();
	}
}

void FAgentZetChatSession::OnToolCallsRejected(const FAgentZetActionPlan& Plan)
{
	// Send rejection as tool_result errors so Claude knows the tools were not executed
	TArray<FAgentZetToolCall> ActiveToolCalls = MoveTemp(ToolCallQueue);
	for (const FAgentZetToolCall& ToolCall : ActiveToolCalls)
	{
		FAgentZetMessage& ToolResultMsg = ConversationManager->AddToolResultMessage(
			ToolCall.ToolUseId,
			TEXT("Tool execution was rejected by the user. Do not retry this action unless explicitly asked."),
			true /* bIsError */);
		ToolResultMsg.ToolName = TEXT("error");
	}

	ActiveToolCalls.Empty();

	// End agentic loop
	bInAgenticLoop = false;
	SetState(EConversationState::Idle);
	OnStatusUpdated.Broadcast(TEXT(""));
	OnAgentFinished.Broadcast(TEXT("Execution rejected by user."));
}

void FAgentZetChatSession::HandleAutoApprovalLimitReached(const FAgentZetAutoApprovalCheck& Check)
{
	FText Title = FText::FromString(TEXT("AgentZet — Approval Required"));
	FText Message = FText::FromString(Check.ApprovalReason);

	EAppReturnType::Type Result = FMessageDialog::Open(EAppMsgType::YesNo, Message, Title);

	if (Result == EAppReturnType::Yes)
	{
		AutoApprovalHandler.ResetBaseline();

		FAgentZetMessage InfoMsg(EAgentZetMessageRole::System,
			TEXT("✅ Continuation approved. Auto-approval counters reset."));
		OnMessageAdded.Broadcast(InfoMsg);

		ProcessToolCallQueue();
	}
	else
	{
		ToolCallQueue.Empty();
		bInAgenticLoop = false;
		AgenticLoopCount = 0;
		SetState(EConversationState::Idle);
		OnStatusUpdated.Broadcast(TEXT(""));
		OnAgentFinished.Broadcast(TEXT("Execution rejected by user."));
	}
}

