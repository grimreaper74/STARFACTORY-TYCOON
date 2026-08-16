#include "LBPressShopCampaignController.h"

#include "EngineUtils.h"
#include "Kismet/GameplayStatics.h"
#include "LBControlRoomOperationsConsole.h"
#include "LBBodyWeldLineActor.h"
#include "LBECoatLineActor.h"
#include "LBFactoryConnectionSubsystem.h"
#include "LBFactoryTransportLink.h"
#include "LBFactoryMachineBuilderSubsystem.h"
#include "LBFactoryBrandSubsystem.h"
#include "LBFactoryBuildMachine.h"
#include "LBFactoryManagementSubsystem.h"
#include "LBInboundDeliveryController.h"
#include "LBCoilAGVController.h"
#include "LBPR004Station.h"
#include "LBPR005Station.h"
#include "LBPR006Station.h"
#include "LBPR007Station.h"
#include "LBPR008Station.h"
#include "LBPR009Station.h"
#include "LBPR010Station.h"
#include "LBPressShopSaveGame.h"
#include "LBPressShopBuildAuthority.h"
#include "LBPressShopStorageZone.h"
#include "LBPressShopSupportFleetController.h"
#include "LBPressTrainAStation.h"
#include "LBPressTrainIdentitySubsystem.h"
#include "LBPlayerBuiltPressFlowController.h"
#include "LBSupportCraneController.h"
#include "LBStillageFLTFleetController.h"
#include "LBFactoryAGVInfrastructure.h"

namespace
{
constexpr int32 CurrentCampaignSaveFormat = 18;
constexpr int32 FirstECoatSaveFormat = 15;
constexpr int32 FirstStillageFleetSaveFormat = 16;
constexpr int32 FirstTopologyAndManagementSaveFormat = 17;
constexpr int32 FirstBodyWeldSaveFormat = 18;
constexpr int32 MaximumPersistedStillageFLTs = 8;

// RestoreCampaign recursively replays one already-preflighted snapshot when a
// commit endpoint reports a late failure. The guard makes that replay bounded:
// a failure in the rollback pass is reported to its caller and is never allowed
// to start another restore.
TSet<const ALBPressShopCampaignController*> ActiveCampaignRollbackPasses;

class FScopedCampaignRollbackPass
{
public:
    explicit FScopedCampaignRollbackPass(const ALBPressShopCampaignController* Controller)
        : Controller(Controller)
    {
        ActiveCampaignRollbackPasses.Add(Controller);
    }

    ~FScopedCampaignRollbackPass()
    {
        ActiveCampaignRollbackPasses.Remove(Controller);
    }

private:
    const ALBPressShopCampaignController* Controller = nullptr;
};

template <typename T>
T* FindSingle(UWorld* World)
{
    T* Found = nullptr;
    for (TActorIterator<T> It(World); It; ++It)
    {
        if (!IsValid(*It) || It->IsActorBeingDestroyed()) continue;
        if (Found) return nullptr;
        Found = *It;
    }
    return Found;
}

template <typename T>
int32 CountActors(UWorld* World)
{
    int32 Count = 0;
    for (TActorIterator<T> It(World); It; ++It)
    {
        if (IsValid(*It) && !It->IsActorBeingDestroyed()) ++Count;
    }
    return Count;
}

template <typename T>
void AddManagedActors(UWorld* World, TSet<TWeakObjectPtr<AActor>>& OutActors)
{
    for (TActorIterator<T> It(World); It; ++It)
    {
        if (IsValid(*It) && !It->IsActorBeingDestroyed()) OutActors.Add(*It);
    }
}

template <typename T>
void DestroyIntroducedManagedActors(UWorld* World,
    const TSet<TWeakObjectPtr<AActor>>& PriorActors)
{
    TArray<TWeakObjectPtr<T>> Introduced;
    for (TActorIterator<T> It(World); It; ++It)
    {
        if (IsValid(*It) && !It->IsActorBeingDestroyed()
            && !PriorActors.Contains(TWeakObjectPtr<AActor>(*It)))
        {
            Introduced.Add(*It);
        }
    }
    for (const TWeakObjectPtr<T>& Actor : Introduced)
        if (Actor.IsValid()) Actor->Destroy();
}

void CaptureManagedActorSet(UWorld* World, TSet<TWeakObjectPtr<AActor>>& OutActors)
{
    AddManagedActors<ALBPressTrainAStation>(World, OutActors);
    AddManagedActors<ALBFactoryBuildMachine>(World, OutActors);
    AddManagedActors<ALBBodyWeldLineActor>(World, OutActors);
    AddManagedActors<ALBECoatLineActor>(World, OutActors);
    AddManagedActors<ALBFactoryAGVInfrastructure>(World, OutActors);
    AddManagedActors<ALBPressShopStorageZone>(World, OutActors);
    AddManagedActors<ALBFactoryTransportLink>(World, OutActors);
    AddManagedActors<ALBCompactStillageFLT>(World, OutActors);
    AddManagedActors<ALBPlayerBuiltPressFlowController>(World, OutActors);
}

void DestroyIntroducedManagedActorSet(UWorld* World,
    const TSet<TWeakObjectPtr<AActor>>& PriorActors)
{
    DestroyIntroducedManagedActors<ALBPressTrainAStation>(World, PriorActors);
    DestroyIntroducedManagedActors<ALBFactoryBuildMachine>(World, PriorActors);
    DestroyIntroducedManagedActors<ALBBodyWeldLineActor>(World, PriorActors);
    DestroyIntroducedManagedActors<ALBECoatLineActor>(World, PriorActors);
    DestroyIntroducedManagedActors<ALBFactoryAGVInfrastructure>(World, PriorActors);
    DestroyIntroducedManagedActors<ALBPressShopStorageZone>(World, PriorActors);
    DestroyIntroducedManagedActors<ALBFactoryTransportLink>(World, PriorActors);
    DestroyIntroducedManagedActors<ALBCompactStillageFLT>(World, PriorActors);
    DestroyIntroducedManagedActors<ALBPlayerBuiltPressFlowController>(World, PriorActors);
}

bool IsLegacyDefaultManagementState(const FLBFactoryManagementSaveState& State)
{
    return State.Version == ULBFactoryManagementSubsystem::CurrentSaveVersion
        && !State.bCampaignInitialised && State.Revision == 0
        && State.OpeningCashPence == ULBFactoryManagementSubsystem::DefaultStartingCashPence
        && State.CashBalancePence == ULBFactoryManagementSubsystem::DefaultStartingCashPence
        && State.OpeningResearchPoints == 0 && State.AvailableResearchPoints == 0
        && State.TotalResearchEarnedPoints == 0 && State.TotalResearchSpentPoints == 0
        && State.NextLedgerSequence == 1 && State.LedgerEntries.IsEmpty()
        && State.CapitalAssets.IsEmpty() && State.ResearchGrants.IsEmpty()
        && State.ResearchUnlocks.IsEmpty() && State.MachineUpgrades.IsEmpty()
        && State.QualityRecords.IsEmpty() && State.MaintenanceRecords.IsEmpty()
        && State.AnalyticsBuckets.IsEmpty() && State.AppliedEventIds.IsEmpty();
}

FLBFactoryManagementSaveState BuildFreshMigratedManagementState()
{
    FLBFactoryManagementSaveState State;
    State.Version = ULBFactoryManagementSubsystem::CurrentSaveVersion;
    State.bCampaignInitialised = true;
    State.Revision = 1;
    State.OpeningCashPence = ULBFactoryManagementSubsystem::DefaultStartingCashPence;
    State.CashBalancePence = ULBFactoryManagementSubsystem::DefaultStartingCashPence;
    State.OpeningResearchPoints = 0;
    State.AvailableResearchPoints = 0;
    State.TotalResearchEarnedPoints = 0;
    State.TotalResearchSpentPoints = 0;
    State.NextLedgerSequence = 1;
    return State;
}

bool ResolveCampaignTopologyAndManagement(const ULBPressShopSaveGame* SaveRoot,
    ELBCampaignTopologyMode& OutTopology, FLBFactoryManagementSaveState& OutManagement)
{
    if (!SaveRoot) return false;
    if (SaveRoot->SaveFormatVersion >= FirstTopologyAndManagementSaveFormat)
    {
        if (!StaticEnum<ELBCampaignTopologyMode>()->IsValidEnumValue(
                static_cast<int64>(SaveRoot->TopologyMode)))
        {
            return false;
        }
        OutTopology = SaveRoot->TopologyMode;
        OutManagement = SaveRoot->FactoryManagement;
        return OutManagement.bCampaignInitialised;
    }

    // Versions 13-16 had one authored topology and no management payload. Reject
    // future-field smuggling rather than silently applying data the old root could
    // never have produced, then migrate to one exact fresh authority state.
    if (SaveRoot->TopologyMode != ELBCampaignTopologyMode::LegacyAuthoredPressShop
        || !IsLegacyDefaultManagementState(SaveRoot->FactoryManagement))
    {
        return false;
    }
    OutTopology = ELBCampaignTopologyMode::LegacyAuthoredPressShop;
    OutManagement = BuildFreshMigratedManagementState();
    return true;
}

bool IsFinitePoint(const FVector& Value)
{
    return FMath::IsFinite(Value.X) && FMath::IsFinite(Value.Y) && FMath::IsFinite(Value.Z);
}

bool IsKnownStillageJobType(const ELBStillageFLTJobType Type)
{
    return Type == ELBStillageFLTJobType::FullStillageToWeld
        || Type == ELBStillageFLTJobType::EmptyStillageToPress;
}

bool IsKnownStillageJobState(const ELBStillageFLTJobState State)
{
    return State == ELBStillageFLTJobState::Pending
        || State == ELBStillageFLTJobState::Claimed
        || State == ELBStillageFLTJobState::DeliveredReturning
        || State == ELBStillageFLTJobState::Completed
        || State == ELBStillageFLTJobState::Failed;
}

bool IsOutstandingStillageJob(const ELBStillageFLTJobState State)
{
    return State == ELBStillageFLTJobState::Pending
        || State == ELBStillageFLTJobState::Claimed
        || State == ELBStillageFLTJobState::DeliveredReturning;
}

bool IsDeterministicStorageStackPad(const FName AuthorityId,
    const FName StackPadId)
{
    if (AuthorityId.IsNone() || StackPadId.IsNone()) return false;
    const FString Prefix = AuthorityId.ToString() + TEXT("-STACK-PAD-");
    const FString Value = StackPadId.ToString();
    if (!Value.StartsWith(Prefix, ESearchCase::CaseSensitive)) return false;
    const FString Suffix = Value.RightChop(Prefix.Len());
    if (Suffix.Len() != 3) return false;
    for (const TCHAR Character : Suffix)
        if (!FChar::IsDigit(Character)) return false;
    return FCString::Atoi(*Suffix) > 0;
}

bool IsKnownStillageFLTPhase(const ELBCompactStillageFLTPhase Phase)
{
    return Phase == ELBCompactStillageFLTPhase::Parked
        || Phase == ELBCompactStillageFLTPhase::TravelToPickup
        || Phase == ELBCompactStillageFLTPhase::PickupDockProving
        || Phase == ELBCompactStillageFLTPhase::RaisingLoad
        || Phase == ELBCompactStillageFLTPhase::TravelToDropoff
        || Phase == ELBCompactStillageFLTPhase::DropoffDockProving
        || Phase == ELBCompactStillageFLTPhase::RaisingToStackTier
        || Phase == ELBCompactStillageFLTPhase::StackLocatorProving
        || Phase == ELBCompactStillageFLTPhase::LoweringLoad
        || Phase == ELBCompactStillageFLTPhase::ReturningToBerth
        || Phase == ELBCompactStillageFLTPhase::Fault;
}

bool IsTravelStillageFLTPhase(const ELBCompactStillageFLTPhase Phase)
{
    return Phase == ELBCompactStillageFLTPhase::TravelToPickup
        || Phase == ELBCompactStillageFLTPhase::TravelToDropoff
        || Phase == ELBCompactStillageFLTPhase::ReturningToBerth;
}

bool IsKnownStillageFLTFault(const ELBCompactStillageFLTFault Fault)
{
    return Fault == ELBCompactStillageFLTFault::None
        || Fault == ELBCompactStillageFLTFault::InvalidIdentity
        || Fault == ELBCompactStillageFLTFault::InvalidJob
        || Fault == ELBCompactStillageFLTFault::RouteUnavailable
        || Fault == ELBCompactStillageFLTFault::RouteCollision
        || Fault == ELBCompactStillageFLTFault::RaisedMastTravelProhibited
        || Fault == ELBCompactStillageFLTFault::StackLocatorMisaligned
        || Fault == ELBCompactStillageFLTFault::RestoreRejected;
}

bool IsLegacyDefaultStillageFleetState(const FLBStillageFLTFleetSaveState& State)
{
    return State.Version == 1 && State.NextUnitSerial == 2 && State.NextJobSequence == 1
        && State.Units.IsEmpty() && State.Jobs.IsEmpty();
}

bool IsStillageFleetSaveStateValid(const FLBStillageFLTFleetSaveState& State)
{
    if (State.Version != 1 || State.NextUnitSerial <= 1 || State.NextJobSequence <= 0
        || State.Units.IsEmpty() || State.Units.Num() > MaximumPersistedStillageFLTs)
    {
        return false;
    }

    TMap<FName, const FLBCompactStillageFLTSaveState*> UnitsById;
    for (const FLBCompactStillageFLTSaveState& Unit : State.Units)
    {
        const bool bLoadIdentityValid = Unit.bCarryingStillage
            ? !Unit.CarriedStillageId.IsNone() : Unit.CarriedStillageId.IsNone();
        if (Unit.Version != 1 || Unit.UnitId.IsNone() || UnitsById.Contains(Unit.UnitId)
            || !IsKnownStillageFLTPhase(Unit.Phase) || !IsKnownStillageFLTFault(Unit.Fault)
            || !IsFinitePoint(Unit.VehicleTransform.GetLocation())
            || !IsFinitePoint(Unit.VehicleTransform.GetScale3D())
            || Unit.VehicleTransform.ContainsNaN() || !IsFinitePoint(Unit.HomeBerth)
            || !FMath::IsFinite(Unit.CurrentSpeedCmPerSecond)
            || Unit.CurrentSpeedCmPerSecond < 0.0f || Unit.CurrentSpeedCmPerSecond > 171.0f
            || !FMath::IsFinite(Unit.CarriageLiftCm)
            || Unit.CarriageLiftCm < 0.0f || Unit.CarriageLiftCm
                > ALBCompactStillageFLT::MaximumSupportedForkPlacementHeightCm
            || !FMath::IsFinite(Unit.RearSteerAngleDegrees)
            || FMath::Abs(Unit.RearSteerAngleDegrees)
                > ALBCompactStillageFLT::MaximumSupportedRearSteerAngleDegrees + 0.1f
            || (IsTravelStillageFLTPhase(Unit.Phase) && Unit.CarriageLiftCm
                > ALBCompactStillageFLT::MaximumPermittedTravelLiftCm + 0.05f)
            || !bLoadIdentityValid || (Unit.bCarriedStillageFull && !Unit.bCarryingStillage)
            || (Unit.Phase == ELBCompactStillageFLTPhase::Parked
                && !Unit.ActiveJobId.IsNone())
            || (Unit.Phase != ELBCompactStillageFLTPhase::Parked
                && Unit.ActiveJobId.IsNone()))
        {
            return false;
        }
        UnitsById.Add(Unit.UnitId, &Unit);
    }

    TSet<FName> SeenJobs;
    TSet<FName> OutstandingStillages;
    TSet<FName> ClaimedUnits;
    TSet<FString> OutstandingStorageAddresses;
    int64 MaximumSequence = 0;
    for (const FLBStillageFLTJob& Job : State.Jobs)
    {
        if (Job.Version != 1 || Job.JobId.IsNone() || Job.StillageId.IsNone()
            || !IsKnownStillageJobType(Job.JobType) || !IsKnownStillageJobState(Job.State)
            || Job.SourceAuthorityId.IsNone() || Job.TargetAuthorityId.IsNone()
            || Job.SourceAuthorityId == Job.TargetAuthorityId || SeenJobs.Contains(Job.JobId)
            || Job.TargetStackPadId.IsNone() || Job.TargetStackTier < 1
            || Job.TargetStackTier > ALBCompactStillageFLT::MaximumSupportedStackTier
            || !FMath::IsFinite(Job.TargetStackPadYawDegrees)
            || Job.CreatedSequence <= 0 || !IsFinitePoint(Job.PickupServicePoint)
            || !IsFinitePoint(Job.DropoffServicePoint)
            || FVector::Dist2D(Job.PickupServicePoint, Job.DropoffServicePoint) < 50.0f
            || !FMath::IsFinite(Job.StillageHalfExtentCm.X)
            || !FMath::IsFinite(Job.StillageHalfExtentCm.Y)
            || Job.StillageHalfExtentCm.X < 20.0f || Job.StillageHalfExtentCm.X > 250.0f
            || Job.StillageHalfExtentCm.Y < 20.0f || Job.StillageHalfExtentCm.Y > 250.0f)
        {
            return false;
        }
        SeenJobs.Add(Job.JobId);
        MaximumSequence = FMath::Max(MaximumSequence, Job.CreatedSequence);
        if (IsOutstandingStillageJob(Job.State))
        {
            if (OutstandingStillages.Contains(Job.StillageId)) return false;
            OutstandingStillages.Add(Job.StillageId);
            if (IsDeterministicStorageStackPad(
                    Job.TargetAuthorityId, Job.TargetStackPadId))
            {
                const FString AddressKey = FString::Printf(TEXT("%s|%s|%d"),
                    *Job.TargetAuthorityId.ToString(),
                    *Job.TargetStackPadId.ToString(), Job.TargetStackTier);
                if (OutstandingStorageAddresses.Contains(AddressKey)) return false;
                OutstandingStorageAddresses.Add(AddressKey);
            }
        }

        const bool bClaimed = Job.State == ELBStillageFLTJobState::Claimed
            || Job.State == ELBStillageFLTJobState::DeliveredReturning;
        if (bClaimed)
        {
            const FLBCompactStillageFLTSaveState* const* Unit = UnitsById.Find(
                Job.ClaimedUnitId);
            if (!Unit || ClaimedUnits.Contains(Job.ClaimedUnitId)
                || (*Unit)->ActiveJobId != Job.JobId)
            {
                return false;
            }
            ClaimedUnits.Add(Job.ClaimedUnitId);
        }
        else if (!Job.ClaimedUnitId.IsNone())
        {
            return false;
        }
    }
    if (State.NextJobSequence <= MaximumSequence) return false;

    for (const TPair<FName, const FLBCompactStillageFLTSaveState*>& Entry : UnitsById)
    {
        const FLBCompactStillageFLTSaveState* Unit = Entry.Value;
        if (Unit->ActiveJobId.IsNone() != (Unit->Phase == ELBCompactStillageFLTPhase::Parked)
            || (!Unit->ActiveJobId.IsNone() && !ClaimedUnits.Contains(Unit->UnitId)))
        {
            return false;
        }
    }
    return true;
}

bool BuildFreshLegacyStillageFleetState(ALBStillageFLTFleetController* Fleet,
    FLBStillageFLTFleetSaveState& OutState)
{
    ALBCompactStillageFLT* Starter = Fleet
        ? Fleet->GetUnitById(TEXT("LB-FLT-AGV-01")) : nullptr;
    FLBCompactStillageFLTSaveState StarterState;
    if (!Starter || !Starter->CaptureSaveState(StarterState)
        || StarterState.HomeBerth.ContainsNaN())
    {
        return false;
    }

    StarterState.Version = 1;
    StarterState.UnitId = TEXT("LB-FLT-AGV-01");
    StarterState.Phase = ELBCompactStillageFLTPhase::Parked;
    StarterState.Fault = ELBCompactStillageFLTFault::None;
    StarterState.VehicleTransform = FTransform(
        Fleet->GetActorQuat(), StarterState.HomeBerth, FVector::OneVector);
    StarterState.CurrentSpeedCmPerSecond = 0.0f;
    StarterState.CarriageLiftCm = 0.0f;
    StarterState.RearSteerAngleDegrees = 0.0f;
    StarterState.bCarryingStillage = false;
    StarterState.bCarriedStillageFull = false;
    StarterState.CarriedStillageId = NAME_None;
    StarterState.ActiveJobId = NAME_None;
    StarterState.bDeliveryEventEmitted = false;

    OutState = FLBStillageFLTFleetSaveState();
    OutState.Units.Add(StarterState);
    return IsStillageFleetSaveStateValid(OutState);
}

FBox SavedBodyWeldEnvelope(const FLBBodyWeldLineSaveState& State)
{
    // This is the persisted placement contract owned by ALBBodyWeldLineActor:
    // local protected centre (2700,0,350), half extent (3000,1500,350).
    return FBox(FVector(-300.0f, -1500.0f, 0.0f),
        FVector(5700.0f, 1500.0f, 700.0f)).TransformBy(State.WorldTransform);
}

FBox SavedECoatEnvelope(const FLBECoatLineSaveState& State)
{
    const ALBECoatLineActor* Defaults = GetDefault<ALBECoatLineActor>();
    if (!Defaults) return FBox(ForceInit);
    const FVector Centre = Defaults->GetProtectedEnvelopeRelativeCentreCm();
    const FVector Extent = Defaults->GetProtectedEnvelopeHalfExtentCm();
    return FBox(Centre - Extent, Centre + Extent).TransformBy(State.WorldTransform);
}

bool SavedGenericMachineEnvelope(const FLBFactoryBuildMachineSaveState& State,
    FBox& OutEnvelope)
{
    // Keep campaign preflight read-only. Constructing an AActor with NewObject is
    // not a valid Unreal lifecycle and configuring a CDO would mutate global class
    // state. These are the stable protected-envelope contracts persisted by the
    // six generic machine types in ALBFactoryBuildMachine::Configure.
    FVector Centre = FVector::ZeroVector;
    FVector Extent = FVector::ZeroVector;
    switch (State.MachineType)
    {
    case ELBFactoryBuildMachineType::InboundDeliveryDock:
        Centre = FVector(64.0f, -59.75f, 398.5f);
        Extent = FVector(716.0f, 909.75f, 398.5f);
        break;
    case ELBFactoryBuildMachineType::DepackagingRobot:
        Extent = FVector(330.0f, 230.0f, 100.0f);
        break;
    case ELBFactoryBuildMachineType::DecoilerFeeder:
        Extent = FVector(750.0f, 1300.0f, 350.0f);
        break;
    case ELBFactoryBuildMachineType::InspectionCell:
        Extent = FVector(600.0f, 500.0f, 300.0f);
        break;
    case ELBFactoryBuildMachineType::OutboundPanelDock:
        Extent = FVector(450.0f, 350.0f, 250.0f);
        break;
    case ELBFactoryBuildMachineType::CoilWeighInspectionCell:
        Extent = FVector(190.0f, 195.0f, 182.0f);
        break;
    default:
        return false;
    }
    OutEnvelope = FBox(Centre - Extent, Centre + Extent)
        .TransformBy(State.WorldTransform);
    return OutEnvelope.IsValid != 0;
}

bool ValidateSavedCompositeLayout(const ULBPressShopSaveGame* SaveRoot)
{
    if (!SaveRoot) return false;
    TArray<FBox> Occupied;
    Occupied.Reserve(SaveRoot->PlayerBuiltMachines.Num()
        + SaveRoot->PlayerStorageZones.Num() + SaveRoot->PressTrains.Num()
        + SaveRoot->PlayerBuiltAGVInfrastructure.Num()
        + SaveRoot->PlayerBuiltBodyWeldLines.Num()
        + SaveRoot->PlayerBuiltECoatLines.Num());

    for (const FLBFactoryBuildMachineSaveState& State : SaveRoot->PlayerBuiltMachines)
    {
        FBox Envelope(ForceInit);
        if (!SavedGenericMachineEnvelope(State, Envelope)) return false;
        Occupied.Add(Envelope);
    }
    for (const FLBPressShopStorageZoneSaveState& State : SaveRoot->PlayerStorageZones)
        Occupied.Add(FBox(-State.ZoneHalfExtent, State.ZoneHalfExtent)
            .TransformBy(State.WorldTransform));
    for (const FLBPressTrainASaveState& State : SaveRoot->PressTrains)
        Occupied.Add(ALBPressTrainAStation::GetProtectedLocalEnvelope()
            .TransformBy(State.WorldTransform));
    for (const FLBFactoryAGVInfrastructureSaveState& State : SaveRoot->PlayerBuiltAGVInfrastructure)
    {
        const FVector Extent = ALBFactoryAGVInfrastructure::GetPlacementHalfExtentForType(State.Type);
        Occupied.Add(FBox(FVector(-Extent.X, -Extent.Y, 0.0f),
            FVector(Extent.X, Extent.Y, Extent.Z * 2.0f)).TransformBy(State.WorldTransform));
    }

    // Existing historical sets may intentionally touch one another at process
    // ports. The v18 addition is stricter: its complete protected envelope may
    // not intersect any saved authority, and ED may not intersect weld.
    for (const FLBBodyWeldLineSaveState& Weld : SaveRoot->PlayerBuiltBodyWeldLines)
    {
        const FBox WeldBox = SavedBodyWeldEnvelope(Weld);
        for (const FBox& Other : Occupied)
            if (WeldBox.Intersect(Other)) return false;
        for (const FLBECoatLineSaveState& ECoat : SaveRoot->PlayerBuiltECoatLines)
            if (WeldBox.Intersect(SavedECoatEnvelope(ECoat))) return false;
        Occupied.Add(WeldBox);
    }
    return true;
}

bool ValidateBodyWeldOwnershipContract(const ULBPressShopSaveGame* SaveRoot)
{
    if (!SaveRoot) return false;
    FString FlowReason;
    if (!ALBPlayerBuiltPressFlowController::ValidateSaveState(
            SaveRoot->PlayerProductionOrders, FlowReason))
    {
        return false;
    }

    const FLBPlayerBuiltPressFlowSaveState& Flow =
        SaveRoot->PlayerProductionOrders;

    // Flow v4 is introduced with root v18. Older roots may migrate their native
    // v1-v3 payload, but cannot smuggle the new weld-ownership fields.
    if (SaveRoot->SaveFormatVersion < FirstBodyWeldSaveFormat)
    {
        return SaveRoot->PlayerBuiltBodyWeldLines.IsEmpty()
            && SaveRoot->PlayerProductionOrders.Version <= 3
            && SaveRoot->PlayerProductionOrders.PendingBaseKitDeliveries.IsEmpty()
            && SaveRoot->PlayerProductionOrders.TransferredBaseKitDeliveries.IsEmpty();
    }

    if (SaveRoot->PlayerBuiltBodyWeldLines.IsEmpty())
    {
        return !Flow.PanelStillages.ContainsByPredicate(
                [](const FLBPanelStillageLoad& Load)
                { return Load.bAcceptedByBodyWeld || !Load.WeldLineId.IsNone(); })
            && Flow.PendingBaseKitDeliveries.IsEmpty()
            && Flow.TransferredBaseKitDeliveries.IsEmpty();
    }

    TMap<FName, const FLBBodyWeldLineSaveState*> WeldById;
    for (const FLBBodyWeldLineSaveState& Weld : SaveRoot->PlayerBuiltBodyWeldLines)
    {
        if (Weld.LineId.IsNone() || WeldById.Contains(Weld.LineId)) return false;
        WeldById.Add(Weld.LineId, &Weld);
    }

    const auto FindFlowPanel = [&Flow](const FName PanelId)
        -> const FLBPanelLineageRecord*
    {
        return Flow.PanelLineage.FindByPredicate(
            [PanelId](const FLBPanelLineageRecord& Panel)
            { return Panel.PanelId == PanelId; });
    };
    const auto FindFlowLoad = [&Flow](const FName StillageId)
        -> const FLBPanelStillageLoad*
    {
        return Flow.PanelStillages.FindByPredicate(
            [StillageId](const FLBPanelStillageLoad& Load)
            { return Load.StillageId == StillageId; });
    };
    const auto ValidateBodyAgainstFlow = [&FindFlowPanel](
        const FLBBodyInWhiteRecord& Body)
    {
        for (const FLBBodyWeldPanelLineage& Lineage : Body.Panels)
        {
            const FLBPanelLineageRecord* Panel = FindFlowPanel(Lineage.PanelId);
            if (!Panel || Panel->OrderId != Body.OrderId
                || Panel->VehicleModelId != Body.VehicleModelId
                || Panel->PanelTypeId != Lineage.PanelTypeId
                || Panel->StillageId != Lineage.StillageId
                || Panel->Disposition != ELBPanelDisposition::Good
                || Panel->Stage != ELBPanelFlowStage::BodyWeldInventory)
            {
                return false;
            }
        }
        return true;
    };

    TSet<FName> WeldOwnedStillages;
    TSet<FName> WeldOwnedPanels;
    TSet<FName> WeldOwnedKits;
    for (const FLBBodyWeldLineSaveState& Weld : SaveRoot->PlayerBuiltBodyWeldLines)
    {
        if ((Weld.bHasOutputBody && !ValidateBodyAgainstFlow(Weld.OutputBody))
            || (Weld.bHasReworkBody && !ValidateBodyAgainstFlow(Weld.ReworkBody)))
        {
            return false;
        }
        for (const FLBBodyInWhiteRecord& Body : Weld.CompletedBodies)
            if (!ValidateBodyAgainstFlow(Body)) return false;
        for (const FLBBodyWeldStillageInventory& Stillage : Weld.Stillages)
        {
            const FLBPanelStillageLoad* Load = FindFlowLoad(Stillage.StillageId);
            if (!Load || WeldOwnedStillages.Contains(Stillage.StillageId)
                || !Load->bAcceptedByBodyWeld || Load->WeldLineId != Weld.LineId
                || Load->OrderId != Stillage.OrderId
                || Load->VehicleModelId != Stillage.VehicleModelId
                || Load->PanelTypeId != Stillage.PanelTypeId
                || Load->CapacityPanels != Stillage.CapacityPanels
                || Load->WeldDeliverySequence != Stillage.DeliverySequence
                || Load->PanelIds.Num() != Stillage.PanelUnits.Num())
            {
                return false;
            }
            WeldOwnedStillages.Add(Stillage.StillageId);
            for (const FLBBodyWeldPanelUnit& Unit : Stillage.PanelUnits)
            {
                const FLBPanelLineageRecord* Panel = FindFlowPanel(Unit.PanelId);
                if (!Panel || WeldOwnedPanels.Contains(Unit.PanelId)
                    || !Load->PanelIds.Contains(Unit.PanelId)
                    || Panel->Stage != ELBPanelFlowStage::BodyWeldInventory
                    || Panel->Disposition != ELBPanelDisposition::Good
                    || Panel->StillageId != Stillage.StillageId
                    || Panel->OrderId != Unit.OrderId
                    || Panel->VehicleModelId != Unit.VehicleModelId
                    || Panel->PanelTypeId != Unit.PanelTypeId)
                {
                    return false;
                }
                WeldOwnedPanels.Add(Unit.PanelId);
            }
        }

        for (const FLBBodyWeldBaseKitUnit& Kit : Weld.BaseKits)
        {
            const FLBBodyWeldBaseKitDeliveryRecord* Delivery =
                Flow.TransferredBaseKitDeliveries.FindByPredicate(
                    [&Kit, &Weld](const FLBBodyWeldBaseKitDeliveryRecord& Candidate)
                    {
                        return Candidate.BaseKit.KitId == Kit.KitId
                            && Candidate.TargetWeldLineId == Weld.LineId;
                    });
            if (!Delivery || WeldOwnedKits.Contains(Kit.KitId)
                || Delivery->BaseKit.OrderId != Kit.OrderId
                || Delivery->BaseKit.VehicleModelId != Kit.VehicleModelId
                || Delivery->BaseKit.KitTypeId != Kit.KitTypeId
                || Delivery->BaseKit.DeliverySequence != Kit.DeliverySequence)
            {
                return false;
            }
            WeldOwnedKits.Add(Kit.KitId);
        }
    }

    // Every flow-side ownership claim must resolve to exactly one persisted weld
    // authority. A consumed stillage may already be an issued/returned empty and
    // therefore no longer appear in the actor's live Stillages array.
    for (const FLBPanelStillageLoad& Load : Flow.PanelStillages)
    {
        if (!Load.bAcceptedByBodyWeld) continue;
        const FLBBodyWeldLineSaveState* const* WeldPtr = WeldById.Find(Load.WeldLineId);
        if (!WeldPtr) return false;
        const FLBBodyWeldLineSaveState& Weld = **WeldPtr;
        const bool bHeldByWeld = WeldOwnedStillages.Contains(Load.StillageId);
        const bool bPendingEmpty = Weld.PendingEmptyReturns.ContainsByPredicate(
            [&Load](const FLBBodyWeldEmptyStillageReturn& Empty)
            { return Empty.StillageId == Load.StillageId; });
        if (!bHeldByWeld && !bPendingEmpty && !Load.bEmptyReturnQueued
            && !Load.bReturnedEmpty)
        {
            return false;
        }
    }
    for (const FLBBodyWeldBaseKitDeliveryRecord& Delivery : Flow.TransferredBaseKitDeliveries)
    {
        const FLBBodyWeldLineSaveState* const* WeldPtr =
            WeldById.Find(Delivery.TargetWeldLineId);
        if (!WeldPtr)
        {
            return false;
        }
        const FLBBodyWeldLineSaveState& Weld = **WeldPtr;
        const bool bPresentInInventory = WeldOwnedKits.Contains(Delivery.BaseKit.KitId);
        const auto BodyUsesKit = [&Delivery](const FLBBodyInWhiteRecord& Body)
        { return Body.BaseKitId == Delivery.BaseKit.KitId; };
        const bool bPresentInCycle = Weld.ActiveReservation.bValid
            && Weld.ActiveReservation.BaseKitId == Delivery.BaseKit.KitId;
        const bool bPresentInBody = (Weld.bHasOutputBody && BodyUsesKit(Weld.OutputBody))
            || (Weld.bHasReworkBody && BodyUsesKit(Weld.ReworkBody))
            || Weld.CompletedBodies.ContainsByPredicate(BodyUsesKit);
        if (!bPresentInInventory && !bPresentInCycle && !bPresentInBody) return false;
    }
    return true;
}

bool SameBodyInWhiteIdentity(const FLBBodyInWhiteRecord& Left,
    const FLBBodyInWhiteRecord& Right)
{
    if (Left.BodyId != Right.BodyId || Left.VehicleModelId != Right.VehicleModelId
        || Left.OrderId != Right.OrderId || Left.BaseKitId != Right.BaseKitId
        || Left.ReservationId != Right.ReservationId
        || Left.WeldLineId != Right.WeldLineId
        || Left.QualityState != Right.QualityState
        || Left.bEDAccepted != Right.bEDAccepted
        || Left.Panels.Num() != Right.Panels.Num()
        || Left.QualityEvidence.bRecipeComplete != Right.QualityEvidence.bRecipeComplete
        || Left.QualityEvidence.bFixtureProgramCorrect
            != Right.QualityEvidence.bFixtureProgramCorrect
        || Left.QualityEvidence.bSpotOperationsComplete
            != Right.QualityEvidence.bSpotOperationsComplete
        || Left.QualityEvidence.bMIGOperationsComplete
            != Right.QualityEvidence.bMIGOperationsComplete
        || Left.QualityEvidence.bRobotCalibrationInTolerance
            != Right.QualityEvidence.bRobotCalibrationInTolerance
        || Left.QualityEvidence.bServiceConditionAcceptable
            != Right.QualityEvidence.bServiceConditionAcceptable
        || Left.QualityEvidence.bSafetyInterlockClear
            != Right.QualityEvidence.bSafetyInterlockClear
        || Left.QualityEvidence.ReasonCodes != Right.QualityEvidence.ReasonCodes
        || !FMath::IsNearlyEqual(Left.CycleEvidence.ClosurePreparationSeconds,
            Right.CycleEvidence.ClosurePreparationSeconds)
        || !FMath::IsNearlyEqual(Left.CycleEvidence.FramingSeconds,
            Right.CycleEvidence.FramingSeconds)
        || !FMath::IsNearlyEqual(Left.CycleEvidence.WeldingSeconds,
            Right.CycleEvidence.WeldingSeconds)
        || !FMath::IsNearlyEqual(Left.CycleEvidence.GeometryCheckSeconds,
            Right.CycleEvidence.GeometryCheckSeconds)
        || Left.CycleEvidence.CompletionSequence
            != Right.CycleEvidence.CompletionSequence)
    {
        return false;
    }
    for (int32 Index = 0; Index < Left.Panels.Num(); ++Index)
    {
        const FLBBodyWeldPanelLineage& A = Left.Panels[Index];
        const FLBBodyWeldPanelLineage& B = Right.Panels[Index];
        if (A.PanelId != B.PanelId || A.PanelTypeId != B.PanelTypeId
            || A.StillageId != B.StillageId)
        {
            return false;
        }
    }
    return true;
}

bool ValidateECoatBodyOwnershipContract(const ULBPressShopSaveGame* SaveRoot)
{
    if (!SaveRoot) return false;
    if (SaveRoot->SaveFormatVersion < FirstBodyWeldSaveFormat)
    {
        return !SaveRoot->PlayerBuiltECoatLines.ContainsByPredicate(
            [](const FLBECoatLineSaveState& ECoat)
            {
                return ECoat.Carriers.ContainsByPredicate(
                    [](const FLBECoatCarrierSaveState& Carrier)
                    { return Carrier.bHasBodyInWhite; });
            });
    }

    TMap<FName, const FLBBodyInWhiteRecord*> CompletedByBodyId;
    for (const FLBBodyWeldLineSaveState& Weld : SaveRoot->PlayerBuiltBodyWeldLines)
    {
        for (const FLBBodyInWhiteRecord& Body : Weld.CompletedBodies)
        {
            if (Body.BodyId.IsNone() || CompletedByBodyId.Contains(Body.BodyId)
                || Body.WeldLineId != Weld.LineId || !Body.bEDAccepted)
            {
                return false;
            }
            CompletedByBodyId.Add(Body.BodyId, &Body);
        }
    }

    TSet<FName> EDOwnedBodyIds;
    for (const FLBECoatLineSaveState& ECoat : SaveRoot->PlayerBuiltECoatLines)
    {
        for (const FLBECoatCarrierSaveState& Carrier : ECoat.Carriers)
        {
            if (!Carrier.bHasBodyInWhite) continue;
            const FLBBodyInWhiteRecord* const* Source =
                CompletedByBodyId.Find(Carrier.BodyInWhite.BodyId);
            if (!Source || EDOwnedBodyIds.Contains(Carrier.BodyInWhite.BodyId)
                || !SameBodyInWhiteIdentity(**Source, Carrier.BodyInWhite))
            {
                return false;
            }
            EDOwnedBodyIds.Add(Carrier.BodyInWhite.BodyId);
        }
    }
    return true;
}

bool ValidateStillageFleetFlowJobContract(const ULBPressShopSaveGame* SaveRoot)
{
    if (!SaveRoot) return false;
    if (SaveRoot->SaveFormatVersion < FirstBodyWeldSaveFormat) return true;

    TMap<FName, const FLBPanelStillageLoad*> DeliveryClaims;
    TMap<FName, const FLBPanelStillageLoad*> EmptyReturnClaims;
    TMap<FName, ELBFactoryBuildMachineType> MachineTypes;
    TSet<FName> WeldIds;
    TSet<FName> EmptyStillageZoneIds;
    TSet<FName> SavedLinkPairs;
    for (const FLBFactoryBuildMachineSaveState& Machine : SaveRoot->PlayerBuiltMachines)
        MachineTypes.Add(Machine.MachineId, Machine.MachineType);
    for (const FLBBodyWeldLineSaveState& Weld : SaveRoot->PlayerBuiltBodyWeldLines)
        WeldIds.Add(Weld.LineId);
    for (const FLBPressShopStorageZoneSaveState& Storage : SaveRoot->PlayerStorageZones)
        if (Storage.StorageType == ELBPressShopStorageType::EmptyPanelStillages)
            EmptyStillageZoneIds.Add(Storage.ZoneId);
    for (const FLBFactoryTransportLinkSaveState& Link : SaveRoot->FactoryTransportLinks)
    {
        SavedLinkPairs.Add(*FString::Printf(TEXT("%s>%s"),
            *Link.SourcePortId.ToString(), *Link.TargetPortId.ToString()));
    }
    for (const FLBPanelStillageLoad& Load : SaveRoot->PlayerProductionOrders.PanelStillages)
    {
        if (!Load.WeldDeliveryJobId.IsNone())
        {
            if (DeliveryClaims.Contains(Load.WeldDeliveryJobId)
                || EmptyReturnClaims.Contains(Load.WeldDeliveryJobId)) return false;
            DeliveryClaims.Add(Load.WeldDeliveryJobId, &Load);
        }
        if (!Load.EmptyReturnJobId.IsNone())
        {
            if (DeliveryClaims.Contains(Load.EmptyReturnJobId)
                || EmptyReturnClaims.Contains(Load.EmptyReturnJobId)) return false;
            EmptyReturnClaims.Add(Load.EmptyReturnJobId, &Load);
        }
    }

    TSet<FName> MatchedDeliveryJobs;
    TSet<FName> MatchedEmptyJobs;
    for (const FLBStillageFLTJob& Job : SaveRoot->StillageFLTFleet.Jobs)
    {
        if (Job.JobType == ELBStillageFLTJobType::FullStillageToWeld)
        {
            const FLBPanelStillageLoad* const* Load = DeliveryClaims.Find(Job.JobId);
            const ELBFactoryBuildMachineType* SourceType =
                MachineTypes.Find(Job.SourceAuthorityId);
            const FName LinkPair(*FString::Printf(TEXT("%s-OUT>%s-STILLAGE-IN"),
                *Job.SourceAuthorityId.ToString(), *Job.TargetAuthorityId.ToString()));
            if (!Load || (*Load)->StillageId != Job.StillageId
                || (*Load)->WeldLineId != Job.TargetAuthorityId
                || !SourceType
                || *SourceType != ELBFactoryBuildMachineType::OutboundPanelDock
                || !WeldIds.Contains(Job.TargetAuthorityId)
                || !SavedLinkPairs.Contains(LinkPair)
                || MatchedDeliveryJobs.Contains(Job.JobId))
            {
                return false;
            }
            MatchedDeliveryJobs.Add(Job.JobId);
        }
        else if (Job.JobType == ELBStillageFLTJobType::EmptyStillageToPress)
        {
            const FLBPanelStillageLoad* const* Load = EmptyReturnClaims.Find(Job.JobId);
            if (!Load || (*Load)->StillageId != Job.StillageId
                || (*Load)->WeldLineId != Job.SourceAuthorityId
                || !WeldIds.Contains(Job.SourceAuthorityId)
                || !EmptyStillageZoneIds.Contains(Job.TargetAuthorityId)
                || !(*Load)->bAcceptedByBodyWeld
                || MatchedEmptyJobs.Contains(Job.JobId))
            {
                return false;
            }
            MatchedEmptyJobs.Add(Job.JobId);
        }
        else
        {
            return false;
        }
    }
    return MatchedDeliveryJobs.Num() == DeliveryClaims.Num()
        && MatchedEmptyJobs.Num() == EmptyReturnClaims.Num();
}

bool ValidatePendingBaseKitTopologyContract(const ULBPressShopSaveGame* SaveRoot)
{
    if (!SaveRoot) return false;
    if (SaveRoot->SaveFormatVersion < FirstBodyWeldSaveFormat)
        return SaveRoot->PlayerProductionOrders.PendingBaseKitDeliveries.IsEmpty();

    TMap<FName, ELBFactoryBuildMachineType> MachineTypes;
    for (const FLBFactoryBuildMachineSaveState& Machine : SaveRoot->PlayerBuiltMachines)
        MachineTypes.Add(Machine.MachineId, Machine.MachineType);
    TSet<FName> WeldIds;
    for (const FLBBodyWeldLineSaveState& Weld : SaveRoot->PlayerBuiltBodyWeldLines)
    {
        if (WeldIds.Contains(Weld.LineId)) return false;
        WeldIds.Add(Weld.LineId);
    }
    TSet<FName> LinkPairs;
    for (const FLBFactoryTransportLinkSaveState& Link : SaveRoot->FactoryTransportLinks)
    {
        const FName Pair(*FString::Printf(TEXT("%s>%s"),
            *Link.SourcePortId.ToString(), *Link.TargetPortId.ToString()));
        if (LinkPairs.Contains(Pair)) return false;
        LinkPairs.Add(Pair);
    }

    const auto ValidateDelivery = [&MachineTypes, &WeldIds, &LinkPairs](
        const FLBBodyWeldBaseKitDeliveryRecord& Delivery)
    {
        const ELBFactoryBuildMachineType* Type =
            MachineTypes.Find(Delivery.DeliveryAuthorityId);
        const FName Pair(*FString::Printf(TEXT("%s-OUT>%s-BASE-KIT-IN"),
            *Delivery.DeliveryAuthorityId.ToString(),
            *Delivery.TargetWeldLineId.ToString()));
        if (!Type || *Type != ELBFactoryBuildMachineType::OutboundPanelDock
            || !WeldIds.Contains(Delivery.TargetWeldLineId)
            || !LinkPairs.Contains(Pair))
        {
            return false;
        }
        return true;
    };
    for (const FLBBodyWeldBaseKitDeliveryRecord& Delivery :
        SaveRoot->PlayerProductionOrders.PendingBaseKitDeliveries)
    {
        if (!ValidateDelivery(Delivery) || Delivery.bTransferred) return false;
    }
    for (const FLBBodyWeldBaseKitDeliveryRecord& Delivery :
        SaveRoot->PlayerProductionOrders.TransferredBaseKitDeliveries)
    {
        if (!ValidateDelivery(Delivery) || !Delivery.bTransferred) return false;
    }
    return true;
}

bool ValidateSavedConnectionIdentities(const ULBPressShopSaveGame* SaveRoot)
{
    if (!SaveRoot) return false;
    struct FSavedPortDescriptor
    {
        FName PortId = NAME_None;
        ELBFactoryPortDirection Direction = ELBFactoryPortDirection::Input;
        ELBFactoryTransportKind TransportKind = ELBFactoryTransportKind::RollerConveyor;
        ELBFactoryMaterialClass MaterialClass = ELBFactoryMaterialClass::Blank;
        int32 ProcessStage = 0;
        float MaximumLinkDistanceCm = 0.0f;
        int32 MaximumConnections = 1;
        FVector WorldLocation = FVector::ZeroVector;
    };

    TMap<FName, FSavedPortDescriptor> Ports;
    const auto AddPort = [&Ports](const FName PortId,
        const ELBFactoryPortDirection Direction,
        const ELBFactoryTransportKind TransportKind,
        const ELBFactoryMaterialClass MaterialClass, const int32 ProcessStage,
        const float MaximumLinkDistanceCm, const int32 MaximumConnections,
        const FTransform& OwnerTransform, const FVector& RelativeLocation)
    {
        if (PortId.IsNone() || Ports.Contains(PortId)
            || MaximumLinkDistanceCm <= 0.0f || MaximumConnections <= 0)
        {
            return false;
        }
        FSavedPortDescriptor Descriptor;
        Descriptor.PortId = PortId;
        Descriptor.Direction = Direction;
        Descriptor.TransportKind = TransportKind;
        Descriptor.MaterialClass = MaterialClass;
        Descriptor.ProcessStage = ProcessStage;
        Descriptor.MaximumLinkDistanceCm = MaximumLinkDistanceCm;
        Descriptor.MaximumConnections = MaximumConnections;
        Descriptor.WorldLocation = OwnerTransform.TransformPosition(RelativeLocation);
        if (!IsFinitePoint(Descriptor.WorldLocation)) return false;
        Ports.Add(PortId, Descriptor);
        return true;
    };

    TSet<FName> BaseKitAdapterIds;
    for (const FLBBodyWeldBaseKitDeliveryRecord& Delivery :
        SaveRoot->PlayerProductionOrders.PendingBaseKitDeliveries)
        BaseKitAdapterIds.Add(Delivery.DeliveryAuthorityId);
    for (const FLBBodyWeldBaseKitDeliveryRecord& Delivery :
        SaveRoot->PlayerProductionOrders.TransferredBaseKitDeliveries)
        BaseKitAdapterIds.Add(Delivery.DeliveryAuthorityId);

    for (const FLBFactoryBuildMachineSaveState& Machine : SaveRoot->PlayerBuiltMachines)
    {
        FVector HalfExtent = FVector::ZeroVector;
        int32 Stage = 0;
        ELBFactoryMaterialClass InputMaterial = ELBFactoryMaterialClass::GeneralParts;
        ELBFactoryMaterialClass OutputMaterial = ELBFactoryMaterialClass::GeneralParts;
        ELBFactoryTransportKind InputTransport = ELBFactoryTransportKind::AGVHandoff;
        ELBFactoryTransportKind OutputTransport = ELBFactoryTransportKind::AGVHandoff;
        int32 InputCapacity = 1;
        switch (Machine.MachineType)
        {
        case ELBFactoryBuildMachineType::InboundDeliveryDock:
            HalfExtent = FVector(160.0f, 850.0f, 225.0f);
            Stage = LBFactoryProcessStage::InboundUnloading;
            InputMaterial = OutputMaterial = ELBFactoryMaterialClass::Coil;
            break;
        case ELBFactoryBuildMachineType::CoilWeighInspectionCell:
            HalfExtent = FVector(190.0f, 195.0f, 182.0f);
            Stage = LBFactoryProcessStage::PR002WeighInspection;
            InputMaterial = OutputMaterial = ELBFactoryMaterialClass::Coil;
            break;
        case ELBFactoryBuildMachineType::DepackagingRobot:
            HalfExtent = FVector(330.0f, 230.0f, 100.0f);
            Stage = LBFactoryProcessStage::DepackAndIdentify;
            InputMaterial = OutputMaterial = ELBFactoryMaterialClass::Coil;
            break;
        case ELBFactoryBuildMachineType::DecoilerFeeder:
            HalfExtent = FVector(750.0f, 1300.0f, 350.0f);
            Stage = LBFactoryProcessStage::DecoilerThreader;
            InputMaterial = ELBFactoryMaterialClass::Coil;
            OutputMaterial = ELBFactoryMaterialClass::Blank;
            OutputTransport = ELBFactoryTransportKind::RollerConveyor;
            InputCapacity = 4;
            break;
        case ELBFactoryBuildMachineType::InspectionCell:
            HalfExtent = FVector(600.0f, 500.0f, 300.0f);
            Stage = LBFactoryProcessStage::Inspection;
            InputMaterial = ELBFactoryMaterialClass::FormedPanel;
            OutputMaterial = ELBFactoryMaterialClass::InspectedPanel;
            InputTransport = OutputTransport = ELBFactoryTransportKind::PanelTransfer;
            InputCapacity = 4;
            break;
        case ELBFactoryBuildMachineType::OutboundPanelDock:
            HalfExtent = FVector(450.0f, 350.0f, 250.0f);
            Stage = LBFactoryProcessStage::WeldShopIntake;
            InputMaterial = OutputMaterial = ELBFactoryMaterialClass::Stillage;
            if (BaseKitAdapterIds.Contains(Machine.MachineId))
                OutputMaterial = ELBFactoryMaterialClass::GeneralParts;
            InputCapacity = 4;
            break;
        default:
            return false;
        }
        const FString Id = Machine.MachineId.ToString();
        if (!AddPort(*FString::Printf(TEXT("%s-IN"), *Id),
                ELBFactoryPortDirection::Input, InputTransport, InputMaterial,
                Stage, 2500.0f, InputCapacity, Machine.WorldTransform,
                FVector(0.0f, -HalfExtent.Y, 0.0f))
            || !AddPort(*FString::Printf(TEXT("%s-OUT"), *Id),
                ELBFactoryPortDirection::Output, OutputTransport, OutputMaterial,
                Stage, 2500.0f, 4, Machine.WorldTransform,
                FVector(0.0f, HalfExtent.Y, 0.0f)))
        {
            return false;
        }
    }
    for (const FLBPressTrainASaveState& Train : SaveRoot->PressTrains)
    {
        const FString Id = Train.TrainId.ToString();
        if (!AddPort(*FString::Printf(TEXT("%s-IN"), *Id),
                ELBFactoryPortDirection::Input, ELBFactoryTransportKind::RollerConveyor,
                ELBFactoryMaterialClass::Blank, LBFactoryProcessStage::PressTrain,
                2500.0f, 1, Train.WorldTransform, FVector(0.0f, -500.0f, 110.0f))
            || !AddPort(*FString::Printf(TEXT("%s-OUT"), *Id),
                ELBFactoryPortDirection::Output, ELBFactoryTransportKind::PanelTransfer,
                ELBFactoryMaterialClass::FormedPanel, LBFactoryProcessStage::PressTrain,
                2500.0f, 4, Train.WorldTransform, FVector(0.0f, 6284.0f, 110.0f)))
        {
            return false;
        }
    }
    for (const FLBPressShopStorageZoneSaveState& Storage : SaveRoot->PlayerStorageZones)
    {
        int32 Stage = 0;
        ELBFactoryMaterialClass InputMaterial = ELBFactoryMaterialClass::GeneralParts;
        ELBFactoryMaterialClass OutputMaterial = ELBFactoryMaterialClass::GeneralParts;
        ELBFactoryTransportKind InputTransport = ELBFactoryTransportKind::AGVHandoff;
        ELBFactoryTransportKind OutputTransport = ELBFactoryTransportKind::AGVHandoff;
        int32 OutputCapacity = 4;
        switch (Storage.StorageType)
        {
        case ELBPressShopStorageType::BareCoils:
            Stage = LBFactoryProcessStage::CoilStorage;
            InputMaterial = OutputMaterial = ELBFactoryMaterialClass::Coil;
            break;
        case ELBPressShopStorageType::PreparedBlanks:
            Stage = LBFactoryProcessStage::PreparedBlankBuffer;
            InputMaterial = OutputMaterial = ELBFactoryMaterialClass::Blank;
            InputTransport = OutputTransport = ELBFactoryTransportKind::RollerConveyor;
            break;
        case ELBPressShopStorageType::FinishedPanelStillages:
            Stage = LBFactoryProcessStage::WIPPanelStillageBuffer;
            InputMaterial = ELBFactoryMaterialClass::InspectedPanel;
            OutputMaterial = ELBFactoryMaterialClass::Stillage;
            InputTransport = ELBFactoryTransportKind::PanelTransfer;
            break;
        case ELBPressShopStorageType::EmptyPanelStillages:
            InputMaterial = OutputMaterial = ELBFactoryMaterialClass::Stillage;
            break;
        case ELBPressShopStorageType::Scrap:
            Stage = LBFactoryProcessStage::Inspection;
            InputMaterial = OutputMaterial = ELBFactoryMaterialClass::Scrap;
            InputTransport = OutputTransport = ELBFactoryTransportKind::BeltConveyor;
            break;
        case ELBPressShopStorageType::MaintenanceParts:
            Stage = 1;
            break;
        case ELBPressShopStorageType::Quarantine:
            Stage = 90;
            OutputCapacity = 1;
            break;
        default:
            return false;
        }
        const FString Id = Storage.ZoneId.ToString();
        if (!AddPort(*FString::Printf(TEXT("%s-IN"), *Id),
                ELBFactoryPortDirection::Input, InputTransport, InputMaterial,
                Stage, 2000.0f, 4, Storage.WorldTransform,
                FVector(0.0f, -Storage.ZoneHalfExtent.Y, 0.0f))
            || !AddPort(*FString::Printf(TEXT("%s-OUT"), *Id),
                ELBFactoryPortDirection::Output, OutputTransport, OutputMaterial,
                Stage, 2000.0f, OutputCapacity, Storage.WorldTransform,
                FVector(0.0f, Storage.ZoneHalfExtent.Y, 0.0f)))
        {
            return false;
        }
    }
    for (const FLBBodyWeldLineSaveState& Weld : SaveRoot->PlayerBuiltBodyWeldLines)
    {
        const FString Id = Weld.LineId.ToString();
        if (!AddPort(*FString::Printf(TEXT("%s-STILLAGE-IN"), *Id),
                ELBFactoryPortDirection::Input, ELBFactoryTransportKind::AGVHandoff,
                ELBFactoryMaterialClass::Stillage, LBFactoryProcessStage::BodyWeld,
                2500.0f, 1, Weld.WorldTransform, FVector(0.0f, -900.0f, 100.0f))
            || !AddPort(*FString::Printf(TEXT("%s-BASE-KIT-IN"), *Id),
                ELBFactoryPortDirection::Input, ELBFactoryTransportKind::AGVHandoff,
                ELBFactoryMaterialClass::GeneralParts, LBFactoryProcessStage::BodyWeld,
                2500.0f, 1, Weld.WorldTransform, FVector(0.0f, 900.0f, 100.0f))
            || !AddPort(*FString::Printf(TEXT("%s-BIW-OUT"), *Id),
                ELBFactoryPortDirection::Output, ELBFactoryTransportKind::PanelTransfer,
                ELBFactoryMaterialClass::BodyInWhite, LBFactoryProcessStage::BodyWeld,
                2500.0f, 1, Weld.WorldTransform, FVector(5400.0f, 0.0f, 150.0f)))
        {
            return false;
        }
    }
    for (const FLBECoatLineSaveState& ECoat : SaveRoot->PlayerBuiltECoatLines)
    {
        const FString Id = ECoat.LineId.ToString();
        if (!AddPort(*FString::Printf(TEXT("%s-IN"), *Id),
                ELBFactoryPortDirection::Input, ELBFactoryTransportKind::PanelTransfer,
                ELBFactoryMaterialClass::BodyInWhite, LBFactoryProcessStage::ECoat,
                2500.0f, 1, ECoat.WorldTransform, FVector(0.0f, 0.0f, 430.0f))
            || !AddPort(*FString::Printf(TEXT("%s-OUT"), *Id),
                ELBFactoryPortDirection::Output, ELBFactoryTransportKind::PanelTransfer,
                ELBFactoryMaterialClass::GeneralParts, LBFactoryProcessStage::ECoat,
                2500.0f, 1, ECoat.WorldTransform, FVector(18900.0f, 0.0f, 430.0f)))
        {
            return false;
        }
    }

    TSet<FName> Pairs;
    TMap<FName, int32> ConnectionCounts;
    for (const FLBFactoryTransportLinkSaveState& Link : SaveRoot->FactoryTransportLinks)
    {
        const FName Pair(*FString::Printf(TEXT("%s>%s"),
            *Link.SourcePortId.ToString(), *Link.TargetPortId.ToString()));
        const FSavedPortDescriptor* Source = Ports.Find(Link.SourcePortId);
        const FSavedPortDescriptor* Target = Ports.Find(Link.TargetPortId);
        if (Link.Version != 1 || Link.TransferredUnits < 0 || Pairs.Contains(Pair)
            || !Source || !Target || Link.SourcePortId == Link.TargetPortId
            || Source->Direction != ELBFactoryPortDirection::Output
            || Target->Direction != ELBFactoryPortDirection::Input
            || Source->ProcessStage + 1 != Target->ProcessStage
            || Source->TransportKind != Target->TransportKind
            || Source->MaterialClass != Target->MaterialClass
            || FVector::Distance(Source->WorldLocation, Target->WorldLocation)
                > FMath::Min(Source->MaximumLinkDistanceCm,
                    Target->MaximumLinkDistanceCm))
        {
            return false;
        }
        const int32 SourceCount = ++ConnectionCounts.FindOrAdd(Source->PortId);
        const int32 TargetCount = ++ConnectionCounts.FindOrAdd(Target->PortId);
        if (SourceCount > Source->MaximumConnections
            || TargetCount > Target->MaximumConnections)
        {
            return false;
        }
        Pairs.Add(Pair);
    }
    return true;
}

bool RestoreClaimedBaseKitAdapterPorts(UWorld* World,
    const ULBPressShopSaveGame* SaveRoot)
{
    if (!World || !SaveRoot) return false;
    TSet<FName> AdapterIds;
    for (const FLBBodyWeldBaseKitDeliveryRecord& Delivery :
        SaveRoot->PlayerProductionOrders.PendingBaseKitDeliveries)
        AdapterIds.Add(Delivery.DeliveryAuthorityId);
    for (const FLBBodyWeldBaseKitDeliveryRecord& Delivery :
        SaveRoot->PlayerProductionOrders.TransferredBaseKitDeliveries)
        AdapterIds.Add(Delivery.DeliveryAuthorityId);

    for (const FName AdapterId : AdapterIds)
    {
        ALBFactoryBuildMachine* Adapter = nullptr;
        for (TActorIterator<ALBFactoryBuildMachine> It(World); It; ++It)
        {
            if (!IsValid(*It) || It->IsActorBeingDestroyed()
                || It->GetMachineId() != AdapterId) continue;
            if (Adapter) return false;
            Adapter = *It;
        }
        if (!Adapter
            || Adapter->GetMachineType()
                != ELBFactoryBuildMachineType::OutboundPanelDock
            || !Adapter->OutputPort)
        {
            return false;
        }
        // The compatibility adapter deliberately reuses the stage-9 outbound
        // dock shell, but its persisted topology carries a finite GeneralParts
        // BIW kit rather than a panel stillage. Reapply that deterministic port
        // contract before recreating links because generic-machine save state
        // intentionally contains no mutable port schema.
        Adapter->OutputPort->Direction = ELBFactoryPortDirection::Output;
        Adapter->OutputPort->TransportKind = ELBFactoryTransportKind::AGVHandoff;
        Adapter->OutputPort->MaterialClass = ELBFactoryMaterialClass::GeneralParts;
        Adapter->OutputPort->ProcessStage = LBFactoryProcessStage::WeldShopIntake;
        Adapter->OutputPort->MaximumAutomaticLinkDistanceCm = 2500.0f;
        Adapter->OutputPort->MaximumConnections = 4;
    }
    return true;
}
}

bool ALBPressShopCampaignController::CaptureCampaign(ULBPressShopSaveGame* SaveRoot)
{
    UWorld* World = GetWorld();
    if (!SaveRoot || !World || SaveRoot->SaveFormatVersion != CurrentCampaignSaveFormat) return false;
    ULBPressTrainIdentitySubsystem* Trains = World->GetSubsystem<ULBPressTrainIdentitySubsystem>();
    ULBFactoryConnectionSubsystem* Connections = World->GetSubsystem<ULBFactoryConnectionSubsystem>();
    ULBFactoryMachineBuilderSubsystem* Machines = World->GetSubsystem<ULBFactoryMachineBuilderSubsystem>();
    ULBFactoryBrandSubsystem* Brand = World->GetSubsystem<ULBFactoryBrandSubsystem>();
    ULBFactoryManagementSubsystem* Management =
        World->GetSubsystem<ULBFactoryManagementSubsystem>();
    ALBPressShopBuildAuthority* BuildAuthority = FindSingle<ALBPressShopBuildAuthority>(World);
    ALBStillageFLTFleetController* StillageFleet = FindSingle<ALBStillageFLTFleetController>(World);
    if (!Trains || !Connections || !Machines || !Brand || !Management
        || !BuildAuthority || !StillageFleet)
    {
        return false;
    }

    const int32 ConsoleCount = CountActors<ALBControlRoomOperationsConsole>(World);
    if (ConsoleCount > 1) return false;
    if (ConsoleCount == 1)
    {
        SaveRoot->TopologyMode = ELBCampaignTopologyMode::LegacyAuthoredPressShop;
        ALBPR004Station* PR004 = FindSingle<ALBPR004Station>(World);
        ALBPR005Station* PR005 = FindSingle<ALBPR005Station>(World);
        ALBPR006Station* PR006 = FindSingle<ALBPR006Station>(World);
        ALBPR007Station* PR007 = FindSingle<ALBPR007Station>(World);
        ALBPR008Station* PR008 = FindSingle<ALBPR008Station>(World);
        ALBPR009Station* PR009 = FindSingle<ALBPR009Station>(World);
        ALBPR010Station* PR010 = FindSingle<ALBPR010Station>(World);
        ALBControlRoomOperationsConsole* Console =
            FindSingle<ALBControlRoomOperationsConsole>(World);
        if (!PR004 || !PR005 || !PR006 || !PR007 || !PR008 || !PR009 || !PR010
            || !Console || !PR004->GetStableSaveState(SaveRoot->PR004))
        {
            return false;
        }
        SaveRoot->PR005 = PR005->CaptureSaveState();
        SaveRoot->PR006 = PR006->CaptureSaveState();
        SaveRoot->PR007 = PR007->CaptureSaveState();
        SaveRoot->PR008 = PR008->CaptureSaveState();
        SaveRoot->PR009 = PR009->CaptureSaveState();
        SaveRoot->PR010 = PR010->CaptureSaveState();
        SaveRoot->ControlRoomOperations = Console->CaptureSaveState();
    }
    else
    {
        SaveRoot->TopologyMode = ELBCampaignTopologyMode::PlayerBuiltFactory;
        // Never carry stale legacy authority state through a reused save object.
        SaveRoot->PR004 = FLBPR004SaveState();
        SaveRoot->PR005 = FLBPR005SaveState();
        SaveRoot->PR006 = FLBPR006SaveState();
        SaveRoot->PR007 = FLBPR007SaveState();
        SaveRoot->PR008 = FLBPR008SaveState();
        SaveRoot->PR009 = FLBPR009SaveState();
        SaveRoot->PR010 = FLBPR010SaveState();
        SaveRoot->ControlRoomOperations = FLBControlRoomOperationsSaveState();
    }

    SaveRoot->FactoryBrand = Brand->CaptureSaveState();
    SaveRoot->FactoryManagement = Management->CaptureSaveState();
    FString ManagementReason;
    if (!SaveRoot->FactoryManagement.bCampaignInitialised
        || !ULBFactoryManagementSubsystem::ValidateSaveState(
            SaveRoot->FactoryManagement, ManagementReason))
    {
        return false;
    }
    if (!Trains->CaptureAllTrains(SaveRoot)) return false;
    if (!Connections->CaptureConnections(SaveRoot->FactoryTransportLinks)) return false;
    if (!BuildAuthority->CaptureStorageZones(SaveRoot->PlayerStorageZones)) return false;
    if (!Machines->CaptureMachines(SaveRoot->PlayerBuiltMachines)) return false;
    if (!Machines->CaptureBodyWeldLines(SaveRoot->PlayerBuiltBodyWeldLines)) return false;
    if (!Machines->CaptureECoatLines(SaveRoot->PlayerBuiltECoatLines)) return false;
    if (!Machines->CaptureAGVInfrastructure(SaveRoot->PlayerBuiltAGVInfrastructure)) return false;
    if (!StillageFleet->CaptureSaveState(SaveRoot->StillageFLTFleet)) return false;
    // Capture into a reusable SaveGame object must never retain a flow payload
    // from a controller that no longer exists in this world.
    SaveRoot->PlayerProductionOrders = FLBPlayerBuiltPressFlowSaveState();
    if (ALBPlayerBuiltPressFlowController* PlayerFlow = FindSingle<ALBPlayerBuiltPressFlowController>(World))
        SaveRoot->PlayerProductionOrders = PlayerFlow->CaptureSaveState();

    SaveRoot->bHasInboundDelivery = false;
    ALBInboundDeliveryController* InboundDelivery = FindSingle<ALBInboundDeliveryController>(World);
    ALBCoilAGVController* InboundAGV = FindSingle<ALBCoilAGVController>(World);
    if (InboundDelivery || InboundAGV)
    {
        if (!InboundDelivery || !InboundAGV || !InboundAGV->GetSaveState(SaveRoot->InboundCoilAGV)) return false;
        SaveRoot->InboundDelivery = InboundDelivery->CaptureSaveState();
        if (SaveRoot->InboundDelivery.InboundDockId.IsNone()
            || SaveRoot->InboundDelivery.PR002MachineId.IsNone()) return false;
        SaveRoot->bHasInboundDelivery = true;
    }

    SaveRoot->CleaningRobots.Reset();
    SaveRoot->MaintenanceRobots.Reset();
    if (ALBPressShopSupportFleetController* Fleet = FindSingle<ALBPressShopSupportFleetController>(World))
        if (!Fleet->CaptureFleetSaveState(SaveRoot)) return false;
    if (ALBSupportCraneController* Crane = FindSingle<ALBSupportCraneController>(World))
        if (!Crane->GetSaveState(SaveRoot->FrontEndSupportCrane)) return false;
    SaveRoot->CampaignId = TEXT("THE_RESTART_PRESS_SHOP");
    SaveRoot->SavedAtUtc = FDateTime::UtcNow();
    return true;
}

bool ALBPressShopCampaignController::PreflightCampaign(const ULBPressShopSaveGame* SaveRoot) const
{
    UWorld* World = GetWorld();
    if (!SaveRoot || !World || (SaveRoot->SaveFormatVersion != 13
        && SaveRoot->SaveFormatVersion != 14 && SaveRoot->SaveFormatVersion != 15
        && SaveRoot->SaveFormatVersion != 16 && SaveRoot->SaveFormatVersion != 17
        && SaveRoot->SaveFormatVersion != CurrentCampaignSaveFormat)
        || SaveRoot->CampaignId != TEXT("THE_RESTART_PRESS_SHOP")) return false;

    ELBCampaignTopologyMode Topology;
    FLBFactoryManagementSaveState ManagementState;
    FString ManagementReason;
    ULBFactoryBrandSubsystem* Brand = World->GetSubsystem<ULBFactoryBrandSubsystem>();
    if (!ResolveCampaignTopologyAndManagement(SaveRoot, Topology, ManagementState)
        || !ULBFactoryManagementSubsystem::ValidateSaveState(
            ManagementState, ManagementReason) || !Brand)
    {
        return false;
    }
    const FLBFactoryBrandSaveState& BrandState = SaveRoot->FactoryBrand;
    FString BrandColourReason;
    bool bBrandNameHasPrintableCharacter = false;
    for (const TCHAR Character : BrandState.FactoryName)
    {
        if (FChar::IsPrint(Character) && !FChar::IsWhitespace(Character))
        {
            bBrandNameHasPrintableCharacter = true;
            break;
        }
    }
    const auto IsFiniteUnitColour = [](const FLinearColor& Colour)
    {
        return FMath::IsFinite(Colour.R) && FMath::IsFinite(Colour.G)
            && FMath::IsFinite(Colour.B) && FMath::IsFinite(Colour.A)
            && Colour.R >= 0.0f && Colour.R <= 1.0f
            && Colour.G >= 0.0f && Colour.G <= 1.0f
            && Colour.B >= 0.0f && Colour.B <= 1.0f;
    };
    if ((BrandState.Version != 1 && BrandState.Version != 2)
        || !bBrandNameHasPrintableCharacter
        || (BrandState.Version == 1
            && (!IsFiniteUnitColour(BrandState.PrimaryColour)
                || !IsFiniteUnitColour(BrandState.SecondaryColour)))
        || (BrandState.Version == 2
            && !ULBFactoryBrandSubsystem::ValidateMachineLiveryColours(
                BrandState.PrimaryColour, BrandState.SecondaryColour,
                BrandColourReason)))
    {
        return false;
    }

    if (Topology == ELBCampaignTopologyMode::LegacyAuthoredPressShop)
    {
        ALBPR004Station* PR004 = FindSingle<ALBPR004Station>(World);
        TArray<FText> Errors;
        if (!PR004 || !PR004->IsSaveStateCoherent(SaveRoot->PR004, Errors)
            || SaveRoot->PR005.StationId != TEXT("PR-005")
            || SaveRoot->PR006.StationId != TEXT("PR-006")
            || SaveRoot->PR007.StationId != TEXT("PR-007")
            || SaveRoot->PR008.StationId != TEXT("PR-008")
            || SaveRoot->PR009.StationId != TEXT("PR-009")
            || SaveRoot->PR010.StationId != TEXT("PR-010")
            || !FindSingle<ALBPR005Station>(World) || !FindSingle<ALBPR006Station>(World)
            || !FindSingle<ALBPR007Station>(World) || !FindSingle<ALBPR008Station>(World)
            || !FindSingle<ALBPR009Station>(World) || !FindSingle<ALBPR010Station>(World)
            || CountActors<ALBControlRoomOperationsConsole>(World) != 1)
        {
            return false;
        }
    }
    else if (Topology == ELBCampaignTopologyMode::PlayerBuiltFactory)
    {
        // A player-built save is restored only into the console-free factory shell.
        // It deliberately has no dependency on PR-004..PR-010 authored actors.
        if (CountActors<ALBControlRoomOperationsConsole>(World) != 0) return false;
    }
    else
    {
        return false;
    }

    const bool bHasFleetData = !SaveRoot->CleaningRobots.IsEmpty() || !SaveRoot->MaintenanceRobots.IsEmpty();
    if (bHasFleetData && (SaveRoot->CleaningRobots.Num() != 2 || SaveRoot->MaintenanceRobots.Num() != 2
        || !FindSingle<ALBPressShopSupportFleetController>(World))) return false;
    ALBStillageFLTFleetController* StillageFleet = FindSingle<ALBStillageFLTFleetController>(World);
    if (!StillageFleet) return false;
    if (SaveRoot->SaveFormatVersion >= FirstStillageFleetSaveFormat)
    {
        if (!IsStillageFleetSaveStateValid(SaveRoot->StillageFLTFleet)) return false;
    }
    else
    {
        FLBStillageFLTFleetSaveState FreshLegacyFleet;
        if (!IsLegacyDefaultStillageFleetState(SaveRoot->StillageFLTFleet)
            || !BuildFreshLegacyStillageFleetState(StillageFleet, FreshLegacyFleet)) return false;
    }
    if (SaveRoot->SaveFormatVersion >= 14 && SaveRoot->bHasInboundDelivery
        && (SaveRoot->InboundDelivery.SaveVersion < 1
            || SaveRoot->InboundDelivery.SaveVersion > 6
            || SaveRoot->InboundDelivery.InboundDockId.IsNone()
            || SaveRoot->InboundDelivery.PR002MachineId.IsNone()
            || SaveRoot->InboundDelivery.CompletedDeliveries < 0
            || (SaveRoot->InboundDelivery.SaveVersion >= 6
                && !StaticEnum<ELBInboundDeliverySourceMode>()->IsValidEnumValue(
                    static_cast<int64>(SaveRoot->InboundDelivery.SourceMode)))
            || !StaticEnum<ELBInboundDeliveryPhase>()->IsValidEnumValue(
                static_cast<int64>(SaveRoot->InboundDelivery.Phase))
            || (SaveRoot->InboundDelivery.Phase != ELBInboundDeliveryPhase::Idle
                && SaveRoot->InboundDelivery.ActiveCoilId.IsNone())
            || !FindSingle<ALBInboundDeliveryController>(World) || !FindSingle<ALBCoilAGVController>(World))) return false;
    if (ALBSupportCraneController* Crane = FindSingle<ALBSupportCraneController>(World))
    {
        FLBSupportCraneSaveState CurrentCraneState;
        const FLBSupportCraneSaveState& SavedCrane = SaveRoot->FrontEndSupportCrane;
        if (!Crane->GetSaveState(CurrentCraneState)
            || SavedCrane.SaveVersion != 1
            || SavedCrane.ServicePointId != CurrentCraneState.ServicePointId
            || !StaticEnum<ELBSupportCranePhase>()->IsValidEnumValue(
                static_cast<int64>(SavedCrane.Phase))
            || !StaticEnum<ELBSupportCranePhase>()->IsValidEnumValue(
                static_cast<int64>(SavedCrane.PhaseBeforeFault))
            || !StaticEnum<ELBSupportCraneFault>()->IsValidEnumValue(
                static_cast<int64>(SavedCrane.Fault))
            || !FMath::IsFinite(SavedCrane.BridgeX)
            || !FMath::IsFinite(SavedCrane.TrolleyY)
            || !FMath::IsFinite(SavedCrane.HookZ))
        {
            return false;
        }
    }
    ULBFactoryMachineBuilderSubsystem* Machines = World->GetSubsystem<ULBFactoryMachineBuilderSubsystem>();
    if (!Machines) return false;
    FString DynamicSaveReason;
    if (!Machines->ValidateMachineSaveSet(SaveRoot->PlayerBuiltMachines, DynamicSaveReason)) return false;
    ALBPressShopBuildAuthority* BuildAuthority = FindSingle<ALBPressShopBuildAuthority>(World);
    if (!BuildAuthority
        || !BuildAuthority->ValidateStorageSaveSet(
            SaveRoot->PlayerStorageZones, DynamicSaveReason)) return false;
    {
        TSet<FName> InfrastructureIds;
        TSet<int32> HandoffTrainIndices;
        int32 ChargerCount = 0;
        for (const FLBFactoryAGVInfrastructureSaveState& State :
            SaveRoot->PlayerBuiltAGVInfrastructure)
        {
            const bool bHandoff = State.Type
                == ELBFactoryAGVInfrastructureType::PressTrainHandoff;
            if ((State.Version != 1 && State.Version != 2)
                || State.InfrastructureId.IsNone()
                || InfrastructureIds.Contains(State.InfrastructureId)
                || !StaticEnum<ELBFactoryAGVInfrastructureType>()->IsValidEnumValue(
                    static_cast<int64>(State.Type))
                || (State.Version >= 2
                    && !StaticEnum<ELBFactoryInfrastructureProvenance>()->IsValidEnumValue(
                        static_cast<int64>(State.Provenance)))
                || !State.WorldTransform.IsValid()
                || !State.WorldTransform.GetScale3D().Equals(FVector::OneVector, 0.001f)
                || (State.Type == ELBFactoryAGVInfrastructureType::ChargingStation
                    && ++ChargerCount > 4)
                || (bHandoff && (!FMath::IsWithinInclusive(State.TrainIndex, 0, 3)
                    || HandoffTrainIndices.Contains(State.TrainIndex)))
                || (!bHandoff && State.TrainIndex != INDEX_NONE))
            {
                return false;
            }
            InfrastructureIds.Add(State.InfrastructureId);
            if (bHandoff) HandoffTrainIndices.Add(State.TrainIndex);
        }
    }
    if (!ALBPlayerBuiltPressFlowController::ValidateSaveState(
            SaveRoot->PlayerProductionOrders, DynamicSaveReason)) return false;
    // Body-weld lines first exist in v18. Older roots may carry only the normal
    // empty default; accepting a non-empty future field would let an old version
    // bypass the dedicated line validator and its exact-ID ownership contract.
    if ((SaveRoot->SaveFormatVersion < FirstBodyWeldSaveFormat
            && !SaveRoot->PlayerBuiltBodyWeldLines.IsEmpty())
        || (SaveRoot->SaveFormatVersion >= FirstBodyWeldSaveFormat
            && !Machines->ValidateBodyWeldLineSaveSet(
                SaveRoot->PlayerBuiltBodyWeldLines, DynamicSaveReason))) return false;
    // v13/v14 files predate this field. Their normal empty default migrates cleanly, while
    // version-smuggled v15 ED-line data is rejected before any campaign actor is mutated.
    if ((SaveRoot->SaveFormatVersion < FirstECoatSaveFormat
            && !SaveRoot->PlayerBuiltECoatLines.IsEmpty())
        || (SaveRoot->SaveFormatVersion >= FirstECoatSaveFormat
            && !Machines->ValidateECoatLineSaveSet(SaveRoot->PlayerBuiltECoatLines,
                DynamicSaveReason))) return false;
    if ((SaveRoot->SaveFormatVersion >= FirstBodyWeldSaveFormat
            && !ValidateSavedCompositeLayout(SaveRoot))
        || !ValidateBodyWeldOwnershipContract(SaveRoot)
        || !ValidateECoatBodyOwnershipContract(SaveRoot)
        || (Topology == ELBCampaignTopologyMode::PlayerBuiltFactory
            && SaveRoot->SaveFormatVersion >= FirstBodyWeldSaveFormat
            && (!ValidateSavedConnectionIdentities(SaveRoot)
                || !ValidateStillageFleetFlowJobContract(SaveRoot)
                || !ValidatePendingBaseKitTopologyContract(SaveRoot)))) return false;
    return FindSingle<ALBPressShopBuildAuthority>(World)
        && World->GetSubsystem<ULBPressTrainIdentitySubsystem>()
        && World->GetSubsystem<ULBFactoryConnectionSubsystem>()
        && Brand
        && World->GetSubsystem<ULBFactoryManagementSubsystem>()
        && Machines;
}

bool ALBPressShopCampaignController::RestoreCampaign(const ULBPressShopSaveGame* SaveRoot)
{
    if (!PreflightCampaign(SaveRoot)) return false;
    UWorld* World = GetWorld();
    ULBPressTrainIdentitySubsystem* Trains = World->GetSubsystem<ULBPressTrainIdentitySubsystem>();
    ULBFactoryConnectionSubsystem* Connections = World->GetSubsystem<ULBFactoryConnectionSubsystem>();
    ULBFactoryMachineBuilderSubsystem* Machines = World->GetSubsystem<ULBFactoryMachineBuilderSubsystem>();
    ULBFactoryBrandSubsystem* Brand = World->GetSubsystem<ULBFactoryBrandSubsystem>();
    ULBFactoryManagementSubsystem* Management =
        World->GetSubsystem<ULBFactoryManagementSubsystem>();
    ALBPressShopBuildAuthority* BuildAuthority = FindSingle<ALBPressShopBuildAuthority>(World);
    ALBStillageFLTFleetController* StillageFleet = FindSingle<ALBStillageFLTFleetController>(World);

    ELBCampaignTopologyMode Topology;
    FLBFactoryManagementSaveState ManagementState;
    if (!ResolveCampaignTopologyAndManagement(
            SaveRoot, Topology, ManagementState)) return false;

    const bool bRollbackPass = ActiveCampaignRollbackPasses.Contains(this);
    ULBPressShopSaveGame* PreviousCampaign = nullptr;
    TSet<TWeakObjectPtr<AActor>> PriorManagedActors;
    bool bPreviouslyHadPlayerFlow = false;
    if (!bRollbackPass)
    {
        PreviousCampaign = NewObject<ULBPressShopSaveGame>(this);
        // A rollback snapshot is useful only if the same campaign transaction can
        // replay it. Prove that before the incoming root is allowed to mutate brand,
        // actors, fleet or management; an inconsistent live factory therefore fails
        // closed at the transaction boundary instead of discovering that during
        // recovery from a later endpoint rejection.
        if (!PreviousCampaign || !CaptureCampaign(PreviousCampaign)
            || !PreflightCampaign(PreviousCampaign))
        {
            return false;
        }
        CaptureManagedActorSet(World, PriorManagedActors);
        bPreviouslyHadPlayerFlow =
            CountActors<ALBPlayerBuiltPressFlowController>(World) == 1;
    }

    const auto FailRestore = [&]()
    {
        if (bRollbackPass) return false;

        // Remove only actors introduced by the failed commit before replaying
        // the complete root snapshot. Endpoints may have legitimately replaced
        // an old actor, so the rollback restore remains responsible for
        // recreating any prior saved identity that no longer has a live actor.
        DestroyIntroducedManagedActorSet(World, PriorManagedActors);
        FScopedCampaignRollbackPass Guard(this);
        const bool bRestored = RestoreCampaign(PreviousCampaign);

        // Player-built restore creates the flow controller on demand even when
        // the pre-commit shell did not yet have one. Preserve that exact actor
        // absence as well as the serialized root state.
        if (bRestored && !bPreviouslyHadPlayerFlow)
        {
            TArray<TWeakObjectPtr<ALBPlayerBuiltPressFlowController>> Flows;
            for (TActorIterator<ALBPlayerBuiltPressFlowController> It(World); It; ++It)
                if (IsValid(*It) && !It->IsActorBeingDestroyed()) Flows.Add(*It);
            for (const TWeakObjectPtr<ALBPlayerBuiltPressFlowController>& Flow : Flows)
                if (Flow.IsValid()) Flow->Destroy();
        }
        ensureMsgf(bRestored,
            TEXT("Campaign rollback replay failed after a late restore rejection"));
        return false;
    };

    // Every endpoint validates its version/identity and converts saved motion to a safe stationary restart state.
    if (!Brand || !Management || !Brand->RestoreSaveState(SaveRoot->FactoryBrand))
        return FailRestore();
    if (Topology == ELBCampaignTopologyMode::LegacyAuthoredPressShop)
    {
        ALBPR004Station* PR004 = FindSingle<ALBPR004Station>(World);
        ALBPR005Station* PR005 = FindSingle<ALBPR005Station>(World);
        ALBPR006Station* PR006 = FindSingle<ALBPR006Station>(World);
        ALBPR007Station* PR007 = FindSingle<ALBPR007Station>(World);
        ALBPR008Station* PR008 = FindSingle<ALBPR008Station>(World);
        ALBPR009Station* PR009 = FindSingle<ALBPR009Station>(World);
        ALBPR010Station* PR010 = FindSingle<ALBPR010Station>(World);
        if (!PR004 || !PR005 || !PR006 || !PR007 || !PR008 || !PR009 || !PR010
            || !PR004->RestoreSaveState(SaveRoot->PR004)
            || !PR005->RestoreSaveState(SaveRoot->PR005)
            || !PR006->RestoreSaveState(SaveRoot->PR006)
            || !PR007->RestoreSaveState(SaveRoot->PR007)
            || !PR008->RestoreSaveState(SaveRoot->PR008)
            || !PR009->RestoreSaveState(SaveRoot->PR009)
            || !PR010->RestoreSaveState(SaveRoot->PR010))
        {
            return FailRestore();
        }
    }
    if (!Trains->RestoreAllTrains(SaveRoot)) return FailRestore();
    FString MachineRestoreReason;
    if (!Machines->RestoreMachines(SaveRoot->PlayerBuiltMachines, MachineRestoreReason))
        return FailRestore();
    if (!RestoreClaimedBaseKitAdapterPorts(World, SaveRoot)) return FailRestore();
    FString BodyWeldRestoreReason;
    if (!Machines->RestoreBodyWeldLines(
            SaveRoot->PlayerBuiltBodyWeldLines, BodyWeldRestoreReason)) return FailRestore();
    FString ECoatRestoreReason;
    if (!Machines->RestoreECoatLines(SaveRoot->PlayerBuiltECoatLines, ECoatRestoreReason))
        return FailRestore();
    FString AGVInfrastructureRestoreReason;
    if (!Machines->RestoreAGVInfrastructure(SaveRoot->PlayerBuiltAGVInfrastructure,
            AGVInfrastructureRestoreReason)) return FailRestore();
    FString StorageRestoreReason;
    if (!BuildAuthority->RestoreStorageZones(
            SaveRoot->PlayerStorageZones, StorageRestoreReason)) return FailRestore();
    // Restore topology only after every dynamic machine and storage endpoint exists.
    FString ConnectionRestoreReason;
    if (!Connections->RestoreConnections(
            SaveRoot->FactoryTransportLinks, ConnectionRestoreReason)) return FailRestore();
    if (SaveRoot->SaveFormatVersion >= FirstStillageFleetSaveFormat)
    {
        if (!StillageFleet->RestoreSaveState(SaveRoot->StillageFLTFleet))
            return FailRestore();
    }
    else
    {
        FLBStillageFLTFleetSaveState FreshLegacyFleet;
        if (!BuildFreshLegacyStillageFleetState(StillageFleet, FreshLegacyFleet)
            || !StillageFleet->RestoreSaveState(FreshLegacyFleet)) return FailRestore();
    }
    ALBPlayerBuiltPressFlowController* PlayerFlow =
        FindSingle<ALBPlayerBuiltPressFlowController>(World);
    if (!PlayerFlow && Topology == ELBCampaignTopologyMode::PlayerBuiltFactory)
        PlayerFlow = World->SpawnActor<ALBPlayerBuiltPressFlowController>();
    if ((Topology == ELBCampaignTopologyMode::PlayerBuiltFactory && !PlayerFlow)
        || (PlayerFlow && !PlayerFlow->RestoreSaveState(SaveRoot->PlayerProductionOrders)))
    {
        return FailRestore();
    }
    if (SaveRoot->SaveFormatVersion >= 14 && SaveRoot->bHasInboundDelivery)
    {
        ALBFactoryBuildMachine* InboundDock = nullptr;
        ALBFactoryBuildMachine* PR002Cell = nullptr;
        for (TActorIterator<ALBFactoryBuildMachine> It(World); It; ++It)
        {
            if (It->GetMachineId() == SaveRoot->InboundDelivery.InboundDockId) InboundDock = *It;
            if (It->GetMachineId() == SaveRoot->InboundDelivery.PR002MachineId
                && It->GetMachineType() == ELBFactoryBuildMachineType::CoilWeighInspectionCell)
                PR002Cell = *It;
        }
        ALBCoilAGVController* InboundAGV = FindSingle<ALBCoilAGVController>(World);
        ALBInboundDeliveryController* InboundDelivery = FindSingle<ALBInboundDeliveryController>(World);
        const ELBInboundDeliverySourceMode SavedSourceMode =
            SaveRoot->InboundDelivery.SaveVersion >= 6
                ? SaveRoot->InboundDelivery.SourceMode
                : ELBInboundDeliverySourceMode::LegacyLorry;
        FString InboundConfigureReason;
        if (!InboundDock || !PR002Cell || !InboundAGV || !InboundDelivery
            || !InboundDelivery->ConfigureForSourceMode(InboundDock, PR002Cell,
                InboundAGV, SavedSourceMode, InboundConfigureReason)
            || !InboundAGV->RestoreInboundSaveState(
                SaveRoot->InboundCoilAGV, InboundDock, PR002Cell)
            || !InboundDelivery->RestoreSaveState(SaveRoot->InboundDelivery))
        {
            return FailRestore();
        }
    }
    if (!SaveRoot->CleaningRobots.IsEmpty())
        if (!FindSingle<ALBPressShopSupportFleetController>(World)->RestoreFleetSaveState(SaveRoot))
            return FailRestore();
    if (ALBSupportCraneController* Crane = FindSingle<ALBSupportCraneController>(World))
        if (!Crane->RestoreSaveState(SaveRoot->FrontEndSupportCrane))
            return FailRestore();
    if (Topology == ELBCampaignTopologyMode::LegacyAuthoredPressShop)
    {
        ALBControlRoomOperationsConsole* Console =
            FindSingle<ALBControlRoomOperationsConsole>(World);
        if (!Console || !Console->RestoreSaveState(
                SaveRoot->ControlRoomOperations)) return FailRestore();
    }

    // Apply finance last. Structural restore paths therefore cannot consume saved
    // cash or duplicate capital transactions; the validated snapshot is the one
    // exact post-load authority state. Pre-v17 roots receive the deterministic
    // fresh migration state built during preflight.
    if (!Management->RestoreSaveState(ManagementState)) return FailRestore();
    return true;
}

bool ALBPressShopCampaignController::SaveCampaignToSlot()
{
    ULBPressShopSaveGame* SaveRoot = Cast<ULBPressShopSaveGame>(
        UGameplayStatics::CreateSaveGameObject(ULBPressShopSaveGame::StaticClass()));
    return CaptureCampaign(SaveRoot)
        && UGameplayStatics::SaveGameToSlot(SaveRoot, CampaignSlotName, CampaignUserIndex);
}

bool ALBPressShopCampaignController::LoadCampaignFromSlot()
{
    const ULBPressShopSaveGame* SaveRoot = Cast<ULBPressShopSaveGame>(
        UGameplayStatics::LoadGameFromSlot(CampaignSlotName, CampaignUserIndex));
    return RestoreCampaign(SaveRoot);
}
