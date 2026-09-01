// Spacecraft-era power budget - engine seam #3 of the Phase-2 scale-up
// (Docs/SPACECRAFT_CONTENT_CATALOGUE_v001.md section 5). Power did not
// exist at all in the car-era management layer; this is its first owner.
//
// The model is an honest BUDGET, not a brownout simulation: supplies
// (power plants) and loads (stations) register here, and a load that would
// exceed the installed supply is REFUSED with a named reason - the player
// builds more generation first. Nothing degrades silently. Removing a
// supply that live loads depend on is likewise refused; the player must
// shed load first. Per-building draw/capacity numbers stay data on the
// callers; this authority owns only the arithmetic and its invariant
// (total draw never exceeds total supply).

#pragma once

#include "CoreMinimal.h"
#include "GameFramework/Actor.h"
#include "LBSpacecraftPowerAuthority.generated.h"

/** One registered supply or load (snapshot vocabulary). */
USTRUCT(BlueprintType)
struct LINEBOSSCARFACTORY_API FLBSpacecraftPowerEntry
{
	GENERATED_BODY()

	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "LineBoss")
	FName EntryId;

	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "LineBoss")
	int32 Kilowatts = 0;
};

/** Whole-authority snapshot for the save pipeline. */
USTRUCT(BlueprintType)
struct LINEBOSSCARFACTORY_API FLBSpacecraftPowerSnapshot
{
	GENERATED_BODY()

	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "LineBoss")
	TArray<FLBSpacecraftPowerEntry> Supplies;

	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "LineBoss")
	TArray<FLBSpacecraftPowerEntry> Loads;
};

/**
 * Single-owner authority for the factory power budget. Integer kilowatts -
 * no floating-point drift in an invariant.
 */
UCLASS()
class LINEBOSSCARFACTORY_API ALBSpacecraftPowerAuthority : public AActor
{
	GENERATED_BODY()

public:
	ALBSpacecraftPowerAuthority();

	/** Adds generation. Fails closed on empty/duplicate id or non-positive
	 *  capacity. */
	bool RegisterSupply(FName SourceId, int32 CapacityKw, FString& OutReason);

	/** Removes generation - refused while the remaining supply could not
	 *  carry the live loads (shed load first; nothing browns out). */
	bool RemoveSupply(FName SourceId, FString& OutReason);

	/** Connects a load. Refused when it would exceed the installed supply -
	 *  the caller keeps the station uncommissioned and tells the player. */
	bool ConnectLoad(FName LoadId, int32 DrawKw, FString& OutReason);

	/** Disconnects a load (frees its draw). */
	bool DisconnectLoad(FName LoadId, FString& OutReason);

	/** The mains feed (owner 2026-08-26: "players should buy electric
	 *  until they buy the power plant"). A CAPPED grid connection that
	 *  is always available and METERED: every kW drawn beyond the
	 *  player's own generation is bought at the tariff. Own plants
	 *  supply first, so generation buys margin, not access. */
	UPROPERTY(EditAnywhere, Category = "LineBoss")
	int32 GridFeedKw = 800;

	/** PROVISIONAL tariff: pence per kW-minute of grid use. */
	UPROPERTY(EditAnywhere, Category = "LineBoss")
	int64 GridTariffPencePerKwMinute = 50;

	/** kW currently drawn from the mains (draw beyond own supply). */
	int32 GetGridUseKw() const;

	/** Surplus generation SOLD back to the electric company (owner
	 *  2026-08-26, the Car Manufacture model): own supply beyond the
	 *  floor's draw, capped by the same feed connection. */
	int32 GetGridExportKw() const;

	/** PROVISIONAL feed-in tariff: pence per kW-minute sold back
	 *  (half the purchase tariff - the utility's margin). */
	UPROPERTY(EditAnywhere, Category = "LineBoss")
	int64 GridSellbackPencePerKwMinute = 25;

	/** Own generation only (plants), excluding the mains feed. */
	int32 GetOwnSupplyKw() const;

	/** Meters the mains: charges the ledger for grid kW-minutes used
	 *  this tick. Whole pence are charged as they accrue; when the
	 *  ledger cannot pay, the arrears flag raises and NEW loads are
	 *  refused until it clears (existing loads stay lit - the honest
	 *  utility model is disconnection-on-renewal, not a blackout). */
	void TickGridMeter(double DeltaSeconds,
		class ALBSpacecraftProductionAuthority* InLedger);

	bool IsGridInArrears() const { return bGridArrears; }

	int32 GetTotalSupplyKw() const;
	int32 GetTotalDrawKw() const;
	int32 GetHeadroomKw() const
	{
		return GetTotalSupplyKw() - GetTotalDrawKw();
	}
	bool HasLoad(FName LoadId) const;
	int32 GetSupplyCount() const { return Supplies.Num(); }
	int32 GetLoadCount() const { return Loads.Num(); }

	FLBSpacecraftPowerSnapshot CaptureSnapshot() const;
	bool RestoreSnapshot(const FLBSpacecraftPowerSnapshot& Snapshot,
		FString& OutReason);
	// InGridFeedKw: the mains capacity the draw check may lean on.
	// Buying grid power is a LEGAL billed state (the top bar prices
	// it), so a snapshot whose draw exceeds owned supply but fits
	// under supply+feed must save and restore - the overnight soak
	// found every pre-power-plant factory refusing to save without
	// this. Default 0 keeps the raw budget arithmetic the unit tests
	// pin.
	static bool ValidateSnapshot(const FLBSpacecraftPowerSnapshot& Snapshot,
		FString& OutReason, int32 InGridFeedKw = 0);

private:
	TArray<FLBSpacecraftPowerEntry> Supplies;
	TArray<FLBSpacecraftPowerEntry> Loads;

	/** Fractional grid pence accrued but not yet charged (derived
	 *  metering state; deliberately unsaved - at most one pence of
	 *  drift across a save). */
	double GridPenceAccrued = 0.0;
	bool bGridArrears = false;

	static const FLBSpacecraftPowerEntry* FindEntry(
		const TArray<FLBSpacecraftPowerEntry>& Entries, FName EntryId);
	static int32 SumKilowatts(
		const TArray<FLBSpacecraftPowerEntry>& Entries);
};
