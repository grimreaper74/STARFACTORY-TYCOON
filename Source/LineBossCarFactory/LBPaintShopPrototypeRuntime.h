#pragma once

#include "CoreMinimal.h"
#include "GameFramework/Info.h"
#include "LBPaintShopBuildAuthority.h"
#include "LBPaintShopCellActor.h"
#include "LBPaintShopExperimentalSaveGame.h"
#include "LBPaintShopPrototypeRuntime.generated.h"

class ALBBodyWeldLineActor;

/** Deterministic stages owned by the isolated one-cell ED-coat runtime. */
UENUM(BlueprintType)
enum class ELBPaintShopPrototypePhase : uint8
{
    Uninitialized,
    Starved,
    Loading,
    Descending,
    Immersing,
    Rising,
    Draining,
    OutputReady,
    Faulted
};

/**
 * Process authority for the first isolated Paint Shop vertical slice. Placement and
 * cell ownership remain in ALBPaintShopBuildAuthority; this actor owns at most one WIP.
 * It creates no packaged runtime child components; AInfo's editor-only sprite may exist in
 * editor builds. Tick delegates to the same explicit deterministic step.
 */
UCLASS(BlueprintType)
class LINEBOSSCARFACTORY_API ALBPaintShopPrototypeRuntime : public AInfo
{
    GENERATED_BODY()

public:
    ALBPaintShopPrototypeRuntime();

    virtual void Tick(float DeltaSeconds) override;

    /** Binds the one externally owned topology authority before initialization. */
    UFUNCTION(BlueprintCallable, Category="Line Boss|Paint Shop|Runtime")
    bool BindBuildAuthority(ALBPaintShopBuildAuthority* InAuthority, FString& OutReason);

    /** Creates exactly one approved EDCoatDip cell through the bound build authority. */
    UFUNCTION(BlueprintCallable, Category="Line Boss|Paint Shop|Runtime")
    bool InitializePrototype(FString& OutReason);

    /**
     * All fallible capacity, duplicate, topology, lineage-save, and presentation preflights
     * complete before the Weld actor is acknowledged. A successful acknowledgement is then
     * committed by plain assignment, preserving the exact returned FLBBodyInWhiteRecord.
     */
    UFUNCTION(BlueprintCallable, Category="Line Boss|Paint Shop|Runtime")
    bool AcceptAndAcknowledgeBodyInWhite(ALBBodyWeldLineActor* SourceLine,
        FName BodyId, FName CarrierId, FString& OutReason);

    UFUNCTION(BlueprintCallable, Category="Line Boss|Paint Shop|Runtime")
    void AdvanceSimulation(float DeltaSeconds);

    UFUNCTION(BlueprintCallable, Category="Line Boss|Paint Shop|Runtime")
    void SetPaused(bool bInPaused);

    UFUNCTION(BlueprintCallable, Category="Line Boss|Paint Shop|Runtime")
    void SetOutputBlocked(bool bInBlocked);

    /** Releases the retained coated WIP only when the downstream output is unblocked. */
    UFUNCTION(BlueprintCallable, Category="Line Boss|Paint Shop|Runtime")
    bool ReleaseOutput(FLBPaintShopWIPSaveState& OutReleasedWIP, FString& OutReason);

    /** Captures topology from the build authority, then adds the exact runtime-owned WIP. */
    bool CaptureSaveState(FLBPaintShopExperimentalSaveState& OutState,
        FString& OutReason) const;

    /** Restores topology from a stripped copy and reconstructs phase from cell progress. */
    bool RestoreSaveState(const FLBPaintShopExperimentalSaveState& State,
        FString& OutReason);

    /** Persists only the isolated Paint prototype schema and slot. */
    UFUNCTION(BlueprintCallable, Category="Line Boss|Paint Shop|Runtime|Save")
    bool SaveToExperimentalSlot(FString& OutReason) const;

    /** Validates the complete isolated payload before applying any runtime mutation. */
    UFUNCTION(BlueprintCallable, Category="Line Boss|Paint Shop|Runtime|Save")
    bool LoadFromExperimentalSlot(FString& OutReason);

#if WITH_DEV_AUTOMATION_TESTS
    /** Test-only unique-slot seam; production and campaign slots are rejected. */
    bool SaveToAutomationSlot(const FString& SlotName, FString& OutReason) const;
    bool LoadFromAutomationSlot(const FString& SlotName, FString& OutReason);
#endif

    UFUNCTION(BlueprintPure, Category="Line Boss|Paint Shop|Runtime")
    bool IsInitialized() const { return bInitialized; }

    UFUNCTION(BlueprintPure, Category="Line Boss|Paint Shop|Runtime")
    bool HasActiveWIP() const { return bHasActiveWIP; }

    UFUNCTION(BlueprintPure, Category="Line Boss|Paint Shop|Runtime")
    bool IsPaused() const { return bPaused; }

    UFUNCTION(BlueprintPure, Category="Line Boss|Paint Shop|Runtime")
    bool IsStarved() const { return bInitialized && !bHasActiveWIP && !bProcessFaulted; }

    UFUNCTION(BlueprintPure, Category="Line Boss|Paint Shop|Runtime")
    bool IsOutputBlocked() const { return bOutputBlocked; }

    UFUNCTION(BlueprintPure, Category="Line Boss|Paint Shop|Runtime")
    bool IsProcessFaulted() const { return bProcessFaulted; }

    UFUNCTION(BlueprintPure, Category="Line Boss|Paint Shop|Runtime")
    FString GetProcessFaultReason() const { return ProcessFaultReason; }

    UFUNCTION(BlueprintPure, Category="Line Boss|Paint Shop|Runtime")
    ELBPaintShopPrototypePhase GetPhase() const { return Phase; }

    UFUNCTION(BlueprintPure, Category="Line Boss|Paint Shop|Runtime")
    float GetPhaseProgress01() const { return PhaseProgress01; }

    UFUNCTION(BlueprintPure, Category="Line Boss|Paint Shop|Runtime")
    float GetCycleProgress01() const { return CycleProgress01; }

    UFUNCTION(BlueprintPure, Category="Line Boss|Paint Shop|Runtime")
    bool GetActiveWIP(FLBPaintShopWIPSaveState& OutWIP) const;

    UFUNCTION(BlueprintPure, Category="Line Boss|Paint Shop|Runtime")
    ALBPaintShopBuildAuthority* GetBuildAuthority() const { return BuildAuthority; }

    UFUNCTION(BlueprintPure, Category="Line Boss|Paint Shop|Runtime")
    ALBPaintShopCellActor* GetEDCoatCell() const;

    UFUNCTION(BlueprintPure, Category="Line Boss|Paint Shop|Runtime")
    static float GetTotalCycleDurationSeconds() { return 10.0f; }

private:
    static constexpr float LoadEndProgress01 = 0.10f;
    static constexpr float DescendEndProgress01 = 0.30f;
    static constexpr float ImmerseEndProgress01 = 0.60f;
    static constexpr float RiseEndProgress01 = 0.80f;
    static constexpr float DrainEndProgress01 = 1.00f;

    UPROPERTY(Transient)
    TObjectPtr<ALBPaintShopBuildAuthority> BuildAuthority;

    UPROPERTY(VisibleInstanceOnly)
    bool bInitialized = false;

    UPROPERTY(VisibleInstanceOnly)
    bool bHasActiveWIP = false;

    UPROPERTY(VisibleInstanceOnly)
    FLBPaintShopWIPSaveState ActiveWIP;

    UPROPERTY(VisibleInstanceOnly)
    bool bPaused = false;

    UPROPERTY(VisibleInstanceOnly)
    bool bOutputBlocked = false;

    UPROPERTY(VisibleInstanceOnly)
    bool bProcessFaulted = false;

    UPROPERTY(VisibleInstanceOnly)
    FString ProcessFaultReason;

    UPROPERTY(VisibleInstanceOnly)
    ELBPaintShopPrototypePhase Phase = ELBPaintShopPrototypePhase::Uninitialized;

    UPROPERTY(VisibleInstanceOnly)
    float PhaseProgress01 = 0.0f;

    UPROPERTY(VisibleInstanceOnly)
    float CycleProgress01 = 0.0f;

    UPROPERTY(VisibleInstanceOnly)
    int32 NextWIPSerial = 1;

    UPROPERTY(VisibleInstanceOnly)
    int64 NextGenealogySequence = 1;

    void UpdatePhaseFromCycleProgress();
    bool ApplyPresentation(FString& OutReason);
    void EnterProcessFault(const FString& Reason);
    bool BuildTentativeAcceptedSave(const FLBBodyInWhiteRecord& Candidate,
        FName CarrierId, FLBPaintShopExperimentalSaveState& OutState,
        FString& OutReason) const;
    bool SaveToSlot(const FString& SlotName, int32 UserIndex, FString& OutReason) const;
    bool LoadFromSlot(const FString& SlotName, int32 UserIndex, FString& OutReason);
    static bool ValidateRuntimeSaveShape(const FLBPaintShopExperimentalSaveState& State,
        FString& OutReason);
    static FLBPaintShopCellPresentationState MakePresentationState(bool bHasWIP,
        float InCycleProgress01, bool bFaulted);
};
