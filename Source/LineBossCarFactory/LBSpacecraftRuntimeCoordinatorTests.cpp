#if WITH_DEV_AUTOMATION_TESTS

#include "LBSpacecraftRuntimeCoordinator.h"

#include "Engine/World.h"
#include "Misc/AutomationTest.h"

namespace LBSpacecraftRuntimeCoordinatorTestsPrivate
{
	struct FLBSpacecraftRuntimeRig
	{
		UWorld* World = nullptr;
		ALBSpacecraftBuildAuthority* Build = nullptr;
		ALBSpacecraftProductionAuthority* Production = nullptr;
		ALBSpacecraftRuntimeCoordinator* Coordinator = nullptr;
	};

	FLBSpacecraftRuntimeRig MakeSpacecraftRuntimeRig()
	{
		FLBSpacecraftRuntimeRig Rig;
		Rig.World = UWorld::CreateWorld(EWorldType::Game, false,
			FName(TEXT("LBSpacecraftRuntimeWorld")));
		Rig.Build = Rig.World->SpawnActor<ALBSpacecraftBuildAuthority>();

		// EVERY factory is built INSIDE a ship factory (owner
		// 2026-08-28). The hall is the player's first move on the
		// world map, so the fixtures take it too.
		{
			FName SpacecraftTestHallId;
			FString SpacecraftTestHallReason;
			Rig.Build->PlaceStarterHall(SpacecraftTestHallId,
				SpacecraftTestHallReason);
		}
		Rig.Production =
			Rig.World->SpawnActor<ALBSpacecraftProductionAuthority>();
		Rig.Coordinator =
			Rig.World->SpawnActor<ALBSpacecraftRuntimeCoordinator>();
		return Rig;
	}

	bool PlaceAndCommissionSpacecraftLine(FLBSpacecraftRuntimeRig& Rig,
		FString& OutReason)
	{
		const TCHAR* Classes[] = {
			TEXT("MaterialProcessor"), TEXT("HullFabricator"),
			TEXT("ComponentFabricator"), TEXT("AssemblyRobot") };
		float Y = -4000.f;
		for (const TCHAR* ClassId : Classes)
		{
			FName StationId;
			if (!Rig.Build->PlaceStation(FName(ClassId),
				FTransform(FRotator::ZeroRotator, FVector(0.f, Y, 0.f)),
				StationId, OutReason))
			{
				return false;
			}
			// Crewed to nominal: these rigs model a factory that
			// WORKS, so its craft come out clean. The defective path
			// has its own tests rather than quietly colouring every
			// flow assertion.
			for (int32 Crew = 0; Crew < 2; ++Crew)
			{
				if (!Rig.Build->InstallStationDrone(StationId, OutReason))
				{
					return false;
				}
			}
			Y += 2200.f;
		}
		// The SPRAY BOOTH closes the line: since 2026-08-28 no line
		// commissions without one, so a rig that lacked it would be
		// testing a factory the game refuses to run. Crewed, like the
		// stations above and for the same reason.
		{
			FName BoothId;
			if (!Rig.Build->PlaceStation(FName(TEXT("SprayBooth")),
				FTransform(FRotator::ZeroRotator, FVector(0.f, Y, 0.f)),
				BoothId, OutReason))
			{
				return false;
			}
			for (int32 Crew = 0; Crew < 2; ++Crew)
			{
				FString CrewReason;
				Rig.Build->InstallStationDrone(BoothId, CrewReason,
					FName(TEXT("Spray")));
			}
		}
		return Rig.Build->CommissionFactory(OutReason);
	}

	/** The same line with NO drones at all - every station bodges the
	 *  fit, which is what the hover test is there to catch. */
	bool PlaceAndCommissionUncrewedLine(FLBSpacecraftRuntimeRig& Rig,
		FString& OutReason)
	{
		const TCHAR* Classes[] = {
			TEXT("MaterialProcessor"), TEXT("HullFabricator"),
			TEXT("ComponentFabricator"), TEXT("AssemblyRobot") };
		float Y = -4000.f;
		for (const TCHAR* ClassId : Classes)
		{
			FName StationId;
			if (!Rig.Build->PlaceStation(FName(ClassId),
				FTransform(FRotator::ZeroRotator, FVector(0.f, Y, 0.f)),
				StationId, OutReason))
			{
				return false;
			}
			Y += 2200.f;
		}
		// The SPRAY BOOTH closes the line: since 2026-08-28 no line
		// commissions without one, so a rig that lacked it would be
		// testing a factory the game refuses to run.
		{
			FName BoothId;
			if (!Rig.Build->PlaceStation(FName(TEXT("SprayBooth")),
				FTransform(FRotator::ZeroRotator, FVector(0.f, Y, 0.f)),
				BoothId, OutReason))
			{
				return false;
			}
		}
		return Rig.Build->CommissionFactory(OutReason);
	}

	bool OfferAndAcceptScoutContract(FLBSpacecraftRuntimeRig& Rig,
		const TCHAR* ContractId, int32 Quantity, FString& OutReason)
	{
		FLBSpacecraftContract Contract;
		Contract.ContractId = FName(ContractId);
		Contract.RecipeId = FName(TEXT("SCOUT-01"));
		Contract.Quantity = Quantity;
		Contract.PricePerUnitPence = 5000000;
		if (!Rig.Production->OfferContract(Contract, OutReason))
		{
			return false;
		}
		return Rig.Production->AcceptContract(FName(ContractId), OutReason);
	}

	// Scout-01 cycle total: 20+45+90+75+30+120+60 = 440 sim seconds.
	constexpr double ScoutTotalCycleSeconds = 440.0;
}

IMPLEMENT_SIMPLE_AUTOMATION_TEST(FLBSpacecraftAnyLineLengthTest,
	"LineBoss.Spacecraft.RuntimeCoordinator.AnyLineLengthBuildsTheCraft",
	EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)

bool FLBSpacecraftAnyLineLengthTest::RunTest(const FString& Parameters)
{
	(void)Parameters;
	using namespace LBSpacecraftRuntimeCoordinatorTestsPrivate;

	// THE PROPERTY THE RESTRUCTURE EXISTS FOR (owner 2026-08-27: "one
	// station type like car manufacturer"): the line is however many
	// stations the player placed. Every other test runs four; this one
	// runs a cramped two and a lavish seven, and holds each to the
	// same physics:
	//   - the craft visits EVERY station, stages climbing monotonically,
	//   - total work is the recipe's, however finely it is split - more
	//     stations pipeline the work, they do not delete it.
	for (const int32 StationCount : { 2, 7 })
	{
		FLBSpacecraftRuntimeRig Rig = MakeSpacecraftRuntimeRig();
		FString Reason;
		float Y = -4000.f;
		for (int32 Index = 0; Index < StationCount; ++Index)
		{
			FName StationId;
			TestTrue(TEXT("a station places"),
				Rig.Build->PlaceStation(FName(TEXT("AssemblyRobot")),
					FTransform(FRotator::ZeroRotator,
						FVector(0.f, Y, 0.f)), StationId, Reason));
			for (int32 Crew = 0; Crew < 2; ++Crew)
			{
				Rig.Build->InstallStationDrone(StationId, Reason);
			}
			Y += 2000.f;
		}
		// Whatever the line's length, it still ends in a spray booth.
		// Offset in X as well as Y: at seven stations the line has
		// walked far enough down the hall that the booth's own 26 m
		// depth no longer fits beyond its end, and a fixture that ran
		// out of floor would fail for a reason unrelated to what it
		// tests. Line order is Y-then-X, so it still sorts last.
		{
			FName BoothId;
			FString BoothReason;
			TestTrue(FString::Printf(TEXT("the booth closes the line: %s"),
				*BoothReason),
				Rig.Build->PlaceStation(FName(TEXT("SprayBooth")),
					FTransform(FRotator::ZeroRotator,
						FVector(3000.f, Y - 2000.f, 0.f)), BoothId,
					BoothReason));
			for (int32 Crew = 0; Crew < 2; ++Crew)
			{
				FString CrewReason;
				Rig.Build->InstallStationDrone(BoothId, CrewReason,
					FName(TEXT("Spray")));
			}
		}
		TestTrue(TEXT("the line commissions at this length"),
			Rig.Build->CommissionFactory(Reason));
		TestTrue(TEXT("the coordinator configures"),
			Rig.Coordinator->ConfigureFromAuthorities(Rig.Build,
				Rig.Production, Reason));
		// The fitting stations PLUS the booth: the craft passes through
		// the booth, so it is a route step like any other.
		TestEqual(TEXT("the route is the stations placed and the booth"),
			Rig.Coordinator->GetRoute().Num(), StationCount + 1);

		// The default split covers the whole fixing sequence at any N.
		int32 AllocatedTotal = 0;
		for (const FLBSpacecraftStationRecord& Record :
			Rig.Build->GetStations())
		{
			AllocatedTotal += Record.AllocatedComponents.Num();
		}
		TestEqual(TEXT("commissioning split every component"),
			AllocatedTotal, 6);

		TestTrue(TEXT("contract ready"),
			OfferAndAcceptScoutContract(Rig, TEXT("C-LEN"), 1, Reason));

		double Elapsed = 0.0;
		int32 Guard = 0;
		int32 FurthestIndex = -1;
		ELBSpacecraftStage HighestStage =
			ELBSpacecraftStage::MaterialIntake;
		while (Rig.Production->GetRevenuePence() == 0 && Guard++ < 600)
		{
			TestTrue(TEXT("tick runs"),
				Rig.Coordinator->TickProduction(5.0, Reason));
			Elapsed += 5.0;
			for (const FLBSpacecraftRuntimeAssignment& Assignment :
				Rig.Coordinator->GetAssignments())
			{
				FurthestIndex = FMath::Max(FurthestIndex,
					Assignment.RouteIndex);
				const FLBSpacecraftUnitState* Unit =
					Rig.Production->FindUnit(Assignment.UnitId);
				if (Unit != nullptr)
				{
					TestTrue(TEXT("the stage ladder never slips back"),
						Unit->Stage >= HighestStage);
					HighestStage = FMath::Max(HighestStage, Unit->Stage);
				}
			}
		}
		TestEqual(TEXT("the craft paid at this line length"),
			Rig.Production->GetRevenuePence(), (int64)5000000);
		// The booth is the last route step, so the craft's furthest
		// index is the booth's - one past the last fitting station.
		TestEqual(TEXT("the craft visited every station and the booth"),
			FurthestIndex, StationCount);
		// Shares sum to the recipe's line work at ANY split, so the
		// serial wall time never dips below the four-station line's.
		TestTrue(TEXT("splitting the work never deletes any of it"),
			Elapsed >= ScoutTotalCycleSeconds);
		Rig.World->DestroyWorld(false);
	}
	return true;
}

IMPLEMENT_SIMPLE_AUTOMATION_TEST(FLBSpacecraftCoordinatorConfigTest,
	"LineBoss.Spacecraft.RuntimeCoordinator.RefusesUntilCommissioned",
	EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)

bool FLBSpacecraftCoordinatorConfigTest::RunTest(const FString& Parameters)
{
	(void)Parameters;
	using namespace LBSpacecraftRuntimeCoordinatorTestsPrivate;
	FLBSpacecraftRuntimeRig Rig = MakeSpacecraftRuntimeRig();
	FString Reason;

	// Unconfigured coordinator refuses to tick.
	TestFalse(TEXT("tick refused before configuration"),
		Rig.Coordinator->TickProduction(1.0, Reason));
	TestTrue(TEXT("refusal names configuration"),
		Reason.Contains(TEXT("NOT CONFIGURED")));

	// An uncommissioned factory refuses configuration.
	TestFalse(TEXT("configure refused before commissioning"),
		Rig.Coordinator->ConfigureFromAuthorities(Rig.Build, Rig.Production,
			Reason));
	TestTrue(TEXT("refusal names commissioning"),
		Reason.Contains(TEXT("COMMISSIONED")));

	// Null authorities refuse.
	TestFalse(TEXT("null authorities refuse"),
		Rig.Coordinator->ConfigureFromAuthorities(nullptr, nullptr, Reason));

	TestTrue(TEXT("line places and commissions"),
		PlaceAndCommissionSpacecraftLine(Rig, Reason));
	TestTrue(TEXT("configure succeeds after commissioning"),
		Rig.Coordinator->ConfigureFromAuthorities(Rig.Build, Rig.Production,
			Reason));
	// One repeated station type: the route is the stations placed.
	// Four fitting stations plus the spray booth the line cannot
	// commission without (owner 2026-08-28).
	TestEqual(TEXT("route length is the stations placed and the booth"),
		Rig.Coordinator->GetRoute().Num(), 5);

	Rig.World->DestroyWorld(false);
	return true;
}

IMPLEMENT_SIMPLE_AUTOMATION_TEST(FLBSpacecraftCoordinatorFlowTest,
	"LineBoss.Spacecraft.RuntimeCoordinator.CraftFlowsOnCycleTimesToDispatch",
	EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)

bool FLBSpacecraftCoordinatorFlowTest::RunTest(const FString& Parameters)
{
	(void)Parameters;
	using namespace LBSpacecraftRuntimeCoordinatorTestsPrivate;
	FLBSpacecraftRuntimeRig Rig = MakeSpacecraftRuntimeRig();
	FString Reason;

	TestTrue(TEXT("line ready"),
		PlaceAndCommissionSpacecraftLine(Rig, Reason));
	TestTrue(TEXT("configured"),
		Rig.Coordinator->ConfigureFromAuthorities(Rig.Build, Rig.Production,
			Reason));
	TestTrue(TEXT("contract ready"),
		OfferAndAcceptScoutContract(Rig, TEXT("C-001"), 1, Reason));

	// Tick in 5-second steps; the craft is auto-started and flows the line.
	double Elapsed = 0.0;
	int32 Guard = 0;
	while (Rig.Production->GetRevenuePence() == 0 && Guard++ < 400)
	{
		TestTrue(TEXT("tick runs"),
			Rig.Coordinator->TickProduction(5.0, Reason));
		Elapsed += 5.0;

		// Invariant every tick: no two units share a station.
		TSet<FName> Occupied;
		for (const FLBSpacecraftRuntimeAssignment& Assignment :
			Rig.Coordinator->GetAssignments())
		{
			bool bTaken = false;
			Occupied.Add(Assignment.StationId, &bTaken);
			TestFalse(TEXT("no station holds two units"), bTaken);
		}
	}

	TestEqual(TEXT("contract settled the full price"),
		Rig.Production->GetRevenuePence(), (int64)5000000);
	// One craft, serial line: wall time is at least the summed cycle times.
	TestTrue(TEXT("dispatch took at least the summed cycle times"),
		Elapsed >= ScoutTotalCycleSeconds);
	TestEqual(TEXT("line is empty after dispatch"),
		Rig.Coordinator->GetAssignments().Num(), 0);

	const FLBSpacecraftContract* Contract =
		Rig.Production->FindContract(FName(TEXT("C-001")));
	if (TestNotNull(TEXT("contract exists"), Contract))
	{
		TestEqual(TEXT("contract complete"), Contract->State,
			ELBSpacecraftContractState::Complete);
	}

	Rig.World->DestroyWorld(false);
	return true;
}

IMPLEMENT_SIMPLE_AUTOMATION_TEST(FLBSpacecraftCoordinatorHoldTest,
	"LineBoss.Spacecraft.RuntimeCoordinator.ManualHoverTestHoldsCraft",
	EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)

bool FLBSpacecraftCoordinatorHoldTest::RunTest(const FString& Parameters)
{
	(void)Parameters;
	using namespace LBSpacecraftRuntimeCoordinatorTestsPrivate;
	FLBSpacecraftRuntimeRig Rig = MakeSpacecraftRuntimeRig();
	FString Reason;

	TestTrue(TEXT("line ready"),
		PlaceAndCommissionSpacecraftLine(Rig, Reason));
	TestTrue(TEXT("configured"),
		Rig.Coordinator->ConfigureFromAuthorities(Rig.Build, Rig.Production,
			Reason));
	TestTrue(TEXT("contract ready"),
		OfferAndAcceptScoutContract(Rig, TEXT("C-001"), 1, Reason));

	// Manual hover test: the craft must WAIT at Testing indefinitely.
	Rig.Coordinator->bAutoRunHoverTest = false;
	for (int32 Tick = 0; Tick < 200; ++Tick)
	{
		TestTrue(TEXT("tick runs"),
			Rig.Coordinator->TickProduction(5.0, Reason));
	}
	// 1000 sim seconds >> 440s of cycles: the craft is held at Testing.
	TestEqual(TEXT("craft is still on the line"),
		Rig.Coordinator->GetAssignments().Num(), 1);
	const FLBSpacecraftRuntimeAssignment& Held =
		Rig.Coordinator->GetAssignments()[0];
	const FLBSpacecraftUnitState* Unit =
		Rig.Production->FindUnit(Held.UnitId);
	if (TestNotNull(TEXT("unit exists"), Unit))
	{
		TestEqual(TEXT("craft holds at Testing"), Unit->Stage,
			ELBSpacecraftStage::Testing);
	}
	TestEqual(TEXT("no revenue while holding"),
		Rig.Production->GetRevenuePence(), (int64)0);

	// The manual pass releases it on the next tick.
	TestTrue(TEXT("manual hover pass records"),
		Rig.Production->RecordQualityResult(Held.UnitId, true, Reason));
	TestTrue(TEXT("tick after the pass"),
		Rig.Coordinator->TickProduction(5.0, Reason));
	TestEqual(TEXT("craft dispatched"),
		Rig.Coordinator->GetAssignments().Num(), 0);
	TestEqual(TEXT("revenue settled"),
		Rig.Production->GetRevenuePence(), (int64)5000000);

	Rig.World->DestroyWorld(false);
	return true;
}

IMPLEMENT_SIMPLE_AUTOMATION_TEST(FLBSpacecraftCoordinatorSaveTest,
	"LineBoss.Spacecraft.RuntimeCoordinator.RuntimeValidatesBeforeRestore",
	EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)

bool FLBSpacecraftCoordinatorSaveTest::RunTest(const FString& Parameters)
{
	(void)Parameters;
	using namespace LBSpacecraftRuntimeCoordinatorTestsPrivate;
	FLBSpacecraftRuntimeRig Rig = MakeSpacecraftRuntimeRig();
	FString Reason;

	TestTrue(TEXT("line ready"),
		PlaceAndCommissionSpacecraftLine(Rig, Reason));
	TestTrue(TEXT("configured"),
		Rig.Coordinator->ConfigureFromAuthorities(Rig.Build, Rig.Production,
			Reason));
	TestTrue(TEXT("contract ready"),
		OfferAndAcceptScoutContract(Rig, TEXT("C-001"), 2, Reason));

	// Run until a craft is mid-line.
	for (int32 Tick = 0; Tick < 30; ++Tick)
	{
		TestTrue(TEXT("tick runs"),
			Rig.Coordinator->TickProduction(5.0, Reason));
	}
	TestTrue(TEXT("a craft is on the line"),
		Rig.Coordinator->GetAssignments().Num() > 0);

	const FLBSpacecraftRuntimeState Snapshot =
		Rig.Coordinator->CaptureRuntime();
	TestTrue(TEXT("captured runtime validates"),
		Rig.Coordinator->ValidateRuntime(Snapshot, Reason));
	TestTrue(TEXT("runtime restores"),
		Rig.Coordinator->RestoreRuntime(Snapshot, Reason));

	// Tampers are rejected wholesale.
	FLBSpacecraftRuntimeState WrongRoute = Snapshot;
	WrongRoute.RouteTopologyHash ^= 0xDEADBEEF;
	TestFalse(TEXT("foreign route hash rejected"),
		Rig.Coordinator->RestoreRuntime(WrongRoute, Reason));

	FLBSpacecraftRuntimeState WrongStage = Snapshot;
	WrongStage.Assignments[0].RouteIndex =
		(WrongStage.Assignments[0].RouteIndex + 3) % 7;
	TestFalse(TEXT("route index disagreeing with unit stage rejected"),
		Rig.Coordinator->RestoreRuntime(WrongStage, Reason));

	FLBSpacecraftRuntimeState GhostUnit = Snapshot;
	GhostUnit.Assignments[0].UnitId = FName(TEXT("SCOUT-01-999999"));
	TestFalse(TEXT("assignment for a unit missing from the ledger rejected"),
		Rig.Coordinator->RestoreRuntime(GhostUnit, Reason));

	// The good state survived the rejected tampers.
	TestTrue(TEXT("runtime still validates after rejections"),
		Rig.Coordinator->ValidateRuntime(
			Rig.Coordinator->CaptureRuntime(), Reason));

	Rig.World->DestroyWorld(false);
	return true;
}


IMPLEMENT_SIMPLE_AUTOMATION_TEST(FLBSpacecraftStationInspectionTest,
	"LineBoss.Spacecraft.RuntimeCoordinator.AStationReworksItsOwnBadWork",
	EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)

bool FLBSpacecraftStationInspectionTest::RunTest(const FString& Parameters)
{
	(void)Parameters;
	using namespace LBSpacecraftRuntimeCoordinatorTestsPrivate;
	// INSPECTION BETWEEN STATIONS (owner 2026-08-28, the settled
	// pulse-line model): a station that notices its own bad work
	// reworks it there and then, instead of handing it down the line.
	//
	// The rule has two halves and both matter:
	//   - a station only inspects when SOMEONE COMPETENT IS WATCHING
	//     (at least one drone, and a crew that is not itself the
	//     reason the work is rough),
	//   - and an under-crewed station therefore pays in TIME at the
	//     station, where an uncrewed one pays at final acceptance.
	auto RunLine = [this](const TCHAR* KindId, int32 CrewPerStation,
		double& OutElapsed)
	{
		FLBSpacecraftRuntimeRig Rig = MakeSpacecraftRuntimeRig();
		FString Reason;
		float Y = -2400.f;
		for (int32 Index = 0; Index < 4; ++Index)
		{
			FName StationId;
			Rig.Build->PlaceStation(FName(TEXT("AssemblyRobot")),
				FTransform(FRotator::ZeroRotator, FVector(0.f, Y, 0.f)),
				StationId, Reason);
			for (int32 Crew = 0; Crew < CrewPerStation; ++Crew)
			{
				Rig.Build->InstallStationDrone(StationId, Reason,
					FName(KindId));
			}
			Y += 1600.f;
		}
		// The spray booth closes the line (owner 2026-08-28: required).
		// Crewed the SAME way as the fitting stations, because this
		// test is about how crew size drives rework - a booth on a
		// different footing would add a variable it is not measuring.
		{
			FName BoothId;
			FString BoothReason;
			Rig.Build->PlaceStation(FName(TEXT("SprayBooth")),
				FTransform(FRotator::ZeroRotator, FVector(0.f, Y, 0.f)),
				BoothId, BoothReason);
			for (int32 Crew = 0; Crew < CrewPerStation; ++Crew)
			{
				FString CrewReason;
				Rig.Build->InstallStationDrone(BoothId, CrewReason,
					FName(KindId));
			}
		}
		Rig.Build->CommissionFactory(Reason);
		Rig.Coordinator->ConfigureFromAuthorities(Rig.Build,
			Rig.Production, Reason);
		OfferAndAcceptScoutContract(Rig, TEXT("C-QA"), 1, Reason);
		OutElapsed = 0.0;
		int32 Guard = 0;
		while (Rig.Production->GetRevenuePence() == 0 && Guard++ < 1200)
		{
			Rig.Coordinator->TickProduction(5.0, Reason);
			OutElapsed += 5.0;
		}
		const bool bPaid = Rig.Production->GetRevenuePence() > 0;
		Rig.World->DestroyWorld(false);
		return bPaid;
	};

	// ONE assembly drone a station: competent, but a drone short of
	// nominal - so each station notices its own rushed fitting and
	// stops to redo it.
	double ShortSeconds = 0.0;
	TestTrue(TEXT("the under-crewed line still delivers"),
		RunLine(TEXT("Assembly"), 1, ShortSeconds));
	// THREE assembly drones: nothing to find, nothing to redo.
	double NominalSeconds = 0.0;
	TestTrue(TEXT("the properly crewed line delivers"),
		RunLine(TEXT("Assembly"), 3, NominalSeconds));

	// THE POINT: rushed work is paid for at the station that rushed it.
	TestTrue(TEXT("an under-crewed line pays for its own rework"),
		ShortSeconds > NominalSeconds);

	// The arithmetic underneath, stated directly.
	TestEqual(TEXT("a full rough crew still bodges one fitting"),
		FLBSpacecraftProductionCatalog::DefectPointsForCrewQuality(
			3, 8, 0.6f), 1);
	TestEqual(TEXT("a full fine crew bodges none"),
		FLBSpacecraftProductionCatalog::DefectPointsForCrewQuality(
			3, 8, 1.6f), 0);
	TestEqual(TEXT("an understaffed fine crew still owes its shortfall"),
		FLBSpacecraftProductionCatalog::DefectPointsForCrewQuality(
			0, 8, 1.6f), 1);
	TestEqual(TEXT("a nominal untyped crew is unchanged"),
		FLBSpacecraftProductionCatalog::DefectPointsForCrewQuality(
			2, 8, 1.f),
		FLBSpacecraftProductionCatalog::DefectPointsForCrew(2, 8));
	TestTrue(TEXT("rework time follows the points"),
		FLBSpacecraftProductionCatalog::StationReworkSecondsFor(2)
		> FLBSpacecraftProductionCatalog::StationReworkSecondsFor(1));
	return true;
}

#endif // WITH_DEV_AUTOMATION_TESTS

IMPLEMENT_SIMPLE_AUTOMATION_TEST(FLBSpacecraftQualityRulesTest,
	"LineBoss.Spacecraft.Quality.CrewDecidesWorkmanship",
	EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)

bool FLBSpacecraftQualityRulesTest::RunTest(const FString& Parameters)
{
	(void)Parameters;
	using Catalog = FLBSpacecraftProductionCatalog;

	// Nominal crew is two: that is where the work-bonus curve reaches
	// 1.0x and where a station fits parts cleanly.
	TestEqual(TEXT("an empty station bodges both fits"),
		Catalog::DefectPointsForCrew(0, 8), 2);
	TestEqual(TEXT("a lone drone rushes one"),
		Catalog::DefectPointsForCrew(1, 8), 1);
	TestEqual(TEXT("nominal crew works clean"),
		Catalog::DefectPointsForCrew(2, 8), 0);
	TestEqual(TEXT("a full crew is no cleaner than nominal"),
		Catalog::DefectPointsForCrew(8, 8), 0);
	// A building or a parts machine never touches the craft.
	TestEqual(TEXT("a station with no drone slots never defects"),
		Catalog::DefectPointsForCrew(0, 0), 0);

	TestTrue(TEXT("a clean craft flies"),
		Catalog::DefectsPassHoverTest(0));
	TestTrue(TEXT("one blemish is survivable"),
		Catalog::DefectsPassHoverTest(1));
	TestFalse(TEXT("two defects do not fly clean"),
		Catalog::DefectsPassHoverTest(2));

	// Rework always costs real line time, and more of it for a worse
	// craft.
	TestEqual(TEXT("rework has a floor"),
		Catalog::ReworkSecondsFor(1), 120.f);
	TestTrue(TEXT("a worse craft owes more"),
		Catalog::ReworkSecondsFor(8) > Catalog::ReworkSecondsFor(2));
	return true;
}

IMPLEMENT_SIMPLE_AUTOMATION_TEST(FLBSpacecraftReworkRecoveryTest,
	"LineBoss.Spacecraft.Quality.FailedCraftReworksAndStillDelivers",
	EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)

bool FLBSpacecraftReworkRecoveryTest::RunTest(const FString& Parameters)
{
	(void)Parameters;
	using namespace LBSpacecraftRuntimeCoordinatorTestsPrivate;
	FLBSpacecraftRuntimeRig Rig = MakeSpacecraftRuntimeRig();
	FString Reason;

	// An UNCREWED line: every station fits badly, so the craft reaches
	// the hover test carrying defects and fails it.
	TestTrue(TEXT("uncrewed line ready"),
		PlaceAndCommissionUncrewedLine(Rig, Reason));
	TestTrue(TEXT("configured"),
		Rig.Coordinator->ConfigureFromAuthorities(Rig.Build, Rig.Production,
			Reason));
	TestTrue(TEXT("contract ready"),
		OfferAndAcceptScoutContract(Rig, TEXT("C-RW1"), 1, Reason));

	bool bSawFailure = false;
	bool bSawRework = false;
	int32 Guard = 0;
	while (Rig.Production->GetRevenuePence() == 0 && Guard++ < 2000)
	{
		TestTrue(TEXT("tick runs"),
			Rig.Coordinator->TickProduction(5.0, Reason));
		for (const FLBSpacecraftUnitState& Unit : Rig.Production->GetUnits())
		{
			if (Unit.FailedQualityTests > 0)
			{
				bSawFailure = true;
			}
			if (Unit.ReworkSecondsRemaining > 0.f)
			{
				bSawRework = true;
			}
		}
	}

	// The point of the test: a failed craft is NOT a dead craft. It is
	// reworked on the clock and delivered late and cheap, so the line
	// can never deadlock at the gate.
	TestTrue(TEXT("the hover test actually failed the craft"), bSawFailure);
	TestTrue(TEXT("the craft went through rework"), bSawRework);
	TestTrue(TEXT("the craft still reached dispatch"),
		Rig.Production->GetRevenuePence() > 0);
	// One failed test deducts 10% of the 5,000,000 price.
	TestEqual(TEXT("the defect penalty came off the settlement"),
		Rig.Production->GetRevenuePence(), static_cast<int64>(4500000));
	// Rework cleared the defects rather than papering over them.
	for (const FLBSpacecraftUnitState& Unit : Rig.Production->GetUnits())
	{
		TestEqual(TEXT("a delivered craft carries no open defects"),
			Unit.DefectPoints, 0);
		TestEqual(TEXT("no rework is left owing"),
			Unit.ReworkSecondsRemaining, 0.f);
	}
	return true;
}

IMPLEMENT_SIMPLE_AUTOMATION_TEST(FLBSpacecraftUnbuildableContractTest,
	"LineBoss.Spacecraft.Quality.AnUnbuildableContractNeverBlocksTheLine",
	EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)

bool FLBSpacecraftUnbuildableContractTest::RunTest(const FString& Parameters)
{
	(void)Parameters;
	using namespace LBSpacecraftRuntimeCoordinatorTestsPrivate;
	FLBSpacecraftRuntimeRig Rig = MakeSpacecraftRuntimeRig();
	FString Reason;

	TestTrue(TEXT("Mk1 line ready"),
		PlaceAndCommissionSpacecraftLine(Rig, Reason));
	TestTrue(TEXT("configured"),
		Rig.Coordinator->ConfigureFromAuthorities(Rig.Build, Rig.Production,
			Reason));

	// A CARGO order lands FIRST. The craft-size law rightly refuses it
	// on a Mk1 line - the Scout is the smallest craft and these
	// stations cannot hold a 21 m hull.
	FLBSpacecraftContract Cargo;
	Cargo.ContractId = FName(TEXT("C-CARGO"));
	Cargo.RecipeId = FName(TEXT("CARGO-01"));
	Cargo.Quantity = 1;
	Cargo.PricePerUnitPence = 12000000;
	TestTrue(TEXT("the cargo order is offered"),
		Rig.Production->OfferContract(Cargo, Reason));
	TestTrue(TEXT("and accepted"),
		Rig.Production->AcceptContract(Cargo.ContractId, Reason));

	// A Scout order the line CAN build lands behind it.
	TestTrue(TEXT("a scout order follows"),
		OfferAndAcceptScoutContract(Rig, TEXT("C-SCOUT"), 1, Reason));

	// The line used to take the cargo order, refuse it, and stop -
	// permanently, with no cancel and no expiry to clear it. It must
	// skip past what it cannot build and get on with what it can.
	int32 Guard = 0;
	while (Rig.Production->GetRevenuePence() == 0 && Guard++ < 600)
	{
		TestTrue(TEXT("tick runs"),
			Rig.Coordinator->TickProduction(5.0, Reason));
	}
	TestTrue(TEXT("the buildable scout still got built and paid"),
		Rig.Production->GetRevenuePence() > 0);

	// The law is intact: the cargo order is skipped, NOT built.
	for (const FLBSpacecraftContract& Contract : Rig.Production->GetContracts())
	{
		if (Contract.ContractId == FName(TEXT("C-CARGO")))
		{
			TestEqual(TEXT("the cargo order was never dispatched"),
				Contract.DispatchedCount, 0);
		}
	}
	Rig.World->DestroyWorld(false);
	return true;
}
