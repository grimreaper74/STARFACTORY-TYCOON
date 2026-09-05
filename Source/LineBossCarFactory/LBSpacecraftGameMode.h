// Spacecraft-era game mode: wires the build authority, production ledger,
// runtime coordinator and WIP presenter into a world, and hosts the
// LB.Spacecraft.* developer console commands that drive the line headlessly
// (registered as console commands, not exec functions, so they work in the
// editor, in -game, and under -ExecCmds in an unattended -NullRHI run).
//
// The premade-factory contract carries over: BeginPlay spawns EMPTY
// authorities. Stations exist only after the player - or the dev command -
// places and commissions them through the normal build authority.

#pragma once

#include "CoreMinimal.h"
#include "GameFramework/GameModeBase.h"
#include "LBSpacecraftBuildAuthority.h"
#include "LBSpacecraftCraftingAuthority.h"
#include "LBSpacecraftDroneFleetAuthority.h"
#include "LBSpacecraftInventoryAuthority.h"
#include "LBSpacecraftPowerAuthority.h"
#include "LBSpacecraftProductionAuthority.h"
#include "LBSpacecraftResearchAuthority.h"
#include "LBSpacecraftRuntimeCoordinator.h"
#include "LBSpacecraftGameMode.generated.h"

struct FLBSpacecraftSaveContext;
class ALBSpacecraftWIPPresentationActor;
class ULBSpacecraftTopBarWidget;

UCLASS()
class LINEBOSSCARFACTORY_API ALBSpacecraftGameMode : public AGameModeBase
{
	GENERATED_BODY()

public:
	ALBSpacecraftGameMode();

	virtual void BeginPlay() override;
	virtual void Tick(float DeltaSeconds) override;

	ALBSpacecraftBuildAuthority* GetBuildAuthority() const
	{
		return BuildAuthority;
	}
	ALBSpacecraftProductionAuthority* GetProductionAuthority() const
	{
		return ProductionAuthority;
	}
	ALBSpacecraftRuntimeCoordinator* GetCoordinator() const
	{
		return Coordinator;
	}
	ALBSpacecraftInventoryAuthority* GetInventoryAuthority() const
	{
		return InventoryAuthority;
	}
	ALBSpacecraftCraftingAuthority* GetCraftingAuthority() const
	{
		return CraftingAuthority;
	}
	ALBSpacecraftPowerAuthority* GetPowerAuthority() const
	{
		return PowerAuthority;
	}
	ALBSpacecraftResearchAuthority* GetResearchAuthority() const
	{
		return ResearchAuthority;
	}
	ALBSpacecraftDroneFleetAuthority* GetDroneFleet() const
	{
		return DroneFleet;
	}
	class ALBSpacecraftTransportAuthority* GetTransportAuthority() const
	{
		return Transport;
	}

	class ALBSpacecraftTrackAuthority* GetTrackAuthority() const
	{
		return TrackAuthority;
	}

	/** CLICK-TO-DRAW track laying (owner 2026-09-01). First click
	 *  anchors the line at the clicked cell facing GhostYawDeg; every
	 *  later click routes the open end to the clicked cell through the
	 *  authority's pure planner and lays the pieces one PAID step at a
	 *  time - each piece spends before it lays and refunds whole on a
	 *  refusal, so a blocked or unaffordable route stops mid-way with
	 *  an honest "LAID k OF n" rather than rolling anything back the
	 *  player already saw. Dev-command lane now; the player path is
	 *  RelayTrackThroughStations. */
	bool LayTrackToPoint(const FVector& FloorPoint, float GhostYawDeg,
		FString& OutToast);

	/** AUTO-CONNECT (owner 2026-09-01: "cant we just have the track
	 *  autamaticly connect between stations?" - which is also the
	 *  benchmark model: stations are the decision, the conveyor is
	 *  just there). Plans the whole chain FIRST, pure and fail-closed
	 *  - Start ahead of the first station, an A* leg to each next
	 *  station in placement order, End cap - and only when every leg
	 *  routes does it tear the old track down, lay the new one, attach
	 *  every station to its straight and turn each to face across its
	 *  leg. Free of charge: the track is infrastructure, the stations
	 *  are the spend. With zero line stations it just clears. */
	static bool RelayTrackThroughStations(
		ALBSpacecraftBuildAuthority& InBuild,
		class ALBSpacecraftTrackAuthority& InTrack,
		class ALBSpacecraftRuntimeCoordinator* InCoordinator,
		ALBSpacecraftProductionAuthority* InLedger, FString& OutReason);

	/** The WIP presenter, for dev commands that need to read what is
	 *  actually being DRAWN rather than what the authorities hold. */
	ALBSpacecraftWIPPresentationActor* GetPresenter() const
	{
		return Presenter;
	}

	class ALBSpacecraftProgressionAuthority* GetProgression() const
	{
		return Progression;
	}

	/** The build/contracts/research panel, so a headless capture can
	 *  reach a tab. Every visual claim on this project that was
	 *  reasoned rather than SEEN has turned out wrong at least once,
	 *  and a panel that only renders after a craft is delivered cannot
	 *  be photographed without driving the game to that point first. */
	class ULBSpacecraftCommandPanelWidget* GetCommandPanel() const
	{
		return CommandPanel;
	}

	class ALBSpacecraftReputationAuthority* GetReputation() const
	{
		return Reputation;
	}

	/** All seven authorities gathered for the save pipeline. */
	FLBSpacecraftSaveContext MakeSaveContext() const;

	/** Factory time control (the Car Manufacture 1/2/3/4 row): 0 pauses
	 *  the SIMULATION (the world keeps rendering, unlike the pause
	 *  menu's hard pause); 1/2/4 scale every economy tick coherently.
	 *  Other values refuse - there are exactly four speeds. */
	bool SetSimSpeed(float NewScale, FString& OutReason);
	float GetSimSpeed() const { return SimTimeScale; }
	static bool IsKnownSimSpeed(float Scale);

	/** Localized top-bar label for the current speed. */
	FText DescribeSimSpeed() const;

	/** Player quick save/load (F5/F9): the same rollback-safe pipeline
	 *  as the console commands, with the outcome as the toast text. */
	bool QuickSave(FString& OutReason);
	bool QuickLoad(FString& OutReason);

	/** Cycles the command panel tab (Tab / Shift+Tab). */
	void CyclePanelTab(int32 Direction);

	/** Opens the settings surface above the pause menu. */
	void OpenSettingsMenu();

	/** Placement with the full Phase-2 policy: research must have opened
	 *  the family (via the build authority's gate); a PowerPlant registers
	 *  its supply; a StorageRack registers its ledger store
	 *  ("Store.<StationId>"); a powered family's draw must connect - any
	 *  wiring failure removes the station again, never leaving it
	 *  half-connected. Static so tests exercise it without a game mode. */
	static bool PlaceStationPowered(ALBSpacecraftBuildAuthority& InBuild,
		ALBSpacecraftPowerAuthority& InPower,
		ALBSpacecraftInventoryAuthority& InInventory, FName DefinitionId,
		const FTransform& Transform, FName& OutStationId,
		FString& OutReason,
		ALBSpacecraftProductionAuthority* InLedger = nullptr,
		class ALBSpacecraftProgressionAuthority* InProgression = nullptr);

	/** Installs a unit into a slot building through the same ledger +
	 *  power wiring as free placement (owner 2026-08-26: the dedicated
	 *  buildings grow by units in slots). Fail-closed with unwind. */
	static bool InstallInSlotPowered(ALBSpacecraftBuildAuthority& InBuild,
		ALBSpacecraftPowerAuthority& InPower, FName HostStationId,
		FName UnitDefinitionId, FName& OutStationId, FString& OutReason,
		ALBSpacecraftProductionAuthority* InLedger = nullptr,
		ALBSpacecraftInventoryAuthority* InInventory = nullptr);

	/** The SITE OVERFLOW YARD (owner 2026-08-27: "we can have a global
	 *  overflow?"). Deliveries land here, haulers draw from it when
	 *  their own rack is short, and machine output spills here when a
	 *  rack is full. It is what stops the local-stockpile model ever
	 *  hard-jamming: goods always have somewhere to be, while a
	 *  station still only eats what has been carried TO it. */
	static FName SiteOverflowStoreId() { return FName(TEXT("Store.Floor")); }

	/** The store a delivery should land in: the first DELIVERY DOCK on
	 *  the floor with room for the order. None when the site has no
	 *  dock, or every dock is backed up - both of which refuse the
	 *  order in plain words rather than teleporting goods in. */
	static FName FindDeliveryStore(const ALBSpacecraftBuildAuthority& InBuild,
		const ALBSpacecraftInventoryAuthority& InInventory, FName ItemId,
		int32 Count, FString& OutReason);

	/** Makes sure every station that consumes materials has its local
	 *  stockpile store. Stations reach the floor by several routes -
	 *  the player's placement, a slot install, the canonical demo line,
	 *  a loaded save - and a station without a stockpile is invisible
	 *  to the delivery drones and can never be fed. Reconciling here
	 *  means no route can forget. Idempotent. */
	static int32 SyncStationStores(const ALBSpacecraftBuildAuthority& InBuild,
		ALBSpacecraftInventoryAuthority& InInventory,
		const class ALBSpacecraftCraftingAuthority* InCrafting = nullptr);

	/** Pure: how big a stockpile has to be to hold the top-up target
	 *  of everything a station handles. Capacity is counted in UNITS
	 *  and items differ in size - a component is eight units, an ore
	 *  is one - so a station fitting five components needs a far
	 *  bigger shelf than one fitting a single part. Deriving it here
	 *  means the shelf always fits the work, instead of a flat number
	 *  that silently starves whichever station happens to outgrow it. */
	static int32 StockpileUnitsForItems(const TArray<FName>& Items,
		int32 TopUpUnits, int32 BaseUnits);

	/** Buys one drone (with its dock) into a line station's slot,
	 *  charged fail-closed (owner 2026-08-26, the worker-slot model). */
	/** The crew a station may hold before QUALITY CONTROL is earned.
	 *  Nominal is two - the point at which a station fits parts
	 *  cleanly - so a new player can always reach "no defects"; going
	 *  beyond that, for speed, is the upgrade the milestone opens. */
	static constexpr int32 NominalStationCrew() { return 2; }

	/** Dismisses the drone in a slot, refunding half its kind's price. */
	static bool DismissStationDronePowered(
		ALBSpacecraftBuildAuthority& InBuild, FName StationId,
		int32 SlotIndex, FString& OutReason,
		ALBSpacecraftProductionAuthority* InLedger = nullptr);

	/** InResearch gates the KIND (2026-09-03): specialist crew are
	 *  research content like any machine, so a kind the player has
	 *  not researched cannot be hired. Optional and defaulted, like
	 *  the progression hook beside it - a caller that passes no
	 *  research authority (dev commands, fixtures) is ungated. */
	static bool InstallStationDronePowered(
		ALBSpacecraftBuildAuthority& InBuild, FName StationId,
		FString& OutReason,
		ALBSpacecraftProductionAuthority* InLedger = nullptr,
		const class ALBSpacecraftProgressionAuthority* InProgression =
			nullptr,
		FName KindId = NAME_None,
		const class ALBSpacecraftResearchAuthority* InResearch = nullptr);

	/** Sell-back fraction refunded when a station is removed through
	 *  RemoveStationPowered with a ledger (PROVISIONAL: half). */
	static constexpr int64 RemovalRefundPercent = 50;

	/** Removal with the same policy in reverse, all fail closed: a plant
	 *  whose supply would strand live loads refuses (shed first), a rack
	 *  still holding items refuses (empty it first), a consumer's load is
	 *  disconnected with it. */
	/** The coordinator/track hooks close the save-poisoning hole
	 *  (audit 2026-09-01): removing a ROUTE station used to leave the
	 *  coordinator ticking a stale route and the next quicksave wrote
	 *  assignments against an uncommissioned layout - a shape the
	 *  loader permanently refuses. With the hooks passed, removal
	 *  fails closed while craft are on the line, and an idle route
	 *  containing the station resets instead of going stale. */
	static bool RemoveStationPowered(ALBSpacecraftBuildAuthority& InBuild,
		ALBSpacecraftPowerAuthority& InPower,
		ALBSpacecraftInventoryAuthority& InInventory,
		ALBSpacecraftCraftingAuthority* InCrafting, FName StationId,
		FString& OutReason,
		ALBSpacecraftProductionAuthority* InLedger = nullptr,
		class ALBSpacecraftRuntimeCoordinator* InCoordinator = nullptr,
		class ALBSpacecraftTrackAuthority* InTrack = nullptr);

	/** Selects a recipe for a PLACED station, class-derived from its
	 *  record and research-gated like placement. */
	static bool SelectStationRecipe(ALBSpacecraftBuildAuthority& InBuild,
		ALBSpacecraftCraftingAuthority& InCrafting,
		ALBSpacecraftResearchAuthority& InResearch, FName StationId,
		FName RecipeId, FString& OutReason);

	/** Buys raw materials with cash (fail-closed) and books the delivery
	 *  into the dev floor store. The inbound mirror of contracts. */
	static bool PlaceResourceOrder(
		ALBSpacecraftInventoryAuthority& InInventory,
		ALBSpacecraftProductionAuthority& InLedger, FName ItemId,
		int32 Count, FName StoreId, FString& OutReason);

	/** Advances every placed, recipe-selected crafting station by
	 *  DeltaSeconds against the dev floor store. Static so tests exercise
	 *  it without a live game mode. Returns completed cycle count. */
	static int32 TickCraftingStations(ALBSpacecraftBuildAuthority& InBuild,
		ALBSpacecraftCraftingAuthority& InCrafting,
		ALBSpacecraftInventoryAuthority& InInventory, double DeltaSeconds,
		const class ALBSpacecraftTransportAuthority* InTransport = nullptr,
		ALBSpacecraftGameMode* InAlertSink = nullptr);

	/** THE SIMULATION'S VOICE. Refusals raised by the running factory -
	 *  as opposed to ones raised by something the player just clicked -
	 *  had nowhere to go: the reason string was written to a local and
	 *  dropped, so a stalled machine simply stopped with no explanation.
	 *  The panel shows whatever is here. Repeats are ignored so a
	 *  per-tick refusal cannot spam the toast. */
	/** THE OFFER BOARD. Keeps a few contracts standing in the Offered
	 *  state for the player to choose between. Accepting used to be a
	 *  spawn button - two hard-coded offers, always x1, always the
	 *  catalogue price, minted and accepted in consecutive statements,
	 *  so the Offered state was unreachable and there was never a
	 *  choice to make. Called from the tick; does nothing once the
	 *  board is full. */
	void RefreshOfferBoard();
	static void RefreshOfferBoard(
		const FLBSpacecraftSaveContext& InContext);

	/** How many offers stand on the board at once (PROVISIONAL). */
	static constexpr int32 OfferBoardSize = 3;

	/** Pure: the terms of the Nth standing offer for a recipe. Bulk
	 *  orders pay slightly less per craft and small ones slightly more,
	 *  so quantity is a real trade against line throughput rather than
	 *  a free multiplier. */
	static int32 OfferQuantityForSlot(int32 Slot);

	/** Pure: how long a customer allows for an order, in sim seconds.
	 *  Built from the craft's own stage times and the quantity, with
	 *  slack for the fact that a real line is throughput-bound rather
	 *  than cycle-bound - a Scout is 440 s of cycle work but a real
	 *  factory took nearer 3,000 s a craft, so the multiplier is set
	 *  off the MEASURED figure, not the theoretical one. A well-run
	 *  factory makes it comfortably; a badly-run one does not, which is
	 *  the whole point. PROVISIONAL. */
	static double ContractAllowanceSeconds(const FLBSpacecraftRecipe& Recipe,
		int32 Quantity);
	static int64 OfferUnitPricePence(int64 BasePence, int32 Quantity,
		int32 ReputationTier);

	void RaiseSimAlert(const FString& Alert);
	/**
	 * What the LINE itself has to say this tick: the hold reason if it
	 * is stopped, else - only while nothing is on the line - why it
	 * will not start. A start refusal while craft are in flight ("no
	 * accepted contract demand", "the head station is occupied") is
	 * the queue answering, not a fault, and the stranger run through
	 * the real panel (2026-09-02) read "No accepted contract demand
	 * for this recipe" across the whole build of their one accepted
	 * ship.
	 */
	static FString LineAlertFor(const FString& HoldReason,
		const FString& StartRefusal, int32 UnitsInFlight);
	/**
	 * Raise the line's complaint, or - when the line has none this tick
	 * and the strip is still showing the line's PREVIOUS complaint -
	 * clear it. Complaints from other sources (a stalled machine) are
	 * left alone; RaiseSimAlert's rule that an empty alert never clears
	 * a real one still holds for everything else.
	 */
	void ApplyLineAlert(const FString& LineAlert);
	const FString& GetSimAlert() const { return SimAlertText; }

	/** Pure: the plainest true sentence for a machine whose output
	 *  buffer is full. With no storage rack on the floor no hauler will
	 *  ever come, so "awaiting drone pickup" is a lie - it names the
	 *  cure instead. */
	static FString BuildBufferStallAlert(FName StationId,
		bool bAnyStorageRack);

	/** Places one station of every catalogue class in a canonical row and
	 *  commissions the factory - the dev/testing shortcut through the same
	 *  build authority the player uses. */
	/** Credits every authority that reads the CONTRACT LEDGER -
	 *  reputation, delivery milestones and research points. Both the
	 *  actor tick and the LB.Spacecraft.Run console command call this,
	 *  because they used to credit different subsets and the dev
	 *  journey silently stopped being a faithful proxy for play. */
	void SyncLedgerDerivedAuthorities();
	static void SyncLedgerDerivedAuthorities(
		const FLBSpacecraftSaveContext& InContext);

private:
	/** Dev showcase only: puts a crate of assembled components on the
	 *  floor so the unattended demo can actually finish a craft. */
	bool StockShowComponents(FString& OutReason);


public:

	/** Lays a demo track and attaches every station the route uses.
	 *
	 *  SHARED BY BOTH PATHS ON PURPOSE. The autoshow laid track and the
	 *  BuildLine console command did not, so a line built from the
	 *  console had stations attached to nothing - and that does not fail
	 *  until you try to LOAD it, because restore validates the whole
	 *  snapshot and refuses a line whose stations have no nodes. A save
	 *  you cannot load is worse than no save button.
	 *
	 *  The track is sized to the route rather than to a fixed list. */
	bool LayLineTrack(FString& OutReason);

	static bool SetupCanonicalLine(ALBSpacecraftBuildAuthority& InBuild,
		FString& OutReason, bool bMk2Line = false);

	/** Builds a working PARTS FACTORY for the commissioned line: buys
	 *  the land, places power and sub-assembly halls, installs one
	 *  machine per distinct recipe of the HULL's whole fabrication
	 *  chain (planned by PlanBuild) with recipes selected and standing
	 *  orders open, places storage racks, and orders the feedstock
	 *  through the ledger - raw ore for the hull chain, the other five
	 *  components IMPORTED at the dock. The make-vs-buy split is
	 *  forced, not stylistic: fabricating all six components needs
	 *  upwards of ninety machines, which does not fit the 220 m floor
	 *  at Mk1 sizes - the import price list is what makes a buildable
	 *  yard possible at all. Construction is an uncharged dev fixture
	 *  like SetupCanonicalLine; the FEEDSTOCK stays charged, because
	 *  spend-against-income is half of what a soak must prove.
	 *  Everything goes through the normal authorities and fails closed
	 *  with the first named refusal. */
	static bool SetupEconomy(ALBSpacecraftBuildAuthority& InBuild,
		ALBSpacecraftPowerAuthority& InPower,
		ALBSpacecraftInventoryAuthority& InInventory,
		ALBSpacecraftCraftingAuthority& InCrafting,
		ALBSpacecraftResearchAuthority& InResearch,
		ALBSpacecraftProductionAuthority& InLedger,
		ALBSpacecraftProgressionAuthority* InProgression,
		int32 CraftTarget, FString& OutReason);

	/** Offers and immediately accepts a Scout-01 contract. */
	static bool StartScoutContract(
		ALBSpacecraftProductionAuthority& InProduction, int32 Quantity,
		FString& OutReason);

	/** Offers and immediately accepts a contract for any catalogue recipe,
	 *  priced at the recipe's baseline revenue. With a reputation
	 *  authority, the recipe's tier gate is enforced fail-closed. */
	static bool StartRecipeContract(
		ALBSpacecraftProductionAuthority& InProduction, FName RecipeId,
		int32 Quantity, FString& OutReason,
		class ALBSpacecraftReputationAuthority* InReputation = nullptr);

	/** Finds the spacecraft game mode of a world, if any. */
	static ALBSpacecraftGameMode* FindInWorld(UWorld* World);

private:
	UPROPERTY()
	TObjectPtr<ALBSpacecraftBuildAuthority> BuildAuthority;

	UPROPERTY()
	TObjectPtr<ALBSpacecraftProductionAuthority> ProductionAuthority;

	/** Accepted contracts whose expiry has already been announced -
	 *  each deadline lapse alerts exactly once (2026-09-01: expiry
	 *  used to be silent and the first stranger ship vanished into
	 *  stock with no trace on screen). */
	TSet<FName> ExpiredContractsAnnounced;

	UPROPERTY()
	TObjectPtr<ALBSpacecraftRuntimeCoordinator> Coordinator;

	UPROPERTY()
	TObjectPtr<ALBSpacecraftInventoryAuthority> InventoryAuthority;

	UPROPERTY()
	TObjectPtr<ALBSpacecraftCraftingAuthority> CraftingAuthority;

	UPROPERTY()
	TObjectPtr<ALBSpacecraftPowerAuthority> PowerAuthority;

	UPROPERTY()
	TObjectPtr<ALBSpacecraftResearchAuthority> ResearchAuthority;

	UPROPERTY()
	TObjectPtr<ALBSpacecraftDroneFleetAuthority> DroneFleet;

	UPROPERTY()
	TObjectPtr<class ALBSpacecraftReputationAuthority> Reputation;

	UPROPERTY()
	TObjectPtr<class ALBSpacecraftTransportAuthority> Transport;

	UPROPERTY()
	TObjectPtr<class ALBSpacecraftProgressionAuthority> Progression;

	UPROPERTY()
	TObjectPtr<class ALBSpacecraftTrackAuthority> TrackAuthority;

public:
	/** Seed the bare-bones starter spine (power plant + material
	 *  processor + storage rack) through the SAME placement path the
	 *  player uses, charged against starting capital. Runs once, only
	 *  on an empty floor. DEV ONLY now (LB.Spacecraft.SeedSpine): the
	 *  owner launched v007 and rejected the pre-seeded floor outright
	 *  (2026-08-28, "its unplayble, already stuff in map") - the game
	 *  opens EMPTY and the player builds everything. Line stations are
	 *  self-powered, so the empty start is affordable: station, crew,
	 *  track, dock and the first craft's imported components all fit
	 *  inside the starting capital. */
	bool SeedStarterSpine(FString& OutReason);

	/** ONE STEP OF THE WHOLE SIMULATION - the line, the crafting
	 *  stations, the drone fleet, the grid meter, the ledger-derived
	 *  authorities and inbound orders, in the order the actor tick runs
	 *  them.
	 *
	 *  Shared by LB.Spacecraft.Run and LB.Spacecraft.Jump so the two
	 *  cannot drift: a jump that ticked a different set of authorities
	 *  than a run would reach states a real playthrough never produces,
	 *  which is the worst possible property for a fixture that exists
	 *  to photograph the game. */
	static bool TickWholeSimStep(ALBSpacecraftGameMode& InGameMode,
		double StepSeconds, FString& OutReason, int32& OutCraftCycles);

	/** The same step over the authorities THEMSELVES, which is where the
	 *  work actually happens; the game-mode overload just gathers them
	 *  and calls this.
	 *
	 *  It takes the save context because that struct already exists to
	 *  collect exactly these authorities - and because keeping the list
	 *  in one place is the whole point. Both faults of 2026-08-29 were
	 *  a second, hand-maintained copy of this list drifting from the
	 *  first: the drone haulers and then the station-store sync ran on
	 *  the actor tick and not here, so a console-driven run starved
	 *  while a headed session was perfect. MakeSaveContext carries a
	 *  scar from the identical mistake ("these two were never set, so
	 *  the LIVE Save command failed closed while the suite's full rigs
	 *  passed").
	 *
	 *  It is also what makes the step TESTABLE. The suite could only
	 *  hand-call SyncStationStores, TickCraftingStations and TickHauls
	 *  one at a time, because the assembled step needed a live game
	 *  mode - so 130 tests proved every part worked and none proved the
	 *  clock ticked them. */
	static bool TickWholeSimStep(const FLBSpacecraftSaveContext& InContext,
		double StepSeconds, FString& OutReason, int32& OutCraftCycles);

	/** THE SHIP FACTORY'S STARTING LOADOUT (owner 2026-08-28: "in ship
	 *  factory player should start with 1 assembly station and 1 of
	 *  each drone and the test and departure and do the full build in
	 *  that station"). Runs when the player places their ship factory
	 *  hall - so the SITE still opens as bare land, and only the floor
	 *  INSIDE the hall they just paid for comes with a seed.
	 *
	 *  ONE station, not five: with a single line station the route
	 *  covers the whole fixing sequence at that one station, which is
	 *  the slowest COMPLETE version of the line. Adding stations is how
	 *  the player splits the sequence up and goes faster.
	 *
	 *  Free, like starting capital - and refused outright once any line
	 *  station exists, so it can never top a player up twice or land on
	 *  top of a loaded save. */
	static bool SeedShipFactoryLoadout(
		ALBSpacecraftBuildAuthority& InBuild,
		class ALBSpacecraftPowerAuthority& InPower,
		class ALBSpacecraftInventoryAuthority& InInventory,
		FName HallId, FString& OutReason,
		class ALBSpacecraftProgressionAuthority* InProgression = nullptr,
		ALBSpacecraftRuntimeCoordinator* InCoordinator = nullptr,
		ALBSpacecraftProductionAuthority* InProduction = nullptr,
		class ALBSpacecraftTrackAuthority* InTrack = nullptr);

	UPROPERTY(EditAnywhere, Category = "LineBoss")
	bool bSeedStarterSpine = false;

private:

	UPROPERTY()
	TObjectPtr<ALBSpacecraftWIPPresentationActor> Presenter;

	UPROPERTY()
	TObjectPtr<ULBSpacecraftTopBarWidget> TopBar;

	UPROPERTY()
	TObjectPtr<class ULBSpacecraftCommandPanelWidget> CommandPanel;

	/** The site hub, kept so a dev command can drive it headlessly.
	 *  A screen whose only input is a mouse click on a picture cannot
	 *  otherwise be tested at all. */
	UPROPERTY()
	TObjectPtr<class ULBSpacecraftSiteHubWidget> SiteHub;

public:
	class ULBSpacecraftSiteHubWidget* GetSiteHub() const
	{
		return SiteHub;
	}

private:

	UPROPERTY()
	TObjectPtr<class ULBSpacecraftPauseMenuWidget> PauseMenu;

	UPROPERTY()
	TObjectPtr<class ULBSpacecraftSettingsWidget> SettingsMenu;

	/** Factory time control: 0 (sim paused), 1, 2 or 4. */
	/** The running factory's most recent complaint (see RaiseSimAlert). */
	UPROPERTY()
	FString SimAlertText;
	/** The last complaint ApplyLineAlert raised, so it clears only its own. */
	FString LastLineAlertText;

	float SimTimeScale = 1.f;

public:
	/** Escape: show/hide the pause menu and pause/resume the sim. */
	void TogglePauseMenu();

	/** Launch cinematic: while a craft departs, the view rides the
	 *  director camera (chicane chase -> sprint crane) and returns to
	 *  the pawn at the door. Esc cancels for that departure.
	 *  DEFAULT OFF (owner, 2026-08-30: "still doing the cinematic and
	 *  cutting to the ship" - the flight itself stays, but the player's
	 *  view no longer gets hijacked away from their own camera to watch
	 *  it happen. */
	UPROPERTY(EditAnywhere, Category = "LineBoss")
	bool bLaunchCameraEnabled = false;

	bool IsLaunchCameraActive() const { return bLaunchCameraLive; }
	void CancelLaunchCamera();

private:
	UPROPERTY()
	TObjectPtr<class ACameraActor> LaunchCamera;

	bool bLaunchCameraLive = false;
	bool bLaunchCameraSuppressed = false;

	void TickLaunchCamera();

public:

private:
};
