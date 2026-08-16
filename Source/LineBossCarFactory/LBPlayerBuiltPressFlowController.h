#pragma once

#include "CoreMinimal.h"
#include "GameFramework/Actor.h"
#include "LBBodyWeldLineActor.h"
#include "LBCompactStillageFLT.h"
#include "LBPlayerBuiltPressFlowController.generated.h"

class ALBFactoryBuildMachine;
class ALBPressShopStorageZone;
class ALBPressTrainAStation;
class ALBStillageFLTFleetController;
class ALBECoatLineActor;
class ALBFactoryTransportLink;

UENUM(BlueprintType)
enum class ELBPanelDisposition : uint8
{
    Pending,
    Good,
    Rejected
};

UENUM(BlueprintType)
enum class ELBPanelFlowStage : uint8
{
    BlankReserved,
    Pressing,
    PressOutput,
    Inspection,
    Inspected,
    WIPStillage,
    WeldShopIntake,
    Rejected,
    /** Exact physical ownership has crossed the stage-9 dock into the composite weld line. */
    BodyWeldInventory
};

USTRUCT(BlueprintType)
struct FLBPanelLineageRecord
{
    GENERATED_BODY()

    UPROPERTY(EditAnywhere, BlueprintReadWrite, SaveGame) FName PanelId;
    UPROPERTY(EditAnywhere, BlueprintReadWrite, SaveGame) FName BlankId;
    UPROPERTY(EditAnywhere, BlueprintReadWrite, SaveGame) FName OrderId;
    UPROPERTY(EditAnywhere, BlueprintReadWrite, SaveGame) FName VehicleModelId;
    UPROPERTY(EditAnywhere, BlueprintReadWrite, SaveGame) FName PanelTypeId;
    UPROPERTY(EditAnywhere, BlueprintReadWrite, SaveGame) FName SourceTrainId;
    UPROPERTY(EditAnywhere, BlueprintReadWrite, SaveGame) FName StillageId;
    UPROPERTY(EditAnywhere, BlueprintReadWrite, SaveGame) ELBPanelDisposition Disposition = ELBPanelDisposition::Pending;
    UPROPERTY(EditAnywhere, BlueprintReadWrite, SaveGame) ELBPanelFlowStage Stage = ELBPanelFlowStage::BlankReserved;
};

USTRUCT(BlueprintType)
struct FLBPanelStillageLoad
{
    GENERATED_BODY()

    UPROPERTY(EditAnywhere, BlueprintReadWrite, SaveGame) FName StillageId;
    UPROPERTY(EditAnywhere, BlueprintReadWrite, SaveGame) FName OrderId;
    UPROPERTY(EditAnywhere, BlueprintReadWrite, SaveGame) FName VehicleModelId;
    UPROPERTY(EditAnywhere, BlueprintReadWrite, SaveGame) FName PanelTypeId;
    UPROPERTY(EditAnywhere, BlueprintReadWrite, SaveGame) int32 CapacityPanels = 1;
    UPROPERTY(EditAnywhere, BlueprintReadWrite, SaveGame) TArray<FName> PanelIds;
    UPROPERTY(EditAnywhere, BlueprintReadWrite, SaveGame) bool bReadyForWeld = false;
    /** Legacy name retained: this means the exact stillage completed the stage-9 intake prerequisite. */
    UPROPERTY(EditAnywhere, BlueprintReadWrite, SaveGame) bool bDeliveredToWeld = false;
    UPROPERTY(EditAnywhere, BlueprintReadWrite, SaveGame) FName WeldLineId = NAME_None;
    UPROPERTY(EditAnywhere, BlueprintReadWrite, SaveGame) FName WeldDeliveryJobId = NAME_None;
    UPROPERTY(EditAnywhere, BlueprintReadWrite, SaveGame) int64 WeldDeliverySequence = 0;
    UPROPERTY(EditAnywhere, BlueprintReadWrite, SaveGame) bool bAcceptedByBodyWeld = false;
    UPROPERTY(EditAnywhere, BlueprintReadWrite, SaveGame) FName EmptyReturnJobId = NAME_None;
    UPROPERTY(EditAnywhere, BlueprintReadWrite, SaveGame) bool bEmptyReturnQueued = false;
    UPROPERTY(EditAnywhere, BlueprintReadWrite, SaveGame) bool bReturnedEmpty = false;
};

/**
 * Saved compatibility-adapter delivery for the finite supplied BIW base kit.
 * DeliveryAuthorityId names the real stage-9 GeneralParts endpoint; this record is not a
 * claim that an FLT physically carried the kit.
 */
USTRUCT(BlueprintType)
struct FLBBodyWeldBaseKitDeliveryRecord
{
    GENERATED_BODY()

    UPROPERTY(EditAnywhere, BlueprintReadWrite, SaveGame) FLBBodyWeldBaseKitUnit BaseKit;
    UPROPERTY(EditAnywhere, BlueprintReadWrite, SaveGame) FName DeliveryAuthorityId = NAME_None;
    UPROPERTY(EditAnywhere, BlueprintReadWrite, SaveGame) FName TargetWeldLineId = NAME_None;
    UPROPERTY(EditAnywhere, BlueprintReadWrite, SaveGame) bool bTransferred = false;
};

USTRUCT(BlueprintType)
struct FLBVehiclePanelBatch
{
    GENERATED_BODY()

    UPROPERTY(EditAnywhere, BlueprintReadWrite, SaveGame) FName OrderId;
    /** Stable product-program identity. The first playable vehicle is the Cairnwell 2040 BEV. */
    UPROPERTY(EditAnywhere, BlueprintReadWrite, SaveGame) FName VehicleModelId = TEXT("CAIRNWELL_2040");
    UPROPERTY(EditAnywhere, BlueprintReadWrite, SaveGame) FName PanelTypeId = TEXT("DOOR_FRONT_LEFT");
    /** Optional prepared-blank source/line. None means any compatible line. */
    UPROPERTY(EditAnywhere, BlueprintReadWrite, SaveGame) FName ProductionLineId;
    UPROPERTY(EditAnywhere, BlueprintReadWrite, SaveGame) FName DedicatedTrainId;
    UPROPERTY(EditAnywhere, BlueprintReadWrite, SaveGame, meta=(ClampMin="1")) int32 RequestedQuantity = 10;
    UPROPERTY(VisibleAnywhere, BlueprintReadOnly, SaveGame) int32 DispatchedQuantity = 0;
};

USTRUCT(BlueprintType)
struct FLBPlayerBuiltPressFlowSaveState
{
    GENERATED_BODY()
    UPROPERTY(EditAnywhere, BlueprintReadWrite, SaveGame) int32 Version = 4;
    UPROPERTY(EditAnywhere, BlueprintReadWrite, SaveGame) TArray<FLBVehiclePanelBatch> PanelBatches;
    UPROPERTY(EditAnywhere, BlueprintReadWrite, SaveGame) TArray<FLBPanelLineageRecord> PanelLineage;
    UPROPERTY(EditAnywhere, BlueprintReadWrite, SaveGame) TArray<FLBPanelStillageLoad> PanelStillages;
    UPROPERTY(EditAnywhere, BlueprintReadWrite, SaveGame) TArray<FLBBodyWeldBaseKitDeliveryRecord> PendingBaseKitDeliveries;
    UPROPERTY(EditAnywhere, BlueprintReadWrite, SaveGame) TArray<FLBBodyWeldBaseKitDeliveryRecord> TransferredBaseKitDeliveries;
    UPROPERTY(EditAnywhere, BlueprintReadWrite, SaveGame) int32 NextStillageSerial = 1;
    UPROPERTY(EditAnywhere, BlueprintReadWrite, SaveGame) int64 NextBodyWeldDeliverySequence = 1;
    UPROPERTY(EditAnywhere, BlueprintReadWrite, SaveGame) bool bAutomaticFlowEnabled = true;
};

/** Transactional material movement for a player-built Press Shop chain. */
UCLASS(BlueprintType)
class LINEBOSSCARFACTORY_API ALBPlayerBuiltPressFlowController : public AActor
{
    GENERATED_BODY()

public:
    ALBPlayerBuiltPressFlowController();

    virtual void BeginPlay() override;
    virtual void Tick(float DeltaSeconds) override;

    UFUNCTION(BlueprintCallable, Category="Cairnwell|Factory Builder|Material Flow")
    bool TransferMachineOutputToStorage(ALBFactoryBuildMachine* Source,
        ALBPressShopStorageZone* Target, FString& OutReason);

    UFUNCTION(BlueprintCallable, Category="Cairnwell|Factory Builder|Material Flow")
    bool TransferStorageToMachine(ALBPressShopStorageZone* Source,
        ALBFactoryBuildMachine* Target, FString& OutReason);

    UFUNCTION(BlueprintCallable, Category="Cairnwell|Factory Builder|Material Flow")
    bool TransferMachineOutputToMachine(ALBFactoryBuildMachine* Source,
        ALBFactoryBuildMachine* Target, FString& OutReason);

    UFUNCTION(BlueprintCallable, Category="Cairnwell|Factory Builder|Material Flow")
    bool ProcessMachine(ALBFactoryBuildMachine* Machine, FName& OutUnitId, FString& OutReason);

    UFUNCTION(BlueprintCallable, Category="Cairnwell|Factory Builder|Material Flow")
    bool TransferBlankBufferToTrain(ALBPressShopStorageZone* Source,
        ALBPressTrainAStation* Target, FString& OutReason);

    UFUNCTION(BlueprintCallable, Category="Cairnwell|Factory Builder|Material Flow")
    bool TransferTrainPanelToInspection(ALBPressTrainAStation* Source,
        ALBFactoryBuildMachine* Target, FString& OutReason);

    /** Completes the closed logistics loop after weld has unloaded a delivered stillage. */
    UFUNCTION(BlueprintCallable, Category="Cairnwell|Factory Builder|Material Flow")
    bool ReturnEmptyStillageFromWeld(FName StillageId,
        ALBPressShopStorageZone* EmptyStorage, FString& OutReason);

    /**
     * Registers one finite supplier/adaptor payload. The scheduler transfers it only through
     * a compatible saved stage-9 GeneralParts/AGVHandoff endpoint into the exact weld LineId.
     */
    UFUNCTION(BlueprintCallable, Category="Cairnwell|Factory Builder|Body Weld")
    bool QueueBodyWeldBaseKitDelivery(const FLBBodyWeldBaseKitUnit& BaseKit,
        FName DeliveryAuthorityId, FName TargetWeldLineId, FString& OutReason);

    /** One bounded deterministic pass over physical weld logistics, recipe and ED handoff. */
    UFUNCTION(BlueprintCallable, Category="Cairnwell|Factory Builder|Body Weld")
    int32 ExecuteBodyWeldIntegrationStep(FString& OutSummary);

    /** Advances every connected player-built process by one bounded deterministic scheduler pass. */
    UFUNCTION(BlueprintCallable, Category="Cairnwell|Factory Builder|Material Flow")
    int32 ExecuteAutomaticStep(FString& OutSummary);

    UFUNCTION(BlueprintCallable, Category="Cairnwell|Factory Builder|Material Flow")
    void SetAutomaticFlowEnabled(bool bEnabled) { bAutomaticFlowEnabled = bEnabled; }

    UFUNCTION(BlueprintPure, Category="Cairnwell|Factory Builder|Material Flow")
    bool IsAutomaticFlowEnabled() const { return bAutomaticFlowEnabled; }

    /** Allows the clean player-builder scheduler to power/start only locally proved healthy trains. */
    UFUNCTION(BlueprintCallable, Category="Cairnwell|Factory Builder|Material Flow")
    void SetConsoleFreeTrainAutostartEnabled(bool bEnabled) { bConsoleFreeTrainAutostartEnabled = bEnabled; }

    UFUNCTION(BlueprintPure, Category="Cairnwell|Factory Builder|Material Flow")
    bool IsConsoleFreeTrainAutostartEnabled() const { return bConsoleFreeTrainAutostartEnabled; }

    UFUNCTION(BlueprintPure, Category="Cairnwell|Factory Builder|Material Flow")
    FString GetLastAutomaticFlowSummary() const { return LastAutomaticFlowSummary; }

    /** Adds a pre-production vehicle panel order. Tooling/changeover is inferred automatically from panel type. */
    UFUNCTION(BlueprintCallable, Category="Cairnwell|Factory Builder|Production Orders")
    bool QueuePanelBatch(const FLBVehiclePanelBatch& Batch, FString& OutReason);
    UFUNCTION(BlueprintPure, Category="Cairnwell|Factory Builder|Production Orders")
    TArray<FLBVehiclePanelBatch> GetPanelBatches() const { return PanelBatches; }
    UFUNCTION(BlueprintPure, Category="Cairnwell|Factory Builder|Traceability")
    TArray<FLBPanelLineageRecord> GetPanelLineage() const { return PanelLineage; }
    UFUNCTION(BlueprintPure, Category="Cairnwell|Factory Builder|Traceability")
    TArray<FLBPanelStillageLoad> GetPanelStillages() const { return PanelStillages; }
    UFUNCTION(BlueprintPure, Category="Cairnwell|Factory Builder|Body Weld")
    TArray<FLBBodyWeldBaseKitDeliveryRecord> GetPendingBodyWeldBaseKitDeliveries() const
    { return PendingBaseKitDeliveries; }
    UFUNCTION(BlueprintPure, Category="Cairnwell|Factory Builder|Body Weld")
    TArray<FLBBodyWeldBaseKitDeliveryRecord> GetTransferredBodyWeldBaseKitDeliveries() const
    { return TransferredBaseKitDeliveries; }
    UFUNCTION(BlueprintPure, Category="Cairnwell|Factory Builder|Production Orders")
    FName GetProductionLineIdForTrain(const ALBPressTrainAStation* Train) const;
    UFUNCTION(BlueprintPure, Category="Cairnwell|Factory Builder|Save")
    FLBPlayerBuiltPressFlowSaveState CaptureSaveState() const;
    /** Mutation-free payload preflight for root campaign save validation. */
    static bool ValidateSaveState(const FLBPlayerBuiltPressFlowSaveState& State,
        FString& OutReason);
    /** Backward-compatible descriptive alias for callers already using this name. */
    static bool IsSaveStateContractValid(const FLBPlayerBuiltPressFlowSaveState& State,
        FString& OutReason);
    UFUNCTION(BlueprintCallable, Category="Cairnwell|Factory Builder|Save")
    bool RestoreSaveState(const FLBPlayerBuiltPressFlowSaveState& State);

private:
    bool RecordLinkedTransfer(const AActor* Source, const AActor* Target, FString& OutReason) const;
    bool TryStartConsoleFreeTrain(ALBPressTrainAStation* Target, FString& OutReason) const;
    FLBVehiclePanelBatch* SelectBatchForTrain(const ALBPressTrainAStation* Train, const AActor* BlankSource);
    void BindKnownPressTrains();
    void BindKnownStillageFleets();
    ALBStillageFLTFleetController* FindStillageFleet() const;
    bool HasOutstandingStillageJob(FName StillageId) const;
    bool EnqueueReadyStillageTransfer(ALBPressShopStorageZone* Source,
        ALBFactoryBuildMachine* Target, FString& OutReason);
    ALBPressShopStorageZone* FindStorageByAuthorityId(FName AuthorityId) const;
    ALBFactoryBuildMachine* FindMachineByAuthorityId(FName AuthorityId) const;
    ALBBodyWeldLineActor* FindBodyWeldLineByAuthorityId(FName AuthorityId) const;
    ALBFactoryTransportLink* FindExactLink(const ULBFactoryProcessPortComponent* SourcePort,
        const ULBFactoryProcessPortComponent* TargetPort) const;
    bool IsAuthoritativeFleetDelivery(FName JobId, FName StillageId,
        ELBStillageFLTJobType JobType, FName SourceAuthorityId, FName TargetAuthorityId,
        FLBStillageFLTJob& OutJob) const;
    void ReconcileStillageFleetDeliveries();
    bool EnqueueCompletedStillageToBodyWeld(FString& OutReason);
    bool CommitStillageToBodyWeld(const FLBStillageFLTJob* DeliveryJob,
        ALBFactoryBuildMachine* SourceDock, ALBBodyWeldLineActor* TargetLine,
        FLBPanelStillageLoad& Load, FString& OutReason);
    bool TransferOneBaseKitToBodyWeld(FString& OutReason);
    bool DispatchOneEmptyStillageReturn(FString& OutReason);
    bool CommitEmptyStillageReturn(const FLBStillageFLTJob& DeliveryJob,
        FLBPanelStillageLoad& Load, FString& OutReason);
    int32 AdvanceBodyWeldRecipes(FString& OutReason);
    int32 HandoffReadyBodyToECoat(FString& OutReason);
    void RefreshStillageReadiness(FName OrderId);
    FLBPanelLineageRecord* FindLineageByPanelId(FName PanelId);
    FLBPanelStillageLoad* FindOpenStillage(const FLBPanelLineageRecord& Panel);
    FLBPanelStillageLoad* FindReadyStoredStillage(const ALBPressShopStorageZone* Source);
    ALBPressShopStorageZone* FindEmptyStillageStorage() const;
    ALBPressShopStorageZone* FindEmptyStillageReturnStorage() const;
    bool PackInspectedPanelIntoStillage(ALBFactoryBuildMachine* Source,
        ALBPressShopStorageZone* Target, FString& OutReason);

    UFUNCTION()
    void HandlePressPanelCompleted(FName PanelId, bool bInspectionPass);

    UFUNCTION()
    void HandleStillageFleetDelivered(FName JobId, FName StillageId,
        ELBStillageFLTJobType JobType, FName SourceAuthorityId, FName TargetAuthorityId);
    UPROPERTY(EditAnywhere, Category="Cairnwell|Factory Builder|Material Flow")
    bool bAutomaticFlowEnabled = true;

    /** Disabled by default so legacy console maps retain their existing start authority. */
    UPROPERTY(EditInstanceOnly, Category="Cairnwell|Factory Builder|Material Flow")
    bool bConsoleFreeTrainAutostartEnabled = false;

    /** Gameplay scheduler cadence, not an engineering cycle-time claim. */
    UPROPERTY(EditAnywhere, Category="Cairnwell|Factory Builder|Material Flow", meta=(ClampMin="0.1"))
    float AutomaticStepIntervalSeconds = 0.5f;

    UPROPERTY(VisibleInstanceOnly, Category="Cairnwell|Factory Builder|Material Flow")
    FString LastAutomaticFlowSummary = TEXT("AUTOMATIC FLOW READY");

    UPROPERTY(EditInstanceOnly, Category="Cairnwell|Factory Builder|Production Orders")
    TArray<FLBVehiclePanelBatch> PanelBatches;

    UPROPERTY(VisibleInstanceOnly, Category="Cairnwell|Factory Builder|Traceability")
    TArray<FLBPanelLineageRecord> PanelLineage;

    UPROPERTY(VisibleInstanceOnly, Category="Cairnwell|Factory Builder|Traceability")
    TArray<FLBPanelStillageLoad> PanelStillages;

    UPROPERTY(VisibleInstanceOnly, Category="Cairnwell|Factory Builder|Body Weld")
    TArray<FLBBodyWeldBaseKitDeliveryRecord> PendingBaseKitDeliveries;

    UPROPERTY(VisibleInstanceOnly, Category="Cairnwell|Factory Builder|Body Weld")
    TArray<FLBBodyWeldBaseKitDeliveryRecord> TransferredBaseKitDeliveries;

    UPROPERTY(VisibleInstanceOnly, Category="Cairnwell|Factory Builder|Traceability")
    int32 NextStillageSerial = 1;

    UPROPERTY(VisibleInstanceOnly, Category="Cairnwell|Factory Builder|Body Weld")
    int64 NextBodyWeldDeliverySequence = 1;

    /** Approved compact Cairnwell pressed-panel stillage half-footprint. */
    UPROPERTY(EditAnywhere, Category="Cairnwell|Factory Builder|Material Flow",
        meta=(ClampMin="20.0", ClampMax="250.0"))
    FVector2D WipStillageHalfExtentCm = FVector2D(85.0f, 155.0f);

    float AutomaticStepAccumulator = 0.0f;
};
