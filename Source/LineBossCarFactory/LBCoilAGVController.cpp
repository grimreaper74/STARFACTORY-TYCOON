#include "LBCoilAGVController.h"

#include "EngineUtils.h"
#include "Engine/StaticMesh.h"
#include "Components/SceneComponent.h"
#include "Components/StaticMeshComponent.h"
#include "Components/BoxComponent.h"
#include "UObject/ConstructorHelpers.h"
#include "UObject/UObjectGlobals.h"
#include "LBFactoryAGVInfrastructure.h"
#include "LBFactoryBuildMachine.h"
#include "LBStatusBeaconComponent.h"

namespace
{
    constexpr TCHAR NativeOneFactoryChassisPath[] = TEXT("/Game/LineBoss/IndustrialKit/MaterialHandling/CoilAGV/Candidate_v001/SM_LB_CoilAGV_Chassis_Candidate_v001.SM_LB_CoilAGV_Chassis_Candidate_v001");
    constexpr TCHAR NativeOneFactoryLiftDeckPath[] = TEXT("/Game/LineBoss/IndustrialKit/MaterialHandling/CoilAGV/Candidate_v001/SM_LB_CoilAGV_LiftDeck_Candidate_v001.SM_LB_CoilAGV_LiftDeck_Candidate_v001");
    constexpr TCHAR NativeOneFactoryLoadPath[] = TEXT("/Game/LineBoss/IndustrialKit/MaterialHandling/MasterCoil/Candidate_v005/SM_LB_MasterCoil_Candidate_v005.SM_LB_MasterCoil_Candidate_v005");

    bool HasExactMeshPath(const UStaticMeshComponent* Component, const TCHAR* ExpectedPath)
    {
        return Component && Component->GetStaticMesh()
            && Component->GetStaticMesh()->GetPathName().Equals(ExpectedPath, ESearchCase::CaseSensitive);
    }

constexpr float InboundRouteCoverageToleranceCm = 75.0f;
constexpr float InboundRouteSampleSpacingCm = 100.0f;
constexpr float MinimumRouteLegLengthCm = 25.0f;

bool IsFiniteCoilAGVVector(const FVector& Value)
{
    return FMath::IsFinite(Value.X) && FMath::IsFinite(Value.Y) && FMath::IsFinite(Value.Z);
}

float DirectionYawDegrees(const FVector& Direction)
{
    return FMath::RadiansToDegrees(FMath::Atan2(Direction.Y, Direction.X));
}

FVector QuadraticBezier(const FVector& Start, const FVector& Control,
    const FVector& End, const float Alpha)
{
    const float OneMinusAlpha = 1.0f - Alpha;
    return OneMinusAlpha * OneMinusAlpha * Start
        + 2.0f * OneMinusAlpha * Alpha * Control + Alpha * Alpha * End;
}

FVector QuadraticBezierTangent(const FVector& Start, const FVector& Control,
    const FVector& End, const float Alpha)
{
    return 2.0f * (1.0f - Alpha) * (Control - Start)
        + 2.0f * Alpha * (End - Control);
}

bool SegmentIntersectsExpandedMachineEnvelope(const FVector& WorldStart,
    const FVector& WorldEnd, const ALBFactoryBuildMachine& Machine,
    const float VehicleRadiusCm, const float ExtraClearanceCm)
{
    FVector LocalStart = Machine.GetActorTransform().InverseTransformPositionNoScale(WorldStart)
        - Machine.GetProtectedEnvelopeRelativeCentre();
    FVector LocalEnd = Machine.GetActorTransform().InverseTransformPositionNoScale(WorldEnd)
        - Machine.GetProtectedEnvelopeRelativeCentre();
    const FVector MachineExtent = Machine.GetProtectedEnvelopeHalfExtent();
    const FVector2D ExpandedExtent(MachineExtent.X + VehicleRadiusCm + ExtraClearanceCm,
        MachineExtent.Y + VehicleRadiusCm + ExtraClearanceCm);
    const FVector2D Start(LocalStart.X, LocalStart.Y);
    const FVector2D End(LocalEnd.X, LocalEnd.Y);
    const FVector2D Delta = End - Start;
    float MinimumAlpha = 0.0f;
    float MaximumAlpha = 1.0f;
    const auto ClipAxis = [&MinimumAlpha, &MaximumAlpha](const float AxisStart,
        const float AxisDelta, const float HalfExtent)
    {
        if (FMath::IsNearlyZero(AxisDelta)) return FMath::Abs(AxisStart) <= HalfExtent;
        float Enter = (-HalfExtent - AxisStart) / AxisDelta;
        float Exit = (HalfExtent - AxisStart) / AxisDelta;
        if (Enter > Exit) Swap(Enter, Exit);
        MinimumAlpha = FMath::Max(MinimumAlpha, Enter);
        MaximumAlpha = FMath::Min(MaximumAlpha, Exit);
        return MinimumAlpha <= MaximumAlpha;
    };
    return ClipAxis(Start.X, Delta.X, ExpandedExtent.X)
        && ClipAxis(Start.Y, Delta.Y, ExpandedExtent.Y);
}

bool IsPointCoveredByRoute(const FVector& WorldPoint,
    const TArray<ALBFactoryAGVInfrastructure*>& RouteSegments)
{
    for (const ALBFactoryAGVInfrastructure* Segment : RouteSegments)
    {
        if (!IsValid(Segment)) continue;
        const FVector Local = Segment->GetActorTransform().InverseTransformPositionNoScale(WorldPoint);
        const FVector HalfExtent = Segment->GetPlacementHalfExtentCm();
        if (FMath::Abs(Local.X) <= HalfExtent.X + InboundRouteCoverageToleranceCm
            && FMath::Abs(Local.Y) <= HalfExtent.Y + InboundRouteCoverageToleranceCm)
        {
            return true;
        }
    }
    return false;
}

bool IsRouteLegContinuouslyCovered(const FVector& Start, const FVector& End,
    const TArray<ALBFactoryAGVInfrastructure*>& RouteSegments)
{
    const float DistanceCm = FVector::Dist2D(Start, End);
    const int32 SampleCount = FMath::Max(1,
        FMath::CeilToInt(DistanceCm / InboundRouteSampleSpacingCm));
    for (int32 SampleIndex = 0; SampleIndex <= SampleCount; ++SampleIndex)
    {
        const float Alpha = static_cast<float>(SampleIndex) / static_cast<float>(SampleCount);
        if (!IsPointCoveredByRoute(FMath::Lerp(Start, End, Alpha), RouteSegments)) return false;
    }
    return true;
}

bool IsValidRouteProfileAssignment(const ELBCoilAGVRouteProfile Profile, const int32 TrainIndex)
{
    switch (Profile)
    {
    case ELBCoilAGVRouteProfile::ManualOrUnassigned:
    case ELBCoilAGVRouteProfile::InboundPR002:
        return TrainIndex == INDEX_NONE;
    case ELBCoilAGVRouteProfile::PressTrainHandoff:
        return FMath::IsWithinInclusive(TrainIndex, 0, 3);
    default:
        return false;
    }
}

bool IsValidRouteGeometry(const FVector& Start, const FVector& Turn, const FVector& Dock)
{
    if (!IsFiniteCoilAGVVector(Start) || !IsFiniteCoilAGVVector(Turn) || !IsFiniteCoilAGVVector(Dock)
        || FVector::Dist2D(Start, Turn) < MinimumRouteLegLengthCm
        || FVector::Dist2D(Turn, Dock) < MinimumRouteLegLengthCm)
    {
        return false;
    }
    return FVector::DotProduct((Turn - Start).GetSafeNormal2D(),
        (Dock - Turn).GetSafeNormal2D()) >= -0.95f;
}

struct FInfrastructureRouteCandidate
{
    ALBFactoryAGVInfrastructure* Wait = nullptr;
    ALBFactoryAGVInfrastructure* Waypoint = nullptr;
    ALBFactoryAGVInfrastructure* Handoff = nullptr;
    float TotalLengthCm = 0.0f;
};

struct FInboundInfrastructureRouteCandidate
{
    ALBFactoryAGVInfrastructure* Wait = nullptr;
    ALBFactoryAGVInfrastructure* Waypoint = nullptr;
    FVector Dock = FVector::ZeroVector;
    float StartAssociationDistanceSquared = 0.0f;
    float TotalLengthCm = 0.0f;
};

void GatherPressTrainRouteCandidates(UWorld* World, const int32 TrainIndex,
    TArray<FInfrastructureRouteCandidate>& OutCandidates)
{
    OutCandidates.Reset();
    if (!World || !FMath::IsWithinInclusive(TrainIndex, 0, 3)) return;

    TArray<ALBFactoryAGVInfrastructure*> WaitPoints;
    TArray<ALBFactoryAGVInfrastructure*> Waypoints;
    TArray<ALBFactoryAGVInfrastructure*> Handoffs;
    TArray<ALBFactoryAGVInfrastructure*> RouteSegments;
    for (TActorIterator<ALBFactoryAGVInfrastructure> It(World); It; ++It)
    {
        if (!IsValid(*It)) continue;
        switch (It->GetInfrastructureType())
        {
        case ELBFactoryAGVInfrastructureType::WaitPoint: WaitPoints.Add(*It); break;
        case ELBFactoryAGVInfrastructureType::RouteWaypoint: Waypoints.Add(*It); break;
        case ELBFactoryAGVInfrastructureType::PressTrainHandoff:
            if (It->GetTrainIndex() == TrainIndex) Handoffs.Add(*It);
            break;
        case ELBFactoryAGVInfrastructureType::AGVRouteSegment: RouteSegments.Add(*It); break;
        default: break;
        }
    }
    if (WaitPoints.IsEmpty() || Waypoints.IsEmpty() || Handoffs.Num() != 1
        || RouteSegments.Num() < 2)
    {
        return;
    }

    ALBFactoryAGVInfrastructure* Handoff = Handoffs[0];
    for (ALBFactoryAGVInfrastructure* Wait : WaitPoints)
    {
        for (ALBFactoryAGVInfrastructure* Waypoint : Waypoints)
        {
            const FVector Start = Wait->GetActorLocation();
            const FVector Turn = Waypoint->GetActorLocation();
            const FVector Dock = Handoff->GetActorLocation();
            if (!IsValidRouteGeometry(Start, Turn, Dock)
                || !IsRouteLegContinuouslyCovered(Start, Turn, RouteSegments)
                || !IsRouteLegContinuouslyCovered(Turn, Dock, RouteSegments))
            {
                continue;
            }
            FInfrastructureRouteCandidate& Candidate = OutCandidates.AddDefaulted_GetRef();
            Candidate.Wait = Wait;
            Candidate.Waypoint = Waypoint;
            Candidate.Handoff = Handoff;
            Candidate.TotalLengthCm = FVector::Dist2D(Start, Turn) + FVector::Dist2D(Turn, Dock);
        }
    }
    OutCandidates.Sort([](const FInfrastructureRouteCandidate& A,
        const FInfrastructureRouteCandidate& B)
    {
        if (!FMath::IsNearlyEqual(A.TotalLengthCm, B.TotalLengthCm))
            return A.TotalLengthCm < B.TotalLengthCm;
        const FString AWait = A.Wait->GetInfrastructureId().ToString();
        const FString BWait = B.Wait->GetInfrastructureId().ToString();
        if (AWait != BWait) return AWait < BWait;
        return A.Waypoint->GetInfrastructureId().ToString()
            < B.Waypoint->GetInfrastructureId().ToString();
    });
}

void GatherInboundRouteCandidates(UWorld* World, ALBFactoryBuildMachine* InboundDock,
    ALBFactoryBuildMachine* PR002Cell,
    TArray<FInboundInfrastructureRouteCandidate>& OutCandidates)
{
    OutCandidates.Reset();
    if (!World || !InboundDock || !PR002Cell
        || InboundDock->GetMachineType() != ELBFactoryBuildMachineType::InboundDeliveryDock
        || PR002Cell->GetMachineType() != ELBFactoryBuildMachineType::CoilWeighInspectionCell
        || !PR002Cell->InputPort)
    {
        return;
    }

    TArray<ALBFactoryAGVInfrastructure*> WaitPoints;
    TArray<ALBFactoryAGVInfrastructure*> Waypoints;
    TArray<ALBFactoryAGVInfrastructure*> RouteSegments;
    for (TActorIterator<ALBFactoryAGVInfrastructure> It(World); It; ++It)
    {
        if (!IsValid(*It)) continue;
        switch (It->GetInfrastructureType())
        {
        case ELBFactoryAGVInfrastructureType::WaitPoint: WaitPoints.Add(*It); break;
        case ELBFactoryAGVInfrastructureType::RouteWaypoint: Waypoints.Add(*It); break;
        case ELBFactoryAGVInfrastructureType::AGVRouteSegment: RouteSegments.Add(*It); break;
        default: break;
        }
    }
    if (WaitPoints.IsEmpty() || Waypoints.IsEmpty() || RouteSegments.Num() < 2) return;

    const FVector Dock = PR002Cell->InputPort->GetComponentLocation();
    const FVector InboundReference = InboundDock->OutputPort
        ? InboundDock->OutputPort->GetComponentLocation() : InboundDock->GetActorLocation();
    for (ALBFactoryAGVInfrastructure* Wait : WaitPoints)
    {
        for (ALBFactoryAGVInfrastructure* Waypoint : Waypoints)
        {
            const FVector Start = Wait->GetActorLocation();
            const FVector Turn = Waypoint->GetActorLocation();
            if (!IsValidRouteGeometry(Start, Turn, Dock)
                || !IsRouteLegContinuouslyCovered(Start, Turn, RouteSegments)
                || !IsRouteLegContinuouslyCovered(Turn, Dock, RouteSegments))
            {
                continue;
            }
            FInboundInfrastructureRouteCandidate& Candidate = OutCandidates.AddDefaulted_GetRef();
            Candidate.Wait = Wait;
            Candidate.Waypoint = Waypoint;
            Candidate.Dock = Dock;
            Candidate.StartAssociationDistanceSquared = FVector::DistSquared2D(Start, InboundReference);
            Candidate.TotalLengthCm = FVector::Dist2D(Start, Turn) + FVector::Dist2D(Turn, Dock);
        }
    }
    OutCandidates.Sort([](const FInboundInfrastructureRouteCandidate& A,
        const FInboundInfrastructureRouteCandidate& B)
    {
        if (!FMath::IsNearlyEqual(A.StartAssociationDistanceSquared,
            B.StartAssociationDistanceSquared))
        {
            return A.StartAssociationDistanceSquared < B.StartAssociationDistanceSquared;
        }
        if (!FMath::IsNearlyEqual(A.TotalLengthCm, B.TotalLengthCm))
            return A.TotalLengthCm < B.TotalLengthCm;
        const FString AWait = A.Wait->GetInfrastructureId().ToString();
        const FString BWait = B.Wait->GetInfrastructureId().ToString();
        if (AWait != BWait) return AWait < BWait;
        return A.Waypoint->GetInfrastructureId().ToString()
            < B.Waypoint->GetInfrastructureId().ToString();
    });
}

float DistanceSquaredToRouteLeg2D(const FVector& Point, const FVector& Start,
    const FVector& End)
{
    const FVector2D A(Start.X, Start.Y);
    const FVector2D B(End.X, End.Y);
    const FVector2D P(Point.X, Point.Y);
    const FVector2D Delta = B - A;
    const float LengthSquared = Delta.SizeSquared();
    const float Alpha = LengthSquared > UE_SMALL_NUMBER
        ? FMath::Clamp(FVector2D::DotProduct(P - A, Delta) / LengthSquared, 0.0f, 1.0f) : 0.0f;
    return FVector2D::DistSquared(P, A + Delta * Alpha);
}

bool IsLegacySavedLocationCompatibleWithRoute(const FLBCoilAGVSaveState& State,
    const FVector& Start, const FVector& Turn, const FVector& Dock)
{
    constexpr float StablePointToleranceCm = 5.0f;
    constexpr float RouteToleranceCm = 200.0f;
    if (State.Phase == ELBCoilAGVPhase::IdleLoaded
        || State.Phase == ELBCoilAGVPhase::AwaitingReload)
    {
        return FVector::Dist2D(State.VehicleLocation, Start) <= StablePointToleranceCm;
    }
    if (State.Phase == ELBCoilAGVPhase::HandoffReady
        || State.Phase == ELBCoilAGVPhase::LowerAfterHandoff)
    {
        return FVector::Dist2D(State.VehicleLocation, Dock) <= StablePointToleranceCm;
    }
    return FMath::Min(DistanceSquaredToRouteLeg2D(State.VehicleLocation, Start, Turn),
        DistanceSquaredToRouteLeg2D(State.VehicleLocation, Turn, Dock))
        <= FMath::Square(RouteToleranceCm);
}
}
ALBCoilAGVController::ALBCoilAGVController()
{
    PrimaryActorTick.bCanEverTick = true;
    SceneRoot = CreateDefaultSubobject<USceneComponent>(TEXT("SceneRoot"));
    SetRootComponent(SceneRoot);
    ApprovedChassisVisual = CreateDefaultSubobject<UStaticMeshComponent>(TEXT("ApprovedChassisVisual"));
    ApprovedChassisVisual->SetupAttachment(SceneRoot);
    ApprovedLiftDeckVisual = CreateDefaultSubobject<UStaticMeshComponent>(TEXT("ApprovedLiftDeckVisual"));
    ApprovedLiftDeckVisual->SetupAttachment(SceneRoot);
    ApprovedLoadVisual = CreateDefaultSubobject<UStaticMeshComponent>(TEXT("ApprovedLoadVisual"));
    ApprovedLoadVisual->SetupAttachment(ApprovedLiftDeckVisual);
    CollisionProxy = CreateDefaultSubobject<UBoxComponent>(TEXT("CollisionProxy"));
    CollisionProxy->SetupAttachment(SceneRoot);
    // Exact untouched-master bounds after its appearance-only +90 degree yaw.
    CollisionProxy->SetRelativeLocation(FVector(-0.0636f, -0.0390f, 0.6163f));
    CollisionProxy->SetBoxExtent(FVector(95.0974f, 72.9841f, 28.5183f));
    CollisionProxy->SetCollisionEnabled(ECollisionEnabled::NoCollision);
    CollisionProxy->SetCollisionResponseToAllChannels(ECR_Block);
    CollisionProxy->SetGenerateOverlapEvents(false);
    CollisionProxy->SetCanEverAffectNavigation(false);
    StatusBeacon = CreateDefaultSubobject<ULBStatusBeaconComponent>(TEXT("CoilAGV_RuntimeStatusBeacon"));
    StatusBeacon->SetupAttachment(SceneRoot);
    StatusBeacon->SetRelativeLocation(FVector(-62.0f, -55.0f, 58.0f));
    StatusBeacon->SetRelativeScale3D(FVector(0.55f));
    StatusBeacon->SetStatus(ELBStatusBeaconState::Idle);
    for (UStaticMeshComponent* Visual : {ApprovedChassisVisual.Get(), ApprovedLiftDeckVisual.Get(), ApprovedLoadVisual.Get()})
    {
        Visual->SetVisibility(false);
        Visual->SetCollisionEnabled(ECollisionEnabled::NoCollision);
        Visual->SetGenerateOverlapEvents(false);
        Visual->SetCanEverAffectNavigation(false);
        Visual->SetMobility(EComponentMobility::Movable);
    }
    static ConstructorHelpers::FObjectFinder<UStaticMesh> Chassis(TEXT("/Game/LineBoss/Runtime/PressShop/CoilAGV/UntouchedControlled_v20260810/SM_Cairnwell_CoilAGV_UntouchedControlled_v20260810.SM_Cairnwell_CoilAGV_UntouchedControlled_v20260810"));
    static ConstructorHelpers::FObjectFinder<UStaticMesh> Coil(TEXT("/Game/LineBoss/Runtime/PressShop/WrappedCoil/Controlled_v20260810/SM_Cairnwell_WrappedCoil_Controlled_v20260810.SM_Cairnwell_WrappedCoil_Controlled_v20260810"));
    if (Chassis.Succeeded()) ApprovedChassisVisual->SetStaticMesh(Chassis.Object);
    if (Coil.Succeeded()) ApprovedLoadVisual->SetStaticMesh(Coil.Object);
    // The untouched master faces local -Y. Rotate only its appearance so route yaw zero
    // points the AGV nose along controller +X; collision uses the already-rotated bounds.
    ApprovedChassisVisual->SetRelativeRotation(FRotator(0.0f, 90.0f, 0.0f));
    // The coil axis and V-cradle are authored in the same source frame. Carry the hidden
    // lift transform through the same yaw so the independently lifted load stays seated.
    ApprovedLiftDeckVisual->SetRelativeRotation(FRotator(0.0f, 90.0f, 0.0f));
    // The repaired wrapped-coil pivot is its bottom face. Blender rays put the untouched
    // cradle valley at 11.45 cm and its cylinder contacts at 13.57 cm. 12.5 cm retains
    // about 1 cm visual clearance without floating the coil.
    ApprovedLoadVisual->SetRelativeLocation(FVector(0.0f, 0.0f, 12.5f));
}

void ALBCoilAGVController::BeginPlay()
{
    Super::BeginPlay();
    DiscoverAndBind();
    UpdateStatusBeacon();
}

bool ALBCoilAGVController::IsNativeOneFactoryPresentationAssetPathAllowed(
    const FString& AssetPath)
{
    // An exact allowlist is intentional. A broad folder/prefix rule could admit a
    // retained generated asset merely because it was copied below a trusted folder.
    return AssetPath.Equals(NativeOneFactoryChassisPath, ESearchCase::CaseSensitive)
        || AssetPath.Equals(NativeOneFactoryLiftDeckPath, ESearchCase::CaseSensitive)
        || AssetPath.Equals(NativeOneFactoryLoadPath, ESearchCase::CaseSensitive);
}

bool ALBCoilAGVController::IsUsingNativeOneFactoryPresentation() const
{
    return bNativeOneFactoryPresentation && bForceOwnedPresentation
        && bUsingOwnedPresentation
        && HasExactMeshPath(ApprovedChassisVisual, NativeOneFactoryChassisPath)
        && HasExactMeshPath(ApprovedLiftDeckVisual, NativeOneFactoryLiftDeckPath)
        && HasExactMeshPath(ApprovedLoadVisual, NativeOneFactoryLoadPath);
}

bool ALBCoilAGVController::ConfigureNativeOneFactoryPresentation(FString& OutReason)
{
    OutReason.Reset();
    const bool bRecoverableLegacyBindingFailure = Phase == ELBCoilAGVPhase::Fault
        && ActiveFault == ELBCoilAGVFault::BindingIncomplete;
    if (!GetWorld()
        || (Phase != ELBCoilAGVPhase::IdleLoaded && !bRecoverableLegacyBindingFailure)
        || !bLoadOwned)
    {
        OutReason = TEXT("NATIVE INBOUND AGV PRESENTATION CAN ONLY BE SELECTED WHILE IDLE AND LOADED");
        return false;
    }

    // Native One Factory is not permitted to inherit any tag-bound legacy vehicle,
    // lift-deck or in-transfer load. Reject contamination before loading or mutating
    // the owned presentation components.
    for (TActorIterator<AActor> It(GetWorld()); It; ++It)
    {
        const AActor* Actor = *It;
        if (!Actor || Actor == this) continue;
        if (Actor->ActorHasTag(ChassisTag) || Actor->ActorHasTag(LiftDeckTag)
            || Actor->ActorHasTag(LoadTag))
        {
            OutReason = FString::Printf(
                TEXT("NATIVE INBOUND AGV REJECTED TAG-BOUND LEGACY PRESENTATION ACTOR %s"),
                *Actor->GetName());
            return false;
        }
    }

    UStaticMesh* NativeChassis = LoadObject<UStaticMesh>(nullptr, NativeOneFactoryChassisPath);
    UStaticMesh* NativeLiftDeck = LoadObject<UStaticMesh>(nullptr, NativeOneFactoryLiftDeckPath);
    UStaticMesh* NativeLoad = LoadObject<UStaticMesh>(nullptr, NativeOneFactoryLoadPath);
    if (!NativeChassis || !NativeLiftDeck || !NativeLoad
        || !NativeChassis->GetPathName().Equals(NativeOneFactoryChassisPath, ESearchCase::CaseSensitive)
        || !NativeLiftDeck->GetPathName().Equals(NativeOneFactoryLiftDeckPath, ESearchCase::CaseSensitive)
        || !NativeLoad->GetPathName().Equals(NativeOneFactoryLoadPath, ESearchCase::CaseSensitive))
    {
        OutReason = TEXT("NATIVE INBOUND AGV EXACT ALLOWLIST ASSETS ARE MISSING OR HAVE MOVED");
        return false;
    }

    ApprovedChassisVisual->SetStaticMesh(NativeChassis);
    ApprovedLiftDeckVisual->SetStaticMesh(NativeLiftDeck);
    ApprovedLoadVisual->SetStaticMesh(NativeLoad);
    ApprovedChassisVisual->SetRelativeLocationAndRotation(
        FVector::ZeroVector, FRotator::ZeroRotator);
    // Import audit: chassis actor datum Z=29 cm, lift-deck datum Z=64 cm.
    OwnedLiftDeckBaseRelativeLocation = FVector(0.0f, 0.0f, 35.0f);
    ApprovedLiftDeckVisual->SetRelativeLocationAndRotation(
        OwnedLiftDeckBaseRelativeLocation, FRotator::ZeroRotator);
    // The retained native master-coil centre is 92 cm above the deck datum.
    ApprovedLoadVisual->SetRelativeLocationAndRotation(
        FVector(0.0f, 0.0f, 92.0f), FRotator::ZeroRotator);
    // Audited loaded envelope: X 361 cm, Y 222 cm and Z 0..259 cm at full lift.
    CollisionProxy->SetRelativeLocation(FVector(0.0f, 0.0f, 100.0f));
    CollisionProxy->SetBoxExtent(FVector(180.5f, 111.0f, 130.0f));

    bForceOwnedPresentation = true;
    bNativeOneFactoryPresentation = true;
    if (!DiscoverAndBind() || !IsUsingNativeOneFactoryPresentation())
    {
        OutReason = TEXT("NATIVE INBOUND AGV COULD NOT PROVE ITS OWNED ALLOWLIST PRESENTATION");
        return false;
    }
    OutReason = TEXT("NATIVE ONE FACTORY AGV PRESENTATION PROVED FROM EXACT PROCEDURAL ASSETS");
    return true;
}

bool ALBCoilAGVController::DiscoverAndBind()
{
    ChassisActor = nullptr;
    LiftDeckActor = nullptr;
    LoadActor = nullptr;
    Modules.Reset();
    bUsingOwnedPresentation = false;
    if (!GetWorld()) return false;
    for (TActorIterator<AActor> It(GetWorld()); !bForceOwnedPresentation && It; ++It)
    {
        AActor* Actor = *It;
        if (Actor == this) continue;
        if (Actor->ActorHasTag(ChassisTag) && !Actor->ActorHasTag(LiftDeckTag)) ChassisActor = Actor;
        if (Actor->ActorHasTag(LiftDeckTag)) LiftDeckActor = Actor;
        if (Actor->ActorHasTag(LoadTag)) LoadActor = Actor;
    }
    if (!ChassisActor || !LiftDeckActor || !LoadActor)
    {
        if (!ApprovedChassisVisual->GetStaticMesh() || !ApprovedLoadVisual->GetStaticMesh()
            || (bNativeOneFactoryPresentation
                && (!HasExactMeshPath(ApprovedChassisVisual, NativeOneFactoryChassisPath)
                    || !HasExactMeshPath(ApprovedLiftDeckVisual, NativeOneFactoryLiftDeckPath)
                    || !HasExactMeshPath(ApprovedLoadVisual, NativeOneFactoryLoadPath))))
        {
            bBound = false;
            LatchFault(ELBCoilAGVFault::BindingIncomplete);
            return false;
        }
        ChassisActor = nullptr; LiftDeckActor = nullptr; LoadActor = nullptr;
        bUsingOwnedPresentation = true;
        SetActorLocationAndRotation(StagedPoint, FRotator::ZeroRotator);
        ApprovedChassisVisual->SetVisibility(true);
        // The legacy full-detail master contains its deck. Native One Factory instead
        // uses the separately authored procedural deck and keeps it visibly articulated.
        ApprovedLiftDeckVisual->SetVisibility(bNativeOneFactoryPresentation);
        ApprovedLoadVisual->SetVisibility(true);
        CollisionProxy->SetCollisionEnabled(ECollisionEnabled::QueryAndPhysics);
        CurrentLocation = StagedPoint;
        CurrentYawDegrees = 0.0f;
        bBound = true;
        if (ActiveFault == ELBCoilAGVFault::BindingIncomplete) ActiveFault = ELBCoilAGVFault::None;
        Phase = ELBCoilAGVPhase::IdleLoaded;
        ApplyPose();
        UpdateStatusBeacon();
        return true;
    }
    ApprovedChassisVisual->SetVisibility(false);
    ApprovedLiftDeckVisual->SetVisibility(false);
    ApprovedLoadVisual->SetVisibility(false);
    CollisionProxy->SetCollisionEnabled(ECollisionEnabled::NoCollision);
    const FTransform ChassisTransform = ChassisActor->GetActorTransform();
    auto Bind = [&](AActor* Actor, const bool bLift, const bool bLoad)
    {
        FBoundModule Module;
        Module.Actor = Actor;
        Module.LocalOffset = ChassisTransform.InverseTransformPosition(Actor->GetActorLocation());
        Module.LocalRotation = Actor->GetActorRotation() - ChassisActor->GetActorRotation();
        Module.bLiftWithDeck = bLift;
        Module.bIsLoad = bLoad;
        Modules.Add(Module);
    };
    Bind(ChassisActor, false, false);
    Bind(LiftDeckActor, true, false);
    Bind(LoadActor, true, true);
    CurrentLocation = ChassisActor->GetActorLocation();
    CurrentYawDegrees = ChassisActor->GetActorRotation().Yaw;
    StagedPoint.Z = CurrentLocation.Z;
    TurnPoint.Z = CurrentLocation.Z;
    DockPoint.Z = CurrentLocation.Z;
    bBound = true;
    if (ActiveFault == ELBCoilAGVFault::BindingIncomplete)
    {
        ActiveFault = ELBCoilAGVFault::None;
        Phase = ELBCoilAGVPhase::IdleLoaded;
    }
    ApplyPose();
    UpdateStatusBeacon();
    return true;
}

bool ALBCoilAGVController::ConfigureRoute(const FVector InStagedPoint, const FVector InTurnPoint, const FVector InDockPoint)
{
    if (!ConfigureRouteInternal(InStagedPoint, InTurnPoint, InDockPoint,
        false, nullptr, nullptr)) return false;
    RouteProfile = ELBCoilAGVRouteProfile::ManualOrUnassigned;
    AssignedRouteTrainIndex = INDEX_NONE;
    return true;
}

bool ALBCoilAGVController::ConfigureRouteInternal(const FVector& InStagedPoint,
    const FVector& InTurnPoint, const FVector& InDockPoint,
    const bool bEnforceProtectedEnvelopes, ALBFactoryBuildMachine* InAllowedStartMachine,
    ALBFactoryBuildMachine* InAllowedDockMachine)
{
    if (IsMotionPhase(Phase) || !IsFiniteCoilAGVVector(InStagedPoint)
        || !IsFiniteCoilAGVVector(InTurnPoint) || !IsFiniteCoilAGVVector(InDockPoint)
        || FVector::Dist2D(InStagedPoint, InTurnPoint) < MinimumRouteLegLengthCm
        || FVector::Dist2D(InTurnPoint, InDockPoint) < MinimumRouteLegLengthCm)
    {
        return false;
    }
    const FVector FirstDirection = (InTurnPoint - InStagedPoint).GetSafeNormal2D();
    const FVector SecondDirection = (InDockPoint - InTurnPoint).GetSafeNormal2D();
    // A single rounded waypoint cannot represent a U-turn. Require another painted waypoint
    // rather than allowing the vehicle to fold back through its own load envelope.
    if (FVector::DotProduct(FirstDirection, SecondDirection) < -0.95f) return false;

    bEnforceProtectedEnvelopeRoute = bEnforceProtectedEnvelopes;
    AllowedStartMachine = InAllowedStartMachine;
    AllowedDockMachine = InAllowedDockMachine;
    if (bEnforceProtectedEnvelopeRoute
        && !IsRouteClearOfProtectedEnvelopes(InStagedPoint, InTurnPoint, InDockPoint))
    {
        bEnforceProtectedEnvelopeRoute = false;
        AllowedStartMachine.Reset();
        AllowedDockMachine.Reset();
        return false;
    }
    StagedPoint = InStagedPoint;
    TurnPoint = InTurnPoint;
    DockPoint = InDockPoint;
    RebuildCornerGeometry();
    if (Phase == ELBCoilAGVPhase::IdleLoaded || Phase == ELBCoilAGVPhase::AwaitingReload)
    {
        CurrentLocation = StagedPoint;
        CurrentYawDegrees = DirectionYawDegrees(FirstDirection);
        CurrentTravelSpeedCmPerSecond = 0.0f;
        CornerProgress = 0.0f;
        ApplyPose();
    }
    return true;
}

void ALBCoilAGVController::RebuildCornerGeometry()
{
    const FVector Incoming = (TurnPoint - StagedPoint).GetSafeNormal2D();
    const FVector Outgoing = (DockPoint - TurnPoint).GetSafeNormal2D();
    const float FirstLegLength = FVector::Dist2D(StagedPoint, TurnPoint);
    const float SecondLegLength = FVector::Dist2D(TurnPoint, DockPoint);
    const float DirectionDot = FVector::DotProduct(Incoming, Outgoing);
    const float Trim = DirectionDot > 0.999f ? 0.0f : FMath::Min3(
        GameplayCornerTrimCm, FirstLegLength * 0.4f, SecondLegLength * 0.4f);
    CornerEntryPoint = TurnPoint - Incoming * Trim;
    CornerExitPoint = TurnPoint + Outgoing * Trim;
    CornerEntryPoint.Z = CornerExitPoint.Z = TurnPoint.Z;
    CornerPathLengthCm = 0.0f;
    FVector Previous = CornerEntryPoint;
    constexpr int32 ArcLengthSamples = 16;
    for (int32 Index = 1; Index <= ArcLengthSamples; ++Index)
    {
        const float Alpha = static_cast<float>(Index) / static_cast<float>(ArcLengthSamples);
        const FVector Point = QuadraticBezier(CornerEntryPoint, TurnPoint, CornerExitPoint, Alpha);
        CornerPathLengthCm += FVector::Dist2D(Previous, Point);
        Previous = Point;
    }
}

bool ALBCoilAGVController::IsRouteClearOfProtectedEnvelopes(const FVector& Start,
    const FVector& Turn, const FVector& Dock) const
{
    return IsRouteClearOfProtectedEnvelopesWithAllowed(Start, Turn, Dock,
        AllowedStartMachine.Get(), AllowedDockMachine.Get());
}

bool ALBCoilAGVController::IsRouteClearOfProtectedEnvelopesWithAllowed(const FVector& Start,
    const FVector& Turn, const FVector& Dock,
    const ALBFactoryBuildMachine* InAllowedStartMachine,
    const ALBFactoryBuildMachine* InAllowedDockMachine) const
{
    if (!GetWorld()) return false;
    const FVector ProxyExtent = CollisionProxy
        ? CollisionProxy->GetUnscaledBoxExtent() : FVector(95.0f, 73.0f, 29.0f);
    const float VehicleRadiusCm = FMath::Max(ProxyExtent.X, ProxyExtent.Y);
    for (TActorIterator<ALBFactoryBuildMachine> It(GetWorld()); It; ++It)
    {
        const ALBFactoryBuildMachine* Machine = *It;
        if (!IsValid(Machine) || Machine->GetMachineId().IsNone()
            || Machine == InAllowedStartMachine
            || Machine == InAllowedDockMachine)
        {
            continue;
        }
        if (SegmentIntersectsExpandedMachineEnvelope(Start, Turn, *Machine,
                VehicleRadiusCm, ProtectedEnvelopeClearanceCm)
            || SegmentIntersectsExpandedMachineEnvelope(Turn, Dock, *Machine,
                VehicleRadiusCm, ProtectedEnvelopeClearanceCm))
        {
            return false;
        }
    }
    return true;
}

bool ALBCoilAGVController::CanAdvanceTo(const FVector& CandidateLocation) const
{
    if (!bEnforceProtectedEnvelopeRoute || !GetWorld()) return true;
    const FVector ProxyExtent = CollisionProxy
        ? CollisionProxy->GetUnscaledBoxExtent() : FVector(95.0f, 73.0f, 29.0f);
    const float VehicleRadiusCm = FMath::Max(ProxyExtent.X, ProxyExtent.Y);
    for (TActorIterator<ALBFactoryBuildMachine> It(GetWorld()); It; ++It)
    {
        const ALBFactoryBuildMachine* Machine = *It;
        if (!IsValid(Machine) || Machine->GetMachineId().IsNone()
            || Machine == AllowedStartMachine.Get()
            || Machine == AllowedDockMachine.Get())
        {
            continue;
        }
        if (SegmentIntersectsExpandedMachineEnvelope(CurrentLocation, CandidateLocation,
            *Machine, VehicleRadiusCm, ProtectedEnvelopeClearanceCm))
        {
            return false;
        }
    }
    return true;
}

float ALBCoilAGVController::RecoverCornerProgressFromLocation() const
{
    float BestProgress = 0.0f;
    float BestDistanceSquared = TNumericLimits<float>::Max();
    constexpr int32 RecoverySamples = 64;
    for (int32 Index = 0; Index <= RecoverySamples; ++Index)
    {
        const float Alpha = static_cast<float>(Index) / static_cast<float>(RecoverySamples);
        const FVector Candidate = QuadraticBezier(CornerEntryPoint, TurnPoint, CornerExitPoint, Alpha);
        const float DistanceSquared = FVector::DistSquared2D(CurrentLocation, Candidate);
        if (DistanceSquared < BestDistanceSquared)
        {
            BestDistanceSquared = DistanceSquared;
            BestProgress = Alpha;
        }
    }
    return BestProgress;
}

bool ALBCoilAGVController::ConfigureFromPlayerBuiltInfrastructure(const int32 TrainIndex)
{
    TArray<FInfrastructureRouteCandidate> Candidates;
    GatherPressTrainRouteCandidates(GetWorld(), TrainIndex, Candidates);
    for (const FInfrastructureRouteCandidate& Candidate : Candidates)
    {
        FVector Start = Candidate.Wait->GetActorLocation();
        FVector Turn = Candidate.Waypoint->GetActorLocation();
        FVector Dock = Candidate.Handoff->GetActorLocation();
        const float TravelHeight = bBound ? CurrentLocation.Z : StagedPoint.Z;
        Start.Z = Turn.Z = Dock.Z = TravelHeight;
        if (!ConfigureRouteInternal(Start, Turn, Dock, true, nullptr, nullptr)) continue;
        RouteProfile = ELBCoilAGVRouteProfile::PressTrainHandoff;
        AssignedRouteTrainIndex = TrainIndex;
        return true;
    }
    return false;
}

bool ALBCoilAGVController::ConfigureInboundRouteFromPlayerBuiltInfrastructure(
    ALBFactoryBuildMachine* InboundDock, ALBFactoryBuildMachine* PR002Cell)
{
    const float TravelHeight = bBound ? CurrentLocation.Z : StagedPoint.Z;
    TArray<FInboundInfrastructureRouteCandidate> Candidates;
    GatherInboundRouteCandidates(GetWorld(), InboundDock, PR002Cell, Candidates);
    for (const FInboundInfrastructureRouteCandidate& Candidate : Candidates)
    {
        FVector Start = Candidate.Wait->GetActorLocation();
        FVector Turn = Candidate.Waypoint->GetActorLocation();
        FVector Dock = Candidate.Dock;
        Start.Z = Turn.Z = Dock.Z = TravelHeight;
        if (!ConfigureRouteInternal(Start, Turn, Dock, true, InboundDock, PR002Cell)) continue;
        RouteProfile = ELBCoilAGVRouteProfile::InboundPR002;
        AssignedRouteTrainIndex = INDEX_NONE;
        return true;
    }
    return false;
}

bool ALBCoilAGVController::StartDispatch(const FString& CoilId)
{
    if (!bBound || Phase != ELBCoilAGVPhase::IdleLoaded || CoilId.IsEmpty() || !bLoadOwned)
    {
        return false;
    }
    if (!SafetyHealthy())
    {
        LatchFault(FirstUnsafeFault());
        return false;
    }
    ActiveCoilId = CoilId;
    ActiveFault = ELBCoilAGVFault::None;
    CurrentTravelSpeedCmPerSecond = 0.0f;
    CornerProgress = 0.0f;
    EnterPhase(ELBCoilAGVPhase::TravelToTurn);
    return true;
}

bool ALBCoilAGVController::ConfirmHandoff(FString& OutCoilId)
{
    OutCoilId.Reset();
    if (!bBound || Phase != ELBCoilAGVPhase::HandoffReady || !bLoadOwned || ActiveCoilId.IsEmpty())
    {
        return false;
    }
    OutCoilId = ActiveCoilId;
    bLoadOwned = false;
    if (LoadActor)
    {
        LoadActor->SetActorHiddenInGame(true);
        LoadActor->SetActorEnableCollision(false);
    }
    if (bUsingOwnedPresentation) ApprovedLoadVisual->SetVisibility(false);
    EnterPhase(ELBCoilAGVPhase::LowerAfterHandoff);
    return true;
}

bool ALBCoilAGVController::ReloadAtStagedPoint(const FString& CoilId)
{
    const bool bFreshInitialLoad = Phase == ELBCoilAGVPhase::IdleLoaded && bLoadOwned && ActiveCoilId.IsEmpty();
    const bool bReturnedEmpty = Phase == ELBCoilAGVPhase::AwaitingReload && !bLoadOwned;
    if (!bBound || (!bFreshInitialLoad && !bReturnedEmpty) || CoilId.IsEmpty())
    {
        return false;
    }
    ActiveCoilId = CoilId;
    bLoadOwned = true;
    LiftHeightCm = 0.0f;
    if (LoadActor)
    {
        LoadActor->SetActorHiddenInGame(false);
        LoadActor->SetActorEnableCollision(true);
    }
    if (bUsingOwnedPresentation) ApprovedLoadVisual->SetVisibility(true);
    ApplyPose();
    EnterPhase(ELBCoilAGVPhase::IdleLoaded);
    return true;
}

bool ALBCoilAGVController::SetSafetyInputs(const bool bRouteIsReservedIn,
    const bool bPedestrianGatesAreProved, const bool bScannerZoneIsClear,
    const bool bLoadIsSecured, const bool bDestinationIsReadyIn,
    const bool bCraneSharedEnvelopeIsClear, const bool bEmergencyCircuitIsHealthyIn)
{
    bRouteReserved = bRouteIsReservedIn;
    bPedestrianGatesProved = bPedestrianGatesAreProved;
    bScannerZoneClear = bScannerZoneIsClear;
    bLoadSecured = bLoadIsSecured;
    bDestinationReady = bDestinationIsReadyIn;
    bCraneSharedEnvelopeClear = bCraneSharedEnvelopeIsClear;
    bEmergencyCircuitHealthy = bEmergencyCircuitIsHealthyIn;
    if (IsMotionPhase(Phase) && !SafetyHealthy()) LatchFault(FirstUnsafeFault());
    return true;
}

bool ALBCoilAGVController::SetControlPower(const bool bEnabled)
{
    bControlPowerOn = bEnabled;
    if (IsMotionPhase(Phase) && !bControlPowerOn) LatchFault(ELBCoilAGVFault::ControlPowerLost);
    else UpdateStatusBeacon();
    return true;
}

bool ALBCoilAGVController::ResetFault(const FName RecoveryEvidenceId)
{
    if (Phase != ELBCoilAGVPhase::Fault || RecoveryEvidenceId.IsNone()
        || ActiveFault == ELBCoilAGVFault::BindingIncomplete || !SafetyHealthy())
    {
        return false;
    }
    ActiveFault = ELBCoilAGVFault::None;
    EnterPhase(PhaseBeforeFault);
    return true;
}

void ALBCoilAGVController::Tick(const float DeltaSeconds)
{
    Super::Tick(DeltaSeconds);
    if (!bBound || Phase == ELBCoilAGVPhase::IdleLoaded || Phase == ELBCoilAGVPhase::HandoffReady
        || Phase == ELBCoilAGVPhase::AwaitingReload || Phase == ELBCoilAGVPhase::Fault)
    {
        return;
    }
    if (!SafetyHealthy())
    {
        LatchFault(FirstUnsafeFault());
        return;
    }
    PhaseElapsedSeconds += DeltaSeconds;
    if (PhaseElapsedSeconds > PhaseTimeoutSeconds)
    {
        LatchFault(ELBCoilAGVFault::DockTimeout);
        return;
    }
    switch (Phase)
    {
    case ELBCoilAGVPhase::TravelToTurn:
        if (MoveTo(CornerEntryPoint, DeltaSeconds, false))
        {
            CornerProgress = 0.0f;
            EnterPhase(ELBCoilAGVPhase::RotateForDock);
        }
        break;
    case ELBCoilAGVPhase::RotateForDock:
        if (MoveAroundCorner(true, DeltaSeconds)) EnterPhase(ELBCoilAGVPhase::TravelToDock);
        break;
    case ELBCoilAGVPhase::TravelToDock:
        if (MoveTo(DockPoint, DeltaSeconds, true)) EnterPhase(ELBCoilAGVPhase::DockProving);
        break;
    case ELBCoilAGVPhase::DockProving:
        if (PhaseElapsedSeconds >= DockProveSeconds) EnterPhase(ELBCoilAGVPhase::RaiseTransferDeck);
        break;
    case ELBCoilAGVPhase::RaiseTransferDeck:
        LiftHeightCm = FMath::FInterpConstantTo(LiftHeightCm, TransferLiftHeightCm, DeltaSeconds, GameplayLiftSpeedCmPerSecond);
        ApplyPose();
        if (FMath::IsNearlyEqual(LiftHeightCm, TransferLiftHeightCm, 0.01f)) EnterPhase(ELBCoilAGVPhase::HandoffReady);
        break;
    case ELBCoilAGVPhase::LowerAfterHandoff:
        LiftHeightCm = FMath::FInterpConstantTo(LiftHeightCm, 0.0f, DeltaSeconds, GameplayLiftSpeedCmPerSecond);
        ApplyPose();
        if (FMath::IsNearlyZero(LiftHeightCm, 0.01f)) EnterPhase(ELBCoilAGVPhase::ReturnToTurn);
        break;
    case ELBCoilAGVPhase::ReturnToTurn:
        if (MoveTo(CornerExitPoint, DeltaSeconds, false))
        {
            CornerProgress = 1.0f;
            EnterPhase(ELBCoilAGVPhase::RotateToStaged);
        }
        break;
    case ELBCoilAGVPhase::RotateToStaged:
        if (MoveAroundCorner(false, DeltaSeconds)) EnterPhase(ELBCoilAGVPhase::ReturnToStaged);
        break;
    case ELBCoilAGVPhase::ReturnToStaged:
        if (MoveTo(StagedPoint, DeltaSeconds, true))
        {
            ActiveCoilId.Reset();
            EnterPhase(ELBCoilAGVPhase::AwaitingReload);
        }
        break;
    default:
        break;
    }
}

bool ALBCoilAGVController::MoveTo(const FVector& Target, const float DeltaSeconds,
    const bool bStopAtTarget)
{
    const FVector ToTarget = Target - CurrentLocation;
    const float DistanceCm = ToTarget.Size2D();
    if (DistanceCm <= 0.05f)
    {
        CurrentLocation = Target;
        if (bStopAtTarget) CurrentTravelSpeedCmPerSecond = 0.0f;
        ApplyPose();
        return true;
    }
    const FVector TravelDirection = ToTarget.GetSafeNormal2D();
    const bool bReverse = Phase == ELBCoilAGVPhase::ReturnToTurn
        || Phase == ELBCoilAGVPhase::ReturnToStaged;
    const float DesiredYaw = DirectionYawDegrees(bReverse ? -TravelDirection : TravelDirection);
    CurrentYawDegrees = FMath::FixedTurn(CurrentYawDegrees, DesiredYaw,
        GameplayTurnRateDegreesPerSecond * DeltaSeconds);
    const float BrakingLimitedSpeed = bStopAtTarget
        ? FMath::Sqrt(FMath::Max(0.0f, 2.0f * GameplayAccelerationCmPerSecondSquared * DistanceCm))
        : GameplayTravelSpeedCmPerSecond;
    const float DesiredSpeed = FMath::Min(GameplayTravelSpeedCmPerSecond, BrakingLimitedSpeed);
    CurrentTravelSpeedCmPerSecond = FMath::FInterpConstantTo(CurrentTravelSpeedCmPerSecond,
        DesiredSpeed, DeltaSeconds, GameplayAccelerationCmPerSecondSquared);
    const float StepCm = FMath::Min(DistanceCm,
        FMath::Max(0.1f, CurrentTravelSpeedCmPerSecond * DeltaSeconds));
    FVector Candidate = CurrentLocation + TravelDirection * StepCm;
    Candidate.Z = FMath::Lerp(CurrentLocation.Z, Target.Z, StepCm / DistanceCm);
    if (!CanAdvanceTo(Candidate))
    {
        CurrentTravelSpeedCmPerSecond = 0.0f;
        LatchFault(ELBCoilAGVFault::RouteObstructed);
        return false;
    }
    CurrentLocation = Candidate;
    if (StepCm >= DistanceCm - 0.05f)
    {
        CurrentLocation = Target;
        if (bStopAtTarget) CurrentTravelSpeedCmPerSecond = 0.0f;
    }
    ApplyPose();
    return CurrentLocation.Equals(Target, 0.05f);
}

bool ALBCoilAGVController::MoveAroundCorner(const bool bOutbound, const float DeltaSeconds)
{
    if (CornerPathLengthCm <= 0.05f)
    {
        CornerProgress = bOutbound ? 1.0f : 0.0f;
        CurrentLocation = bOutbound ? CornerExitPoint : CornerEntryPoint;
        const FVector Direction = bOutbound
            ? (DockPoint - TurnPoint).GetSafeNormal2D()
            : (TurnPoint - StagedPoint).GetSafeNormal2D();
        CurrentYawDegrees = DirectionYawDegrees(Direction);
        ApplyPose();
        return true;
    }
    CurrentTravelSpeedCmPerSecond = FMath::FInterpConstantTo(CurrentTravelSpeedCmPerSecond,
        GameplayTravelSpeedCmPerSecond, DeltaSeconds, GameplayAccelerationCmPerSecondSquared);
    const float ProgressStep = FMath::Max(0.1f,
        CurrentTravelSpeedCmPerSecond * DeltaSeconds) / CornerPathLengthCm;
    const float CandidateProgress = FMath::Clamp(CornerProgress
        + (bOutbound ? ProgressStep : -ProgressStep), 0.0f, 1.0f);
    const FVector Candidate = QuadraticBezier(
        CornerEntryPoint, TurnPoint, CornerExitPoint, CandidateProgress);
    if (!CanAdvanceTo(Candidate))
    {
        CurrentTravelSpeedCmPerSecond = 0.0f;
        LatchFault(ELBCoilAGVFault::RouteObstructed);
        return false;
    }
    CornerProgress = CandidateProgress;
    CurrentLocation = Candidate;
    FVector Tangent = QuadraticBezierTangent(
        CornerEntryPoint, TurnPoint, CornerExitPoint, CornerProgress).GetSafeNormal2D();
    if (Tangent.IsNearlyZero()) Tangent = (DockPoint - StagedPoint).GetSafeNormal2D();
    // The empty vehicle reverses through the same curve, so its nose remains aligned with the
    // outbound tangent while its velocity is opposite. This avoids a second in-place pivot.
    CurrentYawDegrees = DirectionYawDegrees(Tangent);
    ApplyPose();
    return bOutbound ? CornerProgress >= 1.0f - KINDA_SMALL_NUMBER
        : CornerProgress <= KINDA_SMALL_NUMBER;
}

void ALBCoilAGVController::ApplyPose()
{
    if (bUsingOwnedPresentation)
    {
        SetActorLocationAndRotation(CurrentLocation, FRotator(0.0f, CurrentYawDegrees, 0.0f), false, nullptr, ETeleportType::TeleportPhysics);
        ApprovedLiftDeckVisual->SetRelativeLocation(
            OwnedLiftDeckBaseRelativeLocation + FVector(0.0f, 0.0f, LiftHeightCm));
        return;
    }
    const FTransform VehicleTransform(FRotator(0.0f, CurrentYawDegrees, 0.0f), CurrentLocation);
    for (const FBoundModule& Module : Modules)
    {
        AActor* Actor = Module.Actor.Get();
        if (!Actor) continue;
        FVector WorldLocation = VehicleTransform.TransformPosition(Module.LocalOffset);
        if (Module.bLiftWithDeck) WorldLocation.Z += LiftHeightCm;
        Actor->SetActorLocationAndRotation(WorldLocation,
            FRotator(Module.LocalRotation.Pitch, CurrentYawDegrees + Module.LocalRotation.Yaw, Module.LocalRotation.Roll),
            false, nullptr, ETeleportType::TeleportPhysics);
        if (Module.bIsLoad)
        {
            const FVector Expected = VehicleTransform.TransformPosition(Module.LocalOffset) + FVector(0,0,LiftHeightCm);
            MaxLoadFollowErrorCm = FMath::Max(MaxLoadFollowErrorCm, FVector::Distance(Expected, Actor->GetActorLocation()));
        }
    }
}

bool ALBCoilAGVController::SafetyHealthy() const
{
    return bControlPowerOn && bRouteReserved && bPedestrianGatesProved && bScannerZoneClear
        && bLoadSecured && bDestinationReady && bCraneSharedEnvelopeClear && bEmergencyCircuitHealthy;
}

ELBCoilAGVFault ALBCoilAGVController::FirstUnsafeFault() const
{
    if (!bControlPowerOn) return ELBCoilAGVFault::ControlPowerLost;
    if (!bEmergencyCircuitHealthy) return ELBCoilAGVFault::EmergencyCircuitOpen;
    if (!bRouteReserved) return ELBCoilAGVFault::RouteAuthorityLost;
    if (!bPedestrianGatesProved) return ELBCoilAGVFault::PedestrianGateOpen;
    if (!bScannerZoneClear) return ELBCoilAGVFault::ScannerObstructed;
    if (!bLoadSecured) return ELBCoilAGVFault::LoadUnsecured;
    if (!bDestinationReady) return ELBCoilAGVFault::DestinationNotReady;
    if (!bCraneSharedEnvelopeClear) return ELBCoilAGVFault::CraneEnvelopeConflict;
    return ELBCoilAGVFault::None;
}

bool ALBCoilAGVController::IsMotionPhase(const ELBCoilAGVPhase Candidate) const
{
    return Candidate != ELBCoilAGVPhase::IdleLoaded && Candidate != ELBCoilAGVPhase::HandoffReady
        && Candidate != ELBCoilAGVPhase::AwaitingReload && Candidate != ELBCoilAGVPhase::Fault;
}

void ALBCoilAGVController::EnterPhase(const ELBCoilAGVPhase NewPhase)
{
    Phase = NewPhase;
    PhaseElapsedSeconds = 0.0f;
    if (NewPhase == ELBCoilAGVPhase::IdleLoaded || NewPhase == ELBCoilAGVPhase::HandoffReady
        || NewPhase == ELBCoilAGVPhase::AwaitingReload || NewPhase == ELBCoilAGVPhase::Fault)
    {
        CurrentTravelSpeedCmPerSecond = 0.0f;
    }
    UpdateStatusBeacon();
}

void ALBCoilAGVController::LatchFault(const ELBCoilAGVFault Fault)
{
    if (Phase != ELBCoilAGVPhase::Fault) PhaseBeforeFault = Phase;
    ActiveFault = Fault;
    EnterPhase(ELBCoilAGVPhase::Fault);
}

bool ALBCoilAGVController::GetSaveState(FLBCoilAGVSaveState& OutState) const
{
    if (!bBound || (ActiveCoilId.IsEmpty() && Phase != ELBCoilAGVPhase::IdleLoaded
        && Phase != ELBCoilAGVPhase::AwaitingReload)) return false;
    OutState.SaveVersion = 3;
    OutState.Phase = Phase;
    OutState.PhaseBeforeFault = PhaseBeforeFault;
    OutState.Fault = ActiveFault;
    OutState.VehicleLocation = CurrentLocation;
    OutState.VehicleYawDegrees = CurrentYawDegrees;
    OutState.LiftHeightCm = LiftHeightCm;
    OutState.TravelSpeedCmPerSecond = CurrentTravelSpeedCmPerSecond;
    OutState.CornerProgress = CornerProgress;
    OutState.PhaseElapsedSeconds = PhaseElapsedSeconds;
    OutState.CoilId = ActiveCoilId;
    OutState.bLoadOwned = bLoadOwned;
    OutState.RouteStagedPoint = StagedPoint;
    OutState.RouteTurnPoint = TurnPoint;
    OutState.RouteDockPoint = DockPoint;
    OutState.RouteProfile = RouteProfile;
    OutState.AssignedRouteTrainIndex = AssignedRouteTrainIndex;
    return true;
}

bool ALBCoilAGVController::RestoreInboundSaveState(const FLBCoilAGVSaveState& InState,
    ALBFactoryBuildMachine* InboundDock, ALBFactoryBuildMachine* PR002Cell)
{
    if (!bBound || !GetWorld() || !InboundDock || !PR002Cell
        || InboundDock->GetMachineType() != ELBFactoryBuildMachineType::InboundDeliveryDock
        || PR002Cell->GetMachineType() != ELBFactoryBuildMachineType::CoilWeighInspectionCell)
    {
        return false;
    }
    if (InState.SaveVersion >= 3)
    {
        return InState.RouteProfile == ELBCoilAGVRouteProfile::InboundPR002
            && InState.AssignedRouteTrainIndex == INDEX_NONE
            && RestoreSaveState(InState);
    }
    if (InState.SaveVersion != 1 && InState.SaveVersion != 2) return false;

    // Legacy snapshots omitted geometry. The only safe migration is to reconstruct the
    // restored campaign's painted route at the live chassis datum, prove the saved location
    // belongs to that route, then commit route authority and motion as one synchronous unit.
    constexpr float TravelDatumToleranceCm = 0.1f;
    if (!FMath::IsFinite(InState.VehicleLocation.Z)
        || !FMath::IsNearlyEqual(InState.VehicleLocation.Z,
            CurrentLocation.Z, TravelDatumToleranceCm))
    {
        return false;
    }
    TArray<FInboundInfrastructureRouteCandidate> Candidates;
    GatherInboundRouteCandidates(GetWorld(), InboundDock, PR002Cell, Candidates);
    for (const FInboundInfrastructureRouteCandidate& Candidate : Candidates)
    {
        FVector Start = Candidate.Wait->GetActorLocation();
        FVector Turn = Candidate.Waypoint->GetActorLocation();
        FVector Dock = Candidate.Dock;
        Start.Z = Turn.Z = Dock.Z = CurrentLocation.Z;
        if (!IsRouteClearOfProtectedEnvelopesWithAllowed(
                Start, Turn, Dock, InboundDock, PR002Cell)
            || !IsLegacySavedLocationCompatibleWithRoute(InState, Start, Turn, Dock))
        {
            continue;
        }

        const FVector PreviousStagedPoint = StagedPoint;
        const FVector PreviousTurnPoint = TurnPoint;
        const FVector PreviousDockPoint = DockPoint;
        const bool bPreviousProtectedEnvelopeRoute = bEnforceProtectedEnvelopeRoute;
        const TWeakObjectPtr<ALBFactoryBuildMachine> PreviousAllowedStart = AllowedStartMachine;
        const TWeakObjectPtr<ALBFactoryBuildMachine> PreviousAllowedDock = AllowedDockMachine;
        const ELBCoilAGVRouteProfile PreviousProfile = RouteProfile;
        const int32 PreviousTrainIndex = AssignedRouteTrainIndex;

        StagedPoint = Start;
        TurnPoint = Turn;
        DockPoint = Dock;
        bEnforceProtectedEnvelopeRoute = true;
        AllowedStartMachine = InboundDock;
        AllowedDockMachine = PR002Cell;
        RouteProfile = ELBCoilAGVRouteProfile::InboundPR002;
        AssignedRouteTrainIndex = INDEX_NONE;
        if (RestoreSaveState(InState)) return true;

        StagedPoint = PreviousStagedPoint;
        TurnPoint = PreviousTurnPoint;
        DockPoint = PreviousDockPoint;
        bEnforceProtectedEnvelopeRoute = bPreviousProtectedEnvelopeRoute;
        AllowedStartMachine = PreviousAllowedStart;
        AllowedDockMachine = PreviousAllowedDock;
        RouteProfile = PreviousProfile;
        AssignedRouteTrainIndex = PreviousTrainIndex;
        RebuildCornerGeometry();
        return false;
    }
    return false;
}

bool ALBCoilAGVController::RestoreSaveState(const FLBCoilAGVSaveState& InState)
{
    if (!bBound || (InState.SaveVersion != 1 && InState.SaveVersion != 2 && InState.SaveVersion != 3)
        || InState.Phase == ELBCoilAGVPhase::DockProving || InState.Phase == ELBCoilAGVPhase::RaiseTransferDeck
        || !IsFiniteCoilAGVVector(InState.VehicleLocation) || !FMath::IsFinite(InState.VehicleYawDegrees)
        || !FMath::IsFinite(InState.LiftHeightCm) || !FMath::IsFinite(InState.PhaseElapsedSeconds)
        || (InState.SaveVersion >= 2 && (!FMath::IsFinite(InState.TravelSpeedCmPerSecond)
            || !FMath::IsFinite(InState.CornerProgress)))
        || (InState.SaveVersion >= 3 && (!IsValidRouteProfileAssignment(
            InState.RouteProfile, InState.AssignedRouteTrainIndex)
            || !IsValidRouteGeometry(InState.RouteStagedPoint,
                InState.RouteTurnPoint, InState.RouteDockPoint)))
        || (InState.bLoadOwned && InState.CoilId.IsEmpty()
            && InState.Phase != ELBCoilAGVPhase::IdleLoaded)
        || (!InState.bLoadOwned && !InState.CoilId.IsEmpty()
            && InState.Phase != ELBCoilAGVPhase::LowerAfterHandoff
            && InState.Phase != ELBCoilAGVPhase::ReturnToTurn
            && InState.Phase != ELBCoilAGVPhase::RotateToStaged
            && InState.Phase != ELBCoilAGVPhase::ReturnToStaged))
    {
        return false;
    }

    constexpr float TravelDatumToleranceCm = 0.1f;
    if (InState.SaveVersion >= 3
        && (!FMath::IsNearlyEqual(InState.RouteStagedPoint.Z,
                InState.RouteTurnPoint.Z, TravelDatumToleranceCm)
            || !FMath::IsNearlyEqual(InState.RouteStagedPoint.Z,
                InState.RouteDockPoint.Z, TravelDatumToleranceCm)
            || !FMath::IsNearlyEqual(InState.RouteStagedPoint.Z,
                InState.VehicleLocation.Z, TravelDatumToleranceCm)
            || !FMath::IsNearlyEqual(InState.RouteStagedPoint.Z,
                CurrentLocation.Z, TravelDatumToleranceCm)))
    {
        return false;
    }

    // Version three resumes motion only against the exact route geometry that was saved.
    // Automatic profiles must still be authorized by the restored painted route and machine
    // envelopes; an edited/missing route therefore rejects the load rather than silently
    // combining saved vehicle motion with unrelated world geometry.
    if (InState.SaveVersion >= 3)
    {
        const auto MatchesSavedRoute = [&InState](const FVector& Start,
            const FVector& Turn, const FVector& Dock)
        {
            constexpr float RouteMatchToleranceCm = 1.0f;
            FVector NormalizedStart = Start;
            FVector NormalizedTurn = Turn;
            FVector NormalizedDock = Dock;
            NormalizedStart.Z = NormalizedTurn.Z = NormalizedDock.Z
                = InState.RouteStagedPoint.Z;
            return FVector::Dist(NormalizedStart, InState.RouteStagedPoint) <= RouteMatchToleranceCm
                && FVector::Dist(NormalizedTurn, InState.RouteTurnPoint) <= RouteMatchToleranceCm
                && FVector::Dist(NormalizedDock, InState.RouteDockPoint) <= RouteMatchToleranceCm;
        };

        bool bCandidateEnforceProtectedRoute = false;
        ALBFactoryBuildMachine* CandidateAllowedStartMachine = nullptr;
        ALBFactoryBuildMachine* CandidateAllowedDockMachine = nullptr;
        if (InState.RouteProfile == ELBCoilAGVRouteProfile::PressTrainHandoff)
        {
            TArray<FInfrastructureRouteCandidate> Candidates;
            GatherPressTrainRouteCandidates(GetWorld(), InState.AssignedRouteTrainIndex, Candidates);
            bool bAuthorized = false;
            for (const FInfrastructureRouteCandidate& Candidate : Candidates)
            {
                if (!MatchesSavedRoute(Candidate.Wait->GetActorLocation(),
                    Candidate.Waypoint->GetActorLocation(), Candidate.Handoff->GetActorLocation()))
                {
                    continue;
                }
                bAuthorized = IsRouteClearOfProtectedEnvelopesWithAllowed(
                    InState.RouteStagedPoint, InState.RouteTurnPoint,
                    InState.RouteDockPoint, nullptr, nullptr);
                break;
            }
            if (!bAuthorized) return false;
            bCandidateEnforceProtectedRoute = true;
        }
        else if (InState.RouteProfile == ELBCoilAGVRouteProfile::InboundPR002)
        {
            ALBFactoryBuildMachine* Inbound = nullptr;
            ALBFactoryBuildMachine* PR002 = nullptr;
            int32 InboundCount = 0;
            int32 PR002Count = 0;
            for (TActorIterator<ALBFactoryBuildMachine> It(GetWorld()); It; ++It)
            {
                if (!IsValid(*It)) continue;
                if (It->GetMachineType() == ELBFactoryBuildMachineType::InboundDeliveryDock)
                { Inbound = *It; ++InboundCount; }
                else if (It->GetMachineType() == ELBFactoryBuildMachineType::CoilWeighInspectionCell)
                { PR002 = *It; ++PR002Count; }
            }
            if (InboundCount != 1 || PR002Count != 1 || !PR002->InputPort)
                return false;

            TArray<ALBFactoryAGVInfrastructure*> WaitPoints;
            TArray<ALBFactoryAGVInfrastructure*> Waypoints;
            TArray<ALBFactoryAGVInfrastructure*> RouteSegments;
            for (TActorIterator<ALBFactoryAGVInfrastructure> It(GetWorld()); It; ++It)
            {
                if (!IsValid(*It)) continue;
                switch (It->GetInfrastructureType())
                {
                case ELBFactoryAGVInfrastructureType::WaitPoint: WaitPoints.Add(*It); break;
                case ELBFactoryAGVInfrastructureType::RouteWaypoint: Waypoints.Add(*It); break;
                case ELBFactoryAGVInfrastructureType::AGVRouteSegment: RouteSegments.Add(*It); break;
                default: break;
                }
            }
            bool bAuthorized = false;
            for (ALBFactoryAGVInfrastructure* Wait : WaitPoints)
            {
                for (ALBFactoryAGVInfrastructure* Waypoint : Waypoints)
                {
                    const FVector Start = Wait->GetActorLocation();
                    const FVector Turn = Waypoint->GetActorLocation();
                    const FVector Dock = PR002->InputPort->GetComponentLocation();
                    if (!MatchesSavedRoute(Start, Turn, Dock)
                        || !IsRouteLegContinuouslyCovered(Start, Turn, RouteSegments)
                        || !IsRouteLegContinuouslyCovered(Turn, Dock, RouteSegments))
                    {
                        continue;
                    }
                    bAuthorized = IsRouteClearOfProtectedEnvelopesWithAllowed(
                        InState.RouteStagedPoint, InState.RouteTurnPoint,
                        InState.RouteDockPoint, Inbound, PR002);
                    break;
                }
                if (bAuthorized) break;
            }
            if (!bAuthorized) return false;
            bCandidateEnforceProtectedRoute = true;
            CandidateAllowedStartMachine = Inbound;
            CandidateAllowedDockMachine = PR002;
        }
        // Commit route authority atomically only after every profile, paint and protected-
        // envelope check has succeeded. Failed restores leave the pre-existing route intact.
        bEnforceProtectedEnvelopeRoute = bCandidateEnforceProtectedRoute;
        AllowedStartMachine = CandidateAllowedStartMachine;
        AllowedDockMachine = CandidateAllowedDockMachine;
        StagedPoint = InState.RouteStagedPoint;
        TurnPoint = InState.RouteTurnPoint;
        DockPoint = InState.RouteDockPoint;
    }
    Phase = InState.Phase;
    PhaseBeforeFault = InState.PhaseBeforeFault;
    ActiveFault = InState.Fault;
    CurrentLocation = InState.VehicleLocation;
    CurrentYawDegrees = InState.VehicleYawDegrees;
    LiftHeightCm = InState.LiftHeightCm;
    CurrentTravelSpeedCmPerSecond = InState.SaveVersion >= 2
        ? FMath::Clamp(InState.TravelSpeedCmPerSecond, 0.0f, GameplayTravelSpeedCmPerSecond) : 0.0f;
    RebuildCornerGeometry();
    CornerProgress = InState.SaveVersion >= 2
        ? FMath::Clamp(InState.CornerProgress, 0.0f, 1.0f) : RecoverCornerProgressFromLocation();
    PhaseElapsedSeconds = InState.PhaseElapsedSeconds;
    ActiveCoilId = InState.CoilId;
    bLoadOwned = InState.bLoadOwned;
    if (InState.SaveVersion >= 3)
    {
        RouteProfile = InState.RouteProfile;
        AssignedRouteTrainIndex = InState.AssignedRouteTrainIndex;
    }
    if (LoadActor)
    {
        LoadActor->SetActorHiddenInGame(!bLoadOwned);
        LoadActor->SetActorEnableCollision(bLoadOwned);
    }
    if (bUsingOwnedPresentation)
    {
        ApprovedLoadVisual->SetVisibility(bLoadOwned);
    }
    ApplyPose();
    UpdateStatusBeacon();
    return true;
}

void ALBCoilAGVController::UpdateStatusBeacon()
{
    if (!StatusBeacon) return;
    if (!bControlPowerOn && Phase != ELBCoilAGVPhase::Fault)
    {
        StatusBeacon->SetStatus(ELBStatusBeaconState::Stopped);
        return;
    }
    if (Phase == ELBCoilAGVPhase::Fault)
    {
        StatusBeacon->SetStatus(ActiveFault == ELBCoilAGVFault::EmergencyCircuitOpen
            ? ELBStatusBeaconState::Emergency : ELBStatusBeaconState::Fault);
        return;
    }
    if (IsMotionPhase(Phase))
    {
        StatusBeacon->SetStatus(ELBStatusBeaconState::Moving);
        return;
    }
    StatusBeacon->SetStatus(Phase == ELBCoilAGVPhase::HandoffReady
        ? ELBStatusBeaconState::Ready : ELBStatusBeaconState::Idle);
}
