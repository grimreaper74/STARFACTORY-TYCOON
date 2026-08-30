#pragma once

#include "CoreMinimal.h"
#include "GameFramework/Actor.h"
#include "LBOneFactoryPressToolingSupportActor.generated.h"

class UInstancedStaticMeshComponent;
class UMaterialInterface;
class UStaticMesh;
class UStaticMeshComponent;
class UTextRenderComponent;
struct FLBOneFactoryPressStarterLayoutState;

/**
 * Native visual support for Press Train A tooling.  This is intentionally kept
 * outside the retained press aggregate: racks, dies and the changeover cart can
 * be replaced independently and the cart has a real Unreal motion seam.
 */
UCLASS(BlueprintType)
class LINEBOSSCARFACTORY_API ALBOneFactoryPressToolingSupportActor : public AActor
{
    GENERATED_BODY()

public:
    ALBOneFactoryPressToolingSupportActor();

    virtual void Tick(float DeltaSeconds) override;

    UFUNCTION(BlueprintCallable,
        Category="Line Boss|OneFactory|Press Tooling")
    bool ConfigureFromPressLayout(
        const FLBOneFactoryPressStarterLayoutState& Layout, FString& OutReason);

    UFUNCTION(BlueprintPure,
        Category="Line Boss|OneFactory|Press Tooling")
    bool IsConfigured() const { return bConfigured; }

    UFUNCTION(BlueprintPure,
        Category="Line Boss|OneFactory|Press Tooling")
    int32 GetStoredDieSetCount() const { return StoredDieSetCount; }

    static FName GetToolingTag();

private:
    UPROPERTY(VisibleAnywhere, Category="Line Boss|OneFactory|Press Tooling")
    TObjectPtr<USceneComponent> SceneRoot;

    UPROPERTY(VisibleAnywhere, Category="Line Boss|OneFactory|Press Tooling")
    TObjectPtr<UInstancedStaticMeshComponent> RackFrames;

    UPROPERTY(VisibleAnywhere, Category="Line Boss|OneFactory|Press Tooling")
    TObjectPtr<UInstancedStaticMeshComponent> StoredDies;

    UPROPERTY(VisibleAnywhere, Category="Line Boss|OneFactory|Press Tooling")
    TObjectPtr<UInstancedStaticMeshComponent> SafetyRoute;

    // Station-side interfaces remain separate from the store so authored dies
    // can be swapped later without losing their physical changeover positions.
    UPROPERTY(VisibleAnywhere, Category="Line Boss|OneFactory|Press Tooling")
    TObjectPtr<UInstancedStaticMeshComponent> BolsterInterfaces;

    UPROPERTY(VisibleAnywhere, Category="Line Boss|OneFactory|Press Tooling")
    TObjectPtr<UInstancedStaticMeshComponent> DieChangeStaging;

    UPROPERTY(VisibleAnywhere, Category="Line Boss|OneFactory|Press Tooling")
    TObjectPtr<UStaticMeshComponent> DieChangeCart;

    UPROPERTY(VisibleAnywhere, Category="Line Boss|OneFactory|Press Tooling")
    TArray<TObjectPtr<UTextRenderComponent>> DieBayLabels;

    UPROPERTY(Transient)
    TObjectPtr<UStaticMesh> NativeCube;

    UPROPERTY(Transient)
    TObjectPtr<UMaterialInterface> StructureMaterial;

    UPROPERTY(Transient)
    TObjectPtr<UMaterialInterface> SteelMaterial;

    UPROPERTY(Transient)
    TObjectPtr<UMaterialInterface> SafetyMaterial;

    UPROPERTY(Transient)
    FTransform CartRestTransform = FTransform::Identity;

    UPROPERTY(Transient)
    bool bConfigured = false;

    UPROPERTY(Transient)
    int32 StoredDieSetCount = 0;

    static void ConfigureStaticVisual(UStaticMeshComponent* Component);
};
