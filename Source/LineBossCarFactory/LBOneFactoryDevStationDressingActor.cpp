#include "LBOneFactoryDevStationDressingActor.h"

#include "Components/InstancedStaticMeshComponent.h"
#include "Engine/StaticMesh.h"
#include "Engine/World.h"
#include "EngineUtils.h"
#include "LBOneFactoryRuntimeCoordinator.h"
#include "Materials/MaterialInstanceDynamic.h"
#include "Materials/MaterialInterface.h"

namespace LBOneFactoryDressingPrivate
{
    /**
     * Factory Environment Collection meshes, measured in the editor. Pivots sit
     * at the base of each mesh, so a placement Z of zero stands it on the floor.
     *
     *   SM_AssemblyLine01        240 x  90 x 123
     *   SM_IndustrialRobot01_01  343 x 210 x 412
     *   SM_AssemblyLineControl01  50 x  62 x 165
     *   SM_Fence_02              143 x  17 x 113   (pivot at one end)
     *   SM_ConcretePillar01      150 x 150 x 700
     */
    const TCHAR* const ConveyorPath = TEXT("/Game/Meshes/SM_AssemblyLine01");
    const TCHAR* const RobotPath = TEXT("/Game/Meshes/SM_IndustrialRobot01_01");
    const TCHAR* const ControlPath =
        TEXT("/Game/Meshes/SM_AssemblyLineControl01");
    const TCHAR* const FencePath = TEXT("/Game/Meshes/SM_Fence_02");
    const TCHAR* const BeaconPath = TEXT("/Engine/BasicShapes/Cylinder.Cylinder");
    const TCHAR* const BasicMaterialPath =
        TEXT("/Engine/BasicShapes/BasicShapeMaterial.BasicShapeMaterial");

    constexpr double ConveyorLengthCm = 240.0;
    constexpr double FencePanelCm = 143.0;
    constexpr double RobotFootprintCm = 343.0;

    void AddAt(UInstancedStaticMeshComponent* Batch, const FVector& Where,
        const FQuat& Rotation, int32& PieceCount, double UniformScale = 1.0)
    {
        if (!Batch)
        {
            return;
        }
        FTransform Transform;
        Transform.SetLocation(Where);
        Transform.SetRotation(Rotation);
        Transform.SetScale3D(FVector(UniformScale));
        if (Batch->AddInstance(Transform, true) != INDEX_NONE)
        {
            ++PieceCount;
        }
    }
}

ALBOneFactoryDevStationDressingActor::ALBOneFactoryDevStationDressingActor()
{
    PrimaryActorTick.bCanEverTick = false;
    SetReplicates(false);
    SetActorEnableCollision(false);

    SceneRoot = CreateDefaultSubobject<USceneComponent>(TEXT("SceneRoot"));
    SceneRoot->SetMobility(EComponentMobility::Movable);
    SetRootComponent(SceneRoot);

    // ZonePad now carries the conveyor that physically links stations, and
    // Guarding/Equipment carry real pack meshes rather than coloured cubes.
    ZonePad = MakeBatch(TEXT("Dress_Conveyor"));
    Guarding = MakeBatch(TEXT("Dress_Fence"));
    Equipment = MakeBatch(TEXT("Dress_Robot"));
    Beacon = MakeBatch(TEXT("Dress_Control"));

    Tags.AddUnique(GetDressingTag());
    Tags.AddUnique(TEXT("LB.Environment.VisualOnly"));
    Tags.AddUnique(TEXT("LB.NotProcessWIP"));
}

FName ALBOneFactoryDevStationDressingActor::GetDressingTag()
{
    return FName(TEXT("LB.OneFactory.DevStationDressing"));
}

UInstancedStaticMeshComponent*
ALBOneFactoryDevStationDressingActor::MakeBatch(const TCHAR* Name)
{
    UInstancedStaticMeshComponent* Batch =
        CreateDefaultSubobject<UInstancedStaticMeshComponent>(FName(Name));
    if (!Batch)
    {
        return nullptr;
    }
    Batch->SetupAttachment(SceneRoot);
    Batch->SetMobility(EComponentMobility::Movable);
    Batch->SetCollisionEnabled(ECollisionEnabled::NoCollision);
    Batch->SetCollisionResponseToAllChannels(ECR_Ignore);
    Batch->SetGenerateOverlapEvents(false);
    Batch->SetCanEverAffectNavigation(false);
    Batch->SetReceivesDecals(false);
    return Batch;
}

bool ALBOneFactoryDevStationDressingActor::BuildFromRoute(FString& OutReason)
{
    using namespace LBOneFactoryDressingPrivate;

    UWorld* World = GetWorld();
    if (!World)
    {
        OutReason = TEXT("NO WORLD");
        return false;
    }

    ALBOneFactoryRuntimeCoordinator* Coordinator = nullptr;
    for (TActorIterator<ALBOneFactoryRuntimeCoordinator> It(World); It; ++It)
    {
        if (IsValid(*It)) { Coordinator = *It; break; }
    }
    if (!Coordinator)
    {
        OutReason = TEXT("NO RUNTIME COORDINATOR - BUILD THE FACTORY FIRST");
        return false;
    }

    TArray<FLBOneFactoryRuntimeStationStep> Route;
    FName TopologyId = NAME_None;
    if (!Coordinator->GetConfiguredStationRoute(Route, TopologyId, OutReason))
    {
        return false;
    }
    if (Route.Num() == 0)
    {
        OutReason = TEXT("EMPTY ROUTE");
        return false;
    }

    auto LoadMesh = [](const TCHAR* Path) -> UStaticMesh*
    {
        return Cast<UStaticMesh>(StaticLoadObject(UStaticMesh::StaticClass(),
            nullptr, Path));
    };

    UStaticMesh* Conveyor = LoadMesh(ConveyorPath);
    UStaticMesh* Robot = LoadMesh(RobotPath);
    UStaticMesh* Control = LoadMesh(ControlPath);
    UStaticMesh* Fence = LoadMesh(FencePath);
    UStaticMesh* BeaconMesh = LoadMesh(BeaconPath);
    if (!Conveyor || !Robot || !Control || !Fence)
    {
        OutReason = TEXT(
            "FACTORY PACK MESHES NOT FOUND UNDER /Game/Meshes - import the "
            "Factory Environment Collection first");
        return false;
    }

    // Each batch keeps the mesh's own authored materials. That is the whole
    // point of using the pack: nothing here overrides them.
    ZonePad->ClearInstances();
    ZonePad->SetStaticMesh(Conveyor);
    Guarding->ClearInstances();
    Guarding->SetStaticMesh(Fence);
    Equipment->ClearInstances();
    Equipment->SetStaticMesh(Robot);
    Beacon->ClearInstances();
    Beacon->SetStaticMesh(Control);

    DressedStations = 0;
    PieceCount = 0;

    for (int32 Index = 0; Index < Route.Num(); ++Index)
    {
        const FLBOneFactoryRuntimeStationStep& Step = Route[Index];
        const FVector At = Step.WorldTransform.GetLocation();

        // Direction of travel, taken from route order.
        FVector Along(1.0, 0.0, 0.0);
        const bool bHasNext = Route.IsValidIndex(Index + 1);
        if (bHasNext)
        {
            const FVector Next = Route[Index + 1].WorldTransform.GetLocation();
            const FVector Flat(Next.X - At.X, Next.Y - At.Y, 0.0);
            if (!Flat.IsNearlyZero())
            {
                Along = Flat.GetSafeNormal();
            }
        }
        else if (Route.IsValidIndex(Index - 1))
        {
            const FVector Prev = Route[Index - 1].WorldTransform.GetLocation();
            const FVector Flat(At.X - Prev.X, At.Y - Prev.Y, 0.0);
            if (!Flat.IsNearlyZero())
            {
                Along = Flat.GetSafeNormal();
            }
        }
        const FQuat Facing = FRotationMatrix::MakeFromX(Along).ToQuat();
        const FVector Across(-Along.Y, Along.X, 0.0);

        // Nearest neighbour sets how much room this cell has.
        double Nearest = TNumericLimits<double>::Max();
        for (int32 Other = 0; Other < Route.Num(); ++Other)
        {
            if (Other == Index)
            {
                continue;
            }
            const double Distance =
                FVector::Dist2D(At, Route[Other].WorldTransform.GetLocation());
            if (Distance > 1.0)
            {
                Nearest = FMath::Min(Nearest, Distance);
            }
        }
        if (Nearest == TNumericLimits<double>::Max())
        {
            Nearest = 900.0;
        }
        const double CellHalf = FMath::Clamp(Nearest * 0.44, 220.0, 520.0);

        // The working robot, stood off to one side facing the line. Scaled down
        // where a cell is tight so a 3.4 m robot never straddles its neighbour.
        const double RobotScale =
            FMath::Clamp(CellHalf * 2.0 / (RobotFootprintCm * 1.35), 0.55, 1.0);
        AddAt(Equipment,
            At + Across * (CellHalf * 0.78) + Along * (CellHalf * 0.10),
            FRotationMatrix::MakeFromX(-Across).ToQuat(), PieceCount,
            RobotScale);

        // A second robot mirrored across the line at weld positions, which is
        // how a real body shop works: pairs either side of the car.
        if (Step.Department == ELBOneFactoryDepartment::Body)
        {
            AddAt(Equipment,
                At - Across * (CellHalf * 0.78) - Along * (CellHalf * 0.10),
                FRotationMatrix::MakeFromX(Across).ToQuat(), PieceCount,
                RobotScale);
        }

        // Control cabinet, outboard of the robot on the near side.
        AddAt(Beacon,
            At + Across * (CellHalf * 1.20) - Along * (CellHalf * 0.55),
            FRotationMatrix::MakeFromX(-Across).ToQuat(), PieceCount);

        // Guarding down both sides, ends left open so the line can flow.
        const int32 PanelsPerSide =
            FMath::Max(1, FMath::FloorToInt(
                static_cast<float>(CellHalf * 1.7 / FencePanelCm)));
        for (int32 Side = -1; Side <= 1; Side += 2)
        {
            for (int32 Panel = 0; Panel < PanelsPerSide; ++Panel)
            {
                const double Offset =
                    -CellHalf * 0.85 + (Panel + 1) * FencePanelCm;
                AddAt(Guarding,
                    At + Across * (CellHalf * 1.45 * Side) + Along * Offset,
                    Facing, PieceCount);
            }
        }

        // Conveyor from this station to the next, so the line is physically
        // continuous instead of a row of islands.
        if (bHasNext)
        {
            const FVector Next = Route[Index + 1].WorldTransform.GetLocation();
            const double Gap = FVector::Dist2D(At, Next);
            const int32 Sections =
                FMath::FloorToInt(static_cast<float>(Gap / ConveyorLengthCm));
            for (int32 Section = 0; Section < Sections; ++Section)
            {
                const double Travelled =
                    (Section + 0.5) * ConveyorLengthCm - Gap * 0.5;
                AddAt(ZonePad,
                    FMath::Lerp(At, Next, 0.5)
                        + Along * Travelled + FVector(0.0, 0.0, 0.0),
                    Facing, PieceCount);
            }
        }

        ++DressedStations;
    }

    OutReason = FString::Printf(
        TEXT("dressed %d station(s) with %d pack mesh instance(s): robots, "
             "control cabinets, guarding and linking conveyor"),
        DressedStations, PieceCount);
    return true;
}
