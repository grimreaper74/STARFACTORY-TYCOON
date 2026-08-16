#pragma once

#include "CoreMinimal.h"
#include "GameFramework/Actor.h"
#include "LBPR005Station.generated.h"

class USceneComponent;
class UTextRenderComponent;
class UWidgetComponent;
class UAudioComponent;
class USoundBase;
class AActor;

UENUM(BlueprintType)
enum class ELBStationState : uint8
{
    Unsurveyed,
    Isolated,
    SafeForAccess,
    UnderInspection,
    RepairRequired,
    ReadyForTest,
    ManualCommissioning,
    DryCycle,
    FirstOffValidation,
    CertifiedForProduction,
    Idle,
    Setup,
    Starting,
    Running,
    Blocked,
    Hold,
    Stopping,
    Fault,
    Maintenance
};

UENUM(BlueprintType)
enum class ELBPR005Fault : uint8
{
    None,
    IncorrectCoilRecipe,
    CoilNotCentred,
    MandrelExpansionFailure,
    KeeperPositionDisagreement,
    GateOrInterlockOpen,
    StripThreadingOrTensionFault
};

UENUM(BlueprintType)
enum class ELBPR005ControlMode : uint8
{
    Off,
    Manual,
    Jog,
    Automatic
};

USTRUCT(BlueprintType)
struct FLBPR005ConditionProfile
{
    GENERATED_BODY()

    UPROPERTY(EditAnywhere, BlueprintReadWrite, SaveGame)
    float Mechanical = 0.55f;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, SaveGame)
    float Electrical = 0.50f;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, SaveGame)
    float HydraulicPneumatic = 0.45f;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, SaveGame)
    float SafetyCompliance = 0.35f;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, SaveGame)
    float Calibration = 0.30f;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, SaveGame)
    float SoftwareRecipeIntegrity = 0.40f;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, SaveGame)
    float DocumentationCompleteness = 0.45f;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, SaveGame)
    float SparePartsAvailability = 0.35f;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, SaveGame)
    float OperatorFamiliarity = 0.20f;
};

USTRUCT(BlueprintType)
struct FLBPR005CommissioningChecklist
{
    GENERATED_BODY()

    UPROPERTY(EditAnywhere, BlueprintReadWrite, SaveGame)
    bool bUtilitiesAvailable = false;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, SaveGame)
    bool bCorrectCoilIdentified = false;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, SaveGame)
    bool bRecipeSelected = false;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, SaveGame)
    bool bCoilCarPositioned = false;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, SaveGame)
    bool bMandrelExpanded = false;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, SaveGame)
    bool bKeeperEngaged = false;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, SaveGame)
    bool bSnubberEngaged = false;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, SaveGame)
    bool bGuardsClosed = false;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, SaveGame)
    bool bSafetyCircuitReset = false;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, SaveGame)
    bool bStripPeeledAndThreaded = false;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, SaveGame)
    bool bDryCycleComplete = false;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, SaveGame)
    bool bFirstOffProduced = false;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, SaveGame)
    bool bQualityApproved = false;
};

/** Read-only projection consumed by the shared physical HMI and management UI. */
USTRUCT(BlueprintType)
struct FLBPR005HMIStatus
{
    GENERATED_BODY()

    UPROPERTY(BlueprintReadOnly) FName StationId = NAME_None;
    UPROPERTY(BlueprintReadOnly) ELBStationState MachineState = ELBStationState::Unsurveyed;
    UPROPERTY(BlueprintReadOnly) ELBPR005Fault ActiveFault = ELBPR005Fault::None;
    UPROPERTY(BlueprintReadOnly) ELBPR005ControlMode ControlMode = ELBPR005ControlMode::Off;
    UPROPERTY(BlueprintReadOnly) FString CoilId;
    UPROPERTY(BlueprintReadOnly) FName RecipeId = NAME_None;
    UPROPERTY(BlueprintReadOnly) float CoilWidthMillimetres = 0.0f;
    UPROPERTY(BlueprintReadOnly) float RequiredWidthMillimetres = 0.0f;
    UPROPERTY(BlueprintReadOnly) float TargetSpeedMetresPerMinute = 0.0f;
    UPROPERTY(BlueprintReadOnly) float PhaseProgress = 0.0f;
    UPROPERTY(BlueprintReadOnly) float StripLengthMetres = 0.0f;
    UPROPERTY(BlueprintReadOnly) int32 CycleCount = 0;
    UPROPERTY(BlueprintReadOnly) int32 ScrapCount = 0;
    UPROPERTY(BlueprintReadOnly) bool bControlPowerOn = false;
    UPROPERTY(BlueprintReadOnly) bool bUtilitiesAvailable = false;
    UPROPERTY(BlueprintReadOnly) bool bGuardsClosed = false;
    UPROPERTY(BlueprintReadOnly) bool bSafetyCircuitHealthy = false;
    UPROPERTY(BlueprintReadOnly) bool bCorrectCoilAndRecipe = false;
    UPROPERTY(BlueprintReadOnly) bool bDryCycleComplete = false;
    UPROPERTY(BlueprintReadOnly) bool bQualityApproved = false;
    UPROPERTY(BlueprintReadOnly) bool bCertifiedForProduction = false;
    UPROPERTY(BlueprintReadOnly) bool bCanAuthoriseDryCycle = false;
    UPROPERTY(BlueprintReadOnly) bool bCanStartAutomatic = false;
    UPROPERTY(BlueprintReadOnly) TArray<FText> BlockingReasons;
};

/** Versioned stable state stored by the Press Shop campaign SaveGame. */
USTRUCT(BlueprintType)
struct FLBPR005SaveState
{
    GENERATED_BODY()

    UPROPERTY(EditAnywhere, BlueprintReadWrite, SaveGame) int32 Version = 2;
    UPROPERTY(EditAnywhere, BlueprintReadWrite, SaveGame) FName StationId = TEXT("PR-005");
    UPROPERTY(EditAnywhere, BlueprintReadWrite, SaveGame) ELBStationState MachineState = ELBStationState::Unsurveyed;
    UPROPERTY(EditAnywhere, BlueprintReadWrite, SaveGame) ELBStationState StateBeforeFault = ELBStationState::ReadyForTest;
    UPROPERTY(EditAnywhere, BlueprintReadWrite, SaveGame) ELBPR005Fault ActiveFault = ELBPR005Fault::None;
    UPROPERTY(EditAnywhere, BlueprintReadWrite, SaveGame) ELBPR005ControlMode ControlMode = ELBPR005ControlMode::Off;
    UPROPERTY(EditAnywhere, BlueprintReadWrite, SaveGame) FLBPR005ConditionProfile Condition;
    UPROPERTY(EditAnywhere, BlueprintReadWrite, SaveGame) FLBPR005CommissioningChecklist Checklist;
    UPROPERTY(EditAnywhere, BlueprintReadWrite, SaveGame) FString CoilId;
    UPROPERTY(EditAnywhere, BlueprintReadWrite, SaveGame) FString HeatId;
    UPROPERTY(EditAnywhere, BlueprintReadWrite, SaveGame) FString SupplierLotId;
    UPROPERTY(EditAnywhere, BlueprintReadWrite, SaveGame) FString TraceabilityBarcode;
    UPROPERTY(EditAnywhere, BlueprintReadWrite, SaveGame) FName ActiveRecipeId = NAME_None;
    UPROPERTY(EditAnywhere, BlueprintReadWrite, SaveGame) float CoilWidthMillimetres = 0.0f;
    UPROPERTY(EditAnywhere, BlueprintReadWrite, SaveGame) float RequiredStripWidthMillimetres = 0.0f;
    UPROPERTY(EditAnywhere, BlueprintReadWrite, SaveGame) float StripTravelMetres = 0.0f;
    UPROPERTY(EditAnywhere, BlueprintReadWrite, SaveGame) int32 CycleCount = 0;
    UPROPERTY(EditAnywhere, BlueprintReadWrite, SaveGame) int32 ScrapCount = 0;
    UPROPERTY(EditAnywhere, BlueprintReadWrite, SaveGame) float RunningHours = 0.0f;
    UPROPERTY(EditAnywhere, BlueprintReadWrite, SaveGame) float TargetSpeedMetresPerMinute = 12.0f;
    UPROPERTY(EditAnywhere, BlueprintReadWrite, SaveGame) bool bControlPowerOn = false;
    UPROPERTY(EditAnywhere, BlueprintReadWrite, SaveGame) bool bCertifiedForProduction = false;
};

DECLARE_DYNAMIC_MULTICAST_DELEGATE_TwoParams(FLBStationStateChanged, ELBStationState, PreviousState, ELBStationState, NewState);
DECLARE_DYNAMIC_MULTICAST_DELEGATE_OneParam(FLBPR005FaultRaised, ELBPR005Fault, Fault);
DECLARE_DYNAMIC_MULTICAST_DELEGATE_TwoParams(FLBPR005ProductionUpdated, int32, CycleCount, float, StripLengthMetres);

UCLASS(BlueprintType)
class LINEBOSSCARFACTORY_API ALBPR005Station : public AActor
{
    GENERATED_BODY()

public:
    ALBPR005Station();
    virtual void BeginPlay() override;
    virtual void Tick(float DeltaSeconds) override;

    UFUNCTION(BlueprintCallable, Category = "Line Boss|PR-005")
    void SetControlPower(bool bEnabled);

    UFUNCTION(BlueprintCallable, Category = "Line Boss|PR-005|HMI")
    bool SetControlMode(ELBPR005ControlMode NewMode);

    /** Shared-cabinet green button. It never bypasses commissioning or run permissives. */
    UFUNCTION(BlueprintCallable, Category = "Line Boss|PR-005|HMI")
    bool PressCycleStart();

    UFUNCTION(BlueprintCallable, Category = "Line Boss|PR-005")
    void SetUtilitiesAvailable(bool bAvailable);

    UFUNCTION(BlueprintCallable, Category = "Line Boss|PR-005")
    bool LoadCoil(const FString& NewCoilId, float WidthMillimetres);

    UFUNCTION(BlueprintCallable, Category = "Line Boss|PR-005")
    bool LoadCoilWithTraceability(const FString& NewCoilId, const FString& NewHeatId,
        const FString& NewSupplierLotId, const FString& NewTraceabilityBarcode, float WidthMillimetres);

    UFUNCTION(BlueprintPure, Category = "Line Boss|PR-005")
    bool CanLoadCoil(const FString& NewCoilId, float WidthMillimetres, TArray<FText>& BlockingReasons) const;

    UFUNCTION(BlueprintCallable, Category = "Line Boss|PR-005")
    bool SelectRecipe(const FName NewRecipeId, float RequiredWidthMillimetres);

    UFUNCTION(BlueprintCallable, Category = "Line Boss|PR-005")
    void SetCoilCarPositioned(bool bPositioned);

    UFUNCTION(BlueprintCallable, Category = "Line Boss|PR-005")
    void SetMandrelExpanded(bool bExpanded);

    UFUNCTION(BlueprintCallable, Category = "Line Boss|PR-005")
    void SetKeeperAndSnubber(bool bKeeperIsEngaged, bool bSnubberIsEngaged);

    UFUNCTION(BlueprintCallable, Category = "Line Boss|PR-005")
    void SetGuardsClosed(bool bClosed);

    UFUNCTION(BlueprintCallable, Category = "Line Boss|PR-005")
    void SetSafetyCircuitHealthy(bool bHealthy);

    UFUNCTION(BlueprintCallable, Category = "Line Boss|PR-005")
    void SetStripThreaded(bool bThreaded);

    UFUNCTION(BlueprintCallable, Category = "Line Boss|PR-005")
    bool BeginCommissioning();

    UFUNCTION(BlueprintCallable, Category = "Line Boss|PR-005")
    bool BeginDryCycle();

    UFUNCTION(BlueprintCallable, Category = "Line Boss|PR-005")
    void RecordFirstOffProduced();

    UFUNCTION(BlueprintCallable, Category = "Line Boss|PR-005")
    bool ApproveFirstOff();

    UFUNCTION(BlueprintCallable, Category = "Line Boss|PR-005")
    bool StartAutomaticProduction();

    UFUNCTION(BlueprintCallable, Category = "Line Boss|PR-005")
    void RequestControlledStop();

    UFUNCTION(BlueprintCallable, Category = "Line Boss|PR-005")
    void RaiseFault(ELBPR005Fault Fault);

    UFUNCTION(BlueprintCallable, Category = "Line Boss|PR-005")
    bool ResetFault();

    UFUNCTION(BlueprintPure, Category = "Line Boss|PR-005")
    ELBStationState GetMachineState() const { return MachineState; }

    UFUNCTION(BlueprintPure, Category = "Line Boss|PR-005|Traceability")
    FString GetCurrentCoilId() const { return CoilId; }

    UFUNCTION(BlueprintPure, Category = "Line Boss|PR-005|Traceability")
    FString GetCurrentHeatId() const { return HeatId; }

    UFUNCTION(BlueprintPure, Category = "Line Boss|PR-005|Traceability")
    FString GetCurrentSupplierLotId() const { return SupplierLotId; }

    UFUNCTION(BlueprintPure, Category = "Line Boss|PR-005|Traceability")
    FString GetCurrentTraceabilityBarcode() const { return TraceabilityBarcode; }

    UFUNCTION(BlueprintPure, Category = "Line Boss|PR-005")
    float GetPhaseProgress() const;

    UFUNCTION(BlueprintPure, Category = "Line Boss|PR-005")
    bool CanBeginDryCycle(TArray<FText>& BlockingReasons) const;

    UFUNCTION(BlueprintPure, Category = "Line Boss|PR-005")
    bool CanStartAutomatic(TArray<FText>& BlockingReasons) const;

    UFUNCTION(BlueprintPure, Category = "Line Boss|PR-005")
    float GetStripVisualWidthScale() const;

    UFUNCTION(BlueprintPure, Category = "Line Boss|PR-005")
    float GetCoilVisualWidthScale() const;

    UFUNCTION(BlueprintPure, Category = "Line Boss|PR-005")
    float GetVisualMotionTravelMetres() const;

    UFUNCTION(BlueprintPure, Category = "Line Boss|PR-005|Visualisation")
    float GetCoilLoadingPresentationProgress() const { return CoilLoadingPresentationProgress; }

    UFUNCTION(BlueprintPure, Category = "Line Boss|PR-005|HMI")
    FLBPR005HMIStatus GetHMIStatus() const;

    UFUNCTION(BlueprintPure, Category = "Line Boss|PR-005|Save")
    FLBPR005SaveState CaptureSaveState() const;

    /** Deterministic requested-state query used by runtime audio validation. */
    UFUNCTION(BlueprintPure, Category = "Line Boss|PR-005|Audio")
    bool IsAudioLayerRequested(FName LayerId) const;

    UFUNCTION(BlueprintPure, Category = "Line Boss|PR-005|Audio")
    FName GetLastAudioCueId() const { return LastAudioCueId; }

    UFUNCTION(BlueprintPure, Category = "Line Boss|PR-005|Audio")
    int32 GetAudioCueSequence() const { return AudioCueSequence; }

    UFUNCTION(BlueprintCallable, Category = "Line Boss|PR-005|Save")
    bool RestoreSaveState(const FLBPR005SaveState& SavedState);

    UPROPERTY(BlueprintAssignable, Category = "Line Boss|PR-005")
    FLBStationStateChanged OnStateChanged;

    UPROPERTY(BlueprintAssignable, Category = "Line Boss|PR-005")
    FLBPR005FaultRaised OnFaultRaised;

    UPROPERTY(BlueprintAssignable, Category = "Line Boss|PR-005")
    FLBPR005ProductionUpdated OnProductionUpdated;

protected:
    UPROPERTY(VisibleAnywhere, BlueprintReadOnly)
    TObjectPtr<USceneComponent> StationRoot;

    UPROPERTY(VisibleAnywhere, BlueprintReadOnly)
    TObjectPtr<USceneComponent> CoilCarMover;

    UPROPERTY(VisibleAnywhere, BlueprintReadOnly)
    TObjectPtr<USceneComponent> MandrelMover;

    UPROPERTY(VisibleAnywhere, BlueprintReadOnly)
    TObjectPtr<USceneComponent> PayoffCoilMover;

    UPROPERTY(VisibleAnywhere, BlueprintReadOnly)
    TObjectPtr<USceneComponent> StripMover;

    UPROPERTY(VisibleAnywhere, BlueprintReadOnly)
    TObjectPtr<USceneComponent> CropClampMover;

    UPROPERTY(VisibleAnywhere, BlueprintReadOnly)
    TObjectPtr<USceneComponent> CropShearMover;

    UPROPERTY(VisibleAnywhere, BlueprintReadOnly)
    TObjectPtr<USceneComponent> CropPieceMover;

    /** Native interactive 4:3 touchscreen hosted on the authored PR-005 cabinet display. */
    UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category = "Line Boss|PR-005|HMI")
    TObjectPtr<UWidgetComponent> OperatorHMI;

    /** Deterministic live presentation used by command-line PIE and fixed-camera validation. */
    UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category = "Line Boss|PR-005|HMI")
    TObjectPtr<USceneComponent> HMITextRoot;

    UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category = "Line Boss|PR-005|HMI")
    TObjectPtr<UTextRenderComponent> HMIBrandText;

    UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category = "Line Boss|PR-005|HMI")
    TObjectPtr<UTextRenderComponent> HMIStationText;

    UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category = "Line Boss|PR-005|HMI")
    TObjectPtr<UTextRenderComponent> HMIStateText;

    UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category = "Line Boss|PR-005|HMI")
    TObjectPtr<UTextRenderComponent> HMICoilText;

    UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category = "Line Boss|PR-005|HMI")
    TObjectPtr<UTextRenderComponent> HMIRecipeText;

    UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category = "Line Boss|PR-005|HMI")
    TObjectPtr<UTextRenderComponent> HMIPermissiveText;

    UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category = "Line Boss|PR-005|HMI")
    TObjectPtr<UTextRenderComponent> HMIActionText;

    UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category = "Line Boss|PR-005|Audio")
    TObjectPtr<UAudioComponent> HPUAudio;

    UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category = "Line Boss|PR-005|Audio")
    TObjectPtr<UAudioComponent> CoilCarAudio;

    UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category = "Line Boss|PR-005|Audio")
    TObjectPtr<UAudioComponent> RollerDriveAudio;

    UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category = "Line Boss|PR-005|Audio")
    TObjectPtr<UAudioComponent> StripMotionAudio;

    UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category = "Line Boss|PR-005|Audio")
    TObjectPtr<UAudioComponent> WarningAlarmAudio;

    UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category = "Line Boss|PR-005|Audio")
    TObjectPtr<UAudioComponent> ActuatorCueAudio;

    UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category = "Line Boss|PR-005|Audio")
    TObjectPtr<UAudioComponent> SafetyCueAudio;

    UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category = "Line Boss|PR-005|Audio")
    TObjectPtr<UAudioComponent> TransportCueAudio;

    /** Map-bound payoff-coil visuals. Hidden while PR-005 owns no coil. */
    UPROPERTY(EditInstanceOnly, BlueprintReadOnly, Category = "Line Boss|Visualisation")
    TArray<TObjectPtr<AActor>> PayoffCoilPresentationActors;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, SaveGame, Category = "Line Boss|Identity")
    FName StationId = TEXT("PR-005");

    UPROPERTY(EditAnywhere, BlueprintReadWrite, SaveGame, Category = "Line Boss|State")
    ELBStationState MachineState = ELBStationState::Unsurveyed;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, SaveGame, Category = "Line Boss|State")
    ELBStationState StateBeforeFault = ELBStationState::ReadyForTest;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, SaveGame, Category = "Line Boss|State")
    ELBPR005Fault ActiveFault = ELBPR005Fault::None;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, SaveGame, Category = "Line Boss|State")
    ELBPR005ControlMode ControlMode = ELBPR005ControlMode::Off;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, SaveGame, Category = "Line Boss|Condition")
    FLBPR005ConditionProfile Condition;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, SaveGame, Category = "Line Boss|Commissioning")
    FLBPR005CommissioningChecklist Checklist;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, SaveGame, Category = "Line Boss|Production")
    FString CoilId;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, SaveGame, Category = "Line Boss|Traceability")
    FString HeatId;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, SaveGame, Category = "Line Boss|Traceability")
    FString SupplierLotId;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, SaveGame, Category = "Line Boss|Traceability")
    FString TraceabilityBarcode;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, SaveGame, Category = "Line Boss|Production")
    FName ActiveRecipeId = NAME_None;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, SaveGame, Category = "Line Boss|Production")
    float CoilWidthMillimetres = 0.0f;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, SaveGame, Category = "Line Boss|Production")
    float RequiredStripWidthMillimetres = 0.0f;

    /** Width represented by the imported ContinuousStrip source geometry. */
    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Line Boss|Visualisation", meta = (ClampMin = "1.0"))
    float AuthoredStripWidthMillimetres = 1500.0f;

    /** Width represented by the imported PayoffCoil source geometry. */
    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Line Boss|Visualisation", meta = (ClampMin = "1.0"))
    float AuthoredCoilWidthMillimetres = 1512.0f;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, SaveGame, Category = "Line Boss|Production")
    float StripTravelMetres = 0.0f;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, SaveGame, Category = "Line Boss|Production")
    int32 CycleCount = 0;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, SaveGame, Category = "Line Boss|Production")
    int32 ScrapCount = 0;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, SaveGame, Category = "Line Boss|Maintenance")
    float RunningHours = 0.0f;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, SaveGame, Category = "Line Boss|Production", meta = (ClampMin = "0.0"))
    float TargetSpeedMetresPerMinute = 12.0f;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, SaveGame, Category = "Line Boss|State")
    bool bControlPowerOn = false;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, SaveGame, Category = "Line Boss|State")
    bool bCertifiedForProduction = false;

private:
    static constexpr float DryCycleDuration = 8.0f;
    static constexpr float StartingDuration = 2.0f;
    static constexpr float StoppingDuration = 1.5f;
    static constexpr float StripSpeedMetresPerSecond = 0.75f;
    static constexpr float CyclePitchMetres = 1.8f;
    static constexpr float CoilWidthToleranceMillimetres = 1.0f;
    static constexpr float CoilLoadingPresentationDuration = 5.0f;

    float PhaseElapsedSeconds = 0.0f;
    float LastReportedCycleDistance = 0.0f;
    FVector ClampRest;
    FVector ShearRest;
    FVector CropPieceRest;
    FVector CoilCarRest;
    FVector PayoffCoilRest;
    FVector StripRest;
    FRotator MandrelRest;
    FVector StripRestScale = FVector::OneVector;
    FVector PayoffCoilRestScale = FVector::OneVector;
    float HMIRefreshAccumulator = 0.0f;
    float CoilLoadingPresentationElapsed = 0.0f;
    float CoilLoadingPresentationProgress = 1.0f;
    bool bCoilLoadingPresentationActive = false;
    FName LastAudioCueId = NAME_None;
    int32 AudioCueSequence = 0;

    UPROPERTY()
    TObjectPtr<USoundBase> CoilCarStartSound;

    UPROPERTY()
    TObjectPtr<USoundBase> CoilCarStopSound;

    UPROPERTY()
    TObjectPtr<USoundBase> MandrelExpandSound;

    UPROPERTY()
    TObjectPtr<USoundBase> KeeperArmEngageSound;

    UPROPERTY()
    TObjectPtr<USoundBase> GateInterlockSound;

    UPROPERTY()
    TObjectPtr<USoundBase> ControlledStopSound;

    UPROPERTY()
    TObjectPtr<USoundBase> EmergencyStopSound;

    void SetMachineState(ELBStationState NewState);
    void UpdateAudioForState(ELBStationState NewState, bool bPlayTransitionCues);
    void SetLoopRequested(UAudioComponent* Component, bool bRequested, float TargetVolume);
    void PlayOneShot(UAudioComponent* Component, USoundBase* Sound, float Volume);
    void ApplyMachinePose();
    void UpdateCoilPresentation();
    void UpdateHMITextPresentation();
    void StartCoilLoadingPresentation();
    bool CoilMatchesRecipe() const;
};
