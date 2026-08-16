#include "LBFactoryUIStateSubsystem.h"

#include "LBControlRoomOperationsConsole.h"
#include "LBBodyWeldLineActor.h"
#include "LBCoilAGVController.h"
#include "LBECoatLineActor.h"
#include "LBFactoryBuildMachine.h"
#include "LBFactoryManagementSubsystem.h"
#include "LBPlayerBuiltPressFlowController.h"
#include "LBPressShopStorageZone.h"
#include "LBPressTrainAStation.h"
#include "LBSupportRobot.h"
#include "Engine/World.h"
#include "EngineUtils.h"
#include "GameFramework/WorldSettings.h"

namespace
{
    FString MachineTypeName(const ELBFactoryBuildMachineType Type)
    {
        switch (Type)
        {
        case ELBFactoryBuildMachineType::InboundDeliveryDock: return TEXT("INBOUND DELIVERY");
        case ELBFactoryBuildMachineType::CoilWeighInspectionCell: return TEXT("PR-002 COIL INSPECTION");
        case ELBFactoryBuildMachineType::DepackagingRobot: return TEXT("PR-004 DEPACKAGING");
        case ELBFactoryBuildMachineType::DecoilerFeeder: return TEXT("COIL PREPARATION");
        case ELBFactoryBuildMachineType::PressTrain: return TEXT("PRESS TRAIN");
        case ELBFactoryBuildMachineType::InspectionCell: return TEXT("PANEL INSPECTION");
        case ELBFactoryBuildMachineType::OutboundPanelDock: return TEXT("WELD SHOP INTAKE");
        case ELBFactoryBuildMachineType::ECoatLine: return TEXT("ED / E-COAT LINE");
        case ELBFactoryBuildMachineType::BodyWeldLine: return TEXT("BODY WELD / BIW LINE");
        default: return TEXT("FACTORY MACHINE");
        }
    }

    int32 MachineProcessOrder(const ELBFactoryBuildMachineType Type)
    {
        switch (Type)
        {
        case ELBFactoryBuildMachineType::InboundDeliveryDock: return 0;
        case ELBFactoryBuildMachineType::CoilWeighInspectionCell: return 10;
        case ELBFactoryBuildMachineType::DepackagingRobot: return 20;
        case ELBFactoryBuildMachineType::DecoilerFeeder: return 30;
        case ELBFactoryBuildMachineType::PressTrain: return 40;
        case ELBFactoryBuildMachineType::InspectionCell: return 50;
        case ELBFactoryBuildMachineType::OutboundPanelDock: return 60;
        case ELBFactoryBuildMachineType::BodyWeldLine: return 100;
        case ELBFactoryBuildMachineType::ECoatLine: return 110;
        default: return 100;
        }
    }

    FString MachineStateName(const ELBFactoryMachineOperatingState State)
    {
        switch (State)
        {
        case ELBFactoryMachineOperatingState::Idle: return TEXT("IDLE");
        case ELBFactoryMachineOperatingState::Starved: return TEXT("WAITING");
        case ELBFactoryMachineOperatingState::Ready: return TEXT("READY");
        case ELBFactoryMachineOperatingState::Blocked: return TEXT("BLOCKED");
        case ELBFactoryMachineOperatingState::Processing: return TEXT("RUNNING");
        case ELBFactoryMachineOperatingState::Fault: return TEXT("FAULT");
        default: return TEXT("UNKNOWN");
        }
    }

    FString ECoatStateName(const ELBECoatOperatingState State)
    {
        switch (State)
        {
        case ELBECoatOperatingState::Stopped: return TEXT("STOPPED");
        case ELBECoatOperatingState::Starting: return TEXT("STARTING");
        case ELBECoatOperatingState::Running: return TEXT("RUNNING");
        case ELBECoatOperatingState::Paused: return TEXT("PAUSED");
        case ELBECoatOperatingState::Starved: return TEXT("WAITING");
        case ELBECoatOperatingState::Faulted: return TEXT("FAULT");
        case ELBECoatOperatingState::Maintenance: return TEXT("MAINTENANCE");
        case ELBECoatOperatingState::EmergencyStop: return TEXT("EMERGENCY STOP");
        default: return TEXT("UNKNOWN");
        }
    }

    FString BodyWeldPhaseName(const ELBBodyWeldPhase Phase)
    {
        switch (Phase)
        {
        case ELBBodyWeldPhase::AwaitingRecipe: return TEXT("AWAITING RECIPE");
        case ELBBodyWeldPhase::ReservingInputs: return TEXT("RESERVING INPUTS");
        case ELBBodyWeldPhase::ClosurePreparation: return TEXT("CLOSURE PREPARATION");
        case ELBBodyWeldPhase::Framing: return TEXT("FRAMING");
        case ELBBodyWeldPhase::Welding: return TEXT("WELDING");
        case ELBBodyWeldPhase::GeometryCheck: return TEXT("GEOMETRY CHECK");
        case ELBBodyWeldPhase::OutputReady: return TEXT("OUTPUT READY");
        case ELBBodyWeldPhase::TransferringToED: return TEXT("TRANSFERRING TO ED");
        default: return TEXT("UNKNOWN");
        }
    }

    FString StorageTypeName(const ELBPressShopStorageType Type)
    {
        switch (Type)
        {
        case ELBPressShopStorageType::BareCoils: return TEXT("WRAPPED COIL STORAGE");
        case ELBPressShopStorageType::PreparedBlanks: return TEXT("PREPARED BLANK BUFFER");
        case ELBPressShopStorageType::FinishedPanelStillages: return TEXT("FULL PRESSED-PANEL STILLAGE STORE");
        case ELBPressShopStorageType::Scrap: return TEXT("SCRAP STORAGE");
        case ELBPressShopStorageType::MaintenanceParts: return TEXT("MAINTENANCE PARTS");
        case ELBPressShopStorageType::Quarantine: return TEXT("QUARANTINE STORAGE");
        case ELBPressShopStorageType::EmptyPanelStillages: return TEXT("EMPTY STILLAGE RETURN STORE");
        default: return TEXT("STORAGE");
        }
    }

    FString PressStateName(const ELBPressTrainAState State)
    {
        switch (State)
        {
        case ELBPressTrainAState::Isolated: return TEXT("ISOLATED");
        case ELBPressTrainAState::Ready: return TEXT("READY");
        case ELBPressTrainAState::Cycling: return TEXT("RUNNING");
        case ELBPressTrainAState::Stopping: return TEXT("STOPPING");
        case ELBPressTrainAState::Fault: return TEXT("FAULT");
        default: return TEXT("UNKNOWN");
        }
    }

    FString CoilPhaseName(const ELBCoilAGVPhase Phase)
    {
        switch (Phase)
        {
        case ELBCoilAGVPhase::IdleLoaded: return TEXT("LOADED / READY");
        case ELBCoilAGVPhase::AwaitingReload: return TEXT("AWAITING RELOAD");
        case ELBCoilAGVPhase::HandoffReady: return TEXT("HANDOFF READY");
        case ELBCoilAGVPhase::Fault: return TEXT("FAULT");
        default: return TEXT("MOVING");
        }
    }

    int32 SeverityRank(const ELBFactoryUIAlertSeverity Severity)
    {
        switch (Severity)
        {
        case ELBFactoryUIAlertSeverity::Critical: return 0;
        case ELBFactoryUIAlertSeverity::Warning: return 1;
        default: return 2;
        }
    }

    FVector MarkerLocationFor(AActor* Actor)
    {
        if (!Actor) return FVector::ZeroVector;
        FVector Origin;
        FVector Extent;
        Actor->GetActorBounds(true, Origin, Extent);
        return Origin + FVector(0.0f, 0.0f, FMath::Max(Extent.Z, 100.0f) + 120.0f);
    }
}

const FLBFactoryUIStateSnapshot& ULBFactoryUIStateSubsystem::GetSnapshot(const bool bForceRefresh)
{
    UWorld* World = GetWorld();
    const double Now = World ? static_cast<double>(World->GetTimeSeconds()) : 0.0;
    if (bForceRefresh || LastRefreshWorldSeconds < 0.0 || Now - LastRefreshWorldSeconds >= 0.25)
    {
        RefreshSnapshot();
    }
    return CachedSnapshot;
}

void ULBFactoryUIStateSubsystem::ForceRefresh()
{
    RefreshSnapshot();
}

void ULBFactoryUIStateSubsystem::AddAlert(const ELBFactoryUIAlertSeverity Severity,
    const FName EntityId, const FString& Title, const FString& Detail,
    AActor* TargetActor, const int32 ProcessOrder)
{
    FLBFactoryUIAlertSnapshot Alert;
    Alert.Severity = Severity;
    Alert.EntityId = EntityId;
    Alert.Title = Title;
    Alert.Detail = Detail;
    Alert.TargetActor = TargetActor;
    Alert.MarkerWorldLocation = MarkerLocationFor(TargetActor);
    Alert.ProcessOrder = ProcessOrder;
    CachedSnapshot.Alerts.Add(MoveTemp(Alert));
}

void ULBFactoryUIStateSubsystem::RefreshSnapshot()
{
    CachedSnapshot = FLBFactoryUIStateSnapshot();
    UWorld* World = GetWorld();
    if (!World)
    {
        LastRefreshWorldSeconds = 0.0;
        return;
    }

    LastRefreshWorldSeconds = World->GetTimeSeconds();
    if (const AWorldSettings* Settings = World->GetWorldSettings())
    {
        CachedSnapshot.EffectiveSimulationRate = Settings->GetEffectiveTimeDilation();
    }

    // Keep the six production-flow nodes stable even in an empty campaign. A
    // missing actor is a useful player decision (place the next process), not a
    // reason for the HUD to reorder or invent a replacement stage.
    const auto AddProductionStage = [&](const FName StageId,
        const TCHAR* DisplayName, const int32 ProcessOrder)
    {
        FLBFactoryUIProductionStageSnapshot& Stage =
            CachedSnapshot.ProductionStages.AddDefaulted_GetRef();
        Stage.StageId = StageId;
        Stage.DisplayName = DisplayName;
        Stage.ProcessOrder = ProcessOrder;
    };
    AddProductionStage(TEXT("COIL_INTAKE"), TEXT("Coil intake"), 0);
    AddProductionStage(TEXT("BLANK_BUFFER"), TEXT("Blank buffer"), 35);
    AddProductionStage(TEXT("TRANSFER_PRESS"), TEXT("Transfer press"), 40);
    AddProductionStage(TEXT("PANEL_STILLAGES"), TEXT("Panel stillages"), 70);
    AddProductionStage(TEXT("BODY_WELD"), TEXT("Body weld"), 100);
    AddProductionStage(TEXT("ED_COAT"), TEXT("ED coat"), 110);

    const auto FindProductionStage = [&](const FName StageId)
        -> FLBFactoryUIProductionStageSnapshot*
    {
        return CachedSnapshot.ProductionStages.FindByPredicate(
            [StageId](const FLBFactoryUIProductionStageSnapshot& Stage)
            {
                return Stage.StageId == StageId;
            });
    };
    const auto SetProductionStage = [&](const FName StageId, AActor* Actor,
        const FString& State, const FString& Detail, const bool bRunning,
        const bool bWaiting, const bool bFaulted)
    {
        FLBFactoryUIProductionStageSnapshot* Stage = FindProductionStage(StageId);
        if (!Stage || !IsValid(Actor)) return;
        Stage->bInstalled = true;
        Stage->State = State;
        Stage->Detail = Detail;
        Stage->bRunning = bRunning;
        Stage->bWaiting = bWaiting;
        Stage->bFaulted = bFaulted;
        Stage->WorldLocation = Actor->GetActorLocation();
        Stage->TargetActor = Actor;
    };

    // Prefer the player-built order authority in the clean map. Dispatched means issued to a
    // press train, not completed at inspection, so the HUD labels this quantity truthfully.
    for (TActorIterator<ALBPlayerBuiltPressFlowController> It(World); It; ++It)
    {
        const TArray<FLBVehiclePanelBatch> Batches = It->GetPanelBatches();
        const FLBVehiclePanelBatch* Active = Batches.FindByPredicate([](const FLBVehiclePanelBatch& Batch)
        {
            return Batch.RequestedQuantity > 0 && Batch.DispatchedQuantity < Batch.RequestedQuantity;
        });
        if (Active)
        {
            CachedSnapshot.Order.bHasActiveOrder = true;
            CachedSnapshot.Order.OrderId = Active->OrderId;
            CachedSnapshot.Order.VehicleModelId = Active->VehicleModelId;
            CachedSnapshot.Order.PanelTypeId = Active->PanelTypeId;
            CachedSnapshot.Order.IssuedQuantity = Active->DispatchedQuantity;
            CachedSnapshot.Order.RequestedQuantity = Active->RequestedQuantity;
            CachedSnapshot.Order.Objective = FString::Printf(TEXT("%s / %s"),
                *Active->VehicleModelId.ToString(), *Active->PanelTypeId.ToString());
        }
        break;
    }

    // Legacy control-room maps retain their existing order authority.
    if (!CachedSnapshot.Order.bHasActiveOrder)
    {
        for (TActorIterator<ALBControlRoomOperationsConsole> It(World); It; ++It)
        {
            const FLBControlRoomOperationsSaveState State = It->CaptureSaveState();
            if (State.OrderState != ELBControlRoomOrderState::Draft
                && State.OrderState != ELBControlRoomOrderState::Completed
                && State.RequestedQuantity > 0)
            {
                CachedSnapshot.Order.bHasActiveOrder = true;
                CachedSnapshot.Order.OrderId = State.RecipeId.IsNone() ? TEXT("CONTROL-ROOM-ORDER") : State.RecipeId;
                CachedSnapshot.Order.VehicleModelId = TEXT("CURRENT VEHICLE");
                CachedSnapshot.Order.PanelTypeId = State.PanelFamily;
                CachedSnapshot.Order.IssuedQuantity = State.GoodPanels + State.RejectedPanels;
                CachedSnapshot.Order.RequestedQuantity = State.RequestedQuantity;
                CachedSnapshot.Order.Objective = State.PanelFamily.ToString();
            }
            break;
        }
    }

    for (TActorIterator<ALBFactoryBuildMachine> It(World); It; ++It)
    {
        ALBFactoryBuildMachine* Machine = *It;
        if (!IsValid(Machine)) continue;
        ++CachedSnapshot.OperationalAssetCount;
        ++CachedSnapshot.MachineCount;
        const ELBFactoryMachineOperatingState State = Machine->GetOperatingState();
        if (State == ELBFactoryMachineOperatingState::Processing) ++CachedSnapshot.RunningCount;
        if (State == ELBFactoryMachineOperatingState::Starved
            || State == ELBFactoryMachineOperatingState::Blocked) ++CachedSnapshot.WaitingCount;
        if (State == ELBFactoryMachineOperatingState::Fault) ++CachedSnapshot.FaultCount;

        const int32 Order = MachineProcessOrder(Machine->GetMachineType());

        if (Machine->GetMachineType() == ELBFactoryBuildMachineType::InboundDeliveryDock)
        {
            SetProductionStage(TEXT("COIL_INTAKE"), Machine,
                MachineStateName(State),
                FString::Printf(TEXT("%d coils queued"), Machine->GetInputUnitCount()),
                State == ELBFactoryMachineOperatingState::Processing,
                State == ELBFactoryMachineOperatingState::Starved
                    || State == ELBFactoryMachineOperatingState::Blocked,
                State == ELBFactoryMachineOperatingState::Fault);
        }
        if (State == ELBFactoryMachineOperatingState::Fault)
        {
            AddAlert(ELBFactoryUIAlertSeverity::Critical, Machine->GetMachineId(),
                TEXT("MACHINE FAULT"), Machine->GetOperatingReason(), Machine, Order);
        }
        else if (State == ELBFactoryMachineOperatingState::Blocked)
        {
            AddAlert(ELBFactoryUIAlertSeverity::Warning, Machine->GetMachineId(),
                TEXT("OUTPUT BLOCKED"), Machine->GetOperatingReason(), Machine, Order);
        }
        else if (CachedSnapshot.Order.bHasActiveOrder
            && State == ELBFactoryMachineOperatingState::Starved)
        {
            AddAlert(ELBFactoryUIAlertSeverity::Information, Machine->GetMachineId(),
                TEXT("AWAITING MATERIAL"), Machine->GetOperatingReason(), Machine, Order);
        }
    }

    for (TActorIterator<ALBBodyWeldLineActor> It(World); It; ++It)
    {
        ALBBodyWeldLineActor* Line = *It;
        if (!IsValid(Line)
            || !ULBFactoryManagementSubsystem::IsStrictId(Line->GetLineId())) continue;

        ++CachedSnapshot.OperationalAssetCount;
        ++CachedSnapshot.MachineCount;
        const ELBFactoryMachineOperatingState State = Line->GetOperatingState();
        if (State == ELBFactoryMachineOperatingState::Processing)
            ++CachedSnapshot.RunningCount;
        if (State == ELBFactoryMachineOperatingState::Starved
            || State == ELBFactoryMachineOperatingState::Blocked)
            ++CachedSnapshot.WaitingCount;
        if (State == ELBFactoryMachineOperatingState::Fault)
            ++CachedSnapshot.FaultCount;

        FLBBodyInWhiteRecord OutputBody;
        FLBBodyInWhiteRecord ReworkBody;
        FLBFactoryUIBodyWeldLineSnapshot WeldSnapshot;
        WeldSnapshot.LineId = Line->GetLineId();
        WeldSnapshot.State = MachineStateName(State);
        WeldSnapshot.Phase = BodyWeldPhaseName(Line->GetPhase());
        WeldSnapshot.Reason = Line->GetOperatingReason();
        WeldSnapshot.PhaseProgress01 = Line->GetPhaseProgress01();
        WeldSnapshot.AssignedOrderId = Line->GetAssignedOrderId();
        WeldSnapshot.AvailablePanelCount = Line->GetAvailablePanelCount();
        WeldSnapshot.ReservedPanelCount = Line->GetReservedPanelCount();
        WeldSnapshot.AvailableBaseKitCount = Line->GetAvailableBaseKitCount();
        WeldSnapshot.PendingEmptyReturnCount = Line->GetPendingEmptyReturnCount();
        if (Line->GetOutputBody(OutputBody)) WeldSnapshot.OutputBodyId = OutputBody.BodyId;
        if (Line->GetReworkBody(ReworkBody)) WeldSnapshot.ReworkBodyId = ReworkBody.BodyId;
        WeldSnapshot.CompletedBodyCount = Line->GetCompletedBodyCount();
        WeldSnapshot.bEDAvailable = Line->IsEDAvailable();
        WeldSnapshot.WorldLocation = Line->GetActorLocation();
        WeldSnapshot.TargetActor = Line;
        CachedSnapshot.BodyWeldLines.Add(WeldSnapshot);
        SetProductionStage(TEXT("BODY_WELD"), Line, WeldSnapshot.State,
            FString::Printf(TEXT("%s | %d panels"), *WeldSnapshot.Phase,
                WeldSnapshot.AvailablePanelCount),
            State == ELBFactoryMachineOperatingState::Processing,
            State == ELBFactoryMachineOperatingState::Starved
                || State == ELBFactoryMachineOperatingState::Blocked,
            State == ELBFactoryMachineOperatingState::Fault);

        const FString LiveDetail = FString::Printf(
            TEXT("%s | %d PANELS / %d BASE KITS / %d EMPTY RETURNS"),
            *Line->GetOperatingReason(), WeldSnapshot.AvailablePanelCount,
            WeldSnapshot.AvailableBaseKitCount, WeldSnapshot.PendingEmptyReturnCount);
        if (State == ELBFactoryMachineOperatingState::Fault)
        {
            AddAlert(ELBFactoryUIAlertSeverity::Critical, Line->GetLineId(),
                TEXT("BODY WELD LINE FAULT"), LiveDetail, Line, 100);
        }
        else if (!WeldSnapshot.ReworkBodyId.IsNone())
        {
            AddAlert(ELBFactoryUIAlertSeverity::Warning, Line->GetLineId(),
                TEXT("BIW REWORK REQUIRED"), FString::Printf(TEXT("BODY %s | %s"),
                    *WeldSnapshot.ReworkBodyId.ToString(), *LiveDetail), Line, 100);
        }
        else if (!WeldSnapshot.OutputBodyId.IsNone())
        {
            AddAlert(ELBFactoryUIAlertSeverity::Warning, Line->GetLineId(),
                TEXT("BIW OUTPUT AWAITING ED"), FString::Printf(TEXT("BODY %s | %s"),
                    *WeldSnapshot.OutputBodyId.ToString(), *LiveDetail), Line, 100);
        }
        else if (State == ELBFactoryMachineOperatingState::Blocked)
        {
            AddAlert(ELBFactoryUIAlertSeverity::Warning, Line->GetLineId(),
                TEXT("BODY WELD LINE BLOCKED"), LiveDetail, Line, 100);
        }
        else if (State == ELBFactoryMachineOperatingState::Starved
            && !Line->GetAssignedOrderId().IsNone())
        {
            AddAlert(ELBFactoryUIAlertSeverity::Information, Line->GetLineId(),
                TEXT("BODY WELD AWAITING INPUTS"), LiveDetail, Line, 100);
        }
    }

    for (TActorIterator<ALBECoatLineActor> It(World); It; ++It)
    {
        ALBECoatLineActor* Line = *It;
        if (!IsValid(Line)) continue;
        ++CachedSnapshot.OperationalAssetCount;
        ++CachedSnapshot.MachineCount;
        const ELBECoatOperatingState State = Line->GetOperatingState();
        SetProductionStage(TEXT("ED_COAT"), Line, ECoatStateName(State),
            FString::Printf(TEXT("%d carriers"), Line->GetCarrierCount()),
            State == ELBECoatOperatingState::Running,
            State == ELBECoatOperatingState::Paused
                || State == ELBECoatOperatingState::Starved
                || State == ELBECoatOperatingState::Maintenance,
            State == ELBECoatOperatingState::Faulted
                || State == ELBECoatOperatingState::EmergencyStop);
        if (State == ELBECoatOperatingState::Running) ++CachedSnapshot.RunningCount;
        if (State == ELBECoatOperatingState::Paused
            || State == ELBECoatOperatingState::Starved
            || State == ELBECoatOperatingState::Maintenance) ++CachedSnapshot.WaitingCount;
        if (State == ELBECoatOperatingState::Faulted
            || State == ELBECoatOperatingState::EmergencyStop)
        {
            ++CachedSnapshot.FaultCount;
            AddAlert(ELBFactoryUIAlertSeverity::Critical, Line->GetLineId(),
                State == ELBECoatOperatingState::EmergencyStop
                    ? TEXT("ED LINE EMERGENCY STOP") : TEXT("ED LINE FAULT"),
                Line->GetStateReason().IsNone() ? TEXT("INSPECT THE AFFECTED PROCESS BAY")
                    : Line->GetStateReason().ToString(), Line, 110);
        }
        else if (State == ELBECoatOperatingState::Starved
            && CachedSnapshot.Order.bHasActiveOrder)
        {
            AddAlert(ELBFactoryUIAlertSeverity::Information, Line->GetLineId(),
                TEXT("ED LINE AWAITING BODY SHELL"),
                Line->GetStateReason().IsNone() ? TEXT("BODY-WELD INPUT PORT HAS NO CARRIER")
                    : Line->GetStateReason().ToString(), Line, 110);
        }
    }

    for (TActorIterator<ALBPressShopStorageZone> It(World); It; ++It)
    {
        ALBPressShopStorageZone* Zone = *It;
        if (IsValid(Zone)
            && Zone->GetStorageType() == ELBPressShopStorageType::PreparedBlanks)
        {
            SetProductionStage(TEXT("BLANK_BUFFER"), Zone,
                Zone->IsBlocked() ? TEXT("FULL") : TEXT("READY"),
                FString::Printf(TEXT("%d / %d blanks"), Zone->GetOccupancy(),
                    Zone->GetCapacity()), false, Zone->GetOccupancy() == 0,
                false);
        }
        else if (IsValid(Zone)
            && Zone->GetStorageType() == ELBPressShopStorageType::FinishedPanelStillages)
        {
            SetProductionStage(TEXT("PANEL_STILLAGES"), Zone,
                Zone->IsBlocked() ? TEXT("FULL") : TEXT("READY"),
                FString::Printf(TEXT("%d / %d stillages"), Zone->GetOccupancy(),
                    Zone->GetCapacity()), false, Zone->GetOccupancy() == 0,
                false);
        }
        if (IsValid(Zone) && Zone->IsBlocked())
        {
            AddAlert(ELBFactoryUIAlertSeverity::Warning, Zone->GetZoneId(),
                TEXT("STORAGE FULL"), FString::Printf(TEXT("%d / %d UNITS"),
                    Zone->GetOccupancy(), Zone->GetCapacity()), Zone, 70);
        }
    }

    for (TActorIterator<ALBPressTrainAStation> It(World); It; ++It)
    {
        ALBPressTrainAStation* Train = *It;
        if (!IsValid(Train)) continue;
        ++CachedSnapshot.OperationalAssetCount;
        const FLBPressTrainAHMIStatus HMI = Train->GetHMIStatus();
        const bool bAwaitingFirstBlank = CachedSnapshot.Order.bHasActiveOrder
            && HMI.State == ELBPressTrainAState::Isolated
            && HMI.PendingBlankCount == 0;
        const FString PressState = bAwaitingFirstBlank
            ? TEXT("AWAITING BLANKS") : PressStateName(HMI.State);
        const FString PressDetail = bAwaitingFirstBlank
            ? TEXT("MATERIAL IS ROUTING TO THE PRESS")
            : (HMI.TargetStrokesPerMinute > 0.0f
                ? FString::Printf(TEXT("%.1f strokes/min"), HMI.TargetStrokesPerMinute)
                : TEXT("Awaiting production target"));
        SetProductionStage(TEXT("TRANSFER_PRESS"), Train,
            PressState, PressDetail,
            HMI.State == ELBPressTrainAState::Cycling,
            HMI.State == ELBPressTrainAState::Isolated
                || HMI.State == ELBPressTrainAState::Stopping,
            HMI.State == ELBPressTrainAState::Fault);
        if (CachedSnapshot.TargetStrokesPerMinute <= 0.0f)
            CachedSnapshot.TargetStrokesPerMinute = HMI.TargetStrokesPerMinute;
        if (HMI.State == ELBPressTrainAState::Fault)
        {
            ++CachedSnapshot.FaultCount;
            AddAlert(ELBFactoryUIAlertSeverity::Critical, Train->GetTrainId(),
                TEXT("PRESS TRAIN FAULT"), FString::Printf(TEXT("FAULT %d"),
                    static_cast<int32>(HMI.ActiveFault)), Train, 40);
        }
        else if (bAwaitingFirstBlank)
        {
            ++CachedSnapshot.WaitingCount;
            AddAlert(ELBFactoryUIAlertSeverity::Information, Train->GetTrainId(),
                TEXT("PRESS TRAIN AWAITING BLANKS"),
                TEXT("INBOUND MATERIAL IS ROUTING TO THE ASSIGNED TRAIN"), Train, 40);
        }
        else if (CachedSnapshot.Order.bHasActiveOrder && HMI.State == ELBPressTrainAState::Isolated)
        {
            ++CachedSnapshot.WaitingCount;
            AddAlert(ELBFactoryUIAlertSeverity::Warning, Train->GetTrainId(),
                TEXT("PRESS TRAIN ISOLATED"), TEXT("POWER AND START THE ASSIGNED TRAIN"), Train, 40);
        }
    }

    for (TActorIterator<ALBCoilAGVController> It(World); It; ++It)
    {
        ALBCoilAGVController* AGV = *It;
        if (!IsValid(AGV)) continue;
        ++CachedSnapshot.OperationalAssetCount;
        if (AGV->GetFault() != ELBCoilAGVFault::None)
        {
            ++CachedSnapshot.FaultCount;
            AddAlert(ELBFactoryUIAlertSeverity::Critical, AGV->GetFName(),
                TEXT("AGV FAULT"), FString::Printf(TEXT("FAULT %d"),
                    static_cast<int32>(AGV->GetFault())), AGV, 5);
        }
    }

    for (TActorIterator<ALBSupportRobot> It(World); It; ++It)
    {
        ALBSupportRobot* Robot = *It;
        if (!IsValid(Robot)) continue;
        ++CachedSnapshot.OperationalAssetCount;
        const FLBSupportRobotSaveState State = Robot->CaptureCommonSaveState();
        if (State.ActiveFault != ELBSupportRobotFault::None)
        {
            ++CachedSnapshot.FaultCount;
            AddAlert(ELBFactoryUIAlertSeverity::Critical, State.UnitId,
                TEXT("SUPPORT ROBOT FAULT"), Robot->GetLastCommonFaultDetail(), Robot, 80);
        }
    }

    // Management remains an exact, read-only projection here. The HUD never infers money,
    // research, wear or quality from scene appearance and never mutates the authority.
    if (ULBFactoryManagementSubsystem* Management =
        World->GetSubsystem<ULBFactoryManagementSubsystem>())
    {
        const FLBFactoryManagementSaveState Saved = Management->CaptureSaveState();
        FLBFactoryUIManagementSnapshot& Projection = CachedSnapshot.Management;
        Projection.bCampaignInitialised = Saved.bCampaignInitialised;
        if (Projection.bCampaignInitialised)
        {
            const FLBFactoryManagementSnapshot& Source = Management->GetSnapshot();
            Projection.Revision = Source.Revision;
            Projection.CashBalancePence = Source.CashBalancePence;
            Projection.AvailableResearchPoints = Source.AvailableResearchPoints;
            Projection.TotalResearchEarnedPoints = Source.TotalResearchEarnedPoints;
            Projection.TotalResearchSpentPoints = Source.TotalResearchSpentPoints;
            Projection.CapitalSpendPence = Source.CapitalSpendPence;
            Projection.OperatingSpendPence = Source.OperatingSpendPence;
            Projection.MaintenanceSpendPence = Source.MaintenanceSpendPence;
            Projection.UpgradeSpendPence = Source.UpgradeSpendPence;
            Projection.OrderRevenuePence = Source.OrderRevenuePence;
            Projection.CapitalAssetCount = Source.CapitalAssets.Num();
            Projection.UpgradeCount = Source.MachineUpgrades.Num();
            Projection.TrackedMaintenanceAssetCount = Source.MaintenanceByAsset.Num();
            Projection.AnalyticsBucketCount = Source.AnalyticsBuckets.Num();
            Projection.ProducedCount = Source.FactoryQualityTotals.ProducedCount;
            Projection.InspectedCount = Source.FactoryQualityTotals.InspectedCount;
            Projection.PassedCount = Source.FactoryQualityTotals.PassedCount;
            Projection.RejectedCount = Source.FactoryQualityTotals.RejectedCount;
            Projection.ReworkedCount = Source.FactoryQualityTotals.ReworkedCount;
            Projection.ScrappedCount = Source.FactoryQualityTotals.ScrappedCount;
            Projection.ThroughputGoodUnitsPerHour = Source.LifetimeKPIs.ThroughputGoodUnitsPerHour;
            Projection.StarvationRatio = Source.LifetimeKPIs.StarvationRatio;
            Projection.BlockingRatio = Source.LifetimeKPIs.BlockingRatio;
            Projection.FaultDowntimeRatio = Source.LifetimeKPIs.FaultDowntimeRatio;
            Projection.UtilisationRatio = Source.LifetimeKPIs.UtilisationRatio;
            Projection.AvailabilityRatio = Source.LifetimeKPIs.AvailabilityRatio;
            Projection.PerformanceRatio = Source.LifetimeKPIs.PerformanceRatio;
            Projection.QualityRatio = Source.LifetimeKPIs.QualityRatio;
            Projection.OEE = Source.LifetimeKPIs.OEE;
            Projection.ResearchUnlockIds = Source.ResearchUnlockIds;

            const auto FindOrAddAsset = [&Projection](const FName AssetId)
                -> FLBFactoryUIManagementAssetSnapshot&
            {
                if (FLBFactoryUIManagementAssetSnapshot* Existing =
                    Projection.Assets.FindByPredicate([AssetId](
                        const FLBFactoryUIManagementAssetSnapshot& Row)
                    {
                        return Row.AssetId == AssetId;
                    }))
                {
                    return *Existing;
                }
                FLBFactoryUIManagementAssetSnapshot& Added = Projection.Assets.AddDefaulted_GetRef();
                Added.AssetId = AssetId;
                return Added;
            };

            for (const FLBManagementQualityRecord& Quality : Source.QualityByAsset)
            {
                FLBFactoryUIManagementAssetSnapshot& Row = FindOrAddAsset(Quality.AssetId);
                Row.bHasQuality = true;
                Row.ProducedCount = Quality.ProducedCount;
                Row.PassedCount = Quality.PassedCount;
                Row.RejectedCount = Quality.RejectedCount;
                Row.ReworkedCount = Quality.ReworkedCount;
                Row.ScrappedCount = Quality.ScrappedCount;
            }
            for (const FLBManagementMaintenanceRecord& Maintenance : Source.MaintenanceByAsset)
            {
                FLBFactoryUIManagementAssetSnapshot& Row = FindOrAddAsset(Maintenance.AssetId);
                Row.bHasMaintenance = true;
                Row.bServiceDue = Maintenance.IsServiceDue();
                Row.bServicePlanned = Maintenance.bPlannedService;
                Row.bFaulted = Maintenance.bFaulted;
                Row.FaultCode = Maintenance.FaultCode;
                Row.WearFraction = Maintenance.WearFraction;
                Projection.ServiceDueCount += Row.bServiceDue ? 1 : 0;
                Projection.PlannedServiceCount += Row.bServicePlanned ? 1 : 0;
                Projection.ManagementFaultCount += Row.bFaulted ? 1 : 0;

                const bool bAlreadyCritical = CachedSnapshot.Alerts.ContainsByPredicate(
                    [&Maintenance](const FLBFactoryUIAlertSnapshot& Alert)
                    {
                        return Alert.EntityId == Maintenance.AssetId
                            && Alert.Severity == ELBFactoryUIAlertSeverity::Critical;
                    });
                AActor* Target = FindFactoryActorById(Maintenance.AssetId);
                if (Row.bFaulted && !bAlreadyCritical)
                {
                    ++CachedSnapshot.FaultCount;
                    AddAlert(ELBFactoryUIAlertSeverity::Critical, Maintenance.AssetId,
                        TEXT("ASSET FAULT"), Maintenance.FaultCode.IsNone()
                            ? TEXT("INSPECTION REQUIRED") : Maintenance.FaultCode.ToString(),
                        Target, 90);
                }
                else if (Row.bServiceDue && !Row.bFaulted)
                {
                    AddAlert(ELBFactoryUIAlertSeverity::Warning, Maintenance.AssetId,
                        Row.bServicePlanned ? TEXT("PLANNED SERVICE DUE") : TEXT("SERVICE DUE"),
                        FString::Printf(TEXT("WEAR %.0f%%"),
                            Maintenance.WearFraction * 100.0), Target, 90);
                }
            }
            for (const FLBManagementMachineUpgrade& Upgrade : Source.MachineUpgrades)
            {
                ++FindOrAddAsset(Upgrade.MachineId).UpgradeCount;
            }
            Projection.ResearchUnlockIds.Sort([](const FName A, const FName B)
            {
                return A.LexicalLess(B);
            });
            Projection.Assets.Sort([](const FLBFactoryUIManagementAssetSnapshot& A,
                const FLBFactoryUIManagementAssetSnapshot& B)
            {
                if (A.bFaulted != B.bFaulted) return A.bFaulted;
                if (A.bServiceDue != B.bServiceDue) return A.bServiceDue;
                if (!FMath::IsNearlyEqual(A.WearFraction, B.WearFraction))
                    return A.WearFraction > B.WearFraction;
                return A.AssetId.LexicalLess(B.AssetId);
            });
        }
    }

    if (!CachedSnapshot.Order.bHasActiveOrder
        && CachedSnapshot.OperationalAssetCount > 0)
    {
        CachedSnapshot.Order.Objective = TEXT("SCHEDULE THE NEXT PRODUCTION BATCH");
    }

    CachedSnapshot.BodyWeldLines.Sort([](const FLBFactoryUIBodyWeldLineSnapshot& A,
        const FLBFactoryUIBodyWeldLineSnapshot& B)
    {
        return A.LineId.LexicalLess(B.LineId);
    });

    CachedSnapshot.Alerts.Sort([](const FLBFactoryUIAlertSnapshot& A,
        const FLBFactoryUIAlertSnapshot& B)
    {
        const int32 SeverityA = SeverityRank(A.Severity);
        const int32 SeverityB = SeverityRank(B.Severity);
        if (SeverityA != SeverityB) return SeverityA < SeverityB;
        if (A.ProcessOrder != B.ProcessOrder) return A.ProcessOrder < B.ProcessOrder;
        return A.EntityId.LexicalLess(B.EntityId);
    });
}

bool ULBFactoryUIStateSubsystem::BuildInspectorSnapshot(const AActor* Actor,
    FLBFactoryUIInspectorSnapshot& OutSnapshot) const
{
    OutSnapshot = FLBFactoryUIInspectorSnapshot();
    if (!IsValid(Actor)) return false;

    OutSnapshot.WorldLocation = Actor->GetActorLocation();
    if (const ALBBodyWeldLineActor* Line = Cast<ALBBodyWeldLineActor>(Actor))
    {
        FLBBodyInWhiteRecord OutputBody;
        FLBBodyInWhiteRecord ReworkBody;
        const bool bHasOutput = Line->GetOutputBody(OutputBody);
        const bool bHasRework = Line->GetReworkBody(ReworkBody);
        OutSnapshot.bValid = true;
        OutSnapshot.EntityId = Line->GetLineId();
        OutSnapshot.Kind = TEXT("BODY WELD LINE");
        OutSnapshot.DisplayName = TEXT("BODY WELD / BIW ASSEMBLY");
        OutSnapshot.State = MachineStateName(Line->GetOperatingState());
        OutSnapshot.Reason = Line->GetOperatingReason();
        OutSnapshot.DetailLines = {
            FString::Printf(TEXT("PHASE  %s  |  %.0f%%"),
                *BodyWeldPhaseName(Line->GetPhase()), Line->GetPhaseProgress01() * 100.0f),
            FString::Printf(TEXT("ORDER  %s"), Line->GetAssignedOrderId().IsNone()
                ? TEXT("UNASSIGNED") : *Line->GetAssignedOrderId().ToString()),
            FString::Printf(TEXT("PANELS  %d AVAILABLE / %d RESERVED"),
                Line->GetAvailablePanelCount(), Line->GetReservedPanelCount()),
            FString::Printf(TEXT("BASE KITS  %d  |  EMPTY RETURNS  %d"),
                Line->GetAvailableBaseKitCount(), Line->GetPendingEmptyReturnCount()),
            FString::Printf(TEXT("OUTPUT  %s  |  REWORK  %s"),
                bHasOutput ? *OutputBody.BodyId.ToString() : TEXT("NONE"),
                bHasRework ? *ReworkBody.BodyId.ToString() : TEXT("NONE")),
            FString::Printf(TEXT("COMPLETED  %d  |  ED  %s"),
                Line->GetCompletedBodyCount(), Line->IsEDAvailable()
                    ? TEXT("AVAILABLE") : TEXT("UNAVAILABLE"))};
        AppendManagementInspectorData(OutSnapshot.EntityId, OutSnapshot);
        return true;
    }
    if (const ALBFactoryBuildMachine* Machine = Cast<ALBFactoryBuildMachine>(Actor))
    {
        OutSnapshot.bValid = true;
        OutSnapshot.EntityId = Machine->GetMachineId();
        OutSnapshot.Kind = TEXT("MACHINE");
        OutSnapshot.DisplayName = MachineTypeName(Machine->GetMachineType());
        OutSnapshot.State = MachineStateName(Machine->GetOperatingState());
        OutSnapshot.Reason = Machine->GetOperatingReason();
        OutSnapshot.DetailLines = {
            FString::Printf(TEXT("INPUT  %d / %d"), Machine->GetInputUnitCount(), Machine->GetMaximumInputBuffer()),
            FString::Printf(TEXT("OUTPUT  %d / %d"), Machine->GetOutputUnitCount(), Machine->GetMaximumOutputBuffer()),
            FString::Printf(TEXT("PROCESS  %d / %d"), Machine->GetCompletedAutomaticProcessSteps(), Machine->GetRequiredAutomaticProcessSteps()),
            FString::Printf(TEXT("COMPLETED  %d"), Machine->GetCompletedUnitCount())};
        AppendManagementInspectorData(OutSnapshot.EntityId, OutSnapshot);
        return true;
    }
    if (const ALBECoatLineActor* Line = Cast<ALBECoatLineActor>(Actor))
    {
        int32 FaultedBays = 0;
        int32 StarvedBays = 0;
        for (int32 BayIndex = 0; BayIndex < Line->GetBayCount(); ++BayIndex)
        {
            FLBECoatBayOperatingState BayState;
            if (!Line->GetBayOperatingState(BayIndex, BayState)) continue;
            FaultedBays += BayState.bFaulted ? 1 : 0;
            StarvedBays += BayState.bStarved ? 1 : 0;
        }
        OutSnapshot.bValid = true;
        OutSnapshot.EntityId = Line->GetLineId();
        OutSnapshot.Kind = TEXT("PAINT SHOP LINE");
        OutSnapshot.DisplayName = TEXT("ED / E-COAT TREATMENT + CURING");
        OutSnapshot.State = ECoatStateName(Line->GetOperatingState());
        OutSnapshot.Reason = Line->GetStateReason().IsNone()
            ? (Line->GetOperatingState() == ELBECoatOperatingState::Stopped
                ? TEXT("START WHEN A BODY-SHELL CARRIER IS AVAILABLE")
                : TEXT("PROCESS AUTHORITY HEALTHY"))
            : Line->GetStateReason().ToString();
        OutSnapshot.DetailLines = {
            FString::Printf(TEXT("OPEN TREATMENT TANKS  %d x 18 m"), Line->GetTreatmentBayCount()),
            FString::Printf(TEXT("CURING OVEN  72 m  |  CAPACITY  %d BODIES"), Line->GetOvenProcessBayCount()),
            FString::Printf(TEXT("CARRIERS  %d  |  TOTAL LINE  %.0f m"), Line->GetCarrierCount(), Line->GetTotalLengthCm() / 100.0f),
            FString::Printf(TEXT("BAY STATUS  %d FAULT / %d STARVED"), FaultedBays, StarvedBays)};
        AppendManagementInspectorData(OutSnapshot.EntityId, OutSnapshot);
        return true;
    }
    if (const ALBPressShopStorageZone* Zone = Cast<ALBPressShopStorageZone>(Actor))
    {
        OutSnapshot.bValid = true;
        OutSnapshot.EntityId = Zone->GetZoneId();
        OutSnapshot.Kind = TEXT("STORAGE");
        OutSnapshot.DisplayName = StorageTypeName(Zone->GetStorageType());
        OutSnapshot.State = Zone->IsBlocked() ? TEXT("FULL") : Zone->IsStarved() ? TEXT("EMPTY") : TEXT("AVAILABLE");
        OutSnapshot.Reason = Zone->IsBlocked() ? TEXT("NO FREE STORAGE POSITIONS")
            : Zone->IsStarved() ? TEXT("AWAITING MATERIAL") : TEXT("CAPACITY AVAILABLE");
        OutSnapshot.DetailLines = {
            FString::Printf(TEXT("OCCUPANCY  %d / %d"), Zone->GetOccupancy(), Zone->GetCapacity()),
            FString::Printf(TEXT("AVAILABLE  %d"), Zone->GetAvailableCapacity()),
            FString::Printf(TEXT("LAYOUT  %d x %d"), Zone->GetLayoutColumns(), Zone->GetLayoutRows()),
            FString::Printf(TEXT("REPLENISHMENT  %d LOADS"), Zone->GetOutstandingReplenishmentLoads())};
        AppendManagementInspectorData(OutSnapshot.EntityId, OutSnapshot);
        return true;
    }
    if (const ALBPressTrainAStation* Train = Cast<ALBPressTrainAStation>(Actor))
    {
        const FLBPressTrainAHMIStatus HMI = Train->GetHMIStatus();
        OutSnapshot.bValid = true;
        OutSnapshot.EntityId = Train->GetTrainId();
        OutSnapshot.Kind = TEXT("PRESS TRAIN");
        OutSnapshot.DisplayName = Train->GetTrainDisplayName();
        OutSnapshot.State = PressStateName(HMI.State);
        if (HMI.State == ELBPressTrainAState::Fault)
        {
            OutSnapshot.Reason = FString::Printf(TEXT("FAULT %d"),
                static_cast<int32>(HMI.ActiveFault));
        }
        else if (HMI.State == ELBPressTrainAState::Isolated)
        {
            OutSnapshot.Reason = TEXT("POWER AND START THE ASSIGNED TRAIN");
        }
        else if (HMI.State == ELBPressTrainAState::Stopping)
        {
            OutSnapshot.Reason = TEXT("CONTROLLED STOP IN PROGRESS");
        }
        else
        {
            OutSnapshot.Reason = TEXT("PROCESS AUTHORITY ONLINE");
        }
        OutSnapshot.DetailLines = {
            FString::Printf(TEXT("TARGET  %.1f SPM"), HMI.TargetStrokesPerMinute),
            FString::Printf(TEXT("CYCLE  %.0f%%"), HMI.CycleProgress * 100.0f),
            FString::Printf(TEXT("PANELS  %d GOOD / %d REJECT"), HMI.GoodPanels, HMI.RejectedPanels),
            FString::Printf(TEXT("BUFFERS  %d BLANK / %d PANEL"), HMI.PendingBlankCount, HMI.PendingPanelCount)};
        AppendManagementInspectorData(OutSnapshot.EntityId, OutSnapshot);
        return true;
    }
    if (const ALBCoilAGVController* AGV = Cast<ALBCoilAGVController>(Actor))
    {
        OutSnapshot.bValid = true;
        OutSnapshot.EntityId = AGV->GetFName();
        OutSnapshot.Kind = TEXT("AGV");
        OutSnapshot.DisplayName = TEXT("COIL TRANSFER AGV");
        OutSnapshot.State = CoilPhaseName(AGV->GetPhase());
        OutSnapshot.Reason = AGV->GetFault() == ELBCoilAGVFault::None
            ? TEXT("ROUTE AUTHORITY HEALTHY") : FString::Printf(TEXT("FAULT %d"), static_cast<int32>(AGV->GetFault()));
        OutSnapshot.DetailLines = {
            FString::Printf(TEXT("LOAD  %s"), AGV->OwnsLoad() ? TEXT("SECURED") : TEXT("EMPTY")),
            FString::Printf(TEXT("COIL  %s"), *AGV->GetActiveCoilId()),
            FString::Printf(TEXT("LIFT  %.0f cm"), AGV->GetLiftHeightCm()),
            FString::Printf(TEXT("ROUTE PROFILE  %d"), static_cast<int32>(AGV->GetRouteProfile()))};
        AppendManagementInspectorData(OutSnapshot.EntityId, OutSnapshot);
        return true;
    }
    if (const ALBSupportRobot* Robot = Cast<ALBSupportRobot>(Actor))
    {
        const FLBSupportRobotSaveState State = Robot->CaptureCommonSaveState();
        OutSnapshot.bValid = true;
        OutSnapshot.EntityId = State.UnitId;
        OutSnapshot.Kind = TEXT("SUPPORT ROBOT");
        OutSnapshot.DisplayName = State.VariantId.ToString();
        OutSnapshot.State = FString::Printf(TEXT("STATE %d"), static_cast<int32>(State.State));
        OutSnapshot.Reason = State.ActiveFault == ELBSupportRobotFault::None
            ? TEXT("READY") : Robot->GetLastCommonFaultDetail();
        OutSnapshot.DetailLines = {
            FString::Printf(TEXT("BATTERY  %.0f%%"), State.BatteryStateOfChargePercent),
            FString::Printf(TEXT("MISSIONS  %d"), State.MissionCount),
            FString::Printf(TEXT("DOCK  %s"), *State.DockId.ToString()),
            FString::Printf(TEXT("TASK  %s"), *State.ActiveTaskId.ToString())};
        AppendManagementInspectorData(OutSnapshot.EntityId, OutSnapshot);
        return true;
    }
    return false;
}

void ULBFactoryUIStateSubsystem::AppendManagementInspectorData(
    const FName EntityId, FLBFactoryUIInspectorSnapshot& InOutSnapshot) const
{
    const UWorld* World = GetWorld();
    const ULBFactoryManagementSubsystem* Management = World
        ? World->GetSubsystem<ULBFactoryManagementSubsystem>() : nullptr;
    if (!Management || !Management->CaptureSaveState().bCampaignInitialised
        || EntityId.IsNone())
    {
        return;
    }

    const FLBFactoryManagementSnapshot& Source = Management->GetSnapshot();
    if (const FLBManagementMaintenanceRecord* Maintenance =
        Source.MaintenanceByAsset.FindByPredicate([EntityId](
            const FLBManagementMaintenanceRecord& Record)
        {
            return Record.AssetId == EntityId;
        }))
    {
        InOutSnapshot.bHasMaintenance = true;
        InOutSnapshot.bServiceDue = Maintenance->IsServiceDue();
        InOutSnapshot.bServicePlanned = Maintenance->bPlannedService;
        InOutSnapshot.bManagementFaulted = Maintenance->bFaulted;
        InOutSnapshot.FaultCode = Maintenance->FaultCode;
        InOutSnapshot.WearFraction = Maintenance->WearFraction;
        InOutSnapshot.DetailLines.Add(FString::Printf(TEXT("WEAR  %.0f%%  |  SERVICE %s"),
            Maintenance->WearFraction * 100.0,
            Maintenance->IsServiceDue()
                ? (Maintenance->bPlannedService ? TEXT("DUE / PLANNED") : TEXT("DUE"))
                : TEXT("OK")));
        if (Maintenance->bFaulted)
        {
            InOutSnapshot.DetailLines.Add(FString::Printf(TEXT("FAULT  %s"),
                Maintenance->FaultCode.IsNone()
                    ? TEXT("INSPECTION REQUIRED") : *Maintenance->FaultCode.ToString()));
        }
    }
    if (const FLBManagementQualityRecord* Quality =
        Source.QualityByAsset.FindByPredicate([EntityId](
            const FLBManagementQualityRecord& Record)
        {
            return Record.AssetId == EntityId;
        }))
    {
        InOutSnapshot.bHasQuality = true;
        InOutSnapshot.ProducedCount = Quality->ProducedCount;
        InOutSnapshot.PassedCount = Quality->PassedCount;
        InOutSnapshot.RejectedCount = Quality->RejectedCount;
        InOutSnapshot.ReworkedCount = Quality->ReworkedCount;
        InOutSnapshot.ScrappedCount = Quality->ScrappedCount;
        InOutSnapshot.DetailLines.Add(FString::Printf(
            TEXT("QUALITY  %lld PASS / %lld REJECT / %lld SCRAP"),
            Quality->PassedCount, Quality->RejectedCount, Quality->ScrappedCount));
    }
    for (const FLBManagementMachineUpgrade& Upgrade : Source.MachineUpgrades)
    {
        if (Upgrade.MachineId != EntityId) continue;
        ++InOutSnapshot.UpgradeCount;
        const FString Line = FString::Printf(TEXT("UPGRADE  %s  L%d"),
            *Upgrade.UpgradeId.ToString(), Upgrade.Level);
        InOutSnapshot.UpgradeLines.Add(Line);
        InOutSnapshot.DetailLines.Add(Line);
    }
}

AActor* ULBFactoryUIStateSubsystem::FindFactoryActorById(const FName EntityId) const
{
    UWorld* World = GetWorld();
    if (!World || EntityId.IsNone()) return nullptr;
    for (TActorIterator<ALBFactoryBuildMachine> It(World); It; ++It)
        if (It->GetMachineId() == EntityId) return *It;
    for (TActorIterator<ALBPressShopStorageZone> It(World); It; ++It)
        if (It->GetZoneId() == EntityId) return *It;
    for (TActorIterator<ALBPressTrainAStation> It(World); It; ++It)
        if (It->GetTrainId() == EntityId) return *It;
    for (TActorIterator<ALBSupportRobot> It(World); It; ++It)
        if (It->CaptureCommonSaveState().UnitId == EntityId) return *It;
    for (TActorIterator<ALBCoilAGVController> It(World); It; ++It)
        if (It->GetFName() == EntityId) return *It;
    for (TActorIterator<ALBBodyWeldLineActor> It(World); It; ++It)
        if (It->GetLineId() == EntityId) return *It;
    for (TActorIterator<ALBECoatLineActor> It(World); It; ++It)
        if (It->GetLineId() == EntityId) return *It;
    return nullptr;
}
