// Spacecraft-era multi-recipe crafting - engine seam #2 of the Phase-2
// scale-up (Docs/SPACECRAFT_CONTENT_CATALOGUE_v001.md section 5).
//
// A recipe is PURE DATA against the inventory ledger: inputs withdrawn,
// outputs deposited, cycle seconds. Stations own no buffers and no recipe
// logic - the player selects ONE active recipe per station (validated
// against the station's class), and a craft cycle executes atomically on
// ALBSpacecraftInventoryAuthority or not at all.
//
// The recipe table is validated for CHAIN COMPLETENESS, not just shape:
// every processed / sub-part / assembled-component item must have at least
// one producing recipe, and raw items are never craftable (they arrive
// through material intake). Adding an item without its recipe - or a recipe
// with a typo'd item - fails the table, not the player.

#pragma once

#include "CoreMinimal.h"
#include "GameFramework/Actor.h"
#include "LBSpacecraftInventoryAuthority.h"
#include "LBSpacecraftCraftingAuthority.generated.h"

/** One craftable recipe: what a station family turns into what. */
USTRUCT(BlueprintType)
struct LINEBOSSCARFACTORY_API FLBSpacecraftItemRecipe
{
	GENERATED_BODY()

	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "LineBoss")
	FName RecipeId;

	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "LineBoss")
	FString DisplayName;

	/** Station family that crafts this (matches the build-authority
	 *  station class ids, e.g. MaterialProcessor, HullFabricator). */
	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "LineBoss")
	FName StationClassId;

	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "LineBoss")
	TArray<FLBSpacecraftItemStack> Inputs;

	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "LineBoss")
	TArray<FLBSpacecraftItemStack> Outputs;

	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "LineBoss")
	double CycleSeconds = 10.0;
};

/** One station's active recipe choice (snapshot vocabulary). */
USTRUCT(BlueprintType)
struct LINEBOSSCARFACTORY_API FLBSpacecraftStationRecipeSelection
{
	GENERATED_BODY()

	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "LineBoss")
	FName StationId;

	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "LineBoss")
	FName StationClassId;

	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "LineBoss")
	FName RecipeId;

	/** Progress into the current cycle, sim seconds. Advances only while
	 *  the exchange would validate (a starved station stalls, it never
	 *  banks progress it cannot pay for). */
	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "LineBoss")
	double CycleElapsedSeconds = 0.0;

	/** Open order (owner 2026-08-26: "it should only build how many
	 *  you order"). Cycles run ONLY against this count; at zero the
	 *  machine idles with a named state - production quantity is
	 *  player intent, never inventory pressure. */
	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "LineBoss")
	int32 OrderRemaining = 0;

	/** Sub-assembly OUTPUT BUFFER beside the machine (owner 2026-08-26:
	 *  machines are sub-assembly, off the line - parts wait here until
	 *  the heavy drone hauls them to the storage zone). One entry per
	 *  crafted item; a full buffer stalls the machine fail-closed. */
	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "LineBoss")
	TArray<FName> BufferItems;
};

/** Whole-authority snapshot for the save pipeline. */
USTRUCT(BlueprintType)
struct LINEBOSSCARFACTORY_API FLBSpacecraftCraftingSnapshot
{
	GENERATED_BODY()

	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "LineBoss")
	TArray<FLBSpacecraftStationRecipeSelection> Selections;
};

/** One production run in a build plan: which recipe, on which station
 *  family, for how many cycles. */
struct FLBSpacecraftPlannedRun
{
	FName RecipeId;
	FName StationClassId;
	int32 Cycles = 0;
};

/** Static recipe catalogue: the Phase-2 production chain. */
class LINEBOSSCARFACTORY_API FLBSpacecraftRecipeCatalogue
{
public:
	static const TArray<FLBSpacecraftItemRecipe>& GetRecipeTable();

	static const FLBSpacecraftItemRecipe* FindRecipe(FName RecipeId);

	/** All recipes a station family offers (the player's pick list). */
	static TArray<FName> GetRecipesForStationClass(FName StationClassId);

	/** Shape AND chain-completeness validation (see file header). */
	static bool ValidateRecipeTable(FString& OutReason);

	/** Plans backwards from target items to the raw materials that make
	 *  them: which recipes to run, how many cycles of each, and what raw
	 *  stock the whole plan consumes. Runs come out shallowest-first;
	 *  execute them in REVERSE (deepest first) and every input exists by
	 *  the time its consumer runs. Fails closed with a named reason when
	 *  some non-raw item has no maker (an open chain) or the expansion
	 *  does not terminate.
	 *
	 *  Backwards planning is deliberate. The obvious forward simulation
	 *  - fire every satisfiable recipe until the target appears - starves
	 *  on contested intermediates (Proc.Steel has fourteen consumers and
	 *  one producer), a scheduling artefact indistinguishable from a data
	 *  fault. Planning from the target is also what a player does. */
	static bool PlanBuild(const TMap<FName, int32>& Targets,
		TArray<FLBSpacecraftPlannedRun>& OutRuns,
		TMap<FName, int32>& OutRawNeeds, FString& OutReason);
};

/**
 * Single-owner authority for per-station recipe selection and atomic
 * craft-cycle execution against the inventory ledger.
 */
UCLASS()
class LINEBOSSCARFACTORY_API ALBSpacecraftCraftingAuthority : public AActor
{
	GENERATED_BODY()

public:
	ALBSpacecraftCraftingAuthority();

	/** Sets a station's active recipe. Fails closed when the recipe is
	 *  unknown or belongs to a different station family. */
	bool SelectRecipe(FName StationId, FName StationClassId, FName RecipeId,
		FString& OutReason);

	/** Removes a station's selection (an idle station is legal). */
	bool ClearSelection(FName StationId, FString& OutReason);

	/** The station's active recipe, or nullptr when none is selected. */
	const FLBSpacecraftItemRecipe* GetSelectedRecipe(FName StationId) const;

	int32 GetSelectionCount() const { return Selections.Num(); }

	/** Executes ONE craft cycle: every input withdrawn from InputStoreId,
	 *  every output deposited to OutputStoreId - atomically. Validates the
	 *  whole exchange (including same-store freed-volume accounting) before
	 *  a single item moves. */
	bool ExecuteCraftCycle(FName StationId,
		ALBSpacecraftInventoryAuthority& Inventory, FName InputStoreId,
		FName OutputStoreId, FString& OutReason);

	/** Sim-time crafting: advances the station's cycle accumulator and
	 *  executes a full exchange each time CycleSeconds elapses (inputs and
	 *  outputs move at COMPLETION, never up front, so the ledger stays
	 *  atomic). Time only accrues while the exchange would validate - a
	 *  starved or blocked station STALLS with a reason instead of banking
	 *  progress. Returns false only on structural errors (no selection,
	 *  unregistered stores). */
	bool TickCrafting(FName StationId, double DeltaSeconds,
		ALBSpacecraftInventoryAuthority& Inventory, FName InputStoreId,
		FName OutputStoreId, int32& OutCompletedCycles, FString& OutReason);

	/** The station's progress into its current cycle, sim seconds. */
	double GetCycleElapsedSeconds(FName StationId) const;

	/** Adds Count cycles to the station's open order. */
	bool AddOrder(FName StationId, int32 Count, FString& OutReason);

	/** Cycles still owed on the station's open order. */
	int32 GetOrderRemaining(FName StationId) const;

	/** Items waiting in a station's output buffer. */
	int32 GetBufferCount(FName StationId) const;

	/** The item this machine makes (buffered head, else the recipe's
	 *  first output) - the presenter's cargo-display seam. */
	FName GetStationOutputItem(FName StationId) const;

	/** Buffer capacity shared by every sub-assembly machine
	 *  (PROVISIONAL pacing; the owner retunes). */
	UPROPERTY(EditAnywhere, Category = "LineBoss")
	int32 BufferCapacity = 6;

	/** The station whose buffer most needs a pickup (fullest buffer),
	 *  NAME_None when every buffer is empty. */
	FName FindStationWithBufferedOutput() const;

	/** Atomically moves up to MaxCount buffered items into the store -
	 *  the heavy drone's drop-off. Items that do not fit stay in the
	 *  buffer (partial haul is physically honest); refuses whole only
	 *  when the store is unknown. */
	bool TransferBufferToStore(FName StationId,
		ALBSpacecraftInventoryAuthority& Inventory, FName StoreId,
		int32 MaxCount, int32& OutMoved, FString& OutReason);

	FLBSpacecraftCraftingSnapshot CaptureSnapshot() const;
	bool RestoreSnapshot(const FLBSpacecraftCraftingSnapshot& Snapshot,
		FString& OutReason);
	static bool ValidateSnapshot(const FLBSpacecraftCraftingSnapshot& Snapshot,
		FString& OutReason);

private:
	TArray<FLBSpacecraftStationRecipeSelection> Selections;

	const FLBSpacecraftStationRecipeSelection* FindSelection(
		FName StationId) const;
	FLBSpacecraftStationRecipeSelection* FindSelectionMutable(
		FName StationId);

	/** True when one full exchange would currently succeed. */
	static bool ExchangeWouldValidate(const FLBSpacecraftItemRecipe& Recipe,
		const ALBSpacecraftInventoryAuthority& Inventory, FName InputStoreId,
		FName OutputStoreId, FString& OutReason,
		bool bOutputsToBuffer = false);
};
