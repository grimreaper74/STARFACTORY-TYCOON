#if WITH_DEV_AUTOMATION_TESTS

#include "LBSpacecraftCommandPanelWidget.h"
#include "LBSpacecraftProductionAuthority.h"
#include "LBSpacecraftGameMode.h"
#include "LBSpacecraftPlayerPawn.h"
#include "LBSpacecraftObjectivesWidget.h"

#include "Misc/AutomationTest.h"

IMPLEMENT_SIMPLE_AUTOMATION_TEST(FLBSpacecraftSectionViewTest,
	"LineBoss.Spacecraft.UI.SectionsBelongToExactlyOneView",
	EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)

bool FLBSpacecraftSectionViewTest::RunTest(const FString& Parameters)
{
	(void)Parameters;
	using Panel = ULBSpacecraftCommandPanelWidget;
	using Section = Panel::EBuildSection;

	// OUTSIDE and INSIDE are different games and their menus never mix.
	// A screenshot of the opening site caught the world map drawing
	// "THE LINE - WHO FITS WHAT" and a track-laying menu over a plot
	// with no factory entered. The rule had been applied to the
	// building catalogue and assumed everywhere else - the same shape
	// of fault as the view gate that shipped a build which could not
	// be started at all.
	TestTrue(TEXT("the line's fixing split is an INSIDE thing"),
		Panel::SectionBelongsInView(Section::FixingSplit, false));
	TestFalse(TEXT("and never appears on the world map"),
		Panel::SectionBelongsInView(Section::FixingSplit, true));

	TestTrue(TEXT("track is laid INSIDE a factory"),
		Panel::SectionBelongsInView(Section::Track, false));
	TestFalse(TEXT("and never on the world map"),
		Panel::SectionBelongsInView(Section::Track, true));

	// The opposite gate, and worth pinning so it cannot be "fixed" into
	// matching the two above: a bay is site land, chosen by adjacency
	// on a plot the player has to be able to see.
	TestTrue(TEXT("land is bought OUTSIDE, where the plot is"),
		Panel::SectionBelongsInView(Section::Land, true));
	TestFalse(TEXT("and not from inside a building"),
		Panel::SectionBelongsInView(Section::Land, false));

	// Both views own a catalogue; the definitions decide its contents.
	TestTrue(TEXT("the catalogue shows outside"),
		Panel::SectionBelongsInView(Section::Catalogue, true));
	TestTrue(TEXT("and inside"),
		Panel::SectionBelongsInView(Section::Catalogue, false));

	// NOTHING BELONGS TO BOTH except the catalogue. A section drawn in
	// both views is the bug this test exists for, so assert the shape
	// rather than only the cases.
	const Section Exclusive[] = {
		Section::FixingSplit, Section::Track, Section::Land };
	for (Section Which : Exclusive)
	{
		TestNotEqual(TEXT("an exclusive section shows in one view only"),
			Panel::SectionBelongsInView(Which, true),
			Panel::SectionBelongsInView(Which, false));
	}
	return true;
}

IMPLEMENT_SIMPLE_AUTOMATION_TEST(FLBSpacecraftSplitShiftTest,
	"LineBoss.Spacecraft.UI.SplitShiftMovesExactlyOnePart",
	EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)

bool FLBSpacecraftSplitShiftTest::RunTest(const FString& Parameters)
{
	(void)Parameters;
	// The split UI's whole arithmetic: one part, one boundary, or
	// nothing. A refused move returns EMPTY rather than a clamp,
	// because a clamped move looks like it worked.
	using Panel = ULBSpacecraftCommandPanelWidget;
	const TArray<int32> Counts = { 2, 2, 1, 1 };

	TArray<int32> Given = Panel::ComputeSplitShift(Counts, 0, 1);
	TestEqual(TEXT("give moves one down"), Given,
		TArray<int32>({ 1, 3, 1, 1 }));
	TArray<int32> Taken = Panel::ComputeSplitShift(Counts, 1, 0);
	TestEqual(TEXT("take moves one up"), Taken,
		TArray<int32>({ 3, 1, 1, 1 }));
	int32 Total = 0;
	for (int32 Count : Given)
	{
		Total += Count;
	}
	TestEqual(TEXT("no part appears or vanishes"), Total, 6);

	TestEqual(TEXT("an empty slice refuses to give"),
		Panel::ComputeSplitShift({ 0, 6 }, 0, 1).Num(), 0);
	TestEqual(TEXT("off the line refuses"),
		Panel::ComputeSplitShift(Counts, 3, 4).Num(), 0);
	TestEqual(TEXT("a two-station jump refuses"),
		Panel::ComputeSplitShift(Counts, 0, 2).Num(), 0);
	TestEqual(TEXT("a move to itself refuses"),
		Panel::ComputeSplitShift(Counts, 1, 1).Num(), 0);
	return true;
}

IMPLEMENT_SIMPLE_AUTOMATION_TEST(FLBSpacecraftUIPureTest,
	"LineBoss.Spacecraft.UI.PlacementAndLabelMathsAreExact",
	EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)

bool FLBSpacecraftUIPureTest::RunTest(const FString& Parameters)
{
	(void)Parameters;
	// Grid snapping: to the 100 cm grid, on the floor datum.
	const FVector Snapped = ALBSpacecraftPlayerPawn::SnapToBuildGrid(
		FVector(137.f, -263.f, 50.f), 100.f);
	TestEqual(TEXT("X snaps to the nearest 100"), Snapped.X, 100.0);
	TestEqual(TEXT("Y snaps to the nearest 100"), Snapped.Y, -300.0);
	TestEqual(TEXT("Z is forced to the floor datum"), Snapped.Z, 0.0);

	// Footprint picking honours the station's rotation.
	const FTransform Rotated(FRotator(0.f, 90.f, 0.f),
		FVector(1000.f, 0.f, 0.f));
	const FVector2D Footprint(1400.f, 900.f); // long axis now along Y
	TestTrue(TEXT("a point along the rotated long axis is inside"),
		ALBSpacecraftPlayerPawn::StationContainsPoint(Rotated, Footprint,
			FVector(1000.f, 650.f, 0.f)));
	TestFalse(TEXT("the unrotated long axis is now the short one"),
		ALBSpacecraftPlayerPawn::StationContainsPoint(Rotated, Footprint,
			FVector(1650.f, 0.f, 0.f)));

	// Labels read from the real catalogues.
	const FString Mill = ULBSpacecraftCommandPanelWidget::
		BuildStationButtonLabel(FName(TEXT("RollingMill")));
	TestTrue(TEXT("the mill label carries name, price and draw"),
		Mill.Contains(TEXT("Rolling mill")) && Mill.Contains(TEXT("60,000"))
		&& Mill.Contains(TEXT("400 kW")));
	const FString Plant = ULBSpacecraftCommandPanelWidget::
		BuildStationButtonLabel(FName(TEXT("PowerPlant")));
	TestTrue(TEXT("the plant label shows its supply"),
		Plant.Contains(TEXT("+1500 kW")));
	TestTrue(TEXT("an unknown definition yields an empty label"),
		ULBSpacecraftCommandPanelWidget::BuildStationButtonLabel(
			FName(TEXT("NoSuchStation"))).IsEmpty());
	const FString Mk2Locked = ULBSpacecraftCommandPanelWidget::
		BuildResearchButtonLabel(FName(TEXT("Research.Mfg.Mk2")), false);
	const FString Mk2Done = ULBSpacecraftCommandPanelWidget::
		BuildResearchButtonLabel(FName(TEXT("Research.Mfg.Mk2")), true);
	TestTrue(TEXT("a locked node shows its cost"),
		Mk2Locked.Contains(TEXT("(60 pts)")));
	TestTrue(TEXT("an unlocked node says so"),
		Mk2Done.Contains(TEXT("UNLOCKED")));
	return true;
}

IMPLEMENT_SIMPLE_AUTOMATION_TEST(FLBSpacecraftObjectiveLineTest,
	"LineBoss.Spacecraft.UI.ObjectiveLinesReadTheLadder",
	EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)

bool FLBSpacecraftObjectiveLineTest::RunTest(const FString& Parameters)
{
	(void)Parameters;
	TestEqual(TEXT("open objective counts progress"),
		ULBSpacecraftObjectivesWidget::BuildObjectiveLine(1, 3,
			TEXT("QUALITY CONTROL")),
		FString(TEXT("1/3 · QUALITY CONTROL")));
	TestEqual(TEXT("met objective shows the check glyph"),
		ULBSpacecraftObjectivesWidget::BuildObjectiveLine(3, 3,
			TEXT("QUALITY CONTROL")),
		FString(TEXT("✓ QUALITY CONTROL")));
	TestEqual(TEXT("overdelivery still shows the check glyph"),
		ULBSpacecraftObjectivesWidget::BuildObjectiveLine(9, 1,
			TEXT("CONVEYOR BELTS")),
		FString(TEXT("✓ CONVEYOR BELTS")));
	return true;
}

#endif // WITH_DEV_AUTOMATION_TESTS

IMPLEMENT_SIMPLE_AUTOMATION_TEST(FLBSpacecraftHeldContractLineTest,
	"LineBoss.Spacecraft.UI.TheContractsTabShowsWhatYouHold",
	EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)

bool FLBSpacecraftHeldContractLineTest::RunTest(const FString& Parameters)
{
	(void)Parameters;
	using Panel = ULBSpacecraftCommandPanelWidget;

	FLBSpacecraftContract Contract;
	Contract.ContractId = FName(TEXT("SC-CONTRACT-001"));
	Contract.RecipeId = FName(TEXT("SCOUT-01"));
	Contract.Quantity = 3;
	Contract.DispatchedCount = 1;
	Contract.PricePerUnitPence = 5250000;
	Contract.State = ELBSpacecraftContractState::Accepted;

	const FString Building = Panel::BuildHeldContractLine(Contract);
	TestTrue(TEXT("the line names the craft"),
		Building.Contains(TEXT("SCOUT-01")));
	TestTrue(TEXT("it shows progress against the order"),
		Building.Contains(TEXT("1/3")));
	TestTrue(TEXT("it shows what the contract actually pays, premium and all"),
		Building.Contains(TEXT("52,500 cr")));
	TestTrue(TEXT("and that it is being built"),
		Building.Contains(TEXT("BUILDING")));

	// A late contract must read as late, not as merely building.
	Contract.State = ELBSpacecraftContractState::Expired;
	const FString Late = Panel::BuildHeldContractLine(Contract);
	TestTrue(TEXT("an expired contract reads LATE"),
		Late.Contains(TEXT("LATE")));
	TestFalse(TEXT("and no longer reads as in progress"),
		Late.Contains(TEXT("BUILDING")));

	// An offer that has not been taken says so.
	Contract.State = ELBSpacecraftContractState::Offered;
	TestTrue(TEXT("an untaken offer reads OFFERED"),
		Panel::BuildHeldContractLine(Contract).Contains(TEXT("OFFERED")));
	return true;
}

IMPLEMENT_SIMPLE_AUTOMATION_TEST(FLBSpacecraftOfferBoardTest,
	"LineBoss.Spacecraft.UI.TheOfferBoardOffersRealTerms",
	EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)

bool FLBSpacecraftOfferBoardTest::RunTest(const FString& Parameters)
{
	(void)Parameters;
	using Mode = ALBSpacecraftGameMode;

	// The board spreads quantity so the choice is about what the line
	// can carry, not a free multiplier.
	TArray<int32> Quantities;
	for (int32 Slot = 0; Slot < Mode::OfferBoardSize; ++Slot)
	{
		Quantities.AddUnique(Mode::OfferQuantityForSlot(Slot));
	}
	TestTrue(TEXT("the board offers more than one size of order"),
		Quantities.Num() > 1);
	TestTrue(TEXT("every offer is for at least one craft"),
		Mode::OfferQuantityForSlot(0) >= 1
		&& Mode::OfferQuantityForSlot(2) >= 1);
	TestTrue(TEXT("a negative slot still yields a real quantity"),
		Mode::OfferQuantityForSlot(-1) >= 1);

	// Bulk pays less per craft than a one-off - that is the trade.
	const int64 Base = 5000000;
	const int64 Single = Mode::OfferUnitPricePence(Base, 1, 1);
	const int64 Bulk = Mode::OfferUnitPricePence(Base, 4, 1);
	TestTrue(TEXT("a one-off pays a premium per craft"), Single > Base);
	TestTrue(TEXT("a bulk order pays less per craft"), Bulk < Base);
	TestTrue(TEXT("but bulk is still worth more in total"),
		Bulk * 4 > Single * 1);
	TestEqual(TEXT("a worthless recipe stays worthless"),
		Mode::OfferUnitPricePence(0, 2, 3), static_cast<int64>(0));

	// Reputation rides on top of the quantity terms.
	TestTrue(TEXT("a trusted yard is offered more for the same work"),
		Mode::OfferUnitPricePence(Base, 2, 3)
			> Mode::OfferUnitPricePence(Base, 2, 1));

	// The button says what the player is agreeing to.
	FLBSpacecraftContract Offer;
	Offer.ContractId = FName(TEXT("SC-CONTRACT-007"));
	Offer.RecipeId = FName(TEXT("SCOUT-01"));
	Offer.Quantity = 4;
	Offer.PricePerUnitPence = 4700000;
	Offer.State = ELBSpacecraftContractState::Offered;
	const FString Label =
		ULBSpacecraftCommandPanelWidget::BuildOfferButtonLabel(Offer);
	TestTrue(TEXT("the label names the craft"),
		Label.Contains(TEXT("SCOUT-01")));
	TestTrue(TEXT("and the quantity"), Label.Contains(TEXT("x4")));
	TestTrue(TEXT("and the unit price"), Label.Contains(TEXT("47,000 cr")));
	TestTrue(TEXT("and what the whole order is worth"),
		Label.Contains(TEXT("188,000 cr")));
	return true;
}

IMPLEMENT_SIMPLE_AUTOMATION_TEST(FLBSpacecraftContractCustomerTest,
	"LineBoss.Spacecraft.UI.EveryOrderComesFromSomebody",
	EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)

bool FLBSpacecraftContractCustomerTest::RunTest(const FString& Parameters)
{
	(void)Parameters;
	using Panel = ULBSpacecraftCommandPanelWidget;

	// The customer list itself: real names, real liveries, no
	// duplicates - the colours are what each craft will eventually
	// wear, so two customers sharing one would read as a bug.
	const TArray<FLBSpacecraftCustomer>& Customers =
		FLBSpacecraftCustomerCatalogue::GetCustomers();
	TestTrue(TEXT("there is a customer list"), Customers.Num() > 1);
	TSet<FName> SeenIds;
	for (const FLBSpacecraftCustomer& Customer : Customers)
	{
		TestFalse(TEXT("every customer has an id"),
			Customer.CustomerId.IsNone());
		TestFalse(TEXT("and a name to show"),
			Customer.DisplayName.IsEmpty());
		bool bAlready = false;
		SeenIds.Add(Customer.CustomerId, &bAlready);
		TestFalse(TEXT("no customer is listed twice"), bAlready);
	}

	// The board cycles through them rather than asking one buyer for
	// everything, and it is deterministic so a reload rebuilds the
	// same board.
	TestEqual(TEXT("the same slot always names the same customer"),
		FLBSpacecraftCustomerCatalogue::CustomerForIndex(3).CustomerId,
		FLBSpacecraftCustomerCatalogue::CustomerForIndex(3).CustomerId);
	TestNotEqual(TEXT("successive offers come from different buyers"),
		FLBSpacecraftCustomerCatalogue::CustomerForIndex(0).CustomerId,
		FLBSpacecraftCustomerCatalogue::CustomerForIndex(1).CustomerId);
	TestFalse(TEXT("a wild index still names somebody"),
		FLBSpacecraftCustomerCatalogue::CustomerForIndex(-7)
			.CustomerId.IsNone());

	// And the player is told who wants the craft, on the offer and on
	// the order they took.
	FLBSpacecraftContract Offer;
	Offer.ContractId = FName(TEXT("SC-CONTRACT-100"));
	Offer.RecipeId = FName(TEXT("SCOUT-01"));
	Offer.Quantity = 2;
	Offer.PricePerUnitPence = 5000000;
	Offer.State = ELBSpacecraftContractState::Offered;
	Offer.CustomerId = Customers[0].CustomerId;
	const FString Label = Panel::BuildOfferButtonLabel(Offer);
	TestTrue(TEXT("the offer names its customer"),
		Label.Contains(Customers[0].DisplayName));

	Offer.State = ELBSpacecraftContractState::Accepted;
	TestTrue(TEXT("so does the order you took"),
		Panel::BuildHeldContractLine(Offer)
			.Contains(Customers[0].DisplayName));

	// An unknown customer must not blank the line - the order still
	// reads, it just has no name on it.
	Offer.CustomerId = FName(TEXT("Customer.Nobody"));
	TestTrue(TEXT("an unknown customer still leaves a readable line"),
		Panel::BuildHeldContractLine(Offer).Contains(TEXT("SCOUT-01")));
	return true;
}

IMPLEMENT_SIMPLE_AUTOMATION_TEST(FLBSpacecraftBuildMenuGroupingTest,
	"LineBoss.Spacecraft.UI.NothingIsFiledWhereNobodyWouldLookForIt",
	EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)

bool FLBSpacecraftBuildMenuGroupingTest::RunTest(const FString& Parameters)
{
	(void)Parameters;
	using Panel = ULBSpacecraftCommandPanelWidget;
	using Build = ALBSpacecraftBuildAuthority;

	// The build menu used to group by a hardcoded list of ids, so every
	// building added after it was written filed itself under CRAFTING
	// CHAIN - the delivery dock, the power station and the sub-assembly
	// hall all ended up somewhere nobody would look. The grouping is
	// derived now, and this is what stops it rotting again.
	auto GroupOf = [](const TCHAR* Id)
	{
		const FLBSpacecraftStationDefinition* Definition =
			Build::FindDefinition(FName(Id));
		return Definition != nullptr ? Panel::BuildMenuGroupFor(*Definition)
			: -1;
	};

	TestEqual(TEXT("a line station is on the production line"),
		GroupOf(TEXT("MaterialProcessor")), 0);
	TestEqual(TEXT("its bigger mark is a heavy mark"),
		GroupOf(TEXT("MaterialProcessorMk2")), 1);
	TestEqual(TEXT("a parts machine is in the crafting chain"),
		GroupOf(TEXT("RollingMill")), 2);
	TestEqual(TEXT("its bigger mark is a heavy mark too"),
		GroupOf(TEXT("RollingMillMk2")), 1);

	// The three that were misfiled.
	TestEqual(TEXT("the delivery dock is infrastructure"),
		GroupOf(TEXT("DeliveryDock")), 3);
	TestEqual(TEXT("so is the power station"),
		GroupOf(TEXT("PowerStation")), 4);
	// The parts factory and the power plant are WORLD-MAP buildings
	// now (owner 2026-08-28), so they file under the site with the
	// ship factory rather than under interior infrastructure.
	TestEqual(TEXT("and the parts factory"),
		GroupOf(TEXT("SubAssemblyHall")), 4);
	TestEqual(TEXT("and storage, as it always was"),
		GroupOf(TEXT("StorageRack")), 3);

	// Nothing anywhere may land in a group that does not exist, and
	// nothing that crafts nothing may sit in the crafting chain.
	for (const FLBSpacecraftStationDefinition& Definition :
		Build::StationCatalogue())
	{
		const int32 Group = Panel::BuildMenuGroupFor(Definition);
		// Group 4 is THE SITE - the world map's own catalogue
		// (owner 2026-08-28).
		TestTrue(TEXT("every definition lands in a real group"),
			Group >= 0 && Group <= 4);
		TestEqual(TEXT("site buildings file under the site"),
			Definition.bSiteBuilding, Group == 4);
		if (Group == 2)
		{
			TestTrue(TEXT("only real parts machines sit in the chain"),
				FLBSpacecraftRecipeCatalogue::GetRecipesForStationClass(
					Definition.GetRecipeClassId()).Num() > 0);
		}
		if (Group == 0)
		{
			TestFalse(TEXT("only route stations sit on the line"),
				Definition.StageClassId.IsNone());
		}
	}
	return true;
}

IMPLEMENT_SIMPLE_AUTOMATION_TEST(FLBSpacecraftStockVisibleTest,
	"LineBoss.Spacecraft.UI.FinishedStockIsVisibleToThePlayer",
	EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)

bool FLBSpacecraftStockVisibleTest::RunTest(const FString& Parameters)
{
	(void)Parameters;
	using Panel = ULBSpacecraftCommandPanelWidget;

	// A craft built to stock fills the next matching order instantly,
	// so knowing you have one is the difference between an offer being
	// work and an offer being free money.
	const FString Line =
		Panel::BuildFinishedStockLine(FName(TEXT("SCOUT-01")), 2);
	TestTrue(TEXT("the line names the craft"),
		Line.Contains(TEXT("SCOUT-01")));
	TestTrue(TEXT("and how many are standing"), Line.Contains(TEXT("x2")));
	TestTrue(TEXT("and that they are ready to sell"),
		Line.Contains(TEXT("READY TO SELL")));

	// No stock, no line - an empty section would be noise.
	TestTrue(TEXT("no stock shows nothing"),
		Panel::BuildFinishedStockLine(FName(TEXT("SCOUT-01")), 0)
			.IsEmpty());
	TestTrue(TEXT("and a nonsense count shows nothing either"),
		Panel::BuildFinishedStockLine(FName(TEXT("SCOUT-01")), -3)
			.IsEmpty());
	return true;
}
