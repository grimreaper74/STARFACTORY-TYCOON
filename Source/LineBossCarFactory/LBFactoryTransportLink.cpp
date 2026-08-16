#include "LBFactoryTransportLink.h"
#include "Components/HierarchicalInstancedStaticMeshComponent.h"
#include "Components/SplineComponent.h"
#include "Materials/MaterialInstanceDynamic.h"
#include "UObject/ConstructorHelpers.h"

ALBFactoryTransportLink::ALBFactoryTransportLink()
{
    PrimaryActorTick.bCanEverTick = false;
    RouteSpline = CreateDefaultSubobject<USplineComponent>(TEXT("TransportRoute"));
    SetRootComponent(RouteSpline);

    SideRails = CreateDefaultSubobject<UHierarchicalInstancedStaticMeshComponent>(TEXT("SideRails"));
    SideRails->SetupAttachment(RouteSpline);
    SideRails->SetCollisionProfileName(TEXT("BlockAll"));

    RollerOrBeltDeck = CreateDefaultSubobject<UHierarchicalInstancedStaticMeshComponent>(TEXT("RollerOrBeltDeck"));
    RollerOrBeltDeck->SetupAttachment(RouteSpline);
    RollerOrBeltDeck->SetCollisionProfileName(TEXT("BlockAll"));

    SupportLegs = CreateDefaultSubobject<UHierarchicalInstancedStaticMeshComponent>(TEXT("SupportLegs"));
    SupportLegs->SetupAttachment(RouteSpline);
    SupportLegs->SetCollisionProfileName(TEXT("BlockAll"));

    static ConstructorHelpers::FObjectFinder<UStaticMesh> Cube(TEXT("/Engine/BasicShapes/Cube.Cube"));
    static ConstructorHelpers::FObjectFinder<UStaticMesh> Cylinder(TEXT("/Engine/BasicShapes/Cylinder.Cylinder"));
    if (Cube.Succeeded())
    {
        SideRails->SetStaticMesh(Cube.Object);
        SupportLegs->SetStaticMesh(Cube.Object);
    }
    if (Cylinder.Succeeded()) RollerOrBeltDeck->SetStaticMesh(Cylinder.Object);
}

bool ALBFactoryTransportLink::Configure(
    ULBFactoryProcessPortComponent* Source, ULBFactoryProcessPortComponent* Target)
{
    if (!Source || !Target || Source->Direction != ELBFactoryPortDirection::Output
        || Target->Direction != ELBFactoryPortDirection::Input) return false;
    SourcePort = Source;
    TargetPort = Target;
    TransportKind = Source->TransportKind;
    TransferredUnits = 0;
    SetActorLocation(FVector::ZeroVector);
    RouteSpline->ClearSplinePoints(false);
    const FVector Start = Source->GetComponentLocation();
    const FVector End = Target->GetComponentLocation();
    RouteSpline->AddSplinePoint(Start, ESplineCoordinateSpace::World, false);
    if (!FMath::IsNearlyEqual(Start.X, End.X, 1.0f)
        && !FMath::IsNearlyEqual(Start.Y, End.Y, 1.0f))
    {
        RouteSpline->AddSplinePoint(FVector(End.X, Start.Y, FMath::Max(Start.Z, End.Z)),
            ESplineCoordinateSpace::World, false);
    }
    RouteSpline->AddSplinePoint(End, ESplineCoordinateSpace::World, false);
    RouteSpline->UpdateSpline();
    RebuildVisuals();
    Tags.AddUnique(TEXT("LB.FactoryBuilder.AutoTransportLink"));
    return true;
}

void ALBFactoryTransportLink::RebuildVisuals()
{
    SideRails->ClearInstances();
    RollerOrBeltDeck->ClearInstances();
    SupportLegs->ClearInstances();
    const bool bFloorPaintOnly = TransportKind == ELBFactoryTransportKind::AGVHandoff;
    SideRails->SetCollisionEnabled(bFloorPaintOnly
        ? ECollisionEnabled::NoCollision : ECollisionEnabled::QueryAndPhysics);
    SideRails->SetCanEverAffectNavigation(!bFloorPaintOnly);
    RollerOrBeltDeck->SetCollisionEnabled(bFloorPaintOnly
        ? ECollisionEnabled::NoCollision : ECollisionEnabled::QueryAndPhysics);
    RollerOrBeltDeck->SetCanEverAffectNavigation(!bFloorPaintOnly);
    SupportLegs->SetCollisionEnabled(bFloorPaintOnly
        ? ECollisionEnabled::NoCollision : ECollisionEnabled::QueryAndPhysics);
    SupportLegs->SetCanEverAffectNavigation(!bFloorPaintOnly);
    const int32 PointCount = RouteSpline->GetNumberOfSplinePoints();
    for (int32 Index = 0; Index + 1 < PointCount; ++Index)
    {
        AddStraightVisualSection(
            RouteSpline->GetLocationAtSplinePoint(Index, ESplineCoordinateSpace::World),
            RouteSpline->GetLocationAtSplinePoint(Index + 1, ESplineCoordinateSpace::World));
    }
}

void ALBFactoryTransportLink::AddStraightVisualSection(const FVector& Start, const FVector& End)
{
    const FVector Delta = End - Start;
    const float Length = Delta.Size2D();
    if (Length < 10.0f) return;

    const FVector Along = FVector(Delta.X, Delta.Y, 0.0f).GetSafeNormal();
    const FVector Across(-Along.Y, Along.X, 0.0f);
    const FVector Mid = (Start + End) * 0.5f;
    constexpr float ConveyorWidth = 180.0f;
    constexpr float RailThickness = 10.0f;
    constexpr float RailHeight = 30.0f;
    constexpr float DeckHeight = 14.0f;
    const FRotator AlongRotation = Along.Rotation();

    // AGVs travel on the factory floor; they do not need a physical conveyor. Earlier
    // builds fell through to the belt-conveyor branch and constructed hundreds of rollers
    // between the lorry and coil cells. Represent the logical handoff as one narrow painted
    // centreline while retaining the full spline for routing and save data.
    if (TransportKind == ELBFactoryTransportKind::AGVHandoff)
    {
        const FVector FloorMid(Mid.X, Mid.Y, 0.5f);
        SideRails->AddInstanceWorldSpace(FTransform(AlongRotation, FloorMid,
            FVector(Length / 100.0f, 0.12f, 0.01f)));
        return;
    }

    for (float Side : {-1.0f, 1.0f})
    {
        const FVector RailLocation = Mid + Across * Side * (ConveyorWidth * 0.5f);
        SideRails->AddInstanceWorldSpace(FTransform(AlongRotation, RailLocation,
            FVector(Length / 100.0f, RailThickness / 100.0f, RailHeight / 100.0f)));
    }

    if (TransportKind == ELBFactoryTransportKind::RollerConveyor
        || TransportKind == ELBFactoryTransportKind::PanelTransfer)
    {
        const int32 RollerCount = FMath::Max(2, FMath::FloorToInt(Length / 35.0f));
        const FQuat RollerRotation = FRotationMatrix::MakeFromX(Across).ToQuat()
            * FQuat(FVector::RightVector, HALF_PI);
        for (int32 RollerIndex = 0; RollerIndex <= RollerCount; ++RollerIndex)
        {
            const float Alpha = static_cast<float>(RollerIndex) / static_cast<float>(RollerCount);
            const FVector RollerLocation = FMath::Lerp(Start, End, Alpha);
            RollerOrBeltDeck->AddInstanceWorldSpace(FTransform(RollerRotation, RollerLocation,
                FVector(0.12f, 0.12f, ConveyorWidth / 100.0f)));
        }
    }
    else
    {
        // Belt routes use closely packed dark rollers to read as a continuous driven belt.
        const int32 BeltCount = FMath::Max(2, FMath::FloorToInt(Length / 18.0f));
        const FQuat BeltRotation = FRotationMatrix::MakeFromX(Across).ToQuat()
            * FQuat(FVector::RightVector, HALF_PI);
        for (int32 BeltIndex = 0; BeltIndex <= BeltCount; ++BeltIndex)
        {
            const float Alpha = static_cast<float>(BeltIndex) / static_cast<float>(BeltCount);
            RollerOrBeltDeck->AddInstanceWorldSpace(FTransform(BeltRotation,
                FMath::Lerp(Start, End, Alpha) - FVector(0.0f, 0.0f, DeckHeight),
                FVector(0.18f, 0.18f, ConveyorWidth / 100.0f)));
        }
    }

    const int32 SupportCount = FMath::Max(1, FMath::FloorToInt(Length / 200.0f));
    const float SupportHeight = FMath::Max(20.0f, Mid.Z);
    for (int32 SupportIndex = 0; SupportIndex <= SupportCount; ++SupportIndex)
    {
        const float Alpha = static_cast<float>(SupportIndex) / static_cast<float>(SupportCount);
        const FVector Centre = FMath::Lerp(Start, End, Alpha);
        for (float Side : {-1.0f, 1.0f})
        {
            const FVector LegLocation = Centre + Across * Side * (ConveyorWidth * 0.42f)
                - FVector(0.0f, 0.0f, SupportHeight * 0.5f);
            SupportLegs->AddInstanceWorldSpace(FTransform(FRotator::ZeroRotator, LegLocation,
                FVector(0.12f, 0.12f, SupportHeight / 100.0f)));
        }
    }
}

bool ALBFactoryTransportLink::TryTransferUnits(int32 Quantity)
{
    if (Quantity <= 0 || !IsValid(SourcePort) || !IsValid(TargetPort)) return false;
    TransferredUnits += Quantity;
    return true;
}
