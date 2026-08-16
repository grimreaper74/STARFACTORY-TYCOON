#pragma once

#include "CoreMinimal.h"
#include "GameFramework/Actor.h"
#include "LBMachineLiveryComponent.h"
#include "LBCompactStillageFLT.generated.h"

class UBoxComponent;
class USceneComponent;
class USpotLightComponent;
class UStaticMeshComponent;
class ULBStatusBeaconComponent;
class UMaterialInterface;
class UMeshComponent;

UENUM(BlueprintType)
enum class ELBStillageFLTJobType : uint8
{
    FullStillageToWeld,
    EmptyStillageToPress
};

UENUM(BlueprintType)
enum class ELBStillageFLTJobState : uint8
{
    Pending,
    Claimed,
    DeliveredReturning,
    Completed,
    Failed
};

USTRUCT(BlueprintType)
struct FLBStillageFLTJob
{
    GENERATED_BODY()

    UPROPERTY(EditAnywhere, BlueprintReadWrite, SaveGame) int32 Version = 1;
    UPROPERTY(EditAnywhere, BlueprintReadWrite, SaveGame) FName JobId = NAME_None;
    UPROPERTY(EditAnywhere, BlueprintReadWrite, SaveGame) FName StillageId = NAME_None;
    UPROPERTY(EditAnywhere, BlueprintReadWrite, SaveGame) ELBStillageFLTJobType JobType = ELBStillageFLTJobType::FullStillageToWeld;
    UPROPERTY(EditAnywhere, BlueprintReadWrite, SaveGame) FName SourceAuthorityId = NAME_None;
    UPROPERTY(EditAnywhere, BlueprintReadWrite, SaveGame) FName TargetAuthorityId = NAME_None;
    /** Authored floor pad/corner-locator identity at the destination. Never inferred at delivery time. */
    UPROPERTY(EditAnywhere, BlueprintReadWrite, SaveGame) FName TargetStackPadId = NAME_None;
    /** Common full/empty stillage stack contract: 1=floor, 2=1.50 m, 3=2.90 m. */
    UPROPERTY(EditAnywhere, BlueprintReadWrite, SaveGame) int32 TargetStackTier = 1;
    /** Required vehicle yaw at the pad so all four stillage corner locators register. */
    UPROPERTY(EditAnywhere, BlueprintReadWrite, SaveGame) float TargetStackPadYawDegrees = 0.0f;
    /** FLT service point outside the source storage protected envelope. Z is normalised to vehicle-root height. */
    UPROPERTY(EditAnywhere, BlueprintReadWrite, SaveGame) FVector PickupServicePoint = FVector::ZeroVector;
    /** FLT service point outside the destination storage protected envelope. Z is normalised to vehicle-root height. */
    UPROPERTY(EditAnywhere, BlueprintReadWrite, SaveGame) FVector DropoffServicePoint = FVector::ZeroVector;
    /** Load footprint in vehicle local X/Y. The default covers the approved large Cairnwell stillage. */
    UPROPERTY(EditAnywhere, BlueprintReadWrite, SaveGame) FVector2D StillageHalfExtentCm = FVector2D(85.0f, 155.0f);
    UPROPERTY(EditAnywhere, BlueprintReadWrite, SaveGame) ELBStillageFLTJobState State = ELBStillageFLTJobState::Pending;
    UPROPERTY(EditAnywhere, BlueprintReadWrite, SaveGame) FName ClaimedUnitId = NAME_None;
    UPROPERTY(EditAnywhere, BlueprintReadWrite, SaveGame) int64 CreatedSequence = 0;
};

UENUM(BlueprintType)
enum class ELBCompactStillageFLTPhase : uint8
{
    Parked,
    TravelToPickup,
    PickupDockProving,
    RaisingLoad,
    TravelToDropoff,
    DropoffDockProving,
    RaisingToStackTier,
    StackLocatorProving,
    LoweringLoad,
    ReturningToBerth,
    Fault
};

UENUM(BlueprintType)
enum class ELBCompactStillageFLTFault : uint8
{
    None,
    InvalidIdentity,
    InvalidJob,
    RouteUnavailable,
    RouteCollision,
    RaisedMastTravelProhibited,
    StackLocatorMisaligned,
    RestoreRejected
};

USTRUCT(BlueprintType)
struct FLBCompactStillageFLTSaveState
{
    GENERATED_BODY()

    UPROPERTY(EditAnywhere, BlueprintReadWrite, SaveGame) int32 Version = 1;
    UPROPERTY(EditAnywhere, BlueprintReadWrite, SaveGame) FName UnitId = NAME_None;
    UPROPERTY(EditAnywhere, BlueprintReadWrite, SaveGame) ELBCompactStillageFLTPhase Phase = ELBCompactStillageFLTPhase::Parked;
    UPROPERTY(EditAnywhere, BlueprintReadWrite, SaveGame) ELBCompactStillageFLTFault Fault = ELBCompactStillageFLTFault::None;
    UPROPERTY(EditAnywhere, BlueprintReadWrite, SaveGame) FTransform VehicleTransform = FTransform::Identity;
    UPROPERTY(EditAnywhere, BlueprintReadWrite, SaveGame) FVector HomeBerth = FVector::ZeroVector;
    UPROPERTY(EditAnywhere, BlueprintReadWrite, SaveGame) float CurrentSpeedCmPerSecond = 0.0f;
    UPROPERTY(EditAnywhere, BlueprintReadWrite, SaveGame) float CarriageLiftCm = 0.0f;
    UPROPERTY(EditAnywhere, BlueprintReadWrite, SaveGame) float RearSteerAngleDegrees = 0.0f;
    UPROPERTY(EditAnywhere, BlueprintReadWrite, SaveGame) bool bCarryingStillage = false;
    UPROPERTY(EditAnywhere, BlueprintReadWrite, SaveGame) bool bCarriedStillageFull = false;
    UPROPERTY(EditAnywhere, BlueprintReadWrite, SaveGame) FName CarriedStillageId = NAME_None;
    UPROPERTY(EditAnywhere, BlueprintReadWrite, SaveGame) FName ActiveJobId = NAME_None;
    UPROPERTY(EditAnywhere, BlueprintReadWrite, SaveGame) bool bDeliveryEventEmitted = false;
};

DECLARE_DYNAMIC_MULTICAST_DELEGATE_FourParams(FOnLBStillageFLTDelivered,
    FName, UnitId, FName, JobId, FName, StillageId, bool, bStillageWasFull);
DECLARE_DYNAMIC_MULTICAST_DELEGATE_ThreeParams(FOnLBStillageFLTJobFinished,
    FName, UnitId, FName, JobId, bool, bSucceeded);

/**
 * Compact autonomous forklift used for press-WIP stillage logistics.
 *
 * The actor deliberately owns gameplay collision, steering, mast articulation,
 * work lights and status beacon independently of the approved Meshy v003 body.
 * A content Blueprint may replace the fallback meshes while retaining these
 * stable component roots:
 *   PIVOT_MAST_TILT_Y, MOVER_MAST_INNER_STAGE_Z,
 *   MOVER_MAST_SECOND_STAGE_Z, MOVER_CARRIAGE_Z, MOVER_LIFT_ROD_Z,
 *   ADJUSTER_FORK_LEFT_Y and ADJUSTER_FORK_RIGHT_Y.
 */
UCLASS(BlueprintType, Blueprintable)
class LINEBOSSCARFACTORY_API ALBCompactStillageFLT : public AActor
{
    GENERATED_BODY()

public:
    static constexpr int32 MaximumSupportedStackTier = 3;
    static constexpr float MaximumSupportedForkPlacementHeightCm = 290.0f;
    static constexpr float MaximumSupportedRearSteerAngleDegrees = 38.0f;
    static constexpr float MaximumPermittedTravelLiftCm = 12.0f;

    ALBCompactStillageFLT();
    virtual void BeginPlay() override;
    virtual void Tick(float DeltaSeconds) override;

    UFUNCTION(BlueprintCallable, Category="Line Boss|Stillage FLT|Commissioning")
    bool ConfigureUnit(FName InUnitId, FVector InHomeBerth);

    UFUNCTION(BlueprintCallable, Category="Line Boss|Stillage FLT|Job")
    bool StartJob(const FLBStillageFLTJob& Job);

    /** Replans disposable paths after the fleet controller has restored the matching claimed job. */
    bool ResumeAssignedJob(const FLBStillageFLTJob& Job);

    UFUNCTION(BlueprintCallable, Category="Line Boss|Stillage FLT|Fault")
    bool ResetFault();

    UFUNCTION(BlueprintPure, Category="Line Boss|Stillage FLT|State")
    bool IsAvailableForJob() const { return Phase == ELBCompactStillageFLTPhase::Parked && ActiveJobId.IsNone(); }
    UFUNCTION(BlueprintPure, Category="Line Boss|Stillage FLT|State")
    bool IsWaitingForTraffic() const { return bWaitingForTraffic; }
    UFUNCTION(BlueprintPure, Category="Line Boss|Stillage FLT|State")
    FName GetUnitId() const { return UnitId; }
    UFUNCTION(BlueprintPure, Category="Line Boss|Stillage FLT|State")
    FName GetActiveJobId() const { return ActiveJobId; }
    UFUNCTION(BlueprintPure, Category="Line Boss|Stillage FLT|State")
    ELBCompactStillageFLTPhase GetPhase() const { return Phase; }
    UFUNCTION(BlueprintPure, Category="Line Boss|Stillage FLT|State")
    ELBCompactStillageFLTFault GetFault() const { return ActiveFault; }
    UFUNCTION(BlueprintPure, Category="Line Boss|Stillage FLT|State")
    float GetCurrentSpeedMetresPerSecond() const { return CurrentSpeedCmPerSecond / 100.0f; }
    UFUNCTION(BlueprintPure, Category="Line Boss|Stillage FLT|State")
    float GetCarriageLiftCm() const { return CarriageLiftCm; }
    UFUNCTION(BlueprintPure, Category="Line Boss|Stillage FLT|State")
    bool IsCarryingStillage() const { return bCarryingStillage; }
    UFUNCTION(BlueprintPure, Category="Line Boss|Stillage FLT|State")
    bool IsCarryingFullStillage() const { return bCarryingStillage && bCarriedStillageFull; }
    UFUNCTION(BlueprintPure, Category="Line Boss|Stillage FLT|Route")
    int32 GetRuntimeRoutePointCount() const { return RuntimePath.Num(); }

    UFUNCTION(BlueprintCallable, Category="Line Boss|Stillage FLT|Save")
    bool CaptureSaveState(FLBCompactStillageFLTSaveState& OutState) const;
    UFUNCTION(BlueprintCallable, Category="Line Boss|Stillage FLT|Save")
    bool RestoreSaveState(const FLBCompactStillageFLTSaveState& InState);

    UPROPERTY(BlueprintAssignable, Category="Line Boss|Stillage FLT|Events")
    FOnLBStillageFLTDelivered OnStillageDelivered;
    UPROPERTY(BlueprintAssignable, Category="Line Boss|Stillage FLT|Events")
    FOnLBStillageFLTJobFinished OnJobFinished;

    UFUNCTION(BlueprintPure, Category="Line Boss|Stillage FLT|Presentation")
    ULBStatusBeaconComponent* GetStatusBeacon() const { return StatusBeacon; }
    UFUNCTION(BlueprintPure, Category="Line Boss|Stillage FLT|Presentation")
    ULBMachineLiveryComponent* GetMachineLiveryComponent() const { return MachineLivery; }
    UFUNCTION(BlueprintPure, Category="Line Boss|Stillage FLT|Collision")
    UBoxComponent* GetCollisionRoot() const { return CollisionRoot; }
    UFUNCTION(BlueprintPure, Category="Line Boss|Stillage FLT|Presentation")
    USceneComponent* GetMastTiltRoot() const { return MastTiltRoot; }
    UFUNCTION(BlueprintPure, Category="Line Boss|Stillage FLT|Presentation")
    USceneComponent* GetInnerMastMover() const { return InnerMastMover; }
    UFUNCTION(BlueprintPure, Category="Line Boss|Stillage FLT|Presentation")
    USceneComponent* GetSecondMastMover() const { return SecondMastMover; }
    UFUNCTION(BlueprintPure, Category="Line Boss|Stillage FLT|Presentation")
    USceneComponent* GetCarriageMover() const { return CarriageMover; }
    UFUNCTION(BlueprintPure, Category="Line Boss|Stillage FLT|Presentation")
    USceneComponent* GetLiftRodMover() const { return LiftRodMover; }
    UFUNCTION(BlueprintPure, Category="Line Boss|Stillage FLT|Steering")
    USceneComponent* GetRearSteeringPivot() const { return RearSteeringPivot; }
    UFUNCTION(BlueprintPure, Category="Line Boss|Stillage FLT|Steering")
    float GetRearSteerAngleDegrees() const { return CurrentRearSteerAngleDegrees; }
    /** Front drive wheels are fixed; all directional control is at the rear axle. */
    UFUNCTION(BlueprintPure, Category="Line Boss|Stillage FLT|Steering")
    float GetFrontWheelSteerAngleDegrees() const { return 0.0f; }
    UFUNCTION(BlueprintPure, Category="Line Boss|Stillage FLT|Steering")
    float GetOutwardSweepAllowanceCm() const;
    /**
     * Conservative clearance used by the shared route planner while carrying the
     * supplied stillage footprint. This includes the rear-steer swept envelope,
     * protected-envelope margin and the planner's corner-rounding allowance.
     */
    UFUNCTION(BlueprintPure, Category="Line Boss|Stillage FLT|Safety")
    float GetRequiredServicePointStandOffCm(FVector2D StillageHalfExtentCm) const;
    /** Signed speed makes the commanded rear steer reverse correctly while backing. */
    UFUNCTION(BlueprintPure, Category="Line Boss|Stillage FLT|Steering")
    float CalculateRearSteerAngleDegrees(float SignedTravelSpeedCmPerSecond,
        float DesiredBodyYawRateDegreesPerSecond) const;
    /** Both empty and full stillages use this same three-high limit. */
    UFUNCTION(BlueprintPure, Category="Line Boss|Stillage FLT|Stacking")
    int32 GetMaximumStackTier() const { return MaximumSupportedStackTier; }
    UFUNCTION(BlueprintPure, Category="Line Boss|Stillage FLT|Stacking")
    int32 GetCarryingCapacityStillages() const { return 1; }
    UFUNCTION(BlueprintPure, Category="Line Boss|Stillage FLT|Stacking")
    float GetForkPlacementHeightForTier(int32 StackTier) const;
    UFUNCTION(BlueprintPure, Category="Line Boss|Stillage FLT|Stacking")
    float GetMaximumForkPlacementHeightCm() const { return MaximumSupportedForkPlacementHeightCm; }
    UFUNCTION(BlueprintPure, Category="Line Boss|Stillage FLT|Stacking")
    float GetTransportLiftHeightCm() const { return TransportLiftHeightCm; }
    UFUNCTION(BlueprintPure, Category="Line Boss|Stillage FLT|Stacking")
    bool CanReachStackTier(int32 StackTier) const;
    UFUNCTION(BlueprintPure, Category="Line Boss|Stillage FLT|Stacking")
    bool IsAlignedWithTargetStackPad() const;
    UFUNCTION(BlueprintPure, Category="Line Boss|Stillage FLT|Presentation")
    USpotLightComponent* GetLeftMastWorkLight() const { return LeftMastWorkLight; }
    UFUNCTION(BlueprintPure, Category="Line Boss|Stillage FLT|Presentation")
    USpotLightComponent* GetRightMastWorkLight() const { return RightMastWorkLight; }

    /**
     * Explicit hook for a surgically separated approved Meshy paint slot. It never
     * discovers or recolours slots automatically. Optional brightness is applied
     * only when the existing textured parent declares that scalar parameter.
     */
    UFUNCTION(BlueprintCallable, Category="Line Boss|Stillage FLT|Presentation")
    bool RegisterApprovedPaintableSlot(UMeshComponent* MeshComponent, int32 MaterialIndex,
        ELBMachineLiveryRole LiveryRole, FName TintParameter = TEXT("LiveryTint"),
        FName BrightnessParameter = TEXT("TextureBrightness"));

protected:
    UPROPERTY(EditAnywhere, BlueprintReadOnly, Category="Line Boss|Stillage FLT|Motion", meta=(ClampMin="10.0"))
    float EmptyMaximumSpeedCmPerSecond = 170.0f;
    UPROPERTY(EditAnywhere, BlueprintReadOnly, Category="Line Boss|Stillage FLT|Motion", meta=(ClampMin="10.0"))
    float LoadedMaximumSpeedCmPerSecond = 125.0f;
    UPROPERTY(EditAnywhere, BlueprintReadOnly, Category="Line Boss|Stillage FLT|Motion", meta=(ClampMin="1.0"))
    float AccelerationCmPerSecondSquared = 90.0f;
    UPROPERTY(EditAnywhere, BlueprintReadOnly, Category="Line Boss|Stillage FLT|Motion", meta=(ClampMin="1.0"))
    float DecelerationCmPerSecondSquared = 135.0f;
    UPROPERTY(EditAnywhere, BlueprintReadOnly, Category="Line Boss|Stillage FLT|Motion", meta=(ClampMin="1.0"))
    float MaximumSteeringDegreesPerSecond = 55.0f;
    UPROPERTY(EditAnywhere, BlueprintReadOnly, Category="Line Boss|Stillage FLT|Motion", meta=(ClampMin="50.0"))
    float WheelbaseCm = 155.0f;
    UPROPERTY(EditAnywhere, BlueprintReadOnly, Category="Line Boss|Stillage FLT|Motion", meta=(ClampMin="5.0", ClampMax="55.0"))
    float MaximumRearSteerAngleDegrees = MaximumSupportedRearSteerAngleDegrees;
    UPROPERTY(EditAnywhere, BlueprintReadOnly, Category="Line Boss|Stillage FLT|Motion", meta=(ClampMin="5.0"))
    float RearSteerRateDegreesPerSecond = 92.0f;
    UPROPERTY(EditAnywhere, BlueprintReadOnly, Category="Line Boss|Stillage FLT|Motion", meta=(ClampMin="0.1"))
    float HeadingResponseSeconds = 0.62f;
    UPROPERTY(EditAnywhere, BlueprintReadOnly, Category="Line Boss|Stillage FLT|Motion", meta=(ClampMin="10.0"))
    float CornerRadiusCm = 190.0f;
    UPROPERTY(EditAnywhere, BlueprintReadOnly, Category="Line Boss|Stillage FLT|Safety", meta=(ClampMin="0.0"))
    float ProtectedEnvelopeClearanceCm = 45.0f;
    UPROPERTY(EditAnywhere, BlueprintReadOnly, Category="Line Boss|Stillage FLT|Safety", meta=(ClampMin="0.0"))
    float RearTailOverhangCm = 60.0f;
    UPROPERTY(EditAnywhere, BlueprintReadOnly, Category="Line Boss|Stillage FLT|Safety", meta=(ClampMin="0.0"))
    float ForkTipOverhangCm = 75.0f;
    UPROPERTY(EditAnywhere, BlueprintReadOnly, Category="Line Boss|Stillage FLT|Safety", meta=(ClampMin="0.0"))
    float SteeringSweepSafetyMarginCm = 15.0f;
    UPROPERTY(EditAnywhere, BlueprintReadOnly, Category="Line Boss|Stillage FLT|Handling", meta=(ClampMin="0.0", ClampMax="12.0"))
    float TransportLiftHeightCm = MaximumPermittedTravelLiftCm;
    UPROPERTY(EditAnywhere, BlueprintReadOnly, Category="Line Boss|Stillage FLT|Handling", meta=(ClampMin="0.0", ClampMax="290.0"))
    float ForkEntryHeightCm = 3.0f;
    UPROPERTY(EditAnywhere, BlueprintReadOnly, Category="Line Boss|Stillage FLT|Handling", meta=(ClampMin="120.0", ClampMax="180.0"))
    float TierTwoForkPlacementHeightCm = 150.0f;
    UPROPERTY(EditAnywhere, BlueprintReadOnly, Category="Line Boss|Stillage FLT|Handling", meta=(ClampMin="260.0", ClampMax="290.0"))
    float TierThreeForkPlacementHeightCm = MaximumSupportedForkPlacementHeightCm;
    UPROPERTY(EditAnywhere, BlueprintReadOnly, Category="Line Boss|Stillage FLT|Handling", meta=(ClampMin="1.0"))
    float LiftSpeedCmPerSecond = 24.0f;
    UPROPERTY(EditAnywhere, BlueprintReadOnly, Category="Line Boss|Stillage FLT|Handling", meta=(ClampMin="0.1"))
    float DockProveSeconds = 0.55f;
    UPROPERTY(EditAnywhere, BlueprintReadOnly, Category="Line Boss|Stillage FLT|Handling", meta=(ClampMin="0.1"))
    float StackLocatorProveSeconds = 0.35f;
    UPROPERTY(EditAnywhere, BlueprintReadOnly, Category="Line Boss|Stillage FLT|Handling", meta=(ClampMin="1.0", ClampMax="40.0"))
    float StackLocatorPositionToleranceCm = 22.0f;
    UPROPERTY(EditAnywhere, BlueprintReadOnly, Category="Line Boss|Stillage FLT|Handling", meta=(ClampMin="1.0", ClampMax="20.0"))
    float StackLocatorYawToleranceDegrees = 12.0f;
    /** Applied only when approved textured art explicitly exposes TextureBrightness (or the supplied parameter). */
    UPROPERTY(EditAnywhere, BlueprintReadOnly, Category="Line Boss|Stillage FLT|Presentation", meta=(ClampMin="1.0", ClampMax="1.5"))
    float ApprovedTextureBrightnessMultiplier = 1.16f;

private:
    UPROPERTY(VisibleAnywhere, Category="Line Boss|Stillage FLT|Collision") TObjectPtr<UBoxComponent> CollisionRoot;
    /** Rotated 180 degrees so the v003 asset's local -X travel direction matches Unreal actor +X. */
    UPROPERTY(VisibleAnywhere, Category="Line Boss|Stillage FLT|Presentation") TObjectPtr<USceneComponent> VisualAssetRoot;
    UPROPERTY(VisibleAnywhere, Category="Line Boss|Stillage FLT|Presentation") TObjectPtr<UStaticMeshComponent> BodyVisual;
    UPROPERTY(VisibleAnywhere, Category="Line Boss|Stillage FLT|Presentation") TObjectPtr<UStaticMeshComponent> FrameVisual;
    UPROPERTY(VisibleAnywhere, Category="Line Boss|Stillage FLT|Presentation") TObjectPtr<USceneComponent> FixedFrontAxleRoot;
    UPROPERTY(VisibleAnywhere, Category="Line Boss|Stillage FLT|Presentation") TObjectPtr<UStaticMeshComponent> FrontLeftWheelVisual;
    UPROPERTY(VisibleAnywhere, Category="Line Boss|Stillage FLT|Presentation") TObjectPtr<UStaticMeshComponent> FrontRightWheelVisual;
    UPROPERTY(VisibleAnywhere, Category="Line Boss|Stillage FLT|Presentation") TObjectPtr<USceneComponent> RearSteeringPivot;
    UPROPERTY(VisibleAnywhere, Category="Line Boss|Stillage FLT|Presentation") TObjectPtr<UStaticMeshComponent> RearLeftWheelVisual;
    UPROPERTY(VisibleAnywhere, Category="Line Boss|Stillage FLT|Presentation") TObjectPtr<UStaticMeshComponent> RearRightWheelVisual;
    UPROPERTY(VisibleAnywhere, Category="Line Boss|Stillage FLT|Presentation") TObjectPtr<USceneComponent> MastTiltRoot;
    UPROPERTY(VisibleAnywhere, Category="Line Boss|Stillage FLT|Presentation") TObjectPtr<UStaticMeshComponent> OuterMastVisual;
    UPROPERTY(VisibleAnywhere, Category="Line Boss|Stillage FLT|Presentation") TObjectPtr<USceneComponent> InnerMastMover;
    UPROPERTY(VisibleAnywhere, Category="Line Boss|Stillage FLT|Presentation") TObjectPtr<UStaticMeshComponent> InnerMastVisual;
    UPROPERTY(VisibleAnywhere, Category="Line Boss|Stillage FLT|Presentation") TObjectPtr<USceneComponent> SecondMastMover;
    UPROPERTY(VisibleAnywhere, Category="Line Boss|Stillage FLT|Presentation") TObjectPtr<UStaticMeshComponent> SecondMastVisual;
    UPROPERTY(VisibleAnywhere, Category="Line Boss|Stillage FLT|Presentation") TObjectPtr<USceneComponent> CarriageMover;
    UPROPERTY(VisibleAnywhere, Category="Line Boss|Stillage FLT|Presentation") TObjectPtr<UStaticMeshComponent> CarriageVisual;
    UPROPERTY(VisibleAnywhere, Category="Line Boss|Stillage FLT|Presentation") TObjectPtr<USceneComponent> LiftRodMover;
    UPROPERTY(VisibleAnywhere, Category="Line Boss|Stillage FLT|Presentation") TObjectPtr<UStaticMeshComponent> LiftRodVisual;
    UPROPERTY(VisibleAnywhere, Category="Line Boss|Stillage FLT|Presentation") TObjectPtr<USceneComponent> LeftForkAdjuster;
    UPROPERTY(VisibleAnywhere, Category="Line Boss|Stillage FLT|Presentation") TObjectPtr<USceneComponent> RightForkAdjuster;
    UPROPERTY(VisibleAnywhere, Category="Line Boss|Stillage FLT|Presentation") TObjectPtr<UStaticMeshComponent> LeftForkVisual;
    UPROPERTY(VisibleAnywhere, Category="Line Boss|Stillage FLT|Presentation") TObjectPtr<UStaticMeshComponent> RightForkVisual;
    UPROPERTY(VisibleAnywhere, Category="Line Boss|Stillage FLT|Presentation") TObjectPtr<UStaticMeshComponent> CarriedStillageVisual;
    UPROPERTY(VisibleAnywhere, Category="Line Boss|Stillage FLT|Presentation") TObjectPtr<ULBStatusBeaconComponent> StatusBeacon;
    UPROPERTY(VisibleAnywhere, Category="Line Boss|Stillage FLT|Presentation") TObjectPtr<ULBMachineLiveryComponent> MachineLivery;
    UPROPERTY(VisibleAnywhere, Category="Line Boss|Stillage FLT|Presentation") TObjectPtr<USpotLightComponent> LeftMastWorkLight;
    UPROPERTY(VisibleAnywhere, Category="Line Boss|Stillage FLT|Presentation") TObjectPtr<USpotLightComponent> RightMastWorkLight;

    UPROPERTY(VisibleInstanceOnly, SaveGame, Category="Line Boss|Stillage FLT|Identity") FName UnitId = NAME_None;
    UPROPERTY(VisibleInstanceOnly, SaveGame, Category="Line Boss|Stillage FLT|State") ELBCompactStillageFLTPhase Phase = ELBCompactStillageFLTPhase::Parked;
    UPROPERTY(VisibleInstanceOnly, SaveGame, Category="Line Boss|Stillage FLT|State") ELBCompactStillageFLTFault ActiveFault = ELBCompactStillageFLTFault::None;
    UPROPERTY(VisibleInstanceOnly, SaveGame, Category="Line Boss|Stillage FLT|State") FName ActiveJobId = NAME_None;
    UPROPERTY(VisibleInstanceOnly, SaveGame, Category="Line Boss|Stillage FLT|State") FVector HomeBerth = FVector::ZeroVector;

    FLBStillageFLTJob ActiveJob;
    TArray<FVector> RuntimePath;
    int32 RuntimePathIndex = INDEX_NONE;
    FVector RuntimePathStart = FVector::ZeroVector;
    float CurrentSpeedCmPerSecond = 0.0f;
    float CurrentRearSteerAngleDegrees = 0.0f;
    float CarriageLiftCm = 0.0f;
    float PhaseElapsedSeconds = 0.0f;
    float TrafficWaitSeconds = 0.0f;
    bool bCarryingStillage = false;
    bool bCarriedStillageFull = false;
    bool bWaitingForTraffic = false;
    bool bDeliveryEventEmitted = false;
    /**
     * Chosen once for an unloaded return-to-berth leg. A rear-steer FLT may back
     * to its parking bay instead of attempting an in-place U-turn; pickup and
     * drop-off legs remain forks-first. UI/save speed stays a positive magnitude.
     */
    bool bReversingTravel = false;
    FName CarriedStillageId = NAME_None;
    UPROPERTY(Transient) TObjectPtr<UMaterialInterface> GenericTintableMaterial;

    bool ValidateJob(const FLBStillageFLTJob& Job) const;
    bool PlanRouteTo(const FVector& Destination, ELBCompactStillageFLTPhase TravelPhase);
    void TickTravel(float DeltaSeconds);
    void TickHandling(float DeltaSeconds);
    void ArriveAtRouteDestination();
    void CompleteJob(bool bSucceeded);
    void EnterPhase(ELBCompactStillageFLTPhase NewPhase);
    void LatchFault(ELBCompactStillageFLTFault Fault);
    void ApplyArticulation();
    void ApplyLoadFootprint();
    void UpdatePresentationState();
    void EnsureFallbackLiveryBindings();
    FVector NormaliseTravelPoint(const FVector& Point) const;
    bool IsTravelPhase(ELBCompactStillageFLTPhase Candidate) const;
};
