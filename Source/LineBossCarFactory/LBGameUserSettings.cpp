#include "LBGameUserSettings.h"

#include "Misc/App.h"
#include "Misc/CommandLine.h"
#include "Misc/Parse.h"

void ULBGameUserSettings::SetToDefaults()
{
    Super::SetToDefaults();
    GraphicsSetupVersion = 0;
    LastHardwareBenchmarkVersion = 0;
    SelectedGraphicsPreset = ELBGraphicsPreset::Auto;
    bUsedHardwareBenchmarkFallback = false;
}

void ULBGameUserSettings::LoadSettings(const bool bForceReload)
{
    Super::LoadSettings(bForceReload);

    if (GraphicsSetupVersion < 0 || GraphicsSetupVersion > CurrentGraphicsSetupVersion)
        GraphicsSetupVersion = 0;
    if (LastHardwareBenchmarkVersion < 0
        || LastHardwareBenchmarkVersion > CurrentHardwareBenchmarkVersion)
        LastHardwareBenchmarkVersion = 0;
    if (!IsKnownPreset(SelectedGraphicsPreset))
    {
        SelectedGraphicsPreset = ELBGraphicsPreset::Auto;
        GraphicsSetupVersion = 0;
        bUsedHardwareBenchmarkFallback = false;
    }
}

ULBGameUserSettings* ULBGameUserSettings::GetLineBossGameUserSettings()
{
    return Cast<ULBGameUserSettings>(UGameUserSettings::GetGameUserSettings());
}

bool ULBGameUserSettings::IsKnownPreset(const ELBGraphicsPreset Preset)
{
    switch (Preset)
    {
    case ELBGraphicsPreset::Auto:
    case ELBGraphicsPreset::Low:
    case ELBGraphicsPreset::Medium:
    case ELBGraphicsPreset::High:
    case ELBGraphicsPreset::Epic:
    case ELBGraphicsPreset::Custom:
        return true;
    default:
        return false;
    }
}

bool ULBGameUserSettings::TryGetScalabilityLevelForPreset(
    const ELBGraphicsPreset Preset, int32& OutLevel)
{
    switch (Preset)
    {
    case ELBGraphicsPreset::Low:
        OutLevel = 0;
        return true;
    case ELBGraphicsPreset::Medium:
        OutLevel = 1;
        return true;
    case ELBGraphicsPreset::High:
        OutLevel = 2;
        return true;
    case ELBGraphicsPreset::Epic:
        OutLevel = 3;
        return true;
    default:
        OutLevel = INDEX_NONE;
        return false;
    }
}

bool ULBGameUserSettings::SetGraphicsPreset(const ELBGraphicsPreset NewPreset)
{
    if (!IsKnownPreset(NewPreset)) return false;

    int32 ScalabilityLevel = INDEX_NONE;
    if (TryGetScalabilityLevelForPreset(NewPreset, ScalabilityLevel))
    {
        Super::SetOverallScalabilityLevel(ScalabilityLevel);
        GraphicsSetupVersion = CurrentGraphicsSetupVersion;
    }
    else if (NewPreset == ELBGraphicsPreset::Auto)
    {
        // Choosing Auto explicitly queues the current benchmark policy for the settings
        // coordinator; a menu click never starts a blocking benchmark by surprise.
        GraphicsSetupVersion = 0;
    }
    else
    {
        GraphicsSetupVersion = CurrentGraphicsSetupVersion;
    }

    SelectedGraphicsPreset = NewPreset;
    bUsedHardwareBenchmarkFallback = false;
    return true;
}

bool ULBGameUserSettings::IsFirstRunGraphicsSetupNeeded() const
{
    return GraphicsSetupVersion < CurrentGraphicsSetupVersion;
}

bool ULBGameUserSettings::HasHardwareBenchmarkCommandLineOptOut(const TCHAR* CommandLine)
{
    return CommandLine && FParse::Param(CommandLine, TEXT("NoHardwareBenchmark"));
}

bool ULBGameUserSettings::ShouldRunHardwareBenchmarkForState(
    const int32 ExistingSetupVersion,
    const ELBGraphicsPreset ExistingPreset,
    const bool bPlatformSupportsBenchmark,
    const bool bAllowedByCaller,
    const bool bCommandLineOptOut)
{
    return ExistingSetupVersion < CurrentGraphicsSetupVersion
        && ExistingPreset == ELBGraphicsPreset::Auto
        && bPlatformSupportsBenchmark
        && bAllowedByCaller
        && !bCommandLineOptOut;
}

bool ULBGameUserSettings::AreBenchmarkScoresUsable(const float CPUScore, const float GPUScore)
{
    return FMath::IsFinite(CPUScore) && FMath::IsFinite(GPUScore)
        && CPUScore > 0.0f && GPUScore > 0.0f;
}

bool ULBGameUserSettings::IsHardwareBenchmarkSupportedOnThisPlatform()
{
#if PLATFORM_WINDOWS || PLATFORM_LINUX || PLATFORM_MAC
    return FApp::CanEverRender() && !IsRunningDedicatedServer();
#else
    // Console/device profiles will own calibrated defaults; the PC synthetic benchmark
    // must never become an accidental console startup dependency.
    return false;
#endif
}

void ULBGameUserSettings::CacheSafeFallback(const bool bMarkSetupComplete)
{
    // The factory is large enough that a failed or skipped benchmark must not
    // default to a hot, expensive profile. Medium is the safe playable floor;
    // the Settings screen leaves High and Epic as explicit player choices.
    int32 MediumLevel = 1;
    TryGetScalabilityLevelForPreset(ELBGraphicsPreset::Medium, MediumLevel);
    Super::SetOverallScalabilityLevel(MediumLevel);
    SelectedGraphicsPreset = ELBGraphicsPreset::Auto;
    bUsedHardwareBenchmarkFallback = true;
    if (bMarkSetupComplete)
    {
        GraphicsSetupVersion = CurrentGraphicsSetupVersion;
        LastHardwareBenchmarkVersion = 0;
    }
}

ELBGraphicsSetupResult ULBGameUserSettings::InitialiseFirstRunGraphics(
    const bool bAllowHardwareBenchmark)
{
    if (!IsFirstRunGraphicsSetupNeeded())
        return ELBGraphicsSetupResult::AlreadyInitialised;

    // An explicit Low-Epic/Custom preference always wins over a later policy-version bump.
    if (SelectedGraphicsPreset != ELBGraphicsPreset::Auto)
    {
        GraphicsSetupVersion = CurrentGraphicsSetupVersion;
        bUsedHardwareBenchmarkFallback = false;
        SaveSettings();
        return ELBGraphicsSetupResult::ExistingPreferenceRetained;
    }

    const bool bPlatformSupportsBenchmark = IsHardwareBenchmarkSupportedOnThisPlatform();
    const bool bCommandLineOptOut =
        HasHardwareBenchmarkCommandLineOptOut(FCommandLine::Get());
    const bool bShouldBenchmark = ShouldRunHardwareBenchmarkForState(
        GraphicsSetupVersion, SelectedGraphicsPreset, bPlatformSupportsBenchmark,
        bAllowHardwareBenchmark, bCommandLineOptOut);

    if (!bShouldBenchmark)
    {
        // Automation/caller opt-out is deliberately non-persistent, so it cannot consume
        // the player's real first-run Auto benchmark. Unsupported platforms persist their
        // safe device-profile-compatible fallback and never retry the PC benchmark.
        const bool bSkippedByAutomationPolicy = !bAllowHardwareBenchmark
            || bCommandLineOptOut;
        const bool bPersistFallback = !bSkippedByAutomationPolicy;
        CacheSafeFallback(bPersistFallback);
        ApplyNonResolutionSettings();
        if (bPersistFallback)
        {
            SaveSettings();
            return ELBGraphicsSetupResult::FallbackApplied;
        }
        return ELBGraphicsSetupResult::SkippedByPolicy;
    }

    RunHardwareBenchmark();
    if (AreBenchmarkScoresUsable(
        GetLastCPUBenchmarkResult(), GetLastGPUBenchmarkResult()))
    {
        GraphicsSetupVersion = CurrentGraphicsSetupVersion;
        LastHardwareBenchmarkVersion = CurrentHardwareBenchmarkVersion;
        SelectedGraphicsPreset = ELBGraphicsPreset::Auto;
        bUsedHardwareBenchmarkFallback = false;
        ApplyHardwareBenchmarkResults();
        return ELBGraphicsSetupResult::BenchmarkApplied;
    }

    CacheSafeFallback(true);
    // A failed synthetic benchmark must not defeat explicit launch-time display
    // overrides such as -ResX/-ResY/-WINDOWED. The fallback changes quality only;
    // ApplySettings remains the engine authority and checks those overrides here.
    ApplySettings(true);
    return ELBGraphicsSetupResult::FallbackApplied;
}

bool ULBGameUserSettings::SetLineBossScreenResolution(const FIntPoint Resolution)
{
    if (Resolution.X <= 0 || Resolution.Y <= 0) return false;
    SetScreenResolution(Resolution);
    return true;
}

bool ULBGameUserSettings::SetLineBossWindowMode(const EWindowMode::Type WindowMode)
{
    if (WindowMode != EWindowMode::Fullscreen
        && WindowMode != EWindowMode::WindowedFullscreen
        && WindowMode != EWindowMode::Windowed)
        return false;
    SetFullscreenMode(WindowMode);
    return true;
}

void ULBGameUserSettings::SetLineBossVSyncEnabled(const bool bEnabled)
{
    SetVSyncEnabled(bEnabled);
}

bool ULBGameUserSettings::SetLineBossFrameRateLimit(const float FramesPerSecond)
{
    if (!FMath::IsFinite(FramesPerSecond) || FramesPerSecond < 0.0f) return false;
    SetFrameRateLimit(FramesPerSecond);
    return true;
}

bool ULBGameUserSettings::SetLineBossRenderScale(const float Percentage)
{
    if (!FMath::IsFinite(Percentage)) return false;
    SetResolutionScaleValueEx(Percentage);
    SelectedGraphicsPreset = ELBGraphicsPreset::Custom;
    GraphicsSetupVersion = CurrentGraphicsSetupVersion;
    bUsedHardwareBenchmarkFallback = false;
    return true;
}

float ULBGameUserSettings::GetLineBossRenderScale() const
{
    float Normalized = 0.0f;
    float Current = 100.0f;
    float Minimum = 0.0f;
    float Maximum = 100.0f;
    GetResolutionScaleInformationEx(Normalized, Current, Minimum, Maximum);
    return Current;
}

void ULBGameUserSettings::ApplyAndSaveLineBossSettings(
    const bool bCheckForCommandLineOverrides)
{
    ApplySettings(bCheckForCommandLineOverrides);
}
