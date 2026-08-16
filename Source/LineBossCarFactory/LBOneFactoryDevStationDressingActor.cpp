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
        { TEXT("Dress_PressTrain"),
          TEXT("/Game/LineBoss/PressTrains/RuntimeVisual_v449"
               "/SM_CA_MW_PressTrain_CompleteRuntimeVisual_v449"), 5770.0 },
        { TEXT("Dress_Coil"),
          TEXT("/Game/LineBoss/Candidates/PressShop/CleanRebuild_v20260809_v004"
               "/Inbound/SM_CA_MW_WrappedCoil_Repaired_v003"), 181.0 },
        { TEXT("Dress_CoilStand"),
          TEXT("/Game/LineBoss/Candidates/PressShop/CleanRebuild_v20260809_v004"
               "/Inbound/SM_CA_MW_AdjustableCoilStand_Approved_v005"), 190.0 },
        { TEXT("Dress_Stillage"),
          TEXT("/Game/LineBoss/Candidates/WeldShop/PanelStillageRuntime_v001"
               "/SM_LB_PanelStillage_Runtime_v001"), 190.0 },
        { TEXT("Dress_Lorry"),
          TEXT("/Game/LineBoss/Candidates/PressShop/CleanRebuild_v20260809_v004"
               "/Inbound/SM_CA_MW_InboundLorry_Approved_v006"), 800.0 },
        { TEXT("Dress_Destacker"),
          TEXT("/Game/LineBoss/Candidates/PressShop/CleanRebuild_v20260809_v012"
               "/PressTrains/SM_CA_MW_S01_Destack_Approved_v006"), 400.0 },
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
        {
            // The detailed-press recovery design: the complete v449 Train A
            // visual is anchored once at the committed ConfigurablePressTrain
            // station transform, with the mesh's pinned local transform -
            // location [9.25, 2367.5, 0], rotation zero, scale 100 - applied
            // relative to that datum. Its 57.7 m span covers the working length
            // of the press line, so the other press positions get material
            // handling rather than generic machines: coils on stands at the
            // inbound and storage rows, staged stillages at dispatch, and
            // nothing that would interpenetrate the train.
            static const FName PressTrainStation(TEXT("OF_PRESS_TRAIN_001"));
            static const FName InboundStation(
                TEXT("OF_PRESS_INBOUND_RECEIVING_001"));
            static const FName CoilStoreStation(
                TEXT("OF_PRESS_WRAPPED_COIL_STORE_001"));
            static const FName DispatchStation(
                TEXT("OF_PRESS_PANEL_DISPATCH_001"));

            if (Step.StationId == PressTrainStation)
            {
                const FTransform Datum = Step.WorldTransform;
                const FVector TrainAt = Datum.GetLocation()
                    + Datum.GetRotation().RotateVector(
                        FVector(9.25, 2367.5, 0.0));
                // A single 306-section mesh at scale 100 is a one-off, not
                // an instancing case: give it a plain static mesh component,
                // which renders unconditionally.
                if (UStaticMesh* TrainMesh = Cast<UStaticMesh>(
                    StaticLoadObject(UStaticMesh::StaticClass(), nullptr,
                        Kinds[static_cast<int32>(
                            ELBOneFactoryDressingKind::PressTrain)].Path)))
                {
                    UStaticMeshComponent* Train =
                        NewObject<UStaticMeshComponent>(this,
                            TEXT("Dress_PressTrain_Mesh"));
                    Train->SetupAttachment(SceneRoot);
                    Train->SetMobility(EComponentMobility::Movable);
                    Train->SetCollisionEnabled(ECollisionEnabled::NoCollision);
                    Train->SetCanEverAffectNavigation(false);
                    Train->SetStaticMesh(TrainMesh);
                    Train->SetWorldLocationAndRotation(TrainAt,
                        Datum.GetRotation());
                    Train->SetWorldScale3D(FVector(100.0));
                    Train->RegisterComponent();
                    const FBoxSphereBounds TrainBounds = Train->Bounds;
                    UE_LOG(LogTemp, Display,
                        TEXT("LINE_BOSS_DRESS_TRAIN_BOUNDS "
                             "origin=(%.0f,%.0f,%.0f) extent=(%.0f,%.0f,%.0f) "
                             "scale=(%.1f,%.1f,%.1f)"),
                        TrainBounds.Origin.X, TrainBounds.Origin.Y,
                        TrainBounds.Origin.Z, TrainBounds.BoxExtent.X,
                        TrainBounds.BoxExtent.Y, TrainBounds.BoxExtent.Z,
                        Train->GetComponentScale().X,
                        Train->GetComponentScale().Y,
                        Train->GetComponentScale().Z);
                    ++PieceCount;
                }
                UE_LOG(LogTemp, Display,
                    TEXT("LINE_BOSS_DRESS_TRAIN datum=(%.0f,%.0f,%.0f) "
                         "yaw=%.1f placed=(%.0f,%.0f,%.0f) span~=(1360x5770x940)"),
                    Datum.GetLocation().X, Datum.GetLocation().Y,
                    Datum.GetLocation().Z, Datum.Rotator().Yaw,
                    TrainAt.X, TrainAt.Y, TrainAt.Z);
            }
            else if (Step.StationId == InboundStation
                || Step.StationId == CoilStoreStation)
            {
                // The delivery lorry stands at receiving, outboard of the
                // coil row - the visible start of the inbound journey.
                if (Step.StationId == InboundStation)
                {
                    Place(ELBOneFactoryDressingKind::Lorry,
                        At - Across * 650.0, Facing);
                }
                // A row of stored coils across the station, each on its stand.
                const int32 Coils =
                    Step.StationId == CoilStoreStation ? 3 : 2;
                for (int32 CoilIndex = 0; CoilIndex < Coils; ++CoilIndex)
                {
                    const double Offset =
                        (CoilIndex - (Coils - 1) * 0.5) * 260.0;
                    const FVector CoilAt = At + Across * Offset;
                    Place(ELBOneFactoryDressingKind::CoilStand, CoilAt,
                        Facing);
                    Place(ELBOneFactoryDressingKind::Coil,
                        CoilAt + FVector(0.0, 0.0, 20.0), Facing);
                }
            }
            else if (Step.StationId == DispatchStation)
            {
                // Staged stillages waiting for the FLT run to weld intake.
                Place(ELBOneFactoryDressingKind::Stillage,
                    At + Across * 150.0 + FVector(0.0, 0.0, 58.0), Facing);
                Place(ELBOneFactoryDressingKind::Stillage,
                    At - Across * 150.0 + FVector(0.0, 0.0, 58.0), Facing);
            }
            else
            {
                // Blank preparation gets the approved S01 destacker if the
                // station stands clear of the train's measured footprint
                // (x within +-680, y within +-2885 of the anchored datum);
                // buffer and inspection inside the span stay clear.
                static const FName BlankPrepStation(
                    TEXT("OF_PRESS_BLANK_PREP_001"));
                if (Step.StationId == BlankPrepStation)
                {
                    const FLBOneFactoryRuntimeStationStep* Train = nullptr;
                    for (const FLBOneFactoryRuntimeStationStep& Other : Route)
                    {
                        if (Other.StationId == PressTrainStation)
                        {
                            Train = &Other;
                            break;
                        }
                    }
                    bool bClearOfTrain = true;
                    if (Train)
                    {
                        const FVector TrainCentre =
                            Train->WorldTransform.GetLocation()
                            + Train->WorldTransform.GetRotation().RotateVector(
                                FVector(9.25, 2367.5, 0.0));
                        const FVector Delta = At - TrainCentre;
                        bClearOfTrain = FMath::Abs(Delta.X) > 900.0
                            || FMath::Abs(Delta.Y) > 3100.0;
                    }
                    if (bClearOfTrain)
                    {
                        // The approved destacker mesh is authored at roughly
                        // one hundred times its real size - 958 x 1080 x 615
                        // METRES at scale 1, measured in the editor - so it
                        // stands here at 0.01: a 9.6 x 10.8 x 6.2 m cell.
                        Place(ELBOneFactoryDressingKind::Destacker,
                            At + Across * 320.0, FacingOut, 0.01);
                    }
                }
            }
            break;
        }

        case ELBOneFactoryDepartment::Body:
            // Deliberately no machines here. The frozen weld starter
            // presentation already renders the real native robots - 36
            // seven-link arms and 16 C-guns from BodyShopRobotNative_v001 -
            // under its exact 469-instance contract. Pack robots on top were
            // duplicates of a presentation that is already release content.
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

        // Common to every station except Press: a control cabinet and side
        // guarding. The detailed press train carries its own guards, controls
        // and utilities, so generic dressing would interpenetrate it.
        if (Step.Department == ELBOneFactoryDepartment::Press)
        {
            if (Step.bQualityGate)
            {
                Place(ELBOneFactoryDressingKind::LampRamp, At, Facing,
                    FMath::Min(Fit, 1.0));
            }
            ++DressedStations;
            continue;
        }
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

    // Department aprons: the map's authored floor is near-black in the press
    // and logistics areas, so machines there read against a void whatever the
    // light level. A light concrete pad under each department's footprint
    // gives the standard's readable ground. The engine cube's default material
    // is deliberately kept - a plain light grey slab.
    {
        UStaticMesh* Cube = Cast<UStaticMesh>(StaticLoadObject(
            UStaticMesh::StaticClass(), nullptr,
            TEXT("/Engine/BasicShapes/Cube.Cube")));
        UInstancedStaticMeshComponent* ApronBatch =
            NewObject<UInstancedStaticMeshComponent>(this,
                TEXT("Dress_Apron"));
        if (Cube && ApronBatch)
        {
            ApronBatch->SetupAttachment(SceneRoot);
            ApronBatch->SetMobility(EComponentMobility::Movable);
            ApronBatch->SetCollisionEnabled(ECollisionEnabled::NoCollision);
            ApronBatch->SetCanEverAffectNavigation(false);
            ApronBatch->SetStaticMesh(Cube);
            ApronBatch->RegisterComponent();

            FBox DeptBounds[4];
            for (FBox& Box : DeptBounds) { Box.Init(); }
            for (const FLBOneFactoryRuntimeStationStep& Step : Route)
            {
                DeptBounds[static_cast<int32>(Step.Department)] +=
                    Step.WorldTransform.GetLocation();
            }
            for (const FBox& Box : DeptBounds)
            {
                if (!Box.IsValid)
                {
                    continue;
                }
                const FBox Padded = Box.ExpandBy(FVector(1400.0, 1400.0, 0.0));
                const FVector Centre = Padded.GetCenter();
                const FVector Size = Padded.GetSize();
                FTransform Apron;
                Apron.SetLocation(FVector(Centre.X, Centre.Y, -14.0));
                Apron.SetScale3D(FVector(Size.X / 100.0, Size.Y / 100.0, 0.3));
                if (ApronBatch->AddInstance(Apron, true) != INDEX_NONE)
                {
                    ++PieceCount;
                }
            }
        }
    }

    for (int32 Index = 0; Index < KindCount; ++Index)
    {
        if (Batches[Index] && Batches[Index]->GetInstanceCount() > 0)
        {
            UE_LOG(LogTemp, Display,
                TEXT("LINE_BOSS_DRESS_KIND %s count=%d mesh=%s"),
                Kinds[Index].Component,
                Batches[Index]->GetInstanceCount(),
                Batches[Index]->GetStaticMesh()
                    ? *Batches[Index]->GetStaticMesh()->GetName()
                    : TEXT("NONE"));
        }
    }

    OutReason = FString::Printf(
        TEXT("dressed %d station(s) with %d pack instance(s) from %d resolved "
             "mesh famil%s, composed per department"),
        DressedStations, PieceCount, Resolved,
        Resolved == 1 ? TEXT("y") : TEXT("ies"));
    return true;
}
