// Spacecraft-era runtime coordinator: drives units through the route the
// PLAYER built, on the recipe's cycle times, against the production ledger.
//
// House rules carried forward:
//  * refuses to run until the factory is commissioned and a route derives
//    from actual placement (the premade-factory principle, domain-neutral);
//  * one unit per physical station - a blocked unit HOLDS visibly instead of
//    teleporting or stacking;
//  * the Testing stage is the hover test: the coordinator can run it
//    automatically for the slice, or hold the craft for a manual result;
//  * runtime state is captured/validated/restored as a whole, cross-checked
//    against both the ledger and the route topology.

#pragma once

#include "CoreMinimal.h"
#include "GameFramework/Actor.h"
#include "LBSpacecraftBuildAuthority.h"
#include "LBSpacecraftProductionAuthority.h"
#include "LBSpacecraftRuntimeCoordinator.generated.h"

/** THE PULSE LINE (owner 2026-08-28: military-aircraft pulse
 *  mechanics; 2026-09-02: "can you do the pulse line"). The line is
 *  either STOPPED - every craft sits at its station and the stops run -
 *  or MOVING - the cranes carry every finished craft one station
 *  forward together. A station whose stop is over HOLDS its craft
 *  until the whole line is ready; the slowest station sets the pace. */
UENUM(BlueprintType)
enum class ELBSpacecraftLinePhase : uint8
{
	Stopped = 0,
	Moving
};

USTRUCT(BlueprintType)
struct LINEBOSSCARFACTORY_API FLBSpacecraftRuntimeAssignment
{
	GENERATED_BODY()

	UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category = "LineBoss", SaveGame)
	FName UnitId;

	UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category = "LineBoss", SaveGame)
	int32 RouteIndex = 0;

	UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category = "LineBoss", SaveGame)
	FName StationId;

	UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category = "LineBoss", SaveGame)
	float CycleElapsedSeconds = 0.f;

	/** Allocated components for THIS stage step already consumed (a
	 *  held unit must not pay twice when the hold clears). */
	UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category = "LineBoss", SaveGame)
	bool bStageComponentsConsumed = false;

	/** Workmanship for THIS stage step already judged (a held unit
	 *  must not collect the same station's defects twice). */
	UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category = "LineBoss", SaveGame)
	bool bStageDefectsAccrued = false;

	/** The station's stop is over and it is HOLDING the craft for the
	 *  pulse. Cleared when the craft moves (or its stop restarts). */
	UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category = "LineBoss", SaveGame)
	bool bStopComplete = false;

	/** THE CREW THAT ACTUALLY DID THE WORK (2026-09-03 audit): captured
	 *  the instant bStopComplete is set, not read live whenever the
	 *  defect calculation happens to run. For a non-final station that
	 *  run can be tens of seconds to minutes later - the whole line
	 *  waits for its slowest station before the pulse - and until this
	 *  snapshot existed, a player could dismiss a station's crew the
	 *  moment it finished (rational: they're idle, reassign them) and
	 *  have the craft charged defects for work a full crew actually
	 *  did, or install crew just ahead of the pulse to buy a "clean"
	 *  read for work done uncrewed. */
	UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category = "LineBoss", SaveGame)
	int32 SnapshotInstalledDrones = 0;

	UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category = "LineBoss", SaveGame)
	TArray<FName> SnapshotInstalledDroneTypes;
};

USTRUCT(BlueprintType)
struct LINEBOSSCARFACTORY_API FLBSpacecraftRuntimeState
{
	GENERATED_BODY()

	UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category = "LineBoss", SaveGame)
	TArray<FLBSpacecraftRuntimeAssignment> Assignments;

	/** CRC of the route this state was captured against; a restore against a
	 *  different route fails closed. (uint32 is not Blueprint-exposable.) */
	UPROPERTY(VisibleAnywhere, Category = "LineBoss", SaveGame)
	uint32 RouteTopologyHash = 0;

	/** Stopped (stops running, finished stations holding) or Moving
	 *  (the cranes are carrying every finished craft forward). */
	UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category = "LineBoss", SaveGame)
	ELBSpacecraftLinePhase Phase = ELBSpacecraftLinePhase::Stopped;

	/** Seconds into the move phase. */
	UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category = "LineBoss", SaveGame)
	float PhaseElapsedSeconds = 0.f;

	/** Pulses completed since the line was configured (HUD, tests). */
	UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category = "LineBoss", SaveGame)
	int32 PulseCount = 0;
};

UCLASS()
class LINEBOSSCARFACTORY_API ALBSpacecraftRuntimeCoordinator : public AActor
{
	GENERATED_BODY()

public:
	ALBSpacecraftRuntimeCoordinator();

	/** Automatically create units at the head of the line while demand and
	 *  the WIP cap allow it. */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "LineBoss")
	bool bAutoStartUnits = true;

	/** One crane trip: lift, travel one station, set down. The move
	 *  phase lasts ceil(craft to move / cranes) trips, so one crane on
	 *  a four-craft line takes four times as long per pulse as a crane
	 *  per gap - the upgrade axis the owner named (2026-08-29). */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "LineBoss")
	float CraneTripSeconds = 6.f;

	/** Why the head of the line last declined to start a craft.
	 *
	 *  The refusal used to be captured into a local and dropped, with a
	 *  comment calling refusals "normal idle states". That is true of
	 *  "no demand" and "head occupied" and NOT true of "the route
	 *  cannot service this recipe", which is a fault wearing an idle
	 *  state's clothes - and it is why a line with a commissioned
	 *  factory and an accepted contract can sit for thirty sim-minutes
	 *  building nothing while every status line reads healthy. */
	FString LastStartRefusal;

	/** What the line last said when it declined to start a craft.
	 *  Empty when a craft started or nothing has been attempted. */
	const FString& GetLastStartRefusal() const
	{
		return LastStartRefusal;
	}

	/** Automatically record a PASS when the hover test's cycle completes.
	 *  Turn off to hold craft at Testing for a manual/scripted result. */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "LineBoss")
	bool bAutoRunHoverTest = true;

	/** Bind to the two authorities. Refuses when either is missing, the
	 *  factory is not commissioned, or no route derives from placement. */
	bool ConfigureFromAuthorities(ALBSpacecraftBuildAuthority* InBuildAuthority,
		ALBSpacecraftProductionAuthority* InProductionAuthority,
		FString& OutReason,
		class ALBSpacecraftTrackAuthority* InTrack = nullptr);

	bool IsConfigured() const { return Route.Num() > 0; }

	/** Load-path reset (review fix): loading an UNCOMMISSIONED save over
	 *  a running session must not leave a stale route and assignments
	 *  pointing at the pre-load world. */
	void ResetConfiguration();

	/** One production step: advances the sim clock, moves every unit that
	 *  has finished its cycle and has a free station ahead, runs/holds the
	 *  hover test, dispatches, and (optionally) starts new units. */
	bool TickProduction(double DeltaSeconds, FString& OutReason);

	/** WHY THE LINE IS NOT MOVING. Every hold reason the last tick
	 *  produced was computed and thrown away, so a line that stopped
	 *  stopped in silence - the single worst failure mode in a factory
	 *  game. Empty when nothing is held. */
	const FString& GetLastHoldReason() const { return LastHoldReason; }

	/** Manually start one unit at the head of the line. */
	bool TryStartUnit(FName& OutUnitId, FString& OutReason);

	// ---- read access for UI/presentation ----
	const TArray<FLBSpacecraftRouteStep>& GetRoute() const { return Route; }
	const TArray<FLBSpacecraftRuntimeAssignment>& GetAssignments() const
	{
		return Runtime.Assignments;
	}
	/** 0..1 progress through the unit's current cycle; false if unknown. */
	bool GetUnitCycleProgress(FName UnitId, float& OutProgress01) const;

	// ---- the pulse ----
	ELBSpacecraftLinePhase GetLinePhase() const { return Runtime.Phase; }
	int32 GetPulseCount() const { return Runtime.PulseCount; }
	/** Cranes serving the line (from the build authority; at least 1). */
	int32 GetCraneCount() const;
	/** Length of the current/next move phase in seconds. */
	float GetMoveSeconds() const;
	/** 0..1 through the move phase; 0 while stopped. */
	float GetPulseProgress01() const;
	/** True when the station's stop is over and it holds the craft. */
	bool IsUnitStopComplete(FName UnitId) const;
	/** The unit's crane trip within the move phase as a 0..1 window of
	 *  the phase (tail-first order, `cranes` craft per trip). False when
	 *  the unit is not on the line or the line is not moving. */
	bool GetUnitCarryWindow(FName UnitId, float& OutStart01,
		float& OutEnd01) const;
	/** Craft on the line whose stop is complete. */
	int32 CountStopComplete() const;

	/** THE INSPECTION SWEEP. The craft currently under the scan at the
	 *  end of the line, how far the sweep has run, and how many faults
	 *  it has turned up so far. False when nothing is being inspected.
	 *  This is what the drones fly to and what a scan visual follows;
	 *  it invents nothing, it reads the stage the unit is really in. */
	bool GetInspectionSweep(FName& OutUnitId, FName& OutStationId,
		float& OutProgress01, int32& OutDefectsFound) const;

	/** Allocation-driven consumption (owner 2026-08-26, the Car
	 *  Manufacture work-scope model): with an inventory bound, a unit
	 *  leaving a station consumes ONE of each component ALLOCATED
	 *  there from the floor store - all-or-nothing, a shortage holds
	 *  the unit with the missing part named. Stations with an empty
	 *  allocation consume nothing (fail-open default: the loop runs
	 *  before the player allocates anything). */
	void BindInventory(class ALBSpacecraftInventoryAuthority* InInventory)
	{
		InventoryAuthority = InInventory;
	}
	uint32 GetRouteTopologyHash() const { return Runtime.RouteTopologyHash; }

	// ---- save/restore ----
	FLBSpacecraftRuntimeState CaptureRuntime() const { return Runtime; }
	bool ValidateRuntime(const FLBSpacecraftRuntimeState& State,
		FString& OutReason) const;
	bool RestoreRuntime(const FLBSpacecraftRuntimeState& State,
		FString& OutReason);

	static uint32 ComputeRouteTopologyHash(
		const TArray<FLBSpacecraftRouteStep>& InRoute);

private:
	/** Explains WHY a station cannot get an item, naming the building
	 *  that is missing rather than only the item.
	 *
	 *  A player who has ordered goods, watched them land at their own
	 *  delivery dock, and is then told the station "needs 1x
	 *  Component.Hull" has no way to deduce that haulers are based at a
	 *  storage rack and there is no rack. This says so.
	 *
	 *  Declared clear of the UPROPERTY block below on purpose: a
	 *  function slipped between UPROPERTY() and the field it decorates
	 *  makes UnrealHeaderTool report "Found '(' when expecting ';'",
	 *  which names the class and not the real mistake. */
	FString DescribeSupplyShortfall(FName StationId, FName ItemId) const;

	UPROPERTY()
	TObjectPtr<ALBSpacecraftBuildAuthority> BuildAuthority;

	UPROPERTY()
	TObjectPtr<class ALBSpacecraftInventoryAuthority> InventoryAuthority;

	UPROPERTY()
	TObjectPtr<ALBSpacecraftProductionAuthority> ProductionAuthority;

	UPROPERTY(VisibleAnywhere, Category = "LineBoss")
	/** The most recent reason a unit could not move (see above). */
	FString LastHoldReason;

	TArray<FLBSpacecraftRouteStep> Route;

	UPROPERTY(VisibleAnywhere, Category = "LineBoss")
	FLBSpacecraftRuntimeState Runtime;

	FLBSpacecraftRuntimeAssignment* FindAssignment(FName UnitId);
	const FLBSpacecraftRuntimeAssignment* FindAssignment(FName UnitId) const;
	bool StationOccupiedByOther(FName StationId, FName IgnoreUnitId) const;
	/** Finished and with a station ahead: moves on the next pulse. */
	bool IsPulseMover(const FLBSpacecraftRuntimeAssignment& Assignment) const;
	/** The last pulse's verdict, kept until the next pulse (see
	 *  TickProduction). Not saved: a load starts with a clean slate. */
	FString LastPulseHold;

	/** Advance one unit one route step if its cycle is complete and the move
	 *  is legal; returns true when the unit moved (or dispatched). */
	bool TryAdvanceAssignment(FLBSpacecraftRuntimeAssignment& Assignment,
		FString& OutHoldReason);
};
