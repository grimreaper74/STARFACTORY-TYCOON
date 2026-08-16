#pragma once

#include "CoreMinimal.h"
#include "GameFramework/Actor.h"
#include "LBSupportRobot.h"
#include "LBPressShopSupportFleetController.generated.h"

class ALBSupportRobot;
class ULBPressShopSaveGame;

/** Runtime authority for the four installed Press Shop support robots. */
UCLASS(BlueprintType, Blueprintable)
class LINEBOSSCARFACTORY_API ALBPressShopSupportFleetController : public AActor
{
    GENERATED_BODY()

public:
    ALBPressShopSupportFleetController();
    virtual void BeginPlay() override;

    /** Re-discovers and safely commissions the retained two-CR01/two-MR01 fleet. */
    UFUNCTION(BlueprintCallable, Category = "Line Boss|Press Shop|Support Fleet")
    bool InitialiseInstalledFleet();

    /** Captures all four installed units into the campaign save root in deterministic unit-id order. */
    UFUNCTION(BlueprintCallable, Category = "Line Boss|Press Shop|Support Fleet|Save")
    bool CaptureFleetSaveState(ULBPressShopSaveGame* SaveRoot);

    /** Restores an exact two-CR01/two-MR01 snapshot, then performs mandatory safe route revalidation. */
    UFUNCTION(BlueprintCallable, Category = "Line Boss|Press Shop|Support Fleet|Save")
    bool RestoreFleetSaveState(const ULBPressShopSaveGame* SaveRoot);

    /** Preserves the rest of the campaign root while writing the installed fleet to disk. */
    UFUNCTION(BlueprintCallable, Category = "Line Boss|Press Shop|Support Fleet|Save")
    bool SaveFleetToCampaignSlot();

    /** Loads and safely revalidates the installed fleet from the campaign disk slot. */
    UFUNCTION(BlueprintCallable, Category = "Line Boss|Press Shop|Support Fleet|Save")
    bool LoadFleetFromCampaignSlot();

    /** Dispatches one docked unit to its certified service cross-aisle standby point. */
    UFUNCTION(BlueprintCallable, Category = "Line Boss|Press Shop|Support Fleet")
    bool DispatchUnit(FName UnitId);

    /** Returns one stationary dispatched unit to its own certified charging berth. */
    UFUNCTION(BlueprintCallable, Category = "Line Boss|Press Shop|Support Fleet")
    bool ReturnUnitToDock(FName UnitId);

    UFUNCTION(BlueprintPure, Category = "Line Boss|Press Shop|Support Fleet")
    int32 GetInstalledUnitCount() const { return InstalledRobots.Num(); }

    UFUNCTION(BlueprintPure, Category = "Line Boss|Press Shop|Support Fleet")
    bool IsFleetReady() const { return bFleetReady; }

    UFUNCTION(BlueprintPure, Category = "Line Boss|Press Shop|Support Fleet")
    bool GetUnitSnapshot(FName UnitId, FLBSupportRobotSaveState& OutState) const;

    UFUNCTION(BlueprintPure, Category = "Line Boss|Press Shop|Support Fleet|Save")
    bool WasFleetRestoredFromDisk() const { return bRestoredFromDisk; }

    UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "Line Boss|Press Shop|Support Fleet|Save")
    FString CampaignSlotName = TEXT("LB_PRESS_SHOP_CAMPAIGN");

    UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "Line Boss|Press Shop|Support Fleet|Save")
    int32 CampaignUserIndex = 0;

    UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "Line Boss|Press Shop|Support Fleet|Save")
    bool bAutoLoadCampaignFleet = true;

    /**
     * Reference-layout mode for clean/player-built maps. Berth roots are read from the
     * installed robot actors instead of the retired fixed-map coordinate preset.
     */
    UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "Line Boss|Press Shop|Support Fleet|Layout")
    bool bUseInstalledActorTransforms = false;

    /** Shared service aisle used by the clean reference layout. Player-authored route assets supersede this preset. */
    UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "Line Boss|Press Shop|Support Fleet|Layout", meta = (EditCondition = "bUseInstalledActorTransforms"))
    float InstalledLayoutServiceAisleY = -3500.0f;

    /** Common dispatch standby point for the clean reference layout. */
    UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "Line Boss|Press Shop|Support Fleet|Layout", meta = (EditCondition = "bUseInstalledActorTransforms"))
    FVector InstalledLayoutStandbyPoint = FVector(0.0f, -3500.0f, 0.0f);

private:
    UPROPERTY(Transient)
    TMap<FName, TObjectPtr<ALBSupportRobot>> InstalledRobots;

    TMap<FName, FName> DockIds;
    TMap<FName, FVector> BerthRoots;
    TMap<FName, FVector> ApronPoints;
    TMap<FName, FVector> AislePoints;
    TMap<FName, FVector> StandbyPoints;
    TMap<FName, TArray<FVector>> OutboundWaypoints;
    bool bFleetReady = false;
    bool bRestoredFromDisk = false;

    ALBSupportRobot* FindUnit(FName UnitId) const;
    bool DiscoverInstalledFleet();
    bool BuildInstalledTransformRoutes();
    bool ConfigureAutomaticReturn(ALBSupportRobot* Robot, FName UnitId);
    bool RevalidateRestoredRobot(ALBSupportRobot* Robot, FName ExpectedDockId, bool bWasDocked);
    bool CommissionRobot(ALBSupportRobot* Robot, FName DockId);
};
