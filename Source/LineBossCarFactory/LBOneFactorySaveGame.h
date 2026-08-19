#pragma once

#include "CoreMinimal.h"
#include "GameFramework/SaveGame.h"
#include "LBFactoryManagementSubsystem.h"
#include "LBOneFactoryAssemblyStarterLayout.h"
#include "LBOneFactoryBodyWeldStarterLayout.h"
#include "LBOneFactoryPaintStarterLayout.h"
#include "LBOneFactoryPressStarterLayout.h"
#include "LBOneFactoryProductionFlow.h"
#include "LBOneFactorySaveGame.generated.h"

/**
 * Complete presentation-free OneFactory snapshot.
 *
 * The four layout records own gameplay topology and station WIP reservations;
 * ProductionLedger owns each logical vehicle identity and its genealogy.  Visual
 * proxy actors are deliberately not representable in this save schema.
 */
USTRUCT(BlueprintType)
struct LINEBOSSCARFACTORY_API FLBOneFactorySaveState
{
    GENERATED_BODY()

    UPROPERTY(EditAnywhere, BlueprintReadWrite, SaveGame)
    int32 SchemaVersion = 1;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, SaveGame)
    FName SaveFormatId = NAME_None;

    /** Stable factory identity; map presentation revisions do not change it. */
    UPROPERTY(EditAnywhere, BlueprintReadWrite, SaveGame)
    FName FactoryId = NAME_None;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, SaveGame)
    int32 PayloadRevision = 0;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, SaveGame)
    FDateTime CapturedAtUtc;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, SaveGame)
    FLBOneFactoryPressStarterLayoutState PressLayout;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, SaveGame)
    FLBOneFactoryBodyWeldLayoutState BodyWeldLayout;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, SaveGame)
    FLBOneFactoryPaintStarterLayoutState PaintLayout;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, SaveGame)
    FLBOneFactoryAssemblyLayoutState AssemblyLayout;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, SaveGame)
    FLBOneFactoryProductionLedgerState ProductionLedger;

    /**
     * The management economy travels with the factory so money survives the
     * isolated OneFactory slot. Additive: old saves restore with
     * bHasManagementState false and the economy bridge re-initialises the
     * campaign on the next tick.
     */
    UPROPERTY(EditAnywhere, BlueprintReadWrite, SaveGame)
    FLBFactoryManagementSaveState Management;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, SaveGame)
    bool bHasManagementState = false;
};

/** Isolated save root. It has no inheritance or migration path to campaign saves. */
UCLASS(BlueprintType)
class LINEBOSSCARFACTORY_API ULBOneFactorySaveGame : public USaveGame
{
    GENERATED_BODY()

public:
    UPROPERTY(EditAnywhere, BlueprintReadWrite, SaveGame,
        Category="Line Boss|OneFactory|Save")
    FLBOneFactorySaveState FactoryState;

    static constexpr int32 CurrentSchemaVersion = 1;

    static FName GetSaveFormatId();
    static FName GetFactoryId();

    /** Canonical empty factory, useful for validation and in-memory tests. */
    static FLBOneFactorySaveState MakeCanonicalEmptyState();

    /**
     * Validates schema, all department snapshots, ledger genealogy,
     * commissioning agreement and cross-department WIP uniqueness.
     */
    static bool ValidateState(const FLBOneFactorySaveState& State,
        FString& OutReason);
};

