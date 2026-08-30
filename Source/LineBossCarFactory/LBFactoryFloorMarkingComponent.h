#pragma once

#include "CoreMinimal.h"
#include "Components/SceneComponent.h"
#include "LBFactoryFloorMarkingComponent.generated.h"

class UHierarchicalInstancedStaticMeshComponent;
class UMaterialInterface;
class UStaticMesh;

/**
 * Player-built floor-paint vocabulary shared by machines, stores and routes.
 *
 * Markings are deliberately thin, instanced, non-colliding presentation. They
 * follow their owning actor's saved transform and never alter placement,
 * navigation or factory simulation authority.
 */
UENUM(BlueprintType)
enum class ELBFactoryFloorMarkingSemantic : uint8
{
    ServiceEnvelope,
    KeepClearHatch,
    StorageFill,
    StorageBoundary,
    VehicleLane,
    PedestrianCrossing,
    EmptyStillageStorage,
    StillageLoadingBay,
    /** Large, deliberately graphic Press Shop station field; lightened Cairnwell derivative. */
    PressZoneFill,
    /** Literal BRAND_IDENTITY_AUTHORITY Warm White lane and zone edge. */
    PressCreamLane
};

UCLASS(ClassGroup=(LineBoss), meta=(BlueprintSpawnableComponent))
class LINEBOSSCARFACTORY_API ULBFactoryFloorMarkingComponent : public USceneComponent
{
    GENERATED_BODY()

public:
    ULBFactoryFloorMarkingComponent();

    /** Removes all paint instances while retaining the small per-colour render batches. */
    UFUNCTION(BlueprintCallable, Category="Cairnwell|Factory Builder|Floor Paint")
    void ClearMarkings();

    void AddFilledRectangle(const FVector2D& CentreCm, const FVector2D& HalfExtentCm,
        float FloorZCm, ELBFactoryFloorMarkingSemantic Semantic, float ThicknessCm = 1.0f);

    void AddRectangleOutline(const FVector2D& CentreCm, const FVector2D& HalfExtentCm,
        float FloorZCm, float LineWidthCm, ELBFactoryFloorMarkingSemantic Semantic,
        float ThicknessCm = 1.0f);

    /** Adds clipped 45-degree stripes, so keep-clear paint never leaks outside its bay. */
    void AddDiagonalHatching(const FVector2D& CentreCm, const FVector2D& HalfExtentCm,
        float FloorZCm, float StripeWidthCm, float StripePitchCm,
        ELBFactoryFloorMarkingSemantic Semantic, float ThicknessCm = 1.0f);

    /** Adds a local-space dashed line between two player-built points. */
    void AddDashedLine(const FVector2D& StartCm, const FVector2D& EndCm, float FloorZCm,
        float LineWidthCm, float DashLengthCm, float GapLengthCm,
        ELBFactoryFloorMarkingSemantic Semantic, float ThicknessCm = 1.0f);

    UFUNCTION(BlueprintPure, Category="Cairnwell|Factory Builder|Floor Paint")
    int32 GetMarkingCount() const;

    UFUNCTION(BlueprintPure, Category="Cairnwell|Factory Builder|Floor Paint")
    int32 GetMarkingCountBySemantic(ELBFactoryFloorMarkingSemantic Semantic) const;

    UFUNCTION(BlueprintPure, Category="Cairnwell|Factory Builder|Floor Paint")
    bool HasNonCollidingPresentation() const;

    UFUNCTION(BlueprintPure, Category="Cairnwell|Factory Builder|Floor Paint")
    static FLinearColor GetSemanticColour(ELBFactoryFloorMarkingSemantic Semantic);

private:
    UPROPERTY(Transient)
    TObjectPtr<UStaticMesh> PaintCubeMesh;

    UPROPERTY(Transient)
    TObjectPtr<UMaterialInterface> PaintBaseMaterial;

    UPROPERTY(Transient)
    TMap<ELBFactoryFloorMarkingSemantic, TObjectPtr<UHierarchicalInstancedStaticMeshComponent>> PaintBatches;

    UHierarchicalInstancedStaticMeshComponent* FindOrCreateBatch(
        ELBFactoryFloorMarkingSemantic Semantic);
    void AddPaintBox(const FVector2D& CentreCm, const FVector2D& SizeCm, float FloorZCm,
        float ThicknessCm, float YawDegrees, ELBFactoryFloorMarkingSemantic Semantic);
};
