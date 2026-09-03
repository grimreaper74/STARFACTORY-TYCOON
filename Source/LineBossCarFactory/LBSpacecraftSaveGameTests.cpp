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

// FOUND BY AUDIT (2026-09-03, integration gap audit round 3): the
// MidFlightRoundTripRestoresExactly fixture above (30 fixed ticks at
// dt=5.0) genuinely passes through Phase==Moving several times along
// the way, but deterministically always lands back on Phase==Stopped
// by the time it actually saves - so the "pulse fields carried through
// Runtime wholesale" this document's own design doc claims was proven
// had never actually been tested against a save landing mid-transit.
// A manual quicksave has no phase gate (confirmed: grepped for an
// autosave system, none exists) and the default single-crane
// configuration spends several real seconds of every pulse in Moving
// whenever more than one craft is in flight - not a contrived edge
// case. This test drives to Phase==Moving directly (rather than
// hoping a fixed tick count lands there) and saves in that exact
// window.
IMPLEMENT_SIMPLE_AUTOMATION_TEST(FLBSpacecraftSaveDuringMoveRoundTripTest,
	"LineBoss.Spacecraft.SaveLoad.MidMoveRoundTripResolvesThePulseExactlyOnce",
	EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)

bool FLBSpacecraftSaveDuringMoveRoundTripTest::RunTest(
	const FString& Parameters)
{
	(void)Parameters;
	using namespace LBSpacecraftSaveGameTestsPrivate;
	FLBSpacecraftSaveRig Rig = MakeSpacecraftSaveRig();
	FString Reason;

	TestTrue(TEXT("canonical line sets up"),
		ALBSpacecraftGameMode::SetupCanonicalLine(*Rig.Build, Reason));
	TestTrue(TEXT("configured"),
		Rig.Coordinator->ConfigureFromAuthorities(Rig.Build, Rig.Production,
			Reason));
	// Quantity 2: a single unit can flip Phase to Moving (it is the
	// only non-final mover), but a second one in flight means the
	// restored coordinator has real work left to do post-load, which
	// is the more convincing proof the pulse resolves cleanly rather
	// than trivially.
	TestTrue(TEXT("contract starts"),
		ALBSpacecraftGameMode::StartScoutContract(*Rig.Production, 2,
			Reason));

	// Tick until the line is GENUINELY mid-transit, then stop - not a
	// guessed tick count, the actual phase. (Not gated on assignments
	// existing yet: at the very start there are none, and the first
	// unit is only admitted a few ticks in.)
	int32 Guard = 0;
	while (Rig.Coordinator->GetPulseProgress01() == 0.f && Guard++ < 60)
	{
		TestTrue(TEXT("tick runs"), Rig.Coordinator->TickProduction(5.0,
			Reason));
	}
	const float SavedProgress = Rig.Coordinator->GetPulseProgress01();
	TestTrue(TEXT("genuinely mid-move at save time"), SavedProgress > 0.f
		&& SavedProgress < 1.f);
	const int32 SavedPulseCount = Rig.Coordinator->GetPulseCount();
	const int32 SavedAssignments = Rig.Coordinator->GetAssignments().Num();

	TestTrue(TEXT("save succeeds mid-move"),
		FLBSpacecraftSavePipeline::SaveToSlot(Rig.Context(),
			SpacecraftTestSlot, Reason));

	// Diverge hard: run the line well past this pulse and, ideally,
	// into a later one.
	for (int32 Tick = 0; Tick < 20; ++Tick)
	{
		TestTrue(TEXT("tick runs"),
			Rig.Coordinator->TickProduction(5.0, Reason));
	}

	TestTrue(TEXT("load rolls the pulse back to the saved mid-move "
		"instant"),
		FLBSpacecraftSavePipeline::LoadFromSlot(Rig.Context(),
			SpacecraftTestSlot, Reason));
	TestEqual(TEXT("pulse progress restored exactly"),
		Rig.Coordinator->GetPulseProgress01(), SavedProgress);
	TestEqual(TEXT("pulse count restored"),
		Rig.Coordinator->GetPulseCount(), SavedPulseCount);
	TestEqual(TEXT("assignment count restored"),
		Rig.Coordinator->GetAssignments().Num(), SavedAssignments);
	TestTrue(TEXT("restored runtime validates"),
		Rig.Coordinator->ValidateRuntime(
			Rig.Coordinator->CaptureRuntime(), Reason));

	// Resuming must resolve the PENDING pulse exactly once - no
	// double-admission (PulseCount jumping by more than the number of
	// pulses that actually complete) and no stall.
	int32 PulseCountAfter = SavedPulseCount;
	Guard = 0;
	while (PulseCountAfter == SavedPulseCount && Guard++ < 40)
	{
		TestTrue(TEXT("post-load tick runs"),
			Rig.Coordinator->TickProduction(5.0, Reason));
		PulseCountAfter = Rig.Coordinator->GetPulseCount();
	}
	TestEqual(TEXT("the pending pulse resolved exactly once"),
		PulseCountAfter, SavedPulseCount + 1);

	// And the line goes on to actually finish the contract - the
	// restored mid-move state is not just structurally valid, it is
	// alive.
	Guard = 0;
	while (Rig.Production->GetUnits().Num() < 2 && Guard++ < 20)
	{
		TestTrue(TEXT("head admits the second unit eventually"),
			Rig.Coordinator->TickProduction(5.0, Reason));
	}
	TestEqual(TEXT("both units of the contract were admitted - no "
		"skipped admission from a mishandled restore"),
		Rig.Production->GetUnits().Num(), 2);

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

IMPLEMENT_SIMPLE_AUTOMATION_TEST(FLBSpacecraftFreeFormLineRoundTripTest,
	"LineBoss.Spacecraft.SaveLoad.FreeFormLineSurvivesARoundTrip",
	EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)

bool FLBSpacecraftFreeFormLineRoundTripTest::RunTest(
	const FString& Parameters)
{
	(void)Parameters;
	using namespace LBSpacecraftSaveGameTestsPrivate;
	FLBSpacecraftSaveRig Rig = MakeSpacecraftSaveRig();
	FString Reason;

	// Three stations dropped on the 400 cm lattice, deliberately NOT in
	// a straight line - the relayer routes the bends itself, and the
	// save must bring the whole bent line back, not a straight
	// stand-in for it.
	const FVector Spots[] = {
		FVector(0.f, -6000.f, 0.f),
		FVector(0.f, -2000.f, 0.f),
		FVector(2800.f, 0.f, 0.f) };
	TArray<FName> Placed;
	for (const FVector& Spot : Spots)
	{
		FName StationId;
		TestTrue(TEXT("a line station places"),
			Rig.Build->PlaceStation(FName(TEXT("AssemblyRobot")),
				FTransform(FRotator(0.f, 90.f, 0.f), Spot), StationId,
				Reason));
		Placed.Add(StationId);
	}
	TestTrue(TEXT("the relay routes the whole chain"),
		ALBSpacecraftGameMode::RelayTrackThroughStations(*Rig.Build,
			*Rig.Track, nullptr, nullptr, Reason));
	TestTrue(TEXT("the relayed line is complete (start and cap)"),
		Rig.Track->IsComplete());
	const TArray<FName> InOrder = Rig.Track->GetNodeStationsInOrder();
	TestEqual(TEXT("every station attached"), InOrder.Num(), 3);
	for (int32 Index = 0;
		Index < FMath::Min(InOrder.Num(), Placed.Num()); ++Index)
	{
		TestEqual(TEXT("track order is placement order"),
			InOrder[Index], Placed[Index]);
	}

	// Remember the shape of the relayed line before the save.
	const int32 SavedPieceCount = Rig.Track->GetPieces().Num();

	TestTrue(TEXT("save succeeds"), FLBSpacecraftSavePipeline::SaveToSlot(
		Rig.Context(), SpacecraftTestSlot, Reason));

	// Wreck the live track the same way a re-route tears down: detach
	// every station, then pop the open end back to nothing.
	for (const FName& Attached : Rig.Track->GetNodeStationsInOrder())
	{
		Rig.Track->DetachStationNode(Attached, Reason);
	}
	while (Rig.Track->GetPieces().Num() > 0)
	{
		if (!Rig.Track->RemoveOpenEnd(Reason))
		{
			break;
		}
	}
	TestEqual(TEXT("the live track is wrecked"),
		Rig.Track->GetPieces().Num(), 0);

	TestTrue(TEXT("load succeeds"), FLBSpacecraftSavePipeline::LoadFromSlot(
		Rig.Context(), SpacecraftTestSlot, Reason));
	TestTrue(TEXT("the loaded line is complete (start and cap)"),
		Rig.Track->IsComplete());
	TestEqual(TEXT("the same number of pieces came back"),
		Rig.Track->GetPieces().Num(), SavedPieceCount);
	const TArray<FName> ReloadedOrder =
		Rig.Track->GetNodeStationsInOrder();
	TestEqual(TEXT("the same three stations came back"),
		ReloadedOrder.Num(), 3);
	for (int32 Index = 0;
		Index < FMath::Min(ReloadedOrder.Num(), Placed.Num()); ++Index)
	{
		TestEqual(TEXT("in the same placement order"),
			ReloadedOrder[Index], Placed[Index]);
	}

	Rig.World->DestroyWorld(false);
	return true;
}
