#if WITH_DEV_AUTOMATION_TESTS

#include "LBSpacecraftCraftingAuthority.h"
#include "LBSpacecraftDroneFleetAuthority.h"
#include "LBSpacecraftGameMode.h"
#include "LBSpacecraftPowerAuthority.h"

#include "Engine/World.h"
#include "Misc/AutomationTest.h"

namespace LBSpacecraftDroneFleetTestsPrivate
{
	struct FLBSpacecraftDroneRig
	{
		UWorld* World = nullptr;
		ALBSpacecraftBuildAuthority* Build = nullptr;
		ALBSpacecraftCraftingAuthority* Crafting = nullptr;
		ALBSpacecraftPowerAuthority* Power = nullptr;
		ALBSpacecraftResearchAuthority* Research = nullptr;
		ALBSpacecraftInventoryAuthority* Inventory = nullptr;
		ALBSpacecraftDroneFleetAuthority* Fleet = nullptr;
		FName MillId;
		FName PowerHallId;
	};

	FLBSpacecraftDroneRig MakeDroneRig(FAutomationTestBase& Test)
	{
		FLBSpacecraftDroneRig Rig;
		Rig.World = UWorld::CreateWorld(EWorldType::Game, false,
			FName(TEXT("LBSpacecraftDroneWorld")));
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
		Rig.Crafting =
			Rig.World->SpawnActor<ALBSpacecraftCraftingAuthority>();
		Rig.Power = Rig.World->SpawnActor<ALBSpacecraftPowerAuthority>();
		Rig.Research =
			Rig.World->SpawnActor<ALBSpacecraftResearchAuthority>();
		Rig.Inventory =
			Rig.World->SpawnActor<ALBSpacecraftInventoryAuthority>();
		Rig.Fleet =
			Rig.World->SpawnActor<ALBSpacecraftDroneFleetAuthority>();
		FString Reason;
		FName PlantId;
		Test.TestTrue(TEXT("power hall places"),
			// -22000: clear of the 260 m hall (X half 13000, owner
		// 2026-09-01) with the plant's own half-extent to spare.
		ALBSpacecraftGameMode::PlaceStationPowered(*Rig.Build, *Rig.Power, *Rig.Inventory, FName(TEXT("PowerStation")), FTransform(FRotator::ZeroRotator, FVector(-22000.f, 0.f, 0.f)), Rig.PowerHallId, Reason));
		// The generator lives INSIDE its hall (owner
		// 2026-08-26): free placement is refused now.
		Test.TestTrue(TEXT("plant installs in the hall"),
			ALBSpacecraftGameMode::InstallInSlotPowered(*Rig.Build, *Rig.Power, Rig.PowerHallId,
				FName(TEXT("PowerPlant")), PlantId, Reason));
		Test.TestTrue(TEXT("points bank"),
			Rig.Research->AddPoints(10, Reason));
		Test.TestTrue(TEXT("T1 unlocks"),
			Rig.Research->UnlockNode(FName(TEXT("Research.Mfg.T1")),
				Reason));
		// Parts machines live in the sub-assembly hall (owner
		// 2026-08-26), so the rig builds one and installs the mill.
		FName HallId;
		Test.TestTrue(TEXT("sub-assembly hall places"),
			Rig.Build->PlaceStation(FName(TEXT("SubAssemblyHall")),
				FTransform(FRotator::ZeroRotator,
					FVector(22000.f, 0.f, 0.f)), HallId, Reason));
		Test.TestTrue(TEXT("mill installs in the hall"),
			Rig.Build->InstallInSlot(HallId, FName(TEXT("RollingMill")),
				Rig.MillId, Reason));
		return Rig;
	}
}

IMPLEMENT_SIMPLE_AUTOMATION_TEST(FLBSpacecraftDroneFleetPowerTest,
	"LineBoss.Spacecraft.Drones.ChargingDrawsRealGridPower",
	EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)

bool FLBSpacecraftDroneFleetPowerTest::RunTest(const FString& Parameters)
{
	(void)Parameters;
	using namespace LBSpacecraftDroneFleetTestsPrivate;
	FLBSpacecraftDroneRig Rig = MakeDroneRig(*this);
	FString Reason;

	// Owner decision 2026-08-25: production stations host two fitting
	// drones each - REFINED 2026-08-26, power infrastructure runs
	// unmanned ("the plant shouldn't have a drone"), so the mill grows
	// a pair and the power hall grows none.
	Rig.Fleet->SyncFromBuild(Rig.Build, Rig.Power);
	TestEqual(TEXT("the production station grew its pair"),
		Rig.Fleet->GetDroneCount(), 2);
	TestNull(TEXT("the power hall runs unmanned"),
		Rig.Fleet->FindDrone(Rig.PowerHallId, 0));
	TestNotNull(TEXT("drone 0 exists"),
		Rig.Fleet->FindDrone(Rig.MillId, 0));

	// Full drones on an idle station draw nothing.
	const int32 BaselineDraw = Rig.Power->GetTotalDrawKw();
	Rig.Fleet->TickFleet(5.0, Rig.Crafting, Rig.Power);
	TestEqual(TEXT("full idle drones draw no charge power"),
		Rig.Power->GetTotalDrawKw(), BaselineDraw);

	// Drain them via a working flight, then land and watch the grid.
	TestTrue(TEXT("mill selects plate"),
		Rig.Crafting->SelectRecipe(Rig.MillId, FName(TEXT("RollingMill")),
			FName(TEXT("Recipe.PlateStock")), Reason));
	Rig.Fleet->TickFleet(1.0, Rig.Crafting, Rig.Power);
	TestEqual(TEXT("both drones launched"),
		Rig.Fleet->GetFlyingCount(), 2);
	// 180 s battery: after ~160 s of flight the charge nears reserve.
	for (int32 Tick = 0; Tick < 32; ++Tick)
	{
		Rig.Fleet->TickFleet(5.0, Rig.Crafting, Rig.Power);
	}
	TestEqual(TEXT("reserve recalled both drones"),
		Rig.Fleet->GetFlyingCount(), 0);
	Rig.Fleet->TickFleet(1.0, Rig.Crafting, Rig.Power);
	TestEqual(TEXT("two charging docks draw 50 kW from the grid"),
		Rig.Power->GetTotalDrawKw() - BaselineDraw, 50);
	// A full recharge lifts them back off (station still working).
	for (int32 Tick = 0; Tick < 20; ++Tick)
	{
		Rig.Fleet->TickFleet(5.0, Rig.Crafting, Rig.Power);
	}
	TestEqual(TEXT("recharged drones relaunched"),
		Rig.Fleet->GetFlyingCount(), 2);
	TestEqual(TEXT("airborne drones stopped drawing"),
		Rig.Power->GetTotalDrawKw(), BaselineDraw);

	Rig.World->DestroyWorld(false);
	return true;
}

IMPLEMENT_SIMPLE_AUTOMATION_TEST(FLBSpacecraftDroneFleetStallTest,
	"LineBoss.Spacecraft.Drones.NoGridHeadroomMeansNoCharge",
	EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)

bool FLBSpacecraftDroneFleetStallTest::RunTest(const FString& Parameters)
{
	(void)Parameters;
	using namespace LBSpacecraftDroneFleetTestsPrivate;
	FLBSpacecraftDroneRig Rig = MakeDroneRig(*this);
	FString Reason;
	Rig.Fleet->SyncFromBuild(Rig.Build, Rig.Power);

	// Eat ALL remaining headroom so the docks cannot connect.
	TestTrue(TEXT("a big load takes the headroom"),
		Rig.Power->ConnectLoad(FName(TEXT("Load.Hog")),
			Rig.Power->GetHeadroomKw(), Reason));

	// Drain the drones with a working flight, then try to charge.
	TestTrue(TEXT("mill selects plate"),
		Rig.Crafting->SelectRecipe(Rig.MillId, FName(TEXT("RollingMill")),
			FName(TEXT("Recipe.PlateStock")), Reason));
	for (int32 Tick = 0; Tick < 40; ++Tick)
	{
		Rig.Fleet->TickFleet(5.0, Rig.Crafting, Rig.Power);
	}
	TestEqual(TEXT("drones landed at reserve"),
		Rig.Fleet->GetFlyingCount(), 0);
	const FLBSpacecraftDroneState* Drone =
		Rig.Fleet->FindDrone(Rig.MillId, 0);
	const float Stranded = Drone->Charge01;
	for (int32 Tick = 0; Tick < 20; ++Tick)
	{
		Rig.Fleet->TickFleet(5.0, Rig.Crafting, Rig.Power);
	}
	TestEqual(TEXT("no headroom: the charge never rose"),
		Rig.Fleet->FindDrone(Rig.MillId, 0)->Charge01, Stranded);
	TestEqual(TEXT("no phantom loads were connected"),
		Rig.Fleet->GetChargingCount(), 0);

	// Shed the hog: charging resumes on the next ticks.
	TestTrue(TEXT("hog sheds"),
		Rig.Power->DisconnectLoad(FName(TEXT("Load.Hog")), Reason));
	for (int32 Tick = 0; Tick < 4; ++Tick)
	{
		Rig.Fleet->TickFleet(5.0, Rig.Crafting, Rig.Power);
	}
	TestTrue(TEXT("with headroom back, the charge rises"),
		Rig.Fleet->FindDrone(Rig.MillId, 0)->Charge01 > Stranded);

	Rig.World->DestroyWorld(false);
	return true;
}

IMPLEMENT_SIMPLE_AUTOMATION_TEST(FLBSpacecraftDroneFleetSnapshotTest,
	"LineBoss.Spacecraft.Drones.SnapshotValidatesBeforeRestore",
	EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)

bool FLBSpacecraftDroneFleetSnapshotTest::RunTest(const FString& Parameters)
{
	(void)Parameters;
	using namespace LBSpacecraftDroneFleetTestsPrivate;
	FLBSpacecraftDroneRig Rig = MakeDroneRig(*this);
	FString Reason;
	Rig.Fleet->SyncFromBuild(Rig.Build, Rig.Power);

	FLBSpacecraftDroneFleetSnapshot Snapshot =
		Rig.Fleet->CaptureSnapshot();
	TestTrue(TEXT("live snapshot validates"),
		ALBSpacecraftDroneFleetAuthority::ValidateSnapshot(Snapshot,
			Reason));
	FLBSpacecraftDroneFleetSnapshot BadCharge = Snapshot;
	BadCharge.Drones[0].Charge01 = 1.5f;
	TestFalse(TEXT("impossible charge refused"),
		Rig.Fleet->RestoreSnapshot(BadCharge, Rig.Power, Reason));
	FLBSpacecraftDroneFleetSnapshot Duplicate = Snapshot;
	{
		const FLBSpacecraftDroneState First = Duplicate.Drones[0];
		Duplicate.Drones.Add(First);
	}
	TestFalse(TEXT("duplicate drone refused"),
		Rig.Fleet->RestoreSnapshot(Duplicate, Rig.Power, Reason));

	// A drained snapshot restores and immediately charges from the grid.
	Snapshot.Drones[0].Charge01 = 0.4f;
	Snapshot.Drones[1].Charge01 = 0.4f;
	TestTrue(TEXT("drained snapshot restores"),
		Rig.Fleet->RestoreSnapshot(Snapshot, Rig.Power, Reason));
	Rig.Fleet->TickFleet(1.0, Rig.Crafting, Rig.Power);
	TestEqual(TEXT("restored drained drones charge from the grid"),
		Rig.Fleet->GetChargingCount(), 2);

	Rig.World->DestroyWorld(false);
	return true;
}

IMPLEMENT_SIMPLE_AUTOMATION_TEST(FLBSpacecraftDroneFullCrewSaveTest,
	"LineBoss.Spacecraft.Drones.AFullyCrewedStationStillSaves",
	EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)

bool FLBSpacecraftDroneFullCrewSaveTest::RunTest(const FString& Parameters)
{
	(void)Parameters;
	using namespace LBSpacecraftDroneFleetTestsPrivate;
	FLBSpacecraftDroneRig Rig = MakeDroneRig(*this);
	FString Reason;

	// A LINE station holds eight drones (the worker-slot model). The
	// snapshot validator used to cap the drone index at 1, a relic of
	// the days when every station carried exactly two - so buying a
	// third drone anywhere refused the WHOLE save, silently costing
	// the player their progress. Crew one to the brim and prove the
	// snapshot still validates.
	FName LineId;
	TestTrue(TEXT("a line station places"),
		Rig.Build->PlaceStation(FName(TEXT("MaterialProcessor")),
			FTransform(FRotator::ZeroRotator, FVector(4000.f, 4000.f, 0.f)),
			LineId, Reason));
	const FLBSpacecraftStationDefinition* Definition =
		ALBSpacecraftBuildAuthority::FindDefinition(
			FName(TEXT("MaterialProcessor")));
	TestTrue(TEXT("a line station has drone slots"),
		Definition != nullptr && Definition->DroneSlotCount > 2);
	const int32 Slots = Definition != nullptr ? Definition->DroneSlotCount : 0;
	for (int32 Index = 0; Index < Slots; ++Index)
	{
		TestTrue(TEXT("every slot crews"),
			Rig.Build->InstallStationDrone(LineId, Reason));
	}

	Rig.Fleet->SyncFromBuild(Rig.Build, Rig.Power);
	const FLBSpacecraftDroneFleetSnapshot Snapshot =
		Rig.Fleet->CaptureSnapshot();
	TestTrue(TEXT("a fully crewed floor snapshots"),
		Snapshot.Drones.Num() >= Slots);
	TestTrue(TEXT("and that snapshot VALIDATES - the save is not refused"),
		ALBSpacecraftDroneFleetAuthority::ValidateSnapshot(Snapshot,
			Reason));

	// The cap still exists; it is just honest now.
	FLBSpacecraftDroneFleetSnapshot Impossible = Snapshot;
	Impossible.Drones[0].DroneIndex = Slots + 99;
	TestFalse(TEXT("a drone beyond every station's slots is refused"),
		ALBSpacecraftDroneFleetAuthority::ValidateSnapshot(Impossible,
			Reason));

	Rig.World->DestroyWorld(false);
	return true;
}

IMPLEMENT_SIMPLE_AUTOMATION_TEST(FLBSpacecraftDroneAutonomyTest,
	"LineBoss.Spacecraft.Drones.AutonomousSortiesAreBatteryGated",
	EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)

bool FLBSpacecraftDroneAutonomyTest::RunTest(const FString& Parameters)
{
	(void)Parameters;
	using namespace LBSpacecraftDroneFleetTestsPrivate;
	FLBSpacecraftDroneRig Rig = MakeDroneRig(*this);
	FString Reason;
	Rig.Fleet->SyncFromBuild(Rig.Build, Rig.Power);

	// No recipe: everyone stays docked.
	Rig.Fleet->TickFleet(5.0, Rig.Crafting, Rig.Power);
	const FLBSpacecraftDroneState* Drone =
		Rig.Fleet->FindDrone(Rig.MillId, 0);
	TestNotNull(TEXT("drone exists"), Drone);
	if (Drone == nullptr)
	{
		// TestNotNull does not stop the test; dereferencing anyway
		// crashed the whole automation run and cost its report.
		Rig.World->DestroyWorld(false);
		return false;
	}
	TestEqual(TEXT("idle stations keep drones docked"),
		Drone->Mission, ELBSpacecraftDroneMission::Docked);

	// A working station sends the drone on the full sortie cycle.
	TestTrue(TEXT("mill selects plate"),
		ALBSpacecraftGameMode::SelectStationRecipe(*Rig.Build,
			*Rig.Crafting, *Rig.Research, Rig.MillId,
			FName(TEXT("Recipe.PlateStock")), Reason));
	Rig.Fleet->TickFleet(0.5, Rig.Crafting, Rig.Power);
	Drone = Rig.Fleet->FindDrone(Rig.MillId, 0);
	TestEqual(TEXT("launch enters the supply leg"),
		Drone->Mission, ELBSpacecraftDroneMission::ToSupply);
	Rig.Fleet->TickFleet(Rig.Fleet->TravelSeconds + 0.1,
		Rig.Crafting, Rig.Power);
	Drone = Rig.Fleet->FindDrone(Rig.MillId, 0);
	TestEqual(TEXT("supply leg becomes pickup"),
		Drone->Mission, ELBSpacecraftDroneMission::Pickup);
	Rig.Fleet->TickFleet(Rig.Fleet->PickupSeconds + 0.1,
		Rig.Crafting, Rig.Power);
	Rig.Fleet->TickFleet(Rig.Fleet->TravelSeconds + 0.1,
		Rig.Crafting, Rig.Power);
	Drone = Rig.Fleet->FindDrone(Rig.MillId, 0);
	TestEqual(TEXT("the drone reaches fitting"),
		Drone->Mission, ELBSpacecraftDroneMission::Fitting);

	// The battery outranks the job: across a long working stretch the
	// charge NEVER dips meaningfully below reserve - the drone breaks
	// off, recharges and re-sorties on its own (that is the autonomy).
	float LowestCharge = 1.f;
	bool bRedocked = false;
	for (int32 Tick = 0; Tick < 400; ++Tick)
	{
		Rig.Fleet->TickFleet(1.0, Rig.Crafting, Rig.Power);
		Drone = Rig.Fleet->FindDrone(Rig.MillId, 0);
		LowestCharge = FMath::Min(LowestCharge, Drone->Charge01);
		bRedocked |= Drone->Mission == ELBSpacecraftDroneMission::Docked;
	}
	TestTrue(TEXT("the battery floor holds at reserve"),
		LowestCharge >= Rig.Fleet->ReserveFraction - 0.02f);
	TestTrue(TEXT("the drone recharged at least once mid-shift"),
		bRedocked);
	Drone = Rig.Fleet->FindDrone(Rig.MillId, 0);
	TestTrue(TEXT("and it is somewhere in a legitimate cycle"),
		Drone->Mission <= ELBSpacecraftDroneMission::ToDock);

	// Pure alpha helper clamps and picks the right duration.
	FLBSpacecraftDroneState Probe;
	Probe.Mission = ELBSpacecraftDroneMission::Pickup;
	Probe.MissionSeconds = 0.6f;
	TestEqual(TEXT("pickup alpha uses pickup seconds"),
		ALBSpacecraftDroneFleetAuthority::GetMissionAlpha01(
			Probe, 3.f, 1.2f, 6.f), 0.5f);

	Rig.World->DestroyWorld(false);
	return true;
}

#endif // WITH_DEV_AUTOMATION_TESTS
