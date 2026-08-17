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

    // Separate shop buildings, per the owner's 2026-08-17 direction: press,
    // weld, paint and assembly each get their own envelope and the
    // production route crosses open yard between them. The departments
    // already stand tens of metres apart, so no machine moves - only the
    // walls change.
    // Build each shop from its AUTHORED buildable bay, not from the stations
    // that happen to be commissioned. Line Boss is build-your-own: the bay is
    // the floor the player may fill, so a shop sized to today's machines is
    // too small by design - paint's bay is nearly seven times its station
    // footprint. The bays are also authored not to overlap.
    const FLBOneFactoryLayoutDefinition Layout =
        ULBOneFactoryLayoutLibrary::MakeMoorcrossWorksShellLayout();
    FBox SiteBounds(ForceInit);
    FBox DepartmentBounds[4];
    for (FBox& Box : DepartmentBounds)
    {
        Box.Init();
    }
    for (const FLBOneFactoryDepartmentBay& Bay : Layout.DepartmentBays)
    {
        const int32 Index = static_cast<int32>(Bay.Department);
        if (Index < 0 || Index >= 4)
        {
            continue;
        }
        const FVector Centre = Bay.WorldTransform.GetLocation();
        const FVector Half = Bay.SizeCm * 0.5;
        const FBox BayBox(
            FVector(Centre.X - Half.X, Centre.Y - Half.Y, 0.0),
            FVector(Centre.X + Half.X, Centre.Y + Half.Y, 0.0));
        DepartmentBounds[Index] += BayBox;
        SiteBounds += BayBox;
    }
    // The route still decides where portals go, and any station standing
    // outside its bay must still end up indoors.
    for (const FLBOneFactoryRuntimeStationStep& Step : Route)
    {
        const FVector At = Step.WorldTransform.GetLocation();
        SiteBounds += At;
        const int32 Index = static_cast<int32>(Step.Department);
        if (Index >= 0 && Index < 4)
        {
            DepartmentBounds[Index] += At;
        }
    }
    SiteBounds = SiteBounds.ExpandBy(FVector(PaddingCm, PaddingCm, 0.0));

    constexpr double WallThicknessCm = 60.0;
    const double DadoHeightCm = FMath::Min(320.0, WallHeightCm * 0.25);
    const double ClerestoryHeightCm = 420.0;
    // Walls go up in segments so an opening can be left wherever the route
    // crosses: the line leaves one shop and enters the next through a real
    // portal instead of clipping a solid wall.
    constexpr double WallSegmentCm = 400.0;
    constexpr double OpeningClearanceCm = 150.0;

    PieceCount = 0;
    for (AActor* OldDeck : RoofDecks)
    {
        if (IsValid(OldDeck))
        {
            OldDeck->Destroy();
        }
    }
    RoofDecks.Reset();

    TArray<TPair<FVector, FVector>> Legs;
    for (int32 Index = 0; Index + 1 < Route.Num(); ++Index)
    {
        Legs.Emplace(Route[Index].WorldTransform.GetLocation(),
            Route[Index + 1].WorldTransform.GetLocation());
    }
    // A segment opens only when a leg crosses its wall plane between the
    // segment's own ends. Proximity is not enough: the line runs parallel to
    // the long walls for most of each shop, and testing distance alone
    // punched out 51 segments and shredded the buildings.
    auto RouteCrossesSegment = [&Legs](const FVector& SegmentCentre,
        const bool bAlongX, const double HalfLength)
    {
        for (const TPair<FVector, FVector>& Leg : Legs)
        {
            const double FromSide = bAlongX
                ? Leg.Key.Y - SegmentCentre.Y : Leg.Key.X - SegmentCentre.X;
            const double ToSide = bAlongX
                ? Leg.Value.Y - SegmentCentre.Y
                : Leg.Value.X - SegmentCentre.X;
            if ((FromSide > 0.0) == (ToSide > 0.0))
            {
                continue;
            }
            const double Denominator = ToSide - FromSide;
            if (FMath::IsNearlyZero(Denominator))
            {
                continue;
            }
            const double Alpha = -FromSide / Denominator;
            const double CrossAlong = bAlongX
                ? FMath::Lerp(Leg.Key.X, Leg.Value.X, Alpha)
                : FMath::Lerp(Leg.Key.Y, Leg.Value.Y, Alpha);
            const double SegmentAlong =
                bAlongX ? SegmentCentre.X : SegmentCentre.Y;
            if (FMath::Abs(CrossAlong - SegmentAlong)
                <= HalfLength + OpeningClearanceCm)
            {
                return true;
            }
        }
        return false;
    };

    int32 Buildings = 0;
    int32 Openings = 0;
    for (const FBox& RawBox : DepartmentBounds)
    {
        if (!RawBox.IsValid)
        {
            continue;
        }
        // A tight skirt around the department's own machines: the wide
        // site padding made neighbouring shops overlap.
        constexpr double ShopSkirtCm = 400.0;
        const FBox Box =
            RawBox.ExpandBy(FVector(ShopSkirtCm, ShopSkirtCm, 0.0));
        const FVector BuildingMin = Box.Min;
        const FVector BuildingMax = Box.Max;
        const double BuildingX = BuildingMax.X - BuildingMin.X;
        const double BuildingY = BuildingMax.Y - BuildingMin.Y;
        const FVector BuildingCentre = Box.GetCenter();
        ++Buildings;

        for (int32 Side = 0; Side < 4; ++Side)
        {
            const bool bAlongX = Side < 2;
            const double Span = bAlongX ? BuildingX : BuildingY;
            const int32 Segments = FMath::Max(1,
                FMath::CeilToInt32(Span / WallSegmentCm));
            const double SegmentLength = Span / Segments;
            for (int32 Segment = 0; Segment < Segments; ++Segment)
            {
                const double Along = (bAlongX ? BuildingMin.X : BuildingMin.Y)
                    + SegmentLength * (Segment + 0.5);
                const FVector SegmentCentre = bAlongX
                    ? FVector(Along,
                        Side == 0 ? BuildingMin.Y : BuildingMax.Y, 0.0)
                    : FVector(Side == 2 ? BuildingMin.X : BuildingMax.X,
                        Along, 0.0);
                const FVector SegmentScale = bAlongX
                    ? FVector(SegmentLength / CubeCm,
                        WallThicknessCm / CubeCm, WallHeightCm / CubeCm)
                    : FVector(WallThicknessCm / CubeCm,
                        SegmentLength / CubeCm, WallHeightCm / CubeCm);
                const bool bOpening = RouteCrossesSegment(
                    SegmentCentre, bAlongX, SegmentLength * 0.5);

                if (!bOpening)
                {
                    FTransform WallTransform;
                    WallTransform.SetLocation(FVector(SegmentCentre.X,
                        SegmentCentre.Y, WallHeightCm * 0.5));
                    WallTransform.SetScale3D(SegmentScale);
                    if (Walls->AddInstance(WallTransform, true) != INDEX_NONE)
                    {
                        ++PieceCount;
                    }

                    FTransform DadoTransform;
                    DadoTransform.SetLocation(FVector(SegmentCentre.X,
                        SegmentCentre.Y, DadoHeightCm * 0.5));
                    DadoTransform.SetScale3D(FVector(SegmentScale.X * 1.001,
                        SegmentScale.Y * 1.001, DadoHeightCm / CubeCm));
                    if (Dado->AddInstance(DadoTransform, true) != INDEX_NONE)
                    {
                        ++PieceCount;
                    }
                }
                else
                {
                    ++Openings;
                }

                // The glazing band runs unbroken over both walls and
                // portals, so an opening reads as a doorway with a header
                // rather than a missing wall.
                FTransform GlazeTransform;
                GlazeTransform.SetLocation(FVector(SegmentCentre.X,
                    SegmentCentre.Y,
                    WallHeightCm - ClerestoryHeightCm * 0.5 - 60.0));
                GlazeTransform.SetScale3D(FVector(SegmentScale.X * 0.985,
                    SegmentScale.Y * 0.985, ClerestoryHeightCm / CubeCm));
                if (Clerestory->AddInstance(GlazeTransform, true)
                    != INDEX_NONE)
                {
                    ++PieceCount;
                }
            }
        }

        // One roof deck per shop, each on its own untagged actor so the
        // camera-height roof toggle governs them all together.
        if (AStaticMeshActor* Deck = World->SpawnActor<AStaticMeshActor>(
                AStaticMeshActor::StaticClass(),
                FVector(BuildingCentre.X, BuildingCentre.Y,
                    WallHeightCm - 50.0),
                FRotator::ZeroRotator))
        {
            if (UStaticMeshComponent* DeckMesh =
                    Deck->GetStaticMeshComponent())
            {
                DeckMesh->SetMobility(EComponentMobility::Movable);
                DeckMesh->SetStaticMesh(Cube);
                DeckMesh->SetCollisionEnabled(ECollisionEnabled::NoCollision);
                if (UMaterialInstanceDynamic* DeckMaterial =
                        UMaterialInstanceDynamic::Create(Base, this))
                {
                    const FLinearColor DeckColour =
                        FLinearColor::FromSRGBColor(
                            FColor::FromHex(TEXT("26292E")));
                    DeckMaterial->SetVectorParameterValue(TEXT("Color"),
                        DeckColour);
                    DeckMaterial->SetVectorParameterValue(TEXT("BaseColor"),
                        DeckColour);
                    DeckMesh->SetMaterial(0, DeckMaterial);
                    Materials.Add(DeckMaterial);
                }
            }
            Deck->SetActorScale3D(
                FVector(BuildingX / CubeCm, BuildingY / CubeCm, 0.2));
            RoofDecks.Add(Deck);
            ++PieceCount;
        }
    }

    if (ULBOneFactoryDevFactory::IsRoofHidden(this))
    {
        FString RoofReason;
        ULBOneFactoryDevFactory::SetRoofHidden(this, true, 900.0, RoofReason);
    }

    // One site slab under everything, so the yards between the shops read as
    // hardstanding rather than void.
    const FVector SiteCentre = SiteBounds.GetCenter();
    const FVector SiteSize = SiteBounds.GetSize();
    FTransform GroundTransform;
    GroundTransform.SetLocation(FVector(SiteCentre.X, SiteCentre.Y, -6.0));
    GroundTransform.SetScale3D(
        FVector(SiteSize.X / CubeCm, SiteSize.Y / CubeCm, 0.1));
    if (Ceiling->AddInstance(GroundTransform, true) != INDEX_NONE)
    {
        ++PieceCount;
    }

    const double SizeX = SiteSize.X;
    const double SizeY = SiteSize.Y;
    UE_LOG(LogTemp, Display,
        TEXT("LINE_BOSS_ENVELOPE buildings=%d routeOpenings=%d"),
        Buildings, Openings);

    OutReason = FString::Printf(
        TEXT("site %.0f x %.0f cm, shop height %.0f, %d piece(s) across separate shop buildings"),
        SizeX, SizeY, WallHeightCm, PieceCount);
    return true;
}
