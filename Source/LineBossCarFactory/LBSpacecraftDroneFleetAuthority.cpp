#include "LBSpacecraftDroneFleetAuthority.h"
#include "LBSpacecraftRuntimeCoordinator.h"

#include "LBSpacecraftCraftingAuthority.h"
#include "LBSpacecraftInventoryAuthority.h"
#include "LBSpacecraftGameMode.h"
#include "LBSpacecraftPowerAuthority.h"

ALBSpacecraftDroneFleetAuthority::ALBSpacecraftDroneFleetAuthority()
{
	PrimaryActorTick.bCanEverTick = false;
}

FName ALBSpacecraftDroneFleetAuthority::MakeChargeLoadId(FName StationId,
	int32 DroneIndex)
{
	return FName(*FString::Printf(TEXT("DroneCharge.%s.%d"),
		*StationId.ToString(), DroneIndex));
}

void ALBSpacecraftDroneFleetAuthority::DisconnectChargeLoad(FName StationId,
	int32 DroneIndex, ALBSpacecraftPowerAuthority* InPower)
{
	const FName LoadId = MakeChargeLoadId(StationId, DroneIndex);
	if (ConnectedChargeLoads.Remove(LoadId) > 0 && InPower != nullptr)
	{
		FString Ignored;
		InPower->DisconnectLoad(LoadId, Ignored);
	}
}

bool ALBSpacecraftDroneFleetAuthority::StationHostsFittingDrones(
	const FLBSpacecraftStationDefinition& Definition)
{
	// Owner decision 2026-08-25 ("it needs the lot, it's bare"): every
	// station hosts its two fitting drones - the factory must read alive
	// everywhere, and each dock's charging is honest grid draw.
	// REFINED 2026-08-26 (owner: the power plant "shouldn't have a
	// drone"): POWER infrastructure runs itself - the plant and its
	// building carry no crew, so the drones read as production labour
	// rather than decoration.
	// BUILDINGS carry no crew - the units inside them do, so a hall
	// and its machines never double-count. The generator is named
	// exactly on top of that (owner: it "shouldn't have a drone");
	// PowerCellPlant is a CRAFTING machine and keeps its pair.
	// A SITE BUILDING is the same case as a hall: the shell the work
	// happens inside, not a workplace of its own (owner 2026-08-28).
	if (Definition.SlotCount > 0 || Definition.bSiteBuilding
		|| Definition.DefinitionId == FName(TEXT("PowerPlant")))
	{
		return false;
	}
	return true;
}

void ALBSpacecraftDroneFleetAuthority::SyncFromBuild(
	const ALBSpacecraftBuildAuthority* InBuild,
	ALBSpacecraftPowerAuthority* InPower)
{
	if (InBuild == nullptr)
	{
		return;
	}
	// Desired crew per station: LINE stations host exactly their
	// BOUGHT drones (owner 2026-08-26, the worker-slot model);
	// crafting cells keep their standing pair.
	TMap<FName, int32> DesiredCrew;
	for (const FLBSpacecraftStationRecord& Record : InBuild->GetStations())
	{
		const FLBSpacecraftStationDefinition* Definition =
			ALBSpacecraftBuildAuthority::FindDefinition(Record.DefinitionId);
		if (Definition == nullptr)
		{
			continue;
		}
		if (Definition->DroneSlotCount > 0)
		{
			DesiredCrew.Add(Record.StationId, Record.InstalledDrones);
		}
		else if (StationHostsFittingDrones(*Definition))
		{
			DesiredCrew.Add(Record.StationId, 2);
		}
	}
	for (const TPair<FName, int32>& Crew : DesiredCrew)
	{
		for (int32 Index = 0; Index < Crew.Value; ++Index)
		{
			if (FindDrone(Crew.Key, Index) == nullptr)
			{
				FLBSpacecraftDroneState Drone;
				Drone.StationId = Crew.Key;
				Drone.DroneIndex = Index;
				Drone.Charge01 = 1.f;
				Drones.Add(Drone);
			}
		}
	}
	// Removed stations - and sold drone slots - shed their drones and
	// grid loads.
	for (int32 Index = Drones.Num() - 1; Index >= 0; --Index)
	{
		const int32* Desired = DesiredCrew.Find(Drones[Index].StationId);
		if (Desired == nullptr || Drones[Index].DroneIndex >= *Desired)
		{
			DisconnectChargeLoad(Drones[Index].StationId,
				Drones[Index].DroneIndex, InPower);
			Drones.RemoveAt(Index);
		}
	}
	// Heavy haulers mirror the storage racks (owner 2026-08-26: the
	// heavy drone empties sub-assembly buffers into the storage zone)
	// AND the delivery docks. The dock's hauler exists for the first
	// factory: the stranger playthrough (2026-09-02) built line
	// stations and a dock, bought five components, and watched them sit
	// at the dock forever - a rack was a hidden third requirement that
	// nothing on screen had named. A dock's hauler only FEEDS the line
	// from what lands there; collecting machine output into the dock
	// would clog the place bought goods arrive (see the job pick).
	TSet<FName> Racks;
	for (const FLBSpacecraftStationRecord& Record : InBuild->GetStations())
	{
		if (Record.DefinitionId == FName(TEXT("StorageRack"))
			|| Record.DefinitionId == FName(TEXT("StorageRackMk2"))
			|| Record.DefinitionId == FName(TEXT("DeliveryDock")))
		{
			Racks.Add(Record.StationId);
		}
	}
	for (const FName& RackId : Racks)
	{
		const bool bKnown = Hauls.ContainsByPredicate(
			[&RackId](const FLBSpacecraftHaulState& Haul)
			{ return Haul.RackStationId == RackId; });
		if (!bKnown)
		{
			FLBSpacecraftHaulState Haul;
			Haul.RackStationId = RackId;
			Hauls.Add(Haul);
		}
	}
	for (int32 Index = Hauls.Num() - 1; Index >= 0; --Index)
	{
		if (!Racks.Contains(Hauls[Index].RackStationId))
		{
			Hauls.RemoveAt(Index);
		}
	}
}

bool ALBSpacecraftDroneFleetAuthority::StockpileWantsItem(int32 OnHand,
	int32 TopUpTarget)
{
	return OnHand < FMath::Max(TopUpTarget, 1);
}

namespace LBSpacecraftHaulPrivate
{
	// Unity-build safety: helpers qualified by subject.
	FName SpacecraftHaulStoreOf(FName StationId)
	{
		return FName(*FString::Printf(TEXT("Store.%s"),
			*StationId.ToString()));
	}

	/** Everything a station consumes: the components fitted at a line
	 *  station, or the inputs of whatever recipe a machine is set to. */
	/** What a station's shelf should hold of each item, DEMAND-CAPPED.
	 *  Line components keep the plain top-up target (one consumer
	 *  each, nothing can strand). A machine's recipe inputs are capped
	 *  by what its REMAINING ORDER can actually use: the blind target
	 *  used to deliver six of a shared intermediate to whichever shelf
	 *  had room, and with single-producer items (LightAlloy feeds four
	 *  structural recipes) the strand starved the real consumer while
	 *  three blocked machines each sat on a pile - found by the
	 *  self-feeding-factory test's starvation dump. A finished order
	 *  caps at zero, so nothing is hauled to a machine with no work. */
	/** One shelf requirement: the top-up target, and the ONE-CYCLE need
	 *  that reclaim moves are allowed to satisfy (see the reclaim note
	 *  in the Idle scan). */
	struct FLBSpacecraftShelfWant
	{
		FName ItemId;
		int32 TargetUnits = 0;
		int32 OneCycleUnits = 0;
	};

	void SpacecraftHaulRequirementsOf(
		const FLBSpacecraftStationRecord& Record,
		const ALBSpacecraftCraftingAuthority* InCrafting,
		int32 TopUpTargetUnits,
		TArray<FLBSpacecraftShelfWant>& OutWants)
	{
		OutWants.Reset();
		for (const FName& Component : Record.AllocatedComponents)
		{
			FLBSpacecraftShelfWant Want;
			Want.ItemId = Component;
			Want.TargetUnits = TopUpTargetUnits;
			Want.OneCycleUnits = 1;
			OutWants.Add(Want);
		}
		if (InCrafting != nullptr)
		{
			if (const FLBSpacecraftItemRecipe* Recipe =
				InCrafting->GetSelectedRecipe(Record.StationId))
			{
				const int32 Remaining = FMath::Max(
					InCrafting->GetOrderRemaining(Record.StationId), 0);
				for (const FLBSpacecraftItemStack& Input : Recipe->Inputs)
				{
					FLBSpacecraftShelfWant Want;
					Want.ItemId = Input.ItemId;
					// A machine's shelf holds EXACTLY ONE CYCLE of
					// each input, no more and no less. Two separate
					// failures taught both bounds. Less: the flat
					// top-up target (4) was silently smaller than some
					// per-cycle counts (HullFrameSet eats six
					// FrameRibs), so those machines could never be
					// stocked to run at all. More: shelf capacity is
					// finite units, and any input stocked beyond a
					// cycle crowds out the mix - the hull assembler
					// hoarded four of each SET while the skin set it
					// actually lacked had no room to land. Float
					// belongs in the shared racks; the shelf is a
					// fixture, not a store.
					Want.OneCycleUnits =
						Remaining > 0 ? Input.Count : 0;
					Want.TargetUnits = Want.OneCycleUnits;
					OutWants.Add(Want);
				}
			}
		}
	}
	/** The delivery's drop: re-clamped against the shelf AS IT IS NOW and
	 *  transferred source -> shelf in one call. Lifted out of the return
	 *  leg on 2026-09-02 so it can run on ARRIVAL. */
	void SpacecraftHaulDropDelivery(FLBSpacecraftHaulState& Haul,
		ALBSpacecraftCraftingAuthority* InCrafting,
		ALBSpacecraftInventoryAuthority* InInventory,
		const ALBSpacecraftBuildAuthority* InBuild,
		int32 StockpileTopUpUnits)
	{
			// Put it down at the station that wanted it. A
			// full stockpile or a rack that has since been
			// emptied simply ends the run - the next Idle tick
			// re-decides with fresh information.
			//
			// RE-CLAMPED against the shelf as it is NOW: the
			// plan was made a flight ago, and a delivery that
			// landed in between (or a consumed order) can
			// shrink or erase the shortfall. Without this the
			// overshoot re-arms the reclaim oscillation the
			// one-hauler-per-want rule exists to stop. Items
			// move only at dropoff, so clamping to zero means
			// nothing moved at all - there is no cargo to
			// return.
			if (InBuild != nullptr)
			{
				if (const FLBSpacecraftStationRecord* DropRecord
					= InBuild->FindStation(Haul.MachineStationId))
				{
					TArray<FLBSpacecraftShelfWant> DropWants;
					SpacecraftHaulRequirementsOf(*DropRecord,
						InCrafting, StockpileTopUpUnits,
						DropWants);
					for (const FLBSpacecraftShelfWant& DropWant :
						DropWants)
					{
						if (DropWant.ItemId != Haul.CarryItemId)
						{
							continue;
						}
						const int32 NowShort = FMath::Max(
							DropWant.TargetUnits
							- InInventory->GetQuantity(
								SpacecraftHaulStoreOf(
									Haul.MachineStationId),
								Haul.CarryItemId), 0);
						Haul.CarryCount = FMath::Min(
							Haul.CarryCount, NowShort);
						break;
					}
				}
			}
			FString Reason;
			if (Haul.CarryCount > 0
				&& !InInventory->Transfer(Haul.SourceStoreId,
					SpacecraftHaulStoreOf(Haul.MachineStationId),
					Haul.CarryItemId, Haul.CarryCount, Reason))
			{
				// Say it rather than swallow it: a delivery
				// that cannot land is exactly the kind of
				// silent stall this whole system is meant to
				// make visible.
				UE_LOG(LogTemp, Display,
					TEXT("HAUL REFUSED %s x%d -> %s: %s"),
					*Haul.CarryItemId.ToString(),
					Haul.CarryCount,
					*Haul.MachineStationId.ToString(), *Reason);
			}
	}
}

int32 ALBSpacecraftDroneFleetAuthority::HaulLoadFor(
	ELBSpacecraftItemCategory Category, int32 Capacity)
{
	// Only the ASSEMBLED component is one-per-trip: it is the part the
	// line fits and the one the owner watches go by. Sub-parts feed the
	// fabricator cells in crates, so the fabrication chain keeps the
	// pace its tests were tuned to.
	const bool bBigPart =
		Category == ELBSpacecraftItemCategory::AssembledComponent;
	return bBigPart ? 1 : FMath::Max(Capacity, 1);
}

bool ALBSpacecraftDroneFleetAuthority::HaulIsLoaded(
	const FLBSpacecraftHaulState& Haul)
{
	if (Haul.CarryCount <= 0)
	{
		return false;
	}
	return Haul.Job == ELBSpacecraftHaulJob::DeliverInput
		? Haul.Phase == ELBSpacecraftHaulPhase::ToMachine
		: Haul.Phase == ELBSpacecraftHaulPhase::ToStore;
}

void ALBSpacecraftDroneFleetAuthority::TickHauls(double DeltaSeconds,
	ALBSpacecraftCraftingAuthority* InCrafting,
	ALBSpacecraftInventoryAuthority* InInventory,
	const ALBSpacecraftBuildAuthority* InBuild,
	ALBSpacecraftPowerAuthority* InPower)
{
	if (DeltaSeconds <= 0.0 || InCrafting == nullptr
		|| InInventory == nullptr)
	{
		return;
	}
	const float HaulDrainRate = FlightSecondsPerCharge > 0.f
		? 1.f / FlightSecondsPerCharge : 1.f;
	const float HaulChargeRate = ChargeSecondsPerCharge > 0.f
		? 1.f / ChargeSecondsPerCharge : 1.f;
	for (FLBSpacecraftHaulState& Haul : Hauls)
	{
		// THE BATTERY (owner 2026-09-02: "ours will go to their dock
		// and charge"). Flight drains; the pad at home refills, drawing
		// the same grid load a crew dock does when a grid is present
		// (a rig without one charges freely - the honest-grid rule is
		// about a grid that exists and has no headroom). A hauler
		// finishes the run it is on - cargo never strands - and sits
		// out from the reserve until it is fit to launch.
		const FName HaulLoadId(*FString::Printf(TEXT("HaulCharge.%s"),
			*Haul.RackStationId.ToString()));
		if (Haul.Phase != ELBSpacecraftHaulPhase::Idle)
		{
			Haul.Charge01 = FMath::Max(0.f, Haul.Charge01
				- HaulDrainRate * static_cast<float>(DeltaSeconds));
		}
		else
		{
			if (Haul.Charge01 < ReserveFraction)
			{
				Haul.bCharging = true;
			}
			if (Haul.bCharging)
			{
				bool bPowered = InPower == nullptr
					|| ConnectedChargeLoads.Contains(HaulLoadId);
				if (!bPowered)
				{
					FString ChargeReason;
					bPowered = InPower->ConnectLoad(HaulLoadId,
						DockChargeKw, ChargeReason);
					if (bPowered)
					{
						ConnectedChargeLoads.Add(HaulLoadId);
					}
				}
				if (bPowered)
				{
					Haul.Charge01 = FMath::Min(1.f, Haul.Charge01
						+ HaulChargeRate
							* static_cast<float>(DeltaSeconds));
				}
				if (Haul.Charge01 >= LaunchFraction)
				{
					Haul.bCharging = false;
					if (ConnectedChargeLoads.Remove(HaulLoadId) > 0
						&& InPower != nullptr)
					{
						FString Ignored;
						InPower->DisconnectLoad(HaulLoadId, Ignored);
					}
				}
			}
		}
		switch (Haul.Phase)
		{
		case ELBSpacecraftHaulPhase::Idle:
		{
			using namespace LBSpacecraftHaulPrivate;
			if (Haul.bCharging)
			{
				break; // on the pad until fit to fly
			}
			// FEEDING THE LINE COMES FIRST. A station that runs dry
			// stops, so topping up a stockpile outranks clearing a
			// machine's output buffer.
			const FName RackStore =
				SpacecraftHaulStoreOf(Haul.RackStationId);
			FName WantStation;
			FName WantItem;
			FName WantSource;
			int32 WantRoom = 0;
			// Where a hauler may draw from, in order: its OWN rack,
			// then the delivery docks where bought goods land, then
			// the site overflow yard. Drawing from the docks is also
			// what keeps them clear - a backed-up dock refuses new
			// orders.
			TArray<FName> Sources;
			Sources.Add(SpacecraftHaulStoreOf(Haul.RackStationId));
			if (InBuild != nullptr)
			{
				for (const FLBSpacecraftStationRecord& Dock :
					InBuild->GetStations())
				{
					if (Dock.DefinitionId == FName(TEXT("DeliveryDock")))
					{
						Sources.Add(SpacecraftHaulStoreOf(Dock.StationId));
					}
				}
				// EVERY rack, not just this hauler's own. The storage
				// zone is shared (owner: dock -> storage -> stations);
				// with own-rack-only sources each hauler ran a private
				// economy, and parts another hauler had racked were
				// invisible - the self-feeding factory stalled with
				// the missing FrameRibs sitting in the other rack.
				for (const FLBSpacecraftStationRecord& Rack :
					InBuild->GetStations())
				{
					if (Rack.DefinitionId == FName(TEXT("StorageRack")))
					{
						Sources.AddUnique(
							SpacecraftHaulStoreOf(Rack.StationId));
					}
				}
			}
			Sources.Add(ALBSpacecraftGameMode::SiteOverflowStoreId());
			// WHAT IS NEEDED NOW BEFORE WHAT WOULD BE NICE (transporter
			// pass, 2026-09-02). With one big part per trip, a scan that
			// topped the first shelf's first item up to target before
			// looking at anything else left the head station's kit three
			// trips from complete while its float grew. Pass 0 takes
			// only shelves below ONE cycle's need; pass 1 the top-ups.
			for (int32 Pass = 0; Pass < 2 && WantStation.IsNone()
				&& InBuild != nullptr; ++Pass)
			{
				TArray<FLBSpacecraftShelfWant> Wanted;
				for (const FLBSpacecraftStationRecord& Record :
					InBuild->GetStations())
				{
					const FName Stockpile =
						SpacecraftHaulStoreOf(Record.StationId);
					if (Record.StationId == Haul.RackStationId
						|| !InInventory->HasStore(Stockpile))
					{
						continue;
					}
					SpacecraftHaulRequirementsOf(Record, InCrafting,
						StockpileTopUpUnits, Wanted);
					for (const FLBSpacecraftShelfWant& Want : Wanted)
					{
						const FName ItemId = Want.ItemId;
						const int32 OnHand =
							InInventory->GetQuantity(Stockpile, ItemId);
						if (!StockpileWantsItem(OnHand, Want.TargetUnits))
						{
							continue;
						}
						const bool bUrgent = OnHand < Want.OneCycleUnits;
						if ((Pass == 0) != bUrgent)
						{
							continue;
						}
						// ONE hauler per (station, item). Both haulers
						// used to plan the same want in the same tick
						// and both flew it - each delivery overshot,
						// and with reclaim in play the pair oscillated
						// one LightAlloy between two starving machines
						// 5252 times while the ore never moved. The
						// haulers do not coordinate; this check is the
						// coordination.
						bool bAlreadyFlying = false;
						for (const FLBSpacecraftHaulState& OtherHaul :
							Hauls)
						{
							if (&OtherHaul != &Haul
								&& OtherHaul.Phase
									!= ELBSpacecraftHaulPhase::Idle
								&& OtherHaul.Job
									== ELBSpacecraftHaulJob::DeliverInput
								&& OtherHaul.MachineStationId
									== Record.StationId
								&& OtherHaul.CarryItemId == ItemId)
							{
								bAlreadyFlying = true;
								break;
							}
						}
						if (bAlreadyFlying)
						{
							continue;
						}
						// Bring only the SHORTFALL. Carrying a full
						// load regardless overshoots the target, and a
						// shelf sized to hold the target of everything
						// then fills with whatever was fetched first -
						// leaving no room for the one part the station
						// is actually waiting on. That is a deadlock,
						// and it is how the line stopped after five
						// craft with a 94/96 shelf and no Interior.
						const int32 Shortfall =
							FMath::Max(Want.TargetUnits - OnHand, 0);
						if (Shortfall < 1)
						{
							continue;
						}
						// Only promise what can actually be
						// supplied - a hauler never flies for
						// nothing. The rack first, then the site
						// overflow yard where deliveries land.
						// The stockpile must have ROOM for whole
						// items. Capacity is counted in units and a
						// component is several units, so a hauler that
						// loads by item count can arrive with more
						// than fits - and Transfer refuses whole, which
						// silently loses the run.
						const int32 Room = InInventory->GetRoomForItems(
							Stockpile, ItemId);
						if (Room < 1)
						{
							continue;
						}
						FName From;
						int32 Available = 0;
						for (const FName& Candidate : Sources)
						{
							Available = InInventory->GetQuantity(
								Candidate, ItemId);
							if (Available >= 1)
							{
								From = Candidate;
								break;
							}
						}
						if (From.IsNone() && OnHand < Want.OneCycleUnits)
						{
							// RECLAIM. With single-producer
							// intermediates the site can deadlock: the
							// FrameStock mill starves on LightAlloy
							// while every unit of it sits on shelves
							// of machines that are themselves waiting
							// for FrameStock - found by the
							// self-feeding factory test, and no amount
							// of production float fixes it, the wall
							// just moves. So a machine's shelf is a
							// legal source for whatever EXCEEDS its
							// own one-cycle need (all of it, once its
							// order is done). Both ends are one-cycle
							// bounded: reclaim fires only when the
							// taker is below ONE cycle's need and
							// brings at most up to it. The first
							// version topped takers up to their whole
							// multi-cycle target, and two starving
							// machines ping-ponged the same units
							// through both haulers - crafting
							// collapsed from 225 cycles to 20. With
							// both bounds the moves are monotone: a
							// shelf drained to one cycle stops being a
							// source, a taker filled to one cycle
							// stops taking.
							for (const FLBSpacecraftStationRecord&
								Other : InBuild->GetStations())
							{
								if (Other.StationId == Record.StationId)
								{
									continue;
								}
								const FLBSpacecraftItemRecipe*
									OtherRecipe =
									InCrafting->GetSelectedRecipe(
										Other.StationId);
								const FName OtherShelf =
									SpacecraftHaulStoreOf(
										Other.StationId);
								if (OtherRecipe == nullptr
									|| !InInventory->HasStore(OtherShelf))
								{
									continue;
								}
								int32 OneCycleNeed = 0;
								if (InCrafting->GetOrderRemaining(
									Other.StationId) > 0)
								{
									for (const FLBSpacecraftItemStack&
										In : OtherRecipe->Inputs)
									{
										if (In.ItemId == ItemId)
										{
											OneCycleNeed = In.Count;
											break;
										}
									}
								}
								const int32 Excess =
									InInventory->GetQuantity(OtherShelf,
										ItemId) - OneCycleNeed;
								if (Excess >= 1)
								{
									From = OtherShelf;
									Available = FMath::Min(Excess,
										Want.OneCycleUnits - OnHand);
#if !UE_BUILD_SHIPPING
									UE_LOG(LogTemp, Display,
										TEXT("HAUL RECLAIM %s x%d %s ")
										TEXT("-> %s"),
										*ItemId.ToString(), Available,
										*Other.StationId.ToString(),
										*Record.StationId.ToString());
#endif
									break;
								}
							}
						}
						if (From.IsNone())
						{
							continue;
						}
						WantStation = Record.StationId;
						WantItem = ItemId;
						WantSource = From;
						WantRoom = FMath::Min3(Room, Shortfall,
							Available);
						break;
					}
					if (!WantStation.IsNone())
					{
						break;
					}
				}
			}
			if (!WantStation.IsNone())
			{
				Haul.Job = ELBSpacecraftHaulJob::DeliverInput;
				Haul.MachineStationId = WantStation;
				Haul.CarryItemId = WantItem;
				Haul.SourceStoreId = WantSource;
				// Which station's store that is - the pickup leg flies
				// there when it is not home. The yard has no station.
				Haul.SourceStationId = NAME_None;
				if (InBuild != nullptr)
				{
					for (const FLBSpacecraftStationRecord& SourceRecord :
						InBuild->GetStations())
					{
						if (SpacecraftHaulStoreOf(SourceRecord.StationId)
							== WantSource)
						{
							Haul.SourceStationId = SourceRecord.StationId;
							break;
						}
					}
				}
				const FLBSpacecraftItemDefinition* WantRow =
					FLBSpacecraftItemCatalogue::FindItem(WantItem);
				const int32 Load = HaulLoadFor(WantRow != nullptr
					? WantRow->Category : ELBSpacecraftItemCategory::Raw,
					HaulCapacity);
				Haul.CarryCount = FMath::Min3(Load, WantRoom,
					InInventory->GetQuantity(WantSource, WantItem));
				const bool bFromHome = Haul.SourceStationId.IsNone()
					|| Haul.SourceStationId == Haul.RackStationId;
				Haul.Phase = bFromHome ? ELBSpacecraftHaulPhase::ToMachine
					: ELBSpacecraftHaulPhase::ToSource;
				Haul.PhaseSeconds = 0.f;
				break;
			}
			// A DOCK'S hauler never collects: machine output landing in
			// the dock would fill the one store bought goods arrive in,
			// and a backed-up dock refuses new orders.
			if (InBuild != nullptr)
			{
				if (const FLBSpacecraftStationRecord* Host
					= InBuild->FindStation(Haul.RackStationId))
				{
					if (Host->DefinitionId == FName(TEXT("DeliveryDock")))
					{
						break;
					}
				}
			}
			const FName Machine =
				InCrafting->FindStationWithBufferedOutput();
			if (!Machine.IsNone())
			{
				Haul.Job = ELBSpacecraftHaulJob::CollectOutput;
				Haul.CarryItemId = NAME_None;
				Haul.MachineStationId = Machine;
				Haul.Phase = ELBSpacecraftHaulPhase::ToMachine;
				Haul.PhaseSeconds = 0.f;
				Haul.CarryCount = 0;
			}
			break;
		}
		case ELBSpacecraftHaulPhase::ToSource:
			// Empty, home to the store the goods sit in. The goods
			// themselves move only at the drop, atomically, so a save
			// taken anywhere on the trip loses nothing.
			Haul.PhaseSeconds += static_cast<float>(DeltaSeconds);
			if (Haul.PhaseSeconds >= HaulTravelSeconds)
			{
				Haul.Phase = ELBSpacecraftHaulPhase::ToMachine;
				Haul.PhaseSeconds = 0.f;
			}
			break;
		case ELBSpacecraftHaulPhase::ToMachine:
			Haul.PhaseSeconds += static_cast<float>(DeltaSeconds);
			if (Haul.PhaseSeconds >= HaulTravelSeconds)
			{
				if (Haul.Job != ELBSpacecraftHaulJob::DeliverInput)
				{
					// The hook shows what waits; the transfer itself is
					// atomic at the store so a save loses nothing.
					Haul.CarryCount = FMath::Min(HaulCapacity,
						InCrafting->GetBufferCount(
							Haul.MachineStationId));
				}
				else
				{
					// THE DROP HAPPENS WHERE THE DRONE IS (transporter
					// pass, 2026-09-02): a delivery used to land in the
					// station's store when the hauler was back HOME,
					// and read on screen as a collection. It lands on
					// arrival now; the way back is empty.
					LBSpacecraftHaulPrivate::SpacecraftHaulDropDelivery(
						Haul, InCrafting, InInventory, InBuild,
						StockpileTopUpUnits);
					Haul.CarryCount = 0;
				}
				Haul.Phase = ELBSpacecraftHaulPhase::ToStore;
				Haul.PhaseSeconds = 0.f;
			}
			break;
		case ELBSpacecraftHaulPhase::ToStore:
			Haul.PhaseSeconds += static_cast<float>(DeltaSeconds);
			if (Haul.PhaseSeconds >= HaulTravelSeconds)
			{
				using namespace LBSpacecraftHaulPrivate;
				const FName RackStore =
					SpacecraftHaulStoreOf(Haul.RackStationId);
				if (Haul.Job != ELBSpacecraftHaulJob::DeliverInput)
				{
					int32 Moved = 0;
					FString Reason;
					// Output goes into THIS HAULER'S OWN RACK, which
					// is what a rack is for. It used to go to one
					// global "Store.Floor", so a rack you built held
					// nothing and meant nothing.
					InCrafting->TransferBufferToStore(
						Haul.MachineStationId, *InInventory, RackStore,
						HaulCapacity, Moved, Reason);
					if (Moved == 0)
					{
						// The rack is full or absent: SPILL to the site
						// overflow yard rather than jam the machine.
						// Goods always have somewhere to be.
						InCrafting->TransferBufferToStore(
							Haul.MachineStationId, *InInventory,
							ALBSpacecraftGameMode::SiteOverflowStoreId(),
							HaulCapacity, Moved, Reason);
					}
				}
				// Full store keeps the rest buffered: retry from Idle;
				// the machine's own stall names the jam either way.
				Haul.Phase = ELBSpacecraftHaulPhase::Idle;
				Haul.PhaseSeconds = 0.f;
				Haul.CarryCount = 0;
				Haul.MachineStationId = NAME_None;
				Haul.CarryItemId = NAME_None;
				Haul.SourceStoreId = NAME_None;
				Haul.Job = ELBSpacecraftHaulJob::CollectOutput;
			}
			break;
		}
	}
}

float ALBSpacecraftDroneFleetAuthority::GetMissionAlpha01(
	const FLBSpacecraftDroneState& Drone, float InTravelSeconds,
	float InPickupSeconds, float InFittingBurstSeconds)
{
	float Duration = InTravelSeconds;
	switch (Drone.Mission)
	{
	case ELBSpacecraftDroneMission::Pickup:
		Duration = InPickupSeconds;
		break;
	case ELBSpacecraftDroneMission::Fitting:
		Duration = InFittingBurstSeconds;
		break;
	case ELBSpacecraftDroneMission::Docked:
		return 0.f;
	default:
		break;
	}
	return Duration > 0.f
		? FMath::Clamp(Drone.MissionSeconds / Duration, 0.f, 1.f) : 1.f;
}

void ALBSpacecraftDroneFleetAuthority::TickFleet(double DeltaSeconds,
	const ALBSpacecraftCraftingAuthority* InCrafting,
	ALBSpacecraftPowerAuthority* InPower,
	const ALBSpacecraftRuntimeCoordinator* InCoordinator)
{
	if (DeltaSeconds <= 0.0)
	{
		return;
	}
	// A route station PROCESSING a unit is working too - the fitting
	// crew flies for the ship, not only for crafting recipes.
	TSet<FName> BusyRouteStations;
	if (InCoordinator != nullptr && InCoordinator->IsConfigured())
	{
		const TArray<FLBSpacecraftRouteStep>& Route =
			InCoordinator->GetRoute();
		for (const FLBSpacecraftRuntimeAssignment& Assignment :
			InCoordinator->GetAssignments())
		{
			if (Route.IsValidIndex(Assignment.RouteIndex))
			{
				BusyRouteStations.Add(
					Route[Assignment.RouteIndex].StationId);
			}
		}
	}
	// Which station, if any, is hosting the inspection sweep - its crew
	// flies the scan instead of the fitting cycle.
	FName InspectionStationId;
	if (InCoordinator != nullptr)
	{
		FName SweepUnit;
		float SweepProgress = 0.f;
		int32 SweepFound = 0;
		InCoordinator->GetInspectionSweep(SweepUnit, InspectionStationId,
			SweepProgress, SweepFound);
	}
	const float DrainRate = FlightSecondsPerCharge > 0.f
		? 1.f / FlightSecondsPerCharge : 1.f;
	const float ChargeRate = ChargeSecondsPerCharge > 0.f
		? 1.f / ChargeSecondsPerCharge : 1.f;
	for (FLBSpacecraftDroneState& Drone : Drones)
	{
		const bool bStationWorking = (InCrafting != nullptr
			&& InCrafting->GetSelectedRecipe(Drone.StationId) != nullptr)
			|| BusyRouteStations.Contains(Drone.StationId);
		if (Drone.bFlying)
		{
			Drone.Charge01 = FMath::Max(0.f,
				Drone.Charge01 - DrainRate
					* static_cast<float>(DeltaSeconds));
			Drone.MissionSeconds += static_cast<float>(DeltaSeconds);
			// The battery outranks the job: at reserve the drone breaks
			// off for its dock from ANY phase. Work stopping does the
			// same - the sortie ends, it does not freeze mid-air.
			if (Drone.Charge01 <= ReserveFraction || !bStationWorking)
			{
				if (Drone.Mission != ELBSpacecraftDroneMission::ToDock)
				{
					Drone.Mission = ELBSpacecraftDroneMission::ToDock;
					Drone.MissionSeconds = 0.f;
				}
			}
			// Advance the autonomous sortie.
			switch (Drone.Mission)
			{
			case ELBSpacecraftDroneMission::ToSupply:
				if (Drone.MissionSeconds >= TravelSeconds)
				{
					Drone.Mission = ELBSpacecraftDroneMission::Pickup;
					Drone.MissionSeconds = 0.f;
				}
				break;
			case ELBSpacecraftDroneMission::Pickup:
				if (Drone.MissionSeconds >= PickupSeconds)
				{
					Drone.Mission = ELBSpacecraftDroneMission::ToStation;
					Drone.MissionSeconds = 0.f;
				}
				break;
			case ELBSpacecraftDroneMission::ToStation:
				if (Drone.MissionSeconds >= TravelSeconds)
				{
					// At the station hosting the sweep the crew
					// inspects rather than fits - there is nothing
					// left to fit, the craft is finished.
					Drone.Mission = !InspectionStationId.IsNone()
						&& Drone.StationId == InspectionStationId
							? ELBSpacecraftDroneMission::Inspecting
							: ELBSpacecraftDroneMission::Fitting;
					Drone.MissionSeconds = 0.f;
				}
				break;
			case ELBSpacecraftDroneMission::Inspecting:
				// The sweep lasts as long as the scan does. No timer
				// of its own: when the craft leaves Testing the
				// station stops being busy and the sortie ends through
				// the same path that ends every other one.
				if (InspectionStationId.IsNone()
					|| Drone.StationId != InspectionStationId)
				{
					Drone.Mission = ELBSpacecraftDroneMission::ToDock;
					Drone.MissionSeconds = 0.f;
				}
				break;
			case ELBSpacecraftDroneMission::Fitting:
				if (Drone.MissionSeconds >= FittingBurstSeconds)
				{
					// Burst done: fly for the next part.
					Drone.Mission = ELBSpacecraftDroneMission::ToSupply;
					Drone.MissionSeconds = 0.f;
				}
				break;
			case ELBSpacecraftDroneMission::ToDock:
				if (Drone.MissionSeconds >= TravelSeconds)
				{
					Drone.Mission = ELBSpacecraftDroneMission::Docked;
					Drone.MissionSeconds = 0.f;
					Drone.bFlying = false;
				}
				break;
			default:
				Drone.Mission = ELBSpacecraftDroneMission::ToDock;
				Drone.MissionSeconds = 0.f;
				break;
			}
			continue;
		}
		// Docked. Charge if not full - the dock draws REAL grid power,
		// and a grid without headroom charges nothing.
		const FName LoadId =
			MakeChargeLoadId(Drone.StationId, Drone.DroneIndex);
		if (Drone.Charge01 < 1.f)
		{
			bool bPowered = ConnectedChargeLoads.Contains(LoadId);
			if (!bPowered && InPower != nullptr)
			{
				FString Reason;
				bPowered = InPower->ConnectLoad(LoadId, DockChargeKw,
					Reason);
				if (bPowered)
				{
					ConnectedChargeLoads.Add(LoadId);
				}
			}
			if (bPowered)
			{
				Drone.Charge01 = FMath::Min(1.f,
					Drone.Charge01 + ChargeRate
						* static_cast<float>(DeltaSeconds));
			}
		}
		if (Drone.Charge01 >= 1.f
			&& ConnectedChargeLoads.Contains(LoadId))
		{
			DisconnectChargeLoad(Drone.StationId, Drone.DroneIndex,
				InPower);
		}
		// Launch only with a healthy battery.
		if (bStationWorking && Drone.Charge01 >= LaunchFraction)
		{
			DisconnectChargeLoad(Drone.StationId, Drone.DroneIndex,
				InPower);
			Drone.bFlying = true;
			Drone.Mission = ELBSpacecraftDroneMission::ToSupply;
			Drone.MissionSeconds = 0.f;
		}
	}
}

const FLBSpacecraftDroneState* ALBSpacecraftDroneFleetAuthority::FindDrone(
	FName StationId, int32 DroneIndex) const
{
	for (const FLBSpacecraftDroneState& Drone : Drones)
	{
		if (Drone.StationId == StationId
			&& Drone.DroneIndex == DroneIndex)
		{
			return &Drone;
		}
	}
	return nullptr;
}

int32 ALBSpacecraftDroneFleetAuthority::GetFlyingCount() const
{
	int32 Count = 0;
	for (const FLBSpacecraftDroneState& Drone : Drones)
	{
		Count += Drone.bFlying ? 1 : 0;
	}
	return Count;
}

FLBSpacecraftDroneFleetSnapshot
ALBSpacecraftDroneFleetAuthority::CaptureSnapshot() const
{
	FLBSpacecraftDroneFleetSnapshot Snapshot;
	Snapshot.Drones = Drones;
	return Snapshot;
}

bool ALBSpacecraftDroneFleetAuthority::ValidateSnapshot(
	const FLBSpacecraftDroneFleetSnapshot& Snapshot, FString& OutReason)
{
	TSet<FName> Seen;
	for (const FLBSpacecraftDroneState& Drone : Snapshot.Drones)
	{
		// The cap is the WIDEST crew any station class can hold, read
		// from the catalogue. It used to be a literal 1, from when
		// every station carried exactly two fitting drones - once line
		// stations grew eight slots (owner 2026-08-26, the worker-slot
		// model) that literal refused the WHOLE save the moment a
		// player bought a third drone anywhere on the floor.
		static const int32 MaxCrewIndex = []()
		{
			int32 Widest = 0;
			for (const FLBSpacecraftStationDefinition& Definition :
				ALBSpacecraftBuildAuthority::StationCatalogue())
			{
				Widest = FMath::Max(Widest, Definition.DroneSlotCount);
			}
			return FMath::Max(Widest, 2) - 1;
		}();
		if (Drone.StationId.IsNone() || Drone.DroneIndex < 0
			|| Drone.DroneIndex > MaxCrewIndex)
		{
			OutReason = TEXT("SNAPSHOT DRONE IS MALFORMED");
			return false;
		}
		if (Drone.Charge01 < 0.f || Drone.Charge01 > 1.f)
		{
			OutReason = TEXT("SNAPSHOT DRONE HAS AN IMPOSSIBLE CHARGE");
			return false;
		}
		const FName Key = MakeChargeLoadId(Drone.StationId,
			Drone.DroneIndex);
		if (Seen.Contains(Key))
		{
			OutReason = TEXT("SNAPSHOT DUPLICATES A DRONE");
			return false;
		}
		Seen.Add(Key);
	}
	OutReason = TEXT("SNAPSHOT VALID");
	return true;
}

bool ALBSpacecraftDroneFleetAuthority::RestoreSnapshot(
	const FLBSpacecraftDroneFleetSnapshot& Snapshot,
	ALBSpacecraftPowerAuthority* InPower, FString& OutReason)
{
	// Hauls are derived, never saved: reset to Idle; every buffered
	// item is already safe in the crafting snapshot.
	for (FLBSpacecraftHaulState& Haul : Hauls)
	{
		Haul.Phase = ELBSpacecraftHaulPhase::Idle;
		Haul.PhaseSeconds = 0.f;
		Haul.CarryCount = 0;
		Haul.MachineStationId = NAME_None;
	}
	// Whole-snapshot validation BEFORE a single mutation (repo law).
	if (!ValidateSnapshot(Snapshot, OutReason))
	{
		return false;
	}
	// Our live charge loads belong to the OLD state: release them all;
	// the restored fleet reconnects what it needs on its next tick.
	if (InPower != nullptr)
	{
		for (const FName& LoadId : ConnectedChargeLoads)
		{
			FString Ignored;
			InPower->DisconnectLoad(LoadId, Ignored);
		}
	}
	ConnectedChargeLoads.Reset();
	// Review fix (critical): a save taken while docks were charging
	// restores those DroneCharge loads inside the POWER snapshot. Adopt
	// them back into this authority's ownership set, or they become
	// phantom draws no path can ever release and the drones never
	// charge again.
	if (InPower != nullptr)
	{
		for (const FLBSpacecraftDroneState& Drone : Drones)
		{
			const FName LoadId =
				MakeChargeLoadId(Drone.StationId, Drone.DroneIndex);
			if (InPower->HasLoad(LoadId))
			{
				ConnectedChargeLoads.Add(LoadId);
			}
		}
	}
	Drones = Snapshot.Drones;
	OutReason = TEXT("DRONE FLEET RESTORED");
	return true;
}
