#include "LBPressShopBuildAuthority.h"
#include "LBPressShopStorageZone.h"
#include "LBFactoryConnectionSubsystem.h"
#include "LBFactoryAGVInfrastructure.h"
#include "LBPressTrainAStation.h"
#include "EngineUtils.h"

ALBPressShopBuildAuthority::ALBPressShopBuildAuthority()
{
    PrimaryActorTick.bCanEverTick = false;
}

float ALBPressShopBuildAuthority::DistanceSquaredToSegment2D(
    const FVector& Point, const FVector& Start, const FVector& End)
{
    const FVector2D P(Point.X, Point.Y);
    const FVector2D A(Start.X, Start.Y);
    const FVector2D B(End.X, End.Y);
    const FVector2D AB = B - A;
    const float Denominator = AB.SizeSquared();
    const float T = Denominator > UE_SMALL_NUMBER
        ? FMath::Clamp(FVector2D::DotProduct(P - A, AB) / Denominator, 0.0f, 1.0f) : 0.0f;
    return FVector2D::DistSquared(P, A + AB * T);
}

bool ALBPressShopBuildAuthority::EvaluateTrainTransform(
    const FTransform& WorldTransform, FString& OutReason) const
{
    if (WorldTransform.ContainsNaN() || !WorldTransform.GetScale3D().Equals(FVector::OneVector, 0.001f))
    {
        OutReason = TEXT("INVALID TRAIN TRANSFORM OR SCALE");
        return false;
    }
    return EvaluateTrainEnvelope(
        ALBPressTrainAStation::GetProtectedLocalEnvelope().TransformBy(WorldTransform), OutReason);
}

FString ALBPressShopBuildAuthority::DescribeTrainTransform(const FTransform& WorldTransform) const
{
    FString Reason;
    const bool bValid = EvaluateTrainTransform(WorldTransform, Reason);
    return FString::Printf(TEXT("%s: %s"), bValid ? TEXT("VALID") : TEXT("INVALID"), *Reason);
}

bool ALBPressShopBuildAuthority::EvaluateStorageTransform(
    ELBPressShopStorageType StorageType, const FTransform& WorldTransform,
    const FVector& HalfExtent, FString& OutReason) const
{
    OutReason.Reset();
    if (WorldTransform.ContainsNaN() || !WorldTransform.GetScale3D().Equals(FVector::OneVector, 0.001f)
        || HalfExtent.X <= 0.0f || HalfExtent.Y <= 0.0f || HalfExtent.Z <= 0.0f)
    {
        OutReason = TEXT("INVALID STORAGE TRANSFORM OR FOOTPRINT");
        return false;
    }
    if (ALBPressShopStorageZone::IsPanelStillageStorageType(StorageType)
        && HalfExtent.Z + 0.1f < ALBPressShopStorageZone::PanelStillageMinimumZoneHalfHeightCm)
    {
        OutReason = TEXT("THREE-HIGH STILLAGE STORAGE REQUIRES A 4.7 m PROTECTED HEIGHT ENVELOPE");
        return false;
    }
    if (StorageBays.IsEmpty())
    {
        OutReason = TEXT("PRESS SHOP STORAGE BAY NOT CONFIGURED");
        return false;
    }

    const FBox LocalEnvelope(-HalfExtent, HalfExtent);
    const FBox WorldEnvelope = LocalEnvelope.TransformBy(WorldTransform);
    FName AcceptedBay = NAME_None;
    for (const FLBPressShopStorageBay& Bay : StorageBays)
    {
        if (!Bay.AcceptedTypes.Contains(StorageType)) continue;
        const FBox BayBox(Bay.Centre - Bay.HalfExtent, Bay.Centre + Bay.HalfExtent);
        if (BayBox.ExpandBy(1.0f).IsInsideOrOn(WorldEnvelope.Min)
            && BayBox.ExpandBy(1.0f).IsInsideOrOn(WorldEnvelope.Max))
        {
            AcceptedBay = Bay.BayId;
            break;
        }
    }
    if (AcceptedBay.IsNone())
    {
        OutReason = TEXT("STORAGE TYPE OR COMPLETE FOOTPRINT IS NOT AUTHORISED IN THIS BAY");
        return false;
    }

    for (const FLBPressShopProtectedArea& Area : ProtectedAreas)
    {
        const FBox AreaBox(Area.Centre - Area.HalfExtent, Area.Centre + Area.HalfExtent);
        if (WorldEnvelope.Intersect(AreaBox))
        {
            OutReason = FString::Printf(TEXT("PROTECTED AREA %s MUST REMAIN CLEAR"), *Area.AreaId.ToString());
            return false;
        }
    }
    if (const UWorld* World = GetWorld())
    {
        for (TActorIterator<ALBPressShopStorageZone> It(World); It; ++It)
        {
            const ALBPressShopStorageZone* Existing = *It;
            if (!Existing) continue;
            const FBox ExistingLocal(-Existing->GetZoneHalfExtent(), Existing->GetZoneHalfExtent());
            if (WorldEnvelope.Intersect(ExistingLocal.TransformBy(Existing->GetActorTransform())))
            {
                OutReason = FString::Printf(TEXT("STORAGE ZONE %s OCCUPIES THIS FOOTPRINT"),
                    *Existing->GetZoneId().ToString());
                return false;
            }
        }
    }
    const FVector AccessPoint = WorldEnvelope.GetCenter();
    for (const FLBPressShopLogisticsSpine& Spine : LogisticsSpines)
    {
        if (DistanceSquaredToSegment2D(AccessPoint, Spine.Start, Spine.End)
            <= FMath::Square(Spine.MaximumAccessDistanceCm))
        {
            OutReason = FString::Printf(TEXT("VALID IN %s; LOGISTICS %s IN REACH"),
                *AcceptedBay.ToString(), *Spine.SpineId.ToString());
            return true;
        }
    }
    // A player-drawn route is authoritative for a player-built factory. Map-owned spines are
    // retained only for migration of older saves; new layouts do not receive a baked route.
    if (const UWorld* World = GetWorld())
    {
        for (TActorIterator<ALBFactoryAGVInfrastructure> It(World); It; ++It)
        {
            if (!IsValid(*It) || (It->GetInfrastructureType() != ELBFactoryAGVInfrastructureType::AGVRouteSegment
                && It->GetInfrastructureType() != ELBFactoryAGVInfrastructureType::RouteWaypoint)) continue;
            const FVector RouteCentre = It->GetActorLocation();
            const FVector Forward = It->GetActorForwardVector();
            const float RouteHalfLength = FMath::Max(35.0f, It->GetPlacementHalfExtentCm().X);
            if (DistanceSquaredToSegment2D(AccessPoint,
                RouteCentre - Forward * RouteHalfLength, RouteCentre + Forward * RouteHalfLength)
                <= FMath::Square(600.0f))
            {
                OutReason = FString::Printf(TEXT("VALID IN %s; PLAYER-BUILT AGV ROUTE IN REACH"),
                    *AcceptedBay.ToString());
                return true;
            }
        }
    }
    OutReason = TEXT("DRAW A PLAYER-BUILT AGV ROUTE WITHIN 6 m OF THIS STORAGE AREA");
    return false;
}

FString ALBPressShopBuildAuthority::DescribeStorageTransform(
    ELBPressShopStorageType StorageType, const FTransform& WorldTransform,
    const FVector& HalfExtent) const
{
    FString Reason;
    const bool bValid = EvaluateStorageTransform(StorageType, WorldTransform, HalfExtent, Reason);
    return FString::Printf(TEXT("%s: %s"), bValid ? TEXT("VALID") : TEXT("INVALID"), *Reason);
}

bool ALBPressShopBuildAuthority::GetStoragePlacementDefaults(
    ELBPressShopStorageType StorageType, FVector& OutHalfExtent,
    int32& OutCapacity, FString& OutReason) const
{
    OutHalfExtent = FVector::ZeroVector;
    OutCapacity = 0;
    for (const FLBPressShopStorageBay& Bay : StorageBays)
    {
        if (!Bay.AcceptedTypes.Contains(StorageType)) continue;
        if (Bay.DefaultCapacity <= 0 || Bay.DefaultZoneHalfExtent.X <= 0.0f
            || Bay.DefaultZoneHalfExtent.Y <= 0.0f || Bay.DefaultZoneHalfExtent.Z <= 0.0f)
        {
            OutReason = FString::Printf(TEXT("STORAGE DEFAULTS FOR %s ARE TBC"), *Bay.BayId.ToString());
            return false;
        }
        OutHalfExtent = Bay.DefaultZoneHalfExtent;
        OutCapacity = Bay.DefaultCapacity;
        OutReason = FString::Printf(TEXT("AUTHORISED BY %s"), *Bay.BayId.ToString());
        return true;
    }
    OutReason = TEXT("NO AUTHORED STORAGE BAY ACCEPTS THIS MATERIAL TYPE");
    return false;
}

bool ALBPressShopBuildAuthority::CalculateStorageLayout(
    ELBPressShopStorageType StorageType, const FTransform& WorldTransform,
    const FVector& HalfExtent, int32& OutColumns, int32& OutRows,
    int32& OutCapacity, FString& OutReason) const
{
    OutColumns = 0;
    OutRows = 0;
    OutCapacity = 0;
    if (WorldTransform.ContainsNaN() || HalfExtent.X <= 0.0f || HalfExtent.Y <= 0.0f)
    {
        OutReason = TEXT("INVALID STORAGE AREA");
        return false;
    }
    const FBox Envelope = FBox(-HalfExtent, HalfExtent).TransformBy(WorldTransform);
    const FLBPressShopStorageBay* AcceptedBay = nullptr;
    for (const FLBPressShopStorageBay& Bay : StorageBays)
    {
        const FBox BayBox = FBox(Bay.Centre - Bay.HalfExtent, Bay.Centre + Bay.HalfExtent).ExpandBy(1.0f);
        if (Bay.AcceptedTypes.Contains(StorageType)
            && BayBox.IsInsideOrOn(Envelope.Min) && BayBox.IsInsideOrOn(Envelope.Max))
        { AcceptedBay = &Bay; break; }
    }
    if (!AcceptedBay)
    {
        OutReason = TEXT("COMPLETE STORAGE AREA IS OUTSIDE AN AUTHORISED BAY");
        return false;
    }
    FVector2D Pitch = AcceptedBay->StorageUnitPitchCm;
    // Legacy BareCoils is the stable serialized key for the inbound wrapped-coil
    // store. Presentation uses the corrected wrapped-coil assets and wording.
    if (Pitch.X <= 0.0f || Pitch.Y <= 0.0f)
    {
        if (StorageType == ELBPressShopStorageType::BareCoils) Pitch = FVector2D(220.0f, 600.0f);
        else
        {
            OutReason = FString::Printf(TEXT("STORAGE UNIT PITCH FOR %s IS TBC"),
                *AcceptedBay->BayId.ToString());
            return false;
        }
    }
    const float UsableX = HalfExtent.X * 2.0f - AcceptedBay->BoundaryClearanceCm * 2.0f;
    const float UsableY = HalfExtent.Y * 2.0f - AcceptedBay->BoundaryClearanceCm * 2.0f;
    OutColumns = FMath::FloorToInt(UsableX / Pitch.X);
    OutRows = FMath::FloorToInt(UsableY / Pitch.Y);
    const int32 StackLevels = ALBPressShopStorageZone::IsPanelStillageStorageType(StorageType)
        ? ALBPressShopStorageZone::PanelStillageMaximumStackLevels : 1;
    OutCapacity = OutColumns * OutRows * StackLevels;
    if (OutColumns <= 0 || OutRows <= 0 || OutCapacity <= 0)
    {
        OutReason = TEXT("STORAGE AREA IS TOO SMALL FOR ONE AUTHORED POSITION");
        OutColumns = OutRows = OutCapacity = 0;
        return false;
    }
    OutReason = StackLevels > 1
        ? FString::Printf(TEXT("%d COLUMNS x %d ROWS = %d FLOOR BAYS x %d HIGH = %d STILLAGES"),
            OutColumns, OutRows, OutColumns * OutRows, StackLevels, OutCapacity)
        : FString::Printf(TEXT("%d COLUMNS x %d ROWS = %d POSITIONS"),
            OutColumns, OutRows, OutCapacity);
    return true;
}

bool ALBPressShopBuildAuthority::PlaceStorageZone(ELBPressShopStorageType StorageType,
    const FTransform& WorldTransform, const FVector& HalfExtent, int32 Capacity,
    ALBPressShopStorageZone*& OutZone, FString& OutReason)
{
    OutZone = nullptr;
    if (Capacity <= 0)
    {
        OutReason = TEXT("STORAGE CAPACITY MUST BE POSITIVE");
        return false;
    }
    if (!EvaluateStorageTransform(StorageType, WorldTransform, HalfExtent, OutReason) || !GetWorld())
    {
        return false;
    }

    int32 LayoutColumns = 0;
    int32 LayoutRows = 0;
    int32 CalculatedCapacity = 0;
    FString LayoutReason;
    if (CalculateStorageLayout(StorageType, WorldTransform, HalfExtent,
        LayoutColumns, LayoutRows, CalculatedCapacity, LayoutReason)
        && Capacity != CalculatedCapacity)
    {
        OutReason = FString::Printf(TEXT("CAPACITY MUST MATCH GENERATED LAYOUT: %s"), *LayoutReason);
        return false;
    }

    static const TCHAR* TypeCodes[] = {TEXT("COIL"), TEXT("BLANK"), TEXT("PANEL"),
        TEXT("SCRAP"), TEXT("MRO"), TEXT("QUAR"), TEXT("EMPTY-STL")};
    const int32 TypeIndex = static_cast<int32>(StorageType);
    if (TypeIndex < 0 || TypeIndex >= UE_ARRAY_COUNT(TypeCodes))
    {
        OutReason = TEXT("UNKNOWN STORAGE TYPE");
        return false;
    }
    const FName ZoneId(*FString::Printf(TEXT("SZ-%s-%03d"), TypeCodes[TypeIndex], NextStorageSequence));
    ALBPressShopStorageZone* Zone = GetWorld()->SpawnActorDeferred<ALBPressShopStorageZone>(
        ALBPressShopStorageZone::StaticClass(), WorldTransform, this, nullptr,
        ESpawnActorCollisionHandlingMethod::AlwaysSpawn);
    if (!Zone || !Zone->Configure(ZoneId, StorageType, Capacity, HalfExtent))
    {
        if (Zone) Zone->Destroy();
        OutReason = TEXT("STORAGE ZONE INITIALISATION FAILED");
        return false;
    }
    if (ALBPressShopStorageZone::IsPanelStillageStorageType(StorageType)
        && !Zone->ConfigureStacking(ALBPressShopStorageZone::PanelStillageMaximumStackLevels,
            ALBPressShopStorageZone::PanelStillageStackPitchCm))
    {
        Zone->Destroy();
        OutReason = TEXT("THREE-HIGH STILLAGE STACKING INITIALISATION FAILED");
        return false;
    }
    if (CalculatedCapacity > 0)
    {
        const FLBPressShopStorageBay* LayoutBay = StorageBays.FindByPredicate(
            [&](const FLBPressShopStorageBay& Bay)
            {
                const FBox Envelope = FBox(-HalfExtent, HalfExtent).TransformBy(WorldTransform);
                const FBox BayBox = FBox(Bay.Centre - Bay.HalfExtent,
                    Bay.Centre + Bay.HalfExtent).ExpandBy(1.0f);
                return Bay.AcceptedTypes.Contains(StorageType)
                    && BayBox.IsInsideOrOn(Envelope.Min) && BayBox.IsInsideOrOn(Envelope.Max);
            });
        FVector2D Pitch = LayoutBay ? LayoutBay->StorageUnitPitchCm : FVector2D::ZeroVector;
        if ((Pitch.X <= 0.0f || Pitch.Y <= 0.0f)
            && StorageType == ELBPressShopStorageType::BareCoils)
        {
            Pitch = FVector2D(220.0f, 600.0f);
        }
        const float Clearance = LayoutBay ? LayoutBay->BoundaryClearanceCm : 0.0f;
        if (!Zone->ConfigureLayout(LayoutColumns, LayoutRows, Pitch, Clearance))
        {
            Zone->Destroy();
            OutReason = TEXT("STORAGE STAND LAYOUT INITIALISATION FAILED");
            return false;
        }
    }
    if (StorageType == ELBPressShopStorageType::EmptyPanelStillages)
    {
        // Buying an empty-stillage store includes three physical stillages per floor bay.
        // These identities are issued once at placement and then persist/loop through the
        // press and weld logistics system; restore never recreates consumed inventory.
        for (int32 SlotIndex = 0; SlotIndex < Capacity; ++SlotIndex)
        {
            const FName StillageId(*FString::Printf(TEXT("%s-STL-%03d"),
                *ZoneId.ToString(), SlotIndex + 1));
            if (!Zone->TryStoreIdentifiedUnit(StillageId))
            {
                Zone->Destroy();
                OutReason = TEXT("EMPTY STILLAGE STARTER INVENTORY INITIALISATION FAILED");
                return false;
            }
        }
    }
    Zone->FinishSpawning(WorldTransform);
    int32 LinkCount = 0;
    if (ULBFactoryConnectionSubsystem* Connections = GetWorld()->GetSubsystem<ULBFactoryConnectionSubsystem>())
    {
        TArray<ALBFactoryTransportLink*> CreatedLinks;
        FString ConnectionReason;
        // Some retained authored maps pre-place buffers before their machinery. Keep that valid,
        // but immediately connect a player-built zone whenever its ordered predecessor exists.
        if (Connections->AutoConnectNewMachine(Zone, CreatedLinks, ConnectionReason))
            LinkCount = CreatedLinks.Num();
    }
    ++NextStorageSequence;
    OutZone = Zone;
    OutReason = FString::Printf(TEXT("%s PLACED WITH %d AUTOMATIC LINK(S)"),
        *ZoneId.ToString(), LinkCount);
    return true;
}

bool ALBPressShopBuildAuthority::CaptureStorageZones(
    TArray<FLBPressShopStorageZoneSaveState>& OutStates) const
{
    OutStates.Reset();
    if (!GetWorld()) return false;
    TSet<FName> Ids;
    for (TActorIterator<ALBPressShopStorageZone> It(GetWorld()); It; ++It)
    {
        const FLBPressShopStorageZoneSaveState State = (*It)->CaptureSaveState();
        if (State.ZoneId.IsNone() || Ids.Contains(State.ZoneId)) return false;
        Ids.Add(State.ZoneId);
        OutStates.Add(State);
    }
    OutStates.Sort([](const FLBPressShopStorageZoneSaveState& A,
        const FLBPressShopStorageZoneSaveState& B)
    { return A.ZoneId.ToString() < B.ZoneId.ToString(); });
    return true;
}

bool ALBPressShopBuildAuthority::ValidateStorageSaveSet(
    const TArray<FLBPressShopStorageZoneSaveState>& States, FString& OutReason) const
{
    TSet<FName> Ids;
    TArray<FBox> Envelopes;
    for (const FLBPressShopStorageZoneSaveState& State : States)
    {
        const bool bVersionFour = State.Version >= 4;
        const int32 SavedMaximumStackLevels = bVersionFour ? State.MaximumStackLevels : 1;
        const bool bPanelStillageStore =
            ALBPressShopStorageZone::IsPanelStillageStorageType(State.StorageType);
        const int64 SavedFloorPositionCount =
            static_cast<int64>(State.LayoutColumns) * State.LayoutRows;
        bool bStackLevelsValid = !bVersionFour
            || (SavedMaximumStackLevels == 1
                || (bPanelStillageStore
                    && SavedMaximumStackLevels
                        == ALBPressShopStorageZone::PanelStillageMaximumStackLevels));
        bStackLevelsValid = bStackLevelsValid
            && (!bVersionFour || SavedMaximumStackLevels == 1
                || FMath::IsNearlyEqual(State.StackLevelPitchCm,
                    ALBPressShopStorageZone::PanelStillageStackPitchCm, 0.1f))
            && (!bVersionFour || SavedMaximumStackLevels > 1
                || FMath::IsNearlyZero(State.StackLevelPitchCm, 0.1f));
        if (bVersionFour)
        {
            bStackLevelsValid = bStackLevelsValid
                && State.OccupiedStackLevels.Num() == State.Occupancy;
            for (int32 OccupiedIndex = 0;
                bStackLevelsValid && OccupiedIndex < State.OccupiedStackLevels.Num(); ++OccupiedIndex)
            {
                const int32 ExpectedLevel = SavedFloorPositionCount > 0
                    ? static_cast<int32>(OccupiedIndex / SavedFloorPositionCount) + 1 : 1;
                bStackLevelsValid = State.OccupiedStackLevels[OccupiedIndex] == ExpectedLevel
                    && ExpectedLevel <= SavedMaximumStackLevels;
            }
        }
        TSet<FName> UnitIds;
        for (const FName UnitId : State.StoredUnitIds)
            if (UnitId.IsNone() || UnitIds.Contains(UnitId))
            {
                OutReason = TEXT("SAVED STORAGE TRACEABILITY IDENTITIES ARE INVALID");
                return false;
            }
            else UnitIds.Add(UnitId);
        if ((State.Version < 1 || State.Version > 4) || State.ZoneId.IsNone() || Ids.Contains(State.ZoneId)
            || State.WorldTransform.ContainsNaN()
            || !State.WorldTransform.GetScale3D().Equals(FVector::OneVector, 0.001f)
            || State.ZoneHalfExtent.GetMin() <= 0.0f || State.Capacity <= 0
            || State.Occupancy < 0 || State.Occupancy > State.Capacity
            || State.ReorderPoint < 0 || State.ReorderPoint >= State.Capacity
            || State.ReplenishmentBatchSize <= 0 || State.ReplenishmentBatchSize > State.Capacity
            || State.MaximumOutstandingReplenishmentLoads <= 0
            || State.RequestedReplenishmentUnits < 0
            || State.RequestedReplenishmentUnits > State.ReplenishmentBatchSize
                * State.MaximumOutstandingReplenishmentLoads
            || State.Occupancy + State.RequestedReplenishmentUnits > State.Capacity
            || State.StoredUnitIds.Num() > State.Occupancy || !bStackLevelsValid
            || (bVersionFour && SavedMaximumStackLevels > 1
                && State.ZoneHalfExtent.Z + 0.1f
                    < ALBPressShopStorageZone::PanelStillageMinimumZoneHalfHeightCm))
        {
            OutReason = TEXT("SAVED STORAGE STATE IS INVALID OR DUPLICATED");
            return false;
        }
        if (State.Version >= 2 && (State.LayoutColumns <= 0 || State.LayoutRows <= 0
            || SavedFloorPositionCount * SavedMaximumStackLevels != State.Capacity
            || State.StorageUnitPitchCm.X <= 0.0f || State.StorageUnitPitchCm.Y <= 0.0f
            || State.BoundaryClearanceCm < 0.0f))
        {
            OutReason = TEXT("SAVED STORAGE LAYOUT IS INVALID");
            return false;
        }
        Ids.Add(State.ZoneId);
        const FBox Envelope = FBox(-State.ZoneHalfExtent, State.ZoneHalfExtent)
            .TransformBy(State.WorldTransform);
        bool bBayAccepted = false;
        for (const FLBPressShopStorageBay& Bay : StorageBays)
        {
            const FBox BayBox = FBox(Bay.Centre - Bay.HalfExtent, Bay.Centre + Bay.HalfExtent).ExpandBy(1.0f);
            if (Bay.AcceptedTypes.Contains(State.StorageType)
                && BayBox.IsInsideOrOn(Envelope.Min) && BayBox.IsInsideOrOn(Envelope.Max))
            { bBayAccepted = true; break; }
        }
        if (!bBayAccepted)
        {
            OutReason = FString::Printf(TEXT("SAVED STORAGE %s IS OUTSIDE AN AUTHORISED BAY"),
                *State.ZoneId.ToString());
            return false;
        }
        for (const FLBPressShopProtectedArea& Area : ProtectedAreas)
            if (Envelope.Intersect(FBox(Area.Centre - Area.HalfExtent, Area.Centre + Area.HalfExtent)))
            {
                OutReason = FString::Printf(TEXT("SAVED STORAGE %s INTERSECTS PROTECTED AREA %s"),
                    *State.ZoneId.ToString(), *Area.AreaId.ToString());
                return false;
            }
        bool bLogisticsInReach = false;
        for (const FLBPressShopLogisticsSpine& Spine : LogisticsSpines)
            if (DistanceSquaredToSegment2D(Envelope.GetCenter(), Spine.Start, Spine.End)
                <= FMath::Square(Spine.MaximumAccessDistanceCm))
            { bLogisticsInReach = true; break; }
        if (!bLogisticsInReach)
        {
            if (const UWorld* World = GetWorld())
                for (TActorIterator<ALBFactoryAGVInfrastructure> It(World); It; ++It)
                {
                    if (!IsValid(*It) || (It->GetInfrastructureType() != ELBFactoryAGVInfrastructureType::AGVRouteSegment
                        && It->GetInfrastructureType() != ELBFactoryAGVInfrastructureType::RouteWaypoint)) continue;
                    const FVector RouteCentre = It->GetActorLocation();
                    const FVector Forward = It->GetActorForwardVector();
                    const float HalfLength = FMath::Max(35.0f, It->GetPlacementHalfExtentCm().X);
                    if (DistanceSquaredToSegment2D(Envelope.GetCenter(), RouteCentre - Forward * HalfLength,
                        RouteCentre + Forward * HalfLength) <= FMath::Square(600.0f))
                    { bLogisticsInReach = true; break; }
                }
        }
        if (!bLogisticsInReach)
        {
            OutReason = FString::Printf(TEXT("SAVED STORAGE %s HAS NO LOGISTICS ACCESS"),
                *State.ZoneId.ToString());
            return false;
        }
        for (const FBox& ExistingEnvelope : Envelopes)
            if (Envelope.Intersect(ExistingEnvelope))
            {
                OutReason = TEXT("SAVED STORAGE ZONES OVERLAP");
                return false;
            }
        Envelopes.Add(Envelope);
    }
    OutReason = TEXT("SAVED STORAGE SET IS VALID");
    return true;
}

bool ALBPressShopBuildAuthority::RestoreStorageZones(
    const TArray<FLBPressShopStorageZoneSaveState>& States, FString& OutReason)
{
    UWorld* World = GetWorld();
    if (!World || !ValidateStorageSaveSet(States, OutReason)) return false;
    TMap<FName, ALBPressShopStorageZone*> ExistingById;
    for (TActorIterator<ALBPressShopStorageZone> It(World); It; ++It)
    {
        if (!(*It) || (*It)->GetZoneId().IsNone() || ExistingById.Contains((*It)->GetZoneId()))
        {
            OutReason = TEXT("LIVE STORAGE IDENTITIES ARE MISSING OR DUPLICATED");
            return false;
        }
        ExistingById.Add((*It)->GetZoneId(), *It);
    }
    TArray<ALBPressShopStorageZone*> Spawned;
    TSet<FName> RestoredIds;
    int32 MaximumSequence = 0;
    for (const FLBPressShopStorageZoneSaveState& State : States)
    {
        ALBPressShopStorageZone* Zone = ExistingById.FindRef(State.ZoneId);
        if (!Zone)
        {
            Zone = World->SpawnActor<ALBPressShopStorageZone>(ALBPressShopStorageZone::StaticClass(),
                State.WorldTransform, FActorSpawnParameters());
            if (Zone) Spawned.Add(Zone);
        }
        if (!Zone || !Zone->RestoreSaveState(State))
        {
            for (ALBPressShopStorageZone* NewZone : Spawned) if (NewZone) NewZone->Destroy();
            OutReason = TEXT("SAVED STORAGE SET COULD NOT BE RESTORED");
            return false;
        }
        RestoredIds.Add(State.ZoneId);
        FString IdString = State.ZoneId.ToString();
        FString Prefix;
        FString Suffix;
        if (IdString.Split(TEXT("-"), &Prefix, &Suffix, ESearchCase::IgnoreCase, ESearchDir::FromEnd))
            MaximumSequence = FMath::Max(MaximumSequence, FCString::Atoi(*Suffix));
    }
    for (const TPair<FName, ALBPressShopStorageZone*>& Pair : ExistingById)
        if (!RestoredIds.Contains(Pair.Key) && Pair.Value) Pair.Value->Destroy();
    NextStorageSequence = FMath::Max(1, MaximumSequence + 1);
    OutReason = FString::Printf(TEXT("RESTORED %d PLAYER STORAGE ZONE(S)"), States.Num());
    return true;
}

bool ALBPressShopBuildAuthority::EvaluateTrainEnvelope(const FBox& WorldEnvelope, FString& OutReason) const
{
    OutReason.Reset();
    if (!WorldEnvelope.IsValid || BuildBays.IsEmpty())
    {
        OutReason = TEXT("PRESS SHOP BUILD BAY NOT CONFIGURED");
        return false;
    }

    FName AcceptedBay = NAME_None;
    for (const FLBPressShopBuildBay& Bay : BuildBays)
    {
        // One-centimetre tolerance absorbs rotated-box floating-point noise only; authored bays remain authoritative.
        const FBox BayBox = FBox(Bay.Centre - Bay.HalfExtent, Bay.Centre + Bay.HalfExtent).ExpandBy(1.0f);
        if (BayBox.IsInsideOrOn(WorldEnvelope.Min) && BayBox.IsInsideOrOn(WorldEnvelope.Max))
        {
            AcceptedBay = Bay.BayId;
            break;
        }
    }
    if (AcceptedBay.IsNone())
    {
        OutReason = TEXT("COMPLETE TRAIN FOOTPRINT IS OUTSIDE AN AUTHORISED BUILD BAY");
        return false;
    }

    for (const FLBPressShopProtectedArea& Area : ProtectedAreas)
    {
        const FBox AreaBox(Area.Centre - Area.HalfExtent, Area.Centre + Area.HalfExtent);
        if (WorldEnvelope.Intersect(AreaBox))
        {
            OutReason = FString::Printf(TEXT("PROTECTED AREA %s MUST REMAIN CLEAR"), *Area.AreaId.ToString());
            return false;
        }
    }

    if (UtilitySpines.IsEmpty())
    {
        OutReason = TEXT("PRESS SHOP UTILITY SPINE NOT CONFIGURED");
        return false;
    }
    const FVector ConnectionPoint = WorldEnvelope.GetCenter();
    for (const FLBPressShopUtilitySpine& Spine : UtilitySpines)
    {
        if (DistanceSquaredToSegment2D(ConnectionPoint, Spine.Start, Spine.End)
            <= FMath::Square(Spine.MaximumConnectionDistanceCm))
        {
            OutReason = FString::Printf(TEXT("VALID IN %s; UTILITY %s IN REACH"),
                *AcceptedBay.ToString(), *Spine.SpineId.ToString());
            return true;
        }
    }
    OutReason = TEXT("NO VERIFIED PRESS SHOP UTILITY SPINE IN REACH");
    return false;
}
