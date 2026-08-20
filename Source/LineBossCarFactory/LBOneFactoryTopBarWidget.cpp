#include "LBOneFactoryTopBarWidget.h"

#include "Blueprint/WidgetTree.h"
#include "Components/Border.h"
#include "Components/Button.h"
#include "Components/HorizontalBox.h"
#include "Components/HorizontalBoxSlot.h"
#include "Components/Spacer.h"
#include "Components/TextBlock.h"
#include "Engine/World.h"
#include "EngineUtils.h"
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

void ULBOneFactoryTopBarWidget::NativeConstruct()
{
    Super::NativeConstruct();
    BuildTree();
    Refresh();
}

void ULBOneFactoryTopBarWidget::BuildTree()
{
    using namespace LBOneFactoryTopBarPrivate;
    if (!WidgetTree || WidgetTree->RootWidget)
    {
        return;
    }
    UBorder* Root = WidgetTree->ConstructWidget<UBorder>(
        UBorder::StaticClass(), TEXT("TopBarRoot"));
    Root->SetBrushColor(BarBackground);
    Root->SetPadding(FMargin(14.0f, 6.0f));
    WidgetTree->RootWidget = Root;

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
    AddCell(ContractText);
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

    AlertText = MakeText(WidgetTree, TEXT("Alerts"),
        FText::GetEmpty(), 12.0f, Steel);
    AddCell(AlertText);
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
    TArray<FString> Alerts;
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

void ULBOneFactoryTopBarWidget::OnPauseClicked() { SetSimulationRate(0.0f); }
void ULBOneFactoryTopBarWidget::OnSpeed1Clicked() { SetSimulationRate(1.0f); }
void ULBOneFactoryTopBarWidget::OnSpeed2Clicked() { SetSimulationRate(2.0f); }
void ULBOneFactoryTopBarWidget::OnSpeed4Clicked() { SetSimulationRate(4.0f); }

#undef LOCTEXT_NAMESPACE
