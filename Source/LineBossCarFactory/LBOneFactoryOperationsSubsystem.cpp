#include "LBOneFactoryOperationsSubsystem.h"

#include "Engine/World.h"
#include "EngineUtils.h"
#include "LBOneFactoryBootstrap.h"
#include "LBOneFactoryPaintStarterLayout.h"
#include "LBOneFactoryProductionFlow.h"

namespace LBOneFactoryOperationsPrivate
{
    template<typename ActorType>
    bool FindExactActor(UWorld* World, const TCHAR* Label, ActorType*& OutActor,
        FString& OutReason)
    {
        OutActor = nullptr;
        int32 Count = 0;
        if (World)
        {
            for (TActorIterator<ActorType> It(World); It; ++It)
            {
                ActorType* Candidate = *It;
                if (!IsValid(Candidate) || Candidate->IsActorBeingDestroyed())
                    continue;
                ++Count;
                OutActor = Candidate;
            }
        }
        if (Count != 1 || !OutActor
            || OutActor->GetClass() != ActorType::StaticClass())
        {
            OutActor = nullptr;
            OutReason = FString::Printf(
                TEXT("ONEFACTORY OPERATIONS REQUIRES EXACTLY ONE NATIVE %s; FOUND %d"),
                Label, Count);
            return false;
        }
        return true;
    }

    const FLBOneFactoryVehicleUnitState* FindUnit(
        const FLBOneFactoryProductionLedgerState& Ledger, const FName UnitId)
    {
        return Ledger.Units.FindByPredicate([UnitId](
            const FLBOneFactoryVehicleUnitState& Unit)
        { return Unit.UnitId == UnitId; });
    }

    TArray<FName> OrderedRoutedUnitIds(
        const FLBOneFactoryProductionLedgerState& Ledger)
    {
        TArray<FName> UnitIds;
        for (const FLBOneFactoryVehicleUnitState& Unit : Ledger.Units)
            if (Unit.RuntimeStationCursor >= 0) UnitIds.Add(Unit.UnitId);
        UnitIds.Sort([](const FName Left, const FName Right)
        { return Left.ToString() < Right.ToString(); });
        return UnitIds;
    }

    FName PaintColourId(const ELBOneFactoryPaintColour Colour)
    {
        switch (Colour)
        {
        case ELBOneFactoryPaintColour::BodyInWhite: return TEXT("BODY_IN_WHITE");
        case ELBOneFactoryPaintColour::EDPrimerGrey: return TEXT("ED_PRIMER_GREY");
        case ELBOneFactoryPaintColour::ArcticWhite: return TEXT("ARCTIC_WHITE");
        case ELBOneFactoryPaintColour::FoundryGraphite:
            return TEXT("FOUNDRY_GRAPHITE");
        case ELBOneFactoryPaintColour::CairnwellTeal:
            return TEXT("CAIRNWELL_TEAL");
        case ELBOneFactoryPaintColour::SignalRed: return TEXT("SIGNAL_RED");
        case ELBOneFactoryPaintColour::AuroraBlue: return TEXT("AURORA_BLUE");
        default: return NAME_None;
        }
    }

    FString DepartmentLabel(const ELBOneFactoryDepartment Department)
    {
        switch (Department)
        {
        case ELBOneFactoryDepartment::Press: return TEXT("PRESS");
        case ELBOneFactoryDepartment::Body: return TEXT("BODY/WELD");
        case ELBOneFactoryDepartment::Paint: return TEXT("PAINT");
        default: return TEXT("ASSEMBLY");
        }
    }

    FString QualityLabel(const ELBOneFactoryVehicleQualityState State)
    {
        switch (State)
        {
        case ELBOneFactoryVehicleQualityState::Pending: return TEXT("PENDING");
        case ELBOneFactoryVehicleQualityState::Passed: return TEXT("PASSED");
        case ELBOneFactoryVehicleQualityState::ReworkRequired:
            return TEXT("REWORK REQUIRED");
        case ELBOneFactoryVehicleQualityState::Rejected: return TEXT("REJECTED");
        case ELBOneFactoryVehicleQualityState::Scrapped: return TEXT("SCRAPPED");
        default: return TEXT("NOT INSPECTED");
        }
    }

    FName EvidenceId(const FName UnitId, const TCHAR* Action,
        const int32 StageRevision)
    {
        return FName(*FString::Printf(TEXT("OF_UI_%s_%s_R%04d"),
            *UnitId.ToString(), Action, StageRevision));
    }
}

bool ULBOneFactoryOperationsSubsystem::IsOneFactoryOperationsWorld() const
{
    UWorld* World = GetWorld();
    ALBOneFactoryBootstrap* Bootstrap = nullptr;
    FString Reason;
    if (!LBOneFactoryOperationsPrivate::FindExactActor(
            World, TEXT("ONEFACTORY BOOTSTRAP"), Bootstrap, Reason)
        || !Bootstrap->HasValidShell())
        return false;
    ALBOneFactoryProductionFlowAuthority* Production = nullptr;
    ALBOneFactoryRuntimeCoordinator* Coordinator = nullptr;
    return ResolveRuntime(Production, Coordinator, Reason);
}

bool ULBOneFactoryOperationsSubsystem::ResolveRuntime(
    ALBOneFactoryProductionFlowAuthority*& OutProduction,
    ALBOneFactoryRuntimeCoordinator*& OutCoordinator, FString& OutReason) const
{
    using namespace LBOneFactoryOperationsPrivate;
    OutReason.Reset();
    if (!FindExactActor(GetWorld(), TEXT("PRODUCTION FLOW AUTHORITY"),
            OutProduction, OutReason)
        || !FindExactActor(GetWorld(), TEXT("RUNTIME COORDINATOR"),
            OutCoordinator, OutReason))
        return false;
    if (!OutProduction->ActorHasTag(
            ALBOneFactoryProductionFlowAuthority::GetAuthorityTag())
        || !OutCoordinator->ActorHasTag(
            ALBOneFactoryRuntimeCoordinator::GetCoordinatorTag()))
    {
        OutReason = TEXT(
            "ONEFACTORY OPERATIONS RUNTIME BACKBONE IDENTITY TAG CONTRACT FAILED");
        OutProduction = nullptr;
        OutCoordinator = nullptr;
        return false;
    }
    return true;
}

bool ULBOneFactoryOperationsSubsystem::ResolveEffectiveUnit(FName& OutUnitId,
    FLBOneFactoryRuntimeVehicleStatus& OutStatus, FString& OutReason) const
{
    using namespace LBOneFactoryOperationsPrivate;
    OutUnitId = NAME_None;
    OutStatus = FLBOneFactoryRuntimeVehicleStatus();
    ALBOneFactoryProductionFlowAuthority* Production = nullptr;
    ALBOneFactoryRuntimeCoordinator* Coordinator = nullptr;
    if (!ResolveRuntime(Production, Coordinator, OutReason)) return false;
    const TArray<FName> UnitIds = OrderedRoutedUnitIds(Production->CaptureLedger());
    if (UnitIds.IsEmpty())
    {
        OutReason = TEXT("NO ROUTED ONEFACTORY VEHICLE EXISTS");
        return false;
    }
    OutUnitId = UnitIds.Contains(SelectedUnitId) ? SelectedUnitId : UnitIds[0];
    return Coordinator->GetVehicleRuntimeStatus(OutUnitId, OutStatus, OutReason);
}

TArray<FLBOneFactoryBuilderUMGAction>
ULBOneFactoryOperationsSubsystem::GetUMGActions() const
{
    using namespace LBOneFactoryOperationsPrivate;
    TArray<FLBOneFactoryBuilderUMGAction> Actions;
    Actions.SetNum(UMGActionCount);
    for (int32 Index = 0; Index < Actions.Num(); ++Index)
        Actions[Index].ActionIndex = Index;
    Actions[0].Title = TEXT("Create Cairnwell vehicle");
    Actions[1].Title = TEXT("Select next vehicle");
    Actions[2].Title = TEXT("Start / advance cycle");
    Actions[3].Title = TEXT("Pass quality gate");
    Actions[4].Title = TEXT("Request rework");

    ALBOneFactoryProductionFlowAuthority* Production = nullptr;
    ALBOneFactoryRuntimeCoordinator* Coordinator = nullptr;
    FString RuntimeReason;
    if (!ResolveRuntime(Production, Coordinator, RuntimeReason)
        || !Coordinator->ValidateRuntimeFactory(RuntimeReason))
    {
        for (FLBOneFactoryBuilderUMGAction& Action : Actions)
        {
            Action.bEnabled = false;
            Action.Detail = RuntimeReason.IsEmpty()
                ? TEXT("ONEFACTORY RUNTIME BACKBONE IS NOT READY")
                : RuntimeReason;
        }
        return Actions;
    }

    const FLBOneFactoryProductionLedgerState Ledger = Production->CaptureLedger();
    TArray<FLBOneFactoryRuntimeStationStep> Route;
    FName TopologyId;
    FString RouteReason;
    const bool bHasRoute = Coordinator->GetConfiguredStationRoute(
        Route, TopologyId, RouteReason);
    bool bInboundAvailable = bHasRoute && !Route.IsEmpty();
    if (bInboundAvailable)
    {
        ALBOneFactoryPressStarterLayoutAuthority* Press = nullptr;
        if (!FindExactActor(GetWorld(), TEXT("PRESS LAYOUT AUTHORITY"), Press,
                RouteReason))
            bInboundAvailable = false;
        else
        {
            const FLBOneFactoryPressStarterLayoutState PressState =
                Press->CaptureLayout();
            const FLBOneFactoryPressStarterStationState* Inbound =
                PressState.Stations.FindByPredicate([&Route](
                    const FLBOneFactoryPressStarterStationState& Station)
                { return Station.StationId == Route[0].StationId; });
            bInboundAvailable = Inbound
                && Inbound->ActiveOrReservedUnitIds.IsEmpty()
                && Production->GetActiveWIPCount() < Ledger.MaximumConcurrentWIP;
        }
    }
    Actions[0].bEnabled = bInboundAvailable;
    Actions[0].Detail = bInboundAvailable
        ? FString::Printf(TEXT("CREATE BUILD ORDER %06d FROM THE CONFIGURED MODEL, PAINT PROGRAMME AND COIL LOT"),
            Ledger.NextVehicleSerial)
        : RouteReason.IsEmpty()
            ? TEXT("PRESS INBOUND OR MAXIMUM WIP CURRENTLY BLOCKS A NEW VEHICLE")
            : RouteReason;

    const TArray<FName> UnitIds = OrderedRoutedUnitIds(Ledger);
    Actions[1].bEnabled = !UnitIds.IsEmpty();
    Actions[1].Detail = UnitIds.IsEmpty()
        ? TEXT("CREATE A VEHICLE BEFORE SELECTING RUNTIME WIP")
        : FString::Printf(TEXT("%d ROUTED VEHICLE%s | CURRENT %s"),
            UnitIds.Num(), UnitIds.Num() == 1 ? TEXT("") : TEXT("S"),
            *(UnitIds.Contains(SelectedUnitId) ? SelectedUnitId : UnitIds[0]).ToString());

    FName UnitId;
    FLBOneFactoryRuntimeVehicleStatus Status;
    FString StatusReason;
    if (!ResolveEffectiveUnit(UnitId, Status, StatusReason))
    {
        for (int32 Index = 2; Index < Actions.Num(); ++Index)
        {
            Actions[Index].bEnabled = false;
            Actions[Index].Detail = StatusReason;
        }
        return Actions;
    }

    if (Status.bDispatched)
    {
        Actions[2].Title = TEXT("Vehicle dispatched");
        Actions[2].bEnabled = false;
        Actions[2].Detail = FString::Printf(TEXT("%s COMPLETED ALL 57 STATIONS"),
            *UnitId.ToString());
    }
    else if (!Status.bStarted)
    {
        Actions[2].Title = TEXT("Start selected vehicle");
        Actions[2].bEnabled = true;
        Actions[2].Detail = FString::Printf(TEXT("RELEASE %s INTO STATION %d OF 57"),
            *UnitId.ToString(), Status.StationCursor + 1);
    }
    else
    {
        const bool bQualityHold = Status.bAtQualityGate
            && Status.NormalizedCycleProgress >= 1.0f
            && Status.QualityState != ELBOneFactoryVehicleQualityState::Passed;
        Actions[2].Title = Status.bCompleted
            ? TEXT("Dispatch finished vehicle") : TEXT("Advance one station cycle");
        Actions[2].bEnabled = !bQualityHold;
        Actions[2].Detail = bQualityHold
            ? TEXT("RECORD OR COMPLETE THE QUALITY DECISION BEFORE ADVANCING")
            : FString::Printf(TEXT("%s | STATION %d OF 57 | %.0f%% CYCLE"),
                *Status.CurrentStationId.ToString(), Status.StationCursor + 1,
                Status.NormalizedCycleProgress * 100.0f);
    }

    const bool bCanRecordQuality = Status.bAtQualityGate
        && Status.NormalizedCycleProgress >= 1.0f
        && Status.QualityState == ELBOneFactoryVehicleQualityState::Pending;
    Actions[3].bEnabled = bCanRecordQuality;
    Actions[3].Detail = bCanRecordQuality
        ? FString::Printf(TEXT("RECORD PASSED INSPECTION EVIDENCE FOR %s"),
            *UnitId.ToString())
        : TEXT("A COMPLETED PENDING INSPECTION CYCLE IS REQUIRED");

    const bool bCanRequestRework = bCanRecordQuality;
    const bool bCanCompleteRework = Status.bAtQualityGate
        && Status.QualityState ==
            ELBOneFactoryVehicleQualityState::ReworkRequired;
    Actions[4].Title = bCanCompleteRework
        ? TEXT("Complete rework") : TEXT("Request rework");
    Actions[4].bEnabled = bCanRequestRework || bCanCompleteRework;
    Actions[4].Detail = bCanCompleteRework
        ? TEXT("RECORD REWORK EVIDENCE AND RESET THIS INSPECTION CYCLE")
        : bCanRequestRework
            ? TEXT("HOLD THIS UNIT FOR REWORK WITHOUT CHANGING ITS ID")
            : TEXT("REWORK IS AVAILABLE ONLY AT A COMPLETED QUALITY GATE");
    return Actions;
}

FString ULBOneFactoryOperationsSubsystem::GetUMGSummary() const
{
    using namespace LBOneFactoryOperationsPrivate;
    ALBOneFactoryProductionFlowAuthority* Production = nullptr;
    ALBOneFactoryRuntimeCoordinator* Coordinator = nullptr;
    FString Reason;
    if (!ResolveRuntime(Production, Coordinator, Reason)) return Reason;
    const FLBOneFactoryProductionLedgerState Ledger = Production->CaptureLedger();
    FName UnitId;
    FLBOneFactoryRuntimeVehicleStatus Status;
    if (!ResolveEffectiveUnit(UnitId, Status, Reason))
    {
        return FString::Printf(TEXT(
            "57-STATION LINE | WIP %d/%d | COMPLETED %d | DISPATCHED %d | %s | LAST %s: %s"),
            Production->GetActiveWIPCount(), Ledger.MaximumConcurrentWIP,
            Ledger.CompletedVehicleCount, Ledger.DispatchedVehicleCount,
            Ledger.bLinePaused ? TEXT("PAUSED") : TEXT("READY"),
            bLastActionSucceeded ? TEXT("PASS") : TEXT("REJECT"),
            *LastActionReason);
    }
    return FString::Printf(TEXT(
        "%s | %s | STATION %d/57 (%d COMPLETE) | %s | QUALITY %s | %.0f%% | WIP %d/%d | LAST %s: %s"),
        *UnitId.ToString(), *DepartmentLabel(Status.Department),
        FMath::Min(Status.StationCursor + 1, Status.TotalStationCount),
        Status.CompletedStationCount, *Status.CurrentStationId.ToString(),
        *QualityLabel(Status.QualityState),
        Status.NormalizedCycleProgress * 100.0f,
        Production->GetActiveWIPCount(), Ledger.MaximumConcurrentWIP,
        bLastActionSucceeded ? TEXT("PASS") : TEXT("REJECT"),
        *LastActionReason);
}

void ULBOneFactoryOperationsSubsystem::SetLastResult(const bool bSucceeded,
    const FString& Reason, FString& OutReason)
{
    bLastActionSucceeded = bSucceeded;
    LastActionReason = Reason.IsEmpty()
        ? (bSucceeded ? TEXT("ONEFACTORY VEHICLE ACTION SUCCEEDED")
            : TEXT("ONEFACTORY VEHICLE ACTION FAILED CLOSED"))
        : Reason;
    OutReason = LastActionReason;
}

bool ULBOneFactoryOperationsSubsystem::CreateConfiguredVehicle(
    FString& OutReason)
{
    using namespace LBOneFactoryOperationsPrivate;
    ALBOneFactoryProductionFlowAuthority* Production = nullptr;
    ALBOneFactoryRuntimeCoordinator* Coordinator = nullptr;
    FString Reason;
    if (!ResolveRuntime(Production, Coordinator, Reason))
    {
        SetLastResult(false, Reason, OutReason);
        return false;
    }
    ALBOneFactoryPaintStarterLayoutAuthority* Paint = nullptr;
    if (!FindExactActor(GetWorld(), TEXT("PAINT LAYOUT AUTHORITY"), Paint,
            Reason))
    {
        SetLastResult(false, Reason, OutReason);
        return false;
    }
    const FLBOneFactoryPaintStarterLayoutState PaintState =
        Paint->CaptureLayout();
    const int32 Serial = Production->CaptureLedger().NextVehicleSerial;
    const FName BuildOrderId(*FString::Printf(TEXT("OF_BUILD_%06d"), Serial));
    const FName CoilLotId(*FString::Printf(TEXT("OF_COIL_LOT_%06d"), Serial));
    const FName ColourId = PaintColourId(PaintState.SelectedBodyColour);
    FName NewUnitId;
    const bool bCreated = Coordinator->CreateRuntimeVehicleOrder(BuildOrderId,
        PaintState.VehicleModelId, PaintState.PaintProgrammeId, ColourId,
        CoilLotId, NewUnitId, Reason);
    if (bCreated) SelectedUnitId = NewUnitId;
    SetLastResult(bCreated, Reason, OutReason);
    return bCreated;
}

bool ULBOneFactoryOperationsSubsystem::SelectNextVehicle(FString& OutReason)
{
    using namespace LBOneFactoryOperationsPrivate;
    ALBOneFactoryProductionFlowAuthority* Production = nullptr;
    ALBOneFactoryRuntimeCoordinator* Coordinator = nullptr;
    FString Reason;
    if (!ResolveRuntime(Production, Coordinator, Reason))
    {
        SetLastResult(false, Reason, OutReason);
        return false;
    }
    const TArray<FName> UnitIds = OrderedRoutedUnitIds(
        Production->CaptureLedger());
    if (UnitIds.IsEmpty())
    {
        SetLastResult(false, TEXT("NO ROUTED ONEFACTORY VEHICLE EXISTS"),
            OutReason);
        return false;
    }
    const int32 Current = UnitIds.IndexOfByKey(SelectedUnitId);
    SelectedUnitId = UnitIds[(Current + 1) % UnitIds.Num()];
    SetLastResult(true, FString::Printf(TEXT("SELECTED ONEFACTORY VEHICLE %s"),
        *SelectedUnitId.ToString()), OutReason);
    return true;
}

bool ULBOneFactoryOperationsSubsystem::StartOrAdvanceSelectedVehicle(
    FString& OutReason)
{
    ALBOneFactoryProductionFlowAuthority* Production = nullptr;
    ALBOneFactoryRuntimeCoordinator* Coordinator = nullptr;
    FString Reason;
    if (!ResolveRuntime(Production, Coordinator, Reason))
    {
        SetLastResult(false, Reason, OutReason);
        return false;
    }
    FName UnitId;
    FLBOneFactoryRuntimeVehicleStatus Status;
    if (!ResolveEffectiveUnit(UnitId, Status, Reason))
    {
        SetLastResult(false, Reason, OutReason);
        return false;
    }
    SelectedUnitId = UnitId;
    const bool bSucceeded = !Status.bStarted
        ? Coordinator->StartVehicle(UnitId, Reason)
        : Coordinator->TickVehicle(UnitId, FMath::Max(0.001f,
            Status.CycleDurationSeconds - Status.CycleElapsedSeconds), Reason);
    SetLastResult(bSucceeded, Reason, OutReason);
    return bSucceeded;
}

bool ULBOneFactoryOperationsSubsystem::PassSelectedQualityGate(
    FString& OutReason)
{
    using namespace LBOneFactoryOperationsPrivate;
    ALBOneFactoryProductionFlowAuthority* Production = nullptr;
    ALBOneFactoryRuntimeCoordinator* Coordinator = nullptr;
    FString Reason;
    if (!ResolveRuntime(Production, Coordinator, Reason))
    {
        SetLastResult(false, Reason, OutReason);
        return false;
    }
    FName UnitId;
    FLBOneFactoryRuntimeVehicleStatus Status;
    if (!ResolveEffectiveUnit(UnitId, Status, Reason))
    {
        SetLastResult(false, Reason, OutReason);
        return false;
    }
    const FLBOneFactoryProductionLedgerState Ledger =
        Production->CaptureLedger();
    const FLBOneFactoryVehicleUnitState* Unit = FindUnit(Ledger, UnitId);
    const bool bSucceeded = Unit && Coordinator->SubmitRuntimeQualityResult(
        UnitId, ELBOneFactoryVehicleQualityState::Passed,
        EvidenceId(UnitId, TEXT("QUALITY_PASS"), Unit->StageRevision), Reason);
    if (!Unit) Reason = TEXT("SELECTED ONEFACTORY VEHICLE LEFT THE LEDGER");
    SetLastResult(bSucceeded, Reason, OutReason);
    return bSucceeded;
}

bool ULBOneFactoryOperationsSubsystem::RequestOrCompleteSelectedRework(
    FString& OutReason)
{
    using namespace LBOneFactoryOperationsPrivate;
    ALBOneFactoryProductionFlowAuthority* Production = nullptr;
    ALBOneFactoryRuntimeCoordinator* Coordinator = nullptr;
    FString Reason;
    if (!ResolveRuntime(Production, Coordinator, Reason))
    {
        SetLastResult(false, Reason, OutReason);
        return false;
    }
    FName UnitId;
    FLBOneFactoryRuntimeVehicleStatus Status;
    if (!ResolveEffectiveUnit(UnitId, Status, Reason))
    {
        SetLastResult(false, Reason, OutReason);
        return false;
    }
    const FLBOneFactoryProductionLedgerState Ledger =
        Production->CaptureLedger();
    const FLBOneFactoryVehicleUnitState* Unit = FindUnit(Ledger, UnitId);
    bool bSucceeded = false;
    if (!Unit)
        Reason = TEXT("SELECTED ONEFACTORY VEHICLE LEFT THE LEDGER");
    else if (Status.QualityState ==
        ELBOneFactoryVehicleQualityState::ReworkRequired)
        bSucceeded = Coordinator->CompleteRuntimeRework(UnitId,
            EvidenceId(UnitId, TEXT("REWORK_COMPLETE"), Unit->StageRevision),
            Reason);
    else
        bSucceeded = Coordinator->SubmitRuntimeQualityResult(UnitId,
            ELBOneFactoryVehicleQualityState::ReworkRequired,
            EvidenceId(UnitId, TEXT("REWORK_REQUEST"), Unit->StageRevision),
            Reason);
    SetLastResult(bSucceeded, Reason, OutReason);
    return bSucceeded;
}

bool ULBOneFactoryOperationsSubsystem::ExecuteUMGAction(
    const int32 ActionIndex, FString& OutReason)
{
    if (!FMath::IsWithin(ActionIndex, 0, UMGActionCount))
    {
        SetLastResult(false, TEXT("ONEFACTORY OPERATIONS UMG ACTION INDEX IS INVALID"),
            OutReason);
        return false;
    }
    const TArray<FLBOneFactoryBuilderUMGAction> Actions = GetUMGActions();
    if (!Actions[ActionIndex].bEnabled)
    {
        SetLastResult(false, Actions[ActionIndex].Detail, OutReason);
        return false;
    }
    switch (ActionIndex)
    {
    case 0: return CreateConfiguredVehicle(OutReason);
    case 1: return SelectNextVehicle(OutReason);
    case 2: return StartOrAdvanceSelectedVehicle(OutReason);
    case 3: return PassSelectedQualityGate(OutReason);
    default: return RequestOrCompleteSelectedRework(OutReason);
    }
}

bool ULBOneFactoryOperationsSubsystem::SetSimulationRate(
    const float RequestedRate, FString& OutReason)
{
    ALBOneFactoryProductionFlowAuthority* Production = nullptr;
    ALBOneFactoryRuntimeCoordinator* Coordinator = nullptr;
    FString Reason;
    if (!ResolveRuntime(Production, Coordinator, Reason))
    {
        SetLastResult(false, Reason, OutReason);
        return false;
    }
    if (!FMath::IsFinite(RequestedRate) || RequestedRate < 0.0f
        || RequestedRate > 4.0f)
    {
        SetLastResult(false,
            TEXT("ONEFACTORY SIMULATION RATE MUST BE BETWEEN PAUSE AND 4X"),
            OutReason);
        return false;
    }
    const FLBOneFactoryProductionLedgerState Before = Production->CaptureLedger();
    const float BeforeScale = Coordinator->GetRuntimeTimeScale();
    bool bSucceeded = true;
    if (RequestedRate <= KINDA_SMALL_NUMBER)
        bSucceeded = Production->SetLinePaused(true, Reason);
    else
        bSucceeded = Coordinator->SetRuntimeTimeScale(RequestedRate, Reason)
            && Production->SetLinePaused(false, Reason);
    if (!bSucceeded)
    {
        FString Ignored;
        Production->RestoreLedger(Before, Ignored);
        Coordinator->SetRuntimeTimeScale(BeforeScale, Ignored);
    }
    else
        Reason = RequestedRate <= KINDA_SMALL_NUMBER
            ? TEXT("ONEFACTORY LINE PAUSED")
            : FString::Printf(TEXT("ONEFACTORY LINE RUNNING AT %.0fX"),
                RequestedRate);
    SetLastResult(bSucceeded, Reason, OutReason);
    return bSucceeded;
}
