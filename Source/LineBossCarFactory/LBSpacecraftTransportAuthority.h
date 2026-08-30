// Spacecraft-era conveyor transport authority (v002 of the owner's
// "belts auto connect" directive, design per
// Docs/CONVEYORS_SCALE_PLAYABILITY_RESEARCH_v001.md): the single owner
// of belt routes. A belt joins one station to one store with a
// deterministic grid path; a belted station crafts FASTER, an unbelted
// one falls back to drone ferrying - degradation is slower, never
// broken. Fail-closed everywhere; snapshot validates whole-or-nothing.

#pragma once

#include "CoreMinimal.h"
#include "GameFramework/Actor.h"
#include "LBSpacecraftTransportAuthority.generated.h"

class ALBSpacecraftBuildAuthority;
class ALBSpacecraftInventoryAuthority;
class ALBSpacecraftProductionAuthority;

USTRUCT()
struct LINEBOSSCARFACTORY_API FLBSpacecraftBeltRoute
{
	GENERATED_BODY()

	UPROPERTY(SaveGame)
	FName RouteId;

	UPROPERTY(SaveGame)
	FName StationId;

	UPROPERTY(SaveGame)
	FName StoreId;

	/** Grid waypoints, floor space, cm. At least two points. */
	UPROPERTY(SaveGame)
	TArray<FVector> PathPointsCm;

	/** Belt mark: 1 = base. Mk2 arrives with research content. */
	UPROPERTY(SaveGame)
	int32 MarkLevel = 1;
};

USTRUCT()
struct LINEBOSSCARFACTORY_API FLBSpacecraftTransportSnapshot
{
	GENERATED_BODY()

	UPROPERTY(SaveGame)
	TArray<FLBSpacecraftBeltRoute> Routes;

	UPROPERTY(SaveGame)
	int32 NextRouteSequence = 1;
};

UCLASS()
class LINEBOSSCARFACTORY_API ALBSpacecraftTransportAuthority : public AActor
{
	GENERATED_BODY()

public:
	ALBSpacecraftTransportAuthority();

	/** PROVISIONAL: 200 cr per metre (Production Line calibration:
	 *  routing has a real price - a 30 m run costs ~7% of a station). */
	UPROPERTY(EditAnywhere, Category = "LineBoss")
	int64 BeltCostPerMetrePence = 20000;

	/** PROVISIONAL: a belted station crafts this much faster. */
	UPROPERTY(EditAnywhere, Category = "LineBoss")
	float BeltedSpeedMultiplier = 1.4f;

	/** Removal refunds this percentage of the build cost. */
	UPROPERTY(EditAnywhere, Category = "LineBoss")
	int32 RemovalRefundPercent = 50;

	/** Connect a supply belt from a station to a store. Validates
	 *  everything BEFORE charging (station exists, store exists, not
	 *  already belted); the ledger charge is the last step. The path
	 *  is a deterministic two-leg route on the 100 cm grid. */
	bool ConnectSupplyBelt(const ALBSpacecraftBuildAuthority& InBuild,
		const ALBSpacecraftInventoryAuthority& InInventory,
		ALBSpacecraftProductionAuthority* InLedger, FName StationId,
		FName StoreId, FName& OutRouteId, FString& OutReason,
		const class ALBSpacecraftProgressionAuthority* InProgression
			= nullptr);

	/** Remove a belt; refunds RemovalRefundPercent of its build cost. */
	bool DisconnectBelt(ALBSpacecraftProductionAuthority* InLedger,
		FName RouteId, FString& OutReason);

	/** 1.0 for an unbelted station (drones ferry - slower, never
	 *  broken); BeltedSpeedMultiplier when a supply belt is connected. */
	float GetStationSpeedMultiplier(FName StationId) const;

	const TArray<FLBSpacecraftBeltRoute>& GetRoutes() const
	{
		return Routes;
	}

	const FLBSpacecraftBeltRoute* FindRouteForStation(
		FName StationId) const;

	/** Belt build cost for a path, from its metre length. */
	int64 ComputeBeltCostPence(const TArray<FVector>& PathPointsCm) const;

	/** Pure: deterministic two-leg grid path (corner at end X / start
	 *  Y), 100 cm snapped, at least two points. */
	static TArray<FVector> ComputeBeltPathCm(const FVector& StartCm,
		const FVector& EndCm);

	/** Stations that vanish take their belts with them (no refund -
	 *  the station removal already refunded the player). */
	void SyncFromBuild(const ALBSpacecraftBuildAuthority* InBuild);

	FLBSpacecraftTransportSnapshot CaptureSnapshot() const;
	bool ValidateSnapshot(const FLBSpacecraftTransportSnapshot& Snapshot,
		FString& OutReason) const;
	bool RestoreSnapshot(const FLBSpacecraftTransportSnapshot& Snapshot,
		FString& OutReason);

private:
	UPROPERTY(SaveGame)
	TArray<FLBSpacecraftBeltRoute> Routes;

	UPROPERTY(SaveGame)
	int32 NextRouteSequence = 1;
};
