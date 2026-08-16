#include "LBFactoryEnvelopeShutterActor.h"

#include "Components/BoxComponent.h"
#include "Components/SceneComponent.h"
#include "Components/StaticMeshComponent.h"
#include "Engine/StaticMesh.h"
#include "Engine/StaticMeshActor.h"
#include "EngineUtils.h"
#include "Materials/MaterialInterface.h"

namespace LBFactoryEnvelopeShutterPrivate
{
    constexpr float LeafTravelCm = 460.0f;
    constexpr float ExactClosedTolerance = KINDA_SMALL_NUMBER;

    const FName CleanShellAuthorityTag(TEXT("LB.CleanShell.v20260809.v001"));
    const FName NewAuthoredTag(TEXT("LB.Asset.NewAuthored"));
    const FName EnvironmentWallTag(TEXT("LB.Environment.Wall"));

    const TCHAR* StaticWallPath =
        TEXT("/Game/LineBoss/Candidates/Architecture/FactoryEnvelopeKitRuntime_v001/Meshes/Shutter/SM_LB_ShutterBay_StaticWall_v001.SM_LB_ShutterBay_StaticWall_v001");
    const TCHAR* FramePath =
        TEXT("/Game/LineBoss/Candidates/Architecture/FactoryEnvelopeKitRuntime_v001/Meshes/Shutter/SM_LB_ShutterBay_Frame_v001.SM_LB_ShutterBay_Frame_v001");
    const TCHAR* LeafPath =
        TEXT("/Game/LineBoss/Candidates/Architecture/FactoryEnvelopeKitRuntime_v001/Meshes/Shutter/SM_LB_ShutterLeaf_v001.SM_LB_ShutterLeaf_v001");
    const TCHAR* WarmWallMaterialPath =
        TEXT("/Game/LineBoss/Candidates/Architecture/FactoryEnvelopeKitRuntime_v001/Materials/MI_LB_Architecture_WarmOffWhite_v001.MI_LB_Architecture_WarmOffWhite_v001");
    const TCHAR* GraphiteMaterialPath =
        TEXT("/Game/LineBoss/Candidates/Architecture/FactoryEnvelopeKitRuntime_v001/Materials/MI_LB_Architecture_Graphite_v001.MI_LB_Architecture_Graphite_v001");
    const TCHAR* CubePath = TEXT("/Engine/BasicShapes/Cube.Cube");

    void ConfigureStructuralComponent(UStaticMeshComponent* Component)
    {
        if (!Component) return;
        Component->SetMobility(EComponentMobility::Movable);
        Component->SetCollisionEnabled(ECollisionEnabled::QueryAndPhysics);
        Component->SetCollisionObjectType(ECC_WorldStatic);
        Component->SetCollisionResponseToAllChannels(ECR_Block);
        Component->SetGenerateOverlapEvents(false);
        Component->SetCanEverAffectNavigation(true);
        Component->SetCastShadow(true);
    }

    void ConfigureVisualComponent(UStaticMeshComponent* Component)
    {
        if (!Component) return;
        Component->SetMobility(EComponentMobility::Movable);
        Component->SetCollisionEnabled(ECollisionEnabled::NoCollision);
        Component->SetCollisionResponseToAllChannels(ECR_Ignore);
        Component->SetGenerateOverlapEvents(false);
        Component->SetCanEverAffectNavigation(false);
        Component->SetCastShadow(true);
    }
}

ALBFactoryEnvelopeShutterActor::ALBFactoryEnvelopeShutterActor()
{
    PrimaryActorTick.bCanEverTick = false;

    SceneRoot = CreateDefaultSubobject<USceneComponent>(TEXT("SceneRoot"));
    SceneRoot->SetMobility(EComponentMobility::Movable);
    SetRootComponent(SceneRoot);

    StaticWallPresentation = CreateDefaultSubobject<UStaticMeshComponent>(
        TEXT("StaticWallPresentation"));
    StaticWallPresentation->SetupAttachment(SceneRoot);
    LBFactoryEnvelopeShutterPrivate::ConfigureStructuralComponent(StaticWallPresentation);

    FramePresentation = CreateDefaultSubobject<UStaticMeshComponent>(TEXT("FramePresentation"));
    FramePresentation->SetupAttachment(SceneRoot);
    LBFactoryEnvelopeShutterPrivate::ConfigureVisualComponent(FramePresentation);

    LeafMotionRoot = CreateDefaultSubobject<USceneComponent>(TEXT("LeafMotionRoot"));
    LeafMotionRoot->SetupAttachment(SceneRoot);
    LeafMotionRoot->SetMobility(EComponentMobility::Movable);
    LeafMotionRoot->SetRelativeLocation(GetClosedLeafRelativeLocation());

    LeafPresentation = CreateDefaultSubobject<UStaticMeshComponent>(TEXT("LeafPresentation"));
    LeafPresentation->SetupAttachment(LeafMotionRoot);
    LBFactoryEnvelopeShutterPrivate::ConfigureVisualComponent(LeafPresentation);

    LeafBarrier = CreateDefaultSubobject<UBoxComponent>(TEXT("LeafBarrier"));
    LeafBarrier->SetupAttachment(LeafMotionRoot);
    LeafBarrier->SetMobility(EComponentMobility::Movable);
    // The imported leaf is authored below its top-centre root.
    LeafBarrier->SetRelativeLocation(FVector(0.0f, 0.6f, -230.0f));
    LeafBarrier->SetBoxExtent(FVector(217.5f, 3.75f, 230.0f));
    LeafBarrier->SetCollisionObjectType(ECC_WorldDynamic);
    LeafBarrier->SetCollisionResponseToAllChannels(ECR_Block);
    LeafBarrier->SetGenerateOverlapEvents(false);
    LeafBarrier->SetCanEverAffectNavigation(false);
    LeafBarrier->SetHiddenInGame(true);

    // After yaw -90, actor-local X runs along the west wall's world Y axis.
    CreateInfillComponent(TEXT("SouthPlinthInfill"), FVector(2653.25f, 0.0f, 75.0f),
        FVector(4498.5f, 24.0f, 150.0f), true);
    CreateInfillComponent(TEXT("SouthUpperWallInfill"), FVector(2653.25f, 0.0f, 900.0f),
        FVector(4498.5f, 24.0f, 1500.0f), false);
    CreateInfillComponent(TEXT("NorthPlinthInfill"), FVector(-3750.75f, 0.0f, 75.0f),
        FVector(6693.5f, 24.0f, 150.0f), true);
    CreateInfillComponent(TEXT("NorthUpperWallInfill"), FVector(-3750.75f, 0.0f, 900.0f),
        FVector(6693.5f, 24.0f, 1500.0f), false);
    CreateInfillComponent(TEXT("OverBayWallInfill"), FVector(0.0f, 0.0f, 1125.0f),
        FVector(808.0f, 24.0f, 1050.0f), false);

    StaticWallMesh = TSoftObjectPtr<UStaticMesh>(
        FSoftObjectPath(LBFactoryEnvelopeShutterPrivate::StaticWallPath));
    FrameMesh = TSoftObjectPtr<UStaticMesh>(
        FSoftObjectPath(LBFactoryEnvelopeShutterPrivate::FramePath));
    LeafMesh = TSoftObjectPtr<UStaticMesh>(
        FSoftObjectPath(LBFactoryEnvelopeShutterPrivate::LeafPath));
    InfillCubeMesh = TSoftObjectPtr<UStaticMesh>(
        FSoftObjectPath(LBFactoryEnvelopeShutterPrivate::CubePath));
    WarmWallMaterial = TSoftObjectPtr<UMaterialInterface>(
        FSoftObjectPath(LBFactoryEnvelopeShutterPrivate::WarmWallMaterialPath));
    GraphiteMaterial = TSoftObjectPtr<UMaterialInterface>(
        FSoftObjectPath(LBFactoryEnvelopeShutterPrivate::GraphiteMaterialPath));

    Tags.AddUnique(TEXT("LB.FactoryEnvelope.Shutter.v001"));
    Tags.AddUnique(TEXT("LB.Environment.Wall.RuntimeReplacement"));
    SetReplacementPresentationEnabled(false);
}

FTransform ALBFactoryEnvelopeShutterActor::GetAuthoredWorldTransform()
{
    return FTransform(FRotator(0.0f, -90.0f, 0.0f),
        FVector(-11000.0f, -1097.5f, 0.0f), FVector::OneVector);
}

FVector ALBFactoryEnvelopeShutterActor::GetClosedLeafRelativeLocation()
{
    return FVector(-97.5f, -14.5f, 460.0f);
}

FBox ALBFactoryEnvelopeShutterActor::GetAuthoredClearOpeningWorldBounds()
{
    // X spans the authored 24 cm wall plane; Y/Z are the exact 4.35 x 4.60 m aperture.
    return FBox(FVector(-11012.0f, -1217.5f, 0.0f),
        FVector(-10988.0f, -782.5f, 460.0f));
}

UStaticMeshComponent* ALBFactoryEnvelopeShutterActor::CreateInfillComponent(
    const TCHAR* Name, const FVector& RelativeLocation, const FVector& DimensionsCm,
    const bool bUseGraphiteMaterial)
{
    UStaticMeshComponent* Component = CreateDefaultSubobject<UStaticMeshComponent>(Name);
    Component->SetupAttachment(SceneRoot);
    Component->SetRelativeLocation(RelativeLocation);
    Component->SetRelativeScale3D(DimensionsCm / 100.0f);
    Component->ComponentTags.Add(bUseGraphiteMaterial
        ? TEXT("LB.FactoryEnvelope.Material.Graphite")
        : TEXT("LB.FactoryEnvelope.Material.WarmWall"));
    LBFactoryEnvelopeShutterPrivate::ConfigureStructuralComponent(Component);
    ReplacementInfill.Add(Component);
    return Component;
}

void ALBFactoryEnvelopeShutterActor::SetReplacementPresentationEnabled(const bool bEnabled)
{
    StaticWallPresentation->SetVisibility(bEnabled, true);
    FramePresentation->SetVisibility(bEnabled, true);
    LeafPresentation->SetVisibility(bEnabled, true);
    StaticWallPresentation->SetCollisionEnabled(bEnabled
        ? ECollisionEnabled::QueryAndPhysics : ECollisionEnabled::NoCollision);
    StaticWallPresentation->SetCanEverAffectNavigation(bEnabled);
    for (UStaticMeshComponent* Infill : ReplacementInfill)
    {
        if (!Infill) continue;
        Infill->SetVisibility(bEnabled, true);
        Infill->SetCollisionEnabled(bEnabled
            ? ECollisionEnabled::QueryAndPhysics : ECollisionEnabled::NoCollision);
        Infill->SetCanEverAffectNavigation(bEnabled);
    }
    LeafBarrier->SetCollisionEnabled(bEnabled
        && ShutterOpenFraction <= LBFactoryEnvelopeShutterPrivate::ExactClosedTolerance
            ? ECollisionEnabled::QueryOnly : ECollisionEnabled::NoCollision);
    SetActorHiddenInGame(!bEnabled);
}

bool ALBFactoryEnvelopeShutterActor::IsDurableCleanShellWestWall(
    const AStaticMeshActor& Candidate) const
{
    if (!Candidate.ActorHasTag(LBFactoryEnvelopeShutterPrivate::CleanShellAuthorityTag)
        || !Candidate.ActorHasTag(LBFactoryEnvelopeShutterPrivate::NewAuthoredTag)
        || !Candidate.ActorHasTag(LBFactoryEnvelopeShutterPrivate::EnvironmentWallTag))
    {
        return false;
    }

    const UStaticMeshComponent* Component = Candidate.GetStaticMeshComponent();
    const UStaticMesh* Mesh = Component ? Component->GetStaticMesh() : nullptr;
    if (!Component || !Mesh || Mesh->GetPathName() != TEXT("/Engine/BasicShapes/Cube.Cube"))
    {
        return false;
    }

    // Do not depend on editor labels: cooked actors retain tags, mesh, transform and bounds.
    const FVector Dimensions = Mesh->GetBoundingBox()
        .TransformBy(Component->GetComponentTransform()).GetSize();
    return Candidate.GetActorLocation().Equals(FVector(-11000.0f, 0.0f, 825.0f), 0.1f)
        && Candidate.GetActorRotation().Equals(FRotator::ZeroRotator, 0.01f)
        && Dimensions.Equals(FVector(40.0f, 12000.0f, 1650.0f), 0.25f);
}

AStaticMeshActor* ALBFactoryEnvelopeShutterActor::FindUniqueCleanShellWestWall() const
{
    UWorld* World = GetWorld();
    if (!World) return nullptr;

    AStaticMeshActor* Unique = nullptr;
    int32 Matches = 0;
    for (TActorIterator<AStaticMeshActor> It(World); It; ++It)
    {
        if (!IsValid(*It) || !IsDurableCleanShellWestWall(**It)) continue;
        Unique = *It;
        ++Matches;
    }
    return Matches == 1 ? Unique : nullptr;
}

bool ALBFactoryEnvelopeShutterActor::ActivateCleanShellWestWallReplacement()
{
    if (bReplacementActive) return true;

    // Atomic preflight: no target state changes before every exact dependency resolves.
    UStaticMesh* ResolvedStaticWall = StaticWallMesh.LoadSynchronous();
    UStaticMesh* ResolvedFrame = FrameMesh.LoadSynchronous();
    UStaticMesh* ResolvedLeaf = LeafMesh.LoadSynchronous();
    UStaticMesh* ResolvedCube = InfillCubeMesh.LoadSynchronous();
    UMaterialInterface* ResolvedWarm = WarmWallMaterial.LoadSynchronous();
    UMaterialInterface* ResolvedGraphite = GraphiteMaterial.LoadSynchronous();
#if WITH_DEV_AUTOMATION_TESTS
    if (bUseRuntimeAssetsForTests && ResolvedCube && ResolvedWarm && ResolvedGraphite)
    {
        ResolvedStaticWall = ResolvedCube;
        ResolvedFrame = ResolvedCube;
        ResolvedLeaf = ResolvedCube;
    }
#endif
    AStaticMeshActor* TargetWall = FindUniqueCleanShellWestWall();
    if (!ResolvedStaticWall || !ResolvedFrame || !ResolvedLeaf || !ResolvedCube
        || !ResolvedWarm || !ResolvedGraphite || !TargetWall)
    {
        SetReplacementPresentationEnabled(false);
        UE_LOG(LogTemp, Warning,
            TEXT("LINE_BOSS_FACTORY_ENVELOPE_SHUTTER_FALLBACK assets=%d target=%d"),
            ResolvedStaticWall && ResolvedFrame && ResolvedLeaf && ResolvedCube
                && ResolvedWarm && ResolvedGraphite ? 1 : 0,
            TargetWall ? 1 : 0);
        return false;
    }

    StaticWallPresentation->SetStaticMesh(ResolvedStaticWall);
    FramePresentation->SetStaticMesh(ResolvedFrame);
    LeafPresentation->SetStaticMesh(ResolvedLeaf);
    for (UStaticMeshComponent* Infill : ReplacementInfill)
    {
        if (!Infill) continue;
        Infill->SetStaticMesh(ResolvedCube);
        const bool bGraphite = Infill->ComponentHasTag(
            TEXT("LB.FactoryEnvelope.Material.Graphite"));
        Infill->SetMaterial(0, bGraphite ? ResolvedGraphite : ResolvedWarm);
    }

    SetActorTransform(GetAuthoredWorldTransform(), false, nullptr,
        ETeleportType::TeleportPhysics);
    ShutterOpenFraction = 0.0f;
    LeafMotionRoot->SetRelativeLocation(GetClosedLeafRelativeLocation());
    SetReplacementPresentationEnabled(true);

    UStaticMeshComponent* TargetComponent = TargetWall->GetStaticMeshComponent();
    TargetComponent->SetCanEverAffectNavigation(false);
    TargetComponent->SetCollisionEnabled(ECollisionEnabled::NoCollision);
    TargetComponent->SetGenerateOverlapEvents(false);
    TargetWall->SetActorEnableCollision(false);
    TargetWall->SetActorHiddenInGame(true);

    SupersededWall = TargetWall;
    bReplacementActive = true;
    UE_LOG(LogTemp, Display,
        TEXT("LINE_BOSS_FACTORY_ENVELOPE_SHUTTER_ACTIVE wall=%s opening_y=[-1217.5,-782.5]"),
        *TargetWall->GetName());
    return true;
}

bool ALBFactoryEnvelopeShutterActor::SetShutterOpenFraction(const float InOpenFraction)
{
    if (!FMath::IsFinite(InOpenFraction) || !LeafMotionRoot || !LeafBarrier) return false;

    ShutterOpenFraction = FMath::Clamp(InOpenFraction, 0.0f, 1.0f);
    LeafMotionRoot->SetRelativeLocation(GetClosedLeafRelativeLocation()
        + FVector(0.0f, 0.0f,
            LBFactoryEnvelopeShutterPrivate::LeafTravelCm * ShutterOpenFraction));
    const bool bClosed = bReplacementActive
        && ShutterOpenFraction <= LBFactoryEnvelopeShutterPrivate::ExactClosedTolerance;
    LeafBarrier->SetCollisionEnabled(bClosed
        ? ECollisionEnabled::QueryOnly : ECollisionEnabled::NoCollision);
    return true;
}

TArray<FSoftObjectPath> ALBFactoryEnvelopeShutterActor::GetRuntimeAssetPaths() const
{
    return {
        StaticWallMesh.ToSoftObjectPath(), FrameMesh.ToSoftObjectPath(),
        LeafMesh.ToSoftObjectPath(), InfillCubeMesh.ToSoftObjectPath(),
        WarmWallMaterial.ToSoftObjectPath(), GraphiteMaterial.ToSoftObjectPath()
    };
}

#if WITH_DEV_AUTOMATION_TESTS
void ALBFactoryEnvelopeShutterActor::SetRuntimeAssetReferencesForTests(
    const FSoftObjectPath& StaticWallPath, const FSoftObjectPath& FramePath,
    const FSoftObjectPath& LeafPath, const FSoftObjectPath& CubePath,
    const FSoftObjectPath& WarmWallMaterialPath,
    const FSoftObjectPath& GraphiteMaterialPath)
{
    if (bReplacementActive) return;
    StaticWallMesh = TSoftObjectPtr<UStaticMesh>(StaticWallPath);
    FrameMesh = TSoftObjectPtr<UStaticMesh>(FramePath);
    LeafMesh = TSoftObjectPtr<UStaticMesh>(LeafPath);
    InfillCubeMesh = TSoftObjectPtr<UStaticMesh>(CubePath);
    WarmWallMaterial = TSoftObjectPtr<UMaterialInterface>(WarmWallMaterialPath);
    GraphiteMaterial = TSoftObjectPtr<UMaterialInterface>(GraphiteMaterialPath);
}
#endif
