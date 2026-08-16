#include "LBSupportCraneController.h"

#include "EngineUtils.h"

namespace
{
    const FName BridgeMotionTag(TEXT("LB.Motion.CraneBridge"));
    const FName TrolleyMotionTag(TEXT("LB.Motion.CraneTrolley"));
    const FName HoistMotionTag(TEXT("LB.Motion.Hoist"));
    const FName HookMotionTag(TEXT("LB.Motion.CHook"));
    const FName ReevingTag(TEXT("LB.Module.HoistReeving"));
}

ALBSupportCraneController::ALBSupportCraneController()
{
    PrimaryActorTick.bCanEverTick = true;
}

void ALBSupportCraneController::BeginPlay()
{
    Super::BeginPlay();
    DiscoverAndBind();
}

bool ALBSupportCraneController::DiscoverAndBind()
{
    BridgeActors.Reset();
    TrolleyActors.Reset();
    HoistActors.Reset();
    HookActors.Reset();
    ServicePointActor = nullptr;

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
        if (Actor->ActorHasTag(ConfiguredServicePointTag))
        {
            ServicePointActor = Actor;
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

    bBound = ServicePointActor && !BridgeActors.IsEmpty() && !TrolleyActors.IsEmpty()
        && !HoistActors.IsEmpty() && !HookActors.IsEmpty();
    if (!bBound)
    {
        LatchFault(ELBSupportCraneFault::BindingIncomplete);
        return false;
    }

    HomeBridgeX = TrolleyActors[0].InitialLocation.X;
    HomeTrolleyY = TrolleyActors[0].InitialLocation.Y;
    HomeHookZ = HookActors[0].InitialLocation.Z;
    for (const FBoundCraneActor& Bound : HookActors)
    {
        HomeHookZ = FMath::Min(HomeHookZ, Bound.InitialLocation.Z);
    }
    BridgeX = HomeBridgeX;
    TrolleyY = HomeTrolleyY;
    HookZ = HomeHookZ;

    const FVector ServiceLocation = ServicePointActor->GetActorLocation();
    ServiceBridgeX = ServiceLocation.X;
    ServiceTrolleyY = ServiceLocation.Y;
    ServiceHookZ = ServiceLocation.Z;
    ActiveFault = ELBSupportCraneFault::None;
    EnterPhase(ELBSupportCranePhase::Parked);
    return true;
}

void ALBSupportCraneController::BindActor(AActor* Actor, TArray<FBoundCraneActor>& Group,
    const bool bReeving)
{
    FBoundCraneActor Bound;
    Bound.Actor = Actor;
    Bound.InitialLocation = Actor->GetActorLocation();
    Bound.InitialScale = Actor->GetActorScale3D();
    Bound.bReeving = bReeving;
    Group.Add(Bound);
}

bool ALBSupportCraneController::DispatchToConfiguredServicePoint()
{
    if (Phase != ELBSupportCranePhase::Parked)
    {
        return false;
    }
    if (!bBound && !DiscoverAndBind())
    {
        return false;
    }
    if (!bControlPowerOn)
    {
        LatchFault(ELBSupportCraneFault::ControlPowerLost);
        return false;
    }
    const ELBSupportCraneFault SafetyFault = CurrentSafetyFault();
    if (SafetyFault != ELBSupportCraneFault::None)
    {
        LatchFault(SafetyFault);
        return false;
    }
    ActiveFault = ELBSupportCraneFault::None;
    EnterPhase(ELBSupportCranePhase::DispatchingBridge);
    return true;
}

bool ALBSupportCraneController::ReturnToPark()
{
    if (Phase != ELBSupportCranePhase::OnStation)
    {
        return false;
    }
    if (!bControlPowerOn)
    {
        LatchFault(ELBSupportCraneFault::ControlPowerLost);
        return false;
    }
    const ELBSupportCraneFault SafetyFault = CurrentSafetyFault();
    if (SafetyFault != ELBSupportCraneFault::None)
    {
        LatchFault(SafetyFault);
        return false;
    }
    EnterPhase(ELBSupportCranePhase::RaisingToTravel);
    return true;
}

bool ALBSupportCraneController::SetSafetyInputs(const bool bRouteIsClear,
    const bool bPersonnelAreClear, const bool bMaintenancePermitIsActive,
    const bool bSupportZoneIsReserved)
{
    bRouteClear = bRouteIsClear;
    bPersonnelClear = bPersonnelAreClear;
    bMaintenancePermitActive = bMaintenancePermitIsActive;
    bSupportZoneReserved = bSupportZoneIsReserved;
    if (IsMotionPhase(Phase))
    {
        const ELBSupportCraneFault SafetyFault = CurrentSafetyFault();
        if (SafetyFault != ELBSupportCraneFault::None)
        {
            LatchFault(SafetyFault);
        }
    }
    return true;
}

bool ALBSupportCraneController::SetPrimaryCraneClear(const bool bIsClear)
{
    bPrimaryCraneClear = bIsClear;
    if (!bPrimaryCraneClear && IsMotionPhase(Phase))
    {
        LatchFault(ELBSupportCraneFault::PrimaryCraneConflict);
    }
    return true;
}

bool ALBSupportCraneController::SetControlPower(const bool bEnabled)
{
    bControlPowerOn = bEnabled;
    if (!bControlPowerOn && IsMotionPhase(Phase))
    {
        LatchFault(ELBSupportCraneFault::ControlPowerLost);
    }
    return true;
}

bool ALBSupportCraneController::ResetFault(const FName RecoveryEvidenceId)
{
    if (Phase != ELBSupportCranePhase::Fault || RecoveryEvidenceId.IsNone()
        || !bControlPowerOn || !DispatchSafetyHealthy()
        || ActiveFault == ELBSupportCraneFault::BindingIncomplete)
    {
        return false;
    }

    ActiveFault = ELBSupportCraneFault::None;
    if (PhaseBeforeFault == ELBSupportCranePhase::Fault)
    {
        EnterPhase(ELBSupportCranePhase::Parked);
    }
    else
    {
        EnterPhase(PhaseBeforeFault);
    }
    return true;
}

void ALBSupportCraneController::Tick(const float DeltaSeconds)
{
    Super::Tick(DeltaSeconds);
    if (!bBound || Phase == ELBSupportCranePhase::Parked
        || Phase == ELBSupportCranePhase::OnStation || Phase == ELBSupportCranePhase::Fault)
    {
        return;
    }
    if (!bControlPowerOn)
    {
        LatchFault(ELBSupportCraneFault::ControlPowerLost);
        return;
    }
    const ELBSupportCraneFault SafetyFault = CurrentSafetyFault();
    if (SafetyFault != ELBSupportCraneFault::None)
    {
        LatchFault(SafetyFault);
        return;
    }

    PhaseElapsedSeconds += FMath::Max(0.0f, DeltaSeconds);
    bool bReached = false;
    switch (Phase)
    {
    case ELBSupportCranePhase::DispatchingBridge:
        bReached = MoveAxis(BridgeX, ServiceBridgeX, BridgeSpeedCmPerSecond, DeltaSeconds);
        if (bReached) EnterPhase(ELBSupportCranePhase::DispatchingTrolley);
        break;
    case ELBSupportCranePhase::DispatchingTrolley:
        bReached = MoveAxis(TrolleyY, ServiceTrolleyY, TrolleySpeedCmPerSecond, DeltaSeconds);
        if (bReached) EnterPhase(ELBSupportCranePhase::LoweringForSupport);
        break;
    case ELBSupportCranePhase::LoweringForSupport:
        bReached = MoveAxis(HookZ, ServiceHookZ, HoistSpeedCmPerSecond, DeltaSeconds);
        if (bReached) EnterPhase(ELBSupportCranePhase::OnStation);
        break;
    case ELBSupportCranePhase::RaisingToTravel:
        bReached = MoveAxis(HookZ, HomeHookZ, HoistSpeedCmPerSecond, DeltaSeconds);
        if (bReached) EnterPhase(ELBSupportCranePhase::ReturningTrolley);
        break;
    case ELBSupportCranePhase::ReturningTrolley:
        bReached = MoveAxis(TrolleyY, HomeTrolleyY, TrolleySpeedCmPerSecond, DeltaSeconds);
        if (bReached) EnterPhase(ELBSupportCranePhase::ReturningBridge);
        break;
    case ELBSupportCranePhase::ReturningBridge:
        bReached = MoveAxis(BridgeX, HomeBridgeX, BridgeSpeedCmPerSecond, DeltaSeconds);
        if (bReached) EnterPhase(ELBSupportCranePhase::Complete);
        break;
    case ELBSupportCranePhase::Complete:
        if (PhaseElapsedSeconds >= CompleteHoldSeconds)
        {
            EnterPhase(ELBSupportCranePhase::Parked);
        }
        break;
    default:
        break;
    }
    ApplyPose();
}

bool ALBSupportCraneController::MoveAxis(float& Value, const float Target,
    const float Speed, const float DeltaSeconds)
{
    Value = FMath::FInterpConstantTo(Value, Target, FMath::Max(0.0f, DeltaSeconds), Speed);
    return FMath::IsNearlyEqual(Value, Target, 0.1f);
}

void ALBSupportCraneController::ApplyPose()
{
    const float DeltaX = BridgeX - HomeBridgeX;
    const float DeltaY = TrolleyY - HomeTrolleyY;
    const float DeltaZ = HookZ - HomeHookZ;
    for (const FBoundCraneActor& Bound : BridgeActors)
    {
        if (AActor* Actor = Bound.Actor.Get())
        {
            Actor->SetActorLocation(Bound.InitialLocation + FVector(DeltaX, 0.0f, 0.0f));
        }
    }
    for (const FBoundCraneActor& Bound : TrolleyActors)
    {
        if (AActor* Actor = Bound.Actor.Get())
        {
            Actor->SetActorLocation(Bound.InitialLocation + FVector(DeltaX, DeltaY, 0.0f));
        }
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
            Actor->SetActorScale3D(FVector(Bound.InitialScale.X, Bound.InitialScale.Y,
                NewLength / 100.0f));
        }
        else
        {
            Actor->SetActorLocation(Bound.InitialLocation + FVector(DeltaX, DeltaY, DeltaZ));
        }
    }
    for (const FBoundCraneActor& Bound : HookActors)
    {
        if (AActor* Actor = Bound.Actor.Get())
        {
            Actor->SetActorLocation(Bound.InitialLocation + FVector(DeltaX, DeltaY, DeltaZ));
        }
    }
}

bool ALBSupportCraneController::DispatchSafetyHealthy() const
{
    return CurrentSafetyFault() == ELBSupportCraneFault::None;
}

ELBSupportCraneFault ALBSupportCraneController::CurrentSafetyFault() const
{
    if (!bRouteClear || !bPersonnelClear)
    {
        return ELBSupportCraneFault::RouteOrPersonnelUnsafe;
    }
    if (!bMaintenancePermitActive)
    {
        return ELBSupportCraneFault::MaintenancePermitMissing;
    }
    if (!bSupportZoneReserved)
    {
        return ELBSupportCraneFault::SupportZoneNotReserved;
    }
    if (!bPrimaryCraneClear)
    {
        return ELBSupportCraneFault::PrimaryCraneConflict;
    }
    return ELBSupportCraneFault::None;
}

bool ALBSupportCraneController::IsMotionPhase(const ELBSupportCranePhase Candidate) const
{
    return Candidate != ELBSupportCranePhase::Parked
        && Candidate != ELBSupportCranePhase::OnStation
        && Candidate != ELBSupportCranePhase::Complete
        && Candidate != ELBSupportCranePhase::Fault;
}

bool ALBSupportCraneController::IsStablePhase(const ELBSupportCranePhase Candidate) const
{
    return Candidate == ELBSupportCranePhase::Parked || Candidate == ELBSupportCranePhase::OnStation;
}

void ALBSupportCraneController::EnterPhase(const ELBSupportCranePhase NewPhase)
{
    Phase = NewPhase;
    PhaseElapsedSeconds = 0.0f;
}

void ALBSupportCraneController::LatchFault(const ELBSupportCraneFault Fault)
{
    if (Phase != ELBSupportCranePhase::Fault)
    {
        PhaseBeforeFault = Phase;
    }
    ActiveFault = Fault;
    EnterPhase(ELBSupportCranePhase::Fault);
}

bool ALBSupportCraneController::GetSaveState(FLBSupportCraneSaveState& OutState) const
{
    if (!bBound)
    {
        return false;
    }
    OutState.SaveVersion = 1;
    OutState.Phase = Phase;
    OutState.PhaseBeforeFault = PhaseBeforeFault;
    OutState.Fault = ActiveFault;
    OutState.ServicePointId = ConfiguredServicePointTag;
    OutState.BridgeX = BridgeX;
    OutState.TrolleyY = TrolleyY;
    OutState.HookZ = HookZ;
    OutState.bStableState = IsStablePhase(Phase);
    return true;
}

bool ALBSupportCraneController::RestoreSaveState(const FLBSupportCraneSaveState& InState)
{
    if (InState.SaveVersion != 1 || !bBound || InState.ServicePointId != ConfiguredServicePointTag)
    {
        return false;
    }

    BridgeX = InState.BridgeX;
    TrolleyY = InState.TrolleyY;
    HookZ = InState.HookZ;
    if (InState.bStableState && IsStablePhase(InState.Phase))
    {
        Phase = InState.Phase;
        PhaseBeforeFault = InState.PhaseBeforeFault;
        ActiveFault = InState.Fault;
    }
    else
    {
        PhaseBeforeFault = InState.Phase;
        ActiveFault = ELBSupportCraneFault::RestoreInterlockStop;
        Phase = ELBSupportCranePhase::Fault;
    }
    PhaseElapsedSeconds = 0.0f;
    ApplyPose();
    return true;
}
