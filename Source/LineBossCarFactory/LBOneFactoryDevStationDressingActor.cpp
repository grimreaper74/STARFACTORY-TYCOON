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
    const TCHAR* const CubePath = TEXT("/Engine/BasicShapes/Cube.Cube");
    const TCHAR* const CylinderPath = TEXT("/Engine/BasicShapes/Cylinder.Cylinder");
    const TCHAR* const BasicMaterialPath =
        TEXT("/Engine/BasicShapes/BasicShapeMaterial.BasicShapeMaterial");

    /** Engine Cube is 100 cm, so a scale value is also a size in centimetres. */
    constexpr double CubeCm = 100.0;

    constexpr double GuardHeightCm = 115.0;
    constexpr double GuardPostCm = 14.0;
    constexpr double RailThicknessCm = 7.0;
    constexpr double CabinetWidthCm = 85.0;
    constexpr double CabinetDepthCm = 58.0;
    constexpr double CabinetHeightCm = 190.0;
    constexpr double BeaconCm = 22.0;

    void AddBox(UInstancedStaticMeshComponent* Batch, const FVector& Centre,
        const FVector& SizeCm, const FQuat& Rotation, int32& PieceCount)
    {
        if (!Batch)
        {
            return;
        }
        FTransform Transform;
        Transform.SetLocation(Centre);
        Transform.SetRotation(Rotation);
        Transform.SetScale3D(FVector(SizeCm.X / CubeCm, SizeCm.Y / CubeCm,
            SizeCm.Z / CubeCm));
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

    ZonePad = MakeBatch(TEXT("Dress_ZonePad"));
    Guarding = MakeBatch(TEXT("Dress_Guarding"));
    Equipment = MakeBatch(TEXT("Dress_Equipment"));
    Beacon = MakeBatch(TEXT("Dress_Beacon"));

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

    UStaticMesh* Cube = Cast<UStaticMesh>(
        StaticLoadObject(UStaticMesh::StaticClass(), nullptr, CubePath));
    UStaticMesh* Cylinder = Cast<UStaticMesh>(
        StaticLoadObject(UStaticMesh::StaticClass(), nullptr, CylinderPath));
    UMaterialInterface* Base = Cast<UMaterialInterface>(
        StaticLoadObject(UMaterialInterface::StaticClass(), nullptr,
            BasicMaterialPath));
    if (!Cube || !Cylinder || !Base)
    {
        OutReason = TEXT("COULD NOT RESOLVE PRIMITIVES OR BASE MATERIAL");
        return false;
    }

    struct FBatchSetup
    {
        UInstancedStaticMeshComponent* Component;
        UStaticMesh* Mesh;
        const TCHAR* Hex;
    };
    const FBatchSetup Setups[] = {
        { ZonePad,   Cube,     TEXT("1F4B44") },  // Cairnwell Green zone
        { Guarding,  Cube,     TEXT("F2C300") },  // Safety Yellow guarding
        { Equipment, Cube,     TEXT("202428") },  // Foundry Charcoal equipment
        { Beacon,    Cylinder, TEXT("3FBF9E") },  // status beacon
    };
    Materials.Reset();
    for (const FBatchSetup& Setup : Setups)
    {
        if (!Setup.Component)
        {
            OutReason = TEXT("DRESSING BATCH MISSING");
            return false;
        }
        UMaterialInstanceDynamic* Material =
            UMaterialInstanceDynamic::Create(Base, this);
        if (!Material)
        {
            OutReason = TEXT("COULD NOT CREATE DRESSING MATERIAL");
            return false;
        }
        const FLinearColor Colour =
            FLinearColor::FromSRGBColor(FColor::FromHex(Setup.Hex));
        Material->SetVectorParameterValue(TEXT("Color"), Colour);
        Material->SetVectorParameterValue(TEXT("BaseColor"), Colour);
        Setup.Component->ClearInstances();
        Setup.Component->SetStaticMesh(Setup.Mesh);
        Setup.Component->SetMaterial(0, Material);
        Materials.Add(Material);
    }

    DressedStations = 0;
    PieceCount = 0;

    for (int32 Index = 0; Index < Route.Num(); ++Index)
    {
        const FLBOneFactoryRuntimeStationStep& Step = Route[Index];
        const FVector At = Step.WorldTransform.GetLocation();

        // Size each cell from the distance to its nearest neighbour, so cells
        // never overlap however the player has spaced the line.
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
        const double Half = FMath::Clamp(Nearest * 0.40, 170.0, 430.0);

        // Orient the cell to the direction of travel so guarding runs alongside
        // the line rather than across it.
        FVector Along(1.0, 0.0, 0.0);
        if (Route.IsValidIndex(Index + 1))
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

        const double CellLength = Half * 2.0;
        const double CellWidth = Half * 1.45;

        // Zone pad: a thin painted rectangle identifying the cell footprint.
        AddBox(ZonePad, At + FVector(0.0, 0.0, 1.5),
            FVector(CellLength, CellWidth, 3.0), Facing, PieceCount);

        // Guarding down both sides, open at each end so the line can flow.
        for (int32 Side = -1; Side <= 1; Side += 2)
        {
            const FVector SideCentre =
                At + Across * (CellWidth * 0.5 * Side);
            // Two horizontal rails.
            for (int32 Rail = 0; Rail < 2; ++Rail)
            {
                const double RailZ =
                    GuardHeightCm * (Rail == 0 ? 0.45 : 0.92);
                AddBox(Guarding, SideCentre + FVector(0.0, 0.0, RailZ),
                    FVector(CellLength * 0.92, RailThicknessCm,
                        RailThicknessCm), Facing, PieceCount);
            }
            // Posts at each end of the run.
            for (int32 End = -1; End <= 1; End += 2)
            {
                AddBox(Guarding,
                    SideCentre + Along * (CellLength * 0.46 * End)
                        + FVector(0.0, 0.0, GuardHeightCm * 0.5),
                    FVector(GuardPostCm, GuardPostCm, GuardHeightCm),
                    Facing, PieceCount);
            }
        }

        // Control cabinet just outside the guarding, on the near side.
        const FVector CabinetAt = At
            + Across * (CellWidth * 0.5 + CabinetDepthCm * 0.9)
            - Along * (CellLength * 0.30);
        AddBox(Equipment, CabinetAt + FVector(0.0, 0.0, CabinetHeightCm * 0.5),
            FVector(CabinetWidthCm, CabinetDepthCm, CabinetHeightCm),
            Facing, PieceCount);

        // Status beacon on the cabinet: the one place a glance can read state.
        FTransform BeaconTransform;
        BeaconTransform.SetLocation(
            CabinetAt + FVector(0.0, 0.0, CabinetHeightCm + BeaconCm * 0.5));
        BeaconTransform.SetRotation(Facing);
        BeaconTransform.SetScale3D(FVector(BeaconCm / CubeCm,
            BeaconCm / CubeCm, BeaconCm / CubeCm));
        if (Beacon && Beacon->AddInstance(BeaconTransform, true) != INDEX_NONE)
        {
            ++PieceCount;
        }

        // A quality gate gets an overhead inspection beam, so the gates in the
        // line are visible without reading a label.
        if (Step.bQualityGate)
        {
            AddBox(Equipment,
                At + FVector(0.0, 0.0, GuardHeightCm + 210.0),
                FVector(28.0, CellWidth * 1.12, 26.0), Facing, PieceCount);
        }

        ++DressedStations;
    }

    OutReason = FString::Printf(
        TEXT("dressed %d station(s) with %d piece(s)"),
        DressedStations, PieceCount);
    return true;
}
