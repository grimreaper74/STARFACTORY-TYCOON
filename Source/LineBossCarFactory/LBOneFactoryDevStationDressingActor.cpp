#include "LBOneFactoryDevStationDressingActor.h"

#include "Components/InstancedStaticMeshComponent.h"
#include "Engine/StaticMesh.h"
#include "Engine/World.h"
#include "EngineUtils.h"
#include "LBOneFactoryRuntimeCoordinator.h"

namespace LBOneFactoryDressingPrivate
{
    constexpr int32 KindCount =
        static_cast<int32>(ELBOneFactoryDressingKind::Count);

    /**
     * Factory Environment Collection meshes, measured in the editor. Pivots sit
     * at the base of each, so a placement Z of zero stands it on the floor.
     *
     *   SM_AssemblyLine01         240 x  90 x 123
     *   SM_Fence_02               143 x  17 x 113
     *   SM_IndustrialRobot01_01   343 x 210 x 412
     *   SM_AssemblyLineControl01   50 x  62 x 165
     *   SM_AssemblyLineBox01      267 x 266 x 277
     *   SM_AssemblyLineBox02      200 x 264 x 275
     *   SM_Boiler_01              464 x 635 x 534
     *   SM_StorageShelvesBottom01 300 x 160 x 200
     *   SM_DeskControl_01         111 x 300 x 215
     *   SM_AssemblyLineLampRamp   121 x 788 x 588
     */
    struct FKindSpec
    {
        const TCHAR* Component;
        const TCHAR* Path;
        double LengthCm;
    };

    const FKindSpec Kinds[KindCount] = {
        { TEXT("Dress_Conveyor"), TEXT("/Game/Meshes/SM_AssemblyLine01"), 240.0 },
        { TEXT("Dress_Fence"),    TEXT("/Game/Meshes/SM_Fence_02"), 143.0 },
        { TEXT("Dress_Robot"),    TEXT("/Game/Meshes/SM_IndustrialRobot01_01"), 343.0 },
        { TEXT("Dress_Control"),  TEXT("/Game/Meshes/SM_AssemblyLineControl01"), 50.0 },
        { TEXT("Dress_Press"),    TEXT("/Game/Meshes/SM_AssemblyLineBox01"), 267.0 },
        { TEXT("Dress_Booth"),    TEXT("/Game/Meshes/SM_AssemblyLineBox02"), 200.0 },
        { TEXT("Dress_Oven"),     TEXT("/Game/Meshes/SM_Boiler_01"), 464.0 },
        { TEXT("Dress_Rack"),     TEXT("/Game/Meshes/SM_StorageShelvesBottom01"), 300.0 },
        { TEXT("Dress_Bench"),    TEXT("/Game/Meshes/SM_DeskControl_01"), 111.0 },
        { TEXT("Dress_LampRamp"), TEXT("/Game/Meshes/SM_AssemblyLineLampRamp"), 121.0 },
    };
}

ALBOneFactoryDevStationDressingActor::ALBOneFactoryDevStationDressingActor()
{
    using namespace LBOneFactoryDressingPrivate;

    PrimaryActorTick.bCanEverTick = false;
    SetReplicates(false);
    SetActorEnableCollision(false);

    SceneRoot = CreateDefaultSubobject<USceneComponent>(TEXT("SceneRoot"));
    SceneRoot->SetMobility(EComponentMobility::Movable);
    SetRootComponent(SceneRoot);

    Batches.Reserve(KindCount);
    for (int32 Index = 0; Index < KindCount; ++Index)
    {
        UInstancedStaticMeshComponent* Batch =
            CreateDefaultSubobject<UInstancedStaticMeshComponent>(
                FName(Kinds[Index].Component));
        Batch->SetupAttachment(SceneRoot);
        Batch->SetMobility(EComponentMobility::Movable);
        Batch->SetCollisionEnabled(ECollisionEnabled::NoCollision);
        Batch->SetCollisionResponseToAllChannels(ECR_Ignore);
        Batch->SetGenerateOverlapEvents(false);
        Batch->SetCanEverAffectNavigation(false);
        Batch->SetReceivesDecals(false);
        Batches.Add(Batch);
    }

    Tags.AddUnique(GetDressingTag());
    Tags.AddUnique(TEXT("LB.Environment.VisualOnly"));
    Tags.AddUnique(TEXT("LB.NotProcessWIP"));
}

FName ALBOneFactoryDevStationDressingActor::GetDressingTag()
{
    return FName(TEXT("LB.OneFactory.DevStationDressing"));
}

void ALBOneFactoryDevStationDressingActor::Place(
    const ELBOneFactoryDressingKind Kind, const FVector& Where,
    const FQuat& Rotation, const double UniformScale)
{
    const int32 Index = static_cast<int32>(Kind);
    if (!Batches.IsValidIndex(Index) || !Batches[Index]
        || !Batches[Index]->GetStaticMesh())
    {
        return;
    }
    FTransform Transform;
    Transform.SetLocation(Where);
    Transform.SetRotation(Rotation);
    Transform.SetScale3D(FVector(UniformScale));
    if (Batches[Index]->AddInstance(Transform, true) != INDEX_NONE)
    {
        ++PieceCount;
    }
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

    int32 Resolved = 0;
    for (int32 Index = 0; Index < KindCount; ++Index)
    {
        UStaticMesh* Mesh = Cast<UStaticMesh>(StaticLoadObject(
            UStaticMesh::StaticClass(), nullptr, Kinds[Index].Path));
        Batches[Index]->ClearInstances();
        if (Mesh)
        {
            // Keep each mesh's own authored materials: that is the point of
            // using the pack rather than tinting primitives.
            Batches[Index]->SetStaticMesh(Mesh);
            ++Resolved;
        }
    }
    if (Resolved == 0)
    {
        OutReason = TEXT(
            "NO FACTORY PACK MESHES FOUND UNDER /Game/Meshes - import the "
            "Factory Environment Collection first");
        return false;
    }

    DressedStations = 0;
    PieceCount = 0;

    for (int32 Index = 0; Index < Route.Num(); ++Index)
    {
        const FLBOneFactoryRuntimeStationStep& Step = Route[Index];
        const FVector At = Step.WorldTransform.GetLocation();

        FVector Along(1.0, 0.0, 0.0);
        const bool bHasNext = Route.IsValidIndex(Index + 1);
        const int32 Neighbour = bHasNext ? Index + 1 : Index - 1;
        if (Route.IsValidIndex(Neighbour))
        {
            const FVector Other = Route[Neighbour].WorldTransform.GetLocation();
            const FVector Flat = bHasNext
                ? FVector(Other.X - At.X, Other.Y - At.Y, 0.0)
                : FVector(At.X - Other.X, At.Y - Other.Y, 0.0);
            if (!Flat.IsNearlyZero())
            {
                Along = Flat.GetSafeNormal();
            }
        }
        const FQuat Facing = FRotationMatrix::MakeFromX(Along).ToQuat();
        const FQuat FacingIn = FRotationMatrix::MakeFromX(
            FVector(Along.Y, -Along.X, 0.0)).ToQuat();
        const FQuat FacingOut = FRotationMatrix::MakeFromX(
            FVector(-Along.Y, Along.X, 0.0)).ToQuat();
        const FVector Across(-Along.Y, Along.X, 0.0);

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
        const double Fit = FMath::Clamp(CellHalf / 430.0, 0.55, 1.15);

        // Each shop is composed differently, so Press, Body, Paint and Assembly
        // read as different places rather than one repeated cell.
        switch (Step.Department)
        {
        case ELBOneFactoryDepartment::Press:
            // A heavy press either side of the line, with material racking
            // behind it.
            Place(ELBOneFactoryDressingKind::Press,
                At + Across * (CellHalf * 0.95), FacingOut, Fit);
            Place(ELBOneFactoryDressingKind::Press,
                At - Across * (CellHalf * 0.95), FacingIn, Fit);
            Place(ELBOneFactoryDressingKind::Rack,
                At + Across * (CellHalf * 1.85) - Along * (CellHalf * 0.5),
                Facing, Fit);
            break;

        case ELBOneFactoryDepartment::Body:
            // Mirrored six-axis pairs, which is how a real body shop works.
            Place(ELBOneFactoryDressingKind::Robot,
                At + Across * (CellHalf * 0.80), FacingOut, Fit);
            Place(ELBOneFactoryDressingKind::Robot,
                At - Across * (CellHalf * 0.80), FacingIn, Fit);
            break;

        case ELBOneFactoryDepartment::Paint:
            // Enclosed booth modules either side, and an oven at the cure end.
            Place(ELBOneFactoryDressingKind::Booth,
                At + Across * (CellHalf * 0.95), FacingOut, Fit);
            Place(ELBOneFactoryDressingKind::Booth,
                At - Across * (CellHalf * 0.95), FacingIn, Fit);
            if (Step.SemanticStage == ELBOneFactoryVehicleStage::Cure)
            {
                Place(ELBOneFactoryDressingKind::Oven,
                    At + Across * (CellHalf * 2.1), FacingOut, Fit * 0.9);
            }
            break;

        case ELBOneFactoryDepartment::Assembly:
        default:
            // One robot fitting parts, an operator bench opposite, and a parts
            // rack behind: the readable "station + robot + next part" model.
            Place(ELBOneFactoryDressingKind::Robot,
                At + Across * (CellHalf * 0.80), FacingOut, Fit * 0.9);
            Place(ELBOneFactoryDressingKind::Bench,
                At - Across * (CellHalf * 0.85), FacingIn, Fit);
            Place(ELBOneFactoryDressingKind::Rack,
                At - Across * (CellHalf * 1.7), FacingIn, Fit);
            break;
        }

        // Common to every station: a control cabinet and side guarding.
        Place(ELBOneFactoryDressingKind::Control,
            At + Across * (CellHalf * 1.35) - Along * (CellHalf * 0.62),
            FacingOut);

        const int32 PanelsPerSide = FMath::Max(1, FMath::FloorToInt(
            static_cast<float>(CellHalf * 1.6 / Kinds[
                static_cast<int32>(ELBOneFactoryDressingKind::Fence)].LengthCm)));
        for (int32 Side = -1; Side <= 1; Side += 2)
        {
            for (int32 Panel = 0; Panel < PanelsPerSide; ++Panel)
            {
                const double Offset = -CellHalf * 0.8
                    + (Panel + 1) * Kinds[static_cast<int32>(
                        ELBOneFactoryDressingKind::Fence)].LengthCm;
                Place(ELBOneFactoryDressingKind::Fence,
                    At + Across * (CellHalf * 2.35 * Side) + Along * Offset,
                    Facing);
            }
        }

        // An overhead light ramp marks every quality gate, so the inspection
        // points in the line are visible without reading a label.
        if (Step.bQualityGate)
        {
            Place(ELBOneFactoryDressingKind::LampRamp, At, Facing,
                FMath::Min(Fit, 1.0));
        }

        // Conveyor from this station to the next: the line is physically
        // continuous rather than a row of islands.
        if (bHasNext)
        {
            const FVector Next = Route[Index + 1].WorldTransform.GetLocation();
            const double Gap = FVector::Dist2D(At, Next);
            const double SectionCm = Kinds[static_cast<int32>(
                ELBOneFactoryDressingKind::Conveyor)].LengthCm;
            const int32 Sections =
                FMath::FloorToInt(static_cast<float>(Gap / SectionCm));
            for (int32 Section = 0; Section < Sections; ++Section)
            {
                const double Travelled = (Section + 0.5) * SectionCm - Gap * 0.5;
                Place(ELBOneFactoryDressingKind::Conveyor,
                    FMath::Lerp(At, Next, 0.5) + Along * Travelled, Facing);
            }
        }

        ++DressedStations;
    }

    OutReason = FString::Printf(
        TEXT("dressed %d station(s) with %d pack instance(s) from %d resolved "
             "mesh famil%s, composed per department"),
        DressedStations, PieceCount, Resolved,
        Resolved == 1 ? TEXT("y") : TEXT("ies"));
    return true;
}
