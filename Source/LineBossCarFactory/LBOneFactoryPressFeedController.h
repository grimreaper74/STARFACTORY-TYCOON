#pragma once

#include "CoreMinimal.h"
#include "GameFramework/Actor.h"
#include "LBOneFactoryPressFeedController.generated.h"

class ALBPR008Station;
class ALBPR009Station;
class ALBPR010Station;

/**
 * Native transactional route from blank preparation through the four-lane
 * supermarket.  It uses the established PR008/9/10 machine authorities; this
 * actor deliberately owns no shortcut inventory or fake throughput counters.
 */
UCLASS(BlueprintType)
class LINEBOSSCARFACTORY_API ALBOneFactoryPressFeedController : public AActor
{
    GENERATED_BODY()

public:
    ALBOneFactoryPressFeedController();
    virtual void Tick(float DeltaSeconds) override;

    UFUNCTION(BlueprintCallable, Category="Line Boss|OneFactory|Press Feed")
    bool ConfigureAutomaticRoute(FString& OutReason);

    UFUNCTION(BlueprintPure, Category="Line Boss|OneFactory|Press Feed")
    bool IsConfigured() const { return bConfigured; }

    UFUNCTION(BlueprintPure, Category="Line Boss|OneFactory|Press Feed")
    int32 GetDeliveredStackCount() const { return DeliveredStackCount; }

    static FName GetFeedTag();

private:
    UPROPERTY(Transient) TObjectPtr<ALBPR008Station> PR008;
    UPROPERTY(Transient) TObjectPtr<ALBPR009Station> PR009;
    UPROPERTY(Transient) TObjectPtr<ALBPR010Station> PR010;
    UPROPERTY(Transient) bool bConfigured = false;
    UPROPERTY(Transient) int32 DeliveredStackCount = 0;

    bool TransferBlank();
    bool TransferStack();
};
