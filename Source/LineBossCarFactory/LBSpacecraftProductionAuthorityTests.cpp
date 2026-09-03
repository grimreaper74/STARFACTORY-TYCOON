#if WITH_DEV_AUTOMATION_TESTS

#include "LBSpacecraftProductionAuthority.h"
#include "LBSpacecraftBuildAuthority.h"

#include "Engine/World.h"
#include "Misc/AutomationTest.h"

namespace LBSpacecraftProductionAuthorityTestsPrivate
{
	UWorld* MakeSpacecraftLedgerTestWorld()
	{
		return UWorld::CreateWorld(EWorldType::Game, false,
			FName(TEXT("LBSpacecraftLedgerWorld")));
	}

	FLBSpacecraftContract MakeScoutContract(const TCHAR* Id, int32 Quantity,
		double DeadlineSimSeconds = 0.0)
	{
		FLBSpacecraftContract Contract;
		Contract.ContractId = FName(Id);
		Contract.RecipeId = FName(TEXT("SCOUT-01"));
		Contract.Quantity = Quantity;
		Contract.PricePerUnitPence = 5500000; // 55,000 GBP
		Contract.DeadlineSimSeconds = DeadlineSimSeconds;
		return Contract;
	}

	/** Advances a unit to the Testing stage (six legal steps). */
	bool AdvanceSpacecraftUnitToTesting(
		ALBSpacecraftProductionAuthority& Authority, FName UnitId,
		FString& OutReason)
	{
		for (int32 Step = 0; Step < 6; ++Step)
		{
			if (!Authority.AdvanceUnit(UnitId, OutReason))
			{
				return false;
			}
		}
		const FLBSpacecraftUnitState* Unit = Authority.FindUnit(UnitId);
		return Unit != nullptr && Unit->Stage == ELBSpacecraftStage::Testing;
	}
}

IMPLEMENT_SIMPLE_AUTOMATION_TEST(FLBSpacecraftContractLifecycleTest,
	"LineBoss.Spacecraft.ProductionAuthority.ContractOfferAcceptFailsClosed",
	EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)

bool FLBSpacecraftContractLifecycleTest::RunTest(const FString& Parameters)
{
	(void)Parameters;
	using namespace LBSpacecraftProductionAuthorityTestsPrivate;
	UWorld* World = MakeSpacecraftLedgerTestWorld();
	ALBSpacecraftProductionAuthority* Authority =
		World->SpawnActor<ALBSpacecraftProductionAuthority>();
	if (!TestNotNull(TEXT("authority spawns"), Authority))
	{
		World->DestroyWorld(false);
		return false;
	}
	FString Reason;

	// Rejections, each with a reason: empty, unknown recipe, zero quantity.
	FLBSpacecraftContract Bad;
	TestFalse(TEXT("empty contract is rejected"),
		Authority->OfferContract(Bad, Reason));
	FLBSpacecraftContract WrongRecipe = MakeScoutContract(TEXT("C-BAD"), 1);
	WrongRecipe.RecipeId = FName(TEXT("BATTLESHIP-99"));
	TestFalse(TEXT("unknown recipe is rejected"),
		Authority->OfferContract(WrongRecipe, Reason));
	FLBSpacecraftContract ZeroQuantity = MakeScoutContract(TEXT("C-ZERO"), 0);
	TestFalse(TEXT("zero quantity is rejected"),
		Authority->OfferContract(ZeroQuantity, Reason));

	// Offer -> duplicate refused -> accept -> double accept refused.
	TestTrue(TEXT("valid offer lands"),
		Authority->OfferContract(MakeScoutContract(TEXT("C-001"), 2), Reason));
	TestFalse(TEXT("duplicate offer is rejected"),
		Authority->OfferContract(MakeScoutContract(TEXT("C-001"), 2), Reason));
	TestFalse(TEXT("units need an ACCEPTED contract, not an offer"),
		[&]() { FName UnitId; return Authority->CreateUnit(
			FName(TEXT("SCOUT-01")), UnitId, Reason); }());
	TestTrue(TEXT("contract accepts"),
		Authority->AcceptContract(FName(TEXT("C-001")), Reason));
	TestFalse(TEXT("double accept is rejected"),
		Authority->AcceptContract(FName(TEXT("C-001")), Reason));
	TestFalse(TEXT("accepting an unknown contract is rejected"),
		Authority->AcceptContract(FName(TEXT("C-404")), Reason));

	World->DestroyWorld(false);
	return true;
}

IMPLEMENT_SIMPLE_AUTOMATION_TEST(FLBSpacecraftFullLoopTest,
	"LineBoss.Spacecraft.ProductionAuthority.FullLoopDispatchSettlesContract",
	EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)

bool FLBSpacecraftFullLoopTest::RunTest(const FString& Parameters)
{
	(void)Parameters;
	using namespace LBSpacecraftProductionAuthorityTestsPrivate;
	UWorld* World = MakeSpacecraftLedgerTestWorld();
	ALBSpacecraftProductionAuthority* Authority =
		World->SpawnActor<ALBSpacecraftProductionAuthority>();
	FString Reason;

	TestTrue(TEXT("offer"), Authority->OfferContract(
		MakeScoutContract(TEXT("C-001"), 1), Reason));
	TestTrue(TEXT("accept"), Authority->AcceptContract(
		FName(TEXT("C-001")), Reason));

	FName UnitId;
	TestTrue(TEXT("unit creates against accepted demand"),
		Authority->CreateUnit(FName(TEXT("SCOUT-01")), UnitId, Reason));

	// Demand is claimed by the in-flight unit: a second unit is refused.
	FName SecondUnit;
	TestFalse(TEXT("no unclaimed demand for a second unit"),
		Authority->CreateUnit(FName(TEXT("SCOUT-01")), SecondUnit, Reason));
	TestTrue(TEXT("refusal names demand"),
		Reason.Contains(TEXT("DEMAND")));

	TestTrue(TEXT("unit reaches Testing"),
		AdvanceSpacecraftUnitToTesting(*Authority, UnitId, Reason));

	// The gate: no recorded result -> no dispatch.
	TestFalse(TEXT("dispatch refused before the hover test"),
		Authority->AdvanceUnit(UnitId, Reason));
	TestTrue(TEXT("refusal names the quality gate"),
		Reason.Contains(TEXT("QUALITY")));

	// Quality can only be recorded at the gate; earlier attempt on a fresh
	// contract-less recording path is covered by the retest case. Record a
	// pass and dispatch.
	TestTrue(TEXT("hover test pass records"),
		Authority->RecordQualityResult(UnitId, true, Reason));
	TestTrue(TEXT("dispatch succeeds after the pass"),
		Authority->AdvanceUnit(UnitId, Reason));

	const FLBSpacecraftUnitState* Unit = Authority->FindUnit(UnitId);
	TestNotNull(TEXT("unit still exists"), Unit);
	if (Unit != nullptr)
	{
		TestEqual(TEXT("unit is dispatched"), Unit->Stage,
			ELBSpacecraftStage::Dispatched);
		TestTrue(TEXT("unit completed"), Unit->bCompleted);
		TestEqual(TEXT("unit carries all six components"),
			Unit->ProducedComponents.Num(), 6);
	}

	const FLBSpacecraftContract* Contract =
		Authority->FindContract(FName(TEXT("C-001")));
	TestNotNull(TEXT("contract exists"), Contract);
	if (Contract != nullptr)
	{
		TestEqual(TEXT("contract is complete"), Contract->State,
			ELBSpacecraftContractState::Complete);
		TestEqual(TEXT("dispatched count settled"),
			Contract->DispatchedCount, 1);
	}
	TestEqual(TEXT("revenue equals the contract price"),
		Authority->GetRevenuePence(), (int64)5500000);

	// Demand is exhausted: further units are refused.
	TestFalse(TEXT("no further unit without demand"),
		Authority->CreateUnit(FName(TEXT("SCOUT-01")), SecondUnit, Reason));

	World->DestroyWorld(false);
	return true;
}

IMPLEMENT_SIMPLE_AUTOMATION_TEST(FLBSpacecraftQualityRetestTest,
	"LineBoss.Spacecraft.ProductionAuthority.QualityFailBlocksUntilRetest",
	EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)

bool FLBSpacecraftQualityRetestTest::RunTest(const FString& Parameters)
{
	(void)Parameters;
	using namespace LBSpacecraftProductionAuthorityTestsPrivate;
	UWorld* World = MakeSpacecraftLedgerTestWorld();
	ALBSpacecraftProductionAuthority* Authority =
		World->SpawnActor<ALBSpacecraftProductionAuthority>();
	FString Reason;

	TestTrue(TEXT("offer"), Authority->OfferContract(
		MakeScoutContract(TEXT("C-001"), 1), Reason));
	TestTrue(TEXT("accept"), Authority->AcceptContract(
		FName(TEXT("C-001")), Reason));
	FName UnitId;
	TestTrue(TEXT("create"), Authority->CreateUnit(
		FName(TEXT("SCOUT-01")), UnitId, Reason));

	// Quality cannot be recorded away from the gate.
	TestFalse(TEXT("recording before Testing is rejected"),
		Authority->RecordQualityResult(UnitId, true, Reason));
	TestTrue(TEXT("refusal names the gate"),
		Reason.Contains(TEXT("TESTING GATE")));

	TestTrue(TEXT("unit reaches Testing"),
		AdvanceSpacecraftUnitToTesting(*Authority, UnitId, Reason));

	// A failed hover test blocks dispatch, names rework, and can be retested.
	TestTrue(TEXT("failed test records"),
		Authority->RecordQualityResult(UnitId, false, Reason));
	TestFalse(TEXT("failed unit cannot dispatch"),
		Authority->AdvanceUnit(UnitId, Reason));
	TestTrue(TEXT("refusal names the retest"),
		Reason.Contains(TEXT("RETEST")));
	TestTrue(TEXT("retest pass records"),
		Authority->RecordQualityResult(UnitId, true, Reason));
	TestTrue(TEXT("dispatch succeeds after the retest"),
		Authority->AdvanceUnit(UnitId, Reason));

	// Defect penalty (vision: honest economy, PROVISIONAL 10%/defect):
	// the one failed hover test settled this unit at 90% of its price.
	TestEqual(TEXT("the defect deducted 10% from the settlement"),
		Authority->GetRevenuePence(), (int64)(5500000 * 90 / 100));

	World->DestroyWorld(false);
	return true;
}

IMPLEMENT_SIMPLE_AUTOMATION_TEST(FLBSpacecraftCapAndDeadlineTest,
	"LineBoss.Spacecraft.ProductionAuthority.WIPCapAndDeadlineExpiry",
	EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)

bool FLBSpacecraftCapAndDeadlineTest::RunTest(const FString& Parameters)
{
	(void)Parameters;
	using namespace LBSpacecraftProductionAuthorityTestsPrivate;
	UWorld* World = MakeSpacecraftLedgerTestWorld();
	ALBSpacecraftProductionAuthority* Authority =
		World->SpawnActor<ALBSpacecraftProductionAuthority>();
	FString Reason;

	// Ten units of demand, deadline at sim second 100.
	TestTrue(TEXT("offer"), Authority->OfferContract(
		MakeScoutContract(TEXT("C-001"), 10, 100.0), Reason));
	TestTrue(TEXT("accept"), Authority->AcceptContract(
		FName(TEXT("C-001")), Reason));

	// The WIP cap (default 3) refuses the fourth in-flight unit.
	FName UnitIds[4];
	for (int32 Index = 0; Index < 3; ++Index)
	{
		TestTrue(TEXT("unit within cap creates"), Authority->CreateUnit(
			FName(TEXT("SCOUT-01")), UnitIds[Index], Reason));
	}
	TestFalse(TEXT("fourth unit exceeds the WIP cap"),
		Authority->CreateUnit(FName(TEXT("SCOUT-01")), UnitIds[3], Reason));
	TestTrue(TEXT("refusal names the cap"), Reason.Contains(TEXT("WIP CAP")));

	// The clock never runs backwards.
	TestFalse(TEXT("negative clock delta is rejected"),
		Authority->AdvanceSimSeconds(-1.0, Reason));

	// Past the deadline the contract expires and stops creating demand.
	TestTrue(TEXT("clock advances"),
		Authority->AdvanceSimSeconds(150.0, Reason));
	const FLBSpacecraftContract* Contract =
		Authority->FindContract(FName(TEXT("C-001")));
	TestNotNull(TEXT("contract exists"), Contract);
	if (Contract != nullptr)
	{
		TestEqual(TEXT("contract expired"), Contract->State,
			ELBSpacecraftContractState::Expired);
	}

	// BEHAVIOUR CHANGED, deliberately (2026-08-27): an in-flight unit
	// whose contract expired used to be REFUSED at dispatch, and this
	// test pinned that refusal. Refusing is what stranded the craft -
	// it sat at the gate forever with nothing to settle against and
	// blocked the whole line behind it, which deadlines made a real
	// case rather than a theoretical one. It rolls off into finished
	// stock now and waits for an order it fits.
	TestTrue(TEXT("unit reaches Testing"),
		AdvanceSpacecraftUnitToTesting(*Authority, UnitIds[0], Reason));
	TestTrue(TEXT("hover test passes"),
		Authority->RecordQualityResult(UnitIds[0], true, Reason));
	TestTrue(TEXT("with no order, the craft still leaves the line"),
		Authority->AdvanceUnit(UnitIds[0], Reason));
	TestEqual(TEXT("and stands in finished stock"),
		Authority->GetStockedCraftCount(), 1);
	TestEqual(TEXT("unsold, so nothing was paid for it"),
		Authority->GetRevenuePence(), static_cast<int64>(0));

	World->DestroyWorld(false);
	return true;
}

IMPLEMENT_SIMPLE_AUTOMATION_TEST(FLBSpacecraftLedgerSaveTest,
	"LineBoss.Spacecraft.ProductionAuthority.LedgerValidatesBeforeRestore",
	EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)

bool FLBSpacecraftLedgerSaveTest::RunTest(const FString& Parameters)
{
	(void)Parameters;
	using namespace LBSpacecraftProductionAuthorityTestsPrivate;
	UWorld* World = MakeSpacecraftLedgerTestWorld();
	ALBSpacecraftProductionAuthority* Authority =
		World->SpawnActor<ALBSpacecraftProductionAuthority>();
	FString Reason;

	TestTrue(TEXT("offer"), Authority->OfferContract(
		MakeScoutContract(TEXT("C-001"), 2), Reason));
	TestTrue(TEXT("accept"), Authority->AcceptContract(
		FName(TEXT("C-001")), Reason));
	FName UnitId;
	TestTrue(TEXT("create"), Authority->CreateUnit(
		FName(TEXT("SCOUT-01")), UnitId, Reason));
	TestTrue(TEXT("advance once"), Authority->AdvanceUnit(UnitId, Reason));

	const FLBSpacecraftProductionLedgerState Snapshot =
		Authority->CaptureLedger();
	TestTrue(TEXT("captured ledger validates"),
		Authority->ValidateLedger(Snapshot, Reason));

	ALBSpacecraftProductionAuthority* Fresh =
		World->SpawnActor<ALBSpacecraftProductionAuthority>();
	TestTrue(TEXT("ledger restores into a fresh authority"),
		Fresh->RestoreLedger(Snapshot, Reason));
	TestEqual(TEXT("restored unit count matches"),
		Fresh->GetUnits().Num(), 1);

	// Tampered snapshots are rejected wholesale.
	FLBSpacecraftProductionLedgerState DuplicateUnit = Snapshot;
	// copy first: TArray::Add asserts on an element aliased from the same
	// array (Add may reallocate out from under the reference)
	const FLBSpacecraftUnitState DuplicatedRecord = DuplicateUnit.Units[0];
	DuplicateUnit.Units.Add(DuplicatedRecord);
	TestFalse(TEXT("duplicate unit id rejected"),
		Fresh->RestoreLedger(DuplicateUnit, Reason));

	FLBSpacecraftProductionLedgerState OverDispatched = Snapshot;
	OverDispatched.Contracts[0].DispatchedCount = 99;
	TestFalse(TEXT("over-dispatched contract rejected"),
		Fresh->RestoreLedger(OverDispatched, Reason));

	FLBSpacecraftProductionLedgerState StaleSequence = Snapshot;
	StaleSequence.NextUnitSequence = 1;
	TestFalse(TEXT("stale unit sequence rejected"),
		Fresh->RestoreLedger(StaleSequence, Reason));

	FLBSpacecraftProductionLedgerState FalseComplete = Snapshot;
	FalseComplete.Contracts[0].State = ELBSpacecraftContractState::Complete;
	TestFalse(TEXT("complete claim with demand left rejected"),
		Fresh->RestoreLedger(FalseComplete, Reason));

	FLBSpacecraftProductionLedgerState GhostPass = Snapshot;
	GhostPass.Units[0].bQualityPassed = true; // pass without a record
	TestFalse(TEXT("quality pass without a record rejected"),
		Fresh->RestoreLedger(GhostPass, Reason));

	// The good state survived every rejected tamper.
	TestEqual(TEXT("rejected restores leave the ledger untouched"),
		Fresh->GetUnits().Num(), 1);
	TestTrue(TEXT("ledger still validates"),
		Fresh->ValidateLedger(Fresh->CaptureLedger(), Reason));

	World->DestroyWorld(false);
	return true;
}

IMPLEMENT_SIMPLE_AUTOMATION_TEST(FLBSpacecraftConcessionTest,
	"LineBoss.Spacecraft.ProductionAuthority.ConcessionShipsADeviation",
	EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)

bool FLBSpacecraftConcessionTest::RunTest(const FString& Parameters)
{
	(void)Parameters;
	using namespace LBSpacecraftProductionAuthorityTestsPrivate;
	UWorld* World = MakeSpacecraftLedgerTestWorld();
	ALBSpacecraftProductionAuthority* Authority =
		World->SpawnActor<ALBSpacecraftProductionAuthority>();
	FString Reason;

	TestTrue(TEXT("offer"), Authority->OfferContract(
		MakeScoutContract(TEXT("C-001"), 1), Reason));
	TestTrue(TEXT("accept"), Authority->AcceptContract(
		FName(TEXT("C-001")), Reason));
	FName UnitId;
	TestTrue(TEXT("unit creates"),
		Authority->CreateUnit(FName(TEXT("SCOUT-01")), UnitId, Reason));
	TestTrue(TEXT("unit reaches Testing"),
		AdvanceSpacecraftUnitToTesting(*Authority, UnitId, Reason));

	// NOTHING TO CONCEDE YET. A concession is a signature against a
	// KNOWN deviation, so it cannot precede the test that finds one.
	TestFalse(TEXT("an untested craft cannot be conceded"),
		Authority->GrantConcession(UnitId, Reason));
	TestTrue(TEXT("refusal says the craft is untested"),
		Reason.Contains(TEXT("UNTESTED")));

	// Fail it with a deviation small enough for a board to sign.
	TestTrue(TEXT("defects accrue"),
		Authority->AccrueDefects(UnitId, 3, Reason));
	TestTrue(TEXT("hover test fails"),
		Authority->RecordQualityResult(UnitId, false, Reason));

	const FLBSpacecraftUnitState* Failed = Authority->FindUnit(UnitId);
	TestNotNull(TEXT("unit survives the failure"), Failed);
	if (Failed != nullptr)
	{
		TestTrue(TEXT("a failure opens rework"),
			Failed->ReworkSecondsRemaining > 0.f);
	}
	TestFalse(TEXT("a failed craft cannot dispatch"),
		Authority->AdvanceUnit(UnitId, Reason));

	// THE DISPOSITION. This is the decision the mechanic exists for.
	TestTrue(TEXT("the board signs the concession"),
		Authority->GrantConcession(UnitId, Reason));

	const FLBSpacecraftUnitState* Conceded = Authority->FindUnit(UnitId);
	TestNotNull(TEXT("unit still exists"), Conceded);
	if (Conceded != nullptr)
	{
		TestTrue(TEXT("the concession is recorded"),
			Conceded->bConcessionGranted);
		TestEqual(TEXT("what was signed for is recorded, not recomputed"),
			Conceded->ConcededDefectPoints, 3);
		// The concession BUYS OUT the rework. Leaving it open would
		// take the margin and the reputation and still hold the craft.
		TestEqual(TEXT("the rework is bought out"),
			Conceded->ReworkSecondsRemaining, 0.f);
	}

	// Not idempotent, deliberately: a second signature would charge
	// twice for one decision.
	TestFalse(TEXT("it cannot be signed twice"),
		Authority->GrantConcession(UnitId, Reason));
	TestTrue(TEXT("refusal says it already ships on one"),
		Reason.Contains(TEXT("ALREADY")));

	// A concession SUBSTITUTES FOR A PASS - without this the craft
	// would take every cost of the decision and still sit at the gate.
	TestTrue(TEXT("a conceded craft dispatches"),
		Authority->AdvanceUnit(UnitId, Reason));

	// And it is charged for. One failed test alone would deduct 10%;
	// the concession at 3 points deducts more, and REPLACES rather
	// than stacks - a concession that cost more than scrapping would
	// stop being a decision.
	const int32 Expected = FLBSpacecraftProductionCatalog
		::ConcessionDeductionPercent(3);
	const int64 Paid = Authority->GetRevenuePence();
	TestEqual(TEXT("settlement charges the concession, not both"),
		Paid, (int64)5500000 * (100 - Expected) / 100);
	TestTrue(TEXT("a concession costs more than the bare failure"),
		Expected > 10);

	TestTrue(TEXT("reputation is owed for it"),
		Authority->GetConcessionReputationOwed() > 0);
	const int32 Owed = Authority->TakeConcessionReputationOwed();
	TestTrue(TEXT("taking it yields the cost"), Owed > 0);
	TestEqual(TEXT("and it can never be charged twice"),
		Authority->GetConcessionReputationOwed(), 0);

	World->DestroyWorld(false);
	return true;
}

IMPLEMENT_SIMPLE_AUTOMATION_TEST(FLBSpacecraftConcessionCeilingTest,
	"LineBoss.Spacecraft.ProductionAuthority.ConcessionHasACeiling",
	EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)

bool FLBSpacecraftConcessionCeilingTest::RunTest(const FString& Parameters)
{
	(void)Parameters;
	using namespace LBSpacecraftProductionAuthorityTestsPrivate;
	UWorld* World = MakeSpacecraftLedgerTestWorld();
	ALBSpacecraftProductionAuthority* Authority =
		World->SpawnActor<ALBSpacecraftProductionAuthority>();
	FString Reason;

	TestTrue(TEXT("offer"), Authority->OfferContract(
		MakeScoutContract(TEXT("C-001"), 1), Reason));
	TestTrue(TEXT("accept"), Authority->AcceptContract(
		FName(TEXT("C-001")), Reason));
	FName UnitId;
	TestTrue(TEXT("unit creates"),
		Authority->CreateUnit(FName(TEXT("SCOUT-01")), UnitId, Reason));
	TestTrue(TEXT("unit reaches Testing"),
		AdvanceSpacecraftUnitToTesting(*Authority, UnitId, Reason));

	// THE CEILING IS THE WHOLE MECHANIC. Without it a concession is a
	// flat fee that retires the quality gate: every failure, however
	// bad, becomes a small deduction and crewing the line properly
	// stops mattering.
	const int32 Ceiling = FLBSpacecraftProductionCatalog
		::MaxConcedableDefectPoints();
	TestTrue(TEXT("defects accrue past the ceiling"),
		Authority->AccrueDefects(UnitId, Ceiling + 1, Reason));
	TestTrue(TEXT("hover test fails"),
		Authority->RecordQualityResult(UnitId, false, Reason));

	TestFalse(TEXT("too far out to sign off"),
		Authority->GrantConcession(UnitId, Reason));
	TestTrue(TEXT("the refusal names the limit"),
		Reason.Contains(TEXT("LIMIT")));
	// The refusal must be ACTIONABLE - the fail-closed messages are
	// this game's tutorial, so it names the actual numbers.
	TestTrue(TEXT("and states the craft's own count"),
		Reason.Contains(FString::FromInt(Ceiling + 1)));

	// Still barred from dispatch, so the craft is not stranded in a
	// state with no way out: SCRAP is the remaining disposition.
	TestFalse(TEXT("and it still cannot dispatch"),
		Authority->AdvanceUnit(UnitId, Reason));
	TestTrue(TEXT("the craft can be scrapped"),
		Authority->ScrapUnit(UnitId, Reason));
	TestNull(TEXT("and is gone from the line"),
		Authority->FindUnit(UnitId));
	TestFalse(TEXT("scrapping it twice is refused"),
		Authority->ScrapUnit(UnitId, Reason));

	World->DestroyWorld(false);
	return true;
}

IMPLEMENT_SIMPLE_AUTOMATION_TEST(FLBSpacecraftConcessionSaveTest,
	"LineBoss.Spacecraft.ProductionAuthority.ConcessionSurvivesValidation",
	EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)

bool FLBSpacecraftConcessionSaveTest::RunTest(const FString& Parameters)
{
	(void)Parameters;
	using namespace LBSpacecraftProductionAuthorityTestsPrivate;
	UWorld* World = MakeSpacecraftLedgerTestWorld();
	ALBSpacecraftProductionAuthority* Authority =
		World->SpawnActor<ALBSpacecraftProductionAuthority>();
	FString Reason;

	TestTrue(TEXT("offer"), Authority->OfferContract(
		MakeScoutContract(TEXT("C-001"), 1), Reason));
	TestTrue(TEXT("accept"), Authority->AcceptContract(
		FName(TEXT("C-001")), Reason));
	FName UnitId;
	TestTrue(TEXT("unit creates"),
		Authority->CreateUnit(FName(TEXT("SCOUT-01")), UnitId, Reason));
	TestTrue(TEXT("unit reaches Testing"),
		AdvanceSpacecraftUnitToTesting(*Authority, UnitId, Reason));
	TestTrue(TEXT("defects accrue"),
		Authority->AccrueDefects(UnitId, 2, Reason));
	TestTrue(TEXT("hover test fails"),
		Authority->RecordQualityResult(UnitId, false, Reason));
	TestTrue(TEXT("concession granted"),
		Authority->GrantConcession(UnitId, Reason));

	// A GENUINE CONCESSION ROUND-TRIPS.
	FLBSpacecraftProductionLedgerState Saved = Authority->CaptureLedger();
	TestTrue(TEXT("a real concession validates"),
		Authority->ValidateLedger(Saved, Reason));

	// A DEVIATION WITHOUT A SIGNATURE DOES NOT. The two fields are one
	// record; a save where they disagree describes a craft that cannot
	// be priced, and it would settle for the wrong money in silence.
	FLBSpacecraftProductionLedgerState Orphaned = Saved;
	for (FLBSpacecraftUnitState& Unit : Orphaned.Units)
	{
		Unit.bConcessionGranted = false;
	}
	TestFalse(TEXT("a deviation with no concession is rejected"),
		Authority->ValidateLedger(Orphaned, Reason));
	TestTrue(TEXT("and the refusal says so"),
		Reason.Contains(TEXT("WITHOUT A CONCESSION")));

	// NEITHER DOES ONE NO BOARD COULD HAVE SIGNED. Above the ceiling
	// the save is describing something the game cannot produce.
	FLBSpacecraftProductionLedgerState Impossible = Saved;
	for (FLBSpacecraftUnitState& Unit : Impossible.Units)
	{
		Unit.ConcededDefectPoints = FLBSpacecraftProductionCatalog
			::MaxConcedableDefectPoints() + 1;
	}
	TestFalse(TEXT("a concession over the ceiling is rejected"),
		Authority->ValidateLedger(Impossible, Reason));
	TestTrue(TEXT("and the refusal names the limit"),
		Reason.Contains(TEXT("OVER THE LIMIT")));

	FLBSpacecraftProductionLedgerState Negative = Saved;
	for (FLBSpacecraftUnitState& Unit : Negative.Units)
	{
		Unit.ConcededDefectPoints = -1;
	}
	TestFalse(TEXT("negative conceded defects are rejected"),
		Authority->ValidateLedger(Negative, Reason));

	World->DestroyWorld(false);
	return true;
}

IMPLEMENT_SIMPLE_AUTOMATION_TEST(FLBSpacecraftRefitPricingTest,
	"LineBoss.Spacecraft.Refit.PricedByPartsNotByTime",
	EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)

bool FLBSpacecraftRefitPricingTest::RunTest(const FString& Parameters)
{
	(void)Parameters;
	using Catalog = FLBSpacecraftProductionCatalog;

	// THE FAULT THIS TEST EXISTS FOR. The first design priced a refit
	// by the TIME it spent on the line. The fixing order is
	// expensive-first while the cycle times are expensive-LAST, so a
	// time-priced refit was paid for the long tail of the ladder while
	// buying only the cheap end of the bill of materials - worked
	// through, the WORST refit out-earned the BEST new build and made
	// seven times as much per station-second. Pricing by components
	// re-fitted is what stops that, so the property is pinned here.

	// A refit entering before ANY component is made is a whole craft's
	// work and must be priced as one.
	TestEqual(TEXT("entering at the first rung re-fits everything"),
		Catalog::RefitWorkFraction(ELBSpacecraftStage::MaterialIntake),
		1.0f);

	// Later entry can only ever be worth LESS. Monotonic, with no step
	// that goes back up - a non-monotonic curve is exactly how a later,
	// cheaper job ends up paying more than an earlier one.
	float Previous = 1.0f;
	const ELBSpacecraftStage Ladder[] = {
		ELBSpacecraftStage::MaterialIntake,
		ELBSpacecraftStage::MaterialProcessing,
		ELBSpacecraftStage::HullFabrication,
		ELBSpacecraftStage::ComponentFabrication,
		ELBSpacecraftStage::AssemblyStaging,
		ELBSpacecraftStage::Assembly };
	for (ELBSpacecraftStage Stage : Ladder)
	{
		const float Fraction = Catalog::RefitWorkFraction(Stage);
		TestTrue(TEXT("the refit share never rises as entry gets later"),
			Fraction <= Previous + KINDA_SMALL_NUMBER);
		TestTrue(TEXT("and is never negative"), Fraction >= 0.f);
		Previous = Fraction;
	}

	// A rung that re-fits nothing is worth nothing, and is refused
	// rather than sold - selling it is how the first design leaked
	// money for a craft that stood still.
	TestEqual(TEXT("nothing is refitted from assembly"),
		Catalog::RefitWorkFraction(ELBSpacecraftStage::Assembly), 0.f);
	FString Reason;
	TestFalse(TEXT("so a refit may not start at assembly"),
		Catalog::IsLegalRefitEntryStage(
			ELBSpacecraftStage::Assembly, Reason));
	TestTrue(TEXT("and the refusal says to start earlier"),
		Reason.Contains(TEXT("EARLIER")));

	TestFalse(TEXT("nor at the test gate"),
		Catalog::IsLegalRefitEntryStage(
			ELBSpacecraftStage::Testing, Reason));
	TestFalse(TEXT("nor at dispatch"),
		Catalog::IsLegalRefitEntryStage(
			ELBSpacecraftStage::Dispatched, Reason));
	TestTrue(TEXT("but hull fabrication is a legal entry"),
		Catalog::IsLegalRefitEntryStage(
			ELBSpacecraftStage::HullFabrication, Reason));

	// THE SEEDING BOUND. A craft standing at a rung has already been
	// credited with that rung's output, and is NOT paying to have it
	// done again. Off by one here either hands over a free component
	// or charges for one never received.
	FLBSpacecraftRecipe ScoutRecipe;
	TestTrue(TEXT("Scout-01 resolves for the refit bounds"),
		Catalog::FindRecipe(FName(TEXT("SCOUT-01")), ScoutRecipe));
	TArray<ELBSpacecraftComponent> Earned;
	Catalog::ComponentsEarnedBy(
		ELBSpacecraftStage::ComponentFabrication, Earned, &ScoutRecipe);
	TestEqual(TEXT("component fabrication leaves the craft complete"),
		Earned.Num(), 6);

	TArray<ELBSpacecraftComponent> Refitted;
	Catalog::ComponentsRefittedFrom(
		ELBSpacecraftStage::HullFabrication, Refitted, &ScoutRecipe);
	TestEqual(TEXT("entering at hull re-fits the five non-hull parts"),
		Refitted.Num(), 5);
	// The Cargo's bounds are its own ten kinds (2026-09-02), and a
	// Scout is never priced for them.
	FLBSpacecraftRecipe CargoRecipe;
	TestTrue(TEXT("Cargo-01 resolves for the refit bounds"),
		Catalog::FindRecipe(FName(TEXT("CARGO-01")), CargoRecipe));
	TArray<ELBSpacecraftComponent> CargoEarned;
	Catalog::ComponentsEarnedBy(
		ELBSpacecraftStage::ComponentFabrication, CargoEarned, &CargoRecipe);
	TestEqual(TEXT("a Cargo leaves fabrication with ten kinds"),
		CargoEarned.Num(), 10);
	TArray<ELBSpacecraftComponent> CargoRefitted;
	Catalog::ComponentsRefittedFrom(
		ELBSpacecraftStage::HullFabrication, CargoRefitted, &CargoRecipe);
	TestEqual(TEXT("a Cargo entering at hull re-fits nine"),
		CargoRefitted.Num(), 9);
	TestFalse(TEXT("and does NOT re-fit the hull it arrived with"),
		Refitted.Contains(ELBSpacecraftComponent::Hull));

	return true;
}

IMPLEMENT_SIMPLE_AUTOMATION_TEST(FLBSpacecraftRefitLifecycleTest,
	"LineBoss.Spacecraft.Refit.ADeliveredCraftComesBack",
	EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)

bool FLBSpacecraftRefitLifecycleTest::RunTest(const FString& Parameters)
{
	(void)Parameters;
	using namespace LBSpacecraftProductionAuthorityTestsPrivate;
	UWorld* World = MakeSpacecraftLedgerTestWorld();
	ALBSpacecraftProductionAuthority* Authority =
		World->SpawnActor<ALBSpacecraftProductionAuthority>();
	FString Reason;

	// Build and deliver a craft first - a refit is only ever offered on
	// a hull this yard actually shipped.
	TestTrue(TEXT("offer"), Authority->OfferContract(
		MakeScoutContract(TEXT("C-001"), 1), Reason));
	TestTrue(TEXT("accept"), Authority->AcceptContract(
		FName(TEXT("C-001")), Reason));
	FName UnitId;
	TestTrue(TEXT("unit creates"),
		Authority->CreateUnit(FName(TEXT("SCOUT-01")), UnitId, Reason));

	FName TooEarly;
	TestFalse(TEXT("a craft still on the line cannot be refitted"),
		Authority->OfferRefit(UnitId,
			ELBSpacecraftStage::HullFabrication, 0.0, TooEarly, Reason));
	TestTrue(TEXT("and the refusal says it is not delivered"),
		Reason.Contains(TEXT("NOT BEEN DELIVERED")));

	TestTrue(TEXT("reaches testing"),
		AdvanceSpacecraftUnitToTesting(*Authority, UnitId, Reason));
	TestTrue(TEXT("passes"),
		Authority->RecordQualityResult(UnitId, true, Reason));
	TestTrue(TEXT("dispatches"),
		Authority->AdvanceUnit(UnitId, Reason));

	// NOW it can come back.
	FName RefitId;
	TestTrue(TEXT("a delivered craft can be offered a refit"),
		Authority->OfferRefit(UnitId,
			ELBSpacecraftStage::HullFabrication, 0.0, RefitId, Reason));

	const FLBSpacecraftContract* Refit = Authority->FindContract(RefitId);
	TestNotNull(TEXT("the refit order exists"), Refit);
	if (Refit != nullptr)
	{
		TestTrue(TEXT("it knows it is a refit"), Refit->IsRefit());
		TestEqual(TEXT("one hull, one job"), Refit->Quantity, 1);
		// PRICED BELOW A NEW BUILD. A refit that out-earns the build it
		// is a subset of is the failure this whole pricing model exists
		// to prevent.
		//
		// Compared against the RECIPE's revenue, not against the test
		// fixture's contract price - the fixture invents 55,000 cr,
		// while a refit is priced off what the catalogue says a whole
		// craft is worth. Comparing to the wrong baseline is what made
		// this assertion fail the first time.
		FLBSpacecraftRecipe WholeCraft;
		TestTrue(TEXT("the recipe resolves"),
			FLBSpacecraftProductionCatalog::FindRecipe(
				FName(TEXT("SCOUT-01")), WholeCraft));
		TestTrue(TEXT("a refit is worth less than the whole craft"),
			Refit->PricePerUnitPence < WholeCraft.RevenuePence);
		TestTrue(TEXT("but is worth something"),
			Refit->PricePerUnitPence > 0);
	}

	// A hull is in the shop once.
	FName Duplicate;
	TestFalse(TEXT("a second order cannot want the same hull"),
		Authority->OfferRefit(UnitId,
			ELBSpacecraftStage::HullFabrication, 0.0, Duplicate, Reason));
	TestTrue(TEXT("and says so"), Reason.Contains(TEXT("ALREADY")));

	// THE DEMAND TRAP. A refit order must NOT make the yard start a
	// brand-new craft: the customer's ship would never be touched and
	// the player would buy a full bill of materials for a fraction of
	// the work.
	TestTrue(TEXT("accept the refit"),
		Authority->AcceptContract(RefitId, Reason));
	FName Spurious;
	TestFalse(TEXT("a refit order raises NO new-build demand"),
		Authority->CreateUnit(FName(TEXT("SCOUT-01")), Spurious, Reason));
	TestTrue(TEXT("the refusal names demand"),
		Reason.Contains(TEXT("DEMAND")));

	// The refit goes on the line as its own unit.
	FName RefitUnit;
	TestTrue(TEXT("the refit takes to the line"),
		Authority->CreateRefitUnit(RefitId, RefitUnit, Reason));

	// HOLD THE ID BEFORE ATTEMPTING THE DUPLICATE. CreateRefitUnit
	// clears its out-parameter on entry, as every fail-closed call here
	// does, so passing the same variable to the refused second attempt
	// wipes the id the rest of this test needs.
	const FName PlacedRefit = RefitUnit;
	FName Rejected;
	TestFalse(TEXT("and cannot be started twice"),
		Authority->CreateRefitUnit(RefitId, Rejected, Reason));

	const FLBSpacecraftUnitState* Back = Authority->FindUnit(PlacedRefit);
	TestNotNull(TEXT("the returned craft exists"), Back);
	if (Back != nullptr)
	{
		TestTrue(TEXT("it is a refit"), Back->IsRefit());
		TestEqual(TEXT("it names the hull that came back"),
			Back->OriginUnitId, UnitId);
		TestEqual(TEXT("it stands where it joined"), Back->Stage,
			ELBSpacecraftStage::HullFabrication);
		// SEEDED, or the assembly gate would refuse it forever.
		TestTrue(TEXT("it arrives already carrying its hull"),
			Back->ProducedComponents.Contains(
				ELBSpacecraftComponent::Hull));
		// A NEW RECORD, not a rewind: the original's quality history
		// must not be charged again against work bought separately.
		TestEqual(TEXT("its quality history starts clean"),
			Back->FailedQualityTests, 0);
		TestNotEqual(TEXT("and it is not the original unit"),
			Back->UnitId, UnitId);
	}

	// The original is untouched by any of it.
	const FLBSpacecraftUnitState* Original = Authority->FindUnit(UnitId);
	TestNotNull(TEXT("the delivered craft is still on record"), Original);
	if (Original != nullptr)
	{
		TestTrue(TEXT("still completed"), Original->bCompleted);
		TestEqual(TEXT("still dispatched"), Original->Stage,
			ELBSpacecraftStage::Dispatched);
	}

	World->DestroyWorld(false);
	return true;
}

IMPLEMENT_SIMPLE_AUTOMATION_TEST(FLBSpacecraftRefitSaveTest,
	"LineBoss.Spacecraft.Refit.OrdinaryGamesStillSave",
	EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)

bool FLBSpacecraftRefitSaveTest::RunTest(const FString& Parameters)
{
	(void)Parameters;
	using namespace LBSpacecraftProductionAuthorityTestsPrivate;
	UWorld* World = MakeSpacecraftLedgerTestWorld();
	ALBSpacecraftProductionAuthority* Authority =
		World->SpawnActor<ALBSpacecraftProductionAuthority>();
	FString Reason;

	// THE FAULT THIS TEST EXISTS FOR, found by two reviewers
	// independently. A refit invariant keyed on OriginUnitId without
	// first checking IsRefit() buckets every ORDINARY craft together
	// under the empty name. With a WIP cap of 3 and three offers on the
	// board - the opening state of a game containing no refits at all -
	// it would fire, and because saving validates BEFORE writing, the
	// player could never save. This pins the ordinary case.
	TestTrue(TEXT("offer one"), Authority->OfferContract(
		MakeScoutContract(TEXT("C-001"), 3), Reason));
	TestTrue(TEXT("offer two"), Authority->OfferContract(
		MakeScoutContract(TEXT("C-002"), 3), Reason));
	TestTrue(TEXT("offer three"), Authority->OfferContract(
		MakeScoutContract(TEXT("C-003"), 3), Reason));
	TestTrue(TEXT("accept one"), Authority->AcceptContract(
		FName(TEXT("C-001")), Reason));

	FName First;
	FName Second;
	TestTrue(TEXT("first build"),
		Authority->CreateUnit(FName(TEXT("SCOUT-01")), First, Reason));
	TestTrue(TEXT("second build"),
		Authority->CreateUnit(FName(TEXT("SCOUT-01")), Second, Reason));

	// Three offers on the board and two craft in flight, none of them
	// refits. This is the state a game is in within seconds of starting.
	FLBSpacecraftProductionLedgerState Ordinary = Authority->CaptureLedger();
	TestTrue(TEXT("AN ORDINARY GAME WITH NO REFITS STILL VALIDATES"),
		Authority->ValidateLedger(Ordinary, Reason));

	// A craft claiming an order without being a refit is incoherent -
	// the two halves of its identity disagree about what it is.
	FLBSpacecraftProductionLedgerState Mismatched = Ordinary;
	if (Mismatched.Units.Num() > 0)
	{
		Mismatched.Units[0].AssignedContractId = FName(TEXT("C-001"));
		TestFalse(TEXT("a new build assigned to an order is rejected"),
			Authority->ValidateLedger(Mismatched, Reason));
		TestTrue(TEXT("and the refusal says why"),
			Reason.Contains(TEXT("NOT A REFIT")));
	}

	// A refit naming a hull that does not exist cannot be priced or
	// delivered, so it must never restore.
	FLBSpacecraftProductionLedgerState Orphan = Ordinary;
	if (Orphan.Units.Num() > 0)
	{
		Orphan.Units[0].OriginUnitId = FName(TEXT("SCOUT-01-999999"));
		Orphan.Units[0].EntryStage = ELBSpacecraftStage::HullFabrication;
		// The STAGE has to move with the entry rung. Left at the first
		// stage, this fixture trips "stands below the stage it joined
		// at" instead - an earlier invariant - and would have proved a
		// refusal other than the one under test.
		Orphan.Units[0].Stage = ELBSpacecraftStage::HullFabrication;
		TestFalse(TEXT("a refit naming no real craft is rejected"),
			Authority->ValidateLedger(Orphan, Reason));
		TestTrue(TEXT("and says the craft does not exist"),
			Reason.Contains(TEXT("DOES NOT EXIST")));
	}

	World->DestroyWorld(false);
	return true;
}

IMPLEMENT_SIMPLE_AUTOMATION_TEST(FLBSpacecraftFactoryCeilingTest,
	"LineBoss.Spacecraft.Factory.TheCeilingNeverOverstatesTheLine",
	EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)

bool FLBSpacecraftFactoryCeilingTest::RunTest(const FString& Parameters)
{
	(void)Parameters;
	using Catalog = FLBSpacecraftProductionCatalog;
	const FVector Ceiling = Catalog::FactoryMaxCraftEnvelopeCm();

	// THE DRIFT THIS TEST EXISTS TO CATCH. The ceiling read
	// 2400 x 1400 x 700, matching the Mk2 line stations, while the
	// SPRAY BOOTH topped out at 2200 x 1250 - and the booth has no
	// larger mark. A craft between those sizes passed the factory
	// check, was told the factory was built for it, and was then
	// refused at the booth.
	//
	// Both refusals were misleading in that band: the factory one says
	// "NO STATION MARK CAN HELP" when a mark would have, and the
	// station one demands "A LARGER STATION MARK" that does not exist.
	// A ceiling that overstates the line turns a clear refusal into a
	// contradiction, which is worse than simply being conservative.
	for (const FLBSpacecraftStationDefinition& Definition :
		ALBSpacecraftBuildAuthority::StationCatalogue())
	{
		// Only stations a craft actually passes through constrain it.
		// Buildings and slot units declare a zero envelope, which means
		// "no craft stops here" rather than "nothing fits".
		if (Definition.MaxCraftEnvelopeCm.IsNearlyZero())
		{
			continue;
		}
		// A station that cannot take the ceiling is only a fault if it
		// has NO larger mark to name - the whole point of marks is that
		// a Mk1 may legitimately refuse a craft the factory allows.
		// The booth is the case that matters, because it has none.
		if (Definition.DefinitionId != FName(TEXT("SprayBooth")))
		{
			continue;
		}
		const FVector& Limit = Definition.MaxCraftEnvelopeCm;
		TestTrue(FString::Printf(
			TEXT("%s admits the ceiling length (%.0f vs %.0f)"),
			*Definition.DefinitionId.ToString(), Limit.X, Ceiling.X),
			Limit.X >= Ceiling.X);
		TestTrue(FString::Printf(
			TEXT("%s admits the ceiling width (%.0f vs %.0f)"),
			*Definition.DefinitionId.ToString(), Limit.Y, Ceiling.Y),
			Limit.Y >= Ceiling.Y);
		TestTrue(FString::Printf(
			TEXT("%s admits the ceiling height (%.0f vs %.0f)"),
			*Definition.DefinitionId.ToString(), Limit.Z, Ceiling.Z),
			Limit.Z >= Ceiling.Z);
	}

	// Every craft that ships must still fit, or the ladder has outgrown
	// the factory without anyone noticing.
	FString Reason;
	for (const TCHAR* RecipeId : { TEXT("SCOUT-01"), TEXT("CARGO-01") })
	{
		FLBSpacecraftRecipe Recipe;
		if (!Catalog::FindRecipe(FName(RecipeId), Recipe))
		{
			continue;
		}
		TestTrue(FString::Printf(TEXT("%s still fits the factory"),
			RecipeId), Catalog::ValidateCraftFitsFactory(Recipe, Reason));
	}

	// And the gantry is DERIVED from the ceiling, so it must clear it
	// with the working room the derivation promises.
	TestTrue(TEXT("the gantry span clears the widest legal craft"),
		Catalog::GantryRailSpanCm() > Ceiling.Y);

	return true;
}

// THE BROKER (2026-09-03). A finished craft with no matching order used
// to leave the player with nothing to do but wait for the offer board
// to come round to its recipe again - never a soft-lock (the board
// round-robins), but frozen capital and no move available, which is the
// opposite of what a management game should do with an awkward spot.
// The broker is the decision that replaces the waiting. What this pins
// is that it stays a LAST RESORT: taking it must always be worse than
// finding a customer, or the mechanic would quietly become the optimal
// play and orders would stop mattering.
IMPLEMENT_SIMPLE_AUTOMATION_TEST(FLBSpacecraftBrokerSaleTest,
	"LineBoss.Spacecraft.ProductionAuthority.ABrokerClearsStockAtADiscountAndNeverBeatsACustomer",
	EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)

bool FLBSpacecraftBrokerSaleTest::RunTest(const FString& Parameters)
{
	(void)Parameters;
	using namespace LBSpacecraftProductionAuthorityTestsPrivate;
	UWorld* World = MakeSpacecraftLedgerTestWorld();
	ALBSpacecraftProductionAuthority* Ledger =
		World->SpawnActor<ALBSpacecraftProductionAuthority>();
	FString Reason;
	const FName Scout(TEXT("SCOUT-01"));

	// Nothing in stock: fails closed and names why.
	int64 Paid = -1;
	TestFalse(TEXT("an empty stock sells nothing"),
		Ledger->SellStockedCraftToBroker(Scout, Paid, Reason));
	TestEqual(TEXT("and pays nothing"), Paid, (int64)0);
	TestTrue(TEXT("the refusal names the craft"),
		Reason.Contains(TEXT("SCOUT-01")));

	// A CRAFT ENDS UP IN STOCK the way it really does: its contract
	// expires while it is still being built, so it rolls off the line
	// with no order to settle against (the same path
	// WIPCapAndDeadlineExpiry pins).
	TestTrue(TEXT("offer"), Ledger->OfferContract(
		MakeScoutContract(TEXT("C-BRK"), 1, 100.0), Reason));
	TestTrue(TEXT("accept"), Ledger->AcceptContract(
		FName(TEXT("C-BRK")), Reason));
	FName UnitId;
	TestTrue(TEXT("a craft starts"),
		Ledger->CreateUnit(Scout, UnitId, Reason));
	TestTrue(TEXT("its deadline passes mid-build"),
		Ledger->AdvanceSimSeconds(150.0, Reason));
	TestTrue(TEXT("unit reaches Testing"),
		AdvanceSpacecraftUnitToTesting(*Ledger, UnitId, Reason));
	TestTrue(TEXT("hover test passes"),
		Ledger->RecordQualityResult(UnitId, true, Reason));
	TestTrue(TEXT("it still leaves the line"),
		Ledger->AdvanceUnit(UnitId, Reason));
	TestEqual(TEXT("with no order to take it, it lands in stock"),
		Ledger->GetStockedCraftCount(), 1);
	const int64 CashBefore = Ledger->GetCashPence();

	// THE OFFER IS VISIBLE BEFORE THE SALE, and it is a real discount
	// on the craft's list price - the whole trade is cash today
	// against full price later, so the player must be able to see both.
	FLBSpacecraftRecipe Recipe;
	TestTrue(TEXT("the recipe is catalogued"),
		FLBSpacecraftProductionCatalog::FindRecipe(Scout, Recipe));
	const FLBSpacecraftUnitState* Stocked = Ledger->FindUnit(UnitId);
	TestNotNull(TEXT("the stocked craft is findable"), Stocked);
	int64 Offer = 0;
	if (Stocked != nullptr)
	{
		Offer = ALBSpacecraftProductionAuthority::BrokerOfferPence(
			Scout, *Stocked);
	}
	TestTrue(TEXT("the broker offers something"), Offer > 0);
	TestTrue(TEXT("but STRICTLY LESS than the craft's list price - a "
		"clearance sale must never beat finding a customer"),
		Offer < Recipe.RevenuePence);

	// The sale itself: stock clears, cash arrives, and the money is
	// exactly what was quoted.
	TestTrue(TEXT("the broker takes it"),
		Ledger->SellStockedCraftToBroker(Scout, Paid, Reason));
	TestEqual(TEXT("paying exactly what the button said"), Paid, Offer);
	TestEqual(TEXT("stock is clear"), Ledger->GetStockedCraftCount(), 0);
	TestEqual(TEXT("and the cash arrived"),
		Ledger->GetCashPence(), CashBefore + Paid);

	// Selling the same stock twice is refused - the craft is gone.
	TestFalse(TEXT("the same craft cannot be sold twice"),
		Ledger->SellStockedCraftToBroker(Scout, Paid, Reason));

	World->DestroyWorld(false);
	return true;
}

#endif // WITH_DEV_AUTOMATION_TESTS
