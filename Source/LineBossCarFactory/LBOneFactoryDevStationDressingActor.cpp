#include "LBOneFactoryDevStationDressingActor.h"

#include "Components/InstancedStaticMeshComponent.h"
#include "Engine/StaticMesh.h"
#include "Engine/World.h"
#include "EngineUtils.h"
#include "LBOneFactoryBodyWeldStarterLayout.h"
#include "LBOneFactoryProductionFlow.h"
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
        { TEXT("Dress_PressCycleOverlay"),
          TEXT("/Engine/BasicShapes/Cube.Cube"), 5770.0 },
        { TEXT("Dress_Coil"),
          TEXT("/Engine/BasicShapes/Cylinder.Cylinder"), 181.0 },
        { TEXT("Dress_CoilStand"),
          TEXT("/Engine/BasicShapes/Cube.Cube"), 190.0 },
        { TEXT("Dress_Stillage"),
          TEXT("/Game/LineBoss/Candidates/WeldShop/PanelStillageRuntime_v001"
               "/SM_LB_PanelStillage_Runtime_v001"), 190.0 },
        { TEXT("Dress_Lorry"),
          TEXT("/Engine/BasicShapes/Cube.Cube"), 800.0 },
        { TEXT("Dress_Destacker"),
          TEXT("/Game/LineBoss/Candidates/PressShop/CleanRebuild_v20260809_v012"
               "/PressTrains/SM_CA_MW_S01_Destack_Approved_v006"), 400.0 },
        // The native paint kit, measured 2026-08-16: floor pivots, true scale.
        { TEXT("Dress_PaintWashTunnel"),
          TEXT("/Game/LineBoss/Candidates/PaintShop/PaintLineNativeKit_v001"
               "/Process/SM_LB_Paint_PretreatmentWashTunnel_v001"), 852.0 },
        // The commissioned native ED dip tunnel replaces the flash-off
        // stand-in at the ED coat stage (measured 812 x 616 x 625).
        { TEXT("Dress_PaintEDTunnel"),
          TEXT("/Game/LineBoss/Candidates/PaintShop/EDDipTunnel_v001"
               "/SM_LB_Paint_EDDipTunnel_v001"), 812.0 },
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
        // Owner-commissioned models, measured after import 2026-08-16.
        { TEXT("Dress_PressCoilScale"),
          TEXT("/Game/LineBoss/Candidates/PressShop/CoilScale_v001"
               "/SM_LB_Press_CoilScalePlatform_v001"), 424.0 },
        { TEXT("Dress_PressScrapBaler"),
          TEXT("/Game/LineBoss/Candidates/PressShop/ScrapBaler_v001"
               "/SM_LB_Press_ScrapBaler_v001"), 446.0 },
        { TEXT("Dress_WeldClosureTurntable"),
          TEXT("/Game/LineBoss/Candidates/WeldShop/ClosureTurntable_v001"
               "/SM_LB_BodyShop_ClosureTurntable_v001"), 280.0 },
    };
}

ALBOneFactoryDevStationDressingActor::ALBOneFactoryDevStationDressingActor()
{
    using namespace LBOneFactoryDressingPrivate;

    PrimaryActorTick.bCanEverTick = true;
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
    for (int32 Joint = 0; Joint < 7; ++Joint)
    {
        UInstancedStaticMeshComponent* Batch =
            CreateDefaultSubobject<UInstancedStaticMeshComponent>(
                FName(*FString::Printf(TEXT("Dress_RobotJoint%d"), Joint)));
        Batch->SetupAttachment(SceneRoot);
        Batch->SetMobility(EComponentMobility::Movable);
        Batch->SetCollisionEnabled(ECollisionEnabled::NoCollision);
        Batch->SetCollisionResponseToAllChannels(ECR_Ignore);
        Batch->SetGenerateOverlapEvents(false);
        Batch->SetCanEverAffectNavigation(false);
        Batch->SetReceivesDecals(false);
        RobotJointBatches.Add(Batch);
    }

    Tags.AddUnique(GetDressingTag());
    Tags.AddUnique(TEXT("LB.Environment.VisualOnly"));
    Tags.AddUnique(TEXT("LB.NotProcessWIP"));
}

FName ALBOneFactoryDevStationDressingActor::GetDressingTag()
{
    return FName(TEXT("LB.OneFactory.DevStationDressing"));
}

void ALBOneFactoryDevStationDressingActor::Tick(const float DeltaSeconds)
{
    Super::Tick(DeltaSeconds);
    if (!PressTransferCarriage) return;

    bool bTrainActive = false;
    float CycleProgress = 0.0f;
    if (UWorld* World = GetWorld())
    {
        for (TActorIterator<ALBOneFactoryProductionFlowAuthority> It(World);
            It; ++It)
        {
            if (!IsValid(*It)) continue;
            const FLBOneFactoryProductionLedgerState Ledger =
                It->CaptureLedger();
            for (const FLBOneFactoryVehicleUnitState& Unit : Ledger.Units)
            {
                if (Unit.bRuntimeStarted
                    && Unit.Department == ELBOneFactoryDepartment::Press)
                {
                    bTrainActive = true;
                    if (Unit.RuntimeCycleDurationSeconds > KINDA_SMALL_NUMBER)
                    {
                        CycleProgress = FMath::Fmod(
                            Unit.RuntimeCycleElapsedSeconds
                                / Unit.RuntimeCycleDurationSeconds,
                            1.0f);
                    }
                    break;
                }
            }
            break;
        }
    }

    PressTransferCarriage->SetVisibility(bTrainActive, true);
    for (UStaticMeshComponent* Ram : PressRamAssemblies)
    {
        if (Ram) Ram->SetVisibility(bTrainActive, true);
    }
    if (!bTrainActive) return;

    // This visual carriage is enabled only during a live press step. Its
    // short pass makes motion obvious from the management camera.
    PressTransferSeconds = FMath::Fmod(PressTransferSeconds + DeltaSeconds,
        3.6f);
    const float Alpha = FMath::Abs(PressTransferSeconds / 1.8f - 1.0f);
    const float Travel = FMath::Lerp(-2300.0f, 2300.0f, Alpha);
    PressTransferCarriage->SetWorldLocation(
        PressTransferOrigin + PressTransferRotation.RotateVector(
            FVector(0.0f, Travel, 560.0f)));

    // Stagger the five strokes through the real deterministic station cycle.
    // This is presentation-only: the production ledger remains authoritative.
    for (int32 Index = 0; Index < PressRamAssemblies.Num(); ++Index)
    {
        UStaticMeshComponent* Ram = PressRamAssemblies[Index];
        if (!Ram || !PressRamOrigins.IsValidIndex(Index)) continue;
        const float Phase = FMath::Fmod(CycleProgress + 0.19f * Index, 1.0f);
        const float Stroke = FMath::Pow(FMath::Sin(PI * Phase), 6.0f);
        Ram->SetWorldLocation(PressRamOrigins[Index]
            + PressTransferRotation.RotateVector(FVector(0.0f, 0.0f,
                -135.0f * Stroke)));
    }
}

void ALBOneFactoryDevStationDressingActor::Place(
    const ELBOneFactoryDressingKind Kind, const FVector& Where,
    const FQuat& Rotation, const double UniformScale)
{
    const int32 Index = static_cast<int32>(Kind);
    FTransform Transform;
    Transform.SetLocation(Where);
    Transform.SetRotation(Rotation);
    Transform.SetScale3D(FVector(UniformScale));

    // Robots are always the project's own seven-joint unit; the joints
    // share one baked-pivot transform. The pack robot stays only as a
    // fallback when the native meshes are absent.
    if (Kind == ELBOneFactoryDressingKind::Robot
        && RobotJointBatches.Num() == 7 && RobotJointBatches[0]
        && RobotJointBatches[0]->GetStaticMesh())
    {
        for (UInstancedStaticMeshComponent* Joint : RobotJointBatches)
        {
            Joint->AddInstance(Transform, true);
        }
        ++PieceCount;
        return;
    }

    if (!Batches.IsValidIndex(Index) || !Batches[Index]
        || !Batches[Index]->GetStaticMesh())
    {
        return;
    }
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
        if (Index == 0)
        {
            static const TCHAR* JointNames[7] = {
                TEXT("Base"), TEXT("J1"), TEXT("J2"), TEXT("J3"),
                TEXT("J4"), TEXT("J5"), TEXT("J6") };
            for (int32 Joint = 0; Joint < 7; ++Joint)
            {
                RobotJointBatches[Joint]->ClearInstances();
                UStaticMesh* JointMesh = Cast<UStaticMesh>(StaticLoadObject(
                    UStaticMesh::StaticClass(), nullptr,
                    *FString::Printf(TEXT(
                        "/Game/LineBoss/Candidates/WeldShop"
                        "/BodyShopRobotNative_v001/Robot"
                        "/SM_LB_BodyShopRobotNative_%s_v001"),
                        JointNames[Joint])));
                RobotJointBatches[Joint]->SetStaticMesh(JointMesh);
            }
        }
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

    // Closure-duty stations, resolved once per build from the weld layout
    // authority (never static: state must not leak across worlds).
    TSet<FName> ClosureStations;
    bool bClosureStationsResolved = false;

    // Rebuilds must not NewObject over the previous build's live components.
    for (UActorComponent* Piece : DynamicPieces)
    {
        if (Piece)
        {
            Piece->DestroyComponent();
        }
    }
    DynamicPieces.Reset();
    PressTransferCarriage = nullptr;
    PressRamAssemblies.Reset();
    PressRamOrigins.Reset();
    PressTransferSeconds = 0.0f;

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
            // The commissioned press shop has one coherent production train:
            // coil receipt -> blank preparation -> Train A -> inspection ->
            // stillage dispatch.  Earlier recovery dressing placed this whole
            // 57.7 m Train A mesh four times across the bay, which made the
            // player view read as duplicate, intersecting presses rather than
            // a legible line.  Keep the train singular and let the dedicated
            // route stations own all surrounding logistics.
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
                // The OneFactory PressStarterPresentation owns the one
                // verified native aggregate at this datum.  Do not place a
                // second legacy train over it: that was the source of the
                // duplicated, intersecting machines in the player view.
                if (UStaticMesh* MotionMesh = Cast<UStaticMesh>(
                    StaticLoadObject(UStaticMesh::StaticClass(), nullptr,
                        Kinds[static_cast<int32>(
                            ELBOneFactoryDressingKind::PressCycleOverlay)].Path)))
                {
                    UMaterialInterface* Green = Cast<UMaterialInterface>(
                        StaticLoadObject(UMaterialInterface::StaticClass(), nullptr,
                            TEXT("/Game/LineBoss/Factory/OneFactory/v001/Native/Press/DetailedPresentation_v001/Materials/M_CA_MW_PR009_LayeredCairnwellGreen_v086.M_CA_MW_PR009_LayeredCairnwellGreen_v086")));
                    UMaterialInterface* Safety = Cast<UMaterialInterface>(
                        StaticLoadObject(UMaterialInterface::StaticClass(), nullptr,
                            TEXT("/Game/LineBoss/Factory/OneFactory/v001/Native/Press/DetailedPresentation_v001/Materials/M_CA_MW_PR009_LayeredSafetyYellow_v086.M_CA_MW_PR009_LayeredSafetyYellow_v086")));

                    // A moving crossbar makes the real active press cycle
                    // legible. It is hidden unless Press owns live WIP.
                    PressTransferCarriage = NewObject<UStaticMeshComponent>(this);
                    DynamicPieces.Add(PressTransferCarriage);
                    PressTransferCarriage->SetupAttachment(SceneRoot);
                    PressTransferCarriage->SetMobility(EComponentMobility::Movable);
                    PressTransferCarriage->SetCollisionEnabled(ECollisionEnabled::NoCollision);
                    PressTransferCarriage->SetCanEverAffectNavigation(false);
                    PressTransferCarriage->SetStaticMesh(MotionMesh);
                    PressTransferCarriage->SetMaterial(0, Safety);
                    PressTransferCarriage->SetWorldScale3D(FVector(5.5f, 0.30f, 0.15f));
                    PressTransferOrigin = TrainAt;
                    PressTransferRotation = Datum.GetRotation();
                    PressTransferCarriage->SetWorldLocation(
                        PressTransferOrigin + PressTransferRotation.RotateVector(
                            FVector(0.0f, -2300.0f, 560.0f)));
                    PressTransferCarriage->SetWorldRotation(PressTransferRotation);
                    PressTransferCarriage->SetVisibility(false);
                    PressTransferCarriage->RegisterComponent();
                    ++PieceCount;

                    // Five clear rams sit over the existing native train's
                    // five operations.  They are motion overlays, not WIP
                    // or another machine set, and never affect collision.
                    for (int32 PressIndex = 0; PressIndex < 5; ++PressIndex)
                    {
                        UStaticMeshComponent* Ram = NewObject<UStaticMeshComponent>(this);
                        DynamicPieces.Add(Ram);
                        PressRamAssemblies.Add(Ram);
                        Ram->SetupAttachment(SceneRoot);
                        Ram->SetMobility(EComponentMobility::Movable);
                        Ram->SetCollisionEnabled(ECollisionEnabled::NoCollision);
                        Ram->SetCanEverAffectNavigation(false);
                        Ram->SetStaticMesh(MotionMesh);
                        Ram->SetMaterial(0, Green);
                        Ram->SetWorldScale3D(FVector(6.4f, 2.25f, 0.34f));
                        const FVector Origin = TrainAt + Datum.GetRotation()
                            .RotateVector(FVector(0.0f,
                                -1600.0f + 800.0f * PressIndex, 650.0f));
                        PressRamOrigins.Add(Origin);
                        Ram->SetWorldLocation(Origin);
                        Ram->SetWorldRotation(Datum.GetRotation());
                        Ram->SetVisibility(false);
                        Ram->RegisterComponent();
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

                // A single clear outbound lane holds the finished panel
                // stillages.  It remains visibly separate from the train and
                // leaves an uninterrupted service aisle around the press.
                for (int32 Slot = 0; Slot < 4; ++Slot)
                {
                    Place(ELBOneFactoryDressingKind::Stillage,
                        AtLocal(-1500.0, 3800.0 + 460.0 * Slot)
                            + FVector(0.0, 0.0, 58.0), R);
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
                // PR-041 trim scrap collection: a skip row and the
                // commissioned baler on the south service edge, fed from
                // the trim/pierce stages.
                for (int32 Skip = 0; Skip < 4; ++Skip)
                {
                    // The reference stands this mesh at z 59: centre pivot.
                    Place(ELBOneFactoryDressingKind::ScrapSkip,
                        AtLocal(1150.0, -700.0 - 380.0 * Skip)
                            + FVector(0.0, 0.0, 59.0), AlongRows);
                }
                Place(ELBOneFactoryDressingKind::PressScrapBaler,
                    AtLocal(1150.0, -2350.0), AlongRows);
                // PR-004 destrap cell centrepiece: the six-axis robot and
                // its tool rack inside the existing fence line.
                Place(ELBOneFactoryDressingKind::Robot,
                    AtLocal(-2300.0, -8900.0), AlongRows, 0.9);
                Place(ELBOneFactoryDressingKind::Rack,
                    AtLocal(-2650.0, -8600.0), R);
                // PR-002 certified coil scale: the commissioned flush
                // platform (deck, load cells, HMI post) at the weighing
                // position between receipt and the store.
                Place(ELBOneFactoryDressingKind::PressCoilScale,
                    AtLocal(-2300.0, -11500.0), AlongRows);
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
                        // Test in the datum's local frame.  The completed
                        // train is singular, so the blank-prep destacker must
                        // only clear its one real footprint.
                        const FQuat TrainRot =
                            Train->WorldTransform.GetRotation();
                        const FVector TrainCentre =
                            Train->WorldTransform.GetLocation()
                            + TrainRot.RotateVector(
                                FVector(9.25, 2367.5, 0.0));
                        const FVector LocalDelta =
                            TrainRot.UnrotateVector(At - TrainCentre);
                        if (FMath::Abs(LocalDelta.X) <= 900.0
                            && FMath::Abs(LocalDelta.Y) <= 3100.0)
                        {
                            bClearOfTrain = false;
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
        {
            // No machines here - the frozen weld starter presentation
            // renders the native robots under its exact-count contract (489
            // as of v002); pack robots on top were duplicates of release
            // content. The one addition is the commissioned closure
            // turntable, placed outside the presentation's own guard line
            // at the stations whose robots carry the ClosureHandling duty.
            if (!bClosureStationsResolved)
            {
                bClosureStationsResolved = true;
                for (TActorIterator<ALBOneFactoryBodyWeldStarterLayoutAuthority>
                    It(World); It; ++It)
                {
                    if (!IsValid(*It))
                    {
                        continue;
                    }
                    const FLBOneFactoryBodyWeldLayoutState Layout =
                        It->CaptureLayout();
                    for (const FLBOneFactoryBodyWeldStationState& Station :
                        Layout.Stations)
                    {
                        using RR = ELBOneFactoryBodyWeldRobotRole;
                        if (Station.LeftRobotRole == RR::ClosureHandling
                            || Station.RightRobotRole == RR::ClosureHandling)
                        {
                            ClosureStations.Add(Station.StationId);
                        }
                    }
                    break;
                }
            }
            if (ClosureStations.Contains(Step.StationId))
            {
                // 1900 cm across the line clears the presentation's guard
                // panels at +-1570.
                Place(ELBOneFactoryDressingKind::WeldClosureTurntable,
                    At + Across * 1900.0, FacingIn);
            }
            break;
        }

        case ELBOneFactoryDepartment::Paint:
            // Deliberately no process modules here. The frozen paint starter
            // presentation already stands the native kit at these exact
            // canonical station transforms - wash tunnel, the tracked ED
            // line with its open treatment tanks and immersed body, the
            // spray booth with its extraction and service sets, the cure
            // oven and the quality light tunnel - under its own exact-count
            // contract. The dressing used to place a second copy of each at
            // the same transform: same mesh, same place, total z-fight, and
            // the ED enclosure hid the very tracked line the contract exists
            // to show. This is the Body-branch lesson (a duplicate robot set
            // over release content) applied to Paint.
            //
            // Standing the commissioned SM_LB_Paint_EDDipTunnel_v001 as
            // real content belongs in a versioned paint presentation v002,
            // following the weld v002/v003 template - not as an overlay.
            break;

        case ELBOneFactoryDepartment::Assembly:
        default:
            // The native assembly kit by stage, keeping the readable
            // "station + robot + next part" model where no native module
            // maps.
            // The frozen assembly presentation owns the station centre: a
            // skillet carrier at every one of the 24 positions plus the
            // per-operation fixture (the marriage gantry among them). The
            // dressing adds only what the contract lacks, and never at the
            // centre - a second skillet at the same transform z-fought, and
            // the lift platform and alignment bed ran through the carrier.
            switch (Step.SemanticStage)
            {
            case ELBOneFactoryVehicleStage::GeneralAssemblyTrim:
                // The fitting robot works one side with the sequenced parts
                // behind the bench side; the carrier is release content.
                Place(ELBOneFactoryDressingKind::Robot,
                    At + Across * (CellHalf * 0.80), FacingOut, Fit * 0.9);
                Place(ELBOneFactoryDressingKind::Bench,
                    At - Across * (CellHalf * 0.85), FacingIn, Fit);
                Place(ELBOneFactoryDressingKind::AssemblyPartsCart,
                    At - Across * (CellHalf * 1.5), FacingIn);
                break;
            case ELBOneFactoryVehicleStage::PowertrainMarriage:
                // The presentation stands the gantry itself.
                Place(ELBOneFactoryDressingKind::Bench,
                    At - Across * (CellHalf * 1.1), FacingIn, Fit);
                break;
            case ELBOneFactoryVehicleStage::RollingChassis:
                // The ergonomic platform stands beside the line as station
                // equipment rather than through the carrier.
                Place(ELBOneFactoryDressingKind::AssemblyLiftPlatform,
                    At + Across * (CellHalf * 1.55), FacingOut);
                Place(ELBOneFactoryDressingKind::AssemblyWheelRack,
                    At + Across * (CellHalf * 0.95), FacingOut);
                Place(ELBOneFactoryDressingKind::AssemblyWheelRack,
                    At - Across * (CellHalf * 0.95), FacingIn);
                break;
            case ELBOneFactoryVehicleStage::EndOfLineInspection:
                // The alignment bed sits off-line; the arch spans the line
                // downstream of the station centre, clear of the carrier.
                Place(ELBOneFactoryDressingKind::AssemblyAlignmentBed,
                    At + Across * (CellHalf * 1.55), FacingOut);
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
