#include "LBSpacecraftRuntimeCoordinator.h"

#include "LBSpacecraftTrackAuthority.h"
#include "LBSpacecraftDifficulty.h"
#include "LBSpacecraftInventoryAuthority.h"
#include "LBSpacecraftGameMode.h"

namespace LBSpacecraftRuntimeCoordinatorPrivate
{
	// Unity-build safety: helpers qualified by subject.
	float SpacecraftCycleSecondsFor(const FLBSpacecraftRecipe& Recipe,
		ELBSpacecraftStage Stage)
	{
		const float* Found = Recipe.NominalCycleSeconds.Find(Stage);
		return Found != nullptr ? *Found : -1.f;
	}

	// Line work is paced PER STATION now, not per stage: a craft's stop
	// at station i of N takes that station's share of the recipe's total
	// line seconds, weighted by the parts allocated there. Testing (and
	// anything past the line) still runs on its own stage clock.
	float SpacecraftAssignmentCycleSeconds(
		const FLBSpacecraftRecipe& Recipe, ELBSpacecraftStage Stage,
		int32 RouteIndex, int32 RouteCount,
		const ALBSpacecraftBuildAuthority* Build,
		const TArray<FLBSpacecraftRouteStep>& Route)
	{
		if (Stage >= ELBSpacecraftStage::Testing || RouteCount <= 0)
		{
			return SpacecraftCycleSecondsFor(Recipe, Stage);
		}
		// A PROCESS STATION TAKES ITS OWN TIME. Masking, two coats and
		// a flash-off take what they take, however many parts the craft
		// happens to carry - so a booth is never given a slice of the
		// recipe's fitting work.
		if (Build != nullptr && Route.IsValidIndex(RouteIndex))
		{
			const FLBSpacecraftStationRecord* Here =
				Build->FindStation(Route[RouteIndex].StationId);
			const FLBSpacecraftStationDefinition* Definition =
				Here != nullptr
					? ALBSpacecraftBuildAuthority::FindDefinition(
						Here->DefinitionId)
					: nullptr;
			if (Definition != nullptr && Definition->bProcessStation)
			{
				return FMath::Max(Definition->ProcessSeconds, 0.f);
			}
		}
		int32 Allocated = 0;
		int32 TotalAllocated = 0;
		int32 FittingStations = 0;
		if (Build != nullptr)
		{
			for (int32 Index = 0; Index < Route.Num(); ++Index)
			{
				const FLBSpacecraftStationRecord* Record =
					Build->FindStation(Route[Index].StationId);
				const FLBSpacecraftStationDefinition* Definition =
					Record != nullptr
						? ALBSpacecraftBuildAuthority::FindDefinition(
							Record->DefinitionId)
						: nullptr;
				if (Definition != nullptr && Definition->bProcessStation)
				{
					continue; // the booth is not part of the fitting share
				}
				++FittingStations;
				const int32 Count = Record != nullptr
					? Record->AllocatedComponents.Num() : 0;
				TotalAllocated += Count;
				if (Index == RouteIndex)
				{
					Allocated = Count;
				}
			}
		}
		// The denominator counts FITTING stations only, so adding a
		// booth does not silently make every fitting stop shorter and
		// hand the player free throughput.
		RouteCount = FMath::Max(FittingStations, 1);
		return FLBSpacecraftProductionCatalog::StationFitSeconds(
			Recipe, Allocated, TotalAllocated, RouteCount);
	}
}

ALBSpacecraftRuntimeCoordinator::ALBSpacecraftRuntimeCoordinator()
{
	PrimaryActorTick.bCanEverTick = false;
}

uint32 ALBSpacecraftRuntimeCoordinator::ComputeRouteTopologyHash(
	const TArray<FLBSpacecraftRouteStep>& InRoute)
{
	FString Blob;
	for (const FLBSpacecraftRouteStep& Step : InRoute)
	{
		Blob += FString::Printf(TEXT("%d:%s;"),
			static_cast<int32>(Step.Stage), *Step.StationId.ToString());
	}
	return FCrc::StrCrc32(*Blob);
}

FString ALBSpacecraftRuntimeCoordinator::DescribeSupplyShortfall(
	FName StationId, FName ItemId) const
{
	(void)StationId;
	// A diagnosis, never a gate. Missing authorities mean no diagnosis
	// and the bare refusal stands - the line must not behave
	// differently because an explanation could not be produced.
	if (InventoryAuthority == nullptr || BuildAuthority == nullptr)
	{
		return FString();
	}
	static const FName DockDefinition(TEXT("DeliveryDock"));
	static const FName RackDefinition(TEXT("StorageRack"));

	bool bHasDock = false;
	bool bHasRack = false;
	FName HoldingStore;
	FName HoldingStation;
	int32 HoldingCount = 0;
	for (const FLBSpacecraftStationRecord& Record :
		BuildAuthority->GetStations())
	{
		bHasDock |= Record.DefinitionId == DockDefinition;
		bHasRack |= Record.DefinitionId == RackDefinition;
		const FName Store(*FString::Printf(TEXT("Store.%s"),
			*Record.StationId.ToString()));
		const int32 Held = InventoryAuthority->GetQuantity(Store, ItemId);
		if (Held > HoldingCount)
		{
			HoldingCount = Held;
			HoldingStore = Store;
			HoldingStation = Record.StationId;
		}
	}
	const int32 OnTheFloor = InventoryAuthority->GetQuantity(
		ALBSpacecraftGameMode::SiteOverflowStoreId(), ItemId);

	// NOTHING ANYWHERE: the answer is to buy some, and possibly to build
	// the thing that goods can be delivered to at all.
	if (HoldingCount <= 0 && OnTheFloor <= 0)
	{
		return bHasDock
			? FString(TEXT(" - none in the factory; order more at the "
				"delivery dock"))
			: FString(TEXT(" - none in the factory, and no delivery dock "
				"to order them to; build one"));
	}

	// THERE ARE SOME, and they are not moving. This is the case that
	// looked like a broken game: goods the player paid for, sitting in a
	// building the player built, while the factory reports none. Drone
	// haulers work out of a STORAGE RACK, so without a rack nothing is
	// ever collected.
	const FString Where = HoldingCount > 0
		? FString::Printf(TEXT("%d waiting at %s"), HoldingCount,
			*HoldingStation.ToString())
		: FString::Printf(TEXT("%d on the floor"), OnTheFloor);
	// A delivery dock hosts a hauler of its own now (the stranger
	// playthrough, 2026-09-02: five bought components sat at the dock
	// of a rack-less first factory while the line reported "none in
	// the factory"), so only a factory with NEITHER has nothing to
	// carry the goods.
	if (!bHasRack && !bHasDock)
	{
		return FString::Printf(
			TEXT(" - %s, but nothing can carry them; build a delivery "
				"dock or a storage rack, whose drone collects parts"),
			*Where);
	}
	return FString::Printf(TEXT(" - %s, a drone is on its way"), *Where);
}

bool ALBSpacecraftRuntimeCoordinator::ConfigureFromAuthorities(
	ALBSpacecraftBuildAuthority* InBuildAuthority,
	ALBSpacecraftProductionAuthority* InProductionAuthority,
	FString& OutReason, ALBSpacecraftTrackAuthority* InTrack)
{
	if (InBuildAuthority == nullptr || InProductionAuthority == nullptr)
	{
		OutReason = TEXT("Coordinator needs both authorities");
		return false;
	}
	TArray<FLBSpacecraftRouteStep> DerivedRoute;
	if (!InBuildAuthority->BuildRoute(DerivedRoute, OutReason))
	{
		return false; // carries the commissioning/route reason verbatim
	}
	// A LAID TRACK routes the line in TRACK ORDER (owner 2026-08-26,
	// the Car Manufacture node model). With ONE repeated station type
	// there is no such thing as stations in the WRONG order - any
	// arrangement of identical stations is a working line - so the
	// track's whole job here is to say which order the craft visits
	// them in. No track laid = the derived line-order route stands.
	if (InTrack != nullptr && InTrack->GetPieces().Num() > 0)
	{
		if (!InTrack->IsComplete())
		{
			OutReason = InTrack->DescribeProblem();
			return false;
		}
		const TArray<FName> Nodes = InTrack->GetNodeStationsInOrder();
		if (Nodes.Num() != DerivedRoute.Num())
		{
			// NAME THE STATION, SAY WHAT TO DO. "Attach every line
			// station to the track" told the stranger (2026-09-02) to
			// do something the game no longer lets anyone do - the
			// track connects itself. What it cannot do is reach a
			// station; that station is what the player has to move.
			FString Missing;
			for (const FLBSpacecraftRouteStep& Step : DerivedRoute)
			{
				if (!Nodes.Contains(Step.StationId))
				{
					Missing += (Missing.IsEmpty() ? TEXT("") : TEXT(", "))
						+ Step.StationId.ToString();
				}
			}
			OutReason = FString::Printf(
				TEXT("The track cannot reach %s - move it clear of its ")
				TEXT("neighbours, then commission again (%d stations, ")
				TEXT("%d track nodes)"),
				Missing.IsEmpty() ? TEXT("a station") : *Missing,
				DerivedRoute.Num(), Nodes.Num());
			return false;
		}
		TArray<FLBSpacecraftRouteStep> TrackRoute;
		for (int32 Index = 0; Index < Nodes.Num(); ++Index)
		{
			const FLBSpacecraftStationRecord* Record =
				InBuildAuthority->FindStation(Nodes[Index]);
			const FLBSpacecraftStationDefinition* Definition =
				Record != nullptr
					? ALBSpacecraftBuildAuthority::FindDefinition(
						Record->DefinitionId)
					: nullptr;
			if (Definition == nullptr || Definition->StageClassId.IsNone())
			{
				OutReason = FString::Printf(
					TEXT("Track node %d is not a line station"),
					Index + 1);
				return false;
			}
			FLBSpacecraftRouteStep Step;
			Step.StationId = Record->StationId;
			Step.DefinitionId = Record->DefinitionId;
			Step.StationClassId = Definition->StageClassId;
			Step.WorldTransform = Record->WorldTransform;
			Step.Stage = FLBSpacecraftProductionCatalog::StageForRouteIndex(
				Index, Nodes.Num());
			TrackRoute.Add(Step);
		}
		DerivedRoute = MoveTemp(TrackRoute);
	}
	BuildAuthority = InBuildAuthority;
	ProductionAuthority = InProductionAuthority;
	Route = MoveTemp(DerivedRoute);
	const uint32 NewTopologyHash = ComputeRouteTopologyHash(Route);
	// A RECONFIGURE THAT DOES NOT CHANGE THE ROUTE must not touch
	// in-flight assignments. This runs on every station placement
	// (LB.Spacecraft.Place -> RelayTrackThroughStations -> here,
	// unconditionally - even for a non-line building like a delivery
	// dock, which never appears in the line-station route at all) -
	// wiping Runtime.Assignments every time orphaned any craft already
	// on the line, forever: the unit's ledger record survives in
	// ProductionAuthority, but nothing ever creates it a NEW assignment
	// (TryStartUnit only ever spawns units against fresh, unclaimed
	// demand). Found live 2026-09-03: a Cargo unit force-started before
	// a delivery dock existed sat stuck at MaterialIntake permanently -
	// placing THAT dock was the moment that silently cut it loose.
	// The topology hash already exists for exactly this comparison
	// (RestoreRuntime trusts it the same way); only reset when the
	// route's own station composition or order genuinely changed.
	if (NewTopologyHash != Runtime.RouteTopologyHash)
	{
		Runtime.Assignments.Reset();
	}
	Runtime.RouteTopologyHash = NewTopologyHash;
	OutReason.Reset();
	return true;
}

FLBSpacecraftRuntimeAssignment* ALBSpacecraftRuntimeCoordinator::FindAssignment(
	FName UnitId)
{
	for (FLBSpacecraftRuntimeAssignment& Assignment : Runtime.Assignments)
	{
		if (Assignment.UnitId == UnitId)
		{
			return &Assignment;
		}
	}
	return nullptr;
}

const FLBSpacecraftRuntimeAssignment*
ALBSpacecraftRuntimeCoordinator::FindAssignment(FName UnitId) const
{
	return const_cast<ALBSpacecraftRuntimeCoordinator*>(this)
		->FindAssignment(UnitId);
}

bool ALBSpacecraftRuntimeCoordinator::StationOccupiedByOther(FName StationId,
	FName IgnoreUnitId) const
{
	for (const FLBSpacecraftRuntimeAssignment& Assignment : Runtime.Assignments)
	{
		if (Assignment.UnitId != IgnoreUnitId
			&& Assignment.StationId == StationId)
		{
			return true;
		}
	}
	return false;
}

bool ALBSpacecraftRuntimeCoordinator::TryStartUnit(FName& OutUnitId,
	FString& OutReason)
{
	OutUnitId = NAME_None;
	if (!IsConfigured() || ProductionAuthority == nullptr)
	{
		OutReason = TEXT("Coordinator is not configured");
		return false;
	}
	const FLBSpacecraftRouteStep& Head = Route[0];
	if (StationOccupiedByOther(Head.StationId, NAME_None))
	{
		OutReason = TEXT("The head station is occupied");
		return false;
	}
	// Demand decides the recipe: the OLDEST accepted contract with
	// undispatched quantity that THIS LINE CAN ACTUALLY BUILD names
	// what it builds next.
	//
	// The line used to take the oldest such contract and stop there. A
	// player who accepted a Cargo order on a Mk1 line - which the
	// craft-size law rightly refuses - then had every later contract
	// blocked behind it forever, with no cancel and no expiry to clear
	// it: a silent, permanent end to all production and all income.
	// Skipping past a contract the line cannot serve keeps the law
	// intact (the Cargo order is still not built) without bricking the
	// factory, and the refusal that made us skip is the reason the
	// player is shown when NOTHING can be built.
	FName DemandRecipeId = NAME_None;
	FLBSpacecraftRecipe DemandRecipe;
	FString FirstRefusal;
	bool bSawDemand = false;
	for (const FLBSpacecraftContract& Contract :
		ProductionAuthority->GetContracts())
	{
		if (Contract.State != ELBSpacecraftContractState::Accepted
			|| Contract.DispatchedCount >= Contract.Quantity)
		{
			continue;
		}
		bSawDemand = true;
		FLBSpacecraftRecipe Candidate;
		if (!FLBSpacecraftProductionCatalog::FindRecipe(Contract.RecipeId,
			Candidate))
		{
			if (FirstRefusal.IsEmpty())
			{
				FirstRefusal = FString::Printf(
					TEXT("Contract names unknown recipe %s"),
					*Contract.RecipeId.ToString());
			}
			continue;
		}
		FString ServiceRefusal;
		if (!ALBSpacecraftBuildAuthority::RouteCanServiceRecipe(Route,
			Candidate, ServiceRefusal))
		{
			if (FirstRefusal.IsEmpty())
			{
				FirstRefusal = ServiceRefusal;
			}
			continue;
		}
		DemandRecipeId = Contract.RecipeId;
		DemandRecipe = Candidate;
		break;
	}
	if (DemandRecipeId.IsNone())
	{
		OutReason = bSawDemand && !FirstRefusal.IsEmpty()
			? FirstRefusal
			: TEXT("No contract demands a craft");
		return false;
	}
	if (!ProductionAuthority->CreateUnit(DemandRecipeId, OutUnitId,
		OutReason))
	{
		return false;
	}
	FLBSpacecraftRuntimeAssignment Assignment;
	Assignment.UnitId = OutUnitId;
	Assignment.RouteIndex = 0;
	Assignment.StationId = Head.StationId;
	Assignment.CycleElapsedSeconds = 0.f;
	Runtime.Assignments.Add(Assignment);
	OutReason.Reset();
	return true;
}

void ALBSpacecraftRuntimeCoordinator::ResetConfiguration()
{
	Route.Reset();
	Runtime.Assignments.Reset();
}

bool ALBSpacecraftRuntimeCoordinator::TryAdvanceAssignment(
	FLBSpacecraftRuntimeAssignment& Assignment, FString& OutHoldReason)
{
	const FLBSpacecraftUnitState* Unit =
		ProductionAuthority->FindUnit(Assignment.UnitId);
	if (Unit == nullptr)
	{
		OutHoldReason = TEXT("Assigned unit missing from the ledger");
		return false;
	}

	const bool bLastRouteStep = Assignment.RouteIndex == Route.Num() - 1;

	// The hover test: Testing is STATION-LESS (owner 2026-08-26) and
	// happens in place at the end of the line - the self-start hover IS
	// the test. The gate fires when the unit is IN Testing.
	if (bLastRouteStep && Unit->Stage == ELBSpacecraftStage::Testing)
	{
		// A craft under rework is on the floor with its panels off.
		// It retests when the work is paid for, not before.
		if (Unit->ReworkSecondsRemaining > 0.f)
		{
			// SAY WHY AND WHAT TO DO (owner 2026-09-01: easy UI). The
			// overnight stranger run sat on a bare countdown for nine
			// game-minutes with no hint that uncrewed stations caused
			// it - a first-session wall with no door.
			OutHoldReason = FString::Printf(
				TEXT("HOLDING: REWORKING %s - %.0f s LEFT. DEFECTS COME ")
				TEXT("FROM UNCREWED STATIONS - HIRE DRONES TO BUILD ")
				TEXT("CLEAN"),
				*Assignment.UnitId.ToString(),
				Unit->ReworkSecondsRemaining);
			return false;
		}
		if (!Unit->bQualityRecorded)
		{
			if (!bAutoRunHoverTest)
			{
				OutHoldReason = TEXT("Holding for the hover test result");
				return false;
			}
			// THE TRIM LOOP. The self-start hover IS the test, and it
			// judges the WORKMANSHIP the craft collected coming down
			// the line - but a real acceptance is not one reading. Rotor
			// track and balance is run, measure, adjust, run again, and
			// a craft only leaves when the residual is inside limits.
			//
			// A clean craft settles on the first pass. One carrying
			// defects - still inside tolerance, so still airworthy -
			// needs another pass for each, and every pass costs a full
			// Testing cycle of pad time plus the drone-seconds the
			// inspection sweep is already burning.
			const int32 PassesNeeded =
				FLBSpacecraftProductionCatalog::TrimPassesRequired(
					Unit->DefectPoints,
					FLBSpacecraftDifficulty::Current()
						.HoverTestDefectTolerance);
			if (PassesNeeded != INDEX_NONE
				&& Unit->TrimPassesDone + 1 < PassesNeeded)
			{
				// Not settled yet: charge another pass and say what the
				// pad is reading, so the wait is legible rather than a
				// stalled line.
				if (!ProductionAuthority->RecordTrimPass(
					Assignment.UnitId, OutHoldReason))
				{
					return false;
				}
				// RESET THE CYCLE, which the old fail path did not do.
				// CycleElapsedSeconds stays clamped at the cycle length
				// otherwise, so the next pass would run instantly and
				// every trim after the first would be free. It went
				// unnoticed because the gate was one-shot and never
				// looped.
				Assignment.CycleElapsedSeconds = 0.f;
				OutHoldReason = FString::Printf(
					TEXT("Trimming %s - pass %d of %d, %.2f deg out"),
					*Assignment.UnitId.ToString(),
					Unit->TrimPassesDone + 1, PassesNeeded,
					FLBSpacecraftProductionCatalog::TrimResidualDeg(
						Unit->DefectPoints, Unit->TrimPassesDone));
				return false;
			}
			const bool bPassed = PassesNeeded != INDEX_NONE;
			FString QualityReason;
			if (!ProductionAuthority->RecordQualityResult(
				Assignment.UnitId, bPassed, QualityReason))
			{
				OutHoldReason = QualityReason;
				return false;
			}
			if (!bPassed)
			{
				// Reset here too: a retest after rework used to cost no
				// pad time at all, because this path left
				// CycleElapsedSeconds clamped at the cycle length.
				Assignment.CycleElapsedSeconds = 0.f;
				OutHoldReason = FString::Printf(
					TEXT("Hover test failed: %s will not trim out - ")
					TEXT("%d defects, reworking (crew your stations)"),
					*Assignment.UnitId.ToString(), Unit->DefectPoints);
				return false;
			}
		}
	}

	// Allocation-driven consumption: leaving a station spends one of
	// each component ALLOCATED there, all-or-nothing, from the floor
	// store. Empty allocation = nothing consumed (fail-open until the
	// player allocates); a shortage HOLDS the unit, part named.
	if (InventoryAuthority != nullptr && BuildAuthority != nullptr
		&& Route.IsValidIndex(Assignment.RouteIndex))
	{
		const FLBSpacecraftStationRecord* Record =
			BuildAuthority->FindStation(
				Route[Assignment.RouteIndex].StationId);
		if (Record != nullptr && Record->AllocatedComponents.Num() > 0
			&& !Assignment.bStageComponentsConsumed)
		{
			// A station eats from its OWN STOCKPILE (owner 2026-08-27,
			// the Production Line model): goods sit at the station
			// that fits them, and delivery drones keep that stockpile
			// fed. It used to reach into one global "Store.Floor",
			// which made the whole factory's haulage decoration - if
			// anything anywhere on site counted as available, nothing
			// ever had to be carried.
			const FName Stockpile(*FString::Printf(TEXT("Store.%s"),
				*Record->StationId.ToString()));
			// Parts go on in the RECIPE'S FIXING ORDER, not in whatever
			// order the player happened to tick them on. Two things turn
			// on this. The shortage message names the part that is
			// actually blocking the build - the FIRST one missing in
			// sequence - instead of an arbitrary one, so "waiting for
			// the powerplant" does not get reported as "waiting for the
			// seats". And a station that fits several parts fits them in
			// a defined order, which is what lets the drones show it and
			// what makes an allocation a decision rather than a
			// checkbox.
			TArray<FName> ToFit = Record->AllocatedComponents;
			FLBSpacecraftRecipe Fixing;
			if (FLBSpacecraftProductionCatalog::FindRecipe(
				Unit->RecipeId, Fixing))
			{
				// Anything the recipe does not fit sorts last rather than
				// being dropped: an allocation the recipe has no use for
				// is a player mistake to surface, not one to silently
				// honour or silently ignore.
				ToFit.Sort([&Fixing](const FName& A, const FName& B)
				{
					const int32 IndexA =
						FLBSpacecraftProductionCatalog::FixingIndexOf(
							Fixing, A);
					const int32 IndexB =
						FLBSpacecraftProductionCatalog::FixingIndexOf(
							Fixing, B);
					return (IndexA == INDEX_NONE ? MAX_int32 : IndexA)
						< (IndexB == INDEX_NONE ? MAX_int32 : IndexB);
				});
			}
			// HOW MANY, not just which. A bigger craft carries more of
			// the same components - a hauler takes three engines where
			// a scout takes one - and until this was read from the
			// recipe every tier consumed exactly one of everything.
			// That made the second tier cost the same as the first
			// while selling for 2.4 times as much.
			for (const FName& Component : ToFit)
			{
				const int32 Needed = FLBSpacecraftProductionCatalog
					::ComponentCountForItem(Fixing, Component);
				if (InventoryAuthority->GetQuantity(Stockpile, Component)
					< Needed)
				{
					// Production Line's own words for this state. The
					// line waits; it never breaks. The COUNT is named
					// because "needs 1x" when it wants three is a
					// refusal that sends the player to fix the wrong
					// thing.
					// The item's NAME ("Hull component"), not its id
					// ("Component.Hull") - the stranger read the id.
					const FLBSpacecraftItemDefinition* Item =
						FLBSpacecraftItemCatalogue::FindItem(Component);
					OutHoldReason = FString::Printf(
						TEXT("Insufficient resources: %s needs %dx %s%s"),
						*Record->StationId.ToString(), Needed,
						Item != nullptr ? *Item->DisplayName : *Component.ToString(),
						*DescribeSupplyShortfall(Record->StationId,
							Component));
					return false;
				}
			}
			for (const FName& Component : ToFit)
			{
				FString WithdrawReason;
				const bool bTaken = InventoryAuthority->Withdraw(
					Stockpile, Component,
					FLBSpacecraftProductionCatalog::ComponentCountForItem(
						Fixing, Component),
					WithdrawReason);
				checkf(bTaken,
					TEXT("validated component must withdraw"));
			}
			Assignment.bStageComponentsConsumed = true;
		}
	}

	// WORKMANSHIP: the crew that just worked this craft decides how
	// well it was fitted. Charged once per stage step, before the
	// advance, so a held unit never collects the same defects twice.
	if (BuildAuthority != nullptr && !Assignment.bStageDefectsAccrued
		&& Route.IsValidIndex(Assignment.RouteIndex))
	{
		const FLBSpacecraftStationRecord* CrewRecord =
			BuildAuthority->FindStation(
				Route[Assignment.RouteIndex].StationId);
		const FLBSpacecraftStationDefinition* CrewDefinition =
			CrewRecord != nullptr
				? ALBSpacecraftBuildAuthority::FindDefinition(
					CrewRecord->DefinitionId)
				: nullptr;
		if (CrewRecord != nullptr && CrewDefinition != nullptr)
		{
			// THE SNAPSHOT, not the station's live record (2026-09-03
			// audit): this block can run tens of seconds to minutes
			// after the crew that actually did the work, once the
			// whole line pulses - reading live let a player dismiss a
			// finished station's crew (rational, they're idle) and get
			// unfairly charged, or install crew just ahead of the
			// pulse to buy a clean read for work done uncrewed. Only
			// DroneSlotCount (the station's fixed catalog capacity,
			// not per-instance state) still comes from the live
			// definition.
			//
			// The crew's SIZE and its CHARACTER both count: a station
			// short of drones rushes the fit, and a crew of winches
			// bodges where a crew of sprays would not.
			const int32 Points =
				FLBSpacecraftProductionCatalog::DefectPointsForCrewQuality(
					Assignment.SnapshotInstalledDrones,
					CrewDefinition->DroneSlotCount,
					ALBSpacecraftBuildAuthority::ComputeTypedCrewQuality(
						Assignment.SnapshotInstalledDroneTypes));
			FString DefectReason;
			if (!ProductionAuthority->AccrueDefects(Assignment.UnitId,
				Points, DefectReason))
			{
				OutHoldReason = DefectReason;
				return false;
			}
			// INSPECTION BETWEEN STATIONS (owner 2026-08-28, the
			// settled pulse-line model): a station does not pass its
			// own bad work down the line - it opens rework and holds
			// the craft until that work is paid for.
			//
			// But only WHEN SOMEONE COMPETENT IS WATCHING. An empty
			// station has nobody to notice, and a rough crew is the
			// reason the fitting is bad in the first place - neither
			// catches its own mistake, and the craft carries the
			// defect to final acceptance, where it costs far more.
			// Without this the feature ate the end-of-line quality
			// gate entirely: every defect was caught and reworked in
			// place, so no craft could ever fail its hover test.
			const bool bSomeoneIsWatching =
				Assignment.SnapshotInstalledDrones > 0
				&& ALBSpacecraftBuildAuthority::ComputeTypedCrewQuality(
					Assignment.SnapshotInstalledDroneTypes) >= 0.9f;
			if (Points > 0 && bSomeoneIsWatching)
			{
				FString ReworkReason;
				ProductionAuthority->OpenStationRework(Assignment.UnitId,
					FLBSpacecraftProductionCatalog
						::StationReworkSecondsFor(Points),
					ReworkReason);
			}
		}
		Assignment.bStageDefectsAccrued = true;
	}

	// A craft owing rework does not pulse on, wherever it stands. The
	// end-of-line quality gate has its own rework hold; this is the
	// same rule applied at every station, which is what "inspection
	// between stations" means.
	if (Unit->ReworkSecondsRemaining > 0.f && !bLastRouteStep)
	{
		OutHoldReason = FString::Printf(
			TEXT("Inspection: reworking %s at %s - %.0f s remaining"),
			*Assignment.UnitId.ToString(),
			*Assignment.StationId.ToString(),
			Unit->ReworkSecondsRemaining);
		return false;
	}

	// Occupancy: moving to a DIFFERENT physical station needs it free.
	// (Consecutive stages can share one station - e.g. intake + processing.)
	if (!bLastRouteStep)
	{
		const FLBSpacecraftRouteStep& NextStep = Route[Assignment.RouteIndex + 1];
		if (NextStep.StationId != Assignment.StationId
			&& StationOccupiedByOther(NextStep.StationId, Assignment.UnitId))
		{
			OutHoldReason = FString::Printf(TEXT("Holding: station %s occupied"),
				*NextStep.StationId.ToString());
			return false;
		}
	}

	// STAGE IS DERIVED FROM POSITION now (one repeated station type,
	// any line length): departing station i advances the product ladder
	// to station i+1's arrival stage - possibly several rungs on a
	// short line, possibly none on a long one. The unit already IN
	// Testing was handled by the gate above, so this block only ever
	// climbs the station-served rungs and the Assembly->Testing step.
	FString AdvanceReason;
	if (bLastRouteStep)
	{
		if (Unit->Stage == ELBSpacecraftStage::Testing)
		{
			// The gate above recorded a PASS; this single advance is
			// Testing -> Dispatched (settlement happens inside).
			if (!ProductionAuthority->AdvanceUnit(Assignment.UnitId,
				AdvanceReason))
			{
				OutHoldReason = AdvanceReason;
				return false;
			}
		}
		else
		{
			// Fitting done at the line's end: climb the remaining
			// rungs into Testing and hold in place for the self-start.
			int32 Guard = 0;
			while (Guard++ < 16)
			{
				const FLBSpacecraftUnitState* Climbing =
					ProductionAuthority->FindUnit(Assignment.UnitId);
				if (Climbing == nullptr
					|| Climbing->Stage >= ELBSpacecraftStage::Testing)
				{
					break;
				}
				if (!ProductionAuthority->AdvanceUnit(Assignment.UnitId,
					AdvanceReason))
				{
					OutHoldReason = AdvanceReason;
					return false;
				}
			}
			Assignment.CycleElapsedSeconds = 0.f;
			// Assembly and Testing share this station: the craft is
			// not moving on, so its workmanship has been judged.
			Assignment.bStageDefectsAccrued = true;
			OutHoldReason.Reset();
			return true;
		}
		Runtime.Assignments.RemoveAll(
			[UnitId = Assignment.UnitId](
				const FLBSpacecraftRuntimeAssignment& Candidate)
			{
				return Candidate.UnitId == UnitId;
			});
	}
	else
	{
		const ELBSpacecraftStage NextArrival =
			FLBSpacecraftProductionCatalog::StageForRouteIndex(
				Assignment.RouteIndex + 1, Route.Num());
		int32 Guard = 0;
		while (Guard++ < 16)
		{
			const FLBSpacecraftUnitState* Climbing =
				ProductionAuthority->FindUnit(Assignment.UnitId);
			if (Climbing == nullptr || Climbing->Stage >= NextArrival)
			{
				break;
			}
			if (!ProductionAuthority->AdvanceUnit(Assignment.UnitId,
				AdvanceReason))
			{
				OutHoldReason = AdvanceReason;
				return false;
			}
		}
		++Assignment.RouteIndex;
		Assignment.bStageComponentsConsumed = false;
		Assignment.bStageDefectsAccrued = false;
		Assignment.StationId = Route[Assignment.RouteIndex].StationId;
		Assignment.CycleElapsedSeconds = 0.f;
	}
	OutHoldReason.Reset();
	return true;
}

bool ALBSpacecraftRuntimeCoordinator::TickProduction(double DeltaSeconds,
	FString& OutReason)
{
	using namespace LBSpacecraftRuntimeCoordinatorPrivate;
	if (!IsConfigured() || ProductionAuthority == nullptr)
	{
		OutReason = TEXT("Coordinator is not configured");
		return false;
	}
	if (!ProductionAuthority->AdvanceSimSeconds(DeltaSeconds, OutReason))
	{
		return false;
	}

	// Accrue cycle time. A finished stop HOLDS the craft (bStopComplete)
	// rather than releasing it: the pulse below is the only thing that
	// moves a craft.
	for (FLBSpacecraftRuntimeAssignment& Assignment : Runtime.Assignments)
	{
		const FLBSpacecraftUnitState* Unit =
			ProductionAuthority->FindUnit(Assignment.UnitId);
		if (Unit == nullptr)
		{
			continue;
		}
		FLBSpacecraftRecipe Recipe;
		if (!FLBSpacecraftProductionCatalog::FindRecipe(Unit->RecipeId, Recipe))
		{
			continue;
		}
		const float Cycle = SpacecraftAssignmentCycleSeconds(Recipe,
			Unit->Stage, Assignment.RouteIndex, Route.Num(),
			BuildAuthority, Route);
		if (Cycle > 0.f && Assignment.CycleElapsedSeconds < Cycle)
		{
			// Installed drones speed the station's work (owner
			// 2026-08-26, the worker-slot model): 0 drones crawl at
			// half pace, 2 are nominal, 8 fly.
			float WorkBonus = 1.f;
			if (BuildAuthority != nullptr
				&& Route.IsValidIndex(Assignment.RouteIndex))
			{
				WorkBonus = BuildAuthority->GetStationWorkBonus(
					Route[Assignment.RouteIndex].StationId);
			}
			Assignment.CycleElapsedSeconds = FMath::Min(
				Assignment.CycleElapsedSeconds
					+ static_cast<float>(DeltaSeconds) * WorkBonus,
				Cycle);
		}
		if (Cycle > 0.f && Assignment.CycleElapsedSeconds >= Cycle
			&& !Assignment.bStopComplete)
		{
			Assignment.bStopComplete = true;
			// SNAPSHOT THE CREW RIGHT HERE - see the field comment on
			// SnapshotInstalledDrones. The later defect read (in
			// TryAdvanceAssignment, once the pulse actually processes
			// this assignment) uses this, not the station's live
			// record.
			Assignment.SnapshotInstalledDrones = 0;
			Assignment.SnapshotInstalledDroneTypes.Reset();
			if (BuildAuthority != nullptr
				&& Route.IsValidIndex(Assignment.RouteIndex))
			{
				if (const FLBSpacecraftStationRecord* CrewRecord =
					BuildAuthority->FindStation(
						Route[Assignment.RouteIndex].StationId))
				{
					Assignment.SnapshotInstalledDrones =
						CrewRecord->InstalledDrones;
					Assignment.SnapshotInstalledDroneTypes =
						CrewRecord->InstalledDroneTypes;
				}
			}
		}
	}

	// THE PULSE (PULSE_LINE_DESIGN_v001). Stopped: when EVERY craft on
	// the line has finished its stop, the cranes start moving. Moving:
	// when the move phase has run its trips, every craft advances one
	// station together, tail-first so downstream moves free upstream,
	// and the line stops again. A craft the advance refuses (parts
	// missing, rework owed, the next station still taken) holds where
	// it is with its stop still complete, and rides the NEXT pulse.
	//
	// This replaces "each craft moves the moment its own stop is over
	// and the next station is free" - a car line with the belt taken
	// off. On a pulse line the slowest station sets the pace and a
	// finished station visibly waits; that wait is what the player
	// shortens by splitting the fitting order or adding stations.
	bool bPulsed = false;
	FString TickHolds;
	// THE LINE'S END IS NOT A CRANE MOVE. A craft at the last station
	// finishes its fitting, climbs into its hover test in place, and
	// when the test passes it FLIES OUT of the factory itself (owner
	// 2026-08-29: craft depart from the building). None of that waits
	// for a pulse, and none of it occupies a crane - so it runs every
	// tick, as it always did, and the pulse below moves only the craft
	// with a station still ahead of them.
	FString EndHold;
	{
		TArray<FName> AtEnd;
		for (const FLBSpacecraftRuntimeAssignment& Assignment :
			Runtime.Assignments)
		{
			if (Assignment.bStopComplete
				&& Assignment.RouteIndex == Route.Num() - 1)
			{
				AtEnd.Add(Assignment.UnitId);
			}
		}
		for (FName UnitId : AtEnd)
		{
			FLBSpacecraftRuntimeAssignment* Assignment =
				FindAssignment(UnitId);
			if (Assignment == nullptr)
			{
				continue;
			}
			FString HoldReason;
			if (TryAdvanceAssignment(*Assignment, HoldReason))
			{
				if (FLBSpacecraftRuntimeAssignment* Still =
					FindAssignment(UnitId))
				{
					Still->bStopComplete = false; // the test's own stop
				}
			}
			else if (!HoldReason.IsEmpty() && EndHold.IsEmpty())
			{
				EndHold = HoldReason;
			}
		}
	}
	if (Runtime.Phase == ELBSpacecraftLinePhase::Stopped)
	{
		int32 Movers = 0;
		bool bAllComplete = true;
		for (const FLBSpacecraftRuntimeAssignment& Assignment :
			Runtime.Assignments)
		{
			if (Assignment.RouteIndex >= Route.Num() - 1)
			{
				continue; // the line's end, handled above
			}
			if (!Assignment.bStopComplete)
			{
				bAllComplete = false;
				break;
			}
			++Movers;
		}
		if (bAllComplete && Movers > 0)
		{
			Runtime.Phase = ELBSpacecraftLinePhase::Moving;
			Runtime.PhaseElapsedSeconds = 0.f;
		}
	}
	if (Runtime.Phase == ELBSpacecraftLinePhase::Moving)
	{
		Runtime.PhaseElapsedSeconds += static_cast<float>(DeltaSeconds);
		if (Runtime.PhaseElapsedSeconds >= GetMoveSeconds())
		{
			TArray<FLBSpacecraftRuntimeAssignment*> Ordered;
			for (FLBSpacecraftRuntimeAssignment& Assignment :
				Runtime.Assignments)
			{
				if (IsPulseMover(Assignment))
				{
					Ordered.Add(&Assignment);
				}
			}
			Ordered.Sort([](const FLBSpacecraftRuntimeAssignment& A,
				const FLBSpacecraftRuntimeAssignment& B)
			{
				return A.RouteIndex > B.RouteIndex;
			});
			TArray<FName> ToAdvance;
			for (FLBSpacecraftRuntimeAssignment* Assignment : Ordered)
			{
				ToAdvance.Add(Assignment->UnitId);
			}
			for (FName UnitId : ToAdvance)
			{
				// Re-found each time: a dispatch removes an assignment
				// and the array reallocates.
				FLBSpacecraftRuntimeAssignment* Assignment =
					FindAssignment(UnitId);
				if (Assignment == nullptr)
				{
					continue;
				}
				FString HoldReason;
				if (TryAdvanceAssignment(*Assignment, HoldReason))
				{
					// Moved, or climbed into Testing in place: either
					// way a NEW stop begins. (A dispatched unit is
					// gone; FindAssignment says so.)
					if (FLBSpacecraftRuntimeAssignment* Moved =
						FindAssignment(UnitId))
					{
						Moved->bStopComplete = false;
					}
				}
				else if (!HoldReason.IsEmpty() && TickHolds.IsEmpty())
				{
					// Keep the FIRST hold of the pulse: units are
					// walked furthest-first, so the one nearest the
					// end of the line is the one actually blocking.
					TickHolds = HoldReason;
				}
				// A hold is a visible state, not an error - the unit
				// waits, stop still complete, for the next pulse.
			}
			Runtime.Phase = ELBSpacecraftLinePhase::Stopped;
			Runtime.PhaseElapsedSeconds = 0.f;
			++Runtime.PulseCount;
			bPulsed = true;
		}
	}
	// The hold reason is a PULSE's verdict; between pulses it stands,
	// so a starved station stays named until the next pulse clears it.
	// The line's end reports its own holds (the hover test, rework)
	// only when no pulse hold is standing.
	if (bPulsed)
	{
		LastPulseHold = TickHolds;
	}
	LastHoldReason = !LastPulseHold.IsEmpty() ? LastPulseHold : EndHold;

	// Feed the head of the line - INTO AN EMPTY LINE, or at the pulse.
	// A craft admitted mid-stop would start its own clock late and be
	// the slowest station by construction, dragging every pulse; on a
	// pulse line all stops start together.
	if (bAutoStartUnits && (Runtime.Assignments.Num() == 0 || bPulsed))
	{
		FName NewUnitId;
		FString StartReason;
		if (TryStartUnit(NewUnitId, StartReason))
		{
			LastStartRefusal.Reset();
		}
		else
		{
			// KEPT AND SAID ONCE. Some refusals really are idle states -
			// no demand, the head still occupied - but the same line
			// also swallows "the route cannot service this recipe",
			// which is a fault, and swallowing it means a factory that
			// builds nothing looks identical to one waiting for work.
			//
			// Logged only when the reason CHANGES, so a genuinely idle
			// line says its piece once rather than every tick.
			if (StartReason != LastStartRefusal)
			{
				LastStartRefusal = StartReason;
				if (!StartReason.IsEmpty())
				{
					UE_LOG(LogTemp, Warning,
						TEXT("SPACECRAFT LINE NOT STARTING A CRAFT: %s"),
						*StartReason);
				}
			}
		}
	}
	OutReason.Reset();
	return true;
}

bool ALBSpacecraftRuntimeCoordinator::GetUnitCycleProgress(FName UnitId,
	float& OutProgress01) const
{
	using namespace LBSpacecraftRuntimeCoordinatorPrivate;
	OutProgress01 = 0.f;
	const FLBSpacecraftRuntimeAssignment* Assignment = FindAssignment(UnitId);
	if (Assignment == nullptr || ProductionAuthority == nullptr)
	{
		return false;
	}
	const FLBSpacecraftUnitState* Unit =
		ProductionAuthority->FindUnit(UnitId);
	if (Unit == nullptr)
	{
		return false;
	}
	FLBSpacecraftRecipe Recipe;
	if (!FLBSpacecraftProductionCatalog::FindRecipe(Unit->RecipeId, Recipe))
	{
		return false;
	}
	const float Cycle = SpacecraftAssignmentCycleSeconds(Recipe,
		Unit->Stage, Assignment->RouteIndex, Route.Num(),
		BuildAuthority, Route);
	if (Cycle <= 0.f)
	{
		return false;
	}
	OutProgress01 = FMath::Clamp(
		Assignment->CycleElapsedSeconds / Cycle, 0.f, 1.f);
	return true;
}

int32 ALBSpacecraftRuntimeCoordinator::GetCraneCount() const
{
	return BuildAuthority != nullptr ? BuildAuthority->GetCraneCount() : 1;
}

bool ALBSpacecraftRuntimeCoordinator::IsPulseMover(
	const FLBSpacecraftRuntimeAssignment& Assignment) const
{
	// Finished, and with a station still ahead: the line's end leaves
	// under its own power, never on a crane.
	return Assignment.bStopComplete
		&& Assignment.RouteIndex < Route.Num() - 1;
}

int32 ALBSpacecraftRuntimeCoordinator::CountStopComplete() const
{
	int32 Count = 0;
	for (const FLBSpacecraftRuntimeAssignment& Assignment :
		Runtime.Assignments)
	{
		Count += IsPulseMover(Assignment) ? 1 : 0;
	}
	return Count;
}

bool ALBSpacecraftRuntimeCoordinator::GetPaceSetter(
	FLBSpacecraftPaceSetter& Out) const
{
	using namespace LBSpacecraftRuntimeCoordinatorPrivate;
	Out = FLBSpacecraftPaceSetter();
	if (!IsConfigured() || BuildAuthority == nullptr
		|| ProductionAuthority == nullptr)
	{
		return false;
	}
	// WHICH CRAFT'S PACE? The one on the line, or - before anything is
	// started - the one the oldest accepted contract asks for, so the
	// answer is useful while the player is still laying stations out
	// rather than only once production runs.
	FName RecipeId;
	for (const FLBSpacecraftRuntimeAssignment& Assignment :
		Runtime.Assignments)
	{
		if (const FLBSpacecraftUnitState* Unit =
			ProductionAuthority->FindUnit(Assignment.UnitId))
		{
			RecipeId = Unit->RecipeId;
			break;
		}
	}
	if (RecipeId.IsNone())
	{
		for (const FLBSpacecraftContract& Contract :
			ProductionAuthority->GetContracts())
		{
			if (Contract.State == ELBSpacecraftContractState::Accepted)
			{
				RecipeId = Contract.RecipeId;
				break;
			}
		}
	}
	FLBSpacecraftRecipe Recipe;
	if (RecipeId.IsNone()
		|| !FLBSpacecraftProductionCatalog::FindRecipe(RecipeId, Recipe))
	{
		return false;
	}
	// Every station's stop, crew included. Any pre-Testing stage takes
	// the share path (the helper only branches at Testing and beyond,
	// where a craft flies its own test in place rather than taking a
	// stop the pulse waits on), so Assembly stands for "fitting" here.
	bool bFound = false;
	for (int32 Index = 0; Index < Route.Num(); ++Index)
	{
		const float Cycle = SpacecraftAssignmentCycleSeconds(Recipe,
			ELBSpacecraftStage::Assembly, Index, Route.Num(),
			BuildAuthority, Route);
		if (Cycle <= 0.f)
		{
			continue;
		}
		const float Bonus = FMath::Max(
			BuildAuthority->GetStationWorkBonus(Route[Index].StationId),
			KINDA_SMALL_NUMBER);
		const float Stop = Cycle / Bonus;
		if (Stop > Out.StopSeconds)
		{
			Out.RunnerUpStationId = Out.StationId;
			Out.RunnerUpSeconds = Out.StopSeconds;
			Out.StationId = Route[Index].StationId;
			Out.StopSeconds = Stop;
			bFound = true;
		}
		else if (Stop > Out.RunnerUpSeconds)
		{
			Out.RunnerUpStationId = Route[Index].StationId;
			Out.RunnerUpSeconds = Stop;
		}
	}
	if (!bFound)
	{
		return false;
	}
	if (const FLBSpacecraftStationRecord* Record =
		BuildAuthority->FindStation(Out.StationId))
	{
		const FLBSpacecraftStationDefinition* Definition =
			ALBSpacecraftBuildAuthority::FindDefinition(
				Record->DefinitionId);
		Out.bProcessStation =
			Definition != nullptr && Definition->bProcessStation;
	}
	Out.PulseSeconds = Out.StopSeconds + GetMoveSeconds();
	return true;
}

float ALBSpacecraftRuntimeCoordinator::GetMoveSeconds() const
{
	// ceil(craft to move / cranes) trips. Never zero: an empty pulse
	// still takes one trip, so the phase always ends.
	const int32 Moving = FMath::Max(CountStopComplete(), 1);
	const int32 Cranes = FMath::Max(GetCraneCount(), 1);
	const int32 Trips = (Moving + Cranes - 1) / Cranes;
	return FMath::Max(CraneTripSeconds, 0.01f) * Trips;
}

float ALBSpacecraftRuntimeCoordinator::GetPulseProgress01() const
{
	if (Runtime.Phase != ELBSpacecraftLinePhase::Moving)
	{
		return 0.f;
	}
	return FMath::Clamp(Runtime.PhaseElapsedSeconds / GetMoveSeconds(),
		0.f, 1.f);
}

bool ALBSpacecraftRuntimeCoordinator::IsUnitStopComplete(FName UnitId) const
{
	const FLBSpacecraftRuntimeAssignment* Assignment = FindAssignment(UnitId);
	return Assignment != nullptr && Assignment->bStopComplete;
}

bool ALBSpacecraftRuntimeCoordinator::GetUnitCarryWindow(FName UnitId,
	float& OutStart01, float& OutEnd01) const
{
	OutStart01 = 0.f;
	OutEnd01 = 0.f;
	if (Runtime.Phase != ELBSpacecraftLinePhase::Moving)
	{
		return false;
	}
	const FLBSpacecraftRuntimeAssignment* Assignment = FindAssignment(UnitId);
	if (Assignment == nullptr || !IsPulseMover(*Assignment))
	{
		return false;
	}
	// Tail-first order among the craft that move; `cranes` craft share
	// a trip.
	int32 Ahead = 0;
	for (const FLBSpacecraftRuntimeAssignment& Other : Runtime.Assignments)
	{
		if (IsPulseMover(Other) && Other.RouteIndex > Assignment->RouteIndex)
		{
			++Ahead;
		}
	}
	const int32 Cranes = FMath::Max(GetCraneCount(), 1);
	const int32 Moving = FMath::Max(CountStopComplete(), 1);
	const int32 Trips = (Moving + Cranes - 1) / Cranes;
	const int32 Trip = Ahead / Cranes;
	OutStart01 = static_cast<float>(Trip) / Trips;
	OutEnd01 = static_cast<float>(Trip + 1) / Trips;
	return true;
}

bool ALBSpacecraftRuntimeCoordinator::GetInspectionSweep(FName& OutUnitId,
	FName& OutStationId, float& OutProgress01, int32& OutDefectsFound) const
{
	OutUnitId = NAME_None;
	OutStationId = NAME_None;
	OutProgress01 = 0.f;
	OutDefectsFound = 0;
	if (ProductionAuthority == nullptr)
	{
		return false;
	}
	for (const FLBSpacecraftRuntimeAssignment& Assignment :
		Runtime.Assignments)
	{
		const FLBSpacecraftUnitState* Unit =
			ProductionAuthority->FindUnit(Assignment.UnitId);
		if (Unit == nullptr
			|| Unit->Stage != ELBSpacecraftStage::Testing)
		{
			continue;
		}
		// A craft in rework is not being inspected - it is being put
		// right, and it will be scanned again afterwards.
		if (Unit->ReworkSecondsRemaining > 0.f)
		{
			continue;
		}
		float Progress = 0.f;
		GetUnitCycleProgress(Assignment.UnitId, Progress);
		OutUnitId = Assignment.UnitId;
		OutStationId = Assignment.StationId;
		OutProgress01 = Progress;
		OutDefectsFound = FLBSpacecraftProductionCatalog::DefectsFoundByScan(
			Unit->DefectPoints, Progress);
		return true;
	}
	return false;
}

bool ALBSpacecraftRuntimeCoordinator::ValidateRuntime(
	const FLBSpacecraftRuntimeState& State, FString& OutReason) const
{
	if (!IsConfigured() || ProductionAuthority == nullptr)
	{
		OutReason = TEXT("Coordinator is not configured");
		return false;
	}
	if (State.RouteTopologyHash != ComputeRouteTopologyHash(Route))
	{
		OutReason = TEXT("Runtime state belongs to a different route");
		return false;
	}
	TSet<FName> UnitIds;
	TSet<FName> Stations;
	for (const FLBSpacecraftRuntimeAssignment& Assignment : State.Assignments)
	{
		bool bAlready = false;
		UnitIds.Add(Assignment.UnitId, &bAlready);
		if (bAlready)
		{
			OutReason = TEXT("Duplicate unit in runtime state");
			return false;
		}
		if (!Route.IsValidIndex(Assignment.RouteIndex))
		{
			OutReason = TEXT("Assignment route index out of range");
			return false;
		}
		const FLBSpacecraftRouteStep& Step = Route[Assignment.RouteIndex];
		if (Step.StationId != Assignment.StationId)
		{
			OutReason = TEXT("Assignment station disagrees with the route");
			return false;
		}
		const FLBSpacecraftUnitState* Unit =
			ProductionAuthority->FindUnit(Assignment.UnitId);
		if (Unit == nullptr)
		{
			OutReason = FString::Printf(
				TEXT("Runtime unit %s missing from the ledger"),
				*Assignment.UnitId.ToString());
			return false;
		}
		// A station's resident sits at that station's ARRIVAL stage -
		// stage is derived from position now - except the line's end,
		// which also hosts the station-less Testing stage in place.
		const bool bLastStep =
			Assignment.RouteIndex == Route.Num() - 1;
		if (Unit->Stage != Step.Stage
			&& !(bLastStep
				&& Unit->Stage == ELBSpacecraftStage::Testing))
		{
			OutReason = TEXT("Unit stage disagrees with its route step");
			return false;
		}
		if (Assignment.CycleElapsedSeconds < 0.f)
		{
			OutReason = TEXT("Negative cycle time in runtime state");
			return false;
		}
		bool bStationTaken = false;
		Stations.Add(Assignment.StationId, &bStationTaken);
		if (bStationTaken)
		{
			OutReason = TEXT("Two units occupy one station");
			return false;
		}
	}
	if (State.PhaseElapsedSeconds < 0.f || State.PulseCount < 0)
	{
		OutReason = TEXT("Pulse counters out of range");
		return false;
	}
	if (State.Phase == ELBSpacecraftLinePhase::Moving)
	{
		// A move phase carries craft; with nothing on the line there is
		// nothing to carry, and a craft whose stop is not over cannot be
		// on the hook.
		bool bAnyComplete = false;
		for (const FLBSpacecraftRuntimeAssignment& Assignment :
			State.Assignments)
		{
			bAnyComplete |= Assignment.bStopComplete
				&& Assignment.RouteIndex < Route.Num() - 1;
		}
		if (!bAnyComplete)
		{
			OutReason = TEXT("Line is moving with no craft ready to move");
			return false;
		}
	}
	OutReason.Reset();
	return true;
}

bool ALBSpacecraftRuntimeCoordinator::RestoreRuntime(
	const FLBSpacecraftRuntimeState& State, FString& OutReason)
{
	if (!ValidateRuntime(State, OutReason))
	{
		return false; // runtime untouched - restore is all or nothing
	}
	Runtime = State;
	OutReason.Reset();
	return true;
}
