#include "LBCleaningAMR.h"

#include "Components/BoxComponent.h"
#include "Components/ChildActorComponent.h"
#include "Components/PrimitiveComponent.h"
#include "Components/SceneComponent.h"
#include "Components/SpotLightComponent.h"

ALBCleaningAMR::ALBCleaningAMR()
{
    VariantId = TEXT("LB-CR01");
    CollisionRoot->SetBoxExtent(FVector(76.0f, 49.0f, 56.0f));
    RobotVisualRoot->SetRelativeLocation(FVector(0.0f, 0.0f, -56.0f));

    PresentationComponent = CreateDefaultSubobject<UChildActorComponent>(TEXT("CR01Presentation"));
    PresentationComponent->SetupAttachment(RobotVisualRoot);

    CleaningDeckWorkLight = CreateDefaultSubobject<USpotLightComponent>(TEXT("LENS_CR01_CLEANING_DECK_WORKLIGHT"));
    CleaningDeckWorkLight->SetupAttachment(RobotVisualRoot);
    CleaningDeckWorkLight->SetRelativeLocation(FVector(44.0f, 0.0f, 43.0f));
    CleaningDeckWorkLight->SetRelativeRotation(FRotator(-62.0f, 0.0f, 0.0f));
    CleaningDeckWorkLight->SetIntensity(1150.0f);
    CleaningDeckWorkLight->SetAttenuationRadius(430.0f);
    CleaningDeckWorkLight->SetInnerConeAngle(28.0f);
    CleaningDeckWorkLight->SetOuterConeAngle(48.0f);
    CleaningDeckWorkLight->SetLightColor(FLinearColor(0.86f, 0.94f, 1.0f));
    CleaningDeckWorkLight->SetCastShadows(false);
    CleaningDeckWorkLight->SetVisibility(false);

    const auto CreatePivot = [this](const TCHAR* Name, USceneComponent* Parent, const FVector& RelativeLocation)
    {
        USceneComponent* Pivot = CreateDefaultSubobject<USceneComponent>(FName(Name));
        Pivot->SetupAttachment(Parent);
        Pivot->SetRelativeLocation(RelativeLocation);
        return Pivot;
    };

    DriveWheelLeftPivot = CreatePivot(TEXT("PVT_DriveWheel_L"), RobotVisualRoot, FVector(-10.0f, -40.5f, 17.0f));
    DriveWheelRightPivot = CreatePivot(TEXT("PVT_DriveWheel_R"), RobotVisualRoot, FVector(-10.0f, 40.5f, 17.0f));
    FrontCasterSwivelPivot = CreatePivot(TEXT("PVT_CasterSwivel_F"), RobotVisualRoot, FVector(47.0f, 0.0f, 16.0f));
    FrontCasterRollPivot = CreatePivot(TEXT("PVT_CasterRoll_F"), FrontCasterSwivelPivot, FVector(0.0f, 0.0f, -8.0f));
    RearCasterSwivelPivot = CreatePivot(TEXT("PVT_CasterSwivel_R"), RobotVisualRoot, FVector(-53.0f, 0.0f, 16.0f));
    RearCasterRollPivot = CreatePivot(TEXT("PVT_CasterRoll_R"), RearCasterSwivelPivot, FVector(0.0f, 0.0f, -8.0f));

    FrontBrushLiftPivot = CreatePivot(TEXT("PVT_FrontBrushLift"), RobotVisualRoot, FVector(63.5f, 0.0f, 16.5f));
    FrontBrushSpinPivot = CreatePivot(TEXT("PVT_FrontBrushSpin"), FrontBrushLiftPivot, FVector(0.0f, 0.0f, -4.0f));

    SideBrushArmLeftPivot = CreatePivot(TEXT("PVT_SideBrushArm_L"), RobotVisualRoot, FVector(45.0f, -33.0f, 15.5f));
    SideBrushArmRightPivot = CreatePivot(TEXT("PVT_SideBrushArm_R"), RobotVisualRoot, FVector(45.0f, 33.0f, 15.5f));
    SideBrushLiftLeftPivot = CreatePivot(TEXT("PVT_SideBrushLift_L"), SideBrushArmLeftPivot, FVector(7.0f, -17.0f, -5.0f));
    SideBrushLiftRightPivot = CreatePivot(TEXT("PVT_SideBrushLift_R"), SideBrushArmRightPivot, FVector(7.0f, 17.0f, -5.0f));
    SideBrushSpinLeftPivot = CreatePivot(TEXT("PVT_SideBrushSpin_L"), SideBrushLiftLeftPivot, FVector(0.0f, 0.0f, -2.5f));
    SideBrushSpinRightPivot = CreatePivot(TEXT("PVT_SideBrushSpin_R"), SideBrushLiftRightPivot, FVector(0.0f, 0.0f, -2.5f));

    ScrubDeckLiftPivot = CreatePivot(TEXT("PVT_ScrubDeckLift"), RobotVisualRoot, FVector(4.0f, 0.0f, 18.5f));
    ScrubDiscLeftPivot = CreatePivot(TEXT("PVT_ScrubDisc_L"), ScrubDeckLiftPivot, FVector(0.0f, -17.5f, -11.0f));
    ScrubDiscRightPivot = CreatePivot(TEXT("PVT_ScrubDisc_R"), ScrubDeckLiftPivot, FVector(0.0f, 17.5f, -11.0f));

    SqueegeeLiftPivot = CreatePivot(TEXT("PVT_SqueegeeLift"), RobotVisualRoot, FVector(-69.0f, 0.0f, 16.5f));
    SqueegeeYawPivot = CreatePivot(TEXT("PVT_SqueegeeYaw"), SqueegeeLiftPivot, FVector(0.0f, 0.0f, -6.5f));

    HopperSlidePivot = CreatePivot(TEXT("PVT_HopperSlide"), RobotVisualRoot, FVector(38.0f, 0.0f, 28.0f));
    HopperLidPivot = CreatePivot(TEXT("PVT_HopperLid"), RobotVisualRoot, FVector(28.0f, 0.0f, 52.0f));
    LeftDoorPivot = CreatePivot(TEXT("PVT_Door_Left"), RobotVisualRoot, FVector(-8.0f, -45.5f, 69.0f));
    RightDoorPivot = CreatePivot(TEXT("PVT_Door_Right"), RobotVisualRoot, FVector(-8.0f, 45.5f, 69.0f));
    RearDoorPivot = CreatePivot(TEXT("PVT_Door_Rear"), RobotVisualRoot, FVector(-62.0f, 0.0f, 72.0f));
    FilterLidPivot = CreatePivot(TEXT("PVT_FilterLid"), RobotVisualRoot, FVector(-43.0f, -26.0f, 76.0f));

    DockChargeContactLeftPivot = CreatePivot(TEXT("PVT_DockChargeContact_L"), RobotVisualRoot, FVector(-73.5f, -12.0f, 34.0f));
    DockChargeContactRightPivot = CreatePivot(TEXT("PVT_DockChargeContact_R"), RobotVisualRoot, FVector(-73.5f, 12.0f, 34.0f));
}

void ALBCleaningAMR::BeginPlay()
{
    Super::BeginPlay();
    CachePresentationBindings();
}

void ALBCleaningAMR::Tick(float DeltaSeconds)
{
    if (PresentationPivots.IsEmpty())
    {
        CachePresentationBindings();
    }
    const FVector Before = GetActorLocation();
    Super::Tick(DeltaSeconds);
    ApplyCleaningPose(DeltaSeconds);

    if (RobotState == ELBSupportRobotState::Cleaning && bWaterValveOpen && bBrushesRunning)
    {
        TickCleaningResources(FVector::Dist2D(Before, GetActorLocation()));
    }
}

void ALBCleaningAMR::UpdateVariantWorkLights()
{
    if (CleaningDeckWorkLight)
    {
        const bool bCleaningLightOn = RobotState == ELBSupportRobotState::Cleaning
            && bBrushesRunning && bCleaningHeadsLowered;
        CleaningDeckWorkLight->SetVisibility(bCleaningLightOn, true);
    }
}

bool ALBCleaningAMR::StartCleaningTask(FName TaskId, FName CleaningZoneId)
{
    if (TaskId.IsNone() || CleaningZoneId.IsNone() || RobotState != ELBSupportRobotState::Navigating
        || !HasRouteAuthority() || ActiveCleaningFault != ELBCleaningAMRFault::None
        || !bSensorCoverageCertified || CleanWaterLitres <= 0.0f
        || RecoveryWaterLitres >= RecoveryWaterCapacityLitres || HopperLoadLitres >= HopperCapacityLitres
        || FrontBrushWearPercent <= 5.0f || SideBrushWearPercent <= 5.0f
        || ScrubDiscWearPercent <= 5.0f || SqueegeeWearPercent <= 5.0f)
    {
        return false;
    }

    ActiveTaskId = TaskId;
    ActiveCleaningZoneId = CleaningZoneId;
    bWaterValveOpen = true;
    bBrushesRunning = true;
    bCleaningHeadsLowered = true;
    LastCoverageLocation = GetActorLocation();
    SetRobotState(ELBSupportRobotState::Cleaning);
    return true;
}

void ALBCleaningAMR::StopCleaningTask()
{
    bWaterValveOpen = false;
    bBrushesRunning = false;
    bCleaningHeadsLowered = false;
    ActiveCleaningZoneId = NAME_None;
    ActiveTaskId = NAME_None;
    if (RobotState == ELBSupportRobotState::Cleaning)
    {
        SetRobotState(HasRouteAuthority() ? ELBSupportRobotState::Navigating : ELBSupportRobotState::Certified);
    }
}

bool ALBCleaningAMR::SetCleaningResources(float NewCleanWaterLitres, float NewRecoveryWaterLitres, float NewHopperLoadLitres)
{
    if (NewCleanWaterLitres < 0.0f || NewCleanWaterLitres > CleanWaterCapacityLitres
        || NewRecoveryWaterLitres < 0.0f || NewRecoveryWaterLitres > RecoveryWaterCapacityLitres
        || NewHopperLoadLitres < 0.0f || NewHopperLoadLitres > HopperCapacityLitres)
    {
        return false;
    }
    CleanWaterLitres = NewCleanWaterLitres;
    RecoveryWaterLitres = NewRecoveryWaterLitres;
    HopperLoadLitres = NewHopperLoadLitres;
    OnCleaningResourcesChanged.Broadcast(CleanWaterLitres, RecoveryWaterLitres, HopperLoadLitres);
    return true;
}

void ALBCleaningAMR::SetSensorCoverageCertified(bool bCertifiedCoverage)
{
    bSensorCoverageCertified = bCertifiedCoverage;
    if (!bSensorCoverageCertified && HasRouteAuthority())
    {
        ActiveCleaningFault = ELBCleaningAMRFault::SensorDirty;
        RaiseCommonFault(ELBSupportRobotFault::SensorCoverageInvalid,
            TEXT("Safety sensor coverage is dirty, occluded or uncertified."));
    }
}

void ALBCleaningAMR::ReportHazardousSpill(FName SpillId)
{
    if (SpillId.IsNone())
    {
        return;
    }
    bWaterValveOpen = false;
    bBrushesRunning = false;
    bCleaningHeadsLowered = false;
    LastSpillId = SpillId;
    bSpillBoundaryIsolated = false;
    ActiveCleaningFault = ELBCleaningAMRFault::SpillDetected;
    AbortRoute(false);
    RaiseCommonFault(ELBSupportRobotFault::SpillDetected,
        FString::Printf(TEXT("Hazardous spill %s detected; route isolation and a human work order are required."), *SpillId.ToString()));
    OnSpillStateChanged.Broadcast(LastSpillId, bSpillBoundaryIsolated);
}

bool ALBCleaningAMR::ConfirmSpillBoundaryIsolated(FName SpillId)
{
    if (SpillId.IsNone() || SpillId != LastSpillId || ActiveCleaningFault != ELBCleaningAMRFault::SpillDetected)
    {
        return false;
    }
    bSpillBoundaryIsolated = true;
    OnSpillStateChanged.Broadcast(LastSpillId, bSpillBoundaryIsolated);
    return true;
}

bool ALBCleaningAMR::ReleaseSpillStopAfterHumanClearance(FName SpillId)
{
    if (SpillId.IsNone() || SpillId != LastSpillId || !bSpillBoundaryIsolated
        || ActiveCleaningFault != ELBCleaningAMRFault::SpillDetected
        || ActiveCommonFault != ELBSupportRobotFault::SpillDetected)
    {
        return false;
    }
    if (!ClearCommonFault())
    {
        return false;
    }
    ActiveCleaningFault = ELBCleaningAMRFault::None;
    OnSpillStateChanged.Broadcast(LastSpillId, bSpillBoundaryIsolated);
    return true;
}

void ALBCleaningAMR::ReportBrushJam(FName BrushId)
{
    ActiveCleaningFault = ELBCleaningAMRFault::BrushJam;
    bWaterValveOpen = false;
    bBrushesRunning = false;
    bCleaningHeadsLowered = false;
    RaiseCommonFault(ELBSupportRobotFault::BrushJam,
        FString::Printf(TEXT("Cleaning mechanism %s reported a jam."), *BrushId.ToString()));
}

bool ALBCleaningAMR::BeginDockService()
{
    if (!bDocked || (RobotState != ELBSupportRobotState::Docked && RobotState != ELBSupportRobotState::Charging))
    {
        return false;
    }
    bWaterValveOpen = false;
    bBrushesRunning = false;
    bCleaningHeadsLowered = false;
    SetRobotState(ELBSupportRobotState::Servicing);
    return true;
}

bool ALBCleaningAMR::CompleteDockService()
{
    if (!bDocked || RobotState != ELBSupportRobotState::Servicing)
    {
        return false;
    }
    CleanWaterLitres = CleanWaterCapacityLitres;
    RecoveryWaterLitres = 0.0f;
    HopperLoadLitres = 0.0f;
    ActiveCleaningFault = ELBCleaningAMRFault::None;
    ++ServiceCycles;
    SetRobotState(ELBSupportRobotState::Docked);
    OnCleaningResourcesChanged.Broadcast(CleanWaterLitres, RecoveryWaterLitres, HopperLoadLitres);
    return true;
}

FLBCleaningAMRSaveState ALBCleaningAMR::CaptureSaveState() const
{
    FLBCleaningAMRSaveState Saved;
    Saved.Common = CaptureCommonSaveState();
    Saved.CleaningFault = ActiveCleaningFault;
    Saved.CleanWaterLitres = CleanWaterLitres;
    Saved.RecoveryWaterLitres = RecoveryWaterLitres;
    Saved.HopperLoadLitres = HopperLoadLitres;
    Saved.FrontBrushWearPercent = FrontBrushWearPercent;
    Saved.SideBrushWearPercent = SideBrushWearPercent;
    Saved.ScrubDiscWearPercent = ScrubDiscWearPercent;
    Saved.SqueegeeWearPercent = SqueegeeWearPercent;
    Saved.LifetimeCoverageSquareMetres = LifetimeCoverageSquareMetres;
    Saved.ActiveCleaningZoneId = ActiveCleaningZoneId;
    Saved.LastSpillId = LastSpillId;
    Saved.bSensorCoverageCertified = bSensorCoverageCertified;
    Saved.bSpillBoundaryIsolated = bSpillBoundaryIsolated;
    return Saved;
}

bool ALBCleaningAMR::RestoreSaveState(const FLBCleaningAMRSaveState& SavedState)
{
    if (SavedState.Version != 1 || !RestoreCommonSaveState(SavedState.Common))
    {
        return false;
    }
    ActiveCleaningFault = SavedState.CleaningFault;
    CleanWaterLitres = FMath::Clamp(SavedState.CleanWaterLitres, 0.0f, CleanWaterCapacityLitres);
    RecoveryWaterLitres = FMath::Clamp(SavedState.RecoveryWaterLitres, 0.0f, RecoveryWaterCapacityLitres);
    HopperLoadLitres = FMath::Clamp(SavedState.HopperLoadLitres, 0.0f, HopperCapacityLitres);
    FrontBrushWearPercent = FMath::Clamp(SavedState.FrontBrushWearPercent, 0.0f, 100.0f);
    SideBrushWearPercent = FMath::Clamp(SavedState.SideBrushWearPercent, 0.0f, 100.0f);
    ScrubDiscWearPercent = FMath::Clamp(SavedState.ScrubDiscWearPercent, 0.0f, 100.0f);
    SqueegeeWearPercent = FMath::Clamp(SavedState.SqueegeeWearPercent, 0.0f, 100.0f);
    LifetimeCoverageSquareMetres = FMath::Max(0.0f, SavedState.LifetimeCoverageSquareMetres);
    ActiveCleaningZoneId = SavedState.ActiveCleaningZoneId;
    LastSpillId = SavedState.LastSpillId;
    bSensorCoverageCertified = false;
    bSpillBoundaryIsolated = SavedState.bSpillBoundaryIsolated;

    // Never resume water, brush or head motion from disk.
    bWaterValveOpen = false;
    bBrushesRunning = false;
    bCleaningHeadsLowered = false;
    CleaningDeploymentAlpha = 0.0f;
    ApplyCleaningPose(0.0f);
    OnCleaningResourcesChanged.Broadcast(CleanWaterLitres, RecoveryWaterLitres, HopperLoadLitres);
    return true;
}

bool ALBCleaningAMR::HasVariantTravelPermissives(FText& BlockingReason) const
{
    BlockingReason = FText::GetEmpty();
    if (!bSensorCoverageCertified)
    {
        BlockingReason = FText::FromString(TEXT("CR01 safety-sensor coverage is not certified."));
        return false;
    }
    if (ActiveCleaningFault != ELBCleaningAMRFault::None)
    {
        BlockingReason = FText::FromString(TEXT("A CR01 cleaning-system fault is active."));
        return false;
    }
    if (RobotState != ELBSupportRobotState::Cleaning && (bWaterValveOpen || bBrushesRunning || bCleaningHeadsLowered))
    {
        BlockingReason = FText::FromString(TEXT("Cleaning heads, brushes and water must be safely stowed for transit."));
        return false;
    }
    return true;
}

float ALBCleaningAMR::GetMaximumSpeedCentimetresPerSecond(ELBRouteSpeedClass SpeedClass, bool bEmergencyDispatch) const
{
    if (RobotState == ELBSupportRobotState::Cleaning)
    {
        return 70.0f;
    }
    switch (SpeedClass)
    {
    case ELBRouteSpeedClass::Docking:
        return 10.0f;
    case ELBRouteSpeedClass::MachineApproach:
        return 20.0f;
    case ELBRouteSpeedClass::OccupiedAisle:
        return 60.0f;
    case ELBRouteSpeedClass::EmergencyCertifiedClearRoute:
    case ELBRouteSpeedClass::NormalTransit:
    default:
        return 120.0f;
    }
}

void ALBCleaningAMR::OnEnteredSafeStop()
{
    bWaterValveOpen = false;
    bBrushesRunning = false;
    bCleaningHeadsLowered = false;
}

void ALBCleaningAMR::ApplyCleaningPose(float DeltaSeconds)
{
    const float Target = bCleaningHeadsLowered ? 1.0f : 0.0f;
    CleaningDeploymentAlpha = FMath::FInterpConstantTo(CleaningDeploymentAlpha, Target, DeltaSeconds, 1.5f);

    FrontBrushLiftPivot->SetRelativeLocation(FVector(63.5f, 0.0f, 16.5f + 8.0f * (1.0f - CleaningDeploymentAlpha)));
    SideBrushArmLeftPivot->SetRelativeRotation(FRotator(0.0f, -65.0f * CleaningDeploymentAlpha, 0.0f));
    SideBrushArmRightPivot->SetRelativeRotation(FRotator(0.0f, 65.0f * CleaningDeploymentAlpha, 0.0f));
    SideBrushLiftLeftPivot->SetRelativeLocation(FVector(7.0f, -17.0f, -5.0f + 4.5f * (1.0f - CleaningDeploymentAlpha)));
    SideBrushLiftRightPivot->SetRelativeLocation(FVector(7.0f, 17.0f, -5.0f + 4.5f * (1.0f - CleaningDeploymentAlpha)));
    ScrubDeckLiftPivot->SetRelativeLocation(FVector(4.0f, 0.0f, 18.5f + 12.0f * (1.0f - CleaningDeploymentAlpha)));
    SqueegeeLiftPivot->SetRelativeLocation(FVector(-69.0f, 0.0f, 16.5f + 10.0f * (1.0f - CleaningDeploymentAlpha)));

    if (USceneComponent* Pivot = FindPresentationPivot(TEXT("PVT_FrontBrushLift")))
    {
        Pivot->SetRelativeLocation(FVector(63.5f, 0.0f, 16.5f + 8.0f * (1.0f - CleaningDeploymentAlpha)));
    }
    if (USceneComponent* Pivot = FindPresentationPivot(TEXT("PVT_SideBrushArm_L")))
    {
        Pivot->SetRelativeRotation(FRotator(0.0f, -65.0f * CleaningDeploymentAlpha, 0.0f));
    }
    if (USceneComponent* Pivot = FindPresentationPivot(TEXT("PVT_SideBrushArm_R")))
    {
        Pivot->SetRelativeRotation(FRotator(0.0f, 65.0f * CleaningDeploymentAlpha, 0.0f));
    }
    if (USceneComponent* Pivot = FindPresentationPivot(TEXT("PVT_SideBrushLift_L")))
    {
        Pivot->SetRelativeLocation(FVector(7.0f, -17.0f, -5.0f + 4.5f * (1.0f - CleaningDeploymentAlpha)));
    }
    if (USceneComponent* Pivot = FindPresentationPivot(TEXT("PVT_SideBrushLift_R")))
    {
        Pivot->SetRelativeLocation(FVector(7.0f, 17.0f, -5.0f + 4.5f * (1.0f - CleaningDeploymentAlpha)));
    }
    if (USceneComponent* Pivot = FindPresentationPivot(TEXT("PVT_ScrubDeckLift")))
    {
        Pivot->SetRelativeLocation(FVector(4.0f, 0.0f, 18.5f + 12.0f * (1.0f - CleaningDeploymentAlpha)));
    }
    if (USceneComponent* Pivot = FindPresentationPivot(TEXT("PVT_SqueegeeLift")))
    {
        Pivot->SetRelativeLocation(FVector(-69.0f, 0.0f, 16.5f + 10.0f * (1.0f - CleaningDeploymentAlpha)));
    }

    if (bBrushesRunning && DeltaSeconds > 0.0f)
    {
        FrontBrushSpinPivot->AddLocalRotation(FRotator(1500.0f * DeltaSeconds, 0.0f, 0.0f));
        SideBrushSpinLeftPivot->AddLocalRotation(FRotator(0.0f, 1800.0f * DeltaSeconds, 0.0f));
        SideBrushSpinRightPivot->AddLocalRotation(FRotator(0.0f, -1800.0f * DeltaSeconds, 0.0f));
        ScrubDiscLeftPivot->AddLocalRotation(FRotator(0.0f, 1320.0f * DeltaSeconds, 0.0f));
        ScrubDiscRightPivot->AddLocalRotation(FRotator(0.0f, -1320.0f * DeltaSeconds, 0.0f));

        if (USceneComponent* Pivot = FindPresentationPivot(TEXT("PVT_FrontBrushSpin")))
        {
            Pivot->AddLocalRotation(FRotator(1500.0f * DeltaSeconds, 0.0f, 0.0f));
        }
        if (USceneComponent* Pivot = FindPresentationPivot(TEXT("PVT_SideBrushSpin_L")))
        {
            Pivot->AddLocalRotation(FRotator(0.0f, 1800.0f * DeltaSeconds, 0.0f));
        }
        if (USceneComponent* Pivot = FindPresentationPivot(TEXT("PVT_SideBrushSpin_R")))
        {
            Pivot->AddLocalRotation(FRotator(0.0f, -1800.0f * DeltaSeconds, 0.0f));
        }
        if (USceneComponent* Pivot = FindPresentationPivot(TEXT("PVT_ScrubDisc_L")))
        {
            Pivot->AddLocalRotation(FRotator(0.0f, 1320.0f * DeltaSeconds, 0.0f));
        }
        if (USceneComponent* Pivot = FindPresentationPivot(TEXT("PVT_ScrubDisc_R")))
        {
            Pivot->AddLocalRotation(FRotator(0.0f, -1320.0f * DeltaSeconds, 0.0f));
        }
    }
}

void ALBCleaningAMR::CachePresentationBindings()
{
    PresentationPivots.Reset();
    AActor* PresentationActor = PresentationComponent ? PresentationComponent->GetChildActor() : nullptr;
    if (!PresentationActor)
    {
        return;
    }

    TArray<USceneComponent*> SceneComponents;
    PresentationActor->GetComponents(SceneComponents);
    static const FName RequiredPivotNames[] = {
        TEXT("PVT_FrontBrushLift"), TEXT("PVT_FrontBrushSpin"),
        TEXT("PVT_SideBrushArm_L"), TEXT("PVT_SideBrushArm_R"),
        TEXT("PVT_SideBrushLift_L"), TEXT("PVT_SideBrushLift_R"),
        TEXT("PVT_SideBrushSpin_L"), TEXT("PVT_SideBrushSpin_R"),
        TEXT("PVT_ScrubDeckLift"), TEXT("PVT_ScrubDisc_L"), TEXT("PVT_ScrubDisc_R"),
        TEXT("PVT_SqueegeeLift")
    };
    for (USceneComponent* Component : SceneComponents)
    {
        if (!Component)
        {
            continue;
        }
        FString Name = Component->GetName();
        Name.RemoveFromEnd(TEXT("_0"));
        Name.RemoveFromEnd(TEXT("_GEN_VARIABLE"));
        for (const FName RequiredName : RequiredPivotNames)
        {
            if (Name.Contains(RequiredName.ToString()))
            {
                PresentationPivots.Add(RequiredName, Component);
                break;
            }
        }

        if (Name.Contains(TEXT("Collision_CR01_")) || Component->ComponentHasTag(TEXT("LB.CR01.Collision.Body")))
        {
            if (UPrimitiveComponent* Primitive = Cast<UPrimitiveComponent>(Component))
            {
                Primitive->SetCollisionEnabled(ECollisionEnabled::NoCollision);
                Primitive->SetGenerateOverlapEvents(false);
            }
        }
    }
}

USceneComponent* ALBCleaningAMR::FindPresentationPivot(FName ComponentName) const
{
    const TWeakObjectPtr<USceneComponent>* Found = PresentationPivots.Find(ComponentName);
    return Found ? Found->Get() : nullptr;
}

void ALBCleaningAMR::TickCleaningResources(float DistanceMovedCentimetres)
{
    if (DistanceMovedCentimetres <= 0.0f)
    {
        return;
    }
    const float AreaSquareMetres = (DistanceMovedCentimetres / 100.0f) * CleaningSwathMetres;
    LifetimeCoverageSquareMetres += AreaSquareMetres;

    // Gameplay-tunable consumption rates; authoritative capacities and swath are
    // fixed by the Pro pack, while these rates remain balancing parameters.
    const float WaterUsed = AreaSquareMetres * 0.10f;
    CleanWaterLitres = FMath::Max(0.0f, CleanWaterLitres - WaterUsed);
    RecoveryWaterLitres = FMath::Min(RecoveryWaterCapacityLitres, RecoveryWaterLitres + WaterUsed * 0.85f);
    HopperLoadLitres = FMath::Min(HopperCapacityLitres, HopperLoadLitres + AreaSquareMetres * 0.015f);
    FrontBrushWearPercent = FMath::Max(0.0f, FrontBrushWearPercent - AreaSquareMetres * 0.0008f);
    SideBrushWearPercent = FMath::Max(0.0f, SideBrushWearPercent - AreaSquareMetres * 0.0010f);
    ScrubDiscWearPercent = FMath::Max(0.0f, ScrubDiscWearPercent - AreaSquareMetres * 0.0007f);
    SqueegeeWearPercent = FMath::Max(0.0f, SqueegeeWearPercent - AreaSquareMetres * 0.0009f);
    OnCleaningResourcesChanged.Broadcast(CleanWaterLitres, RecoveryWaterLitres, HopperLoadLitres);

    if (CleanWaterLitres <= 0.0f)
    {
        ActiveCleaningFault = ELBCleaningAMRFault::CleanWaterEmpty;
        StopCleaningTask();
        RaiseCommonFault(ELBSupportRobotFault::TankFull, TEXT("CR01 clean-water tank is empty."));
    }
    else if (RecoveryWaterLitres >= RecoveryWaterCapacityLitres || HopperLoadLitres >= HopperCapacityLitres)
    {
        ActiveCleaningFault = ELBCleaningAMRFault::TankFull;
        StopCleaningTask();
        RaiseCommonFault(ELBSupportRobotFault::TankFull, TEXT("CR01 recovery tank or debris hopper is full."));
    }
}
