#pragma once

#include "CoreMinimal.h"
#include "GameFramework/Actor.h"
#include "LBCoilAGVController.generated.h"

class USceneComponent;
class UStaticMeshComponent;
class UBoxComponent;
class ULBStatusBeaconComponent;
class ALBFactoryBuildMachine;

UENUM(BlueprintType)
enum class ELBCoilAGVPhase : uint8
{
    IdleLoaded,
    TravelToTurn,
    RotateForDock,
    TravelToDock,
    DockProving,
    RaiseTransferDeck,
    HandoffReady,
    LowerAfterHandoff,
    ReturnToTurn,
    RotateToStaged,
    ReturnToStaged,
    AwaitingReload,
    Fault
};

UENUM(BlueprintType)
enum class ELBCoilAGVFault : uint8
{
    None,
    BindingIncomplete,
    ControlPowerLost,
    RouteAuthorityLost,
    PedestrianGateOpen,
    ScannerObstructed,
    LoadUnsecured,
    DestinationNotReady,
    CraneEnvelopeConflict,
    EmergencyCircuitOpen,
    RouteObstructed,
    DockTimeout
};

/** Explicit ownership prevents an infrastructure edit from rerouting the wrong vehicle. */
UENUM(BlueprintType)
enum class ELBCoilAGVRouteProfile : uint8
{
    ManualOrUnassigned,
    InboundPR002,
    PressTrainHandoff
};

USTRUCT(BlueprintType)
struct FLBCoilAGVSaveState
{
    GENERATED_BODY()

    UPROPERTY(EditAnywhere, BlueprintReadWrite, SaveGame) int32 SaveVersion = 3;
    UPROPERTY(EditAnywhere, BlueprintReadWrite, SaveGame) ELBCoilAGVPhase Phase = ELBCoilAGVPhase::IdleLoaded;
    UPROPERTY(EditAnywhere, BlueprintReadWrite, SaveGame) ELBCoilAGVPhase PhaseBeforeFault = ELBCoilAGVPhase::IdleLoaded;
    UPROPERTY(EditAnywhere, BlueprintReadWrite, SaveGame) ELBCoilAGVFault Fault = ELBCoilAGVFault::None;
    UPROPERTY(EditAnywhere, BlueprintReadWrite, SaveGame) FVector VehicleLocation = FVector::ZeroVector;
    UPROPERTY(EditAnywhere, BlueprintReadWrite, SaveGame) float VehicleYawDegrees = 0.0f;
    UPROPERTY(EditAnywhere, BlueprintReadWrite, SaveGame) float LiftHeightCm = 0.0f;
    UPROPERTY(EditAnywhere, BlueprintReadWrite, SaveGame) float TravelSpeedCmPerSecond = 0.0f;
    UPROPERTY(EditAnywhere, BlueprintReadWrite, SaveGame) float CornerProgress = 0.0f;
    UPROPERTY(EditAnywhere, BlueprintReadWrite, SaveGame) float PhaseElapsedSeconds = 0.0f;
    UPROPERTY(EditAnywhere, BlueprintReadWrite, SaveGame) FString CoilId;
    UPROPERTY(EditAnywhere, BlueprintReadWrite, SaveGame) bool bLoadOwned = true;
    /** Exact certified geometry is required to resume an in-flight save safely. */
    UPROPERTY(EditAnywhere, BlueprintReadWrite, SaveGame) FVector RouteStagedPoint = FVector::ZeroVector;
    UPROPERTY(EditAnywhere, BlueprintReadWrite, SaveGame) FVector RouteTurnPoint = FVector::ZeroVector;
    UPROPERTY(EditAnywhere, BlueprintReadWrite, SaveGame) FVector RouteDockPoint = FVector::ZeroVector;
    UPROPERTY(EditAnywhere, BlueprintReadWrite, SaveGame) ELBCoilAGVRouteProfile RouteProfile = ELBCoilAGVRouteProfile::ManualOrUnassigned;
    /** 0-3 only for PressTrainHandoff; INDEX_NONE for every other profile. */
    UPROPERTY(EditAnywhere, BlueprintReadWrite, SaveGame) int32 AssignedRouteTrainIndex = INDEX_NONE;
};

/**
 * Runtime authority for the owner-directed PR003-to-PR004 coil AGV proposal.
 * Motion values are gameplay tuning values only; real speed, stopping distance,
 * payload certification and safety performance remain TBC.
 */
UCLASS()
class LINEBOSSCARFACTORY_API ALBCoilAGVController : public AActor
{
    GENERATED_BODY()

public:
    ALBCoilAGVController();
    virtual void BeginPlay() override;
    virtual void Tick(float DeltaSeconds) override;

    UFUNCTION(BlueprintCallable, Category="Cairnwell|Coil AGV|Binding")
    bool DiscoverAndBind();

    /**
     * Selects the exact procedural Cairnwell AGV, lift deck and master-coil assets
     * approved for the native One Factory inbound lane.  The method is deliberately
     * fail closed: legacy tagged presentation actors and every non-allowlisted asset
     * path are rejected rather than silently falling back to the retained lorry-era
     * presentation.
     */
    UFUNCTION(BlueprintCallable, Category="Cairnwell|Coil AGV|Presentation")
    bool ConfigureNativeOneFactoryPresentation(FString& OutReason);

    /** Exact-path provenance predicate used by bootstrap and focused automation. */
    UFUNCTION(BlueprintPure, Category="Cairnwell|Coil AGV|Presentation")
    static bool IsNativeOneFactoryPresentationAssetPathAllowed(const FString& AssetPath);

    UFUNCTION(BlueprintCallable, Category="Cairnwell|Coil AGV|Dispatch")
    bool StartDispatch(const FString& CoilId);

    /** Confirms that the exact carried coil has been accepted by the dock. */
    UFUNCTION(BlueprintCallable, Category="Cairnwell|Coil AGV|Dispatch")
    bool ConfirmHandoff(FString& OutCoilId);

    /** Loads the next identified coil after the empty AGV has returned home. */
    UFUNCTION(BlueprintCallable, Category="Cairnwell|Coil AGV|Dispatch")
    bool ReloadAtStagedPoint(const FString& CoilId);

    UFUNCTION(BlueprintCallable, Category="Cairnwell|Coil AGV|Safety")
    bool SetSafetyInputs(bool bRouteIsReserved, bool bPedestrianGatesAreProved,
        bool bScannerZoneIsClear, bool bLoadIsSecured, bool bDestinationIsReady,
        bool bCraneSharedEnvelopeIsClear, bool bEmergencyCircuitIsHealthy);

    UFUNCTION(BlueprintCallable, Category="Cairnwell|Coil AGV|Safety")
    bool SetControlPower(bool bEnabled);

    UFUNCTION(BlueprintCallable, Category="Cairnwell|Coil AGV|Fault")
    bool ResetFault(FName RecoveryEvidenceId);

    UFUNCTION(BlueprintCallable, Category="Cairnwell|Coil AGV|Save")
    bool GetSaveState(FLBCoilAGVSaveState& OutState) const;

    UFUNCTION(BlueprintCallable, Category="Cairnwell|Coil AGV|Save")
    bool RestoreSaveState(const FLBCoilAGVSaveState& InState);

    /**
     * Campaign restore boundary for the single inbound vehicle. Legacy v1/v2 snapshots did
     * not contain route geometry, so this first derives and certifies the restored painted
     * Inbound-to-PR002 route, then commits that route and the saved motion together.
     */
    bool RestoreInboundSaveState(const FLBCoilAGVSaveState& InState,
        ALBFactoryBuildMachine* InboundDock, ALBFactoryBuildMachine* PR002Cell);

    UFUNCTION(BlueprintCallable, Category="Cairnwell|Coil AGV|Route")
    bool ConfigureRoute(FVector InStagedPoint, FVector InTurnPoint, FVector InDockPoint);

    /** Derives the live route from player-placed wait, waypoint, route segments and train handoff. */
    UFUNCTION(BlueprintCallable, Category="Cairnwell|Coil AGV|Route")
    bool ConfigureFromPlayerBuiltInfrastructure(int32 TrainIndex = 0);
    bool ConfigureInboundRouteFromPlayerBuiltInfrastructure(ALBFactoryBuildMachine* InboundDock, ALBFactoryBuildMachine* PR002Cell);
    FVector GetConfiguredDockPoint() const { return DockPoint; }

    UFUNCTION(BlueprintPure, Category="Cairnwell|Coil AGV|State") ELBCoilAGVPhase GetPhase() const { return Phase; }
    UFUNCTION(BlueprintPure, Category="Cairnwell|Coil AGV|State") ELBCoilAGVFault GetFault() const { return ActiveFault; }
    UFUNCTION(BlueprintPure, Category="Cairnwell|Coil AGV|State") bool IsHandoffReady() const { return Phase == ELBCoilAGVPhase::HandoffReady; }
    UFUNCTION(BlueprintPure, Category="Cairnwell|Coil AGV|State") FVector GetVehicleLocation() const { return CurrentLocation; }
    UFUNCTION(BlueprintPure, Category="Cairnwell|Coil AGV|State") float GetVehicleYawDegrees() const { return CurrentYawDegrees; }
    UFUNCTION(BlueprintPure, Category="Cairnwell|Coil AGV|State") float GetLiftHeightCm() const { return LiftHeightCm; }
    UFUNCTION(BlueprintPure, Category="Cairnwell|Coil AGV|State") float GetMaxLoadFollowErrorCm() const { return MaxLoadFollowErrorCm; }
    UFUNCTION(BlueprintPure, Category="Cairnwell|Coil AGV|State") bool IsAwaitingReload() const { return Phase == ELBCoilAGVPhase::AwaitingReload; }
    UFUNCTION(BlueprintPure, Category="Cairnwell|Coil AGV|State") bool OwnsLoad() const { return bLoadOwned; }
    UFUNCTION(BlueprintPure, Category="Cairnwell|Coil AGV|State") FString GetActiveCoilId() const { return ActiveCoilId; }
    UFUNCTION(BlueprintPure, Category="Cairnwell|Coil AGV|Route") ELBCoilAGVRouteProfile GetRouteProfile() const { return RouteProfile; }
    UFUNCTION(BlueprintPure, Category="Cairnwell|Coil AGV|Route") int32 GetAssignedRouteTrainIndex() const { return AssignedRouteTrainIndex; }
    UFUNCTION(BlueprintPure, Category="Cairnwell|Coil AGV|Presentation") bool IsUsingApprovedPlayerBuiltPresentation() const { return bUsingOwnedPresentation; }
    UFUNCTION(BlueprintPure, Category="Cairnwell|Coil AGV|Presentation") bool IsUsingNativeOneFactoryPresentation() const;
    UFUNCTION(BlueprintPure, Category="Cairnwell|Coil AGV|Presentation") UStaticMeshComponent* GetApprovedChassisVisual() const { return ApprovedChassisVisual; }
    UFUNCTION(BlueprintPure, Category="Cairnwell|Coil AGV|Presentation") UStaticMeshComponent* GetApprovedLiftDeckVisual() const { return ApprovedLiftDeckVisual; }
    UFUNCTION(BlueprintPure, Category="Cairnwell|Coil AGV|Presentation") UStaticMeshComponent* GetApprovedLoadVisual() const { return ApprovedLoadVisual; }
    UFUNCTION(BlueprintPure, Category="Cairnwell|Coil AGV|Collision") UBoxComponent* GetCollisionProxy() const { return CollisionProxy; }

protected:
    UPROPERTY(EditAnywhere, BlueprintReadOnly, Category="Cairnwell|Coil AGV|Binding") FName ChassisTag = TEXT("LB.Vehicle.CoilAGV");
    UPROPERTY(EditAnywhere, BlueprintReadOnly, Category="Cairnwell|Coil AGV|Binding") FName LiftDeckTag = TEXT("LB.Vehicle.CoilAGV.LiftDeck");
    UPROPERTY(EditAnywhere, BlueprintReadOnly, Category="Cairnwell|Coil AGV|Binding") FName LoadTag = TEXT("LB.Inventory.InTransfer");
    UPROPERTY(EditAnywhere, BlueprintReadOnly, Category="Cairnwell|Coil AGV|Route") FVector StagedPoint = FVector(-6200.0f,-2700.0f,29.0f);
    UPROPERTY(EditAnywhere, BlueprintReadOnly, Category="Cairnwell|Coil AGV|Route") FVector TurnPoint = FVector(-5550.0f,-2700.0f,29.0f);
    UPROPERTY(EditAnywhere, BlueprintReadOnly, Category="Cairnwell|Coil AGV|Route") FVector DockPoint = FVector(-5550.0f,-2000.0f,29.0f);
    UPROPERTY(EditAnywhere, BlueprintReadOnly, Category="Cairnwell|Coil AGV|Motion", meta=(ClampMin="1.0")) float GameplayTravelSpeedCmPerSecond = 120.0f;
    UPROPERTY(EditAnywhere, BlueprintReadOnly, Category="Cairnwell|Coil AGV|Motion", meta=(ClampMin="1.0")) float GameplayTurnRateDegreesPerSecond = 60.0f;
    UPROPERTY(EditAnywhere, BlueprintReadOnly, Category="Cairnwell|Coil AGV|Motion", meta=(ClampMin="1.0")) float GameplayAccelerationCmPerSecondSquared = 180.0f;
    /** Trim applied on each route leg to form a moving quadratic corner instead of a stop-and-pivot turn. */
    UPROPERTY(EditAnywhere, BlueprintReadOnly, Category="Cairnwell|Coil AGV|Motion", meta=(ClampMin="0.0")) float GameplayCornerTrimCm = 180.0f;
    /** Extra floor-plane clearance around every player-built machine protected envelope. */
    UPROPERTY(EditAnywhere, BlueprintReadOnly, Category="Cairnwell|Coil AGV|Safety", meta=(ClampMin="0.0")) float ProtectedEnvelopeClearanceCm = 35.0f;
    UPROPERTY(EditAnywhere, BlueprintReadOnly, Category="Cairnwell|Coil AGV|Motion", meta=(ClampMin="0.1")) float DockProveSeconds = 0.75f;
    UPROPERTY(EditAnywhere, BlueprintReadOnly, Category="Cairnwell|Coil AGV|Motion", meta=(ClampMin="0.0")) float TransferLiftHeightCm = 8.0f;
    UPROPERTY(EditAnywhere, BlueprintReadOnly, Category="Cairnwell|Coil AGV|Motion", meta=(ClampMin="0.1")) float GameplayLiftSpeedCmPerSecond = 8.0f;
    UPROPERTY(EditAnywhere, BlueprintReadOnly, Category="Cairnwell|Coil AGV|Motion", meta=(ClampMin="1.0")) float PhaseTimeoutSeconds = 30.0f;

private:
    UPROPERTY(VisibleAnywhere, Category="Cairnwell|Coil AGV|Presentation") TObjectPtr<USceneComponent> SceneRoot;
    UPROPERTY(VisibleAnywhere, Category="Cairnwell|Coil AGV|Presentation") TObjectPtr<UStaticMeshComponent> ApprovedChassisVisual;
    UPROPERTY(VisibleAnywhere, Category="Cairnwell|Coil AGV|Presentation") TObjectPtr<UStaticMeshComponent> ApprovedLiftDeckVisual;
    UPROPERTY(VisibleAnywhere, Category="Cairnwell|Coil AGV|Presentation") TObjectPtr<UStaticMeshComponent> ApprovedLoadVisual;
    UPROPERTY(VisibleAnywhere, Category="Cairnwell|Coil AGV|Collision") TObjectPtr<UBoxComponent> CollisionProxy;
    /** Independent light stack retained when the approved AGV body mesh changes. */
    UPROPERTY(VisibleAnywhere, Category="Cairnwell|Coil AGV|Presentation") TObjectPtr<ULBStatusBeaconComponent> StatusBeacon;
    struct FBoundModule
    {
        TWeakObjectPtr<AActor> Actor;
        FVector LocalOffset = FVector::ZeroVector;
        FRotator LocalRotation = FRotator::ZeroRotator;
        bool bLiftWithDeck = false;
        bool bIsLoad = false;
    };

    UPROPERTY(Transient) TObjectPtr<AActor> ChassisActor;
    UPROPERTY(Transient) TObjectPtr<AActor> LiftDeckActor;
    UPROPERTY(Transient) TObjectPtr<AActor> LoadActor;
    TArray<FBoundModule> Modules;
    ELBCoilAGVPhase Phase = ELBCoilAGVPhase::IdleLoaded;
    ELBCoilAGVPhase PhaseBeforeFault = ELBCoilAGVPhase::IdleLoaded;
    ELBCoilAGVFault ActiveFault = ELBCoilAGVFault::None;
    ELBCoilAGVRouteProfile RouteProfile = ELBCoilAGVRouteProfile::ManualOrUnassigned;
    int32 AssignedRouteTrainIndex = INDEX_NONE;
    FVector CurrentLocation = FVector::ZeroVector;
    float CurrentYawDegrees = 0.0f;
    float LiftHeightCm = 0.0f;
    float CurrentTravelSpeedCmPerSecond = 0.0f;
    float CornerProgress = 0.0f;
    float CornerPathLengthCm = 0.0f;
    float PhaseElapsedSeconds = 0.0f;
    FVector CornerEntryPoint = FVector::ZeroVector;
    FVector CornerExitPoint = FVector::ZeroVector;
    FString ActiveCoilId;
    bool bLoadOwned = true;
    bool bBound = false;
    bool bUsingOwnedPresentation = false;
    /** Native mode must never bind a retained map-authored/Meshy-era vehicle by tag. */
    bool bForceOwnedPresentation = false;
    bool bNativeOneFactoryPresentation = false;
    FVector OwnedLiftDeckBaseRelativeLocation = FVector::ZeroVector;
    bool bControlPowerOn = true;
    bool bRouteReserved = true;
    bool bPedestrianGatesProved = true;
    bool bScannerZoneClear = true;
    bool bLoadSecured = true;
    bool bDestinationReady = true;
    bool bCraneSharedEnvelopeClear = true;
    bool bEmergencyCircuitHealthy = true;
    float MaxLoadFollowErrorCm = 0.0f;
    bool bEnforceProtectedEnvelopeRoute = false;
    TWeakObjectPtr<ALBFactoryBuildMachine> AllowedStartMachine;
    TWeakObjectPtr<ALBFactoryBuildMachine> AllowedDockMachine;

    bool IsMotionPhase(ELBCoilAGVPhase Candidate) const;
    bool SafetyHealthy() const;
    ELBCoilAGVFault FirstUnsafeFault() const;
    void EnterPhase(ELBCoilAGVPhase NewPhase);
    void LatchFault(ELBCoilAGVFault Fault);
    bool ConfigureRouteInternal(const FVector& InStagedPoint, const FVector& InTurnPoint,
        const FVector& InDockPoint, bool bEnforceProtectedEnvelopes,
        ALBFactoryBuildMachine* InAllowedStartMachine, ALBFactoryBuildMachine* InAllowedDockMachine);
    void RebuildCornerGeometry();
    bool MoveTo(const FVector& Target, float DeltaSeconds, bool bStopAtTarget);
    bool MoveAroundCorner(bool bOutbound, float DeltaSeconds);
    bool IsRouteClearOfProtectedEnvelopes(const FVector& Start, const FVector& Turn,
        const FVector& Dock) const;
    bool IsRouteClearOfProtectedEnvelopesWithAllowed(const FVector& Start, const FVector& Turn,
        const FVector& Dock, const ALBFactoryBuildMachine* InAllowedStartMachine,
        const ALBFactoryBuildMachine* InAllowedDockMachine) const;
    bool CanAdvanceTo(const FVector& CandidateLocation) const;
    float RecoverCornerProgressFromLocation() const;
    void ApplyPose();
    void UpdateStatusBeacon();
};
