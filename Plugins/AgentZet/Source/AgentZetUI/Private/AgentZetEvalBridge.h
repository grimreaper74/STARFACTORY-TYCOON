// Copyright AgentZet. All Rights Reserved.

#pragma once

#include "CoreMinimal.h"
#include "Containers/Ticker.h"

class SAgentZetMainPanel;
class FAgentZetChatSession;
class FJsonObject;
struct FAgentZetMessage;
struct FAgentZetActionPlan;

/**
 * File-based eval bridge for driving AgentZet programmatically (2026-08-31).
 *
 * Purpose: the autonomous-developer framework needs SCRIPTED, repeatable
 * proof that the local model can inspect the project, make a reversible
 * change, and detect compile failures - evidence, not hand-testing. The
 * chat panel is interactive Slate, so this bridge feeds it prompts from
 * files and captures full transcripts back to files, running the EXACT
 * code path the UI runs (SAgentZetMainPanel::OnPromptSubmitted).
 *
 * Safety model mirrors the game's ALBDeveloperAutomationBridge:
 *   - Off unless the editor is launched with -AgentZetEvalBridge.
 *   - Editor builds only (this module is editor-only anyway).
 *   - Touches only Saved/AgentZetEval/ under the project directory.
 *   - Opens no socket.
 *
 * Protocol (all under <ProjectSaved>/AgentZetEval/):
 *   bridge.ready          - written at startup: {session, startedUtc}
 *   inbox/<id>.prompt.txt - a prompt to run; consumed (deleted) on pickup
 *   outbox/<id>.jsonl     - transcript: one JSON object per line
 *                           ({type:prompt|message|auto_approved|finished})
 *   outbox/<id>.done      - completion summary: {reason, messages, seconds}
 *
 * One eval runs at a time; further inbox files wait until the session is
 * idle again. Tool-approval pauses are auto-approved (recorded in the
 * transcript) - the flag is an explicit dev opt-in on a dev machine, and
 * unattended write-tool evals cannot exist without it.
 */
class FAgentZetEvalBridge : public TSharedFromThis<FAgentZetEvalBridge>
{
public:
	~FAgentZetEvalBridge();

	/** True when -AgentZetEvalBridge is on the editor command line. */
	static bool IsEnabledOnCommandLine();

	void Start();
	void Stop();

private:
	bool Tick(float DeltaTime);
	void TryPickupPrompt();
	void BindToSession(const TSharedPtr<FAgentZetChatSession>& Session);
	void UnbindFromSession();

	void HandleMessageAdded(const FAgentZetMessage& Message);
	void HandleAgentFinished(const FString& Reason);
	void HandleToolRequiresApproval(const FAgentZetActionPlan& Plan);
	void HandleToolResultRecorded(const FString& ToolName,
		const FString& ResultContent, bool bIsError);

	void WriteTranscriptLine(const TSharedRef<FJsonObject>& Line);
	void FinishEval(const FString& Reason);

	FTSTicker::FDelegateHandle TickerHandle;

	FString RootDir;
	FString InboxDir;
	FString OutboxDir;

	/** Non-empty while an eval is running; doubles as the output stem. */
	FString ActiveEvalId;
	double EvalStartSeconds = 0.0;
	int32 MessageCount = 0;

	/** Throttle for tab-invoke attempts while no panel exists yet. */
	double LastTabInvokeSeconds = 0.0;

	TWeakPtr<FAgentZetChatSession> BoundSession;
	FDelegateHandle MessageAddedHandle;
	FDelegateHandle AgentFinishedHandle;
	FDelegateHandle ApprovalHandle;
	FDelegateHandle ToolResultHandle;
};
