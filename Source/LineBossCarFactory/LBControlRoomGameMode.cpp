#include "LBControlRoomGameMode.h"

#include "LBControlRoomHUD.h"
#include "LBControlRoomPawn.h"

ALBControlRoomGameMode::ALBControlRoomGameMode()
{
    DefaultPawnClass = ALBControlRoomPawn::StaticClass();
    HUDClass = ALBControlRoomHUD::StaticClass();
}
