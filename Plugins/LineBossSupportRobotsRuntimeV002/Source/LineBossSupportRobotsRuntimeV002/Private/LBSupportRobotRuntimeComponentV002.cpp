#include "LBSupportRobotRuntimeComponentV002.h"

#include "Components/SceneComponent.h"
#include "Engine/World.h"
#include "GameFramework/Actor.h"

namespace
{
    FLBAnchorSpecV002 MakeAnchor(FName Name, FName ParentName, const FVector& RelativeLocation,
        double YawDegrees = 0.0)
    {
        FLBAnchorSpecV002 Spec;
        Spec.Name = Name;
        Spec.ParentName = ParentName;
        Spec.RelativeLocationCentimetres = RelativeLocation;
        Spec.RelativeRotationDegrees = FRotator(0.0, YawDegrees, 0.0);
        return Spec;
    }
}

ULBSupportRobotRuntimeComponentV002::ULBSupportRobotRuntimeComponentV002()
{
    PrimaryComponentTick.bCanEverTick = true;
    PrimaryComponentTick.bStartWithTickEnabled = true;
}

void ULBSupportRobotRuntimeComponentV002::BeginPlay()
{
    Super::BeginPlay();
    CurrentCommandedSpeedCentimetresPerSecond = 0.0;
    if (VariantId != GetExpectedVariantIdV002())
    {
        RaiseCommonFault(ELBSupportRobotCommonFaultV002::VariantInterlockOpen,
            TEXT("The serialized robot variant does not match its native runtime class."));
    }
    ResolveAndValidateAnchors();
    if (!bAnchorContractValid)
    {
        RaiseCommonFault(ELBSupportRobotCommonFaultV002::AnchorContractInvalid,
            TEXT("The owner does not satisfy the pack-authoritative v002 anchor contract."));
    }
}

void ULBSupportRobotRuntimeComponentV002::EndPlay(const EEndPlayReason::Type EndPlayReason)
{
    OnSafeStopV002();
    ClearAllTransientAuthorityV002();
    Super::EndPlay(EndPlayReason);
}

void ULBSupportRobotRuntimeComponentV002::TickComponent(float DeltaTime, ELevelTick TickType,
    FActorComponentTickFunction* ThisTickFunction)
{
    Super::TickComponent(DeltaTime, TickType, ThisTickFunction);
    if (!FMath::IsFinite(DeltaTime) || DeltaTime <= 0.0f)
    {
        return;
    }

    if (HasTrustedRouteGrant())
    {
        TickTrustedRoute(static_cast<double>(DeltaTime));
    }
    if (HasTrustedDockProof())
    {
        TickTrustedDock(static_cast<double>(DeltaTime));
    }
    TickVariantProcessV002(static_cast<double>(DeltaTime));
    if (CommissioningState != ELBSupportRobotCommissioningStateV002::Mothballed
        && CommissioningState != ELBSupportRobotCommissioningStateV002::RepairRequired)
    {
        OperatingHours += static_cast<double>(DeltaTime) / 3600.0;
    }
}

bool ULBSupportRobotRuntimeComponentV002::ConfigureIdentity(FName NewUnitId, FName NewVariantId)
{
    if (NewUnitId.IsNone() || NewVariantId.IsNone() || HasTrustedRouteGrant()
        || HasTrustedDockProof() || !ActiveTaskId.IsNone()
        || NewVariantId != GetExpectedVariantIdV002())
    {
        return false;
    }
    if (!UnitId.IsNone() && UnitId != NewUnitId)
    {
        return false;
    }
    if (!VariantId.IsNone() && VariantId != NewVariantId)
    {
        return false;
    }
    UnitId = NewUnitId;
    VariantId = NewVariantId;
    return true;
}

void ULBSupportRobotRuntimeComponentV002::AppendAnchorContract(TArray<FLBAnchorSpecV002>& InOutSpecs) const
{
    InOutSpecs.Append({
        MakeAnchor(TEXT("PayloadInterface"), NAME_None, FVector(0.0, 0.0, 38.5)),
        MakeAnchor(TEXT("Attach_CR01_Payload"), TEXT("PayloadInterface"), FVector::ZeroVector),
        MakeAnchor(TEXT("Attach_MR01_Payload"), TEXT("PayloadInterface"), FVector::ZeroVector),
        MakeAnchor(TEXT("Attach_ConfigSpecificService"), TEXT("PayloadInterface"), FVector::ZeroVector),
        MakeAnchor(TEXT("Attach_DriveWheel_L"), NAME_None, FVector(-10.0, -40.5, 17.0)),
        MakeAnchor(TEXT("Attach_DriveWheel_R"), NAME_None, FVector(-10.0, 40.5, 17.0)),
        MakeAnchor(TEXT("Attach_Suspension_Front"), NAME_None, FVector(47.0, 0.0, 16.0)),
        MakeAnchor(TEXT("Attach_CasterRoll_Front"), TEXT("Attach_Suspension_Front"), FVector(0.0, 0.0, -8.0)),
        MakeAnchor(TEXT("Attach_Suspension_Rear"), NAME_None, FVector(-53.0, 0.0, 16.0)),
        MakeAnchor(TEXT("Attach_CasterRoll_Rear"), TEXT("Attach_Suspension_Rear"), FVector(0.0, 0.0, -8.0)),
        MakeAnchor(TEXT("Attach_Sensor_Front"), NAME_None, FVector(66.0, 0.0, 50.0)),
        MakeAnchor(TEXT("Attach_Sensor_Rear"), NAME_None, FVector(-66.0, 0.0, 50.0), 180.0),
        MakeAnchor(TEXT("Attach_Sensor_Left"), NAME_None, FVector(0.0, -41.0, 50.0), -90.0),
        MakeAnchor(TEXT("Attach_Sensor_Right"), NAME_None, FVector(0.0, 41.0, 50.0), 90.0),
        MakeAnchor(TEXT("Attach_DockDatum"), NAME_None, FVector(-73.5, 0.0, 31.0), 180.0),
        MakeAnchor(TEXT("Attach_ChargeContact_L"), NAME_None, FVector(-73.5, -12.0, 34.0), 180.0),
        MakeAnchor(TEXT("Attach_ChargeContact_R"), NAME_None, FVector(-73.5, 12.0, 34.0), 180.0),
        MakeAnchor(TEXT("Attach_NetworkContact"), NAME_None, FVector(-73.5, 0.0, 39.0), 180.0),
        MakeAnchor(TEXT("Attach_TowFront"), NAME_None, FVector(73.5, 0.0, 18.0)),
        MakeAnchor(TEXT("Attach_TowRear"), NAME_None, FVector(-73.5, 0.0, 18.0), 180.0),
        MakeAnchor(TEXT("Attach_AudioDrive_L"), NAME_None, FVector(-10.0, -40.5, 17.0)),
        MakeAnchor(TEXT("Attach_AudioDrive_R"), NAME_None, FVector(-10.0, 40.5, 17.0)),
        // CR/RP01 authority remains the v002 shared decision; MR's conflicting 950 mm row stays quarantined.
        MakeAnchor(TEXT("Attach_AudioWarning"), NAME_None, FVector(-62.0, 0.0, 85.0), 180.0)
    });
}

USceneComponent* ULBSupportRobotRuntimeComponentV002::FindUniqueAnchorComponent(
    FName CanonicalName, bool& bOutDuplicate) const
{
    bOutDuplicate = false;
    const AActor* Owner = GetOwner();
    if (!IsValid(Owner) || CanonicalName.IsNone())
    {
        return nullptr;
    }

    const FName DotTag(*FString::Printf(TEXT("LB.Anchor.%s"), *CanonicalName.ToString()));
    const FName ColonTag(*FString::Printf(TEXT("LBAnchor:%s"), *CanonicalName.ToString()));
    const FName RP01Tag(*FString::Printf(TEXT("LB.RP01.Anchor.%s"), *CanonicalName.ToString()));
    const FName CR01Tag(*FString::Printf(TEXT("LB.CR01.Anchor.%s"), *CanonicalName.ToString()));
    const FName MR01Tag(*FString::Printf(TEXT("LB.MR01.Anchor.%s"), *CanonicalName.ToString()));
    const FString CanonicalString = CanonicalName.ToString();
    TInlineComponentArray<USceneComponent*> Components(Owner);
    USceneComponent* Match = nullptr;
    for (USceneComponent* Component : Components)
    {
        if (!IsValid(Component))
        {
            continue;
        }
        const FString ComponentName = Component->GetFName().ToString();
        const bool bGeneratedCanonicalName = ComponentName == CanonicalString + TEXT("_GEN_VARIABLE")
            || ComponentName == CanonicalString + TEXT("_0");
        const bool bMatches = Component->GetFName() == CanonicalName || bGeneratedCanonicalName
            || Component->ComponentHasTag(DotTag) || Component->ComponentHasTag(ColonTag)
            || Component->ComponentHasTag(RP01Tag) || Component->ComponentHasTag(CR01Tag)
            || Component->ComponentHasTag(MR01Tag);
        if (!bMatches)
        {
            continue;
        }
        if (Match != nullptr && Match != Component)
        {
            bOutDuplicate = true;
            return nullptr;
        }
        Match = Component;
    }
    return Match;
}

bool ULBSupportRobotRuntimeComponentV002::ResolveAndValidateAnchors()
{
    ResolvedAnchors.Reset();
    MissingOrInvalidAnchors.Reset();
    bAnchorContractValid = false;

    AActor* Owner = GetOwner();
    if (!IsValid(Owner) || !IsValid(Owner->GetRootComponent()))
    {
        MissingOrInvalidAnchors.Add(TEXT("OWNER_ROOT"));
        return false;
    }
    if (!LBSupportRobotFiniteV002::IsFiniteTransform(Owner->GetActorTransform())
        || !Owner->GetActorScale3D().Equals(FVector::OneVector, AnchorScaleTolerance))
    {
        MissingOrInvalidAnchors.Add(TEXT("OWNER_SCALE"));
        return false;
    }

    TArray<FLBAnchorSpecV002> Specs;
    AppendAnchorContract(Specs);
    TMap<USceneComponent*, FName> ClaimedComponents;
    for (const FLBAnchorSpecV002& Spec : Specs)
    {
        bool bDuplicate = false;
        USceneComponent* Component = FindUniqueAnchorComponent(Spec.Name, bDuplicate);
        if (bDuplicate || !IsValid(Component))
        {
            if (Spec.bRequired) MissingOrInvalidAnchors.AddUnique(Spec.Name);
            continue;
        }
        if (const FName* ExistingClaim = ClaimedComponents.Find(Component))
        {
            // One component cannot impersonate multiple canonical anchors by
            // carrying several tags, even when two rest transforms coincide.
            MissingOrInvalidAnchors.AddUnique(*ExistingClaim);
            MissingOrInvalidAnchors.AddUnique(Spec.Name);
            ResolvedAnchors.Remove(*ExistingClaim);
            continue;
        }
        ClaimedComponents.Add(Component, Spec.Name);
        ResolvedAnchors.Add(Spec.Name, Component);
    }

    for (const FLBAnchorSpecV002& Spec : Specs)
    {
        const TWeakObjectPtr<USceneComponent>* WeakFound = ResolvedAnchors.Find(Spec.Name);
        USceneComponent* Component = WeakFound != nullptr ? WeakFound->Get() : nullptr;
        if (!IsValid(Component))
        {
            continue;
        }
        if (!LBSupportRobotFiniteV002::IsFiniteVector(Component->GetRelativeLocation())
            || !LBSupportRobotFiniteV002::IsFiniteRotator(Component->GetRelativeRotation())
            || !LBSupportRobotFiniteV002::IsFiniteVector(Component->GetRelativeScale3D())
            || !Component->GetRelativeScale3D().Equals(FVector::OneVector, AnchorScaleTolerance)
            || Component->IsUsingAbsoluteLocation() || Component->IsUsingAbsoluteRotation()
            || Component->IsUsingAbsoluteScale()
            || !Component->GetRelativeLocation().Equals(Spec.RelativeLocationCentimetres,
                AnchorPositionToleranceCentimetres)
            || !Component->GetRelativeRotation().Equals(Spec.RelativeRotationDegrees,
                AnchorRotationToleranceDegrees))
        {
            MissingOrInvalidAnchors.AddUnique(Spec.Name);
            continue;
        }

        USceneComponent* ExpectedParent = Owner->GetRootComponent();
        if (!Spec.ParentName.IsNone())
        {
            const TWeakObjectPtr<USceneComponent>* ParentWeak = ResolvedAnchors.Find(Spec.ParentName);
            ExpectedParent = ParentWeak != nullptr ? ParentWeak->Get() : nullptr;
        }
        if (!IsValid(ExpectedParent) || Component->GetAttachParent() != ExpectedParent)
        {
            MissingOrInvalidAnchors.AddUnique(Spec.Name);
        }
    }

    bAnchorContractValid = MissingOrInvalidAnchors.IsEmpty();
    return bAnchorContractValid;
}

USceneComponent* ULBSupportRobotRuntimeComponentV002::GetResolvedAnchor(FName CanonicalAnchorName) const
{
    const TWeakObjectPtr<USceneComponent>* Found = ResolvedAnchors.Find(CanonicalAnchorName);
    return Found != nullptr ? Found->Get() : nullptr;
}

ULBSupportRobotAuthorityRegistryV002* ULBSupportRobotRuntimeComponentV002::GetAuthorityRegistry() const
{
    UWorld* World = GetWorld();
    return IsValid(World) ? World->GetSubsystem<ULBSupportRobotAuthorityRegistryV002>() : nullptr;
}

bool ULBSupportRobotRuntimeComponentV002::ValidateTrustedCommissioningEvidence(
    FName StageId, FName EvidenceId) const
{
    FString Failure;
    ULBSupportRobotAuthorityRegistryV002* Registry = GetAuthorityRegistry();
    return Registry != nullptr && !UnitId.IsNone() && !VariantId.IsNone()
        && Registry->ValidateCommissioningEvidence(
            UnitId, VariantId, StageId, EvidenceId, GetOwner(), Failure);
}

bool ULBSupportRobotRuntimeComponentV002::RevalidateActiveDockProofV002(
    FString& OutFailure) const
{
    ULBSupportRobotAuthorityRegistryV002* Registry = GetAuthorityRegistry();
    return Registry != nullptr && ActiveDockProof.IsComplete()
        && Registry->RevalidateDockProof(ActiveDockProof, GetOwner(), OutFailure);
}

bool ULBSupportRobotRuntimeComponentV002::IsCertifiedForOperationV002() const
{
    return bCommissioningCertified
        && CommissioningState == ELBSupportRobotCommissioningStateV002::Certified
        && Condition == ELBSupportRobotConditionV002::Commissioned
        && VariantId == GetExpectedVariantIdV002();
}

bool ULBSupportRobotRuntimeComponentV002::HasOperationalBatteryReserveV002() const
{
    return FMath::IsFinite(BatteryHealthPercent)
        && FMath::IsFinite(BatteryStateOfChargePercent)
        && BatteryHealthPercent > 0.0
        && BatteryStateOfChargePercent > LowBatteryThresholdPercent;
}

bool ULBSupportRobotRuntimeComponentV002::BeginInspection(FName EvidenceId)
{
    if ((CommissioningState != ELBSupportRobotCommissioningStateV002::Mothballed
        && CommissioningState != ELBSupportRobotCommissioningStateV002::RepairRequired)
        || !ValidateTrustedCommissioningEvidence(TEXT("BEGIN_INSPECTION"), EvidenceId))
    {
        return false;
    }
    CommissioningState = ELBSupportRobotCommissioningStateV002::Inspection;
    Condition = ELBSupportRobotConditionV002::Surveyed;
    return true;
}

bool ULBSupportRobotRuntimeComponentV002::RecordRepairRequired(FName EvidenceId)
{
    if (CommissioningState != ELBSupportRobotCommissioningStateV002::Inspection
        || !ValidateTrustedCommissioningEvidence(TEXT("REPAIR_REQUIRED"), EvidenceId))
    {
        return false;
    }
    CommissioningState = ELBSupportRobotCommissioningStateV002::RepairRequired;
    Condition = ELBSupportRobotConditionV002::RepairInProgress;
    bCommissioningCertified = false;
    bRouteRevalidationRequired = true;
    return true;
}

bool ULBSupportRobotRuntimeComponentV002::MarkReadyForTest(FName EvidenceId)
{
    if ((CommissioningState != ELBSupportRobotCommissioningStateV002::Inspection
        && CommissioningState != ELBSupportRobotCommissioningStateV002::RepairRequired)
        || !ValidateTrustedCommissioningEvidence(TEXT("READY_FOR_TEST"), EvidenceId))
    {
        return false;
    }
    CommissioningState = ELBSupportRobotCommissioningStateV002::ReadyForTest;
    Condition = ELBSupportRobotConditionV002::Restored;
    bManualCommissioningComplete = false;
    bCalibrationComplete = false;
    return true;
}

bool ULBSupportRobotRuntimeComponentV002::BeginManualCommissioning(FName EvidenceId)
{
    if (CommissioningState != ELBSupportRobotCommissioningStateV002::ReadyForTest
        || !ValidateTrustedCommissioningEvidence(TEXT("BEGIN_MANUAL_COMMISSIONING"), EvidenceId))
    {
        return false;
    }
    CommissioningState = ELBSupportRobotCommissioningStateV002::ManualCommissioning;
    bManualCommissioningComplete = false;
    return true;
}

bool ULBSupportRobotRuntimeComponentV002::CompleteManualCommissioning(FName EvidenceId)
{
    if (CommissioningState != ELBSupportRobotCommissioningStateV002::ManualCommissioning
        || !ValidateTrustedCommissioningEvidence(TEXT("COMPLETE_MANUAL_COMMISSIONING"), EvidenceId))
    {
        return false;
    }
    bManualCommissioningComplete = true;
    return true;
}

bool ULBSupportRobotRuntimeComponentV002::BeginCalibration(FName EvidenceId)
{
    if (!RequiresCalibration() || !bManualCommissioningComplete
        || CommissioningState != ELBSupportRobotCommissioningStateV002::ManualCommissioning
        || !ValidateTrustedCommissioningEvidence(TEXT("BEGIN_CALIBRATION"), EvidenceId))
    {
        return false;
    }
    CommissioningState = ELBSupportRobotCommissioningStateV002::Calibration;
    bCalibrationComplete = false;
    return true;
}

bool ULBSupportRobotRuntimeComponentV002::CompleteCalibration(FName EvidenceId)
{
    if (!RequiresCalibration() || CommissioningState != ELBSupportRobotCommissioningStateV002::Calibration
        || !ValidateTrustedCommissioningEvidence(TEXT("COMPLETE_CALIBRATION"), EvidenceId))
    {
        return false;
    }
    bCalibrationComplete = true;
    return true;
}

bool ULBSupportRobotRuntimeComponentV002::BeginRouteValidation(FName EvidenceId)
{
    const bool bCorrectState = RequiresCalibration()
        ? CommissioningState == ELBSupportRobotCommissioningStateV002::Calibration && bCalibrationComplete
        : CommissioningState == ELBSupportRobotCommissioningStateV002::ManualCommissioning && bManualCommissioningComplete;
    if (!bCorrectState || !ValidateTrustedCommissioningEvidence(TEXT("BEGIN_ROUTE_VALIDATION"), EvidenceId))
    {
        return false;
    }
    CommissioningState = ELBSupportRobotCommissioningStateV002::RouteValidation;
    bRouteRevalidationRequired = true;
    return true;
}

bool ULBSupportRobotRuntimeComponentV002::CertifyRobot(FName FinalApprovalEvidenceId)
{
    FString VariantFailure;
    FString DynamicFailure;
    if (CommissioningState != ELBSupportRobotCommissioningStateV002::RouteValidation
        || ActiveCommonFault != ELBSupportRobotCommonFaultV002::None
        || HasTrustedRouteGrant() || !ActiveTaskId.IsNone()
        || BatteryHealthPercent <= 0.0
        || BatteryStateOfChargePercent <= LowBatteryThresholdPercent
        || !ResolveAndValidateAnchors()
        || !RefreshVariantDynamicInterlocksV002(DynamicFailure)
        || !ValidateVariantForCertification(VariantFailure)
        || !ValidateTrustedCommissioningEvidence(TEXT("FINAL_CERTIFICATION"), FinalApprovalEvidenceId))
    {
        return false;
    }
    CommissioningState = ELBSupportRobotCommissioningStateV002::Certified;
    Condition = ELBSupportRobotConditionV002::Commissioned;
    bCommissioningCertified = true;
    bRouteRevalidationRequired = true;
    SetOperatingState(ELBSupportRobotOperatingStateV002::Stopped);
    return true;
}

bool ULBSupportRobotRuntimeComponentV002::AcknowledgeStoppedRouteRevalidation(FName EvidenceId)
{
    if (!IsCertifiedForOperationV002()
        || HasTrustedRouteGrant() || HasTrustedDockProof() || !ActiveTaskId.IsNone()
        || ActiveCommonFault != ELBSupportRobotCommonFaultV002::None || !ResolveAndValidateAnchors())
    {
        return false;
    }
    FString Failure;
    ULBSupportRobotAuthorityRegistryV002* Registry = GetAuthorityRegistry();
    if (Registry == nullptr || !Registry->ValidateRouteRevalidation(UnitId, EvidenceId, GetOwner(), Failure))
    {
        return false;
    }
    bRouteRevalidationRequired = false;
    SetOperatingState(ELBSupportRobotOperatingStateV002::Stopped);
    return true;
}

bool ULBSupportRobotRuntimeComponentV002::RequestCertifiedRoute(const FLBRouteRequestV002& Request)
{
    FString VariantFailure;
    if (!IsCertifiedForOperationV002() || bRouteRevalidationRequired
        || !ResolveAndValidateAnchors()
        || ActiveCommonFault != ELBSupportRobotCommonFaultV002::None || HasTrustedRouteGrant()
        || !ActiveTaskId.IsNone() || Request.RouteId.IsNone() || Request.ExpectedRevision <= 0
        || !RefreshVariantDynamicInterlocksV002(VariantFailure)
        || !ValidateVariantTravelPermissives(VariantFailure))
    {
        return false;
    }
    if (BatteryHealthPercent <= 0.0
        || BatteryStateOfChargePercent <= LowBatteryThresholdPercent)
    {
        RaiseCommonFault(ELBSupportRobotCommonFaultV002::LowBattery,
            BatteryHealthPercent <= 0.0
                ? TEXT("Battery health has no trusted non-zero service measurement.")
                : TEXT("Battery is at or below the route reserve threshold."));
        return false;
    }

    ULBSupportRobotAuthorityRegistryV002* Registry = GetAuthorityRegistry();
    FString Failure;
    FLBTrustedRouteGrantV002 Grant;
    if (Registry == nullptr || !Registry->IssueRouteGrant(
        UnitId, VariantId, Request, GetOwner(), Grant, Failure))
    {
        RaiseCommonFault(ELBSupportRobotCommonFaultV002::RouteAuthorityUnavailable, Failure);
        return false;
    }

    if (HasTrustedDockProof())
    {
        ReleasePhysicalDockProof();
    }
    ActiveRouteGrant = Grant;
    PendingDockId = NAME_None;
    CurrentCommandedSpeedCentimetresPerSecond = 0.0;
    SetOperatingState(ELBSupportRobotOperatingStateV002::Dispatched);
    SetOperatingState(ELBSupportRobotOperatingStateV002::Navigating);
    return true;
}

void ULBSupportRobotRuntimeComponentV002::AbortRouteAndStop()
{
    if (HasTrustedRouteGrant())
    {
        if (ULBSupportRobotAuthorityRegistryV002* Registry = GetAuthorityRegistry())
        {
            Registry->RevokeRouteGrant(ActiveRouteGrant.GrantId, UnitId);
        }
    }
    ActiveRouteGrant = FLBTrustedRouteGrantV002();
    CurrentCommandedSpeedCentimetresPerSecond = 0.0;
    PendingDockId = NAME_None;
    bRouteRevalidationRequired = true;
    SetOperatingState(ELBSupportRobotOperatingStateV002::Stopped);
    OnSafeStopV002();
}

bool ULBSupportRobotRuntimeComponentV002::RequestPhysicalDockProof(FName DockId)
{
    if (DockId.IsNone() || HasTrustedRouteGrant() || HasTrustedDockProof()
        || !ActiveTaskId.IsNone()
        || ActiveCommonFault != ELBSupportRobotCommonFaultV002::None)
    {
        return false;
    }
    if (!PendingDockId.IsNone() && PendingDockId != DockId)
    {
        return false;
    }
    ULBSupportRobotAuthorityRegistryV002* Registry = GetAuthorityRegistry();
    FString Failure;
    FLBTrustedDockProofV002 Proof;
    if (Registry == nullptr || !Registry->AcquireDockProof(UnitId, DockId, GetOwner(), Proof, Failure))
    {
        return false;
    }
    ActiveDockProof = Proof;
    PendingDockId = NAME_None;
    SetOperatingState(ELBSupportRobotOperatingStateV002::Docked);
    return true;
}

bool ULBSupportRobotRuntimeComponentV002::ReleasePhysicalDockProof()
{
    if (!HasTrustedDockProof() || !ActiveTaskId.IsNone())
    {
        return false;
    }
    if (ULBSupportRobotAuthorityRegistryV002* Registry = GetAuthorityRegistry())
    {
        Registry->ReleaseDockProof(ActiveDockProof.ProofId, UnitId);
    }
    ActiveDockProof = FLBTrustedDockProofV002();
    SetOperatingState(ELBSupportRobotOperatingStateV002::Stopped);
    return true;
}

bool ULBSupportRobotRuntimeComponentV002::ApplyTrustedBatteryServiceResult(
    double NewStateOfChargePercent, double NewHealthPercent, FName ServiceEvidenceId)
{
    if (HasTrustedRouteGrant() || !ActiveTaskId.IsNone()
        || !FMath::IsFinite(NewStateOfChargePercent)
        || !FMath::IsFinite(NewHealthPercent)
        || NewStateOfChargePercent < 0.0 || NewStateOfChargePercent > 100.0
        || NewHealthPercent < 0.0 || NewHealthPercent > 100.0
        || !ValidateTrustedCommissioningEvidence(
            TEXT("RP01_BATTERY_SERVICE"), ServiceEvidenceId))
    {
        return false;
    }
    BatteryStateOfChargePercent = NewStateOfChargePercent;
    BatteryHealthPercent = NewHealthPercent;
    ++ServiceCycles;
    return true;
}

bool ULBSupportRobotRuntimeComponentV002::RequestFaultClear(FName ClearanceEvidenceId)
{
    const FName VariantFaultId = GetActiveVariantFaultIdV002();
    if ((ActiveCommonFault == ELBSupportRobotCommonFaultV002::None && VariantFaultId.IsNone())
        || ClearanceEvidenceId.IsNone() || HasTrustedRouteGrant() || !ActiveTaskId.IsNone())
    {
        return false;
    }

    FString Failure;
    if (!CanCommitVariantFaultClearV002(Failure))
    {
        return false;
    }
    if (ActiveCommonFault == ELBSupportRobotCommonFaultV002::AnchorContractInvalid
        && !ResolveAndValidateAnchors())
    {
        return false;
    }

    ULBSupportRobotAuthorityRegistryV002* Registry = GetAuthorityRegistry();
    if (Registry == nullptr || !Registry->ValidateFaultClearance(UnitId, VariantId,
        ActiveCommonFault, VariantFaultId, ClearanceEvidenceId, GetOwner(), Failure))
    {
        return false;
    }

    // Validate everything first, then commit variant before common. No virtual
    // travel-permissive call can deadlock on the still-active variant fault.
    CommitVariantFaultClearV002();
    const ELBSupportRobotCommonFaultV002 Previous = ActiveCommonFault;
    ActiveCommonFault = ELBSupportRobotCommonFaultV002::None;
    bRouteRevalidationRequired = true;
    SetOperatingState(ELBSupportRobotOperatingStateV002::Stopped);
    OnCommonFaultChanged.Broadcast(Previous, ActiveCommonFault);
    return true;
}

FLBSupportRobotSafeSaveV002 ULBSupportRobotRuntimeComponentV002::CaptureSafeSaveState() const
{
    FLBSupportRobotSafeSaveV002 Saved;
    Saved.UnitId = UnitId;
    Saved.VariantId = VariantId;
    Saved.CommissioningState = CommissioningState;
    Saved.Condition = Condition;
    Saved.PersistedFault = ActiveCommonFault;
    Saved.BatteryStateOfChargePercent = BatteryStateOfChargePercent;
    Saved.BatteryHealthPercent = BatteryHealthPercent;
    Saved.OperatingHours = OperatingHours;
    Saved.MissionCount = MissionCount;
    Saved.ServiceCycles = ServiceCycles;
    Saved.bCommissioningCertified = bCommissioningCertified;
    Saved.LastObservedTransform = IsValid(GetOwner()) ? GetOwner()->GetActorTransform() : FTransform::Identity;
    return Saved;
}

bool ULBSupportRobotRuntimeComponentV002::RestoreSafeStopped(
    const FLBSupportRobotSafeSaveV002& SavedState)
{
    const bool bSavedStateCertified =
        SavedState.CommissioningState == ELBSupportRobotCommissioningStateV002::Certified;
    const bool bSavedConditionCommissioned =
        SavedState.Condition == ELBSupportRobotConditionV002::Commissioned;
    if (SavedState.Version != 2 || SavedState.UnitId.IsNone() || SavedState.VariantId.IsNone()
        || static_cast<uint8>(SavedState.CommissioningState)
            > static_cast<uint8>(ELBSupportRobotCommissioningStateV002::Certified)
        || static_cast<uint8>(SavedState.Condition)
            > static_cast<uint8>(ELBSupportRobotConditionV002::Commissioned)
        || static_cast<uint8>(SavedState.PersistedFault)
            > static_cast<uint8>(ELBSupportRobotCommonFaultV002::RestoreRevalidationRequired)
        || !FMath::IsFinite(SavedState.BatteryStateOfChargePercent)
        || !FMath::IsFinite(SavedState.BatteryHealthPercent)
        || !FMath::IsFinite(SavedState.OperatingHours)
        || !LBSupportRobotFiniteV002::IsFiniteTransform(SavedState.LastObservedTransform)
        || SavedState.BatteryStateOfChargePercent < 0.0
        || SavedState.BatteryStateOfChargePercent > 100.0
        || SavedState.BatteryHealthPercent < 0.0
        || SavedState.BatteryHealthPercent > 100.0
        || SavedState.OperatingHours < 0.0 || SavedState.MissionCount < 0
        || SavedState.ServiceCycles < 0
        || SavedState.bCommissioningCertified != bSavedStateCertified
        || bSavedStateCertified != bSavedConditionCommissioned
        || SavedState.VariantId != GetExpectedVariantIdV002()
        || (!UnitId.IsNone() && UnitId != SavedState.UnitId)
        || (!VariantId.IsNone() && VariantId != SavedState.VariantId))
    {
        return false;
    }

    const ELBSupportRobotCommonFaultV002 PreviousFault = ActiveCommonFault;
    ClearAllTransientAuthorityV002();
    UnitId = SavedState.UnitId;
    VariantId = SavedState.VariantId;
    Condition = SavedState.Condition;
    bCommissioningCertified = SavedState.bCommissioningCertified;
    CommissioningState = bCommissioningCertified
        ? ELBSupportRobotCommissioningStateV002::Certified : SavedState.CommissioningState;
    BatteryStateOfChargePercent = SavedState.BatteryStateOfChargePercent;
    BatteryHealthPercent = SavedState.BatteryHealthPercent;
    OperatingHours = SavedState.OperatingHours;
    MissionCount = SavedState.MissionCount;
    ServiceCycles = SavedState.ServiceCycles;

    // Deliberately do not apply LastObservedTransform and do not restore dock,
    // route, task, permit, localisation, sensor or physical interlock proofs.
    ActiveTaskId = NAME_None;
    PendingDockId = NAME_None;
    bRouteRevalidationRequired = true;
    bManualCommissioningComplete = false;
    bCalibrationComplete = false;
    CurrentCommandedSpeedCentimetresPerSecond = 0.0;
    ActiveCommonFault = SavedState.PersistedFault == ELBSupportRobotCommonFaultV002::None
        ? ELBSupportRobotCommonFaultV002::RestoreRevalidationRequired
        : SavedState.PersistedFault;
    SetOperatingState(ELBSupportRobotOperatingStateV002::SafetyStop);
    OnSafeStoppedRestoreV002();
    if (PreviousFault != ActiveCommonFault)
    {
        OnCommonFaultChanged.Broadcast(PreviousFault, ActiveCommonFault);
    }
    return true;
}

void ULBSupportRobotRuntimeComponentV002::RaiseCommonFault(
    ELBSupportRobotCommonFaultV002 Fault, const FString& Detail)
{
    if (Fault == ELBSupportRobotCommonFaultV002::None)
    {
        return;
    }
    if (static_cast<uint8>(Fault)
        > static_cast<uint8>(ELBSupportRobotCommonFaultV002::RestoreRevalidationRequired))
    {
        Fault = ELBSupportRobotCommonFaultV002::VariantInterlockOpen;
    }
    const ELBSupportRobotCommonFaultV002 Previous = ActiveCommonFault;
    ClearAllTransientAuthorityV002();
    ActiveCommonFault = Fault;
    bRouteRevalidationRequired = true;
    CurrentCommandedSpeedCentimetresPerSecond = 0.0;
    SetOperatingState(ELBSupportRobotOperatingStateV002::SafetyStop);
    OnSafeStopV002();
    OnCommonFaultChanged.Broadcast(Previous, ActiveCommonFault);
    UE_LOG(LogTemp, Warning, TEXT("LB support robot v002 %s safe-stopped: %s"),
        *UnitId.ToString(), *Detail);
}

bool ULBSupportRobotRuntimeComponentV002::ValidateVariantForCertification(FString& OutFailure) const
{
    OutFailure.Reset();
    return true;
}

FName ULBSupportRobotRuntimeComponentV002::GetExpectedVariantIdV002() const
{
    return TEXT("LB-RP01");
}

bool ULBSupportRobotRuntimeComponentV002::ValidateVariantTravelPermissives(FString& OutFailure) const
{
    OutFailure.Reset();
    return true;
}

bool ULBSupportRobotRuntimeComponentV002::RefreshVariantDynamicInterlocksV002(FString& OutFailure)
{
    OutFailure.Reset();
    return true;
}

void ULBSupportRobotRuntimeComponentV002::OnSafeStopV002()
{
}

void ULBSupportRobotRuntimeComponentV002::OnRouteFinishedSafelyV002()
{
    ActiveTaskId = NAME_None;
}

void ULBSupportRobotRuntimeComponentV002::OnSafeStoppedRestoreV002()
{
    ActiveTaskId = NAME_None;
}

bool ULBSupportRobotRuntimeComponentV002::CanCommitVariantFaultClearV002(FString& OutFailure) const
{
    OutFailure.Reset();
    return true;
}

void ULBSupportRobotRuntimeComponentV002::CommitVariantFaultClearV002()
{
}

double ULBSupportRobotRuntimeComponentV002::GetMaximumSpeedCentimetresPerSecondV002(
    ELBRouteSpeedClassV002 SpeedClass, bool bEmergencyDispatch) const
{
    switch (SpeedClass)
    {
    case ELBRouteSpeedClassV002::Docking: return 10.0;
    case ELBRouteSpeedClassV002::MachineApproach: return 20.0;
    case ELBRouteSpeedClassV002::OccupiedAisle: return 60.0;
    case ELBRouteSpeedClassV002::EmergencyCertifiedClearRoute: return bEmergencyDispatch ? 120.0 : 100.0;
    case ELBRouteSpeedClassV002::NormalTransit:
    default: return 100.0;
    }
}

double ULBSupportRobotRuntimeComponentV002::GetAccelerationCentimetresPerSecondSquaredV002(
    ELBRouteSpeedClassV002 SpeedClass, bool bEmergencyDispatch) const
{
    return SpeedClass == ELBRouteSpeedClassV002::OccupiedAisle ? 35.0 : 80.0;
}

void ULBSupportRobotRuntimeComponentV002::SetOperatingState(
    ELBSupportRobotOperatingStateV002 NewState)
{
    if (OperatingState == NewState)
    {
        return;
    }
    const ELBSupportRobotOperatingStateV002 Previous = OperatingState;
    OperatingState = NewState;
    OnOperatingStateChanged.Broadcast(Previous, NewState);
}

void ULBSupportRobotRuntimeComponentV002::ClearAllTransientAuthorityV002()
{
    ULBSupportRobotAuthorityRegistryV002* Registry = GetAuthorityRegistry();
    if (Registry != nullptr && HasTrustedRouteGrant())
    {
        Registry->RevokeRouteGrant(ActiveRouteGrant.GrantId, UnitId);
    }
    if (Registry != nullptr && HasTrustedDockProof())
    {
        Registry->ReleaseDockProof(ActiveDockProof.ProofId, UnitId);
    }
    ActiveRouteGrant = FLBTrustedRouteGrantV002();
    ActiveDockProof = FLBTrustedDockProofV002();
    PendingDockId = NAME_None;
    CurrentCommandedSpeedCentimetresPerSecond = 0.0;
}

bool ULBSupportRobotRuntimeComponentV002::ValidateDynamicRouteSafety(
    const FLBRouteSafetySnapshotV002& Safety, ELBSupportRobotCommonFaultV002& OutFault,
    FString& OutFailure) const
{
    OutFault = ELBSupportRobotCommonFaultV002::RouteAuthorityLost;
    if (!Safety.bGrantValid) { OutFailure = TEXT("Trusted route grant is no longer valid."); return false; }
    if (!Safety.bLocalisationHealthy) { OutFault = ELBSupportRobotCommonFaultV002::LocalisationLost; OutFailure = TEXT("Localisation proof was lost."); return false; }
    if (!Safety.bSafetyNetworkHealthy) { OutFault = ELBSupportRobotCommonFaultV002::SafetyNetworkUnhealthy; OutFailure = TEXT("Safety-network proof was lost."); return false; }
    if (Safety.bProtectiveFieldIntrusion) { OutFault = ELBSupportRobotCommonFaultV002::ProtectiveFieldIntrusion; OutFailure = TEXT("Person or vehicle entered the protective route field."); return false; }
    if (Safety.bOpenGate) { OutFault = ELBSupportRobotCommonFaultV002::OpenGate; OutFailure = TEXT("An open gate intersects the route corridor."); return false; }
    if (Safety.bOpenTrappedKeyBoundary) { OutFault = ELBSupportRobotCommonFaultV002::TrappedKeyBoundary; OutFailure = TEXT("An open trapped-key boundary intersects the route corridor."); return false; }
    if (Safety.bSuspendedLoadZoneIntersection) { OutFault = ELBSupportRobotCommonFaultV002::SuspendedLoadZone; OutFailure = TEXT("A suspended-load exclusion intersects the route corridor."); return false; }
    if (Safety.bLowTractionOrSpill) { OutFault = ELBSupportRobotCommonFaultV002::LowTractionOrSpill; OutFailure = TEXT("Low traction or a spill invalidated the route."); return false; }
    if (!Safety.bRouteClear) { OutFault = ELBSupportRobotCommonFaultV002::RouteObstructed; OutFailure = TEXT("The certified corridor is obstructed."); return false; }
    OutFault = ELBSupportRobotCommonFaultV002::None;
    OutFailure.Reset();
    return true;
}

ELBRouteSpeedClassV002 ULBSupportRobotRuntimeComponentV002::GetEffectiveSpeedClass(
    const FLBRouteSafetySnapshotV002& Safety) const
{
    auto MostRestrictive = [](ELBRouteSpeedClassV002 A, ELBRouteSpeedClassV002 B)
    {
        return static_cast<uint8>(A) <= static_cast<uint8>(B) ? A : B;
    };
    ELBRouteSpeedClassV002 Effective = ActiveRouteGrant.SpeedClass;
    if (Safety.bSharedAisleOccupied)
    {
        Effective = MostRestrictive(Effective, ELBRouteSpeedClassV002::OccupiedAisle);
    }
    if (Safety.bMachineApproach)
    {
        Effective = MostRestrictive(Effective, ELBRouteSpeedClassV002::MachineApproach);
    }
    if (Safety.bDockingApproach)
    {
        Effective = MostRestrictive(Effective, ELBRouteSpeedClassV002::Docking);
    }
    return Effective;
}

void ULBSupportRobotRuntimeComponentV002::TickTrustedRoute(double DeltaSeconds)
{
    ULBSupportRobotAuthorityRegistryV002* Registry = GetAuthorityRegistry();
    FLBRouteSafetySnapshotV002 Safety;
    FString Failure;
    if (Registry == nullptr || !Registry->RevalidateRouteGrant(ActiveRouteGrant, GetOwner(), Safety, Failure))
    {
        RaiseCommonFault(ELBSupportRobotCommonFaultV002::RouteAuthorityLost, Failure);
        return;
    }

    ELBSupportRobotCommonFaultV002 SafetyFault;
    if (!ValidateDynamicRouteSafety(Safety, SafetyFault, Failure))
    {
        RaiseCommonFault(SafetyFault, Failure);
        return;
    }

    FString VariantFailure;
    if (!RefreshVariantDynamicInterlocksV002(VariantFailure)
        || !ValidateVariantTravelPermissives(VariantFailure))
    {
        RaiseCommonFault(ELBSupportRobotCommonFaultV002::VariantInterlockOpen, VariantFailure);
        return;
    }

    const ELBRouteSpeedClassV002 SpeedClass = GetEffectiveSpeedClass(Safety);
    const double MaximumSpeed = GetMaximumSpeedCentimetresPerSecondV002(
        SpeedClass, ActiveRouteGrant.bEmergencyDispatch);
    const double Acceleration = GetAccelerationCentimetresPerSecondSquaredV002(
        SpeedClass, ActiveRouteGrant.bEmergencyDispatch);
    FLBRouteAdvanceResultV002 Result = Registry->AdvanceRoute(ActiveRouteGrant, GetOwner(),
        DeltaSeconds, MaximumSpeed, Acceleration);
    if (!Result.bSucceeded)
    {
        RaiseCommonFault(ELBSupportRobotCommonFaultV002::RouteObstructed, Result.FailureDetail);
        return;
    }

    BatteryStateOfChargePercent = FMath::Max(0.0, BatteryStateOfChargePercent
        - (Result.DistanceMovedCentimetres / 100.0) * TransitDrainPercentPerMetre);
    if (BatteryStateOfChargePercent <= LowBatteryThresholdPercent)
    {
        RaiseCommonFault(ELBSupportRobotCommonFaultV002::LowBattery,
            TEXT("Battery reached the route-abort reserve threshold."));
        return;
    }
    if (Result.bRouteComplete)
    {
        CompleteTrustedRoute();
    }
}

void ULBSupportRobotRuntimeComponentV002::TickTrustedDock(double DeltaSeconds)
{
    ULBSupportRobotAuthorityRegistryV002* Registry = GetAuthorityRegistry();
    FString Failure;
    if (Registry == nullptr || !Registry->RevalidateDockProof(ActiveDockProof, GetOwner(), Failure))
    {
        RaiseCommonFault(ELBSupportRobotCommonFaultV002::DockProofLost, Failure);
        return;
    }
    BatteryStateOfChargePercent = FMath::Min(100.0,
        BatteryStateOfChargePercent + ChargingRatePercentPerSecond * DeltaSeconds);
    SetOperatingState(BatteryStateOfChargePercent < 100.0
        ? ELBSupportRobotOperatingStateV002::Charging
        : ELBSupportRobotOperatingStateV002::Docked);
}

void ULBSupportRobotRuntimeComponentV002::CompleteTrustedRoute()
{
    const FName DestinationDockId = ActiveRouteGrant.DestinationDockId;
    if (ULBSupportRobotAuthorityRegistryV002* Registry = GetAuthorityRegistry())
    {
        Registry->RevokeRouteGrant(ActiveRouteGrant.GrantId, UnitId);
    }
    ActiveRouteGrant = FLBTrustedRouteGrantV002();
    CurrentCommandedSpeedCentimetresPerSecond = 0.0;
    ++MissionCount;
    OnRouteFinishedSafelyV002();
    PendingDockId = DestinationDockId;
    SetOperatingState(ELBSupportRobotOperatingStateV002::Stopped);
    // A named destination never auto-docks. RequestPhysicalDockProof must pass.
}
