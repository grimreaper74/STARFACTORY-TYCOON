#include "LBPR006Station.h"

#include "Components/SceneComponent.h"
#include "Components/TextRenderComponent.h"
#include "Engine/TextRenderActor.h"
#include "EngineUtils.h"

#define LOCTEXT_NAMESPACE "CairnwellPR006"

ALBPR006Station::ALBPR006Station()
{
    PrimaryActorTick.bCanEverTick = true;
    StationRoot = CreateDefaultSubobject<USceneComponent>(TEXT("PR006_StationRoot"));
    SetRootComponent(StationRoot);
    for (int32 Index = 0; Index < 9; ++Index)
    {
        USceneComponent* Mover = CreateDefaultSubobject<USceneComponent>(*FString::Printf(TEXT("PR006_LowerRollMover_%02d"), Index + 1));
        Mover->SetupAttachment(StationRoot);
        LowerRollMovers.Add(Mover);
    }
    for (int32 Index = 0; Index < 10; ++Index)
    {
        USceneComponent* Mover = CreateDefaultSubobject<USceneComponent>(*FString::Printf(TEXT("PR006_UpperRollMover_%02d"), Index + 1));
        Mover->SetupAttachment(StationRoot);
        UpperRollMovers.Add(Mover);
    }
    UpperCassetteMover = CreateDefaultSubobject<USceneComponent>(TEXT("PR006_UpperCassetteMover"));
    UpperCassetteMover->SetupAttachment(StationRoot);
    for (int32 Index = 0; Index < 4; ++Index)
    {
        USceneComponent* Mover = CreateDefaultSubobject<USceneComponent>(*FString::Printf(TEXT("PR006_GapCylinderMover_%02d"), Index + 1));
        Mover->SetupAttachment(StationRoot);
        GapCylinderMovers.Add(Mover);
    }
    for (int32 Index = 0; Index < 3; ++Index)
    {
        USceneComponent* Mover = CreateDefaultSubobject<USceneComponent>(*FString::Printf(TEXT("PR006_DriveMotorMover_%02d"), Index + 1));
        Mover->SetupAttachment(StationRoot);
        DriveMotorMovers.Add(Mover);
    }
}

void ALBPR006Station::BeginPlay()
{
    Super::BeginPlay();
    UpperCassetteRestLocation = UpperCassetteMover->GetRelativeLocation();
    GapCylinderRestLocations.Reset();
    for (USceneComponent* Mover : GapCylinderMovers) GapCylinderRestLocations.Add(Mover->GetRelativeLocation());
    BindMapPresentation();
    ApplyMachinePose();
    UpdateHMITextPresentation();
}

void ALBPR006Station::Tick(float DeltaSeconds)
{
    Super::Tick(DeltaSeconds);
    PhaseElapsedSeconds += DeltaSeconds;
    if (State == ELBPR006State::Calibrating)
    {
        const float Alpha = FMath::Clamp(PhaseElapsedSeconds / CalibrationDurationSeconds, 0.0f, 1.0f);
        ActualRollGapMm = FMath::Lerp(CalibrationStartGapMm, TargetRollGapMm, Alpha);
        MotorLoadPercent = FMath::Lerp(8.0f, 28.0f, Alpha);
        if (Alpha >= 1.0f) SetState(ELBPR006State::Running);
    }
    else if (State == ELBPR006State::Stopping && PhaseElapsedSeconds >= StoppingDurationSeconds)
    {
        MotorLoadPercent = 0.0f;
        SetState(ELBPR006State::Ready);
    }
    if (State == ELBPR006State::Calibrating || State == ELBPR006State::Running) EvaluateRuntimePermissives();
    if (State == ELBPR006State::Running)
    {
        const float TravelThisTick = TargetLineSpeedMetresPerMinute * DeltaSeconds / 60.0f;
        StripTravelMetres += TravelThisTick;
        RunningHours += DeltaSeconds / 3600.0f;
        MotorLoadPercent = FMath::Clamp(32.0f + TargetLineSpeedMetresPerMinute * 1.65f, 0.0f, 100.0f);
        MotionAngleDegrees = FMath::Fmod(MotionAngleDegrees + DeltaSeconds * 680.0f, 360.0f);
    }
    else if (State == ELBPR006State::Calibrating)
    {
        MotionAngleDegrees = FMath::Fmod(MotionAngleDegrees + DeltaSeconds * 120.0f, 360.0f);
    }
    ApplyMachinePose();
    UpdateHMITextPresentation();
}

void ALBPR006Station::SetState(ELBPR006State NewState)
{
    if (State == NewState) return;
    const ELBPR006State Previous = State;
    State = NewState;
    PhaseElapsedSeconds = 0.0f;
    OnStateChanged.Broadcast(Previous, NewState);
}

void ALBPR006Station::SetControlPower(bool bEnabled)
{
    bControlPowerOn = bEnabled;
    if (!bEnabled) { ActiveFault = ELBPR006Fault::None; MotorLoadPercent = 0.0f; SetState(ELBPR006State::Isolated); }
    else if (State == ELBPR006State::Isolated) SetState(ELBPR006State::Ready);
}

void ALBPR006Station::SetGuardsClosed(bool bClosed)
{
    bGuardsClosed = bClosed;
    if (!bClosed && (State == ELBPR006State::Calibrating || State == ELBPR006State::Running)) RaiseFault(ELBPR006Fault::GuardOpen);
}

void ALBPR006Station::SetStripAvailable(bool bAvailable)
{
    bStripAvailable = bAvailable;
    if (!bAvailable && (State == ELBPR006State::Calibrating || State == ELBPR006State::Running)) RaiseFault(ELBPR006Fault::StripUnavailable);
}

void ALBPR006Station::SetCassetteLocked(bool bLocked)
{
    bCassetteLocked = bLocked;
    if (!bLocked && (State == ELBPR006State::Calibrating || State == ELBPR006State::Running)) RaiseFault(ELBPR006Fault::CassetteUnlocked);
}

void ALBPR006Station::SetDrivesHealthy(bool bHealthy)
{
    bDrivesHealthy = bHealthy;
    if (!bHealthy && (State == ELBPR006State::Calibrating || State == ELBPR006State::Running)) RaiseFault(ELBPR006Fault::DriveFault);
}

void ALBPR006Station::SetActualRollGap(float GapMm)
{
    ActualRollGapMm = FMath::Clamp(GapMm, 0.1f, 10.0f);
    if (State == ELBPR006State::Running && FMath::Abs(ActualRollGapMm - TargetRollGapMm) > MaximumGapErrorMm) RaiseFault(ELBPR006Fault::RollGapOutOfTolerance);
}

void ALBPR006Station::SetMotorLoad(float LoadPercent)
{
    MotorLoadPercent = FMath::Clamp(LoadPercent, 0.0f, 150.0f);
    if (State == ELBPR006State::Running && MotorLoadPercent >= MaximumMotorLoadPercent) RaiseFault(ELBPR006Fault::MotorOverload);
}

void ALBPR006Station::SetLevellerRecipe(FName NewCassetteId, float StripThicknessMm, float RollGapMm, float LineSpeedMetresPerMinute)
{
    if (State == ELBPR006State::Running || State == ELBPR006State::Calibrating) return;
    CassetteId = NewCassetteId.IsNone() ? FName(TEXT("L-1500-A")) : NewCassetteId;
    TargetStripThicknessMm = FMath::Clamp(StripThicknessMm, 0.4f, 4.0f);
    TargetRollGapMm = FMath::Clamp(RollGapMm, 0.1f, 6.0f);
    TargetLineSpeedMetresPerMinute = FMath::Max(0.0f, LineSpeedMetresPerMinute);
}

bool ALBPR006Station::CanStart(TArray<FText>& BlockingReasons) const
{
    BlockingReasons.Reset();
    if (!bControlPowerOn) BlockingReasons.Add(LOCTEXT("PowerOff", "Control power is off"));
    if (State != ELBPR006State::Ready) BlockingReasons.Add(LOCTEXT("NotReady", "Station is not ready"));
    if (!bGuardsClosed) BlockingReasons.Add(LOCTEXT("GuardOpen", "Guard or cassette service door is open"));
    if (!bStripAvailable) BlockingReasons.Add(LOCTEXT("NoStrip", "Incoming strip is unavailable"));
    if (!bCassetteLocked) BlockingReasons.Add(LOCTEXT("CassetteUnlocked", "Leveller cassette is not locked"));
    if (!bDrivesHealthy) BlockingReasons.Add(LOCTEXT("DriveFault", "Leveller drive group is unavailable"));
    return BlockingReasons.IsEmpty();
}

bool ALBPR006Station::StartLine()
{
    TArray<FText> Reasons;
    if (!CanStart(Reasons)) return false;
    ActiveFault = ELBPR006Fault::None;
    CalibrationStartGapMm = ActualRollGapMm;
    SetState(ELBPR006State::Calibrating);
    return true;
}

void ALBPR006Station::RequestControlledStop()
{
    if (State == ELBPR006State::Calibrating || State == ELBPR006State::Running) SetState(ELBPR006State::Stopping);
}

void ALBPR006Station::RaiseFault(ELBPR006Fault Fault)
{
    if (Fault == ELBPR006Fault::None || State == ELBPR006State::Fault) return;
    ActiveFault = Fault;
    MotorLoadPercent = 0.0f;
    SetState(ELBPR006State::Fault);
    OnFaultRaised.Broadcast(Fault);
}

void ALBPR006Station::EvaluateRuntimePermissives()
{
    if (!bGuardsClosed) RaiseFault(ELBPR006Fault::GuardOpen);
    else if (!bStripAvailable) RaiseFault(ELBPR006Fault::StripUnavailable);
    else if (!bCassetteLocked) RaiseFault(ELBPR006Fault::CassetteUnlocked);
    else if (!bDrivesHealthy) RaiseFault(ELBPR006Fault::DriveFault);
    else if (State == ELBPR006State::Running && FMath::Abs(ActualRollGapMm - TargetRollGapMm) > MaximumGapErrorMm) RaiseFault(ELBPR006Fault::RollGapOutOfTolerance);
    else if (MotorLoadPercent >= MaximumMotorLoadPercent) RaiseFault(ELBPR006Fault::MotorOverload);
}

bool ALBPR006Station::ResetFault()
{
    if (State != ELBPR006State::Fault || ActiveFault == ELBPR006Fault::None || !bControlPowerOn) return false;
    const ELBPR006State Previous = State;
    State = ELBPR006State::Ready;
    TArray<FText> Reasons;
    const bool bHealthy = CanStart(Reasons);
    State = Previous;
    if (!bHealthy) return false;
    ActiveFault = ELBPR006Fault::None;
    SetState(ELBPR006State::Ready);
    return true;
}

FLBPR006HMIStatus ALBPR006Station::GetHMIStatus() const
{
    FLBPR006HMIStatus Status;
    Status.StationId = StationId; Status.State = State; Status.ActiveFault = ActiveFault; Status.CassetteId = CassetteId;
    Status.TargetStripThicknessMm = TargetStripThicknessMm; Status.TargetRollGapMm = TargetRollGapMm; Status.ActualRollGapMm = ActualRollGapMm;
    Status.StripTravelMetres = StripTravelMetres; Status.LineSpeedMetresPerMinute = State == ELBPR006State::Running ? TargetLineSpeedMetresPerMinute : 0.0f;
    Status.MotorLoadPercent = MotorLoadPercent;
    Status.CalibrationProgress = State == ELBPR006State::Calibrating ? FMath::Clamp(PhaseElapsedSeconds / CalibrationDurationSeconds, 0.0f, 1.0f) : (State == ELBPR006State::Running ? 1.0f : 0.0f);
    Status.bControlPowerOn = bControlPowerOn; Status.bGuardsClosed = bGuardsClosed; Status.bStripAvailable = bStripAvailable; Status.bCassetteLocked = bCassetteLocked; Status.bDrivesHealthy = bDrivesHealthy;
    Status.bCanStart = CanStart(Status.BlockingReasons);
    return Status;
}

FLBPR006SaveState ALBPR006Station::CaptureSaveState() const
{
    FLBPR006SaveState Saved;
    Saved.StationId = StationId; Saved.State = State; Saved.ActiveFault = ActiveFault; Saved.CassetteId = CassetteId;
    Saved.TargetStripThicknessMm = TargetStripThicknessMm; Saved.TargetRollGapMm = TargetRollGapMm; Saved.ActualRollGapMm = ActualRollGapMm;
    Saved.StripTravelMetres = StripTravelMetres; Saved.RunningHours = RunningHours; Saved.TargetLineSpeedMetresPerMinute = TargetLineSpeedMetresPerMinute; Saved.MotorLoadPercent = MotorLoadPercent;
    Saved.bControlPowerOn = bControlPowerOn; Saved.bGuardsClosed = bGuardsClosed; Saved.bStripAvailable = bStripAvailable; Saved.bCassetteLocked = bCassetteLocked; Saved.bDrivesHealthy = bDrivesHealthy;
    return Saved;
}

bool ALBPR006Station::RestoreSaveState(const FLBPR006SaveState& SavedState)
{
    if (SavedState.Version != 1 || SavedState.StationId != StationId) return false;
    ActiveFault = SavedState.ActiveFault; CassetteId = SavedState.CassetteId; TargetStripThicknessMm = FMath::Clamp(SavedState.TargetStripThicknessMm, 0.4f, 4.0f);
    TargetRollGapMm = FMath::Clamp(SavedState.TargetRollGapMm, 0.1f, 6.0f); ActualRollGapMm = FMath::Clamp(SavedState.ActualRollGapMm, 0.1f, 10.0f);
    StripTravelMetres = FMath::Max(0.0f, SavedState.StripTravelMetres); RunningHours = FMath::Max(0.0f, SavedState.RunningHours); TargetLineSpeedMetresPerMinute = FMath::Max(0.0f, SavedState.TargetLineSpeedMetresPerMinute);
    MotorLoadPercent = FMath::Clamp(SavedState.MotorLoadPercent, 0.0f, 150.0f); bControlPowerOn = SavedState.bControlPowerOn; bGuardsClosed = SavedState.bGuardsClosed; bStripAvailable = SavedState.bStripAvailable; bCassetteLocked = SavedState.bCassetteLocked; bDrivesHealthy = SavedState.bDrivesHealthy;
    const bool bWasMoving = SavedState.State == ELBPR006State::Calibrating || SavedState.State == ELBPR006State::Running || SavedState.State == ELBPR006State::Stopping;
    State = !bControlPowerOn ? ELBPR006State::Isolated : (bWasMoving ? ELBPR006State::Ready : SavedState.State);
    if (bWasMoving) { ActiveFault = ELBPR006Fault::None; MotorLoadPercent = 0.0f; }
    PhaseElapsedSeconds = 0.0f; MotionAngleDegrees = 0.0f;
    if (HasActorBegunPlay()) ApplyMachinePose();
    return true;
}

void ALBPR006Station::ApplyMachinePose()
{
    for (USceneComponent* Mover : LowerRollMovers) Mover->SetRelativeRotation(FRotator(MotionAngleDegrees, 0.0f, 0.0f));
    for (USceneComponent* Mover : UpperRollMovers) Mover->SetRelativeRotation(FRotator(-MotionAngleDegrees, 0.0f, 0.0f));
    for (USceneComponent* Mover : DriveMotorMovers) Mover->SetRelativeRotation(FRotator(MotionAngleDegrees * 0.65f, 0.0f, 0.0f));
    const float GapDeltaCm = (ActualRollGapMm - TargetRollGapMm) * 0.10f;
    UpperCassetteMover->SetRelativeLocation(UpperCassetteRestLocation + FVector(0.0f, 0.0f, GapDeltaCm));
    for (int32 Index = 0; Index < GapCylinderMovers.Num() && Index < GapCylinderRestLocations.Num(); ++Index)
        GapCylinderMovers[Index]->SetRelativeLocation(GapCylinderRestLocations[Index] + FVector(0.0f, 0.0f, GapDeltaCm));
}

void ALBPR006Station::BindMapPresentation()
{
    for (TActorIterator<ATextRenderActor> It(GetWorld()); It; ++It)
    {
        const FString ActorName = It->GetActorNameOrLabel();
        if (ActorName.Contains(TEXT("PR006")) && ActorName.Contains(TEXT("HMI_Text_State"))) { HMIStatePresentation = *It; break; }
    }
}

void ALBPR006Station::UpdateHMITextPresentation()
{
    if (!HMIStatePresentation.IsValid()) return;
    UTextRenderComponent* Text = HMIStatePresentation->GetTextRender(); if (!Text) return;
    const UEnum* StateEnum = StaticEnum<ELBPR006State>(); const UEnum* FaultEnum = StaticEnum<ELBPR006Fault>();
    const FString StateName = StateEnum ? StateEnum->GetNameStringByValue(static_cast<int64>(State)).ToUpper() : TEXT("UNKNOWN");
    if (ActiveFault != ELBPR006Fault::None)
    {
        const FString FaultName = FaultEnum ? FaultEnum->GetNameStringByValue(static_cast<int64>(ActiveFault)).ToUpper() : TEXT("FAULT");
        Text->SetText(FText::FromString(FString::Printf(TEXT("FAULT %s | STOPPED"), *FaultName))); Text->SetTextRenderColor(FColor(220, 45, 35));
    }
    else
    {
        Text->SetText(FText::FromString(FString::Printf(TEXT("%s | GAP %.2f mm | LOAD %.0f%%"), *StateName, ActualRollGapMm, MotorLoadPercent)));
        Text->SetTextRenderColor(State == ELBPR006State::Running ? FColor(45, 220, 145) : FColor(225, 166, 0));
    }
}

#undef LOCTEXT_NAMESPACE
