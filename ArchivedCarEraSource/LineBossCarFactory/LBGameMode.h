#pragma once

#include "CoreMinimal.h"
#include "GameFramework/GameModeBase.h"
#include "LBGameMode.generated.h"

class ALBCleaningAMR;
class ALBMaintenanceAMR;
class UWorld;

UCLASS()
class LINEBOSSCARFACTORY_API ALBGameMode : public AGameModeBase
{
    GENERATED_BODY()

public:
    ALBGameMode();
    virtual void BeginPlay() override;

private:
    /** Ensures the clean player-built game owns the retained two-CR01/two-MR01 starter fleet. */
    void EnsureCleanSupportFleet(UWorld* World);

    UPROPERTY()
    TSubclassOf<ALBCleaningAMR> CleaningRobotClass;

    UPROPERTY()
    TSubclassOf<ALBMaintenanceAMR> MaintenanceRobotClass;
};
