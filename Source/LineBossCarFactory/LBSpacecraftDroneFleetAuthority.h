// Spacecraft-era drone fleet authority (owner, 2026-08-25): the fitting
// drones are REAL power consumers, not decoration. Each crafting station
// owns two drones; a drone flies only while its station works AND it has
// battery; flight drains the battery; at reserve it returns to its dock;
// charging on the dock registers a genuine load on the power grid - and a
// grid without headroom simply does not charge it (honest stall, named by
// the state, never a fake recharge).
//
// The presenter MIRRORS this authority; it never invents drone state.

#pragma once

#include "CoreMinimal.h"
#include "GameFramework/Actor.h"
#include "LBSpacecraftBuildAuthority.h"
#include "LBSpacecraftInventoryAuthority.h"
#include "LBSpacecraftDroneFleetAuthority.generated.h"

class ALBSpacecraftCraftingAuthority;
class ALBSpacecraftPowerAuthority;

/** A drone's autonomous mission phase (owner 2026-08-25: drones are
 *  autonomous workers, not station puppets). The cycle is
 *  Docked -> ToSupply -> Pickup -> ToStation -> Fitting -> ToDock,
 *  battery-gated at every step. */
UENUM(BlueprintType)
enum class ELBSpacecraftDroneMission : uint8
{
	Docked = 0,
	ToSupply,
	Pickup,
	ToStation,
	Fitting,
	/** Flying the INSPECTION SWEEP over a finished craft at the end of
	 *  the line (owner 2026-08-27). The Testing stage is 60 s of
	 *  "engine test and inspection" that showed nothing at all; the
	 *  crew now flies it, and the faults the sweep turns up are the
	 *  ones the hover test is about to judge. Appended, so saved
	 *  missions keep their meaning. */
	Inspecting,
	ToDock
};

/** One drone's persistent state. */
USTRUCT(BlueprintType)
struct LINEBOSSCARFACTORY_API FLBSpacecraftDroneState
{
	GENERATED_BODY()

	UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category = "LineBoss")
	FName StationId;

	UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category = "LineBoss")
	int32 DroneIndex = 0;

	/** 0..1 battery state of charge. */
	UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category = "LineBoss")
	float Charge01 = 1.f;

	UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category = "LineBoss")
	bool bFlying = false;

	UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category = "LineBoss")
	ELBSpacecraftDroneMission Mission = ELBSpacecraftDroneMission::Docked;

	/** Seconds inside the current mission phase. */
	UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category = "LineBoss")
	float MissionSeconds = 0.f;
};

/** The heavy hauler's run phase (owner 2026-08-26: sub-assembly
 *  buffers are emptied by the heavy transport drone, machine ->
 *  part storage). Hauls are DERIVED state: never saved; a restore
 *  resets haulers to Idle and the buffers keep every item. */
UENUM(BlueprintType)
enum class ELBSpacecraftHaulPhase : uint8
{
	Idle = 0,
	ToMachine,
	ToStore,
	/** Flying EMPTY from home to the store the goods are drawn from,
	 *  when that store is not the hauler's own (a dock, another rack).
	 *  Added 2026-09-02 with the transporter pass: a delivery used to
	 *  be two legs named for the collect job, and read backwards. */
	ToSource
};

/** What a hauler is doing this run (owner 2026-08-27, the Production
 *  Line model). Collecting empties a machine's output buffer into the
 *  rack; delivering carries feedstock from the rack to the stockpile
 *  beside a station that is about to run dry. Delivering is what makes
 *  the drones matter: a station can only eat what has been brought to
 *  it. */
UENUM(BlueprintType)
enum class ELBSpacecraftHaulJob : uint8
{
	CollectOutput = 0,
	DeliverInput
};

/** One heavy hauler (one per storage rack, and one per delivery dock -
 *  a dock's hauler only feeds the line). */
USTRUCT(BlueprintType)
struct LINEBOSSCARFACTORY_API FLBSpacecraftHaulState
{
	GENERATED_BODY()

	UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category = "LineBoss")
	FName RackStationId;

	UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category = "LineBoss")
	FName MachineStationId;

	UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category = "LineBoss")
	ELBSpacecraftHaulPhase Phase = ELBSpacecraftHaulPhase::Idle;

	UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category = "LineBoss")
	float PhaseSeconds = 0.f;

	/** Items shown on the hook (display; the transfer is atomic at
	 *  the store so a mid-flight save loses nothing). */
	UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category = "LineBoss")
	int32 CarryCount = 0;

	UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category = "LineBoss")
	ELBSpacecraftHaulJob Job = ELBSpacecraftHaulJob::CollectOutput;

	/** DeliverInput: the feedstock being carried to the station. */
	UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category = "LineBoss")
	FName CarryItemId;

	/** DeliverInput: which store the load was drawn from - the
	 *  hauler's own rack, or the site overflow yard when the rack was
	 *  short. */
	UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category = "LineBoss")
	FName SourceStoreId;

	/** The station whose store SourceStoreId is, so the presenter can
	 *  fly the pickup leg somewhere real; None for the site yard. */
	UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category = "LineBoss")
	FName SourceStationId;

	/** THE HAULERS CHARGE TOO (owner 2026-09-02: "ours will go to their
	 *  dock and charge"). Same battery as the crews: flight drains it,
	 *  the pad at home refills it, and a hauler under reserve sits out
	 *  until it is fit to fly. Never abandons a run mid-air - a trip is
	 *  short against the battery and cargo must not strand. */
	UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category = "LineBoss")
	float Charge01 = 1.f;

	/** On the pad topping up (true from the reserve until LaunchFraction). */
	UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category = "LineBoss")
	bool bCharging = false;
};

/** Whole-fleet snapshot for the save pipeline. */
USTRUCT(BlueprintType)
struct LINEBOSSCARFACTORY_API FLBSpacecraftDroneFleetSnapshot
{
	GENERATED_BODY()

	UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category = "LineBoss")
	TArray<FLBSpacecraftDroneState> Drones;
};

UCLASS()
class LINEBOSSCARFACTORY_API ALBSpacecraftDroneFleetAuthority : public AActor
{
	GENERATED_BODY()

public:
	ALBSpacecraftDroneFleetAuthority();

	/** Battery empties after this many seconds of flight. */
	UPROPERTY(EditAnywhere, Category = "LineBoss")
	float FlightSecondsPerCharge = 180.f;

	/** A full charge from empty takes this long on the dock. */
	UPROPERTY(EditAnywhere, Category = "LineBoss")
	float ChargeSecondsPerCharge = 60.f;

	/** Below this fraction a flying drone returns to its dock. */
	UPROPERTY(EditAnywhere, Category = "LineBoss")
	float ReserveFraction = 0.15f;

	/** A docked drone relaunches only at or above this fraction. */
	UPROPERTY(EditAnywhere, Category = "LineBoss")
	float LaunchFraction = 0.9f;

	/** Grid draw of ONE charging dock, integer kilowatts. */
	UPROPERTY(EditAnywhere, Category = "LineBoss")
	int32 DockChargeKw = 25;

	/** Mirrors the placed crafting stations: two drones per crafting
	 *  family station; drones of removed stations disappear (their
	 *  charging loads are disconnected first). */
	/** One rule for WHERE fitting drones live, shared by the battery
	 *  sim and the presenter so they can never disagree. Owner decision
	 *  2026-08-25: EVERY station is staffed ("it needs the lot"). */
	static bool StationHostsFittingDrones(
		const struct FLBSpacecraftStationDefinition& Definition);

	void SyncFromBuild(const ALBSpacecraftBuildAuthority* InBuild,
		ALBSpacecraftPowerAuthority* InPower);

	/** Advances the fleet on SIM time: flight drains, reserve recalls,
	 *  docking charges - and charging draws real grid power through
	 *  InPower, refusing (no charge gained) when the grid has no
	 *  headroom. */
	void TickFleet(double DeltaSeconds,
		const ALBSpacecraftCraftingAuthority* InCrafting,
		ALBSpacecraftPowerAuthority* InPower,
		const class ALBSpacecraftRuntimeCoordinator* InCoordinator
			= nullptr);

	/** Advances the heavy haulers: an idle hauler flies to the fullest
	 *  sub-assembly buffer, then to the store, where the transfer is
	 *  ATOMIC (buffer -> store in one call; a full store keeps the
	 *  remainder buffered and the machine stalled - honest, named). */
	/** How many units a station's stockpile is topped up to before a
	 *  hauler looks elsewhere (PROVISIONAL). Small on purpose - this
	 *  is a stockpile beside a machine, and keeping it fed is the job
	 *  the drones exist to do. */
	UPROPERTY(EditAnywhere, Category = "LineBoss")
	int32 StockpileTopUpUnits = 4;

	/** The shipped top-up target, for callers that size a stockpile
	 *  before any fleet exists. */
	static constexpr int32 DefaultStockpileTopUpUnits() { return 4; }

	/** Pure: does this station want more of this item right now? */
	static bool StockpileWantsItem(int32 OnHand, int32 TopUpTarget);

	void TickHauls(double DeltaSeconds,
		class ALBSpacecraftCraftingAuthority* InCrafting,
		class ALBSpacecraftInventoryAuthority* InInventory,
		const class ALBSpacecraftBuildAuthority* InBuild = nullptr,
		ALBSpacecraftPowerAuthority* InPower = nullptr);
	/** Pure: how many of an item one haul run carries. An assembled
	 *  component goes ONE per trip - that is what a ship-sized part
	 *  means and what the owner wants to see in the claw (2026-09-02);
	 *  raw stock, processed stock and sub-parts ride in crates of up to
	 *  Capacity. */
	static int32 HaulLoadFor(ELBSpacecraftItemCategory Category,
		int32 Capacity);
	/** Pure, shared with the presenter so the picture cannot disagree
	 *  with the ledger: is the hook loaded in this phase of this job?
	 *  A delivery carries OUT (ToMachine) and returns empty; a
	 *  collection flies out empty and carries HOME (ToStore). */
	static bool HaulIsLoaded(const FLBSpacecraftHaulState& Haul);

	UPROPERTY(EditAnywhere, Category = "LineBoss")
	float HaulTravelSeconds = 4.f;

	/** Items one haul run can carry (PROVISIONAL pacing). */
	UPROPERTY(EditAnywhere, Category = "LineBoss")
	int32 HaulCapacity = 4;

	const TArray<FLBSpacecraftHaulState>& GetHauls() const
	{
		return Hauls;
	}

	/** Seconds a drone spends in each travelling/working phase
	 *  (PROVISIONAL pacing). Fitting runs while the station crafts. */
	UPROPERTY(EditAnywhere, Category = "LineBoss")
	float TravelSeconds = 3.f;

	UPROPERTY(EditAnywhere, Category = "LineBoss")
	float PickupSeconds = 1.2f;

	UPROPERTY(EditAnywhere, Category = "LineBoss")
	float FittingBurstSeconds = 6.f;

	/** Phase progress 0..1 for the drone's current mission leg. */
	static float GetMissionAlpha01(const FLBSpacecraftDroneState& Drone,
		float InTravelSeconds, float InPickupSeconds,
		float InFittingBurstSeconds);

	int32 GetDroneCount() const { return Drones.Num(); }
	const FLBSpacecraftDroneState* FindDrone(FName StationId,
		int32 DroneIndex) const;
	int32 GetFlyingCount() const;
	int32 GetChargingCount() const { return ConnectedChargeLoads.Num(); }

	FLBSpacecraftDroneFleetSnapshot CaptureSnapshot() const;
	bool RestoreSnapshot(const FLBSpacecraftDroneFleetSnapshot& Snapshot,
		ALBSpacecraftPowerAuthority* InPower, FString& OutReason);
	static bool ValidateSnapshot(
		const FLBSpacecraftDroneFleetSnapshot& Snapshot, FString& OutReason);

private:
	UPROPERTY(VisibleAnywhere, Category = "LineBoss")
	TArray<FLBSpacecraftDroneState> Drones;

	/** Heavy haulers, one per storage rack; derived state, unsaved. */
	UPROPERTY(VisibleAnywhere, Category = "LineBoss")
	TArray<FLBSpacecraftHaulState> Hauls;

	/** Charge-load ids currently connected to the grid (ours only). */
	TSet<FName> ConnectedChargeLoads;

	static FName MakeChargeLoadId(FName StationId, int32 DroneIndex);
	void DisconnectChargeLoad(FName StationId, int32 DroneIndex,
		ALBSpacecraftPowerAuthority* InPower);
};
