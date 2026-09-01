// Line track authority: chain laying, node attachment, completeness
// problems, snapshot validation, and track-ordered routing.

#if WITH_DEV_AUTOMATION_TESTS

#include "LBSpacecraftTrackAuthority.h"
#include "LBSpacecraftBuildAuthority.h"
#include "LBSpacecraftGameMode.h"
#include "LBSpacecraftInventoryAuthority.h"
#include "LBSpacecraftProductionAuthority.h"
#include "LBSpacecraftRuntimeCoordinator.h"

#include "Engine/World.h"
#include "Misc/AutomationTest.h"

IMPLEMENT_SIMPLE_AUTOMATION_TEST(FLBSpacecraftTrackRoutePlanTest,
	"LineBoss.Spacecraft.Track.ClickRoutePlansToTheClickedCell",
	EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)

bool FLBSpacecraftTrackRoutePlanTest::RunTest(const FString& Parameters)
{
	(void)Parameters;
	// The open end exits at the origin heading east (+X); every case
	// walks the planned pieces through ComputePieceExit and asserts the
	// LAST piece occupies the clicked cell - the planner's contract.
	const FTransform ExitEast(FRotator::ZeroRotator, FVector::ZeroVector);
	const auto LandingCell = [](const FTransform& Exit,
		const TArray<ELBSpacecraftTrackPiece>& Plan)
	{
		FTransform Walk = Exit;
		FVector Landing = Exit.GetLocation();
		for (const ELBSpacecraftTrackPiece Piece : Plan)
		{
			Landing = Walk.GetLocation();
			Walk = ALBSpacecraftTrackAuthority::ComputePieceExit(
				Walk, Piece);
		}
		return Landing;
	};
	TArray<ELBSpacecraftTrackPiece> Plan;
	FString Reason;
	const TArray<FVector> NoTrack;

	// Dead ahead: three cells forward plans four straights (the last
	// occupies the clicked cell).
	TestTrue(TEXT("a forward click plans"),
		ALBSpacecraftTrackAuthority::PlanRouteToPoint(ExitEast,
			FVector(1200.f, 0.f, 0.f), NoTrack, Plan, Reason));
	TestEqual(TEXT("forward plan is straights to the cell"),
		Plan.Num(), 4);
	TestTrue(TEXT("forward plan lands on the clicked cell"),
		LandingCell(ExitEast, Plan).Equals(
			FVector(1200.f, 0.f, 0.f), 1.f));

	// An L: two cells forward, three right - straights, ONE right
	// turn at the corner, straights down the lateral leg.
	TestTrue(TEXT("an L click plans"),
		ALBSpacecraftTrackAuthority::PlanRouteToPoint(ExitEast,
			FVector(800.f, 1200.f, 0.f), NoTrack, Plan, Reason));
	TestEqual(TEXT("L plan is 2 + turn + 3"), Plan.Num(), 6);
	TestEqual(TEXT("the corner is a right turn"),
		Plan[2], ELBSpacecraftTrackPiece::TurnRight);
	TestTrue(TEXT("L plan lands on the clicked cell"),
		LandingCell(ExitEast, Plan).Equals(
			FVector(800.f, 1200.f, 0.f), 1.f));

	// Leftward lateral picks the left turn.
	TestTrue(TEXT("a left L plans"),
		ALBSpacecraftTrackAuthority::PlanRouteToPoint(ExitEast,
			FVector(0.f, -800.f, 0.f), NoTrack, Plan, Reason));
	TestEqual(TEXT("the immediate corner is a left turn"),
		Plan[0], ELBSpacecraftTrackPiece::TurnLeft);
	TestTrue(TEXT("left plan lands on the clicked cell"),
		LandingCell(ExitEast, Plan).Equals(
			FVector(0.f, -800.f, 0.f), 1.f));

	// Clicking the open end cell itself lays exactly one straight.
	TestTrue(TEXT("clicking the exit cell plans"),
		ALBSpacecraftTrackAuthority::PlanRouteToPoint(ExitEast,
			FVector(0.f, 0.f, 0.f), NoTrack, Plan, Reason));
	TestEqual(TEXT("the exit-cell plan is one straight"), Plan.Num(), 1);

	// Behind the open end routes a U (owner 2026-09-01 "only seems to
	// go up" - half the floor was unreachable under forward-only
	// planning; the A* loops around).
	TestTrue(TEXT("a click behind plans a route"),
		ALBSpacecraftTrackAuthority::PlanRouteToPoint(ExitEast,
			FVector(-800.f, 800.f, 0.f), NoTrack, Plan, Reason));
	TestTrue(TEXT("the behind route lands on the clicked cell"),
		LandingCell(ExitEast, Plan).Equals(
			FVector(-800.f, 800.f, 0.f), 1.f));
	TestTrue(TEXT("a click directly astern also plans"),
		ALBSpacecraftTrackAuthority::PlanRouteToPoint(ExitEast,
			FVector(-800.f, 0.f, 0.f), NoTrack, Plan, Reason));
	TestTrue(TEXT("the astern route lands on the clicked cell"),
		LandingCell(ExitEast, Plan).Equals(
			FVector(-800.f, 0.f, 0.f), 1.f));

	// OBSTACLES: laid track blocks cells and the planner detours
	// around them instead of marching through (the v1 walk died on
	// "WOULD CROSS ITSELF" mid-route).
	{
		TArray<FVector> Blocking;
		Blocking.Add(FVector(400.f, 0.f, 0.f)); // dead ahead, cell (1,0)
		TestTrue(TEXT("a blocked straight line detours"),
			ALBSpacecraftTrackAuthority::PlanRouteToPoint(ExitEast,
				FVector(1200.f, 0.f, 0.f), Blocking, Plan, Reason));
		TestTrue(TEXT("the detour lands on the clicked cell"),
			LandingCell(ExitEast, Plan).Equals(
				FVector(1200.f, 0.f, 0.f), 1.f));
		// Walk the plan: no piece may sit on the blocked cell.
		FTransform Walk = ExitEast;
		bool bTouchedBlock = false;
		for (const ELBSpacecraftTrackPiece Piece : Plan)
		{
			if (Walk.GetLocation().Equals(FVector(400.f, 0.f, 0.f), 1.f))
			{
				bTouchedBlock = true;
			}
			Walk = ALBSpacecraftTrackAuthority::ComputePieceExit(Walk,
				Piece);
		}
		TestFalse(TEXT("the detour avoids the occupied cell"),
			bTouchedBlock);
		// A click ON laid track refuses - there is already line there.
		TestFalse(TEXT("clicking an occupied cell refuses"),
			ALBSpacecraftTrackAuthority::PlanRouteToPoint(ExitEast,
				FVector(400.f, 0.f, 0.f), Blocking, Plan, Reason));
		TestTrue(TEXT("the occupied refusal names the cause"),
			Reason.Contains(TEXT("ALREADY")));
	}

	// A rotated open end plans in ITS frame: heading south (+Y yaw 90),
	// a click further south is dead ahead.
	const FTransform ExitSouth(FRotator(0.f, 90.f, 0.f),
		FVector(2000.f, 1000.f, 0.f));
	TestTrue(TEXT("a rotated exit plans in its own frame"),
		ALBSpacecraftTrackAuthority::PlanRouteToPoint(ExitSouth,
			FVector(2000.f, 1800.f, 0.f), NoTrack, Plan, Reason));
	TestEqual(TEXT("the rotated plan is all straights"), Plan.Num(), 3);
	TestTrue(TEXT("rotated plan lands on the clicked cell"),
		LandingCell(ExitSouth, Plan).Equals(
			FVector(2000.f, 1800.f, 0.f), 1.f));

	// FLOAT DRIFT REGRESSION (2026-09-01): cos(90 deg) is -4.4e-8 in
	// float, so before exit snapping a yaw-90 run drifted X and the
	// first piece after a turn landed at 399.9999 - refused as
	// off-grid. Walk a long yaw-90 run through a turn and demand every
	// exit sits EXACTLY on the 100 cm lattice.
	{
		FTransform Walk(FRotator(0.f, 90.f, 0.f), FVector::ZeroVector);
		for (int32 Step = 0; Step < 20; ++Step)
		{
			Walk = ALBSpacecraftTrackAuthority::ComputePieceExit(Walk,
				ELBSpacecraftTrackPiece::Straight);
		}
		Walk = ALBSpacecraftTrackAuthority::ComputePieceExit(Walk,
			ELBSpacecraftTrackPiece::TurnLeft);
		Walk = ALBSpacecraftTrackAuthority::ComputePieceExit(Walk,
			ELBSpacecraftTrackPiece::Straight);
		const FVector Drifted = Walk.GetLocation();
		TestTrue(TEXT("post-turn exit X sits exactly on the lattice"),
			FMath::IsNearlyZero(
				FMath::Fmod(Drifted.X, 100.f), 0.0001f));
		TestTrue(TEXT("post-turn exit Y sits exactly on the lattice"),
			FMath::IsNearlyZero(
				FMath::Fmod(Drifted.Y, 100.f), 0.0001f));
	}
	return true;
}

IMPLEMENT_SIMPLE_AUTOMATION_TEST(FLBSpacecraftTrackChainTest,
	"LineBoss.Spacecraft.Track.ChainLaysFailClosedAndRoutes",
	EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)

bool FLBSpacecraftTrackChainTest::RunTest(const FString& Parameters)
{
	(void)Parameters;
	// Pure exit maths: a straight advances 400 cm along yaw; turns
	// rotate the build direction a quarter turn.
	const FTransform East(FRotator::ZeroRotator, FVector::ZeroVector);
	const FTransform StraightExit =
		ALBSpacecraftTrackAuthority::ComputePieceExit(East,
			ELBSpacecraftTrackPiece::Straight);
	TestTrue(TEXT("a straight advances one piece east"),
		StraightExit.GetLocation().Equals(FVector(400.f, 0.f, 0.f), 1.f));
	const FTransform RightExit =
		ALBSpacecraftTrackAuthority::ComputePieceExit(East,
			ELBSpacecraftTrackPiece::TurnRight);
	TestTrue(TEXT("a right turn heads south"),
		RightExit.GetLocation().Equals(FVector(0.f, 400.f, 0.f), 1.f));

	UWorld* World = UWorld::CreateWorld(EWorldType::Game, false,
		FName(TEXT("LBSpacecraftTrackWorld")));
	ALBSpacecraftTrackAuthority* Track =
		World->SpawnActor<ALBSpacecraftTrackAuthority>();
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
	FName PieceId;

	// The chain is fail-closed at both ends.
	TestFalse(TEXT("extending an unstarted line refuses"),
		Track->ExtendLine(ELBSpacecraftTrackPiece::Straight, PieceId,
			Reason));
	TestTrue(TEXT("the refusal says start first"),
		Reason.Contains(TEXT("START THE LINE")));
	TestTrue(TEXT("the line starts on the grid"),
		Track->StartLine(FTransform(FRotator(0.f, 90.f, 0.f),
			FVector(0.f, -6000.f, 0.f)), PieceId, Reason));
	TestFalse(TEXT("a second start refuses"),
		Track->StartLine(FTransform::Identity, PieceId, Reason));

	// Straights for the four stations AND the spray booth, then the cap.
	// The booth is a line station: the craft travels the track through
	// it, so it takes a node like everything else on the line.
	TArray<FName> StraightPieces;
	for (int32 Piece = 0; Piece < 5; ++Piece)
	{
		TestTrue(TEXT("a straight lays at the open end"),
			Track->ExtendLine(ELBSpacecraftTrackPiece::Straight,
				PieceId, Reason));
		StraightPieces.Add(PieceId);
	}
	TestTrue(TEXT("an incomplete line names its problem"),
		Track->DescribeProblem().Contains(TEXT("END NOT SET")));
	TestTrue(TEXT("the end caps the line"),
		Track->ExtendLine(ELBSpacecraftTrackPiece::End, PieceId,
			Reason));
	TestTrue(TEXT("the capped line is complete"), Track->IsComplete());
	TestFalse(TEXT("a capped line refuses growth"),
		Track->ExtendLine(ELBSpacecraftTrackPiece::Straight, PieceId,
			Reason));

	// Stations attach as nodes, in build order, straight pieces only.
	// ONE repeated station type: the line is four assembly stations.
	const TCHAR* Classes[] = { TEXT("AssemblyRobot"),
		TEXT("AssemblyRobot"), TEXT("AssemblyRobot"),
		TEXT("AssemblyRobot") };
	TArray<FName> StationIds;
	float Y = -4400.f;
	for (const TCHAR* ClassId : Classes)
	{
		FName StationId;
		TestTrue(TEXT("a line station places"),
			Build->PlaceStation(FName(ClassId),
				FTransform(FRotator::ZeroRotator,
					FVector(2000.f, Y, 0.f)), StationId, Reason));
		StationIds.Add(StationId);
		Y += 2300.f;
	}
	// The booth closes the line (owner 2026-08-28: required).
	{
		FName BoothId;
		TestTrue(TEXT("the spray booth places"),
			Build->PlaceStation(FName(TEXT("SprayBooth")),
				FTransform(FRotator::ZeroRotator,
					FVector(2000.f, Y, 0.f)), BoothId, Reason));
		StationIds.Add(BoothId);
	}
	for (int32 Node = 0; Node < 5; ++Node)
	{
		TestTrue(TEXT("a station attaches to its piece"),
			Track->AttachStationNode(StationIds[Node],
				StraightPieces[Node], Build, Reason));
	}
	TestFalse(TEXT("a station attaches only once"),
		Track->AttachStationNode(StationIds[0], StraightPieces[1],
			Build, Reason));
	TestEqual(TEXT("nodes come back in track order"),
		Track->GetNodeStationsInOrder()[0], StationIds[0]);

	// The coordinator routes from the track, in track order.
	ALBSpacecraftProductionAuthority* Production =
		World->SpawnActor<ALBSpacecraftProductionAuthority>();
	ALBSpacecraftRuntimeCoordinator* Coordinator =
		World->SpawnActor<ALBSpacecraftRuntimeCoordinator>();
	TestTrue(TEXT("the line commissions"),
		Build->CommissionFactory(Reason));
	TestTrue(TEXT("the coordinator routes from the track"),
		Coordinator->ConfigureFromAuthorities(Build, Production, Reason,
			Track));
	TestTrue(TEXT("the route exists"),
		Coordinator->GetRoute().Num() > 0);
	if (Coordinator->GetRoute().Num() > 0)
	{
		TestEqual(TEXT("the first route step is the first node"),
			Coordinator->GetRoute()[0].StationId, StationIds[0]);
	}

	// With ONE repeated station type there is no wrong order of
	// stations - any arrangement of identical stations is a working
	// line. Swapping two nodes therefore REORDERS the route rather
	// than refusing, which is the point of the model: the track says
	// which order the craft visits them in, and that is all it says.
	TestTrue(TEXT("node one detaches"),
		Track->DetachStationNode(StationIds[0], Reason));
	TestTrue(TEXT("node two detaches"),
		Track->DetachStationNode(StationIds[1], Reason));
	TestTrue(TEXT("station two takes piece one"),
		Track->AttachStationNode(StationIds[1], StraightPieces[0],
			Build, Reason));
	TestTrue(TEXT("station one takes piece two"),
		Track->AttachStationNode(StationIds[0], StraightPieces[1],
			Build, Reason));
	TestTrue(TEXT("a swapped line still routes"),
		Coordinator->ConfigureFromAuthorities(Build, Production, Reason,
			Track));
	if (Coordinator->GetRoute().Num() > 1)
	{
		TestEqual(TEXT("the swap reordered the route"),
			Coordinator->GetRoute()[0].StationId, StationIds[1]);
	}
	// What DOES refuse: a line station standing off the track. Every
	// station must be a node, or the craft has a stop with no rail.
	TestTrue(TEXT("node two detaches again"),
		Track->DetachStationNode(StationIds[1], Reason));
	TestFalse(TEXT("a station off the track refuses to route"),
		Coordinator->ConfigureFromAuthorities(Build, Production, Reason,
			Track));
	TestTrue(TEXT("the refusal says to attach it"),
		Reason.Contains(TEXT("ATTACH EVERY LINE STATION")));
	// Piece 1 is occupied by station 0 since the swap; piece 0 is the
	// free one.
	TestTrue(TEXT("node two reattaches"),
		Track->AttachStationNode(StationIds[1], StraightPieces[0],
			Build, Reason));

	// Snapshot: the chain must be continuous to restore.
	FLBSpacecraftTrackSnapshot Snapshot = Track->CaptureSnapshot();
	TestTrue(TEXT("a live track snapshot validates"),
		Track->ValidateSnapshot(Snapshot, Reason));
	FLBSpacecraftTrackSnapshot Broken = Snapshot;
	Broken.Pieces[2].WorldTransform.AddToTranslation(
		FVector(400.f, 0.f, 0.f));
	TestFalse(TEXT("a broken chain refuses to restore"),
		Track->RestoreSnapshot(Broken, Reason));
	TestTrue(TEXT("the refusal names the break"),
		Reason.Contains(TEXT("BREAKS AT")));
	TestTrue(TEXT("the good snapshot restores"),
		Track->RestoreSnapshot(Snapshot, Reason));

	World->DestroyWorld(false);
	return true;
}


IMPLEMENT_SIMPLE_AUTOMATION_TEST(FLBSpacecraftAllocationConsumptionTest,
	"LineBoss.Spacecraft.Track.AllocatedComponentsConsumeOnDeparture",
	EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)

bool FLBSpacecraftAllocationConsumptionTest::RunTest(
	const FString& Parameters)
{
	(void)Parameters;
	UWorld* World = UWorld::CreateWorld(EWorldType::Game, false,
		FName(TEXT("LBSpacecraftAllocConsumeWorld")));
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
	ALBSpacecraftInventoryAuthority* Inventory =
		World->SpawnActor<ALBSpacecraftInventoryAuthority>();
	FString Reason;

	TestTrue(TEXT("line builds"),
		ALBSpacecraftGameMode::SetupCanonicalLine(*Build, Reason));
	// Staff for nominal pace. The first station is the ROUTE's head -
	// one repeated type, so identity comes from position, not class.
	for (const FLBSpacecraftStationRecord& Record : Build->GetStations())
	{
		for (int32 Slot = 0; Slot < 2; ++Slot)
		{
			Build->InstallStationDrone(Record.StationId, Reason);
		}
	}
	TArray<FLBSpacecraftRouteStep> HeadRoute;
	TestTrue(TEXT("the line routes"), Build->BuildRoute(HeadRoute, Reason));
	const FName FirstStation = HeadRoute.Num() > 0
		? HeadRoute[0].StationId : NAME_None;
	// Commissioning split the fixing sequence across the line, so the
	// head station wants its SLICE - the hull first among it. Stock
	// everything in that slice EXCEPT the hull, so the hold this test
	// exercises is precisely the hull shortage.
	TestTrue(TEXT("hull allocates at the first station"),
		Build->SetComponentAllocated(FirstStation,
			FName(TEXT("Component.Hull")), true, Reason));
	// The station eats from ITS OWN stockpile now (owner 2026-08-27,
	// the Production Line model), so that is the shelf this test
	// stocks - and leaving it empty is what makes the unit hold.
	const FName FirstStock(*FString::Printf(TEXT("Store.%s"),
		*FirstStation.ToString()));
	ALBSpacecraftGameMode::SyncStationStores(*Build, *Inventory);
	TestTrue(TEXT("the station has a stockpile"),
		Inventory->HasStore(FirstStock));
	if (const FLBSpacecraftStationRecord* Head =
		Build->FindStation(FirstStation))
	{
		for (const FName& Component : Head->AllocatedComponents)
		{
			if (Component != FName(TEXT("Component.Hull")))
			{
				TestTrue(TEXT("the rest of the head slice stocks"),
					Inventory->Deposit(FirstStock, Component, 1,
						Reason));
			}
		}
	}
	Coordinator->BindInventory(Inventory);
	TestTrue(TEXT("configured"),
		Coordinator->ConfigureFromAuthorities(Build, Production,
			Reason));
	TestTrue(TEXT("contract starts"),
		ALBSpacecraftGameMode::StartScoutContract(*Production, 1,
			Reason));

	// Without the hull in the store, the unit HOLDS at the first
	// station with the shortage named - and never pays twice.
	for (int32 Tick = 0; Tick < 12; ++Tick)
	{
		Coordinator->TickProduction(10.0, Reason);
	}
	TestEqual(TEXT("the unit holds at the first station"),
		Coordinator->GetAssignments()[0].RouteIndex, 0);

	// Deposit the hull: the unit departs and the store is spent.
	TestTrue(TEXT("a hull deposits into the station's stockpile"),
		Inventory->Deposit(FirstStock, FName(TEXT("Component.Hull")), 1,
			Reason));
	for (int32 Tick = 0; Tick < 6; ++Tick)
	{
		Coordinator->TickProduction(10.0, Reason);
	}
	TestTrue(TEXT("the unit departed the allocated station"),
		Coordinator->GetAssignments()[0].RouteIndex > 0);
	TestEqual(TEXT("the hull was consumed"),
		Inventory->GetQuantity(FirstStock,
			FName(TEXT("Component.Hull"))), 0);

	World->DestroyWorld(false);
	return true;
}

#endif // WITH_DEV_AUTOMATION_TESTS
