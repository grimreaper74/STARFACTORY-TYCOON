// Spacecraft-era research unlocks - the last Phase-2 engine seam (one
// branch for early access; Docs/SPACECRAFT_CONTENT_CATALOGUE_v001.md
// sections 3 and 5). Unlocks open CONTENT (station families and their
// recipes), never stat bonuses - the owner's plan is explicit about that.
//
// The Manufacturing branch gates the six Phase-2 station families added by
// the crafting seam: the slice's original five families are free, and each
// research tier opens the next rung of the chain. The node table is
// validated like every other catalogue: unique ids, prerequisites that
// exist AND appear earlier in the table (structurally acyclic), unlocks
// that name real recipe-catalogue station classes.

#pragma once

#include "CoreMinimal.h"
#include "GameFramework/Actor.h"
#include "LBSpacecraftProductionAuthority.h"
#include "LBSpacecraftResearchAuthority.generated.h"

/** One research node. */
USTRUCT(BlueprintType)
struct LINEBOSSCARFACTORY_API FLBSpacecraftResearchNode
{
	GENERATED_BODY()

	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "LineBoss")
	FName NodeId;

	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "LineBoss")
	FString DisplayName;

	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "LineBoss")
	FName Branch;

	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "LineBoss")
	int32 CostPoints = 0;

	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "LineBoss")
	TArray<FName> Prerequisites;

	/** Station families this node opens for building and crafting. */
	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "LineBoss")
	TArray<FName> UnlockedStationClasses;

	/** Drone KINDS this node opens for hiring (2026-09-03). Still
	 *  content, not a stat bonus: the player unlocks a new kind of
	 *  crew to buy and place, exactly as they unlock a new machine -
	 *  what changes is what exists to choose from, never a multiplier
	 *  applied behind their back. Seven kinds shipped with quality
	 *  weights from 0.6 to 1.7 and all seven were hireable from the
	 *  first minute, so the choice carried no progression at all. */
	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "LineBoss")
	TArray<FName> UnlockedDroneKinds;
};

/** Whole-authority snapshot for the save pipeline. */
USTRUCT(BlueprintType)
struct LINEBOSSCARFACTORY_API FLBSpacecraftResearchSnapshot
{
	GENERATED_BODY()

	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "LineBoss")
	int32 Points = 0;

	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "LineBoss")
	TArray<FName> UnlockedNodes;

	/** Contracts already paid out in research points, so a reload
	 *  cannot farm the same delivery twice. */
	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "LineBoss")
	TArray<FName> CreditedContracts;

	/** Per-delivery high-water marks (supersedes the list above). */
	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "LineBoss")
	TArray<FLBSpacecraftDeliveryCredit> DeliveryCredits;
};

/** Static research catalogue: the EA Manufacturing branch. */
class LINEBOSSCARFACTORY_API FLBSpacecraftResearchCatalogue
{
public:
	static const TArray<FLBSpacecraftResearchNode>& GetNodeTable();

	static const FLBSpacecraftResearchNode* FindNode(FName NodeId);

	/** Station families available with NO research (the slice five). */
	static const TArray<FName>& GetDefaultStationClasses();

	/** Crew kinds available with NO research. Exactly one: the plain
	 *  assembly drone at nominal quality, which is also the fallback
	 *  every kind-less caller already gets - so an unresearched
	 *  factory crews normally and researches its SPECIALISTS. */
	static const TArray<FName>& GetDefaultDroneKinds();

	/** Shape, ordering-acyclicity and unlock-target validation. */
	static bool ValidateNodeTable(FString& OutReason);
};

/**
 * Single-owner authority for research points and unlocked nodes. Points
 * are earned by callers (contracts, later a Research Lab building) and
 * spent here; an unlock without its prerequisites or points is refused.
 */
UCLASS()
class LINEBOSSCARFACTORY_API ALBSpacecraftResearchAuthority : public AActor
{
	GENERATED_BODY()

public:
	ALBSpacecraftResearchAuthority();

	/** Adds earned research points. Fails closed on non-positive amounts. */
	bool AddPoints(int32 Points, FString& OutReason);

	/** Banks research points for every contract COMPLETED since the
	 *  last sync. Until this existed, points had no source outside a
	 *  dev console command and the whole tree was unreachable content:
	 *  delivering craft is how a factory learns. Idempotent - each
	 *  contract is credited once, tracked through the snapshot. */
	void SyncFromLedger(const class ALBSpacecraftProductionAuthority*
		InProduction);

	/** Pure: research points earned by delivering this much value.
	 *  PROVISIONAL pacing (owner tunes): one point per 500,000
	 *  hundredths, so a 50,000 cr Scout teaches 10 points and buys
	 *  Basic Fabrication on the first delivery. */
	static int32 PointsForDeliveredValuePence(int64 ValuePence);

	int32 GetPoints() const { return PointsBanked; }

	/** Spends points to unlock a node. Fails closed when the node is
	 *  unknown, already unlocked, missing a prerequisite, or unaffordable. */
	bool UnlockNode(FName NodeId, FString& OutReason);

	bool IsNodeUnlocked(FName NodeId) const;

	/** True for the default (slice) families and for any family opened by
	 *  an unlocked node. The build authority and crafting UI gate on this. */
	bool IsStationClassUnlocked(FName StationClassId) const;

	/** True for the default crew kind and for any kind opened by an
	 *  unlocked node. The hire path and the crew UI gate on this. */
	bool IsDroneKindUnlocked(FName KindId) const;

	int32 GetUnlockedNodeCount() const { return UnlockedNodes.Num(); }

	FLBSpacecraftResearchSnapshot CaptureSnapshot() const;
	bool RestoreSnapshot(const FLBSpacecraftResearchSnapshot& Snapshot,
		FString& OutReason);
	static bool ValidateSnapshot(
		const FLBSpacecraftResearchSnapshot& Snapshot, FString& OutReason);

private:
	int32 PointsBanked = 0;

	UPROPERTY()
	TArray<FName> CreditedContracts;

	UPROPERTY()
	TArray<FLBSpacecraftDeliveryCredit> DeliveryCredits;

	TArray<FName> UnlockedNodes;
};
