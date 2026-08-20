#include "LBOneFactoryDetailPanelWidget.h"

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
#include "Engine/World.h"
#include "EngineUtils.h"
#include "LBOneFactoryOperationsSubsystem.h"
#include "LBOneFactoryRuntimeCoordinator.h"
#include "LBOneFactoryUITypes.h"

#define LOCTEXT_NAMESPACE "LineBossOneFactoryUI"

namespace LBOneFactoryDetailPanelPrivate
{
    const FLinearColor PanelBackground(0.031f, 0.037f, 0.042f, 0.94f);
    const FLinearColor Warm(0.88f, 0.86f, 0.80f, 1.0f);
    const FLinearColor Steel(0.44f, 0.46f, 0.48f, 1.0f);
    const FLinearColor ActionIdle(0.10f, 0.35f, 0.28f, 1.0f);

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

    FText DepartmentLabel(const ELBOneFactoryDepartment Department)
    {
        switch (Department)
        {
        case ELBOneFactoryDepartment::Press:
            return LOCTEXT("DeptPress", "PRESS SHOP");
        case ELBOneFactoryDepartment::Body:
            return LOCTEXT("DeptBody", "BODY SHOP");
        case ELBOneFactoryDepartment::Paint:
            return LOCTEXT("DeptPaint", "PAINT SHOP");
        default:
            return LOCTEXT("DeptAssembly", "ASSEMBLY SHOP");
        }
    }

    /** Cause first (UI rule 2): the sentence names why, not a magnitude. */
    FText CauseSentence(const ELBOneFactoryGroupState State)
    {
        switch (State)
        {
        case ELBOneFactoryGroupState::Running:
            return LOCTEXT("CauseRunning",
                "Cycling normally. Every unit here is inside its station's "
                "cycle time.");
        case ELBOneFactoryGroupState::Waiting:
            return LOCTEXT("CauseBlocked",
                "A finished unit cannot move on - the next station along "
                "the route is still occupied.");
        case ELBOneFactoryGroupState::Hold:
            return LOCTEXT("CauseQualityHold",
                "A unit is held at the quality gate awaiting its "
                "inspection result.");
        default:
            return LOCTEXT("CauseIdle",
                "No unit is in this part of the plant right now.");
        }
    }
}

TSharedRef<SWidget> ULBOneFactoryDetailPanelWidget::RebuildWidget()
{
    // The tree must exist before Slate takes it; NativeConstruct is too
    // late for widgets created without a Blueprint asset.
    BuildTree();
    return Super::RebuildWidget();
}

void ULBOneFactoryDetailPanelWidget::NativeConstruct()
{
    Super::NativeConstruct();
    // The widget spans the viewport; only the panel's controls take hits.
    SetVisibility(ESlateVisibility::SelfHitTestInvisible);
}

void ULBOneFactoryDetailPanelWidget::BuildTree()
{
    using namespace LBOneFactoryDetailPanelPrivate;
    if (!WidgetTree || WidgetTree->RootWidget)
    {
        return;
    }
    // Root pins the auto-sized panel to the right edge, below the top bar;
    // the fillers on the left and bottom stay click-through.
    UVerticalBox* RootBox = WidgetTree->ConstructWidget<UVerticalBox>(
        UVerticalBox::StaticClass(), TEXT("DetailRootBox"));
    WidgetTree->RootWidget = RootBox;

    USpacer* TopClearance = WidgetTree->ConstructWidget<USpacer>(
        USpacer::StaticClass(), TEXT("DetailTopClearance"));
    TopClearance->SetSize(FVector2D(1.0f, 44.0f));
    RootBox->AddChildToVerticalBox(TopClearance);

    UHorizontalBox* Row = WidgetTree->ConstructWidget<UHorizontalBox>(
        UHorizontalBox::StaticClass(), TEXT("DetailRow"));
    if (UVerticalBoxSlot* RowSlot = RootBox->AddChildToVerticalBox(Row))
    {
        RowSlot->SetSize(FSlateChildSize(ESlateSizeRule::Automatic));
        RowSlot->SetHorizontalAlignment(HAlign_Fill);
    }
    USpacer* LeftFill = WidgetTree->ConstructWidget<USpacer>(
        USpacer::StaticClass(), TEXT("DetailLeftFill"));
    if (UHorizontalBoxSlot* FillSlot = Row->AddChildToHorizontalBox(LeftFill))
    {
        FillSlot->SetSize(FSlateChildSize(ESlateSizeRule::Fill));
    }

    PanelBorder = WidgetTree->ConstructWidget<UBorder>(
        UBorder::StaticClass(), TEXT("DetailPanel"));
    PanelBorder->SetBrushColor(PanelBackground);
    PanelBorder->SetPadding(FMargin(14.0f, 10.0f, 14.0f, 12.0f));
    PanelBorder->SetVisibility(ESlateVisibility::Collapsed);
    if (UHorizontalBoxSlot* PanelSlot = Row->AddChildToHorizontalBox(
            PanelBorder))
    {
        PanelSlot->SetPadding(FMargin(0.0f, 0.0f, 10.0f, 0.0f));
    }

    UVerticalBox* Body = WidgetTree->ConstructWidget<UVerticalBox>(
        UVerticalBox::StaticClass(), TEXT("DetailBody"));
    PanelBorder->SetContent(Body);

    UHorizontalBox* TitleRow = WidgetTree->ConstructWidget<UHorizontalBox>(
        UHorizontalBox::StaticClass(), TEXT("DetailTitleRow"));
    Body->AddChildToVerticalBox(TitleRow);
    TitleText = MakeText(WidgetTree, TEXT("DetailTitle"), FText::GetEmpty(),
        15.0f, Warm);
    TitleRow->AddChildToHorizontalBox(TitleText);
    USpacer* TitleGap = WidgetTree->ConstructWidget<USpacer>(
        USpacer::StaticClass(), TEXT("DetailTitleGap"));
    TitleGap->SetSize(FVector2D(24.0f, 1.0f));
    if (UHorizontalBoxSlot* TitleGapSlot =
            TitleRow->AddChildToHorizontalBox(TitleGap))
    {
        TitleGapSlot->SetSize(FSlateChildSize(ESlateSizeRule::Fill));
    }
    CloseButton = WidgetTree->ConstructWidget<UButton>(
        UButton::StaticClass(), TEXT("DetailClose"));
    CloseButton->SetBackgroundColor(Steel);
    UTextBlock* CloseLabel = MakeText(WidgetTree, TEXT("DetailCloseLabel"),
        LOCTEXT("DetailCloseGlyph", "X"), 10.0f, Warm);
    CloseButton->AddChild(CloseLabel);
    FScriptDelegate CloseDelegate;
    CloseDelegate.BindUFunction(this, TEXT("OnCloseClicked"));
    CloseButton->OnClicked.Add(CloseDelegate);
    TitleRow->AddChildToHorizontalBox(CloseButton);

    DepartmentText = MakeText(WidgetTree, TEXT("DetailDept"),
        FText::GetEmpty(), 10.0f, Steel);
    Body->AddChildToVerticalBox(DepartmentText);

    CauseText = MakeText(WidgetTree, TEXT("DetailCause"), FText::GetEmpty(),
        12.0f, Warm);
    CauseText->SetAutoWrapText(true);
    if (UVerticalBoxSlot* CauseSlot = Body->AddChildToVerticalBox(CauseText))
    {
        CauseSlot->SetPadding(FMargin(0.0f, 8.0f, 0.0f, 8.0f));
    }

    auto AddStat = [this, &Body](const TCHAR* Name,
        TObjectPtr<UTextBlock>& OutText)
    {
        OutText = MakeText(WidgetTree, Name, FText::GetEmpty(), 11.0f,
            Steel);
        if (UVerticalBoxSlot* StatSlot = Body->AddChildToVerticalBox(OutText))
        {
            StatSlot->SetPadding(FMargin(0.0f, 1.0f, 0.0f, 1.0f));
        }
    };
    AddStat(TEXT("DetailStations"), StationsText);
    AddStat(TEXT("DetailUnits"), UnitsText);
    AddStat(TEXT("DetailRate"), RateText);
    AddStat(TEXT("DetailProgress"), ProgressText);

    PrimaryButton = WidgetTree->ConstructWidget<UButton>(
        UButton::StaticClass(), TEXT("DetailPrimary"));
    PrimaryButton->SetBackgroundColor(ActionIdle);
    PrimaryLabel = MakeText(WidgetTree, TEXT("DetailPrimaryLabel"),
        FText::GetEmpty(), 12.0f, Warm);
    PrimaryButton->AddChild(PrimaryLabel);
    if (UButtonSlot* LabelSlot = Cast<UButtonSlot>(PrimaryLabel->Slot))
    {
        LabelSlot->SetPadding(FMargin(12.0f, 5.0f));
        LabelSlot->SetHorizontalAlignment(HAlign_Center);
    }
    FScriptDelegate PrimaryDelegate;
    PrimaryDelegate.BindUFunction(this, TEXT("OnPrimaryActionClicked"));
    PrimaryButton->OnClicked.Add(PrimaryDelegate);
    if (UVerticalBoxSlot* PrimarySlot = Body->AddChildToVerticalBox(
            PrimaryButton))
    {
        PrimarySlot->SetPadding(FMargin(0.0f, 10.0f, 0.0f, 0.0f));
        PrimarySlot->SetHorizontalAlignment(HAlign_Fill);
    }
}

void ULBOneFactoryDetailPanelWidget::NativeTick(const FGeometry& MyGeometry,
    const float InDeltaTime)
{
    Super::NativeTick(MyGeometry, InDeltaTime);
    if (ShownGroupIndex == INDEX_NONE)
    {
        return;
    }
    RefreshAccumulator += InDeltaTime;
    if (RefreshAccumulator >= 0.25f)
    {
        RefreshAccumulator = 0.0f;
        Refresh();
    }
}

void ULBOneFactoryDetailPanelWidget::ShowGroup(const int32 GroupIndex)
{
    ShownGroupIndex = GroupIndex;
    if (PanelBorder)
    {
        PanelBorder->SetVisibility(ESlateVisibility::Visible);
    }
    Refresh();
}

void ULBOneFactoryDetailPanelWidget::Hide()
{
    ShownGroupIndex = INDEX_NONE;
    if (PanelBorder)
    {
        PanelBorder->SetVisibility(ESlateVisibility::Collapsed);
    }
}

void ULBOneFactoryDetailPanelWidget::Refresh()
{
    using namespace LBOneFactoryDetailPanelPrivate;
    TArray<FLBOneFactoryProcessGroup> Groups;
    TArray<FString> Alerts;
    int32 UnitsLive = 0;
    int32 Dispatched = 0;
    if (!ALBOneFactoryProductionHUD::CollectGroups(GetWorld(), Groups,
            UnitsLive, Dispatched, Alerts)
        || !Groups.IsValidIndex(ShownGroupIndex))
    {
        Hide();
        return;
    }
    const FLBOneFactoryProcessGroup& Group = Groups[ShownGroupIndex];

    TitleText->SetText(FText::FromString(Group.Label.ToUpper()));
    DepartmentText->SetText(Group.bHasDepartment
        ? DepartmentLabel(Group.Department) : FText::GetEmpty());

    const FLBOneFactoryStatusToken Token =
        ULBOneFactoryUITokens::TokenForStatus(
            Group.State == ELBOneFactoryGroupState::Running
                ? ELBOneFactoryStationStatus::Working
            : Group.State == ELBOneFactoryGroupState::Waiting
                ? ELBOneFactoryStationStatus::Blocked
            : Group.State == ELBOneFactoryGroupState::Hold
                ? ELBOneFactoryStationStatus::QualityHold
                : ELBOneFactoryStationStatus::Offline);
    CauseText->SetText(CauseSentence(Group.State));
    CauseText->SetColorAndOpacity(FSlateColor(
        Group.State == ELBOneFactoryGroupState::Idle ? Steel : Token.Colour));

    StationsText->SetText(FText::Format(
        LOCTEXT("DetailStationsLine",
            "Stations: {0}{1}"),
        FText::AsNumber(Group.StationCount),
        Group.bHasQualityGate
            ? LOCTEXT("DetailQualityGate", "  (includes a quality gate)")
            : FText::GetEmpty()));
    UnitsText->SetText(FText::Format(
        LOCTEXT("DetailUnitsLine", "Units here: {0}"),
        FText::AsNumber(Group.UnitCount)));

    FNumberFormattingOptions RateFormat;
    RateFormat.MaximumFractionalDigits = 1;
    RateText->SetText(Group.bHasDepartment
        ? FText::Format(
            LOCTEXT("DetailRateLine",
                "Measured: {0} cars/hr   Capacity: {1} cars/hr"),
            FText::AsNumber(Group.MeasuredRatePerHour, &RateFormat),
            FText::AsNumber(Group.ThroughputPerHour, &RateFormat))
        : FText::Format(
            LOCTEXT("DetailCapacityLine", "Capacity: {0} cars/hr"),
            FText::AsNumber(Group.ThroughputPerHour, &RateFormat)));

    ProgressText->SetText(FText::Format(
        LOCTEXT("DetailProgressLine", "Mean cycle progress: {0}%"),
        FText::AsNumber(FMath::RoundToInt(Group.MeanProgress * 100.0f))));

    // One honest primary action: service the fleet when wear says so,
    // resume when the line is paused, otherwise just close.
    PrimaryAction = EPrimaryAction::Close;
    FText ActionLabel = LOCTEXT("ActionClose", "CLOSE");
    FLBOneFactoryManagementBand Band;
    if (ALBOneFactoryProductionHUD::CollectManagement(GetWorld(), Band))
    {
        if (Band.FleetWear01 > 0.6)
        {
            PrimaryAction = EPrimaryAction::ServiceFleet;
            ActionLabel = LOCTEXT("ActionService",
                "SERVICE THE FLEET  -  £25,000");
        }
        else if (Band.bPaused)
        {
            PrimaryAction = EPrimaryAction::ResumeLine;
            ActionLabel = LOCTEXT("ActionResume", "RESUME THE LINE");
        }
    }
    PrimaryLabel->SetText(ActionLabel);
    PrimaryButton->SetBackgroundColor(
        PrimaryAction == EPrimaryAction::ServiceFleet
            ? ULBOneFactoryUITokens::TokenForStatus(
                ELBOneFactoryStationStatus::WearCritical).Colour
            : ActionIdle);
}

void ULBOneFactoryDetailPanelWidget::OnPrimaryActionClicked()
{
    UWorld* World = GetWorld();
    if (!World)
    {
        return;
    }
    switch (PrimaryAction)
    {
    case EPrimaryAction::ServiceFleet:
    {
        TActorIterator<ALBOneFactoryRuntimeCoordinator> It(World);
        if (It)
        {
            FString Reason;
            It->PerformPlantMaintenance(Reason);
        }
        break;
    }
    case EPrimaryAction::ResumeLine:
        if (ULBOneFactoryOperationsSubsystem* Operations =
                World->GetSubsystem<ULBOneFactoryOperationsSubsystem>())
        {
            FString Reason;
            Operations->SetSimulationRate(1.0f, Reason);
        }
        break;
    default:
        Hide();
        break;
    }
}

void ULBOneFactoryDetailPanelWidget::OnCloseClicked()
{
    Hide();
}

#undef LOCTEXT_NAMESPACE
