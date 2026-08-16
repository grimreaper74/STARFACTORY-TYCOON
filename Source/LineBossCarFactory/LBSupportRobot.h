#pragma once

#include "CoreMinimal.h"
#include "GameFramework/Actor.h"
#include "LBSupportRobot.generated.h"

class UBoxComponent;
class USceneComponent;
class ULBStatusBeaconComponent;
class USpotLightComponent;

/** Shared campaign and operating states used by both RP01 variants. */
UENUM(BlueprintType)
enum class ELBSupportRobotState : uint8
{
    Mothballed,
    Inspection,
    RepairRequired,
    ReadyForTest,
    ManualCommissioning,
    Calibration,
    RouteValidation,
    Certified,
    Docked,
    Dispatched,
    Navigating,
    Cleaning,
    Inspecting,
    Diagnosing,
    WaitingForPermission,
    LightService,
    Lubricating,
    DeliveringParts,
    ModuleExchange,
    Verifying,
    Returning,
    Servicing,
    Charging,
    Blocked,
    SpillDetected,
    LowBattery,
    TankFull,
    BrushJam,
    SensorDirty,
    AccessDenied,
    LOTOInvalid,
    ToolFault,
    Lost,
    LeakDetected,
    PartMismatch,
    ArmOverload,
    SafetyStop,
    Fault,
    Maintenance
};

UENUM(BlueprintType)
enum class ELBSupportRobotCondition : uint8
{
    Mothballed,
    Surveyed,
    RepairInProgress,
    Restored,
    Commissioned
};

UENUM(BlueprintType)
enum class ELBSupportRobotFault : uint8
{
    None,
    RouteNotCertified,
    RouteAuthorityLost,
    RouteObstructed,
    LocalisationLost,
    SafetyNetworkUnhealthy,
    LowBattery,
    DockingFailed,
    DockContactsDirty,
    SpillDetected,
    TankFull,
    BrushJam,
    SensorCoverageInvalid,
    VariantInterlockOpen,
    RestoreRevalidationRequired
};

UENUM(BlueprintType)
enum class ELBRouteSpeedClass : uint8
{
    Docking,
    MachineApproach,
    OccupiedAisle,
    NormalTransit,
    EmergencyCertifiedClearRoute
};

/** A route is an explicit certified asset contract; navmesh reachability alone never grants authority. */
USTRUCT(BlueprintType)
struct FLBSupportRobotRoute
{
    GENERATED_BODY()

    UPROPERTY(EditAnywhere, BlueprintReadWrite)
    FName RouteId = NAME_None;

    UPROPERTY(EditAnywhere, BlueprintReadWrite)
    int32 Revision = 1;

    UPROPERTY(EditAnywhere, BlueprintReadWrite)
    bool bCertified = false;

    UPROPERTY(EditAnywhere, BlueprintReadWrite)
    ELBRouteSpeedClass SpeedClass = ELBRouteSpeedClass::NormalTransit;

    UPROPERTY(EditAnywhere, BlueprintReadWrite)
    TArray<FVector> Waypoints;

    UPROPERTY(EditAnywhere, BlueprintReadWrite)
    FName DestinationDockId = NAME_None;
};

/** Common, versioned RP01 state persisted by both robot variants. */
USTRUCT(BlueprintType)
struct FLBSupportRobotSaveState
{
    GENERATED_BODY()

    UPROPERTY(EditAnywhere, BlueprintReadWrite, SaveGame)
    int32 Version = 1;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, SaveGame)
    FName UnitId = NAME_None;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, SaveGame)
    FName VariantId = NAME_None;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, SaveGame)
    ELBSupportRobotState State = ELBSupportRobotState::Mothballed;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, SaveGame)
    ELBSupportRobotCondition Condition = ELBSupportRobotCondition::Mothballed;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, SaveGame)
    ELBSupportRobotFault ActiveFault = ELBSupportRobotFault::None;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, SaveGame)
    float BatteryStateOfChargePercent = 0.0f;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, SaveGame)
    float BatteryHealthPercent = 65.0f;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, SaveGame)
    float OperatingHours = 0.0f;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, SaveGame)
    int32 MissionCount = 0;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, SaveGame)
    int32 ServiceCycles = 0;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, SaveGame)
    bool bCertified = false;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, SaveGame)
    bool bDocked = false;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, SaveGame)
    FName DockId = NAME_None;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, SaveGame)
    FName LastCertifiedRouteId = NAME_None;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, SaveGame)
    int32 LastCertifiedRouteRevision = 0;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, SaveGame)
    FName ActiveTaskId = NAME_None;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, SaveGame)
    FTransform SavedTransform;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, SaveGame)
    bool bRouteRevalidationRequired = true;
};

DECLARE_DYNAMIC_MULTICAST_DELEGATE_TwoParams(FLBSupportRobotStateChanged, ELBSupportRobotState, PreviousState, ELBSupportRobotState, NewState);
DECLARE_DYNAMIC_MULTICAST_DELEGATE_TwoParams(FLBSupportRobotFaultChanged, ELBSupportRobotFault, PreviousFault, ELBSupportRobotFault, NewFault);
DECLARE_DYNAMIC_MULTICAST_DELEGATE_TwoParams(FLBSupportRobotRouteEvent, FName, UnitId, FName, RouteId);
DECLARE_DYNAMIC_MULTICAST_DELEGATE_ThreeParams(FLBSupportRobotWorkOrder, FName, UnitId, FName, WorkOrderType, FString, Detail);

/**
 * Reusable LB-RP01 mobile-platform authority.
 *
 * The actor moves only along an explicitly certified route after route authority,
 * localisation, safety-network and variant interlocks are all proved. Loading a
 * save never resumes hidden motion: route authority is discarded and the robot
 * must be revalidated from a stopped state.
 */
UCLASS(BlueprintType, Blueprintable)
class LINEBOSSCARFACTORY_API ALBSupportRobot : public AActor
{
    GENERATED_BODY()

public:
    ALBSupportRobot();

    virtual void BeginPlay() override;
    virtual void Tick(float DeltaSeconds) override;

    UFUNCTION(BlueprintCallable, Category = "Line Boss|Support Robot|Identity")
    bool ConfigureIdentity(FName NewUnitId, FName NewVariantId);

    UFUNCTION(BlueprintCallable, Category = "Line Boss|Support Robot|Restoration")
    bool BeginInspection();

    UFUNCTION(BlueprintCallable, Category = "Line Boss|Support Robot|Restoration")
    bool RecordRepairRequired();

    UFUNCTION(BlueprintCallable, Category = "Line Boss|Support Robot|Restoration")
    bool MarkReadyForTest();

    UFUNCTION(BlueprintCallable, Category = "Line Boss|Support Robot|Restoration")
    bool BeginRouteValidation();

    UFUNCTION(BlueprintCallable, Category = "Line Boss|Support Robot|Restoration")
    bool CertifyRobot();

    UFUNCTION(BlueprintCallable, Category = "Line Boss|Support Robot|Safety")
    void SetSafetyHealth(bool bLocalisationIsHealthy, bool bSafetyNetworkIsHealthy);

    UFUNCTION(BlueprintCallable, Category = "Line Boss|Support Robot|Safety")
    void SetRouteEnvironment(bool bRouteIsClear, bool bPersonIsInRoute, bool bMachineApproach, bool bDockingApproach);

    UFUNCTION(BlueprintCallable, Category = "Line Boss|Support Robot|Route")
    bool BeginCertifiedRoute(const FLBSupportRobotRoute& Route, bool bEmergencyDispatch);

    UFUNCTION(BlueprintCallable, Category = "Line Boss|Support Robot|Route")
    void AbortRoute(bool bRaiseAuthorityFault);

    UFUNCTION(BlueprintCallable, Category = "Line Boss|Support Robot|Dock")
    bool ConfirmDocked(FName NewDockId);

    UFUNCTION(BlueprintCallable, Category = "Line Boss|Support Robot|Dock")
    bool Undock();

    /** Assigns the certified route the robot autonomously uses when charge falls below reserve. */
    UFUNCTION(BlueprintCallable, Category = "Line Boss|Support Robot|Dock")
    bool ConfigureAutomaticChargingRoute(const FLBSupportRobotRoute& Route, float DispatchThresholdPercent = 30.0f);

    UFUNCTION(BlueprintCallable, Category = "Line Boss|Support Robot|Fault")
    void RaiseCommonFault(ELBSupportRobotFault Fault, const FString& Detail);

    UFUNCTION(BlueprintCallable, Category = "Line Boss|Support Robot|Fault")
    bool ClearCommonFault();

    UFUNCTION(BlueprintPure, Category = "Line Boss|Support Robot|Safety")
    bool CanTravel(FText& BlockingReason) const;

    UFUNCTION(BlueprintPure, Category = "Line Boss|Support Robot|Save")
    FLBSupportRobotSaveState CaptureCommonSaveState() const;

    UFUNCTION(BlueprintCallable, Category = "Line Boss|Support Robot|Save")
    bool RestoreCommonSaveState(const FLBSupportRobotSaveState& SavedState);

    UFUNCTION(BlueprintPure, Category = "Line Boss|Support Robot|State")
    ELBSupportRobotState GetRobotState() const { return RobotState; }

    UFUNCTION(BlueprintPure, Category = "Line Boss|Support Robot|Fault")
    FString GetLastCommonFaultDetail() const { return LastCommonFaultDetail; }

    UFUNCTION(BlueprintPure, Category = "Line Boss|Support Robot|State")
    float GetBatteryStateOfChargePercent() const { return BatteryStateOfChargePercent; }

    UFUNCTION(BlueprintPure, Category = "Line Boss|Support Robot|Route")
    bool HasRouteAuthority() const { return bRouteAuthorityGranted; }

    UFUNCTION(BlueprintPure, Category = "Line Boss|Support Robot|Route")
    float GetCurrentSpeedMetresPerSecond() const { return CurrentSpeedCentimetresPerSecond / 100.0f; }

    /** Runtime points after obstacle detours and curved-corner sampling are applied. */
    UFUNCTION(BlueprintPure, Category = "Line Boss|Support Robot|Route")
    int32 GetActiveRuntimeRoutePointCount() const { return ActiveRoute.Waypoints.Num(); }

    UFUNCTION(BlueprintPure, Category = "Line Boss|Support Robot|Dock")
    bool HasAutomaticChargingRoute() const { return bAutomaticChargingEnabled; }

    UFUNCTION(BlueprintPure, Category = "Line Boss|Support Robot|Dock")
    bool IsDocked() const { return bDocked; }

    UFUNCTION(BlueprintPure, Category = "Line Boss|Support Robot|Dock")
    FName GetDockId() const { return DockId; }

    /** Real scene lights mounted independently of replaceable presentation art. */
    USpotLightComponent* GetLeftForwardWorkLight() const { return LeftForwardWorkLight; }
    USpotLightComponent* GetRightForwardWorkLight() const { return RightForwardWorkLight; }

    UPROPERTY(BlueprintAssignable, Category = "Line Boss|Support Robot|Events")
    FLBSupportRobotStateChanged OnRobotStateChanged;

    UPROPERTY(BlueprintAssignable, Category = "Line Boss|Support Robot|Events")
    FLBSupportRobotFaultChanged OnCommonFaultChanged;

    UPROPERTY(BlueprintAssignable, Category = "Line Boss|Support Robot|Events")
    FLBSupportRobotRouteEvent OnRouteStarted;

    UPROPERTY(BlueprintAssignable, Category = "Line Boss|Support Robot|Events")
    FLBSupportRobotRouteEvent OnRouteCompleted;

    UPROPERTY(BlueprintAssignable, Category = "Line Boss|Support Robot|Events")
    FLBSupportRobotWorkOrder OnWorkOrderRequested;

protected:
    UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category = "Line Boss|Support Robot|Components")
    TObjectPtr<UBoxComponent> CollisionRoot;

    UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category = "Line Boss|Support Robot|Components")
    TObjectPtr<USceneComponent> RobotVisualRoot;

    UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category = "Line Boss|Support Robot|Components")
    TObjectPtr<USceneComponent> PayloadMount;

    UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category = "Line Boss|Support Robot|Components")
    TObjectPtr<USceneComponent> DockInterface;

    UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category = "Line Boss|Support Robot|Components")
    TObjectPtr<USceneComponent> SafetyScannerOrigin;

    UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category = "Line Boss|Support Robot|Components")
    TObjectPtr<USceneComponent> RouteProjectorOrigin;

    /** Mesh-independent safety/status stack retained when CR01 or MR01 artwork is replaced. */
    UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category = "Line Boss|Support Robot|Components")
    TObjectPtr<ULBStatusBeaconComponent> StatusBeacon;

    UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category = "Line Boss|Support Robot|Components")
    TObjectPtr<USpotLightComponent> LeftForwardWorkLight;

    UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category = "Line Boss|Support Robot|Components")
    TObjectPtr<USpotLightComponent> RightForwardWorkLight;

    UPROPERTY(EditInstanceOnly, BlueprintReadOnly, SaveGame, Category = "Line Boss|Support Robot|Identity")
    FName UnitId = NAME_None;

    UPROPERTY(EditDefaultsOnly, BlueprintReadOnly, Category = "Line Boss|Support Robot|Identity")
    FName VariantId = TEXT("LB-RP01");

    UPROPERTY(VisibleInstanceOnly, BlueprintReadOnly, SaveGame, Category = "Line Boss|Support Robot|State")
    ELBSupportRobotState RobotState = ELBSupportRobotState::Mothballed;

    UPROPERTY(VisibleInstanceOnly, BlueprintReadOnly, SaveGame, Category = "Line Boss|Support Robot|State")
    ELBSupportRobotCondition Condition = ELBSupportRobotCondition::Mothballed;

    UPROPERTY(VisibleInstanceOnly, BlueprintReadOnly, SaveGame, Category = "Line Boss|Support Robot|State")
    ELBSupportRobotFault ActiveCommonFault = ELBSupportRobotFault::None;

    UPROPERTY(EditInstanceOnly, BlueprintReadOnly, SaveGame, Category = "Line Boss|Support Robot|Battery", meta = (ClampMin = "0.0", ClampMax = "100.0"))
    float BatteryStateOfChargePercent = 0.0f;

    UPROPERTY(EditInstanceOnly, BlueprintReadOnly, SaveGame, Category = "Line Boss|Support Robot|Battery", meta = (ClampMin = "0.0", ClampMax = "100.0"))
    float BatteryHealthPercent = 65.0f;

    UPROPERTY(VisibleInstanceOnly, BlueprintReadOnly, SaveGame, Category = "Line Boss|Support Robot|Counters")
    float OperatingHours = 0.0f;

    UPROPERTY(VisibleInstanceOnly, BlueprintReadOnly, SaveGame, Category = "Line Boss|Support Robot|Counters")
    int32 MissionCount = 0;

    UPROPERTY(VisibleInstanceOnly, BlueprintReadOnly, SaveGame, Category = "Line Boss|Support Robot|Counters")
    int32 ServiceCycles = 0;

    UPROPERTY(VisibleInstanceOnly, BlueprintReadOnly, SaveGame, Category = "Line Boss|Support Robot|Commissioning")
    bool bCertified = false;

    UPROPERTY(VisibleInstanceOnly, BlueprintReadOnly, SaveGame, Category = "Line Boss|Support Robot|Dock")
    bool bDocked = false;

    UPROPERTY(VisibleInstanceOnly, BlueprintReadOnly, SaveGame, Category = "Line Boss|Support Robot|Dock")
    FName DockId = NAME_None;

    UPROPERTY(VisibleInstanceOnly, BlueprintReadOnly, SaveGame, Category = "Line Boss|Support Robot|Task")
    FName ActiveTaskId = NAME_None;

    UPROPERTY(VisibleInstanceOnly, BlueprintReadOnly, SaveGame, Category = "Line Boss|Support Robot|Route")
    bool bRouteRevalidationRequired = true;

    virtual bool HasVariantTravelPermissives(FText& BlockingReason) const;
    virtual float GetMaximumSpeedCentimetresPerSecond(ELBRouteSpeedClass SpeedClass, bool bEmergencyDispatch) const;
    virtual void OnEnteredSafeStop();
    virtual void UpdateVariantWorkLights();

    void SetRobotState(ELBSupportRobotState NewState);
    void ForceSafeStop(ELBSupportRobotFault Fault, const FString& Detail);
    void UpdateStatusBeacon();
    void UpdateWorkLights();

private:
    FLBSupportRobotRoute ActiveRoute;
    FLBSupportRobotRoute AutomaticChargingRoute;
    int32 ActiveWaypointIndex = INDEX_NONE;
    bool bRouteAuthorityGranted = false;
    bool bEmergencyRoute = false;
    bool bLocalisationHealthy = false;
    bool bSafetyNetworkHealthy = false;
    bool bRouteClear = false;
    bool bPersonInRoute = false;
    bool bMachineApproach = false;
    bool bDockingApproach = false;
    bool bAutomaticChargingEnabled = false;
    bool bAutomaticChargeReturnActive = false;
    FString LastCommonFaultDetail;
    float AutomaticChargeDispatchThresholdPercent = 30.0f;
    float CurrentSpeedCentimetresPerSecond = 0.0f;
    FVector ActiveRouteStartLocation = FVector::ZeroVector;

    static constexpr float WaypointToleranceCentimetres = 18.0f;
    static constexpr float AccelerationCentimetresPerSecondSquared = 80.0f;
    static constexpr float DecelerationCentimetresPerSecondSquared = 120.0f;
    static constexpr float MaximumSteeringDegreesPerSecond = 72.0f;
    static constexpr float MinimumSteeringLookAheadCentimetres = 65.0f;
    static constexpr float MaximumSteeringLookAheadCentimetres = 145.0f;
    static constexpr float ChargingRatePercentPerSecond = 0.20f;
    static constexpr float TransitDrainPercentPerMetre = 0.015f;
    static constexpr float LowBatteryThresholdPercent = 15.0f;

    bool IsMotionOrWorkState(ELBSupportRobotState State) const;
    ELBRouteSpeedClass GetEffectiveSpeedClass() const;
    void TickRouteMovement(float DeltaSeconds);
    void TickBattery(float DeltaSeconds, float DistanceMovedCentimetres);
    bool TryBeginAutomaticChargeReturn();
    void CompleteActiveRoute();
};
