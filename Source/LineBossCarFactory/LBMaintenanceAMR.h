#pragma once

#include "CoreMinimal.h"
#include "LBSupportRobot.h"
#include "LBMaintenanceAMR.generated.h"

class UPoseableMeshComponent;
class UStaticMeshComponent;
class USpotLightComponent;

class USceneComponent;

UENUM(BlueprintType)
enum class ELBMaintenanceTool : uint8
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
enum class ELBMaintenanceTask : uint8
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

/** Exact F01-F22 maintenance fault authority from the Pro pack. */
UENUM(BlueprintType)
enum class ELBMaintenanceAMRFault : uint8
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
struct FLBMaintenanceAMRSaveState
{
    GENERATED_BODY()

    UPROPERTY(EditAnywhere, BlueprintReadWrite, SaveGame)
    int32 Version = 1;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, SaveGame)
    FLBSupportRobotSaveState Common;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, SaveGame)
    ELBMaintenanceAMRFault MaintenanceFault = ELBMaintenanceAMRFault::None;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, SaveGame)
    ELBMaintenanceTask ActiveTask = ELBMaintenanceTask::Inspection;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, SaveGame)
    ELBMaintenanceTool ActiveTool = ELBMaintenanceTool::None;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, SaveGame)
    TArray<ELBMaintenanceTool> ToolRackInventory;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, SaveGame)
    TArray<float> ArmJointDegrees;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, SaveGame)
    float ArmLiftMillimetres = 0.0f;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, SaveGame)
    int32 ToolCarouselSlot = 1;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, SaveGame)
    bool bToolPresent = false;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, SaveGame)
    bool bToolLocked = false;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, SaveGame)
    bool bArmParked = true;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, SaveGame)
    bool bMastStowed = true;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, SaveGame)
    float MastExtensionMillimetres = 0.0f;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, SaveGame)
    bool bOutriggersDeployed = false;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, SaveGame)
    TArray<float> OutriggerFootLoadsKilograms;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, SaveGame)
    bool bDoorsClosed = true;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, SaveGame)
    bool bPartsDrawerClosed = true;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, SaveGame)
    bool bPayloadSecured = true;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, SaveGame)
    FName WorkPointId = NAME_None;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, SaveGame)
    FName LastCompletedPermitId = NAME_None;
};

DECLARE_DYNAMIC_MULTICAST_DELEGATE_TwoParams(FLBMaintenanceFaultEvent, ELBMaintenanceAMRFault, Fault, FString, Detail);
DECLARE_DYNAMIC_MULTICAST_DELEGATE_ThreeParams(FLBMaintenanceToolChanged, ELBMaintenanceTool, PreviousTool, ELBMaintenanceTool, NewTool, int32, RackSlot);
DECLARE_DYNAMIC_MULTICAST_DELEGATE_TwoParams(FLBMaintenanceArmEvent, FName, UnitId, bool, bArmParked);

/** LB-MR01 inspection and light-maintenance variant built on RP01. */
UCLASS(BlueprintType, Blueprintable)
class LINEBOSSCARFACTORY_API ALBMaintenanceAMR : public ALBSupportRobot
{
    GENERATED_BODY()

public:
    ALBMaintenanceAMR();

    virtual void Tick(float DeltaSeconds) override;

    UFUNCTION(BlueprintCallable, Category = "Line Boss|MR01|Travel")
    void SetTravelInterlocks(bool bArmIsParked, bool bMastIsStowed, bool bMastTravelIsApproved,
        bool bAllOutriggersStowed, bool bAllDoorsClosed, bool bDrawerClosed, bool bPayloadIsSecured);

    UFUNCTION(BlueprintCallable, Category = "Line Boss|MR01|Work Authority")
    void SetWorkPermissives(FName CertifiedWorkPointId, FName PermitId, bool bParkingBrakeIsApplied,
        bool bExclusionZoneIsReserved, bool bNoSuspendedLoadZone, bool bTaskAuthorityIsValid,
        bool bCellPermissionGranted, bool bPlayerAuthorisationGranted, bool bLOTOIsValid);

    UFUNCTION(BlueprintCallable, Category = "Line Boss|MR01|Outriggers")
    bool SetOutriggersDeployed(bool bDeploy, const TArray<float>& FootLoadsKilograms);

    UFUNCTION(BlueprintCallable, Category = "Line Boss|MR01|Mast")
    bool SetMastExtension(float ExtensionMillimetres, bool bTravelApprovedWhenExtended);

    UFUNCTION(BlueprintCallable, Category = "Line Boss|MR01|Task")
    bool BeginMaintenanceTask(ELBMaintenanceTask Task, FName TaskId, bool bRequiresPhysicalLOTO);

    UFUNCTION(BlueprintCallable, Category = "Line Boss|MR01|Task")
    bool CompleteMaintenanceTask(FName EvidenceId);

    UFUNCTION(BlueprintPure, Category = "Line Boss|MR01|Arm")
    bool CanUseArm(FText& BlockingReason) const;

    UFUNCTION(BlueprintCallable, Category = "Line Boss|MR01|Arm")
    bool CommandArmPose(float LiftMillimetres, const TArray<float>& JointDegrees);

    UFUNCTION(BlueprintCallable, Category = "Line Boss|MR01|Arm")
    bool ParkArm();

    UFUNCTION(BlueprintCallable, Category = "Line Boss|MR01|Tool Changer")
    bool BeginToolChange(int32 RackSlot, ELBMaintenanceTool RequestedTool);

    UFUNCTION(BlueprintCallable, Category = "Line Boss|MR01|Tool Changer")
    bool CompleteToolChange(int32 RackSlot, ELBMaintenanceTool IdentifiedTool,
        bool bPresenceSignal, bool bLockSignal, float StraightWithdrawalMillimetres);

    UFUNCTION(BlueprintCallable, Category = "Line Boss|MR01|Fault")
    void RaiseMaintenanceFault(ELBMaintenanceAMRFault Fault, const FString& Detail);

    UFUNCTION(BlueprintCallable, Category = "Line Boss|MR01|Fault")
    bool ClearMaintenanceFault();

    UFUNCTION(BlueprintPure, Category = "Line Boss|MR01|Save")
    FLBMaintenanceAMRSaveState CaptureSaveState() const;

    UFUNCTION(BlueprintCallable, Category = "Line Boss|MR01|Save")
    bool RestoreSaveState(const FLBMaintenanceAMRSaveState& SavedState);

    UPROPERTY(BlueprintAssignable, Category = "Line Boss|MR01|Events")
    FLBMaintenanceFaultEvent OnMaintenanceFault;

    UPROPERTY(BlueprintAssignable, Category = "Line Boss|MR01|Events")
    FLBMaintenanceToolChanged OnToolChanged;

    UPROPERTY(BlueprintAssignable, Category = "Line Boss|MR01|Events")
    FLBMaintenanceArmEvent OnArmParkedChanged;

    USpotLightComponent* GetToolTaskWorkLight() const { return ToolTaskWorkLight; }

protected:
    virtual void BeginPlay() override;
    virtual bool HasVariantTravelPermissives(FText& BlockingReason) const override;
    virtual float GetMaximumSpeedCentimetresPerSecond(ELBRouteSpeedClass SpeedClass, bool bEmergencyDispatch) const override;
    virtual void OnEnteredSafeStop() override;
    virtual void UpdateVariantWorkLights() override;

    UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category = "Line Boss|MR01|Contract Pivots")
    TArray<TObjectPtr<USceneComponent>> ContractPivots;

    UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category = "Line Boss|MR01|Tool Rack")
    TArray<TObjectPtr<USceneComponent>> ToolRackSockets;

    UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category = "Line Boss|MR01|Arm")
    TObjectPtr<USceneComponent> ToolMountSocket;

    UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category = "Line Boss|MR01|Arm")
    TObjectPtr<USceneComponent> ToolCentrePointSocket;

    /** Upper-body task lamp illuminates the approved arm work envelope. */
    UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category = "Line Boss|MR01|Arm")
    TObjectPtr<USpotLightComponent> ToolTaskWorkLight;

    UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category = "Line Boss|MR01|Arm")
    TObjectPtr<USceneComponent> ArmParkingCradle;

    /** Blueprint-supplied v020 presentation components, discovered by tags. */
    UPROPERTY(Transient)
    TObjectPtr<UPoseableMeshComponent> ArmPoseableVisual;

    UPROPERTY(Transient)
    TObjectPtr<UStaticMeshComponent> ArmLiftSleeveVisual;

    UPROPERTY(Transient)
    TObjectPtr<UStaticMeshComponent> ArmLiftCarriageVisual;

private:
    UPROPERTY(VisibleInstanceOnly, SaveGame, Category = "Line Boss|MR01|Fault")
    ELBMaintenanceAMRFault ActiveMaintenanceFault = ELBMaintenanceAMRFault::None;

    UPROPERTY(VisibleInstanceOnly, SaveGame, Category = "Line Boss|MR01|Task")
    ELBMaintenanceTask ActiveMaintenanceTask = ELBMaintenanceTask::Inspection;

    UPROPERTY(VisibleInstanceOnly, SaveGame, Category = "Line Boss|MR01|Tool")
    ELBMaintenanceTool ActiveTool = ELBMaintenanceTool::None;

    UPROPERTY(VisibleInstanceOnly, SaveGame, Category = "Line Boss|MR01|Tool")
    TArray<ELBMaintenanceTool> ToolRackInventory;

    UPROPERTY(VisibleInstanceOnly, SaveGame, Category = "Line Boss|MR01|Arm")
    TArray<float> CurrentJointDegrees;

    UPROPERTY(VisibleInstanceOnly, SaveGame, Category = "Line Boss|MR01|Arm")
    float CurrentArmLiftMillimetres = 0.0f;

    UPROPERTY(VisibleInstanceOnly, SaveGame, Category = "Line Boss|MR01|Tool")
    bool bToolPresent = false;

    UPROPERTY(VisibleInstanceOnly, SaveGame, Category = "Line Boss|MR01|Tool")
    bool bToolLocked = false;

    UPROPERTY(VisibleInstanceOnly, SaveGame, Category = "Line Boss|MR01|Travel")
    bool bArmParked = true;

    UPROPERTY(VisibleInstanceOnly, SaveGame, Category = "Line Boss|MR01|Travel")
    bool bMastStowed = true;

    UPROPERTY(VisibleInstanceOnly, SaveGame, Category = "Line Boss|MR01|Mast")
    float MastExtensionMillimetres = 0.0f;

    UPROPERTY(VisibleInstanceOnly, SaveGame, Category = "Line Boss|MR01|Outriggers")
    bool bOutriggersDeployed = false;

    UPROPERTY(VisibleInstanceOnly, SaveGame, Category = "Line Boss|MR01|Outriggers")
    TArray<float> OutriggerFootLoadsKilograms;

    UPROPERTY(VisibleInstanceOnly, SaveGame, Category = "Line Boss|MR01|Travel")
    bool bDoorsClosed = true;

    UPROPERTY(VisibleInstanceOnly, SaveGame, Category = "Line Boss|MR01|Travel")
    bool bPartsDrawerClosed = true;

    UPROPERTY(VisibleInstanceOnly, SaveGame, Category = "Line Boss|MR01|Travel")
    bool bPayloadSecured = true;

    FName WorkPointId = NAME_None;
    FName ActivePermitId = NAME_None;
    FName LastCompletedPermitId = NAME_None;
    bool bMastTravelApproved = false;
    bool bAllOutriggersStowed = true;
    bool bParkingBrakeApplied = false;
    bool bExclusionZoneReserved = false;
    bool bOutsideSuspendedLoadZone = false;
    bool bTaskAuthorityValid = false;
    bool bCellPermissionGranted = false;
    bool bPlayerAuthorisationGranted = false;
    bool bLOTOValid = false;
    bool bTaskRequiresPhysicalLOTO = false;
    bool bArmMotionActive = false;
    bool bArmParkingCommand = false;
    float OutriggerDeploymentAlpha = 0.0f;
    TArray<float> TargetJointDegrees;
    float TargetArmLiftMillimetres = 0.0f;
    int32 ToolCarouselSlot = 1;
    int32 PendingToolRackSlot = INDEX_NONE;
    ELBMaintenanceTool PendingRequestedTool = ELBMaintenanceTool::None;

    USceneComponent* CreateContractPivot(const TCHAR* Name, USceneComponent* Parent, const FVector& RelativeLocation);
    USceneComponent* FindContractPivot(FName PivotName) const;
    ELBMaintenanceTool RequiredToolForTask(ELBMaintenanceTask Task) const;
    ELBSupportRobotState StateForTask(ELBMaintenanceTask Task) const;
    bool IsArmAtParkedPose() const;
    bool IsJointPoseValid(float LiftMillimetres, const TArray<float>& JointDegrees) const;
    bool AreFootLoadsProved(const TArray<float>& FootLoadsKilograms) const;
    void ApplyArmPose(float DeltaSeconds);
    void ApplyOutriggerPose(float DeltaSeconds);
    void ApplyMastPose();
    void AttachPresentationComponentsToContracts();
    void CachePresentationComponents();
    void ApplyPresentationPose();
    void ApplyToolVisualState();

    TMap<FName, FTransform> ArmReferenceComponentTransforms;
};
