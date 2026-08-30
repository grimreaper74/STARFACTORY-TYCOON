#include "LBInboundArticulatedCarrierActor.h"

#include "Components/BoxComponent.h"
#include "Components/SceneComponent.h"
#include "Engine/World.h"

#if WITH_DEV_AUTOMATION_TESTS
#include "Misc/AutomationTest.h"
#endif

namespace LBInboundArticulatedCarrierPrivate
{
    constexpr float PoseTolerance = 0.01f;
    constexpr float MinimumTrackingVectorCm = 5.0f;

    bool IsFiniteTransform(const FTransform& Transform)
    {
        return Transform.IsValid() && !Transform.ContainsNaN();
    }
}

ALBInboundArticulatedCarrierActor::ALBInboundArticulatedCarrierActor()
{
    PrimaryActorTick.bCanEverTick = false;
    SetActorEnableCollision(true);

    SceneRoot = CreateDefaultSubobject<USceneComponent>(TEXT("SceneRoot"));
    SetRootComponent(SceneRoot);
    SceneRoot->SetMobility(EComponentMobility::Movable);

    TractorAuthorityProxy = CreateDefaultSubobject<UBoxComponent>(TEXT("IN01A_TractorAuthorityProxy"));
    TractorAuthorityProxy->SetupAttachment(SceneRoot);
    TractorAuthorityProxy->SetBoxExtent(FVector(
        TractorLengthCm * 0.5f, TractorWidthCm * 0.5f, AuthorityHeightCm * 0.5f));
    ConfigureAuthorityProxy(TractorAuthorityProxy);

    TractorPresentationAnchor = CreateDefaultSubobject<USceneComponent>(TEXT("IN01A_TractorPresentationAnchor"));
    TractorPresentationAnchor->SetupAttachment(SceneRoot);
    TractorPresentationAnchor->SetMobility(EComponentMobility::Movable);

    TractorHitch = CreateDefaultSubobject<USceneComponent>(TEXT("PVT_IN01_TractorHitchYaw"));
    TractorHitch->SetupAttachment(SceneRoot);
    TractorHitch->SetRelativeLocation(FVector(TractorHitchLocalXCm, 0.0f, 0.0f));
    TractorHitch->SetMobility(EComponentMobility::Movable);

    TrailerYawPivot = CreateDefaultSubobject<USceneComponent>(TEXT("PVT_IN01_TrailerYaw"));
    TrailerYawPivot->SetupAttachment(TractorHitch);
    TrailerYawPivot->SetRelativeTransform(FTransform::Identity);
    TrailerYawPivot->SetMobility(EComponentMobility::Movable);

    TrailerBodyCentre = CreateDefaultSubobject<USceneComponent>(TEXT("IN01B_TrailerBodyCentre"));
    TrailerBodyCentre->SetupAttachment(TrailerYawPivot);
    TrailerBodyCentre->SetRelativeLocation(FVector(-TrailerHitchLocalXCm, 0.0f, 0.0f));
    TrailerBodyCentre->SetMobility(EComponentMobility::Movable);

    TrailerAuthorityProxy = CreateDefaultSubobject<UBoxComponent>(TEXT("IN01B_TrailerAuthorityProxy"));
    TrailerAuthorityProxy->SetupAttachment(TrailerBodyCentre);
    TrailerAuthorityProxy->SetBoxExtent(FVector(
        TrailerLengthCm * 0.5f, TrailerWidthCm * 0.5f, AuthorityHeightCm * 0.5f));
    ConfigureAuthorityProxy(TrailerAuthorityProxy);

    TrailerPresentationAnchor = CreateDefaultSubobject<USceneComponent>(TEXT("IN01B_TrailerPresentationAnchor"));
    TrailerPresentationAnchor->SetupAttachment(TrailerBodyCentre);
    TrailerPresentationAnchor->SetMobility(EComponentMobility::Movable);

    TrailerCargoRoot = CreateDefaultSubobject<USceneComponent>(TEXT("IN01B_SeparateCargoRoot"));
    TrailerCargoRoot->SetupAttachment(TrailerBodyCentre);
    TrailerCargoRoot->SetMobility(EComponentMobility::Movable);

    Tags.AddUnique(GetAuthorityTag());
    Tags.AddUnique(TEXT("LB.Provenance.NativeCode"));
    Tags.AddUnique(TEXT("LB.Inbound.GameplayAuthorityProxy"));
}

void ALBInboundArticulatedCarrierActor::ConfigureAuthorityProxy(UBoxComponent* Proxy)
{
    if (!Proxy)
    {
        return;
    }
    Proxy->SetMobility(EComponentMobility::Movable);
    Proxy->SetCollisionProfileName(TEXT("BlockAllDynamic"));
    Proxy->SetCollisionEnabled(ECollisionEnabled::QueryAndPhysics);
    Proxy->SetGenerateOverlapEvents(false);
    Proxy->SetCanEverAffectNavigation(false);
    Proxy->SetHiddenInGame(true, true);
}

bool ALBInboundArticulatedCarrierActor::IsValidPlanarPose(
    const FTransform& Transform, FString& OutReason) const
{
    if (!LBInboundArticulatedCarrierPrivate::IsFiniteTransform(Transform))
    {
        OutReason = TEXT("ARTICULATED CARRIER REJECTED NON-FINITE TRACTOR POSE");
        return false;
    }
    const FRotator Rotation = Transform.Rotator();
    if (FMath::Abs(Rotation.Pitch) > LBInboundArticulatedCarrierPrivate::PoseTolerance
        || FMath::Abs(Rotation.Roll) > LBInboundArticulatedCarrierPrivate::PoseTolerance)
    {
        OutReason = TEXT("ARTICULATED CARRIER ACCEPTS PLANAR YAW POSES ONLY");
        return false;
    }
    if (!Transform.GetScale3D().Equals(FVector::OneVector,
        LBInboundArticulatedCarrierPrivate::PoseTolerance))
    {
        OutReason = TEXT("ARTICULATED CARRIER COLLISION AUTHORITY REQUIRES UNIT SCALE");
        return false;
    }
    return true;
}

void ALBInboundArticulatedCarrierActor::ApplyTrailerRelativeYawUnchecked(
    const float NewRelativeYawDegrees)
{
    TrailerYawPivot->SetRelativeRotation(FRotator(0.0f, NewRelativeYawDegrees, 0.0f),
        false, nullptr, ETeleportType::TeleportPhysics);
}

bool ALBInboundArticulatedCarrierActor::SetTrailerRelativeYawDegrees(
    const float NewRelativeYawDegrees, FString& OutReason)
{
    if (!IsTrailerRelativeYawWithinLimits(NewRelativeYawDegrees))
    {
        OutReason = FString::Printf(
            TEXT("ARTICULATED CARRIER YAW %.2f EXCEEDS PROVED LIMIT %.2f"),
            NewRelativeYawDegrees, MaximumArticulationDegrees);
        return false;
    }
    ApplyTrailerRelativeYawUnchecked(NewRelativeYawDegrees);
    OutReason = TEXT("ARTICULATED CARRIER TRAILER YAW APPLIED");
    return true;
}

bool ALBInboundArticulatedCarrierActor::IsTrailerRelativeYawWithinLimits(
    const float CandidateRelativeYawDegrees) const
{
    return FMath::IsFinite(CandidateRelativeYawDegrees)
        && FMath::Abs(CandidateRelativeYawDegrees) <= MaximumArticulationDegrees;
}

float ALBInboundArticulatedCarrierActor::GetTrailerRelativeYawDegrees() const
{
    return TrailerYawPivot ? FMath::UnwindDegrees(
        TrailerYawPivot->GetRelativeRotation().Yaw) : 0.0f;
}

FVector ALBInboundArticulatedCarrierActor::GetTractorHitchWorldLocation() const
{
    return TractorHitch ? TractorHitch->GetComponentLocation() : GetActorLocation();
}

FVector ALBInboundArticulatedCarrierActor::GetTrailerBodyCentreWorldLocation() const
{
    return TrailerBodyCentre ? TrailerBodyCentre->GetComponentLocation() : GetActorLocation();
}

bool ALBInboundArticulatedCarrierActor::ResetStraightAtTractorPose(
    const FTransform& NewTractorWorldTransform, FString& OutReason)
{
    if (!IsValidPlanarPose(NewTractorWorldTransform, OutReason))
    {
        return false;
    }
    SetActorTransform(NewTractorWorldTransform, false, nullptr,
        ETeleportType::TeleportPhysics);
    ApplyTrailerRelativeYawUnchecked(0.0f);
    OutReason = TEXT("ARTICULATED CARRIER RESET STRAIGHT AT TRACTOR POSE");
    return true;
}

bool ALBInboundArticulatedCarrierActor::AdvanceTractorPoseAndSolveTrailer(
    const FTransform& NewTractorWorldTransform, FString& OutReason)
{
    if (!IsValidPlanarPose(NewTractorWorldTransform, OutReason))
    {
        return false;
    }
    const FVector CurrentTractorLocation = GetActorLocation();
    const FVector NewTractorLocation = NewTractorWorldTransform.GetLocation();
    if (FVector::Dist2D(CurrentTractorLocation, NewTractorLocation) > MaximumSolverStepCm)
    {
        OutReason = TEXT("ARTICULATED CARRIER SOLVER STEP EXCEEDS TUNNEL-SAFE LIMIT");
        return false;
    }

    const FVector PreviousTrailerCentre = GetTrailerBodyCentreWorldLocation();
    const FVector NewHitch = NewTractorWorldTransform.TransformPosition(
        FVector(TractorHitchLocalXCm, 0.0f, 0.0f));
    FVector TrackingVector = PreviousTrailerCentre - NewHitch;
    TrackingVector.Z = 0.0f;
    if (TrackingVector.SizeSquared2D()
        < FMath::Square(LBInboundArticulatedCarrierPrivate::MinimumTrackingVectorCm))
    {
        OutReason = TEXT("ARTICULATED CARRIER LOST ITS TRAILER TRACKING VECTOR");
        return false;
    }

    const float DesiredTrailerWorldYaw = TrackingVector.Rotation().Yaw;
    const float TractorWorldYaw = NewTractorWorldTransform.Rotator().Yaw;
    const float DesiredRelativeYaw = FMath::FindDeltaAngleDegrees(
        TractorWorldYaw, DesiredTrailerWorldYaw);
    if (FMath::Abs(DesiredRelativeYaw) > MaximumArticulationDegrees)
    {
        OutReason = TEXT("ARTICULATED CARRIER STEP WOULD JACK-KNIFE THE TRAILER");
        return false;
    }

    SetActorTransform(NewTractorWorldTransform, false, nullptr,
        ETeleportType::TeleportPhysics);
    ApplyTrailerRelativeYawUnchecked(DesiredRelativeYaw);
    OutReason = TEXT("ARTICULATED CARRIER TRACTOR ADVANCED AND TRAILER SOLVED");
    return true;
}

FName ALBInboundArticulatedCarrierActor::GetAuthorityTag()
{
    return FName(TEXT("LB.Inbound.ArticulatedCarrier.IN01.v001"));
}

#if WITH_DEV_AUTOMATION_TESTS

IMPLEMENT_SIMPLE_AUTOMATION_TEST(
    FLBInboundArticulatedCarrierGeometryTest,
    "LineBoss.PressShop.Inbound.ArticulatedCarrier.ExactRegisteredGeometry",
    EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)

bool FLBInboundArticulatedCarrierGeometryTest::RunTest(const FString& Parameters)
{
    (void)Parameters;
    UWorld* World = UWorld::CreateWorld(EWorldType::Game, false,
        TEXT("LBInboundArticulatedCarrierGeometryTest"));
    ALBInboundArticulatedCarrierActor* Carrier = World
        ? World->SpawnActor<ALBInboundArticulatedCarrierActor>() : nullptr;
    if (!TestNotNull(TEXT("Articulated inbound carrier spawns"), Carrier))
    {
        if (World) World->DestroyWorld(false);
        return false;
    }

    TestTrue(TEXT("Stable authority tag is present"),
        Carrier->ActorHasTag(ALBInboundArticulatedCarrierActor::GetAuthorityTag()));
    TestTrue(TEXT("Tractor proxy exists"), Carrier->GetTractorAuthorityProxy() != nullptr);
    TestTrue(TEXT("Trailer proxy exists"), Carrier->GetTrailerAuthorityProxy() != nullptr);
    if (Carrier->GetTractorAuthorityProxy() && Carrier->GetTrailerAuthorityProxy())
    {
        const FVector TractorExtent = Carrier->GetTractorAuthorityProxy()->GetUnscaledBoxExtent();
        const FVector TrailerExtent = Carrier->GetTrailerAuthorityProxy()->GetUnscaledBoxExtent();
        TestTrue(TEXT("Tractor proxy is exact 4.80 x 2.55 m footprint"),
            FMath::IsNearlyEqual(TractorExtent.X * 2.0f, 480.0f)
                && FMath::IsNearlyEqual(TractorExtent.Y * 2.0f, 255.0f));
        TestTrue(TEXT("Trailer proxy is exact 12.20 x 2.55 m footprint"),
            FMath::IsNearlyEqual(TrailerExtent.X * 2.0f, 1220.0f)
                && FMath::IsNearlyEqual(TrailerExtent.Y * 2.0f, 255.0f));
        TestEqual(TEXT("Tractor collision is authoritative"),
            Carrier->GetTractorAuthorityProxy()->GetCollisionEnabled(),
            ECollisionEnabled::QueryAndPhysics);
        TestEqual(TEXT("Trailer collision is authoritative"),
            Carrier->GetTrailerAuthorityProxy()->GetCollisionEnabled(),
            ECollisionEnabled::QueryAndPhysics);
    }
    TestTrue(TEXT("Parked body centres are exactly 8.00 m apart"),
        FMath::IsNearlyEqual(FVector::Dist2D(Carrier->GetActorLocation(),
            Carrier->GetTrailerBodyCentreWorldLocation()), 800.0f));

    FString Reason;
    TestTrue(TEXT("A proved 35-degree hitch yaw applies"),
        Carrier->SetTrailerRelativeYawDegrees(35.0f, Reason));
    TestTrue(TEXT("Applied hitch yaw is observable"),
        FMath::IsNearlyEqual(Carrier->GetTrailerRelativeYawDegrees(), 35.0f));
    TestFalse(TEXT("A jack-knifed manual yaw fails closed"),
        Carrier->SetTrailerRelativeYawDegrees(88.0f, Reason));
    TestTrue(TEXT("Rejected yaw does not mutate the trailer"),
        FMath::IsNearlyEqual(Carrier->GetTrailerRelativeYawDegrees(), 35.0f));

    Carrier->Destroy();
    World->DestroyWorld(false);
    return true;
}

IMPLEMENT_SIMPLE_AUTOMATION_TEST(
    FLBInboundArticulatedCarrierMotionTest,
    "LineBoss.PressShop.Inbound.ArticulatedCarrier.ForwardKinematicHitch",
    EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)

bool FLBInboundArticulatedCarrierMotionTest::RunTest(const FString& Parameters)
{
    (void)Parameters;
    UWorld* World = UWorld::CreateWorld(EWorldType::Game, false,
        TEXT("LBInboundArticulatedCarrierMotionTest"));
    ALBInboundArticulatedCarrierActor* Carrier = World
        ? World->SpawnActor<ALBInboundArticulatedCarrierActor>() : nullptr;
    if (!TestNotNull(TEXT("Articulated motion fixture spawns"), Carrier))
    {
        if (World) World->DestroyWorld(false);
        return false;
    }

    FString Reason;
    TestTrue(TEXT("Fixture starts from a proved straight pose"),
        Carrier->ResetStraightAtTractorPose(FTransform::Identity, Reason));
    TestTrue(TEXT("A straight one-metre pull advances"),
        Carrier->AdvanceTractorPoseAndSolveTrailer(
            FTransform(FRotator::ZeroRotator, FVector(-100.0f, 0.0f, 0.0f)), Reason));
    TestTrue(TEXT("Straight pull retains zero articulation"),
        FMath::IsNearlyZero(Carrier->GetTrailerRelativeYawDegrees(), 0.01f));
    const FTransform CornerPose(FRotator::ZeroRotator,
        FVector(-100.0f, -100.0f, 0.0f));
    TestTrue(TEXT("A bounded corner step solves"),
        Carrier->AdvanceTractorPoseAndSolveTrailer(CornerPose, Reason));
    TestTrue(TEXT("Corner step produces trailer articulation"),
        FMath::Abs(Carrier->GetTrailerRelativeYawDegrees()) > 1.0f);
    const FTransform BeforeRejected = Carrier->GetActorTransform();
    TestFalse(TEXT("A large tunnelling step fails closed"),
        Carrier->AdvanceTractorPoseAndSolveTrailer(
            FTransform(FRotator::ZeroRotator, FVector(1000.0f, 0.0f, 0.0f)), Reason));
    TestTrue(TEXT("Rejected solver step leaves tractor unchanged"),
        Carrier->GetActorTransform().Equals(BeforeRejected));

    Carrier->Destroy();
    World->DestroyWorld(false);
    return true;
}

#endif
