#include "LBFreeRoamGameMode.h"

#include "LBFreeRoamPawn.h"

ALBFreeRoamGameMode::ALBFreeRoamGameMode()
{
    DefaultPawnClass = ALBFreeRoamPawn::StaticClass();
}
