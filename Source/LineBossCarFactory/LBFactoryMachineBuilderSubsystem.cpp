#include "LBFactoryMachineBuilderSubsystem.h"

#include "EngineUtils.h"
#include "Components/BoxComponent.h"
#include "Components/PrimitiveComponent.h"
#include "LBBodyWeldLineActor.h"
#include "LBFactoryConnectionSubsystem.h"
#include "LBFactoryTransportLink.h"
#include "LBCoilAGVController.h"
#include "LBECoatLineActor.h"
#include "LBPressShopBuildAuthority.h"
#include "LBPressShopStorageZone.h"
#include "LBPressTrainAStation.h"
#include "LBPressTrainIdentitySubsystem.h"
#include "LBPlayerBuiltPressFlowController.h"
#include "Engine/OverlapResult.h"
#include "UObject/UnrealType.h"

namespace
{
const TCHAR* MachinePrefix(const ELBFactoryBuildMachineType Type)
{
    switch (Type)
    {
    case ELBFactoryBuildMachineType::InboundDeliveryDock: return TEXT("INBOUND");
    case ELBFactoryBuildMachineType::CoilWeighInspectionCell: return TEXT("PR002");
    case ELBFactoryBuildMachineType::DepackagingRobot: return TEXT("DEPACK");
    case ELBFactoryBuildMachineType::DecoilerFeeder: return TEXT("COIL-PREP");
    case ELBFactoryBuildMachineType::InspectionCell: return TEXT("INSPECT");
    case ELBFactoryBuildMachineType::OutboundPanelDock: return TEXT("OUTBOUND");
    case ELBFactoryBuildMachineType::ECoatLine: return TEXT("ED-LINE");
    case ELBFactoryBuildMachineType::BodyWeldLine: return TEXT("WELD-LINE");
    default: return TEXT("MACHINE");
    }
}

const TCHAR* AGVInfrastructurePrefix(const ELBFactoryAGVInfrastructureType Type)
{
    switch (Type)
    {
    case ELBFactoryAGVInfrastructureType::ChargingStation: return TEXT("CS");
    case ELBFactoryAGVInfrastructureType::WaitPoint: return TEXT("AGV-WAIT");
    case ELBFactoryAGVInfrastructureType::RouteWaypoint: return TEXT("AGV-ROUTE");
    case ELBFactoryAGVInfrastructureType::PressTrainHandoff: return TEXT("S01-HANDOFF");
    case ELBFactoryAGVInfrastructureType::AGVRouteSegment: return TEXT("AGV-ROUTE-SEG");
    case ELBFactoryAGVInfrastructureType::PedestrianWalkway: return TEXT("WALKWAY");
    case ELBFactoryAGVInfrastructureType::PedestrianCrossing: return TEXT("CROSSING");
    case ELBFactoryAGVInfrastructureType::SafetyFence: return TEXT("FENCE");
    default: return TEXT("AGV-INFRA");
    }
}

bool IsRouteAuthorityType(const ELBFactoryAGVInfrastructureType Type)
{
    return Type == ELBFactoryAGVInfrastructureType::WaitPoint
        || Type == ELBFactoryAGVInfrastructureType::RouteWaypoint
        || Type == ELBFactoryAGVInfrastructureType::PressTrainHandoff
        || Type == ELBFactoryAGVInfrastructureType::AGVRouteSegment;
}

bool IsAGVAffectedByInfrastructureEdit(const ALBCoilAGVController& AGV,
    const ALBFactoryAGVInfrastructure& Edited)
{
    if (AGV.GetRouteProfile() == ELBCoilAGVRouteProfile::ManualOrUnassigned) return false;
    if (Edited.GetInfrastructureType() == ELBFactoryAGVInfrastructureType::PressTrainHandoff)
    {
        return AGV.GetRouteProfile() == ELBCoilAGVRouteProfile::PressTrainHandoff
            && AGV.GetAssignedRouteTrainIndex() == Edited.GetTrainIndex();
    }
    return Edited.GetInfrastructureType() == ELBFactoryAGVInfrastructureType::WaitPoint
        || Edited.GetInfrastructureType() == ELBFactoryAGVInfrastructureType::RouteWaypoint
        || Edited.GetInfrastructureType() == ELBFactoryAGVInfrastructureType::AGVRouteSegment;
}

bool IsPaintOnlyInfrastructure(const ELBFactoryAGVInfrastructureType Type)
{
    return Type == ELBFactoryAGVInfrastructureType::RouteWaypoint
        || Type == ELBFactoryAGVInfrastructureType::AGVRouteSegment
        || Type == ELBFactoryAGVInfrastructureType::PedestrianWalkway
        || Type == ELBFactoryAGVInfrastructureType::PedestrianCrossing;
}

bool InfrastructureMayIntentionallyOverlap(const ELBFactoryAGVInfrastructureType A,
    const ELBFactoryAGVInfrastructureType B)
{
    if (IsPaintOnlyInfrastructure(A) && IsPaintOnlyInfrastructure(B)) return true;
    const bool bANavigationPaint = A == ELBFactoryAGVInfrastructureType::RouteWaypoint
        || A == ELBFactoryAGVInfrastructureType::AGVRouteSegment;
    const bool bBNavigationPaint = B == ELBFactoryAGVInfrastructureType::RouteWaypoint
        || B == ELBFactoryAGVInfrastructureType::AGVRouteSegment;
    const bool bAEndpoint = A == ELBFactoryAGVInfrastructureType::WaitPoint
        || A == ELBFactoryAGVInfrastructureType::PressTrainHandoff;
    const bool bBEndpoint = B == ELBFactoryAGVInfrastructureType::WaitPoint
        || B == ELBFactoryAGVInfrastructureType::PressTrainHandoff;
    return (bANavigationPaint && bBEndpoint) || (bBNavigationPaint && bAEndpoint);
}

FBox InfrastructureEnvelope(const ALBFactoryAGVInfrastructure& Item, const FTransform& Transform)
{
    const FVector HalfExtent = Item.GetPlacementHalfExtentCm();
    return FBox(FVector(-HalfExtent.X, -HalfExtent.Y, 0.0f),
        FVector(HalfExtent.X, HalfExtent.Y, HalfExtent.Z * 2.0f)).TransformBy(Transform);
}

bool IsOnSingleFactoryFloorDatum(UWorld& World, const FBox& Candidate,
    const FVector& CandidateRoot)
{
    ALBPressShopBuildAuthority* Authority = nullptr;
    for (TActorIterator<ALBPressShopBuildAuthority> It(&World); It; ++It)
    {
        if (!IsValid(*It)) continue;
        if (Authority) return false;
        Authority = *It;
    }
    if (!Authority) return false;
    constexpr float FloorDatumToleranceCm = 1.0f;
    for (const FLBPressShopBuildBay& Bay : Authority->BuildBays)
    {
        if (!FMath::IsNearlyEqual(CandidateRoot.Z, Bay.Centre.Z, FloorDatumToleranceCm)) continue;
        const FBox BayBox(Bay.Centre - Bay.HalfExtent, Bay.Centre + Bay.HalfExtent);
        if (BayBox.ExpandBy(FloorDatumToleranceCm).IsInsideOrOn(Candidate.Min)
            && BayBox.ExpandBy(FloorDatumToleranceCm).IsInsideOrOn(Candidate.Max))
        {
            return true;
        }
    }
    return false;
}

bool GetBodyWeldPlacementEnvelope(FVector& OutHalfExtent, FVector& OutRelativeCentre)
{
    const ALBBodyWeldLineActor* Defaults = GetDefault<ALBBodyWeldLineActor>();
    const UBoxComponent* Envelope = Defaults ? Defaults->GetProtectedEnvelope() : nullptr;
    if (!Envelope) return false;
    OutHalfExtent = Envelope->GetUnscaledBoxExtent();
    OutRelativeCentre = Envelope->GetRelativeLocation();
    return OutHalfExtent.GetMin() > 0.0f;
}

bool ValidateECoatEnvelopeAgainstWorld(UWorld& World, const FTransform& WorldTransform,
    const ALBECoatLineActor* IgnoredLine, FString& OutReason)
{
    const ALBECoatLineActor* Defaults = GetDefault<ALBECoatLineActor>();
    if (!Defaults)
    {
        OutReason = TEXT("ED LINE PLACEMENT CONTRACT IS OFFLINE");
        return false;
    }
    const FVector HalfExtent = Defaults->GetProtectedEnvelopeHalfExtentCm();
    const FVector RelativeCentre = Defaults->GetProtectedEnvelopeRelativeCentreCm();
    const FBox LocalEnvelope(RelativeCentre - HalfExtent, RelativeCentre + HalfExtent);
    const FBox Candidate = LocalEnvelope.TransformBy(WorldTransform);
    if (!IsOnSingleFactoryFloorDatum(World, Candidate, WorldTransform.GetLocation()))
    {
        OutReason = TEXT("ED LINE MUST SIT ON ONE FACTORY FLOOR DATUM WITH ITS COMPLETE 189 m FOOTPRINT INSIDE THE BUILD BAY");
        return false;
    }

    ALBPressShopBuildAuthority* Authority = nullptr;
    for (TActorIterator<ALBPressShopBuildAuthority> It(&World); It; ++It)
    {
        if (!IsValid(*It)) continue;
        if (Authority)
        {
            OutReason = TEXT("MULTIPLE FACTORY BUILD AUTHORITIES MAKE ED LINE PLACEMENT AMBIGUOUS");
            return false;
        }
        Authority = *It;
    }
    if (!Authority)
    {
        OutReason = TEXT("FACTORY BUILD FLOOR AUTHORITY IS OFFLINE");
        return false;
    }
    FString AuthorityReason;
    if (!Authority->EvaluateTrainEnvelope(Candidate, AuthorityReason))
    {
        AuthorityReason.ReplaceInline(TEXT("TRAIN FOOTPRINT"), TEXT("ED LINE FOOTPRINT"));
        AuthorityReason.ReplaceInline(TEXT("PRESS SHOP"), TEXT("FACTORY"));
        OutReason = FString::Printf(TEXT("ED LINE FOOTPRINT REJECTED: %s"), *AuthorityReason);
        return false;
    }
    AuthorityReason.ReplaceInline(TEXT("PRESS SHOP"), TEXT("FACTORY"));

    for (TActorIterator<ALBFactoryBuildMachine> It(&World); It; ++It)
    {
        if (!IsValid(*It)) continue;
        const FBox OtherLocal(It->GetProtectedEnvelopeRelativeCentre()
                - It->GetProtectedEnvelopeHalfExtent(),
            It->GetProtectedEnvelopeRelativeCentre() + It->GetProtectedEnvelopeHalfExtent());
        if (Candidate.Intersect(OtherLocal.TransformBy(It->GetActorTransform())))
        {
            OutReason = FString::Printf(TEXT("ED LINE ENVELOPE OVERLAPS MACHINE %s"),
                *It->GetMachineId().ToString());
            return false;
        }
    }
    for (TActorIterator<ALBPressTrainAStation> It(&World); It; ++It)
    {
        if (IsValid(*It) && Candidate.Intersect(
            ALBPressTrainAStation::GetProtectedLocalEnvelope().TransformBy(It->GetActorTransform())))
        {
            OutReason = FString::Printf(TEXT("ED LINE ENVELOPE OVERLAPS PRESS TRAIN %s"),
                *It->GetTrainId().ToString());
            return false;
        }
    }
    for (TActorIterator<ALBPressShopStorageZone> It(&World); It; ++It)
    {
        if (!IsValid(*It)) continue;
        const FBox StorageLocal(-It->GetZoneHalfExtent(), It->GetZoneHalfExtent());
        if (Candidate.Intersect(StorageLocal.TransformBy(It->GetActorTransform())))
        {
            OutReason = FString::Printf(TEXT("ED LINE ENVELOPE OVERLAPS STORAGE %s"),
                *It->GetZoneId().ToString());
            return false;
        }
    }
    for (TActorIterator<ALBFactoryAGVInfrastructure> It(&World); It; ++It)
    {
        if (IsValid(*It) && Candidate.Intersect(InfrastructureEnvelope(**It, It->GetActorTransform())))
        {
            OutReason = FString::Printf(TEXT("ED LINE ENVELOPE OVERLAPS EDITABLE %s"),
                *It->GetInfrastructureId().ToString());
            return false;
        }
    }
    for (TActorIterator<ALBBodyWeldLineActor> It(&World); It; ++It)
    {
        if (!IsValid(*It)) continue;
        const UBoxComponent* Envelope = It->GetProtectedEnvelope();
        if (!Envelope) continue;
        const FVector OtherCentre = Envelope->GetRelativeLocation();
        const FVector OtherExtent = Envelope->GetUnscaledBoxExtent();
        if (Candidate.Intersect(FBox(OtherCentre - OtherExtent,
            OtherCentre + OtherExtent).TransformBy(It->GetActorTransform())))
        {
            OutReason = FString::Printf(TEXT("ED LINE ENVELOPE OVERLAPS BODY WELD LINE %s"),
                *It->GetLineId().ToString());
            return false;
        }
    }
    for (TActorIterator<ALBECoatLineActor> It(&World); It; ++It)
    {
        if (!IsValid(*It) || *It == IgnoredLine) continue;
        const FBox OtherLocal(It->GetProtectedEnvelopeRelativeCentreCm()
                - It->GetProtectedEnvelopeHalfExtentCm(),
            It->GetProtectedEnvelopeRelativeCentreCm() + It->GetProtectedEnvelopeHalfExtentCm());
        if (Candidate.Intersect(OtherLocal.TransformBy(It->GetActorTransform())))
        {
            OutReason = FString::Printf(TEXT("ED LINE ENVELOPE OVERLAPS %s"),
                *It->GetLineId().ToString());
            return false;
        }
    }

    const FVector CollisionHalfExtent(
        FMath::Max(1.0f, HalfExtent.X - 5.0f),
        FMath::Max(1.0f, HalfExtent.Y - 5.0f),
        FMath::Max(1.0f, HalfExtent.Z - 5.0f));
    FCollisionQueryParams Params(SCENE_QUERY_STAT(LBECoatLinePlacementEnvelope), false);
    Params.AddIgnoredActor(Authority);
    if (IgnoredLine) Params.AddIgnoredActor(IgnoredLine);
    for (TActorIterator<ALBFactoryBuildMachine> It(&World); It; ++It)
        if (IsValid(*It)) Params.AddIgnoredActor(*It);
    for (TActorIterator<ALBPressTrainAStation> It(&World); It; ++It)
        if (IsValid(*It)) Params.AddIgnoredActor(*It);
    for (TActorIterator<ALBPressShopStorageZone> It(&World); It; ++It)
        if (IsValid(*It)) Params.AddIgnoredActor(*It);
    for (TActorIterator<ALBFactoryAGVInfrastructure> It(&World); It; ++It)
        if (IsValid(*It)) Params.AddIgnoredActor(*It);
    for (TActorIterator<ALBBodyWeldLineActor> It(&World); It; ++It)
        if (IsValid(*It)) Params.AddIgnoredActor(*It);
    for (TActorIterator<ALBECoatLineActor> It(&World); It; ++It)
        if (IsValid(*It)) Params.AddIgnoredActor(*It);
    for (TActorIterator<ALBFactoryTransportLink> It(&World); It; ++It)
        if (IsValid(*It)) Params.AddIgnoredActor(*It);
    const FVector Centre = WorldTransform.TransformPosition(RelativeCentre);
    if (World.OverlapAnyTestByChannel(Centre, WorldTransform.GetRotation(), ECC_WorldDynamic,
        FCollisionShape::MakeBox(CollisionHalfExtent), Params))
    {
        OutReason = TEXT("ED LINE PROTECTED ENVELOPE IS OBSTRUCTED");
        return false;
    }

    OutReason = FString::Printf(TEXT("%s; 189 m ENVELOPE CLEAR; BODY-SHELL PORTS RESERVED"),
        *AuthorityReason);
    return true;
}

bool ValidateBodyWeldEnvelopeAgainstWorld(UWorld& World, const FTransform& WorldTransform,
    const ALBBodyWeldLineActor* IgnoredLine, FString& OutReason)
{
    FVector HalfExtent;
    FVector RelativeCentre;
    if (!GetBodyWeldPlacementEnvelope(HalfExtent, RelativeCentre))
    {
        OutReason = TEXT("BODY WELD LINE PLACEMENT CONTRACT IS OFFLINE");
        return false;
    }
    const FBox Candidate = FBox(RelativeCentre - HalfExtent,
        RelativeCentre + HalfExtent).TransformBy(WorldTransform);
    if (!IsOnSingleFactoryFloorDatum(World, Candidate, WorldTransform.GetLocation()))
    {
        OutReason = TEXT("BODY WELD LINE MUST SIT ON ONE FACTORY FLOOR DATUM WITH ITS COMPLETE 60 x 30 m FOOTPRINT INSIDE THE BUILD BAY");
        return false;
    }

    ALBPressShopBuildAuthority* Authority = nullptr;
    for (TActorIterator<ALBPressShopBuildAuthority> It(&World); It; ++It)
    {
        if (!IsValid(*It)) continue;
        if (Authority)
        {
            OutReason = TEXT("MULTIPLE FACTORY BUILD AUTHORITIES MAKE BODY WELD LINE PLACEMENT AMBIGUOUS");
            return false;
        }
        Authority = *It;
    }
    if (!Authority)
    {
        OutReason = TEXT("FACTORY BUILD FLOOR AUTHORITY IS OFFLINE");
        return false;
    }
    FString AuthorityReason;
    if (!Authority->EvaluateTrainEnvelope(Candidate, AuthorityReason))
    {
        AuthorityReason.ReplaceInline(TEXT("TRAIN FOOTPRINT"), TEXT("BODY WELD LINE FOOTPRINT"));
        AuthorityReason.ReplaceInline(TEXT("PRESS SHOP"), TEXT("FACTORY"));
        OutReason = FString::Printf(TEXT("BODY WELD LINE FOOTPRINT REJECTED: %s"), *AuthorityReason);
        return false;
    }
    AuthorityReason.ReplaceInline(TEXT("PRESS SHOP"), TEXT("FACTORY"));

    for (TActorIterator<ALBFactoryBuildMachine> It(&World); It; ++It)
    {
        if (!IsValid(*It)) continue;
        const FVector OtherCentre = It->GetProtectedEnvelopeRelativeCentre();
        const FVector OtherExtent = It->GetProtectedEnvelopeHalfExtent();
        if (Candidate.Intersect(FBox(OtherCentre - OtherExtent,
            OtherCentre + OtherExtent).TransformBy(It->GetActorTransform())))
        {
            OutReason = FString::Printf(TEXT("BODY WELD LINE ENVELOPE OVERLAPS MACHINE %s"),
                *It->GetMachineId().ToString());
            return false;
        }
    }
    for (TActorIterator<ALBPressTrainAStation> It(&World); It; ++It)
    {
        if (IsValid(*It) && Candidate.Intersect(
            ALBPressTrainAStation::GetProtectedLocalEnvelope().TransformBy(It->GetActorTransform())))
        {
            OutReason = FString::Printf(TEXT("BODY WELD LINE ENVELOPE OVERLAPS PRESS TRAIN %s"),
                *It->GetTrainId().ToString());
            return false;
        }
    }
    for (TActorIterator<ALBPressShopStorageZone> It(&World); It; ++It)
    {
        if (!IsValid(*It)) continue;
        const FVector Extent = It->GetZoneHalfExtent();
        if (Candidate.Intersect(FBox(-Extent, Extent).TransformBy(It->GetActorTransform())))
        {
            OutReason = FString::Printf(TEXT("BODY WELD LINE ENVELOPE OVERLAPS STORAGE %s"),
                *It->GetZoneId().ToString());
            return false;
        }
    }
    for (TActorIterator<ALBFactoryAGVInfrastructure> It(&World); It; ++It)
    {
        if (IsValid(*It) && Candidate.Intersect(InfrastructureEnvelope(**It, It->GetActorTransform())))
        {
            OutReason = FString::Printf(TEXT("BODY WELD LINE ENVELOPE OVERLAPS EDITABLE %s"),
                *It->GetInfrastructureId().ToString());
            return false;
        }
    }
    for (TActorIterator<ALBECoatLineActor> It(&World); It; ++It)
    {
        if (!IsValid(*It)) continue;
        const FVector OtherCentre = It->GetProtectedEnvelopeRelativeCentreCm();
        const FVector OtherExtent = It->GetProtectedEnvelopeHalfExtentCm();
        if (Candidate.Intersect(FBox(OtherCentre - OtherExtent,
            OtherCentre + OtherExtent).TransformBy(It->GetActorTransform())))
        {
            OutReason = FString::Printf(TEXT("BODY WELD LINE ENVELOPE OVERLAPS ED LINE %s"),
                *It->GetLineId().ToString());
            return false;
        }
    }
    for (TActorIterator<ALBBodyWeldLineActor> It(&World); It; ++It)
    {
        if (!IsValid(*It) || *It == IgnoredLine) continue;
        const UBoxComponent* Envelope = It->GetProtectedEnvelope();
        if (!Envelope) continue;
        const FVector OtherCentre = Envelope->GetRelativeLocation();
        const FVector OtherExtent = Envelope->GetUnscaledBoxExtent();
        if (Candidate.Intersect(FBox(OtherCentre - OtherExtent,
            OtherCentre + OtherExtent).TransformBy(It->GetActorTransform())))
        {
            OutReason = FString::Printf(TEXT("BODY WELD LINE ENVELOPE OVERLAPS %s"),
                *It->GetLineId().ToString());
            return false;
        }
    }

    const FVector CollisionHalfExtent(
        FMath::Max(1.0f, HalfExtent.X - 5.0f),
        FMath::Max(1.0f, HalfExtent.Y - 5.0f),
        FMath::Max(1.0f, HalfExtent.Z - 5.0f));
    FCollisionQueryParams Params(SCENE_QUERY_STAT(LBBodyWeldLinePlacementEnvelope), false);
    Params.AddIgnoredActor(Authority);
    if (IgnoredLine) Params.AddIgnoredActor(IgnoredLine);
    for (TActorIterator<ALBFactoryBuildMachine> It(&World); It; ++It)
        if (IsValid(*It)) Params.AddIgnoredActor(*It);
    for (TActorIterator<ALBPressTrainAStation> It(&World); It; ++It)
        if (IsValid(*It)) Params.AddIgnoredActor(*It);
    for (TActorIterator<ALBPressShopStorageZone> It(&World); It; ++It)
        if (IsValid(*It)) Params.AddIgnoredActor(*It);
    for (TActorIterator<ALBFactoryAGVInfrastructure> It(&World); It; ++It)
        if (IsValid(*It)) Params.AddIgnoredActor(*It);
    for (TActorIterator<ALBECoatLineActor> It(&World); It; ++It)
        if (IsValid(*It)) Params.AddIgnoredActor(*It);
    for (TActorIterator<ALBBodyWeldLineActor> It(&World); It; ++It)
        if (IsValid(*It)) Params.AddIgnoredActor(*It);
    for (TActorIterator<ALBFactoryTransportLink> It(&World); It; ++It)
        if (IsValid(*It)) Params.AddIgnoredActor(*It);
    const FVector CollisionCentre = WorldTransform.TransformPosition(RelativeCentre);
    if (World.OverlapAnyTestByChannel(CollisionCentre, WorldTransform.GetRotation(),
        ECC_WorldDynamic, FCollisionShape::MakeBox(CollisionHalfExtent), Params))
    {
        FString BlockingDescription(TEXT("UNKNOWN WORLD-DYNAMIC COMPONENT"));
        TArray<FOverlapResult> Overlaps;
        if (World.OverlapMultiByChannel(Overlaps, CollisionCentre,
            WorldTransform.GetRotation(), ECC_WorldDynamic,
            FCollisionShape::MakeBox(CollisionHalfExtent), Params))
        {
            for (const FOverlapResult& Overlap : Overlaps)
            {
                const AActor* BlockingActor = Overlap.GetActor();
                const UPrimitiveComponent* BlockingComponent = Overlap.GetComponent();
                if (!BlockingActor && !BlockingComponent) continue;
                BlockingDescription = FString::Printf(TEXT("%s / %s"),
                    BlockingActor ? *BlockingActor->GetActorNameOrLabel() : TEXT("NO ACTOR"),
                    BlockingComponent ? *BlockingComponent->GetName() : TEXT("NO COMPONENT"));
                break;
            }
        }
        OutReason = FString::Printf(
            TEXT("BODY WELD LINE PROTECTED ENVELOPE IS OBSTRUCTED BY %s"),
            *BlockingDescription);
        return false;
    }
    OutReason = FString::Printf(TEXT("%s; 60 x 30 m BODY WELD ENVELOPE CLEAR"),
        *AuthorityReason);
    return true;
}

bool HasBlockingWorldObstruction(UWorld& World, const FVector& HalfExtent,
    const FTransform& Transform, const AActor* IgnoredActor)
{
    const FVector CollisionHalfExtent(
        FMath::Max(1.0f, HalfExtent.X - 2.0f),
        FMath::Max(1.0f, HalfExtent.Y - 2.0f),
        FMath::Max(0.5f, HalfExtent.Z - 0.5f));
    const FVector Centre = Transform.TransformPosition(FVector(0.0f, 0.0f, HalfExtent.Z));
    const FBox Candidate(FVector(-HalfExtent.X, -HalfExtent.Y, 0.0f),
        FVector(HalfExtent.X, HalfExtent.Y, HalfExtent.Z * 2.0f));
    if (!IsOnSingleFactoryFloorDatum(World, Candidate.TransformBy(Transform),
        Transform.GetLocation())) return true;
    FCollisionQueryParams Params(SCENE_QUERY_STAT(LBInfrastructureEditWorldEnvelope), false);
    if (IgnoredActor) Params.AddIgnoredActor(IgnoredActor);
    for (TActorIterator<ALBFactoryAGVInfrastructure> It(&World); It; ++It)
        if (IsValid(*It)) Params.AddIgnoredActor(*It);
    // Machine, train and storage authorities are checked below with their larger protected
    // envelopes and original-overlap rollback semantics.
    for (TActorIterator<ALBFactoryBuildMachine> It(&World); It; ++It)
        if (IsValid(*It)) Params.AddIgnoredActor(*It);
    for (TActorIterator<ALBPressTrainAStation> It(&World); It; ++It)
        if (IsValid(*It)) Params.AddIgnoredActor(*It);
    for (TActorIterator<ALBPressShopStorageZone> It(&World); It; ++It)
        if (IsValid(*It)) Params.AddIgnoredActor(*It);
    for (TActorIterator<ALBECoatLineActor> It(&World); It; ++It)
        if (IsValid(*It)) Params.AddIgnoredActor(*It);
    for (TActorIterator<ALBBodyWeldLineActor> It(&World); It; ++It)
        if (IsValid(*It)) Params.AddIgnoredActor(*It);

    // Do not treat the support surface as a raised obstruction. Ignore the exact component
    // hit below the root, not its whole actor, so walls attached to a factory shell still block.
    FHitResult FloorHit;
    FCollisionObjectQueryParams FloorObjects;
    FloorObjects.AddObjectTypesToQuery(ECC_WorldStatic);
    FCollisionQueryParams FloorParams(SCENE_QUERY_STAT(LBInfrastructureEditFloor), false);
    if (IgnoredActor) FloorParams.AddIgnoredActor(IgnoredActor);
    const FVector Root = Transform.GetLocation();
    if (World.LineTraceSingleByObjectType(FloorHit, Root + FVector(0.0f, 0.0f, 20.0f),
        Root - FVector(0.0f, 0.0f, 200.0f), FloorObjects, FloorParams)
        && FloorHit.GetComponent()
        && FloorHit.GetComponent()->GetCollisionObjectType() == ECC_WorldStatic
        && FloorHit.GetComponent()->Bounds.GetBox().Max.Z <= Root.Z + 1.0f
        && FVector::DotProduct(FloorHit.ImpactNormal.GetSafeNormal(), FVector::UpVector) >= 0.9f)
    {
        Params.AddIgnoredComponent(FloorHit.GetComponent());
    }
    return World.OverlapBlockingTestByChannel(Centre, Transform.GetRotation(),
        ECC_WorldDynamic, FCollisionShape::MakeBox(CollisionHalfExtent), Params);
}

bool ValidateInfrastructureEnvelopeAgainstWorld(UWorld& World,
    const ELBFactoryAGVInfrastructureType Type, const FTransform& WorldTransform,
    const ALBFactoryAGVInfrastructure* IgnoredItem, const FBox* OriginalEnvelope,
    FString& OutReason, const ALBFactoryBuildMachine* AllowedStartMachine = nullptr,
    const ALBFactoryBuildMachine* AllowedDockMachine = nullptr)
{
    if (!WorldTransform.IsValid()
        || !WorldTransform.GetScale3D().Equals(FVector::OneVector, 0.001f))
    {
        OutReason = TEXT("PLAYER INFRASTRUCTURE PLACEMENT TRANSFORM IS INVALID");
        return false;
    }

    const FVector HalfExtent = ALBFactoryAGVInfrastructure::GetPlacementHalfExtentForType(Type);
    const FBox LocalEnvelope(FVector(-HalfExtent.X, -HalfExtent.Y, 0.0f),
        FVector(HalfExtent.X, HalfExtent.Y, HalfExtent.Z * 2.0f));
    const FBox Candidate = LocalEnvelope.TransformBy(WorldTransform);
    if (!IsOnSingleFactoryFloorDatum(World, Candidate, WorldTransform.GetLocation()))
    {
        OutReason = TEXT("INFRASTRUCTURE ROOT AND COMPLETE FOOTPRINT MUST REMAIN ON ONE AUTHORISED FACTORY FLOOR DATUM");
        return false;
    }

    ALBPressShopBuildAuthority* Authority = nullptr;
    for (TActorIterator<ALBPressShopBuildAuthority> It(&World); It; ++It)
    {
        if (!IsValid(*It)) continue;
        if (Authority)
        {
            OutReason = TEXT("MULTIPLE FACTORY FLOOR AUTHORITIES PREVENT A SAFE PLACEMENT");
            return false;
        }
        Authority = *It;
    }
    if (!Authority || Authority->BuildBays.IsEmpty())
    {
        OutReason = TEXT("FACTORY FLOOR BUILD AUTHORITY IS OFFLINE");
        return false;
    }
    for (const FLBPressShopProtectedArea& Area : Authority->ProtectedAreas)
    {
        if (Candidate.Intersect(FBox(Area.Centre - Area.HalfExtent, Area.Centre + Area.HalfExtent)))
        {
            OutReason = FString::Printf(TEXT("PROTECTED AREA %s MUST REMAIN CLEAR"),
                *Area.AreaId.ToString());
            return false;
        }
    }
    if (HasBlockingWorldObstruction(World, HalfExtent, WorldTransform, IgnoredItem))
    {
        OutReason = TEXT("RAISED WORLD OBSTRUCTION OCCUPIES THIS INFRASTRUCTURE ENVELOPE");
        return false;
    }

    const auto IsNewConflict = [&Candidate, OriginalEnvelope](const FBox& Other)
    {
        return Candidate.Intersect(Other)
            && (!OriginalEnvelope || !OriginalEnvelope->Intersect(Other));
    };
    for (TActorIterator<ALBFactoryBuildMachine> It(&World); It; ++It)
    {
        // A generated inbound route deliberately begins and ends inside its connected
        // handoff envelopes. Public/player placement passes no exceptions here.
        if (!IsValid(*It) || *It == AllowedStartMachine || *It == AllowedDockMachine) continue;
        const FVector Centre = It->GetProtectedEnvelopeRelativeCentre();
        const FVector Extent = It->GetProtectedEnvelopeHalfExtent();
        const FBox Other = FBox(Centre - Extent, Centre + Extent).TransformBy(It->GetActorTransform());
        if (IsNewConflict(Other))
        {
            OutReason = FString::Printf(TEXT("PROTECTED MACHINE ENVELOPE %s IS OBSTRUCTED"),
                *It->GetMachineId().ToString());
            return false;
        }
    }
    for (TActorIterator<ALBPressTrainAStation> It(&World); It; ++It)
    {
        if (!IsValid(*It)) continue;
        const FBox Other = ALBPressTrainAStation::GetProtectedLocalEnvelope().TransformBy(
            It->GetActorTransform());
        if (IsNewConflict(Other))
        {
            OutReason = FString::Printf(TEXT("PROTECTED PRESS-TRAIN ENVELOPE %s IS OBSTRUCTED"),
                *It->GetTrainId().ToString());
            return false;
        }
    }
    for (TActorIterator<ALBPressShopStorageZone> It(&World); It; ++It)
    {
        if (!IsValid(*It)) continue;
        const FVector Extent = It->GetZoneHalfExtent();
        const FBox Other = FBox(-Extent, Extent).TransformBy(It->GetActorTransform());
        if (IsNewConflict(Other))
        {
            OutReason = FString::Printf(TEXT("STORAGE ZONE %s OCCUPIES THIS FOOTPRINT"),
                *It->GetZoneId().ToString());
            return false;
        }
    }
    for (TActorIterator<ALBECoatLineActor> It(&World); It; ++It)
    {
        if (!IsValid(*It)) continue;
        const FBox OtherLocal(It->GetProtectedEnvelopeRelativeCentreCm()
                - It->GetProtectedEnvelopeHalfExtentCm(),
            It->GetProtectedEnvelopeRelativeCentreCm() + It->GetProtectedEnvelopeHalfExtentCm());
        // ECoat is a newly introduced hard safety authority. Do not preserve an old route
        // overlap with the tank/oven envelope: an edit must move the item clear.
        if (Candidate.Intersect(OtherLocal.TransformBy(It->GetActorTransform())))
        {
            OutReason = FString::Printf(TEXT("ED LINE %s OCCUPIES THIS FOOTPRINT"),
                *It->GetLineId().ToString());
            return false;
        }
    }
    for (TActorIterator<ALBBodyWeldLineActor> It(&World); It; ++It)
    {
        if (!IsValid(*It)) continue;
        const UBoxComponent* Envelope = It->GetProtectedEnvelope();
        if (!Envelope) continue;
        const FVector Centre = Envelope->GetRelativeLocation();
        const FVector Extent = Envelope->GetUnscaledBoxExtent();
        if (Candidate.Intersect(FBox(Centre - Extent,
            Centre + Extent).TransformBy(It->GetActorTransform())))
        {
            OutReason = FString::Printf(TEXT("BODY WELD LINE %s OCCUPIES THIS FOOTPRINT"),
                *It->GetLineId().ToString());
            return false;
        }
    }
    for (TActorIterator<ALBFactoryAGVInfrastructure> It(&World); It; ++It)
    {
        if (!IsValid(*It) || *It == IgnoredItem) continue;
        if (InfrastructureMayIntentionallyOverlap(Type, It->GetInfrastructureType())) continue;
        if (Candidate.Intersect(InfrastructureEnvelope(**It, It->GetActorTransform())))
        {
            OutReason = FString::Printf(TEXT("INFRASTRUCTURE %s OCCUPIES THIS FOOTPRINT"),
                *It->GetInfrastructureId().ToString());
            return false;
        }
    }
    OutReason = TEXT("FACTORY FLOOR, BODY WELD, ED LINE AND PROTECTED ENVELOPES ARE CLEAR");
    return true;
}

ALBFactoryBuildMachine* FindUniqueGenericMachine(UWorld* World, const FName MachineId,
    FString& OutReason)
{
    if (!World || MachineId.IsNone())
    {
        OutReason = TEXT("A VALID MACHINE ID IS REQUIRED");
        return nullptr;
    }
    ALBFactoryBuildMachine* Match = nullptr;
    for (TActorIterator<ALBFactoryBuildMachine> It(World); It; ++It)
    {
        if (!IsValid(*It) || It->GetMachineId() != MachineId) continue;
        if (Match)
        {
            OutReason = FString::Printf(TEXT("MACHINE ID %s IS DUPLICATED"),
                *MachineId.ToString());
            return nullptr;
        }
        Match = *It;
    }
    if (!Match)
        OutReason = FString::Printf(TEXT("MACHINE %s IS ALREADY ABSENT"), *MachineId.ToString());
    return Match;
}

bool ActorPropertyReferencesMachine(const AActor& Candidate,
    const ALBFactoryBuildMachine& Machine)
{
    for (TFieldIterator<FObjectPropertyBase> It(Candidate.GetClass()); It; ++It)
    {
        const FObjectPropertyBase* Property = *It;
        if (!Property) continue;
        for (int32 ArrayIndex = 0; ArrayIndex < Property->ArrayDim; ++ArrayIndex)
            if (Property->GetObjectPropertyValue_InContainer(&Candidate, ArrayIndex) == &Machine)
                return true;
    }
    for (TFieldIterator<FArrayProperty> It(Candidate.GetClass()); It; ++It)
    {
        const FArrayProperty* ArrayProperty = *It;
        const FObjectPropertyBase* ObjectInner = ArrayProperty
            ? CastField<FObjectPropertyBase>(ArrayProperty->Inner) : nullptr;
        if (!ObjectInner) continue;
        FScriptArrayHelper Helper(ArrayProperty,
            ArrayProperty->ContainerPtrToValuePtr<void>(&Candidate));
        for (int32 Index = 0; Index < Helper.Num(); ++Index)
            if (ObjectInner->GetObjectPropertyValue(Helper.GetRawPtr(Index)) == &Machine)
                return true;
    }
    return false;
}

bool ValidateGenericMachineEnvelopeAgainstWorld(UWorld& World,
    const FTransform& WorldTransform, const FVector& HalfExtent,
    const FVector& RelativeCentre, const ALBFactoryBuildMachine* IgnoredMachine,
    FString& OutReason)
{
    const FBox Candidate = FBox(RelativeCentre - HalfExtent,
        RelativeCentre + HalfExtent).TransformBy(WorldTransform);
    if (!IsOnSingleFactoryFloorDatum(World, Candidate, WorldTransform.GetLocation()))
    {
        OutReason = TEXT("MACHINE ROOT AND COMPLETE PROTECTED ENVELOPE MUST REMAIN ON ONE AUTHORISED FACTORY FLOOR DATUM");
        return false;
    }

    ALBPressShopBuildAuthority* Authority = nullptr;
    for (TActorIterator<ALBPressShopBuildAuthority> It(&World); It; ++It)
    {
        if (!IsValid(*It)) continue;
        if (Authority)
        {
            OutReason = TEXT("MULTIPLE FACTORY BUILD AUTHORITIES MAKE MACHINE PLACEMENT AMBIGUOUS");
            return false;
        }
        Authority = *It;
    }
    if (!Authority || Authority->BuildBays.IsEmpty())
    {
        OutReason = TEXT("FACTORY BUILD FLOOR AUTHORITY IS OFFLINE");
        return false;
    }
    for (const FLBPressShopProtectedArea& Area : Authority->ProtectedAreas)
    {
        if (Candidate.Intersect(FBox(Area.Centre - Area.HalfExtent,
            Area.Centre + Area.HalfExtent)))
        {
            OutReason = FString::Printf(TEXT("PROTECTED AREA %s MUST REMAIN CLEAR"),
                *Area.AreaId.ToString());
            return false;
        }
    }

    for (TActorIterator<ALBFactoryBuildMachine> It(&World); It; ++It)
    {
        if (!IsValid(*It) || *It == IgnoredMachine) continue;
        const FVector OtherCentre = It->GetProtectedEnvelopeRelativeCentre();
        const FVector OtherExtent = It->GetProtectedEnvelopeHalfExtent();
        if (Candidate.Intersect(FBox(OtherCentre - OtherExtent,
            OtherCentre + OtherExtent).TransformBy(It->GetActorTransform())))
        {
            OutReason = FString::Printf(TEXT("MACHINE ENVELOPE OVERLAPS %s"),
                *It->GetMachineId().ToString());
            return false;
        }
    }
    for (TActorIterator<ALBPressTrainAStation> It(&World); It; ++It)
    {
        if (IsValid(*It) && Candidate.Intersect(
            ALBPressTrainAStation::GetProtectedLocalEnvelope().TransformBy(It->GetActorTransform())))
        {
            OutReason = FString::Printf(TEXT("MACHINE ENVELOPE OVERLAPS PRESS TRAIN %s"),
                *It->GetTrainId().ToString());
            return false;
        }
    }
    for (TActorIterator<ALBPressShopStorageZone> It(&World); It; ++It)
    {
        if (!IsValid(*It)) continue;
        const FVector Extent = It->GetZoneHalfExtent();
        if (Candidate.Intersect(FBox(-Extent, Extent).TransformBy(It->GetActorTransform())))
        {
            OutReason = FString::Printf(TEXT("MACHINE ENVELOPE OVERLAPS STORAGE %s"),
                *It->GetZoneId().ToString());
            return false;
        }
    }
    for (TActorIterator<ALBFactoryAGVInfrastructure> It(&World); It; ++It)
    {
        if (IsValid(*It) && Candidate.Intersect(
            InfrastructureEnvelope(**It, It->GetActorTransform())))
        {
            OutReason = FString::Printf(TEXT("MACHINE ENVELOPE OVERLAPS INFRASTRUCTURE %s"),
                *It->GetInfrastructureId().ToString());
            return false;
        }
    }
    for (TActorIterator<ALBECoatLineActor> It(&World); It; ++It)
    {
        if (!IsValid(*It)) continue;
        const FVector Centre = It->GetProtectedEnvelopeRelativeCentreCm();
        const FVector Extent = It->GetProtectedEnvelopeHalfExtentCm();
        if (Candidate.Intersect(FBox(Centre - Extent,
            Centre + Extent).TransformBy(It->GetActorTransform())))
        {
            OutReason = FString::Printf(TEXT("MACHINE ENVELOPE OVERLAPS ED LINE %s"),
                *It->GetLineId().ToString());
            return false;
        }
    }
    for (TActorIterator<ALBBodyWeldLineActor> It(&World); It; ++It)
    {
        if (!IsValid(*It)) continue;
        const UBoxComponent* Envelope = It->GetProtectedEnvelope();
        if (!Envelope) continue;
        const FVector Centre = Envelope->GetRelativeLocation();
        const FVector Extent = Envelope->GetUnscaledBoxExtent();
        if (Candidate.Intersect(FBox(Centre - Extent,
            Centre + Extent).TransformBy(It->GetActorTransform())))
        {
            OutReason = FString::Printf(TEXT("MACHINE ENVELOPE OVERLAPS BODY WELD LINE %s"),
                *It->GetLineId().ToString());
            return false;
        }
    }

    const FVector CollisionHalfExtent(
        FMath::Max(1.0f, HalfExtent.X - 2.0f),
        FMath::Max(1.0f, HalfExtent.Y - 2.0f),
        FMath::Max(1.0f, HalfExtent.Z - 2.0f));
    FCollisionQueryParams Params(SCENE_QUERY_STAT(LBGenericMachineEditEnvelope), false);
    Params.AddIgnoredActor(Authority);
    if (IgnoredMachine) Params.AddIgnoredActor(IgnoredMachine);
    for (TActorIterator<ALBFactoryBuildMachine> It(&World); It; ++It)
        if (IsValid(*It)) Params.AddIgnoredActor(*It);
    for (TActorIterator<ALBPressTrainAStation> It(&World); It; ++It)
        if (IsValid(*It)) Params.AddIgnoredActor(*It);
    for (TActorIterator<ALBPressShopStorageZone> It(&World); It; ++It)
        if (IsValid(*It)) Params.AddIgnoredActor(*It);
    for (TActorIterator<ALBFactoryAGVInfrastructure> It(&World); It; ++It)
        if (IsValid(*It)) Params.AddIgnoredActor(*It);
    for (TActorIterator<ALBECoatLineActor> It(&World); It; ++It)
        if (IsValid(*It)) Params.AddIgnoredActor(*It);
    for (TActorIterator<ALBBodyWeldLineActor> It(&World); It; ++It)
        if (IsValid(*It)) Params.AddIgnoredActor(*It);
    for (TActorIterator<ALBFactoryTransportLink> It(&World); It; ++It)
        if (IsValid(*It)) Params.AddIgnoredActor(*It);
    if (World.OverlapBlockingTestByChannel(WorldTransform.TransformPosition(RelativeCentre),
        WorldTransform.GetRotation(), ECC_WorldDynamic,
        FCollisionShape::MakeBox(CollisionHalfExtent), Params))
    {
        OutReason = TEXT("MACHINE PROTECTED ENVELOPE IS OBSTRUCTED");
        return false;
    }

    OutReason = TEXT("MACHINE FLOOR DATUM AND COMPLETE PROTECTED ENVELOPE ARE CLEAR");
    return true;
}
}

bool ULBFactoryMachineBuilderSubsystem::HasGenericMachine(const ELBFactoryBuildMachineType Type) const
{
    if (!GetWorld()) return false;
    for (TActorIterator<ALBFactoryBuildMachine> It(GetWorld()); It; ++It)
        if (IsValid(*It) && It->GetMachineType() == Type) return true;
    return false;
}

bool ULBFactoryMachineBuilderSubsystem::HasECoatLine() const
{
    if (!GetWorld()) return false;
    for (TActorIterator<ALBECoatLineActor> It(GetWorld()); It; ++It)
        if (IsValid(*It)) return true;
    return false;
}

bool ULBFactoryMachineBuilderSubsystem::HasBodyWeldLine() const
{
    if (!GetWorld()) return false;
    for (TActorIterator<ALBBodyWeldLineActor> It(GetWorld()); It; ++It)
        if (IsValid(*It)) return true;
    return false;
}

bool ULBFactoryMachineBuilderSubsystem::HasStorageType(const uint8 StorageTypeValue) const
{
    if (!GetWorld()) return false;
    for (TActorIterator<ALBPressShopStorageZone> It(GetWorld()); It; ++It)
        if (IsValid(*It) && static_cast<uint8>(It->GetStorageType()) == StorageTypeValue) return true;
    return false;
}

bool ULBFactoryMachineBuilderSubsystem::CanPlaceMachine(
    const ELBFactoryBuildMachineType MachineType, FString& OutReason) const
{
    OutReason.Reset();
    UWorld* World = GetWorld();
    if (!World)
    {
        OutReason = TEXT("FACTORY BUILDER WORLD IS OFFLINE");
        return false;
    }
    switch (MachineType)
    {
    case ELBFactoryBuildMachineType::InboundDeliveryDock:
        if (HasGenericMachine(MachineType))
        {
            OutReason = TEXT("THE PRESS SHOP ALREADY HAS ITS INBOUND DELIVERY AUTHORITY");
            return false;
        }
        break;
    case ELBFactoryBuildMachineType::DepackagingRobot:
        if (!HasGenericMachine(ELBFactoryBuildMachineType::InboundDeliveryDock))
        {
            OutReason = TEXT("PLACE THE INBOUND DELIVERY CELL FIRST");
            return false;
        }
        if (!HasGenericMachine(ELBFactoryBuildMachineType::CoilWeighInspectionCell))
        {
            OutReason = TEXT("PLACE THE PR002 COIL WEIGH / INSPECTION CELL FIRST");
            return false;
        }
        if (!HasStorageType(static_cast<uint8>(ELBPressShopStorageType::BareCoils)))
        {
            OutReason = TEXT("PLACE AND CONNECT WRAPPED COIL STORAGE AFTER PR002");
            return false;
        }
        break;
    case ELBFactoryBuildMachineType::CoilWeighInspectionCell:
        if (!HasGenericMachine(ELBFactoryBuildMachineType::InboundDeliveryDock))
        {
            OutReason = TEXT("PLACE THE INBOUND DELIVERY CELL FIRST");
            return false;
        }
        if (HasGenericMachine(MachineType))
        {
            OutReason = TEXT("THE PRESS SHOP ALREADY HAS ITS PR002 COIL WEIGH / INSPECTION CELL");
            return false;
        }
        if (!HasStorageType(static_cast<uint8>(ELBPressShopStorageType::BareCoils)))
        {
            OutReason = TEXT("PLACE WRAPPED COIL STORAGE SO THE UNLOAD AGV HAS A SAFE BUFFER");
            return false;
        }
        break;
    case ELBFactoryBuildMachineType::DecoilerFeeder:
        if (!HasGenericMachine(ELBFactoryBuildMachineType::DepackagingRobot))
        {
            OutReason = TEXT("PLACE A DEPACKAGING ROBOT FIRST");
            return false;
        }
        break;
    case ELBFactoryBuildMachineType::PressTrain:
    {
        if (!HasGenericMachine(ELBFactoryBuildMachineType::DecoilerFeeder))
        {
            OutReason = TEXT("PLACE A PR005-PR010 COIL PREPARATION LINE FIRST");
            return false;
        }
        if (!HasStorageType(static_cast<uint8>(ELBPressShopStorageType::PreparedBlanks)))
        {
            OutReason = TEXT("PLACE A PREPARED-BLANK BUFFER FIRST");
            return false;
        }
        int32 LiveTrainCount = 0;
        for (TActorIterator<ALBPressTrainAStation> It(World); It; ++It)
            if (IsValid(*It)) ++LiveTrainCount;
        if (LiveTrainCount >= 4)
        {
            OutReason = TEXT("THE FOUR AUTHORED PRESS TRAINS A-D ARE ALREADY INSTALLED");
            return false;
        }
        break;
    }
    case ELBFactoryBuildMachineType::InspectionCell:
    {
        bool bHasTrain = false;
        for (TActorIterator<ALBPressTrainAStation> It(World); It; ++It) bHasTrain |= IsValid(*It);
        if (!bHasTrain)
        {
            OutReason = TEXT("PLACE A PRESS TRAIN FIRST");
            return false;
        }
        break;
    }
    case ELBFactoryBuildMachineType::OutboundPanelDock:
        if (!HasGenericMachine(ELBFactoryBuildMachineType::InspectionCell))
        {
            OutReason = TEXT("PLACE A PANEL INSPECTION CELL FIRST");
            return false;
        }
        if (!HasStorageType(static_cast<uint8>(ELBPressShopStorageType::FinishedPanelStillages)))
        {
            OutReason = TEXT("PLACE A FULL PRESSED-PANEL STILLAGE BUFFER FIRST");
            return false;
        }
        if (!HasStorageType(static_cast<uint8>(ELBPressShopStorageType::EmptyPanelStillages)))
        {
            OutReason = TEXT("PLACE AN EMPTY STILLAGE RETURN STORE FIRST");
            return false;
        }
        break;
    case ELBFactoryBuildMachineType::BodyWeldLine:
        if (!HasGenericMachine(ELBFactoryBuildMachineType::OutboundPanelDock))
        {
            OutReason = TEXT("COMPLETE THE PRESSED-PANEL WIP BUFFER AND WELD SHOP INTAKE FIRST");
            return false;
        }
        if (HasBodyWeldLine())
        {
            OutReason = TEXT("THE FACTORY ALREADY HAS ITS COMPLETE BODY WELD LINE");
            return false;
        }
        break;
    case ELBFactoryBuildMachineType::ECoatLine:
        if (!HasBodyWeldLine())
        {
            OutReason = TEXT("PLACE THE COMPLETE BODY WELD LINE FIRST");
            return false;
        }
        if (HasECoatLine())
        {
            OutReason = TEXT("THE FACTORY ALREADY HAS ITS COMPLETE ED / E-COAT LINE");
            return false;
        }
        break;
    default:
        OutReason = TEXT("MACHINE TYPE IS NOT IN THE PRESS SHOP CATALOGUE");
        return false;
    }
    OutReason = TEXT("NEXT REQUIRED MACHINE IS AVAILABLE");
    return true;
}

TArray<ELBPressShopStorageType> ULBFactoryMachineBuilderSubsystem::GetAvailableStorageTypes() const
{
    TArray<ELBPressShopStorageType> Result;
    if (!HasGenericMachine(ELBFactoryBuildMachineType::InboundDeliveryDock)) return Result;

    // Extra upstream capacity remains available after it is first unlocked so a player can
    // respond to a visible bottleneck without breaking process order.
    Result.Add(ELBPressShopStorageType::MaintenanceParts);
    Result.Add(ELBPressShopStorageType::Quarantine);

    // The first storage zone is deliberately available as soon as the unloading cell exists.
    // That lets the handler remove and safely hold a coil while the player lays out the buffer.
    Result.Add(ELBPressShopStorageType::BareCoils);

    if (HasGenericMachine(ELBFactoryBuildMachineType::DecoilerFeeder))
        Result.Add(ELBPressShopStorageType::PreparedBlanks);

    bool bHasTrain = false;
    if (GetWorld())
        for (TActorIterator<ALBPressTrainAStation> It(GetWorld()); It; ++It) bHasTrain |= IsValid(*It);
    if (bHasTrain) Result.Add(ELBPressShopStorageType::Scrap);

    if (HasGenericMachine(ELBFactoryBuildMachineType::InspectionCell))
    {
        Result.Add(ELBPressShopStorageType::EmptyPanelStillages);
        Result.Add(ELBPressShopStorageType::FinishedPanelStillages);
    }
    return Result;
}

bool ULBFactoryMachineBuilderSubsystem::CanPlaceAGVInfrastructure(
    const ELBFactoryAGVInfrastructureType Type, const int32 TrainIndex, FString& OutReason) const
{
    OutReason.Reset();
    UWorld* World = GetWorld();
    if (!World)
    {
        OutReason = TEXT("FACTORY BUILDER WORLD IS OFFLINE");
        return false;
    }

    const bool bNeedsInbound = Type == ELBFactoryAGVInfrastructureType::ChargingStation
        || Type == ELBFactoryAGVInfrastructureType::WaitPoint
        || Type == ELBFactoryAGVInfrastructureType::RouteWaypoint
        || Type == ELBFactoryAGVInfrastructureType::PressTrainHandoff
        || Type == ELBFactoryAGVInfrastructureType::AGVRouteSegment;
    if (bNeedsInbound && !HasGenericMachine(ELBFactoryBuildMachineType::InboundDeliveryDock))
    {
        OutReason = TEXT("PLACE THE INBOUND DELIVERY CELL BEFORE ITS AGV INFRASTRUCTURE");
        return false;
    }

    int32 MatchingCount = 0;
    for (TActorIterator<ALBFactoryAGVInfrastructure> It(World); It; ++It)
    {
        if (!IsValid(*It) || It->GetInfrastructureType() != Type) continue;
        ++MatchingCount;
        if (Type == ELBFactoryAGVInfrastructureType::PressTrainHandoff
            && It->GetTrainIndex() == TrainIndex)
        {
            OutReason = FString::Printf(TEXT("TRAIN %c ALREADY HAS ITS S01 AGV HANDOFF"), TCHAR('A' + TrainIndex));
            return false;
        }
    }

    if (Type == ELBFactoryAGVInfrastructureType::ChargingStation && MatchingCount >= 4)
    {
        OutReason = TEXT("THE REFERENCE PRESS SHOP ALREADY HAS FOUR AGV CHARGING STATIONS");
        return false;
    }
    if (Type == ELBFactoryAGVInfrastructureType::PressTrainHandoff
        && !FMath::IsWithinInclusive(TrainIndex, 0, 3))
    {
        OutReason = TEXT("PRESS-TRAIN AGV HANDOFF REQUIRES TRAIN INDEX 0-3 (A-D)");
        return false;
    }
    if (Type != ELBFactoryAGVInfrastructureType::PressTrainHandoff && TrainIndex != INDEX_NONE)
    {
        OutReason = TEXT("ONLY A PRESS-TRAIN HANDOFF MAY HAVE A TRAIN INDEX");
        return false;
    }
    OutReason = TEXT("AGV INFRASTRUCTURE IS AVAILABLE FOR PLAYER PLACEMENT");
    return true;
}

TArray<ELBFactoryAGVInfrastructureType> ULBFactoryMachineBuilderSubsystem::GetAvailableInfrastructureTypes() const
{
    TArray<ELBFactoryAGVInfrastructureType> Result;
    // Pedestrian and guarding infrastructure can be laid before the production line exists.
    Result.Add(ELBFactoryAGVInfrastructureType::PedestrianWalkway);
    Result.Add(ELBFactoryAGVInfrastructureType::PedestrianCrossing);
    Result.Add(ELBFactoryAGVInfrastructureType::SafetyFence);
    if (HasGenericMachine(ELBFactoryBuildMachineType::InboundDeliveryDock))
    {
        Result.Add(ELBFactoryAGVInfrastructureType::AGVRouteSegment);
        Result.Add(ELBFactoryAGVInfrastructureType::RouteWaypoint);
        Result.Add(ELBFactoryAGVInfrastructureType::WaitPoint);
        Result.Add(ELBFactoryAGVInfrastructureType::ChargingStation);
        Result.Add(ELBFactoryAGVInfrastructureType::PressTrainHandoff);
    }
    return Result;
}

int32 ULBFactoryMachineBuilderSubsystem::GetNextAvailablePressTrainHandoffIndex() const
{
    TSet<int32> Assigned;
    if (GetWorld())
    {
        for (TActorIterator<ALBFactoryAGVInfrastructure> It(GetWorld()); It; ++It)
        {
            if (IsValid(*It)
                && It->GetInfrastructureType() == ELBFactoryAGVInfrastructureType::PressTrainHandoff
                && FMath::IsWithinInclusive(It->GetTrainIndex(), 0, 3))
            {
                Assigned.Add(It->GetTrainIndex());
            }
        }
    }
    for (int32 TrainIndex = 0; TrainIndex < 4; ++TrainIndex)
        if (!Assigned.Contains(TrainIndex)) return TrainIndex;
    return INDEX_NONE;
}

FName ULBFactoryMachineBuilderSubsystem::AllocateAGVInfrastructureId(
    const ELBFactoryAGVInfrastructureType Type, const int32 TrainIndex) const
{
    if (Type == ELBFactoryAGVInfrastructureType::PressTrainHandoff
        && FMath::IsWithinInclusive(TrainIndex, 0, 3))
        return FName(*FString::Printf(TEXT("S01-HANDOFF-%c"), TCHAR('A' + TrainIndex)));

    TSet<FName> Used;
    if (GetWorld())
        for (TActorIterator<ALBFactoryAGVInfrastructure> It(GetWorld()); It; ++It)
            if (IsValid(*It)) Used.Add(It->GetInfrastructureId());
    for (int32 Sequence = 1; Sequence <= 999; ++Sequence)
    {
        const FName Candidate(*FString::Printf(TEXT("%s-%02d"), AGVInfrastructurePrefix(Type), Sequence));
        if (!Used.Contains(Candidate)) return Candidate;
    }
    return NAME_None;
}

bool ULBFactoryMachineBuilderSubsystem::PlaceAGVInfrastructure(
    const ELBFactoryAGVInfrastructureType Type, const int32 TrainIndex,
    const FTransform& WorldTransform, ALBFactoryAGVInfrastructure*& OutInfrastructure, FString& OutReason)
{
    return PlaceAGVInfrastructureAllowingConnectedMachines(Type, TrainIndex, WorldTransform,
        nullptr, nullptr, OutInfrastructure, OutReason);
}

bool ULBFactoryMachineBuilderSubsystem::PlaceAGVInfrastructureAllowingConnectedMachines(
    const ELBFactoryAGVInfrastructureType Type, const int32 TrainIndex,
    const FTransform& WorldTransform, const ALBFactoryBuildMachine* AllowedStartMachine,
    const ALBFactoryBuildMachine* AllowedDockMachine,
    ALBFactoryAGVInfrastructure*& OutInfrastructure, FString& OutReason)
{
    OutInfrastructure = nullptr;
    UWorld* World = GetWorld();
    if (!World || !CanPlaceAGVInfrastructure(Type, TrainIndex, OutReason)
        || !ValidateInfrastructureEnvelopeAgainstWorld(*World, Type, WorldTransform,
            nullptr, nullptr, OutReason, AllowedStartMachine, AllowedDockMachine)) return false;
    const FName Id = AllocateAGVInfrastructureId(Type, TrainIndex);
    ALBFactoryAGVInfrastructure* Infrastructure = World->SpawnActor<ALBFactoryAGVInfrastructure>(
        ALBFactoryAGVInfrastructure::StaticClass(), WorldTransform);
    if (!Infrastructure || !Infrastructure->Configure(Id, Type, TrainIndex))
    {
        if (Infrastructure) Infrastructure->Destroy();
        OutReason = TEXT("AGV INFRASTRUCTURE PACKAGE COULD NOT BE CREATED");
        return false;
    }
    OutInfrastructure = Infrastructure;
    OutReason = FString::Printf(TEXT("PLACED PLAYER-BUILT %s"), *Id.ToString());
    return true;
}

bool ULBFactoryMachineBuilderSubsystem::ValidateAGVInfrastructurePlacement(
    const ELBFactoryAGVInfrastructureType Type, const int32 TrainIndex,
    const FTransform& WorldTransform, FString& OutReason) const
{
    UWorld* World = GetWorld();
    if (!World || !CanPlaceAGVInfrastructure(Type, TrainIndex, OutReason)) return false;
    return ValidateInfrastructureEnvelopeAgainstWorld(*World, Type, WorldTransform,
        nullptr, nullptr, OutReason);
}

bool ULBFactoryMachineBuilderSubsystem::UpdateAGVInfrastructureTransform(
    const FName InfrastructureId, const FTransform& WorldTransform, FString& OutReason)
{
    UWorld* World = GetWorld();
    if (!World || InfrastructureId.IsNone() || !WorldTransform.IsValid()
        || !WorldTransform.GetScale3D().Equals(FVector::OneVector, 0.001f))
    {
        OutReason = TEXT("PLAYER INFRASTRUCTURE EDIT TRANSFORM IS INVALID");
        return false;
    }
    for (TActorIterator<ALBFactoryAGVInfrastructure> It(World); It; ++It)
    {
        if (!IsValid(*It) || It->GetInfrastructureId() != InfrastructureId) continue;
        if (!CanEditAGVInfrastructure(InfrastructureId, OutReason)
            || !ValidateAGVInfrastructureTransform(InfrastructureId, WorldTransform, OutReason))
            return false;
        const FTransform PreviousTransform = It->GetActorTransform();
        if (!It->SetActorTransform(WorldTransform, false, nullptr, ETeleportType::TeleportPhysics))
        {
            OutReason = TEXT("PLAYER INFRASTRUCTURE EDIT COULD NOT BE APPLIED");
            return false;
        }
        if (!RebindIdleCoilAGVsAfterInfrastructureEdit(*It, OutReason))
        {
            It->SetActorTransform(PreviousTransform, false, nullptr, ETeleportType::TeleportPhysics);
            FString RebindRollbackReason;
            RebindIdleCoilAGVsAfterInfrastructureEdit(*It, RebindRollbackReason);
            OutReason = FString::Printf(TEXT("EDIT ROLLED BACK: %s"), *OutReason);
            return false;
        }
        It->MarkPlayerEdited();
        OutReason = FString::Printf(TEXT("UPDATED PLAYER-BUILT %s"), *InfrastructureId.ToString());
        return true;
    }
    OutReason = FString::Printf(TEXT("PLAYER-BUILT %s WAS NOT FOUND"), *InfrastructureId.ToString());
    return false;
}

bool ULBFactoryMachineBuilderSubsystem::CanEditAGVInfrastructure(
    const FName InfrastructureId, FString& OutReason) const
{
    UWorld* World = GetWorld();
    ALBFactoryAGVInfrastructure* Item = nullptr;
    if (World)
        for (TActorIterator<ALBFactoryAGVInfrastructure> It(World); It; ++It)
            if (IsValid(*It) && It->GetInfrastructureId() == InfrastructureId)
            { Item = *It; break; }
    if (!Item)
    {
        OutReason = TEXT("SELECTED INFRASTRUCTURE WAS NOT FOUND");
        return false;
    }
    if (!IsRouteAuthorityType(Item->GetInfrastructureType()))
    {
        OutReason = TEXT("INFRASTRUCTURE IS SAFE TO EDIT");
        return true;
    }
    for (TActorIterator<ALBCoilAGVController> It(World); It; ++It)
    {
        if (!IsValid(*It)) continue;
        if (It->GetRouteProfile() == ELBCoilAGVRouteProfile::ManualOrUnassigned)
        {
            OutReason = TEXT("ASSIGN OR CONFIGURE EVERY LIVE COIL AGV ROUTE BEFORE EDITING ROUTE INFRASTRUCTURE");
            return false;
        }
        if (!IsAGVAffectedByInfrastructureEdit(**It, *Item)) continue;
        const ELBCoilAGVPhase Phase = It->GetPhase();
        if (Phase != ELBCoilAGVPhase::IdleLoaded && Phase != ELBCoilAGVPhase::AwaitingReload)
        {
            OutReason = TEXT("WAIT FOR THE COIL AGV TO STOP AT A STAGED POINT BEFORE EDITING ITS ROUTE");
            return false;
        }
    }
    OutReason = TEXT("ALL ROUTE USERS ARE IDLE");
    return true;
}

bool ULBFactoryMachineBuilderSubsystem::ValidateAGVInfrastructureTransform(
    const FName InfrastructureId, const FTransform& WorldTransform, FString& OutReason) const
{
    UWorld* World = GetWorld();
    if (!World || InfrastructureId.IsNone() || !WorldTransform.IsValid()
        || !WorldTransform.GetScale3D().Equals(FVector::OneVector, 0.001f))
    {
        OutReason = TEXT("PLAYER INFRASTRUCTURE EDIT TRANSFORM IS INVALID");
        return false;
    }

    ALBFactoryAGVInfrastructure* Item = nullptr;
    for (TActorIterator<ALBFactoryAGVInfrastructure> It(World); It; ++It)
        if (IsValid(*It) && It->GetInfrastructureId() == InfrastructureId)
        { Item = *It; break; }
    if (!Item)
    {
        OutReason = TEXT("SELECTED INFRASTRUCTURE WAS NOT FOUND");
        return false;
    }

    const FBox OriginalEnvelope = InfrastructureEnvelope(*Item, Item->GetActorTransform());
    return ValidateInfrastructureEnvelopeAgainstWorld(*World, Item->GetInfrastructureType(),
        WorldTransform, Item, &OriginalEnvelope, OutReason);
}

bool ULBFactoryMachineBuilderSubsystem::RebindIdleCoilAGVsAfterInfrastructureEdit(
    ALBFactoryAGVInfrastructure* Edited, FString& OutReason) const
{
    if (!Edited || !IsRouteAuthorityType(Edited->GetInfrastructureType()) || !GetWorld()) return true;
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
    for (TActorIterator<ALBCoilAGVController> It(GetWorld()); It; ++It)
    {
        ALBCoilAGVController* AGV = *It;
        if (!IsValid(AGV)) continue;
        if (AGV->GetRouteProfile() == ELBCoilAGVRouteProfile::ManualOrUnassigned)
        {
            OutReason = TEXT("ASSIGN OR CONFIGURE EVERY LIVE COIL AGV ROUTE BEFORE EDITING ROUTE INFRASTRUCTURE");
            return false;
        }
        if (!IsAGVAffectedByInfrastructureEdit(*AGV, *Edited)) continue;
        bool bRebound = false;
        switch (AGV->GetRouteProfile())
        {
        case ELBCoilAGVRouteProfile::InboundPR002:
            bRebound = InboundCount == 1 && PR002Count == 1
                && AGV->ConfigureInboundRouteFromPlayerBuiltInfrastructure(Inbound, PR002);
            break;
        case ELBCoilAGVRouteProfile::PressTrainHandoff:
            bRebound = AGV->ConfigureFromPlayerBuiltInfrastructure(
                AGV->GetAssignedRouteTrainIndex());
            break;
        case ELBCoilAGVRouteProfile::ManualOrUnassigned:
        default:
            continue;
        }
        if (!bRebound)
        {
            OutReason = TEXT("EDIT WOULD BREAK THE CERTIFIED AGV ROUTE; MOVE CONNECTED TILES IN A LATER ROUTE EDIT SESSION");
            return false;
        }
    }
    return true;
}

bool ULBFactoryMachineBuilderSubsystem::CaptureAGVInfrastructure(
    TArray<FLBFactoryAGVInfrastructureSaveState>& OutStates) const
{
    OutStates.Reset();
    if (!GetWorld()) return false;
    TSet<FName> Ids;
    for (TActorIterator<ALBFactoryAGVInfrastructure> It(GetWorld()); It; ++It)
    {
        if (!IsValid(*It) || It->GetInfrastructureId().IsNone() || Ids.Contains(It->GetInfrastructureId())) return false;
        Ids.Add(It->GetInfrastructureId());
        OutStates.Add(It->CaptureSaveState());
    }
    OutStates.Sort([](const FLBFactoryAGVInfrastructureSaveState& A,
        const FLBFactoryAGVInfrastructureSaveState& B)
        { return A.InfrastructureId.LexicalLess(B.InfrastructureId); });
    return true;
}

bool ULBFactoryMachineBuilderSubsystem::RestoreAGVInfrastructure(
    const TArray<FLBFactoryAGVInfrastructureSaveState>& States, FString& OutReason)
{
    UWorld* World = GetWorld();
    if (!World) return false;
    TSet<FName> Ids;
    TSet<int32> HandoffTrainIndices;
    int32 ChargerCount = 0;
    for (const FLBFactoryAGVInfrastructureSaveState& State : States)
    {
        if ((State.Version != 1 && State.Version != 2) || State.InfrastructureId.IsNone() || Ids.Contains(State.InfrastructureId)
            || !State.WorldTransform.IsValid() || !State.WorldTransform.GetScale3D().Equals(FVector::OneVector, 0.001f))
        {
            OutReason = TEXT("SAVED AGV INFRASTRUCTURE SET IS INVALID");
            return false;
        }
        Ids.Add(State.InfrastructureId);
        if (State.Type == ELBFactoryAGVInfrastructureType::ChargingStation && ++ChargerCount > 4)
        {
            OutReason = TEXT("SAVED AGV INFRASTRUCTURE EXCEEDS FOUR CHARGERS");
            return false;
        }
        if (State.Type == ELBFactoryAGVInfrastructureType::PressTrainHandoff)
        {
            if (!FMath::IsWithinInclusive(State.TrainIndex, 0, 3) || HandoffTrainIndices.Contains(State.TrainIndex))
            {
                OutReason = TEXT("SAVED AGV INFRASTRUCTURE HAS AN INVALID OR DUPLICATE TRAIN HANDOFF");
                return false;
            }
            HandoffTrainIndices.Add(State.TrainIndex);
        }
        else if (State.TrainIndex != INDEX_NONE)
        {
            OutReason = TEXT("SAVED NON-HANDOFF AGV INFRASTRUCTURE HAS A TRAIN INDEX");
            return false;
        }
    }

    TArray<ALBFactoryAGVInfrastructure*> Existing;
    for (TActorIterator<ALBFactoryAGVInfrastructure> It(World); It; ++It) Existing.Add(*It);
    for (int32 Index = 0; Index < States.Num(); ++Index)
    {
        ALBFactoryAGVInfrastructure* Item = Existing.IsValidIndex(Index) ? Existing[Index]
            : World->SpawnActor<ALBFactoryAGVInfrastructure>();
        if (!Item || !Item->RestoreSaveState(States[Index]))
        {
            OutReason = TEXT("SAVED AGV INFRASTRUCTURE COULD NOT BE RESTORED");
            return false;
        }
    }
    for (int32 Index = States.Num(); Index < Existing.Num(); ++Index)
        if (Existing[Index]) Existing[Index]->Destroy();
    OutReason = FString::Printf(TEXT("RESTORED %d PLAYER-BUILT AGV INFRASTRUCTURE ITEM(S)"), States.Num());
    return true;
}

FName ULBFactoryMachineBuilderSubsystem::AllocateMachineId(const ELBFactoryBuildMachineType Type) const
{
    TSet<FName> Used;
    if (GetWorld())
        for (TActorIterator<ALBFactoryBuildMachine> It(GetWorld()); It; ++It)
            if (IsValid(*It)) Used.Add(It->GetMachineId());
    for (int32 Sequence = 1; Sequence <= 999; ++Sequence)
    {
        const FName Candidate(*FString::Printf(TEXT("%s-%03d"), MachinePrefix(Type), Sequence));
        if (!Used.Contains(Candidate)) return Candidate;
    }
    return NAME_None;
}

FName ULBFactoryMachineBuilderSubsystem::AllocateECoatLineId() const
{
    TSet<FName> Used;
    if (GetWorld())
        for (TActorIterator<ALBECoatLineActor> It(GetWorld()); It; ++It)
            if (IsValid(*It)) Used.Add(It->GetLineId());
    for (int32 Sequence = 1; Sequence <= 99; ++Sequence)
    {
        const FName Candidate(*FString::Printf(TEXT("ED-LINE-%02d"), Sequence));
        if (!Used.Contains(Candidate)) return Candidate;
    }
    return NAME_None;
}

FName ULBFactoryMachineBuilderSubsystem::AllocateBodyWeldLineId() const
{
    TSet<FName> Used;
    if (GetWorld())
        for (TActorIterator<ALBBodyWeldLineActor> It(GetWorld()); It; ++It)
            if (IsValid(*It)) Used.Add(It->GetLineId());
    for (int32 Sequence = 1; Sequence <= 99; ++Sequence)
    {
        const FName Candidate(*FString::Printf(TEXT("WELD-LINE-%02d"), Sequence));
        if (!Used.Contains(Candidate)) return Candidate;
    }
    return NAME_None;
}

bool ULBFactoryMachineBuilderSubsystem::GetMachinePlacementEnvelope(
    const ELBFactoryBuildMachineType MachineType, FVector& OutHalfExtent,
    FVector& OutRelativeCentre, float& OutRootHeightCm, FString& OutReason) const
{
    OutHalfExtent = FVector::ZeroVector;
    OutRelativeCentre = FVector::ZeroVector;
    OutRootHeightCm = 0.0f;
    OutReason.Reset();

    if (MachineType == ELBFactoryBuildMachineType::BodyWeldLine)
    {
        if (!GetBodyWeldPlacementEnvelope(OutHalfExtent, OutRelativeCentre))
        {
            OutReason = TEXT("BODY WELD LINE PLACEMENT CONTRACT IS OFFLINE");
            return false;
        }
        OutReason = TEXT("60 x 30 m BODY WELD LINE PROTECTED ENVELOPE READY");
        return true;
    }

    if (MachineType == ELBFactoryBuildMachineType::ECoatLine)
    {
        const ALBECoatLineActor* Defaults = GetDefault<ALBECoatLineActor>();
        if (!Defaults)
        {
            OutReason = TEXT("ED LINE PLACEMENT CONTRACT IS OFFLINE");
            return false;
        }
        OutHalfExtent = Defaults->GetProtectedEnvelopeHalfExtentCm();
        OutRelativeCentre = Defaults->GetProtectedEnvelopeRelativeCentreCm();
        // The composite actor origin is the entry-floor datum; all 189 m remain above it.
        OutRootHeightCm = 0.0f;
        OutReason = TEXT("189 m ED LINE PROTECTED ENVELOPE READY");
        return OutHalfExtent.GetMin() > 0.0f;
    }

    UWorld* World = GetWorld();
    ALBFactoryBuildMachine* Defaults = World ? World->SpawnActor<ALBFactoryBuildMachine>() : nullptr;
    if (!Defaults || !Defaults->Configure(TEXT("PLACEMENT-CONTRACT"), MachineType))
    {
        if (Defaults) Defaults->Destroy();
        OutReason = TEXT("MACHINE PLACEMENT CONTRACT COULD NOT BE CREATED");
        return false;
    }
    OutHalfExtent = Defaults->GetProtectedEnvelopeHalfExtent();
    OutRelativeCentre = Defaults->GetProtectedEnvelopeRelativeCentre();
    OutRootHeightCm = Defaults->GetPlacementRootHeightCm();
    Defaults->Destroy();
    OutReason = TEXT("MACHINE PROTECTED ENVELOPE READY");
    return OutHalfExtent.GetMin() > 0.0f;
}

bool ULBFactoryMachineBuilderSubsystem::ValidateMachineTransform(
    const ELBFactoryBuildMachineType MachineType, const FTransform& WorldTransform,
    FString& OutReason) const
{
    UWorld* World = GetWorld();
    if (!World || !WorldTransform.IsValid()
        || !WorldTransform.GetScale3D().Equals(FVector::OneVector, 0.001f))
    {
        OutReason = TEXT("MACHINE PLACEMENT TRANSFORM IS INVALID");
        return false;
    }
    if (!CanPlaceMachine(MachineType, OutReason)) return false;

    FVector HalfExtent;
    FVector RelativeCentre;
    float RootHeightCm = 0.0f;
    if (!GetMachinePlacementEnvelope(MachineType, HalfExtent, RelativeCentre,
        RootHeightCm, OutReason)) return false;

    // Every generic edit now uses its complete protected envelope. The selected actor is
    // null for a new placement, so this path also remains a truthful public preview preflight.
    if (MachineType != ELBFactoryBuildMachineType::ECoatLine
        && MachineType != ELBFactoryBuildMachineType::BodyWeldLine)
    {
        return ValidateGenericMachineEnvelopeAgainstWorld(*World, WorldTransform,
            HalfExtent, RelativeCentre, nullptr, OutReason);
    }

    return MachineType == ELBFactoryBuildMachineType::BodyWeldLine
        ? ValidateBodyWeldEnvelopeAgainstWorld(*World, WorldTransform, nullptr, OutReason)
        : ValidateECoatEnvelopeAgainstWorld(*World, WorldTransform, nullptr, OutReason);
}

bool ULBFactoryMachineBuilderSubsystem::ValidateMachineTransform(
    const ELBFactoryBuildMachineType MachineType, const FTransform& WorldTransform,
    const ALBFactoryBuildMachine* IgnoredMachine, FString& OutReason) const
{
    UWorld* World = GetWorld();
    if (!World || !IsValid(IgnoredMachine) || IgnoredMachine->GetWorld() != World
        || IgnoredMachine->GetMachineType() != MachineType || !WorldTransform.IsValid()
        || !WorldTransform.GetScale3D().Equals(FVector::OneVector, 0.001f))
    {
        OutReason = TEXT("MACHINE EDIT TRANSFORM OR SELECTED MACHINE IS INVALID");
        return false;
    }
    return ValidateGenericMachineEnvelopeAgainstWorld(*World, WorldTransform,
        IgnoredMachine->GetProtectedEnvelopeHalfExtent(),
        IgnoredMachine->GetProtectedEnvelopeRelativeCentre(), IgnoredMachine, OutReason);
}

bool ULBFactoryMachineBuilderSubsystem::ValidateMachineTransformForEdit(
    const FName MachineId, const FTransform& WorldTransform, FString& OutReason) const
{
    ALBFactoryBuildMachine* Machine = FindUniqueGenericMachine(GetWorld(), MachineId, OutReason);
    return Machine && ValidateMachineTransform(Machine->GetMachineType(),
        WorldTransform, Machine, OutReason);
}

bool ULBFactoryMachineBuilderSubsystem::CanEditMachine(
    const FName MachineId, FString& OutReason) const
{
    UWorld* World = GetWorld();
    ALBFactoryBuildMachine* Machine = FindUniqueGenericMachine(World, MachineId, OutReason);
    if (!Machine) return false;
    if (Machine->IsActorBeingDestroyed())
    {
        OutReason = TEXT("MACHINE REMOVAL IS ALREADY IN PROGRESS");
        return false;
    }

    const FLBFactoryBuildMachineSaveState State = Machine->CaptureSaveState();
    if (!State.InputUnitIds.IsEmpty() || !State.OutputUnitIds.IsEmpty()
        || !State.CompletedUnitIds.IsEmpty()
        || State.CompletedAutomaticProcessSteps > 0
        || State.OperatingState == ELBFactoryMachineOperatingState::Processing)
    {
        OutReason = TEXT("MACHINE HAS ACTIVE OR RETAINED WIP AND CANNOT BE EDITED");
        return false;
    }

    for (TActorIterator<ALBPlayerBuiltPressFlowController> It(World); It; ++It)
    {
        if (!IsValid(*It)) continue;
        for (const FLBBodyWeldBaseKitDeliveryRecord& Reservation
            : It->GetPendingBodyWeldBaseKitDeliveries())
        {
            if (!Reservation.bTransferred && Reservation.DeliveryAuthorityId == MachineId)
            {
                OutReason = TEXT("MACHINE OWNS AN ACTIVE LOGISTICS RESERVATION");
                return false;
            }
        }
    }

    if (Machine->GetOwner() || Machine->GetAttachParentActor())
    {
        OutReason = TEXT("MACHINE HAS EXTERNAL OWNER OR ATTACHMENT AUTHORITY");
        return false;
    }
    for (TActorIterator<AActor> It(World); It; ++It)
    {
        AActor* Other = *It;
        if (!IsValid(Other) || Other == Machine || Cast<ALBFactoryTransportLink>(Other)) continue;
        if (Other->GetOwner() == Machine || Other->GetAttachParentActor() == Machine
            || ActorPropertyReferencesMachine(*Other, *Machine))
        {
            OutReason = FString::Printf(TEXT("MACHINE IS OWNED OR REFERENCED BY DEPENDENT ACTOR %s"),
                *Other->GetActorNameOrLabel());
            return false;
        }
    }

    ULBFactoryConnectionSubsystem* Connections =
        World->GetSubsystem<ULBFactoryConnectionSubsystem>();
    TArray<FLBFactoryTransportLinkSaveState> ExactEdges;
    if (!Connections || !Connections->CaptureConnectionsForActor(
        Machine, ExactEdges, OutReason))
    {
        if (!Connections) OutReason = TEXT("FACTORY CONNECTION AUTHORITY IS OFFLINE");
        return false;
    }

    OutReason = FString::Printf(TEXT("MACHINE %s IS IDLE, UNRESERVED AND SAFE TO EDIT"),
        *MachineId.ToString());
    return true;
}

bool ULBFactoryMachineBuilderSubsystem::MoveMachine(const FName MachineId,
    const FTransform& WorldTransform, FString& OutReason)
{
    UWorld* World = GetWorld();
    if (!CanEditMachine(MachineId, OutReason)) return false;
    ALBFactoryBuildMachine* Machine = FindUniqueGenericMachine(World, MachineId, OutReason);
    if (!Machine) return false;
    const FTransform OriginalTransform = Machine->GetActorTransform();
    if (OriginalTransform.Equals(WorldTransform, 0.001f))
    {
        OutReason = TEXT("MACHINE IS ALREADY AT THE REQUESTED TRANSFORM");
        return true;
    }
    if (!ValidateMachineTransform(Machine->GetMachineType(), WorldTransform,
        Machine, OutReason)) return false;

    ULBFactoryConnectionSubsystem* Connections =
        World->GetSubsystem<ULBFactoryConnectionSubsystem>();
    TArray<FLBFactoryTransportLinkSaveState> ExactEdges;
    if (!Connections || !Connections->CaptureConnectionsForActor(
        Machine, ExactEdges, OutReason))
    {
        if (!Connections) OutReason = TEXT("FACTORY CONNECTION AUTHORITY IS OFFLINE");
        return false;
    }
    const FLBFactoryBuildMachineSaveState BeforeState = Machine->CaptureSaveState();

    if (!Machine->SetActorTransform(WorldTransform, false, nullptr,
        ETeleportType::TeleportPhysics))
    {
        Machine->SetActorTransform(OriginalTransform, false, nullptr,
            ETeleportType::TeleportPhysics);
        OutReason = TEXT("MACHINE TRANSFORM COULD NOT BE APPLIED");
        return false;
    }

    FString RebuildReason;
    if (!Connections->RebuildActorConnections(Machine, ExactEdges, RebuildReason))
    {
        Machine->SetActorTransform(OriginalTransform, false, nullptr,
            ETeleportType::TeleportPhysics);
        OutReason = FString::Printf(TEXT("MACHINE MOVE ROLLED BACK: %s"), *RebuildReason);
        return false;
    }

    const FLBFactoryBuildMachineSaveState AfterState = Machine->CaptureSaveState();
    const bool bMachineStatePreserved = AfterState.MachineId == BeforeState.MachineId
        && AfterState.MachineType == BeforeState.MachineType
        && AfterState.InputUnitIds == BeforeState.InputUnitIds
        && AfterState.OutputUnitIds == BeforeState.OutputUnitIds
        && AfterState.CompletedUnitIds == BeforeState.CompletedUnitIds
        && AfterState.NextOutputSerial == BeforeState.NextOutputSerial
        && AfterState.MaximumInputBuffer == BeforeState.MaximumInputBuffer
        && AfterState.MaximumOutputBuffer == BeforeState.MaximumOutputBuffer
        && AfterState.OperatingState == BeforeState.OperatingState
        && AfterState.OperatingReason == BeforeState.OperatingReason
        && AfterState.RequiredAutomaticProcessSteps == BeforeState.RequiredAutomaticProcessSteps
        && AfterState.CompletedAutomaticProcessSteps == BeforeState.CompletedAutomaticProcessSteps;
    TArray<FLBFactoryTransportLinkSaveState> RecapturedEdges;
    FString RecaptureReason;
    bool bLinksPreserved = Connections->CaptureConnectionsForActor(
        Machine, RecapturedEdges, RecaptureReason)
        && RecapturedEdges.Num() == ExactEdges.Num();
    for (int32 Index = 0; bLinksPreserved && Index < ExactEdges.Num(); ++Index)
    {
        bLinksPreserved = RecapturedEdges[Index].Version == ExactEdges[Index].Version
            && RecapturedEdges[Index].SourcePortId == ExactEdges[Index].SourcePortId
            && RecapturedEdges[Index].TargetPortId == ExactEdges[Index].TargetPortId
            && RecapturedEdges[Index].TransferredUnits == ExactEdges[Index].TransferredUnits;
    }
    if (!bMachineStatePreserved || !bLinksPreserved)
    {
        Machine->RestoreSaveState(BeforeState);
        FString RollbackReason;
        Connections->RebuildActorConnections(Machine, ExactEdges, RollbackReason);
        OutReason = TEXT("MACHINE MOVE POSTCONDITION FAILED AND WAS ROLLED BACK");
        return false;
    }

    OutReason = FString::Printf(TEXT("MOVED %s; %d EXACT TRANSPORT LINK(S) REBUILT"),
        *MachineId.ToString(), ExactEdges.Num());
    return true;
}

bool ULBFactoryMachineBuilderSubsystem::RemoveMachine(
    const FName MachineId, FString& OutReason)
{
    UWorld* World = GetWorld();
    ALBFactoryBuildMachine* Machine = FindUniqueGenericMachine(World, MachineId, OutReason);
    if (!Machine)
        return World && !MachineId.IsNone() && OutReason.Contains(TEXT("ALREADY ABSENT"));
    if (!CanEditMachine(MachineId, OutReason)) return false;

    ULBFactoryConnectionSubsystem* Connections =
        World->GetSubsystem<ULBFactoryConnectionSubsystem>();
    if (!Connections)
    {
        OutReason = TEXT("FACTORY CONNECTION AUTHORITY IS OFFLINE");
        return false;
    }
    TArray<FLBFactoryTransportLinkSaveState> CompleteGraphBefore;
    if (!Connections->CaptureConnections(CompleteGraphBefore))
    {
        OutReason = TEXT("FACTORY CONNECTION INVENTORY COULD NOT BE CAPTURED BEFORE REMOVAL");
        return false;
    }
    if (!Connections->DisconnectActor(Machine, OutReason)) return false;
    if (!Machine->Destroy())
    {
        FString RestoreReason;
        Connections->RestoreConnections(CompleteGraphBefore, RestoreReason);
        OutReason = FString::Printf(TEXT("MACHINE REMOVAL FAILED; CONNECTIONS RESTORED: %s"),
            *RestoreReason);
        return false;
    }

    OutReason = FString::Printf(TEXT("REMOVED IDLE MACHINE %s AND ITS TRANSPORT LINKS"),
        *MachineId.ToString());
    return true;
}

bool ULBFactoryMachineBuilderSubsystem::PlaceMachine(const ELBFactoryBuildMachineType MachineType,
    const FTransform& WorldTransform, AActor*& OutMachine, FString& OutReason)
{
    OutMachine = nullptr;
    UWorld* World = GetWorld();
    if (!CanPlaceMachine(MachineType, OutReason) || !World || !WorldTransform.IsValid()
        || !WorldTransform.GetScale3D().Equals(FVector::OneVector, 0.001f)) return false;
    if ((MachineType == ELBFactoryBuildMachineType::ECoatLine
            || MachineType == ELBFactoryBuildMachineType::BodyWeldLine)
        && !ValidateMachineTransform(MachineType, WorldTransform, OutReason)) return false;

    AActor* Candidate = nullptr;
    if (MachineType == ELBFactoryBuildMachineType::PressTrain)
    {
        ULBPressTrainIdentitySubsystem* Trains = World->GetSubsystem<ULBPressTrainIdentitySubsystem>();
        ALBPressTrainAStation* Train = nullptr;
        if (!Trains || !Trains->PlaceTrain(WorldTransform, TEXT("PRESS TRAIN"), TEXT("BODY PANELS"), Train))
        {
            OutReason = TEXT("PRESS TRAIN FAILED ITS EXISTING PLACEMENT OR VISUAL AUTHORITY");
            return false;
        }
        Candidate = Train;
    }
    else if (MachineType == ELBFactoryBuildMachineType::BodyWeldLine)
    {
        const FName LineId = AllocateBodyWeldLineId();
        ALBBodyWeldLineActor* Line = World->SpawnActor<ALBBodyWeldLineActor>(
            ALBBodyWeldLineActor::StaticClass(), WorldTransform);
        if (!Line || LineId.IsNone() || !Line->Configure(LineId))
        {
            if (Line) Line->Destroy();
            OutReason = TEXT("BODY WELD LINE PACKAGE COULD NOT BE CREATED");
            return false;
        }
        Line->Tags.AddUnique(TEXT("LB.FactoryBuilder.Machine"));
        Candidate = Line;
    }
    else if (MachineType == ELBFactoryBuildMachineType::ECoatLine)
    {
        const FName LineId = AllocateECoatLineId();
        ALBECoatLineActor* Line = World->SpawnActor<ALBECoatLineActor>(
            ALBECoatLineActor::StaticClass(), WorldTransform);
        if (!Line || LineId.IsNone() || !Line->Configure(LineId))
        {
            if (Line) Line->Destroy();
            OutReason = TEXT("ED / E-COAT LINE PACKAGE COULD NOT BE CREATED");
            return false;
        }
        Line->Tags.AddUnique(TEXT("LB.FactoryBuilder.Machine"));
        Candidate = Line;
    }
    else
    {
        const FName MachineId = AllocateMachineId(MachineType);
        ALBFactoryBuildMachine* Machine = World->SpawnActor<ALBFactoryBuildMachine>(
            ALBFactoryBuildMachine::StaticClass(), WorldTransform);
        if (!Machine || !Machine->Configure(MachineId, MachineType))
        {
            if (Machine) Machine->Destroy();
            OutReason = TEXT("MACHINE PACKAGE COULD NOT BE CREATED");
            return false;
        }
        Candidate = Machine;
    }

    TArray<ALBFactoryTransportLink*> Links;
    ULBFactoryConnectionSubsystem* Connections = World->GetSubsystem<ULBFactoryConnectionSubsystem>();
    auto FailPlacement = [&]()
    {
        for (ALBFactoryTransportLink* Link : Links)
        {
            if (!Link) continue;
            for (TActorIterator<AActor> ActorIt(World); ActorIt; ++ActorIt)
            {
                TArray<ULBFactoryProcessPortComponent*> Ports;
                ActorIt->GetComponents(Ports);
                for (ULBFactoryProcessPortComponent* Port : Ports)
                    if (Port) Port->RemoveConnection(Link);
            }
            Link->Destroy();
        }
        if (ALBPressTrainAStation* Train = Cast<ALBPressTrainAStation>(Candidate))
            World->GetSubsystem<ULBPressTrainIdentitySubsystem>()->RemoveTrain(Train);
        else Candidate->Destroy();
    };
    if (!Connections)
    {
        OutReason = TEXT("FACTORY CONNECTION AUTHORITY IS OFFLINE");
        FailPlacement();
        return false;
    }
    if (MachineType == ELBFactoryBuildMachineType::BodyWeldLine)
    {
        ALBBodyWeldLineActor* WeldLine = CastChecked<ALBBodyWeldLineActor>(Candidate);
        struct FPredecessor
        {
            ULBFactoryProcessPortComponent* Port = nullptr;
            double DistanceSquared = 0.0;
        };
        TArray<FPredecessor> Predecessors;
        for (TActorIterator<ALBFactoryBuildMachine> It(World); It; ++It)
        {
            if (!IsValid(*It)
                || It->GetMachineType() != ELBFactoryBuildMachineType::OutboundPanelDock) continue;
            FString CandidateReason;
            if (Connections->CanConnect(It->OutputPort,
                WeldLine->GetStillageInputPort(), CandidateReason))
            {
                Predecessors.Add({It->OutputPort, FVector::DistSquared(
                    It->OutputPort->GetComponentLocation(),
                    WeldLine->GetStillageInputPort()->GetComponentLocation())});
            }
        }
        Predecessors.Sort([](const FPredecessor& A, const FPredecessor& B)
        {
            if (!FMath::IsNearlyEqual(A.DistanceSquared, B.DistanceSquared))
                return A.DistanceSquared < B.DistanceSquared;
            return A.Port->PortId.ToString() < B.Port->PortId.ToString();
        });
        ALBFactoryTransportLink* Link = nullptr;
        if (Predecessors.IsEmpty() || !Connections->Connect(Predecessors[0].Port,
            WeldLine->GetStillageInputPort(), Link, OutReason))
        {
            if (Predecessors.IsEmpty())
                OutReason = TEXT("NO IN-RANGE OUTBOUND STILLAGE HANDOFF FOR THE BODY WELD LINE");
            FailPlacement();
            return false;
        }
        Links.Add(Link);
        // BaseKitInputPort is deliberately optional. Its later logistics authority may
        // connect it, but catalogue placement must never invent or require a supplier.
    }
    else if (MachineType == ELBFactoryBuildMachineType::ECoatLine)
    {
        ALBECoatLineActor* ECoatLine = CastChecked<ALBECoatLineActor>(Candidate);
        struct FPredecessor
        {
            ULBFactoryProcessPortComponent* Port = nullptr;
            double DistanceSquared = 0.0;
        };
        TArray<FPredecessor> Predecessors;
        for (TActorIterator<ALBBodyWeldLineActor> It(World); It; ++It)
        {
            if (!IsValid(*It)) continue;
            FString CandidateReason;
            if (Connections->CanConnect(It->GetBIWOutputPort(),
                ECoatLine->GetInputPort(), CandidateReason))
            {
                Predecessors.Add({It->GetBIWOutputPort(), FVector::DistSquared(
                    It->GetBIWOutputPort()->GetComponentLocation(),
                    ECoatLine->GetInputPort()->GetComponentLocation())});
            }
        }
        Predecessors.Sort([](const FPredecessor& A, const FPredecessor& B)
        {
            if (!FMath::IsNearlyEqual(A.DistanceSquared, B.DistanceSquared))
                return A.DistanceSquared < B.DistanceSquared;
            return A.Port->PortId.ToString() < B.Port->PortId.ToString();
        });
        ALBFactoryTransportLink* Link = nullptr;
        if (Predecessors.IsEmpty() || !Connections->Connect(Predecessors[0].Port,
            ECoatLine->GetInputPort(), Link, OutReason))
        {
            if (Predecessors.IsEmpty())
                OutReason = TEXT("NO IN-RANGE BODY-IN-WHITE HANDOFF FOR THE ED LINE");
            FailPlacement();
            return false;
        }
        Links.Add(Link);
    }
    else if (!Connections->AutoConnectNewMachine(Candidate, Links, OutReason))
    {
        FailPlacement();
        return false;
    }
    FString AutomaticRouteResult;
    if (MachineType == ELBFactoryBuildMachineType::CoilWeighInspectionCell)
    {
        ALBFactoryBuildMachine* InboundDock = nullptr;
        for (TActorIterator<ALBFactoryBuildMachine> It(World); It; ++It)
            if (IsValid(*It) && It->GetMachineType() == ELBFactoryBuildMachineType::InboundDeliveryDock)
            {
                InboundDock = *It;
                break;
            }
        if (!CreateAutomaticInboundAGVRoute(InboundDock,
            Cast<ALBFactoryBuildMachine>(Candidate), AutomaticRouteResult))
        {
            FailPlacement();
            OutReason = AutomaticRouteResult;
            return false;
        }
    }
    const int32 WalkwayTiles = CreateAutomaticServiceWalkways(Links);
    OutMachine = Candidate;
    if (MachineType == ELBFactoryBuildMachineType::BodyWeldLine)
    {
        OutReason = TEXT("PLACED COMPLETE BODY WELD LINE; OUTBOUND STILLAGE HANDOFF CONNECTED; OPTIONAL BASE-KIT INPUT RESERVED; BODY-IN-WHITE OUTPUT READY");
    }
    else if (MachineType == ELBFactoryBuildMachineType::ECoatLine)
    {
        OutReason = TEXT("PLACED COMPLETE 189 m ED / E-COAT LINE; SIX 18 m TANKS, 9 m DRAIN AND 72 m OVEN; BODY-WELD INPUT CONNECTED; PAINT OUTPUT PORT RESERVED");
    }
    else OutReason = AutomaticRouteResult.IsEmpty()
        ? FString::Printf(TEXT("PLACED %s WITH %d AUTOMATIC LINK(S)"), *Candidate->GetName(), Links.Num())
        : FString::Printf(TEXT("PLACED %s WITH %d AUTOMATIC LINK(S); %s; %d SERVICE WALKWAY TILES"),
            *Candidate->GetName(), Links.Num(), *AutomaticRouteResult, WalkwayTiles);
    return true;
}

#if !UE_BUILD_SHIPPING
AActor* ULBFactoryMachineBuilderSubsystem::PlaceMachineForVisualQA(
    const ELBFactoryBuildMachineType MachineType, const FTransform& WorldTransform,
    FString& OutReason)
{
    if (MachineType != ELBFactoryBuildMachineType::BodyWeldLine
        && MachineType != ELBFactoryBuildMachineType::ECoatLine)
    {
        OutReason = TEXT("VISUAL-QA COMPOSITE SPAWN SUPPORTS BODY WELD OR ED ONLY");
        return nullptr;
    }
    UWorld* World = GetWorld();
    if (!World || !WorldTransform.IsValid()
        || !WorldTransform.GetScale3D().Equals(FVector::OneVector, 0.001f))
    {
        OutReason = TEXT("VISUAL-QA COMPOSITE SPAWN RECEIVED AN INVALID WORLD TRANSFORM");
        return nullptr;
    }

    if (MachineType == ELBFactoryBuildMachineType::BodyWeldLine)
    {
        if (HasBodyWeldLine())
        {
            OutReason = TEXT("VISUAL-QA WORLD ALREADY CONTAINS A BODY WELD LINE");
            return nullptr;
        }
        ALBBodyWeldLineActor* Line = World->SpawnActor<ALBBodyWeldLineActor>(
            ALBBodyWeldLineActor::StaticClass(), WorldTransform);
        const FName LineId = AllocateBodyWeldLineId();
        if (!Line || LineId.IsNone() || !Line->Configure(LineId))
        {
            if (Line) Line->Destroy();
            OutReason = TEXT("VISUAL-QA BODY WELD LINE COULD NOT BE CREATED");
            return nullptr;
        }
        Line->Tags.AddUnique(TEXT("LB.FactoryBuilder.Machine"));
        Line->Tags.AddUnique(TEXT("LB.Development.VisualQA.Composite"));
        OutReason = TEXT("VISUAL-QA BODY WELD COMPOSITE SPAWNED WITHOUT PLAYER PLACEMENT CLAIM");
        return Line;
    }

    if (HasECoatLine())
    {
        OutReason = TEXT("VISUAL-QA WORLD ALREADY CONTAINS AN ED LINE");
        return nullptr;
    }
    ALBECoatLineActor* Line = World->SpawnActor<ALBECoatLineActor>(
        ALBECoatLineActor::StaticClass(), WorldTransform);
    const FName LineId = AllocateECoatLineId();
    if (!Line || LineId.IsNone() || !Line->Configure(LineId))
    {
        if (Line) Line->Destroy();
        OutReason = TEXT("VISUAL-QA ED LINE COULD NOT BE CREATED");
        return nullptr;
    }
    Line->Tags.AddUnique(TEXT("LB.FactoryBuilder.Machine"));
    Line->Tags.AddUnique(TEXT("LB.Development.VisualQA.Composite"));
    OutReason = TEXT("VISUAL-QA ED COMPOSITE SPAWNED WITHOUT PLAYER PLACEMENT CLAIM");
    return Line;
}
#endif

int32 ULBFactoryMachineBuilderSubsystem::CreateAutomaticServiceWalkways(
    const TArray<ALBFactoryTransportLink*>& Links)
{
    int32 CreatedCount = 0;
    auto PlaceLeg = [&](const FVector& RawA, const FVector& RawB)
    {
        FVector A(RawA.X, RawA.Y, 0.0f);
        FVector B(RawB.X, RawB.Y, 0.0f);
        const FVector Direction = (B - A).GetSafeNormal2D();
        const float Length = FVector::Dist2D(A, B);
        if (Length < 1.0f || Direction.IsNearlyZero()) return;
        // Keep the pedestrian strip outside the 230 cm AGV lane / 180 cm conveyor.
        const FVector Offset(-Direction.Y * 300.0f, Direction.X * 300.0f, 0.0f);
        A += Offset;
        B += Offset;
        const int32 TileCount = FMath::Max(1, FMath::CeilToInt(Length / 500.0f));
        const float Yaw = Direction.Rotation().Yaw;
        for (int32 TileIndex = 0; TileIndex < TileCount; ++TileIndex)
        {
            ALBFactoryAGVInfrastructure* Walkway = nullptr;
            FString Reason;
            const float Alpha = (static_cast<float>(TileIndex) + 0.5f)
                / static_cast<float>(TileCount);
            if (PlaceAGVInfrastructure(ELBFactoryAGVInfrastructureType::PedestrianWalkway,
                INDEX_NONE, FTransform(FRotator(0.0f, Yaw, 0.0f), FMath::Lerp(A, B, Alpha)),
                Walkway, Reason) && Walkway)
            {
                Walkway->Tags.AddUnique(TEXT("LB.FactoryBuilder.AutomaticServiceWalkway"));
                Walkway->MarkAutomaticallyGenerated();
                ++CreatedCount;
            }
        }
    };
    for (ALBFactoryTransportLink* Link : Links)
    {
        if (!Link || !Link->GetSourcePort() || !Link->GetTargetPort()) continue;
        const FVector Start = Link->GetSourcePort()->GetComponentLocation();
        const FVector End = Link->GetTargetPort()->GetComponentLocation();
        const FVector Turn(End.X, Start.Y, 0.0f);
        PlaceLeg(Start, Turn);
        PlaceLeg(Turn, End);
    }
    return CreatedCount;
}

bool ULBFactoryMachineBuilderSubsystem::CreateAutomaticInboundAGVRoute(
    ALBFactoryBuildMachine* InboundDock, ALBFactoryBuildMachine* PR002Cell, FString& OutReason)
{
    UWorld* World = GetWorld();
    if (!World || !InboundDock || !PR002Cell || !InboundDock->OutputPort || !PR002Cell->InputPort)
    {
        OutReason = TEXT("AUTOMATIC INBOUND AGV ROUTE HAS NO VALID ENDPOINTS");
        return false;
    }

    const FVector Start(InboundDock->OutputPort->GetComponentLocation().X,
        InboundDock->OutputPort->GetComponentLocation().Y, 0.0f);
    const FVector Dock(PR002Cell->InputPort->GetComponentLocation().X,
        PR002Cell->InputPort->GetComponentLocation().Y, 0.0f);
    // A deterministic Manhattan route is easy for a new player to read and edit. Keep the
    // first leg aligned with the lorry, then turn once toward PR002. When both ports are
    // already collinear, the Manhattan corner is the dock itself. The AGV deliberately
    // rejects that zero-length second leg, so split the straight route at its midpoint
    // instead of silently leaving the live vehicle on an old map-authored route.
    constexpr float MinimumControllerLegLengthCm = 25.0f;
    if (FVector::Dist2D(Start, Dock) < MinimumControllerLegLengthCm * 2.0f)
    {
        OutReason = TEXT("AUTOMATIC INBOUND AGV ROUTE ENDPOINTS ARE TOO CLOSE");
        return false;
    }
    FVector Turn(Dock.X, Start.Y, 0.0f);
    if (FVector::Dist2D(Start, Turn) < MinimumControllerLegLengthCm
        || FVector::Dist2D(Turn, Dock) < MinimumControllerLegLengthCm)
    {
        Turn = FMath::Lerp(Start, Dock, 0.5f);
    }
    TArray<ALBFactoryAGVInfrastructure*> Created;
    auto PlaceAutomatic = [&](const ELBFactoryAGVInfrastructureType Type,
        const FVector& Location, const float Yaw) -> bool
    {
        ALBFactoryAGVInfrastructure* Item = nullptr;
        FString Reason;
        if (!PlaceAGVInfrastructureAllowingConnectedMachines(Type, INDEX_NONE,
            FTransform(FRotator(0.0f, Yaw, 0.0f), Location), InboundDock, PR002Cell,
            Item, Reason) || !Item)
        {
            OutReason = Reason.IsEmpty() ? TEXT("AUTOMATIC AGV ROUTE TILE COULD NOT BE CREATED") : Reason;
            return false;
        }
        Item->Tags.AddUnique(TEXT("LB.FactoryBuilder.AutomaticAGVRoute"));
        Item->MarkAutomaticallyGenerated();
        Created.Add(Item);
        return true;
    };
    auto PlaceLeg = [&](const FVector& A, const FVector& B) -> bool
    {
        const float Length = FVector::Dist2D(A, B);
        if (Length < 1.0f) return true;
        const int32 TileCount = FMath::Max(1, FMath::CeilToInt(Length / 500.0f));
        const float Yaw = (B - A).Rotation().Yaw;
        for (int32 TileIndex = 0; TileIndex < TileCount; ++TileIndex)
        {
            const float Alpha = (static_cast<float>(TileIndex) + 0.5f)
                / static_cast<float>(TileCount);
            if (!PlaceAutomatic(ELBFactoryAGVInfrastructureType::AGVRouteSegment,
                FMath::Lerp(A, B, Alpha), Yaw)) return false;
        }
        return true;
    };

    if (!PlaceAutomatic(ELBFactoryAGVInfrastructureType::WaitPoint, Start, 0.0f)
        || !PlaceAutomatic(ELBFactoryAGVInfrastructureType::RouteWaypoint, Turn, 0.0f)
        || !PlaceLeg(Start, Turn) || !PlaceLeg(Turn, Dock))
    {
        for (ALBFactoryAGVInfrastructure* Item : Created) if (Item) Item->Destroy();
        return false;
    }

    TArray<ALBCoilAGVController*> LiveAGVs;
    TArray<ALBCoilAGVController*> InboundRouteOwners;
    TArray<ALBCoilAGVController*> UnassignedControllers;
    for (TActorIterator<ALBCoilAGVController> It(World); It; ++It)
    {
        if (!IsValid(*It)) continue;
        LiveAGVs.Add(*It);
        if (It->GetRouteProfile() == ELBCoilAGVRouteProfile::InboundPR002)
            InboundRouteOwners.Add(*It);
        else if (It->GetRouteProfile() == ELBCoilAGVRouteProfile::ManualOrUnassigned)
            UnassignedControllers.Add(*It);
    }

    TArray<ALBCoilAGVController*> TargetAGVs = InboundRouteOwners;
    // The first player-built inbound route may claim the sole controller in an otherwise
    // empty shop. Once a fleet exists, ManualOrUnassigned is ambiguous and is never stolen
    // from a hand-authored route or reassigned over a train-owned controller.
    if (TargetAGVs.IsEmpty() && LiveAGVs.Num() == 1 && UnassignedControllers.Num() == 1)
        TargetAGVs.Add(UnassignedControllers[0]);

    int32 ConfiguredAGVs = 0;
    for (ALBCoilAGVController* AGV : TargetAGVs)
    {
        if (AGV->ConfigureInboundRouteFromPlayerBuiltInfrastructure(InboundDock, PR002Cell))
            ++ConfiguredAGVs;
    }
    if (ConfiguredAGVs != TargetAGVs.Num())
    {
        for (ALBFactoryAGVInfrastructure* Item : Created) if (Item) Item->Destroy();
        OutReason = TEXT("AUTOMATIC INBOUND AGV ROUTE COULD NOT CONFIGURE ITS ASSIGNED COIL AGV");
        return false;
    }
    OutReason = FString::Printf(TEXT("AUTOMATIC AGV ROUTE CREATED (%d TILES, %d ACTIVE AGV%s)"),
        Created.Num(), ConfiguredAGVs, ConfiguredAGVs == 1 ? TEXT("") : TEXT("S"));
    return true;
}

TArray<ELBFactoryBuildMachineType> ULBFactoryMachineBuilderSubsystem::GetAvailableMachineTypes() const
{
    TArray<ELBFactoryBuildMachineType> Result;
    const ELBFactoryBuildMachineType OrderedTypes[] = {
        // Whole-factory milestones remain first and preserve process order.
        ELBFactoryBuildMachineType::BodyWeldLine,
        ELBFactoryBuildMachineType::ECoatLine,
        ELBFactoryBuildMachineType::InboundDeliveryDock,
        ELBFactoryBuildMachineType::CoilWeighInspectionCell,
        ELBFactoryBuildMachineType::DepackagingRobot,
        ELBFactoryBuildMachineType::DecoilerFeeder,
        ELBFactoryBuildMachineType::PressTrain,
        ELBFactoryBuildMachineType::InspectionCell,
        ELBFactoryBuildMachineType::OutboundPanelDock
    };
    for (const ELBFactoryBuildMachineType Type : OrderedTypes)
    {
        FString Reason;
        if (CanPlaceMachine(Type, Reason)) Result.Add(Type);
    }
    return Result;
}

bool ULBFactoryMachineBuilderSubsystem::CaptureMachines(
    TArray<FLBFactoryBuildMachineSaveState>& OutStates) const
{
    OutStates.Reset();
    if (!GetWorld()) return false;
    TSet<FName> Ids;
    for (TActorIterator<ALBFactoryBuildMachine> It(GetWorld()); It; ++It)
    {
        if (!IsValid(*It) || It->GetMachineId().IsNone() || Ids.Contains(It->GetMachineId())) return false;
        Ids.Add(It->GetMachineId());
        OutStates.Add(It->CaptureSaveState());
    }
    OutStates.Sort([](const FLBFactoryBuildMachineSaveState& A, const FLBFactoryBuildMachineSaveState& B)
        { return A.MachineId.LexicalLess(B.MachineId); });
    return true;
}

bool ULBFactoryMachineBuilderSubsystem::ValidateMachineSaveSet(
    const TArray<FLBFactoryBuildMachineSaveState>& States, FString& OutReason) const
{
    TSet<FName> Ids;
    for (const FLBFactoryBuildMachineSaveState& State : States)
    {
        const uint8 TypeValue = static_cast<uint8>(State.MachineType);
        if ((State.Version != 1 && State.Version != 2) || State.MachineId.IsNone()
            || Ids.Contains(State.MachineId)
            || TypeValue > static_cast<uint8>(ELBFactoryBuildMachineType::BodyWeldLine)
            || State.MachineType == ELBFactoryBuildMachineType::PressTrain
            || State.MachineType == ELBFactoryBuildMachineType::ECoatLine
            || State.MachineType == ELBFactoryBuildMachineType::BodyWeldLine
            || !State.WorldTransform.IsValid()
            || !State.WorldTransform.GetScale3D().Equals(FVector::OneVector, 0.001f))
        {
            OutReason = TEXT("SAVED MACHINE SET IS INVALID");
            return false;
        }
        Ids.Add(State.MachineId);
    }
    OutReason = TEXT("SAVED MACHINE SET IS VALID");
    return true;
}

bool ULBFactoryMachineBuilderSubsystem::RestoreMachines(
    const TArray<FLBFactoryBuildMachineSaveState>& States, FString& OutReason)
{
    UWorld* World = GetWorld();
    if (!World) return false;
    if (!ValidateMachineSaveSet(States, OutReason)) return false;

    TArray<ALBFactoryBuildMachine*> Existing;
    for (TActorIterator<ALBFactoryBuildMachine> It(World); It; ++It)
        if (IsValid(*It)) Existing.Add(*It);
    Existing.Sort([](const ALBFactoryBuildMachine& A, const ALBFactoryBuildMachine& B)
        { return A.GetMachineId().LexicalLess(B.GetMachineId()); });
    TArray<FLBFactoryBuildMachineSaveState> PreviousStates;
    PreviousStates.Reserve(Existing.Num());
    for (const ALBFactoryBuildMachine* Machine : Existing)
        PreviousStates.Add(Machine->CaptureSaveState());
    TArray<ALBFactoryBuildMachine*> Spawned;
    for (int32 Index = 0; Index < States.Num(); ++Index)
    {
        const bool bSpawnedForRestore = !Existing.IsValidIndex(Index);
        ALBFactoryBuildMachine* Machine = bSpawnedForRestore ? World->SpawnActor<ALBFactoryBuildMachine>()
            : Existing[Index];
        if (bSpawnedForRestore && Machine) Spawned.Add(Machine);
        if (!Machine || !Machine->RestoreSaveState(States[Index]))
        {
            for (ALBFactoryBuildMachine* Created : Spawned)
                if (IsValid(Created)) Created->Destroy();
            const int32 RestoreCount = FMath::Min(Index + 1, Existing.Num());
            for (int32 RestoreIndex = 0; RestoreIndex < RestoreCount; ++RestoreIndex)
                if (IsValid(Existing[RestoreIndex]))
                    Existing[RestoreIndex]->RestoreSaveState(PreviousStates[RestoreIndex]);
            OutReason = TEXT("SAVED MACHINE PACKAGE COULD NOT BE RESTORED");
            return false;
        }
    }
    for (int32 Index = States.Num(); Index < Existing.Num(); ++Index)
        if (Existing[Index]) Existing[Index]->Destroy();
    OutReason = FString::Printf(TEXT("RESTORED %d PLAYER-BUILT MACHINE(S)"), States.Num());
    return true;
}

bool ULBFactoryMachineBuilderSubsystem::CaptureBodyWeldLines(
    TArray<FLBBodyWeldLineSaveState>& OutStates) const
{
    OutStates.Reset();
    if (!GetWorld()) return false;
    TSet<FName> Ids;
    for (TActorIterator<ALBBodyWeldLineActor> It(GetWorld()); It; ++It)
    {
        if (!IsValid(*It) || It->GetLineId().IsNone() || Ids.Contains(It->GetLineId())) return false;
        Ids.Add(It->GetLineId());
        OutStates.Add(It->CaptureSaveState());
    }
    OutStates.Sort([](const FLBBodyWeldLineSaveState& A, const FLBBodyWeldLineSaveState& B)
        { return A.LineId.LexicalLess(B.LineId); });
    return OutStates.Num() <= 1;
}

bool ULBFactoryMachineBuilderSubsystem::ValidateBodyWeldLineSaveSet(
    const TArray<FLBBodyWeldLineSaveState>& States, FString& OutReason) const
{
    UWorld* World = GetWorld();
    if (!World)
    {
        OutReason = TEXT("BODY WELD SAVE PREFLIGHT WORLD IS OFFLINE");
        return false;
    }
    if (States.Num() > 1)
    {
        OutReason = TEXT("SAVED FACTORY HAS MORE THAN ONE COMPLETE BODY WELD LINE");
        return false;
    }
    FVector HalfExtent;
    FVector RelativeCentre;
    if (!GetBodyWeldPlacementEnvelope(HalfExtent, RelativeCentre))
    {
        OutReason = TEXT("BODY WELD SAVE CONTRACT IS OFFLINE");
        return false;
    }
    TSet<FName> Ids;
    const FBox LocalEnvelope(RelativeCentre - HalfExtent, RelativeCentre + HalfExtent);
    for (const FLBBodyWeldLineSaveState& State : States)
    {
        if (!ALBBodyWeldLineActor::IsSaveStateContractValid(State)
            || Ids.Contains(State.LineId)
            || !IsOnSingleFactoryFloorDatum(*World,
                LocalEnvelope.TransformBy(State.WorldTransform), State.WorldTransform.GetLocation()))
        {
            OutReason = TEXT("SAVED BODY WELD LINE SET IS INVALID OR OFF THE AUTHORISED FACTORY FLOOR");
            return false;
        }
        Ids.Add(State.LineId);
    }
    OutReason = TEXT("SAVED BODY WELD LINE CONTRACT IS VALID");
    return true;
}

bool ULBFactoryMachineBuilderSubsystem::RestoreBodyWeldLines(
    const TArray<FLBBodyWeldLineSaveState>& States, FString& OutReason)
{
    UWorld* World = GetWorld();
    if (!World) return false;
    if (!ValidateBodyWeldLineSaveSet(States, OutReason)) return false;

    TArray<ALBBodyWeldLineActor*> Existing;
    for (TActorIterator<ALBBodyWeldLineActor> It(World); It; ++It)
        if (IsValid(*It)) Existing.Add(*It);
    Existing.Sort([](const ALBBodyWeldLineActor& A, const ALBBodyWeldLineActor& B)
        { return A.GetLineId().LexicalLess(B.GetLineId()); });
    for (int32 Index = 0; Index < States.Num(); ++Index)
    {
        const bool bSpawnedForRestore = !Existing.IsValidIndex(Index);
        ALBBodyWeldLineActor* Line = bSpawnedForRestore
            ? World->SpawnActor<ALBBodyWeldLineActor>() : Existing[Index];
        const FLBBodyWeldLineSaveState PreviousState = !bSpawnedForRestore && Line
            ? Line->CaptureSaveState() : FLBBodyWeldLineSaveState();
        FString PlacementReason;
        if (!Line || !ValidateBodyWeldEnvelopeAgainstWorld(*World, States[Index].WorldTransform,
                Line, PlacementReason)
            || !Line->RestoreSaveState(States[Index]))
        {
            if (Line)
            {
                if (bSpawnedForRestore) Line->Destroy();
                else Line->RestoreSaveState(PreviousState);
            }
            OutReason = FString::Printf(TEXT("SAVED BODY WELD LINE COULD NOT BE RESTORED: %s"),
                *PlacementReason);
            return false;
        }
        Line->Tags.AddUnique(TEXT("LB.FactoryBuilder.Machine"));
    }
    for (int32 Index = States.Num(); Index < Existing.Num(); ++Index)
        if (Existing[Index]) Existing[Index]->Destroy();
    OutReason = FString::Printf(TEXT("RESTORED %d BODY WELD LINE(S)"), States.Num());
    return true;
}

bool ULBFactoryMachineBuilderSubsystem::CaptureECoatLines(
    TArray<FLBECoatLineSaveState>& OutStates) const
{
    OutStates.Reset();
    if (!GetWorld()) return false;
    TSet<FName> Ids;
    for (TActorIterator<ALBECoatLineActor> It(GetWorld()); It; ++It)
    {
        if (!IsValid(*It) || It->GetLineId().IsNone() || Ids.Contains(It->GetLineId())) return false;
        Ids.Add(It->GetLineId());
        OutStates.Add(It->CaptureSaveState());
    }
    OutStates.Sort([](const FLBECoatLineSaveState& A, const FLBECoatLineSaveState& B)
        { return A.LineId.LexicalLess(B.LineId); });
    return OutStates.Num() <= 1;
}

bool ULBFactoryMachineBuilderSubsystem::ValidateECoatLineSaveSet(
    const TArray<FLBECoatLineSaveState>& States, FString& OutReason) const
{
    UWorld* World = GetWorld();
    if (!World)
    {
        OutReason = TEXT("ED / E-COAT SAVE PREFLIGHT WORLD IS OFFLINE");
        return false;
    }
    if (States.Num() > 1)
    {
        OutReason = TEXT("SAVED FACTORY HAS MORE THAN ONE COMPLETE ED / E-COAT LINE");
        return false;
    }
    TSet<FName> Ids;
    const ALBECoatLineActor* Defaults = GetDefault<ALBECoatLineActor>();
    if (!Defaults)
    {
        OutReason = TEXT("ED / E-COAT SAVE CONTRACT IS OFFLINE");
        return false;
    }
    const FBox LocalEnvelope(Defaults->GetProtectedEnvelopeRelativeCentreCm()
            - Defaults->GetProtectedEnvelopeHalfExtentCm(),
        Defaults->GetProtectedEnvelopeRelativeCentreCm() + Defaults->GetProtectedEnvelopeHalfExtentCm());
    for (const FLBECoatLineSaveState& State : States)
    {
        const FBox Candidate = LocalEnvelope.TransformBy(State.WorldTransform);
        if (!ALBECoatLineActor::IsSaveStateContractValid(State)
            || Ids.Contains(State.LineId)
            || !IsOnSingleFactoryFloorDatum(*World, Candidate, State.WorldTransform.GetLocation()))
        {
            OutReason = TEXT("SAVED ED / E-COAT LINE SET IS INVALID OR OFF THE AUTHORISED FACTORY FLOOR");
            return false;
        }
        Ids.Add(State.LineId);
    }
    OutReason = TEXT("SAVED ED / E-COAT LINE CONTRACT IS VALID");
    return true;
}

bool ULBFactoryMachineBuilderSubsystem::RestoreECoatLines(
    const TArray<FLBECoatLineSaveState>& States, FString& OutReason)
{
    UWorld* World = GetWorld();
    if (!World) return false;
    if (!ValidateECoatLineSaveSet(States, OutReason)) return false;

    TArray<ALBECoatLineActor*> Existing;
    for (TActorIterator<ALBECoatLineActor> It(World); It; ++It)
        if (IsValid(*It)) Existing.Add(*It);
    for (int32 Index = 0; Index < States.Num(); ++Index)
    {
        const bool bSpawnedForRestore = !Existing.IsValidIndex(Index);
        ALBECoatLineActor* Line = bSpawnedForRestore
            ? World->SpawnActor<ALBECoatLineActor>() : Existing[Index];
        const FLBECoatLineSaveState PreviousState = !bSpawnedForRestore && Line
            ? Line->CaptureSaveState() : FLBECoatLineSaveState();
        FString PlacementReason;
        if (!Line || !ValidateECoatEnvelopeAgainstWorld(*World, States[Index].WorldTransform,
                Line, PlacementReason)
            || !Line->RestoreSaveState(States[Index]))
        {
            if (Line)
            {
                if (bSpawnedForRestore) Line->Destroy();
                else Line->RestoreSaveState(PreviousState);
            }
            OutReason = FString::Printf(TEXT("SAVED ED / E-COAT LINE COULD NOT BE RESTORED: %s"),
                *PlacementReason);
            return false;
        }
    }
    for (int32 Index = States.Num(); Index < Existing.Num(); ++Index)
        if (Existing[Index]) Existing[Index]->Destroy();
    OutReason = FString::Printf(TEXT("RESTORED %d ED / E-COAT LINE(S)"), States.Num());
    return true;
}
