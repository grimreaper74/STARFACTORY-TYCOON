#pragma once

#include "CoreMinimal.h"
#include "LBSpacecraftDifficulty.h"
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

    /** Spacecraft-era player preferences: audio and camera feel. The
     *  clamps are the contract - out-of-range config never applies. */
    static constexpr float MinCameraSpeedScale = 0.25f;
    static constexpr float MaxCameraSpeedScale = 2.0f;

    UFUNCTION(BlueprintPure, Category="Line Boss|Settings|Audio")
    float GetMasterVolume() const { return MasterVolume; }

    UFUNCTION(BlueprintCallable, Category="Line Boss|Settings|Audio")
    void SetMasterVolume(float NewVolume);

    /** Pushes the master volume onto the world's audio device (transient
     *  by engine design - reapplied at startup and on change). Safe with
     *  no audio device (-nosound / NullRHI automation). */
    void ApplyMasterVolumeToWorld(UWorld* World) const;

    UFUNCTION(BlueprintPure, Category="Line Boss|Settings|Camera")
    bool IsEdgeScrollEnabled() const { return bEdgeScrollEnabled; }

    UFUNCTION(BlueprintCallable, Category="Line Boss|Settings|Camera")
    void SetEdgeScrollEnabled(bool bEnabled) { bEdgeScrollEnabled = bEnabled; }

    UFUNCTION(BlueprintPure, Category="Line Boss|Settings|Camera")
    float GetCameraPanSpeedScale() const { return CameraPanSpeedScale; }

    UFUNCTION(BlueprintCallable, Category="Line Boss|Settings|Camera")
    void SetCameraPanSpeedScale(float NewScale);

    UFUNCTION(BlueprintPure, Category="Line Boss|Settings|Camera")
    float GetCameraZoomSpeedScale() const { return CameraZoomSpeedScale; }

    UFUNCTION(BlueprintCallable, Category="Line Boss|Settings|Camera")
    void SetCameraZoomSpeedScale(float NewScale);

    UFUNCTION(BlueprintPure, Category="Line Boss|Settings|Camera")
    bool IsZoomInverted() const { return bInvertZoom; }

    UFUNCTION(BlueprintCallable, Category="Line Boss|Settings|Camera")
    void SetZoomInverted(bool bInverted) { bInvertZoom = bInverted; }

    /** Pure clamp seams shared with automation. */
    static float ClampMasterVolume01(float Volume);
    static float ClampCameraSpeedScale(float Scale);

    /** Pure seams used by startup code and automation without running the benchmark. */
    static bool TryGetScalabilityLevelForPreset(ELBGraphicsPreset Preset, int32& OutLevel);
    static bool HasHardwareBenchmarkCommandLineOptOut(const TCHAR* CommandLine);
    static bool ShouldRunHardwareBenchmarkForState(
        int32 ExistingSetupVersion,
        ELBGraphicsPreset ExistingPreset,
        bool bPlatformSupportsBenchmark,
        bool bAllowedByCaller,
        bool bCommandLineOptOut);
    /** GAMEPLAY DIFFICULTY (owner 2026-08-27). Unreal has no notion of
     *  one - GameUserSettings is graphics scalability - so it is kept
     *  here beside the other player choices and persisted the same way.
     *  Applied to the running game by the spacecraft game mode. */
    ELBSpacecraftDifficulty GetSpacecraftDifficulty() const
    {
        return SpacecraftDifficulty;
    }
    void SetSpacecraftDifficulty(ELBSpacecraftDifficulty Difficulty);

    static bool AreBenchmarkScoresUsable(float CPUScore, float GPUScore);
    static bool IsHardwareBenchmarkSupportedOnThisPlatform();

private:
    UPROPERTY(Config)
    ELBSpacecraftDifficulty SpacecraftDifficulty =
        ELBSpacecraftDifficulty::Standard;

    UPROPERTY(Config)
    int32 GraphicsSetupVersion = 0;

    UPROPERTY(Config)
    int32 LastHardwareBenchmarkVersion = 0;

    UPROPERTY(Config)
    ELBGraphicsPreset SelectedGraphicsPreset = ELBGraphicsPreset::Auto;

    UPROPERTY(Config)
    bool bUsedHardwareBenchmarkFallback = false;

    UPROPERTY(Config)
    float MasterVolume = 1.0f;

    UPROPERTY(Config)
    bool bEdgeScrollEnabled = false;

    UPROPERTY(Config)
    float CameraPanSpeedScale = 1.0f;

    UPROPERTY(Config)
    float CameraZoomSpeedScale = 1.0f;

    UPROPERTY(Config)
    bool bInvertZoom = false;

    static bool IsKnownPreset(ELBGraphicsPreset Preset);
    void CacheSafeFallback(bool bMarkSetupComplete);
};
