#include "LBCleaningRobotRuntimeComponentV002.h"

namespace
{
    FLBAnchorSpecV002 CRAnchor(FName Name, const FVector& RelativeLocation)
    {
        FLBAnchorSpecV002 Spec;
        Spec.Name = Name;
        Spec.RelativeLocationCentimetres = RelativeLocation;
        return Spec;
    }

    FLBAnchorSpecV002 CRChildAnchor(FName Name, FName ParentName,
        const FVector& RelativeLocation)
    {
        FLBAnchorSpecV002 Spec = CRAnchor(Name, RelativeLocation);
        Spec.ParentName = ParentName;
        return Spec;
    }
}

ULBCleaningRobotRuntimeComponentV002::ULBCleaningRobotRuntimeComponentV002()
{
    VariantId = TEXT("LB-CR01");
}

void ULBCleaningRobotRuntimeComponentV002::AppendAnchorContract(
    TArray<FLBAnchorSpecV002>& InOutSpecs) const
{
    Super::AppendAnchorContract(InOutSpecs);
    InOutSpecs.Append({
        CRChildAnchor(TEXT("CR01PayloadFrame"), TEXT("Attach_CR01_Payload"), FVector(0.0, 0.0, -38.5)),
        CRChildAnchor(TEXT("PVT_FrontBrushLift"), TEXT("CR01PayloadFrame"), FVector(63.5, 0.0, 16.5)),
        CRChildAnchor(TEXT("PVT_FrontBrushSpin"), TEXT("PVT_FrontBrushLift"), FVector(0.0, 0.0, -4.0)),
        CRChildAnchor(TEXT("PVT_SideBrushArm_L"), TEXT("CR01PayloadFrame"), FVector(45.0, -33.0, 15.5)),
        CRChildAnchor(TEXT("PVT_SideBrushArm_R"), TEXT("CR01PayloadFrame"), FVector(45.0, 33.0, 15.5)),
        CRChildAnchor(TEXT("PVT_SideBrushLift_L"), TEXT("PVT_SideBrushArm_L"), FVector(7.0, -17.0, -5.0)),
        CRChildAnchor(TEXT("PVT_SideBrushLift_R"), TEXT("PVT_SideBrushArm_R"), FVector(7.0, 17.0, -5.0)),
        CRChildAnchor(TEXT("PVT_SideBrushSpin_L"), TEXT("PVT_SideBrushLift_L"), FVector(0.0, 0.0, -2.5)),
        CRChildAnchor(TEXT("PVT_SideBrushSpin_R"), TEXT("PVT_SideBrushLift_R"), FVector(0.0, 0.0, -2.5)),
        CRChildAnchor(TEXT("PVT_ScrubDeckLift"), TEXT("CR01PayloadFrame"), FVector(4.0, 0.0, 18.5)),
        CRChildAnchor(TEXT("PVT_ScrubDisc_L"), TEXT("PVT_ScrubDeckLift"), FVector(0.0, -17.5, -11.0)),
        CRChildAnchor(TEXT("PVT_ScrubDisc_R"), TEXT("PVT_ScrubDeckLift"), FVector(0.0, 17.5, -11.0)),
        CRChildAnchor(TEXT("PVT_SqueegeeLift"), TEXT("CR01PayloadFrame"), FVector(-69.0, 0.0, 16.5)),
        CRChildAnchor(TEXT("PVT_SqueegeeYaw"), TEXT("PVT_SqueegeeLift"), FVector(0.0, 0.0, -6.5)),
        CRChildAnchor(TEXT("PVT_HopperSlide"), TEXT("CR01PayloadFrame"), FVector(38.0, 0.0, 28.0)),
        CRChildAnchor(TEXT("PVT_HopperLid"), TEXT("CR01PayloadFrame"), FVector(28.0, 0.0, 52.0)),
        CRChildAnchor(TEXT("PVT_Door_Left"), TEXT("CR01PayloadFrame"), FVector(-8.0, -45.5, 69.0)),
        CRChildAnchor(TEXT("PVT_Door_Right"), TEXT("CR01PayloadFrame"), FVector(-8.0, 45.5, 69.0)),
        CRChildAnchor(TEXT("PVT_Door_Rear"), TEXT("CR01PayloadFrame"), FVector(-62.0, 0.0, 72.0)),
        CRChildAnchor(TEXT("PVT_FilterLid"), TEXT("CR01PayloadFrame"), FVector(-43.0, -26.0, 76.0))
    });
    // Dock water/waste pivots M28-M30 belong to the dock authority actor, not this component.
}

bool ULBCleaningRobotRuntimeComponentV002::RequestSensorCoverageCertification(FName EvidenceId)
{
    if (EvidenceId.IsNone() || HasTrustedRouteGrant() || !ActiveTaskId.IsNone())
    {
        return false;
    }
    FString Failure;
    ULBSupportRobotAuthorityRegistryV002* Registry = GetAuthorityRegistry();
    bSensorCoverageProvedThisSession = Registry != nullptr
        && Registry->ValidateSensorCoverage(UnitId, VariantId,
            EvidenceId, GetOwner(), Failure);
    ActiveSensorCoverageEvidenceId = bSensorCoverageProvedThisSession
        ? EvidenceId : NAME_None;
    if (!bSensorCoverageProvedThisSession)
    {
        ActiveCleaningFault = ELBCleaningRobotFaultV002::SensorDirty;
        RaiseCommonFault(ELBSupportRobotCommonFaultV002::VariantInterlockOpen, Failure);
    }
    return bSensorCoverageProvedThisSession;
}

bool ULBCleaningRobotRuntimeComponentV002::StartCleaningTask(FName TaskId,
    FName CleaningZoneId, FName AuthorityEvidenceId)
{
    if (TaskId.IsNone() || CleaningZoneId.IsNone() || !HasTrustedRouteGrant()
        || !ActiveTaskId.IsNone() || ActiveCleaningFault != ELBCleaningRobotFaultV002::None
        || !bSensorCoverageProvedThisSession
        || RecoveryWaterLitres >= RecoveryWaterCapacityLitres
        || HopperLoadLitres >= HopperCapacityLitres || FrontBrushWearPercent <= 5.0
        || SideBrushWearPercent <= 5.0)
    {
        return false;
    }

    FString Failure;
    ULBSupportRobotAuthorityRegistryV002* Registry = GetAuthorityRegistry();
    if (Registry == nullptr || !Registry->ValidateVariantTaskAuthority(UnitId, VariantId,
        TaskId, CleaningZoneId, AuthorityEvidenceId, GetOwner(), Failure))
    {
        return false;
    }

    FLBTrustedCleaningTaskGrantV002 NewGrant;
    if (!Registry->IssueCleaningTaskGrant(UnitId, TaskId, CleaningZoneId,
        AuthorityEvidenceId, GetOwner(), NewGrant, Failure))
    {
        return false;
    }
    const bool bWetScrub = NewGrant.Mode == ELBCleaningModeV002::WetScrub;
    if ((bWetScrub && (CleanWaterLitres <= 0.0 || ScrubDiscWearPercent <= 5.0
        || SqueegeeWearPercent <= 5.0)))
    {
        Registry->RevokeCleaningTaskGrant(NewGrant.GrantId, UnitId);
        return false;
    }

    ActiveTaskId = TaskId;
    ActiveCleaningZoneId = CleaningZoneId;
    ActiveTaskAuthorityEvidenceId = AuthorityEvidenceId;
    ActiveCleaningTaskGrant = NewGrant;
    LastCleaningProcessSequence = 0;
    bWetScrubActive = bWetScrub;
    bWaterValveCommandedOpen = bWetScrub;
    bBrushesCommandedRunning = true;
    bCleaningHeadsCommandedLowered = true;
    SetOperatingState(ELBSupportRobotOperatingStateV002::Working);
    return true;
}

void ULBCleaningRobotRuntimeComponentV002::StopCleaningTask()
{
    CommandAllCleaningMechanismsSafe();
    RevokeActiveCleaningTaskGrant();
    ActiveTaskId = NAME_None;
    ActiveCleaningZoneId = NAME_None;
    ActiveTaskAuthorityEvidenceId = NAME_None;
    bWetScrubActive = false;
    if (HasTrustedRouteGrant())
    {
        SetOperatingState(ELBSupportRobotOperatingStateV002::Navigating);
    }
    else
    {
        SetOperatingState(ELBSupportRobotOperatingStateV002::Stopped);
    }
}

void ULBCleaningRobotRuntimeComponentV002::ReportHazardousSpill(FName SpillId)
{
    if (SpillId.IsNone())
    {
        return;
    }
    LastSpillId = SpillId;
    ActiveCleaningFault = ELBCleaningRobotFaultV002::SpillDetected;
    CommandAllCleaningMechanismsSafe();
    RevokeActiveCleaningTaskGrant();
    ActiveTaskId = NAME_None;
    ActiveCleaningZoneId = NAME_None;
    RaiseCommonFault(ELBSupportRobotCommonFaultV002::LowTractionOrSpill,
        FString::Printf(TEXT("CR01 hazardous spill %s requires trusted human clearance."),
            *SpillId.ToString()));
}

void ULBCleaningRobotRuntimeComponentV002::ReportCleaningFault(
    ELBCleaningRobotFaultV002 Fault, FName SourceId, const FString& Detail)
{
    if (Fault == ELBCleaningRobotFaultV002::None)
    {
        return;
    }
    if (static_cast<uint8>(Fault)
        > static_cast<uint8>(ELBCleaningRobotFaultV002::ProcessAuthorityFault))
    {
        RaiseCommonFault(ELBSupportRobotCommonFaultV002::VariantInterlockOpen,
            TEXT("CR01 received an out-of-contract fault identifier and safe-stopped."));
        return;
    }
    ActiveCleaningFault = Fault;
    CommandAllCleaningMechanismsSafe();
    RevokeActiveCleaningTaskGrant();
    ActiveTaskId = NAME_None;
    ActiveCleaningZoneId = NAME_None;
    RaiseCommonFault(ELBSupportRobotCommonFaultV002::VariantInterlockOpen,
        FString::Printf(TEXT("CR01 %s: %s"), *SourceId.ToString(), *Detail));
}

bool ULBCleaningRobotRuntimeComponentV002::ApplyTrustedDockServiceResult(
    double NewCleanWaterLitres, double NewRecoveryWaterLitres, double NewHopperLoadLitres)
{
    FString DockFailure;
    if (!RevalidateActiveDockProofV002(DockFailure) || !FMath::IsFinite(NewCleanWaterLitres)
        || !FMath::IsFinite(NewRecoveryWaterLitres) || !FMath::IsFinite(NewHopperLoadLitres)
        || NewCleanWaterLitres < 0.0 || NewCleanWaterLitres > CleanWaterCapacityLitres
        || NewRecoveryWaterLitres < 0.0 || NewRecoveryWaterLitres > RecoveryWaterCapacityLitres
        || NewHopperLoadLitres < 0.0 || NewHopperLoadLitres > HopperCapacityLitres)
    {
        return false;
    }
    CleanWaterLitres = NewCleanWaterLitres;
    RecoveryWaterLitres = NewRecoveryWaterLitres;
    HopperLoadLitres = NewHopperLoadLitres;
    ++ServiceCycles;
    return true;
}

bool ULBCleaningRobotRuntimeComponentV002::ApplyTrustedConsumableServiceResult(
    double NewFrontBrushWearPercent, double NewSideBrushWearPercent,
    double NewScrubDiscWearPercent, double NewSqueegeeWearPercent,
    FName ServiceEvidenceId)
{
    if (HasTrustedRouteGrant() || !ActiveTaskId.IsNone()
        || !FMath::IsFinite(NewFrontBrushWearPercent)
        || !FMath::IsFinite(NewSideBrushWearPercent)
        || !FMath::IsFinite(NewScrubDiscWearPercent)
        || !FMath::IsFinite(NewSqueegeeWearPercent)
        || NewFrontBrushWearPercent < 0.0 || NewFrontBrushWearPercent > 100.0
        || NewSideBrushWearPercent < 0.0 || NewSideBrushWearPercent > 100.0
        || NewScrubDiscWearPercent < 0.0 || NewScrubDiscWearPercent > 100.0
        || NewSqueegeeWearPercent < 0.0 || NewSqueegeeWearPercent > 100.0
        || !ValidateTrustedCommissioningEvidence(TEXT("CR01_CONSUMABLE_SERVICE"),
            ServiceEvidenceId))
    {
        return false;
    }
    FrontBrushWearPercent = NewFrontBrushWearPercent;
    SideBrushWearPercent = NewSideBrushWearPercent;
    ScrubDiscWearPercent = NewScrubDiscWearPercent;
    SqueegeeWearPercent = NewSqueegeeWearPercent;
    ++ServiceCycles;
    return true;
}

FLBCleaningRobotSafeSaveV002 ULBCleaningRobotRuntimeComponentV002::CaptureCleaningSafeSave() const
{
    FLBCleaningRobotSafeSaveV002 Saved;
    Saved.Common = CaptureSafeSaveState();
    Saved.PersistedCleaningFault = ActiveCleaningFault;
    Saved.CleanWaterLitres = CleanWaterLitres;
    Saved.RecoveryWaterLitres = RecoveryWaterLitres;
    Saved.HopperLoadLitres = HopperLoadLitres;
    Saved.FrontBrushWearPercent = FrontBrushWearPercent;
    Saved.SideBrushWearPercent = SideBrushWearPercent;
    Saved.ScrubDiscWearPercent = ScrubDiscWearPercent;
    Saved.SqueegeeWearPercent = SqueegeeWearPercent;
    Saved.LifetimeCoverageSquareMetres = LifetimeCoverageSquareMetres;
    Saved.LastSpillId = LastSpillId;
    return Saved;
}

bool ULBCleaningRobotRuntimeComponentV002::RestoreCleaningSafeStopped(
    const FLBCleaningRobotSafeSaveV002& SavedState)
{
    if (SavedState.Version != 2 || !FMath::IsFinite(SavedState.CleanWaterLitres)
        || !FMath::IsFinite(SavedState.RecoveryWaterLitres)
        || !FMath::IsFinite(SavedState.HopperLoadLitres)
        || !FMath::IsFinite(SavedState.FrontBrushWearPercent)
        || !FMath::IsFinite(SavedState.SideBrushWearPercent)
        || !FMath::IsFinite(SavedState.ScrubDiscWearPercent)
        || !FMath::IsFinite(SavedState.SqueegeeWearPercent)
        || !FMath::IsFinite(SavedState.LifetimeCoverageSquareMetres)
        || static_cast<uint8>(SavedState.PersistedCleaningFault)
            > static_cast<uint8>(ELBCleaningRobotFaultV002::ProcessAuthorityFault)
        || SavedState.CleanWaterLitres < 0.0
        || SavedState.CleanWaterLitres > CleanWaterCapacityLitres
        || SavedState.RecoveryWaterLitres < 0.0
        || SavedState.RecoveryWaterLitres > RecoveryWaterCapacityLitres
        || SavedState.HopperLoadLitres < 0.0
        || SavedState.HopperLoadLitres > HopperCapacityLitres
        || SavedState.FrontBrushWearPercent < 0.0
        || SavedState.FrontBrushWearPercent > 100.0
        || SavedState.SideBrushWearPercent < 0.0
        || SavedState.SideBrushWearPercent > 100.0
        || SavedState.ScrubDiscWearPercent < 0.0
        || SavedState.ScrubDiscWearPercent > 100.0
        || SavedState.SqueegeeWearPercent < 0.0
        || SavedState.SqueegeeWearPercent > 100.0
        || SavedState.LifetimeCoverageSquareMetres < 0.0
        || !RestoreSafeStopped(SavedState.Common))
    {
        return false;
    }

    ActiveCleaningFault = SavedState.PersistedCleaningFault;
    CleanWaterLitres = SavedState.CleanWaterLitres;
    RecoveryWaterLitres = SavedState.RecoveryWaterLitres;
    HopperLoadLitres = SavedState.HopperLoadLitres;
    FrontBrushWearPercent = SavedState.FrontBrushWearPercent;
    SideBrushWearPercent = SavedState.SideBrushWearPercent;
    ScrubDiscWearPercent = SavedState.ScrubDiscWearPercent;
    SqueegeeWearPercent = SavedState.SqueegeeWearPercent;
    LifetimeCoverageSquareMetres = SavedState.LifetimeCoverageSquareMetres;
    LastSpillId = SavedState.LastSpillId;
    bSensorCoverageProvedThisSession = false;
    ActiveSensorCoverageEvidenceId = NAME_None;
    ActiveTaskAuthorityEvidenceId = NAME_None;
    ActiveCleaningTaskGrant = FLBTrustedCleaningTaskGrantV002();
    LastCleaningProcessSequence = 0;
    CommandAllCleaningMechanismsSafe();
    ActiveTaskId = NAME_None;
    ActiveCleaningZoneId = NAME_None;
    return true;
}

bool ULBCleaningRobotRuntimeComponentV002::ValidateVariantForCertification(
    FString& OutFailure) const
{
    if (!bSensorCoverageProvedThisSession)
    {
        OutFailure = TEXT("CR01 sensor coverage has no trusted session proof.");
        return false;
    }
    if (ActiveCleaningFault != ELBCleaningRobotFaultV002::None)
    {
        OutFailure = TEXT("A CR01 cleaning fault is active.");
        return false;
    }
    OutFailure.Reset();
    return true;
}

bool ULBCleaningRobotRuntimeComponentV002::ValidateVariantTravelPermissives(
    FString& OutFailure) const
{
    if (!bSensorCoverageProvedThisSession)
    {
        OutFailure = TEXT("CR01 sensor coverage has no trusted session proof.");
        return false;
    }
    if (ActiveCleaningFault != ELBCleaningRobotFaultV002::None)
    {
        OutFailure = TEXT("A CR01 cleaning fault is active.");
        return false;
    }
    const bool bActivelyCleaning = OperatingState == ELBSupportRobotOperatingStateV002::Working
        && !ActiveTaskId.IsNone();
    if (!bActivelyCleaning && (bWaterValveCommandedOpen || bBrushesCommandedRunning
        || bCleaningHeadsCommandedLowered))
    {
        OutFailure = TEXT("CR01 cleaning mechanisms are not commanded safe for travel.");
        return false;
    }
    OutFailure.Reset();
    return true;
}

bool ULBCleaningRobotRuntimeComponentV002::RefreshVariantDynamicInterlocksV002(
    FString& OutFailure)
{
    ULBSupportRobotAuthorityRegistryV002* Registry = GetAuthorityRegistry();
    if (Registry == nullptr || !bSensorCoverageProvedThisSession
        || ActiveSensorCoverageEvidenceId.IsNone()
        || !Registry->ValidateSensorCoverage(UnitId, VariantId,
            ActiveSensorCoverageEvidenceId, GetOwner(), OutFailure))
    {
        bSensorCoverageProvedThisSession = false;
        ActiveSensorCoverageEvidenceId = NAME_None;
        if (OutFailure.IsEmpty())
        {
            OutFailure = TEXT("CR01 sensor coverage proof is absent or no longer current.");
        }
        return false;
    }

    if (!ActiveTaskId.IsNone())
    {
        if (ActiveCleaningZoneId.IsNone() || ActiveTaskAuthorityEvidenceId.IsNone()
            || !Registry->ValidateVariantTaskAuthority(UnitId, VariantId, ActiveTaskId,
                ActiveCleaningZoneId, ActiveTaskAuthorityEvidenceId, GetOwner(), OutFailure)
            || !ActiveCleaningTaskGrant.IsComplete()
            || !Registry->RevalidateCleaningTaskGrant(
                ActiveCleaningTaskGrant, GetOwner(), OutFailure))
        {
            if (OutFailure.IsEmpty())
            {
                OutFailure = TEXT("CR01 cleaning-task authority is absent or no longer current.");
            }
            return false;
        }
    }
    OutFailure.Reset();
    return true;
}

void ULBCleaningRobotRuntimeComponentV002::TickVariantProcessV002(double DeltaSeconds)
{
    if (OperatingState != ELBSupportRobotOperatingStateV002::Working
        || ActiveTaskId.IsNone())
    {
        return;
    }

    ULBSupportRobotAuthorityRegistryV002* Registry = GetAuthorityRegistry();
    FLBTrustedCleaningProcessSampleV002 Sample;
    FString Failure;
    const double SpeedMetresPerSecond =
        GetCurrentCommandedSpeedCentimetresPerSecondV002() / 100.0;
    const double MaximumCoverageDelta =
        SpeedMetresPerSecond * DeltaSeconds * CleaningSwathMetres + 0.01;
    if (Registry == nullptr || !Registry->SampleCleaningProcess(
        ActiveCleaningTaskGrant, GetOwner(), DeltaSeconds, Sample, Failure)
        || Sample.Sequence <= LastCleaningProcessSequence
        || Sample.CoverageDeltaSquareMetres > MaximumCoverageDelta
        || !FMath::IsFinite(LifetimeCoverageSquareMetres
            + Sample.CoverageDeltaSquareMetres)
        || Sample.CleanWaterConsumedLitres > CleanWaterLitres
        || RecoveryWaterLitres + Sample.RecoveryWaterAddedLitres > RecoveryWaterCapacityLitres
        || HopperLoadLitres + Sample.HopperLoadAddedLitres > HopperCapacityLitres
        || Sample.FrontBrushWearConsumedPercent > FrontBrushWearPercent
        || Sample.SideBrushWearConsumedPercent > SideBrushWearPercent
        || Sample.ScrubDiscWearConsumedPercent > ScrubDiscWearPercent
        || Sample.SqueegeeWearConsumedPercent > SqueegeeWearPercent)
    {
        ActiveCleaningFault = ELBCleaningRobotFaultV002::ProcessAuthorityFault;
        CommandAllCleaningMechanismsSafe();
        RevokeActiveCleaningTaskGrant();
        ActiveTaskId = NAME_None;
        ActiveCleaningZoneId = NAME_None;
        ActiveTaskAuthorityEvidenceId = NAME_None;
        RaiseCommonFault(ELBSupportRobotCommonFaultV002::VariantInterlockOpen,
            Failure.IsEmpty() ? TEXT("CR01 cleaning-process proof was invalid or implausible.") : Failure);
        return;
    }

    LastCleaningProcessSequence = Sample.Sequence;
    CleanWaterLitres -= Sample.CleanWaterConsumedLitres;
    RecoveryWaterLitres += Sample.RecoveryWaterAddedLitres;
    HopperLoadLitres += Sample.HopperLoadAddedLitres;
    FrontBrushWearPercent -= Sample.FrontBrushWearConsumedPercent;
    SideBrushWearPercent -= Sample.SideBrushWearConsumedPercent;
    ScrubDiscWearPercent -= Sample.ScrubDiscWearConsumedPercent;
    SqueegeeWearPercent -= Sample.SqueegeeWearConsumedPercent;
    LifetimeCoverageSquareMetres += Sample.CoverageDeltaSquareMetres;
}

void ULBCleaningRobotRuntimeComponentV002::OnSafeStopV002()
{
    CommandAllCleaningMechanismsSafe();
    RevokeActiveCleaningTaskGrant();
    bSensorCoverageProvedThisSession = false;
    ActiveSensorCoverageEvidenceId = NAME_None;
    ActiveTaskAuthorityEvidenceId = NAME_None;
    ActiveTaskId = NAME_None;
    ActiveCleaningZoneId = NAME_None;
}

void ULBCleaningRobotRuntimeComponentV002::OnRouteFinishedSafelyV002()
{
    StopCleaningTask();
    Super::OnRouteFinishedSafelyV002();
}

void ULBCleaningRobotRuntimeComponentV002::OnSafeStoppedRestoreV002()
{
    Super::OnSafeStoppedRestoreV002();
    bSensorCoverageProvedThisSession = false;
    ActiveSensorCoverageEvidenceId = NAME_None;
    ActiveTaskAuthorityEvidenceId = NAME_None;
    ActiveCleaningTaskGrant = FLBTrustedCleaningTaskGrantV002();
    LastCleaningProcessSequence = 0;
    CommandAllCleaningMechanismsSafe();
    ActiveCleaningZoneId = NAME_None;
}

FName ULBCleaningRobotRuntimeComponentV002::GetActiveVariantFaultIdV002() const
{
    if (ActiveCleaningFault == ELBCleaningRobotFaultV002::None)
    {
        return NAME_None;
    }
    const UEnum* Enum = StaticEnum<ELBCleaningRobotFaultV002>();
    return Enum != nullptr ? FName(*Enum->GetNameStringByValue(
        static_cast<int64>(ActiveCleaningFault))) : TEXT("CR01_UNKNOWN_FAULT");
}

bool ULBCleaningRobotRuntimeComponentV002::CanCommitVariantFaultClearV002(
    FString& OutFailure) const
{
    OutFailure.Reset();
    return true;
}

void ULBCleaningRobotRuntimeComponentV002::CommitVariantFaultClearV002()
{
    ActiveCleaningFault = ELBCleaningRobotFaultV002::None;
    bSensorCoverageProvedThisSession = false;
    ActiveSensorCoverageEvidenceId = NAME_None;
    ActiveTaskAuthorityEvidenceId = NAME_None;
    CommandAllCleaningMechanismsSafe();
}

double ULBCleaningRobotRuntimeComponentV002::GetMaximumSpeedCentimetresPerSecondV002(
    ELBRouteSpeedClassV002 SpeedClass, bool bEmergencyDispatch) const
{
    double RouteMaximum = 120.0;
    switch (SpeedClass)
    {
    case ELBRouteSpeedClassV002::Docking: RouteMaximum = 10.0; break;
    case ELBRouteSpeedClassV002::MachineApproach: RouteMaximum = 20.0; break;
    case ELBRouteSpeedClassV002::OccupiedAisle: RouteMaximum = 60.0; break;
    case ELBRouteSpeedClassV002::EmergencyCertifiedClearRoute:
    case ELBRouteSpeedClassV002::NormalTransit:
    default: break;
    }
    return OperatingState == ELBSupportRobotOperatingStateV002::Working && !ActiveTaskId.IsNone()
        ? FMath::Min(70.0, RouteMaximum) : RouteMaximum;
}

void ULBCleaningRobotRuntimeComponentV002::CommandAllCleaningMechanismsSafe()
{
    bWaterValveCommandedOpen = false;
    bBrushesCommandedRunning = false;
    bCleaningHeadsCommandedLowered = false;
    bWetScrubActive = false;
}

void ULBCleaningRobotRuntimeComponentV002::RevokeActiveCleaningTaskGrant()
{
    if (ActiveCleaningTaskGrant.GrantId.IsValid())
    {
        if (ULBSupportRobotAuthorityRegistryV002* Registry = GetAuthorityRegistry())
        {
            Registry->RevokeCleaningTaskGrant(ActiveCleaningTaskGrant.GrantId, UnitId);
        }
    }
    ActiveCleaningTaskGrant = FLBTrustedCleaningTaskGrantV002();
    LastCleaningProcessSequence = 0;
}
