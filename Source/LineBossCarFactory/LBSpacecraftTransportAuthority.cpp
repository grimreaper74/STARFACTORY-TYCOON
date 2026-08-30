#include "LBSpacecraftTransportAuthority.h"

#include "LBSpacecraftBuildAuthority.h"
#include "LBSpacecraftInventoryAuthority.h"
#include "LBSpacecraftProductionAuthority.h"
#include "LBSpacecraftProgressionAuthority.h"

ALBSpacecraftTransportAuthority::ALBSpacecraftTransportAuthority()
{
	PrimaryActorTick.bCanEverTick = false;
}

TArray<FVector> ALBSpacecraftTransportAuthority::ComputeBeltPathCm(
	const FVector& StartCm, const FVector& EndCm)
{
	auto Snap = [](float Value)
	{
		return FMath::GridSnap(Value, 100.f);
	};
	const FVector Start(Snap(StartCm.X), Snap(StartCm.Y), 0.f);
	const FVector End(Snap(EndCm.X), Snap(EndCm.Y), 0.f);
	TArray<FVector> Path;
	Path.Add(Start);
	// Deterministic two-leg route: corner at (End.X, Start.Y). A
	// degenerate leg (already aligned) collapses to a straight belt.
	const FVector Corner(End.X, Start.Y, 0.f);
	if (!Corner.Equals(Start, 1.f) && !Corner.Equals(End, 1.f))
	{
		Path.Add(Corner);
	}
	Path.Add(End);
	return Path;
}

int64 ALBSpacecraftTransportAuthority::ComputeBeltCostPence(
	const TArray<FVector>& PathPointsCm) const
{
	float LengthCm = 0.f;
	for (int32 Index = 0; Index + 1 < PathPointsCm.Num(); ++Index)
	{
		LengthCm += FVector::Dist2D(PathPointsCm[Index],
			PathPointsCm[Index + 1]);
	}
	// Review fix: a sub-metre run still costs one metre - a zero
	// price would be refused by the ledger's positive-spend guard.
	return FMath::Max<int64>(1, static_cast<int64>(LengthCm / 100.f))
		* BeltCostPerMetrePence;
}

const FLBSpacecraftBeltRoute*
ALBSpacecraftTransportAuthority::FindRouteForStation(FName StationId) const
{
	for (const FLBSpacecraftBeltRoute& Route : Routes)
	{
		if (Route.StationId == StationId)
		{
			return &Route;
		}
	}
	return nullptr;
}

float ALBSpacecraftTransportAuthority::GetStationSpeedMultiplier(
	FName StationId) const
{
	// Unbelted stations still work: drones ferry (slower, never broken).
	return FindRouteForStation(StationId) != nullptr
		? BeltedSpeedMultiplier : 1.f;
}

bool ALBSpacecraftTransportAuthority::ConnectSupplyBelt(
	const ALBSpacecraftBuildAuthority& InBuild,
	const ALBSpacecraftInventoryAuthority& InInventory,
	ALBSpacecraftProductionAuthority* InLedger, FName StationId,
	FName StoreId, FName& OutRouteId, FString& OutReason,
	const ALBSpacecraftProgressionAuthority* InProgression)
{
	OutRouteId = NAME_None;
	// Review fix: the unlock gate lives HERE, in the owning authority -
	// call sites cannot forget it.
	if (InProgression != nullptr
		&& !InProgression->IsUnlocked(ELBSpacecraftUnlock::Belts))
	{
		OutReason = InProgression->DescribeLock(
			ELBSpacecraftUnlock::Belts);
		return false;
	}
	const FLBSpacecraftStationRecord* Station = nullptr;
	for (const FLBSpacecraftStationRecord& Record : InBuild.GetStations())
	{
		if (Record.StationId == StationId)
		{
			Station = &Record;
			break;
		}
	}
	if (Station == nullptr)
	{
		OutReason = FString::Printf(
			TEXT("UNKNOWN STATION %s - NO BELT BUILT"),
			*StationId.ToString());
		return false;
	}
	if (!InInventory.HasStore(StoreId))
	{
		OutReason = FString::Printf(
			TEXT("UNKNOWN STORE %s - NO BELT BUILT"),
			*StoreId.ToString());
		return false;
	}
	if (FindRouteForStation(StationId) != nullptr)
	{
		OutReason = FString::Printf(
			TEXT("%s ALREADY HAS A SUPPLY BELT - REMOVE IT FIRST"),
			*StationId.ToString());
		return false;
	}
	// v002 stores have no world transform of their own; the belt runs
	// from the station to the floor-store apron at the dock wall.
	const FVector StationCm = Station->WorldTransform.GetLocation();
	const FVector StoreCm(-11000.f + 1100.f, 0.f, 0.f);
	FLBSpacecraftBeltRoute Route;
	Route.PathPointsCm = ComputeBeltPathCm(StationCm, StoreCm);
	const int64 CostPence = ComputeBeltCostPence(Route.PathPointsCm);
	if (InLedger != nullptr
		&& !InLedger->SpendPence(CostPence, OutReason))
	{
		return false; // the refusal already names the shortfall
	}
	Route.RouteId = FName(*FString::Printf(TEXT("BELT-%04d"),
		NextRouteSequence++));
	Route.StationId = StationId;
	Route.StoreId = StoreId;
	Route.MarkLevel = 1;
	Routes.Add(Route);
	OutRouteId = Route.RouteId;
	OutReason = FString::Printf(
		TEXT("BELT %s CONNECTED - %s CRAFTS FASTER NOW"),
		*Route.RouteId.ToString(), *StationId.ToString());
	return true;
}

bool ALBSpacecraftTransportAuthority::DisconnectBelt(
	ALBSpacecraftProductionAuthority* InLedger, FName RouteId,
	FString& OutReason)
{
	for (int32 Index = 0; Index < Routes.Num(); ++Index)
	{
		if (Routes[Index].RouteId != RouteId)
		{
			continue;
		}
		if (InLedger != nullptr)
		{
			const int64 Refund = ComputeBeltCostPence(
				Routes[Index].PathPointsCm)
				* RemovalRefundPercent / 100;
			FString EarnReason;
			InLedger->EarnPence(Refund, EarnReason);
		}
		Routes.RemoveAt(Index);
		OutReason = FString::Printf(TEXT("BELT %s REMOVED"),
			*RouteId.ToString());
		return true;
	}
	OutReason = FString::Printf(TEXT("UNKNOWN BELT %s"),
		*RouteId.ToString());
	return false;
}

void ALBSpacecraftTransportAuthority::SyncFromBuild(
	const ALBSpacecraftBuildAuthority* InBuild)
{
	if (InBuild == nullptr)
	{
		return;
	}
	TSet<FName> Alive;
	for (const FLBSpacecraftStationRecord& Record : InBuild->GetStations())
	{
		Alive.Add(Record.StationId);
	}
	for (int32 Index = Routes.Num() - 1; Index >= 0; --Index)
	{
		if (!Alive.Contains(Routes[Index].StationId))
		{
			Routes.RemoveAt(Index);
		}
	}
}

FLBSpacecraftTransportSnapshot
ALBSpacecraftTransportAuthority::CaptureSnapshot() const
{
	FLBSpacecraftTransportSnapshot Snapshot;
	Snapshot.Routes = Routes;
	Snapshot.NextRouteSequence = NextRouteSequence;
	return Snapshot;
}

bool ALBSpacecraftTransportAuthority::ValidateSnapshot(
	const FLBSpacecraftTransportSnapshot& Snapshot,
	FString& OutReason) const
{
	TSet<FName> Seen;
	int32 HighestSequence = 0;
	for (const FLBSpacecraftBeltRoute& Route : Snapshot.Routes)
	{
		if (Route.RouteId.IsNone() || Route.StationId.IsNone()
			|| Route.StoreId.IsNone())
		{
			OutReason = TEXT("SNAPSHOT BELT ROUTE IS MALFORMED");
			return false;
		}
		if (Seen.Contains(Route.RouteId))
		{
			OutReason = FString::Printf(
				TEXT("SNAPSHOT DUPLICATES BELT %s"),
				*Route.RouteId.ToString());
			return false;
		}
		Seen.Add(Route.RouteId);
		if (Route.PathPointsCm.Num() < 2)
		{
			OutReason = FString::Printf(
				TEXT("SNAPSHOT BELT %s HAS NO PATH"),
				*Route.RouteId.ToString());
			return false;
		}
		if (Route.MarkLevel < 1)
		{
			OutReason = FString::Printf(
				TEXT("SNAPSHOT BELT %s HAS AN INVALID MARK"),
				*Route.RouteId.ToString());
			return false;
		}
		FString Suffix = Route.RouteId.ToString();
		int32 DashIndex;
		if (Suffix.FindLastChar(TEXT('-'), DashIndex))
		{
			HighestSequence = FMath::Max(HighestSequence,
				FCString::Atoi(*Suffix.Mid(DashIndex + 1)));
		}
	}
	if (Snapshot.NextRouteSequence <= HighestSequence)
	{
		OutReason = TEXT("SNAPSHOT BELT SEQUENCE WOULD REUSE IDS");
		return false;
	}
	OutReason = TEXT("SNAPSHOT VALID");
	return true;
}

bool ALBSpacecraftTransportAuthority::RestoreSnapshot(
	const FLBSpacecraftTransportSnapshot& Snapshot, FString& OutReason)
{
	// Validate the ENTIRE snapshot before a single mutation.
	if (!ValidateSnapshot(Snapshot, OutReason))
	{
		return false;
	}
	Routes = Snapshot.Routes;
	NextRouteSequence = Snapshot.NextRouteSequence;
	OutReason = TEXT("TRANSPORT RESTORED");
	return true;
}
