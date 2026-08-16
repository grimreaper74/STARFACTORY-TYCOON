#include "LBSettingsRootWidget.h"

#include "Blueprint/WidgetTree.h"
#include "Brushes/SlateRoundedBoxBrush.h"
#include "Components/Border.h"
#include "Components/Button.h"
#include "Components/ButtonSlot.h"
#include "Components/ComboBoxString.h"
#include "Components/HorizontalBox.h"
#include "Components/HorizontalBoxSlot.h"
#include "Components/Overlay.h"
#include "Components/OverlaySlot.h"
#include "Components/ScaleBox.h"
#include "Components/ScaleBoxSlot.h"
#include "Components/SizeBox.h"
#include "Components/Spacer.h"
#include "Components/TextBlock.h"
#include "Components/VerticalBox.h"
#include "Components/VerticalBoxSlot.h"
#include "Fonts/SlateFontInfo.h"
#include "HAL/PlatformProperties.h"
#include "InputCoreTypes.h"
#include "Kismet/KismetSystemLibrary.h"
#include "LBFactoryBrandSubsystem.h"
#include "Styling/CoreStyle.h"

namespace LBSettingsUI
{
    constexpr float PanelWidth = 1120.0f;
    constexpr float PanelHeight = 760.0f;

    const FLinearColor Backdrop(0.0015f, 0.0040f, 0.0045f, 0.82f);
    const FLinearColor Ink(0.0065f, 0.0100f, 0.0120f, 0.995f);
    const FLinearColor InkSoft(0.0110f, 0.0170f, 0.0200f, 1.0f);
    const FLinearColor Card(0.0200f, 0.0290f, 0.0330f, 1.0f);
    const FLinearColor CardHover(0.0320f, 0.0450f, 0.0500f, 1.0f);
    const FLinearColor Stroke(0.055f, 0.075f, 0.082f, 0.95f);
    const FLinearColor OffWhite(0.91f, 0.92f, 0.89f, 1.0f);
    const FLinearColor Muted(0.58f, 0.63f, 0.63f, 1.0f);
    const FLinearColor Green(0.030f, 0.64f, 0.235f, 1.0f);
    const FLinearColor GreenDark(0.008f, 0.110f, 0.050f, 1.0f);
    const FLinearColor Red(0.90f, 0.18f, 0.14f, 1.0f);

    FSlateFontInfo Font(const int32 Size, const bool bBold = false)
    {
        return FSlateFontInfo(FCoreStyle::GetDefaultFontStyle(
            bBold ? TEXT("Bold") : TEXT("Regular"), Size));
    }

    FSlateBrush RoundedBrush(const FLinearColor Fill, const FLinearColor Outline,
        const float OutlineWidth = 1.0f, const float Radius = 10.0f)
    {
        return FSlateRoundedBoxBrush(Fill,
            FVector4(Radius, Radius, Radius, Radius), Outline, OutlineWidth);
    }

    FButtonStyle ButtonStyle(const bool bPrimary)
    {
        FButtonStyle Style;
        const FLinearColor Normal = bPrimary ? FLinearColor(0.025f, 0.38f, 0.15f, 1.0f)
            : Card;
        const FLinearColor Hover = bPrimary ? FLinearColor(0.035f, 0.54f, 0.21f, 1.0f)
            : CardHover;
        Style.SetNormal(RoundedBrush(Normal, bPrimary ? Green : Stroke, 1.0f, 8.0f));
        Style.SetHovered(RoundedBrush(Hover, Green, 1.5f, 8.0f));
        Style.SetPressed(RoundedBrush(GreenDark, Green, 2.0f, 8.0f));
        Style.SetDisabled(RoundedBrush(Card.CopyWithNewOpacity(0.45f), Stroke, 1.0f, 8.0f));
        Style.SetNormalPadding(FMargin(1.0f));
        Style.SetPressedPadding(FMargin(2.0f, 3.0f, 0.0f, 0.0f));
        return Style;
    }

    FComboBoxStyle ComboStyle()
    {
        FComboButtonStyle ComboButton = FComboButtonStyle::GetDefault();
        ComboButton.SetButtonStyle(ButtonStyle(false));
        ComboButton.SetMenuBorderBrush(RoundedBrush(InkSoft, Stroke, 1.0f, 8.0f));
        ComboButton.SetMenuBorderPadding(FMargin(4.0f));
        ComboButton.SetContentPadding(FMargin(14.0f, 8.0f));

        FComboBoxStyle Style = FComboBoxStyle::GetDefault();
        Style.SetComboButtonStyle(ComboButton);
        Style.SetContentPadding(FMargin(0.0f));
        Style.SetMenuRowPadding(FMargin(4.0f, 2.0f));
        return Style;
    }

    FTableRowStyle ComboRowStyle()
    {
        const FSlateBrush Normal = RoundedBrush(InkSoft, Stroke, 0.0f, 4.0f);
        const FSlateBrush Hover = RoundedBrush(CardHover, Green, 1.0f, 4.0f);
        const FSlateBrush Active = RoundedBrush(GreenDark, Green, 1.0f, 4.0f);
        FTableRowStyle Style = FTableRowStyle::GetDefault();
        Style.SetEvenRowBackgroundBrush(Normal)
            .SetOddRowBackgroundBrush(Normal)
            .SetEvenRowBackgroundHoveredBrush(Hover)
            .SetOddRowBackgroundHoveredBrush(Hover)
            .SetActiveBrush(Active)
            .SetActiveHoveredBrush(Active)
            .SetInactiveBrush(Active)
            .SetInactiveHoveredBrush(Active)
            .SetTextColor(FSlateColor(OffWhite))
            .SetSelectedTextColor(FSlateColor(OffWhite));
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

    FString PresetName(const ELBGraphicsPreset Preset)
    {
        switch (Preset)
        {
        case ELBGraphicsPreset::Auto: return TEXT("Auto");
        case ELBGraphicsPreset::Low: return TEXT("Low");
        case ELBGraphicsPreset::Medium: return TEXT("Medium");
        case ELBGraphicsPreset::High: return TEXT("High");
        case ELBGraphicsPreset::Epic: return TEXT("Epic");
        case ELBGraphicsPreset::Custom: return TEXT("Custom");
        default: return TEXT("Auto");
        }
    }

    struct FLiveryOption
    {
        const TCHAR* Label;
        FLinearColor Colour;
    };

    const FLiveryOption FactoryLiveryOptions[] = {
        {TEXT("Cairnwell green"), FLinearColor(0.035f, 0.36f, 0.16f, 1.0f)},
        {TEXT("Production blue"), FLinearColor(0.025f, 0.22f, 0.55f, 1.0f)},
        {TEXT("Deep red"), FLinearColor(0.55f, 0.055f, 0.045f, 1.0f)},
        {TEXT("Industrial orange"), FLinearColor(0.80f, 0.24f, 0.025f, 1.0f)},
        {TEXT("Violet"), FLinearColor(0.30f, 0.075f, 0.48f, 1.0f)},
        {TEXT("Steel"), FLinearColor(0.38f, 0.43f, 0.46f, 1.0f)},
        {TEXT("Charcoal"), FLinearColor(0.055f, 0.07f, 0.075f, 1.0f)},
        {TEXT("Warm alloy"), FLinearColor(0.55f, 0.50f, 0.40f, 1.0f)}};

    FString LiveryName(const FLinearColor& Colour)
    {
        int32 BestIndex = 0;
        float BestDistance = TNumericLimits<float>::Max();
        for (int32 Index = 0; Index < UE_ARRAY_COUNT(FactoryLiveryOptions); ++Index)
        {
            const FLinearColor& Candidate = FactoryLiveryOptions[Index].Colour;
            const float Distance = FVector3f(
                Colour.R - Candidate.R, Colour.G - Candidate.G,
                Colour.B - Candidate.B).SizeSquared();
            if (Distance < BestDistance)
            {
                BestDistance = Distance;
                BestIndex = Index;
            }
        }
        return FactoryLiveryOptions[BestIndex].Label;
    }

    FString WindowModeName(const EWindowMode::Type Mode)
    {
        switch (Mode)
        {
        case EWindowMode::Fullscreen: return TEXT("Fullscreen");
        case EWindowMode::WindowedFullscreen: return TEXT("Borderless");
        case EWindowMode::Windowed: return TEXT("Windowed");
        default: return TEXT("Borderless");
        }
    }

    bool TryParseWindowMode(const FString& Option, EWindowMode::Type& OutMode)
    {
        if (Option.Equals(TEXT("Fullscreen"), ESearchCase::IgnoreCase))
            OutMode = EWindowMode::Fullscreen;
        else if (Option.Equals(TEXT("Borderless"), ESearchCase::IgnoreCase))
            OutMode = EWindowMode::WindowedFullscreen;
        else if (Option.Equals(TEXT("Windowed"), ESearchCase::IgnoreCase))
            OutMode = EWindowMode::Windowed;
        else
            return false;
        return true;
    }

    void AddOptionIfMissing(UComboBoxString* Combo, const FString& Option)
    {
        if (Combo && Combo->FindOptionIndex(Option) == INDEX_NONE)
            Combo->AddOption(Option);
    }
}

TArray<FString> ULBSettingsRootWidget::GetGraphicsPresetOptions()
{
    return {TEXT("Auto"), TEXT("Low"), TEXT("Medium"), TEXT("High"),
        TEXT("Epic"), TEXT("Custom")};
}

TArray<FString> ULBSettingsRootWidget::GetFactoryLiveryOptions()
{
    TArray<FString> Options;
    Options.Reserve(UE_ARRAY_COUNT(LBSettingsUI::FactoryLiveryOptions));
    for (const LBSettingsUI::FLiveryOption& Option : LBSettingsUI::FactoryLiveryOptions)
        Options.Add(Option.Label);
    return Options;
}

TArray<FName> ULBSettingsRootWidget::GetCanonicalControllerControlIds()
{
    return {TEXT("PRESET"), TEXT("VSYNC"), TEXT("RENDER_SCALE"),
        TEXT("PRIMARY_LIVERY"), TEXT("SECONDARY_LIVERY"),
        TEXT("RESOLUTION"), TEXT("WINDOW_MODE"), TEXT("FRAME_CAP"),
        TEXT("AUTO_DETECT"), TEXT("CANCEL"), TEXT("APPLY")};
}

TArray<FName> ULBSettingsRootWidget::GetDisplayConfirmationControlIds()
{
    return {TEXT("REVERT_DISPLAY"), TEXT("KEEP_DISPLAY")};
}

bool ULBSettingsRootWidget::TryParseResolutionOption(
    const FString& Option, FIntPoint& OutResolution)
{
    FString Compact = Option;
    Compact.ReplaceInline(TEXT(" "), TEXT(""));
    int32 Separator = INDEX_NONE;
    if (!Compact.FindChar(TEXT('x'), Separator)
        && !Compact.FindChar(TEXT('X'), Separator))
        return false;
    const FString WidthText = Compact.Left(Separator);
    const FString HeightText = Compact.Mid(Separator + 1);
    if (!WidthText.IsNumeric() || !HeightText.IsNumeric()) return false;
    const FIntPoint Parsed(FCString::Atoi(*WidthText), FCString::Atoi(*HeightText));
    if (Parsed.X < 640 || Parsed.Y < 480) return false;
    OutResolution = Parsed;
    return true;
}

bool ULBSettingsRootWidget::TryParseGraphicsPresetOption(
    const FString& Option, ELBGraphicsPreset& OutPreset)
{
    const TArray<FString> Options = GetGraphicsPresetOptions();
    for (int32 Index = 0; Index < Options.Num(); ++Index)
    {
        if (Option.Equals(Options[Index], ESearchCase::IgnoreCase))
        {
            OutPreset = static_cast<ELBGraphicsPreset>(Index);
            return true;
        }
    }
    return false;
}

bool ULBSettingsRootWidget::TryGetFactoryLiveryColour(const FString& Option,
    FLinearColor& OutColour)
{
    for (const LBSettingsUI::FLiveryOption& Candidate : LBSettingsUI::FactoryLiveryOptions)
    {
        if (Option.Equals(Candidate.Label, ESearchCase::IgnoreCase))
        {
            OutColour = Candidate.Colour;
            return true;
        }
    }
    return false;
}

bool ULBSettingsRootWidget::IsBackInputKey(const FKey& Key)
{
    return Key == EKeys::Escape || Key == EKeys::Gamepad_FaceButton_Right;
}

void ULBSettingsRootWidget::SetSettingsAuthorityForTesting(
    ULBGameUserSettings* InSettings)
{
    SettingsAuthorityOverride = InSettings;
    // Native UUserWidget instances without a player context deliberately skip
    // NativeOnInitialized. Give focused automation the same authored tree without
    // weakening the production CreateWidget path.
    if (WidgetTree)
    {
        SetIsFocusable(true);
        BuildShell();
        ConfigureControllerNavigation();
        RefreshFromSettings();
    }
}

TSharedRef<SWidget> ULBSettingsRootWidget::RebuildWidget()
{
    // UUserWidget takes WidgetTree->RootWidget before NativeConstruct runs. Build
    // the native tree here so both production AddToPlayerScreen and automation get
    // the authored shell instead of UUserWidget's fallback spacer.
    SetIsFocusable(true);
    BuildShell();
    ConfigureControllerNavigation();
    return Super::RebuildWidget();
}

void ULBSettingsRootWidget::NativeOnInitialized()
{
    Super::NativeOnInitialized();
    SetIsFocusable(true);
    BuildShell();
    ConfigureControllerNavigation();
}

void ULBSettingsRootWidget::NativeConstruct()
{
    Super::NativeConstruct();
    RefreshFromSettings();
    ConfigureControllerNavigation();
    FocusInitialControl();
}

void ULBSettingsRootWidget::NativeTick(const FGeometry& MyGeometry,
    const float InDeltaTime)
{
    Super::NativeTick(MyGeometry, InDeltaTime);
    if (!bDisplayConfirmationActive) return;

    DisplayConfirmationTimeRemaining = FMath::Max(
        0.0f, DisplayConfirmationTimeRemaining - InDeltaTime);
    if (DisplayConfirmationLabel)
    {
        DisplayConfirmationLabel->SetText(FText::FromString(FString::Printf(
            TEXT("Keep these display settings?  Reverting in %d seconds."),
            FMath::CeilToInt(DisplayConfirmationTimeRemaining))));
    }
    if (DisplayConfirmationTimeRemaining <= 0.0f)
        FinishDisplayConfirmation(false);
}

FReply ULBSettingsRootWidget::NativeOnKeyDown(const FGeometry& InGeometry,
    const FKeyEvent& InKeyEvent)
{
    if (IsBackInputKey(InKeyEvent.GetKey()))
    {
        if (bDisplayConfirmationActive) FinishDisplayConfirmation(false);
        else OnCloseRequested.Broadcast();
        return FReply::Handled();
    }
    return Super::NativeOnKeyDown(InGeometry, InKeyEvent);
}

void ULBSettingsRootWidget::BuildShell()
{
    if (!WidgetTree || WidgetTree->RootWidget) return;

    RootOverlay = WidgetTree->ConstructWidget<UOverlay>(
        UOverlay::StaticClass(), TEXT("LBSettingsRoot"));
    WidgetTree->RootWidget = RootOverlay;

    UBorder* Dim = WidgetTree->ConstructWidget<UBorder>(
        UBorder::StaticClass(), TEXT("SettingsBackdrop"));
    Dim->SetBrush(LBSettingsUI::RoundedBrush(
        LBSettingsUI::Backdrop, FLinearColor::Transparent, 0.0f, 0.0f));
    UOverlaySlot* DimSlot = RootOverlay->AddChildToOverlay(Dim);
    DimSlot->SetHorizontalAlignment(HAlign_Fill);
    DimSlot->SetVerticalAlignment(VAlign_Fill);

    UScaleBox* Scale = WidgetTree->ConstructWidget<UScaleBox>(
        UScaleBox::StaticClass(), TEXT("SettingsScale"));
    Scale->SetStretch(EStretch::ScaleToFit);
    Scale->SetStretchDirection(EStretchDirection::DownOnly);
    UOverlaySlot* ScaleOverlaySlot = RootOverlay->AddChildToOverlay(Scale);
    ScaleOverlaySlot->SetHorizontalAlignment(HAlign_Fill);
    ScaleOverlaySlot->SetVerticalAlignment(VAlign_Fill);

    USizeBox* DesignSize = WidgetTree->ConstructWidget<USizeBox>(
        USizeBox::StaticClass(), TEXT("SettingsDesignSize"));
    DesignSize->SetWidthOverride(LBSettingsUI::PanelWidth);
    DesignSize->SetHeightOverride(LBSettingsUI::PanelHeight);
    Scale->AddChild(DesignSize);
    if (UScaleBoxSlot* DesignSlot = Cast<UScaleBoxSlot>(DesignSize->Slot))
    {
        DesignSlot->SetHorizontalAlignment(HAlign_Center);
        DesignSlot->SetVerticalAlignment(VAlign_Center);
    }

    SettingsPanel = WidgetTree->ConstructWidget<UBorder>(
        UBorder::StaticClass(), TEXT("SettingsPanel"));
    SettingsPanel->SetBrush(LBSettingsUI::RoundedBrush(
        LBSettingsUI::Ink, LBSettingsUI::Stroke, 1.25f, 14.0f));
    SettingsPanel->SetPadding(FMargin(32.0f, 26.0f));
    DesignSize->AddChild(SettingsPanel);

    UVerticalBox* Page = WidgetTree->ConstructWidget<UVerticalBox>(
        UVerticalBox::StaticClass(), TEXT("SettingsPage"));
    SettingsPanel->AddChild(Page);

    UHorizontalBox* Header = WidgetTree->ConstructWidget<UHorizontalBox>(
        UHorizontalBox::StaticClass(), TEXT("SettingsHeader"));
    UVerticalBoxSlot* HeaderSlot = Page->AddChildToVerticalBox(Header);
    HeaderSlot->SetSize(FSlateChildSize(ESlateSizeRule::Automatic));
    HeaderSlot->SetPadding(FMargin(0.0f, 0.0f, 0.0f, 16.0f));

    UVerticalBox* HeaderCopy = WidgetTree->ConstructWidget<UVerticalBox>(
        UVerticalBox::StaticClass(), TEXT("SettingsHeaderCopy"));
    UHorizontalBoxSlot* HeaderCopySlot = Header->AddChildToHorizontalBox(HeaderCopy);
    HeaderCopySlot->SetSize(FSlateChildSize(ESlateSizeRule::Fill));
    HeaderCopy->AddChildToVerticalBox(LBSettingsUI::Text(WidgetTree,
        TEXT("SettingsTitle"), TEXT("SETTINGS"), 30, LBSettingsUI::OffWhite, true));
    HeaderCopy->AddChildToVerticalBox(LBSettingsUI::Text(WidgetTree,
        TEXT("SettingsSubtitle"),
        TEXT("Tune the factory view for this machine. Changes save locally."),
        14, LBSettingsUI::Muted));

    UBorder* SectionBadge = WidgetTree->ConstructWidget<UBorder>(
        UBorder::StaticClass(), TEXT("SettingsSectionBadge"));
    SectionBadge->SetBrush(LBSettingsUI::RoundedBrush(
        LBSettingsUI::GreenDark, LBSettingsUI::Green, 1.0f, 16.0f));
    SectionBadge->SetPadding(FMargin(16.0f, 8.0f));
    UHorizontalBoxSlot* BadgeSlot = Header->AddChildToHorizontalBox(SectionBadge);
    BadgeSlot->SetVerticalAlignment(VAlign_Center);
    SectionBadge->AddChild(LBSettingsUI::Text(WidgetTree,
        TEXT("SettingsSectionBadgeLabel"), TEXT("GRAPHICS + DISPLAY"), 12,
        LBSettingsUI::Green, true));

    UBorder* Divider = WidgetTree->ConstructWidget<UBorder>(
        UBorder::StaticClass(), TEXT("SettingsHeaderDivider"));
    Divider->SetBrush(LBSettingsUI::RoundedBrush(
        LBSettingsUI::Stroke, FLinearColor::Transparent, 0.0f, 0.0f));
    UVerticalBoxSlot* DividerSlot = Page->AddChildToVerticalBox(Divider);
    DividerSlot->SetSize(FSlateChildSize(ESlateSizeRule::Automatic));
    DividerSlot->SetPadding(FMargin(0.0f, 0.0f, 0.0f, 18.0f));
    Divider->SetDesiredSizeScale(FVector2D(1.0f, 1.0f));
    USizeBox* DividerHeight = WidgetTree->ConstructWidget<USizeBox>(
        USizeBox::StaticClass(), TEXT("SettingsDividerHeight"));
    DividerHeight->SetHeightOverride(1.0f);
    Divider->AddChild(DividerHeight);

    UHorizontalBox* Sections = WidgetTree->ConstructWidget<UHorizontalBox>(
        UHorizontalBox::StaticClass(), TEXT("SettingsSections"));
    UVerticalBoxSlot* SectionsSlot = Page->AddChildToVerticalBox(Sections);
    SectionsSlot->SetSize(FSlateChildSize(ESlateSizeRule::Fill));

    auto BuildColumn = [&](const FName BorderName, const FString& Heading)
    {
        UBorder* ColumnBorder = WidgetTree->ConstructWidget<UBorder>(
            UBorder::StaticClass(), BorderName);
        ColumnBorder->SetBrush(LBSettingsUI::RoundedBrush(
            LBSettingsUI::InkSoft, LBSettingsUI::Stroke, 1.0f, 10.0f));
        ColumnBorder->SetPadding(FMargin(20.0f, 16.0f));
        UHorizontalBoxSlot* ColumnSlot = Sections->AddChildToHorizontalBox(ColumnBorder);
        ColumnSlot->SetSize(FSlateChildSize(ESlateSizeRule::Fill));
        ColumnSlot->SetPadding(FMargin(
            BorderName == TEXT("GraphicsColumn") ? 0.0f : 8.0f, 0.0f,
            BorderName == TEXT("GraphicsColumn") ? 8.0f : 0.0f, 0.0f));
        UVerticalBox* Column = WidgetTree->ConstructWidget<UVerticalBox>(
            UVerticalBox::StaticClass(), *FString::Printf(TEXT("%sContent"), *BorderName.ToString()));
        ColumnBorder->AddChild(Column);
        UTextBlock* HeadingLabel = LBSettingsUI::Text(WidgetTree,
            *FString::Printf(TEXT("%sHeading"), *BorderName.ToString()),
            Heading, 16, LBSettingsUI::Green, true);
        UVerticalBoxSlot* HeadingSlot = Column->AddChildToVerticalBox(HeadingLabel);
        HeadingSlot->SetPadding(FMargin(0.0f, 0.0f, 0.0f, 12.0f));
        return Column;
    };

    UVerticalBox* GraphicsColumn = BuildColumn(TEXT("GraphicsColumn"),
        TEXT("GRAPHICS QUALITY"));
    PresetCombo = BuildSettingCombo(GraphicsColumn, TEXT("GraphicsPreset"),
        TEXT("Quality preset"), TEXT("Auto benchmarks this PC; Custom preserves mixed settings."),
        GetGraphicsPresetOptions());
    VSyncCombo = BuildSettingCombo(GraphicsColumn, TEXT("VSync"),
        TEXT("Vertical sync"), TEXT("Prevents tearing; may add a small amount of input latency."),
        {TEXT("Off"), TEXT("On")});
    RenderScaleCombo = BuildSettingCombo(GraphicsColumn, TEXT("RenderScale"),
        TEXT("Render scale"), TEXT("Lower values improve performance while UI stays full resolution."),
        {TEXT("50%"), TEXT("60%"), TEXT("70%"), TEXT("80%"), TEXT("90%"), TEXT("100%")});
    RenderScaleCombo->OnSelectionChanged.AddDynamic(
        this, &ULBSettingsRootWidget::HandleRenderScaleChanged);

    UTextBlock* AppearanceHeading = LBSettingsUI::Text(WidgetTree,
        TEXT("AppearanceHeading"), TEXT("FACTORY APPEARANCE"), 16,
        LBSettingsUI::Green, true);
    UVerticalBoxSlot* AppearanceHeadingSlot = GraphicsColumn->AddChildToVerticalBox(
        AppearanceHeading);
    AppearanceHeadingSlot->SetPadding(FMargin(0.0f, 16.0f, 0.0f, 8.0f));
    PrimaryLiveryCombo = BuildSettingCombo(GraphicsColumn, TEXT("PrimaryLivery"),
        TEXT("Machine primary"), TEXT("Applied to approved machine livery. Safety yellow remains fixed."),
        GetFactoryLiveryOptions());
    SecondaryLiveryCombo = BuildSettingCombo(GraphicsColumn, TEXT("SecondaryLivery"),
        TEXT("Machine secondary"), TEXT("Choose a contrasting frame colour for clear industrial readability."),
        GetFactoryLiveryOptions());

    UVerticalBox* DisplayColumn = BuildColumn(TEXT("DisplayColumn"),
        TEXT("DISPLAY"));
    TArray<FString> ResolutionOptions;
    TArray<FIntPoint> SupportedResolutions;
    if (!FPlatformProperties::HasFixedResolution()
        && UKismetSystemLibrary::GetSupportedFullscreenResolutions(
            SupportedResolutions))
    {
        SupportedResolutions.Sort([](const FIntPoint& A, const FIntPoint& B)
        {
            return A.X == B.X ? A.Y < B.Y : A.X < B.X;
        });
        for (const FIntPoint Resolution : SupportedResolutions)
        {
            if (Resolution.X < 1280 || Resolution.Y < 720) continue;
            const FString Option = FString::Printf(TEXT("%d x %d"),
                Resolution.X, Resolution.Y);
            if (!ResolutionOptions.Contains(Option)) ResolutionOptions.Add(Option);
        }
    }
    if (ResolutionOptions.IsEmpty())
    {
        ResolutionOptions = {TEXT("1280 x 720"), TEXT("1600 x 900"),
            TEXT("1920 x 1080"), TEXT("2560 x 1440"), TEXT("3840 x 2160")};
    }
    ResolutionCombo = BuildSettingCombo(DisplayColumn, TEXT("Resolution"),
        TEXT("Resolution"), TEXT("Display changes must be confirmed or they automatically revert."),
        ResolutionOptions);
    WindowModeCombo = BuildSettingCombo(DisplayColumn, TEXT("WindowMode"),
        TEXT("Window mode"), TEXT("Borderless is the recommended desktop default."),
        {TEXT("Fullscreen"), TEXT("Borderless"), TEXT("Windowed")});
    FrameCapCombo = BuildSettingCombo(DisplayColumn, TEXT("FrameCap"),
        TEXT("Frame limit"), TEXT("A stable cap keeps thermals and frame pacing under control."),
        {TEXT("Uncapped"), TEXT("30 FPS"), TEXT("60 FPS"), TEXT("90 FPS"),
            TEXT("120 FPS"), TEXT("144 FPS")});

    const bool bDisplayControlsSupported = !FPlatformProperties::HasFixedResolution();
    ResolutionCombo->SetIsEnabled(bDisplayControlsSupported);
    WindowModeCombo->SetIsEnabled(bDisplayControlsSupported);

    StatusLabel = LBSettingsUI::Text(WidgetTree, TEXT("SettingsStatus"),
        TEXT("Changes are staged until Apply."), 13, LBSettingsUI::Muted);
    StatusLabel->SetAutoWrapText(true);
    UVerticalBoxSlot* StatusSlot = Page->AddChildToVerticalBox(StatusLabel);
    StatusSlot->SetSize(FSlateChildSize(ESlateSizeRule::Automatic));
    StatusSlot->SetPadding(FMargin(2.0f, 12.0f, 2.0f, 4.0f));

    UTextBlock* ControlHint = LBSettingsUI::Text(WidgetTree,
        TEXT("SettingsControllerHint"),
        TEXT("A / ENTER: SELECT     B / ESC: BACK     START / F10: SETTINGS"),
        11, LBSettingsUI::Green, true);
    ControlHint->SetJustification(ETextJustify::Right);
    UVerticalBoxSlot* ControlHintSlot = Page->AddChildToVerticalBox(ControlHint);
    ControlHintSlot->SetSize(FSlateChildSize(ESlateSizeRule::Automatic));
    ControlHintSlot->SetPadding(FMargin(2.0f, 0.0f, 2.0f, 10.0f));

    UHorizontalBox* Footer = WidgetTree->ConstructWidget<UHorizontalBox>(
        UHorizontalBox::StaticClass(), TEXT("SettingsFooter"));
    UVerticalBoxSlot* FooterSlot = Page->AddChildToVerticalBox(Footer);
    FooterSlot->SetSize(FSlateChildSize(ESlateSizeRule::Automatic));

    auto AddFooterButton = [&](UButton* Button, const float Width)
    {
        USizeBox* Size = WidgetTree->ConstructWidget<USizeBox>(
            USizeBox::StaticClass(), *FString::Printf(TEXT("%sSize"), *Button->GetName()));
        Size->SetWidthOverride(Width);
        Size->SetHeightOverride(50.0f);
        Size->AddChild(Button);
        UHorizontalBoxSlot* Slot = Footer->AddChildToHorizontalBox(Size);
        Slot->SetPadding(FMargin(0.0f, 0.0f, 10.0f, 0.0f));
    };

    AutoDetectButton = BuildActionButton(TEXT("AutoDetectButton"),
        TEXT("AUTO DETECT AGAIN"));
    AutoDetectButton->OnClicked.AddDynamic(this,
        &ULBSettingsRootWidget::HandleAutoDetectClicked);
    AddFooterButton(AutoDetectButton, 202.0f);
    MainFocusOrder.Add(AutoDetectButton);

    USpacer* FooterPush = WidgetTree->ConstructWidget<USpacer>(
        USpacer::StaticClass(), TEXT("SettingsFooterPush"));
    UHorizontalBoxSlot* PushSlot = Footer->AddChildToHorizontalBox(FooterPush);
    PushSlot->SetSize(FSlateChildSize(ESlateSizeRule::Fill));

    CancelButton = BuildActionButton(TEXT("CancelButton"), TEXT("CANCEL"));
    CancelButton->OnClicked.AddDynamic(this,
        &ULBSettingsRootWidget::HandleCancelClicked);
    AddFooterButton(CancelButton, 138.0f);
    MainFocusOrder.Add(CancelButton);

    ApplyButton = BuildActionButton(TEXT("ApplyButton"), TEXT("APPLY"), true);
    ApplyButton->OnClicked.AddDynamic(this,
        &ULBSettingsRootWidget::HandleApplyClicked);
    AddFooterButton(ApplyButton, 152.0f);
    MainFocusOrder.Add(ApplyButton);

    DisplayConfirmationOverlay = WidgetTree->ConstructWidget<UOverlay>(
        UOverlay::StaticClass(), TEXT("DisplayConfirmationOverlay"));
    UOverlaySlot* ConfirmationRootSlot = RootOverlay->AddChildToOverlay(
        DisplayConfirmationOverlay);
    ConfirmationRootSlot->SetHorizontalAlignment(HAlign_Fill);
    ConfirmationRootSlot->SetVerticalAlignment(VAlign_Fill);

    UBorder* ConfirmationDim = WidgetTree->ConstructWidget<UBorder>(
        UBorder::StaticClass(), TEXT("DisplayConfirmationDim"));
    ConfirmationDim->SetBrush(LBSettingsUI::RoundedBrush(
        FLinearColor(0.0f, 0.0f, 0.0f, 0.88f), FLinearColor::Transparent, 0.0f, 0.0f));
    UOverlaySlot* ConfirmationDimSlot = DisplayConfirmationOverlay->AddChildToOverlay(
        ConfirmationDim);
    ConfirmationDimSlot->SetHorizontalAlignment(HAlign_Fill);
    ConfirmationDimSlot->SetVerticalAlignment(VAlign_Fill);

    USizeBox* ConfirmationSize = WidgetTree->ConstructWidget<USizeBox>(
        USizeBox::StaticClass(), TEXT("DisplayConfirmationSize"));
    ConfirmationSize->SetWidthOverride(620.0f);
    ConfirmationSize->SetHeightOverride(250.0f);
    UOverlaySlot* ConfirmationSizeSlot = DisplayConfirmationOverlay->AddChildToOverlay(
        ConfirmationSize);
    ConfirmationSizeSlot->SetHorizontalAlignment(HAlign_Center);
    ConfirmationSizeSlot->SetVerticalAlignment(VAlign_Center);

    UBorder* ConfirmationPanel = WidgetTree->ConstructWidget<UBorder>(
        UBorder::StaticClass(), TEXT("DisplayConfirmationPanel"));
    ConfirmationPanel->SetBrush(LBSettingsUI::RoundedBrush(
        LBSettingsUI::Ink, LBSettingsUI::Green, 1.5f, 12.0f));
    ConfirmationPanel->SetPadding(FMargin(28.0f, 24.0f));
    ConfirmationSize->AddChild(ConfirmationPanel);

    UVerticalBox* ConfirmationContent = WidgetTree->ConstructWidget<UVerticalBox>(
        UVerticalBox::StaticClass(), TEXT("DisplayConfirmationContent"));
    ConfirmationPanel->AddChild(ConfirmationContent);
    ConfirmationContent->AddChildToVerticalBox(LBSettingsUI::Text(WidgetTree,
        TEXT("DisplayConfirmationTitle"), TEXT("CONFIRM DISPLAY"), 22,
        LBSettingsUI::OffWhite, true));
    DisplayConfirmationLabel = LBSettingsUI::Text(WidgetTree,
        TEXT("DisplayConfirmationLabel"), TEXT("Keep these display settings?"),
        15, LBSettingsUI::Muted);
    UVerticalBoxSlot* ConfirmationLabelSlot =
        ConfirmationContent->AddChildToVerticalBox(DisplayConfirmationLabel);
    ConfirmationLabelSlot->SetPadding(FMargin(0.0f, 12.0f, 0.0f, 22.0f));

    UHorizontalBox* ConfirmationActions = WidgetTree->ConstructWidget<UHorizontalBox>(
        UHorizontalBox::StaticClass(), TEXT("DisplayConfirmationActions"));
    UVerticalBoxSlot* ConfirmationActionsSlot =
        ConfirmationContent->AddChildToVerticalBox(ConfirmationActions);
    ConfirmationActionsSlot->SetHorizontalAlignment(HAlign_Right);

    RevertDisplayButton = BuildActionButton(TEXT("RevertDisplayButton"), TEXT("REVERT"));
    RevertDisplayButton->OnClicked.AddDynamic(this,
        &ULBSettingsRootWidget::HandleRevertDisplayClicked);
    USizeBox* RevertSize = WidgetTree->ConstructWidget<USizeBox>(
        USizeBox::StaticClass(), TEXT("RevertDisplaySize"));
    RevertSize->SetWidthOverride(150.0f);
    RevertSize->SetHeightOverride(50.0f);
    RevertSize->AddChild(RevertDisplayButton);
    UHorizontalBoxSlot* RevertSlot = ConfirmationActions->AddChildToHorizontalBox(RevertSize);
    RevertSlot->SetPadding(FMargin(0.0f, 0.0f, 12.0f, 0.0f));

    KeepDisplayButton = BuildActionButton(TEXT("KeepDisplayButton"),
        TEXT("KEEP SETTINGS"), true);
    KeepDisplayButton->OnClicked.AddDynamic(this,
        &ULBSettingsRootWidget::HandleKeepDisplayClicked);
    USizeBox* KeepSize = WidgetTree->ConstructWidget<USizeBox>(
        USizeBox::StaticClass(), TEXT("KeepDisplaySize"));
    KeepSize->SetWidthOverride(190.0f);
    KeepSize->SetHeightOverride(50.0f);
    KeepSize->AddChild(KeepDisplayButton);
    ConfirmationActions->AddChildToHorizontalBox(KeepSize);

    DisplayConfirmationOverlay->SetVisibility(ESlateVisibility::Collapsed);
}

UComboBoxString* ULBSettingsRootWidget::BuildSettingCombo(UVerticalBox* Column,
    const FName Name, const FString& Label, const FString& SupportingText,
    const TArray<FString>& Options)
{
    UVerticalBox* Row = WidgetTree->ConstructWidget<UVerticalBox>(
        UVerticalBox::StaticClass(), *FString::Printf(TEXT("%sRow"), *Name.ToString()));
    UVerticalBoxSlot* RowSlot = Column->AddChildToVerticalBox(Row);
    RowSlot->SetPadding(FMargin(0.0f, 0.0f, 0.0f, 13.0f));

    Row->AddChildToVerticalBox(LBSettingsUI::Text(WidgetTree,
        *FString::Printf(TEXT("%sLabel"), *Name.ToString()), Label, 14,
        LBSettingsUI::OffWhite, true));
    UTextBlock* Hint = LBSettingsUI::Text(WidgetTree,
        *FString::Printf(TEXT("%sHint"), *Name.ToString()), SupportingText, 11,
        LBSettingsUI::Muted);
    Hint->SetAutoWrapText(true);
    UVerticalBoxSlot* HintSlot = Row->AddChildToVerticalBox(Hint);
    HintSlot->SetPadding(FMargin(0.0f, 2.0f, 0.0f, 6.0f));

    USizeBox* ComboSize = WidgetTree->ConstructWidget<USizeBox>(
        USizeBox::StaticClass(), *FString::Printf(TEXT("%sSize"), *Name.ToString()));
    ComboSize->SetHeightOverride(46.0f);
    UComboBoxString* Combo = WidgetTree->ConstructWidget<UComboBoxString>(
        UComboBoxString::StaticClass(), Name);
    Combo->SetEnableGamepadNavigationMode(true);
    Combo->SetMaxListHeight(330.0f);
    Combo->SetContentPadding(FMargin(12.0f, 7.0f));
    Combo->SetWidgetStyle(LBSettingsUI::ComboStyle());
    Combo->SetItemStyle(LBSettingsUI::ComboRowStyle());
    for (const FString& Option : Options) Combo->AddOption(Option);
    if (!Options.IsEmpty()) Combo->SetSelectedOption(Options[0]);
    ComboSize->AddChild(Combo);
    Row->AddChildToVerticalBox(ComboSize);
    MainFocusOrder.Add(Combo);
    return Combo;
}

UButton* ULBSettingsRootWidget::BuildActionButton(const FName Name,
    const FString& Label, const bool bPrimaryAction)
{
    UButton* Button = WidgetTree->ConstructWidget<UButton>(
        UButton::StaticClass(), Name);
    Button->SetClickMethod(EButtonClickMethod::DownAndUp);
    Button->SetPressMethod(EButtonPressMethod::DownAndUp);
    Button->SetStyle(LBSettingsUI::ButtonStyle(bPrimaryAction));
    UTextBlock* LabelWidget = LBSettingsUI::Text(WidgetTree,
        *FString::Printf(TEXT("%sLabel"), *Name.ToString()), Label, 13,
        bPrimaryAction ? FLinearColor::White : LBSettingsUI::OffWhite, true);
    LabelWidget->SetJustification(ETextJustify::Center);
    Button->AddChild(LabelWidget);
    if (UButtonSlot* LabelSlot = Cast<UButtonSlot>(LabelWidget->Slot))
    {
        LabelSlot->SetPadding(FMargin(10.0f, 6.0f));
        LabelSlot->SetHorizontalAlignment(HAlign_Center);
        LabelSlot->SetVerticalAlignment(VAlign_Center);
    }
    return Button;
}

void ULBSettingsRootWidget::ConfigureControllerNavigation()
{
    bControllerNavigationConfigured = false;
    if (MainFocusOrder.Num() != MainControllerControlCount) return;
    for (int32 Index = 0; Index < MainFocusOrder.Num(); ++Index)
    {
        UWidget* Current = MainFocusOrder[Index];
        UWidget* Previous = MainFocusOrder[
            (Index + MainFocusOrder.Num() - 1) % MainFocusOrder.Num()];
        UWidget* Next = MainFocusOrder[(Index + 1) % MainFocusOrder.Num()];
        if (!Current || !Previous || !Next) return;
        Current->SetNavigationRuleExplicit(EUINavigation::Up, Previous);
        Current->SetNavigationRuleExplicit(EUINavigation::Down, Next);
    }

    for (int32 Index = 6; Index < MainFocusOrder.Num(); ++Index)
    {
        UWidget* Current = MainFocusOrder[Index];
        Current->SetNavigationRuleExplicit(EUINavigation::Left,
            MainFocusOrder[Index == 6 ? MainFocusOrder.Num() - 1 : Index - 1]);
        Current->SetNavigationRuleExplicit(EUINavigation::Right,
            MainFocusOrder[Index == MainFocusOrder.Num() - 1 ? 6 : Index + 1]);
    }

    if (!RevertDisplayButton || !KeepDisplayButton) return;
    RevertDisplayButton->SetNavigationRuleExplicit(EUINavigation::Left,
        KeepDisplayButton);
    RevertDisplayButton->SetNavigationRuleExplicit(EUINavigation::Right,
        KeepDisplayButton);
    RevertDisplayButton->SetNavigationRuleExplicit(EUINavigation::Up,
        KeepDisplayButton);
    RevertDisplayButton->SetNavigationRuleExplicit(EUINavigation::Down,
        KeepDisplayButton);
    RevertDisplayButton->SetNavigationRuleExplicit(EUINavigation::Next,
        KeepDisplayButton);
    RevertDisplayButton->SetNavigationRuleExplicit(EUINavigation::Previous,
        KeepDisplayButton);
    KeepDisplayButton->SetNavigationRuleExplicit(EUINavigation::Left,
        RevertDisplayButton);
    KeepDisplayButton->SetNavigationRuleExplicit(EUINavigation::Right,
        RevertDisplayButton);
    KeepDisplayButton->SetNavigationRuleExplicit(EUINavigation::Up,
        RevertDisplayButton);
    KeepDisplayButton->SetNavigationRuleExplicit(EUINavigation::Down,
        RevertDisplayButton);
    KeepDisplayButton->SetNavigationRuleExplicit(EUINavigation::Next,
        RevertDisplayButton);
    KeepDisplayButton->SetNavigationRuleExplicit(EUINavigation::Previous,
        RevertDisplayButton);
    bControllerNavigationConfigured = true;
}

bool ULBSettingsRootWidget::HasRenderableSettingsShell() const
{
    return IsValid(RootOverlay) && IsValid(SettingsPanel)
        && MainFocusOrder.Num() == MainControllerControlCount
        // UUserWidget can retain a wrapper around a historical spacer while its
        // authored children are the actual viewport content. Validate those child
        // Slate counterparts, which is also safe for focused automation.
        && RootOverlay->GetCachedWidget().IsValid()
        && SettingsPanel->GetCachedWidget().IsValid();
}

bool ULBSettingsRootWidget::HasCompleteControllerFocusGraph() const
{
    if (!bControllerNavigationConfigured
        || MainFocusOrder.Num() != MainControllerControlCount
        || GetCanonicalControllerControlIds().Num() != MainControllerControlCount
        || !RevertDisplayButton || !KeepDisplayButton)
        return false;
    for (const UWidget* Control : MainFocusOrder)
    {
        if (!IsValid(Control)) return false;
        if (const UComboBoxString* Combo = Cast<UComboBoxString>(Control))
        {
            if (!Combo->IsFocusable()) return false;
        }
        else if (const UButton* Button = Cast<UButton>(Control))
        {
            if (!Button->GetIsFocusable()) return false;
        }
        else return false;
    }
    return RevertDisplayButton->GetIsFocusable()
        && KeepDisplayButton->GetIsFocusable();
}

ULBGameUserSettings* ULBSettingsRootWidget::ResolveSettings() const
{
    return SettingsAuthorityOverride.IsValid()
        ? SettingsAuthorityOverride.Get()
        : ULBGameUserSettings::GetLineBossGameUserSettings();
}

void ULBSettingsRootWidget::RefreshFromSettings()
{
    ULBGameUserSettings* Settings = ResolveSettings();
    if (!Settings)
    {
        SetStatus(TEXT("Graphics settings authority is unavailable."), true);
        if (ApplyButton) ApplyButton->SetIsEnabled(false);
        if (AutoDetectButton) AutoDetectButton->SetIsEnabled(false);
        return;
    }

    if (ApplyButton) ApplyButton->SetIsEnabled(true);
    if (AutoDetectButton) AutoDetectButton->SetIsEnabled(true);
    if (PresetCombo)
        PresetCombo->SetSelectedOption(LBSettingsUI::PresetName(
            Settings->GetGraphicsPreset()));
    if (VSyncCombo)
        VSyncCombo->SetSelectedOption(Settings->IsVSyncEnabled()
            ? TEXT("On") : TEXT("Off"));

    if (FrameCapCombo)
    {
        const float Limit = Settings->GetFrameRateLimit();
        const FString Option = Limit <= 0.0f ? TEXT("Uncapped")
            : FString::Printf(TEXT("%d FPS"), FMath::RoundToInt(Limit));
        LBSettingsUI::AddOptionIfMissing(FrameCapCombo, Option);
        FrameCapCombo->SetSelectedOption(Option);
    }

    if (RenderScaleCombo)
    {
        const FString Option = FString::Printf(TEXT("%d%%"),
            FMath::RoundToInt(Settings->GetLineBossRenderScale()));
        LBSettingsUI::AddOptionIfMissing(RenderScaleCombo, Option);
        RenderScaleCombo->SetSelectedOption(Option);
    }

    if (ResolutionCombo)
    {
        FIntPoint Resolution = Settings->GetScreenResolution();
        if (Resolution.X < 640 || Resolution.Y < 480)
            Resolution = Settings->GetDesktopResolution();
        if (Resolution.X < 640 || Resolution.Y < 480)
            Resolution = FIntPoint(1920, 1080);
        const FString Option = FString::Printf(TEXT("%d x %d"),
            Resolution.X, Resolution.Y);
        LBSettingsUI::AddOptionIfMissing(ResolutionCombo, Option);
        ResolutionCombo->SetSelectedOption(Option);
    }
    if (WindowModeCombo)
        WindowModeCombo->SetSelectedOption(LBSettingsUI::WindowModeName(
            Settings->GetFullscreenMode()));

    if (const UWorld* World = GetWorld())
    {
        if (const ULBFactoryBrandSubsystem* Brand = World->GetSubsystem<ULBFactoryBrandSubsystem>())
        {
            if (PrimaryLiveryCombo)
                PrimaryLiveryCombo->SetSelectedOption(
                    LBSettingsUI::LiveryName(Brand->GetPrimaryColour()));
            if (SecondaryLiveryCombo)
                SecondaryLiveryCombo->SetSelectedOption(
                    LBSettingsUI::LiveryName(Brand->GetSecondaryColour()));
        }
    }

    SetStatus(Settings->UsedHardwareBenchmarkFallback()
        ? TEXT("Auto used the safe High fallback on this machine.")
        : TEXT("Changes are staged until Apply."));
}

void ULBSettingsRootWidget::FocusInitialControl()
{
    if (PresetCombo)
    {
        if (APlayerController* Controller = GetOwningPlayer())
            PresetCombo->SetUserFocus(Controller);
        else
            PresetCombo->SetKeyboardFocus();
    }
}

void ULBSettingsRootWidget::CancelAndRevertPendingDisplayChange()
{
    if (bDisplayConfirmationActive) FinishDisplayConfirmation(false);
}

void ULBSettingsRootWidget::SetStatus(const FString& Message, const bool bError)
{
    if (!StatusLabel) return;
    StatusLabel->SetText(FText::FromString(Message));
    StatusLabel->SetColorAndOpacity(FSlateColor(
        bError ? LBSettingsUI::Red : LBSettingsUI::Muted));
}

bool ULBSettingsRootWidget::ApplyStagedSettings()
{
    ULBGameUserSettings* Settings = ResolveSettings();
    if (!Settings || !PresetCombo || !ResolutionCombo || !WindowModeCombo
        || !VSyncCombo || !FrameCapCombo || !RenderScaleCombo
        || !PrimaryLiveryCombo || !SecondaryLiveryCombo)
    {
        SetStatus(TEXT("Settings could not be applied."), true);
        return false;
    }

    ELBGraphicsPreset Preset = ELBGraphicsPreset::Auto;
    if (!TryParseGraphicsPresetOption(PresetCombo->GetSelectedOption(), Preset))
    {
        SetStatus(TEXT("Choose a valid graphics preset."), true);
        return false;
    }

    FIntPoint Resolution;
    EWindowMode::Type WindowMode = EWindowMode::WindowedFullscreen;
    if (!TryParseResolutionOption(ResolutionCombo->GetSelectedOption(), Resolution)
        || !LBSettingsUI::TryParseWindowMode(
            WindowModeCombo->GetSelectedOption(), WindowMode))
    {
        SetStatus(TEXT("Choose a valid display mode."), true);
        return false;
    }

    FString FrameText = FrameCapCombo->GetSelectedOption();
    float FrameLimit = 0.0f;
    if (!FrameText.Equals(TEXT("Uncapped"), ESearchCase::IgnoreCase))
    {
        FrameText.RemoveFromEnd(TEXT(" FPS"));
        FrameLimit = FCString::Atof(*FrameText);
        if (FrameLimit <= 0.0f)
        {
            SetStatus(TEXT("Choose a valid frame limit."), true);
            return false;
        }
    }

    FString ScaleText = RenderScaleCombo->GetSelectedOption();
    ScaleText.RemoveFromEnd(TEXT("%"));
    const float RenderScale = FCString::Atof(*ScaleText);
    if (RenderScale < 25.0f || RenderScale > 200.0f)
    {
        SetStatus(TEXT("Choose a valid render scale."), true);
        return false;
    }

    FLinearColor PrimaryLivery = FLinearColor::Black;
    FLinearColor SecondaryLivery = FLinearColor::Black;
    if (!TryGetFactoryLiveryColour(PrimaryLiveryCombo->GetSelectedOption(), PrimaryLivery)
        || !TryGetFactoryLiveryColour(SecondaryLiveryCombo->GetSelectedOption(), SecondaryLivery))
    {
        SetStatus(TEXT("Choose valid factory livery colours."), true);
        return false;
    }

    if (UWorld* World = GetWorld())
    {
        if (ULBFactoryBrandSubsystem* Brand = World->GetSubsystem<ULBFactoryBrandSubsystem>())
        {
            FString LiveryReason;
            if (!Brand->SetMachineLiveryColours(PrimaryLivery, SecondaryLivery, LiveryReason))
            {
                SetStatus(LiveryReason, true);
                return false;
            }
        }
    }

    const bool bCanChangeDisplay = !FPlatformProperties::HasFixedResolution();
    const bool bDisplayChanged = bCanChangeDisplay
        && (Resolution != Settings->GetScreenResolution()
            || WindowMode != Settings->GetFullscreenMode());

    if (!Settings->SetGraphicsPreset(Preset))
    {
        SetStatus(TEXT("The selected quality preset is unavailable."), true);
        return false;
    }
    if (Preset == ELBGraphicsPreset::Auto)
        Settings->InitialiseFirstRunGraphics(true);
    else if (Preset == ELBGraphicsPreset::Custom)
        Settings->SetLineBossRenderScale(RenderScale);

    Settings->SetLineBossVSyncEnabled(
        VSyncCombo->GetSelectedOption().Equals(TEXT("On"), ESearchCase::IgnoreCase));
    Settings->SetLineBossFrameRateLimit(FrameLimit);
    if (bCanChangeDisplay)
    {
        Settings->SetLineBossScreenResolution(Resolution);
        Settings->SetLineBossWindowMode(WindowMode);
    }
    if (bDisplayChanged)
    {
        // Do not persist an unconfirmed display mode. Non-resolution choices are
        // applied now and saved when the player either keeps or reverts the mode.
        Settings->ApplyResolutionSettings(false);
        Settings->ApplyNonResolutionSettings();
        BeginDisplayConfirmation();
    }
    else
    {
        Settings->ApplyAndSaveLineBossSettings(false);
        RefreshFromSettings();
        SetStatus(TEXT("Settings applied and saved."));
        if (PresetCombo) PresetCombo->SetKeyboardFocus();
    }
    return true;
}

void ULBSettingsRootWidget::BeginDisplayConfirmation()
{
    bDisplayConfirmationActive = true;
    DisplayConfirmationTimeRemaining = DisplayConfirmationSeconds;
    if (DisplayConfirmationOverlay)
        DisplayConfirmationOverlay->SetVisibility(ESlateVisibility::Visible);
    if (DisplayConfirmationLabel)
        DisplayConfirmationLabel->SetText(FText::FromString(FString::Printf(
            TEXT("Keep these display settings?  Reverting in %d seconds."),
            FMath::CeilToInt(DisplayConfirmationSeconds))));
    if (KeepDisplayButton) KeepDisplayButton->SetKeyboardFocus();
}

void ULBSettingsRootWidget::FinishDisplayConfirmation(const bool bKeepChanges)
{
    ULBGameUserSettings* Settings = ResolveSettings();
    if (Settings)
    {
        if (bKeepChanges)
        {
            Settings->ConfirmVideoMode();
            Settings->SaveSettings();
        }
        else
        {
            Settings->RevertVideoMode();
            Settings->ApplyResolutionSettings(false);
            Settings->SaveSettings();
        }
    }
    bDisplayConfirmationActive = false;
    DisplayConfirmationTimeRemaining = 0.0f;
    if (DisplayConfirmationOverlay)
        DisplayConfirmationOverlay->SetVisibility(ESlateVisibility::Collapsed);
    RefreshFromSettings();
    SetStatus(bKeepChanges
        ? TEXT("Display settings confirmed and saved.")
        : TEXT("Display settings reverted; other changes remain saved."));
    if (PresetCombo) PresetCombo->SetKeyboardFocus();
}

void ULBSettingsRootWidget::HandleApplyClicked()
{
    ApplyStagedSettings();
}

void ULBSettingsRootWidget::HandleCancelClicked()
{
    if (bDisplayConfirmationActive) FinishDisplayConfirmation(false);
    else OnCloseRequested.Broadcast();
}

void ULBSettingsRootWidget::HandleAutoDetectClicked()
{
    ULBGameUserSettings* Settings = ResolveSettings();
    if (!Settings)
    {
        SetStatus(TEXT("Auto Detect is unavailable."), true);
        return;
    }
    Settings->SetGraphicsPreset(ELBGraphicsPreset::Auto);
    const ELBGraphicsSetupResult Result = Settings->InitialiseFirstRunGraphics(true);
    RefreshFromSettings();
    SetStatus(Result == ELBGraphicsSetupResult::BenchmarkApplied
        ? TEXT("Auto Detect completed and saved the recommended quality.")
        : TEXT("Auto Detect completed using the safe High fallback."),
        Result == ELBGraphicsSetupResult::SkippedByPolicy);
}

void ULBSettingsRootWidget::HandleAppearanceClicked()
{
    if (bDisplayConfirmationActive) FinishDisplayConfirmation(false);
    OnAppearanceRequested.Broadcast();
}

void ULBSettingsRootWidget::HandleKeepDisplayClicked()
{
    if (bDisplayConfirmationActive) FinishDisplayConfirmation(true);
}

void ULBSettingsRootWidget::HandleRevertDisplayClicked()
{
    if (bDisplayConfirmationActive) FinishDisplayConfirmation(false);
}

void ULBSettingsRootWidget::HandleRenderScaleChanged(
    FString SelectedItem, const ESelectInfo::Type SelectionType)
{
    if (SelectionType != ESelectInfo::Direct && PresetCombo)
        PresetCombo->SetSelectedOption(TEXT("Custom"));
}
