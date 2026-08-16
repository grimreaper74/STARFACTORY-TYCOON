#include "LBMaintenanceAMR.h"

#include "Components/BoxComponent.h"
#include "Components/PoseableMeshComponent.h"
#include "Components/SceneComponent.h"
#include "Components/SpotLightComponent.h"
#include "Components/StaticMeshComponent.h"

ALBMaintenanceAMR::ALBMaintenanceAMR()
{
    VariantId = TEXT("LB-MR01");
    CollisionRoot->SetBoxExtent(FVector(77.5f, 46.5f, 62.5f));
    RobotVisualRoot->SetRelativeLocation(FVector(0.0f, 0.0f, -62.5f));

    CurrentJointDegrees = {180.0f, -75.0f, 150.0f, 0.0f, 120.0f, 0.0f};
    TargetJointDegrees = CurrentJointDegrees;
    OutriggerFootLoadsKilograms = {0.0f, 0.0f, 0.0f, 0.0f};
    ToolRackInventory = {
        ELBMaintenanceTool::T1_InspectionHead,
        ELBMaintenanceTool::T2_ConditionProbe,
        ELBMaintenanceTool::T3_Lubrication,
        ELBMaintenanceTool::T4_Cleaning,
        ELBMaintenanceTool::T5_ServiceGripper,
        ELBMaintenanceTool::T6_TorqueTool,
        ELBMaintenanceTool::T7_FluidLeak,
        ELBMaintenanceTool::T8_ModuleExchange};

    USceneComponent* SuspFL = CreateContractPivot(TEXT("PVT_Susp_FL"), RobotVisualRoot, FVector(50.0f, -40.5f, 25.0f));
    USceneComponent* SuspFR = CreateContractPivot(TEXT("PVT_Susp_FR"), RobotVisualRoot, FVector(50.0f, 40.5f, 25.0f));
    USceneComponent* SuspRL = CreateContractPivot(TEXT("PVT_Susp_RL"), RobotVisualRoot, FVector(-50.0f, -40.5f, 25.0f));
    USceneComponent* SuspRR = CreateContractPivot(TEXT("PVT_Susp_RR"), RobotVisualRoot, FVector(-50.0f, 40.5f, 25.0f));
    CreateContractPivot(TEXT("PVT_Wheel_FL"), SuspFL, FVector(0.0f, 0.0f, -8.0f));
    CreateContractPivot(TEXT("PVT_Wheel_FR"), SuspFR, FVector(0.0f, 0.0f, -8.0f));
    CreateContractPivot(TEXT("PVT_Wheel_RL"), SuspRL, FVector(0.0f, 0.0f, -8.0f));
    CreateContractPivot(TEXT("PVT_Wheel_RR"), SuspRR, FVector(0.0f, 0.0f, -8.0f));

    USceneComponent* OutFL = CreateContractPivot(TEXT("PVT_Outrigger_FL_Extend"), RobotVisualRoot, FVector(43.0f, -43.0f, 22.0f));
    USceneComponent* OutFR = CreateContractPivot(TEXT("PVT_Outrigger_FR_Extend"), RobotVisualRoot, FVector(43.0f, 43.0f, 22.0f));
    USceneComponent* OutRL = CreateContractPivot(TEXT("PVT_Outrigger_RL_Extend"), RobotVisualRoot, FVector(-43.0f, -43.0f, 22.0f));
    USceneComponent* OutRR = CreateContractPivot(TEXT("PVT_Outrigger_RR_Extend"), RobotVisualRoot, FVector(-43.0f, 43.0f, 22.0f));
    CreateContractPivot(TEXT("PVT_Outrigger_FL_Drop"), OutFL, FVector(0.0f, 0.0f, -6.0f));
    CreateContractPivot(TEXT("PVT_Outrigger_FR_Drop"), OutFR, FVector(0.0f, 0.0f, -6.0f));
    CreateContractPivot(TEXT("PVT_Outrigger_RL_Drop"), OutRL, FVector(0.0f, 0.0f, -6.0f));
    CreateContractPivot(TEXT("PVT_Outrigger_RR_Drop"), OutRR, FVector(0.0f, 0.0f, -6.0f));

    USceneComponent* ArmLift = CreateContractPivot(TEXT("PVT_ArmLift"), RobotVisualRoot, FVector(10.0f, 0.0f, 66.0f));
    USceneComponent* ArmJ1 = CreateContractPivot(TEXT("PVT_ArmJ1"), ArmLift, FVector(0.0f, 0.0f, 10.0f));
    USceneComponent* ArmJ2 = CreateContractPivot(TEXT("PVT_ArmJ2"), ArmJ1, FVector(0.0f, 0.0f, 14.0f));
    USceneComponent* ArmJ3 = CreateContractPivot(TEXT("PVT_ArmJ3"), ArmJ2, FVector(55.0f, 0.0f, 0.0f));
    USceneComponent* ArmJ4 = CreateContractPivot(TEXT("PVT_ArmJ4"), ArmJ3, FVector(50.0f, 0.0f, 0.0f));
    USceneComponent* ArmJ5 = CreateContractPivot(TEXT("PVT_ArmJ5"), ArmJ4, FVector(20.0f, 0.0f, 0.0f));
    USceneComponent* ArmJ6 = CreateContractPivot(TEXT("PVT_ArmJ6"), ArmJ5, FVector(15.0f, 0.0f, 0.0f));
    USceneComponent* ToolClamp = CreateContractPivot(TEXT("PVT_ToolClamp"), ArmJ6, FVector(10.0f, 0.0f, 0.0f));

    ToolMountSocket = CreateDefaultSubobject<USceneComponent>(TEXT("SCK_ToolCoupler"));
    ToolMountSocket->SetupAttachment(ToolClamp);
    ToolCentrePointSocket = CreateDefaultSubobject<USceneComponent>(TEXT("SCK_ArmTCP"));
    ToolCentrePointSocket->SetupAttachment(ToolMountSocket);
    ToolCentrePointSocket->SetRelativeLocation(FVector(30.0f, 0.0f, 0.0f));

    ToolTaskWorkLight = CreateDefaultSubobject<USpotLightComponent>(TEXT("LENS_MR01_TOOL_TASK_WORKLIGHT"));
    // The presentation arm is a poseable mesh, so the native contract pivots do
    // not provide a truthful runtime TCP transform. Keep this real task lamp on
    // the upper chassis until the arm exposes a bone-attached light socket.
    ToolTaskWorkLight->SetupAttachment(RobotVisualRoot);
    ToolTaskWorkLight->SetRelativeLocation(FVector(47.0f, 0.0f, 92.0f));
    ToolTaskWorkLight->SetRelativeRotation(FRotator(-18.0f, 0.0f, 0.0f));
    ToolTaskWorkLight->SetIntensity(1350.0f);
    ToolTaskWorkLight->SetAttenuationRadius(520.0f);
    ToolTaskWorkLight->SetInnerConeAngle(22.0f);
    ToolTaskWorkLight->SetOuterConeAngle(42.0f);
    ToolTaskWorkLight->SetLightColor(FLinearColor(1.0f, 0.94f, 0.82f));
    ToolTaskWorkLight->SetCastShadows(false);
    ToolTaskWorkLight->SetVisibility(false);
    ArmParkingCradle = CreateDefaultSubobject<USceneComponent>(TEXT("SCK_ArmParkingCradle"));
    ArmParkingCradle->SetupAttachment(RobotVisualRoot);
    ArmParkingCradle->SetRelativeLocation(FVector(39.0f, 0.0f, 103.0f));

    USceneComponent* MastLift = CreateContractPivot(TEXT("PVT_MastLift"), RobotVisualRoot, FVector(-45.0f, 28.0f, 85.0f));
    USceneComponent* MastPan = CreateContractPivot(TEXT("PVT_MastPan"), MastLift, FVector(0.0f, 0.0f, 33.0f));
    CreateContractPivot(TEXT("PVT_MastTilt"), MastPan, FVector::ZeroVector);

    USceneComponent* Carousel = CreateContractPivot(TEXT("PVT_ToolCarousel"), RobotVisualRoot, FVector(-33.0f, 25.5f, 65.0f));
    for (int32 Slot = 1; Slot <= 8; ++Slot)
    {
        const FName SocketName(*FString::Printf(TEXT("SCK_ToolRack_%02d"), Slot));
        USceneComponent* Socket = CreateDefaultSubobject<USceneComponent>(SocketName);
        Socket->SetupAttachment(Carousel);
        Socket->SetRelativeLocation(FVector(0.0f, 0.0f, 21.0f));
        Socket->SetRelativeRotation(FRotator(0.0f, 180.0f, 45.0f * static_cast<float>(Slot - 1)));
        ToolRackSockets.Add(Socket);
    }

    CreateContractPivot(TEXT("PVT_PartsDrawer"), RobotVisualRoot, FVector(-15.0f, -43.0f, 58.0f));
    CreateContractPivot(TEXT("PVT_Door_Left"), RobotVisualRoot, FVector(-10.0f, -45.5f, 70.0f));
    CreateContractPivot(TEXT("PVT_Door_Right"), RobotVisualRoot, FVector(-10.0f, 45.5f, 70.0f));
    CreateContractPivot(TEXT("PVT_Door_Rear"), RobotVisualRoot, FVector(-72.0f, 0.0f, 72.0f));
    CreateContractPivot(TEXT("PVT_DockCharge_L"), RobotVisualRoot, FVector(-73.5f, -12.0f, 34.0f));
    CreateContractPivot(TEXT("PVT_DockCharge_R"), RobotVisualRoot, FVector(-73.5f, 12.0f, 34.0f));
}

void ALBMaintenanceAMR::BeginPlay()
{
    Super::BeginPlay();
    AttachPresentationComponentsToContracts();
    CachePresentationComponents();
    ApplyPresentationPose();
    ApplyToolVisualState();
}

void ALBMaintenanceAMR::AttachPresentationComponentsToContracts()
{
    static const FString Prefix(TEXT("LB.MR01.AttachTo."));
    TArray<USceneComponent*> SceneComponents;
    GetComponents(SceneComponents);

    for (USceneComponent* Component : SceneComponents)
    {
        if (!IsValid(Component))
        {
            continue;
        }
        for (const FName Tag : Component->ComponentTags)
        {
            const FString TagString = Tag.ToString();
            if (!TagString.StartsWith(Prefix))
            {
                continue;
            }
            const FName TargetName(*TagString.RightChop(Prefix.Len()));
            USceneComponent* Target = FindContractPivot(TargetName);
            if (!IsValid(Target))
            {
                for (USceneComponent* Candidate : SceneComponents)
                {
                    if (!IsValid(Candidate))
                    {
                        continue;
                    }
                    FString CandidateName = Candidate->GetName();
                    CandidateName.RemoveFromEnd(TEXT("_0"));
                    CandidateName.RemoveFromEnd(TEXT("_GEN_VARIABLE"));
                    if (CandidateName == TargetName.ToString())
                    {
                        Target = Candidate;
                        break;
                    }
                }
            }
            if (IsValid(Target) && Target != Component)
            {
                Component->AttachToComponent(Target, FAttachmentTransformRules::KeepWorldTransform);
            }
            break;
        }
    }
}

void ALBMaintenanceAMR::Tick(float DeltaSeconds)
{
    Super::Tick(DeltaSeconds);
    // Blueprint SCS components can finish registration after native BeginPlay
    // in commandlet, streamed and reinstanced worlds. Bind lazily once their
    // tagged presentation is actually present.
    if (!IsValid(ArmPoseableVisual))
    {
        AttachPresentationComponentsToContracts();
        CachePresentationComponents();
        ApplyToolVisualState();
    }
    ApplyArmPose(DeltaSeconds);
    ApplyOutriggerPose(DeltaSeconds);
    ApplyMastPose();
    ApplyPresentationPose();
}

void ALBMaintenanceAMR::UpdateVariantWorkLights()
{
    if (!ToolTaskWorkLight)
    {
        return;
    }

    const bool bTaskLightOn = RobotState == ELBSupportRobotState::Inspecting
        || RobotState == ELBSupportRobotState::Diagnosing
        || RobotState == ELBSupportRobotState::LightService
        || RobotState == ELBSupportRobotState::Lubricating
        || RobotState == ELBSupportRobotState::Cleaning
        || RobotState == ELBSupportRobotState::DeliveringParts
        || RobotState == ELBSupportRobotState::ModuleExchange
        || RobotState == ELBSupportRobotState::Verifying;
    ToolTaskWorkLight->SetVisibility(bTaskLightOn, true);
}

void ALBMaintenanceAMR::SetTravelInterlocks(bool bArmIsParked, bool bMastIsStowed, bool bMastTravelIsApproved,
    bool bAreAllOutriggersStowed, bool bAllDoorsClosed, bool bDrawerClosed, bool bPayloadIsSecured)
{
    bArmParked = bArmIsParked && IsArmAtParkedPose();
    bMastStowed = bMastIsStowed;
    bMastTravelApproved = bMastTravelIsApproved;
    bAllOutriggersStowed = bAreAllOutriggersStowed;
    bDoorsClosed = bAllDoorsClosed;
    bPartsDrawerClosed = bDrawerClosed;
    bPayloadSecured = bPayloadIsSecured;

    if (HasRouteAuthority())
    {
        FText Reason;
        if (!HasVariantTravelPermissives(Reason))
        {
            RaiseCommonFault(ELBSupportRobotFault::VariantInterlockOpen, Reason.ToString());
        }
    }
}

void ALBMaintenanceAMR::SetWorkPermissives(FName CertifiedWorkPointId, FName PermitId, bool bParkingBrakeIsApplied,
    bool bExclusionZoneIsReserved, bool bNoSuspendedLoadZone, bool bTaskAuthorityIsValid,
    bool bCellPermissionIsGranted, bool bPlayerAuthorisationIsGranted, bool bLOTOIsValid)
{
    WorkPointId = CertifiedWorkPointId;
    ActivePermitId = PermitId;
    bParkingBrakeApplied = bParkingBrakeIsApplied;
    bExclusionZoneReserved = bExclusionZoneIsReserved;
    bOutsideSuspendedLoadZone = bNoSuspendedLoadZone;
    bTaskAuthorityValid = bTaskAuthorityIsValid;
    bCellPermissionGranted = bCellPermissionIsGranted;
    bPlayerAuthorisationGranted = bPlayerAuthorisationIsGranted;
    bLOTOValid = bLOTOIsValid;

    if (bArmMotionActive && (!bExclusionZoneReserved || !bTaskAuthorityValid || !bCellPermissionGranted))
    {
        RaiseMaintenanceFault(ELBMaintenanceAMRFault::F15_ExclusionZoneIntrusion,
            TEXT("Arm authority or the reserved exclusion zone was lost during motion."));
    }
}

bool ALBMaintenanceAMR::SetOutriggersDeployed(bool bDeploy, const TArray<float>& FootLoadsKilograms)
{
    if (HasRouteAuthority() || bArmMotionActive)
    {
        return false;
    }
    if (bDeploy)
    {
        if (!bParkingBrakeApplied || WorkPointId.IsNone() || !bExclusionZoneReserved || !AreFootLoadsProved(FootLoadsKilograms))
        {
            RaiseMaintenanceFault(ELBMaintenanceAMRFault::F12_OutriggerNotDeployed,
                TEXT("Four proved outrigger foot loads are required before arm work."));
            return false;
        }
        OutriggerFootLoadsKilograms = FootLoadsKilograms;
        bOutriggersDeployed = true;
        bAllOutriggersStowed = false;
    }
    else
    {
        if (!bArmParked)
        {
            return false;
        }
        OutriggerFootLoadsKilograms = {0.0f, 0.0f, 0.0f, 0.0f};
        bOutriggersDeployed = false;
        bAllOutriggersStowed = true;
    }
    return true;
}

bool ALBMaintenanceAMR::SetMastExtension(float ExtensionMillimetres, bool bTravelApprovedWhenExtended)
{
    if (HasRouteAuthority() || ExtensionMillimetres < 0.0f || ExtensionMillimetres > 1200.0f
        || (ExtensionMillimetres > 0.0f && !bParkingBrakeApplied))
    {
        return false;
    }
    MastExtensionMillimetres = ExtensionMillimetres;
    bMastStowed = FMath::IsNearlyZero(MastExtensionMillimetres, 0.5f);
    bMastTravelApproved = bMastStowed || bTravelApprovedWhenExtended;
    return true;
}

bool ALBMaintenanceAMR::BeginMaintenanceTask(ELBMaintenanceTask Task, FName TaskId, bool bRequiresPhysicalLOTO)
{
    if (TaskId.IsNone() || !ActiveTaskId.IsNone() || ActiveMaintenanceFault != ELBMaintenanceAMRFault::None)
    {
        return false;
    }
    bTaskRequiresPhysicalLOTO = bRequiresPhysicalLOTO;
    const ELBMaintenanceTool RequiredTool = RequiredToolForTask(Task);
    if (ActiveTool != RequiredTool || !bToolPresent || !bToolLocked)
    {
        RaiseMaintenanceFault(ELBMaintenanceAMRFault::F06_IncorrectToolSelected,
            TEXT("The task/tool identity, tool-presence and lock signals do not agree."));
        return false;
    }
    if (bTaskRequiresPhysicalLOTO && !bLOTOValid)
    {
        RaiseMaintenanceFault(ELBMaintenanceAMRFault::F14_LOTOStatusInvalid,
            TEXT("This approved task requires a human-applied and validated physical LOTO permit."));
        return false;
    }
    const ELBMaintenanceTask PreviousTask = ActiveMaintenanceTask;
    ActiveMaintenanceTask = Task;
    FText BlockingReason;
    if (!CanUseArm(BlockingReason))
    {
        ActiveMaintenanceTask = PreviousTask;
        bTaskRequiresPhysicalLOTO = false;
        return false;
    }
    ActiveTaskId = TaskId;
    SetRobotState(StateForTask(Task));
    return true;
}

bool ALBMaintenanceAMR::CompleteMaintenanceTask(FName EvidenceId)
{
    const bool bTaskState = RobotState == ELBSupportRobotState::Inspecting
        || RobotState == ELBSupportRobotState::Diagnosing
        || RobotState == ELBSupportRobotState::LightService
        || RobotState == ELBSupportRobotState::Lubricating
        || RobotState == ELBSupportRobotState::Cleaning
        || RobotState == ELBSupportRobotState::DeliveringParts
        || RobotState == ELBSupportRobotState::ModuleExchange;
    if (EvidenceId.IsNone() || ActiveTaskId.IsNone() || bArmMotionActive || !bTaskState
        || ActivePermitId.IsNone() || !bTaskAuthorityValid)
    {
        return false;
    }
    LastCompletedPermitId = ActivePermitId;
    ActiveTaskId = NAME_None;
    ActivePermitId = NAME_None;
    bTaskAuthorityValid = false;
    bCellPermissionGranted = false;
    bPlayerAuthorisationGranted = false;
    bTaskRequiresPhysicalLOTO = false;
    SetRobotState(ELBSupportRobotState::Verifying);
    SetRobotState(ELBSupportRobotState::Certified);
    return true;
}

bool ALBMaintenanceAMR::CanUseArm(FText& BlockingReason) const
{
    BlockingReason = FText::GetEmpty();
    if (!bCertified || HasRouteAuthority())
    {
        BlockingReason = FText::FromString(TEXT("MR01 must be certified and stationary."));
        return false;
    }
    if (WorkPointId.IsNone() || !bParkingBrakeApplied)
    {
        BlockingReason = FText::FromString(TEXT("A certified work point and proved parking brake are required."));
        return false;
    }
    if (!bExclusionZoneReserved || !bOutsideSuspendedLoadZone)
    {
        BlockingReason = FText::FromString(TEXT("The work exclusion zone is not reserved or intersects a suspended-load zone."));
        return false;
    }
    if (!bOutriggersDeployed || !AreFootLoadsProved(OutriggerFootLoadsKilograms))
    {
        BlockingReason = FText::FromString(TEXT("Four deployed outriggers with proved foot loads are required."));
        return false;
    }
    if (!bTaskAuthorityValid || !bCellPermissionGranted || !bPlayerAuthorisationGranted)
    {
        BlockingReason = FText::FromString(TEXT("Task, cell and player authority are not all valid."));
        return false;
    }
    if (bTaskRequiresPhysicalLOTO && !bLOTOValid)
    {
        BlockingReason = FText::FromString(TEXT("The task requires a proved automated isolation and zero-energy lock."));
        return false;
    }
    if (PendingToolRackSlot == INDEX_NONE)
    {
        const ELBMaintenanceTool RequiredTool = RequiredToolForTask(ActiveMaintenanceTask);
        if (ActiveTool != RequiredTool || !bToolPresent || !bToolLocked)
        {
            BlockingReason = FText::FromString(TEXT("Correct seated and locked task tool is not proved."));
            return false;
        }
    }
    return true;
}

bool ALBMaintenanceAMR::CommandArmPose(float LiftMillimetres, const TArray<float>& JointDegrees)
{
    FText BlockingReason;
    if (!CanUseArm(BlockingReason) || !IsJointPoseValid(LiftMillimetres, JointDegrees))
    {
        return false;
    }
    TargetArmLiftMillimetres = LiftMillimetres;
    TargetJointDegrees = JointDegrees;
    bArmMotionActive = true;
    bArmParkingCommand = false;
    bArmParked = false;
    OnArmParkedChanged.Broadcast(UnitId, bArmParked);
    return true;
}

bool ALBMaintenanceAMR::ParkArm()
{
    if (HasRouteAuthority() || !bParkingBrakeApplied || !bExclusionZoneReserved || !bTaskAuthorityValid)
    {
        return false;
    }
    TargetArmLiftMillimetres = 0.0f;
    TargetJointDegrees = {180.0f, -75.0f, 150.0f, 0.0f, 120.0f, 0.0f};
    bArmMotionActive = true;
    bArmParkingCommand = true;
    bArmParked = false;
    OnArmParkedChanged.Broadcast(UnitId, bArmParked);
    return true;
}

bool ALBMaintenanceAMR::BeginToolChange(int32 RackSlot, ELBMaintenanceTool RequestedTool)
{
    if (RackSlot < 1 || RackSlot > 8 || RequestedTool == ELBMaintenanceTool::None
        || !ToolRackInventory.IsValidIndex(RackSlot - 1) || ToolRackInventory[RackSlot - 1] != RequestedTool
        || PendingToolRackSlot != INDEX_NONE || !ActiveTaskId.IsNone())
    {
        RaiseMaintenanceFault(ELBMaintenanceAMRFault::F18_ToolRackSlotMismatch,
            TEXT("Requested tool does not match the indexed rack-slot inventory."));
        return false;
    }
    PendingToolRackSlot = RackSlot;
    PendingRequestedTool = RequestedTool;
    FText BlockingReason;
    if (!CanUseArm(BlockingReason))
    {
        PendingToolRackSlot = INDEX_NONE;
        PendingRequestedTool = ELBMaintenanceTool::None;
        return false;
    }
    ToolCarouselSlot = RackSlot;
    SetRobotState(ELBSupportRobotState::LightService);
    return true;
}

bool ALBMaintenanceAMR::CompleteToolChange(int32 RackSlot, ELBMaintenanceTool IdentifiedTool,
    bool bPresenceSignal, bool bLockSignal, float StraightWithdrawalMillimetres)
{
    if (bArmMotionActive || RackSlot != PendingToolRackSlot || IdentifiedTool != PendingRequestedTool
        || !ToolRackInventory.IsValidIndex(RackSlot - 1) || ToolRackInventory[RackSlot - 1] != IdentifiedTool)
    {
        RaiseMaintenanceFault(ELBMaintenanceAMRFault::F18_ToolRackSlotMismatch,
            TEXT("Rack occupancy, requested tool and read-back tool identity disagree."));
        return false;
    }
    if (!bPresenceSignal || !bLockSignal)
    {
        RaiseMaintenanceFault(ELBMaintenanceAMRFault::F05_ToolNotSeated,
            TEXT("The 12 mm coupling lock and tool-presence signals are not both proved."));
        return false;
    }
    if (StraightWithdrawalMillimetres < 350.0f)
    {
        RaiseMaintenanceFault(ELBMaintenanceAMRFault::F05_ToolNotSeated,
            TEXT("The required 350 mm straight rack-withdrawal clearance was not completed."));
        return false;
    }

    const ELBMaintenanceTool PreviousTool = ActiveTool;
    ToolRackInventory[RackSlot - 1] = PreviousTool;
    ActiveTool = IdentifiedTool;
    bToolPresent = true;
    bToolLocked = true;
    PendingToolRackSlot = INDEX_NONE;
    PendingRequestedTool = ELBMaintenanceTool::None;
    OnToolChanged.Broadcast(PreviousTool, ActiveTool, RackSlot);
    ApplyToolVisualState();
    return true;
}

void ALBMaintenanceAMR::RaiseMaintenanceFault(ELBMaintenanceAMRFault Fault, const FString& Detail)
{
    if (Fault == ELBMaintenanceAMRFault::None)
    {
        return;
    }
    ActiveMaintenanceFault = Fault;
    ELBSupportRobotFault CommonFault = ELBSupportRobotFault::VariantInterlockOpen;
    if (Fault == ELBMaintenanceAMRFault::F01_DirtySafetyScanner) CommonFault = ELBSupportRobotFault::SensorCoverageInvalid;
    else if (Fault == ELBMaintenanceAMRFault::F02_LostLocalisation) CommonFault = ELBSupportRobotFault::LocalisationLost;
    else if (Fault == ELBMaintenanceAMRFault::F03_LowOrDegradedBattery) CommonFault = ELBSupportRobotFault::LowBattery;
    else if (Fault == ELBMaintenanceAMRFault::F17_DockingContactsDirty) CommonFault = ELBSupportRobotFault::DockContactsDirty;
    RaiseCommonFault(CommonFault, Detail);

    if (Fault == ELBMaintenanceAMRFault::F13_CellAccessNotAuthorised) SetRobotState(ELBSupportRobotState::AccessDenied);
    else if (Fault == ELBMaintenanceAMRFault::F14_LOTOStatusInvalid) SetRobotState(ELBSupportRobotState::LOTOInvalid);
    else if (Fault == ELBMaintenanceAMRFault::F05_ToolNotSeated || Fault == ELBMaintenanceAMRFault::F06_IncorrectToolSelected
        || Fault == ELBMaintenanceAMRFault::F18_ToolRackSlotMismatch) SetRobotState(ELBSupportRobotState::ToolFault);
    else if (Fault == ELBMaintenanceAMRFault::F10_ReplacementPartMismatch) SetRobotState(ELBSupportRobotState::PartMismatch);
    else if (Fault == ELBMaintenanceAMRFault::F11_ManipulatorOverload) SetRobotState(ELBSupportRobotState::ArmOverload);
    else if (Fault == ELBMaintenanceAMRFault::F16_LeakOrContaminationDetected) SetRobotState(ELBSupportRobotState::LeakDetected);
    OnMaintenanceFault.Broadcast(Fault, Detail);
}

bool ALBMaintenanceAMR::ClearMaintenanceFault()
{
    if (ActiveMaintenanceFault == ELBMaintenanceAMRFault::None || !ClearCommonFault())
    {
        return false;
    }
    ActiveMaintenanceFault = ELBMaintenanceAMRFault::None;
    PendingToolRackSlot = INDEX_NONE;
    PendingRequestedTool = ELBMaintenanceTool::None;
    return true;
}

FLBMaintenanceAMRSaveState ALBMaintenanceAMR::CaptureSaveState() const
{
    FLBMaintenanceAMRSaveState Saved;
    Saved.Common = CaptureCommonSaveState();
    Saved.MaintenanceFault = ActiveMaintenanceFault;
    Saved.ActiveTask = ActiveMaintenanceTask;
    Saved.ActiveTool = ActiveTool;
    Saved.ToolRackInventory = ToolRackInventory;
    Saved.ArmJointDegrees = CurrentJointDegrees;
    Saved.ArmLiftMillimetres = CurrentArmLiftMillimetres;
    Saved.ToolCarouselSlot = ToolCarouselSlot;
    Saved.bToolPresent = bToolPresent;
    Saved.bToolLocked = bToolLocked;
    Saved.bArmParked = bArmParked;
    Saved.bMastStowed = bMastStowed;
    Saved.MastExtensionMillimetres = MastExtensionMillimetres;
    Saved.bOutriggersDeployed = bOutriggersDeployed;
    Saved.OutriggerFootLoadsKilograms = OutriggerFootLoadsKilograms;
    Saved.bDoorsClosed = bDoorsClosed;
    Saved.bPartsDrawerClosed = bPartsDrawerClosed;
    Saved.bPayloadSecured = bPayloadSecured;
    Saved.WorkPointId = WorkPointId;
    Saved.LastCompletedPermitId = LastCompletedPermitId;
    return Saved;
}

bool ALBMaintenanceAMR::RestoreSaveState(const FLBMaintenanceAMRSaveState& SavedState)
{
    if (SavedState.Version != 1 || SavedState.ArmJointDegrees.Num() != 6
        || SavedState.ToolRackInventory.Num() != 8 || !RestoreCommonSaveState(SavedState.Common))
    {
        return false;
    }
    ActiveMaintenanceFault = SavedState.MaintenanceFault;
    ActiveMaintenanceTask = SavedState.ActiveTask;
    ActiveTool = SavedState.ActiveTool;
    ToolRackInventory = SavedState.ToolRackInventory;
    CurrentJointDegrees = SavedState.ArmJointDegrees;
    TargetJointDegrees = CurrentJointDegrees;
    CurrentArmLiftMillimetres = FMath::Clamp(SavedState.ArmLiftMillimetres, 0.0f, 400.0f);
    TargetArmLiftMillimetres = CurrentArmLiftMillimetres;
    ToolCarouselSlot = FMath::Clamp(SavedState.ToolCarouselSlot, 1, 8);
    bToolPresent = SavedState.bToolPresent;
    bToolLocked = SavedState.bToolLocked;
    bArmParked = SavedState.bArmParked;
    MastExtensionMillimetres = FMath::Clamp(SavedState.MastExtensionMillimetres, 0.0f, 1200.0f);
    bMastStowed = FMath::IsNearlyZero(MastExtensionMillimetres, 0.5f);
    bOutriggersDeployed = SavedState.bOutriggersDeployed;
    OutriggerFootLoadsKilograms = SavedState.OutriggerFootLoadsKilograms.Num() == 4
        ? SavedState.OutriggerFootLoadsKilograms : TArray<float>{0.0f, 0.0f, 0.0f, 0.0f};
    OutriggerDeploymentAlpha = bOutriggersDeployed ? 1.0f : 0.0f;
    bAllOutriggersStowed = !bOutriggersDeployed;
    bDoorsClosed = SavedState.bDoorsClosed;
    bPartsDrawerClosed = SavedState.bPartsDrawerClosed;
    bPayloadSecured = SavedState.bPayloadSecured;
    WorkPointId = SavedState.WorkPointId;
    LastCompletedPermitId = SavedState.LastCompletedPermitId;

    // Work permits and powered motion are session authority, never save authority.
    ActivePermitId = NAME_None;
    bParkingBrakeApplied = false;
    bExclusionZoneReserved = false;
    bOutsideSuspendedLoadZone = false;
    bTaskAuthorityValid = false;
    bCellPermissionGranted = false;
    bPlayerAuthorisationGranted = false;
    bLOTOValid = false;
    bTaskRequiresPhysicalLOTO = false;
    bArmMotionActive = false;
    bArmParkingCommand = false;
    PendingToolRackSlot = INDEX_NONE;
    PendingRequestedTool = ELBMaintenanceTool::None;
    ApplyArmPose(0.0f);
    ApplyOutriggerPose(0.0f);
    ApplyMastPose();
    ApplyPresentationPose();
    ApplyToolVisualState();
    return true;
}

bool ALBMaintenanceAMR::HasVariantTravelPermissives(FText& BlockingReason) const
{
    BlockingReason = FText::GetEmpty();
    if (ActiveMaintenanceFault != ELBMaintenanceAMRFault::None)
    {
        BlockingReason = FText::FromString(TEXT("An MR01 maintenance fault is active."));
        return false;
    }
    if (!bArmParked || bArmMotionActive)
    {
        BlockingReason = FText::FromString(TEXT("Six-axis arm parking is not proved."));
        return false;
    }
    if (!bMastStowed && !bMastTravelApproved)
    {
        BlockingReason = FText::FromString(TEXT("Inspection mast is not stowed or approved for restricted travel."));
        return false;
    }
    if (!bAllOutriggersStowed || bOutriggersDeployed)
    {
        BlockingReason = FText::FromString(TEXT("All four outriggers must be fully stowed."));
        return false;
    }
    if (!bDoorsClosed || !bPartsDrawerClosed || !bPayloadSecured)
    {
        BlockingReason = FText::FromString(TEXT("Doors, parts drawer and payload must be secured."));
        return false;
    }
    if (bToolPresent && !bToolLocked)
    {
        BlockingReason = FText::FromString(TEXT("Present tool is not mechanically locked."));
        return false;
    }
    return true;
}

float ALBMaintenanceAMR::GetMaximumSpeedCentimetresPerSecond(ELBRouteSpeedClass SpeedClass, bool bEmergencyDispatch) const
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
        return bEmergencyDispatch && bArmParked && bMastStowed && bAllOutriggersStowed
            && bDoorsClosed && bPartsDrawerClosed && bPayloadSecured ? 200.0f : 120.0f;
    case ELBRouteSpeedClass::NormalTransit:
    default:
        return 120.0f;
    }
}

void ALBMaintenanceAMR::OnEnteredSafeStop()
{
    bArmMotionActive = false;
    bArmParkingCommand = false;
}

USceneComponent* ALBMaintenanceAMR::CreateContractPivot(const TCHAR* Name, USceneComponent* Parent, const FVector& RelativeLocation)
{
    USceneComponent* Pivot = CreateDefaultSubobject<USceneComponent>(FName(Name));
    Pivot->SetupAttachment(Parent);
    Pivot->SetRelativeLocation(RelativeLocation);
    ContractPivots.Add(Pivot);
    return Pivot;
}

USceneComponent* ALBMaintenanceAMR::FindContractPivot(FName PivotName) const
{
    for (USceneComponent* Pivot : ContractPivots)
    {
        if (IsValid(Pivot) && Pivot->GetFName() == PivotName)
        {
            return Pivot;
        }
    }
    return nullptr;
}

ELBMaintenanceTool ALBMaintenanceAMR::RequiredToolForTask(ELBMaintenanceTask Task) const
{
    switch (Task)
    {
    case ELBMaintenanceTask::Inspection: return ELBMaintenanceTool::T1_InspectionHead;
    case ELBMaintenanceTask::Diagnosis: return ELBMaintenanceTool::T2_ConditionProbe;
    case ELBMaintenanceTask::Lubrication: return ELBMaintenanceTool::T3_Lubrication;
    case ELBMaintenanceTask::SensorCleaning: return ELBMaintenanceTool::T4_Cleaning;
    case ELBMaintenanceTask::PartsDelivery: return ELBMaintenanceTool::T5_ServiceGripper;
    case ELBMaintenanceTask::ApprovedFastenerService: return ELBMaintenanceTool::T6_TorqueTool;
    case ELBMaintenanceTask::LeakClassification: return ELBMaintenanceTool::T7_FluidLeak;
    case ELBMaintenanceTask::ApprovedModuleExchange: return ELBMaintenanceTool::T8_ModuleExchange;
    default: return ELBMaintenanceTool::None;
    }
}

ELBSupportRobotState ALBMaintenanceAMR::StateForTask(ELBMaintenanceTask Task) const
{
    switch (Task)
    {
    case ELBMaintenanceTask::Inspection: return ELBSupportRobotState::Inspecting;
    case ELBMaintenanceTask::Diagnosis: return ELBSupportRobotState::Diagnosing;
    case ELBMaintenanceTask::Lubrication: return ELBSupportRobotState::Lubricating;
    case ELBMaintenanceTask::SensorCleaning: return ELBSupportRobotState::Cleaning;
    case ELBMaintenanceTask::PartsDelivery: return ELBSupportRobotState::DeliveringParts;
    case ELBMaintenanceTask::ApprovedModuleExchange: return ELBSupportRobotState::ModuleExchange;
    default: return ELBSupportRobotState::LightService;
    }
}

bool ALBMaintenanceAMR::IsArmAtParkedPose() const
{
    if (CurrentJointDegrees.Num() != 6 || !FMath::IsNearlyZero(CurrentArmLiftMillimetres, 1.0f))
    {
        return false;
    }
    static const float ParkedPose[] = {180.0f, -75.0f, 150.0f, 0.0f, 120.0f, 0.0f};
    for (int32 Joint = 0; Joint < 6; ++Joint)
    {
        if (!FMath::IsNearlyEqual(CurrentJointDegrees[Joint], ParkedPose[Joint], 1.0f))
        {
            return false;
        }
    }
    return true;
}

bool ALBMaintenanceAMR::IsJointPoseValid(float LiftMillimetres, const TArray<float>& JointDegrees) const
{
    if (LiftMillimetres < 0.0f || LiftMillimetres > 400.0f || JointDegrees.Num() != 6)
    {
        return false;
    }
    return JointDegrees[0] >= -180.0f && JointDegrees[0] <= 180.0f
        && JointDegrees[1] >= -95.0f && JointDegrees[1] <= 120.0f
        && JointDegrees[2] >= -145.0f && JointDegrees[2] <= 150.0f
        && JointDegrees[3] >= -200.0f && JointDegrees[3] <= 200.0f
        && JointDegrees[4] >= -120.0f && JointDegrees[4] <= 120.0f;
    // J6 is continuous by contract and is deliberately not range-clamped.
}

bool ALBMaintenanceAMR::AreFootLoadsProved(const TArray<float>& FootLoadsKilograms) const
{
    if (FootLoadsKilograms.Num() != 4)
    {
        return false;
    }
    for (const float Load : FootLoadsKilograms)
    {
        if (Load < 25.0f)
        {
            return false;
        }
    }
    return true;
}

void ALBMaintenanceAMR::ApplyArmPose(float DeltaSeconds)
{
    if (CurrentJointDegrees.Num() != 6 || TargetJointDegrees.Num() != 6)
    {
        return;
    }
    static const float JointSpeeds[] = {90.0f, 75.0f, 90.0f, 120.0f, 120.0f, 150.0f};
    bool bReached = true;
    CurrentArmLiftMillimetres = FMath::FInterpConstantTo(CurrentArmLiftMillimetres, TargetArmLiftMillimetres, DeltaSeconds, 60.0f);
    bReached &= FMath::IsNearlyEqual(CurrentArmLiftMillimetres, TargetArmLiftMillimetres, 0.1f);
    for (int32 Joint = 0; Joint < 6; ++Joint)
    {
        CurrentJointDegrees[Joint] = FMath::FInterpConstantTo(CurrentJointDegrees[Joint], TargetJointDegrees[Joint], DeltaSeconds, JointSpeeds[Joint]);
        bReached &= FMath::IsNearlyEqual(CurrentJointDegrees[Joint], TargetJointDegrees[Joint], 0.1f);
    }

    if (USceneComponent* Pivot = FindContractPivot(TEXT("PVT_ArmLift")))
        Pivot->SetRelativeLocation(FVector(10.0f, 0.0f, 66.0f + CurrentArmLiftMillimetres / 10.0f));
    if (USceneComponent* Pivot = FindContractPivot(TEXT("PVT_ArmJ1")))
        Pivot->SetRelativeRotation(FRotator(0.0f, CurrentJointDegrees[0], 0.0f));
    if (USceneComponent* Pivot = FindContractPivot(TEXT("PVT_ArmJ2")))
        Pivot->SetRelativeRotation(FRotator(CurrentJointDegrees[1], 0.0f, 0.0f));
    if (USceneComponent* Pivot = FindContractPivot(TEXT("PVT_ArmJ3")))
        Pivot->SetRelativeRotation(FRotator(CurrentJointDegrees[2], 0.0f, 0.0f));
    if (USceneComponent* Pivot = FindContractPivot(TEXT("PVT_ArmJ4")))
        Pivot->SetRelativeRotation(FRotator(0.0f, 0.0f, CurrentJointDegrees[3]));
    if (USceneComponent* Pivot = FindContractPivot(TEXT("PVT_ArmJ5")))
        Pivot->SetRelativeRotation(FRotator(CurrentJointDegrees[4], 0.0f, 0.0f));
    if (USceneComponent* Pivot = FindContractPivot(TEXT("PVT_ArmJ6")))
        Pivot->SetRelativeRotation(FRotator(0.0f, 0.0f, CurrentJointDegrees[5]));
    if (USceneComponent* Pivot = FindContractPivot(TEXT("PVT_ToolClamp")))
        Pivot->SetRelativeLocation(FVector(bToolLocked ? 10.0f : 11.2f, 0.0f, 0.0f));

    if (bArmMotionActive && bReached)
    {
        bArmMotionActive = false;
        if (bArmParkingCommand)
        {
            bArmParkingCommand = false;
            bArmParked = true;
            OnArmParkedChanged.Broadcast(UnitId, bArmParked);
        }
    }
}

void ALBMaintenanceAMR::ApplyOutriggerPose(float DeltaSeconds)
{
    const float Target = bOutriggersDeployed ? 1.0f : 0.0f;
    OutriggerDeploymentAlpha = FMath::FInterpConstantTo(OutriggerDeploymentAlpha, Target, DeltaSeconds, 0.8f);
    const TCHAR* ExtendNames[] = {
        TEXT("PVT_Outrigger_FL_Extend"), TEXT("PVT_Outrigger_FR_Extend"),
        TEXT("PVT_Outrigger_RL_Extend"), TEXT("PVT_Outrigger_RR_Extend")};
    const TCHAR* DropNames[] = {
        TEXT("PVT_Outrigger_FL_Drop"), TEXT("PVT_Outrigger_FR_Drop"),
        TEXT("PVT_Outrigger_RL_Drop"), TEXT("PVT_Outrigger_RR_Drop")};
    const float X[] = {43.0f, 43.0f, -43.0f, -43.0f};
    const float Y[] = {-43.0f, 43.0f, -43.0f, 43.0f};
    for (int32 Index = 0; Index < 4; ++Index)
    {
        const float Side = Y[Index] < 0.0f ? -1.0f : 1.0f;
        if (USceneComponent* Pivot = FindContractPivot(FName(ExtendNames[Index])))
            Pivot->SetRelativeLocation(FVector(X[Index], Y[Index] + Side * 18.0f * OutriggerDeploymentAlpha, 22.0f));
        if (USceneComponent* Pivot = FindContractPivot(FName(DropNames[Index])))
            Pivot->SetRelativeLocation(FVector(0.0f, 0.0f, -6.0f - 12.0f * OutriggerDeploymentAlpha));
    }
}

void ALBMaintenanceAMR::ApplyMastPose()
{
    if (USceneComponent* Pivot = FindContractPivot(TEXT("PVT_MastLift")))
        Pivot->SetRelativeLocation(FVector(-45.0f, 28.0f, 85.0f + MastExtensionMillimetres / 10.0f));
    if (USceneComponent* Carousel = FindContractPivot(TEXT("PVT_ToolCarousel")))
        Carousel->SetRelativeRotation(FRotator(0.0f, 0.0f, 45.0f * static_cast<float>(ToolCarouselSlot - 1)));
}

void ALBMaintenanceAMR::CachePresentationComponents()
{
    ArmPoseableVisual = nullptr;
    ArmLiftSleeveVisual = nullptr;
    ArmLiftCarriageVisual = nullptr;
    ArmReferenceComponentTransforms.Reset();

    TArray<UPoseableMeshComponent*> PoseableComponents;
    GetComponents(PoseableComponents);
    for (UPoseableMeshComponent* Component : PoseableComponents)
    {
        if (IsValid(Component) && Component->ComponentHasTag(TEXT("LB.MR01.ArmPoseable")))
        {
            ArmPoseableVisual = Component;
            break;
        }
    }

    TArray<UStaticMeshComponent*> StaticComponents;
    GetComponents(StaticComponents);
    for (UStaticMeshComponent* Component : StaticComponents)
    {
        if (!IsValid(Component))
        {
            continue;
        }
        if (Component->ComponentHasTag(TEXT("LB.MR01.ArmLiftSleeve")))
        {
            ArmLiftSleeveVisual = Component;
        }
        else if (Component->ComponentHasTag(TEXT("LB.MR01.ArmLiftCarriage")))
        {
            ArmLiftCarriageVisual = Component;
        }
    }

    if (IsValid(ArmPoseableVisual))
    {
        static const FName BoneNames[] = {
            TEXT("root"), TEXT("lift"), TEXT("j1_base"), TEXT("j2_shoulder"), TEXT("j3_elbow"),
            TEXT("j4_wrist_roll"), TEXT("j5_wrist_pitch"), TEXT("j6_tool_roll"),
            TEXT("tool_coupler"), TEXT("tcp")};
        for (const FName BoneName : BoneNames)
        {
            if (ArmPoseableVisual->GetBoneIndex(BoneName) != INDEX_NONE)
            {
                ArmReferenceComponentTransforms.Add(
                    BoneName,
                    ArmPoseableVisual->GetBoneTransformByName(BoneName, EBoneSpaces::ComponentSpace));
            }
        }
    }
}

void ALBMaintenanceAMR::ApplyPresentationPose()
{
    // The connected two-stage lift remains authoritative even while the
    // poseable skeletal reference is still initializing.
    if (IsValid(ArmLiftSleeveVisual))
    {
        ArmLiftSleeveVisual->SetRelativeLocation(FVector(0.0f, 0.0f, CurrentArmLiftMillimetres / 20.0f));
    }
    if (IsValid(ArmLiftCarriageVisual))
    {
        ArmLiftCarriageVisual->SetRelativeLocation(FVector(0.0f, 0.0f, CurrentArmLiftMillimetres / 10.0f));
    }

    if (!IsValid(ArmPoseableVisual) || CurrentJointDegrees.Num() != 6)
    {
        return;
    }
    if (ArmReferenceComponentTransforms.Num() == 0)
    {
        CachePresentationComponents();
        if (!IsValid(ArmPoseableVisual))
        {
            return;
        }
    }

    TMap<FName, FTransform> PosedComponentTransforms;
    if (const FTransform* RootReference = ArmReferenceComponentTransforms.Find(TEXT("root")))
    {
        PosedComponentTransforms.Add(TEXT("root"), *RootReference);
        ArmPoseableVisual->SetBoneTransformByName(TEXT("root"), *RootReference, EBoneSpaces::ComponentSpace);
    }

    auto ApplyBone = [this, &PosedComponentTransforms](const FName BoneName, const FName ParentName,
        const FRotator DeltaRotation, const FVector ParentSpaceTranslationOffset)
    {
        const FTransform* Reference = ArmReferenceComponentTransforms.Find(BoneName);
        const FTransform* ReferenceParent = ArmReferenceComponentTransforms.Find(ParentName);
        const FTransform* PosedParent = PosedComponentTransforms.Find(ParentName);
        if (!Reference || !ReferenceParent || !PosedParent)
        {
            return;
        }
        FTransform Local = Reference->GetRelativeTransform(*ReferenceParent);
        Local.SetRotation(DeltaRotation.Quaternion() * Local.GetRotation());
        Local.AddToTranslation(ParentSpaceTranslationOffset);
        const FTransform ComponentTransform = Local * *PosedParent;
        PosedComponentTransforms.Add(BoneName, ComponentTransform);
        ArmPoseableVisual->SetBoneTransformByName(BoneName, ComponentTransform, EBoneSpaces::ComponentSpace);
    };

    // Supplier J1 command 180 degrees is the visual zero published by the Pro
    // pack. The remaining commands map directly to the CFR joint axes.
    // Lift travel is authored in robot/component Z, not the supplier armature's
    // scaled and rotated parent space. Applying it directly in component space
    // prevents the FBX root scale from multiplying a 400 mm command.
    if (const FTransform* LiftReference = ArmReferenceComponentTransforms.Find(TEXT("lift")))
    {
        FTransform LiftTransform = *LiftReference;
        LiftTransform.AddToTranslation(FVector(0.0f, 0.0f, CurrentArmLiftMillimetres / 10.0f));
        PosedComponentTransforms.Add(TEXT("lift"), LiftTransform);
        ArmPoseableVisual->SetBoneTransformByName(TEXT("lift"), LiftTransform, EBoneSpaces::ComponentSpace);
    }
    // The authored arm links run along local -Y. In Unreal, FRotator Pitch is
    // rotation about Y, Roll is rotation about X, and Yaw is rotation about Z.
    // Therefore shoulder/elbow/wrist pitch use Roll (X), while the two axial
    // wrist rolls use Pitch (Y). The previous mapping used Pitch for J2/J3/J5
    // and Roll for J4/J6, leaving the arm flat in plan instead of folding it.
    ApplyBone(TEXT("j1_base"), TEXT("lift"), FRotator(0.0f, CurrentJointDegrees[0] - 180.0f, 0.0f), FVector::ZeroVector);
    ApplyBone(TEXT("j2_shoulder"), TEXT("j1_base"), FRotator(0.0f, 0.0f, CurrentJointDegrees[1]), FVector::ZeroVector);
    ApplyBone(TEXT("j3_elbow"), TEXT("j2_shoulder"), FRotator(0.0f, 0.0f, CurrentJointDegrees[2]), FVector::ZeroVector);
    ApplyBone(TEXT("j4_wrist_roll"), TEXT("j3_elbow"), FRotator(0.0f, CurrentJointDegrees[3], 0.0f), FVector::ZeroVector);
    ApplyBone(TEXT("j5_wrist_pitch"), TEXT("j4_wrist_roll"), FRotator(0.0f, 0.0f, CurrentJointDegrees[4]), FVector::ZeroVector);
    ApplyBone(TEXT("j6_tool_roll"), TEXT("j5_wrist_pitch"), FRotator(0.0f, CurrentJointDegrees[5], 0.0f), FVector::ZeroVector);
    ApplyBone(TEXT("tool_coupler"), TEXT("j6_tool_roll"), FRotator::ZeroRotator, FVector::ZeroVector);
    ApplyBone(TEXT("tcp"), TEXT("tool_coupler"), FRotator::ZeroRotator, FVector::ZeroVector);
    ArmPoseableVisual->RefreshBoneTransforms();
}

void ALBMaintenanceAMR::ApplyToolVisualState()
{
    TArray<UStaticMeshComponent*> StaticComponents;
    GetComponents(StaticComponents);
    for (UStaticMeshComponent* Component : StaticComponents)
    {
        if (!IsValid(Component))
        {
            continue;
        }
        for (int32 ToolIndex = 0; ToolIndex < 8; ++ToolIndex)
        {
            const int32 ToolNumber = ToolIndex + 1;
            const FName StoredTag(*FString::Printf(TEXT("LB.MR01.Tool.T%d.Stored"), ToolNumber));
            const FName EquippedTag(*FString::Printf(TEXT("LB.MR01.Tool.T%d.Equipped"), ToolNumber));
            const ELBMaintenanceTool Tool = static_cast<ELBMaintenanceTool>(ToolNumber);
            if (Component->ComponentHasTag(StoredTag))
            {
                const bool bStored = ToolRackInventory.IsValidIndex(ToolIndex) && ToolRackInventory[ToolIndex] == Tool;
                Component->SetVisibility(bStored, true);
                Component->SetHiddenInGame(!bStored, true);
            }
            else if (Component->ComponentHasTag(EquippedTag))
            {
                if (IsValid(ArmPoseableVisual)
                    && (Component->GetAttachParent() != ArmPoseableVisual
                        || Component->GetAttachSocketName() != TEXT("tool_coupler")))
                {
                    Component->AttachToComponent(ArmPoseableVisual,
                        FAttachmentTransformRules::SnapToTargetNotIncludingScale, TEXT("tool_coupler"));
                }
                const bool bEquipped = ActiveTool == Tool && bToolPresent && bToolLocked;
                Component->SetVisibility(bEquipped, true);
                Component->SetHiddenInGame(!bEquipped, true);
            }
        }
    }
}
