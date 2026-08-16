#include "LBMaintenanceRobotRuntimeComponentV002.h"

namespace
{
    FLBAnchorSpecV002 MRAnchor(FName Name, FName ParentName,
        const FVector& RelativeLocation, const FRotator& RelativeRotation = FRotator::ZeroRotator)
    {
        FLBAnchorSpecV002 Spec;
        Spec.Name = Name;
        Spec.ParentName = ParentName;
        Spec.RelativeLocationCentimetres = RelativeLocation;
        Spec.RelativeRotationDegrees = RelativeRotation;
        return Spec;
    }
}

ULBMaintenanceRobotRuntimeComponentV002::ULBMaintenanceRobotRuntimeComponentV002()
{
    VariantId = TEXT("LB-MR01");
    LastObservedJointDegrees = {180.0, -35.0, 130.0, 0.0, -95.0, 0.0};
    ToolRackInventory = {
        ELBMaintenanceToolV002::T1_InspectionHead,
        ELBMaintenanceToolV002::T2_ConditionProbe,
        ELBMaintenanceToolV002::T3_Lubrication,
        ELBMaintenanceToolV002::T4_Cleaning,
        ELBMaintenanceToolV002::T5_ServiceGripper,
        ELBMaintenanceToolV002::T6_TorqueTool,
        ELBMaintenanceToolV002::T7_FluidLeak,
        ELBMaintenanceToolV002::T8_ModuleExchange
    };
}

void ULBMaintenanceRobotRuntimeComponentV002::AppendAnchorContract(
    TArray<FLBAnchorSpecV002>& InOutSpecs) const
{
    Super::AppendAnchorContract(InOutSpecs);
    InOutSpecs.Append({
        MRAnchor(TEXT("MR01PayloadFrame"), TEXT("Attach_MR01_Payload"), FVector(0.0, 0.0, -38.5)),
        MRAnchor(TEXT("PVT_Susp_FL"), TEXT("MR01PayloadFrame"), FVector(50.0, -40.5, 25.0)),
        MRAnchor(TEXT("PVT_Susp_FR"), TEXT("MR01PayloadFrame"), FVector(50.0, 40.5, 25.0)),
        MRAnchor(TEXT("PVT_Susp_RL"), TEXT("MR01PayloadFrame"), FVector(-50.0, -40.5, 25.0)),
        MRAnchor(TEXT("PVT_Susp_RR"), TEXT("MR01PayloadFrame"), FVector(-50.0, 40.5, 25.0)),
        MRAnchor(TEXT("PVT_Wheel_FL"), TEXT("PVT_Susp_FL"), FVector(0.0, 0.0, -8.0)),
        MRAnchor(TEXT("PVT_Wheel_FR"), TEXT("PVT_Susp_FR"), FVector(0.0, 0.0, -8.0)),
        MRAnchor(TEXT("PVT_Wheel_RL"), TEXT("PVT_Susp_RL"), FVector(0.0, 0.0, -8.0)),
        MRAnchor(TEXT("PVT_Wheel_RR"), TEXT("PVT_Susp_RR"), FVector(0.0, 0.0, -8.0)),
        MRAnchor(TEXT("PVT_Outrigger_FL_Extend"), TEXT("MR01PayloadFrame"), FVector(43.0, -43.0, 22.0)),
        MRAnchor(TEXT("PVT_Outrigger_FR_Extend"), TEXT("MR01PayloadFrame"), FVector(43.0, 43.0, 22.0)),
        MRAnchor(TEXT("PVT_Outrigger_RL_Extend"), TEXT("MR01PayloadFrame"), FVector(-43.0, -43.0, 22.0)),
        MRAnchor(TEXT("PVT_Outrigger_RR_Extend"), TEXT("MR01PayloadFrame"), FVector(-43.0, 43.0, 22.0)),
        MRAnchor(TEXT("PVT_Outrigger_FL_Drop"), TEXT("PVT_Outrigger_FL_Extend"), FVector(0.0, 0.0, -6.0)),
        MRAnchor(TEXT("PVT_Outrigger_FR_Drop"), TEXT("PVT_Outrigger_FR_Extend"), FVector(0.0, 0.0, -6.0)),
        MRAnchor(TEXT("PVT_Outrigger_RL_Drop"), TEXT("PVT_Outrigger_RL_Extend"), FVector(0.0, 0.0, -6.0)),
        MRAnchor(TEXT("PVT_Outrigger_RR_Drop"), TEXT("PVT_Outrigger_RR_Extend"), FVector(0.0, 0.0, -6.0)),
        MRAnchor(TEXT("PVT_ArmLift"), TEXT("MR01PayloadFrame"), FVector(10.0, 0.0, 66.0)),
        MRAnchor(TEXT("PVT_ArmJ1"), TEXT("PVT_ArmLift"), FVector(0.0, 0.0, 10.0)),
        MRAnchor(TEXT("PVT_ArmJ2"), TEXT("PVT_ArmJ1"), FVector(0.0, 0.0, 14.0)),
        MRAnchor(TEXT("PVT_ArmJ3"), TEXT("PVT_ArmJ2"), FVector(55.0, 0.0, 0.0)),
        MRAnchor(TEXT("PVT_ArmJ4"), TEXT("PVT_ArmJ3"), FVector(50.0, 0.0, 0.0)),
        MRAnchor(TEXT("PVT_ArmJ5"), TEXT("PVT_ArmJ4"), FVector(20.0, 0.0, 0.0)),
        MRAnchor(TEXT("PVT_ArmJ6"), TEXT("PVT_ArmJ5"), FVector(15.0, 0.0, 0.0)),
        MRAnchor(TEXT("PVT_ToolClamp"), TEXT("PVT_ArmJ6"), FVector(10.0, 0.0, 0.0)),
        MRAnchor(TEXT("SCK_ToolCoupler"), TEXT("PVT_ToolClamp"), FVector::ZeroVector),
        MRAnchor(TEXT("SCK_ArmTCP"), TEXT("SCK_ToolCoupler"), FVector(30.0, 0.0, 0.0)),
        MRAnchor(TEXT("SCK_ArmParkingCradle"), TEXT("MR01PayloadFrame"), FVector(39.0, 0.0, 103.0)),
        MRAnchor(TEXT("PVT_MastLift"), TEXT("MR01PayloadFrame"), FVector(-45.0, 28.0, 85.0)),
        MRAnchor(TEXT("PVT_MastPan"), TEXT("PVT_MastLift"), FVector(0.0, 0.0, 33.0)),
        MRAnchor(TEXT("PVT_MastTilt"), TEXT("PVT_MastPan"), FVector::ZeroVector),
        MRAnchor(TEXT("PVT_ToolCarousel"), TEXT("MR01PayloadFrame"), FVector(-33.0, 25.5, 65.0)),
        MRAnchor(TEXT("PVT_PartsDrawer"), TEXT("MR01PayloadFrame"), FVector(-15.0, -43.0, 58.0)),
        MRAnchor(TEXT("PVT_Door_Left"), TEXT("MR01PayloadFrame"), FVector(-10.0, -45.5, 70.0)),
        MRAnchor(TEXT("PVT_Door_Right"), TEXT("MR01PayloadFrame"), FVector(-10.0, 45.5, 70.0)),
        MRAnchor(TEXT("PVT_Door_Rear"), TEXT("MR01PayloadFrame"), FVector(-72.0, 0.0, 72.0))
    });
    for (int32 Slot = 1; Slot <= 8; ++Slot)
    {
        InOutSpecs.Add(MRAnchor(
            FName(*FString::Printf(TEXT("SCK_ToolRack_%02d"), Slot)),
            TEXT("PVT_ToolCarousel"), FVector(0.0, 0.0, 21.0),
            FRotator(0.0, 180.0, 45.0 * static_cast<double>(Slot - 1))));
    }
    // M35-M37 are dock-side pivots and must be resolved by the dock authority actor.
}

void ULBMaintenanceRobotRuntimeComponentV002::TickComponent(float DeltaTime,
    ELevelTick TickType, FActorComponentTickFunction* ThisTickFunction)
{
    Super::TickComponent(DeltaTime, TickType, ThisTickFunction);
    if (!ActiveWorkGrant.IsComplete())
    {
        return;
    }

    FString Failure;
    ELBMaintenanceRobotFaultV002 SuggestedFault =
        ELBMaintenanceRobotFaultV002::F15_ExclusionZoneIntrusion;
    if (!RefreshWorkAndToolProofs(Failure, bArmMotionActive, &SuggestedFault))
    {
        ReportMaintenanceFault(SuggestedFault, Failure);
    }
}

bool ULBMaintenanceRobotRuntimeComponentV002::RequestTravelReadinessProof(FName EvidenceId)
{
    if (HasTrustedRouteGrant() || !ActiveTaskId.IsNone()
        || ActiveMaintenanceFault != ELBMaintenanceRobotFaultV002::None
        || ActiveCommonFault != ELBSupportRobotCommonFaultV002::None)
    {
        return false;
    }
    FString Failure;
    FLBTrustedTravelInterlockProofV002 Proof;
    ULBSupportRobotAuthorityRegistryV002* Registry = GetAuthorityRegistry();
    if (Registry == nullptr || !Registry->AcquireTravelInterlockProof(UnitId,
        EvidenceId, GetOwner(), Proof, Failure))
    {
        return false;
    }
    ActiveTravelProof = Proof;
    return true;
}

bool ULBMaintenanceRobotRuntimeComponentV002::RequestToolCouplingProof(
    ELBMaintenanceToolV002 RequestedTool, int32 RackSlot, FName EvidenceId)
{
    if (RequestedTool == ELBMaintenanceToolV002::None || RackSlot < 1 || RackSlot > 8
        || HasTrustedRouteGrant() || bArmMotionActive || !ActiveTaskId.IsNone()
        || ActiveTool != ELBMaintenanceToolV002::None || ActiveToolProof.IsComplete()
        || ActiveCommonFault != ELBSupportRobotCommonFaultV002::None
        || !ToolRackInventory.IsValidIndex(RackSlot - 1)
        || ToolRackInventory[RackSlot - 1] != RequestedTool)
    {
        return false;
    }

    FString Failure;
    FLBTrustedToolCouplingProofV002 Proof;
    ULBSupportRobotAuthorityRegistryV002* Registry = GetAuthorityRegistry();
    const FName ToolId = ToolIdForEnum(RequestedTool);
    if (Registry == nullptr || !Registry->AcquireToolCouplingProof(UnitId, ToolId,
        RackSlot, EvidenceId, GetOwner(), Proof, Failure))
    {
        ReportMaintenanceFault(ELBMaintenanceRobotFaultV002::F05_ToolNotSeated, Failure);
        return false;
    }

    ActiveToolProof = Proof;
    ActiveTool = RequestedTool;
    ToolRackInventory[RackSlot - 1] = ELBMaintenanceToolV002::None;
    return true;
}

bool ULBMaintenanceRobotRuntimeComponentV002::RequestActiveToolReturnProof(
    int32 RackSlot, FName EvidenceId)
{
    if (ActiveTool == ELBMaintenanceToolV002::None || RackSlot < 1 || RackSlot > 8
        || EvidenceId.IsNone() || HasTrustedRouteGrant() || bArmMotionActive
        || !ActiveTaskId.IsNone() || !ToolRackInventory.IsValidIndex(RackSlot - 1)
        || ToolRackInventory[RackSlot - 1] != ELBMaintenanceToolV002::None)
    {
        return false;
    }

    FString Failure;
    FLBTrustedToolReturnProofV002 Proof;
    ULBSupportRobotAuthorityRegistryV002* Registry = GetAuthorityRegistry();
    if (Registry == nullptr || !Registry->AcquireToolReturnProof(UnitId,
        ToolIdForEnum(ActiveTool), RackSlot, EvidenceId, GetOwner(), Proof, Failure))
    {
        return false;
    }

    ToolRackInventory[RackSlot - 1] = ActiveTool;
    ActiveTool = ELBMaintenanceToolV002::None;
    ActiveToolProof = FLBTrustedToolCouplingProofV002();
    return true;
}

bool ULBMaintenanceRobotRuntimeComponentV002::BeginMaintenanceTask(
    ELBMaintenanceTaskV002 Task, FName TaskId, FName CertifiedWorkPointId, FName PermitId)
{
    if (TaskId.IsNone() || CertifiedWorkPointId.IsNone() || PermitId.IsNone()
        || HasTrustedRouteGrant() || HasTrustedDockProof() || !ActiveTaskId.IsNone()
        || !IsCertifiedForOperationV002()
        || ActiveCommonFault != ELBSupportRobotCommonFaultV002::None
        || ActiveMaintenanceFault != ELBMaintenanceRobotFaultV002::None
        || ActiveTool != RequiredToolForTask(Task) || !ActiveToolProof.IsComplete()
        || ActiveToolProof.ToolId != ToolIdForEnum(ActiveTool))
    {
        return false;
    }
    if (!HasOperationalBatteryReserveV002())
    {
        ReportMaintenanceFault(ELBMaintenanceRobotFaultV002::F03_LowOrDegradedBattery,
            TEXT("MR01 cannot begin maintenance work without trusted battery reserve."));
        return false;
    }

    FString Failure;
    FLBTrustedToolCouplingProofV002 CurrentToolProof;
    FLBTrustedWorkAuthorityV002 Grant;
    ULBSupportRobotAuthorityRegistryV002* Registry = GetAuthorityRegistry();
    if (Registry == nullptr || !Registry->RevalidateToolCouplingProof(ActiveToolProof,
        GetOwner(), CurrentToolProof, Failure)
        || !Registry->IssueWorkAuthority(UnitId, VariantId,
            CertifiedWorkPointId, PermitId, TaskId, GetOwner(), Grant, Failure))
    {
        return false;
    }
    if (CurrentToolProof.ToolMassKilograms + Grant.HandledPayloadMassKilograms
        > MaximumArmPayloadIncludingToolKilograms)
    {
        Registry->RevokeWorkAuthority(Grant.GrantId, UnitId);
        return false;
    }

    ActiveMaintenanceTask = Task;
    ActiveTaskId = TaskId;
    ActiveToolProof = CurrentToolProof;
    ActiveWorkGrant = Grant;
    ActiveOutriggerProof = FLBTrustedOutriggerProofV002();
    SetOperatingState(ELBSupportRobotOperatingStateV002::Working);
    return true;
}

bool ULBMaintenanceRobotRuntimeComponentV002::RequestOutriggerDeploymentProof()
{
    if (!ActiveWorkGrant.IsComplete() || ActiveTaskId.IsNone() || bArmMotionActive)
    {
        return false;
    }
    FString Failure;
    ELBMaintenanceRobotFaultV002 SuggestedFault =
        ELBMaintenanceRobotFaultV002::F15_ExclusionZoneIntrusion;
    if (!RefreshWorkAndToolProofs(Failure, false, &SuggestedFault))
    {
        ReportMaintenanceFault(SuggestedFault, Failure);
        return false;
    }
    FLBTrustedOutriggerProofV002 Proof;
    ULBSupportRobotAuthorityRegistryV002* Registry = GetAuthorityRegistry();
    if (Registry == nullptr || !Registry->AcquireOutriggerProof(UnitId,
        ActiveWorkGrant.WorkPointId, GetOwner(), Proof, Failure))
    {
        ReportMaintenanceFault(ELBMaintenanceRobotFaultV002::F12_OutriggerNotDeployed, Failure);
        return false;
    }
    ActiveOutriggerProof = Proof;
    return true;
}

bool ULBMaintenanceRobotRuntimeComponentV002::CanUseArm(FText& BlockingReason) const
{
    BlockingReason = FText::GetEmpty();
    if (HasTrustedRouteGrant() || ActiveTaskId.IsNone() || !ActiveWorkGrant.IsComplete())
    {
        BlockingReason = FText::FromString(TEXT("A current trusted work grant is required while stationary."));
        return false;
    }
    if (!ActiveOutriggerProof.HasFiniteFourLoads())
    {
        BlockingReason = FText::FromString(TEXT("All four outriggers need current position and finite load proof."));
        return false;
    }
    if (!ActiveToolProof.IsComplete() || ActiveTool != RequiredToolForTask(ActiveMaintenanceTask)
        || ActiveToolProof.ToolId != ToolIdForEnum(ActiveTool))
    {
        BlockingReason = FText::FromString(TEXT("The correct T1-T8 tool needs current 45-degree index, 350 mm withdrawal and 12 mm lock proof."));
        return false;
    }
    if (ActiveToolProof.ToolMassKilograms + ActiveWorkGrant.HandledPayloadMassKilograms
        > MaximumArmPayloadIncludingToolKilograms)
    {
        BlockingReason = FText::FromString(TEXT("Tool plus handled payload exceeds the 25 kg arm rating."));
        return false;
    }
    if (ActiveMaintenanceFault != ELBMaintenanceRobotFaultV002::None)
    {
        BlockingReason = FText::FromString(TEXT("An MR01 F01-F22 fault is active."));
        return false;
    }
    return true;
}

bool ULBMaintenanceRobotRuntimeComponentV002::AuthorizeArmMotionCommand(
    double LiftMillimetres, const TArray<double>& JointDegrees,
    FGuid& OutCommandId, FString& OutFailure)
{
    OutCommandId.Invalidate();
    FText BlockingReason;
    if (bArmMotionActive || !CanUseArm(BlockingReason)
        || !IsJointPoseValid(LiftMillimetres, JointDegrees))
    {
        OutFailure = bArmMotionActive
            ? TEXT("A prior arm command is still active and must complete or safe-stop first.")
            : BlockingReason.IsEmpty()
            ? TEXT("Arm command contains a non-finite or out-of-contract lift/joint pose.")
            : BlockingReason.ToString();
        return false;
    }
    FString DynamicFailure;
    if (!RefreshWorkAndToolProofs(DynamicFailure, true))
    {
        OutFailure = DynamicFailure;
        return false;
    }
    ActiveArmCommandId = FGuid::NewGuid();
    AuthorizedJointDegrees = JointDegrees;
    AuthorizedArmLiftMillimetres = LiftMillimetres;
    bArmMotionActive = ActiveArmCommandId.IsValid();
    OutCommandId = ActiveArmCommandId;
    OutFailure.Reset();
    return bArmMotionActive;
}

void ULBMaintenanceRobotRuntimeComponentV002::NotifyArmMotionStopped(
    const FGuid& CommandId, const TArray<double>& ObservedJointDegrees,
    double ObservedLiftMillimetres)
{
    if (!bArmMotionActive || !CommandId.IsValid() || CommandId != ActiveArmCommandId)
    {
        ReportMaintenanceFault(ELBMaintenanceRobotFaultV002::F20_DiagnosticHandshakeFailed,
            TEXT("Motion adapter reported completion without the matching authorised command ID."));
        return;
    }
    if (!IsJointPoseValid(ObservedLiftMillimetres, ObservedJointDegrees))
    {
        ReportMaintenanceFault(ELBMaintenanceRobotFaultV002::F04_ArmCalibrationDrift,
            TEXT("Motion adapter returned a non-finite or out-of-contract observed pose."));
        return;
    }
    bool bMatchesAuthorizedTarget = FMath::IsNearlyEqual(
        ObservedLiftMillimetres, AuthorizedArmLiftMillimetres, 0.5)
        && ObservedJointDegrees.Num() == AuthorizedJointDegrees.Num();
    for (int32 JointIndex = 0;
        bMatchesAuthorizedTarget && JointIndex < ObservedJointDegrees.Num(); ++JointIndex)
    {
        bMatchesAuthorizedTarget = FMath::Abs(FMath::FindDeltaAngleDegrees(
            AuthorizedJointDegrees[JointIndex], ObservedJointDegrees[JointIndex])) <= 0.25;
    }
    if (!bMatchesAuthorizedTarget)
    {
        ReportMaintenanceFault(ELBMaintenanceRobotFaultV002::F04_ArmCalibrationDrift,
            TEXT("Motion adapter completion pose does not match the authorised command target."));
        return;
    }
    LastObservedJointDegrees = ObservedJointDegrees;
    LastObservedArmLiftMillimetres = ObservedLiftMillimetres;
    ClearArmMotionCommandV002();
}

bool ULBMaintenanceRobotRuntimeComponentV002::CompleteMaintenanceTask(FName EvidenceId)
{
    if (EvidenceId.IsNone() || ActiveTaskId.IsNone() || bArmMotionActive
        || !ActiveWorkGrant.IsComplete())
    {
        return false;
    }
    FString Failure;
    ULBSupportRobotAuthorityRegistryV002* Registry = GetAuthorityRegistry();
    if (Registry == nullptr || !RefreshWorkAndToolProofs(Failure, true)
        || !Registry->ValidateArmParkedProof(UnitId, GetOwner(), Failure)
        || !Registry->ValidateTaskCompletionEvidence(UnitId, ActiveTaskId,
            ActiveWorkGrant.PermitId, EvidenceId, GetOwner(), Failure))
    {
        return false;
    }
    LastCompletedPermitId = ActiveWorkGrant.PermitId;
    RevokeWorkAuthorityAndClearTask();
    SetOperatingState(ELBSupportRobotOperatingStateV002::Stopped);
    return true;
}

void ULBMaintenanceRobotRuntimeComponentV002::AbortMaintenanceTaskAndSafeStop()
{
    RevokeWorkAuthorityAndClearTask();
    ClearArmMotionCommandV002();
    RaiseCommonFault(ELBSupportRobotCommonFaultV002::VariantInterlockOpen,
        TEXT("MR01 maintenance task was aborted and all session authority was revoked."));
}

void ULBMaintenanceRobotRuntimeComponentV002::ReportMaintenanceFault(
    ELBMaintenanceRobotFaultV002 Fault, const FString& Detail)
{
    if (Fault == ELBMaintenanceRobotFaultV002::None)
    {
        return;
    }
    if (static_cast<uint8>(Fault)
        > static_cast<uint8>(ELBMaintenanceRobotFaultV002::F22_ArmParkingNotProved))
    {
        RaiseCommonFault(ELBSupportRobotCommonFaultV002::VariantInterlockOpen,
            TEXT("MR01 received an out-of-contract fault identifier and safe-stopped."));
        return;
    }
    ActiveMaintenanceFault = Fault;
    ELBSupportRobotCommonFaultV002 CommonFault = ELBSupportRobotCommonFaultV002::VariantInterlockOpen;
    if (Fault == ELBMaintenanceRobotFaultV002::F02_LostLocalisation)
        CommonFault = ELBSupportRobotCommonFaultV002::LocalisationLost;
    else if (Fault == ELBMaintenanceRobotFaultV002::F03_LowOrDegradedBattery)
        CommonFault = ELBSupportRobotCommonFaultV002::LowBattery;
    else if (Fault == ELBMaintenanceRobotFaultV002::F16_LeakOrContaminationDetected)
        CommonFault = ELBSupportRobotCommonFaultV002::LowTractionOrSpill;
    else if (Fault == ELBMaintenanceRobotFaultV002::F17_DockingContactsDirty)
        CommonFault = ELBSupportRobotCommonFaultV002::DockProofLost;
    RevokeWorkAuthorityAndClearTask();
    ClearArmMotionCommandV002();
    RaiseCommonFault(CommonFault, Detail);
}

FLBMaintenanceRobotSafeSaveV002 ULBMaintenanceRobotRuntimeComponentV002::CaptureMaintenanceSafeSave() const
{
    FLBMaintenanceRobotSafeSaveV002 Saved;
    Saved.Common = CaptureSafeSaveState();
    Saved.PersistedMaintenanceFault = ActiveMaintenanceFault;
    Saved.ExpectedActiveTool = ActiveTool;
    Saved.ExpectedToolRackInventory = ToolRackInventory;
    Saved.LastObservedJointDegrees = LastObservedJointDegrees;
    Saved.LastObservedArmLiftMillimetres = LastObservedArmLiftMillimetres;
    Saved.LastObservedMastExtensionMillimetres = LastObservedMastExtensionMillimetres;
    Saved.LastCompletedPermitId = LastCompletedPermitId;
    return Saved;
}

bool ULBMaintenanceRobotRuntimeComponentV002::RestoreMaintenanceSafeStopped(
    const FLBMaintenanceRobotSafeSaveV002& SavedState)
{
    if (SavedState.Version != 2 || SavedState.ExpectedToolRackInventory.Num() != 8
        || SavedState.LastObservedJointDegrees.Num() != 6
        || !FMath::IsFinite(SavedState.LastObservedArmLiftMillimetres)
        || !FMath::IsFinite(SavedState.LastObservedMastExtensionMillimetres))
    {
        return false;
    }
    for (const double Joint : SavedState.LastObservedJointDegrees)
    {
        if (!FMath::IsFinite(Joint)) return false;
    }
    if (SavedState.LastObservedArmLiftMillimetres < 0.0
        || SavedState.LastObservedArmLiftMillimetres > 400.0
        || SavedState.LastObservedMastExtensionMillimetres < 0.0
        || SavedState.LastObservedMastExtensionMillimetres > 1200.0
        || SavedState.LastObservedJointDegrees[0] < -180.0
        || SavedState.LastObservedJointDegrees[0] > 180.0
        || SavedState.LastObservedJointDegrees[1] < -95.0
        || SavedState.LastObservedJointDegrees[1] > 120.0
        || SavedState.LastObservedJointDegrees[2] < -145.0
        || SavedState.LastObservedJointDegrees[2] > 150.0
        || SavedState.LastObservedJointDegrees[3] < -200.0
        || SavedState.LastObservedJointDegrees[3] > 200.0
        || SavedState.LastObservedJointDegrees[4] < -120.0
        || SavedState.LastObservedJointDegrees[4] > 120.0)
    {
        return false;
    }
    TSet<uint8> SeenTools;
    int32 EmptyRackSlots = 0;
    for (const ELBMaintenanceToolV002 Tool : SavedState.ExpectedToolRackInventory)
    {
        const uint8 Value = static_cast<uint8>(Tool);
        if (Tool == ELBMaintenanceToolV002::None)
        {
            ++EmptyRackSlots;
            continue;
        }
        if (Value > 8 || SeenTools.Contains(Value)) return false;
        SeenTools.Add(Value);
    }
    if (static_cast<uint8>(SavedState.ExpectedActiveTool) > 8
        || static_cast<uint8>(SavedState.PersistedMaintenanceFault) > 22
        || (SavedState.ExpectedActiveTool == ELBMaintenanceToolV002::None
            && (EmptyRackSlots != 0 || SeenTools.Num() != 8))
        || (SavedState.ExpectedActiveTool != ELBMaintenanceToolV002::None
            && (EmptyRackSlots != 1 || SeenTools.Num() != 7
                || SeenTools.Contains(static_cast<uint8>(SavedState.ExpectedActiveTool)))))
    {
        return false;
    }
    if (!RestoreSafeStopped(SavedState.Common))
    {
        return false;
    }

    ActiveMaintenanceFault = SavedState.PersistedMaintenanceFault;
    ActiveTool = SavedState.ExpectedActiveTool;
    ToolRackInventory = SavedState.ExpectedToolRackInventory;
    LastObservedJointDegrees = SavedState.LastObservedJointDegrees;
    LastObservedArmLiftMillimetres = SavedState.LastObservedArmLiftMillimetres;
    LastObservedMastExtensionMillimetres = SavedState.LastObservedMastExtensionMillimetres;
    LastCompletedPermitId = SavedState.LastCompletedPermitId;

    // Observations are retained for UI only. All physical/session proofs are
    // invalidated, no arm/mast/outrigger pose is applied, and no task resumes.
    ClearArmMotionCommandV002();
    ClearAllVariantProofs();
    ActiveTaskId = NAME_None;
    return true;
}

bool ULBMaintenanceRobotRuntimeComponentV002::ValidateVariantForCertification(
    FString& OutFailure) const
{
    if (ActiveMaintenanceFault != ELBMaintenanceRobotFaultV002::None)
    {
        OutFailure = TEXT("An MR01 F01-F22 fault is active.");
        return false;
    }
    if (!ActiveTravelProof.IsCompleteForNormalTravel())
    {
        OutFailure = TEXT("MR01 has no current native travel-interlock proof.");
        return false;
    }
    OutFailure.Reset();
    return true;
}

bool ULBMaintenanceRobotRuntimeComponentV002::ValidateVariantTravelPermissives(
    FString& OutFailure) const
{
    if (ActiveMaintenanceFault != ELBMaintenanceRobotFaultV002::None)
    {
        OutFailure = TEXT("An MR01 F01-F22 fault is active.");
        return false;
    }
    if (!ActiveTravelProof.IsCompleteForNormalTravel())
    {
        OutFailure = TEXT("MR01 travel interlocks have no current native proof.");
        return false;
    }
    if (ActiveWorkGrant.IsComplete() || ActiveOutriggerProof.HasFiniteFourLoads()
        || bArmMotionActive)
    {
        OutFailure = TEXT("Work authority, deployed outriggers or arm motion still inhibits travel.");
        return false;
    }
    OutFailure.Reset();
    return true;
}

bool ULBMaintenanceRobotRuntimeComponentV002::RefreshVariantDynamicInterlocksV002(
    FString& OutFailure)
{
    if (!ActiveTravelProof.IsCompleteForNormalTravel())
    {
        OutFailure = TEXT("MR01 travel proof is absent or structurally invalid.");
        return false;
    }
    ULBSupportRobotAuthorityRegistryV002* Registry = GetAuthorityRegistry();
    FLBTrustedTravelInterlockProofV002 Current;
    if (Registry == nullptr || !Registry->RevalidateTravelInterlockProof(
        ActiveTravelProof, GetOwner(), Current, OutFailure))
    {
        ActiveTravelProof = FLBTrustedTravelInterlockProofV002();
        return false;
    }
    ActiveTravelProof = Current;
    return true;
}

void ULBMaintenanceRobotRuntimeComponentV002::OnSafeStopV002()
{
    RevokeWorkAuthorityAndClearTask();
    ClearArmMotionCommandV002();
    ActiveTravelProof = FLBTrustedTravelInterlockProofV002();
    ActiveToolProof = FLBTrustedToolCouplingProofV002();
    ActiveOutriggerProof = FLBTrustedOutriggerProofV002();
}

void ULBMaintenanceRobotRuntimeComponentV002::OnRouteFinishedSafelyV002()
{
    Super::OnRouteFinishedSafelyV002();
    ActiveTravelProof = FLBTrustedTravelInterlockProofV002();
}

void ULBMaintenanceRobotRuntimeComponentV002::OnSafeStoppedRestoreV002()
{
    Super::OnSafeStoppedRestoreV002();
    ClearArmMotionCommandV002();
    ClearAllVariantProofs();
}

FName ULBMaintenanceRobotRuntimeComponentV002::GetActiveVariantFaultIdV002() const
{
    const int32 Value = static_cast<int32>(ActiveMaintenanceFault);
    return Value > 0 && Value <= 22
        ? FName(*FString::Printf(TEXT("F%02d"), Value)) : NAME_None;
}

bool ULBMaintenanceRobotRuntimeComponentV002::CanCommitVariantFaultClearV002(
    FString& OutFailure) const
{
    OutFailure.Reset();
    return true;
}

void ULBMaintenanceRobotRuntimeComponentV002::CommitVariantFaultClearV002()
{
    ActiveMaintenanceFault = ELBMaintenanceRobotFaultV002::None;
    ClearArmMotionCommandV002();
    ClearAllVariantProofs();
    ActiveTaskId = NAME_None;
}

double ULBMaintenanceRobotRuntimeComponentV002::GetMaximumSpeedCentimetresPerSecondV002(
    ELBRouteSpeedClassV002 SpeedClass, bool bEmergencyDispatch) const
{
    switch (SpeedClass)
    {
    case ELBRouteSpeedClassV002::Docking: return 10.0;
    case ELBRouteSpeedClassV002::MachineApproach: return 20.0;
    case ELBRouteSpeedClassV002::OccupiedAisle: return 60.0;
    case ELBRouteSpeedClassV002::EmergencyCertifiedClearRoute:
        return bEmergencyDispatch && ActiveTravelProof.IsCompleteForEmergencyTravel()
            ? 200.0 : 120.0;
    case ELBRouteSpeedClassV002::NormalTransit:
    default: return 120.0;
    }
}

double ULBMaintenanceRobotRuntimeComponentV002::GetAccelerationCentimetresPerSecondSquaredV002(
    ELBRouteSpeedClassV002 SpeedClass, bool bEmergencyDispatch) const
{
    if (SpeedClass == ELBRouteSpeedClassV002::OccupiedAisle) return 35.0;
    if (SpeedClass == ELBRouteSpeedClassV002::EmergencyCertifiedClearRoute
        && bEmergencyDispatch && ActiveTravelProof.IsCompleteForEmergencyTravel()) return 120.0;
    return 80.0;
}

ELBMaintenanceToolV002 ULBMaintenanceRobotRuntimeComponentV002::RequiredToolForTask(
    ELBMaintenanceTaskV002 Task) const
{
    switch (Task)
    {
    case ELBMaintenanceTaskV002::Inspection: return ELBMaintenanceToolV002::T1_InspectionHead;
    case ELBMaintenanceTaskV002::Diagnosis: return ELBMaintenanceToolV002::T2_ConditionProbe;
    case ELBMaintenanceTaskV002::Lubrication: return ELBMaintenanceToolV002::T3_Lubrication;
    case ELBMaintenanceTaskV002::SensorCleaning: return ELBMaintenanceToolV002::T4_Cleaning;
    case ELBMaintenanceTaskV002::PartsDelivery: return ELBMaintenanceToolV002::T5_ServiceGripper;
    case ELBMaintenanceTaskV002::ApprovedFastenerService: return ELBMaintenanceToolV002::T6_TorqueTool;
    case ELBMaintenanceTaskV002::LeakClassification: return ELBMaintenanceToolV002::T7_FluidLeak;
    case ELBMaintenanceTaskV002::ApprovedModuleExchange: return ELBMaintenanceToolV002::T8_ModuleExchange;
    default: return ELBMaintenanceToolV002::None;
    }
}

FName ULBMaintenanceRobotRuntimeComponentV002::ToolIdForEnum(ELBMaintenanceToolV002 Tool) const
{
    const int32 Value = static_cast<int32>(Tool);
    return Value >= 1 && Value <= 8 ? FName(*FString::Printf(TEXT("T%d"), Value)) : NAME_None;
}

bool ULBMaintenanceRobotRuntimeComponentV002::IsJointPoseValid(double LiftMillimetres,
    const TArray<double>& JointDegrees) const
{
    if (!FMath::IsFinite(LiftMillimetres) || LiftMillimetres < 0.0
        || LiftMillimetres > 400.0 || JointDegrees.Num() != 6)
    {
        return false;
    }
    for (const double Joint : JointDegrees)
    {
        if (!FMath::IsFinite(Joint)) return false;
    }
    return JointDegrees[0] >= -170.0 && JointDegrees[0] <= 170.0
        && JointDegrees[1] >= -95.0 && JointDegrees[1] <= 120.0
        && JointDegrees[2] >= -145.0 && JointDegrees[2] <= 150.0
        && JointDegrees[3] >= -200.0 && JointDegrees[3] <= 200.0
        && JointDegrees[4] >= -120.0 && JointDegrees[4] <= 120.0;
    // J6 is continuous but must still be finite. The pack's exceptional 180-degree
    // folded J1 pose is reserved for a future collision-checked parking adapter.
}

void ULBMaintenanceRobotRuntimeComponentV002::ClearArmMotionCommandV002()
{
    bArmMotionActive = false;
    ActiveArmCommandId.Invalidate();
    AuthorizedJointDegrees.Reset();
    AuthorizedArmLiftMillimetres = 0.0;
}

void ULBMaintenanceRobotRuntimeComponentV002::RevokeWorkAuthorityAndClearTask()
{
    if (ActiveWorkGrant.IsComplete())
    {
        if (ULBSupportRobotAuthorityRegistryV002* Registry = GetAuthorityRegistry())
        {
            Registry->RevokeWorkAuthority(ActiveWorkGrant.GrantId, UnitId);
        }
    }
    ActiveWorkGrant = FLBTrustedWorkAuthorityV002();
    ActiveOutriggerProof = FLBTrustedOutriggerProofV002();
    ActiveTaskId = NAME_None;
}

void ULBMaintenanceRobotRuntimeComponentV002::ClearAllVariantProofs()
{
    RevokeWorkAuthorityAndClearTask();
    ActiveTravelProof = FLBTrustedTravelInterlockProofV002();
    ActiveToolProof = FLBTrustedToolCouplingProofV002();
    ActiveOutriggerProof = FLBTrustedOutriggerProofV002();
}

bool ULBMaintenanceRobotRuntimeComponentV002::RefreshWorkAndToolProofs(
    FString& OutFailure, bool bRequireOutriggerProof,
    ELBMaintenanceRobotFaultV002* OutSuggestedFault)
{
    auto SetSuggestedFault = [OutSuggestedFault](ELBMaintenanceRobotFaultV002 Fault)
    {
        if (OutSuggestedFault != nullptr)
        {
            *OutSuggestedFault = Fault;
        }
    };

    ULBSupportRobotAuthorityRegistryV002* Registry = GetAuthorityRegistry();
    if (Registry == nullptr || !ActiveWorkGrant.IsComplete())
    {
        SetSuggestedFault(ELBMaintenanceRobotFaultV002::F15_ExclusionZoneIntrusion);
        OutFailure = TEXT("Required MR01 work authority is absent.");
        return false;
    }
    if (!ActiveToolProof.IsComplete())
    {
        SetSuggestedFault(ELBMaintenanceRobotFaultV002::F05_ToolNotSeated);
        OutFailure = TEXT("Required MR01 tool-coupling proof is absent.");
        return false;
    }
    const bool bHasOutriggerProof = ActiveOutriggerProof.HasFiniteFourLoads();
    if (bRequireOutriggerProof && !bHasOutriggerProof)
    {
        SetSuggestedFault(ELBMaintenanceRobotFaultV002::F12_OutriggerNotDeployed);
        OutFailure = TEXT("Required MR01 four-outrigger proof is absent.");
        return false;
    }

    FLBTrustedWorkAuthorityV002 CurrentWork;
    FLBTrustedToolCouplingProofV002 CurrentTool;
    FLBTrustedOutriggerProofV002 CurrentOutriggers;
    if (!Registry->RevalidateWorkAuthority(
        ActiveWorkGrant, GetOwner(), CurrentWork, OutFailure))
    {
        if (CurrentWork.bPhysicalLOTORequired && !CurrentWork.bPhysicalLOTOValid)
        {
            SetSuggestedFault(ELBMaintenanceRobotFaultV002::F14_LOTOStatusInvalid);
        }
        else if ((CurrentWork.bCellPermissionRequired && !CurrentWork.bCellPermissionGranted)
            || (CurrentWork.bPlayerAuthorisationRequired
                && !CurrentWork.bPlayerAuthorisationGranted))
        {
            SetSuggestedFault(ELBMaintenanceRobotFaultV002::F13_CellAccessNotAuthorised);
        }
        else
        {
            SetSuggestedFault(ELBMaintenanceRobotFaultV002::F15_ExclusionZoneIntrusion);
        }
        return false;
    }
    if (!Registry->RevalidateToolCouplingProof(
        ActiveToolProof, GetOwner(), CurrentTool, OutFailure))
    {
        SetSuggestedFault(ELBMaintenanceRobotFaultV002::F05_ToolNotSeated);
        return false;
    }
    if (bHasOutriggerProof && !Registry->RevalidateOutriggerProof(
        ActiveOutriggerProof, GetOwner(), CurrentOutriggers, OutFailure))
    {
        SetSuggestedFault(ELBMaintenanceRobotFaultV002::F12_OutriggerNotDeployed);
        return false;
    }
    if (CurrentTool.ToolMassKilograms + CurrentWork.HandledPayloadMassKilograms
        > MaximumArmPayloadIncludingToolKilograms)
    {
        SetSuggestedFault(ELBMaintenanceRobotFaultV002::F11_ManipulatorOverload);
        OutFailure = TEXT("Revalidated tool plus payload exceeds the 25 kg arm rating.");
        return false;
    }
    ActiveWorkGrant = CurrentWork;
    ActiveToolProof = CurrentTool;
    if (bHasOutriggerProof)
    {
        ActiveOutriggerProof = CurrentOutriggers;
    }
    OutFailure.Reset();
    return true;
}
