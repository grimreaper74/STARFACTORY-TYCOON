#include "LBStillageFLTFleetController.h"

#include "LBBodyWeldLineActor.h"
#include "LBFactoryBuildMachine.h"
#include "LBPressShopStorageZone.h"

#include "Algo/Sort.h"
#include "Components/BoxComponent.h"
#include "Components/SceneComponent.h"
#include "Engine/World.h"
#include "EngineUtils.h"

namespace
{
    bool IsFinitePoint(const FVector& Value)
    {
        return FMath::IsFinite(Value.X) && FMath::IsFinite(Value.Y) && FMath::IsFinite(Value.Z);
    }

    bool IsOutstanding(const ELBStillageFLTJobState State)
    {
        return State == ELBStillageFLTJobState::Pending
            || State == ELBStillageFLTJobState::Claimed
            || State == ELBStillageFLTJobState::DeliveredReturning;
    }

    bool IsKnownJobType(const ELBStillageFLTJobType Type)
    {
        return Type == ELBStillageFLTJobType::FullStillageToWeld
            || Type == ELBStillageFLTJobType::EmptyStillageToPress;
    }

    bool IsKnownJobState(const ELBStillageFLTJobState State)
    {
        return State == ELBStillageFLTJobState::Pending
            || State == ELBStillageFLTJobState::Claimed
            || State == ELBStillageFLTJobState::DeliveredReturning
            || State == ELBStillageFLTJobState::Completed
            || State == ELBStillageFLTJobState::Failed;
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

    bool IsKnownPhase(const ELBCompactStillageFLTPhase Phase)
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

    bool IsKnownFault(const ELBCompactStillageFLTFault Fault)
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

    bool IsTravelPhase(const ELBCompactStillageFLTPhase Phase)
    {
        return Phase == ELBCompactStillageFLTPhase::TravelToPickup
            || Phase == ELBCompactStillageFLTPhase::TravelToDropoff
            || Phase == ELBCompactStillageFLTPhase::ReturningToBerth;
    }

    float ProjectHalfExtent(const FVector& Direction, const FVector& AxisX,
        const FVector& AxisY, const FVector2D& HalfExtent)
    {
        return FMath::Abs(FVector::DotProduct(Direction, AxisX)) * HalfExtent.X
            + FMath::Abs(FVector::DotProduct(Direction, AxisY)) * HalfExtent.Y;
    }
}

ALBStillageFLTFleetController::ALBStillageFLTFleetController()
{
    PrimaryActorTick.bCanEverTick = true;
    PrimaryActorTick.bStartWithTickEnabled = true;
    SceneRoot = CreateDefaultSubobject<USceneComponent>(TEXT("SceneRoot"));
    SetRootComponent(SceneRoot);
    UnitClass = ALBCompactStillageFLT::StaticClass();
}

void ALBStillageFLTFleetController::BeginPlay()
{
    Super::BeginPlay();
    if (bAutoInitialiseFreshFleet && !bInitialised)
    {
        InitialiseFreshFleet();
    }
}

void ALBStillageFLTFleetController::Tick(const float DeltaSeconds)
{
    Super::Tick(DeltaSeconds);
    InstalledUnits.RemoveAll([](const TObjectPtr<ALBCompactStillageFLT>& Unit)
    {
        return !IsValid(Unit);
    });
    if (bAutoDispatchJobs && DeltaSeconds >= 0.0f)
    {
        DispatchPendingJobs();
    }
}

ALBCompactStillageFLT* ALBStillageFLTFleetController::SpawnUnit(const FName InUnitId,
    const FVector& HomeBerth, const FRotator& Rotation)
{
    if (!GetWorld() || InUnitId.IsNone() || !UnitClass || GetUnitById(InUnitId))
    {
        return nullptr;
    }
    FActorSpawnParameters Params;
    Params.Owner = this;
    Params.SpawnCollisionHandlingOverride = ESpawnActorCollisionHandlingMethod::AlwaysSpawn;
    ALBCompactStillageFLT* Unit = GetWorld()->SpawnActor<ALBCompactStillageFLT>(
        UnitClass, HomeBerth, Rotation, Params);
    if (!Unit || !Unit->ConfigureUnit(InUnitId, HomeBerth))
    {
        if (Unit) Unit->Destroy();
        return nullptr;
    }
    Unit->OnStillageDelivered.AddUniqueDynamic(
        this, &ALBStillageFLTFleetController::HandleUnitDelivered);
    Unit->OnJobFinished.AddUniqueDynamic(
        this, &ALBStillageFLTFleetController::HandleUnitFinished);
    InstalledUnits.Add(Unit);
    InstalledUnits.Sort([](const ALBCompactStillageFLT& Left, const ALBCompactStillageFLT& Right)
    {
        return Left.GetUnitId().LexicalLess(Right.GetUnitId());
    });
    return Unit;
}

bool ALBStillageFLTFleetController::InitialiseFreshFleet()
{
    InstalledUnits.RemoveAll([](const TObjectPtr<ALBCompactStillageFLT>& Unit)
    {
        return !IsValid(Unit);
    });
    if (!InstalledUnits.IsEmpty())
    {
        bInitialised = true;
        return InstalledUnits.Num() >= FreshCampaignStarterUnitCount;
    }

    NextUnitSerial = 1;
    const FVector Home = GetActorTransform().TransformPosition(
        FVector(0.0f, 0.0f, VehicleRootHeightCm));
    const FName UnitId(*FString::Printf(TEXT("LB-FLT-AGV-%02d"), NextUnitSerial));
    if (!SpawnUnit(UnitId, Home, GetActorRotation()))
    {
        return false;
    }
    ++NextUnitSerial;
    bInitialised = InstalledUnits.Num() == FreshCampaignStarterUnitCount;
    return bInitialised;
}

bool ALBStillageFLTFleetController::SpawnNextPurchasedUnit()
{
    if (InstalledUnits.Num() >= MaximumFleetSize)
    {
        return false;
    }
    const FVector LocalBerth(0.0f, BerthSpacingCm * InstalledUnits.Num(), VehicleRootHeightCm);
    const FVector Home = GetActorTransform().TransformPosition(LocalBerth);
    const FName UnitId(*FString::Printf(TEXT("LB-FLT-AGV-%02d"), NextUnitSerial));
    if (!SpawnUnit(UnitId, Home, GetActorRotation()))
    {
        return false;
    }
    ++NextUnitSerial;
    return true;
}

bool ALBStillageFLTFleetController::TryPurchaseAdditionalFLT(int32& InOutAvailableFunds)
{
    if (!InitialiseFreshFleet() || InOutAvailableFunds < AdditionalFLTPurchaseCost
        || InstalledUnits.Num() >= MaximumFleetSize)
    {
        return false;
    }
    if (!SpawnNextPurchasedUnit())
    {
        return false;
    }
    InOutAvailableFunds -= AdditionalFLTPurchaseCost;
    return true;
}

bool ALBStillageFLTFleetController::ResolveAuthorityEnvelope(AActor* Actor,
    FName& OutAuthorityId, FVector& OutCentre, FVector2D& OutHalfExtent,
    FVector& OutAxisX, FVector& OutAxisY) const
{
    if (!IsValid(Actor))
    {
        return false;
    }
    OutAxisX = Actor->GetActorForwardVector().GetSafeNormal2D();
    OutAxisY = Actor->GetActorRightVector().GetSafeNormal2D();
    if (const ALBPressShopStorageZone* Storage = Cast<ALBPressShopStorageZone>(Actor))
    {
        const FVector Extent = Storage->GetZoneHalfExtent();
        OutAuthorityId = Storage->GetZoneId();
        OutCentre = Storage->GetActorLocation();
        OutHalfExtent = FVector2D(Extent.X, Extent.Y);
    }
    else if (const ALBBodyWeldLineActor* WeldLine = Cast<ALBBodyWeldLineActor>(Actor))
    {
        const UBoxComponent* Envelope = WeldLine->GetProtectedEnvelope();
        if (!Envelope) return false;
        for (TActorIterator<ALBBodyWeldLineActor> It(GetWorld()); It; ++It)
            if (IsValid(*It) && *It != WeldLine
                && It->GetLineId() == WeldLine->GetLineId()) return false;
        const FTransform EnvelopeTransform = Envelope->GetComponentTransform();
        const FVector Extent = Envelope->GetScaledBoxExtent();
        OutAuthorityId = WeldLine->GetLineId();
        OutCentre = EnvelopeTransform.GetLocation();
        OutHalfExtent = FVector2D(Extent.X, Extent.Y);
        OutAxisX = EnvelopeTransform.GetUnitAxis(EAxis::X).GetSafeNormal2D();
        OutAxisY = EnvelopeTransform.GetUnitAxis(EAxis::Y).GetSafeNormal2D();
    }
    else if (const ALBFactoryBuildMachine* Machine = Cast<ALBFactoryBuildMachine>(Actor))
    {
        const FVector Extent = Machine->GetProtectedEnvelopeHalfExtent();
        OutAuthorityId = Machine->GetMachineId();
        OutCentre = Machine->GetActorTransform().TransformPositionNoScale(
            Machine->GetProtectedEnvelopeRelativeCentre());
        OutHalfExtent = FVector2D(Extent.X, Extent.Y);
    }
    else
    {
        const FBox Bounds = Actor->GetComponentsBoundingBox(true);
        if (!Bounds.IsValid)
        {
            return false;
        }
        OutAuthorityId = Actor->GetFName();
        OutCentre = Bounds.GetCenter();
        const FVector Extent = Bounds.GetExtent();
        OutHalfExtent = FVector2D(Extent.X, Extent.Y);
        OutAxisX = FVector::ForwardVector;
        OutAxisY = FVector::RightVector;
    }
    return !OutAuthorityId.IsNone() && IsFinitePoint(OutCentre)
        && OutHalfExtent.X > 0.0f && OutHalfExtent.Y > 0.0f
        && !OutAxisX.IsNearlyZero() && !OutAxisY.IsNearlyZero();
}

bool ALBStillageFLTFleetController::BuildActorJob(AActor* SourceActor,
    AActor* TargetActor, const FName StillageId, const ELBStillageFLTJobType JobType,
    const int32 TargetStackTier, const FName TargetStackPadId,
    const FVector2D& StillageHalfExtentCm, FName& OutJobId)
{
    OutJobId = NAME_None;
    if (StillageId.IsNone() || SourceActor == TargetActor)
    {
        return false;
    }
    if (const ALBPressShopStorageZone* SourceStorage = Cast<ALBPressShopStorageZone>(SourceActor))
    {
        // The source keeps physical ownership until the delivery delegate. Never
        // generate, substitute or withdraw a different stillage ID here.
        if (!SourceStorage->ContainsIdentifiedUnit(StillageId))
        {
            return false;
        }
    }
    if (const ALBPressShopStorageZone* TargetStorage = Cast<ALBPressShopStorageZone>(TargetActor))
    {
        const bool bAutomaticStoragePlacement = TargetStackTier == 0
            && ALBPressShopStorageZone::IsPanelStillageStorageType(
                TargetStorage->GetStorageType());
        if ((bAutomaticStoragePlacement && TargetStorage->GetAvailableCapacity() <= 0)
            || (bAutomaticStoragePlacement
                && TargetStorage->ContainsIdentifiedUnit(StillageId)))
        {
            return false;
        }
    }

    FName SourceId;
    FName TargetId;
    FVector SourceCentre;
    FVector TargetCentre;
    FVector2D SourceExtent;
    FVector2D TargetExtent;
    FVector SourceAxisX;
    FVector SourceAxisY;
    FVector TargetAxisX;
    FVector TargetAxisY;
    if (!ResolveAuthorityEnvelope(SourceActor, SourceId, SourceCentre, SourceExtent,
            SourceAxisX, SourceAxisY)
        || !ResolveAuthorityEnvelope(TargetActor, TargetId, TargetCentre, TargetExtent,
            TargetAxisX, TargetAxisY) || SourceId == TargetId)
    {
        return false;
    }
    const FVector Direction = (TargetCentre - SourceCentre).GetSafeNormal2D();
    if (Direction.IsNearlyZero())
    {
        return false;
    }
    const float SourceProjection = ProjectHalfExtent(
        Direction, SourceAxisX, SourceAxisY, SourceExtent);
    const float TargetProjection = ProjectHalfExtent(
        Direction, TargetAxisX, TargetAxisY, TargetExtent);
    const ALBCompactStillageFLT* PlanningUnit = nullptr;
    for (const ALBCompactStillageFLT* Unit : InstalledUnits)
    {
        if (IsValid(Unit))
        {
            PlanningUnit = Unit;
            break;
        }
    }
    if (!PlanningUnit)
    {
        const UClass* PlanningClass = UnitClass
            ? UnitClass.Get() : ALBCompactStillageFLT::StaticClass();
        PlanningUnit = PlanningClass
            ? Cast<ALBCompactStillageFLT>(PlanningClass->GetDefaultObject()) : nullptr;
    }
    const float LoadedPlanningStandOff = PlanningUnit
        ? PlanningUnit->GetRequiredServicePointStandOffCm(StillageHalfExtentCm)
        : ServicePointStandOffCm;
    const float EffectiveStandOff = FMath::Max(
        ServicePointStandOffCm, LoadedPlanningStandOff);
    const FVector Pickup = SourceCentre + Direction * (SourceProjection + EffectiveStandOff);
    const FVector Dropoff = TargetCentre - Direction * (TargetProjection + EffectiveStandOff);
    if (FVector::Dist2D(Pickup, Dropoff) < MinimumServiceLaneLengthCm)
    {
        // Reject layouts that leave no physical room for the rear-steer chassis
        // to clear one authority and straighten onto the next locator pad.
        return false;
    }
    int32 ResolvedStackTier = TargetStackTier;
    FName ResolvedPadId = TargetStackPadId;
    const ALBPressShopStorageZone* TargetStorage =
        Cast<ALBPressShopStorageZone>(TargetActor);
    if (TargetStorage
        && ALBPressShopStorageZone::IsPanelStillageStorageType(
            TargetStorage->GetStorageType()))
    {
        const ELBPressShopStorageType ExpectedStorageType =
            JobType == ELBStillageFLTJobType::FullStillageToWeld
                ? ELBPressShopStorageType::FinishedPanelStillages
                : ELBPressShopStorageType::EmptyPanelStillages;
        if (TargetStorage->GetStorageType() != ExpectedStorageType)
        {
            return false;
        }
    }
    if (ResolvedStackTier == 0)
    {
        if (TargetStorage
            && ALBPressShopStorageZone::IsPanelStillageStorageType(
                TargetStorage->GetStorageType()))
        {
            if (!ResolveFirstFreeStorageStackAddress(
                    TargetStorage, ResolvedStackTier, ResolvedPadId))
            {
                return false;
            }
        }
        else
        {
            // Process docks and composite weld actors are single service pads,
            // not three-high inventory stores.
            ResolvedStackTier = 1;
            ResolvedPadId = TargetId;
        }
    }
    else if (ResolvedPadId.IsNone())
    {
        ResolvedPadId = TargetId;
    }
    return EnqueueExactJobToStackTier(StillageId, JobType, SourceId, TargetId,
        Pickup, Dropoff, ResolvedStackTier, ResolvedPadId, Direction.Rotation().Yaw,
        StillageHalfExtentCm, OutJobId);
}

bool ALBStillageFLTFleetController::ResolveFirstFreeStorageStackAddress(
    const ALBPressShopStorageZone* TargetStorage,
    int32& OutTargetStackTier, FName& OutTargetStackPadId) const
{
    OutTargetStackTier = 0;
    OutTargetStackPadId = NAME_None;
    if (!IsValid(TargetStorage)
        || !ALBPressShopStorageZone::IsPanelStillageStorageType(
            TargetStorage->GetStorageType()))
    {
        return false;
    }

    const int32 Capacity = TargetStorage->GetCapacity();
    const int32 Occupancy = TargetStorage->GetOccupancy();
    if (Capacity <= 0 || Occupancy < 0 || Occupancy > Capacity)
    {
        return false;
    }
    FName LastPadId;
    int32 LastTier = 0;
    if (!TargetStorage->GetStackAddressForStorageIndex(
            Capacity - 1, LastPadId, LastTier)
        || LastPadId.IsNone() || LastTier < 1
        || LastTier > ALBCompactStillageFLT::MaximumSupportedStackTier)
    {
        // A three-high store without its authored grid (or any storage whose
        // capacity cannot be represented by its address contract) is not safe
        // to route automatically.
        return false;
    }

    // Occupied inventory follows the storage authority's compact fill order.
    // Outstanding jobs reserve their exact saved address without increasing
    // occupancy, so enqueue never teleports or duplicates a physical stillage.
    TSet<int32> UnavailableIndices;
    for (int32 OccupiedIndex = 0; OccupiedIndex < Occupancy; ++OccupiedIndex)
    {
        UnavailableIndices.Add(OccupiedIndex);
    }
    const FLBPressShopStorageZoneSaveState StorageState =
        TargetStorage->CaptureSaveState();
    const int32 AnonymousOccupiedUnits = FMath::Max(0,
        Occupancy - StorageState.StoredUnitIds.Num());
    for (const FLBStillageFLTJob& Job : Jobs)
    {
        if (!IsOutstanding(Job.State)
            || Job.TargetAuthorityId != TargetStorage->GetZoneId())
        {
            continue;
        }
        int32 ReservedIndex = INDEX_NONE;
        if (!TargetStorage->GetStorageIndexForStackAddress(
                Job.TargetStackPadId, Job.TargetStackTier, ReservedIndex))
        {
            return false;
        }
        if (ReservedIndex < Occupancy)
        {
            const int32 StoredUnitIndex =
                StorageState.StoredUnitIds.IndexOfByKey(Job.StillageId);
            const int32 IdentifiedStorageIndex = StoredUnitIndex == INDEX_NONE
                ? INDEX_NONE : AnonymousOccupiedUnits + StoredUnitIndex;
            if (IdentifiedStorageIndex != ReservedIndex)
            {
                // The address is occupied by a different physical stillage.
                // Do not move the reservation or compact ownership silently.
                return false;
            }
            continue;
        }
        if (UnavailableIndices.Contains(ReservedIndex))
        {
            // Duplicate live reservation. Do not guess another bay around a
            // corrupted ownership ledger.
            return false;
        }
        UnavailableIndices.Add(ReservedIndex);
    }

    for (int32 CandidateIndex = 0; CandidateIndex < Capacity; ++CandidateIndex)
    {
        if (UnavailableIndices.Contains(CandidateIndex))
        {
            continue;
        }
        return TargetStorage->GetStackAddressForStorageIndex(CandidateIndex,
            OutTargetStackPadId, OutTargetStackTier);
    }
    return false;
}

bool ALBStillageFLTFleetController::EnqueueFullStillageTransfer(const FName StillageId,
    AActor* FullPressWipStorage, AActor* WeldIntake,
    const FVector2D StillageHalfExtentCm, FName& OutJobId)
{
    return BuildActorJob(FullPressWipStorage, WeldIntake, StillageId,
        ELBStillageFLTJobType::FullStillageToWeld, 0, NAME_None,
        StillageHalfExtentCm, OutJobId);
}

bool ALBStillageFLTFleetController::EnqueueFullStillageTransferToStackTier(
    const FName StillageId, AActor* FullPressWipStorage, AActor* WeldIntake,
    const int32 TargetStackTier, const FName TargetStackPadId,
    const FVector2D StillageHalfExtentCm, FName& OutJobId)
{
    return BuildActorJob(FullPressWipStorage, WeldIntake, StillageId,
        ELBStillageFLTJobType::FullStillageToWeld, TargetStackTier,
        TargetStackPadId, StillageHalfExtentCm, OutJobId);
}

bool ALBStillageFLTFleetController::EnqueueEmptyStillageReturn(const FName StillageId,
    AActor* WeldEmptyStillageStorage, AActor* PressEmptyStillageStorage,
    const FVector2D StillageHalfExtentCm, FName& OutJobId)
{
    return BuildActorJob(WeldEmptyStillageStorage, PressEmptyStillageStorage, StillageId,
        ELBStillageFLTJobType::EmptyStillageToPress, 0, NAME_None,
        StillageHalfExtentCm, OutJobId);
}

bool ALBStillageFLTFleetController::EnqueueEmptyStillageReturnToStackTier(
    const FName StillageId, AActor* WeldEmptyStillageStorage,
    AActor* PressEmptyStillageStorage, const int32 TargetStackTier,
    const FName TargetStackPadId, const FVector2D StillageHalfExtentCm,
    FName& OutJobId)
{
    return BuildActorJob(WeldEmptyStillageStorage, PressEmptyStillageStorage, StillageId,
        ELBStillageFLTJobType::EmptyStillageToPress, TargetStackTier,
        TargetStackPadId, StillageHalfExtentCm, OutJobId);
}

bool ALBStillageFLTFleetController::EnqueueExactJob(const FName StillageId,
    const ELBStillageFLTJobType JobType, const FName SourceAuthorityId,
    const FName TargetAuthorityId, const FVector PickupServicePoint,
    const FVector DropoffServicePoint, const FVector2D StillageHalfExtentCm,
    FName& OutJobId)
{
    const FVector Approach = (DropoffServicePoint - PickupServicePoint).GetSafeNormal2D();
    const float PadYawDegrees = Approach.IsNearlyZero()
        ? 0.0f : Approach.Rotation().Yaw;
    return EnqueueExactJobToStackTier(StillageId, JobType, SourceAuthorityId,
        TargetAuthorityId, PickupServicePoint, DropoffServicePoint, 1,
        TargetAuthorityId, PadYawDegrees, StillageHalfExtentCm, OutJobId);
}

bool ALBStillageFLTFleetController::EnqueueExactJobToStackTier(
    const FName StillageId, const ELBStillageFLTJobType JobType,
    const FName SourceAuthorityId, const FName TargetAuthorityId,
    const FVector PickupServicePoint, const FVector DropoffServicePoint,
    const int32 TargetStackTier, const FName TargetStackPadId,
    const float TargetStackPadYawDegrees, const FVector2D StillageHalfExtentCm,
    FName& OutJobId)
{
    OutJobId = NAME_None;
    if (!InitialiseFreshFleet() || StillageId.IsNone() || SourceAuthorityId.IsNone()
        || TargetAuthorityId.IsNone() || SourceAuthorityId == TargetAuthorityId
        || TargetStackPadId.IsNone() || TargetStackTier < 1
        || TargetStackTier > ALBCompactStillageFLT::MaximumSupportedStackTier
        || !FMath::IsFinite(TargetStackPadYawDegrees)
        || !IsFinitePoint(PickupServicePoint) || !IsFinitePoint(DropoffServicePoint)
        || FVector::Dist2D(PickupServicePoint, DropoffServicePoint) < 50.0f
        || !FMath::IsFinite(StillageHalfExtentCm.X)
        || !FMath::IsFinite(StillageHalfExtentCm.Y)
        || StillageHalfExtentCm.X < 20.0f || StillageHalfExtentCm.X > 250.0f
        || StillageHalfExtentCm.Y < 20.0f || StillageHalfExtentCm.Y > 250.0f
        || HasOutstandingJobForStillage(StillageId))
    {
        return false;
    }
    if (IsDeterministicStorageStackPad(TargetAuthorityId, TargetStackPadId)
        && Jobs.ContainsByPredicate(
            [TargetAuthorityId, TargetStackPadId, TargetStackTier](
                const FLBStillageFLTJob& Existing)
            {
                return IsOutstanding(Existing.State)
                    && Existing.TargetAuthorityId == TargetAuthorityId
                    && Existing.TargetStackPadId == TargetStackPadId
                    && Existing.TargetStackTier == TargetStackTier;
            }))
    {
        return false;
    }

    FLBStillageFLTJob Job;
    Job.JobId = FName(*FString::Printf(TEXT("LB-FLT-JOB-%06lld"),
        static_cast<long long>(NextJobSequence)));
    Job.StillageId = StillageId;
    Job.JobType = JobType;
    Job.SourceAuthorityId = SourceAuthorityId;
    Job.TargetAuthorityId = TargetAuthorityId;
    Job.TargetStackPadId = TargetStackPadId;
    Job.TargetStackTier = TargetStackTier;
    Job.TargetStackPadYawDegrees = FMath::UnwindDegrees(TargetStackPadYawDegrees);
    Job.PickupServicePoint = PickupServicePoint;
    Job.DropoffServicePoint = DropoffServicePoint;
    Job.StillageHalfExtentCm = StillageHalfExtentCm;
    Job.State = ELBStillageFLTJobState::Pending;
    Job.CreatedSequence = NextJobSequence++;
    Jobs.Add(Job);
    OutJobId = Job.JobId;
    if (bAutoDispatchJobs)
    {
        DispatchPendingJobs();
    }
    return true;
}

bool ALBStillageFLTFleetController::CanDispatchDirection(
    const FLBStillageFLTJob& Candidate) const
{
    // Full and empty traffic share a narrow first-playable logistics aisle.
    // Convoys in one direction may run together; reverse jobs wait until that
    // direction clears, avoiding head-on deadlock while extra FLTs add capacity.
    for (const FLBStillageFLTJob& Job : Jobs)
    {
        if ((Job.State == ELBStillageFLTJobState::Claimed
                || Job.State == ELBStillageFLTJobState::DeliveredReturning)
            && Job.JobType != Candidate.JobType)
        {
            return false;
        }
    }
    return true;
}

int32 ALBStillageFLTFleetController::DispatchPendingJobs()
{
    int32 ClaimedCount = 0;
    for (FLBStillageFLTJob& Job : Jobs)
    {
        if (Job.State != ELBStillageFLTJobState::Pending || !CanDispatchDirection(Job))
        {
            continue;
        }
        ALBCompactStillageFLT* Available = nullptr;
        for (ALBCompactStillageFLT* Unit : InstalledUnits)
        {
            if (IsValid(Unit) && Unit->IsAvailableForJob())
            {
                Available = Unit;
                break;
            }
        }
        if (!Available)
        {
            break;
        }

        // Claim is committed before dispatch. StartJob receives the exact
        // claimed snapshot; a failed route plan rolls the claim back atomically.
        Job.State = ELBStillageFLTJobState::Claimed;
        Job.ClaimedUnitId = Available->GetUnitId();
        if (!Available->StartJob(Job))
        {
            Job.State = ELBStillageFLTJobState::Pending;
            Job.ClaimedUnitId = NAME_None;
            continue;
        }
        ++ClaimedCount;
    }
    return ClaimedCount;
}

void ALBStillageFLTFleetController::HandleUnitDelivered(const FName UnitId,
    const FName JobId, const FName StillageId, const bool bStillageWasFull)
{
    FLBStillageFLTJob* Job = Jobs.FindByPredicate([JobId](const FLBStillageFLTJob& Candidate)
    {
        return Candidate.JobId == JobId;
    });
    if (!Job || Job->State != ELBStillageFLTJobState::Claimed
        || Job->ClaimedUnitId != UnitId || Job->StillageId != StillageId
        || bStillageWasFull != (Job->JobType == ELBStillageFLTJobType::FullStillageToWeld))
    {
        return;
    }
    Job->State = ELBStillageFLTJobState::DeliveredReturning;
    OnStillageDelivered.Broadcast(Job->JobId, Job->StillageId, Job->JobType,
        Job->SourceAuthorityId, Job->TargetAuthorityId);
}

void ALBStillageFLTFleetController::HandleUnitFinished(const FName UnitId,
    const FName JobId, const bool bSucceeded)
{
    FLBStillageFLTJob* Job = Jobs.FindByPredicate([JobId](const FLBStillageFLTJob& Candidate)
    {
        return Candidate.JobId == JobId;
    });
    if (!Job || Job->ClaimedUnitId != UnitId
        || (Job->State != ELBStillageFLTJobState::Claimed
            && Job->State != ELBStillageFLTJobState::DeliveredReturning))
    {
        return;
    }
    Job->State = bSucceeded && Job->State == ELBStillageFLTJobState::DeliveredReturning
        ? ELBStillageFLTJobState::Completed : ELBStillageFLTJobState::Failed;
    Job->ClaimedUnitId = NAME_None;
}

bool ALBStillageFLTFleetController::GetJobSnapshot(const FName JobId,
    FLBStillageFLTJob& OutJob) const
{
    const FLBStillageFLTJob* Job = Jobs.FindByPredicate([JobId](const FLBStillageFLTJob& Candidate)
    {
        return Candidate.JobId == JobId;
    });
    if (!Job)
    {
        return false;
    }
    OutJob = *Job;
    return true;
}

TArray<FLBStillageFLTJob> ALBStillageFLTFleetController::GetJobSnapshots() const
{
    TArray<FLBStillageFLTJob> Snapshots = Jobs;
    Snapshots.Sort([](const FLBStillageFLTJob& Left, const FLBStillageFLTJob& Right)
    {
        if (Left.CreatedSequence != Right.CreatedSequence)
            return Left.CreatedSequence < Right.CreatedSequence;
        return Left.JobId.LexicalLess(Right.JobId);
    });
    return Snapshots;
}

bool ALBStillageFLTFleetController::HasOutstandingJobForStillage(
    const FName StillageId) const
{
    return !StillageId.IsNone() && Jobs.ContainsByPredicate(
        [StillageId](const FLBStillageFLTJob& Job)
        {
            return Job.StillageId == StillageId && IsOutstanding(Job.State);
        });
}

int32 ALBStillageFLTFleetController::GetPendingJobCount() const
{
    int32 Count = 0;
    for (const FLBStillageFLTJob& Job : Jobs)
    {
        Count += Job.State == ELBStillageFLTJobState::Pending ? 1 : 0;
    }
    return Count;
}

int32 ALBStillageFLTFleetController::GetActiveJobCount() const
{
    int32 Count = 0;
    for (const FLBStillageFLTJob& Job : Jobs)
    {
        Count += Job.State == ELBStillageFLTJobState::Claimed
            || Job.State == ELBStillageFLTJobState::DeliveredReturning ? 1 : 0;
    }
    return Count;
}

ALBCompactStillageFLT* ALBStillageFLTFleetController::GetUnitById(const FName UnitId) const
{
    const TObjectPtr<ALBCompactStillageFLT>* Found = InstalledUnits.FindByPredicate(
        [UnitId](const TObjectPtr<ALBCompactStillageFLT>& Unit)
        {
            return IsValid(Unit) && Unit->GetUnitId() == UnitId;
        });
    return Found ? Found->Get() : nullptr;
}

bool ALBStillageFLTFleetController::CaptureSaveState(
    FLBStillageFLTFleetSaveState& OutState) const
{
    if (!bInitialised || InstalledUnits.Num() < FreshCampaignStarterUnitCount)
    {
        return false;
    }
    OutState = FLBStillageFLTFleetSaveState();
    OutState.NextUnitSerial = NextUnitSerial;
    OutState.NextJobSequence = NextJobSequence;
    OutState.Jobs = Jobs;
    for (const ALBCompactStillageFLT* Unit : InstalledUnits)
    {
        FLBCompactStillageFLTSaveState UnitState;
        if (!IsValid(Unit) || !Unit->CaptureSaveState(UnitState))
        {
            return false;
        }
        OutState.Units.Add(UnitState);
    }
    OutState.Units.Sort([](const FLBCompactStillageFLTSaveState& Left,
        const FLBCompactStillageFLTSaveState& Right)
    {
        return Left.UnitId.LexicalLess(Right.UnitId);
    });
    OutState.Jobs.Sort([](const FLBStillageFLTJob& Left, const FLBStillageFLTJob& Right)
    {
        return Left.CreatedSequence < Right.CreatedSequence;
    });
    return true;
}

bool ALBStillageFLTFleetController::ValidateSaveState(
    const FLBStillageFLTFleetSaveState& InState) const
{
    if (InState.Version != 1 || InState.NextUnitSerial <= FreshCampaignStarterUnitCount
        || InState.NextJobSequence <= 0
        || InState.Units.Num() < FreshCampaignStarterUnitCount
        || InState.Units.Num() > MaximumFleetSize)
    {
        return false;
    }

    TMap<FName, const FLBCompactStillageFLTSaveState*> UnitsById;
    for (const FLBCompactStillageFLTSaveState& Unit : InState.Units)
    {
        const bool bLoadIdentityValid = Unit.bCarryingStillage
            ? !Unit.CarriedStillageId.IsNone() : Unit.CarriedStillageId.IsNone();
        if (Unit.Version != 1 || Unit.UnitId.IsNone() || UnitsById.Contains(Unit.UnitId)
            || !IsKnownPhase(Unit.Phase) || !IsKnownFault(Unit.Fault)
            || !IsFinitePoint(Unit.HomeBerth) || Unit.VehicleTransform.ContainsNaN()
            || !IsFinitePoint(Unit.VehicleTransform.GetLocation())
            || !IsFinitePoint(Unit.VehicleTransform.GetScale3D())
            || !FMath::IsFinite(Unit.CurrentSpeedCmPerSecond)
            || Unit.CurrentSpeedCmPerSecond < 0.0f
            || Unit.CurrentSpeedCmPerSecond > 171.0f
            || !FMath::IsFinite(Unit.CarriageLiftCm)
            || Unit.CarriageLiftCm < 0.0f
            || Unit.CarriageLiftCm > ALBCompactStillageFLT::MaximumSupportedForkPlacementHeightCm
            || !FMath::IsFinite(Unit.RearSteerAngleDegrees)
            || FMath::Abs(Unit.RearSteerAngleDegrees)
                > ALBCompactStillageFLT::MaximumSupportedRearSteerAngleDegrees + 0.1f
            || (IsTravelPhase(Unit.Phase) && Unit.CarriageLiftCm
                > ALBCompactStillageFLT::MaximumPermittedTravelLiftCm + 0.05f)
            || !bLoadIdentityValid || (Unit.bCarriedStillageFull && !Unit.bCarryingStillage))
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
    for (const FLBStillageFLTJob& Job : InState.Jobs)
    {
        if (Job.Version != 1 || Job.JobId.IsNone() || Job.StillageId.IsNone()
            || !IsKnownJobType(Job.JobType) || !IsKnownJobState(Job.State)
            || Job.SourceAuthorityId.IsNone() || Job.TargetAuthorityId.IsNone()
            || Job.SourceAuthorityId == Job.TargetAuthorityId
            || Job.TargetStackPadId.IsNone() || Job.TargetStackTier < 1
            || Job.TargetStackTier > ALBCompactStillageFLT::MaximumSupportedStackTier
            || !FMath::IsFinite(Job.TargetStackPadYawDegrees)
            || SeenJobs.Contains(Job.JobId) || Job.CreatedSequence <= 0
            || !IsFinitePoint(Job.PickupServicePoint) || !IsFinitePoint(Job.DropoffServicePoint)
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
        if (IsOutstanding(Job.State))
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
            const FLBCompactStillageFLTSaveState* const* Unit = UnitsById.Find(Job.ClaimedUnitId);
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
    if (InState.NextJobSequence <= MaximumSequence)
    {
        return false;
    }
    for (const TPair<FName, const FLBCompactStillageFLTSaveState*>& Entry : UnitsById)
    {
        const FLBCompactStillageFLTSaveState* Unit = Entry.Value;
        if (Unit->ActiveJobId.IsNone() != (Unit->Phase == ELBCompactStillageFLTPhase::Parked))
        {
            return false;
        }
        if (!Unit->ActiveJobId.IsNone() && !SeenJobs.Contains(Unit->ActiveJobId))
        {
            return false;
        }
    }
    return true;
}

bool ALBStillageFLTFleetController::RestoreSaveState(
    const FLBStillageFLTFleetSaveState& InState)
{
    if (!ValidateSaveState(InState))
    {
        return false;
    }

    for (ALBCompactStillageFLT* Unit : InstalledUnits)
    {
        if (IsValid(Unit)) Unit->Destroy();
    }
    InstalledUnits.Reset();
    Jobs = InState.Jobs;
    NextUnitSerial = InState.NextUnitSerial;
    NextJobSequence = InState.NextJobSequence;
    bInitialised = false;

    for (const FLBCompactStillageFLTSaveState& UnitState : InState.Units)
    {
        ALBCompactStillageFLT* Unit = SpawnUnit(UnitState.UnitId, UnitState.HomeBerth,
            UnitState.VehicleTransform.Rotator());
        if (!Unit || !Unit->RestoreSaveState(UnitState))
        {
            return false;
        }
    }
    for (FLBStillageFLTJob& Job : Jobs)
    {
        if (Job.State != ELBStillageFLTJobState::Claimed
            && Job.State != ELBStillageFLTJobState::DeliveredReturning)
        {
            continue;
        }
        ALBCompactStillageFLT* Unit = GetUnitById(Job.ClaimedUnitId);
        if (!Unit || !Unit->ResumeAssignedJob(Job))
        {
            return false;
        }
    }
    bInitialised = InstalledUnits.Num() >= FreshCampaignStarterUnitCount;
    return bInitialised;
}
