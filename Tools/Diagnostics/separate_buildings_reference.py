"""Rewrite the envelope actor to build one building per department."""
import io

P = (r"C:/Users/greg_/Projects/LineBossCarFactory_Unreal 5.8/Source/"
     r"LineBossCarFactory/LBOneFactoryDevEnvelopeActor.cpp")
text = io.open(P, encoding="utf-8").read()

start = text.index("    FBox Bounds(ForceInit);")
end = text.index('    OutReason = FString::Printf(')

NEW = r'''    // Separate shop buildings, per the owner's 2026-08-17 direction: press,
    // weld, paint and assembly each get their own envelope and the
    // production route crosses open yard between them. The departments
    // already stand tens of metres apart, so no machine moves - only the
    // walls change.
    FBox SiteBounds(ForceInit);
    FBox DepartmentBounds[4];
    for (FBox& Box : DepartmentBounds)
    {
        Box.Init();
    }
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
    constexpr double OpeningClearanceCm = 800.0;

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
    auto RouteCrosses = [&Legs](const FVector& SegmentCentre)
    {
        const FVector Flat(SegmentCentre.X, SegmentCentre.Y, 0.0);
        for (const TPair<FVector, FVector>& Leg : Legs)
        {
            const FVector Closest = FMath::ClosestPointOnSegment(Flat,
                FVector(Leg.Key.X, Leg.Key.Y, 0.0),
                FVector(Leg.Value.X, Leg.Value.Y, 0.0));
            if (FVector::Dist(Closest, Flat) < OpeningClearanceCm)
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
        const FBox Box = RawBox.ExpandBy(FVector(PaddingCm, PaddingCm, 0.0));
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
                const bool bOpening = RouteCrosses(SegmentCentre);

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

'''

text = text[:start] + NEW + text[end:]

# The summary line should now describe the site, not a single hall.
text = text.replace(
    'TEXT("envelope %.0f x %.0f cm, height %.0f, %d piece(s)"),',
    'TEXT("site %.0f x %.0f cm, shop height %.0f, %d piece(s) across '
    'separate shop buildings"),', 1)

io.open(P, "w", encoding="utf-8").write(text)
print("envelope rewritten for separate buildings")
