#include "LBCompactStillageFLT.h"

#include "LBMobileRoutePlanner.h"
#include "LBStatusBeaconComponent.h"

#include "Components/BoxComponent.h"
#include "Components/MeshComponent.h"
#include "Components/SceneComponent.h"
#include "Components/SpotLightComponent.h"
#include "Components/StaticMeshComponent.h"
#include "Materials/MaterialInstanceDynamic.h"
#include "Materials/MaterialInterface.h"
#include "UObject/ConstructorHelpers.h"

namespace
{
    constexpr float VehicleHalfLengthCm = 125.0f;
    constexpr float VehicleHalfWidthCm = 42.0f;
    constexpr float VehicleHalfHeightCm = 82.0f;
    constexpr float WaypointToleranceCm = 16.0f;
    constexpr float MinimumLookAheadCm = 75.0f;
    constexpr float MaximumLookAheadCm = 185.0f;
    constexpr float FinalStackApproachLengthCm = 500.0f;
    constexpr float MinimumLegForAuthoredStackApproachCm = 650.0f;
    constexpr float MaximumCarriageTravelCm =
        ALBCompactStillageFLT::MaximumSupportedForkPlacementHeightCm;
    constexpr float FreeCarriageTravelCm = 90.0f;
    constexpr float FirstTelescopicStageTravelCm = 100.0f;
    constexpr float SecondTelescopicStageTravelCm = 100.0f;

    bool IsFiniteVector(const FVector& Value)
    {
        return FMath::IsFinite(Value.X) && FMath::IsFinite(Value.Y) && FMath::IsFinite(Value.Z);
    }

    bool IsFiniteTransform(const FTransform& Value)
    {
        return IsFiniteVector(Value.GetLocation())
            && IsFiniteVector(Value.GetScale3D())
            && !Value.ContainsNaN();
    }

    bool IsKnownPhaseValue(const ELBCompactStillageFLTPhase Phase)
    {
        return Phase == ELBCompactStillageFLTPhase::Parked
            || Phase == ELBCompactStillageFLTPhase::TravelToPickup
            || Phase == ELBCompactStillageFLTPhase::PickupDockProving
            || Phase == ELBCompactStillageFLTPhase::RaisingLoad
            || Phase == ELBCompactStillageFLTPhase::TravelToDropoff
            || Phase == ELBCompactStillageFLTPhase::DropoffDockProving
            || Phase == ELBCompactStillageFLTPhase::RaisingToStackTier
            || Phase == ELBCompactStillageFLTPhase::StackLocatorProving
            || Phase == ELBCompactStillageFLTPhase::LoweringLoad
            || Phase == ELBCompactStillageFLTPhase::ReturningToBerth
            || Phase == ELBCompactStillageFLTPhase::Fault;
    }

    bool IsKnownFaultValue(const ELBCompactStillageFLTFault Fault)
    {
        return Fault == ELBCompactStillageFLTFault::None
            || Fault == ELBCompactStillageFLTFault::InvalidIdentity
            || Fault == ELBCompactStillageFLTFault::InvalidJob
            || Fault == ELBCompactStillageFLTFault::RouteUnavailable
            || Fault == ELBCompactStillageFLTFault::RouteCollision
            || Fault == ELBCompactStillageFLTFault::RaisedMastTravelProhibited
            || Fault == ELBCompactStillageFLTFault::StackLocatorMisaligned
            || Fault == ELBCompactStillageFLTFault::RestoreRejected;
    }
}

ALBCompactStillageFLT::ALBCompactStillageFLT()
{
    PrimaryActorTick.bCanEverTick = true;
    PrimaryActorTick.bStartWithTickEnabled = true;

    CollisionRoot = CreateDefaultSubobject<UBoxComponent>(TEXT("CollisionRoot"));
    SetRootComponent(CollisionRoot);
    CollisionRoot->SetBoxExtent(FVector(VehicleHalfLengthCm, VehicleHalfWidthCm, VehicleHalfHeightCm));
    CollisionRoot->SetCollisionEnabled(ECollisionEnabled::QueryAndPhysics);
    CollisionRoot->SetCollisionObjectType(ECC_Pawn);
    CollisionRoot->SetCollisionResponseToAllChannels(ECR_Block);
    CollisionRoot->SetGenerateOverlapEvents(false);
    CollisionRoot->SetCanEverAffectNavigation(false);
    CollisionRoot->SetMobility(EComponentMobility::Movable);

    VisualAssetRoot = CreateDefaultSubobject<USceneComponent>(TEXT("CFAGV_ROOT"));
    VisualAssetRoot->SetupAttachment(CollisionRoot);
    VisualAssetRoot->SetRelativeLocation(FVector(0.0f, 0.0f, -VehicleHalfHeightCm));
    // Approved v003 travels and carries forks along local -X.
    VisualAssetRoot->SetRelativeRotation(FRotator(0.0f, 180.0f, 0.0f));

    BodyVisual = CreateDefaultSubobject<UStaticMeshComponent>(TEXT("PaintableBodyFallback"));
    BodyVisual->SetupAttachment(VisualAssetRoot);
    BodyVisual->SetRelativeLocation(FVector(24.0f, 0.0f, 62.0f));
    BodyVisual->SetRelativeScale3D(FVector(1.34f, 0.74f, 0.66f));

    FrameVisual = CreateDefaultSubobject<UStaticMeshComponent>(TEXT("PaintableFrameFallback"));
    FrameVisual->SetupAttachment(VisualAssetRoot);
    FrameVisual->SetRelativeLocation(FVector(10.0f, 0.0f, 25.0f));
    FrameVisual->SetRelativeScale3D(FVector(1.62f, 0.78f, 0.18f));

    FixedFrontAxleRoot = CreateDefaultSubobject<USceneComponent>(TEXT("FIXED_FRONT_DRIVE_AXLE"));
    FixedFrontAxleRoot->SetupAttachment(VisualAssetRoot);
    FixedFrontAxleRoot->SetRelativeLocation(FVector(-62.0f, 0.0f, 25.0f));
    FrontLeftWheelVisual = CreateDefaultSubobject<UStaticMeshComponent>(TEXT("FrontWheelLeftFixed"));
    FrontLeftWheelVisual->SetupAttachment(FixedFrontAxleRoot);
    FrontLeftWheelVisual->SetRelativeLocation(FVector(0.0f, -34.0f, 0.0f));
    FrontRightWheelVisual = CreateDefaultSubobject<UStaticMeshComponent>(TEXT("FrontWheelRightFixed"));
    FrontRightWheelVisual->SetupAttachment(FixedFrontAxleRoot);
    FrontRightWheelVisual->SetRelativeLocation(FVector(0.0f, 34.0f, 0.0f));

    RearSteeringPivot = CreateDefaultSubobject<USceneComponent>(TEXT("PIVOT_REAR_STEER_Z"));
    RearSteeringPivot->SetupAttachment(VisualAssetRoot);
    RearSteeringPivot->SetRelativeLocation(FVector(66.0f, 0.0f, 23.0f));
    RearLeftWheelVisual = CreateDefaultSubobject<UStaticMeshComponent>(TEXT("RearWheelLeftSteered"));
    RearLeftWheelVisual->SetupAttachment(RearSteeringPivot);
    RearLeftWheelVisual->SetRelativeLocation(FVector(0.0f, -27.0f, 0.0f));
    RearRightWheelVisual = CreateDefaultSubobject<UStaticMeshComponent>(TEXT("RearWheelRightSteered"));
    RearRightWheelVisual->SetupAttachment(RearSteeringPivot);
    RearRightWheelVisual->SetRelativeLocation(FVector(0.0f, 27.0f, 0.0f));

    MastTiltRoot = CreateDefaultSubobject<USceneComponent>(TEXT("PIVOT_MAST_TILT_Y"));
    MastTiltRoot->SetupAttachment(VisualAssetRoot);
    MastTiltRoot->SetRelativeLocation(FVector(-92.0f, 0.0f, 10.0f));

    OuterMastVisual = CreateDefaultSubobject<UStaticMeshComponent>(TEXT("MastOuterFallback"));
    OuterMastVisual->SetupAttachment(MastTiltRoot);
    OuterMastVisual->SetRelativeLocation(FVector(0.0f, 0.0f, 72.0f));
    OuterMastVisual->SetRelativeScale3D(FVector(0.16f, 0.82f, 1.36f));

    InnerMastMover = CreateDefaultSubobject<USceneComponent>(TEXT("MOVER_MAST_INNER_STAGE_Z"));
    InnerMastMover->SetupAttachment(MastTiltRoot);
    InnerMastVisual = CreateDefaultSubobject<UStaticMeshComponent>(TEXT("MastInnerFallback"));
    InnerMastVisual->SetupAttachment(InnerMastMover);
    InnerMastVisual->SetRelativeLocation(FVector(-3.0f, 0.0f, 66.0f));
    InnerMastVisual->SetRelativeScale3D(FVector(0.12f, 0.68f, 1.18f));

    SecondMastMover = CreateDefaultSubobject<USceneComponent>(TEXT("MOVER_MAST_SECOND_STAGE_Z"));
    SecondMastMover->SetupAttachment(InnerMastMover);
    SecondMastVisual = CreateDefaultSubobject<UStaticMeshComponent>(TEXT("MastSecondStageFallback"));
    SecondMastVisual->SetupAttachment(SecondMastMover);
    SecondMastVisual->SetRelativeLocation(FVector(-6.0f, 0.0f, 60.0f));
    SecondMastVisual->SetRelativeScale3D(FVector(0.09f, 0.58f, 1.05f));

    CarriageMover = CreateDefaultSubobject<USceneComponent>(TEXT("MOVER_CARRIAGE_Z"));
    CarriageMover->SetupAttachment(SecondMastMover);
    CarriageMover->SetRelativeLocation(FVector(-15.0f, 0.0f, 28.0f));
    CarriageVisual = CreateDefaultSubobject<UStaticMeshComponent>(TEXT("CarriageFallback"));
    CarriageVisual->SetupAttachment(CarriageMover);
    CarriageVisual->SetRelativeScale3D(FVector(0.16f, 0.76f, 0.42f));

    LiftRodMover = CreateDefaultSubobject<USceneComponent>(TEXT("MOVER_LIFT_ROD_Z"));
    LiftRodMover->SetupAttachment(MastTiltRoot);
    LiftRodVisual = CreateDefaultSubobject<UStaticMeshComponent>(TEXT("LiftRodFallback"));
    LiftRodVisual->SetupAttachment(LiftRodMover);
    LiftRodVisual->SetRelativeLocation(FVector(4.0f, 0.0f, 42.0f));
    LiftRodVisual->SetRelativeScale3D(FVector(0.07f, 0.07f, 0.84f));

    LeftForkAdjuster = CreateDefaultSubobject<USceneComponent>(TEXT("ADJUSTER_FORK_LEFT_Y"));
    LeftForkAdjuster->SetupAttachment(CarriageMover);
    LeftForkAdjuster->SetRelativeLocation(FVector(0.0f, -18.5f, 0.0f));
    RightForkAdjuster = CreateDefaultSubobject<USceneComponent>(TEXT("ADJUSTER_FORK_RIGHT_Y"));
    RightForkAdjuster->SetupAttachment(CarriageMover);
    RightForkAdjuster->SetRelativeLocation(FVector(0.0f, 18.5f, 0.0f));

    LeftForkVisual = CreateDefaultSubobject<UStaticMeshComponent>(TEXT("ForkLeftFallback"));
    LeftForkVisual->SetupAttachment(LeftForkAdjuster);
    LeftForkVisual->SetRelativeLocation(FVector(-53.0f, 0.0f, -21.0f));
    LeftForkVisual->SetRelativeScale3D(FVector(1.06f, 0.085f, 0.075f));
    RightForkVisual = CreateDefaultSubobject<UStaticMeshComponent>(TEXT("ForkRightFallback"));
    RightForkVisual->SetupAttachment(RightForkAdjuster);
    RightForkVisual->SetRelativeLocation(FVector(-53.0f, 0.0f, -21.0f));
    RightForkVisual->SetRelativeScale3D(FVector(1.06f, 0.085f, 0.075f));

    CarriedStillageVisual = CreateDefaultSubobject<UStaticMeshComponent>(TEXT("CarriedStillageProxy"));
    CarriedStillageVisual->SetupAttachment(CarriageMover);
    CarriedStillageVisual->SetRelativeLocation(FVector(-112.0f, 0.0f, -4.0f));
    CarriedStillageVisual->SetVisibility(false);

    StatusBeacon = CreateDefaultSubobject<ULBStatusBeaconComponent>(TEXT("StatusBeacon"));
    StatusBeacon->SetupAttachment(VisualAssetRoot);
    StatusBeacon->SetRelativeLocation(FVector(48.0f, 0.0f, 154.0f));
    MachineLivery = CreateDefaultSubobject<ULBMachineLiveryComponent>(TEXT("MachineLivery"));

    LeftMastWorkLight = CreateDefaultSubobject<USpotLightComponent>(TEXT("LENS_MAST_WORKLIGHT_LEFT"));
    LeftMastWorkLight->SetupAttachment(MastTiltRoot);
    LeftMastWorkLight->SetRelativeLocation(FVector(-15.0f, -28.0f, 126.0f));
    LeftMastWorkLight->SetRelativeRotation(FRotator(0.0f, 180.0f, 0.0f));
    RightMastWorkLight = CreateDefaultSubobject<USpotLightComponent>(TEXT("LENS_MAST_WORKLIGHT_RIGHT"));
    RightMastWorkLight->SetupAttachment(MastTiltRoot);
    RightMastWorkLight->SetRelativeLocation(FVector(-15.0f, 28.0f, 126.0f));
    RightMastWorkLight->SetRelativeRotation(FRotator(0.0f, 180.0f, 0.0f));
    for (USpotLightComponent* Light : {LeftMastWorkLight, RightMastWorkLight})
    {
        Light->SetIntensity(1750.0f);
        Light->SetAttenuationRadius(650.0f);
        Light->SetInnerConeAngle(18.0f);
        Light->SetOuterConeAngle(34.0f);
        Light->SetLightColor(FLinearColor(0.90f, 0.96f, 1.0f));
        Light->SetCastShadows(false);
        Light->SetVisibility(false);
    }

    static ConstructorHelpers::FObjectFinder<UStaticMesh> CubeMesh(TEXT("/Engine/BasicShapes/Cube.Cube"));
    static ConstructorHelpers::FObjectFinder<UStaticMesh> CylinderMesh(TEXT("/Engine/BasicShapes/Cylinder.Cylinder"));
    static ConstructorHelpers::FObjectFinder<UMaterialInterface> BasicMaterial(
        TEXT("/Engine/BasicShapes/BasicShapeMaterial.BasicShapeMaterial"));
    static ConstructorHelpers::FObjectFinder<UMaterialInterface> SteelMaterial(
        TEXT("/Game/LineBoss/Candidates/ControlRoom/MainControlRoom_v002/Materials/M_CA_BrushedSteel_R_v002.M_CA_BrushedSteel_R_v002"));
    static ConstructorHelpers::FObjectFinder<UMaterialInterface> SafetyYellowMaterial(
        TEXT("/Game/LineBoss/Candidates/ControlRoom/MainControlRoom_v002/Materials/M_CA_SafetyYellow_R_v002.M_CA_SafetyYellow_R_v002"));
    GenericTintableMaterial = BasicMaterial.Object;
    for (UStaticMeshComponent* Mesh : {BodyVisual, FrameVisual, OuterMastVisual, InnerMastVisual,
        SecondMastVisual, CarriageVisual, LiftRodVisual, LeftForkVisual, RightForkVisual,
        CarriedStillageVisual})
    {
        Mesh->SetStaticMesh(CubeMesh.Object);
        Mesh->SetCollisionEnabled(ECollisionEnabled::NoCollision);
        Mesh->SetGenerateOverlapEvents(false);
        Mesh->SetCanEverAffectNavigation(false);
        Mesh->SetMobility(EComponentMobility::Movable);
    }
    for (UStaticMeshComponent* Wheel : {FrontLeftWheelVisual, FrontRightWheelVisual,
        RearLeftWheelVisual, RearRightWheelVisual})
    {
        Wheel->SetStaticMesh(CylinderMesh.Object);
        Wheel->SetRelativeRotation(FRotator(0.0f, 0.0f, 90.0f));
        Wheel->SetRelativeScale3D(FVector(0.25f, 0.25f, 0.13f));
        Wheel->SetCollisionEnabled(ECollisionEnabled::NoCollision);
        Wheel->SetGenerateOverlapEvents(false);
        Wheel->SetCanEverAffectNavigation(false);
        Wheel->SetMobility(EComponentMobility::Movable);
    }
    if (BasicMaterial.Succeeded())
    {
        BodyVisual->SetMaterial(0, BasicMaterial.Object);
        FrameVisual->SetMaterial(0, BasicMaterial.Object);
        CarriedStillageVisual->SetMaterial(0, BasicMaterial.Object);
    }
    if (SteelMaterial.Succeeded())
    {
        OuterMastVisual->SetMaterial(0, SteelMaterial.Object);
        InnerMastVisual->SetMaterial(0, SteelMaterial.Object);
        SecondMastVisual->SetMaterial(0, SteelMaterial.Object);
        LiftRodVisual->SetMaterial(0, SteelMaterial.Object);
        LeftForkVisual->SetMaterial(0, SteelMaterial.Object);
        RightForkVisual->SetMaterial(0, SteelMaterial.Object);
    }
    if (BasicMaterial.Succeeded())
    {
        FrontLeftWheelVisual->SetMaterial(0, BasicMaterial.Object);
        FrontRightWheelVisual->SetMaterial(0, BasicMaterial.Object);
        RearLeftWheelVisual->SetMaterial(0, BasicMaterial.Object);
        RearRightWheelVisual->SetMaterial(0, BasicMaterial.Object);
    }
    if (SafetyYellowMaterial.Succeeded())
    {
        // The load backrest/carriage remains safety yellow and is intentionally outside livery.
        CarriageVisual->SetMaterial(0, SafetyYellowMaterial.Object);
    }
}

void ALBCompactStillageFLT::BeginPlay()
{
    Super::BeginPlay();
    EnsureFallbackLiveryBindings();
    ApplyArticulation();
    ApplyLoadFootprint();
    UpdatePresentationState();
}

void ALBCompactStillageFLT::EnsureFallbackLiveryBindings()
{
    if (MachineLivery && GenericTintableMaterial && MachineLivery->GetMaterialBindingCount() == 0)
    {
        MachineLivery->RegisterGenericMaterialBinding(BodyVisual, 0,
            ELBMachineLiveryRole::PrimaryBody, GenericTintableMaterial, TEXT("Color"));
        MachineLivery->RegisterGenericMaterialBinding(FrameVisual, 0,
            ELBMachineLiveryRole::SecondaryFrame, GenericTintableMaterial, TEXT("Color"));
    }
}

bool ALBCompactStillageFLT::RegisterApprovedPaintableSlot(UMeshComponent* MeshComponent,
    const int32 MaterialIndex, const ELBMachineLiveryRole LiveryRole, const FName TintParameter,
    const FName BrightnessParameter)
{
    if (!MachineLivery || !MeshComponent || MaterialIndex < 0
        || MaterialIndex >= MeshComponent->GetNumMaterials())
    {
        return false;
    }
    UMaterialInterface* ExistingMaterial = MeshComponent->GetMaterial(MaterialIndex);
    float ExistingBrightness = 1.0f;
    const bool bHasAuthoredBrightness = ExistingMaterial && !BrightnessParameter.IsNone()
        && ExistingMaterial->GetScalarParameterValue(
            FMaterialParameterInfo(BrightnessParameter), ExistingBrightness);
    const int32 BindingIndex = MachineLivery->GetMaterialBindingCount();
    if (!MachineLivery->RegisterTexturedMaterialBinding(
        MeshComponent, MaterialIndex, LiveryRole, TintParameter))
    {
        return false;
    }
    if (bHasAuthoredBrightness)
    {
        if (UMaterialInstanceDynamic* MID = MachineLivery->GetDynamicMaterialForBinding(BindingIndex))
        {
            MID->SetScalarParameterValue(BrightnessParameter,
                FMath::Max(ExistingBrightness, ApprovedTextureBrightnessMultiplier));
        }
    }
    return true;
}

bool ALBCompactStillageFLT::ConfigureUnit(const FName InUnitId, const FVector InHomeBerth)
{
    if (InUnitId.IsNone() || !IsFiniteVector(InHomeBerth)
        || (!UnitId.IsNone() && UnitId != InUnitId) || !ActiveJobId.IsNone())
    {
        return false;
    }
    UnitId = InUnitId;
    HomeBerth = InHomeBerth;
    // A fleet may commission this unit after a manually driven or streaming
    // world has entered play. Keep presentation setup independent of whether
    // BeginPlay was dispatched before or after ConfigureUnit.
    EnsureFallbackLiveryBindings();
    SetActorLocation(HomeBerth, false, nullptr, ETeleportType::None);
    ActiveFault = ELBCompactStillageFLTFault::None;
    EnterPhase(ELBCompactStillageFLTPhase::Parked);
    return true;
}

bool ALBCompactStillageFLT::ValidateJob(const FLBStillageFLTJob& Job) const
{
    return Job.Version == 1 && !Job.JobId.IsNone() && !Job.StillageId.IsNone()
        && !Job.SourceAuthorityId.IsNone() && !Job.TargetAuthorityId.IsNone()
        && Job.SourceAuthorityId != Job.TargetAuthorityId
        && !Job.TargetStackPadId.IsNone()
        && Job.TargetStackTier >= 1 && Job.TargetStackTier <= MaximumSupportedStackTier
        && FMath::IsFinite(Job.TargetStackPadYawDegrees)
        && IsFiniteVector(Job.PickupServicePoint) && IsFiniteVector(Job.DropoffServicePoint)
        && FVector::Dist2D(Job.PickupServicePoint, Job.DropoffServicePoint) >= 50.0f
        && FMath::IsFinite(Job.StillageHalfExtentCm.X)
        && FMath::IsFinite(Job.StillageHalfExtentCm.Y)
        && Job.StillageHalfExtentCm.X >= 20.0f && Job.StillageHalfExtentCm.X <= 250.0f
        && Job.StillageHalfExtentCm.Y >= 20.0f && Job.StillageHalfExtentCm.Y <= 250.0f;
}

float ALBCompactStillageFLT::GetOutwardSweepAllowanceCm() const
{
    const float MaximumOverhang = FMath::Max(RearTailOverhangCm, ForkTipOverhangCm);
    return MaximumOverhang * FMath::Sin(FMath::DegreesToRadians(MaximumRearSteerAngleDegrees))
        + SteeringSweepSafetyMarginCm;
}

float ALBCompactStillageFLT::GetRequiredServicePointStandOffCm(
    const FVector2D StillageHalfExtentCm) const
{
    const FVector2D LoadedHalfExtent(
        FMath::Max(VehicleHalfLengthCm, StillageHalfExtentCm.X),
        FMath::Max(VehicleHalfWidthCm, StillageHalfExtentCm.Y)
            + GetOutwardSweepAllowanceCm());
    // LBMobileRoutePlanner plans against a circumscribed vehicle radius and adds
    // half the requested corner radius before validating the rounded path. Keep
    // pickup/drop-off locator points outside that same envelope so a newly loaded
    // FLT can leave its source without being declared inside an obstacle.
    return LoadedHalfExtent.Size() + ProtectedEnvelopeClearanceCm
        + CornerRadiusCm * 0.5f + 2.0f;
}

float ALBCompactStillageFLT::CalculateRearSteerAngleDegrees(
    const float SignedTravelSpeedCmPerSecond,
    const float DesiredBodyYawRateDegreesPerSecond) const
{
    const float DirectionSign = SignedTravelSpeedCmPerSecond < 0.0f ? -1.0f : 1.0f;
    const float EffectiveSignedSpeed = DirectionSign
        * FMath::Max(FMath::Abs(SignedTravelSpeedCmPerSecond), 20.0f);
    const float DesiredYawRateRadians = FMath::DegreesToRadians(
        DesiredBodyYawRateDegreesPerSecond);
    const float RearSteerRadians = FMath::Atan(
        -WheelbaseCm * DesiredYawRateRadians / EffectiveSignedSpeed);
    return FMath::Clamp(FMath::RadiansToDegrees(RearSteerRadians),
        -MaximumRearSteerAngleDegrees, MaximumRearSteerAngleDegrees);
}

float ALBCompactStillageFLT::GetForkPlacementHeightForTier(const int32 StackTier) const
{
    switch (StackTier)
    {
    case 1:
        return ForkEntryHeightCm;
    case 2:
        return TierTwoForkPlacementHeightCm;
    case 3:
        return TierThreeForkPlacementHeightCm;
    default:
        return -1.0f;
    }
}

bool ALBCompactStillageFLT::CanReachStackTier(const int32 StackTier) const
{
    const float Height = GetForkPlacementHeightForTier(StackTier);
    return Height >= 0.0f && Height <= MaximumCarriageTravelCm + KINDA_SMALL_NUMBER;
}

bool ALBCompactStillageFLT::IsAlignedWithTargetStackPad() const
{
    if (!ValidateJob(ActiveJob) || ActiveJob.TargetStackPadId.IsNone())
    {
        return false;
    }
    const FVector PadCentre = NormaliseTravelPoint(ActiveJob.DropoffServicePoint);
    const float PositionErrorCm = FVector::Dist2D(GetActorLocation(), PadCentre);
    const float YawErrorDegrees = FMath::Abs(FMath::FindDeltaAngleDegrees(
        GetActorRotation().Yaw, ActiveJob.TargetStackPadYawDegrees));
    return PositionErrorCm <= StackLocatorPositionToleranceCm
        && YawErrorDegrees <= StackLocatorYawToleranceDegrees;
}

bool ALBCompactStillageFLT::StartJob(const FLBStillageFLTJob& Job)
{
    if (!IsAvailableForJob() || UnitId.IsNone() || !ValidateJob(Job))
    {
        return false;
    }
    ActiveJob = Job;
    ActiveJobId = Job.JobId;
    bDeliveryEventEmitted = false;
    bCarryingStillage = false;
    bCarriedStillageFull = false;
    CarriedStillageId = NAME_None;
    CarriageLiftCm = ForkEntryHeightCm;
    ApplyArticulation();
    ApplyLoadFootprint();
    if (!PlanRouteTo(Job.PickupServicePoint, ELBCompactStillageFLTPhase::TravelToPickup))
    {
        ActiveJob = FLBStillageFLTJob();
        ActiveJobId = NAME_None;
        return false;
    }
    return true;
}

bool ALBCompactStillageFLT::ResumeAssignedJob(const FLBStillageFLTJob& Job)
{
    if (!ValidateJob(Job) || ActiveJobId != Job.JobId || UnitId != Job.ClaimedUnitId)
    {
        return false;
    }
    ActiveJob = Job;
    // Restore applies the conservative default before the claimed job is
    // rebound. Re-apply now so a non-default stillage keeps its saved envelope.
    ApplyLoadFootprint();
    if (Phase == ELBCompactStillageFLTPhase::Fault)
    {
        UpdatePresentationState();
        return true;
    }
    if (Phase == ELBCompactStillageFLTPhase::LoweringLoad)
    {
        return bDeliveryEventEmitted && !bCarryingStillage;
    }
    if (Phase == ELBCompactStillageFLTPhase::ReturningToBerth)
    {
        if (!bDeliveryEventEmitted || bCarryingStillage
            || CarriageLiftCm > TransportLiftHeightCm + 0.05f)
        {
            return false;
        }
        bCarryingStillage = false;
        CarriedStillageId = NAME_None;
        ApplyLoadFootprint();
        return PlanRouteTo(HomeBerth, ELBCompactStillageFLTPhase::ReturningToBerth);
    }
    if (Phase == ELBCompactStillageFLTPhase::PickupDockProving
        || Phase == ELBCompactStillageFLTPhase::RaisingLoad
        || Phase == ELBCompactStillageFLTPhase::DropoffDockProving
        || Phase == ELBCompactStillageFLTPhase::RaisingToStackTier
        || Phase == ELBCompactStillageFLTPhase::StackLocatorProving)
    {
        return true;
    }
    if (Phase == ELBCompactStillageFLTPhase::TravelToDropoff && bCarryingStillage)
    {
        return PlanRouteTo(Job.DropoffServicePoint,
            ELBCompactStillageFLTPhase::TravelToDropoff);
    }
    if (Phase == ELBCompactStillageFLTPhase::TravelToPickup && !bCarryingStillage)
    {
        return PlanRouteTo(Job.PickupServicePoint,
            ELBCompactStillageFLTPhase::TravelToPickup);
    }
    return false;
}

bool ALBCompactStillageFLT::ResetFault()
{
    if (Phase != ELBCompactStillageFLTPhase::Fault)
    {
        return false;
    }
    ActiveFault = ELBCompactStillageFLTFault::None;
    if (ActiveJobId.IsNone())
    {
        EnterPhase(ELBCompactStillageFLTPhase::Parked);
        return true;
    }
    if (bDeliveryEventEmitted)
    {
        if (CarriageLiftCm > ForkEntryHeightCm + 0.05f)
        {
            EnterPhase(ELBCompactStillageFLTPhase::LoweringLoad);
            return true;
        }
        return PlanRouteTo(HomeBerth, ELBCompactStillageFLTPhase::ReturningToBerth);
    }
    if (bCarryingStillage && CarriageLiftCm > TransportLiftHeightCm + 0.05f)
    {
        if (!IsAlignedWithTargetStackPad())
        {
            LatchFault(ELBCompactStillageFLTFault::StackLocatorMisaligned);
            return false;
        }
        EnterPhase(ELBCompactStillageFLTPhase::StackLocatorProving);
        return true;
    }
    return bCarryingStillage
        ? PlanRouteTo(ActiveJob.DropoffServicePoint, ELBCompactStillageFLTPhase::TravelToDropoff)
        : PlanRouteTo(ActiveJob.PickupServicePoint, ELBCompactStillageFLTPhase::TravelToPickup);
}

void ALBCompactStillageFLT::Tick(const float DeltaSeconds)
{
    Super::Tick(DeltaSeconds);
    if (DeltaSeconds <= 0.0f || Phase == ELBCompactStillageFLTPhase::Fault)
    {
        return;
    }
    if (Phase == ELBCompactStillageFLTPhase::Parked)
    {
        CurrentRearSteerAngleDegrees = FMath::FInterpConstantTo(
            CurrentRearSteerAngleDegrees, 0.0f, DeltaSeconds,
            RearSteerRateDegreesPerSecond);
        ApplyArticulation();
        return;
    }
    PhaseElapsedSeconds += DeltaSeconds;
    if (IsTravelPhase(Phase))
    {
        TickTravel(DeltaSeconds);
    }
    else
    {
        CurrentRearSteerAngleDegrees = FMath::FInterpConstantTo(
            CurrentRearSteerAngleDegrees, 0.0f, DeltaSeconds,
            RearSteerRateDegreesPerSecond);
        ApplyArticulation();
        TickHandling(DeltaSeconds);
    }
}

FVector ALBCompactStillageFLT::NormaliseTravelPoint(const FVector& Point) const
{
    return FVector(Point.X, Point.Y, HomeBerth.Z);
}

bool ALBCompactStillageFLT::PlanRouteTo(const FVector& Destination,
    const ELBCompactStillageFLTPhase TravelPhase)
{
    if (!GetWorld() || !IsTravelPhase(TravelPhase) || !IsFiniteVector(Destination)
        || CarriageLiftCm > TransportLiftHeightCm + 0.05f)
    {
        return false;
    }
    LBMobileRoutePlanner::FSettings Settings;
    const FVector Extent = CollisionRoot
        ? CollisionRoot->GetUnscaledBoxExtent()
        : FVector(VehicleHalfLengthCm, VehicleHalfWidthCm, VehicleHalfHeightCm);
    Settings.VehicleHalfExtentCm = FVector2D(Extent.X, Extent.Y);
    Settings.EnvelopeClearanceCm = ProtectedEnvelopeClearanceCm;
    Settings.CornerRadiusCm = CornerRadiusCm;
    Settings.MaximumCurveStepDegrees = 10.0f;
    const FVector Target = NormaliseTravelPoint(Destination);
    TArray<FVector> CertifiedWaypoints;
    if (TravelPhase == ELBCompactStillageFLTPhase::TravelToDropoff
        && ValidateJob(ActiveJob)
        && FVector::Dist2D(GetActorLocation(), Target)
            >= MinimumLegForAuthoredStackApproachCm)
    {
        // Give the rear-steer chassis a genuine straightening lane before the
        // locator pad. Chasing only the final point can stop the body diagonally
        // after a 180-degree change of aisle even though its forks reached the
        // correct position.
        const FVector PadForward = FRotator(
            0.0f, ActiveJob.TargetStackPadYawDegrees, 0.0f).Vector();
        CertifiedWaypoints.Add(Target - PadForward * FinalStackApproachLengthCm);
    }
    CertifiedWaypoints.Add(Target);
    TArray<FVector> Planned;
    if (!LBMobileRoutePlanner::BuildClearanceAwarePath(
        GetWorld(), GetActorLocation(), CertifiedWaypoints, Settings, Planned)
        || Planned.IsEmpty())
    {
        return false;
    }
    RuntimePath = MoveTemp(Planned);
    RuntimePathIndex = 0;
    RuntimePathStart = GetActorLocation();
    CurrentSpeedCmPerSecond = FMath::Max(0.0f, CurrentSpeedCmPerSecond);
    const FVector FirstMotion = (RuntimePath[0] - RuntimePathStart).GetSafeNormal2D();
    bReversingTravel = TravelPhase == ELBCompactStillageFLTPhase::ReturningToBerth
        && !FirstMotion.IsNearlyZero()
        && FMath::Abs(FMath::FindDeltaAngleDegrees(
            GetActorRotation().Yaw, FirstMotion.Rotation().Yaw)) > 100.0f;
    bWaitingForTraffic = false;
    TrafficWaitSeconds = 0.0f;
    EnterPhase(TravelPhase);
    return true;
}

void ALBCompactStillageFLT::TickTravel(const float DeltaSeconds)
{
    if (CarriageLiftCm > TransportLiftHeightCm + 0.05f)
    {
        LatchFault(ELBCompactStillageFLTFault::RaisedMastTravelProhibited);
        return;
    }
    if (!RuntimePath.IsValidIndex(RuntimePathIndex))
    {
        LatchFault(ELBCompactStillageFLTFault::RouteUnavailable);
        return;
    }

    const FVector Current = GetActorLocation();
    while (RuntimePath.IsValidIndex(RuntimePathIndex))
    {
        const FVector Target = RuntimePath[RuntimePathIndex];
        const FVector SegmentStart = RuntimePathIndex == 0
            ? RuntimePathStart : RuntimePath[RuntimePathIndex - 1];
        const FVector Segment = (Target - SegmentStart).GetSafeNormal2D();
        const float Distance = FVector::Dist2D(Current, Target);
        const bool bFinalPoint = RuntimePathIndex == RuntimePath.Num() - 1;
        if (bFinalPoint && Distance <= 0.5f)
        {
            CurrentSpeedCmPerSecond = FMath::FInterpConstantTo(CurrentSpeedCmPerSecond,
                0.0f, DeltaSeconds, DecelerationCmPerSecondSquared);
            CurrentRearSteerAngleDegrees = FMath::FInterpConstantTo(
                CurrentRearSteerAngleDegrees, 0.0f, DeltaSeconds,
                RearSteerRateDegreesPerSecond);
            ApplyArticulation();
            if (CurrentSpeedCmPerSecond <= KINDA_SMALL_NUMBER)
            {
                SetActorLocation(Target, false, nullptr, ETeleportType::None);
                ++RuntimePathIndex;
                ArriveAtRouteDestination();
            }
            return;
        }
        if (bFinalPoint)
        {
            // Never consume the final point through the ordinary waypoint
            // tolerance. Braking must reach zero before arrival so speed and
            // animation cannot snap during the last few centimetres.
            break;
        }
        const bool bPassedPoint = !bFinalPoint && !Segment.IsNearlyZero()
            && FVector::DotProduct((Current - Target).GetSafeNormal2D(), Segment) > 0.0f
            && Distance <= MaximumLookAheadCm;
        if (Distance > WaypointToleranceCm && !bPassedPoint)
        {
            break;
        }
        ++RuntimePathIndex;
    }
    if (!RuntimePath.IsValidIndex(RuntimePathIndex))
    {
        ArriveAtRouteDestination();
        return;
    }

    float RemainingDistance = FVector::Dist2D(Current, RuntimePath[RuntimePathIndex]);
    for (int32 Index = RuntimePathIndex + 1; Index < RuntimePath.Num(); ++Index)
    {
        RemainingDistance += FVector::Dist2D(RuntimePath[Index - 1], RuntimePath[Index]);
    }
    const float MaximumSpeed = bCarryingStillage
        ? LoadedMaximumSpeedCmPerSecond : EmptyMaximumSpeedCmPerSecond;
    const float LookAhead = FMath::Clamp(70.0f + CurrentSpeedCmPerSecond * 0.78f,
        MinimumLookAheadCm, MaximumLookAheadCm);
    FVector SteeringTarget = Current;
    FVector Cursor = Current;
    float LookAheadRemaining = LookAhead;
    for (int32 Index = RuntimePathIndex; Index < RuntimePath.Num(); ++Index)
    {
        const float SegmentLength = FVector::Dist2D(Cursor, RuntimePath[Index]);
        if (SegmentLength >= LookAheadRemaining && SegmentLength > KINDA_SMALL_NUMBER)
        {
            SteeringTarget = FMath::Lerp(Cursor, RuntimePath[Index], LookAheadRemaining / SegmentLength);
            break;
        }
        SteeringTarget = RuntimePath[Index];
        LookAheadRemaining -= SegmentLength;
        Cursor = RuntimePath[Index];
    }
    const FVector SteeringDirection = (SteeringTarget - Current).GetSafeNormal2D();
    if (SteeringDirection.IsNearlyZero())
    {
        CurrentSpeedCmPerSecond = FMath::FInterpConstantTo(CurrentSpeedCmPerSecond,
            0.0f, DeltaSeconds, DecelerationCmPerSecondSquared);
        CurrentRearSteerAngleDegrees = FMath::FInterpConstantTo(
            CurrentRearSteerAngleDegrees, 0.0f, DeltaSeconds,
            RearSteerRateDegreesPerSecond);
        ApplyArticulation();
        return;
    }

    const float TravelDirectionSign = bReversingTravel ? -1.0f : 1.0f;
    const float DesiredYaw = SteeringDirection.Rotation().Yaw
        + (bReversingTravel ? 180.0f : 0.0f);
    const float SignedHeadingError = FMath::FindDeltaAngleDegrees(
        GetActorRotation().Yaw, DesiredYaw);
    const float HeadingError = FMath::Abs(SignedHeadingError);
    const float BrakingSpeed = FMath::Sqrt(FMath::Max(0.0f,
        2.0f * DecelerationCmPerSecondSquared * RemainingDistance));
    const float HeadingScale = FMath::GetMappedRangeValueClamped(
        FVector2D(0.0f, 90.0f), FVector2D(1.0f, 0.16f), HeadingError);
    const float DesiredSpeed = FMath::Min3(MaximumSpeed, BrakingSpeed, MaximumSpeed * HeadingScale);
    const float SpeedRate = DesiredSpeed >= CurrentSpeedCmPerSecond
        ? AccelerationCmPerSecondSquared : DecelerationCmPerSecondSquared;
    CurrentSpeedCmPerSecond = FMath::FInterpConstantTo(
        CurrentSpeedCmPerSecond, DesiredSpeed, DeltaSeconds, SpeedRate);

    const float DesiredYawRateDegrees = FMath::Clamp(
        SignedHeadingError / FMath::Max(HeadingResponseSeconds, 0.1f),
        -MaximumSteeringDegreesPerSecond, MaximumSteeringDegreesPerSecond);
    const float TargetRearSteerAngle = CalculateRearSteerAngleDegrees(
        TravelDirectionSign * CurrentSpeedCmPerSecond, DesiredYawRateDegrees);
    CurrentRearSteerAngleDegrees = FMath::FInterpConstantTo(CurrentRearSteerAngleDegrees,
        TargetRearSteerAngle, DeltaSeconds, RearSteerRateDegreesPerSecond);
    ApplyArticulation();
    const float BodyYawRateRadians = -TravelDirectionSign * CurrentSpeedCmPerSecond
        / FMath::Max(WheelbaseCm, 1.0f)
        * FMath::Tan(FMath::DegreesToRadians(CurrentRearSteerAngleDegrees));
    FRotator NewRotation = GetActorRotation();
    NewRotation.Yaw += FMath::RadiansToDegrees(BodyYawRateRadians) * DeltaSeconds;
    NewRotation.Normalize();
    SetActorRotation(NewRotation, ETeleportType::None);
    const FVector TravelDirection = NewRotation.Vector().GetSafeNormal2D()
        * TravelDirectionSign;
    const float DistanceToCurrentPoint = FVector::Dist2D(
        Current, RuntimePath[RuntimePathIndex]);
    const float Travel = FMath::Min(DistanceToCurrentPoint,
        CurrentSpeedCmPerSecond * DeltaSeconds);
    const FVector DesiredLocation = Current + TravelDirection * Travel;
    FHitResult Hit;
    SetActorLocation(DesiredLocation, true, &Hit, ETeleportType::None);
    if (Hit.bBlockingHit)
    {
        if (Cast<ALBCompactStillageFLT>(Hit.GetActor()))
        {
            bWaitingForTraffic = true;
            TrafficWaitSeconds += DeltaSeconds;
            CurrentSpeedCmPerSecond = FMath::FInterpConstantTo(CurrentSpeedCmPerSecond,
                0.0f, DeltaSeconds, DecelerationCmPerSecondSquared * 1.5f);
            UpdatePresentationState();
            return;
        }
        UE_LOG(LogTemp, Warning,
            TEXT("Stillage FLT %s route collision during phase %d with actor %s component %s at %s"),
            *UnitId.ToString(), static_cast<int32>(Phase), *GetNameSafe(Hit.GetActor()),
            *GetNameSafe(Hit.GetComponent()), *Hit.ImpactPoint.ToCompactString());
        LatchFault(ELBCompactStillageFLTFault::RouteCollision);
        return;
    }
    if (bWaitingForTraffic)
    {
        bWaitingForTraffic = false;
        TrafficWaitSeconds = 0.0f;
        UpdatePresentationState();
    }
}

void ALBCompactStillageFLT::ArriveAtRouteDestination()
{
    RuntimePath.Reset();
    RuntimePathIndex = INDEX_NONE;
    CurrentSpeedCmPerSecond = 0.0f;
    bReversingTravel = false;
    switch (Phase)
    {
    case ELBCompactStillageFLTPhase::TravelToPickup:
        EnterPhase(ELBCompactStillageFLTPhase::PickupDockProving);
        break;
    case ELBCompactStillageFLTPhase::TravelToDropoff:
        EnterPhase(ELBCompactStillageFLTPhase::DropoffDockProving);
        break;
    case ELBCompactStillageFLTPhase::ReturningToBerth:
        CompleteJob(true);
        break;
    default:
        LatchFault(ELBCompactStillageFLTFault::RouteUnavailable);
        break;
    }
}

void ALBCompactStillageFLT::TickHandling(const float DeltaSeconds)
{
    switch (Phase)
    {
    case ELBCompactStillageFLTPhase::PickupDockProving:
        if (PhaseElapsedSeconds >= DockProveSeconds)
        {
            bCarryingStillage = true;
            bCarriedStillageFull = ActiveJob.JobType == ELBStillageFLTJobType::FullStillageToWeld;
            CarriedStillageId = ActiveJob.StillageId;
            ApplyLoadFootprint();
            EnterPhase(ELBCompactStillageFLTPhase::RaisingLoad);
        }
        break;
    case ELBCompactStillageFLTPhase::RaisingLoad:
        CarriageLiftCm = FMath::FInterpConstantTo(CarriageLiftCm,
            TransportLiftHeightCm, DeltaSeconds, LiftSpeedCmPerSecond);
        ApplyArticulation();
        if (FMath::IsNearlyEqual(CarriageLiftCm, TransportLiftHeightCm, 0.05f)
            && !PlanRouteTo(ActiveJob.DropoffServicePoint,
                ELBCompactStillageFLTPhase::TravelToDropoff))
        {
            LatchFault(ELBCompactStillageFLTFault::RouteUnavailable);
        }
        break;
    case ELBCompactStillageFLTPhase::DropoffDockProving:
        if (PhaseElapsedSeconds >= DockProveSeconds)
        {
            if (!IsAlignedWithTargetStackPad())
            {
                LatchFault(ELBCompactStillageFLTFault::StackLocatorMisaligned);
                break;
            }
            EnterPhase(ELBCompactStillageFLTPhase::RaisingToStackTier);
        }
        break;
    case ELBCompactStillageFLTPhase::RaisingToStackTier:
    {
        if (!IsAlignedWithTargetStackPad())
        {
            LatchFault(ELBCompactStillageFLTFault::StackLocatorMisaligned);
            break;
        }
        const float TargetHeight = GetForkPlacementHeightForTier(ActiveJob.TargetStackTier);
        if (TargetHeight < 0.0f)
        {
            LatchFault(ELBCompactStillageFLTFault::InvalidJob);
            break;
        }
        CarriageLiftCm = FMath::FInterpConstantTo(CarriageLiftCm,
            TargetHeight, DeltaSeconds, LiftSpeedCmPerSecond);
        ApplyArticulation();
        if (FMath::IsNearlyEqual(CarriageLiftCm, TargetHeight, 0.05f))
        {
            EnterPhase(ELBCompactStillageFLTPhase::StackLocatorProving);
        }
        break;
    }
    case ELBCompactStillageFLTPhase::StackLocatorProving:
        if (!IsAlignedWithTargetStackPad())
        {
            LatchFault(ELBCompactStillageFLTFault::StackLocatorMisaligned);
            break;
        }
        if (PhaseElapsedSeconds >= StackLocatorProveSeconds)
        {
            if (!bDeliveryEventEmitted)
            {
                bDeliveryEventEmitted = true;
                OnStillageDelivered.Broadcast(UnitId, ActiveJobId,
                    CarriedStillageId, bCarriedStillageFull);
            }
            bCarryingStillage = false;
            bCarriedStillageFull = false;
            CarriedStillageId = NAME_None;
            ApplyLoadFootprint();
            EnterPhase(ELBCompactStillageFLTPhase::LoweringLoad);
        }
        break;
    case ELBCompactStillageFLTPhase::LoweringLoad:
        CarriageLiftCm = FMath::FInterpConstantTo(CarriageLiftCm,
            ForkEntryHeightCm, DeltaSeconds, LiftSpeedCmPerSecond);
        ApplyArticulation();
        if (FMath::IsNearlyEqual(CarriageLiftCm, ForkEntryHeightCm, 0.05f))
        {
            if (!bDeliveryEventEmitted || bCarryingStillage)
            {
                LatchFault(ELBCompactStillageFLTFault::InvalidJob);
                break;
            }
            if (!PlanRouteTo(HomeBerth, ELBCompactStillageFLTPhase::ReturningToBerth))
            {
                LatchFault(ELBCompactStillageFLTFault::RouteUnavailable);
            }
        }
        break;
    default:
        LatchFault(ELBCompactStillageFLTFault::InvalidJob);
        break;
    }
}

void ALBCompactStillageFLT::CompleteJob(const bool bSucceeded)
{
    const FName CompletedJobId = ActiveJobId;
    RuntimePath.Reset();
    RuntimePathIndex = INDEX_NONE;
    CurrentSpeedCmPerSecond = 0.0f;
    bReversingTravel = false;
    bWaitingForTraffic = false;
    ActiveJobId = NAME_None;
    ActiveJob = FLBStillageFLTJob();
    ActiveFault = ELBCompactStillageFLTFault::None;
    EnterPhase(ELBCompactStillageFLTPhase::Parked);
    if (!CompletedJobId.IsNone())
    {
        OnJobFinished.Broadcast(UnitId, CompletedJobId, bSucceeded);
    }
}

void ALBCompactStillageFLT::EnterPhase(const ELBCompactStillageFLTPhase NewPhase)
{
    Phase = NewPhase;
    PhaseElapsedSeconds = 0.0f;
    UpdatePresentationState();
}

void ALBCompactStillageFLT::LatchFault(const ELBCompactStillageFLTFault Fault)
{
    CurrentSpeedCmPerSecond = 0.0f;
    ActiveFault = Fault;
    RuntimePath.Reset();
    RuntimePathIndex = INDEX_NONE;
    bReversingTravel = false;
    bWaitingForTraffic = false;
    EnterPhase(ELBCompactStillageFLTPhase::Fault);
}

bool ALBCompactStillageFLT::IsTravelPhase(const ELBCompactStillageFLTPhase Candidate) const
{
    return Candidate == ELBCompactStillageFLTPhase::TravelToPickup
        || Candidate == ELBCompactStillageFLTPhase::TravelToDropoff
        || Candidate == ELBCompactStillageFLTPhase::ReturningToBerth;
}

void ALBCompactStillageFLT::ApplyArticulation()
{
    CarriageLiftCm = FMath::Clamp(CarriageLiftCm, 0.0f, MaximumCarriageTravelCm);
    // Honest triplex kinematics: the carriage takes its finite free lift first,
    // then two separate nested mast stages extend. No stage mesh is stretched.
    const float FreeCarriageTravel = FMath::Min(CarriageLiftCm, FreeCarriageTravelCm);
    const float TelescopicTravel = FMath::Max(0.0f, CarriageLiftCm - FreeCarriageTravel);
    const float FirstStageTravel = FMath::Min(
        TelescopicTravel * 0.5f, FirstTelescopicStageTravelCm);
    const float SecondStageTravel = FMath::Min(
        TelescopicTravel - FirstStageTravel, SecondTelescopicStageTravelCm);
    if (InnerMastMover)
    {
        InnerMastMover->SetRelativeLocation(FVector(0.0f, 0.0f, FirstStageTravel));
    }
    if (SecondMastMover)
    {
        SecondMastMover->SetRelativeLocation(FVector(0.0f, 0.0f, SecondStageTravel));
    }
    if (CarriageMover)
    {
        CarriageMover->SetRelativeLocation(
            FVector(-15.0f, 0.0f, 28.0f + FreeCarriageTravel));
    }
    if (LiftRodMover)
    {
        LiftRodMover->SetRelativeLocation(FVector(0.0f, 0.0f,
            FMath::Min(CarriageLiftCm * 0.5f, 145.0f)));
    }
    if (RearSteeringPivot)
    {
        RearSteeringPivot->SetRelativeRotation(
            FRotator(0.0f, CurrentRearSteerAngleDegrees, 0.0f));
    }
    if (MastTiltRoot)
    {
        const bool bLoadedTravel = bCarryingStillage && IsTravelPhase(Phase);
        MastTiltRoot->SetRelativeRotation(FRotator(bLoadedTravel ? -2.0f : 0.0f, 0.0f, 0.0f));
    }
}

void ALBCompactStillageFLT::ApplyLoadFootprint()
{
    const FVector2D LoadExtent = ValidateJob(ActiveJob)
        ? ActiveJob.StillageHalfExtentCm : FVector2D(85.0f, 155.0f);
    const float SweepAllowance = GetOutwardSweepAllowanceCm();
    const FVector Extent = bCarryingStillage
        ? FVector(FMath::Max(VehicleHalfLengthCm, LoadExtent.X),
            FMath::Max(VehicleHalfWidthCm, LoadExtent.Y) + SweepAllowance,
            VehicleHalfHeightCm)
        : FVector(VehicleHalfLengthCm, VehicleHalfWidthCm + SweepAllowance,
            VehicleHalfHeightCm);
    if (CollisionRoot)
    {
        CollisionRoot->SetBoxExtent(Extent, true);
    }
    if (CarriedStillageVisual)
    {
        CarriedStillageVisual->SetRelativeScale3D(
            FVector(LoadExtent.X / 50.0f, LoadExtent.Y / 50.0f, 0.68f));
        CarriedStillageVisual->SetVisibility(bCarryingStillage, true);
    }
    ApplyArticulation();
}

void ALBCompactStillageFLT::UpdatePresentationState()
{
    if (StatusBeacon)
    {
        ELBStatusBeaconState BeaconState = ELBStatusBeaconState::Idle;
        if (Phase == ELBCompactStillageFLTPhase::Fault)
        {
            BeaconState = ELBStatusBeaconState::Fault;
        }
        else if (IsTravelPhase(Phase))
        {
            BeaconState = bWaitingForTraffic
                ? ELBStatusBeaconState::Waiting : ELBStatusBeaconState::Moving;
        }
        else if (Phase != ELBCompactStillageFLTPhase::Parked)
        {
            BeaconState = ELBStatusBeaconState::Running;
        }
        StatusBeacon->SetStatus(BeaconState);
    }
    const bool bWorkLightsOn = Phase != ELBCompactStillageFLTPhase::Parked
        && Phase != ELBCompactStillageFLTPhase::Fault;
    if (LeftMastWorkLight) LeftMastWorkLight->SetVisibility(bWorkLightsOn, true);
    if (RightMastWorkLight) RightMastWorkLight->SetVisibility(bWorkLightsOn, true);
    ApplyArticulation();
}

bool ALBCompactStillageFLT::CaptureSaveState(FLBCompactStillageFLTSaveState& OutState) const
{
    if (UnitId.IsNone())
    {
        return false;
    }
    OutState = FLBCompactStillageFLTSaveState();
    OutState.UnitId = UnitId;
    OutState.Phase = Phase;
    OutState.Fault = ActiveFault;
    OutState.VehicleTransform = GetActorTransform();
    OutState.HomeBerth = HomeBerth;
    OutState.CurrentSpeedCmPerSecond = CurrentSpeedCmPerSecond;
    OutState.CarriageLiftCm = CarriageLiftCm;
    OutState.RearSteerAngleDegrees = CurrentRearSteerAngleDegrees;
    OutState.bCarryingStillage = bCarryingStillage;
    OutState.bCarriedStillageFull = bCarriedStillageFull;
    OutState.CarriedStillageId = CarriedStillageId;
    OutState.ActiveJobId = ActiveJobId;
    OutState.bDeliveryEventEmitted = bDeliveryEventEmitted;
    return true;
}

bool ALBCompactStillageFLT::RestoreSaveState(const FLBCompactStillageFLTSaveState& InState)
{
    const bool bLoadIdentityValid = InState.bCarryingStillage
        ? !InState.CarriedStillageId.IsNone() : InState.CarriedStillageId.IsNone();
    if (InState.Version != 1 || InState.UnitId.IsNone()
        || (!UnitId.IsNone() && UnitId != InState.UnitId)
        || !IsKnownPhaseValue(InState.Phase) || !IsKnownFaultValue(InState.Fault)
        || !IsFiniteTransform(InState.VehicleTransform) || !IsFiniteVector(InState.HomeBerth)
        || !FMath::IsFinite(InState.CurrentSpeedCmPerSecond)
        || InState.CurrentSpeedCmPerSecond < 0.0f
        || InState.CurrentSpeedCmPerSecond > EmptyMaximumSpeedCmPerSecond + 1.0f
        || !FMath::IsFinite(InState.CarriageLiftCm)
        || InState.CarriageLiftCm < 0.0f || InState.CarriageLiftCm > MaximumCarriageTravelCm
        || (IsTravelPhase(InState.Phase) && InState.CarriageLiftCm
            > MaximumPermittedTravelLiftCm + 0.05f)
        || !FMath::IsFinite(InState.RearSteerAngleDegrees)
        || FMath::Abs(InState.RearSteerAngleDegrees) > MaximumRearSteerAngleDegrees + 0.1f
        || !bLoadIdentityValid
        || (InState.bCarriedStillageFull && !InState.bCarryingStillage)
        || (InState.Phase == ELBCompactStillageFLTPhase::Parked && !InState.ActiveJobId.IsNone())
        || (InState.Phase != ELBCompactStillageFLTPhase::Parked
            && InState.Phase != ELBCompactStillageFLTPhase::Fault
            && InState.ActiveJobId.IsNone()))
    {
        return false;
    }

    UnitId = InState.UnitId;
    Phase = InState.Phase;
    ActiveFault = InState.Fault;
    HomeBerth = InState.HomeBerth;
    CurrentSpeedCmPerSecond = InState.CurrentSpeedCmPerSecond;
    CarriageLiftCm = InState.CarriageLiftCm;
    CurrentRearSteerAngleDegrees = InState.RearSteerAngleDegrees;
    bCarryingStillage = InState.bCarryingStillage;
    bCarriedStillageFull = InState.bCarriedStillageFull;
    CarriedStillageId = InState.CarriedStillageId;
    ActiveJobId = InState.ActiveJobId;
    bDeliveryEventEmitted = InState.bDeliveryEventEmitted;
    RuntimePath.Reset();
    RuntimePathIndex = INDEX_NONE;
    bReversingTravel = false;
    bWaitingForTraffic = false;
    SetActorTransform(InState.VehicleTransform, false, nullptr, ETeleportType::None);
    ApplyLoadFootprint();
    UpdatePresentationState();
    return true;
}
