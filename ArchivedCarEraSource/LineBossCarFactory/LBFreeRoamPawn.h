#pragma once

#include "CoreMinimal.h"
#include "GameFramework/SpectatorPawn.h"
#include "LBFreeRoamPawn.generated.h"

/** No-collision owner inspection camera for unrestricted whole-factory review. */
UCLASS()
class LINEBOSSCARFACTORY_API ALBFreeRoamPawn : public ASpectatorPawn
{
    GENERATED_BODY()

public:
    ALBFreeRoamPawn();

protected:
    virtual void BeginPlay() override;

private:
    UPROPERTY(EditDefaultsOnly, Category="Line Boss|Free Roam")
    float MinimumInitialHeightCm = 500.0f;
};
