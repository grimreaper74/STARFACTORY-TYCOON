#pragma once

#include "CoreMinimal.h"
#include "GameFramework/SaveGame.h"
#include "LBCleaningAMR.h"
#include "LBMaintenanceAMR.h"
#include "LBPR004Station.h"
#include "LBPR005Station.h"
#include "LBPR006Station.h"
#include "LBPR007Station.h"
#include "LBPR008Station.h"
#include "LBPR009Station.h"
#include "LBPR010Station.h"
#include "LBPressTrainAStation.h"
#include "LBSupportCraneController.h"
#include "LBControlRoomOperationsConsole.h"
#include "LBFactoryConnectionSubsystem.h"
#include "LBFactoryBuildMachine.h"
#include "LBFactoryAGVInfrastructure.h"
#include "LBPressShopStorageZone.h"
#include "LBCoilAGVController.h"
#include "LBInboundDeliveryController.h"
#include "LBFactoryBrandSubsystem.h"
#include "LBPlayerBuiltPressFlowController.h"
#include "LBBodyWeldLineActor.h"
#include "LBECoatLineActor.h"
#include "LBStillageFLTFleetController.h"
#include "LBFactoryManagementSubsystem.h"
#include "LBPressShopSaveGame.generated.h"

/**
 * Explicit campaign topology. Legacy authored saves own the fixed PR-004..PR-010
 * actor chain and operations console; player-built saves own only the dynamic
 * factory graph. Keeping Legacy first makes pre-v17 files deserialize to the only
 * topology they historically supported.
 */
UENUM(BlueprintType)
enum class ELBCampaignTopologyMode : uint8
{
    LegacyAuthoredPressShop,
    PlayerBuiltFactory
};

/** Versioned campaign save root. Other Press stations are added as they become operational. */
UCLASS(BlueprintType)
class LINEBOSSCARFACTORY_API ULBPressShopSaveGame : public USaveGame
{
    GENERATED_BODY()

public:
    UPROPERTY(EditAnywhere, BlueprintReadWrite, SaveGame, Category = "Line Boss|Save")
    int32 SaveFormatVersion = 18;

    /** Authoritative topology discriminator from v17 onward. */
    UPROPERTY(EditAnywhere, BlueprintReadWrite, SaveGame, Category = "Line Boss|Save")
    ELBCampaignTopologyMode TopologyMode = ELBCampaignTopologyMode::LegacyAuthoredPressShop;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, SaveGame, Category = "Line Boss|Save")
    FString CampaignId = TEXT("THE_RESTART_PRESS_SHOP");

    UPROPERTY(EditAnywhere, BlueprintReadWrite, SaveGame, Category = "Line Boss|Save")
    FDateTime SavedAtUtc;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, SaveGame, Category = "Line Boss|Save")
    FLBFactoryBrandSaveState FactoryBrand;

    /** Deterministic finance/research/quality/maintenance/analytics authority. */
    UPROPERTY(EditAnywhere, BlueprintReadWrite, SaveGame, Category = "Line Boss|Save")
    FLBFactoryManagementSaveState FactoryManagement;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, SaveGame, Category = "Line Boss|Save")
    FLBPR004SaveState PR004;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, SaveGame, Category = "Line Boss|Save")
    FLBPR005SaveState PR005;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, SaveGame, Category = "Line Boss|Save")
    FLBPR006SaveState PR006;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, SaveGame, Category = "Line Boss|Save")
    FLBPR007SaveState PR007;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, SaveGame, Category = "Line Boss|Save")
    FLBPR008SaveState PR008;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, SaveGame, Category = "Line Boss|Save")
    FLBPR009SaveState PR009;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, SaveGame, Category = "Line Boss|Save")
    FLBPR010SaveState PR010;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, SaveGame, Category = "Line Boss|Save")
    FLBPressTrainASaveState PressTrainA;

    /** Current multi-train records, keyed by immutable PersistentTrainGuid. PressTrainA remains for v12 migration. */
    UPROPERTY(EditAnywhere, BlueprintReadWrite, SaveGame, Category = "Line Boss|Save")
    TArray<FLBPressTrainASaveState> PressTrains;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, SaveGame, Category = "Line Boss|Save")
    TArray<FLBCleaningAMRSaveState> CleaningRobots;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, SaveGame, Category = "Line Boss|Save")
    TArray<FLBMaintenanceAMRSaveState> MaintenanceRobots;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, SaveGame, Category = "Line Boss|Save")
    FLBSupportCraneSaveState FrontEndSupportCrane;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, SaveGame, Category = "Line Boss|Save")
    FLBControlRoomOperationsSaveState ControlRoomOperations;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, SaveGame, Category = "Line Boss|Save")
    TArray<FLBFactoryTransportLinkSaveState> FactoryTransportLinks;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, SaveGame, Category = "Line Boss|Save")
    TArray<FLBPressShopStorageZoneSaveState> PlayerStorageZones;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, SaveGame, Category = "Line Boss|Save")
    TArray<FLBFactoryBuildMachineSaveState> PlayerBuiltMachines;

    /** Player-placed composite body-weld authority, introduced by save format 18. */
    UPROPERTY(EditAnywhere, BlueprintReadWrite, SaveGame, Category = "Line Boss|Save")
    TArray<FLBBodyWeldLineSaveState> PlayerBuiltBodyWeldLines;

    /** Player-placed whole-factory ED line state, separate from compact press-shop machines. */
    UPROPERTY(EditAnywhere, BlueprintReadWrite, SaveGame, Category = "Line Boss|Save")
    TArray<FLBECoatLineSaveState> PlayerBuiltECoatLines;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, SaveGame)
    TArray<FLBFactoryAGVInfrastructureSaveState> PlayerBuiltAGVInfrastructure;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, SaveGame, Category = "Line Boss|Save")
    bool bHasInboundDelivery = false;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, SaveGame, Category = "Line Boss|Save")
    FLBCoilAGVSaveState InboundCoilAGV;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, SaveGame, Category = "Line Boss|Save")
    FLBInboundDeliverySaveState InboundDelivery;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, SaveGame, Category = "Line Boss|Save")
    FLBPlayerBuiltPressFlowSaveState PlayerProductionOrders;

    /** Compact press-WIP stillage FLTs, including paid capacity and exact queued/claimed jobs. */
    UPROPERTY(EditAnywhere, BlueprintReadWrite, SaveGame, Category = "Line Boss|Save")
    FLBStillageFLTFleetSaveState StillageFLTFleet;
};
