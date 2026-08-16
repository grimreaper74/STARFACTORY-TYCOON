#include "LBPR010Station.h"

#include "Components/SceneComponent.h"
#include "Components/TextRenderComponent.h"
#include "Engine/TextRenderActor.h"
#include "GameFramework/Actor.h"

#define LOCTEXT_NAMESPACE "LBPR010Station"

ALBPR010Station::ALBPR010Station()
{
    PrimaryActorTick.bCanEverTick = true;
    StationRoot = CreateDefaultSubobject<USceneComponent>(TEXT("PR010_StationRoot"));
    SetRootComponent(StationRoot);
    ShuttleMover = CreateDefaultSubobject<USceneComponent>(TEXT("PR010_ShuttleMover"));
    ShuttleMover->SetupAttachment(StationRoot);
    for (int32 Index = 0; Index < 4; ++Index)
    {
        USceneComponent* Roller = CreateDefaultSubobject<USceneComponent>(*FString::Printf(TEXT("PR010_LaneRollMover_%c"), TCHAR('A' + Index)));
        Roller->SetupAttachment(StationRoot); LaneRollMovers.Add(Roller);
        USceneComponent* Stop = CreateDefaultSubobject<USceneComponent>(*FString::Printf(TEXT("PR010_LaneStopMover_%c"), TCHAR('A' + Index)));
        Stop->SetupAttachment(StationRoot); LaneStopMovers.Add(Stop);
        USceneComponent* Gate = CreateDefaultSubobject<USceneComponent>(*FString::Printf(TEXT("PR010_ReservationGateMover_%c"), TCHAR('A' + Index)));
        Gate->SetupAttachment(StationRoot); ReservationGateMovers.Add(Gate);
    }
    QualityHoldMover = CreateDefaultSubobject<USceneComponent>(TEXT("PR010_QualityHoldMover"));
    QualityHoldMover->SetupAttachment(StationRoot);
    LaneReservations.Init(NAME_None, 4);
}

void ALBPR010Station::BeginPlay()
{
    Super::BeginPlay();
    CapturePresentationBases();
    UpdatePresentation();
}

void ALBPR010Station::CapturePresentationBases()
{
    if (bPresentationBasesCaptured) return;
    ShuttleBaseTransform = ShuttleMover->GetRelativeTransform();
    LaneRollBaseTransforms.Reset(); LaneStopBaseTransforms.Reset(); ReservationGateBaseTransforms.Reset();
    for (USceneComponent* Component : LaneRollMovers) LaneRollBaseTransforms.Add(Component->GetRelativeTransform());
    for (USceneComponent* Component : LaneStopMovers) LaneStopBaseTransforms.Add(Component->GetRelativeTransform());
    for (USceneComponent* Component : ReservationGateMovers) ReservationGateBaseTransforms.Add(Component->GetRelativeTransform());
    QualityHoldBaseTransform = QualityHoldMover->GetRelativeTransform();
    BoundRollBaseRotations.Reset();
    for (AActor* Actor : BoundRollActors) BoundRollBaseRotations.Add(Actor ? Actor->GetActorRotation() : FRotator::ZeroRotator);
    BoundGateBaseRotations.Reset();
    for (AActor* Actor : BoundGateActors) BoundGateBaseRotations.Add(Actor ? Actor->GetActorRotation() : FRotator::ZeroRotator);
    bPresentationBasesCaptured = true;
}

void ALBPR010Station::UpdatePresentation()
{
    CapturePresentationBases();
    const float Progress = GetPhaseProgress();
    const float Smooth = Progress * Progress * (3.0f - 2.0f * Progress);
    const float Pulse = FMath::Sin(Progress * PI);
    const float LaneTargets[4] = {-450.0f, -150.0f, 150.0f, 450.0f};
    const float ShuttleX = ActiveLaneIndex >= 0 && ActiveLaneIndex < 4
        && (State == ELBPR010State::LaneSelect || State == ELBPR010State::Transfer)
        ? LaneTargets[ActiveLaneIndex] * Smooth : 0.0f;
    ShuttleMover->SetRelativeLocationAndRotation(ShuttleBaseTransform.GetLocation() + FVector(ShuttleX, 0.0f, 0.0f), ShuttleBaseTransform.Rotator());
    for (int32 Index = 0; Index < 4; ++Index)
    {
        const bool bLaneMoving = Index == ActiveLaneIndex && (State == ELBPR010State::Transfer || State == ELBPR010State::VehicleHandoff);
        LaneRollMovers[Index]->SetRelativeLocationAndRotation(LaneRollBaseTransforms[Index].GetLocation(), LaneRollBaseTransforms[Index].Rotator());
        const bool bStopRaised = GetLane(Index).Num() > 0 && State != ELBPR010State::VehicleHandoff;
        LaneStopMovers[Index]->SetRelativeLocationAndRotation(LaneStopBaseTransforms[Index].GetLocation() + FVector(0, 0, bStopRaised ? 12.0f : 0.0f), LaneStopBaseTransforms[Index].Rotator());
        const bool bGateOpen = Index == PendingDispatchLaneIndex && State == ELBPR010State::VehicleHandoff;
        ReservationGateMovers[Index]->SetRelativeLocationAndRotation(ReservationGateBaseTransforms[Index].GetLocation(), ReservationGateBaseTransforms[Index].Rotator());
    }
    for (int32 BoundIndex = 0; BoundIndex < BoundRollActors.Num(); ++BoundIndex)
    {
        AActor* Actor = BoundRollActors[BoundIndex];
        if (!Actor || !BoundRollBaseRotations.IsValidIndex(BoundIndex) || !BoundRollLaneIndices.IsValidIndex(BoundIndex)) continue;
        const int32 LaneIndex = BoundRollLaneIndices[BoundIndex];
        const bool bLaneMoving = LaneIndex == ActiveLaneIndex && (State == ELBPR010State::Transfer || State == ELBPR010State::VehicleHandoff);
        Actor->SetActorRotation(BoundRollBaseRotations[BoundIndex] + FRotator(0.0f, 0.0f, bLaneMoving ? 360.0f * Progress : 0.0f));
    }
    for (int32 BoundIndex = 0; BoundIndex < BoundGateActors.Num(); ++BoundIndex)
    {
        AActor* Actor = BoundGateActors[BoundIndex];
        if (!Actor || !BoundGateBaseRotations.IsValidIndex(BoundIndex) || !BoundGateLaneIndices.IsValidIndex(BoundIndex)) continue;
        const int32 LaneIndex = BoundGateLaneIndices[BoundIndex];
        const bool bGateOpen = LaneIndex == PendingDispatchLaneIndex && State == ELBPR010State::VehicleHandoff;
        Actor->SetActorRotation(BoundGateBaseRotations[BoundIndex] + FRotator(0.0f, bGateOpen ? 90.0f * Smooth : 0.0f, 0.0f));
    }
    QualityHoldMover->SetRelativeLocationAndRotation(QualityHoldBaseTransform.GetLocation() +
        FVector(0, bInboundQualityHoldRequested && State == ELBPR010State::Transfer ? 250.0f * Smooth : 0.0f, 0), QualityHoldBaseTransform.Rotator());
}

float ALBPR010Station::GetPhaseDuration() const
{
    switch (State)
    {
    case ELBPR010State::LaneSelect: return 0.35f;
    case ELBPR010State::Transfer: return 1.2f;
    case ELBPR010State::Stored: return 0.35f;
    case ELBPR010State::TrainReserved: return 0.4f;
    case ELBPR010State::VehicleHandoff: return 1.0f;
    case ELBPR010State::Stopping: return 0.3f;
    default: return 0.0f;
    }
}

float ALBPR010Station::GetPhaseProgress() const
{
    const float Duration = GetPhaseDuration();
    return Duration > 0.0f ? FMath::Clamp(PhaseElapsedSeconds / Duration, 0.0f, 1.0f) : 0.0f;
}

bool ALBPR010Station::IsMovingState() const
{
    return State == ELBPR010State::LaneSelect || State == ELBPR010State::Transfer
        || State == ELBPR010State::TrainReserved || State == ELBPR010State::VehicleHandoff
        || State == ELBPR010State::Stopping;
}

void ALBPR010Station::Tick(float DeltaSeconds)
{
    Super::Tick(DeltaSeconds);
    EvaluatePermissives();
    if (State == ELBPR010State::Fault || State == ELBPR010State::Isolated)
    {
        UpdatePresentation();
        UpdateHMITextPresentation();
        return;
    }
    if (State == ELBPR010State::ReservationWait)
    {
        if (bControlledStopRequested) SetState(ELBPR010State::Stopping);
        else if (PendingDispatchLaneIndex >= 0) SetState(ELBPR010State::TrainReserved);
        else if (!InboundStackId.IsNone()) SetState(ELBPR010State::LaneSelect);
    }
    const float Duration = GetPhaseDuration();
    if (Duration > 0.0f)
    {
        PhaseElapsedSeconds += FMath::Max(0.0f, DeltaSeconds);
        if (PhaseElapsedSeconds >= Duration) AdvanceState();
    }
    UpdatePresentation();
    UpdateHMITextPresentation();
}

void ALBPR010Station::SetState(ELBPR010State NewState)
{
    if (State == NewState) return;
    const ELBPR010State Previous = State;
    State = NewState;
    PhaseElapsedSeconds = 0.0f;
    OnStateChanged.Broadcast(Previous, NewState);
}

void ALBPR010Station::AdvanceState()
{
    switch (State)
    {
    case ELBPR010State::LaneSelect:
        if (bInboundQualityHoldRequested)
        {
            if (!QualityHoldStackId.IsNone()) { RaiseFault(ELBPR010Fault::QualityHoldOccupied); return; }
            ActiveLaneIndex = -2;
        }
        else
        {
            ActiveLaneIndex = FindAvailableLane();
            if (ActiveLaneIndex < 0) { RaiseFault(ELBPR010Fault::LaneFull); return; }
        }
        SetState(ELBPR010State::Transfer);
        break;
    case ELBPR010State::Transfer:
        if (bInboundQualityHoldRequested) QualityHoldStackId = InboundStackId;
        else GetLane(ActiveLaneIndex).Add(InboundStackId);
        if (!InboundBlankIds.IsEmpty())
        {
            FLBPR010StackManifest Manifest;
            Manifest.StackId = InboundStackId;
            Manifest.BlankIds = MoveTemp(InboundBlankIds);
            StoredStackManifests.Add(MoveTemp(Manifest));
        }
        ++TotalStacksStored;
        InboundStackId = NAME_None;
        bInboundQualityHoldRequested = false;
        SetState(ELBPR010State::Stored);
        break;
    case ELBPR010State::Stored:
        ActiveLaneIndex = -1;
        SetState(bControlledStopRequested ? ELBPR010State::Stopping : ELBPR010State::ReservationWait);
        break;
    case ELBPR010State::TrainReserved:
        if (!bVehicleHandoffReady || !bCrossingClosed || !bCrossingClear) return;
        ActiveLaneIndex = PendingDispatchLaneIndex;
        SetState(ELBPR010State::VehicleHandoff);
        break;
    case ELBPR010State::VehicleHandoff:
        if (!GetLane(PendingDispatchLaneIndex).IsEmpty())
        {
            LastReleasedStackId = GetLane(PendingDispatchLaneIndex)[0];
            LastReleasedBlankIds.Reset();
            for (int32 ManifestIndex = 0; ManifestIndex < StoredStackManifests.Num(); ++ManifestIndex)
            {
                if (StoredStackManifests[ManifestIndex].StackId == LastReleasedStackId)
                {
                    LastReleasedBlankIds = MoveTemp(StoredStackManifests[ManifestIndex].BlankIds);
                    StoredStackManifests.RemoveAt(ManifestIndex);
                    break;
                }
            }
            GetLane(PendingDispatchLaneIndex).RemoveAt(0);
            ++TotalStacksDispatched;
        }
        LaneReservations[PendingDispatchLaneIndex] = NAME_None;
        PendingDispatchLaneIndex = -1;
        ActiveLaneIndex = -1;
        SetState(bControlledStopRequested ? ELBPR010State::Stopping : ELBPR010State::ReservationWait);
        break;
    case ELBPR010State::Stopping:
        bControlledStopRequested = false;
        SetState(ELBPR010State::Ready);
        break;
    default: break;
    }
}

void ALBPR010Station::RaiseFault(ELBPR010Fault Fault)
{
    if (Fault == ELBPR010Fault::None || State == ELBPR010State::Fault) return;
    ActiveFault = Fault;
    bAlarmAcknowledged = false;
    SetState(ELBPR010State::Fault);
    OnFaultRaised.Broadcast(Fault);
}

void ALBPR010Station::EvaluatePermissives()
{
    if (bEmergencyStopActive) RaiseFault(ELBPR010Fault::EmergencyStopActive);
    else if (!bSafetyCircuitHealthy) RaiseFault(ELBPR010Fault::SafetyCircuitFault);
    else if (!bGuardsClosed) RaiseFault(ELBPR010Fault::GuardInterlockOpen);
    else if (IsMovingState() && (!bCrossingClosed || !bCrossingClear)) RaiseFault(ELBPR010Fault::ControlledCrossingInterlock);
    else if (IsMovingState() && !bShuttleHealthy) RaiseFault(ELBPR010Fault::ShuttleFault);
}

bool ALBPR010Station::CanStart(TArray<FText>& Reasons) const
{
    Reasons.Reset();
    if (!bControlPowerOn) Reasons.Add(LOCTEXT("NoPower", "Control power is off."));
    if (State != ELBPR010State::Ready) Reasons.Add(LOCTEXT("NotReady", "PR-010 is not ready."));
    if (ActiveFault != ELBPR010Fault::None) Reasons.Add(LOCTEXT("Fault", "A PR-010 fault is active."));
    if (!bGuardsClosed || !bSafetyCircuitHealthy || bEmergencyStopActive) Reasons.Add(LOCTEXT("Safety", "Safety permissives are not healthy."));
    if (!bCrossingClosed || !bCrossingClear) Reasons.Add(LOCTEXT("Crossing", "Controlled crossing is not closed and clear."));
    if (!bShuttleHealthy) Reasons.Add(LOCTEXT("Shuttle", "Infeed shuttle is unavailable."));
    if (bIsolationRequested || bZeroEnergyProved) Reasons.Add(LOCTEXT("Isolation", "PR-010 is isolated."));
    return Reasons.IsEmpty();
}

bool ALBPR010Station::StartCycle()
{
    TArray<FText> Reasons;
    if (!CanStart(Reasons)) return false;
    bControlledStopRequested = false;
    bRestartRequiredAfterLoad = false;
    SetState(ELBPR010State::ReservationWait);
    return true;
}

void ALBPR010Station::RequestControlledStop()
{
    if (State == ELBPR010State::ReservationWait || State == ELBPR010State::Stored) SetState(ELBPR010State::Stopping);
    else if (IsMovingState()) bControlledStopRequested = true;
}

bool ALBPR010Station::AcknowledgeAlarm(FName CommandSource)
{
    if (State != ELBPR010State::Fault || ActiveFault == ELBPR010Fault::None) return false;
    bAlarmAcknowledged = true; LastCommandSource = CommandSource; return true;
}

bool ALBPR010Station::ResetFault()
{
    if (State != ELBPR010State::Fault || !bAlarmAcknowledged || !bControlPowerOn || bEmergencyStopActive
        || !bSafetyCircuitHealthy || !bGuardsClosed || !bCrossingClosed || !bCrossingClear || !bShuttleHealthy || bIsolationRequested) return false;
    ActiveFault = ELBPR010Fault::None;
    bAlarmAcknowledged = false;
    ActiveLaneIndex = -1;
    SetState(ELBPR010State::Ready);
    return true;
}

bool ALBPR010Station::RequestIsolation(FName CommandSource)
{
    bControlPowerOn = false; bIsolationRequested = true; bZeroEnergyProved = false;
    bControlledStopRequested = false; LastSafetyEvidenceId = NAME_None; LastCommandSource = CommandSource;
    SetState(ELBPR010State::Isolated); return true;
}

bool ALBPR010Station::ConfirmZeroEnergyIsolation(bool bZeroMotionVerified, bool bStoredEnergyReleased, FName EvidenceId)
{
    if (!bIsolationRequested || bControlPowerOn || State != ELBPR010State::Isolated
        || !bZeroMotionVerified || !bStoredEnergyReleased || EvidenceId.IsNone()) return false;
    bZeroEnergyProved = true; LastSafetyEvidenceId = EvidenceId; return true;
}

bool ALBPR010Station::ReleaseIsolation(FName CommandSource)
{
    if (!bIsolationRequested || !bZeroEnergyProved || !bGuardsClosed || !bCrossingClosed || !bCrossingClear
        || bEmergencyStopActive || !bSafetyCircuitHealthy) return false;
    bIsolationRequested = false; bZeroEnergyProved = false; bControlPowerOn = true; LastCommandSource = CommandSource;
    SetState(ELBPR010State::Ready); return true;
}

bool ALBPR010Station::ExecuteRemoteCommand(ELBPR010Command Command, FName CommandSource, FName AuthorityId)
{
    if (AuthorityId != RemoteAuthorityId || CommandSource.IsNone()) return false;
    LastCommandSource = CommandSource;
    switch (Command)
    {
    case ELBPR010Command::PowerOn:
        if (bIsolationRequested || bEmergencyStopActive) return false;
        bControlPowerOn = true; SetState(ELBPR010State::Ready); return true;
    case ELBPR010Command::PowerOff: bControlPowerOn = false; SetState(ELBPR010State::Isolated); return true;
    case ELBPR010Command::Start: return StartCycle();
    case ELBPR010Command::ControlledStop: RequestControlledStop(); return true;
    case ELBPR010Command::AcknowledgeAlarm: return AcknowledgeAlarm(CommandSource);
    case ELBPR010Command::Reset: return ResetFault();
    case ELBPR010Command::RequestIsolation: return RequestIsolation(CommandSource);
    case ELBPR010Command::ReleaseIsolation: return ReleaseIsolation(CommandSource);
    default: return false;
    }
}

void ALBPR010Station::ConfigureHealthyInputs()
{
    bGuardsClosed = true; bCrossingClosed = true; bCrossingClear = true; bShuttleHealthy = true;
    bVehicleHandoffReady = true; bSafetyCircuitHealthy = true; bEmergencyStopActive = false;
}

bool ALBPR010Station::CanAcceptUpstreamStack(TArray<FText>& Reasons) const
{
    Reasons.Reset();
    if (!bControlPowerOn) Reasons.Add(LOCTEXT("AcceptPower", "PR-010 control power is off."));
    if (State != ELBPR010State::Ready && State != ELBPR010State::ReservationWait && State != ELBPR010State::Stored)
        Reasons.Add(LOCTEXT("AcceptState", "PR-010 is not ready to accept a stack."));
    if (ActiveFault != ELBPR010Fault::None) Reasons.Add(LOCTEXT("AcceptFault", "PR-010 has an active fault."));
    if (!InboundStackId.IsNone()) Reasons.Add(LOCTEXT("AcceptOccupied", "PR-010 already owns an inbound stack."));
    if (!bGuardsClosed || !bCrossingClosed || !bCrossingClear || !bSafetyCircuitHealthy || bEmergencyStopActive || bIsolationRequested)
        Reasons.Add(LOCTEXT("AcceptSafety", "PR-010 safety state prevents receipt."));
    if (!bShuttleHealthy) Reasons.Add(LOCTEXT("AcceptShuttle", "PR-010 shuttle is unavailable."));
    if (FindAvailableLane() < 0 && !QualityHoldStackId.IsNone()) Reasons.Add(LOCTEXT("AcceptCapacity", "PR-010 storage and quality hold are full."));
    return Reasons.IsEmpty();
}

bool ALBPR010Station::OfferUpstreamStack(FName StackId, bool bRouteToQualityHold)
{
    if (StackId.IsNone()) return false;
    TArray<FText> Reasons;
    if (!CanAcceptUpstreamStack(Reasons)) return false;
    if (bRouteToQualityHold && !QualityHoldStackId.IsNone()) return false;
    InboundStackId = StackId; InboundBlankIds.Reset(); bInboundQualityHoldRequested = bRouteToQualityHold; return true;
}

bool ALBPR010Station::OfferUpstreamStackWithManifest(FName StackId, const TArray<FName>& BlankIds, bool bRouteToQualityHold)
{
    if (StackId.IsNone() || BlankIds.IsEmpty()) return false;
    TSet<FName> UniqueBlankIds;
    for (const FName BlankId : BlankIds)
    {
        if (BlankId.IsNone() || UniqueBlankIds.Contains(BlankId)) return false;
        UniqueBlankIds.Add(BlankId);
    }
    if (!OfferUpstreamStack(StackId, bRouteToQualityHold)) return false;
    InboundBlankIds = BlankIds;
    return true;
}

bool ALBPR010Station::GetBlankIdsForStack(FName StackId, TArray<FName>& BlankIds) const
{
    BlankIds.Reset();
    if (StackId.IsNone()) return false;
    if (InboundStackId == StackId && !InboundBlankIds.IsEmpty())
    {
        BlankIds = InboundBlankIds;
        return true;
    }
    if (LastReleasedStackId == StackId && !LastReleasedBlankIds.IsEmpty())
    {
        BlankIds = LastReleasedBlankIds;
        return true;
    }
    for (const FLBPR010StackManifest& Manifest : StoredStackManifests)
    {
        if (Manifest.StackId == StackId)
        {
            BlankIds = Manifest.BlankIds;
            return !BlankIds.IsEmpty();
        }
    }
    return false;
}

bool ALBPR010Station::RequestLaneDispatch(int32 LaneIndex, FName TrainReservationId)
{
    if (!GetLane(LaneIndex).IsValidIndex(0) || TrainReservationId.IsNone() || PendingDispatchLaneIndex >= 0
        || !LaneReservations.IsValidIndex(LaneIndex) || !LaneReservations[LaneIndex].IsNone()
        || (State != ELBPR010State::ReservationWait && State != ELBPR010State::Stored)) return false;
    LaneReservations[LaneIndex] = TrainReservationId;
    PendingDispatchLaneIndex = LaneIndex;
    return true;
}

void ALBPR010Station::SetGuardsClosed(bool bClosed) { bGuardsClosed = bClosed; EvaluatePermissives(); }
void ALBPR010Station::SetControlledCrossing(bool bClosed, bool bClear) { bCrossingClosed = bClosed; bCrossingClear = bClear; EvaluatePermissives(); }
void ALBPR010Station::SetShuttleHealthy(bool bHealthy) { bShuttleHealthy = bHealthy; EvaluatePermissives(); }
void ALBPR010Station::SetVehicleHandoffReady(bool bReady) { bVehicleHandoffReady = bReady; }
void ALBPR010Station::SetSafetyCircuitHealthy(bool bHealthy) { bSafetyCircuitHealthy = bHealthy; EvaluatePermissives(); }
void ALBPR010Station::SetEmergencyStopActive(bool bActive) { bEmergencyStopActive = bActive; if (bActive) bSafetyCircuitHealthy = false; EvaluatePermissives(); }

int32 ALBPR010Station::FindAvailableLane() const
{
    for (int32 Index = 0; Index < 4; ++Index)
        if (GetLane(Index).Num() < 2 && LaneReservations.IsValidIndex(Index) && LaneReservations[Index].IsNone()) return Index;
    return -1;
}

TArray<FName>& ALBPR010Station::GetLane(int32 LaneIndex)
{
    switch (LaneIndex) { case 0: return LaneAStackIds; case 1: return LaneBStackIds; case 2: return LaneCStackIds; default: return LaneDStackIds; }
}

const TArray<FName>& ALBPR010Station::GetLane(int32 LaneIndex) const
{
    switch (LaneIndex) { case 0: return LaneAStackIds; case 1: return LaneBStackIds; case 2: return LaneCStackIds; default: return LaneDStackIds; }
}

USceneComponent* ALBPR010Station::ResolvePresentationBindingTarget(FName ObjectName, FName SemanticRole) const
{
    const FString Object = ObjectName.ToString();
    const FString SemanticRoleString = SemanticRole.ToString();
    if (SemanticRoleString == TEXT("moving_infeed_shuttle") || Object.Contains(TEXT("M01_InfeedShuttle"))) return ShuttleMover;
    if (SemanticRoleString == TEXT("moving_quality_spur") || Object.Contains(TEXT("M06_QualityHold"))) return QualityHoldMover;
    auto LaneIndex = [&Object]() -> int32
    {
        if (Object.Contains(TEXT("LaneA"))) return 0; if (Object.Contains(TEXT("LaneB"))) return 1;
        if (Object.Contains(TEXT("LaneC"))) return 2; if (Object.Contains(TEXT("LaneD"))) return 3; return -1;
    }();
    if (LaneIndex >= 0 && SemanticRoleString == TEXT("moving_carrier_roller")) return LaneRollMovers[LaneIndex];
    if (LaneIndex >= 0 && SemanticRoleString == TEXT("moving_stop_pin")) return LaneStopMovers[LaneIndex];
    if (LaneIndex >= 0 && SemanticRoleString == TEXT("moving_reservation_gate")) return ReservationGateMovers[LaneIndex];
    return StationRoot;
}

bool ALBPR010Station::BindPresentationActor(FName ObjectName, FName SemanticRole, AActor* VisualActor)
{
    if (!VisualActor || !VisualActor->GetRootComponent() || ObjectName.IsNone()) return false;
    const FString Object = ObjectName.ToString();
    const FString BindingRole = SemanticRole.ToString();
    int32 LaneIndex = -1;
    if (Object.Contains(TEXT("LaneA"))) LaneIndex = 0;
    else if (Object.Contains(TEXT("LaneB"))) LaneIndex = 1;
    else if (Object.Contains(TEXT("LaneC"))) LaneIndex = 2;
    else if (Object.Contains(TEXT("LaneD"))) LaneIndex = 3;
    if (BindingRole == TEXT("moving_carrier_roller") && LaneIndex >= 0)
    {
        BoundRollActors.Add(VisualActor);
        BoundRollLaneIndices.Add(LaneIndex);
        return VisualActor->AttachToComponent(StationRoot, FAttachmentTransformRules::KeepWorldTransform);
    }
    if (BindingRole == TEXT("moving_reservation_gate") && LaneIndex >= 0)
    {
        BoundGateActors.Add(VisualActor);
        BoundGateLaneIndices.Add(LaneIndex);
        return VisualActor->AttachToComponent(StationRoot, FAttachmentTransformRules::KeepWorldTransform);
    }
    USceneComponent* Target = ResolvePresentationBindingTarget(ObjectName, SemanticRole);
    return Target && VisualActor->AttachToComponent(Target, FAttachmentTransformRules::KeepWorldTransform);
}

bool ALBPR010Station::BindHMITextActor(FName FieldName, ATextRenderActor* TextActor)
{
    if (FieldName.IsNone() || !IsValid(TextActor) || !TextActor->GetTextRender()) return false;
    static const TSet<FName> SupportedFields = {
        TEXT("State"), TEXT("Capacity"), TEXT("Fault"), TEXT("LastStack")};
    if (!SupportedFields.Contains(FieldName)) return false;
    BoundHMITextActors.Add(FieldName, TextActor);
    return true;
}

void ALBPR010Station::UpdateHMITextPresentation()
{
    if (BoundHMITextActors.IsEmpty()) return;
    auto StateLabel = [this]() -> FString
    {
        switch (State)
        {
        case ELBPR010State::Isolated: return TEXT("ISOLATED");
        case ELBPR010State::Ready: return TEXT("READY");
        case ELBPR010State::ReservationWait: return TEXT("RESERVATION WAIT");
        case ELBPR010State::LaneSelect: return TEXT("LANE SELECT");
        case ELBPR010State::Transfer: return TEXT("TRANSFER");
        case ELBPR010State::Stored: return TEXT("STORED");
        case ELBPR010State::TrainReserved: return TEXT("TRAIN RESERVED");
        case ELBPR010State::VehicleHandoff: return TEXT("VEHICLE HANDOFF");
        case ELBPR010State::Stopping: return TEXT("STOPPING");
        case ELBPR010State::Fault: return TEXT("FAULT");
        default: return TEXT("UNKNOWN");
        }
    };
    auto FaultLabel = [this]() -> FString
    {
        const UEnum* Enum = StaticEnum<ELBPR010Fault>();
        return Enum ? Enum->GetNameStringByValue(static_cast<int64>(ActiveFault)).ToUpper() : TEXT("UNKNOWN");
    };

    const int32 OccupiedLanePositions = LaneAStackIds.Num() + LaneBStackIds.Num() + LaneCStackIds.Num() + LaneDStackIds.Num();
    for (auto It = BoundHMITextActors.CreateIterator(); It; ++It)
    {
        ATextRenderActor* Actor = It.Value().Get();
        if (!IsValid(Actor) || !Actor->GetTextRender())
        {
            It.RemoveCurrent();
            continue;
        }
        UTextRenderComponent* Text = Actor->GetTextRender();
        if (It.Key() == TEXT("State"))
        {
            Text->SetText(FText::FromString(FString::Printf(TEXT("REMOTE %s"), *StateLabel())));
            Text->SetTextRenderColor(State == ELBPR010State::Fault ? FColor(230, 55, 45) : FColor(80, 230, 180));
        }
        else if (It.Key() == TEXT("Capacity"))
        {
            Text->SetText(FText::FromString(FString::Printf(TEXT("%d / 8 STACK POSITIONS"), OccupiedLanePositions)));
            Text->SetTextRenderColor(FColor(235, 240, 235));
        }
        else if (It.Key() == TEXT("Fault"))
        {
            Text->SetText(FText::FromString(ActiveFault == ELBPR010Fault::None ? TEXT("NO ACTIVE FAULT") : FString::Printf(TEXT("FAULT: %s"), *FaultLabel())));
            Text->SetTextRenderColor(ActiveFault == ELBPR010Fault::None ? FColor(80, 230, 180) : FColor(230, 55, 45));
        }
        else if (It.Key() == TEXT("LastStack"))
        {
            Text->SetText(FText::FromString(LastReleasedStackId.IsNone() ? TEXT("LAST RELEASE: --") : FString::Printf(TEXT("LAST RELEASE: %s"), *LastReleasedStackId.ToString())));
        }
    }
}

FLBPR010HMIStatus ALBPR010Station::GetHMIStatus() const
{
    FLBPR010HMIStatus H;
    H.State = State; H.ActiveFault = ActiveFault; H.ActiveLaneIndex = ActiveLaneIndex;
    H.LaneStackCounts = {LaneAStackIds.Num(), LaneBStackIds.Num(), LaneCStackIds.Num(), LaneDStackIds.Num()};
    H.LaneReservations = LaneReservations; H.InboundStackId = InboundStackId; H.QualityHoldStackId = QualityHoldStackId;
    H.LastReleasedStackId = LastReleasedStackId; H.TotalStacksStored = TotalStacksStored; H.TotalStacksDispatched = TotalStacksDispatched;
    H.LastReleasedBlankCount = LastReleasedBlankIds.Num();
    H.PhaseProgress = GetPhaseProgress(); H.bControlPowerOn = bControlPowerOn; H.bGuardsClosed = bGuardsClosed;
    H.bCrossingClosed = bCrossingClosed; H.bCrossingClear = bCrossingClear; H.bShuttleHealthy = bShuttleHealthy;
    H.bVehicleHandoffReady = bVehicleHandoffReady; H.bSafetyCircuitHealthy = bSafetyCircuitHealthy;
    H.bEmergencyStopActive = bEmergencyStopActive; H.bAlarmAcknowledged = bAlarmAcknowledged;
    H.bIsolationRequested = bIsolationRequested; H.bZeroEnergyProved = bZeroEnergyProved;
    H.bRestartRequiredAfterLoad = bRestartRequiredAfterLoad; H.LastCommandSource = LastCommandSource;
    H.LastSafetyEvidenceId = LastSafetyEvidenceId; H.bCanStart = CanStart(H.BlockingReasons);
    return H;
}

FLBPR010SaveState ALBPR010Station::CaptureSaveState() const
{
    FLBPR010SaveState S;
    S.State = State; S.ActiveFault = ActiveFault; S.LaneAStackIds = LaneAStackIds; S.LaneBStackIds = LaneBStackIds;
    S.LaneCStackIds = LaneCStackIds; S.LaneDStackIds = LaneDStackIds; S.LaneReservations = LaneReservations;
    S.ActiveLaneIndex = ActiveLaneIndex; S.PendingDispatchLaneIndex = PendingDispatchLaneIndex;
    S.InboundStackId = InboundStackId; S.QualityHoldStackId = QualityHoldStackId; S.LastReleasedStackId = LastReleasedStackId;
    S.InboundBlankIds = InboundBlankIds; S.StoredStackManifests = StoredStackManifests; S.LastReleasedBlankIds = LastReleasedBlankIds;
    S.TotalStacksStored = TotalStacksStored; S.TotalStacksDispatched = TotalStacksDispatched;
    S.bInboundQualityHoldRequested = bInboundQualityHoldRequested; S.bControlPowerOn = bControlPowerOn;
    S.bGuardsClosed = bGuardsClosed; S.bCrossingClosed = bCrossingClosed; S.bCrossingClear = bCrossingClear;
    S.bShuttleHealthy = bShuttleHealthy; S.bVehicleHandoffReady = bVehicleHandoffReady;
    S.bSafetyCircuitHealthy = bSafetyCircuitHealthy; S.bEmergencyStopActive = bEmergencyStopActive;
    S.bAlarmAcknowledged = bAlarmAcknowledged; S.bIsolationRequested = bIsolationRequested; S.bZeroEnergyProved = bZeroEnergyProved;
    S.bRestartRequiredAfterLoad = bRestartRequiredAfterLoad; S.LastCommandSource = LastCommandSource; S.LastSafetyEvidenceId = LastSafetyEvidenceId;
    return S;
}

bool ALBPR010Station::RestoreSaveState(const FLBPR010SaveState& S)
{
    if ((S.Version != 1 && S.Version != 2) || S.StationId != TEXT("PR-010") || S.LaneAStackIds.Num() > 2 || S.LaneBStackIds.Num() > 2
        || S.LaneCStackIds.Num() > 2 || S.LaneDStackIds.Num() > 2) return false;
    LaneAStackIds = S.LaneAStackIds; LaneBStackIds = S.LaneBStackIds; LaneCStackIds = S.LaneCStackIds; LaneDStackIds = S.LaneDStackIds;
    LaneReservations = S.LaneReservations; LaneReservations.SetNum(4); ActiveLaneIndex = S.ActiveLaneIndex;
    PendingDispatchLaneIndex = S.PendingDispatchLaneIndex; InboundStackId = S.InboundStackId;
    QualityHoldStackId = S.QualityHoldStackId; LastReleasedStackId = S.LastReleasedStackId;
    InboundBlankIds = S.Version >= 2 ? S.InboundBlankIds : TArray<FName>();
    StoredStackManifests = S.Version >= 2 ? S.StoredStackManifests : TArray<FLBPR010StackManifest>();
    LastReleasedBlankIds = S.Version >= 2 ? S.LastReleasedBlankIds : TArray<FName>();
    TotalStacksStored = FMath::Max(0, S.TotalStacksStored); TotalStacksDispatched = FMath::Max(0, S.TotalStacksDispatched);
    bInboundQualityHoldRequested = S.bInboundQualityHoldRequested; bControlPowerOn = S.bControlPowerOn;
    bGuardsClosed = S.bGuardsClosed; bCrossingClosed = S.bCrossingClosed; bCrossingClear = S.bCrossingClear;
    bShuttleHealthy = S.bShuttleHealthy; bVehicleHandoffReady = S.bVehicleHandoffReady;
    bSafetyCircuitHealthy = S.bSafetyCircuitHealthy; bEmergencyStopActive = S.bEmergencyStopActive;
    bAlarmAcknowledged = S.bAlarmAcknowledged; bIsolationRequested = S.bIsolationRequested; bZeroEnergyProved = S.bZeroEnergyProved;
    bRestartRequiredAfterLoad = S.bRestartRequiredAfterLoad; LastCommandSource = S.LastCommandSource; LastSafetyEvidenceId = S.LastSafetyEvidenceId;
    const bool bWasMoving = S.State == ELBPR010State::LaneSelect || S.State == ELBPR010State::Transfer
        || S.State == ELBPR010State::TrainReserved || S.State == ELBPR010State::VehicleHandoff || S.State == ELBPR010State::Stopping;
    ActiveFault = bWasMoving ? ELBPR010Fault::None : S.ActiveFault;
    State = !bControlPowerOn ? ELBPR010State::Isolated : (bWasMoving ? ELBPR010State::Ready : S.State);
    if (bWasMoving) { bAlarmAcknowledged = false; bRestartRequiredAfterLoad = true; ActiveLaneIndex = -1; PendingDispatchLaneIndex = -1; LaneReservations.Init(NAME_None, 4); }
    PhaseElapsedSeconds = 0.0f; bControlledStopRequested = false; return true;
}

#undef LOCTEXT_NAMESPACE
