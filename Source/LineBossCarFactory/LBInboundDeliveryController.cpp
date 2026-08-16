#include "LBInboundDeliveryController.h"

#include "EngineUtils.h"
#include "LBCoilAGVController.h"
#include "LBFactoryBuildMachine.h"
#include "LBFactoryTransportLink.h"
#include "LBPressShopStorageZone.h"
#include "Components/SceneComponent.h"
#include "Components/StaticMeshComponent.h"

namespace
{
    // Powered C-hook Candidate_v035 retained interface: its padded bore arm carries the
    // coil centre 1.50 m along source +X and 0.59 m below the hook component datum.
    const FVector HookDatumToLoadCentreCm(150.0, 0.0, -59.0);
    // The temporary handler ram is a 1.6 m cylinder whose local +Z becomes world +X.
    // Its nose sits 0.8 m from the component origin and enters the coil bore.
    // Common-pivot datum of the separate v999 lift assembly. Its tapered ram
    // nose is at local -X and 1.10 m above the floor.
    const FVector HandlerRamDatumToLoadCentreCm(-301.5, 0.0, 110.0);

    FVector EvaluateCubicPath(const FVector& Start, const FVector& ControlA,
        const FVector& ControlB, const FVector& End, const float Alpha)
    {
        const float OneMinusAlpha = 1.0f - Alpha;
        return Start * (OneMinusAlpha * OneMinusAlpha * OneMinusAlpha)
            + ControlA * (3.0f * OneMinusAlpha * OneMinusAlpha * Alpha)
            + ControlB * (3.0f * OneMinusAlpha * Alpha * Alpha)
            + End * (Alpha * Alpha * Alpha);
    }

    FVector EvaluateCubicPathDerivative(const FVector& Start, const FVector& ControlA,
        const FVector& ControlB, const FVector& End, const float Alpha)
    {
        const float OneMinusAlpha = 1.0f - Alpha;
        return (ControlA - Start) * (3.0f * OneMinusAlpha * OneMinusAlpha)
            + (ControlB - ControlA) * (6.0f * OneMinusAlpha * Alpha)
            + (End - ControlB) * (3.0f * Alpha * Alpha);
    }

    FVector EvaluateCubicPathSecondDerivative(const FVector& Start,
        const FVector& ControlA, const FVector& ControlB, const FVector& End,
        const float Alpha)
    {
        return (ControlB - ControlA * 2.0f + Start) * (6.0f * (1.0f - Alpha))
            + (End - ControlB * 2.0f + ControlA) * (6.0f * Alpha);
    }

    float EvaluateCubicPathCurvature(const FVector& Start, const FVector& ControlA,
        const FVector& ControlB, const FVector& End, const float Alpha)
    {
        const FVector First = EvaluateCubicPathDerivative(Start, ControlA,
            ControlB, End, Alpha);
        const FVector Second = EvaluateCubicPathSecondDerivative(Start, ControlA,
            ControlB, End, Alpha);
        const float Denominator = FMath::Pow(FMath::Max(First.Size2D(), 0.01f), 3.0f);
        return (First.X * Second.Y - First.Y * Second.X) / Denominator;
    }

    float ApproximateCubicPathLength(const FVector& Start, const FVector& ControlA,
        const FVector& ControlB, const FVector& End, const float FromAlpha,
        const float ToAlpha, const int32 Segments = 16)
    {
        FVector Previous = EvaluateCubicPath(Start, ControlA, ControlB, End, FromAlpha);
        float LengthCm = 0.0f;
        for (int32 Segment = 1; Segment <= Segments; ++Segment)
        {
            const float Alpha = FMath::Lerp(FromAlpha, ToAlpha,
                static_cast<float>(Segment) / static_cast<float>(Segments));
            const FVector Current = EvaluateCubicPath(Start, ControlA, ControlB, End, Alpha);
            LengthCm += FVector::Dist2D(Previous, Current);
            Previous = Current;
        }
        return LengthCm;
    }

    bool SegmentIntersectsExpandedMachineEnvelope(const FVector& WorldStart,
        const FVector& WorldEnd, const ALBFactoryBuildMachine& Machine,
        const float SweepRadiusCm, const float ExtraClearanceCm)
    {
        const FVector LocalStart = Machine.GetActorTransform().InverseTransformPositionNoScale(
            WorldStart) - Machine.GetProtectedEnvelopeRelativeCentre();
        const FVector LocalEnd = Machine.GetActorTransform().InverseTransformPositionNoScale(
            WorldEnd) - Machine.GetProtectedEnvelopeRelativeCentre();
        const FVector MachineExtent = Machine.GetProtectedEnvelopeHalfExtent();
        const FVector2D ExpandedExtent(MachineExtent.X + SweepRadiusCm + ExtraClearanceCm,
            MachineExtent.Y + SweepRadiusCm + ExtraClearanceCm);
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

    bool IsLegacyInboundSourcePresentationActor(const AActor* Actor)
    {
        if (!Actor) return false;
        static const FName LegacyTags[] = {
            TEXT("LB.Inbound.Visual.Lorry"),
            TEXT("LB.Inbound.Visual.CraneBridge"),
            TEXT("LB.Inbound.Visual.CraneTrolley"),
            TEXT("LB.Inbound.Visual.Hoist"),
            TEXT("LB.Inbound.Visual.Hook"),
            TEXT("LB.Inbound.Visual.Saddle"),
            TEXT("LB.Inbound.Visual.TrailerCoil.01"),
            TEXT("LB.Inbound.Visual.TrailerCoil.02"),
            TEXT("LB.Inbound.Visual.TrailerCoil.03"),
            TEXT("LB.Inbound.Visual.TrailerCoil.04")
        };
        for (const FName Tag : LegacyTags)
            if (Actor->ActorHasTag(Tag)) return true;
        return false;
    }
}

ALBInboundDeliveryController::ALBInboundDeliveryController()
{
    PrimaryActorTick.bCanEverTick = true;
}

void ALBInboundDeliveryController::BeginPlay()
{
    Super::BeginPlay();
    if (SourceMode == ELBInboundDeliverySourceMode::LegacyLorry
        && bAutoDiscoverVisualSequence && !bVisualSequenceBound)
    {
        DiscoverAndBindVisualSequence();
    }
}

void ALBInboundDeliveryController::SetPlayerBuilderBootstrapEnabled(const bool bEnabled)
{
    bPlayerBuilderBootstrapEnabled = bEnabled;
    bPlayerBuilderBootstrapBound = false;
    PlayerBuilderBootstrapAccumulator = bEnabled ? PlayerBuilderBootstrapIntervalSeconds : 0.0f;
}

bool ALBInboundDeliveryController::DiscoverAndBindVisualSequence()
{
    if (!GetWorld() || SourceMode != ELBInboundDeliverySourceMode::LegacyLorry)
        return false;
    AActor* Lorry = nullptr;
    AActor* Bridge = nullptr;
    AActor* Trolley = nullptr;
    AActor* Hoist = nullptr;
    AActor* Hook = nullptr;
    AActor* Saddle = nullptr;
    TArray<AActor*> Coils;
    Coils.SetNumZeroed(4);
    const auto FindTag = [](const AActor* Actor, const TCHAR* Value)
    {
        return Actor && Actor->ActorHasTag(FName(Value));
    };
    for (TActorIterator<AActor> It(GetWorld()); It; ++It)
    {
        AActor* Actor = *It;
        if (FindTag(Actor, TEXT("LB.Inbound.Visual.Lorry"))) Lorry = Actor;
        else if (FindTag(Actor, TEXT("LB.Inbound.Visual.CraneBridge"))) Bridge = Actor;
        else if (FindTag(Actor, TEXT("LB.Inbound.Visual.CraneTrolley"))) Trolley = Actor;
        else if (FindTag(Actor, TEXT("LB.Inbound.Visual.Hoist"))) Hoist = Actor;
        else if (FindTag(Actor, TEXT("LB.Inbound.Visual.Hook"))) Hook = Actor;
        else if (FindTag(Actor, TEXT("LB.Inbound.Visual.Saddle"))) Saddle = Actor;
        for (int32 Index = 0; Index < 4; ++Index)
        {
            const FName CoilTag(*FString::Printf(TEXT("LB.Inbound.Visual.TrailerCoil.%02d"), Index + 1));
            if (Actor && Actor->ActorHasTag(CoilTag)) Coils[Index] = Actor;
        }
    }
    return ConfigureVisualSequence(Lorry, Bridge, Trolley, Hoist, Hook, Saddle, Coils,
        AuthoredLorryApproachPoint, AuthoredLorryDockPoint);
}

bool ALBInboundDeliveryController::Configure(ALBFactoryBuildMachine* InInboundDock,
    ALBFactoryBuildMachine* InPR002Cell, ALBCoilAGVController* InCoilAGV)
{
    FString IgnoredReason;
    return ConfigureForSourceMode(InInboundDock, InPR002Cell, InCoilAGV,
        ELBInboundDeliverySourceMode::LegacyLorry, IgnoredReason);
}

bool ALBInboundDeliveryController::ConfigureForSourceMode(
    ALBFactoryBuildMachine* InInboundDock, ALBFactoryBuildMachine* InPR002Cell,
    ALBCoilAGVController* InCoilAGV, const ELBInboundDeliverySourceMode InSourceMode,
    FString& OutReason)
{
    OutReason.Reset();
    if (!StaticEnum<ELBInboundDeliverySourceMode>()->IsValidEnumValue(
            static_cast<int64>(InSourceMode))
        || !InInboundDock || !InPR002Cell || !InCoilAGV
        || !GetWorld() || InInboundDock->GetWorld() != GetWorld()
        || InPR002Cell->GetWorld() != GetWorld() || InCoilAGV->GetWorld() != GetWorld()
        || InInboundDock->GetMachineType() != ELBFactoryBuildMachineType::InboundDeliveryDock
        || InPR002Cell->GetMachineType() != ELBFactoryBuildMachineType::CoilWeighInspectionCell)
    {
        OutReason = TEXT("INBOUND SOURCE MODE NEEDS ONE VALID DOCK, PR002 AND COIL AGV IN THIS WORLD");
        return false;
    }
    const bool bSameBoundEndpoints = InboundDock == InInboundDock
        && PR002Cell == InPR002Cell && CoilAGV == InCoilAGV
        && SourceMode == InSourceMode;
    const bool bCompletingWaitingStorageBinding = SourceMode == InSourceMode
        && Phase == ELBInboundDeliveryPhase::WaitingForStorage
        && !ActiveCoilId.IsNone()
        && InboundDock == InInboundDock
        && PR002Cell == nullptr
        && CoilAGV == InCoilAGV;
    if ((InboundDock || PR002Cell || CoilAGV) && SourceMode != InSourceMode)
    {
        OutReason = TEXT("A CONFIGURED INBOUND AUTHORITY CANNOT SWITCH SOURCE MODE");
        return false;
    }
    if (!bSameBoundEndpoints && !bCompletingWaitingStorageBinding
        && (Phase != ELBInboundDeliveryPhase::Idle || !ActiveCoilId.IsNone()))
    {
        OutReason = TEXT("INBOUND SOURCE MODE CAN ONLY CHANGE ENDPOINTS WHILE IDLE");
        return false;
    }
    if (!HasRequiredLink(InInboundDock, InPR002Cell))
    {
        OutReason = TEXT("INBOUND SOURCE MODE NEEDS ONE REAL DOCK-TO-PR002 LINK");
        return false;
    }
    if (InSourceMode == ELBInboundDeliverySourceMode::NativeAGVArrival)
    {
        const bool bAlreadyProvedNativeBinding = bSameBoundEndpoints
            && InCoilAGV->IsUsingNativeOneFactoryPresentation()
            && InInboundDock->IsUsingNativeAGVArrivalPresentation();
        if (!bAlreadyProvedNativeBinding
            && (InInboundDock->GetInputUnitCount() != 0
                || InInboundDock->GetOutputUnitCount() != 0
                || InInboundDock->GetCompletedUnitCount() != 0))
        {
            OutReason = TEXT("NATIVE AGV ARRIVAL CANNOT BIND WHILE THE INBOUND DOCK OWNS WIP");
            return false;
        }
        for (TActorIterator<AActor> It(GetWorld()); It; ++It)
        {
            if (IsLegacyInboundSourcePresentationActor(*It))
            {
                OutReason = FString::Printf(
                    TEXT("NATIVE AGV ARRIVAL REJECTED LEGACY LORRY UNLOAD ACTOR %s"),
                    *It->GetName());
                return false;
            }
        }
        if (!bAlreadyProvedNativeBinding)
        {
            FString PresentationReason;
            if (!InCoilAGV->ConfigureNativeOneFactoryPresentation(PresentationReason))
            {
                OutReason = PresentationReason;
                return false;
            }
            if (!InInboundDock->ConfigureNativeAGVArrivalPresentation(PresentationReason))
            {
                OutReason = PresentationReason;
                return false;
            }
        }
    }
    InboundDock = InInboundDock;
    PR002Cell = InPR002Cell;
    CoilAGV = InCoilAGV;
    SourceMode = InSourceMode;
    if (SourceMode == ELBInboundDeliverySourceMode::NativeAGVArrival)
    {
        bAutoDiscoverVisualSequence = false;
        ClearLegacyVisualSequenceBinding();
        OutReason = TEXT("NATIVE AGV ARRIVAL BOUND; LORRY AND COIL-HANDLER UNLOAD PRESENTATION DISABLED");
    }
    else
    {
        OutReason = TEXT("LEGACY LORRY INBOUND SOURCE BOUND");
    }
    return true;
}

bool ALBInboundDeliveryController::DiscoverPlayerBuilderEndpoints()
{
    bPlayerBuilderBootstrapBound = false;
    if (!GetWorld())
    {
        LastReason = TEXT("PLAYER-BUILDER INBOUND BOOTSTRAP HAS NO WORLD");
        return false;
    }

    TArray<ALBFactoryBuildMachine*> InboundCandidates;
    TArray<ALBFactoryBuildMachine*> PR002Candidates;
    TArray<ALBCoilAGVController*> AGVCandidates;
    for (TActorIterator<ALBFactoryBuildMachine> It(GetWorld()); It; ++It)
    {
        ALBFactoryBuildMachine* Machine = *It;
        if (!IsValid(Machine) || !Machine->ActorHasTag(TEXT("LB.FactoryBuilder.Machine"))) continue;
        if (Machine->GetMachineType() == ELBFactoryBuildMachineType::InboundDeliveryDock)
            InboundCandidates.Add(Machine);
        else if (Machine->GetMachineType() == ELBFactoryBuildMachineType::CoilWeighInspectionCell)
            PR002Candidates.Add(Machine);
    }
    for (TActorIterator<ALBCoilAGVController> It(GetWorld()); It; ++It)
        if (IsValid(*It)) AGVCandidates.Add(*It);

    if (InboundCandidates.Num() != 1 || PR002Candidates.Num() > 1 || AGVCandidates.Num() != 1)
    {
        LastReason = FString::Printf(
            TEXT("PLAYER-BUILDER INBOUND NEEDS ONE DOCK, AT MOST ONE PR002 AND ONE COIL AGV (FOUND %d/%d/%d)"),
            InboundCandidates.Num(), PR002Candidates.Num(), AGVCandidates.Num());
        return false;
    }

    ALBFactoryBuildMachine* CandidateInbound = InboundCandidates[0];
    ALBCoilAGVController* CandidateAGV = AGVCandidates[0];
    InboundDock = CandidateInbound;
    CoilAGV = CandidateAGV;
    if (SourceMode == ELBInboundDeliverySourceMode::LegacyLorry
        && !bPlayerBuiltComponentSequence && !ConfigurePlayerBuiltVisualSequence(CandidateInbound))
    {
        LastReason = TEXT("PLAYER-BUILDER MODULAR UNLOAD PRESENTATION COULD NOT BIND");
        return false;
    }
    if (PR002Candidates.IsEmpty())
    {
        PR002Cell = nullptr;
        LastReason = TEXT("UNLOAD CELL IS READY; COIL WILL BE HELD UNTIL STORAGE AND PR002 ARE INSTALLED");
        return true;
    }

    ALBFactoryBuildMachine* CandidatePR002 = PR002Candidates[0];
    int32 RequiredLinkCount = 0;
    for (TActorIterator<ALBFactoryTransportLink> It(GetWorld()); It; ++It)
    {
        const ALBFactoryTransportLink* Link = *It;
        if (IsValid(Link) && Link->GetSourcePort() && Link->GetTargetPort()
            && Link->GetSourcePort()->GetOwner() == CandidateInbound
            && Link->GetTargetPort()->GetOwner() == CandidatePR002)
        {
            ++RequiredLinkCount;
        }
    }
    if (RequiredLinkCount != 1)
    {
        LastReason = FString::Printf(
            TEXT("PLAYER-BUILDER INBOUND NEEDS ONE REAL DOCK-TO-PR002 LINK (FOUND %d)"),
            RequiredLinkCount);
        return false;
    }

    if (!CandidateAGV->ConfigureInboundRouteFromPlayerBuiltInfrastructure(
        CandidateInbound, CandidatePR002))
    {
        LastReason = TEXT("PLAYER-BUILDER INBOUND AGV ROUTE NEEDS A WAIT POINT, WAYPOINT AND TWO ROUTE SEGMENTS");
        return false;
    }
    FString ConfigureReason;
    if (!ConfigureForSourceMode(CandidateInbound, CandidatePR002, CandidateAGV,
        SourceMode, ConfigureReason))
    {
        LastReason = ConfigureReason;
        return false;
    }

    bPlayerBuilderBootstrapBound = true;
    LastReason = TEXT("PLAYER-BUILDER INBOUND IS BOUND AND READY");
    return true;
}

void ALBInboundDeliveryController::TickPlayerBuilderBootstrap(const float DeltaSeconds)
{
    if (!bPlayerBuilderBootstrapEnabled || Phase != ELBInboundDeliveryPhase::Idle) return;
    PlayerBuilderBootstrapAccumulator += DeltaSeconds;
    if (PlayerBuilderBootstrapAccumulator < PlayerBuilderBootstrapIntervalSeconds) return;
    PlayerBuilderBootstrapAccumulator = FMath::Fmod(
        PlayerBuilderBootstrapAccumulator, PlayerBuilderBootstrapIntervalSeconds);
    if (!DiscoverPlayerBuilderEndpoints()) return;
    if (!InboundDock || (SourceMode == ELBInboundDeliverySourceMode::LegacyLorry
        && InboundDock->GetVisibleTrailerCoilCount() <= 0))
    {
        LastReason = TEXT("PLAYER-BUILDER INBOUND TRAILER IS EMPTY");
        return;
    }
    FString StartReason;
    const FName CoilId(*FString::Printf(
        TEXT("COIL-INBOUND-%06d"), CompletedDeliveries + 1));
    if (!StartDelivery(CoilId, StartReason)) LastReason = StartReason;
}

bool ALBInboundDeliveryController::ConfigureVisualSequence(AActor* InLorry, AActor* InCraneBridge,
    AActor* InCraneTrolley, AActor* InHoist, AActor* InHook, AActor* InReceivingSaddle,
    const TArray<AActor*>& InTrailerCoils, const FVector InLorryApproachPoint,
    const FVector InLorryDockPoint)
{
    if (SourceMode != ELBInboundDeliverySourceMode::LegacyLorry
        || !InLorry || !InCraneBridge || !InCraneTrolley || !InHoist || !InHook || !InReceivingSaddle
        || InTrailerCoils.Num() != 4 || InTrailerCoils.Contains(nullptr))
    {
        return false;
    }
    LorryActor = InLorry;
    CraneBridgeActor = InCraneBridge;
    CraneTrolleyActor = InCraneTrolley;
    HoistActor = InHoist;
    HookActor = InHook;
    ReceivingSaddleActor = InReceivingSaddle;
    TrailerCoilActors.Reset();
    TrailerCoilHomeTransforms.Reset();
    for (AActor* Coil : InTrailerCoils)
    {
        TrailerCoilActors.Add(Coil);
        TrailerCoilHomeTransforms.Add(Coil->GetActorTransform());
        Coil->SetActorHiddenInGame(false);
    }
    LorryApproachPoint = InLorryApproachPoint;
    LorryDockPoint = InLorryDockPoint;
    AuthoredLorryApproachPoint = InLorryApproachPoint;
    AuthoredLorryDockPoint = InLorryDockPoint;
    HookHomeLocation = HookActor->GetActorLocation();
    HoistHomeLocation = HoistActor->GetActorLocation();
    bLorryDocked = LorryActor->GetActorLocation().Equals(LorryDockPoint, 2.0f);
    bVisualSequenceBound = true;
    bPlayerBuiltComponentSequence = false;
    return true;
}

bool ALBInboundDeliveryController::ConfigurePlayerBuiltVisualSequence(ALBFactoryBuildMachine* InPlayerBuiltInboundDock)
{
    if (SourceMode != ELBInboundDeliverySourceMode::LegacyLorry
        || !InPlayerBuiltInboundDock
        || InPlayerBuiltInboundDock->GetMachineType() != ELBFactoryBuildMachineType::InboundDeliveryDock)
        return false;
    // Save-compatible component slots now present the crane-replacement coil-handler AGV.
    PlayerBridgeComponent = InPlayerBuiltInboundDock->GetInboundCoilHandlerMastComponent();
    PlayerHookComponent = InPlayerBuiltInboundDock->GetInboundCoilHandlerRamComponent();
    PlayerTrolleyComponent = InPlayerBuiltInboundDock->GetInboundCoilHandlerCarriageComponent();
    PlayerHoistComponent = InPlayerBuiltInboundDock->GetInboundCoilHandlerBackrestComponent();
    PlayerHandlerChassisComponent = InPlayerBuiltInboundDock->GetInboundCoilHandlerChassisComponent();
    PlayerTrailerCoilComponents.Reset();
    for (int32 Index = 0; Index < 4; ++Index)
        PlayerTrailerCoilComponents.Add(InPlayerBuiltInboundDock->GetTrailerCoilComponent(Index));
    if (!PlayerHandlerChassisComponent || !PlayerBridgeComponent || !PlayerTrolleyComponent
        || !PlayerHoistComponent || !PlayerHookComponent
        || PlayerTrailerCoilComponents.Contains(nullptr)) return false;
    InboundDock = InPlayerBuiltInboundDock;
    PlayerSaddleLoadPoint = InPlayerBuiltInboundDock->GetReceivingSaddleLoadPoint();
    HookHomeLocation = PlayerHookComponent->GetComponentLocation();
    HoistHomeLocation = PlayerHoistComponent->GetComponentLocation();
    TrailerCoilHomeTransforms.Reset();
    for (UStaticMeshComponent* Coil : PlayerTrailerCoilComponents)
        TrailerCoilHomeTransforms.Add(Coil->GetComponentTransform());
    bLorryDocked = true;
    bPlayerBuiltComponentSequence = true;
    bVisualSequenceBound = true;
    ResetCoilHandlerDriveState();
    return true;
}

FName ALBInboundDeliveryController::GetInboundDockId() const
{
    return InboundDock ? InboundDock->GetMachineId() : NAME_None;
}

FName ALBInboundDeliveryController::GetPR002MachineId() const
{
    return PR002Cell ? PR002Cell->GetMachineId() : NAME_None;
}

bool ALBInboundDeliveryController::HasRequiredLink() const
{
    return HasRequiredLink(InboundDock, PR002Cell);
}

bool ALBInboundDeliveryController::HasRequiredLink(
    ALBFactoryBuildMachine* CandidateInbound,
    ALBFactoryBuildMachine* CandidatePR002) const
{
    if (!GetWorld() || !CandidateInbound || !CandidatePR002) return false;
    for (TActorIterator<ALBFactoryTransportLink> It(GetWorld()); It; ++It)
    {
        const ALBFactoryTransportLink* Link = *It;
        if (Link && Link->GetSourcePort() && Link->GetTargetPort()
            && Link->GetSourcePort()->GetOwner() == CandidateInbound
            && Link->GetTargetPort()->GetOwner() == CandidatePR002)
        {
            return true;
        }
    }
    return false;
}

void ALBInboundDeliveryController::ClearLegacyVisualSequenceBinding()
{
    LorryActor = nullptr;
    CraneBridgeActor = nullptr;
    CraneTrolleyActor = nullptr;
    HoistActor = nullptr;
    HookActor = nullptr;
    ReceivingSaddleActor = nullptr;
    TrailerCoilActors.Reset();
    PlayerBridgeComponent = nullptr;
    PlayerTrolleyComponent = nullptr;
    PlayerHoistComponent = nullptr;
    PlayerHookComponent = nullptr;
    PlayerHandlerChassisComponent = nullptr;
    PlayerTrailerCoilComponents.Reset();
    TrailerCoilHomeTransforms.Reset();
    bVisualSequenceBound = false;
    bPlayerBuiltComponentSequence = false;
    bLorryDocked = false;
    ActiveVisualCoilIndex = INDEX_NONE;
}

bool ALBInboundDeliveryController::StartDelivery(const FName CoilId, FString& OutReason)
{
    OutReason.Reset();
    if (Phase != ELBInboundDeliveryPhase::Idle || CoilId.IsNone() || !InboundDock || !CoilAGV)
    {
        OutReason = TEXT("INBOUND DELIVERY AUTHORITY IS NOT IDLE OR IS NOT FULLY BOUND");
        return false;
    }
    if (SourceMode == ELBInboundDeliverySourceMode::NativeAGVArrival
        && !CoilAGV->IsUsingNativeOneFactoryPresentation())
    {
        OutReason = TEXT("NATIVE INBOUND DELIVERY LOST ITS EXACT PROCEDURAL AGV PRESENTATION");
        return false;
    }
    const FLBFactoryBuildMachineSaveState DockBefore = InboundDock->CaptureSaveState();
    if (!InboundDock->ReceiveDeliveredUnit(CoilId))
    {
        InboundDock->RestoreSaveState(DockBefore);
        OutReason = TEXT("THE IDENTIFIED COIL COULD NOT BE ACCEPTED AT THE INBOUND DOCK");
        return false;
    }
    ActiveCoilId = CoilId;
    if (bVisualSequenceBound)
    {
        const int32 VisualCount = bPlayerBuiltComponentSequence
            ? PlayerTrailerCoilComponents.Num() : TrailerCoilActors.Num();
        ActiveVisualCoilIndex = CompletedDeliveries % VisualCount;
        const bool bVisualAvailable = bPlayerBuiltComponentSequence
            ? PlayerTrailerCoilComponents.IsValidIndex(ActiveVisualCoilIndex)
                && PlayerTrailerCoilComponents[ActiveVisualCoilIndex]
                && PlayerTrailerCoilComponents[ActiveVisualCoilIndex]->IsVisible()
            : TrailerCoilActors.IsValidIndex(ActiveVisualCoilIndex)
                && TrailerCoilActors[ActiveVisualCoilIndex]
                && !TrailerCoilActors[ActiveVisualCoilIndex]->IsHidden();
        if (!bVisualAvailable)
        {
            InboundDock->RestoreSaveState(DockBefore);
            ActiveCoilId = NAME_None;
            OutReason = TEXT("THE NEXT TRAILER COIL IS NOT AVAILABLE FOR THE COIL-HANDLER AGV");
            return false;
        }
        EnterPhase(bLorryDocked ? ELBInboundDeliveryPhase::DockProving : ELBInboundDeliveryPhase::TruckReverse);
        LastReason = FString::Printf(TEXT("%s RESERVED; LORRY REVERSING TO THE PROTECTED UNLOAD BAY"), *CoilId.ToString());
        OutReason = LastReason;
        return true;
    }
    if (!HasWrappedCoilStorage() || !PR002Cell || !HasRequiredLink()
        || !PR002Cell->CanAcceptInputUnit())
    {
        EnterPhase(ELBInboundDeliveryPhase::WaitingForStorage);
        LastReason = FString::Printf(TEXT("%s IS SAFELY HELD; PLACE WRAPPED COIL STORAGE AND PR002"),
            *CoilId.ToString());
        OutReason = LastReason;
        return true;
    }
    FString DispatchReason;
    if (!DispatchFromSaddle(DispatchReason))
    {
        InboundDock->RestoreSaveState(DockBefore);
        ActiveCoilId = NAME_None;
        OutReason = DispatchReason;
        return false;
    }
    LastReason = DispatchReason;
    OutReason = LastReason;
    return true;
}

bool ALBInboundDeliveryController::HasWrappedCoilStorage() const
{
    if (!GetWorld()) return false;
    for (TActorIterator<ALBPressShopStorageZone> It(GetWorld()); It; ++It)
        if (IsValid(*It) && It->GetStorageType() == ELBPressShopStorageType::BareCoils
            && It->GetAvailableCapacity() > 0) return true;
    return false;
}

bool ALBInboundDeliveryController::DispatchFromSaddle(FString& OutReason)
{
    FName ReleasedId;
    if (!InboundDock || !CoilAGV || !InboundDock->ReleaseOutputUnit(ReleasedId)
        || ReleasedId != ActiveCoilId || !CoilAGV->ReloadAtStagedPoint(ActiveCoilId.ToString())
        || !CoilAGV->StartDispatch(ActiveCoilId.ToString()))
    {
        OutReason = TEXT("THE IDENTIFIED COIL COULD NOT BE SAFELY HANDED FROM THE SADDLE TO THE AGV");
        return false;
    }
    if (TrailerCoilActors.IsValidIndex(ActiveVisualCoilIndex) && TrailerCoilActors[ActiveVisualCoilIndex])
    {
        TrailerCoilActors[ActiveVisualCoilIndex]->SetActorHiddenInGame(true);
    }
    if (bPlayerBuiltComponentSequence && PlayerTrailerCoilComponents.IsValidIndex(ActiveVisualCoilIndex)
        && PlayerTrailerCoilComponents[ActiveVisualCoilIndex])
        PlayerTrailerCoilComponents[ActiveVisualCoilIndex]->SetVisibility(false);
    EnterPhase(ELBInboundDeliveryPhase::AGVDispatch);
    OutReason = SourceMode == ELBInboundDeliverySourceMode::NativeAGVArrival
        ? FString::Printf(TEXT("%s PROVED AT THE NATIVE ARRIVAL DOCK AND DISPATCHED BY AGV"),
            *ActiveCoilId.ToString())
        : FString::Printf(TEXT("%s PROVED ON THE RECEIVING SADDLE AND DISPATCHED BY AGV"),
            *ActiveCoilId.ToString());
    return true;
}

bool ALBInboundDeliveryController::CommitHandoff(FString& OutReason)
{
    const FLBFactoryBuildMachineSaveState PR002Before = PR002Cell->CaptureSaveState();
    ALBFactoryTransportLink* RequiredLink = nullptr;
    for (TActorIterator<ALBFactoryTransportLink> It(GetWorld()); It; ++It)
    {
        ALBFactoryTransportLink* Link = *It;
        if (Link && Link->GetSourcePort() && Link->GetTargetPort()
            && Link->GetSourcePort()->GetOwner() == InboundDock
            && Link->GetTargetPort()->GetOwner() == PR002Cell)
        {
            RequiredLink = Link;
            break;
        }
    }
    if (!RequiredLink || !PR002Cell->AcceptInputUnit(ActiveCoilId)
        || !RequiredLink->TryTransferUnits(1))
    {
        PR002Cell->RestoreSaveState(PR002Before);
        OutReason = TEXT("PR002 OR ITS AUTOMATIC HANDOFF LINK REJECTED THE DELIVERY");
        return false;
    }
    FString AGVCoilId;
    if (!CoilAGV->ConfirmHandoff(AGVCoilId) || FName(*AGVCoilId) != ActiveCoilId)
    {
        PR002Cell->RestoreSaveState(PR002Before);
        OutReason = TEXT("AGV HANDOFF IDENTITY DID NOT MATCH THE RESERVED COIL");
        return false;
    }
    ++CompletedDeliveries;
    OutReason = FString::Printf(TEXT("%s ACCEPTED BY PR002 AFTER PROVED AGV HANDOFF"), *ActiveCoilId.ToString());
    LastReason = OutReason;
    EnterPhase(ELBInboundDeliveryPhase::AGVReturn);
    return true;
}

void ALBInboundDeliveryController::Tick(const float DeltaSeconds)
{
    Super::Tick(DeltaSeconds);
    TickPlayerBuilderBootstrap(DeltaSeconds);
    if (Phase == ELBInboundDeliveryPhase::WaitingForStorage)
    {
        PhaseElapsedSeconds += DeltaSeconds;
        if (PhaseElapsedSeconds < PlayerBuilderBootstrapIntervalSeconds) return;
        PhaseElapsedSeconds = 0.0f;
        // Only the clean player-builder campaign is allowed to replace configured
        // endpoints/presentation while a coil is waiting.  An explicitly configured
        // authored unload sequence may use the same factory-machine tags, but it must
        // retain its lorry/crane actors across all four coils.  Unconditional discovery
        // changed that sequence into the modular coil-handler after its first unload and
        // left the second coil driving an unrelated, partially configured presentation.
        if (bPlayerBuilderBootstrapEnabled)
        {
            DiscoverPlayerBuilderEndpoints();
        }
        if (!HasWrappedCoilStorage())
        {
            LastReason = FString::Printf(TEXT("%s IS SAFELY HELD; PLACE WRAPPED COIL STORAGE"),
                *ActiveCoilId.ToString());
            return;
        }
        if (!PR002Cell || !HasRequiredLink() || !PR002Cell->CanAcceptInputUnit())
        {
            LastReason = FString::Printf(TEXT("%s IS SAFELY HELD; PLACE OR CLEAR PR002"),
                *ActiveCoilId.ToString());
            return;
        }
        FString Reason;
        if (!DispatchFromSaddle(Reason)) LatchFault(Reason); else LastReason = Reason;
        return;
    }
    if (!IsValid(CoilAGV) || Phase == ELBInboundDeliveryPhase::Idle
        || Phase == ELBInboundDeliveryPhase::Fault) return;
    PhaseElapsedSeconds += DeltaSeconds;
    if (bPlayerBuiltComponentSequence && Phase >= ELBInboundDeliveryPhase::TruckReverse)
    {
        TickPlayerBuiltVisualSequence(DeltaSeconds);
        return;
    }
    AActor* ActiveCoil = TrailerCoilActors.IsValidIndex(ActiveVisualCoilIndex)
        ? TrailerCoilActors[ActiveVisualCoilIndex].Get() : nullptr;
    if (bVisualSequenceBound && Phase >= ELBInboundDeliveryPhase::TruckReverse)
    {
        if (!LorryActor || !CraneBridgeActor || !CraneTrolleyActor || !HoistActor || !HookActor
            || !ReceivingSaddleActor || !ActiveCoil)
        {
            LatchFault(TEXT("INBOUND UNLOAD VISUAL BINDING WAS LOST"));
            return;
        }
        const FVector CoilHome = TrailerCoilHomeTransforms[ActiveVisualCoilIndex].GetLocation();
        const FVector Saddle = ReceivingSaddleActor->GetActorLocation();
        const FVector CoilClear(CoilHome.X, CoilHome.Y, FMath::Max(CoilHome.Z, Saddle.Z) + LiftClearanceCm);
        const FVector SaddleClear(Saddle.X, Saddle.Y, CoilClear.Z);
        if (Phase == ELBInboundDeliveryPhase::TruckReverse)
        {
            const FVector Before = LorryActor->GetActorLocation();
            const bool bDocked = MoveActorTo(LorryActor, LorryDockPoint, LorryReverseSpeedCmPerSecond, DeltaSeconds);
            const FVector TrailerDelta = LorryActor->GetActorLocation() - Before;
            if (!TrailerDelta.IsNearlyZero())
            {
                for (int32 Index = 0; Index < TrailerCoilActors.Num(); ++Index)
                {
                    if (TrailerCoilActors[Index] && !TrailerCoilActors[Index]->IsHidden())
                    {
                        TrailerCoilActors[Index]->AddActorWorldOffset(TrailerDelta, false, nullptr, ETeleportType::TeleportPhysics);
                        TrailerCoilHomeTransforms[Index].AddToTranslation(TrailerDelta);
                    }
                }
            }
            if (bDocked)
            {
                bLorryDocked = true;
                EnterPhase(ELBInboundDeliveryPhase::DockProving);
            }
            return;
        }
        if (Phase == ELBInboundDeliveryPhase::DockProving)
        {
            if (PhaseElapsedSeconds >= DockProveSeconds) EnterPhase(ELBInboundDeliveryPhase::CraneToCoil);
            return;
        }
        if (Phase == ELBInboundDeliveryPhase::CraneToCoil)
        {
            const FVector HookTarget(CoilHome.X, CoilHome.Y, HookHomeLocation.Z);
            const FVector Delta = HookTarget - HookActor->GetActorLocation();
            const bool bHookReady = MoveActorTo(HookActor, HookTarget, CraneTravelSpeedCmPerSecond, DeltaSeconds);
            MoveActorTo(HoistActor, HoistActor->GetActorLocation() + FVector(Delta.X, Delta.Y, 0.0f), CraneTravelSpeedCmPerSecond, DeltaSeconds);
            MoveActorTo(CraneTrolleyActor, CraneTrolleyActor->GetActorLocation() + FVector(Delta.X, Delta.Y, 0.0f), CraneTravelSpeedCmPerSecond, DeltaSeconds);
            if (bHookReady) EnterPhase(ELBInboundDeliveryPhase::HookLower);
            return;
        }
        if (Phase == ELBInboundDeliveryPhase::HookLower)
        {
            const FVector Target(CoilHome.X, CoilHome.Y, CoilHome.Z);
            if (MoveActorTo(HookActor, Target, HookTravelSpeedCmPerSecond, DeltaSeconds)) EnterPhase(ELBInboundDeliveryPhase::HookEngage);
            return;
        }
        if (Phase == ELBInboundDeliveryPhase::HookEngage)
        {
            ApplyCarriedCoilPose(HookActor->GetActorLocation());
            if (PhaseElapsedSeconds >= HookEngageSeconds) EnterPhase(ELBInboundDeliveryPhase::CoilLift);
            return;
        }
        if (Phase == ELBInboundDeliveryPhase::CoilLift)
        {
            const bool bReady = MoveActorTo(HookActor, CoilClear, HookTravelSpeedCmPerSecond, DeltaSeconds);
            ApplyCarriedCoilPose(HookActor->GetActorLocation());
            if (bReady) EnterPhase(ELBInboundDeliveryPhase::CraneToSaddle);
            return;
        }
        if (Phase == ELBInboundDeliveryPhase::CraneToSaddle)
        {
            const bool bReady = MoveActorTo(HookActor, SaddleClear, CraneTravelSpeedCmPerSecond, DeltaSeconds);
            ApplyCarriedCoilPose(HookActor->GetActorLocation());
            if (bReady) EnterPhase(ELBInboundDeliveryPhase::CoilLower);
            return;
        }
        if (Phase == ELBInboundDeliveryPhase::CoilLower)
        {
            const bool bReady = MoveActorTo(HookActor, Saddle, HookTravelSpeedCmPerSecond, DeltaSeconds);
            ApplyCarriedCoilPose(HookActor->GetActorLocation());
            if (bReady) EnterPhase(ELBInboundDeliveryPhase::SaddleRelease);
            return;
        }
        if (Phase == ELBInboundDeliveryPhase::SaddleRelease)
        {
            ApplyCarriedCoilPose(Saddle);
            if (PhaseElapsedSeconds >= SaddleReleaseSeconds)
            {
                EnterPhase(ELBInboundDeliveryPhase::WaitingForStorage);
                LastReason = FString::Printf(TEXT("%s UNLOADED AND HELD; WAITING FOR WRAPPED COIL STORAGE"),
                    *ActiveCoilId.ToString());
            }
            return;
        }
    }
    if (CoilAGV->GetPhase() == ELBCoilAGVPhase::Fault)
    {
        LatchFault(TEXT("COIL AGV FAULTED DURING INBOUND DELIVERY"));
        return;
    }
    if (Phase == ELBInboundDeliveryPhase::AGVDispatch && CoilAGV->IsHandoffReady())
    {
        LastReason = FString::Printf(TEXT("%s ALIGNED; AGV HANDOFF PROVING"), *ActiveCoilId.ToString());
        EnterPhase(ELBInboundDeliveryPhase::AGVHandoff);
    }
    else if (Phase == ELBInboundDeliveryPhase::AGVHandoff)
    {
        if (!CoilAGV->IsHandoffReady())
        {
            LatchFault(TEXT("AGV LEFT THE PROVED HANDOFF POSITION BEFORE IDENTITY TRANSFER"));
        }
        else if (PhaseElapsedSeconds >= AGVHandoffSeconds)
        {
            FString Reason;
            if (!CommitHandoff(Reason)) LatchFault(Reason);
        }
    }
    else if (Phase == ELBInboundDeliveryPhase::AGVReturn && CoilAGV->IsAwaitingReload())
    {
        ActiveCoilId = NAME_None;
        ActiveVisualCoilIndex = INDEX_NONE;
        LastReason = TEXT("INBOUND AGV RETURNED AND IS READY FOR THE NEXT COIL");
        EnterPhase(ELBInboundDeliveryPhase::Idle);
    }
}

bool ALBInboundDeliveryController::MoveActorTo(AActor* Actor, const FVector& Target,
    const float Speed, const float DeltaSeconds)
{
    if (!Actor) return false;
    const FVector Next = FMath::VInterpConstantTo(Actor->GetActorLocation(), Target, DeltaSeconds, Speed);
    Actor->SetActorLocation(Next, false, nullptr, ETeleportType::TeleportPhysics);
    return Next.Equals(Target, 1.0f);
}

bool ALBInboundDeliveryController::MoveComponentTo(USceneComponent* Component, const FVector& Target,
    const float Speed, const float DeltaSeconds)
{
    if (!Component) return false;
    const FVector Next = FMath::VInterpConstantTo(Component->GetComponentLocation(), Target, DeltaSeconds, Speed);
    Component->SetWorldLocation(Next, false, nullptr, ETeleportType::TeleportPhysics);
    return Next.Equals(Target, 1.0f);
}

float ALBInboundDeliveryController::CalculateCoilHandlerRearSteerAngleDegrees(
    const float SignedTravelSpeedCmPerSecond,
    const float DesiredBodyYawRateDegreesPerSecond) const
{
    const float DirectionSign = SignedTravelSpeedCmPerSecond < 0.0f ? -1.0f : 1.0f;
    const float EffectiveSignedSpeed = DirectionSign
        * FMath::Max(FMath::Abs(SignedTravelSpeedCmPerSecond), 20.0f);
    const float DesiredYawRateRadians = FMath::DegreesToRadians(
        DesiredBodyYawRateDegreesPerSecond);
    // Rear-steered bicycle model: positive forward speed needs opposite rear-wheel
    // lock to create the requested body yaw; reversing changes that command's sign.
    const float RearSteerRadians = FMath::Atan(
        -CoilHandlerWheelbaseCm * DesiredYawRateRadians / EffectiveSignedSpeed);
    return FMath::Clamp(FMath::RadiansToDegrees(RearSteerRadians),
        -CoilHandlerMaximumRearSteerAngleDegrees,
        CoilHandlerMaximumRearSteerAngleDegrees);
}

float ALBInboundDeliveryController::GetCoilHandlerSweptClearanceRadiusCm() const
{
    const float LoadedFootprintRadius = FVector2D(
        CoilHandlerLoadedHalfLengthCm, CoilHandlerLoadedHalfWidthCm).Size();
    const float RearCounterweightSwing = CoilHandlerRearCounterweightOverhangCm
        * FMath::Sin(FMath::DegreesToRadians(
            CoilHandlerMaximumRearSteerAngleDegrees));
    return LoadedFootprintRadius + RearCounterweightSwing
        + CoilHandlerSteeringSweepMarginCm;
}

bool ALBInboundDeliveryController::IsCoilHandlerSweptPathClear(
    const FVector Start, const FVector End) const
{
    if (!GetWorld()) return false;
    const float SweepRadiusCm = GetCoilHandlerSweptClearanceRadiusCm();
    for (TActorIterator<ALBFactoryBuildMachine> It(GetWorld()); It; ++It)
    {
        const ALBFactoryBuildMachine* Machine = *It;
        if (!IsValid(Machine) || Machine->GetMachineId().IsNone()
            || Machine == InboundDock || Machine == PR002Cell)
        {
            continue;
        }
        if (SegmentIntersectsExpandedMachineEnvelope(Start, End, *Machine,
            SweepRadiusCm, CoilHandlerProtectedEnvelopeClearanceCm))
        {
            return false;
        }
    }
    return true;
}

void ALBInboundDeliveryController::ApplyRigidCoilHandlerPose(
    const FTransform& NewChassisTransform)
{
    if (!PlayerHandlerChassisComponent) return;
    const FTransform PriorChassisTransform =
        PlayerHandlerChassisComponent->GetComponentTransform();
    const FTransform BridgeRelative = PlayerBridgeComponent
        ? PlayerBridgeComponent->GetComponentTransform().GetRelativeTransform(
            PriorChassisTransform) : FTransform::Identity;
    const FTransform TrolleyRelative = PlayerTrolleyComponent
        ? PlayerTrolleyComponent->GetComponentTransform().GetRelativeTransform(
            PriorChassisTransform) : FTransform::Identity;
    const FTransform HoistRelative = PlayerHoistComponent
        ? PlayerHoistComponent->GetComponentTransform().GetRelativeTransform(
            PriorChassisTransform) : FTransform::Identity;
    const FTransform HookRelative = PlayerHookComponent
        ? PlayerHookComponent->GetComponentTransform().GetRelativeTransform(
            PriorChassisTransform) : FTransform::Identity;

    PlayerHandlerChassisComponent->SetWorldTransform(NewChassisTransform,
        false, nullptr, ETeleportType::TeleportPhysics);
    const auto ApplyRelative = [&NewChassisTransform](USceneComponent* Component,
        const FTransform& RelativeTransform)
    {
        if (Component)
            Component->SetWorldTransform(RelativeTransform * NewChassisTransform,
                false, nullptr, ETeleportType::TeleportPhysics);
    };
    ApplyRelative(PlayerBridgeComponent, BridgeRelative);
    ApplyRelative(PlayerTrolleyComponent, TrolleyRelative);
    ApplyRelative(PlayerHoistComponent, HoistRelative);
    ApplyRelative(PlayerHookComponent, HookRelative);
    if (InboundDock)
        InboundDock->SetInboundCoilHandlerRearSteerAngleDegrees(
            CoilHandlerRearSteerAngleDegrees);
}

void ALBInboundDeliveryController::ResetCoilHandlerDriveState(
    const bool bStraightenRearWheels)
{
    CoilHandlerTravelSpeedCmPerSecond = 0.0f;
    bCoilHandlerDriveCommandActive = false;
    bCoilHandlerDrivingInReverse = false;
    CoilHandlerActiveRamTarget = FVector::ZeroVector;
    CoilHandlerPathStart = FVector::ZeroVector;
    CoilHandlerPathControlA = FVector::ZeroVector;
    CoilHandlerPathControlB = FVector::ZeroVector;
    CoilHandlerPathEnd = FVector::ZeroVector;
    CoilHandlerPathAlpha = 0.0f;
    CoilHandlerPathMaximumCurvature = 0.0f;
    bCoilHandlerPathAtDestination = false;
    if (bStraightenRearWheels)
    {
        CoilHandlerRearSteerAngleDegrees = 0.0f;
        if (InboundDock)
            InboundDock->SetInboundCoilHandlerRearSteerAngleDegrees(0.0f);
    }
}

bool ALBInboundDeliveryController::DrivePlayerBuiltCoilHandlerToRamTarget(
    const FVector& RamTarget, const float MaximumSpeedCmPerSecond,
    const float DeltaSeconds)
{
    if (!PlayerHandlerChassisComponent || !PlayerHookComponent
        || DeltaSeconds <= 0.0f || MaximumSpeedCmPerSecond <= 0.0f)
    {
        return false;
    }

    const FTransform ChassisTransform =
        PlayerHandlerChassisComponent->GetComponentTransform();

    // At the destination the chassis is stopped while the rear wheels smoothly return
    // to centre. Wheel steering without body yaw is valid; a stationary body pivot is not.
    if (bCoilHandlerPathAtDestination)
    {
        CoilHandlerRearSteerAngleDegrees = FMath::FInterpConstantTo(
            CoilHandlerRearSteerAngleDegrees, 0.0f, DeltaSeconds,
            CoilHandlerRearSteerRateDegreesPerSecond);
        if (InboundDock)
            InboundDock->SetInboundCoilHandlerRearSteerAngleDegrees(
                CoilHandlerRearSteerAngleDegrees);
        if (FMath::IsNearlyZero(CoilHandlerRearSteerAngleDegrees, 0.05f))
        {
            CoilHandlerRearSteerAngleDegrees = 0.0f;
            ResetCoilHandlerDriveState(false);
            return true;
        }
        return false;
    }

    if (!bCoilHandlerDriveCommandActive)
    {
        const FVector RamLocation = PlayerHookComponent->GetComponentLocation();
        const FVector ToRamTarget(RamTarget.X - RamLocation.X,
            RamTarget.Y - RamLocation.Y, 0.0f);
        if (ToRamTarget.Size2D() <= 1.0f)
        {
            ResetCoilHandlerDriveState();
            return true;
        }

        const FVector DesiredTravelDirection = ToRamTarget.GetSafeNormal2D();
        // CHF01's mast/load face is local -X; local +X is its rear counterweight.
        const FVector CurrentFrontDirection =
            -ChassisTransform.GetUnitAxis(EAxis::X).GetSafeNormal2D();
        bCoilHandlerDrivingInReverse = FVector::DotProduct(
            CurrentFrontDirection, DesiredTravelDirection) < 0.0f;
        const FVector StartTravelDirection = bCoilHandlerDrivingInReverse
            ? -CurrentFrontDirection : CurrentFrontDirection;
        const float LongitudinalDistance = FVector::DotProduct(
            ToRamTarget, StartTravelDirection);
        if (LongitudinalDistance <= 2.0f)
        {
            LatchFault(TEXT("COIL HANDLER NEEDS MORE RUN-UP SPACE FOR A REAR-STEER TURN"));
            return false;
        }

        bCoilHandlerDriveCommandActive = true;
        CoilHandlerActiveRamTarget = RamTarget;
        CoilHandlerPathStart = ChassisTransform.GetLocation();
        CoilHandlerPathEnd = CoilHandlerPathStart + ToRamTarget;
        CoilHandlerPathAlpha = 0.0f;
        CoilHandlerPathMaximumCurvature = 0.0f;

        // The handler must finish square to the bore/saddle. A symmetric cubic lane-change
        // gives it a continuous S-curve: rear lock crosses through zero naturally, the body
        // never pivots, and the 3.015 m ram datum returns to its exact target orientation.
        float BestMaximumCurvature = BIG_NUMBER;
        FVector BestControlA = CoilHandlerPathStart;
        FVector BestControlB = CoilHandlerPathEnd;
        constexpr int32 HandleCandidates = 40;
        for (int32 CandidateIndex = 0; CandidateIndex <= HandleCandidates; ++CandidateIndex)
        {
            const float HandleAlpha = static_cast<float>(CandidateIndex)
                / static_cast<float>(HandleCandidates);
            const float HandleLength = FMath::Lerp(
                FMath::Max(5.0f, LongitudinalDistance * 0.08f),
                LongitudinalDistance * 0.98f, HandleAlpha);
            const FVector CandidateControlA = CoilHandlerPathStart
                + StartTravelDirection * HandleLength;
            const FVector CandidateControlB = CoilHandlerPathEnd
                - StartTravelDirection * HandleLength;
            float CandidateMaximumCurvature = 0.0f;
            bool bCandidateMovesForward = true;
            for (int32 Sample = 0; Sample <= 40; ++Sample)
            {
                const float Alpha = static_cast<float>(Sample) / 40.0f;
                const FVector Derivative = EvaluateCubicPathDerivative(
                    CoilHandlerPathStart, CandidateControlA, CandidateControlB,
                    CoilHandlerPathEnd, Alpha);
                bCandidateMovesForward &= FVector::DotProduct(
                    Derivative, StartTravelDirection) > 0.1f;
                CandidateMaximumCurvature = FMath::Max(CandidateMaximumCurvature,
                    FMath::Abs(EvaluateCubicPathCurvature(CoilHandlerPathStart,
                        CandidateControlA, CandidateControlB, CoilHandlerPathEnd, Alpha)));
            }
            if (bCandidateMovesForward
                && CandidateMaximumCurvature < BestMaximumCurvature)
            {
                BestMaximumCurvature = CandidateMaximumCurvature;
                BestControlA = CandidateControlA;
                BestControlB = CandidateControlB;
            }
        }
        const float MaximumKinematicCurvature = FMath::Tan(FMath::DegreesToRadians(
            CoilHandlerMaximumRearSteerAngleDegrees))
            / FMath::Max(CoilHandlerWheelbaseCm, 1.0f);
        if (!FMath::IsFinite(BestMaximumCurvature)
            || BestMaximumCurvature > MaximumKinematicCurvature * 1.01f)
        {
            ResetCoilHandlerDriveState();
            LatchFault(TEXT("COIL HANDLER REAR-STEER TURNING RADIUS IS TOO TIGHT FOR THIS APPROACH"));
            return false;
        }
        CoilHandlerPathControlA = BestControlA;
        CoilHandlerPathControlB = BestControlB;
        CoilHandlerPathMaximumCurvature = BestMaximumCurvature;
    }

    const float StartCurvature = EvaluateCubicPathCurvature(CoilHandlerPathStart,
        CoilHandlerPathControlA, CoilHandlerPathControlB, CoilHandlerPathEnd,
        CoilHandlerPathAlpha);
    const float NominalSignedSpeed = bCoilHandlerDrivingInReverse ? -100.0f : 100.0f;
    const float DesiredBodyYawRateDegrees = FMath::RadiansToDegrees(
        100.0f * StartCurvature);
    const float TargetRearSteerAngle = CalculateCoilHandlerRearSteerAngleDegrees(
        NominalSignedSpeed, DesiredBodyYawRateDegrees);
    CoilHandlerRearSteerAngleDegrees = FMath::FInterpConstantTo(
        CoilHandlerRearSteerAngleDegrees, TargetRearSteerAngle, DeltaSeconds,
        CoilHandlerRearSteerRateDegreesPerSecond);
    if (InboundDock)
        InboundDock->SetInboundCoilHandlerRearSteerAngleDegrees(
            CoilHandlerRearSteerAngleDegrees);

    // Pre-steer the rear axle before rolling, just as the real rear-steered handler does.
    if (CoilHandlerPathAlpha <= KINDA_SMALL_NUMBER
        && !FMath::IsNearlyEqual(CoilHandlerRearSteerAngleDegrees,
            TargetRearSteerAngle, 0.25f))
    {
        return false;
    }

    const float RemainingPathLength = ApproximateCubicPathLength(
        CoilHandlerPathStart, CoilHandlerPathControlA, CoilHandlerPathControlB,
        CoilHandlerPathEnd, CoilHandlerPathAlpha, 1.0f, 24);
    const float BrakingLimitedSpeed = FMath::Sqrt(FMath::Max(0.0f,
        2.0f * CoilHandlerDecelerationCmPerSecondSquared * RemainingPathLength));
    const float CurvatureLimitedSpeed = CoilHandlerPathMaximumCurvature > KINDA_SMALL_NUMBER
        ? FMath::DegreesToRadians(CoilHandlerMaximumYawRateDegreesPerSecond)
            / CoilHandlerPathMaximumCurvature
        : MaximumSpeedCmPerSecond;
    const float DesiredSpeed = FMath::Min3(MaximumSpeedCmPerSecond,
        BrakingLimitedSpeed, CurvatureLimitedSpeed);
    const float SpeedRate = DesiredSpeed >= CoilHandlerTravelSpeedCmPerSecond
        ? CoilHandlerAccelerationCmPerSecondSquared
        : CoilHandlerDecelerationCmPerSecondSquared;
    CoilHandlerTravelSpeedCmPerSecond = FMath::FInterpConstantTo(
        CoilHandlerTravelSpeedCmPerSecond, DesiredSpeed, DeltaSeconds, SpeedRate);
    const float TravelBudgetCm = CoilHandlerTravelSpeedCmPerSecond * DeltaSeconds;

    float NextAlpha = 1.0f;
    if (TravelBudgetCm < RemainingPathLength)
    {
        float LowerAlpha = CoilHandlerPathAlpha;
        float UpperAlpha = 1.0f;
        for (int32 Iteration = 0; Iteration < 10; ++Iteration)
        {
            const float CandidateAlpha = (LowerAlpha + UpperAlpha) * 0.5f;
            const float CandidateLength = ApproximateCubicPathLength(
                CoilHandlerPathStart, CoilHandlerPathControlA,
                CoilHandlerPathControlB, CoilHandlerPathEnd,
                CoilHandlerPathAlpha, CandidateAlpha, 6);
            if (CandidateLength <= TravelBudgetCm) LowerAlpha = CandidateAlpha;
            else UpperAlpha = CandidateAlpha;
        }
        NextAlpha = LowerAlpha;
    }

    const FVector CandidateLocation = EvaluateCubicPath(CoilHandlerPathStart,
        CoilHandlerPathControlA, CoilHandlerPathControlB, CoilHandlerPathEnd,
        NextAlpha);
    if (!IsCoilHandlerSweptPathClear(ChassisTransform.GetLocation(), CandidateLocation))
    {
        CoilHandlerTravelSpeedCmPerSecond = 0.0f;
        LatchFault(TEXT("COIL HANDLER SWEPT COUNTERWEIGHT/LOAD ENVELOPE IS OBSTRUCTED"));
        return false;
    }
    const FVector PathTangent = EvaluateCubicPathDerivative(CoilHandlerPathStart,
        CoilHandlerPathControlA, CoilHandlerPathControlB, CoilHandlerPathEnd,
        NextAlpha).GetSafeNormal2D();
    FRotator NewRotation = ChassisTransform.Rotator();
    NewRotation.Yaw = FMath::UnwindDegrees(PathTangent.Rotation().Yaw
        + (bCoilHandlerDrivingInReverse ? 0.0f : 180.0f));
    FTransform CandidateTransform = ChassisTransform;
    CandidateTransform.SetRotation(NewRotation.Quaternion());
    CandidateTransform.SetLocation(CandidateLocation);
    ApplyRigidCoilHandlerPose(CandidateTransform);
    CoilHandlerPathAlpha = NextAlpha;
    if (NextAlpha >= 1.0f - KINDA_SMALL_NUMBER)
    {
        CoilHandlerTravelSpeedCmPerSecond = 0.0f;
        bCoilHandlerPathAtDestination = true;
    }
    return false;
}

void ALBInboundDeliveryController::TickPlayerBuiltVisualSequence(const float DeltaSeconds)
{
    if (!PlayerTrailerCoilComponents.IsValidIndex(ActiveVisualCoilIndex)
        || !PlayerTrailerCoilComponents[ActiveVisualCoilIndex] || !PlayerHookComponent
        || !PlayerHoistComponent || !PlayerTrolleyComponent || !PlayerBridgeComponent
        || !PlayerHandlerChassisComponent)
    {
        LatchFault(TEXT("PLAYER-BUILT INBOUND UNLOAD VISUAL BINDING WAS LOST"));
        return;
    }
    UStaticMeshComponent* ActiveCoil = PlayerTrailerCoilComponents[ActiveVisualCoilIndex];
    const FVector CoilPivotHome = TrailerCoilHomeTransforms[ActiveVisualCoilIndex].GetLocation();
    const FVector CoilBoreOffset = ActiveCoil->GetComponentQuat().RotateVector(
        ActiveCoil->GetStaticMesh()->GetBounds().Origin);
    const FVector CoilBoreHome = CoilPivotHome + CoilBoreOffset;
    const FVector SaddleBoreCentre = PlayerSaddleLoadPoint + CoilBoreOffset;
    const FVector RamLoadOffset = PlayerHookComponent->GetComponentQuat().RotateVector(
        HandlerRamDatumToLoadCentreCm);
    const FVector CoilBoreClear(CoilBoreHome.X, CoilBoreHome.Y,
        FMath::Max(CoilBoreHome.Z, SaddleBoreCentre.Z) + LiftClearanceCm);
    const FVector SaddleBoreClear(SaddleBoreCentre.X, SaddleBoreCentre.Y, CoilBoreClear.Z);
    const FVector RamAtCoil = CoilBoreHome - RamLoadOffset;
    const FVector RamAtCoilClear = CoilBoreClear - RamLoadOffset;
    const FVector RamAtSaddleClear = SaddleBoreClear - RamLoadOffset;
    const FVector RamAtSaddle = SaddleBoreCentre - RamLoadOffset;
    const auto MoveHandlerFromRam = [this, DeltaSeconds](const FVector& RamTarget,
        const float Speed, const bool bDriveVehicleRoot)
    {
        if (bDriveVehicleRoot)
        {
            return DrivePlayerBuiltCoilHandlerToRamTarget(
                RamTarget, Speed, DeltaSeconds);
        }
        const FVector Before = PlayerHookComponent->GetComponentLocation();
        // Floor travel is handled above as a rear-steered rigid vehicle. These remaining
        // phases are vertical mast articulation only: the chassis and fixed mast stay down.
        const FVector EffectiveTarget(Before.X, Before.Y, RamTarget.Z);
        const bool bReady = MoveComponentTo(PlayerHookComponent, EffectiveTarget, Speed, DeltaSeconds);
        const FVector Delta = PlayerHookComponent->GetComponentLocation() - Before;
        if (!Delta.IsNearlyZero())
        {
            PlayerTrolleyComponent->AddWorldOffset(Delta, false, nullptr, ETeleportType::TeleportPhysics);
            PlayerHoistComponent->AddWorldOffset(Delta, false, nullptr, ETeleportType::TeleportPhysics);
        }
        return bReady;
    };
    if (Phase == ELBInboundDeliveryPhase::TruckReverse) { EnterPhase(ELBInboundDeliveryPhase::DockProving); return; }
    if (Phase == ELBInboundDeliveryPhase::DockProving)
    {
        if (PhaseElapsedSeconds >= DockProveSeconds) EnterPhase(ELBInboundDeliveryPhase::CraneToCoil);
        return;
    }
    if (Phase == ELBInboundDeliveryPhase::CraneToCoil)
    {
        const FVector RamTarget(RamAtCoil.X, RamAtCoil.Y, PlayerHookComponent->GetComponentLocation().Z);
        // Approach on the floor with the complete driverless handler. The subsequent insert
        // and lift phases remain local mast articulation, so the chassis never enters the
        // trailer envelope and the lift assembly never travels without its vehicle.
        const bool bReady = MoveHandlerFromRam(RamTarget, CraneTravelSpeedCmPerSecond, true);
        if (bReady) EnterPhase(ELBInboundDeliveryPhase::HookLower);
        return;
    }
    if (Phase == ELBInboundDeliveryPhase::HookLower)
    {
        if (MoveHandlerFromRam(RamAtCoil, HookTravelSpeedCmPerSecond, false))
            EnterPhase(ELBInboundDeliveryPhase::HookEngage);
        return;
    }
    if (Phase == ELBInboundDeliveryPhase::HookEngage)
    {
        ApplyCarriedCoilPose(PlayerHookComponent->GetComponentLocation());
        if (PhaseElapsedSeconds >= HookEngageSeconds) EnterPhase(ELBInboundDeliveryPhase::CoilLift);
        return;
    }
    if (Phase == ELBInboundDeliveryPhase::CoilLift)
    {
        const bool bReady = MoveHandlerFromRam(RamAtCoilClear, HookTravelSpeedCmPerSecond, false);
        ApplyCarriedCoilPose(PlayerHookComponent->GetComponentLocation());
        if (bReady) EnterPhase(ELBInboundDeliveryPhase::CraneToSaddle);
        return;
    }
    if (Phase == ELBInboundDeliveryPhase::CraneToSaddle)
    {
        // Carry the raised coil to the same-side saddle with the complete vehicle root.
        // The handler stays outside the trailer because its ram remains on the trailer side;
        // only the following lower phase articulates vertically.
        const bool bReady = MoveHandlerFromRam(RamAtSaddleClear, CraneTravelSpeedCmPerSecond, true);
        ApplyCarriedCoilPose(PlayerHookComponent->GetComponentLocation());
        if (bReady) EnterPhase(ELBInboundDeliveryPhase::CoilLower);
        return;
    }
    if (Phase == ELBInboundDeliveryPhase::CoilLower)
    {
        const bool bReady = MoveHandlerFromRam(RamAtSaddle, HookTravelSpeedCmPerSecond, false);
        ApplyCarriedCoilPose(PlayerHookComponent->GetComponentLocation());
        if (bReady) EnterPhase(ELBInboundDeliveryPhase::SaddleRelease);
        return;
    }
    if (Phase == ELBInboundDeliveryPhase::SaddleRelease)
    {
        // Release the load from the ram and seat its bottom-pivot directly on the V-block.
        ActiveCoil->SetWorldLocation(PlayerSaddleLoadPoint,
            false, nullptr, ETeleportType::TeleportPhysics);
        if (PhaseElapsedSeconds >= SaddleReleaseSeconds)
        {
            EnterPhase(ELBInboundDeliveryPhase::WaitingForStorage);
            LastReason = FString::Printf(TEXT("%s UNLOADED AND HELD; WAITING FOR WRAPPED COIL STORAGE"),
                *ActiveCoilId.ToString());
        }
    }
}

void ALBInboundDeliveryController::ApplyCarriedCoilPose(const FVector& Location)
{
    if (bPlayerBuiltComponentSequence && PlayerTrailerCoilComponents.IsValidIndex(ActiveVisualCoilIndex)
        && PlayerTrailerCoilComponents[ActiveVisualCoilIndex])
    {
        UStaticMeshComponent* Coil = PlayerTrailerCoilComponents[ActiveVisualCoilIndex];
        if (!PlayerHookComponent || !Coil->GetStaticMesh()) return;
        const FVector HookLoadCentre = Location + PlayerHookComponent->GetComponentQuat().RotateVector(
            HandlerRamDatumToLoadCentreCm);
        const FVector CoilBoreOffset = Coil->GetComponentQuat().RotateVector(
            Coil->GetStaticMesh()->GetBounds().Origin);
        Coil->SetWorldLocation(HookLoadCentre - CoilBoreOffset,
            false, nullptr, ETeleportType::TeleportPhysics);
        return;
    }
    if (TrailerCoilActors.IsValidIndex(ActiveVisualCoilIndex) && TrailerCoilActors[ActiveVisualCoilIndex])
    {
        TrailerCoilActors[ActiveVisualCoilIndex]->SetActorLocation(Location, false, nullptr, ETeleportType::TeleportPhysics);
    }
}

void ALBInboundDeliveryController::EnterPhase(const ELBInboundDeliveryPhase NewPhase)
{
    Phase = NewPhase;
    PhaseElapsedSeconds = 0.0f;
}

void ALBInboundDeliveryController::LatchFault(const FString& Reason)
{
    LastReason = Reason;
    EnterPhase(ELBInboundDeliveryPhase::Fault);
}

bool ALBInboundDeliveryController::ResetFault(const FName RecoveryEvidenceId, FString& OutReason)
{
    if (Phase != ELBInboundDeliveryPhase::Fault || RecoveryEvidenceId.IsNone() || !CoilAGV)
    {
        OutReason = TEXT("NAMED RECOVERY EVIDENCE AND A BOUND AGV ARE REQUIRED");
        return false;
    }
    if (CoilAGV->GetPhase() == ELBCoilAGVPhase::Fault && !CoilAGV->ResetFault(RecoveryEvidenceId))
    {
        OutReason = TEXT("THE COIL AGV SAFETY INTERLOCK STILL REJECTS RECOVERY");
        return false;
    }
    EnterPhase(CoilAGV->IsHandoffReady() ? ELBInboundDeliveryPhase::AGVHandoff : ELBInboundDeliveryPhase::AGVDispatch);
    OutReason = TEXT("INBOUND DELIVERY RECOVERY ACCEPTED");
    LastReason = OutReason;
    return true;
}

FLBInboundDeliverySaveState ALBInboundDeliveryController::CaptureSaveState() const
{
    FLBInboundDeliverySaveState State;
    State.SourceMode = SourceMode;
    State.Phase = Phase;
    State.InboundDockId = GetInboundDockId();
    State.CoilStoreId = GetPR002MachineId(); // legacy alias for v1/v2 readers
    State.PR002MachineId = GetPR002MachineId();
    State.ActiveCoilId = ActiveCoilId;
    State.LastReason = LastReason;
    State.CompletedDeliveries = CompletedDeliveries;
    State.PhaseElapsedSeconds = PhaseElapsedSeconds;
    State.ActiveVisualCoilIndex = ActiveVisualCoilIndex;
    State.bLorryDocked = bLorryDocked;
    if (LorryActor) State.LorryTransform = LorryActor->GetActorTransform();
    else if (InboundDock) State.LorryTransform = InboundDock->GetActorTransform();
    if (TrailerCoilActors.IsValidIndex(ActiveVisualCoilIndex) && TrailerCoilActors[ActiveVisualCoilIndex])
        State.ActiveCoilTransform = TrailerCoilActors[ActiveVisualCoilIndex]->GetActorTransform();
    else if (PlayerTrailerCoilComponents.IsValidIndex(ActiveVisualCoilIndex)
        && PlayerTrailerCoilComponents[ActiveVisualCoilIndex])
        State.ActiveCoilTransform = PlayerTrailerCoilComponents[ActiveVisualCoilIndex]->GetComponentTransform();
    if (bPlayerBuiltComponentSequence)
    {
        if (PlayerHandlerChassisComponent) State.CoilHandlerChassisTransform = PlayerHandlerChassisComponent->GetComponentTransform();
        if (PlayerBridgeComponent) State.CraneBridgeTransform = PlayerBridgeComponent->GetComponentTransform();
        if (PlayerTrolleyComponent) State.CraneTrolleyTransform = PlayerTrolleyComponent->GetComponentTransform();
        if (PlayerHoistComponent) State.CraneHoistTransform = PlayerHoistComponent->GetComponentTransform();
        if (PlayerHookComponent) State.CraneHookTransform = PlayerHookComponent->GetComponentTransform();
    }
    else
    {
        if (CraneBridgeActor) State.CraneBridgeTransform = CraneBridgeActor->GetActorTransform();
        if (CraneTrolleyActor) State.CraneTrolleyTransform = CraneTrolleyActor->GetActorTransform();
        if (HoistActor) State.CraneHoistTransform = HoistActor->GetActorTransform();
        if (HookActor) State.CraneHookTransform = HookActor->GetActorTransform();
    }
    return State;
}

bool ALBInboundDeliveryController::RestoreSaveState(const FLBInboundDeliverySaveState& State)
{
    const FName SavedPR002Id = State.SaveVersion >= 3 ? State.PR002MachineId : State.CoilStoreId;
    const ELBInboundDeliverySourceMode SavedSourceMode = State.SaveVersion >= 6
        ? State.SourceMode : ELBInboundDeliverySourceMode::LegacyLorry;
    if ((State.SaveVersion < 1 || State.SaveVersion > 6)
        || State.CompletedDeliveries < 0 || State.InboundDockId.IsNone() || SavedPR002Id.IsNone()
        || !StaticEnum<ELBInboundDeliverySourceMode>()->IsValidEnumValue(
            static_cast<int64>(SavedSourceMode))
        || SavedSourceMode != SourceMode
        || State.InboundDockId != GetInboundDockId() || SavedPR002Id != GetPR002MachineId()
        || (State.Phase != ELBInboundDeliveryPhase::Idle && State.ActiveCoilId.IsNone()))
    {
        return false;
    }
    Phase = State.Phase;
    ActiveCoilId = State.ActiveCoilId;
    LastReason = State.LastReason;
    CompletedDeliveries = State.CompletedDeliveries;
    PhaseElapsedSeconds = State.SaveVersion >= 2 ? FMath::Max(0.0f, State.PhaseElapsedSeconds) : 0.0f;
    ActiveVisualCoilIndex = State.SaveVersion >= 2 ? State.ActiveVisualCoilIndex : INDEX_NONE;
    bLorryDocked = State.SaveVersion >= 2 && State.bLorryDocked;
    if (State.SaveVersion >= 2 && bVisualSequenceBound)
    {
        if (LorryActor) LorryActor->SetActorTransform(State.LorryTransform, false, nullptr, ETeleportType::TeleportPhysics);
        if (TrailerCoilActors.IsValidIndex(ActiveVisualCoilIndex) && TrailerCoilActors[ActiveVisualCoilIndex])
            TrailerCoilActors[ActiveVisualCoilIndex]->SetActorTransform(State.ActiveCoilTransform, false, nullptr, ETeleportType::TeleportPhysics);
        else if (PlayerTrailerCoilComponents.IsValidIndex(ActiveVisualCoilIndex)
            && PlayerTrailerCoilComponents[ActiveVisualCoilIndex])
            PlayerTrailerCoilComponents[ActiveVisualCoilIndex]->SetWorldTransform(
                State.ActiveCoilTransform, false, nullptr, ETeleportType::TeleportPhysics);
        if (State.SaveVersion >= 4)
        {
            if (bPlayerBuiltComponentSequence)
            {
                if (State.SaveVersion >= 5 && PlayerHandlerChassisComponent)
                    PlayerHandlerChassisComponent->SetWorldTransform(State.CoilHandlerChassisTransform,
                        false, nullptr, ETeleportType::TeleportPhysics);
                if (PlayerBridgeComponent) PlayerBridgeComponent->SetWorldTransform(State.CraneBridgeTransform, false, nullptr, ETeleportType::TeleportPhysics);
                if (PlayerTrolleyComponent) PlayerTrolleyComponent->SetWorldTransform(State.CraneTrolleyTransform, false, nullptr, ETeleportType::TeleportPhysics);
                if (PlayerHoistComponent) PlayerHoistComponent->SetWorldTransform(State.CraneHoistTransform, false, nullptr, ETeleportType::TeleportPhysics);
                if (PlayerHookComponent) PlayerHookComponent->SetWorldTransform(State.CraneHookTransform, false, nullptr, ETeleportType::TeleportPhysics);
            }
            else
            {
                if (CraneBridgeActor) CraneBridgeActor->SetActorTransform(State.CraneBridgeTransform, false, nullptr, ETeleportType::TeleportPhysics);
                if (CraneTrolleyActor) CraneTrolleyActor->SetActorTransform(State.CraneTrolleyTransform, false, nullptr, ETeleportType::TeleportPhysics);
                if (HoistActor) HoistActor->SetActorTransform(State.CraneHoistTransform, false, nullptr, ETeleportType::TeleportPhysics);
                if (HookActor) HookActor->SetActorTransform(State.CraneHookTransform, false, nullptr, ETeleportType::TeleportPhysics);
            }
        }
    }
    if (bPlayerBuiltComponentSequence)
    {
        // v1-v5 did not persist a transient steering command. Resume from the exact saved
        // chassis pose with zero speed and let the next tick derive a safe rear-wheel lock.
        ResetCoilHandlerDriveState();
    }
    return true;
}
