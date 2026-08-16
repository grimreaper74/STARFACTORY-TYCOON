#pragma once

#include "CoreMinimal.h"
#include "GameFramework/Actor.h"
#include "LBPressTrainAStation.generated.h"

class USceneComponent;
class ATextRenderActor;
class UAudioComponent;
class USoundBase;
class ULBFactoryProcessPortComponent;
class ULBStatusBeaconComponent;

UENUM(BlueprintType)
enum class ELBPressTrainAState : uint8
{
    Isolated,
    Ready,
    Cycling,
    Stopping,
    Fault
};

UENUM(BlueprintType)
enum class ELBPressTrainAPhase : uint8
{
    WaitingForBlank,
    DestackAndLoad,
    TransferToS02,
    DrawS02,
    TransferToS03,
    FormS03,
    TransferToS04,
    TrimS04,
    TransferToS05,
    PierceS05,
    TransferToS06,
    RestrikeS06,
    TransferToS07,
    UnloadAndInspect,
    StillageOutput
};

UENUM(BlueprintType)
enum class ELBPressTrainAFault : uint8
{
    None,
    EmergencyStopActive,
    AccessInterlockOpen,
    SafetyCircuitUnhealthy,
    ReservedBlankUnavailable,
    DestackFault,
    TransferFault,
    HydraulicPressureLow,
    PressOverload,
    InspectionUnavailable,
    StillageOutputBlocked
};

UENUM(BlueprintType)
enum class ELBPressTrainACommand : uint8
{
    PowerOn,
    PowerOff,
    Start,
    ControlledStop,
    AcknowledgeAlarm,
    Reset,
    RequestIsolation,
    ReleaseIsolation
};

USTRUCT(BlueprintType)
struct FLBPressTrainAHMIStatus
{
    GENERATED_BODY()

    UPROPERTY(BlueprintReadOnly) FName TrainId = TEXT("TRAIN_A");
    UPROPERTY(BlueprintReadOnly) ELBPressTrainAState State = ELBPressTrainAState::Isolated;
    UPROPERTY(BlueprintReadOnly) ELBPressTrainAPhase Phase = ELBPressTrainAPhase::WaitingForBlank;
    UPROPERTY(BlueprintReadOnly) ELBPressTrainAFault ActiveFault = ELBPressTrainAFault::None;
    UPROPERTY(BlueprintReadOnly) float CycleProgress = 0.0f;
    UPROPERTY(BlueprintReadOnly) float TargetStrokesPerMinute = 10.0f;
    UPROPERTY(BlueprintReadOnly) float HydraulicPressureBar = 280.0f;
    UPROPERTY(BlueprintReadOnly) float PressLoadPercent = 0.0f;
    UPROPERTY(BlueprintReadOnly) int32 PendingBlankCount = 0;
    UPROPERTY(BlueprintReadOnly) FName OldestPendingBlankId;
    UPROPERTY(BlueprintReadOnly) FName InProcessBlankId;
    UPROPERTY(BlueprintReadOnly) int32 GoodPanels = 0;
    UPROPERTY(BlueprintReadOnly) int32 RejectedPanels = 0;
    UPROPERTY(BlueprintReadOnly) int32 PendingPanelCount = 0;
    UPROPERTY(BlueprintReadOnly) FName OldestPendingPanelId;
    UPROPERTY(BlueprintReadOnly) bool bControlPowerOn = false;
    UPROPERTY(BlueprintReadOnly) bool bAccessInterlocksClosed = true;
    UPROPERTY(BlueprintReadOnly) bool bSafetyCircuitHealthy = true;
    UPROPERTY(BlueprintReadOnly) bool bEmergencyStopActive = false;
    UPROPERTY(BlueprintReadOnly) bool bDestackHealthy = true;
    UPROPERTY(BlueprintReadOnly) bool bTransferHealthy = true;
    UPROPERTY(BlueprintReadOnly) bool bInspectionHealthy = true;
    UPROPERTY(BlueprintReadOnly) bool bStillageOutputClear = true;
    UPROPERTY(BlueprintReadOnly) bool bAlarmAcknowledged = false;
    UPROPERTY(BlueprintReadOnly) bool bIsolationRequested = false;
    UPROPERTY(BlueprintReadOnly) bool bZeroEnergyProved = false;
    UPROPERTY(BlueprintReadOnly) bool bRestartRequiredAfterLoad = false;
    UPROPERTY(BlueprintReadOnly) FName LastCommandSource;
    UPROPERTY(BlueprintReadOnly) FName LastSafetyEvidenceId;
    UPROPERTY(BlueprintReadOnly) bool bCanStart = false;
    UPROPERTY(BlueprintReadOnly) TArray<FText> BlockingReasons;
};

USTRUCT(BlueprintType)
struct FLBPressTrainASaveState
{
    GENERATED_BODY()

    UPROPERTY(EditAnywhere, BlueprintReadWrite, SaveGame) int32 Version = 4;
    UPROPERTY(EditAnywhere, BlueprintReadWrite, SaveGame) FGuid PersistentTrainGuid;
    UPROPERTY(EditAnywhere, BlueprintReadWrite, SaveGame) FName TrainId = TEXT("TRAIN_A");
    UPROPERTY(EditAnywhere, BlueprintReadWrite, SaveGame) FString TrainDisplayName = TEXT("TRAIN A");
    UPROPERTY(EditAnywhere, BlueprintReadWrite, SaveGame) FTransform WorldTransform = FTransform::Identity;
    UPROPERTY(EditAnywhere, BlueprintReadWrite, SaveGame) ELBPressTrainAState State = ELBPressTrainAState::Isolated;
    UPROPERTY(EditAnywhere, BlueprintReadWrite, SaveGame) ELBPressTrainAPhase Phase = ELBPressTrainAPhase::WaitingForBlank;
    UPROPERTY(EditAnywhere, BlueprintReadWrite, SaveGame) ELBPressTrainAFault ActiveFault = ELBPressTrainAFault::None;
    UPROPERTY(EditAnywhere, BlueprintReadWrite, SaveGame) TArray<FName> PendingBlankIds;
    UPROPERTY(EditAnywhere, BlueprintReadWrite, SaveGame) TArray<FName> PendingBlankReservationIds;
    UPROPERTY(EditAnywhere, BlueprintReadWrite, SaveGame) FName InProcessBlankId;
    UPROPERTY(EditAnywhere, BlueprintReadWrite, SaveGame) FName InProcessReservationId;
    UPROPERTY(EditAnywhere, BlueprintReadWrite, SaveGame) TArray<FName> PendingPanelIds;
    UPROPERTY(EditAnywhere, BlueprintReadWrite, SaveGame) FName PendingPanelHandoffTransactionId;
    UPROPERTY(EditAnywhere, BlueprintReadWrite, SaveGame) FName PendingPanelHandoffPanelId;
    UPROPERTY(EditAnywhere, BlueprintReadWrite, SaveGame) int32 NextPanelSerial = 1;
    UPROPERTY(EditAnywhere, BlueprintReadWrite, SaveGame) int32 GoodPanels = 0;
    UPROPERTY(EditAnywhere, BlueprintReadWrite, SaveGame) int32 RejectedPanels = 0;
    UPROPERTY(EditAnywhere, BlueprintReadWrite, SaveGame) FName ActiveVehicleModelId = NAME_None;
    UPROPERTY(EditAnywhere, BlueprintReadWrite, SaveGame) FName ActivePanelTypeId = NAME_None;
    UPROPERTY(EditAnywhere, BlueprintReadWrite, SaveGame) FName ActiveDieId = NAME_None;
    UPROPERTY(EditAnywhere, BlueprintReadWrite, SaveGame) float RunningHours = 0.0f;
    UPROPERTY(EditAnywhere, BlueprintReadWrite, SaveGame) float CycleElapsedSeconds = 0.0f;
    UPROPERTY(EditAnywhere, BlueprintReadWrite, SaveGame) float TargetStrokesPerMinute = 10.0f;
    UPROPERTY(EditAnywhere, BlueprintReadWrite, SaveGame) float HydraulicPressureBar = 280.0f;
    UPROPERTY(EditAnywhere, BlueprintReadWrite, SaveGame) float PressLoadPercent = 45.0f;
    UPROPERTY(EditAnywhere, BlueprintReadWrite, SaveGame) bool bControlPowerOn = false;
    UPROPERTY(EditAnywhere, BlueprintReadWrite, SaveGame) bool bAccessInterlocksClosed = true;
    UPROPERTY(EditAnywhere, BlueprintReadWrite, SaveGame) bool bSafetyCircuitHealthy = true;
    UPROPERTY(EditAnywhere, BlueprintReadWrite, SaveGame) bool bEmergencyStopActive = false;
    UPROPERTY(EditAnywhere, BlueprintReadWrite, SaveGame) bool bDestackHealthy = true;
    UPROPERTY(EditAnywhere, BlueprintReadWrite, SaveGame) bool bTransferHealthy = true;
    UPROPERTY(EditAnywhere, BlueprintReadWrite, SaveGame) bool bInspectionHealthy = true;
    UPROPERTY(EditAnywhere, BlueprintReadWrite, SaveGame) bool bStillageOutputClear = true;
    UPROPERTY(EditAnywhere, BlueprintReadWrite, SaveGame) bool bNextInspectionPass = true;
    UPROPERTY(EditAnywhere, BlueprintReadWrite, SaveGame) bool bAlarmAcknowledged = false;
    UPROPERTY(EditAnywhere, BlueprintReadWrite, SaveGame) bool bIsolationRequested = false;
    UPROPERTY(EditAnywhere, BlueprintReadWrite, SaveGame) bool bZeroEnergyProved = false;
    UPROPERTY(EditAnywhere, BlueprintReadWrite, SaveGame) bool bRestartRequiredAfterLoad = false;
    UPROPERTY(EditAnywhere, BlueprintReadWrite, SaveGame) FName LastCommandSource;
    UPROPERTY(EditAnywhere, BlueprintReadWrite, SaveGame) FName LastSafetyEvidenceId;
};

DECLARE_DYNAMIC_MULTICAST_DELEGATE_TwoParams(FLBPressTrainAStateChanged, ELBPressTrainAState, PreviousState, ELBPressTrainAState, NewState);
DECLARE_DYNAMIC_MULTICAST_DELEGATE_OneParam(FLBPressTrainAFaultRaised, ELBPressTrainAFault, Fault);
DECLARE_DYNAMIC_MULTICAST_DELEGATE_TwoParams(FLBPressTrainAPanelCompleted, FName, PanelId, bool, bInspectionPass);

/** Isolated native process, safety and persistence authority for Moorcross Press Train A. */
UCLASS(BlueprintType)
class LINEBOSSCARFACTORY_API ALBPressTrainAStation : public AActor
{
    GENERATED_BODY()

public:
    ALBPressTrainAStation();
    virtual void BeginPlay() override;
    virtual void EndPlay(const EEndPlayReason::Type EndPlayReason) override;
    virtual void Tick(float DeltaSeconds) override;

    UFUNCTION(BlueprintCallable, Category="Cairnwell|Press Train A") void SetControlPower(bool bEnabled);
    UFUNCTION(BlueprintCallable, Category="Cairnwell|Press Train A|Safety") void SetAccessInterlocksClosed(bool bClosed);
    UFUNCTION(BlueprintCallable, Category="Cairnwell|Press Train A|Safety") void SetSafetyCircuitHealthy(bool bHealthy);
    UFUNCTION(BlueprintCallable, Category="Cairnwell|Press Train A|Safety") void SetEmergencyStopActive(bool bActive);
    UFUNCTION(BlueprintCallable, Category="Cairnwell|Press Train A|Process") void SetDestackHealthy(bool bHealthy);
    UFUNCTION(BlueprintCallable, Category="Cairnwell|Press Train A|Process") void SetTransferHealthy(bool bHealthy);
    UFUNCTION(BlueprintCallable, Category="Cairnwell|Press Train A|Process") void SetHydraulicPressure(float PressureBar);
    UFUNCTION(BlueprintCallable, Category="Cairnwell|Press Train A|Process") void SetPressLoad(float LoadPercent);
    UFUNCTION(BlueprintCallable, Category="Cairnwell|Press Train A|Quality") void SetInspectionHealthy(bool bHealthy);
    UFUNCTION(BlueprintCallable, Category="Cairnwell|Press Train A|Quality") void SetNextInspectionPass(bool bPass);
    UFUNCTION(BlueprintCallable, Category="Cairnwell|Press Train A|Output") void SetStillageOutputClear(bool bClear);
    UFUNCTION(BlueprintCallable, Category="Cairnwell|Press Train A|Recipe") void SetTargetStrokesPerMinute(float StrokesPerMinute);
    /** Configure one isolated A-D variant without duplicating the proven process/safety authority. */
    UFUNCTION(BlueprintCallable, Category="Cairnwell|Press Trains|Identity") bool ConfigureTrainVariant(
        FName NewTrainId, const FString& NewDisplayName, const FString& NewPartFamily, FLinearColor NewAccentColor);
    UFUNCTION(BlueprintPure, Category="Cairnwell|Press Trains|Identity") FString GetTrainDisplayName() const { return TrainDisplayName; }
    UFUNCTION(BlueprintPure, Category="Cairnwell|Press Trains|Identity") FName GetTrainId() const { return TrainId; }
    UFUNCTION(BlueprintPure, Category="Cairnwell|Press Trains|Identity") FGuid GetPersistentTrainGuid() const { return PersistentTrainGuid; }
    UFUNCTION(BlueprintPure, Category="Cairnwell|Press Trains|Identity") FName GetStationId(int32 StationNumber) const;
    /** Identity-subsystem endpoint; gameplay code should register/restore through the subsystem. */
    void ApplyPersistentIdentity(const FGuid& NewGuid, FName NewTrainId, const FString& NewDisplayName);
    UFUNCTION(BlueprintPure, Category="Cairnwell|Press Trains|Identity") FString GetPartFamily() const { return PartFamily; }
    UFUNCTION(BlueprintCallable, Category="Cairnwell|Press Train A|Recipe")
    bool SetActiveProductionRecipe(FName VehicleModelId, FName PanelTypeId, FName DieId);
    UFUNCTION(BlueprintPure, Category="Cairnwell|Press Train A|Recipe") FName GetActiveVehicleModelId() const { return ActiveVehicleModelId; }
    UFUNCTION(BlueprintPure, Category="Cairnwell|Press Train A|Recipe") FName GetActivePanelTypeId() const { return ActivePanelTypeId; }
    UFUNCTION(BlueprintPure, Category="Cairnwell|Press Train A|Recipe") FName GetActiveDieId() const { return ActiveDieId; }
    /** Enables the approved complete Train A-D presentation for a player-built train. */
    UFUNCTION(BlueprintCallable, Category="Cairnwell|Press Trains|Presentation") bool EnableCompletedRuntimeVisual();
    UFUNCTION(BlueprintPure, Category="Cairnwell|Press Trains|Presentation") bool HasCompletedRuntimeVisual() const;
    UFUNCTION(BlueprintPure, Category="Cairnwell|Press Trains|Presentation")
    class UStaticMeshComponent* GetCompletedRuntimeVisualComponent() const { return CompletedRuntimeVisual; }
    UFUNCTION(BlueprintPure, Category="Cairnwell|Press Trains|Presentation")
    int32 GetApprovedModularVisualCount() const { return ApprovedModularTrainVisuals.Num(); }
    /** Car-independent flat sheet presented by S01; formed-panel art remains recipe-owned. */
    UFUNCTION(BlueprintPure, Category="Cairnwell|Press Trains|Presentation")
    class UStaticMeshComponent* GetDestackFeedBlankVisualComponent() const { return DestackFeedBlankVisual; }
    /** Current complete S01-S07 footprint, rooted at the S01 player-placement datum. */
    static FBox GetProtectedLocalEnvelope();

    UFUNCTION(BlueprintCallable, Category="Cairnwell|Press Train A|Material Flow") bool QueueReservedBlank(FName ReservationId, FName BlankId);
    UFUNCTION(BlueprintPure, Category="Cairnwell|Press Train A|Material Flow") int32 GetPendingBlankCount() const { return PendingBlankIds.Num(); }
    UFUNCTION(BlueprintPure, Category="Cairnwell|Press Train A|Material Flow") bool CanReleasePanel(TArray<FText>& BlockingReasons) const;
    UFUNCTION(BlueprintCallable, Category="Cairnwell|Press Train A|Material Flow") bool RequestPanelHandoff(FName TransactionId, FName& PanelId);
    UFUNCTION(BlueprintCallable, Category="Cairnwell|Press Train A|Material Flow") bool ConfirmPanelHandoff(FName TransactionId);
    UFUNCTION(BlueprintCallable, Category="Cairnwell|Press Train A|Material Flow") void CancelPanelHandoff(FName TransactionId);

    UFUNCTION(BlueprintCallable, Category="Cairnwell|Press Train A") bool StartLine();
    UFUNCTION(BlueprintCallable, Category="Cairnwell|Press Train A") void RequestControlledStop();
    UFUNCTION(BlueprintCallable, Category="Cairnwell|Press Train A|Safety") bool AcknowledgeAlarm(FName CommandSource);
    UFUNCTION(BlueprintCallable, Category="Cairnwell|Press Train A|Safety") bool ResetFault();
    UFUNCTION(BlueprintCallable, Category="Cairnwell|Press Train A|Safety") bool RequestIsolation(FName CommandSource);
    UFUNCTION(BlueprintCallable, Category="Cairnwell|Press Train A|Safety") bool ConfirmZeroEnergyIsolation(bool bZeroMotionVerified, bool bHydraulicPressureReleased, FName EvidenceId);
    UFUNCTION(BlueprintCallable, Category="Cairnwell|Press Train A|Safety") bool ReleaseIsolation(FName CommandSource, bool bGuardZoneClear);
    UFUNCTION(BlueprintCallable, Category="Cairnwell|Press Train A|Remote") bool ExecuteRemoteCommand(ELBPressTrainACommand Command, FName CommandSource, FName AuthorityId);
    UFUNCTION(BlueprintPure, Category="Cairnwell|Press Train A") bool CanStart(TArray<FText>& BlockingReasons) const;
    UFUNCTION(BlueprintPure, Category="Cairnwell|Press Train A|HMI") FLBPressTrainAHMIStatus GetHMIStatus() const;
    UFUNCTION(BlueprintPure, Category="Cairnwell|Press Train A|Save") FLBPressTrainASaveState CaptureSaveState() const;
    UFUNCTION(BlueprintCallable, Category="Cairnwell|Press Train A|Save") bool RestoreSaveState(const FLBPressTrainASaveState& SavedState);
    /** Deterministic requested-state query used by runtime audio validation. */
    UFUNCTION(BlueprintPure, Category="Cairnwell|Press Train A|Audio") bool IsAudioLayerRequested(FName LayerId) const;
    UFUNCTION(BlueprintPure, Category="Cairnwell|Press Train A|Audio") FName GetLastAudioCueId() const { return LastAudioCueId; }
    UFUNCTION(BlueprintPure, Category="Cairnwell|Press Train A|Audio") int32 GetAudioCueSequence() const { return AudioCueSequence; }
    UFUNCTION(BlueprintPure, Category="Cairnwell|Press Train A|Audio") bool HasCompleteAudioAssetSet() const;

    UPROPERTY(BlueprintAssignable, Category="Cairnwell|Press Train A") FLBPressTrainAStateChanged OnStateChanged;
    UPROPERTY(BlueprintAssignable, Category="Cairnwell|Press Train A") FLBPressTrainAFaultRaised OnFaultRaised;
    UPROPERTY(BlueprintAssignable, Category="Cairnwell|Press Train A") FLBPressTrainAPanelCompleted OnPanelCompleted;

    UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category="Cairnwell|Factory Builder|Connections") TObjectPtr<ULBFactoryProcessPortComponent> FactoryInputPort;
    UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category="Cairnwell|Factory Builder|Connections") TObjectPtr<ULBFactoryProcessPortComponent> FactoryOutputPort;

protected:
    UPROPERTY(VisibleAnywhere, BlueprintReadOnly) TObjectPtr<USceneComponent> StationRoot;
    /** Geometry-audited internal panel/cup centreline; end cells adapt this to the lower builder ports. */
    UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category="Cairnwell|Press Train A|Datums") TObjectPtr<USceneComponent> InternalProcessPanelDatum;
    UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category="Cairnwell|Press Trains|Presentation") TObjectPtr<class UStaticMeshComponent> CompletedRuntimeVisual;
    UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category="Cairnwell|Press Trains|Presentation") TArray<TObjectPtr<class UStaticMeshComponent>> ApprovedModularTrainVisuals;
    UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category="Cairnwell|Press Trains|Presentation") TObjectPtr<class UTextRenderComponent> TrainIdentityOperatorSide;
    UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category="Cairnwell|Press Trains|Presentation") TObjectPtr<class UTextRenderComponent> TrainIdentityServiceSide;
    /** One independent working stack per S01-S07 cell, not baked into replaceable Meshy art. */
    UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category="Cairnwell|Press Trains|Presentation") TArray<TObjectPtr<ULBStatusBeaconComponent>> CellStatusBeacons;
    UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category="Cairnwell|Press Train A|Motion") TObjectPtr<USceneComponent> DestackLiftMover;
    /** One real, flat feed blank. It is intentionally outside the 105 fixed machine modules. */
    UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category="Cairnwell|Press Train A|Motion") TObjectPtr<class UStaticMeshComponent> DestackFeedBlankVisual;
    UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category="Cairnwell|Press Train A|Motion") TObjectPtr<USceneComponent> TransferLiftMover;
    UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category="Cairnwell|Press Train A|Motion") TObjectPtr<USceneComponent> TransferPitchMover;
    UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category="Cairnwell|Press Train A|Motion") TArray<TObjectPtr<USceneComponent>> ApprovedTransferGapRoots;
    UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category="Cairnwell|Press Train A|Motion") TArray<TObjectPtr<USceneComponent>> ApprovedTransferLiftMovers;
    UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category="Cairnwell|Press Train A|Motion") TArray<TObjectPtr<USceneComponent>> ApprovedTransferPitchMovers;
    UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category="Cairnwell|Press Train A|Motion") TObjectPtr<USceneComponent> S02SlideMover;
    UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category="Cairnwell|Press Train A|Motion") TObjectPtr<USceneComponent> S03SlideMover;
    UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category="Cairnwell|Press Train A|Motion") TObjectPtr<USceneComponent> S04SlideMover;
    UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category="Cairnwell|Press Train A|Motion") TObjectPtr<USceneComponent> S05SlideMover;
    UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category="Cairnwell|Press Train A|Motion") TObjectPtr<USceneComponent> S06SlideMover;
    UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category="Cairnwell|Press Train A|Motion") TObjectPtr<USceneComponent> UnloadRobotMover;
    UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category="Cairnwell|Press Train A|Motion") TObjectPtr<USceneComponent> FormedPanelMover;
    UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category="Cairnwell|Press Train A|Audio") TObjectPtr<UAudioComponent> HydraulicPowerAudio;
    UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category="Cairnwell|Press Train A|Audio") TObjectPtr<UAudioComponent> TransferServoAudio;
    UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category="Cairnwell|Press Train A|Audio") TObjectPtr<UAudioComponent> RobotServoAudio;
    UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category="Cairnwell|Press Train A|Audio") TObjectPtr<UAudioComponent> WarningAlarmAudio;
    UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category="Cairnwell|Press Train A|Audio") TObjectPtr<UAudioComponent> PressCueAudio;
    UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category="Cairnwell|Press Train A|Audio") TObjectPtr<UAudioComponent> SafetyCueAudio;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, SaveGame, Category="Cairnwell|Identity") FGuid PersistentTrainGuid;
    UPROPERTY(EditAnywhere, BlueprintReadWrite, SaveGame, Category="Cairnwell|Identity") FName TrainId = TEXT("TRAIN_A");
    UPROPERTY(EditAnywhere, BlueprintReadWrite, SaveGame, Category="Cairnwell|Identity") FString TrainDisplayName = TEXT("TRAIN A");
    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="Cairnwell|Identity") FString PartFamily = TEXT("LARGE OUTER PANELS");
    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="Cairnwell|Identity") FLinearColor TrainAccentColor = FLinearColor(0.231f, 0.510f, 0.769f, 1.0f);
    UPROPERTY(EditAnywhere, BlueprintReadWrite, SaveGame, Category="Cairnwell|State") ELBPressTrainAState State = ELBPressTrainAState::Isolated;
    UPROPERTY(EditAnywhere, BlueprintReadWrite, SaveGame, Category="Cairnwell|State") ELBPressTrainAPhase Phase = ELBPressTrainAPhase::WaitingForBlank;
    UPROPERTY(EditAnywhere, BlueprintReadWrite, SaveGame, Category="Cairnwell|State") ELBPressTrainAFault ActiveFault = ELBPressTrainAFault::None;
    UPROPERTY(EditAnywhere, BlueprintReadWrite, SaveGame, Category="Cairnwell|Material Flow") TArray<FName> PendingBlankIds;
    UPROPERTY(EditAnywhere, BlueprintReadWrite, SaveGame, Category="Cairnwell|Material Flow") TArray<FName> PendingBlankReservationIds;
    UPROPERTY(EditAnywhere, BlueprintReadWrite, SaveGame, Category="Cairnwell|Material Flow") FName InProcessBlankId;
    UPROPERTY(EditAnywhere, BlueprintReadWrite, SaveGame, Category="Cairnwell|Material Flow") FName InProcessReservationId;
    UPROPERTY(EditAnywhere, BlueprintReadWrite, SaveGame, Category="Cairnwell|Material Flow") TArray<FName> PendingPanelIds;
    UPROPERTY(EditAnywhere, BlueprintReadWrite, SaveGame, Category="Cairnwell|Material Flow") FName PendingPanelHandoffTransactionId;
    UPROPERTY(EditAnywhere, BlueprintReadWrite, SaveGame, Category="Cairnwell|Material Flow") FName PendingPanelHandoffPanelId;
    UPROPERTY(EditAnywhere, BlueprintReadWrite, SaveGame, Category="Cairnwell|Production") int32 NextPanelSerial = 1;
    UPROPERTY(EditAnywhere, BlueprintReadWrite, SaveGame, Category="Cairnwell|Production") int32 GoodPanels = 0;
    UPROPERTY(EditAnywhere, BlueprintReadWrite, SaveGame, Category="Cairnwell|Production") int32 RejectedPanels = 0;
    UPROPERTY(EditAnywhere, BlueprintReadWrite, SaveGame, Category="Cairnwell|Production") FName ActiveVehicleModelId = NAME_None;
    UPROPERTY(EditAnywhere, BlueprintReadWrite, SaveGame, Category="Cairnwell|Production") FName ActivePanelTypeId = NAME_None;
    UPROPERTY(EditAnywhere, BlueprintReadWrite, SaveGame, Category="Cairnwell|Production") FName ActiveDieId = NAME_None;
    UPROPERTY(EditAnywhere, BlueprintReadWrite, SaveGame, Category="Cairnwell|Maintenance") float RunningHours = 0.0f;
    UPROPERTY(EditAnywhere, BlueprintReadWrite, SaveGame, Category="Cairnwell|Recipe", meta=(ClampMin="4.0", ClampMax="15.0")) float TargetStrokesPerMinute = 10.0f;
    UPROPERTY(EditAnywhere, BlueprintReadWrite, SaveGame, Category="Cairnwell|Process") float HydraulicPressureBar = 280.0f;
    UPROPERTY(EditAnywhere, BlueprintReadWrite, SaveGame, Category="Cairnwell|Process") float PressLoadPercent = 45.0f;
    UPROPERTY(EditAnywhere, BlueprintReadWrite, SaveGame, Category="Cairnwell|Safety") bool bControlPowerOn = false;
    UPROPERTY(EditAnywhere, BlueprintReadWrite, SaveGame, Category="Cairnwell|Safety") bool bAccessInterlocksClosed = true;
    UPROPERTY(EditAnywhere, BlueprintReadWrite, SaveGame, Category="Cairnwell|Safety") bool bSafetyCircuitHealthy = true;
    UPROPERTY(EditAnywhere, BlueprintReadWrite, SaveGame, Category="Cairnwell|Safety") bool bEmergencyStopActive = false;
    UPROPERTY(EditAnywhere, BlueprintReadWrite, SaveGame, Category="Cairnwell|Process") bool bDestackHealthy = true;
    UPROPERTY(EditAnywhere, BlueprintReadWrite, SaveGame, Category="Cairnwell|Process") bool bTransferHealthy = true;
    UPROPERTY(EditAnywhere, BlueprintReadWrite, SaveGame, Category="Cairnwell|Quality") bool bInspectionHealthy = true;
    UPROPERTY(EditAnywhere, BlueprintReadWrite, SaveGame, Category="Cairnwell|Quality") bool bNextInspectionPass = true;
    UPROPERTY(EditAnywhere, BlueprintReadWrite, SaveGame, Category="Cairnwell|Output") bool bStillageOutputClear = true;
    UPROPERTY(EditAnywhere, BlueprintReadWrite, SaveGame, Category="Cairnwell|Safety") bool bAlarmAcknowledged = false;
    UPROPERTY(EditAnywhere, BlueprintReadWrite, SaveGame, Category="Cairnwell|Safety") bool bIsolationRequested = false;
    UPROPERTY(EditAnywhere, BlueprintReadWrite, SaveGame, Category="Cairnwell|Safety") bool bZeroEnergyProved = false;
    UPROPERTY(EditAnywhere, BlueprintReadWrite, SaveGame, Category="Cairnwell|State") bool bRestartRequiredAfterLoad = false;
    UPROPERTY(EditAnywhere, BlueprintReadWrite, SaveGame, Category="Cairnwell|Authority") FName LastCommandSource;
    UPROPERTY(EditAnywhere, BlueprintReadWrite, SaveGame, Category="Cairnwell|Safety") FName LastSafetyEvidenceId;
    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="Cairnwell|Authority") FName RemoteAuthorityId = TEXT("CW.MW.CONTROL_ROOM");
    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="Cairnwell|Authority") bool bRemoteControlEnabled = true;

private:
    static constexpr float MinimumHydraulicPressureBar = 200.0f;
    static constexpr float MaximumPressLoadPercent = 100.0f;
    static constexpr int32 MaximumPendingBlanks = 4;
    static constexpr int32 MaximumPendingPanels = 4;
    static constexpr float ControlledStopDurationSeconds = 0.5f;

    float CycleElapsedSeconds = 0.0f;
    float StopElapsedSeconds = 0.0f;
    TArray<TWeakObjectPtr<AActor>> DestackPresentations;
    TArray<FTransform> DestackRestTransforms;
    TArray<TWeakObjectPtr<AActor>> TransferPresentations;
    TArray<FTransform> TransferRestTransforms;
    TArray<TWeakObjectPtr<AActor>> StageSlidePresentations[5];
    TArray<FTransform> StageSlideRestTransforms[5];
    TArray<TWeakObjectPtr<AActor>> StageUpperDiePresentations[5];
    TArray<FTransform> StageUpperDieRestTransforms[5];
    TArray<TWeakObjectPtr<AActor>> CarriedWorkpiecePresentations[5];
    TArray<FTransform> CarriedWorkpieceRestTransforms[5];
    TArray<TWeakObjectPtr<AActor>> UnloadRobotPresentations;
    TArray<FTransform> UnloadRobotRestTransforms;
    TArray<TWeakObjectPtr<AActor>> FormedPanelPresentations;
    TArray<FTransform> FormedPanelRestTransforms;
    /** Tagged modular guard visuals pivot about their authored hinge edge. */
    TArray<TWeakObjectPtr<AActor>> AccessGatePresentations;
    TArray<FTransform> AccessGateRestTransforms;
    /** Tagged flywheel/shaft visuals rotate independently of the fixed housing. */
    TArray<TWeakObjectPtr<AActor>> FlywheelPresentations;
    TArray<FTransform> FlywheelRestTransforms;
    TArray<TWeakObjectPtr<AActor>> RedBeaconPresentations;
    TArray<TWeakObjectPtr<AActor>> AmberBeaconPresentations;
    TArray<TWeakObjectPtr<AActor>> GreenBeaconPresentations;
    TWeakObjectPtr<ATextRenderActor> HMIStatePresentation;
    FName LastAudioCueId = NAME_None;
    int32 AudioCueSequence = 0;

    UPROPERTY() TObjectPtr<USoundBase> PressStrokeSound;
    UPROPERTY() TObjectPtr<USoundBase> ControlledStopSound;
    UPROPERTY() TObjectPtr<USoundBase> GateInterlockSound;
    UPROPERTY() TObjectPtr<USoundBase> EmergencyStopSound;

    void SetState(ELBPressTrainAState NewState);
    void RaiseFault(ELBPressTrainAFault Fault);
    void EvaluateRuntimePermissives();
    float GetCycleDurationSeconds() const;
    float GetCycleProgress() const;
    void UpdatePhaseFromProgress(float Progress);
    void BeginNextBlankIfAvailable();
    void CompleteCurrentPanel();
    void ApplyMachinePose();
    void BindMapPresentation();
    void UpdateHMITextPresentation();
    void UpdateTrainIdentityPresentation();
    void UpdateAudioForState(ELBPressTrainAState NewState, bool bPlayTransitionCues);
    void UpdateStatusBeacons();
    void SetLoopRequested(UAudioComponent* Component, bool bRequested, float TargetVolume);
    void PlayOneShot(UAudioComponent* Component, USoundBase* Sound, float Volume);
};
