// Spacecraft-era reputation authority (vision priority 2, owner-endorsed):
// the commercial ladder beside the research tree. Completed contracts earn
// reputation points; reputation TIERS gate which contract offers a player
// may accept (bigger craft need a name, not just bigger stations). Points
// are credited PER DELIVERY - the ledger is synced, never trusted twice.
// All numbers PROVISIONAL pending the owner's economy tuning.

#pragma once

#include "CoreMinimal.h"
#include "GameFramework/Actor.h"
#include "LBSpacecraftProductionAuthority.h"
#include "LBSpacecraftReputationAuthority.generated.h"

class ALBSpacecraftProductionAuthority;

/** Whole-authority snapshot for the save pipeline. */
USTRUCT(BlueprintType)
struct LINEBOSSCARFACTORY_API FLBSpacecraftReputationSnapshot
{
	GENERATED_BODY()

	UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category = "LineBoss")
	int32 Points = 0;

	/** LEGACY: contracts credited under the old
	 *  pay-once-on-completion rule. Kept so a save written then cannot
	 *  pay out a second time under the new rule. */
	UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category = "LineBoss")
	TArray<FName> CreditedContracts;

	/** Per-delivery high-water marks - reputation is earned by each
	 *  ship that arrives, not only by a finished contract. */
	UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category = "LineBoss")
	TArray<FLBSpacecraftDeliveryCredit> DeliveryCredits;

	/** Contracts already docked for running late, so a missed
	 *  deadline costs a name exactly once. */
	UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category = "LineBoss")
	TArray<FName> PenalisedContracts;
};

UCLASS()
class LINEBOSSCARFACTORY_API ALBSpacecraftReputationAuthority : public AActor
{
	GENERATED_BODY()

public:
	ALBSpacecraftReputationAuthority();

	/** Hundredths of delivered value per reputation point
	 *  (PROVISIONAL). Reputation used to be a flat two points for any
	 *  contract, so a Scout and a Cargo built your name equally - the
	 *  harder job has to count for more. */
	UPROPERTY(EditAnywhere, Category = "LineBoss")
	// Scaled x3 on 2026-08-27 alongside the craft price retune. Points
	// are delivered VALUE divided by this, so tripling what a craft
	// sells for would otherwise climb the 10/25/50 tier ladder three
	// times faster and hand the player Cargo-tier contracts after two
	// deliveries. The rate moves with the prices so the PACING stays
	// where it was tuned; the ladder thresholds are untouched.
	int64 PencePerReputationPoint = 7500000;

	/** Credits every newly Complete contract in the ledger exactly once. */
	void SyncFromLedger(const ALBSpacecraftProductionAuthority* InProduction);

	int32 GetPoints() const { return Points; }

	/** Tier 1..4 from banked points (PROVISIONAL thresholds 0/10/25/50). */
	int32 GetTier() const;
	static int32 TierForPoints(int32 InPoints);

	/** Pure: what missing a deadline costs. A name is easier to lose
	 *  than to build - failing an order costs more than delivering one
	 *  earns, and a bigger order costs more to fail. Never negative,
	 *  and reputation floors at zero: a bad run sets you back, it does
	 *  not put you in debt. PROVISIONAL. */
	int32 LatePenaltyForContract(const FLBSpacecraftContract& Contract) const;

	/** Pure: reputation earned by delivering this much value. */
	int32 PointsForDeliveredValuePence(int64 ValuePence) const;

	/** Pure: the price premium a tier commands, in percent. A name
	 *  worth having is worth paying for - without this a tier bought
	 *  nothing except permission to click the Cargo button
	 *  (PROVISIONAL: 5% a tier above the first). */
	static int32 PricePremiumPercentForTier(int32 Tier);

	/** Pure: a base price with this tier's premium applied. */
	static int64 ApplyTierPremiumPence(int64 BasePence, int32 Tier);

	FLBSpacecraftReputationSnapshot CaptureSnapshot() const;
	bool RestoreSnapshot(const FLBSpacecraftReputationSnapshot& Snapshot,
		FString& OutReason);
	static bool ValidateSnapshot(
		const FLBSpacecraftReputationSnapshot& Snapshot, FString& OutReason);

private:
	UPROPERTY(VisibleAnywhere, Category = "LineBoss")
	int32 Points = 0;

	UPROPERTY(VisibleAnywhere, Category = "LineBoss")
TArray<FName> CreditedContracts;

TArray<FLBSpacecraftDeliveryCredit> DeliveryCredits;

	TArray<FName> PenalisedContracts;
};
