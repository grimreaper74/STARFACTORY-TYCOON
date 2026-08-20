#include "LBOneFactoryDevRestoredShopActor.h"

#include "Components/InstancedStaticMeshComponent.h"
#include "Components/PointLightComponent.h"
#include "Dom/JsonObject.h"
#include "Engine/StaticMesh.h"
#include "Engine/World.h"
#include "EngineUtils.h"
#include "HAL/FileManager.h"
#include "LBOneFactoryRuntimeCoordinator.h"
#include "Materials/MaterialInterface.h"
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
    for (UPointLightComponent* Old : FixtureLights)
    {
        if (Old)
        {
            Old->DestroyComponent();
        }
    }
    FixtureLights.Reset();
    PlacedCount = 0;

    // Instances batch per (mesh, override-material signature): the reference
    // map authors per-actor overrides - aged RAL1023 on the crane girders,
    // brand smooth/layered sets on the guarding - and every instance of a
    // batch shares its component's materials.
    TMap<FString, UInstancedStaticMeshComponent*> ByMesh;
    int32 MissingMeshes = 0;
    int32 OverriddenBatches = 0;
    for (const TSharedPtr<FJsonValue>& Value : *Actors)
    {
        const TSharedPtr<FJsonObject> Entry = Value->AsObject();
        if (!Entry.IsValid())
        {
            continue;
        }
        const FString MeshPath = Entry->GetStringField(TEXT("mesh"));

        TArray<FString> MaterialPaths;
        const TArray<TSharedPtr<FJsonValue>>* MaterialValues = nullptr;
        if (Entry->TryGetArrayField(TEXT("mats"), MaterialValues)
            && MaterialValues)
        {
            for (const TSharedPtr<FJsonValue>& MaterialValue : *MaterialValues)
            {
                FString Path;
                MaterialValue->TryGetString(Path);
                MaterialPaths.Add(Path);
            }
        }
        FString BatchKey = MeshPath;
        for (const FString& Path : MaterialPaths)
        {
            BatchKey += TEXT("|");
            BatchKey += Path;
        }

        UInstancedStaticMeshComponent* Batch = ByMesh.FindRef(BatchKey);
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
            bool bOverrodeAny = false;
            for (int32 Slot = 0; Slot < MaterialPaths.Num(); ++Slot)
            {
                if (MaterialPaths[Slot].IsEmpty())
                {
                    continue;
                }
                if (UMaterialInterface* Material = Cast<UMaterialInterface>(
                        StaticLoadObject(UMaterialInterface::StaticClass(),
                            nullptr, *MaterialPaths[Slot])))
                {
                    Batch->SetMaterial(Slot, Material);
                    bOverrodeAny = true;
                }
            }
            if (bOverrodeAny)
            {
                ++OverriddenBatches;
            }
            Batch->RegisterComponent();
            ByMesh.Add(BatchKey, Batch);
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

        // The reference authors its light fixtures as SM_Lamp01 meshes; a
        // real point light under each one turns them from dark props into
        // the shop's actual lighting.
        if (MeshPath.EndsWith(TEXT("SM_Lamp01")))
        {
            UPointLightComponent* Fixture =
                NewObject<UPointLightComponent>(this);
            Fixture->SetupAttachment(SceneRoot);
            Fixture->SetMobility(EComponentMobility::Movable);
            // Lights-out plant: robots inspect by machine vision, so there
            // are no human task pools (owner, 2026-08-20). These fixtures
            // are the shop's only light, and with the eye adapted the
            // pool-to-floor contrast is set purely by the falloff curve -
            // intensity changes cancel out. A flat exponent falloff gives
            // the even wash the fiction wants; inverse-square always
            // paints a hot circle under the lamp.
            Fixture->bUseInverseSquaredFalloff = false;
            Fixture->LightFalloffExponent = 1.2f;
            Fixture->SetIntensity(4.0f);
            Fixture->SetAttenuationRadius(2800.0f);
            Fixture->SetSourceRadius(150.0f);
            Fixture->SetLightColor(FLinearColor(1.0f, 0.894f, 0.804f));
            Fixture->SetCastShadows(false);
            Fixture->SetWorldLocation(Instance.GetLocation()
                + FVector(0.0, 0.0, -60.0));
            Fixture->RegisterComponent();
            FixtureLights.Add(Fixture);
        }
    }

    OutReason = FString::Printf(
        TEXT("restored shop: %d instance(s) across %d batch(es), %d with "
             "authored overrides; %d mesh path(s) unresolved"),
        PlacedCount, Batches.Num(), OverriddenBatches, MissingMeshes);
    return PlacedCount > 0;
}
