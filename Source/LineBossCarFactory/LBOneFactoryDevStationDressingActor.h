#pragma once

#include "CoreMinimal.h"
#include "GameFramework/Actor.h"
#include "LBOneFactoryDevStationDressingActor.generated.h"

class UInstancedStaticMeshComponent;
class UMaterialInstanceDynamic;
class USceneComponent;

/**
 * Turns each configured station from a floor pad into something that reads as a
 * working cell.
 *
 * The starter presentations are pinned to exact instance counts by contract -
 * the Body/Weld one to 469 - so station geometry cannot simply be added there
 * without a versioned v002 presentation and regenerated tests. This actor adds
 * the dressing alongside instead: a zone pad, safety guarding, a control
 * cabinet and a status beacon per station, all sized from the live route and
 * spawned at runtime.
 *
 * It follows the factory visual standard rather than decorating freely: strong
 * simple silhouettes, no pipe clutter or micro-railings, Safety Yellow used only
 * for guarding, and nothing added that does not correspond to a real station.
 */
UCLASS()
class LINEBOSSCARFACTORY_API ALBOneFactoryDevStationDressingActor : public AActor
{
    GENERATED_BODY()

public:
    ALBOneFactoryDevStationDressingActor();

    /** Dresses every station in the configured route. */
    UFUNCTION(BlueprintCallable, Category="Line Boss|OneFactory|Developer")
    bool BuildFromRoute(FString& OutReason);

    UFUNCTION(BlueprintPure, Category="Line Boss|OneFactory|Developer")
    int32 GetDressedStationCount() const { return DressedStations; }

    static FName GetDressingTag();

private:
    UInstancedStaticMeshComponent* MakeBatch(const TCHAR* Name);

    UPROPERTY()
    TObjectPtr<USceneComponent> SceneRoot;

    /** Cairnwell Green zone pad marking the cell footprint. */
    UPROPERTY()
    TObjectPtr<UInstancedStaticMeshComponent> ZonePad;

    /** Safety Yellow posts and rails. Functional colour, per the brand rules. */
    UPROPERTY()
    TObjectPtr<UInstancedStaticMeshComponent> Guarding;

    /** Foundry Charcoal control cabinet and overhead beam. */
    UPROPERTY()
    TObjectPtr<UInstancedStaticMeshComponent> Equipment;

    /** Status beacon on top of each cabinet. */
    UPROPERTY()
    TObjectPtr<UInstancedStaticMeshComponent> Beacon;

    UPROPERTY()
    TArray<TObjectPtr<UMaterialInstanceDynamic>> Materials;

    int32 DressedStations = 0;
    int32 PieceCount = 0;
};
