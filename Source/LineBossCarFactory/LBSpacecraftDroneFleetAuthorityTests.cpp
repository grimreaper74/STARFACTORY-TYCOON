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

IMPLEMENT_SIMPLE_AUTOMATION_TEST(FLBSpacecraftHaulDeliveryLegsTest,
	"LineBoss.Spacecraft.Drones.ADeliveryDropsWhereTheHaulerIsAndBigPartsGoOneAtATime",
	EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)

bool FLBSpacecraftHaulDeliveryLegsTest::RunTest(const FString& Parameters)
{
	(void)Parameters;
	using namespace LBSpacecraftDroneFleetTestsPrivate;
	// Transporter pass (owner 2026-09-02, "the heavy drones are supposed
	// to pick the parts up ... and carry them to the line"). A delivery
	// used to land in the station's store when the hauler was back
	// HOME, so on screen the drone flew out empty and came back loaded.
	// Now it carries OUT, drops on arrival and returns empty - and when
	// the goods sit somewhere other than home, a pickup leg comes first.
	TestEqual(TEXT("an assembled component goes one per trip"),
		ALBSpacecraftDroneFleetAuthority::HaulLoadFor(
			ELBSpacecraftItemCategory::AssembledComponent, 4), 1);
	TestEqual(TEXT("raw stock rides in a crate"),
		ALBSpacecraftDroneFleetAuthority::HaulLoadFor(
			ELBSpacecraftItemCategory::Raw, 4), 4);
	TestEqual(TEXT("sub-parts ride in a crate too"),
		ALBSpacecraftDroneFleetAuthority::HaulLoadFor(
			ELBSpacecraftItemCategory::SubPart, 4), 4);
	{
		FLBSpacecraftHaulState Probe;
		Probe.Job = ELBSpacecraftHaulJob::DeliverInput;
		Probe.CarryCount = 1;
		Probe.Phase = ELBSpacecraftHaulPhase::ToMachine;
		TestTrue(TEXT("a delivery is loaded on the way out"),
			ALBSpacecraftDroneFleetAuthority::HaulIsLoaded(Probe));
		Probe.Phase = ELBSpacecraftHaulPhase::ToStore;
		TestFalse(TEXT("and empty on the way home"),
			ALBSpacecraftDroneFleetAuthority::HaulIsLoaded(Probe));
		Probe.Job = ELBSpacecraftHaulJob::CollectOutput;
		TestTrue(TEXT("a collection is loaded on the way home"),
			ALBSpacecraftDroneFleetAuthority::HaulIsLoaded(Probe));
		Probe.Phase = ELBSpacecraftHaulPhase::ToMachine;
		TestFalse(TEXT("and empty on the way out"),
			ALBSpacecraftDroneFleetAuthority::HaulIsLoaded(Probe));
	}

	FLBSpacecraftDroneRig Rig = MakeDroneRig(*this);
	FString Reason;
	FName RackId;
	TestTrue(TEXT("rack places"),
		Rig.Build->PlaceStation(FName(TEXT("StorageRack")),
			FTransform(FRotator::ZeroRotator,
				FVector(-4000.f, 0.f, 0.f)), RackId, Reason));
	// ONE hauler, the rack's, so the legs under test are unambiguous:
	// the dock placed below never gets its own hauler because the
	// fleet is not re-synced after it.
	Rig.Fleet->SyncFromBuild(Rig.Build, Rig.Power);
	TestEqual(TEXT("one hauler per rack"), Rig.Fleet->GetHauls().Num(), 1);
	FName DockId;
	TestTrue(TEXT("dock places"),
		Rig.Build->PlaceStation(FName(TEXT("DeliveryDock")),
			FTransform(FRotator::ZeroRotator,
				FVector(-4000.f, 3000.f, 0.f)), DockId, Reason));
	ALBSpacecraftGameMode::SyncStationStores(*Rig.Build, *Rig.Inventory,
		Rig.Crafting);
	const FName RackStore(*FString::Printf(TEXT("Store.%s"),
		*RackId.ToString()));
	const FName DockStore(*FString::Printf(TEXT("Store.%s"),
		*DockId.ToString()));
	const FName MillShelf(*FString::Printf(TEXT("Store.%s"),
		*Rig.MillId.ToString()));
	const FName Steel(TEXT("Proc.Steel"));
	TestTrue(TEXT("mill selects plate"),
		ALBSpacecraftGameMode::SelectStationRecipe(*Rig.Build,
			*Rig.Crafting, *Rig.Research, Rig.MillId,
			FName(TEXT("Recipe.PlateStock")), Reason));
	TestTrue(TEXT("a standing order opens"),
		Rig.Crafting->AddOrder(Rig.MillId, 99, Reason));

	// SCENARIO A - goods at HOME: out loaded, drop on arrival, home empty.
	TestTrue(TEXT("steel lands in the rack"),
		Rig.Inventory->Deposit(RackStore, Steel, 8, Reason));
	Rig.Fleet->TickHauls(0.1, Rig.Crafting, Rig.Inventory, Rig.Build,
		Rig.Power);
	const FLBSpacecraftHaulState* Haul = &Rig.Fleet->GetHauls()[0];
	TestEqual(TEXT("the hauler plans a delivery to the mill"),
		Haul->MachineStationId, Rig.MillId);
	TestEqual(TEXT("from its own rack"), Haul->SourceStationId, RackId);
	TestEqual(TEXT("with no pickup leg when the goods are home"),
		Haul->Phase, ELBSpacecraftHaulPhase::ToMachine);
	const int32 Carried = Haul->CarryCount;
	TestTrue(TEXT("it carries something"), Carried >= 1);
	TestTrue(TEXT("and the hook is loaded on the way out"),
		ALBSpacecraftDroneFleetAuthority::HaulIsLoaded(*Haul));
	TestEqual(TEXT("nothing has landed yet"),
		Rig.Inventory->GetQuantity(MillShelf, Steel), 0);
	Rig.Fleet->TickHauls(Rig.Fleet->HaulTravelSeconds + 0.1, Rig.Crafting,
		Rig.Inventory, Rig.Build, Rig.Power);
	Haul = &Rig.Fleet->GetHauls()[0];
	TestEqual(TEXT("the steel is on the mill's shelf ON ARRIVAL"),
		Rig.Inventory->GetQuantity(MillShelf, Steel), Carried);
	TestEqual(TEXT("the hauler heads home"),
		Haul->Phase, ELBSpacecraftHaulPhase::ToStore);
	TestEqual(TEXT("empty"), Haul->CarryCount, 0);
	TestFalse(TEXT("hook empty on the way home"),
		ALBSpacecraftDroneFleetAuthority::HaulIsLoaded(*Haul));
	Rig.Fleet->TickHauls(Rig.Fleet->HaulTravelSeconds + 0.1, Rig.Crafting,
		Rig.Inventory, Rig.Build, Rig.Power);
	TestEqual(TEXT("and is home"),
		Rig.Fleet->GetHauls()[0].Phase, ELBSpacecraftHaulPhase::Idle);

	// SCENARIO B - goods at the DOCK: a pickup leg first, then the same.
	// The mill eats its shelf so it wants steel again; the rack is
	// empty, the dock is not.
	{
		int32 Drained = 0;
		Rig.Inventory->Withdraw(RackStore, Steel,
			Rig.Inventory->GetQuantity(RackStore, Steel), Reason);
		while (Rig.Crafting->ExecuteCraftCycle(Rig.MillId, *Rig.Inventory,
			MillShelf, MillShelf, Reason))
		{
			Rig.Crafting->TransferBufferToStore(Rig.MillId, *Rig.Inventory,
				DockStore, 99, Drained, Reason);
		}
		Rig.Inventory->Withdraw(MillShelf, Steel,
			Rig.Inventory->GetQuantity(MillShelf, Steel), Reason);
	}
	TestEqual(TEXT("the shelf is bare again"),
		Rig.Inventory->GetQuantity(MillShelf, Steel), 0);
	TestTrue(TEXT("steel lands at the dock"),
		Rig.Inventory->Deposit(DockStore, Steel, 8, Reason));
	Rig.Fleet->TickHauls(0.1, Rig.Crafting, Rig.Inventory, Rig.Build,
		Rig.Power);
	Haul = &Rig.Fleet->GetHauls()[0];
	TestEqual(TEXT("the goods are drawn from the dock"),
		Haul->SourceStationId, DockId);
	TestEqual(TEXT("so a pickup leg comes first"),
		Haul->Phase, ELBSpacecraftHaulPhase::ToSource);
	TestFalse(TEXT("flown empty"),
		ALBSpacecraftDroneFleetAuthority::HaulIsLoaded(*Haul));
	Rig.Fleet->TickHauls(Rig.Fleet->HaulTravelSeconds + 0.1, Rig.Crafting,
		Rig.Inventory, Rig.Build, Rig.Power);
	Haul = &Rig.Fleet->GetHauls()[0];
	TestEqual(TEXT("then the loaded leg to the mill"),
		Haul->Phase, ELBSpacecraftHaulPhase::ToMachine);
	TestTrue(TEXT("loaded"),
		ALBSpacecraftDroneFleetAuthority::HaulIsLoaded(*Haul));
	const int32 CarriedB = Haul->CarryCount;
	Rig.Fleet->TickHauls(Rig.Fleet->HaulTravelSeconds + 0.1, Rig.Crafting,
		Rig.Inventory, Rig.Build, Rig.Power);
	TestEqual(TEXT("dropped on arrival from the dock's stock"),
		Rig.Inventory->GetQuantity(MillShelf, Steel), CarriedB);
	TestEqual(TEXT("the dock gave it up"),
		Rig.Inventory->GetQuantity(DockStore, Steel), 8 - CarriedB);
	Rig.World->DestroyWorld(false);
	return true;
}

IMPLEMENT_SIMPLE_AUTOMATION_TEST(FLBSpacecraftHaulerChargesTest,
	"LineBoss.Spacecraft.Drones.AHaulerChargesBetweenTripsAndKeepsHauling",
	EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)

bool FLBSpacecraftHaulerChargesTest::RunTest(const FString& Parameters)
{
	(void)Parameters;
	using namespace LBSpacecraftDroneFleetTestsPrivate;
	// Owner 2026-09-02: "ours will go to their dock and charge". The
	// hauler has the crews' battery: it never abandons a run, sits out
	// from the reserve until fit to launch, draws the grid while it
	// charges, and hauls again afterwards. Constant traffic is a fleet
	// size question, not a tireless drone.
	FLBSpacecraftDroneRig Rig = MakeDroneRig(*this);
	FString Reason;
	FName RackId;
	TestTrue(TEXT("rack places"),
		Rig.Build->PlaceStation(FName(TEXT("StorageRack")),
			FTransform(FRotator::ZeroRotator,
				FVector(-4000.f, 0.f, 0.f)), RackId, Reason));
	Rig.Fleet->SyncFromBuild(Rig.Build, Rig.Power);
	ALBSpacecraftGameMode::SyncStationStores(*Rig.Build, *Rig.Inventory,
		Rig.Crafting);
	const FName RackStore(*FString::Printf(TEXT("Store.%s"),
		*RackId.ToString()));
	const FName MillShelf(*FString::Printf(TEXT("Store.%s"),
		*Rig.MillId.ToString()));
	const FName Steel(TEXT("Proc.Steel"));
	TestTrue(TEXT("mill selects plate"),
		ALBSpacecraftGameMode::SelectStationRecipe(*Rig.Build,
			*Rig.Crafting, *Rig.Research, Rig.MillId,
			FName(TEXT("Recipe.PlateStock")), Reason));
	TestTrue(TEXT("a standing order opens"),
		Rig.Crafting->AddOrder(Rig.MillId, 99, Reason));
	// Endless demand: the mill eats whatever lands and its plate is
	// cleared away, the rack never runs dry.
	float LowestCharge = 1.f;
	bool bChargedOnce = false;
	int32 DeliveriesBeforeCharge = 0;
	int32 DeliveriesAfterCharge = 0;
	int32 LastShelf = 0;
	for (int32 Tick = 0; Tick < 900; ++Tick)
	{
		if (Rig.Inventory->GetQuantity(RackStore, Steel) < 8)
		{
			Rig.Inventory->Deposit(RackStore, Steel, 8, Reason);
		}
		int32 Drained = 0;
		while (Rig.Crafting->ExecuteCraftCycle(Rig.MillId, *Rig.Inventory,
			MillShelf, MillShelf, Reason))
		{
			Rig.Crafting->TransferBufferToStore(Rig.MillId, *Rig.Inventory,
				RackStore, 99, Drained, Reason);
		}
		Rig.Fleet->TickHauls(1.0, Rig.Crafting, Rig.Inventory, Rig.Build,
			Rig.Power);
		const FLBSpacecraftHaulState& Haul = Rig.Fleet->GetHauls()[0];
		LowestCharge = FMath::Min(LowestCharge, Haul.Charge01);
		bChargedOnce |= Haul.bCharging;
		const int32 Shelf = Rig.Inventory->GetQuantity(MillShelf, Steel);
		if (Shelf > LastShelf)
		{
			(bChargedOnce ? DeliveriesAfterCharge : DeliveriesBeforeCharge)++;
		}
		LastShelf = Shelf;
	}
	TestTrue(TEXT("the hauler delivered before its first charge"),
		DeliveriesBeforeCharge > 0);
	TestTrue(TEXT("it went onto the pad to charge"), bChargedOnce);
	// A run in progress finishes: the floor is the reserve less one
	// short trip's drain, never a flat battery.
	TestTrue(TEXT("the battery floor holds near the reserve"),
		LowestCharge >= Rig.Fleet->ReserveFraction
			- 3.f * Rig.Fleet->HaulTravelSeconds
				/ Rig.Fleet->FlightSecondsPerCharge - 0.02f);
	TestTrue(TEXT("and it hauled again after charging"),
		DeliveriesAfterCharge > 0);
	const FLBSpacecraftHaulState& Final = Rig.Fleet->GetHauls()[0];
	TestTrue(TEXT("it ends somewhere legitimate"),
		Final.Phase <= ELBSpacecraftHaulPhase::ToSource);
	Rig.World->DestroyWorld(false);
	return true;
}

#endif // WITH_DEV_AUTOMATION_TESTS
