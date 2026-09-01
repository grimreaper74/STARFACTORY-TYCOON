// Spacecraft-era factory build authority: player-placed, grid-snapped
// stations. Generalises the proven Body Shop grid model (100 cm snap,
// quarter-turn yaw, floor datum, fail-closed placement) to the spacecraft
// line, with the route DERIVED from the stage table plus what the player
// actually placed - never from a hard-coded station list.
//
// Stations are data records owned by this authority (single-owner pattern);
// presentation reconstructs from the records and never creates a second
// logical station.

#pragma once

#include "CoreMinimal.h"
#include "GameFramework/Actor.h"
#include "LBSpacecraftProductionTypes.h"
#include "LBSpacecraftBuildAuthority.generated.h"

/** Placeable station family. DefinitionId matches the stage table's
 *  StationClassId, which is the single source of truth for what the line
 *  needs. */
USTRUCT(BlueprintType)
struct LINEBOSSCARFACTORY_API FLBSpacecraftStationDefinition
{
	GENERATED_BODY()

	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "LineBoss")
	FName DefinitionId;

	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "LineBoss")
	FString DisplayName;

	/** Footprint on the grid in centimetres (X = along flow at yaw 0). */
	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "LineBoss")
	FVector2D FootprintCm = FVector2D::ZeroVector;

	/** Purchase price, integer pence (the management ledger is pence). */
	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "LineBoss")
	int64 CostPence = 0;

	/** The largest craft envelope (L, W, H cm) this station mark can
	 *  service. The Scout is the smallest craft: larger tiers need larger
	 *  station marks, and the line refuses recipes it cannot hold. */
	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "LineBoss")
	FVector MaxCraftEnvelopeCm = FVector::ZeroVector;

	/** Electrical draw registered with the power authority when this
	 *  station goes live. The slice's five route families are 0 kW (the
	 *  starter line predates the power system and stays self-powered);
	 *  every Phase-2 crafting family draws real power. */
	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "LineBoss")
	int32 PowerDrawKw = 0;

	/** The stage-table class this station SERVICES on the route. Marks of
	 *  the same class share it (MaterialProcessorMk2 services
	 *  MaterialProcessor); crafting and infrastructure families leave it
	 *  None. Commissioning and routing match on THIS, so any sufficient
	 *  mark satisfies a stage. */
	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "LineBoss")
	FName StageClassId;

	/** Superseded definitions kept ONLY so existing saves still resolve
	 *  their placed stations. Hidden from the build menu; everything
	 *  else (placement, routing, capacity) treats them normally. The
	 *  four car-shaped line families became one repeated station type
	 *  (owner 2026-08-27: "one station type like car manufacturer"). */
	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "LineBoss")
	bool bLegacyHidden = false;

	/** Generation this station adds to the power authority when placed
	 *  (PowerPlant family). Zero for everything that only consumes. */
	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "LineBoss")
	int32 PowerSupplyKw = 0;

	/** Ledger store capacity this station registers when placed
	 *  (StorageRack family). Zero for stations that hold no items. */
	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "LineBoss")
	int32 StorageCapacityUnits = 0;

	/** Which class's RECIPES this station can run. Empty means "my own
	 *  id", which is every Mk1. A bigger mark points at the mark below
	 *  it, so a Rolling mill Mk2 runs the rolling mill's recipes rather
	 *  than needing a duplicate recipe table of its own. */
	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "LineBoss")
	FName RecipeClassId;

	/** How much faster this mark works than the mark below it. 1.0 is
	 *  nominal; a bigger mark buys throughput. */
	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "LineBoss")
	float CraftSpeedMultiplier = 1.f;

	/** The recipe class in force - RecipeClassId, or this station's own
	 *  id when it has none. */
	FName GetRecipeClassId() const
	{
		return RecipeClassId.IsNone() ? DefinitionId : RecipeClassId;
	}

	/** LOCAL STOCKPILE capacity, in units, for a station that consumes
	 *  materials (owner 2026-08-27, the Production Line model): goods
	 *  sit AT the station that will use them, kept fed by delivery
	 *  drones, and a station whose stockpile runs dry says
	 *  "INSUFFICIENT RESOURCES" and waits. Deliberately small - this
	 *  is a stockpile beside a machine, not a warehouse; bulk lives in
	 *  storage racks. Zero for stations that consume nothing. */
	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "LineBoss")
	int32 InputStockpileUnits = 0;

	/** Dedicated slot buildings (owner 2026-08-26): how many hosted
	 *  units this building holds. Zero for everything else. */
	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "LineBoss")
	int32 SlotCount = 0;

	/** Drone slots on PRODUCTION-LINE stations (owner 2026-08-26, the
	 *  Car Manufacture worker-slot model): each slot takes one bought
	 *  drone with its dock; installed drones speed the station's
	 *  fitting work. Zero on non-route families. */
	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "LineBoss")
	int32 DroneSlotCount = 0;

	/** What a slot hosts: a definition id (PowerStation hosts
	 *  PowerPlant), or "AnyCraftingMachine" for the sub-assembly hall.
	 *  None on non-slot buildings. */
	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "LineBoss")
	FName SlotUnitClass;

	/** A PROCESS station: the craft PASSES THROUGH it rather than having
	 *  parts fitted at it (owner 2026-08-28: "maybe a different station
	 *  for spraying"). This is what keeps the one-repeated-station rule
	 *  intact - the rule is about FITTING stations, and a spray booth
	 *  fits nothing. A process station is never given a share of the
	 *  fixing sequence, and it takes ProcessSeconds rather than a slice
	 *  of the recipe's line work.
	 *
	 *  Paint is the one process a real factory always encloses, because
	 *  overspray ruins the parts around it - which is exactly why the
	 *  craft should not be sprayed standing on the fitting line. */
	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "LineBoss")
	bool bProcessStation = false;

	/** How long a craft dwells in a PROCESS station, in sim seconds.
	 *  A fixed time, not a share of the recipe: masking, spraying and
	 *  flashing off take what they take however many parts the craft
	 *  carries. */
	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "LineBoss")
	float ProcessSeconds = 0.f;

	/** True for the stage-table route families commissioning requires.
	 *  Crafting families (Phase-2) are optional extras: a factory
	 *  commissions without them, but they still place, gate and craft. */
	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "LineBoss")
	bool bRouteRequired = true;

	/** A SITE BUILDING: placed on the outside world map, entered by
	 *  clicking it, and the thing everything else is built INSIDE
	 *  (owner 2026-08-28: "game should start on world map and player
	 *  should be only able to pick the ship factory, place on map,
	 *  click on it to enter then build factory"). The build menu shows
	 *  site buildings on the map and interior buildings inside, so the
	 *  two catalogues never mix. */
	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "LineBoss")
	bool bSiteBuilding = false;

	/** The interior floor a site building offers, in centimetres.
	 *  Interior placement is legal only within this rectangle around
	 *  the building's own transform - which is what "build the factory
	 *  inside it" means mechanically. Zero on non-site buildings. */
	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "LineBoss")
	FVector2D InteriorFloorCm = FVector2D::ZeroVector;

	/** WHERE THE DOOR IS, relative to the building's own transform
	 *  (owner 2026-08-28: "can you place roads to where doors are?").
	 *  Roads run to this point, so a rotated building is served on the
	 *  side its door actually faces. Zero means "no door" - nothing is
	 *  served, rather than a road to the middle of a wall. */
	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "LineBoss")
	FVector2D DoorOffsetCm = FVector2D::ZeroVector;

	/** The door's world position for a placed transform: the offset
	 *  rotated by the building's yaw. Pure, so the road layer and any
	 *  future traffic agree on one answer. */
	FVector DoorWorldCm(const FTransform& PlacedTransform) const;
};

/** A KIND OF DRONE that can fill a line station's slot (owner
 *  2026-08-28). Four models already exist in the presenter - this is
 *  what turns them into a choice with consequences.
 *
 *  FittingWeight is the drone's contribution to the station's work
 *  rate relative to a general assembly drone; QualityWeight is its
 *  contribution to workmanship. A station crewed entirely with spray
 *  drones fits slowly and finishes beautifully, one crewed with
 *  winches is fast and rough - which is the decision the menu exists
 *  to offer. */
USTRUCT(BlueprintType)
struct LINEBOSSCARFACTORY_API FLBSpacecraftDroneKind
{
	GENERATED_BODY()

	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "LineBoss")
	FName KindId;

	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "LineBoss")
	FString DisplayName;

	/** What it is for, in the player's words - the menu shows it. */
	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "LineBoss")
	FString Role;

	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "LineBoss")
	int64 CostPence = 0;

	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "LineBoss")
	float FittingWeight = 1.f;

	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "LineBoss")
	float QualityWeight = 1.f;

	/** GROUND CREW (owner 2026-08-28: "we also need 3 ground drones...
	 *  for working underneath the ship"). A ground drone drives on the
	 *  floor and works UNDER the craft, where a flier cannot reach; an
	 *  aerial one hovers around it. The presenter reads this to decide
	 *  where a drone stands, and the two are not interchangeable in the
	 *  fiction even when their weights are similar. */
	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "LineBoss")
	bool bGroundCrew = false;
};

/** One placed station: a data record, not an actor. */
USTRUCT(BlueprintType)
struct LINEBOSSCARFACTORY_API FLBSpacecraftStationRecord
{
	GENERATED_BODY()

	UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category = "LineBoss", SaveGame)
	FName StationId;

	UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category = "LineBoss", SaveGame)
	FName DefinitionId;

	UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category = "LineBoss", SaveGame)
	FTransform WorldTransform = FTransform::Identity;

	/** The slot building hosting this unit (None = free-standing).
	 *  Hosted units live inside the host's footprint, removed with it. */
	UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category = "LineBoss", SaveGame)
	FName HostStationId;

	/** Bought drones on this station's slots (route stations only;
	 *  the fleet mirrors this count). Kept as the COUNT for save
	 *  compatibility and for everything that only asks "how many"; the
	 *  types below say what each one is. */
	UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category = "LineBoss", SaveGame)
	int32 InstalledDrones = 0;

	/** WHICH DRONES fill this station's slots (owner 2026-08-28: "with
	 *  drone slots instead of robots and clicking on it should bring
	 *  up a build menu like car manufacturer so you can pick what
	 *  drones you want"). One entry per installed drone, in slot
	 *  order. Appended after InstalledDrones so an older save restores
	 *  as a crew of the default type rather than failing.
	 *
	 *  Kept in step with InstalledDrones by the authority - the count
	 *  is what the fleet and the work bonus read, the types are what
	 *  the player chose and what each drone DOES. */
	UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category = "LineBoss", SaveGame)
	TArray<FName> InstalledDroneTypes;

	/** Which assembled components are FITTED at this station (the
	 *  Car Manufacture work-scope allocation; the player edits it). */
	UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category = "LineBoss", SaveGame)
	TArray<FName> AllocatedComponents;
};

/** One step of the derived production route. */
USTRUCT(BlueprintType)
struct LINEBOSSCARFACTORY_API FLBSpacecraftRouteStep
{
	GENERATED_BODY()

	UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category = "LineBoss")
	ELBSpacecraftStage Stage = ELBSpacecraftStage::MaterialIntake;

	UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category = "LineBoss")
	FName StationClassId;

	UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category = "LineBoss")
	FName StationId;

	/** The PLACED station's definition (its mark) - capacity checks use
	 *  this, never the base class, so a bigger mark counts. */
	UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category = "LineBoss")
	FName DefinitionId;

	UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category = "LineBoss")
	FTransform WorldTransform = FTransform::Identity;
};

/** Whole-layout snapshot for save/restore: validated in full before a single
 *  mutation is applied. */
USTRUCT(BlueprintType)
struct LINEBOSSCARFACTORY_API FLBSpacecraftFactoryLayoutState
{
	GENERATED_BODY()

	UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category = "LineBoss", SaveGame)
	TArray<FLBSpacecraftStationRecord> Stations;

	UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category = "LineBoss", SaveGame)
	int32 NextStationSequence = 1;

	UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category = "LineBoss", SaveGame)
	bool bCommissioned = false;
};

UCLASS()
class LINEBOSSCARFACTORY_API ALBSpacecraftBuildAuthority : public AActor
{
	GENERATED_BODY()

public:
	ALBSpacecraftBuildAuthority();

	/** Grid contract: 100 cm snap, floor datum Z = 0, quarter-turn yaw only,
	 *  unit scale. */
	static float GetPlacementGridCm() { return 100.f; }

	/** THE SITE - half-extent of the world map's buildable ground, in
	 *  centimetres. One number, shared by the land grid, the camera's
	 *  site framing and the ground dressing, so the map has a single
	 *  size rather than five copies of one.
	 *
	 *  600 m across (owner 2026-08-28: "the world map needs to be
	 *  bigger for when parts factory and power plant buildings are
	 *  unlocked"). The 220 m plot it replaced was the FACTORY FLOOR,
	 *  and the ship factory alone fills it; the site is the ground
	 *  several buildings stand on, so it has to be several times the
	 *  building. The player starts owning the middle 220 m of it and
	 *  buys outward. */
	static constexpr float SiteHalfExtentCm() { return 30000.f; }

	/** Half-extent of the buildable floor, centred on the authority. */
	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "LineBoss")
	float BuildAreaHalfExtentCm = SiteHalfExtentCm();

	/** The placeable catalogue, derived from the stage table so a new stage
	 *  class automatically becomes a required placeable. */
	static const TArray<FLBSpacecraftStationDefinition>& StationCatalogue();

	static const FLBSpacecraftStationDefinition* FindDefinition(FName DefinitionId);

	/** Grid legality of a candidate transform (snap, yaw, datum, scale). */
	static bool IsTransformGridAligned(const FTransform& Transform,
		FString& OutReason);

	/** Optional pre-placement gate (research locks, power headroom - policy
	 *  the game mode owns). When bound, a false return refuses placement
	 *  with the gate's reason. Unbound means ungated (tests, dev rigs). */
	/** The gate currently in force, so a caller can CHAIN a new rule
	 *  in front of it rather than silently replacing everything that
	 *  came before - the gates are set up in layers and losing one
	 *  would quietly unlock whatever it guarded. */
	const TFunction<bool(FName, FString&)>& GetPlacementGate() const
	{
		return PlacementGate;
	}

	void SetPlacementGate(TFunction<bool(FName, FString&)> InGate)
	{
		PlacementGate = MoveTemp(InGate);
	}

	/** Places the SHIP FACTORY at the origin - the site building whose
	 *  interior floor everything else is built on. The player's first
	 *  move on the world map; here so fixtures and tests take exactly
	 *  the same step rather than each inventing their own hall. Does
	 *  nothing (and succeeds) when a hall already stands. */
	bool PlaceStarterHall(FName& OutStationId, FString& OutReason);

	/** True when this transform may hold this definition given the site
	 *  buildings that stand: site buildings anywhere legal, everything
	 *  else only within a placed building's interior floor (owner
	 *  2026-08-28, the world-map opening). Names its refusal - "place a
	 *  ship factory first" is the tutorial for the first move. */
	bool IsInteriorPlacementLegal(FName DefinitionId,
		const FTransform& Transform, FString& OutReason) const;

	// ---- placement (all fail closed with a reason) ----
	bool PlaceStation(FName DefinitionId, const FTransform& Transform,
		FName& OutStationId, FString& OutReason);

	/** Installs a unit into a slot building: overlap is legal INSIDE
	 *  the host's footprint, the unit is bound to the host (removed
	 *  with it), and every gate fails closed - unknown host, no slots,
	 *  wrong unit class, slots full. */
	/** The building class that owns this class as its slot unit, or
	 *  None when the class is placed freely on the floor. */
	static FName FindSlotHostClassFor(FName UnitDefinitionId);

	bool InstallInSlot(FName HostStationId, FName UnitDefinitionId,
		FName& OutStationId, FString& OutReason);

	/** How many units a slot building currently hosts. */
	int32 GetHostedCount(FName HostStationId) const;

	/** The placed record for a station id, nullptr when unknown
	 *  (public: the track and coordinator read records by id). */
	const FLBSpacecraftStationRecord* FindStation(FName StationId) const;

	/** Pure placement query for ghosts and snap targets: would this
	 *  definition at this transform pass the envelope rules against
	 *  the placed stations? Same test PlaceStation runs, callable
	 *  without mutating anything - so what a ghost promises is what
	 *  the click gets (owner 2026-09-01: the snap picked a piece by
	 *  track order, and its refusal named a station the player was
	 *  not even pointing at). */
	bool IsStationEnvelopeLegal(FName DefinitionId,
		const FTransform& Transform, FString& OutReason) const;

	// ---- production-line drone slots (owner 2026-08-26) ----
	/** PROVISIONAL: one drone with its dock, bought into a slot. */
	UPROPERTY(EditAnywhere, Category = "LineBoss")
	int64 DroneUnitCostPence = 1200000;

	/** Buys one drone into a route station's next free slot. */
	/** Installs one drone of a chosen KIND into a free slot (owner
	 *  2026-08-28: the player picks what drones they want). An unknown
	 *  or unnamed kind installs the default assembly drone, so every
	 *  older caller keeps working and no fixture has to learn types. */
	bool InstallStationDrone(FName StationId, FString& OutReason,
		FName KindId = NAME_None);

	/** Removes the drone in a slot, refunding nothing here - the ledger
	 *  side is the game mode's. Fails closed on an empty slot. */
	bool RemoveStationDrone(FName StationId, int32 SlotIndex,
		FString& OutReason);

	/** Removes one installed drone (no refund here; the powered
	 *  wrapper owns money). */
	bool RemoveStationDrone(FName StationId, FString& OutReason);

	/** Toggles a component's fit allocation on a route station. */
	/** THE FIXING SPLIT (owner 2026-08-27). The recipe's fixing order is
	 *  one sequence; the player decides where one station's work ends
	 *  and the next begins by moving the splits along it. Counts are
	 *  per ROUTE STATION, in route order, and must sum to the whole
	 *  sequence - a part with no station is a part that never gets
	 *  fitted, so there is no such thing as a partial split.
	 *
	 *  This is the ONLY way to express an allocation that cannot be
	 *  wrong: slices are contiguous and in order by construction, so
	 *  "fit the navigation before the hull" is unrepresentable rather
	 *  than refused after the fact.
	 *
	 *  Storage stays FLBSpacecraftStationRecord::AllocatedComponents -
	 *  the drones, the coordinator and the save all already read it. */
	bool SetFixingSplit(FName RecipeId, const TArray<int32>& StationCounts,
		FString& OutReason);

	/** The split as it stands: the route's stations in order, and how
	 *  many sequence entries each one fits. Fails closed if the stored
	 *  allocation is not a valid split (hand-edited, or from a save
	 *  written before splits existed), naming what is wrong rather than
	 *  rounding it into something plausible. */
	bool GetFixingSplit(FName RecipeId, TArray<FName>& OutStationIds,
		TArray<int32>& OutStationCounts, FString& OutReason) const;

	/** True when this placed station FITS PARTS - a line station that is
	 *  not a process station. The spray booth is on the line and is not
	 *  one of these: nothing is bolted on inside a paint booth. */
	bool IsFittingStation(FName StationId) const;

	bool SetComponentAllocated(FName StationId, FName ComponentItemId,
		bool bAllocated, FString& OutReason);

	/** Pure: fitting-speed bonus for an installed-drone count -
	 *  0 drones crawl at half speed, 2 are nominal, 8 fly at 2.5x. */
	static float ComputeDroneWorkBonus(int32 InstalledDrones)
	{
		return FMath::Clamp(0.5f + 0.25f * InstalledDrones, 0.5f, 2.5f);
	}

	/** THE DRONE TYPES a line station's slots accept, in menu order.
	 *  Four models exist and all four are already drawn by the
	 *  presenter; this is what makes them a CHOICE rather than a
	 *  paint job. */
	static const TArray<FLBSpacecraftDroneKind>& DroneKinds();

	/** The kind, or nullptr when the id is not one. */
	static const FLBSpacecraftDroneKind* FindDroneKind(FName KindId);

	/** The station's crew multiplier, TYPE-AWARE: each drone
	 *  contributes its own kind's fitting weight instead of every
	 *  drone counting the same. An empty type list (an old save, or a
	 *  crew installed before types existed) falls back to the plain
	 *  count, so nothing loses its crew. */
	static float ComputeTypedDroneWorkBonus(
		const FLBSpacecraftStationRecord& Record);

	/** The crew's average QUALITY weight - what decides whether this
	 *  station's own inspection finds anything. 1.0 (nominal) for an
	 *  empty or untyped crew, so nothing changes behaviour by
	 *  accident. */
	static float ComputeTypedCrewQuality(
		const FLBSpacecraftStationRecord& Record);

	/** The station's current work bonus (1.0 for unknown stations -
	 *  the route never stalls on a lookup miss). */
	float GetStationWorkBonus(FName StationId) const;
	bool MoveStation(FName StationId, const FTransform& NewTransform,
		FString& OutReason);
	bool RemoveStation(FName StationId, FString& OutReason);

	/** Commission the factory: refuses unless every station class the stage
	 *  table requires has at least one placed station. */
	bool CommissionFactory(FString& OutReason);
	bool IsCommissioned() const { return Layout.bCommissioned; }

	/** Derive the serial production route from the stage table and the
	 *  placed stations. Length always equals the table's station stage
	 *  count; fails closed when a required class is missing. */
	bool BuildRoute(TArray<FLBSpacecraftRouteStep>& OutRoute,
		FString& OutReason) const;

	/** Can every station on the route physically hold this recipe's craft?
	 *  Fails closed naming the first station that cannot. */
	static bool RouteCanServiceRecipe(
		const TArray<FLBSpacecraftRouteStep>& InRoute,
		const FLBSpacecraftRecipe& Recipe, FString& OutReason);

	// ---- save/restore: validate the whole snapshot before any mutation ----
	FLBSpacecraftFactoryLayoutState CaptureState() const { return Layout; }
	bool ValidateState(const FLBSpacecraftFactoryLayoutState& State,
		FString& OutReason) const;
	bool RestoreState(const FLBSpacecraftFactoryLayoutState& State,
		FString& OutReason);

	const TArray<FLBSpacecraftStationRecord>& GetStations() const
	{
		return Layout.Stations;
	}

private:
	UPROPERTY(VisibleAnywhere, Category = "LineBoss")
	FLBSpacecraftFactoryLayoutState Layout;

	TFunction<bool(FName, FString&)> PlacementGate;



	/** Overlap/bounds test for a candidate envelope, ignoring one station
	 *  (for moves). */
	bool EnvelopeIsLegal(FName DefinitionId, const FTransform& Transform,
		FName IgnoreStationId, const TArray<FLBSpacecraftStationRecord>& Against,
		FString& OutReason) const;
};
