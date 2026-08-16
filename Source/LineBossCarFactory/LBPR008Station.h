#pragma once

#include "CoreMinimal.h"
#include "GameFramework/Actor.h"
#include "LBPR008Station.generated.h"

class USceneComponent;
class ATextRenderActor;

UENUM(BlueprintType)
enum class ELBPR008State : uint8
{
    Isolated,
    Ready,
    Threading,
    Running,
    Stopping,
    Fault
};

UENUM(BlueprintType)
enum class ELBPR008Fault : uint8
{
    None,
    EmergencyStopActive,
    GuardOpen,
    StripUnavailable,
    StripLoopOutOfRange,
    EdgeTrackingLimit,
    FeedPositionError,
    IncorrectCutLength,
    FeedServoFault,
    PrePunchToolFault,
    PressShearOverload,
    PressHydraulicLow,
    SlugChuteFull,
    ScrapBinFull,
    BlankOutfeedBlocked
};

UENUM(BlueprintType)
enum class ELBPR008RuntimePhase : uint8
{
    StripWait,
    LoopControl,
    Feeding,
    PrePunch,
    Cutting,
    Discharging
};

UENUM(BlueprintType)
enum class ELBPR008Command : uint8
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
struct FLBPR008HMIStatus
{
    GENERATED_BODY()

    UPROPERTY(BlueprintReadOnly) FName StationId = TEXT("PR-008");
    UPROPERTY(BlueprintReadOnly) ELBPR008State State = ELBPR008State::Isolated;
    UPROPERTY(BlueprintReadOnly) ELBPR008Fault ActiveFault = ELBPR008Fault::None;
    UPROPERTY(BlueprintReadOnly) ELBPR008RuntimePhase RuntimePhase = ELBPR008RuntimePhase::StripWait;
    UPROPERTY(BlueprintReadOnly) float StripTravelMetres = 0.0f;
    UPROPERTY(BlueprintReadOnly) int32 BlanksProduced = 0;
    UPROPERTY(BlueprintReadOnly) int32 PendingBlankCount = 0;
    UPROPERTY(BlueprintReadOnly) FName OldestPendingBlankId;
    UPROPERTY(BlueprintReadOnly) float TargetBlankLengthMm = 0.0f;
    UPROPERTY(BlueprintReadOnly) float LineSpeedMetresPerMinute = 0.0f;
    UPROPERTY(BlueprintReadOnly) float HydraulicPressureBar = 0.0f;
    UPROPERTY(BlueprintReadOnly) float ScrapBinFillPercent = 0.0f;
    UPROPERTY(BlueprintReadOnly) float StripLoopPercent = 50.0f;
    UPROPERTY(BlueprintReadOnly) float EdgeTrackingDeviationMm = 0.0f;
    UPROPERTY(BlueprintReadOnly) float FeedPositionErrorMm = 0.0f;
    UPROPERTY(BlueprintReadOnly) float MeasuredCutLengthMm = 0.0f;
    UPROPERTY(BlueprintReadOnly) float PressShearLoadPercent = 0.0f;
    UPROPERTY(BlueprintReadOnly) float SlugChuteFillPercent = 0.0f;
    UPROPERTY(BlueprintReadOnly) float CycleProgress = 0.0f;
    UPROPERTY(BlueprintReadOnly) bool bControlPowerOn = false;
    UPROPERTY(BlueprintReadOnly) bool bGuardsClosed = false;
    UPROPERTY(BlueprintReadOnly) bool bStripAvailable = false;
    UPROPERTY(BlueprintReadOnly) bool bFeedServoHealthy = false;
    UPROPERTY(BlueprintReadOnly) bool bBlankOutfeedClear = false;
    UPROPERTY(BlueprintReadOnly) bool bPrePunchToolHealthy = false;
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
struct FLBPR008SaveState
{
    GENERATED_BODY()

    UPROPERTY(EditAnywhere, BlueprintReadWrite, SaveGame) int32 Version = 3;
    UPROPERTY(EditAnywhere, BlueprintReadWrite, SaveGame) FName StationId = TEXT("PR-008");
    UPROPERTY(EditAnywhere, BlueprintReadWrite, SaveGame) ELBPR008State State = ELBPR008State::Isolated;
    UPROPERTY(EditAnywhere, BlueprintReadWrite, SaveGame) ELBPR008Fault ActiveFault = ELBPR008Fault::None;
    UPROPERTY(EditAnywhere, BlueprintReadWrite, SaveGame) ELBPR008RuntimePhase RuntimePhase = ELBPR008RuntimePhase::StripWait;
    UPROPERTY(EditAnywhere, BlueprintReadWrite, SaveGame) float StripTravelMetres = 0.0f;
    UPROPERTY(EditAnywhere, BlueprintReadWrite, SaveGame) int32 BlanksProduced = 0;
    UPROPERTY(EditAnywhere, BlueprintReadWrite, SaveGame) int32 NextBlankSerial = 1;
    UPROPERTY(EditAnywhere, BlueprintReadWrite, SaveGame) TArray<FName> PendingBlankIds;
    UPROPERTY(EditAnywhere, BlueprintReadWrite, SaveGame) FName PendingHandoffTransactionId;
    UPROPERTY(EditAnywhere, BlueprintReadWrite, SaveGame) FName PendingHandoffBlankId;
    UPROPERTY(EditAnywhere, BlueprintReadWrite, SaveGame) float RunningHours = 0.0f;
    UPROPERTY(EditAnywhere, BlueprintReadWrite, SaveGame) float TargetBlankLengthMm = 1450.0f;
    UPROPERTY(EditAnywhere, BlueprintReadWrite, SaveGame) float TargetLineSpeedMetresPerMinute = 18.0f;
    UPROPERTY(EditAnywhere, BlueprintReadWrite, SaveGame) float HydraulicPressureBar = 210.0f;
    UPROPERTY(EditAnywhere, BlueprintReadWrite, SaveGame) float ScrapBinFillPercent = 0.0f;
    UPROPERTY(EditAnywhere, BlueprintReadWrite, SaveGame) float StripLoopPercent = 50.0f;
    UPROPERTY(EditAnywhere, BlueprintReadWrite, SaveGame) float EdgeTrackingDeviationMm = 0.0f;
    UPROPERTY(EditAnywhere, BlueprintReadWrite, SaveGame) float FeedPositionErrorMm = 0.0f;
    UPROPERTY(EditAnywhere, BlueprintReadWrite, SaveGame) float MeasuredCutLengthMm = 1450.0f;
    UPROPERTY(EditAnywhere, BlueprintReadWrite, SaveGame) float PressShearLoadPercent = 0.0f;
    UPROPERTY(EditAnywhere, BlueprintReadWrite, SaveGame) float SlugChuteFillPercent = 0.0f;
    UPROPERTY(EditAnywhere, BlueprintReadWrite, SaveGame) bool bControlPowerOn = false;
    UPROPERTY(EditAnywhere, BlueprintReadWrite, SaveGame) bool bGuardsClosed = true;
    UPROPERTY(EditAnywhere, BlueprintReadWrite, SaveGame) bool bStripAvailable = false;
    UPROPERTY(EditAnywhere, BlueprintReadWrite, SaveGame) bool bFeedServoHealthy = true;
    UPROPERTY(EditAnywhere, BlueprintReadWrite, SaveGame) bool bBlankOutfeedClear = true;
    UPROPERTY(EditAnywhere, BlueprintReadWrite, SaveGame) bool bPrePunchToolHealthy = true;
    UPROPERTY(EditAnywhere, BlueprintReadWrite, SaveGame) bool bSafetyCircuitHealthy = true;
    UPROPERTY(EditAnywhere, BlueprintReadWrite, SaveGame) bool bEmergencyStopActive = false;
    UPROPERTY(EditAnywhere, BlueprintReadWrite, SaveGame) bool bAlarmAcknowledged = false;
    UPROPERTY(EditAnywhere, BlueprintReadWrite, SaveGame) bool bIsolationRequested = false;
    UPROPERTY(EditAnywhere, BlueprintReadWrite, SaveGame) bool bZeroEnergyProved = false;
    UPROPERTY(EditAnywhere, BlueprintReadWrite, SaveGame) bool bRestartRequiredAfterLoad = false;
    UPROPERTY(EditAnywhere, BlueprintReadWrite, SaveGame) FName LastCommandSource;
    UPROPERTY(EditAnywhere, BlueprintReadWrite, SaveGame) FName LastSafetyEvidenceId;
};

DECLARE_DYNAMIC_MULTICAST_DELEGATE_TwoParams(FLBPR008StateChanged, ELBPR008State, PreviousState, ELBPR008State, NewState);
DECLARE_DYNAMIC_MULTICAST_DELEGATE_OneParam(FLBPR008FaultRaised, ELBPR008Fault, Fault);

/** Native process authority for PR-008 servo feed, pre-punch and blank cutting. */
UCLASS(BlueprintType)
class LINEBOSSCARFACTORY_API ALBPR008Station : public AActor
{
    GENERATED_BODY()

public:
    ALBPR008Station();
    virtual void BeginPlay() override;
    virtual void Tick(float DeltaSeconds) override;

    UFUNCTION(BlueprintCallable, Category="Cairnwell|PR-008") void SetControlPower(bool bEnabled);
    UFUNCTION(BlueprintCallable, Category="Cairnwell|PR-008") void SetGuardsClosed(bool bClosed);
    UFUNCTION(BlueprintCallable, Category="Cairnwell|PR-008") void SetStripAvailable(bool bAvailable);
    UFUNCTION(BlueprintCallable, Category="Cairnwell|PR-008") void SetFeedServoHealthy(bool bHealthy);
    UFUNCTION(BlueprintCallable, Category="Cairnwell|PR-008") void SetHydraulicPressure(float PressureBar);
    UFUNCTION(BlueprintCallable, Category="Cairnwell|PR-008") void SetScrapBinFill(float FillPercent);
    UFUNCTION(BlueprintCallable, Category="Cairnwell|PR-008") void SetBlankOutfeedClear(bool bClear);
    UFUNCTION(BlueprintCallable, Category="Cairnwell|PR-008") void SetStripLoopPercent(float LoopPercent);
    UFUNCTION(BlueprintCallable, Category="Cairnwell|PR-008") void SetEdgeTrackingDeviation(float DeviationMm);
    UFUNCTION(BlueprintCallable, Category="Cairnwell|PR-008") void SetFeedPositionError(float ErrorMm);
    UFUNCTION(BlueprintCallable, Category="Cairnwell|PR-008") void SetMeasuredCutLength(float LengthMm);
    UFUNCTION(BlueprintCallable, Category="Cairnwell|PR-008") void SetPrePunchToolHealthy(bool bHealthy);
    UFUNCTION(BlueprintCallable, Category="Cairnwell|PR-008") void SetPressShearLoad(float LoadPercent);
    UFUNCTION(BlueprintCallable, Category="Cairnwell|PR-008") void SetSlugChuteFill(float FillPercent);
    UFUNCTION(BlueprintCallable, Category="Cairnwell|PR-008|Safety") void SetSafetyCircuitHealthy(bool bHealthy);
    UFUNCTION(BlueprintCallable, Category="Cairnwell|PR-008|Safety") void SetEmergencyStopActive(bool bActive);
    UFUNCTION(BlueprintCallable, Category="Cairnwell|PR-008|Safety") bool AcknowledgeAlarm(FName CommandSource);
    UFUNCTION(BlueprintCallable, Category="Cairnwell|PR-008|Safety") bool RequestIsolation(FName CommandSource);
    UFUNCTION(BlueprintCallable, Category="Cairnwell|PR-008|Safety") bool ConfirmZeroEnergyIsolation(bool bZeroMotionVerified, bool bHydraulicPressureReleased, FName EvidenceId);
    UFUNCTION(BlueprintCallable, Category="Cairnwell|PR-008|Safety") bool ReleaseIsolation(FName CommandSource, bool bGuardZoneClear);
    UFUNCTION(BlueprintCallable, Category="Cairnwell|PR-008|Remote") bool ExecuteRemoteCommand(ELBPR008Command Command, FName CommandSource, FName AuthorityId);
    UFUNCTION(BlueprintCallable, Category="Cairnwell|PR-008") void SetBlankRecipe(float BlankLengthMm, float LineSpeedMetresPerMinute);
    UFUNCTION(BlueprintCallable, Category="Cairnwell|PR-008") bool StartLine();
    UFUNCTION(BlueprintCallable, Category="Cairnwell|PR-008") void RequestControlledStop();
    UFUNCTION(BlueprintCallable, Category="Cairnwell|PR-008") bool ResetFault();
    UFUNCTION(BlueprintPure, Category="Cairnwell|PR-008|Material Flow") bool CanReleaseBlank(TArray<FText>& BlockingReasons) const;
    UFUNCTION(BlueprintCallable, Category="Cairnwell|PR-008|Material Flow") bool RequestBlankHandoff(FName TransactionId, FName& BlankId);
    UFUNCTION(BlueprintCallable, Category="Cairnwell|PR-008|Material Flow") bool ConfirmBlankHandoff(FName TransactionId);
    UFUNCTION(BlueprintCallable, Category="Cairnwell|PR-008|Material Flow") void CancelBlankHandoff(FName TransactionId);
    UFUNCTION(BlueprintPure, Category="Cairnwell|PR-008|Material Flow") int32 GetPendingBlankCount() const { return PendingBlankIds.Num(); }
    UFUNCTION(BlueprintPure, Category="Cairnwell|PR-008|Material Flow") FName GetOldestPendingBlankId() const { return PendingBlankIds.IsEmpty() ? NAME_None : PendingBlankIds[0]; }
    UFUNCTION(BlueprintPure, Category="Cairnwell|PR-008") bool CanStart(TArray<FText>& BlockingReasons) const;
    UFUNCTION(BlueprintPure, Category="Cairnwell|PR-008|HMI") FLBPR008HMIStatus GetHMIStatus() const;
    UFUNCTION(BlueprintPure, Category="Cairnwell|PR-008|Save") FLBPR008SaveState CaptureSaveState() const;
    UFUNCTION(BlueprintCallable, Category="Cairnwell|PR-008|Save") bool RestoreSaveState(const FLBPR008SaveState& SavedState);

    UPROPERTY(BlueprintAssignable, Category="Cairnwell|PR-008") FLBPR008StateChanged OnStateChanged;
    UPROPERTY(BlueprintAssignable, Category="Cairnwell|PR-008") FLBPR008FaultRaised OnFaultRaised;

protected:
    UPROPERTY(VisibleAnywhere, BlueprintReadOnly) TObjectPtr<USceneComponent> StationRoot;
    UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category="Cairnwell|PR-008|Motion") TObjectPtr<USceneComponent> FeedRollLowerMover;
    UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category="Cairnwell|PR-008|Motion") TObjectPtr<USceneComponent> FeedRollUpperMover;
    UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category="Cairnwell|PR-008|Motion") TObjectPtr<USceneComponent> LoopRollMover;
    UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category="Cairnwell|PR-008|Motion") TObjectPtr<USceneComponent> EdgeGuideOperatorMover;
    UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category="Cairnwell|PR-008|Motion") TObjectPtr<USceneComponent> EdgeGuideDriveMover;
    UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category="Cairnwell|PR-008|Motion") TObjectPtr<USceneComponent> TelescopeStage1Mover;
    UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category="Cairnwell|PR-008|Motion") TObjectPtr<USceneComponent> TelescopeStage2Mover;
    UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category="Cairnwell|PR-008|Motion") TObjectPtr<USceneComponent> TelescopeStage3Mover;
    UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category="Cairnwell|PR-008|Motion") TObjectPtr<USceneComponent> PrePunchMover;
    UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category="Cairnwell|PR-008|Motion") TObjectPtr<USceneComponent> ScrapFlapMover;
    UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category="Cairnwell|PR-008|Motion") TObjectPtr<USceneComponent> ServiceDoorOperatorMover;
    UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category="Cairnwell|PR-008|Motion") TObjectPtr<USceneComponent> ServiceDoorDriveMover;
    UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category="Cairnwell|PR-008|Motion") TObjectPtr<USceneComponent> GuillotineMover;
    UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category="Cairnwell|PR-008|Motion") TObjectPtr<USceneComponent> OutfeedRollMover;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, SaveGame, Category="Cairnwell|Identity") FName StationId = TEXT("PR-008");
    UPROPERTY(EditAnywhere, BlueprintReadWrite, SaveGame, Category="Cairnwell|State") ELBPR008State State = ELBPR008State::Isolated;
    UPROPERTY(EditAnywhere, BlueprintReadWrite, SaveGame, Category="Cairnwell|State") ELBPR008Fault ActiveFault = ELBPR008Fault::None;
    UPROPERTY(EditAnywhere, BlueprintReadWrite, SaveGame, Category="Cairnwell|State") ELBPR008RuntimePhase RuntimePhase = ELBPR008RuntimePhase::StripWait;
    UPROPERTY(EditAnywhere, BlueprintReadWrite, SaveGame, Category="Cairnwell|Production") float StripTravelMetres = 0.0f;
    UPROPERTY(EditAnywhere, BlueprintReadWrite, SaveGame, Category="Cairnwell|Production") int32 BlanksProduced = 0;
    UPROPERTY(EditAnywhere, BlueprintReadWrite, SaveGame, Category="Cairnwell|Production") int32 NextBlankSerial = 1;
    UPROPERTY(EditAnywhere, BlueprintReadWrite, SaveGame, Category="Cairnwell|Production") TArray<FName> PendingBlankIds;
    UPROPERTY(EditAnywhere, BlueprintReadWrite, SaveGame, Category="Cairnwell|Production") FName PendingHandoffTransactionId;
    UPROPERTY(EditAnywhere, BlueprintReadWrite, SaveGame, Category="Cairnwell|Production") FName PendingHandoffBlankId;
    UPROPERTY(EditAnywhere, BlueprintReadWrite, SaveGame, Category="Cairnwell|Maintenance") float RunningHours = 0.0f;
    UPROPERTY(EditAnywhere, BlueprintReadWrite, SaveGame, Category="Cairnwell|Recipe", meta=(ClampMin="500.0", ClampMax="4000.0")) float TargetBlankLengthMm = 1450.0f;
    UPROPERTY(EditAnywhere, BlueprintReadWrite, SaveGame, Category="Cairnwell|Recipe", meta=(ClampMin="0.0")) float TargetLineSpeedMetresPerMinute = 18.0f;
    UPROPERTY(EditAnywhere, BlueprintReadWrite, SaveGame, Category="Cairnwell|Process") float HydraulicPressureBar = 210.0f;
    UPROPERTY(EditAnywhere, BlueprintReadWrite, SaveGame, Category="Cairnwell|Process") float ScrapBinFillPercent = 0.0f;
    UPROPERTY(EditAnywhere, BlueprintReadWrite, SaveGame, Category="Cairnwell|Process") float StripLoopPercent = 50.0f;
    UPROPERTY(EditAnywhere, BlueprintReadWrite, SaveGame, Category="Cairnwell|Process") float EdgeTrackingDeviationMm = 0.0f;
    UPROPERTY(EditAnywhere, BlueprintReadWrite, SaveGame, Category="Cairnwell|Process") float FeedPositionErrorMm = 0.0f;
    UPROPERTY(EditAnywhere, BlueprintReadWrite, SaveGame, Category="Cairnwell|Process") float MeasuredCutLengthMm = 1450.0f;
    UPROPERTY(EditAnywhere, BlueprintReadWrite, SaveGame, Category="Cairnwell|Process") float PressShearLoadPercent = 0.0f;
    UPROPERTY(EditAnywhere, BlueprintReadWrite, SaveGame, Category="Cairnwell|Process") float SlugChuteFillPercent = 0.0f;
    UPROPERTY(EditAnywhere, BlueprintReadWrite, SaveGame, Category="Cairnwell|State") bool bControlPowerOn = false;
    UPROPERTY(EditAnywhere, BlueprintReadWrite, SaveGame, Category="Cairnwell|State") bool bGuardsClosed = true;
    UPROPERTY(EditAnywhere, BlueprintReadWrite, SaveGame, Category="Cairnwell|State") bool bStripAvailable = false;
    UPROPERTY(EditAnywhere, BlueprintReadWrite, SaveGame, Category="Cairnwell|State") bool bFeedServoHealthy = true;
    UPROPERTY(EditAnywhere, BlueprintReadWrite, SaveGame, Category="Cairnwell|State") bool bBlankOutfeedClear = true;
    UPROPERTY(EditAnywhere, BlueprintReadWrite, SaveGame, Category="Cairnwell|State") bool bPrePunchToolHealthy = true;
    UPROPERTY(EditAnywhere, BlueprintReadWrite, SaveGame, Category="Cairnwell|Safety") bool bSafetyCircuitHealthy = true;
    UPROPERTY(EditAnywhere, BlueprintReadWrite, SaveGame, Category="Cairnwell|Safety") bool bEmergencyStopActive = false;
    UPROPERTY(EditAnywhere, BlueprintReadWrite, SaveGame, Category="Cairnwell|Safety") bool bAlarmAcknowledged = false;
    UPROPERTY(EditAnywhere, BlueprintReadWrite, SaveGame, Category="Cairnwell|Safety") bool bIsolationRequested = false;
    UPROPERTY(EditAnywhere, BlueprintReadWrite, SaveGame, Category="Cairnwell|Safety") bool bZeroEnergyProved = false;
    UPROPERTY(EditAnywhere, BlueprintReadWrite, SaveGame, Category="Cairnwell|State") bool bRestartRequiredAfterLoad = false;
    UPROPERTY(EditAnywhere, BlueprintReadWrite, SaveGame, Category="Cairnwell|Authority") FName LastCommandSource;
    UPROPERTY(EditAnywhere, BlueprintReadWrite, SaveGame, Category="Cairnwell|Safety") FName LastSafetyEvidenceId;
    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="Cairnwell|Authority") FName RemoteAuthorityId = TEXT("CW.MW.CONTROL_ROOM");
    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="Cairnwell|Authority") bool bRemoteControlEnabled = true;

private:
    static constexpr float MinimumHydraulicPressureBar = 160.0f;
    static constexpr float MaximumScrapBinFillPercent = 95.0f;
    static constexpr float MinimumStripLoopPercent = 10.0f;
    static constexpr float MaximumStripLoopPercent = 90.0f;
    static constexpr float MaximumEdgeTrackingDeviationMm = 150.0f;
    static constexpr float MaximumFeedPositionErrorMm = 2.0f;
    static constexpr float MaximumCutLengthErrorMm = 2.0f;
    static constexpr float MaximumPressShearLoadPercent = 100.0f;
    static constexpr float MaximumSlugChuteFillPercent = 95.0f;
    static constexpr float ThreadingDurationSeconds = 1.5f;
    static constexpr float StoppingDurationSeconds = 1.0f;
    static constexpr float CutAllowanceMetres = 0.10f;
    static constexpr int32 MaximumPendingBlanks = 3;

    float PhaseElapsedSeconds = 0.0f;
    float CycleTravelMetres = 0.0f;
    float MotionAngleDegrees = 0.0f;
    FVector EdgeGuideOperatorRestLocation = FVector::ZeroVector;
    FVector EdgeGuideDriveRestLocation = FVector::ZeroVector;
    FVector TelescopeStage1RestLocation = FVector::ZeroVector;
    FVector TelescopeStage2RestLocation = FVector::ZeroVector;
    FVector TelescopeStage3RestLocation = FVector::ZeroVector;
    FVector PrePunchRestLocation = FVector::ZeroVector;
    FVector GuillotineRestLocation = FVector::ZeroVector;
    FRotator FeedRollLowerRestRotation = FRotator::ZeroRotator;
    FRotator FeedRollUpperRestRotation = FRotator::ZeroRotator;
    FRotator LoopRollRestRotation = FRotator::ZeroRotator;
    FRotator OutfeedRollRestRotation = FRotator::ZeroRotator;
    FRotator ScrapFlapRestRotation = FRotator::ZeroRotator;
    FRotator ServiceDoorOperatorRestRotation = FRotator::ZeroRotator;
    FRotator ServiceDoorDriveRestRotation = FRotator::ZeroRotator;
    TArray<TWeakObjectPtr<AActor>> LoopRollPresentations;
    TArray<FRotator> LoopRollPresentationRestRotations;
    TArray<TWeakObjectPtr<AActor>> DischargeRollPresentations;
    TArray<FRotator> DischargeRollPresentationRestRotations;
    TWeakObjectPtr<ATextRenderActor> HMIStatePresentation;

    void SetState(ELBPR008State NewState);
    void RaiseFault(ELBPR008Fault Fault);
    void EvaluateRuntimePermissives();
    float GetBlankPitchMetres() const;
    float GetCycleProgress() const;
    void ApplyMachinePose();
    void BindMapPresentation();
    void UpdateHMITextPresentation();
};
