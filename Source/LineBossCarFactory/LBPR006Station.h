#pragma once

#include "CoreMinimal.h"
#include "GameFramework/Actor.h"
#include "LBPR006Station.generated.h"

class USceneComponent;
class ATextRenderActor;

UENUM(BlueprintType)
enum class ELBPR006State : uint8
{
    Isolated,
    Ready,
    Calibrating,
    Running,
    Stopping,
    Fault
};

UENUM(BlueprintType)
enum class ELBPR006Fault : uint8
{
    None,
    GuardOpen,
    StripUnavailable,
    CassetteUnlocked,
    DriveFault,
    RollGapOutOfTolerance,
    MotorOverload
};

USTRUCT(BlueprintType)
struct FLBPR006HMIStatus
{
    GENERATED_BODY()

    UPROPERTY(BlueprintReadOnly) FName StationId = TEXT("PR-006");
    UPROPERTY(BlueprintReadOnly) ELBPR006State State = ELBPR006State::Isolated;
    UPROPERTY(BlueprintReadOnly) ELBPR006Fault ActiveFault = ELBPR006Fault::None;
    UPROPERTY(BlueprintReadOnly) FName CassetteId = TEXT("L-1500-A");
    UPROPERTY(BlueprintReadOnly) float TargetStripThicknessMm = 0.0f;
    UPROPERTY(BlueprintReadOnly) float TargetRollGapMm = 0.0f;
    UPROPERTY(BlueprintReadOnly) float ActualRollGapMm = 0.0f;
    UPROPERTY(BlueprintReadOnly) float StripTravelMetres = 0.0f;
    UPROPERTY(BlueprintReadOnly) float LineSpeedMetresPerMinute = 0.0f;
    UPROPERTY(BlueprintReadOnly) float MotorLoadPercent = 0.0f;
    UPROPERTY(BlueprintReadOnly) float CalibrationProgress = 0.0f;
    UPROPERTY(BlueprintReadOnly) bool bControlPowerOn = false;
    UPROPERTY(BlueprintReadOnly) bool bGuardsClosed = false;
    UPROPERTY(BlueprintReadOnly) bool bStripAvailable = false;
    UPROPERTY(BlueprintReadOnly) bool bCassetteLocked = false;
    UPROPERTY(BlueprintReadOnly) bool bDrivesHealthy = false;
    UPROPERTY(BlueprintReadOnly) bool bCanStart = false;
    UPROPERTY(BlueprintReadOnly) TArray<FText> BlockingReasons;
};

USTRUCT(BlueprintType)
struct FLBPR006SaveState
{
    GENERATED_BODY()

    UPROPERTY(EditAnywhere, BlueprintReadWrite, SaveGame) int32 Version = 1;
    UPROPERTY(EditAnywhere, BlueprintReadWrite, SaveGame) FName StationId = TEXT("PR-006");
    UPROPERTY(EditAnywhere, BlueprintReadWrite, SaveGame) ELBPR006State State = ELBPR006State::Isolated;
    UPROPERTY(EditAnywhere, BlueprintReadWrite, SaveGame) ELBPR006Fault ActiveFault = ELBPR006Fault::None;
    UPROPERTY(EditAnywhere, BlueprintReadWrite, SaveGame) FName CassetteId = TEXT("L-1500-A");
    UPROPERTY(EditAnywhere, BlueprintReadWrite, SaveGame) float TargetStripThicknessMm = 1.20f;
    UPROPERTY(EditAnywhere, BlueprintReadWrite, SaveGame) float TargetRollGapMm = 1.15f;
    UPROPERTY(EditAnywhere, BlueprintReadWrite, SaveGame) float ActualRollGapMm = 1.80f;
    UPROPERTY(EditAnywhere, BlueprintReadWrite, SaveGame) float StripTravelMetres = 0.0f;
    UPROPERTY(EditAnywhere, BlueprintReadWrite, SaveGame) float RunningHours = 0.0f;
    UPROPERTY(EditAnywhere, BlueprintReadWrite, SaveGame) float TargetLineSpeedMetresPerMinute = 16.0f;
    UPROPERTY(EditAnywhere, BlueprintReadWrite, SaveGame) float MotorLoadPercent = 0.0f;
    UPROPERTY(EditAnywhere, BlueprintReadWrite, SaveGame) bool bControlPowerOn = false;
    UPROPERTY(EditAnywhere, BlueprintReadWrite, SaveGame) bool bGuardsClosed = true;
    UPROPERTY(EditAnywhere, BlueprintReadWrite, SaveGame) bool bStripAvailable = false;
    UPROPERTY(EditAnywhere, BlueprintReadWrite, SaveGame) bool bCassetteLocked = true;
    UPROPERTY(EditAnywhere, BlueprintReadWrite, SaveGame) bool bDrivesHealthy = true;
};

DECLARE_DYNAMIC_MULTICAST_DELEGATE_TwoParams(FLBPR006StateChanged, ELBPR006State, PreviousState, ELBPR006State, NewState);
DECLARE_DYNAMIC_MULTICAST_DELEGATE_OneParam(FLBPR006FaultRaised, ELBPR006Fault, Fault);

/** Native cassette, roll-gap and drive authority for the PR-006 precision leveller. */
UCLASS(BlueprintType)
class LINEBOSSCARFACTORY_API ALBPR006Station : public AActor
{
    GENERATED_BODY()

public:
    ALBPR006Station();
    virtual void BeginPlay() override;
    virtual void Tick(float DeltaSeconds) override;

    UFUNCTION(BlueprintCallable, Category="Cairnwell|PR-006") void SetControlPower(bool bEnabled);
    UFUNCTION(BlueprintCallable, Category="Cairnwell|PR-006") void SetGuardsClosed(bool bClosed);
    UFUNCTION(BlueprintCallable, Category="Cairnwell|PR-006") void SetStripAvailable(bool bAvailable);
    UFUNCTION(BlueprintCallable, Category="Cairnwell|PR-006") void SetCassetteLocked(bool bLocked);
    UFUNCTION(BlueprintCallable, Category="Cairnwell|PR-006") void SetDrivesHealthy(bool bHealthy);
    UFUNCTION(BlueprintCallable, Category="Cairnwell|PR-006") void SetActualRollGap(float GapMm);
    UFUNCTION(BlueprintCallable, Category="Cairnwell|PR-006") void SetMotorLoad(float LoadPercent);
    UFUNCTION(BlueprintCallable, Category="Cairnwell|PR-006") void SetLevellerRecipe(FName NewCassetteId, float StripThicknessMm, float RollGapMm, float LineSpeedMetresPerMinute);
    UFUNCTION(BlueprintCallable, Category="Cairnwell|PR-006") bool StartLine();
    UFUNCTION(BlueprintCallable, Category="Cairnwell|PR-006") void RequestControlledStop();
    UFUNCTION(BlueprintCallable, Category="Cairnwell|PR-006") bool ResetFault();
    UFUNCTION(BlueprintPure, Category="Cairnwell|PR-006") bool CanStart(TArray<FText>& BlockingReasons) const;
    UFUNCTION(BlueprintPure, Category="Cairnwell|PR-006|HMI") FLBPR006HMIStatus GetHMIStatus() const;
    UFUNCTION(BlueprintPure, Category="Cairnwell|PR-006|Save") FLBPR006SaveState CaptureSaveState() const;
    UFUNCTION(BlueprintCallable, Category="Cairnwell|PR-006|Save") bool RestoreSaveState(const FLBPR006SaveState& SavedState);

    UPROPERTY(BlueprintAssignable, Category="Cairnwell|PR-006") FLBPR006StateChanged OnStateChanged;
    UPROPERTY(BlueprintAssignable, Category="Cairnwell|PR-006") FLBPR006FaultRaised OnFaultRaised;

protected:
    UPROPERTY(VisibleAnywhere, BlueprintReadOnly) TObjectPtr<USceneComponent> StationRoot;
    UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category="Cairnwell|PR-006|Motion") TArray<TObjectPtr<USceneComponent>> LowerRollMovers;
    UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category="Cairnwell|PR-006|Motion") TArray<TObjectPtr<USceneComponent>> UpperRollMovers;
    UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category="Cairnwell|PR-006|Motion") TObjectPtr<USceneComponent> UpperCassetteMover;
    UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category="Cairnwell|PR-006|Motion") TArray<TObjectPtr<USceneComponent>> GapCylinderMovers;
    UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category="Cairnwell|PR-006|Motion") TArray<TObjectPtr<USceneComponent>> DriveMotorMovers;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, SaveGame, Category="Cairnwell|Identity") FName StationId = TEXT("PR-006");
    UPROPERTY(EditAnywhere, BlueprintReadWrite, SaveGame, Category="Cairnwell|Identity") FName CassetteId = TEXT("L-1500-A");
    UPROPERTY(EditAnywhere, BlueprintReadWrite, SaveGame, Category="Cairnwell|State") ELBPR006State State = ELBPR006State::Isolated;
    UPROPERTY(EditAnywhere, BlueprintReadWrite, SaveGame, Category="Cairnwell|State") ELBPR006Fault ActiveFault = ELBPR006Fault::None;
    UPROPERTY(EditAnywhere, BlueprintReadWrite, SaveGame, Category="Cairnwell|Recipe") float TargetStripThicknessMm = 1.20f;
    UPROPERTY(EditAnywhere, BlueprintReadWrite, SaveGame, Category="Cairnwell|Recipe") float TargetRollGapMm = 1.15f;
    UPROPERTY(EditAnywhere, BlueprintReadWrite, SaveGame, Category="Cairnwell|Process") float ActualRollGapMm = 1.80f;
    UPROPERTY(EditAnywhere, BlueprintReadWrite, SaveGame, Category="Cairnwell|Production") float StripTravelMetres = 0.0f;
    UPROPERTY(EditAnywhere, BlueprintReadWrite, SaveGame, Category="Cairnwell|Maintenance") float RunningHours = 0.0f;
    UPROPERTY(EditAnywhere, BlueprintReadWrite, SaveGame, Category="Cairnwell|Recipe") float TargetLineSpeedMetresPerMinute = 16.0f;
    UPROPERTY(EditAnywhere, BlueprintReadWrite, SaveGame, Category="Cairnwell|Process") float MotorLoadPercent = 0.0f;
    UPROPERTY(EditAnywhere, BlueprintReadWrite, SaveGame, Category="Cairnwell|State") bool bControlPowerOn = false;
    UPROPERTY(EditAnywhere, BlueprintReadWrite, SaveGame, Category="Cairnwell|State") bool bGuardsClosed = true;
    UPROPERTY(EditAnywhere, BlueprintReadWrite, SaveGame, Category="Cairnwell|State") bool bStripAvailable = false;
    UPROPERTY(EditAnywhere, BlueprintReadWrite, SaveGame, Category="Cairnwell|State") bool bCassetteLocked = true;
    UPROPERTY(EditAnywhere, BlueprintReadWrite, SaveGame, Category="Cairnwell|State") bool bDrivesHealthy = true;

private:
    static constexpr float CalibrationDurationSeconds = 2.0f;
    static constexpr float StoppingDurationSeconds = 1.25f;
    static constexpr float MaximumGapErrorMm = 0.25f;
    static constexpr float MaximumMotorLoadPercent = 95.0f;

    float PhaseElapsedSeconds = 0.0f;
    float CalibrationStartGapMm = 1.80f;
    float MotionAngleDegrees = 0.0f;
    FVector UpperCassetteRestLocation = FVector::ZeroVector;
    TArray<FVector> GapCylinderRestLocations;
    TWeakObjectPtr<ATextRenderActor> HMIStatePresentation;

    void SetState(ELBPR006State NewState);
    void RaiseFault(ELBPR006Fault Fault);
    void EvaluateRuntimePermissives();
    void ApplyMachinePose();
    void BindMapPresentation();
    void UpdateHMITextPresentation();
};
