#include "LBFactoryAGVInfrastructure.h"
#include "LBFactoryFloorMarkingComponent.h"

#include "Components/BoxComponent.h"
#include "Components/StaticMeshComponent.h"
#include "Materials/MaterialInstanceDynamic.h"
#include "UObject/ConstructorHelpers.h"

ALBFactoryAGVInfrastructure::ALBFactoryAGVInfrastructure()
{
    PrimaryActorTick.bCanEverTick = false;
    SceneRoot = CreateDefaultSubobject<USceneComponent>(TEXT("SceneRoot"));
    SetRootComponent(SceneRoot);
    MarkerBody = CreateDefaultSubobject<UStaticMeshComponent>(TEXT("MarkerBody"));
    MarkerBody->SetupAttachment(SceneRoot);
    MarkerBody->SetCollisionEnabled(ECollisionEnabled::NoCollision);
    MarkerBody->SetCanEverAffectNavigation(false);
    FloorMarking = CreateDefaultSubobject<UStaticMeshComponent>(TEXT("FloorMarking"));
    FloorMarking->SetupAttachment(SceneRoot);
    FloorMarking->SetCollisionEnabled(ECollisionEnabled::NoCollision);
    FloorMarking->SetCanEverAffectNavigation(false);
    FloorMarking->SetCastShadow(false);
    SafetyMarkings = CreateDefaultSubobject<ULBFactoryFloorMarkingComponent>(TEXT("InfrastructureSafetyMarkings"));
    SafetyMarkings->SetupAttachment(SceneRoot);
    PlacementEnvelope = CreateDefaultSubobject<UBoxComponent>(TEXT("PlacementEnvelope"));
    PlacementEnvelope->SetupAttachment(SceneRoot);
    PlacementEnvelope->SetCollisionProfileName(TEXT("BlockAll"));
    SelectionProxy = CreateDefaultSubobject<UBoxComponent>(TEXT("SelectionProxy"));
    SelectionProxy->SetupAttachment(SceneRoot);
    SelectionProxy->SetCollisionEnabled(ECollisionEnabled::QueryOnly);
    SelectionProxy->SetCollisionObjectType(ECC_WorldDynamic);
    SelectionProxy->SetCollisionResponseToAllChannels(ECR_Ignore);
    SelectionProxy->SetCollisionResponseToChannel(ECC_Visibility, ECR_Block);
    SelectionProxy->SetCanEverAffectNavigation(false);
    static ConstructorHelpers::FObjectFinder<UStaticMesh> Cube(TEXT("/Engine/BasicShapes/Cube.Cube"));
    if (Cube.Succeeded())
    {
        MarkerBody->SetStaticMesh(Cube.Object);
        FloorMarking->SetStaticMesh(Cube.Object);
    }
}

FVector ALBFactoryAGVInfrastructure::GetPlacementHalfExtentForType(
    const ELBFactoryAGVInfrastructureType Type)
{
    switch (Type)
    {
    case ELBFactoryAGVInfrastructureType::ChargingStation: return FVector(190.0f, 135.0f, 20.0f);
    case ELBFactoryAGVInfrastructureType::WaitPoint: return FVector(140.0f, 110.0f, 10.0f);
    case ELBFactoryAGVInfrastructureType::RouteWaypoint: return FVector(35.0f, 35.0f, 5.0f);
    case ELBFactoryAGVInfrastructureType::PressTrainHandoff: return FVector(190.0f, 135.0f, 10.0f);
    case ELBFactoryAGVInfrastructureType::AGVRouteSegment: return FVector(250.0f, 115.0f, 2.0f);
    case ELBFactoryAGVInfrastructureType::PedestrianWalkway: return FVector(250.0f, 75.0f, 2.0f);
    case ELBFactoryAGVInfrastructureType::PedestrianCrossing: return FVector(115.0f, 75.0f, 2.0f);
    case ELBFactoryAGVInfrastructureType::SafetyFence: return FVector(250.0f, 10.0f, 100.0f);
    default: return FVector(100.0f, 75.0f, 15.0f);
    }
}

bool ALBFactoryAGVInfrastructure::Configure(const FName InId,
    const ELBFactoryAGVInfrastructureType InType, const int32 InTrainIndex)
{
    if (InId.IsNone()) return false;
    const bool bHandoff = InType == ELBFactoryAGVInfrastructureType::PressTrainHandoff;
    if ((bHandoff && !FMath::IsWithinInclusive(InTrainIndex, 0, 3))
        || (!bHandoff && InTrainIndex != INDEX_NONE)) return false;

    InfrastructureId = InId;
    InfrastructureType = InType;
    TrainIndex = InTrainIndex;
    Provenance = ELBFactoryInfrastructureProvenance::PlayerPlaced;

    const FVector HalfExtent = GetPlacementHalfExtentForType(InType);
    PlacementEnvelope->SetBoxExtent(HalfExtent);
    PlacementEnvelope->SetRelativeLocation(FVector(0.0f, 0.0f, HalfExtent.Z));
    const float SelectionHalfHeight = FMath::Max(20.0f, HalfExtent.Z);
    SelectionProxy->SetBoxExtent(FVector(HalfExtent.X, HalfExtent.Y, SelectionHalfHeight));
    SelectionProxy->SetRelativeLocation(FVector(0.0f, 0.0f, SelectionHalfHeight));
    const bool bPaintOnly = InType == ELBFactoryAGVInfrastructureType::RouteWaypoint
        || InType == ELBFactoryAGVInfrastructureType::AGVRouteSegment
        || InType == ELBFactoryAGVInfrastructureType::PedestrianWalkway
        || InType == ELBFactoryAGVInfrastructureType::PedestrianCrossing;
    // Painted routes and walkways are planning/safety markings, not raised equipment
    // or invisible walls. Hide the old full-height marker cube entirely.
    MarkerBody->SetVisibility(!bPaintOnly);
    // Keep physical collision only on equipment, handoffs and guarding.
    PlacementEnvelope->SetCollisionEnabled(bPaintOnly
        ? ECollisionEnabled::NoCollision : ECollisionEnabled::QueryAndPhysics);
    MarkerBody->SetRelativeScale3D(HalfExtent / 50.0f);
    MarkerBody->SetRelativeLocation(FVector(0.0f, 0.0f, HalfExtent.Z));
    // Engine cube is 100 cm. Keep the paint 1 cm thick and inset within the validated envelope.
    FVector MarkingHalfExtent(FMath::Max(20.0f, HalfExtent.X - 8.0f),
        FMath::Max(20.0f, HalfExtent.Y - 8.0f), 0.5f);
    if (InType == ELBFactoryAGVInfrastructureType::AGVRouteSegment)
    {
        // A route is a centreline, not a conveyor bed. Preserve the 2.3 m logical
        // navigation lane in PlacementEnvelope while giving its paint a 30 cm width
        // that remains readable from the 1280x720 management overview.
        MarkingHalfExtent.Y = 15.0f;
    }
    FloorMarking->SetRelativeScale3D(MarkingHalfExtent / 50.0f);
    FloorMarking->SetRelativeLocation(FVector(0.0f, 0.0f, 0.6f));
    const TCHAR* ColourHex = TEXT("2167A5");
    if (InType == ELBFactoryAGVInfrastructureType::PedestrianWalkway) ColourHex = TEXT("3A9B66");
    else if (InType == ELBFactoryAGVInfrastructureType::PedestrianCrossing) ColourHex = TEXT("F2C94C");
    else if (InType == ELBFactoryAGVInfrastructureType::SafetyFence) ColourHex = TEXT("E4B223");
    FloorMarkingColour = FLinearColor::FromSRGBColor(FColor::FromHex(ColourHex));
    if (UMaterialInstanceDynamic* PaintMaterial = FloorMarking->CreateAndSetMaterialInstanceDynamic(0))
    {
        PaintMaterial->SetVectorParameterValue(TEXT("Color"), FloorMarkingColour);
    }
    SafetyMarkings->ClearMarkings();
    const FVector2D PaintExtent(MarkingHalfExtent.X, MarkingHalfExtent.Y);
    switch (InType)
    {
    case ELBFactoryAGVInfrastructureType::AGVRouteSegment:
        // The navigation envelope remains 2.3 m wide; two dashed blue edge guides make
        // that lane legible without turning it into a raised conveyor.
        SafetyMarkings->AddDashedLine(FVector2D(-HalfExtent.X + 10.0f, -HalfExtent.Y + 14.0f),
            FVector2D(HalfExtent.X - 10.0f, -HalfExtent.Y + 14.0f), 0.8f,
            20.0f, 62.0f, 42.0f, ELBFactoryFloorMarkingSemantic::VehicleLane, 0.8f);
        SafetyMarkings->AddDashedLine(FVector2D(-HalfExtent.X + 10.0f, HalfExtent.Y - 14.0f),
            FVector2D(HalfExtent.X - 10.0f, HalfExtent.Y - 14.0f), 0.8f,
            20.0f, 62.0f, 42.0f, ELBFactoryFloorMarkingSemantic::VehicleLane, 0.8f);
        break;
    case ELBFactoryAGVInfrastructureType::PedestrianWalkway:
        SafetyMarkings->AddRectangleOutline(FVector2D::ZeroVector, PaintExtent, 0.8f,
            16.0f, ELBFactoryFloorMarkingSemantic::PedestrianCrossing, 0.8f);
        break;
    case ELBFactoryAGVInfrastructureType::PedestrianCrossing:
        // White zebra bars sit over the yellow warning tile and remain readable at
        // management-camera distance.
        for (float X = -PaintExtent.X + 18.0f; X <= PaintExtent.X - 18.0f; X += 42.0f)
        {
            SafetyMarkings->AddFilledRectangle(FVector2D(X, 0.0f),
                FVector2D(11.0f, FMath::Max(10.0f, PaintExtent.Y - 9.0f)), 0.8f,
                ELBFactoryFloorMarkingSemantic::PedestrianCrossing, 0.8f);
        }
        break;
    case ELBFactoryAGVInfrastructureType::PressTrainHandoff:
        SafetyMarkings->AddDiagonalHatching(FVector2D::ZeroVector,
            FVector2D(HalfExtent.X - 16.0f, HalfExtent.Y - 16.0f), 0.5f,
            14.0f, 60.0f, ELBFactoryFloorMarkingSemantic::KeepClearHatch, 0.8f);
        SafetyMarkings->AddRectangleOutline(FVector2D::ZeroVector,
            FVector2D(HalfExtent.X, HalfExtent.Y), 0.8f, 12.0f,
            ELBFactoryFloorMarkingSemantic::ServiceEnvelope, 1.0f);
        break;
    case ELBFactoryAGVInfrastructureType::ChargingStation:
    case ELBFactoryAGVInfrastructureType::WaitPoint:
        SafetyMarkings->AddRectangleOutline(FVector2D::ZeroVector,
            FVector2D(HalfExtent.X, HalfExtent.Y), 0.8f, 12.0f,
            ELBFactoryFloorMarkingSemantic::ServiceEnvelope, 1.0f);
        break;
    default:
        break;
    }
    Tags = { TEXT("LB.PlayerBuilt.Infrastructure"), FName(*FString::Printf(TEXT("LB.Infrastructure.%s"), *InfrastructureId.ToString())) };
    RefreshProvenanceTags();
    return true;
}

void ALBFactoryAGVInfrastructure::RefreshProvenanceTags()
{
    Tags.Remove(TEXT("LB.FactoryBuilder.Automatic"));
    Tags.Remove(TEXT("LB.FactoryBuilder.PlayerEditedAutomatic"));
    if (Provenance == ELBFactoryInfrastructureProvenance::Automatic)
        Tags.AddUnique(TEXT("LB.FactoryBuilder.Automatic"));
    else if (Provenance == ELBFactoryInfrastructureProvenance::PlayerEditedAutomatic)
        Tags.AddUnique(TEXT("LB.FactoryBuilder.PlayerEditedAutomatic"));
}

void ALBFactoryAGVInfrastructure::MarkAutomaticallyGenerated()
{
    Provenance = ELBFactoryInfrastructureProvenance::Automatic;
    RefreshProvenanceTags();
}

void ALBFactoryAGVInfrastructure::MarkPlayerEdited()
{
    if (Provenance == ELBFactoryInfrastructureProvenance::Automatic)
        Provenance = ELBFactoryInfrastructureProvenance::PlayerEditedAutomatic;
    RefreshProvenanceTags();
}

void ALBFactoryAGVInfrastructure::SetSelectionHighlighted(const bool bHighlighted)
{
    if (MarkerBody) MarkerBody->SetRenderCustomDepth(bHighlighted);
    if (FloorMarking) FloorMarking->SetRenderCustomDepth(bHighlighted);
}

FVector ALBFactoryAGVInfrastructure::GetPlacementHalfExtentCm() const
{
    return PlacementEnvelope ? PlacementEnvelope->GetUnscaledBoxExtent() : FVector::ZeroVector;
}

bool ALBFactoryAGVInfrastructure::HasFloorMarkingPresentation() const
{
    return FloorMarking && FloorMarking->GetStaticMesh()
        && FloorMarking->GetCollisionEnabled() == ECollisionEnabled::NoCollision
        && !FloorMarking->CanEverAffectNavigation()
        && !FloorMarking->CastShadow;
}

FVector ALBFactoryAGVInfrastructure::GetFloorMarkingDimensionsCm() const
{
    return FloorMarking && FloorMarking->GetStaticMesh()
        ? FloorMarking->GetComponentScale() * 100.0f : FVector::ZeroVector;
}

FLBFactoryAGVInfrastructureSaveState ALBFactoryAGVInfrastructure::CaptureSaveState() const
{
    FLBFactoryAGVInfrastructureSaveState State;
    State.InfrastructureId = InfrastructureId;
    State.Type = InfrastructureType;
    State.WorldTransform = GetActorTransform();
    State.TrainIndex = TrainIndex;
    State.Provenance = Provenance;
    return State;
}

bool ALBFactoryAGVInfrastructure::RestoreSaveState(const FLBFactoryAGVInfrastructureSaveState& State)
{
    if ((State.Version != 1 && State.Version != 2) || !State.WorldTransform.IsValid()
        || !State.WorldTransform.GetScale3D().Equals(FVector::OneVector, 0.001f)
        || !Configure(State.InfrastructureId, State.Type, State.TrainIndex)) return false;
    Provenance = State.Version >= 2 ? State.Provenance : ELBFactoryInfrastructureProvenance::PlayerPlaced;
    RefreshProvenanceTags();
    SetActorTransform(State.WorldTransform);
    return true;
}

FName ALBFactoryAGVInfrastructure::GetTrainLabel() const
{
    return FMath::IsWithinInclusive(TrainIndex, 0, 3)
        ? FName(*FString::Printf(TEXT("TRAIN %c"), TCHAR('A' + TrainIndex))) : NAME_None;
}
