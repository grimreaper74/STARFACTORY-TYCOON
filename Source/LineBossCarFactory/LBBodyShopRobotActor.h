#pragma once

#include "CoreMinimal.h"
#include "GameFramework/Actor.h"
#include "LBBodyShopTypes.h"
#include "LBBodyShopRobotActor.generated.h"

class USceneComponent;
class UStaticMesh;
class UStaticMeshComponent;

/**
 * Articulated presentation for one robot assigned to one fixture-owned slot.
 * It consumes only authored mount transforms and bounded process poses.
 */
UCLASS(BlueprintType)
class LINEBOSSCARFACTORY_API ALBBodyShopRobotActor : public AActor
{
    GENERATED_BODY()

public:
    ALBBodyShopRobotActor();

    virtual void Tick(float DeltaSeconds) override;

    /** Script-exposed so editor placement tooling can commission saved robots. */
    UFUNCTION(BlueprintCallable, Category="Line Boss|Body Shop|Robot")
    bool ConfigureForAuthoredSlot(const FName InCellId,
        const FLBBodyShopRobotSlotDefinition& InSlot,
        const FLBBodyShopRobotAssignment& InAssignment, FString& OutReason);

    UFUNCTION(BlueprintCallable, Category="Line Boss|Body Shop|Robot")
    void SetAuthoredPose(ELBBodyShopRobotPose InPose, bool bInstant = false);

    UFUNCTION(BlueprintPure, Category="Line Boss|Body Shop|Robot")
    bool HasCompleteArtPresentation() const { return bCompleteArtPresentation; }

    UFUNCTION(BlueprintPure, Category="Line Boss|Body Shop|Robot")
    bool IsConfiguredForAuthoredSlot() const { return bConfigured; }

    UFUNCTION(BlueprintPure, Category="Line Boss|Body Shop|Robot")
    FName GetOwningCellId() const { return OwningCellId; }

    UFUNCTION(BlueprintPure, Category="Line Boss|Body Shop|Robot")
    FName GetSlotId() const { return SlotId; }

    UFUNCTION(BlueprintPure, Category="Line Boss|Body Shop|Robot")
    ELBBodyShopRobotPose GetCurrentPose() const { return CurrentPose; }

    UFUNCTION(BlueprintPure, Category="Line Boss|Body Shop|Robot")
    ELBBodyShopRobotPose GetTargetPose() const { return TargetPose; }

    /** Pauses only authored joint interpolation/work-point cycling; pose commands remain valid. */
    UFUNCTION(BlueprintCallable, Category="Line Boss|Body Shop|Robot")
    void SetArticulationRunning(bool bInRunning) { bArticulationRunning = bInRunning; }

    UFUNCTION(BlueprintPure, Category="Line Boss|Body Shop|Robot")
    bool IsArticulationRunning() const { return bArticulationRunning; }

    UFUNCTION(BlueprintPure, Category="Line Boss|Body Shop|Robot")
    float GetJointAngleDegrees(int32 JointIndex) const;

    /** Six-axis source order is J1..J6; legacy indices 0..4 retain their joint names. */
    static int32 GetAuthoredJointCount();

    /** Active authored weld-work point while Process is cycling; INDEX_NONE outside weld work. */
    UFUNCTION(BlueprintPure, Category="Line Boss|Body Shop|Robot")
    int32 GetCurrentWeldWorkPoseIndex() const { return WeldWorkPoseIndex; }

    /** Frozen native C-gun contact datum; still presentation-only until imported-socket validation. */
    UFUNCTION(BlueprintPure, Category="Line Boss|Body Shop|Robot")
    FVector GetWeldGunPresentationTipLocation() const;

    UFUNCTION(BlueprintPure, Category="Line Boss|Body Shop|Robot")
    FVector GetWeldGunPresentationApproachDirection() const;

    UFUNCTION(BlueprintPure, Category="Line Boss|Body Shop|Robot")
    int32 GetVacuumContactSocketCount() const;

    UFUNCTION(BlueprintPure, Category="Line Boss|Body Shop|Robot")
    FVector GetVacuumContactSocketLocation(int32 SocketIndex) const;

    static bool GetAuthoredJointLimits(int32 JointIndex, float& OutMinimumDegrees,
        float& OutMaximumDegrees);
    static bool GetAuthoredPoseAngles(ELBBodyShopRobotPose Pose,
        ELBBodyShopRobotRole RobotRole, TArray<float>& OutJointAngles);
    static bool GetAuthoredPoseAnglesForSlot(ELBBodyShopRobotPose Pose,
        ELBBodyShopRobotRole RobotRole, FName AuthoredSlotId,
        TArray<float>& OutJointAngles);

    /** Three bounded spot-weld work points used while the runtime requests Process. */
    static int32 GetAuthoredWeldWorkPoseCount();
    static bool GetAuthoredWeldWorkPoseAngles(int32 WorkPoseIndex,
        FName AuthoredSlotId, TArray<float>& OutJointAngles);

    /**
     * Computes the frozen native-v001 process contact in fixture-local space. The candidate
     * remains presentation-only until real imported sockets and swept collision are verified.
     */
    static bool GetAuthoredWeldContactCandidate(int32 WorkPoseIndex,
        FName AuthoredSlotId, FVector& OutGunTipFixtureLocal,
        FVector& OutFixtureTargetLocal, FVector& OutGunApproachFixtureLocal);
    static bool IsAuthoredWeldContactCandidateCredible(int32 WorkPoseIndex,
        FName AuthoredSlotId, float& OutTipToTargetDistanceCm,
        float& OutApproachToTargetDot);

    /** Exact frozen pivot offsets, expressed in the owning parent component's centimetres. */
    static bool GetAuthoredJointPivotRelativeLocation(int32 JointIndex,
        FVector& OutPivotParentCm);

    /** Shoulder/J3 elbow/J4 wrist points for one frozen Process work pose. */
    static bool GetAuthoredWeldWorkPoseKinematics(int32 WorkPoseIndex,
        FName AuthoredSlotId, FVector& OutShoulderFixtureLocal,
        FVector& OutElbowFixtureLocal, FVector& OutWristFixtureLocal);

    static FVector GetAuthoredWeldContactSocketRelativeLocation();

    /** Frozen analytical preflight only; these values are not Unreal collision evidence. */
    static void GetAuthoredAnalyticalClearanceEvidence(float& OutMinimumWipClearanceCm,
        float& OutMinimumFloorClearanceCm, float& OutMinimumOuterFenceClearanceCm,
        float& OutMinimumPairedRobotClearanceCm);

    /** Native source flange/adapter rest transforms are identity; J1..J6 carry orientation. */
    static FTransform GetAuthoredToolFlangeRelativeTransform();
    static FTransform GetAuthoredToolAdapterRelativeTransform(
        ELBBodyShopRobotRole RobotRole, FName AuthoredSlotId);

    /** Local-space rotation contract used by the articulated scene-component pivots. */
    static FRotator GetAuthoredJointRelativeRotation(int32 JointIndex,
        float JointAngleDegrees);

private:
    UPROPERTY(VisibleAnywhere) TObjectPtr<USceneComponent> SceneRoot;
    UPROPERTY(VisibleAnywhere) TObjectPtr<USceneComponent> J1Pivot;
    UPROPERTY(VisibleAnywhere) TObjectPtr<USceneComponent> J2Pivot;
    UPROPERTY(VisibleAnywhere) TObjectPtr<USceneComponent> J3Pivot;
    UPROPERTY(VisibleAnywhere) TObjectPtr<USceneComponent> J4Pivot;
    UPROPERTY(VisibleAnywhere) TObjectPtr<USceneComponent> J5Pivot;
    UPROPERTY(VisibleAnywhere) TObjectPtr<USceneComponent> J6Pivot;
    UPROPERTY(VisibleAnywhere) TObjectPtr<USceneComponent> ToolFlange;
    UPROPERTY(VisibleAnywhere) TObjectPtr<USceneComponent> ToolAdapter;
    UPROPERTY(VisibleAnywhere) TObjectPtr<UStaticMeshComponent> BasePresentation;
    UPROPERTY(VisibleAnywhere) TObjectPtr<UStaticMeshComponent> J1Presentation;
    UPROPERTY(VisibleAnywhere) TObjectPtr<UStaticMeshComponent> J2Presentation;
    UPROPERTY(VisibleAnywhere) TObjectPtr<UStaticMeshComponent> J3Presentation;
    UPROPERTY(VisibleAnywhere) TObjectPtr<UStaticMeshComponent> J4Presentation;
    UPROPERTY(VisibleAnywhere) TObjectPtr<UStaticMeshComponent> J5Presentation;
    UPROPERTY(VisibleAnywhere) TObjectPtr<UStaticMeshComponent> J6Presentation;
    UPROPERTY(VisibleAnywhere) TObjectPtr<UStaticMeshComponent> ToolPresentation;

    UPROPERTY(VisibleInstanceOnly) FName OwningCellId = NAME_None;
    UPROPERTY(VisibleInstanceOnly) FName SlotId = NAME_None;
    UPROPERTY(VisibleInstanceOnly) ELBBodyShopRobotRole RobotRole = ELBBodyShopRobotRole::None;
    UPROPERTY(VisibleInstanceOnly) ELBBodyShopToolType ToolType = ELBBodyShopToolType::None;
    UPROPERTY(VisibleInstanceOnly) ELBBodyShopRobotPose CurrentPose = ELBBodyShopRobotPose::Home;
    UPROPERTY(VisibleInstanceOnly) ELBBodyShopRobotPose TargetPose = ELBBodyShopRobotPose::Home;
    UPROPERTY(VisibleInstanceOnly) bool bConfigured = false;
    UPROPERTY(VisibleInstanceOnly) bool bCompleteArtPresentation = false;
    UPROPERTY(VisibleInstanceOnly) bool bArticulationRunning = true;
    UPROPERTY(VisibleInstanceOnly) TArray<float> CurrentJointAngles;
    UPROPERTY(VisibleInstanceOnly) TArray<float> TargetJointAngles;
    UPROPERTY(VisibleInstanceOnly) int32 WeldWorkPoseIndex = INDEX_NONE;
    UPROPERTY(VisibleInstanceOnly) float WeldWorkPoseHoldSeconds = 0.0f;

    UPROPERTY() TSoftObjectPtr<UStaticMesh> BaseMesh;
    UPROPERTY() TSoftObjectPtr<UStaticMesh> J1Mesh;
    UPROPERTY() TSoftObjectPtr<UStaticMesh> J2Mesh;
    UPROPERTY() TSoftObjectPtr<UStaticMesh> J3Mesh;
    UPROPERTY() TSoftObjectPtr<UStaticMesh> J4Mesh;
    UPROPERTY() TSoftObjectPtr<UStaticMesh> J5Mesh;
    UPROPERTY() TSoftObjectPtr<UStaticMesh> J6Mesh;
    UPROPERTY() TSoftObjectPtr<UStaticMesh> PanelPick8CupToolMesh;
    UPROPERTY() TSoftObjectPtr<UStaticMesh> SpotCGunToolMesh;
    void ConfigureHierarchy();
    bool LoadCompleteArt(ELBBodyShopToolType InTool, FString& OutReason);
    void ApplyJointTransforms();
    void AdvanceWeldWorkPose();
    void SetPresentationSafety(UStaticMeshComponent* Component) const;
};
