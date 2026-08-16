#pragma once

#include "CoreMinimal.h"
#include "LBGameUserSettings.h"
#include "Subsystems/GameInstanceSubsystem.h"
#include "LBGraphicsStartupSubsystem.generated.h"

/** Stable process policy outcome for the one-shot graphics startup coordinator. */
UENUM()
enum class ELBGraphicsStartupCoordinatorState : uint8
{
    NotAttempted,
    Coordinated,
    AlreadyAttempted,
    SkippedNonGameProcess,
    SkippedDedicatedServer,
    SkippedCommandlet,
    SkippedAutomation,
    SettingsUnavailable
};

/**
 * Process-lifetime graphics startup authority.
 *
 * A game-instance subsystem is deliberately used instead of GameMode or WorldSubsystem:
 * the same instance survives ordinary world travel, so settings are loaded and the
 * versioned first-run graphics policy is evaluated at most once per game process.
 */
UCLASS()
class LINEBOSSCARFACTORY_API ULBGraphicsStartupSubsystem final
    : public UGameInstanceSubsystem
{
    GENERATED_BODY()

public:
    virtual void Initialize(FSubsystemCollectionBase& Collection) override;

    bool HasAttemptedStartupInitialisation() const { return bStartupAttempted; }
    ELBGraphicsStartupCoordinatorState GetCoordinatorState() const
    {
        return CoordinatorState;
    }
    ELBGraphicsSetupResult GetGraphicsSetupResult() const { return GraphicsSetupResult; }

    /** Pure policy seam used by the subsystem and focused automation tests. */
    static ELBGraphicsStartupCoordinatorState EvaluateProcessPolicy(
        bool bAlreadyAttempted,
        bool bIsGameProcess,
        bool bIsDedicatedServer,
        bool bIsCommandlet,
        bool bIsAutomationProcess);

    /** Stable tokens form the machine-readable startup log contract. */
    static const TCHAR* GetStableCoordinatorStateToken(
        ELBGraphicsStartupCoordinatorState State);
    static const TCHAR* GetStableSetupResultToken(ELBGraphicsSetupResult Result);

private:
    void LogStartupResult(
        const ULBGameUserSettings* Settings,
        bool bBenchmarkSupported,
        bool bCommandLineOptOut) const;

    bool bStartupAttempted = false;
    ELBGraphicsStartupCoordinatorState CoordinatorState =
        ELBGraphicsStartupCoordinatorState::NotAttempted;
    ELBGraphicsSetupResult GraphicsSetupResult =
        ELBGraphicsSetupResult::AlreadyInitialised;
};
