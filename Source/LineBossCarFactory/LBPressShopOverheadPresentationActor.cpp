#include "LBPressShopOverheadPresentationActor.h"

#include "Components/RectLightComponent.h"
#include "Components/SceneComponent.h"
#include "Engine/World.h"
#include "EngineUtils.h"
#include "LBOneFactoryPressStarterLayout.h"
#include "LBOneFactoryProductionFlow.h"
#include "LBOneFactoryRuntimeCoordinator.h"
#include "LBOneFactoryRuntimeRegistrySubsystem.h"
#include "LBPressShopOverheadVisualLayerActor.h"

namespace LBPressShopOverheadPresentationPrivate
{
    const TCHAR* const MachineIds[] = {
        TEXT("IN01_ARTICULATED_CARRIER"),
        TEXT("IN02_COIL_HANDLER_AGV"),
        TEXT("IN03_COIL_STORAGE"),
        TEXT("IN04_DEPACK"),
        TEXT("IN05_COIL_PREP"),
        TEXT("S01_DESTACK_LOAD"),
        TEXT("S02_DEEP_DRAW"),
        TEXT("S03_FORM"),
        TEXT("S04_TRIM"),
        TEXT("S05_PIERCE"),
        TEXT("S06_FLANGE"),
        TEXT("S07_INSPECTION"),
        TEXT("S07_PALLETISER"),
        TEXT("SUPPORT_FLEET")
    };

    const TCHAR* const BeaconComponentNames[] = {
        TEXT("IN01_ArticulatedCarrier_StatusBeacon"),
        TEXT("IN02_CoilHandlerAGV_StatusBeacon"),
        TEXT("IN03_CoilStorage_StatusBeacon"),
        TEXT("IN04_Depack_StatusBeacon"),
        TEXT("IN05_CoilPrep_StatusBeacon"),
        TEXT("S01_DestackLoad_StatusBeacon"),
        TEXT("S02_DeepDraw_StatusBeacon"),
        TEXT("S03_Form_StatusBeacon"),
        TEXT("S04_Trim_StatusBeacon"),
        TEXT("S05_Pierce_StatusBeacon"),
        TEXT("S06_Flange_StatusBeacon"),
        TEXT("S07_Inspection_StatusBeacon"),
        TEXT("S07_Palletiser_StatusBeacon"),
        TEXT("SupportFleet_StatusBeacon")
    };

    const TCHAR* const TaskLightIds[] = {
        TEXT("IN04_DEPACK_TASK"),
        TEXT("S07_INSPECTION_TASK_A"),
        TEXT("S07_INSPECTION_TASK_B"),
        TEXT("S07_PALLETISER_TASK")
    };

    const TCHAR* const TaskLightComponentNames[] = {
        TEXT("IN04_Depack_TaskLight"),
        TEXT("S07_Inspection_TaskLight_A"),
        TEXT("S07_Inspection_TaskLight_B"),
        TEXT("S07_Palletiser_TaskLight")
    };

    const TCHAR* const TaskLightMachineIds[] = {
        TEXT("IN04_DEPACK"),
        TEXT("S07_INSPECTION"),
        TEXT("S07_INSPECTION"),
        TEXT("S07_PALLETISER")
    };

    static_assert(UE_ARRAY_COUNT(MachineIds)
        == UE_ARRAY_COUNT(BeaconComponentNames));
    static_assert(UE_ARRAY_COUNT(TaskLightIds)
        == UE_ARRAY_COUNT(TaskLightComponentNames));
    static_assert(UE_ARRAY_COUNT(TaskLightIds)
        == UE_ARRAY_COUNT(TaskLightMachineIds));

    constexpr float BindingRefreshSeconds = 1.0f;
    // PressShop_S01_TrueOverheadCoilPrep_v001 documents the S01A cart as a
    // continuous 0.0 to 3.2 m world translation, with +X as process flow.
    constexpr float CoilCartTravelCm = 320.0f;
    // The cart must be seated at the decoiler before payoff/strip motion.  This
    // is a presentation phase split within the canonical station's 0..1 time;
    // it does not alter cycle duration, reservations, genealogy or WIP.
    constexpr float CoilCartTransferEnd = 0.36f;
    const FLinearColor WarmWhite(1.0f, 0.965f, 0.86f);
}

ALBPressShopOverheadPresentationActor::
    ALBPressShopOverheadPresentationActor()
{
    PrimaryActorTick.bCanEverTick = true;
    PrimaryActorTick.bStartWithTickEnabled = true;
    SetReplicates(false);
    SetActorEnableCollision(false);

    SceneRoot = CreateDefaultSubobject<USceneComponent>(TEXT("SceneRoot"));
    SceneRoot->SetMobility(EComponentMobility::Movable);
    SetRootComponent(SceneRoot);

    using namespace LBPressShopOverheadPresentationPrivate;
    BeaconMachineIds.Reserve(UE_ARRAY_COUNT(MachineIds));
    StatusBeacons.Reserve(UE_ARRAY_COUNT(MachineIds));
    for (int32 Index = 0; Index < UE_ARRAY_COUNT(MachineIds); ++Index)
    {
        BeaconMachineIds.Add(FName(MachineIds[Index]));
        ULBStatusBeaconComponent* Beacon =
            CreateDefaultSubobject<ULBStatusBeaconComponent>(
                FName(BeaconComponentNames[Index]));
        Beacon->SetupAttachment(SceneRoot);
        Beacon->SetRelativeScale3D(FVector(0.60f));
        Beacon->SetStatus(ELBStatusBeaconState::Off);
        StatusBeacons.Add(Beacon);
    }

    TaskLightIds.Reserve(UE_ARRAY_COUNT(TaskLightComponentNames));
    TaskLightMachineIds.Reserve(UE_ARRAY_COUNT(TaskLightComponentNames));
    TaskLights.Reserve(UE_ARRAY_COUNT(TaskLightComponentNames));
    for (int32 Index = 0; Index < UE_ARRAY_COUNT(TaskLightComponentNames);
        ++Index)
    {
        TaskLightIds.Add(FName(
            LBPressShopOverheadPresentationPrivate::TaskLightIds[Index]));
        TaskLightMachineIds.Add(FName(
            LBPressShopOverheadPresentationPrivate::TaskLightMachineIds[Index]));
        URectLightComponent* Light = CreateDefaultSubobject<URectLightComponent>(
            FName(TaskLightComponentNames[Index]));
        Light->SetupAttachment(SceneRoot);
        Light->SetMobility(EComponentMobility::Movable);
        Light->SetRelativeRotation(FRotator(-90.0f, 0.0f, 0.0f));
        Light->SetLightColor(WarmWhite);
        Light->SetIntensity(0.0f);
        Light->SetAttenuationRadius(900.0f);
        Light->SetSourceWidth(340.0f);
        Light->SetSourceHeight(180.0f);
        Light->SetCastShadows(false);
        Light->SetVisibility(false, true);
        TaskLights.Add(Light);
    }

    Tags.AddUnique(GetPresentationTag());
    Tags.AddUnique(TEXT("LB.Environment.VisualOnly"));
    Tags.AddUnique(TEXT("LB.NotProcessWIP"));
    ResetMachineStates(ELBStatusBeaconState::Off);
}

FName ALBPressShopOverheadPresentationActor::GetPresentationTag()
{
    return TEXT("LB.PressShop.OverheadPresentation.v001");
}

void ALBPressShopOverheadPresentationActor::Tick(const float DeltaSeconds)
{
    Super::Tick(DeltaSeconds);
    BindingRefreshAccumulator += FMath::Max(0.0f, DeltaSeconds);
    if (BindingRefreshAccumulator >=
        LBPressShopOverheadPresentationPrivate::BindingRefreshSeconds
        || BoundLayers.IsEmpty())
    {
        BindingRefreshAccumulator = 0.0f;
        RefreshLayerBindings();
        SuppressSupersededPressPresentation();
    }

    FString Reason;
    RefreshFromRuntime(Reason);
}

void ALBPressShopOverheadPresentationActor::SetPresentationEnabled(
    const bool bEnabled)
{
    bPresentationEnabled = bEnabled;
    ApplyLayerStates();
    ApplyBeaconStates();
    if (!bEnabled)
    {
        for (URectLightComponent* Light : TaskLights)
        {
            if (Light)
            {
                Light->SetIntensity(0.0f);
                Light->SetVisibility(false, true);
            }
        }
    }
}

bool ALBPressShopOverheadPresentationActor::SetMachineBeaconAnchor(
    const FName MachineId, const FVector WorldAnchorCm)
{
    if (ULBStatusBeaconComponent* Beacon = GetStatusBeacon(MachineId))
    {
        Beacon->SetWorldLocation(WorldAnchorCm);
        return true;
    }
    return false;
}

bool ALBPressShopOverheadPresentationActor::SetTaskLightAnchor(
    const FName TaskLightId, const FVector WorldAnchorCm)
{
    if (URectLightComponent* Light = GetTaskLight(TaskLightId))
    {
        Light->SetWorldLocation(WorldAnchorCm);
        return true;
    }
    return false;
}

ULBStatusBeaconComponent*
ALBPressShopOverheadPresentationActor::GetStatusBeacon(
    const FName MachineId) const
{
    const int32 Index = BeaconMachineIds.IndexOfByKey(MachineId);
    return StatusBeacons.IsValidIndex(Index) ? StatusBeacons[Index] : nullptr;
}

URectLightComponent* ALBPressShopOverheadPresentationActor::GetTaskLight(
    const FName TaskLightId) const
{
    const int32 Index = TaskLightIds.IndexOfByKey(TaskLightId);
    return TaskLights.IsValidIndex(Index) ? TaskLights[Index] : nullptr;
}

ELBStatusBeaconState ALBPressShopOverheadPresentationActor::ResolveBeaconState(
    const bool bCommissioned, const bool bLinePaused,
    const bool bDepartmentFaulted, const bool bOutputBlocked,
    const bool bMachineActive, const bool bMachineMoving,
    const bool bWaitingAtGate)
{
    if (!bCommissioned) return ELBStatusBeaconState::Off;
    if (bDepartmentFaulted) return ELBStatusBeaconState::Fault;
    if (bLinePaused) return ELBStatusBeaconState::Stopped;
    if (bWaitingAtGate || bOutputBlocked)
        return ELBStatusBeaconState::Waiting;
    if (bMachineMoving) return ELBStatusBeaconState::Moving;
    if (bMachineActive) return ELBStatusBeaconState::Running;
    return ELBStatusBeaconState::Ready;
}

void ALBPressShopOverheadPresentationActor::ComputePressVisualState(
    const float NormalizedCycleProgress, FName& OutActiveMachineId,
    ELBPressShopOverheadPressFrame& OutFrame,
    float& OutLocalProgress01, bool& bOutTransferActive)
{
    static const FName PressMachines[] = {
        TEXT("S02_DEEP_DRAW"), TEXT("S03_FORM"), TEXT("S04_TRIM"),
        TEXT("S05_PIERCE"), TEXT("S06_FLANGE")
    };
    const float Clamped = FMath::Clamp(NormalizedCycleProgress, 0.0f, 1.0f);
    constexpr int32 PressMachineCount = static_cast<int32>(
        UE_ARRAY_COUNT(PressMachines));
    const float Scaled = Clamped * PressMachineCount;
    const int32 Index = FMath::Min(
        FMath::FloorToInt(Scaled), PressMachineCount - 1);
    OutActiveMachineId = PressMachines[Index];
    OutLocalProgress01 = Clamped >= 1.0f
        ? 1.0f : FMath::Clamp(Scaled - Index, 0.0f, 1.0f);

    bOutTransferActive = false;
    if (OutLocalProgress01 < 0.28f)
        OutFrame = ELBPressShopOverheadPressFrame::Open;
    else if (OutLocalProgress01 < 0.52f)
        OutFrame = ELBPressShopOverheadPressFrame::Descending;
    else if (OutLocalProgress01 < 0.68f)
        OutFrame = ELBPressShopOverheadPressFrame::Contact;
    else if (OutLocalProgress01 < 0.90f)
        OutFrame = ELBPressShopOverheadPressFrame::Rising;
    else
    {
        OutFrame = ELBPressShopOverheadPressFrame::Open;
        bOutTransferActive = true;
    }
}

void ALBPressShopOverheadPresentationActor::ComputeDepackVisualState(
    const float NormalizedDepackProgress, FName& OutPoseState,
    float& OutLocalProgress01)
{
    const float Progress = FMath::Clamp(NormalizedDepackProgress, 0.0f, 1.0f);
    if (Progress < 0.25f)
    {
        OutPoseState = TEXT("ROLLERS");
        OutLocalProgress01 = Progress / 0.25f;
    }
    else if (Progress < 0.65f)
    {
        OutPoseState = TEXT("WRAP_REMOVE");
        OutLocalProgress01 = (Progress - 0.25f) / 0.40f;
    }
    else
    {
        OutPoseState = TEXT("VISION_INSPECT");
        OutLocalProgress01 = (Progress - 0.65f) / 0.35f;
    }
    OutLocalProgress01 = FMath::Clamp(OutLocalProgress01, 0.0f, 1.0f);
}

void ALBPressShopOverheadPresentationActor::ComputeCoilFeedVisualState(
    const float NormalizedCycleProgress, float& OutCartTravel01,
    float& OutPayoffProgress01, bool& bOutCartMoving,
    bool& bOutPayoffActive)
{
    using namespace LBPressShopOverheadPresentationPrivate;
    const float Progress = FMath::Clamp(NormalizedCycleProgress, 0.0f, 1.0f);
    const float LinearCart = FMath::Clamp(
        Progress / CoilCartTransferEnd, 0.0f, 1.0f);
    // Smooth endpoints keep the heavy cart from snapping into motion while
    // retaining an exact, deterministic position for every cycle cursor.
    OutCartTravel01 = FMath::SmoothStep(0.0f, 1.0f, LinearCart);
    bOutCartMoving = Progress > 0.0f && Progress < CoilCartTransferEnd;
    bOutPayoffActive = Progress >= CoilCartTransferEnd;
    OutPayoffProgress01 = bOutPayoffActive
        ? FMath::Clamp((Progress - CoilCartTransferEnd)
            / (1.0f - CoilCartTransferEnd), 0.0f, 1.0f)
        : 0.0f;
}

bool ALBPressShopOverheadPresentationActor::BuildAuthoredMotionRange(
    const FName MotionChannel, const FTransform& PlacedTransform,
    FTransform& OutStart, FTransform& OutEnd)
{
    if (MotionChannel != TEXT("CoilTransferToDecoiler"))
    {
        return false;
    }

    OutStart = PlacedTransform;
    OutEnd = PlacedTransform;
    OutEnd.AddToTranslation(FVector(
        LBPressShopOverheadPresentationPrivate::CoilCartTravelCm,
        0.0f, 0.0f));
    return true;
}

FName ALBPressShopOverheadPresentationActor::FrameStateName(
    const ELBPressShopOverheadPressFrame Frame)
{
    switch (Frame)
    {
    case ELBPressShopOverheadPressFrame::Descending:
        return TEXT("DESCENDING");
    case ELBPressShopOverheadPressFrame::Contact:
        return TEXT("CONTACT");
    case ELBPressShopOverheadPressFrame::Rising:
        return TEXT("RISING");
    default:
        return TEXT("OPEN");
    }
}

FName ALBPressShopOverheadPresentationActor::BeaconColourName(
    const ELBStatusBeaconState State)
{
    switch (State)
    {
    case ELBStatusBeaconState::Ready:
    case ELBStatusBeaconState::Running:
        return TEXT("GREEN");
    case ELBStatusBeaconState::Idle:
    case ELBStatusBeaconState::Waiting:
    case ELBStatusBeaconState::Moving:
        return TEXT("AMBER");
    case ELBStatusBeaconState::Stopped:
    case ELBStatusBeaconState::Fault:
    case ELBStatusBeaconState::Emergency:
        return TEXT("RED");
    default:
        return TEXT("OFF");
    }
}

void ALBPressShopOverheadPresentationActor::ResetMachineStates(
    const ELBStatusBeaconState DefaultState)
{
    MachineStates.Reset();
    for (const FName MachineId : BeaconMachineIds)
    {
        FMachineRuntimeState State;
        State.Beacon = DefaultState;
        MachineStates.Add(MachineId, State);
    }
}

ALBPressShopOverheadPresentationActor::FMachineRuntimeState&
ALBPressShopOverheadPresentationActor::StateFor(const FName MachineId)
{
    return MachineStates.FindOrAdd(MachineId);
}

bool ALBPressShopOverheadPresentationActor::RefreshFromRuntime(
    FString& OutReason)
{
    UWorld* World = GetWorld();
    if (!World)
    {
        OutReason = TEXT("OVERHEAD PRESENTATION HAS NO WORLD");
        return false;
    }

    ULBOneFactoryRuntimeRegistrySubsystem* Registry =
        World->GetSubsystem<ULBOneFactoryRuntimeRegistrySubsystem>();
    ALBOneFactoryProductionFlowAuthority* Production = nullptr;
    ALBOneFactoryRuntimeCoordinator* Coordinator = nullptr;
    FString RegistryReason;
    if (!Registry || !Registry->ResolveRuntimeBackbone(
            Production, Coordinator, RegistryReason))
    {
        ResetMachineStates(ELBStatusBeaconState::Off);
        ApplyLayerStates();
        ApplyBeaconStates();
        ApplyTaskLightStates(false, false, false);
        OutReason = RegistryReason.IsEmpty()
            ? TEXT("OVERHEAD PRESENTATION IS WAITING FOR ONEFACTORY RUNTIME")
            : RegistryReason;
        return false;
    }

    const FLBOneFactoryProductionLedgerState Ledger =
        Production->CaptureLedger();
    const bool bCommissioned = Ledger.Commissioning.bPressCommissioned;
    const bool bFaulted = Ledger.FaultedDepartments.Contains(
        ELBOneFactoryDepartment::Press);
    const bool bOutputBlocked = Ledger.OutputBlockedDepartments.Contains(
        ELBOneFactoryDepartment::Press);
    const ELBStatusBeaconState DefaultState = ResolveBeaconState(
        bCommissioned, Ledger.bLinePaused, bFaulted, bOutputBlocked,
        false, false, false);
    ResetMachineStates(DefaultState);

    const auto Activate = [this, bCommissioned, bFaulted, bOutputBlocked,
        &Ledger](const FName MachineId, const float Progress01,
        const bool bMoving, const bool bWaiting,
        const ELBPressShopOverheadPressFrame Frame,
        const FName PoseState, const bool bTransfer)
    {
        FMachineRuntimeState& State = StateFor(MachineId);
        State.bActive = true;
        State.Progress01 = FMath::Clamp(Progress01, 0.0f, 1.0f);
        State.PressFrame = Frame;
        State.PoseState = PoseState;
        State.bTransferActive = bTransfer;
        State.Beacon = ResolveBeaconState(bCommissioned, Ledger.bLinePaused,
            bFaulted, bOutputBlocked, true, bMoving, bWaiting);
    };

    for (const FLBOneFactoryVehicleUnitState& Unit : Ledger.Units)
    {
        if (!Unit.bRuntimeStarted || Unit.bCompleted || Unit.bDispatched
            || Unit.Department != ELBOneFactoryDepartment::Press)
        {
            continue;
        }

        FLBOneFactoryRuntimeVehicleStatus Status;
        FString StatusReason;
        if (!Coordinator->GetVehicleRuntimeStatus(
                Unit.UnitId, Status, StatusReason))
        {
            continue;
        }
        const float Progress = FMath::Clamp(
            Status.NormalizedCycleProgress, 0.0f, 1.0f);
        const bool bWaiting = Status.bAwaitingQualityResult;

        if (Status.CurrentStationId ==
            LBOneFactoryPressStarterIds::InboundReceiving())
        {
            if (Progress < 0.48f)
            {
                Activate(TEXT("IN01_ARTICULATED_CARRIER"),
                    Progress / 0.48f, false, bWaiting,
                    ELBPressShopOverheadPressFrame::Open,
                    TEXT("UNLOADING"), false);
            }
            else
            {
                Activate(TEXT("IN02_COIL_HANDLER_AGV"),
                    (Progress - 0.48f) / 0.52f, true, bWaiting,
                    ELBPressShopOverheadPressFrame::Open,
                    TEXT("TRANSFER"), true);
            }
        }
        else if (Status.CurrentStationId ==
            LBOneFactoryPressStarterIds::WrappedCoilStorage())
        {
            Activate(TEXT("IN03_COIL_STORAGE"), Progress, false, bWaiting,
                ELBPressShopOverheadPressFrame::Open,
                TEXT("STORE"), false);
        }
        else if (Status.CurrentStationId ==
            LBOneFactoryPressStarterIds::BlankPreparation())
        {
            if (Progress < 0.38f)
            {
                FName DepackPose;
                float DepackProgress = 0.0f;
                ComputeDepackVisualState(Progress / 0.38f,
                    DepackPose, DepackProgress);
                Activate(TEXT("IN04_DEPACK"), DepackProgress,
                    false, bWaiting, ELBPressShopOverheadPressFrame::Open,
                    DepackPose, false);
            }
            else
            {
                Activate(TEXT("IN05_COIL_PREP"),
                    (Progress - 0.38f) / 0.62f, false, bWaiting,
                    ELBPressShopOverheadPressFrame::Open,
                    TEXT("FEED"), Progress > 0.82f);
            }
        }
        else if (Status.CurrentStationId ==
            LBOneFactoryPressStarterIds::PreparedBlankBuffer())
        {
            float CartTravel = 0.0f;
            float PayoffProgress = 0.0f;
            bool bCartMoving = false;
            bool bPayoffActive = false;
            ComputeCoilFeedVisualState(Progress, CartTravel,
                PayoffProgress, bCartMoving, bPayoffActive);
            Activate(TEXT("S01_DESTACK_LOAD"), Progress,
                bCartMoving || bPayoffActive, bWaiting,
                ELBPressShopOverheadPressFrame::Open,
                TEXT("LOAD"), Progress > 0.78f);
        }
        else if (Status.CurrentStationId ==
            LBOneFactoryPressStarterIds::PressTrain())
        {
            FName PressMachine;
            ELBPressShopOverheadPressFrame Frame;
            float LocalProgress = 0.0f;
            bool bTransfer = false;
            ComputePressVisualState(Progress, PressMachine, Frame,
                LocalProgress, bTransfer);
            Activate(PressMachine, LocalProgress, bTransfer, bWaiting,
                Frame, FrameStateName(Frame), bTransfer);
            if (bTransfer)
            {
                Activate(TEXT("SUPPORT_FLEET"), LocalProgress,
                    true, false, ELBPressShopOverheadPressFrame::Open,
                    TEXT("TRANSFER"), true);
            }
        }
        else if (Status.CurrentStationId ==
            LBOneFactoryPressStarterIds::PanelInspection())
        {
            const FName Pose = Progress < 0.18f ? FName(TEXT("PARKED"))
                : Progress < 0.42f ? FName(TEXT("PICK"))
                : Progress < 0.78f ? FName(TEXT("INSPECT"))
                : FName(TEXT("PLACE"));
            Activate(TEXT("S07_INSPECTION"), Progress,
                Progress >= 0.18f && !bWaiting, bWaiting,
                ELBPressShopOverheadPressFrame::Open,
                Pose, Progress > 0.78f);
        }
        else if (Status.CurrentStationId ==
            LBOneFactoryPressStarterIds::PanelDispatch())
        {
            const FName Pose = Progress < 0.20f ? FName(TEXT("PARKED"))
                : Progress < 0.52f ? FName(TEXT("PICK"))
                : Progress < 0.86f ? FName(TEXT("PLACE"))
                : FName(TEXT("PARKED"));
            Activate(TEXT("S07_PALLETISER"), Progress,
                Progress >= 0.20f, bWaiting,
                ELBPressShopOverheadPressFrame::Open,
                Pose, Progress > 0.82f);
            if (Progress > 0.82f)
            {
                Activate(TEXT("SUPPORT_FLEET"), Progress,
                    true, false, ELBPressShopOverheadPressFrame::Open,
                    TEXT("OUTBOUND"), true);
            }
        }
    }

    ApplyLayerStates();
    ApplyBeaconStates();
    ApplyTaskLightStates(bCommissioned, bFaulted, Ledger.bLinePaused);
    OutReason = FString::Printf(TEXT(
        "OVERHEAD PRESS PRESENTATION FOLLOWS CANONICAL LEDGER REVISION %d"),
        Ledger.Revision);
    return true;
}

void ALBPressShopOverheadPresentationActor::RefreshLayerBindings()
{
    BoundLayers.Reset();
    UWorld* World = GetWorld();
    if (!World) return;
    for (TActorIterator<ALBPressShopOverheadVisualLayerActor> It(World); It;
        ++It)
    {
        ALBPressShopOverheadVisualLayerActor* Layer = *It;
        if (IsValid(Layer) && !Layer->IsActorBeingDestroyed())
        {
            if (!Layer->bHasMotionRange)
            {
                FTransform Start;
                FTransform End;
                if (BuildAuthoredMotionRange(Layer->MotionChannel,
                        Layer->GetActorTransform(), Start, End))
                {
                    Layer->MotionStart = Start;
                    Layer->MotionEnd = End;
                    Layer->bHasMotionRange = true;
                }
            }
            BoundLayers.Add(Layer);
        }
    }
}

void ALBPressShopOverheadPresentationActor::
    SuppressSupersededPressPresentation() const
{
    UWorld* World = GetWorld();
    if (!World) return;
    static const FName SupersededTag(
        TEXT("LB.OneFactory.PressStarter.Presentation.v001"));
    for (TActorIterator<AActor> It(World); It; ++It)
    {
        AActor* Actor = *It;
        if (!IsValid(Actor) || Actor == this
            || !Actor->ActorHasTag(SupersededTag))
        {
            continue;
        }
        Actor->SetActorHiddenInGame(true);
        Actor->SetActorEnableCollision(false);
    }
}

void ALBPressShopOverheadPresentationActor::ApplyLayerStates()
{
    for (int32 Index = BoundLayers.Num() - 1; Index >= 0; --Index)
    {
        ALBPressShopOverheadVisualLayerActor* Layer = BoundLayers[Index].Get();
        if (!IsValid(Layer))
        {
            BoundLayers.RemoveAtSwap(Index);
            continue;
        }

        const FMachineRuntimeState* State = MachineStates.Find(Layer->MachineId);
        const FMachineRuntimeState Fallback;
        const FMachineRuntimeState& Runtime = State ? *State : Fallback;
        bool bVisible = bPresentationEnabled;
        float MotionAlpha = Runtime.Progress01;
        bool bMotionChannelActive = true;
        if (Layer->MachineId == TEXT("S01_DESTACK_LOAD"))
        {
            float CartTravel = 0.0f;
            float PayoffProgress = 0.0f;
            bool bCartMoving = false;
            bool bPayoffActive = false;
            ComputeCoilFeedVisualState(Runtime.Progress01, CartTravel,
                PayoffProgress, bCartMoving, bPayoffActive);
            if (Layer->MotionChannel == TEXT("CoilTransferToDecoiler"))
            {
                MotionAlpha = CartTravel;
            }
            else if (Layer->MotionChannel == TEXT("S01_DECOILER_PAYOFF")
                || Layer->MotionChannel == TEXT("S01_ENTRY_STRIP_PULSE")
                || Layer->MotionChannel == TEXT("S01_FEED_STRIP_PULSE"))
            {
                MotionAlpha = PayoffProgress;
                bMotionChannelActive = bPayoffActive;
            }
        }
        switch (Layer->LayerRole)
        {
        case ELBPressShopOverheadLayerRole::Base:
            break;
        case ELBPressShopOverheadLayerRole::FrameState:
            bVisible = bVisible
                && Layer->StateId == FrameStateName(Runtime.PressFrame);
            break;
        case ELBPressShopOverheadLayerRole::Workpiece:
            bVisible = bVisible && Runtime.bActive;
            break;
        case ELBPressShopOverheadLayerRole::MovingOverlay:
            bVisible = bVisible && Runtime.bActive
                && bMotionChannelActive
                && (Layer->StateId.IsNone()
                    || Layer->StateId == Runtime.PoseState);
            break;
        case ELBPressShopOverheadLayerRole::ContactEffect:
            bVisible = bVisible && Runtime.bActive
                && Runtime.PressFrame
                    == ELBPressShopOverheadPressFrame::Contact;
            break;
        case ELBPressShopOverheadLayerRole::CyanTransfer:
            bVisible = bVisible && (Layer->StateId.IsNone()
                ? Runtime.bTransferActive
                : Runtime.bActive && Layer->StateId == Runtime.PoseState);
            break;
        case ELBPressShopOverheadLayerRole::BeaconGlow:
            bVisible = bVisible
                && Layer->StateId == BeaconColourName(Runtime.Beacon);
            break;
        case ELBPressShopOverheadLayerRole::TaskLightGlow:
            bVisible = bVisible
                && Runtime.Beacon != ELBStatusBeaconState::Off
                && Runtime.Beacon != ELBStatusBeaconState::Fault;
            break;
        case ELBPressShopOverheadLayerRole::ConveyorMotion:
            bVisible = bVisible && Runtime.bActive
                && bMotionChannelActive
                && (Layer->StateId.IsNone()
                    || Layer->StateId == Runtime.PoseState);
            // Belts/rollers can repeat several times per station cycle, while
            // inspection sweeps and other one-shot sequences must retain the
            // authoritative 0..1 progress and clamp on their final frame.
            MotionAlpha = Layer->bSequenceLoops
                ? FMath::Fmod(MotionAlpha * 4.0f, 1.0f)
                : MotionAlpha;
            break;
        case ELBPressShopOverheadLayerRole::RobotPose:
            bVisible = bVisible
                && Layer->StateId == Runtime.PoseState;
            break;
        default:
            bVisible = false;
            break;
        }
        bVisible = bVisible
            && Layer->IsSequenceFrameVisible(MotionAlpha);
        Layer->ApplyPresentationState(bVisible, MotionAlpha);
    }
}

void ALBPressShopOverheadPresentationActor::ApplyBeaconStates()
{
    for (int32 Index = 0; Index < StatusBeacons.Num(); ++Index)
    {
        ULBStatusBeaconComponent* Beacon = StatusBeacons[Index];
        if (!Beacon || !BeaconMachineIds.IsValidIndex(Index)) continue;
        const FMachineRuntimeState* State = MachineStates.Find(
            BeaconMachineIds[Index]);
        Beacon->SetStatus(bPresentationEnabled && State
            ? State->Beacon : ELBStatusBeaconState::Off);
    }
}

void ALBPressShopOverheadPresentationActor::ApplyTaskLightStates(
    const bool bPressCommissioned, const bool bPressFaulted,
    const bool bLinePaused)
{
    for (int32 Index = 0; Index < TaskLights.Num(); ++Index)
    {
        URectLightComponent* Light = TaskLights[Index];
        if (!Light || !TaskLightMachineIds.IsValidIndex(Index)) continue;
        const FMachineRuntimeState* State = MachineStates.Find(
            TaskLightMachineIds[Index]);
        const bool bVisible = bPresentationEnabled && bPressCommissioned
            && !bPressFaulted;
        float Intensity = 0.0f;
        if (bVisible)
        {
            if (bLinePaused) Intensity = 500.0f;
            else if (State && State->bActive) Intensity = 5600.0f;
            else Intensity = 1800.0f;
        }
        Light->SetIntensity(Intensity);
        Light->SetVisibility(bVisible, true);
    }
}
