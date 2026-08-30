// Spacecraft-era progression authority (research doc v001, owner
// approved "implement all" 2026-08-25): the single owner of milestone
// state. Deliveries are the unlock events - contract counts open
// belts, fabrication (make-vs-buy) and QA in turn - and expansion BAYS
// are bought with credits, bay by bay, on the fixed floor. The runway
// strip is protected land and can never be bought or built over.
// Fail-closed everywhere; snapshot validates whole-or-nothing.

#pragma once

#include "CoreMinimal.h"
#include "GameFramework/Actor.h"
#include "LBSpacecraftProgressionAuthority.generated.h"

class ALBSpacecraftProductionAuthority;

UENUM(BlueprintType)
enum class ELBSpacecraftUnlock : uint8
{
	Belts = 0,
	Fabrication,
	QualityControl
};

USTRUCT()
struct LINEBOSSCARFACTORY_API FLBSpacecraftProgressionSnapshot
{
	GENERATED_BODY()

	UPROPERTY(SaveGame)
	int32 CreditedDeliveries = 0;

	UPROPERTY(SaveGame)
	TArray<FIntPoint> OwnedBays;
};

UCLASS()
class LINEBOSSCARFACTORY_API ALBSpacecraftProgressionAuthority
	: public AActor
{
	GENERATED_BODY()

public:
	ALBSpacecraftProgressionAuthority();

	// ---- milestone ladder (research: contracts ARE the unlocks) ----

	/** Deliveries needed per unlock (PROVISIONAL: belts after the 1st,
	 *  fabrication after the 2nd, QA after the 3rd). */
	UPROPERTY(EditAnywhere, Category = "LineBoss")
	int32 DeliveriesForBelts = 1;

	UPROPERTY(EditAnywhere, Category = "LineBoss")
	int32 DeliveriesForFabrication = 2;

	UPROPERTY(EditAnywhere, Category = "LineBoss")
	int32 DeliveriesForQuality = 3;

	/** Mirror of the ledger's settled contracts; monotonic. */
	void SyncFromLedger(const ALBSpacecraftProductionAuthority* InLedger);

	bool IsUnlocked(ELBSpacecraftUnlock Unlock) const;

	/** Plain-words reason a locked feature refuses, for the toasts. */
	FString DescribeLock(ELBSpacecraftUnlock Unlock) const;

	int32 GetCreditedDeliveries() const { return CreditedDeliveries; }

	// ---- expansion bays (research amended by critique: bays layer on
	// the owner's 240 m floor, no resize) ----

	/** Bay edge, cm: a 55 m bay holds a Cargo-01 station with
	 *  clearance. The 220 m buildable square is a 4 x 4 bay grid. */
	UPROPERTY(EditAnywhere, Category = "LineBoss")
	float BayEdgeCm = 5500.f;

	/** PROVISIONAL: each new bay costs this many hundredths. */
	UPROPERTY(EditAnywhere, Category = "LineBoss")
	int64 BayCostPence = 15000000; // 150,000 cr

	/** Bays inside this many cm of the +X floor edge are RUNWAY LAND
	 *  and can never be owned (the sprint corridor is protected). */
	UPROPERTY(EditAnywhere, Category = "LineBoss")
	float RunwayReserveCm = 3000.f;

	/** Grid coordinate of the bay containing a floor point. */
	FIntPoint BayForPointCm(const FVector& PointCm) const;

	bool IsBayOwned(FIntPoint Bay) const;

	/** True when the whole footprint rectangle lies in owned bays. */
	bool IsFootprintOwned(const FVector& CentreCm,
		const FVector2D& FootprintCm, FString& OutReason) const;

	/** Buys one bay, fail-closed: already owned, runway land, not
	 *  adjacent to owned land, or insufficient funds all refuse with
	 *  plain words. The charge is the last step. */
	bool PurchaseBay(FIntPoint Bay,
		ALBSpacecraftProductionAuthority* InLedger, FString& OutReason);

	int32 GetOwnedBayCount() const { return OwnedBays.Num(); }

	/** Seeds the starting land: the 2 x 3 block around the starter
	 *  spine, free of charge, once, on an unowned map. */
	bool SeedStartingBays(FString& OutReason);

	FLBSpacecraftProgressionSnapshot CaptureSnapshot() const;
	bool ValidateSnapshot(
		const FLBSpacecraftProgressionSnapshot& Snapshot,
		FString& OutReason) const;
	bool RestoreSnapshot(
		const FLBSpacecraftProgressionSnapshot& Snapshot,
		FString& OutReason);

private:
	UPROPERTY(SaveGame)
	int32 CreditedDeliveries = 0;

	UPROPERTY(SaveGame)
	TArray<FIntPoint> OwnedBays;

	bool IsRunwayLand(FIntPoint Bay) const;
	bool IsAdjacentToOwned(FIntPoint Bay) const;
};
