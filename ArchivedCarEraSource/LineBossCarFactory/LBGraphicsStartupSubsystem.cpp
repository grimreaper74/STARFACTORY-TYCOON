#include "LBGraphicsStartupSubsystem.h"

#include "CoreGlobals.h"
#include "Misc/App.h"
#include "Misc/CommandLine.h"
#include "Misc/CoreMisc.h"

DEFINE_LOG_CATEGORY_STATIC(LogLineBossGraphicsStartup, Log, All);

namespace
{
const TCHAR* GraphicsPresetToken(const ELBGraphicsPreset Preset)
{
    switch (Preset)
    {
    case ELBGraphicsPreset::Auto: return TEXT("Auto");
    case ELBGraphicsPreset::Low: return TEXT("Low");
    case ELBGraphicsPreset::Medium: return TEXT("Medium");
    case ELBGraphicsPreset::High: return TEXT("High");
    case ELBGraphicsPreset::Epic: return TEXT("Epic");
    case ELBGraphicsPreset::Custom: return TEXT("Custom");
    default: return TEXT("Unknown");
    }
}
}

ELBGraphicsStartupCoordinatorState ULBGraphicsStartupSubsystem::EvaluateProcessPolicy(
    const bool bAlreadyAttempted,
    const bool bIsGameProcess,
    const bool bIsDedicatedServer,
    const bool bIsCommandlet,
    const bool bIsAutomationProcess)
{
    if (bAlreadyAttempted)
        return ELBGraphicsStartupCoordinatorState::AlreadyAttempted;
    if (bIsDedicatedServer)
        return ELBGraphicsStartupCoordinatorState::SkippedDedicatedServer;
    if (bIsCommandlet)
        return ELBGraphicsStartupCoordinatorState::SkippedCommandlet;
    if (bIsAutomationProcess)
        return ELBGraphicsStartupCoordinatorState::SkippedAutomation;
    if (!bIsGameProcess)
        return ELBGraphicsStartupCoordinatorState::SkippedNonGameProcess;
    return ELBGraphicsStartupCoordinatorState::Coordinated;
}

const TCHAR* ULBGraphicsStartupSubsystem::GetStableCoordinatorStateToken(
    const ELBGraphicsStartupCoordinatorState State)
{
    switch (State)
    {
    case ELBGraphicsStartupCoordinatorState::NotAttempted: return TEXT("NotAttempted");
    case ELBGraphicsStartupCoordinatorState::Coordinated: return TEXT("Coordinated");
    case ELBGraphicsStartupCoordinatorState::AlreadyAttempted: return TEXT("AlreadyAttempted");
    case ELBGraphicsStartupCoordinatorState::SkippedNonGameProcess: return TEXT("SkippedNonGameProcess");
    case ELBGraphicsStartupCoordinatorState::SkippedDedicatedServer: return TEXT("SkippedDedicatedServer");
    case ELBGraphicsStartupCoordinatorState::SkippedCommandlet: return TEXT("SkippedCommandlet");
    case ELBGraphicsStartupCoordinatorState::SkippedAutomation: return TEXT("SkippedAutomation");
    case ELBGraphicsStartupCoordinatorState::SettingsUnavailable: return TEXT("SettingsUnavailable");
    default: return TEXT("Unknown");
    }
}

const TCHAR* ULBGraphicsStartupSubsystem::GetStableSetupResultToken(
    const ELBGraphicsSetupResult Result)
{
    switch (Result)
    {
    case ELBGraphicsSetupResult::AlreadyInitialised: return TEXT("AlreadyInitialised");
    case ELBGraphicsSetupResult::BenchmarkApplied: return TEXT("BenchmarkApplied");
    case ELBGraphicsSetupResult::FallbackApplied: return TEXT("FallbackApplied");
    case ELBGraphicsSetupResult::SkippedByPolicy: return TEXT("SkippedByPolicy");
    case ELBGraphicsSetupResult::ExistingPreferenceRetained: return TEXT("ExistingPreferenceRetained");
    default: return TEXT("Unknown");
    }
}

bool ULBGraphicsStartupSubsystem::ApplySafeDefaultFrameRateLimit(
    ULBGameUserSettings* Settings)
{
    if (!Settings || (FMath::IsFinite(Settings->GetFrameRateLimit())
            && Settings->GetFrameRateLimit() > 0.0f))
    {
        return false;
    }
    Settings->SetLineBossFrameRateLimit(60.0f);
    Settings->SetLineBossVSyncEnabled(true);
    return true;
}

void ULBGraphicsStartupSubsystem::Initialize(FSubsystemCollectionBase& Collection)
{
    Super::Initialize(Collection);

    const bool bBenchmarkSupported =
        ULBGameUserSettings::IsHardwareBenchmarkSupportedOnThisPlatform();
    const bool bCommandLineOptOut =
        ULBGameUserSettings::HasHardwareBenchmarkCommandLineOptOut(
            FCommandLine::Get());
    CoordinatorState = EvaluateProcessPolicy(
        bStartupAttempted,
        IsRunningGame(),
        IsRunningDedicatedServer(),
        IsRunningCommandlet(),
        GIsAutomationTesting || FApp::IsUnattended());
    bStartupAttempted = true;

    if (CoordinatorState != ELBGraphicsStartupCoordinatorState::Coordinated)
    {
        LogStartupResult(nullptr, bBenchmarkSupported, bCommandLineOptOut);
        return;
    }

    ULBGameUserSettings* Settings =
        ULBGameUserSettings::GetLineBossGameUserSettings();
    if (!Settings)
    {
        CoordinatorState = ELBGraphicsStartupCoordinatorState::SettingsUnavailable;
        LogStartupResult(nullptr, bBenchmarkSupported, bCommandLineOptOut);
        return;
    }

    // Loading here is intentionally idempotent and occurs after process policy. It
    // never touches editor/commandlet/automation state, and it runs before any world
    // GameMode can begin play.
    Settings->LoadSettings(false);

    // Older development builds persisted Unreal's unlimited default.  Retain a
    // player's explicit finite preference, but never let an inherited unlimited
    // value make the factory overview render flat-out on every launch.
    if (ApplySafeDefaultFrameRateLimit(Settings))
    {
        Settings->ApplyAndSaveLineBossSettings(false);
    }

    // Platform support remains an internal settings decision: unsupported platforms
    // persist their safe fallback. This flag is reserved for an explicit process
    // opt-out, which must not consume a desktop player's first-run benchmark marker.
    GraphicsSetupResult =
        Settings->InitialiseFirstRunGraphics(!bCommandLineOptOut);

    LogStartupResult(Settings, bBenchmarkSupported, bCommandLineOptOut);
}

void ULBGraphicsStartupSubsystem::LogStartupResult(
    const ULBGameUserSettings* Settings,
    const bool bBenchmarkSupported,
    const bool bCommandLineOptOut) const
{
    const TCHAR* SetupToken =
        CoordinatorState == ELBGraphicsStartupCoordinatorState::Coordinated
        ? GetStableSetupResultToken(GraphicsSetupResult)
        : TEXT("NotInvoked");
    const TCHAR* PresetToken = Settings
        ? GraphicsPresetToken(Settings->GetGraphicsPreset())
        : TEXT("Unavailable");
    const int32 SetupVersion = Settings
        ? Settings->GetGraphicsSetupVersion() : INDEX_NONE;
    const int32 BenchmarkVersion = Settings
        ? Settings->GetLastHardwareBenchmarkVersion() : INDEX_NONE;
    const int32 bFallback = Settings
        ? (Settings->UsedHardwareBenchmarkFallback() ? 1 : 0) : 0;

    UE_LOG(LogLineBossGraphicsStartup, Display,
        TEXT("LINE_BOSS_GRAPHICS_STARTUP state=%s setup=%s preset=%s setup_version=%d benchmark_version=%d fallback=%d benchmark_supported=%d command_line_opt_out=%d"),
        GetStableCoordinatorStateToken(CoordinatorState),
        SetupToken,
        PresetToken,
        SetupVersion,
        BenchmarkVersion,
        bFallback,
        bBenchmarkSupported ? 1 : 0,
        bCommandLineOptOut ? 1 : 0);
}
