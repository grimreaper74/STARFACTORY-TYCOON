#pragma once

#include "CoreMinimal.h"
#include "GameFramework/Actor.h"
#include "LBOneFactoryPressFeedPresentationActor.generated.h"

class UInstancedStaticMeshComponent;
class USceneComponent;
class UStaticMesh;
class UStaticMeshComponent;
class UMaterialInterface;
class UTextRenderComponent;
struct FLBOneFactoryPressStarterLayoutState;

/** Visual-only native machinery for the real PR008→PR010 route. */
UCLASS(BlueprintType)
class LINEBOSSCARFACTORY_API ALBOneFactoryPressFeedPresentationActor : public AActor
{
    GENERATED_BODY()
public:
    ALBOneFactoryPressFeedPresentationActor();
    virtual void Tick(float DeltaSeconds) override;

    UFUNCTION(BlueprintCallable, Category="Line Boss|OneFactory|Press Feed")
    bool ConfigureFromPressLayout(const FLBOneFactoryPressStarterLayoutState& Layout,
        FString& OutReason);
    UFUNCTION(BlueprintPure, Category="Line Boss|OneFactory|Press Feed")
    bool IsConfigured() const { return bConfigured; }
    UFUNCTION(BlueprintPure, Category="Line Boss|OneFactory|Press Feed")
    int32 GetVisibleModuleCount() const { return 3; }
    static FName GetPresentationTag();
private:
    UPROPERTY(VisibleAnywhere) TObjectPtr<USceneComponent> SceneRoot;
    UPROPERTY(VisibleAnywhere) TObjectPtr<UInstancedStaticMeshComponent> GreenStructure;
    UPROPERTY(VisibleAnywhere) TObjectPtr<UInstancedStaticMeshComponent> SteelConveyors;
    UPROPERTY(VisibleAnywhere) TObjectPtr<UInstancedStaticMeshComponent> SafetyGuarding;
    UPROPERTY(VisibleAnywhere) TObjectPtr<UStaticMeshComponent> ShearBlade;
    UPROPERTY(VisibleAnywhere) TObjectPtr<UStaticMeshComponent> SupermarketShuttle;
    UPROPERTY(VisibleAnywhere) TArray<TObjectPtr<UTextRenderComponent>> ModuleLabels;
    UPROPERTY(Transient) TObjectPtr<UStaticMesh> Cube;
    UPROPERTY(Transient) TObjectPtr<UMaterialInterface> Green;
    UPROPERTY(Transient) TObjectPtr<UMaterialInterface> Steel;
    UPROPERTY(Transient) TObjectPtr<UMaterialInterface> Yellow;
    UPROPERTY(Transient) FTransform ShearRest = FTransform::Identity;
    UPROPERTY(Transient) FTransform ShuttleRest = FTransform::Identity;
    UPROPERTY(Transient) bool bConfigured = false;
    static void ConfigureVisual(UStaticMeshComponent* Component);
};
