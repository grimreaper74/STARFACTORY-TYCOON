#include "LBOneFactoryPressStarterPresentationActor.h"

#include "Components/SceneComponent.h"
#include "Components/StaticMeshComponent.h"
#include "Engine/StaticMesh.h"
#include "Materials/MaterialInterface.h"
#include "UObject/ConstructorHelpers.h"

namespace LBOneFactoryPressPresentationPrivate
{
    constexpr int32 ExpectedVisualBatchCount = 1;
    constexpr int32 ExpectedRenderedAggregateCount = 1;
    constexpr int32 ExpectedLogicalItemCount = 268;
    constexpr int32 ExpectedMaterialSlotCount = 306;
    constexpr float TransformTolerance = 0.01f;

    const TCHAR* DetailedPresentationRoot =
        TEXT("/Game/LineBoss/Factory/OneFactory/v001/Native/Press/DetailedPresentation_v001/");
    const TCHAR* DetailedMeshPath = TEXT(
        "/Game/LineBoss/Factory/OneFactory/v001/Native/Press/DetailedPresentation_v001/"
        "SM_OneFactoryDetailedPressPresentation_v001."
        "SM_OneFactoryDetailedPressPresentation_v001");
    const TCHAR* DetailedMaterialPaths[] =
    {
        TEXT("/Game/LineBoss/Factory/OneFactory/v001/Native/Press/DetailedPresentation_v001/Materials/M_CA_MW_PR009_AmberSafetyActive_v086.M_CA_MW_PR009_AmberSafetyActive_v086"),
        TEXT("/Game/LineBoss/Factory/OneFactory/v001/Native/Press/DetailedPresentation_v001/Materials/M_CA_MW_PR009_DriveBlue_v086.M_CA_MW_PR009_DriveBlue_v086"),
        TEXT("/Game/LineBoss/Factory/OneFactory/v001/Native/Press/DetailedPresentation_v001/Materials/M_CA_MW_PR009_EStopRed_v086.M_CA_MW_PR009_EStopRed_v086"),
        TEXT("/Game/LineBoss/Factory/OneFactory/v001/Native/Press/DetailedPresentation_v001/Materials/M_CA_MW_PR009_LabelWhite_v086.M_CA_MW_PR009_LabelWhite_v086"),
        TEXT("/Game/LineBoss/Factory/OneFactory/v001/Native/Press/DetailedPresentation_v001/Materials/M_CA_MW_PR009_LayeredCairnwellGreen_v086.M_CA_MW_PR009_LayeredCairnwellGreen_v086"),
        TEXT("/Game/LineBoss/Factory/OneFactory/v001/Native/Press/DetailedPresentation_v001/Materials/M_CA_MW_PR009_LayeredFoundryCharcoal_v086.M_CA_MW_PR009_LayeredFoundryCharcoal_v086"),
        TEXT("/Game/LineBoss/Factory/OneFactory/v001/Native/Press/DetailedPresentation_v001/Materials/M_CA_MW_PR009_LayeredSafetyYellow_v086.M_CA_MW_PR009_LayeredSafetyYellow_v086"),
        TEXT("/Game/LineBoss/Factory/OneFactory/v001/Native/Press/DetailedPresentation_v001/Materials/M_CA_MW_PR009_LayeredServiceGrey_v086.M_CA_MW_PR009_LayeredServiceGrey_v086"),
        TEXT("/Game/LineBoss/Factory/OneFactory/v001/Native/Press/DetailedPresentation_v001/Materials/M_CA_MW_PR009_MachinedSteel_v086.M_CA_MW_PR009_MachinedSteel_v086"),
        TEXT("/Game/LineBoss/Factory/OneFactory/v001/Native/Press/DetailedPresentation_v001/Materials/M_CA_MW_PR009_OiledBlankSteel_v086.M_CA_MW_PR009_OiledBlankSteel_v086"),
        TEXT("/Game/LineBoss/Factory/OneFactory/v001/Native/Press/DetailedPresentation_v001/Materials/M_CA_MW_PR009_Rubber_v086.M_CA_MW_PR009_Rubber_v086"),
        TEXT("/Game/LineBoss/Factory/OneFactory/v001/Native/Press/DetailedPresentation_v001/Materials/M_CA_MW_PR009_SensorGlass_v086.M_CA_MW_PR009_SensorGlass_v086"),
        TEXT("/Game/LineBoss/Factory/OneFactory/v001/Native/Press/DetailedPresentation_v001/Materials/M_CA_MW_PT_ServiceCopper_v383.M_CA_MW_PT_ServiceCopper_v383")
    };
    const FVector DetailedAggregateLocalLocationCm(9.25f, 2367.5f, 0.0f);
    const FVector DetailedAggregateLocalScale(100.0f, 100.0f, 100.0f);
    const TCHAR* ExpectedPresentationClassPath =
        TEXT("/Script/LineBossCarFactory.LBOneFactoryPressStarterPresentationActor");

    const FLBOneFactoryPressStarterStationState* FindStation(
        const FLBOneFactoryPressStarterLayoutState& Layout,
        const ELBOneFactoryPressStarterRole Role)
    {
        return Layout.Stations.FindByPredicate([Role](
            const FLBOneFactoryPressStarterStationState& Station)
        {
            return Station.Role == Role;
        });
    }

    const FLBOneFactoryPressStarterStationState* FindStation(
        const FLBOneFactoryPressStarterLayoutState& Layout,
        const FName StationId)
    {
        return Layout.Stations.FindByPredicate([StationId](
            const FLBOneFactoryPressStarterStationState& Station)
        {
            return Station.StationId == StationId;
        });
    }

    bool IsFiniteTransform(const FTransform& Transform)
    {
        const FVector Location = Transform.GetLocation();
        const FVector Scale = Transform.GetScale3D();
        const FQuat Rotation = Transform.GetRotation();
        return !Transform.ContainsNaN() && Rotation.IsNormalized()
            && FMath::IsFinite(Location.X) && FMath::IsFinite(Location.Y)
            && FMath::IsFinite(Location.Z) && FMath::IsFinite(Scale.X)
            && FMath::IsFinite(Scale.Y) && FMath::IsFinite(Scale.Z)
            && Scale.GetMin() > 0.0f;
    }

    bool SameItem(const FLBOneFactoryPressPresentationItem& Left,
        const FLBOneFactoryPressPresentationItem& Right)
    {
        return Left.Version == Right.Version
            && Left.PresentationId == Right.PresentationId
            && Left.StationId == Right.StationId
            && Left.Role == Right.Role
            && Left.Batch == Right.Batch
            && Left.WorldTransform.Equals(Right.WorldTransform,
                TransformTolerance)
            && Left.bRepresentsProcessWIP == Right.bRepresentsProcessWIP;
    }

    FString MakePresentationId(const FName StationId, const FString& Suffix)
    {
        return FString::Printf(TEXT("OF_PRESS_VIS_%s_%s"),
            *StationId.ToString(), *Suffix);
    }

    struct FStationBuilder
    {
        TArray<FLBOneFactoryPressPresentationItem>& Items;
        const FLBOneFactoryPressStarterStationState& Station;

        void Add(const FString& Suffix,
            const ELBOneFactoryPressPresentationBatch Batch,
            const FVector& LocalLocation, const FVector& DimensionsCm,
            const FRotator& LocalRotation = FRotator::ZeroRotator)
        {
            FLBOneFactoryPressPresentationItem& Item =
                Items.AddDefaulted_GetRef();
            Item.PresentationId = FName(*MakePresentationId(
                Station.StationId, Suffix));
            Item.StationId = Station.StationId;
            Item.Role = Station.Role;
            Item.Batch = Batch;
            const FTransform LocalTransform(LocalRotation, LocalLocation,
                DimensionsCm / 100.0f);
            Item.WorldTransform = LocalTransform * Station.WorldTransform;
            Item.bRepresentsProcessWIP = false;
        }

        void AddFootprintAndStatus()
        {
            const FVector Half = Station.FootprintSizeCm * 0.5f;
            constexpr float LineWidthCm = 18.0f;
            constexpr float PaintHeightCm = 4.0f;
            Add(TEXT("FOOTPRINT_SOUTH"),
                ELBOneFactoryPressPresentationBatch::FloorRouteCube,
                FVector(0.0f, -Half.Y + LineWidthCm * 0.5f,
                    PaintHeightCm * 0.5f),
                FVector(Station.FootprintSizeCm.X, LineWidthCm,
                    PaintHeightCm));
            Add(TEXT("FOOTPRINT_NORTH"),
                ELBOneFactoryPressPresentationBatch::FloorRouteCube,
                FVector(0.0f, Half.Y - LineWidthCm * 0.5f,
                    PaintHeightCm * 0.5f),
                FVector(Station.FootprintSizeCm.X, LineWidthCm,
                    PaintHeightCm));
            Add(TEXT("FOOTPRINT_WEST"),
                ELBOneFactoryPressPresentationBatch::FloorRouteCube,
                FVector(-Half.X + LineWidthCm * 0.5f, 0.0f,
                    PaintHeightCm * 0.5f),
                FVector(LineWidthCm,
                    Station.FootprintSizeCm.Y - LineWidthCm * 2.0f,
                    PaintHeightCm));
            Add(TEXT("FOOTPRINT_EAST"),
                ELBOneFactoryPressPresentationBatch::FloorRouteCube,
                FVector(Half.X - LineWidthCm * 0.5f, 0.0f,
                    PaintHeightCm * 0.5f),
                FVector(LineWidthCm,
                    Station.FootprintSizeCm.Y - LineWidthCm * 2.0f,
                    PaintHeightCm));
            const FVector MarkerLocation(Half.X - 90.0f,
                Half.Y - 90.0f, 100.0f);
            Add(TEXT("STATUS_POST"),
                ELBOneFactoryPressPresentationBatch::TealStructureCube,
                MarkerLocation, FVector(32.0f, 32.0f, 200.0f));
            Add(TEXT("STATUS_CAP"),
                ELBOneFactoryPressPresentationBatch::StatusCube,
                MarkerLocation + FVector(0.0f, 0.0f, 125.0f),
                FVector(62.0f, 62.0f, 50.0f));
        }
    };

    void BuildInboundReceiving(
        TArray<FLBOneFactoryPressPresentationItem>& Items,
        const FLBOneFactoryPressStarterStationState& Station)
    {
        FStationBuilder B{Items, Station};
        B.Add(TEXT("AGV_DECK_LOWER"),
            ELBOneFactoryPressPresentationBatch::GraphiteCube,
            FVector(-250.0f, 0.0f, 90.0f),
            FVector(1300.0f, 720.0f, 150.0f));
        B.Add(TEXT("AGV_DECK_UPPER"),
            ELBOneFactoryPressPresentationBatch::TealStructureCube,
            FVector(-250.0f, 0.0f, 190.0f),
            FVector(980.0f, 560.0f, 80.0f));
        const FVector WheelLocations[] = {
            FVector(-700.0f, -330.0f, 65.0f),
            FVector(200.0f, -330.0f, 65.0f),
            FVector(-700.0f, 330.0f, 65.0f),
            FVector(200.0f, 330.0f, 65.0f)};
        for (int32 Index = 0; Index < UE_ARRAY_COUNT(WheelLocations); ++Index)
        {
            B.Add(FString::Printf(TEXT("AGV_WHEEL_%02d"), Index + 1),
                ELBOneFactoryPressPresentationBatch::GraphiteCylinder,
                WheelLocations[Index], FVector(170.0f, 170.0f, 90.0f),
                FRotator(0.0f, 0.0f, 90.0f));
        }
        B.Add(TEXT("DELIVERY_COIL"),
            ELBOneFactoryPressPresentationBatch::GraphiteCylinder,
            FVector(-250.0f, 0.0f, 390.0f),
            FVector(480.0f, 480.0f, 580.0f),
            FRotator(0.0f, 0.0f, 90.0f));
        B.Add(TEXT("COIL_CRADLE_LEFT"),
            ELBOneFactoryPressPresentationBatch::SafetyCube,
            FVector(-250.0f, -270.0f, 270.0f),
            FVector(720.0f, 90.0f, 120.0f));
        B.Add(TEXT("COIL_CRADLE_RIGHT"),
            ELBOneFactoryPressPresentationBatch::SafetyCube,
            FVector(-250.0f, 270.0f, 270.0f),
            FVector(720.0f, 90.0f, 120.0f));
        B.Add(TEXT("UNLOAD_ARCH_LEFT"),
            ELBOneFactoryPressPresentationBatch::TealStructureCube,
            FVector(850.0f, -650.0f, 325.0f),
            FVector(140.0f, 140.0f, 650.0f));
        B.Add(TEXT("UNLOAD_ARCH_RIGHT"),
            ELBOneFactoryPressPresentationBatch::TealStructureCube,
            FVector(850.0f, 650.0f, 325.0f),
            FVector(140.0f, 140.0f, 650.0f));
        B.Add(TEXT("UNLOAD_ARCH_BEAM"),
            ELBOneFactoryPressPresentationBatch::TealStructureCube,
            FVector(850.0f, 0.0f, 650.0f),
            FVector(160.0f, 1440.0f, 150.0f));
        B.AddFootprintAndStatus();
    }

    void BuildCoilStore(TArray<FLBOneFactoryPressPresentationItem>& Items,
        const FLBOneFactoryPressStarterStationState& Station)
    {
        FStationBuilder B{Items, Station};
        int32 CoilIndex = 0;
        for (int32 Row = 0; Row < 2; ++Row)
        {
            for (int32 Column = 0; Column < 3; ++Column)
            {
                ++CoilIndex;
                const FVector Centre(-950.0f + Column * 950.0f,
                    -520.0f + Row * 1040.0f, 350.0f);
                B.Add(FString::Printf(TEXT("COIL_%02d"), CoilIndex),
                    ELBOneFactoryPressPresentationBatch::GraphiteCylinder,
                    Centre, FVector(520.0f, 520.0f, 650.0f),
                    FRotator(0.0f, 0.0f, 90.0f));
                B.Add(FString::Printf(TEXT("CRADLE_%02d_LEFT"), CoilIndex),
                    ELBOneFactoryPressPresentationBatch::SafetyCube,
                    Centre + FVector(0.0f, -310.0f, -220.0f),
                    FVector(720.0f, 80.0f, 100.0f));
                B.Add(FString::Printf(TEXT("CRADLE_%02d_RIGHT"), CoilIndex),
                    ELBOneFactoryPressPresentationBatch::SafetyCube,
                    Centre + FVector(0.0f, 310.0f, -220.0f),
                    FVector(720.0f, 80.0f, 100.0f));
                B.Add(FString::Printf(TEXT("STORE_PAD_%02d"), CoilIndex),
                    ELBOneFactoryPressPresentationBatch::TealStructureCube,
                    Centre + FVector(0.0f, 0.0f, -300.0f),
                    FVector(760.0f, 780.0f, 70.0f));
            }
        }
        const FVector PostLocations[] = {
            FVector(-1650.0f, -1050.0f, 300.0f),
            FVector(1650.0f, -1050.0f, 300.0f),
            FVector(-1650.0f, 1050.0f, 300.0f),
            FVector(1650.0f, 1050.0f, 300.0f)};
        for (int32 Index = 0; Index < UE_ARRAY_COUNT(PostLocations); ++Index)
        {
            B.Add(FString::Printf(TEXT("STORE_POST_%02d"), Index + 1),
                ELBOneFactoryPressPresentationBatch::TealStructureCube,
                PostLocations[Index], FVector(100.0f, 100.0f, 600.0f));
        }
        B.Add(TEXT("STORE_BEAM_SOUTH"),
            ELBOneFactoryPressPresentationBatch::TealStructureCube,
            FVector(0.0f, -1050.0f, 600.0f),
            FVector(3400.0f, 100.0f, 100.0f));
        B.Add(TEXT("STORE_BEAM_NORTH"),
            ELBOneFactoryPressPresentationBatch::TealStructureCube,
            FVector(0.0f, 1050.0f, 600.0f),
            FVector(3400.0f, 100.0f, 100.0f));
        B.AddFootprintAndStatus();
    }

    void BuildBlankPreparation(
        TArray<FLBOneFactoryPressPresentationItem>& Items,
        const FLBOneFactoryPressStarterStationState& Station)
    {
        FStationBuilder B{Items, Station};
        B.Add(TEXT("PREP_FOUNDATION"),
            ELBOneFactoryPressPresentationBatch::TealStructureCube,
            FVector(0.0f, 0.0f, 35.0f),
            FVector(4200.0f, 1600.0f, 70.0f));
        B.Add(TEXT("DECOILER_COIL"),
            ELBOneFactoryPressPresentationBatch::GraphiteCylinder,
            FVector(-1850.0f, 0.0f, 390.0f),
            FVector(620.0f, 620.0f, 720.0f),
            FRotator(0.0f, 0.0f, 90.0f));
        B.Add(TEXT("DECOILER_HUB"),
            ELBOneFactoryPressPresentationBatch::SteelCylinder,
            FVector(-1850.0f, 0.0f, 390.0f),
            FVector(210.0f, 210.0f, 900.0f),
            FRotator(0.0f, 0.0f, 90.0f));
        for (int32 Index = 0; Index < 4; ++Index)
        {
            B.Add(FString::Printf(TEXT("FEED_ROLLER_%02d"), Index + 1),
                ELBOneFactoryPressPresentationBatch::SteelCylinder,
                FVector(-1050.0f + Index * 520.0f, 0.0f, 245.0f),
                FVector(150.0f, 150.0f, 1050.0f),
                FRotator(0.0f, 0.0f, 90.0f));
        }
        for (int32 Index = 0; Index < 3; ++Index)
        {
            B.Add(FString::Printf(TEXT("FEED_BED_%02d"), Index + 1),
                ELBOneFactoryPressPresentationBatch::GraphiteCube,
                FVector(-1100.0f + Index * 900.0f, 0.0f, 140.0f),
                FVector(780.0f, 1250.0f, 120.0f));
        }
        const FVector FramePosts[] = {
            FVector(-500.0f, -700.0f, 390.0f),
            FVector(-500.0f, 700.0f, 390.0f),
            FVector(1350.0f, -700.0f, 390.0f),
            FVector(1350.0f, 700.0f, 390.0f)};
        for (int32 Index = 0; Index < UE_ARRAY_COUNT(FramePosts); ++Index)
        {
            B.Add(FString::Printf(TEXT("PREP_FRAME_POST_%02d"), Index + 1),
                ELBOneFactoryPressPresentationBatch::TealStructureCube,
                FramePosts[Index], FVector(120.0f, 120.0f, 720.0f));
        }
        B.Add(TEXT("PREP_FRAME_BEAM_SOUTH"),
            ELBOneFactoryPressPresentationBatch::TealStructureCube,
            FVector(425.0f, -700.0f, 750.0f),
            FVector(1970.0f, 120.0f, 120.0f));
        B.Add(TEXT("PREP_FRAME_BEAM_NORTH"),
            ELBOneFactoryPressPresentationBatch::TealStructureCube,
            FVector(425.0f, 700.0f, 750.0f),
            FVector(1970.0f, 120.0f, 120.0f));
        B.Add(TEXT("CUTTER_CROWN"),
            ELBOneFactoryPressPresentationBatch::TealStructureCube,
            FVector(1350.0f, 0.0f, 700.0f),
            FVector(500.0f, 1500.0f, 180.0f));
        B.Add(TEXT("CUTTER_SLIDE"),
            ELBOneFactoryPressPresentationBatch::SteelCube,
            FVector(1350.0f, 0.0f, 465.0f),
            FVector(280.0f, 1250.0f, 130.0f));
        B.Add(TEXT("PREP_CONSOLE"),
            ELBOneFactoryPressPresentationBatch::GraphiteCube,
            FVector(1950.0f, -720.0f, 180.0f),
            FVector(380.0f, 420.0f, 360.0f));
        B.Add(TEXT("PREP_SCREEN"),
            ELBOneFactoryPressPresentationBatch::StatusCube,
            FVector(1950.0f, -935.0f, 300.0f),
            FVector(240.0f, 25.0f, 120.0f));
        for (int32 Index = 0; Index < 4; ++Index)
        {
            B.Add(FString::Printf(TEXT("EXIT_BLANK_%02d"), Index + 1),
                ELBOneFactoryPressPresentationBatch::SteelCube,
                FVector(1850.0f, 100.0f, 185.0f + Index * 20.0f),
                FVector(650.0f, 1050.0f, 12.0f));
        }
        B.AddFootprintAndStatus();
    }

    void BuildPreparedBlankAndDieBuffer(
        TArray<FLBOneFactoryPressPresentationItem>& Items,
        const FLBOneFactoryPressStarterStationState& Station)
    {
        FStationBuilder B{Items, Station};
        const float StackX[] = {-760.0f, 0.0f, 760.0f};
        for (int32 Stack = 0; Stack < UE_ARRAY_COUNT(StackX); ++Stack)
        {
            B.Add(FString::Printf(TEXT("BLANK_PALLET_%02d"), Stack + 1),
                ELBOneFactoryPressPresentationBatch::GraphiteCube,
                FVector(StackX[Stack], -430.0f, 55.0f),
                FVector(620.0f, 850.0f, 110.0f));
            for (int32 Sheet = 0; Sheet < 4; ++Sheet)
            {
                B.Add(FString::Printf(TEXT("BLANK_%02d_%02d"),
                        Stack + 1, Sheet + 1),
                    ELBOneFactoryPressPresentationBatch::SteelCube,
                    FVector(StackX[Stack], -430.0f,
                        120.0f + Sheet * 18.0f),
                    FVector(570.0f, 790.0f, 10.0f));
            }
        }
        const FVector RackPosts[] = {
            FVector(-1120.0f, 860.0f, 330.0f),
            FVector(1120.0f, 860.0f, 330.0f),
            FVector(-1120.0f, 180.0f, 330.0f),
            FVector(1120.0f, 180.0f, 330.0f)};
        for (int32 Index = 0; Index < UE_ARRAY_COUNT(RackPosts); ++Index)
        {
            B.Add(FString::Printf(TEXT("DIE_RACK_POST_%02d"), Index + 1),
                ELBOneFactoryPressPresentationBatch::TealStructureCube,
                RackPosts[Index], FVector(100.0f, 100.0f, 660.0f));
        }
        B.Add(TEXT("DIE_RACK_BEAM_FRONT"),
            ELBOneFactoryPressPresentationBatch::TealStructureCube,
            FVector(0.0f, 180.0f, 650.0f),
            FVector(2340.0f, 100.0f, 100.0f));
        B.Add(TEXT("DIE_RACK_BEAM_REAR"),
            ELBOneFactoryPressPresentationBatch::TealStructureCube,
            FVector(0.0f, 860.0f, 650.0f),
            FVector(2340.0f, 100.0f, 100.0f));
        for (int32 Die = 0; Die < 3; ++Die)
        {
            const float X = -720.0f + Die * 720.0f;
            B.Add(FString::Printf(TEXT("DIE_PALLET_%02d"), Die + 1),
                ELBOneFactoryPressPresentationBatch::SafetyCube,
                FVector(X, 520.0f, 85.0f),
                FVector(590.0f, 520.0f, 90.0f));
            B.Add(FString::Printf(TEXT("DIE_TOOL_%02d"), Die + 1),
                ELBOneFactoryPressPresentationBatch::GraphiteCube,
                FVector(X, 520.0f, 210.0f),
                FVector(480.0f, 400.0f, 170.0f));
        }
        B.AddFootprintAndStatus();
    }

    void BuildPressTrain(TArray<FLBOneFactoryPressPresentationItem>& Items,
        const FLBOneFactoryPressStarterStationState& Station)
    {
        FStationBuilder B{Items, Station};
        for (int32 Stage = 0; Stage < 7; ++Stage)
        {
            const float Y = -3000.0f + Stage * 1000.0f;
            const float ColumnHeight = 400.0f + Stage * 45.0f;
            const FString Prefix = FString::Printf(TEXT("PRESS_STAGE_%02d"),
                Stage + 1);
            B.Add(Prefix + TEXT("_BASE"),
                ELBOneFactoryPressPresentationBatch::GraphiteCube,
                FVector(0.0f, Y, 60.0f),
                FVector(1800.0f, 720.0f, 120.0f));
            B.Add(Prefix + TEXT("_COLUMN_LEFT"),
                ELBOneFactoryPressPresentationBatch::TealStructureCube,
                FVector(-700.0f, Y, 100.0f + ColumnHeight * 0.5f),
                FVector(210.0f, 560.0f, ColumnHeight));
            B.Add(Prefix + TEXT("_COLUMN_RIGHT"),
                ELBOneFactoryPressPresentationBatch::TealStructureCube,
                FVector(700.0f, Y, 100.0f + ColumnHeight * 0.5f),
                FVector(210.0f, 560.0f, ColumnHeight));
            B.Add(Prefix + TEXT("_CROWN"),
                ELBOneFactoryPressPresentationBatch::TealStructureCube,
                FVector(0.0f, Y, 180.0f + ColumnHeight),
                FVector(1700.0f, 620.0f, 160.0f));
            B.Add(Prefix + TEXT("_SLIDE"),
                ELBOneFactoryPressPresentationBatch::SteelCube,
                FVector(0.0f, Y, ColumnHeight),
                FVector(1100.0f, 500.0f, 120.0f));
            B.Add(Prefix + TEXT("_BOLSTER"),
                ELBOneFactoryPressPresentationBatch::GraphiteCube,
                FVector(0.0f, Y, 155.0f),
                FVector(1200.0f, 520.0f, 90.0f));
            B.Add(Prefix + TEXT("_GUARD_LEFT"),
                ELBOneFactoryPressPresentationBatch::SafetyCube,
                FVector(-1030.0f, Y, 175.0f),
                FVector(90.0f, 680.0f, 350.0f));
            B.Add(Prefix + TEXT("_GUARD_RIGHT"),
                ELBOneFactoryPressPresentationBatch::SafetyCube,
                FVector(1030.0f, Y, 175.0f),
                FVector(90.0f, 680.0f, 350.0f));
            B.Add(Prefix + TEXT("_STATUS"),
                ELBOneFactoryPressPresentationBatch::StatusCube,
                FVector(1030.0f, Y, 395.0f),
                FVector(75.0f, 75.0f, 75.0f));
        }
        for (int32 Transfer = 0; Transfer < 8; ++Transfer)
        {
            B.Add(FString::Printf(TEXT("PRESS_TRANSFER_%02d"), Transfer + 1),
                ELBOneFactoryPressPresentationBatch::SteelCube,
                FVector(0.0f, -3500.0f + Transfer * 1000.0f, 105.0f),
                FVector(1120.0f, 250.0f, 90.0f));
        }
        const FVector SilhouetteColumns[] = {
            FVector(-1000.0f, -3500.0f, 450.0f),
            FVector(1000.0f, -3500.0f, 450.0f),
            FVector(-1000.0f, 3500.0f, 450.0f),
            FVector(1000.0f, 3500.0f, 450.0f)};
        for (int32 Index = 0; Index < UE_ARRAY_COUNT(SilhouetteColumns); ++Index)
        {
            B.Add(FString::Printf(TEXT("HIGH_GANTRY_COLUMN_%02d"), Index + 1),
                ELBOneFactoryPressPresentationBatch::TealStructureCube,
                SilhouetteColumns[Index], FVector(120.0f, 120.0f, 900.0f));
        }
        B.Add(TEXT("HIGH_GANTRY_RAIL_LEFT"),
            ELBOneFactoryPressPresentationBatch::TealStructureCube,
            FVector(-1000.0f, 0.0f, 850.0f),
            FVector(120.0f, 7500.0f, 120.0f));
        B.Add(TEXT("HIGH_GANTRY_RAIL_RIGHT"),
            ELBOneFactoryPressPresentationBatch::TealStructureCube,
            FVector(1000.0f, 0.0f, 850.0f),
            FVector(120.0f, 7500.0f, 120.0f));
        const float BridgeY[] = {-2500.0f, 0.0f, 2500.0f};
        for (int32 Index = 0; Index < UE_ARRAY_COUNT(BridgeY); ++Index)
        {
            B.Add(FString::Printf(TEXT("HIGH_CRANE_BRIDGE_%02d"), Index + 1),
                ELBOneFactoryPressPresentationBatch::SafetyCube,
                FVector(0.0f, BridgeY[Index], 830.0f),
                FVector(2200.0f, 120.0f, 120.0f));
        }
        B.Add(TEXT("HIGH_CRANE_HOIST"),
            ELBOneFactoryPressPresentationBatch::GraphiteCube,
            FVector(0.0f, 0.0f, 740.0f),
            FVector(260.0f, 260.0f, 180.0f));
        B.Add(TEXT("HIGH_CRANE_HOOK"),
            ELBOneFactoryPressPresentationBatch::SteelCylinder,
            FVector(0.0f, 0.0f, 610.0f),
            FVector(80.0f, 80.0f, 180.0f));
        B.AddFootprintAndStatus();
    }

    void BuildInspection(TArray<FLBOneFactoryPressPresentationItem>& Items,
        const FLBOneFactoryPressStarterStationState& Station)
    {
        FStationBuilder B{Items, Station};
        B.Add(TEXT("INSPECTION_TABLE"),
            ELBOneFactoryPressPresentationBatch::GraphiteCube,
            FVector(-150.0f, 0.0f, 150.0f),
            FVector(1500.0f, 1100.0f, 300.0f));
        B.Add(TEXT("INSPECTION_SURFACE"),
            ELBOneFactoryPressPresentationBatch::SteelCube,
            FVector(-150.0f, 0.0f, 315.0f),
            FVector(1400.0f, 1000.0f, 30.0f));
        B.Add(TEXT("SCANNER_POST_LEFT"),
            ELBOneFactoryPressPresentationBatch::TealStructureCube,
            FVector(-760.0f, 0.0f, 390.0f),
            FVector(120.0f, 120.0f, 780.0f));
        B.Add(TEXT("SCANNER_POST_RIGHT"),
            ELBOneFactoryPressPresentationBatch::TealStructureCube,
            FVector(460.0f, 0.0f, 390.0f),
            FVector(120.0f, 120.0f, 780.0f));
        B.Add(TEXT("SCANNER_BEAM"),
            ELBOneFactoryPressPresentationBatch::TealStructureCube,
            FVector(-150.0f, 0.0f, 760.0f),
            FVector(1340.0f, 140.0f, 140.0f));
        B.Add(TEXT("SCANNER_HEAD_LEFT"),
            ELBOneFactoryPressPresentationBatch::SteelCylinder,
            FVector(-450.0f, 0.0f, 650.0f),
            FVector(110.0f, 110.0f, 180.0f));
        B.Add(TEXT("SCANNER_HEAD_RIGHT"),
            ELBOneFactoryPressPresentationBatch::SteelCylinder,
            FVector(150.0f, 0.0f, 650.0f),
            FVector(110.0f, 110.0f, 180.0f));
        B.Add(TEXT("DISPLAY_PANEL"),
            ELBOneFactoryPressPresentationBatch::SteelCube,
            FVector(-150.0f, 0.0f, 345.0f),
            FVector(900.0f, 650.0f, 16.0f));
        B.Add(TEXT("LIGHT_BAR_LEFT"),
            ELBOneFactoryPressPresentationBatch::StatusCube,
            FVector(-760.0f, -180.0f, 700.0f),
            FVector(50.0f, 280.0f, 50.0f));
        B.Add(TEXT("LIGHT_BAR_RIGHT"),
            ELBOneFactoryPressPresentationBatch::StatusCube,
            FVector(460.0f, -180.0f, 700.0f),
            FVector(50.0f, 280.0f, 50.0f));
        B.Add(TEXT("INSPECTION_CONSOLE"),
            ELBOneFactoryPressPresentationBatch::GraphiteCube,
            FVector(800.0f, -650.0f, 180.0f),
            FVector(360.0f, 320.0f, 360.0f));
        B.Add(TEXT("INSPECTION_SCREEN"),
            ELBOneFactoryPressPresentationBatch::StatusCube,
            FVector(800.0f, -825.0f, 300.0f),
            FVector(230.0f, 30.0f, 120.0f));
        B.AddFootprintAndStatus();
    }

    void BuildDispatch(TArray<FLBOneFactoryPressPresentationItem>& Items,
        const FLBOneFactoryPressStarterStationState& Station)
    {
        FStationBuilder B{Items, Station};
        for (int32 Stillage = 0; Stillage < 3; ++Stillage)
        {
            const float X = -780.0f + Stillage * 780.0f;
            const FString Prefix = FString::Printf(TEXT("EMPTY_STILLAGE_%02d"),
                Stillage + 1);
            B.Add(Prefix + TEXT("_BASE"),
                ELBOneFactoryPressPresentationBatch::GraphiteCube,
                FVector(X, 360.0f, 65.0f),
                FVector(620.0f, 850.0f, 130.0f));
            const FVector PostOffsets[] = {
                FVector(-270.0f, -380.0f, 300.0f),
                FVector(270.0f, -380.0f, 300.0f),
                FVector(-270.0f, 380.0f, 300.0f),
                FVector(270.0f, 380.0f, 300.0f)};
            for (int32 Post = 0; Post < UE_ARRAY_COUNT(PostOffsets); ++Post)
            {
                B.Add(Prefix + FString::Printf(TEXT("_POST_%02d"), Post + 1),
                    ELBOneFactoryPressPresentationBatch::TealStructureCube,
                    FVector(X, 360.0f, 0.0f) + PostOffsets[Post],
                    FVector(70.0f, 70.0f, 600.0f));
            }
            B.Add(Prefix + TEXT("_RAIL_FRONT"),
                ELBOneFactoryPressPresentationBatch::TealStructureCube,
                FVector(X, -20.0f, 570.0f),
                FVector(620.0f, 70.0f, 70.0f));
            B.Add(Prefix + TEXT("_RAIL_REAR"),
                ELBOneFactoryPressPresentationBatch::TealStructureCube,
                FVector(X, 740.0f, 570.0f),
                FVector(620.0f, 70.0f, 70.0f));
            B.Add(Prefix + TEXT("_EMPTY_BOARD"),
                ELBOneFactoryPressPresentationBatch::SafetyCube,
                FVector(X, -35.0f, 410.0f),
                FVector(300.0f, 30.0f, 130.0f));
        }
        B.Add(TEXT("DISPATCH_AGV_DECK"),
            ELBOneFactoryPressPresentationBatch::GraphiteCube,
            FVector(0.0f, -650.0f, 90.0f),
            FVector(1250.0f, 560.0f, 150.0f));
        B.Add(TEXT("DISPATCH_AGV_TOP"),
            ELBOneFactoryPressPresentationBatch::TealStructureCube,
            FVector(0.0f, -650.0f, 185.0f),
            FVector(900.0f, 430.0f, 70.0f));
        const float WheelX[] = {-450.0f, 450.0f};
        const float WheelY[] = {-880.0f, -420.0f};
        int32 Wheel = 0;
        for (const float X : WheelX)
        {
            for (const float Y : WheelY)
            {
                ++Wheel;
                B.Add(FString::Printf(TEXT("DISPATCH_AGV_WHEEL_%02d"), Wheel),
                    ELBOneFactoryPressPresentationBatch::GraphiteCylinder,
                    FVector(X, Y, 65.0f), FVector(150.0f, 150.0f, 80.0f),
                    FRotator(0.0f, 0.0f, 90.0f));
            }
        }
        B.Add(TEXT("DISPATCH_SIGN_LEFT"),
            ELBOneFactoryPressPresentationBatch::TealStructureCube,
            FVector(-850.0f, -900.0f, 360.0f),
            FVector(100.0f, 100.0f, 720.0f));
        B.Add(TEXT("DISPATCH_SIGN_RIGHT"),
            ELBOneFactoryPressPresentationBatch::TealStructureCube,
            FVector(850.0f, -900.0f, 360.0f),
            FVector(100.0f, 100.0f, 720.0f));
        B.Add(TEXT("DISPATCH_SIGN_TOP"),
            ELBOneFactoryPressPresentationBatch::SafetyCube,
            FVector(0.0f, -900.0f, 700.0f),
            FVector(1800.0f, 120.0f, 120.0f));
        B.AddFootprintAndStatus();
    }

    void AddMaterialRoutes(TArray<FLBOneFactoryPressPresentationItem>& Items,
        const FLBOneFactoryPressStarterLayoutState& Layout)
    {
        for (const FLBOneFactoryPressStarterConnectionState& Connection :
            Layout.Connections)
        {
            const FLBOneFactoryPressStarterStationState* Source =
                FindStation(Layout, Connection.SourceStationId);
            const FLBOneFactoryPressStarterStationState* Target =
                FindStation(Layout, Connection.TargetStationId);
            if (!Source || !Target) continue;
            const FVector Start = Source->WorldTransform.GetLocation();
            const FVector End = Target->WorldTransform.GetLocation();
            const FVector Delta = End - Start;
            const float Length = Delta.Size2D();
            if (Length <= KINDA_SMALL_NUMBER) continue;
            FLBOneFactoryPressPresentationItem& Item =
                Items.AddDefaulted_GetRef();
            Item.PresentationId = FName(*FString::Printf(TEXT("OF_PRESS_VIS_%s"),
                *Connection.ConnectionId.ToString()));
            Item.StationId = Target->StationId;
            Item.Role = Target->Role;
            Item.Batch = ELBOneFactoryPressPresentationBatch::FloorRouteCube;
            const float Yaw = FMath::RadiansToDegrees(
                FMath::Atan2(Delta.Y, Delta.X));
            Item.WorldTransform = FTransform(FRotator(0.0f, Yaw, 0.0f),
                (Start + End) * 0.5f + FVector(0.0f, 0.0f, 3.0f),
                FVector(Length / 100.0f, 0.22f, 0.06f));
            Item.bRepresentsProcessWIP = false;
        }
    }
}

ALBOneFactoryPressStarterPresentationActor::
    ALBOneFactoryPressStarterPresentationActor()
{
    PrimaryActorTick.bCanEverTick = false;
    SetReplicates(false);
    SetActorEnableCollision(false);

    SceneRoot = CreateDefaultSubobject<USceneComponent>(TEXT("SceneRoot"));
    SceneRoot->SetMobility(EComponentMobility::Movable);
    SetRootComponent(SceneRoot);

    DetailedPresentationA = CreateDefaultSubobject<UStaticMeshComponent>(
        TEXT("DetailedPresentationA"));
    DetailedPresentationB = CreateDefaultSubobject<UStaticMeshComponent>(
        TEXT("DetailedPresentationB"));
    for (UStaticMeshComponent* Component : GetDetailedPresentationComponents())
    {
        if (!Component) continue;
        Component->SetupAttachment(SceneRoot);
        ConfigureDetailedPresentationComponent(Component);
    }

    static ConstructorHelpers::FObjectFinder<UStaticMesh> DetailedMeshFinder(
        LBOneFactoryPressPresentationPrivate::DetailedMeshPath);
    DetailedPresentationMesh = DetailedMeshFinder.Succeeded()
        ? DetailedMeshFinder.Object : nullptr;

    Tags.AddUnique(GetPresentationTag());
    // Retained verbatim because the existing exact-pair validator consumes it.
    Tags.AddUnique(TEXT("LB.OneFactory.PressStarter.NativeProcedural"));
    Tags.AddUnique(TEXT("LB.Provenance.VerifiedPreMeshyNative"));
    Tags.AddUnique(TEXT("LB.Environment.VisualOnly"));
    Tags.AddUnique(TEXT("LB.NotProcessWIP"));
    SetActorHiddenInGame(true);
}

TArray<UStaticMeshComponent*>
ALBOneFactoryPressStarterPresentationActor::
    GetDetailedPresentationComponents() const
{
    return { DetailedPresentationA.Get(), DetailedPresentationB.Get() };
}

UStaticMeshComponent* ALBOneFactoryPressStarterPresentationActor::
    GetDetailedPresentationComponent(const int32 Index) const
{
    switch (Index)
    {
    case 0: return DetailedPresentationA.Get();
    case 1: return DetailedPresentationB.Get();
    default: return nullptr;
    }
}

void ALBOneFactoryPressStarterPresentationActor::
    ConfigureDetailedPresentationComponent(UStaticMeshComponent* Component)
{
    if (!Component) return;
    Component->SetMobility(EComponentMobility::Movable);
    Component->SetCollisionEnabled(ECollisionEnabled::NoCollision);
    Component->SetCollisionResponseToAllChannels(ECR_Ignore);
    Component->SetGenerateOverlapEvents(false);
    Component->SetCanEverAffectNavigation(false);
    Component->SetCastShadow(true);
    Component->SetReceivesDecals(false);
    Component->SetVisibility(false, true);
    Component->SetHiddenInGame(true, true);
}

bool ALBOneFactoryPressStarterPresentationActor::ValidateDetailedMeshAsset(
    const UStaticMesh* Mesh, FString& OutReason)
{
    using namespace LBOneFactoryPressPresentationPrivate;
    if (!Mesh || !Mesh->GetPathName().Equals(DetailedMeshPath,
            ESearchCase::CaseSensitive))
    {
        OutReason = TEXT(
            "PRESS DETAILED PRESENTATION MESH DID NOT RESOLVE TO ITS EXACT OWNED PATH");
        return false;
    }
    if (Mesh->GetStaticMaterials().Num() != ExpectedMaterialSlotCount)
    {
        OutReason = TEXT(
            "PRESS DETAILED PRESENTATION REQUIRES EXACTLY 306 MATERIAL SLOTS");
        return false;
    }

    TSet<FString> ExpectedMaterials;
    for (const TCHAR* MaterialPath : DetailedMaterialPaths)
        ExpectedMaterials.Add(MaterialPath);
    TSet<FString> ObservedMaterials;
    for (int32 SlotIndex = 0; SlotIndex < ExpectedMaterialSlotCount;
        ++SlotIndex)
    {
        const UMaterialInterface* Material = Mesh->GetMaterial(SlotIndex);
        const FString MaterialPath = Material ? Material->GetPathName() : FString();
        if (!Material || !ExpectedMaterials.Contains(MaterialPath))
        {
            OutReason = FString::Printf(TEXT(
                "PRESS DETAILED PRESENTATION MATERIAL SLOT %d IS NULL OR OUTSIDE THE EXACT 13-ASSET OWNED SET"),
                SlotIndex);
            return false;
        }
        ObservedMaterials.Add(MaterialPath);
    }
    if (ObservedMaterials.Num() != UE_ARRAY_COUNT(DetailedMaterialPaths))
    {
        OutReason = TEXT(
            "PRESS DETAILED PRESENTATION DOES NOT USE ALL 13 ACCEPTED PBR MATERIALS");
        return false;
    }
    OutReason = TEXT(
        "PRESS DETAILED PRESENTATION MESH HAS EXACTLY 306 OWNED PBR MATERIAL BINDINGS");
    return true;
}

bool ALBOneFactoryPressStarterPresentationActor::
    BuildDetailedAggregateWorldTransform(
        const FLBOneFactoryPressStarterLayoutState& Layout,
        FTransform& OutWorldTransform, FString& OutReason)
{
    using namespace LBOneFactoryPressPresentationPrivate;
    const FLBOneFactoryPressStarterStationState* PressStation = FindStation(
        Layout, ELBOneFactoryPressStarterRole::ConfigurablePressTrain);
    if (!PressStation || !IsFiniteTransform(PressStation->WorldTransform))
    {
        OutReason = TEXT(
            "PRESS DETAILED PRESENTATION HAS NO VALID CONFIGURABLE-PRESS-TRAIN ANCHOR");
        return false;
    }
    const FTransform LocalTransform(FQuat::Identity,
        DetailedAggregateLocalLocationCm, DetailedAggregateLocalScale);
    OutWorldTransform = LocalTransform * PressStation->WorldTransform;
    if (!IsFiniteTransform(OutWorldTransform))
    {
        OutReason = TEXT(
            "PRESS DETAILED PRESENTATION AGGREGATE WORLD TRANSFORM IS INVALID");
        return false;
    }
    OutReason = TEXT(
        "PRESS DETAILED PRESENTATION IS ANCHORED TO CONFIGURABLE PRESS TRAIN");
    return true;
}

void ALBOneFactoryPressStarterPresentationActor::ClearPresentation()
{
    for (UStaticMeshComponent* Component : GetDetailedPresentationComponents())
    {
        if (!Component) continue;
        Component->SetVisibility(false, true);
        Component->SetHiddenInGame(true, true);
        Component->SetStaticMesh(nullptr);
    }
    ConfiguredItems.Reset();
    ConfiguredStationTransforms.Reset();
    ConfiguredLayoutId = NAME_None;
    ConfiguredLayoutRevision = INDEX_NONE;
    bPresentationConfigured = false;
    ActiveDetailedPresentationIndex = INDEX_NONE;
    SetActorHiddenInGame(true);
}

bool ALBOneFactoryPressStarterPresentationActor::ConfigureFromLayout(
    const FLBOneFactoryPressStarterLayoutState& Layout, FString& OutReason)
{
    if (!ValidateNativePresentationReferences(GetPresentationClassPath(),
            GetRequiredNativeAssetPaths(), OutReason))
    {
        OutReason = FString::Printf(TEXT("PRESS PRESENTATION PROVENANCE FAILED: %s"),
            *OutReason);
        return false;
    }
    TArray<FLBOneFactoryPressPresentationItem> CandidateItems =
        BuildExpectedPresentationItems(Layout);
    if (!ValidatePresentationContract(Layout, CandidateItems, OutReason))
    {
        OutReason = FString::Printf(TEXT("PRESS PRESENTATION CONTRACT FAILED: %s"),
            *OutReason);
        return false;
    }

    UStaticMesh* ResolvedDetailedMesh = DetailedPresentationMesh.Get();
    if (!ValidateDetailedMeshAsset(ResolvedDetailedMesh, OutReason))
    {
        OutReason = FString::Printf(TEXT("PRESS PRESENTATION ASSET FAILED: %s"),
            *OutReason);
        return false;
    }

    FTransform CandidateAggregateWorldTransform;
    if (!BuildDetailedAggregateWorldTransform(Layout,
            CandidateAggregateWorldTransform, OutReason))
    {
        OutReason = FString::Printf(TEXT("PRESS PRESENTATION ANCHOR FAILED: %s"),
            *OutReason);
        return false;
    }

    TMap<FName, FTransform> CandidateStationTransforms;
    CandidateStationTransforms.Reserve(Layout.Stations.Num());
    for (const FLBOneFactoryPressStarterStationState& Station : Layout.Stations)
        CandidateStationTransforms.Add(Station.StationId, Station.WorldTransform);

    const TArray<UStaticMeshComponent*> Components =
        GetDetailedPresentationComponents();
    if (Components.Num() != 2 || Components.Contains(nullptr))
    {
        OutReason = TEXT(
            "PRESS PRESENTATION REQUIRES EXACTLY TWO PRIVATE STAGING COMPONENTS");
        return false;
    }

    const int32 StagingIndex = ActiveDetailedPresentationIndex == 0 ? 1 : 0;
    UStaticMeshComponent* Staging = GetDetailedPresentationComponent(StagingIndex);
    if (!Staging
        || (bPresentationConfigured
            && StagingIndex == ActiveDetailedPresentationIndex))
    {
        OutReason = TEXT(
            "PRESS PRESENTATION COULD NOT ACQUIRE AN INACTIVE STAGING COMPONENT");
        return false;
    }

    // Stage completely while hidden. Every failure below clears staging only and
    // leaves the former committed component and snapshot untouched.
    Staging->SetVisibility(false, true);
    Staging->SetHiddenInGame(true, true);
    Staging->SetStaticMesh(nullptr);
    Staging->SetWorldTransform(CandidateAggregateWorldTransform, false, nullptr,
        ETeleportType::TeleportPhysics);
    const bool bMeshAssigned = Staging->SetStaticMesh(ResolvedDetailedMesh);
    if (!bMeshAssigned || Staging->GetStaticMesh() != ResolvedDetailedMesh
        || !Staging->GetComponentTransform().Equals(
            CandidateAggregateWorldTransform,
            LBOneFactoryPressPresentationPrivate::TransformTolerance))
    {
        Staging->SetStaticMesh(nullptr);
        OutReason = TEXT(
            "PRESS PRESENTATION STAGING COMPONENT FAILED EXACT MESH/TRANSFORM VALIDATION");
        return false;
    }

    UStaticMeshComponent* Former = GetDetailedPresentationComponent(
        ActiveDetailedPresentationIndex);
    if (Former)
    {
        Former->SetVisibility(false, true);
        Former->SetHiddenInGame(true, true);
        Former->SetStaticMesh(nullptr);
    }

    ConfiguredStationTransforms = MoveTemp(CandidateStationTransforms);
    ConfiguredItems = MoveTemp(CandidateItems);
    ConfiguredLayoutId = Layout.LayoutId;
    ConfiguredLayoutRevision = Layout.Revision;
    ActiveDetailedPresentationIndex = StagingIndex;
    bPresentationConfigured = true;
    SetActorHiddenInGame(false);
    Staging->SetVisibility(true, true);
    Staging->SetHiddenInGame(false, true);
    OutReason = TEXT(
        "NATIVE DETAILED PRESS PRESENTATION ACTIVE: 1 V449 AGGREGATE, 306 OWNED PBR SLOTS, 268 LOGICAL ITEMS, WIP 0");
    return true;
}

int32 ALBOneFactoryPressStarterPresentationActor::GetVisibleInstanceCount() const
{
    const UStaticMeshComponent* Active = GetDetailedPresentationComponent(
        ActiveDetailedPresentationIndex);
    return bPresentationConfigured && Active && Active->GetStaticMesh()
        && Active->IsVisible() && !Active->bHiddenInGame ? 1 : 0;
}

int32 ALBOneFactoryPressStarterPresentationActor::GetVisualBatchCount() const
{
    return GetVisibleInstanceCount() > 0 ? 1 : 0;
}

int32 ALBOneFactoryPressStarterPresentationActor::GetInstanceCountForRole(
    const ELBOneFactoryPressStarterRole InRole) const
{
    int32 Count = 0;
    for (const FLBOneFactoryPressPresentationItem& Item : ConfiguredItems)
    {
        if (Item.Role == InRole) ++Count;
    }
    return Count;
}

int32 ALBOneFactoryPressStarterPresentationActor::GetInstanceCountForBatch(
    const ELBOneFactoryPressPresentationBatch Batch) const
{
    int32 Count = 0;
    for (const FLBOneFactoryPressPresentationItem& Item : ConfiguredItems)
    {
        if (Item.Batch == Batch) ++Count;
    }
    return Count;
}

bool ALBOneFactoryPressStarterPresentationActor::GetConfiguredStationTransform(
    const FName StationId, FTransform& OutWorldTransform) const
{
    const FTransform* Found = ConfiguredStationTransforms.Find(StationId);
    if (!bPresentationConfigured || !Found) return false;
    OutWorldTransform = *Found;
    return true;
}

TArray<FLBOneFactoryPressPresentationItem>
ALBOneFactoryPressStarterPresentationActor::GetConfiguredItemsForRole(
    const ELBOneFactoryPressStarterRole InRole) const
{
    TArray<FLBOneFactoryPressPresentationItem> Result;
    for (const FLBOneFactoryPressPresentationItem& Item : ConfiguredItems)
    {
        if (Item.Role == InRole) Result.Add(Item);
    }
    return Result;
}

int32 ALBOneFactoryPressStarterPresentationActor::GetExpectedVisualBatchCount()
{
    return LBOneFactoryPressPresentationPrivate::ExpectedVisualBatchCount;
}

int32 ALBOneFactoryPressStarterPresentationActor::GetExpectedVisibleInstanceCount()
{
    return LBOneFactoryPressPresentationPrivate::ExpectedRenderedAggregateCount;
}

int32 ALBOneFactoryPressStarterPresentationActor::GetExpectedInstanceCountForRole(
    const ELBOneFactoryPressStarterRole InRole)
{
    switch (InRole)
    {
    case ELBOneFactoryPressStarterRole::InboundCoilReceiving: return 18;
    case ELBOneFactoryPressStarterRole::WrappedCoilStorage: return 37;
    case ELBOneFactoryPressStarterRole::BlankPreparation: return 31;
    case ELBOneFactoryPressStarterRole::PreparedBlankBuffer: return 34;
    case ELBOneFactoryPressStarterRole::ConfigurablePressTrain: return 89;
    case ELBOneFactoryPressStarterRole::PanelInspection: return 19;
    case ELBOneFactoryPressStarterRole::PanelStillageDispatch: return 40;
    default: return 0;
    }
}

int32 ALBOneFactoryPressStarterPresentationActor::GetExpectedInstanceCountForBatch(
    const ELBOneFactoryPressPresentationBatch Batch)
{
    switch (Batch)
    {
    case ELBOneFactoryPressPresentationBatch::GraphiteCube: return 32;
    case ELBOneFactoryPressPresentationBatch::TealStructureCube: return 88;
    case ELBOneFactoryPressPresentationBatch::SteelCube: return 34;
    case ELBOneFactoryPressPresentationBatch::SafetyCube: return 38;
    case ELBOneFactoryPressPresentationBatch::StatusCube: return 18;
    case ELBOneFactoryPressPresentationBatch::GraphiteCylinder: return 16;
    case ELBOneFactoryPressPresentationBatch::SteelCylinder: return 8;
    case ELBOneFactoryPressPresentationBatch::FloorRouteCube: return 34;
    default: return 0;
    }
}

TArray<FSoftObjectPath>
ALBOneFactoryPressStarterPresentationActor::GetRequiredNativeAssetPaths()
{
    using namespace LBOneFactoryPressPresentationPrivate;
    TArray<FSoftObjectPath> RequiredAssets;
    RequiredAssets.Reserve(1 + UE_ARRAY_COUNT(DetailedMaterialPaths));
    RequiredAssets.Emplace(DetailedMeshPath);
    for (const TCHAR* MaterialPath : DetailedMaterialPaths)
        RequiredAssets.Emplace(MaterialPath);
    return RequiredAssets;
}

bool ALBOneFactoryPressStarterPresentationActor::
    ValidateNativePresentationReferences(
        const FString& PresentationClassPath,
        const TArray<FSoftObjectPath>& AssetPaths, FString& OutReason)
{
    using namespace LBOneFactoryPressPresentationPrivate;
    const FLBOneFactoryPressNativeOnlyProfile Profile =
        ULBOneFactoryPressStarterLayoutLibrary::MakeNativeOnlyProfile();
    if (!ULBOneFactoryPressStarterLayoutLibrary::ValidateNativeOnlyProfile(
            Profile, OutReason))
    {
        return false;
    }
    if (!PresentationClassPath.Equals(ExpectedPresentationClassPath,
            ESearchCase::CaseSensitive))
    {
        OutReason = TEXT("PRESS PRESENTATION CLASS DRIFTED FROM ITS EXACT NATIVE CODE CONTRACT");
        return false;
    }
    for (const FString& Token : Profile.ForbiddenSourceTokens)
    {
        if (PresentationClassPath.Contains(Token, ESearchCase::IgnoreCase))
        {
            OutReason = TEXT("PRESS PRESENTATION CLASS CONTAINS A FORBIDDEN SOURCE TOKEN");
            return false;
        }
    }
    if (!ULBOneFactoryLayoutLibrary::ValidateAssetProvenance(
            Profile.Policy, ELBOneFactoryAssetProvenance::NativeCode,
            PresentationClassPath, OutReason))
    {
        return false;
    }

    const TArray<FSoftObjectPath> Expected = GetRequiredNativeAssetPaths();
    if (AssetPaths.Num() != Expected.Num())
    {
        OutReason = TEXT(
            "PRESS PRESENTATION REQUIRES THE EXACT OWNED MESH PLUS 13 PBR MATERIAL REFERENCES");
        return false;
    }
    for (int32 Index = 0; Index < Expected.Num(); ++Index)
    {
        if (AssetPaths[Index].IsNull() || AssetPaths[Index] != Expected[Index])
        {
            OutReason = TEXT(
                "PRESS PRESENTATION OWNED ASSET REFERENCE LIST DRIFTED");
            return false;
        }
        const FString Reference = AssetPaths[Index].ToString();
        if (!Reference.StartsWith(DetailedPresentationRoot,
                ESearchCase::CaseSensitive))
        {
            OutReason = TEXT(
                "PRESS PRESENTATION REFERENCE IS OUTSIDE ITS OWNED ONEFACTORY NATIVE PRESS ROOT");
            return false;
        }
        for (const FString& Token : Profile.ForbiddenSourceTokens)
        {
            if (Reference.Contains(Token, ESearchCase::IgnoreCase))
            {
                OutReason = TEXT("PRESS PRESENTATION REFERENCE CONTAINS A FORBIDDEN SOURCE TOKEN");
                return false;
            }
        }
        if (!ULBOneFactoryLayoutLibrary::ValidateAssetProvenance(
                Profile.Policy,
                ELBOneFactoryAssetProvenance::VerifiedPreMeshyNative,
                Reference, OutReason))
        {
            return false;
        }
    }
    OutReason = TEXT(
        "PRESS PRESENTATION CLASS AND EXACT 14-ASSET OWNED V449 CLOSURE HAVE VERIFIED PRE-MESHY NATIVE PROVENANCE");
    return true;
}

TArray<FLBOneFactoryPressPresentationItem>
ALBOneFactoryPressStarterPresentationActor::BuildExpectedPresentationItems(
    const FLBOneFactoryPressStarterLayoutState& Layout)
{
    using namespace LBOneFactoryPressPresentationPrivate;
    FString LayoutReason;
    if (!ULBOneFactoryPressStarterLayoutLibrary::ValidateStarterLayout(
            Layout, LayoutReason))
    {
        return {};
    }

    TArray<FLBOneFactoryPressPresentationItem> Items;
    Items.Reserve(ExpectedLogicalItemCount);
    const FLBOneFactoryPressStarterStationState* Inbound = FindStation(Layout,
        ELBOneFactoryPressStarterRole::InboundCoilReceiving);
    const FLBOneFactoryPressStarterStationState* CoilStore = FindStation(Layout,
        ELBOneFactoryPressStarterRole::WrappedCoilStorage);
    const FLBOneFactoryPressStarterStationState* BlankPrep = FindStation(Layout,
        ELBOneFactoryPressStarterRole::BlankPreparation);
    const FLBOneFactoryPressStarterStationState* BlankBuffer = FindStation(Layout,
        ELBOneFactoryPressStarterRole::PreparedBlankBuffer);
    const FLBOneFactoryPressStarterStationState* Press = FindStation(Layout,
        ELBOneFactoryPressStarterRole::ConfigurablePressTrain);
    const FLBOneFactoryPressStarterStationState* Inspection = FindStation(Layout,
        ELBOneFactoryPressStarterRole::PanelInspection);
    const FLBOneFactoryPressStarterStationState* Dispatch = FindStation(Layout,
        ELBOneFactoryPressStarterRole::PanelStillageDispatch);
    if (!Inbound || !CoilStore || !BlankPrep || !BlankBuffer || !Press
        || !Inspection || !Dispatch)
    {
        return {};
    }
    BuildInboundReceiving(Items, *Inbound);
    BuildCoilStore(Items, *CoilStore);
    BuildBlankPreparation(Items, *BlankPrep);
    BuildPreparedBlankAndDieBuffer(Items, *BlankBuffer);
    BuildPressTrain(Items, *Press);
    BuildInspection(Items, *Inspection);
    BuildDispatch(Items, *Dispatch);
    AddMaterialRoutes(Items, Layout);
    return Items;
}

bool ALBOneFactoryPressStarterPresentationActor::ValidatePresentationContract(
    const FLBOneFactoryPressStarterLayoutState& Layout,
    const TArray<FLBOneFactoryPressPresentationItem>& Items,
    FString& OutReason)
{
    using namespace LBOneFactoryPressPresentationPrivate;
    if (!ULBOneFactoryPressStarterLayoutLibrary::ValidateStarterLayout(
            Layout, OutReason))
    {
        return false;
    }
    const TArray<FLBOneFactoryPressPresentationItem> Expected =
        BuildExpectedPresentationItems(Layout);
    if (Expected.Num() != ExpectedLogicalItemCount
        || Items.Num() != ExpectedLogicalItemCount)
    {
        OutReason = TEXT(
            "PRESS PRESENTATION REQUIRES EXACTLY 268 LOGICAL VISUAL RECORDS");
        return false;
    }

    TSet<FName> Identities;
    TMap<ELBOneFactoryPressStarterRole, int32> RoleCounts;
    TMap<ELBOneFactoryPressPresentationBatch, int32> BatchCounts;
    int32 PressCrownCount = 0;
    float HighestPrimitiveTopCm = 0.0f;
    for (int32 Index = 0; Index < Items.Num(); ++Index)
    {
        const FLBOneFactoryPressPresentationItem& Item = Items[Index];
        const FLBOneFactoryPressStarterStationState* Station =
            FindStation(Layout, Item.StationId);
        if (Item.Version != 1 || Item.PresentationId.IsNone()
            || Item.StationId.IsNone() || !Station || Station->Role != Item.Role
            || Item.bRepresentsProcessWIP || !IsFiniteTransform(Item.WorldTransform))
        {
            OutReason = TEXT("PRESS PRESENTATION HAS INVALID CORE DATA OR A WIP CLAIM");
            return false;
        }
        if (Identities.Contains(Item.PresentationId))
        {
            OutReason = TEXT("PRESS PRESENTATION IDENTITIES MUST BE UNIQUE");
            return false;
        }
        Identities.Add(Item.PresentationId);
        RoleCounts.FindOrAdd(Item.Role) += 1;
        BatchCounts.FindOrAdd(Item.Batch) += 1;
        if (!SameItem(Item, Expected[Index]))
        {
            OutReason = TEXT("PRESS PRESENTATION INVENTORY OR TRANSFORM DRIFTED FROM V001");
            return false;
        }
        const FString Id = Item.PresentationId.ToString();
        if (Item.Role == ELBOneFactoryPressStarterRole::ConfigurablePressTrain
            && Id.Contains(TEXT("PRESS_STAGE_"))
            && Id.EndsWith(TEXT("_CROWN")))
        {
            ++PressCrownCount;
        }
        HighestPrimitiveTopCm = FMath::Max(HighestPrimitiveTopCm,
            Item.WorldTransform.GetLocation().Z
                + Item.WorldTransform.GetScale3D().Z * 50.0f);
    }
    if (Identities.Num() != ExpectedLogicalItemCount || PressCrownCount != 7
        || HighestPrimitiveTopCm < 900.0f)
    {
        OutReason = TEXT("PRESS PRESENTATION LOST ITS SEVEN-STAGE OR RAISED-SILHOUETTE CONTRACT");
        return false;
    }
    for (int32 Value = static_cast<int32>(
            ELBOneFactoryPressStarterRole::InboundCoilReceiving);
        Value <= static_cast<int32>(
            ELBOneFactoryPressStarterRole::PanelStillageDispatch); ++Value)
    {
        const ELBOneFactoryPressStarterRole Role =
            static_cast<ELBOneFactoryPressStarterRole>(Value);
        if (RoleCounts.FindRef(Role) != GetExpectedInstanceCountForRole(Role))
        {
            OutReason = TEXT("PRESS PRESENTATION ROLE COUNTS DRIFTED");
            return false;
        }
    }
    for (int32 Value = static_cast<int32>(
            ELBOneFactoryPressPresentationBatch::GraphiteCube);
        Value <= static_cast<int32>(
            ELBOneFactoryPressPresentationBatch::FloorRouteCube); ++Value)
    {
        const ELBOneFactoryPressPresentationBatch Batch =
            static_cast<ELBOneFactoryPressPresentationBatch>(Value);
        if (BatchCounts.FindRef(Batch) !=
            GetExpectedInstanceCountForBatch(Batch))
        {
            OutReason = TEXT("PRESS PRESENTATION BATCH COUNTS DRIFTED");
            return false;
        }
    }
    OutReason = TEXT(
        "PRESS PRESENTATION CONTRACT VALID: 8 LOGICAL BATCHES, 268 LOGICAL ITEMS, 7 STAGES, WIP 0");
    return true;
}

const TCHAR* ALBOneFactoryPressStarterPresentationActor::GetPresentationClassPath()
{
    return LBOneFactoryPressPresentationPrivate::ExpectedPresentationClassPath;
}

FName ALBOneFactoryPressStarterPresentationActor::GetPresentationTag()
{
    return TEXT("LB.OneFactory.PressStarter.Presentation.v001");
}
