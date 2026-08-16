#pragma once

#include "CoreMinimal.h"
#include "GameFramework/Actor.h"
#include "LBInboundDeliveryController.generated.h"

class ALBFactoryBuildMachine;
class ALBCoilAGVController;
class USceneComponent;
class UStaticMeshComponent;

/**
 * Append-only inbound origin selector. Retained maps default to LegacyLorry;
 * the unified One Factory opts explicitly into our procedural AGV arrival.
 */
UENUM(BlueprintType)
enum class ELBInboundDeliverySourceMode : uint8
{
    LegacyLorry,
    NativeAGVArrival
};

UENUM(BlueprintType)
enum class ELBInboundDeliveryPhase : uint8
{
    Idle,
    AGVDispatch,
    AGVHandoff,
    AGVReturn,
    Fault,
    TruckReverse,
    DockProving,
    CraneToCoil,
    HookLower,
    HookEngage,
    CoilLift,
    CraneToSaddle,
    CoilLower,
    SaddleRelease,
    /** The unloading cell has removed the coil, but the player has not installed its buffer yet. */
    WaitingForStorage
};

USTRUCT(BlueprintType)
struct FLBInboundDeliverySaveState
{
    GENERATED_BODY()
    UPROPERTY(EditAnywhere, BlueprintReadWrite, SaveGame) int32 SaveVersion = 6;
    /** v6 prevents a native One Factory save from restoring through the legacy lorry path. */
    UPROPERTY(EditAnywhere, BlueprintReadWrite, SaveGame)
    ELBInboundDeliverySourceMode SourceMode = ELBInboundDeliverySourceMode::LegacyLorry;
    UPROPERTY(EditAnywhere, BlueprintReadWrite, SaveGame) ELBInboundDeliveryPhase Phase = ELBInboundDeliveryPhase::Idle;
    UPROPERTY(EditAnywhere, BlueprintReadWrite, SaveGame) FName InboundDockId;
    /** Deprecated v1/v2 endpoint alias retained only so old saves fail closed with a named endpoint. */
    UPROPERTY(EditAnywhere, BlueprintReadWrite, SaveGame) FName CoilStoreId;
    /** Authoritative v3 first-process endpoint: PR002 weighing, identity and material inspection. */
    UPROPERTY(EditAnywhere, BlueprintReadWrite, SaveGame) FName PR002MachineId;
    UPROPERTY(EditAnywhere, BlueprintReadWrite, SaveGame) FName ActiveCoilId;
    UPROPERTY(EditAnywhere, BlueprintReadWrite, SaveGame) FString LastReason;
    UPROPERTY(EditAnywhere, BlueprintReadWrite, SaveGame) int32 CompletedDeliveries = 0;
    UPROPERTY(EditAnywhere, BlueprintReadWrite, SaveGame) float PhaseElapsedSeconds = 0.0f;
    UPROPERTY(EditAnywhere, BlueprintReadWrite, SaveGame) int32 ActiveVisualCoilIndex = INDEX_NONE;
    UPROPERTY(EditAnywhere, BlueprintReadWrite, SaveGame) bool bLorryDocked = false;
    UPROPERTY(EditAnywhere, BlueprintReadWrite, SaveGame) FTransform LorryTransform;
    UPROPERTY(EditAnywhere, BlueprintReadWrite, SaveGame) FTransform ActiveCoilTransform;
    /** v4 preserves the complete moving crane pose so a mid-unload resume cannot snap apart. */
    UPROPERTY(EditAnywhere, BlueprintReadWrite, SaveGame) FTransform CraneBridgeTransform;
    UPROPERTY(EditAnywhere, BlueprintReadWrite, SaveGame) FTransform CraneTrolleyTransform;
    UPROPERTY(EditAnywhere, BlueprintReadWrite, SaveGame) FTransform CraneHoistTransform;
    UPROPERTY(EditAnywhere, BlueprintReadWrite, SaveGame) FTransform CraneHookTransform;
    /** v5 adds the driverless coil-handler chassis; v1-v4 crane fields remain compatible aliases. */
    UPROPERTY(EditAnywhere, BlueprintReadWrite, SaveGame) FTransform CoilHandlerChassisTransform;
};

/**
 * Fail-closed coordinator for the visible inbound-dock to PR002 AGV leg.
 * Legacy maps retain their lorry/dock source. One Factory instead admits one
 * identified coil on the exact procedural native AGV. In both modes the AGV
 * owns it while moving, and PR002 owns it only after a proved handoff and real
 * process link. The normal player-built flow controller moves inspected output
 * onward to storage.
 */
UCLASS(BlueprintType)
class LINEBOSSCARFACTORY_API ALBInboundDeliveryController : public AActor
{
    GENERATED_BODY()

public:
    ALBInboundDeliveryController();
    virtual void BeginPlay() override;
    virtual void Tick(float DeltaSeconds) override;

    UFUNCTION(BlueprintCallable, Category="Cairnwell|Inbound Delivery")
    bool Configure(ALBFactoryBuildMachine* InInboundDock, ALBFactoryBuildMachine* InPR002Cell,
        ALBCoilAGVController* InCoilAGV);

    /**
     * Atomic source-aware binding used by One Factory. NativeAGVArrival proves the
     * exact procedural AGV/deck/coil paths and rejects legacy tag-bound presentation.
     */
    UFUNCTION(BlueprintCallable, Category="Cairnwell|Inbound Delivery")
    bool ConfigureForSourceMode(ALBFactoryBuildMachine* InInboundDock,
        ALBFactoryBuildMachine* InPR002Cell, ALBCoilAGVController* InCoilAGV,
        ELBInboundDeliverySourceMode InSourceMode, FString& OutReason);

    /** Optional map-authored presentation binding. Authority still remains in this controller. */
    UFUNCTION(BlueprintCallable, Category="Cairnwell|Inbound Delivery|Visual Sequence")
    bool ConfigureVisualSequence(AActor* InLorry, AActor* InCraneBridge, AActor* InCraneTrolley,
        AActor* InHoist, AActor* InHook, AActor* InReceivingSaddle,
        const TArray<AActor*>& InTrailerCoils, FVector InLorryApproachPoint, FVector InLorryDockPoint);

    /** Binds the modular lorry/coil-handler/coil components owned by a player-placed inbound package. */
    UFUNCTION(BlueprintCallable, Category="Cairnwell|Inbound Delivery|Visual Sequence")
    bool ConfigurePlayerBuiltVisualSequence(ALBFactoryBuildMachine* InPlayerBuiltInboundDock);

    /** Enables bounded late binding and deterministic deliveries for the clean player-builder map. */
    UFUNCTION(BlueprintCallable, Category="Cairnwell|Inbound Delivery|Player Builder")
    void SetPlayerBuilderBootstrapEnabled(bool bEnabled);

    UFUNCTION(BlueprintPure, Category="Cairnwell|Inbound Delivery|Player Builder")
    bool IsPlayerBuilderBootstrapEnabled() const { return bPlayerBuilderBootstrapEnabled; }

    UFUNCTION(BlueprintPure, Category="Cairnwell|Inbound Delivery|Player Builder")
    bool IsPlayerBuilderBootstrapBound() const { return bPlayerBuilderBootstrapBound; }

    UFUNCTION(BlueprintCallable, Category="Cairnwell|Inbound Delivery")
    bool StartDelivery(FName CoilId, FString& OutReason);

    UFUNCTION(BlueprintCallable, Category="Cairnwell|Inbound Delivery")
    bool ResetFault(FName RecoveryEvidenceId, FString& OutReason);

    UFUNCTION(BlueprintPure, Category="Cairnwell|Inbound Delivery") ELBInboundDeliveryPhase GetPhase() const { return Phase; }
    UFUNCTION(BlueprintPure, Category="Cairnwell|Inbound Delivery") ELBInboundDeliverySourceMode GetSourceMode() const { return SourceMode; }
    UFUNCTION(BlueprintPure, Category="Cairnwell|Inbound Delivery") FName GetActiveCoilId() const { return ActiveCoilId; }
    UFUNCTION(BlueprintPure, Category="Cairnwell|Inbound Delivery") int32 GetCompletedDeliveries() const { return CompletedDeliveries; }
    UFUNCTION(BlueprintPure, Category="Cairnwell|Inbound Delivery") FString GetLastReason() const { return LastReason; }
    UFUNCTION(BlueprintPure, Category="Cairnwell|Inbound Delivery") FName GetInboundDockId() const;
    UFUNCTION(BlueprintPure, Category="Cairnwell|Inbound Delivery") FName GetPR002MachineId() const;
    UFUNCTION(BlueprintPure, Category="Cairnwell|Inbound Delivery",
        meta=(DeprecatedFunction, DeprecationMessage="Inbound delivery now terminates at PR002; use GetPR002MachineId"))
    FName GetCoilStoreId() const { return GetPR002MachineId(); }
    UFUNCTION(BlueprintPure, Category="Cairnwell|Inbound Delivery") int32 GetActiveVisualCoilIndex() const { return ActiveVisualCoilIndex; }
    UFUNCTION(BlueprintPure, Category="Cairnwell|Inbound Delivery") bool IsVisualSequenceBound() const { return bVisualSequenceBound; }

    /** Front/load wheels stay fixed; directional control is exclusively at the rear axle. */
    UFUNCTION(BlueprintPure, Category="Cairnwell|Inbound Delivery|Coil Handler|Steering")
    float GetCoilHandlerFrontWheelSteerAngleDegrees() const { return 0.0f; }
    UFUNCTION(BlueprintPure, Category="Cairnwell|Inbound Delivery|Coil Handler|Steering")
    float GetCoilHandlerRearSteerAngleDegrees() const { return CoilHandlerRearSteerAngleDegrees; }
    /** Signed speed reverses the rear-wheel command for an equal body-yaw request. */
    UFUNCTION(BlueprintPure, Category="Cairnwell|Inbound Delivery|Coil Handler|Steering")
    float CalculateCoilHandlerRearSteerAngleDegrees(float SignedTravelSpeedCmPerSecond,
        float DesiredBodyYawRateDegreesPerSecond) const;
    /** Conservative loaded CHF01 counterweight/coil sweep used by every driven step. */
    UFUNCTION(BlueprintPure, Category="Cairnwell|Inbound Delivery|Coil Handler|Safety")
    float GetCoilHandlerSweptClearanceRadiusCm() const;
    UFUNCTION(BlueprintPure, Category="Cairnwell|Inbound Delivery|Coil Handler|Safety")
    bool IsCoilHandlerSweptPathClear(FVector Start, FVector End) const;

    /** Rebinds a map-authored sequence from stable actor tags after map load. */
    UFUNCTION(BlueprintCallable, Category="Cairnwell|Inbound Delivery|Visual Sequence")
    bool DiscoverAndBindVisualSequence();

    UFUNCTION(BlueprintCallable, Category="Cairnwell|Inbound Delivery|Save")
    FLBInboundDeliverySaveState CaptureSaveState() const;
    UFUNCTION(BlueprintCallable, Category="Cairnwell|Inbound Delivery|Save")
    bool RestoreSaveState(const FLBInboundDeliverySaveState& State);

private:
    /** Map-authored references may persist for the installed scenario; campaign restore rebinds them by ID. */
    UPROPERTY(VisibleInstanceOnly, Category="Cairnwell|Inbound Delivery") TObjectPtr<ALBFactoryBuildMachine> InboundDock;
    UPROPERTY(VisibleInstanceOnly, Category="Cairnwell|Inbound Delivery") TObjectPtr<ALBFactoryBuildMachine> PR002Cell;
    UPROPERTY(VisibleInstanceOnly, Category="Cairnwell|Inbound Delivery") TObjectPtr<ALBCoilAGVController> CoilAGV;
    UPROPERTY(VisibleInstanceOnly, Category="Cairnwell|Inbound Delivery|Visual Sequence") TObjectPtr<AActor> LorryActor;
    UPROPERTY(VisibleInstanceOnly, Category="Cairnwell|Inbound Delivery|Visual Sequence") TObjectPtr<AActor> CraneBridgeActor;
    UPROPERTY(VisibleInstanceOnly, Category="Cairnwell|Inbound Delivery|Visual Sequence") TObjectPtr<AActor> CraneTrolleyActor;
    UPROPERTY(VisibleInstanceOnly, Category="Cairnwell|Inbound Delivery|Visual Sequence") TObjectPtr<AActor> HoistActor;
    UPROPERTY(VisibleInstanceOnly, Category="Cairnwell|Inbound Delivery|Visual Sequence") TObjectPtr<AActor> HookActor;
    UPROPERTY(VisibleInstanceOnly, Category="Cairnwell|Inbound Delivery|Visual Sequence") TObjectPtr<AActor> ReceivingSaddleActor;
    UPROPERTY(VisibleInstanceOnly, Category="Cairnwell|Inbound Delivery|Visual Sequence") TArray<TObjectPtr<AActor>> TrailerCoilActors;
    UPROPERTY(VisibleInstanceOnly, Category="Cairnwell|Inbound Delivery|Visual Sequence") TObjectPtr<USceneComponent> PlayerBridgeComponent;
    UPROPERTY(VisibleInstanceOnly, Category="Cairnwell|Inbound Delivery|Visual Sequence") TObjectPtr<USceneComponent> PlayerTrolleyComponent;
    UPROPERTY(VisibleInstanceOnly, Category="Cairnwell|Inbound Delivery|Visual Sequence") TObjectPtr<USceneComponent> PlayerHoistComponent;
    UPROPERTY(VisibleInstanceOnly, Category="Cairnwell|Inbound Delivery|Visual Sequence") TObjectPtr<USceneComponent> PlayerHookComponent;
    UPROPERTY(VisibleInstanceOnly, Category="Cairnwell|Inbound Delivery|Visual Sequence") TObjectPtr<USceneComponent> PlayerHandlerChassisComponent;
    UPROPERTY(VisibleInstanceOnly, Category="Cairnwell|Inbound Delivery|Visual Sequence") TArray<TObjectPtr<UStaticMeshComponent>> PlayerTrailerCoilComponents;
    UPROPERTY(EditAnywhere, Category="Cairnwell|Inbound Delivery|Visual Sequence", meta=(ClampMin="1.0")) float LorryReverseSpeedCmPerSecond = 180.0f;
    UPROPERTY(EditAnywhere, Category="Cairnwell|Inbound Delivery|Visual Sequence", meta=(ClampMin="1.0")) float CraneTravelSpeedCmPerSecond = 150.0f;
    UPROPERTY(EditAnywhere, Category="Cairnwell|Inbound Delivery|Visual Sequence", meta=(ClampMin="1.0")) float HookTravelSpeedCmPerSecond = 100.0f;
    UPROPERTY(EditAnywhere, Category="Cairnwell|Inbound Delivery|Coil Handler|Motion", meta=(ClampMin="100.0"))
    float CoilHandlerWheelbaseCm = 300.0f;
    UPROPERTY(EditAnywhere, Category="Cairnwell|Inbound Delivery|Coil Handler|Motion", meta=(ClampMin="5.0", ClampMax="80.0"))
    float CoilHandlerMaximumRearSteerAngleDegrees = 70.0f;
    UPROPERTY(EditAnywhere, Category="Cairnwell|Inbound Delivery|Coil Handler|Motion", meta=(ClampMin="5.0"))
    float CoilHandlerRearSteerRateDegreesPerSecond = 76.0f;
    UPROPERTY(EditAnywhere, Category="Cairnwell|Inbound Delivery|Coil Handler|Motion", meta=(ClampMin="5.0"))
    float CoilHandlerMaximumYawRateDegreesPerSecond = 34.0f;
    UPROPERTY(EditAnywhere, Category="Cairnwell|Inbound Delivery|Coil Handler|Motion", meta=(ClampMin="1.0"))
    float CoilHandlerAccelerationCmPerSecondSquared = 95.0f;
    UPROPERTY(EditAnywhere, Category="Cairnwell|Inbound Delivery|Coil Handler|Motion", meta=(ClampMin="1.0"))
    float CoilHandlerDecelerationCmPerSecondSquared = 145.0f;
    UPROPERTY(EditAnywhere, Category="Cairnwell|Inbound Delivery|Coil Handler|Motion", meta=(ClampMin="0.1"))
    float CoilHandlerHeadingResponseSeconds = 0.85f;
    /** Loaded hybrid is 6.39 m overall; this covers body, ram and carried-coil footprint. */
    UPROPERTY(EditAnywhere, Category="Cairnwell|Inbound Delivery|Coil Handler|Safety", meta=(ClampMin="100.0"))
    float CoilHandlerLoadedHalfLengthCm = 320.0f;
    UPROPERTY(EditAnywhere, Category="Cairnwell|Inbound Delivery|Coil Handler|Safety", meta=(ClampMin="50.0"))
    float CoilHandlerLoadedHalfWidthCm = 110.0f;
    UPROPERTY(EditAnywhere, Category="Cairnwell|Inbound Delivery|Coil Handler|Safety", meta=(ClampMin="0.0"))
    float CoilHandlerRearCounterweightOverhangCm = 70.0f;
    UPROPERTY(EditAnywhere, Category="Cairnwell|Inbound Delivery|Coil Handler|Safety", meta=(ClampMin="0.0"))
    float CoilHandlerSteeringSweepMarginCm = 25.0f;
    UPROPERTY(EditAnywhere, Category="Cairnwell|Inbound Delivery|Coil Handler|Safety", meta=(ClampMin="0.0"))
    float CoilHandlerProtectedEnvelopeClearanceCm = 25.0f;
    UPROPERTY(EditAnywhere, Category="Cairnwell|Inbound Delivery|Visual Sequence", meta=(ClampMin="0.1")) float DockProveSeconds = 1.0f;
    UPROPERTY(EditAnywhere, Category="Cairnwell|Inbound Delivery|Visual Sequence", meta=(ClampMin="0.1")) float HookEngageSeconds = 0.75f;
    UPROPERTY(EditAnywhere, Category="Cairnwell|Inbound Delivery|Visual Sequence", meta=(ClampMin="0.1")) float SaddleReleaseSeconds = 0.75f;
    /** Keeps the proved AGV/store transfer visible long enough for player feedback and cameras. */
    UPROPERTY(EditAnywhere, Category="Cairnwell|Inbound Delivery|Visual Sequence", meta=(ClampMin="0.1")) float AGVHandoffSeconds = 1.25f;
    UPROPERTY(EditAnywhere, Category="Cairnwell|Inbound Delivery|Visual Sequence", meta=(ClampMin="25.0")) float LiftClearanceCm = 260.0f;
    UPROPERTY(EditInstanceOnly, Category="Cairnwell|Inbound Delivery|Visual Sequence") bool bAutoDiscoverVisualSequence = true;
    UPROPERTY(EditInstanceOnly, Category="Cairnwell|Inbound Delivery|Player Builder") bool bPlayerBuilderBootstrapEnabled = false;
    UPROPERTY(EditAnywhere, Category="Cairnwell|Inbound Delivery|Player Builder", meta=(ClampMin="0.1"))
    float PlayerBuilderBootstrapIntervalSeconds = 0.5f;
    UPROPERTY(EditInstanceOnly, Category="Cairnwell|Inbound Delivery|Visual Sequence") FVector AuthoredLorryApproachPoint = FVector::ZeroVector;
    UPROPERTY(EditInstanceOnly, Category="Cairnwell|Inbound Delivery|Visual Sequence") FVector AuthoredLorryDockPoint = FVector::ZeroVector;
    ELBInboundDeliveryPhase Phase = ELBInboundDeliveryPhase::Idle;
    FName ActiveCoilId;
    FString LastReason;
    int32 CompletedDeliveries = 0;
    float PhaseElapsedSeconds = 0.0f;
    int32 ActiveVisualCoilIndex = INDEX_NONE;
    bool bLorryDocked = false;
    bool bVisualSequenceBound = false;
    bool bPlayerBuiltComponentSequence = false;
    bool bPlayerBuilderBootstrapBound = false;
    ELBInboundDeliverySourceMode SourceMode = ELBInboundDeliverySourceMode::LegacyLorry;
    float PlayerBuilderBootstrapAccumulator = 0.0f;
    FVector PlayerSaddleLoadPoint = FVector::ZeroVector;
    FVector LorryApproachPoint = FVector::ZeroVector;
    FVector LorryDockPoint = FVector::ZeroVector;
    FVector HookHomeLocation = FVector::ZeroVector;
    FVector HoistHomeLocation = FVector::ZeroVector;
    TArray<FTransform> TrailerCoilHomeTransforms;
    float CoilHandlerTravelSpeedCmPerSecond = 0.0f;
    float CoilHandlerRearSteerAngleDegrees = 0.0f;
    bool bCoilHandlerDriveCommandActive = false;
    bool bCoilHandlerDrivingInReverse = false;
    FVector CoilHandlerActiveRamTarget = FVector::ZeroVector;
    FVector CoilHandlerPathStart = FVector::ZeroVector;
    FVector CoilHandlerPathControlA = FVector::ZeroVector;
    FVector CoilHandlerPathControlB = FVector::ZeroVector;
    FVector CoilHandlerPathEnd = FVector::ZeroVector;
    float CoilHandlerPathAlpha = 0.0f;
    float CoilHandlerPathMaximumCurvature = 0.0f;
    bool bCoilHandlerPathAtDestination = false;

    bool HasRequiredLink() const;
    bool HasRequiredLink(ALBFactoryBuildMachine* CandidateInbound,
        ALBFactoryBuildMachine* CandidatePR002) const;
    void ClearLegacyVisualSequenceBinding();
    bool HasWrappedCoilStorage() const;
    void TickPlayerBuilderBootstrap(float DeltaSeconds);
    bool DiscoverPlayerBuilderEndpoints();
    bool CommitHandoff(FString& OutReason);
    bool DispatchFromSaddle(FString& OutReason);
    bool MoveActorTo(AActor* Actor, const FVector& Target, float Speed, float DeltaSeconds);
    bool MoveComponentTo(USceneComponent* Component, const FVector& Target, float Speed, float DeltaSeconds);
    bool DrivePlayerBuiltCoilHandlerToRamTarget(const FVector& RamTarget,
        float MaximumSpeedCmPerSecond, float DeltaSeconds);
    void ApplyRigidCoilHandlerPose(const FTransform& NewChassisTransform);
    void ResetCoilHandlerDriveState(bool bStraightenRearWheels = true);
    void TickPlayerBuiltVisualSequence(float DeltaSeconds);
    void EnterPhase(ELBInboundDeliveryPhase NewPhase);
    void ApplyCarriedCoilPose(const FVector& Location);
    void LatchFault(const FString& Reason);
};
