#include "LBFactoryEnvelopeSideDressingActor.h"

#include "Components/HierarchicalInstancedStaticMeshComponent.h"
#include "Components/SceneComponent.h"
#include "Engine/StaticMesh.h"
#include "Materials/MaterialInterface.h"

namespace LBFactoryEnvelopeSidesPrivate
{
    constexpr float WallY = 5810.0f;
    constexpr float ColumnHeightCm = 500.0f;
    constexpr float BaySpacingCm = 2000.0f;
    constexpr int32 BayCount = 10;
    constexpr float FirstBayX = -9000.0f;

    const TCHAR* ColumnPath =
        TEXT("/Game/LineBoss/Vendor/FactoryEnvironment/Meshes/SM_Column_02.SM_Column_02");
    const TCHAR* BeamPath =
        TEXT("/Game/LineBoss/Vendor/FactoryEnvironment/Meshes/SM_MetalBeam01.SM_MetalBeam01");
    const TCHAR* ServiceCabinetPath =
        TEXT("/Game/LineBoss/IndustrialKit/PressShop/FrontEndDressing/SM_LB_ServiceCabinet_1800_v001.SM_LB_ServiceCabinet_1800_v001");
    const TCHAR* ExteriorApronMeshPath = TEXT("/Engine/BasicShapes/Cube.Cube");
    const TCHAR* ExteriorApronMaterialPath =
        TEXT("/Game/LineBoss/Materials/Environment/MI_LB_SealedFactoryConcrete_Neutral_v001.MI_LB_SealedFactoryConcrete_Neutral_v001");

    FTransform MakeTransform(const FVector& Location, const FRotator& Rotation = FRotator::ZeroRotator,
        const FVector& Scale = FVector::OneVector)
    {
        return FTransform(Rotation, Location, Scale);
    }
}

ALBFactoryEnvelopeSideDressingActor::ALBFactoryEnvelopeSideDressingActor()
{
    PrimaryActorTick.bCanEverTick = false;

    SceneRoot = CreateDefaultSubobject<USceneComponent>(TEXT("SceneRoot"));
    SetRootComponent(SceneRoot);

    ColumnInstances = CreateDefaultSubobject<UHierarchicalInstancedStaticMeshComponent>(TEXT("ColumnInstances"));
    ColumnInstances->SetupAttachment(SceneRoot);
    BeamInstances = CreateDefaultSubobject<UHierarchicalInstancedStaticMeshComponent>(TEXT("BeamInstances"));
    BeamInstances->SetupAttachment(SceneRoot);
    ServiceCabinetInstances = CreateDefaultSubobject<UHierarchicalInstancedStaticMeshComponent>(TEXT("ServiceCabinetInstances"));
    ServiceCabinetInstances->SetupAttachment(SceneRoot);
    ExteriorApronInstances = CreateDefaultSubobject<UHierarchicalInstancedStaticMeshComponent>(TEXT("ExteriorApronInstances"));
    ExteriorApronInstances->SetupAttachment(SceneRoot);
    ConfigureVisualInstances(ColumnInstances);
    ConfigureVisualInstances(BeamInstances);
    ConfigureVisualInstances(ServiceCabinetInstances);
    ConfigureVisualInstances(ExteriorApronInstances);

    ColumnMesh = TSoftObjectPtr<UStaticMesh>(FSoftObjectPath(LBFactoryEnvelopeSidesPrivate::ColumnPath));
    BeamMesh = TSoftObjectPtr<UStaticMesh>(FSoftObjectPath(LBFactoryEnvelopeSidesPrivate::BeamPath));
    ServiceCabinetMesh = TSoftObjectPtr<UStaticMesh>(FSoftObjectPath(LBFactoryEnvelopeSidesPrivate::ServiceCabinetPath));
    ExteriorApronMesh = TSoftObjectPtr<UStaticMesh>(FSoftObjectPath(LBFactoryEnvelopeSidesPrivate::ExteriorApronMeshPath));

    Tags.AddUnique(TEXT("LB.FactoryEnvelope.SideDressing.v001"));
    Tags.AddUnique(TEXT("LB.Environment.VisualOnly"));
}

void ALBFactoryEnvelopeSideDressingActor::ConfigureVisualInstances(
    UHierarchicalInstancedStaticMeshComponent* Component) const
{
    if (!Component) return;
    Component->SetMobility(EComponentMobility::Movable);
    Component->SetCollisionEnabled(ECollisionEnabled::NoCollision);
    Component->SetCollisionResponseToAllChannels(ECR_Ignore);
    Component->SetGenerateOverlapEvents(false);
    Component->SetCanEverAffectNavigation(false);
    // The real envelope lights provide the scene lighting. These are visual rhythm only and
    // must not cast a second set of large wall/floor shadows across the management overview.
    Component->SetCastShadow(false);
}

void ALBFactoryEnvelopeSideDressingActor::ClearPresentation()
{
    ColumnInstances->ClearInstances();
    BeamInstances->ClearInstances();
    ServiceCabinetInstances->ClearInstances();
    ExteriorApronInstances->ClearInstances();
    bPresentationActive = false;
}

bool ALBFactoryEnvelopeSideDressingActor::ActivatePresentation()
{
    if (bPresentationActive) return true;

    UStaticMesh* Column = ColumnMesh.LoadSynchronous();
    UStaticMesh* Beam = BeamMesh.LoadSynchronous();
    UStaticMesh* Cabinet = ServiceCabinetMesh.LoadSynchronous();
    UStaticMesh* ApronMesh = ExteriorApronMesh.LoadSynchronous();
    UMaterialInterface* ApronMaterial = LoadObject<UMaterialInterface>(nullptr,
        LBFactoryEnvelopeSidesPrivate::ExteriorApronMaterialPath);
    if (!Column || !Beam || !Cabinet || !ApronMesh || !ApronMaterial)
    {
        ClearPresentation();
        UE_LOG(LogTemp, Warning,
            TEXT("LINE_BOSS_FACTORY_ENVELOPE_SIDES_FALLBACK column=%d beam=%d cabinet=%d apron=%d material=%d"),
            Column ? 1 : 0, Beam ? 1 : 0, Cabinet ? 1 : 0, ApronMesh ? 1 : 0,
            ApronMaterial ? 1 : 0);
        return false;
    }

    ColumnInstances->SetStaticMesh(Column);
    BeamInstances->SetStaticMesh(Beam);
    ServiceCabinetInstances->SetStaticMesh(Cabinet);
    ExteriorApronInstances->SetStaticMesh(ApronMesh);
    ExteriorApronInstances->SetMaterial(0, ApronMaterial);

    // The overhead management camera deliberately hides the roof. Give that view one coherent
    // exterior ground plane rather than an infinite black background or four visually detached
    // strips. It is visual context only: it cannot block placement, navigation or AGV routes.
    constexpr float SiteHalfX = 18000.0f;
    constexpr float SiteHalfY = 13000.0f;
    constexpr float ApronThickness = 2.0f;
    ExteriorApronInstances->AddInstance(LBFactoryEnvelopeSidesPrivate::MakeTransform(
        FVector(0.0f, 0.0f, -ApronThickness), FRotator::ZeroRotator,
        FVector(SiteHalfX / 50.0f, SiteHalfY / 50.0f, ApronThickness / 100.0f)));

    // Every 20 m bay gets a three-storey column and two horizontal service rails on both
    // long walls. The project assets remain at authored proportions; only beam length is
    // extended along its native 6 m longitudinal axis to span one 20 m bay.
    for (int32 BayIndex = 0; BayIndex < LBFactoryEnvelopeSidesPrivate::BayCount; ++BayIndex)
    {
        const float X = LBFactoryEnvelopeSidesPrivate::FirstBayX
            + static_cast<float>(BayIndex) * LBFactoryEnvelopeSidesPrivate::BaySpacingCm;
        for (const float Side : {-1.0f, 1.0f})
        {
            const float Y = Side * LBFactoryEnvelopeSidesPrivate::WallY;
            for (int32 Level = 0; Level < 3; ++Level)
            {
                const float Z = (static_cast<float>(Level) + 0.5f)
                    * LBFactoryEnvelopeSidesPrivate::ColumnHeightCm;
                ColumnInstances->AddInstance(LBFactoryEnvelopeSidesPrivate::MakeTransform(
                    FVector(X, Y, Z), FRotator::ZeroRotator));
            }
            BeamInstances->AddInstance(LBFactoryEnvelopeSidesPrivate::MakeTransform(
                FVector(X, Y, 545.0f), FRotator::ZeroRotator, FVector(3.333333f, 1.0f, 1.0f)));
            BeamInstances->AddInstance(LBFactoryEnvelopeSidesPrivate::MakeTransform(
                FVector(X, Y, 1100.0f), FRotator::ZeroRotator, FVector(3.333333f, 1.0f, 1.0f)));

            // Sparse, repeated cabinet nodes give the large hall a believable service rhythm
            // without filling its floor or pretending to be a player-built production asset.
            if (BayIndex == 1 || BayIndex == 5 || BayIndex == 8)
            {
                const FRotator FacingFactory(0.0f, Side > 0.0f ? 180.0f : 0.0f, 0.0f);
                ServiceCabinetInstances->AddInstance(LBFactoryEnvelopeSidesPrivate::MakeTransform(
                    FVector(X + 420.0f, Side * 5725.0f, 90.5f), FacingFactory));
            }
        }
    }

    bPresentationActive = true;
    UE_LOG(LogTemp, Display,
        TEXT("LINE_BOSS_FACTORY_ENVELOPE_SIDES_ACTIVE columns=%d beams=%d cabinets=%d apron=%d"),
        GetColumnInstanceCount(), GetBeamInstanceCount(), GetServiceCabinetInstanceCount(),
        GetExteriorApronInstanceCount());
    return true;
}

int32 ALBFactoryEnvelopeSideDressingActor::GetColumnInstanceCount() const
{
    return ColumnInstances ? ColumnInstances->GetInstanceCount() : 0;
}

int32 ALBFactoryEnvelopeSideDressingActor::GetBeamInstanceCount() const
{
    return BeamInstances ? BeamInstances->GetInstanceCount() : 0;
}

int32 ALBFactoryEnvelopeSideDressingActor::GetServiceCabinetInstanceCount() const
{
    return ServiceCabinetInstances ? ServiceCabinetInstances->GetInstanceCount() : 0;
}

int32 ALBFactoryEnvelopeSideDressingActor::GetExteriorApronInstanceCount() const
{
    return ExteriorApronInstances ? ExteriorApronInstances->GetInstanceCount() : 0;
}

TArray<FSoftObjectPath> ALBFactoryEnvelopeSideDressingActor::GetRuntimeAssetPaths() const
{
    return {ColumnMesh.ToSoftObjectPath(), BeamMesh.ToSoftObjectPath(),
        ServiceCabinetMesh.ToSoftObjectPath(), ExteriorApronMesh.ToSoftObjectPath()};
}
