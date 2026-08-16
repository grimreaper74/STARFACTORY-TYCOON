#include "LBBodyShopPrototypeRootWidget.h"

#include "Blueprint/WidgetTree.h"
#include "Brushes/SlateRoundedBoxBrush.h"
#include "Components/Border.h"
#include "Components/Button.h"
#include "Components/ButtonSlot.h"
#include "Components/HorizontalBox.h"
#include "Components/HorizontalBoxSlot.h"
#include "Components/Overlay.h"
#include "Components/OverlaySlot.h"
#include "Components/SizeBox.h"
#include "Components/TextBlock.h"
#include "Components/VerticalBox.h"
#include "Components/VerticalBoxSlot.h"
#include "EngineUtils.h"
#include "Fonts/SlateFontInfo.h"
#include "LBBodyShopManagementPawn.h"
#include "LBBodyShopPrototypeWorldBootstrap.h"
#include "Styling/CoreStyle.h"

namespace LBBodyShopPrototypeUI
{
    const FLinearColor Ink(0.0065f, 0.0100f, 0.0120f, 0.96f);
    const FLinearColor Card(0.0200f, 0.0290f, 0.0330f, 0.96f);
    const FLinearColor CardHover(0.0320f, 0.0450f, 0.0500f, 1.0f);
    const FLinearColor Stroke(0.055f, 0.075f, 0.082f, 0.95f);
    const FLinearColor OffWhite(0.91f, 0.92f, 0.89f, 1.0f);
    const FLinearColor Muted(0.58f, 0.63f, 0.63f, 1.0f);
    const FLinearColor Green(0.030f, 0.64f, 0.235f, 1.0f);
    const FLinearColor GreenDark(0.008f, 0.110f, 0.050f, 1.0f);
    const FLinearColor Amber(1.0f, 0.58f, 0.08f, 1.0f);
    const FLinearColor Red(0.90f, 0.18f, 0.14f, 1.0f);

    FSlateFontInfo Font(const int32 Size, const bool bBold = false)
    {
        return FSlateFontInfo(FCoreStyle::GetDefaultFontStyle(
            bBold ? TEXT("Bold") : TEXT("Regular"), Size));
    }

    FSlateBrush RoundedBrush(const FLinearColor Fill, const FLinearColor Outline,
        const float OutlineWidth = 1.0f, const float Radius = 8.0f)
    {
        return FSlateRoundedBoxBrush(Fill,
            FVector4(Radius, Radius, Radius, Radius), Outline, OutlineWidth);
    }

    FButtonStyle ButtonStyle(const bool bPrimary)
    {
        FButtonStyle Style;
        const FLinearColor Normal = bPrimary
            ? FLinearColor(0.025f, 0.38f, 0.15f, 1.0f) : Card;
        const FLinearColor Hover = bPrimary
            ? FLinearColor(0.035f, 0.54f, 0.21f, 1.0f) : CardHover;
        Style.SetNormal(RoundedBrush(Normal, bPrimary ? Green : Stroke));
        Style.SetHovered(RoundedBrush(Hover, Green, 1.5f));
        Style.SetPressed(RoundedBrush(GreenDark, Green, 2.0f));
        Style.SetDisabled(RoundedBrush(Card.CopyWithNewOpacity(0.42f), Stroke));
        Style.SetNormalPadding(FMargin(1.0f));
        Style.SetPressedPadding(FMargin(2.0f, 3.0f, 0.0f, 0.0f));
        return Style;
    }

    UTextBlock* Text(UWidgetTree* Tree, const FName Name, const FString& Value,
        const int32 Size, const FLinearColor Colour, const bool bBold = false)
    {
        UTextBlock* Label = Tree->ConstructWidget<UTextBlock>(
            UTextBlock::StaticClass(), Name);
        Label->SetText(FText::FromString(Value));
        Label->SetFont(Font(Size, bBold));
        Label->SetColorAndOpacity(FSlateColor(Colour));
        Label->SetAutoWrapText(false);
        return Label;
    }

    UButton* Button(UWidgetTree* Tree, const FName Name, UTextBlock*& OutLabel,
        const FString& TextValue, const bool bPrimary)
    {
        UButton* Result = Tree->ConstructWidget<UButton>(UButton::StaticClass(), Name);
        Result->SetStyle(ButtonStyle(bPrimary));
        OutLabel = Text(Tree, FName(*(Name.ToString() + TEXT("Label"))),
            TextValue, 14, OffWhite, true);
        if (UButtonSlot* Slot = Cast<UButtonSlot>(Result->AddChild(OutLabel)))
        {
            Slot->SetPadding(FMargin(14.0f, 9.0f));
            Slot->SetHorizontalAlignment(HAlign_Center);
            Slot->SetVerticalAlignment(VAlign_Center);
        }
        return Result;
    }

    FString StageName(const ELBBodyShopRuntimeStage Stage)
    {
        const UEnum* Enum = StaticEnum<ELBBodyShopRuntimeStage>();
        return Enum ? Enum->GetDisplayNameTextByValue(static_cast<int64>(Stage)).ToString()
            : TEXT("Unknown");
    }
}

TArray<FName> ULBBodyShopPrototypeRootWidget::GetCanonicalControlIds()
{
    return {TEXT("START_PAUSE"), TEXT("SAVE"), TEXT("LOAD"),
        TEXT("CLEAR_HELD"), TEXT("ROBOT_SLOTS")};
}

FString ULBBodyShopPrototypeRootWidget::GetPrimaryActionLabel(
    const ELBBodyShopRuntimeStage Stage, const bool bSimulationRunning)
{
    if (bSimulationRunning) return TEXT("Pause line");
    switch (Stage)
    {
    case ELBBodyShopRuntimeStage::Ready:
        return TEXT("Start pilot cycle");
    case ELBBodyShopRuntimeStage::AwaitingPanelStillage:
        return TEXT("Waiting for stillage");
    case ELBBodyShopRuntimeStage::Complete:
        return TEXT("Release output first");
    case ELBBodyShopRuntimeStage::TransferringStillage:
    case ELBBodyShopRuntimeStage::PresentingPanel:
    case ELBBodyShopRuntimeStage::WeldingUnderbody:
    case ELBBodyShopRuntimeStage::ConveyingSkid:
    case ELBBodyShopRuntimeStage::Inspecting:
        return TEXT("Resume line");
    default:
        return TEXT("Line unavailable");
    }
}

TSharedRef<SWidget> ULBBodyShopPrototypeRootWidget::RebuildWidget()
{
    BuildShell();
    return Super::RebuildWidget();
}

void ULBBodyShopPrototypeRootWidget::NativeOnInitialized()
{
    Super::NativeOnInitialized();
    BuildShell();
}

void ULBBodyShopPrototypeRootWidget::NativeConstruct()
{
    Super::NativeConstruct();
    RefreshFromRuntime();
}

void ULBBodyShopPrototypeRootWidget::NativeTick(const FGeometry& MyGeometry,
    const float InDeltaTime)
{
    Super::NativeTick(MyGeometry, InDeltaTime);
    RefreshAccumulatorSeconds += InDeltaTime;
    if (RefreshAccumulatorSeconds >= 0.20f)
    {
        RefreshAccumulatorSeconds = 0.0f;
        RefreshFromRuntime();
    }
}

void ULBBodyShopPrototypeRootWidget::BuildShell()
{
    if (!WidgetTree || WidgetTree->RootWidget) return;

    UOverlay* Root = WidgetTree->ConstructWidget<UOverlay>(
        UOverlay::StaticClass(), TEXT("BodyShopPrototypeRoot"));
    Root->SetVisibility(ESlateVisibility::SelfHitTestInvisible);
    WidgetTree->RootWidget = Root;

    UBorder* Header = WidgetTree->ConstructWidget<UBorder>(
        UBorder::StaticClass(), TEXT("BodyShopHeader"));
    Header->SetBrush(LBBodyShopPrototypeUI::RoundedBrush(
        LBBodyShopPrototypeUI::Ink, FLinearColor::Transparent, 0.0f, 0.0f));
    Header->SetPadding(FMargin(20.0f, 10.0f));
    UOverlaySlot* HeaderSlot = Root->AddChildToOverlay(Header);
    HeaderSlot->SetHorizontalAlignment(HAlign_Fill);
    HeaderSlot->SetVerticalAlignment(VAlign_Top);

    UHorizontalBox* HeaderRow = WidgetTree->ConstructWidget<UHorizontalBox>(
        UHorizontalBox::StaticClass(), TEXT("BodyShopHeaderRow"));
    Header->AddChild(HeaderRow);
    UTextBlock* Brand = LBBodyShopPrototypeUI::Text(WidgetTree,
        TEXT("BodyShopBrand"), TEXT("CAIRNWELL 2040  /  BODY SHOP"), 17,
        LBBodyShopPrototypeUI::OffWhite, true);
    UHorizontalBoxSlot* BrandSlot = HeaderRow->AddChildToHorizontalBox(Brand);
    BrandSlot->SetSize(FSlateChildSize(ESlateSizeRule::Fill));
    StageLabel = LBBodyShopPrototypeUI::Text(WidgetTree,
        TEXT("BodyShopStage"), TEXT("OFFLINE"), 15,
        LBBodyShopPrototypeUI::Green, true);
    HeaderRow->AddChildToHorizontalBox(StageLabel);

    USizeBox* PanelSize = WidgetTree->ConstructWidget<USizeBox>(
        USizeBox::StaticClass(), TEXT("BodyShopOperatorPanelSize"));
    PanelSize->SetWidthOverride(540.0f);
    UOverlaySlot* PanelOverlaySlot = Root->AddChildToOverlay(PanelSize);
    PanelOverlaySlot->SetHorizontalAlignment(HAlign_Left);
    PanelOverlaySlot->SetVerticalAlignment(VAlign_Bottom);
    PanelOverlaySlot->SetPadding(FMargin(24.0f, 0.0f, 0.0f, 24.0f));

    UBorder* Panel = WidgetTree->ConstructWidget<UBorder>(
        UBorder::StaticClass(), TEXT("BodyShopOperatorPanel"));
    Panel->SetBrush(LBBodyShopPrototypeUI::RoundedBrush(
        LBBodyShopPrototypeUI::Ink, LBBodyShopPrototypeUI::Stroke, 1.0f, 12.0f));
    Panel->SetPadding(FMargin(18.0f));
    PanelSize->AddChild(Panel);

    UVerticalBox* Stack = WidgetTree->ConstructWidget<UVerticalBox>(
        UVerticalBox::StaticClass(), TEXT("BodyShopOperatorStack"));
    Panel->AddChild(Stack);
    Stack->AddChildToVerticalBox(LBBodyShopPrototypeUI::Text(WidgetTree,
        TEXT("BodyShopOperatorTitle"), TEXT("Underbody pilot cell"), 22,
        LBBodyShopPrototypeUI::OffWhite, true));
    StatusLabel = LBBodyShopPrototypeUI::Text(WidgetTree,
        TEXT("BodyShopRuntimeStatus"), TEXT("Waiting for isolated runtime"), 14,
        LBBodyShopPrototypeUI::Muted);
    Stack->AddChildToVerticalBox(StatusLabel)->SetPadding(FMargin(0.0f, 5.0f, 0.0f, 0.0f));
    WIPLabel = LBBodyShopPrototypeUI::Text(WidgetTree,
        TEXT("BodyShopWIPStatus"), TEXT("WIP 0  /  ROBOTS 0"), 13,
        LBBodyShopPrototypeUI::Muted);
    Stack->AddChildToVerticalBox(WIPLabel)->SetPadding(FMargin(0.0f, 3.0f, 0.0f, 12.0f));

    UHorizontalBox* Actions = WidgetTree->ConstructWidget<UHorizontalBox>(
        UHorizontalBox::StaticClass(), TEXT("BodyShopPrimaryActions"));
    Stack->AddChildToVerticalBox(Actions);
    UTextBlock* PrimaryLabelWidget = nullptr;
    PrimaryActionButton = LBBodyShopPrototypeUI::Button(WidgetTree,
        TEXT("BodyShopStartPause"), PrimaryLabelWidget, TEXT("Start pilot cycle"), true);
    PrimaryActionLabel = PrimaryLabelWidget;
    UHorizontalBoxSlot* PrimarySlot = Actions->AddChildToHorizontalBox(PrimaryActionButton);
    PrimarySlot->SetSize(FSlateChildSize(ESlateSizeRule::Fill));
    PrimarySlot->SetPadding(FMargin(0.0f, 0.0f, 6.0f, 0.0f));
    PrimaryActionButton->OnClicked.AddDynamic(this,
        &ULBBodyShopPrototypeRootWidget::HandlePrimaryActionClicked);

    UTextBlock* ClearLabel = nullptr;
    ClearHeldButton = LBBodyShopPrototypeUI::Button(WidgetTree,
        TEXT("BodyShopClearHeld"), ClearLabel, TEXT("Release held unit"), false);
    UHorizontalBoxSlot* ClearSlot = Actions->AddChildToHorizontalBox(ClearHeldButton);
    ClearSlot->SetSize(FSlateChildSize(ESlateSizeRule::Fill));
    ClearSlot->SetPadding(FMargin(6.0f, 0.0f, 0.0f, 0.0f));
    ClearHeldButton->OnClicked.AddDynamic(this,
        &ULBBodyShopPrototypeRootWidget::HandleClearHeldClicked);

    UHorizontalBox* Secondary = WidgetTree->ConstructWidget<UHorizontalBox>(
        UHorizontalBox::StaticClass(), TEXT("BodyShopSecondaryActions"));
    Stack->AddChildToVerticalBox(Secondary)->SetPadding(FMargin(0.0f, 10.0f, 0.0f, 0.0f));
    UTextBlock* SaveLabel = nullptr;
    SaveButton = LBBodyShopPrototypeUI::Button(WidgetTree,
        TEXT("BodyShopSave"), SaveLabel, TEXT("Save"), false);
    UTextBlock* LoadLabel = nullptr;
    LoadButton = LBBodyShopPrototypeUI::Button(WidgetTree,
        TEXT("BodyShopLoad"), LoadLabel, TEXT("Load"), false);
    UTextBlock* SlotsLabel = nullptr;
    RobotSlotsButton = LBBodyShopPrototypeUI::Button(WidgetTree,
        TEXT("BodyShopRobotSlots"), SlotsLabel, TEXT("Robot slots"), false);
    for (UButton* ButtonWidget : {SaveButton.Get(), LoadButton.Get(), RobotSlotsButton.Get()})
    {
        UHorizontalBoxSlot* ActionSlot = Secondary->AddChildToHorizontalBox(ButtonWidget);
        ActionSlot->SetSize(FSlateChildSize(ESlateSizeRule::Fill));
        ActionSlot->SetPadding(FMargin(3.0f));
    }
    SaveButton->OnClicked.AddDynamic(this, &ULBBodyShopPrototypeRootWidget::HandleSaveClicked);
    LoadButton->OnClicked.AddDynamic(this, &ULBBodyShopPrototypeRootWidget::HandleLoadClicked);
    RobotSlotsButton->OnClicked.AddDynamic(this,
        &ULBBodyShopPrototypeRootWidget::HandleRobotSlotsClicked);

    LastActionLabel = LBBodyShopPrototypeUI::Text(WidgetTree,
        TEXT("BodyShopLastAction"), LastActionText, 12, LBBodyShopPrototypeUI::Muted);
    Stack->AddChildToVerticalBox(LastActionLabel)->SetPadding(FMargin(0.0f, 10.0f, 0.0f, 0.0f));
    Stack->AddChildToVerticalBox(LBBodyShopPrototypeUI::Text(WidgetTree,
        TEXT("BodyShopControlsHint"),
        TEXT("SPACE start/pause   F5 save   F9 load   T robot reach/sweep"),
        11, LBBodyShopPrototypeUI::Muted));
}

bool ULBBodyShopPrototypeRootWidget::HasRenderableShell() const
{
    return WidgetTree && WidgetTree->RootWidget && StageLabel && StatusLabel
        && WIPLabel && PrimaryActionButton && SaveButton && LoadButton
        && ClearHeldButton && RobotSlotsButton;
}

void ULBBodyShopPrototypeRootWidget::RefreshFromRuntime()
{
    ALBBodyShopPrototypeRuntime* Runtime = ResolveRuntime();
    if (!Runtime)
    {
        if (StageLabel) StageLabel->SetText(FText::FromString(TEXT("OFFLINE")));
        if (StatusLabel) StatusLabel->SetText(FText::FromString(
            TEXT("Waiting for isolated Body Shop runtime")));
        if (WIPLabel) WIPLabel->SetText(FText::FromString(TEXT("WIP 0  /  ROBOTS 0")));
        if (PrimaryActionButton) PrimaryActionButton->SetIsEnabled(false);
        if (SaveButton) SaveButton->SetIsEnabled(false);
        if (LoadButton) LoadButton->SetIsEnabled(false);
        if (ClearHeldButton) ClearHeldButton->SetIsEnabled(false);
        return;
    }

    const ELBBodyShopRuntimeStage Stage = Runtime->GetRuntimeStage();
    const bool bRunning = Runtime->IsSimulationRunning();
    if (StageLabel)
    {
        StageLabel->SetText(FText::FromString(
            LBBodyShopPrototypeUI::StageName(Stage).ToUpper()));
    }
    if (StatusLabel) StatusLabel->SetText(FText::FromString(Runtime->GetRuntimeStatusText()));
    if (WIPLabel)
    {
        WIPLabel->SetText(FText::FromString(FString::Printf(
            TEXT("WIP %d  /  VISIBLE %d  /  ROBOTS %d"),
            Runtime->GetActivePilotWIPCount(),
            Runtime->GetVisibleRuntimeWIPPresentationCount(),
            Runtime->GetSpawnedRobotCount())));
    }
    if (PrimaryActionLabel)
    {
        PrimaryActionLabel->SetText(FText::FromString(
            GetPrimaryActionLabel(Stage, bRunning)));
    }
    const bool bPausedActiveFlow = !bRunning && Runtime->GetActivePilotWIPCount() == 1
        && (Stage == ELBBodyShopRuntimeStage::TransferringStillage
            || Stage == ELBBodyShopRuntimeStage::PresentingPanel
            || Stage == ELBBodyShopRuntimeStage::WeldingUnderbody
            || Stage == ELBBodyShopRuntimeStage::ConveyingSkid
            || Stage == ELBBodyShopRuntimeStage::Inspecting);
    const bool bPrimaryAvailable = Runtime->IsRuntimeInitialised()
        && (bRunning || Stage == ELBBodyShopRuntimeStage::Ready || bPausedActiveFlow);
    if (PrimaryActionButton) PrimaryActionButton->SetIsEnabled(bPrimaryAvailable);
    if (SaveButton) SaveButton->SetIsEnabled(Runtime->IsRuntimeInitialised());
    if (LoadButton) LoadButton->SetIsEnabled(Runtime->IsRuntimeInitialised());
    if (ClearHeldButton)
    {
        ClearHeldButton->SetIsEnabled(Stage == ELBBodyShopRuntimeStage::OutputBlocked
            || Stage == ELBBodyShopRuntimeStage::QualityHold
            || Stage == ELBBodyShopRuntimeStage::Complete);
    }
}

void ULBBodyShopPrototypeRootWidget::SetLastAction(
    const FString& Message, const bool bError)
{
    LastActionText = Message.IsEmpty() ? TEXT("No status returned") : Message;
    if (LastActionLabel)
    {
        LastActionLabel->SetText(FText::FromString(LastActionText));
        LastActionLabel->SetColorAndOpacity(FSlateColor(
            bError ? LBBodyShopPrototypeUI::Red : LBBodyShopPrototypeUI::Green));
    }
}

ALBBodyShopPrototypeRuntime* ULBBodyShopPrototypeRootWidget::ResolveRuntime() const
{
    UWorld* World = GetWorld();
    if (!World) return nullptr;
    for (TActorIterator<ALBBodyShopPrototypeWorldBootstrap> It(World); It; ++It)
    {
        if (IsValid(*It) && !It->IsActorBeingDestroyed())
            return Cast<ALBBodyShopPrototypeRuntime>((*It)->GetRuntimeActor());
    }
    return nullptr;
}

ALBBodyShopManagementPawn* ULBBodyShopPrototypeRootWidget::ResolveManagementPawn() const
{
    return GetOwningPlayerPawn<ALBBodyShopManagementPawn>();
}

void ULBBodyShopPrototypeRootWidget::HandlePrimaryActionClicked()
{
    ALBBodyShopPrototypeRuntime* Runtime = ResolveRuntime();
    if (!Runtime) return SetLastAction(TEXT("Body Shop runtime is unavailable"), true);
    FString Reason;
    bool bSuccess = false;
    if (Runtime->IsSimulationRunning())
        bSuccess = Runtime->SetSimulationRunning(false, Reason);
    else if (Runtime->GetActivePilotWIPCount() > 0)
        bSuccess = Runtime->SetSimulationRunning(true, Reason);
    else
        bSuccess = Runtime->StartPilotCycle(Reason);
    SetLastAction(Reason, !bSuccess);
    RefreshFromRuntime();
}

void ULBBodyShopPrototypeRootWidget::HandleSaveClicked()
{
    ALBBodyShopPrototypeRuntime* Runtime = ResolveRuntime();
    if (!Runtime) return SetLastAction(TEXT("Body Shop runtime is unavailable"), true);
    FString Reason;
    const bool bSuccess = Runtime->SaveToExperimentalSlot(Reason);
    SetLastAction(Reason, !bSuccess);
}

void ULBBodyShopPrototypeRootWidget::HandleLoadClicked()
{
    ALBBodyShopPrototypeRuntime* Runtime = ResolveRuntime();
    if (!Runtime) return SetLastAction(TEXT("Body Shop runtime is unavailable"), true);
    FString Reason;
    const bool bSuccess = Runtime->LoadFromExperimentalSlot(Reason);
    SetLastAction(Reason, !bSuccess);
    RefreshFromRuntime();
}

void ULBBodyShopPrototypeRootWidget::HandleClearHeldClicked()
{
    ALBBodyShopPrototypeRuntime* Runtime = ResolveRuntime();
    if (!Runtime) return SetLastAction(TEXT("Body Shop runtime is unavailable"), true);
    FString Reason;
    const bool bSuccess = Runtime->ReleaseHeldPilotUnit(Reason);
    SetLastAction(Reason, !bSuccess);
    RefreshFromRuntime();
}

void ULBBodyShopPrototypeRootWidget::HandleRobotSlotsClicked()
{
    ALBBodyShopManagementPawn* Pawn = ResolveManagementPawn();
    if (!Pawn) return SetLastAction(TEXT("Management camera is unavailable"), true);
    Pawn->ToggleRobotSlotOverlay();
    SetLastAction(Pawn->IsRobotSlotOverlayRequested()
        ? TEXT("Robot reach and sweep overlays enabled")
        : TEXT("Robot reach and sweep overlays hidden"), false);
}
