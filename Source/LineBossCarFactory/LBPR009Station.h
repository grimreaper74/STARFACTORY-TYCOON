#pragma once

#include "CoreMinimal.h"
#include "GameFramework/Actor.h"
#include "LBPR009Station.generated.h"

class USceneComponent;

UENUM(BlueprintType)
enum class ELBPR009State : uint8
{
    Isolated,
    Ready,
    Receiving,
    Centering,
    Stacking,
    SeparatorPlacement,
    Releasing,
    Stopping,
    Fault
};

UENUM(BlueprintType)
enum class ELBPR009Fault : uint8
{
    None,
    EmergencyStopActive,
    GuardOpen,
    SafetyCircuitFault,
    UpstreamUnavailable,
    ReceiverBlocked,
    VisionReject,
    GantryFault,
    VacuumLoss,
    LiftTableFault,
    JoggerFault,
    SeparatorEmpty,
    SeparatorJam,
    StackHeightLimit,
    CarrierUnavailable,
    OutfeedBlocked
};

UENUM(BlueprintType)
enum class ELBPR009Command : uint8
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
struct FLBPR009HMIStatus
{
    GENERATED_BODY()

    UPROPERTY(BlueprintReadOnly) FName StationId = TEXT("PR-009");
    UPROPERTY(BlueprintReadOnly) ELBPR009State State = ELBPR009State::Isolated;
    UPROPERTY(BlueprintReadOnly) ELBPR009Fault ActiveFault = ELBPR009Fault::None;
    UPROPERTY(BlueprintReadOnly) int32 CurrentStackBlankCount = 0;
    UPROPERTY(BlueprintReadOnly) int32 TargetStackBlankCount = 0;
    UPROPERTY(BlueprintReadOnly) int32 TotalBlanksStacked = 0;
    UPROPERTY(BlueprintReadOnly) int32 SeparatorSheetsPlaced = 0;
    UPROPERTY(BlueprintReadOnly) int32 CarriersReleased = 0;
    UPROPERTY(BlueprintReadOnly) int32 RejectedBlanks = 0;
    UPROPERTY(BlueprintReadOnly) float StackHeightMm = 0.0f;
    UPROPERTY(BlueprintReadOnly) float PhaseProgress = 0.0f;
    UPROPERTY(BlueprintReadOnly) FName CurrentCarrierId;
    UPROPERTY(BlueprintReadOnly) FName CurrentBlankId;
    UPROPERTY(BlueprintReadOnly) FName PendingReleasedStackId;
    UPROPERTY(BlueprintReadOnly) int32 PendingReleasedBlankCount = 0;
    UPROPERTY(BlueprintReadOnly) bool bControlPowerOn = false;
    UPROPERTY(BlueprintReadOnly) bool bGuardsClosed = false;
    UPROPERTY(BlueprintReadOnly) bool bUpstreamBlankAvailable = false;
    UPROPERTY(BlueprintReadOnly) bool bReceiverClear = false;
    UPROPERTY(BlueprintReadOnly) bool bVisionHealthy = false;
    UPROPERTY(BlueprintReadOnly) bool bGantryHealthy = false;
    UPROPERTY(BlueprintReadOnly) bool bVacuumHealthy = false;
    UPROPERTY(BlueprintReadOnly) bool bLiftTableHealthy = false;
    UPROPERTY(BlueprintReadOnly) bool bJoggersHealthy = false;
    UPROPERTY(BlueprintReadOnly) bool bSeparatorAvailable = false;
    UPROPERTY(BlueprintReadOnly) bool bCarrierAvailable = false;
    UPROPERTY(BlueprintReadOnly) bool bOutfeedClear = false;
    UPROPERTY(BlueprintReadOnly) bool bSafetyCircuitHealthy = false;
    UPROPERTY(BlueprintReadOnly) bool bEmergencyStopActive = false;
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
struct FLBPR009SaveState
{
    GENERATED_BODY()

    UPROPERTY(EditAnywhere, BlueprintReadWrite, SaveGame) int32 Version = 2;
    UPROPERTY(EditAnywhere, BlueprintReadWrite, SaveGame) FName StationId = TEXT("PR-009");
    UPROPERTY(EditAnywhere, BlueprintReadWrite, SaveGame) ELBPR009State State = ELBPR009State::Isolated;
    UPROPERTY(EditAnywhere, BlueprintReadWrite, SaveGame) ELBPR009Fault ActiveFault = ELBPR009Fault::None;
    UPROPERTY(EditAnywhere, BlueprintReadWrite, SaveGame) int32 CurrentStackBlankCount = 0;
    UPROPERTY(EditAnywhere, BlueprintReadWrite, SaveGame) int32 TargetStackBlankCount = 40;
    UPROPERTY(EditAnywhere, BlueprintReadWrite, SaveGame) int32 SeparatorInterval = 10;
    UPROPERTY(EditAnywhere, BlueprintReadWrite, SaveGame) int32 TotalBlanksStacked = 0;
    UPROPERTY(EditAnywhere, BlueprintReadWrite, SaveGame) int32 SeparatorSheetsPlaced = 0;
    UPROPERTY(EditAnywhere, BlueprintReadWrite, SaveGame) int32 CarriersReleased = 0;
    UPROPERTY(EditAnywhere, BlueprintReadWrite, SaveGame) int32 RejectedBlanks = 0;
    UPROPERTY(EditAnywhere, BlueprintReadWrite, SaveGame) float NominalBlankThicknessMm = 1.2f;
    UPROPERTY(EditAnywhere, BlueprintReadWrite, SaveGame) FName CurrentCarrierId = TEXT("PR009-CARRIER-0001");
    UPROPERTY(EditAnywhere, BlueprintReadWrite, SaveGame) FName CurrentBlankId;
    UPROPERTY(EditAnywhere, BlueprintReadWrite, SaveGame) TArray<FName> CurrentStackBlankIds;
    UPROPERTY(EditAnywhere, BlueprintReadWrite, SaveGame) FName PendingReleasedStackId;
    UPROPERTY(EditAnywhere, BlueprintReadWrite, SaveGame) TArray<FName> PendingReleasedBlankIds;
    UPROPERTY(EditAnywhere, BlueprintReadWrite, SaveGame) FName PendingStackHandoffTransactionId;
    UPROPERTY(EditAnywhere, BlueprintReadWrite, SaveGame) bool bControlPowerOn = false;
    UPROPERTY(EditAnywhere, BlueprintReadWrite, SaveGame) bool bGuardsClosed = true;
    UPROPERTY(EditAnywhere, BlueprintReadWrite, SaveGame) bool bUpstreamBlankAvailable = false;
    UPROPERTY(EditAnywhere, BlueprintReadWrite, SaveGame) bool bReceiverClear = true;
    UPROPERTY(EditAnywhere, BlueprintReadWrite, SaveGame) bool bVisionHealthy = true;
    UPROPERTY(EditAnywhere, BlueprintReadWrite, SaveGame) bool bGantryHealthy = true;
    UPROPERTY(EditAnywhere, BlueprintReadWrite, SaveGame) bool bVacuumHealthy = true;
    UPROPERTY(EditAnywhere, BlueprintReadWrite, SaveGame) bool bLiftTableHealthy = true;
    UPROPERTY(EditAnywhere, BlueprintReadWrite, SaveGame) bool bJoggersHealthy = true;
    UPROPERTY(EditAnywhere, BlueprintReadWrite, SaveGame) bool bSeparatorAvailable = true;
    UPROPERTY(EditAnywhere, BlueprintReadWrite, SaveGame) bool bCarrierAvailable = true;
    UPROPERTY(EditAnywhere, BlueprintReadWrite, SaveGame) bool bOutfeedClear = true;
    UPROPERTY(EditAnywhere, BlueprintReadWrite, SaveGame) bool bSafetyCircuitHealthy = true;
    UPROPERTY(EditAnywhere, BlueprintReadWrite, SaveGame) bool bEmergencyStopActive = false;
    UPROPERTY(EditAnywhere, BlueprintReadWrite, SaveGame) bool bAlarmAcknowledged = false;
    UPROPERTY(EditAnywhere, BlueprintReadWrite, SaveGame) bool bIsolationRequested = false;
    UPROPERTY(EditAnywhere, BlueprintReadWrite, SaveGame) bool bZeroEnergyProved = false;
    UPROPERTY(EditAnywhere, BlueprintReadWrite, SaveGame) bool bRestartRequiredAfterLoad = false;
    UPROPERTY(EditAnywhere, BlueprintReadWrite, SaveGame) FName LastCommandSource;
    UPROPERTY(EditAnywhere, BlueprintReadWrite, SaveGame) FName LastSafetyEvidenceId;
};

DECLARE_DYNAMIC_MULTICAST_DELEGATE_TwoParams(FLBPR009StateChanged, ELBPR009State, PreviousState, ELBPR009State, NewState);
DECLARE_DYNAMIC_MULTICAST_DELEGATE_OneParam(FLBPR009FaultRaised, ELBPR009Fault, Fault);

/** Native remote authority for PR-009 receiving, centring, stacking and carrier release. */
UCLASS(BlueprintType)
class LINEBOSSCARFACTORY_API ALBPR009Station : public AActor
{
    GENERATED_BODY()

public:
    ALBPR009Station();
    virtual void BeginPlay() override;
    virtual void Tick(float DeltaSeconds) override;

    UFUNCTION(BlueprintCallable, Category="Cairnwell|PR-009") void ConfigureHealthyInputs(bool bBlankAvailable = true);
    UFUNCTION(BlueprintCallable, Category="Cairnwell|PR-009") void SetUpstreamBlankAvailable(bool bAvailable, FName BlankId = NAME_None);
    UFUNCTION(BlueprintPure, Category="Cairnwell|PR-009|Material Flow") bool CanAcceptUpstreamBlank(TArray<FText>& BlockingReasons) const;
    UFUNCTION(BlueprintCallable, Category="Cairnwell|PR-009|Material Flow") bool AcceptUpstreamBlank(FName BlankId);
    UFUNCTION(BlueprintPure, Category="Cairnwell|PR-009|Material Flow") bool CanReleaseCompletedStack(TArray<FText>& BlockingReasons) const;
    UFUNCTION(BlueprintCallable, Category="Cairnwell|PR-009|Material Flow") bool RequestStackHandoff(FName TransactionId, FName& StackId, TArray<FName>& BlankIds);
    UFUNCTION(BlueprintCallable, Category="Cairnwell|PR-009|Material Flow") bool ConfirmStackHandoff(FName TransactionId);
    UFUNCTION(BlueprintCallable, Category="Cairnwell|PR-009|Material Flow") bool CancelStackHandoff(FName TransactionId);
    UFUNCTION(BlueprintCallable, Category="Cairnwell|PR-009|Presentation")
    bool BindPresentationActor(FName SemanticObjectName, FName SemanticRole, FName IntendedBindingParent, AActor* VisualActor);
    UFUNCTION(BlueprintCallable, Category="Cairnwell|PR-009") void SetReceiverClear(bool bClear);
    UFUNCTION(BlueprintCallable, Category="Cairnwell|PR-009") void SetVisionHealthy(bool bHealthy);
    UFUNCTION(BlueprintCallable, Category="Cairnwell|PR-009") void SetGantryHealthy(bool bHealthy);
    UFUNCTION(BlueprintCallable, Category="Cairnwell|PR-009") void SetVacuumHealthy(bool bHealthy);
    UFUNCTION(BlueprintCallable, Category="Cairnwell|PR-009") void SetLiftTableHealthy(bool bHealthy);
    UFUNCTION(BlueprintCallable, Category="Cairnwell|PR-009") void SetJoggersHealthy(bool bHealthy);
    UFUNCTION(BlueprintCallable, Category="Cairnwell|PR-009") void SetSeparatorAvailable(bool bAvailable);
    UFUNCTION(BlueprintCallable, Category="Cairnwell|PR-009") void SetCarrierAvailable(bool bAvailable, FName CarrierId = NAME_None);
    UFUNCTION(BlueprintCallable, Category="Cairnwell|PR-009") void SetOutfeedClear(bool bClear);
    UFUNCTION(BlueprintCallable, Category="Cairnwell|PR-009|Safety") void SetGuardsClosed(bool bClosed);
    UFUNCTION(BlueprintCallable, Category="Cairnwell|PR-009|Safety") void SetSafetyCircuitHealthy(bool bHealthy);
    UFUNCTION(BlueprintCallable, Category="Cairnwell|PR-009|Safety") void SetEmergencyStopActive(bool bActive);
    UFUNCTION(BlueprintCallable, Category="Cairnwell|PR-009") void SetStackRecipe(int32 StackBlankCount, int32 InSeparatorInterval, float BlankThicknessMm);
    UFUNCTION(BlueprintCallable, Category="Cairnwell|PR-009|Remote") bool ExecuteRemoteCommand(ELBPR009Command Command, FName CommandSource, FName AuthorityId);
    UFUNCTION(BlueprintCallable, Category="Cairnwell|PR-009|Safety") bool AcknowledgeAlarm(FName CommandSource);
    UFUNCTION(BlueprintCallable, Category="Cairnwell|PR-009|Safety") bool ConfirmZeroEnergyIsolation(bool bZeroMotionVerified, bool bPneumaticEnergyReleased, FName EvidenceId);
    UFUNCTION(BlueprintPure, Category="Cairnwell|PR-009") bool CanStart(TArray<FText>& BlockingReasons) const;
    UFUNCTION(BlueprintPure, Category="Cairnwell|PR-009|HMI") FLBPR009HMIStatus GetHMIStatus() const;
    UFUNCTION(BlueprintPure, Category="Cairnwell|PR-009|Save") FLBPR009SaveState CaptureSaveState() const;
    UFUNCTION(BlueprintCallable, Category="Cairnwell|PR-009|Save") bool RestoreSaveState(const FLBPR009SaveState& SavedState);
    UFUNCTION(BlueprintPure, Category="Cairnwell|PR-009|Presentation") float GetServiceDoorAngleDegrees() const { return ServiceDoorAngleDegrees; }

    UPROPERTY(BlueprintAssignable, Category="Cairnwell|PR-009") FLBPR009StateChanged OnStateChanged;
    UPROPERTY(BlueprintAssignable, Category="Cairnwell|PR-009") FLBPR009FaultRaised OnFaultRaised;

protected:
    UPROPERTY(VisibleAnywhere, BlueprintReadOnly) TObjectPtr<USceneComponent> StationRoot;
    UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category="Cairnwell|PR-009|Presentation") TArray<TObjectPtr<USceneComponent>> InfeedRollMovers;
    UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category="Cairnwell|PR-009|Presentation") TObjectPtr<USceneComponent> GantryBridgeMover;
    UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category="Cairnwell|PR-009|Presentation") TObjectPtr<USceneComponent> GantryCrossSlideMover;
    UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category="Cairnwell|PR-009|Presentation") TObjectPtr<USceneComponent> GantryZMover;
    UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category="Cairnwell|PR-009|Presentation") TObjectPtr<USceneComponent> LiftTableMover;
    UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category="Cairnwell|PR-009|Presentation") TObjectPtr<USceneComponent> SideJoggerLeftMover;
    UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category="Cairnwell|PR-009|Presentation") TObjectPtr<USceneComponent> SideJoggerRightMover;
    UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category="Cairnwell|PR-009|Presentation") TObjectPtr<USceneComponent> EndJoggerMover;
    UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category="Cairnwell|PR-009|Presentation") TObjectPtr<USceneComponent> SeparatorPickerMover;
    UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category="Cairnwell|PR-009|Presentation") TArray<TObjectPtr<USceneComponent>> OutputRollMovers;
    UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category="Cairnwell|PR-009|Presentation") TObjectPtr<USceneComponent> ServiceDoorMover;
    UPROPERTY(EditAnywhere, BlueprintReadWrite, SaveGame, Category="Cairnwell|State") ELBPR009State State = ELBPR009State::Isolated;
    UPROPERTY(EditAnywhere, BlueprintReadWrite, SaveGame, Category="Cairnwell|State") ELBPR009Fault ActiveFault = ELBPR009Fault::None;
    UPROPERTY(EditAnywhere, BlueprintReadWrite, SaveGame, Category="Cairnwell|Production") int32 CurrentStackBlankCount = 0;
    UPROPERTY(EditAnywhere, BlueprintReadWrite, SaveGame, Category="Cairnwell|Recipe") int32 TargetStackBlankCount = 40;
    UPROPERTY(EditAnywhere, BlueprintReadWrite, SaveGame, Category="Cairnwell|Recipe") int32 SeparatorInterval = 10;
    UPROPERTY(EditAnywhere, BlueprintReadWrite, SaveGame, Category="Cairnwell|Production") int32 TotalBlanksStacked = 0;
    UPROPERTY(EditAnywhere, BlueprintReadWrite, SaveGame, Category="Cairnwell|Production") int32 SeparatorSheetsPlaced = 0;
    UPROPERTY(EditAnywhere, BlueprintReadWrite, SaveGame, Category="Cairnwell|Production") int32 CarriersReleased = 0;
    UPROPERTY(EditAnywhere, BlueprintReadWrite, SaveGame, Category="Cairnwell|Quality") int32 RejectedBlanks = 0;
    UPROPERTY(EditAnywhere, BlueprintReadWrite, SaveGame, Category="Cairnwell|Recipe") float NominalBlankThicknessMm = 1.2f;
    UPROPERTY(EditAnywhere, BlueprintReadWrite, SaveGame, Category="Cairnwell|Traceability") FName CurrentCarrierId = TEXT("PR009-CARRIER-0001");
    UPROPERTY(EditAnywhere, BlueprintReadWrite, SaveGame, Category="Cairnwell|Traceability") FName CurrentBlankId;
    UPROPERTY(EditAnywhere, BlueprintReadWrite, SaveGame, Category="Cairnwell|Traceability") TArray<FName> CurrentStackBlankIds;
    UPROPERTY(EditAnywhere, BlueprintReadWrite, SaveGame, Category="Cairnwell|Traceability") FName PendingReleasedStackId;
    UPROPERTY(EditAnywhere, BlueprintReadWrite, SaveGame, Category="Cairnwell|Traceability") TArray<FName> PendingReleasedBlankIds;
    UPROPERTY(EditAnywhere, BlueprintReadWrite, SaveGame, Category="Cairnwell|Traceability") FName PendingStackHandoffTransactionId;
    UPROPERTY(EditAnywhere, BlueprintReadWrite, SaveGame, Category="Cairnwell|State") bool bControlPowerOn = false;
    UPROPERTY(EditAnywhere, BlueprintReadWrite, SaveGame, Category="Cairnwell|State") bool bGuardsClosed = true;
    UPROPERTY(EditAnywhere, BlueprintReadWrite, SaveGame, Category="Cairnwell|State") bool bUpstreamBlankAvailable = false;
    UPROPERTY(EditAnywhere, BlueprintReadWrite, SaveGame, Category="Cairnwell|State") bool bReceiverClear = true;
    UPROPERTY(EditAnywhere, BlueprintReadWrite, SaveGame, Category="Cairnwell|State") bool bVisionHealthy = true;
    UPROPERTY(EditAnywhere, BlueprintReadWrite, SaveGame, Category="Cairnwell|State") bool bGantryHealthy = true;
    UPROPERTY(EditAnywhere, BlueprintReadWrite, SaveGame, Category="Cairnwell|State") bool bVacuumHealthy = true;
    UPROPERTY(EditAnywhere, BlueprintReadWrite, SaveGame, Category="Cairnwell|State") bool bLiftTableHealthy = true;
    UPROPERTY(EditAnywhere, BlueprintReadWrite, SaveGame, Category="Cairnwell|State") bool bJoggersHealthy = true;
    UPROPERTY(EditAnywhere, BlueprintReadWrite, SaveGame, Category="Cairnwell|State") bool bSeparatorAvailable = true;
    UPROPERTY(EditAnywhere, BlueprintReadWrite, SaveGame, Category="Cairnwell|State") bool bCarrierAvailable = true;
    UPROPERTY(EditAnywhere, BlueprintReadWrite, SaveGame, Category="Cairnwell|State") bool bOutfeedClear = true;
    UPROPERTY(EditAnywhere, BlueprintReadWrite, SaveGame, Category="Cairnwell|Safety") bool bSafetyCircuitHealthy = true;
    UPROPERTY(EditAnywhere, BlueprintReadWrite, SaveGame, Category="Cairnwell|Safety") bool bEmergencyStopActive = false;
    UPROPERTY(EditAnywhere, BlueprintReadWrite, SaveGame, Category="Cairnwell|Safety") bool bAlarmAcknowledged = false;
    UPROPERTY(EditAnywhere, BlueprintReadWrite, SaveGame, Category="Cairnwell|Safety") bool bIsolationRequested = false;
    UPROPERTY(EditAnywhere, BlueprintReadWrite, SaveGame, Category="Cairnwell|Safety") bool bZeroEnergyProved = false;
    UPROPERTY(EditAnywhere, BlueprintReadWrite, SaveGame, Category="Cairnwell|State") bool bRestartRequiredAfterLoad = false;
    UPROPERTY(EditAnywhere, BlueprintReadWrite, SaveGame, Category="Cairnwell|Authority") FName LastCommandSource;
    UPROPERTY(EditAnywhere, BlueprintReadWrite, SaveGame, Category="Cairnwell|Safety") FName LastSafetyEvidenceId;
    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="Cairnwell|Authority") FName RemoteAuthorityId = TEXT("CW.MW.CONTROL_ROOM");

private:
    float PhaseElapsedSeconds = 0.0f;
    bool bControlledStopRequested = false;
    bool bPresentationBasesCaptured = false;
    TArray<FTransform> InfeedRollBaseTransforms;
    TArray<FTransform> OutputRollBaseTransforms;
    FTransform GantryBridgeBaseTransform;
    FTransform GantryCrossSlideBaseTransform;
    FTransform GantryZBaseTransform;
    FTransform LiftTableBaseTransform;
    FTransform SideJoggerLeftBaseTransform;
    FTransform SideJoggerRightBaseTransform;
    FTransform EndJoggerBaseTransform;
    FTransform SeparatorPickerBaseTransform;
    FTransform ServiceDoorBaseTransform;
    float ServiceDoorAngleDegrees = 0.0f;

    void SetState(ELBPR009State NewState);
    void RaiseFault(ELBPR009Fault Fault);
    void EvaluatePermissives();
    bool ResetFault();
    bool RequestIsolation(FName CommandSource);
    bool ReleaseIsolation(FName CommandSource);
    bool StartCycle();
    void RequestControlledStop();
    float GetPhaseDuration() const;
    float GetPhaseProgress() const;
    bool IsMovingState() const;
    void CapturePresentationBases();
    void UpdatePresentation();
    static void ApplyPresentationOffset(USceneComponent* Component, const FTransform& BaseTransform,
        const FVector& TranslationOffset, const FRotator& RotationOffset);
    USceneComponent* ResolvePresentationBindingTarget(FName SemanticObjectName, FName SemanticRole,
        FName IntendedBindingParent) const;
};
