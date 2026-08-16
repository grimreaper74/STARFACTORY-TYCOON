#include "LBOneFactoryProductionHUD.h"

#include "Engine/Canvas.h"
#include "Engine/Engine.h"
#include "Engine/Font.h"
#include "EngineUtils.h"
#include "LBOneFactoryRuntimeCoordinator.h"

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
        const TCHAR* Label;
        ELBOneFactoryVehicleStage First;
        ELBOneFactoryVehicleStage Last;
    };
    const FGroupSpec GroupSpecs[] = {
        { TEXT("Coil intake"),     ELBOneFactoryVehicleStage::InboundCoil,
                                   ELBOneFactoryVehicleStage::BlankPreparation },
        { TEXT("Press"),           ELBOneFactoryVehicleStage::Pressing,
                                   ELBOneFactoryVehicleStage::Pressing },
        { TEXT("Panel stillages"), ELBOneFactoryVehicleStage::PressedPanelStillage,
                                   ELBOneFactoryVehicleStage::PressedPanelStillage },
        { TEXT("Body weld"),       ELBOneFactoryVehicleStage::BodyFraming,
                                   ELBOneFactoryVehicleStage::BodyQualityInspection },
        { TEXT("Paint"),           ELBOneFactoryVehicleStage::Pretreatment,
                                   ELBOneFactoryVehicleStage::PaintQualityInspection },
        { TEXT("Assembly"),        ELBOneFactoryVehicleStage::GeneralAssemblyTrim,
                                   ELBOneFactoryVehicleStage::EndOfLineInspection },
        { TEXT("Dispatch"),        ELBOneFactoryVehicleStage::FinishedVehicle,
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

    const TCHAR* StateLabel(const ELBOneFactoryGroupState State)
    {
        switch (State)
        {
        case ELBOneFactoryGroupState::Running: return TEXT("Running");
        case ELBOneFactoryGroupState::Waiting: return TEXT("Waiting");
        case ELBOneFactoryGroupState::Hold:    return TEXT("Hold");
        default:                               return TEXT("Idle");
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
        OutGroups[Index].Label = GroupSpecs[Index].Label;
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
            OutAlerts.Add(FString::Printf(
                TEXT("%s held at %s awaiting a quality result."),
                *Group.Label, *Status.CurrentStationId.ToString()));
        }
        else if (Status.NormalizedCycleProgress >= 0.999f)
        {
            if (Group.State != ELBOneFactoryGroupState::Hold)
            {
                Group.State = ELBOneFactoryGroupState::Waiting;
            }
            OutAlerts.Add(FString::Printf(
                TEXT("%s finished its cycle at %s and cannot move on."),
                *Group.Label, *Status.CurrentStationId.ToString()));
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
            DrawText(TEXT("MOORCROSS WORKS  -  no commissioned factory yet.  "
                          "Run LB.OneFactory.BuildWholeFactory"),
                Warm, 20.0f * Scale, 13.0f * Scale, Font, Scale, false);
        }
        return;
    }

    DrawTopBar(Width, Height, Scale, UnitsLive, Dispatched, Alerts);
    DrawFlowStrip(Width, Height, Scale, Groups);
    DrawAlertToast(Width, Height, Scale, Alerts);
}

void ALBOneFactoryProductionHUD::DrawTopBar(const float Width,
    const float Height, const float Scale, const int32 UnitsLive,
    const int32 Dispatched, const TArray<FString>& Alerts)
{
    using namespace LBOneFactoryHUDPrivate;
    UFont* Small = GEngine ? GEngine->GetSmallFont() : nullptr;
    UFont* Large = GEngine ? GEngine->GetLargeFont() : nullptr;

    const float BarH = 46.0f * Scale;
    DrawRect(CharcoalDeep.CopyWithNewOpacity(0.90f), 0.0f, 0.0f, Width, BarH);
    DrawRect(CairnwellLit.CopyWithNewOpacity(0.55f), 0.0f, BarH - 2.0f * Scale,
        Width, 2.0f * Scale);

    const float Pad = 18.0f * Scale;
    if (Large)
    {
        DrawText(TEXT("CAIRNWELL AUTOMOTIVE"), Warm, Pad, 8.0f * Scale,
            Large, Scale, false);
    }
    if (Small)
    {
        DrawText(TEXT("MOORCROSS WORKS"), Steel, Pad, 28.0f * Scale,
            Small, Scale, false);
    }

    // Right-aligned readouts. Each is a live figure, never a placeholder.
    float Cursor = Width - Pad;
    const float TimeScale = 1.0f;
    struct FReadout
    {
        FString Key;
        FString Value;
        FLinearColor Colour;
    };
    TArray<FReadout> Readouts;
    Readouts.Add({ TEXT("ALERTS"),
        FString::Printf(TEXT("%d"), Alerts.Num()),
        Alerts.Num() > 0 ? Yellow : Steel });
    Readouts.Add({ TEXT("DISPATCHED"),
        FString::Printf(TEXT("%d"), Dispatched), Warm });
    Readouts.Add({ TEXT("ON LINE"),
        FString::Printf(TEXT("%d"), UnitsLive), Warm });

    for (const FReadout& Readout : Readouts)
    {
        const float BlockW = 128.0f * Scale;
        Cursor -= BlockW;
        if (Small)
        {
            DrawText(Readout.Key, Steel, Cursor, 9.0f * Scale, Small,
                Scale, false);
        }
        if (Large)
        {
            DrawText(Readout.Value, Readout.Colour, Cursor, 24.0f * Scale,
                Large, Scale, false);
        }
    }
}

void ALBOneFactoryProductionHUD::DrawFlowStrip(const float Width,
    const float Height, const float Scale,
    const TArray<FLBOneFactoryProcessGroup>& Groups)
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
        DrawText(TEXT("PRODUCTION FLOW"), Steel, Pad, StripY + 8.0f * Scale,
            Small, Scale, false);
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
            DrawText(FString::Printf(TEXT("%d station%s%s"),
                    Group.StationCount, Group.StationCount == 1
                        ? TEXT("") : TEXT("s"),
                    Group.bHasQualityGate ? TEXT("  QA GATE") : TEXT("")),
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
            DrawText(FString::Printf(TEXT("%s  %d unit%s"),
                    StateLabel(Group.State), Group.UnitCount,
                    Group.UnitCount == 1 ? TEXT("") : TEXT("s")),
                Accent, X + 10.0f * Scale, BarY + 10.0f * Scale, Small,
                Scale, false);

            if (Group.ThroughputPerHour > 0.0f)
            {
                DrawText(FString::Printf(TEXT("%.1f/hr"),
                        Group.ThroughputPerHour),
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
