#include "LBPR008Station.h"

#include "Components/SceneComponent.h"
#include "Components/TextRenderComponent.h"
#include "Engine/TextRenderActor.h"
#include "EngineUtils.h"

#define LOCTEXT_NAMESPACE "CairnwellPR008"

ALBPR008Station::ALBPR008Station()
{
    PrimaryActorTick.bCanEverTick = true;
    StationRoot = CreateDefaultSubobject<USceneComponent>(TEXT("PR008_StationRoot"));
    SetRootComponent(StationRoot);
    FeedRollLowerMover = CreateDefaultSubobject<USceneComponent>(TEXT("PR008_FeedRollLowerMover"));
    FeedRollLowerMover->SetupAttachment(StationRoot);
    FeedRollUpperMover = CreateDefaultSubobject<USceneComponent>(TEXT("PR008_FeedRollUpperMover"));
    FeedRollUpperMover->SetupAttachment(StationRoot);
    LoopRollMover = CreateDefaultSubobject<USceneComponent>(TEXT("PR008_LoopRollMover"));
    LoopRollMover->SetupAttachment(StationRoot);
    EdgeGuideOperatorMover = CreateDefaultSubobject<USceneComponent>(TEXT("PR008_EdgeGuideOperatorMover"));
    EdgeGuideOperatorMover->SetupAttachment(StationRoot);
    EdgeGuideDriveMover = CreateDefaultSubobject<USceneComponent>(TEXT("PR008_EdgeGuideDriveMover"));
    EdgeGuideDriveMover->SetupAttachment(StationRoot);
    TelescopeStage1Mover = CreateDefaultSubobject<USceneComponent>(TEXT("PR008_TelescopeStage1Mover"));
    TelescopeStage1Mover->SetupAttachment(StationRoot);
    TelescopeStage2Mover = CreateDefaultSubobject<USceneComponent>(TEXT("PR008_TelescopeStage2Mover"));
    TelescopeStage2Mover->SetupAttachment(StationRoot);
    TelescopeStage3Mover = CreateDefaultSubobject<USceneComponent>(TEXT("PR008_TelescopeStage3Mover"));
    TelescopeStage3Mover->SetupAttachment(StationRoot);
    PrePunchMover = CreateDefaultSubobject<USceneComponent>(TEXT("PR008_PrePunchMover"));
    PrePunchMover->SetupAttachment(StationRoot);
    ScrapFlapMover = CreateDefaultSubobject<USceneComponent>(TEXT("PR008_ScrapFlapMover"));
    ScrapFlapMover->SetupAttachment(StationRoot);
    ServiceDoorOperatorMover = CreateDefaultSubobject<USceneComponent>(TEXT("PR008_ServiceDoorOperatorMover"));
    ServiceDoorOperatorMover->SetupAttachment(StationRoot);
    ServiceDoorDriveMover = CreateDefaultSubobject<USceneComponent>(TEXT("PR008_ServiceDoorDriveMover"));
    ServiceDoorDriveMover->SetupAttachment(StationRoot);
    GuillotineMover = CreateDefaultSubobject<USceneComponent>(TEXT("PR008_GuillotineMover"));
    GuillotineMover->SetupAttachment(StationRoot);
    OutfeedRollMover = CreateDefaultSubobject<USceneComponent>(TEXT("PR008_OutfeedRollMover"));
    OutfeedRollMover->SetupAttachment(StationRoot);
}

void ALBPR008Station::BeginPlay()
{
    Super::BeginPlay();
    EdgeGuideOperatorRestLocation = EdgeGuideOperatorMover->GetRelativeLocation();
    EdgeGuideDriveRestLocation = EdgeGuideDriveMover->GetRelativeLocation();
    TelescopeStage1RestLocation = TelescopeStage1Mover->GetRelativeLocation();
    TelescopeStage2RestLocation = TelescopeStage2Mover->GetRelativeLocation();
    TelescopeStage3RestLocation = TelescopeStage3Mover->GetRelativeLocation();
    PrePunchRestLocation = PrePunchMover->GetRelativeLocation();
    GuillotineRestLocation = GuillotineMover->GetRelativeLocation();
    FeedRollLowerRestRotation = FeedRollLowerMover->GetRelativeRotation();
    FeedRollUpperRestRotation = FeedRollUpperMover->GetRelativeRotation();
    LoopRollRestRotation = LoopRollMover->GetRelativeRotation();
    OutfeedRollRestRotation = OutfeedRollMover->GetRelativeRotation();
    ScrapFlapRestRotation = ScrapFlapMover->GetRelativeRotation();
    ServiceDoorOperatorRestRotation = ServiceDoorOperatorMover->GetRelativeRotation();
    ServiceDoorDriveRestRotation = ServiceDoorDriveMover->GetRelativeRotation();
    BindMapPresentation();
    ApplyMachinePose();
    UpdateHMITextPresentation();
}

void ALBPR008Station::Tick(float DeltaSeconds)
{
    Super::Tick(DeltaSeconds);
    PhaseElapsedSeconds += DeltaSeconds;
    if (State == ELBPR008State::Threading && PhaseElapsedSeconds >= ThreadingDurationSeconds)
    {
        SetState(ELBPR008State::Running);
    }
    else if (State == ELBPR008State::Stopping && PhaseElapsedSeconds >= StoppingDurationSeconds)
    {
        SetState(ELBPR008State::Ready);
    }

    if (State == ELBPR008State::Threading || State == ELBPR008State::Running)
    {
        EvaluateRuntimePermissives();
    }
    if (State == ELBPR008State::Running)
    {
        const float TravelThisTick = TargetLineSpeedMetresPerMinute * DeltaSeconds / 60.0f;
        StripTravelMetres += TravelThisTick;
        CycleTravelMetres += TravelThisTick;
        RunningHours += DeltaSeconds / 3600.0f;
        const float Pitch = GetBlankPitchMetres();
        while (CycleTravelMetres >= Pitch)
        {
            if (PendingBlankIds.Num() >= MaximumPendingBlanks)
            {
                RaiseFault(ELBPR008Fault::BlankOutfeedBlocked);
                break;
            }
            CycleTravelMetres -= Pitch;
            ++BlanksProduced;
            PendingBlankIds.Add(FName(*FString::Printf(TEXT("PR008-BLANK-%06d"), NextBlankSerial++)));
            ScrapBinFillPercent = FMath::Min(100.0f, ScrapBinFillPercent + 0.06f);
        }
        MotionAngleDegrees = FMath::Fmod(MotionAngleDegrees + DeltaSeconds * 620.0f, 360.0f);
        const float Cycle = GetCycleProgress();
        if (Cycle < 0.18f) RuntimePhase = ELBPR008RuntimePhase::Feeding;
        else if (Cycle < 0.44f) RuntimePhase = ELBPR008RuntimePhase::PrePunch;
        else if (Cycle < 0.72f) RuntimePhase = ELBPR008RuntimePhase::Cutting;
        else RuntimePhase = ELBPR008RuntimePhase::Discharging;
    }
    else if (State == ELBPR008State::Threading)
    {
        MotionAngleDegrees = FMath::Fmod(MotionAngleDegrees + DeltaSeconds * 180.0f, 360.0f);
        RuntimePhase = ELBPR008RuntimePhase::LoopControl;
    }
    else
    {
        RuntimePhase = ELBPR008RuntimePhase::StripWait;
    }
    ApplyMachinePose();
    UpdateHMITextPresentation();
}

void ALBPR008Station::SetState(ELBPR008State NewState)
{
    if (State == NewState) return;
    const ELBPR008State Previous = State;
    State = NewState;
    PhaseElapsedSeconds = 0.0f;
    OnStateChanged.Broadcast(Previous, NewState);
}

void ALBPR008Station::SetControlPower(bool bEnabled)
{
    if (bEnabled && bIsolationRequested) return;
    bControlPowerOn = bEnabled;
    if (!bEnabled)
    {
        SetState(ELBPR008State::Isolated);
    }
    else if (State == ELBPR008State::Isolated)
    {
        SetState(ActiveFault == ELBPR008Fault::None ? ELBPR008State::Ready : ELBPR008State::Fault);
    }
}

void ALBPR008Station::SetGuardsClosed(bool bClosed)
{
    bGuardsClosed = bClosed;
    if (!bClosed && (State == ELBPR008State::Threading || State == ELBPR008State::Running)) RaiseFault(ELBPR008Fault::GuardOpen);
}

void ALBPR008Station::SetStripAvailable(bool bAvailable)
{
    bStripAvailable = bAvailable;
    if (!bAvailable && (State == ELBPR008State::Threading || State == ELBPR008State::Running)) RaiseFault(ELBPR008Fault::StripUnavailable);
}

void ALBPR008Station::SetFeedServoHealthy(bool bHealthy)
{
    bFeedServoHealthy = bHealthy;
    if (!bHealthy && (State == ELBPR008State::Threading || State == ELBPR008State::Running)) RaiseFault(ELBPR008Fault::FeedServoFault);
}

void ALBPR008Station::SetHydraulicPressure(float PressureBar)
{
    HydraulicPressureBar = FMath::Clamp(PressureBar, 0.0f, 350.0f);
    if (HydraulicPressureBar < MinimumHydraulicPressureBar && (State == ELBPR008State::Threading || State == ELBPR008State::Running)) RaiseFault(ELBPR008Fault::PressHydraulicLow);
}

void ALBPR008Station::SetScrapBinFill(float FillPercent)
{
    ScrapBinFillPercent = FMath::Clamp(FillPercent, 0.0f, 100.0f);
    if (ScrapBinFillPercent >= MaximumScrapBinFillPercent && State == ELBPR008State::Running) RaiseFault(ELBPR008Fault::ScrapBinFull);
}

void ALBPR008Station::SetBlankOutfeedClear(bool bClear)
{
    bBlankOutfeedClear = bClear;
    if (!bClear && State == ELBPR008State::Running) RaiseFault(ELBPR008Fault::BlankOutfeedBlocked);
}

void ALBPR008Station::SetStripLoopPercent(float LoopPercent)
{
    StripLoopPercent = FMath::Clamp(LoopPercent, 0.0f, 100.0f);
    if ((StripLoopPercent < MinimumStripLoopPercent || StripLoopPercent > MaximumStripLoopPercent)
        && (State == ELBPR008State::Threading || State == ELBPR008State::Running))
    {
        RaiseFault(ELBPR008Fault::StripLoopOutOfRange);
    }
}

void ALBPR008Station::SetEdgeTrackingDeviation(float DeviationMm)
{
    EdgeTrackingDeviationMm = FMath::Clamp(DeviationMm, -300.0f, 300.0f);
    if (FMath::Abs(EdgeTrackingDeviationMm) > MaximumEdgeTrackingDeviationMm
        && (State == ELBPR008State::Threading || State == ELBPR008State::Running))
    {
        RaiseFault(ELBPR008Fault::EdgeTrackingLimit);
    }
}

void ALBPR008Station::SetFeedPositionError(float ErrorMm)
{
    FeedPositionErrorMm = FMath::Clamp(ErrorMm, -100.0f, 100.0f);
    if (FMath::Abs(FeedPositionErrorMm) > MaximumFeedPositionErrorMm
        && (State == ELBPR008State::Threading || State == ELBPR008State::Running))
    {
        RaiseFault(ELBPR008Fault::FeedPositionError);
    }
}

void ALBPR008Station::SetMeasuredCutLength(float LengthMm)
{
    MeasuredCutLengthMm = FMath::Max(0.0f, LengthMm);
    if (FMath::Abs(MeasuredCutLengthMm - TargetBlankLengthMm) > MaximumCutLengthErrorMm
        && State == ELBPR008State::Running)
    {
        RaiseFault(ELBPR008Fault::IncorrectCutLength);
    }
}

void ALBPR008Station::SetPrePunchToolHealthy(bool bHealthy)
{
    bPrePunchToolHealthy = bHealthy;
    if (!bHealthy && (State == ELBPR008State::Threading || State == ELBPR008State::Running))
    {
        RaiseFault(ELBPR008Fault::PrePunchToolFault);
    }
}

void ALBPR008Station::SetPressShearLoad(float LoadPercent)
{
    PressShearLoadPercent = FMath::Clamp(LoadPercent, 0.0f, 200.0f);
    if (PressShearLoadPercent > MaximumPressShearLoadPercent
        && (State == ELBPR008State::Threading || State == ELBPR008State::Running))
    {
        RaiseFault(ELBPR008Fault::PressShearOverload);
    }
}

void ALBPR008Station::SetSlugChuteFill(float FillPercent)
{
    SlugChuteFillPercent = FMath::Clamp(FillPercent, 0.0f, 100.0f);
    if (SlugChuteFillPercent >= MaximumSlugChuteFillPercent && State == ELBPR008State::Running)
    {
        RaiseFault(ELBPR008Fault::SlugChuteFull);
    }
}

void ALBPR008Station::SetSafetyCircuitHealthy(bool bHealthy)
{
    bSafetyCircuitHealthy = bHealthy;
    if (!bHealthy && (State == ELBPR008State::Threading || State == ELBPR008State::Running))
    {
        RaiseFault(ELBPR008Fault::EmergencyStopActive);
    }
}

void ALBPR008Station::SetEmergencyStopActive(bool bActive)
{
    bEmergencyStopActive = bActive;
    bAlarmAcknowledged = false;
    if (bActive)
    {
        bSafetyCircuitHealthy = false;
        RaiseFault(ELBPR008Fault::EmergencyStopActive);
    }
}

bool ALBPR008Station::AcknowledgeAlarm(FName CommandSource)
{
    if (CommandSource.IsNone() || ActiveFault == ELBPR008Fault::None) return false;
    LastCommandSource = CommandSource;
    bAlarmAcknowledged = true;
    return true;
}

bool ALBPR008Station::RequestIsolation(FName CommandSource)
{
    if (CommandSource.IsNone()) return false;
    LastCommandSource = CommandSource;
    RequestControlledStop();
    bIsolationRequested = true;
    bZeroEnergyProved = false;
    LastSafetyEvidenceId = NAME_None;
    SetControlPower(false);
    return true;
}

bool ALBPR008Station::ConfirmZeroEnergyIsolation(
    bool bZeroMotionVerified, bool bHydraulicPressureReleased, FName EvidenceId)
{
    if (!bIsolationRequested || bControlPowerOn || State != ELBPR008State::Isolated
        || !bZeroMotionVerified || !bHydraulicPressureReleased || EvidenceId.IsNone())
    {
        return false;
    }
    bZeroEnergyProved = true;
    LastSafetyEvidenceId = EvidenceId;
    return true;
}

bool ALBPR008Station::ReleaseIsolation(FName CommandSource, bool bGuardZoneClear)
{
    if (CommandSource.IsNone() || !bIsolationRequested || !bZeroEnergyProved || !bGuardZoneClear
        || !bGuardsClosed || bEmergencyStopActive || !bSafetyCircuitHealthy)
    {
        return false;
    }
    LastCommandSource = CommandSource;
    bIsolationRequested = false;
    bZeroEnergyProved = false;
    SetControlPower(true);
    return true;
}

bool ALBPR008Station::ExecuteRemoteCommand(
    ELBPR008Command Command, FName CommandSource, FName AuthorityId)
{
    if (!bRemoteControlEnabled || CommandSource.IsNone() || AuthorityId != RemoteAuthorityId) return false;
    LastCommandSource = CommandSource;
    switch (Command)
    {
    case ELBPR008Command::PowerOn: SetControlPower(true); return bControlPowerOn;
    case ELBPR008Command::PowerOff: SetControlPower(false); return !bControlPowerOn;
    case ELBPR008Command::Start: return StartLine();
    case ELBPR008Command::ControlledStop: RequestControlledStop(); return true;
    case ELBPR008Command::AcknowledgeAlarm: return AcknowledgeAlarm(CommandSource);
    case ELBPR008Command::Reset: return ResetFault();
    case ELBPR008Command::RequestIsolation: return RequestIsolation(CommandSource);
    case ELBPR008Command::ReleaseIsolation: return ReleaseIsolation(CommandSource, true);
    default: return false;
    }
}

void ALBPR008Station::SetBlankRecipe(float BlankLengthMm, float LineSpeedMetresPerMinute)
{
    if (State == ELBPR008State::Running || State == ELBPR008State::Threading) return;
    TargetBlankLengthMm = FMath::Clamp(BlankLengthMm, 500.0f, 4000.0f);
    TargetLineSpeedMetresPerMinute = FMath::Max(0.0f, LineSpeedMetresPerMinute);
    MeasuredCutLengthMm = TargetBlankLengthMm;
    CycleTravelMetres = 0.0f;
}

bool ALBPR008Station::CanStart(TArray<FText>& BlockingReasons) const
{
    BlockingReasons.Reset();
    if (!bControlPowerOn) BlockingReasons.Add(LOCTEXT("PowerOff", "Control power is off"));
    if (State != ELBPR008State::Ready) BlockingReasons.Add(LOCTEXT("NotReady", "Station is not ready"));
    if (bIsolationRequested) BlockingReasons.Add(LOCTEXT("IsolationActive", "Maintenance isolation is active"));
    if (bEmergencyStopActive) BlockingReasons.Add(LOCTEXT("EmergencyStop", "Emergency stop is active"));
    if (!bSafetyCircuitHealthy) BlockingReasons.Add(LOCTEXT("SafetyCircuit", "Safety circuit is not reset"));
    if (!bGuardsClosed) BlockingReasons.Add(LOCTEXT("GuardsOpen", "Guard or service door is open"));
    if (!bStripAvailable) BlockingReasons.Add(LOCTEXT("NoStrip", "Incoming strip is unavailable"));
    if (StripLoopPercent < MinimumStripLoopPercent || StripLoopPercent > MaximumStripLoopPercent)
        BlockingReasons.Add(LOCTEXT("LoopRange", "Strip loop is outside its safe range"));
    if (FMath::Abs(EdgeTrackingDeviationMm) > MaximumEdgeTrackingDeviationMm)
        BlockingReasons.Add(LOCTEXT("EdgeLimit", "Edge tracking is outside its correction range"));
    if (FMath::Abs(FeedPositionErrorMm) > MaximumFeedPositionErrorMm)
        BlockingReasons.Add(LOCTEXT("FeedPosition", "Feed position error exceeds tolerance"));
    if (!bFeedServoHealthy) BlockingReasons.Add(LOCTEXT("ServoFault", "Feed servo is unavailable"));
    if (!bPrePunchToolHealthy) BlockingReasons.Add(LOCTEXT("PrePunchTool", "Pre-punch tool is unavailable"));
    if (PressShearLoadPercent > MaximumPressShearLoadPercent)
        BlockingReasons.Add(LOCTEXT("ShearOverload", "Press or shear overload is active"));
    if (HydraulicPressureBar < MinimumHydraulicPressureBar) BlockingReasons.Add(LOCTEXT("HydraulicLow", "Press hydraulic pressure is low"));
    if (SlugChuteFillPercent >= MaximumSlugChuteFillPercent)
        BlockingReasons.Add(LOCTEXT("SlugFull", "Slug chute requires collection"));
    if (ScrapBinFillPercent >= MaximumScrapBinFillPercent) BlockingReasons.Add(LOCTEXT("ScrapFull", "Scrap bin requires collection"));
    if (!bBlankOutfeedClear) BlockingReasons.Add(LOCTEXT("OutfeedBlocked", "Blank outfeed is blocked"));
    if (PendingBlankIds.Num() >= MaximumPendingBlanks)
        BlockingReasons.Add(LOCTEXT("BlankBufferFull", "The PR-008 blank discharge buffer is full"));
    return BlockingReasons.IsEmpty();
}

bool ALBPR008Station::StartLine()
{
    TArray<FText> Reasons;
    if (!CanStart(Reasons)) return false;
    ActiveFault = ELBPR008Fault::None;
    bAlarmAcknowledged = false;
    bRestartRequiredAfterLoad = false;
    SetState(ELBPR008State::Threading);
    return true;
}

void ALBPR008Station::RequestControlledStop()
{
    if (State == ELBPR008State::Threading || State == ELBPR008State::Running) SetState(ELBPR008State::Stopping);
}

void ALBPR008Station::RaiseFault(ELBPR008Fault Fault)
{
    if (Fault == ELBPR008Fault::None || State == ELBPR008State::Fault) return;
    ActiveFault = Fault;
    if (bControlPowerOn) SetState(ELBPR008State::Fault);
    OnFaultRaised.Broadcast(Fault);
}

void ALBPR008Station::EvaluateRuntimePermissives()
{
    if (bEmergencyStopActive || !bSafetyCircuitHealthy) RaiseFault(ELBPR008Fault::EmergencyStopActive);
    else if (!bGuardsClosed) RaiseFault(ELBPR008Fault::GuardOpen);
    else if (!bStripAvailable) RaiseFault(ELBPR008Fault::StripUnavailable);
    else if (StripLoopPercent < MinimumStripLoopPercent || StripLoopPercent > MaximumStripLoopPercent) RaiseFault(ELBPR008Fault::StripLoopOutOfRange);
    else if (FMath::Abs(EdgeTrackingDeviationMm) > MaximumEdgeTrackingDeviationMm) RaiseFault(ELBPR008Fault::EdgeTrackingLimit);
    else if (FMath::Abs(FeedPositionErrorMm) > MaximumFeedPositionErrorMm) RaiseFault(ELBPR008Fault::FeedPositionError);
    else if (!bFeedServoHealthy) RaiseFault(ELBPR008Fault::FeedServoFault);
    else if (!bPrePunchToolHealthy) RaiseFault(ELBPR008Fault::PrePunchToolFault);
    else if (PressShearLoadPercent > MaximumPressShearLoadPercent) RaiseFault(ELBPR008Fault::PressShearOverload);
    else if (HydraulicPressureBar < MinimumHydraulicPressureBar) RaiseFault(ELBPR008Fault::PressHydraulicLow);
    else if (SlugChuteFillPercent >= MaximumSlugChuteFillPercent) RaiseFault(ELBPR008Fault::SlugChuteFull);
    else if (ScrapBinFillPercent >= MaximumScrapBinFillPercent) RaiseFault(ELBPR008Fault::ScrapBinFull);
    else if (!bBlankOutfeedClear || PendingBlankIds.Num() >= MaximumPendingBlanks) RaiseFault(ELBPR008Fault::BlankOutfeedBlocked);
}

bool ALBPR008Station::ResetFault()
{
    if (State != ELBPR008State::Fault || ActiveFault == ELBPR008Fault::None || !bControlPowerOn
        || !bAlarmAcknowledged || bEmergencyStopActive || !bSafetyCircuitHealthy || bIsolationRequested)
    {
        return false;
    }
    const ELBPR008State PreviousState = State;
    State = ELBPR008State::Ready;
    TArray<FText> Reasons;
    const bool bHealthy = CanStart(Reasons);
    State = PreviousState;
    if (!bHealthy) return false;
    ActiveFault = ELBPR008Fault::None;
    bAlarmAcknowledged = false;
    SetState(ELBPR008State::Ready);
    return true;
}

bool ALBPR008Station::CanReleaseBlank(TArray<FText>& BlockingReasons) const
{
    BlockingReasons.Reset();
    if (PendingBlankIds.IsEmpty()) BlockingReasons.Add(LOCTEXT("NoPendingBlank", "No identified blank is waiting at PR-008 outfeed"));
    if (!PendingHandoffTransactionId.IsNone()) BlockingReasons.Add(LOCTEXT("BlankHandoffActive", "Another blank handoff is already active"));
    if (!bBlankOutfeedClear) BlockingReasons.Add(LOCTEXT("BlankRouteBlocked", "The PR-008 blank outfeed route is blocked"));
    if (!bGuardsClosed || bEmergencyStopActive || !bSafetyCircuitHealthy || bIsolationRequested)
        BlockingReasons.Add(LOCTEXT("BlankHandoffSafety", "PR-008 safety or isolation state prevents blank handoff"));
    return BlockingReasons.IsEmpty();
}

bool ALBPR008Station::RequestBlankHandoff(FName TransactionId, FName& BlankId)
{
    BlankId = NAME_None;
    if (TransactionId.IsNone()) return false;
    TArray<FText> BlockingReasons;
    if (!CanReleaseBlank(BlockingReasons)) return false;
    PendingHandoffTransactionId = TransactionId;
    PendingHandoffBlankId = PendingBlankIds[0];
    BlankId = PendingHandoffBlankId;
    return true;
}

bool ALBPR008Station::ConfirmBlankHandoff(FName TransactionId)
{
    if (TransactionId.IsNone() || TransactionId != PendingHandoffTransactionId
        || PendingHandoffBlankId.IsNone() || PendingBlankIds.IsEmpty()
        || PendingBlankIds[0] != PendingHandoffBlankId)
    {
        return false;
    }
    PendingBlankIds.RemoveAt(0);
    PendingHandoffTransactionId = NAME_None;
    PendingHandoffBlankId = NAME_None;
    return true;
}

void ALBPR008Station::CancelBlankHandoff(FName TransactionId)
{
    if (!TransactionId.IsNone() && TransactionId == PendingHandoffTransactionId)
    {
        PendingHandoffTransactionId = NAME_None;
        PendingHandoffBlankId = NAME_None;
    }
}

float ALBPR008Station::GetBlankPitchMetres() const
{
    return FMath::Max(0.6f, TargetBlankLengthMm / 1000.0f + CutAllowanceMetres);
}

float ALBPR008Station::GetCycleProgress() const
{
    return FMath::Clamp(CycleTravelMetres / GetBlankPitchMetres(), 0.0f, 1.0f);
}

FLBPR008HMIStatus ALBPR008Station::GetHMIStatus() const
{
    FLBPR008HMIStatus Status;
    Status.StationId = StationId;
    Status.State = State;
    Status.ActiveFault = ActiveFault;
    Status.RuntimePhase = RuntimePhase;
    Status.StripTravelMetres = StripTravelMetres;
    Status.BlanksProduced = BlanksProduced;
    Status.PendingBlankCount = PendingBlankIds.Num();
    Status.OldestPendingBlankId = PendingBlankIds.IsEmpty() ? NAME_None : PendingBlankIds[0];
    Status.TargetBlankLengthMm = TargetBlankLengthMm;
    Status.LineSpeedMetresPerMinute = State == ELBPR008State::Running ? TargetLineSpeedMetresPerMinute : 0.0f;
    Status.HydraulicPressureBar = HydraulicPressureBar;
    Status.ScrapBinFillPercent = ScrapBinFillPercent;
    Status.StripLoopPercent = StripLoopPercent;
    Status.EdgeTrackingDeviationMm = EdgeTrackingDeviationMm;
    Status.FeedPositionErrorMm = FeedPositionErrorMm;
    Status.MeasuredCutLengthMm = MeasuredCutLengthMm;
    Status.PressShearLoadPercent = PressShearLoadPercent;
    Status.SlugChuteFillPercent = SlugChuteFillPercent;
    Status.CycleProgress = GetCycleProgress();
    Status.bControlPowerOn = bControlPowerOn;
    Status.bGuardsClosed = bGuardsClosed;
    Status.bStripAvailable = bStripAvailable;
    Status.bFeedServoHealthy = bFeedServoHealthy;
    Status.bBlankOutfeedClear = bBlankOutfeedClear;
    Status.bPrePunchToolHealthy = bPrePunchToolHealthy;
    Status.bSafetyCircuitHealthy = bSafetyCircuitHealthy;
    Status.bEmergencyStopActive = bEmergencyStopActive;
    Status.bAlarmAcknowledged = bAlarmAcknowledged;
    Status.bIsolationRequested = bIsolationRequested;
    Status.bZeroEnergyProved = bZeroEnergyProved;
    Status.bRestartRequiredAfterLoad = bRestartRequiredAfterLoad;
    Status.LastCommandSource = LastCommandSource;
    Status.LastSafetyEvidenceId = LastSafetyEvidenceId;
    Status.bCanStart = CanStart(Status.BlockingReasons);
    return Status;
}

FLBPR008SaveState ALBPR008Station::CaptureSaveState() const
{
    FLBPR008SaveState Saved;
    Saved.StationId = StationId;
    Saved.State = State;
    Saved.ActiveFault = ActiveFault;
    Saved.RuntimePhase = RuntimePhase;
    Saved.StripTravelMetres = StripTravelMetres;
    Saved.BlanksProduced = BlanksProduced;
    Saved.NextBlankSerial = NextBlankSerial;
    Saved.PendingBlankIds = PendingBlankIds;
    Saved.PendingHandoffTransactionId = PendingHandoffTransactionId;
    Saved.PendingHandoffBlankId = PendingHandoffBlankId;
    Saved.RunningHours = RunningHours;
    Saved.TargetBlankLengthMm = TargetBlankLengthMm;
    Saved.TargetLineSpeedMetresPerMinute = TargetLineSpeedMetresPerMinute;
    Saved.HydraulicPressureBar = HydraulicPressureBar;
    Saved.ScrapBinFillPercent = ScrapBinFillPercent;
    Saved.StripLoopPercent = StripLoopPercent;
    Saved.EdgeTrackingDeviationMm = EdgeTrackingDeviationMm;
    Saved.FeedPositionErrorMm = FeedPositionErrorMm;
    Saved.MeasuredCutLengthMm = MeasuredCutLengthMm;
    Saved.PressShearLoadPercent = PressShearLoadPercent;
    Saved.SlugChuteFillPercent = SlugChuteFillPercent;
    Saved.bControlPowerOn = bControlPowerOn;
    Saved.bGuardsClosed = bGuardsClosed;
    Saved.bStripAvailable = bStripAvailable;
    Saved.bFeedServoHealthy = bFeedServoHealthy;
    Saved.bBlankOutfeedClear = bBlankOutfeedClear;
    Saved.bPrePunchToolHealthy = bPrePunchToolHealthy;
    Saved.bSafetyCircuitHealthy = bSafetyCircuitHealthy;
    Saved.bEmergencyStopActive = bEmergencyStopActive;
    Saved.bAlarmAcknowledged = bAlarmAcknowledged;
    Saved.bIsolationRequested = bIsolationRequested;
    Saved.bZeroEnergyProved = bZeroEnergyProved;
    Saved.bRestartRequiredAfterLoad = bRestartRequiredAfterLoad;
    Saved.LastCommandSource = LastCommandSource;
    Saved.LastSafetyEvidenceId = LastSafetyEvidenceId;
    return Saved;
}

bool ALBPR008Station::RestoreSaveState(const FLBPR008SaveState& SavedState)
{
    if ((SavedState.Version != 2 && SavedState.Version != 3) || SavedState.StationId != StationId) return false;
    ActiveFault = SavedState.ActiveFault;
    RuntimePhase = SavedState.RuntimePhase;
    StripTravelMetres = FMath::Max(0.0f, SavedState.StripTravelMetres);
    BlanksProduced = FMath::Max(0, SavedState.BlanksProduced);
    NextBlankSerial = SavedState.Version >= 3 ? FMath::Max(1, SavedState.NextBlankSerial) : BlanksProduced + 1;
    PendingBlankIds = SavedState.Version >= 3 ? SavedState.PendingBlankIds : TArray<FName>();
    if (PendingBlankIds.Num() > MaximumPendingBlanks) PendingBlankIds.SetNum(MaximumPendingBlanks);
    PendingBlankIds.RemoveAll([](FName BlankId) { return BlankId.IsNone(); });
    PendingHandoffTransactionId = SavedState.Version >= 3 ? SavedState.PendingHandoffTransactionId : NAME_None;
    PendingHandoffBlankId = SavedState.Version >= 3 ? SavedState.PendingHandoffBlankId : NAME_None;
    if (PendingHandoffTransactionId.IsNone() || PendingHandoffBlankId.IsNone()
        || PendingBlankIds.IsEmpty() || PendingBlankIds[0] != PendingHandoffBlankId)
    {
        PendingHandoffTransactionId = NAME_None;
        PendingHandoffBlankId = NAME_None;
    }
    RunningHours = FMath::Max(0.0f, SavedState.RunningHours);
    TargetBlankLengthMm = FMath::Clamp(SavedState.TargetBlankLengthMm, 500.0f, 4000.0f);
    TargetLineSpeedMetresPerMinute = FMath::Max(0.0f, SavedState.TargetLineSpeedMetresPerMinute);
    HydraulicPressureBar = FMath::Clamp(SavedState.HydraulicPressureBar, 0.0f, 350.0f);
    ScrapBinFillPercent = FMath::Clamp(SavedState.ScrapBinFillPercent, 0.0f, 100.0f);
    StripLoopPercent = FMath::Clamp(SavedState.StripLoopPercent, 0.0f, 100.0f);
    EdgeTrackingDeviationMm = FMath::Clamp(SavedState.EdgeTrackingDeviationMm, -300.0f, 300.0f);
    FeedPositionErrorMm = FMath::Clamp(SavedState.FeedPositionErrorMm, -100.0f, 100.0f);
    MeasuredCutLengthMm = FMath::Max(0.0f, SavedState.MeasuredCutLengthMm);
    PressShearLoadPercent = FMath::Clamp(SavedState.PressShearLoadPercent, 0.0f, 200.0f);
    SlugChuteFillPercent = FMath::Clamp(SavedState.SlugChuteFillPercent, 0.0f, 100.0f);
    bControlPowerOn = SavedState.bControlPowerOn;
    bGuardsClosed = SavedState.bGuardsClosed;
    bStripAvailable = SavedState.bStripAvailable;
    bFeedServoHealthy = SavedState.bFeedServoHealthy;
    bBlankOutfeedClear = SavedState.bBlankOutfeedClear;
    bPrePunchToolHealthy = SavedState.bPrePunchToolHealthy;
    bSafetyCircuitHealthy = SavedState.bSafetyCircuitHealthy;
    bEmergencyStopActive = SavedState.bEmergencyStopActive;
    bAlarmAcknowledged = SavedState.bAlarmAcknowledged;
    bIsolationRequested = SavedState.bIsolationRequested;
    bZeroEnergyProved = SavedState.bZeroEnergyProved;
    bRestartRequiredAfterLoad = SavedState.bRestartRequiredAfterLoad;
    LastCommandSource = SavedState.LastCommandSource;
    LastSafetyEvidenceId = SavedState.LastSafetyEvidenceId;
    const bool bWasMoving = SavedState.State == ELBPR008State::Threading || SavedState.State == ELBPR008State::Running || SavedState.State == ELBPR008State::Stopping;
    State = !bControlPowerOn ? ELBPR008State::Isolated : (bWasMoving ? ELBPR008State::Ready : SavedState.State);
    if (bWasMoving)
    {
        ActiveFault = ELBPR008Fault::None;
        RuntimePhase = ELBPR008RuntimePhase::StripWait;
        bAlarmAcknowledged = false;
        bRestartRequiredAfterLoad = true;
    }
    PhaseElapsedSeconds = 0.0f;
    CycleTravelMetres = 0.0f;
    MotionAngleDegrees = 0.0f;
    if (HasActorBegunPlay()) ApplyMachinePose();
    return true;
}

void ALBPR008Station::ApplyMachinePose()
{
    const float Cycle = GetCycleProgress();
    const float PrePunchStroke = FMath::Pow(FMath::Sin(PI * FMath::Clamp((Cycle - 0.12f) / 0.45f, 0.0f, 1.0f)), 8.0f);
    const float GuillotineStroke = FMath::Pow(FMath::Sin(PI * FMath::Clamp((Cycle - 0.48f) / 0.40f, 0.0f, 1.0f)), 8.0f);
    const float GuideTravelCm = FMath::Clamp(EdgeTrackingDeviationMm, -150.0f, 150.0f) / 10.0f;
    const float SupportExtensionCm = State == ELBPR008State::Running
        ? 120.0f * FMath::Clamp(FMath::Sin(PI * Cycle), 0.0f, 1.0f)
        : 0.0f;
    const float ScrapFlapAngle = State == ELBPR008State::Running
        ? 70.0f * FMath::Pow(FMath::Sin(PI * FMath::Clamp((Cycle - 0.30f) / 0.30f, 0.0f, 1.0f)), 6.0f)
        : 0.0f;
    const float ServiceDoorAngle = bGuardsClosed ? 0.0f : 110.0f;

    // Unreal FRotator's Roll channel is rotation about local X.
    FeedRollLowerMover->SetRelativeRotation(FeedRollLowerRestRotation + FRotator(0.0f, 0.0f, MotionAngleDegrees));
    FeedRollUpperMover->SetRelativeRotation(FeedRollUpperRestRotation + FRotator(0.0f, 0.0f, -MotionAngleDegrees));
    LoopRollMover->SetRelativeRotation(LoopRollRestRotation + FRotator(0.0f, 0.0f, MotionAngleDegrees * 0.45f));
    OutfeedRollMover->SetRelativeRotation(OutfeedRollRestRotation + FRotator(0.0f, 0.0f, MotionAngleDegrees));
    EdgeGuideOperatorMover->SetRelativeLocation(EdgeGuideOperatorRestLocation + FVector(GuideTravelCm, 0.0f, 0.0f));
    EdgeGuideDriveMover->SetRelativeLocation(EdgeGuideDriveRestLocation + FVector(GuideTravelCm, 0.0f, 0.0f));
    TelescopeStage1Mover->SetRelativeLocation(TelescopeStage1RestLocation + FVector(0.0f, SupportExtensionCm / 3.0f, 0.0f));
    TelescopeStage2Mover->SetRelativeLocation(TelescopeStage2RestLocation + FVector(0.0f, SupportExtensionCm * 2.0f / 3.0f, 0.0f));
    TelescopeStage3Mover->SetRelativeLocation(TelescopeStage3RestLocation + FVector(0.0f, SupportExtensionCm, 0.0f));
    PrePunchMover->SetRelativeLocation(PrePunchRestLocation + FVector(0.0f, 0.0f, -22.0f * PrePunchStroke));
    GuillotineMover->SetRelativeLocation(GuillotineRestLocation + FVector(0.0f, 0.0f, -18.0f * GuillotineStroke));
    ScrapFlapMover->SetRelativeRotation(ScrapFlapRestRotation + FRotator(0.0f, 0.0f, ScrapFlapAngle));
    ServiceDoorOperatorMover->SetRelativeRotation(ServiceDoorOperatorRestRotation + FRotator(0.0f, ServiceDoorAngle, 0.0f));
    ServiceDoorDriveMover->SetRelativeRotation(ServiceDoorDriveRestRotation + FRotator(0.0f, -ServiceDoorAngle, 0.0f));

    const FQuat LocalXRoll(FVector::ForwardVector, FMath::DegreesToRadians(MotionAngleDegrees));
    for (int32 Index = 0; Index < LoopRollPresentations.Num(); ++Index)
    {
        if (LoopRollPresentations[Index].IsValid() && LoopRollPresentationRestRotations.IsValidIndex(Index))
        {
            LoopRollPresentations[Index]->SetActorRotation(
                LoopRollPresentationRestRotations[Index].Quaternion() * LocalXRoll);
        }
    }
    for (int32 Index = 0; Index < DischargeRollPresentations.Num(); ++Index)
    {
        if (DischargeRollPresentations[Index].IsValid() && DischargeRollPresentationRestRotations.IsValidIndex(Index))
        {
            DischargeRollPresentations[Index]->SetActorRotation(
                DischargeRollPresentationRestRotations[Index].Quaternion() * LocalXRoll);
        }
    }
}

void ALBPR008Station::BindMapPresentation()
{
    LoopRollPresentations.Reset();
    LoopRollPresentationRestRotations.Reset();
    DischargeRollPresentations.Reset();
    DischargeRollPresentationRestRotations.Reset();
    for (TActorIterator<AActor> It(GetWorld()); It; ++It)
    {
        AActor* Actor = *It;
        if (Actor->ActorHasTag(TEXT("LB.Presentation.PR008.LoopRoll")))
        {
            LoopRollPresentations.Add(Actor);
            LoopRollPresentationRestRotations.Add(Actor->GetActorRotation());
        }
        if (Actor->ActorHasTag(TEXT("LB.Presentation.PR008.DischargeRoll")))
        {
            DischargeRollPresentations.Add(Actor);
            DischargeRollPresentationRestRotations.Add(Actor->GetActorRotation());
        }
        ATextRenderActor* TextActor = Cast<ATextRenderActor>(Actor);
        if (TextActor && (TextActor->ActorHasTag(TEXT("LB.HMI.PR008.LiveState"))
            || (TextActor->GetActorNameOrLabel().Contains(TEXT("PR008")) && TextActor->GetActorNameOrLabel().Contains(TEXT("HMI_Text_State")))))
        {
            HMIStatePresentation = TextActor;
        }
    }
}

void ALBPR008Station::UpdateHMITextPresentation()
{
    if (!HMIStatePresentation.IsValid()) return;
    UTextRenderComponent* Text = HMIStatePresentation->GetTextRender();
    if (!Text) return;
    const UEnum* StateEnum = StaticEnum<ELBPR008State>();
    const UEnum* FaultEnum = StaticEnum<ELBPR008Fault>();
    const UEnum* PhaseEnum = StaticEnum<ELBPR008RuntimePhase>();
    const FString StateName = StateEnum ? StateEnum->GetNameStringByValue(static_cast<int64>(State)).ToUpper() : TEXT("UNKNOWN");
    const FString PhaseName = PhaseEnum ? PhaseEnum->GetNameStringByValue(static_cast<int64>(RuntimePhase)).ToUpper() : TEXT("UNKNOWN");
    if (ActiveFault != ELBPR008Fault::None)
    {
        const FString FaultName = FaultEnum ? FaultEnum->GetNameStringByValue(static_cast<int64>(ActiveFault)).ToUpper() : TEXT("FAULT");
        Text->SetText(FText::FromString(FString::Printf(TEXT("FAULT %s | %s"), *FaultName,
            bAlarmAcknowledged ? TEXT("ACKNOWLEDGED") : TEXT("ACK REQUIRED"))));
        Text->SetTextRenderColor(FColor(220, 45, 35));
    }
    else
    {
        Text->SetText(FText::FromString(FString::Printf(TEXT("%s / %s | BLANKS %d | %4.0f mm"),
            *StateName, *PhaseName, BlanksProduced, TargetBlankLengthMm)));
        Text->SetTextRenderColor(State == ELBPR008State::Running ? FColor(45, 220, 145) : FColor(225, 166, 0));
    }
}

#undef LOCTEXT_NAMESPACE
