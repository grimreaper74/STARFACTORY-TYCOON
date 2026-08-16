#pragma once

#include "CoreMinimal.h"
#include "GameFramework/Actor.h"
#include "LBOneFactoryDevRestoredShopActor.generated.h"

class UInstancedStaticMeshComponent;
class USceneComponent;

/**
 * Materialises the complete restored press-shop surroundings in Moorcross.
 *
 * The protected LB_PressShop_FullFactoryRestored_v001 map was read once,
 * offline, and every non-train static mesh actor - the overhead crane with its
 * runway and columns, guard rails, floor trench grates, lamps, pipework,
 * carrier rollers, HMI cabinets and the logistics corner - was recorded to a
 * datum-relative manifest staged at
 * Content/LineBoss/Reference/RestoredShop/shop_manifest.json. Engine-primitive
 * walls and floors were dropped: Moorcross has its own.
 *
 * This actor loads that manifest and rebuilds the shop around the committed
 * ConfigurablePressTrain datum, rotated ninety degrees to match the Moorcross
 * train row. The protected map is never written; this is the recovery doc's
 * read-and-materialise pattern applied to everything around the trains.
 */
UCLASS()
class LINEBOSSCARFACTORY_API ALBOneFactoryDevRestoredShopActor : public AActor
{
    GENERATED_BODY()

public:
    ALBOneFactoryDevRestoredShopActor();

    /** Rebuilds the reference shop around the press datum. */
    UFUNCTION(BlueprintCallable, Category="Line Boss|OneFactory|Developer")
    bool BuildFromManifest(FString& OutReason);

    UFUNCTION(BlueprintPure, Category="Line Boss|OneFactory|Developer")
    int32 GetPlacedCount() const { return PlacedCount; }

    static FName GetShopTag();

private:
    UPROPERTY()
    TObjectPtr<USceneComponent> SceneRoot;

    UPROPERTY()
    TArray<TObjectPtr<UInstancedStaticMeshComponent>> Batches;

    int32 PlacedCount = 0;
};
