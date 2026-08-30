#if WITH_DEV_AUTOMATION_TESTS

#include "LBSpacecraftCraftingAuthority.h"
#include "LBSpacecraftInventoryAuthority.h"
#include "LBSpacecraftDroneFleetAuthority.h"

#include "Engine/World.h"
#include "Misc/AutomationTest.h"

IMPLEMENT_SIMPLE_AUTOMATION_TEST(FLBSpacecraftLineNeverFabricatesTest,
	"LineBoss.Spacecraft.Crafting.TheLineFitsPartsAndNeverMakesThem",
	EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)

bool FLBSpacecraftLineNeverFabricatesTest::RunTest(const FString& Parameters)
{
	(void)Parameters;
	// THE OWNER'S RULE (2026-08-27): "anything that makes parts is sub
	// assembly which goes in a different building", and "the car gets
	// parts fitted at each station and doesn't make parts".
	//
	// Nothing in the code said so, which is exactly how it got broken:
	// spreading the hundred-part catalogue across machines put 34 part
	// recipes onto the hull and component fabricators and 11 stock
	// recipes onto the material processor - all three of which are LINE
	// stations - because those stations were NAMED for fabrication. The
	// craft routes through them. Every test passed.
	//
	// A rule that only lives in a conversation gets broken by the next
	// person who reads a station's name instead of the route table.
	TSet<FName> RouteClasses;
	for (const FLBSpacecraftStageDescriptor& Row :
		FLBSpacecraftProductionCatalog::StageTable())
	{
		if (!Row.StationClassId.IsNone())
		{
			RouteClasses.Add(Row.StationClassId);
		}
	}
	TestTrue(TEXT("there is a line to protect"), RouteClasses.Num() > 0);

	int32 Offenders = 0;
	for (const FLBSpacecraftItemRecipe& Recipe :
		FLBSpacecraftRecipeCatalogue::GetRecipeTable())
	{
		if (RouteClasses.Contains(Recipe.StationClassId))
		{
			++Offenders;
			AddError(FString::Printf(
				TEXT("%s is assigned to %s, which is a LINE station - "
					"the line fits parts, it never makes them. Move it "
					"to a sub-assembly building."),
				*Recipe.RecipeId.ToString(),
				*Recipe.StationClassId.ToString()));
		}
	}
	TestEqual(TEXT("no recipe is assigned to a line station"), Offenders, 0);

	// And the converse, so this cannot be satisfied by emptying the
	// recipe table: the parts still have to be made SOMEWHERE.
	TestTrue(TEXT("the sub-assembly buildings carry the whole catalogue"),
		FLBSpacecraftRecipeCatalogue::GetRecipeTable().Num() > 100);

	return true;
}

IMPLEMENT_SIMPLE_AUTOMATION_TEST(FLBSpacecraftRecipeCatalogueTest,
	"LineBoss.Spacecraft.Crafting.RecipeCatalogueValidAndChainComplete",
	EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)

bool FLBSpacecraftRecipeCatalogueTest::RunTest(const FString& Parameters)
{
	(void)Parameters;
	FString Reason;
	TestTrue(TEXT("recipe table validates (shape + chain completeness)"),
		FLBSpacecraftRecipeCatalogue::ValidateRecipeTable(Reason));
	// 122 = 16 processed-stock recipes + 100 parts + 6 components. The
	// hundred-part catalogue landed 2026-08-27; the number is asserted
	// rather than left loose because a recipe silently vanishing is how
	// a part becomes unmakeable with nothing failing.
	TestEqual(TEXT("Phase-2 table carries 126 recipes"),
		FLBSpacecraftRecipeCatalogue::GetRecipeTable().Num(), 126);
	TestEqual(TEXT("the material processor offers twelve recipes"),
		FLBSpacecraftRecipeCatalogue::GetRecipesForStationClass(
			FName(TEXT("Smelter"))).Num(), 12);
	TestEqual(TEXT("the sub-assembly robot builds all six BOM components"),
		FLBSpacecraftRecipeCatalogue::GetRecipesForStationClass(
			FName(TEXT("SubAssemblyRobot"))).Num(), 6);
	TestEqual(TEXT("an unknown station class offers nothing"),
		FLBSpacecraftRecipeCatalogue::GetRecipesForStationClass(
			FName(TEXT("PaintBooth"))).Num(), 0);
	TestNull(TEXT("unknown recipe resolves to nothing"),
		FLBSpacecraftRecipeCatalogue::FindRecipe(
			FName(TEXT("Recipe.Unobtainium"))));
	return true;
}

IMPLEMENT_SIMPLE_AUTOMATION_TEST(FLBSpacecraftRecipeSelectionTest,
	"LineBoss.Spacecraft.Crafting.SelectionFailsClosedOnClassMismatch",
	EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)

bool FLBSpacecraftRecipeSelectionTest::RunTest(const FString& Parameters)
{
	(void)Parameters;
	UWorld* World = UWorld::CreateWorld(EWorldType::Game, false,
		FName(TEXT("LBSpacecraftCraftingSelectionWorld")));
	ALBSpacecraftCraftingAuthority* Crafting =
		World->SpawnActor<ALBSpacecraftCraftingAuthority>();
	FString Reason;
	const FName Station(TEXT("Station.MP.01"));
	const FName ProcessorClass(TEXT("Smelter"));

	TestFalse(TEXT("empty station id refused"),
		Crafting->SelectRecipe(NAME_None, ProcessorClass,
			FName(TEXT("Recipe.Steel")), Reason));
	TestFalse(TEXT("unknown recipe refused"),
		Crafting->SelectRecipe(Station, ProcessorClass,
			FName(TEXT("Recipe.Unobtainium")), Reason));
	TestFalse(TEXT("a hull recipe cannot run on a material processor"),
		Crafting->SelectRecipe(Station, ProcessorClass,
			FName(TEXT("Recipe.HullSection")), Reason));
	TestEqual(TEXT("refused selections stored nothing"),
		Crafting->GetSelectionCount(), 0);

	TestTrue(TEXT("matching recipe selects"),
		Crafting->SelectRecipe(Station, ProcessorClass,
			FName(TEXT("Recipe.Steel")), Reason));
	TestTrue(TEXT("reselecting swaps in place"),
		Crafting->SelectRecipe(Station, ProcessorClass,
			FName(TEXT("Recipe.FuelMix")), Reason));
	TestEqual(TEXT("one station still has one selection"),
		Crafting->GetSelectionCount(), 1);
	const FLBSpacecraftItemRecipe* Active =
		Crafting->GetSelectedRecipe(Station);
	TestNotNull(TEXT("active recipe resolves"), Active);
	if (Active != nullptr)
	{
		TestEqual(TEXT("active recipe is the reselection"),
			Active->RecipeId, FName(TEXT("Recipe.FuelMix")));
	}
	TestTrue(TEXT("selection clears"),
		Crafting->ClearSelection(Station, Reason));
	TestFalse(TEXT("clearing an idle station reports honestly"),
		Crafting->ClearSelection(Station, Reason));

	// Snapshot restore refuses corrupt selections before mutating.
	TestTrue(TEXT("selection returns for the snapshot"),
		Crafting->SelectRecipe(Station, ProcessorClass,
			FName(TEXT("Recipe.Steel")), Reason));
	FLBSpacecraftCraftingSnapshot Snapshot = Crafting->CaptureSnapshot();
	TestTrue(TEXT("live snapshot validates"),
		ALBSpacecraftCraftingAuthority::ValidateSnapshot(Snapshot, Reason));
	FLBSpacecraftCraftingSnapshot WrongClass = Snapshot;
	WrongClass.Selections[0].StationClassId = FName(TEXT("StructureFab"));
	TestFalse(TEXT("class-mismatched snapshot refused"),
		Crafting->RestoreSnapshot(WrongClass, Reason));
	TestNotNull(TEXT("refused restore left the selection intact"),
		Crafting->GetSelectedRecipe(Station));

	World->DestroyWorld(false);
	return true;
}

IMPLEMENT_SIMPLE_AUTOMATION_TEST(FLBSpacecraftCraftCycleTest,
	"LineBoss.Spacecraft.Crafting.CraftCycleIsAtomicOnTheLedger",
	EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)

bool FLBSpacecraftCraftCycleTest::RunTest(const FString& Parameters)
{
	(void)Parameters;
	UWorld* World = UWorld::CreateWorld(EWorldType::Game, false,
		FName(TEXT("LBSpacecraftCraftCycleWorld")));
	ALBSpacecraftCraftingAuthority* Crafting =
		World->SpawnActor<ALBSpacecraftCraftingAuthority>();
	ALBSpacecraftInventoryAuthority* Inventory =
		World->SpawnActor<ALBSpacecraftInventoryAuthority>();
	FString Reason;
	const FName In(TEXT("Store.In"));
	const FName Out(TEXT("Store.Out"));
	const FName Station(TEXT("Station.MP.01"));
	TestTrue(TEXT("input store registers"),
		Inventory->RegisterStore(In, 100, Reason));
	TestTrue(TEXT("output store registers"),
		Inventory->RegisterStore(Out, 100, Reason));

	// No recipe, then no stock: both refuse and move nothing.
	TestFalse(TEXT("idle station refuses to craft"),
		Crafting->ExecuteCraftCycle(Station, *Inventory, In, Out, Reason));
	TestTrue(TEXT("steel recipe selects"),
		Crafting->SelectRecipe(Station, FName(TEXT("Smelter")),
			FName(TEXT("Recipe.Steel")), Reason));
	// Made to order: without an order, even a stocked machine refuses.
	TestFalse(TEXT("no open order refuses the craft"),
		Crafting->ExecuteCraftCycle(Station, *Inventory, In, Out, Reason));
	TestTrue(TEXT("the refusal names the order"),
		Reason.Contains(TEXT("NO OPEN ORDER")));
	TestTrue(TEXT("an order opens"),
		Crafting->AddOrder(Station, 99, Reason));
	TestFalse(TEXT("empty input store refuses the craft whole"),
		Crafting->ExecuteCraftCycle(Station, *Inventory, In, Out, Reason));
	TestTrue(TEXT("one ore deposits"),
		Inventory->Deposit(In, FName(TEXT("Raw.IronOre")), 1, Reason));
	TestFalse(TEXT("half the inputs still refuse the craft whole"),
		Crafting->ExecuteCraftCycle(Station, *Inventory, In, Out, Reason));
	TestEqual(TEXT("refused craft consumed nothing"),
		Inventory->GetQuantity(In, FName(TEXT("Raw.IronOre"))), 1);
	TestEqual(TEXT("refused craft produced nothing"),
		Inventory->GetUsedUnits(Out), 0);

	// A valid cycle consumes the inputs and BUFFERS the outputs (owner
	// 2026-08-26: sub-assembly machines are off the line; the heavy
	// drone hauls the buffer to storage).
	TestTrue(TEXT("second ore deposits"),
		Inventory->Deposit(In, FName(TEXT("Raw.IronOre")), 1, Reason));
	TestTrue(TEXT("craft cycle runs"),
		Crafting->ExecuteCraftCycle(Station, *Inventory, In, Out, Reason));
	TestEqual(TEXT("both ores consumed"),
		Inventory->GetQuantity(In, FName(TEXT("Raw.IronOre"))), 0);
	TestEqual(TEXT("two steel buffered at the machine"),
		Crafting->GetBufferCount(Station), 2);
	TestEqual(TEXT("nothing reached the store without a haul"),
		Inventory->GetQuantity(Out, FName(TEXT("Proc.Steel"))), 0);
	int32 Moved = 0;
	TestTrue(TEXT("the haul lands the steel"),
		Crafting->TransferBufferToStore(Station, *Inventory, Out, 99,
			Moved, Reason));
	TestEqual(TEXT("two steel hauled"), Moved, 2);
	TestEqual(TEXT("the store holds the hauled steel"),
		Inventory->GetQuantity(Out, FName(TEXT("Proc.Steel"))), 2);

	// A tight store takes what fits; the remainder stays buffered
	// (partial haul is physically honest - the drone leaves the rest).
	const FName Tight(TEXT("Store.Tight"));
	TestTrue(TEXT("tight store registers (capacity 1)"),
		Inventory->RegisterStore(Tight, 1, Reason));
	TestTrue(TEXT("ore restocks the input store"),
		Inventory->Deposit(In, FName(TEXT("Raw.IronOre")), 2, Reason));
	TestTrue(TEXT("another cycle buffers two more steel"),
		Crafting->ExecuteCraftCycle(Station, *Inventory, In, Out, Reason));
	TestTrue(TEXT("the tight haul still reports moved items"),
		Crafting->TransferBufferToStore(Station, *Inventory, Tight, 99,
			Moved, Reason));
	TestEqual(TEXT("only one steel fit the tight store"), Moved, 1);
	TestEqual(TEXT("the remainder stays buffered"),
		Crafting->GetBufferCount(Station), 1);
	TestTrue(TEXT("the partial haul names the full store"),
		Reason.Contains(TEXT("FULL")));

	World->DestroyWorld(false);
	return true;
}

IMPLEMENT_SIMPLE_AUTOMATION_TEST(FLBSpacecraftCraftingChainTest,
	"LineBoss.Spacecraft.Crafting.RawChainBuildsAHullComponent",
	EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)

bool FLBSpacecraftCraftingChainTest::RunTest(const FString& Parameters)
{
	(void)Parameters;
	// Integration proof that the DATA works, not just the mechanism: can
	// raw ore actually become an assembled Hull component?
	//
	// This PLANS the build and then executes the plan, rather than
	// running the factory forward and hoping. Two earlier attempts are
	// worth recording because both looked reasonable:
	//
	//  - A hand-written list of steps and quantities. Fine at nine
	//    steps; the hundred-part catalogue made it four levels deep, and
	//    every number would need recomputing by hand on every recipe
	//    change. That is the arithmetic nobody redoes and everybody
	//    trusts.
	//  - Firing every satisfiable recipe each round until a hull
	//    appeared. Looks like a fair simulation, is not: Proc.Steel has
	//    fourteen consumers and one producer, so it is eaten the instant
	//    it exists and the structural path starves, while Part.WiringLoom
	//    - which almost nothing consumes - climbs into the hundreds. A
	//    scheduling artefact of the test, mistakable for a data fault.
	//
	// Planning backwards from the target has neither problem, and it is
	// also what a player does.
	UWorld* World = UWorld::CreateWorld(EWorldType::Game, false,
		FName(TEXT("LBSpacecraftCraftingChainWorld")));
	ALBSpacecraftCraftingAuthority* Crafting =
		World->SpawnActor<ALBSpacecraftCraftingAuthority>();
	ALBSpacecraftInventoryAuthority* Inventory =
		World->SpawnActor<ALBSpacecraftInventoryAuthority>();
	FString Reason;
	const FName Floor(TEXT("Store.Floor"));
	TestTrue(TEXT("floor store registers"),
		Inventory->RegisterStore(Floor, 1000000, Reason));

	const FName Target(TEXT("Component.Hull"));

	// --- plan: the catalogue's own backwards planner (promoted from
	// this test on 2026-08-27 - the shape was proven here first, and a
	// "what do I need to build X" list is gameplay, not test scaffolding).
	TMap<FName, int32> Targets;
	Targets.Add(Target, 1);
	TArray<FLBSpacecraftPlannedRun> Plan;
	TMap<FName, int32> RawNeed;
	TestTrue(TEXT("the catalogue plans the hull"),
		FLBSpacecraftRecipeCatalogue::PlanBuild(Targets, Plan, RawNeed,
			Reason));
	TestTrue(TEXT("a hull pulls a real chain behind it"), Plan.Num() > 20);

	// Whatever raws the plan asked for, stocked with headroom.
	for (const TPair<FName, int32>& Want : RawNeed)
	{
		TestTrue(*FString::Printf(TEXT("%s stocks"), *Want.Key.ToString()),
			Inventory->Deposit(Floor, Want.Key, Want.Value + 8, Reason));
	}
	TestTrue(TEXT("the hull is made of raw materials"), RawNeed.Num() >= 4);

	// --- execute: deepest first, which is the plan in reverse ---
	for (int32 Index = Plan.Num() - 1; Index >= 0; --Index)
	{
		const FLBSpacecraftPlannedRun& Run = Plan[Index];
		const FName StationId(*FString::Printf(TEXT("St.%s"),
			*Run.RecipeId.ToString()));
		FString Step;
		if (!TestTrue(*FString::Printf(TEXT("%s selects"),
				*Run.RecipeId.ToString()),
			Crafting->SelectRecipe(StationId, Run.StationClassId,
				Run.RecipeId, Step)))
		{
			continue;
		}
		TestTrue(*FString::Printf(TEXT("%s orders %d"),
				*Run.RecipeId.ToString(), Run.Cycles),
			Crafting->AddOrder(StationId, Run.Cycles, Step));
		for (int32 Cycle = 0; Cycle < Run.Cycles; ++Cycle)
		{
			if (!Crafting->ExecuteCraftCycle(StationId, *Inventory, Floor,
				Floor, Step))
			{
				AddError(FString::Printf(TEXT("%s cycle %d refused: %s"),
					*Run.RecipeId.ToString(), Cycle, *Step));
				break;
			}
			// The buffer is drained every cycle: it is small, and a full
			// buffer refuses the next craft whole.
			int32 Moved = 0;
			Crafting->TransferBufferToStore(StationId, *Inventory, Floor,
				99, Moved, Step);
		}
	}

	TestEqual(TEXT("raw ore becomes exactly one Hull component"),
		Inventory->GetQuantity(Floor, Target), 1);

	// The other five components must be makeable too - a chain that
	// closes for the hull and dead-ends for the interior cannot build a
	// craft, and testing only the hull would not notice.
	for (uint8 Index = 0; Index < 6; ++Index)
	{
		const FName ComponentItem =
			FLBSpacecraftItemCatalogue::GetAssembledComponentItemId(Index);
		bool bMade = false;
		for (const FLBSpacecraftItemRecipe& Recipe :
			FLBSpacecraftRecipeCatalogue::GetRecipeTable())
		{
			for (const FLBSpacecraftItemStack& Out : Recipe.Outputs)
			{
				bMade |= (Out.ItemId == ComponentItem);
			}
		}
		TestTrue(*FString::Printf(TEXT("%s is made by some recipe"),
			*ComponentItem.ToString()), bMade);
	}

	World->DestroyWorld(false);
	return true;
}

IMPLEMENT_SIMPLE_AUTOMATION_TEST(FLBSpacecraftTimedCraftingTest,
	"LineBoss.Spacecraft.Crafting.TimedCyclesAccrueOnlyWhilePayable",
	EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)

bool FLBSpacecraftTimedCraftingTest::RunTest(const FString& Parameters)
{
	(void)Parameters;
	UWorld* World = UWorld::CreateWorld(EWorldType::Game, false,
		FName(TEXT("LBSpacecraftTimedCraftWorld")));
	ALBSpacecraftCraftingAuthority* Crafting =
		World->SpawnActor<ALBSpacecraftCraftingAuthority>();
	ALBSpacecraftInventoryAuthority* Inventory =
		World->SpawnActor<ALBSpacecraftInventoryAuthority>();
	FString Reason;
	int32 Cycles = 0;
	const FName Floor(TEXT("Store.Floor"));
	const FName Station(TEXT("Station.MP.01"));
	TestTrue(TEXT("store registers"),
		Inventory->RegisterStore(Floor, 200, Reason));
	TestTrue(TEXT("steel recipe selects (8 s cycle)"),
		Crafting->SelectRecipe(Station, FName(TEXT("Smelter")),
			FName(TEXT("Recipe.Steel")), Reason));
	TestTrue(TEXT("a standing order opens"),
		Crafting->AddOrder(Station, 99, Reason));

	// Structural failures return false.
	TestFalse(TEXT("non-positive sim time refused"),
		Crafting->TickCrafting(Station, 0.0, *Inventory, Floor, Floor,
			Cycles, Reason));
	TestFalse(TEXT("an idle station refuses the tick"),
		Crafting->TickCrafting(FName(TEXT("Station.Idle")), 5.0, *Inventory,
			Floor, Floor, Cycles, Reason));

	// A starved station STALLS: no progress banked, no items moved.
	TestTrue(TEXT("starved tick reports a stall"),
		Crafting->TickCrafting(Station, 20.0, *Inventory, Floor, Floor,
			Cycles, Reason));
	TestEqual(TEXT("stall completes nothing"), Cycles, 0);
	TestTrue(TEXT("stall names the shortage"),
		Reason.Contains(TEXT("STALLED")));
	TestEqual(TEXT("stall banks no progress"),
		Crafting->GetCycleElapsedSeconds(Station), 0.0);

	// With materials, time accrues and the cycle completes at 8 s.
	TestTrue(TEXT("ore deposits"),
		Inventory->Deposit(Floor, FName(TEXT("Raw.IronOre")), 4, Reason));
	TestTrue(TEXT("5 s tick runs"),
		Crafting->TickCrafting(Station, 5.0, *Inventory, Floor, Floor,
			Cycles, Reason));
	TestEqual(TEXT("mid-cycle completes nothing"), Cycles, 0);
	TestEqual(TEXT("no items move mid-cycle"),
		Crafting->GetBufferCount(Station), 0);
	TestTrue(TEXT("4 s tick crosses the boundary"),
		Crafting->TickCrafting(Station, 4.0, *Inventory, Floor, Floor,
			Cycles, Reason));
	TestEqual(TEXT("exactly one cycle completed"), Cycles, 1);
	TestEqual(TEXT("the outputs landed in the machine buffer"),
		Crafting->GetBufferCount(Station), 2);
	TestEqual(TEXT("the remainder carries (9-8=1 s)"),
		Crafting->GetCycleElapsedSeconds(Station), 1.0);

	// A long tick completes what it can pay for, then stalls at the
	// boundary: 2 ore left = one more cycle, however much time passes.
	TestTrue(TEXT("30 s tick runs"),
		Crafting->TickCrafting(Station, 30.0, *Inventory, Floor, Floor,
			Cycles, Reason));
	TestEqual(TEXT("only the payable cycle completed"), Cycles, 1);
	TestEqual(TEXT("four steel buffered total"),
		Crafting->GetBufferCount(Station), 4);
	TestEqual(TEXT("ore is exhausted"),
		Inventory->GetQuantity(Floor, FName(TEXT("Raw.IronOre"))), 0);

	// Snapshot: an impossible cycle clock is refused before mutation.
	FLBSpacecraftCraftingSnapshot Snapshot = Crafting->CaptureSnapshot();
	TestTrue(TEXT("live snapshot validates"),
		ALBSpacecraftCraftingAuthority::ValidateSnapshot(Snapshot, Reason));
	FLBSpacecraftCraftingSnapshot BadClock = Snapshot;
	BadClock.Selections[0].CycleElapsedSeconds = 999.0;
	TestFalse(TEXT("over-cycle clock snapshot refused"),
		Crafting->RestoreSnapshot(BadClock, Reason));

	World->DestroyWorld(false);
	return true;
}


IMPLEMENT_SIMPLE_AUTOMATION_TEST(FLBSpacecraftSubAssemblyBufferTest,
	"LineBoss.Spacecraft.Crafting.BufferFillsStallsAndHauls",
	EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)

bool FLBSpacecraftSubAssemblyBufferTest::RunTest(const FString& Parameters)
{
	(void)Parameters;
	UWorld* World = UWorld::CreateWorld(EWorldType::Game, false,
		FName(TEXT("LBSpacecraftBufferWorld")));
	ALBSpacecraftCraftingAuthority* Crafting =
		World->SpawnActor<ALBSpacecraftCraftingAuthority>();
	ALBSpacecraftInventoryAuthority* Inventory =
		World->SpawnActor<ALBSpacecraftInventoryAuthority>();
	FString Reason;
	const FName Floor(TEXT("Store.Floor"));
	const FName Station(TEXT("Station.MP.01"));
	TestTrue(TEXT("store registers"),
		Inventory->RegisterStore(Floor, 200, Reason));
	TestTrue(TEXT("ore deposits"),
		Inventory->Deposit(Floor, FName(TEXT("Raw.IronOre")), 20, Reason));
	TestTrue(TEXT("steel selects"),
		Crafting->SelectRecipe(Station, FName(TEXT("Smelter")),
			FName(TEXT("Recipe.Steel")), Reason));
	// Made to order: exactly TWO cycles are ordered here - the third
	// refuses with the order named even though ore and buffer allow it.
	TestTrue(TEXT("a two-cycle order opens"),
		Crafting->AddOrder(Station, 2, Reason));
	for (int32 Cycle = 0; Cycle < 2; ++Cycle)
	{
		TestTrue(TEXT("ordered cycle crafts"),
			Crafting->ExecuteCraftCycle(Station, *Inventory, Floor,
				Floor, Reason));
	}
	TestFalse(TEXT("the exhausted order refuses the third cycle"),
		Crafting->ExecuteCraftCycle(Station, *Inventory, Floor, Floor,
			Reason));
	TestTrue(TEXT("the refusal names the order"),
		Reason.Contains(TEXT("NO OPEN ORDER")));
	int32 Drained = 0;
	TestTrue(TEXT("the order-test buffer drains"),
		Crafting->TransferBufferToStore(Station, *Inventory, Floor, 99,
			Drained, Reason));
	TestTrue(TEXT("a fresh standing order opens"),
		Crafting->AddOrder(Station, 99, Reason));

	// The buffer fills to capacity (2 steel per cycle, capacity 6 =
	// three cycles), then the machine stalls FAIL-CLOSED, named.
	for (int32 Cycle = 0; Cycle < 3; ++Cycle)
	{
		TestTrue(TEXT("cycle crafts into the buffer"),
			Crafting->ExecuteCraftCycle(Station, *Inventory, Floor,
				Floor, Reason));
	}
	TestEqual(TEXT("buffer at capacity"),
		Crafting->GetBufferCount(Station), Crafting->BufferCapacity);
	TestFalse(TEXT("a full buffer refuses the next cycle"),
		Crafting->ExecuteCraftCycle(Station, *Inventory, Floor, Floor,
			Reason));
	TestTrue(TEXT("the refusal names the pickup"),
		Reason.Contains(TEXT("AWAITING DRONE PICKUP")));

	// The heavy drone's run empties the buffer via the fleet authority
	// and the machine resumes.
	ALBSpacecraftDroneFleetAuthority* Fleet =
		World->SpawnActor<ALBSpacecraftDroneFleetAuthority>();
	ALBSpacecraftBuildAuthority* Build =
		World->SpawnActor<ALBSpacecraftBuildAuthority>();

		// EVERY factory is built INSIDE a ship factory (owner
		// 2026-08-28). The hall is the player's first move on the
		// world map, so the fixtures take it too.
		{
			FName SpacecraftTestHallId;
			FString SpacecraftTestHallReason;
			Build->PlaceStarterHall(SpacecraftTestHallId,
				SpacecraftTestHallReason);
		}
	FName RackId;
	TestTrue(TEXT("rack places"),
		Build->PlaceStation(FName(TEXT("StorageRack")),
			FTransform(FRotator::ZeroRotator,
				FVector(-4000.f, 0.f, 0.f)), RackId, Reason));
	Fleet->SyncFromBuild(Build, nullptr);
	TestEqual(TEXT("one hauler per rack"), Fleet->GetHauls().Num(), 1);
	// Idle -> ToMachine -> ToStore -> transfer: two travel legs.
	const int32 SteelBeforeHaul =
		Inventory->GetQuantity(Floor, FName(TEXT("Proc.Steel")));
	Fleet->TickHauls(0.1, Crafting, Inventory);
	TestEqual(TEXT("the hauler launched at the fullest buffer"),
		Fleet->GetHauls()[0].MachineStationId, Station);
	Fleet->TickHauls(Fleet->HaulTravelSeconds + 0.1, Crafting, Inventory);
	Fleet->TickHauls(Fleet->HaulTravelSeconds + 0.1, Crafting, Inventory);
	TestEqual(TEXT("the haul moved a full load to the store"),
		Inventory->GetQuantity(Floor, FName(TEXT("Proc.Steel")))
			- SteelBeforeHaul,
		Fleet->HaulCapacity);
	TestEqual(TEXT("the remainder stays buffered"),
		Crafting->GetBufferCount(Station),
		Crafting->BufferCapacity - Fleet->HaulCapacity);
	TestTrue(TEXT("the machine crafts again"),
		Crafting->ExecuteCraftCycle(Station, *Inventory, Floor, Floor,
			Reason));

	// Buffered items survive the save pipeline.
	FLBSpacecraftCraftingSnapshot Snapshot = Crafting->CaptureSnapshot();
	TestTrue(TEXT("buffered snapshot validates"),
		ALBSpacecraftCraftingAuthority::ValidateSnapshot(Snapshot,
			Reason));
	TestTrue(TEXT("buffered snapshot restores"),
		Crafting->RestoreSnapshot(Snapshot, Reason));
	TestEqual(TEXT("the buffer survived the roundtrip"),
		Crafting->GetBufferCount(Station), 4);

	World->DestroyWorld(false);
	return true;
}

#endif // WITH_DEV_AUTOMATION_TESTS
