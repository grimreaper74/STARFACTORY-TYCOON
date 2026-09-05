#if WITH_DEV_AUTOMATION_TESTS

#include "LBSpacecraftProductionTypes.h"
#include "LBSpacecraftInventoryAuthority.h"
#include "LBSpacecraftCraftingAuthority.h"

#include "Misc/AutomationTest.h"

IMPLEMENT_SIMPLE_AUTOMATION_TEST(FLBSpacecraftStageTableValidTest,
	"LineBoss.Spacecraft.Production.StageTableValid",
	EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)

bool FLBSpacecraftStageTableValidTest::RunTest(const FString& Parameters)
{
	(void)Parameters;
	FString Error;
	TestTrue(TEXT("stage table validates"),
		FLBSpacecraftProductionCatalog::ValidateStageTable(Error));
	TestTrue(TEXT("no error text on success"), Error.IsEmpty());
	// Route length is derived from the table - the car-era hard-coded 57
	// lesson. Six station-served stages: Testing is station-less now
	// (the self-start at the line end IS the test, owner 2026-08-26).
	TestEqual(TEXT("station stage count derives from the table"),
		FLBSpacecraftProductionCatalog::StationStageCount(), 6);
	TestTrue(TEXT("Testing is the quality gate"),
		FLBSpacecraftProductionCatalog::IsQualityGate(
			ELBSpacecraftStage::Testing));
	TestFalse(TEXT("Assembly is not a quality gate"),
		FLBSpacecraftProductionCatalog::IsQualityGate(
			ELBSpacecraftStage::Assembly));
	return true;
}

IMPLEMENT_SIMPLE_AUTOMATION_TEST(FLBSpacecraftSerialFlowTest,
	"LineBoss.Spacecraft.Production.SerialFlowAndTerminalStage",
	EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)

bool FLBSpacecraftSerialFlowTest::RunTest(const FString& Parameters)
{
	(void)Parameters;
	FLBSpacecraftRecipe Scout;
	TestTrue(TEXT("Scout-01 recipe exists"),
		FLBSpacecraftProductionCatalog::FindRecipe(
			FName(TEXT("SCOUT-01")), Scout));

	FLBSpacecraftUnitState Unit;
	Unit.UnitId = FName(TEXT("SCOUT-01-000001"));
	Unit.RecipeId = Scout.RecipeId;

	// A unit walks the whole serial flow, one stage at a time, to Dispatched.
	FString Reason;
	int32 Steps = 0;
	while (FLBSpacecraftProductionCatalog::AdvanceUnit(Unit, Scout, Reason))
	{
		++Steps;
		if (Steps > 32)
		{
			AddError(TEXT("advance did not terminate"));
			return false;
		}
	}
	TestEqual(TEXT("unit ends Dispatched"), Unit.Stage,
		ELBSpacecraftStage::Dispatched);
	TestTrue(TEXT("unit reports completed"), Unit.bCompleted);
	TestEqual(TEXT("seven advances to terminal"), Steps, 7);
	TestEqual(TEXT("all six components earned"),
		Unit.ProducedComponents.Num(), 6);

	// Terminal stage refuses further movement, with a reason.
	TestFalse(TEXT("terminal unit cannot advance"),
		FLBSpacecraftProductionCatalog::AdvanceUnit(Unit, Scout, Reason));
	TestFalse(TEXT("terminal refusal carries a reason"), Reason.IsEmpty());
	return true;
}

IMPLEMENT_SIMPLE_AUTOMATION_TEST(FLBSpacecraftAssemblyGateTest,
	"LineBoss.Spacecraft.Production.AssemblyRequiresCompleteComponentSet",
	EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)

bool FLBSpacecraftAssemblyGateTest::RunTest(const FString& Parameters)
{
	(void)Parameters;
	FLBSpacecraftRecipe Scout;
	TestTrue(TEXT("Scout-01 recipe exists"),
		FLBSpacecraftProductionCatalog::FindRecipe(
			FName(TEXT("SCOUT-01")), Scout));

	// Fabricate a unit standing at AssemblyStaging with an incomplete BOM
	// (Hull missing - as if HullFabrication had been skipped).
	FLBSpacecraftUnitState Unit;
	Unit.UnitId = FName(TEXT("SCOUT-01-000002"));
	Unit.RecipeId = Scout.RecipeId;
	Unit.Stage = ELBSpacecraftStage::AssemblyStaging;
	Unit.ProducedComponents = {
		ELBSpacecraftComponent::Electronics, ELBSpacecraftComponent::Power,
		ELBSpacecraftComponent::Propulsion, ELBSpacecraftComponent::Navigation,
		ELBSpacecraftComponent::Interior };

	FString Reason;
	TestFalse(TEXT("assembly rejects an incomplete component set"),
		FLBSpacecraftProductionCatalog::CanEnterStage(Unit, Scout,
			ELBSpacecraftStage::Assembly, Reason));
	TestTrue(TEXT("rejection names the component gate"),
		Reason.Contains(TEXT("COMPLETE COMPONENT SET")));

	Unit.ProducedComponents.Add(ELBSpacecraftComponent::Hull);
	TestTrue(TEXT("assembly accepts a complete component set"),
		FLBSpacecraftProductionCatalog::CanEnterStage(Unit, Scout,
			ELBSpacecraftStage::Assembly, Reason));

	// Stage skipping is illegal even with a complete BOM.
	TestFalse(TEXT("skipping straight to Testing is rejected"),
		FLBSpacecraftProductionCatalog::CanEnterStage(Unit, Scout,
			ELBSpacecraftStage::Testing, Reason));
	TestTrue(TEXT("skip rejection names serial flow"),
		Reason.Contains(TEXT("SERIAL FLOW ONLY")));
	return true;
}

IMPLEMENT_SIMPLE_AUTOMATION_TEST(FLBSpacecraftFixingOrderTest,
	"LineBoss.Spacecraft.Production.FixingOrderIsTheBuildSequence",
	EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)

bool FLBSpacecraftFixingOrderTest::RunTest(const FString& Parameters)
{
	(void)Parameters;
	using Catalog = FLBSpacecraftProductionCatalog;

	const TArray<FLBSpacecraftRecipe>& Recipes = Catalog::CanonicalRecipes();
	TestTrue(TEXT("there are recipes to check"), Recipes.Num() > 0);

	for (const FLBSpacecraftRecipe& Recipe : Recipes)
	{
		const FString Name = Recipe.RecipeId.ToString();
		FString Error;
		TestTrue(*FString::Printf(TEXT("%s has a valid fixing order"), *Name),
			Catalog::ValidateFixingOrder(Recipe, Error));

		// The shell comes first. Everything else is fitted INTO it, so a
		// sequence that starts anywhere else is not a build sequence.
		TestTrue(*FString::Printf(TEXT("%s fits the hull first"), *Name),
			Recipe.FixingOrder.Num() > 0
				&& Recipe.FixingOrder[0] == ELBSpacecraftComponent::Hull);

		// The sequence covers the requirements exactly - the property
		// that makes the two lists safe to keep separate.
		TestEqual(*FString::Printf(TEXT("%s fits every part it requires"),
			*Name), Recipe.FixingOrder.Num(),
			Recipe.RequiredComponents.Num());

		// Item ids resolve, in order, with no gaps.
		const TArray<FName> Sequence = Catalog::FixingSequenceItemIds(Recipe);
		TestEqual(*FString::Printf(TEXT("%s sequence resolves to items"),
			*Name), Sequence.Num(), Recipe.FixingOrder.Num());
		for (int32 Index = 0; Index < Sequence.Num(); ++Index)
		{
			TestEqual(*FString::Printf(TEXT("%s item %d knows its place"),
				*Name, Index),
				Catalog::FixingIndexOf(Recipe, Sequence[Index]), Index);
		}
		TestEqual(*FString::Printf(
			TEXT("%s does not fit a part it never heard of"), *Name),
			Catalog::FixingIndexOf(Recipe, FName(TEXT("Item.NotAPart"))),
			(int32)INDEX_NONE);
	}

	// Internals are shared across craft tiers, and until 2026-09-02 so
	// was the whole sequence. The Cargo made the deliberate decision
	// this comment used to reserve: it carries kinds of its own and
	// fits them in its own order. What still holds for every tier is
	// that it STARTS like the Scout - shell, powerplant, engines - and
	// fits every kind the Scout fits.
	if (Recipes.Num() >= 2)
	{
		for (int32 Index = 1; Index < Recipes.Num(); ++Index)
		{
			const TArray<ELBSpacecraftComponent>& First =
				Recipes[0].FixingOrder;
			const TArray<ELBSpacecraftComponent>& Later =
				Recipes[Index].FixingOrder;
			bool bSameStart = Later.Num() >= 3 && First.Num() >= 3;
			for (int32 Step = 0; bSameStart && Step < 3; ++Step)
			{
				bSameStart = Later[Step] == First[Step];
			}
			bool bCoversFirst = true;
			for (ELBSpacecraftComponent Kind : First)
			{
				bCoversFirst &= Later.Contains(Kind);
			}
			TestTrue(*FString::Printf(
				TEXT("%s starts like %s and fits everything it fits"),
				*Recipes[Index].RecipeId.ToString(),
				*Recipes[0].RecipeId.ToString()),
				bSameStart && bCoversFirst);
		}
	}

	// The validator has to reject each way the two lists can drift apart,
	// because every one of them fails SILENTLY at runtime: a part never
	// fitted, or a part allocated that never arrives.
	FLBSpacecraftRecipe Broken = Recipes[0];
	FString Error;
	Broken.FixingOrder.Empty();
	TestFalse(TEXT("an empty fixing order is refused"),
		Catalog::ValidateFixingOrder(Broken, Error));
	TestTrue(TEXT("and says so"), Error.Contains(TEXT("FIXING ORDER")));

	Broken = Recipes[0];
	// Through a LOCAL, not Add(FixingOrder[0]): passing a reference into
	// the array being grown trips UE's aliasing assertion when the Add
	// reallocates. It is checked, so it crashes rather than corrupting -
	// but it crashes the whole run, not just this test.
	const ELBSpacecraftComponent Duplicate = Broken.FixingOrder[0];
	Broken.FixingOrder.Add(Duplicate);
	TestFalse(TEXT("fitting the same part twice is refused"),
		Catalog::ValidateFixingOrder(Broken, Error));

	Broken = Recipes[0];
	Broken.FixingOrder.RemoveAt(Broken.FixingOrder.Num() - 1);
	TestFalse(TEXT("leaving a required part unfitted is refused"),
		Catalog::ValidateFixingOrder(Broken, Error));

	Broken = Recipes[0];
	Broken.RequiredComponents.Remove(ELBSpacecraftComponent::Interior);
	TestFalse(TEXT("fitting a part the recipe does not use is refused"),
		Catalog::ValidateFixingOrder(Broken, Error));

	// And a recipe carrying a broken sequence must fail WHOLE-recipe
	// validation too, or the guard only protects code that thinks to ask.
	Broken = Recipes[0];
	Broken.FixingOrder.Empty();
	TestFalse(TEXT("recipe validation refuses a broken fixing order"),
		Catalog::ValidateRecipe(Broken, Error));

	return true;
}

IMPLEMENT_SIMPLE_AUTOMATION_TEST(FLBSpacecraftRecipeValidationTest,
	"LineBoss.Spacecraft.Production.RecipeValidationFailsClosed",
	EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)

bool FLBSpacecraftRecipeValidationTest::RunTest(const FString& Parameters)
{
	(void)Parameters;
	FString Error;
	for (const FLBSpacecraftRecipe& Recipe :
		FLBSpacecraftProductionCatalog::CanonicalRecipes())
	{
		TestTrue(FString::Printf(TEXT("canonical recipe %s validates"),
			*Recipe.RecipeId.ToString()),
			FLBSpacecraftProductionCatalog::ValidateRecipe(Recipe, Error));
	}

	// Missing cycle time -> rejected with the stage named.
	FLBSpacecraftRecipe Broken;
	TestTrue(TEXT("Scout-01 recipe exists"),
		FLBSpacecraftProductionCatalog::FindRecipe(
			FName(TEXT("SCOUT-01")), Broken));
	Broken.NominalCycleSeconds.Remove(ELBSpacecraftStage::Testing);
	TestFalse(TEXT("recipe without a Testing cycle time is rejected"),
		FLBSpacecraftProductionCatalog::ValidateRecipe(Broken, Error));
	TestTrue(TEXT("rejection names the missing stage"),
		Error.Contains(TEXT("Testing")));

	// Zero revenue -> rejected.
	FLBSpacecraftRecipe Free;
	FLBSpacecraftProductionCatalog::FindRecipe(FName(TEXT("SCOUT-01")), Free);
	Free.RevenuePence = 0;
	TestFalse(TEXT("recipe without revenue is rejected"),
		FLBSpacecraftProductionCatalog::ValidateRecipe(Free, Error));
	return true;
}

IMPLEMENT_SIMPLE_AUTOMATION_TEST(FLBSpacecraftCargoTenComponentsTest,
	"LineBoss.Spacecraft.Production.TheCargoCarriesTenKindsEachBackedByRealParts",
	EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)

bool FLBSpacecraftCargoTenComponentsTest::RunTest(const FString& Parameters)
{
	(void)Parameters;
	// Owner 2026-09-02: the line grows by components per craft, and a
	// visible feature must be wired into the parts catalogue. The Cargo
	// tier carries ten kinds; every one is an item with an import price
	// and a sub-assembly recipe that produces it, the fixing order
	// covers them and the plating goes on last.
	FLBSpacecraftRecipe Cargo;
	TestTrue(TEXT("Cargo-01 resolves"),
		FLBSpacecraftProductionCatalog::FindRecipe(FName(TEXT("CARGO-01")),
			Cargo));
	TestEqual(TEXT("ten kinds"), Cargo.RequiredComponents.Num(), 10);
	FString Error;
	TestTrue(TEXT("its fixing order validates"),
		FLBSpacecraftProductionCatalog::ValidateFixingOrder(Cargo, Error));
	TestEqual(TEXT("the plating goes on last"),
		Cargo.FixingOrder.Last(), ELBSpacecraftComponent::Shielding);
	const TArray<FLBSpacecraftItemRecipe>& Recipes =
		FLBSpacecraftRecipeCatalogue::GetRecipeTable();
	for (ELBSpacecraftComponent Kind : Cargo.RequiredComponents)
	{
		const FName ItemId =
			FLBSpacecraftItemCatalogue::GetAssembledComponentItemId(
				static_cast<uint8>(Kind));
		TestFalse(TEXT("every kind maps to an item id"), ItemId.IsNone());
		const FLBSpacecraftItemDefinition* Row =
			FLBSpacecraftItemCatalogue::FindItem(ItemId);
		TestTrue(*FString::Printf(TEXT("%s is an assembled component row"),
			*ItemId.ToString()), Row != nullptr && Row->Category
				== ELBSpacecraftItemCategory::AssembledComponent);
		TestTrue(*FString::Printf(TEXT("%s has an import price"),
			*ItemId.ToString()),
			FLBSpacecraftItemCatalogue::GetItemImportPricePence(ItemId) > 0);
		bool bMade = false;
		for (const FLBSpacecraftItemRecipe& Recipe : Recipes)
		{
			for (const FLBSpacecraftItemStack& Output : Recipe.Outputs)
			{
				bMade |= Output.ItemId == ItemId;
			}
		}
		TestTrue(*FString::Printf(TEXT("%s has a recipe that makes it"),
			*ItemId.ToString()), bMade);
	}
	// The Scout is untouched: six kinds, and its loadout is its own.
	FLBSpacecraftRecipe Scout;
	TestTrue(TEXT("Scout-01 resolves"),
		FLBSpacecraftProductionCatalog::FindRecipe(FName(TEXT("SCOUT-01")),
			Scout));
	TestEqual(TEXT("the Scout keeps six"), Scout.RequiredComponents.Num(), 6);
	FString TableReason;
	TestTrue(TEXT("the item table still validates"),
		FLBSpacecraftItemCatalogue::ValidateItemTable(TableReason));
	return true;
}

#endif // WITH_DEV_AUTOMATION_TESTS
