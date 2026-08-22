#pragma once

#include "CoreMinimal.h"
#include "GameFramework/Actor.h"
#include "LBPressTrainSignageActor.generated.h"

class UStaticMeshComponent;
class UTextRenderComponent;

/**
 * Native, cook-safe train identification board.  It replaces legacy imported
 * signage whose material dependencies were incomplete, while keeping the
 * press trains legible in the playable factory.
 */
UCLASS()
class LINEBOSSCARFACTORY_API ALBPressTrainSignageActor : public AActor
{
    GENERATED_BODY()

public:
    ALBPressTrainSignageActor();

    UStaticMeshComponent* GetSignPlate() const { return SignPlate; }
    UTextRenderComponent* GetLabel() const { return Label; }

private:
    UPROPERTY(VisibleAnywhere, Category="Line Boss|Press")
    TObjectPtr<UStaticMeshComponent> SignPlate;

    UPROPERTY(VisibleAnywhere, Category="Line Boss|Press")
    TObjectPtr<UTextRenderComponent> Label;
};
