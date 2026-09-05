// Spacecraft-era production authority: the single owner of spacecraft WIP,
// contracts, the sim clock and the revenue tally. Everything else reads.
//
// Carries the house pattern forward: fail closed with a named reason,
// validate the ENTIRE snapshot before a single restore mutation, and never
// let presentation create a second logical record.
//
// New over the car era: contracts have an explicit OFFER -> ACCEPT beat (the
// pivot plan's first loop step, which the car ledger never had), and the
// quality gate is the Testing stage's hover test - a unit cannot leave
// Testing without a recorded pass, and a recorded fail can be retested.

#pragma once

#include "CoreMinimal.h"
#include "GameFramework/Actor.h"
#include "LBSpacecraftProductionTypes.h"
#include "LBSpacecraftProductionAuthority.generated.h"

UENUM(BlueprintType)
enum class ELBSpacecraftContractState : uint8
{
	Offered = 0,
	Accepted,
	Complete,
	Expired,
	/** An OFFER nobody took, lapsed off the board with the deadline it
	 *  carried. Distinct from Expired on purpose: failing an order you
	 *  accepted costs your name, and declining one by not taking it
	 *  must not. Appended, so saved values keep their meaning. */
	Withdrawn
};

/** How much of a contract an authority has already paid out on.
 *  Research and reputation used to credit only when a contract went
 *  COMPLETE, so a player who took a four-craft order delivered four
 *  ships and saw no progression at all until the last one landed. They
 *  credit per DELIVERY now, and this is the high-water mark. */
USTRUCT(BlueprintType)
struct LINEBOSSCARFACTORY_API FLBSpacecraftDeliveryCredit
{
	GENERATED_BODY()

	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "LineBoss")
	FName ContractId;

	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "LineBoss")
	int32 CreditedDeliveries = 0;
};

/** WHO the order is for. A contract used to carry a recipe and nothing
 *  else, so every offer on the board was from nobody in particular and
 *  they all read alike. The livery colour rides along ready for the
 *  paint pass - the owner's decision (2026-08-25) is that the FACTORY
 *  stays neutral cold steel and COLOUR BELONGS TO THE SHIPS, each craft
 *  wearing its customer's colours. Nothing renders it yet: the craft
 *  meshes have no tint parameter, so this is the half that does not
 *  need art.
 *
 *  NAMES ARE PLACEHOLDERS pending the owner - they are in-world
 *  customers, not this game's brand, which is still undecided. */
USTRUCT(BlueprintType)
struct LINEBOSSCARFACTORY_API FLBSpacecraftCustomer
{
	GENERATED_BODY()

	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "LineBoss")
	FName CustomerId;

	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "LineBoss")
	FString DisplayName;

	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "LineBoss")
	FLinearColor LiveryColour = FLinearColor::White;
};

USTRUCT(BlueprintType)
struct LINEBOSSCARFACTORY_API FLBSpacecraftContract
{
	GENERATED_BODY()

	/** Who ordered it, and the colours they want it in. */
	UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category = "LineBoss", SaveGame)
	FName CustomerId;

	UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category = "LineBoss", SaveGame)
	FLinearColor LiveryColour = FLinearColor::White;

	UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category = "LineBoss", SaveGame)
	FName ContractId;

	UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category = "LineBoss", SaveGame)
	FName RecipeId;

	UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category = "LineBoss", SaveGame)
	int32 Quantity = 0;

	UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category = "LineBoss", SaveGame)
	int64 PricePerUnitPence = 0;

	/** Sim-clock deadline; non-positive means no deadline. */
	UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category = "LineBoss", SaveGame)
	double DeadlineSimSeconds = 0.0;

	UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category = "LineBoss", SaveGame)
	int32 DispatchedCount = 0;

	UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category = "LineBoss", SaveGame)
	ELBSpacecraftContractState State = ELBSpacecraftContractState::Offered;

	/** THE CRAFT COMING BACK. None on a new-build order; its presence
	 *  is what makes this a refit, so there is no separate flag that
	 *  could fall out of step with it. */
	UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category = "LineBoss", SaveGame)
	FName RefitOriginUnitId;

	/** THE SCOPE SOLD: the rung the craft rejoins at. Everything from
	 *  there on is the work bought, and the price was computed from it,
	 *  so it is not derivable from the recipe. */
	UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category = "LineBoss", SaveGame)
	ELBSpacecraftStage RefitEntryStage = ELBSpacecraftStage::MaterialIntake;

	bool IsRefit() const { return !RefitOriginUnitId.IsNone(); }
};

/** Whole-ledger snapshot; validated in full before restore. */
USTRUCT(BlueprintType)
struct LINEBOSSCARFACTORY_API FLBSpacecraftProductionLedgerState
{
	GENERATED_BODY()

	UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category = "LineBoss", SaveGame)
	double SimSeconds = 0.0;

	UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category = "LineBoss", SaveGame)
	TArray<FLBSpacecraftUnitState> Units;

	UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category = "LineBoss", SaveGame)
	TArray<FLBSpacecraftContract> Contracts;

	UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category = "LineBoss", SaveGame)
	int32 NextUnitSequence = 1;

	/** Review fix: contract ids are LEDGER state (a function-local
	 *  static counter was process state - reused ids after load). */
	UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category = "LineBoss", SaveGame)
	int32 NextContractSequence = 1;

	UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category = "LineBoss", SaveGame)
	int64 RevenuePence = 0;

	/** Player cash. Starts at the PROVISIONAL starting capital (owner has
	 *  not tuned the economy yet); settlements add to it; station builds
	 *  spend it fail-closed - it never goes negative. */
	UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category = "LineBoss", SaveGame)
	int64 CashPence = 0;

	UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category = "LineBoss", SaveGame)
	int32 WIPCap = 3;
};

namespace LBSpacecraftCreditPrivate
{
	/** Deliveries on this contract not yet paid out, advancing the
	 *  high-water mark past them. Inline and shared, because both the
	 *  research and reputation authorities need it and a helper
	 *  defined in one .cpp is exactly the kind of thing this module's
	 *  unity build collides on.
	 *
	 *  Migration: an id carried in the old fully-credited list is
	 *  treated as already settled, so a save written before
	 *  per-delivery credit existed cannot pay out twice. */
	inline int32 SpacecraftClaimNewDeliveries(
		TArray<FLBSpacecraftDeliveryCredit>& Credits,
		const TArray<FName>& LegacyFullyCredited,
		const FLBSpacecraftContract& Contract)
	{
		const int32 Dispatched = FMath::Max(Contract.DispatchedCount, 0);
		FLBSpacecraftDeliveryCredit* Credit = Credits.FindByPredicate(
			[&Contract](const FLBSpacecraftDeliveryCredit& Row)
			{ return Row.ContractId == Contract.ContractId; });
		if (Credit == nullptr)
		{
			FLBSpacecraftDeliveryCredit Row;
			Row.ContractId = Contract.ContractId;
			Row.CreditedDeliveries =
				LegacyFullyCredited.Contains(Contract.ContractId)
					? Dispatched : 0;
			Credit = &Credits.Add_GetRef(Row);
		}
		const int32 Fresh = Dispatched - Credit->CreditedDeliveries;
		if (Fresh <= 0)
		{
			return 0;
		}
		Credit->CreditedDeliveries = Dispatched;
		return Fresh;
	}
}

/** The customer list offers are drawn from. */
class LINEBOSSCARFACTORY_API FLBSpacecraftCustomerCatalogue
{
public:
	static const TArray<FLBSpacecraftCustomer>& GetCustomers();
	static const FLBSpacecraftCustomer* FindCustomer(FName CustomerId);

	/** The customer for the Nth offer the yard has seen. Deterministic
	 *  so a save reloads to the same board. */
	static const FLBSpacecraftCustomer& CustomerForIndex(int32 Index);

	/** THE LIVERY A CRAFT OF THIS RECIPE IS BEING PAINTED IN (owner:
	 *  "colour belongs to the ships" - each contract paints the craft
	 *  in the customer's colours).
	 *
	 *  A unit carries its RECIPE, not its contract, so the livery is
	 *  resolved through the work outstanding: the accepted contract for
	 *  that recipe which still owes craft. Where several are open, the
	 *  one with the EARLIEST DEADLINE wins - that is the one the floor
	 *  is working to, and picking "the first in the array" would repaint
	 *  the craft whenever the array happened to reorder.
	 *
	 *  Falls back to white, which reads as unpainted primer rather than
	 *  as some other customer's colour. Pure. */
	static FLinearColor LiveryForRecipe(
		const TArray<FLBSpacecraftContract>& Contracts, FName RecipeId);
};

UCLASS()
class LINEBOSSCARFACTORY_API ALBSpacecraftProductionAuthority : public AActor
{
	GENERATED_BODY()

public:
	ALBSpacecraftProductionAuthority();

	// ---- contracts: offer -> accept -> (complete | expired) ----
	bool OfferContract(const FLBSpacecraftContract& Contract, FString& OutReason);
	bool AcceptContract(FName ContractId, FString& OutReason);

	// ---- units ----
	/** Creates a unit only when an accepted contract still has UNCLAIMED
	 *  demand for the recipe (in-flight units count against demand) and the
	 *  WIP cap has room. */
	bool CreateUnit(FName RecipeId, FName& OutUnitId, FString& OutReason);

	/** One serial step. Leaving Testing additionally requires a recorded
	 *  quality PASS, and the terminal step requires an accepted contract to
	 *  settle against - otherwise the unit stays put, with the reason named. */
	bool AdvanceUnit(FName UnitId, FString& OutReason);

	/** Adds workmanship defects to a unit as it leaves a station.
	 *  Refuses an unknown unit or a negative count; adding zero is a
	 *  no-op that still succeeds (a fully crewed station is normal). */
	/** Sells any craft standing in finished stock into orders that can
	 *  take them. Called on the sim clock, so a craft built to stock is
	 *  sold the moment a suitable order is accepted. Returns how many
	 *  were sold. */
	int32 SettleStockedCraft();

	/** How many finished craft are built and unsold. */
	int32 GetStockedCraftCount() const;

	/** THE CAP IS THE CARRIERS (2026-09-04). It used to be a flat 3
	 *  living in the ledger, enforced with "WIP cap 3 reached" and
	 *  explained by nothing on screen - a rule the player met as a
	 *  refusal rather than a thing they could see or change. A craft
	 *  rides a carrier for its whole time on the line, so the number
	 *  of carriers owned IS how many craft can be in build; the build
	 *  authority owns that number and pushes it here. Fails closed on
	 *  a non-positive cap: a factory that can hold no craft at all is
	 *  never what anyone meant. */
	bool SetWIPCap(int32 NewCap, FString& OutReason);

	int32 GetWIPCap() const { return Ledger.WIPCap; }

	/** THE BROKER (2026-09-03). A finished craft with no matching order
	 *  used to sit in stock with nothing the player could do but wait
	 *  for the offer board to come round to its recipe again. It was
	 *  never a soft-lock - the board round-robins, so a buyer always
	 *  turns up eventually - but it was frozen capital and zero agency,
	 *  which is the opposite of what a management game wants from an
	 *  awkward situation. Selling to a broker is the decision that
	 *  replaces the waiting: cash today at a discount, against full
	 *  price whenever a real customer appears.
	 *  Sells the OLDEST stocked craft of this recipe. Fails closed when
	 *  nothing of that kind is in stock. */
	bool SellStockedCraftToBroker(FName RecipeId, int64& OutPaidPence,
		FString& OutReason);

	/** What a broker would pay for this craft right now, defects and
	 *  all - so the button can say the number before it is pressed. */
	static int64 BrokerOfferPence(FName RecipeId,
		const struct FLBSpacecraftUnitState& Unit);

	/** Share of a craft's list price a broker pays. PROVISIONAL, and
	 *  the owner's to tune like the station sell-back's 50%. */
	static constexpr int64 BrokerPricePercent = 60;

	/** The price deduction a craft carries for its own failures (and
	 *  any concession granted in their place). Shared so a craft is
	 *  discounted identically however it is sold. */
	static int64 UnitDeductionPercent(
		const struct FLBSpacecraftUnitState& Unit);

private:
	/** Pays for one craft against one order, defect penalty and all.
	 *  Shared so a craft sold OUT OF STOCK is settled exactly as one
	 *  sold straight off the line. */
	void SellUnitInto(struct FLBSpacecraftUnitState& Unit,
		struct FLBSpacecraftContract& Contract);

public:

	bool AccrueDefects(FName UnitId, int32 Points, FString& OutReason);

	/** A STATION'S OWN INSPECTION opens rework on the craft standing
	 *  there (owner 2026-08-28, the settled pulse-line model: work does
	 *  not move on until that station's work is right). Adds to any
	 *  rework already owed rather than replacing it. */
	bool OpenStationRework(FName UnitId, float Seconds, FString& OutReason);

	/** Records the hover test. A FAIL also opens the rework the craft
	 *  now owes, so a failed craft can never sit at the gate forever -
	 *  the two happen together or not at all. */
	bool RecordQualityResult(FName UnitId, bool bPassed, FString& OutReason);

	/** Bank one completed TRIM PASS on a craft sitting on the pad.
	 *  Refuses off-gate for the same reason RecordQualityResult does:
	 *  a pass banked against a craft that is not being tested would be
	 *  invisible state nobody can account for. */
	bool RecordTrimPass(FName UnitId, FString& OutReason);

	// ---- refit: a delivered craft comes back ----

	/**
	 * Offers a refit on a craft this yard actually delivered.
	 *
	 * The offer is generated FROM the delivery record rather than
	 * invented: the returning ship must be a real unit of this yard's,
	 * dispatched and completed. That ties refit work to the player's
	 * own history instead of to a spawn table - and it is why a craft
	 * shipped on a concession is the natural thing to see again.
	 *
	 * Price is the whole-craft price scaled by the COMPONENTS actually
	 * re-fitted, never by time spent (see RefitWorkFraction).
	 */
	bool OfferRefit(FName OriginUnitId, ELBSpacecraftStage EntryStage,
		double DeadlineSimSeconds, FName& OutContractId, FString& OutReason);

	/**
	 * Puts the returned craft on the line as a NEW unit that names the
	 * original.
	 *
	 * A new record rather than a rewind of the delivered one, because
	 * the validator holds "completed if and only if dispatched" in both
	 * directions - and because the original's failed-test deductions
	 * must not be charged again against work the customer is paying for
	 * separately. It arrives already credited with the components it
	 * kept, which is what carries it past the assembly gate without
	 * walking the whole ladder.
	 */
	bool CreateRefitUnit(FName ContractId, FName& OutUnitId,
		FString& OutReason);

	/** The order a craft must settle against, or null. A refit settles
	 *  ONLY against the order it was commissioned for; a new build
	 *  keeps the fungible match-by-recipe behaviour. */
	struct FLBSpacecraftContract* SettlementContractFor(
		const struct FLBSpacecraftUnitState& Unit);

	// ---- the material review board ----
	//
	// A failed craft used to have exactly one future: pay the rework,
	// retest. These are the other two dispositions a real board has,
	// and between them they turn a toll into a decision - pay TIME to
	// put it right, pay MARGIN AND REPUTATION to ship it anyway, or
	// cut the loss on one that is too far gone.

	/** CONCEDE: ship the craft as-is under a recorded deviation.
	 *
	 *  Substitutes for a quality pass, clears the rework it owed, and
	 *  charges the difference in settlement and reputation instead.
	 *  Fails closed above the concession ceiling, on an untested or
	 *  passing craft, and on one already conceded - a second signature
	 *  would charge twice for one decision. */
	bool GrantConcession(FName UnitId, FString& OutReason);

	/** SCRAP: destroy the craft and clear the line.
	 *
	 *  The disposition of last resort, for a craft too far out to
	 *  concede and not worth reworking. Nothing is recovered yet; the
	 *  cost is everything already spent on it, which is the point. */
	bool ScrapUnit(FName UnitId, FString& OutReason);

	/** Reputation cost banked by concessions so far this session. Read
	 *  by the reputation authority; kept here because the production
	 *  authority is what witnesses the decision. */
	int32 GetConcessionReputationOwed() const
	{
		return ConcessionReputationOwed;
	}

	/** Clears the owed reputation once it has been applied, so it can
	 *  never be charged twice. Returns what was cleared. */
	int32 TakeConcessionReputationOwed()
	{
		const int32 Owed = ConcessionReputationOwed;
		ConcessionReputationOwed = 0;
		return Owed;
	}

	// ---- sim clock ----
	/** Advances the clock and expires overdue contracts. Negative deltas are
	 *  rejected - the clock never runs backwards. */
	bool AdvanceSimSeconds(double DeltaSeconds, FString& OutReason);

	// ---- save/restore ----
	FLBSpacecraftProductionLedgerState CaptureLedger() const { return Ledger; }
	bool ValidateLedger(const FLBSpacecraftProductionLedgerState& State,
		FString& OutReason) const;
	bool RestoreLedger(const FLBSpacecraftProductionLedgerState& State,
		FString& OutReason);

	// ---- read access ----
	const TArray<FLBSpacecraftUnitState>& GetUnits() const { return Ledger.Units; }
	const TArray<FLBSpacecraftContract>& GetContracts() const
	{
		return Ledger.Contracts;
	}
	int64 GetRevenuePence() const { return Ledger.RevenuePence; }
	int64 GetCashPence() const { return Ledger.CashPence; }

	/** PROVISIONAL starting capital: 60,000,000 pence (600,000 GBP) -
	 *  enough for the starter line plus power and a first crafting
	 *  station. The owner retunes this number. */
	static constexpr int64 ProvisionalStartingCapitalPence = 90000000;

	/** Spends cash fail-closed: refused whole when funds are short. */
	/** Mints the next ledger-owned contract id. */
	FName MintContractId();

	bool SpendPence(int64 AmountPence, FString& OutReason);

	/** Adds cash (contract settlements, sell-backs). */
	bool EarnPence(int64 AmountPence, FString& OutReason);
	double GetSimSeconds() const { return Ledger.SimSeconds; }
	const FLBSpacecraftUnitState* FindUnit(FName UnitId) const;
	const FLBSpacecraftContract* FindContract(FName ContractId) const;

private:
	UPROPERTY(VisibleAnywhere, Category = "LineBoss")
	FLBSpacecraftProductionLedgerState Ledger;

	/** Reputation charged by concessions and not yet applied.
	 *
	 *  Banked rather than pushed straight at the reputation authority
	 *  because this authority owns the DECISION and that one owns the
	 *  SCORE - having the production side reach in and mutate another
	 *  authority's state is exactly the shared-mutable-state tangle the
	 *  single-owner pattern exists to prevent. It is taken, not read,
	 *  so the same cost can never be applied twice. */
	int32 ConcessionReputationOwed = 0;

	FLBSpacecraftContract* FindContractMutable(FName ContractId);
	FLBSpacecraftUnitState* FindUnitMutable(FName UnitId);

	/** Accepted-contract demand for a recipe not yet claimed by dispatched
	 *  or in-flight units. */
	int32 UnclaimedDemand(FName RecipeId) const;

	/** Oldest accepted contract with remaining demand for the recipe. */
	FLBSpacecraftContract* OldestOpenContract(FName RecipeId);
};
