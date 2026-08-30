#include "LBSpacecraftReputationAuthority.h"

#include "LBSpacecraftDifficulty.h"
#include "LBSpacecraftProductionAuthority.h"

ALBSpacecraftReputationAuthority::ALBSpacecraftReputationAuthority()
{
	PrimaryActorTick.bCanEverTick = false;
}

int32 ALBSpacecraftReputationAuthority::TierForPoints(int32 InPoints)
{
	// PROVISIONAL thresholds pending the owner's economy tuning.
	if (InPoints >= 50)
	{
		return 4;
	}
	if (InPoints >= 25)
	{
		return 3;
	}
	if (InPoints >= 10)
	{
		return 2;
	}
	return 1;
}

int32 ALBSpacecraftReputationAuthority::PointsForDeliveredValuePence(
	int64 ValuePence) const
{
	if (ValuePence <= 0 || PencePerReputationPoint <= 0)
	{
		return 0;
	}
	// At the shipped rate a 50,000 cr Scout is worth two points - the
	// old flat rate - and a Cargo, being the harder job, is worth more.
	return static_cast<int32>(ValuePence / PencePerReputationPoint);
}

int32 ALBSpacecraftReputationAuthority::PricePremiumPercentForTier(int32 Tier)
{
	return 5 * FMath::Max(Tier - 1, 0);
}

int64 ALBSpacecraftReputationAuthority::ApplyTierPremiumPence(int64 BasePence,
	int32 Tier)
{
	if (BasePence <= 0)
	{
		return BasePence;
	}
	return BasePence * (100 + PricePremiumPercentForTier(Tier)) / 100;
}

int32 ALBSpacecraftReputationAuthority::LatePenaltyForContract(
	const FLBSpacecraftContract& Contract) const
{
	// Twice what the whole order would have earned, with a floor so
	// even a small failure is felt.
	const int32 Earned = PointsForDeliveredValuePence(
		Contract.PricePerUnitPence
		* static_cast<int64>(FMath::Max(Contract.Quantity, 0)));
	const int32 Base = FMath::Max(3, Earned * 2);
	// What failing costs is a difficulty dial.
	return FMath::Max(1, static_cast<int32>(Base
		* FMath::Max(FLBSpacecraftDifficulty::Current().LatePenaltyScale,
			0.f)));
}

int32 ALBSpacecraftReputationAuthority::GetTier() const
{
	return TierForPoints(Points);
}

void ALBSpacecraftReputationAuthority::SyncFromLedger(
	const ALBSpacecraftProductionAuthority* InProduction)
{
	if (InProduction == nullptr)
	{
		return;
	}
	// EVERY DELIVERY builds the name, not just a finished contract -
	// the customer saw each ship arrive.
	for (const FLBSpacecraftContract& Contract :
		InProduction->GetContracts())
	{
		const int32 Fresh =
			LBSpacecraftCreditPrivate::SpacecraftClaimNewDeliveries(
				DeliveryCredits, CreditedContracts, Contract);
		if (Fresh > 0)
		{
			Points += PointsForDeliveredValuePence(
				Contract.PricePerUnitPence * static_cast<int64>(Fresh));
		}
		// A MISSED DEADLINE costs the name it would have built. Docked
		// once, and only for an order actually taken on - an offer
		// nobody accepted simply rotted off the board.
		if (Contract.State == ELBSpacecraftContractState::Expired
			&& Contract.DispatchedCount < Contract.Quantity
			&& !PenalisedContracts.Contains(Contract.ContractId))
		{
			PenalisedContracts.Add(Contract.ContractId);
			Points = FMath::Max(0,
				Points - LatePenaltyForContract(Contract));
		}
	}
}

FLBSpacecraftReputationSnapshot
ALBSpacecraftReputationAuthority::CaptureSnapshot() const
{
	FLBSpacecraftReputationSnapshot Snapshot;
	Snapshot.Points = Points;
	Snapshot.CreditedContracts = CreditedContracts;
	Snapshot.DeliveryCredits = DeliveryCredits;
	Snapshot.PenalisedContracts = PenalisedContracts;
	return Snapshot;
}

bool ALBSpacecraftReputationAuthority::ValidateSnapshot(
	const FLBSpacecraftReputationSnapshot& Snapshot, FString& OutReason)
{
	if (Snapshot.Points < 0)
	{
		OutReason = TEXT("SNAPSHOT BANKS NEGATIVE REPUTATION");
		return false;
	}
	TSet<FName> Seen;
	for (const FName& ContractId : Snapshot.CreditedContracts)
	{
		if (ContractId.IsNone())
		{
			OutReason = TEXT("SNAPSHOT CREDITS A NAMELESS CONTRACT");
			return false;
		}
		if (Seen.Contains(ContractId))
		{
			OutReason = TEXT("SNAPSHOT CREDITS A CONTRACT TWICE");
			return false;
		}
		Seen.Add(ContractId);
	}
	for (const FLBSpacecraftDeliveryCredit& Credit :
		Snapshot.DeliveryCredits)
	{
		if (Credit.ContractId.IsNone())
		{
			OutReason = TEXT("SNAPSHOT CREDITS A NAMELESS CONTRACT");
			return false;
		}
		if (Credit.CreditedDeliveries < 0)
		{
			OutReason = TEXT("SNAPSHOT CREDITS NEGATIVE DELIVERIES");
			return false;
		}
		if (Seen.Contains(Credit.ContractId))
		{
			OutReason = TEXT("SNAPSHOT CREDITS A CONTRACT TWICE");
			return false;
		}
		Seen.Add(Credit.ContractId);
	}
	OutReason = TEXT("SNAPSHOT VALID");
	return true;
}

bool ALBSpacecraftReputationAuthority::RestoreSnapshot(
	const FLBSpacecraftReputationSnapshot& Snapshot, FString& OutReason)
{
	// Whole-snapshot validation BEFORE a single mutation (repo law).
	if (!ValidateSnapshot(Snapshot, OutReason))
	{
		return false;
	}
	Points = Snapshot.Points;
	CreditedContracts = Snapshot.CreditedContracts;
	DeliveryCredits = Snapshot.DeliveryCredits;
	PenalisedContracts = Snapshot.PenalisedContracts;
	OutReason = TEXT("REPUTATION RESTORED");
	return true;
}
