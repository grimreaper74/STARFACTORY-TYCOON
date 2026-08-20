#include "LBOneFactoryAlertCenterWidget.h"

#include "Blueprint/WidgetTree.h"
#include "Components/Border.h"
#include "Components/Button.h"
#include "Components/ButtonSlot.h"
#include "Components/HorizontalBox.h"
#include "Components/HorizontalBoxSlot.h"
#include "Components/Spacer.h"
#include "Components/TextBlock.h"
#include "Components/VerticalBox.h"
#include "Components/VerticalBoxSlot.h"
#include "LBOneFactoryDetailPanelWidget.h"
#include "LBOneFactoryFlowStripWidget.h"
#include "LBOneFactoryUITypes.h"

#define LOCTEXT_NAMESPACE "LineBossOneFactoryUI"

namespace LBOneFactoryAlertCenterPrivate
{
    const FLinearColor PanelBackground(0.031f, 0.037f, 0.042f, 0.94f);
    const FLinearColor RowBackground(0.055f, 0.065f, 0.075f, 1.0f);
    const FLinearColor Warm(0.88f, 0.86f, 0.80f, 1.0f);
    const FLinearColor Steel(0.44f, 0.46f, 0.48f, 1.0f);

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

    FText GlyphForStatus(const ELBOneFactoryStationStatus Status)
    {
        switch (ULBOneFactoryUITokens::TokenForStatus(Status).Glyph)
        {
        case ELBOneFactoryStatusGlyph::CircleFilled:
            return FText::FromString(TEXT("●"));
        case ELBOneFactoryStatusGlyph::Triangle:
            return FText::FromString(TEXT("▲"));
        case ELBOneFactoryStatusGlyph::Square:
            return FText::FromString(TEXT("■"));
        case ELBOneFactoryStatusGlyph::Diamond:
            return FText::FromString(TEXT("◆"));
        default:
            return FText::FromString(TEXT("○"));
        }
    }
}

TSharedRef<SWidget> ULBOneFactoryAlertCenterWidget::RebuildWidget()
{
    // The tree must exist before Slate takes it; NativeConstruct is too
    // late for widgets created without a Blueprint asset.
    BuildTree();
    return Super::RebuildWidget();
}

void ULBOneFactoryAlertCenterWidget::NativeConstruct()
{
    Super::NativeConstruct();
    // The widget spans the viewport; only its own surfaces take hits.
    SetVisibility(ESlateVisibility::SelfHitTestInvisible);
}

void ULBOneFactoryAlertCenterWidget::BuildTree()
{
    using namespace LBOneFactoryAlertCenterPrivate;
    if (!WidgetTree || WidgetTree->RootWidget)
    {
        return;
    }
    UVerticalBox* RootBox = WidgetTree->ConstructWidget<UVerticalBox>(
        UVerticalBox::StaticClass(), TEXT("AlertRootBox"));
    WidgetTree->RootWidget = RootBox;

    USpacer* TopClearance = WidgetTree->ConstructWidget<USpacer>(
        USpacer::StaticClass(), TEXT("AlertTopClearance"));
    TopClearance->SetSize(FVector2D(1.0f, 44.0f));
    RootBox->AddChildToVerticalBox(TopClearance);

    // Toast banner: centred, only for toast-severity conditions, only while
    // the inbox is closed (the inbox supersedes it).
    UHorizontalBox* ToastRow = WidgetTree->ConstructWidget<UHorizontalBox>(
        UHorizontalBox::StaticClass(), TEXT("AlertToastRow"));
    RootBox->AddChildToVerticalBox(ToastRow);
    USpacer* ToastLeft = WidgetTree->ConstructWidget<USpacer>(
        USpacer::StaticClass(), TEXT("AlertToastLeft"));
    if (UHorizontalBoxSlot* LeftSlot = ToastRow->AddChildToHorizontalBox(
            ToastLeft))
    {
        LeftSlot->SetSize(FSlateChildSize(ESlateSizeRule::Fill));
    }
    ToastBorder = WidgetTree->ConstructWidget<UBorder>(
        UBorder::StaticClass(), TEXT("AlertToast"));
    ToastBorder->SetBrushColor(PanelBackground);
    ToastBorder->SetPadding(FMargin(16.0f, 7.0f));
    ToastBorder->SetVisibility(ESlateVisibility::Collapsed);
    ToastRow->AddChildToHorizontalBox(ToastBorder);
    ToastText = MakeText(WidgetTree, TEXT("AlertToastText"),
        FText::GetEmpty(), 12.0f, Warm);
    ToastBorder->SetContent(ToastText);
    USpacer* ToastRight = WidgetTree->ConstructWidget<USpacer>(
        USpacer::StaticClass(), TEXT("AlertToastRight"));
    if (UHorizontalBoxSlot* RightSlot = ToastRow->AddChildToHorizontalBox(
            ToastRight))
    {
        RightSlot->SetSize(FSlateChildSize(ESlateSizeRule::Fill));
    }

    // Inbox: pinned to the right edge under the bell.
    UHorizontalBox* InboxRow = WidgetTree->ConstructWidget<UHorizontalBox>(
        UHorizontalBox::StaticClass(), TEXT("AlertInboxRow"));
    if (UVerticalBoxSlot* InboxRowSlot = RootBox->AddChildToVerticalBox(
            InboxRow))
    {
        InboxRowSlot->SetPadding(FMargin(0.0f, 4.0f, 0.0f, 0.0f));
    }
    USpacer* InboxLeft = WidgetTree->ConstructWidget<USpacer>(
        USpacer::StaticClass(), TEXT("AlertInboxLeft"));
    if (UHorizontalBoxSlot* InboxLeftSlot =
            InboxRow->AddChildToHorizontalBox(InboxLeft))
    {
        InboxLeftSlot->SetSize(FSlateChildSize(ESlateSizeRule::Fill));
    }
    InboxBorder = WidgetTree->ConstructWidget<UBorder>(
        UBorder::StaticClass(), TEXT("AlertInbox"));
    InboxBorder->SetBrushColor(PanelBackground);
    InboxBorder->SetPadding(FMargin(12.0f, 8.0f, 12.0f, 10.0f));
    InboxBorder->SetVisibility(ESlateVisibility::Collapsed);
    if (UHorizontalBoxSlot* InboxSlot = InboxRow->AddChildToHorizontalBox(
            InboxBorder))
    {
        InboxSlot->SetPadding(FMargin(0.0f, 0.0f, 10.0f, 0.0f));
    }

    UVerticalBox* InboxBody = WidgetTree->ConstructWidget<UVerticalBox>(
        UVerticalBox::StaticClass(), TEXT("AlertInboxBody"));
    InboxBorder->SetContent(InboxBody);
    InboxTitle = MakeText(WidgetTree, TEXT("AlertInboxTitle"),
        LOCTEXT("InboxTitle", "ALERTS"), 12.0f, Warm);
    InboxBody->AddChildToVerticalBox(InboxTitle);
    EmptyText = MakeText(WidgetTree, TEXT("AlertInboxEmpty"),
        LOCTEXT("InboxEmpty", "No alerts. The plant is quiet."), 11.0f,
        Steel);
    if (UVerticalBoxSlot* EmptySlot = InboxBody->AddChildToVerticalBox(
            EmptyText))
    {
        EmptySlot->SetPadding(FMargin(0.0f, 6.0f, 0.0f, 0.0f));
    }

    static const FName Handlers[MaxRows] = {
        TEXT("OnRow0Clicked"), TEXT("OnRow1Clicked"), TEXT("OnRow2Clicked"),
        TEXT("OnRow3Clicked"), TEXT("OnRow4Clicked"), TEXT("OnRow5Clicked"),
        TEXT("OnRow6Clicked"), TEXT("OnRow7Clicked") };
    for (int32 Index = 0; Index < MaxRows; ++Index)
    {
        UButton* Row = WidgetTree->ConstructWidget<UButton>(
            UButton::StaticClass(),
            FName(*FString::Printf(TEXT("AlertRow%d"), Index)));
        Row->SetBackgroundColor(RowBackground);
        Row->SetVisibility(ESlateVisibility::Collapsed);
        FScriptDelegate Delegate;
        Delegate.BindUFunction(this, Handlers[Index]);
        Row->OnClicked.Add(Delegate);
        UTextBlock* Text = MakeText(WidgetTree,
            FName(*FString::Printf(TEXT("AlertRow%dText"), Index)),
            FText::GetEmpty(), 11.0f, Warm);
        Text->SetAutoWrapText(true);
        Row->AddChild(Text);
        if (UButtonSlot* TextSlot = Cast<UButtonSlot>(Text->Slot))
        {
            TextSlot->SetPadding(FMargin(8.0f, 4.0f));
            TextSlot->SetHorizontalAlignment(HAlign_Left);
        }
        if (UVerticalBoxSlot* RowSlot = InboxBody->AddChildToVerticalBox(
                Row))
        {
            RowSlot->SetPadding(FMargin(0.0f, 4.0f, 0.0f, 0.0f));
            RowSlot->SetHorizontalAlignment(HAlign_Fill);
        }
        RowButtons.Add(Row);
        RowTexts.Add(Text);
    }
}

void ULBOneFactoryAlertCenterWidget::NativeTick(const FGeometry& MyGeometry,
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

void ULBOneFactoryAlertCenterWidget::ToggleInbox()
{
    bInboxOpen = !bInboxOpen;
    if (InboxBorder)
    {
        InboxBorder->SetVisibility(bInboxOpen
            ? ESlateVisibility::Visible : ESlateVisibility::Collapsed);
    }
    if (bInboxOpen)
    {
        if (DetailPanel)
        {
            DetailPanel->Hide();
        }
        Refresh();
    }
}

void ULBOneFactoryAlertCenterWidget::HideInbox()
{
    if (bInboxOpen)
    {
        ToggleInbox();
    }
}

void ULBOneFactoryAlertCenterWidget::Refresh()
{
    using namespace LBOneFactoryAlertCenterPrivate;
    TArray<FLBOneFactoryProcessGroup> Groups;
    TArray<FLBOneFactoryLiveAlert> Alerts;
    int32 UnitsLive = 0;
    int32 Dispatched = 0;
    const bool bCollected = ALBOneFactoryProductionHUD::CollectGroups(
        GetWorld(), Groups, UnitsLive, Dispatched, Alerts);

    // Toast: the first toast-severity condition, only while the inbox is
    // closed. Stateful - it vanishes the moment the condition resolves.
    const FLBOneFactoryLiveAlert* Toast = nullptr;
    if (bCollected && !bInboxOpen)
    {
        for (const FLBOneFactoryLiveAlert& Alert : Alerts)
        {
            if (ULBOneFactoryUITokens::TokenForStatus(Alert.Status).Severity
                == ELBOneFactoryAlertSeverity::Toast)
            {
                Toast = &Alert;
                break;
            }
        }
    }
    if (ToastBorder)
    {
        ToastBorder->SetVisibility(Toast
            ? ESlateVisibility::HitTestInvisible
            : ESlateVisibility::Collapsed);
        if (Toast && ToastText)
        {
            ToastText->SetText(FText::Format(
                LOCTEXT("ToastLine", "{0}  {1}"),
                GlyphForStatus(Toast->Status), Toast->Message));
            ToastText->SetColorAndOpacity(FSlateColor(
                ULBOneFactoryUITokens::TokenForStatus(Toast->Status)
                    .Colour));
        }
    }

    if (!bInboxOpen)
    {
        return;
    }
    RowGroupIndices.Reset();
    if (InboxTitle)
    {
        InboxTitle->SetText(FText::Format(
            LOCTEXT("InboxTitleCount", "ALERTS  ({0})"),
            FText::AsNumber(bCollected ? Alerts.Num() : 0)));
    }
    if (EmptyText)
    {
        EmptyText->SetVisibility(!bCollected || Alerts.Num() == 0
            ? ESlateVisibility::Visible : ESlateVisibility::Collapsed);
    }
    for (int32 Index = 0; Index < RowButtons.Num(); ++Index)
    {
        const bool bUsed = bCollected && Alerts.IsValidIndex(Index);
        RowButtons[Index]->SetVisibility(bUsed
            ? ESlateVisibility::Visible : ESlateVisibility::Collapsed);
        if (!bUsed)
        {
            continue;
        }
        const FLBOneFactoryLiveAlert& Alert = Alerts[Index];
        RowTexts[Index]->SetText(FText::Format(
            LOCTEXT("InboxRow", "{0}  {1}"), GlyphForStatus(Alert.Status),
            Alert.Message));
        RowTexts[Index]->SetColorAndOpacity(FSlateColor(
            ULBOneFactoryUITokens::TokenForStatus(Alert.Status).Colour));
        RowGroupIndices.Add(Alert.GroupIndex);
    }
}

void ULBOneFactoryAlertCenterWidget::NavigateRow(const int32 RowIndex)
{
    if (!RowGroupIndices.IsValidIndex(RowIndex) || !FlowStrip)
    {
        return;
    }
    const int32 GroupIndex = RowGroupIndices[RowIndex];
    if (GroupIndex != INDEX_NONE
        && FlowStrip->SimulateCardClick(GroupIndex))
    {
        HideInbox();
    }
}

void ULBOneFactoryAlertCenterWidget::OnRow0Clicked() { NavigateRow(0); }
void ULBOneFactoryAlertCenterWidget::OnRow1Clicked() { NavigateRow(1); }
void ULBOneFactoryAlertCenterWidget::OnRow2Clicked() { NavigateRow(2); }
void ULBOneFactoryAlertCenterWidget::OnRow3Clicked() { NavigateRow(3); }
void ULBOneFactoryAlertCenterWidget::OnRow4Clicked() { NavigateRow(4); }
void ULBOneFactoryAlertCenterWidget::OnRow5Clicked() { NavigateRow(5); }
void ULBOneFactoryAlertCenterWidget::OnRow6Clicked() { NavigateRow(6); }
void ULBOneFactoryAlertCenterWidget::OnRow7Clicked() { NavigateRow(7); }

#undef LOCTEXT_NAMESPACE
