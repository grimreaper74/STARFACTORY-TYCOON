#if WITH_DEV_AUTOMATION_TESTS

#include "LBSpacecraftGameMode.h"
#include "LBSpacecraftSaveGame.h"
#include "LBSpacecraftTrackAuthority.h"
#include "LBSpacecraftTransportAuthority.h"
#include "LBSpacecraftProgressionAuthority.h"

#include "Engine/World.h"
#include "Kismet/GameplayStatics.h"
#include "Misc/AutomationTest.h"

namespace LBSpacecraftSaveGameTestsPrivate
{
	const TCHAR* SpacecraftTestSlot = TEXT("LBSpacecraftAutomationTestSlot");

	struct FLBSpacecraftSaveRig
	{
		UWorld* World = nullptr;
		ALBSpacecraftBuildAuthority* Build = nullptr;
		ALBSpacecraftProductionAuthority* Production = nullptr;
		ALBSpacecraftRuntimeCoordinator* Coordinator = nullptr;
		ALBSpacecraftInventoryAuthority* Inventory = nullptr;
		ALBSpacecraftCraftingAuthority* Crafting = nullptr;
		ALBSpacecraftPowerAuthority* Power = nullptr;
		ALBSpacecraftResearchAuthority* Research = nullptr;
		ALBSpacecraftDroneFleetAuthority* DroneFleet = nullptr;
		ALBSpacecraftReputationAuthority* Reputation = nullptr;
		ALBSpacecraftTransportAuthority* Transport = nullptr;
		ALBSpacecraftProgressionAuthority* Progression = nullptr;
		ALBSpacecraftTrackAuthority* Track = nullptr;

		FLBSpacecraftSaveContext Context() const
		{
			FLBSpacecraftSaveContext Out;
			Out.Build = Build;
			Out.Production = Production;
			Out.Coordinator = Coordinator;
			Out.Inventory = Inventory;
			Out.Crafting = Crafting;
			Out.Power = Power;
			Out.Research = Research;
			Out.DroneFleet = DroneFleet;
			Out.Reputation = Reputation;
			Out.Transport = Transport;
			Out.Progression = Progression;
			Out.Track = Track;
			return Out;
		}
	};

	FLBSpacecraftSaveRig MakeSpacecraftSaveRig()
	{
		FLBSpacecraftSaveRig Rig;
		Rig.World = UWorld::CreateWorld(EWorldType::Game, false,
			FName(TEXT("LBSpacecraftSaveWorld")));
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
		Rig.Inventory =
			Rig.World->SpawnActor<ALBSpacecraftInventoryAuthority>();
		Rig.Crafting =
			Rig.World->SpawnActor<ALBSpacecraftCraftingAuthority>();
		Rig.Power = Rig.World->SpawnActor<ALBSpacecraftPowerAuthority>();
		Rig.Research =
			Rig.World->SpawnActor<ALBSpacecraftResearchAuthority>();
		Rig.DroneFleet =
			Rig.World->SpawnActor<ALBSpacecraftDroneFleetAuthority>();
		Rig.Reputation =
			Rig.World->SpawnActor<ALBSpacecraftReputationAuthority>();
		Rig.Transport =
			Rig.World->SpawnActor<ALBSpacecraftTransportAuthority>();
		Rig.Progression =
			Rig.World->SpawnActor<ALBSpacecraftProgressionAuthority>();
		Rig.Track =
			Rig.World->SpawnActor<ALBSpacecraftTrackAuthority>();
		return Rig;
	}

	bool RunSpacecraftLineToMidFlight(FLBSpacecraftSaveRig& Rig,
		FString& OutReason)
	{
		if (!ALBSpacecraftGameMode::SetupCanonicalLine(*Rig.Build, OutReason)
			|| !Rig.Coordinator->ConfigureFromAuthorities(Rig.Build,
				Rig.Production, OutReason)
			|| !ALBSpacecraftGameMode::StartScoutContract(*Rig.Production, 2,
				OutReason))
		{
			return false;
		}
		for (int32 Tick = 0; Tick < 30; ++Tick)
		{
			if (!Rig.Coordinator->TickProduction(5.0, OutReason))
			{
				return false;
			}
		}
		return Rig.Coordinator->GetAssignments().Num() > 0;
	}
}

IMPLEMENT_SIMPLE_AUTOMATION_TEST(FLBSpacecraftSaveRoundTripTest,
	"LineBoss.Spacecraft.SaveLoad.MidFlightRoundTripRestoresExactly",
	EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)

bool FLBSpacecraftSaveRoundTripTest::RunTest(const FString& Parameters)
{
	(void)Parameters;
	using namespace LBSpacecraftSaveGameTestsPrivate;
	FLBSpacecraftSaveRig Rig = MakeSpacecraftSaveRig();
	FString Reason;

	TestTrue(TEXT("line runs to mid-flight"),
		RunSpacecraftLineToMidFlight(Rig, Reason));

	// Remember the moment of the save.
	const double SavedSim = Rig.Production->GetSimSeconds();
	const int32 SavedUnits = Rig.Production->GetUnits().Num();
	const int32 SavedAssignments = Rig.Coordinator->GetAssignments().Num();
	const FName SavedFirstUnit = Rig.Coordinator->GetAssignments()[0].UnitId;
	const ELBSpacecraftStage SavedStage =
		Rig.Production->FindUnit(SavedFirstUnit)->Stage;

	TestTrue(TEXT("save succeeds"), FLBSpacecraftSavePipeline::SaveToSlot(
		Rig.Context(), SpacecraftTestSlot, Reason));

	// Let the live state diverge well past the saved moment.
	for (int32 Tick = 0; Tick < 60; ++Tick)
	{
		TestTrue(TEXT("tick runs"),
			Rig.Coordinator->TickProduction(5.0, Reason));
	}
	TestTrue(TEXT("state diverged"),
		Rig.Production->GetSimSeconds() > SavedSim + 1.0);

	// Load rolls everything back to the saved moment, coherently.
	TestTrue(TEXT("load succeeds"), FLBSpacecraftSavePipeline::LoadFromSlot(
		Rig.Context(), SpacecraftTestSlot, Reason));
	TestEqual(TEXT("sim clock restored"),
		Rig.Production->GetSimSeconds(), SavedSim);
	TestEqual(TEXT("unit count restored"),
		Rig.Production->GetUnits().Num(), SavedUnits);
	TestEqual(TEXT("assignments restored"),
		Rig.Coordinator->GetAssignments().Num(), SavedAssignments);
	TestEqual(TEXT("first unit stage restored"),
		Rig.Production->FindUnit(SavedFirstUnit)->Stage, SavedStage);
	TestTrue(TEXT("restored runtime validates"),
		Rig.Coordinator->ValidateRuntime(
			Rig.Coordinator->CaptureRuntime(), Reason));

	// The loaded factory keeps producing to completion - it is alive.
	int32 Guard = 0;
	while (Rig.Production->GetRevenuePence() < 30000000 && Guard++ < 600)
	{
		TestTrue(TEXT("post-load tick runs"),
			Rig.Coordinator->TickProduction(5.0, Reason));
	}
	TestEqual(TEXT("loaded factory completes the contract"),
		Rig.Production->GetRevenuePence(), (int64)30000000);

	UGameplayStatics::DeleteGameInSlot(SpacecraftTestSlot, 0);
	Rig.World->DestroyWorld(false);
	return true;
}

IMPLEMENT_SIMPLE_AUTOMATION_TEST(FLBSpacecraftSaveFailClosedTest,
	"LineBoss.Spacecraft.SaveLoad.MissingAndForeignSlotsFailClosed",
	EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)

bool FLBSpacecraftSaveFailClosedTest::RunTest(const FString& Parameters)
{
	(void)Parameters;
	using namespace LBSpacecraftSaveGameTestsPrivate;
	FLBSpacecraftSaveRig Rig = MakeSpacecraftSaveRig();
	FString Reason;

	// Loading a missing slot is refused with the slot named.
	TestFalse(TEXT("missing slot refuses"),
		FLBSpacecraftSavePipeline::LoadFromSlot(Rig.Context(),
			TEXT("LBSpacecraftNoSuchSlot"), Reason));
	TestTrue(TEXT("refusal names the slot"),
		Reason.Contains(TEXT("LBSpacecraftNoSuchSlot")));

	// A failed load must leave a running factory untouched (rollback).
	TestTrue(TEXT("line runs to mid-flight"),
		RunSpacecraftLineToMidFlight(Rig, Reason));
	const double LiveSim = Rig.Production->GetSimSeconds();
	const int32 LiveAssignments = Rig.Coordinator->GetAssignments().Num();
	TestFalse(TEXT("missing slot still refuses mid-flight"),
		FLBSpacecraftSavePipeline::LoadFromSlot(Rig.Context(),
			TEXT("LBSpacecraftNoSuchSlot"), Reason));
	TestEqual(TEXT("sim clock untouched by the refused load"),
		Rig.Production->GetSimSeconds(), LiveSim);
	TestEqual(TEXT("assignments untouched by the refused load"),
		Rig.Coordinator->GetAssignments().Num(), LiveAssignments);

	// An empty slot name refuses to save.
	TestFalse(TEXT("empty slot name refuses to save"),
		FLBSpacecraftSavePipeline::SaveToSlot(Rig.Context(), FString(),
			Reason));

	Rig.World->DestroyWorld(false);
	return true;
}

#endif // WITH_DEV_AUTOMATION_TESTS

IMPLEMENT_SIMPLE_AUTOMATION_TEST(FLBSpacecraftNewStateSurvivesSaveTest,
	"LineBoss.Spacecraft.SaveLoad.TwoDaysOfNewStateSurvivesARoundTrip",
	EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)

bool FLBSpacecraftNewStateSurvivesSaveTest::RunTest(const FString& Parameters)
{
	(void)Parameters;
	using namespace LBSpacecraftSaveGameTestsPrivate;
	FLBSpacecraftSaveRig Rig = MakeSpacecraftSaveRig();
	FString Reason;

	// Everything the last two days added to a save, set to values that
	// are obviously not the defaults - workmanship, rework, finished
	// stock, who ordered it and in what colours, the deadline, and the
	// per-delivery credit both progression authorities keep. None of it
	// had a single line of save coverage.
	FLBSpacecraftProductionLedgerState Ledger = Rig.Production->CaptureLedger();
	FLBSpacecraftContract Contract;
	Contract.ContractId = FName(TEXT("C-ROUNDTRIP"));
	Contract.RecipeId = FName(TEXT("SCOUT-01"));
	Contract.Quantity = 3;
	Contract.DispatchedCount = 1;
	Contract.PricePerUnitPence = 15750000;
	Contract.DeadlineSimSeconds = 4321.0;
	Contract.CustomerId = FName(TEXT("Customer.Freight"));
	Contract.LiveryColour = FLinearColor(0.72f, 0.36f, 0.06f);
	Contract.State = ELBSpacecraftContractState::Accepted;
	Ledger.Contracts.Add(Contract);

	FLBSpacecraftUnitState Unit;
	Unit.UnitId = FName(TEXT("SCOUT-01-ROUNDTRIP"));
	Unit.RecipeId = FName(TEXT("SCOUT-01"));
	Unit.Stage = ELBSpacecraftStage::Testing;
	Unit.DefectPoints = 3;
	Unit.ReworkSecondsRemaining = 217.5f;
	Unit.FailedQualityTests = 2;
	Unit.bQualityRecorded = true;
	Unit.bAwaitingSale = true;
	Ledger.Units.Add(Unit);
	TestTrue(TEXT("the ledger takes the state"),
		Rig.Production->RestoreLedger(Ledger, Reason));

	// Progression credit, on both ladders.
	Rig.Research->SyncFromLedger(Rig.Production);
	Rig.Reputation->SyncFromLedger(Rig.Production);
	const int32 SavedPoints = Rig.Research->GetPoints();
	const int32 SavedRep = Rig.Reputation->GetPoints();
	TestTrue(TEXT("the delivery credited something to remember"),
		SavedPoints > 0 && SavedRep > 0);

	TestTrue(TEXT("save succeeds"), FLBSpacecraftSavePipeline::SaveToSlot(
		Rig.Context(), SpacecraftTestSlot, Reason));

	// Wreck the live state thoroughly.
	FLBSpacecraftProductionLedgerState Wrecked = Rig.Production->CaptureLedger();
	for (FLBSpacecraftUnitState& Live : Wrecked.Units)
	{
		Live.DefectPoints = 0;
		Live.ReworkSecondsRemaining = 0.f;
		Live.bAwaitingSale = false;
		Live.FailedQualityTests = 0;
	}
	for (FLBSpacecraftContract& Live : Wrecked.Contracts)
	{
		Live.CustomerId = NAME_None;
		Live.DeadlineSimSeconds = 0.0;
	}
	TestTrue(TEXT("the wrecked ledger applies"),
		Rig.Production->RestoreLedger(Wrecked, Reason));
	TestTrue(TEXT("more points bank on top"),
		Rig.Research->AddPoints(77, Reason));

	TestTrue(TEXT("load succeeds"), FLBSpacecraftSavePipeline::LoadFromSlot(
		Rig.Context(), SpacecraftTestSlot, Reason));

	// EVERY field back, exactly.
	const FLBSpacecraftUnitState* Back =
		Rig.Production->FindUnit(FName(TEXT("SCOUT-01-ROUNDTRIP")));
	TestNotNull(TEXT("the unit came back"), Back);
	if (Back != nullptr)
	{
		TestEqual(TEXT("workmanship defects survived"),
			Back->DefectPoints, 3);
		TestEqual(TEXT("rework owing survived"),
			Back->ReworkSecondsRemaining, 217.5f);
		TestEqual(TEXT("failed tests survived"),
			Back->FailedQualityTests, 2);
		TestTrue(TEXT("finished-but-unsold survived"),
			Back->bAwaitingSale);
	}
	const FLBSpacecraftContract* BackContract =
		Rig.Production->FindContract(FName(TEXT("C-ROUNDTRIP")));
	TestNotNull(TEXT("the contract came back"), BackContract);
	if (BackContract != nullptr)
	{
		TestEqual(TEXT("the customer survived"),
			BackContract->CustomerId, FName(TEXT("Customer.Freight")));
		TestEqual(TEXT("the deadline survived"),
			BackContract->DeadlineSimSeconds, 4321.0);
		TestTrue(TEXT("the livery survived"),
			BackContract->LiveryColour.Equals(
				FLinearColor(0.72f, 0.36f, 0.06f), 0.001f));
	}
	TestEqual(TEXT("research points rewound"),
		Rig.Research->GetPoints(), SavedPoints);
	TestEqual(TEXT("reputation rewound"),
		Rig.Reputation->GetPoints(), SavedRep);

	// And the credit high-water marks came with them: re-syncing must
	// not pay for the same delivery a second time after a load.
	Rig.Research->SyncFromLedger(Rig.Production);
	Rig.Reputation->SyncFromLedger(Rig.Production);
	TestEqual(TEXT("a reload cannot re-credit research"),
		Rig.Research->GetPoints(), SavedPoints);
	TestEqual(TEXT("nor reputation"),
		Rig.Reputation->GetPoints(), SavedRep);

	Rig.World->DestroyWorld(false);
	return true;
}
