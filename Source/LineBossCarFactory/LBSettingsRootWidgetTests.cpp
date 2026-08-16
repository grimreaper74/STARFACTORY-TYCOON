#if WITH_DEV_AUTOMATION_TESTS

#include "LBSettingsRootWidget.h"

#include "Components/Button.h"
#include "Components/ComboBoxString.h"
#include "Components/Overlay.h"
#include "InputCoreTypes.h"
#include "Misc/AutomationTest.h"

IMPLEMENT_SIMPLE_AUTOMATION_TEST(
    FLBSettingsNativeOptionContractTest,
    "LineBoss.Settings.UMG.NativeOptionAndInputContract",
    EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)

bool FLBSettingsNativeOptionContractTest::RunTest(const FString& Parameters)
{
    const TArray<FString> Presets =
        ULBSettingsRootWidget::GetGraphicsPresetOptions();
    const FString ExpectedPresets[] = {
        TEXT("Auto"), TEXT("Low"), TEXT("Medium"), TEXT("High"),
        TEXT("Epic"), TEXT("Custom")};
    TestEqual(TEXT("Every player-facing graphics preset is exposed"),
        Presets.Num(), static_cast<int32>(UE_ARRAY_COUNT(ExpectedPresets)));
    for (int32 Index = 0; Index < UE_ARRAY_COUNT(ExpectedPresets); ++Index)
        TestEqual(FString::Printf(TEXT("Preset %d keeps its stable label"), Index),
            Presets[Index], ExpectedPresets[Index]);

    ELBGraphicsPreset ParsedPreset = ELBGraphicsPreset::Auto;
    for (int32 Index = 0; Index < Presets.Num(); ++Index)
    {
        TestTrue(FString::Printf(TEXT("%s round-trips through the settings parser"),
            *Presets[Index]), ULBSettingsRootWidget::TryParseGraphicsPresetOption(
                Presets[Index], ParsedPreset));
        TestEqual(TEXT("Parsed preset keeps its stable enum ordinal"),
            static_cast<int32>(ParsedPreset), Index);
    }
    TestFalse(TEXT("Invented graphics presets fail closed"),
        ULBSettingsRootWidget::TryParseGraphicsPresetOption(
            TEXT("Ultra Cinematic Plus"), ParsedPreset));

    FIntPoint Resolution;
    TestTrue(TEXT("A spaced 16:9 resolution parses"),
        ULBSettingsRootWidget::TryParseResolutionOption(
            TEXT("1920 x 1080"), Resolution));
    TestEqual(TEXT("Resolution width remains exact"), Resolution.X, 1920);
    TestEqual(TEXT("Resolution height remains exact"), Resolution.Y, 1080);
    TestTrue(TEXT("Compact upper-case resolution parses"),
        ULBSettingsRootWidget::TryParseResolutionOption(
            TEXT("2560X1440"), Resolution));
    TestFalse(TEXT("Too-small display modes fail closed"),
        ULBSettingsRootWidget::TryParseResolutionOption(
            TEXT("320 x 200"), Resolution));
    TestFalse(TEXT("Malformed display modes fail closed"),
        ULBSettingsRootWidget::TryParseResolutionOption(
            TEXT("full screen"), Resolution));

    TestTrue(TEXT("Keyboard Escape is an explicit settings back action"),
        ULBSettingsRootWidget::IsBackInputKey(EKeys::Escape));
    TestTrue(TEXT("Controller face-right is an explicit settings back action"),
        ULBSettingsRootWidget::IsBackInputKey(EKeys::Gamepad_FaceButton_Right));
    TestFalse(TEXT("Controller accept cannot accidentally cancel settings"),
        ULBSettingsRootWidget::IsBackInputKey(EKeys::Gamepad_FaceButton_Bottom));
    return true;
}

IMPLEMENT_SIMPLE_AUTOMATION_TEST(
    FLBSettingsNativeControllerFocusTest,
    "LineBoss.Settings.UMG.ControllerFocusAndFunctionalControls",
    EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)

bool FLBSettingsNativeControllerFocusTest::RunTest(const FString& Parameters)
{
    ULBGameUserSettings* Settings = NewObject<ULBGameUserSettings>();
    TestNotNull(TEXT("A test-local settings authority exists"), Settings);
    if (!Settings) return false;
    Settings->SetToDefaults();
    Settings->SetLineBossScreenResolution(FIntPoint(1920, 1080));
    Settings->SetLineBossWindowMode(EWindowMode::WindowedFullscreen);
    Settings->SetLineBossVSyncEnabled(true);
    Settings->SetLineBossFrameRateLimit(60.0f);
    Settings->SetLineBossRenderScale(80.0f);
    Settings->SetGraphicsPreset(ELBGraphicsPreset::High);

    ULBSettingsRootWidget* Widget = NewObject<ULBSettingsRootWidget>();
    TestNotNull(TEXT("The native settings widget can be instantiated"), Widget);
    if (!Widget) return false;
    TestTrue(TEXT("The native settings widget initializes its authored tree"),
        Widget->Initialize());
    Widget->SetSettingsAuthorityForTesting(Settings);
    // Keep the Slate owner alive while checking cached widget counterparts.
    // A real viewport owns this reference for the widget's entire visible lifetime.
    const TSharedRef<SWidget> SlateShell = Widget->TakeWidget();
    Widget->RefreshFromSettings();

    TestTrue(TEXT("The complete native settings shell has a Slate counterpart"),
        Widget->HasRenderableSettingsShell());
    TestTrue(TEXT("Every main and confirmation action has an explicit controller path"),
        Widget->HasCompleteControllerFocusGraph());

    const TArray<FName> MainControlIds =
        ULBSettingsRootWidget::GetCanonicalControllerControlIds();
    TestEqual(TEXT("The main controller loop covers every functional control"),
        MainControlIds.Num(), ULBSettingsRootWidget::MainControllerControlCount);
    TSet<FName> DistinctControlIds;
    for (const FName ControlId : MainControlIds) DistinctControlIds.Add(ControlId);
    TestEqual(TEXT("Controller focus IDs cannot alias each other"),
        DistinctControlIds.Num(), ULBSettingsRootWidget::MainControllerControlCount);
    TestEqual(TEXT("Display confirmation owns exactly Revert and Keep"),
        ULBSettingsRootWidget::GetDisplayConfirmationControlIds().Num(), 2);

    UComboBoxString* Preset = Cast<UComboBoxString>(
        Widget->GetWidgetFromName(TEXT("GraphicsPreset")));
    UComboBoxString* RenderScale = Cast<UComboBoxString>(
        Widget->GetWidgetFromName(TEXT("RenderScale")));
    TestNotNull(TEXT("Graphics preset is a real focusable selector"), Preset);
    TestNotNull(TEXT("Render scale is a real focusable selector"), RenderScale);
    if (Preset)
    {
        TestTrue(TEXT("Preset selector accepts controller focus"), Preset->IsFocusable());
        TestEqual(TEXT("UI reads the current High setting authority"),
            Preset->GetSelectedOption(), FString(TEXT("High")));
        TestEqual(TEXT("Every graphics preset is selectable"),
            Preset->GetOptionCount(), 6);
    }
    if (RenderScale && Preset)
    {
        RenderScale->OnSelectionChanged.Broadcast(TEXT("70%"),
            ESelectInfo::OnKeyPress);
        TestEqual(TEXT("A player render-scale edit truthfully stages Custom"),
            Preset->GetSelectedOption(), FString(TEXT("Custom")));
    }

    const FName ButtonNames[] = {
        TEXT("AutoDetectButton"), TEXT("CancelButton"),
        TEXT("ApplyButton"), TEXT("RevertDisplayButton"), TEXT("KeepDisplayButton")};
    for (const FName ButtonName : ButtonNames)
    {
        UButton* Button = Cast<UButton>(Widget->GetWidgetFromName(ButtonName));
        TestNotNull(FString::Printf(TEXT("%s is a real button"),
            *ButtonName.ToString()), Button);
        if (Button)
        {
            TestTrue(FString::Printf(TEXT("%s accepts controller focus"),
                *ButtonName.ToString()), Button->GetIsFocusable());
            TestTrue(FString::Printf(TEXT("%s is wired to behavior"),
                *ButtonName.ToString()), Button->OnClicked.IsBound());
        }
    }

    const FName LiveryNames[] = {TEXT("PrimaryLivery"), TEXT("SecondaryLivery")};
    for (const FName LiveryName : LiveryNames)
    {
        UComboBoxString* Livery = Cast<UComboBoxString>(
            Widget->GetWidgetFromName(LiveryName));
        TestNotNull(FString::Printf(TEXT("%s is a native livery selector"),
            *LiveryName.ToString()), Livery);
        if (Livery)
        {
            TestTrue(FString::Printf(TEXT("%s accepts controller focus"),
                *LiveryName.ToString()), Livery->IsFocusable());
            TestEqual(FString::Printf(TEXT("%s exposes every approved livery"),
                *LiveryName.ToString()), Livery->GetOptionCount(), 8);
        }
    }

    UOverlay* Confirmation = Cast<UOverlay>(
        Widget->GetWidgetFromName(TEXT("DisplayConfirmationOverlay")));
    TestNotNull(TEXT("Risky display changes own a real confirmation overlay"),
        Confirmation);
    if (Confirmation)
        TestEqual(TEXT("Display confirmation starts closed"),
            Confirmation->GetVisibility(), ESlateVisibility::Collapsed);
    TestFalse(TEXT("No display confirmation countdown is invented at startup"),
        Widget->IsDisplayConfirmationActive());
    return true;
}

#endif
