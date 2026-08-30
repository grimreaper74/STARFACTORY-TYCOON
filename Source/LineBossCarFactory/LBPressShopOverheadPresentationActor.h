#pragma once

#include "CoreMinimal.h"
#include "GameFramework/Actor.h"
#include "LBStatusBeaconComponent.h"
#include "LBPressShopOverheadPresentationActor.generated.h"

class ALBPressShopOverheadVisualLayerActor;
class URectLightComponent;
class USceneComponent;

/** Exact sprite frame used to show a vertical press stroke from true overhead. */
UENUM(BlueprintType)
enum class ELBPressShopOverheadPressFrame : uint8
{
    Open,
    Descending,
    Contact,
    Rising
};

/**
 * Presentation-only runtime adapter for the isolated 2126 overhead press shop.
 *
 * The canonical OneFactory coordinator and production ledger remain the only
 * gameplay authorities.  This actor discovers those authorities after
 * BeginPlay, reads their persisted deterministic progress, and drives imported
 * RGBA sprite layers, native ULBStatusBeaconComponents and restrained task
 * lights.  It never creates UnitIds, advances production, owns genealogy or
 * writes state back into the game.
 */
UCLASS(BlueprintType)
class LINEBOSSCARFACTORY_API ALBPressShopOverheadPresentationActor final :
    public AActor
{
    GENERATED_BODY()

public:
    ALBPressShopOverheadPresentationActor();

    virtual void Tick(float DeltaSeconds) override;

    /** Reads canonical runtime state and updates presentation only. */
    UFUNCTION(BlueprintCallable, Category="Cairnwell|Press Shop|Overhead")
    bool RefreshFromRuntime(FString& OutReason);

    UFUNCTION(BlueprintCallable, Category="Cairnwell|Press Shop|Overhead")
    void SetPresentationEnabled(bool bEnabled);

    UFUNCTION(BlueprintPure, Category="Cairnwell|Press Shop|Overhead")
    bool IsPresentationEnabled() const { return bPresentationEnabled; }

    /** A guarded map/import lane uses these setters for exact world anchors. */
    UFUNCTION(BlueprintCallable, Category="Cairnwell|Press Shop|Overhead")
    bool SetMachineBeaconAnchor(FName MachineId, FVector WorldAnchorCm);

    UFUNCTION(BlueprintCallable, Category="Cairnwell|Press Shop|Overhead")
    bool SetTaskLightAnchor(FName TaskLightId, FVector WorldAnchorCm);

    UFUNCTION(BlueprintPure, Category="Cairnwell|Press Shop|Overhead")
    ULBStatusBeaconComponent* GetStatusBeacon(FName MachineId) const;

    UFUNCTION(BlueprintPure, Category="Cairnwell|Press Shop|Overhead")
    URectLightComponent* GetTaskLight(FName TaskLightId) const;

    UFUNCTION(BlueprintPure, Category="Cairnwell|Press Shop|Overhead")
    int32 GetStatusBeaconCount() const { return StatusBeacons.Num(); }

    UFUNCTION(BlueprintPure, Category="Cairnwell|Press Shop|Overhead")
    int32 GetTaskLightCount() const { return TaskLights.Num(); }

    UFUNCTION(BlueprintPure, Category="Cairnwell|Press Shop|Overhead")
    int32 GetBoundVisualLayerCount() const { return BoundLayers.Num(); }

    /** This is a view of gameplay, never a second gameplay controller. */
    UFUNCTION(BlueprintPure, Category="Cairnwell|Press Shop|Overhead")
    static bool OwnsProductionState() { return false; }

    static FName GetPresentationTag();

    /** Deterministic S02-S06 sequence derived from one PressTrain cycle. */
    static void ComputePressVisualState(float NormalizedCycleProgress,
        FName& OutActiveMachineId,
        ELBPressShopOverheadPressFrame& OutFrame,
        float& OutLocalProgress01,
        bool& bOutTransferActive);

    /** Exact IN04 subphase and local progress for its independent 8-frame sets. */
    static void ComputeDepackVisualState(float NormalizedDepackProgress,
        FName& OutPoseState, float& OutLocalProgress01);

    /**
     * Exact S01 material-flow split from the approved overhead source pack.
     * The empty coil cart completes its authored transfer before payoff and
     * strip-feed frame sequences begin; artwork still never advances gameplay.
     */
    static void ComputeCoilFeedVisualState(float NormalizedCycleProgress,
        float& OutCartTravel01, float& OutPayoffProgress01,
        bool& bOutCartMoving, bool& bOutPayoffActive);

    /**
     * Builds source-authorised runtime endpoints for transform channels whose
     * spawn registry intentionally retained only a placed anchor.
     */
    static bool BuildAuthoredMotionRange(FName MotionChannel,
        const FTransform& PlacedTransform, FTransform& OutStart,
        FTransform& OutEnd);

    /** Shared fail-safe mapping used by runtime and automation tests. */
    static ELBStatusBeaconState ResolveBeaconState(bool bCommissioned,
        bool bLinePaused, bool bDepartmentFaulted, bool bOutputBlocked,
        bool bMachineActive, bool bMachineMoving, bool bWaitingAtGate);

private:
    struct FMachineRuntimeState
    {
        ELBStatusBeaconState Beacon = ELBStatusBeaconState::Off;
        float Progress01 = 0.0f;
        ELBPressShopOverheadPressFrame PressFrame =
            ELBPressShopOverheadPressFrame::Open;
        FName PoseState = TEXT("PARKED");
        bool bActive = false;
        bool bTransferActive = false;
    };

    UPROPERTY()
    TObjectPtr<USceneComponent> SceneRoot;

    UPROPERTY(VisibleAnywhere, Category="Cairnwell|Press Shop|Overhead")
    TArray<TObjectPtr<ULBStatusBeaconComponent>> StatusBeacons;

    UPROPERTY(VisibleAnywhere, Category="Cairnwell|Press Shop|Overhead")
    TArray<TObjectPtr<URectLightComponent>> TaskLights;

    TArray<FName> BeaconMachineIds;
    TArray<FName> TaskLightIds;
    TArray<FName> TaskLightMachineIds;
    TArray<TWeakObjectPtr<ALBPressShopOverheadVisualLayerActor>> BoundLayers;
    TMap<FName, FMachineRuntimeState> MachineStates;

    bool bPresentationEnabled = true;
    float BindingRefreshAccumulator = 0.0f;

    void RefreshLayerBindings();
    void SuppressSupersededPressPresentation() const;
    void ApplyLayerStates();
    void ApplyBeaconStates();
    void ApplyTaskLightStates(bool bPressCommissioned,
        bool bPressFaulted, bool bLinePaused);
    void ResetMachineStates(ELBStatusBeaconState DefaultState);
    FMachineRuntimeState& StateFor(FName MachineId);
    static FName FrameStateName(ELBPressShopOverheadPressFrame Frame);
    static FName BeaconColourName(ELBStatusBeaconState State);
};
