// Copyright AgentZet. All Rights Reserved.

#include "AgentZetContextManager.h"
#include "AgentZetInterfaces.h"
#include "AgentZetConversationManager.h"
#include "AgentZetTokenCounter.h"
#include "AgentZetSettings.h"
#include "AgentZetCoreModule.h"

FAgentZetContextManager::FAgentZetContextManager(
	TSharedPtr<IAgentZetLLMClient> InLLMClient,
	TSharedPtr<FAgentZetConversationManager> InConversationManager)
	: LLMClient(InLLMClient)
	, ConversationManager(InConversationManager)
	, bIsManaging(false)
{
	Condenser = MakeShared<FAgentZetContextCondenser>(InLLMClient, InConversationManager);
}

FAgentZetContextManager::~FAgentZetContextManager()
{
}

void FAgentZetContextManager::SetLLMClient(TSharedPtr<IAgentZetLLMClient> InLLMClient)
{
	LLMClient = InLLMClient;
	if (Condenser.IsValid())
	{
		Condenser->SetLLMClient(InLLMClient);
	}
}

// ============================================================================
// ManageContext — Called after each successful API response
// Ported from Roo Code's manageContext() in context-management/index.ts
// ============================================================================

void FAgentZetContextManager::ManageContext(
	const FString& SystemPrompt,
	const FAgentZetTokenUsage& LastTokenUsage,
	TFunction<void(const FAgentZetContextManagementResult&)> OnComplete,
	const FString& EnvironmentDetails,
	const FString& FoldedCodeContext)
{
	if (bIsManaging)
	{
		UE_LOG(LogAgentZet, Warning, TEXT("ContextManager: Already managing context. Ignoring."));
		FAgentZetContextManagementResult EmptyResult;
		OnComplete(EmptyResult);
		return;
	}

	if (!ConversationManager.IsValid())
	{
		FAgentZetContextManagementResult EmptyResult;
		OnComplete(EmptyResult);
		return;
	}

	const UAgentZetDeveloperSettings* Settings = UAgentZetDeveloperSettings::Get();
	if (!Settings)
	{
		FAgentZetContextManagementResult EmptyResult;
		OnComplete(EmptyResult);
		return;
	}

	// Compute current token usage.
	// LOCAL-MODEL WINDOW TRUTH (2026-08-31): for Ollama the real window
	// is OllamaContextSize (what the server actually enforces via
	// num_ctx), NOT the Claude-sized ContextWindow enum. With the enum's
	// 200k basis, every percentage here was ~12x too small for a 16k
	// local window - so truncation would never have protected the real
	// limit, while (with a broken 0% threshold in config) condensation
	// fired on every turn. Measured live: a fresh 6.5k-token
	// conversation was condensed at "14% full" and truncated at "23%",
	// destroying the tool result the model had just fetched.
	const bool bIsExtendedWindow = (Settings->ContextWindow == EAgentZetContextWindow::Extended_1M);
	int32 ContextWindowTokens = FAgentZetTokenCounter::GetContextWindowTokens(bIsExtendedWindow);
	if (Settings->ActiveProvider == EAgentZetProvider::Ollama
		&& Settings->OllamaContextSize > 0)
	{
		ContextWindowTokens = Settings->OllamaContextSize;
	}
	const int32 MaxResponseTokens = Settings->MaxResponseTokens;

	// Total tokens = last API response input + output tokens
	const int32 TotalTokens = LastTokenUsage.InputTokens + LastTokenUsage.OutputTokens;

	// Calculate effective history token estimate
	TArray<FAgentZetMessage> EffectiveHistory = ConversationManager->GetEffectiveHistory();
	const int32 EstimatedTokens = FAgentZetTokenCounter::EstimateTokens(EffectiveHistory)
		+ FAgentZetTokenCounter::EstimateTokens(SystemPrompt);

	// Use the larger of reported tokens and estimated tokens
	const int32 PrevContextTokens = FMath::Max(TotalTokens, EstimatedTokens);

	// Allowed tokens = context window * (1 - buffer %) - reserved for response
	const float TokenBuffer = 1.0f - TokenBufferPercent;
	const int32 AllowedTokens = FMath::FloorToInt(ContextWindowTokens * TokenBuffer) - MaxResponseTokens;
	const float ContextPercent = FAgentZetTokenCounter::GetContextUsagePercent(PrevContextTokens, ContextWindowTokens);

	UE_LOG(LogAgentZet, Log,
		TEXT("ContextManager: context=%d/%d tokens (%.1f%%), allowed=%d, autoCondense=%s, threshold=%d%%"),
		PrevContextTokens, ContextWindowTokens, ContextPercent,
		AllowedTokens, Settings->bAutoCondenseContext ? TEXT("true") : TEXT("false"),
		Settings->AutoCondenseThresholdPercent);

	// Check if we need to manage context.
	// CLAMPED IN CODE (2026-08-31): the property metadata claims
	// ClampMin=5, but values loaded from ini bypass Slate clamps - this
	// machine's config held AutoCondenseThresholdPercent=0, which made
	// "condense" fire on EVERY turn and summarize away fresh tool
	// results (the condenser also drops tool results wholesale on
	// OpenAI-compatible providers). A threshold below 5% can never be
	// a real intention; refuse it here where it actually matters.
	const int32 EffectiveCondenseThreshold =
		FMath::Clamp(Settings->AutoCondenseThresholdPercent, 5, 100);
	const bool bNeedsCondense = Settings->bAutoCondenseContext
		&& ContextPercent >= static_cast<float>(EffectiveCondenseThreshold);
	const bool bNeedsTruncate = PrevContextTokens > AllowedTokens;

	if (!bNeedsCondense && !bNeedsTruncate)
	{
		// No management needed
		FAgentZetContextManagementResult EmptyResult;
		EmptyResult.PrevContextTokens = PrevContextTokens;
		EmptyResult.ContextPercent = ContextPercent;
		OnComplete(EmptyResult);
		return;
	}

	bIsManaging = true;

	// Try condensation first if enabled
	if (bNeedsCondense && Condenser.IsValid() && !Condenser->IsCondensing())
	{
		FAgentZetSummarizeOptions Options;
		Options.SystemPrompt = SystemPrompt;
		Options.CustomCondensingPrompt = Settings->CustomCondensingPrompt;
		Options.bIsAutomaticTrigger = true;
		Options.EnvironmentDetails = EnvironmentDetails;
		Options.FoldedCodeContext = FoldedCodeContext;

		Condenser->SummarizeConversation(Options,
			[this, OnComplete, PrevContextTokens, ContextPercent, AllowedTokens]
			(const FAgentZetCondenseResult& CondenseResult)
			{
				bIsManaging = false;

				if (CondenseResult.bSuccess)
				{
					FAgentZetContextManagementResult Result;
					Result.bDidManage = true;
					Result.bDidCondense = true;
					Result.PrevContextTokens = PrevContextTokens;
					Result.ContextPercent = ContextPercent;
					Result.NewContextTokens = CondenseResult.NewContextTokens;
					OnComplete(Result);
				}
				else
				{
					// Condensation failed — fall back to truncation if needed
					UE_LOG(LogAgentZet, Warning,
						TEXT("ContextManager: Condensation failed (%s). Falling back to truncation if needed."),
						*CondenseResult.ErrorMessage);

					FAgentZetContextManagementResult Result;
					Result.bDidManage = false;
					Result.PrevContextTokens = PrevContextTokens;
					Result.ContextPercent = ContextPercent;
					Result.ErrorMessage = CondenseResult.ErrorMessage;

					if (PrevContextTokens > AllowedTokens)
					{
						TruncateConversation(TruncationFrac, Result);
					}

					OnComplete(Result);
				}
			});
	}
	else if (bNeedsTruncate)
	{
		// Auto-condense disabled or condenser busy — use truncation directly
		UE_LOG(LogAgentZet, Log,
			TEXT("ContextManager: Context exceeds allowed tokens (%d > %d). Applying truncation."),
			PrevContextTokens, AllowedTokens);

		FAgentZetContextManagementResult Result;
		Result.PrevContextTokens = PrevContextTokens;
		Result.ContextPercent = ContextPercent;
		TruncateConversation(TruncationFrac, Result);

		bIsManaging = false;
		OnComplete(Result);
	}
	else
	{
		bIsManaging = false;
		FAgentZetContextManagementResult EmptyResult;
		EmptyResult.PrevContextTokens = PrevContextTokens;
		EmptyResult.ContextPercent = ContextPercent;
		OnComplete(EmptyResult);
	}
}

// ============================================================================
// TruncateConversation — Non-destructive sliding window
// ============================================================================

void FAgentZetContextManager::TruncateConversation(float FracToRemove, FAgentZetContextManagementResult& OutResult)
{
	if (!ConversationManager.IsValid()) return;

	int32 MessagesRemoved = ConversationManager->TruncateConversation(FracToRemove);

	if (MessagesRemoved > 0)
	{
		OutResult.bDidManage = true;
		OutResult.bDidTruncate = true;
		OutResult.MessagesRemoved = MessagesRemoved;

		// Re-estimate token count after truncation
		TArray<FAgentZetMessage> EffectiveHistory = ConversationManager->GetEffectiveHistory();
		OutResult.NewContextTokens = FAgentZetTokenCounter::EstimateTokens(EffectiveHistory);

		UE_LOG(LogAgentZet, Log,
			TEXT("ContextManager: Truncated %d messages. Estimated new context: %d tokens."),
			MessagesRemoved, OutResult.NewContextTokens);
	}
}
