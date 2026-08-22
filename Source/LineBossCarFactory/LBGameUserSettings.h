#pragma once

#include "CoreMinimal.h"
#include "GameFramework/GameUserSettings.h"
#include "LBGameUserSettings.generated.h"

/** Player-facing quality choices. Auto is benchmark driven; Custom is a mixed quality state. */
UENUM(BlueprintType)
enum class ELBGraphicsPreset : uint8
{
    Auto UMETA(DisplayName="Auto"),
    Low UMETA(DisplayName="Low"),
    Medium UMETA(DisplayName="Medium"),
    High UMETA(DisplayName="High"),
    Epic UMETA(DisplayName="Epic"),
    Custom UMETA(DisplayName="Custom")
};

/** Outcome of the bounded first-run graphics setup. */
UENUM(BlueprintType)
enum class ELBGraphicsSetupResult : uint8
{
    AlreadyInitialised,
    BenchmarkApplied,
    FallbackApplied,
    SkippedByPolicy,
    ExistingPreferenceRetained
};

/**
 * Line Boss' local-machine graphics settings authority.
 *
 * Display state and scalability remain owned and persisted by UGameUserSettings. This
 * subclass adds only the player-facing preset identity and versioned Auto setup policy.
 */
UCLASS(Config=GameUserSettings)
class LINEBOSSCARFACTORY_API ULBGameUserSettings final : public UGameUserSettings
{
    GENERATED_BODY()

public:
    static constexpr int32 CurrentGraphicsSetupVersion = 1;
    static constexpr int32 CurrentHardwareBenchmarkVersion = 1;

    virtual void SetToDefaults() override;
    virtual void LoadSettings(bool bForceReload = false) override;

    /** Returns the configured engine singleton, or null if project registration is broken. */
    UFUNCTION(BlueprintPure, Category="Line Boss|Settings|Graphics")
    static ULBGameUserSettings* GetLineBossGameUserSettings();

    UFUNCTION(BlueprintPure, Category="Line Boss|Settings|Graphics")
    ELBGraphicsPreset GetGraphicsPreset() const { return SelectedGraphicsPreset; }

    /** Updates cached scalability state. Auto is resolved separately by InitialiseFirstRunGraphics. */
    UFUNCTION(BlueprintCallable, Category="Line Boss|Settings|Graphics")
    bool SetGraphicsPreset(ELBGraphicsPreset NewPreset);

    UFUNCTION(BlueprintPure, Category="Line Boss|Settings|Graphics")
    bool IsFirstRunGraphicsSetupNeeded() const;

    /**
     * Resolves Auto once per policy version. Desktop PCs benchmark; unsupported platforms
     * and invalid results receive a safe Medium fallback. -NoHardwareBenchmark skips the
     * benchmark without consuming the player's future first-run benchmark.
     */
    UFUNCTION(BlueprintCallable, Category="Line Boss|Settings|Graphics",
        meta=(bAllowHardwareBenchmark=true))
    ELBGraphicsSetupResult InitialiseFirstRunGraphics(bool bAllowHardwareBenchmark = true);

    UFUNCTION(BlueprintPure, Category="Line Boss|Settings|Graphics")
    int32 GetGraphicsSetupVersion() const { return GraphicsSetupVersion; }

    UFUNCTION(BlueprintPure, Category="Line Boss|Settings|Graphics")
    int32 GetLastHardwareBenchmarkVersion() const { return LastHardwareBenchmarkVersion; }

    UFUNCTION(BlueprintPure, Category="Line Boss|Settings|Graphics")
    bool UsedHardwareBenchmarkFallback() const { return bUsedHardwareBenchmarkFallback; }

    /** Display wrappers deliberately delegate to UGameUserSettings instead of duplicating state. */
    UFUNCTION(BlueprintCallable, Category="Line Boss|Settings|Display")
    bool SetLineBossScreenResolution(FIntPoint Resolution);

    UFUNCTION(BlueprintCallable, Category="Line Boss|Settings|Display")
    bool SetLineBossWindowMode(EWindowMode::Type WindowMode);

    UFUNCTION(BlueprintCallable, Category="Line Boss|Settings|Display")
    void SetLineBossVSyncEnabled(bool bEnabled);

    /** Zero disables the cap; finite non-negative values are passed to UGameUserSettings. */
    UFUNCTION(BlueprintCallable, Category="Line Boss|Settings|Display")
    bool SetLineBossFrameRateLimit(float FramesPerSecond);

    /** Sets engine resolution quality in percent and marks the quality preset Custom. */
    UFUNCTION(BlueprintCallable, Category="Line Boss|Settings|Graphics")
    bool SetLineBossRenderScale(float Percentage);

    UFUNCTION(BlueprintPure, Category="Line Boss|Settings|Graphics")
    float GetLineBossRenderScale() const;

    /** ApplySettings is the engine authority and also persists the pending settings. */
    UFUNCTION(BlueprintCallable, Category="Line Boss|Settings")
    void ApplyAndSaveLineBossSettings(bool bCheckForCommandLineOverrides = true);

    /** Pure seams used by startup code and automation without running the benchmark. */
    static bool TryGetScalabilityLevelForPreset(ELBGraphicsPreset Preset, int32& OutLevel);
    static bool HasHardwareBenchmarkCommandLineOptOut(const TCHAR* CommandLine);
    static bool ShouldRunHardwareBenchmarkForState(
        int32 ExistingSetupVersion,
        ELBGraphicsPreset ExistingPreset,
        bool bPlatformSupportsBenchmark,
        bool bAllowedByCaller,
        bool bCommandLineOptOut);
    static bool AreBenchmarkScoresUsable(float CPUScore, float GPUScore);
    static bool IsHardwareBenchmarkSupportedOnThisPlatform();

private:
    UPROPERTY(Config)
    int32 GraphicsSetupVersion = 0;

    UPROPERTY(Config)
    int32 LastHardwareBenchmarkVersion = 0;

    UPROPERTY(Config)
    ELBGraphicsPreset SelectedGraphicsPreset = ELBGraphicsPreset::Auto;

    UPROPERTY(Config)
    bool bUsedHardwareBenchmarkFallback = false;

    static bool IsKnownPreset(ELBGraphicsPreset Preset);
    void CacheSafeFallback(bool bMarkSetupComplete);
};
