#pragma once

#include "CoreMinimal.h"
#include "GameFramework/Actor.h"
#include "LBPR010Station.generated.h"

class USceneComponent;
class AActor;
class ATextRenderActor;

UENUM(BlueprintType)
enum class ELBPR010State : uint8
{
    Isolated,
    Ready,
    ReservationWait,
    LaneSelect,
    Transfer,
    Stored,
    TrainReserved,
    VehicleHandoff,
    Stopping,
    Fault
};

UENUM(BlueprintType)
enum class ELBPR010Fault : uint8
{
    None,
    EmergencyStopActive,
    SafetyCircuitFault,
    GuardInterlockOpen,
    ControlledCrossingInterlock,
    ShuttleFault,
    LaneFull,
    ReservationMismatch,
    HandoffUnavailable,
    QualityHoldOccupied
};

UENUM(BlueprintType)
enum class ELBPR010Command : uint8
{
    PowerOn,
    PowerOff,
    Start,
    ControlledStop,
    AcknowledgeAlarm,
    Reset,
    RequestIsolation,
    ReleaseIsolation
};

USTRUCT(BlueprintType)
struct FLBPR010StackManifest
{
    GENERATED_BODY()

    UPROPERTY(EditAnywhere, BlueprintReadWrite, SaveGame) FName StackId;
    UPROPERTY(EditAnywhere, BlueprintReadWrite, SaveGame) TArray<FName> BlankIds;
};

USTRUCT(BlueprintType)
struct FLBPR010HMIStatus
{
    GENERATED_BODY()

    UPROPERTY(BlueprintReadOnly) FName StationId = TEXT("PR-010");
    UPROPERTY(BlueprintReadOnly) ELBPR010State State = ELBPR010State::Isolated;
    UPROPERTY(BlueprintReadOnly) ELBPR010Fault ActiveFault = ELBPR010Fault::None;
    UPROPERTY(BlueprintReadOnly) TArray<int32> LaneStackCounts;
    UPROPERTY(BlueprintReadOnly) TArray<FName> LaneReservations;
    UPROPERTY(BlueprintReadOnly) int32 ActiveLaneIndex = -1;
    UPROPERTY(BlueprintReadOnly) FName InboundStackId;
    UPROPERTY(BlueprintReadOnly) FName QualityHoldStackId;
    UPROPERTY(BlueprintReadOnly) FName LastReleasedStackId;
    UPROPERTY(BlueprintReadOnly) int32 LastReleasedBlankCount = 0;
    UPROPERTY(BlueprintReadOnly) int32 TotalStacksStored = 0;
    UPROPERTY(BlueprintReadOnly) int32 TotalStacksDispatched = 0;
    UPROPERTY(BlueprintReadOnly) float PhaseProgress = 0.0f;
    UPROPERTY(BlueprintReadOnly) bool bControlPowerOn = false;
    UPROPERTY(BlueprintReadOnly) bool bGuardsClosed = false;
    UPROPERTY(BlueprintReadOnly) bool bCrossingClosed = false;
    UPROPERTY(BlueprintReadOnly) bool bCrossingClear = false;
    UPROPERTY(BlueprintReadOnly) bool bShuttleHealthy = false;
    UPROPERTY(BlueprintReadOnly) bool bVehicleHandoffReady = false;
    UPROPERTY(BlueprintReadOnly) bool bSafetyCircuitHealthy = false;
    UPROPERTY(BlueprintReadOnly) bool bEmergencyStopActive = false;
    UPROPERTY(BlueprintReadOnly) bool bAlarmAcknowledged = false;
    UPROPERTY(BlueprintReadOnly) bool bIsolationRequested = false;
    UPROPERTY(BlueprintReadOnly) bool bZeroEnergyProved = false;
    UPROPERTY(BlueprintReadOnly) bool bRestartRequiredAfterLoad = false;
    UPROPERTY(BlueprintReadOnly) FName LastCommandSource;
    UPROPERTY(BlueprintReadOnly) FName LastSafetyEvidenceId;
    UPROPERTY(BlueprintReadOnly) bool bCanStart = false;
    UPROPERTY(BlueprintReadOnly) TArray<FText> BlockingReasons;
};

USTRUCT(BlueprintType)
struct FLBPR010SaveState
{
    GENERATED_BODY()

    UPROPERTY(EditAnywhere, BlueprintReadWrite, SaveGame) int32 Version = 2;
    UPROPERTY(EditAnywhere, BlueprintReadWrite, SaveGame) FName StationId = TEXT("PR-010");
    UPROPERTY(EditAnywhere, BlueprintReadWrite, SaveGame) ELBPR010State State = ELBPR010State::Isolated;
    UPROPERTY(EditAnywhere, BlueprintReadWrite, SaveGame) ELBPR010Fault ActiveFault = ELBPR010Fault::None;
    UPROPERTY(EditAnywhere, BlueprintReadWrite, SaveGame) TArray<FName> LaneAStackIds;
    UPROPERTY(EditAnywhere, BlueprintReadWrite, SaveGame) TArray<FName> LaneBStackIds;
    UPROPERTY(EditAnywhere, BlueprintReadWrite, SaveGame) TArray<FName> LaneCStackIds;
    UPROPERTY(EditAnywhere, BlueprintReadWrite, SaveGame) TArray<FName> LaneDStackIds;
    UPROPERTY(EditAnywhere, BlueprintReadWrite, SaveGame) TArray<FName> LaneReservations;
    UPROPERTY(EditAnywhere, BlueprintReadWrite, SaveGame) int32 ActiveLaneIndex = -1;
    UPROPERTY(EditAnywhere, BlueprintReadWrite, SaveGame) int32 PendingDispatchLaneIndex = -1;
    UPROPERTY(EditAnywhere, BlueprintReadWrite, SaveGame) FName InboundStackId;
    UPROPERTY(EditAnywhere, BlueprintReadWrite, SaveGame) FName QualityHoldStackId;
    UPROPERTY(EditAnywhere, BlueprintReadWrite, SaveGame) FName LastReleasedStackId;
    UPROPERTY(EditAnywhere, BlueprintReadWrite, SaveGame) TArray<FName> InboundBlankIds;
    UPROPERTY(EditAnywhere, BlueprintReadWrite, SaveGame) TArray<FLBPR010StackManifest> StoredStackManifests;
    UPROPERTY(EditAnywhere, BlueprintReadWrite, SaveGame) TArray<FName> LastReleasedBlankIds;
    UPROPERTY(EditAnywhere, BlueprintReadWrite, SaveGame) int32 TotalStacksStored = 0;
    UPROPERTY(EditAnywhere, BlueprintReadWrite, SaveGame) int32 TotalStacksDispatched = 0;
    UPROPERTY(EditAnywhere, BlueprintReadWrite, SaveGame) bool bInboundQualityHoldRequested = false;
    UPROPERTY(EditAnywhere, BlueprintReadWrite, SaveGame) bool bControlPowerOn = false;
    UPROPERTY(EditAnywhere, BlueprintReadWrite, SaveGame) bool bGuardsClosed = true;
    UPROPERTY(EditAnywhere, BlueprintReadWrite, SaveGame) bool bCrossingClosed = true;
    UPROPERTY(EditAnywhere, BlueprintReadWrite, SaveGame) bool bCrossingClear = true;
    UPROPERTY(EditAnywhere, BlueprintReadWrite, SaveGame) bool bShuttleHealthy = true;
    UPROPERTY(EditAnywhere, BlueprintReadWrite, SaveGame) bool bVehicleHandoffReady = true;
    UPROPERTY(EditAnywhere, BlueprintReadWrite, SaveGame) bool bSafetyCircuitHealthy = true;
    UPROPERTY(EditAnywhere, BlueprintReadWrite, SaveGame) bool bEmergencyStopActive = false;
    UPROPERTY(EditAnywhere, BlueprintReadWrite, SaveGame) bool bAlarmAcknowledged = false;
    UPROPERTY(EditAnywhere, BlueprintReadWrite, SaveGame) bool bIsolationRequested = false;
    UPROPERTY(EditAnywhere, BlueprintReadWrite, SaveGame) bool bZeroEnergyProved = false;
    UPROPERTY(EditAnywhere, BlueprintReadWrite, SaveGame) bool bRestartRequiredAfterLoad = false;
    UPROPERTY(EditAnywhere, BlueprintReadWrite, SaveGame) FName LastCommandSource;
    UPROPERTY(EditAnywhere, BlueprintReadWrite, SaveGame) FName LastSafetyEvidenceId;
};

DECLARE_DYNAMIC_MULTICAST_DELEGATE_TwoParams(FLBPR010StateChanged, ELBPR010State, PreviousState, ELBPR010State, NewState);
DECLARE_DYNAMIC_MULTICAST_DELEGATE_OneParam(FLBPR010FaultRaised, ELBPR010Fault, Fault);

/** Remote four-lane blank-buffer, reservation and autonomous vehicle-handoff authority. */
UCLASS(BlueprintType)
class LINEBOSSCARFACTORY_API ALBPR010Station : public AActor
{
    GENERATED_BODY()

public:
    ALBPR010Station();
    virtual void BeginPlay() override;
    virtual void Tick(float DeltaSeconds) override;

    UFUNCTION(BlueprintCallable, Category="Cairnwell|PR-010") void ConfigureHealthyInputs();
    UFUNCTION(BlueprintCallable, Category="Cairnwell|PR-010|Material Flow") bool OfferUpstreamStack(FName StackId, bool bRouteToQualityHold = false);
    UFUNCTION(BlueprintCallable, Category="Cairnwell|PR-010|Material Flow") bool OfferUpstreamStackWithManifest(FName StackId, const TArray<FName>& BlankIds, bool bRouteToQualityHold = false);
    UFUNCTION(BlueprintPure, Category="Cairnwell|PR-010|Traceability") bool GetBlankIdsForStack(FName StackId, TArray<FName>& BlankIds) const;
    UFUNCTION(BlueprintPure, Category="Cairnwell|PR-010|Traceability") TArray<FName> GetLastReleasedBlankIds() const { return LastReleasedBlankIds; }
    UFUNCTION(BlueprintPure, Category="Cairnwell|PR-010|Material Flow") bool CanAcceptUpstreamStack(TArray<FText>& BlockingReasons) const;
    UFUNCTION(BlueprintCallable, Category="Cairnwell|PR-010|Dispatch") bool RequestLaneDispatch(int32 LaneIndex, FName TrainReservationId);
    UFUNCTION(BlueprintCallable, Category="Cairnwell|PR-010|Presentation") bool BindPresentationActor(FName SemanticObjectName, FName SemanticRole, AActor* VisualActor);
    UFUNCTION(BlueprintCallable, Category="Cairnwell|PR-010|HMI") bool BindHMITextActor(FName FieldName, ATextRenderActor* TextActor);
    UFUNCTION(BlueprintCallable, Category="Cairnwell|PR-010|Safety") void SetGuardsClosed(bool bClosed);
    UFUNCTION(BlueprintCallable, Category="Cairnwell|PR-010|Safety") void SetControlledCrossing(bool bClosed, bool bClear);
    UFUNCTION(BlueprintCallable, Category="Cairnwell|PR-010") void SetShuttleHealthy(bool bHealthy);
    UFUNCTION(BlueprintCallable, Category="Cairnwell|PR-010") void SetVehicleHandoffReady(bool bReady);
    UFUNCTION(BlueprintCallable, Category="Cairnwell|PR-010|Safety") void SetSafetyCircuitHealthy(bool bHealthy);
    UFUNCTION(BlueprintCallable, Category="Cairnwell|PR-010|Safety") void SetEmergencyStopActive(bool bActive);
    UFUNCTION(BlueprintCallable, Category="Cairnwell|PR-010|Remote") bool ExecuteRemoteCommand(ELBPR010Command Command, FName CommandSource, FName AuthorityId);
    UFUNCTION(BlueprintCallable, Category="Cairnwell|PR-010|Safety") bool AcknowledgeAlarm(FName CommandSource);
    UFUNCTION(BlueprintCallable, Category="Cairnwell|PR-010|Safety") bool ConfirmZeroEnergyIsolation(bool bZeroMotionVerified, bool bStoredEnergyReleased, FName EvidenceId);
    UFUNCTION(BlueprintPure, Category="Cairnwell|PR-010") bool CanStart(TArray<FText>& BlockingReasons) const;
    UFUNCTION(BlueprintPure, Category="Cairnwell|PR-010|HMI") FLBPR010HMIStatus GetHMIStatus() const;
    UFUNCTION(BlueprintPure, Category="Cairnwell|PR-010|Save") FLBPR010SaveState CaptureSaveState() const;
    UFUNCTION(BlueprintCallable, Category="Cairnwell|PR-010|Save") bool RestoreSaveState(const FLBPR010SaveState& SavedState);

    UPROPERTY(BlueprintAssignable, Category="Cairnwell|PR-010") FLBPR010StateChanged OnStateChanged;
    UPROPERTY(BlueprintAssignable, Category="Cairnwell|PR-010") FLBPR010FaultRaised OnFaultRaised;

protected:
    UPROPERTY(VisibleAnywhere, BlueprintReadOnly) TObjectPtr<USceneComponent> StationRoot;
    UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category="Cairnwell|PR-010|Presentation") TObjectPtr<USceneComponent> ShuttleMover;
    UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category="Cairnwell|PR-010|Presentation") TArray<TObjectPtr<USceneComponent>> LaneRollMovers;
    UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category="Cairnwell|PR-010|Presentation") TArray<TObjectPtr<USceneComponent>> LaneStopMovers;
    UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category="Cairnwell|PR-010|Presentation") TArray<TObjectPtr<USceneComponent>> ReservationGateMovers;
    UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category="Cairnwell|PR-010|Presentation") TObjectPtr<USceneComponent> QualityHoldMover;
    UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category="Cairnwell|PR-010|Presentation") TArray<TObjectPtr<AActor>> BoundRollActors;
    UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category="Cairnwell|PR-010|Presentation") TArray<int32> BoundRollLaneIndices;
    UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category="Cairnwell|PR-010|Presentation") TArray<TObjectPtr<AActor>> BoundGateActors;
    UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category="Cairnwell|PR-010|Presentation") TArray<int32> BoundGateLaneIndices;
    UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category="Cairnwell|PR-010|HMI") TMap<FName, TObjectPtr<ATextRenderActor>> BoundHMITextActors;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, SaveGame, Category="Cairnwell|State") ELBPR010State State = ELBPR010State::Isolated;
    UPROPERTY(EditAnywhere, BlueprintReadWrite, SaveGame, Category="Cairnwell|State") ELBPR010Fault ActiveFault = ELBPR010Fault::None;
    UPROPERTY(EditAnywhere, BlueprintReadWrite, SaveGame, Category="Cairnwell|Inventory") TArray<FName> LaneAStackIds;
    UPROPERTY(EditAnywhere, BlueprintReadWrite, SaveGame, Category="Cairnwell|Inventory") TArray<FName> LaneBStackIds;
    UPROPERTY(EditAnywhere, BlueprintReadWrite, SaveGame, Category="Cairnwell|Inventory") TArray<FName> LaneCStackIds;
    UPROPERTY(EditAnywhere, BlueprintReadWrite, SaveGame, Category="Cairnwell|Inventory") TArray<FName> LaneDStackIds;
    UPROPERTY(EditAnywhere, BlueprintReadWrite, SaveGame, Category="Cairnwell|Reservations") TArray<FName> LaneReservations;
    UPROPERTY(EditAnywhere, BlueprintReadWrite, SaveGame, Category="Cairnwell|State") int32 ActiveLaneIndex = -1;
    UPROPERTY(EditAnywhere, BlueprintReadWrite, SaveGame, Category="Cairnwell|State") int32 PendingDispatchLaneIndex = -1;
    UPROPERTY(EditAnywhere, BlueprintReadWrite, SaveGame, Category="Cairnwell|Traceability") FName InboundStackId;
    UPROPERTY(EditAnywhere, BlueprintReadWrite, SaveGame, Category="Cairnwell|Traceability") FName QualityHoldStackId;
    UPROPERTY(EditAnywhere, BlueprintReadWrite, SaveGame, Category="Cairnwell|Traceability") FName LastReleasedStackId;
    UPROPERTY(EditAnywhere, BlueprintReadWrite, SaveGame, Category="Cairnwell|Traceability") TArray<FName> InboundBlankIds;
    UPROPERTY(EditAnywhere, BlueprintReadWrite, SaveGame, Category="Cairnwell|Traceability") TArray<FLBPR010StackManifest> StoredStackManifests;
    UPROPERTY(EditAnywhere, BlueprintReadWrite, SaveGame, Category="Cairnwell|Traceability") TArray<FName> LastReleasedBlankIds;
    UPROPERTY(EditAnywhere, BlueprintReadWrite, SaveGame, Category="Cairnwell|Production") int32 TotalStacksStored = 0;
    UPROPERTY(EditAnywhere, BlueprintReadWrite, SaveGame, Category="Cairnwell|Production") int32 TotalStacksDispatched = 0;
    UPROPERTY(EditAnywhere, BlueprintReadWrite, SaveGame, Category="Cairnwell|Quality") bool bInboundQualityHoldRequested = false;
    UPROPERTY(EditAnywhere, BlueprintReadWrite, SaveGame, Category="Cairnwell|State") bool bControlPowerOn = false;
    UPROPERTY(EditAnywhere, BlueprintReadWrite, SaveGame, Category="Cairnwell|Safety") bool bGuardsClosed = true;
    UPROPERTY(EditAnywhere, BlueprintReadWrite, SaveGame, Category="Cairnwell|Safety") bool bCrossingClosed = true;
    UPROPERTY(EditAnywhere, BlueprintReadWrite, SaveGame, Category="Cairnwell|Safety") bool bCrossingClear = true;
    UPROPERTY(EditAnywhere, BlueprintReadWrite, SaveGame, Category="Cairnwell|State") bool bShuttleHealthy = true;
    UPROPERTY(EditAnywhere, BlueprintReadWrite, SaveGame, Category="Cairnwell|State") bool bVehicleHandoffReady = true;
    UPROPERTY(EditAnywhere, BlueprintReadWrite, SaveGame, Category="Cairnwell|Safety") bool bSafetyCircuitHealthy = true;
    UPROPERTY(EditAnywhere, BlueprintReadWrite, SaveGame, Category="Cairnwell|Safety") bool bEmergencyStopActive = false;
    UPROPERTY(EditAnywhere, BlueprintReadWrite, SaveGame, Category="Cairnwell|Safety") bool bAlarmAcknowledged = false;
    UPROPERTY(EditAnywhere, BlueprintReadWrite, SaveGame, Category="Cairnwell|Safety") bool bIsolationRequested = false;
    UPROPERTY(EditAnywhere, BlueprintReadWrite, SaveGame, Category="Cairnwell|Safety") bool bZeroEnergyProved = false;
    UPROPERTY(EditAnywhere, BlueprintReadWrite, SaveGame, Category="Cairnwell|State") bool bRestartRequiredAfterLoad = false;
    UPROPERTY(EditAnywhere, BlueprintReadWrite, SaveGame, Category="Cairnwell|Authority") FName LastCommandSource;
    UPROPERTY(EditAnywhere, BlueprintReadWrite, SaveGame, Category="Cairnwell|Safety") FName LastSafetyEvidenceId;
    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="Cairnwell|Authority") FName RemoteAuthorityId = TEXT("CW.MW.CONTROL_ROOM");

private:
    float PhaseElapsedSeconds = 0.0f;
    bool bControlledStopRequested = false;
    bool bPresentationBasesCaptured = false;
    FTransform ShuttleBaseTransform;
    TArray<FTransform> LaneRollBaseTransforms;
    TArray<FTransform> LaneStopBaseTransforms;
    TArray<FTransform> ReservationGateBaseTransforms;
    FTransform QualityHoldBaseTransform;
    TArray<FRotator> BoundRollBaseRotations;
    TArray<FRotator> BoundGateBaseRotations;

    void SetState(ELBPR010State NewState);
    void RaiseFault(ELBPR010Fault Fault);
    void EvaluatePermissives();
    void AdvanceState();
    void CapturePresentationBases();
    void UpdatePresentation();
    void UpdateHMITextPresentation();
    float GetPhaseDuration() const;
    float GetPhaseProgress() const;
    bool IsMovingState() const;
    bool StartCycle();
    void RequestControlledStop();
    bool ResetFault();
    bool RequestIsolation(FName CommandSource);
    bool ReleaseIsolation(FName CommandSource);
    int32 FindAvailableLane() const;
    TArray<FName>& GetLane(int32 LaneIndex);
    const TArray<FName>& GetLane(int32 LaneIndex) const;
    USceneComponent* ResolvePresentationBindingTarget(FName SemanticObjectName, FName SemanticRole) const;
};
