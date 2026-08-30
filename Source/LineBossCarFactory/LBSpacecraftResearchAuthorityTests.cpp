#if WITH_DEV_AUTOMATION_TESTS

#include "LBSpacecraftResearchAuthority.h"

#include "LBSpacecraftProductionAuthority.h"
#include "LBSpacecraftReputationAuthority.h"
#include "LBSpacecraftGameMode.h"

#include "Engine/World.h"
#include "Misc/AutomationTest.h"

IMPLEMENT_SIMPLE_AUTOMATION_TEST(FLBSpacecraftResearchCatalogueTest,
	"LineBoss.Spacecraft.Research.ManufacturingBranchValid",
	EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)

bool FLBSpacecraftResearchCatalogueTest::RunTest(const FString& Parameters)
{
	(void)Parameters;
	FString Reason;
	TestTrue(TEXT("research table validates"),
		FLBSpacecraftResearchCatalogue::ValidateNodeTable(Reason));
	TestEqual(TEXT("four tiers, the route Mk2 marks and the parts Mk2 marks"),
		FLBSpacecraftResearchCatalogue::GetNodeTable().Num(), 6);
	// 9 = the five slice families, power plant, storage rack, and BOTH
	// halls (owner 2026-08-26: generators and parts machines live only
	// inside their buildings, so neither hall can be research-locked).
	// Thirteen since 2026-08-27: the Smelter, Structure fab and Fit-out
	// fab joined the free set when fabrication moved off the LINE. They
	// do work the player previously had for nothing on line stations, and
	// gating them would lock the chain behind research points that can
	// only be earned by delivering craft the chain has to build.
	// 14 since 2026-08-28: the SHIP FACTORY joined them. It is the
	// player's first move on the world map, so nothing at all can be
	// built until it stands - it can never sit behind research.
	// 15 since 2026-08-28: the SPRAY BOOTH is free because the line
	// REFUSES TO COMMISSION without one, and locking it behind points
	// a player can only earn by delivering craft would lock the game
	// behind itself.
	TestEqual(TEXT("slice families plus infrastructure are free"),
		FLBSpacecraftResearchCatalogue::GetDefaultStationClasses().Num(), 15);
	TestNull(TEXT("unknown node resolves to nothing"),
		FLBSpacecraftResearchCatalogue::FindNode(
			FName(TEXT("Research.Mfg.T9"))));
	return true;
}

IMPLEMENT_SIMPLE_AUTOMATION_TEST(FLBSpacecraftResearchUnlockTest,
	"LineBoss.Spacecraft.Research.UnlocksFailClosedAndGateFamilies",
	EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)

bool FLBSpacecraftResearchUnlockTest::RunTest(const FString& Parameters)
{
	(void)Parameters;
	UWorld* World = UWorld::CreateWorld(EWorldType::Game, false,
		FName(TEXT("LBSpacecraftResearchWorld")));
	ALBSpacecraftResearchAuthority* Research =
		World->SpawnActor<ALBSpacecraftResearchAuthority>();
	FString Reason;
	const FName T1(TEXT("Research.Mfg.T1"));
	const FName T2(TEXT("Research.Mfg.T2"));

	// The family gate: slice families free, researched families locked.
	TestTrue(TEXT("the slice material processor is always available"),
		Research->IsStationClassUnlocked(FName(TEXT("MaterialProcessor"))));
	TestFalse(TEXT("the rolling mill needs research"),
		Research->IsStationClassUnlocked(FName(TEXT("RollingMill"))));

	// Unlocks fail closed on points, prerequisites and repeats.
	TestFalse(TEXT("zero points refuse tier 1"),
		Research->UnlockNode(T1, Reason));
	TestFalse(TEXT("non-positive earnings refused"),
		Research->AddPoints(0, Reason));
	TestTrue(TEXT("points bank"), Research->AddPoints(30, Reason));
	TestFalse(TEXT("tier 2 refuses without tier 1"),
		Research->UnlockNode(T2, Reason));
	TestTrue(TEXT("refusal names the prerequisite"),
		Reason.Contains(TEXT("Research.Mfg.T1")));
	TestFalse(TEXT("unknown node refused"),
		Research->UnlockNode(FName(TEXT("Research.Mfg.T9")), Reason));
	TestTrue(TEXT("tier 1 unlocks"), Research->UnlockNode(T1, Reason));
	TestEqual(TEXT("tier 1 spent its cost"), Research->GetPoints(), 20);
	TestFalse(TEXT("double unlock refused"),
		Research->UnlockNode(T1, Reason));
	TestTrue(TEXT("tier 1 opened the rolling mill"),
		Research->IsStationClassUnlocked(FName(TEXT("RollingMill"))));
	TestFalse(TEXT("tier 2 families stay locked"),
		Research->IsStationClassUnlocked(FName(TEXT("PowerCellPlant"))));
	TestFalse(TEXT("20 banked cannot afford tier 2's 25"),
		Research->UnlockNode(T2, Reason));
	TestTrue(TEXT("more points bank"), Research->AddPoints(5, Reason));
	TestTrue(TEXT("tier 2 unlocks at exact cost"),
		Research->UnlockNode(T2, Reason));
	TestEqual(TEXT("the bank is empty"), Research->GetPoints(), 0);

	// Snapshots: closure-consistent restores only.
	const FLBSpacecraftResearchSnapshot Snapshot =
		Research->CaptureSnapshot();
	TestTrue(TEXT("live snapshot validates"),
		ALBSpacecraftResearchAuthority::ValidateSnapshot(Snapshot, Reason));
	FLBSpacecraftResearchSnapshot Orphan;
	Orphan.Points = 10;
	Orphan.UnlockedNodes.Add(T2); // T2 without T1: corrupt closure.
	TestFalse(TEXT("prerequisite-orphaned snapshot refused"),
		Research->RestoreSnapshot(Orphan, Reason));
	FLBSpacecraftResearchSnapshot Negative = Snapshot;
	Negative.Points = -1;
	TestFalse(TEXT("negative-points snapshot refused"),
		Research->RestoreSnapshot(Negative, Reason));
	TestEqual(TEXT("refused restores left both unlocks standing"),
		Research->GetUnlockedNodeCount(), 2);

	World->DestroyWorld(false);
	return true;
}

#endif // WITH_DEV_AUTOMATION_TESTS

IMPLEMENT_SIMPLE_AUTOMATION_TEST(FLBSpacecraftResearchEarnedTest,
	"LineBoss.Spacecraft.Research.DeliveriesBankResearchPoints",
	EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)

bool FLBSpacecraftResearchEarnedTest::RunTest(const FString& Parameters)
{
	(void)Parameters;
	using Research = ALBSpacecraftResearchAuthority;

	// Pure pacing rule: a Scout delivery (150,000 cr since the
	// hundred-part retune) teaches exactly Basic Fabrication - 10
	// points - so the FIRST delivery opens the chain.
	TestEqual(TEXT("a scout delivery is worth ten points"),
		Research::PointsForDeliveredValuePence(15000000), 10);
	TestEqual(TEXT("a cargo delivery teaches more"),
		Research::PointsForDeliveredValuePence(36000000), 24);
	TestEqual(TEXT("nothing delivered teaches nothing"),
		Research::PointsForDeliveredValuePence(0), 0);
	TestEqual(TEXT("a negative value is never a windfall"),
		Research::PointsForDeliveredValuePence(-15000000), 0);

	UWorld* World = UWorld::CreateWorld(EWorldType::Game, false,
		FName(TEXT("LBSpacecraftResearchEarnWorld")));
	ALBSpacecraftResearchAuthority* Bank =
		World->SpawnActor<ALBSpacecraftResearchAuthority>();
	ALBSpacecraftProductionAuthority* Production =
		World->SpawnActor<ALBSpacecraftProductionAuthority>();
	FString Reason;

	FLBSpacecraftContract Contract;
	Contract.ContractId = FName(TEXT("C-RESEARCH"));
	Contract.RecipeId = FName(TEXT("SCOUT-01"));
	Contract.Quantity = 1;
	Contract.PricePerUnitPence = 15000000;
	TestTrue(TEXT("contract offered"),
		Production->OfferContract(Contract, Reason));
	TestTrue(TEXT("contract accepted"),
		Production->AcceptContract(Contract.ContractId, Reason));

	// An open contract teaches nothing - only DELIVERY does.
	Bank->SyncFromLedger(Production);
	TestEqual(TEXT("an unfinished contract banks nothing"),
		Bank->GetPoints(), 0);

	// Complete it through the ledger, consistently - the restore
	// validator refuses a "complete" contract nothing was dispatched
	// against, so state and count move together.
	FLBSpacecraftProductionLedgerState Ledger = Production->CaptureLedger();
	TestEqual(TEXT("one contract on the ledger"), Ledger.Contracts.Num(), 1);
	Ledger.Contracts[0].DispatchedCount = Ledger.Contracts[0].Quantity;
	Ledger.Contracts[0].State = ELBSpacecraftContractState::Complete;
	TestTrue(TEXT("the completed ledger restores"),
		Production->RestoreLedger(Ledger, Reason));
	Bank->SyncFromLedger(Production);
	TestEqual(TEXT("delivering it banks the points"),
		Bank->GetPoints(), 10);

	// Idempotent: ticking again must not farm the same delivery.
	Bank->SyncFromLedger(Production);
	Bank->SyncFromLedger(Production);
	TestEqual(TEXT("the same delivery is never paid twice"),
		Bank->GetPoints(), 10);

	// And the first delivery really does buy the first node.
	TestTrue(TEXT("basic fabrication is now affordable"),
		Bank->UnlockNode(FName(TEXT("Research.Mfg.T1")), Reason));

	// A reload must not re-credit either.
	const FLBSpacecraftResearchSnapshot Snapshot = Bank->CaptureSnapshot();
	TestTrue(TEXT("the snapshot restores"),
		Bank->RestoreSnapshot(Snapshot, Reason));
	Bank->SyncFromLedger(Production);
	TestEqual(TEXT("a reload cannot farm the delivery again"),
		Bank->GetPoints(), 0);

	World->DestroyWorld(false);
	return true;
}

IMPLEMENT_SIMPLE_AUTOMATION_TEST(FLBSpacecraftReputationDepthTest,
	"LineBoss.Spacecraft.Research.AReputationIsWorthMoney",
	EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)

bool FLBSpacecraftReputationDepthTest::RunTest(const FString& Parameters)
{
	(void)Parameters;
	using Rep = ALBSpacecraftReputationAuthority;

	// The premium: a trusted builder is paid more. Tier 1 is the
	// baseline, and every tier above it is worth 5%.
	TestEqual(TEXT("the first tier commands no premium"),
		Rep::PricePremiumPercentForTier(1), 0);
	TestEqual(TEXT("the second tier is worth five percent"),
		Rep::PricePremiumPercentForTier(2), 5);
	TestEqual(TEXT("the fourth tier is worth fifteen"),
		Rep::PricePremiumPercentForTier(4), 15);
	TestEqual(TEXT("a tier below the first is never a discount"),
		Rep::PricePremiumPercentForTier(0), 0);

	TestEqual(TEXT("tier one pays the base price"),
		Rep::ApplyTierPremiumPence(5000000, 1),
		static_cast<int64>(5000000));
	TestEqual(TEXT("tier two pays five percent more"),
		Rep::ApplyTierPremiumPence(5000000, 2),
		static_cast<int64>(5250000));
	TestEqual(TEXT("a free contract stays free"),
		Rep::ApplyTierPremiumPence(0, 4), static_cast<int64>(0));

	// Earning: the harder job builds your name faster. A Scout is still
	// worth the two points it always was, so nothing regresses.
	UWorld* World = UWorld::CreateWorld(EWorldType::Game, false,
		FName(TEXT("LBSpacecraftReputationDepthWorld")));
	ALBSpacecraftReputationAuthority* Reputation =
		World->SpawnActor<ALBSpacecraftReputationAuthority>();
	TestEqual(TEXT("a scout delivery is still worth two"),
		Reputation->PointsForDeliveredValuePence(15000000), 2);
	TestTrue(TEXT("a cargo delivery builds the name faster"),
		Reputation->PointsForDeliveredValuePence(36000000)
			> Reputation->PointsForDeliveredValuePence(15000000));
	TestEqual(TEXT("nothing delivered earns nothing"),
		Reputation->PointsForDeliveredValuePence(0), 0);

	World->DestroyWorld(false);
	return true;
}

IMPLEMENT_SIMPLE_AUTOMATION_TEST(FLBSpacecraftPerDeliveryCreditTest,
	"LineBoss.Spacecraft.Research.ProgressionCreditsEveryDelivery",
	EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)

bool FLBSpacecraftPerDeliveryCreditTest::RunTest(const FString& Parameters)
{
	(void)Parameters;
	UWorld* World = UWorld::CreateWorld(EWorldType::Game, false,
		FName(TEXT("LBSpacecraftPerDeliveryWorld")));
	ALBSpacecraftResearchAuthority* Bank =
		World->SpawnActor<ALBSpacecraftResearchAuthority>();
	ALBSpacecraftReputationAuthority* Name =
		World->SpawnActor<ALBSpacecraftReputationAuthority>();
	ALBSpacecraftProductionAuthority* Production =
		World->SpawnActor<ALBSpacecraftProductionAuthority>();
	FString Reason;

	// A FOUR-craft order, of the kind the offer board now hands out.
	FLBSpacecraftContract Contract;
	Contract.ContractId = FName(TEXT("C-RUN"));
	Contract.RecipeId = FName(TEXT("SCOUT-01"));
	Contract.Quantity = 4;
	Contract.PricePerUnitPence = 15000000;
	TestTrue(TEXT("contract offered"),
		Production->OfferContract(Contract, Reason));
	TestTrue(TEXT("contract accepted"),
		Production->AcceptContract(Contract.ContractId, Reason));

	auto DispatchOne = [&]()
	{
		FLBSpacecraftProductionLedgerState Ledger = Production->CaptureLedger();
		++Ledger.Contracts[0].DispatchedCount;
		if (Ledger.Contracts[0].DispatchedCount >= Ledger.Contracts[0].Quantity)
		{
			Ledger.Contracts[0].State = ELBSpacecraftContractState::Complete;
		}
		return Production->RestoreLedger(Ledger, Reason);
	};

	// ONE ship delivered, of four. The old rule paid nothing until the
	// whole order landed, so a player built four craft and watched the
	// research tree stay dead.
	TestTrue(TEXT("the first ship is delivered"), DispatchOne());
	Bank->SyncFromLedger(Production);
	Name->SyncFromLedger(Production);
	TestEqual(TEXT("the first delivery already teaches"),
		Bank->GetPoints(), 10);
	TestEqual(TEXT("and already builds the name"), Name->GetPoints(), 2);

	// Re-syncing without a new delivery must pay nothing.
	Bank->SyncFromLedger(Production);
	Name->SyncFromLedger(Production);
	TestEqual(TEXT("no delivery, no further credit"),
		Bank->GetPoints(), 10);
	TestEqual(TEXT("reputation likewise"), Name->GetPoints(), 2);

	// The rest of the order pays as it lands, not in a lump.
	TestTrue(TEXT("a second ship"), DispatchOne());
	Bank->SyncFromLedger(Production);
	TestEqual(TEXT("the second delivery teaches too"),
		Bank->GetPoints(), 20);

	TestTrue(TEXT("the third"), DispatchOne());
	TestTrue(TEXT("and the fourth completes the order"), DispatchOne());
	Bank->SyncFromLedger(Production);
	Name->SyncFromLedger(Production);
	TestEqual(TEXT("four deliveries, four lots of credit"),
		Bank->GetPoints(), 40);
	TestEqual(TEXT("and four lots of reputation"), Name->GetPoints(), 8);

	// Completing the contract must not pay a fifth time.
	Bank->SyncFromLedger(Production);
	TestEqual(TEXT("completion is not a bonus round"),
		Bank->GetPoints(), 40);

	// A reload cannot farm the same deliveries again.
	const FLBSpacecraftResearchSnapshot Snapshot = Bank->CaptureSnapshot();
	TestTrue(TEXT("the snapshot restores"),
		Bank->RestoreSnapshot(Snapshot, Reason));
	Bank->SyncFromLedger(Production);
	TestEqual(TEXT("a reload re-credits nothing"), Bank->GetPoints(), 40);

	World->DestroyWorld(false);
	return true;
}

IMPLEMENT_SIMPLE_AUTOMATION_TEST(FLBSpacecraftContractDeadlineTest,
	"LineBoss.Spacecraft.Research.MissingADeadlineCostsYourName",
	EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)

bool FLBSpacecraftContractDeadlineTest::RunTest(const FString& Parameters)
{
	(void)Parameters;
	using Mode = ALBSpacecraftGameMode;

	FLBSpacecraftRecipe Scout;
	TestTrue(TEXT("the scout recipe exists"),
		FLBSpacecraftProductionCatalog::FindRecipe(FName(TEXT("SCOUT-01")),
			Scout));

	// A bigger order buys more time, and even a single craft gets a
	// real allowance rather than a knife-edge.
	//
	// MEASURED AGAINST THE BUILD, NOT AGAINST A CONSTANT. This used to
	// assert One > 1800 s, which pinned the old formula's base rather
	// than any property of the game - and 1800 s of slack on a 440 s
	// craft was the whole problem: at eleven to fourteen times the time
	// needed, nothing on the line had time pressure attached and a
	// rework could never threaten a delivery.
	double Work = 0.0;
	double Bottleneck = 0.0;
	for (const TPair<ELBSpacecraftStage, float>& Stage :
		Scout.NominalCycleSeconds)
	{
		Work += FMath::Max(Stage.Value, 0.f);
		Bottleneck = FMath::Max(Bottleneck,
			static_cast<double>(FMath::Max(Stage.Value, 0.f)));
	}
	const double One = Mode::ContractAllowanceSeconds(Scout, 1);
	const double Four = Mode::ContractAllowanceSeconds(Scout, 4);

	TestTrue(TEXT("one craft gets more time than it takes to build"),
		One > Work);
	// THE CORRIDOR. Slack has to be near the largest rework a craft can
	// owe or nothing ever threatens a deadline; far under the build and
	// ordinary variance makes the player late through no fault of their
	// own. Bounded on both sides, because both failures are real.
	TestTrue(TEXT("but not so much that a rework can never threaten it"),
		One < Work * 3.0);
	TestTrue(TEXT("four craft get more"), Four > One);

	// PIPELINED, NOT MULTIPLIED. Four craft cost three extra bottleneck
	// cycles, not three extra builds - the line is a pipeline. The old
	// formula multiplied whole-craft work by quantity, which is why an
	// eight-craft order was allowed ten hours.
	TestEqual(TEXT("extra craft cost one bottleneck cycle each"),
		Four - One, Bottleneck * 3.0);
	// So slack is CONSTANT: the disposition choice behaves the same on
	// a single craft as on a run of four.
	TestEqual(TEXT("slack does not grow with order size"),
		One - Work, Four - (Work + Bottleneck * 3.0));

	TestTrue(TEXT("a nonsense quantity still yields an allowance"),
		Mode::ContractAllowanceSeconds(Scout, 0) > 0.0);

	UWorld* World = UWorld::CreateWorld(EWorldType::Game, false,
		FName(TEXT("LBSpacecraftDeadlineWorld")));
	ALBSpacecraftProductionAuthority* Production =
		World->SpawnActor<ALBSpacecraftProductionAuthority>();
	ALBSpacecraftReputationAuthority* Name =
		World->SpawnActor<ALBSpacecraftReputationAuthority>();
	FString Reason;

	// Build a name worth losing.
	FLBSpacecraftContract Done;
	Done.ContractId = FName(TEXT("C-DONE"));
	Done.RecipeId = FName(TEXT("SCOUT-01"));
	Done.Quantity = 4;
	Done.PricePerUnitPence = 15000000;
	TestTrue(TEXT("offered"), Production->OfferContract(Done, Reason));
	TestTrue(TEXT("accepted"),
		Production->AcceptContract(Done.ContractId, Reason));
	FLBSpacecraftProductionLedgerState Ledger = Production->CaptureLedger();
	Ledger.Contracts[0].DispatchedCount = 4;
	Ledger.Contracts[0].State = ELBSpacecraftContractState::Complete;
	TestTrue(TEXT("delivered"), Production->RestoreLedger(Ledger, Reason));
	Name->SyncFromLedger(Production);
	const int32 Earned = Name->GetPoints();
	TestTrue(TEXT("delivering built a name"), Earned > 0);

	// Now take an order and miss it.
	FLBSpacecraftContract Missed;
	Missed.ContractId = FName(TEXT("C-LATE"));
	Missed.RecipeId = FName(TEXT("SCOUT-01"));
	Missed.Quantity = 2;
	Missed.PricePerUnitPence = 15000000;
	Missed.DeadlineSimSeconds = Production->GetSimSeconds() + 100.0;
	TestTrue(TEXT("the late order is offered"),
		Production->OfferContract(Missed, Reason));
	TestTrue(TEXT("and accepted"),
		Production->AcceptContract(Missed.ContractId, Reason));

	// An offer nobody took, on the same clock.
	FLBSpacecraftContract Ignored;
	Ignored.ContractId = FName(TEXT("C-IGNORED"));
	Ignored.RecipeId = FName(TEXT("SCOUT-01"));
	Ignored.Quantity = 1;
	Ignored.PricePerUnitPence = 15000000;
	Ignored.DeadlineSimSeconds = Production->GetSimSeconds() + 100.0;
	TestTrue(TEXT("an offer sits on the board"),
		Production->OfferContract(Ignored, Reason));

	TestTrue(TEXT("the clock runs past both"),
		Production->AdvanceSimSeconds(500.0, Reason));

	const FLBSpacecraftContract* Late =
		Production->FindContract(FName(TEXT("C-LATE")));
	TestNotNull(TEXT("the late order still exists"), Late);
	if (Late != nullptr)
	{
		TestEqual(TEXT("an order you took and missed EXPIRES"),
			Late->State, ELBSpacecraftContractState::Expired);
	}
	const FLBSpacecraftContract* Lapsed =
		Production->FindContract(FName(TEXT("C-IGNORED")));
	TestNotNull(TEXT("the lapsed offer still exists"), Lapsed);
	if (Lapsed != nullptr)
	{
		TestEqual(TEXT("an offer you never took merely LAPSES"),
			Lapsed->State, ELBSpacecraftContractState::Withdrawn);
	}

	Name->SyncFromLedger(Production);
	TestTrue(TEXT("missing a deadline cost the name"),
		Name->GetPoints() < Earned);
	const int32 AfterPenalty = Name->GetPoints();
	Name->SyncFromLedger(Production);
	TestEqual(TEXT("and cost it exactly once"),
		Name->GetPoints(), AfterPenalty);

	// Reputation floors at zero - a bad run sets you back, it does not
	// put you in debt.
	for (int32 Round = 0; Round < 10; ++Round)
	{
		FLBSpacecraftContract More;
		More.ContractId = FName(*FString::Printf(TEXT("C-BAD-%d"), Round));
		More.RecipeId = FName(TEXT("SCOUT-01"));
		More.Quantity = 4;
		More.PricePerUnitPence = 15000000;
		More.DeadlineSimSeconds = Production->GetSimSeconds() + 10.0;
		Production->OfferContract(More, Reason);
		Production->AcceptContract(More.ContractId, Reason);
		Production->AdvanceSimSeconds(100.0, Reason);
		Name->SyncFromLedger(Production);
	}
	TestTrue(TEXT("a name can be lost but never goes negative"),
		Name->GetPoints() >= 0);

	World->DestroyWorld(false);
	return true;
}
