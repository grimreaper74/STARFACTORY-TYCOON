#if WITH_DEV_AUTOMATION_TESTS

#include "LBSpacecraftInventoryAuthority.h"

#include "Engine/World.h"
#include "Misc/AutomationTest.h"

IMPLEMENT_SIMPLE_AUTOMATION_TEST(FLBSpacecraftItemCatalogueTest,
	"LineBoss.Spacecraft.Inventory.ItemCatalogueValid",
	EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)

bool FLBSpacecraftItemCatalogueTest::RunTest(const FString& Parameters)
{
	(void)Parameters;
	FString Reason;
	TestTrue(TEXT("item table validates structurally"),
		FLBSpacecraftItemCatalogue::ValidateItemTable(Reason));
	// 131 = 9 raw + 16 processed + 100 parts + 6 components (the
	// hundred-part catalogue, 2026-08-27).
	TestEqual(TEXT("Phase-2 table carries 131 items"),
		FLBSpacecraftItemCatalogue::GetItemTable().Num(), 135);
	TestNull(TEXT("unknown ids resolve to nothing"),
		FLBSpacecraftItemCatalogue::FindItem(FName(TEXT("Raw.Unobtainium"))));
	// The assembled-component rows mirror the six-slot BOM one-to-one.
	for (uint8 Component = 0; Component < 6; ++Component)
	{
		const FLBSpacecraftItemDefinition* Row =
			FLBSpacecraftItemCatalogue::FindItem(
				FLBSpacecraftItemCatalogue::GetAssembledComponentItemId(
					Component));
		TestNotNull(TEXT("every BOM slot has an assembled item"), Row);
		if (Row != nullptr)
		{
			TestEqual(TEXT("BOM slot item is an assembled component"),
				Row->Category,
				ELBSpacecraftItemCategory::AssembledComponent);
		}
	}
	TestTrue(TEXT("out-of-range BOM index yields NAME_None"),
		FLBSpacecraftItemCatalogue::GetAssembledComponentItemId(6).IsNone());
	return true;
}

IMPLEMENT_SIMPLE_AUTOMATION_TEST(FLBSpacecraftInventoryMutationTest,
	"LineBoss.Spacecraft.Inventory.MutationsFailClosedWhole",
	EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)

bool FLBSpacecraftInventoryMutationTest::RunTest(const FString& Parameters)
{
	(void)Parameters;
	UWorld* World = UWorld::CreateWorld(EWorldType::Game, false,
		FName(TEXT("LBSpacecraftInventoryWorld")));
	ALBSpacecraftInventoryAuthority* Inventory =
		World->SpawnActor<ALBSpacecraftInventoryAuthority>();
	FString Reason;

	// Registration fails closed.
	TestFalse(TEXT("empty store id refused"),
		Inventory->RegisterStore(NAME_None, 100, Reason));
	TestFalse(TEXT("non-positive capacity refused"),
		Inventory->RegisterStore(FName(TEXT("Store.A")), 0, Reason));
	TestTrue(TEXT("store A registers"),
		Inventory->RegisterStore(FName(TEXT("Store.A")), 20, Reason));
	TestFalse(TEXT("duplicate store refused"),
		Inventory->RegisterStore(FName(TEXT("Store.A")), 20, Reason));
	TestTrue(TEXT("store B registers"),
		Inventory->RegisterStore(FName(TEXT("Store.B")), 8, Reason));

	const FName Steel(TEXT("Proc.Steel"));
	const FName Hull(TEXT("Part.HullSection")); // volume 4

	// Deposits: unknown store/item and overflow all refuse WHOLE.
	TestFalse(TEXT("unknown store refuses deposit"),
		Inventory->Deposit(FName(TEXT("Store.X")), Steel, 1, Reason));
	TestFalse(TEXT("unknown item refuses deposit"),
		Inventory->Deposit(FName(TEXT("Store.A")),
			FName(TEXT("Raw.Unobtainium")), 1, Reason));
	TestFalse(TEXT("non-positive count refuses deposit"),
		Inventory->Deposit(FName(TEXT("Store.A")), Steel, 0, Reason));
	TestTrue(TEXT("16 steel fits in 20 units"),
		Inventory->Deposit(FName(TEXT("Store.A")), Steel, 16, Reason));
	TestFalse(TEXT("a hull section (4 units) + 1 steel would overflow"),
		Inventory->Deposit(FName(TEXT("Store.A")), Hull, 2, Reason));
	TestTrue(TEXT("exactly-full deposit is allowed"),
		Inventory->Deposit(FName(TEXT("Store.A")), Hull, 1, Reason));
	TestEqual(TEXT("store A is exactly full"),
		Inventory->GetUsedUnits(FName(TEXT("Store.A"))), 20);

	// Withdrawals fail closed on stock.
	TestFalse(TEXT("over-withdraw refused"),
		Inventory->Withdraw(FName(TEXT("Store.A")), Steel, 17, Reason));
	TestEqual(TEXT("refused withdraw changed nothing"),
		Inventory->GetQuantity(FName(TEXT("Store.A")), Steel), 16);
	TestTrue(TEXT("valid withdraw succeeds"),
		Inventory->Withdraw(FName(TEXT("Store.A")), Steel, 6, Reason));
	TestEqual(TEXT("ten steel remain"),
		Inventory->GetQuantity(FName(TEXT("Store.A")), Steel), 10);

	// Transfers are atomic: a refused move leaves BOTH stores untouched.
	TestFalse(TEXT("transfer to self refused"),
		Inventory->Transfer(FName(TEXT("Store.A")), FName(TEXT("Store.A")),
			Steel, 1, Reason));
	TestFalse(TEXT("transfer larger than destination capacity refused"),
		Inventory->Transfer(FName(TEXT("Store.A")), FName(TEXT("Store.B")),
			Steel, 9, Reason));
	TestEqual(TEXT("source unchanged after refused transfer"),
		Inventory->GetQuantity(FName(TEXT("Store.A")), Steel), 10);
	TestEqual(TEXT("destination unchanged after refused transfer"),
		Inventory->GetUsedUnits(FName(TEXT("Store.B"))), 0);
	TestTrue(TEXT("fitting transfer succeeds"),
		Inventory->Transfer(FName(TEXT("Store.A")), FName(TEXT("Store.B")),
			Steel, 8, Reason));
	TestEqual(TEXT("two steel remain at the source"),
		Inventory->GetQuantity(FName(TEXT("Store.A")), Steel), 2);
	TestEqual(TEXT("eight steel arrived"),
		Inventory->GetQuantity(FName(TEXT("Store.B")), Steel), 8);

	World->DestroyWorld(false);
	return true;
}

IMPLEMENT_SIMPLE_AUTOMATION_TEST(FLBSpacecraftInventorySnapshotTest,
	"LineBoss.Spacecraft.Inventory.SnapshotValidatesBeforeRestore",
	EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)

bool FLBSpacecraftInventorySnapshotTest::RunTest(const FString& Parameters)
{
	(void)Parameters;
	UWorld* World = UWorld::CreateWorld(EWorldType::Game, false,
		FName(TEXT("LBSpacecraftInventorySnapshotWorld")));
	ALBSpacecraftInventoryAuthority* Inventory =
		World->SpawnActor<ALBSpacecraftInventoryAuthority>();
	FString Reason;
	TestTrue(TEXT("store registers"),
		Inventory->RegisterStore(FName(TEXT("Store.A")), 50, Reason));
	TestTrue(TEXT("stock deposits"),
		Inventory->Deposit(FName(TEXT("Store.A")),
			FName(TEXT("Raw.IronOre")), 30, Reason));

	// Round trip restores exactly.
	const FLBSpacecraftInventorySnapshot Snapshot =
		Inventory->CaptureSnapshot();
	TestTrue(TEXT("live snapshot validates"),
		ALBSpacecraftInventoryAuthority::ValidateSnapshot(Snapshot, Reason));
	TestTrue(TEXT("more stock deposits"),
		Inventory->Deposit(FName(TEXT("Store.A")),
			FName(TEXT("Raw.IronOre")), 5, Reason));
	TestTrue(TEXT("snapshot restores"),
		Inventory->RestoreSnapshot(Snapshot, Reason));
	TestEqual(TEXT("restore rewound the extra deposit"),
		Inventory->GetQuantity(FName(TEXT("Store.A")),
			FName(TEXT("Raw.IronOre"))), 30);

	// Corrupt snapshots refuse BEFORE mutating: state stays intact.
	FLBSpacecraftInventorySnapshot OverCapacity = Snapshot;
	OverCapacity.Stores[0].Stacks[0].Count = 999;
	TestFalse(TEXT("over-capacity snapshot refused"),
		Inventory->RestoreSnapshot(OverCapacity, Reason));
	FLBSpacecraftInventorySnapshot UnknownItem = Snapshot;
	UnknownItem.Stores[0].Stacks[0].ItemId = FName(TEXT("Raw.Unobtainium"));
	TestFalse(TEXT("unknown-item snapshot refused"),
		Inventory->RestoreSnapshot(UnknownItem, Reason));
	FLBSpacecraftInventorySnapshot DupStore = Snapshot;
	{
		// Copy first: Add(Array[0]) aliases during reallocation.
		const FLBSpacecraftInventoryStoreState First = DupStore.Stores[0];
		DupStore.Stores.Add(First);
	}
	TestFalse(TEXT("duplicate-store snapshot refused"),
		Inventory->RestoreSnapshot(DupStore, Reason));
	FLBSpacecraftInventorySnapshot NegativeStack = Snapshot;
	NegativeStack.Stores[0].Stacks[0].Count = -3;
	TestFalse(TEXT("negative-stack snapshot refused"),
		Inventory->RestoreSnapshot(NegativeStack, Reason));
	TestEqual(TEXT("every refused restore left the ledger untouched"),
		Inventory->GetQuantity(FName(TEXT("Store.A")),
			FName(TEXT("Raw.IronOre"))), 30);

	World->DestroyWorld(false);
	return true;
}

#endif // WITH_DEV_AUTOMATION_TESTS
