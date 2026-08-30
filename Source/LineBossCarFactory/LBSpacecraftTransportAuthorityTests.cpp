// Conveyor transport authority: belts connect fail-closed, charge the
// ledger, speed the belted station, vanish with removed stations, and
// snapshot whole-or-nothing.

#if WITH_DEV_AUTOMATION_TESTS

#include "LBSpacecraftGameMode.h"
#include "LBSpacecraftInventoryAuthority.h"
#include "LBSpacecraftPowerAuthority.h"
#include "LBSpacecraftProductionAuthority.h"
#include "LBSpacecraftTransportAuthority.h"
#include "LBSpacecraftProgressionAuthority.h"

#include "Engine/World.h"
#include "Misc/AutomationTest.h"

namespace LBSpacecraftTransportTestsPrivate
{
	struct FLBSpacecraftTransportRig
	{
		UWorld* World = nullptr;
		ALBSpacecraftBuildAuthority* Build = nullptr;
		ALBSpacecraftPowerAuthority* Power = nullptr;
		ALBSpacecraftInventoryAuthority* Inventory = nullptr;
		ALBSpacecraftProductionAuthority* Production = nullptr;
		ALBSpacecraftTransportAuthority* Transport = nullptr;
		FName ProcessorId;
	};

	FLBSpacecraftTransportRig MakeTransportRig(FAutomationTestBase& Test)
	{
		FLBSpacecraftTransportRig Rig;
		Rig.World = UWorld::CreateWorld(EWorldType::Game, false,
			FName(TEXT("LBSpacecraftTransportWorld")));
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
		Rig.Power = Rig.World->SpawnActor<ALBSpacecraftPowerAuthority>();
		Rig.Inventory =
			Rig.World->SpawnActor<ALBSpacecraftInventoryAuthority>();
		Rig.Production =
			Rig.World->SpawnActor<ALBSpacecraftProductionAuthority>();
		Rig.Transport =
			Rig.World->SpawnActor<ALBSpacecraftTransportAuthority>();
		FString Reason;
		Test.TestTrue(TEXT("floor store registers"),
			Rig.Inventory->RegisterStore(FName(TEXT("Store.Floor")), 200,
				Reason));
		FName PlantId;
		FName PowerHallId;
		Test.TestTrue(TEXT("power hall places"),
			ALBSpacecraftGameMode::PlaceStationPowered(*Rig.Build, *Rig.Power, *Rig.Inventory, FName(TEXT("PowerStation")), FTransform(FRotator::ZeroRotator, FVector(-16000.f, 0.f, 0.f)), PowerHallId, Reason));
		// The generator lives INSIDE its hall (owner
		// 2026-08-26): free placement is refused now.
		Test.TestTrue(TEXT("plant installs in the hall"),
			ALBSpacecraftGameMode::InstallInSlotPowered(*Rig.Build, *Rig.Power, PowerHallId,
				FName(TEXT("PowerPlant")), PlantId, Reason));
		Test.TestTrue(TEXT("processor places"),
			ALBSpacecraftGameMode::PlaceStationPowered(*Rig.Build,
				*Rig.Power, *Rig.Inventory,
				FName(TEXT("MaterialProcessor")),
				FTransform(FRotator::ZeroRotator,
					FVector(4000.f, 2000.f, 0.f)), Rig.ProcessorId,
				Reason));
		return Rig;
	}
}

IMPLEMENT_SIMPLE_AUTOMATION_TEST(FLBSpacecraftTransportBeltTest,
	"LineBoss.Spacecraft.Transport.BeltsConnectFailClosedAndCharge",
	EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)

bool FLBSpacecraftTransportBeltTest::RunTest(const FString& Parameters)
{
	(void)Parameters;
	using namespace LBSpacecraftTransportTestsPrivate;
	FLBSpacecraftTransportRig Rig = MakeTransportRig(*this);
	FString Reason;
	FName RouteId;

	// Pure path maths: two-leg grid route, snapped, at least two points.
	const TArray<FVector> Path =
		ALBSpacecraftTransportAuthority::ComputeBeltPathCm(
			FVector(4000.f, 2000.f, 0.f), FVector(-9900.f, 0.f, 0.f));
	TestTrue(TEXT("path has a corner"), Path.Num() == 3);
	// GUARDED. TestTrue does not abort, so the indexing below used to
	// run even when the path came back short - and an out-of-range
	// index is a hard assertion that takes down the WHOLE SUITE rather
	// than failing this one test. A test must fail, not crash.
	if (Path.Num() < 3)
	{
		AddError(FString::Printf(
			TEXT("belt path came back with %d points, expected 3"),
			Path.Num()));
		return false;
	}
	TestTrue(TEXT("path is grid snapped"),
		FMath::IsNearlyZero(FMath::Fmod(Path[1].X, 100.f))
			&& FMath::IsNearlyZero(FMath::Fmod(Path[1].Y, 100.f)));

	// Unknown station and unknown store refuse in plain words.
	TestFalse(TEXT("unknown station refused"),
		Rig.Transport->ConnectSupplyBelt(*Rig.Build, *Rig.Inventory,
			Rig.Production, FName(TEXT("Nope-001")),
			FName(TEXT("Store.Floor")), RouteId, Reason));
	TestTrue(TEXT("refusal names the station"),
		Reason.Contains(TEXT("UNKNOWN STATION")));
	TestFalse(TEXT("unknown store refused"),
		Rig.Transport->ConnectSupplyBelt(*Rig.Build, *Rig.Inventory,
			Rig.Production, Rig.ProcessorId, FName(TEXT("Store.Nope")),
			RouteId, Reason));
	TestTrue(TEXT("refusal names the store"),
		Reason.Contains(TEXT("UNKNOWN STORE")));

	// The unlock gate lives in the authority: zero deliveries means a
	// plain-words refusal naming the ladder.
	{
		ALBSpacecraftProgressionAuthority* Gate =
			Rig.World->SpawnActor<ALBSpacecraftProgressionAuthority>();
		TestFalse(TEXT("locked belts refuse in the authority"),
			Rig.Transport->ConnectSupplyBelt(*Rig.Build, *Rig.Inventory,
				Rig.Production, Rig.ProcessorId,
				FName(TEXT("Store.Floor")), RouteId, Reason, Gate));
		TestTrue(TEXT("the refusal names the unlock"),
			Reason.Contains(TEXT("UNLOCKS AFTER DELIVERY")));
	}

	// A real connection charges the ledger by distance.
	const int64 CashBefore = Rig.Production->GetCashPence();
	TestTrue(TEXT("belt connects"),
		Rig.Transport->ConnectSupplyBelt(*Rig.Build, *Rig.Inventory,
			Rig.Production, Rig.ProcessorId, FName(TEXT("Store.Floor")),
			RouteId, Reason));
	TestTrue(TEXT("belt has an id"), !RouteId.IsNone());
	TestTrue(TEXT("the belt cost cash"),
		Rig.Production->GetCashPence() < CashBefore);
	TestEqual(TEXT("belted station crafts faster"),
		Rig.Transport->GetStationSpeedMultiplier(Rig.ProcessorId),
		Rig.Transport->BeltedSpeedMultiplier);
	TestEqual(TEXT("unbelted station keeps drone pace"),
		Rig.Transport->GetStationSpeedMultiplier(FName(TEXT("Other"))),
		1.f);

	// One supply belt per station.
	TestFalse(TEXT("second belt refused"),
		Rig.Transport->ConnectSupplyBelt(*Rig.Build, *Rig.Inventory,
			Rig.Production, Rig.ProcessorId, FName(TEXT("Store.Floor")),
			RouteId, Reason));
	TestTrue(TEXT("refusal says already belted"),
		Reason.Contains(TEXT("ALREADY HAS A SUPPLY BELT")));

	// Snapshot roundtrip; corrupt snapshots refuse whole.
	const FLBSpacecraftTransportSnapshot Good =
		Rig.Transport->CaptureSnapshot();
	FLBSpacecraftTransportSnapshot Bad = Good;
	Bad.Routes[0].PathPointsCm.Reset();
	TestFalse(TEXT("pathless snapshot refused"),
		Rig.Transport->RestoreSnapshot(Bad, Reason));
	TestEqual(TEXT("refusal left the live route standing"),
		Rig.Transport->GetRoutes().Num(), 1);
	TestTrue(TEXT("good snapshot restores"),
		Rig.Transport->RestoreSnapshot(Good, Reason));

	// A removed station takes its belt along.
	TestTrue(TEXT("processor removes"),
		ALBSpacecraftGameMode::RemoveStationPowered(*Rig.Build,
			*Rig.Power, *Rig.Inventory, nullptr, Rig.ProcessorId,
			Reason));
	Rig.Transport->SyncFromBuild(Rig.Build);
	TestEqual(TEXT("the belt went with the station"),
		Rig.Transport->GetRoutes().Num(), 0);

	Rig.World->DestroyWorld(false);
	return true;
}

#endif // WITH_DEV_AUTOMATION_TESTS
