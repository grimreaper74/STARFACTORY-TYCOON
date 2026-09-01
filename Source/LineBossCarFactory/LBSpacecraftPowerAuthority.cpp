#include "LBSpacecraftPowerAuthority.h"

#include "LBSpacecraftProductionAuthority.h"

ALBSpacecraftPowerAuthority::ALBSpacecraftPowerAuthority()
{
	PrimaryActorTick.bCanEverTick = false;
}

const FLBSpacecraftPowerEntry* ALBSpacecraftPowerAuthority::FindEntry(
	const TArray<FLBSpacecraftPowerEntry>& Entries, FName EntryId)
{
	for (const FLBSpacecraftPowerEntry& Entry : Entries)
	{
		if (Entry.EntryId == EntryId)
		{
			return &Entry;
		}
	}
	return nullptr;
}

int32 ALBSpacecraftPowerAuthority::SumKilowatts(
	const TArray<FLBSpacecraftPowerEntry>& Entries)
{
	int32 Total = 0;
	for (const FLBSpacecraftPowerEntry& Entry : Entries)
	{
		Total += Entry.Kilowatts;
	}
	return Total;
}

bool ALBSpacecraftPowerAuthority::RegisterSupply(FName SourceId,
	int32 CapacityKw, FString& OutReason)
{
	if (SourceId.IsNone())
	{
		OutReason = TEXT("SUPPLY REGISTRATION REQUIRES AN ID");
		return false;
	}
	if (CapacityKw <= 0)
	{
		OutReason = TEXT("SUPPLY CAPACITY MUST BE POSITIVE");
		return false;
	}
	if (FindEntry(Supplies, SourceId) != nullptr)
	{
		OutReason = FString::Printf(TEXT("SUPPLY %s ALREADY EXISTS"),
			*SourceId.ToString());
		return false;
	}
	FLBSpacecraftPowerEntry Entry;
	Entry.EntryId = SourceId;
	Entry.Kilowatts = CapacityKw;
	Supplies.Add(Entry);
	OutReason = FString::Printf(TEXT("SUPPLY %s ONLINE (%d kW)"),
		*SourceId.ToString(), CapacityKw);
	return true;
}

bool ALBSpacecraftPowerAuthority::RemoveSupply(FName SourceId,
	FString& OutReason)
{
	for (int32 Index = 0; Index < Supplies.Num(); ++Index)
	{
		if (Supplies[Index].EntryId != SourceId)
		{
			continue;
		}
		const int32 RemainingSupply =
			GetTotalSupplyKw() - Supplies[Index].Kilowatts;
		if (RemainingSupply < GetTotalDrawKw())
		{
			OutReason = FString::Printf(
				TEXT("REMOVING %s WOULD STRAND %d kW OF LOAD - SHED FIRST"),
				*SourceId.ToString(), GetTotalDrawKw() - RemainingSupply);
			return false;
		}
		Supplies.RemoveAt(Index);
		OutReason = TEXT("SUPPLY REMOVED");
		return true;
	}
	OutReason = FString::Printf(TEXT("UNKNOWN SUPPLY %s"),
		*SourceId.ToString());
	return false;
}

bool ALBSpacecraftPowerAuthority::ConnectLoad(FName LoadId, int32 DrawKw,
	FString& OutReason)
{
	if (LoadId.IsNone())
	{
		OutReason = TEXT("LOAD CONNECTION REQUIRES AN ID");
		return false;
	}
	if (DrawKw <= 0)
	{
		OutReason = TEXT("LOAD DRAW MUST BE POSITIVE");
		return false;
	}
	if (FindEntry(Loads, LoadId) != nullptr)
	{
		OutReason = FString::Printf(TEXT("LOAD %s ALREADY CONNECTED"),
			*LoadId.ToString());
		return false;
	}
	if (GetTotalDrawKw() + DrawKw > GetTotalSupplyKw())
	{
		OutReason = FString::Printf(
			TEXT("LOAD %s NEEDS %d kW BUT ONLY %d kW HEADROOM - BUILD POWER"),
			*LoadId.ToString(), DrawKw, GetHeadroomKw());
		return false;
	}
	FLBSpacecraftPowerEntry Entry;
	Entry.EntryId = LoadId;
	Entry.Kilowatts = DrawKw;
	Loads.Add(Entry);
	OutReason = FString::Printf(TEXT("LOAD %s CONNECTED (%d kW)"),
		*LoadId.ToString(), DrawKw);
	return true;
}

bool ALBSpacecraftPowerAuthority::DisconnectLoad(FName LoadId,
	FString& OutReason)
{
	for (int32 Index = 0; Index < Loads.Num(); ++Index)
	{
		if (Loads[Index].EntryId == LoadId)
		{
			Loads.RemoveAt(Index);
			OutReason = TEXT("LOAD DISCONNECTED");
			return true;
		}
	}
	OutReason = FString::Printf(TEXT("UNKNOWN LOAD %s"),
		*LoadId.ToString());
	return false;
}

int32 ALBSpacecraftPowerAuthority::GetTotalSupplyKw() const
{
	// The mains feed rides on top of own generation - unless the meter
	// is in arrears, when the grid stops extending credit (existing
	// loads stay lit; NEW connections must fit own generation).
	return SumKilowatts(Supplies) + (bGridArrears ? 0 : GridFeedKw);
}

int32 ALBSpacecraftPowerAuthority::GetOwnSupplyKw() const
{
	return SumKilowatts(Supplies);
}

int32 ALBSpacecraftPowerAuthority::GetGridUseKw() const
{
	return FMath::Clamp(GetTotalDrawKw() - SumKilowatts(Supplies), 0,
		GridFeedKw);
}

int32 ALBSpacecraftPowerAuthority::GetGridExportKw() const
{
	// A generator THROTTLES TO ITS LOAD - it does not burn away at
	// full output into an empty factory. Export is therefore capped by
	// the site's own draw as well as by the feed: a working factory
	// with spare capacity sells its surplus, an IDLE one sells
	// nothing.
	//
	// Without this cap the starter plant exported its full 800 kW from
	// the first frame with the floor drawing nothing, paying the
	// player 200 cr a sim-minute to leave the game running. Cash that
	// strictly increases while you do nothing takes the downside out
	// of every build decision. PROVISIONAL shape pending the owner's
	// economy tuning; the feed-in tariff itself is unchanged.
	const int32 DrawKw = GetTotalDrawKw();
	const int32 Surplus = SumKilowatts(Supplies) - DrawKw;
	return FMath::Clamp(FMath::Min(Surplus, DrawKw), 0, GridFeedKw);
}

void ALBSpacecraftPowerAuthority::TickGridMeter(double DeltaSeconds,
	ALBSpacecraftProductionAuthority* InLedger)
{
	if (DeltaSeconds <= 0.0 || InLedger == nullptr)
	{
		return;
	}
	const int32 GridKw = GetGridUseKw();
	if (GridKw <= 0)
	{
		// Own generation covers the floor: nothing metered, and a paid
		// bill clears any arrears (the utility reconnects). SURPLUS is
		// sold back to the electric company at the feed-in tariff
		// (owner 2026-08-26, the Car Manufacture model).
		bGridArrears = false;
		const int32 ExportKw = GetGridExportKw();
		if (ExportKw > 0)
		{
			GridPenceAccrued -= static_cast<double>(ExportKw)
				* static_cast<double>(GridSellbackPencePerKwMinute)
				* (DeltaSeconds / 60.0);
			const int64 Earned =
				static_cast<int64>(-GridPenceAccrued);
			if (Earned > 0)
			{
				FString EarnReason;
				InLedger->EarnPence(Earned, EarnReason);
				GridPenceAccrued += static_cast<double>(Earned);
			}
		}
		return;
	}
	GridPenceAccrued += static_cast<double>(GridKw)
		* static_cast<double>(GridTariffPencePerKwMinute)
		* (DeltaSeconds / 60.0);
	const int64 Due = static_cast<int64>(GridPenceAccrued);
	if (Due <= 0)
	{
		return;
	}
	FString Reason;
	if (InLedger->SpendPence(Due, Reason))
	{
		GridPenceAccrued -= static_cast<double>(Due);
		bGridArrears = false;
	}
	else
	{
		// The bill cannot be paid: arrears - the grid stops extending
		// NEW credit (fail closed, named) but nothing browns out.
		bGridArrears = true;
	}
}

int32 ALBSpacecraftPowerAuthority::GetTotalDrawKw() const
{
	return SumKilowatts(Loads);
}

bool ALBSpacecraftPowerAuthority::HasLoad(FName LoadId) const
{
	return FindEntry(Loads, LoadId) != nullptr;
}

FLBSpacecraftPowerSnapshot
ALBSpacecraftPowerAuthority::CaptureSnapshot() const
{
	FLBSpacecraftPowerSnapshot Snapshot;
	Snapshot.Supplies = Supplies;
	Snapshot.Loads = Loads;
	return Snapshot;
}

bool ALBSpacecraftPowerAuthority::ValidateSnapshot(
	const FLBSpacecraftPowerSnapshot& Snapshot, FString& OutReason,
	int32 InGridFeedKw)
{
	int32 Totals[2] = {0, 0};
	const TArray<FLBSpacecraftPowerEntry>* Sides[2] =
		{&Snapshot.Supplies, &Snapshot.Loads};
	for (int32 Side = 0; Side < 2; ++Side)
	{
		TSet<FName> SeenIds;
		for (const FLBSpacecraftPowerEntry& Entry : *Sides[Side])
		{
			if (Entry.EntryId.IsNone() || Entry.Kilowatts <= 0)
			{
				OutReason = TEXT("SNAPSHOT POWER ENTRY IS MALFORMED");
				return false;
			}
			if (SeenIds.Contains(Entry.EntryId))
			{
				OutReason = FString::Printf(
					TEXT("SNAPSHOT DUPLICATES POWER ENTRY %s"),
					*Entry.EntryId.ToString());
				return false;
			}
			SeenIds.Add(Entry.EntryId);
			Totals[Side] += Entry.Kilowatts;
		}
	}
	if (Totals[1] > Totals[0] + InGridFeedKw)
	{
		OutReason = FString::Printf(
			TEXT("SNAPSHOT DRAW %d kW EXCEEDS SUPPLY %d kW PLUS GRID ")
			TEXT("FEED %d kW"), Totals[1], Totals[0], InGridFeedKw);
		return false;
	}
	OutReason = TEXT("SNAPSHOT VALID");
	return true;
}

bool ALBSpacecraftPowerAuthority::RestoreSnapshot(
	const FLBSpacecraftPowerSnapshot& Snapshot, FString& OutReason)
{
	// Whole-snapshot validation BEFORE a single mutation (repo law).
	// The instance knows its mains feed; a grid-billed factory is a
	// legal thing to restore.
	if (!ValidateSnapshot(Snapshot, OutReason, GridFeedKw))
	{
		return false;
	}
	Supplies = Snapshot.Supplies;
	Loads = Snapshot.Loads;
	OutReason = TEXT("POWER RESTORED");
	return true;
}
