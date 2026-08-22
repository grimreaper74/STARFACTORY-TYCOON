#include "LBManagementRootWidget.h"

#include "Blueprint/WidgetTree.h"
#include "Brushes/SlateRoundedBoxBrush.h"
#include "Components/Border.h"
#include "Components/Button.h"
#include "Components/ButtonSlot.h"
#include "Components/CanvasPanel.h"
#include "Components/CanvasPanelSlot.h"
#include "Components/HorizontalBox.h"
#include "Components/HorizontalBoxSlot.h"
#include "Components/Image.h"
#include "Components/Overlay.h"
#include "Components/OverlaySlot.h"
#include "Components/ProgressBar.h"
#include "Components/ScaleBox.h"
#include "Components/SizeBox.h"
#include "Components/Spacer.h"
#include "Components/TextBlock.h"
#include "Components/VerticalBox.h"
#include "Components/VerticalBoxSlot.h"
#include "Fonts/SlateFontInfo.h"
#include "Engine/Texture2D.h"
#include "InputCoreTypes.h"
#include "LBFactoryBrandSubsystem.h"
#include "Styling/CoreStyle.h"

namespace LBManagementShell
{
    constexpr float DesignWidth = 1920.0f;
    constexpr float DesignHeight = 1080.0f;
    // Linear-space colours measured from the selected mock-up. Keeping these
    // values genuinely dark avoids the medium-grey gamma lift seen in v006.
    const FLinearColor Ink(0.0065f, 0.0100f, 0.0120f, 0.985f);
    const FLinearColor InkSoft(0.0110f, 0.0170f, 0.0200f, 0.985f);
    const FLinearColor Card(0.0200f, 0.0290f, 0.0330f, 0.99f);
    const FLinearColor CardHover(0.0320f, 0.0450f, 0.0500f, 1.0f);
    const FLinearColor Stroke(0.036f, 0.052f, 0.060f, 0.90f);
    const FLinearColor OffWhite(0.91f, 0.92f, 0.89f, 1.0f);
    const FLinearColor Muted(0.58f, 0.63f, 0.63f, 1.0f);
    const FLinearColor Green(0.030f, 0.64f, 0.235f, 1.0f);
    const FLinearColor GreenDark(0.008f, 0.110f, 0.050f, 1.0f);
    const FLinearColor Amber(1.0f, 0.69f, 0.12f, 1.0f);
    const FLinearColor Red(0.95f, 0.20f, 0.16f, 1.0f);
    const FLinearColor Disabled(0.29f, 0.33f, 0.33f, 1.0f);

    const FName StageIds[] = {
        TEXT("COIL_INTAKE"), TEXT("BLANK_BUFFER"), TEXT("TRANSFER_PRESS"),
        TEXT("PANEL_STILLAGES"), TEXT("BODY_WELD"), TEXT("ED_COAT")};
    const TCHAR* StageNames[] = {
        TEXT("Coil intake"), TEXT("Blank buffer"), TEXT("Transfer press"),
        TEXT("Panel stillages"), TEXT("Body weld"), TEXT("ED coat")};
    const FName DestinationIds[] = {
        TEXT("FACTORY"), TEXT("BUILD"), TEXT("ORDERS"), TEXT("ASSETS"),
        TEXT("MAINTENANCE"), TEXT("RESEARCH"), TEXT("ANALYTICS")};
    const TCHAR* DestinationLabels[] = {
        TEXT("Factory"), TEXT("Build"), TEXT("Orders"), TEXT("Assets"),
        TEXT("Maint."), TEXT("Research"), TEXT("Analytics")};

    FSlateFontInfo Font(const int32 Size, const bool bBold = false)
    {
        return FSlateFontInfo(FCoreStyle::GetDefaultFontStyle(
            bBold ? TEXT("Bold") : TEXT("Regular"), Size));
    }

    FSlateBrush RoundedBrush(const FLinearColor Fill, const FLinearColor Outline,
        const float OutlineWidth = 1.0f, const float Radius = 10.0f)
    {
        FSlateRoundedBoxBrush Brush(Fill,
            FVector4(Radius, Radius, Radius, Radius), Outline, OutlineWidth);
        return Brush;
    }

    FButtonStyle ButtonStyle(const FLinearColor Normal, const FLinearColor Hover,
        const FLinearColor Pressed, const FLinearColor Outline,
        const float Radius = 8.0f)
    {
        FButtonStyle Style;
        Style.SetNormal(RoundedBrush(Normal, Outline, 1.0f, Radius));
        Style.SetHovered(RoundedBrush(Hover, Green, 1.5f, Radius));
        Style.SetPressed(RoundedBrush(Pressed, Green, 2.0f, Radius));
        Style.SetDisabled(RoundedBrush(Disabled.CopyWithNewOpacity(0.65f),
            Stroke, 1.0f, Radius));
        Style.SetNormalPadding(FMargin(0.0f));
        Style.SetPressedPadding(FMargin(1.0f, 2.0f, 0.0f, 0.0f));
        return Style;
    }

    // Navigation belongs to the persistent shell, not to a stack of legacy
    // command buttons.  Keep the resting state deliberately quiet and reveal
    // the control only through the focused/hovered state.
    FButtonStyle NavigationStyle()
    {
        FButtonStyle Style;
        Style.SetNormal(RoundedBrush(FLinearColor::Transparent,
            FLinearColor::Transparent, 0.0f, 16.0f));
        Style.SetHovered(RoundedBrush(InkSoft, Green, 1.0f, 16.0f));
        Style.SetPressed(RoundedBrush(GreenDark, Green, 1.5f, 16.0f));
        Style.SetDisabled(RoundedBrush(FLinearColor::Transparent,
            FLinearColor::Transparent, 0.0f, 16.0f));
        Style.SetNormalPadding(FMargin(0.0f));
        Style.SetPressedPadding(FMargin(0.0f));
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

    USizeBox* FixedSize(UWidgetTree* Tree, const FName Name,
        const float Width, const float Height)
    {
        USizeBox* Box = Tree->ConstructWidget<USizeBox>(USizeBox::StaticClass(), Name);
        Box->SetWidthOverride(Width);
        Box->SetHeightOverride(Height);
        return Box;
    }

    FString FormatMoney(const int64 Pence)
    {
        const double Pounds = static_cast<double>(Pence) / 100.0;
        if (FMath::Abs(Pounds) >= 1000000.0)
            return FString::Printf(TEXT("£%.2fm"), Pounds / 1000000.0);
        if (FMath::Abs(Pounds) >= 1000.0)
            return FString::Printf(TEXT("£%.1fk"), Pounds / 1000.0);
        return FString::Printf(TEXT("£%.0f"), Pounds);
    }
}

FLBManagementShellLayoutMetrics ULBManagementRootWidget::CalculateLayoutMetrics(
    const FVector2D ViewportSize)
{
    FLBManagementShellLayoutMetrics Result;
    Result.ViewportSize = FVector2D(FMath::Max(ViewportSize.X, 1.0f),
        FMath::Max(ViewportSize.Y, 1.0f));
    Result.UIScale = FMath::Clamp(FMath::Min(
        Result.ViewportSize.X / LBManagementShell::DesignWidth,
        Result.ViewportSize.Y / LBManagementShell::DesignHeight), 2.0f / 3.0f, 1.35f);
    Result.bCompact = Result.ViewportSize.X < 1500.0f || Result.ViewportSize.Y < 850.0f;
    // The live hierarchy is one uniformly scaled 1920 x 1080 design canvas.
    // Report the exact rendered sizes rather than a second compact layout that
    // would disagree with the ScaleBox geometry.
    Result.TopStripHeight = 72.0f * Result.UIScale;
    Result.FlowTrayHeight = 344.0f * Result.UIScale;
    Result.OuterMargin = 32.0f * Result.UIScale;
    Result.DetailWidth = 354.0f * Result.UIScale;
    Result.FlowTrayBottomMargin = DesignFlowTrayBottomMargin * Result.UIScale;
    Result.SurfaceCornerRadius = DesignSurfaceCornerRadius * Result.UIScale;
    return Result;
}

TArray<FName> ULBManagementRootWidget::GetCanonicalProductionStageIds()
{
    return TArray<FName>(LBManagementShell::StageIds,
        UE_ARRAY_COUNT(LBManagementShell::StageIds));
}

TArray<FName> ULBManagementRootWidget::GetCanonicalManagementDestinationIds()
{
    return TArray<FName>(LBManagementShell::DestinationIds,
        UE_ARRAY_COUNT(LBManagementShell::DestinationIds));
}

FSoftObjectPath ULBManagementRootWidget::GetStageThumbnailPath(const FName StageId)
{
    // Production cards deliberately use the native schematic beneath their
    // live state data.  Do not soft-load historical imported thumbnails here:
    // keeping this null makes a development or shipping cook independent of
    // that third-party image pack.
    (void)StageId;
    return FSoftObjectPath();
}

FSoftObjectPath ULBManagementRootWidget::GetBrandLogoPath()
{
    return FSoftObjectPath(TEXT("/Game/LineBoss/Brand/Cairnwell/Candidate_v002/T_Cairnwell_PrimaryLogo_v002.T_Cairnwell_PrimaryLogo_v002"));
}

bool ULBManagementRootWidget::ShouldShowStageStatusDot(
    const FLBManagementStagePresentation& Stage)
{
    return Stage.bInstalled;
}

bool ULBManagementRootWidget::ShouldHighlightStageConnector(
    const FLBManagementStagePresentation& Upstream,
    const FLBManagementStagePresentation& Downstream)
{
    return Upstream.bInstalled && Downstream.bInstalled;
}

bool ULBManagementRootWidget::HasTruthfulThroughput(
    const double GoodUnitsPerHour)
{
    return GoodUnitsPerHour > KINDA_SMALL_NUMBER;
}

bool ULBManagementRootWidget::IsReservedGameplayKey(const FKey& Key)
{
    return Key == EKeys::W || Key == EKeys::A || Key == EKeys::S
        || Key == EKeys::D || Key == EKeys::Q || Key == EKeys::E
        || Key == EKeys::SpaceBar || Key == EKeys::Home;
}

TSharedRef<SWidget> ULBManagementRootWidget::RebuildWidget()
{
    // UUserWidget resolves WidgetTree->RootWidget before NativeConstruct. Build
    // here so the viewport receives the modern shell itself, not the empty-tree
    // spacer that leaves the legacy Canvas HUD visible underneath.
    SetIsFocusable(true);
    BuildCanonicalPresentations();
    BuildShell();
    return Super::RebuildWidget();
}

void ULBManagementRootWidget::NativeOnInitialized()
{
    Super::NativeOnInitialized();
    SetIsFocusable(true);
    BuildCanonicalPresentations();
    // Build the native tree before RebuildWidget asks WidgetTree for its root.
    // Creating it later in NativeConstruct leaves Slate hosting the fallback
    // spacer that was produced for an empty tree, even though this UObject tree
    // then exists and reports itself visible.
    BuildShell();
}

void ULBManagementRootWidget::NativeConstruct()
{
    Super::NativeConstruct();
    // These six small UI textures are the selected production-flow art authority.
    // Resolve them once on construction so a cold packaged launch never presents
    // an "art pending" shell merely because nothing else happened to cache them.
    ReloadStageThumbnails();
    RefreshFromFactoryState(true);
    ConfigureFocusNavigation();
    if (StageButtons.IsValidIndex(SelectedStageIndex))
        StageButtons[SelectedStageIndex]->SetKeyboardFocus();
}

void ULBManagementRootWidget::NativeTick(const FGeometry& MyGeometry,
    const float InDeltaTime)
{
    Super::NativeTick(MyGeometry, InDeltaTime);
    RefreshAccumulator += InDeltaTime;
    if (RefreshAccumulator >= RefreshPeriodSeconds)
    {
        RefreshAccumulator = 0.0f;
        RefreshFromFactoryState(false);
    }

    const FVector2D ViewportSize = MyGeometry.GetLocalSize();
    if (!ViewportSize.Equals(LastViewportSize, 1.0f))
        UpdateResponsiveLayout(ViewportSize);
}

FReply ULBManagementRootWidget::NativeOnKeyDown(const FGeometry& InGeometry,
    const FKeyEvent& InKeyEvent)
{
    const FKey Key = InKeyEvent.GetKey();
    // This widget can receive focus after a mouse click. Keep the documented
    // factory controls unhandled so the player controller receives them.
    if (IsReservedGameplayKey(Key))
        return FReply::Unhandled();
    if (Key == EKeys::F10 || Key == EKeys::Gamepad_Special_Right)
    {
        RequestDestination(TEXT("SETTINGS"));
        return FReply::Handled();
    }
    // Keep the mouse-first management shell from stealing the factory camera
    // controls. A/D and Space are documented gameplay inputs (pan and pause),
    // so the UI navigation route is deliberately arrows/Enter only.
    if (Key == EKeys::Left
        || Key == EKeys::Gamepad_DPad_Left || Key == EKeys::Gamepad_LeftStick_Left)
    {
        SelectRelativeProductionStage(-1, true);
        return FReply::Handled();
    }
    if (Key == EKeys::Right
        || Key == EKeys::Gamepad_DPad_Right || Key == EKeys::Gamepad_LeftStick_Right)
    {
        SelectRelativeProductionStage(1, true);
        return FReply::Handled();
    }
    if (Key == EKeys::Enter
        || Key == EKeys::Virtual_Gamepad_Accept.GetVirtualKey()
        || Key == EKeys::Gamepad_FaceButton_Bottom)
    {
        ActivateSelectedStage();
        return FReply::Handled();
    }
    return Super::NativeOnKeyDown(InGeometry, InKeyEvent);
}

void ULBManagementRootWidget::BuildCanonicalPresentations()
{
    PresentedStages.Reset(ProductionStageCount);
    for (int32 Index = 0; Index < ProductionStageCount; ++Index)
    {
        FLBManagementStagePresentation& Stage = PresentedStages.AddDefaulted_GetRef();
        Stage.StageId = LBManagementShell::StageIds[Index];
        Stage.DisplayName = FText::FromString(LBManagementShell::StageNames[Index]);
        Stage.Thumbnail = TSoftObjectPtr<UTexture2D>(GetStageThumbnailPath(Stage.StageId));
        Stage.StateText = FText::FromString(TEXT("NOT INSTALLED"));
        Stage.DetailText = FText::FromString(TEXT("PLACE THIS PROCESS ASSET"));
        Stage.bThumbnailAvailable = Stage.Thumbnail.Get() != nullptr;
    }
}

void ULBManagementRootWidget::BuildShell()
{
    if (!WidgetTree || WidgetTree->RootWidget) return;

    RootCanvas = WidgetTree->ConstructWidget<UCanvasPanel>(
        UCanvasPanel::StaticClass(), TEXT("LBManagementRoot"));
    WidgetTree->RootWidget = RootCanvas;

    // Author the shell once in the selected mock-up's 1920 x 1080 design space,
    // then scale it uniformly. This keeps every card, aperture and hit target in
    // the same relationship at 720p and 1080p instead of clipping fixed children
    // inside independently resized parent panels.
    ShellScaleBox = WidgetTree->ConstructWidget<UScaleBox>(
        UScaleBox::StaticClass(), TEXT("ManagementShellScale"));
    ShellScaleBox->SetStretch(EStretch::ScaleToFit);
    ShellScaleBox->SetStretchDirection(EStretchDirection::Both);
    UCanvasPanelSlot* ScaleSlot = RootCanvas->AddChildToCanvas(ShellScaleBox);
    ScaleSlot->SetAnchors(FAnchors(0.0f, 0.0f, 1.0f, 1.0f));
    ScaleSlot->SetOffsets(FMargin(0.0f));

    USizeBox* DesignSize = LBManagementShell::FixedSize(
        WidgetTree, TEXT("ManagementDesignSize"),
        LBManagementShell::DesignWidth, LBManagementShell::DesignHeight);
    ShellScaleBox->AddChild(DesignSize);
    DesignCanvas = WidgetTree->ConstructWidget<UCanvasPanel>(
        UCanvasPanel::StaticClass(), TEXT("ManagementDesignCanvas"));
    DesignSize->AddChild(DesignCanvas);

    BuildTopCommandStrip(DesignCanvas);
    BuildProductionFlow(DesignCanvas);
    BuildManagementContext(DesignCanvas);
    UpdateResponsiveLayout(FVector2D(LBManagementShell::DesignWidth,
        LBManagementShell::DesignHeight));
}

void ULBManagementRootWidget::BuildManagementContext(UCanvasPanel* Canvas)
{
    ContextBorder = WidgetTree->ConstructWidget<UBorder>(
        UBorder::StaticClass(), TEXT("ManagementContextPanel"));
    ContextBorder->SetBrush(LBManagementShell::RoundedBrush(
        LBManagementShell::Ink, LBManagementShell::Stroke, 1.2f,
        DesignSurfaceCornerRadius));
    ContextBorder->SetPadding(FMargin(32.0f, 26.0f));
    ContextBorder->SetVisibility(ESlateVisibility::Collapsed);
    UCanvasPanelSlot* ContextSlot = Canvas->AddChildToCanvas(ContextBorder);
    ContextSlot->SetAnchors(FAnchors(0.0f, 1.0f, 1.0f, 1.0f));
    ContextSlot->SetAlignment(FVector2D(0.0f, 1.0f));
    ContextSlot->SetOffsets(FMargin(32.0f, -40.0f, 32.0f, 344.0f));

    UVerticalBox* Stack = WidgetTree->ConstructWidget<UVerticalBox>(
        UVerticalBox::StaticClass(), TEXT("ManagementContextStack"));
    ContextBorder->AddChild(Stack);
    ContextTitleLabel = LBManagementShell::Text(WidgetTree,
        TEXT("ManagementContextTitle"), TEXT("Build factory"), 26,
        LBManagementShell::OffWhite, true);
    Stack->AddChildToVerticalBox(ContextTitleLabel)->SetPadding(
        FMargin(0.0f, 0.0f, 0.0f, 8.0f));
    ContextSummaryLabel = LBManagementShell::Text(WidgetTree,
        TEXT("ManagementContextSummary"), TEXT("Choose a factory asset."), 15,
        LBManagementShell::Muted, false);
    ContextSummaryLabel->SetAutoWrapText(true);
    Stack->AddChildToVerticalBox(ContextSummaryLabel)->SetPadding(
        FMargin(0.0f, 0.0f, 0.0f, 20.0f));

    UHorizontalBox* Actions = WidgetTree->ConstructWidget<UHorizontalBox>(
        UHorizontalBox::StaticClass(), TEXT("ManagementContextActions"));
    Stack->AddChildToVerticalBox(Actions)->SetSize(
        FSlateChildSize(ESlateSizeRule::Fill));
    for (int32 Index = 0; Index < 5; ++Index)
    {
        UButton* Button = WidgetTree->ConstructWidget<UButton>(UButton::StaticClass(),
            *FString::Printf(TEXT("ManagementContextAction_%d"), Index));
        Button->SetStyle(LBManagementShell::ButtonStyle(
            LBManagementShell::Card, LBManagementShell::CardHover,
            LBManagementShell::GreenDark, LBManagementShell::Stroke, 8.0f));
        ContextActionButtons.Add(Button);
        UHorizontalBoxSlot* ButtonSlot = Actions->AddChildToHorizontalBox(Button);
        ButtonSlot->SetSize(FSlateChildSize(ESlateSizeRule::Fill));
        ButtonSlot->SetPadding(FMargin(Index == 0 ? 0.0f : 5.0f, 0.0f,
            Index == 4 ? 0.0f : 5.0f, 0.0f));
        UBorder* Card = WidgetTree->ConstructWidget<UBorder>(UBorder::StaticClass(),
            *FString::Printf(TEXT("ManagementContextCard_%d"), Index));
        Card->SetBrush(LBManagementShell::RoundedBrush(
            LBManagementShell::Card, LBManagementShell::Stroke, 1.0f, 8.0f));
        Card->SetPadding(FMargin(14.0f, 14.0f));
        if (UButtonSlot* CardSlot = Cast<UButtonSlot>(Button->AddChild(Card)))
        {
            CardSlot->SetHorizontalAlignment(HAlign_Fill);
            CardSlot->SetVerticalAlignment(VAlign_Fill);
        }
        UVerticalBox* CardStack = WidgetTree->ConstructWidget<UVerticalBox>(
            UVerticalBox::StaticClass(), *FString::Printf(TEXT("ManagementContextCardStack_%d"), Index));
        Card->AddChild(CardStack);
        UTextBlock* Title = LBManagementShell::Text(WidgetTree,
            *FString::Printf(TEXT("ManagementContextActionTitle_%d"), Index),
            TEXT("No action"), 17, LBManagementShell::OffWhite, true);
        Title->SetAutoWrapText(true);
        ContextActionTitles.Add(Title);
        CardStack->AddChildToVerticalBox(Title);
        UTextBlock* Detail = LBManagementShell::Text(WidgetTree,
            *FString::Printf(TEXT("ManagementContextActionDetail_%d"), Index),
            TEXT(""), 13, LBManagementShell::Muted, false);
        Detail->SetAutoWrapText(true);
        ContextActionDetails.Add(Detail);
        CardStack->AddChildToVerticalBox(Detail)->SetPadding(FMargin(0.0f, 10.0f, 0.0f, 0.0f));
        Button->SetVisibility(ESlateVisibility::Collapsed);
        if (Index == 0) Button->OnClicked.AddDynamic(this, &ULBManagementRootWidget::OnContextAction0Clicked);
        else if (Index == 1) Button->OnClicked.AddDynamic(this, &ULBManagementRootWidget::OnContextAction1Clicked);
        else if (Index == 2) Button->OnClicked.AddDynamic(this, &ULBManagementRootWidget::OnContextAction2Clicked);
        else if (Index == 3) Button->OnClicked.AddDynamic(this, &ULBManagementRootWidget::OnContextAction3Clicked);
        else Button->OnClicked.AddDynamic(this, &ULBManagementRootWidget::OnContextAction4Clicked);
    }
}

void ULBManagementRootWidget::BuildTopCommandStrip(UCanvasPanel* Canvas)
{
    TopStripSizeBox = LBManagementShell::FixedSize(
        WidgetTree, TEXT("TopCommandStripSize"),
        LBManagementShell::DesignWidth, 72.0f);
    TopStripSizeBox->ClearWidthOverride();
    UCanvasPanelSlot* StripSlot = Canvas->AddChildToCanvas(TopStripSizeBox);
    StripSlot->SetAnchors(FAnchors(0.0f, 0.0f, 1.0f, 0.0f));
    StripSlot->SetOffsets(FMargin(0.0f, 0.0f, 0.0f, 72.0f));

    UBorder* Strip = WidgetTree->ConstructWidget<UBorder>(
        UBorder::StaticClass(), TEXT("TopCommandStrip"));
    Strip->SetBrush(LBManagementShell::RoundedBrush(
        LBManagementShell::Ink, LBManagementShell::Stroke, 1.0f, 0.0f));
    Strip->SetPadding(FMargin(20.0f, 10.0f));
    TopStripSizeBox->AddChild(Strip);

    UHorizontalBox* Row = WidgetTree->ConstructWidget<UHorizontalBox>(
        UHorizontalBox::StaticClass(), TEXT("TopCommandRow"));
    Strip->AddChild(Row);

    USizeBox* BrandBox = LBManagementShell::FixedSize(
        WidgetTree, TEXT("BrandBlock"), 246.0f, 52.0f);
    UHorizontalBoxSlot* BrandSlot = Row->AddChildToHorizontalBox(BrandBox);
    BrandSlot->SetVerticalAlignment(VAlign_Center);
    // The supplied print logo is intentionally near-black and becomes an
    // unreadable smudge on a dark operations shell.  Use the actual brand name
    // as the persistent navigation mark; the full logo remains available in
    // appearance/brand views where its artwork can be shown at a useful size.
    UVerticalBox* BrandStack = WidgetTree->ConstructWidget<UVerticalBox>(
        UVerticalBox::StaticClass(), TEXT("CairnwellWordmark"));
    BrandBox->AddChild(BrandStack);
    UTextBlock* BrandName = LBManagementShell::Text(WidgetTree,
        TEXT("CairnwellWordmarkName"), TEXT("CAIRNWELL"), 18,
        LBManagementShell::OffWhite, true);
    BrandName->SetToolTipText(FText::FromString(TEXT("Cairnwell Automotive")));
    BrandStack->AddChildToVerticalBox(BrandName)->SetPadding(FMargin(0.0f, 5.0f, 0.0f, 0.0f));
    UTextBlock* BrandDescriptor = LBManagementShell::Text(WidgetTree,
        TEXT("CairnwellWordmarkDescriptor"), TEXT("AUTOMOTIVE SYSTEMS"), 8,
        LBManagementShell::Green, true);
    BrandStack->AddChildToVerticalBox(BrandDescriptor);

    // Keep the native shell intentionally bounded: these are the three pages
    // required to build and run OneFactory plus its real Settings overlay. The
    // remaining legacy destinations retain their canonical routing IDs, but are
    // not duplicated here as a second full-width navigation system.
    auto AddDestinationButton = [this, Row](const FName SizeName,
        const FName ButtonName, const FName LabelName, const FString& Label,
        const float Width, const FString& ToolTip)
    {
        USizeBox* ButtonBox = LBManagementShell::FixedSize(
            WidgetTree, SizeName, Width, 34.0f);
        UHorizontalBoxSlot* NavigationSlot =
            Row->AddChildToHorizontalBox(ButtonBox);
        NavigationSlot->SetPadding(FMargin(2.0f, 0.0f));
        NavigationSlot->SetVerticalAlignment(VAlign_Center);

        UButton* Button = WidgetTree->ConstructWidget<UButton>(
            UButton::StaticClass(), ButtonName);
        Button->SetStyle(LBManagementShell::NavigationStyle());
        // UButton is focusable by default; keep that constructor contract intact
        // so keyboard and controller navigation can enter this command strip.
        Button->SetToolTipText(FText::FromString(ToolTip));
        UTextBlock* ButtonLabel = LBManagementShell::Text(WidgetTree,
            LabelName, Label, 10, LBManagementShell::OffWhite, true);
        ButtonLabel->SetJustification(ETextJustify::Center);
        Button->AddChild(ButtonLabel);
        ButtonBox->AddChild(Button);
        TopDestinationButtons.Add(Button);
        return Button;
    };

    UButton* BuildButton = AddDestinationButton(TEXT("BuildDestinationSize"),
        TEXT("Destination_BUILD"), TEXT("DestinationBuildLabel"),
        TEXT("BUILD"), 74.0f,
        TEXT("Build and commission factory departments and stations"));
    BuildButton->OnClicked.AddDynamic(
        this, &ULBManagementRootWidget::OnBuildDestinationClicked);

    // Production deliberately requests ORDERS: that stable destination is the
    // existing HUD route to ELBManagementPage::Production and now projects the
    // five authoritative OneFactory vehicle actions when that world is active.
    UButton* ProductionButton = AddDestinationButton(
        TEXT("ProductionDestinationSize"), TEXT("Destination_ORDERS"),
        TEXT("DestinationProductionLabel"), TEXT("PRODUCTION"), 104.0f,
        TEXT("Create vehicles and operate the live production route"));
    ProductionButton->OnClicked.AddDynamic(
        this, &ULBManagementRootWidget::OnOrdersDestinationClicked);

    UButton* AnalyticsButton = AddDestinationButton(
        TEXT("AnalyticsDestinationSize"), TEXT("Destination_ANALYTICS"),
        TEXT("DestinationAnalyticsLabel"), TEXT("ANALYTICS"), 94.0f,
        TEXT("Review factory results and access OneFactory save / load"));
    AnalyticsButton->OnClicked.AddDynamic(
        this, &ULBManagementRootWidget::OnAnalyticsDestinationClicked);

    UButton* SettingsButton = AddDestinationButton(
        TEXT("SettingsDestinationSize"), TEXT("Destination_SETTINGS"),
        TEXT("DestinationSettingsLabel"), TEXT("SETTINGS"), 86.0f,
        TEXT("Open graphics, display and factory appearance settings"));
    SettingsButton->OnClicked.AddDynamic(
        this, &ULBManagementRootWidget::OnSettingsDestinationClicked);

    USizeBox* OrderBox = LBManagementShell::FixedSize(
        WidgetTree, TEXT("OrderBlock"), 236.0f, 52.0f);
    UHorizontalBoxSlot* OrderSlot = Row->AddChildToHorizontalBox(OrderBox);
    OrderSlot->SetPadding(FMargin(10.0f, 0.0f, 4.0f, 0.0f));
    OrderLabel = LBManagementShell::Text(WidgetTree, TEXT("OrderLabel"),
        TEXT("CAIRNWELL 2040   0 / 0 issued"), 14,
        LBManagementShell::OffWhite, true);
    OrderLabel->SetJustification(ETextJustify::Center);
    OrderBox->AddChild(OrderLabel);

    USizeBox* CashBox = LBManagementShell::FixedSize(
        WidgetTree, TEXT("CashBlock"), 108.0f, 52.0f);
    UHorizontalBoxSlot* CashSlot = Row->AddChildToHorizontalBox(CashBox);
    CashSlot->SetPadding(FMargin(5.0f, 0.0f));
    CashLabel = LBManagementShell::Text(WidgetTree, TEXT("CashLabel"),
        TEXT("£0"), 16, LBManagementShell::OffWhite, true);
    CashLabel->SetJustification(ETextJustify::Center);
    CashBox->AddChild(CashLabel);

    USpacer* RightPush = WidgetTree->ConstructWidget<USpacer>(
        USpacer::StaticClass(), TEXT("AlertRightAlignmentSpacer"));
    UHorizontalBoxSlot* RightPushSlot = Row->AddChildToHorizontalBox(RightPush);
    RightPushSlot->SetSize(FSlateChildSize(ESlateSizeRule::Fill));

    auto AddSimulationButton = [this, Row](const FName SizeName,
        const FName ButtonName, const FName LabelName, const FString& Label,
        const float Width, const FString& ToolTip)
    {
        USizeBox* ButtonBox = LBManagementShell::FixedSize(
            WidgetTree, SizeName, Width, 34.0f);
        UHorizontalBoxSlot* ButtonSlot = Row->AddChildToHorizontalBox(ButtonBox);
        ButtonSlot->SetPadding(FMargin(2.0f, 0.0f));
        ButtonSlot->SetVerticalAlignment(VAlign_Center);

        UButton* Button = WidgetTree->ConstructWidget<UButton>(
            UButton::StaticClass(), ButtonName);
        Button->SetStyle(LBManagementShell::ButtonStyle(
            LBManagementShell::Card, LBManagementShell::CardHover,
            LBManagementShell::GreenDark, LBManagementShell::Stroke, 7.0f));
        // UButton is focusable by default; do not replace it with a passive label.
        Button->SetToolTipText(FText::FromString(ToolTip));
        UTextBlock* ButtonLabel = LBManagementShell::Text(WidgetTree,
            LabelName, Label, 9, LBManagementShell::OffWhite, true);
        ButtonLabel->SetJustification(ETextJustify::Center);
        Button->AddChild(ButtonLabel);
        ButtonBox->AddChild(Button);
        SimulationRateButtons.Add(Button);
        return Button;
    };

    UButton* PauseButton = AddSimulationButton(TEXT("SimulationPauseSize"),
        TEXT("Simulation_PAUSE"), TEXT("SimulationPauseLabel"),
        TEXT("PAUSE"), 62.0f, TEXT("Pause OneFactory simulation"));
    PauseButton->OnClicked.AddDynamic(
        this, &ULBManagementRootWidget::OnPauseClicked);
    UButton* PlayButton = AddSimulationButton(TEXT("SimulationPlaySize"),
        TEXT("Simulation_PLAY"), TEXT("SimulationPlayLabel"),
        TEXT("PLAY"), 54.0f, TEXT("Run OneFactory simulation at normal speed"));
    PlayButton->OnClicked.AddDynamic(
        this, &ULBManagementRootWidget::OnPlayClicked);
    UButton* FastForwardButton = AddSimulationButton(
        TEXT("SimulationFastForwardSize"), TEXT("Simulation_FAST_FORWARD"),
        TEXT("SimulationFastForwardLabel"), TEXT("2X"), 50.0f,
        TEXT("Run OneFactory simulation at double speed"));
    FastForwardButton->OnClicked.AddDynamic(
        this, &ULBManagementRootWidget::OnFastForwardClicked);

    USizeBox* AlertBox = LBManagementShell::FixedSize(
        WidgetTree, TEXT("AlertBlock"), 186.0f, 52.0f);
    UHorizontalBoxSlot* AlertSlot = Row->AddChildToHorizontalBox(AlertBox);
    AlertSlot->SetPadding(FMargin(10.0f, 0.0f, 0.0f, 0.0f));
    AlertLabel = LBManagementShell::Text(WidgetTree, TEXT("AlertLabel"),
        TEXT("No alerts"), 14, LBManagementShell::Muted, true);
    AlertLabel->SetJustification(ETextJustify::Right);
    AlertBox->AddChild(AlertLabel);
}

void ULBManagementRootWidget::BuildProductionFlow(UCanvasPanel* Canvas)
{
    FlowTraySizeBox = LBManagementShell::FixedSize(
        WidgetTree, TEXT("ProductionFlowTraySize"),
        1856.0f, 344.0f);
    FlowTraySizeBox->ClearWidthOverride();
    UCanvasPanelSlot* TraySlot = Canvas->AddChildToCanvas(FlowTraySizeBox);
    TraySlot->SetAnchors(FAnchors(0.0f, 1.0f, 1.0f, 1.0f));
    TraySlot->SetAlignment(FVector2D(0.0f, 1.0f));
    TraySlot->SetOffsets(FMargin(32.0f, -DesignFlowTrayBottomMargin,
        32.0f, 344.0f));

    FlowTrayBorder = WidgetTree->ConstructWidget<UBorder>(
        UBorder::StaticClass(), TEXT("ProductionFlowTray"));
    FlowTrayBorder->SetBrush(LBManagementShell::RoundedBrush(
        LBManagementShell::Ink, LBManagementShell::Stroke, 1.2f,
        DesignSurfaceCornerRadius));
    FlowTrayBorder->SetPadding(FMargin(28.0f, 18.0f));
    FlowTraySizeBox->AddChild(FlowTrayBorder);

    UVerticalBox* TrayStack = WidgetTree->ConstructWidget<UVerticalBox>(
        UVerticalBox::StaticClass(), TEXT("ProductionFlowStack"));
    FlowTrayBorder->AddChild(TrayStack);
    FlowTitleLabel = LBManagementShell::Text(WidgetTree,
        TEXT("ProductionFlowTitle"), TEXT("Production flow"), 24,
        LBManagementShell::OffWhite, true);
    UVerticalBoxSlot* TitleSlot = TrayStack->AddChildToVerticalBox(FlowTitleLabel);
    TitleSlot->SetPadding(FMargin(0.0f, 0.0f, 0.0f, 14.0f));

    UHorizontalBox* TrayContent = WidgetTree->ConstructWidget<UHorizontalBox>(
        UHorizontalBox::StaticClass(), TEXT("ProductionFlowContent"));
    UVerticalBoxSlot* ContentSlot = TrayStack->AddChildToVerticalBox(TrayContent);
    ContentSlot->SetSize(FSlateChildSize(ESlateSizeRule::Fill));

    StageRow = WidgetTree->ConstructWidget<UHorizontalBox>(
        UHorizontalBox::StaticClass(), TEXT("ProductionStageRow"));
    UHorizontalBoxSlot* StageRowSlot = TrayContent->AddChildToHorizontalBox(StageRow);
    StageRowSlot->SetSize(FSlateChildSize(ESlateSizeRule::Fill));
    StageRowSlot->SetPadding(FMargin(0.0f, 0.0f, 22.0f, 0.0f));
    for (int32 Index = 0; Index < ProductionStageCount; ++Index)
    {
        BuildStageCard(Index, StageRow);
        if (Index < ProductionConnectorCount)
            BuildStageConnector(Index, StageRow);
    }
    BuildDetailPanel(TrayContent);
}

void ULBManagementRootWidget::BuildStageCard(const int32 StageIndex,
    UHorizontalBox* Row)
{
    USizeBox* CardSize = LBManagementShell::FixedSize(WidgetTree,
        *FString::Printf(TEXT("StageSize_%d"), StageIndex), 210.0f, 258.0f);
    UHorizontalBoxSlot* RowSlot = Row->AddChildToHorizontalBox(CardSize);
    RowSlot->SetSize(FSlateChildSize(ESlateSizeRule::Fill));
    RowSlot->SetPadding(FMargin(StageIndex == 0 ? 0.0f : 3.0f, 0.0f,
        StageIndex == ProductionStageCount - 1 ? 0.0f : 3.0f, 0.0f));

    UButton* Button = WidgetTree->ConstructWidget<UButton>(UButton::StaticClass(),
        *FString::Printf(TEXT("StageButton_%d"), StageIndex));
    Button->SetClickMethod(EButtonClickMethod::DownAndUp);
    Button->SetPressMethod(EButtonPressMethod::DownAndUp);
    Button->SetStyle(LBManagementShell::ButtonStyle(
        LBManagementShell::Card, LBManagementShell::CardHover,
        LBManagementShell::GreenDark, LBManagementShell::Stroke, 8.0f));
    StageButtons.Add(Button);
    CardSize->AddChild(Button);

    UBorder* CardBorder = WidgetTree->ConstructWidget<UBorder>(
        UBorder::StaticClass(), *FString::Printf(TEXT("StageCard_%d"), StageIndex));
    CardBorder->SetBrush(LBManagementShell::RoundedBrush(FLinearColor::Transparent,
        LBManagementShell::Stroke, 1.0f, 8.0f));
    CardBorder->SetPadding(FMargin(12.0f, 10.0f));
    StageCardBorders.Add(CardBorder);
    if (UButtonSlot* CardSlot = Cast<UButtonSlot>(Button->AddChild(CardBorder)))
    {
        CardSlot->SetHorizontalAlignment(HAlign_Fill);
        CardSlot->SetVerticalAlignment(VAlign_Fill);
        CardSlot->SetPadding(FMargin(0.0f));
    }

    UVerticalBox* Stack = WidgetTree->ConstructWidget<UVerticalBox>(
        UVerticalBox::StaticClass(), *FString::Printf(TEXT("StageStack_%d"), StageIndex));
    CardBorder->AddChild(Stack);
    UTextBlock* Title = LBManagementShell::Text(WidgetTree,
        *FString::Printf(TEXT("StageTitle_%d"), StageIndex),
        LBManagementShell::StageNames[StageIndex], 17,
        LBManagementShell::OffWhite, true);
    Title->SetJustification(ETextJustify::Center);
    UVerticalBoxSlot* TitleSlot = Stack->AddChildToVerticalBox(Title);
    TitleSlot->SetPadding(FMargin(0.0f, 1.0f, 0.0f, 8.0f));

    UOverlay* ArtOverlay = WidgetTree->ConstructWidget<UOverlay>(
        UOverlay::StaticClass(), *FString::Printf(TEXT("StageArt_%d"), StageIndex));
    UVerticalBoxSlot* ArtSlot = Stack->AddChildToVerticalBox(ArtOverlay);
    ArtSlot->SetSize(FSlateChildSize(ESlateSizeRule::Fill));
    UImage* Image = WidgetTree->ConstructWidget<UImage>(UImage::StaticClass(),
        *FString::Printf(TEXT("StageImage_%d"), StageIndex));
    Image->SetDesiredSizeOverride(FVector2D(186.0f, 118.0f));
    // Do not ask UImage to stream a missing package; ResolveThumbnail exposes
    // an intentional empty-art state until the strict v003 import lands.
    StageImages.Add(Image);
    UOverlaySlot* ImageSlot = ArtOverlay->AddChildToOverlay(Image);
    ImageSlot->SetHorizontalAlignment(HAlign_Fill);
    ImageSlot->SetVerticalAlignment(VAlign_Fill);
    UTextBlock* ArtStatus = LBManagementShell::Text(WidgetTree,
        *FString::Printf(TEXT("StageArtStatus_%d"), StageIndex),
        TEXT("LIVE SCHEMATIC"), 12, LBManagementShell::Muted, true);
    ArtStatus->SetJustification(ETextJustify::Center);
    ArtStatus->SetAutoWrapText(true);
    StageArtStatusLabels.Add(ArtStatus);
    UOverlaySlot* ArtStatusSlot = ArtOverlay->AddChildToOverlay(ArtStatus);
    ArtStatusSlot->SetHorizontalAlignment(HAlign_Fill);
    ArtStatusSlot->SetVerticalAlignment(VAlign_Center);

    UHorizontalBox* StateRow = WidgetTree->ConstructWidget<UHorizontalBox>(
        UHorizontalBox::StaticClass(),
        *FString::Printf(TEXT("StageStateRow_%d"), StageIndex));
    UVerticalBoxSlot* StateRowSlot = Stack->AddChildToVerticalBox(StateRow);
    StateRowSlot->SetPadding(FMargin(0.0f, 8.0f, 0.0f, 2.0f));
    USizeBox* DotSize = LBManagementShell::FixedSize(WidgetTree,
        *FString::Printf(TEXT("StageStatusDotSize_%d"), StageIndex), 10.0f, 10.0f);
    UHorizontalBoxSlot* DotSizeSlot = StateRow->AddChildToHorizontalBox(DotSize);
    DotSizeSlot->SetPadding(FMargin(0.0f, 0.0f, 7.0f, 0.0f));
    DotSizeSlot->SetVerticalAlignment(VAlign_Center);
    UBorder* StatusDot = WidgetTree->ConstructWidget<UBorder>(
        UBorder::StaticClass(),
        *FString::Printf(TEXT("StageStatusDot_%d"), StageIndex));
    StatusDot->SetBrush(LBManagementShell::RoundedBrush(
        LBManagementShell::Muted, FLinearColor::Transparent, 0.0f, 5.0f));
    StatusDot->SetVisibility(ESlateVisibility::Collapsed);
    DotSize->AddChild(StatusDot);
    StageStatusDots.Add(StatusDot);
    UTextBlock* State = LBManagementShell::Text(WidgetTree,
        *FString::Printf(TEXT("StageState_%d"), StageIndex),
        TEXT("NOT INSTALLED"), 14, LBManagementShell::Muted, true);
    UHorizontalBoxSlot* StateSlot = StateRow->AddChildToHorizontalBox(State);
    StateSlot->SetVerticalAlignment(VAlign_Center);
    StageStateLabels.Add(State);

    if (StageIndex == 0) Button->OnClicked.AddDynamic(this,
        &ULBManagementRootWidget::OnStage0Clicked);
    else if (StageIndex == 1) Button->OnClicked.AddDynamic(this,
        &ULBManagementRootWidget::OnStage1Clicked);
    else if (StageIndex == 2) Button->OnClicked.AddDynamic(this,
        &ULBManagementRootWidget::OnStage2Clicked);
    else if (StageIndex == 3) Button->OnClicked.AddDynamic(this,
        &ULBManagementRootWidget::OnStage3Clicked);
    else if (StageIndex == 4) Button->OnClicked.AddDynamic(this,
        &ULBManagementRootWidget::OnStage4Clicked);
    else Button->OnClicked.AddDynamic(this,
        &ULBManagementRootWidget::OnStage5Clicked);
}

void ULBManagementRootWidget::BuildStageConnector(
    const int32 UpstreamStageIndex, UHorizontalBox* Row)
{
    USizeBox* ConnectorSize = LBManagementShell::FixedSize(WidgetTree,
        *FString::Printf(TEXT("StageConnectorSize_%d"), UpstreamStageIndex),
        24.0f, 2.0f);
    UHorizontalBoxSlot* ConnectorSlot = Row->AddChildToHorizontalBox(ConnectorSize);
    ConnectorSlot->SetVerticalAlignment(VAlign_Center);
    UBorder* ConnectorLine = WidgetTree->ConstructWidget<UBorder>(
        UBorder::StaticClass(),
        *FString::Printf(TEXT("StageConnector_%d"), UpstreamStageIndex));
    ConnectorLine->SetBrush(LBManagementShell::RoundedBrush(
        LBManagementShell::Stroke, FLinearColor::Transparent, 0.0f, 1.0f));
    ConnectorLine->SetToolTipText(FText::FromString(FString::Printf(
        TEXT("Canonical flow: %s to %s"),
        LBManagementShell::StageNames[UpstreamStageIndex],
        LBManagementShell::StageNames[UpstreamStageIndex + 1])));
    ConnectorSize->AddChild(ConnectorLine);
    StageConnectorLines.Add(ConnectorLine);
}

void ULBManagementRootWidget::BuildDetailPanel(UHorizontalBox* TrayContent)
{
    USizeBox* DividerSize = LBManagementShell::FixedSize(
        WidgetTree, TEXT("StageDetailDividerSize"),
        DesignDetailDividerWidth, 258.0f);
    UHorizontalBoxSlot* DividerSlot = TrayContent->AddChildToHorizontalBox(DividerSize);
    DividerSlot->SetPadding(FMargin(4.0f, 0.0f, 20.0f, 0.0f));
    UBorder* Divider = WidgetTree->ConstructWidget<UBorder>(
        UBorder::StaticClass(), TEXT("StageDetailDivider"));
    Divider->SetBrush(LBManagementShell::RoundedBrush(
        LBManagementShell::Stroke, FLinearColor::Transparent, 0.0f, 0.0f));
    DividerSize->AddChild(Divider);

    USizeBox* DetailSize = LBManagementShell::FixedSize(
        WidgetTree, TEXT("StageDetailSize"),
        354.0f, 258.0f);
    UHorizontalBoxSlot* DetailSlot = TrayContent->AddChildToHorizontalBox(DetailSize);

    DetailBorder = WidgetTree->ConstructWidget<UBorder>(UBorder::StaticClass(),
        TEXT("StageDetailPanel"));
    DetailBorder->SetBrush(LBManagementShell::RoundedBrush(
        FLinearColor::Transparent, FLinearColor::Transparent, 0.0f, 0.0f));
    DetailBorder->SetPadding(FMargin(0.0f, 10.0f, 12.0f, 10.0f));
    DetailSize->AddChild(DetailBorder);
    UVerticalBox* Stack = WidgetTree->ConstructWidget<UVerticalBox>(
        UVerticalBox::StaticClass(), TEXT("StageDetailStack"));
    DetailBorder->AddChild(Stack);

    DetailTitleLabel = LBManagementShell::Text(WidgetTree, TEXT("DetailTitle"),
        TEXT("Transfer press"), 22, LBManagementShell::Green, true);
    Stack->AddChildToVerticalBox(DetailTitleLabel);
    DetailStateLabel = LBManagementShell::Text(WidgetTree, TEXT("DetailState"),
        TEXT("STAGE 03 / 06  |  NOT INSTALLED"), 13,
        LBManagementShell::Muted, true);
    UVerticalBoxSlot* StateSlot = Stack->AddChildToVerticalBox(DetailStateLabel);
    StateSlot->SetPadding(FMargin(0.0f, 5.0f, 0.0f, 9.0f));
    DetailDescriptionLabel = LBManagementShell::Text(WidgetTree,
        TEXT("DetailDescription"), TEXT("PLACE THIS PROCESS ASSET"),
        14, LBManagementShell::OffWhite, false);
    DetailDescriptionLabel->SetAutoWrapText(true);
    UVerticalBoxSlot* DescriptionSlot = Stack->AddChildToVerticalBox(
        DetailDescriptionLabel);
    DescriptionSlot->SetSize(FSlateChildSize(ESlateSizeRule::Fill));

    DetailThroughputLabel = LBManagementShell::Text(WidgetTree,
        TEXT("DetailThroughput"), TEXT("FACTORY GOOD OUTPUT   0.0 units/hr"),
        13, LBManagementShell::OffWhite, true);
    DetailThroughputLabel->SetVisibility(ESlateVisibility::Collapsed);
    UVerticalBoxSlot* ThroughputSlot = Stack->AddChildToVerticalBox(
        DetailThroughputLabel);
    ThroughputSlot->SetPadding(FMargin(0.0f, 4.0f, 0.0f, 4.0f));

    DetailOrderLabel = LBManagementShell::Text(WidgetTree, TEXT("DetailOrder"),
        TEXT("NO ACTIVE PRODUCTION ORDER"), 13, LBManagementShell::Muted, true);
    UVerticalBoxSlot* OrderSlot = Stack->AddChildToVerticalBox(DetailOrderLabel);
    OrderSlot->SetPadding(FMargin(0.0f, 4.0f, 0.0f, 5.0f));
    DetailOrderProgress = WidgetTree->ConstructWidget<UProgressBar>(
        UProgressBar::StaticClass(), TEXT("DetailOrderProgress"));
    DetailOrderProgress->SetPercent(0.0f);
    DetailOrderProgress->SetFillColorAndOpacity(LBManagementShell::Green);
    UVerticalBoxSlot* ProgressSlot = Stack->AddChildToVerticalBox(DetailOrderProgress);
    ProgressSlot->SetPadding(FMargin(0.0f, 0.0f, 0.0f, 12.0f));

    USizeBox* ActionSize = LBManagementShell::FixedSize(
        WidgetTree, TEXT("PrimaryActionSize"),
        310.0f, 52.0f);
    UVerticalBoxSlot* ActionSlot = Stack->AddChildToVerticalBox(ActionSize);
    PrimaryActionButton = WidgetTree->ConstructWidget<UButton>(
        UButton::StaticClass(), TEXT("PrimaryStageAction"));
    PrimaryActionButton->SetStyle(LBManagementShell::ButtonStyle(
        LBManagementShell::GreenDark, LBManagementShell::Green,
        LBManagementShell::Green * 0.72f, LBManagementShell::Green, 8.0f));
    PrimaryActionButton->OnClicked.AddDynamic(this,
        &ULBManagementRootWidget::OnPrimaryActionClicked);
    PrimaryActionLabel = LBManagementShell::Text(WidgetTree,
        TEXT("PrimaryActionLabel"), TEXT("BUILD THIS STAGE"), 16,
        LBManagementShell::OffWhite, true);
    PrimaryActionLabel->SetJustification(ETextJustify::Center);
    PrimaryActionButton->AddChild(PrimaryActionLabel);
    ActionSize->AddChild(PrimaryActionButton);
}

void ULBManagementRootWidget::ApplyFactorySnapshot(
    const FLBFactoryUIStateSnapshot& Snapshot)
{
    LastSnapshot = Snapshot;
    if (PresentedStages.Num() != ProductionStageCount)
        BuildCanonicalPresentations();

    for (int32 Index = 0; Index < ProductionStageCount; ++Index)
    {
        FLBManagementStagePresentation& Presented = PresentedStages[Index];
        const FLBFactoryUIProductionStageSnapshot* Source =
            Snapshot.ProductionStages.FindByPredicate(
                [&Presented](const FLBFactoryUIProductionStageSnapshot& Candidate)
                {
                    return Candidate.StageId == Presented.StageId;
                });
        Presented.bInstalled = Source && Source->bInstalled;
        Presented.bRunning = Source && Source->bRunning;
        Presented.bWaiting = Source && Source->bWaiting;
        Presented.bFaulted = Source && Source->bFaulted;
        Presented.StateText = FText::FromString(Source
            ? Source->State : TEXT("NOT INSTALLED"));
        Presented.DetailText = FText::FromString(Source
            ? Source->Detail : TEXT("PLACE THIS PROCESS ASSET"));
        ResolveThumbnail(Index, false);
    }
    RefreshPresentation();
}

void ULBManagementRootWidget::RefreshFromFactoryState(const bool bForceRefresh)
{
    if (!GetWorld()) return;
    if (ULBFactoryUIStateSubsystem* UIState =
        GetWorld()->GetSubsystem<ULBFactoryUIStateSubsystem>())
    {
        ApplyFactorySnapshot(UIState->GetSnapshot(bForceRefresh));
    }
}

void ULBManagementRootWidget::SetManagementContext(const FName PageId,
    const FString& Heading, const FString& Summary,
    const TArray<FLBManagementContextActionPresentation>& Actions)
{
    const bool bOverview = PageId == TEXT("FACTORY");
    if (FlowTrayBorder)
        FlowTrayBorder->SetVisibility(bOverview
            ? ESlateVisibility::Visible : ESlateVisibility::Collapsed);
    if (ContextBorder)
        ContextBorder->SetVisibility(bOverview
            ? ESlateVisibility::Collapsed : ESlateVisibility::Visible);
    if (bOverview) return;

    if (ContextTitleLabel)
        ContextTitleLabel->SetText(FText::FromString(Heading));
    if (ContextSummaryLabel)
        ContextSummaryLabel->SetText(FText::FromString(Summary));
    ContextActionIndices.Reset();
    for (int32 Index = 0; Index < ContextActionButtons.Num(); ++Index)
    {
        UButton* Button = ContextActionButtons[Index];
        const bool bHasAction = Actions.IsValidIndex(Index);
        if (!Button) continue;
        Button->SetVisibility(bHasAction
            ? ESlateVisibility::Visible : ESlateVisibility::Collapsed);
        if (!bHasAction) continue;
        const FLBManagementContextActionPresentation& Action = Actions[Index];
        ContextActionIndices.Add(Action.ActionIndex);
        Button->SetIsEnabled(Action.bEnabled);
        Button->SetToolTipText(Action.Detail);
        if (ContextActionTitles.IsValidIndex(Index))
            ContextActionTitles[Index]->SetText(Action.Title);
        if (ContextActionDetails.IsValidIndex(Index))
            ContextActionDetails[Index]->SetText(Action.Detail);
    }
}

void ULBManagementRootWidget::RefreshPresentation()
{
    if (FactoryNameLabel && GetWorld())
    {
        if (const ULBFactoryBrandSubsystem* Brand =
            GetWorld()->GetSubsystem<ULBFactoryBrandSubsystem>())
            FactoryNameLabel->SetText(FText::FromString(
                Brand->GetFactoryName().ToUpper()));
    }
    if (OrderLabel)
    {
        const FString Model = LastSnapshot.Order.VehicleModelId.IsNone()
            ? TEXT("NO ACTIVE ORDER")
            : LastSnapshot.Order.VehicleModelId.ToString().Replace(TEXT("_"), TEXT(" "));
        OrderLabel->SetText(FText::FromString(LastSnapshot.Order.bHasActiveOrder
            ? FString::Printf(TEXT("%s   %d / %d issued"), *Model,
                LastSnapshot.Order.IssuedQuantity,
                LastSnapshot.Order.RequestedQuantity)
            : TEXT("NO ACTIVE ORDER")));
    }
    if (CashLabel)
        CashLabel->SetText(FText::FromString(
            LBManagementShell::FormatMoney(LastSnapshot.Management.CashBalancePence)));
    if (AlertLabel)
    {
        AlertLabel->SetText(FText::FromString(LastSnapshot.Alerts.IsEmpty()
            ? TEXT("No alerts")
            : FString::Printf(TEXT("%d %s"), LastSnapshot.Alerts.Num(),
                LastSnapshot.Alerts.Num() == 1 ? TEXT("alert") : TEXT("alerts"))));
        AlertLabel->SetColorAndOpacity(FSlateColor(LastSnapshot.Alerts.IsEmpty()
            ? LBManagementShell::Muted : LBManagementShell::Amber));
    }

    for (int32 Index = 0; Index < ProductionStageCount; ++Index)
    {
        RefreshStageCard(Index);
        if (Index < ProductionConnectorCount)
            RefreshStageConnector(Index);
    }
    RefreshDetailPanel();
}

void ULBManagementRootWidget::RefreshStageCard(const int32 StageIndex)
{
    if (!PresentedStages.IsValidIndex(StageIndex)) return;
    const FLBManagementStagePresentation& Stage = PresentedStages[StageIndex];
    const FLinearColor StateColour = Stage.bFaulted ? LBManagementShell::Red
        : Stage.bWaiting ? LBManagementShell::Amber
        : Stage.bRunning ? LBManagementShell::Green
        : Stage.bInstalled ? LBManagementShell::OffWhite
        : LBManagementShell::Muted;
    if (StageStateLabels.IsValidIndex(StageIndex))
    {
        StageStateLabels[StageIndex]->SetText(Stage.StateText);
        StageStateLabels[StageIndex]->SetColorAndOpacity(FSlateColor(StateColour));
    }
    if (StageStatusDots.IsValidIndex(StageIndex))
    {
        StageStatusDots[StageIndex]->SetVisibility(
            ShouldShowStageStatusDot(Stage)
                ? ESlateVisibility::HitTestInvisible
                : ESlateVisibility::Collapsed);
        StageStatusDots[StageIndex]->SetBrush(LBManagementShell::RoundedBrush(
            StateColour, FLinearColor::Transparent, 0.0f, 5.0f));
    }
    if (StageImages.IsValidIndex(StageIndex))
    {
        if (Stage.bThumbnailAvailable && Stage.Thumbnail.Get())
            StageImages[StageIndex]->SetBrushFromTexture(Stage.Thumbnail.Get(), false);
        StageImages[StageIndex]->SetVisibility(Stage.bThumbnailAvailable
            ? ESlateVisibility::HitTestInvisible : ESlateVisibility::Collapsed);
    }
    if (StageArtStatusLabels.IsValidIndex(StageIndex))
    {
        StageArtStatusLabels[StageIndex]->SetVisibility(Stage.bThumbnailAvailable
            ? ESlateVisibility::Collapsed : ESlateVisibility::HitTestInvisible);
        StageArtStatusLabels[StageIndex]->SetText(FText::FromString(
            TEXT("LIVE SCHEMATIC\nNATIVE STAGE ICON")));
    }
    if (StageCardBorders.IsValidIndex(StageIndex))
    {
        const bool bSelected = StageIndex == SelectedStageIndex;
        StageCardBorders[StageIndex]->SetBrush(LBManagementShell::RoundedBrush(
            bSelected ? LBManagementShell::GreenDark.CopyWithNewOpacity(0.30f)
                      : FLinearColor::Transparent,
            bSelected ? LBManagementShell::Green : LBManagementShell::Stroke,
            bSelected ? 2.0f : 1.0f, 8.0f));
    }
    if (StageButtons.IsValidIndex(StageIndex))
    {
        const FString Description = FString::Printf(TEXT("%s, stage %d of 6, %s. %s"),
            *Stage.DisplayName.ToString(), StageIndex + 1,
            *Stage.StateText.ToString(), *Stage.DetailText.ToString());
        StageButtons[StageIndex]->SetToolTipText(FText::FromString(Description));
    }
}

void ULBManagementRootWidget::RefreshStageConnector(
    const int32 UpstreamStageIndex)
{
    if (!StageConnectorLines.IsValidIndex(UpstreamStageIndex)
        || !PresentedStages.IsValidIndex(UpstreamStageIndex)
        || !PresentedStages.IsValidIndex(UpstreamStageIndex + 1))
        return;
    const FLBManagementStagePresentation& Upstream =
        PresentedStages[UpstreamStageIndex];
    const FLBManagementStagePresentation& Downstream =
        PresentedStages[UpstreamStageIndex + 1];
    const bool bLive = ShouldHighlightStageConnector(Upstream, Downstream);
    const bool bFaulted = bLive && (Upstream.bFaulted || Downstream.bFaulted);
    const FLinearColor ConnectorColour = bFaulted ? LBManagementShell::Red
        : bLive ? LBManagementShell::Green : LBManagementShell::Stroke;
    StageConnectorLines[UpstreamStageIndex]->SetBrush(
        LBManagementShell::RoundedBrush(ConnectorColour,
            FLinearColor::Transparent, 0.0f, 1.0f));
    StageConnectorLines[UpstreamStageIndex]->SetToolTipText(FText::FromString(
        FString::Printf(TEXT("%s to %s: %s"),
            *Upstream.DisplayName.ToString(), *Downstream.DisplayName.ToString(),
            bLive ? (bFaulted ? TEXT("CONNECTED, FAULT PRESENT") : TEXT("CONNECTED"))
                  : TEXT("PLANNED - BOTH STAGES ARE NOT YET INSTALLED"))));
}

void ULBManagementRootWidget::ResolveThumbnail(const int32 StageIndex,
    const bool bForceSynchronousLoad)
{
    if (!PresentedStages.IsValidIndex(StageIndex)) return;
    FLBManagementStagePresentation& Stage = PresentedStages[StageIndex];
    UObject* Resolved = Stage.Thumbnail.Get();
    if (!Resolved && bForceSynchronousLoad)
        Resolved = Stage.Thumbnail.LoadSynchronous();
    Stage.bThumbnailAvailable = Cast<UTexture2D>(Resolved) != nullptr;
}

void ULBManagementRootWidget::RefreshDetailPanel()
{
    if (!PresentedStages.IsValidIndex(SelectedStageIndex)) return;
    const FLBManagementStagePresentation& Stage = PresentedStages[SelectedStageIndex];
    const FLinearColor StateColour = Stage.bFaulted ? LBManagementShell::Red
        : Stage.bWaiting ? LBManagementShell::Amber
        : Stage.bRunning ? LBManagementShell::Green
        : Stage.bInstalled ? LBManagementShell::OffWhite
        : LBManagementShell::Muted;
    if (DetailTitleLabel)
    {
        DetailTitleLabel->SetText(Stage.DisplayName);
        DetailTitleLabel->SetColorAndOpacity(FSlateColor(StateColour));
    }
    if (DetailStateLabel)
        DetailStateLabel->SetText(FText::FromString(FString::Printf(
            TEXT("STAGE %02d / 06  |  %s"), SelectedStageIndex + 1,
            *Stage.StateText.ToString().ToUpper())));
    if (DetailDescriptionLabel)
        DetailDescriptionLabel->SetText(Stage.DetailText);

    if (DetailThroughputLabel)
    {
        const double Throughput =
            LastSnapshot.Management.ThroughputGoodUnitsPerHour;
        const bool bHasThroughput = HasTruthfulThroughput(Throughput);
        DetailThroughputLabel->SetVisibility(bHasThroughput
            ? ESlateVisibility::HitTestInvisible : ESlateVisibility::Collapsed);
        if (bHasThroughput)
            DetailThroughputLabel->SetText(FText::FromString(FString::Printf(
                TEXT("FACTORY GOOD OUTPUT   %.1f units/hr"), Throughput)));
    }

    const int32 Requested = FMath::Max(0, LastSnapshot.Order.RequestedQuantity);
    const int32 Issued = FMath::Clamp(LastSnapshot.Order.IssuedQuantity, 0, Requested);
    if (DetailOrderLabel)
        DetailOrderLabel->SetText(FText::FromString(LastSnapshot.Order.bHasActiveOrder
            ? FString::Printf(TEXT("ORDER OUTPUT   %d / %d"), Issued, Requested)
            : TEXT("NO ACTIVE PRODUCTION ORDER")));
    if (DetailOrderProgress)
    {
        DetailOrderProgress->SetPercent(Requested > 0
            ? static_cast<float>(Issued) / static_cast<float>(Requested) : 0.0f);
        DetailOrderProgress->SetVisibility(
            LastSnapshot.Order.bHasActiveOrder && Requested > 0
                ? ESlateVisibility::HitTestInvisible
                : ESlateVisibility::Collapsed);
    }
    if (PrimaryActionLabel)
        PrimaryActionLabel->SetText(FText::FromString(Stage.bInstalled
            ? TEXT("FOCUS LIVE ASSET") : TEXT("BUILD THIS STAGE")));
    if (PrimaryActionButton)
    {
        PrimaryActionButton->SetIsEnabled(true);
        PrimaryActionButton->SetToolTipText(FText::FromString(Stage.bInstalled
            ? FString::Printf(TEXT("Move the factory camera to %s"),
                *Stage.DisplayName.ToString())
            : FString::Printf(TEXT("Open placement for %s"),
                *Stage.DisplayName.ToString())));
    }
    if (PrimaryActionButton && StageButtons.IsValidIndex(SelectedStageIndex))
    {
        StageButtons[SelectedStageIndex]->SetNavigationRuleExplicit(
            EUINavigation::Down, PrimaryActionButton);
        PrimaryActionButton->SetNavigationRuleExplicit(EUINavigation::Up,
            StageButtons[SelectedStageIndex]);
    }
}

void ULBManagementRootWidget::SelectProductionStage(const int32 StageIndex,
    const bool bMoveKeyboardFocus)
{
    if (PresentedStages.IsEmpty()) return;
    const int32 Previous = SelectedStageIndex;
    SelectedStageIndex = FMath::Clamp(StageIndex, 0, ProductionStageCount - 1);
    if (Previous != SelectedStageIndex)
    {
        RefreshStageCard(Previous);
        RefreshStageCard(SelectedStageIndex);
        RefreshDetailPanel();
        OnStageSelectionChanged.Broadcast(
            PresentedStages[SelectedStageIndex].StageId);
    }
    if (bMoveKeyboardFocus && StageButtons.IsValidIndex(SelectedStageIndex))
        StageButtons[SelectedStageIndex]->SetKeyboardFocus();
}

void ULBManagementRootWidget::SelectRelativeProductionStage(const int32 Direction,
    const bool bMoveKeyboardFocus)
{
    const int32 Step = Direction < 0 ? -1 : 1;
    const int32 Next = (SelectedStageIndex + Step + ProductionStageCount)
        % ProductionStageCount;
    SelectProductionStage(Next, bMoveKeyboardFocus);
}

void ULBManagementRootWidget::ActivateSelectedStage()
{
    if (PresentedStages.IsValidIndex(SelectedStageIndex))
        OnStageActionRequested.Broadcast(PresentedStages[SelectedStageIndex].StageId);
}

void ULBManagementRootWidget::ReloadStageThumbnails()
{
    for (int32 Index = 0; Index < PresentedStages.Num(); ++Index)
    {
        FLBManagementStagePresentation& Stage = PresentedStages[Index];
        Stage.Thumbnail.ResetWeakPtr();
        ResolveThumbnail(Index, true);
    }
    RefreshPresentation();
}

bool ULBManagementRootWidget::HasCompleteThumbnailSet() const
{
    return PresentedStages.Num() == ProductionStageCount
        && PresentedStages.ContainsByPredicate([](const FLBManagementStagePresentation& Stage)
        {
            return !Stage.bThumbnailAvailable;
        }) == false;
}

bool ULBManagementRootWidget::HasRenderableShell() const
{
    return RootCanvas && ShellScaleBox && DesignCanvas
        && DesignCanvas->GetCachedWidget().IsValid();
}

void ULBManagementRootWidget::UpdateResponsiveLayout(const FVector2D ViewportSize)
{
    LastViewportSize = ViewportSize;
    if (!RootCanvas || !ShellScaleBox || !TopStripSizeBox || !FlowTraySizeBox) return;
    // ScaleToFit responds during Slate layout, including the first prepass, and
    // produces exact 2/3 and 1.0 scales at the two acceptance viewports.
}

void ULBManagementRootWidget::ConfigureFocusNavigation()
{
    if (StageButtons.Num() != ProductionStageCount || !PrimaryActionButton) return;

    TArray<UButton*> TopCommandButtons;
    TopCommandButtons.Reserve(
        TopDestinationButtons.Num() + SimulationRateButtons.Num());
    for (const TObjectPtr<UButton>& Button : TopDestinationButtons)
        if (Button) TopCommandButtons.Add(Button.Get());
    for (const TObjectPtr<UButton>& Button : SimulationRateButtons)
        if (Button) TopCommandButtons.Add(Button.Get());
    for (int32 Index = 0; Index < TopCommandButtons.Num(); ++Index)
    {
        UButton* Current = TopCommandButtons[Index];
        Current->SetNavigationRuleExplicit(EUINavigation::Left,
            TopCommandButtons[(Index + TopCommandButtons.Num() - 1)
                % TopCommandButtons.Num()]);
        Current->SetNavigationRuleExplicit(EUINavigation::Right,
            TopCommandButtons[(Index + 1) % TopCommandButtons.Num()]);
    }

    for (int32 Index = 0; Index < ProductionStageCount; ++Index)
    {
        UButton* Current = StageButtons[Index];
        Current->SetNavigationRuleExplicit(EUINavigation::Left,
            StageButtons[(Index + ProductionStageCount - 1) % ProductionStageCount]);
        Current->SetNavigationRuleExplicit(EUINavigation::Right,
            StageButtons[(Index + 1) % ProductionStageCount]);
        Current->SetNavigationRuleExplicit(EUINavigation::Down,
            PrimaryActionButton);
        if (TopDestinationButtons.IsValidIndex(1))
            Current->SetNavigationRuleExplicit(EUINavigation::Up,
                TopDestinationButtons[1]);
    }
    PrimaryActionButton->SetNavigationRuleExplicit(EUINavigation::Up,
        StageButtons[SelectedStageIndex]);
}

void ULBManagementRootWidget::RequestDestination(const FName DestinationId)
{
    OnDestinationRequested.Broadcast(DestinationId);
}

void ULBManagementRootWidget::RequestSimulationRate(const float Rate)
{
    OnSimulationRateRequested.Broadcast(Rate);
}

void ULBManagementRootWidget::HandleStageClicked(const int32 StageIndex)
{
    SelectProductionStage(StageIndex, true);
}

void ULBManagementRootWidget::OnStage0Clicked() { HandleStageClicked(0); }
void ULBManagementRootWidget::OnStage1Clicked() { HandleStageClicked(1); }
void ULBManagementRootWidget::OnStage2Clicked() { HandleStageClicked(2); }
void ULBManagementRootWidget::OnStage3Clicked() { HandleStageClicked(3); }
void ULBManagementRootWidget::OnStage4Clicked() { HandleStageClicked(4); }
void ULBManagementRootWidget::OnStage5Clicked() { HandleStageClicked(5); }
void ULBManagementRootWidget::OnPrimaryActionClicked() { ActivateSelectedStage(); }
void ULBManagementRootWidget::OnFactoryDestinationClicked() { RequestDestination(TEXT("FACTORY")); }
void ULBManagementRootWidget::OnBuildDestinationClicked() { RequestDestination(TEXT("BUILD")); }
void ULBManagementRootWidget::OnOrdersDestinationClicked() { RequestDestination(TEXT("ORDERS")); }
void ULBManagementRootWidget::OnAssetsDestinationClicked() { RequestDestination(TEXT("ASSETS")); }
void ULBManagementRootWidget::OnMaintenanceDestinationClicked() { RequestDestination(TEXT("MAINTENANCE")); }
void ULBManagementRootWidget::OnResearchDestinationClicked() { RequestDestination(TEXT("RESEARCH")); }
void ULBManagementRootWidget::OnAnalyticsDestinationClicked() { RequestDestination(TEXT("ANALYTICS")); }
void ULBManagementRootWidget::OnSettingsDestinationClicked() { RequestDestination(TEXT("SETTINGS")); }
void ULBManagementRootWidget::OnContextAction0Clicked() { if (ContextActionIndices.IsValidIndex(0)) OnContextActionRequested.Broadcast(ContextActionIndices[0]); }
void ULBManagementRootWidget::OnContextAction1Clicked() { if (ContextActionIndices.IsValidIndex(1)) OnContextActionRequested.Broadcast(ContextActionIndices[1]); }
void ULBManagementRootWidget::OnContextAction2Clicked() { if (ContextActionIndices.IsValidIndex(2)) OnContextActionRequested.Broadcast(ContextActionIndices[2]); }
void ULBManagementRootWidget::OnContextAction3Clicked() { if (ContextActionIndices.IsValidIndex(3)) OnContextActionRequested.Broadcast(ContextActionIndices[3]); }
void ULBManagementRootWidget::OnContextAction4Clicked() { if (ContextActionIndices.IsValidIndex(4)) OnContextActionRequested.Broadcast(ContextActionIndices[4]); }
void ULBManagementRootWidget::OnPauseClicked() { RequestSimulationRate(0.0f); }
void ULBManagementRootWidget::OnPlayClicked() { RequestSimulationRate(1.0f); }
void ULBManagementRootWidget::OnFastForwardClicked() { RequestSimulationRate(2.0f); }
