#if WITH_DEV_AUTOMATION_TESTS

#include "LBSpacecraftPowerAuthority.h"

#include "Engine/World.h"
#include "Misc/AutomationTest.h"

IMPLEMENT_SIMPLE_AUTOMATION_TEST(FLBSpacecraftPowerBudgetTest,
	"LineBoss.Spacecraft.Power.BudgetFailsClosedNeverBrownsOut",
	EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)

bool FLBSpacecraftPowerBudgetTest::RunTest(const FString& Parameters)
{
	(void)Parameters;
	UWorld* World = UWorld::CreateWorld(EWorldType::Game, false,
		FName(TEXT("LBSpacecraftPowerWorld")));
	ALBSpacecraftPowerAuthority* Power =
		World->SpawnActor<ALBSpacecraftPowerAuthority>();
	// These cases test the raw budget arithmetic: the mains
	// feed (its policy has its own coverage) is switched off.
	Power->GridFeedKw = 0;
	FString Reason;

	// A dead grid refuses every load with a named reason.
	TestFalse(TEXT("no supply refuses the first load"),
		Power->ConnectLoad(FName(TEXT("Station.MP.01")), 50, Reason));
	TestTrue(TEXT("refusal names the shortfall"),
		Reason.Contains(TEXT("BUILD POWER")));

	// Registration fails closed.
	TestFalse(TEXT("empty supply id refused"),
		Power->RegisterSupply(NAME_None, 100, Reason));
	TestFalse(TEXT("non-positive capacity refused"),
		Power->RegisterSupply(FName(TEXT("Plant.01")), 0, Reason));
	TestTrue(TEXT("plant registers"),
		Power->RegisterSupply(FName(TEXT("Plant.01")), 100, Reason));
	TestFalse(TEXT("duplicate plant refused"),
		Power->RegisterSupply(FName(TEXT("Plant.01")), 100, Reason));

	// The budget admits exactly what fits and refuses the rest whole.
	TestTrue(TEXT("first load fits"),
		Power->ConnectLoad(FName(TEXT("Station.MP.01")), 50, Reason));
	TestFalse(TEXT("duplicate load refused"),
		Power->ConnectLoad(FName(TEXT("Station.MP.01")), 10, Reason));
	TestFalse(TEXT("over-budget load refused"),
		Power->ConnectLoad(FName(TEXT("Station.HF.01")), 60, Reason));
	TestEqual(TEXT("refused load drew nothing"),
		Power->GetTotalDrawKw(), 50);
	TestTrue(TEXT("an exact-fit load is allowed"),
		Power->ConnectLoad(FName(TEXT("Station.HF.01")), 50, Reason));
	TestEqual(TEXT("headroom is exactly zero"), Power->GetHeadroomKw(), 0);

	// Supply removal is refused while loads depend on it.
	TestFalse(TEXT("removing the only plant is refused under load"),
		Power->RemoveSupply(FName(TEXT("Plant.01")), Reason));
	TestTrue(TEXT("refusal says shed first"),
		Reason.Contains(TEXT("SHED FIRST")));
	TestEqual(TEXT("refused removal changed nothing"),
		Power->GetTotalSupplyKw(), 100);
	TestTrue(TEXT("second plant registers"),
		Power->RegisterSupply(FName(TEXT("Plant.02")), 100, Reason));
	TestTrue(TEXT("now the first plant can retire"),
		Power->RemoveSupply(FName(TEXT("Plant.01")), Reason));
	TestTrue(TEXT("shedding a load frees draw"),
		Power->DisconnectLoad(FName(TEXT("Station.HF.01")), Reason));
	TestEqual(TEXT("draw reflects the shed"), Power->GetTotalDrawKw(), 50);
	TestFalse(TEXT("unknown load reports honestly"),
		Power->DisconnectLoad(FName(TEXT("Station.HF.01")), Reason));

	World->DestroyWorld(false);
	return true;
}

IMPLEMENT_SIMPLE_AUTOMATION_TEST(FLBSpacecraftPowerSnapshotTest,
	"LineBoss.Spacecraft.Power.SnapshotValidatesBeforeRestore",
	EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)

bool FLBSpacecraftPowerSnapshotTest::RunTest(const FString& Parameters)
{
	(void)Parameters;
	UWorld* World = UWorld::CreateWorld(EWorldType::Game, false,
		FName(TEXT("LBSpacecraftPowerSnapshotWorld")));
	ALBSpacecraftPowerAuthority* Power =
		World->SpawnActor<ALBSpacecraftPowerAuthority>();
	// These cases test the raw budget arithmetic: the mains
	// feed (its policy has its own coverage) is switched off.
	Power->GridFeedKw = 0;
	FString Reason;
	TestTrue(TEXT("plant registers"),
		Power->RegisterSupply(FName(TEXT("Plant.01")), 100, Reason));
	TestTrue(TEXT("load connects"),
		Power->ConnectLoad(FName(TEXT("Station.MP.01")), 40, Reason));

	const FLBSpacecraftPowerSnapshot Snapshot = Power->CaptureSnapshot();
	TestTrue(TEXT("live snapshot validates"),
		ALBSpacecraftPowerAuthority::ValidateSnapshot(Snapshot, Reason));
	TestTrue(TEXT("extra load connects"),
		Power->ConnectLoad(FName(TEXT("Station.HF.01")), 30, Reason));
	TestTrue(TEXT("snapshot restores"),
		Power->RestoreSnapshot(Snapshot, Reason));
	TestEqual(TEXT("restore rewound the extra load"),
		Power->GetTotalDrawKw(), 40);
	TestFalse(TEXT("the rewound load is gone"),
		Power->HasLoad(FName(TEXT("Station.HF.01"))));

	// Corrupt snapshots refuse BEFORE mutating.
	FLBSpacecraftPowerSnapshot OverDraw = Snapshot;
	OverDraw.Loads[0].Kilowatts = 999;
	TestFalse(TEXT("draw-exceeds-supply snapshot refused"),
		Power->RestoreSnapshot(OverDraw, Reason));
	FLBSpacecraftPowerSnapshot DupSupply = Snapshot;
	{
		// Copy first: Add(Array[0]) aliases during reallocation.
		const FLBSpacecraftPowerEntry First = DupSupply.Supplies[0];
		DupSupply.Supplies.Add(First);
	}
	TestFalse(TEXT("duplicate-supply snapshot refused"),
		Power->RestoreSnapshot(DupSupply, Reason));
	FLBSpacecraftPowerSnapshot NegativeLoad = Snapshot;
	NegativeLoad.Loads[0].Kilowatts = -5;
	TestFalse(TEXT("negative-load snapshot refused"),
		Power->RestoreSnapshot(NegativeLoad, Reason));
	TestEqual(TEXT("every refused restore left the budget untouched"),
		Power->GetTotalDrawKw(), 40);

	World->DestroyWorld(false);
	return true;
}

#endif // WITH_DEV_AUTOMATION_TESTS
