// Spacecraft-era item/inventory ledger - engine seam #1 of the Phase-2
// scale-up (Docs/SPACECRAFT_CONTENT_CATALOGUE_v001.md section 5).
//
// One authority owns every item quantity in the factory, keyed by store.
// Stations and logistics NEVER hold their own private counts - they request
// deposits, withdrawals and transfers here, and every mutation can fail
// closed with a named reason. This is the seam the later multi-recipe
// stations, conveyors and AGV logistics all attach to: a recipe becomes
// pure data (inputs withdrawn, outputs deposited) instead of per-station
// buffer code.
//
// The item catalogue is a DATA TABLE like the stage table: content scale-up
// means adding rows, and the table is validated (unique ids, sane volumes,
// the six assembled components mirroring ELBSpacecraftComponent) rather
// than trusted.

#pragma once

#include "CoreMinimal.h"
#include "GameFramework/Actor.h"
#include "LBSpacecraftInventoryAuthority.generated.h"

/** Where an item sits in the production chain. */
UENUM(BlueprintType)
enum class ELBSpacecraftItemCategory : uint8
{
	Raw = 0,
	Processed,
	SubPart,
	AssembledComponent
};

/** One row of the item catalogue. */
USTRUCT(BlueprintType)
struct LINEBOSSCARFACTORY_API FLBSpacecraftItemDefinition
{
	GENERATED_BODY()

	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "LineBoss")
	FName ItemId;

	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "LineBoss")
	FString DisplayName;

	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "LineBoss")
	ELBSpacecraftItemCategory Category = ELBSpacecraftItemCategory::Raw;

	/** Storage units ONE item occupies. Capacity maths never divides. */
	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "LineBoss")
	int32 UnitVolume = 1;
};

/** A quantity of one item inside a store (snapshot vocabulary). */
USTRUCT(BlueprintType)
struct LINEBOSSCARFACTORY_API FLBSpacecraftItemStack
{
	GENERATED_BODY()

	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "LineBoss")
	FName ItemId;

	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "LineBoss")
	int32 Count = 0;
};

/** One store's full state (snapshot vocabulary). */
USTRUCT(BlueprintType)
struct LINEBOSSCARFACTORY_API FLBSpacecraftInventoryStoreState
{
	GENERATED_BODY()

	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "LineBoss")
	FName StoreId;

	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "LineBoss")
	int32 CapacityUnits = 0;

	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "LineBoss")
	TArray<FLBSpacecraftItemStack> Stacks;
};

/** One inbound resource order: raws bought with cash, arriving on the
 *  sim clock (the ATT-inspired mirror of outbound contracts). */
USTRUCT(BlueprintType)
struct LINEBOSSCARFACTORY_API FLBSpacecraftResourceOrder
{
	GENERATED_BODY()

	UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category = "LineBoss")
	FName OrderId;

	UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category = "LineBoss")
	FName ItemId;

	UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category = "LineBoss")
	int32 Count = 0;

	UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category = "LineBoss")
	FName StoreId;

	UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category = "LineBoss")
	double ArrivesAtSeconds = 0.0;
};

/** Whole-ledger snapshot for the save pipeline. */
USTRUCT(BlueprintType)
struct LINEBOSSCARFACTORY_API FLBSpacecraftInventorySnapshot
{
	GENERATED_BODY()

	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "LineBoss")
	TArray<FLBSpacecraftInventoryStoreState> Stores;

	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "LineBoss")
	TArray<FLBSpacecraftResourceOrder> Orders;

	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "LineBoss")
	double OrderClockSeconds = 0.0;
};

/** Static item catalogue: the Phase-2 slice of the ~70-item chain. */
class LINEBOSSCARFACTORY_API FLBSpacecraftItemCatalogue
{
public:
	/** The frozen Phase-2 item table (raw, processed, sub-part, component). */
	static const TArray<FLBSpacecraftItemDefinition>& GetItemTable();

	/** nullptr when the id is not in the table. */
	static const FLBSpacecraftItemDefinition* FindItem(FName ItemId);

	/** Structural validation of the table itself. */
	static bool ValidateItemTable(FString& OutReason);

	/** The assembled-component item id for a BOM component enumerator. */
	static FName GetAssembledComponentItemId(uint8 ComponentIndex);

	/** Purchase price per unit for RAW items (PROVISIONAL economy
	 *  numbers); 0 for anything that cannot be bought - only raws are. */
	static int64 GetRawItemPricePence(FName ItemId);

	/** Make-vs-buy (research doc v001): every sub-part can be IMPORTED
	 *  at the dock for a premium instead of fabricated on-site.
	 *  PROVISIONAL prices; 0 = not importable. */
	static int64 GetItemImportPricePence(FName ItemId);

	/** Purchase price for an order: raw price, else import price. */
	static int64 GetOrderablePricePence(FName ItemId);

	/** Delivery lead time for an order (PROVISIONAL: 30 s + 2 s per
	 *  10 units). */
	static double GetOrderLeadSeconds(int32 Count);
};

/**
 * Single-owner authority for every item quantity in the factory.
 * Mutations validate first and fail closed whole - a deposit that does not
 * fit deposits nothing, a transfer that cannot complete moves nothing.
 */
UCLASS()
class LINEBOSSCARFACTORY_API ALBSpacecraftInventoryAuthority : public AActor
{
	GENERATED_BODY()

public:
	ALBSpacecraftInventoryAuthority();

	/** Creates an empty store. Fails closed on duplicate id, empty id or a
	 *  non-positive capacity. */
	bool RegisterStore(FName StoreId, int32 CapacityUnits, FString& OutReason);

	/** Removes a store. Refused while it still holds ANY items - removal
	 *  never destroys stock; empty it first. */
	bool RemoveStore(FName StoreId, FString& OutReason);

	/** Adds Count items to a store; fails closed when the store or item is
	 *  unknown, the count is non-positive, or the volume does not fit. */
	bool Deposit(FName StoreId, FName ItemId, int32 Count, FString& OutReason);

	/** Removes Count items; fails closed on unknown store/item, non-positive
	 *  count or insufficient stock. */
	bool Withdraw(FName StoreId, FName ItemId, int32 Count,
		FString& OutReason);

	/** Atomic move: both sides validated before either mutates. */
	bool Transfer(FName FromStoreId, FName ToStoreId, FName ItemId,
		int32 Count, FString& OutReason);

	int32 GetQuantity(FName StoreId, FName ItemId) const;
	int32 GetUsedUnits(FName StoreId) const;
	int32 GetCapacityUnits(FName StoreId) const;
	int32 GetStoreCount() const { return Stores.Num(); }
	/** True once anything at all has arrived in any store - the
	 *  objectives panel's "parts ordered" step. */
	bool HasAnyStock() const;

	/** Every registered store id, in registration order. */
	TArray<FName> GetStoreIds() const;

	/** How many WHOLE ITEMS of this kind a store still has room for.
	 *  Capacity is measured in units and a component is several units,
	 *  so a hauler that counts in items must ask this before it loads -
	 *  otherwise it arrives with more than will fit and the transfer is
	 *  refused whole, silently. */
	int32 GetRoomForItems(FName StoreId, FName ItemId) const;

	/** Resizes a store. Refuses to shrink below what it already holds -
	 *  goods are never squeezed out of existence. */
	bool SetStoreCapacity(FName StoreId, int32 CapacityUnits,
		FString& OutReason);
	bool HasStore(FName StoreId) const;

	/** Places an inbound order (cash is charged by the CALLER - the game
	 *  mode pairs this with the production ledger). Fails closed on
	 *  non-raw items, bad counts, or an unknown destination store. */
	bool PlaceOrder(FName ItemId, int32 Count, FName StoreId,
		FName& OutOrderId, FString& OutReason);

	/** Advances the order clock; arrived orders deposit into their store
	 *  (an over-full store holds the delivery until space frees - the
	 *  goods never vanish). */
	void TickOrders(double DeltaSeconds);

	const TArray<FLBSpacecraftResourceOrder>& GetPendingOrders() const
	{
		return Orders;
	}
	double GetOrderClockSeconds() const { return OrderClockSeconds; }

	/** Save-pipeline surface: capture is always legal; restore validates the
	 *  ENTIRE snapshot before a single mutation. */
	FLBSpacecraftInventorySnapshot CaptureSnapshot() const;
	bool RestoreSnapshot(const FLBSpacecraftInventorySnapshot& Snapshot,
		FString& OutReason);

	/** Pure snapshot validation, exposed so save code can pre-flight. */
	static bool ValidateSnapshot(const FLBSpacecraftInventorySnapshot& Snapshot,
		FString& OutReason);

private:
	/** Store order follows registration; lookups are by id. Stack arrays
	 *  hold only positive counts of known items. */
	TArray<FLBSpacecraftInventoryStoreState> Stores;

	TArray<FLBSpacecraftResourceOrder> Orders;
	double OrderClockSeconds = 0.0;
	int32 NextOrderSequence = 1;

	FLBSpacecraftInventoryStoreState* FindStore(FName StoreId);
	const FLBSpacecraftInventoryStoreState* FindStore(FName StoreId) const;
	static int32 UsedUnitsOf(const FLBSpacecraftInventoryStoreState& Store);
};
