#include "LBPR009Station.h"

#include "Components/SceneComponent.h"

#define LOCTEXT_NAMESPACE "CairnwellPR009"

ALBPR009Station::ALBPR009Station()
{
    PrimaryActorTick.bCanEverTick = true;
    StationRoot = CreateDefaultSubobject<USceneComponent>(TEXT("PR009_StationRoot"));
    SetRootComponent(StationRoot);

    for (int32 Index = 1; Index <= 9; ++Index)
    {
        USceneComponent* Mover = CreateDefaultSubobject<USceneComponent>(
            *FString::Printf(TEXT("PR009_InfeedRollMover_%02d"), Index));
        Mover->SetupAttachment(StationRoot);
        InfeedRollMovers.Add(Mover);
    }
    GantryBridgeMover = CreateDefaultSubobject<USceneComponent>(TEXT("PR009_GantryBridgeMover"));
    GantryBridgeMover->SetupAttachment(StationRoot);
    GantryCrossSlideMover = CreateDefaultSubobject<USceneComponent>(TEXT("PR009_GantryCrossSlideMover"));
    GantryCrossSlideMover->SetupAttachment(GantryBridgeMover);
    GantryZMover = CreateDefaultSubobject<USceneComponent>(TEXT("PR009_GantryZMover"));
    GantryZMover->SetupAttachment(GantryCrossSlideMover);
    LiftTableMover = CreateDefaultSubobject<USceneComponent>(TEXT("PR009_LiftTableMover"));
    LiftTableMover->SetupAttachment(StationRoot);
    SideJoggerLeftMover = CreateDefaultSubobject<USceneComponent>(TEXT("PR009_SideJoggerLeftMover"));
    SideJoggerLeftMover->SetupAttachment(StationRoot);
    SideJoggerRightMover = CreateDefaultSubobject<USceneComponent>(TEXT("PR009_SideJoggerRightMover"));
    SideJoggerRightMover->SetupAttachment(StationRoot);
    EndJoggerMover = CreateDefaultSubobject<USceneComponent>(TEXT("PR009_EndJoggerMover"));
    EndJoggerMover->SetupAttachment(StationRoot);
    SeparatorPickerMover = CreateDefaultSubobject<USceneComponent>(TEXT("PR009_SeparatorPickerMover"));
    SeparatorPickerMover->SetupAttachment(StationRoot);
    for (int32 Index = 1; Index <= 9; ++Index)
    {
        USceneComponent* Mover = CreateDefaultSubobject<USceneComponent>(
            *FString::Printf(TEXT("PR009_OutputRollMover_%02d"), Index));
        Mover->SetupAttachment(StationRoot);
        OutputRollMovers.Add(Mover);
    }
    ServiceDoorMover = CreateDefaultSubobject<USceneComponent>(TEXT("PR009_ServiceDoorMover"));
    ServiceDoorMover->SetupAttachment(StationRoot);
    // The v002 enclosure service-door hinge is fixed relative to the PR-009 datum.
    ServiceDoorMover->SetRelativeLocation(FVector(-73.0f, -231.5f, 0.0f));
}

void ALBPR009Station::BeginPlay()
{
    Super::BeginPlay();
    CapturePresentationBases();
    UpdatePresentation();
}

void ALBPR009Station::CapturePresentationBases()
{
    InfeedRollBaseTransforms.Reset();
    for (const USceneComponent* Mover : InfeedRollMovers)
        InfeedRollBaseTransforms.Add(Mover ? Mover->GetRelativeTransform() : FTransform::Identity);
    OutputRollBaseTransforms.Reset();
    for (const USceneComponent* Mover : OutputRollMovers)
        OutputRollBaseTransforms.Add(Mover ? Mover->GetRelativeTransform() : FTransform::Identity);
    GantryBridgeBaseTransform = GantryBridgeMover->GetRelativeTransform();
    GantryCrossSlideBaseTransform = GantryCrossSlideMover->GetRelativeTransform();
    GantryZBaseTransform = GantryZMover->GetRelativeTransform();
    LiftTableBaseTransform = LiftTableMover->GetRelativeTransform();
    SideJoggerLeftBaseTransform = SideJoggerLeftMover->GetRelativeTransform();
    SideJoggerRightBaseTransform = SideJoggerRightMover->GetRelativeTransform();
    EndJoggerBaseTransform = EndJoggerMover->GetRelativeTransform();
    SeparatorPickerBaseTransform = SeparatorPickerMover->GetRelativeTransform();
    ServiceDoorBaseTransform = ServiceDoorMover->GetRelativeTransform();
    bPresentationBasesCaptured = true;
}

void ALBPR009Station::ApplyPresentationOffset(USceneComponent* Component, const FTransform& BaseTransform,
    const FVector& TranslationOffset, const FRotator& RotationOffset)
{
    if (!Component) return;
    Component->SetRelativeLocationAndRotation(
        BaseTransform.GetLocation() + TranslationOffset,
        BaseTransform.Rotator() + RotationOffset);
}

void ALBPR009Station::UpdatePresentation()
{
    if (!bPresentationBasesCaptured) CapturePresentationBases();
    const float Progress = GetPhaseProgress();
    const float Smooth = FMath::InterpEaseInOut(0.0f, 1.0f, Progress, 2.0f);
    const float Pulse = FMath::Sin(Progress * PI);
    const float InfeedDegrees = State == ELBPR009State::Receiving ? Progress * 1080.0f : 0.0f;
    const float OutputDegrees = State == ELBPR009State::Releasing ? Progress * 1080.0f : 0.0f;
    for (int32 Index = 0; Index < InfeedRollMovers.Num(); ++Index)
        ApplyPresentationOffset(InfeedRollMovers[Index], InfeedRollBaseTransforms[Index], FVector::ZeroVector,
            FRotator(InfeedDegrees, 0.0f, 0.0f));
    for (int32 Index = 0; Index < OutputRollMovers.Num(); ++Index)
        ApplyPresentationOffset(OutputRollMovers[Index], OutputRollBaseTransforms[Index], FVector::ZeroVector,
            FRotator(OutputDegrees, 0.0f, 0.0f));

    const bool bStacking = State == ELBPR009State::Stacking;
    const float StackLane = TargetStackBlankCount > 1
        ? static_cast<float>(CurrentStackBlankCount % 5) / 4.0f : 0.5f;
    ApplyPresentationOffset(GantryBridgeMover, GantryBridgeBaseTransform,
        FVector(0.0f, bStacking ? 280.0f * StackLane : 0.0f, 0.0f), FRotator::ZeroRotator);
    ApplyPresentationOffset(GantryCrossSlideMover, GantryCrossSlideBaseTransform,
        FVector(bStacking ? FMath::Lerp(-40.0f, 40.0f, StackLane) : 0.0f, 0.0f, 0.0f), FRotator::ZeroRotator);
    ApplyPresentationOffset(GantryZMover, GantryZBaseTransform,
        FVector(0.0f, 0.0f, bStacking ? -130.0f * Pulse : 0.0f), FRotator::ZeroRotator);
    ApplyPresentationOffset(LiftTableMover, LiftTableBaseTransform,
        FVector(0.0f, 0.0f, bStacking ? 60.0f * Smooth : 0.0f), FRotator::ZeroRotator);

    const float JogTravel = State == ELBPR009State::Centering ? 30.0f * Pulse : 0.0f;
    ApplyPresentationOffset(SideJoggerLeftMover, SideJoggerLeftBaseTransform,
        FVector(JogTravel, 0.0f, 0.0f), FRotator::ZeroRotator);
    ApplyPresentationOffset(SideJoggerRightMover, SideJoggerRightBaseTransform,
        FVector(-JogTravel, 0.0f, 0.0f), FRotator::ZeroRotator);
    ApplyPresentationOffset(EndJoggerMover, EndJoggerBaseTransform,
        FVector(0.0f, State == ELBPR009State::Centering ? -35.0f * Pulse : 0.0f, 0.0f), FRotator::ZeroRotator);
    ApplyPresentationOffset(SeparatorPickerMover, SeparatorPickerBaseTransform,
        FVector(0.0f, State == ELBPR009State::SeparatorPlacement ? 50.0f * Smooth : 0.0f,
            State == ELBPR009State::SeparatorPlacement ? -35.0f * Pulse : 0.0f),
        FRotator::ZeroRotator);
    ServiceDoorMover->SetRelativeLocationAndRotation(
        ServiceDoorBaseTransform.GetLocation(),
        ServiceDoorBaseTransform.Rotator() + FRotator(0.0f, ServiceDoorAngleDegrees, 0.0f));
}

void ALBPR009Station::SetState(ELBPR009State NewState)
{
    if (State == NewState) return;
    const ELBPR009State Previous = State;
    State = NewState;
    PhaseElapsedSeconds = 0.0f;
    OnStateChanged.Broadcast(Previous, State);
}

bool ALBPR009Station::IsMovingState() const
{
    return State == ELBPR009State::Receiving || State == ELBPR009State::Centering
        || State == ELBPR009State::Stacking || State == ELBPR009State::SeparatorPlacement
        || State == ELBPR009State::Releasing || State == ELBPR009State::Stopping;
}

float ALBPR009Station::GetPhaseDuration() const
{
    switch (State)
    {
    case ELBPR009State::Receiving: return 1.0f;
    case ELBPR009State::Centering: return 0.5f;
    case ELBPR009State::Stacking: return 0.75f;
    case ELBPR009State::SeparatorPlacement: return 0.4f;
    case ELBPR009State::Releasing: return 1.0f;
    case ELBPR009State::Stopping: return 0.5f;
    default: return 0.0f;
    }
}

float ALBPR009Station::GetPhaseProgress() const
{
    const float Duration = GetPhaseDuration();
    return Duration > 0.0f ? FMath::Clamp(PhaseElapsedSeconds / Duration, 0.0f, 1.0f) : 0.0f;
}

void ALBPR009Station::Tick(float DeltaSeconds)
{
    Super::Tick(DeltaSeconds);
    ServiceDoorAngleDegrees = FMath::FInterpConstantTo(
        ServiceDoorAngleDegrees, bGuardsClosed ? 0.0f : 105.0f, DeltaSeconds, 90.0f);
    if (!IsMovingState()) { UpdatePresentation(); return; }
    EvaluatePermissives();
    if (State == ELBPR009State::Fault) { UpdatePresentation(); return; }
    if (State == ELBPR009State::Receiving && !bUpstreamBlankAvailable)
    {
        PhaseElapsedSeconds = 0.0f;
        UpdatePresentation();
        return;
    }
    PhaseElapsedSeconds += FMath::Max(0.0f, DeltaSeconds);
    if (PhaseElapsedSeconds < GetPhaseDuration()) { UpdatePresentation(); return; }

    switch (State)
    {
    case ELBPR009State::Receiving:
        bUpstreamBlankAvailable = false;
        SetState(ELBPR009State::Centering);
        break;
    case ELBPR009State::Centering:
        if (!bVisionHealthy) { ++RejectedBlanks; RaiseFault(ELBPR009Fault::VisionReject); return; }
        SetState(ELBPR009State::Stacking);
        break;
    case ELBPR009State::Stacking:
        if (!CurrentBlankId.IsNone()) CurrentStackBlankIds.Add(CurrentBlankId);
        ++CurrentStackBlankCount;
        ++TotalBlanksStacked;
        CurrentBlankId = NAME_None;
        if (CurrentStackBlankCount >= TargetStackBlankCount) SetState(ELBPR009State::Releasing);
        else if (SeparatorInterval > 0 && CurrentStackBlankCount % SeparatorInterval == 0) SetState(ELBPR009State::SeparatorPlacement);
        else if (bControlledStopRequested) SetState(ELBPR009State::Stopping);
        else { SetState(ELBPR009State::Receiving); }
        break;
    case ELBPR009State::SeparatorPlacement:
        if (!bSeparatorAvailable) { RaiseFault(ELBPR009Fault::SeparatorEmpty); return; }
        ++SeparatorSheetsPlaced;
        if (bControlledStopRequested) SetState(ELBPR009State::Stopping);
        else { SetState(ELBPR009State::Receiving); }
        break;
    case ELBPR009State::Releasing:
        if (!PendingReleasedStackId.IsNone())
        {
            PhaseElapsedSeconds = 0.0f;
            UpdatePresentation();
            return;
        }
        if (!bCarrierAvailable) { RaiseFault(ELBPR009Fault::CarrierUnavailable); return; }
        if (!bOutfeedClear) { RaiseFault(ELBPR009Fault::OutfeedBlocked); return; }
        PendingReleasedStackId = CurrentCarrierId;
        PendingReleasedBlankIds = MoveTemp(CurrentStackBlankIds);
        PendingStackHandoffTransactionId = NAME_None;
        ++CarriersReleased;
        CurrentStackBlankCount = 0;
        CurrentCarrierId = FName(*FString::Printf(TEXT("PR009-CARRIER-%04d"), CarriersReleased + 1));
        if (bControlledStopRequested) SetState(ELBPR009State::Stopping);
        else { SetState(ELBPR009State::Receiving); }
        break;
    case ELBPR009State::Stopping:
        bControlledStopRequested = false;
        SetState(ELBPR009State::Ready);
        break;
    default:
        break;
    }
    UpdatePresentation();
}

void ALBPR009Station::RaiseFault(ELBPR009Fault Fault)
{
    if (Fault == ELBPR009Fault::None) return;
    ActiveFault = Fault;
    bAlarmAcknowledged = false;
    SetState(ELBPR009State::Fault);
    OnFaultRaised.Broadcast(Fault);
}

void ALBPR009Station::EvaluatePermissives()
{
    if (bEmergencyStopActive) RaiseFault(ELBPR009Fault::EmergencyStopActive);
    else if (!bSafetyCircuitHealthy) RaiseFault(ELBPR009Fault::SafetyCircuitFault);
    else if (!bGuardsClosed) RaiseFault(ELBPR009Fault::GuardOpen);
    else if (!bReceiverClear && State == ELBPR009State::Receiving) RaiseFault(ELBPR009Fault::ReceiverBlocked);
    else if (!bGantryHealthy) RaiseFault(ELBPR009Fault::GantryFault);
    else if (!bVacuumHealthy) RaiseFault(ELBPR009Fault::VacuumLoss);
    else if (!bLiftTableHealthy) RaiseFault(ELBPR009Fault::LiftTableFault);
    else if (!bJoggersHealthy) RaiseFault(ELBPR009Fault::JoggerFault);
    else if (CurrentStackBlankCount > TargetStackBlankCount) RaiseFault(ELBPR009Fault::StackHeightLimit);
}

bool ALBPR009Station::CanStart(TArray<FText>& Reasons) const
{
    Reasons.Reset();
    if (!bControlPowerOn) Reasons.Add(LOCTEXT("NoPower", "Control power is off."));
    if (State != ELBPR009State::Ready) Reasons.Add(LOCTEXT("NotReady", "Station is not ready."));
    if (ActiveFault != ELBPR009Fault::None) Reasons.Add(LOCTEXT("Faulted", "A fault is active."));
    if (!bGuardsClosed) Reasons.Add(LOCTEXT("GuardOpen", "A guard is open."));
    if (!bSafetyCircuitHealthy || bEmergencyStopActive) Reasons.Add(LOCTEXT("Safety", "Safety circuit is not healthy."));
    if (!bReceiverClear) Reasons.Add(LOCTEXT("Receiver", "Receiver is blocked."));
    if (!bVisionHealthy || !bGantryHealthy || !bVacuumHealthy || !bLiftTableHealthy || !bJoggersHealthy)
        Reasons.Add(LOCTEXT("Mechanisms", "One or more stacking mechanisms are unavailable."));
    if (!bSeparatorAvailable) Reasons.Add(LOCTEXT("Separator", "Separator stock is unavailable."));
    if (!bCarrierAvailable || !bOutfeedClear) Reasons.Add(LOCTEXT("Carrier", "Carrier release route is unavailable."));
    if (bIsolationRequested || bZeroEnergyProved) Reasons.Add(LOCTEXT("Isolated", "Station is isolated."));
    return Reasons.IsEmpty();
}

bool ALBPR009Station::StartCycle()
{
    TArray<FText> Reasons;
    if (!CanStart(Reasons)) return false;
    bControlledStopRequested = false;
    bRestartRequiredAfterLoad = false;
    SetState(ELBPR009State::Receiving);
    return true;
}

void ALBPR009Station::RequestControlledStop()
{
    if (IsMovingState()) bControlledStopRequested = true;
}

bool ALBPR009Station::AcknowledgeAlarm(FName CommandSource)
{
    if (ActiveFault == ELBPR009Fault::None) return false;
    bAlarmAcknowledged = true;
    LastCommandSource = CommandSource;
    return true;
}

bool ALBPR009Station::ResetFault()
{
    if (State != ELBPR009State::Fault || ActiveFault == ELBPR009Fault::None || !bAlarmAcknowledged
        || !bControlPowerOn || bEmergencyStopActive || !bSafetyCircuitHealthy || bIsolationRequested) return false;
    const ELBPR009State Previous = State;
    const ELBPR009Fault PreviousFault = ActiveFault;
    State = ELBPR009State::Ready;
    ActiveFault = ELBPR009Fault::None;
    TArray<FText> Reasons;
    const bool bHealthy = CanStart(Reasons);
    State = Previous;
    ActiveFault = PreviousFault;
    if (!bHealthy) return false;
    ActiveFault = ELBPR009Fault::None;
    bAlarmAcknowledged = false;
    SetState(ELBPR009State::Ready);
    return true;
}

bool ALBPR009Station::RequestIsolation(FName CommandSource)
{
    if (IsMovingState()) RequestControlledStop();
    bControlPowerOn = false;
    bIsolationRequested = true;
    bZeroEnergyProved = false;
    LastSafetyEvidenceId = NAME_None;
    LastCommandSource = CommandSource;
    SetState(ELBPR009State::Isolated);
    return true;
}

bool ALBPR009Station::ConfirmZeroEnergyIsolation(bool bZeroMotionVerified, bool bPneumaticEnergyReleased, FName EvidenceId)
{
    if (!bIsolationRequested || bControlPowerOn || State != ELBPR009State::Isolated
        || !bZeroMotionVerified || !bPneumaticEnergyReleased || EvidenceId.IsNone()) return false;
    bZeroEnergyProved = true;
    LastSafetyEvidenceId = EvidenceId;
    return true;
}

bool ALBPR009Station::ReleaseIsolation(FName CommandSource)
{
    if (!bIsolationRequested || !bZeroEnergyProved || !bGuardsClosed || bEmergencyStopActive || !bSafetyCircuitHealthy) return false;
    bIsolationRequested = false;
    bZeroEnergyProved = false;
    bControlPowerOn = true;
    LastCommandSource = CommandSource;
    SetState(ELBPR009State::Ready);
    return true;
}

bool ALBPR009Station::ExecuteRemoteCommand(ELBPR009Command Command, FName CommandSource, FName AuthorityId)
{
    if (AuthorityId != RemoteAuthorityId || CommandSource.IsNone()) return false;
    LastCommandSource = CommandSource;
    switch (Command)
    {
    case ELBPR009Command::PowerOn:
        if (bIsolationRequested || bEmergencyStopActive) return false;
        bControlPowerOn = true; SetState(ELBPR009State::Ready); return true;
    case ELBPR009Command::PowerOff:
        bControlPowerOn = false; SetState(ELBPR009State::Isolated); return true;
    case ELBPR009Command::Start: return StartCycle();
    case ELBPR009Command::ControlledStop: RequestControlledStop(); return true;
    case ELBPR009Command::AcknowledgeAlarm: return AcknowledgeAlarm(CommandSource);
    case ELBPR009Command::Reset: return ResetFault();
    case ELBPR009Command::RequestIsolation: return RequestIsolation(CommandSource);
    case ELBPR009Command::ReleaseIsolation: return ReleaseIsolation(CommandSource);
    default: return false;
    }
}

void ALBPR009Station::ConfigureHealthyInputs(bool bBlankAvailable)
{
    bGuardsClosed = true; bUpstreamBlankAvailable = bBlankAvailable; bReceiverClear = true;
    bVisionHealthy = true; bGantryHealthy = true; bVacuumHealthy = true; bLiftTableHealthy = true;
    bJoggersHealthy = true; bSeparatorAvailable = true; bCarrierAvailable = true; bOutfeedClear = true;
    bSafetyCircuitHealthy = true; bEmergencyStopActive = false;
}

void ALBPR009Station::SetUpstreamBlankAvailable(bool bAvailable, FName BlankId)
{
    bUpstreamBlankAvailable = bAvailable;
    if (!BlankId.IsNone()) CurrentBlankId = BlankId;
    else if (!bAvailable) CurrentBlankId = NAME_None;
}

bool ALBPR009Station::CanAcceptUpstreamBlank(TArray<FText>& BlockingReasons) const
{
    BlockingReasons.Reset();
    if (!bControlPowerOn) BlockingReasons.Add(LOCTEXT("BlankAcceptNoPower", "PR-009 control power is off"));
    if (State != ELBPR009State::Ready && State != ELBPR009State::Receiving)
        BlockingReasons.Add(LOCTEXT("BlankAcceptState", "PR-009 is not ready to receive a blank"));
    if (ActiveFault != ELBPR009Fault::None) BlockingReasons.Add(LOCTEXT("BlankAcceptFault", "PR-009 has an active fault"));
    if (bUpstreamBlankAvailable || !CurrentBlankId.IsNone())
        BlockingReasons.Add(LOCTEXT("BlankAcceptOccupied", "PR-009 already owns an identified inbound blank"));
    if (!bReceiverClear) BlockingReasons.Add(LOCTEXT("BlankAcceptReceiver", "PR-009 receiver is blocked"));
    if (!bGuardsClosed || bEmergencyStopActive || !bSafetyCircuitHealthy || bIsolationRequested)
        BlockingReasons.Add(LOCTEXT("BlankAcceptSafety", "PR-009 safety or isolation state prevents blank receipt"));
    return BlockingReasons.IsEmpty();
}

bool ALBPR009Station::AcceptUpstreamBlank(FName BlankId)
{
    if (BlankId.IsNone()) return false;
    TArray<FText> BlockingReasons;
    if (!CanAcceptUpstreamBlank(BlockingReasons)) return false;
    CurrentBlankId = BlankId;
    bUpstreamBlankAvailable = true;
    return true;
}

bool ALBPR009Station::CanReleaseCompletedStack(TArray<FText>& BlockingReasons) const
{
    BlockingReasons.Reset();
    if (PendingReleasedStackId.IsNone())
        BlockingReasons.Add(LOCTEXT("StackHandoffNone", "PR-009 has no released stack awaiting handoff"));
    if (PendingReleasedBlankIds.IsEmpty())
        BlockingReasons.Add(LOCTEXT("StackHandoffEmptyManifest", "The released stack has no traceable blank manifest"));
    if (!PendingReleasedStackId.IsNone() && PendingReleasedBlankIds.Num() != TargetStackBlankCount)
        BlockingReasons.Add(LOCTEXT("StackHandoffIncompleteManifest", "The released stack blank manifest is incomplete"));
    if (!PendingStackHandoffTransactionId.IsNone())
        BlockingReasons.Add(LOCTEXT("StackHandoffReserved", "The released stack is already reserved by another transaction"));
    return BlockingReasons.IsEmpty();
}

bool ALBPR009Station::RequestStackHandoff(FName TransactionId, FName& StackId, TArray<FName>& BlankIds)
{
    StackId = NAME_None;
    BlankIds.Reset();
    if (TransactionId.IsNone()) return false;
    TArray<FText> BlockingReasons;
    if (!CanReleaseCompletedStack(BlockingReasons)) return false;
    PendingStackHandoffTransactionId = TransactionId;
    StackId = PendingReleasedStackId;
    BlankIds = PendingReleasedBlankIds;
    return true;
}

bool ALBPR009Station::ConfirmStackHandoff(FName TransactionId)
{
    if (TransactionId.IsNone() || PendingStackHandoffTransactionId != TransactionId) return false;
    PendingReleasedStackId = NAME_None;
    PendingReleasedBlankIds.Reset();
    PendingStackHandoffTransactionId = NAME_None;
    return true;
}

bool ALBPR009Station::CancelStackHandoff(FName TransactionId)
{
    if (TransactionId.IsNone() || PendingStackHandoffTransactionId != TransactionId) return false;
    PendingStackHandoffTransactionId = NAME_None;
    return true;
}

USceneComponent* ALBPR009Station::ResolvePresentationBindingTarget(FName SemanticObjectName,
    FName SemanticRole, FName IntendedBindingParent) const
{
    const FString Object = SemanticObjectName.ToString();
    const FString SemanticRoleString = SemanticRole.ToString();
    const FString Parent = IntendedBindingParent.ToString();
    auto ParseTrailingIndex = [](const FString& Value) -> int32
    {
        FString Left;
        FString Right;
        return Value.Split(TEXT("_"), &Left, &Right, ESearchCase::CaseSensitive, ESearchDir::FromEnd)
            ? FCString::Atoi(*Right) : 0;
    };
    if (Object.StartsWith(TEXT("PR009_M01_InfeedRoll_")))
    {
        const int32 Index = ParseTrailingIndex(Object) - 1;
        return InfeedRollMovers.IsValidIndex(Index) ? InfeedRollMovers[Index].Get() : nullptr;
    }
    if (SemanticRoleString == TEXT("moving_output_roller") || Object.StartsWith(TEXT("PR009_08_OutputRoll_")))
    {
        const int32 Index = ParseTrailingIndex(Object) - 1;
        return OutputRollMovers.IsValidIndex(Index) ? OutputRollMovers[Index].Get() : nullptr;
    }
    if (Object.StartsWith(TEXT("PR009_M04_")) || Parent == TEXT("PR009_M04_GantryZ_Carriage_01")) return GantryZMover;
    if (Object.StartsWith(TEXT("PR009_M03_")) || Parent == TEXT("PR009_M03_GantryCrossSlide_01")) return GantryCrossSlideMover;
    if (Object.StartsWith(TEXT("PR009_M02_")) || Parent == TEXT("PR009_M02_GantryBridge_01")) return GantryBridgeMover;
    if (Object.StartsWith(TEXT("PR009_M05_"))) return LiftTableMover;
    if (Object == TEXT("PR009_M06_SideJogger_L")) return SideJoggerLeftMover;
    if (Object == TEXT("PR009_M06_SideJogger_R")) return SideJoggerRightMover;
    if (Object.StartsWith(TEXT("PR009_M07_"))) return EndJoggerMover;
    if (Object.StartsWith(TEXT("PR009_M08_")) || Parent == TEXT("PR009_M08_SeparatorPicker_01")) return SeparatorPickerMover;
    if (SemanticRoleString == TEXT("service_door") || Object == TEXT("PR009_ENC_ServiceDoor_01")) return ServiceDoorMover;
    return StationRoot;
}

bool ALBPR009Station::BindPresentationActor(FName SemanticObjectName, FName SemanticRole,
    FName IntendedBindingParent, AActor* VisualActor)
{
    if (!VisualActor || !VisualActor->GetRootComponent() || SemanticObjectName.IsNone()) return false;
    USceneComponent* Target = ResolvePresentationBindingTarget(SemanticObjectName, SemanticRole, IntendedBindingParent);
    if (!Target) return false;
    return VisualActor->AttachToComponent(Target, FAttachmentTransformRules::KeepWorldTransform);
}
void ALBPR009Station::SetReceiverClear(bool bClear) { bReceiverClear = bClear; EvaluatePermissives(); }
void ALBPR009Station::SetVisionHealthy(bool bHealthy) { bVisionHealthy = bHealthy; EvaluatePermissives(); }
void ALBPR009Station::SetGantryHealthy(bool bHealthy) { bGantryHealthy = bHealthy; EvaluatePermissives(); }
void ALBPR009Station::SetVacuumHealthy(bool bHealthy) { bVacuumHealthy = bHealthy; EvaluatePermissives(); }
void ALBPR009Station::SetLiftTableHealthy(bool bHealthy) { bLiftTableHealthy = bHealthy; EvaluatePermissives(); }
void ALBPR009Station::SetJoggersHealthy(bool bHealthy) { bJoggersHealthy = bHealthy; EvaluatePermissives(); }
void ALBPR009Station::SetSeparatorAvailable(bool bAvailable) { bSeparatorAvailable = bAvailable; }
void ALBPR009Station::SetCarrierAvailable(bool bAvailable, FName CarrierId) { bCarrierAvailable = bAvailable; if (!CarrierId.IsNone()) CurrentCarrierId = CarrierId; }
void ALBPR009Station::SetOutfeedClear(bool bClear) { bOutfeedClear = bClear; }
void ALBPR009Station::SetGuardsClosed(bool bClosed) { bGuardsClosed = bClosed; EvaluatePermissives(); }
void ALBPR009Station::SetSafetyCircuitHealthy(bool bHealthy) { bSafetyCircuitHealthy = bHealthy; EvaluatePermissives(); }
void ALBPR009Station::SetEmergencyStopActive(bool bActive) { bEmergencyStopActive = bActive; if (bActive) bSafetyCircuitHealthy = false; EvaluatePermissives(); }

void ALBPR009Station::SetStackRecipe(int32 StackBlankCount, int32 InSeparatorInterval, float BlankThicknessMm)
{
    TargetStackBlankCount = FMath::Clamp(StackBlankCount, 1, 500);
    SeparatorInterval = FMath::Clamp(InSeparatorInterval, 0, TargetStackBlankCount);
    NominalBlankThicknessMm = FMath::Clamp(BlankThicknessMm, 0.3f, 8.0f);
}

FLBPR009HMIStatus ALBPR009Station::GetHMIStatus() const
{
    FLBPR009HMIStatus Status;
    Status.State = State; Status.ActiveFault = ActiveFault; Status.CurrentStackBlankCount = CurrentStackBlankCount;
    Status.TargetStackBlankCount = TargetStackBlankCount; Status.TotalBlanksStacked = TotalBlanksStacked;
    Status.SeparatorSheetsPlaced = SeparatorSheetsPlaced; Status.CarriersReleased = CarriersReleased;
    Status.RejectedBlanks = RejectedBlanks; Status.StackHeightMm = CurrentStackBlankCount * NominalBlankThicknessMm;
    Status.PhaseProgress = GetPhaseProgress(); Status.CurrentCarrierId = CurrentCarrierId; Status.CurrentBlankId = CurrentBlankId;
    Status.PendingReleasedStackId = PendingReleasedStackId; Status.PendingReleasedBlankCount = PendingReleasedBlankIds.Num();
    Status.bControlPowerOn = bControlPowerOn; Status.bGuardsClosed = bGuardsClosed;
    Status.bUpstreamBlankAvailable = bUpstreamBlankAvailable; Status.bReceiverClear = bReceiverClear;
    Status.bVisionHealthy = bVisionHealthy; Status.bGantryHealthy = bGantryHealthy; Status.bVacuumHealthy = bVacuumHealthy;
    Status.bLiftTableHealthy = bLiftTableHealthy; Status.bJoggersHealthy = bJoggersHealthy;
    Status.bSeparatorAvailable = bSeparatorAvailable; Status.bCarrierAvailable = bCarrierAvailable; Status.bOutfeedClear = bOutfeedClear;
    Status.bSafetyCircuitHealthy = bSafetyCircuitHealthy; Status.bEmergencyStopActive = bEmergencyStopActive;
    Status.bAlarmAcknowledged = bAlarmAcknowledged; Status.bIsolationRequested = bIsolationRequested;
    Status.bZeroEnergyProved = bZeroEnergyProved; Status.bRestartRequiredAfterLoad = bRestartRequiredAfterLoad;
    Status.LastCommandSource = LastCommandSource; Status.LastSafetyEvidenceId = LastSafetyEvidenceId;
    Status.bCanStart = CanStart(Status.BlockingReasons);
    return Status;
}

FLBPR009SaveState ALBPR009Station::CaptureSaveState() const
{
    FLBPR009SaveState S;
    S.State = State; S.ActiveFault = ActiveFault; S.CurrentStackBlankCount = CurrentStackBlankCount;
    S.TargetStackBlankCount = TargetStackBlankCount; S.SeparatorInterval = SeparatorInterval;
    S.TotalBlanksStacked = TotalBlanksStacked; S.SeparatorSheetsPlaced = SeparatorSheetsPlaced;
    S.CarriersReleased = CarriersReleased; S.RejectedBlanks = RejectedBlanks; S.NominalBlankThicknessMm = NominalBlankThicknessMm;
    S.CurrentCarrierId = CurrentCarrierId; S.CurrentBlankId = CurrentBlankId; S.bControlPowerOn = bControlPowerOn;
    S.CurrentStackBlankIds = CurrentStackBlankIds; S.PendingReleasedStackId = PendingReleasedStackId;
    S.PendingReleasedBlankIds = PendingReleasedBlankIds; S.PendingStackHandoffTransactionId = PendingStackHandoffTransactionId;
    S.bGuardsClosed = bGuardsClosed; S.bUpstreamBlankAvailable = bUpstreamBlankAvailable; S.bReceiverClear = bReceiverClear;
    S.bVisionHealthy = bVisionHealthy; S.bGantryHealthy = bGantryHealthy; S.bVacuumHealthy = bVacuumHealthy;
    S.bLiftTableHealthy = bLiftTableHealthy; S.bJoggersHealthy = bJoggersHealthy; S.bSeparatorAvailable = bSeparatorAvailable;
    S.bCarrierAvailable = bCarrierAvailable; S.bOutfeedClear = bOutfeedClear; S.bSafetyCircuitHealthy = bSafetyCircuitHealthy;
    S.bEmergencyStopActive = bEmergencyStopActive; S.bAlarmAcknowledged = bAlarmAcknowledged;
    S.bIsolationRequested = bIsolationRequested; S.bZeroEnergyProved = bZeroEnergyProved;
    S.bRestartRequiredAfterLoad = bRestartRequiredAfterLoad; S.LastCommandSource = LastCommandSource;
    S.LastSafetyEvidenceId = LastSafetyEvidenceId;
    return S;
}

bool ALBPR009Station::RestoreSaveState(const FLBPR009SaveState& S)
{
    if ((S.Version != 1 && S.Version != 2) || S.StationId != TEXT("PR-009")) return false;
    ActiveFault = S.ActiveFault; CurrentStackBlankCount = FMath::Max(0, S.CurrentStackBlankCount);
    TargetStackBlankCount = FMath::Clamp(S.TargetStackBlankCount, 1, 500);
    SeparatorInterval = FMath::Clamp(S.SeparatorInterval, 0, TargetStackBlankCount);
    TotalBlanksStacked = FMath::Max(0, S.TotalBlanksStacked); SeparatorSheetsPlaced = FMath::Max(0, S.SeparatorSheetsPlaced);
    CarriersReleased = FMath::Max(0, S.CarriersReleased); RejectedBlanks = FMath::Max(0, S.RejectedBlanks);
    NominalBlankThicknessMm = FMath::Clamp(S.NominalBlankThicknessMm, 0.3f, 8.0f);
    CurrentCarrierId = S.CurrentCarrierId; CurrentBlankId = S.CurrentBlankId; bControlPowerOn = S.bControlPowerOn;
    CurrentStackBlankIds = S.Version >= 2 ? S.CurrentStackBlankIds : TArray<FName>();
    PendingReleasedStackId = S.Version >= 2 ? S.PendingReleasedStackId : NAME_None;
    PendingReleasedBlankIds = S.Version >= 2 ? S.PendingReleasedBlankIds : TArray<FName>();
    PendingStackHandoffTransactionId = S.Version >= 2 ? S.PendingStackHandoffTransactionId : NAME_None;
    bGuardsClosed = S.bGuardsClosed; bUpstreamBlankAvailable = S.bUpstreamBlankAvailable; bReceiverClear = S.bReceiverClear;
    bVisionHealthy = S.bVisionHealthy; bGantryHealthy = S.bGantryHealthy; bVacuumHealthy = S.bVacuumHealthy;
    bLiftTableHealthy = S.bLiftTableHealthy; bJoggersHealthy = S.bJoggersHealthy; bSeparatorAvailable = S.bSeparatorAvailable;
    bCarrierAvailable = S.bCarrierAvailable; bOutfeedClear = S.bOutfeedClear; bSafetyCircuitHealthy = S.bSafetyCircuitHealthy;
    bEmergencyStopActive = S.bEmergencyStopActive; bAlarmAcknowledged = S.bAlarmAcknowledged;
    bIsolationRequested = S.bIsolationRequested; bZeroEnergyProved = S.bZeroEnergyProved;
    bRestartRequiredAfterLoad = S.bRestartRequiredAfterLoad; LastCommandSource = S.LastCommandSource;
    LastSafetyEvidenceId = S.LastSafetyEvidenceId;
    const bool bWasMoving = S.State == ELBPR009State::Receiving || S.State == ELBPR009State::Centering
        || S.State == ELBPR009State::Stacking || S.State == ELBPR009State::SeparatorPlacement
        || S.State == ELBPR009State::Releasing || S.State == ELBPR009State::Stopping;
    State = !bControlPowerOn ? ELBPR009State::Isolated : (bWasMoving ? ELBPR009State::Ready : S.State);
    if (bWasMoving) { ActiveFault = ELBPR009Fault::None; bAlarmAcknowledged = false; bRestartRequiredAfterLoad = true; }
    PhaseElapsedSeconds = 0.0f; bControlledStopRequested = false;
    return true;
}

#undef LOCTEXT_NAMESPACE
