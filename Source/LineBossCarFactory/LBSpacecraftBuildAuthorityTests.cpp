#if WITH_DEV_AUTOMATION_TESTS

#include "LBSpacecraftBuildAuthority.h"
#include "LBSpacecraftDroneFleetAuthority.h"
#include "LBSpacecraftInventoryAuthority.h"
#include "LBSpacecraftPowerAuthority.h"
#include "LBSpacecraftGameMode.h"
#include "LBSpacecraftProductionAuthority.h"

#include "Engine/World.h"
#include "Misc/AutomationTest.h"

namespace LBSpacecraftBuildAuthorityTestsPrivate
{
	UWorld* MakeSpacecraftBuildTestWorld()
	{
		return UWorld::CreateWorld(EWorldType::Game, false,
			FName(TEXT("LBSpacecraftBuildWorld")));
	}

	FTransform SpacecraftGridTransform(float XCm, float YCm, float YawDeg = 0.f)
	{
		return FTransform(FRotator(0.f, YawDeg, 0.f), FVector(XCm, YCm, 0.f));
	}

	/** Places one legal station of each class; returns false on any failure. */
	bool PlaceSpacecraftFullLine(ALBSpacecraftBuildAuthority& Authority,
		FString& OutReason)
	{
		const TCHAR* Classes[] = {
			TEXT("MaterialProcessor"), TEXT("HullFabricator"),
			TEXT("ComponentFabricator"), TEXT("AssemblyRobot") };
		float Y = -4000.f;
		for (const TCHAR* ClassId : Classes)
		{
			FName StationId;
			if (!Authority.PlaceStation(FName(ClassId),
				SpacecraftGridTransform(0.f, Y), StationId, OutReason))
			{
				return false;
			}
			Y += 2200.f;
		}
		// The SPRAY BOOTH closes the line: since 2026-08-28 a line
		// cannot commission without one, so a "full line" that lacked
		// it would not be full.
		FName BoothId;
		return Authority.PlaceStation(FName(TEXT("SprayBooth")),
			SpacecraftGridTransform(0.f, Y), BoothId, OutReason);
	}
}

IMPLEMENT_SIMPLE_AUTOMATION_TEST(FLBSpacecraftGridSnapTest,
	"LineBoss.Spacecraft.FactoryBuilder.GridSnapFailsClosed",
	EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)

bool FLBSpacecraftGridSnapTest::RunTest(const FString& Parameters)
{
	(void)Parameters;
	using namespace LBSpacecraftBuildAuthorityTestsPrivate;
	UWorld* World = MakeSpacecraftBuildTestWorld();
	ALBSpacecraftBuildAuthority* Authority =
		World->SpawnActor<ALBSpacecraftBuildAuthority>();

		// EVERY factory is built INSIDE a ship factory (owner
		// 2026-08-28). The hall is the player's first move on the
		// world map, so the fixtures take it too.
		{
			FName SpacecraftTestHallId;
			FString SpacecraftTestHallReason;
			Authority->PlaceStarterHall(SpacecraftTestHallId,
				SpacecraftTestHallReason);
		}
	if (!TestNotNull(TEXT("authority spawns"), Authority))
	{
		World->DestroyWorld(false);
		return false;
	}
	FString Reason;
	FName StationId;

	// off-grid X
	TestFalse(TEXT("off-grid placement is rejected"),
		Authority->PlaceStation(FName(TEXT("MaterialProcessor")),
			SpacecraftGridTransform(150.f, 0.f), StationId, Reason));
	TestTrue(TEXT("rejection names the grid"),
		Reason.Contains(TEXT("100 CM GRID")));

	// non-quarter yaw
	TestFalse(TEXT("45 degree yaw is rejected"),
		Authority->PlaceStation(FName(TEXT("MaterialProcessor")),
			SpacecraftGridTransform(0.f, 0.f, 45.f), StationId, Reason));

	// floating above the floor
	FTransform Floating = SpacecraftGridTransform(0.f, 0.f);
	Floating.SetLocation(FVector(0.f, 0.f, 50.f));
	TestFalse(TEXT("off-datum placement is rejected"),
		Authority->PlaceStation(FName(TEXT("MaterialProcessor")), Floating,
			StationId, Reason));

	// unknown definition
	TestFalse(TEXT("unknown station class is rejected"),
		Authority->PlaceStation(FName(TEXT("PaintBooth")),
			SpacecraftGridTransform(0.f, 0.f), StationId, Reason));

	// legal placements: on grid, quarter turns
	TestTrue(TEXT("on-grid placement succeeds"),
		Authority->PlaceStation(FName(TEXT("MaterialProcessor")),
			SpacecraftGridTransform(0.f, 0.f), StationId, Reason));
	TestTrue(TEXT("station id is issued"), !StationId.IsNone());
	TestTrue(TEXT("90 degree yaw is legal"),
		Authority->PlaceStation(FName(TEXT("MaterialProcessor")),
			SpacecraftGridTransform(2000.f, 0.f, 90.f), StationId, Reason));

	World->DestroyWorld(false);
	return true;
}

IMPLEMENT_SIMPLE_AUTOMATION_TEST(FLBSpacecraftOverlapTest,
	"LineBoss.Spacecraft.FactoryBuilder.OverlapAndBoundsFailClosed",
	EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)

bool FLBSpacecraftOverlapTest::RunTest(const FString& Parameters)
{
	(void)Parameters;
	using namespace LBSpacecraftBuildAuthorityTestsPrivate;
	UWorld* World = MakeSpacecraftBuildTestWorld();
	ALBSpacecraftBuildAuthority* Authority =
		World->SpawnActor<ALBSpacecraftBuildAuthority>();

		// EVERY factory is built INSIDE a ship factory (owner
		// 2026-08-28). The hall is the player's first move on the
		// world map, so the fixtures take it too.
		{
			FName SpacecraftTestHallId;
			FString SpacecraftTestHallReason;
			Authority->PlaceStarterHall(SpacecraftTestHallId,
				SpacecraftTestHallReason);
		}
	FString Reason;
	FName First;
	FName Second;

	// MaterialProcessor is 1200x800 cm.
	TestTrue(TEXT("first station places"),
		Authority->PlaceStation(FName(TEXT("MaterialProcessor")),
			SpacecraftGridTransform(0.f, 0.f), First, Reason));

	// 800 cm away on X: envelopes (1200 wide) overlap -> rejected.
	TestFalse(TEXT("overlapping placement is rejected"),
		Authority->PlaceStation(FName(TEXT("MaterialProcessor")),
			SpacecraftGridTransform(800.f, 0.f), Second, Reason));
	TestTrue(TEXT("rejection names the blocking station"),
		Reason.Contains(First.ToString()));

	// exactly touching edge to edge (1200 cm apart) is legal.
	TestTrue(TEXT("edge-to-edge placement is legal"),
		Authority->PlaceStation(FName(TEXT("MaterialProcessor")),
			SpacecraftGridTransform(1200.f, 0.f), Second, Reason));

	// yaw swaps the footprint: a 90-degree MaterialProcessor is 800 wide in
	// X, so at 1100 cm from station one (600+400=1000 < 1100) it fits.
	FName Third;
	TestTrue(TEXT("rotated footprint uses swapped extents"),
		Authority->PlaceStation(FName(TEXT("MaterialProcessor")),
			SpacecraftGridTransform(-1100.f, 0.f, 90.f), Third, Reason));

	// leaving the buildable floor is rejected.
	FName Fourth;
	TestFalse(TEXT("placement outside the floor is rejected"),
		Authority->PlaceStation(FName(TEXT("MaterialProcessor")),
			// Half a footprint past the site edge - derived from the
			// site's own size, not a copied literal, so widening the
			// world map (600 m, owner 2026-08-28) never turns this
			// bounds test into a test of nothing.
			SpacecraftGridTransform(
				ALBSpacecraftBuildAuthority::SiteHalfExtentCm() - 100.f,
				0.f), Fourth, Reason));
	TestTrue(TEXT("rejection names the floor"),
		Reason.Contains(TEXT("BUILDABLE FLOOR")));

	// moving onto another station is rejected and leaves the mover in place.
	TestFalse(TEXT("move onto an occupied envelope is rejected"),
		Authority->MoveStation(Second, SpacecraftGridTransform(0.f, 0.f),
			Reason));

	World->DestroyWorld(false);
	return true;
}

IMPLEMENT_SIMPLE_AUTOMATION_TEST(FLBSpacecraftCommissionRouteTest,
	"LineBoss.Spacecraft.FactoryBuilder.CommissionAndRouteFromPlacement",
	EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)

bool FLBSpacecraftCommissionRouteTest::RunTest(const FString& Parameters)
{
	(void)Parameters;
	using namespace LBSpacecraftBuildAuthorityTestsPrivate;
	UWorld* World = MakeSpacecraftBuildTestWorld();
	ALBSpacecraftBuildAuthority* Authority =
		World->SpawnActor<ALBSpacecraftBuildAuthority>();

		// EVERY factory is built INSIDE a ship factory (owner
		// 2026-08-28). The hall is the player's first move on the
		// world map, so the fixtures take it too.
		{
			FName SpacecraftTestHallId;
			FString SpacecraftTestHallReason;
			Authority->PlaceStarterHall(SpacecraftTestHallId,
				SpacecraftTestHallReason);
		}
	FString Reason;

	// An empty factory refuses to commission, naming the missing class.
	TestFalse(TEXT("empty factory cannot commission"),
		Authority->CommissionFactory(Reason));
	TestTrue(TEXT("refusal names a station class"),
		Reason.Contains(TEXT("BEFORE COMMISSIONING")));

	// The route also refuses before commissioning.
	TArray<FLBSpacecraftRouteStep> Route;
	TestFalse(TEXT("route refuses before commissioning"),
		Authority->BuildRoute(Route, Reason));

	TestTrue(TEXT("full line places"),
		PlaceSpacecraftFullLine(*Authority, Reason));
	TestTrue(TEXT("full line commissions"),
		Authority->CommissionFactory(Reason));
	TestTrue(TEXT("route builds"), Authority->BuildRoute(Route, Reason));

	// ONE repeated station type (owner 2026-08-27): the route is every
	// placed line station in line order, so its length is the number of
	// stations placed - the player's throughput decision - not the
	// stage table's row count. Each step carries the ARRIVAL stage the
	// derived stage map assigns it, monotonically up the ladder.
	// Four fitting stations plus the spray booth the line cannot
	// commission without (owner 2026-08-28).
	TestEqual(TEXT("route length equals the stations placed"), Route.Num(),
		5);
	ELBSpacecraftStage Previous = ELBSpacecraftStage::MaterialIntake;
	for (int32 Index = 0; Index < Route.Num(); ++Index)
	{
		const FLBSpacecraftRouteStep& Step = Route[Index];
		TestEqual(TEXT("route step carries the derived arrival stage"),
			Step.Stage, FLBSpacecraftProductionCatalog::StageForRouteIndex(
				Index, Route.Num()));
		TestTrue(TEXT("arrival stages never go backwards"),
			Step.Stage >= Previous);
		Previous = Step.Stage;
		TestEqual(TEXT("route step uses the line station class"),
			Step.StationClassId, FName(TEXT("LineStation")));
		TestTrue(TEXT("route step binds a placed station"),
			!Step.StationId.IsNone());
	}

	// Removing a station de-commissions; the route fails closed again.
	if (Route.Num() == 0)
	{
		AddError(TEXT("no route to remove from"));
		World->DestroyWorld(false);
		return false;
	}
	const FName Removed = Route.Last().StationId;
	TestTrue(TEXT("station removes"),
		Authority->RemoveStation(Removed, Reason));
	TestFalse(TEXT("factory is no longer commissioned"),
		Authority->IsCommissioned());
	TestFalse(TEXT("route refuses after decommission"),
		Authority->BuildRoute(Route, Reason));

	World->DestroyWorld(false);
	return true;
}

IMPLEMENT_SIMPLE_AUTOMATION_TEST(FLBSpacecraftLayoutSaveTest,
	"LineBoss.Spacecraft.FactoryBuilder.SaveValidatesBeforeRestore",
	EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)

bool FLBSpacecraftLayoutSaveTest::RunTest(const FString& Parameters)
{
	(void)Parameters;
	using namespace LBSpacecraftBuildAuthorityTestsPrivate;
	UWorld* World = MakeSpacecraftBuildTestWorld();
	ALBSpacecraftBuildAuthority* Authority =
		World->SpawnActor<ALBSpacecraftBuildAuthority>();

		// EVERY factory is built INSIDE a ship factory (owner
		// 2026-08-28). The hall is the player's first move on the
		// world map, so the fixtures take it too.
		{
			FName SpacecraftTestHallId;
			FString SpacecraftTestHallReason;
			Authority->PlaceStarterHall(SpacecraftTestHallId,
				SpacecraftTestHallReason);
		}
	FString Reason;

	TestTrue(TEXT("full line places"),
		PlaceSpacecraftFullLine(*Authority, Reason));
	TestTrue(TEXT("full line commissions"),
		Authority->CommissionFactory(Reason));

	const FLBSpacecraftFactoryLayoutState Snapshot = Authority->CaptureState();
	TestTrue(TEXT("captured snapshot validates"),
		Authority->ValidateState(Snapshot, Reason));

	// Round trip into a fresh authority.
	ALBSpacecraftBuildAuthority* Fresh =
		World->SpawnActor<ALBSpacecraftBuildAuthority>();

		// EVERY factory is built INSIDE a ship factory (owner
		// 2026-08-28). The hall is the player's first move on the
		// world map, so the fixtures take it too.
		{
			FName SpacecraftTestHallId;
			FString SpacecraftTestHallReason;
			Fresh->PlaceStarterHall(SpacecraftTestHallId,
				SpacecraftTestHallReason);
		}
	TestTrue(TEXT("snapshot restores into a fresh authority"),
		Fresh->RestoreState(Snapshot, Reason));
	TestEqual(TEXT("restored station count matches"),
		Fresh->GetStations().Num(), Snapshot.Stations.Num());
	TestTrue(TEXT("restored factory keeps commissioning"),
		Fresh->IsCommissioned());

	// Tampered snapshots are rejected wholesale and mutate nothing.
	FLBSpacecraftFactoryLayoutState OffGrid = Snapshot;
	OffGrid.Stations[0].WorldTransform.SetLocation(FVector(33.f, 0.f, 0.f));
	TestFalse(TEXT("off-grid tamper is rejected"),
		Fresh->RestoreState(OffGrid, Reason));

	FLBSpacecraftFactoryLayoutState Duplicate = Snapshot;
	Duplicate.Stations[1].StationId = Duplicate.Stations[0].StationId;
	TestFalse(TEXT("duplicate-id tamper is rejected"),
		Fresh->RestoreState(Duplicate, Reason));

	FLBSpacecraftFactoryLayoutState StaleCounter = Snapshot;
	StaleCounter.NextStationSequence = 1;
	TestFalse(TEXT("stale sequence counter is rejected"),
		Fresh->RestoreState(StaleCounter, Reason));

	// One repeated station type: a commissioned line with THREE stations
	// is legitimate now, so dropping one is no longer a false claim.
	// The false claim is a commissioned flag over NO line stations.
	FLBSpacecraftFactoryLayoutState FalseClaim = Snapshot;
	for (int32 Index = FalseClaim.Stations.Num() - 1; Index >= 0; --Index)
	{
		const FLBSpacecraftStationDefinition* Definition =
			ALBSpacecraftBuildAuthority::FindDefinition(
				FalseClaim.Stations[Index].DefinitionId);
		if (Definition != nullptr && !Definition->StageClassId.IsNone())
		{
			FalseClaim.Stations.RemoveAt(Index);
		}
	}
	TestFalse(TEXT("commissioned claim with no line stations is rejected"),
		Fresh->RestoreState(FalseClaim, Reason));

	// After all the rejected tampers, the authority still holds the good state.
	TestEqual(TEXT("rejected restores leave the layout untouched"),
		Fresh->GetStations().Num(), Snapshot.Stations.Num());
	TestTrue(TEXT("still commissioned after rejected restores"),
		Fresh->IsCommissioned());

	World->DestroyWorld(false);
	return true;
}

IMPLEMENT_SIMPLE_AUTOMATION_TEST(FLBSpacecraftCraftCapacityTest,
	"LineBoss.Spacecraft.FactoryBuilder.StationCapacityFailsClosedForBigCraft",
	EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)

bool FLBSpacecraftCraftCapacityTest::RunTest(const FString& Parameters)
{
	(void)Parameters;
	using namespace LBSpacecraftBuildAuthorityTestsPrivate;
	UWorld* World = MakeSpacecraftBuildTestWorld();
	ALBSpacecraftBuildAuthority* Authority =
		World->SpawnActor<ALBSpacecraftBuildAuthority>();

		// EVERY factory is built INSIDE a ship factory (owner
		// 2026-08-28). The hall is the player's first move on the
		// world map, so the fixtures take it too.
		{
			FName SpacecraftTestHallId;
			FString SpacecraftTestHallReason;
			Authority->PlaceStarterHall(SpacecraftTestHallId,
				SpacecraftTestHallReason);
		}
	FString Reason;

	TestTrue(TEXT("full line places"),
		PlaceSpacecraftFullLine(*Authority, Reason));
	TestTrue(TEXT("commissions"), Authority->CommissionFactory(Reason));
	TArray<FLBSpacecraftRouteStep> Route;
	TestTrue(TEXT("route builds"), Authority->BuildRoute(Route, Reason));

	// Every Mk1 station must hold the SMALLEST craft (the Scout)...
	FLBSpacecraftRecipe Scout;
	TestTrue(TEXT("Scout recipe exists"),
		FLBSpacecraftProductionCatalog::FindRecipe(
			FName(TEXT("SCOUT-01")), Scout));
	TestTrue(TEXT("Mk1 line holds the Scout"),
		ALBSpacecraftBuildAuthority::RouteCanServiceRecipe(Route, Scout,
			Reason));

	// ...and refuse a bigger tier, naming the station and the needed mark.
	FLBSpacecraftRecipe Cargo = Scout;
	Cargo.RecipeId = FName(TEXT("CARGO-01"));
	Cargo.CraftEnvelopeCm = FVector(2200.f, 1200.f, 600.f);
	TestFalse(TEXT("Mk1 line refuses a cargo-sized craft"),
		ALBSpacecraftBuildAuthority::RouteCanServiceRecipe(Route, Cargo,
			Reason));
	TestTrue(TEXT("refusal demands a larger station mark"),
		Reason.Contains(TEXT("LARGER STATION MARK")));

	// Catalogue sanity: every ROUTE station class declares a capacity at
	// least the size of the smallest craft. Crafting families hold parts,
	// never a craft, and must declare exactly zero (the capacity law does
	// not apply to them).
	for (const FLBSpacecraftStationDefinition& Definition :
		ALBSpacecraftBuildAuthority::StationCatalogue())
	{
		if (Definition.bRouteRequired)
		{
			TestTrue(FString::Printf(TEXT("%s declares a capacity"),
				*Definition.DefinitionId.ToString()),
				Definition.MaxCraftEnvelopeCm.X >= Scout.CraftEnvelopeCm.X
				&& Definition.MaxCraftEnvelopeCm.Y >= Scout.CraftEnvelopeCm.Y
				&& Definition.MaxCraftEnvelopeCm.Z >= Scout.CraftEnvelopeCm.Z);
		}
		else
		{
			TestTrue(FString::Printf(TEXT("%s is a parts station"),
				*Definition.DefinitionId.ToString()),
				Definition.MaxCraftEnvelopeCm.IsNearlyZero());
		}
	}

	World->DestroyWorld(false);
	return true;
}


IMPLEMENT_SIMPLE_AUTOMATION_TEST(FLBSpacecraftGridAndSlotsTest,
	"LineBoss.Spacecraft.Build.MeteredGridAndSlotBuildings",
	EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)

bool FLBSpacecraftGridAndSlotsTest::RunTest(const FString& Parameters)
{
	(void)Parameters;
	UWorld* World = UWorld::CreateWorld(EWorldType::Game, false,
		FName(TEXT("LBSpacecraftGridSlotsWorld")));
	ALBSpacecraftBuildAuthority* Build =
		World->SpawnActor<ALBSpacecraftBuildAuthority>();

		// EVERY factory is built INSIDE a ship factory (owner
		// 2026-08-28). The hall is the player's first move on the
		// world map, so the fixtures take it too.
		{
			FName SpacecraftTestHallId;
			FString SpacecraftTestHallReason;
			Build->PlaceStarterHall(SpacecraftTestHallId,
				SpacecraftTestHallReason);
		}
	ALBSpacecraftPowerAuthority* Power =
		World->SpawnActor<ALBSpacecraftPowerAuthority>();
	ALBSpacecraftProductionAuthority* Production =
		World->SpawnActor<ALBSpacecraftProductionAuthority>();
	FString Reason;

	// --- metered grid (owner 2026-08-26: buy electric until the
	// plant). A load with NO plants connects on the mains feed... ---
	TestTrue(TEXT("a load connects on grid credit alone"),
		Power->ConnectLoad(FName(TEXT("Load.A")), 400, Reason));
	TestEqual(TEXT("the whole draw is metered"),
		Power->GetGridUseKw(), 400);
	// ...and one minute of use bills draw x tariff to the ledger.
	const int64 CashBefore = Production->GetCashPence();
	Power->TickGridMeter(60.0, Production);
	TestEqual(TEXT("one kW-minute rate billed for 400 kW"),
		CashBefore - Production->GetCashPence(),
		400 * Power->GridTariffPencePerKwMinute);
	// Own generation covers first: metered use drops to zero.
	TestTrue(TEXT("a plant registers"),
		Power->RegisterSupply(FName(TEXT("Plant.A")), 1500, Reason));
	TestEqual(TEXT("own generation ends the metering"),
		Power->GetGridUseKw(), 0);
	const int64 CashAfterPlant = Production->GetCashPence();
	Power->TickGridMeter(60.0, Production);
	// Surplus SELLS BACK (owner 2026-08-26, the Car Manufacture
	// model), but a generator throttles to its load: 1500 own against
	// a 400 kW draw exports 400, not the whole 1100 spare.
	TestEqual(TEXT("export is capped by the site's own load"),
		Power->GetGridExportKw(), 400);
	TestEqual(TEXT("a minute of surplus earned the feed-in rate"),
		Production->GetCashPence() - CashAfterPlant,
		400 * Power->GridSellbackPencePerKwMinute);

	// AN IDLE FACTORY SELLS NOTHING. This is the whole point of the
	// load cap: cash that rises while the player does nothing takes
	// the downside out of every build decision.
	TestTrue(TEXT("the load is released"),
		Power->DisconnectLoad(FName(TEXT("Load.A")), Reason));
	TestEqual(TEXT("no load, no export"), Power->GetGridExportKw(), 0);
	const int64 CashWhileIdle = Production->GetCashPence();
	Power->TickGridMeter(600.0, Production);
	TestEqual(TEXT("ten idle minutes earn nothing"),
		Production->GetCashPence(), CashWhileIdle);

	// --- slot buildings ---
	FName HallId;
	if (!TestTrue(TEXT("the power station places (gate unbound in rigs)"),
		Build->PlaceStation(FName(TEXT("PowerStation")),
			FTransform(FRotator::ZeroRotator,
				FVector(-16000.f, 0.f, 0.f)), HallId, Reason)))
	{
		AddError(FString::Printf(TEXT("power station refused: %s"),
			*Reason));
	}
	FName UnitId;
	TestFalse(TEXT("a rack refuses a power slot"),
		Build->InstallInSlot(HallId, FName(TEXT("StorageRack")), UnitId,
			Reason));
	TestTrue(TEXT("the refusal names the slot class"),
		Reason.Contains(TEXT("SLOTS HOLD")));
	// FILL IT, whatever it holds: the slot count belongs to the
	// building's definition (it grew with the building on 2026-08-28),
	// and a test that hard-codes it stops testing "full" the moment
	// the number changes.
	const FLBSpacecraftStationDefinition* PowerDefinition =
		ALBSpacecraftBuildAuthority::FindDefinition(
			FName(TEXT("PowerStation")));
	TestNotNull(TEXT("the power plant is catalogued"), PowerDefinition);
	const int32 Slots = PowerDefinition != nullptr
		? PowerDefinition->SlotCount : 0;
	TestTrue(TEXT("it holds something"), Slots > 0);
	// Funded on purpose: this test is about SLOT CAPACITY, and a
	// building that now holds eight generators costs more than the
	// starting capital to fill. Running out of money here would fail
	// the test for a true fact about the economy that it is not
	// testing.
	FString FundReason;
	TestTrue(TEXT("the yard is funded for the fill"),
		Production->EarnPence(Slots * 20000000, FundReason));
	for (int32 Slot = 0; Slot < Slots; ++Slot)
	{
		TestTrue(TEXT("a plant unit installs"),
			ALBSpacecraftGameMode::InstallInSlotPowered(*Build, *Power,
				HallId, FName(TEXT("PowerPlant")), UnitId, Reason,
				Production));
	}
	TestEqual(TEXT("every slot is filled"),
		Build->GetHostedCount(HallId), Slots);
	TestFalse(TEXT("one more install refuses - slots full"),
		Build->InstallInSlot(HallId, FName(TEXT("PowerPlant")), UnitId,
			Reason));
	TestTrue(TEXT("the refusal names the count"),
		Reason.Contains(TEXT("SLOTS FULL")));
	TestEqual(TEXT("hosted plants supply the grid"),
		Power->GetOwnSupplyKw(), 1500 + Slots * 1500);

	// Removing the building takes the hosted units - and their
	// supplies - with it through the powered path.
	TestTrue(TEXT("the building removes"),
		ALBSpacecraftGameMode::RemoveStationPowered(*Build, *Power,
			*World->SpawnActor<ALBSpacecraftInventoryAuthority>(),
			nullptr, HallId, Reason, Production));
	TestEqual(TEXT("hosted units went with it"),
		Build->GetHostedCount(HallId), 0);
	TestEqual(TEXT("their supplies disconnected"),
		Power->GetOwnSupplyKw(), 1500);

	World->DestroyWorld(false);
	return true;
}


IMPLEMENT_SIMPLE_AUTOMATION_TEST(FLBSpacecraftFixingSplitTest,
	"LineBoss.Spacecraft.FactoryBuilder.TheLineSplitsTheFixingSequence",
	EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)

bool FLBSpacecraftFixingSplitTest::RunTest(const FString& Parameters)
{
	(void)Parameters;
	using namespace LBSpacecraftBuildAuthorityTestsPrivate;
	UWorld* World = MakeSpacecraftBuildTestWorld();
	ALBSpacecraftBuildAuthority* Authority =
		World->SpawnActor<ALBSpacecraftBuildAuthority>();

		// EVERY factory is built INSIDE a ship factory (owner
		// 2026-08-28). The hall is the player's first move on the
		// world map, so the fixtures take it too.
		{
			FName SpacecraftTestHallId;
			FString SpacecraftTestHallReason;
			Authority->PlaceStarterHall(SpacecraftTestHallId,
				SpacecraftTestHallReason);
		}
	FString Reason;
	const FName Scout(TEXT("SCOUT-01"));

	TArray<FName> Stations;
	TArray<int32> Counts;

	// No line, no split. Reading one refuses rather than returning an
	// empty arrangement that would render as "nothing is fitted anywhere".
	TestFalse(TEXT("an unbuilt line has no split to read"),
		Authority->GetFixingSplit(Scout, Stations, Counts, Reason));
	TestFalse(TEXT("and says why"), Reason.IsEmpty());

	TestTrue(TEXT("full line places"),
		PlaceSpacecraftFullLine(*Authority, Reason));
	TestTrue(TEXT("full line commissions"),
		Authority->CommissionFactory(Reason));

	// THE SHIPPED DEFAULT MUST ALREADY BE A VALID SPLIT. Commissioning
	// allocates from what each stage produces, which predates splits
	// entirely - if that arrangement is not contiguous and in order, then
	// every existing save opens onto a line the player is told to fix.
	TestTrue(TEXT("the commissioned default reads back as a valid split"),
		Authority->GetFixingSplit(Scout, Stations, Counts, Reason));
	// One entry per DISTINCT station, not per route step: the
	// MaterialProcessor serves both intake and processing, and the
	// AssemblyRobot serves both staging and assembly, so the line has
	// fewer stations than it has stages.
	TestTrue(TEXT("one entry per distinct station, not per stage"),
		Stations.Num() > 0
			&& Stations.Num()
				<= FLBSpacecraftProductionCatalog::StationStageCount());
	TestEqual(TEXT("stations are listed once each"), Stations.Num(),
		TSet<FName>(Stations).Num());
	TestEqual(TEXT("counts match stations"), Counts.Num(), Stations.Num());

	FLBSpacecraftRecipe Recipe;
	TestTrue(TEXT("scout resolves"),
		FLBSpacecraftProductionCatalog::FindRecipe(Scout, Recipe));
	const int32 PartCount = Recipe.FixingOrder.Num();
	int32 Total = 0;
	for (int32 Count : Counts)
	{
		Total += Count;
	}
	TestEqual(TEXT("every part has a station"), Total, PartCount);

	// Re-splitting: hand one part from whichever station has the most to
	// the LAST station on the line. Derived rather than hard-coded, so
	// this survives the default arrangement being retuned.
	int32 Busiest = INDEX_NONE;
	for (int32 Index = 0; Index < Counts.Num(); ++Index)
	{
		if (Busiest == INDEX_NONE || Counts[Index] > Counts[Busiest])
		{
			Busiest = Index;
		}
	}
	TestTrue(TEXT("some station fits something"),
		Busiest != INDEX_NONE && Counts[Busiest] > 0);
	if (Busiest != INDEX_NONE && Counts[Busiest] > 0
		&& Busiest != Counts.Num() - 1)
	{
		TArray<int32> Moved = Counts;
		Moved[Busiest] -= 1;
		Moved[Moved.Num() - 1] += 1;
		TestTrue(TEXT("the line re-splits"),
			Authority->SetFixingSplit(Scout, Moved, Reason));

		TArray<int32> ReadBack;
		TestTrue(TEXT("the new split reads back"),
			Authority->GetFixingSplit(Scout, Stations, ReadBack, Reason));
		TestEqual(TEXT("the moved part landed where it was sent"),
			ReadBack, Moved);

		// And the parts a station holds are the RIGHT slice, not just the
		// right number: the last station must now hold the last part in
		// the fixing order.
		const TArray<FName> Sequence =
			FLBSpacecraftProductionCatalog::FixingSequenceItemIds(Recipe);
		const FLBSpacecraftStationRecord* Last =
			Authority->FindStation(Stations.Last());
		if (TestNotNull(TEXT("last station exists"), Last))
		{
			TestTrue(TEXT("the end of the line fits the end of the "
				"sequence"),
				Last->AllocatedComponents.Contains(Sequence.Last()));
		}
	}

	// Refusals. Each of these would otherwise produce a line that looks
	// allocated and quietly never finishes a craft.
	TArray<int32> TooFew;
	TooFew.Add(PartCount);
	TestFalse(TEXT("a split that misses stations is refused"),
		Authority->SetFixingSplit(Scout, TooFew, Reason));
	TestTrue(TEXT("and counts them"), Reason.Contains(TEXT("STATIONS")));

	TArray<int32> Negative;
	Negative.Init(0, Stations.Num());
	Negative[0] = -1;
	Negative[1] = PartCount + 1;
	TestFalse(TEXT("a negative slice is refused"),
		Authority->SetFixingSplit(Scout, Negative, Reason));

	TArray<int32> Short;
	Short.Init(0, Stations.Num());
	Short[0] = PartCount - 1; // one part left with nowhere to go
	TestFalse(TEXT("leaving a part unallocated is refused"),
		Authority->SetFixingSplit(Scout, Short, Reason));
	TestTrue(TEXT("and says how many are homeless"),
		Reason.Contains(TEXT("NEEDS ALL")));

	// A refused split must not have half-applied. The line still reads
	// back exactly as it did before the attempt.
	TArray<int32> Unchanged;
	TestTrue(TEXT("the line still reads"),
		Authority->GetFixingSplit(Scout, Stations, Unchanged, Reason));
	int32 StillTotal = 0;
	for (int32 Count : Unchanged)
	{
		StillTotal += Count;
	}
	TestEqual(TEXT("a refused split changed nothing"), StillTotal,
		PartCount);

	// A whole line on one station is legal - inefficient, not invalid.
	TArray<int32> AllOnFirst;
	AllOnFirst.Init(0, Stations.Num());
	AllOnFirst[0] = PartCount;
	TestTrue(TEXT("one station may fit the lot"),
		Authority->SetFixingSplit(Scout, AllOnFirst, Reason));

	World->DestroyWorld(false);
	return true;
}

IMPLEMENT_SIMPLE_AUTOMATION_TEST(FLBSpacecraftMarkLadderTest,
	"LineBoss.Spacecraft.Build.EveryMk2CostsMoreThanTheMk1ItReplaces",
	EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)

bool FLBSpacecraftMarkLadderTest::RunTest(const FString& Parameters)
{
	(void)Parameters;
	// The Mk2 line cost was halved on 2026-08-27 (owner-agreed): 850,000
	// cr for the four route marks was 25 to 30 Scout deliveries before a
	// player saw the second tier at all. Halving four literals is easy;
	// halving them PAST the Mk1 they upgrade would be easy too, and the
	// result - an upgrade that is bigger, faster AND cheaper - would be
	// nonsense that nothing else in the codebase would notice. This
	// walks the whole catalogue so the next tuning pass cannot do it
	// either, whichever direction it moves the numbers.
	const TArray<FLBSpacecraftStationDefinition>& Catalogue =
		ALBSpacecraftBuildAuthority::StationCatalogue();
	int32 MarksChecked = 0;
	for (const FLBSpacecraftStationDefinition& Mk2 : Catalogue)
	{
		const FString Id = Mk2.DefinitionId.ToString();
		if (!Id.EndsWith(TEXT("Mk2")))
		{
			continue;
		}
		const FName BaseId(*Id.LeftChop(3));
		const FLBSpacecraftStationDefinition* Mk1 =
			Catalogue.FindByPredicate(
				[BaseId](const FLBSpacecraftStationDefinition& Entry)
				{
					return Entry.DefinitionId == BaseId;
				});
		if (Mk1 == nullptr)
		{
			AddError(FString::Printf(
				TEXT("%s upgrades a station that is not in the "
					"catalogue (%s)"), *Id, *BaseId.ToString()));
			continue;
		}
		++MarksChecked;
		TestTrue(*FString::Printf(
			TEXT("%s costs more than %s"), *Id, *BaseId.ToString()),
			Mk2.CostPence > Mk1->CostPence);
		// An upgrade must also BE an upgrade in the ways the player
		// bought it for, or the extra cost buys nothing.
		TestTrue(*FString::Printf(TEXT("%s works faster"), *Id),
			Mk2.CraftSpeedMultiplier >= Mk1->CraftSpeedMultiplier);
		TestTrue(*FString::Printf(TEXT("%s is not smaller"), *Id),
			Mk2.FootprintCm.X >= Mk1->FootprintCm.X
				&& Mk2.FootprintCm.Y >= Mk1->FootprintCm.Y);
	}
	// Guard the guard: if the naming convention ever changes, this test
	// would quietly check nothing and still pass.
	TestTrue(TEXT("the catalogue actually contains Mk2 marks"),
		MarksChecked >= 4);
	return true;
}

IMPLEMENT_SIMPLE_AUTOMATION_TEST(FLBSpacecraftStationDroneSlotsTest,
	"LineBoss.Spacecraft.Build.LineStationDroneSlotsAndAllocation",
	EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)

bool FLBSpacecraftStationDroneSlotsTest::RunTest(const FString& Parameters)
{
	(void)Parameters;
	// Pure bonus maths: 0 drones crawl, 2 nominal, 8 fly, capped.
	TestEqual(TEXT("no drones crawl at half pace"),
		ALBSpacecraftBuildAuthority::ComputeDroneWorkBonus(0), 0.5f);
	TestEqual(TEXT("two drones are nominal"),
		ALBSpacecraftBuildAuthority::ComputeDroneWorkBonus(2), 1.f);
	TestEqual(TEXT("eight drones fly at 2.5x"),
		ALBSpacecraftBuildAuthority::ComputeDroneWorkBonus(8), 2.5f);

	UWorld* World = UWorld::CreateWorld(EWorldType::Game, false,
		FName(TEXT("LBSpacecraftDroneSlotsWorld")));
	ALBSpacecraftBuildAuthority* Build =
		World->SpawnActor<ALBSpacecraftBuildAuthority>();

		// EVERY factory is built INSIDE a ship factory (owner
		// 2026-08-28). The hall is the player's first move on the
		// world map, so the fixtures take it too.
		{
			FName SpacecraftTestHallId;
			FString SpacecraftTestHallReason;
			Build->PlaceStarterHall(SpacecraftTestHallId,
				SpacecraftTestHallReason);
		}
	FString Reason;
	FName StationId;
	TestTrue(TEXT("a line station places"),
		Build->PlaceStation(FName(TEXT("AssemblyRobot")),
			FTransform(FRotator::ZeroRotator, FVector(0.f, 0.f, 0.f)),
			StationId, Reason));

	// Slots fill to eight and refuse the ninth, named.
	for (int32 Drone = 0; Drone < 8; ++Drone)
	{
		TestTrue(TEXT("a drone installs"),
			Build->InstallStationDrone(StationId, Reason));
	}
	TestFalse(TEXT("the ninth drone refuses"),
		Build->InstallStationDrone(StationId, Reason));
	TestTrue(TEXT("the refusal names the slots"),
		Reason.Contains(TEXT("DRONE SLOTS FULL")));
	TestEqual(TEXT("full slots fly"),
		Build->GetStationWorkBonus(StationId), 2.5f);
	TestTrue(TEXT("a drone sells back"),
		Build->RemoveStationDrone(StationId, Reason));

	// A crafting machine has no drone slots.
	// Parts machines live in the sub-assembly hall (owner 2026-08-26),
	// so the mill is INSTALLED, never placed loose on the floor.
	FName HallId;
	TestTrue(TEXT("a sub-assembly hall places"),
		Build->PlaceStation(FName(TEXT("SubAssemblyHall")),
			FTransform(FRotator::ZeroRotator,
				FVector(16000.f, 0.f, 0.f)), HallId, Reason));
	FName MillId;
	TestFalse(TEXT("a loose mill is refused"),
		Build->PlaceStation(FName(TEXT("RollingMill")),
			FTransform(FRotator::ZeroRotator,
				FVector(4000.f, 0.f, 0.f)), MillId, Reason));
	TestTrue(TEXT("the refusal names the hall"),
		Reason.Contains(TEXT("GOES INSIDE")));
	TestTrue(TEXT("a mill installs in the hall"),
		Build->InstallInSlot(HallId, FName(TEXT("RollingMill")),
			MillId, Reason));
	TestFalse(TEXT("the mill refuses drone slots"),
		Build->InstallStationDrone(MillId, Reason));

	// Allocation: components only, line stations only.
	TestTrue(TEXT("hull allocates"),
		Build->SetComponentAllocated(StationId,
			FName(TEXT("Component.Hull")), true, Reason));
	TestFalse(TEXT("a raw refuses allocation"),
		Build->SetComponentAllocated(StationId,
			FName(TEXT("Raw.IronOre")), true, Reason));
	TestFalse(TEXT("the mill refuses allocation"),
		Build->SetComponentAllocated(MillId,
			FName(TEXT("Component.Hull")), true, Reason));

	// The fleet mirrors BOUGHT drones on line stations.
	ALBSpacecraftDroneFleetAuthority* Fleet =
		World->SpawnActor<ALBSpacecraftDroneFleetAuthority>();
	Fleet->SyncFromBuild(Build, nullptr);
	int32 LineCrew = 0;
	for (int32 Index = 0; Index < 8; ++Index)
	{
		if (Fleet->FindDrone(StationId, Index) != nullptr)
		{
			++LineCrew;
		}
	}
	TestEqual(TEXT("the fleet crews the bought drones"), LineCrew, 7);
	TestEqual(TEXT("the crafting cell keeps its standing pair"),
		Fleet->FindDrone(MillId, 1) != nullptr, true);

	// Everything survives the save pipeline.
	FLBSpacecraftFactoryLayoutState Snapshot = Build->CaptureState();
	TestTrue(TEXT("the slotted layout validates"),
		Build->ValidateState(Snapshot, Reason));
	TestTrue(TEXT("the slotted layout restores"),
		Build->RestoreState(Snapshot, Reason));
	TestEqual(TEXT("drones survived the roundtrip"),
		Build->GetStationWorkBonus(StationId),
		ALBSpacecraftBuildAuthority::ComputeDroneWorkBonus(7));

	World->DestroyWorld(false);
	return true;
}


IMPLEMENT_SIMPLE_AUTOMATION_TEST(FLBSpacecraftWorldMapOpeningTest,
	"LineBoss.Spacecraft.Build.TheShipFactoryIsBuiltBeforeAnythingInsideIt",
	EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)

bool FLBSpacecraftWorldMapOpeningTest::RunTest(const FString& Parameters)
{
	(void)Parameters;
	// THE OPENING (owner 2026-08-28): "game should start on world map
	// and player should be only able to pick the ship factory, place on
	// map, click on it to enter then build factory."
	//
	// The mechanic that makes that real rather than cosmetic: nothing
	// but a site building may be placed on bare ground, and everything
	// else must stand within a placed building's interior floor. A
	// player who tries to build a line first is TOLD to place a ship
	// factory - the refusal is the tutorial.
	UWorld* World = UWorld::CreateWorld(EWorldType::Game, false,
		FName(TEXT("LBSpacecraftWorldMapOpeningWorld")));
	ALBSpacecraftBuildAuthority* Build =
		World->SpawnActor<ALBSpacecraftBuildAuthority>();
	FString Reason;
	FName StationId;

	TestFalse(TEXT("a line station on bare ground is refused"),
		Build->PlaceStation(FName(TEXT("AssemblyRobot")),
			FTransform(FRotator::ZeroRotator, FVector(0.f, 0.f, 0.f)),
			StationId, Reason));
	TestTrue(TEXT("the refusal names the first move"),
		Reason.Contains(TEXT("PLACE A SHIP FACTORY FIRST")));
	TestEqual(TEXT("nothing was placed"), Build->GetStations().Num(), 0);

	FName HallId;
	TestTrue(TEXT("the ship factory places on bare ground"),
		Build->PlaceStarterHall(HallId, Reason));
	TestEqual(TEXT("the site holds one building"),
		Build->GetStations().Num(), 1);

	// Inside it, the same station is legal - and the hall's own
	// envelope never blocks what it contains.
	TestTrue(TEXT("the line places inside the ship factory"),
		Build->PlaceStation(FName(TEXT("AssemblyRobot")),
			FTransform(FRotator::ZeroRotator, FVector(0.f, 0.f, 0.f)),
			StationId, Reason));

	// Beyond the interior floor it is refused again, by a DIFFERENT
	// reason: there is a factory, this is just not inside it.
	FName OutsideId;
	const FLBSpacecraftStationDefinition* Hall =
		ALBSpacecraftBuildAuthority::FindDefinition(
			FName(TEXT("ShipFactoryHall")));
	TestNotNull(TEXT("the ship factory is catalogued"), Hall);
	if (Hall != nullptr)
	{
		const float BeyondY = Hall->InteriorFloorCm.Y * 0.5f + 900.f;
		TestFalse(TEXT("a station beyond the floor is refused"),
			Build->PlaceStation(FName(TEXT("StorageRack")),
				FTransform(FRotator::ZeroRotator,
					FVector(0.f, BeyondY, 0.f)), OutsideId, Reason));
	}

	// A second ship factory may not sit on the first: site buildings
	// still clash with each other like any other footprint.
	FName SecondHallId;
	TestFalse(TEXT("two ship factories cannot share ground"),
		Build->PlaceStation(FName(TEXT("ShipFactoryHall")),
			FTransform(FRotator::ZeroRotator, FVector(0.f, 0.f, 0.f)),
			SecondHallId, Reason));

	World->DestroyWorld(false);
	return true;
}


IMPLEMENT_SIMPLE_AUTOMATION_TEST(FLBSpacecraftDroneCrewChoiceTest,
	"LineBoss.Spacecraft.Build.TheCrewYouPickChangesWhatAStationDoes",
	EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)

bool FLBSpacecraftDroneCrewChoiceTest::RunTest(const FString& Parameters)
{
	(void)Parameters;
	// Owner 2026-08-28: "with drone slots instead of robots and
	// clicking on it should bring up a build menu like car manufacturer
	// so you can pick what drones you want."
	//
	// A menu of four identical things is not a choice, so the property
	// worth pinning is that the PICK MATTERS: a station crewed with
	// winches works faster than the same station crewed with sprays,
	// and both remember what they are.
	UWorld* World = UWorld::CreateWorld(EWorldType::Game, false,
		FName(TEXT("LBSpacecraftDroneCrewWorld")));
	ALBSpacecraftBuildAuthority* Build =
		World->SpawnActor<ALBSpacecraftBuildAuthority>();
	FString Reason;
	FName HallId;
	Build->PlaceStarterHall(HallId, Reason);

	// Four fliers plus the three wheeled ground crew (owner
	// 2026-08-28). The count is asserted rather than the names so
	// adding a kind is a deliberate act, not an accident.
	TestEqual(TEXT("seven kinds are offered"),
		ALBSpacecraftBuildAuthority::DroneKinds().Num(), 7);
	int32 GroundKinds = 0;
	for (const FLBSpacecraftDroneKind& Kind :
		ALBSpacecraftBuildAuthority::DroneKinds())
	{
		if (Kind.bGroundCrew) { ++GroundKinds; }
	}
	TestEqual(TEXT("three of them work on the floor"), GroundKinds, 3);
	TestNull(TEXT("an unknown kind resolves to nothing"),
		ALBSpacecraftBuildAuthority::FindDroneKind(
			FName(TEXT("Chicken"))));

	FName FastId;
	FName FineId;
	TestTrue(TEXT("two stations place"),
		Build->PlaceStation(FName(TEXT("AssemblyRobot")),
			FTransform(FRotator::ZeroRotator, FVector(0.f, -2400.f, 0.f)),
			FastId, Reason)
		&& Build->PlaceStation(FName(TEXT("AssemblyRobot")),
			FTransform(FRotator::ZeroRotator, FVector(0.f, 0.f, 0.f)),
			FineId, Reason));
	for (int32 Index = 0; Index < 3; ++Index)
	{
		TestTrue(TEXT("a winch hires"),
			Build->InstallStationDrone(FastId, Reason,
				FName(TEXT("Winch"))));
		TestTrue(TEXT("a spray hires"),
			Build->InstallStationDrone(FineId, Reason,
				FName(TEXT("Spray"))));
	}
	const FLBSpacecraftStationRecord* Fast = Build->FindStation(FastId);
	const FLBSpacecraftStationRecord* Fine = Build->FindStation(FineId);
	TestNotNull(TEXT("the fast station stands"), Fast);
	TestNotNull(TEXT("the fine station stands"), Fine);
	if (Fast == nullptr || Fine == nullptr)
	{
		World->DestroyWorld(false);
		return false;
	}
	TestEqual(TEXT("the crew is remembered by kind"),
		Fast->InstalledDroneTypes.Num(), 3);
	TestEqual(TEXT("and it is the kind that was picked"),
		Fast->InstalledDroneTypes[0], FName(TEXT("Winch")));
	TestEqual(TEXT("the count still agrees with the types"),
		Fast->InstalledDrones, Fast->InstalledDroneTypes.Num());

	// THE POINT: same station, same crew SIZE, different work rate.
	const float FastBonus =
		ALBSpacecraftBuildAuthority::ComputeTypedDroneWorkBonus(*Fast);
	const float FineBonus =
		ALBSpacecraftBuildAuthority::ComputeTypedDroneWorkBonus(*Fine);
	TestTrue(TEXT("winches fit faster than sprays"), FastBonus > FineBonus);

	// An UNTYPED crew (an old save) keeps exactly its old behaviour.
	FLBSpacecraftStationRecord Legacy = *Fast;
	Legacy.InstalledDroneTypes.Reset();
	TestEqual(TEXT("an untyped crew falls back to the plain count"),
		ALBSpacecraftBuildAuthority::ComputeTypedDroneWorkBonus(Legacy),
		ALBSpacecraftBuildAuthority::ComputeDroneWorkBonus(
			Legacy.InstalledDrones));

	// Dismissal takes the named slot, and the two lists stay in step.
	TestTrue(TEXT("a drone is dismissed"),
		Build->RemoveStationDrone(FastId, 0, Reason));
	Fast = Build->FindStation(FastId);
	TestEqual(TEXT("the count fell"), Fast->InstalledDrones, 2);
	TestEqual(TEXT("and so did the type list"),
		Fast->InstalledDroneTypes.Num(), 2);
	while (Build->RemoveStationDrone(FastId, 0, Reason)) {}
	TestFalse(TEXT("an empty station refuses dismissal"),
		Build->RemoveStationDrone(FastId, 0, Reason));
	TestTrue(TEXT("the refusal says so"),
		Reason.Contains(TEXT("NO INSTALLED DRONES")));

	World->DestroyWorld(false);
	return true;
}


IMPLEMENT_SIMPLE_AUTOMATION_TEST(FLBSpacecraftPortalClearsStationsTest,
	"LineBoss.Spacecraft.Gantry.PortalClearsEveryLineStation",
	EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)

bool FLBSpacecraftPortalClearsStationsTest::RunTest(
	const FString& Parameters)
{
	(void)Parameters;
	using Catalog = FLBSpacecraftProductionCatalog;

	// THE CRANE DRIVES OVER THESE. A gantry is a portal: its legs run on
	// rails outboard of the line and the bridge passes over the station
	// tops as it travels. So the span is bounded by the widest station
	// it must pass, not by the craft it happens to be carrying - and
	// sizing it against the craft is exactly how it came to be 21.5 m
	// while its own assembly station Mk2 was 27.0 m across.
	//
	// This walks the real catalogue rather than trusting the constant,
	// so adding a wider mark fails here instead of producing a crane
	// that clips through a station in a packaged build.
	const float Declared = Catalog::WidestLineStationAcrossCm();
	float WidestFound = 0.f;
	FName WidestId;

	for (const FLBSpacecraftStationDefinition& Definition :
		ALBSpacecraftBuildAuthority::StationCatalogue())
	{
		if (Definition.StageClassId != FName(TEXT("LineStation")))
		{
			continue;
		}
		// A station may be placed at any quarter turn and a rotated
		// footprint swaps its axes, so the crane has to clear the
		// LARGER one whichever way the player faces it.
		const float Across = FMath::Max(Definition.FootprintCm.X,
			Definition.FootprintCm.Y);
		if (Across > WidestFound)
		{
			WidestFound = Across;
			WidestId = Definition.DefinitionId;
		}
	}

	if (!TestTrue(TEXT("the catalogue contains at least one line station"),
		WidestFound > 0.f))
	{
		return false;
	}

	TestTrue(*FString::Printf(
		TEXT("declared widest line station (%.0f cm) is not smaller than "
			"%s at %.0f cm - raise WidestLineStationAcrossCm and rebuild "
			"the gantry to match"),
		Declared, *WidestId.ToString(), WidestFound),
		Declared >= WidestFound - 0.5f);

	// And the portal actually clears it, with its legs outside rather
	// than merely level with the station's corner.
	const float Span = Catalog::GantryRailSpanCm();
	TestTrue(*FString::Printf(
		TEXT("gantry span %.0f cm clears the widest line station %s at "
			"%.0f cm"),
		Span, *WidestId.ToString(), WidestFound),
		Span > WidestFound);

	// The craft constraint still has to hold. Both bound the span; the
	// larger wins, and neither may be dropped.
	TestTrue(*FString::Printf(
		TEXT("gantry span %.0f cm still clears the craft envelope "
			"%.0f cm"),
		Span, Catalog::FactoryMaxCraftEnvelopeCm().Y),
		Span > Catalog::FactoryMaxCraftEnvelopeCm().Y);

	return true;
}

#endif // WITH_DEV_AUTOMATION_TESTS
