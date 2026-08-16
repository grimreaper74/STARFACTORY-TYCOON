#pragma once

#include "CoreMinimal.h"
#include "GameFramework/Actor.h"
#include "LBPR007Station.generated.h"

class USceneComponent;
class ATextRenderActor;

UENUM(BlueprintType)
enum class ELBPR007State : uint8
{
    Isolated,
    Ready,
    Priming,
    Running,
    Stopping,
    Fault
};

UENUM(BlueprintType)
enum class ELBPR007Fault : uint8
{
    None,
    GuardOpen,
    LowWashLevel,
    LowLubeLevel,
    FilterDifferentialHigh,
    MistExtractionUnavailable
};

USTRUCT(BlueprintType)
struct FLBPR007HMIStatus
{
    GENERATED_BODY()

    UPROPERTY(BlueprintReadOnly) FName StationId = TEXT("PR-007");
    UPROPERTY(BlueprintReadOnly) ELBPR007State State = ELBPR007State::Isolated;
    UPROPERTY(BlueprintReadOnly) ELBPR007Fault ActiveFault = ELBPR007Fault::None;
    UPROPERTY(BlueprintReadOnly) float WashLevelPercent = 0.0f;
    UPROPERTY(BlueprintReadOnly) float LubeLevelPercent = 0.0f;
    UPROPERTY(BlueprintReadOnly) float FilterDifferentialBar = 0.0f;
    UPROPERTY(BlueprintReadOnly) float StripTravelMetres = 0.0f;
    UPROPERTY(BlueprintReadOnly) float LineSpeedMetresPerMinute = 0.0f;
    UPROPERTY(BlueprintReadOnly) float HoodPosition = 0.0f;
    UPROPERTY(BlueprintReadOnly) bool bControlPowerOn = false;
    UPROPERTY(BlueprintReadOnly) bool bGuardsClosed = false;
    UPROPERTY(BlueprintReadOnly) bool bStripThreaded = false;
    UPROPERTY(BlueprintReadOnly) bool bMistExtractionHealthy = false;
    UPROPERTY(BlueprintReadOnly) bool bCanStart = false;
    UPROPERTY(BlueprintReadOnly) TArray<FText> BlockingReasons;
};

USTRUCT(BlueprintType)
struct FLBPR007SaveState
{
    GENERATED_BODY()

    UPROPERTY(EditAnywhere, BlueprintReadWrite, SaveGame) int32 Version = 1;
    UPROPERTY(EditAnywhere, BlueprintReadWrite, SaveGame) FName StationId = TEXT("PR-007");
    UPROPERTY(EditAnywhere, BlueprintReadWrite, SaveGame) ELBPR007State State = ELBPR007State::Isolated;
    UPROPERTY(EditAnywhere, BlueprintReadWrite, SaveGame) ELBPR007Fault ActiveFault = ELBPR007Fault::None;
    UPROPERTY(EditAnywhere, BlueprintReadWrite, SaveGame) float WashLevelPercent = 75.0f;
    UPROPERTY(EditAnywhere, BlueprintReadWrite, SaveGame) float LubeLevelPercent = 75.0f;
    UPROPERTY(EditAnywhere, BlueprintReadWrite, SaveGame) float FilterDifferentialBar = 0.25f;
    UPROPERTY(EditAnywhere, BlueprintReadWrite, SaveGame) float StripTravelMetres = 0.0f;
    UPROPERTY(EditAnywhere, BlueprintReadWrite, SaveGame) float RunningHours = 0.0f;
    UPROPERTY(EditAnywhere, BlueprintReadWrite, SaveGame) float TargetLineSpeedMetresPerMinute = 12.0f;
    UPROPERTY(EditAnywhere, BlueprintReadWrite, SaveGame) bool bControlPowerOn = false;
    UPROPERTY(EditAnywhere, BlueprintReadWrite, SaveGame) bool bGuardsClosed = true;
    UPROPERTY(EditAnywhere, BlueprintReadWrite, SaveGame) bool bStripThreaded = false;
    UPROPERTY(EditAnywhere, BlueprintReadWrite, SaveGame) bool bMistExtractionHealthy = true;
};

DECLARE_DYNAMIC_MULTICAST_DELEGATE_TwoParams(FLBPR007StateChanged, ELBPR007State, PreviousState, ELBPR007State, NewState);
DECLARE_DYNAMIC_MULTICAST_DELEGATE_OneParam(FLBPR007FaultRaised, ELBPR007Fault, Fault);

/** Native authority for the PR-007 strip washer and precision lubricator. */
UCLASS(BlueprintType)
class LINEBOSSCARFACTORY_API ALBPR007Station : public AActor
{
    GENERATED_BODY()

public:
    ALBPR007Station();
    virtual void BeginPlay() override;
    virtual void Tick(float DeltaSeconds) override;

    UFUNCTION(BlueprintCallable, Category="Cairnwell|PR-007") void SetControlPower(bool bEnabled);
    UFUNCTION(BlueprintCallable, Category="Cairnwell|PR-007") void SetGuardsClosed(bool bClosed);
    UFUNCTION(BlueprintCallable, Category="Cairnwell|PR-007") void SetStripThreaded(bool bThreaded);
    UFUNCTION(BlueprintCallable, Category="Cairnwell|PR-007") void SetMistExtractionHealthy(bool bHealthy);
    UFUNCTION(BlueprintCallable, Category="Cairnwell|PR-007") void SetFluidLevels(float NewWashPercent, float NewLubePercent);
    UFUNCTION(BlueprintCallable, Category="Cairnwell|PR-007") void SetFilterDifferential(float DifferentialBar);
    UFUNCTION(BlueprintCallable, Category="Cairnwell|PR-007") bool StartLine();
    UFUNCTION(BlueprintCallable, Category="Cairnwell|PR-007") void RequestControlledStop();
    UFUNCTION(BlueprintCallable, Category="Cairnwell|PR-007") bool ResetFault();
    UFUNCTION(BlueprintPure, Category="Cairnwell|PR-007") bool CanStart(TArray<FText>& BlockingReasons) const;
    UFUNCTION(BlueprintPure, Category="Cairnwell|PR-007|HMI") FLBPR007HMIStatus GetHMIStatus() const;
    UFUNCTION(BlueprintPure, Category="Cairnwell|PR-007|Save") FLBPR007SaveState CaptureSaveState() const;
    UFUNCTION(BlueprintCallable, Category="Cairnwell|PR-007|Save") bool RestoreSaveState(const FLBPR007SaveState& SavedState);

    UPROPERTY(BlueprintAssignable, Category="Cairnwell|PR-007") FLBPR007StateChanged OnStateChanged;
    UPROPERTY(BlueprintAssignable, Category="Cairnwell|PR-007") FLBPR007FaultRaised OnFaultRaised;

protected:
    UPROPERTY(VisibleAnywhere, BlueprintReadOnly) TObjectPtr<USceneComponent> StationRoot;
    UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category="Cairnwell|PR-007|Motion") TObjectPtr<USceneComponent> WashHoodMover;
    UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category="Cairnwell|PR-007|Motion") TObjectPtr<USceneComponent> WashPumpMover;
    UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category="Cairnwell|PR-007|Motion") TObjectPtr<USceneComponent> LubePumpMover;
    UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category="Cairnwell|PR-007|Motion") TObjectPtr<USceneComponent> FeedRollerMover;
    UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category="Cairnwell|PR-007|Motion") TObjectPtr<USceneComponent> WashRollerMover;
    UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category="Cairnwell|PR-007|Motion") TObjectPtr<USceneComponent> LubeRollerMover;
    UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category="Cairnwell|PR-007|Motion") TObjectPtr<USceneComponent> OutfeedRollerMover;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, SaveGame, Category="Cairnwell|Identity") FName StationId = TEXT("PR-007");
    UPROPERTY(EditAnywhere, BlueprintReadWrite, SaveGame, Category="Cairnwell|State") ELBPR007State State = ELBPR007State::Isolated;
    UPROPERTY(EditAnywhere, BlueprintReadWrite, SaveGame, Category="Cairnwell|State") ELBPR007Fault ActiveFault = ELBPR007Fault::None;
    UPROPERTY(EditAnywhere, BlueprintReadWrite, SaveGame, Category="Cairnwell|Process") float WashLevelPercent = 75.0f;
    UPROPERTY(EditAnywhere, BlueprintReadWrite, SaveGame, Category="Cairnwell|Process") float LubeLevelPercent = 75.0f;
    UPROPERTY(EditAnywhere, BlueprintReadWrite, SaveGame, Category="Cairnwell|Process") float FilterDifferentialBar = 0.25f;
    UPROPERTY(EditAnywhere, BlueprintReadWrite, SaveGame, Category="Cairnwell|Production") float StripTravelMetres = 0.0f;
    UPROPERTY(EditAnywhere, BlueprintReadWrite, SaveGame, Category="Cairnwell|Maintenance") float RunningHours = 0.0f;
    UPROPERTY(EditAnywhere, BlueprintReadWrite, SaveGame, Category="Cairnwell|Production", meta=(ClampMin="0.0")) float TargetLineSpeedMetresPerMinute = 12.0f;
    UPROPERTY(EditAnywhere, BlueprintReadWrite, SaveGame, Category="Cairnwell|State") bool bControlPowerOn = false;
    UPROPERTY(EditAnywhere, BlueprintReadWrite, SaveGame, Category="Cairnwell|State") bool bGuardsClosed = true;
    UPROPERTY(EditAnywhere, BlueprintReadWrite, SaveGame, Category="Cairnwell|State") bool bStripThreaded = false;
    UPROPERTY(EditAnywhere, BlueprintReadWrite, SaveGame, Category="Cairnwell|State") bool bMistExtractionHealthy = true;

private:
    static constexpr float MinimumFluidPercent = 8.0f;
    static constexpr float MaximumFilterDifferentialBar = 1.5f;
    static constexpr float PrimingDurationSeconds = 2.5f;
    static constexpr float StoppingDurationSeconds = 1.5f;
    static constexpr float WashConsumptionPercentPerMetre = 0.004f;
    static constexpr float LubeConsumptionPercentPerMetre = 0.002f;

    float PhaseElapsedSeconds = 0.0f;
    float MotionAngleDegrees = 0.0f;
    FVector HoodRestLocation = FVector::ZeroVector;
    TWeakObjectPtr<ATextRenderActor> HMIStatePresentation;

    void SetState(ELBPR007State NewState);
    void RaiseFault(ELBPR007Fault Fault);
    void EvaluateRuntimePermissives();
    void ApplyMachinePose();
    void BindMapPresentation();
    void UpdateHMITextPresentation();
};
