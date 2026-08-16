#pragma once

#include "CoreMinimal.h"
#include "LBSupportRobotRuntimeComponentV002.h"
#include "LBMaintenanceRobotRuntimeComponentV002.generated.h"

UENUM(BlueprintType)
enum class ELBMaintenanceToolV002 : uint8
{
    None,
    T1_InspectionHead,
    T2_ConditionProbe,
    T3_Lubrication,
    T4_Cleaning,
    T5_ServiceGripper,
    T6_TorqueTool,
    T7_FluidLeak,
    T8_ModuleExchange
};

UENUM(BlueprintType)
enum class ELBMaintenanceTaskV002 : uint8
{
    Inspection,
    Diagnosis,
    Lubrication,
    SensorCleaning,
    PartsDelivery,
    ApprovedFastenerService,
    LeakClassification,
    ApprovedModuleExchange
};

UENUM(BlueprintType)
enum class ELBMaintenanceRobotFaultV002 : uint8
{
    None,
    F01_DirtySafetyScanner,
    F02_LostLocalisation,
    F03_LowOrDegradedBattery,
    F04_ArmCalibrationDrift,
    F05_ToolNotSeated,
    F06_IncorrectToolSelected,
    F07_GreaseCartridgeEmpty,
    F08_LubricationPointBlocked,
    F09_TorqueVerificationFailed,
    F10_ReplacementPartMismatch,
    F11_ManipulatorOverload,
    F12_OutriggerNotDeployed,
    F13_CellAccessNotAuthorised,
    F14_LOTOStatusInvalid,
    F15_ExclusionZoneIntrusion,
    F16_LeakOrContaminationDetected,
    F17_DockingContactsDirty,
    F18_ToolRackSlotMismatch,
    F19_SensorMastJam,
    F20_DiagnosticHandshakeFailed,
    F21_PartsDrawerOpen,
    F22_ArmParkingNotProved
};

USTRUCT(BlueprintType)
struct LINEBOSSSUPPORTROBOTSRUNTIMEV002_API FLBMaintenanceRobotSafeSaveV002
{
    GENERATED_BODY()

    UPROPERTY(EditAnywhere, BlueprintReadWrite, SaveGame, Category = "Line Boss|MR01 v002|Save")
    int32 Version = 2;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, SaveGame, Category = "Line Boss|MR01 v002|Save")
    FLBSupportRobotSafeSaveV002 Common;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, SaveGame, Category = "Line Boss|MR01 v002|Save")
    ELBMaintenanceRobotFaultV002 PersistedMaintenanceFault = ELBMaintenanceRobotFaultV002::None;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, SaveGame, Category = "Line Boss|MR01 v002|Save")
    ELBMaintenanceToolV002 ExpectedActiveTool = ELBMaintenanceToolV002::None;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, SaveGame, Category = "Line Boss|MR01 v002|Save")
    TArray<ELBMaintenanceToolV002> ExpectedToolRackInventory;

    /** Diagnostic observation only; restore never commands this pose. */
    UPROPERTY(EditAnywhere, BlueprintReadWrite, SaveGame, Category = "Line Boss|MR01 v002|Save")
    TArray<double> LastObservedJointDegrees;

    /** Diagnostic observation only; restore never commands this lift. */
    UPROPERTY(EditAnywhere, BlueprintReadWrite, SaveGame, Category = "Line Boss|MR01 v002|Save")
    double LastObservedArmLiftMillimetres = 0.0;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, SaveGame, Category = "Line Boss|MR01 v002|Save")
    double LastObservedMastExtensionMillimetres = 0.0;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, SaveGame, Category = "Line Boss|MR01 v002|Save")
    FName LastCompletedPermitId = NAME_None;
};

/** Authority-first MR01 runtime component. It owns no arm, wheel, mesh or collision. */
UCLASS(BlueprintType, ClassGroup = (LineBoss), meta = (BlueprintSpawnableComponent))
class LINEBOSSSUPPORTROBOTSRUNTIMEV002_API ULBMaintenanceRobotRuntimeComponentV002
    : public ULBSupportRobotRuntimeComponentV002
{
    GENERATED_BODY()

public:
    ULBMaintenanceRobotRuntimeComponentV002();

    virtual void TickComponent(float DeltaTime, ELevelTick TickType,
        FActorComponentTickFunction* ThisTickFunction) override;

    UFUNCTION(BlueprintCallable, Category = "Line Boss|MR01 v002|Travel")
    bool RequestTravelReadinessProof(FName EvidenceId);

    UFUNCTION(BlueprintCallable, Category = "Line Boss|MR01 v002|Tool")
    bool RequestToolCouplingProof(ELBMaintenanceToolV002 RequestedTool,
        int32 RackSlot, FName EvidenceId);

    UFUNCTION(BlueprintCallable, Category = "Line Boss|MR01 v002|Tool")
    bool RequestActiveToolReturnProof(int32 RackSlot, FName EvidenceId);

    UFUNCTION(BlueprintCallable, Category = "Line Boss|MR01 v002|Task")
    bool BeginMaintenanceTask(ELBMaintenanceTaskV002 Task, FName TaskId,
        FName CertifiedWorkPointId, FName PermitId);

    UFUNCTION(BlueprintCallable, Category = "Line Boss|MR01 v002|Outriggers")
    bool RequestOutriggerDeploymentProof();

    UFUNCTION(BlueprintPure, Category = "Line Boss|MR01 v002|Arm")
    bool CanUseArm(FText& BlockingReason) const;

    /** Native motion adapter authorization; does not move geometry itself. */
    bool AuthorizeArmMotionCommand(double LiftMillimetres,
        const TArray<double>& JointDegrees, FGuid& OutCommandId, FString& OutFailure);

    /** Native motion adapter completion notification. */
    void NotifyArmMotionStopped(const FGuid& CommandId,
        const TArray<double>& ObservedJointDegrees, double ObservedLiftMillimetres);

    UFUNCTION(BlueprintCallable, Category = "Line Boss|MR01 v002|Task")
    bool CompleteMaintenanceTask(FName EvidenceId);

    UFUNCTION(BlueprintCallable, Category = "Line Boss|MR01 v002|Task")
    void AbortMaintenanceTaskAndSafeStop();

    UFUNCTION(BlueprintCallable, Category = "Line Boss|MR01 v002|Fault")
    void ReportMaintenanceFault(ELBMaintenanceRobotFaultV002 Fault,
        const FString& Detail);

    UFUNCTION(BlueprintPure, Category = "Line Boss|MR01 v002|Save")
    FLBMaintenanceRobotSafeSaveV002 CaptureMaintenanceSafeSave() const;

    /** Native save-coordinator boundary; Blueprint cannot apply a fabricated DTO. */
    bool RestoreMaintenanceSafeStopped(const FLBMaintenanceRobotSafeSaveV002& SavedState);

protected:
    virtual void AppendAnchorContract(TArray<FLBAnchorSpecV002>& InOutSpecs) const override;
    virtual FName GetExpectedVariantIdV002() const override { return TEXT("LB-MR01"); }
    virtual bool RequiresCalibration() const override { return true; }
    virtual bool ValidateVariantForCertification(FString& OutFailure) const override;
    virtual bool ValidateVariantTravelPermissives(FString& OutFailure) const override;
    virtual bool RefreshVariantDynamicInterlocksV002(FString& OutFailure) override;
    virtual void OnSafeStopV002() override;
    virtual void OnRouteFinishedSafelyV002() override;
    virtual void OnSafeStoppedRestoreV002() override;
    virtual FName GetActiveVariantFaultIdV002() const override;
    virtual bool CanCommitVariantFaultClearV002(FString& OutFailure) const override;
    virtual void CommitVariantFaultClearV002() override;
    virtual double GetMaximumSpeedCentimetresPerSecondV002(ELBRouteSpeedClassV002 SpeedClass,
        bool bEmergencyDispatch) const override;
    virtual double GetAccelerationCentimetresPerSecondSquaredV002(
        ELBRouteSpeedClassV002 SpeedClass, bool bEmergencyDispatch) const override;

private:
    UPROPERTY(VisibleInstanceOnly, SaveGame, Category = "Line Boss|MR01 v002|Fault")
    ELBMaintenanceRobotFaultV002 ActiveMaintenanceFault = ELBMaintenanceRobotFaultV002::None;

    UPROPERTY(VisibleInstanceOnly, Category = "Line Boss|MR01 v002|Task")
    ELBMaintenanceTaskV002 ActiveMaintenanceTask = ELBMaintenanceTaskV002::Inspection;

    UPROPERTY(VisibleInstanceOnly, SaveGame, Category = "Line Boss|MR01 v002|Tool")
    ELBMaintenanceToolV002 ActiveTool = ELBMaintenanceToolV002::None;

    UPROPERTY(VisibleInstanceOnly, SaveGame, Category = "Line Boss|MR01 v002|Tool")
    TArray<ELBMaintenanceToolV002> ToolRackInventory;

    UPROPERTY(VisibleInstanceOnly, SaveGame, Category = "Line Boss|MR01 v002|Arm")
    TArray<double> LastObservedJointDegrees;

    UPROPERTY(VisibleInstanceOnly, SaveGame, Category = "Line Boss|MR01 v002|Arm")
    double LastObservedArmLiftMillimetres = 0.0;

    UPROPERTY(VisibleInstanceOnly, SaveGame, Category = "Line Boss|MR01 v002|Mast")
    double LastObservedMastExtensionMillimetres = 0.0;

    UPROPERTY(VisibleInstanceOnly, SaveGame, Category = "Line Boss|MR01 v002|Task")
    FName LastCompletedPermitId = NAME_None;

    UPROPERTY(VisibleInstanceOnly, Category = "Line Boss|MR01 v002|Arm")
    bool bArmMotionActive = false;

    FGuid ActiveArmCommandId;
    TArray<double> AuthorizedJointDegrees;
    double AuthorizedArmLiftMillimetres = 0.0;

    FLBTrustedTravelInterlockProofV002 ActiveTravelProof;
    FLBTrustedToolCouplingProofV002 ActiveToolProof;
    FLBTrustedWorkAuthorityV002 ActiveWorkGrant;
    FLBTrustedOutriggerProofV002 ActiveOutriggerProof;

    static constexpr double MaximumArmPayloadIncludingToolKilograms = 25.0;

    ELBMaintenanceToolV002 RequiredToolForTask(ELBMaintenanceTaskV002 Task) const;
    FName ToolIdForEnum(ELBMaintenanceToolV002 Tool) const;
    bool IsJointPoseValid(double LiftMillimetres, const TArray<double>& JointDegrees) const;
    void ClearArmMotionCommandV002();
    void RevokeWorkAuthorityAndClearTask();
    void ClearAllVariantProofs();
    bool RefreshWorkAndToolProofs(FString& OutFailure, bool bRequireOutriggerProof,
        ELBMaintenanceRobotFaultV002* OutSuggestedFault = nullptr);
};
