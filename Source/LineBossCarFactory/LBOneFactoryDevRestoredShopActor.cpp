#include "LBOneFactoryDevRestoredShopActor.h"

#include "Components/InstancedStaticMeshComponent.h"
#include "Dom/JsonObject.h"
#include "Engine/StaticMesh.h"
#include "Engine/World.h"
#include "EngineUtils.h"
#include "HAL/FileManager.h"
#include "LBOneFactoryRuntimeCoordinator.h"
#include "Misc/FileHelper.h"
#include "Misc/Paths.h"
#include "Serialization/JsonReader.h"
#include "Serialization/JsonSerializer.h"

ALBOneFactoryDevRestoredShopActor::ALBOneFactoryDevRestoredShopActor()
{
    PrimaryActorTick.bCanEverTick = false;
    SetReplicates(false);
    SetActorEnableCollision(false);

    SceneRoot = CreateDefaultSubobject<USceneComponent>(TEXT("SceneRoot"));
    SceneRoot->SetMobility(EComponentMobility::Movable);
    SetRootComponent(SceneRoot);

    Tags.AddUnique(GetShopTag());
    Tags.AddUnique(TEXT("LB.Environment.VisualOnly"));
    Tags.AddUnique(TEXT("LB.NotProcessWIP"));
}

FName ALBOneFactoryDevRestoredShopActor::GetShopTag()
{
    return FName(TEXT("LB.OneFactory.DevRestoredShop"));
}

bool ALBOneFactoryDevRestoredShopActor::BuildFromManifest(FString& OutReason)
{
    UWorld* World = GetWorld();
    if (!World)
    {
        OutReason = TEXT("NO WORLD");
        return false;
    }

    // Anchor: the committed ConfigurablePressTrain station, same datum the
    // trains stand on.
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
    static const FName PressTrainStation(TEXT("OF_PRESS_TRAIN_001"));
    const FLBOneFactoryRuntimeStationStep* Anchor = nullptr;
    for (const FLBOneFactoryRuntimeStationStep& Step : Route)
    {
        if (Step.StationId == PressTrainStation)
        {
            Anchor = &Step;
            break;
        }
    }
    if (!Anchor)
    {
        OutReason = TEXT("NO CONFIGURABLE PRESS TRAIN IN THE ROUTE");
        return false;
    }
    const FVector DatumLocation = Anchor->WorldTransform.GetLocation()
        + Anchor->WorldTransform.GetRotation().RotateVector(
            FVector(9.25, 2367.5, 0.0));
    const FQuat DatumRotation = Anchor->WorldTransform.GetRotation();

    const FString ManifestPath = FPaths::ProjectContentDir()
        / TEXT("LineBoss/Reference/RestoredShop/shop_manifest.json");
    FString Raw;
    if (!FFileHelper::LoadFileToString(Raw, *ManifestPath))
    {
        OutReason = FString::Printf(TEXT("MANIFEST NOT READABLE: %s"),
            *ManifestPath);
        return false;
    }
    TSharedPtr<FJsonObject> Root;
    const TSharedRef<TJsonReader<>> Reader = TJsonReaderFactory<>::Create(Raw);
    if (!FJsonSerializer::Deserialize(Reader, Root) || !Root.IsValid())
    {
        OutReason = TEXT("MANIFEST PARSE FAILED");
        return false;
    }
    const TArray<TSharedPtr<FJsonValue>>* Actors = nullptr;
    if (!Root->TryGetArrayField(TEXT("actors"), Actors) || !Actors)
    {
        OutReason = TEXT("MANIFEST HAS NO ACTORS");
        return false;
    }

    // The restored shop's train row runs across the other axis: reference X
    // (train length) maps to Moorcross Y, reference Y (row spacing) to -X.
    // That is a +90 degree yaw applied datum-locally.
    const FQuat ReferenceToLocal(FVector::UpVector,
        FMath::DegreesToRadians(90.0));

    for (UInstancedStaticMeshComponent* Old : Batches)
    {
        if (Old)
        {
            Old->DestroyComponent();
        }
    }
    Batches.Reset();
    PlacedCount = 0;

    TMap<FString, UInstancedStaticMeshComponent*> ByMesh;
    int32 MissingMeshes = 0;
    for (const TSharedPtr<FJsonValue>& Value : *Actors)
    {
        const TSharedPtr<FJsonObject> Entry = Value->AsObject();
        if (!Entry.IsValid())
        {
            continue;
        }
        const FString MeshPath = Entry->GetStringField(TEXT("mesh"));

        UInstancedStaticMeshComponent* Batch = ByMesh.FindRef(MeshPath);
        if (!Batch)
        {
            UStaticMesh* Mesh = Cast<UStaticMesh>(StaticLoadObject(
                UStaticMesh::StaticClass(), nullptr, *MeshPath));
            if (!Mesh)
            {
                ++MissingMeshes;
                continue;
            }
            Batch = NewObject<UInstancedStaticMeshComponent>(this);
            Batch->SetupAttachment(SceneRoot);
            Batch->SetMobility(EComponentMobility::Movable);
            Batch->SetCollisionEnabled(ECollisionEnabled::NoCollision);
            Batch->SetCanEverAffectNavigation(false);
            Batch->SetStaticMesh(Mesh);
            Batch->RegisterComponent();
            ByMesh.Add(MeshPath, Batch);
            Batches.Add(Batch);
        }

        auto ReadVector = [&Entry](const TCHAR* Field) -> FVector
        {
            const TArray<TSharedPtr<FJsonValue>>* Numbers = nullptr;
            if (Entry->TryGetArrayField(Field, Numbers) && Numbers
                && Numbers->Num() == 3)
            {
                return FVector((*Numbers)[0]->AsNumber(),
                    (*Numbers)[1]->AsNumber(), (*Numbers)[2]->AsNumber());
            }
            return FVector::ZeroVector;
        };
        const FVector RelativeLocation = ReadVector(TEXT("loc"));
        const FVector RotationValues = ReadVector(TEXT("rot"));
        FVector Scale = ReadVector(TEXT("scale"));
        if (Scale.IsNearlyZero())
        {
            Scale = FVector::OneVector;
        }

        const FQuat ReferenceRotation = FRotator(RotationValues.X,
            RotationValues.Y, RotationValues.Z).Quaternion();
        const FQuat LocalRotation = ReferenceToLocal * ReferenceRotation;
        const FVector LocalLocation =
            ReferenceToLocal.RotateVector(RelativeLocation);

        FTransform Instance;
        Instance.SetLocation(DatumLocation
            + DatumRotation.RotateVector(LocalLocation));
        Instance.SetRotation(DatumRotation * LocalRotation);
        Instance.SetScale3D(Scale);
        if (Batch->AddInstance(Instance, true) != INDEX_NONE)
        {
            ++PlacedCount;
        }
    }

    OutReason = FString::Printf(
        TEXT("restored shop: %d instance(s) across %d mesh(es); %d mesh "
             "path(s) unresolved"),
        PlacedCount, Batches.Num(), MissingMeshes);
    return PlacedCount > 0;
}
