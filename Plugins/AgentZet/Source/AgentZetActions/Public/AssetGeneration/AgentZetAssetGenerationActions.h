// Copyright AgentZet. All Rights Reserved.

#pragma once

#include "CoreMinimal.h"
#include "AgentZetInterfaces.h"

/**
 * TRELLIS asset-generation tools (2026-08-31, LineBoss fork).
 *
 * Three tools that give the LOCAL model an image -> /Game pipeline with
 * evidence at every step, wrapping the repo's existing fail-closed lanes:
 *
 *   generate_3d_asset      - launches Scripts/trellis_generate_v001.ps1
 *                            DETACHED (TRELLIS takes 53-290 s and tool
 *                            execution is synchronous on the game thread,
 *                            so blocking here would freeze the editor).
 *                            Returns immediately with a job handle.
 *   check_asset_job        - polls the job by reading its on-disk state
 *                            (manifest present = done; pid alive = still
 *                            running; neither = failed, log tail returned).
 *                            Waits up to 15 s in-tool so the model needs
 *                            only 2-3 polls for a res-512 generation.
 *   import_generated_asset - Blender join+scale+ground+FBX via
 *                            Tools/trellis_prepare_import_v001.py, then
 *                            AssetImportTask import, Nanite check, bounds
 *                            verification vs the declared size, and an
 *                            audit receipt under Saved/Audits/Spacecraft/.
 *
 * Job state lives ON DISK under Saved/AgentZetJobs/AssetGen/<name>/ - the
 * executor is recreated with the panel, so nothing may live in members.
 */
class AGENTZETACTIONS_API FAgentZetAssetGenerationActions : public IAgentZetActionExecutor
{
public:
    FAgentZetAssetGenerationActions();
    virtual ~FAgentZetAssetGenerationActions();

    virtual FName GetActionName() const override;
    virtual FText GetDisplayName() const override;
    virtual EAgentZetActionCategory GetCategory() const override;
    virtual EAgentZetRiskLevel GetDefaultRiskLevel() const override;
    virtual FAgentZetActionPlan PreviewAction(const TSharedRef<FJsonObject>& Params) override;
    virtual FAgentZetActionResult ExecuteAction(const TSharedRef<FJsonObject>& Params) override;
    virtual bool CanUndo() const override;
    virtual bool UndoAction() override;
    virtual TArray<FString> GetSupportedToolNames() const override;
    virtual bool ValidateParams(const TSharedRef<FJsonObject>& Params, TArray<FString>& OutErrors) const override;

private:
    FAgentZetActionResult ExecuteGenerate(const TSharedRef<FJsonObject>& Params);
    FAgentZetActionResult ExecuteCheckJob(const TSharedRef<FJsonObject>& Params);
    FAgentZetActionResult ExecuteImport(const TSharedRef<FJsonObject>& Params);
};
