#include "LBSupportRobot.h"
#include "LBMobileRoutePlanner.h"
#include "LBSupportRobotServiceDock.h"
#include "LBStatusBeaconComponent.h"

#include "Components/BoxComponent.h"
#include "Components/SceneComponent.h"
#include "Components/SpotLightComponent.h"
#include "Engine/World.h"
#include "EngineUtils.h"

ALBSupportRobot::ALBSupportRobot()
{
    PrimaryActorTick.bCanEverTick = true;

    CollisionRoot = CreateDefaultSubobject<UBoxComponent>(TEXT("RP01_CollisionRoot"));
    CollisionRoot->SetBoxExtent(FVector(76.0f, 46.5f, 55.0f));
    CollisionRoot->SetCollisionProfileName(TEXT("Pawn"));
    CollisionRoot->SetGenerateOverlapEvents(true);
    SetRootComponent(CollisionRoot);

    // Authored robot geometry uses the CFR ground projection as its origin.
    // The collision root is centred vertically, so the visual datum is lowered.
    RobotVisualRoot = CreateDefaultSubobject<USceneComponent>(TEXT("RP01_VisualRoot_CFR"));
    RobotVisualRoot->SetupAttachment(CollisionRoot);
    RobotVisualRoot->SetRelativeLocation(FVector(0.0f, 0.0f, -55.0f));

    PayloadMount = CreateDefaultSubobject<USceneComponent>(TEXT("SOCKET_RP01_PayloadPlate"));
    PayloadMount->SetupAttachment(RobotVisualRoot);
    PayloadMount->SetRelativeLocation(FVector(0.0f, 0.0f, 61.0f));

    DockInterface = CreateDefaultSubobject<USceneComponent>(TEXT("SOCKET_RP01_DockElectricalData"));
    DockInterface->SetupAttachment(RobotVisualRoot);
    DockInterface->SetRelativeLocation(FVector(-73.5f, 0.0f, 34.0f));

    SafetyScannerOrigin = CreateDefaultSubobject<USceneComponent>(TEXT("SOCKET_RP01_SafetyScanner"));
    SafetyScannerOrigin->SetupAttachment(RobotVisualRoot);
    SafetyScannerOrigin->SetRelativeLocation(FVector(68.0f, 0.0f, 39.0f));

    RouteProjectorOrigin = CreateDefaultSubobject<USceneComponent>(TEXT("SOCKET_RP01_RouteProjector"));
    RouteProjectorOrigin->SetupAttachment(RobotVisualRoot);
    RouteProjectorOrigin->SetRelativeLocation(FVector(70.0f, 0.0f, 24.0f));

    StatusBeacon = CreateDefaultSubobject<ULBStatusBeaconComponent>(TEXT("RP01_RuntimeStatusBeacon"));
    StatusBeacon->SetupAttachment(RobotVisualRoot);
    // The shared RP01/Meshy envelope is about 1.12 m tall. The independent stack
    // sits above the rear shoulder and survives future visual-mesh replacements.
    StatusBeacon->SetRelativeLocation(FVector(-43.0f, 0.0f, 103.0f));
    StatusBeacon->SetRelativeScale3D(FVector(0.45f));
    StatusBeacon->SetStatus(ELBStatusBeaconState::Stopped);

    LeftForwardWorkLight = CreateDefaultSubobject<USpotLightComponent>(TEXT("LENS_RP01_FORWARD_WORKLIGHT_LEFT"));
    LeftForwardWorkLight->SetupAttachment(RobotVisualRoot);
    LeftForwardWorkLight->SetRelativeLocation(FVector(70.0f, -28.0f, 50.0f));
    LeftForwardWorkLight->SetRelativeRotation(FRotator(-7.0f, 0.0f, 0.0f));

    RightForwardWorkLight = CreateDefaultSubobject<USpotLightComponent>(TEXT("LENS_RP01_FORWARD_WORKLIGHT_RIGHT"));
    RightForwardWorkLight->SetupAttachment(RobotVisualRoot);
    RightForwardWorkLight->SetRelativeLocation(FVector(70.0f, 28.0f, 50.0f));
    RightForwardWorkLight->SetRelativeRotation(FRotator(-7.0f, 0.0f, 0.0f));

    for (USpotLightComponent* Light : {LeftForwardWorkLight, RightForwardWorkLight})
    {
        Light->SetIntensity(1500.0f);
        Light->SetAttenuationRadius(700.0f);
        Light->SetInnerConeAngle(17.0f);
        Light->SetOuterConeAngle(33.0f);
        Light->SetLightColor(FLinearColor(0.88f, 0.95f, 1.0f));
        Light->SetCastShadows(false);
        Light->SetVisibility(false);
    }

}

void ALBSupportRobot::BeginPlay()
{
    Super::BeginPlay();
    CurrentSpeedCentimetresPerSecond = 0.0f;
    UpdateStatusBeacon();
    UpdateWorkLights();
}

void ALBSupportRobot::Tick(float DeltaSeconds)
{
    Super::Tick(DeltaSeconds);

    // Variant task mechanics can change without a common state transition
    // (brush valves, arm permissives, tool presence), so presentation lighting
    // is reconciled once per frame as a cheap, deterministic visual contract.
    UpdateWorkLights();

    const FVector Before = GetActorLocation();
    if (bRouteAuthorityGranted && IsMotionOrWorkState(RobotState))
    {
        TickRouteMovement(DeltaSeconds);
    }

    const float DistanceMovedCentimetres = FVector::Dist2D(Before, GetActorLocation());
    TickBattery(DeltaSeconds, DistanceMovedCentimetres);

    if (RobotState != ELBSupportRobotState::Mothballed && RobotState != ELBSupportRobotState::RepairRequired)
    {
        OperatingHours += FMath::Max(0.0f, DeltaSeconds) / 3600.0f;
    }
}

bool ALBSupportRobot::ConfigureIdentity(FName NewUnitId, FName NewVariantId)
{
    if (NewUnitId.IsNone() || NewVariantId.IsNone())
    {
        return false;
    }
    if (!UnitId.IsNone() && UnitId != NewUnitId)
    {
        return false;
    }
    if (!VariantId.IsNone() && VariantId != TEXT("LB-RP01") && VariantId != NewVariantId)
    {
        return false;
    }
    UnitId = NewUnitId;
    VariantId = NewVariantId;
    return true;
}

bool ALBSupportRobot::BeginInspection()
{
    if (RobotState != ELBSupportRobotState::Mothballed && RobotState != ELBSupportRobotState::RepairRequired)
    {
        return false;
    }
    Condition = ELBSupportRobotCondition::Surveyed;
    SetRobotState(ELBSupportRobotState::Inspection);
    return true;
}

bool ALBSupportRobot::RecordRepairRequired()
{
    if (RobotState != ELBSupportRobotState::Inspection)
    {
        return false;
    }
    Condition = ELBSupportRobotCondition::RepairInProgress;
    bCertified = false;
    bRouteRevalidationRequired = true;
    SetRobotState(ELBSupportRobotState::RepairRequired);
    return true;
}

bool ALBSupportRobot::MarkReadyForTest()
{
    if (RobotState != ELBSupportRobotState::Inspection && RobotState != ELBSupportRobotState::RepairRequired)
    {
        return false;
    }
    Condition = ELBSupportRobotCondition::Restored;
    ActiveCommonFault = ELBSupportRobotFault::None;
    SetRobotState(ELBSupportRobotState::ReadyForTest);
    return true;
}

bool ALBSupportRobot::BeginRouteValidation()
{
    if (RobotState != ELBSupportRobotState::ReadyForTest && RobotState != ELBSupportRobotState::ManualCommissioning
        && RobotState != ELBSupportRobotState::SafetyStop)
    {
        return false;
    }
    if (!bLocalisationHealthy || !bSafetyNetworkHealthy)
    {
        return false;
    }
    bRouteRevalidationRequired = true;
    SetRobotState(ELBSupportRobotState::RouteValidation);
    return true;
}

bool ALBSupportRobot::CertifyRobot()
{
    if (RobotState != ELBSupportRobotState::RouteValidation || !bLocalisationHealthy || !bSafetyNetworkHealthy)
    {
        return false;
    }
    FText VariantReason;
    if (!HasVariantTravelPermissives(VariantReason))
    {
        return false;
    }
    bCertified = true;
    bRouteRevalidationRequired = false;
    Condition = ELBSupportRobotCondition::Commissioned;
    ActiveCommonFault = ELBSupportRobotFault::None;
    SetRobotState(ELBSupportRobotState::Certified);
    return true;
}

void ALBSupportRobot::SetSafetyHealth(bool bLocalisationIsHealthy, bool bSafetyNetworkIsHealthy)
{
    bLocalisationHealthy = bLocalisationIsHealthy;
    bSafetyNetworkHealthy = bSafetyNetworkIsHealthy;
    if (bRouteAuthorityGranted && !bLocalisationHealthy)
    {
        ForceSafeStop(ELBSupportRobotFault::LocalisationLost, TEXT("Localisation confidence fell below the certified-route limit."));
    }
    else if (bRouteAuthorityGranted && !bSafetyNetworkHealthy)
    {
        ForceSafeStop(ELBSupportRobotFault::SafetyNetworkUnhealthy, TEXT("The RP01 safety network is unhealthy."));
    }
}

void ALBSupportRobot::SetRouteEnvironment(bool bRouteIsClear, bool bPersonIsInRoute, bool bIsMachineApproach, bool bIsDockingApproach)
{
    bRouteClear = bRouteIsClear;
    bPersonInRoute = bPersonIsInRoute;
    bMachineApproach = bIsMachineApproach;
    bDockingApproach = bIsDockingApproach;
    if (bRouteAuthorityGranted && !bRouteClear)
    {
        ForceSafeStop(ELBSupportRobotFault::RouteObstructed, TEXT("The certified route is no longer clear."));
    }
}

bool ALBSupportRobot::BeginCertifiedRoute(const FLBSupportRobotRoute& Route, bool bEmergencyDispatch)
{
    FText BlockingReason;
    if (!CanTravel(BlockingReason) || !Route.bCertified || Route.RouteId.IsNone() || Route.Revision <= 0 || Route.Waypoints.IsEmpty())
    {
        return false;
    }
    if (bEmergencyDispatch && Route.SpeedClass != ELBRouteSpeedClass::EmergencyCertifiedClearRoute)
    {
        return false;
    }

    LBMobileRoutePlanner::FSettings PlannerSettings;
    const FVector CollisionHalfExtent = CollisionRoot
        ? CollisionRoot->GetScaledBoxExtent()
        : FVector(76.0f, 46.5f, 55.0f);
    PlannerSettings.VehicleHalfExtentCm = FVector2D(CollisionHalfExtent.X, CollisionHalfExtent.Y);
    PlannerSettings.EnvelopeClearanceCm = 40.0f;
    PlannerSettings.CornerRadiusCm = 150.0f;
    PlannerSettings.MaximumCurveStepDegrees = 12.0f;
    TArray<FVector> RuntimeWaypoints;
    if (!LBMobileRoutePlanner::BuildClearanceAwarePath(
        GetWorld(), GetActorLocation(), Route.Waypoints, PlannerSettings, RuntimeWaypoints))
    {
        LastCommonFaultDetail = TEXT("The certified route has no clearance-safe path around the current machine and storage layout.");
        return false;
    }

    ActiveRoute = Route;
    ActiveRoute.Waypoints = MoveTemp(RuntimeWaypoints);
    ActiveWaypointIndex = 0;
    ActiveRouteStartLocation = GetActorLocation();
    bRouteAuthorityGranted = true;
    bEmergencyRoute = bEmergencyDispatch;
    bAutomaticChargeReturnActive = false;
    bDocked = false;
    DockId = NAME_None;
    CurrentSpeedCentimetresPerSecond = 0.0f;
    SetRobotState(ELBSupportRobotState::Dispatched);
    OnRouteStarted.Broadcast(UnitId, Route.RouteId);
    SetRobotState(ELBSupportRobotState::Navigating);
    return true;
}

void ALBSupportRobot::AbortRoute(bool bRaiseAuthorityFault)
{
    const bool bHadRoute = bRouteAuthorityGranted;
    bRouteAuthorityGranted = false;
    bEmergencyRoute = false;
    bAutomaticChargeReturnActive = false;
    ActiveWaypointIndex = INDEX_NONE;
    ActiveRoute = FLBSupportRobotRoute();
    ActiveRouteStartLocation = GetActorLocation();
    CurrentSpeedCentimetresPerSecond = 0.0f;

    if (bRaiseAuthorityFault && bHadRoute)
    {
        RaiseCommonFault(ELBSupportRobotFault::RouteAuthorityLost, TEXT("Route authority was withdrawn before the route completed."));
    }
    else if (bHadRoute && IsMotionOrWorkState(RobotState))
    {
        SetRobotState(bCertified ? ELBSupportRobotState::Certified : ELBSupportRobotState::SafetyStop);
    }
}

bool ALBSupportRobot::ConfirmDocked(FName NewDockId)
{
    if (NewDockId.IsNone() || bRouteAuthorityGranted || CurrentSpeedCentimetresPerSecond > KINDA_SMALL_NUMBER)
    {
        return false;
    }
    bDocked = true;
    DockId = NewDockId;
    SetRobotState(ELBSupportRobotState::Docked);
    SetRobotState(ELBSupportRobotState::Charging);
    return true;
}

bool ALBSupportRobot::Undock()
{
    if (!bDocked || !bCertified || bRouteRevalidationRequired)
    {
        return false;
    }
    bDocked = false;
    DockId = NAME_None;
    SetRobotState(ELBSupportRobotState::Certified);
    return true;
}

bool ALBSupportRobot::ConfigureAutomaticChargingRoute(const FLBSupportRobotRoute& Route, float DispatchThresholdPercent)
{
    if (!Route.bCertified || Route.RouteId.IsNone() || Route.Revision <= 0 || Route.Waypoints.IsEmpty()
        || Route.DestinationDockId.IsNone() || Route.SpeedClass == ELBRouteSpeedClass::EmergencyCertifiedClearRoute
        || DispatchThresholdPercent < LowBatteryThresholdPercent || DispatchThresholdPercent > 80.0f)
    {
        return false;
    }

    AutomaticChargingRoute = Route;
    AutomaticChargeDispatchThresholdPercent = DispatchThresholdPercent;
    bAutomaticChargingEnabled = true;
    return true;
}

void ALBSupportRobot::RaiseCommonFault(ELBSupportRobotFault Fault, const FString& Detail)
{
    if (Fault == ELBSupportRobotFault::None)
    {
        return;
    }
    ForceSafeStop(Fault, Detail);
}

bool ALBSupportRobot::ClearCommonFault()
{
    if (ActiveCommonFault == ELBSupportRobotFault::None || !bLocalisationHealthy || !bSafetyNetworkHealthy || !bRouteClear)
    {
        return false;
    }
    FText VariantReason;
    if (!HasVariantTravelPermissives(VariantReason))
    {
        return false;
    }
    const ELBSupportRobotFault Previous = ActiveCommonFault;
    ActiveCommonFault = ELBSupportRobotFault::None;
    LastCommonFaultDetail.Reset();
    bRouteRevalidationRequired = true;
    SetRobotState(ELBSupportRobotState::ReadyForTest);
    OnCommonFaultChanged.Broadcast(Previous, ActiveCommonFault);
    return true;
}

bool ALBSupportRobot::CanTravel(FText& BlockingReason) const
{
    BlockingReason = FText::GetEmpty();
    if (!bCertified)
    {
        BlockingReason = FText::FromString(TEXT("Robot commissioning certification is missing."));
        return false;
    }
    if (bRouteRevalidationRequired)
    {
        BlockingReason = FText::FromString(TEXT("Certified-route validation is required after load, repair or fault."));
        return false;
    }
    if (ActiveCommonFault != ELBSupportRobotFault::None)
    {
        BlockingReason = FText::FromString(TEXT("A common platform fault is active."));
        return false;
    }
    if (!bLocalisationHealthy)
    {
        BlockingReason = FText::FromString(TEXT("Localisation is not healthy."));
        return false;
    }
    if (!bSafetyNetworkHealthy)
    {
        BlockingReason = FText::FromString(TEXT("Safety network is not healthy."));
        return false;
    }
    if (!bRouteClear)
    {
        BlockingReason = FText::FromString(TEXT("Route-clear authority is absent."));
        return false;
    }
    if (BatteryStateOfChargePercent <= 5.0f)
    {
        BlockingReason = FText::FromString(TEXT("Battery state of charge is below the safe-motion reserve."));
        return false;
    }
    return HasVariantTravelPermissives(BlockingReason);
}

FLBSupportRobotSaveState ALBSupportRobot::CaptureCommonSaveState() const
{
    FLBSupportRobotSaveState Saved;
    Saved.UnitId = UnitId;
    Saved.VariantId = VariantId;
    Saved.State = RobotState;
    Saved.Condition = Condition;
    Saved.ActiveFault = ActiveCommonFault;
    Saved.BatteryStateOfChargePercent = BatteryStateOfChargePercent;
    Saved.BatteryHealthPercent = BatteryHealthPercent;
    Saved.OperatingHours = OperatingHours;
    Saved.MissionCount = MissionCount;
    Saved.ServiceCycles = ServiceCycles;
    Saved.bCertified = bCertified;
    Saved.bDocked = bDocked;
    Saved.DockId = DockId;
    Saved.LastCertifiedRouteId = ActiveRoute.RouteId;
    Saved.LastCertifiedRouteRevision = ActiveRoute.Revision;
    Saved.ActiveTaskId = ActiveTaskId;
    Saved.SavedTransform = GetActorTransform();
    Saved.bRouteRevalidationRequired = bRouteRevalidationRequired;
    return Saved;
}

bool ALBSupportRobot::RestoreCommonSaveState(const FLBSupportRobotSaveState& SavedState)
{
    if (SavedState.Version != 1 || SavedState.UnitId.IsNone() || SavedState.VariantId.IsNone())
    {
        return false;
    }
    if ((!UnitId.IsNone() && UnitId != SavedState.UnitId)
        || (!VariantId.IsNone() && VariantId != TEXT("LB-RP01") && VariantId != SavedState.VariantId))
    {
        return false;
    }

    UnitId = SavedState.UnitId;
    VariantId = SavedState.VariantId;
    Condition = SavedState.Condition;
    ActiveCommonFault = SavedState.ActiveFault;
    BatteryStateOfChargePercent = FMath::Clamp(SavedState.BatteryStateOfChargePercent, 0.0f, 100.0f);
    BatteryHealthPercent = FMath::Clamp(SavedState.BatteryHealthPercent, 0.0f, 100.0f);
    OperatingHours = FMath::Max(0.0f, SavedState.OperatingHours);
    MissionCount = FMath::Max(0, SavedState.MissionCount);
    ServiceCycles = FMath::Max(0, SavedState.ServiceCycles);
    bCertified = SavedState.bCertified;
    bDocked = SavedState.bDocked;
    DockId = SavedState.bDocked ? SavedState.DockId : NAME_None;
    ActiveTaskId = SavedState.ActiveTaskId;
    SetActorTransform(SavedState.SavedTransform, false, nullptr, ETeleportType::TeleportPhysics);

    // Save files record where work stopped, but never restore route authority or
    // resume motion/arm/cleaning behind the player's back.
    ActiveRoute = FLBSupportRobotRoute();
    ActiveWaypointIndex = INDEX_NONE;
    ActiveRouteStartLocation = GetActorLocation();
    bRouteAuthorityGranted = false;
    bEmergencyRoute = false;
    bAutomaticChargeReturnActive = false;
    CurrentSpeedCentimetresPerSecond = 0.0f;
    bRouteRevalidationRequired = true;
    bLocalisationHealthy = false;
    bSafetyNetworkHealthy = false;
    bRouteClear = false;

    if (Condition == ELBSupportRobotCondition::Mothballed)
    {
        SetRobotState(ELBSupportRobotState::Mothballed);
    }
    else if (Condition == ELBSupportRobotCondition::RepairInProgress)
    {
        SetRobotState(ELBSupportRobotState::RepairRequired);
    }
    else if (bDocked)
    {
        SetRobotState(ELBSupportRobotState::Docked);
    }
    else
    {
        if (ActiveCommonFault == ELBSupportRobotFault::None)
        {
            ActiveCommonFault = ELBSupportRobotFault::RestoreRevalidationRequired;
        }
        SetRobotState(ELBSupportRobotState::SafetyStop);
    }
    OnEnteredSafeStop();
    return true;
}

bool ALBSupportRobot::HasVariantTravelPermissives(FText& BlockingReason) const
{
    BlockingReason = FText::GetEmpty();
    return true;
}

float ALBSupportRobot::GetMaximumSpeedCentimetresPerSecond(ELBRouteSpeedClass SpeedClass, bool bEmergencyDispatch) const
{
    switch (SpeedClass)
    {
    case ELBRouteSpeedClass::Docking:
        return 10.0f;
    case ELBRouteSpeedClass::MachineApproach:
        return 20.0f;
    case ELBRouteSpeedClass::OccupiedAisle:
        return 60.0f;
    case ELBRouteSpeedClass::EmergencyCertifiedClearRoute:
        return bEmergencyDispatch ? 120.0f : 100.0f;
    case ELBRouteSpeedClass::NormalTransit:
    default:
        return 100.0f;
    }
}

void ALBSupportRobot::OnEnteredSafeStop()
{
}

void ALBSupportRobot::UpdateVariantWorkLights()
{
}

void ALBSupportRobot::SetRobotState(ELBSupportRobotState NewState)
{
    if (RobotState == NewState)
    {
        UpdateStatusBeacon();
        UpdateWorkLights();
        return;
    }
    const ELBSupportRobotState Previous = RobotState;
    RobotState = NewState;
    UpdateStatusBeacon();
    UpdateWorkLights();
    OnRobotStateChanged.Broadcast(Previous, NewState);
}

void ALBSupportRobot::UpdateWorkLights()
{
    // Parked or charging robots do not wash the factory view. Active waits and
    // safe stops retain their lamps so the unit remains conspicuous to players.
    const bool bForwardLightsOn = RobotState != ELBSupportRobotState::Mothballed
        && RobotState != ELBSupportRobotState::Inspection
        && RobotState != ELBSupportRobotState::RepairRequired
        && RobotState != ELBSupportRobotState::ReadyForTest
        && RobotState != ELBSupportRobotState::ManualCommissioning
        && RobotState != ELBSupportRobotState::Calibration
        && RobotState != ELBSupportRobotState::Certified
        && RobotState != ELBSupportRobotState::Docked
        && RobotState != ELBSupportRobotState::Charging;

    if (LeftForwardWorkLight)
    {
        LeftForwardWorkLight->SetVisibility(bForwardLightsOn, true);
    }
    if (RightForwardWorkLight)
    {
        RightForwardWorkLight->SetVisibility(bForwardLightsOn, true);
    }
    UpdateVariantWorkLights();
}

void ALBSupportRobot::UpdateStatusBeacon()
{
    if (!StatusBeacon) return;

    if (ActiveCommonFault != ELBSupportRobotFault::None)
    {
        StatusBeacon->SetStatus(ELBStatusBeaconState::Fault);
        return;
    }

    switch (RobotState)
    {
    case ELBSupportRobotState::Dispatched:
    case ELBSupportRobotState::Navigating:
    case ELBSupportRobotState::Returning:
        StatusBeacon->SetStatus(ELBStatusBeaconState::Moving);
        break;

    case ELBSupportRobotState::Cleaning:
    case ELBSupportRobotState::Inspecting:
    case ELBSupportRobotState::Diagnosing:
    case ELBSupportRobotState::LightService:
    case ELBSupportRobotState::Lubricating:
    case ELBSupportRobotState::DeliveringParts:
    case ELBSupportRobotState::ModuleExchange:
    case ELBSupportRobotState::Verifying:
    case ELBSupportRobotState::Servicing:
    case ELBSupportRobotState::Maintenance:
        StatusBeacon->SetStatus(ELBStatusBeaconState::Running);
        break;

    case ELBSupportRobotState::Certified:
        StatusBeacon->SetStatus(ELBStatusBeaconState::Ready);
        break;

    case ELBSupportRobotState::ReadyForTest:
    case ELBSupportRobotState::ManualCommissioning:
    case ELBSupportRobotState::Calibration:
    case ELBSupportRobotState::RouteValidation:
    case ELBSupportRobotState::Docked:
    case ELBSupportRobotState::Charging:
    case ELBSupportRobotState::WaitingForPermission:
        StatusBeacon->SetStatus(ELBStatusBeaconState::Waiting);
        break;

    case ELBSupportRobotState::Mothballed:
    case ELBSupportRobotState::Inspection:
    case ELBSupportRobotState::RepairRequired:
        StatusBeacon->SetStatus(ELBStatusBeaconState::Stopped);
        break;

    default:
        // Blocked, safety-stop and variant-specific fault states are always red.
        StatusBeacon->SetStatus(ELBStatusBeaconState::Fault);
        break;
    }
}

void ALBSupportRobot::ForceSafeStop(ELBSupportRobotFault Fault, const FString& Detail)
{
    const ELBSupportRobotFault PreviousFault = ActiveCommonFault;
    ActiveCommonFault = Fault;
    LastCommonFaultDetail = Detail;
    bRouteAuthorityGranted = false;
    bEmergencyRoute = false;
    ActiveWaypointIndex = INDEX_NONE;
    ActiveRoute = FLBSupportRobotRoute();
    ActiveRouteStartLocation = GetActorLocation();
    CurrentSpeedCentimetresPerSecond = 0.0f;
    bRouteRevalidationRequired = true;

    switch (Fault)
    {
    case ELBSupportRobotFault::RouteObstructed:
        SetRobotState(ELBSupportRobotState::Blocked);
        break;
    case ELBSupportRobotFault::LowBattery:
        SetRobotState(ELBSupportRobotState::LowBattery);
        break;
    case ELBSupportRobotFault::SpillDetected:
        SetRobotState(ELBSupportRobotState::SpillDetected);
        break;
    case ELBSupportRobotFault::TankFull:
        SetRobotState(ELBSupportRobotState::TankFull);
        break;
    case ELBSupportRobotFault::BrushJam:
        SetRobotState(ELBSupportRobotState::BrushJam);
        break;
    case ELBSupportRobotFault::SensorCoverageInvalid:
        SetRobotState(ELBSupportRobotState::SensorDirty);
        break;
    default:
        SetRobotState(ELBSupportRobotState::SafetyStop);
        break;
    }

    OnEnteredSafeStop();
    OnCommonFaultChanged.Broadcast(PreviousFault, ActiveCommonFault);
    OnWorkOrderRequested.Broadcast(UnitId, TEXT("SUPPORT_ROBOT_FAULT"), Detail);
}

bool ALBSupportRobot::IsMotionOrWorkState(ELBSupportRobotState State) const
{
    return State == ELBSupportRobotState::Dispatched
        || State == ELBSupportRobotState::Navigating
        || State == ELBSupportRobotState::Cleaning
        || State == ELBSupportRobotState::Returning;
}

ELBRouteSpeedClass ALBSupportRobot::GetEffectiveSpeedClass() const
{
    if (bDockingApproach)
    {
        return ELBRouteSpeedClass::Docking;
    }
    if (bMachineApproach)
    {
        return ELBRouteSpeedClass::MachineApproach;
    }
    if (bPersonInRoute)
    {
        return ELBRouteSpeedClass::OccupiedAisle;
    }
    return ActiveRoute.SpeedClass;
}

void ALBSupportRobot::TickRouteMovement(float DeltaSeconds)
{
    FText BlockingReason;
    if (!bRouteAuthorityGranted || !CanTravel(BlockingReason) || !ActiveRoute.Waypoints.IsValidIndex(ActiveWaypointIndex))
    {
        ForceSafeStop(ELBSupportRobotFault::RouteAuthorityLost, BlockingReason.ToString());
        return;
    }

    const FVector CurrentLocation = GetActorLocation();
    // Pure-pursuit followers do not necessarily touch every sampled curve point.
    // Advance a point once it is reached or the robot has crossed its local
    // normal plane while remaining close to that segment.
    while (ActiveRoute.Waypoints.IsValidIndex(ActiveWaypointIndex))
    {
        const FVector Target = ActiveRoute.Waypoints[ActiveWaypointIndex];
        const FVector SegmentStart = ActiveWaypointIndex == 0
            ? ActiveRouteStartLocation
            : ActiveRoute.Waypoints[ActiveWaypointIndex - 1];
        const FVector Segment = (Target - SegmentStart).GetSafeNormal2D();
        const float Distance = FVector::Dist2D(CurrentLocation, Target);
        const bool bFinalPoint = ActiveWaypointIndex == ActiveRoute.Waypoints.Num() - 1;
        if (bFinalPoint && Distance <= WaypointToleranceCentimetres)
        {
            CurrentSpeedCentimetresPerSecond = FMath::FInterpConstantTo(
                CurrentSpeedCentimetresPerSecond, 0.0f, DeltaSeconds,
                DecelerationCentimetresPerSecondSquared);
            if (CurrentSpeedCentimetresPerSecond <= KINDA_SMALL_NUMBER)
            {
                ++ActiveWaypointIndex;
                CompleteActiveRoute();
            }
            return;
        }
        const bool bPassedPoint = !bFinalPoint && !Segment.IsNearlyZero()
            && FVector::DotProduct((CurrentLocation - Target).GetSafeNormal2D(), Segment) > 0.0f
            && Distance <= MaximumSteeringLookAheadCentimetres;
        if (Distance > WaypointToleranceCentimetres && !bPassedPoint)
        {
            break;
        }
        ++ActiveWaypointIndex;
    }
    if (!ActiveRoute.Waypoints.IsValidIndex(ActiveWaypointIndex))
    {
        CompleteActiveRoute();
        return;
    }

    float RemainingRouteDistance = FVector::Dist2D(
        CurrentLocation, ActiveRoute.Waypoints[ActiveWaypointIndex]);
    for (int32 PointIndex = ActiveWaypointIndex + 1; PointIndex < ActiveRoute.Waypoints.Num(); ++PointIndex)
    {
        RemainingRouteDistance += FVector::Dist2D(
            ActiveRoute.Waypoints[PointIndex - 1], ActiveRoute.Waypoints[PointIndex]);
    }

    const float MaximumSpeed = GetMaximumSpeedCentimetresPerSecond(GetEffectiveSpeedClass(), bEmergencyRoute);
    const float LookAheadDistance = FMath::Clamp(
        55.0f + CurrentSpeedCentimetresPerSecond * 0.9f,
        MinimumSteeringLookAheadCentimetres,
        MaximumSteeringLookAheadCentimetres);
    FVector SteeringTarget = CurrentLocation;
    FVector Cursor = CurrentLocation;
    float LookAheadRemaining = LookAheadDistance;
    for (int32 PointIndex = ActiveWaypointIndex; PointIndex < ActiveRoute.Waypoints.Num(); ++PointIndex)
    {
        const FVector Point = ActiveRoute.Waypoints[PointIndex];
        const float SegmentLength = FVector::Dist2D(Cursor, Point);
        if (SegmentLength >= LookAheadRemaining && SegmentLength > KINDA_SMALL_NUMBER)
        {
            SteeringTarget = FMath::Lerp(Cursor, Point, LookAheadRemaining / SegmentLength);
            break;
        }
        SteeringTarget = Point;
        LookAheadRemaining -= SegmentLength;
        Cursor = Point;
    }

    const FVector SteeringDirection = (SteeringTarget - CurrentLocation).GetSafeNormal2D();
    if (SteeringDirection.IsNearlyZero())
    {
        CurrentSpeedCentimetresPerSecond = FMath::FInterpConstantTo(
            CurrentSpeedCentimetresPerSecond, 0.0f, DeltaSeconds,
            DecelerationCentimetresPerSecondSquared);
        return;
    }

    const FRotator CurrentRotation = GetActorRotation();
    FRotator DesiredRotation = SteeringDirection.Rotation();
    DesiredRotation.Pitch = CurrentRotation.Pitch;
    DesiredRotation.Roll = CurrentRotation.Roll;
    const float HeadingErrorDegrees = FMath::Abs(FMath::FindDeltaAngleDegrees(CurrentRotation.Yaw, DesiredRotation.Yaw));

    // Brake to the final destination, and bleed speed before a large heading
    // correction so the body follows the sampled arc instead of sliding side-on.
    const float BrakingSpeed = FMath::Sqrt(FMath::Max(
        0.0f, 2.0f * DecelerationCentimetresPerSecondSquared
            * FMath::Max(0.0f, RemainingRouteDistance - WaypointToleranceCentimetres)));
    const float HeadingSpeedScale = FMath::GetMappedRangeValueClamped(
        FVector2D(0.0f, 90.0f), FVector2D(1.0f, 0.18f), HeadingErrorDegrees);
    const float DesiredSpeed = FMath::Min3(MaximumSpeed, BrakingSpeed, MaximumSpeed * HeadingSpeedScale);
    const float SpeedChangeRate = DesiredSpeed >= CurrentSpeedCentimetresPerSecond
        ? AccelerationCentimetresPerSecondSquared
        : DecelerationCentimetresPerSecondSquared;
    CurrentSpeedCentimetresPerSecond = FMath::FInterpConstantTo(
        CurrentSpeedCentimetresPerSecond, DesiredSpeed, DeltaSeconds, SpeedChangeRate);

    const FRotator NewRotation = FMath::RInterpConstantTo(
        CurrentRotation, DesiredRotation, DeltaSeconds, MaximumSteeringDegreesPerSecond);
    SetActorRotation(NewRotation);
    const FVector TravelDirection = NewRotation.Vector().GetSafeNormal2D();
    const float DistanceToCurrentPoint = FVector::Dist2D(
        CurrentLocation, ActiveRoute.Waypoints[ActiveWaypointIndex]);
    const float Travel = FMath::Min(DistanceToCurrentPoint,
        CurrentSpeedCentimetresPerSecond * FMath::Max(0.0f, DeltaSeconds));
    const FVector Start = GetActorLocation();
    const FVector Desired = Start + TravelDirection * Travel;
    FHitResult Hit;
    SetActorLocation(Desired, true, &Hit, ETeleportType::None);

    // A flush sealed-concrete datum and the robot's own assigned service dock
    // can be reported by the initial horizontal sweep. Re-test the same full
    // robot box while ignoring only those authorities. The assigned dock is
    // ignored solely inside its 3.5 m approach/egress envelope; every other
    // dock, machine, guard and robot remains an authoritative blocker.
    const FName ExpectedHomeDockId = UnitId.IsNone()
        ? NAME_None
        : FName(*FString::Printf(TEXT("LB-DOCK-%s"), *UnitId.ToString().RightChop(3)));
    FString UnitTagSuffix = UnitId.ToString().RightChop(3);
    UnitTagSuffix.ReplaceInline(TEXT("-"), TEXT("_"));
    const FName ExpectedVisualDockTag(*FString::Printf(TEXT("LB.SupportFleet.%s"), *UnitTagSuffix));
    const ALBSupportRobotServiceDock* HitDock = Cast<ALBSupportRobotServiceDock>(Hit.GetActor());
    const bool bAssignedDockContact = HitDock
        && HitDock->GetDockId() == ExpectedHomeDockId
        && FVector::Dist2D(Start, HitDock->GetActorLocation()) <= 350.0f;
    const bool bAssignedVisualDockContact = Hit.GetActor()
        && Hit.GetActor()->ActorHasTag(TEXT("LB.SupportFleet.Dock"))
        && Hit.GetActor()->ActorHasTag(ExpectedVisualDockTag)
        && FVector::Dist2D(Start, Hit.GetActor()->GetActorLocation()) <= 350.0f;
    const bool bFloorContact = Hit.bBlockingHit && Hit.GetActor()
        && (Hit.GetActor()->ActorHasTag(TEXT("LB.Environment.Floor.SealedConcrete"))
            || Hit.GetActor()->ActorHasTag(TEXT("LB.SupportArea.Role.BayFloor")));
    if (Hit.bBlockingHit && Hit.GetActor() && (bFloorContact || bAssignedDockContact || bAssignedVisualDockContact))
    {
        FCollisionQueryParams Params(SCENE_QUERY_STAT(LBSupportRobotHorizontalTravel), false, this);
        for (TActorIterator<AActor> It(GetWorld()); It; ++It)
        {
            if (It->ActorHasTag(TEXT("LB.Environment.Floor.SealedConcrete"))
                || It->ActorHasTag(TEXT("LB.SupportArea.Role.BayFloor")))
            {
                Params.AddIgnoredActor(*It);
            }
            if (const ALBSupportRobotServiceDock* Dock = Cast<ALBSupportRobotServiceDock>(*It))
            {
                if (Dock->GetDockId() == ExpectedHomeDockId
                    && FVector::Dist2D(Start, Dock->GetActorLocation()) <= 350.0f)
                {
                    Params.AddIgnoredActor(*It);
                }
            }
            if (It->ActorHasTag(TEXT("LB.SupportFleet.Dock"))
                && It->ActorHasTag(ExpectedVisualDockTag)
                && FVector::Dist2D(Start, It->GetActorLocation()) <= 350.0f)
            {
                Params.AddIgnoredActor(*It);
            }
        }
        FHitResult NonFloorHit;
        const bool bOtherBlocker = GetWorld()->SweepSingleByChannel(
            NonFloorHit, Start, Desired, CollisionRoot->GetComponentQuat(),
            CollisionRoot->GetCollisionObjectType(),
            FCollisionShape::MakeBox(CollisionRoot->GetScaledBoxExtent()), Params);
        if (bOtherBlocker)
        {
            Hit = NonFloorHit;
        }
        else
        {
            SetActorLocation(Desired, false, nullptr, ETeleportType::None);
            Hit = FHitResult();
        }
    }
    if (Hit.bBlockingHit)
    {
        ForceSafeStop(ELBSupportRobotFault::RouteObstructed, FString::Printf(TEXT("Route collision with %s."), *GetNameSafe(Hit.GetActor())));
    }
}

void ALBSupportRobot::TickBattery(float DeltaSeconds, float DistanceMovedCentimetres)
{
    if (bDocked && (RobotState == ELBSupportRobotState::Docked || RobotState == ELBSupportRobotState::Charging))
    {
        BatteryStateOfChargePercent = FMath::Min(100.0f, BatteryStateOfChargePercent + ChargingRatePercentPerSecond * DeltaSeconds);
        if (BatteryStateOfChargePercent < 100.0f)
        {
            SetRobotState(ELBSupportRobotState::Charging);
        }
        else
        {
            SetRobotState(ELBSupportRobotState::Docked);
        }
        return;
    }

    if (DistanceMovedCentimetres > 0.0f)
    {
        BatteryStateOfChargePercent = FMath::Max(0.0f,
            BatteryStateOfChargePercent - (DistanceMovedCentimetres / 100.0f) * TransitDrainPercentPerMetre);
    }

    const bool bIdleAndAvailable = !bRouteAuthorityGranted && ActiveTaskId.IsNone()
        && (RobotState == ELBSupportRobotState::Certified || RobotState == ELBSupportRobotState::Docked);
    if (bIdleAndAvailable && BatteryStateOfChargePercent <= AutomaticChargeDispatchThresholdPercent)
    {
        TryBeginAutomaticChargeReturn();
    }

    if (bRouteAuthorityGranted && !bAutomaticChargeReturnActive
        && BatteryStateOfChargePercent <= LowBatteryThresholdPercent)
    {
        if (!ActiveTaskId.IsNone() || !TryBeginAutomaticChargeReturn())
        {
            ForceSafeStop(ELBSupportRobotFault::LowBattery,
                TEXT("Battery reached reserve and no certified automatic charging return was available."));
        }
    }
}

bool ALBSupportRobot::TryBeginAutomaticChargeReturn()
{
    if (!bAutomaticChargingEnabled || AutomaticChargingRoute.DestinationDockId.IsNone()
        || !ActiveTaskId.IsNone() || bDocked || !bCertified || bRouteRevalidationRequired
        || ActiveCommonFault != ELBSupportRobotFault::None)
    {
        return false;
    }

    if (bRouteAuthorityGranted)
    {
        AbortRoute(false);
    }
    if (!BeginCertifiedRoute(AutomaticChargingRoute, false))
    {
        return false;
    }
    bAutomaticChargeReturnActive = true;
    SetRobotState(ELBSupportRobotState::Returning);
    return true;
}

void ALBSupportRobot::CompleteActiveRoute()
{
    const FName CompletedRouteId = ActiveRoute.RouteId;
    const FName DestinationDockId = ActiveRoute.DestinationDockId;
    bRouteAuthorityGranted = false;
    bEmergencyRoute = false;
    bAutomaticChargeReturnActive = false;
    ActiveWaypointIndex = INDEX_NONE;
    ActiveRoute = FLBSupportRobotRoute();
    ActiveRouteStartLocation = GetActorLocation();
    CurrentSpeedCentimetresPerSecond = 0.0f;
    ++MissionCount;

    if (!DestinationDockId.IsNone())
    {
        bDocked = true;
        DockId = DestinationDockId;
        SetRobotState(ELBSupportRobotState::Docked);
    }
    else
    {
        SetRobotState(ELBSupportRobotState::Certified);
    }
    OnRouteCompleted.Broadcast(UnitId, CompletedRouteId);
}
