#pragma once

#include "CoreMinimal.h"
#include "LBSupportRobot.h"
#include "LBCleaningAMR.generated.h"

class USceneComponent;
class UChildActorComponent;
class USpotLightComponent;

UENUM(BlueprintType)
enum class ELBCleaningAMRFault : uint8
{
    None,
    SpillDetected,
    TankFull,
    CleanWaterEmpty,
    BrushJam,
    SensorDirty,
    DockWaterCouplerFault,
    DockDirtyCouplerFault,
    WasteGateFault
};

USTRUCT(BlueprintType)
struct FLBCleaningAMRSaveState
{
    GENERATED_BODY()

    UPROPERTY(EditAnywhere, BlueprintReadWrite, SaveGame)
    int32 Version = 1;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, SaveGame)
    FLBSupportRobotSaveState Common;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, SaveGame)
    ELBCleaningAMRFault CleaningFault = ELBCleaningAMRFault::None;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, SaveGame)
    float CleanWaterLitres = 0.0f;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, SaveGame)
    float RecoveryWaterLitres = 0.0f;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, SaveGame)
    float HopperLoadLitres = 0.0f;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, SaveGame)
    float FrontBrushWearPercent = 100.0f;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, SaveGame)
    float SideBrushWearPercent = 100.0f;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, SaveGame)
    float ScrubDiscWearPercent = 100.0f;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, SaveGame)
    float SqueegeeWearPercent = 100.0f;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, SaveGame)
    float LifetimeCoverageSquareMetres = 0.0f;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, SaveGame)
    FName ActiveCleaningZoneId = NAME_None;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, SaveGame)
    FName LastSpillId = NAME_None;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, SaveGame)
    bool bSensorCoverageCertified = false;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, SaveGame)
    bool bSpillBoundaryIsolated = false;
};

DECLARE_DYNAMIC_MULTICAST_DELEGATE_ThreeParams(FLBCleaningResourcesChanged, float, CleanWaterLitres, float, RecoveryWaterLitres, float, HopperLoadLitres);
DECLARE_DYNAMIC_MULTICAST_DELEGATE_TwoParams(FLBCleaningSpillEvent, FName, SpillId, bool, bBoundaryIsolated);

/** LB-CR01 cleaning variant built on the shared RP01 platform. */
UCLASS(BlueprintType, Blueprintable)
class LINEBOSSCARFACTORY_API ALBCleaningAMR : public ALBSupportRobot
{
    GENERATED_BODY()

public:
    ALBCleaningAMR();

    virtual void BeginPlay() override;
    virtual void Tick(float DeltaSeconds) override;

    UFUNCTION(BlueprintCallable, Category = "Line Boss|CR01|Cleaning")
    bool StartCleaningTask(FName TaskId, FName CleaningZoneId);

    UFUNCTION(BlueprintCallable, Category = "Line Boss|CR01|Cleaning")
    void StopCleaningTask();

    UFUNCTION(BlueprintCallable, Category = "Line Boss|CR01|Resources")
    bool SetCleaningResources(float NewCleanWaterLitres, float NewRecoveryWaterLitres, float NewHopperLoadLitres);

    UFUNCTION(BlueprintCallable, Category = "Line Boss|CR01|Safety")
    void SetSensorCoverageCertified(bool bCertifiedCoverage);

    UFUNCTION(BlueprintCallable, Category = "Line Boss|CR01|Safety")
    void ReportHazardousSpill(FName SpillId);

    UFUNCTION(BlueprintCallable, Category = "Line Boss|CR01|Safety")
    bool ConfirmSpillBoundaryIsolated(FName SpillId);

    UFUNCTION(BlueprintCallable, Category = "Line Boss|CR01|Safety")
    bool ReleaseSpillStopAfterHumanClearance(FName SpillId);

    UFUNCTION(BlueprintCallable, Category = "Line Boss|CR01|Fault")
    void ReportBrushJam(FName BrushId);

    UFUNCTION(BlueprintCallable, Category = "Line Boss|CR01|Dock")
    bool BeginDockService();

    UFUNCTION(BlueprintCallable, Category = "Line Boss|CR01|Dock")
    bool CompleteDockService();

    UFUNCTION(BlueprintPure, Category = "Line Boss|CR01|Save")
    FLBCleaningAMRSaveState CaptureSaveState() const;

    UFUNCTION(BlueprintCallable, Category = "Line Boss|CR01|Save")
    bool RestoreSaveState(const FLBCleaningAMRSaveState& SavedState);

    UPROPERTY(BlueprintAssignable, Category = "Line Boss|CR01|Events")
    FLBCleaningResourcesChanged OnCleaningResourcesChanged;

    UPROPERTY(BlueprintAssignable, Category = "Line Boss|CR01|Events")
    FLBCleaningSpillEvent OnSpillStateChanged;

    USpotLightComponent* GetCleaningDeckWorkLight() const { return CleaningDeckWorkLight; }

protected:
    virtual bool HasVariantTravelPermissives(FText& BlockingReason) const override;
    virtual float GetMaximumSpeedCentimetresPerSecond(ELBRouteSpeedClass SpeedClass, bool bEmergencyDispatch) const override;
    virtual void OnEnteredSafeStop() override;
    virtual void UpdateVariantWorkLights() override;

    /** Visual-only authored CR01/RP01 assembly; authority and blocking collision stay on this actor. */
    UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category = "Line Boss|CR01|Presentation")
    TObjectPtr<UChildActorComponent> PresentationComponent;

    /** Downward flood lamp that makes the active brush/scrub area readable. */
    UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category = "Line Boss|CR01|Presentation")
    TObjectPtr<USpotLightComponent> CleaningDeckWorkLight;

    UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category = "Line Boss|CR01|RP01 Running Gear Pivots")
    TObjectPtr<USceneComponent> DriveWheelLeftPivot;

    UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category = "Line Boss|CR01|RP01 Running Gear Pivots")
    TObjectPtr<USceneComponent> DriveWheelRightPivot;

    UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category = "Line Boss|CR01|RP01 Running Gear Pivots")
    TObjectPtr<USceneComponent> FrontCasterSwivelPivot;

    UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category = "Line Boss|CR01|RP01 Running Gear Pivots")
    TObjectPtr<USceneComponent> FrontCasterRollPivot;

    UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category = "Line Boss|CR01|RP01 Running Gear Pivots")
    TObjectPtr<USceneComponent> RearCasterSwivelPivot;

    UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category = "Line Boss|CR01|RP01 Running Gear Pivots")
    TObjectPtr<USceneComponent> RearCasterRollPivot;

    UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category = "Line Boss|CR01|Pivots")
    TObjectPtr<USceneComponent> FrontBrushLiftPivot;

    UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category = "Line Boss|CR01|Pivots")
    TObjectPtr<USceneComponent> FrontBrushSpinPivot;

    UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category = "Line Boss|CR01|Pivots")
    TObjectPtr<USceneComponent> SideBrushArmLeftPivot;

    UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category = "Line Boss|CR01|Pivots")
    TObjectPtr<USceneComponent> SideBrushArmRightPivot;

    UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category = "Line Boss|CR01|Pivots")
    TObjectPtr<USceneComponent> SideBrushLiftLeftPivot;

    UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category = "Line Boss|CR01|Pivots")
    TObjectPtr<USceneComponent> SideBrushLiftRightPivot;

    UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category = "Line Boss|CR01|Pivots")
    TObjectPtr<USceneComponent> SideBrushSpinLeftPivot;

    UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category = "Line Boss|CR01|Pivots")
    TObjectPtr<USceneComponent> SideBrushSpinRightPivot;

    UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category = "Line Boss|CR01|Pivots")
    TObjectPtr<USceneComponent> ScrubDeckLiftPivot;

    UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category = "Line Boss|CR01|Pivots")
    TObjectPtr<USceneComponent> ScrubDiscLeftPivot;

    UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category = "Line Boss|CR01|Pivots")
    TObjectPtr<USceneComponent> ScrubDiscRightPivot;

    UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category = "Line Boss|CR01|Pivots")
    TObjectPtr<USceneComponent> SqueegeeLiftPivot;

    UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category = "Line Boss|CR01|Pivots")
    TObjectPtr<USceneComponent> SqueegeeYawPivot;

    UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category = "Line Boss|CR01|Service Pivots")
    TObjectPtr<USceneComponent> HopperSlidePivot;

    UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category = "Line Boss|CR01|Service Pivots")
    TObjectPtr<USceneComponent> HopperLidPivot;

    UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category = "Line Boss|CR01|Service Pivots")
    TObjectPtr<USceneComponent> LeftDoorPivot;

    UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category = "Line Boss|CR01|Service Pivots")
    TObjectPtr<USceneComponent> RightDoorPivot;

    UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category = "Line Boss|CR01|Service Pivots")
    TObjectPtr<USceneComponent> RearDoorPivot;

    UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category = "Line Boss|CR01|Service Pivots")
    TObjectPtr<USceneComponent> FilterLidPivot;

    UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category = "Line Boss|CR01|Dock Pivots")
    TObjectPtr<USceneComponent> DockChargeContactLeftPivot;

    UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category = "Line Boss|CR01|Dock Pivots")
    TObjectPtr<USceneComponent> DockChargeContactRightPivot;

private:
    UPROPERTY(VisibleInstanceOnly, SaveGame, Category = "Line Boss|CR01|Fault")
    ELBCleaningAMRFault ActiveCleaningFault = ELBCleaningAMRFault::None;

    UPROPERTY(EditInstanceOnly, SaveGame, Category = "Line Boss|CR01|Resources", meta = (ClampMin = "0.0", ClampMax = "120.0"))
    float CleanWaterLitres = 0.0f;

    UPROPERTY(EditInstanceOnly, SaveGame, Category = "Line Boss|CR01|Resources", meta = (ClampMin = "0.0", ClampMax = "130.0"))
    float RecoveryWaterLitres = 0.0f;

    UPROPERTY(EditInstanceOnly, SaveGame, Category = "Line Boss|CR01|Resources", meta = (ClampMin = "0.0", ClampMax = "45.0"))
    float HopperLoadLitres = 0.0f;

    UPROPERTY(VisibleInstanceOnly, SaveGame, Category = "Line Boss|CR01|Wear")
    float FrontBrushWearPercent = 100.0f;

    UPROPERTY(VisibleInstanceOnly, SaveGame, Category = "Line Boss|CR01|Wear")
    float SideBrushWearPercent = 100.0f;

    UPROPERTY(VisibleInstanceOnly, SaveGame, Category = "Line Boss|CR01|Wear")
    float ScrubDiscWearPercent = 100.0f;

    UPROPERTY(VisibleInstanceOnly, SaveGame, Category = "Line Boss|CR01|Wear")
    float SqueegeeWearPercent = 100.0f;

    UPROPERTY(VisibleInstanceOnly, SaveGame, Category = "Line Boss|CR01|Cleaning")
    float LifetimeCoverageSquareMetres = 0.0f;

    UPROPERTY(VisibleInstanceOnly, SaveGame, Category = "Line Boss|CR01|Cleaning")
    FName ActiveCleaningZoneId = NAME_None;

    UPROPERTY(VisibleInstanceOnly, SaveGame, Category = "Line Boss|CR01|Safety")
    FName LastSpillId = NAME_None;

    UPROPERTY(VisibleInstanceOnly, SaveGame, Category = "Line Boss|CR01|Safety")
    bool bSensorCoverageCertified = false;

    UPROPERTY(VisibleInstanceOnly, SaveGame, Category = "Line Boss|CR01|Safety")
    bool bSpillBoundaryIsolated = false;

    bool bWaterValveOpen = false;
    bool bBrushesRunning = false;
    bool bCleaningHeadsLowered = false;
    float CleaningDeploymentAlpha = 0.0f;
    FVector LastCoverageLocation = FVector::ZeroVector;

    TMap<FName, TWeakObjectPtr<USceneComponent>> PresentationPivots;

    static constexpr float CleanWaterCapacityLitres = 120.0f;
    static constexpr float RecoveryWaterCapacityLitres = 130.0f;
    static constexpr float HopperCapacityLitres = 45.0f;
    static constexpr float CleaningSwathMetres = 1.35f;

    void ApplyCleaningPose(float DeltaSeconds);
    void TickCleaningResources(float DistanceMovedCentimetres);
    void CachePresentationBindings();
    USceneComponent* FindPresentationPivot(FName ComponentName) const;
};
