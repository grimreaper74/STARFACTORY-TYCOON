#include "LBOneFactoryAssemblyStarterPresentationActor.h"

#include "Components/HierarchicalInstancedStaticMeshComponent.h"
#include "Components/SceneComponent.h"
#include "Engine/StaticMesh.h"
#include "Materials/MaterialInstanceDynamic.h"
#include "Materials/MaterialInterface.h"

namespace LBOneFactoryAssemblyPresentationPrivate
{
    constexpr int32 ExpectedBatchCount = 10;
    constexpr int32 ExpectedInstanceCount = 95;
    constexpr float TransformTolerance = 0.01f;

    const TCHAR* SkilletCarrierPath = TEXT(
        "/Game/LineBoss/Candidates/AssemblyShop/AssemblyLineNativeKit_v001/Logistics/SM_LB_Assembly_SkilletCarrier_v001.SM_LB_Assembly_SkilletCarrier_v001");
    const TCHAR* SequencedPartsCartPath = TEXT(
        "/Game/LineBoss/Candidates/AssemblyShop/AssemblyLineNativeKit_v001/Logistics/SM_LB_Assembly_SequencedPartsCart_v001.SM_LB_Assembly_SequencedPartsCart_v001");
    const TCHAR* WheelTireRackPath = TEXT(
        "/Game/LineBoss/Candidates/AssemblyShop/AssemblyLineNativeKit_v001/Logistics/SM_LB_Assembly_WheelTireRack_v001.SM_LB_Assembly_WheelTireRack_v001");
    const TCHAR* CockpitInstallAssistPath = TEXT(
        "/Game/LineBoss/Candidates/AssemblyShop/AssemblyLineNativeKit_v001/Robotics/SM_LB_Assembly_CockpitInstallAssist_v001.SM_LB_Assembly_CockpitInstallAssist_v001");
    const TCHAR* HeavyMarriageGantryPath = TEXT(
        "/Game/LineBoss/Candidates/AssemblyShop/AssemblyLineNativeKit_v001/Robotics/SM_LB_Assembly_HeavyMarriageGantry_v001.SM_LB_Assembly_HeavyMarriageGantry_v001");
    const TCHAR* ErgonomicLiftPlatformPath = TEXT(
        "/Game/LineBoss/Candidates/AssemblyShop/AssemblyLineNativeKit_v001/Stations/SM_LB_Assembly_ErgonomicLiftPlatform_v001.SM_LB_Assembly_ErgonomicLiftPlatform_v001");
    const TCHAR* WheelAlignmentBedPath = TEXT(
        "/Game/LineBoss/Candidates/AssemblyShop/AssemblyLineNativeKit_v001/Test/SM_LB_Assembly_WheelAlignmentBed_v001.SM_LB_Assembly_WheelAlignmentBed_v001");
    const TCHAR* EOLInspectionArchPath = TEXT(
        "/Game/LineBoss/Candidates/AssemblyShop/AssemblyLineNativeKit_v001/Test/SM_LB_Assembly_EOLInspectionArch_v001.SM_LB_Assembly_EOLInspectionArch_v001");
    const TCHAR* CubePath = TEXT("/Engine/BasicShapes/Cube.Cube");
    const TCHAR* BasicMaterialPath =
        TEXT("/Engine/BasicShapes/BasicShapeMaterial.BasicShapeMaterial");
    const TCHAR* ExpectedPresentationClassPath = TEXT(
        "/Script/LineBossCarFactory.LBOneFactoryAssemblyStarterPresentationActor");

    const FLBOneFactoryAssemblyStationState* FindStation(
        const FLBOneFactoryAssemblyLayoutState& Layout,
        const int32 LinePosition)
    {
        return Layout.Stations.FindByPredicate([LinePosition](
            const FLBOneFactoryAssemblyStationState& Station)
        {
            return Station.LinePosition == LinePosition;
        });
    }

    const FLBOneFactoryAssemblyStationState* FindStation(
        const FLBOneFactoryAssemblyLayoutState& Layout,
        const FName StationId)
    {
        return Layout.Stations.FindByPredicate([StationId](
            const FLBOneFactoryAssemblyStationState& Station)
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

    ELBOneFactoryAssemblyPresentationBatch BatchForOperation(
        const ELBOneFactoryAssemblyOperation Operation)
    {
        using B = ELBOneFactoryAssemblyPresentationBatch;
        using O = ELBOneFactoryAssemblyOperation;
        switch (Operation)
        {
        case O::PaintedBodyReceive:
        case O::MainWiringHarness:
        case O::HVACModule:
        case O::BatteryAndFuelSystem:
        case O::FluidsCharge:
        case O::FinishedVehicleDispatch:
            return B::SequencedPartsCart;
        case O::DoorOff:
        case O::InteriorTrim:
        case O::Closures:
        case O::UnderbodyTorque:
        case O::ExhaustAndThermal:
        case O::DoorRefit:
            return B::ErgonomicLiftPlatform;
        case O::InstrumentPanelCockpit:
        case O::Glazing:
        case O::Seats:
            return B::CockpitInstallAssist;
        case O::FrontRearCornerModules:
        case O::PowertrainPreparation:
        case O::PowertrainMarriage:
            return B::HeavyMarriageGantry;
        case O::WheelsAndTires:
            return B::WheelTireRack;
        case O::WheelAlignment:
        case O::BrakeRollDyno:
            return B::WheelAlignmentBed;
        case O::SoftwareFlash:
        case O::ElectricalFunctionalTest:
        case O::FinalInspectionAndRework:
            return B::EOLInspectionArch;
        default:
            return B::SequencedPartsCart;
        }
    }

    FString MakePresentationId(const FName StationId, const TCHAR* Suffix)
    {
        return FString::Printf(TEXT("OF_ASSEMBLY_VIS_%s_%s"),
            *StationId.ToString(), Suffix);
    }

    void AddItem(TArray<FLBOneFactoryAssemblyPresentationItem>& Items,
        const FName PresentationId, const FName StationId,
        const int32 LinePosition,
        const ELBOneFactoryAssemblyPresentationBatch Batch,
        const FTransform& WorldTransform,
        const bool bOperationFixture = false,
        const ELBOneFactoryAssemblyOperation Operation =
            ELBOneFactoryAssemblyOperation::PaintedBodyReceive)
    {
        FLBOneFactoryAssemblyPresentationItem& Item =
            Items.AddDefaulted_GetRef();
        Item.PresentationId = PresentationId;
        Item.StationId = StationId;
        Item.LinePosition = LinePosition;
        Item.Batch = Batch;
        Item.Operation = Operation;
        Item.bOperationFixture = bOperationFixture;
        Item.WorldTransform = WorldTransform;
        Item.bRepresentsProcessWIP = false;
    }

    bool SameItem(const FLBOneFactoryAssemblyPresentationItem& Left,
        const FLBOneFactoryAssemblyPresentationItem& Right)
    {
        return Left.Version == Right.Version
            && Left.PresentationId == Right.PresentationId
            && Left.StationId == Right.StationId
            && Left.LinePosition == Right.LinePosition
            && Left.Batch == Right.Batch
            && Left.Operation == Right.Operation
            && Left.bOperationFixture == Right.bOperationFixture
            && Left.WorldTransform.Equals(Right.WorldTransform,
                TransformTolerance)
            && Left.bRepresentsProcessWIP == Right.bRepresentsProcessWIP;
    }
}

ALBOneFactoryAssemblyStarterPresentationActor::
    ALBOneFactoryAssemblyStarterPresentationActor()
{
    PrimaryActorTick.bCanEverTick = false;
    SetReplicates(false);
    SetActorEnableCollision(false);

    SceneRoot = CreateDefaultSubobject<USceneComponent>(TEXT("SceneRoot"));
    SceneRoot->SetMobility(EComponentMobility::Movable);
    SetRootComponent(SceneRoot);

    SkilletCarrierBatch =
        CreateDefaultSubobject<UHierarchicalInstancedStaticMeshComponent>(
            TEXT("SkilletCarrierBatch"));
    SequencedPartsCartBatch =
        CreateDefaultSubobject<UHierarchicalInstancedStaticMeshComponent>(
            TEXT("SequencedPartsCartBatch"));
    WheelTireRackBatch =
        CreateDefaultSubobject<UHierarchicalInstancedStaticMeshComponent>(
            TEXT("WheelTireRackBatch"));
    CockpitInstallAssistBatch =
        CreateDefaultSubobject<UHierarchicalInstancedStaticMeshComponent>(
            TEXT("CockpitInstallAssistBatch"));
    HeavyMarriageGantryBatch =
        CreateDefaultSubobject<UHierarchicalInstancedStaticMeshComponent>(
            TEXT("HeavyMarriageGantryBatch"));
    ErgonomicLiftPlatformBatch =
        CreateDefaultSubobject<UHierarchicalInstancedStaticMeshComponent>(
            TEXT("ErgonomicLiftPlatformBatch"));
    WheelAlignmentBedBatch =
        CreateDefaultSubobject<UHierarchicalInstancedStaticMeshComponent>(
            TEXT("WheelAlignmentBedBatch"));
    EOLInspectionArchBatch =
        CreateDefaultSubobject<UHierarchicalInstancedStaticMeshComponent>(
            TEXT("EOLInspectionArchBatch"));
    FloorRouteCubeBatch =
        CreateDefaultSubobject<UHierarchicalInstancedStaticMeshComponent>(
            TEXT("FloorRouteCubeBatch"));
    StatusCubeBatch =
        CreateDefaultSubobject<UHierarchicalInstancedStaticMeshComponent>(
            TEXT("StatusCubeBatch"));

    for (UHierarchicalInstancedStaticMeshComponent* Batch : GetAllBatches())
    {
        if (!Batch) continue;
        Batch->SetupAttachment(SceneRoot);
        ConfigureVisualBatch(Batch);
    }
    FloorRouteCubeBatch->SetCastShadow(false);
    StatusCubeBatch->SetCastShadow(false);

    using namespace LBOneFactoryAssemblyPresentationPrivate;
    SkilletCarrierMesh = TSoftObjectPtr<UStaticMesh>(
        FSoftObjectPath(SkilletCarrierPath));
    SequencedPartsCartMesh = TSoftObjectPtr<UStaticMesh>(
        FSoftObjectPath(SequencedPartsCartPath));
    WheelTireRackMesh = TSoftObjectPtr<UStaticMesh>(
        FSoftObjectPath(WheelTireRackPath));
    CockpitInstallAssistMesh = TSoftObjectPtr<UStaticMesh>(
        FSoftObjectPath(CockpitInstallAssistPath));
    HeavyMarriageGantryMesh = TSoftObjectPtr<UStaticMesh>(
        FSoftObjectPath(HeavyMarriageGantryPath));
    ErgonomicLiftPlatformMesh = TSoftObjectPtr<UStaticMesh>(
        FSoftObjectPath(ErgonomicLiftPlatformPath));
    WheelAlignmentBedMesh = TSoftObjectPtr<UStaticMesh>(
        FSoftObjectPath(WheelAlignmentBedPath));
    EOLInspectionArchMesh = TSoftObjectPtr<UStaticMesh>(
        FSoftObjectPath(EOLInspectionArchPath));
    CubeMesh = TSoftObjectPtr<UStaticMesh>(FSoftObjectPath(CubePath));
    SemanticBaseMaterial = TSoftObjectPtr<UMaterialInterface>(
        FSoftObjectPath(BasicMaterialPath));

    Tags.AddUnique(GetPresentationTag());
    Tags.AddUnique(TEXT("LB.OneFactory.AssemblyStarter.NativeAuthored"));
    Tags.AddUnique(TEXT("LB.Environment.VisualOnly"));
    Tags.AddUnique(TEXT("LB.NotProcessWIP"));
    SetActorHiddenInGame(true);
}

void ALBOneFactoryAssemblyStarterPresentationActor::ConfigureVisualBatch(
    UHierarchicalInstancedStaticMeshComponent* Component)
{
    if (!Component) return;
    Component->SetMobility(EComponentMobility::Movable);
    Component->SetCollisionEnabled(ECollisionEnabled::NoCollision);
    Component->SetCollisionResponseToAllChannels(ECR_Ignore);
    Component->SetGenerateOverlapEvents(false);
    Component->SetCanEverAffectNavigation(false);
    Component->SetReceivesDecals(false);
}

TArray<UHierarchicalInstancedStaticMeshComponent*>
ALBOneFactoryAssemblyStarterPresentationActor::GetAllBatches() const
{
    return {
        SkilletCarrierBatch.Get(),
        SequencedPartsCartBatch.Get(),
        WheelTireRackBatch.Get(),
        CockpitInstallAssistBatch.Get(),
        HeavyMarriageGantryBatch.Get(),
        ErgonomicLiftPlatformBatch.Get(),
        WheelAlignmentBedBatch.Get(),
        EOLInspectionArchBatch.Get(),
        FloorRouteCubeBatch.Get(),
        StatusCubeBatch.Get()
    };
}

UHierarchicalInstancedStaticMeshComponent*
ALBOneFactoryAssemblyStarterPresentationActor::FindBatchComponent(
    const ELBOneFactoryAssemblyPresentationBatch Batch) const
{
    switch (Batch)
    {
    case ELBOneFactoryAssemblyPresentationBatch::SkilletCarrier:
        return SkilletCarrierBatch.Get();
    case ELBOneFactoryAssemblyPresentationBatch::SequencedPartsCart:
        return SequencedPartsCartBatch.Get();
    case ELBOneFactoryAssemblyPresentationBatch::WheelTireRack:
        return WheelTireRackBatch.Get();
    case ELBOneFactoryAssemblyPresentationBatch::CockpitInstallAssist:
        return CockpitInstallAssistBatch.Get();
    case ELBOneFactoryAssemblyPresentationBatch::HeavyMarriageGantry:
        return HeavyMarriageGantryBatch.Get();
    case ELBOneFactoryAssemblyPresentationBatch::ErgonomicLiftPlatform:
        return ErgonomicLiftPlatformBatch.Get();
    case ELBOneFactoryAssemblyPresentationBatch::WheelAlignmentBed:
        return WheelAlignmentBedBatch.Get();
    case ELBOneFactoryAssemblyPresentationBatch::EOLInspectionArch:
        return EOLInspectionArchBatch.Get();
    case ELBOneFactoryAssemblyPresentationBatch::FloorRouteCube:
        return FloorRouteCubeBatch.Get();
    case ELBOneFactoryAssemblyPresentationBatch::StatusCube:
        return StatusCubeBatch.Get();
    default:
        return nullptr;
    }
}

void ALBOneFactoryAssemblyStarterPresentationActor::ClearPresentation()
{
    for (UHierarchicalInstancedStaticMeshComponent* Batch : GetAllBatches())
    {
        if (!Batch) continue;
        Batch->ClearInstances();
        Batch->SetStaticMesh(nullptr);
    }
    if (FloorRouteCubeBatch) FloorRouteCubeBatch->SetMaterial(0, nullptr);
    if (StatusCubeBatch) StatusCubeBatch->SetMaterial(0, nullptr);
    SemanticMaterials.Reset();
    ConfiguredItems.Reset();
    ConfiguredStationTransforms.Reset();
    ConfiguredLayoutId = NAME_None;
    ConfiguredLayoutRevision = INDEX_NONE;
    bPresentationConfigured = false;
    SetActorHiddenInGame(true);
}

bool ALBOneFactoryAssemblyStarterPresentationActor::ConfigureFromLayout(
    const FLBOneFactoryAssemblyLayoutState& Layout, FString& OutReason)
{
    ClearPresentation();
    if (!ValidateNativePresentationReferences(GetPresentationClassPath(),
            GetRequiredNativeAssetPaths(), OutReason))
    {
        OutReason = FString::Printf(
            TEXT("ASSEMBLY PRESENTATION PROVENANCE FAILED: %s"), *OutReason);
        return false;
    }
    const TArray<FLBOneFactoryAssemblyPresentationItem> CandidateItems =
        BuildExpectedPresentationItems(Layout);
    if (!ValidatePresentationContract(Layout, CandidateItems, OutReason))
    {
        OutReason = FString::Printf(
            TEXT("ASSEMBLY PRESENTATION CONTRACT FAILED: %s"), *OutReason);
        return false;
    }

    UStaticMesh* ResolvedCube = CubeMesh.LoadSynchronous();
    TArray<UStaticMesh*> Meshes = {
        SkilletCarrierMesh.LoadSynchronous(),
        SequencedPartsCartMesh.LoadSynchronous(),
        WheelTireRackMesh.LoadSynchronous(),
        CockpitInstallAssistMesh.LoadSynchronous(),
        HeavyMarriageGantryMesh.LoadSynchronous(),
        ErgonomicLiftPlatformMesh.LoadSynchronous(),
        WheelAlignmentBedMesh.LoadSynchronous(),
        EOLInspectionArchMesh.LoadSynchronous(),
        ResolvedCube,
        ResolvedCube
    };
    UMaterialInterface* ResolvedMaterial = SemanticBaseMaterial.LoadSynchronous();
    const TArray<UHierarchicalInstancedStaticMeshComponent*> Batches =
        GetAllBatches();
    if (Meshes.Num() != GetExpectedVisualBatchCount()
        || Meshes.Contains(nullptr) || !ResolvedMaterial
        || Batches.Num() != GetExpectedVisualBatchCount()
        || Batches.Contains(nullptr))
    {
        OutReason = TEXT(
            "ASSEMBLY PRESENTATION COULD NOT RESOLVE ALL EIGHT AUTHORED MESHES AND TWO ENGINE BATCHES");
        ClearPresentation();
        return false;
    }
    for (int32 Index = 0; Index < Batches.Num(); ++Index)
        Batches[Index]->SetStaticMesh(Meshes[Index]);

    const FLinearColor RouteColour = FLinearColor::FromSRGBColor(
        FColor::FromHex(TEXT("D79F2B")));
    const FLinearColor StatusColour = FLinearColor::FromSRGBColor(
        FColor::FromHex(Layout.bCommissioned ? TEXT("39C980") : TEXT("E1B83F")));
    const FLinearColor SemanticColours[] = {RouteColour, StatusColour};
    UHierarchicalInstancedStaticMeshComponent* SemanticBatches[] = {
        FloorRouteCubeBatch.Get(), StatusCubeBatch.Get()};
    for (int32 Index = 0; Index < UE_ARRAY_COUNT(SemanticBatches); ++Index)
    {
        UMaterialInstanceDynamic* Material =
            UMaterialInstanceDynamic::Create(ResolvedMaterial, this);
        if (!Material)
        {
            OutReason = TEXT(
                "ASSEMBLY PRESENTATION COULD NOT CREATE ITS TWO SEMANTIC MATERIALS");
            ClearPresentation();
            return false;
        }
        Material->SetVectorParameterValue(TEXT("Color"), SemanticColours[Index]);
        Material->SetVectorParameterValue(TEXT("BaseColor"), SemanticColours[Index]);
        SemanticBatches[Index]->SetMaterial(0, Material);
        SemanticMaterials.Add(Material);
    }

    for (const FLBOneFactoryAssemblyPresentationItem& Item : CandidateItems)
    {
        UHierarchicalInstancedStaticMeshComponent* Batch =
            FindBatchComponent(Item.Batch);
        if (!Batch || Batch->AddInstance(Item.WorldTransform, true) == INDEX_NONE)
        {
            OutReason = FString::Printf(
                TEXT("ASSEMBLY PRESENTATION FAILED TO COMMIT %s"),
                *Item.PresentationId.ToString());
            ClearPresentation();
            return false;
        }
    }
    if (GetVisibleInstanceCount() != GetExpectedVisibleInstanceCount()
        || GetVisualBatchCount() != GetExpectedVisualBatchCount())
    {
        OutReason = TEXT(
            "ASSEMBLY PRESENTATION COMMIT DID NOT MATCH ITS EXACT BATCH/INSTANCE COUNTS");
        ClearPresentation();
        return false;
    }

    for (const FLBOneFactoryAssemblyStationState& Station : Layout.Stations)
        ConfiguredStationTransforms.Add(Station.StationId, Station.WorldTransform);
    ConfiguredItems = CandidateItems;
    ConfiguredLayoutId = Layout.LayoutId;
    ConfiguredLayoutRevision = Layout.Revision;
    bPresentationConfigured = true;
    SetActorHiddenInGame(false);
    OutReason = TEXT(
        "NATIVE ASSEMBLY PRESENTATION ACTIVE: 10 BATCHES, 95 INSTANCES, 24 POSITIONS, WIP 0");
    return true;
}

int32 ALBOneFactoryAssemblyStarterPresentationActor::
    GetVisibleInstanceCount() const
{
    int32 Count = 0;
    for (const UHierarchicalInstancedStaticMeshComponent* Batch : GetAllBatches())
        Count += Batch ? Batch->GetInstanceCount() : 0;
    return Count;
}

int32 ALBOneFactoryAssemblyStarterPresentationActor::GetVisualBatchCount() const
{
    int32 Count = 0;
    for (const UHierarchicalInstancedStaticMeshComponent* Batch : GetAllBatches())
    {
        if (Batch && Batch->GetInstanceCount() > 0) ++Count;
    }
    return Count;
}

int32 ALBOneFactoryAssemblyStarterPresentationActor::GetInstanceCountForBatch(
    const ELBOneFactoryAssemblyPresentationBatch Batch) const
{
    const UHierarchicalInstancedStaticMeshComponent* Component =
        FindBatchComponent(Batch);
    return Component ? Component->GetInstanceCount() : 0;
}

bool ALBOneFactoryAssemblyStarterPresentationActor::
    GetConfiguredStationTransform(
        const FName StationId, FTransform& OutWorldTransform) const
{
    const FTransform* Found = ConfiguredStationTransforms.Find(StationId);
    if (!bPresentationConfigured || !Found) return false;
    OutWorldTransform = *Found;
    return true;
}

TArray<FLBOneFactoryAssemblyPresentationItem>
ALBOneFactoryAssemblyStarterPresentationActor::GetConfiguredItemsForOperation(
    const ELBOneFactoryAssemblyOperation InOperation) const
{
    TArray<FLBOneFactoryAssemblyPresentationItem> Result;
    for (const FLBOneFactoryAssemblyPresentationItem& Item : ConfiguredItems)
    {
        if (Item.bOperationFixture && Item.Operation == InOperation)
            Result.Add(Item);
    }
    return Result;
}

int32 ALBOneFactoryAssemblyStarterPresentationActor::
    GetExpectedVisualBatchCount()
{
    return LBOneFactoryAssemblyPresentationPrivate::ExpectedBatchCount;
}

int32 ALBOneFactoryAssemblyStarterPresentationActor::
    GetExpectedVisibleInstanceCount()
{
    return LBOneFactoryAssemblyPresentationPrivate::ExpectedInstanceCount;
}

int32 ALBOneFactoryAssemblyStarterPresentationActor::
    GetExpectedInstanceCountForBatch(
        const ELBOneFactoryAssemblyPresentationBatch Batch)
{
    using B = ELBOneFactoryAssemblyPresentationBatch;
    switch (Batch)
    {
    case B::SkilletCarrier: return 24;
    case B::SequencedPartsCart: return 6;
    case B::WheelTireRack: return 1;
    case B::CockpitInstallAssist: return 3;
    case B::HeavyMarriageGantry: return 3;
    case B::ErgonomicLiftPlatform: return 6;
    case B::WheelAlignmentBed: return 2;
    case B::EOLInspectionArch: return 3;
    case B::FloorRouteCube: return 23;
    case B::StatusCube: return 24;
    default: return 0;
    }
}

TArray<FSoftObjectPath>
ALBOneFactoryAssemblyStarterPresentationActor::GetRequiredNativeAssetPaths()
{
    using namespace LBOneFactoryAssemblyPresentationPrivate;
    return {
        FSoftObjectPath(SkilletCarrierPath),
        FSoftObjectPath(SequencedPartsCartPath),
        FSoftObjectPath(WheelTireRackPath),
        FSoftObjectPath(CockpitInstallAssistPath),
        FSoftObjectPath(HeavyMarriageGantryPath),
        FSoftObjectPath(ErgonomicLiftPlatformPath),
        FSoftObjectPath(WheelAlignmentBedPath),
        FSoftObjectPath(EOLInspectionArchPath),
        FSoftObjectPath(CubePath),
        FSoftObjectPath(BasicMaterialPath)
    };
}

bool ALBOneFactoryAssemblyStarterPresentationActor::
    ValidateNativePresentationReferences(
        const FString& PresentationClassPath,
        const TArray<FSoftObjectPath>& AssetPaths, FString& OutReason)
{
    using namespace LBOneFactoryAssemblyPresentationPrivate;
    if (!PresentationClassPath.Equals(ExpectedPresentationClassPath,
            ESearchCase::CaseSensitive))
    {
        OutReason = TEXT(
            "ASSEMBLY PRESENTATION CLASS DRIFTED FROM ITS EXACT NATIVE CODE CONTRACT");
        return false;
    }
    if (!ULBOneFactoryLayoutLibrary::ValidateAssetProvenance(
            ELBOneFactoryProvenancePolicy::NativeOnly,
            ELBOneFactoryAssetProvenance::NativeCode,
            PresentationClassPath, OutReason))
    {
        return false;
    }

    const TArray<FSoftObjectPath> Expected = GetRequiredNativeAssetPaths();
    if (AssetPaths.Num() != Expected.Num())
    {
        OutReason = TEXT(
            "ASSEMBLY PRESENTATION REQUIRES EXACTLY EIGHT AUTHORED AND TWO ENGINE REFERENCES");
        return false;
    }
    // Generator-name tokens RETIRED 2026-08-24 (spacecraft-pivot ruling).
    static const TCHAR* ForbiddenTokens[] = {
        TEXT("/Downloads/"),
        TEXT("/Developer/Validation/")};
    const FString AuthoredRoot = TEXT(
        "/Game/LineBoss/Candidates/AssemblyShop/AssemblyLineNativeKit_v001/");
    for (int32 Index = 0; Index < Expected.Num(); ++Index)
    {
        if (AssetPaths[Index].IsNull() || AssetPaths[Index] != Expected[Index])
        {
            OutReason = TEXT(
                "ASSEMBLY PRESENTATION ASSET LIST OR ORDER DRIFTED FROM V001");
            return false;
        }
        const FString Reference = AssetPaths[Index].ToString();
        for (const TCHAR* Token : ForbiddenTokens)
        {
            if (Reference.Contains(Token, ESearchCase::IgnoreCase))
            {
                OutReason = TEXT(
                    "ASSEMBLY PRESENTATION REFERENCE CONTAINS A FORBIDDEN SOURCE TOKEN");
                return false;
            }
        }
        const bool bAuthored = Index < 8;
        if ((bAuthored && !Reference.StartsWith(AuthoredRoot,
                ESearchCase::CaseSensitive))
            || (!bAuthored && !Reference.StartsWith(
                TEXT("/Engine/BasicShapes/"), ESearchCase::CaseSensitive)))
        {
            OutReason = TEXT(
                "ASSEMBLY PRESENTATION REFERENCE LEFT ITS EXACT NATIVE ROOT");
            return false;
        }
        if (!ULBOneFactoryLayoutLibrary::ValidateAssetProvenance(
                ELBOneFactoryProvenancePolicy::NativeOnly,
                bAuthored ? ELBOneFactoryAssetProvenance::NativeAuthored
                    : ELBOneFactoryAssetProvenance::NativeProcedural,
                Reference, OutReason))
        {
            return false;
        }
    }
    OutReason = TEXT(
        "ASSEMBLY PRESENTATION CLASS, EIGHT AUTHORED MESHES AND TWO ENGINE REFERENCES ARE NATIVE-ONLY");
    return true;
}

TArray<FLBOneFactoryAssemblyPresentationItem>
ALBOneFactoryAssemblyStarterPresentationActor::BuildExpectedPresentationItems(
    const FLBOneFactoryAssemblyLayoutState& Layout)
{
    using namespace LBOneFactoryAssemblyPresentationPrivate;
    FString Reason;
    if (!ULBOneFactoryAssemblyStarterLayoutLibrary::ValidateStarterLayout(
            Layout, Reason))
    {
        return {};
    }

    TArray<FLBOneFactoryAssemblyPresentationItem> Items;
    Items.Reserve(ExpectedInstanceCount);
    for (int32 Position = 1;
        Position <= ULBOneFactoryAssemblyStarterLayoutLibrary::
            RequiredStationCount; ++Position)
    {
        const FLBOneFactoryAssemblyStationState* Station =
            FindStation(Layout, Position);
        if (!Station) return {};

        const float TravelYaw = Position <= 12 ? 0.0f : 180.0f;
        const FTransform DirectionFrame(FRotator(0.0f, TravelYaw, 0.0f),
            FVector::ZeroVector, FVector::OneVector);
        AddItem(Items,
            FName(*MakePresentationId(Station->StationId, TEXT("CARRIER"))),
            Station->StationId, Position,
            ELBOneFactoryAssemblyPresentationBatch::SkilletCarrier,
            DirectionFrame * Station->WorldTransform);

        TArray<ELBOneFactoryAssemblyOperation> Operations =
            Station->AssignedOperations;
        Operations.Sort([](const ELBOneFactoryAssemblyOperation Left,
            const ELBOneFactoryAssemblyOperation Right)
        {
            return static_cast<uint8>(Left) < static_cast<uint8>(Right);
        });
        for (int32 Index = 0; Index < Operations.Num(); ++Index)
        {
            const ELBOneFactoryAssemblyOperation Operation = Operations[Index];
            const float OffsetX =
                (static_cast<float>(Index)
                    - (static_cast<float>(Operations.Num()) - 1.0f) * 0.5f)
                * 450.0f;
            const FTransform FixtureLocal(FRotator::ZeroRotator,
                FVector(OffsetX, 700.0f, 0.0f), FVector::OneVector);
            AddItem(Items,
                FName(*FString::Printf(TEXT("OF_ASSEMBLY_VIS_%s_OP_%02d"),
                    *Station->StationId.ToString(),
                    static_cast<int32>(Operation) + 1)),
                Station->StationId, Position, BatchForOperation(Operation),
                FixtureLocal * DirectionFrame * Station->WorldTransform,
                true, Operation);
        }

        const FTransform StatusLocal(FRotator::ZeroRotator,
            FVector(700.0f, -1400.0f, 75.0f),
            FVector(0.5f, 0.5f, 1.5f));
        AddItem(Items,
            FName(*MakePresentationId(Station->StationId, TEXT("STATUS"))),
            Station->StationId, Position,
            ELBOneFactoryAssemblyPresentationBatch::StatusCube,
            StatusLocal * DirectionFrame * Station->WorldTransform);
    }

    for (const FLBOneFactoryAssemblyConnectionState& Connection :
        Layout.Connections)
    {
        const FLBOneFactoryAssemblyStationState* Source =
            FindStation(Layout, Connection.SourceStationId);
        const FLBOneFactoryAssemblyStationState* Target =
            FindStation(Layout, Connection.TargetStationId);
        if (!Source || !Target) return {};
        const FVector Start = Source->WorldTransform.GetLocation();
        const FVector End = Target->WorldTransform.GetLocation();
        const FVector Delta = End - Start;
        const float Length = Delta.Size2D();
        const float Yaw = FMath::RadiansToDegrees(
            FMath::Atan2(Delta.Y, Delta.X));
        const FTransform RouteTransform(FRotator(0.0f, Yaw, 0.0f),
            (Start + End) * 0.5f + FVector(0.0f, 0.0f, 4.0f),
            FVector(Length / 100.0f, 1.8f, 0.08f));
        AddItem(Items,
            FName(*FString::Printf(TEXT("OF_ASSEMBLY_VIS_%s"),
                *Connection.ConnectionId.ToString())),
            Target->StationId, Target->LinePosition,
            ELBOneFactoryAssemblyPresentationBatch::FloorRouteCube,
            RouteTransform);
    }
    return Items;
}

bool ALBOneFactoryAssemblyStarterPresentationActor::
    ValidatePresentationContract(
        const FLBOneFactoryAssemblyLayoutState& Layout,
        const TArray<FLBOneFactoryAssemblyPresentationItem>& Items,
        FString& OutReason)
{
    using namespace LBOneFactoryAssemblyPresentationPrivate;
    if (!ULBOneFactoryAssemblyStarterLayoutLibrary::ValidateStarterLayout(
            Layout, OutReason))
    {
        return false;
    }
    const TArray<FLBOneFactoryAssemblyPresentationItem> Expected =
        BuildExpectedPresentationItems(Layout);
    if (Expected.Num() != ExpectedInstanceCount
        || Items.Num() != ExpectedInstanceCount)
    {
        OutReason = TEXT(
            "ASSEMBLY PRESENTATION REQUIRES EXACTLY 95 VISUAL INSTANCES");
        return false;
    }

    TSet<FName> Identities;
    TSet<ELBOneFactoryAssemblyOperation> PresentedOperations;
    TMap<FName, int32> CarrierCounts;
    TMap<FName, int32> StatusCounts;
    TMap<ELBOneFactoryAssemblyPresentationBatch, int32> BatchCounts;
    for (int32 Index = 0; Index < Items.Num(); ++Index)
    {
        const FLBOneFactoryAssemblyPresentationItem& Item = Items[Index];
        const FLBOneFactoryAssemblyStationState* Station =
            FindStation(Layout, Item.StationId);
        if (Item.Version != 1 || Item.PresentationId.IsNone()
            || Item.StationId.IsNone() || !Station
            || Station->LinePosition != Item.LinePosition
            || Item.bRepresentsProcessWIP
            || !IsFiniteTransform(Item.WorldTransform))
        {
            OutReason = TEXT(
                "ASSEMBLY PRESENTATION HAS INVALID CORE DATA OR A WIP CLAIM");
            return false;
        }
        if (Identities.Contains(Item.PresentationId))
        {
            OutReason = TEXT(
                "ASSEMBLY PRESENTATION IDENTITIES MUST BE UNIQUE");
            return false;
        }
        Identities.Add(Item.PresentationId);
        BatchCounts.FindOrAdd(Item.Batch) += 1;
        if (!SameItem(Item, Expected[Index]))
        {
            OutReason = TEXT(
                "ASSEMBLY PRESENTATION INVENTORY OR TRANSFORM DRIFTED FROM V001");
            return false;
        }
        if (Item.Batch ==
            ELBOneFactoryAssemblyPresentationBatch::SkilletCarrier)
        {
            CarrierCounts.FindOrAdd(Item.StationId) += 1;
        }
        if (Item.Batch == ELBOneFactoryAssemblyPresentationBatch::StatusCube)
        {
            StatusCounts.FindOrAdd(Item.StationId) += 1;
        }
        if (Item.bOperationFixture)
        {
            if (!Station->AssignedOperations.Contains(Item.Operation)
                || PresentedOperations.Contains(Item.Operation)
                || Item.Batch != BatchForOperation(Item.Operation))
            {
                OutReason = TEXT(
                    "ASSEMBLY OPERATION FIXTURE IS DUPLICATED, MISASSIGNED OR USES THE WRONG ASSET");
                return false;
            }
            PresentedOperations.Add(Item.Operation);
        }
    }
    if (Identities.Num() != ExpectedInstanceCount
        || PresentedOperations.Num()
            != ULBOneFactoryAssemblyStarterLayoutLibrary::RequiredOperationCount
        || CarrierCounts.Num()
            != ULBOneFactoryAssemblyStarterLayoutLibrary::RequiredStationCount
        || StatusCounts.Num()
            != ULBOneFactoryAssemblyStarterLayoutLibrary::RequiredStationCount)
    {
        OutReason = TEXT(
            "ASSEMBLY PRESENTATION LOST A POSITION, OPERATION OR STABLE ID");
        return false;
    }
    for (const FLBOneFactoryAssemblyStationState& Station : Layout.Stations)
    {
        if (CarrierCounts.FindRef(Station.StationId) != 1
            || StatusCounts.FindRef(Station.StationId) != 1)
        {
            OutReason = TEXT(
                "EVERY ASSEMBLY POSITION REQUIRES ONE CARRIER AND ONE STATUS MARKER");
            return false;
        }
    }
    for (int32 Value = static_cast<int32>(
            ELBOneFactoryAssemblyPresentationBatch::SkilletCarrier);
        Value <= static_cast<int32>(
            ELBOneFactoryAssemblyPresentationBatch::StatusCube); ++Value)
    {
        const ELBOneFactoryAssemblyPresentationBatch Batch =
            static_cast<ELBOneFactoryAssemblyPresentationBatch>(Value);
        if (BatchCounts.FindRef(Batch) !=
            GetExpectedInstanceCountForBatch(Batch))
        {
            OutReason = TEXT(
                "ASSEMBLY PRESENTATION BATCH COUNTS DRIFTED FROM V001");
            return false;
        }
    }
    OutReason = TEXT(
        "ASSEMBLY PRESENTATION CONTRACT VALID: 10 BATCHES, 95 INSTANCES, 24 POSITIONS, 23 ROUTES, WIP 0");
    return true;
}

const TCHAR* ALBOneFactoryAssemblyStarterPresentationActor::
    GetPresentationClassPath()
{
    return LBOneFactoryAssemblyPresentationPrivate::
        ExpectedPresentationClassPath;
}

FName ALBOneFactoryAssemblyStarterPresentationActor::GetPresentationTag()
{
    return TEXT("LB.OneFactory.AssemblyStarter.Presentation.v001");
}
