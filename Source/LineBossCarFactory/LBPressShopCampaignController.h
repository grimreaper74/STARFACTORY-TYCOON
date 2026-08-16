#pragma once

#include "CoreMinimal.h"
#include "GameFramework/Actor.h"
#include "LBPressShopCampaignController.generated.h"

class ULBPressShopSaveGame;

/** Single transactional campaign-save authority for the complete Press Shop. */
UCLASS(BlueprintType, Blueprintable)
class LINEBOSSCARFACTORY_API ALBPressShopCampaignController : public AActor
{
    GENERATED_BODY()

public:
    UFUNCTION(BlueprintCallable, Category="Cairnwell|Press Shop|Campaign")
    bool CaptureCampaign(ULBPressShopSaveGame* SaveRoot);

    UFUNCTION(BlueprintCallable, Category="Cairnwell|Press Shop|Campaign")
    bool RestoreCampaign(const ULBPressShopSaveGame* SaveRoot);

    UFUNCTION(BlueprintCallable, Category="Cairnwell|Press Shop|Campaign")
    bool SaveCampaignToSlot();

    UFUNCTION(BlueprintCallable, Category="Cairnwell|Press Shop|Campaign")
    bool LoadCampaignFromSlot();

    UPROPERTY(EditAnywhere, BlueprintReadOnly, Category="Cairnwell|Press Shop|Campaign")
    FString CampaignSlotName = TEXT("LB_PRESS_SHOP_CAMPAIGN");

    UPROPERTY(EditAnywhere, BlueprintReadOnly, Category="Cairnwell|Press Shop|Campaign")
    int32 CampaignUserIndex = 0;

private:
    bool PreflightCampaign(const ULBPressShopSaveGame* SaveRoot) const;
};
