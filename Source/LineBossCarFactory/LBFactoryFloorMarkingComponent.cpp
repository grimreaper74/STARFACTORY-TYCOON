#include "LBFactoryFloorMarkingComponent.h"

#include "Components/HierarchicalInstancedStaticMeshComponent.h"
#include "Materials/MaterialInstanceDynamic.h"
#include "Materials/MaterialInterface.h"
#include "UObject/ConstructorHelpers.h"

namespace
{
    constexpr float MinimumPaintDimensionCm = 1.0f;
}

ULBFactoryFloorMarkingComponent::ULBFactoryFloorMarkingComponent()
{
    PrimaryComponentTick.bCanEverTick = false;
    SetMobility(EComponentMobility::Movable);

    static ConstructorHelpers::FObjectFinder<UStaticMesh> CubeMesh(
        TEXT("/Engine/BasicShapes/Cube.Cube"));
    static ConstructorHelpers::FObjectFinder<UMaterialInterface> BasicPaintMaterial(
        TEXT("/Engine/BasicShapes/BasicShapeMaterial.BasicShapeMaterial"));
    if (CubeMesh.Succeeded()) PaintCubeMesh = CubeMesh.Object;
    if (BasicPaintMaterial.Succeeded()) PaintBaseMaterial = BasicPaintMaterial.Object;
}

FLinearColor ULBFactoryFloorMarkingComponent::GetSemanticColour(
    const ELBFactoryFloorMarkingSemantic Semantic)
{
    switch (Semantic)
    {
    case ELBFactoryFloorMarkingSemantic::ServiceEnvelope:
        return FLinearColor::FromSRGBColor(FColor::FromHex(TEXT("F2C94C")));
    case ELBFactoryFloorMarkingSemantic::KeepClearHatch:
        return FLinearColor::FromSRGBColor(FColor::FromHex(TEXT("D62F2F")));
    case ELBFactoryFloorMarkingSemantic::StorageFill:
        return FLinearColor::FromSRGBColor(FColor::FromHex(TEXT("2D7D55")));
    case ELBFactoryFloorMarkingSemantic::StorageBoundary:
        return FLinearColor::FromSRGBColor(FColor::FromHex(TEXT("F1F3F4")));
    case ELBFactoryFloorMarkingSemantic::VehicleLane:
        return FLinearColor::FromSRGBColor(FColor::FromHex(TEXT("2878B8")));
    case ELBFactoryFloorMarkingSemantic::PedestrianCrossing:
        return FLinearColor::FromSRGBColor(FColor::FromHex(TEXT("FFFFFF")));
    case ELBFactoryFloorMarkingSemantic::EmptyStillageStorage:
        return FLinearColor::FromSRGBColor(FColor::FromHex(TEXT("2F80ED")));
    case ELBFactoryFloorMarkingSemantic::StillageLoadingBay:
        return FLinearColor::FromSRGBColor(FColor::FromHex(TEXT("F2A93B")));
    case ELBFactoryFloorMarkingSemantic::PressZoneFill:
        // Graphic floor field derived from Cairnwell Green, intentionally
        // light enough to read below machinery at the management camera.
        return FLinearColor::FromSRGBColor(FColor::FromHex(TEXT("A7C6B0")));
    case ELBFactoryFloorMarkingSemantic::PressCreamLane:
        return FLinearColor::FromSRGBColor(FColor::FromHex(TEXT("F3F1E9")));
    default:
        return FLinearColor::White;
    }
}

UHierarchicalInstancedStaticMeshComponent* ULBFactoryFloorMarkingComponent::FindOrCreateBatch(
    const ELBFactoryFloorMarkingSemantic Semantic)
{
    if (TObjectPtr<UHierarchicalInstancedStaticMeshComponent>* Existing = PaintBatches.Find(Semantic))
    {
        return Existing->Get();
    }
    AActor* Owner = GetOwner();
    if (!Owner || !PaintCubeMesh) return nullptr;

    UHierarchicalInstancedStaticMeshComponent* Batch =
        NewObject<UHierarchicalInstancedStaticMeshComponent>(Owner);
    if (!Batch) return nullptr;
    Owner->AddInstanceComponent(Batch);
    Batch->SetupAttachment(this);
    Batch->SetStaticMesh(PaintCubeMesh);
    Batch->SetMobility(EComponentMobility::Movable);
    Batch->SetCollisionEnabled(ECollisionEnabled::NoCollision);
    Batch->SetGenerateOverlapEvents(false);
    Batch->SetCanEverAffectNavigation(false);
    Batch->SetCastShadow(false);
    Batch->SetReceivesDecals(false);
    if (PaintBaseMaterial)
    {
        UMaterialInstanceDynamic* Paint = UMaterialInstanceDynamic::Create(PaintBaseMaterial, Owner);
        if (Paint)
        {
            const FLinearColor Colour = GetSemanticColour(Semantic);
            Paint->SetVectorParameterValue(TEXT("Color"), Colour);
            Paint->SetVectorParameterValue(TEXT("BaseColor"), Colour);
            Batch->SetMaterial(0, Paint);
        }
    }
    Batch->RegisterComponent();
    PaintBatches.Add(Semantic, Batch);
    return Batch;
}

void ULBFactoryFloorMarkingComponent::ClearMarkings()
{
    for (const TPair<ELBFactoryFloorMarkingSemantic,
        TObjectPtr<UHierarchicalInstancedStaticMeshComponent>>& Pair : PaintBatches)
    {
        if (Pair.Value) Pair.Value->ClearInstances();
    }
}

void ULBFactoryFloorMarkingComponent::AddPaintBox(const FVector2D& CentreCm,
    const FVector2D& SizeCm, const float FloorZCm, const float ThicknessCm,
    const float YawDegrees, const ELBFactoryFloorMarkingSemantic Semantic)
{
    if (!FMath::IsFinite(CentreCm.X) || !FMath::IsFinite(CentreCm.Y)
        || !FMath::IsFinite(FloorZCm) || SizeCm.X < MinimumPaintDimensionCm
        || SizeCm.Y < MinimumPaintDimensionCm || ThicknessCm <= 0.0f) return;
    UHierarchicalInstancedStaticMeshComponent* Batch = FindOrCreateBatch(Semantic);
    if (!Batch) return;
    const FVector Location(CentreCm.X, CentreCm.Y, FloorZCm + ThicknessCm * 0.5f);
    const FVector Scale(SizeCm.X / 100.0f, SizeCm.Y / 100.0f, ThicknessCm / 100.0f);
    Batch->AddInstance(FTransform(FRotator(0.0f, YawDegrees, 0.0f), Location, Scale));
}

void ULBFactoryFloorMarkingComponent::AddFilledRectangle(const FVector2D& CentreCm,
    const FVector2D& HalfExtentCm, const float FloorZCm,
    const ELBFactoryFloorMarkingSemantic Semantic, const float ThicknessCm)
{
    if (HalfExtentCm.X <= 0.0f || HalfExtentCm.Y <= 0.0f) return;
    AddPaintBox(CentreCm, HalfExtentCm * 2.0f, FloorZCm, ThicknessCm, 0.0f, Semantic);
}

void ULBFactoryFloorMarkingComponent::AddRectangleOutline(const FVector2D& CentreCm,
    const FVector2D& HalfExtentCm, const float FloorZCm, const float LineWidthCm,
    const ELBFactoryFloorMarkingSemantic Semantic, const float ThicknessCm)
{
    if (HalfExtentCm.X <= 0.0f || HalfExtentCm.Y <= 0.0f || LineWidthCm <= 0.0f) return;
    const float Width = FMath::Min(LineWidthCm, FMath::Min(HalfExtentCm.X, HalfExtentCm.Y));
    AddPaintBox(FVector2D(CentreCm.X, CentreCm.Y - HalfExtentCm.Y + Width * 0.5f),
        FVector2D(HalfExtentCm.X * 2.0f, Width), FloorZCm, ThicknessCm, 0.0f, Semantic);
    AddPaintBox(FVector2D(CentreCm.X, CentreCm.Y + HalfExtentCm.Y - Width * 0.5f),
        FVector2D(HalfExtentCm.X * 2.0f, Width), FloorZCm, ThicknessCm, 0.0f, Semantic);
    const float InnerHeight = FMath::Max(MinimumPaintDimensionCm,
        HalfExtentCm.Y * 2.0f - Width * 2.0f);
    AddPaintBox(FVector2D(CentreCm.X - HalfExtentCm.X + Width * 0.5f, CentreCm.Y),
        FVector2D(Width, InnerHeight), FloorZCm, ThicknessCm, 0.0f, Semantic);
    AddPaintBox(FVector2D(CentreCm.X + HalfExtentCm.X - Width * 0.5f, CentreCm.Y),
        FVector2D(Width, InnerHeight), FloorZCm, ThicknessCm, 0.0f, Semantic);
}

void ULBFactoryFloorMarkingComponent::AddDiagonalHatching(const FVector2D& CentreCm,
    const FVector2D& HalfExtentCm, const float FloorZCm, const float StripeWidthCm,
    const float StripePitchCm, const ELBFactoryFloorMarkingSemantic Semantic,
    const float ThicknessCm)
{
    if (HalfExtentCm.X <= StripeWidthCm || HalfExtentCm.Y <= StripeWidthCm
        || StripeWidthCm <= 0.0f || StripePitchCm < StripeWidthCm) return;

    // Stripe lines use direction (1,1) and are stepped along its perpendicular.
    // Intersect every infinite line with the rectangle to keep hatch paint clipped.
    const FVector2D Direction(UE_INV_SQRT_2, UE_INV_SQRT_2);
    const FVector2D Normal(-UE_INV_SQRT_2, UE_INV_SQRT_2);
    const float ProjectionRadius = HalfExtentCm.X * FMath::Abs(Normal.X)
        + HalfExtentCm.Y * FMath::Abs(Normal.Y);
    const int32 StripeCount = FMath::FloorToInt((ProjectionRadius * 2.0f) / StripePitchCm) + 1;
    const float FirstOffset = -0.5f * (StripeCount - 1) * StripePitchCm;
    for (int32 StripeIndex = 0; StripeIndex < StripeCount; ++StripeIndex)
    {
        const float Offset = FirstOffset + StripeIndex * StripePitchCm;
        const FVector2D Point = Normal * Offset;
        float MinAlong = -BIG_NUMBER;
        float MaxAlong = BIG_NUMBER;
        const auto ClipAxis = [&](const float PointAxis, const float DirectionAxis,
            const float HalfExtentAxis)
        {
            if (FMath::IsNearlyZero(DirectionAxis)) return FMath::Abs(PointAxis) <= HalfExtentAxis;
            float A = (-HalfExtentAxis - PointAxis) / DirectionAxis;
            float B = (HalfExtentAxis - PointAxis) / DirectionAxis;
            if (A > B) Swap(A, B);
            MinAlong = FMath::Max(MinAlong, A);
            MaxAlong = FMath::Min(MaxAlong, B);
            return MinAlong < MaxAlong;
        };
        if (!ClipAxis(Point.X, Direction.X, HalfExtentCm.X)
            || !ClipAxis(Point.Y, Direction.Y, HalfExtentCm.Y)) continue;
        const float Length = MaxAlong - MinAlong;
        if (Length < MinimumPaintDimensionCm) continue;
        const FVector2D StripeCentre = CentreCm + Point
            + Direction * ((MinAlong + MaxAlong) * 0.5f);
        AddPaintBox(StripeCentre, FVector2D(Length, StripeWidthCm), FloorZCm,
            ThicknessCm, 45.0f, Semantic);
    }
}

void ULBFactoryFloorMarkingComponent::AddDashedLine(const FVector2D& StartCm,
    const FVector2D& EndCm, const float FloorZCm, const float LineWidthCm,
    const float DashLengthCm, const float GapLengthCm,
    const ELBFactoryFloorMarkingSemantic Semantic, const float ThicknessCm)
{
    const FVector2D Delta = EndCm - StartCm;
    const float TotalLength = Delta.Size();
    if (TotalLength < MinimumPaintDimensionCm || LineWidthCm <= 0.0f
        || DashLengthCm <= 0.0f || GapLengthCm < 0.0f) return;
    const FVector2D Direction = Delta / TotalLength;
    const float Yaw = FMath::RadiansToDegrees(FMath::Atan2(Direction.Y, Direction.X));
    for (float Along = 0.0f; Along < TotalLength; Along += DashLengthCm + GapLengthCm)
    {
        const float Length = FMath::Min(DashLengthCm, TotalLength - Along);
        const FVector2D Centre = StartCm + Direction * (Along + Length * 0.5f);
        AddPaintBox(Centre, FVector2D(Length, LineWidthCm), FloorZCm,
            ThicknessCm, Yaw, Semantic);
    }
}

int32 ULBFactoryFloorMarkingComponent::GetMarkingCount() const
{
    int32 Count = 0;
    for (const TPair<ELBFactoryFloorMarkingSemantic,
        TObjectPtr<UHierarchicalInstancedStaticMeshComponent>>& Pair : PaintBatches)
    {
        if (Pair.Value) Count += Pair.Value->GetInstanceCount();
    }
    return Count;
}

int32 ULBFactoryFloorMarkingComponent::GetMarkingCountBySemantic(
    const ELBFactoryFloorMarkingSemantic Semantic) const
{
    const TObjectPtr<UHierarchicalInstancedStaticMeshComponent>* Batch = PaintBatches.Find(Semantic);
    return Batch && Batch->Get() ? Batch->Get()->GetInstanceCount() : 0;
}

bool ULBFactoryFloorMarkingComponent::HasNonCollidingPresentation() const
{
    if (GetMarkingCount() <= 0) return false;
    for (const TPair<ELBFactoryFloorMarkingSemantic,
        TObjectPtr<UHierarchicalInstancedStaticMeshComponent>>& Pair : PaintBatches)
    {
        const UHierarchicalInstancedStaticMeshComponent* Batch = Pair.Value;
        if (!Batch || Batch->GetInstanceCount() <= 0) continue;
        if (!Batch->GetStaticMesh() || Batch->GetCollisionEnabled() != ECollisionEnabled::NoCollision
            || Batch->CanEverAffectNavigation() || Batch->CastShadow) return false;
    }
    return true;
}
