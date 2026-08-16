#include "LBOneFactoryDevEnvelopeActor.h"

#include "Components/InstancedStaticMeshComponent.h"
#include "Engine/StaticMesh.h"
#include "Engine/StaticMeshActor.h"
#include "Engine/World.h"
#include "EngineUtils.h"
#include "LBOneFactoryDevFactoryCommands.h"
#include "LBOneFactoryRuntimeCoordinator.h"
#include "Materials/MaterialInstanceDynamic.h"
#include "Materials/MaterialInterface.h"

namespace LBOneFactoryDevEnvelopePrivate
{
    const TCHAR* const CubePath = TEXT("/Engine/BasicShapes/Cube.Cube");
    const TCHAR* const BasicMaterialPath =
        TEXT("/Engine/BasicShapes/BasicShapeMaterial.BasicShapeMaterial");

    /** Engine Cube is 100 cm, so a scale value is also a size in centimetres. */
    constexpr double CubeCm = 100.0;
}

ALBOneFactoryDevEnvelopeActor::ALBOneFactoryDevEnvelopeActor()
{
    PrimaryActorTick.bCanEverTick = false;
    SetReplicates(false);
    SetActorEnableCollision(false);

    SceneRoot = CreateDefaultSubobject<USceneComponent>(TEXT("SceneRoot"));
    SceneRoot->SetMobility(EComponentMobility::Movable);
    SetRootComponent(SceneRoot);

    Walls = MakeBatch(TEXT("Env_Walls"), TEXT("6B7078"), 0.75f);
    Dado = MakeBatch(TEXT("Env_Dado"), TEXT("3C4650"), 0.6f);
    Ceiling = MakeBatch(TEXT("Env_Ceiling"), TEXT("4A4F56"), 0.85f);
    Clerestory = MakeBatch(TEXT("Env_Clerestory"), TEXT("E8F0FA"), 0.2f);

    Tags.AddUnique(GetEnvelopeTag());
    Tags.AddUnique(TEXT("LB.Environment.VisualOnly"));
    Tags.AddUnique(TEXT("LB.NotProcessWIP"));
}

FName ALBOneFactoryDevEnvelopeActor::GetEnvelopeTag()
{
    return FName(TEXT("LB.OneFactory.DevEnvelope"));
}

UInstancedStaticMeshComponent* ALBOneFactoryDevEnvelopeActor::MakeBatch(
    const TCHAR* Name, const TCHAR* HexColour, const float Roughness)
{
    UInstancedStaticMeshComponent* Batch =
        CreateDefaultSubobject<UInstancedStaticMeshComponent>(FName(Name));
    if (!Batch)
    {
        return nullptr;
    }
    Batch->SetupAttachment(SceneRoot);
    Batch->SetMobility(EComponentMobility::Movable);
    Batch->SetCollisionEnabled(ECollisionEnabled::NoCollision);
    Batch->SetCollisionResponseToAllChannels(ECR_Ignore);
    Batch->SetGenerateOverlapEvents(false);
    Batch->SetCanEverAffectNavigation(false);
    Batch->SetReceivesDecals(false);
    return Batch;
}

bool ALBOneFactoryDevEnvelopeActor::BuildFromRoute(const double PaddingCm,
    const double WallHeightCm, FString& OutReason)
{
    using namespace LBOneFactoryDevEnvelopePrivate;

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

    UStaticMesh* Cube = Cast<UStaticMesh>(
        StaticLoadObject(UStaticMesh::StaticClass(), nullptr, CubePath));
    UMaterialInterface* Base = Cast<UMaterialInterface>(
        StaticLoadObject(UMaterialInterface::StaticClass(), nullptr,
            BasicMaterialPath));
    if (!Cube || !Base)
    {
        OutReason = TEXT("COULD NOT RESOLVE CUBE OR BASE MATERIAL");
        return false;
    }

    struct FBatchSetup
    {
        UInstancedStaticMeshComponent* Component;
        const TCHAR* Hex;
    };
    const FBatchSetup Setups[] = {
        { Walls, TEXT("6B7078") },
        { Dado, TEXT("3C4650") },
        { Ceiling, TEXT("9B9C98") },
        { Clerestory, TEXT("E8F0FA") },
    };
    Materials.Reset();
    for (const FBatchSetup& Setup : Setups)
    {
        if (!Setup.Component)
        {
            OutReason = TEXT("ENVELOPE BATCH MISSING");
            return false;
        }
        UMaterialInstanceDynamic* Material =
            UMaterialInstanceDynamic::Create(Base, this);
        if (!Material)
        {
            OutReason = TEXT("COULD NOT CREATE ENVELOPE MATERIAL");
            return false;
        }
        const FLinearColor Colour =
            FLinearColor::FromSRGBColor(FColor::FromHex(Setup.Hex));
        Material->SetVectorParameterValue(TEXT("Color"), Colour);
        Material->SetVectorParameterValue(TEXT("BaseColor"), Colour);
        Setup.Component->ClearInstances();
        Setup.Component->SetStaticMesh(Cube);
        Setup.Component->SetMaterial(0, Material);
        Materials.Add(Material);
    }

    FBox Bounds(ForceInit);
    for (const FLBOneFactoryRuntimeStationStep& Step : Route)
    {
        Bounds += Step.WorldTransform.GetLocation();
    }
    Bounds = Bounds.ExpandBy(FVector(PaddingCm, PaddingCm, 0.0));

    const FVector Min = Bounds.Min;
    const FVector Max = Bounds.Max;
    const double SizeX = Max.X - Min.X;
    const double SizeY = Max.Y - Min.Y;
    const FVector Centre = Bounds.GetCenter();

    constexpr double WallThicknessCm = 60.0;
    const double DadoHeightCm = FMath::Min(320.0, WallHeightCm * 0.25);
    const double ClerestoryHeightCm = 420.0;

    PieceCount = 0;

    // Four walls. Each is one stretched cube, with a darker dado band along the
    // bottom and a bright glazing strip at the top so a flat wall still has
    // horizontal banding to read against.
    struct FWall
    {
        FVector Centre;
        FVector Scale;
    };
    const FWall WallSpecs[] = {
        // Along X at each Y extreme.
        { FVector(Centre.X, Min.Y, WallHeightCm * 0.5),
          FVector(SizeX / CubeCm, WallThicknessCm / CubeCm,
              WallHeightCm / CubeCm) },
        { FVector(Centre.X, Max.Y, WallHeightCm * 0.5),
          FVector(SizeX / CubeCm, WallThicknessCm / CubeCm,
              WallHeightCm / CubeCm) },
        // Along Y at each X extreme.
        { FVector(Min.X, Centre.Y, WallHeightCm * 0.5),
          FVector(WallThicknessCm / CubeCm, SizeY / CubeCm,
              WallHeightCm / CubeCm) },
        { FVector(Max.X, Centre.Y, WallHeightCm * 0.5),
          FVector(WallThicknessCm / CubeCm, SizeY / CubeCm,
              WallHeightCm / CubeCm) },
    };

    for (const FWall& Wall : WallSpecs)
    {
        FTransform WallTransform;
        WallTransform.SetLocation(Wall.Centre);
        WallTransform.SetScale3D(Wall.Scale);
        if (Walls->AddInstance(WallTransform, true) != INDEX_NONE)
        {
            ++PieceCount;
        }

        // Dado sits just inboard of the wall face at floor level.
        FTransform DadoTransform;
        DadoTransform.SetLocation(
            FVector(Wall.Centre.X, Wall.Centre.Y, DadoHeightCm * 0.5));
        DadoTransform.SetScale3D(FVector(
            Wall.Scale.X * 1.001, Wall.Scale.Y * 1.001,
            DadoHeightCm / CubeCm));
        if (Dado->AddInstance(DadoTransform, true) != INDEX_NONE)
        {
            ++PieceCount;
        }

        // Glazing strip just below the eaves.
        FTransform GlazeTransform;
        GlazeTransform.SetLocation(FVector(Wall.Centre.X, Wall.Centre.Y,
            WallHeightCm - ClerestoryHeightCm * 0.5 - 60.0));
        GlazeTransform.SetScale3D(FVector(
            Wall.Scale.X * 0.985, Wall.Scale.Y * 0.985,
            ClerestoryHeightCm / CubeCm));
        if (Clerestory->AddInstance(GlazeTransform, true) != INDEX_NONE)
        {
            ++PieceCount;
        }
    }

    // The roof deck sits just under the eaves on its own untagged actor:
    // the camera-height toggle in FrameProductionLine hides it for
    // management shots looking in from above and restores it for
    // floor-level views, which otherwise top out in black void above the
    // restored shop's trusses.
    if (RoofDeck)
    {
        RoofDeck->Destroy();
        RoofDeck = nullptr;
    }
    if (AStaticMeshActor* Deck = World->SpawnActor<AStaticMeshActor>(
            AStaticMeshActor::StaticClass(),
            FVector(Centre.X, Centre.Y, WallHeightCm - 50.0),
            FRotator::ZeroRotator))
    {
        if (UStaticMeshComponent* DeckMesh = Deck->GetStaticMeshComponent())
        {
            DeckMesh->SetMobility(EComponentMobility::Movable);
            DeckMesh->SetStaticMesh(Cube);
            DeckMesh->SetCollisionEnabled(ECollisionEnabled::NoCollision);
            if (UMaterialInstanceDynamic* DeckMaterial =
                    UMaterialInstanceDynamic::Create(Base, this))
            {
                const FLinearColor DeckColour =
                    FLinearColor::FromSRGBColor(FColor::FromHex(TEXT("26292E")));
                DeckMaterial->SetVectorParameterValue(TEXT("Color"), DeckColour);
                DeckMaterial->SetVectorParameterValue(TEXT("BaseColor"),
                    DeckColour);
                DeckMesh->SetMaterial(0, DeckMaterial);
                Materials.Add(DeckMaterial);
            }
        }
        Deck->SetActorScale3D(FVector(SizeX / CubeCm, SizeY / CubeCm, 0.2));
        RoofDeck = Deck;
        ++PieceCount;

        // A rebuild must not resurrect the roof over a management camera:
        // re-apply the world's current roof state to the fresh deck.
        if (ULBOneFactoryDevFactory::IsRoofHidden(this))
        {
            FString RoofReason;
            ULBOneFactoryDevFactory::SetRoofHidden(this, true, 900.0,
                RoofReason);
        }
    }

    // A floor slab as well. The map's authored floor is smaller than the
    // configured station route, so stations at the far ends of Press and
    // Assembly stand over void and render as black holes with machines
    // apparently floating. This covers the whole routed footprint, sitting just
    // below the authored floor so it fills the gaps without z-fighting it.
    FTransform FloorTransform;
    FloorTransform.SetLocation(FVector(Centre.X, Centre.Y, -6.0));
    FloorTransform.SetScale3D(
        FVector(SizeX / CubeCm, SizeY / CubeCm, 0.1));
    if (Ceiling->AddInstance(FloorTransform, true) != INDEX_NONE)
    {
        ++PieceCount;
    }

    OutReason = FString::Printf(
        TEXT("envelope %.0f x %.0f cm, height %.0f, %d piece(s)"),
        SizeX, SizeY, WallHeightCm, PieceCount);
    return true;
}
