#include "LBGameUserSettings.h"

#include "Misc/AutomationTest.h"
#include "Misc/ConfigCacheIni.h"

#include <limits>

#if WITH_DEV_AUTOMATION_TESTS

IMPLEMENT_SIMPLE_AUTOMATION_TEST(FLBGraphicsPresetAndVideoAuthorityTest,
    "LineBoss.Settings.Graphics.PresetAndVideoAuthority",
    EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)

bool FLBGraphicsPresetAndVideoAuthorityTest::RunTest(const FString& Parameters)
{
    ULBGameUserSettings* Settings = NewObject<ULBGameUserSettings>();
    TestNotNull(TEXT("Line Boss settings authority can be instantiated"), Settings);
    if (!Settings) return false;

    Settings->SetToDefaults();
    TestEqual(TEXT("Fresh settings select Auto"), Settings->GetGraphicsPreset(),
        ELBGraphicsPreset::Auto);
    TestEqual(TEXT("Fresh settings have not consumed first-run setup"),
        Settings->GetGraphicsSetupVersion(), 0);

    struct FPresetCase
    {
        ELBGraphicsPreset Preset;
        int32 ExpectedLevel;
    };
    const FPresetCase Cases[] = {
        { ELBGraphicsPreset::Low, 0 },
        { ELBGraphicsPreset::Medium, 1 },
        { ELBGraphicsPreset::High, 2 },
        { ELBGraphicsPreset::Epic, 3 }
    };
    for (const FPresetCase& Case : Cases)
    {
        int32 MappedLevel = INDEX_NONE;
        TestTrue(TEXT("Named preset has an engine scalability mapping"),
            ULBGameUserSettings::TryGetScalabilityLevelForPreset(
                Case.Preset, MappedLevel));
        TestEqual(TEXT("Named preset maps to the expected engine level"),
            MappedLevel, Case.ExpectedLevel);
        TestTrue(TEXT("Named preset can be cached"),
            Settings->SetGraphicsPreset(Case.Preset));
        TestEqual(TEXT("UGameUserSettings owns the resulting scalability level"),
            Settings->GetOverallScalabilityLevel(), Case.ExpectedLevel);
        TestEqual(TEXT("Named preference completes first-run policy"),
            Settings->GetGraphicsSetupVersion(),
            ULBGameUserSettings::CurrentGraphicsSetupVersion);
    }

    int32 UnmappedLevel = 123;
    TestFalse(TEXT("Auto has no hard-coded scalability level"),
        ULBGameUserSettings::TryGetScalabilityLevelForPreset(
            ELBGraphicsPreset::Auto, UnmappedLevel));
    TestEqual(TEXT("Unmapped preset returns INDEX_NONE"), UnmappedLevel, INDEX_NONE);
    TestFalse(TEXT("Custom has no hard-coded scalability level"),
        ULBGameUserSettings::TryGetScalabilityLevelForPreset(
            ELBGraphicsPreset::Custom, UnmappedLevel));

    TestTrue(TEXT("Resolution wrapper accepts a positive mode"),
        Settings->SetLineBossScreenResolution(FIntPoint(1920, 1080)));
    TestEqual(TEXT("Resolution remains owned by UGameUserSettings"),
        Settings->GetScreenResolution(), FIntPoint(1920, 1080));
    TestFalse(TEXT("Resolution wrapper rejects an invalid size"),
        Settings->SetLineBossScreenResolution(FIntPoint(0, 1080)));
    TestEqual(TEXT("Rejected resolution does not mutate cached state"),
        Settings->GetScreenResolution(), FIntPoint(1920, 1080));

    TestTrue(TEXT("Window-mode wrapper accepts an engine window mode"),
        Settings->SetLineBossWindowMode(EWindowMode::Windowed));
    TestEqual(TEXT("Window mode remains owned by UGameUserSettings"),
        Settings->GetFullscreenMode(), EWindowMode::Windowed);
    Settings->SetLineBossVSyncEnabled(true);
    TestTrue(TEXT("VSync remains owned by UGameUserSettings"), Settings->IsVSyncEnabled());
    TestTrue(TEXT("Frame-limit wrapper accepts a finite non-negative limit"),
        Settings->SetLineBossFrameRateLimit(144.0f));
    TestEqual(TEXT("Frame limit remains owned by UGameUserSettings"),
        Settings->GetFrameRateLimit(), 144.0f);
    TestFalse(TEXT("Frame-limit wrapper rejects negative values"),
        Settings->SetLineBossFrameRateLimit(-1.0f));

    TestTrue(TEXT("Render scale wrapper accepts a finite percentage"),
        Settings->SetLineBossRenderScale(77.0f));
    TestEqual(TEXT("Render-scale edit makes the quality preset Custom"),
        Settings->GetGraphicsPreset(), ELBGraphicsPreset::Custom);
    TestTrue(TEXT("Render scale remains within engine authority"),
        FMath::IsNearlyEqual(Settings->GetLineBossRenderScale(), 77.0f));
    TestFalse(TEXT("Render scale rejects non-finite values"),
        Settings->SetLineBossRenderScale(
            std::numeric_limits<float>::quiet_NaN()));

    TestTrue(TEXT("Selecting Auto queues benchmark resolution"),
        Settings->SetGraphicsPreset(ELBGraphicsPreset::Auto));
    TestTrue(TEXT("Auto restores the pending first-run marker"),
        Settings->IsFirstRunGraphicsSetupNeeded());
    return true;
}

IMPLEMENT_SIMPLE_AUTOMATION_TEST(FLBGraphicsFirstRunPolicyAndRegistrationTest,
    "LineBoss.Settings.Graphics.FirstRunPolicyAndRegistration",
    EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)

bool FLBGraphicsFirstRunPolicyAndRegistrationTest::RunTest(const FString& Parameters)
{
    TestTrue(TEXT("An uninitialised desktop Auto profile requests a benchmark"),
        ULBGameUserSettings::ShouldRunHardwareBenchmarkForState(
            0, ELBGraphicsPreset::Auto, true, true, false));
    TestFalse(TEXT("The current setup version never benchmarks again"),
        ULBGameUserSettings::ShouldRunHardwareBenchmarkForState(
            ULBGameUserSettings::CurrentGraphicsSetupVersion,
            ELBGraphicsPreset::Auto, true, true, false));
    TestFalse(TEXT("An explicit named preset is retained"),
        ULBGameUserSettings::ShouldRunHardwareBenchmarkForState(
            0, ELBGraphicsPreset::High, true, true, false));
    TestFalse(TEXT("Unsupported platforms never run the PC benchmark"),
        ULBGameUserSettings::ShouldRunHardwareBenchmarkForState(
            0, ELBGraphicsPreset::Auto, false, true, false));
    TestFalse(TEXT("A caller can disable benchmarking for automation"),
        ULBGameUserSettings::ShouldRunHardwareBenchmarkForState(
            0, ELBGraphicsPreset::Auto, true, false, false));
    TestFalse(TEXT("The command-line opt-out disables benchmarking"),
        ULBGameUserSettings::ShouldRunHardwareBenchmarkForState(
            0, ELBGraphicsPreset::Auto, true, true, true));

    TestTrue(TEXT("-NoHardwareBenchmark is recognised case-insensitively"),
        ULBGameUserSettings::HasHardwareBenchmarkCommandLineOptOut(
            TEXT("LineBoss -nohardwarebenchmark -game")));
    TestFalse(TEXT("Unrelated command lines do not opt out"),
        ULBGameUserSettings::HasHardwareBenchmarkCommandLineOptOut(
            TEXT("LineBoss -game")));

    TestTrue(TEXT("Finite positive CPU/GPU scores are usable"),
        ULBGameUserSettings::AreBenchmarkScoresUsable(42.0f, 57.0f));
    TestFalse(TEXT("Engine sentinel benchmark scores trigger fallback"),
        ULBGameUserSettings::AreBenchmarkScoresUsable(-1.0f, -1.0f));
    TestFalse(TEXT("Non-finite benchmark scores trigger fallback"),
        ULBGameUserSettings::AreBenchmarkScoresUsable(
            std::numeric_limits<float>::quiet_NaN(), 57.0f));

    FString RegisteredClass;
    const bool bHasRegistration = GConfig && GConfig->GetString(
        TEXT("/Script/Engine.Engine"), TEXT("GameUserSettingsClassName"),
        RegisteredClass, GEngineIni);
    TestTrue(TEXT("DefaultEngine registers a custom settings class"), bHasRegistration);
    TestEqual(TEXT("The registered class is Line Boss' UGameUserSettings authority"),
        RegisteredClass,
        FString(TEXT("/Script/LineBossCarFactory.LBGameUserSettings")));
    TestEqual(TEXT("The settings subclass persists to GameUserSettings.ini"),
        ULBGameUserSettings::StaticClass()->GetConfigName(),
        FString(TEXT("GameUserSettings")));
    return true;
}

#endif
