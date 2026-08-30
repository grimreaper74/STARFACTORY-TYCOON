#if WITH_DEV_AUTOMATION_TESTS

#include "LBSpacecraftGameMode.h"
#include "LBSpacecraftWIPPresentationActor.h"
#include "LBSpacecraftTrackAuthority.h"

#include "Engine/World.h"
#include "Misc/AutomationTest.h"

namespace LBSpacecraftVisualCountPrivate
{
	/** Stations that get a MACHINE VISUAL: everything except the site
	 *  buildings, which the shell layer draws (owner 2026-08-28). */
	inline int32 SpacecraftMachineStationCount(
		const ALBSpacecraftBuildAuthority& InBuild)
	{
		int32 Count = 0;
		for (const FLBSpacecraftStationRecord& Record :
			InBuild.GetStations())
		{
			const FLBSpacecraftStationDefinition* Definition =
				ALBSpacecraftBuildAuthority::FindDefinition(
					Record.DefinitionId);
			if (Definition != nullptr && !Definition->bSiteBuilding)
			{
				++Count;
			}
		}
		return Count;
	}
}

IMPLEMENT_SIMPLE_AUTOMATION_TEST(FLBSpacecraftCanonicalLineTest,
	"LineBoss.Spacecraft.GameMode.CanonicalLineRunsToRevenue",
	EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)

bool FLBSpacecraftCanonicalLineTest::RunTest(const FString& Parameters)
{
	(void)Parameters;
	UWorld* World = UWorld::CreateWorld(EWorldType::Game, false,
		FName(TEXT("LBSpacecraftGameModeWorld")));
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
	ALBSpacecraftProductionAuthority* Production =
		World->SpawnActor<ALBSpacecraftProductionAuthority>();
	ALBSpacecraftRuntimeCoordinator* Coordinator =
		World->SpawnActor<ALBSpacecraftRuntimeCoordinator>();
	FString Reason;

	// The dev shortcut goes through the SAME build authority as the player.
	TestTrue(TEXT("canonical line builds and commissions"),
		ALBSpacecraftGameMode::SetupCanonicalLine(*Build, Reason));
	// One repeated station type: the canonical line is four assembly
	// stations, and the route is however many stand.
	TestEqual(TEXT("the canonical line stands FIVE fitting stations, a hall "
			"and the booth - six route stations including the booth, "
			"which is the shape the owner asked for on 2026-08-29"),
		// 7 = the ship factory the line is built inside, its FIVE
		// fitting stations, and the spray booth the line cannot
		// commission without.
		//
		// Was four stations and six records. The owner asked on
		// 2026-08-29 for "6 stations including paint booth", which is
		// five fitting stations plus the booth on the route, and the
		// hall they stand in makes seven records. Six is also where the
		// current craft stops paying: the fixing order is six
		// components, so a seventh fitting station would pass through
		// fitting nothing until the parts catalogue splits finer.
		Build->GetStations().Num(), 7);
	TestTrue(TEXT("coordinator configures"),
		Coordinator->ConfigureFromAuthorities(Build, Production, Reason));
	TestTrue(TEXT("scout contract starts"),
		ALBSpacecraftGameMode::StartScoutContract(*Production, 2, Reason));

	// Run the line; two craft must dispatch and pay.
	int32 Guard = 0;
	while (Production->GetRevenuePence() < 30000000 && Guard++ < 600)
	{
		TestTrue(TEXT("tick runs"),
			Coordinator->TickProduction(5.0, Reason));
	}
	TestEqual(TEXT("both craft paid the contract price"),
		Production->GetRevenuePence(), (int64)30000000);
	TestEqual(TEXT("line empties after the contract completes"),
		Coordinator->GetAssignments().Num(), 0);

	World->DestroyWorld(false);
	return true;
}

IMPLEMENT_SIMPLE_AUTOMATION_TEST(FLBSpacecraftPresenterTest,
	"LineBoss.Spacecraft.Presentation.PresenterMirrorsAuthoritiesOnly",
	EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)

bool FLBSpacecraftPresenterTest::RunTest(const FString& Parameters)
{
	(void)Parameters;
	UWorld* World = UWorld::CreateWorld(EWorldType::Game, false,
		FName(TEXT("LBSpacecraftPresenterWorld")));
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
	ALBSpacecraftProductionAuthority* Production =
		World->SpawnActor<ALBSpacecraftProductionAuthority>();
	ALBSpacecraftRuntimeCoordinator* Coordinator =
		World->SpawnActor<ALBSpacecraftRuntimeCoordinator>();
	ALBSpacecraftWIPPresentationActor* Presenter =
		World->SpawnActor<ALBSpacecraftWIPPresentationActor>();
	Presenter->BindAuthorities(Build, Coordinator, Production);
	FString Reason;

	// An empty factory draws nothing.
	Presenter->Tick(0.1f);
	TestEqual(TEXT("no station visuals before building"),
		Presenter->GetStationVisualCount(), 0);
	TestEqual(TEXT("no unit visuals before building"),
		Presenter->GetUnitVisualCount(), 0);

	TestTrue(TEXT("line builds"),
		ALBSpacecraftGameMode::SetupCanonicalLine(*Build, Reason));
	TestTrue(TEXT("coordinator configures"),
		Coordinator->ConfigureFromAuthorities(Build, Production, Reason));
	TestTrue(TEXT("contract starts"),
		ALBSpacecraftGameMode::StartScoutContract(*Production, 1, Reason));

	// One station visual per record, exactly.
	Presenter->Tick(0.1f);
	TestEqual(TEXT("one visual per placed station"),
		Presenter->GetStationVisualCount(),
		LBSpacecraftVisualCountPrivate::SpacecraftMachineStationCount(*Build));

	// Mid-run: exactly as many unit visuals as runtime assignments.
	for (int32 Tick = 0; Tick < 10; ++Tick)
	{
		TestTrue(TEXT("tick runs"),
			Coordinator->TickProduction(5.0, Reason));
	}
	Presenter->Tick(0.1f);
	TestEqual(TEXT("unit visuals mirror the assignments"),
		Presenter->GetUnitVisualCount(),
		Coordinator->GetAssignments().Num());
	TestTrue(TEXT("a unit is actually in flight"),
		Presenter->GetUnitVisualCount() > 0);

	// Run to completion: dispatched craft disappear from the floor.
	int32 Guard = 0;
	while (Production->GetRevenuePence() == 0 && Guard++ < 400)
	{
		TestTrue(TEXT("tick runs"),
			Coordinator->TickProduction(5.0, Reason));
	}
	Presenter->Tick(0.1f);
	TestEqual(TEXT("dispatched craft leave the presentation"),
		Presenter->GetUnitVisualCount(), 0);
	TestEqual(TEXT("stations remain"),
		Presenter->GetStationVisualCount(),
		LBSpacecraftVisualCountPrivate::SpacecraftMachineStationCount(*Build));

	// Removing a station removes its visual - the presenter never leads.
	const FName Removed = Build->GetStations()[0].StationId;
	TestTrue(TEXT("station removes"),
		Build->RemoveStation(Removed, Reason));
	Presenter->Tick(0.1f);
	TestEqual(TEXT("visual count follows the authority"),
		Presenter->GetStationVisualCount(),
		LBSpacecraftVisualCountPrivate::SpacecraftMachineStationCount(*Build));

	World->DestroyWorld(false);
	return true;
}

IMPLEMENT_SIMPLE_AUTOMATION_TEST(FLBSpacecraftFlightPresentationTest,
	"LineBoss.Spacecraft.Presentation.HoverBobAndDispatchFlyAway",
	EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)

bool FLBSpacecraftFlightPresentationTest::RunTest(const FString& Parameters)
{
	(void)Parameters;
	UWorld* World = UWorld::CreateWorld(EWorldType::Game, false,
		FName(TEXT("LBSpacecraftFlightWorld")));
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
	ALBSpacecraftProductionAuthority* Production =
		World->SpawnActor<ALBSpacecraftProductionAuthority>();
	ALBSpacecraftRuntimeCoordinator* Coordinator =
		World->SpawnActor<ALBSpacecraftRuntimeCoordinator>();
	ALBSpacecraftWIPPresentationActor* Presenter =
		World->SpawnActor<ALBSpacecraftWIPPresentationActor>();
	Presenter->BindAuthorities(Build, Coordinator, Production);
	FString Reason;

	TestTrue(TEXT("line builds"),
		ALBSpacecraftGameMode::SetupCanonicalLine(*Build, Reason));
	// Staff the line at nominal pace (owner 2026-08-26: drones are
	// bought into station slots; an unstaffed line crawls at half
	// speed, which this journey test does not model).
	for (const FLBSpacecraftStationRecord& Record : Build->GetStations())
	{
		// The ship factory BUILDING has no drone slots - the stations
		// inside it do (owner 2026-08-28).
		const FLBSpacecraftStationDefinition* Definition =
			ALBSpacecraftBuildAuthority::FindDefinition(
				Record.DefinitionId);
		if (Definition == nullptr || Definition->DroneSlotCount == 0)
		{
			continue;
		}
		for (int32 Slot = 0; Slot < 2; ++Slot)
		{
			TestTrue(TEXT("a line drone installs"),
				Build->InstallStationDrone(Record.StationId, Reason));
		}
	}
	TestTrue(TEXT("configured"),
		Coordinator->ConfigureFromAuthorities(Build, Production, Reason));
	TestTrue(TEXT("contract starts"),
		ALBSpacecraftGameMode::StartScoutContract(*Production, 1, Reason));

	// Hold at Testing so the hover is observable.
	Coordinator->bAutoRunHoverTest = false;
	FName UnitId = NAME_None;
	for (int32 Tick = 0; Tick < 120 && UnitId.IsNone(); ++Tick)
	{
		TestTrue(TEXT("tick runs"),
			Coordinator->TickProduction(5.0, Reason));
		Presenter->Tick(0.5f);
		for (const FLBSpacecraftRuntimeAssignment& Assignment :
			Coordinator->GetAssignments())
		{
			const FLBSpacecraftUnitState* Unit =
				Production->FindUnit(Assignment.UnitId);
			if (Unit != nullptr
				&& Unit->Stage == ELBSpacecraftStage::Testing)
			{
				UnitId = Assignment.UnitId;
			}
		}
	}
	TestFalse(TEXT("a craft reached the hover test"), UnitId.IsNone());

	// The hovering craft sits WELL above the station block (350 cm) plus the
	// normal parked lift (100 cm): the 600 cm test hover must show.
	Presenter->Tick(0.5f);
	FVector HoverLocation = FVector::ZeroVector;
	TestTrue(TEXT("hovering craft has a visual"),
		Presenter->GetUnitVisualLocation(UnitId, HoverLocation));
	TestTrue(TEXT("craft is visibly hovering"), HoverLocation.Z > 800.f);

	// The bob moves it between frames.
	FVector Later = FVector::ZeroVector;
	Presenter->Tick(0.7f);
	TestTrue(TEXT("hovering craft still has a visual"),
		Presenter->GetUnitVisualLocation(UnitId, Later));
	TestTrue(TEXT("the hover bobs over time"),
		!FMath::IsNearlyEqual(HoverLocation.Z, Later.Z, 0.5f));
	TestEqual(TEXT("the hovering craft burns its belly RCS flames"),
		Presenter->GetUnitFlameCount(UnitId), 7);

	// Pass the hover test; the craft dispatches and FLIES OUT instead of
	// blinking away, then finishes its departure and disappears.
	TestTrue(TEXT("hover pass records"),
		Production->RecordQualityResult(UnitId, true, Reason));
	// The pass applies when the Testing CYCLE completes (60 s) - the craft
	// keeps hovering until the test itself is done, then dispatches.
	for (int32 Tick = 0; Tick < 14; ++Tick)
	{
		TestTrue(TEXT("tick runs"),
			Coordinator->TickProduction(5.0, Reason));
	}
	TestEqual(TEXT("assignment left the line"),
		Coordinator->GetAssignments().Num(), 0);
	Presenter->Tick(0.1f);
	TestEqual(TEXT("no unit visual after dispatch"),
		Presenter->GetUnitVisualCount(), 0);
	TestEqual(TEXT("one departing craft"),
		Presenter->GetDepartingVisualCount(), 1);
	TestEqual(TEXT("the departing craft carries its 7 flames"),
		Presenter->GetDepartingFlameCount(), 7);

	// Thruster mix (owner, 2026-08-25): belly RCS through the chicane,
	// mains spool at throttle-up, belly fades as speed builds.
	float Belly = 0.f;
	float Main = 0.f;
	ALBSpacecraftWIPPresentationActor::ComputeThrusterMix(
		0.5f, 2.2f, 2.6f, Belly, Main);
	TestTrue(TEXT("early chicane: belly only"),
		Belly > 0.99f && Main < 0.01f);
	ALBSpacecraftWIPPresentationActor::ComputeThrusterMix(
		2.1f, 2.2f, 2.6f, Belly, Main);
	TestTrue(TEXT("late chicane: mains spooling"),
		Belly > 0.99f && Main > 0.1f && Main < 0.35f);
	ALBSpacecraftWIPPresentationActor::ComputeThrusterMix(
		4.0f, 2.2f, 2.6f, Belly, Main);
	TestTrue(TEXT("at speed: mains only"),
		Belly < 0.01f && Main > 0.99f);

	// The flight plan (owner, 2026-08-30: "want to see it do it but not
	// the cinematic" - the S-weave was cut, keeping a plain taxi-then-
	// sprint). Pure-maths checks: the taxi slides smoothly and
	// monotonically to the lateral target with no S-curve overshoot;
	// the sprint is quadratic (accelerating) and covers the factory
	// length; the whole flight is deterministic and time-bounded.
	const FVector LateralTargetCm(900.f, 0.f, 0.f);
	const FVector QuarterTaxi =
		ALBSpacecraftWIPPresentationActor::ComputeDepartureOffsetCm(
			0.55f, 2.2f, 900.f, 2.6f, 26000.f, 3500.f,
			LateralTargetCm.X);
	const FVector ThreeQuarterTaxi =
		ALBSpacecraftWIPPresentationActor::ComputeDepartureOffsetCm(
			1.65f, 2.2f, 900.f, 2.6f, 26000.f, 3500.f,
			LateralTargetCm.X);
	TestTrue(TEXT("the taxi is monotonic toward the lateral target"),
		ThreeQuarterTaxi.X > QuarterTaxi.X);
	TestTrue(TEXT("the taxi never overshoots the lateral target"),
		QuarterTaxi.X <= LateralTargetCm.X + 1.f
			&& ThreeQuarterTaxi.X <= LateralTargetCm.X + 1.f);
	const FVector ChicaneEnd =
		ALBSpacecraftWIPPresentationActor::ComputeDepartureOffsetCm(
			2.2f, 2.2f, 900.f, 2.6f, 26000.f, 3500.f,
			LateralTargetCm.X);
	TestTrue(TEXT("the taxi ends exactly on the lateral target"),
		FMath::Abs(ChicaneEnd.X - LateralTargetCm.X) < 1.f);
	const FVector MidSprint =
		ALBSpacecraftWIPPresentationActor::ComputeDepartureOffsetCm(
			3.5f, 2.2f, 900.f, 2.6f, 26000.f, 3500.f);
	const FVector EndSprint =
		ALBSpacecraftWIPPresentationActor::ComputeDepartureOffsetCm(
			4.8f, 2.2f, 900.f, 2.6f, 26000.f, 3500.f);
	TestTrue(TEXT("the sprint accelerates (quadratic, not linear)"),
		(ChicaneEnd.Y - EndSprint.Y)
			> 2.f * (ChicaneEnd.Y - MidSprint.Y));
	TestTrue(TEXT("full pelt covers the factory length and exits"),
		EndSprint.Y < -26000.f);

	for (int32 Tick = 0; Tick < 8; ++Tick)
	{
		Presenter->Tick(1.0f);
	}
	TestEqual(TEXT("departure completes and the craft is gone"),
		Presenter->GetDepartingVisualCount(), 0);

	World->DestroyWorld(false);
	return true;
}

IMPLEMENT_SIMPLE_AUTOMATION_TEST(FLBSpacecraftLineIsLoadableTest,
	"LineBoss.Spacecraft.GameMode.CanonicalLineIsLoadable",
	EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)

bool FLBSpacecraftLineIsLoadableTest::RunTest(const FString& Parameters)
{
	(void)Parameters;
	// EVERY ROUTE STATION NEEDS A TRACK NODE, and nothing checked it.
	//
	// A line whose stations are attached to no track RUNS PERFECTLY
	// WELL - it builds craft, takes contracts, earns money. It fails
	// only when you LOAD it, because restore validates the whole
	// snapshot before mutating and refuses a route with no nodes. The
	// symptom therefore appears nowhere near the cause, and only in a
	// path no test exercised.
	//
	// Which is how it shipped: growing the line from four stations to
	// six overran the demo track's four straights, the track was
	// silently binned, and the game carried on working. The save button
	// written the same afternoon would have produced saves that could
	// never be loaded.
	UWorld* World = UWorld::CreateWorld(EWorldType::Game, false,
		FName(TEXT("LBSpacecraftLoadableWorld")));
	ALBSpacecraftBuildAuthority* Build =
		World->SpawnActor<ALBSpacecraftBuildAuthority>();
	ALBSpacecraftProductionAuthority* Production =
		World->SpawnActor<ALBSpacecraftProductionAuthority>();
	ALBSpacecraftRuntimeCoordinator* Coordinator =
		World->SpawnActor<ALBSpacecraftRuntimeCoordinator>();
	ALBSpacecraftTrackAuthority* Track =
		World->SpawnActor<ALBSpacecraftTrackAuthority>();
	FString Reason;
	{
		FName HallId;
		FString HallReason;
		Build->PlaceStarterHall(HallId, HallReason);
	}
	if (!TestTrue(TEXT("the canonical line builds"),
			ALBSpacecraftGameMode::SetupCanonicalLine(*Build, Reason))
		|| !TestTrue(TEXT("the coordinator configures"),
			Coordinator->ConfigureFromAuthorities(Build, Production,
				Reason)))
	{
		World->DestroyWorld(false);
		return false;
	}

	TArray<FName> RouteStations;
	for (const FLBSpacecraftRouteStep& Step : Coordinator->GetRoute())
	{
		RouteStations.AddUnique(Step.StationId);
	}
	TestTrue(TEXT("the route visits at least one station"),
		RouteStations.Num() > 0);

	// The line must fit the track's node budget, or no amount of laying
	// track could ever attach them all and the save would be
	// permanently unloadable.
	TestTrue(*FString::Printf(
		TEXT("the route's %d stations fit the track's %d-node budget - "
			"a line longer than the track can hold could never be "
			"saved and reloaded"),
		RouteStations.Num(), Track->MaxNodes),
		RouteStations.Num() <= Track->MaxNodes);

	World->DestroyWorld(false);
	return true;
}



IMPLEMENT_SIMPLE_AUTOMATION_TEST(FLBSpacecraftBufferStallAlertTest,
	"LineBoss.Spacecraft.GameMode.AStalledMachineSaysWhyAndHowToFixIt",
	EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)

bool FLBSpacecraftBufferStallAlertTest::RunTest(const FString& Parameters)
{
	(void)Parameters;
	const FName Mill(TEXT("RollingMill-010"));

	// With a rack on the floor a hauler really is coming, so waiting is
	// the truth.
	const FString Waiting =
		ALBSpacecraftGameMode::BuildBufferStallAlert(Mill, true);
	TestTrue(TEXT("the waiting message names the machine"),
		Waiting.Contains(Mill.ToString()));
	TestTrue(TEXT("and says a hauler is coming"),
		Waiting.Contains(TEXT("HAULER")));

	// With NO rack, no hauler will ever come. Telling the player to
	// wait would be a lie, so the message names the cure instead.
	const FString Stopped =
		ALBSpacecraftGameMode::BuildBufferStallAlert(Mill, false);
	TestTrue(TEXT("the stall message names the machine"),
		Stopped.Contains(Mill.ToString()));
	TestTrue(TEXT("it says the machine has STOPPED, not that it waits"),
		Stopped.Contains(TEXT("STOPPED")));
	TestTrue(TEXT("and it names the cure in plain words"),
		Stopped.Contains(TEXT("BUILD A STORAGE RACK")));
	TestFalse(TEXT("it never promises a pickup that cannot happen"),
		Stopped.Contains(TEXT("WAITING FOR A HAULER")));

	// The alert channel ignores repeats - it is raised every tick by a
	// machine that is still stuck.
	UWorld* World = UWorld::CreateWorld(EWorldType::Game, false,
		FName(TEXT("LBSpacecraftAlertWorld")));
	ALBSpacecraftGameMode* GameMode =
		World->SpawnActor<ALBSpacecraftGameMode>();
	TestTrue(TEXT("a new game mode has nothing to complain about"),
		GameMode->GetSimAlert().IsEmpty());
	GameMode->RaiseSimAlert(Stopped);
	TestEqual(TEXT("the complaint is carried"),
		GameMode->GetSimAlert(), Stopped);
	GameMode->RaiseSimAlert(FString());
	TestEqual(TEXT("an empty alert never clears a real one"),
		GameMode->GetSimAlert(), Stopped);

	World->DestroyWorld(false);
	return true;
}

// MOVED TO THE END OF THE FILE. This #endif sat mid-file, which
// left the two tests below it OUTSIDE the automation guard - they
// would be compiled unconditionally, including in a Shipping build
// where IMPLEMENT_SIMPLE_AUTOMATION_TEST has nothing to expand to.
// Latent rather than broken, because this project does not build
// Shipping today.
#endif // WITH_DEV_AUTOMATION_TESTS
