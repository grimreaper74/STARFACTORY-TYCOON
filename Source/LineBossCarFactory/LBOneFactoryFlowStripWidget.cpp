#include "LBOneFactoryFlowStripWidget.h"

#include "Blueprint/WidgetTree.h"
#include "Components/Border.h"
#include "Components/Button.h"
#include "Components/ButtonSlot.h"
#include "Components/HorizontalBox.h"
#include "Components/HorizontalBoxSlot.h"
#include "Components/ProgressBar.h"
#include "Components/Spacer.h"
#include "Components/TextBlock.h"
#include "Components/VerticalBox.h"
#include "Components/VerticalBoxSlot.h"
#include "LBManagementPawn.h"
#include "LBOneFactoryAlertCenterWidget.h"
#include "LBOneFactoryDetailPanelWidget.h"
#include "LBOneFactoryUITypes.h"

#define LOCTEXT_NAMESPACE "LineBossOneFactoryUI"

namespace LBOneFactoryFlowStripPrivate
{
    const FLinearColor StripBackground(0.031f, 0.037f, 0.042f, 0.92f);
    const FLinearColor CardIdle(0.055f, 0.065f, 0.075f, 1.0f);
    const FLinearColor CardActive(0.10f, 0.35f, 0.28f, 0.55f);
    const FLinearColor Warm(0.88f, 0.86f, 0.80f, 1.0f);
    const FLinearColor Steel(0.44f, 0.46f, 0.48f, 1.0f);
    const FLinearColor TrackDim(0.88f, 0.86f, 0.80f, 0.14f);

    UTextBlock* MakeText(UWidgetTree* Tree, const FName Name,
        const FText& Value, const float Size, const FLinearColor& Colour)
    {
        UTextBlock* Text = Tree->ConstructWidget<UTextBlock>(
            UTextBlock::StaticClass(), Name);
        Text->SetText(Value);
        FSlateFontInfo Font = Text->GetFont();
        Font.Size = Size;
        Text->SetFont(Font);
        Text->SetColorAndOpacity(FSlateColor(Colour));
        return Text;
    }

    /** Group state to the shared status token (UI rule 1: one status model). */
    FLBOneFactoryStatusToken TokenForGroup(const ELBOneFactoryGroupState State)
    {
        switch (State)
        {
        case ELBOneFactoryGroupState::Running:
            return ULBOneFactoryUITokens::TokenForStatus(
                ELBOneFactoryStationStatus::Working);
        case ELBOneFactoryGroupState::Waiting:
            return ULBOneFactoryUITokens::TokenForStatus(
                ELBOneFactoryStationStatus::Blocked);
        case ELBOneFactoryGroupState::Hold:
            return ULBOneFactoryUITokens::TokenForStatus(
                ELBOneFactoryStationStatus::QualityHold);
        default:
            return ULBOneFactoryUITokens::TokenForStatus(
                ELBOneFactoryStationStatus::Offline);
        }
    }

    /** Shape per status so colour is never the only encoding (UI rule 4).
        An idle group gets a hollow circle: no work, not a fault. */
    FText GlyphForGroup(const ELBOneFactoryGroupState State)
    {
        switch (State)
        {
        case ELBOneFactoryGroupState::Running:
            return FText::FromString(TEXT("●")); // filled circle
        case ELBOneFactoryGroupState::Waiting:
            return FText::FromString(TEXT("■")); // square
        case ELBOneFactoryGroupState::Hold:
            return FText::FromString(TEXT("◆")); // diamond
        default:
            return FText::FromString(TEXT("○")); // hollow circle
        }
    }

    FText LabelForGroup(const ELBOneFactoryGroupState State)
    {
        switch (State)
        {
        case ELBOneFactoryGroupState::Running:
            return LOCTEXT("GroupRunning", "Running");
        case ELBOneFactoryGroupState::Waiting:
            return LOCTEXT("GroupBlocked", "Blocked");
        case ELBOneFactoryGroupState::Hold:
            return LOCTEXT("GroupQualityHold", "Quality hold");
        default:
            return LOCTEXT("GroupIdle", "Idle");
        }
    }

    /** Measured rate is recorded per department, so it is only honest on the
        card that heads that department (UI rule 6: honest numbers). */
    bool GroupShowsMeasuredRate(const int32 Index)
    {
        return Index == 1 || Index == 3 || Index == 4 || Index == 5;
    }
}

TSharedRef<SWidget> ULBOneFactoryFlowStripWidget::RebuildWidget()
{
    // The tree must exist before Slate takes it; NativeConstruct is too
    // late for widgets created without a Blueprint asset.
    BuildTree();
    return Super::RebuildWidget();
}

void ULBOneFactoryFlowStripWidget::NativeConstruct()
{
    Super::NativeConstruct();
    // The widget spans the viewport; only the strip's own cards take hits.
    SetVisibility(ESlateVisibility::SelfHitTestInvisible);
    Refresh();
}

void ULBOneFactoryFlowStripWidget::BuildTree()
{
    using namespace LBOneFactoryFlowStripPrivate;
    if (!WidgetTree || WidgetTree->RootWidget)
    {
        return;
    }
    // Root is a vertical box whose filler pushes the auto-sized strip to the
    // bottom edge; everything above it stays untouched and click-through.
    UVerticalBox* RootBox = WidgetTree->ConstructWidget<UVerticalBox>(
        UVerticalBox::StaticClass(), TEXT("FlowRootBox"));
    WidgetTree->RootWidget = RootBox;

    USpacer* Filler = WidgetTree->ConstructWidget<USpacer>(
        USpacer::StaticClass(), TEXT("FlowFiller"));
    if (UVerticalBoxSlot* FillSlot = RootBox->AddChildToVerticalBox(Filler))
    {
        FillSlot->SetSize(FSlateChildSize(ESlateSizeRule::Fill));
    }

    // Onboarding hint: one quiet line naming the controls, shown for the
    // first sim-minutes of a session and never again after.
    UHorizontalBox* HintRow = WidgetTree->ConstructWidget<UHorizontalBox>(
        UHorizontalBox::StaticClass(), TEXT("FlowHintRow"));
    RootBox->AddChildToVerticalBox(HintRow);
    USpacer* HintLeft = WidgetTree->ConstructWidget<USpacer>(
        USpacer::StaticClass(), TEXT("FlowHintLeft"));
    if (UHorizontalBoxSlot* HintLeftSlot =
            HintRow->AddChildToHorizontalBox(HintLeft))
    {
        HintLeftSlot->SetSize(FSlateChildSize(ESlateSizeRule::Fill));
    }
    HintBorder = WidgetTree->ConstructWidget<UBorder>(
        UBorder::StaticClass(), TEXT("FlowHint"));
    HintBorder->SetBrushColor(StripBackground);
    HintBorder->SetPadding(FMargin(14.0f, 5.0f));
    HintBorder->SetVisibility(ESlateVisibility::Collapsed);
    HintBorder->SetContent(MakeText(WidgetTree, TEXT("FlowHintText"),
        LOCTEXT("OnboardingHint",
            "Space pauses  ·  1/2/3 set the speed  ·  click a card or "
            "press F1-F4 to visit a shop  ·  N places an order  ·  "
            "Shift+F5-F8 saves a view, F5-F8 returns"),
        11.0f, Steel));
    HintRow->AddChildToHorizontalBox(HintBorder);
    USpacer* HintRight = WidgetTree->ConstructWidget<USpacer>(
        USpacer::StaticClass(), TEXT("FlowHintRight"));
    if (UHorizontalBoxSlot* HintRightSlot =
            HintRow->AddChildToHorizontalBox(HintRight))
    {
        HintRightSlot->SetSize(FSlateChildSize(ESlateSizeRule::Fill));
    }

    StripBorder = WidgetTree->ConstructWidget<UBorder>(
        UBorder::StaticClass(), TEXT("FlowStrip"));
    StripBorder->SetBrushColor(StripBackground);
    StripBorder->SetPadding(FMargin(14.0f, 6.0f, 14.0f, 8.0f));
    // Hidden until the first successful collection so an uncommissioned
    // world shows no empty chrome.
    StripBorder->SetVisibility(ESlateVisibility::Collapsed);
    if (UVerticalBoxSlot* StripSlot = RootBox->AddChildToVerticalBox(
            StripBorder))
    {
        StripSlot->SetHorizontalAlignment(HAlign_Fill);
        StripSlot->SetSize(FSlateChildSize(ESlateSizeRule::Automatic));
    }

    UVerticalBox* StripBox = WidgetTree->ConstructWidget<UVerticalBox>(
        UVerticalBox::StaticClass(), TEXT("FlowStripBox"));
    StripBorder->SetContent(StripBox);

    UHorizontalBox* Header = WidgetTree->ConstructWidget<UHorizontalBox>(
        UHorizontalBox::StaticClass(), TEXT("FlowHeader"));
    StripBox->AddChildToVerticalBox(Header);
    Header->AddChildToHorizontalBox(MakeText(WidgetTree,
        TEXT("FlowTitle"), LOCTEXT("FlowTitle", "PRODUCTION FLOW"), 10.0f,
        Steel));
    USpacer* HeaderGap = WidgetTree->ConstructWidget<USpacer>(
        USpacer::StaticClass(), TEXT("FlowHeaderGap"));
    if (UHorizontalBoxSlot* GapSlot = Header->AddChildToHorizontalBox(
            HeaderGap))
    {
        GapSlot->SetSize(FSlateChildSize(ESlateSizeRule::Fill));
    }
    SummaryText = MakeText(WidgetTree, TEXT("FlowSummary"),
        FText::GetEmpty(), 10.0f, Steel);
    Header->AddChildToHorizontalBox(SummaryText);

    CardsRow = WidgetTree->ConstructWidget<UHorizontalBox>(
        UHorizontalBox::StaticClass(), TEXT("FlowCards"));
    if (UVerticalBoxSlot* CardsSlot = StripBox->AddChildToVerticalBox(
            CardsRow))
    {
        CardsSlot->SetPadding(FMargin(0.0f, 6.0f, 0.0f, 0.0f));
    }
}

void ULBOneFactoryFlowStripWidget::EnsureCards(const int32 Count)
{
    using namespace LBOneFactoryFlowStripPrivate;
    static const FName Handlers[MaxCards] = {
        TEXT("OnCard0Clicked"), TEXT("OnCard1Clicked"),
        TEXT("OnCard2Clicked"), TEXT("OnCard3Clicked"),
        TEXT("OnCard4Clicked"), TEXT("OnCard5Clicked"),
        TEXT("OnCard6Clicked") };
    if (CardButtons.Num() == 0)
    {
        // Rounded faces per the target mockup; the selected state carries
        // an emerald outline instead of a fill change.
        auto MakeFace = [](const FLinearColor& Outline, const float Width)
        {
            FSlateBrush Brush;
            Brush.DrawAs = ESlateBrushDrawType::RoundedBox;
            Brush.TintColor = FLinearColor::White;
            Brush.OutlineSettings = FSlateBrushOutlineSettings(
                FVector4(4.0f, 4.0f, 4.0f, 4.0f), Outline, Width);
            return Brush;
        };
        const FSlateBrush Face = MakeFace(
            FLinearColor(0.10f, 0.12f, 0.13f, 1.0f), 1.0f);
        CardStyle.SetNormal(Face);
        CardStyle.SetHovered(MakeFace(
            FLinearColor(0.16f, 0.35f, 0.29f, 1.0f), 1.0f));
        CardStyle.SetPressed(Face);
        const FSlateBrush Selected = MakeFace(
            FLinearColor(0.15f, 0.75f, 0.55f, 1.0f), 1.6f);
        SelectedCardStyle.SetNormal(Selected);
        SelectedCardStyle.SetHovered(Selected);
        SelectedCardStyle.SetPressed(Selected);
    }
    const int32 Wanted = FMath::Min(Count, MaxCards);
    for (int32 Index = CardButtons.Num(); Index < Wanted; ++Index)
    {
        UButton* Button = WidgetTree->ConstructWidget<UButton>(
            UButton::StaticClass(),
            FName(*FString::Printf(TEXT("FlowCard%d"), Index)));
        Button->SetStyle(CardStyle);
        Button->SetBackgroundColor(CardIdle);
        FScriptDelegate Delegate;
        Delegate.BindUFunction(this, Handlers[Index]);
        Button->OnClicked.Add(Delegate);

        UVerticalBox* Body = WidgetTree->ConstructWidget<UVerticalBox>(
            UVerticalBox::StaticClass(),
            FName(*FString::Printf(TEXT("FlowCard%dBody"), Index)));
        Button->AddChild(Body);
        if (UButtonSlot* BodySlot = Cast<UButtonSlot>(Body->Slot))
        {
            BodySlot->SetPadding(FMargin(10.0f, 6.0f));
            BodySlot->SetHorizontalAlignment(HAlign_Fill);
            BodySlot->SetVerticalAlignment(VAlign_Fill);
        }

        // Title row: name left, the station count big on the right
        // (target mockup layout).
        UHorizontalBox* TitleRow =
            WidgetTree->ConstructWidget<UHorizontalBox>(
                UHorizontalBox::StaticClass(),
                FName(*FString::Printf(TEXT("FlowCard%dTitle"), Index)));
        Body->AddChildToVerticalBox(TitleRow);
        UTextBlock* Name = MakeText(WidgetTree,
            FName(*FString::Printf(TEXT("FlowCard%dName"), Index)),
            FText::GetEmpty(), 13.0f, Warm);
        TitleRow->AddChildToHorizontalBox(Name);
        USpacer* TitleGap = WidgetTree->ConstructWidget<USpacer>(
            USpacer::StaticClass(),
            FName(*FString::Printf(TEXT("FlowCard%dTitleGap"), Index)));
        if (UHorizontalBoxSlot* TitleGapSlot =
                TitleRow->AddChildToHorizontalBox(TitleGap))
        {
            TitleGapSlot->SetSize(FSlateChildSize(ESlateSizeRule::Fill));
        }
        UTextBlock* CountText = MakeText(WidgetTree,
            FName(*FString::Printf(TEXT("FlowCard%dCount"), Index)),
            FText::GetEmpty(), 15.0f, Steel);
        TitleRow->AddChildToHorizontalBox(CountText);

        UProgressBar* Progress = WidgetTree->ConstructWidget<UProgressBar>(
            UProgressBar::StaticClass(),
            FName(*FString::Printf(TEXT("FlowCard%dProgress"), Index)));
        Progress->SetPercent(0.0f);
        if (UVerticalBoxSlot* ProgressSlot = Body->AddChildToVerticalBox(
                Progress))
        {
            ProgressSlot->SetPadding(FMargin(0.0f, 5.0f, 0.0f, 3.0f));
        }

        // Status then the rate, both centred (target mockup layout).
        UTextBlock* Status = MakeText(WidgetTree,
            FName(*FString::Printf(TEXT("FlowCard%dStatus"), Index)),
            FText::GetEmpty(), 11.0f, Warm);
        if (UVerticalBoxSlot* StatusSlot =
                Body->AddChildToVerticalBox(Status))
        {
            StatusSlot->SetHorizontalAlignment(HAlign_Center);
        }
        UTextBlock* Rate = MakeText(WidgetTree,
            FName(*FString::Printf(TEXT("FlowCard%dRate"), Index)),
            FText::GetEmpty(), 10.0f, Steel);
        if (UVerticalBoxSlot* RateSlot = Body->AddChildToVerticalBox(Rate))
        {
            RateSlot->SetPadding(FMargin(0.0f, 2.0f, 0.0f, 0.0f));
            RateSlot->SetHorizontalAlignment(HAlign_Center);
        }

        if (UHorizontalBoxSlot* CardSlot = CardsRow->AddChildToHorizontalBox(
                Button))
        {
            CardSlot->SetSize(FSlateChildSize(ESlateSizeRule::Fill));
            CardSlot->SetPadding(
                FMargin(Index > 0 ? 6.0f : 0.0f, 0.0f, 0.0f, 0.0f));
            CardSlot->SetVerticalAlignment(VAlign_Fill);
        }

        CardButtons.Add(Button);
        CardNames.Add(Name);
        CardCounts.Add(CountText);
        CardProgress.Add(Progress);
        CardStatus.Add(Status);
        CardRate.Add(Rate);
    }
}

void ULBOneFactoryFlowStripWidget::NativeTick(const FGeometry& MyGeometry,
    const float InDeltaTime)
{
    Super::NativeTick(MyGeometry, InDeltaTime);
    RefreshAccumulator += InDeltaTime;
    if (RefreshAccumulator >= 0.25f)
    {
        RefreshAccumulator = 0.0f;
        Refresh();
    }
}

void ULBOneFactoryFlowStripWidget::Refresh()
{
    using namespace LBOneFactoryFlowStripPrivate;
    TArray<FLBOneFactoryProcessGroup> Groups;
    TArray<FLBOneFactoryLiveAlert> Alerts;
    int32 UnitsLive = 0;
    int32 Dispatched = 0;
    if (!ALBOneFactoryProductionHUD::CollectGroups(GetWorld(), Groups,
            UnitsLive, Dispatched, Alerts)
        || Groups.Num() == 0)
    {
        if (StripBorder)
        {
            StripBorder->SetVisibility(ESlateVisibility::Collapsed);
        }
        return;
    }
    CachedGroups = Groups;

    // v2.1 bottleneck highlight: with units in flow, the department with
    // the lowest authored capacity is the structural constraint - its
    // card says so rather than making the player compare rate lines.
    int32 BottleneckIndex = INDEX_NONE;
    if (UnitsLive > 0)
    {
        float LowestCapacity = TNumericLimits<float>::Max();
        for (int32 Index = 0; Index < Groups.Num(); ++Index)
        {
            const FLBOneFactoryProcessGroup& Group = Groups[Index];
            if (Group.bHasDepartment && Group.ThroughputPerHour > 0.0f
                && Group.ThroughputPerHour < LowestCapacity)
            {
                LowestCapacity = Group.ThroughputPerHour;
                BottleneckIndex = Index;
            }
        }
    }
    EnsureCards(Groups.Num());
    if (StripBorder)
    {
        StripBorder->SetVisibility(ESlateVisibility::Visible);
    }

    // The control hint accompanies the first quarter sim-hour, then leaves
    // for good; it is a whisper, not a tutorial.
    if (HintBorder)
    {
        FLBOneFactoryManagementBand Band;
        const bool bShowHint =
            ALBOneFactoryProductionHUD::CollectManagement(GetWorld(), Band)
            && Band.SimClockSeconds < 900.0;
        HintBorder->SetVisibility(bShowHint
            ? ESlateVisibility::HitTestInvisible
            : ESlateVisibility::Collapsed);
    }

    if (SummaryText)
    {
        SummaryText->SetText(FText::Format(
            LOCTEXT("FlowSummaryLine",
                "ON LINE {0}   DISPATCHED {1}   ALERTS {2}"),
            FText::AsNumber(UnitsLive), FText::AsNumber(Dispatched),
            FText::AsNumber(Alerts.Num())));
        SummaryText->SetColorAndOpacity(FSlateColor(Alerts.Num() > 0
            ? ULBOneFactoryUITokens::TokenForStatus(
                ELBOneFactoryStationStatus::Starved).Colour
            : Steel));
    }

    FNumberFormattingOptions RateFormat;
    RateFormat.MaximumFractionalDigits = 1;
    for (int32 Index = 0;
        Index < CardButtons.Num() && Index < Groups.Num(); ++Index)
    {
        const FLBOneFactoryProcessGroup& Group = Groups[Index];
        const FLBOneFactoryStatusToken Token = TokenForGroup(Group.State);

        const bool bSelected = DetailPanel
            && DetailPanel->GetShownGroupIndex() == Index;
        CardButtons[Index]->SetStyle(
            bSelected ? SelectedCardStyle : CardStyle);
        CardButtons[Index]->SetBackgroundColor(
            Group.UnitCount > 0 ? CardActive : CardIdle);
        CardNames[Index]->SetText(FText::FromString(Group.Label));
        CardCounts[Index]->SetText(FText::AsNumber(Group.StationCount));

        CardProgress[Index]->SetPercent(
            FMath::Clamp(Group.MeanProgress, 0.0f, 1.0f));
        CardProgress[Index]->SetFillColorAndOpacity(Token.Colour);

        CardStatus[Index]->SetText(FText::Format(
            LOCTEXT("CardStatus",
                "{0} {1}  ·  {2} {2}|plural(one=unit,other=units)"),
            GlyphForGroup(Group.State), LabelForGroup(Group.State),
            FText::AsNumber(Group.UnitCount)));
        CardStatus[Index]->SetColorAndOpacity(FSlateColor(
            Group.State == ELBOneFactoryGroupState::Idle
                ? Steel : Token.Colour));

        // Measured cars/hour where the department records one; the route's
        // bottleneck capacity everywhere, so expectations stay anchored.
        if (GroupShowsMeasuredRate(Index) && Group.bHasDepartment)
        {
            CardRate[Index]->SetText(Index == BottleneckIndex
                ? FText::Format(
                    LOCTEXT("CardRateBottleneck",
                        "{0}/hr  ·  cap {1}/hr  ·  bottleneck"),
                    FText::AsNumber(Group.MeasuredRatePerHour, &RateFormat),
                    FText::AsNumber(Group.ThroughputPerHour, &RateFormat))
                : FText::Format(
                    LOCTEXT("CardRateMeasured", "{0}/hr  ·  cap {1}/hr"),
                    FText::AsNumber(Group.MeasuredRatePerHour, &RateFormat),
                    FText::AsNumber(Group.ThroughputPerHour, &RateFormat)));
        }
        else if (Group.ThroughputPerHour > 0.0f)
        {
            CardRate[Index]->SetText(FText::Format(
                LOCTEXT("CardRateCapacity", "cap {0}/hr"),
                FText::AsNumber(Group.ThroughputPerHour, &RateFormat)));
        }
        else
        {
            CardRate[Index]->SetText(FText::GetEmpty());
        }

        // v2.1 tooltip: the card's numbers in one hover, plus the click
        // affordance - stations, live units, measured vs capacity rate
        // and mean cycle progress.
        CardButtons[Index]->SetToolTipText(FText::Format(
            LOCTEXT("CardTooltip",
                "{0}\n{1} {1}|plural(one=station,other=stations){2}\n"
                "{3} {3}|plural(one=unit,other=units) in this group\n"
                "Measured {4}/hr of {5}/hr capacity\n"
                "Mean cycle progress {6}%\n"
                "Click to open the detail panel"),
            FText::FromString(Group.Label.ToUpper()),
            FText::AsNumber(Group.StationCount),
            Group.bHasQualityGate
                ? LOCTEXT("CardTooltipGate", " (includes a quality gate)")
                : FText::GetEmpty(),
            FText::AsNumber(Group.UnitCount),
            FText::AsNumber(Group.MeasuredRatePerHour, &RateFormat),
            FText::AsNumber(Group.ThroughputPerHour, &RateFormat),
            FText::AsNumber(FMath::RoundToInt(
                FMath::Clamp(Group.MeanProgress, 0.0f, 1.0f) * 100.0f))));
        CardRate[Index]->SetColorAndOpacity(FSlateColor(Steel));
    }
}

bool ULBOneFactoryFlowStripWidget::FocusGroup(const int32 Index)
{
    if (!CachedGroups.IsValidIndex(Index)
        || !CachedGroups[Index].WorldBounds.IsValid)
    {
        return false;
    }
    APlayerController* Controller = GetOwningPlayer();
    ALBManagementPawn* Pawn = Controller
        ? Cast<ALBManagementPawn>(Controller->GetPawn()) : nullptr;
    if (!Pawn)
    {
        return false;
    }
    const FBox& Bounds = CachedGroups[Index].WorldBounds;
    const FVector Size = Bounds.GetSize();
    // Frame the group's long axis with margin; keep the player's yaw so the
    // jump never spins the world underneath them.
    const float Zoom = FMath::Clamp(
        FMath::Max(Size.X, Size.Y) * 1.25f + 3000.0f, 4200.0f, 45000.0f);
    const bool bFramed = Pawn->SetAutomationCamera(Bounds.GetCenter(),
        Pawn->GetActorRotation().Yaw, Zoom);
    if (bFramed)
    {
        if (AlertCenter)
        {
            AlertCenter->HideInbox();
        }
        if (DetailPanel)
        {
            DetailPanel->ShowGroup(Index);
        }
    }
    return bFramed;
}

void ULBOneFactoryFlowStripWidget::OnCard0Clicked() { FocusGroup(0); }
void ULBOneFactoryFlowStripWidget::OnCard1Clicked() { FocusGroup(1); }
void ULBOneFactoryFlowStripWidget::OnCard2Clicked() { FocusGroup(2); }
void ULBOneFactoryFlowStripWidget::OnCard3Clicked() { FocusGroup(3); }
void ULBOneFactoryFlowStripWidget::OnCard4Clicked() { FocusGroup(4); }
void ULBOneFactoryFlowStripWidget::OnCard5Clicked() { FocusGroup(5); }
void ULBOneFactoryFlowStripWidget::OnCard6Clicked() { FocusGroup(6); }

#undef LOCTEXT_NAMESPACE
