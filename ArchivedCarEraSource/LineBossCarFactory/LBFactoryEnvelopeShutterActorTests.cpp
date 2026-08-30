#if WITH_DEV_AUTOMATION_TESTS

#include "LBFactoryEnvelopeShutterActor.h"

#include "Algo/AllOf.h"
#include "Components/BoxComponent.h"
#include "Components/StaticMeshComponent.h"
#include "Engine/Engine.h"
#include "Engine/StaticMesh.h"
#include "Engine/StaticMeshActor.h"
#include "Engine/World.h"
#include "EngineUtils.h"
#include "LBFactoryAGVInfrastructure.h"
#include "LBFactoryTransportLink.h"
#include "Materials/MaterialInterface.h"
#include "Misc/AutomationTest.h"

namespace LBFactoryEnvelopeShutterTests
{
    const FName CleanShellTag(TEXT("LB.CleanShell.v20260809.v001"));
    const FName NewAuthoredTag(TEXT("LB.Asset.NewAuthored"));
    const FName WallTag(TEXT("LB.Environment.Wall"));

    UWorld* CreateWorld(const TCHAR* Name)
    {
        UWorld* World = UWorld::CreateWorld(EWorldType::Game, false, FName(Name));
        if (!World) return nullptr;
        FWorldContext& Context = GEngine->CreateNewWorldContext(EWorldType::Game);
        Context.SetCurrentWorld(World);
        World->InitializeActorsForPlay(FURL());
        return World;
    }

    void DestroyWorld(UWorld* World)
    {
        if (!World) return;
        World->DestroyWorld(false);
        GEngine->DestroyWorldContext(World);
    }

    template<typename TActor>
    TActor* Spawn(UWorld* World, const TCHAR* Name, const FTransform& Transform)
    {
        if (!World) return nullptr;
        FActorSpawnParameters Params;
        Params.Name = FName(Name);
        Params.SpawnCollisionHandlingOverride =
            ESpawnActorCollisionHandlingMethod::AlwaysSpawn;
        return World->SpawnActor<TActor>(TActor::StaticClass(), Transform, Params);
    }

    AStaticMeshActor* SpawnCleanWestWall(UWorld* World, const TCHAR* Name,
        UStaticMesh* Cube)
    {
        AStaticMeshActor* Wall = Spawn<AStaticMeshActor>(World, Name,
            FTransform(FVector(-11000.0f, 0.0f, 825.0f)));
        if (!Wall || !Cube) return Wall;

        Wall->Tags = {CleanShellTag, NewAuthoredTag, WallTag};
        Wall->SetActorEnableCollision(true);
        Wall->SetActorHiddenInGame(false);
        UStaticMeshComponent* Component = Wall->GetStaticMeshComponent();
        Component->SetMobility(EComponentMobility::Movable);
        Component->SetStaticMesh(Cube);
        Component->SetWorldScale3D(FVector(0.4f, 120.0f, 16.5f));
        Component->SetCollisionEnabled(ECollisionEnabled::QueryAndPhysics);
        Component->SetCollisionResponseToAllChannels(ECR_Block);
        Component->SetCanEverAffectNavigation(true);
        return Wall;
    }

    ALBFactoryEnvelopeShutterActor* SpawnTestShutter(UWorld* World,
        UStaticMesh* Cube, UMaterialInterface* Material)
    {
        ALBFactoryEnvelopeShutterActor* Shutter =
            Spawn<ALBFactoryEnvelopeShutterActor>(World, TEXT("LB_Test_Shutter"),
                ALBFactoryEnvelopeShutterActor::GetAuthoredWorldTransform());
        if (!Shutter || !Cube || !Material) return Shutter;
        Shutter->SetUseRuntimeAssetsForTests(true);
        const FSoftObjectPath CubePath(Cube->GetPathName());
        const FSoftObjectPath MaterialPath(Material->GetPathName());
        Shutter->SetRuntimeAssetReferencesForTests(CubePath, CubePath, CubePath,
            CubePath, MaterialPath, MaterialPath);
        return Shutter;
    }

    struct FTrackedActor
    {
        TWeakObjectPtr<AActor> Actor;
        FTransform Transform;
        TArray<FName> Tags;
    };

    TArray<FTrackedActor> SnapshotTrackedActors(UWorld* World)
    {
        TArray<FTrackedActor> Result;
        if (!World) return Result;
        for (TActorIterator<AActor> It(World); It; ++It)
        {
            if (!IsValid(*It)) continue;
            if (It->ActorHasTag(TEXT("LB.Environment.Floor"))
                || It->ActorHasTag(TEXT("LB.FloorPaint.FixedWalkway"))
                || It->ActorHasTag(TEXT("LB.FloorPaint.FixedSafetyEdge"))
                || It->IsA<ALBFactoryAGVInfrastructure>()
                || It->IsA<ALBFactoryTransportLink>())
            {
                Result.Add({*It, It->GetActorTransform(), It->Tags});
            }
        }
        return Result;
    }

    bool TrackedActorsUnchanged(const TArray<FTrackedActor>& Before, UWorld* World)
    {
        if (!World) return false;
        TArray<FTrackedActor> After = SnapshotTrackedActors(World);
        if (After.Num() != Before.Num()) return false;
        for (const FTrackedActor& Row : Before)
        {
            const FTrackedActor* Current = After.FindByPredicate(
                [&Row](const FTrackedActor& Candidate)
                {
                    return Candidate.Actor == Row.Actor;
                });
            if (!Current || !Current->Actor.IsValid()
                || !Current->Transform.Equals(Row.Transform, 0.001f)
                || Current->Tags != Row.Tags)
            {
                return false;
            }
        }
        return true;
    }
}

IMPLEMENT_SIMPLE_AUTOMATION_TEST(FLBFactoryEnvelopeShutterAssetTransformContractTest,
    "LineBoss.Environment.FactoryEnvelope.Shutter.AssetAndTransformContract",
    EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)

bool FLBFactoryEnvelopeShutterAssetTransformContractTest::RunTest(const FString& Parameters)
{
    using namespace LBFactoryEnvelopeShutterTests;
    UWorld* World = CreateWorld(TEXT("LB_ShutterAssetTransformContract"));
    TestNotNull(TEXT("Transient shutter contract world exists"), World);
    if (!World) return false;

    ALBFactoryEnvelopeShutterActor* Shutter = Spawn<ALBFactoryEnvelopeShutterActor>(
        World, TEXT("LB_Shutter_Contract"),
        ALBFactoryEnvelopeShutterActor::GetAuthoredWorldTransform());
    TestNotNull(TEXT("Shutter actor spawns"), Shutter);
    if (!Shutter)
    {
        DestroyWorld(World);
        return false;
    }

    const FTransform Authored = ALBFactoryEnvelopeShutterActor::GetAuthoredWorldTransform();
    TestTrue(TEXT("Authored west-wall transform is exact"),
        Authored.GetLocation().Equals(FVector(-11000.0f, -1097.5f, 0.0f), 0.001f)
        && Authored.GetRotation().Rotator().Equals(FRotator(0.0f, -90.0f, 0.0f), 0.001f)
        && Authored.GetScale3D().Equals(FVector::OneVector, 0.001f));
    TestTrue(TEXT("Closed leaf top-centre is exact"),
        ALBFactoryEnvelopeShutterActor::GetClosedLeafRelativeLocation().Equals(
            FVector(-97.5f, -14.5f, 460.0f), 0.001f));

    const FBox Opening = ALBFactoryEnvelopeShutterActor::GetAuthoredClearOpeningWorldBounds();
    TestTrue(TEXT("Clear opening is 4.35 by 4.60 m and centred on Y=-1000"),
        FMath::IsNearlyEqual(Opening.GetSize().Y, 435.0f, 0.001f)
        && FMath::IsNearlyEqual(Opening.GetSize().Z, 460.0f, 0.001f)
        && FMath::IsNearlyEqual(Opening.GetCenter().Y, -1000.0f, 0.001f));

    const TArray<FSoftObjectPath> Paths = Shutter->GetRuntimeAssetPaths();
    TestTrue(TEXT("Six stable imported/cube/material references are exposed"), Paths.Num() == 6
        && Paths[0].ToString() == TEXT("/Game/LineBoss/Candidates/Architecture/FactoryEnvelopeKitRuntime_v001/Meshes/Shutter/SM_LB_ShutterBay_StaticWall_v001.SM_LB_ShutterBay_StaticWall_v001")
        && Paths[1].ToString() == TEXT("/Game/LineBoss/Candidates/Architecture/FactoryEnvelopeKitRuntime_v001/Meshes/Shutter/SM_LB_ShutterBay_Frame_v001.SM_LB_ShutterBay_Frame_v001")
        && Paths[2].ToString() == TEXT("/Game/LineBoss/Candidates/Architecture/FactoryEnvelopeKitRuntime_v001/Meshes/Shutter/SM_LB_ShutterLeaf_v001.SM_LB_ShutterLeaf_v001"));
    TestTrue(TEXT("Imported runtime assets and both infill materials resolve"),
        Paths.Num() == 6 && Algo::AllOf(Paths,
            [](const FSoftObjectPath& Path) { return Path.TryLoad() != nullptr; }));

    UStaticMesh* WallMesh = Paths.Num() > 0
        ? Cast<UStaticMesh>(Paths[0].ResolveObject()) : nullptr;
    UStaticMesh* FrameMesh = Paths.Num() > 1
        ? Cast<UStaticMesh>(Paths[1].ResolveObject()) : nullptr;
    UStaticMesh* LeafMesh = Paths.Num() > 2
        ? Cast<UStaticMesh>(Paths[2].ResolveObject()) : nullptr;
    TestTrue(TEXT("Validated imported topology stays at wall/frame/leaf LOD contract"),
        WallMesh && FrameMesh && LeafMesh
        && WallMesh->GetNumLODs() == 1 && WallMesh->GetNumTriangles(0) == 972
        && FrameMesh->GetNumLODs() == 1 && FrameMesh->GetNumTriangles(0) == 432
        && LeafMesh->GetNumLODs() == 3
        && LeafMesh->GetNumTriangles(0) == 3564
        && LeafMesh->GetNumTriangles(1) == 1836
        && LeafMesh->GetNumTriangles(2) == 972);

    DestroyWorld(World);
    return true;
}

IMPLEMENT_SIMPLE_AUTOMATION_TEST(FLBFactoryEnvelopeShutterAtomicReplacementTest,
    "LineBoss.Environment.FactoryEnvelope.Shutter.AtomicCleanShellReplacement",
    EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)

bool FLBFactoryEnvelopeShutterAtomicReplacementTest::RunTest(const FString& Parameters)
{
    using namespace LBFactoryEnvelopeShutterTests;
    UStaticMesh* Cube = LoadObject<UStaticMesh>(nullptr, TEXT("/Engine/BasicShapes/Cube.Cube"));
    UMaterialInterface* Material = LoadObject<UMaterialInterface>(nullptr,
        TEXT("/Engine/EngineMaterials/DefaultMaterial.DefaultMaterial"));
    TestTrue(TEXT("Engine fixtures resolve"), Cube && Material);
    if (!Cube || !Material) return false;

    auto RunFailback = [this, Cube, Material](const int32 TargetCount, const TCHAR* WorldName)
    {
        UWorld* World = LBFactoryEnvelopeShutterTests::CreateWorld(WorldName);
        if (!World) return false;
        TArray<AStaticMeshActor*> Walls;
        for (int32 Index = 0; Index < TargetCount; ++Index)
        {
            Walls.Add(LBFactoryEnvelopeShutterTests::SpawnCleanWestWall(World,
                *FString::Printf(TEXT("CookedWestWall_%d"), Index), Cube));
        }
        ALBFactoryEnvelopeShutterActor* Shutter =
            LBFactoryEnvelopeShutterTests::SpawnTestShutter(World, Cube, Material);
        const bool bActivated = Shutter && Shutter->ActivateCleanShellWestWallReplacement();
        bool bWallsIntact = !bActivated && Shutter && !Shutter->IsReplacementActive();
        for (AStaticMeshActor* Wall : Walls)
        {
            bWallsIntact &= Wall && !Wall->IsHidden()
                && Wall->GetActorEnableCollision()
                && Wall->GetStaticMeshComponent()->GetCollisionEnabled()
                    == ECollisionEnabled::QueryAndPhysics
                && Wall->GetStaticMeshComponent()->CanEverAffectNavigation();
        }
        LBFactoryEnvelopeShutterTests::DestroyWorld(World);
        return bWallsIntact;
    };
    TestTrue(TEXT("Zero matching walls retains the complete old shell"),
        RunFailback(0, TEXT("LB_Shutter_NoTarget")));
    TestTrue(TEXT("Ambiguous matching walls retain both complete old shells"),
        RunFailback(2, TEXT("LB_Shutter_AmbiguousTarget")));

    UWorld* World = CreateWorld(TEXT("LB_Shutter_ExactTarget"));
    AStaticMeshActor* WestWall = SpawnCleanWestWall(World, TEXT("CookedWestWall_Exact"), Cube);
    ALBFactoryEnvelopeShutterActor* Shutter = SpawnTestShutter(World, Cube, Material);
    TestTrue(TEXT("Exact durable wall activates one atomic replacement"),
        Shutter && Shutter->ActivateCleanShellWestWallReplacement()
        && Shutter->ActivateCleanShellWestWallReplacement()
        && Shutter->IsReplacementActive()
        && Shutter->GetSupersededWall() == WestWall);
    TestTrue(TEXT("Only after success, old west wall is hidden and removed from collision/nav"),
        WestWall && WestWall->IsHidden() && !WestWall->GetActorEnableCollision()
        && WestWall->GetStaticMeshComponent()->GetCollisionEnabled()
            == ECollisionEnabled::NoCollision
        && !WestWall->GetStaticMeshComponent()->CanEverAffectNavigation());
    TestTrue(TEXT("Replacement owns imported wall plus five structural infills"),
        Shutter && Shutter->GetStaticWallPresentation()->IsVisible()
        && Shutter->GetStaticWallPresentation()->GetCollisionEnabled()
            == ECollisionEnabled::QueryAndPhysics
        && Shutter->GetStaticWallPresentation()->CanEverAffectNavigation()
        && Shutter->GetReplacementInfillCount() == 5
        && Algo::AllOf(Shutter->GetReplacementInfill(),
            [](const TObjectPtr<UStaticMeshComponent>& Infill)
            {
                return Infill && Infill->IsVisible()
                    && Infill->GetCollisionEnabled() == ECollisionEnabled::QueryAndPhysics
                    && Infill->CanEverAffectNavigation();
            }));
    TestTrue(TEXT("Frame and leaf remain presentation-only"),
        Shutter && Shutter->GetFramePresentation()->GetCollisionEnabled()
            == ECollisionEnabled::NoCollision
        && !Shutter->GetFramePresentation()->CanEverAffectNavigation()
        && Shutter->GetLeafPresentation()->GetCollisionEnabled()
            == ECollisionEnabled::NoCollision
        && !Shutter->GetLeafPresentation()->CanEverAffectNavigation());

    DestroyWorld(World);
    return true;
}

IMPLEMENT_SIMPLE_AUTOMATION_TEST(FLBFactoryEnvelopeShutterMotionIsolationTest,
    "LineBoss.Environment.FactoryEnvelope.Shutter.TransformMotionCollisionAndPaintIsolation",
    EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)

bool FLBFactoryEnvelopeShutterMotionIsolationTest::RunTest(const FString& Parameters)
{
    using namespace LBFactoryEnvelopeShutterTests;
    UWorld* World = CreateWorld(TEXT("LB_Shutter_MotionIsolation"));
    UStaticMesh* Cube = LoadObject<UStaticMesh>(nullptr, TEXT("/Engine/BasicShapes/Cube.Cube"));
    UMaterialInterface* Material = LoadObject<UMaterialInterface>(nullptr,
        TEXT("/Engine/EngineMaterials/DefaultMaterial.DefaultMaterial"));
    TestTrue(TEXT("Motion isolation fixtures resolve"), World && Cube && Material);
    if (!World || !Cube || !Material)
    {
        DestroyWorld(World);
        return false;
    }

    SpawnCleanWestWall(World, TEXT("CookedWestWall_Motion"), Cube);
    auto SpawnTrackedMesh = [World, Cube](const TCHAR* Name, const FName Tag,
        const FVector& Location)
    {
        AStaticMeshActor* Actor = Spawn<AStaticMeshActor>(World, Name, FTransform(Location));
        Actor->Tags.AddUnique(Tag);
        Actor->GetStaticMeshComponent()->SetMobility(EComponentMobility::Movable);
        Actor->GetStaticMeshComponent()->SetStaticMesh(Cube);
        Actor->GetStaticMeshComponent()->SetCollisionEnabled(ECollisionEnabled::NoCollision);
        Actor->GetStaticMeshComponent()->SetCanEverAffectNavigation(false);
        return Actor;
    };
    SpawnTrackedMesh(TEXT("FloorSentinel"), TEXT("LB.Environment.Floor"), FVector(0,0,-25));
    SpawnTrackedMesh(TEXT("WestWalkwaySentinel"), TEXT("LB.FloorPaint.FixedWalkway"),
        FVector(-10200,0,1));
    SpawnTrackedMesh(TEXT("WestSafetyEdgeSentinel"), TEXT("LB.FloorPaint.FixedSafetyEdge"),
        FVector(-9425,0,1.6f));
    Spawn<ALBFactoryAGVInfrastructure>(World, TEXT("RouteSentinel"),
        FTransform(FVector(-10000,-1000,0)));
    Spawn<ALBFactoryTransportLink>(World, TEXT("TransportSentinel"),
        FTransform(FVector(-9000,-1000,0)));
    const TArray<FTrackedActor> Before = SnapshotTrackedActors(World);

    ALBFactoryEnvelopeShutterActor* Shutter = SpawnTestShutter(World, Cube, Material);
    TestTrue(TEXT("Shutter activates for motion contract"),
        Shutter && Shutter->ActivateCleanShellWestWallReplacement());
    if (!Shutter || !Shutter->IsReplacementActive())
    {
        DestroyWorld(World);
        return false;
    }

    TestTrue(TEXT("Closed pivot and query-only barrier are exact"),
        Shutter->GetLeafPresentation()->GetAttachParent()->GetRelativeLocation().Equals(
            FVector(-97.5f, -14.5f, 460.0f), 0.001f)
        && Shutter->GetLeafBarrier()->GetCollisionEnabled()
            == ECollisionEnabled::QueryOnly
        && !Shutter->GetLeafBarrier()->CanEverAffectNavigation());
    TestTrue(TEXT("Half-open raises 230 cm and disables the barrier"),
        Shutter->SetShutterOpenFraction(0.5f)
        && Shutter->GetLeafPresentation()->GetAttachParent()->GetRelativeLocation().Equals(
            FVector(-97.5f, -14.5f, 690.0f), 0.001f)
        && Shutter->GetLeafBarrier()->GetCollisionEnabled()
            == ECollisionEnabled::NoCollision);
    TestTrue(TEXT("Open raises 460 cm and remains physically clear"),
        Shutter->SetShutterOpenFraction(1.0f)
        && Shutter->GetLeafPresentation()->GetAttachParent()->GetRelativeLocation().Equals(
            FVector(-97.5f, -14.5f, 920.0f), 0.001f)
        && Shutter->GetLeafBarrier()->GetCollisionEnabled()
            == ECollisionEnabled::NoCollision);
    TestTrue(TEXT("Returning exactly closed restores only the query barrier"),
        Shutter->SetShutterOpenFraction(0.0f)
        && Shutter->GetLeafBarrier()->GetCollisionEnabled()
            == ECollisionEnabled::QueryOnly);
    TestTrue(TEXT("Floor, fixed west paint, generated route and transport authority are untouched"),
        TrackedActorsUnchanged(Before, World));

    DestroyWorld(World);
    return true;
}

#endif
