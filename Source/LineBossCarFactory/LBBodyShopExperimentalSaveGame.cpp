#include "LBBodyShopExperimentalSaveGame.h"

FName ULBBodyShopExperimentalSaveGame::GetSlotName()
{
    return TEXT("LineBoss_BodyShopExperimental_v001");
}

bool ULBBodyShopExperimentalSaveGame::ValidateForLoad(FString& OutReason) const
{
    OutReason.Reset();
    if (SaveSchemaVersion != SchemaVersion)
    {
        OutReason = TEXT("BODY SHOP EXPERIMENTAL SAVE SCHEMA IS NOT VERSION 1");
        return false;
    }
    if (PrototypeMapId != TEXT("LB_BodyShop_Prototype_v001"))
    {
        OutReason = TEXT("BODY SHOP EXPERIMENTAL SAVE TARGETS A DIFFERENT PROTOTYPE MAP");
        return false;
    }
    return FLBBodyShopDefinitionRegistry::ValidateExperimentalSaveState(State, OutReason);
}
