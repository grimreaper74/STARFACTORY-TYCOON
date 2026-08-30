#pragma once

#include "CoreMinimal.h"
#include "GameFramework/GameModeBase.h"
#include "LBFreeRoamGameMode.generated.h"

/** Standalone inspection mode; intentionally excludes production interaction authority. */
UCLASS()
class LINEBOSSCARFACTORY_API ALBFreeRoamGameMode : public AGameModeBase
{
    GENERATED_BODY()

public:
    ALBFreeRoamGameMode();
};
