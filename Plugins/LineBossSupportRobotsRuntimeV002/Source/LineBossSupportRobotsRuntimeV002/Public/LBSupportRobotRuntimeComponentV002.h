#pragma once

#include "CoreMinimal.h"
#include "Components/ActorComponent.h"
#include "LBSupportRobotAuthorityRegistryV002.h"
#include "LBSupportRobotRuntimeComponentV002.generated.h"

class USceneComponent;

DECLARE_DYNAMIC_MULTICAST_DELEGATE_TwoParams(FLBSupportRobotStateChangedV002,
    ELBSupportRobotOperatingStateV002, PreviousState,
    ELBSupportRobotOperatingStateV002, NewState);
DECLARE_DYNAMIC_MULTICAST_DELEGATE_TwoParams(FLBSupportRobotFaultChangedV002,
    ELBSupportRobotCommonFaultV002, PreviousFault,
    ELBSupportRobotCommonFaultV002, NewFault);

/**
 * Geometry-free, authority-first RP01 runtime controller.
 *
 * This component may attach to APawn or AActor. It never creates/replaces a
 * root, collision or mesh component. Pack anchors are resolved by canonical
 * component name (including Blueprint's _GEN_VARIABLE suffix) or
 * LB.Anchor.<name> / LBAnchor:<name> component tag.
 */
UCLASS(BlueprintType, ClassGroup = (LineBoss), meta = (BlueprintSpawnableComponent))
class LINEBOSSSUPPORTROBOTSRUNTIMEV002_API ULBSupportRobotRuntimeComponentV002 : public UActorComponent
{
    GENERATED_BODY()

public:
    ULBSupportRobotRuntimeComponentV002();

    virtual void BeginPlay() override;
    virtual void EndPlay(const EEndPlayReason::Type EndPlayReason) override;
    virtual void TickComponent(float DeltaTime, ELevelTick TickType,
        FActorComponentTickFunction* ThisTickFunction) override;

    UFUNCTION(BlueprintCallable, Category = "Line Boss|Support Robots v002|Identity")
    bool ConfigureIdentity(FName NewUnitId, FName NewVariantId);

    UFUNCTION(BlueprintCallable, Category = "Line Boss|Support Robots v002|Anchors")
    bool ResolveAndValidateAnchors();

    UFUNCTION(BlueprintPure, Category = "Line Boss|Support Robots v002|Anchors")
    USceneComponent* GetResolvedAnchor(FName CanonicalAnchorName) const;

    UFUNCTION(BlueprintPure, Category = "Line Boss|Support Robots v002|Anchors")
    bool IsAnchorContractValid() const { return bAnchorContractValid; }

    UFUNCTION(BlueprintPure, Category = "Line Boss|Support Robots v002|Anchors")
    TArray<FName> GetMissingOrInvalidAnchors() const { return MissingOrInvalidAnchors; }

    UFUNCTION(BlueprintCallable, Category = "Line Boss|Support Robots v002|Commissioning")
    bool BeginInspection(FName EvidenceId);

    UFUNCTION(BlueprintCallable, Category = "Line Boss|Support Robots v002|Commissioning")
    bool RecordRepairRequired(FName EvidenceId);

    UFUNCTION(BlueprintCallable, Category = "Line Boss|Support Robots v002|Commissioning")
    bool MarkReadyForTest(FName EvidenceId);

    UFUNCTION(BlueprintCallable, Category = "Line Boss|Support Robots v002|Commissioning")
    bool BeginManualCommissioning(FName EvidenceId);

    UFUNCTION(BlueprintCallable, Category = "Line Boss|Support Robots v002|Commissioning")
    bool CompleteManualCommissioning(FName EvidenceId);

    UFUNCTION(BlueprintCallable, Category = "Line Boss|Support Robots v002|Commissioning")
    bool BeginCalibration(FName EvidenceId);

    UFUNCTION(BlueprintCallable, Category = "Line Boss|Support Robots v002|Commissioning")
    bool CompleteCalibration(FName EvidenceId);

    UFUNCTION(BlueprintCallable, Category = "Line Boss|Support Robots v002|Commissioning")
    bool BeginRouteValidation(FName EvidenceId);

    UFUNCTION(BlueprintCallable, Category = "Line Boss|Support Robots v002|Commissioning")
    bool CertifyRobot(FName FinalApprovalEvidenceId);

    UFUNCTION(BlueprintCallable, Category = "Line Boss|Support Robots v002|Route")
    bool AcknowledgeStoppedRouteRevalidation(FName EvidenceId);

    UFUNCTION(BlueprintCallable, Category = "Line Boss|Support Robots v002|Route")
    bool RequestCertifiedRoute(const FLBRouteRequestV002& Request);

    UFUNCTION(BlueprintCallable, Category = "Line Boss|Support Robots v002|Route")
    void AbortRouteAndStop();

    UFUNCTION(BlueprintCallable, Category = "Line Boss|Support Robots v002|Dock")
    bool RequestPhysicalDockProof(FName DockId);

    UFUNCTION(BlueprintCallable, Category = "Line Boss|Support Robots v002|Dock")
    bool ReleasePhysicalDockProof();

    /** Trusted native service result; zero health remains valid data but inhibits operation. */
    bool ApplyTrustedBatteryServiceResult(double NewStateOfChargePercent,
        double NewHealthPercent, FName ServiceEvidenceId);

    UFUNCTION(BlueprintCallable, Category = "Line Boss|Support Robots v002|Fault")
    bool RequestFaultClear(FName ClearanceEvidenceId);

    UFUNCTION(BlueprintPure, Category = "Line Boss|Support Robots v002|Save")
    FLBSupportRobotSafeSaveV002 CaptureSafeSaveState() const;

    /** Native save-coordinator boundary; Blueprint cannot apply a fabricated DTO. */
    bool RestoreSafeStopped(const FLBSupportRobotSafeSaveV002& SavedState);

    UFUNCTION(BlueprintPure, Category = "Line Boss|Support Robots v002|State")
    ELBSupportRobotCommissioningStateV002 GetCommissioningState() const { return CommissioningState; }

    UFUNCTION(BlueprintPure, Category = "Line Boss|Support Robots v002|State")
    ELBSupportRobotOperatingStateV002 GetOperatingState() const { return OperatingState; }

    UFUNCTION(BlueprintPure, Category = "Line Boss|Support Robots v002|State")
    ELBSupportRobotCommonFaultV002 GetActiveCommonFault() const { return ActiveCommonFault; }

    UFUNCTION(BlueprintPure, Category = "Line Boss|Support Robots v002|State")
    bool HasTrustedRouteGrant() const { return ActiveRouteGrant.IsStructurallyValid(); }

    UFUNCTION(BlueprintPure, Category = "Line Boss|Support Robots v002|State")
    bool HasTrustedDockProof() const { return ActiveDockProof.IsComplete(); }

    UFUNCTION(BlueprintPure, Category = "Line Boss|Support Robots v002|Battery")
    double GetBatteryStateOfChargePercent() const { return BatteryStateOfChargePercent; }

    UFUNCTION(BlueprintPure, Category = "Line Boss|Support Robots v002|Battery")
    double GetBatteryHealthPercent() const { return BatteryHealthPercent; }

    UPROPERTY(BlueprintAssignable, Category = "Line Boss|Support Robots v002|Events")
    FLBSupportRobotStateChangedV002 OnOperatingStateChanged;

    UPROPERTY(BlueprintAssignable, Category = "Line Boss|Support Robots v002|Events")
    FLBSupportRobotFaultChangedV002 OnCommonFaultChanged;

    /** Native integration boundary; reporting a fault can only reduce authority. */
    void RaiseCommonFault(ELBSupportRobotCommonFaultV002 Fault, const FString& Detail);

protected:
    UPROPERTY(EditInstanceOnly, BlueprintReadOnly, Category = "Line Boss|Support Robots v002|Identity")
    FName UnitId = NAME_None;

    UPROPERTY(VisibleInstanceOnly, BlueprintReadOnly, Category = "Line Boss|Support Robots v002|Identity")
    FName VariantId = TEXT("LB-RP01");

    UPROPERTY(VisibleInstanceOnly, BlueprintReadOnly, SaveGame, Category = "Line Boss|Support Robots v002|State")
    ELBSupportRobotCommissioningStateV002 CommissioningState = ELBSupportRobotCommissioningStateV002::Mothballed;

    UPROPERTY(VisibleInstanceOnly, BlueprintReadOnly, SaveGame, Category = "Line Boss|Support Robots v002|State")
    ELBSupportRobotConditionV002 Condition = ELBSupportRobotConditionV002::Mothballed;

    UPROPERTY(VisibleInstanceOnly, BlueprintReadOnly, Category = "Line Boss|Support Robots v002|State")
    ELBSupportRobotOperatingStateV002 OperatingState = ELBSupportRobotOperatingStateV002::Stopped;

    UPROPERTY(VisibleInstanceOnly, BlueprintReadOnly, Category = "Line Boss|Support Robots v002|Fault")
    ELBSupportRobotCommonFaultV002 ActiveCommonFault = ELBSupportRobotCommonFaultV002::None;

    UPROPERTY(EditInstanceOnly, BlueprintReadOnly, SaveGame, Category = "Line Boss|Support Robots v002|Battery",
        meta = (ClampMin = "0.0", ClampMax = "100.0"))
    double BatteryStateOfChargePercent = 0.0;

    UPROPERTY(EditInstanceOnly, BlueprintReadOnly, SaveGame, Category = "Line Boss|Support Robots v002|Battery",
        meta = (ClampMin = "0.0", ClampMax = "100.0"))
    double BatteryHealthPercent = 0.0;

    UPROPERTY(VisibleInstanceOnly, BlueprintReadOnly, SaveGame, Category = "Line Boss|Support Robots v002|Counters")
    double OperatingHours = 0.0;

    UPROPERTY(VisibleInstanceOnly, BlueprintReadOnly, SaveGame, Category = "Line Boss|Support Robots v002|Counters")
    int32 MissionCount = 0;

    UPROPERTY(VisibleInstanceOnly, BlueprintReadOnly, SaveGame, Category = "Line Boss|Support Robots v002|Counters")
    int32 ServiceCycles = 0;

    UPROPERTY(VisibleInstanceOnly, BlueprintReadOnly, Category = "Line Boss|Support Robots v002|Route")
    bool bRouteRevalidationRequired = true;

    UPROPERTY(VisibleInstanceOnly, BlueprintReadOnly, Category = "Line Boss|Support Robots v002|Task")
    FName ActiveTaskId = NAME_None;

    virtual void AppendAnchorContract(TArray<FLBAnchorSpecV002>& InOutSpecs) const;
    virtual FName GetExpectedVariantIdV002() const;
    virtual bool RequiresCalibration() const { return false; }
    virtual bool ValidateVariantForCertification(FString& OutFailure) const;
    virtual bool ValidateVariantTravelPermissives(FString& OutFailure) const;
    virtual bool RefreshVariantDynamicInterlocksV002(FString& OutFailure);
    virtual void TickVariantProcessV002(double DeltaSeconds) {}
    virtual void OnSafeStopV002();
    virtual void OnRouteFinishedSafelyV002();
    virtual void OnSafeStoppedRestoreV002();
    virtual FName GetActiveVariantFaultIdV002() const { return NAME_None; }
    virtual bool CanCommitVariantFaultClearV002(FString& OutFailure) const;
    virtual void CommitVariantFaultClearV002();
    virtual double GetMaximumSpeedCentimetresPerSecondV002(ELBRouteSpeedClassV002 SpeedClass,
        bool bEmergencyDispatch) const;
    virtual double GetAccelerationCentimetresPerSecondSquaredV002(
        ELBRouteSpeedClassV002 SpeedClass, bool bEmergencyDispatch) const;

    ULBSupportRobotAuthorityRegistryV002* GetAuthorityRegistry() const;
    bool ValidateTrustedCommissioningEvidence(FName StageId, FName EvidenceId) const;
    bool RevalidateActiveDockProofV002(FString& OutFailure) const;
    bool IsCertifiedForOperationV002() const;
    bool HasOperationalBatteryReserveV002() const;
    void SetOperatingState(ELBSupportRobotOperatingStateV002 NewState);
    void ClearAllTransientAuthorityV002();
    double GetCurrentCommandedSpeedCentimetresPerSecondV002() const
    {
        return CurrentCommandedSpeedCentimetresPerSecond;
    }

private:
    UPROPERTY(VisibleInstanceOnly, Category = "Line Boss|Support Robots v002|Anchors")
    bool bAnchorContractValid = false;

    UPROPERTY(VisibleInstanceOnly, Category = "Line Boss|Support Robots v002|Anchors")
    TArray<FName> MissingOrInvalidAnchors;

    TMap<FName, TWeakObjectPtr<USceneComponent>> ResolvedAnchors;
    FLBTrustedRouteGrantV002 ActiveRouteGrant;
    FLBTrustedDockProofV002 ActiveDockProof;
    FName PendingDockId = NAME_None;
    bool bManualCommissioningComplete = false;
    bool bCalibrationComplete = false;
    bool bCommissioningCertified = false;
    double CurrentCommandedSpeedCentimetresPerSecond = 0.0;

    static constexpr double LowBatteryThresholdPercent = 15.0;
    static constexpr double TransitDrainPercentPerMetre = 0.015;
    static constexpr double ChargingRatePercentPerSecond = 0.20;
    static constexpr double AnchorPositionToleranceCentimetres = 0.20;
    static constexpr double AnchorRotationToleranceDegrees = 0.25;
    static constexpr double AnchorScaleTolerance = 0.001;

    USceneComponent* FindUniqueAnchorComponent(FName CanonicalName, bool& bOutDuplicate) const;
    bool ValidateDynamicRouteSafety(const FLBRouteSafetySnapshotV002& Safety,
        ELBSupportRobotCommonFaultV002& OutFault, FString& OutFailure) const;
    ELBRouteSpeedClassV002 GetEffectiveSpeedClass(const FLBRouteSafetySnapshotV002& Safety) const;
    void TickTrustedRoute(double DeltaSeconds);
    void TickTrustedDock(double DeltaSeconds);
    void CompleteTrustedRoute();
};
