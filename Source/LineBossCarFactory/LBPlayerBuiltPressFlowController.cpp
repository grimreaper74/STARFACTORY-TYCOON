#include "LBPlayerBuiltPressFlowController.h"

#include "EngineUtils.h"
#include "LBECoatLineActor.h"
#include "LBFactoryBuildMachine.h"
#include "LBFactoryTransportLink.h"
#include "LBPressShopStorageZone.h"
#include "LBPressTrainAStation.h"
#include "LBStillageFLTFleetController.h"
#include "LBVehiclePanelCatalog.h"

ALBPlayerBuiltPressFlowController::ALBPlayerBuiltPressFlowController()
{
    PrimaryActorTick.bCanEverTick = true;
    PrimaryActorTick.TickInterval = 0.1f;
}

void ALBPlayerBuiltPressFlowController::BeginPlay()
{
    Super::BeginPlay();
    BindKnownPressTrains();
    BindKnownStillageFleets();
}

void ALBPlayerBuiltPressFlowController::BindKnownPressTrains()
{
    if (!GetWorld()) return;
    for (TActorIterator<ALBPressTrainAStation> It(GetWorld()); It; ++It)
    {
        if (IsValid(*It))
            It->OnPanelCompleted.AddUniqueDynamic(
                this, &ALBPlayerBuiltPressFlowController::HandlePressPanelCompleted);
    }
}

void ALBPlayerBuiltPressFlowController::BindKnownStillageFleets()
{
    if (!GetWorld()) return;
    for (TActorIterator<ALBStillageFLTFleetController> It(GetWorld()); It; ++It)
    {
        if (IsValid(*It))
        {
            It->OnStillageDelivered.AddUniqueDynamic(
                this, &ALBPlayerBuiltPressFlowController::HandleStillageFleetDelivered);
        }
    }
}

ALBStillageFLTFleetController* ALBPlayerBuiltPressFlowController::FindStillageFleet() const
{
    if (!GetWorld()) return nullptr;
    ALBStillageFLTFleetController* Selected = nullptr;
    for (TActorIterator<ALBStillageFLTFleetController> It(GetWorld()); It; ++It)
    {
        if (!IsValid(*It)) continue;
        if (!Selected || It->GetFName().LexicalLess(Selected->GetFName())) Selected = *It;
    }
    return Selected;
}

bool ALBPlayerBuiltPressFlowController::HasOutstandingStillageJob(
    const FName StillageId) const
{
    if (StillageId.IsNone() || !GetWorld()) return false;
    for (TActorIterator<ALBStillageFLTFleetController> It(GetWorld()); It; ++It)
    {
        if (IsValid(*It) && It->HasOutstandingJobForStillage(StillageId)) return true;
    }
    return false;
}

ALBPressShopStorageZone* ALBPlayerBuiltPressFlowController::FindStorageByAuthorityId(
    const FName AuthorityId) const
{
    if (AuthorityId.IsNone() || !GetWorld()) return nullptr;
    ALBPressShopStorageZone* Match = nullptr;
    for (TActorIterator<ALBPressShopStorageZone> It(GetWorld()); It; ++It)
    {
        if (!IsValid(*It) || It->GetZoneId() != AuthorityId) continue;
        if (Match) return nullptr;
        Match = *It;
    }
    return Match;
}

ALBFactoryBuildMachine* ALBPlayerBuiltPressFlowController::FindMachineByAuthorityId(
    const FName AuthorityId) const
{
    if (AuthorityId.IsNone() || !GetWorld()) return nullptr;
    ALBFactoryBuildMachine* Match = nullptr;
    for (TActorIterator<ALBFactoryBuildMachine> It(GetWorld()); It; ++It)
    {
        if (!IsValid(*It) || It->GetMachineId() != AuthorityId) continue;
        if (Match) return nullptr;
        Match = *It;
    }
    return Match;
}

ALBBodyWeldLineActor* ALBPlayerBuiltPressFlowController::FindBodyWeldLineByAuthorityId(
    const FName AuthorityId) const
{
    if (AuthorityId.IsNone() || !GetWorld()) return nullptr;
    ALBBodyWeldLineActor* Match = nullptr;
    for (TActorIterator<ALBBodyWeldLineActor> It(GetWorld()); It; ++It)
    {
        if (!IsValid(*It) || It->GetLineId() != AuthorityId) continue;
        if (Match) return nullptr;
        Match = *It;
    }
    return Match;
}

ALBFactoryTransportLink* ALBPlayerBuiltPressFlowController::FindExactLink(
    const ULBFactoryProcessPortComponent* SourcePort,
    const ULBFactoryProcessPortComponent* TargetPort) const
{
    if (!SourcePort || !TargetPort || !GetWorld()) return nullptr;
    ALBFactoryTransportLink* Match = nullptr;
    for (TActorIterator<ALBFactoryTransportLink> It(GetWorld()); It; ++It)
    {
        ALBFactoryTransportLink* Link = *It;
        if (!IsValid(Link) || Link->GetSourcePort() != SourcePort
            || Link->GetTargetPort() != TargetPort) continue;
        if (Match) return nullptr;
        Match = Link;
    }
    return Match;
}

bool ALBPlayerBuiltPressFlowController::IsAuthoritativeFleetDelivery(
    const FName JobId, const FName StillageId, const ELBStillageFLTJobType JobType,
    const FName SourceAuthorityId, const FName TargetAuthorityId,
    FLBStillageFLTJob& OutJob) const
{
    OutJob = FLBStillageFLTJob();
    if (JobId.IsNone() || StillageId.IsNone() || !GetWorld()) return false;
    bool bFound = false;
    for (TActorIterator<ALBStillageFLTFleetController> It(GetWorld()); It; ++It)
    {
        FLBStillageFLTJob Job;
        if (!IsValid(*It) || !It->GetJobSnapshot(JobId, Job)) continue;
        if (bFound || Job.StillageId != StillageId || Job.JobType != JobType
            || Job.SourceAuthorityId != SourceAuthorityId
            || Job.TargetAuthorityId != TargetAuthorityId
            || (Job.State != ELBStillageFLTJobState::DeliveredReturning
                && Job.State != ELBStillageFLTJobState::Completed)) return false;
        OutJob = Job;
        bFound = true;
    }
    return bFound;
}

void ALBPlayerBuiltPressFlowController::ReconcileStillageFleetDeliveries()
{
    if (!GetWorld()) return;
    TArray<FLBStillageFLTJob> Delivered;
    for (TActorIterator<ALBStillageFLTFleetController> It(GetWorld()); It; ++It)
    {
        if (!IsValid(*It)) continue;
        for (const FLBStillageFLTJob& Job : It->GetJobSnapshots())
            if (Job.State == ELBStillageFLTJobState::DeliveredReturning
                || Job.State == ELBStillageFLTJobState::Completed)
                Delivered.Add(Job);
    }
    Delivered.Sort([](const FLBStillageFLTJob& Left, const FLBStillageFLTJob& Right)
    {
        if (Left.CreatedSequence != Right.CreatedSequence)
            return Left.CreatedSequence < Right.CreatedSequence;
        return Left.JobId.LexicalLess(Right.JobId);
    });
    for (const FLBStillageFLTJob& Job : Delivered)
        HandleStillageFleetDelivered(Job.JobId, Job.StillageId, Job.JobType,
            Job.SourceAuthorityId, Job.TargetAuthorityId);
}

bool ALBPlayerBuiltPressFlowController::QueueBodyWeldBaseKitDelivery(
    const FLBBodyWeldBaseKitUnit& BaseKit, const FName DeliveryAuthorityId,
    const FName TargetWeldLineId, FString& OutReason)
{
    OutReason.Reset();
    if (BaseKit.KitId.IsNone() || BaseKit.OrderId.IsNone()
        || BaseKit.KitTypeId != ALBBodyWeldLineActor::GetBaseKitTypeId()
        || BaseKit.VehicleModelId != ALBBodyWeldLineActor::GetVehicleModelId()
        || BaseKit.bReserved || BaseKit.bConsumed || DeliveryAuthorityId.IsNone()
        || TargetWeldLineId.IsNone())
    {
        OutReason = TEXT("FINITE BASE KIT REQUIRES EXACT IDS AND STAGE-9 DELIVERY AUTHORITIES");
        return false;
    }
    const auto HasKitId = [&BaseKit](const FLBBodyWeldBaseKitDeliveryRecord& Existing)
        { return Existing.BaseKit.KitId == BaseKit.KitId; };
    if (PendingBaseKitDeliveries.ContainsByPredicate(HasKitId)
        || TransferredBaseKitDeliveries.ContainsByPredicate(HasKitId))
    {
        OutReason = TEXT("BASE KIT ID ALREADY EXISTS IN THE DELIVERY LEDGER");
        return false;
    }
    FLBBodyWeldBaseKitDeliveryRecord& Delivery = PendingBaseKitDeliveries.AddDefaulted_GetRef();
    Delivery.BaseKit = BaseKit;
    Delivery.BaseKit.DeliverySequence = NextBodyWeldDeliverySequence++;
    Delivery.DeliveryAuthorityId = DeliveryAuthorityId;
    Delivery.TargetWeldLineId = TargetWeldLineId;
    OutReason = FString::Printf(TEXT("FINITE BASE KIT %s QUEUED AT ADAPTER %s"),
        *BaseKit.KitId.ToString(), *DeliveryAuthorityId.ToString());
    return true;
}

bool ALBPlayerBuiltPressFlowController::QueuePanelBatch(
    const FLBVehiclePanelBatch& Batch, FString& OutReason)
{
    if (!LBCairnwell2040PanelCatalog::IsApprovedStampedRecipe(
            Batch.VehicleModelId, Batch.PanelTypeId)
        || Batch.RequestedQuantity <= 0)
    {
        OutReason = TEXT("SELECT AN APPROVED CAIRNWELL 2040 STAMPED PANEL AND A POSITIVE QUANTITY");
        return false;
    }
    FLBVehiclePanelBatch Copy = Batch;
    Copy.DispatchedQuantity = 0;
    if (Copy.OrderId.IsNone())
        Copy.OrderId = FName(*FString::Printf(TEXT("ORDER-%s-%04d"),
            *Copy.VehicleModelId.ToString(), PanelBatches.Num() + 1));
    if (PanelBatches.ContainsByPredicate([&Copy](const FLBVehiclePanelBatch& Existing)
        {
            return Existing.OrderId == Copy.OrderId
                && Existing.VehicleModelId == Copy.VehicleModelId
                && Existing.PanelTypeId == Copy.PanelTypeId;
        }))
    {
        OutReason = TEXT("THIS ORDER ALREADY CONTAINS THAT PANEL FAMILY");
        return false;
    }
    PanelBatches.Add(Copy);
    OutReason = FString::Printf(TEXT("QUEUED %d x %s FOR %s"), Copy.RequestedQuantity,
        *Copy.PanelTypeId.ToString(), *Copy.VehicleModelId.ToString());
    return true;
}

FLBPlayerBuiltPressFlowSaveState ALBPlayerBuiltPressFlowController::CaptureSaveState() const
{
    FLBPlayerBuiltPressFlowSaveState State;
    State.PanelBatches = PanelBatches;
    State.PanelLineage = PanelLineage;
    State.PanelStillages = PanelStillages;
    State.PendingBaseKitDeliveries = PendingBaseKitDeliveries;
    State.TransferredBaseKitDeliveries = TransferredBaseKitDeliveries;
    State.NextStillageSerial = NextStillageSerial;
    State.NextBodyWeldDeliverySequence = NextBodyWeldDeliverySequence;
    State.bAutomaticFlowEnabled = bAutomaticFlowEnabled;
    return State;
}

bool ALBPlayerBuiltPressFlowController::ValidateSaveState(
    const FLBPlayerBuiltPressFlowSaveState& State, FString& OutReason)
{
    OutReason = TEXT("INVALID PLAYER-BUILT PRESS/WELD FLOW SAVE CONTRACT");
    if (State.Version < 1 || State.Version > 4 || State.NextStillageSerial <= 0
        || (State.Version >= 4 && State.NextBodyWeldDeliverySequence <= 0)) return false;
    TSet<FString> BatchKeys;
    for (const FLBVehiclePanelBatch& Batch : State.PanelBatches)
    {
        const FString BatchKey = FString::Printf(TEXT("%s|%s|%s"),
            *Batch.OrderId.ToString(), *Batch.VehicleModelId.ToString(),
            *Batch.PanelTypeId.ToString());
        if (Batch.OrderId.IsNone()
            || !LBCairnwell2040PanelCatalog::IsApprovedStampedRecipe(
                Batch.VehicleModelId, Batch.PanelTypeId)
            || Batch.RequestedQuantity <= 0 || Batch.DispatchedQuantity < 0
            || Batch.DispatchedQuantity > Batch.RequestedQuantity || BatchKeys.Contains(BatchKey)) return false;
        BatchKeys.Add(BatchKey);
    }

    const auto HasMatchingBatch = [&State](const FName OrderId, const FName VehicleModelId,
        const FName PanelTypeId)
    {
        return State.PanelBatches.ContainsByPredicate(
            [OrderId, VehicleModelId, PanelTypeId](const FLBVehiclePanelBatch& Batch)
            {
                return Batch.OrderId == OrderId && Batch.VehicleModelId == VehicleModelId
                    && Batch.PanelTypeId == PanelTypeId;
            });
    };

    TSet<FName> PanelIds;
    for (const FLBPanelLineageRecord& Panel : State.PanelLineage)
    {
        if (Panel.OrderId.IsNone() || Panel.BlankId.IsNone()
            || !HasMatchingBatch(Panel.OrderId, Panel.VehicleModelId, Panel.PanelTypeId)
            || !LBCairnwell2040PanelCatalog::IsApprovedStampedRecipe(
                Panel.VehicleModelId, Panel.PanelTypeId)
            || Panel.Disposition > ELBPanelDisposition::Rejected
            || !StaticEnum<ELBPanelFlowStage>()->IsValidEnumValue(
                static_cast<int64>(Panel.Stage))
            || (!Panel.PanelId.IsNone() && PanelIds.Contains(Panel.PanelId))) return false;
        if (!Panel.PanelId.IsNone()) PanelIds.Add(Panel.PanelId);
        const bool bRequiresStillage = Panel.Stage == ELBPanelFlowStage::WIPStillage
            || Panel.Stage == ELBPanelFlowStage::WeldShopIntake
            || Panel.Stage == ELBPanelFlowStage::BodyWeldInventory;
        if (bRequiresStillage && Panel.StillageId.IsNone()) return false;
        if (Panel.Disposition == ELBPanelDisposition::Rejected
            && Panel.Stage != ELBPanelFlowStage::Rejected) return false;
    }

    TSet<FName> StillageIds;
    TSet<FName> PackedPanelIds;
    TSet<FName> WeldDeliveryJobIds;
    TSet<FName> EmptyReturnJobIds;
    int64 MaximumDeliverySequence = 0;
    for (const FLBPanelStillageLoad& Load : State.PanelStillages)
    {
        const FLBStampedPanelDefinition* Definition = LBCairnwell2040PanelCatalog::Find(
            Load.VehicleModelId, Load.PanelTypeId);
        if (Load.StillageId.IsNone() || Load.OrderId.IsNone()
            || !HasMatchingBatch(Load.OrderId, Load.VehicleModelId, Load.PanelTypeId) || !Definition
            || StillageIds.Contains(Load.StillageId)
            || Load.CapacityPanels != Definition->StillageCapacity
            || Load.PanelIds.IsEmpty() || Load.PanelIds.Num() > Load.CapacityPanels
            || (Load.bDeliveredToWeld && !Load.bReadyForWeld)
            || (Load.bAcceptedByBodyWeld && (!Load.bDeliveredToWeld || Load.WeldLineId.IsNone()))
            || (!Load.bDeliveredToWeld && (!Load.WeldLineId.IsNone()
                || !Load.WeldDeliveryJobId.IsNone() || Load.WeldDeliverySequence != 0
                || Load.bAcceptedByBodyWeld))
            || (Load.bAcceptedByBodyWeld && Load.WeldDeliverySequence <= 0)
            || (!Load.bAcceptedByBodyWeld && Load.WeldDeliverySequence != 0)
            || (!Load.bAcceptedByBodyWeld && Load.bDeliveredToWeld
                && (Load.WeldLineId.IsNone() != Load.WeldDeliveryJobId.IsNone()))
            || (Load.bEmptyReturnQueued && (!Load.bAcceptedByBodyWeld
                || Load.EmptyReturnJobId.IsNone() || Load.bReturnedEmpty))
            || (!Load.bEmptyReturnQueued && !Load.bReturnedEmpty
                && !Load.EmptyReturnJobId.IsNone())
            || (Load.bReturnedEmpty && (!Load.bDeliveredToWeld
                || Load.bEmptyReturnQueued))
            || (State.Version < 4 && (!Load.WeldLineId.IsNone()
                || !Load.WeldDeliveryJobId.IsNone() || Load.WeldDeliverySequence != 0
                || Load.bAcceptedByBodyWeld || !Load.EmptyReturnJobId.IsNone()
                || Load.bEmptyReturnQueued))) return false;
        if ((!Load.WeldDeliveryJobId.IsNone()
                && (WeldDeliveryJobIds.Contains(Load.WeldDeliveryJobId)
                    || EmptyReturnJobIds.Contains(Load.WeldDeliveryJobId)))
            || (!Load.EmptyReturnJobId.IsNone()
                && (WeldDeliveryJobIds.Contains(Load.EmptyReturnJobId)
                    || EmptyReturnJobIds.Contains(Load.EmptyReturnJobId)))) return false;
        if (!Load.WeldDeliveryJobId.IsNone()) WeldDeliveryJobIds.Add(Load.WeldDeliveryJobId);
        if (!Load.EmptyReturnJobId.IsNone()) EmptyReturnJobIds.Add(Load.EmptyReturnJobId);
        MaximumDeliverySequence = FMath::Max(
            MaximumDeliverySequence, Load.WeldDeliverySequence);
        StillageIds.Add(Load.StillageId);
        for (const FName PanelId : Load.PanelIds)
        {
            const FLBPanelLineageRecord* Panel = State.PanelLineage.FindByPredicate(
                [PanelId](const FLBPanelLineageRecord& Candidate)
                { return Candidate.PanelId == PanelId; });
            if (PanelId.IsNone() || PackedPanelIds.Contains(PanelId) || !Panel
                || Panel->Disposition != ELBPanelDisposition::Good
                || Panel->StillageId != Load.StillageId
                || Panel->OrderId != Load.OrderId
                || Panel->VehicleModelId != Load.VehicleModelId
                || Panel->PanelTypeId != Load.PanelTypeId
                || (Load.bAcceptedByBodyWeld
                    && Panel->Stage != ELBPanelFlowStage::BodyWeldInventory)
                || (!Load.bAcceptedByBodyWeld && Load.bDeliveredToWeld
                    && Panel->Stage != ELBPanelFlowStage::WeldShopIntake)
                || (!Load.bDeliveredToWeld
                    && Panel->Stage != ELBPanelFlowStage::WIPStillage)) return false;
            PackedPanelIds.Add(PanelId);
        }
    }

    TSet<FName> KitIds;
    const auto ValidateBaseKitDelivery = [&KitIds, &MaximumDeliverySequence](
        const FLBBodyWeldBaseKitDeliveryRecord& Delivery, const bool bExpectTransferred)
    {
        const FLBBodyWeldBaseKitUnit& Kit = Delivery.BaseKit;
        if (Kit.KitId.IsNone() || KitIds.Contains(Kit.KitId) || Kit.OrderId.IsNone()
            || Kit.KitTypeId != ALBBodyWeldLineActor::GetBaseKitTypeId()
            || Kit.VehicleModelId != ALBBodyWeldLineActor::GetVehicleModelId()
            || Kit.DeliverySequence <= 0 || Kit.bReserved || Kit.bConsumed
            || Delivery.DeliveryAuthorityId.IsNone() || Delivery.TargetWeldLineId.IsNone()
            || Delivery.bTransferred != bExpectTransferred) return false;
        KitIds.Add(Kit.KitId);
        MaximumDeliverySequence = FMath::Max(MaximumDeliverySequence, Kit.DeliverySequence);
        return true;
    };
    if (State.Version < 4
        && (!State.PendingBaseKitDeliveries.IsEmpty()
            || !State.TransferredBaseKitDeliveries.IsEmpty())) return false;
    for (const FLBBodyWeldBaseKitDeliveryRecord& Delivery : State.PendingBaseKitDeliveries)
        if (!ValidateBaseKitDelivery(Delivery, false)) return false;
    for (const FLBBodyWeldBaseKitDeliveryRecord& Delivery : State.TransferredBaseKitDeliveries)
        if (!ValidateBaseKitDelivery(Delivery, true)) return false;
    if (State.Version >= 4 && State.NextBodyWeldDeliverySequence <= MaximumDeliverySequence)
        return false;

    OutReason.Reset();
    return true;
}

bool ALBPlayerBuiltPressFlowController::IsSaveStateContractValid(
    const FLBPlayerBuiltPressFlowSaveState& State, FString& OutReason)
{
    return ValidateSaveState(State, OutReason);
}

bool ALBPlayerBuiltPressFlowController::RestoreSaveState(
    const FLBPlayerBuiltPressFlowSaveState& State)
{
    FString ValidationReason;
    if (!ValidateSaveState(State, ValidationReason)) return false;
    PanelBatches = State.PanelBatches;
    PanelLineage = State.Version >= 2 ? State.PanelLineage : TArray<FLBPanelLineageRecord>();
    PanelStillages = State.Version >= 2 ? State.PanelStillages : TArray<FLBPanelStillageLoad>();
    PendingBaseKitDeliveries = State.Version >= 4
        ? State.PendingBaseKitDeliveries : TArray<FLBBodyWeldBaseKitDeliveryRecord>();
    TransferredBaseKitDeliveries = State.Version >= 4
        ? State.TransferredBaseKitDeliveries : TArray<FLBBodyWeldBaseKitDeliveryRecord>();
    NextStillageSerial = State.Version >= 2 ? State.NextStillageSerial : 1;
    NextBodyWeldDeliverySequence = State.Version >= 4
        ? State.NextBodyWeldDeliverySequence : 1;
    bAutomaticFlowEnabled = State.bAutomaticFlowEnabled;
    BindKnownPressTrains();
    BindKnownStillageFleets();
    return true;
}

FName ALBPlayerBuiltPressFlowController::GetProductionLineIdForTrain(
    const ALBPressTrainAStation* Train) const
{
    if (!Train || !GetWorld()) return NAME_None;
    for (TActorIterator<ALBFactoryTransportLink> It(GetWorld()); It; ++It)
    {
        const ALBFactoryTransportLink* Link = *It;
        if (!Link || !Link->GetSourcePort() || !Link->GetTargetPort()
            || Link->GetTargetPort()->GetOwner() != Train) continue;
        const AActor* Source = Link->GetSourcePort()->GetOwner();
        if (const ALBPressShopStorageZone* Storage = Cast<ALBPressShopStorageZone>(Source))
            return Storage->GetZoneId();
        return Source ? FName(*Source->GetName()) : NAME_None;
    }
    return NAME_None;
}

FLBVehiclePanelBatch* ALBPlayerBuiltPressFlowController::SelectBatchForTrain(
    const ALBPressTrainAStation* Train, const AActor* BlankSource)
{
    if (!Train) return nullptr;
    FName LineId = NAME_None;
    if (const ALBPressShopStorageZone* Storage = Cast<ALBPressShopStorageZone>(BlankSource))
        LineId = Storage->GetZoneId();
    else if (BlankSource) LineId = FName(*BlankSource->GetName());
    for (FLBVehiclePanelBatch& Batch : PanelBatches)
    {
        if (Batch.DispatchedQuantity >= Batch.RequestedQuantity) continue;
        if (!Batch.DedicatedTrainId.IsNone() && Batch.DedicatedTrainId != Train->GetTrainId()) continue;
        if (!Batch.ProductionLineId.IsNone() && Batch.ProductionLineId != LineId) continue;
        return &Batch;
    }
    return nullptr;
}

void ALBPlayerBuiltPressFlowController::Tick(const float DeltaSeconds)
{
    Super::Tick(DeltaSeconds);
    BindKnownPressTrains();
    BindKnownStillageFleets();
    if (!bAutomaticFlowEnabled) return;
    AutomaticStepAccumulator += DeltaSeconds;
    if (AutomaticStepAccumulator < AutomaticStepIntervalSeconds) return;
    AutomaticStepAccumulator = FMath::Fmod(AutomaticStepAccumulator, AutomaticStepIntervalSeconds);
    ExecuteAutomaticStep(LastAutomaticFlowSummary);
}

bool ALBPlayerBuiltPressFlowController::RecordLinkedTransfer(
    const AActor* Source, const AActor* Target, FString& OutReason) const
{
    if (!Source || !Target || !GetWorld()) return false;
    for (TActorIterator<ALBFactoryTransportLink> It(GetWorld()); It; ++It)
    {
        ALBFactoryTransportLink* Link = *It;
        if (Link && Link->GetSourcePort() && Link->GetTargetPort()
            && Link->GetSourcePort()->GetOwner() == Source && Link->GetTargetPort()->GetOwner() == Target)
        {
            if (!Link->TryTransferUnits(1)) return false;
            OutReason = FString::Printf(TEXT("%s MOVED TO %s"), *Source->GetName(), *Target->GetName());
            return true;
        }
    }
    OutReason = TEXT("NO VALID AUTOMATIC TRANSPORT LINK JOINS THESE PROCESS ENDPOINTS");
    return false;
}

bool ALBPlayerBuiltPressFlowController::TransferMachineOutputToStorage(
    ALBFactoryBuildMachine* Source, ALBPressShopStorageZone* Target, FString& OutReason)
{
    if (!Source || !Target) return false;
    if (Source->GetMachineType() == ELBFactoryBuildMachineType::InspectionCell
        && Target->GetStorageType() == ELBPressShopStorageType::FinishedPanelStillages)
    {
        return PackInspectedPanelIntoStillage(Source, Target, OutReason);
    }
    const FLBFactoryBuildMachineSaveState SourceBefore = Source->CaptureSaveState();
    const FLBPressShopStorageZoneSaveState TargetBefore = Target->CaptureSaveState();
    FName UnitId;
    if (!Source->ReleaseOutputUnit(UnitId) || !Target->TryStoreIdentifiedUnit(UnitId)
        || !RecordLinkedTransfer(Source, Target, OutReason))
    {
        Source->RestoreSaveState(SourceBefore);
        Target->RestoreSaveState(TargetBefore);
        if (OutReason.IsEmpty()) OutReason = TEXT("MACHINE-TO-STORAGE TRANSFER WAS REJECTED");
        return false;
    }
    return true;
}

bool ALBPlayerBuiltPressFlowController::TransferStorageToMachine(
    ALBPressShopStorageZone* Source, ALBFactoryBuildMachine* Target, FString& OutReason)
{
    if (!Source || !Target) return false;
    if (Source->GetStorageType() == ELBPressShopStorageType::FinishedPanelStillages
        && Target->GetMachineType() == ELBFactoryBuildMachineType::OutboundPanelDock)
    {
        BindKnownStillageFleets();
        if (FindStillageFleet())
        {
            // A commissioned FLT owns this route. Inventory remains in the full-WIP
            // authority until the physical drop-off delegate commits the handoff.
            return EnqueueReadyStillageTransfer(Source, Target, OutReason);
        }
    }
    const FLBPressShopStorageZoneSaveState SourceBefore = Source->CaptureSaveState();
    const FLBFactoryBuildMachineSaveState TargetBefore = Target->CaptureSaveState();
    const TArray<FLBPanelLineageRecord> LineageBefore = PanelLineage;
    const TArray<FLBPanelStillageLoad> StillagesBefore = PanelStillages;
    FName UnitId;
    FLBPanelStillageLoad* ReadyLoad = nullptr;
    if (Source->GetStorageType() == ELBPressShopStorageType::FinishedPanelStillages)
    {
        ReadyLoad = FindReadyStoredStillage(Source);
        UnitId = ReadyLoad ? ReadyLoad->StillageId : NAME_None;
    }
    const bool bWithdrawn = ReadyLoad
        ? Source->TryWithdrawIdentifiedUnitById(UnitId)
        : Source->TryWithdrawIdentifiedUnit(UnitId);
    if (!bWithdrawn || !Target->AcceptInputUnit(UnitId)
        || !RecordLinkedTransfer(Source, Target, OutReason))
    {
        Source->RestoreSaveState(SourceBefore);
        Target->RestoreSaveState(TargetBefore);
        PanelLineage = LineageBefore;
        PanelStillages = StillagesBefore;
        if (OutReason.IsEmpty()) OutReason = TEXT("STORAGE-TO-MACHINE TRANSFER WAS REJECTED");
        return false;
    }
    if (ReadyLoad)
    {
        ReadyLoad = PanelStillages.FindByPredicate([UnitId](const FLBPanelStillageLoad& Load)
            { return Load.StillageId == UnitId; });
        if (ReadyLoad)
        {
            ReadyLoad->bDeliveredToWeld = true;
            for (FLBPanelLineageRecord& Panel : PanelLineage)
                if (Panel.StillageId == UnitId) Panel.Stage = ELBPanelFlowStage::WeldShopIntake;
        }
    }
    return true;
}

bool ALBPlayerBuiltPressFlowController::EnqueueReadyStillageTransfer(
    ALBPressShopStorageZone* Source, ALBFactoryBuildMachine* Target, FString& OutReason)
{
    if (!Source || !Target
        || Source->GetStorageType() != ELBPressShopStorageType::FinishedPanelStillages
        || Target->GetMachineType() != ELBFactoryBuildMachineType::OutboundPanelDock)
    {
        OutReason = TEXT("PHYSICAL STILLAGE ROUTE REQUIRES FULL PRESS WIP AND WELD INTAKE");
        return false;
    }
    ALBStillageFLTFleetController* Fleet = FindStillageFleet();
    if (!Fleet)
    {
        OutReason = TEXT("NO STILLAGE FLT FLEET IS COMMISSIONED");
        return false;
    }
    if (!Target->CanAcceptInputUnit())
    {
        OutReason = TEXT("WELD INTAKE BUFFER IS FULL");
        return false;
    }

    bool bFoundReadyLoad = false;
    bool bFoundOutstandingLoad = false;
    for (const FLBPanelStillageLoad& Load : PanelStillages)
    {
        if (!Load.bReadyForWeld || Load.bDeliveredToWeld
            || !Source->ContainsIdentifiedUnit(Load.StillageId))
        {
            continue;
        }
        bFoundReadyLoad = true;
        if (HasOutstandingStillageJob(Load.StillageId))
        {
            bFoundOutstandingLoad = true;
            continue;
        }

        FName JobId;
        if (!Fleet->EnqueueFullStillageTransfer(Load.StillageId, Source, Target,
                WipStillageHalfExtentCm, JobId))
        {
            OutReason = FString::Printf(TEXT("FLT REJECTED READY STILLAGE %s"),
                *Load.StillageId.ToString());
            return false;
        }
        OutReason = FString::Printf(TEXT("%s DISPATCHED ON PHYSICAL FLT JOB %s"),
            *Load.StillageId.ToString(), *JobId.ToString());
        return true;
    }

    OutReason = bFoundOutstandingLoad
        ? TEXT("READY STILLAGE ALREADY HAS AN EXACT PHYSICAL FLT JOB")
        : bFoundReadyLoad
            ? TEXT("READY STILLAGE CANNOT BE DISPATCHED")
            : TEXT("NO READY FULL WIP STILLAGE IS STORED");
    return false;
}

void ALBPlayerBuiltPressFlowController::HandleStillageFleetDelivered(
    const FName JobId, const FName StillageId, const ELBStillageFLTJobType JobType,
    const FName SourceAuthorityId, const FName TargetAuthorityId)
{
    if (JobId.IsNone() || StillageId.IsNone() || !GetWorld())
    {
        return;
    }
    FLBStillageFLTJob Job;
    if (!IsAuthoritativeFleetDelivery(JobId, StillageId, JobType,
        SourceAuthorityId, TargetAuthorityId, Job)) return;

    FLBPanelStillageLoad* Load = PanelStillages.FindByPredicate(
        [StillageId](const FLBPanelStillageLoad& Candidate)
        { return Candidate.StillageId == StillageId; });
    if (!Load) return;

    if (JobType == ELBStillageFLTJobType::EmptyStillageToPress)
    {
        if (Load->bReturnedEmpty) return;
        FString Reason;
        CommitEmptyStillageReturn(Job, *Load, Reason);
        LastAutomaticFlowSummary = Reason;
        return;
    }
    if (JobType != ELBStillageFLTJobType::FullStillageToWeld) return;

    if (ALBBodyWeldLineActor* WeldLine = FindBodyWeldLineByAuthorityId(TargetAuthorityId))
    {
        if (Load->bAcceptedByBodyWeld) return;
        ALBFactoryBuildMachine* SourceDock = FindMachineByAuthorityId(SourceAuthorityId);
        FString Reason;
        CommitStillageToBodyWeld(&Job, SourceDock, WeldLine, *Load, Reason);
        LastAutomaticFlowSummary = Reason;
        return;
    }

    if (Load->bDeliveredToWeld) return; // Idempotent stage-9 duplicate delivery event.

    ALBPressShopStorageZone* Source = FindStorageByAuthorityId(SourceAuthorityId);
    ALBFactoryBuildMachine* Target = FindMachineByAuthorityId(TargetAuthorityId);
    if (!Load || !Load->bReadyForWeld || Load->bReturnedEmpty || !Source || !Target
        || Source->GetStorageType() != ELBPressShopStorageType::FinishedPanelStillages
        || Target->GetMachineType() != ELBFactoryBuildMachineType::OutboundPanelDock
        || !Source->ContainsIdentifiedUnit(StillageId))
    {
        LastAutomaticFlowSummary = FString::Printf(
            TEXT("FLT DELIVERY %s REJECTED: OWNERSHIP AUTHORITIES DO NOT MATCH"),
            *JobId.ToString());
        return;
    }

    const FLBPressShopStorageZoneSaveState SourceBefore = Source->CaptureSaveState();
    const FLBFactoryBuildMachineSaveState TargetBefore = Target->CaptureSaveState();
    const TArray<FLBPanelLineageRecord> LineageBefore = PanelLineage;
    const TArray<FLBPanelStillageLoad> StillagesBefore = PanelStillages;
    if (!Source->TryWithdrawIdentifiedUnitById(StillageId)
        || !Target->AcceptInputUnit(StillageId))
    {
        Source->RestoreSaveState(SourceBefore);
        Target->RestoreSaveState(TargetBefore);
        PanelLineage = LineageBefore;
        PanelStillages = StillagesBefore;
        LastAutomaticFlowSummary = FString::Printf(
            TEXT("FLT DELIVERY %s ROLLED BACK: WELD INTAKE REJECTED %s"),
            *JobId.ToString(), *StillageId.ToString());
        return;
    }

    Load = PanelStillages.FindByPredicate([StillageId](const FLBPanelStillageLoad& Candidate)
        { return Candidate.StillageId == StillageId; });
    if (!Load)
    {
        Source->RestoreSaveState(SourceBefore);
        Target->RestoreSaveState(TargetBefore);
        PanelLineage = LineageBefore;
        PanelStillages = StillagesBefore;
        return;
    }
    Load->bDeliveredToWeld = true;
    for (FLBPanelLineageRecord& Panel : PanelLineage)
    {
        if (Panel.StillageId == StillageId) Panel.Stage = ELBPanelFlowStage::WeldShopIntake;
    }
    LastAutomaticFlowSummary = FString::Printf(
        TEXT("FLT DELIVERY %s COMMITTED: %s ENTERED WELD INTAKE"),
        *JobId.ToString(), *StillageId.ToString());
}

bool ALBPlayerBuiltPressFlowController::TransferMachineOutputToMachine(
    ALBFactoryBuildMachine* Source, ALBFactoryBuildMachine* Target, FString& OutReason)
{
    if (!Source || !Target) return false;
    const FLBFactoryBuildMachineSaveState SourceBefore = Source->CaptureSaveState();
    const FLBFactoryBuildMachineSaveState TargetBefore = Target->CaptureSaveState();
    FName UnitId;
    if (!Source->ReleaseOutputUnit(UnitId) || !Target->AcceptInputUnit(UnitId)
        || !RecordLinkedTransfer(Source, Target, OutReason))
    {
        Source->RestoreSaveState(SourceBefore);
        Target->RestoreSaveState(TargetBefore);
        if (OutReason.IsEmpty()) OutReason = TEXT("INTER-MACHINE TRANSFER WAS REJECTED");
        return false;
    }
    return true;
}

bool ALBPlayerBuiltPressFlowController::ProcessMachine(
    ALBFactoryBuildMachine* Machine, FName& OutUnitId, FString& OutReason)
{
    if (!Machine || !Machine->ProcessNextUnit(OutUnitId))
    {
        OutReason = TEXT("MACHINE HAS NO PROCESSABLE INPUT UNIT");
        return false;
    }
    if (Machine->GetMachineType() == ELBFactoryBuildMachineType::InspectionCell)
        if (FLBPanelLineageRecord* Panel = FindLineageByPanelId(OutUnitId))
            Panel->Stage = ELBPanelFlowStage::Inspected;
    OutReason = FString::Printf(TEXT("%s PROCESSED %s"), *Machine->GetMachineId().ToString(), *OutUnitId.ToString());
    return true;
}

bool ALBPlayerBuiltPressFlowController::TransferBlankBufferToTrain(
    ALBPressShopStorageZone* Source, ALBPressTrainAStation* Target, FString& OutReason)
{
    if (!Source || !Target) return false;
    BindKnownPressTrains();
    FLBVehiclePanelBatch* Batch = SelectBatchForTrain(Target, Source);
    if (!Batch && !PanelBatches.IsEmpty())
    {
        OutReason = TEXT("NO PANEL BATCH IS ASSIGNED TO THIS TRAIN");
        return false;
    }
    const FName AutomaticToolingId = Batch
        ? FName(*FString::Printf(TEXT("AUTO_%s"), *Batch->PanelTypeId.ToString())) : NAME_None;
    if (Batch && !Target->SetActiveProductionRecipe(
        Batch->VehicleModelId, Batch->PanelTypeId, AutomaticToolingId))
    {
        OutReason = TEXT("TRAIN IS BUSY AND CANNOT COMPLETE ITS DIE CHANGE");
        return false;
    }
    const FLBPressShopStorageZoneSaveState SourceBefore = Source->CaptureSaveState();
    const FLBPressTrainASaveState TargetBefore = Target->CaptureSaveState();
    FName BlankId;
    if (!Source->TryWithdrawIdentifiedUnit(BlankId))
    {
        OutReason = TEXT("BLANK BUFFER IS STARVED");
        return false;
    }
    const FName ReservationId(*FString::Printf(TEXT("BUILDER-RES-%s"), *BlankId.ToString()));
    if (!Target->QueueReservedBlank(ReservationId, BlankId)
        || !RecordLinkedTransfer(Source, Target, OutReason))
    {
        Source->RestoreSaveState(SourceBefore);
        Target->RestoreSaveState(TargetBefore);
        if (OutReason.IsEmpty()) OutReason = TEXT("BLANK BUFFER HANDOFF TO PRESS TRAIN WAS REJECTED");
        return false;
    }
    if (Batch)
    {
        FLBPanelLineageRecord& Panel = PanelLineage.AddDefaulted_GetRef();
        Panel.BlankId = BlankId;
        Panel.OrderId = Batch->OrderId;
        Panel.VehicleModelId = Batch->VehicleModelId;
        Panel.PanelTypeId = Batch->PanelTypeId;
        Panel.SourceTrainId = Target->GetTrainId();
        Panel.Disposition = ELBPanelDisposition::Pending;
        Panel.Stage = ELBPanelFlowStage::BlankReserved;
        ++Batch->DispatchedQuantity;
    }
    return true;
}

bool ALBPlayerBuiltPressFlowController::TryStartConsoleFreeTrain(
    ALBPressTrainAStation* Target, FString& OutReason) const
{
    OutReason.Reset();
    if (!bConsoleFreeTrainAutostartEnabled || !Target)
    {
        OutReason = TEXT("CONSOLE-FREE TRAIN AUTOSTART IS NOT ENABLED");
        return false;
    }

    FLBPressTrainAHMIStatus Status = Target->GetHMIStatus();
    if (Status.PendingBlankCount <= 0)
    {
        OutReason = TEXT("NO IDENTIFIED RESERVED BLANK IS QUEUED");
        return false;
    }
    if (Status.bRestartRequiredAfterLoad)
    {
        OutReason = TEXT("TRAIN REQUIRES AN EXPLICIT PLAYER RESTART AFTER LOAD");
        return false;
    }
    if (Status.ActiveFault != ELBPressTrainAFault::None || Status.bIsolationRequested
        || Status.bEmergencyStopActive || !Status.bSafetyCircuitHealthy
        || !Status.bAccessInterlocksClosed || !Status.bDestackHealthy
        || !Status.bTransferHealthy || !Status.bInspectionHealthy
        || !Status.bStillageOutputClear)
    {
        OutReason = TEXT("TRAIN SAFETY OR PROCESS PERMISSIVES ARE NOT HEALTHY");
        return false;
    }
    if (Status.State == ELBPressTrainAState::Cycling
        || Status.State == ELBPressTrainAState::Stopping)
    {
        OutReason = TEXT("TRAIN IS ALREADY MOVING");
        return false;
    }

    bool bPoweredByPlayerFlow = false;
    if (!Status.bControlPowerOn)
    {
        TArray<FText> PrePowerReasons;
        Target->CanStart(PrePowerReasons);
        // A healthy isolated train has only the expected power-off and not-ready blockers.
        // Any additional blocker leaves it isolated and demands player intervention.
        if (Status.State != ELBPressTrainAState::Isolated || PrePowerReasons.Num() != 2)
        {
            OutReason = TEXT("TRAIN HAS A START BLOCKER BEYOND LOCAL CONTROL POWER");
            return false;
        }
        Target->SetControlPower(true);
        bPoweredByPlayerFlow = true;
    }

    Status = Target->GetHMIStatus();
    TArray<FText> BlockingReasons;
    if (Status.bRestartRequiredAfterLoad || !Target->CanStart(BlockingReasons)
        || !Target->StartLine())
    {
        if (bPoweredByPlayerFlow) Target->SetControlPower(false);
        OutReason = TEXT("TRAIN FAILED ITS FINAL LOCAL START PERMISSIVE CHECK");
        return false;
    }

    OutReason = FString::Printf(TEXT("%s LOCALLY POWERED AND STARTED WITH A RESERVED BLANK"),
        *Status.TrainId.ToString());
    return true;
}

bool ALBPlayerBuiltPressFlowController::TransferTrainPanelToInspection(
    ALBPressTrainAStation* Source, ALBFactoryBuildMachine* Target, FString& OutReason)
{
    if (!Source || !Target) return false;
    const FLBPressTrainASaveState SourceBefore = Source->CaptureSaveState();
    const FLBFactoryBuildMachineSaveState TargetBefore = Target->CaptureSaveState();
    FName PanelId;
    const FLBPressTrainAHMIStatus Status = Source->GetHMIStatus();
    if (Status.OldestPendingPanelId.IsNone())
    {
        OutReason = TEXT("PRESS TRAIN OUTPUT IS STARVED");
        return false;
    }
    const FName TransactionId(*FString::Printf(TEXT("BUILDER-PANEL-%s"), *Status.OldestPendingPanelId.ToString()));
    if (!Source->RequestPanelHandoff(TransactionId, PanelId)
        || !Target->AcceptInputUnit(PanelId)
        || !Source->ConfirmPanelHandoff(TransactionId)
        || !RecordLinkedTransfer(Source, Target, OutReason))
    {
        Source->RestoreSaveState(SourceBefore);
        Target->RestoreSaveState(TargetBefore);
        if (OutReason.IsEmpty()) OutReason = TEXT("PRESS PANEL HANDOFF TO INSPECTION WAS REJECTED");
        return false;
    }
    FLBPanelLineageRecord* Panel = FindLineageByPanelId(PanelId);
    if (!Panel)
    {
        FName VehicleModelId;
        FName PanelTypeId;
        if (LBCairnwell2040PanelCatalog::ParsePressedPanelUnitId(
                PanelId, VehicleModelId, PanelTypeId))
        {
            Panel = PanelLineage.FindByPredicate(
                [Source, VehicleModelId, PanelTypeId](const FLBPanelLineageRecord& Candidate)
                {
                    return Candidate.PanelId.IsNone()
                        && Candidate.SourceTrainId == Source->GetTrainId()
                        && Candidate.VehicleModelId == VehicleModelId
                        && Candidate.PanelTypeId == PanelTypeId;
                });
            if (Panel)
            {
                Panel->PanelId = PanelId;
                Panel->Disposition = ELBPanelDisposition::Good;
            }
        }
    }
    if (Panel) Panel->Stage = ELBPanelFlowStage::Inspection;
    return true;
}

FLBPanelLineageRecord* ALBPlayerBuiltPressFlowController::FindLineageByPanelId(
    const FName PanelId)
{
    if (PanelId.IsNone()) return nullptr;
    return PanelLineage.FindByPredicate([PanelId](const FLBPanelLineageRecord& Panel)
        { return Panel.PanelId == PanelId; });
}

void ALBPlayerBuiltPressFlowController::HandlePressPanelCompleted(
    const FName PanelId, const bool bInspectionPass)
{
    FName VehicleModelId;
    FName PanelTypeId;
    if (!LBCairnwell2040PanelCatalog::ParsePressedPanelUnitId(
            PanelId, VehicleModelId, PanelTypeId)) return;

    FString Prefix;
    PanelId.ToString().Split(TEXT("-PANEL-"), &Prefix, nullptr);
    const TCHAR Variant = Prefix.Len() >= 2 ? Prefix[Prefix.Len() - 1] : TCHAR('A');
    FLBPanelLineageRecord* Panel = PanelLineage.FindByPredicate(
        [VehicleModelId, PanelTypeId, Variant](const FLBPanelLineageRecord& Candidate)
        {
            return Candidate.PanelId.IsNone()
                && Candidate.VehicleModelId == VehicleModelId
                && Candidate.PanelTypeId == PanelTypeId
                && Candidate.SourceTrainId.ToString().EndsWith(FString::Chr(Variant));
        });
    if (!Panel)
    {
        Panel = PanelLineage.FindByPredicate(
            [VehicleModelId, PanelTypeId](const FLBPanelLineageRecord& Candidate)
            {
                return Candidate.PanelId.IsNone()
                    && Candidate.VehicleModelId == VehicleModelId
                    && Candidate.PanelTypeId == PanelTypeId;
            });
    }
    if (!Panel) return;

    Panel->PanelId = PanelId;
    Panel->Disposition = bInspectionPass
        ? ELBPanelDisposition::Good : ELBPanelDisposition::Rejected;
    Panel->Stage = bInspectionPass
        ? ELBPanelFlowStage::PressOutput : ELBPanelFlowStage::Rejected;
    RefreshStillageReadiness(Panel->OrderId);
}

FLBPanelStillageLoad* ALBPlayerBuiltPressFlowController::FindOpenStillage(
    const FLBPanelLineageRecord& Panel)
{
    return PanelStillages.FindByPredicate([&Panel](const FLBPanelStillageLoad& Load)
    {
        return Load.OrderId == Panel.OrderId
            && Load.VehicleModelId == Panel.VehicleModelId
            && Load.PanelTypeId == Panel.PanelTypeId
            && !Load.bReadyForWeld && !Load.bDeliveredToWeld && !Load.bReturnedEmpty
            && Load.PanelIds.Num() < Load.CapacityPanels;
    });
}

ALBPressShopStorageZone* ALBPlayerBuiltPressFlowController::FindEmptyStillageStorage() const
{
    if (!GetWorld()) return nullptr;
    TArray<ALBPressShopStorageZone*> Candidates;
    for (TActorIterator<ALBPressShopStorageZone> It(GetWorld()); It; ++It)
    {
        if (IsValid(*It)
            && It->GetStorageType() == ELBPressShopStorageType::EmptyPanelStillages
            && It->GetIdentifiedUnitCount() > 0)
        {
            Candidates.Add(*It);
        }
    }
    Candidates.Sort([](const ALBPressShopStorageZone& A, const ALBPressShopStorageZone& B)
    {
        return A.GetZoneId().ToString() < B.GetZoneId().ToString();
    });
    return Candidates.IsEmpty() ? nullptr : Candidates[0];
}

FLBPanelStillageLoad* ALBPlayerBuiltPressFlowController::FindReadyStoredStillage(
    const ALBPressShopStorageZone* Source)
{
    if (!Source) return nullptr;
    return PanelStillages.FindByPredicate([Source](const FLBPanelStillageLoad& Load)
    {
        return Load.bReadyForWeld && !Load.bDeliveredToWeld
            && Source->ContainsIdentifiedUnit(Load.StillageId);
    });
}

void ALBPlayerBuiltPressFlowController::RefreshStillageReadiness(const FName OrderId)
{
    if (OrderId.IsNone()) return;
    for (FLBPanelStillageLoad& Load : PanelStillages)
    {
        if (Load.OrderId != OrderId || Load.bDeliveredToWeld) continue;
        const FLBVehiclePanelBatch* Batch = PanelBatches.FindByPredicate(
            [&Load](const FLBVehiclePanelBatch& Candidate)
            {
                return Candidate.OrderId == Load.OrderId
                    && Candidate.VehicleModelId == Load.VehicleModelId
                    && Candidate.PanelTypeId == Load.PanelTypeId;
            });
        if (!Batch) continue;
        int32 TerminalCount = 0;
        int32 GoodCount = 0;
        int32 PackedGoodCount = 0;
        for (const FLBPanelLineageRecord& Panel : PanelLineage)
        {
            if (Panel.OrderId != Load.OrderId || Panel.VehicleModelId != Load.VehicleModelId
                || Panel.PanelTypeId != Load.PanelTypeId || Panel.PanelId.IsNone()
                || Panel.Disposition == ELBPanelDisposition::Pending) continue;
            ++TerminalCount;
            if (Panel.Disposition == ELBPanelDisposition::Good)
            {
                ++GoodCount;
                if (!Panel.StillageId.IsNone()) ++PackedGoodCount;
            }
        }
        const bool bOrderTerminal = TerminalCount >= Batch->RequestedQuantity;
        const bool bAllGoodPacked = PackedGoodCount >= GoodCount;
        Load.bReadyForWeld = Load.PanelIds.Num() >= Load.CapacityPanels
            || (bOrderTerminal && bAllGoodPacked && !Load.PanelIds.IsEmpty());
    }
}

bool ALBPlayerBuiltPressFlowController::PackInspectedPanelIntoStillage(
    ALBFactoryBuildMachine* Source, ALBPressShopStorageZone* Target, FString& OutReason)
{
    const FLBFactoryBuildMachineSaveState SourceBefore = Source->CaptureSaveState();
    const FLBPressShopStorageZoneSaveState TargetBefore = Target->CaptureSaveState();
    const TArray<FLBPanelLineageRecord> LineageBefore = PanelLineage;
    const TArray<FLBPanelStillageLoad> StillagesBefore = PanelStillages;
    const int32 SerialBefore = NextStillageSerial;
    ALBPressShopStorageZone* EmptyStorage = nullptr;
    FLBPressShopStorageZoneSaveState EmptyStorageBefore;
    bool bEmptyStorageChanged = false;

    FName PanelId;
    FLBPanelLineageRecord* Panel = nullptr;
    FLBPanelStillageLoad* Load = nullptr;
    bool bCreatedLoad = false;
    if (Source->ReleaseOutputUnit(PanelId)) Panel = FindLineageByPanelId(PanelId);
    if (Panel && Panel->Disposition == ELBPanelDisposition::Good
        && Panel->Stage == ELBPanelFlowStage::Inspected)
    {
        Load = FindOpenStillage(*Panel);
        if (!Load)
        {
            const FLBStampedPanelDefinition* Definition = LBCairnwell2040PanelCatalog::Find(
                Panel->VehicleModelId, Panel->PanelTypeId);
            EmptyStorage = FindEmptyStillageStorage();
            if (Definition && EmptyStorage)
            {
                EmptyStorageBefore = EmptyStorage->CaptureSaveState();
                FLBPanelStillageLoad& NewLoad = PanelStillages.AddDefaulted_GetRef();
                NewLoad.OrderId = Panel->OrderId;
                NewLoad.VehicleModelId = Panel->VehicleModelId;
                NewLoad.PanelTypeId = Panel->PanelTypeId;
                NewLoad.CapacityPanels = Definition->StillageCapacity;
                if (EmptyStorage->TryWithdrawIdentifiedUnit(NewLoad.StillageId))
                {
                    ++NextStillageSerial;
                    Load = &NewLoad;
                    bCreatedLoad = true;
                    bEmptyStorageChanged = true;
                }
            }
        }
    }

    if (!Panel || !Load || Load->PanelIds.Contains(PanelId)
        || Load->PanelIds.Num() >= Load->CapacityPanels)
    {
        const FString Diagnostic = FString::Printf(
            TEXT("PANEL=%s LINEAGE=%s DISPOSITION=%d STAGE=%d LOAD=%s TARGET_FREE=%d"),
            *PanelId.ToString(), Panel ? TEXT("FOUND") : TEXT("MISSING"),
            Panel ? static_cast<int32>(Panel->Disposition) : -1,
            Panel ? static_cast<int32>(Panel->Stage) : -1,
            Load ? *Load->StillageId.ToString() : TEXT("NONE"),
            Target->GetAvailableCapacity());
        Source->RestoreSaveState(SourceBefore);
        Target->RestoreSaveState(TargetBefore);
        if (bEmptyStorageChanged && EmptyStorage) EmptyStorage->RestoreSaveState(EmptyStorageBefore);
        PanelLineage = LineageBefore;
        PanelStillages = StillagesBefore;
        NextStillageSerial = SerialBefore;
        OutReason = FString::Printf(TEXT("INSPECTED PANEL HAS NO COMPATIBLE WIP STILLAGE CAPACITY: %s"),
            *Diagnostic);
        return false;
    }

    Load->PanelIds.Add(PanelId);
    Panel->StillageId = Load->StillageId;
    Panel->Stage = ELBPanelFlowStage::WIPStillage;
    RefreshStillageReadiness(Panel->OrderId);
    if (Load->bReadyForWeld && !Target->ContainsIdentifiedUnit(Load->StillageId)
        && !Target->TryStoreIdentifiedUnit(Load->StillageId))
    {
        Source->RestoreSaveState(SourceBefore);
        Target->RestoreSaveState(TargetBefore);
        if (bEmptyStorageChanged && EmptyStorage) EmptyStorage->RestoreSaveState(EmptyStorageBefore);
        PanelLineage = LineageBefore;
        PanelStillages = StillagesBefore;
        NextStillageSerial = SerialBefore;
        OutReason = TEXT("FULL WIP STILLAGE BUFFER HAS NO FREE BAY");
        return false;
    }
    if (!RecordLinkedTransfer(Source, Target, OutReason))
    {
        Source->RestoreSaveState(SourceBefore);
        Target->RestoreSaveState(TargetBefore);
        if (bEmptyStorageChanged && EmptyStorage) EmptyStorage->RestoreSaveState(EmptyStorageBefore);
        PanelLineage = LineageBefore;
        PanelStillages = StillagesBefore;
        NextStillageSerial = SerialBefore;
        OutReason = TEXT("WIP STILLAGE TRANSFER LINK REJECTED THE PANEL");
        return false;
    }
    OutReason = FString::Printf(TEXT("%s PACKED INTO %s (%d/%d)%s"),
        *PanelId.ToString(), *Load->StillageId.ToString(), Load->PanelIds.Num(),
        Load->CapacityPanels, bCreatedLoad ? TEXT(" NEW STILLAGE") : TEXT(""));
    return true;
}

bool ALBPlayerBuiltPressFlowController::ReturnEmptyStillageFromWeld(
    const FName StillageId, ALBPressShopStorageZone* EmptyStorage, FString& OutReason)
{
    FLBPanelStillageLoad* Load = PanelStillages.FindByPredicate(
        [StillageId](const FLBPanelStillageLoad& Candidate)
        { return Candidate.StillageId == StillageId; });
    if (StillageId.IsNone() || !Load || !Load->bDeliveredToWeld || Load->bReturnedEmpty
        || Load->bEmptyReturnQueued
        || !EmptyStorage
        || EmptyStorage->GetStorageType() != ELBPressShopStorageType::EmptyPanelStillages)
    {
        OutReason = TEXT("WELD RETURN REQUIRES ONE DELIVERED STILLAGE AND AN EMPTY STILLAGE STORE");
        return false;
    }
    if (!EmptyStorage->TryStoreIdentifiedUnit(StillageId))
    {
        OutReason = TEXT("EMPTY STILLAGE RETURN STORE IS FULL");
        return false;
    }
    Load->bReturnedEmpty = true;
    Load->bEmptyReturnQueued = false;
    Load->EmptyReturnJobId = NAME_None;
    OutReason = FString::Printf(TEXT("%s RETURNED EMPTY FROM WELD"), *StillageId.ToString());
    return true;
}

bool ALBPlayerBuiltPressFlowController::CommitStillageToBodyWeld(
    const FLBStillageFLTJob* DeliveryJob, ALBFactoryBuildMachine* SourceDock,
    ALBBodyWeldLineActor* TargetLine, FLBPanelStillageLoad& Load, FString& OutReason)
{
    OutReason.Reset();
    if (!SourceDock || !TargetLine || !Load.bReadyForWeld || !Load.bDeliveredToWeld
        || Load.bAcceptedByBodyWeld || Load.bReturnedEmpty
        || SourceDock->GetMachineType() != ELBFactoryBuildMachineType::OutboundPanelDock
        || !FindExactLink(SourceDock->OutputPort, TargetLine->GetStillageInputPort()))
    {
        OutReason = TEXT("BODY WELD HANDOFF REQUIRES THE COMPLETED STAGE-9 DOCK AND EXACT LINK");
        return false;
    }
    const FLBFactoryBuildMachineSaveState DockBefore = SourceDock->CaptureSaveState();
    if (!DockBefore.CompletedUnitIds.Contains(Load.StillageId))
    {
        OutReason = TEXT("EXACT STILLAGE HAS NOT COMPLETED THE STAGE-9 INTAKE PREREQUISITE");
        return false;
    }
    const FLBBodyWeldLineSaveState WeldBefore = TargetLine->CaptureSaveState();
    const TArray<FLBPanelLineageRecord> LineageBefore = PanelLineage;
    const TArray<FLBPanelStillageLoad> StillagesBefore = PanelStillages;
    const int64 SequenceBefore = NextBodyWeldDeliverySequence;
    ALBFactoryTransportLink* Link = FindExactLink(
        SourceDock->OutputPort, TargetLine->GetStillageInputPort());

    FLBBodyWeldStillageInventory Payload;
    Payload.StillageId = Load.StillageId;
    Payload.OrderId = Load.OrderId;
    Payload.VehicleModelId = Load.VehicleModelId;
    Payload.PanelTypeId = Load.PanelTypeId;
    Payload.DeliverySequence = NextBodyWeldDeliverySequence;
    Payload.CapacityPanels = Load.CapacityPanels;
    for (const FName PanelId : Load.PanelIds)
    {
        const FLBPanelLineageRecord* Lineage = PanelLineage.FindByPredicate(
            [PanelId, &Load](const FLBPanelLineageRecord& Candidate)
            {
                return Candidate.PanelId == PanelId && Candidate.StillageId == Load.StillageId
                    && Candidate.OrderId == Load.OrderId
                    && Candidate.VehicleModelId == Load.VehicleModelId
                    && Candidate.PanelTypeId == Load.PanelTypeId
                    && Candidate.Disposition == ELBPanelDisposition::Good
                    && Candidate.Stage == ELBPanelFlowStage::WeldShopIntake;
            });
        if (!Lineage)
        {
            OutReason = TEXT("STILLAGE MANIFEST AND EXACT PANEL LINEAGE DO NOT MATCH");
            return false;
        }
        FLBBodyWeldPanelUnit& Panel = Payload.PanelUnits.AddDefaulted_GetRef();
        Panel.PanelId = Lineage->PanelId;
        Panel.OrderId = Lineage->OrderId;
        Panel.VehicleModelId = Lineage->VehicleModelId;
        Panel.PanelTypeId = Lineage->PanelTypeId;
        Panel.StillageId = Lineage->StillageId;
    }
    Payload.PanelUnits.Sort([](const FLBBodyWeldPanelUnit& Left,
        const FLBBodyWeldPanelUnit& Right) { return Left.PanelId.LexicalLess(Right.PanelId); });

    FLBFactoryBuildMachineSaveState DockAfter = DockBefore;
    if (DockAfter.CompletedUnitIds.RemoveSingle(Load.StillageId) != 1)
    {
        OutReason = TEXT("STAGE-9 DOCK DOES NOT OWN THE EXACT COMPLETED STILLAGE");
        return false;
    }
    const bool bAssignedHere = TargetLine->GetAssignedOrderId().IsNone();
    const bool bOrderCompatible = bAssignedHere
        ? TargetLine->SetAssignedOrder(Load.OrderId)
        : TargetLine->GetAssignedOrderId() == Load.OrderId;
    FString WeldReason;
    const bool bCommitted = bOrderCompatible
        && SourceDock->RestoreSaveState(DockAfter)
        && TargetLine->ReceivePanelStillage(Payload, WeldReason)
        && Link && Link->TryTransferUnits(1);
    if (!bCommitted)
    {
        SourceDock->RestoreSaveState(DockBefore);
        TargetLine->RestoreSaveState(WeldBefore);
        PanelLineage = LineageBefore;
        PanelStillages = StillagesBefore;
        NextBodyWeldDeliverySequence = SequenceBefore;
        OutReason = WeldReason.IsEmpty()
            ? TEXT("BODY WELD EXACT-ID HANDOFF ROLLED BACK") : WeldReason;
        return false;
    }

    FLBPanelStillageLoad* CommittedLoad = PanelStillages.FindByPredicate(
        [&Load](const FLBPanelStillageLoad& Candidate)
        { return Candidate.StillageId == Load.StillageId; });
    if (!CommittedLoad)
    {
        SourceDock->RestoreSaveState(DockBefore);
        TargetLine->RestoreSaveState(WeldBefore);
        PanelLineage = LineageBefore;
        PanelStillages = StillagesBefore;
        NextBodyWeldDeliverySequence = SequenceBefore;
        OutReason = TEXT("BODY WELD MANIFEST LOST DURING COMMIT; TRANSACTION ROLLED BACK");
        return false;
    }
    CommittedLoad->WeldLineId = TargetLine->GetLineId();
    CommittedLoad->WeldDeliveryJobId = DeliveryJob ? DeliveryJob->JobId : NAME_None;
    CommittedLoad->WeldDeliverySequence = NextBodyWeldDeliverySequence++;
    CommittedLoad->bAcceptedByBodyWeld = true;
    for (FLBPanelLineageRecord& Panel : PanelLineage)
        if (Panel.StillageId == CommittedLoad->StillageId)
            Panel.Stage = ELBPanelFlowStage::BodyWeldInventory;
    OutReason = FString::Printf(TEXT("%s COMMITTED EXACTLY INTO BODY WELD %s"),
        *CommittedLoad->StillageId.ToString(), *TargetLine->GetLineId().ToString());
    return true;
}

bool ALBPlayerBuiltPressFlowController::EnqueueCompletedStillageToBodyWeld(FString& OutReason)
{
    OutReason.Reset();
    if (!GetWorld()) return false;
    struct FCandidate
    {
        ALBFactoryBuildMachine* Dock = nullptr;
        ALBBodyWeldLineActor* Weld = nullptr;
        FLBPanelStillageLoad* Load = nullptr;
    };
    TArray<FCandidate> Candidates;
    for (FLBPanelStillageLoad& Load : PanelStillages)
    {
        if (!Load.bDeliveredToWeld || Load.bAcceptedByBodyWeld || Load.bReturnedEmpty
            || HasOutstandingStillageJob(Load.StillageId)) continue;
        bool bDeliveredJobAwaitsCommit = false;
        if (!Load.WeldDeliveryJobId.IsNone())
        {
            for (TActorIterator<ALBStillageFLTFleetController> FleetIt(GetWorld());
                FleetIt; ++FleetIt)
            {
                FLBStillageFLTJob ExistingJob;
                if (IsValid(*FleetIt)
                    && FleetIt->GetJobSnapshot(Load.WeldDeliveryJobId, ExistingJob)
                    && ExistingJob.StillageId == Load.StillageId
                    && ExistingJob.JobType == ELBStillageFLTJobType::FullStillageToWeld
                    && (ExistingJob.State == ELBStillageFLTJobState::DeliveredReturning
                        || ExistingJob.State == ELBStillageFLTJobState::Completed))
                {
                    bDeliveredJobAwaitsCommit = true;
                    break;
                }
            }
        }
        if (bDeliveredJobAwaitsCommit) continue;
        for (TActorIterator<ALBFactoryTransportLink> It(GetWorld()); It; ++It)
        {
            ALBFactoryBuildMachine* Dock = It->GetSourcePort()
                ? Cast<ALBFactoryBuildMachine>(It->GetSourcePort()->GetOwner()) : nullptr;
            ALBBodyWeldLineActor* Weld = It->GetTargetPort()
                ? Cast<ALBBodyWeldLineActor>(It->GetTargetPort()->GetOwner()) : nullptr;
            if (!Dock || !Weld || It->GetSourcePort() != Dock->OutputPort
                || It->GetTargetPort() != Weld->GetStillageInputPort()
                || Dock->GetMachineType() != ELBFactoryBuildMachineType::OutboundPanelDock
                || !Dock->CaptureSaveState().CompletedUnitIds.Contains(Load.StillageId)
                || (!Weld->GetAssignedOrderId().IsNone()
                    && Weld->GetAssignedOrderId() != Load.OrderId)) continue;
            Candidates.Add({Dock, Weld, &Load});
        }
    }
    Candidates.Sort([](const FCandidate& Left, const FCandidate& Right)
    {
        if (Left.Weld->GetLineId() != Right.Weld->GetLineId())
            return Left.Weld->GetLineId().LexicalLess(Right.Weld->GetLineId());
        if (Left.Dock->GetMachineId() != Right.Dock->GetMachineId())
            return Left.Dock->GetMachineId().LexicalLess(Right.Dock->GetMachineId());
        return Left.Load->StillageId.LexicalLess(Right.Load->StillageId);
    });
    if (Candidates.IsEmpty())
    {
        OutReason = TEXT("NO COMPLETED STAGE-9 STILLAGE IS ROUTABLE TO BODY WELD");
        return false;
    }
    FCandidate& Candidate = Candidates[0];
    if (ALBStillageFLTFleetController* Fleet = FindStillageFleet())
    {
        FName JobId;
        if (!Fleet->EnqueueFullStillageTransfer(Candidate.Load->StillageId,
            Candidate.Dock, Candidate.Weld, WipStillageHalfExtentCm, JobId))
        {
            OutReason = TEXT("FLT REJECTED THE EXACT STAGE-9 TO BODY-WELD ROUTE");
            return false;
        }
        Candidate.Load->WeldLineId = Candidate.Weld->GetLineId();
        Candidate.Load->WeldDeliveryJobId = JobId;
        OutReason = FString::Printf(TEXT("%s DISPATCHED TO %s ON %s"),
            *Candidate.Load->StillageId.ToString(), *Candidate.Weld->GetLineId().ToString(),
            *JobId.ToString());
        return true;
    }
    return CommitStillageToBodyWeld(nullptr, Candidate.Dock, Candidate.Weld,
        *Candidate.Load, OutReason);
}

ALBPressShopStorageZone* ALBPlayerBuiltPressFlowController::FindEmptyStillageReturnStorage() const
{
    if (!GetWorld()) return nullptr;
    TArray<ALBPressShopStorageZone*> Candidates;
    for (TActorIterator<ALBPressShopStorageZone> It(GetWorld()); It; ++It)
        if (IsValid(*It)
            && It->GetStorageType() == ELBPressShopStorageType::EmptyPanelStillages
            && It->GetAvailableCapacity() > 0) Candidates.Add(*It);
    Candidates.Sort([](const ALBPressShopStorageZone& Left,
        const ALBPressShopStorageZone& Right)
    {
        return Left.GetZoneId().LexicalLess(Right.GetZoneId());
    });
    return Candidates.IsEmpty() ? nullptr : Candidates[0];
}

bool ALBPlayerBuiltPressFlowController::CommitEmptyStillageReturn(
    const FLBStillageFLTJob& DeliveryJob, FLBPanelStillageLoad& Load, FString& OutReason)
{
    OutReason.Reset();
    ALBBodyWeldLineActor* SourceLine = FindBodyWeldLineByAuthorityId(
        DeliveryJob.SourceAuthorityId);
    ALBPressShopStorageZone* TargetStorage = FindStorageByAuthorityId(
        DeliveryJob.TargetAuthorityId);
    if (!SourceLine || !TargetStorage || !Load.bAcceptedByBodyWeld
        || Load.bReturnedEmpty || !Load.bEmptyReturnQueued
        || Load.EmptyReturnJobId != DeliveryJob.JobId
        || Load.WeldLineId != SourceLine->GetLineId()
        || TargetStorage->GetStorageType() != ELBPressShopStorageType::EmptyPanelStillages)
    {
        OutReason = TEXT("EMPTY RETURN AUTHORITIES OR EXACT SAVED JOB DO NOT MATCH");
        return false;
    }
    const FLBPressShopStorageZoneSaveState StorageBefore = TargetStorage->CaptureSaveState();
    const TArray<FLBPanelStillageLoad> StillagesBefore = PanelStillages;
    if (!TargetStorage->TryStoreIdentifiedUnit(Load.StillageId))
    {
        TargetStorage->RestoreSaveState(StorageBefore);
        PanelStillages = StillagesBefore;
        OutReason = TEXT("EMPTY STILLAGE RETURN STORAGE IS FULL; DELIVERY REMAINS RECONCILABLE");
        return false;
    }
    FLBPanelStillageLoad* Committed = PanelStillages.FindByPredicate(
        [&Load](const FLBPanelStillageLoad& Candidate)
        { return Candidate.StillageId == Load.StillageId; });
    if (!Committed)
    {
        TargetStorage->RestoreSaveState(StorageBefore);
        PanelStillages = StillagesBefore;
        OutReason = TEXT("EMPTY STILLAGE RETURN MANIFEST DISAPPEARED");
        return false;
    }
    Committed->bEmptyReturnQueued = false;
    Committed->bReturnedEmpty = true;
    OutReason = FString::Printf(TEXT("%s RETURNED EMPTY ON EXACT JOB %s"),
        *Committed->StillageId.ToString(), *DeliveryJob.JobId.ToString());
    return true;
}

bool ALBPlayerBuiltPressFlowController::DispatchOneEmptyStillageReturn(FString& OutReason)
{
    OutReason.Reset();
    if (!GetWorld()) return false;
    TArray<ALBBodyWeldLineActor*> Lines;
    for (TActorIterator<ALBBodyWeldLineActor> It(GetWorld()); It; ++It)
        if (IsValid(*It) && It->GetPendingEmptyReturnCount() > 0) Lines.Add(*It);
    Lines.Sort([](const ALBBodyWeldLineActor& Left, const ALBBodyWeldLineActor& Right)
    {
        return Left.GetLineId().LexicalLess(Right.GetLineId());
    });
    ALBPressShopStorageZone* EmptyStorage = FindEmptyStillageReturnStorage();
    if (Lines.IsEmpty() || !EmptyStorage)
    {
        OutReason = TEXT("NO WELD EMPTY RETURN OR PRESS EMPTY-STILLAGE CAPACITY");
        return false;
    }
    for (ALBBodyWeldLineActor* Line : Lines)
    {
        const FLBBodyWeldLineSaveState WeldBefore = Line->CaptureSaveState();
        if (WeldBefore.PendingEmptyReturns.IsEmpty()) continue;
        TArray<FLBBodyWeldEmptyStillageReturn> Pending = WeldBefore.PendingEmptyReturns;
        Pending.Sort([](const FLBBodyWeldEmptyStillageReturn& Left,
            const FLBBodyWeldEmptyStillageReturn& Right)
        {
            if (Left.QueueSequence != Right.QueueSequence)
                return Left.QueueSequence < Right.QueueSequence;
            return Left.StillageId.LexicalLess(Right.StillageId);
        });
        FLBPanelStillageLoad* Load = PanelStillages.FindByPredicate(
            [&Pending, Line](const FLBPanelStillageLoad& Candidate)
            {
                return Candidate.StillageId == Pending[0].StillageId
                    && Candidate.bAcceptedByBodyWeld && !Candidate.bReturnedEmpty
                    && !Candidate.bEmptyReturnQueued
                    && Candidate.WeldLineId == Line->GetLineId();
            });
        if (!Load || HasOutstandingStillageJob(Pending[0].StillageId)) continue;
        const TArray<FLBPanelStillageLoad> StillagesBefore = PanelStillages;
        FLBBodyWeldEmptyStillageReturn Popped;
        if (!Line->PopEmptyStillageReturn(Popped)
            || Popped.StillageId != Pending[0].StillageId)
        {
            Line->RestoreSaveState(WeldBefore);
            continue;
        }
        if (ALBStillageFLTFleetController* Fleet = FindStillageFleet())
        {
            FName JobId;
            if (!Fleet->EnqueueEmptyStillageReturn(Popped.StillageId, Line, EmptyStorage,
                WipStillageHalfExtentCm, JobId))
            {
                Line->RestoreSaveState(WeldBefore);
                PanelStillages = StillagesBefore;
                OutReason = TEXT("EMPTY RETURN ENQUEUE FAILED; WELD POP WAS ROLLED BACK");
                return false;
            }
            Load = PanelStillages.FindByPredicate([&Popped](const FLBPanelStillageLoad& Candidate)
                { return Candidate.StillageId == Popped.StillageId; });
            Load->EmptyReturnJobId = JobId;
            Load->bEmptyReturnQueued = true;
            OutReason = FString::Printf(TEXT("%s EMPTY RETURN DISPATCHED ON %s"),
                *Popped.StillageId.ToString(), *JobId.ToString());
            return true;
        }
        FString DirectReason;
        if (!ReturnEmptyStillageFromWeld(Popped.StillageId, EmptyStorage, DirectReason))
        {
            Line->RestoreSaveState(WeldBefore);
            PanelStillages = StillagesBefore;
            OutReason = TEXT("DIRECT EMPTY RETURN FAILED; WELD POP WAS ROLLED BACK");
            return false;
        }
        OutReason = DirectReason;
        return true;
    }
    OutReason = TEXT("ALL PENDING EMPTY RETURNS ALREADY HAVE EXACT PHYSICAL JOBS");
    return false;
}

bool ALBPlayerBuiltPressFlowController::TransferOneBaseKitToBodyWeld(FString& OutReason)
{
    OutReason.Reset();
    TArray<int32> CandidateIndices;
    CandidateIndices.Reserve(PendingBaseKitDeliveries.Num());
    for (int32 Index = 0; Index < PendingBaseKitDeliveries.Num(); ++Index)
        CandidateIndices.Add(Index);
    CandidateIndices.Sort([this](const int32 LeftIndex, const int32 RightIndex)
    {
        const FLBBodyWeldBaseKitDeliveryRecord& Left = PendingBaseKitDeliveries[LeftIndex];
        const FLBBodyWeldBaseKitDeliveryRecord& Right = PendingBaseKitDeliveries[RightIndex];
        if (Left.BaseKit.DeliverySequence != Right.BaseKit.DeliverySequence)
            return Left.BaseKit.DeliverySequence < Right.BaseKit.DeliverySequence;
        return Left.BaseKit.KitId.LexicalLess(Right.BaseKit.KitId);
    });
    for (const int32 Index : CandidateIndices)
    {
        const FLBBodyWeldBaseKitDeliveryRecord Delivery = PendingBaseKitDeliveries[Index];
        ALBFactoryBuildMachine* Adapter = FindMachineByAuthorityId(Delivery.DeliveryAuthorityId);
        ALBBodyWeldLineActor* WeldLine = FindBodyWeldLineByAuthorityId(Delivery.TargetWeldLineId);
        if (!Adapter || !WeldLine || Adapter->OutputPort->ProcessStage != LBFactoryProcessStage::WeldShopIntake
            || Adapter->OutputPort->MaterialClass != ELBFactoryMaterialClass::GeneralParts
            || Adapter->OutputPort->TransportKind != ELBFactoryTransportKind::AGVHandoff
            || !FindExactLink(Adapter->OutputPort, WeldLine->GetBaseKitInputPort())
            || (!WeldLine->GetAssignedOrderId().IsNone()
                && WeldLine->GetAssignedOrderId() != Delivery.BaseKit.OrderId)) continue;

        const FLBBodyWeldLineSaveState WeldBefore = WeldLine->CaptureSaveState();
        const TArray<FLBBodyWeldBaseKitDeliveryRecord> PendingBefore = PendingBaseKitDeliveries;
        const TArray<FLBBodyWeldBaseKitDeliveryRecord> TransferredBefore = TransferredBaseKitDeliveries;
        ALBFactoryTransportLink* Link = FindExactLink(
            Adapter->OutputPort, WeldLine->GetBaseKitInputPort());
        FString WeldReason;
        const bool bAssigned = WeldLine->GetAssignedOrderId().IsNone()
            ? WeldLine->SetAssignedOrder(Delivery.BaseKit.OrderId)
            : true;
        if (!bAssigned || !WeldLine->ReceiveBaseKit(Delivery.BaseKit, WeldReason)
            || !Link || !Link->TryTransferUnits(1))
        {
            WeldLine->RestoreSaveState(WeldBefore);
            PendingBaseKitDeliveries = PendingBefore;
            TransferredBaseKitDeliveries = TransferredBefore;
            OutReason = WeldReason.IsEmpty()
                ? TEXT("FINITE BASE-KIT ADAPTER TRANSFER ROLLED BACK") : WeldReason;
            return false;
        }
        PendingBaseKitDeliveries.RemoveAt(Index);
        FLBBodyWeldBaseKitDeliveryRecord Committed = Delivery;
        Committed.bTransferred = true;
        TransferredBaseKitDeliveries.Add(Committed);
        OutReason = FString::Printf(TEXT("FINITE BASE KIT %s TRANSFERRED FROM ADAPTER %s TO %s"),
            *Delivery.BaseKit.KitId.ToString(), *Adapter->GetMachineId().ToString(),
            *WeldLine->GetLineId().ToString());
        return true;
    }
    OutReason = TEXT("NO FINITE BASE KIT HAS A COMPATIBLE STAGE-9 ADAPTER LINK");
    return false;
}

int32 ALBPlayerBuiltPressFlowController::AdvanceBodyWeldRecipes(FString& OutReason)
{
    OutReason.Reset();
    if (!GetWorld()) return 0;
    TArray<ALBBodyWeldLineActor*> Lines;
    for (TActorIterator<ALBBodyWeldLineActor> It(GetWorld()); It; ++It)
        if (IsValid(*It)) Lines.Add(*It);
    Lines.Sort([](const ALBBodyWeldLineActor& Left, const ALBBodyWeldLineActor& Right)
        { return Left.GetLineId().LexicalLess(Right.GetLineId()); });
    int32 Count = 0;
    for (ALBBodyWeldLineActor* Line : Lines)
    {
        FString Reason;
        if (Line->GetPhase() == ELBBodyWeldPhase::AwaitingRecipe
            && Line->TryReserveRecipe(Reason))
        {
            ++Count;
            OutReason = FString::Printf(TEXT("%s RESERVED A COMPLETE EXACT RECIPE"),
                *Line->GetLineId().ToString());
        }
        if (Line->GetPhase() == ELBBodyWeldPhase::ReservingInputs
            && Line->CommitReservedInputs(Reason))
        {
            ++Count;
            OutReason = FString::Printf(TEXT("%s COMMITTED ITS COMPLETE EXACT RECIPE"),
                *Line->GetLineId().ToString());
        }
    }
    return Count;
}

int32 ALBPlayerBuiltPressFlowController::HandoffReadyBodyToECoat(FString& OutReason)
{
    OutReason.Reset();
    if (!GetWorld()) return 0;
    struct FCandidate
    {
        ALBBodyWeldLineActor* Weld = nullptr;
        ALBECoatLineActor* ECoat = nullptr;
        FLBBodyInWhiteRecord Body;
    };
    TArray<FCandidate> Candidates;
    for (TActorIterator<ALBFactoryTransportLink> It(GetWorld()); It; ++It)
    {
        ALBBodyWeldLineActor* Weld = It->GetSourcePort()
            ? Cast<ALBBodyWeldLineActor>(It->GetSourcePort()->GetOwner()) : nullptr;
        ALBECoatLineActor* ECoat = It->GetTargetPort()
            ? Cast<ALBECoatLineActor>(It->GetTargetPort()->GetOwner()) : nullptr;
        FLBBodyInWhiteRecord Body;
        if (!Weld || !ECoat || It->GetSourcePort() != Weld->GetBIWOutputPort()
            || It->GetTargetPort() != ECoat->GetInputPort()
            || !Weld->GetOutputBody(Body) || Body.QualityState != ELBBodyWeldQualityState::Good
            || Body.bEDAccepted) continue;
        const FName CarrierId(*FString::Printf(TEXT("EDC-%s"), *Body.BodyId.ToString()));
        FLBECoatCarrierSaveState ExistingCarrier;
        if (ECoat->GetCarrierState(CarrierId, ExistingCarrier)) continue;
        Candidates.Add({Weld, ECoat, Body});
    }
    Candidates.Sort([](const FCandidate& Left, const FCandidate& Right)
    {
        if (Left.ECoat->GetLineId() != Right.ECoat->GetLineId())
            return Left.ECoat->GetLineId().LexicalLess(Right.ECoat->GetLineId());
        if (Left.Weld->GetLineId() != Right.Weld->GetLineId())
            return Left.Weld->GetLineId().LexicalLess(Right.Weld->GetLineId());
        return Left.Body.BodyId.LexicalLess(Right.Body.BodyId);
    });
    if (Candidates.IsEmpty())
    {
        OutReason = TEXT("NO GOOD BIW HAS A FREE EXACT ED CARRIER AND COMPATIBLE LINK");
        return 0;
    }
    FCandidate& Candidate = Candidates[0];
    const FName CarrierId(*FString::Printf(TEXT("EDC-%s"), *Candidate.Body.BodyId.ToString()));
    FString EDReason;
    if (!Candidate.ECoat->AcceptAndAcknowledgeBodyInWhite(
        Candidate.Weld, Candidate.Body.BodyId, CarrierId, EDReason))
    {
        OutReason = EDReason;
        return 0;
    }
    ALBFactoryTransportLink* Link = FindExactLink(
        Candidate.Weld->GetBIWOutputPort(), Candidate.ECoat->GetInputPort());
    // ED acknowledgement is the exact ownership boundary. The link counter is projection
    // only and is preflighted above; TryTransferUnits is currently infallible here.
    if (Link) Link->TryTransferUnits(1);
    OutReason = FString::Printf(TEXT("%s ACKNOWLEDGED BY ED %s ON CARRIER %s"),
        *Candidate.Body.BodyId.ToString(), *Candidate.ECoat->GetLineId().ToString(),
        *CarrierId.ToString());
    return 1;
}

int32 ALBPlayerBuiltPressFlowController::ExecuteBodyWeldIntegrationStep(FString& OutSummary)
{
    OutSummary.Reset();
    if (!GetWorld())
    {
        OutSummary = TEXT("BODY WELD INTEGRATION HAS NO WORLD AUTHORITY");
        return 0;
    }
    BindKnownStillageFleets();
    ReconcileStillageFleetDeliveries();
    int32 Count = 0;
    FString LastReason;
    FString Reason;
    if (EnqueueCompletedStillageToBodyWeld(Reason)) { ++Count; LastReason = Reason; }
    if (TransferOneBaseKitToBodyWeld(Reason)) { ++Count; LastReason = Reason; }
    const int32 RecipeCount = AdvanceBodyWeldRecipes(Reason);
    Count += RecipeCount;
    if (RecipeCount > 0) LastReason = Reason;
    if (DispatchOneEmptyStillageReturn(Reason)) { ++Count; LastReason = Reason; }
    const int32 EDCount = HandoffReadyBodyToECoat(Reason);
    Count += EDCount;
    if (EDCount > 0) LastReason = Reason;
    OutSummary = Count > 0
        ? FString::Printf(TEXT("BODY WELD INTEGRATION: %d ACTIONS; %s"), Count, *LastReason)
        : TEXT("BODY WELD INTEGRATION: IDLE");
    return Count;
}

int32 ALBPlayerBuiltPressFlowController::ExecuteAutomaticStep(FString& OutSummary)
{
    OutSummary.Empty();
    if (!GetWorld())
    {
        OutSummary = TEXT("AUTOMATIC FLOW HAS NO WORLD AUTHORITY");
        return 0;
    }

    TArray<ALBFactoryTransportLink*> Links;
    for (TActorIterator<ALBFactoryTransportLink> It(GetWorld()); It; ++It)
        if (It->GetSourcePort() && It->GetTargetPort()) Links.Add(*It);
    Links.Sort([](const ALBFactoryTransportLink& A, const ALBFactoryTransportLink& B)
    {
        const ULBFactoryProcessPortComponent* AP = A.GetSourcePort();
        const ULBFactoryProcessPortComponent* BP = B.GetSourcePort();
        if (AP->ProcessStage != BP->ProcessStage) return AP->ProcessStage > BP->ProcessStage;
        if (AP->PortId != BP->PortId) return AP->PortId.ToString() < BP->PortId.ToString();
        return A.GetTargetPort()->PortId.ToString() < B.GetTargetPort()->PortId.ToString();
    });

    int32 MovementCount = 0;
    auto RouteOnePass = [this, &Links, &MovementCount]()
    {
        for (ALBFactoryTransportLink* Link : Links)
        {
            AActor* SourceOwner = Link->GetSourcePort()->GetOwner();
            AActor* TargetOwner = Link->GetTargetPort()->GetOwner();
            FString Reason;
            bool bMoved = false;
            if (ALBFactoryBuildMachine* SourceMachine = Cast<ALBFactoryBuildMachine>(SourceOwner))
            {
                // The inbound coordinator owns lorry/crane/AGV handoff; never teleport around it.
                if (SourceMachine->GetMachineType() == ELBFactoryBuildMachineType::InboundDeliveryDock) continue;
                if (ALBPressShopStorageZone* TargetStorage = Cast<ALBPressShopStorageZone>(TargetOwner))
                    bMoved = SourceMachine->GetOutputUnitCount() > 0 && TargetStorage->GetAvailableCapacity() > 0
                        && TransferMachineOutputToStorage(SourceMachine, TargetStorage, Reason);
                else if (ALBFactoryBuildMachine* TargetMachine = Cast<ALBFactoryBuildMachine>(TargetOwner))
                    bMoved = SourceMachine->GetOutputUnitCount() > 0 && TargetMachine->CanAcceptInputUnit()
                        && TransferMachineOutputToMachine(SourceMachine, TargetMachine, Reason);
            }
            else if (ALBPressShopStorageZone* SourceStorage = Cast<ALBPressShopStorageZone>(SourceOwner))
            {
                if (ALBFactoryBuildMachine* TargetMachine = Cast<ALBFactoryBuildMachine>(TargetOwner))
                    bMoved = SourceStorage->GetOccupancy() > 0 && TargetMachine->CanAcceptInputUnit()
                        && TransferStorageToMachine(SourceStorage, TargetMachine, Reason);
                else if (ALBPressTrainAStation* TargetTrain = Cast<ALBPressTrainAStation>(TargetOwner))
                    bMoved = SourceStorage->GetOccupancy() > 0
                        && TargetTrain->GetHMIStatus().PendingBlankCount < 4
                        && TransferBlankBufferToTrain(SourceStorage, TargetTrain, Reason);
            }
            else if (ALBPressTrainAStation* SourceTrain = Cast<ALBPressTrainAStation>(SourceOwner))
            {
                if (ALBFactoryBuildMachine* TargetMachine = Cast<ALBFactoryBuildMachine>(TargetOwner))
                    bMoved = SourceTrain->GetHMIStatus().PendingPanelCount > 0 && TargetMachine->CanAcceptInputUnit()
                        && TransferTrainPanelToInspection(SourceTrain, TargetMachine, Reason);
            }
            if (bMoved) ++MovementCount;
        }
    };

    // Empty downstream buffers first, then process at most one unit per machine, then clear outputs.
    RouteOnePass();

    FString BodyWeldSummary;
    const int32 BodyWeldActionCount = ExecuteBodyWeldIntegrationStep(BodyWeldSummary);
    int32 StartedTrainCount = 0;
    if (bConsoleFreeTrainAutostartEnabled)
    {
        TArray<ALBPressTrainAStation*> Trains;
        for (TActorIterator<ALBPressTrainAStation> It(GetWorld()); It; ++It)
            if (IsValid(*It)) Trains.Add(*It);
        Trains.Sort([](const ALBPressTrainAStation& A, const ALBPressTrainAStation& B)
        {
            return A.GetTrainId().ToString() < B.GetTrainId().ToString();
        });
        for (ALBPressTrainAStation* Train : Trains)
        {
            const FLBPressTrainAHMIStatus Status = Train->GetHMIStatus();
            if (Status.PendingBlankCount <= 0
                || Status.State == ELBPressTrainAState::Cycling
                || Status.State == ELBPressTrainAState::Stopping) continue;
            FString StartReason;
            if (TryStartConsoleFreeTrain(Train, StartReason)) ++StartedTrainCount;
        }
    }
    TArray<ALBFactoryBuildMachine*> Machines;
    for (TActorIterator<ALBFactoryBuildMachine> It(GetWorld()); It; ++It) Machines.Add(*It);
    Machines.Sort([](const ALBFactoryBuildMachine& A, const ALBFactoryBuildMachine& B)
    {
        if (A.InputPort->ProcessStage != B.InputPort->ProcessStage)
            return A.InputPort->ProcessStage > B.InputPort->ProcessStage;
        return A.GetMachineId().ToString() < B.GetMachineId().ToString();
    });
    int32 AdvancedCount = 0;
    int32 ProcessedCount = 0;
    for (ALBFactoryBuildMachine* Machine : Machines)
    {
        if (Machine->GetMachineType() == ELBFactoryBuildMachineType::InboundDeliveryDock) continue;
        FName UnitId;
        bool bCompleted = false;
        if (Machine->AdvanceAutomaticProcess(UnitId, bCompleted))
        {
            ++AdvancedCount;
            if (bCompleted)
            {
                ++ProcessedCount;
                if (Machine->GetMachineType() == ELBFactoryBuildMachineType::InspectionCell)
                    if (FLBPanelLineageRecord* Panel = FindLineageByPanelId(UnitId))
                        Panel->Stage = ELBPanelFlowStage::Inspected;
            }
        }
        else Machine->RefreshOperatingState();
    }
    RouteOnePass();

    int32 StarvedCount = 0;
    int32 BlockedCount = 0;
    for (ALBFactoryBuildMachine* Machine : Machines)
    {
        Machine->RefreshOperatingState();
        StarvedCount += Machine->GetOperatingState() == ELBFactoryMachineOperatingState::Starved ? 1 : 0;
        BlockedCount += Machine->GetOperatingState() == ELBFactoryMachineOperatingState::Blocked ? 1 : 0;
    }
    OutSummary = FString::Printf(
        TEXT("AUTOMATIC FLOW: %d MOVED, %d TRAINS STARTED, %d ADVANCED, %d COMPLETED, %d BODY WELD, %d STARVED, %d BLOCKED"),
        MovementCount, StartedTrainCount, AdvancedCount, ProcessedCount,
        BodyWeldActionCount, StarvedCount, BlockedCount);
    LastAutomaticFlowSummary = OutSummary;
    return MovementCount + AdvancedCount + BodyWeldActionCount;
}
