#include "LBOneFactoryPaintStarterPresentationActor.h"

#include "Components/HierarchicalInstancedStaticMeshComponent.h"
#include "Components/SceneComponent.h"
#include "Engine/StaticMesh.h"
#include "Materials/MaterialInstanceDynamic.h"
#include "Materials/MaterialInterface.h"
#include "UObject/ConstructorHelpers.h"

namespace LBOneFactoryPaintPresentationPrivate
{
    constexpr int32 ExpectedComponentCount = 24;
    constexpr int32 ExpectedBatchCount = 22;
    constexpr int32 ExpectedInstanceCount = 119;
    constexpr int32 NativeProfileAssetCount = 10;
    constexpr int32 SupplementalEDAssetCount = 14;
    constexpr float TransformTolerance = 0.01f;

    constexpr float TreatmentScaleX = 0.18f;
    constexpr float TreatmentScaleY = 0.55f;
    constexpr float TreatmentScaleZ = 0.65f;
    constexpr float TreatmentModuleHalfOffsetCm = 81.0f;
    constexpr float TreatmentLiquidScaleX = 0.36f;
    constexpr float TreatmentLiquidZCm = 185.25f;
    constexpr float TreatmentRailOffsetYCm = 165.0f;
    constexpr float ImmersedBodyZCm = 113.75f;

    const TCHAR* ExpectedPresentationClassPath =
        TEXT("/Script/LineBossCarFactory.LBOneFactoryPaintStarterPresentationActor");
    const TCHAR* CuringOvenPath = TEXT(
        "/Game/LineBoss/Candidates/PaintShop/PaintLineNativeKit_v001/Process/"
        "SM_LB_Paint_CuringOvenTunnel_v001.SM_LB_Paint_CuringOvenTunnel_v001");
    const TCHAR* PretreatmentPath = TEXT(
        "/Game/LineBoss/Candidates/PaintShop/PaintLineNativeKit_v001/Process/"
        "SM_LB_Paint_PretreatmentWashTunnel_v001.SM_LB_Paint_PretreatmentWashTunnel_v001");
    const TCHAR* FlashOffPath = TEXT(
        "/Game/LineBoss/Candidates/PaintShop/PaintLineNativeKit_v001/Process/"
        "SM_LB_Paint_FlashOffTunnel_v001.SM_LB_Paint_FlashOffTunnel_v001");
    const TCHAR* QualityLightPath = TEXT(
        "/Game/LineBoss/Candidates/PaintShop/PaintLineNativeKit_v001/Quality/"
        "SM_LB_Paint_QualityLightTunnel_v001.SM_LB_Paint_QualityLightTunnel_v001");
    const TCHAR* BodySkidPath = TEXT(
        "/Game/LineBoss/Candidates/PaintShop/PaintLineNativeKit_v001/Logistics/"
        "SM_LB_Paint_BodySkidCarrier_v001.SM_LB_Paint_BodySkidCarrier_v001");
    const TCHAR* ServiceSetPath = TEXT(
        "/Game/LineBoss/Candidates/PaintShop/PaintLineNativeKit_v001/Services/"
        "SM_LB_Paint_ServiceSet_v001.SM_LB_Paint_ServiceSet_v001");
    const TCHAR* AirExtractionPath = TEXT(
        "/Game/LineBoss/Candidates/PaintShop/PaintLineNativeKit_v001/Services/"
        "SM_LB_Paint_AirExtractionModule_v001.SM_LB_Paint_AirExtractionModule_v001");
    const TCHAR* SprayBoothPath = TEXT(
        "/Game/LineBoss/Candidates/PaintShop/SprayBoothRuntime_v002/"
        "SM_LB_PaintSprayBooth_Runtime_v002.SM_LB_PaintSprayBooth_Runtime_v002");
    const TCHAR* CubePath = TEXT("/Engine/BasicShapes/Cube.Cube");
    const TCHAR* BasicMaterialPath =
        TEXT("/Engine/BasicShapes/BasicShapeMaterial.BasicShapeMaterial");
    const TCHAR* EDTreatmentStartPath = TEXT(
        "/Game/LineBoss/Candidates/PaintShop/EDLine/Runtime_v002/Modules/"
        "SM_LB_EDLine_OpenTreatmentModule_NoRail_Start_v002."
        "SM_LB_EDLine_OpenTreatmentModule_NoRail_Start_v002");
    const TCHAR* EDTreatmentEndPath = TEXT(
        "/Game/LineBoss/Candidates/PaintShop/EDLine/Runtime_v002/Modules/"
        "SM_LB_EDLine_OpenTreatmentModule_NoRail_End_v002."
        "SM_LB_EDLine_OpenTreatmentModule_NoRail_End_v002");
    const TCHAR* EDDrainInspectionPath = TEXT(
        "/Game/LineBoss/Candidates/PaintShop/EDLine/Runtime_v001/Modules/"
        "SM_LB_EDLine_DrainInspectionModule_Blockout_v001."
        "SM_LB_EDLine_DrainInspectionModule_Blockout_v001");
    // v002: the blockout oven modules give way to one production oven bay
    // tiled end to end, and the carrier gantry the bodies hang from.
    const TCHAR* EDOvenSegmentPath = TEXT(
        "/Game/LineBoss/Candidates/PaintShop/EDLineOven_v002/"
        "SM_LB_EDLine_OvenSegment_v002."
        "SM_LB_EDLine_OvenSegment_v002");
    const TCHAR* EDCarrierGantryPath = TEXT(
        "/Game/LineBoss/Candidates/PaintShop/EDLineGantry_v001/"
        "SM_LB_EDLine_CarrierGantryBay_v001."
        "SM_LB_EDLine_CarrierGantryBay_v001");
    const TCHAR* EDTreatmentLiquidPath = TEXT(
        "/Game/LineBoss/Candidates/PaintShop/EDLine/Runtime_v001/Process/"
        "SM_LB_EDLine_TreatmentLiquidSurface_Blockout_v001."
        "SM_LB_EDLine_TreatmentLiquidSurface_Blockout_v001");
    const TCHAR* EDImmersedBIWPath = TEXT(
        "/Game/LineBoss/Factory/OneFactory/v001/Vehicles/"
        "Cairnwell2040Runtime_v001/Meshes/"
        "SM_LB_C2040_BIW_AutomotiveSkeleton_v001."
        "SM_LB_C2040_BIW_AutomotiveSkeleton_v001");
    const TCHAR* EDImmersedBIWMaterialPath = TEXT(
        "/Game/LineBoss/Factory/OneFactory/v001/Vehicles/"
        "Cairnwell2040Runtime_v001/Materials/"
        "M_LB_C2040_BIWGalvanized_v001.M_LB_C2040_BIWGalvanized_v001");
    const TCHAR* EDProfiledRailMaterialPath = TEXT(
        "/Game/LineBoss/Candidates/PaintShop/EDLine/Runtime_v001/Materials/"
        "MI_LB_EDLine_StructuralSteel_Graphite_v001."
        "MI_LB_EDLine_StructuralSteel_Graphite_v001");

    const TCHAR* EDLiquidMaterialPaths[] = {
        TEXT("/Game/LineBoss/Candidates/PaintShop/EDLine/Runtime_v001/Materials/MI_LB_EDLine_Liquid_Degrease_v001.MI_LB_EDLine_Liquid_Degrease_v001"),
        TEXT("/Game/LineBoss/Candidates/PaintShop/EDLine/Runtime_v001/Materials/MI_LB_EDLine_Liquid_Rinse1_v001.MI_LB_EDLine_Liquid_Rinse1_v001"),
        TEXT("/Game/LineBoss/Candidates/PaintShop/EDLine/Runtime_v001/Materials/MI_LB_EDLine_Liquid_Phosphate_v001.MI_LB_EDLine_Liquid_Phosphate_v001"),
        TEXT("/Game/LineBoss/Candidates/PaintShop/EDLine/Runtime_v001/Materials/MI_LB_EDLine_Liquid_Rinse2_v001.MI_LB_EDLine_Liquid_Rinse2_v001"),
        TEXT("/Game/LineBoss/Candidates/PaintShop/EDLine/Runtime_v001/Materials/MI_LB_EDLine_Liquid_ED_Ecoat_v001.MI_LB_EDLine_Liquid_ED_Ecoat_v001"),
        TEXT("/Game/LineBoss/Candidates/PaintShop/EDLine/Runtime_v001/Materials/MI_LB_EDLine_Liquid_UF_Rinse_v001.MI_LB_EDLine_Liquid_UF_Rinse_v001")
    };

    const TCHAR* SupplementalEDAssetPaths[] = {
        EDTreatmentStartPath,
        EDTreatmentEndPath,
        EDDrainInspectionPath,
        EDOvenSegmentPath,
        EDCarrierGantryPath,
        EDTreatmentLiquidPath,
        EDImmersedBIWPath,
        EDLiquidMaterialPaths[0],
        EDLiquidMaterialPaths[1],
        EDLiquidMaterialPaths[2],
        EDLiquidMaterialPaths[3],
        EDLiquidMaterialPaths[4],
        EDLiquidMaterialPaths[5],
        EDImmersedBIWMaterialPath
    };

    template <typename TObjectType>
    TObjectType* FindConstructorObject(const TCHAR* Path)
    {
        ConstructorHelpers::FObjectFinder<TObjectType> Finder(Path);
        return Finder.Succeeded() ? Finder.Object.Get() : nullptr;
    }

    const FLBOneFactoryPaintStarterStationState* FindStation(
        const FLBOneFactoryPaintStarterLayoutState& Layout,
        const ELBOneFactoryPaintStarterRole Role)
    {
        return Layout.Stations.FindByPredicate([Role](
            const FLBOneFactoryPaintStarterStationState& Station)
        {
            return Station.Role == Role;
        });
    }

    const FLBOneFactoryPaintStarterStationState* FindStation(
        const FLBOneFactoryPaintStarterLayoutState& Layout,
        const FName StationId)
    {
        return Layout.Stations.FindByPredicate([StationId](
            const FLBOneFactoryPaintStarterStationState& Station)
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

    bool SameItem(const FLBOneFactoryPaintPresentationItem& Left,
        const FLBOneFactoryPaintPresentationItem& Right)
    {
        return Left.Version == Right.Version
            && Left.PresentationId == Right.PresentationId
            && Left.StationId == Right.StationId
            && Left.Role == Right.Role
            && Left.Batch == Right.Batch
            && Left.WorldTransform.Equals(Right.WorldTransform,
                TransformTolerance)
            && Left.bClaimsHiddenProcessInternals ==
                Right.bClaimsHiddenProcessInternals
            && Left.bRepresentsProcessWIP == Right.bRepresentsProcessWIP;
    }

    FString MakePresentationId(const FName StationId, const FString& Suffix)
    {
        return FString::Printf(TEXT("OF_PAINT_VIS_%s_%s"),
            *StationId.ToString(), *Suffix);
    }

    void AddItem(TArray<FLBOneFactoryPaintPresentationItem>& Items,
        const FLBOneFactoryPaintStarterStationState& Station,
        const FString& Suffix,
        const ELBOneFactoryPaintPresentationBatch Batch,
        const FTransform& LocalTransform = FTransform::Identity)
    {
        FLBOneFactoryPaintPresentationItem& Item =
            Items.AddDefaulted_GetRef();
        Item.PresentationId = FName(*MakePresentationId(
            Station.StationId, Suffix));
        Item.StationId = Station.StationId;
        Item.Role = Station.Role;
        Item.Batch = Batch;
        Item.WorldTransform = LocalTransform * Station.WorldTransform;
        Item.bClaimsHiddenProcessInternals = false;
        Item.bRepresentsProcessWIP = false;
    }

    void AddStatus(TArray<FLBOneFactoryPaintPresentationItem>& Items,
        const FLBOneFactoryPaintStarterStationState& Station)
    {
        const FVector Half = Station.FootprintSizeCm * 0.5f;
        const FTransform Local(FRotator::ZeroRotator,
            FVector(Half.X - 55.0f, Half.Y - 55.0f, 80.0f),
            FVector(0.35f, 0.35f, 1.6f));
        AddItem(Items, Station, TEXT("SEMANTIC_STATUS"),
            ELBOneFactoryPaintPresentationBatch::StatusCube, Local);
    }

    void AddRoute(TArray<FLBOneFactoryPaintPresentationItem>& Items,
        const FLBOneFactoryPaintStarterStationState& Source,
        const FLBOneFactoryPaintStarterStationState& Target,
        const int32 RouteIndex)
    {
        const FVector Start = Source.WorldTransform.GetLocation();
        const FVector End = Target.WorldTransform.GetLocation();
        const FVector Delta = End - Start;
        const float Length = FVector2D(Delta.X, Delta.Y).Size();
        const float Yaw = FMath::RadiansToDegrees(
            FMath::Atan2(Delta.Y, Delta.X));
        const FTransform World(FRotator(0.0f, Yaw, 0.0f),
            (Start + End) * 0.5f + FVector(0.0f, 0.0f, 3.0f),
            FVector(Length / 100.0f, 0.16f, 0.06f));
        FLBOneFactoryPaintPresentationItem& Item =
            Items.AddDefaulted_GetRef();
        Item.PresentationId = FName(*MakePresentationId(Source.StationId,
            FString::Printf(TEXT("ROUTE_%02d"), RouteIndex + 1)));
        Item.StationId = Source.StationId;
        Item.Role = Source.Role;
        Item.Batch = ELBOneFactoryPaintPresentationBatch::FloorRouteCube;
        Item.WorldTransform = World;
        Item.bClaimsHiddenProcessInternals = false;
        Item.bRepresentsProcessWIP = false;
    }

    FTransform Offset(const FVector& Location)
    {
        return FTransform(FRotator::ZeroRotator, Location,
            FVector::OneVector);
    }

    FTransform CubeAt(const FVector& Location, const FVector& DimensionsCm)
    {
        return FTransform(FRotator::ZeroRotator, Location,
            DimensionsCm / 100.0f);
    }

    void AddRailSegment(
        TArray<FLBOneFactoryPaintPresentationItem>& Items,
        const FLBOneFactoryPaintStarterStationState& Station,
        const int32 TankIndex, const int32 SideIndex,
        const int32 SegmentIndex, const FVector& Start, const FVector& End)
    {
        const FVector Delta = End - Start;
        const FQuat Rotation = FRotationMatrix::MakeFromX(
            Delta.GetSafeNormal()).ToQuat();
        const FTransform Local(Rotation, (Start + End) * 0.5f,
            FVector(Delta.Size() / 100.0f, 0.055f, 0.055f));
        AddItem(Items, Station, FString::Printf(
                TEXT("TANK_%02d_RAIL_%d_SEG_%02d"),
                TankIndex + 1, SideIndex + 1, SegmentIndex + 1),
            ELBOneFactoryPaintPresentationBatch::EDProfiledRailCube, Local);
    }

    void AddTreatmentTank(
        TArray<FLBOneFactoryPaintPresentationItem>& Items,
        const FLBOneFactoryPaintStarterStationState& Station,
        const int32 TankIndex, const float CentreXCm,
        const ELBOneFactoryPaintPresentationBatch LiquidBatch)
    {
        const FVector ModuleScale(
            TreatmentScaleX, TreatmentScaleY, TreatmentScaleZ);
        AddItem(Items, Station,
            FString::Printf(TEXT("TANK_%02d_START"), TankIndex + 1),
            ELBOneFactoryPaintPresentationBatch::EDTreatmentStartModule,
            FTransform(FRotator::ZeroRotator,
                FVector(CentreXCm - TreatmentModuleHalfOffsetCm, 0.0f, 0.0f),
                ModuleScale));
        AddItem(Items, Station,
            FString::Printf(TEXT("TANK_%02d_END"), TankIndex + 1),
            ELBOneFactoryPaintPresentationBatch::EDTreatmentEndModule,
            FTransform(FRotator::ZeroRotator,
                FVector(CentreXCm + TreatmentModuleHalfOffsetCm, 0.0f, 0.0f),
                ModuleScale));
        AddItem(Items, Station,
            FString::Printf(TEXT("TANK_%02d_GANTRY"), TankIndex + 1),
            ELBOneFactoryPaintPresentationBatch::EDCarrierGantryBay,
            FTransform(FRotator::ZeroRotator,
                FVector(CentreXCm, 0.0f, 0.0f), FVector::OneVector));
        AddItem(Items, Station,
            FString::Printf(TEXT("TANK_%02d_LIQUID"), TankIndex + 1),
            LiquidBatch,
            FTransform(FRotator::ZeroRotator,
                FVector(CentreXCm, 0.0f, TreatmentLiquidZCm),
                FVector(TreatmentLiquidScaleX, TreatmentScaleY,
                    TreatmentScaleZ)));

        const float ProfileXCm[] = {
            -900.0f, -600.0f, -150.0f, 150.0f, 600.0f, 900.0f};
        const float ProfileZCm[] = {
            800.0f, 800.0f, 545.0f, 545.0f, 800.0f, 800.0f};
        for (int32 SideIndex = 0; SideIndex < 2; ++SideIndex)
        {
            const float Y = SideIndex == 0
                ? -TreatmentRailOffsetYCm : TreatmentRailOffsetYCm;
            for (int32 SegmentIndex = 0; SegmentIndex < 5; ++SegmentIndex)
            {
                const FVector Start(
                    CentreXCm + ProfileXCm[SegmentIndex] * TreatmentScaleX,
                    Y, ProfileZCm[SegmentIndex] * TreatmentScaleZ);
                const FVector End(
                    CentreXCm + ProfileXCm[SegmentIndex + 1] * TreatmentScaleX,
                    Y, ProfileZCm[SegmentIndex + 1] * TreatmentScaleZ);
                AddRailSegment(Items, Station, TankIndex, SideIndex,
                    SegmentIndex, Start, End);
            }
        }
    }
}

ALBOneFactoryPaintStarterPresentationActor::
    ALBOneFactoryPaintStarterPresentationActor()
{
    using namespace LBOneFactoryPaintPresentationPrivate;
    PrimaryActorTick.bCanEverTick = false;
    SetReplicates(false);
    SetActorEnableCollision(false);

    SceneRoot = CreateDefaultSubobject<USceneComponent>(TEXT("SceneRoot"));
    SceneRoot->SetMobility(EComponentMobility::Movable);
    SetRootComponent(SceneRoot);

    CuringOvenBatch =
        CreateDefaultSubobject<UHierarchicalInstancedStaticMeshComponent>(
            TEXT("CuringOvenBatch"));
    PretreatmentBatch =
        CreateDefaultSubobject<UHierarchicalInstancedStaticMeshComponent>(
            TEXT("PretreatmentBatch"));
    FlashOffBatch =
        CreateDefaultSubobject<UHierarchicalInstancedStaticMeshComponent>(
            TEXT("FlashOffBatch"));
    QualityLightBatch =
        CreateDefaultSubobject<UHierarchicalInstancedStaticMeshComponent>(
            TEXT("QualityLightBatch"));
    BodySkidBatch =
        CreateDefaultSubobject<UHierarchicalInstancedStaticMeshComponent>(
            TEXT("BodySkidBatch"));
    ServiceSetBatch =
        CreateDefaultSubobject<UHierarchicalInstancedStaticMeshComponent>(
            TEXT("ServiceSetBatch"));
    AirExtractionBatch =
        CreateDefaultSubobject<UHierarchicalInstancedStaticMeshComponent>(
            TEXT("AirExtractionBatch"));
    SprayBoothBatch =
        CreateDefaultSubobject<UHierarchicalInstancedStaticMeshComponent>(
            TEXT("SprayBoothBatch"));
    FloorRouteBatch =
        CreateDefaultSubobject<UHierarchicalInstancedStaticMeshComponent>(
            TEXT("FloorRouteBatch"));
    StatusBatch =
        CreateDefaultSubobject<UHierarchicalInstancedStaticMeshComponent>(
            TEXT("StatusBatch"));
    ProgrammeColourBatch =
        CreateDefaultSubobject<UHierarchicalInstancedStaticMeshComponent>(
            TEXT("ProgrammeColourBatch"));
    EDTreatmentStartBatch =
        CreateDefaultSubobject<UHierarchicalInstancedStaticMeshComponent>(
            TEXT("EDTreatmentStartBatch"));
    EDTreatmentEndBatch =
        CreateDefaultSubobject<UHierarchicalInstancedStaticMeshComponent>(
            TEXT("EDTreatmentEndBatch"));
    EDLiquidDegreaseBatch =
        CreateDefaultSubobject<UHierarchicalInstancedStaticMeshComponent>(
            TEXT("EDLiquidDegreaseBatch"));
    EDLiquidRinse1Batch =
        CreateDefaultSubobject<UHierarchicalInstancedStaticMeshComponent>(
            TEXT("EDLiquidRinse1Batch"));
    EDLiquidPhosphateBatch =
        CreateDefaultSubobject<UHierarchicalInstancedStaticMeshComponent>(
            TEXT("EDLiquidPhosphateBatch"));
    EDLiquidRinse2Batch =
        CreateDefaultSubobject<UHierarchicalInstancedStaticMeshComponent>(
            TEXT("EDLiquidRinse2Batch"));
    EDLiquidEDCoatBatch =
        CreateDefaultSubobject<UHierarchicalInstancedStaticMeshComponent>(
            TEXT("EDLiquidEDCoatBatch"));
    EDLiquidUFRinseBatch =
        CreateDefaultSubobject<UHierarchicalInstancedStaticMeshComponent>(
            TEXT("EDLiquidUFRinseBatch"));
    EDProfiledRailBatch =
        CreateDefaultSubobject<UHierarchicalInstancedStaticMeshComponent>(
            TEXT("EDProfiledRailBatch"));
    EDImmersedBodyBatch =
        CreateDefaultSubobject<UHierarchicalInstancedStaticMeshComponent>(
            TEXT("EDImmersedBodyBatch"));
    EDDrainInspectionBatch =
        CreateDefaultSubobject<UHierarchicalInstancedStaticMeshComponent>(
            TEXT("EDDrainInspectionBatch"));
    EDOvenSegmentBatch =
        CreateDefaultSubobject<UHierarchicalInstancedStaticMeshComponent>(
            TEXT("EDOvenSegmentBatch"));
    EDCarrierGantryBatch =
        CreateDefaultSubobject<UHierarchicalInstancedStaticMeshComponent>(
            TEXT("EDCarrierGantryBatch"));

    for (UHierarchicalInstancedStaticMeshComponent* Batch : GetAllBatches())
    {
        if (!Batch) continue;
        Batch->SetupAttachment(SceneRoot);
        ConfigureVisualBatch(Batch);
    }
    FloorRouteBatch->SetCastShadow(false);
    StatusBatch->SetCastShadow(false);
    ProgrammeColourBatch->SetCastShadow(false);

    CuringOvenMesh = TSoftObjectPtr<UStaticMesh>(FSoftObjectPath(CuringOvenPath));
    PretreatmentMesh = TSoftObjectPtr<UStaticMesh>(FSoftObjectPath(PretreatmentPath));
    FlashOffMesh = TSoftObjectPtr<UStaticMesh>(FSoftObjectPath(FlashOffPath));
    QualityLightMesh = TSoftObjectPtr<UStaticMesh>(FSoftObjectPath(QualityLightPath));
    BodySkidMesh = TSoftObjectPtr<UStaticMesh>(FSoftObjectPath(BodySkidPath));
    ServiceSetMesh = TSoftObjectPtr<UStaticMesh>(FSoftObjectPath(ServiceSetPath));
    AirExtractionMesh = TSoftObjectPtr<UStaticMesh>(FSoftObjectPath(AirExtractionPath));
    SprayBoothMesh = TSoftObjectPtr<UStaticMesh>(FSoftObjectPath(SprayBoothPath));
    CubeMesh = TSoftObjectPtr<UStaticMesh>(FSoftObjectPath(CubePath));
    SemanticBaseMaterial = TSoftObjectPtr<UMaterialInterface>(
        FSoftObjectPath(BasicMaterialPath));

    EDTreatmentStartMesh = FindConstructorObject<UStaticMesh>(
        EDTreatmentStartPath);
    EDTreatmentEndMesh = FindConstructorObject<UStaticMesh>(
        EDTreatmentEndPath);
    EDDrainInspectionMesh = FindConstructorObject<UStaticMesh>(
        EDDrainInspectionPath);
    EDOvenSegmentMesh =
        FindConstructorObject<UStaticMesh>(EDOvenSegmentPath);
    EDCarrierGantryMesh =
        FindConstructorObject<UStaticMesh>(EDCarrierGantryPath);
    EDTreatmentLiquidMesh = FindConstructorObject<UStaticMesh>(
        EDTreatmentLiquidPath);
    EDImmersedBIWMesh = FindConstructorObject<UStaticMesh>(
        EDImmersedBIWPath);
    EDImmersedBIWMaterial = FindConstructorObject<UMaterialInterface>(
        EDImmersedBIWMaterialPath);
    EDTreatmentLiquidMaterials.Reserve(UE_ARRAY_COUNT(EDLiquidMaterialPaths));
    for (const TCHAR* MaterialPath : EDLiquidMaterialPaths)
    {
        EDTreatmentLiquidMaterials.Add(
            FindConstructorObject<UMaterialInterface>(MaterialPath));
    }

    Tags.AddUnique(GetPresentationTag());
    Tags.AddUnique(TEXT("LB.OneFactory.PaintStarter.NativeAuthored"));
    Tags.AddUnique(TEXT("LB.Environment.VisualOnly"));
    // Retained for the builder's legacy spray-booth compatibility audit; the
    // pretreatment/ED route itself is now visibly open and tracked.
    Tags.AddUnique(TEXT("LB.Paint.BlackBoxExteriorOnly"));
    Tags.AddUnique(TEXT("LB.Paint.TrackedEDLineVisible"));
    Tags.AddUnique(TEXT("LB.Paint.OpenTreatmentVisible"));
    Tags.AddUnique(TEXT("LB.NotProcessWIP"));
    SetActorHiddenInGame(true);
}

void ALBOneFactoryPaintStarterPresentationActor::ConfigureVisualBatch(
    UHierarchicalInstancedStaticMeshComponent* Component)
{
    if (!Component) return;
    Component->PrimaryComponentTick.bCanEverTick = false;
    Component->SetComponentTickEnabled(false);
    Component->SetMobility(EComponentMobility::Movable);
    Component->SetCollisionEnabled(ECollisionEnabled::NoCollision);
    Component->SetCollisionResponseToAllChannels(ECR_Ignore);
    Component->SetGenerateOverlapEvents(false);
    Component->SetCanEverAffectNavigation(false);
    Component->SetCastShadow(true);
    Component->SetReceivesDecals(false);
    Component->SetCullDistances(0, 80000);
}

TArray<UHierarchicalInstancedStaticMeshComponent*>
ALBOneFactoryPaintStarterPresentationActor::GetAllBatches() const
{
    return {
        CuringOvenBatch.Get(),
        PretreatmentBatch.Get(),
        FlashOffBatch.Get(),
        QualityLightBatch.Get(),
        BodySkidBatch.Get(),
        ServiceSetBatch.Get(),
        AirExtractionBatch.Get(),
        SprayBoothBatch.Get(),
        FloorRouteBatch.Get(),
        StatusBatch.Get(),
        ProgrammeColourBatch.Get(),
        EDTreatmentStartBatch.Get(),
        EDTreatmentEndBatch.Get(),
        EDLiquidDegreaseBatch.Get(),
        EDLiquidRinse1Batch.Get(),
        EDLiquidPhosphateBatch.Get(),
        EDLiquidRinse2Batch.Get(),
        EDLiquidEDCoatBatch.Get(),
        EDLiquidUFRinseBatch.Get(),
        EDProfiledRailBatch.Get(),
        EDImmersedBodyBatch.Get(),
        EDDrainInspectionBatch.Get(),
        EDOvenSegmentBatch.Get(),
        EDCarrierGantryBatch.Get()
    };
}

UHierarchicalInstancedStaticMeshComponent*
ALBOneFactoryPaintStarterPresentationActor::FindBatchComponent(
    const ELBOneFactoryPaintPresentationBatch Batch) const
{
    switch (Batch)
    {
    case ELBOneFactoryPaintPresentationBatch::CuringOvenTunnel:
        return CuringOvenBatch.Get();
    case ELBOneFactoryPaintPresentationBatch::PretreatmentWashTunnel:
        return PretreatmentBatch.Get();
    case ELBOneFactoryPaintPresentationBatch::FlashOffTunnel:
        return FlashOffBatch.Get();
    case ELBOneFactoryPaintPresentationBatch::QualityLightTunnel:
        return QualityLightBatch.Get();
    case ELBOneFactoryPaintPresentationBatch::BodySkidCarrier:
        return BodySkidBatch.Get();
    case ELBOneFactoryPaintPresentationBatch::PaintServiceSet:
        return ServiceSetBatch.Get();
    case ELBOneFactoryPaintPresentationBatch::AirExtractionModule:
        return AirExtractionBatch.Get();
    case ELBOneFactoryPaintPresentationBatch::BlackBoxSprayBooth:
        return SprayBoothBatch.Get();
    case ELBOneFactoryPaintPresentationBatch::FloorRouteCube:
        return FloorRouteBatch.Get();
    case ELBOneFactoryPaintPresentationBatch::StatusCube:
        return StatusBatch.Get();
    case ELBOneFactoryPaintPresentationBatch::ProgrammeColourCube:
        return ProgrammeColourBatch.Get();
    case ELBOneFactoryPaintPresentationBatch::EDTreatmentStartModule:
        return EDTreatmentStartBatch.Get();
    case ELBOneFactoryPaintPresentationBatch::EDTreatmentEndModule:
        return EDTreatmentEndBatch.Get();
    case ELBOneFactoryPaintPresentationBatch::EDLiquidDegrease:
        return EDLiquidDegreaseBatch.Get();
    case ELBOneFactoryPaintPresentationBatch::EDLiquidRinse1:
        return EDLiquidRinse1Batch.Get();
    case ELBOneFactoryPaintPresentationBatch::EDLiquidPhosphate:
        return EDLiquidPhosphateBatch.Get();
    case ELBOneFactoryPaintPresentationBatch::EDLiquidRinse2:
        return EDLiquidRinse2Batch.Get();
    case ELBOneFactoryPaintPresentationBatch::EDLiquidEDCoat:
        return EDLiquidEDCoatBatch.Get();
    case ELBOneFactoryPaintPresentationBatch::EDLiquidUFRinse:
        return EDLiquidUFRinseBatch.Get();
    case ELBOneFactoryPaintPresentationBatch::EDProfiledRailCube:
        return EDProfiledRailBatch.Get();
    case ELBOneFactoryPaintPresentationBatch::EDImmersedBody:
        return EDImmersedBodyBatch.Get();
    case ELBOneFactoryPaintPresentationBatch::EDDrainInspectionModule:
        return EDDrainInspectionBatch.Get();
    case ELBOneFactoryPaintPresentationBatch::EDOvenSegment:
        return EDOvenSegmentBatch.Get();
    case ELBOneFactoryPaintPresentationBatch::EDCarrierGantryBay:
        return EDCarrierGantryBatch.Get();
    default:
        return nullptr;
    }
}

void ALBOneFactoryPaintStarterPresentationActor::ClearPresentation()
{
    for (UHierarchicalInstancedStaticMeshComponent* Batch : GetAllBatches())
    {
        if (!Batch) continue;
        Batch->ClearInstances();
        Batch->SetStaticMesh(nullptr);
        Batch->EmptyOverrideMaterials();
    }
    SemanticMaterials.Reset();
    ConfiguredItems.Reset();
    ConfiguredStationTransforms.Reset();
    ConfiguredLayoutId = NAME_None;
    ConfiguredLayoutRevision = INDEX_NONE;
    ConfiguredBodyColour = ELBOneFactoryPaintColour::BodyInWhite;
    bPresentationConfigured = false;
    SetActorHiddenInGame(true);
}

bool ALBOneFactoryPaintStarterPresentationActor::ConfigureFromLayout(
    const FLBOneFactoryPaintStarterLayoutState& Layout, FString& OutReason)
{
    using namespace LBOneFactoryPaintPresentationPrivate;
    ClearPresentation();
    if (!ValidateNativePresentationReferences(GetPresentationClassPath(),
            GetRequiredNativeAssetPaths(), OutReason))
    {
        OutReason = FString::Printf(TEXT("PAINT PRESENTATION PROVENANCE FAILED: %s"),
            *OutReason);
        return false;
    }
    const TArray<FLBOneFactoryPaintPresentationItem> CandidateItems =
        BuildExpectedPresentationItems(Layout);
    if (!ValidatePresentationContract(Layout, CandidateItems, OutReason))
    {
        OutReason = FString::Printf(TEXT("PAINT PRESENTATION CONTRACT FAILED: %s"),
            *OutReason);
        return false;
    }

    UStaticMesh* ResolvedCuring = CuringOvenMesh.LoadSynchronous();
    UStaticMesh* ResolvedPretreatment = PretreatmentMesh.LoadSynchronous();
    UStaticMesh* ResolvedFlash = FlashOffMesh.LoadSynchronous();
    UStaticMesh* ResolvedQuality = QualityLightMesh.LoadSynchronous();
    UStaticMesh* ResolvedSkid = BodySkidMesh.LoadSynchronous();
    UStaticMesh* ResolvedService = ServiceSetMesh.LoadSynchronous();
    UStaticMesh* ResolvedExtraction = AirExtractionMesh.LoadSynchronous();
    UStaticMesh* ResolvedBooth = SprayBoothMesh.LoadSynchronous();
    UStaticMesh* ResolvedCube = CubeMesh.LoadSynchronous();
    UMaterialInterface* ResolvedMaterial = SemanticBaseMaterial.LoadSynchronous();
    const TArray<UStaticMesh*> ResolvedMeshes = {
        ResolvedCuring, ResolvedPretreatment, ResolvedFlash, ResolvedQuality,
        ResolvedSkid, ResolvedService, ResolvedExtraction, ResolvedBooth,
        ResolvedCube};
    const int32 RequiredLODs[] = {3, 3, 3, 3, 3, 3, 3, 2, 1};
    for (int32 Index = 0; Index < ResolvedMeshes.Num(); ++Index)
    {
        if (!ResolvedMeshes[Index]
            || ResolvedMeshes[Index]->GetNumLODs() != RequiredLODs[Index])
        {
            OutReason = FString::Printf(TEXT(
                "PAINT PRESENTATION COULD NOT RESOLVE EXACT MESH/LOD CONTRACT AT INDEX %d"),
                Index);
            ClearPresentation();
            return false;
        }
    }
    const TArray<UStaticMesh*> SupplementalMeshes = {
        EDTreatmentStartMesh.Get(), EDTreatmentEndMesh.Get(),
        EDDrainInspectionMesh.Get(), EDOvenSegmentMesh.Get(),
        EDCarrierGantryMesh.Get(),
        EDTreatmentLiquidMesh.Get(), EDImmersedBIWMesh.Get()};
    for (int32 Index = 0; Index < SupplementalMeshes.Num(); ++Index)
    {
        if (!SupplementalMeshes[Index]
            || SupplementalMeshes[Index]->GetNumLODs() < 1)
        {
            OutReason = FString::Printf(TEXT(
                "PAINT PRESENTATION COULD NOT RESOLVE ED MESH AT CLOSURE INDEX %d"),
                Index);
            ClearPresentation();
            return false;
        }
    }
    if (EDTreatmentLiquidMaterials.Num()
            != UE_ARRAY_COUNT(EDLiquidMaterialPaths))
    {
        OutReason = TEXT("PAINT PRESENTATION ED LIQUID MATERIAL CLOSURE DRIFTED");
        ClearPresentation();
        return false;
    }
    if (!EDImmersedBIWMaterial)
    {
        OutReason = TEXT(
            "PAINT PRESENTATION COULD NOT RESOLVE THE V013 C2040 BIW MATERIAL");
        ClearPresentation();
        return false;
    }
    if (EDImmersedBIWMesh->GetNumLODs() != 3
        || EDImmersedBIWMesh->GetStaticMaterials().Num() != 1
        || EDImmersedBIWMesh->GetMaterial(0) != EDImmersedBIWMaterial.Get())
    {
        OutReason = TEXT(
            "PAINT PRESENTATION V013 C2040 BIW LOD/MATERIAL BINDING DRIFTED");
        ClearPresentation();
        return false;
    }
    for (const TObjectPtr<UMaterialInterface>& Material
        : EDTreatmentLiquidMaterials)
    {
        if (!Material)
        {
            OutReason = TEXT("PAINT PRESENTATION COULD NOT RESOLVE ED LIQUID MATERIAL");
            ClearPresentation();
            return false;
        }
    }
    const TArray<UHierarchicalInstancedStaticMeshComponent*> Batches =
        GetAllBatches();
    if (!ResolvedMaterial || Batches.Num() != ExpectedComponentCount
        || Batches.Contains(nullptr))
    {
        OutReason = TEXT(
            "PAINT PRESENTATION COULD NOT RESOLVE ITS MATERIAL OR 24 COMPONENTS");
        ClearPresentation();
        return false;
    }

    CuringOvenBatch->SetStaticMesh(ResolvedCuring);
    PretreatmentBatch->SetStaticMesh(ResolvedPretreatment);
    FlashOffBatch->SetStaticMesh(ResolvedFlash);
    QualityLightBatch->SetStaticMesh(ResolvedQuality);
    BodySkidBatch->SetStaticMesh(ResolvedSkid);
    ServiceSetBatch->SetStaticMesh(ResolvedService);
    AirExtractionBatch->SetStaticMesh(ResolvedExtraction);
    SprayBoothBatch->SetStaticMesh(ResolvedBooth);
    FloorRouteBatch->SetStaticMesh(ResolvedCube);
    StatusBatch->SetStaticMesh(ResolvedCube);
    ProgrammeColourBatch->SetStaticMesh(ResolvedCube);
    EDTreatmentStartBatch->SetStaticMesh(EDTreatmentStartMesh.Get());
    EDTreatmentEndBatch->SetStaticMesh(EDTreatmentEndMesh.Get());
    EDLiquidDegreaseBatch->SetStaticMesh(EDTreatmentLiquidMesh.Get());
    EDLiquidRinse1Batch->SetStaticMesh(EDTreatmentLiquidMesh.Get());
    EDLiquidPhosphateBatch->SetStaticMesh(EDTreatmentLiquidMesh.Get());
    EDLiquidRinse2Batch->SetStaticMesh(EDTreatmentLiquidMesh.Get());
    EDLiquidEDCoatBatch->SetStaticMesh(EDTreatmentLiquidMesh.Get());
    EDLiquidUFRinseBatch->SetStaticMesh(EDTreatmentLiquidMesh.Get());
    EDProfiledRailBatch->SetStaticMesh(ResolvedCube);
    EDImmersedBodyBatch->SetStaticMesh(EDImmersedBIWMesh.Get());
    EDImmersedBodyBatch->SetMaterial(0, EDImmersedBIWMaterial.Get());
    EDDrainInspectionBatch->SetStaticMesh(EDDrainInspectionMesh.Get());
    EDOvenSegmentBatch->SetStaticMesh(EDOvenSegmentMesh.Get());
    EDCarrierGantryBatch->SetStaticMesh(EDCarrierGantryMesh.Get());

    UHierarchicalInstancedStaticMeshComponent* LiquidBatches[] = {
        EDLiquidDegreaseBatch.Get(), EDLiquidRinse1Batch.Get(),
        EDLiquidPhosphateBatch.Get(), EDLiquidRinse2Batch.Get(),
        EDLiquidEDCoatBatch.Get(), EDLiquidUFRinseBatch.Get()};
    for (int32 Index = 0; Index < UE_ARRAY_COUNT(LiquidBatches); ++Index)
    {
        LiquidBatches[Index]->SetMaterial(
            0, EDTreatmentLiquidMaterials[Index].Get());
    }
    UMaterialInterface* RailMaterial = EDTreatmentStartMesh->GetMaterial(1);
    if (!RailMaterial || !RailMaterial->GetPathName().Equals(
            EDProfiledRailMaterialPath, ESearchCase::CaseSensitive))
    {
        OutReason = TEXT(
            "PAINT PRESENTATION ED PROFILED RAIL MATERIAL SLOT 1 DRIFTED");
        ClearPresentation();
        return false;
    }
    EDProfiledRailBatch->SetMaterial(0, RailMaterial);

    const FLinearColor SemanticColours[] = {
        FLinearColor::FromSRGBColor(FColor::FromHex(TEXT("D79F2B"))),
        Layout.bCommissioned
            ? FLinearColor::FromSRGBColor(FColor::FromHex(TEXT("39C980")))
            : FLinearColor::FromSRGBColor(FColor::FromHex(TEXT("E1B83F"))),
        ULBOneFactoryPaintStarterLayoutLibrary::GetProgrammeDisplayColour(
            Layout.SelectedBodyColour)};
    UHierarchicalInstancedStaticMeshComponent* SemanticBatches[] = {
        FloorRouteBatch.Get(), StatusBatch.Get(), ProgrammeColourBatch.Get()};
    for (int32 Index = 0; Index < UE_ARRAY_COUNT(SemanticBatches); ++Index)
    {
        UMaterialInstanceDynamic* Material =
            UMaterialInstanceDynamic::Create(ResolvedMaterial, this);
        if (!Material)
        {
            OutReason = TEXT("PAINT PRESENTATION COULD NOT CREATE THREE SEMANTIC MATERIALS");
            ClearPresentation();
            return false;
        }
        Material->SetVectorParameterValue(TEXT("Color"), SemanticColours[Index]);
        Material->SetVectorParameterValue(TEXT("BaseColor"), SemanticColours[Index]);
        SemanticBatches[Index]->SetMaterial(0, Material);
        SemanticMaterials.Add(Material);
    }

    for (const FLBOneFactoryPaintPresentationItem& Item : CandidateItems)
    {
        UHierarchicalInstancedStaticMeshComponent* Batch =
            FindBatchComponent(Item.Batch);
        if (!Batch || Batch->AddInstance(Item.WorldTransform, true) == INDEX_NONE)
        {
            OutReason = FString::Printf(
                TEXT("PAINT PRESENTATION FAILED TO COMMIT %s"),
                *Item.PresentationId.ToString());
            ClearPresentation();
            return false;
        }
    }
    if (GetVisibleInstanceCount() != GetExpectedVisibleInstanceCount()
        || GetVisualBatchCount() != GetExpectedVisualBatchCount())
    {
        OutReason = TEXT("PAINT PRESENTATION COMMIT MISSED ITS EXACT COUNTS");
        ClearPresentation();
        return false;
    }

    for (const FLBOneFactoryPaintStarterStationState& Station : Layout.Stations)
        ConfiguredStationTransforms.Add(Station.StationId, Station.WorldTransform);
    ConfiguredItems = CandidateItems;
    ConfiguredLayoutId = Layout.LayoutId;
    ConfiguredLayoutRevision = Layout.Revision;
    ConfiguredBodyColour = Layout.SelectedBodyColour;
    bPresentationConfigured = true;
    SetActorHiddenInGame(false);
    OutReason = FString::Printf(TEXT(
        "NATIVE PAINT STARTER ACTIVE: 22 VISIBLE BATCHES, 119 INSTANCES, "
        "6 OPEN TANKS, 1 ED BAKE OVEN, %s, WIP 0"),
        *ULBOneFactoryPaintStarterLayoutLibrary::GetColourDisplayName(
            Layout.SelectedBodyColour));
    return true;
}

int32 ALBOneFactoryPaintStarterPresentationActor::GetVisibleInstanceCount() const
{
    int32 Count = 0;
    for (const UHierarchicalInstancedStaticMeshComponent* Batch : GetAllBatches())
        Count += Batch ? Batch->GetInstanceCount() : 0;
    return Count;
}

int32 ALBOneFactoryPaintStarterPresentationActor::GetVisualBatchCount() const
{
    int32 Count = 0;
    for (const UHierarchicalInstancedStaticMeshComponent* Batch : GetAllBatches())
        if (Batch && Batch->GetInstanceCount() > 0) ++Count;
    return Count;
}

int32 ALBOneFactoryPaintStarterPresentationActor::GetInstanceCountForBatch(
    const ELBOneFactoryPaintPresentationBatch Batch) const
{
    const UHierarchicalInstancedStaticMeshComponent* Component =
        FindBatchComponent(Batch);
    return Component ? Component->GetInstanceCount() : 0;
}

int32 ALBOneFactoryPaintStarterPresentationActor::GetInstanceCountForRole(
    const ELBOneFactoryPaintStarterRole InRole) const
{
    int32 Count = 0;
    for (const FLBOneFactoryPaintPresentationItem& Item : ConfiguredItems)
        if (Item.Role == InRole) ++Count;
    return Count;
}

bool ALBOneFactoryPaintStarterPresentationActor::GetConfiguredStationTransform(
    const FName StationId, FTransform& OutWorldTransform) const
{
    const FTransform* Found = ConfiguredStationTransforms.Find(StationId);
    if (!bPresentationConfigured || !Found) return false;
    OutWorldTransform = *Found;
    return true;
}

TArray<FLBOneFactoryPaintPresentationItem>
ALBOneFactoryPaintStarterPresentationActor::GetConfiguredItemsForRole(
    const ELBOneFactoryPaintStarterRole InRole) const
{
    TArray<FLBOneFactoryPaintPresentationItem> Result;
    for (const FLBOneFactoryPaintPresentationItem& Item : ConfiguredItems)
        if (Item.Role == InRole) Result.Add(Item);
    return Result;
}

int32 ALBOneFactoryPaintStarterPresentationActor::GetExpectedVisualBatchCount()
{
    return LBOneFactoryPaintPresentationPrivate::ExpectedBatchCount;
}

int32 ALBOneFactoryPaintStarterPresentationActor::GetExpectedVisibleInstanceCount()
{
    return LBOneFactoryPaintPresentationPrivate::ExpectedInstanceCount;
}

int32 ALBOneFactoryPaintStarterPresentationActor::GetExpectedInstanceCountForBatch(
    const ELBOneFactoryPaintPresentationBatch Batch)
{
    switch (Batch)
    {
    case ELBOneFactoryPaintPresentationBatch::CuringOvenTunnel: return 1;
    case ELBOneFactoryPaintPresentationBatch::PretreatmentWashTunnel: return 0;
    case ELBOneFactoryPaintPresentationBatch::FlashOffTunnel: return 0;
    case ELBOneFactoryPaintPresentationBatch::QualityLightTunnel: return 1;
    case ELBOneFactoryPaintPresentationBatch::BodySkidCarrier: return 2;
    case ELBOneFactoryPaintPresentationBatch::PaintServiceSet: return 3;
    case ELBOneFactoryPaintPresentationBatch::AirExtractionModule: return 5;
    case ELBOneFactoryPaintPresentationBatch::BlackBoxSprayBooth: return 1;
    case ELBOneFactoryPaintPresentationBatch::FloorRouteCube: return 7;
    case ELBOneFactoryPaintPresentationBatch::StatusCube: return 8;
    case ELBOneFactoryPaintPresentationBatch::ProgrammeColourCube: return 1;
    case ELBOneFactoryPaintPresentationBatch::EDTreatmentStartModule: return 6;
    case ELBOneFactoryPaintPresentationBatch::EDTreatmentEndModule: return 6;
    case ELBOneFactoryPaintPresentationBatch::EDLiquidDegrease: return 1;
    case ELBOneFactoryPaintPresentationBatch::EDLiquidRinse1: return 1;
    case ELBOneFactoryPaintPresentationBatch::EDLiquidPhosphate: return 1;
    case ELBOneFactoryPaintPresentationBatch::EDLiquidRinse2: return 1;
    case ELBOneFactoryPaintPresentationBatch::EDLiquidEDCoat: return 1;
    case ELBOneFactoryPaintPresentationBatch::EDLiquidUFRinse: return 1;
    case ELBOneFactoryPaintPresentationBatch::EDProfiledRailCube: return 60;
    case ELBOneFactoryPaintPresentationBatch::EDImmersedBody: return 1;
    case ELBOneFactoryPaintPresentationBatch::EDDrainInspectionModule: return 1;
    // Four bays of the production oven, and one carrier gantry bay over
    // each of the six dip tanks.
    case ELBOneFactoryPaintPresentationBatch::EDOvenSegment: return 4;
    case ELBOneFactoryPaintPresentationBatch::EDCarrierGantryBay: return 6;
    default: return 0;
    }
}

int32 ALBOneFactoryPaintStarterPresentationActor::GetExpectedInstanceCountForRole(
    const ELBOneFactoryPaintStarterRole Role)
{
    switch (Role)
    {
    case ELBOneFactoryPaintStarterRole::BodySkidReceiving: return 3;
    case ELBOneFactoryPaintStarterRole::PretreatmentWash: return 60;
    case ELBOneFactoryPaintStarterRole::EDCoatLogicalProcess: return 33;
    case ELBOneFactoryPaintStarterRole::FlashOff: return 8;
    case ELBOneFactoryPaintStarterRole::BlackBoxSprayBooth: return 6;
    case ELBOneFactoryPaintStarterRole::CuringOven: return 4;
    case ELBOneFactoryPaintStarterRole::QualityLightInspection: return 3;
    case ELBOneFactoryPaintStarterRole::PaintedBodyDispatch: return 2;
    default: return 0;
    }
}

TArray<FSoftObjectPath>
ALBOneFactoryPaintStarterPresentationActor::GetRequiredNativeAssetPaths()
{
    using namespace LBOneFactoryPaintPresentationPrivate;
    return {
        FSoftObjectPath(CuringOvenPath),
        FSoftObjectPath(PretreatmentPath),
        FSoftObjectPath(FlashOffPath),
        FSoftObjectPath(QualityLightPath),
        FSoftObjectPath(BodySkidPath),
        FSoftObjectPath(ServiceSetPath),
        FSoftObjectPath(AirExtractionPath),
        FSoftObjectPath(SprayBoothPath),
        FSoftObjectPath(CubePath),
        FSoftObjectPath(BasicMaterialPath),
        FSoftObjectPath(EDTreatmentStartPath),
        FSoftObjectPath(EDTreatmentEndPath),
        FSoftObjectPath(EDDrainInspectionPath),
        FSoftObjectPath(EDOvenSegmentPath),
        FSoftObjectPath(EDCarrierGantryPath),
        FSoftObjectPath(EDTreatmentLiquidPath),
        FSoftObjectPath(EDImmersedBIWPath),
        FSoftObjectPath(EDLiquidMaterialPaths[0]),
        FSoftObjectPath(EDLiquidMaterialPaths[1]),
        FSoftObjectPath(EDLiquidMaterialPaths[2]),
        FSoftObjectPath(EDLiquidMaterialPaths[3]),
        FSoftObjectPath(EDLiquidMaterialPaths[4]),
        FSoftObjectPath(EDLiquidMaterialPaths[5]),
        FSoftObjectPath(EDImmersedBIWMaterialPath)
    };
}

bool ALBOneFactoryPaintStarterPresentationActor::
    ValidateNativePresentationReferences(
        const FString& PresentationClassPath,
        const TArray<FSoftObjectPath>& AssetPaths, FString& OutReason)
{
    using namespace LBOneFactoryPaintPresentationPrivate;
    const FLBOneFactoryPaintNativeOnlyProfile Profile =
        ULBOneFactoryPaintStarterLayoutLibrary::MakeNativeOnlyProfile();
    if (!ULBOneFactoryPaintStarterLayoutLibrary::ValidateNativeOnlyProfile(
            Profile, OutReason))
    {
        return false;
    }
    if (!PresentationClassPath.Equals(ExpectedPresentationClassPath,
            ESearchCase::CaseSensitive))
    {
        OutReason = TEXT("PAINT PRESENTATION CLASS DRIFTED FROM ITS EXACT CONTRACT");
        return false;
    }
    if (!ULBOneFactoryPaintStarterLayoutLibrary::ValidateNativeReference(
            Profile, PresentationClassPath, PresentationClassPath,
            ELBOneFactoryAssetProvenance::NativeCode, OutReason))
    {
        return false;
    }
    const TArray<FSoftObjectPath> Expected = GetRequiredNativeAssetPaths();
    static_assert(UE_ARRAY_COUNT(SupplementalEDAssetPaths)
        == SupplementalEDAssetCount);
    if (AssetPaths.Num() != Expected.Num()
        || Expected.Num() != NativeProfileAssetCount + SupplementalEDAssetCount
        || Profile.AllowedAssets.Num() != NativeProfileAssetCount)
    {
        OutReason = TEXT(
            "PAINT PRESENTATION REQUIRES EXACTLY 10 PROFILE AND 14 ED/BIW REFERENCES");
        return false;
    }
    TSet<FString> ExactIdentities;
    for (int32 Index = 0; Index < NativeProfileAssetCount; ++Index)
    {
        if (AssetPaths[Index].IsNull() || AssetPaths[Index] != Expected[Index]
            || Profile.AllowedAssets[Index].AssetPath != Expected[Index])
        {
            OutReason = TEXT("PAINT PRESENTATION EXACT ASSET LIST DRIFTED");
            return false;
        }
        if (!ULBOneFactoryPaintStarterLayoutLibrary::ValidateNativeReference(
                Profile, PresentationClassPath, AssetPaths[Index].ToString(),
                Profile.AllowedAssets[Index].Provenance, OutReason))
        {
            return false;
        }
        ExactIdentities.Add(AssetPaths[Index].ToString());
    }
    for (int32 Index = 0; Index < SupplementalEDAssetCount; ++Index)
    {
        const int32 AssetIndex = NativeProfileAssetCount + Index;
        const FSoftObjectPath ExactPath(SupplementalEDAssetPaths[Index]);
        const FString Reference = AssetPaths[AssetIndex].ToString();
        if (AssetPaths[AssetIndex].IsNull()
            || AssetPaths[AssetIndex] != Expected[AssetIndex]
            || AssetPaths[AssetIndex] != ExactPath
            || ExactIdentities.Contains(Reference))
        {
            OutReason = TEXT(
                "PAINT PRESENTATION EXACT ED ASSET CLOSURE DRIFTED OR DUPLICATED");
            return false;
        }
        if (!ULBOneFactoryLayoutLibrary::ValidateAssetProvenance(
                Profile.Policy, ELBOneFactoryAssetProvenance::NativeAuthored,
                Reference, OutReason))
        {
            return false;
        }
        ExactIdentities.Add(Reference);
    }
    OutReason = TEXT(
        "PAINT PRESENTATION CLASS, 10 PROFILE ASSETS, AND 15 ED/BIW ASSETS ARE EXACT");
    return true;
}

TArray<FLBOneFactoryPaintPresentationItem>
ALBOneFactoryPaintStarterPresentationActor::BuildExpectedPresentationItems(
    const FLBOneFactoryPaintStarterLayoutState& Layout)
{
    using namespace LBOneFactoryPaintPresentationPrivate;
    FString LayoutReason;
    if (!ULBOneFactoryPaintStarterLayoutLibrary::ValidateStarterLayout(
            Layout, LayoutReason))
    {
        return {};
    }
    const FLBOneFactoryPaintStarterStationState* Receiving =
        FindStation(Layout, ELBOneFactoryPaintStarterRole::BodySkidReceiving);
    const FLBOneFactoryPaintStarterStationState* Pretreatment =
        FindStation(Layout, ELBOneFactoryPaintStarterRole::PretreatmentWash);
    const FLBOneFactoryPaintStarterStationState* ED =
        FindStation(Layout, ELBOneFactoryPaintStarterRole::EDCoatLogicalProcess);
    const FLBOneFactoryPaintStarterStationState* Flash =
        FindStation(Layout, ELBOneFactoryPaintStarterRole::FlashOff);
    const FLBOneFactoryPaintStarterStationState* Spray =
        FindStation(Layout, ELBOneFactoryPaintStarterRole::BlackBoxSprayBooth);
    const FLBOneFactoryPaintStarterStationState* Oven =
        FindStation(Layout, ELBOneFactoryPaintStarterRole::CuringOven);
    const FLBOneFactoryPaintStarterStationState* Quality =
        FindStation(Layout, ELBOneFactoryPaintStarterRole::QualityLightInspection);
    const FLBOneFactoryPaintStarterStationState* Dispatch =
        FindStation(Layout, ELBOneFactoryPaintStarterRole::PaintedBodyDispatch);
    if (!Receiving || !Pretreatment || !ED || !Flash || !Spray || !Oven
        || !Quality || !Dispatch)
    {
        return {};
    }

    TArray<FLBOneFactoryPaintPresentationItem> Items;
    Items.Reserve(ExpectedInstanceCount);

    AddItem(Items, *Receiving, TEXT("BODY_SKID"),
        ELBOneFactoryPaintPresentationBatch::BodySkidCarrier);
    AddItem(Items, *Pretreatment, TEXT("SERVICE_SET"),
        ELBOneFactoryPaintPresentationBatch::PaintServiceSet,
        Offset(FVector(200.0f, -430.0f, 0.0f)));
    AddItem(Items, *Pretreatment, TEXT("AIR_EXTRACTION"),
        ELBOneFactoryPaintPresentationBatch::AirExtractionModule,
        Offset(FVector(-250.0f, 430.0f, 0.0f)));
    AddTreatmentTank(Items, *Pretreatment, 0, -486.0f,
        ELBOneFactoryPaintPresentationBatch::EDLiquidDegrease);
    AddTreatmentTank(Items, *Pretreatment, 1, -162.0f,
        ELBOneFactoryPaintPresentationBatch::EDLiquidRinse1);
    AddTreatmentTank(Items, *Pretreatment, 2, 162.0f,
        ELBOneFactoryPaintPresentationBatch::EDLiquidPhosphate);
    AddTreatmentTank(Items, *Pretreatment, 3, 486.0f,
        ELBOneFactoryPaintPresentationBatch::EDLiquidRinse2);

    AddItem(Items, *ED, TEXT("SERVICE_SET"),
        ELBOneFactoryPaintPresentationBatch::PaintServiceSet,
        Offset(FVector(270.0f, -350.0f, 0.0f)));
    AddItem(Items, *ED, TEXT("AIR_EXTRACTION"),
        ELBOneFactoryPaintPresentationBatch::AirExtractionModule,
        Offset(FVector(270.0f, 350.0f, 0.0f)));
    AddTreatmentTank(Items, *ED, 4, -162.0f,
        ELBOneFactoryPaintPresentationBatch::EDLiquidEDCoat);
    AddTreatmentTank(Items, *ED, 5, 162.0f,
        ELBOneFactoryPaintPresentationBatch::EDLiquidUFRinse);
    AddItem(Items, *ED, TEXT("TANK_05_IMMERSED_BODY"),
        ELBOneFactoryPaintPresentationBatch::EDImmersedBody,
        FTransform(FRotator::ZeroRotator,
            FVector(-162.0f, 0.0f, ImmersedBodyZCm),
            FVector(0.4f, 0.4f, 0.4f)));

    AddItem(Items, *Flash, TEXT("AIR_EXTRACTION"),
        ELBOneFactoryPaintPresentationBatch::AirExtractionModule,
        Offset(FVector(0.0f, 415.0f, 0.0f)));
    const FVector EDOvenScale(0.20f, 0.75f, 0.65f);
    AddItem(Items, *Flash, TEXT("ED_DRAIN_INSPECTION"),
        ELBOneFactoryPaintPresentationBatch::EDDrainInspectionModule,
        FTransform(FRotator::ZeroRotator, FVector(-360.0f, 0.0f, 0.0f),
            EDOvenScale));
    // The oven runs on from the tank row as one long enclosure: four
    // production bays butted end to end at the module's measured 355 cm
    // length, at authored scale.
    for (int32 Bay = 0; Bay < 4; ++Bay)
    {
        AddItem(Items, *Flash,
            FString::Printf(TEXT("ED_OVEN_BAY_%02d"), Bay + 1),
            ELBOneFactoryPaintPresentationBatch::EDOvenSegment,
            FTransform(FRotator::ZeroRotator,
                FVector(-180.0f + 355.0f * Bay, 0.0f, 0.0f),
                FVector::OneVector));
    }

    AddItem(Items, *Spray, TEXT("OPEN_END_BLACK_BOX_BOOTH"),
        ELBOneFactoryPaintPresentationBatch::BlackBoxSprayBooth);
    AddItem(Items, *Spray, TEXT("SERVICE_SET"),
        ELBOneFactoryPaintPresentationBatch::PaintServiceSet,
        Offset(FVector(0.0f, -390.0f, 0.0f)));
    AddItem(Items, *Spray, TEXT("AIR_EXTRACTION"),
        ELBOneFactoryPaintPresentationBatch::AirExtractionModule,
        Offset(FVector(0.0f, 390.0f, 0.0f)));
    AddItem(Items, *Spray, TEXT("SELECTED_COLOUR"),
        ELBOneFactoryPaintPresentationBatch::ProgrammeColourCube,
        CubeAt(FVector(600.0f, -500.0f, 90.0f),
            FVector(120.0f, 40.0f, 180.0f)));

    AddItem(Items, *Oven, TEXT("OPEN_END_CURING_TUNNEL"),
        ELBOneFactoryPaintPresentationBatch::CuringOvenTunnel);
    AddItem(Items, *Oven, TEXT("AIR_EXTRACTION"),
        ELBOneFactoryPaintPresentationBatch::AirExtractionModule,
        Offset(FVector(0.0f, 430.0f, 0.0f)));

    AddItem(Items, *Quality, TEXT("QUALITY_LIGHT_TUNNEL"),
        ELBOneFactoryPaintPresentationBatch::QualityLightTunnel);
    AddItem(Items, *Dispatch, TEXT("PAINTED_BODY_SKID"),
        ELBOneFactoryPaintPresentationBatch::BodySkidCarrier);

    for (const FLBOneFactoryPaintStarterStationState& Station : Layout.Stations)
        AddStatus(Items, Station);
    for (int32 Index = 0; Index < Layout.Connections.Num(); ++Index)
        AddRoute(Items, Layout.Stations[Index], Layout.Stations[Index + 1], Index);
    return Items;
}

bool ALBOneFactoryPaintStarterPresentationActor::ValidatePresentationContract(
    const FLBOneFactoryPaintStarterLayoutState& Layout,
    const TArray<FLBOneFactoryPaintPresentationItem>& Items,
    FString& OutReason)
{
    using namespace LBOneFactoryPaintPresentationPrivate;
    if (!ULBOneFactoryPaintStarterLayoutLibrary::ValidateStarterLayout(
            Layout, OutReason))
    {
        return false;
    }
    const TArray<FLBOneFactoryPaintPresentationItem> Expected =
        BuildExpectedPresentationItems(Layout);
    if (Expected.Num() != ExpectedInstanceCount
        || Items.Num() != ExpectedInstanceCount)
    {
        OutReason = TEXT("PAINT PRESENTATION REQUIRES EXACTLY 119 VISUAL ITEMS");
        return false;
    }

    TSet<FName> Identities;
    TMap<ELBOneFactoryPaintPresentationBatch, int32> BatchCounts;
    TMap<ELBOneFactoryPaintStarterRole, int32> RoleCounts;
    for (int32 Index = 0; Index < Items.Num(); ++Index)
    {
        const FLBOneFactoryPaintPresentationItem& Item = Items[Index];
        const FString Id = Item.PresentationId.ToString();
        if (Item.Version != 1 || Item.PresentationId.IsNone()
            || Item.StationId.IsNone() || !FindStation(Layout, Item.StationId)
            || Identities.Contains(Item.PresentationId)
            || !IsFiniteTransform(Item.WorldTransform)
            || Item.bClaimsHiddenProcessInternals
            || Item.bRepresentsProcessWIP
            || Id.Contains(TEXT("ROBOT"), ESearchCase::IgnoreCase)
            || Id.Contains(TEXT("WINDOW"), ESearchCase::IgnoreCase)
            || Id.Contains(TEXT("SIDE_DOOR"), ESearchCase::IgnoreCase)
            || Id.Contains(TEXT("INTERNAL"), ESearchCase::IgnoreCase)
            || !SameItem(Item, Expected[Index]))
        {
            OutReason = TEXT("PAINT PRESENTATION ITEM DRIFTED OR CLAIMS FORBIDDEN DETAIL/WIP");
            return false;
        }
        Identities.Add(Item.PresentationId);
        BatchCounts.FindOrAdd(Item.Batch) += 1;
        RoleCounts.FindOrAdd(Item.Role) += 1;
    }
    for (int32 Value = static_cast<int32>(
            ELBOneFactoryPaintPresentationBatch::CuringOvenTunnel);
        Value <= static_cast<int32>(
            ELBOneFactoryPaintPresentationBatch::EDCarrierGantryBay); ++Value)
    {
        const ELBOneFactoryPaintPresentationBatch Batch =
            static_cast<ELBOneFactoryPaintPresentationBatch>(Value);
        if (BatchCounts.FindRef(Batch) != GetExpectedInstanceCountForBatch(Batch))
        {
            OutReason = TEXT("PAINT PRESENTATION BATCH COUNTS DRIFTED");
            return false;
        }
    }
    for (int32 Value = static_cast<int32>(
            ELBOneFactoryPaintStarterRole::BodySkidReceiving);
        Value <= static_cast<int32>(
            ELBOneFactoryPaintStarterRole::PaintedBodyDispatch); ++Value)
    {
        const ELBOneFactoryPaintStarterRole Role =
            static_cast<ELBOneFactoryPaintStarterRole>(Value);
        if (RoleCounts.FindRef(Role) != GetExpectedInstanceCountForRole(Role))
        {
            OutReason = TEXT("PAINT PRESENTATION ROLE COUNTS DRIFTED");
            return false;
        }
    }
    OutReason = TEXT(
        "PAINT PRESENTATION VALID: 22 VISIBLE BATCHES, 119 ITEMS, 6 OPEN "
        "TANKS, 60 PROFILED RAILS, 1 ED BAKE OVEN, 1 SPRAY BOOTH, WIP 0");
    return true;
}

const TCHAR* ALBOneFactoryPaintStarterPresentationActor::GetPresentationClassPath()
{
    return LBOneFactoryPaintPresentationPrivate::ExpectedPresentationClassPath;
}

FName ALBOneFactoryPaintStarterPresentationActor::GetPresentationTag()
{
    return FName(TEXT("LB.OneFactory.PaintStarter.Presentation.v002"));
}
