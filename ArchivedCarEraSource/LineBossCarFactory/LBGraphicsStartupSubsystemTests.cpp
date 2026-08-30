#include "LBGraphicsStartupSubsystem.h"

#include "Misc/AutomationTest.h"
#include "Scalability.h"

#if WITH_DEV_AUTOMATION_TESTS

IMPLEMENT_SIMPLE_AUTOMATION_TEST(FLBGraphicsStartupProcessLifetimePolicyTest,
    "LineBoss.Settings.Graphics.Startup.ProcessLifetimePolicy",
    EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)

bool FLBGraphicsStartupProcessLifetimePolicyTest::RunTest(const FString& Parameters)
{
    using EState = ELBGraphicsStartupCoordinatorState;

    TestEqual(TEXT("A fresh normal game process coordinates graphics startup"),
        ULBGraphicsStartupSubsystem::EvaluateProcessPolicy(
            false, true, false, false, false),
        EState::Coordinated);
    TestEqual(TEXT("A second invocation in the same game instance is rejected"),
        ULBGraphicsStartupSubsystem::EvaluateProcessPolicy(
            true, true, false, false, false),
        EState::AlreadyAttempted);
    TestEqual(TEXT("Ordinary map travel cannot create a second startup decision"),
        ULBGraphicsStartupSubsystem::EvaluateProcessPolicy(
            true, true, false, false, false),
        EState::AlreadyAttempted);

    TestEqual(TEXT("PIE/editor processes do not alter player machine settings"),
        ULBGraphicsStartupSubsystem::EvaluateProcessPolicy(
            false, false, false, false, false),
        EState::SkippedNonGameProcess);
    TestEqual(TEXT("Dedicated servers never coordinate graphics settings"),
        ULBGraphicsStartupSubsystem::EvaluateProcessPolicy(
            false, false, true, false, false),
        EState::SkippedDedicatedServer);
    TestEqual(TEXT("Commandlets never coordinate graphics settings"),
        ULBGraphicsStartupSubsystem::EvaluateProcessPolicy(
            false, false, false, true, false),
        EState::SkippedCommandlet);
    TestEqual(TEXT("Unattended automation never runs a startup benchmark"),
        ULBGraphicsStartupSubsystem::EvaluateProcessPolicy(
            false, true, false, false, true),
        EState::SkippedAutomation);
    TestFalse(TEXT("A coordinated console launch still cannot run the PC benchmark"),
        ULBGameUserSettings::ShouldRunHardwareBenchmarkForState(
            0, ELBGraphicsPreset::Auto, false, true, false));
    TestFalse(TEXT("The command-line opt-out reaches the non-benchmark policy path"),
        ULBGameUserSettings::ShouldRunHardwareBenchmarkForState(
            0, ELBGraphicsPreset::Auto, true, true, true));
    return true;
}

IMPLEMENT_SIMPLE_AUTOMATION_TEST(FLBGraphicsStartupStableLogContractTest,
    "LineBoss.Settings.Graphics.Startup.StableLogContract",
    EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)

bool FLBGraphicsStartupStableLogContractTest::RunTest(const FString& Parameters)
{
    TestEqual(TEXT("Coordinated state has a stable machine-readable token"),
        FString(ULBGraphicsStartupSubsystem::GetStableCoordinatorStateToken(
            ELBGraphicsStartupCoordinatorState::Coordinated)),
        FString(TEXT("Coordinated")));
    TestEqual(TEXT("Automation suppression has a stable machine-readable token"),
        FString(ULBGraphicsStartupSubsystem::GetStableCoordinatorStateToken(
            ELBGraphicsStartupCoordinatorState::SkippedAutomation)),
        FString(TEXT("SkippedAutomation")));
    TestEqual(TEXT("Benchmark success has a stable machine-readable token"),
        FString(ULBGraphicsStartupSubsystem::GetStableSetupResultToken(
            ELBGraphicsSetupResult::BenchmarkApplied)),
        FString(TEXT("BenchmarkApplied")));
    TestEqual(TEXT("Command-line/caller opt-out has a stable result token"),
        FString(ULBGraphicsStartupSubsystem::GetStableSetupResultToken(
            ELBGraphicsSetupResult::SkippedByPolicy)),
        FString(TEXT("SkippedByPolicy")));
    return true;
}

IMPLEMENT_SIMPLE_AUTOMATION_TEST(FLBGraphicsStartupOptOutMarkerTest,
    "LineBoss.Settings.Graphics.Startup.OptOutDoesNotConsumeMarker",
    EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)

bool FLBGraphicsStartupOptOutMarkerTest::RunTest(const FString& Parameters)
{
    const Scalability::FQualityLevels PreviousQuality =
        Scalability::GetQualityLevels();
    ULBGameUserSettings* Settings = NewObject<ULBGameUserSettings>();
    TestNotNull(TEXT("A fresh settings authority exists"), Settings);
    if (!Settings) return false;

    Settings->SetToDefaults();
    const ELBGraphicsSetupResult Result =
        Settings->InitialiseFirstRunGraphics(false);
    TestEqual(TEXT("A disabled benchmark reports a policy skip"),
        Result, ELBGraphicsSetupResult::SkippedByPolicy);
    TestEqual(TEXT("A disabled benchmark does not consume the setup marker"),
        Settings->GetGraphicsSetupVersion(), 0);
    TestEqual(TEXT("A disabled benchmark does not claim a benchmark version"),
        Settings->GetLastHardwareBenchmarkVersion(), 0);
    TestEqual(TEXT("A skipped benchmark uses the cool Medium fallback"),
        Settings->GetOverallScalabilityLevel(), 1);
    TestTrue(TEXT("The next normal launch still needs first-run graphics setup"),
        Settings->IsFirstRunGraphicsSetupNeeded());
    Scalability::SetQualityLevels(PreviousQuality);
    return true;
}

IMPLEMENT_SIMPLE_AUTOMATION_TEST(FLBGraphicsStartupSafeFrameCapTest,
    "LineBoss.Settings.Graphics.Startup.SafeFrameCap",
    EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)

bool FLBGraphicsStartupSafeFrameCapTest::RunTest(const FString& Parameters)
{
    ULBGameUserSettings* Settings = NewObject<ULBGameUserSettings>();
    TestNotNull(TEXT("A settings authority exists for the safe-cap policy"), Settings);
    if (!Settings) return false;

    Settings->SetFrameRateLimit(0.0f);
    TestTrue(TEXT("An inherited unlimited rate is capped"),
        ULBGraphicsStartupSubsystem::ApplySafeDefaultFrameRateLimit(Settings));
    TestEqual(TEXT("The safe default is 60 FPS"),
        Settings->GetFrameRateLimit(), 60.0f);
    TestTrue(TEXT("The safe default enables VSync"), Settings->IsVSyncEnabled());

    Settings->SetFrameRateLimit(120.0f);
    TestFalse(TEXT("An explicit finite preference is retained"),
        ULBGraphicsStartupSubsystem::ApplySafeDefaultFrameRateLimit(Settings));
    TestEqual(TEXT("The finite preference is unchanged"),
        Settings->GetFrameRateLimit(), 120.0f);
    return true;
}

#endif
