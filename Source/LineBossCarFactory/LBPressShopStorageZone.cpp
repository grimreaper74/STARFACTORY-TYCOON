#include "LBPressShopStorageZone.h"
#include "LBFactoryFloorMarkingComponent.h"
#include "LBFactoryProcessPortComponent.h"
#include "Components/BoxComponent.h"
#include "Components/HierarchicalInstancedStaticMeshComponent.h"
#include "Components/SceneComponent.h"
#include "Engine/StaticMesh.h"
#include "Materials/MaterialInterface.h"
#include "UObject/ConstructorHelpers.h"

bool ALBPressShopStorageZone::IsPanelStillageStorageType(
    const ELBPressShopStorageType InStorageType)
{
    return InStorageType == ELBPressShopStorageType::FinishedPanelStillages
        || InStorageType == ELBPressShopStorageType::EmptyPanelStillages;
}

ALBPressShopStorageZone::ALBPressShopStorageZone()
{
    PrimaryActorTick.bCanEverTick = false;
    SceneRoot = CreateDefaultSubobject<USceneComponent>(TEXT("SceneRoot"));
    SetRootComponent(SceneRoot);

    ZoneVolume = CreateDefaultSubobject<UBoxComponent>(TEXT("ZoneVolume"));
    ZoneVolume->SetupAttachment(SceneRoot);
    ZoneVolume->SetCollisionEnabled(ECollisionEnabled::QueryOnly);
    ZoneVolume->SetCollisionResponseToAllChannels(ECR_Overlap);
    ZoneVolume->SetGenerateOverlapEvents(true);

    FloorMarkings = CreateDefaultSubobject<ULBFactoryFloorMarkingComponent>(TEXT("StorageFloorMarkings"));
    FloorMarkings->SetupAttachment(SceneRoot);

    IngressPoint = CreateDefaultSubobject<ULBFactoryProcessPortComponent>(TEXT("IngressPoint"));
    IngressPoint->SetupAttachment(SceneRoot);
    EgressPoint = CreateDefaultSubobject<ULBFactoryProcessPortComponent>(TEXT("EgressPoint"));
    EgressPoint->SetupAttachment(SceneRoot);

    StandBases = CreateDefaultSubobject<UHierarchicalInstancedStaticMeshComponent>(TEXT("StandBases"));
    StandBases->SetupAttachment(SceneRoot);
    StandBases->SetCollisionEnabled(ECollisionEnabled::QueryAndPhysics);
    StandBases->SetCollisionResponseToAllChannels(ECR_Block);
    StandBases->SetCanEverAffectNavigation(true);

    StandSaddles = CreateDefaultSubobject<UHierarchicalInstancedStaticMeshComponent>(TEXT("StandSaddles"));
    StandSaddles->SetupAttachment(SceneRoot);
    StandSaddles->SetCollisionEnabled(ECollisionEnabled::NoCollision);
    StandSaddles->SetCanEverAffectNavigation(false);

    StoredUnits = CreateDefaultSubobject<UHierarchicalInstancedStaticMeshComponent>(TEXT("StoredUnits"));
    StoredUnits->SetupAttachment(SceneRoot);
    StoredUnits->SetCollisionEnabled(ECollisionEnabled::NoCollision);
    StoredUnits->SetCanEverAffectNavigation(false);

    StoredLoads = CreateDefaultSubobject<UHierarchicalInstancedStaticMeshComponent>(TEXT("StoredLoads"));
    StoredLoads->SetupAttachment(SceneRoot);
    StoredLoads->SetCollisionEnabled(ECollisionEnabled::NoCollision);
    StoredLoads->SetCanEverAffectNavigation(false);

    static ConstructorHelpers::FObjectFinder<UStaticMesh> CubeMesh(TEXT("/Engine/BasicShapes/Cube.Cube"));
    static ConstructorHelpers::FObjectFinder<UStaticMesh> CylinderMesh(TEXT("/Engine/BasicShapes/Cylinder.Cylinder"));
    static ConstructorHelpers::FObjectFinder<UStaticMesh> CoilStandMesh(TEXT(
        "/Game/LineBoss/Runtime/PressShop/PR004_v997/SM_Cairnwell_AdjustableCoilSaddle_Runtime_v997.SM_Cairnwell_AdjustableCoilSaddle_Runtime_v997"));
    static ConstructorHelpers::FObjectFinder<UStaticMesh> WrappedCoilMesh(TEXT(
        "/Game/LineBoss/Candidates/PressShop/CleanRebuild_v20260809_v004/Inbound/SM_CA_MW_WrappedCoil_Repaired_v003.SM_CA_MW_WrappedCoil_Repaired_v003"));
    static ConstructorHelpers::FObjectFinder<UStaticMesh> PanelStillageMesh(TEXT(
        "/Game/LineBoss/Candidates/WeldShop/PanelStillageRuntime_v001/SM_LB_PanelStillage_Runtime_v001.SM_LB_PanelStillage_Runtime_v001"));
    static ConstructorHelpers::FObjectFinder<UMaterialInterface> GreenMaterial(TEXT(
        "/Game/LineBoss/Candidates/ControlRoom/MainControlRoom_v002/Materials/M_CA_CairnwellGreen_R_v002.M_CA_CairnwellGreen_R_v002"));
    static ConstructorHelpers::FObjectFinder<UMaterialInterface> CharcoalMaterial(TEXT(
        "/Game/LineBoss/Candidates/ControlRoom/MainControlRoom_v002/Materials/M_CA_FoundryCharcoal_R_v002.M_CA_FoundryCharcoal_R_v002"));
    static ConstructorHelpers::FObjectFinder<UMaterialInterface> YellowMaterial(TEXT(
        "/Game/LineBoss/Candidates/ControlRoom/MainControlRoom_v002/Materials/M_CA_SafetyYellow_R_v002.M_CA_SafetyYellow_R_v002"));
    static ConstructorHelpers::FObjectFinder<UMaterialInterface> SteelMaterial(TEXT(
        "/Game/LineBoss/Candidates/ControlRoom/MainControlRoom_v002/Materials/M_CA_BrushedSteel_R_v002.M_CA_BrushedSteel_R_v002"));
    if (CubeMesh.Succeeded())
    {
        PrimitiveCubeMesh = CubeMesh.Object;
        StandBases->SetStaticMesh(CubeMesh.Object);
        StandSaddles->SetStaticMesh(CubeMesh.Object);
        StoredLoads->SetStaticMesh(CubeMesh.Object);
    }
    if (CoilStandMesh.Succeeded()) ApprovedCoilStandMesh = CoilStandMesh.Object;
    if (WrappedCoilMesh.Succeeded()) ApprovedWrappedCoilMesh = WrappedCoilMesh.Object;
    if (PanelStillageMesh.Succeeded()) ApprovedPanelStillageMesh = PanelStillageMesh.Object;
    if (GreenMaterial.Succeeded()) FactoryGreenMaterial = GreenMaterial.Object;
    if (CharcoalMaterial.Succeeded()) FactoryCharcoalMaterial = CharcoalMaterial.Object;
    if (YellowMaterial.Succeeded()) FactoryYellowMaterial = YellowMaterial.Object;
    if (SteelMaterial.Succeeded()) FactorySteelMaterial = SteelMaterial.Object;
    if (CylinderMesh.Succeeded()) StoredUnits->SetStaticMesh(CylinderMesh.Object);
}

bool ALBPressShopStorageZone::Configure(FName InZoneId,
    ELBPressShopStorageType InStorageType, int32 InCapacity, const FVector& InHalfExtent)
{
    if (InZoneId.IsNone() || InCapacity <= 0 || InHalfExtent.X <= 0.0f
        || InHalfExtent.Y <= 0.0f || InHalfExtent.Z <= 0.0f || Occupancy > InCapacity)
    {
        return false;
    }
    ZoneId = InZoneId;
    StorageType = InStorageType;
    Capacity = InCapacity;
    StoredUnitIds.Reset();
    LayoutColumns = 0;
    LayoutRows = 0;
    StorageUnitPitchCm = FVector2D::ZeroVector;
    BoundaryClearanceCm = 0.0f;
    MaximumStackLevels = 1;
    StackLevelPitchCm = 0.0f;
    ReorderPoint = FMath::Max(1, Capacity / 4);
    ReplenishmentBatchSize = FMath::Max(1, Capacity / 2);
    MaximumOutstandingReplenishmentLoads = 2;
    RequestedReplenishmentUnits = 0;
    ZoneHalfExtent = InHalfExtent;
    ZoneVolume->SetBoxExtent(InHalfExtent);
    IngressPoint->SetRelativeLocation(FVector(0.0f, -InHalfExtent.Y, 0.0f));
    EgressPoint->SetRelativeLocation(FVector(0.0f, InHalfExtent.Y, 0.0f));
    IngressPoint->PortId = FName(*FString::Printf(TEXT("%s-IN"), *ZoneId.ToString()));
    EgressPoint->PortId = FName(*FString::Printf(TEXT("%s-OUT"), *ZoneId.ToString()));
    IngressPoint->Direction = ELBFactoryPortDirection::Input;
    EgressPoint->Direction = ELBFactoryPortDirection::Output;
    IngressPoint->MaximumAutomaticLinkDistanceCm = 2000.0f;
    EgressPoint->MaximumAutomaticLinkDistanceCm = 2000.0f;
    // Buffers are deliberate convergence points for parallel machines.
    IngressPoint->MaximumConnections = 4;
    EgressPoint->MaximumConnections = 4;
    switch (StorageType)
    {
    case ELBPressShopStorageType::BareCoils:
        IngressPoint->ProcessStage = EgressPoint->ProcessStage = LBFactoryProcessStage::CoilStorage;
        IngressPoint->MaterialClass = EgressPoint->MaterialClass = ELBFactoryMaterialClass::Coil;
        IngressPoint->TransportKind = EgressPoint->TransportKind = ELBFactoryTransportKind::AGVHandoff;
        break;
    case ELBPressShopStorageType::PreparedBlanks:
        IngressPoint->ProcessStage = EgressPoint->ProcessStage = LBFactoryProcessStage::PreparedBlankBuffer;
        IngressPoint->MaterialClass = EgressPoint->MaterialClass = ELBFactoryMaterialClass::Blank;
        IngressPoint->TransportKind = EgressPoint->TransportKind = ELBFactoryTransportKind::RollerConveyor;
        break;
    case ELBPressShopStorageType::FinishedPanelStillages:
        IngressPoint->ProcessStage = EgressPoint->ProcessStage = LBFactoryProcessStage::WIPPanelStillageBuffer;
        IngressPoint->MaterialClass = ELBFactoryMaterialClass::InspectedPanel;
        IngressPoint->TransportKind = ELBFactoryTransportKind::PanelTransfer;
        EgressPoint->MaterialClass = ELBFactoryMaterialClass::Stillage;
        EgressPoint->TransportKind = ELBFactoryTransportKind::AGVHandoff;
        break;
    case ELBPressShopStorageType::EmptyPanelStillages:
        // Empty-stillage inventory is a closed logistics loop rather than another
        // production-stage link. Stage zero prevents the automatic process linker from
        // inventing a material conversion while the FLT fleet moves exact StillageIds.
        IngressPoint->ProcessStage = EgressPoint->ProcessStage = 0;
        IngressPoint->MaterialClass = EgressPoint->MaterialClass = ELBFactoryMaterialClass::Stillage;
        IngressPoint->TransportKind = EgressPoint->TransportKind = ELBFactoryTransportKind::AGVHandoff;
        break;
    case ELBPressShopStorageType::Scrap:
        IngressPoint->ProcessStage = EgressPoint->ProcessStage = LBFactoryProcessStage::Inspection;
        IngressPoint->MaterialClass = EgressPoint->MaterialClass = ELBFactoryMaterialClass::Scrap;
        IngressPoint->TransportKind = EgressPoint->TransportKind = ELBFactoryTransportKind::BeltConveyor;
        break;
    case ELBPressShopStorageType::MaintenanceParts:
        IngressPoint->ProcessStage = EgressPoint->ProcessStage = 1;
        IngressPoint->MaterialClass = EgressPoint->MaterialClass = ELBFactoryMaterialClass::GeneralParts;
        IngressPoint->TransportKind = EgressPoint->TransportKind = ELBFactoryTransportKind::AGVHandoff;
        break;
    case ELBPressShopStorageType::Quarantine:
        IngressPoint->ProcessStage = EgressPoint->ProcessStage = 90;
        IngressPoint->MaterialClass = EgressPoint->MaterialClass = ELBFactoryMaterialClass::GeneralParts;
        IngressPoint->TransportKind = EgressPoint->TransportKind = ELBFactoryTransportKind::AGVHandoff;
        EgressPoint->MaximumConnections = 1;
        break;
    default:
        break;
    }
    Tags.AddUnique(TEXT("LB.FactoryBuilder.StorageZone"));
    Tags.AddUnique(FName(*FString::Printf(TEXT("LB.Storage.%s"), *ZoneId.ToString())));
    RebuildFloorMarkings();
#if WITH_EDITOR
    SetActorLabel(ZoneId.ToString());
#endif
    return true;
}

bool ALBPressShopStorageZone::ConfigureStacking(
    const int32 InMaximumStackLevels, const float InStackLevelPitchCm)
{
    const bool bPanelStillageStore = IsPanelStillageStorageType(StorageType);
    const bool bSupportedLevelCount = InMaximumStackLevels == 1
        || (bPanelStillageStore
            && InMaximumStackLevels == PanelStillageMaximumStackLevels);
    if (!bSupportedLevelCount
        || (InMaximumStackLevels > 1 && InStackLevelPitchCm <= 0.0f)
        || (LayoutColumns > 0 && LayoutRows > 0
            && static_cast<int64>(LayoutColumns) * LayoutRows * InMaximumStackLevels != Capacity))
    {
        return false;
    }
    MaximumStackLevels = InMaximumStackLevels;
    StackLevelPitchCm = InMaximumStackLevels > 1 ? InStackLevelPitchCm : 0.0f;
    RefreshStoredUnitVisuals();
    return true;
}

bool ALBPressShopStorageZone::ConfigureLayout(int32 InColumns, int32 InRows,
    const FVector2D& InStorageUnitPitchCm, float InBoundaryClearanceCm)
{
    if (InColumns <= 0 || InRows <= 0
        || static_cast<int64>(InColumns) * InRows * MaximumStackLevels != Capacity
        || InStorageUnitPitchCm.X <= 0.0f || InStorageUnitPitchCm.Y <= 0.0f
        || InBoundaryClearanceCm < 0.0f)
    {
        return false;
    }
    const float RequiredX = InColumns * InStorageUnitPitchCm.X + InBoundaryClearanceCm * 2.0f;
    const float RequiredY = InRows * InStorageUnitPitchCm.Y + InBoundaryClearanceCm * 2.0f;
    if (RequiredX > ZoneHalfExtent.X * 2.0f + 1.0f
        || RequiredY > ZoneHalfExtent.Y * 2.0f + 1.0f)
    {
        return false;
    }
    LayoutColumns = InColumns;
    LayoutRows = InRows;
    StorageUnitPitchCm = InStorageUnitPitchCm;
    BoundaryClearanceCm = InBoundaryClearanceCm;
    RebuildFloorMarkings();
    RebuildStorageVisuals();
    return true;
}

bool ALBPressShopStorageZone::GetStackAddressForStorageIndex(
    const int32 StorageIndex, FName& OutStackPadId, int32& OutStackTier) const
{
    OutStackPadId = NAME_None;
    OutStackTier = 0;
    if (ZoneId.IsNone() || StorageIndex < 0 || StorageIndex >= Capacity
        || MaximumStackLevels < 1)
    {
        return false;
    }

    // Player-placed three-high zones require their authored grid. A legacy or
    // configure-only one-high zone receives deterministic virtual bays so old
    // saves remain routable without inventing a different inventory contract.
    int32 FloorPositionCount = GetFloorPositionCount();
    if (FloorPositionCount <= 0)
    {
        if (MaximumStackLevels > 1)
        {
            return false;
        }
        if (Capacity % MaximumStackLevels != 0)
        {
            return false;
        }
        FloorPositionCount = Capacity / MaximumStackLevels;
    }
    if (FloorPositionCount <= 0
        || FloorPositionCount * MaximumStackLevels != Capacity)
    {
        return false;
    }

    const int32 FloorPositionIndex = StorageIndex % FloorPositionCount;
    OutStackTier = StorageIndex / FloorPositionCount + 1;
    if (OutStackTier < 1 || OutStackTier > MaximumStackLevels)
    {
        OutStackTier = 0;
        return false;
    }
    OutStackPadId = FName(*FString::Printf(TEXT("%s-STACK-PAD-%03d"),
        *ZoneId.ToString(), FloorPositionIndex + 1));
    return !OutStackPadId.IsNone();
}

bool ALBPressShopStorageZone::GetStorageIndexForStackAddress(
    const FName StackPadId, const int32 StackTier, int32& OutStorageIndex) const
{
    OutStorageIndex = INDEX_NONE;
    if (ZoneId.IsNone() || StackPadId.IsNone() || StackTier < 1
        || StackTier > MaximumStackLevels || MaximumStackLevels < 1)
    {
        return false;
    }

    int32 FloorPositionCount = GetFloorPositionCount();
    if (FloorPositionCount <= 0)
    {
        if (MaximumStackLevels > 1 || Capacity % MaximumStackLevels != 0)
        {
            return false;
        }
        FloorPositionCount = Capacity / MaximumStackLevels;
    }
    if (FloorPositionCount <= 0
        || FloorPositionCount * MaximumStackLevels != Capacity)
    {
        return false;
    }

    const FString Prefix = ZoneId.ToString() + TEXT("-STACK-PAD-");
    const FString Value = StackPadId.ToString();
    if (!Value.StartsWith(Prefix, ESearchCase::CaseSensitive))
    {
        return false;
    }
    const FString Suffix = Value.RightChop(Prefix.Len());
    if (Suffix.Len() != 3)
    {
        return false;
    }
    for (const TCHAR Character : Suffix)
    {
        if (!FChar::IsDigit(Character)) return false;
    }
    const int32 BayOrdinal = FCString::Atoi(*Suffix);
    if (BayOrdinal < 1 || BayOrdinal > FloorPositionCount)
    {
        return false;
    }
    OutStorageIndex = (StackTier - 1) * FloorPositionCount + BayOrdinal - 1;
    return OutStorageIndex >= 0 && OutStorageIndex < Capacity;
}

void ALBPressShopStorageZone::RebuildFloorMarkings()
{
    if (!FloorMarkings) return;
    FloorMarkings->ClearMarkings();
    if (ZoneHalfExtent.X <= 0.0f || ZoneHalfExtent.Y <= 0.0f
        || ZoneHalfExtent.Z <= 0.0f) return;

    const FVector2D Centre = FVector2D::ZeroVector;
    const FVector2D Extent(ZoneHalfExtent.X, ZoneHalfExtent.Y);
    const float FloorZ = -ZoneHalfExtent.Z;
    const bool bControlledStore = StorageType == ELBPressShopStorageType::Scrap
        || StorageType == ELBPressShopStorageType::Quarantine;

    if (bControlledStore)
    {
        // Scrap and quarantine remain visually distinct from safe inventory: red
        // keep-clear stripes, bounded by the same white storage-zone ownership line.
        const FVector2D HatchExtent(FMath::Max(20.0f, Extent.X - 18.0f),
            FMath::Max(20.0f, Extent.Y - 18.0f));
        FloorMarkings->AddDiagonalHatching(Centre, HatchExtent, FloorZ + 0.1f,
            16.0f, 72.0f, ELBFactoryFloorMarkingSemantic::KeepClearHatch, 0.8f);
    }
    else
    {
        // Safe material buffers are unmistakable painted floor, not a collection of
        // floating slot props. Keep a small inset so the white ownership line is crisp.
        const FVector2D FillExtent(FMath::Max(10.0f, Extent.X - 9.0f),
            FMath::Max(10.0f, Extent.Y - 9.0f));
        FloorMarkings->AddFilledRectangle(Centre, FillExtent, FloorZ + 0.05f,
            StorageType == ELBPressShopStorageType::EmptyPanelStillages
                ? ELBFactoryFloorMarkingSemantic::EmptyStillageStorage
                : ELBFactoryFloorMarkingSemantic::StorageFill, 0.7f);
    }

    FloorMarkings->AddRectangleOutline(Centre, Extent, FloorZ + 0.45f, 12.0f,
        ELBFactoryFloorMarkingSemantic::StorageBoundary, 1.0f);

    // Once the player confirms a generated layout, paint its individual positions.
    // These divisions are presentation only and exactly follow the persisted slot grid.
    if (LayoutColumns > 1 && StorageUnitPitchCm.X > 0.0f)
    {
        const float FirstSlotX = -0.5f * (LayoutColumns - 1) * StorageUnitPitchCm.X;
        for (int32 Column = 0; Column < LayoutColumns - 1; ++Column)
        {
            const float DividerX = FirstSlotX + (Column + 0.5f) * StorageUnitPitchCm.X;
            FloorMarkings->AddDashedLine(FVector2D(DividerX, -Extent.Y + 16.0f),
                FVector2D(DividerX, Extent.Y - 16.0f), FloorZ + 0.55f,
                4.0f, Extent.Y * 2.0f, 0.0f,
                ELBFactoryFloorMarkingSemantic::StorageBoundary, 0.8f);
        }
    }
    if (LayoutRows > 1 && StorageUnitPitchCm.Y > 0.0f)
    {
        const float FirstSlotY = -0.5f * (LayoutRows - 1) * StorageUnitPitchCm.Y;
        for (int32 Row = 0; Row < LayoutRows - 1; ++Row)
        {
            const float DividerY = FirstSlotY + (Row + 0.5f) * StorageUnitPitchCm.Y;
            FloorMarkings->AddDashedLine(FVector2D(-Extent.X + 16.0f, DividerY),
                FVector2D(Extent.X - 16.0f, DividerY), FloorZ + 0.55f,
                4.0f, Extent.X * 2.0f, 0.0f,
                ELBFactoryFloorMarkingSemantic::StorageBoundary, 0.8f);
        }
    }
}

bool ALBPressShopStorageZone::TryStore(int32 Quantity)
{
    if (Quantity <= 0 || Quantity > GetAvailableCapacity()
        || (IsPanelStillageStorageType(StorageType) && Quantity != 1)) return false;
    Occupancy += Quantity;
    RequestedReplenishmentUnits = FMath::Max(0, RequestedReplenishmentUnits - Quantity);
    RefreshStoredUnitVisuals();
    return true;
}

bool ALBPressShopStorageZone::TryWithdraw(int32 Quantity)
{
    if (Quantity <= 0 || Quantity > Occupancy
        || (IsPanelStillageStorageType(StorageType) && Quantity != 1)) return false;
    const int32 AnonymousUnits = Occupancy - StoredUnitIds.Num();
    const int32 IdentifiedToRemove = FMath::Max(0, Quantity - AnonymousUnits);
    if (IdentifiedToRemove > 0) StoredUnitIds.RemoveAt(0, IdentifiedToRemove);
    Occupancy -= Quantity;
    EvaluateReplenishmentDemand();
    RefreshStoredUnitVisuals();
    return true;
}

bool ALBPressShopStorageZone::TryStoreIdentifiedUnit(const FName UnitId)
{
    if (UnitId.IsNone() || StoredUnitIds.Contains(UnitId) || !TryStore(1)) return false;
    StoredUnitIds.Add(UnitId);
    return true;
}

bool ALBPressShopStorageZone::TryWithdrawIdentifiedUnit(FName& OutUnitId)
{
    OutUnitId = NAME_None;
    if (StoredUnitIds.IsEmpty() || Occupancy <= 0) return false;
    OutUnitId = StoredUnitIds[0];
    StoredUnitIds.RemoveAt(0);
    --Occupancy;
    EvaluateReplenishmentDemand();
    RefreshStoredUnitVisuals();
    return true;
}

bool ALBPressShopStorageZone::TryWithdrawIdentifiedUnitById(const FName UnitId)
{
    if (UnitId.IsNone() || Occupancy <= 0) return false;
    const int32 Index = StoredUnitIds.IndexOfByKey(UnitId);
    if (Index == INDEX_NONE) return false;
    StoredUnitIds.RemoveAt(Index);
    --Occupancy;
    EvaluateReplenishmentDemand();
    RefreshStoredUnitVisuals();
    return true;
}

bool ALBPressShopStorageZone::ConfigureReplenishment(int32 InReorderPoint,
    int32 InBatchSize, int32 InMaximumOutstandingLoads)
{
    if (Capacity <= 0 || InReorderPoint < 0 || InReorderPoint >= Capacity
        || InBatchSize <= 0 || InBatchSize > Capacity || InMaximumOutstandingLoads <= 0)
    {
        return false;
    }
    ReorderPoint = InReorderPoint;
    ReplenishmentBatchSize = InBatchSize;
    MaximumOutstandingReplenishmentLoads = InMaximumOutstandingLoads;
    RequestedReplenishmentUnits = 0;
    EvaluateReplenishmentDemand();
    return true;
}

int32 ALBPressShopStorageZone::GetOutstandingReplenishmentLoads() const
{
    return ReplenishmentBatchSize > 0
        ? FMath::DivideAndRoundUp(RequestedReplenishmentUnits, ReplenishmentBatchSize) : 0;
}

void ALBPressShopStorageZone::EvaluateReplenishmentDemand()
{
    // Empty stillages are a conserved closed-loop asset. They return from weld and must
    // never be silently replenished like purchased consumables.
    if (StorageType == ELBPressShopStorageType::EmptyPanelStillages)
    {
        RequestedReplenishmentUnits = 0;
        return;
    }
    if (Capacity <= 0 || Occupancy > ReorderPoint || RequestedReplenishmentUnits > 0) return;
    const int32 TargetLevel = FMath::Min(Capacity, ReorderPoint + ReplenishmentBatchSize);
    const int32 DesiredUnits = FMath::Max(0, TargetLevel - Occupancy);
    const int32 MaximumRequestedUnits = ReplenishmentBatchSize * MaximumOutstandingReplenishmentLoads;
    RequestedReplenishmentUnits = FMath::Min(DesiredUnits, MaximumRequestedUnits);
}

FLBPressShopStorageZoneSaveState ALBPressShopStorageZone::CaptureSaveState() const
{
    FLBPressShopStorageZoneSaveState State;
    State.ZoneId = ZoneId;
    State.StorageType = StorageType;
    State.WorldTransform = GetActorTransform();
    State.ZoneHalfExtent = ZoneHalfExtent;
    State.Capacity = Capacity;
    State.Occupancy = Occupancy;
    State.ReorderPoint = ReorderPoint;
    State.ReplenishmentBatchSize = ReplenishmentBatchSize;
    State.MaximumOutstandingReplenishmentLoads = MaximumOutstandingReplenishmentLoads;
    State.RequestedReplenishmentUnits = RequestedReplenishmentUnits;
    State.LayoutColumns = LayoutColumns;
    State.LayoutRows = LayoutRows;
    State.StorageUnitPitchCm = StorageUnitPitchCm;
    State.BoundaryClearanceCm = BoundaryClearanceCm;
    State.MaximumStackLevels = MaximumStackLevels;
    State.StackLevelPitchCm = StackLevelPitchCm;
    const int32 FloorPositionCount = GetFloorPositionCount();
    State.OccupiedStackLevels.Reserve(Occupancy);
    for (int32 OccupiedIndex = 0; OccupiedIndex < Occupancy; ++OccupiedIndex)
    {
        State.OccupiedStackLevels.Add(FloorPositionCount > 0
            ? OccupiedIndex / FloorPositionCount + 1 : 1);
    }
    State.StoredUnitIds = StoredUnitIds;
    return State;
}

bool ALBPressShopStorageZone::RestoreSaveState(const FLBPressShopStorageZoneSaveState& State)
{
    TSet<FName> UniqueUnitIds;
    for (const FName UnitId : State.StoredUnitIds)
        if (UnitId.IsNone() || UniqueUnitIds.Contains(UnitId)) return false; else UniqueUnitIds.Add(UnitId);
    const bool bVersionFour = State.Version >= 4;
    const int32 RestoredMaximumStackLevels = bVersionFour ? State.MaximumStackLevels : 1;
    const float RestoredStackLevelPitchCm = bVersionFour ? State.StackLevelPitchCm : 0.0f;
    const bool bPanelStillageStore = IsPanelStillageStorageType(State.StorageType);
    const int64 SavedFloorPositionCount = static_cast<int64>(State.LayoutColumns) * State.LayoutRows;
    bool bStackLevelsValid = !bVersionFour
        || (RestoredMaximumStackLevels == 1
            || (bPanelStillageStore
                && RestoredMaximumStackLevels == PanelStillageMaximumStackLevels));
    bStackLevelsValid = bStackLevelsValid
        && (!bVersionFour || RestoredMaximumStackLevels == 1
            || FMath::IsNearlyEqual(RestoredStackLevelPitchCm, PanelStillageStackPitchCm, 0.1f))
        && (!bVersionFour || RestoredMaximumStackLevels > 1
            || FMath::IsNearlyZero(RestoredStackLevelPitchCm, 0.1f));
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
                && ExpectedLevel <= RestoredMaximumStackLevels;
        }
    }
    if ((State.Version < 1 || State.Version > 4) || State.ZoneId.IsNone() || State.WorldTransform.ContainsNaN()
        || !State.WorldTransform.GetScale3D().Equals(FVector::OneVector, 0.001f)
        || State.Capacity <= 0 || State.Occupancy < 0 || State.Occupancy > State.Capacity
        || State.ReorderPoint < 0 || State.ReorderPoint >= State.Capacity
        || State.ReplenishmentBatchSize <= 0 || State.ReplenishmentBatchSize > State.Capacity
        || State.MaximumOutstandingReplenishmentLoads <= 0 || State.RequestedReplenishmentUnits < 0
        || State.RequestedReplenishmentUnits > State.ReplenishmentBatchSize * State.MaximumOutstandingReplenishmentLoads
        || State.Occupancy + State.RequestedReplenishmentUnits > State.Capacity
        || State.StoredUnitIds.Num() > State.Occupancy || !bStackLevelsValid
        || (bVersionFour && RestoredMaximumStackLevels > 1
            && State.ZoneHalfExtent.Z + 0.1f < PanelStillageMinimumZoneHalfHeightCm))
    {
        return false;
    }
    SetActorTransform(State.WorldTransform);
    Occupancy = 0;
    if (!Configure(State.ZoneId, State.StorageType, State.Capacity, State.ZoneHalfExtent)) return false;
    Occupancy = State.Occupancy;
    ReorderPoint = State.ReorderPoint;
    ReplenishmentBatchSize = State.ReplenishmentBatchSize;
    MaximumOutstandingReplenishmentLoads = State.MaximumOutstandingReplenishmentLoads;
    RequestedReplenishmentUnits = State.RequestedReplenishmentUnits;
    StoredUnitIds = State.Version >= 3 ? State.StoredUnitIds : TArray<FName>();
    if (!ConfigureStacking(RestoredMaximumStackLevels, RestoredStackLevelPitchCm)) return false;
    if (State.Version >= 2
        && (SavedFloorPositionCount * RestoredMaximumStackLevels != State.Capacity
            || !ConfigureLayout(State.LayoutColumns, State.LayoutRows,
                State.StorageUnitPitchCm, State.BoundaryClearanceCm)))
    {
        return false;
    }
    RefreshStoredUnitVisuals();
    return true;
}

int32 ALBPressShopStorageZone::GetGeneratedStandCount() const
{
    return StandBases ? StandBases->GetInstanceCount() : 0;
}

int32 ALBPressShopStorageZone::GetVisibleStoredUnitCount() const
{
    return (StoredUnits ? StoredUnits->GetInstanceCount() : 0)
        + (StoredLoads ? StoredLoads->GetInstanceCount() : 0);
}

float ALBPressShopStorageZone::GetFirstStandBottomWorldZ() const
{
    if (!StandBases || StandBases->GetInstanceCount() == 0 || !StandBases->GetStaticMesh()) return BIG_NUMBER;
    FTransform Transform;
    if (!StandBases->GetInstanceTransform(0, Transform, true)) return BIG_NUMBER;
    const FBox Bounds = StandBases->GetStaticMesh()->GetBoundingBox().TransformBy(Transform);
    return Bounds.Min.Z;
}

float ALBPressShopStorageZone::GetFirstStoredUnitBottomWorldZ() const
{
    return GetVisibleStoredUnitBottomWorldZ(0);
}

float ALBPressShopStorageZone::GetVisibleStoredUnitBottomWorldZ(const int32 VisibleUnitIndex) const
{
    const UHierarchicalInstancedStaticMeshComponent* VisualComponent =
        StorageType == ELBPressShopStorageType::BareCoils ? StoredUnits : StoredLoads;
    if (!VisualComponent || VisibleUnitIndex < 0
        || VisibleUnitIndex >= VisualComponent->GetInstanceCount()
        || !VisualComponent->GetStaticMesh()) return BIG_NUMBER;
    FTransform Transform;
    if (!VisualComponent->GetInstanceTransform(VisibleUnitIndex, Transform, true)) return BIG_NUMBER;
    const FBox Bounds = VisualComponent->GetStaticMesh()->GetBoundingBox().TransformBy(Transform);
    return Bounds.Min.Z;
}

FVector ALBPressShopStorageZone::GetSlotLocation(int32 SlotIndex) const
{
    const int32 Column = LayoutColumns > 0 ? SlotIndex % LayoutColumns : 0;
    const int32 Row = LayoutColumns > 0 ? SlotIndex / LayoutColumns : 0;
    const float StartX = -0.5f * (LayoutColumns - 1) * StorageUnitPitchCm.X;
    const float StartY = -0.5f * (LayoutRows - 1) * StorageUnitPitchCm.Y;
    return FVector(StartX + Column * StorageUnitPitchCm.X,
        StartY + Row * StorageUnitPitchCm.Y, -ZoneHalfExtent.Z + 12.5f);
}

void ALBPressShopStorageZone::RebuildStorageVisuals()
{
    if (!StandBases || !StandSaddles || !StoredUnits || !StoredLoads) return;
    StandBases->ClearInstances();
    StandSaddles->ClearInstances();
    StoredUnits->ClearInstances();
    StoredLoads->ClearInstances();
    StandBases->SetStaticMesh(StorageType == ELBPressShopStorageType::BareCoils && ApprovedCoilStandMesh
        ? ApprovedCoilStandMesh : PrimitiveCubeMesh);
    if (StorageType == ELBPressShopStorageType::BareCoils && ApprovedWrappedCoilMesh)
        StoredUnits->SetStaticMesh(ApprovedWrappedCoilMesh);
    else if (IsPanelStillageStorageType(StorageType) && ApprovedPanelStillageMesh)
        StoredLoads->SetStaticMesh(ApprovedPanelStillageMesh);
    else
        StoredLoads->SetStaticMesh(PrimitiveCubeMesh);
    // Never override the owner-approved stand/coil material slots. Pending-art storage
    // primitives use the shared controlled factory palette so they remain readable in game.
    if (StorageType != ELBPressShopStorageType::BareCoils)
    {
        if (FactoryCharcoalMaterial) StandBases->SetMaterial(0, FactoryCharcoalMaterial);
        if (FactoryYellowMaterial) StandSaddles->SetMaterial(0, FactoryYellowMaterial);
        if (!IsPanelStillageStorageType(StorageType) && FactorySteelMaterial)
            StoredLoads->SetMaterial(0, FactorySteelMaterial);
        if (!IsPanelStillageStorageType(StorageType)
            && StorageType == ELBPressShopStorageType::Scrap && FactoryGreenMaterial)
            StoredLoads->SetMaterial(0, FactoryGreenMaterial);
    }
    if (LayoutColumns <= 0 || LayoutRows <= 0) return;

    const int32 FloorPositionCount = GetFloorPositionCount();
    for (int32 SlotIndex = 0; SlotIndex < FloorPositionCount; ++SlotIndex)
    {
        const FVector Slot = GetSlotLocation(SlotIndex);
        const FVector BaseScale = StorageType == ELBPressShopStorageType::BareCoils && ApprovedCoilStandMesh
            ? FVector::OneVector
            // Empty non-coil storage is a painted/marked floor bay, not a raised pallet.
            // Retain one instance per logical slot for layout and tests, but keep it thin
            // enough that an empty buffer reads as available floor space from the camera.
            : FVector(FMath::Max(0.5f, StorageUnitPitchCm.X / 125.0f),
                FMath::Max(0.5f, StorageUnitPitchCm.Y / 125.0f), 0.025f);
        const FVector BaseLocation = StorageType == ELBPressShopStorageType::BareCoils && ApprovedCoilStandMesh
            ? FVector(Slot.X, Slot.Y, -ZoneHalfExtent.Z)
            : FVector(Slot.X, Slot.Y, -ZoneHalfExtent.Z + 1.25f);
        if (StorageType == ELBPressShopStorageType::BareCoils && ApprovedCoilStandMesh)
        {
            // One complete split-master V-block saddle per slot. The full-detail Blender
            // master retains independent chocks for a later adjustable-spacing upgrade.
            StandBases->AddInstance(FTransform(FRotator::ZeroRotator, BaseLocation, BaseScale));
        }
        else
        {
            StandBases->AddInstance(FTransform(FRotator::ZeroRotator, BaseLocation, BaseScale));
        }

        if (StorageType == ELBPressShopStorageType::BareCoils)
        {
            // The approved v005 asset is the complete empty adjustable stand, including both
            // opposing chocks. Coils remain independent inventory visuals and snap onto it.
        }
        else
        {
            // Paint a crisp boundary around every player-defined bay. This keeps empty
            // storage readable as reserved logistics floor without erecting fake racks or
            // repeated posts. Loads and stillages remain inventory-driven visuals.
            constexpr float LineWidthCm = 7.5f;
            constexpr float PaintHeightCm = 1.2f;
            const float HalfBayX = FMath::Max(30.0f, StorageUnitPitchCm.X * 0.46f);
            const float HalfBayY = FMath::Max(30.0f, StorageUnitPitchCm.Y * 0.46f);
            const float PaintZ = -ZoneHalfExtent.Z + PaintHeightCm * 0.5f + 2.6f;
            const FVector HorizontalScale(HalfBayX / 50.0f, LineWidthCm / 100.0f,
                PaintHeightCm / 100.0f);
            const FVector VerticalScale(LineWidthCm / 100.0f, HalfBayY / 50.0f,
                PaintHeightCm / 100.0f);
            StandSaddles->AddInstance(FTransform(FRotator::ZeroRotator,
                FVector(Slot.X, Slot.Y - HalfBayY, PaintZ), HorizontalScale));
            StandSaddles->AddInstance(FTransform(FRotator::ZeroRotator,
                FVector(Slot.X, Slot.Y + HalfBayY, PaintZ), HorizontalScale));
            StandSaddles->AddInstance(FTransform(FRotator::ZeroRotator,
                FVector(Slot.X - HalfBayX, Slot.Y, PaintZ), VerticalScale));
            StandSaddles->AddInstance(FTransform(FRotator::ZeroRotator,
                FVector(Slot.X + HalfBayX, Slot.Y, PaintZ), VerticalScale));
        }
    }
    RefreshStoredUnitVisuals();
}

void ALBPressShopStorageZone::RefreshStoredUnitVisuals()
{
    if (!StoredUnits || !StoredLoads) return;
    StoredUnits->ClearInstances();
    StoredLoads->ClearInstances();
    if (LayoutColumns <= 0) return;
    const int32 VisibleCount = FMath::Min(Occupancy, Capacity);
    const int32 FloorPositionCount = GetFloorPositionCount();
    if (FloorPositionCount <= 0) return;
    for (int32 OccupiedIndex = 0; OccupiedIndex < VisibleCount; ++OccupiedIndex)
    {
        const int32 FloorPositionIndex = OccupiedIndex % FloorPositionCount;
        const int32 StackLevelIndex = OccupiedIndex / FloorPositionCount;
        FVector Slot = GetSlotLocation(FloorPositionIndex);
        FRotator Rotation = FRotator::ZeroRotator;
        FVector Scale(0.85f, 0.85f, 0.65f);
        switch (StorageType)
        {
        case ELBPressShopStorageType::BareCoils:
            if (ApprovedWrappedCoilMesh)
            {
                // The repaired coil pivot is its lowest bound. Keep that bound on the floor and
                // retract the approved adjustable stands so their curved chocks meet the lower
                // circumference without floating the load or burying it through the floor.
                Slot.Z = -ZoneHalfExtent.Z + 41.0f;
                Rotation = FRotator::ZeroRotator;
                Scale = FVector::OneVector;
            }
            else
            {
                Slot.Z += 110.0f;
                Rotation = FRotator(90.0f, 0.0f, 0.0f);
                Scale = FVector(1.8f, 1.8f, 1.45f);
            }
            break;
        case ELBPressShopStorageType::PreparedBlanks:
            Slot.Z += 45.0f;
            Scale = FVector(1.45f, 1.05f, 0.45f);
            break;
        case ELBPressShopStorageType::FinishedPanelStillages:
            if (ApprovedPanelStillageMesh)
            {
                // Ground the imported Meshy stillage by its actual local bound rather than
                // assuming the old Cube pivot. The authoritative 145 cm tier pitch remains
                // unchanged, preserving the exact storage/FLT address contract.
                Slot.Z = -ZoneHalfExtent.Z
                    - ApprovedPanelStillageMesh->GetBoundingBox().Min.Z
                    + StackLevelIndex * StackLevelPitchCm;
                Scale = FVector::OneVector;
            }
            else
            {
                Slot.Z += 60.0f + StackLevelIndex * StackLevelPitchCm;
                Scale = FVector(1.25f, 0.35f, 1.45f);
            }
            break;
        case ELBPressShopStorageType::EmptyPanelStillages:
            if (ApprovedPanelStillageMesh)
            {
                Slot.Z = -ZoneHalfExtent.Z
                    - ApprovedPanelStillageMesh->GetBoundingBox().Min.Z
                    + StackLevelIndex * StackLevelPitchCm;
                Scale = FVector::OneVector;
            }
            else
            {
                Slot.Z += 60.0f + StackLevelIndex * StackLevelPitchCm;
                Scale = FVector(1.25f, 0.35f, 1.45f);
            }
            break;
        case ELBPressShopStorageType::Scrap:
            Slot.Z += 60.0f;
            Scale = FVector(0.9f, 0.9f, 1.0f);
            break;
        case ELBPressShopStorageType::MaintenanceParts:
            Slot.Z += 65.0f;
            Scale = FVector(0.75f, 0.75f, 0.85f);
            break;
        case ELBPressShopStorageType::Quarantine:
            Slot.Z += 65.0f;
            Scale = FVector(0.9f, 0.9f, 0.85f);
            break;
        default:
            break;
        }
        UHierarchicalInstancedStaticMeshComponent* VisualComponent =
            StorageType == ELBPressShopStorageType::BareCoils ? StoredUnits : StoredLoads;
        VisualComponent->AddInstance(FTransform(Rotation, Slot, Scale));
    }
}
