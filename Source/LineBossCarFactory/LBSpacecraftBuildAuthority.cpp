#include "LBSpacecraftBuildAuthority.h"

#include "LBSpacecraftInventoryAuthority.h"

#include "LBSpacecraftCraftingAuthority.h"
#include "LBSpacecraftProductionTypes.h"

namespace LBSpacecraftBuildAuthorityPrivate
{
	// Unity-build safety: helpers qualified by subject.
	constexpr float SpacecraftGridToleranceCm = 0.1f;
	constexpr float SpacecraftYawToleranceDeg = 0.1f;

	bool SpacecraftValueOnGrid(float ValueCm, float GridCm)
	{
		const float Remainder = FMath::Fmod(FMath::Abs(ValueCm), GridCm);
		return Remainder < SpacecraftGridToleranceCm
			|| GridCm - Remainder < SpacecraftGridToleranceCm;
	}

	/** World-space half extents of a footprint under quarter-turn yaw. */
	FVector2D SpacecraftWorldHalfExtents(const FVector2D& FootprintCm,
		const FTransform& Transform)
	{
		const float Yaw = FMath::Fmod(
			FMath::Abs(Transform.Rotator().Yaw) + 360.f, 180.f);
		const bool bSwapped = FMath::Abs(Yaw - 90.f) < 1.f;
		return bSwapped
			? FVector2D(FootprintCm.Y * 0.5f, FootprintCm.X * 0.5f)
			: FVector2D(FootprintCm.X * 0.5f, FootprintCm.Y * 0.5f);
	}
}

ALBSpacecraftBuildAuthority::ALBSpacecraftBuildAuthority()
{
	PrimaryActorTick.bCanEverTick = false;
}

const TArray<FLBSpacecraftStationDefinition>&
ALBSpacecraftBuildAuthority::StationCatalogue()
{
	static const TArray<FLBSpacecraftStationDefinition> Catalogue = []()
	{
		// Footprints in centimetres, sized around the 14 m Scout-01 and the
		// 18 m test bay's placement contract.
		// These are the MARK 1 stations, sized for the SMALLEST craft in the
		// ladder (the 14.0 x 7.5 x 3.9 m Scout) with modest headroom. Bigger
		// craft tiers ship larger marks with larger capacity envelopes; the
		// route refuses any recipe its stations cannot hold.
		struct FLBSpacecraftStationSize
		{
			const TCHAR* Id;
			const TCHAR* Display;
			FVector2D Footprint;
			int64 CostPence;
			FVector MaxCraft;
		};
		// ONE STATION TYPE serves the line (owner 2026-08-27: "one
		// station type like car manufacturer... but with our drones
		// instead of robots"). AssemblyRobot is that type, renamed for
		// the player; the other three ids are LEGACY - kept so existing
		// saves still resolve their placed stations, hidden from the
		// build menu, and identical in behaviour. Every one carries the
		// single LineStation stage class: the route is however many
		// line stations the player placed, in line order, and the craft
		// has its parts FITTED at each one. Nothing on the line makes
		// anything.
		const FLBSpacecraftStationSize Sizes[] = {
			{ TEXT("AssemblyRobot"), TEXT("Assembly station Mk1"),
			  FVector2D(1800.f, 1400.f), 12000000,
			  FVector(1600.f, 900.f, 500.f) },
			// Legacy ids (pre-2026-08-27 saves). Same envelope as the
			// one true station so a restored line behaves uniformly.
			{ TEXT("MaterialProcessor"), TEXT("Material processor Mk1"),
			  FVector2D(1200.f, 800.f), 4500000,
			  FVector(1600.f, 900.f, 500.f) },
			{ TEXT("HullFabricator"), TEXT("Hull fabricator Mk1"),
			  FVector2D(1600.f, 1200.f), 9500000,
			  FVector(1600.f, 900.f, 500.f) },
			{ TEXT("ComponentFabricator"), TEXT("Component fabricator Mk1"),
			  FVector2D(1400.f, 1000.f), 8000000,
			  FVector(1600.f, 900.f, 500.f) },
		};

		TArray<FLBSpacecraftStationDefinition> Out;
		for (const FLBSpacecraftStationSize& Size : Sizes)
		{
			FLBSpacecraftStationDefinition Definition;
			Definition.DefinitionId = FName(Size.Id);
			Definition.DisplayName = Size.Display;
			Definition.FootprintCm = Size.Footprint;
			Definition.CostPence = Size.CostPence;
			Definition.MaxCraftEnvelopeCm = Size.MaxCraft;
			Definition.StageClassId = FName(TEXT("LineStation"));
			Definition.bLegacyHidden =
				Definition.DefinitionId != FName(TEXT("AssemblyRobot"));
			// Owner 2026-08-26: every line station carries eight drone
			// slots (the worker-slot model).
			Definition.DroneSlotCount = 8;
			// The BASE stockpile beside the line, kept fed by delivery
			// drones (Production Line model); SyncStationStores derives
			// the real size from the parts the station actually fits.
			Definition.InputStockpileUnits = 48;
			Out.Add(Definition);
		}

		// THE SPRAY BOOTH (owner 2026-08-28: "maybe a different station
		// for spraying" - required, and in the starting loadout).
		//
		// It is a LINE station but not a FITTING one: the craft passes
		// through, gets the customer's livery, and comes out. Nothing
		// is bolted on here. That distinction is what lets the booth
		// exist without reopening the one-repeated-station rule, which
		// is about stations that fit parts.
		//
		// Bigger than a fitting station on purpose: a booth has to
		// ENCLOSE the craft, not stand beside it, and the Scout is the
		// smallest craft there will ever be - the envelope is sized for
		// the Cargo-01 at 1.5x so the first booth does not become
		// useless at the second tier.
		{
			FLBSpacecraftStationDefinition Booth;
			Booth.DefinitionId = FName(TEXT("SprayBooth"));
			Booth.DisplayName = TEXT("Spray booth");
			Booth.FootprintCm = FVector2D(2600.f, 1800.f);
			Booth.CostPence = 9500000; // 95,000 cr
			Booth.MaxCraftEnvelopeCm = FVector(2200.f, 1250.f, 700.f);
			Booth.StageClassId = FName(TEXT("LineStation"));
			Booth.bProcessStation = true;
			// Masking, two coats and a flash-off. Long enough to be a
			// real step in the line's rhythm, short enough that one
			// booth does not throttle a line the player has widened.
			Booth.ProcessSeconds = 45.f;
			// Spray drones work here (they already exist as a hire
			// kind, and this is the place they were always for).
			Booth.DroneSlotCount = 4;
			// SELF-POWERED, like every other route station. Extraction
			// fans, heaters and booth lighting are exactly the kind of
			// load that should draw from the grid - but route stations
			// are all 0 kW by a standing decision, and making the booth
			// the sole exception would put a generator between the
			// player and their first craft. It is a one-line change on
			// the day route stations take grid power.
			Booth.PowerDrawKw = 0;
			Out.Add(Booth);
		}

		// MARK 2 route stations (research-gated): sized so the CARGO-01
		// envelope (21.0 x 11.2 x 5.8 m = 1.5x Scout, owner-approved
		// 2026-08-25) fits with headroom. Like all route marks they
		// stay self-powered (0 kW) until the owner decides route stations
		// should draw grid power.
		struct FLBSpacecraftMk2Mark
		{
			const TCHAR* Id;
			const TCHAR* StageClass;
			const TCHAR* Display;
			FVector2D Footprint;
			int64 CostPence;
			FVector MaxCraft;
		};
		// HALVED (owner-agreed tuning, 2026-08-27). These four together
		// used to cost 850,000 cr - roughly 25 to 30 Scout deliveries
		// before a player saw the second tier at all, which is a long
		// time to grind toward a thing you have already researched.
		// They now total 425,000 cr. Nothing else about the upgrade
		// changed: the research gate, the sizes and the speed
		// multiplier all stand. PROVISIONAL like every other number
		// here - the four literals below are the whole knob.
		const FLBSpacecraftMk2Mark Mk2Marks[] = {
			{ TEXT("AssemblyRobotMk2"), TEXT("LineStation"),
			  TEXT("Assembly station Mk2"), FVector2D(2700.f, 2100.f),
			  15000000, FVector(2400.f, 1400.f, 700.f) },
			// Legacy Mk2 ids (pre-2026-08-27 saves), menu-hidden.
			{ TEXT("MaterialProcessorMk2"), TEXT("LineStation"),
			  TEXT("Material processor Mk2"), FVector2D(1800.f, 1200.f),
			  5500000, FVector(2400.f, 1400.f, 700.f) },
			{ TEXT("HullFabricatorMk2"), TEXT("LineStation"),
			  TEXT("Hull fabricator Mk2"), FVector2D(2400.f, 1800.f),
			  12000000, FVector(2400.f, 1400.f, 700.f) },
			{ TEXT("ComponentFabricatorMk2"), TEXT("LineStation"),
			  TEXT("Component fabricator Mk2"), FVector2D(2100.f, 1500.f),
			  10000000, FVector(2400.f, 1400.f, 700.f) },
		};
		for (const FLBSpacecraftMk2Mark& Mark : Mk2Marks)
		{
			FLBSpacecraftStationDefinition Definition;
			Definition.DefinitionId = FName(Mark.Id);
			Definition.DisplayName = Mark.Display;
			Definition.FootprintCm = Mark.Footprint;
			Definition.CostPence = Mark.CostPence;
			Definition.MaxCraftEnvelopeCm = Mark.MaxCraft;
			Definition.StageClassId = FName(Mark.StageClass);
			Definition.bLegacyHidden =
				Definition.DefinitionId != FName(TEXT("AssemblyRobotMk2"));
			Definition.DroneSlotCount = 8;
			// A bigger mark starts from a bigger shelf.
			Definition.InputStockpileUnits = 80;
			Out.Add(Definition);
		}

		// Phase-2 crafting families (2026-08-24): parts stations serving the
		// recipe catalogue, NOT the craft route - commissioning never needs
		// them (bRouteRequired=false) and the craft-capacity law does not
		// apply (they hold parts, never a craft, so the envelope is zero).
		// Each draws real power; research gates their placement via the
		// game mode's placement gate.
		struct FLBSpacecraftCraftingFamily
		{
			const TCHAR* Id;
			const TCHAR* Display;
			FVector2D Footprint;
			int64 CostPence;
			int32 PowerDrawKw;
		};
		const FLBSpacecraftCraftingFamily CraftingFamilies[] = {
			{ TEXT("RollingMill"), TEXT("Rolling mill Mk1"),
			  FVector2D(1400.f, 900.f), 6000000, 400 },
			{ TEXT("CircuitFab"), TEXT("Circuit fab Mk1"),
			  FVector2D(1000.f, 800.f), 7000000, 250 },
			{ TEXT("ElectronicsStation"), TEXT("Electronics station Mk1"),
			  FVector2D(1200.f, 900.f), 7500000, 300 },
			{ TEXT("PowerCellPlant"), TEXT("Power cell plant Mk1"),
			  FVector2D(1200.f, 1000.f), 8000000, 350 },
			{ TEXT("PropulsionStation"), TEXT("Propulsion station Mk1"),
			  FVector2D(1600.f, 1100.f), 9000000, 500 },
			// NO ROBOTS - DRONES FIT EVERYTHING (owner, restated
			// 2026-08-29). This was "Sub-assembly robot Mk1" in the
			// player's face while every other machine here is a fab,
			// plant, station or mill. The identifier SubAssemblyRobot
			// survives only because placed stations record it in the
			// save and renaming it without a redirect would orphan
			// them; it is never shown. The robot-arm MESH it points
			// at is a separate and still-open problem.
			{ TEXT("SubAssemblyRobot"), TEXT("Sub-assembly fab Mk1"),
			  FVector2D(1800.f, 1300.f), 11000000, 600 },
			// Owner 2026-08-27: "anything that makes parts is sub
			// assembly which goes in a different building", and "the
			// car gets parts fitted at each station and doesn't make
			// parts". These three exist to take the fabrication that
			// was standing ON THE LINE: 34 part recipes had landed on
			// the hull and component fabricators, and 11 stock recipes
			// on the material processor, because those stations were
			// NAMED for fabrication even though the craft routes
			// through them.
			{ TEXT("Smelter"), TEXT("Smelter Mk1"),
			  FVector2D(1400.f, 1000.f), 5500000, 450 },
			{ TEXT("StructureFab"), TEXT("Structure fab Mk1"),
			  FVector2D(1800.f, 1400.f), 10500000, 550 },
			{ TEXT("FitOutFab"), TEXT("Fit-out fab Mk1"),
			  FVector2D(1400.f, 1100.f), 8500000, 350 },
		};
		for (const FLBSpacecraftCraftingFamily& Family : CraftingFamilies)
		{
			FLBSpacecraftStationDefinition Definition;
			Definition.DefinitionId = FName(Family.Id);
			Definition.DisplayName = Family.Display;
			Definition.FootprintCm = Family.Footprint;
			Definition.CostPence = Family.CostPence;
			Definition.MaxCraftEnvelopeCm = FVector::ZeroVector;
			Definition.PowerDrawKw = Family.PowerDrawKw;
			// Parts machines hold their own feedstock too - the
			// drones bring raw and processed goods to the machine
			// rather than the machine reaching into a global pool.
			// Recipe inputs are small, cheap items, so this base goes
			// a long way further than the line's component shelves.
			Definition.InputStockpileUnits = 40;
			Definition.bRouteRequired = false;
			Out.Add(Definition);
		}

		// PARTS MACHINE Mk2 MARKS (owner 2026-08-27): the same upgrade
		// path the line stations have, for the six crafting families.
		// A bigger mark runs the SAME RECIPES faster and holds more,
		// so it points at the mark below it rather than duplicating
		// the recipe table. Research-gated at the end of the tree -
		// this is what a mature factory spends its points on.
		for (const FLBSpacecraftCraftingFamily& Family : CraftingFamilies)
		{
			FLBSpacecraftStationDefinition Mk2;
			Mk2.DefinitionId = FName(*FString::Printf(TEXT("%sMk2"),
				Family.Id));
			Mk2.DisplayName = FString(Family.Display).Replace(
				TEXT("Mk1"), TEXT("Mk2"));
			// Bigger floor, dearer, and it draws more for the speed.
			Mk2.FootprintCm = FVector2D(Family.Footprint.X * 1.4f,
				Family.Footprint.Y * 1.4f);
			Mk2.CostPence = Family.CostPence * 5 / 2;
			Mk2.PowerDrawKw = Family.PowerDrawKw * 3 / 2;
			Mk2.MaxCraftEnvelopeCm = FVector::ZeroVector;
			Mk2.RecipeClassId = FName(Family.Id);
			Mk2.CraftSpeedMultiplier = 1.6f;
			Mk2.InputStockpileUnits = 80;
			Mk2.bRouteRequired = false;
			Out.Add(Mk2);
		}

		// Infrastructure (no recipes, no research): the buildings that make
		// the crafting families possible. A PowerPlant SUPPLIES the grid; a
		// StorageRack registers a ledger store. Both are placement-wired by
		// the game mode (PlaceStationPowered / RemoveStationPowered).
		{
			FLBSpacecraftStationDefinition PowerPlant;
			PowerPlant.DefinitionId = FName(TEXT("PowerPlant"));
			PowerPlant.DisplayName = TEXT("Power plant Mk1");
			PowerPlant.FootprintCm = FVector2D(1600.f, 1600.f);
			PowerPlant.CostPence = 15000000;
			PowerPlant.MaxCraftEnvelopeCm = FVector::ZeroVector;
			PowerPlant.PowerSupplyKw = 1500;
			PowerPlant.bRouteRequired = false;
			Out.Add(PowerPlant);

			// Dedicated slot buildings (owner 2026-08-26): capacity
			// grows by installing units INTO the building, not by
			// scattering standalones. Both are gated on owning the
			// first unit of their kind (the game mode's placement
			// gate names it).
			FLBSpacecraftStationDefinition PowerStation;
			PowerStation.DefinitionId = FName(TEXT("PowerStation"));
			// A WORLD-MAP BUILDING at the site scale (owner 2026-08-28:
			// "should be same scale and let user place"). Generators
			// install into its slots once the player has entered it.
			PowerStation.DisplayName = TEXT("Power plant");
			PowerStation.FootprintCm = FVector2D(12000.f, 12000.f);
			PowerStation.CostPence = 20000000;
			PowerStation.bSiteBuilding = true;
			PowerStation.DoorOffsetCm = FVector2D(-6000.f, 0.f);
			// Slots sized to the BUILDING (owner 2026-08-28, one site
			// scale): a 120 m power plant holding four generators was
			// the old 24 m shed's number kept by accident.
			PowerStation.SlotCount = 8;
			PowerStation.SlotUnitClass = FName(TEXT("PowerPlant"));
			PowerStation.bRouteRequired = false;
			// STAGE 2 (owner 2026-08-28): the power station and the
			// parts factory become their own buildings on the world
			// map, unlocked after the ship factory - "should only be
			// able to build the ship building hall for now until parts
			// factory and power plant is unlocked". Both are already
			// gated, so the world map offers only the ship factory
			// today; promoting them to site buildings needs a site
			// LAYOUT (where each stands, how much land each takes) and
			// that is the owner's to see rather than mine to invent.
			Out.Add(PowerStation);

			FLBSpacecraftStationDefinition SubAssemblyHall;
			SubAssemblyHall.DefinitionId =
				FName(TEXT("SubAssemblyHall"));
			// THE PARTS FACTORY - the owner's own name for it
			// (2026-08-27: "basically they build a ship factory and a
			// parts factory"), a world-map building at the site scale.
			SubAssemblyHall.DisplayName = TEXT("Parts factory");
			SubAssemblyHall.FootprintCm = FVector2D(12000.f, 12000.f);
			SubAssemblyHall.CostPence = 18000000;
			SubAssemblyHall.bSiteBuilding = true;
			SubAssemblyHall.DoorOffsetCm = FVector2D(-6000.f, 0.f);
			// A 120 m parts factory holds a real machine floor - twelve
			// cells - rather than the four the old 30 m hall held.
			SubAssemblyHall.SlotCount = 12;
			SubAssemblyHall.SlotUnitClass =
				FName(TEXT("AnyCraftingMachine"));
			SubAssemblyHall.bRouteRequired = false;
			// The parts factory - interior for now, a world-map
			// building in stage 2 (see the note on PowerStation).
			// Gated on the ON-SITE FABRICATION delivery milestone.
			Out.Add(SubAssemblyHall);

			// THE DELIVERY DOCK (owner 2026-08-27): ordered materials
			// used to appear in a virtual store on a timer - bought
			// goods teleported onto the floor. They land HERE now, and
			// the haulers carry them on to storage and to the stations
			// that need them. Its hold is deliberately modest: a dock
			// that nobody clears backs up and refuses new deliveries,
			// which is the pressure that makes storage and haulers
			// worth buying.
			FLBSpacecraftStationDefinition DeliveryDock;
			DeliveryDock.DefinitionId = FName(TEXT("DeliveryDock"));
			DeliveryDock.DisplayName = TEXT("Delivery dock");
			DeliveryDock.FootprintCm = FVector2D(1800.f, 1200.f);
			DeliveryDock.CostPence = 3500000;
			DeliveryDock.MaxCraftEnvelopeCm = FVector::ZeroVector;
			DeliveryDock.StorageCapacityUnits = 400;
			DeliveryDock.bRouteRequired = false;
			Out.Add(DeliveryDock);

			FLBSpacecraftStationDefinition StorageRack;
			StorageRack.DefinitionId = FName(TEXT("StorageRack"));
			StorageRack.DisplayName = TEXT("Storage rack Mk1");
			StorageRack.FootprintCm = FVector2D(1000.f, 600.f);
			StorageRack.CostPence = 2000000;
			StorageRack.MaxCraftEnvelopeCm = FVector::ZeroVector;
			StorageRack.StorageCapacityUnits = 2000;
			StorageRack.bRouteRequired = false;
			Out.Add(StorageRack);

			// THE SHIP FACTORY HALL - the world map's first and only
			// offering (owner 2026-08-28). The player places this on
			// the outside map, clicks it to enter, and builds the line
			// inside it. Its interior floor is the plot the interior
			// catalogue may be placed on, sized to hold a long line
			// with room for halls and racks beside it.
			FLBSpacecraftStationDefinition ShipFactory;
			ShipFactory.DefinitionId = FName(TEXT("ShipFactoryHall"));
			ShipFactory.DisplayName = TEXT("Ship factory");
			ShipFactory.DoorOffsetCm = FVector2D(-9000.f, 0.f);
			// ONE SITE SCALE (owner 2026-08-28): the ship factory, the
			// parts factory and the power plant are the same size on
			// the map, so the site reads as a place rather than one
			// giant shed with sheds beside it. Its interior floor is
			// the line's ground.
			// The ship factory is the big hall of the three - it holds
			// the whole production line - but it is the SAME KIND of
			// building at the same architectural scale as the parts
			// factory and power plant beside it (owner 2026-08-28),
			// not a shed the size of the site.
			ShipFactory.FootprintCm = FVector2D(18000.f, 18000.f);
			// SIZED TO WHAT STANDS IN IT. At 180 m square the whole
			// starting line covered 3.9% of the floor, which is why the
			// hall has always read bare. Long down the line axis so
			// adding stations - the game's central decision - still has
			// room, and narrower across so the floor reads full.
			// SIZED FROM A LAYOUT BUDGET, not by eye
			// (Docs/HALL_LAYOUT_BUDGET_v001.md). The two axes are not
			// the same problem:
			//
			// Y STAYS 18000 because it is what lets the LINE GROW. The
			// line lays from Y=-2400 stepping 2200 per Mk2 station, so
			// 18000 holds about six of them before the booth runs off
			// the floor - and how many stations to build is the central
			// decision of this game. An earlier attempt at 14000 failed
			// because the half-extent is 7000 and the BOOTH ALONE needs
			// 7300: short by 300 cm, of the last thing on the line.
			//
			// X STAYS 18000 because the hall holds PARALLEL LINES, not
			// one. The Mk2 integration fixture lays a second line at
			// X=6000, and a Mk2 station is 2700 wide, so that alone
			// needs 7350 of half-extent. 12000 was tried and refused
			// every Mk2 station with "MUST STAND INSIDE A BUILDING".
			//
			// So the hall is the right size on BOTH axes: Y for the
			// line to grow along, X for more than one line to stand
			// side by side. It reads empty because the early game puts
			// ONE Mk1 station in a hall built for several Mk2 lines -
			// which is a progression problem, and the answer is to fill
			// it or to start the player somewhere smaller, never to cap
			// what the factory can become.
			ShipFactory.InteriorFloorCm = FVector2D(18000.f, 18000.f);
			ShipFactory.CostPence = 25000000;
			// ZERO, and it must stay zero. MaxCraftEnvelopeCm means "a
			// craft STOPS HERE" - it is the route-station capacity, and
			// there is a catalogue law, tested, that every non-route
			// class declares exactly zero. The hall is not a route
			// station: the craft does not stop AT it, the hall CONTAINS
			// the line.
			//
			// Setting it here was an attempt to let the building state
			// the biggest craft it can house, and it broke that law
			// immediately. That idea is still right - post-EA craft
			// should be admitted by building a bigger hall - but it
			// needs its OWN field with its own meaning, not an overload
			// of one that already means something else.
			ShipFactory.MaxCraftEnvelopeCm = FVector::ZeroVector;
			ShipFactory.bRouteRequired = false;
			ShipFactory.bSiteBuilding = true;
			Out.Add(ShipFactory);
		}
		return Out;
	}();
	return Catalogue;
}

const FLBSpacecraftStationDefinition* ALBSpacecraftBuildAuthority::FindDefinition(
	FName DefinitionId)
{
	for (const FLBSpacecraftStationDefinition& Definition : StationCatalogue())
	{
		if (Definition.DefinitionId == DefinitionId)
		{
			return &Definition;
		}
	}
	return nullptr;
}

bool ALBSpacecraftBuildAuthority::IsTransformGridAligned(
	const FTransform& Transform, FString& OutReason)
{
	using namespace LBSpacecraftBuildAuthorityPrivate;
	const FVector Location = Transform.GetLocation();
	if (!SpacecraftValueOnGrid(Location.X, GetPlacementGridCm())
		|| !SpacecraftValueOnGrid(Location.Y, GetPlacementGridCm()))
	{
		OutReason = TEXT("SPACECRAFT STATIONS MUST SNAP TO THE 100 CM GRID");
		return false;
	}
	if (FMath::Abs(Location.Z) > SpacecraftGridToleranceCm)
	{
		OutReason = TEXT("SPACECRAFT STATIONS SIT ON THE FLOOR DATUM Z=0");
		return false;
	}
	const FRotator Rotation = Transform.Rotator();
	if (FMath::Abs(Rotation.Pitch) > SpacecraftYawToleranceDeg
		|| FMath::Abs(Rotation.Roll) > SpacecraftYawToleranceDeg)
	{
		OutReason = TEXT("SPACECRAFT STATIONS MUST NOT PITCH OR ROLL");
		return false;
	}
	const float Yaw = FMath::Fmod(FMath::Abs(Rotation.Yaw) + 360.f, 90.f);
	if (Yaw > SpacecraftYawToleranceDeg
		&& 90.f - Yaw > SpacecraftYawToleranceDeg)
	{
		OutReason = TEXT("SPACECRAFT STATIONS ROTATE IN 90 DEGREE STEPS ONLY");
		return false;
	}
	if (!Transform.GetScale3D().Equals(FVector::OneVector, 0.001f))
	{
		OutReason = TEXT("SPACECRAFT STATIONS USE UNIT SCALE");
		return false;
	}
	OutReason.Reset();
	return true;
}

bool ALBSpacecraftBuildAuthority::EnvelopeIsLegal(FName DefinitionId,
	const FTransform& Transform, FName IgnoreStationId,
	const TArray<FLBSpacecraftStationRecord>& Against, FString& OutReason) const
{
	using namespace LBSpacecraftBuildAuthorityPrivate;
	const FLBSpacecraftStationDefinition* Definition = FindDefinition(DefinitionId);
	if (Definition == nullptr)
	{
		OutReason = FString::Printf(TEXT("UNKNOWN STATION DEFINITION %s"),
			*DefinitionId.ToString());
		return false;
	}
	const FVector2D Half = SpacecraftWorldHalfExtents(
		Definition->FootprintCm, Transform);
	const FVector Location = Transform.GetLocation();

	if (FMath::Abs(Location.X) + Half.X > BuildAreaHalfExtentCm
		|| FMath::Abs(Location.Y) + Half.Y > BuildAreaHalfExtentCm)
	{
		OutReason = TEXT("STATION ENVELOPE LEAVES THE BUILDABLE FLOOR");
		return false;
	}

	for (const FLBSpacecraftStationRecord& Other : Against)
	{
		if (Other.StationId == IgnoreStationId)
		{
			continue;
		}
		const FLBSpacecraftStationDefinition* OtherDefinition =
			FindDefinition(Other.DefinitionId);
		if (OtherDefinition == nullptr)
		{
			OutReason = FString::Printf(
				TEXT("PLACED STATION %s HAS AN UNKNOWN DEFINITION"),
				*Other.StationId.ToString());
			return false;
		}
		// A BUILDING NEVER CLASHES WITH ITS OWN CONTENTS. The ship
		// factory's footprint IS the floor its line stands on, so the
		// overlap test only compares like with like: site buildings
		// against site buildings (two halls may not share ground), and
		// interior buildings against interior buildings (two machines
		// may not share a spot). Without this the hall's envelope
		// refuses every station the player enters it to build.
		if (Definition->bSiteBuilding != OtherDefinition->bSiteBuilding)
		{
			continue;
		}
		const FVector2D OtherHalf = SpacecraftWorldHalfExtents(
			OtherDefinition->FootprintCm, Other.WorldTransform);
		const FVector OtherLocation = Other.WorldTransform.GetLocation();
		// Strict inequality: stations may touch edge to edge, never overlap.
		if (FMath::Abs(Location.X - OtherLocation.X) < Half.X + OtherHalf.X
			&& FMath::Abs(Location.Y - OtherLocation.Y) < Half.Y + OtherHalf.Y)
		{
			OutReason = FString::Printf(TEXT("ENVELOPE OVERLAPS STATION %s"),
				*Other.StationId.ToString());
			return false;
		}
	}
	OutReason.Reset();
	return true;
}

bool ALBSpacecraftBuildAuthority::IsStationEnvelopeLegal(
	FName DefinitionId, const FTransform& Transform,
	FString& OutReason) const
{
	return EnvelopeIsLegal(DefinitionId, Transform, NAME_None,
		GetStations(), OutReason);
}

FName ALBSpacecraftBuildAuthority::FindSlotHostClassFor(
	FName UnitDefinitionId)
{
	// Which building (if any) must house this class? Two ways to
	// match: a building that names the class outright (the power
	// station names PowerPlant), or one that takes ANY crafting
	// machine - the sub-assembly hall (owner 2026-08-26: "the parts
	// one should be in its own building").
	//
	// A LINE station is never housed even though it owns recipes: it
	// stands on the route, and its StageClassId says so. That single
	// test is what keeps the line outdoors and the parts machines in.
	const FLBSpacecraftStationDefinition* Unit =
		FindDefinition(UnitDefinitionId);
	if (Unit == nullptr || !Unit->StageClassId.IsNone())
	{
		return NAME_None;
	}
	const FLBSpacecraftStationDefinition* UnitForRecipes =
		FindDefinition(UnitDefinitionId);
	const bool bCraftingMachine = UnitForRecipes != nullptr
		&& FLBSpacecraftRecipeCatalogue::GetRecipesForStationClass(
			UnitForRecipes->GetRecipeClassId()).Num() > 0;
	for (const FLBSpacecraftStationDefinition& Candidate :
		StationCatalogue())
	{
		if (Candidate.SlotCount <= 0)
		{
			continue;
		}
		if (Candidate.SlotUnitClass == UnitDefinitionId)
		{
			return Candidate.DefinitionId;
		}
		if (bCraftingMachine && Candidate.SlotUnitClass
			== FName(TEXT("AnyCraftingMachine")))
		{
			return Candidate.DefinitionId;
		}
	}
	return NAME_None;
}

FVector FLBSpacecraftStationDefinition::DoorWorldCm(
	const FTransform& PlacedTransform) const
{
	if (DoorOffsetCm.IsNearlyZero())
	{
		return PlacedTransform.GetLocation();
	}
	const FVector Local(DoorOffsetCm.X, DoorOffsetCm.Y, 0.f);
	return PlacedTransform.GetLocation()
		+ PlacedTransform.GetRotation().RotateVector(Local);
}

const TArray<FLBSpacecraftDroneKind>&
ALBSpacecraftBuildAuthority::DroneKinds()
{
	// The FOUR MODELS the presenter already flies, given jobs (owner
	// 2026-08-28: "you can pick what drones you want"). Weights are
	// PROVISIONAL and deliberately opposed - a crew is a trade, not a
	// ladder, so no kind is simply the best one.
	static const TArray<FLBSpacecraftDroneKind> Kinds = []()
	{
		TArray<FLBSpacecraftDroneKind> Out;
		FLBSpacecraftDroneKind Assembly;
		Assembly.KindId = FName(TEXT("Assembly"));
		Assembly.DisplayName = TEXT("Assembly drone");
		Assembly.Role = TEXT("Fits parts. The all-rounder.");
		Assembly.CostPence = 1200000;
		Assembly.FittingWeight = 1.f;
		Assembly.QualityWeight = 1.f;
		Out.Add(Assembly);

		FLBSpacecraftDroneKind Winch;
		Winch.KindId = FName(TEXT("Winch"));
		Winch.DisplayName = TEXT("Winch drone");
		Winch.Role = TEXT("Heavy lift - fast, rougher work.");
		Winch.CostPence = 1600000;
		Winch.FittingWeight = 1.5f;
		Winch.QualityWeight = 0.6f;
		Out.Add(Winch);

		FLBSpacecraftDroneKind Spray;
		Spray.KindId = FName(TEXT("Spray"));
		Spray.DisplayName = TEXT("Spray drone");
		Spray.Role = TEXT("Finishing - slow, but clean work.");
		Spray.CostPence = 1400000;
		Spray.FittingWeight = 0.6f;
		Spray.QualityWeight = 1.6f;
		Out.Add(Spray);

		// THE GROUND CREW. They work under the craft, which is why the
		// lifter can carry the fitting weight it does - it is holding
		// the thing up while the others work. Prices sit above the
		// fliers': a wheeled machine with a lift deck is a bigger buy
		// than a quadcopter.
		FLBSpacecraftDroneKind GroundLifter;
		GroundLifter.KindId = FName(TEXT("GroundLifter"));
		GroundLifter.DisplayName = TEXT("Ground lifter");
		GroundLifter.Role = TEXT("Drives under the craft and takes its weight.");
		GroundLifter.CostPence = 1900000;
		GroundLifter.FittingWeight = 1.4f;
		GroundLifter.QualityWeight = 1.1f;
		GroundLifter.bGroundCrew = true;
		Out.Add(GroundLifter);

		FLBSpacecraftDroneKind GroundAssembly;
		GroundAssembly.KindId = FName(TEXT("GroundAssembly"));
		GroundAssembly.DisplayName = TEXT("Ground assembly rover");
		GroundAssembly.Role = TEXT("Works the underside - gear, bays, ducts.");
		GroundAssembly.CostPence = 1700000;
		GroundAssembly.FittingWeight = 1.2f;
		GroundAssembly.QualityWeight = 1.2f;
		GroundAssembly.bGroundCrew = true;
		Out.Add(GroundAssembly);

		FLBSpacecraftDroneKind GroundSprayer;
		GroundSprayer.KindId = FName(TEXT("GroundSprayer"));
		GroundSprayer.DisplayName = TEXT("Ground sprayer");
		GroundSprayer.Role = TEXT("Seals and finishes the belly. Slow, careful.");
		GroundSprayer.CostPence = 1800000;
		GroundSprayer.FittingWeight = 0.7f;
		GroundSprayer.QualityWeight = 1.7f;
		GroundSprayer.bGroundCrew = true;
		Out.Add(GroundSprayer);

		FLBSpacecraftDroneKind CargoLift;
		CargoLift.KindId = FName(TEXT("CargoLift"));
		CargoLift.DisplayName = TEXT("Cargo-lift drone");
		CargoLift.Role = TEXT("Keeps the stockpile moving. Steady.");
		CargoLift.CostPence = 1300000;
		CargoLift.FittingWeight = 0.9f;
		CargoLift.QualityWeight = 1.1f;
		Out.Add(CargoLift);
		return Out;
	}();
	return Kinds;
}

float ALBSpacecraftBuildAuthority::ComputeTypedCrewQuality(
	const FLBSpacecraftStationRecord& Record)
{
	if (Record.InstalledDroneTypes.Num() == 0)
	{
		return 1.f;   // untyped or empty: nominal, changes nothing
	}
	float Total = 0.f;
	for (const FName& KindId : Record.InstalledDroneTypes)
	{
		const FLBSpacecraftDroneKind* Kind = FindDroneKind(KindId);
		Total += Kind != nullptr ? Kind->QualityWeight : 1.f;
	}
	return Total / static_cast<float>(Record.InstalledDroneTypes.Num());
}

const FLBSpacecraftDroneKind* ALBSpacecraftBuildAuthority::FindDroneKind(
	FName KindId)
{
	for (const FLBSpacecraftDroneKind& Kind : DroneKinds())
	{
		if (Kind.KindId == KindId)
		{
			return &Kind;
		}
	}
	return nullptr;
}

float ALBSpacecraftBuildAuthority::ComputeTypedDroneWorkBonus(
	const FLBSpacecraftStationRecord& Record)
{
	// An untyped crew (a save from before types, or a crew installed
	// by a fixture) keeps exactly the behaviour it had: the plain
	// count. Nothing loses its drones to a data migration.
	if (Record.InstalledDroneTypes.Num() == 0)
	{
		return ComputeDroneWorkBonus(Record.InstalledDrones);
	}
	float Weighted = 0.f;
	for (const FName& KindId : Record.InstalledDroneTypes)
	{
		const FLBSpacecraftDroneKind* Kind = FindDroneKind(KindId);
		Weighted += Kind != nullptr ? Kind->FittingWeight : 1.f;
	}
	// Same curve as the count version, so two nominal drones is still
	// 1.0x and a station is never worse off for choosing its crew.
	return FMath::Clamp(0.5f + 0.25f * Weighted, 0.5f, 2.5f);
}

bool ALBSpacecraftBuildAuthority::RemoveStationDrone(FName StationId,
	int32 SlotIndex, FString& OutReason)
{
	for (FLBSpacecraftStationRecord& Record : Layout.Stations)
	{
		if (Record.StationId != StationId)
		{
			continue;
		}
		if (Record.InstalledDrones <= 0)
		{
			OutReason = FString::Printf(
				TEXT("%s HAS NO INSTALLED DRONES"),
				*StationId.ToString());
			return false;
		}
		--Record.InstalledDrones;
		if (Record.InstalledDroneTypes.IsValidIndex(SlotIndex))
		{
			Record.InstalledDroneTypes.RemoveAt(SlotIndex);
		}
		else if (Record.InstalledDroneTypes.Num() > 0)
		{
			Record.InstalledDroneTypes.Pop();
		}
		OutReason = FString::Printf(TEXT("DRONE REMOVED (%d LEFT)"),
			Record.InstalledDrones);
		return true;
	}
	OutReason = FString::Printf(TEXT("UNKNOWN STATION %s"),
		*StationId.ToString());
	return false;
}

bool ALBSpacecraftBuildAuthority::PlaceStarterHall(FName& OutStationId,
	FString& OutReason)
{
	for (const FLBSpacecraftStationRecord& Record : Layout.Stations)
	{
		const FLBSpacecraftStationDefinition* Definition =
			FindDefinition(Record.DefinitionId);
		if (Definition != nullptr && Definition->bSiteBuilding
			&& !Definition->InteriorFloorCm.IsNearlyZero())
		{
			OutStationId = Record.StationId;
			OutReason = TEXT("A SHIP FACTORY ALREADY STANDS");
			return true;
		}
	}
	return PlaceStation(FName(TEXT("ShipFactoryHall")),
		FTransform(FRotator::ZeroRotator, FVector::ZeroVector),
		OutStationId, OutReason);
}

bool ALBSpacecraftBuildAuthority::IsInteriorPlacementLegal(
	FName DefinitionId, const FTransform& Transform,
	FString& OutReason) const
{
	const FLBSpacecraftStationDefinition* Definition =
		FindDefinition(DefinitionId);
	if (Definition == nullptr || Definition->bSiteBuilding)
	{
		return true; // site buildings stand on the open site
	}
	const FVector2D Half = Definition->FootprintCm * 0.5f;
	const FVector Where = Transform.GetLocation();
	// Yaw-aware: a rotated station's footprint swaps axes, and the
	// grid only ever allows 90-degree steps.
	const float Yaw = Transform.GetRotation().Rotator().Yaw;
	const bool bSwapped = FMath::IsNearlyEqual(
		FMath::Abs(FMath::UnwindDegrees(Yaw)), 90.f, 1.f);
	const FVector2D HalfWorld = bSwapped
		? FVector2D(Half.Y, Half.X) : Half;
	int32 Halls = 0;
	for (const FLBSpacecraftStationRecord& Record : Layout.Stations)
	{
		const FLBSpacecraftStationDefinition* Host =
			FindDefinition(Record.DefinitionId);
		if (Host == nullptr || !Host->bSiteBuilding
			|| Host->InteriorFloorCm.IsNearlyZero())
		{
			continue;
		}
		++Halls;
		const FVector HostWhere = Record.WorldTransform.GetLocation();
		const FVector2D HostHalf = Host->InteriorFloorCm * 0.5f;
		if (FMath::Abs(Where.X - HostWhere.X) + HalfWorld.X <= HostHalf.X
			&& FMath::Abs(Where.Y - HostWhere.Y) + HalfWorld.Y
				<= HostHalf.Y)
		{
			return true;
		}
	}
	OutReason = Halls == 0
		? FString::Printf(
			TEXT("NOTHING IS BUILT ON THIS SITE YET - PLACE A SHIP ")
			TEXT("FACTORY FIRST, THEN BUILD %s INSIDE IT"),
			*Definition->DisplayName.ToUpper())
		: FString::Printf(
			TEXT("%s MUST STAND INSIDE A BUILDING - MOVE IT ONTO A ")
			TEXT("FACTORY FLOOR"), *Definition->DisplayName.ToUpper());
	return false;
}

bool ALBSpacecraftBuildAuthority::PlaceStation(FName DefinitionId,
	const FTransform& Transform, FName& OutStationId, FString& OutReason)
{
	OutStationId = NAME_None;
	// Policy gate first (research locks, power headroom - the game mode's
	// call): a gated family is refused before geometry is even considered.
	if (PlacementGate && !PlacementGate(DefinitionId, OutReason))
	{
		return false;
	}
	if (!IsTransformGridAligned(Transform, OutReason))
	{
		return false;
	}
	// Slot units live in their building, never loose on the floor
	// (owner 2026-08-26: the power plant "is supposed to be in its own
	// building"). Free placement is refused in plain words; the route
	// in is InstallInSlot on a host that owns the class.
	if (const FName Host = FindSlotHostClassFor(DefinitionId);
		!Host.IsNone())
	{
		const FLBSpacecraftStationDefinition* HostDefinition =
			FindDefinition(Host);
		OutReason = FString::Printf(
			TEXT("%s GOES INSIDE A %s - BUILD ONE AND INSTALL IT ")
			TEXT("IN A SLOT"), *DefinitionId.ToString(),
			HostDefinition != nullptr
				? *HostDefinition->DisplayName : *Host.ToString());
		return false;
	}
	if (!EnvelopeIsLegal(DefinitionId, Transform, NAME_None, Layout.Stations,
		OutReason))
	{
		return false;
	}
	// INSIDE THE FACTORY. Everything that is not itself a site building
	// belongs within a placed site building's interior floor (owner
	// 2026-08-28: place the ship factory on the map, "click on it to
	// enter then build factory"). Before any hall exists the site is
	// bare ground and only site buildings may be placed - which is what
	// makes the ship factory the player's genuine first move rather
	// than a step they can skip.
	if (!IsInteriorPlacementLegal(DefinitionId, Transform, OutReason))
	{
		return false;
	}
	FLBSpacecraftStationRecord Record;
	Record.StationId = FName(*FString::Printf(TEXT("%s-%03d"),
		*DefinitionId.ToString(), Layout.NextStationSequence));
	Record.DefinitionId = DefinitionId;
	Record.WorldTransform = Transform;
	Layout.Stations.Add(Record);
	++Layout.NextStationSequence;
	OutStationId = Record.StationId;
	OutReason.Reset();
	return true;
}

int32 ALBSpacecraftBuildAuthority::GetHostedCount(
	FName HostStationId) const
{
	int32 Count = 0;
	for (const FLBSpacecraftStationRecord& Record : Layout.Stations)
	{
		if (Record.HostStationId == HostStationId)
		{
			++Count;
		}
	}
	return Count;
}

bool ALBSpacecraftBuildAuthority::InstallStationDrone(FName StationId,
	FString& OutReason, FName KindId)
{
	for (FLBSpacecraftStationRecord& Record : Layout.Stations)
	{
		if (Record.StationId != StationId)
		{
			continue;
		}
		const FLBSpacecraftStationDefinition* Definition =
			FindDefinition(Record.DefinitionId);
		if (Definition == nullptr || Definition->DroneSlotCount <= 0)
		{
			OutReason = FString::Printf(
				TEXT("%s HAS NO DRONE SLOTS"), *StationId.ToString());
			return false;
		}
		if (Record.InstalledDrones >= Definition->DroneSlotCount)
		{
			OutReason = FString::Printf(
				TEXT("%s DRONE SLOTS FULL (%d/%d)"),
				*StationId.ToString(), Record.InstalledDrones,
				Definition->DroneSlotCount);
			return false;
		}
		// The KIND the player picked, defaulted so every existing
		// caller keeps its behaviour.
		const FLBSpacecraftDroneKind* Kind = FindDroneKind(KindId);
		if (Kind == nullptr)
		{
			Kind = FindDroneKind(FName(TEXT("Assembly")));
		}
		++Record.InstalledDrones;
		Record.InstalledDroneTypes.Add(
			Kind != nullptr ? Kind->KindId : FName(TEXT("Assembly")));
		OutReason = FString::Printf(TEXT("%s INSTALLED (%d/%d)"),
			Kind != nullptr ? *Kind->DisplayName.ToUpper()
				: TEXT("DRONE"),
			Record.InstalledDrones, Definition->DroneSlotCount);
		return true;
	}
	OutReason = FString::Printf(TEXT("UNKNOWN STATION %s"),
		*StationId.ToString());
	return false;
}

bool ALBSpacecraftBuildAuthority::RemoveStationDrone(FName StationId,
	FString& OutReason)
{
	// "Remove the last one" - the shape every existing caller wants -
	// expressed in terms of the slot-aware removal, because two
	// functions that each decrement the crew is exactly how the count
	// and the TYPE LIST drifted apart the day types were added (a
	// station read as seven drones and worked like eight).
	const FLBSpacecraftStationRecord* Record = FindStation(StationId);
	const int32 LastSlot = Record != nullptr
		? Record->InstalledDrones - 1 : 0;
	return RemoveStationDrone(StationId, FMath::Max(LastSlot, 0),
		OutReason);
}

namespace LBSpacecraftFixingSplitPrivate
{
	// The DISTINCT stations of a route, in route order. A station is not
	// the same thing as a route step: MaterialIntake and
	// MaterialProcessing both run on the MaterialProcessor, and
	// AssemblyStaging and Assembly both run on the AssemblyRobot. The
	// split divides parts across STATIONS - splitting per step made the
	// second step overwrite the first step's slice on the shared
	// station, which is a silent way to lose parts.
	//
	// Unity-build safety: qualified by subject.
	/** The route's distinct FITTING stations, in line order. A process
	 *  station (the spray booth) is on the route and is deliberately
	 *  not here: the fixing sequence is split across stations that fit
	 *  parts, and nothing is bolted on inside a paint booth. */
	TArray<FName> SpacecraftDistinctRouteStations(
		const TArray<FLBSpacecraftRouteStep>& Route,
		const ALBSpacecraftBuildAuthority& Build)
	{
		TArray<FName> Stations;
		for (const FLBSpacecraftRouteStep& Step : Route)
		{
			if (Build.IsFittingStation(Step.StationId))
			{
				Stations.AddUnique(Step.StationId);
			}
		}
		return Stations;
	}
}

bool ALBSpacecraftBuildAuthority::IsFittingStation(FName StationId) const
{
	// The pinned trap: when the hundred-part catalogue was first spread
	// across the line, 34 part recipes landed on line stations because
	// the stations were NAMED "fabricator". The lesson was to ask what
	// a station IS, not what it is called - so the booth is excluded by
	// a flag on its definition, and every allocation path asks here.
	const FLBSpacecraftStationRecord* Record = FindStation(StationId);
	const FLBSpacecraftStationDefinition* Definition = Record != nullptr
		? FindDefinition(Record->DefinitionId) : nullptr;
	return Definition != nullptr && !Definition->StageClassId.IsNone()
		&& !Definition->bProcessStation;
}

bool ALBSpacecraftBuildAuthority::SetFixingSplit(
	FName RecipeId, const TArray<int32>& StationCounts, FString& OutReason)
{
	FLBSpacecraftRecipe Recipe;
	if (!FLBSpacecraftProductionCatalog::FindRecipe(RecipeId, Recipe))
	{
		OutReason = FString::Printf(TEXT("UNKNOWN RECIPE %s"),
			*RecipeId.ToString());
		return false;
	}
	const TArray<FName> Sequence =
		FLBSpacecraftProductionCatalog::FixingSequenceItemIds(Recipe);

	TArray<FLBSpacecraftRouteStep> Route;
	FString RouteReason;
	if (!BuildRoute(Route, RouteReason))
	{
		OutReason = FString::Printf(
			TEXT("NO LINE TO SPLIT: %s"), *RouteReason);
		return false;
	}
	const TArray<FName> Stations =
		LBSpacecraftFixingSplitPrivate::SpacecraftDistinctRouteStations(
			Route, *this);
	if (StationCounts.Num() != Stations.Num())
	{
		OutReason = FString::Printf(
			TEXT("SPLIT COVERS %d STATIONS BUT THE LINE HAS %d"),
			StationCounts.Num(), Stations.Num());
		return false;
	}

	int32 Total = 0;
	for (int32 Index = 0; Index < StationCounts.Num(); ++Index)
	{
		if (StationCounts[Index] < 0)
		{
			OutReason = FString::Printf(
				TEXT("%s CANNOT FIT A NEGATIVE NUMBER OF PARTS"),
				*Stations[Index].ToString());
			return false;
		}
		Total += StationCounts[Index];
	}
	// Every part must have a station. A part nobody fits is a part the
	// craft leaves without, discovered as a mystery at the hover test
	// rather than here where it can be pointed at.
	if (Total != Sequence.Num())
	{
		OutReason = FString::Printf(
			TEXT("SPLIT FITS %d PARTS BUT %s NEEDS ALL %d"),
			Total, *RecipeId.ToString(), Sequence.Num());
		return false;
	}

	// Validated whole, THEN applied - the pre-mutation rule. A split
	// rejected halfway would leave the line allocated to neither the old
	// arrangement nor the new one.
	int32 Cursor = 0;
	for (int32 Index = 0; Index < Stations.Num(); ++Index)
	{
		for (FLBSpacecraftStationRecord& Record : Layout.Stations)
		{
			if (Record.StationId != Stations[Index])
			{
				continue;
			}
			Record.AllocatedComponents.Reset();
			for (int32 Slot = 0; Slot < StationCounts[Index]; ++Slot)
			{
				Record.AllocatedComponents.Add(Sequence[Cursor + Slot]);
			}
			break;
		}
		Cursor += StationCounts[Index];
	}
	OutReason = FString::Printf(TEXT("%s SPLIT ACROSS %d STATIONS"),
		*RecipeId.ToString(), Stations.Num());
	return true;
}

bool ALBSpacecraftBuildAuthority::GetFixingSplit(FName RecipeId,
	TArray<FName>& OutStationIds, TArray<int32>& OutStationCounts,
	FString& OutReason) const
{
	OutStationIds.Reset();
	OutStationCounts.Reset();

	FLBSpacecraftRecipe Recipe;
	if (!FLBSpacecraftProductionCatalog::FindRecipe(RecipeId, Recipe))
	{
		OutReason = FString::Printf(TEXT("UNKNOWN RECIPE %s"),
			*RecipeId.ToString());
		return false;
	}
	const TArray<FName> Sequence =
		FLBSpacecraftProductionCatalog::FixingSequenceItemIds(Recipe);

	TArray<FLBSpacecraftRouteStep> Route;
	FString RouteReason;
	if (!BuildRoute(Route, RouteReason))
	{
		OutReason = FString::Printf(TEXT("NO LINE TO READ: %s"),
			*RouteReason);
		return false;
	}

	// Walk the sequence and the line together. A valid split hands out
	// the sequence in order, so the two cursors advance in lockstep;
	// anything else is reported rather than rounded into something
	// plausible.
	int32 Cursor = 0;
	for (const FName& StationId :
		LBSpacecraftFixingSplitPrivate::SpacecraftDistinctRouteStations(
			Route, *this))
	{
		const FLBSpacecraftStationRecord* Record = FindStation(StationId);
		const int32 Count = Record != nullptr
			? Record->AllocatedComponents.Num() : 0;
		if (Record != nullptr)
		{
			for (int32 Slot = 0; Slot < Count; ++Slot)
			{
				if (!Sequence.IsValidIndex(Cursor + Slot)
					|| !Record->AllocatedComponents.Contains(
						Sequence[Cursor + Slot]))
				{
					OutReason = FString::Printf(
						TEXT("%s IS NOT FITTING A CONTIGUOUS RUN OF THE ")
						TEXT("%s SEQUENCE - RE-SPLIT THE LINE"),
						*StationId.ToString(), *RecipeId.ToString());
					return false;
				}
			}
		}
		OutStationIds.Add(StationId);
		OutStationCounts.Add(Count);
		Cursor += Count;
	}
	if (Cursor != Sequence.Num())
	{
		OutReason = FString::Printf(
			TEXT("THE LINE FITS %d OF %s'S %d PARTS - %d HAVE NO ")
			TEXT("STATION"), Cursor, *RecipeId.ToString(),
			Sequence.Num(), Sequence.Num() - Cursor);
		return false;
	}
	OutReason.Reset();
	return true;
}

bool ALBSpacecraftBuildAuthority::SetComponentAllocated(FName StationId,
	FName ComponentItemId, bool bAllocated, FString& OutReason)
{
	if (!ComponentItemId.ToString().StartsWith(TEXT("Component.")))
	{
		OutReason = FString::Printf(
			TEXT("%s IS NOT AN ASSEMBLED COMPONENT"),
			*ComponentItemId.ToString());
		return false;
	}
	for (FLBSpacecraftStationRecord& Record : Layout.Stations)
	{
		if (Record.StationId != StationId)
		{
			continue;
		}
		const FLBSpacecraftStationDefinition* Definition =
			FindDefinition(Record.DefinitionId);
		if (Definition == nullptr || Definition->StageClassId.IsNone())
		{
			OutReason = FString::Printf(
				TEXT("%s IS NOT A LINE STATION - NOTHING IS FITTED ")
				TEXT("THERE"), *StationId.ToString());
			return false;
		}
		// A PROCESS station fits nothing (the spray booth: the craft
		// passes THROUGH it). This path used to check only
		// StageClassId, and the booth's is "LineStation" - so a
		// component could be allocated to it. The booth has no
		// stockpile, so SyncStationStores skips it, no store is ever
		// registered, and the coordinator then asks a store that does
		// not exist for a part it can never get: the line holds on
		// INSUFFICIENT RESOURCES permanently with no way back.
		//
		// IsFittingStation exists for exactly this and its own comment
		// says "every allocation path asks here" - this one did not.
		if (Definition->bProcessStation)
		{
			OutReason = FString::Printf(
				TEXT("%s IS A PROCESS STATION - THE CRAFT PASSES ")
				TEXT("THROUGH IT AND HAS NOTHING FITTED THERE"),
				*StationId.ToString());
			return false;
		}
		if (bAllocated)
		{
			Record.AllocatedComponents.AddUnique(ComponentItemId);
		}
		else
		{
			Record.AllocatedComponents.Remove(ComponentItemId);
		}
		OutReason = FString::Printf(TEXT("%s %s AT %s"),
			*ComponentItemId.ToString(),
			bAllocated ? TEXT("ALLOCATED") : TEXT("REMOVED"),
			*StationId.ToString());
		return true;
	}
	OutReason = FString::Printf(TEXT("UNKNOWN STATION %s"),
		*StationId.ToString());
	return false;
}

float ALBSpacecraftBuildAuthority::GetStationWorkBonus(
	FName StationId) const
{
	for (const FLBSpacecraftStationRecord& Record : Layout.Stations)
	{
		if (Record.StationId == StationId)
		{
			const FLBSpacecraftStationDefinition* Definition =
				FindDefinition(Record.DefinitionId);
			if (Definition != nullptr && Definition->DroneSlotCount > 0)
			{
				return ComputeTypedDroneWorkBonus(Record);
			}
			return 1.f;
		}
	}
	return 1.f;
}

bool ALBSpacecraftBuildAuthority::InstallInSlot(FName HostStationId,
	FName UnitDefinitionId, FName& OutStationId, FString& OutReason)
{
	OutStationId = NAME_None;
	const FLBSpacecraftStationRecord* Host = nullptr;
	for (const FLBSpacecraftStationRecord& Record : Layout.Stations)
	{
		if (Record.StationId == HostStationId)
		{
			Host = &Record;
			break;
		}
	}
	if (Host == nullptr)
	{
		OutReason = FString::Printf(TEXT("UNKNOWN SLOT BUILDING %s"),
			*HostStationId.ToString());
		return false;
	}
	const FLBSpacecraftStationDefinition* HostDefinition =
		FindDefinition(Host->DefinitionId);
	if (HostDefinition == nullptr || HostDefinition->SlotCount <= 0)
	{
		OutReason = FString::Printf(TEXT("%s HAS NO SLOTS"),
			*HostStationId.ToString());
		return false;
	}
	const FLBSpacecraftStationDefinition* UnitDefinition =
		FindDefinition(UnitDefinitionId);
	if (UnitDefinition == nullptr)
	{
		OutReason = FString::Printf(TEXT("UNKNOWN UNIT %s"),
			*UnitDefinitionId.ToString());
		return false;
	}
	const bool bClassLegal =
		HostDefinition->SlotUnitClass == UnitDefinitionId
		|| (HostDefinition->SlotUnitClass
				== FName(TEXT("AnyCraftingMachine"))
			&& UnitDefinition != nullptr
			&& FLBSpacecraftRecipeCatalogue::GetRecipesForStationClass(
				UnitDefinition->GetRecipeClassId()).Num() > 0);
	if (!bClassLegal)
	{
		OutReason = FString::Printf(
			TEXT("%s SLOTS HOLD %s UNITS - %s REFUSED"),
			*HostStationId.ToString(),
			*HostDefinition->SlotUnitClass.ToString(),
			*UnitDefinitionId.ToString());
		return false;
	}
	const int32 Hosted = GetHostedCount(HostStationId);
	if (Hosted >= HostDefinition->SlotCount)
	{
		OutReason = FString::Printf(
			TEXT("%s SLOTS FULL (%d/%d)"), *HostStationId.ToString(),
			Hosted, HostDefinition->SlotCount);
		return false;
	}
	// Slot layout: a 2x2 grid inside the host footprint.
	// Slot centres snap to the build grid: a saved layout is validated
	// with the same grid rule as a placed one, and an off-grid slot
	// (a 2200 cm hall quarters to 550) would fail its own restore.
	const float Grid = GetPlacementGridCm();
	const float QuarterX =
		FMath::GridSnap(HostDefinition->FootprintCm.X * 0.25f, Grid);
	const float QuarterY =
		FMath::GridSnap(HostDefinition->FootprintCm.Y * 0.25f, Grid);
	const FVector SlotLocal[] = {
		FVector(-QuarterX, -QuarterY, 0.f),
		FVector(QuarterX, -QuarterY, 0.f),
		FVector(-QuarterX, QuarterY, 0.f),
		FVector(QuarterX, QuarterY, 0.f) };
	const int32 SlotIndex = FMath::Min(Hosted, 3);
	FTransform UnitTransform = Host->WorldTransform;
	UnitTransform.SetLocation(Host->WorldTransform.TransformPosition(
		SlotLocal[SlotIndex]));
	FLBSpacecraftStationRecord Record;
	Record.StationId = FName(*FString::Printf(TEXT("%s-%03d"),
		*UnitDefinitionId.ToString(), Layout.NextStationSequence));
	Record.DefinitionId = UnitDefinitionId;
	Record.WorldTransform = UnitTransform;
	Record.HostStationId = HostStationId;
	Layout.Stations.Add(Record);
	++Layout.NextStationSequence;
	OutStationId = Record.StationId;
	OutReason.Reset();
	return true;
}

bool ALBSpacecraftBuildAuthority::MoveStation(FName StationId,
	const FTransform& NewTransform, FString& OutReason)
{
	FLBSpacecraftStationRecord* Record = nullptr;
	for (FLBSpacecraftStationRecord& Candidate : Layout.Stations)
	{
		if (Candidate.StationId == StationId)
		{
			Record = &Candidate;
			break;
		}
	}
	if (Record == nullptr)
	{
		OutReason = FString::Printf(TEXT("UNKNOWN STATION %s"),
			*StationId.ToString());
		return false;
	}
	if (!IsTransformGridAligned(NewTransform, OutReason))
	{
		return false;
	}
	if (!EnvelopeIsLegal(Record->DefinitionId, NewTransform, StationId,
		Layout.Stations, OutReason))
	{
		return false;
	}
	Record->WorldTransform = NewTransform;
	OutReason.Reset();
	return true;
}

bool ALBSpacecraftBuildAuthority::RemoveStation(FName StationId,
	FString& OutReason)
{
	const FLBSpacecraftStationRecord* Record = FindStation(StationId);
	if (Record == nullptr)
	{
		OutReason = FString::Printf(TEXT("UNKNOWN STATION %s"),
			*StationId.ToString());
		return false;
	}
	const FLBSpacecraftStationDefinition* Definition =
		FindDefinition(Record->DefinitionId);
	// Removing a station that SERVICES a stage invalidates commissioning
	// (the line may no longer be complete); optional crafting and
	// infrastructure stations come and go without stopping the line.
	const bool bBreaksLine =
		Definition == nullptr || !Definition->StageClassId.IsNone();
	// A slot building takes its hosted units with it (they live
	// inside its footprint and cannot stand alone).
	Layout.Stations.RemoveAll(
		[StationId](const FLBSpacecraftStationRecord& Candidate)
		{
			return Candidate.StationId == StationId
				|| Candidate.HostStationId == StationId;
		});
	if (bBreaksLine)
	{
		Layout.bCommissioned = false;
	}
	OutReason.Reset();
	return true;
}

bool ALBSpacecraftBuildAuthority::CommissionFactory(FString& OutReason)
{
	// ONE repeated station type since 2026-08-27: the line needs at
	// least one line station, and that is all it needs. How many is the
	// player's throughput decision, not a commissioning requirement.
	// The phrase BEFORE COMMISSIONING is load-bearing - callers grep it.
	int32 LineStations = 0;
	for (const FLBSpacecraftStationRecord& Record : Layout.Stations)
	{
		const FLBSpacecraftStationDefinition* Definition =
			FindDefinition(Record.DefinitionId);
		if (Definition != nullptr && !Definition->StageClassId.IsNone())
		{
			++LineStations;
		}
	}
	if (LineStations == 0)
	{
		OutReason = TEXT("FACTORY NEEDS AT LEAST ONE ASSEMBLY STATION ")
			TEXT("BEFORE COMMISSIONING");
		return false;
	}
	// NO BOOTH, NO LINE (owner 2026-08-28: the spray booth is
	// REQUIRED). Paint is not an optional finish here - a craft leaves
	// in the customer's livery, and there is nowhere else to put it on.
	// Refused at COMMISSIONING rather than at delivery, so the player
	// finds out while they are building the line instead of after they
	// have run a whole craft through it.
	{
		bool bHasBooth = false;
		bool bHasFitting = false;
		for (const FLBSpacecraftStationRecord& Record : Layout.Stations)
		{
			const FLBSpacecraftStationDefinition* Definition =
				FindDefinition(Record.DefinitionId);
			if (Definition == nullptr || Definition->StageClassId.IsNone())
			{
				continue;
			}
			bHasBooth = bHasBooth || Definition->bProcessStation;
			bHasFitting = bHasFitting || !Definition->bProcessStation;
		}
		if (bHasFitting && !bHasBooth)
		{
			Layout.bCommissioned = false;
			OutReason = TEXT("THE LINE HAS NO SPRAY BOOTH - EVERY CRAFT ")
				TEXT("LEAVES IN THE CUSTOMER'S LIVERY AND THERE IS ")
				TEXT("NOWHERE TO PAINT IT");
			return false;
		}
	}
	Layout.bCommissioned = true;

	// COMMISSIONING FITS OUT THE LINE: the fixing sequence is split
	// near-evenly across the placed stations in line order, so a craft
	// costs the six assembled components it is made of from the first
	// run. The allocation stays per-station data the player re-splits;
	// this is only the default. Consumption is fail-open on an EMPTY
	// allocation, which is why defaulting matters: an unallocated line
	// built craft for free, 100% margin, whole parts chain optional.
	TArray<FLBSpacecraftRouteStep> Route;
	FString RouteReason;
	if (!BuildRoute(Route, RouteReason))
	{
		Layout.bCommissioned = false;
		OutReason = RouteReason;
		return false;
	}
	// FITTING stations only: handing a share of the fixing sequence to
	// the spray booth would have parts bolted on inside a paint booth,
	// and would quietly starve the stations that should have had them.
	TArray<FName> Stations;
	for (const FLBSpacecraftRouteStep& Step : Route)
	{
		if (IsFittingStation(Step.StationId))
		{
			Stations.AddUnique(Step.StationId);
		}
	}
	const TArray<FLBSpacecraftRecipe>& Recipes =
		FLBSpacecraftProductionCatalog::CanonicalRecipes();
	if (Recipes.Num() > 0 && Stations.Num() > 0)
	{
		// The shared fixing order (internals are shared across tiers).
		const TArray<FName> Sequence =
			FLBSpacecraftProductionCatalog::FixingSequenceItemIds(
				Recipes[0]);
		const int32 Count = Stations.Num();
		const int32 Base = Sequence.Num() / Count;
		const int32 Extra = Sequence.Num() % Count;
		int32 Cursor = 0;
		for (int32 Index = 0; Index < Count; ++Index)
		{
			const int32 Share = Base + (Index < Extra ? 1 : 0);
			for (FLBSpacecraftStationRecord& Record : Layout.Stations)
			{
				if (Record.StationId != Stations[Index])
				{
					continue;
				}
				Record.AllocatedComponents.Reset();
				for (int32 Slot = 0; Slot < Share
					&& Sequence.IsValidIndex(Cursor + Slot); ++Slot)
				{
					Record.AllocatedComponents.Add(Sequence[Cursor + Slot]);
				}
				break;
			}
			Cursor += Share;
		}
	}
	OutReason.Reset();
	return true;
}

bool ALBSpacecraftBuildAuthority::BuildRoute(
	TArray<FLBSpacecraftRouteStep>& OutRoute, FString& OutReason) const
{
	OutRoute.Reset();
	if (!Layout.bCommissioned)
	{
		OutReason = TEXT("FACTORY MUST BE COMMISSIONED BEFORE ROUTING");
		return false;
	}

	// THE ROUTE IS EVERY PLACED LINE STATION, IN LINE ORDER (owner
	// 2026-08-27: one repeated station type, Car Manufacture style).
	// It used to be one station per fabrication stage, picked biggest-
	// mark-then-nearest; now the craft physically visits each station
	// the player placed and has parts fitted at every one. How many
	// stations the line has IS the throughput decision.
	//
	// Order: ascending Y, then X. Every line this game has ever laid -
	// the dev builder, the test fixtures, the starter spine - runs
	// along Y, so Y-order is line order. When the site map brings
	// free-form tracks, this becomes arc-length along the laid track.
	struct FLBSpacecraftOrderedStation
	{
		const FLBSpacecraftStationRecord* Record = nullptr;
		const FLBSpacecraftStationDefinition* Definition = nullptr;
	};
	TArray<FLBSpacecraftOrderedStation> Line;
	for (const FLBSpacecraftStationRecord& Record : Layout.Stations)
	{
		const FLBSpacecraftStationDefinition* Definition =
			FindDefinition(Record.DefinitionId);
		if (Definition == nullptr || Definition->StageClassId.IsNone())
		{
			continue;
		}
		FLBSpacecraftOrderedStation Entry;
		Entry.Record = &Record;
		Entry.Definition = Definition;
		Line.Add(Entry);
	}
	if (Line.Num() == 0)
	{
		OutReason = TEXT("NO LINE STATIONS PLACED - THE ROUTE IS EMPTY");
		return false;
	}
	Line.Sort([](const FLBSpacecraftOrderedStation& A,
		const FLBSpacecraftOrderedStation& B)
	{
		const FVector LocationA = A.Record->WorldTransform.GetLocation();
		const FVector LocationB = B.Record->WorldTransform.GetLocation();
		if (LocationA.Y != LocationB.Y)
		{
			return LocationA.Y < LocationB.Y;
		}
		return LocationA.X < LocationB.X;
	});

	const int32 Count = Line.Num();
	for (int32 Index = 0; Index < Count; ++Index)
	{
		FLBSpacecraftRouteStep Step;
		Step.StationId = Line[Index].Record->StationId;
		Step.DefinitionId = Line[Index].Record->DefinitionId;
		Step.StationClassId = Line[Index].Definition->StageClassId;
		// The step carries the PRODUCT stage a craft ARRIVES in here:
		// station i of N covers stage rows [i*6/N ..), so stage and
		// station stay coherent at any line length - the save
		// validator and the topology hash both key on it.
		Step.Stage = FLBSpacecraftProductionCatalog::StageForRouteIndex(
			Index, Count);
		OutRoute.Add(Step);
	}
	OutReason.Reset();
	return true;
}

bool ALBSpacecraftBuildAuthority::RouteCanServiceRecipe(
	const TArray<FLBSpacecraftRouteStep>& InRoute,
	const FLBSpacecraftRecipe& Recipe, FString& OutReason)
{
	for (const FLBSpacecraftRouteStep& Step : InRoute)
	{
		// The PLACED mark decides capacity; StationClassId is the fallback
		// for legacy steps that never recorded a definition.
		const FLBSpacecraftStationDefinition* Definition = FindDefinition(
			Step.DefinitionId.IsNone() ? Step.StationClassId
				: Step.DefinitionId);
		if (Definition == nullptr)
		{
			OutReason = FString::Printf(
				TEXT("ROUTE STEP %s HAS AN UNKNOWN STATION CLASS"),
				*Step.StationId.ToString());
			return false;
		}
		const FVector& Craft = Recipe.CraftEnvelopeCm;
		const FVector& Max = Definition->MaxCraftEnvelopeCm;
		if (Craft.X > Max.X || Craft.Y > Max.Y || Craft.Z > Max.Z)
		{
			OutReason = FString::Printf(
				TEXT("STATION %s (%s) CANNOT HOLD A %.0fx%.0fx%.0f CM CRAFT ")
				TEXT("- ITS LIMIT IS %.0fx%.0fx%.0f CM. A LARGER STATION ")
				TEXT("MARK IS REQUIRED"),
				*Step.StationId.ToString(), *Definition->DisplayName,
				Craft.X, Craft.Y, Craft.Z, Max.X, Max.Y, Max.Z);
			return false;
		}
	}
	OutReason.Reset();
	return true;
}

bool ALBSpacecraftBuildAuthority::ValidateState(
	const FLBSpacecraftFactoryLayoutState& State, FString& OutReason) const
{
	TSet<FName> Ids;
	int32 MaxSequence = 0;
	for (int32 Index = 0; Index < State.Stations.Num(); ++Index)
	{
		const FLBSpacecraftStationRecord& Record = State.Stations[Index];
		if (Record.StationId.IsNone())
		{
			OutReason = TEXT("A SAVED STATION HAS NO ID");
			return false;
		}
		bool bAlready = false;
		Ids.Add(Record.StationId, &bAlready);
		if (bAlready)
		{
			OutReason = FString::Printf(TEXT("DUPLICATE STATION ID %s"),
				*Record.StationId.ToString());
			return false;
		}
		if (!IsTransformGridAligned(Record.WorldTransform, OutReason))
		{
			return false;
		}
		// Overlap check against the OTHER saved stations only.
		// Hosted slot-building units overlap their host BY DESIGN -
		// exempt the host/hosted family from each other (found while
		// adding drone slots: a save with slotted units would have
		// refused to restore).
		TArray<FLBSpacecraftStationRecord> Others;
		for (int32 Other = 0; Other < State.Stations.Num(); ++Other)
		{
			if (Other == Index)
			{
				continue;
			}
			const FLBSpacecraftStationRecord& Candidate =
				State.Stations[Other];
			const bool bFamily =
				(!Record.HostStationId.IsNone()
					&& (Candidate.StationId == Record.HostStationId
						|| Candidate.HostStationId
							== Record.HostStationId))
				|| Candidate.HostStationId == Record.StationId;
			if (!bFamily)
			{
				Others.Add(Candidate);
			}
		}
		if (Record.HostStationId.IsNone()
			&& !EnvelopeIsLegal(Record.DefinitionId,
				Record.WorldTransform, NAME_None, Others, OutReason))
		{
			return false;
		}
		// Drone slots: within bounds, allocations are components.
		const FLBSpacecraftStationDefinition* SlotDefinition =
			FindDefinition(Record.DefinitionId);
		const int32 SlotMax = SlotDefinition != nullptr
			? SlotDefinition->DroneSlotCount : 0;
		if (Record.InstalledDrones < 0 || Record.InstalledDrones > SlotMax)
		{
			OutReason = FString::Printf(
				TEXT("SAVED STATION %s HAS %d DRONES FOR %d SLOTS"),
				*Record.StationId.ToString(), Record.InstalledDrones,
				SlotMax);
			return false;
		}
		for (const FName& Allocated : Record.AllocatedComponents)
		{
			if (!Allocated.ToString().StartsWith(TEXT("Component.")))
			{
				OutReason = FString::Printf(
					TEXT("SAVED STATION %s ALLOCATES NON-COMPONENT %s"),
					*Record.StationId.ToString(),
					*Allocated.ToString());
				return false;
			}
		}
		int32 Sequence = 0;
		FString Suffix = Record.StationId.ToString();
		int32 DashIndex = INDEX_NONE;
		if (Suffix.FindLastChar(TEXT('-'), DashIndex))
		{
			Sequence = FCString::Atoi(*Suffix.Mid(DashIndex + 1));
		}
		MaxSequence = FMath::Max(MaxSequence, Sequence);
	}
	if (State.NextStationSequence <= MaxSequence)
	{
		OutReason = TEXT("SAVED SEQUENCE COUNTER WOULD REUSE A STATION ID");
		return false;
	}
	if (State.bCommissioned)
	{
		TSet<FName> ServicedClasses;
		for (const FLBSpacecraftStationRecord& Record : State.Stations)
		{
			const FLBSpacecraftStationDefinition* Definition =
				FindDefinition(Record.DefinitionId);
			if (Definition != nullptr && !Definition->StageClassId.IsNone())
			{
				ServicedClasses.Add(Definition->StageClassId);
			}
		}
		for (const FLBSpacecraftStageDescriptor& Row :
			FLBSpacecraftProductionCatalog::StageTable())
		{
			// Mirrors CommissionFactory: any mark of a class satisfies it.
			if (!Row.StationClassId.IsNone()
				&& !ServicedClasses.Contains(Row.StationClassId))
			{
				OutReason = TEXT(
					"SAVE CLAIMS COMMISSIONED WITHOUT EVERY ROUTE CLASS");
				return false;
			}
		}
	}
	OutReason.Reset();
	return true;
}

bool ALBSpacecraftBuildAuthority::RestoreState(
	const FLBSpacecraftFactoryLayoutState& State, FString& OutReason)
{
	if (!ValidateState(State, OutReason))
	{
		return false; // layout untouched - restore is all or nothing
	}
	Layout = State;
	OutReason.Reset();
	return true;
}

const FLBSpacecraftStationRecord* ALBSpacecraftBuildAuthority::FindStation(
	FName StationId) const
{
	for (const FLBSpacecraftStationRecord& Record : Layout.Stations)
	{
		if (Record.StationId == StationId)
		{
			return &Record;
		}
	}
	return nullptr;
}
