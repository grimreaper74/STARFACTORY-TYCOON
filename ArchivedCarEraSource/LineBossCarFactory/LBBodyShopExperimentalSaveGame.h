#pragma once

#include "CoreMinimal.h"
#include "GameFramework/SaveGame.h"
#include "LBBodyShopTypes.h"
#include "LBBodyShopExperimentalSaveGame.generated.h"

/**
 * Experimental Body Shop persistence only. This type is deliberately separate
 * from campaign v18 and has no migration path into the legacy Press save.
 */
UCLASS(BlueprintType)
class LINEBOSSCARFACTORY_API ULBBodyShopExperimentalSaveGame : public USaveGame
{
    GENERATED_BODY()

public:
    static constexpr int32 SchemaVersion = 1;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, SaveGame, Category="Line Boss|Body Shop|Save")
    FLBBodyShopExperimentalSaveState State;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, SaveGame, Category="Line Boss|Body Shop|Save")
    FString PrototypeMapId = TEXT("LB_BodyShop_Prototype_v001");

    UPROPERTY(EditAnywhere, BlueprintReadWrite, SaveGame, Category="Line Boss|Body Shop|Save")
    int32 SaveSchemaVersion = SchemaVersion;

    static FName GetSlotName();
    static int32 GetUserIndex() { return 0; }

    bool ValidateForLoad(FString& OutReason) const;
};
