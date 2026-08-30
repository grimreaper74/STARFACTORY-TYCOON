// Spacecraft-era save slot: the factory layout, production ledger, runtime
// assignments AND the Phase-2 authorities (inventory, crafting, power,
// research) captured TOGETHER, so a load can never mix states from
// different sessions. Restore is rollback-safe: each subsystem validates
// before applying, and any failure restores the pre-load state wholesale -
// invalid data never partly applies.

#pragma once

#include "CoreMinimal.h"
#include "GameFramework/SaveGame.h"
#include "LBSpacecraftBuildAuthority.h"
#include "LBSpacecraftCraftingAuthority.h"
#include "LBSpacecraftDroneFleetAuthority.h"
#include "LBSpacecraftInventoryAuthority.h"
#include "LBSpacecraftPowerAuthority.h"
#include "LBSpacecraftReputationAuthority.h"
#include "LBSpacecraftTransportAuthority.h"
#include "LBSpacecraftTrackAuthority.h"
#include "LBSpacecraftProgressionAuthority.h"
#include "LBSpacecraftProductionAuthority.h"
#include "LBSpacecraftResearchAuthority.h"
#include "LBSpacecraftRuntimeCoordinator.h"
#include "LBSpacecraftSaveGame.generated.h"

UCLASS()
class LINEBOSSCARFACTORY_API ULBSpacecraftSaveGame : public USaveGame
{
	GENERATED_BODY()

public:
	/** Bump on any breaking change to the saved structs; loads of another
	 *  version are refused outright (no migration yet - pre-release saves
	 *  carry no player investment worth migrating).
	 *  v2 (2026-08-24): Phase-2 snapshots added (inventory, crafting,
	 *  power, research).
	 *  v3 (2026-08-25): drone fleet (batteries + charge loads) added.
	 *  v4 (2026-08-25): player cash joined the production ledger;
	 *  reputation snapshot added the same day.
	 *  v7 (2026-08-26): the LINE TRACK joined the save (laid pieces +
	 *  station nodes). */
	static constexpr int32 CurrentSchemaVersion = 7;

	UPROPERTY()
	int32 SchemaVersion = CurrentSchemaVersion;

	UPROPERTY()
	FLBSpacecraftFactoryLayoutState FactoryLayout;

	UPROPERTY()
	FLBSpacecraftProductionLedgerState Ledger;

	UPROPERTY()
	FLBSpacecraftRuntimeState Runtime;

	UPROPERTY()
	FLBSpacecraftInventorySnapshot Inventory;

	UPROPERTY()
	FLBSpacecraftCraftingSnapshot Crafting;

	UPROPERTY()
	FLBSpacecraftPowerSnapshot Power;

	UPROPERTY()
	FLBSpacecraftResearchSnapshot Research;

	UPROPERTY()
	FLBSpacecraftDroneFleetSnapshot DroneFleet;

	UPROPERTY()
	FLBSpacecraftReputationSnapshot Reputation;

	UPROPERTY(SaveGame)
	FLBSpacecraftTransportSnapshot Transport;

	UPROPERTY(SaveGame)
	FLBSpacecraftProgressionSnapshot Progression;

	UPROPERTY(SaveGame)
	FLBSpacecraftTrackSnapshot LineTrack;
};

/** Every authority a save touches, gathered once. ALL are required: a
 *  save that silently skipped a subsystem would load as data loss. */
struct LINEBOSSCARFACTORY_API FLBSpacecraftSaveContext
{
	ALBSpacecraftBuildAuthority* Build = nullptr;
	ALBSpacecraftProductionAuthority* Production = nullptr;
	ALBSpacecraftRuntimeCoordinator* Coordinator = nullptr;
	ALBSpacecraftInventoryAuthority* Inventory = nullptr;
	ALBSpacecraftCraftingAuthority* Crafting = nullptr;
	ALBSpacecraftPowerAuthority* Power = nullptr;
	ALBSpacecraftResearchAuthority* Research = nullptr;
	ALBSpacecraftDroneFleetAuthority* DroneFleet = nullptr;
	ALBSpacecraftReputationAuthority* Reputation = nullptr;
	ALBSpacecraftTransportAuthority* Transport = nullptr;
	ALBSpacecraftProgressionAuthority* Progression = nullptr;
	class ALBSpacecraftTrackAuthority* Track = nullptr;

	bool IsComplete() const
	{
		return Build != nullptr && Production != nullptr
			&& Coordinator != nullptr && Inventory != nullptr
			&& Crafting != nullptr && Power != nullptr
			&& Research != nullptr && DroneFleet != nullptr
			&& Reputation != nullptr && Transport != nullptr
			&& Progression != nullptr && Track != nullptr;
	}
};

/** Static save/load pipeline - testable without a game mode. */
class LINEBOSSCARFACTORY_API FLBSpacecraftSavePipeline
{
public:
	static bool SaveToSlot(const FLBSpacecraftSaveContext& Context,
		const FString& SlotName, FString& OutReason);

	/** Applies layout -> ledger -> inventory -> crafting -> power ->
	 *  research -> (reconfigure) -> runtime. Any failure rolls every
	 *  subsystem back to its pre-load state and reports why. */
	static bool LoadFromSlot(const FLBSpacecraftSaveContext& Context,
		const FString& SlotName, FString& OutReason);
};
