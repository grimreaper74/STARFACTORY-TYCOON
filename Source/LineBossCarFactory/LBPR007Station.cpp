#include "LBPR007Station.h"

#include "Components/SceneComponent.h"
#include "Components/TextRenderComponent.h"
#include "Engine/TextRenderActor.h"
#include "EngineUtils.h"

#define LOCTEXT_NAMESPACE "CairnwellPR007"

ALBPR007Station::ALBPR007Station()
{
    PrimaryActorTick.bCanEverTick = true;
    StationRoot = CreateDefaultSubobject<USceneComponent>(TEXT("PR007_StationRoot"));
    SetRootComponent(StationRoot);
    WashHoodMover = CreateDefaultSubobject<USceneComponent>(TEXT("PR007_WashHoodMover"));
    WashHoodMover->SetupAttachment(StationRoot);
    WashPumpMover = CreateDefaultSubobject<USceneComponent>(TEXT("PR007_WashPumpMover"));
    WashPumpMover->SetupAttachment(StationRoot);
    LubePumpMover = CreateDefaultSubobject<USceneComponent>(TEXT("PR007_LubePumpMover"));
    LubePumpMover->SetupAttachment(StationRoot);
    FeedRollerMover = CreateDefaultSubobject<USceneComponent>(TEXT("PR007_FeedRollerMover"));
    FeedRollerMover->SetupAttachment(StationRoot);
    WashRollerMover = CreateDefaultSubobject<USceneComponent>(TEXT("PR007_WashRollerMover"));
    WashRollerMover->SetupAttachment(StationRoot);
    LubeRollerMover = CreateDefaultSubobject<USceneComponent>(TEXT("PR007_LubeRollerMover"));
    LubeRollerMover->SetupAttachment(StationRoot);
    OutfeedRollerMover = CreateDefaultSubobject<USceneComponent>(TEXT("PR007_OutfeedRollerMover"));
    OutfeedRollerMover->SetupAttachment(StationRoot);
}

void ALBPR007Station::BeginPlay()
{
    Super::BeginPlay();
    HoodRestLocation = WashHoodMover->GetRelativeLocation();
    BindMapPresentation();
    ApplyMachinePose();
    UpdateHMITextPresentation();
}

void ALBPR007Station::Tick(float DeltaSeconds)
{
    Super::Tick(DeltaSeconds);
    PhaseElapsedSeconds += DeltaSeconds;

    if (State == ELBPR007State::Priming && PhaseElapsedSeconds >= PrimingDurationSeconds)
    {
        SetState(ELBPR007State::Running);
    }
    else if (State == ELBPR007State::Stopping && PhaseElapsedSeconds >= StoppingDurationSeconds)
    {
        SetState(ELBPR007State::Ready);
    }

    if (State == ELBPR007State::Priming || State == ELBPR007State::Running)
    {
        EvaluateRuntimePermissives();
    }

    if (State == ELBPR007State::Running)
    {
        const float TravelThisTick = TargetLineSpeedMetresPerMinute * DeltaSeconds / 60.0f;
        StripTravelMetres += TravelThisTick;
        RunningHours += DeltaSeconds / 3600.0f;
        WashLevelPercent = FMath::Max(0.0f, WashLevelPercent - TravelThisTick * WashConsumptionPercentPerMetre);
        LubeLevelPercent = FMath::Max(0.0f, LubeLevelPercent - TravelThisTick * LubeConsumptionPercentPerMetre);
        FilterDifferentialBar = FMath::Min(3.0f, FilterDifferentialBar + TravelThisTick * 0.00002f);
        MotionAngleDegrees = FMath::Fmod(MotionAngleDegrees + DeltaSeconds * 540.0f, 360.0f);
    }
    else if (State == ELBPR007State::Priming)
    {
        MotionAngleDegrees = FMath::Fmod(MotionAngleDegrees + DeltaSeconds * 270.0f, 360.0f);
    }
    ApplyMachinePose();
    UpdateHMITextPresentation();
}

void ALBPR007Station::SetState(ELBPR007State NewState)
{
    if (State == NewState) return;
    const ELBPR007State Previous = State;
    State = NewState;
    PhaseElapsedSeconds = 0.0f;
    OnStateChanged.Broadcast(Previous, NewState);
}

void ALBPR007Station::SetControlPower(bool bEnabled)
{
    bControlPowerOn = bEnabled;
    if (!bEnabled)
    {
        ActiveFault = ELBPR007Fault::None;
        SetState(ELBPR007State::Isolated);
    }
    else if (State == ELBPR007State::Isolated)
    {
        SetState(ELBPR007State::Ready);
    }
}

void ALBPR007Station::SetGuardsClosed(bool bClosed)
{
    bGuardsClosed = bClosed;
    if (!bClosed && (State == ELBPR007State::Priming || State == ELBPR007State::Running)) RaiseFault(ELBPR007Fault::GuardOpen);
}

void ALBPR007Station::SetStripThreaded(bool bThreaded) { bStripThreaded = bThreaded; }

void ALBPR007Station::SetMistExtractionHealthy(bool bHealthy)
{
    bMistExtractionHealthy = bHealthy;
    if (!bHealthy && (State == ELBPR007State::Priming || State == ELBPR007State::Running)) RaiseFault(ELBPR007Fault::MistExtractionUnavailable);
}

void ALBPR007Station::SetFluidLevels(float NewWashPercent, float NewLubePercent)
{
    WashLevelPercent = FMath::Clamp(NewWashPercent, 0.0f, 100.0f);
    LubeLevelPercent = FMath::Clamp(NewLubePercent, 0.0f, 100.0f);
}

void ALBPR007Station::SetFilterDifferential(float DifferentialBar)
{
    FilterDifferentialBar = FMath::Clamp(DifferentialBar, 0.0f, 3.0f);
}

bool ALBPR007Station::CanStart(TArray<FText>& BlockingReasons) const
{
    BlockingReasons.Reset();
    if (!bControlPowerOn) BlockingReasons.Add(LOCTEXT("PowerOff", "Control power is off"));
    if (State != ELBPR007State::Ready) BlockingReasons.Add(LOCTEXT("NotReady", "Station is not ready"));
    if (!bGuardsClosed) BlockingReasons.Add(LOCTEXT("GuardsOpen", "Guard or service door is open"));
    if (!bStripThreaded) BlockingReasons.Add(LOCTEXT("StripNotThreaded", "Strip is not threaded"));
    if (WashLevelPercent < MinimumFluidPercent) BlockingReasons.Add(LOCTEXT("WashLow", "Wash-fluid level is low"));
    if (LubeLevelPercent < MinimumFluidPercent) BlockingReasons.Add(LOCTEXT("LubeLow", "Lubricant level is low"));
    if (FilterDifferentialBar > MaximumFilterDifferentialBar) BlockingReasons.Add(LOCTEXT("FilterHigh", "Filter differential pressure is high"));
    if (!bMistExtractionHealthy) BlockingReasons.Add(LOCTEXT("ExtractionBad", "Mist extraction is unavailable"));
    return BlockingReasons.IsEmpty();
}

bool ALBPR007Station::StartLine()
{
    TArray<FText> Reasons;
    if (!CanStart(Reasons)) return false;
    ActiveFault = ELBPR007Fault::None;
    SetState(ELBPR007State::Priming);
    return true;
}

void ALBPR007Station::RequestControlledStop()
{
    if (State == ELBPR007State::Priming || State == ELBPR007State::Running) SetState(ELBPR007State::Stopping);
}

void ALBPR007Station::RaiseFault(ELBPR007Fault Fault)
{
    if (Fault == ELBPR007Fault::None || State == ELBPR007State::Fault) return;
    ActiveFault = Fault;
    SetState(ELBPR007State::Fault);
    OnFaultRaised.Broadcast(Fault);
}

void ALBPR007Station::EvaluateRuntimePermissives()
{
    if (!bGuardsClosed) RaiseFault(ELBPR007Fault::GuardOpen);
    else if (WashLevelPercent < MinimumFluidPercent) RaiseFault(ELBPR007Fault::LowWashLevel);
    else if (LubeLevelPercent < MinimumFluidPercent) RaiseFault(ELBPR007Fault::LowLubeLevel);
    else if (FilterDifferentialBar > MaximumFilterDifferentialBar) RaiseFault(ELBPR007Fault::FilterDifferentialHigh);
    else if (!bMistExtractionHealthy) RaiseFault(ELBPR007Fault::MistExtractionUnavailable);
}

bool ALBPR007Station::ResetFault()
{
    if (State != ELBPR007State::Fault || ActiveFault == ELBPR007Fault::None || !bControlPowerOn) return false;
    TArray<FText> Reasons;
    const ELBPR007State PreviousState = State;
    State = ELBPR007State::Ready;
    const bool bPermissivesHealthy = CanStart(Reasons);
    State = PreviousState;
    if (!bPermissivesHealthy) return false;
    ActiveFault = ELBPR007Fault::None;
    SetState(ELBPR007State::Ready);
    return true;
}

FLBPR007HMIStatus ALBPR007Station::GetHMIStatus() const
{
    FLBPR007HMIStatus Status;
    Status.StationId = StationId;
    Status.State = State;
    Status.ActiveFault = ActiveFault;
    Status.WashLevelPercent = WashLevelPercent;
    Status.LubeLevelPercent = LubeLevelPercent;
    Status.FilterDifferentialBar = FilterDifferentialBar;
    Status.StripTravelMetres = StripTravelMetres;
    Status.LineSpeedMetresPerMinute = State == ELBPR007State::Running ? TargetLineSpeedMetresPerMinute : 0.0f;
    Status.HoodPosition = State == ELBPR007State::Priming ? FMath::Clamp(PhaseElapsedSeconds / PrimingDurationSeconds, 0.0f, 1.0f)
        : (State == ELBPR007State::Running ? 1.0f : (State == ELBPR007State::Stopping ? 1.0f - FMath::Clamp(PhaseElapsedSeconds / StoppingDurationSeconds, 0.0f, 1.0f) : 0.0f));
    Status.bControlPowerOn = bControlPowerOn;
    Status.bGuardsClosed = bGuardsClosed;
    Status.bStripThreaded = bStripThreaded;
    Status.bMistExtractionHealthy = bMistExtractionHealthy;
    Status.bCanStart = CanStart(Status.BlockingReasons);
    return Status;
}

FLBPR007SaveState ALBPR007Station::CaptureSaveState() const
{
    FLBPR007SaveState Saved;
    Saved.StationId = StationId;
    Saved.State = State;
    Saved.ActiveFault = ActiveFault;
    Saved.WashLevelPercent = WashLevelPercent;
    Saved.LubeLevelPercent = LubeLevelPercent;
    Saved.FilterDifferentialBar = FilterDifferentialBar;
    Saved.StripTravelMetres = StripTravelMetres;
    Saved.RunningHours = RunningHours;
    Saved.TargetLineSpeedMetresPerMinute = TargetLineSpeedMetresPerMinute;
    Saved.bControlPowerOn = bControlPowerOn;
    Saved.bGuardsClosed = bGuardsClosed;
    Saved.bStripThreaded = bStripThreaded;
    Saved.bMistExtractionHealthy = bMistExtractionHealthy;
    return Saved;
}

bool ALBPR007Station::RestoreSaveState(const FLBPR007SaveState& SavedState)
{
    if (SavedState.Version != 1 || SavedState.StationId != StationId) return false;
    ActiveFault = SavedState.ActiveFault;
    WashLevelPercent = FMath::Clamp(SavedState.WashLevelPercent, 0.0f, 100.0f);
    LubeLevelPercent = FMath::Clamp(SavedState.LubeLevelPercent, 0.0f, 100.0f);
    FilterDifferentialBar = FMath::Clamp(SavedState.FilterDifferentialBar, 0.0f, 3.0f);
    StripTravelMetres = FMath::Max(0.0f, SavedState.StripTravelMetres);
    RunningHours = FMath::Max(0.0f, SavedState.RunningHours);
    TargetLineSpeedMetresPerMinute = FMath::Max(0.0f, SavedState.TargetLineSpeedMetresPerMinute);
    bControlPowerOn = SavedState.bControlPowerOn;
    bGuardsClosed = SavedState.bGuardsClosed;
    bStripThreaded = SavedState.bStripThreaded;
    bMistExtractionHealthy = SavedState.bMistExtractionHealthy;
    const bool bWasMoving = SavedState.State == ELBPR007State::Priming || SavedState.State == ELBPR007State::Running || SavedState.State == ELBPR007State::Stopping;
    State = !bControlPowerOn ? ELBPR007State::Isolated : (bWasMoving ? ELBPR007State::Ready : SavedState.State);
    if (bWasMoving) ActiveFault = ELBPR007Fault::None;
    PhaseElapsedSeconds = 0.0f;
    MotionAngleDegrees = 0.0f;
    if (HasActorBegunPlay()) ApplyMachinePose();
    return true;
}

void ALBPR007Station::ApplyMachinePose()
{
    const float HoodPosition = GetHMIStatus().HoodPosition;
    WashHoodMover->SetRelativeLocation(HoodRestLocation + FVector(0.0f, 0.0f, -18.0f * HoodPosition));
    WashPumpMover->SetRelativeRotation(FRotator(MotionAngleDegrees, 0.0f, 0.0f));
    LubePumpMover->SetRelativeRotation(FRotator(MotionAngleDegrees * 0.8f, 0.0f, 0.0f));
    FeedRollerMover->SetRelativeRotation(FRotator(MotionAngleDegrees, 0.0f, 0.0f));
    WashRollerMover->SetRelativeRotation(FRotator(MotionAngleDegrees, 0.0f, 0.0f));
    LubeRollerMover->SetRelativeRotation(FRotator(MotionAngleDegrees, 0.0f, 0.0f));
    OutfeedRollerMover->SetRelativeRotation(FRotator(MotionAngleDegrees, 0.0f, 0.0f));
}

void ALBPR007Station::BindMapPresentation()
{
    for (TActorIterator<ATextRenderActor> It(GetWorld()); It; ++It)
    {
        const FString ActorName = It->GetActorNameOrLabel();
        if (ActorName.Contains(TEXT("PR007")) && ActorName.Contains(TEXT("HMI_Text_State")))
        {
            HMIStatePresentation = *It;
            break;
        }
    }
}

void ALBPR007Station::UpdateHMITextPresentation()
{
    if (!HMIStatePresentation.IsValid()) return;
    UTextRenderComponent* Text = HMIStatePresentation->GetTextRender();
    if (!Text) return;
    const UEnum* StateEnum = StaticEnum<ELBPR007State>();
    const UEnum* FaultEnum = StaticEnum<ELBPR007Fault>();
    const FString StateName = StateEnum ? StateEnum->GetNameStringByValue(static_cast<int64>(State)).ToUpper() : TEXT("UNKNOWN");
    if (ActiveFault != ELBPR007Fault::None)
    {
        const FString FaultName = FaultEnum ? FaultEnum->GetNameStringByValue(static_cast<int64>(ActiveFault)).ToUpper() : TEXT("FAULT");
        Text->SetText(FText::FromString(FString::Printf(TEXT("FAULT %s | STOPPED"), *FaultName)));
        Text->SetTextRenderColor(FColor(220, 45, 35));
    }
    else
    {
        Text->SetText(FText::FromString(FString::Printf(TEXT("%s | WASH %.0f%% | LUBE %.0f%%"), *StateName, WashLevelPercent, LubeLevelPercent)));
        Text->SetTextRenderColor(State == ELBPR007State::Running ? FColor(45, 220, 145) : FColor(225, 166, 0));
    }
}

#undef LOCTEXT_NAMESPACE
