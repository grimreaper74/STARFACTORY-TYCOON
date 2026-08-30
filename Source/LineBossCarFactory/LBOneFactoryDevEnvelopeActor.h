#pragma once

#include "CoreMinimal.h"
#include "GameFramework/Actor.h"
#include "LBOneFactoryDevEnvelopeActor.generated.h"

class UInstancedStaticMeshComponent;
class UMaterialInstanceDynamic;
class USceneComponent;

/**
 * A development building envelope for the Moorcross Works site.
 *
 * The shipped map provides a floor, roof beams and columns but no walls, so the
 * site fades to black at its edges and reads as objects on a lit plane rather
 * than the inside of a factory. This actor closes it in.
 *
 * It is deliberately NOT the legacy press-shop envelope. The OneFactory
 * bootstrap contract requires SpawnsLegacyFactoryContent() to stay false, so
 * ALBFactoryEnvelopeShutterActor and its side dressing must not appear here.
 * Everything below is engine primitives sized from the live station route,
 * spawned at runtime and never saved, so the protected map is untouched.
 *
 * A permanent envelope belongs in the map or in an authored native kit. This
 * exists so the factory can be looked at and judged now.
 */
UCLASS()
class LINEBOSSCARFACTORY_API ALBOneFactoryDevEnvelopeActor : public AActor
{
    GENERATED_BODY()

public:
    ALBOneFactoryDevEnvelopeActor();

    /**
     * Builds walls, a site slab, roof decks and roof-line clerestory strips
     * around the configured route. Padding is added beyond the outermost
     * stations so the aisles do not run straight into a wall.
     */
    UFUNCTION(BlueprintCallable, Category="Line Boss|OneFactory|Developer")
    bool BuildFromRoute(double PaddingCm, double WallHeightCm,
        FString& OutReason);

    /**
     * Explicit presentation-policy variant. Roofless candidate maps retain
     * the envelope walls, dado, clerestory and site slab but do not receive
     * the four runtime roof decks that would cover a true-overhead view.
     */
    bool BuildFromRouteWithRoofPolicy(double PaddingCm, double WallHeightCm,
        bool bIncludeRoofDecks, FString& OutReason);

    UFUNCTION(BlueprintPure, Category="Line Boss|OneFactory|Developer")
    int32 GetPieceCount() const { return PieceCount; }

    int32 GetRoofDeckCount() const;
    int32 GetWallInstanceCount() const;
    int32 GetDadoInstanceCount() const;
    int32 GetClerestoryInstanceCount() const;
    int32 GetSiteSlabInstanceCount() const;

    static FName GetEnvelopeTag();

private:
    UInstancedStaticMeshComponent* MakeBatch(const TCHAR* Name,
        const TCHAR* HexColour, float Roughness);

    UPROPERTY()
    TObjectPtr<USceneComponent> SceneRoot;

    /** Outer wall panels. */
    UPROPERTY()
    TObjectPtr<UInstancedStaticMeshComponent> Walls;

    /** Lower dado band, so walls are not one flat colour. */
    UPROPERTY()
    TObjectPtr<UInstancedStaticMeshComponent> Dado;

    /** Floor slab covering the routed footprint where the map has none. */
    UPROPERTY()
    TObjectPtr<UInstancedStaticMeshComponent> Ceiling;

    /** Bright strips at the roof line reading as daylight glazing. */
    UPROPERTY()
    TObjectPtr<UInstancedStaticMeshComponent> Clerestory;

    UPROPERTY()
    TArray<TObjectPtr<UMaterialInstanceDynamic>> Materials;

    /**
     * One roof deck per shop building, each on its own untagged actor so the
     * camera-height roof toggle governs them while the walls stay exempt.
     */
    UPROPERTY()
    TArray<TObjectPtr<AActor>> RoofDecks;

    int32 PieceCount = 0;
};
