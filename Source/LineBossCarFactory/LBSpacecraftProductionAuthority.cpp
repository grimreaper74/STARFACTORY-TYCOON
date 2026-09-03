#include "LBSpacecraftProductionAuthority.h"

#include "LBSpacecraftDifficulty.h"

namespace LBSpacecraftProductionAuthorityPrivate
{
	// Unity-build safety: helpers qualified by subject.
	int32 SpacecraftUnitSuffix(FName UnitId)
	{
		const FString Text = UnitId.ToString();
		int32 DashIndex = INDEX_NONE;
		return Text.FindLastChar(TEXT('-'), DashIndex)
			? FCString::Atoi(*Text.Mid(DashIndex + 1)) : 0;
	}
}

namespace LBSpacecraftCustomerPrivate
{
	// Unity-build safety: helper qualified by subject.
	FLBSpacecraftCustomer SpacecraftMakeCustomer(const TCHAR* Id,
		const TCHAR* Display, const FLinearColor& Livery)
	{
		FLBSpacecraftCustomer Customer;
		Customer.CustomerId = FName(Id);
		Customer.DisplayName = Display;
		Customer.LiveryColour = Livery;
		return Customer;
	}
}

const TArray<FLBSpacecraftCustomer>&
FLBSpacecraftCustomerCatalogue::GetCustomers()
{
	using namespace LBSpacecraftCustomerPrivate;
	// PLACEHOLDER NAMES pending the owner. These are in-world clients,
	// deliberately plain, and deliberately NOT the Cairnwell names -
	// those are car-era prior art and this game's own brand is still
	// undecided. The colours are each customer's livery; the factory
	// itself stays neutral cold steel.
	static const TArray<FLBSpacecraftCustomer> Customers = {
		SpacecraftMakeCustomer(TEXT("Customer.Survey"),
			TEXT("Orbital Survey Board"),
			FLinearColor(0.10f, 0.35f, 0.62f)),
		SpacecraftMakeCustomer(TEXT("Customer.Freight"),
			TEXT("Deep Reach Freight"),
			FLinearColor(0.72f, 0.36f, 0.06f)),
		SpacecraftMakeCustomer(TEXT("Customer.Rescue"),
			TEXT("Coastal Rescue Wing"),
			FLinearColor(0.68f, 0.10f, 0.12f)),
		SpacecraftMakeCustomer(TEXT("Customer.Research"),
			TEXT("Hollis Research Trust"),
			FLinearColor(0.86f, 0.86f, 0.88f)),
		SpacecraftMakeCustomer(TEXT("Customer.Prospect"),
			TEXT("Fenwick Prospecting"),
			FLinearColor(0.20f, 0.44f, 0.24f)) };
	return Customers;
}

const FLBSpacecraftCustomer* FLBSpacecraftCustomerCatalogue::FindCustomer(
	FName CustomerId)
{
	for (const FLBSpacecraftCustomer& Customer : GetCustomers())
	{
		if (Customer.CustomerId == CustomerId)
		{
			return &Customer;
		}
	}
	return nullptr;
}

FLinearColor FLBSpacecraftCustomerCatalogue::LiveryForRecipe(
	const TArray<FLBSpacecraftContract>& Contracts, FName RecipeId)
{
	const FLBSpacecraftContract* Chosen = nullptr;
	for (const FLBSpacecraftContract& Contract : Contracts)
	{
		if (Contract.RecipeId != RecipeId
			|| Contract.State != ELBSpacecraftContractState::Accepted
			|| Contract.DispatchedCount >= Contract.Quantity)
		{
			continue;
		}
		if (Chosen == nullptr)
		{
			Chosen = &Contract;
			continue;
		}
		// Earliest deadline wins - that is the contract the floor is
		// working to. Taking "the first in the array" would repaint the
		// craft whenever the array happened to reorder. A contract with
		// NO deadline never displaces one with a clock running.
		const bool bHasDeadline = Contract.DeadlineSimSeconds > 0.0;
		const bool bChosenHasDeadline = Chosen->DeadlineSimSeconds > 0.0;
		if (bHasDeadline
			&& (!bChosenHasDeadline
				|| Contract.DeadlineSimSeconds
					< Chosen->DeadlineSimSeconds))
		{
			Chosen = &Contract;
		}
	}
	return Chosen != nullptr ? Chosen->LiveryColour : FLinearColor::White;
}

const FLBSpacecraftCustomer&
FLBSpacecraftCustomerCatalogue::CustomerForIndex(int32 Index)
{
	const TArray<FLBSpacecraftCustomer>& Customers = GetCustomers();
	return Customers[FMath::Abs(Index) % Customers.Num()];
}

ALBSpacecraftProductionAuthority::ALBSpacecraftProductionAuthority()
{
	PrimaryActorTick.bCanEverTick = false;
	// The opening balance is a difficulty dial. Set here rather than
	// adjusted later, so a new factory never briefly holds the wrong
	// amount and nothing has to remember to correct it.
	Ledger.CashPence =
		FLBSpacecraftDifficulty::Current().StartingCapitalPence;
}

FName ALBSpacecraftProductionAuthority::MintContractId()
{
	return FName(*FString::Printf(TEXT("SC-CONTRACT-%03d"),
		Ledger.NextContractSequence++));
}

bool ALBSpacecraftProductionAuthority::SpendPence(int64 AmountPence,
	FString& OutReason)
{
	if (AmountPence <= 0)
	{
		OutReason = TEXT("Spend amount must be positive");
		return false;
	}
	if (Ledger.CashPence < AmountPence)
	{
		// Shown verbatim as a player toast: CREDITS, never the
		// internal hundredths (owner currency decision, 2026-08-25).
		OutReason = FString::Printf(
			TEXT("Insufficient funds - need %lld cr, have %lld cr"),
			AmountPence / 100, Ledger.CashPence / 100);
		return false;
	}
	Ledger.CashPence -= AmountPence;
	OutReason.Reset();
	return true;
}

bool ALBSpacecraftProductionAuthority::EarnPence(int64 AmountPence,
	FString& OutReason)
{
	if (AmountPence <= 0)
	{
		OutReason = TEXT("Earn amount must be positive");
		return false;
	}
	Ledger.CashPence += AmountPence;
	OutReason.Reset();
	return true;
}

bool ALBSpacecraftProductionAuthority::OfferContract(
	const FLBSpacecraftContract& Contract, FString& OutReason)
{
	if (Contract.ContractId.IsNone())
	{
		OutReason = TEXT("Contract needs an ID");
		return false;
	}
	if (FindContract(Contract.ContractId) != nullptr)
	{
		OutReason = FString::Printf(TEXT("Contract %s already exists"),
			*Contract.ContractId.ToString());
		return false;
	}
	FLBSpacecraftRecipe Recipe;
	if (!FLBSpacecraftProductionCatalog::FindRecipe(Contract.RecipeId, Recipe))
	{
		OutReason = FString::Printf(TEXT("Unknown recipe %s"),
			*Contract.RecipeId.ToString());
		return false;
	}
	if (Contract.Quantity <= 0 || Contract.PricePerUnitPence <= 0)
	{
		OutReason = TEXT("Contract needs positive quantity and price");
		return false;
	}
	if (Contract.DispatchedCount != 0
		|| Contract.State != ELBSpacecraftContractState::Offered)
	{
		OutReason = TEXT("A new contract starts undispatched and offered");
		return false;
	}
	if (Contract.DeadlineSimSeconds > 0.0
		&& Contract.DeadlineSimSeconds <= Ledger.SimSeconds)
	{
		OutReason = TEXT("Contract deadline is already in the past");
		return false;
	}
	Ledger.Contracts.Add(Contract);
	OutReason.Reset();
	return true;
}

bool ALBSpacecraftProductionAuthority::AcceptContract(FName ContractId,
	FString& OutReason)
{
	FLBSpacecraftContract* Contract = FindContractMutable(ContractId);
	if (Contract == nullptr)
	{
		OutReason = FString::Printf(TEXT("Unknown contract %s"),
			*ContractId.ToString());
		return false;
	}
	if (Contract->State != ELBSpacecraftContractState::Offered)
	{
		OutReason = TEXT("Only an offered contract can be accepted");
		return false;
	}
	Contract->State = ELBSpacecraftContractState::Accepted;
	OutReason.Reset();
	return true;
}

int32 ALBSpacecraftProductionAuthority::UnclaimedDemand(FName RecipeId) const
{
	// DEMAND IS MATCHED BY KIND AS WELL AS BY RECIPE.
	//
	// A refit order wants ONE NAMED HULL back; it does not want a new
	// craft built. Counting it here would tell the yard to start a
	// brand-new build to satisfy it - the customer's ship never gets
	// touched, and the player pays a full bill of materials for work
	// they were only owed a fraction of. The mirror is just as bad: a
	// refit standing on the line would suppress the new build some
	// other order actually needed.
	//
	// Both halves therefore skip refits, which keeps new builds behaving
	// exactly as they always have.
	int32 Demand = 0;
	for (const FLBSpacecraftContract& Contract : Ledger.Contracts)
	{
		if (Contract.State == ELBSpacecraftContractState::Accepted
			&& Contract.RecipeId == RecipeId
			&& !Contract.IsRefit())
		{
			Demand += Contract.Quantity - Contract.DispatchedCount;
		}
	}
	for (const FLBSpacecraftUnitState& Unit : Ledger.Units)
	{
		if (Unit.RecipeId == RecipeId
			&& Unit.Stage != ELBSpacecraftStage::Dispatched
			&& !Unit.IsRefit())
		{
			--Demand; // in-flight units already claim demand
		}
	}
	return Demand;
}

FLBSpacecraftContract* ALBSpacecraftProductionAuthority::OldestOpenContract(
	FName RecipeId)
{
	for (FLBSpacecraftContract& Contract : Ledger.Contracts)
	{
		if (Contract.State == ELBSpacecraftContractState::Accepted
			&& Contract.RecipeId == RecipeId
			&& Contract.DispatchedCount < Contract.Quantity)
		{
			return &Contract; // array order is offer order = oldest first
		}
	}
	return nullptr;
}

bool ALBSpacecraftProductionAuthority::CreateUnit(FName RecipeId,
	FName& OutUnitId, FString& OutReason)
{
	OutUnitId = NAME_None;
	FLBSpacecraftRecipe Recipe;
	if (!FLBSpacecraftProductionCatalog::FindRecipe(RecipeId, Recipe))
	{
		OutReason = FString::Printf(TEXT("Unknown recipe %s"),
			*RecipeId.ToString());
		return false;
	}
	int32 InFlight = 0;
	for (const FLBSpacecraftUnitState& Unit : Ledger.Units)
	{
		InFlight += Unit.Stage != ELBSpacecraftStage::Dispatched ? 1 : 0;
	}
	if (InFlight >= Ledger.WIPCap)
	{
		OutReason = FString::Printf(TEXT("WIP cap %d reached"), Ledger.WIPCap);
		return false;
	}
	if (UnclaimedDemand(RecipeId) <= 0)
	{
		OutReason = TEXT("No accepted contract demand for this recipe");
		return false;
	}
	FLBSpacecraftUnitState Unit;
	Unit.UnitId = FName(*FString::Printf(TEXT("%s-%06d"),
		*RecipeId.ToString(), Ledger.NextUnitSequence));
	Unit.RecipeId = RecipeId;
	Ledger.Units.Add(Unit);
	++Ledger.NextUnitSequence;
	OutUnitId = Unit.UnitId;
	OutReason.Reset();
	return true;
}

bool ALBSpacecraftProductionAuthority::AdvanceUnit(FName UnitId,
	FString& OutReason)
{
	FLBSpacecraftUnitState* Unit = FindUnitMutable(UnitId);
	if (Unit == nullptr)
	{
		OutReason = FString::Printf(TEXT("Unknown unit %s"),
			*UnitId.ToString());
		return false;
	}
	FLBSpacecraftRecipe Recipe;
	if (!FLBSpacecraftProductionCatalog::FindRecipe(Unit->RecipeId, Recipe))
	{
		OutReason = TEXT("Unit recipe is no longer registered");
		return false;
	}
	ELBSpacecraftStage Target = Unit->Stage;
	if (!FLBSpacecraftProductionCatalog::NextStage(Unit->Stage, Target))
	{
		OutReason = TEXT("Unit is at the terminal stage");
		return false;
	}

	// The hover test: nothing leaves Testing without a recorded pass.
	if (FLBSpacecraftProductionCatalog::IsQualityGate(Unit->Stage))
	{
		if (!Unit->bQualityRecorded)
		{
			OutReason = TEXT("Quality result not yet recorded at the gate");
			return false;
		}
		// A CONCESSION SUBSTITUTES FOR A PASS. That is the entire
		// disposition: the player has signed for the deviation and
		// paid in margin and reputation instead of in line time. If
		// this gate did not honour it, a conceded craft would take
		// every cost and still sit at the gate forever.
		if (!Unit->bQualityPassed && !Unit->bConcessionGranted)
		{
			OutReason = TEXT("Quality failed - retest before dispatch");
			return false;
		}
	}

	// The terminal step SELLS the craft if there is an order for it.
	// If there is not, it still rolls off the line - into finished
	// stock. Refusing the advance is what stranded a craft whose
	// contract expired mid-build: it sat at the gate forever with
	// nothing to settle against, and everything behind it stopped.
	// A refit settles ONLY against the order it was commissioned for;
	// a new build stays fungible and keeps matching by recipe. Paying a
	// refit into whichever order happened to be oldest would credit the
	// wrong customer for the wrong ship, and would let one hull close
	// out an order for a craft that was never built.
	FLBSpacecraftContract* Settlement =
		Target == ELBSpacecraftStage::Dispatched
			? SettlementContractFor(*Unit) : nullptr;

	if (!FLBSpacecraftProductionCatalog::AdvanceUnit(*Unit, Recipe, OutReason))
	{
		return false;
	}
	if (Target == ELBSpacecraftStage::Dispatched)
	{
		if (Settlement != nullptr)
		{
			SellUnitInto(*Unit, *Settlement);
		}
		else
		{
			Unit->bAwaitingSale = true;
		}
	}
	OutReason.Reset();
	return true;
}

int64 ALBSpacecraftProductionAuthority::UnitDeductionPercent(
	const FLBSpacecraftUnitState& Unit)
{
	// Defect penalty (vision: honest machine economy): each failed
	// hover test costs 10% of the price, capped at 30% (PROVISIONAL).
	// It travels with the CRAFT, so a shoddy one sells for less
	// whenever it sells - out of stock, off the line, or to a broker.
	int64 DeductionPercent = FMath::Min<int64>(
		static_cast<int64>(Unit.FailedQualityTests) * 10, 30);
	// A CONCESSION IS CHARGED IN PLACE OF THE FAILURES, NOT ON TOP.
	//
	// The two are the same event seen twice: the craft failed, and the
	// player chose to ship it anyway. Adding both would bill the
	// failure and then bill the decision not to fix the failure, and a
	// concession would cost more than scrapping - which would make the
	// disposition pointless rather than expensive.
	//
	// Charged from the points RECORDED AT SIGNING rather than the live
	// count, so the settlement matches what was actually agreed even
	// if the craft's defects move afterwards.
	if (Unit.bConcessionGranted)
	{
		DeductionPercent = FMath::Max(DeductionPercent,
			static_cast<int64>(FLBSpacecraftProductionCatalog
				::ConcessionDeductionPercent(Unit.ConcededDefectPoints)));
	}
	return DeductionPercent;
}

int64 ALBSpacecraftProductionAuthority::BrokerOfferPence(
	FName RecipeId, const FLBSpacecraftUnitState& Unit)
{
	FLBSpacecraftRecipe Recipe;
	if (!FLBSpacecraftProductionCatalog::FindRecipe(RecipeId, Recipe)
		|| Recipe.RevenuePence <= 0)
	{
		return 0;
	}
	// PROVISIONAL 60% (owner tunes, like the station sell-back's 50%).
	// The discount IS the mechanic: a broker takes the craft off your
	// hands today, and the difference between this and a real order is
	// what patience is worth. Deep enough that waiting for a customer
	// is usually right, shallow enough that clearing a jam is a real
	// option rather than a punishment.
	const int64 Base = Recipe.RevenuePence * BrokerPricePercent / 100;
	return Base * (100 - UnitDeductionPercent(Unit)) / 100;
}

bool ALBSpacecraftProductionAuthority::SellStockedCraftToBroker(
	FName RecipeId, int64& OutPaidPence, FString& OutReason)
{
	OutPaidPence = 0;
	// The OLDEST of that kind, so repeated sales clear stock in the
	// order it was built rather than in whatever order the array sits.
	FLBSpacecraftUnitState* Oldest = nullptr;
	for (FLBSpacecraftUnitState& Unit : Ledger.Units)
	{
		if (!Unit.bAwaitingSale || Unit.RecipeId != RecipeId)
		{
			continue;
		}
		if (Oldest == nullptr)
		{
			Oldest = &Unit;
		}
	}
	if (Oldest == nullptr)
	{
		OutReason = FString::Printf(
			TEXT("NO %s IN FINISHED STOCK"), *RecipeId.ToString());
		return false;
	}
	const int64 PaidPence = BrokerOfferPence(RecipeId, *Oldest);
	if (PaidPence <= 0)
	{
		OutReason = FString::Printf(
			TEXT("NO BROKER PRICE FOR %s"), *RecipeId.ToString());
		return false;
	}
	// Settled like any other sale: the craft leaves stock and the money
	// is revenue. It is NOT a contract delivery, so it credits no
	// research points and moves no reputation - a clearance sale
	// teaches the factory nothing and impresses nobody.
	Oldest->bAwaitingSale = false;
	Ledger.RevenuePence += PaidPence;
	Ledger.CashPence += PaidPence;
	OutPaidPence = PaidPence;
	OutReason = FString::Printf(
		TEXT("SOLD %s TO A BROKER FOR %lld"), *RecipeId.ToString(),
		PaidPence / 100);
	return true;
}

void ALBSpacecraftProductionAuthority::SellUnitInto(
	FLBSpacecraftUnitState& Unit, FLBSpacecraftContract& Contract)
{
	Unit.bAwaitingSale = false;
	++Contract.DispatchedCount;
	const int64 PaidPence = Contract.PricePerUnitPence
		* (100 - UnitDeductionPercent(Unit)) / 100;
	Ledger.RevenuePence += PaidPence;
	Ledger.CashPence += PaidPence;
	if (Contract.DispatchedCount >= Contract.Quantity)
	{
		Contract.State = ELBSpacecraftContractState::Complete;
	}
}

bool ALBSpacecraftProductionAuthority::SetWIPCap(int32 NewCap,
	FString& OutReason)
{
	if (NewCap <= 0)
	{
		OutReason = TEXT("A FACTORY MUST HOLD AT LEAST ONE CRAFT");
		return false;
	}
	// Craft already on the line are NOT thrown off when the cap drops.
	// Nothing in the game can sell a carrier today, but if that ever
	// arrives, the honest behaviour is that the line finishes what it
	// started and simply admits nothing new until it is under the cap
	// again - which is exactly what CreateUnit's >= test already does.
	Ledger.WIPCap = NewCap;
	OutReason = FString::Printf(TEXT("THE LINE HOLDS %d CRAFT"), NewCap);
	return true;
}

int32 ALBSpacecraftProductionAuthority::GetStockedCraftCount() const
{
	int32 Count = 0;
	for (const FLBSpacecraftUnitState& Unit : Ledger.Units)
	{
		if (Unit.bAwaitingSale)
		{
			++Count;
		}
	}
	return Count;
}

int32 ALBSpacecraftProductionAuthority::SettleStockedCraft()
{
	int32 Sold = 0;
	for (FLBSpacecraftUnitState& Unit : Ledger.Units)
	{
		if (!Unit.bAwaitingSale)
		{
			continue;
		}
		FLBSpacecraftContract* Contract = OldestOpenContract(Unit.RecipeId);
		if (Contract == nullptr)
		{
			continue;
		}
		SellUnitInto(Unit, *Contract);
		++Sold;
	}
	return Sold;
}

bool ALBSpacecraftProductionAuthority::AccrueDefects(FName UnitId,
	int32 Points, FString& OutReason)
{
	if (Points < 0)
	{
		OutReason = TEXT("Defects are never negative");
		return false;
	}
	FLBSpacecraftUnitState* Unit = FindUnitMutable(UnitId);
	if (Unit == nullptr)
	{
		OutReason = FString::Printf(TEXT("Unknown unit %s"),
			*UnitId.ToString());
		return false;
	}
	Unit->DefectPoints += Points;
	OutReason.Reset();
	return true;
}

bool ALBSpacecraftProductionAuthority::RecordTrimPass(
	FName UnitId, FString& OutReason)
{
	FLBSpacecraftUnitState* Unit = FindUnitMutable(UnitId);
	if (Unit == nullptr)
	{
		OutReason = FString::Printf(TEXT("No such unit %s"),
			*UnitId.ToString());
		return false;
	}
	// Off-gate is a refusal, not a no-op. A trim pass banked against a
	// craft that is not on the pad is state nobody can account for, and
	// the save validator would rightly reject it on the way back in.
	if (Unit->Stage != ELBSpacecraftStage::Testing)
	{
		OutReason = FString::Printf(
			TEXT("%s is not on the pad - nothing to trim"),
			*UnitId.ToString());
		return false;
	}
	if (Unit->bQualityRecorded)
	{
		OutReason = FString::Printf(
			TEXT("%s has already been signed off"), *UnitId.ToString());
		return false;
	}
	++Unit->TrimPassesDone;
	return true;
}

bool ALBSpacecraftProductionAuthority::RecordQualityResult(FName UnitId,
	bool bPassed, FString& OutReason)
{
	FLBSpacecraftUnitState* Unit = FindUnitMutable(UnitId);
	if (Unit == nullptr)
	{
		OutReason = FString::Printf(TEXT("Unknown unit %s"),
			*UnitId.ToString());
		return false;
	}
	if (!FLBSpacecraftProductionCatalog::IsQualityGate(Unit->Stage))
	{
		OutReason = TEXT("Quality is recorded at the testing gate only");
		return false;
	}
	Unit->bQualityRecorded = true;
	Unit->bQualityPassed = bPassed;
	if (!bPassed)
	{
		++Unit->FailedQualityTests;
		// Open the rework in the SAME act as the failure. A failed
		// craft that owed no rework would block dispatch forever
		// (AdvanceUnit refuses to leave Testing without a pass) and
		// nothing would ever clear it - a permanent line deadlock.
		Unit->ReworkSecondsRemaining =
			FLBSpacecraftProductionCatalog::ReworkSecondsFor(
				Unit->DefectPoints);
	}
	OutReason.Reset();
	return true;
}

namespace LBSpacecraftRefitPrivate
{
	/** A stage's player-facing name. FindStage is the public accessor;
	 *  the terse internal name lives in the types .cpp and is not
	 *  reachable from here. */
	FString StageName(ELBSpacecraftStage Stage)
	{
		const FLBSpacecraftStageDescriptor* Row =
			FLBSpacecraftProductionCatalog::FindStage(Stage);
		return Row != nullptr ? Row->DisplayName : TEXT("an unknown stage");
	}
}

bool ALBSpacecraftProductionAuthority::OfferRefit(FName OriginUnitId,
	ELBSpacecraftStage EntryStage, double DeadlineSimSeconds,
	FName& OutContractId, FString& OutReason)
{
	OutContractId = NAME_None;
	if (!FLBSpacecraftProductionCatalog::IsLegalRefitEntryStage(
		EntryStage, OutReason))
	{
		return false;
	}
	const FLBSpacecraftUnitState* Origin = FindUnit(OriginUnitId);
	if (Origin == nullptr)
	{
		OutReason = FString::Printf(TEXT("No such craft %s"),
			*OriginUnitId.ToString());
		return false;
	}
	// ONLY A CRAFT THIS YARD ACTUALLY DELIVERED comes back. A ship
	// still on the line is not a returning customer's, and offering a
	// refit on one would let the player be paid twice for the same
	// work while it is still being done the first time.
	if (!Origin->bCompleted
		|| Origin->Stage != ELBSpacecraftStage::Dispatched)
	{
		OutReason = FString::Printf(
			TEXT("%s has not been delivered yet"), *OriginUnitId.ToString());
		return false;
	}
	// A hull is in the shop once. Without this the player could stack
	// refit orders on one ship and run it down the line repeatedly.
	for (const FLBSpacecraftUnitState& Unit : Ledger.Units)
	{
		if (Unit.IsRefit() && Unit.OriginUnitId == OriginUnitId
			&& Unit.Stage != ELBSpacecraftStage::Dispatched)
		{
			OutReason = FString::Printf(
				TEXT("%s is already in the shop"), *OriginUnitId.ToString());
			return false;
		}
	}
	for (const FLBSpacecraftContract& Contract : Ledger.Contracts)
	{
		const bool bLive =
			Contract.State == ELBSpacecraftContractState::Offered
			|| Contract.State == ELBSpacecraftContractState::Accepted;
		if (bLive && Contract.IsRefit()
			&& Contract.RefitOriginUnitId == OriginUnitId)
		{
			OutReason = FString::Printf(
				TEXT("An order already wants %s back"),
				*OriginUnitId.ToString());
			return false;
		}
	}

	FLBSpacecraftRecipe Recipe;
	if (!FLBSpacecraftProductionCatalog::FindRecipe(Origin->RecipeId, Recipe))
	{
		OutReason = TEXT("That craft's recipe is no longer registered");
		return false;
	}

	FLBSpacecraftContract Refit;
	Refit.ContractId = FName(*FString::Printf(TEXT("REFIT-%06d"),
		Ledger.NextContractSequence));
	Refit.RecipeId = Origin->RecipeId;
	Refit.Quantity = 1;   // one hull, one job. Validated below.
	Refit.RefitOriginUnitId = OriginUnitId;
	Refit.RefitEntryStage = EntryStage;
	Refit.DeadlineSimSeconds = DeadlineSimSeconds;
	// PRICED BY THE PARTS RE-FITTED, NOT BY TIME SPENT. Pricing by
	// time was the first design and it broke the game: the fixing
	// order is expensive-first while the cycle times are expensive-
	// last, so a time-priced refit was paid for the long end of the
	// ladder and bought only the cheap end of the bill of materials.
	// The worst refit out-earned the best new build.
	const float Fraction =
		FLBSpacecraftProductionCatalog::RefitWorkFraction(EntryStage,
			&Recipe);
	Refit.PricePerUnitPence = static_cast<int64>(
		static_cast<double>(Recipe.RevenuePence) * Fraction);
	if (Refit.PricePerUnitPence <= 0)
	{
		OutReason = TEXT("That refit would be worth nothing");
		return false;
	}
	Refit.CustomerId = Origin->RecipeId;

	if (!OfferContract(Refit, OutReason))
	{
		return false;
	}
	OutContractId = Refit.ContractId;
	UE_LOG(LogTemp, Display,
		TEXT("SPACECRAFT REFIT OFFERED %s on %s from %s - %.0f%% of a build"),
		*OutContractId.ToString(), *OriginUnitId.ToString(),
		*LBSpacecraftRefitPrivate::StageName(EntryStage),
		Fraction * 100.f);
	OutReason.Reset();
	return true;
}

bool ALBSpacecraftProductionAuthority::CreateRefitUnit(FName ContractId,
	FName& OutUnitId, FString& OutReason)
{
	OutUnitId = NAME_None;
	FLBSpacecraftContract* Contract = FindContractMutable(ContractId);
	if (Contract == nullptr)
	{
		OutReason = FString::Printf(TEXT("Unknown order %s"),
			*ContractId.ToString());
		return false;
	}
	if (!Contract->IsRefit())
	{
		OutReason = TEXT("That order is a new build, not a refit");
		return false;
	}
	if (Contract->State != ELBSpacecraftContractState::Accepted)
	{
		OutReason = TEXT("That refit order has not been accepted");
		return false;
	}
	for (const FLBSpacecraftUnitState& Unit : Ledger.Units)
	{
		if (Unit.AssignedContractId == ContractId)
		{
			OutReason = TEXT("That refit is already on the line");
			return false;
		}
	}
	const FLBSpacecraftUnitState* Origin =
		FindUnit(Contract->RefitOriginUnitId);
	if (Origin == nullptr)
	{
		OutReason = FString::Printf(TEXT("The craft %s no longer exists"),
			*Contract->RefitOriginUnitId.ToString());
		return false;
	}
	int32 InFlight = 0;
	for (const FLBSpacecraftUnitState& Unit : Ledger.Units)
	{
		InFlight += Unit.Stage != ELBSpacecraftStage::Dispatched ? 1 : 0;
	}
	if (InFlight >= Ledger.WIPCap)
	{
		// A refit competes for line capacity exactly as a build does -
		// that is most of what makes taking one a decision.
		OutReason = FString::Printf(
			TEXT("WIP cap %d reached - no room for the refit"),
			Ledger.WIPCap);
		return false;
	}

	FLBSpacecraftUnitState Unit;
	Unit.UnitId = FName(*FString::Printf(TEXT("%s-%06d"),
		*Contract->RecipeId.ToString(), Ledger.NextUnitSequence));
	Unit.RecipeId = Contract->RecipeId;
	// FLATTENED: a refit of a refit names the ROOT hull, so "is this
	// ship already in the shop" stays one comparison rather than a walk
	// back through a chain that could be arbitrarily long.
	Unit.OriginUnitId = Origin->IsRefit()
		? Origin->OriginUnitId : Contract->RefitOriginUnitId;
	Unit.EntryStage = Contract->RefitEntryStage;
	Unit.Stage = Contract->RefitEntryStage;
	Unit.AssignedContractId = ContractId;
	// SEEDED WITH WHAT IT KEPT. AdvanceUnit is otherwise the only
	// writer of this list, and the assembly gate refuses a craft whose
	// component set is incomplete - so a refit dropped in mid-ladder
	// without this would be stuck at assembly forever.
	{
		FLBSpacecraftRecipe SeedRecipe;
		const bool bSeedRecipe = FLBSpacecraftProductionCatalog::FindRecipe(
			Unit.RecipeId, SeedRecipe);
		FLBSpacecraftProductionCatalog::ComponentsEarnedBy(
			Contract->RefitEntryStage, Unit.ProducedComponents,
			bSeedRecipe ? &SeedRecipe : nullptr);
	}

	Ledger.Units.Add(Unit);
	++Ledger.NextUnitSequence;
	OutUnitId = Unit.UnitId;
	UE_LOG(LogTemp, Display,
		TEXT("SPACECRAFT REFIT ON THE LINE %s (hull %s) at %s"),
		*OutUnitId.ToString(), *Unit.OriginUnitId.ToString(),
		*LBSpacecraftRefitPrivate::StageName(Unit.EntryStage));
	OutReason.Reset();
	return true;
}

FLBSpacecraftContract* ALBSpacecraftProductionAuthority::
	SettlementContractFor(const FLBSpacecraftUnitState& Unit)
{
	// A REFIT SETTLES ONLY AGAINST ITS OWN ORDER. New builds stay
	// fungible and keep matching by recipe, which is what stops this
	// change from disturbing them - but a refit is one named hull
	// bought by one named customer, and letting it settle against
	// whichever order happened to be oldest would pay the wrong person
	// for the wrong ship.
	if (Unit.IsRefit())
	{
		if (Unit.AssignedContractId.IsNone())
		{
			return nullptr;
		}
		FLBSpacecraftContract* Assigned =
			FindContractMutable(Unit.AssignedContractId);
		return (Assigned != nullptr
			&& Assigned->State == ELBSpacecraftContractState::Accepted)
			? Assigned : nullptr;
	}
	return OldestOpenContract(Unit.RecipeId);
}

bool ALBSpacecraftProductionAuthority::GrantConcession(FName UnitId,
	FString& OutReason)
{
	FLBSpacecraftUnitState* Unit = FindUnitMutable(UnitId);
	if (Unit == nullptr)
	{
		OutReason = FString::Printf(TEXT("Unknown unit %s"),
			*UnitId.ToString());
		return false;
	}
	// EVERY legality question is answered by the pure rule, so the
	// panel can ask the same question before offering the button and
	// get the same answer. A UI that offers an action the authority
	// will refuse is how a player learns to distrust the interface.
	if (!FLBSpacecraftProductionCatalog::CanConcede(*Unit, OutReason))
	{
		return false;
	}

	// Read the cost BEFORE anything mutates, so the record and the
	// charge cannot disagree about what was signed off.
	const int32 Conceded = Unit->DefectPoints;

	Unit->bConcessionGranted = true;
	Unit->ConcededDefectPoints = Conceded;
	// The concession BUYS OUT the rework - that is what the player is
	// paying for. Leaving the debt open would take their margin and
	// their reputation and still hold the craft, which is every cost
	// and no benefit.
	Unit->ReworkSecondsRemaining = 0.f;
	ConcessionReputationOwed +=
		FLBSpacecraftProductionCatalog::ConcessionReputationCost(Conceded);

	UE_LOG(LogTemp, Display,
		TEXT("SPACECRAFT MRB: %s SHIPS ON CONCESSION - %d defect points, ")
		TEXT("%d%% off settlement, %d reputation"),
		*UnitId.ToString(), Conceded,
		FLBSpacecraftProductionCatalog::ConcessionDeductionPercent(Conceded),
		FLBSpacecraftProductionCatalog::ConcessionReputationCost(Conceded));
	OutReason.Reset();
	return true;
}

bool ALBSpacecraftProductionAuthority::ScrapUnit(FName UnitId,
	FString& OutReason)
{
	const FLBSpacecraftUnitState* Unit = FindUnit(UnitId);
	if (Unit == nullptr)
	{
		OutReason = FString::Printf(TEXT("Unknown unit %s"),
			*UnitId.ToString());
		return false;
	}
	// A SOLD craft is somebody else's. Scrapping it would destroy a
	// record the ledger has already settled against, which is the kind
	// of quiet inconsistency the whole validate-before-mutate design
	// exists to make impossible.
	if (Unit->bCompleted && !Unit->bAwaitingSale)
	{
		OutReason = TEXT("That craft has already been delivered");
		return false;
	}
	const int32 Removed = Ledger.Units.RemoveAll(
		[UnitId](const FLBSpacecraftUnitState& Candidate)
		{
			return Candidate.UnitId == UnitId;
		});
	if (Removed <= 0)
	{
		// Unreachable given the lookup above, and still refused rather
		// than reported as success: a scrap that removed nothing while
		// claiming to have worked would leave the line blocked by a
		// craft the player believes is gone.
		OutReason = TEXT("Nothing was scrapped");
		return false;
	}
	UE_LOG(LogTemp, Display,
		TEXT("SPACECRAFT MRB: %s SCRAPPED"), *UnitId.ToString());
	OutReason.Reset();
	return true;
}

bool ALBSpacecraftProductionAuthority::OpenStationRework(FName UnitId,
	float Seconds, FString& OutReason)
{
	if (Seconds <= 0.f)
	{
		OutReason = TEXT("No rework to open");
		return false;
	}
	FLBSpacecraftUnitState* Unit = FindUnitMutable(UnitId);
	if (Unit == nullptr)
	{
		OutReason = FString::Printf(TEXT("Unknown unit %s"),
			*UnitId.ToString());
		return false;
	}
	Unit->ReworkSecondsRemaining += Seconds;
	OutReason = FString::Printf(TEXT("Rework opened: %.0f s"), Seconds);
	return true;
}

bool ALBSpacecraftProductionAuthority::AdvanceSimSeconds(double DeltaSeconds,
	FString& OutReason)
{
	if (DeltaSeconds < 0.0)
	{
		OutReason = TEXT("The sim clock never runs backwards");
		return false;
	}
	Ledger.SimSeconds += DeltaSeconds;
	// Stock finds its buyer on the clock: a craft built to stock sells
	// the moment an order it fits is on the books.
	SettleStockedCraft();
	// Rework burns down on the sim clock. When the last second is paid
	// the craft is clean again and its recorded FAIL is cleared, so
	// the hover test runs afresh - that retest is the way out.
	for (FLBSpacecraftUnitState& Unit : Ledger.Units)
	{
		if (Unit.ReworkSecondsRemaining <= 0.f)
		{
			continue;
		}
		Unit.ReworkSecondsRemaining -= static_cast<float>(DeltaSeconds);
		if (Unit.ReworkSecondsRemaining <= 0.f)
		{
			Unit.ReworkSecondsRemaining = 0.f;
			Unit.DefectPoints = 0;
			Unit.bQualityRecorded = false;
			Unit.bQualityPassed = false;
		}
	}
	for (FLBSpacecraftContract& Contract : Ledger.Contracts)
	{
		const bool bLive = Contract.State == ELBSpacecraftContractState::Offered
			|| Contract.State == ELBSpacecraftContractState::Accepted;
		if (bLive && Contract.DeadlineSimSeconds > 0.0
			&& Ledger.SimSeconds > Contract.DeadlineSimSeconds)
		{
			// An order you TOOK ON and did not finish is a failure and
			// costs your name; an offer you simply never accepted just
			// lapses off the board.
			Contract.State =
				Contract.State == ELBSpacecraftContractState::Accepted
					? ELBSpacecraftContractState::Expired
					: ELBSpacecraftContractState::Withdrawn;
		}
	}
	OutReason.Reset();
	return true;
}

bool ALBSpacecraftProductionAuthority::ValidateLedger(
	const FLBSpacecraftProductionLedgerState& State, FString& OutReason) const
{
	using namespace LBSpacecraftProductionAuthorityPrivate;
	if (State.SimSeconds < 0.0 || State.WIPCap <= 0
		|| State.RevenuePence < 0 || State.CashPence < 0)
	{
		OutReason = TEXT("Ledger scalars out of range");
		return false;
	}

	TSet<FName> UnitIds;
	int32 MaxSuffix = 0;
	const int32 StageCount =
		FLBSpacecraftProductionCatalog::StageTable().Num();
	for (const FLBSpacecraftUnitState& Unit : State.Units)
	{
		if (Unit.DefectPoints < 0 || Unit.ReworkSecondsRemaining < 0.f)
		{
			OutReason = TEXT("Unit defect/rework counters out of range");
			return false;
		}
		if (Unit.FailedQualityTests < 0)
		{
			OutReason = FString::Printf(
				TEXT("Unit %s has negative quality failures"),
				*Unit.UnitId.ToString());
			return false;
		}
		// A CONCESSION IS A SIGNED RECORD, so a save claiming one has
		// to carry what was signed. These two disagreeing means the
		// deviation cannot be priced, and a craft that cannot be priced
		// would settle for the wrong money in silence.
		if (Unit.ConcededDefectPoints < 0)
		{
			OutReason = FString::Printf(
				TEXT("Unit %s has negative conceded defects"),
				*Unit.UnitId.ToString());
			return false;
		}
		if (!Unit.bConcessionGranted && Unit.ConcededDefectPoints > 0)
		{
			OutReason = FString::Printf(
				TEXT("Unit %s records a conceded deviation without a ")
				TEXT("concession"), *Unit.UnitId.ToString());
			return false;
		}
		// ---- REFIT INVARIANTS ----
		//
		// EVERY ONE OF THESE IS GUARDED ON IsRefit() FIRST, and that is
		// not tidiness. A new build carries OriginUnitId == None, so an
		// unguarded rule keyed on that field buckets every ordinary
		// craft together under the empty name. With a WIP cap of 3 and
		// three offers on the board, that fires on the opening state of
		// a game containing no refits at all - and because SaveToSlot
		// validates BEFORE writing, the player would simply never be
		// able to save, told "TWO REFITS ARE OPEN ON CRAFT None".
		if (Unit.IsRefit())
		{
			// The entry rung has to be one a refit could have been sold
			// at, or the price it was bought for was never legal.
			FString EntryReason;
			if (!FLBSpacecraftProductionCatalog::IsLegalRefitEntryStage(
				Unit.EntryStage, EntryReason))
			{
				OutReason = FString::Printf(
					TEXT("Refit %s entered at an illegal stage: %s"),
					*Unit.UnitId.ToString(), *EntryReason);
				return false;
			}
			// A craft cannot stand BELOW where it joined. The ladder
			// only climbs, so this catches a save that has wound one
			// back to steal the work again.
			if (static_cast<int32>(Unit.Stage)
				< static_cast<int32>(Unit.EntryStage))
			{
				OutReason = FString::Printf(
					TEXT("Refit %s stands below the stage it joined at"),
					*Unit.UnitId.ToString());
				return false;
			}
			// It must still name a real hull.
			bool bFoundOrigin = false;
			for (const FLBSpacecraftUnitState& Other : State.Units)
			{
				if (Other.UnitId == Unit.OriginUnitId)
				{
					bFoundOrigin = true;
					break;
				}
			}
			if (!bFoundOrigin)
			{
				OutReason = FString::Printf(
					TEXT("Refit %s names a craft that does not exist: %s"),
					*Unit.UnitId.ToString(),
					*Unit.OriginUnitId.ToString());
				return false;
			}
			// A refit that has not been dispatched is live work, and a
			// hull can only be in the shop once.
			if (Unit.Stage != ELBSpacecraftStage::Dispatched)
			{
				for (const FLBSpacecraftUnitState& Other : State.Units)
				{
					if (Other.UnitId != Unit.UnitId && Other.IsRefit()
						&& Other.OriginUnitId == Unit.OriginUnitId
						&& Other.Stage != ELBSpacecraftStage::Dispatched)
					{
						OutReason = FString::Printf(
							TEXT("Two refits are open on craft %s"),
							*Unit.OriginUnitId.ToString());
						return false;
					}
				}
			}
		}
		else if (!Unit.AssignedContractId.IsNone())
		{
			// The assignment is what makes a refit settle against its
			// own order. On a new build it must be absent, or the two
			// halves of the identity disagree about what this craft is.
			OutReason = FString::Printf(
				TEXT("Unit %s is assigned to an order but is not a refit"),
				*Unit.UnitId.ToString());
			return false;
		}

		if (Unit.bConcessionGranted
			&& Unit.ConcededDefectPoints > FLBSpacecraftProductionCatalog
				::MaxConcedableDefectPoints())
		{
			// Above the ceiling no board could have signed it, so the
			// save is describing something the game cannot produce.
			OutReason = FString::Printf(
				TEXT("Unit %s concedes %d defects, over the limit of %d"),
				*Unit.UnitId.ToString(), Unit.ConcededDefectPoints,
				FLBSpacecraftProductionCatalog
					::MaxConcedableDefectPoints());
			return false;
		}
		if (Unit.UnitId.IsNone())
		{
			OutReason = TEXT("A saved unit has no ID");
			return false;
		}
		bool bAlready = false;
		UnitIds.Add(Unit.UnitId, &bAlready);
		if (bAlready)
		{
			OutReason = FString::Printf(TEXT("Duplicate unit ID %s"),
				*Unit.UnitId.ToString());
			return false;
		}
		FLBSpacecraftRecipe Recipe;
		if (!FLBSpacecraftProductionCatalog::FindRecipe(Unit.RecipeId, Recipe))
		{
			OutReason = FString::Printf(TEXT("Unit %s has unknown recipe"),
				*Unit.UnitId.ToString());
			return false;
		}
		if (static_cast<int32>(Unit.Stage) >= StageCount)
		{
			OutReason = TEXT("Unit stage outside the stage table");
			return false;
		}
		if (Unit.bCompleted
			!= (Unit.Stage == ELBSpacecraftStage::Dispatched))
		{
			OutReason = TEXT("Unit completion flag disagrees with its stage");
			return false;
		}
		if (Unit.bQualityPassed && !Unit.bQualityRecorded)
		{
			OutReason = TEXT("Unit claims a pass without a recorded result");
			return false;
		}
		MaxSuffix = FMath::Max(MaxSuffix, SpacecraftUnitSuffix(Unit.UnitId));
	}
	if (State.NextUnitSequence <= MaxSuffix)
	{
		OutReason = TEXT("Saved unit sequence would reuse an ID");
		return false;
	}

	TSet<FName> ContractIds;
	for (const FLBSpacecraftContract& Contract : State.Contracts)
	{
		if (Contract.ContractId.IsNone())
		{
			OutReason = TEXT("A saved contract has no ID");
			return false;
		}
		bool bAlready = false;
		ContractIds.Add(Contract.ContractId, &bAlready);
		if (bAlready)
		{
			OutReason = FString::Printf(TEXT("Duplicate contract ID %s"),
				*Contract.ContractId.ToString());
			return false;
		}
		FLBSpacecraftRecipe Recipe;
		if (!FLBSpacecraftProductionCatalog::FindRecipe(
			Contract.RecipeId, Recipe))
		{
			OutReason = TEXT("A saved contract has an unknown recipe");
			return false;
		}
		if (Contract.Quantity <= 0 || Contract.PricePerUnitPence <= 0
			|| Contract.DispatchedCount < 0
			|| Contract.DispatchedCount > Contract.Quantity)
		{
			OutReason = TEXT("Saved contract counts out of range");
			return false;
		}
		const bool bShouldBeComplete =
			Contract.DispatchedCount == Contract.Quantity;
		if (bShouldBeComplete
			&& Contract.State == ELBSpacecraftContractState::Accepted)
		{
			OutReason = TEXT("Fully dispatched contract not marked complete");
			return false;
		}
		if (Contract.State == ELBSpacecraftContractState::Complete
			&& !bShouldBeComplete)
		{
			OutReason = TEXT("Contract marked complete with demand left");
			return false;
		}
	}
	OutReason.Reset();
	return true;
}

bool ALBSpacecraftProductionAuthority::RestoreLedger(
	const FLBSpacecraftProductionLedgerState& State, FString& OutReason)
{
	if (!ValidateLedger(State, OutReason))
	{
		return false; // ledger untouched - restore is all or nothing
	}
	Ledger = State;
	OutReason.Reset();
	return true;
}

const FLBSpacecraftUnitState* ALBSpacecraftProductionAuthority::FindUnit(
	FName UnitId) const
{
	for (const FLBSpacecraftUnitState& Unit : Ledger.Units)
	{
		if (Unit.UnitId == UnitId)
		{
			return &Unit;
		}
	}
	return nullptr;
}

const FLBSpacecraftContract* ALBSpacecraftProductionAuthority::FindContract(
	FName ContractId) const
{
	for (const FLBSpacecraftContract& Contract : Ledger.Contracts)
	{
		if (Contract.ContractId == ContractId)
		{
			return &Contract;
		}
	}
	return nullptr;
}

FLBSpacecraftContract* ALBSpacecraftProductionAuthority::FindContractMutable(
	FName ContractId)
{
	return const_cast<FLBSpacecraftContract*>(FindContract(ContractId));
}

FLBSpacecraftUnitState* ALBSpacecraftProductionAuthority::FindUnitMutable(
	FName UnitId)
{
	return const_cast<FLBSpacecraftUnitState*>(FindUnit(UnitId));
}
