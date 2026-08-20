#include "LBOneFactoryTopBarWidget.h"

#include "Blueprint/WidgetTree.h"
#include "Components/Border.h"
#include "Components/Button.h"
#include "Components/HorizontalBox.h"
#include "Components/HorizontalBoxSlot.h"
#include "Components/Spacer.h"
#include "Components/TextBlock.h"
#include "Components/VerticalBox.h"
#include "Components/VerticalBoxSlot.h"
#include "Engine/World.h"
#include "EngineUtils.h"
#include "LBOneFactoryAlertCenterWidget.h"
#include "LBOneFactoryOperationsSubsystem.h"
#include "LBOneFactoryProductionHUD.h"
#include "LBOneFactoryRuntimeCoordinator.h"

#define LOCTEXT_NAMESPACE "LineBossOneFactoryUI"

namespace LBOneFactoryTopBarPrivate
{
    const FLinearColor BarBackground(0.031f, 0.037f, 0.042f, 0.92f);
    const FLinearColor Warm(0.88f, 0.86f, 0.80f, 1.0f);
    const FLinearColor Steel(0.44f, 0.46f, 0.48f, 1.0f);
    const FLinearColor Active(0.10f, 0.35f, 0.28f, 1.0f);

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
}

TSharedRef<SWidget> ULBOneFactoryTopBarWidget::RebuildWidget()
{
    // The tree must exist before Slate takes it; NativeConstruct is too
    // late for widgets created without a Blueprint asset.
    BuildTree();
    return Super::RebuildWidget();
}

void ULBOneFactoryTopBarWidget::NativeConstruct()
{
    Super::NativeConstruct();
    // The widget spans the viewport; only the bar's own controls take hits.
    SetVisibility(ESlateVisibility::SelfHitTestInvisible);
    Refresh();
}

void ULBOneFactoryTopBarWidget::BuildTree()
{
    using namespace LBOneFactoryTopBarPrivate;
    if (!WidgetTree || WidgetTree->RootWidget)
    {
        return;
    }
    // Root is a vertical box whose only child auto-sizes: the bar hugs the
    // top edge and the rest of the screen stays untouched and click-through.
    UVerticalBox* RootBox = WidgetTree->ConstructWidget<UVerticalBox>(
        UVerticalBox::StaticClass(), TEXT("TopBarRootBox"));
    WidgetTree->RootWidget = RootBox;

    UBorder* Root = WidgetTree->ConstructWidget<UBorder>(
        UBorder::StaticClass(), TEXT("TopBarRoot"));
    Root->SetBrushColor(BarBackground);
    Root->SetPadding(FMargin(14.0f, 6.0f));
    if (UVerticalBoxSlot* BarSlot = RootBox->AddChildToVerticalBox(Root))
    {
        BarSlot->SetHorizontalAlignment(HAlign_Fill);
        BarSlot->SetSize(FSlateChildSize(ESlateSizeRule::Automatic));
    }

    UHorizontalBox* Row = WidgetTree->ConstructWidget<UHorizontalBox>(
        UHorizontalBox::StaticClass(), TEXT("TopBarRow"));
    Root->SetContent(Row);

    auto AddCell = [&Row](UWidget* Widget, const float CellPad = 12.0f,
        const bool bFill = false)
    {
        UHorizontalBoxSlot* Slot = Row->AddChildToHorizontalBox(Widget);
        Slot->SetPadding(FMargin(CellPad, 0.0f, 0.0f, 0.0f));
        Slot->SetVerticalAlignment(VAlign_Center);
        if (bFill)
        {
            Slot->SetSize(FSlateChildSize(ESlateSizeRule::Fill));
        }
    };

    AddCell(MakeText(WidgetTree, TEXT("Brand"),
        LOCTEXT("TopBarBrand", "MOORCROSS WORKS"), 15.0f, Warm), 0.0f);
    AddCell(MakeText(WidgetTree, TEXT("Model"),
        LOCTEXT("TopBarModel", "CAIRNWELL 2040"), 11.0f, Steel));

    USpacer* Gap = WidgetTree->ConstructWidget<USpacer>(
        USpacer::StaticClass(), TEXT("TopBarGap"));
    AddCell(Gap, 0.0f, true);

    ContractText = MakeText(WidgetTree, TEXT("Contract"),
        LOCTEXT("TopBarNoContract", "No open contract"), 13.0f, Warm);
    OrdersButton = WidgetTree->ConstructWidget<UButton>(
        UButton::StaticClass(), TEXT("TopBarOrders"));
    OrdersButton->SetBackgroundColor(FLinearColor(0.0f, 0.0f, 0.0f, 0.0f));
    OrdersButton->AddChild(ContractText);
    FScriptDelegate OrdersDelegate;
    OrdersDelegate.BindUFunction(this, TEXT("OnOrdersClicked"));
    OrdersButton->OnClicked.Add(OrdersDelegate);
    OrdersButton->SetToolTipText(
        LOCTEXT("TopBarOrdersTip", "Click to list every order"));
    AddCell(OrdersButton);
    CashText = MakeText(WidgetTree, TEXT("Cash"),
        LOCTEXT("TopBarCashPending", "CASH -"), 13.0f, Warm);
    AddCell(CashText);
    ClockText = MakeText(WidgetTree, TEXT("Clock"),
        FText::GetEmpty(), 13.0f, Warm);
    AddCell(ClockText);
    RepWearText = MakeText(WidgetTree, TEXT("RepWear"),
        FText::GetEmpty(), 12.0f, Steel);
    AddCell(RepWearText);

    struct FTransport
    {
        const TCHAR* Name;
        FText Label;
        TObjectPtr<UButton>* Button;
        TObjectPtr<UTextBlock>* LabelBlock;
        FName Handler;
    };
    const FTransport Transports[] = {
        { TEXT("PauseBtn"), LOCTEXT("TransportPause", "II"),
          &PauseButton, &PauseLabel, TEXT("OnPauseClicked") },
        { TEXT("Speed1Btn"), LOCTEXT("TransportSpeed1", "1x"),
          &Speed1Button, &Speed1Label, TEXT("OnSpeed1Clicked") },
        { TEXT("Speed2Btn"), LOCTEXT("TransportSpeed2", "2x"),
          &Speed2Button, &Speed2Label, TEXT("OnSpeed2Clicked") },
        { TEXT("Speed4Btn"), LOCTEXT("TransportSpeed4", "4x"),
          &Speed4Button, &Speed4Label, TEXT("OnSpeed4Clicked") },
    };
    for (const FTransport& Transport : Transports)
    {
        UButton* Button = WidgetTree->ConstructWidget<UButton>(
            UButton::StaticClass(), Transport.Name);
        UTextBlock* Label = MakeText(WidgetTree,
            FName(*(FString(Transport.Name) + TEXT("Label"))),
            Transport.Label, 12.0f, Warm);
        Button->AddChild(Label);
        FScriptDelegate Delegate;
        Delegate.BindUFunction(this, Transport.Handler);
        Button->OnClicked.Add(Delegate);
        *Transport.Button = Button;
        *Transport.LabelBlock = Label;
        AddCell(Button, 6.0f);
    }

    // The bell is a button: it toggles the alert centre's inbox.
    AlertButton = WidgetTree->ConstructWidget<UButton>(
        UButton::StaticClass(), TEXT("AlertsBtn"));
    AlertButton->SetBackgroundColor(Steel);
    AlertText = MakeText(WidgetTree, TEXT("Alerts"),
        FText::GetEmpty(), 12.0f, Warm);
    AlertButton->AddChild(AlertText);
    FScriptDelegate AlertDelegate;
    AlertDelegate.BindUFunction(this, TEXT("OnAlertsClicked"));
    AlertButton->OnClicked.Add(AlertDelegate);
    AddCell(AlertButton, 6.0f);

    // v2.1 orders dropdown under the bar, opened from the contract cell.
    OrdersBorder = WidgetTree->ConstructWidget<UBorder>(
        UBorder::StaticClass(), TEXT("TopBarOrdersPanel"));
    OrdersBorder->SetBrushColor(FLinearColor(0.031f, 0.037f, 0.042f,
        0.94f));
    OrdersBorder->SetPadding(FMargin(10.0f, 8.0f));
    OrdersBorder->SetVisibility(ESlateVisibility::Collapsed);
    UVerticalBox* OrdersBox = WidgetTree->ConstructWidget<UVerticalBox>(
        UVerticalBox::StaticClass(), TEXT("TopBarOrdersBox"));
    OrdersBox->AddChildToVerticalBox(MakeText(WidgetTree,
        TEXT("TopBarOrdersTitle"),
        LOCTEXT("TopBarOrdersTitle", "ORDERS"), 10.0f, Steel));
    for (int32 Index = 0; Index < 6; ++Index)
    {
        UTextBlock* Line = MakeText(WidgetTree,
            FName(*FString::Printf(TEXT("TopBarOrder%d"), Index)),
            FText::GetEmpty(), 11.0f, Warm);
        Line->SetVisibility(ESlateVisibility::Collapsed);
        if (UVerticalBoxSlot* LineSlot =
            OrdersBox->AddChildToVerticalBox(Line))
        {
            LineSlot->SetPadding(FMargin(0.0f, 2.0f, 0.0f, 0.0f));
        }
        OrderTexts.Add(Line);
    }
    OrdersBorder->SetContent(OrdersBox);
    if (UVerticalBoxSlot* PanelSlot = Cast<UVerticalBoxSlot>(
            WidgetTree->RootWidget
                ? Cast<UVerticalBox>(WidgetTree->RootWidget)
                    ->AddChildToVerticalBox(OrdersBorder) : nullptr))
    {
        PanelSlot->SetHorizontalAlignment(HAlign_Right);
        PanelSlot->SetPadding(FMargin(0.0f, 2.0f, 300.0f, 0.0f));
    }

    // v2.1 day-summary banner, centred under the bar, transient.
    SummaryBorder = WidgetTree->ConstructWidget<UBorder>(
        UBorder::StaticClass(), TEXT("TopBarSummaryPanel"));
    SummaryBorder->SetBrushColor(FLinearColor(0.031f, 0.037f, 0.042f,
        0.94f));
    SummaryBorder->SetPadding(FMargin(14.0f, 6.0f));
    SummaryBorder->SetVisibility(ESlateVisibility::Collapsed);
    SummaryText = MakeText(WidgetTree, TEXT("TopBarSummaryText"),
        FText::GetEmpty(), 12.0f, Warm);
    SummaryBorder->SetContent(SummaryText);
    if (UVerticalBoxSlot* SummarySlot = Cast<UVerticalBoxSlot>(
            WidgetTree->RootWidget
                ? Cast<UVerticalBox>(WidgetTree->RootWidget)
                    ->AddChildToVerticalBox(SummaryBorder) : nullptr))
    {
        SummarySlot->SetHorizontalAlignment(HAlign_Center);
        SummarySlot->SetPadding(FMargin(0.0f, 2.0f, 0.0f, 0.0f));
    }
}

void ULBOneFactoryTopBarWidget::OnOrdersClicked()
{
    bOrdersOpen = !bOrdersOpen;
    if (OrdersBorder)
    {
        OrdersBorder->SetVisibility(bOrdersOpen
            ? ESlateVisibility::HitTestInvisible
            : ESlateVisibility::Collapsed);
    }
    if (bOrdersOpen && AlertCenter)
    {
        AlertCenter->HideInbox();
    }
    Refresh();
}

void ULBOneFactoryTopBarWidget::NativeTick(const FGeometry& MyGeometry,
    const float InDeltaTime)
{
    Super::NativeTick(MyGeometry, InDeltaTime);
    RefreshAccumulator += InDeltaTime;
    if (RefreshAccumulator >= 0.25f)
    {
        RefreshAccumulator = 0.0f;
        Refresh();
    }
    if (SummarySecondsLeft > 0.0f)
    {
        SummarySecondsLeft -= InDeltaTime;
        if (SummarySecondsLeft <= 0.0f && SummaryBorder)
        {
            SummaryBorder->SetVisibility(ESlateVisibility::Collapsed);
        }
    }
}

void ULBOneFactoryTopBarWidget::Refresh()
{
    using namespace LBOneFactoryTopBarPrivate;
    FLBOneFactoryManagementBand Band;
    if (!ALBOneFactoryProductionHUD::CollectManagement(GetWorld(), Band))
    {
        return;
    }

    // Oldest open contract is the pace-setter (mockup's order counter).
    const FLBOneFactoryContractRow* ActiveContract = nullptr;
    for (const FLBOneFactoryContractRow& Row : Band.Contracts)
    {
        if (Row.State == ELBOneFactoryContractState::Open)
        {
            ActiveContract = &Row;
            break;
        }
    }
    if (ActiveContract)
    {
        const int32 MinutesLeft = FMath::Max(0,
            FMath::FloorToInt32(ActiveContract->SecondsRemaining / 60.0));
        ContractText->SetText(FText::Format(
            LOCTEXT("TopBarContract", "{0}  {1}/{2}  {3}h {4}m"),
            FText::FromString(ActiveContract->ContractId),
            FText::AsNumber(ActiveContract->DispatchedCount),
            FText::AsNumber(ActiveContract->Quantity),
            FText::AsNumber(MinutesLeft / 60),
            FText::AsNumber(MinutesLeft % 60)));
    }
    else
    {
        ContractText->SetText(
            LOCTEXT("TopBarNoContract", "No open contract"));
    }

    if (bOrdersOpen)
    {
        for (int32 Index = 0; Index < OrderTexts.Num(); ++Index)
        {
            const bool bUsed = Band.Contracts.IsValidIndex(Index);
            OrderTexts[Index]->SetVisibility(bUsed
                ? ESlateVisibility::Visible : ESlateVisibility::Collapsed);
            if (!bUsed)
            {
                continue;
            }
            const FLBOneFactoryContractRow& Row = Band.Contracts[Index];
            const int32 RowMinutes = FMath::Max(0,
                FMath::FloorToInt32(Row.SecondsRemaining / 60.0));
            const FText StateLabel =
                Row.State == ELBOneFactoryContractState::Complete
                    ? LOCTEXT("TopBarOrderComplete", "complete")
                : Row.State == ELBOneFactoryContractState::Expired
                    ? LOCTEXT("TopBarOrderExpired", "expired")
                : Row.bEmergency
                    ? LOCTEXT("TopBarOrderUrgent", "URGENT")
                    : LOCTEXT("TopBarOrderOpen", "open");
            OrderTexts[Index]->SetText(FText::Format(
                LOCTEXT("TopBarOrderRow",
                    "{0}  ·  {1}/{2}  ·  {3}h {4}m  ·  {5}"),
                FText::FromString(Row.ContractId),
                FText::AsNumber(Row.DispatchedCount),
                FText::AsNumber(Row.Quantity),
                FText::AsNumber(RowMinutes / 60),
                FText::AsNumber(RowMinutes % 60), StateLabel));
            OrderTexts[Index]->SetColorAndOpacity(FSlateColor(
                Row.bEmergency
                    ? ULBOneFactoryUITokens::TokenForStatus(
                        ELBOneFactoryStationStatus::Blocked).Colour
                    : Row.State == ELBOneFactoryContractState::Open
                        ? Warm : Steel));
        }
    }

    const FLBOneFactoryStatusToken FinanceToken =
        ULBOneFactoryUITokens::TokenForStatus(
            Band.FinancialState == ELBOneFactoryFinancialState::Emergency
                ? ELBOneFactoryStationStatus::Blocked
                : Band.FinancialState == ELBOneFactoryFinancialState::Warning
                    ? ELBOneFactoryStationStatus::Starved
                    : ELBOneFactoryStationStatus::Working);
    CashText->SetText(Band.bHasCash
        ? FText::Format(LOCTEXT("TopBarCash", "£{0}"),
            FText::AsNumber(Band.CashPence / 100))
        : LOCTEXT("TopBarCashPending", "CASH -"));
    CashText->SetColorAndOpacity(FSlateColor(FinanceToken.Colour));

    if (Band.bHasCash)
    {
        const int32 SimDay = 1 + FMath::FloorToInt32(
            static_cast<float>(Band.SimClockSeconds / 86400.0));
        if (LastSimDay == -1 || SimDay != LastSimDay)
        {
            TArray<FLBOneFactoryProcessGroup> Groups;
            TArray<FLBOneFactoryLiveAlert> Alerts;
            int32 UnitsLive = 0;
            int32 Dispatched = 0;
            const bool bHaveDispatch =
                ALBOneFactoryProductionHUD::CollectGroups(GetWorld(),
                    Groups, UnitsLive, Dispatched, Alerts);
            if (LastSimDay != -1 && SummaryText && SummaryBorder)
            {
                const int64 CashDeltaPence =
                    Band.CashPence - DayStartCashPence;
                SummaryText->SetText(FText::Format(
                    LOCTEXT("TopBarDaySummary",
                        "DAY {0}  ·  yesterday: {1} dispatched  ·  "
                        "cash {2}£{3}"),
                    FText::AsNumber(SimDay),
                    FText::AsNumber(bHaveDispatch
                        ? FMath::Max(0, Dispatched - DayStartDispatched)
                        : 0),
                    CashDeltaPence < 0
                        ? LOCTEXT("TopBarSummaryMinus", "-")
                        : LOCTEXT("TopBarSummaryPlus", "+"),
                    FText::AsNumber(FMath::Abs(CashDeltaPence) / 100)));
                SummaryBorder->SetVisibility(
                    ESlateVisibility::HitTestInvisible);
                SummarySecondsLeft = 20.0f;
            }
            LastSimDay = SimDay;
            DayStartCashPence = Band.CashPence;
            if (bHaveDispatch)
            {
                DayStartDispatched = Dispatched;
            }
        }
    }

    const int32 TotalMinutes =
        FMath::FloorToInt32(Band.SimClockSeconds / 60.0);
    FNumberFormattingOptions TwoDigits;
    TwoDigits.MinimumIntegralDigits = 2;
    ClockText->SetText(FText::Format(
        LOCTEXT("TopBarClock", "DAY {0}  {1}:{2}"),
        FText::AsNumber(1 + TotalMinutes / (24 * 60)),
        FText::AsNumber((TotalMinutes / 60) % 24),
        FText::AsNumber(TotalMinutes % 60, &TwoDigits)));

    RepWearText->SetText(FText::Format(
        LOCTEXT("TopBarRepWear", "REP {0}  WEAR {1}%"),
        FText::AsNumber(Band.Reputation),
        FText::AsNumber(FMath::RoundToInt(Band.FleetWear01 * 100.0))));

    // Lit active transport segment (honest speed: read, not assumed).
    UButton* Buttons[] = { PauseButton, Speed1Button, Speed2Button,
        Speed4Button };
    int32 ActiveIndex = 1;
    if (Band.bPaused)
    {
        ActiveIndex = 0;
    }
    else if (const UWorld* World = GetWorld())
    {
        for (TActorIterator<ALBOneFactoryRuntimeCoordinator>
            It(const_cast<UWorld*>(World)); It; ++It)
        {
            const float Scale = It->GetRuntimeTimeScale();
            ActiveIndex = Scale >= 3.0f ? 3 : Scale >= 1.5f ? 2 : 1;
            break;
        }
    }
    for (int32 Index = 0; Index < 4; ++Index)
    {
        if (Buttons[Index])
        {
            Buttons[Index]->SetBackgroundColor(
                Index == ActiveIndex ? Active : Steel);
        }
    }

    TArray<FLBOneFactoryProcessGroup> Groups;
    TArray<FLBOneFactoryLiveAlert> Alerts;
    int32 Live = 0;
    int32 Dispatched = 0;
    ALBOneFactoryProductionHUD::CollectGroups(GetWorld(), Groups, Live,
        Dispatched, Alerts);
    AlertText->SetText(FText::Format(
        LOCTEXT("TopBarAlerts", "ALERTS {0}"),
        FText::AsNumber(Alerts.Num())));
    AlertText->SetColorAndOpacity(FSlateColor(Alerts.Num() > 0
        ? ULBOneFactoryUITokens::TokenForStatus(
            ELBOneFactoryStationStatus::Starved).Colour
        : Steel));
}

bool ULBOneFactoryTopBarWidget::SetSimulationRate(const float Rate)
{
    UWorld* World = GetWorld();
    ULBOneFactoryOperationsSubsystem* Operations =
        World ? World->GetSubsystem<ULBOneFactoryOperationsSubsystem>()
              : nullptr;
    if (!Operations)
    {
        return false;
    }
    FString Reason;
    return Operations->SetSimulationRate(Rate, Reason);
}

void ULBOneFactoryTopBarWidget::OnAlertsClicked()
{
    if (AlertCenter)
    {
        AlertCenter->ToggleInbox();
    }
}

void ULBOneFactoryTopBarWidget::OnPauseClicked() { SetSimulationRate(0.0f); }
void ULBOneFactoryTopBarWidget::OnSpeed1Clicked() { SetSimulationRate(1.0f); }
void ULBOneFactoryTopBarWidget::OnSpeed2Clicked() { SetSimulationRate(2.0f); }
void ULBOneFactoryTopBarWidget::OnSpeed4Clicked() { SetSimulationRate(4.0f); }

#undef LOCTEXT_NAMESPACE
