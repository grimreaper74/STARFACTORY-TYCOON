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
    const int32 Wanted = FMath::Min(Count, MaxCards);
    for (int32 Index = CardButtons.Num(); Index < Wanted; ++Index)
    {
        UButton* Button = WidgetTree->ConstructWidget<UButton>(
            UButton::StaticClass(),
            FName(*FString::Printf(TEXT("FlowCard%d"), Index)));
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

        UTextBlock* Name = MakeText(WidgetTree,
            FName(*FString::Printf(TEXT("FlowCard%dName"), Index)),
            FText::GetEmpty(), 13.0f, Warm);
        Body->AddChildToVerticalBox(Name);
        UTextBlock* Meta = MakeText(WidgetTree,
            FName(*FString::Printf(TEXT("FlowCard%dMeta"), Index)),
            FText::GetEmpty(), 10.0f, Steel);
        Body->AddChildToVerticalBox(Meta);

        UProgressBar* Progress = WidgetTree->ConstructWidget<UProgressBar>(
            UProgressBar::StaticClass(),
            FName(*FString::Printf(TEXT("FlowCard%dProgress"), Index)));
        Progress->SetPercent(0.0f);
        if (UVerticalBoxSlot* ProgressSlot = Body->AddChildToVerticalBox(
                Progress))
        {
            ProgressSlot->SetPadding(FMargin(0.0f, 5.0f, 0.0f, 3.0f));
        }

        // Status and rate stack; sharing a row crowds the narrow cards.
        UTextBlock* Status = MakeText(WidgetTree,
            FName(*FString::Printf(TEXT("FlowCard%dStatus"), Index)),
            FText::GetEmpty(), 11.0f, Warm);
        Body->AddChildToVerticalBox(Status);
        UTextBlock* Rate = MakeText(WidgetTree,
            FName(*FString::Printf(TEXT("FlowCard%dRate"), Index)),
            FText::GetEmpty(), 10.0f, Steel);
        if (UVerticalBoxSlot* RateSlot = Body->AddChildToVerticalBox(Rate))
        {
            RateSlot->SetPadding(FMargin(0.0f, 2.0f, 0.0f, 0.0f));
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
        CardMeta.Add(Meta);
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
    EnsureCards(Groups.Num());
    if (StripBorder)
    {
        StripBorder->SetVisibility(ESlateVisibility::Visible);
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

        CardButtons[Index]->SetBackgroundColor(
            Group.UnitCount > 0 ? CardActive : CardIdle);
        CardNames[Index]->SetText(FText::FromString(Group.Label));
        CardMeta[Index]->SetText(FText::Format(
            LOCTEXT("CardMeta",
                "{0} {0}|plural(one=station,other=stations){1}"),
            FText::AsNumber(Group.StationCount),
            Group.bHasQualityGate
                ? LOCTEXT("CardQualityGate", "  ·  QA gate")
                : FText::GetEmpty()));

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
            CardRate[Index]->SetText(FText::Format(
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
