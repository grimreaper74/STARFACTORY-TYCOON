#include "LBSpacecraftResearchAuthority.h"

#include "LBSpacecraftBuildAuthority.h"
#include "LBSpacecraftCraftingAuthority.h"
#include "LBSpacecraftProductionAuthority.h"


namespace LBSpacecraftResearchPrivate
{
	// Unity-build safety: helpers qualified by subject.
	FLBSpacecraftResearchNode MakeResearchNode(const TCHAR* Id,
		const TCHAR* Display, int32 CostPoints,
		std::initializer_list<const TCHAR*> Prerequisites,
		std::initializer_list<const TCHAR*> StationClasses)
	{
		FLBSpacecraftResearchNode Node;
		Node.NodeId = FName(Id);
		Node.DisplayName = Display;
		Node.Branch = FName(TEXT("Manufacturing"));
		Node.CostPoints = CostPoints;
		for (const TCHAR* Prerequisite : Prerequisites)
		{
			Node.Prerequisites.Add(FName(Prerequisite));
		}
		for (const TCHAR* StationClass : StationClasses)
		{
			Node.UnlockedStationClasses.Add(FName(StationClass));
		}
		return Node;
	}

	/** A node that opens CREW KINDS rather than station families. */
	FLBSpacecraftResearchNode MakeCrewResearchNode(const TCHAR* Id,
		const TCHAR* Display, int32 CostPoints,
		std::initializer_list<const TCHAR*> Prerequisites,
		std::initializer_list<const TCHAR*> DroneKinds)
	{
		FLBSpacecraftResearchNode Node =
			MakeResearchNode(Id, Display, CostPoints, Prerequisites, {});
		Node.Branch = FName(TEXT("Crew"));
		for (const TCHAR* KindId : DroneKinds)
		{
			Node.UnlockedDroneKinds.Add(FName(KindId));
		}
		return Node;
	}

	TArray<FLBSpacecraftResearchNode> BuildManufacturingBranch()
	{
		TArray<FLBSpacecraftResearchNode> Table;
		// Four tiers per the owner's plan; each opens the next rung of the
		// Phase-2 chain the crafting seam introduced.
		Table.Add(MakeResearchNode(TEXT("Research.Mfg.T1"),
			TEXT("Basic Fabrication"), 10, {},
			{TEXT("RollingMill"), TEXT("CircuitFab")}));
		Table.Add(MakeResearchNode(TEXT("Research.Mfg.T2"),
			TEXT("Powered Assembly"), 25, {TEXT("Research.Mfg.T1")},
			{TEXT("PowerCellPlant"), TEXT("ElectronicsStation")}));
		Table.Add(MakeResearchNode(TEXT("Research.Mfg.T3"),
			TEXT("Propulsion Works"), 50, {TEXT("Research.Mfg.T2")},
			{TEXT("PropulsionStation")}));
		Table.Add(MakeResearchNode(TEXT("Research.Mfg.T4"),
			TEXT("Robotic Sub-Assembly"), 80, {TEXT("Research.Mfg.T3")},
			{TEXT("SubAssemblyRobot")}));
		// THE PARTS UPGRADE, SPLIT THREE WAYS (2026-09-03). It used to
		// be one 100-point node that handed over all nine bigger marks
		// at once - the most expensive thing in the tree and the least
		// interesting, because there was nothing to decide: you saved
		// up, you bought it, your whole parts floor upgraded. Split by
		// what the machines actually make, each node is affordable on
		// its own and the player upgrades the part of their factory
		// that is ACTUALLY their bottleneck first. Same nine marks,
		// same total ballpark, three real decisions instead of none.
		// The bigger YARD RACK rides with the heavy stock machinery:
		// the node is about handling materials at scale, and a yard
		// that cannot hold what the bigger mills eat is the same
		// bottleneck seen from the other end.
		Table.Add(MakeResearchNode(TEXT("Research.Mfg.HeavyStock"),
			TEXT("Heavy Stock Machinery"), 30,
			{TEXT("Research.Mfg.T4")},
			{TEXT("RollingMillMk2"), TEXT("SmelterMk2"),
				TEXT("StructureFabMk2"), TEXT("StorageRackMk2")}));
		Table.Add(MakeResearchNode(TEXT("Research.Mfg.HeavyElectronics"),
			TEXT("Heavy Electronics"), 30,
			{TEXT("Research.Mfg.T4")},
			{TEXT("CircuitFabMk2"), TEXT("ElectronicsStationMk2"),
				TEXT("PowerCellPlantMk2")}));
		Table.Add(MakeResearchNode(TEXT("Research.Mfg.HeavyPropulsion"),
			TEXT("Heavy Propulsion and Fit-out"), 30,
			{TEXT("Research.Mfg.T4")},
			{TEXT("PropulsionStationMk2"), TEXT("FitOutFabMk2"),
				TEXT("SubAssemblyRobotMk2")}));
		// Mark upgrades: the Mk2 route stations that hold Cargo-tier craft.
		Table.Add(MakeResearchNode(TEXT("Research.Mfg.Mk2"),
			TEXT("Heavy Station Marks"), 60, {TEXT("Research.Mfg.T2")},
			{TEXT("MaterialProcessorMk2"), TEXT("HullFabricatorMk2"),
				TEXT("ComponentFabricatorMk2"), TEXT("AssemblyRobotMk2")}));

		// THE CREW BRANCH (2026-09-03). Seven drone kinds shipped -
		// quality weights from the winch's rough 0.6 to the ground
		// sprayer's 1.7, each at its own price - and every one was
		// hireable from the first minute, so picking a crew carried no
		// progression at all. They are content like any machine: the
		// plain assembly drone stays free (it is also the fallback
		// every kind-less caller gets), and the SPECIALISTS are earned.
		// This branch hangs off T1 rather than the deep chain so a
		// player has a real choice early: widen what your factory can
		// MAKE, or improve who BUILDS it.
		Table.Add(MakeCrewResearchNode(TEXT("Research.Crew.Specialists"),
			TEXT("Crew Specialisation"), 15, {TEXT("Research.Mfg.T1")},
			{TEXT("Spray"), TEXT("Winch")}));
		Table.Add(MakeCrewResearchNode(TEXT("Research.Crew.HeavyLift"),
			TEXT("Heavy Lift Crew"), 20,
			{TEXT("Research.Crew.Specialists")},
			{TEXT("CargoLift")}));
		// GROUND CREW park on the floor and work the craft's belly -
		// the choreography the fitting stations already draw for them.
		Table.Add(MakeCrewResearchNode(TEXT("Research.Crew.Ground"),
			TEXT("Ground Crew"), 25,
			{TEXT("Research.Crew.Specialists")},
			{TEXT("GroundLifter"), TEXT("GroundAssembly")}));
		Table.Add(MakeCrewResearchNode(TEXT("Research.Crew.Precision"),
			TEXT("Precision Finishing"), 40,
			{TEXT("Research.Crew.Ground")},
			{TEXT("GroundSprayer")}));
		return Table;
	}

	TArray<FName> BuildDefaultStationClasses()
	{
		// The slice's five families need no research (the playable floor),
		// and neither does infrastructure - power and storage must be
		// buildable BEFORE the research that needs them.
		// The POWER STATION joins them (owner 2026-08-26): generators
		// live only inside their hall now, so the hall is the thing
		// the player buys - locking it would lock power itself.
		return {FName(TEXT("MaterialProcessor")),
			FName(TEXT("HullFabricator")),
			FName(TEXT("ComponentFabricator")),
			FName(TEXT("AssemblyRobot")), FName(TEXT("TestingRig")),
			// The SPRAY BOOTH is free for the plainest reason of all:
			// the line REFUSES TO COMMISSION without one (owner
			// 2026-08-28), so locking it behind research points the
			// player can only earn by delivering craft would lock the
			// game behind itself.
			FName(TEXT("SprayBooth")),
			FName(TEXT("PowerPlant")), FName(TEXT("StorageRack")),
			FName(TEXT("PowerStation")),
			FName(TEXT("SubAssemblyHall")),
			// The DELIVERY DOCK is where bought goods arrive, so it
			// cannot sit behind research the player buys with points
			// they can only earn by delivering craft they cannot build
			// without materials.
			FName(TEXT("DeliveryDock")),
			// The three sub-assembly buildings that took the
			// fabrication off the LINE on 2026-08-27 are free for the
			// same reason the delivery dock is: the work they do was
			// previously done by line stations the player already had.
			// Gating them behind research would lock the player out of
			// making steel at all - and research points come from
			// deliveries, which need parts, which need steel.
			FName(TEXT("Smelter")),
			FName(TEXT("StructureFab")),
			FName(TEXT("FitOutFab")),
			// THE SHIP FACTORY is the player's first move on the world
			// map (owner 2026-08-28) - the one building offered before
			// anything else exists. Nothing at all can be built until
			// it stands, so it can never sit behind research.
			FName(TEXT("ShipFactoryHall"))};
	}
}

const TArray<FLBSpacecraftResearchNode>&
FLBSpacecraftResearchCatalogue::GetNodeTable()
{
	static const TArray<FLBSpacecraftResearchNode> Table =
		LBSpacecraftResearchPrivate::BuildManufacturingBranch();
	return Table;
}

const FLBSpacecraftResearchNode* FLBSpacecraftResearchCatalogue::FindNode(
	FName NodeId)
{
	for (const FLBSpacecraftResearchNode& Node : GetNodeTable())
	{
		if (Node.NodeId == NodeId)
		{
			return &Node;
		}
	}
	return nullptr;
}

const TArray<FName>&
FLBSpacecraftResearchCatalogue::GetDefaultStationClasses()
{
	static const TArray<FName> Defaults =
		LBSpacecraftResearchPrivate::BuildDefaultStationClasses();
	return Defaults;
}

const TArray<FName>&
FLBSpacecraftResearchCatalogue::GetDefaultDroneKinds()
{
	// ONE free kind, deliberately. Assembly is the nominal-quality
	// drone and the fallback FindDroneKind hands back for an unknown
	// name, so a factory with no research crews every station to
	// nominal and builds clean craft - nobody is gated out of playing.
	// What research buys is the SPECIALISTS beside it.
	static const TArray<FName> Defaults = {FName(TEXT("Assembly"))};
	return Defaults;
}

bool FLBSpacecraftResearchCatalogue::ValidateNodeTable(FString& OutReason)
{
	const TArray<FLBSpacecraftResearchNode>& Table = GetNodeTable();
	if (Table.Num() == 0)
	{
		OutReason = TEXT("RESEARCH TABLE IS EMPTY");
		return false;
	}
	TSet<FName> SeenIds;
	for (const FLBSpacecraftResearchNode& Node : Table)
	{
		if (Node.NodeId.IsNone() || Node.DisplayName.IsEmpty()
			|| Node.Branch.IsNone())
		{
			OutReason = TEXT("RESEARCH NODE IS MALFORMED");
			return false;
		}
		if (SeenIds.Contains(Node.NodeId))
		{
			OutReason = FString::Printf(TEXT("DUPLICATE RESEARCH NODE %s"),
				*Node.NodeId.ToString());
			return false;
		}
		if (Node.CostPoints <= 0)
		{
			OutReason = FString::Printf(
				TEXT("RESEARCH NODE %s HAS A NON-POSITIVE COST"),
				*Node.NodeId.ToString());
			return false;
		}
		// Prerequisites must already be listed - ordering makes the graph
		// structurally acyclic without a traversal.
		for (const FName& Prerequisite : Node.Prerequisites)
		{
			if (!SeenIds.Contains(Prerequisite))
			{
				OutReason = FString::Printf(
					TEXT("RESEARCH NODE %s NEEDS %s BEFORE IT IN THE TABLE"),
					*Node.NodeId.ToString(), *Prerequisite.ToString());
				return false;
			}
		}
		SeenIds.Add(Node.NodeId);
		// CONTENT ONLY, still: a node must hand over something that
		// EXISTS to build or hire. Crew kinds count as content for the
		// same reason machines do - what changes is what the player
		// can choose from, never a multiplier behind their back.
		if (Node.UnlockedStationClasses.Num() == 0
			&& Node.UnlockedDroneKinds.Num() == 0)
		{
			OutReason = FString::Printf(
				TEXT("RESEARCH NODE %s UNLOCKS NOTHING - CONTENT ONLY"),
				*Node.NodeId.ToString());
			return false;
		}
		for (const FName& StationClass : Node.UnlockedStationClasses)
		{
			// Every unlocked family must either craft recipes or be a
			// route mark (a catalogue definition servicing a stage); the
			// slice defaults never need researching twice.
			const FLBSpacecraftStationDefinition* Unlocked =
				ALBSpacecraftBuildAuthority::FindDefinition(StationClass);
			const bool bRouteMark =
				Unlocked != nullptr && !Unlocked->StageClassId.IsNone();
			// Ask the RECIPE class, not the id: a bigger parts mark
			// runs the mark below it's recipes rather than carrying a
			// duplicate table, and asking its own id would call it a
			// family that crafts nothing.
			const FName RecipeClass = Unlocked != nullptr
				? Unlocked->GetRecipeClassId() : StationClass;
			// STORAGE COUNTS AS CONTENT TOO (2026-09-03). The rule was
			// written when only crafting families and route marks were
			// unlockable; a bigger yard rack is neither, and crafts
			// nothing, but it is plainly a real thing the player
			// builds. Without this the validator refuses it as
			// "CRAFTS NOTHING" and the node table fails closed.
			const bool bStorage = Unlocked != nullptr
				&& Unlocked->StorageCapacityUnits > 0;
			if (!bRouteMark && !bStorage
				&& FLBSpacecraftRecipeCatalogue::GetRecipesForStationClass(
					RecipeClass).Num() == 0)
			{
				OutReason = FString::Printf(
					TEXT("RESEARCH NODE %s UNLOCKS %s WHICH CRAFTS NOTHING"),
					*Node.NodeId.ToString(), *StationClass.ToString());
				return false;
			}
			if (GetDefaultStationClasses().Contains(StationClass))
			{
				OutReason = FString::Printf(
					TEXT("RESEARCH NODE %s RE-LOCKS A DEFAULT FAMILY"),
					*Node.NodeId.ToString());
				return false;
			}
		}
		// CREW KINDS get the same two checks their station families
		// get: the kind must actually exist in the drone catalogue,
		// and the free kind can never be sold back to the player.
		for (const FName& KindId : Node.UnlockedDroneKinds)
		{
			if (ALBSpacecraftBuildAuthority::FindDroneKind(KindId)
				== nullptr)
			{
				OutReason = FString::Printf(
					TEXT("RESEARCH NODE %s UNLOCKS UNKNOWN CREW KIND %s"),
					*Node.NodeId.ToString(), *KindId.ToString());
				return false;
			}
			if (GetDefaultDroneKinds().Contains(KindId))
			{
				OutReason = FString::Printf(
					TEXT("RESEARCH NODE %s RE-LOCKS THE FREE CREW KIND"),
					*Node.NodeId.ToString());
				return false;
			}
		}
	}
	OutReason = TEXT("RESEARCH TABLE VALID");
	return true;
}

ALBSpacecraftResearchAuthority::ALBSpacecraftResearchAuthority()
{
	PrimaryActorTick.bCanEverTick = false;
}

bool ALBSpacecraftResearchAuthority::AddPoints(int32 Points,
	FString& OutReason)
{
	if (Points <= 0)
	{
		OutReason = TEXT("RESEARCH POINTS MUST BE POSITIVE");
		return false;
	}
	PointsBanked += Points;
	OutReason = FString::Printf(TEXT("%d POINTS BANKED"), PointsBanked);
	return true;
}

bool ALBSpacecraftResearchAuthority::UnlockNode(FName NodeId,
	FString& OutReason)
{
	const FLBSpacecraftResearchNode* Node =
		FLBSpacecraftResearchCatalogue::FindNode(NodeId);
	if (Node == nullptr)
	{
		OutReason = FString::Printf(TEXT("UNKNOWN RESEARCH NODE %s"),
			*NodeId.ToString());
		return false;
	}
	if (UnlockedNodes.Contains(NodeId))
	{
		OutReason = FString::Printf(TEXT("NODE %s IS ALREADY UNLOCKED"),
			*NodeId.ToString());
		return false;
	}
	for (const FName& Prerequisite : Node->Prerequisites)
	{
		if (!UnlockedNodes.Contains(Prerequisite))
		{
			OutReason = FString::Printf(
				TEXT("NODE %s REQUIRES %s FIRST"),
				*NodeId.ToString(), *Prerequisite.ToString());
			return false;
		}
	}
	if (PointsBanked < Node->CostPoints)
	{
		OutReason = FString::Printf(
			TEXT("NODE %s COSTS %d POINTS, %d BANKED - RESEARCH REFUSED"),
			*NodeId.ToString(), Node->CostPoints, PointsBanked);
		return false;
	}
	PointsBanked -= Node->CostPoints;
	UnlockedNodes.Add(NodeId);
	OutReason = FString::Printf(TEXT("UNLOCKED %s"), *NodeId.ToString());
	return true;
}

bool ALBSpacecraftResearchAuthority::IsNodeUnlocked(FName NodeId) const
{
	return UnlockedNodes.Contains(NodeId);
}

bool ALBSpacecraftResearchAuthority::IsStationClassUnlocked(
	FName StationClassId) const
{
	if (FLBSpacecraftResearchCatalogue::GetDefaultStationClasses().Contains(
			StationClassId))
	{
		return true;
	}
	for (const FName& NodeId : UnlockedNodes)
	{
		const FLBSpacecraftResearchNode* Node =
			FLBSpacecraftResearchCatalogue::FindNode(NodeId);
		if (Node != nullptr
			&& Node->UnlockedStationClasses.Contains(StationClassId))
		{
			return true;
		}
	}
	return false;
}

bool ALBSpacecraftResearchAuthority::IsDroneKindUnlocked(
	FName KindId) const
{
	// A KIND-LESS HIRE IS THE PLAIN DRONE. Every existing caller that
	// passes no kind falls back to Assembly downstream, so an empty
	// name must read as unlocked or the whole game stops crewing.
	if (KindId.IsNone()
		|| FLBSpacecraftResearchCatalogue::GetDefaultDroneKinds()
			.Contains(KindId))
	{
		return true;
	}
	for (const FName& NodeId : UnlockedNodes)
	{
		const FLBSpacecraftResearchNode* Node =
			FLBSpacecraftResearchCatalogue::FindNode(NodeId);
		if (Node != nullptr && Node->UnlockedDroneKinds.Contains(KindId))
		{
			return true;
		}
	}
	return false;
}

int32 ALBSpacecraftResearchAuthority::PointsForDeliveredValuePence(
	int64 ValuePence)
{
	if (ValuePence <= 0)
	{
		return 0;
	}
	// PROVISIONAL pacing pending the owner's economy tuning: a Scout
	// delivery teaches 10 points, which is exactly Basic Fabrication -
	// so the first delivery opens the chain rather than the tree
	// sitting dead.
	//
	// Rescaled x3 on 2026-08-27 with the craft price retune. Points are
	// delivered VALUE divided by this, so tripling what a craft sells
	// for would otherwise triple research income and unlock the tree
	// three times faster. The RATE moves with the prices; the intent -
	// one Scout, one first unlock - is what is being held fixed.
	constexpr int64 PencePerPoint = 1500000;
	return static_cast<int32>(ValuePence / PencePerPoint);
}

void ALBSpacecraftResearchAuthority::SyncFromLedger(
	const ALBSpacecraftProductionAuthority* InProduction)
{
	if (InProduction == nullptr)
	{
		return;
	}
	// EVERY DELIVERY TEACHES, not every finished contract. Waiting for
	// a four-craft order to complete meant four ships built and no
	// progression to show for any of them.
	for (const FLBSpacecraftContract& Contract : InProduction->GetContracts())
	{
		const int32 Fresh =
			LBSpacecraftCreditPrivate::SpacecraftClaimNewDeliveries(
				DeliveryCredits, CreditedContracts, Contract);
		if (Fresh > 0)
		{
			PointsBanked += PointsForDeliveredValuePence(
				Contract.PricePerUnitPence * static_cast<int64>(Fresh));
		}
	}
}

FLBSpacecraftResearchSnapshot
ALBSpacecraftResearchAuthority::CaptureSnapshot() const
{
	FLBSpacecraftResearchSnapshot Snapshot;
	Snapshot.Points = PointsBanked;
	Snapshot.UnlockedNodes = UnlockedNodes;
	Snapshot.CreditedContracts = CreditedContracts;
	Snapshot.DeliveryCredits = DeliveryCredits;
	return Snapshot;
}

bool ALBSpacecraftResearchAuthority::ValidateSnapshot(
	const FLBSpacecraftResearchSnapshot& Snapshot, FString& OutReason)
{
	if (Snapshot.Points < 0)
	{
		OutReason = TEXT("SNAPSHOT BANKS NEGATIVE POINTS");
		return false;
	}
	TSet<FName> CreditedSeen;
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
		if (CreditedSeen.Contains(Credit.ContractId))
		{
			OutReason = TEXT("SNAPSHOT CREDITS A CONTRACT TWICE");
			return false;
		}
		CreditedSeen.Add(Credit.ContractId);
	}
	TSet<FName> Seen;
	for (const FName& NodeId : Snapshot.UnlockedNodes)
	{
		const FLBSpacecraftResearchNode* Node =
			FLBSpacecraftResearchCatalogue::FindNode(NodeId);
		if (Node == nullptr)
		{
			OutReason = FString::Printf(
				TEXT("SNAPSHOT UNLOCKS UNKNOWN NODE %s"),
				*NodeId.ToString());
			return false;
		}
		if (Seen.Contains(NodeId))
		{
			OutReason = FString::Printf(
				TEXT("SNAPSHOT DUPLICATES NODE %s"), *NodeId.ToString());
			return false;
		}
		Seen.Add(NodeId);
		// Prerequisite closure: an unlocked node's prerequisites must be
		// in the same snapshot, or the save is corrupt.
		for (const FName& Prerequisite : Node->Prerequisites)
		{
			if (!Snapshot.UnlockedNodes.Contains(Prerequisite))
			{
				OutReason = FString::Printf(
					TEXT("SNAPSHOT UNLOCKS %s WITHOUT ITS PREREQUISITE %s"),
					*NodeId.ToString(), *Prerequisite.ToString());
				return false;
			}
		}
	}
	OutReason = TEXT("SNAPSHOT VALID");
	return true;
}

bool ALBSpacecraftResearchAuthority::RestoreSnapshot(
	const FLBSpacecraftResearchSnapshot& Snapshot, FString& OutReason)
{
	// Whole-snapshot validation BEFORE a single mutation (repo law).
	if (!ValidateSnapshot(Snapshot, OutReason))
	{
		return false;
	}
	PointsBanked = Snapshot.Points;
	UnlockedNodes = Snapshot.UnlockedNodes;
	CreditedContracts = Snapshot.CreditedContracts;
	DeliveryCredits = Snapshot.DeliveryCredits;
	OutReason = TEXT("RESEARCH RESTORED");
	return true;
}
