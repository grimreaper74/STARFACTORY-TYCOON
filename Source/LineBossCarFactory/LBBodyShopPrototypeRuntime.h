#pragma once

#include "CoreMinimal.h"
#include "GameFramework/Info.h"
#include "LBBodyShopBuildAuthority.h"
#include "LBBodyShopRobotActor.h"
#include "LBBodyShopTypes.h"
#include "LBBodyShopPrototypeRuntime.generated.h"

class ALBBodyShopCellActor;
class ULBBodyShopExperimentalSaveGame;
class USceneComponent;
class UStaticMesh;
class UStaticMeshComponent;

/**
 * Deliberately small state machine for the approved underbody vertical slice.
 * It uses authored fixture poses and deterministic hand-offs only; it is not a
 * robot programming or general production scheduler.
 */
UENUM(BlueprintType)
enum class ELBBodyShopRuntimeStage : uint8
{
    Offline,
    Ready,
    AwaitingPanelStillage,
    TransferringStillage,
    PresentingPanel,
    WeldingUnderbody,
    ConveyingSkid,
    Inspecting,
    OutputBlocked,
    QualityHold,
    Complete,
    Faulted
};

/** The one logical WIP visual owned by the experimental runtime. */
UENUM(BlueprintType)
enum class ELBBodyShopWIPPresentationKind : uint8
{
    None,
    Stillage,
    Panel,
    SkidUnderbody
};

/** Deterministic presentation sample derived from stage progress and authored cell anchors. */
USTRUCT(BlueprintType)
struct FLBBodyShopWIPPresentationSample
{
    GENERATED_BODY()

    UPROPERTY(VisibleAnywhere, BlueprintReadOnly)
    ELBBodyShopWIPPresentationKind Kind = ELBBodyShopWIPPresentationKind::None;

    UPROPERTY(VisibleAnywhere, BlueprintReadOnly)
    FTransform WorldTransform = FTransform::Identity;

    UPROPERTY(VisibleAnywhere, BlueprintReadOnly)
    float Progress01 = 0.0f;
};

/** Exact authored assignments required by the first underbody slice. */
USTRUCT(BlueprintType)
struct FLBBodyShopPilotRobotBinding
{
    GENERATED_BODY()

    UPROPERTY(VisibleAnywhere, BlueprintReadOnly) FName CellDefinitionId = NAME_None;
    UPROPERTY(VisibleAnywhere, BlueprintReadOnly) FName SlotId = NAME_None;
    UPROPERTY(VisibleAnywhere, BlueprintReadOnly) ELBBodyShopRobotRole Role = ELBBodyShopRobotRole::None;
    UPROPERTY(VisibleAnywhere, BlueprintReadOnly) ELBBodyShopToolType Tool = ELBBodyShopToolType::None;
};

/**
 * Runtime authority for the isolated Body Shop underbody demonstration.
 *
 * It is explicitly bound to a new ALBBodyShopBuildAuthority rather than
 * looking up any campaign/Press/legacy actors. All persistence uses the
 * separate experimental v1 save type.
 */
UCLASS(BlueprintType)
class LINEBOSSCARFACTORY_API ALBBodyShopPrototypeRuntime : public AInfo
{
    GENERATED_BODY()

public:
    ALBBodyShopPrototypeRuntime();

    virtual void BeginPlay() override;
    virtual void Tick(float DeltaSeconds) override;

    /** Explicit binding seam used by the isolated map bootstrap. */
    UFUNCTION(BlueprintCallable, Category="Line Boss|Body Shop|Prototype")
    bool BindBuildAuthority(ALBBodyShopBuildAuthority* InBuildAuthority, FString& OutReason);

    /** Constructs, connects and commissions the approved six-cell vertical slice once. */
    UFUNCTION(BlueprintCallable, Category="Line Boss|Body Shop|Prototype")
    bool BuildAndCommissionApprovedUnderbodySlice(FString& OutReason);

    /** Seeds exactly one pilot panel stillage and starts deterministic production. */
    UFUNCTION(BlueprintCallable, Category="Line Boss|Body Shop|Prototype")
    bool StartPilotCycle(FString& OutReason);

    /** Pauses/resumes an already seeded deterministic pilot cycle. */
    UFUNCTION(BlueprintCallable, Category="Line Boss|Body Shop|Prototype")
    bool SetSimulationRunning(bool bInRunning, FString& OutReason);

    /** Explicit validation controls; these are not campaign gameplay controls. */
    UFUNCTION(BlueprintCallable, Category="Line Boss|Body Shop|Prototype|Validation")
    void SetPilotStillageAvailable(bool bInAvailable);

    UFUNCTION(BlueprintCallable, Category="Line Boss|Body Shop|Prototype|Validation")
    void SetOutputBufferBlockedForValidation(bool bInBlocked);

    UFUNCTION(BlueprintCallable, Category="Line Boss|Body Shop|Prototype|Validation")
    void SetNextVisionResultForValidation(bool bInPass);

    /** Player-facing release for one completed output or rejected quality-hold unit. */
    UFUNCTION(BlueprintCallable, Category="Line Boss|Body Shop|Prototype")
    bool ReleaseHeldPilotUnit(FString& OutReason);

    /** Compatibility wrapper retained for existing validation callers. */
    UFUNCTION(BlueprintCallable, Category="Line Boss|Body Shop|Prototype|Validation")
    bool ClearHeldPilotUnitForValidation(FString& OutReason);

    /** Captures the complete isolated graph and its one-pilot WIP state. */
    bool CaptureExperimentalSaveState(FLBBodyShopExperimentalSaveState& OutState,
        FString& OutReason);

    /** Restores topology, robot slots and WIP from experimental v1 only. */
    bool RestoreExperimentalSaveState(const FLBBodyShopExperimentalSaveState& InState,
        FString& OutReason);

    UFUNCTION(BlueprintCallable, Category="Line Boss|Body Shop|Prototype|Save")
    bool SaveToExperimentalSlot(FString& OutReason);

    UFUNCTION(BlueprintCallable, Category="Line Boss|Body Shop|Prototype|Save")
    bool LoadFromExperimentalSlot(FString& OutReason);

    UFUNCTION(BlueprintPure, Category="Line Boss|Body Shop|Prototype")
    bool IsRuntimeInitialised() const { return bRuntimeInitialised; }

    UFUNCTION(BlueprintPure, Category="Line Boss|Body Shop|Prototype")
    bool IsSimulationRunning() const { return bSimulationRunning; }

    UFUNCTION(BlueprintPure, Category="Line Boss|Body Shop|Prototype")
    ELBBodyShopRuntimeStage GetRuntimeStage() const { return RuntimeStage; }

    UFUNCTION(BlueprintPure, Category="Line Boss|Body Shop|Prototype")
    FString GetRuntimeStatusText() const { return RuntimeStatusText; }

    UFUNCTION(BlueprintPure, Category="Line Boss|Body Shop|Prototype")
    int32 GetActivePilotWIPCount() const { return ActiveWIP.Num(); }

    /** Exactly one logical runtime WIP visual is counted, including a skid/body pair. */
    UFUNCTION(BlueprintPure, Category="Line Boss|Body Shop|Prototype")
    int32 GetVisibleRuntimeWIPPresentationCount() const;

    UFUNCTION(BlueprintPure, Category="Line Boss|Body Shop|Prototype")
    ELBBodyShopWIPPresentationKind GetCurrentWIPPresentationKind() const
    {
        return CurrentWIPPresentationSample.Kind;
    }

    UFUNCTION(BlueprintPure, Category="Line Boss|Body Shop|Prototype")
    FTransform GetCurrentWIPPresentationTransform() const
    {
        return CurrentWIPPresentationSample.WorldTransform;
    }

    UFUNCTION(BlueprintPure, Category="Line Boss|Body Shop|Prototype")
    float GetCurrentWIPPresentationProgress01() const
    {
        return CurrentWIPPresentationSample.Progress01;
    }

    UFUNCTION(BlueprintPure, Category="Line Boss|Body Shop|Prototype")
    bool HasValidWIPPresentationArt() const { return bWIPPresentationArtValid; }

    UFUNCTION(BlueprintPure, Category="Line Boss|Body Shop|Prototype")
    FString GetWIPPresentationFailureReason() const { return WIPPresentationFailureReason; }

    /** Runtime-resolved mesh paths; validation must prove visible WIP uses approved art. */
    UFUNCTION(BlueprintPure, Category="Line Boss|Body Shop|Prototype|Presentation")
    FString GetPilotStillagePresentationMeshPath() const;

    UFUNCTION(BlueprintPure, Category="Line Boss|Body Shop|Prototype|Presentation")
    FString GetPilotSkidPresentationMeshPath() const;

    UFUNCTION(BlueprintPure, Category="Line Boss|Body Shop|Prototype|Presentation")
    FString GetPilotUnderbodyPresentationMeshPath() const;

    /** True only when the component and its AInfo owner can both contribute to a game frame. */
    UFUNCTION(BlueprintPure, Category="Line Boss|Body Shop|Prototype|Presentation")
    bool IsPilotSkidPresentationVisibleAndUnhidden() const;

    UFUNCTION(BlueprintPure, Category="Line Boss|Body Shop|Prototype|Presentation")
    bool IsPilotUnderbodyPresentationVisibleAndUnhidden() const;

    /** World-space render bounds exposed for deterministic fixture/conveyor validation. */
    UFUNCTION(BlueprintPure, Category="Line Boss|Body Shop|Prototype|Presentation")
    FVector GetPilotSkidPresentationWorldBoundsMin() const;

    UFUNCTION(BlueprintPure, Category="Line Boss|Body Shop|Prototype|Presentation")
    FVector GetPilotSkidPresentationWorldBoundsMax() const;

    UFUNCTION(BlueprintPure, Category="Line Boss|Body Shop|Prototype|Presentation")
    FVector GetPilotUnderbodyPresentationWorldBoundsMin() const;

    UFUNCTION(BlueprintPure, Category="Line Boss|Body Shop|Prototype|Presentation")
    FVector GetPilotUnderbodyPresentationWorldBoundsMax() const;

    /** Weld-stage pair is above the powered rollers and wholly inside the fixture footprint. */
    UFUNCTION(BlueprintPure, Category="Line Boss|Body Shop|Prototype|Presentation")
    bool IsSkidUnderbodyPresentationAlignedInWeldFixture() const;

    /** Render-thread evidence seam for fresh PIE/package capture validators. */
    UFUNCTION(BlueprintPure, Category="Line Boss|Body Shop|Prototype|Presentation")
    bool WasPilotSkidPresentationRecentlyRendered(float ToleranceSeconds = 1.0f) const;

    UFUNCTION(BlueprintPure, Category="Line Boss|Body Shop|Prototype|Presentation")
    bool WasPilotUnderbodyPresentationRecentlyRendered(float ToleranceSeconds = 1.0f) const;

    UFUNCTION(BlueprintPure, Category="Line Boss|Body Shop|Prototype|Presentation")
    bool WasSkidUnderbodyPresentationRecentlyRendered(float ToleranceSeconds = 1.0f) const;

    /** Raw render-thread timestamp lets evidence capture prove rendering happened after camera placement. */
    UFUNCTION(BlueprintPure, Category="Line Boss|Body Shop|Prototype|Presentation")
    float GetPilotSkidLastRenderTimeOnScreenSeconds() const;

    UFUNCTION(BlueprintPure, Category="Line Boss|Body Shop|Prototype|Presentation")
    float GetPilotUnderbodyLastRenderTimeOnScreenSeconds() const;

    UFUNCTION(BlueprintPure, Category="Line Boss|Body Shop|Prototype")
    int32 GetSpawnedRobotCount() const { return SpawnedRobots.Num(); }

    /** Exact validation seam for simulation/articulation pause-state agreement. */
    UFUNCTION(BlueprintPure, Category="Line Boss|Body Shop|Prototype|Validation")
    int32 GetRunningRobotArticulationCount() const;

    UFUNCTION(BlueprintPure, Category="Line Boss|Body Shop|Prototype")
    ALBBodyShopBuildAuthority* GetBuildAuthority() const { return BuildAuthority.Get(); }

    /** Stable testable contract for the single handling and two spot-weld robots. */
    static TArray<FLBBodyShopPilotRobotBinding> GetRequiredPilotRobotBindings();

    /** Validates the topology/WIP portion that this first slice owns. */
    static bool ValidateRuntimeSaveState(const FLBBodyShopExperimentalSaveState& InState,
        FString& OutReason);

    /** Maps a persisted WIP location to its deterministic next process stage. */
    static ELBBodyShopRuntimeStage GetStageForWIPLocation(FName DefinitionId,
        ELBBodyShopQualityResult Quality, ELBBodyShopCellState CellState);

    /** Pure sampling contract used by runtime playback, save/reload checks and focused tests. */
    static FLBBodyShopWIPPresentationSample SampleWIPPresentation(
        ELBBodyShopRuntimeStage Stage, float StageProgress01,
        const FTransform& StillageDockTransform,
        const FTransform& PanelPresentationTransform,
        const FTransform& UnderbodyFixtureTransform,
        const FTransform& StraightConveyorTransform,
        const FTransform& VisionGateTransform,
        const FTransform& OutputBufferTransform);

private:
    UPROPERTY(VisibleAnywhere) TObjectPtr<USceneComponent> SceneRoot;
    UPROPERTY(VisibleAnywhere) TObjectPtr<UStaticMeshComponent> PilotStillagePresentation;
    UPROPERTY(VisibleAnywhere) TObjectPtr<UStaticMeshComponent> PilotPanelPresentation;
    UPROPERTY(VisibleAnywhere) TObjectPtr<UStaticMeshComponent> PilotSkidPresentation;
    UPROPERTY(VisibleAnywhere) TObjectPtr<UStaticMeshComponent> PilotUnderbodyPresentation;

    UPROPERTY(Transient, VisibleInstanceOnly, Category="Line Boss|Body Shop|Prototype")
    TObjectPtr<ALBBodyShopBuildAuthority> BuildAuthority;

    UPROPERTY(Transient, VisibleInstanceOnly, Category="Line Boss|Body Shop|Prototype")
    TArray<TObjectPtr<ALBBodyShopRobotActor>> SpawnedRobots;

    UPROPERTY(VisibleInstanceOnly, Category="Line Boss|Body Shop|Prototype")
    TArray<FLBBodyShopWIPSaveState> ActiveWIP;

    UPROPERTY(VisibleInstanceOnly, Category="Line Boss|Body Shop|Prototype")
    ELBBodyShopRuntimeStage RuntimeStage = ELBBodyShopRuntimeStage::Offline;

    UPROPERTY(VisibleInstanceOnly, Category="Line Boss|Body Shop|Prototype")
    FString RuntimeStatusText;

    UPROPERTY(VisibleInstanceOnly, Category="Line Boss|Body Shop|Prototype")
    bool bRuntimeInitialised = false;

    UPROPERTY(VisibleInstanceOnly, Category="Line Boss|Body Shop|Prototype")
    bool bSimulationRunning = false;

    UPROPERTY(EditAnywhere, Category="Line Boss|Body Shop|Prototype|Validation")
    bool bPilotStillageAvailable = true;

    UPROPERTY(EditAnywhere, Category="Line Boss|Body Shop|Prototype|Validation")
    bool bOutputBufferBlockedForValidation = false;

    UPROPERTY(EditAnywhere, Category="Line Boss|Body Shop|Prototype|Validation")
    bool bNextVisionPassForValidation = true;

    UPROPERTY(VisibleInstanceOnly, Category="Line Boss|Body Shop|Prototype")
    float StageElapsedSeconds = 0.0f;

    UPROPERTY(VisibleInstanceOnly, Category="Line Boss|Body Shop|Prototype")
    int32 NextWIPSerial = 1;

    UPROPERTY(VisibleInstanceOnly, Category="Line Boss|Body Shop|Prototype")
    int64 NextGenealogySequence = 1;

    UPROPERTY(VisibleInstanceOnly, Category="Line Boss|Body Shop|Prototype|Presentation")
    FLBBodyShopWIPPresentationSample CurrentWIPPresentationSample;

    UPROPERTY(VisibleInstanceOnly, Category="Line Boss|Body Shop|Prototype|Presentation")
    bool bWIPPresentationArtValid = false;

    UPROPERTY(VisibleInstanceOnly, Category="Line Boss|Body Shop|Prototype|Presentation")
    FString WIPPresentationFailureReason;

    UPROPERTY() TSoftObjectPtr<UStaticMesh> PilotStillageMesh;
    UPROPERTY() TSoftObjectPtr<UStaticMesh> PilotSkidMesh;
    UPROPERTY() TSoftObjectPtr<UStaticMesh> PilotUnderbodyMesh;

    bool SpawnConfiguredRobots(FString& OutReason);
    void DestroyRuntimeRobots();
    bool ValidateRequiredRobotBindings(FString& OutReason) const;
    bool IsAuthorityReady(FString& OutReason) const;
    bool IsPilotCycleActive() const;
    void SeedPilotStillage();
    void AdvanceSimulation(float DeltaSeconds);
    void EnterStage(ELBBodyShopRuntimeStage InStage, float InElapsedSeconds = 0.0f);
    void TransferPilotUnitToDefinition(FName TargetDefinitionId);
    void CompleteVisionInspection();
    void RefreshRuntimeCellStates();
    void RefreshRobotPoses();
    void SetSimulationAndArticulationRunning(bool bInRunning);
    void ApplyRobotArticulationRunningState();
    void RefreshPilotPresentation();
    void HidePilotPresentation();
    bool ValidatePilotPresentationArt(FString& OutReason);
    bool TryGetPilotPresentationAnchors(FTransform& OutStillageDock,
        FTransform& OutPanelPresentation, FTransform& OutUnderbodyFixture,
        FTransform& OutStraightConveyor, FTransform& OutVisionGate,
        FTransform& OutOutputBuffer, FString& OutReason) const;
    float GetCurrentStageDurationSeconds() const;
    float GetCurrentStageProgress01() const;
    ALBBodyShopCellActor* FindCellByDefinition(FName DefinitionId) const;
    FLBBodyShopWIPSaveState* GetPilotWIP();
    const FLBBodyShopWIPSaveState* GetPilotWIP() const;
    void ResetRuntimeWIP();
    static bool ValidateApprovedSliceTopology(const FLBBodyShopExperimentalSaveState& InState,
        FString& OutReason);
    static FName GetDefinitionIdForCellId(const FLBBodyShopExperimentalSaveState& InState,
        FName CellId);
    static bool IsActiveFlowStage(ELBBodyShopRuntimeStage InStage);
};
