#include "LBBridgeCraneController.h"

#include "EngineUtils.h"
#include "LBPR004Station.h"

namespace
{
    const FName BridgeMotionTag(TEXT("LB.Motion.CraneBridge"));
    const FName TrolleyMotionTag(TEXT("LB.Motion.CraneTrolley"));
    const FName HoistMotionTag(TEXT("LB.Motion.Hoist"));
    const FName HookMotionTag(TEXT("LB.Motion.CHook"));
    const FName ReevingTag(TEXT("LB.Module.HoistReeving"));
}

ALBBridgeCraneController::ALBBridgeCraneController()
{
    PrimaryActorTick.bCanEverTick = true;
}

void ALBBridgeCraneController::BeginPlay()
{
    Super::BeginPlay();
    DiscoverAndBind();
}

bool ALBBridgeCraneController::DiscoverAndBind()
{
    BridgeActors.Reset();
    TrolleyActors.Reset();
    HoistActors.Reset();
    HookActors.Reset();
    SourceAttachmentActors.Reset();
    PR004Station = nullptr;
    SourceCoilActor = nullptr;

    UWorld* World = GetWorld();
    if (!World)
    {
        return false;
    }

    for (TActorIterator<AActor> It(World); It; ++It)
    {
        AActor* Actor = *It;
        if (!Actor || Actor == this)
        {
            continue;
        }
        if (!PR004Station)
        {
            PR004Station = Cast<ALBPR004Station>(Actor);
        }
        if (Actor->ActorHasTag(SourceCoilTag))
        {
            SourceCoilActor = Actor;
        }
        if (Actor->ActorHasTag(SourceAttachmentTag))
        {
            BindActor(Actor, SourceAttachmentActors);
        }
        if (!Actor->ActorHasTag(CraneTag))
        {
            continue;
        }
        if (Actor->ActorHasTag(BridgeMotionTag))
        {
            BindActor(Actor, BridgeActors);
        }
        if (Actor->ActorHasTag(TrolleyMotionTag))
        {
            BindActor(Actor, TrolleyActors);
        }
        if (Actor->ActorHasTag(HoistMotionTag))
        {
            BindActor(Actor, HoistActors, Actor->ActorHasTag(ReevingTag));
        }
        if (Actor->ActorHasTag(HookMotionTag))
        {
            BindActor(Actor, HookActors);
        }
    }

    bBound = PR004Station && SourceCoilActor && !BridgeActors.IsEmpty()
        && !TrolleyActors.IsEmpty() && !HoistActors.IsEmpty() && !HookActors.IsEmpty();
    if (!bBound)
    {
        LatchFault(ELBBridgeCraneFault::BindingIncomplete);
        return false;
    }

    // The logical bridge axis is the trolley/hoist centreline. A double-girder
    // crane's first girder is deliberately offset from that datum.
    InitialBridgeX = TrolleyActors[0].InitialLocation.X;
    InitialTrolleyY = TrolleyActors[0].InitialLocation.Y;
    InitialHookZ = HookActors[0].InitialLocation.Z;
    for (const FBoundCraneActor& Bound : HookActors)
    {
        InitialHookZ = FMath::Min(InitialHookZ, Bound.InitialLocation.Z);
    }
    BridgeX = InitialBridgeX;
    TrolleyY = InitialTrolleyY;
    HookZ = InitialHookZ;

    const FVector SourceLocation = SourceCoilActor->GetActorLocation();
    const FVector StationLocation = PR004Station->GetActorLocation();
    PickupX = SourceLocation.X;
    PickupY = SourceLocation.Y;
    PickupZ = SourceLocation.Z + PickupHookZOffset;
    DropX = StationLocation.X;
    DropY = StationLocation.Y;
    DropZ = StationLocation.Z + DropHookZOffset;
    return true;
}

void ALBBridgeCraneController::BindActor(AActor* Actor, TArray<FBoundCraneActor>& Group, const bool bReeving)
{
    FBoundCraneActor Bound;
    Bound.Actor = Actor;
    Bound.InitialLocation = Actor->GetActorLocation();
    Bound.InitialScale = Actor->GetActorScale3D();
    Bound.bReeving = bReeving;
    Group.Add(Bound);
}

bool ALBBridgeCraneController::StartConfiguredTransfer()
{
    return StartTransfer(ConfiguredCoilId);
}

bool ALBBridgeCraneController::StartTransfer(const FString& CoilId)
{
    if (Phase != ELBBridgeCranePhase::Idle && Phase != ELBBridgeCranePhase::Complete)
    {
        return false;
    }
    if (!bBound && !DiscoverAndBind())
    {
        return false;
    }
    if (CoilId.IsEmpty() || !SourceCoilActor || SourceCoilActor->IsHidden())
    {
        LatchFault(ELBBridgeCraneFault::SourceCoilUnavailable);
        return false;
    }
    if (!bControlPowerOn)
    {
        LatchFault(ELBBridgeCraneFault::ControlPowerLost);
        return false;
    }
    if (!SafetyHealthy())
    {
        LatchFault(ELBBridgeCraneFault::RouteOrPersonnelUnsafe);
        return false;
    }
    if (!PR004Station || PR004Station->GetProcessState() != ELBPR004State::AwaitingCoil
        || !PR004Station->GetCurrentCoilId().IsEmpty())
    {
        LatchFault(ELBBridgeCraneFault::PR004RejectedDeposit);
        return false;
    }

    ActiveCoilId = CoilId;
    bCarryingCoil = false;
    bSourceCoilConsumed = false;
    MaxLoadFollowErrorCm = 0.0f;
    MaxAttachmentFollowErrorCm = 0.0f;
    ActiveFault = ELBBridgeCraneFault::None;
    PR004Station->SetCHookWithdrawn(false);
    EnterPhase(ELBBridgeCranePhase::BridgeToPickup);
    return true;
}

bool ALBBridgeCraneController::SetSafetyInputs(const bool bRouteIsClear,
    const bool bPersonnelAreClear, const bool bTransferGateIsClosed)
{
    bRouteClear = bRouteIsClear;
    bPersonnelClear = bPersonnelAreClear;
    bTransferGateClosed = bTransferGateIsClosed;
    if (!SafetyHealthy() && IsMotionPhase(Phase))
    {
        LatchFault(ELBBridgeCraneFault::RouteOrPersonnelUnsafe);
    }
    return true;
}

bool ALBBridgeCraneController::SetControlPower(const bool bEnabled)
{
    bControlPowerOn = bEnabled;
    if (!bControlPowerOn && IsMotionPhase(Phase))
    {
        LatchFault(ELBBridgeCraneFault::ControlPowerLost);
    }
    return true;
}

bool ALBBridgeCraneController::ResetFault(const FName RecoveryEvidenceId)
{
    if (Phase != ELBBridgeCranePhase::Fault || RecoveryEvidenceId.IsNone()
        || !bControlPowerOn || !SafetyHealthy() || ActiveFault == ELBBridgeCraneFault::BindingIncomplete)
    {
        return false;
    }
    ActiveFault = ELBBridgeCraneFault::None;
    EnterPhase(PhaseBeforeFault);
    return true;
}

void ALBBridgeCraneController::Tick(const float DeltaSeconds)
{
    Super::Tick(DeltaSeconds);
    if (!bBound || Phase == ELBBridgeCranePhase::Idle || Phase == ELBBridgeCranePhase::Complete
        || Phase == ELBBridgeCranePhase::Fault)
    {
        return;
    }
    if (!bControlPowerOn)
    {
        LatchFault(ELBBridgeCraneFault::ControlPowerLost);
        return;
    }
    if (!SafetyHealthy())
    {
        LatchFault(ELBBridgeCraneFault::RouteOrPersonnelUnsafe);
        return;
    }

    PhaseElapsedSeconds += FMath::Max(0.0f, DeltaSeconds);
    bool bReached = false;
    switch (Phase)
    {
    case ELBBridgeCranePhase::BridgeToPickup:
        bReached = MoveAxis(BridgeX, PickupX, BridgeSpeedCmPerSecond, DeltaSeconds);
        if (bReached) EnterPhase(ELBBridgeCranePhase::TrolleyToPickup);
        break;
    case ELBBridgeCranePhase::TrolleyToPickup:
        bReached = MoveAxis(TrolleyY, PickupY, TrolleySpeedCmPerSecond, DeltaSeconds);
        if (bReached) EnterPhase(ELBBridgeCranePhase::LoweringToPickup);
        break;
    case ELBBridgeCranePhase::LoweringToPickup:
        bReached = MoveAxis(HookZ, PickupZ, HoistSpeedCmPerSecond, DeltaSeconds);
        if (bReached) EnterPhase(ELBBridgeCranePhase::SecuringLoad);
        break;
    case ELBBridgeCranePhase::SecuringLoad:
        if (PhaseElapsedSeconds >= SecureDelaySeconds)
        {
            bCarryingCoil = true;
            SetSourcePresentation(true, false);
            EnterPhase(ELBBridgeCranePhase::RaisingLoad);
        }
        break;
    case ELBBridgeCranePhase::RaisingLoad:
        bReached = MoveAxis(HookZ, SafeHookZ, HoistSpeedCmPerSecond, DeltaSeconds);
        if (bReached) EnterPhase(ELBBridgeCranePhase::BridgeToDrop);
        break;
    case ELBBridgeCranePhase::BridgeToDrop:
        bReached = MoveAxis(BridgeX, DropX, BridgeSpeedCmPerSecond, DeltaSeconds);
        if (bReached) EnterPhase(ELBBridgeCranePhase::TrolleyToDrop);
        break;
    case ELBBridgeCranePhase::TrolleyToDrop:
        bReached = MoveAxis(TrolleyY, DropY, TrolleySpeedCmPerSecond, DeltaSeconds);
        if (bReached) EnterPhase(ELBBridgeCranePhase::LoweringToDrop);
        break;
    case ELBBridgeCranePhase::LoweringToDrop:
        bReached = MoveAxis(HookZ, DropZ, HoistSpeedCmPerSecond, DeltaSeconds);
        if (bReached) EnterPhase(ELBBridgeCranePhase::Depositing);
        break;
    case ELBBridgeCranePhase::Depositing:
        if (!PR004Station || !PR004Station->LoadPackagedCoilWithTraceability(
            ActiveCoilId, ConfiguredHeatId, ConfiguredSupplierLotId, ConfiguredTraceabilityBarcode))
        {
            LatchFault(ELBBridgeCraneFault::PR004RejectedDeposit);
            break;
        }
        PR004Station->SetCradleLocked(true);
        bCarryingCoil = false;
        bSourceCoilConsumed = true;
        SetSourcePresentation(false, false);
        EnterPhase(ELBBridgeCranePhase::WithdrawingHook);
        break;
    case ELBBridgeCranePhase::WithdrawingHook:
        bReached = MoveAxis(HookZ, SafeHookZ, HoistSpeedCmPerSecond, DeltaSeconds);
        if (bReached)
        {
            PR004Station->SetCHookWithdrawn(true);
            EnterPhase(ELBBridgeCranePhase::Complete);
        }
        break;
    default:
        break;
    }
    ApplyPose();
}

bool ALBBridgeCraneController::MoveAxis(float& Value, const float Target,
    const float Speed, const float DeltaSeconds)
{
    Value = FMath::FInterpConstantTo(Value, Target, FMath::Max(0.0f, DeltaSeconds), Speed);
    return FMath::IsNearlyEqual(Value, Target, 0.1f);
}

void ALBBridgeCraneController::ApplyPose()
{
    const float DeltaX = BridgeX - InitialBridgeX;
    const float DeltaY = TrolleyY - InitialTrolleyY;
    const float DeltaZ = HookZ - InitialHookZ;
    for (const FBoundCraneActor& Bound : BridgeActors)
    {
        if (AActor* Actor = Bound.Actor.Get()) Actor->SetActorLocation(Bound.InitialLocation + FVector(DeltaX, 0.0f, 0.0f));
    }
    for (const FBoundCraneActor& Bound : TrolleyActors)
    {
        if (AActor* Actor = Bound.Actor.Get()) Actor->SetActorLocation(Bound.InitialLocation + FVector(DeltaX, DeltaY, 0.0f));
    }
    for (const FBoundCraneActor& Bound : HoistActors)
    {
        AActor* Actor = Bound.Actor.Get();
        if (!Actor) continue;
        if (Bound.bReeving)
        {
            const float HalfInitialLength = 50.0f * Bound.InitialScale.Z;
            const float TopZ = Bound.InitialLocation.Z + HalfInitialLength;
            const float BottomZ = Bound.InitialLocation.Z - HalfInitialLength + DeltaZ;
            const float NewLength = FMath::Max(10.0f, TopZ - BottomZ);
            Actor->SetActorLocation(FVector(Bound.InitialLocation.X + DeltaX,
                Bound.InitialLocation.Y + DeltaY, (TopZ + BottomZ) * 0.5f));
            Actor->SetActorScale3D(FVector(Bound.InitialScale.X, Bound.InitialScale.Y, NewLength / 100.0f));
        }
        else
        {
            Actor->SetActorLocation(Bound.InitialLocation + FVector(DeltaX, DeltaY, DeltaZ));
        }
    }
    for (const FBoundCraneActor& Bound : HookActors)
    {
        if (AActor* Actor = Bound.Actor.Get()) Actor->SetActorLocation(Bound.InitialLocation + FVector(DeltaX, DeltaY, DeltaZ));
    }
    if (bCarryingCoil && SourceCoilActor)
    {
        // The hook actor datum is at the forged C-body centre.  Its padded
        // lower arm enters the coil bore below that datum, so preserve the
        // physical engagement offset throughout lift and travel.
        const FVector SourceLocation(BridgeX, TrolleyY, HookZ - PickupHookZOffset);
        SourceCoilActor->SetActorLocation(SourceLocation);
        MaxLoadFollowErrorCm = FMath::Max(MaxLoadFollowErrorCm,
            FVector::Distance(SourceCoilActor->GetActorLocation(), SourceLocation));
        const FVector InitialSourceLocation(PickupX, PickupY, PickupZ - PickupHookZOffset);
        for (const FBoundCraneActor& Bound : SourceAttachmentActors)
        {
            if (AActor* Actor = Bound.Actor.Get())
            {
                Actor->SetActorLocation(SourceLocation + (Bound.InitialLocation - InitialSourceLocation));
                const FVector ExpectedAttachment = SourceLocation + (Bound.InitialLocation - InitialSourceLocation);
                MaxAttachmentFollowErrorCm = FMath::Max(MaxAttachmentFollowErrorCm,
                    FVector::Distance(Actor->GetActorLocation(), ExpectedAttachment));
            }
        }
    }
}

bool ALBBridgeCraneController::SafetyHealthy() const
{
    return bRouteClear && bPersonnelClear && bTransferGateClosed;
}

bool ALBBridgeCraneController::IsMotionPhase(const ELBBridgeCranePhase Candidate) const
{
    return Candidate != ELBBridgeCranePhase::Idle && Candidate != ELBBridgeCranePhase::Complete
        && Candidate != ELBBridgeCranePhase::Fault;
}

void ALBBridgeCraneController::EnterPhase(const ELBBridgeCranePhase NewPhase)
{
    Phase = NewPhase;
    PhaseElapsedSeconds = 0.0f;
}

void ALBBridgeCraneController::LatchFault(const ELBBridgeCraneFault Fault)
{
    if (Phase != ELBBridgeCranePhase::Fault)
    {
        PhaseBeforeFault = Phase;
    }
    ActiveFault = Fault;
    EnterPhase(ELBBridgeCranePhase::Fault);
}

void ALBBridgeCraneController::SetSourcePresentation(const bool bVisible, const bool bCollisionEnabled)
{
    if (!SourceCoilActor) return;
    SourceCoilActor->SetActorHiddenInGame(!bVisible);
    SourceCoilActor->SetActorEnableCollision(bCollisionEnabled);
    for (const FBoundCraneActor& Bound : SourceAttachmentActors)
    {
        if (AActor* Actor = Bound.Actor.Get())
        {
            Actor->SetActorHiddenInGame(!bVisible);
            Actor->SetActorEnableCollision(false);
        }
    }
}

bool ALBBridgeCraneController::GetSaveState(FLBBridgeCraneSaveState& OutState) const
{
    if (!bBound || ActiveCoilId.IsEmpty() && Phase != ELBBridgeCranePhase::Idle)
    {
        return false;
    }
    OutState.SaveVersion = 1;
    OutState.Phase = Phase;
    OutState.PhaseBeforeFault = PhaseBeforeFault;
    OutState.Fault = ActiveFault;
    OutState.CoilId = ActiveCoilId;
    OutState.BridgeX = BridgeX;
    OutState.TrolleyY = TrolleyY;
    OutState.HookZ = HookZ;
    OutState.PhaseElapsedSeconds = PhaseElapsedSeconds;
    OutState.bCarryingCoil = bCarryingCoil;
    OutState.bSourceCoilConsumed = bSourceCoilConsumed;
    return true;
}

bool ALBBridgeCraneController::RestoreSaveState(const FLBBridgeCraneSaveState& InState)
{
    if (InState.SaveVersion != 1 || !bBound || InState.Phase == ELBBridgeCranePhase::Depositing
        || (InState.bCarryingCoil && InState.CoilId.IsEmpty()))
    {
        return false;
    }
    Phase = InState.Phase;
    PhaseBeforeFault = InState.PhaseBeforeFault;
    ActiveFault = InState.Fault;
    ActiveCoilId = InState.CoilId;
    BridgeX = InState.BridgeX;
    TrolleyY = InState.TrolleyY;
    HookZ = InState.HookZ;
    PhaseElapsedSeconds = FMath::Max(0.0f, InState.PhaseElapsedSeconds);
    bCarryingCoil = InState.bCarryingCoil;
    bSourceCoilConsumed = InState.bSourceCoilConsumed;
    SetSourcePresentation(!bSourceCoilConsumed, !bCarryingCoil && !bSourceCoilConsumed);
    ApplyPose();
    return true;
}
