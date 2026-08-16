#pragma once

#include "CoreMinimal.h"
#include "GameFramework/Actor.h"
#include "LBPressShopNavigationBootstrap.generated.h"

/** Ensures Press Shop maps have runtime navigation for support robots and automated logistics. */
UCLASS()
class LINEBOSSCARFACTORY_API ALBPressShopNavigationBootstrap : public AActor
{
    GENERATED_BODY()

public:
    ALBPressShopNavigationBootstrap();
    virtual void BeginPlay() override;

    UFUNCTION(BlueprintPure, Category = "Line Boss|Press Shop|Navigation")
    bool IsNavigationReady() const { return bNavigationReady; }

    /** Runs the gate through native code so automation does not invoke a
     *  static NavigationSystem Python wrapper on its class default object. */
    UFUNCTION(BlueprintCallable, Category = "Line Boss|Press Shop|Navigation")
    bool ValidatePath(const FVector& Start, const FVector& End);

    UFUNCTION(BlueprintPure, Category = "Line Boss|Press Shop|Navigation")
    float GetValidatedPathLength() const { return ValidatedPathLength; }

    UFUNCTION(BlueprintPure, Category = "Line Boss|Press Shop|Navigation")
    const TArray<FVector>& GetValidatedPathPoints() const { return ValidatedPathPoints; }

    UFUNCTION(BlueprintPure, Category = "Line Boss|Press Shop|Navigation")
    bool IsValidatedPathPartial() const { return bValidatedPathPartial; }

private:
    UPROPERTY(VisibleInstanceOnly, Category = "Line Boss|Press Shop|Navigation")
    bool bNavigationReady = false;

    UPROPERTY(VisibleInstanceOnly, Category = "Line Boss|Press Shop|Navigation")
    float ValidatedPathLength = -1.0f;

    UPROPERTY(VisibleInstanceOnly, Category = "Line Boss|Press Shop|Navigation")
    TArray<FVector> ValidatedPathPoints;

    UPROPERTY(VisibleInstanceOnly, Category = "Line Boss|Press Shop|Navigation")
    bool bValidatedPathPartial = false;

    FTimerHandle BuildTimer;
    void EnsureNavigationReady();
};
