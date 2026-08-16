#pragma once

#include "CoreMinimal.h"
#include "LBSupportRobotRuntimeComponentV002.h"
#include "LBCleaningRobotRuntimeComponentV002.generated.h"

UENUM(BlueprintType)
enum class ELBCleaningRobotFaultV002 : uint8
{
    None,
    SpillDetected,
    TankFull,
    CleanWaterEmpty,
    BrushJam,
    SensorDirty,
    DockWaterCouplerFault,
    DockDirtyCouplerFault,
    WasteGateFault,
    ProcessAuthorityFault
};

USTRUCT(BlueprintType)
struct LINEBOSSSUPPORTROBOTSRUNTIMEV002_API FLBCleaningRobotSafeSaveV002
{
    GENERATED_BODY()

    UPROPERTY(EditAnywhere, BlueprintReadWrite, SaveGame, Category = "Line Boss|CR01 v002|Save")
    int32 Version = 2;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, SaveGame, Category = "Line Boss|CR01 v002|Save")
    FLBSupportRobotSafeSaveV002 Common;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, SaveGame, Category = "Line Boss|CR01 v002|Save")
    ELBCleaningRobotFaultV002 PersistedCleaningFault = ELBCleaningRobotFaultV002::None;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, SaveGame, Category = "Line Boss|CR01 v002|Save")
    double CleanWaterLitres = 0.0;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, SaveGame, Category = "Line Boss|CR01 v002|Save")
    double RecoveryWaterLitres = 0.0;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, SaveGame, Category = "Line Boss|CR01 v002|Save")
    double HopperLoadLitres = 0.0;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, SaveGame, Category = "Line Boss|CR01 v002|Save")
    double FrontBrushWearPercent = 0.0;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, SaveGame, Category = "Line Boss|CR01 v002|Save")
    double SideBrushWearPercent = 0.0;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, SaveGame, Category = "Line Boss|CR01 v002|Save")
    double ScrubDiscWearPercent = 0.0;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, SaveGame, Category = "Line Boss|CR01 v002|Save")
    double SqueegeeWearPercent = 0.0;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, SaveGame, Category = "Line Boss|CR01 v002|Save")
    double LifetimeCoverageSquareMetres = 0.0;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, SaveGame, Category = "Line Boss|CR01 v002|Save")
    FName LastSpillId = NAME_None;
};

/** Geometry-free CR01 logic; visual adapters consume desired mechanism state later. */
UCLASS(BlueprintType, ClassGroup = (LineBoss), meta = (BlueprintSpawnableComponent))
class LINEBOSSSUPPORTROBOTSRUNTIMEV002_API ULBCleaningRobotRuntimeComponentV002
    : public ULBSupportRobotRuntimeComponentV002
{
    GENERATED_BODY()

public:
    ULBCleaningRobotRuntimeComponentV002();

    UFUNCTION(BlueprintCallable, Category = "Line Boss|CR01 v002|Safety")
    bool RequestSensorCoverageCertification(FName EvidenceId);

    UFUNCTION(BlueprintCallable, Category = "Line Boss|CR01 v002|Cleaning")
    bool StartCleaningTask(FName TaskId, FName CleaningZoneId, FName AuthorityEvidenceId);

    UFUNCTION(BlueprintCallable, Category = "Line Boss|CR01 v002|Cleaning")
    void StopCleaningTask();

    UFUNCTION(BlueprintCallable, Category = "Line Boss|CR01 v002|Safety")
    void ReportHazardousSpill(FName SpillId);

    UFUNCTION(BlueprintCallable, Category = "Line Boss|CR01 v002|Fault")
    void ReportCleaningFault(ELBCleaningRobotFaultV002 Fault, FName SourceId,
        const FString& Detail);

    /** Native dock provider result only; deliberately not Blueprint-callable. */
    bool ApplyTrustedDockServiceResult(double NewCleanWaterLitres,
        double NewRecoveryWaterLitres, double NewHopperLoadLitres);

    /** Trusted service/commissioning path for replaced consumables. */
    bool ApplyTrustedConsumableServiceResult(double NewFrontBrushWearPercent,
        double NewSideBrushWearPercent, double NewScrubDiscWearPercent,
        double NewSqueegeeWearPercent, FName ServiceEvidenceId);

    UFUNCTION(BlueprintPure, Category = "Line Boss|CR01 v002|Save")
    FLBCleaningRobotSafeSaveV002 CaptureCleaningSafeSave() const;

    /** Native save-coordinator boundary; Blueprint cannot apply a fabricated DTO. */
    bool RestoreCleaningSafeStopped(const FLBCleaningRobotSafeSaveV002& SavedState);

protected:
    virtual void AppendAnchorContract(TArray<FLBAnchorSpecV002>& InOutSpecs) const override;
    virtual FName GetExpectedVariantIdV002() const override { return TEXT("LB-CR01"); }
    virtual bool ValidateVariantForCertification(FString& OutFailure) const override;
    virtual bool ValidateVariantTravelPermissives(FString& OutFailure) const override;
    virtual bool RefreshVariantDynamicInterlocksV002(FString& OutFailure) override;
    virtual void TickVariantProcessV002(double DeltaSeconds) override;
    virtual void OnSafeStopV002() override;
    virtual void OnRouteFinishedSafelyV002() override;
    virtual void OnSafeStoppedRestoreV002() override;
    virtual FName GetActiveVariantFaultIdV002() const override;
    virtual bool CanCommitVariantFaultClearV002(FString& OutFailure) const override;
    virtual void CommitVariantFaultClearV002() override;
    virtual double GetMaximumSpeedCentimetresPerSecondV002(ELBRouteSpeedClassV002 SpeedClass,
        bool bEmergencyDispatch) const override;

private:
    UPROPERTY(VisibleInstanceOnly, SaveGame, Category = "Line Boss|CR01 v002|Fault")
    ELBCleaningRobotFaultV002 ActiveCleaningFault = ELBCleaningRobotFaultV002::None;

    UPROPERTY(VisibleInstanceOnly, SaveGame, Category = "Line Boss|CR01 v002|Resources")
    double CleanWaterLitres = 0.0;

    UPROPERTY(VisibleInstanceOnly, SaveGame, Category = "Line Boss|CR01 v002|Resources")
    double RecoveryWaterLitres = 0.0;

    UPROPERTY(VisibleInstanceOnly, SaveGame, Category = "Line Boss|CR01 v002|Resources")
    double HopperLoadLitres = 0.0;

    UPROPERTY(VisibleInstanceOnly, SaveGame, Category = "Line Boss|CR01 v002|Wear")
    double FrontBrushWearPercent = 0.0;

    UPROPERTY(VisibleInstanceOnly, SaveGame, Category = "Line Boss|CR01 v002|Wear")
    double SideBrushWearPercent = 0.0;

    UPROPERTY(VisibleInstanceOnly, SaveGame, Category = "Line Boss|CR01 v002|Wear")
    double ScrubDiscWearPercent = 0.0;

    UPROPERTY(VisibleInstanceOnly, SaveGame, Category = "Line Boss|CR01 v002|Wear")
    double SqueegeeWearPercent = 0.0;

    UPROPERTY(VisibleInstanceOnly, SaveGame, Category = "Line Boss|CR01 v002|Coverage")
    double LifetimeCoverageSquareMetres = 0.0;

    UPROPERTY(VisibleInstanceOnly, Category = "Line Boss|CR01 v002|Safety")
    bool bSensorCoverageProvedThisSession = false;

    FName ActiveSensorCoverageEvidenceId = NAME_None;
    FName ActiveTaskAuthorityEvidenceId = NAME_None;
    FLBTrustedCleaningTaskGrantV002 ActiveCleaningTaskGrant;
    uint64 LastCleaningProcessSequence = 0;

    UPROPERTY(VisibleInstanceOnly, Category = "Line Boss|CR01 v002|Cleaning")
    FName ActiveCleaningZoneId = NAME_None;

    UPROPERTY(VisibleInstanceOnly, Category = "Line Boss|CR01 v002|Cleaning")
    bool bWetScrubActive = false;

    UPROPERTY(VisibleInstanceOnly, Category = "Line Boss|CR01 v002|Cleaning")
    bool bWaterValveCommandedOpen = false;

    UPROPERTY(VisibleInstanceOnly, Category = "Line Boss|CR01 v002|Cleaning")
    bool bBrushesCommandedRunning = false;

    UPROPERTY(VisibleInstanceOnly, Category = "Line Boss|CR01 v002|Cleaning")
    bool bCleaningHeadsCommandedLowered = false;

    UPROPERTY(VisibleInstanceOnly, SaveGame, Category = "Line Boss|CR01 v002|Safety")
    FName LastSpillId = NAME_None;

    static constexpr double CleanWaterCapacityLitres = 120.0;
    static constexpr double RecoveryWaterCapacityLitres = 130.0;
    static constexpr double HopperCapacityLitres = 45.0;
    static constexpr double CleaningSwathMetres = 1.35;
    static constexpr double FrontBrushRpm = 250.0;
    static constexpr double SideBrushRpm = 180.0;
    static constexpr double ScrubDiscRpm = 300.0;
    static constexpr double FrontBrushLiftMillimetresPerSecond = 35.0;
    static constexpr double SideBrushArmDegreesPerSecond = 25.0;
    static constexpr double SideBrushLiftMillimetresPerSecond = 25.0;
    static constexpr double ScrubDeckLiftMillimetresPerSecond = 30.0;
    static constexpr double SqueegeeLiftMillimetresPerSecond = 35.0;

    void CommandAllCleaningMechanismsSafe();
    void RevokeActiveCleaningTaskGrant();
};
