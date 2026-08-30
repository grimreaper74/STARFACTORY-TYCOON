#if WITH_DEV_AUTOMATION_TESTS

#include "Misc/AutomationTest.h"

#include "Components/DirectionalLightComponent.h"
#include "Components/RectLightComponent.h"
#include "Components/SkyLightComponent.h"
#include "Components/StaticMeshComponent.h"
#include "Engine/DirectionalLight.h"
#include "Engine/Engine.h"
#include "Engine/PostProcessVolume.h"
#include "Engine/RectLight.h"
#include "Engine/SkyLight.h"
#include "Engine/StaticMesh.h"
#include "Engine/StaticMeshActor.h"
#include "Engine/World.h"
#include "EngineUtils.h"
#include "LBGameMode.h"
#include "Materials/MaterialInstanceDynamic.h"
#include "Materials/MaterialInterface.h"
#include "Materials/MaterialInstance.h"

namespace
{
UWorld* CreateVisualTuningWorld()
{
    UWorld* World = UWorld::CreateWorld(EWorldType::Game, false,
        TEXT("LB_VisualTuning_RuntimeContract"));
    if (!World) return nullptr;

    FWorldContext& Context = GEngine->CreateNewWorldContext(EWorldType::Game);
    Context.SetCurrentWorld(World);
    World->InitializeActorsForPlay(FURL());
    return World;
}

void DestroyVisualTuningWorld(UWorld* World)
{
    if (!World) return;
    World->DestroyWorld(false);
    GEngine->DestroyWorldContext(World);
}

template <typename TActorType>
TActorType* SpawnNamedActor(UWorld* World, const TCHAR* Name,
    const FVector& Location = FVector::ZeroVector)
{
    if (!World) return nullptr;

    FActorSpawnParameters SpawnParams;
    SpawnParams.Name = FName(Name);
    SpawnParams.SpawnCollisionHandlingOverride =
        ESpawnActorCollisionHandlingMethod::AlwaysSpawn;
    TActorType* Actor = World->SpawnActor<TActorType>(TActorType::StaticClass(),
        FTransform(FRotator::ZeroRotator, Location), SpawnParams);
#if WITH_EDITOR
    if (Actor) Actor->SetActorLabel(Name, false);
#endif
    return Actor;
}

AStaticMeshActor* SpawnMeshFixture(UWorld* World, const TCHAR* Name,
    const FVector& Location, UStaticMesh* Mesh, UMaterialInterface* Material)
{
    AStaticMeshActor* Actor = SpawnNamedActor<AStaticMeshActor>(World, Name, Location);
    if (!Actor) return nullptr;

    Actor->SetActorEnableCollision(true);
    Actor->SetActorHiddenInGame(false);
    if (UStaticMeshComponent* Component = Actor->GetStaticMeshComponent())
    {
        Component->SetMobility(EComponentMobility::Movable);
        Component->SetStaticMesh(Mesh);
        Component->SetMaterial(0, Material);
    }
    return Actor;
}

bool NearlyEqualColour(const FLinearColor& Actual, const FLinearColor& Expected,
    const float Tolerance = 0.015f)
{
    return Actual.Equals(Expected, Tolerance);
}
}

IMPLEMENT_SIMPLE_AUTOMATION_TEST(FLBFactoryVisualTuningRuntimeContractTest,
    "LineBoss.VisualTuning.RuntimeContract",
    EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)

bool FLBFactoryVisualTuningRuntimeContractTest::RunTest(const FString& Parameters)
{
    UWorld* World = CreateVisualTuningWorld();
    TestNotNull(TEXT("Visual-tuning transient world exists"), World);
    if (!World) return false;

    ASkyLight* CleanSky = SpawnNamedActor<ASkyLight>(World,
        TEXT("CookedSkyActor_2147480001"));
    ASkyLight* FutureSky = SpawnNamedActor<ASkyLight>(World,
        TEXT("LB_PAINT_Light_Sky_FutureZone"));
    ADirectionalLight* CleanSun = SpawnNamedActor<ADirectionalLight>(World,
        TEXT("CookedDirectionalActor_2147480002"));
    ADirectionalLight* FutureSun = SpawnNamedActor<ADirectionalLight>(World,
        TEXT("LB_ASSEMBLY_Light_Directional_FutureZone"));
    ARectLight* CleanFixture = SpawnNamedActor<ARectLight>(World,
        TEXT("CookedRectActor_2147480003"));
    ARectLight* FutureFixture = SpawnNamedActor<ARectLight>(World,
        TEXT("LB_WELD_Light_Rect_FutureZone"));
    ARectLight* UntaggedCleanName = SpawnNamedActor<ARectLight>(World,
        TEXT("LB_CLEAN_Light_Rect_Untagged_Test"));
    ARectLight* AuthoredTrainFill = SpawnNamedActor<ARectLight>(World,
        TEXT("LB_CLEAN_TrainFill_Test"));
    TestTrue(TEXT("Clean-shell and future-zone light fixtures spawn"),
        CleanSky && FutureSky && CleanSun && FutureSun && CleanFixture && FutureFixture
        && UntaggedCleanName && AuthoredTrainFill);
    if (!CleanSky || !FutureSky || !CleanSun || !FutureSun
        || !CleanFixture || !FutureFixture || !UntaggedCleanName || !AuthoredTrainFill)
    {
        DestroyVisualTuningWorld(World);
        return false;
    }

    USkyLightComponent* CleanSkyComponent = CleanSky->GetLightComponent();
    USkyLightComponent* FutureSkyComponent = FutureSky->GetLightComponent();
    UDirectionalLightComponent* CleanSunComponent =
        Cast<UDirectionalLightComponent>(CleanSun->GetLightComponent());
    UDirectionalLightComponent* FutureSunComponent =
        Cast<UDirectionalLightComponent>(FutureSun->GetLightComponent());
    URectLightComponent* CleanFixtureComponent =
        Cast<URectLightComponent>(CleanFixture->GetLightComponent());
    URectLightComponent* FutureFixtureComponent =
        Cast<URectLightComponent>(FutureFixture->GetLightComponent());
    URectLightComponent* UntaggedCleanNameComponent =
        Cast<URectLightComponent>(UntaggedCleanName->GetLightComponent());
    URectLightComponent* AuthoredTrainFillComponent =
        Cast<URectLightComponent>(AuthoredTrainFill->GetLightComponent());
    TestTrue(TEXT("Every light fixture exposes its expected component"),
        CleanSkyComponent && FutureSkyComponent && CleanSunComponent
        && FutureSunComponent && CleanFixtureComponent && FutureFixtureComponent
        && UntaggedCleanNameComponent && AuthoredTrainFillComponent);
    if (!CleanSkyComponent || !FutureSkyComponent || !CleanSunComponent
        || !FutureSunComponent || !CleanFixtureComponent || !FutureFixtureComponent
        || !UntaggedCleanNameComponent || !AuthoredTrainFillComponent)
    {
        DestroyVisualTuningWorld(World);
        return false;
    }

    const FName CleanShellAuthorityTag(TEXT("LB.CleanShell.v20260809.v001"));
    CleanSky->Tags.AddUnique(CleanShellAuthorityTag);
    CleanSun->Tags.AddUnique(CleanShellAuthorityTag);
    CleanFixture->Tags.AddUnique(CleanShellAuthorityTag);
    // Train-fill lights can live inside the clean-shell authority in cooked maps, but
    // remain a separate authored accent-light contract and must not be flattened.
    AuthoredTrainFill->Tags.AddUnique(CleanShellAuthorityTag);
    AuthoredTrainFill->Tags.AddUnique(TEXT("LB.Lighting.TrainFill"));

    CleanSkyComponent->SetMobility(EComponentMobility::Stationary);
    CleanSkyComponent->SetIntensity(0.25f);
    // Seed every future-zone sentinel while dynamic changes are allowed, then
    // freeze it as Static. A later clean-shell-only pass must not thaw it.
    FutureSkyComponent->SetMobility(EComponentMobility::Movable);
    FutureSkyComponent->SetIntensity(0.37f);
    FutureSkyComponent->SetLightColor(FLinearColor(0.20f, 0.30f, 0.40f));
    FutureSkyComponent->bLowerHemisphereIsBlack = true;
    FutureSkyComponent->SetLowerHemisphereColor(FLinearColor(0.11f, 0.12f, 0.13f));
    FutureSkyComponent->SetOcclusionExponent(1.31f);
    FutureSkyComponent->SetMinOcclusion(0.07f);
    FutureSkyComponent->SetMobility(EComponentMobility::Static);

    CleanSunComponent->SetMobility(EComponentMobility::Stationary);
    CleanSunComponent->SetIntensity(0.50f);
    CleanSunComponent->SetCastShadows(true);
    FutureSunComponent->SetMobility(EComponentMobility::Stationary);
    FutureSunComponent->SetIntensity(0.91f);
    FutureSunComponent->SetLightColor(FLinearColor(0.24f, 0.34f, 0.44f), false);
    FutureSunComponent->SetLightSourceAngle(0.70f);
    FutureSunComponent->SetShadowSourceAngleFactor(0.63f);
    FutureSunComponent->SetShadowAmount(0.81f);
    FutureSunComponent->SetCastShadows(true);

    CleanFixtureComponent->SetMobility(EComponentMobility::Stationary);
    CleanFixtureComponent->SetIntensity(777.0f);
    CleanFixtureComponent->SetVisibility(true);
    FutureFixtureComponent->SetMobility(EComponentMobility::Stationary);
    FutureFixtureComponent->SetIntensity(321.0f);
    FutureFixtureComponent->SetLightColor(FLinearColor(0.31f, 0.41f, 0.51f), false);
    FutureFixtureComponent->SetVisibility(true);
    UntaggedCleanNameComponent->SetMobility(EComponentMobility::Stationary);
    UntaggedCleanNameComponent->SetIntensity(654.0f);
    UntaggedCleanNameComponent->SetLightColor(FLinearColor(0.32f, 0.42f, 0.52f), false);
    UntaggedCleanNameComponent->SetVisibility(true);
    AuthoredTrainFillComponent->SetMobility(EComponentMobility::Stationary);
    AuthoredTrainFillComponent->SetIntensity(987.0f);
    AuthoredTrainFillComponent->SetLightColor(FLinearColor(0.33f, 0.43f, 0.53f), false);
    AuthoredTrainFillComponent->SetVisibility(true);

    UStaticMesh* Cube = LoadObject<UStaticMesh>(nullptr,
        TEXT("/Engine/BasicShapes/Cube.Cube"));
    UMaterialInterface* SentinelMaterial = LoadObject<UMaterialInterface>(nullptr,
        TEXT("/Engine/EngineMaterials/DefaultMaterial.DefaultMaterial"));
    TestTrue(TEXT("Visual fixtures load the engine cube and sentinel material"),
        Cube && SentinelMaterial);

    AStaticMeshActor* CleanRoof = SpawnMeshFixture(World, TEXT("CookedRoofActor_2147480005"),
        FVector(0.0f, 0.0f, 1700.0f), Cube, SentinelMaterial);
    AStaticMeshActor* CleanRoofV2 = SpawnMeshFixture(World,
        TEXT("CookedRoofLinerV2Actor_2147480006"), FVector(0.0f, 50.0f, 1675.0f),
        Cube, SentinelMaterial);
    AStaticMeshActor* TallCleanCrane = SpawnMeshFixture(World,
        TEXT("LB_CLEAN_Crane_Overhead_Test"), FVector(100.0f, 0.0f, 3000.0f),
        Cube, SentinelMaterial);
    AStaticMeshActor* TallFutureOven = SpawnMeshFixture(World,
        TEXT("LB_PAINT_Oven_Tall_Test"), FVector(200.0f, 0.0f, 3500.0f),
        Cube, SentinelMaterial);
    AStaticMeshActor* CleanFloor = SpawnMeshFixture(World,
        TEXT("CookedStructuralSlabActor_2147480004"), FVector(0.0f, 100.0f, 0.0f),
        Cube, SentinelMaterial);
    AStaticMeshActor* CleanWall = SpawnMeshFixture(World,
        TEXT("LB_CLEAN_Wall_Test"), FVector(0.0f, 200.0f, 0.0f),
        Cube, SentinelMaterial);
    AStaticMeshActor* FutureFloor = SpawnMeshFixture(World,
        TEXT("LB_PAINT_Floor_Test"), FVector(0.0f, 300.0f, 0.0f),
        Cube, SentinelMaterial);
    AStaticMeshActor* UntaggedCleanFloor = SpawnMeshFixture(World,
        TEXT("LB_CLEAN_Floor_Untagged_Test"), FVector(0.0f, 400.0f, 0.0f),
        Cube, SentinelMaterial);
    AStaticMeshActor* GeneratedRoutePaint = SpawnMeshFixture(World,
        TEXT("LB_AUTOMATIC_Route_Paint_Test"), FVector(0.0f, 500.0f, 0.0f),
        Cube, SentinelMaterial);
    TestTrue(TEXT("Roof, tall-equipment and surface fixtures spawn"), CleanRoof
        && CleanRoofV2
        && TallCleanCrane && TallFutureOven && CleanFloor && CleanWall && FutureFloor
        && UntaggedCleanFloor && GeneratedRoutePaint);
    if (!CleanRoof || !CleanRoofV2 || !TallCleanCrane || !TallFutureOven
        || !CleanFloor || !CleanWall || !FutureFloor || !UntaggedCleanFloor
        || !GeneratedRoutePaint)
    {
        DestroyVisualTuningWorld(World);
        return false;
    }
    CleanRoof->Tags.AddUnique(CleanShellAuthorityTag);
    CleanRoof->Tags.AddUnique(TEXT("LB.Environment.RoofLiner"));
    CleanRoofV2->Tags.AddUnique(TEXT("LB.CleanShell.v20260809.v002"));
    CleanRoofV2->Tags.AddUnique(TEXT("LB.Environment.RoofLiner"));
    CleanFloor->Tags.AddUnique(CleanShellAuthorityTag);
    CleanFloor->Tags.AddUnique(TEXT("LB.Environment.Floor"));
    CleanWall->Tags.AddUnique(CleanShellAuthorityTag);
    CleanWall->Tags.AddUnique(TEXT("LB.Environment.Wall"));
    GeneratedRoutePaint->Tags.AddUnique(CleanShellAuthorityTag);
    GeneratedRoutePaint->Tags.AddUnique(TEXT("LB.FloorPaint.FixedWalkway"));

    ALBGameMode* GameMode = SpawnNamedActor<ALBGameMode>(World,
        TEXT("LB_VisualTuning_GameMode"));
    TestNotNull(TEXT("Factory GameMode spawns for runtime tuning"), GameMode);
    if (GameMode) GameMode->DispatchBeginPlay();

    APostProcessVolume* FactoryGrade = nullptr;
    int32 FactoryGradeCount = 0;
    for (TActorIterator<APostProcessVolume> It(World); It; ++It)
    {
        if (IsValid(*It) && It->ActorHasTag(TEXT("LB.Visual.FactoryColourGrade")))
        {
            FactoryGrade = *It;
            ++FactoryGradeCount;
        }
    }
    TestEqual(TEXT("Runtime creates exactly one tagged factory colour grade"),
        FactoryGradeCount, 1);
    TestTrue(TEXT("Factory colour grade is unbound at full high-priority blend"),
        FactoryGrade && FactoryGrade->bUnbound
        && FMath::IsNearlyEqual(FactoryGrade->Priority, 1000.0f)
        && FMath::IsNearlyEqual(FactoryGrade->BlendWeight, 1.0f));
    if (FactoryGrade)
    {
        const FPostProcessSettings& Grade = FactoryGrade->Settings;
        TestTrue(TEXT("Factory grade owns the approved local-light exposure balance"),
            Grade.bOverride_AutoExposureBias
            && FMath::IsNearlyEqual(Grade.AutoExposureBias, 0.95f));
        TestTrue(TEXT("Factory grade owns restrained global contrast"),
            Grade.bOverride_ColorContrast
            && Grade.ColorContrast.Equals(FVector4(1.02f, 1.02f, 1.02f, 1.0f), 0.001f));
        TestTrue(TEXT("Factory grade owns restrained global saturation"),
            Grade.bOverride_ColorSaturation
            && Grade.ColorSaturation.Equals(FVector4(1.06f, 1.06f, 1.06f, 1.0f), 0.001f));
        TestTrue(TEXT("Factory grade keeps vignette and AO restrained"),
            Grade.bOverride_VignetteIntensity
            && FMath::IsNearlyEqual(Grade.VignetteIntensity, 0.10f)
            && Grade.bOverride_AmbientOcclusionIntensity
            && FMath::IsNearlyEqual(Grade.AmbientOcclusionIntensity, 0.58f)
            && Grade.bOverride_AmbientOcclusionRadius
            && FMath::IsNearlyEqual(Grade.AmbientOcclusionRadius, 120.0f)
            && Grade.bOverride_LumenAmbientOcclusionIntensity
            && FMath::IsNearlyEqual(Grade.LumenAmbientOcclusionIntensity, 0.58f));
    }

    TestTrue(TEXT("Clean-shell skylight receives the approved bright fill contract"),
        CleanSkyComponent->Mobility == EComponentMobility::Movable
        && FMath::IsNearlyEqual(CleanSkyComponent->Intensity, 1.65f)
        && CleanSkyComponent->LightColor
            == FLinearColor(0.94f, 0.97f, 1.0f).ToFColor(true)
        && !CleanSkyComponent->bLowerHemisphereIsBlack
        && NearlyEqualColour(CleanSkyComponent->LowerHemisphereColor,
            FLinearColor(0.18f, 0.19f, 0.20f), 0.001f)
        && FMath::IsNearlyEqual(CleanSkyComponent->OcclusionExponent, 1.10f)
        && FMath::IsNearlyEqual(CleanSkyComponent->MinOcclusion, 0.08f));
    TestTrue(TEXT("Future-zone skylight is not mutated by clean-shell tuning"),
        FutureSkyComponent->Mobility == EComponentMobility::Static
        && FMath::IsNearlyEqual(FutureSkyComponent->Intensity, 0.37f)
        && FutureSkyComponent->LightColor
            == FLinearColor(0.20f, 0.30f, 0.40f).ToFColor(true)
        && FutureSkyComponent->bLowerHemisphereIsBlack
        && NearlyEqualColour(FutureSkyComponent->LowerHemisphereColor,
            FLinearColor(0.11f, 0.12f, 0.13f), 0.001f)
        && FMath::IsNearlyEqual(FutureSkyComponent->OcclusionExponent, 1.31f)
        && FMath::IsNearlyEqual(FutureSkyComponent->MinOcclusion, 0.07f));

    TestTrue(TEXT("Clean-shell directional light receives the approved soft rig"),
        CleanSunComponent->Mobility == EComponentMobility::Movable
        && FMath::IsNearlyEqual(CleanSunComponent->Intensity, 1.80f)
        && CleanSunComponent->LightColor
            == FLinearColor(1.0f, 0.97f, 0.92f).ToFColor(false)
        && FMath::IsNearlyEqual(CleanSunComponent->LightSourceAngle, 8.0f)
        && FMath::IsNearlyEqual(CleanSunComponent->ShadowSourceAngleFactor, 1.0f)
        && FMath::IsNearlyEqual(CleanSunComponent->ShadowAmount, 0.03f)
        && CleanSunComponent->CastShadows);
    TestTrue(TEXT("Future-zone directional light retains every sentinel setting"),
        FutureSunComponent->Mobility == EComponentMobility::Stationary
        && FMath::IsNearlyEqual(FutureSunComponent->Intensity, 0.91f)
        && FutureSunComponent->LightColor
            == FLinearColor(0.24f, 0.34f, 0.44f).ToFColor(false)
        && FMath::IsNearlyEqual(FutureSunComponent->LightSourceAngle, 0.70f)
        && FMath::IsNearlyEqual(FutureSunComponent->ShadowSourceAngleFactor, 0.63f)
        && FMath::IsNearlyEqual(FutureSunComponent->ShadowAmount, 0.81f)
        && FutureSunComponent->CastShadows);

    TestTrue(TEXT("Clean-shell rect fixture is suppressed to prevent repeated floor pools"),
        CleanFixtureComponent->Mobility == EComponentMobility::Movable
        && FMath::IsNearlyZero(CleanFixtureComponent->Intensity)
        && !CleanFixtureComponent->CastShadows
        && !CleanFixtureComponent->IsVisible());
    TestTrue(TEXT("Future-zone rect fixture remains visible and otherwise untouched"),
        FutureFixtureComponent->Mobility == EComponentMobility::Stationary
        && FMath::IsNearlyEqual(FutureFixtureComponent->Intensity, 321.0f)
        && FutureFixtureComponent->LightColor
            == FLinearColor(0.31f, 0.41f, 0.51f).ToFColor(false)
        && FutureFixtureComponent->IsVisible());
    TestTrue(TEXT("Clean-looking untagged rect light is outside runtime authority"),
        UntaggedCleanNameComponent->Mobility == EComponentMobility::Stationary
        && FMath::IsNearlyEqual(UntaggedCleanNameComponent->Intensity, 654.0f)
        && UntaggedCleanNameComponent->LightColor
            == FLinearColor(0.32f, 0.42f, 0.52f).ToFColor(false)
        && UntaggedCleanNameComponent->IsVisible());
    TestTrue(TEXT("Later authored train-fill fixture is outside shell-light authority"),
        AuthoredTrainFillComponent->Mobility == EComponentMobility::Stationary
        && FMath::IsNearlyEqual(AuthoredTrainFillComponent->Intensity, 987.0f)
        && AuthoredTrainFillComponent->LightColor
            == FLinearColor(0.33f, 0.43f, 0.53f).ToFColor(false)
        && AuthoredTrainFillComponent->IsVisible());

    TestTrue(TEXT("Durably tagged clean-shell roof pieces are hidden without editor labels"),
        CleanRoof->IsHidden() && !CleanRoof->GetActorEnableCollision());
    TestTrue(TEXT("Promoted v002 roof liner remains part of the hidden roof authority"),
        CleanRoofV2->IsHidden() && !CleanRoofV2->GetActorEnableCollision());
    TestTrue(TEXT("Tall clean-shell crane is not mistaken for a roof"),
        !TallCleanCrane->IsHidden() && TallCleanCrane->GetActorEnableCollision());
    TestTrue(TEXT("Tall future paint oven is not mistaken for a roof"),
        !TallFutureOven->IsHidden() && TallFutureOven->GetActorEnableCollision());

    UMaterialInterface* FloorMaterial =
        CleanFloor->GetStaticMeshComponent()->GetMaterial(0);
    TestTrue(TEXT("Only the clean-shell floor receives the world-scale slab material"),
        FloorMaterial && FloorMaterial->GetPathName()
            == TEXT("/Game/LineBoss/Materials/Environment/MI_LB_SealedFactoryConcrete_Neutral_v001.MI_LB_SealedFactoryConcrete_Neutral_v001"));
    TestTrue(TEXT("Clean-shell floor material is an authored instance, not a flat runtime MID"),
        FloorMaterial && FloorMaterial->IsA<UMaterialInstance>()
        && !FloorMaterial->IsA<UMaterialInstanceDynamic>());
    UMaterialInterface* WallMaterial =
        CleanWall->GetStaticMeshComponent()->GetMaterial(0);
    TestTrue(TEXT("Only the tagged clean-shell wall receives the approved warm envelope material"),
        WallMaterial && WallMaterial->GetPathName()
            == TEXT("/Game/LineBoss/Candidates/Architecture/FactoryEnvelopeKitRuntime_v001/Materials/MI_LB_Architecture_WarmOffWhite_v001.MI_LB_Architecture_WarmOffWhite_v001"));
    for (int32 MaterialIndex = 0;
        MaterialIndex < CleanWall->GetStaticMeshComponent()->GetNumMaterials(); ++MaterialIndex)
    {
        UMaterialInterface* SlotMaterial =
            CleanWall->GetStaticMeshComponent()->GetMaterial(MaterialIndex);
        TestTrue(FString::Printf(TEXT("Clean-shell wall slot %d receives the approved warm envelope material"),
            MaterialIndex), SlotMaterial && SlotMaterial->GetPathName()
                == TEXT("/Game/LineBoss/Candidates/Architecture/FactoryEnvelopeKitRuntime_v001/Materials/MI_LB_Architecture_WarmOffWhite_v001.MI_LB_Architecture_WarmOffWhite_v001"));
    }
    TestTrue(TEXT("Future-zone floor material remains authored and untouched"),
        FutureFloor->GetStaticMeshComponent()->GetMaterial(0) == SentinelMaterial);
    TestTrue(TEXT("Clean-looking untagged floor remains authored and untouched"),
        UntaggedCleanFloor->GetStaticMeshComponent()->GetMaterial(0) == SentinelMaterial);
    TestTrue(TEXT("Generated route paint remains its own material authority"),
        GeneratedRoutePaint->GetStaticMeshComponent()->GetMaterial(0) == SentinelMaterial);
    TestTrue(TEXT("Future-zone tall oven material remains authored and untouched"),
        TallFutureOven->GetStaticMeshComponent()->GetMaterial(0) == SentinelMaterial);

    DestroyVisualTuningWorld(World);
    return true;
}

#endif
