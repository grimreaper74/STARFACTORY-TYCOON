#include "LBSpacecraftProgressionAuthority.h"
#include "LBSpacecraftBuildAuthority.h"

#include "LBSpacecraftProductionAuthority.h"

ALBSpacecraftProgressionAuthority::ALBSpacecraftProgressionAuthority()
{
	PrimaryActorTick.bCanEverTick = false;
}

void ALBSpacecraftProgressionAuthority::SyncFromLedger(
	const ALBSpacecraftProductionAuthority* InLedger)
{
	if (InLedger == nullptr)
	{
		return;
	}
	int32 Complete = 0;
	for (const FLBSpacecraftContract& Contract :
		InLedger->GetContracts())
	{
		if (Contract.State == ELBSpacecraftContractState::Complete)
		{
			++Complete;
		}
	}
	// Monotonic: deliveries only ever accumulate.
	CreditedDeliveries = FMath::Max(CreditedDeliveries, Complete);
}

bool ALBSpacecraftProgressionAuthority::IsUnlocked(
	ELBSpacecraftUnlock Unlock) const
{
	switch (Unlock)
	{
	case ELBSpacecraftUnlock::Belts:
		return CreditedDeliveries >= DeliveriesForBelts;
	case ELBSpacecraftUnlock::Fabrication:
		return CreditedDeliveries >= DeliveriesForFabrication;
	case ELBSpacecraftUnlock::QualityControl:
		return CreditedDeliveries >= DeliveriesForQuality;
	}
	return false;
}

FString ALBSpacecraftProgressionAuthority::DescribeLock(
	ELBSpacecraftUnlock Unlock) const
{
	int32 Needed = 0;
	const TCHAR* What = TEXT("");
	switch (Unlock)
	{
	case ELBSpacecraftUnlock::Belts:
		Needed = DeliveriesForBelts;
		What = TEXT("CONVEYOR BELTS");
		break;
	case ELBSpacecraftUnlock::Fabrication:
		Needed = DeliveriesForFabrication;
		What = TEXT("ON-SITE FABRICATION");
		break;
	case ELBSpacecraftUnlock::QualityControl:
		Needed = DeliveriesForQuality;
		What = TEXT("QUALITY CONTROL");
		break;
	}
	// Short enough to survive the panel's row width (owner 2026-09-01:
	// the long form truncated mid-word, which reads as a bug). The
	// contract phrase "UNLOCKS AFTER DELIVERY" is load-bearing - a
	// transport test greps for it.
	return FString::Printf(
		TEXT("UNLOCKS AFTER DELIVERY %d: %s (%d done)"),
		Needed, What, CreditedDeliveries);
}

FIntPoint ALBSpacecraftProgressionAuthority::BayForPointCm(
	const FVector& PointCm) const
{
	return FIntPoint(
		FMath::FloorToInt(PointCm.X / BayEdgeCm),
		FMath::FloorToInt(PointCm.Y / BayEdgeCm));
}

bool ALBSpacecraftProgressionAuthority::IsBayOwned(FIntPoint Bay) const
{
	return OwnedBays.Contains(Bay);
}

bool ALBSpacecraftProgressionAuthority::IsRunwayLand(FIntPoint Bay) const
{
	// The +X strip beyond the reserve line is the sprint corridor.
	// Review fix: the spurious +BayEdgeCm pushed the protection line a
	// whole bay off the floor, making the guard vacuous. A bay is
	// runway land when ANY part of it crosses the reserve line.
	const float BayMaxX = (Bay.X + 1) * BayEdgeCm;
	return BayMaxX >
		ALBSpacecraftBuildAuthority::SiteHalfExtentCm() - RunwayReserveCm;
}

bool ALBSpacecraftProgressionAuthority::IsAdjacentToOwned(
	FIntPoint Bay) const
{
	if (OwnedBays.Num() == 0)
	{
		return true; // the very first land needs no neighbour
	}
	static const FIntPoint Sides[] = {
		FIntPoint(1, 0), FIntPoint(-1, 0),
		FIntPoint(0, 1), FIntPoint(0, -1) };
	for (const FIntPoint& Side : Sides)
	{
		if (OwnedBays.Contains(Bay + Side))
		{
			return true;
		}
	}
	return false;
}

bool ALBSpacecraftProgressionAuthority::IsFootprintOwned(
	const FVector& CentreCm, const FVector2D& FootprintCm,
	FString& OutReason) const
{
	const FVector Corners[] = {
		CentreCm + FVector(FootprintCm.X * 0.5f, FootprintCm.Y * 0.5f, 0),
		CentreCm + FVector(-FootprintCm.X * 0.5f, FootprintCm.Y * 0.5f, 0),
		CentreCm + FVector(FootprintCm.X * 0.5f, -FootprintCm.Y * 0.5f, 0),
		CentreCm + FVector(-FootprintCm.X * 0.5f,
			-FootprintCm.Y * 0.5f, 0) };
	for (const FVector& Corner : Corners)
	{
		const FIntPoint Bay = BayForPointCm(Corner);
		if (!IsBayOwned(Bay))
		{
			OutReason = FString::Printf(
				TEXT("BAY (%d,%d) IS NOT YOURS - BUY THE BAY FIRST"),
				Bay.X, Bay.Y);
			return false;
		}
	}
	return true;
}

bool ALBSpacecraftProgressionAuthority::PurchaseBay(FIntPoint Bay,
	ALBSpacecraftProductionAuthority* InLedger, FString& OutReason)
{
	if (IsBayOwned(Bay))
	{
		OutReason = FString::Printf(TEXT("BAY (%d,%d) IS ALREADY YOURS"),
			Bay.X, Bay.Y);
		return false;
	}
	// Review fix: bays beyond the buildable floor are not for sale.
	const float FloorHalfCm =
		ALBSpacecraftBuildAuthority::SiteHalfExtentCm();
	if (Bay.X * BayEdgeCm >= FloorHalfCm
		|| (Bay.X + 1) * BayEdgeCm <= -FloorHalfCm
		|| Bay.Y * BayEdgeCm >= FloorHalfCm
		|| (Bay.Y + 1) * BayEdgeCm <= -FloorHalfCm)
	{
		OutReason = FString::Printf(
			TEXT("BAY (%d,%d) IS OFF THE FLOOR"), Bay.X, Bay.Y);
		return false;
	}
	if (IsRunwayLand(Bay))
	{
		OutReason = TEXT(
			"THAT IS RUNWAY LAND - THE LAUNCH CORRIDOR IS NOT FOR SALE");
		return false;
	}
	if (!IsAdjacentToOwned(Bay))
	{
		OutReason = FString::Printf(
			TEXT("BAY (%d,%d) DOES NOT TOUCH YOUR LAND"), Bay.X, Bay.Y);
		return false;
	}
	if (InLedger != nullptr
		&& !InLedger->SpendPence(BayCostPence, OutReason))
	{
		return false; // the refusal names the shortfall
	}
	OwnedBays.Add(Bay);
	OutReason = FString::Printf(TEXT("BAY (%d,%d) PURCHASED"),
		Bay.X, Bay.Y);
	return true;
}

bool ALBSpacecraftProgressionAuthority::SeedStartingBays(
	FString& OutReason)
{
	if (OwnedBays.Num() > 0)
	{
		OutReason = TEXT("LAND ALREADY SEEDED");
		return false;
	}
	// THE STARTING PLOT is the middle 440 m of the 600 m site: room for
	// the three site buildings at their shared 120 m scale with space
	// between them for roads, and an outer ring still to buy (owner
	// 2026-08-28: bigger map, same-scale buildings the player places).
	int32 Granted = 0;
	for (int32 X = -4; X <= 3; ++X)
	{
		for (int32 Y = -4; Y <= 3; ++Y)
		{
			const FIntPoint Bay(X, Y);
			if (IsRunwayLand(Bay))
			{
				continue;
			}
			OwnedBays.Add(Bay);
			++Granted;
		}
	}
	OutReason = FString::Printf(TEXT("STARTING LAND READY - %d BAYS"),
		Granted);
	return true;
}

FLBSpacecraftProgressionSnapshot
ALBSpacecraftProgressionAuthority::CaptureSnapshot() const
{
	FLBSpacecraftProgressionSnapshot Snapshot;
	Snapshot.CreditedDeliveries = CreditedDeliveries;
	Snapshot.OwnedBays = OwnedBays;
	return Snapshot;
}

bool ALBSpacecraftProgressionAuthority::ValidateSnapshot(
	const FLBSpacecraftProgressionSnapshot& Snapshot,
	FString& OutReason) const
{
	if (Snapshot.CreditedDeliveries < 0)
	{
		OutReason = TEXT("SNAPSHOT DELIVERY COUNT IS NEGATIVE");
		return false;
	}
	TSet<FIntPoint> Seen;
	for (const FIntPoint& Bay : Snapshot.OwnedBays)
	{
		if (Seen.Contains(Bay))
		{
			OutReason = FString::Printf(
				TEXT("SNAPSHOT DUPLICATES BAY (%d,%d)"), Bay.X, Bay.Y);
			return false;
		}
		Seen.Add(Bay);
		if (IsRunwayLand(Bay))
		{
			OutReason = FString::Printf(
				TEXT("SNAPSHOT OWNS RUNWAY LAND (%d,%d)"), Bay.X, Bay.Y);
			return false;
		}
	}
	OutReason = TEXT("SNAPSHOT VALID");
	return true;
}

bool ALBSpacecraftProgressionAuthority::RestoreSnapshot(
	const FLBSpacecraftProgressionSnapshot& Snapshot, FString& OutReason)
{
	// Validate the ENTIRE snapshot before a single mutation.
	if (!ValidateSnapshot(Snapshot, OutReason))
	{
		return false;
	}
	CreditedDeliveries = Snapshot.CreditedDeliveries;
	OwnedBays = Snapshot.OwnedBays;
	OutReason = TEXT("PROGRESSION RESTORED");
	return true;
}
