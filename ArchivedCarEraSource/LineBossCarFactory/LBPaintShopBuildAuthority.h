#pragma once

#include "CoreMinimal.h"
#include "GameFramework/Info.h"
#include "LBPaintShopExperimentalSaveGame.h"
#include "LBPaintShopBuildAuthority.generated.h"

class ALBPaintShopCellActor;
class UBoxComponent;

/** The single stable placement owned by the first isolated ED-coat vertical slice. */
USTRUCT(BlueprintType)
struct FLBPaintShopApprovedEDCoatLayoutItem
{
    GENERATED_BODY()

    UPROPERTY(VisibleAnywhere, BlueprintReadOnly)
    FName CellId = NAME_None;

    UPROPERTY(VisibleAnywhere, BlueprintReadOnly)
    FName DefinitionId = NAME_None;

    UPROPERTY(VisibleAnywhere, BlueprintReadOnly)
    FTransform WorldTransform = FTransform::Identity;
};

/**
 * Isolated placement authority for the first Paint Shop ED-coat cell only.
 * It owns no process WIP, lineage, generic placement graph, or legacy E-coat state.
 */
UCLASS(BlueprintType)
class LINEBOSSCARFACTORY_API ALBPaintShopBuildAuthority : public AInfo
{
    GENERATED_BODY()

public:
    ALBPaintShopBuildAuthority();

    UFUNCTION(BlueprintPure, Category="Line Boss|Paint Shop|Build")
    float GetPlacementGridCm() const { return 100.0f; }

    /** Mutation-free preflight for the one approved canonical ED-coat placement. */
    bool ValidateApprovedCellPlacement(FName DefinitionId, const FTransform& WorldTransform,
        FString& OutReason) const;

    UFUNCTION(BlueprintPure, Category="Line Boss|Paint Shop|Build")
    void ValidateApprovedCellPlacementForValidation(FName DefinitionId,
        const FTransform& WorldTransform, bool& bOutValid, FString& OutReason) const;

    UFUNCTION(BlueprintPure, Category="Line Boss|Paint Shop|Build")
    ALBPaintShopCellActor* FindCell(FName CellId) const;

    /** Builds exactly one empty deterministic EDCoatDipCell layout. */
    bool BuildApprovedEDCoatDipLayout(FString& OutReason);

    /**
     * Captures topology only. It fails if the owned actor no longer exactly matches the
     * retained topology record and never synthesizes or owns WIP.
     */
    bool CaptureTopologySaveState(FLBPaintShopExperimentalSaveState& OutState,
        FString& OutReason) const;

    /**
     * All-or-nothing topology restore. Callers must pass a copy with WIP and its cell
     * ownership references stripped; the original runtime/lineage state remains theirs.
     */
    bool RestoreTopologySaveState(const FLBPaintShopExperimentalSaveState& State,
        FString& OutReason);

    static FLBPaintShopApprovedEDCoatLayoutItem GetApprovedEDCoatDipLayout();

private:
    UPROPERTY(Transient)
    TObjectPtr<ALBPaintShopCellActor> OwnedCell;

    /** Exact topology-only record last built or restored; WIP is always empty. */
    UPROPERTY(Transient)
    FLBPaintShopExperimentalSaveState TopologyState;

    bool ValidateTopologyState(const FLBPaintShopExperimentalSaveState& State,
        FString& OutReason) const;
    static bool ValidateCellBounds(const ALBPaintShopCellActor* Cell,
        const FTransform& WorldTransform, FString& OutReason);
    static bool GetLocalBounds(const UBoxComponent* Component, FBox& OutBounds);
};
