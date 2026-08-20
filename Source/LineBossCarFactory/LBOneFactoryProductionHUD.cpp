#include "LBOneFactoryProductionHUD.h"

#include "Engine/Canvas.h"
#include "Engine/Engine.h"
#include "Engine/Font.h"
#include "EngineUtils.h"
#include "Blueprint/UserWidget.h"
#include "Internationalization/Text.h"
#include "LBFactoryManagementSubsystem.h"
#include "LBOneFactoryRuntimeCoordinator.h"
#include "LBOneFactoryTopBarWidget.h"

#define LOCTEXT_NAMESPACE "LineBossProductionHUD"

namespace LBOneFactoryHUDPrivate
{
    // BRAND_IDENTITY_AUTHORITY palette. Safety Yellow and Signal Red stay
    // functional: they only appear as waiting and hold states.
    const FLinearColor Charcoal =
        FLinearColor::FromSRGBColor(FColor::FromHex(TEXT("202428")));
    const FLinearColor CharcoalDeep =
        FLinearColor::FromSRGBColor(FColor::FromHex(TEXT("171A1D")));
    const FLinearColor Cairnwell =
        FLinearColor::FromSRGBColor(FColor::FromHex(TEXT("1F4B44")));
    const FLinearColor CairnwellLit =
        FLinearColor::FromSRGBColor(FColor::FromHex(TEXT("3FBF9E")));
    const FLinearColor Steel =
        FLinearColor::FromSRGBColor(FColor::FromHex(TEXT("70777C")));
    const FLinearColor Warm =
        FLinearColor::FromSRGBColor(FColor::FromHex(TEXT("F3F1E9")));
    const FLinearColor Yellow =
        FLinearColor::FromSRGBColor(FColor::FromHex(TEXT("F2C300")));
    const FLinearColor Red =
        FLinearColor::FromSRGBColor(FColor::FromHex(TEXT("C7352C")));

    /** The seven coarse stages of the car's journey, in physical order. */
    struct FGroupSpec
    {
        ELBOneFactoryVehicleStage First;
        ELBOneFactoryVehicleStage Last;
    };
    /** Player-facing group names, gathered for localisation. */
    FText GroupDisplayLabel(const int32 GroupIndex)
    {
        switch (GroupIndex)
        {
        case 0: return LOCTEXT("GroupCoilIntake", "Coil intake");
        case 1: return LOCTEXT("GroupPress", "Press");
        case 2: return LOCTEXT("GroupPanelStillages", "Panel stillages");
        case 3: return LOCTEXT("GroupBodyWeld", "Body weld");
        case 4: return LOCTEXT("GroupPaint", "Paint");
        case 5: return LOCTEXT("GroupAssembly", "Assembly");
        default: return LOCTEXT("GroupDispatch", "Dispatch");
        }
    }

    // Names live in GroupDisplayLabel; this table is stage ranges only.
    const FGroupSpec GroupSpecs[] = {
        { ELBOneFactoryVehicleStage::InboundCoil,
          ELBOneFactoryVehicleStage::BlankPreparation },
        { ELBOneFactoryVehicleStage::Pressing,
          ELBOneFactoryVehicleStage::Pressing },
        { ELBOneFactoryVehicleStage::PressedPanelStillage,
          ELBOneFactoryVehicleStage::PressedPanelStillage },
        { ELBOneFactoryVehicleStage::BodyFraming,
          ELBOneFactoryVehicleStage::BodyQualityInspection },
        { ELBOneFactoryVehicleStage::Pretreatment,
          ELBOneFactoryVehicleStage::PaintQualityInspection },
        { ELBOneFactoryVehicleStage::GeneralAssemblyTrim,
          ELBOneFactoryVehicleStage::EndOfLineInspection },
        { ELBOneFactoryVehicleStage::FinishedVehicle,
          ELBOneFactoryVehicleStage::Dispatched },
    };
    constexpr int32 GroupCount = UE_ARRAY_COUNT(GroupSpecs);

    int32 GroupIndexForStage(const ELBOneFactoryVehicleStage Stage)
    {
        const uint8 Value = static_cast<uint8>(Stage);
        for (int32 Index = 0; Index < GroupCount; ++Index)
        {
            if (Value >= static_cast<uint8>(GroupSpecs[Index].First)
                && Value <= static_cast<uint8>(GroupSpecs[Index].Last))
            {
                return Index;
            }
        }
        return INDEX_NONE;
    }

    FLinearColor StateColour(const ELBOneFactoryGroupState State)
    {
        switch (State)
        {
        case ELBOneFactoryGroupState::Running: return CairnwellLit;
        case ELBOneFactoryGroupState::Waiting: return Yellow;
        case ELBOneFactoryGroupState::Hold:    return Red;
        default:                               return Steel;
        }
    }

    /** One decimal place, matching the HUD's original rate formatting. */
    const FNumberFormattingOptions RateFormat =
        FNumberFormattingOptions()
            .SetMinimumFractionalDigits(1)
            .SetMaximumFractionalDigits(1);

    FText StateLabel(const ELBOneFactoryGroupState State)
    {
        switch (State)
        {
        case ELBOneFactoryGroupState::Running:
            return LOCTEXT("StateRunning", "Running");
        case ELBOneFactoryGroupState::Waiting:
            return LOCTEXT("StateWaiting", "Waiting");
        case ELBOneFactoryGroupState::Hold:
            return LOCTEXT("StateHold", "Hold");
        default:
            return LOCTEXT("StateIdle", "Idle");
        }
    }
}

ALBOneFactoryProductionHUD::ALBOneFactoryProductionHUD()
{
    PrimaryActorTick.bCanEverTick = false;
}

ELBOneFactoryGroupState ALBOneFactoryProductionHUD::StateForStage(
    const ELBOneFactoryVehicleStage Stage)
{
    return LBOneFactoryHUDPrivate::GroupIndexForStage(Stage) == INDEX_NONE
        ? ELBOneFactoryGroupState::Idle
        : ELBOneFactoryGroupState::Running;
}

bool ALBOneFactoryProductionHUD::CollectGroups(const UWorld* World,
    TArray<FLBOneFactoryProcessGroup>& OutGroups, int32& OutUnitsLive,
    int32& OutDispatched, TArray<FString>& OutAlerts)
{
    using namespace LBOneFactoryHUDPrivate;

    OutGroups.Reset();
    OutUnitsLive = 0;
    OutDispatched = 0;
    OutAlerts.Reset();
    if (!World)
    {
        return false;
    }

    ALBOneFactoryRuntimeCoordinator* Coordinator = nullptr;
    ALBOneFactoryProductionFlowAuthority* Production = nullptr;
    for (TActorIterator<ALBOneFactoryRuntimeCoordinator> It(World); It; ++It)
    {
        if (IsValid(*It)) { Coordinator = *It; break; }
    }
    for (TActorIterator<ALBOneFactoryProductionFlowAuthority> It(World); It; ++It)
    {
        if (IsValid(*It)) { Production = *It; break; }
    }
    if (!Coordinator || !Production)
    {
        return false;
    }

    OutGroups.SetNum(GroupCount);
    // Bottleneck cycle per group, so throughput reflects the slowest station in
    // it rather than an average that no real line would achieve.
    TArray<float> SlowestCycle;
    SlowestCycle.Init(0.0f, GroupCount);
    for (int32 Index = 0; Index < GroupCount; ++Index)
    {
        OutGroups[Index].Label = GroupDisplayLabel(Index).ToString();
    }

    TArray<FLBOneFactoryRuntimeStationStep> Route;
    FName TopologyId = NAME_None;
    FString Reason;
    if (Coordinator->GetConfiguredStationRoute(Route, TopologyId, Reason))
    {
        for (const FLBOneFactoryRuntimeStationStep& Step : Route)
        {
            const int32 Index = GroupIndexForStage(Step.SemanticStage);
            if (Index == INDEX_NONE)
            {
                continue;
            }
            ++OutGroups[Index].StationCount;
            OutGroups[Index].bHasQualityGate |= Step.bQualityGate;
            SlowestCycle[Index] =
                FMath::Max(SlowestCycle[Index], Step.NominalCycleSeconds);
        }
    }
    for (int32 Index = 0; Index < GroupCount; ++Index)
    {
        OutGroups[Index].ThroughputPerHour = SlowestCycle[Index] > KINDA_SMALL_NUMBER
            ? 3600.0f / SlowestCycle[Index]
            : 0.0f;
    }

    TArray<float> ProgressTotal;
    ProgressTotal.Init(0.0f, GroupCount);

    const FLBOneFactoryProductionLedgerState Ledger = Production->CaptureLedger();
    for (const FLBOneFactoryVehicleUnitState& Unit : Ledger.Units)
    {
        if (Unit.bDispatched)
        {
            ++OutDispatched;
            continue;
        }
        ++OutUnitsLive;

        const int32 Index = GroupIndexForStage(Unit.Stage);
        if (Index == INDEX_NONE)
        {
            continue;
        }
        FLBOneFactoryProcessGroup& Group = OutGroups[Index];
        ++Group.UnitCount;

        FLBOneFactoryRuntimeVehicleStatus Status;
        FString StatusReason;
        if (!Coordinator->GetVehicleRuntimeStatus(Unit.UnitId, Status,
                StatusReason))
        {
            continue;
        }
        ProgressTotal[Index] += Status.NormalizedCycleProgress;

        if (Status.bAwaitingQualityResult)
        {
            Group.State = ELBOneFactoryGroupState::Hold;
            OutAlerts.Add(FText::Format(
                LOCTEXT("AlertQualityHold",
                    "{Group} held at {Station} awaiting a quality result."),
                FFormatNamedArguments{
                    { TEXT("Group"), FText::FromString(Group.Label) },
                    { TEXT("Station"),
                      FText::FromName(Status.CurrentStationId) } })
                .ToString());
        }
        else if (Status.NormalizedCycleProgress >= 0.999f)
        {
            if (Group.State != ELBOneFactoryGroupState::Hold)
            {
                Group.State = ELBOneFactoryGroupState::Waiting;
            }
            OutAlerts.Add(FText::Format(
                LOCTEXT("AlertBlockedTransfer",
                    "{Group} finished its cycle at {Station} and cannot "
                    "move on."),
                FFormatNamedArguments{
                    { TEXT("Group"), FText::FromString(Group.Label) },
                    { TEXT("Station"),
                      FText::FromName(Status.CurrentStationId) } })
                .ToString());
        }
        else if (Group.State == ELBOneFactoryGroupState::Idle)
        {
            Group.State = ELBOneFactoryGroupState::Running;
        }
    }

    for (int32 Index = 0; Index < GroupCount; ++Index)
    {
        OutGroups[Index].MeanProgress = OutGroups[Index].UnitCount > 0
            ? ProgressTotal[Index] / OutGroups[Index].UnitCount
            : 0.0f;
    }
    return true;
}

void ALBOneFactoryProductionHUD::DrawHUD()
{
    Super::DrawHUD();
    if (!Canvas)
    {
        return;
    }

    const float Width = static_cast<float>(Canvas->SizeX);
    const float Height = static_cast<float>(Canvas->SizeY);
    const float Scale = FMath::Max(Height / 1080.0f, 0.5f);

    TArray<FLBOneFactoryProcessGroup> Groups;
    TArray<FString> Alerts;
    int32 UnitsLive = 0;
    int32 Dispatched = 0;
    if (!CollectGroups(GetWorld(), Groups, UnitsLive, Dispatched, Alerts))
    {
        using namespace LBOneFactoryHUDPrivate;
        UFont* Font = GEngine ? GEngine->GetLargeFont() : nullptr;
        DrawRect(CharcoalDeep.CopyWithNewOpacity(0.86f), 0.0f, 0.0f,
            Width, 44.0f * Scale);
        if (Font)
        {
            DrawText(LOCTEXT("BannerNoFactory",
                    "MOORCROSS WORKS  -  no commissioned factory yet.  "
                    "Run LB.OneFactory.BuildWholeFactory").ToString(),
                Warm, 20.0f * Scale, 13.0f * Scale, Font, Scale, false);
        }
        return;
    }

    DrawFlowStrip(Width, Height, Scale, Groups, UnitsLive, Dispatched,
        Alerts.Num());
    DrawAlertToast(Width, Height, Scale, Alerts);

    if (bUseCanvasManagementBand)
    {
        FLBOneFactoryManagementBand Band;
        if (CollectManagement(GetWorld(), Band))
        {
            DrawManagementBand(Width, Scale, Band);
        }
    }
}

void ALBOneFactoryProductionHUD::BeginPlay()
{
    Super::BeginPlay();
    if (APlayerController* Controller = GetOwningPlayerController())
    {
        TopBarWidget = CreateWidget<ULBOneFactoryTopBarWidget>(Controller,
            ULBOneFactoryTopBarWidget::StaticClass());
        if (TopBarWidget)
        {
            TopBarWidget->AddToViewport(10);
        }
    }
}

bool ALBOneFactoryProductionHUD::CollectManagement(const UWorld* World,
    FLBOneFactoryManagementBand& OutBand)
{
    if (!World)
    {
        return false;
    }
    ALBOneFactoryProductionFlowAuthority* Production = nullptr;
    for (TActorIterator<ALBOneFactoryProductionFlowAuthority>
        It(const_cast<UWorld*>(World)); It; ++It)
    {
        Production = *It;
        break;
    }
    if (!Production)
    {
        return false;
    }
    const FLBOneFactoryProductionLedgerState Ledger =
        Production->CaptureLedger();
    OutBand.SimClockSeconds = Ledger.SimClockSeconds;
    OutBand.bPaused = Ledger.bLinePaused;
    OutBand.Reputation = Ledger.ReputationScore;
    OutBand.FleetWear01 = Ledger.FleetWear01;
    OutBand.FinancialState = Ledger.FinancialState;
    for (const FLBOneFactoryVehicleContract& Contract : Ledger.Contracts)
    {
        FLBOneFactoryContractRow Row;
        Row.ContractId = Contract.ContractId.ToString();
        Row.DispatchedCount = Contract.DispatchedCount;
        Row.Quantity = Contract.Quantity;
        Row.SecondsRemaining = Contract.DeadlineSimSeconds > 0.0
            ? Contract.DeadlineSimSeconds - Ledger.SimClockSeconds : 0.0;
        Row.State = Contract.State;
        Row.bEmergency = Contract.bEmergency;
        OutBand.Contracts.Add(Row);
    }
    if (const ULBFactoryManagementSubsystem* Management =
            World->GetSubsystem<ULBFactoryManagementSubsystem>())
    {
        if (Management->IsCampaignInitialised())
        {
            OutBand.bHasCash = true;
            OutBand.CashPence = Management->GetCashBalancePence();
        }
    }
    return true;
}

void ALBOneFactoryProductionHUD::DrawManagementBand(const float Width,
    const float Scale, const FLBOneFactoryManagementBand& Band)
{
    using namespace LBOneFactoryHUDPrivate;
    UFont* Font = GEngine ? GEngine->GetSmallFont() : nullptr;
    if (!Font)
    {
        return;
    }
    const float BandW = 300.0f * Scale;
    const float RowH = 18.0f * Scale;
    const float X = Width - BandW - 14.0f * Scale;
    float Y = 12.0f * Scale;

    // Header rows: cash, clock/pause, reputation and wear.
    int32 Rows = 3 + FMath::Min(Band.Contracts.Num(), 4);
    DrawRect(CharcoalDeep.CopyWithNewOpacity(0.88f), X - 8.0f * Scale,
        Y - 6.0f * Scale, BandW, Rows * RowH + 16.0f * Scale);
    const FLinearColor StateColour =
        Band.FinancialState == ELBOneFactoryFinancialState::Emergency
            ? Red
            : Band.FinancialState == ELBOneFactoryFinancialState::Warning
                ? Yellow : CairnwellLit;
    const FText CashText = Band.bHasCash
        ? FText::Format(LOCTEXT("BandCash", "CASH  £{0}"),
            FText::AsNumber(Band.CashPence / 100))
        : LOCTEXT("BandCashPending", "CASH  -");
    DrawText(CashText.ToString(), StateColour, X, Y, Font, Scale, false);
    Y += RowH;

    const int32 TotalMinutes =
        FMath::FloorToInt32(Band.SimClockSeconds / 60.0);
    FNumberFormattingOptions TwoDigits;
    TwoDigits.MinimumIntegralDigits = 2;
    const FText ClockText = FText::Format(
        LOCTEXT("BandClock", "DAY {0}  {1}:{2}{3}"),
        FText::AsNumber(1 + TotalMinutes / (24 * 60)),
        FText::AsNumber((TotalMinutes / 60) % 24),
        FText::AsNumber(TotalMinutes % 60, &TwoDigits),
        Band.bPaused ? LOCTEXT("BandPaused", "   PAUSED")
                     : FText::GetEmpty());
    DrawText(ClockText.ToString(), Band.bPaused ? Yellow : Warm, X, Y, Font,
        Scale, false);
    Y += RowH;

    const int32 WearPercent = FMath::RoundToInt(Band.FleetWear01 * 100.0);
    const FText WearText = FText::Format(
        LOCTEXT("BandRepWear", "REP {0}   WEAR {1}%{2}"),
        FText::AsNumber(Band.Reputation), FText::AsNumber(WearPercent),
        Band.FleetWear01 > 0.6 ? LOCTEXT("BandServiceDue", "   SERVICE DUE")
                               : FText::GetEmpty());
    DrawText(WearText.ToString(),
        Band.FleetWear01 > 0.6 ? Yellow : Steel, X, Y, Font, Scale, false);
    Y += RowH;

    // Up to four contracts, open first (creation order preserved).
    int32 Drawn = 0;
    for (const FLBOneFactoryContractRow& Row : Band.Contracts)
    {
        if (Drawn >= 4)
        {
            break;
        }
        FText Status;
        if (Row.State == ELBOneFactoryContractState::Complete)
        {
            Status = LOCTEXT("ContractComplete", "COMPLETE");
        }
        else if (Row.State == ELBOneFactoryContractState::Expired)
        {
            Status = LOCTEXT("ContractExpired", "EXPIRED");
        }
        else
        {
            const int32 MinutesLeft = FMath::Max(0,
                FMath::FloorToInt32(Row.SecondsRemaining / 60.0));
            Status = FText::Format(LOCTEXT("ContractDue", "due {0}h {1}m"),
                FText::AsNumber(MinutesLeft / 60),
                FText::AsNumber(MinutesLeft % 60));
        }
        const FText RowText = FText::Format(
            LOCTEXT("ContractRow", "{0}{1}  {2}/{3}  {4}"),
            Row.bEmergency ? LOCTEXT("ContractRescue", "RESCUE ")
                           : FText::GetEmpty(),
            FText::FromString(Row.ContractId),
            FText::AsNumber(Row.DispatchedCount),
            FText::AsNumber(Row.Quantity), Status);
        const FLinearColor RowColour =
            Row.State == ELBOneFactoryContractState::Expired ? Steel
            : Row.bEmergency ? Yellow
            : Row.State == ELBOneFactoryContractState::Complete
                ? CairnwellLit : Warm;
        DrawText(RowText.ToString(), RowColour, X, Y, Font, Scale, false);
        Y += RowH;
        ++Drawn;
    }
}

void ALBOneFactoryProductionHUD::DrawFlowStrip(const float Width,
    const float Height, const float Scale,
    const TArray<FLBOneFactoryProcessGroup>& Groups, const int32 UnitsLive,
    const int32 Dispatched, const int32 AlertCount)
{
    using namespace LBOneFactoryHUDPrivate;
    UFont* Small = GEngine ? GEngine->GetSmallFont() : nullptr;
    UFont* Large = GEngine ? GEngine->GetLargeFont() : nullptr;

    const float StripH = 132.0f * Scale;
    const float StripY = Height - StripH;
    DrawRect(CharcoalDeep.CopyWithNewOpacity(0.92f), 0.0f, StripY, Width, StripH);
    DrawRect(CairnwellLit.CopyWithNewOpacity(0.45f), 0.0f, StripY,
        Width, 2.0f * Scale);

    const float Pad = 18.0f * Scale;
    if (Small)
    {
        DrawText(LOCTEXT("HeaderProductionFlow", "PRODUCTION FLOW")
                .ToString(), Steel, Pad, StripY + 8.0f * Scale,
            Small, Scale, false);

        const FString Summary = FString::Printf(
            TEXT("ON LINE %d     DISPATCHED %d     ALERTS %d"),
            UnitsLive, Dispatched, AlertCount);
        DrawText(Summary, AlertCount > 0 ? Yellow : Steel,
            Width - Pad - 280.0f * Scale, StripY + 8.0f * Scale, Small,
            Scale, false);
    }

    const float CardsY = StripY + 28.0f * Scale;
    const float CardH = StripH - 38.0f * Scale;
    const float Gap = 8.0f * Scale;
    const float Available = Width - Pad * 2.0f;
    const float ArrowW = 14.0f * Scale;
    const int32 Count = Groups.Num();
    if (Count == 0)
    {
        return;
    }
    const float CardW =
        (Available - (Count - 1) * (Gap + ArrowW)) / static_cast<float>(Count);

    float X = Pad;
    for (int32 Index = 0; Index < Count; ++Index)
    {
        const FLBOneFactoryProcessGroup& Group = Groups[Index];
        const FLinearColor Accent = StateColour(Group.State);
        const bool bActive = Group.UnitCount > 0;

        DrawRect(bActive
            ? Cairnwell.CopyWithNewOpacity(0.30f)
            : Warm.CopyWithNewOpacity(0.045f), X, CardsY, CardW, CardH);
        // Left severity stripe so state reads before any text is parsed.
        DrawRect(Accent, X, CardsY, 3.0f * Scale, CardH);

        if (Large)
        {
            DrawText(Group.Label, Warm, X + 10.0f * Scale,
                CardsY + 7.0f * Scale, Large, Scale, false);
        }
        if (Small)
        {
            DrawText(FText::Format(
                    LOCTEXT("StationCount", "{0} {0}|plural(one=station,"
                        "other=stations){1}"),
                    FText::AsNumber(Group.StationCount),
                    Group.bHasQualityGate
                        ? LOCTEXT("QualityGateSuffix", "  QA GATE")
                        : FText::GetEmpty()).ToString(),
                Steel, X + 10.0f * Scale, CardsY + 27.0f * Scale, Small,
                Scale, false);
        }

        // Progress bar: mean cycle progress of the units standing in the group.
        const float BarY = CardsY + CardH - 34.0f * Scale;
        const float BarW = CardW - 20.0f * Scale;
        DrawRect(Warm.CopyWithNewOpacity(0.14f), X + 10.0f * Scale, BarY,
            BarW, 4.0f * Scale);
        if (Group.UnitCount > 0)
        {
            DrawRect(Accent, X + 10.0f * Scale, BarY,
                BarW * FMath::Clamp(Group.MeanProgress, 0.0f, 1.0f),
                4.0f * Scale);
        }

        if (Small)
        {
            DrawText(FText::Format(
                    LOCTEXT("StateAndUnits",
                        "{State}  {Count} {Count}|plural(one=unit,"
                        "other=units)"),
                    FFormatNamedArguments{
                        { TEXT("State"), StateLabel(Group.State) },
                        { TEXT("Count"),
                          FText::AsNumber(Group.UnitCount) } }).ToString(),
                Accent, X + 10.0f * Scale, BarY + 10.0f * Scale, Small,
                Scale, false);

            if (Group.ThroughputPerHour > 0.0f)
            {
                DrawText(FText::Format(
                        LOCTEXT("ThroughputPerHour", "{0}/hr"),
                        FText::AsNumber(Group.ThroughputPerHour,
                            &RateFormat)).ToString(),
                    Warm, X + CardW - 62.0f * Scale, BarY + 10.0f * Scale,
                    Small, Scale, false);
            }
        }

        X += CardW;
        if (Index < Count - 1)
        {
            if (Large)
            {
                DrawText(TEXT(">"), CairnwellLit, X + Gap * 0.5f,
                    CardsY + CardH * 0.42f, Large, Scale, false);
            }
            X += Gap + ArrowW;
        }
    }
}

void ALBOneFactoryProductionHUD::DrawAlertToast(const float Width,
    const float Height, const float Scale, const TArray<FString>& Alerts)
{
    using namespace LBOneFactoryHUDPrivate;
    if (Alerts.Num() == 0)
    {
        return;
    }
    UFont* Small = GEngine ? GEngine->GetSmallFont() : nullptr;
    if (!Small)
    {
        return;
    }

    const float ToastW = 470.0f * Scale;
    const float ToastH = 34.0f * Scale;
    const float X = Width - ToastW - 20.0f * Scale;
    float Y = Height - 132.0f * Scale - 14.0f * Scale - ToastH;

    // Newest first, at most three, so a stalled line does not paper the screen.
    const int32 Shown = FMath::Min(Alerts.Num(), 3);
    for (int32 Index = 0; Index < Shown; ++Index)
    {
        DrawRect(CharcoalDeep.CopyWithNewOpacity(0.94f), X, Y, ToastW, ToastH);
        DrawRect(Yellow, X, Y, 3.0f * Scale, ToastH);
        DrawText(Alerts[Index].Left(78), Warm, X + 12.0f * Scale,
            Y + 9.0f * Scale, Small, Scale, false);
        Y -= ToastH + 6.0f * Scale;
    }
}

#undef LOCTEXT_NAMESPACE
