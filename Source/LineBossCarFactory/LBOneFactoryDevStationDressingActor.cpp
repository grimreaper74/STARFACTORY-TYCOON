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
        // The native paint kit, measured 2026-08-16: floor pivots, true scale.
        { TEXT("Dress_PaintWashTunnel"),
          TEXT("/Game/LineBoss/Candidates/PaintShop/PaintLineNativeKit_v001"
               "/Process/SM_LB_Paint_PretreatmentWashTunnel_v001"), 852.0 },
        { TEXT("Dress_PaintEDTunnel"),
          TEXT("/Game/LineBoss/Candidates/PaintShop/PaintLineNativeKit_v001"
               "/Process/SM_LB_Paint_FlashOffTunnel_v001"), 702.0 },
        { TEXT("Dress_PaintSprayBooth"),
          TEXT("/Game/LineBoss/Candidates/PaintShop/SprayBoothRuntime_v002"
               "/SM_LB_PaintSprayBooth_Runtime_v002"), 1200.0 },
        { TEXT("Dress_PaintCureOven"),
          TEXT("/Game/LineBoss/Candidates/PaintShop/PaintLineNativeKit_v001"
               "/Process/SM_LB_Paint_CuringOvenTunnel_v001"), 902.0 },
        { TEXT("Dress_PaintQualityTunnel"),
          TEXT("/Game/LineBoss/Candidates/PaintShop/PaintLineNativeKit_v001"
               "/Quality/SM_LB_Paint_QualityLightTunnel_v001"), 602.0 },
        { TEXT("Dress_PaintAirExtract"),
          TEXT("/Game/LineBoss/Candidates/PaintShop/PaintLineNativeKit_v001"
               "/Services/SM_LB_Paint_AirExtractionModule_v001"), 340.0 },
        { TEXT("Dress_PaintServiceSet"),
          TEXT("/Game/LineBoss/Candidates/PaintShop/PaintLineNativeKit_v001"
               "/Services/SM_LB_Paint_ServiceSet_v001"), 344.0 },
        // The native assembly kit, measured 2026-08-16: floor pivots, true
        // scale.
        { TEXT("Dress_AssemblySkillet"),
          TEXT("/Game/LineBoss/Candidates/AssemblyShop"
               "/AssemblyLineNativeKit_v001/Logistics"
               "/SM_LB_Assembly_SkilletCarrier_v001"), 520.0 },
        { TEXT("Dress_AssemblyPartsCart"),
          TEXT("/Game/LineBoss/Candidates/AssemblyShop"
               "/AssemblyLineNativeKit_v001/Logistics"
               "/SM_LB_Assembly_SequencedPartsCart_v001"), 180.0 },
        { TEXT("Dress_AssemblyMarriageGantry"),
          TEXT("/Game/LineBoss/Candidates/AssemblyShop"
               "/AssemblyLineNativeKit_v001/Robotics"
               "/SM_LB_Assembly_HeavyMarriageGantry_v001"), 600.0 },
        { TEXT("Dress_AssemblyLiftPlatform"),
          TEXT("/Game/LineBoss/Candidates/AssemblyShop"
               "/AssemblyLineNativeKit_v001/Stations"
               "/SM_LB_Assembly_ErgonomicLiftPlatform_v001"), 550.0 },
        { TEXT("Dress_AssemblyWheelRack"),
          TEXT("/Game/LineBoss/Candidates/AssemblyShop"
               "/AssemblyLineNativeKit_v001/Logistics"
               "/SM_LB_Assembly_WheelTireRack_v001"), 240.0 },
        { TEXT("Dress_AssemblyEOLArch"),
          TEXT("/Game/LineBoss/Candidates/AssemblyShop"
               "/AssemblyLineNativeKit_v001/Test"
               "/SM_LB_Assembly_EOLInspectionArch_v001"), 226.0 },
        { TEXT("Dress_AssemblyAlignmentBed"),
          TEXT("/Game/LineBoss/Candidates/AssemblyShop"
               "/AssemblyLineNativeKit_v001/Test"
               "/SM_LB_Assembly_WheelAlignmentBed_v001"), 540.0 },
        { TEXT("Dress_ScrapSkip"),
          TEXT("/Game/Meshes/SM_PalletCart_PalletBox_open"), 180.0 },
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

    // Rebuilds must not NewObject over the previous build's live components.
    for (UActorComponent* Piece : DynamicPieces)
    {
        if (Piece)
        {
            Piece->DestroyComponent();
        }
    }
    DynamicPieces.Reset();

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
                // The pinned v449 mesh is one complete train row, placed four
                // times at the reference row pitch. The reference map's own
                // v049 aggregates were tried in its place and read near-black
                // under the Moorcross lighting standard - the restored map
                // only reads because of its own authored lights - so the
                // recovery doc's v449 pin stands and the aggregates are
                // filtered out of the manifest.
                if (UStaticMesh* TrainMesh = Cast<UStaticMesh>(
                    StaticLoadObject(UStaticMesh::StaticClass(), nullptr,
                        Kinds[static_cast<int32>(
                            ELBOneFactoryDressingKind::PressTrain)].Path)))
                {
                    for (int32 TrainIndex = 0; TrainIndex < 4; ++TrainIndex)
                    {
                        // 2200 cm row pitch: the reference grid every
                        // row-keyed manifest asset is authored on (identity
                        // plates at ref Y 0/2200/4400/6600; v356 pitch
                        // receipts record centre_pitch_cm 2200.0). The
                        // earlier 2251 had no provenance and pushed rows
                        // B-D off the grid by 51/102/153 cm.
                        const FVector SiblingOffset =
                            Datum.GetRotation().RotateVector(
                                FVector(-2200.0 * TrainIndex, 0.0, 0.0));
                        UStaticMeshComponent* Train =
                            NewObject<UStaticMeshComponent>(this);
                        DynamicPieces.Add(Train);
                        Train->SetupAttachment(SceneRoot);
                        Train->SetMobility(EComponentMobility::Movable);
                        Train->SetCollisionEnabled(
                            ECollisionEnabled::NoCollision);
                        Train->SetCanEverAffectNavigation(false);
                        Train->SetStaticMesh(TrainMesh);
                        Train->SetWorldLocationAndRotation(
                            TrainAt + SiblingOffset, Datum.GetRotation());
                        Train->SetWorldScale3D(FVector(100.0));
                        Train->RegisterComponent();
                        ++PieceCount;
                    }
                }
                UE_LOG(LogTemp, Display,
                    TEXT("LINE_BOSS_DRESS_TRAIN datum=(%.0f,%.0f,%.0f) "
                         "yaw=%.1f placed=(%.0f,%.0f,%.0f)"),
                    Datum.GetLocation().X, Datum.GetLocation().Y,
                    Datum.GetLocation().Z, Datum.Rotator().Yaw,
                    TrainAt.X, TrainAt.Y, TrainAt.Z);

                // The master plan's outbound and service edges, keyed to the
                // same datum. Local axes: +Y runs down the train length
                // toward the outbound end (reference east), -X marches
                // across the four rows, +X is the reference south edge.
                const FQuat R = Datum.GetRotation();
                auto AtLocal = [&](const double LocalX, const double LocalY)
                {
                    return TrainAt + R.RotateVector(
                        FVector(LocalX, LocalY, 0.0));
                };
                const FQuat AlongRows =
                    R * FQuat(FVector::UpVector, PI * 0.5);

                // PR-043 full/empty stillage marshalling: three lanes of
                // four between the row lines, east of the trains.
                for (int32 Lane = 0; Lane < 3; ++Lane)
                {
                    const double LaneX = -1100.0 - 2200.0 * Lane;
                    for (int32 Slot = 0; Slot < 4; ++Slot)
                    {
                        Place(ELBOneFactoryDressingKind::Stillage,
                            AtLocal(LaneX, 3800.0 + 420.0 * Slot)
                                + FVector(0.0, 0.0, 58.0), R);
                    }
                }
                // PR-044 FLT dispatch: the outbound lorry at the east dock.
                Place(ELBOneFactoryDressingKind::Lorry,
                    AtLocal(-3300.0, 6000.0), AlongRows);
                // PR-040 quarantine: a fenced pen with two suspect stillages.
                for (int32 Panel = 0; Panel < 4; ++Panel)
                {
                    Place(ELBOneFactoryDressingKind::Fence,
                        AtLocal(-6800.0 + 150.0 * Panel, 4050.0), R);
                    Place(ELBOneFactoryDressingKind::Fence,
                        AtLocal(-6800.0 + 150.0 * Panel, 4650.0), R);
                }
                Place(ELBOneFactoryDressingKind::Stillage,
                    AtLocal(-6650.0, 4250.0) + FVector(0.0, 0.0, 58.0), R);
                Place(ELBOneFactoryDressingKind::Stillage,
                    AtLocal(-6650.0, 4450.0) + FVector(0.0, 0.0, 58.0), R);
                // PR-039 first-off dimensional scan: light ramp, HMI, bench.
                Place(ELBOneFactoryDressingKind::LampRamp,
                    AtLocal(800.0, 4200.0), AlongRows, 0.9);
                Place(ELBOneFactoryDressingKind::Control,
                    AtLocal(600.0, 3900.0), R);
                Place(ELBOneFactoryDressingKind::Bench,
                    AtLocal(1000.0, 3900.0), R);
                // PR-041 trim scrap collection: a skip row and baler block
                // on the south service edge, fed from the trim/pierce
                // stages.
                for (int32 Skip = 0; Skip < 4; ++Skip)
                {
                    // The reference stands this mesh at z 59: centre pivot.
                    Place(ELBOneFactoryDressingKind::ScrapSkip,
                        AtLocal(1150.0, -700.0 - 380.0 * Skip)
                            + FVector(0.0, 0.0, 59.0), AlongRows);
                }
                Place(ELBOneFactoryDressingKind::Press,
                    AtLocal(1150.0, -2350.0), AlongRows, 0.9);
                // PR-004 destrap cell centrepiece: the six-axis robot and
                // its tool rack inside the existing fence line.
                Place(ELBOneFactoryDressingKind::Robot,
                    AtLocal(-2300.0, -8900.0), AlongRows, 0.9);
                Place(ELBOneFactoryDressingKind::Rack,
                    AtLocal(-2650.0, -8600.0), R);
                // PR-002 certified coil scale: HMI pedestal and bench at
                // the weighing position between receipt and the store.
                Place(ELBOneFactoryDressingKind::Control,
                    AtLocal(-2300.0, -11500.0), R);
                Place(ELBOneFactoryDressingKind::Bench,
                    AtLocal(-2050.0, -11500.0), AlongRows);
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
                static const FName BlankBufferStation(
                    TEXT("OF_PRESS_PREPARED_BLANK_BUFFER_001"));
                static const FName PanelInspectionStation(
                    TEXT("OF_PRESS_PANEL_INSPECTION_001"));
                if (Step.StationId == BlankBufferStation)
                {
                    // Staged blanks waiting for the trains: stillages and a
                    // rack row, so the buffer's 8-second WIP dwell happens
                    // beside machinery instead of on bare floor.
                    Place(ELBOneFactoryDressingKind::Stillage,
                        At + Across * 220.0 + FVector(0.0, 0.0, 58.0),
                        Facing);
                    Place(ELBOneFactoryDressingKind::Stillage,
                        At - Across * 220.0 + FVector(0.0, 0.0, 58.0),
                        Facing);
                    Place(ELBOneFactoryDressingKind::Rack,
                        At - Along * 320.0, FacingIn, Fit);
                    Place(ELBOneFactoryDressingKind::Rack,
                        At + Along * 320.0, FacingIn, Fit);
                }
                else if (Step.StationId == PanelInspectionStation)
                {
                    // Panel inspection: operator bench and the overhead
                    // light ramp, keyed by station id - the press
                    // bQualityGate flag is never true, so keying the ramp
                    // off it left this station bare.
                    Place(ELBOneFactoryDressingKind::Bench,
                        At - Across * 260.0, FacingIn, Fit);
                    Place(ELBOneFactoryDressingKind::LampRamp, At, Facing,
                        FMath::Min(Fit, 1.0));
                }
                // Blank preparation gets the approved S01 destacker if the
                // station stands clear of every train row's measured
                // footprint; stations inside a span stay clear.
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
                        // Test in the datum's local frame - the station is
                        // player-movable and rotatable - and against all four
                        // train rows at the reference 2200 pitch, not just
                        // row A.
                        const FQuat TrainRot =
                            Train->WorldTransform.GetRotation();
                        const FVector TrainCentre =
                            Train->WorldTransform.GetLocation()
                            + TrainRot.RotateVector(
                                FVector(9.25, 2367.5, 0.0));
                        const FVector LocalDelta =
                            TrainRot.UnrotateVector(At - TrainCentre);
                        for (int32 Row = 0; Row < 4; ++Row)
                        {
                            const double RowDeltaX =
                                LocalDelta.X + 2200.0 * Row;
                            if (FMath::Abs(RowDeltaX) <= 900.0
                                && FMath::Abs(LocalDelta.Y) <= 3100.0)
                            {
                                bClearOfTrain = false;
                                break;
                            }
                        }
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
        {
            // The native paint kit, on the line: each process stage is a
            // drive-through module straddling its station, the way the
            // approved mockup draws the ED coat card, so bodies pass through
            // real tunnels instead of between pack-box stand-ins. Each module
            // is scaled to at most 92% of its cell so neighbouring tunnels
            // never interpenetrate; never scaled above authored size.
            auto TunnelScale = [&](const ELBOneFactoryDressingKind Kind)
            {
                const double Length =
                    Kinds[static_cast<int32>(Kind)].LengthCm;
                return FMath::Min(1.0, (CellHalf * 2.0 * 0.92) / Length);
            };
            switch (Step.SemanticStage)
            {
            case ELBOneFactoryVehicleStage::Pretreatment:
                Place(ELBOneFactoryDressingKind::PaintWashTunnel, At, Facing,
                    TunnelScale(ELBOneFactoryDressingKind::PaintWashTunnel));
                break;
            case ELBOneFactoryVehicleStage::EDCoat:
                Place(ELBOneFactoryDressingKind::PaintEDTunnel, At, Facing,
                    TunnelScale(ELBOneFactoryDressingKind::PaintEDTunnel));
                break;
            case ELBOneFactoryVehicleStage::ColourCoat:
                Place(ELBOneFactoryDressingKind::PaintSprayBooth, At, Facing,
                    TunnelScale(ELBOneFactoryDressingKind::PaintSprayBooth));
                // The booth's services stand on its service side.
                Place(ELBOneFactoryDressingKind::PaintAirExtract,
                    At + Across * (CellHalf * 1.15), FacingOut, 1.0);
                Place(ELBOneFactoryDressingKind::PaintServiceSet,
                    At + Across * (CellHalf * 1.15) + Along * 400.0,
                    FacingOut, 1.0);
                break;
            case ELBOneFactoryVehicleStage::Cure:
                Place(ELBOneFactoryDressingKind::PaintCureOven, At, Facing,
                    TunnelScale(ELBOneFactoryDressingKind::PaintCureOven));
                break;
            case ELBOneFactoryVehicleStage::PaintQualityInspection:
                Place(ELBOneFactoryDressingKind::PaintQualityTunnel, At,
                    Facing, TunnelScale(
                        ELBOneFactoryDressingKind::PaintQualityTunnel));
                break;
            default:
                // A stage without a native module keeps the enclosed booth
                // stand-ins rather than an empty station.
                Place(ELBOneFactoryDressingKind::Booth,
                    At + Across * (CellHalf * 0.95), FacingOut, Fit);
                Place(ELBOneFactoryDressingKind::Booth,
                    At - Across * (CellHalf * 0.95), FacingIn, Fit);
                break;
            }
            break;
        }

        case ELBOneFactoryDepartment::Assembly:
        default:
            // The native assembly kit by stage, keeping the readable
            // "station + robot + next part" model where no native module
            // maps.
            switch (Step.SemanticStage)
            {
            case ELBOneFactoryVehicleStage::GeneralAssemblyTrim:
                // The body rides a skillet carrier; the fitting robot works
                // one side with the sequenced parts behind the bench side.
                Place(ELBOneFactoryDressingKind::AssemblySkillet, At, Facing);
                Place(ELBOneFactoryDressingKind::Robot,
                    At + Across * (CellHalf * 0.80), FacingOut, Fit * 0.9);
                Place(ELBOneFactoryDressingKind::Bench,
                    At - Across * (CellHalf * 0.85), FacingIn, Fit);
                Place(ELBOneFactoryDressingKind::AssemblyPartsCart,
                    At - Across * (CellHalf * 1.5), FacingIn);
                break;
            case ELBOneFactoryVehicleStage::PowertrainMarriage:
                Place(ELBOneFactoryDressingKind::AssemblyMarriageGantry, At,
                    Facing);
                Place(ELBOneFactoryDressingKind::Bench,
                    At - Across * (CellHalf * 1.1), FacingIn, Fit);
                break;
            case ELBOneFactoryVehicleStage::RollingChassis:
                Place(ELBOneFactoryDressingKind::AssemblyLiftPlatform, At,
                    Facing);
                Place(ELBOneFactoryDressingKind::AssemblyWheelRack,
                    At + Across * (CellHalf * 0.95), FacingOut);
                Place(ELBOneFactoryDressingKind::AssemblyWheelRack,
                    At - Across * (CellHalf * 0.95), FacingIn);
                break;
            case ELBOneFactoryVehicleStage::EndOfLineInspection:
                Place(ELBOneFactoryDressingKind::AssemblyAlignmentBed, At,
                    Facing);
                Place(ELBOneFactoryDressingKind::AssemblyEOLArch,
                    At + Along * 350.0, Facing);
                break;
            default:
                Place(ELBOneFactoryDressingKind::Robot,
                    At + Across * (CellHalf * 0.80), FacingOut, Fit * 0.9);
                Place(ELBOneFactoryDressingKind::Bench,
                    At - Across * (CellHalf * 0.85), FacingIn, Fit);
                Place(ELBOneFactoryDressingKind::Rack,
                    At - Across * (CellHalf * 1.7), FacingIn, Fit);
                break;
            }
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

        // The weld presentation carries its own guard line at +-1570; the
        // generic fence at +-CellHalf*2.35 lands at +-1222 at the 2000 cm
        // weld pitch - straight through 34 of the 36 robot bases - and
        // would remain a redundant inner fence even with the robots pulled
        // in. Body guards itself, like Press.
        if (Step.Department != ELBOneFactoryDepartment::Body)
        {
            const int32 PanelsPerSide = FMath::Max(1, FMath::FloorToInt(
                static_cast<float>(CellHalf * 1.6 / Kinds[
                    static_cast<int32>(
                        ELBOneFactoryDressingKind::Fence)].LengthCm)));
            for (int32 Side = -1; Side <= 1; Side += 2)
            {
                for (int32 Panel = 0; Panel < PanelsPerSide; ++Panel)
                {
                    const double Offset = -CellHalf * 0.8
                        + (Panel + 1) * Kinds[static_cast<int32>(
                            ELBOneFactoryDressingKind::Fence)].LengthCm;
                    Place(ELBOneFactoryDressingKind::Fence,
                        At + Across * (CellHalf * 2.35 * Side)
                            + Along * Offset,
                        Facing);
                }
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
        // continuous rather than a row of islands. Long runs follow the same
        // Manhattan legs as the painted flow routes - along the line axis,
        // then across - instead of cutting a diagonal through open floor.
        if (bHasNext)
        {
            const FVector Next = Route[Index + 1].WorldTransform.GetLocation();
            const double SectionCm = Kinds[static_cast<int32>(
                ELBOneFactoryDressingKind::Conveyor)].LengthCm;
            auto LayLeg = [&](const FVector& RawFrom, const FVector& RawTo)
            {
                // Keep the sections clear of the station cells at each end:
                // conveyors starting exactly at a station centre ran through
                // the weld fixture slabs and any parked body.
                constexpr double CellClearanceCm = 500.0;
                const FVector RawFlat(RawTo.X - RawFrom.X,
                    RawTo.Y - RawFrom.Y, 0.0);
                if (RawFlat.Size() < SectionCm + 2.0 * CellClearanceCm)
                {
                    return;
                }
                const FVector Trim =
                    RawFlat.GetSafeNormal() * CellClearanceCm;
                const FVector From = RawFrom + Trim;
                const FVector To = RawTo - Trim;
                const FVector Flat(To.X - From.X, To.Y - From.Y, 0.0);
                const double Gap = Flat.Size();
                if (Gap < SectionCm)
                {
                    return;
                }
                const FVector Dir = Flat.GetSafeNormal();
                const FQuat LegFacing =
                    FRotationMatrix::MakeFromX(Dir).ToQuat();
                const int32 Sections =
                    FMath::FloorToInt(static_cast<float>(Gap / SectionCm));
                for (int32 Section = 0; Section < Sections; ++Section)
                {
                    const double Travelled =
                        (Section + 0.5) * SectionCm - Gap * 0.5;
                    Place(ELBOneFactoryDressingKind::Conveyor,
                        FMath::Lerp(From, To, 0.5) + Dir * Travelled,
                        LegFacing);
                }
            };
            if (FMath::Abs(Next.X - At.X) > 600.0
                && FMath::Abs(Next.Y - At.Y) > 600.0)
            {
                const FVector Corner(Next.X, At.Y, At.Z);
                LayLeg(At, Corner);
                LayLeg(Corner, Next);
            }
            else
            {
                LayLeg(At, Next);
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
            NewObject<UInstancedStaticMeshComponent>(this);
        if (Cube && ApronBatch)
        {
            DynamicPieces.Add(ApronBatch);
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

    // The production-flow route, painted on the floor in brand green the way
    // the approved Cairnwell mockup draws it: one stripe per consecutive
    // station pair, the long inter-department runs included, so the whole
    // coils-to-dispatch path reads from the management camera.
    {
        UStaticMesh* Cube = Cast<UStaticMesh>(StaticLoadObject(
            UStaticMesh::StaticClass(), nullptr,
            TEXT("/Engine/BasicShapes/Cube.Cube")));
        UMaterialInterface* Base = Cast<UMaterialInterface>(
            StaticLoadObject(UMaterialInterface::StaticClass(), nullptr,
                TEXT("/Engine/BasicShapes/BasicShapeMaterial")
                TEXT(".BasicShapeMaterial")));
        UInstancedStaticMeshComponent* RouteBatch =
            NewObject<UInstancedStaticMeshComponent>(this);
        if (Cube && Base && RouteBatch)
        {
            DynamicPieces.Add(RouteBatch);
            RouteBatch->SetupAttachment(SceneRoot);
            RouteBatch->SetMobility(EComponentMobility::Movable);
            RouteBatch->SetCollisionEnabled(ECollisionEnabled::NoCollision);
            RouteBatch->SetCanEverAffectNavigation(false);
            RouteBatch->SetStaticMesh(Cube);
            if (UMaterialInstanceDynamic* Paint =
                    UMaterialInstanceDynamic::Create(Base, this))
            {
                const FLinearColor RouteGreen =
                    FLinearColor::FromSRGBColor(FColor::FromHex(TEXT("2F8A5F")));
                Paint->SetVectorParameterValue(TEXT("Color"), RouteGreen);
                Paint->SetVectorParameterValue(TEXT("BaseColor"), RouteGreen);
                RouteBatch->SetMaterial(0, Paint);
                RouteMaterial = Paint;
            }
            RouteBatch->RegisterComponent();

            auto AddStripe = [&](const FVector& From, const FVector& To)
            {
                const FVector Flat(To.X - From.X, To.Y - From.Y, 0.0);
                const double Length = Flat.Size();
                if (Length < 50.0)
                {
                    return;
                }
                FTransform Stripe;
                Stripe.SetLocation(FVector(
                    (From.X + To.X) * 0.5, (From.Y + To.Y) * 0.5, 4.0));
                Stripe.SetRotation(
                    FRotationMatrix::MakeFromX(Flat).ToQuat());
                // Half a stripe width of overrun so the two legs of a
                // Manhattan corner join without a notch.
                Stripe.SetScale3D(
                    FVector(Length / 100.0 + 0.6, 1.2, 0.04));
                if (RouteBatch->AddInstance(Stripe, true) != INDEX_NONE)
                {
                    ++PieceCount;
                }
            };
            // Orthogonal legs, the way the approved mockup paints routes:
            // along the line axis first, then across to the next station.
            for (int32 Index = 0; Index + 1 < Route.Num(); ++Index)
            {
                const FVector From = Route[Index].WorldTransform.GetLocation();
                const FVector To =
                    Route[Index + 1].WorldTransform.GetLocation();
                const FVector Corner(To.X, From.Y, 0.0);
                AddStripe(From, Corner);
                AddStripe(Corner, To);
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
