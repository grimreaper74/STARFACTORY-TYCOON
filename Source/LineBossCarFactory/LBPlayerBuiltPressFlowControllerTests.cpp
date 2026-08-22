#include "LBPlayerBuiltPressFlowController.h"

#include "Engine/World.h"
#include "LBECoatLineActor.h"
#include "LBFactoryBuildMachine.h"
#include "LBFactoryConnectionSubsystem.h"
#include "LBFactoryTransportLink.h"
#include "LBCompactStillageFLT.h"
#include "LBPressShopStorageZone.h"
#include "LBPressTrainAStation.h"
#include "LBStillageFLTFleetController.h"
#include "LBVehiclePanelCatalog.h"
#include "Engine/Engine.h"
#include "Misc/AutomationTest.h"

#if WITH_DEV_AUTOMATION_TESTS

namespace
{
    UWorld* MakeInitialisedPhysicalFLTWorld(const FName Name)
    {
        UWorld* World = UWorld::CreateWorld(EWorldType::Game, false, Name);
        if (!World || !GEngine)
        {
            if (World) World->DestroyWorld(false);
            return nullptr;
        }
        FWorldContext& Context = GEngine->CreateNewWorldContext(EWorldType::Game);
        Context.SetCurrentWorld(World);
        World->InitializeActorsForPlay(FURL());
        World->BeginPlay();
        return World;
    }

    void DestroyInitialisedPhysicalFLTWorld(UWorld* World)
    {
        if (!World) return;
        World->DestroyWorld(false);
        if (GEngine) GEngine->DestroyWorldContext(World);
    }

    FName MakeBodyWeldFlowPanelId(const FName Family, const int32 Serial)
    {
        return FName(*FString::Printf(TEXT("PTA-PANEL-CAIRNWELL_2040-%s-%06d"),
            *Family.ToString(), Serial));
    }

    FLBBodyWeldStillageInventory MakeBodyWeldFlowStillage(const FName StillageId,
        const FName OrderId, const FName Family, const int32 Serial,
        const int64 DeliverySequence)
    {
        FLBBodyWeldStillageInventory Stillage;
        Stillage.StillageId = StillageId;
        Stillage.OrderId = OrderId;
        Stillage.VehicleModelId = TEXT("CAIRNWELL_2040");
        Stillage.PanelTypeId = Family;
        Stillage.DeliverySequence = DeliverySequence;
        if (const FLBStampedPanelDefinition* Definition =
            LBCairnwell2040PanelCatalog::Find(Stillage.VehicleModelId, Family))
        {
            Stillage.CapacityPanels = Definition->StillageCapacity;
        }
        FLBBodyWeldPanelUnit& Panel = Stillage.PanelUnits.AddDefaulted_GetRef();
        Panel.PanelId = MakeBodyWeldFlowPanelId(Family, Serial);
        Panel.OrderId = OrderId;
        Panel.VehicleModelId = Stillage.VehicleModelId;
        Panel.PanelTypeId = Family;
        Panel.StillageId = StillageId;
        return Stillage;
    }

    FLBPlayerBuiltPressFlowSaveState MakeBodyWeldFlowManifest(const FName OrderId,
        const FName Family, const FName StillageId, const int32 PanelSerial,
        const bool bAcceptedByBodyWeld = false,
        const FName WeldLineId = NAME_None)
    {
        FLBPlayerBuiltPressFlowSaveState State;
        FLBVehiclePanelBatch& Batch = State.PanelBatches.AddDefaulted_GetRef();
        Batch.OrderId = OrderId;
        Batch.VehicleModelId = TEXT("CAIRNWELL_2040");
        Batch.PanelTypeId = Family;
        Batch.RequestedQuantity = 1;
        Batch.DispatchedQuantity = 1;
        FLBPanelLineageRecord& Panel = State.PanelLineage.AddDefaulted_GetRef();
        Panel.PanelId = MakeBodyWeldFlowPanelId(Family, PanelSerial);
        Panel.BlankId = FName(*FString::Printf(TEXT("BLANK-BODY-WELD-%06d"), PanelSerial));
        Panel.OrderId = OrderId;
        Panel.VehicleModelId = Batch.VehicleModelId;
        Panel.PanelTypeId = Family;
        Panel.StillageId = StillageId;
        Panel.Disposition = ELBPanelDisposition::Good;
        Panel.Stage = bAcceptedByBodyWeld
            ? ELBPanelFlowStage::BodyWeldInventory : ELBPanelFlowStage::WeldShopIntake;
        FLBPanelStillageLoad& Load = State.PanelStillages.AddDefaulted_GetRef();
        Load.StillageId = StillageId;
        Load.OrderId = OrderId;
        Load.VehicleModelId = Batch.VehicleModelId;
        Load.PanelTypeId = Family;
        if (const FLBStampedPanelDefinition* Definition =
            LBCairnwell2040PanelCatalog::Find(Load.VehicleModelId, Family))
        {
            Load.CapacityPanels = Definition->StillageCapacity;
        }
        Load.PanelIds.Add(Panel.PanelId);
        Load.bReadyForWeld = true;
        Load.bDeliveredToWeld = true;
        Load.bAcceptedByBodyWeld = bAcceptedByBodyWeld;
        Load.WeldLineId = bAcceptedByBodyWeld ? WeldLineId : NAME_None;
        Load.WeldDeliverySequence = bAcceptedByBodyWeld ? 1 : 0;
        State.NextBodyWeldDeliverySequence = bAcceptedByBodyWeld ? 2 : 1;
        return State;
    }

    ALBFactoryTransportLink* MakeBodyWeldFlowLink(UWorld* World,
        ULBFactoryProcessPortComponent* Source, ULBFactoryProcessPortComponent* Target)
    {
        ALBFactoryTransportLink* Link = World
            ? World->SpawnActor<ALBFactoryTransportLink>() : nullptr;
        return Link && Link->Configure(Source, Target) ? Link : nullptr;
    }
}

IMPLEMENT_SIMPLE_AUTOMATION_TEST(FLBPlayerBuiltPressEndToEndFlowTest,
    "LineBoss.FactoryBuilder.MaterialFlow.InboundCoilToWeldShopStillage",
    EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)

bool FLBPlayerBuiltPressEndToEndFlowTest::RunTest(const FString& Parameters)
{
    UWorld* World = UWorld::CreateWorld(EWorldType::Game, false, TEXT("LB_PlayerBuilt_EndToEndFlow"));
    ULBFactoryConnectionSubsystem* Connections = World ? NewObject<ULBFactoryConnectionSubsystem>(World) : nullptr;
    ALBPlayerBuiltPressFlowController* Flow = World ? World->SpawnActor<ALBPlayerBuiltPressFlowController>() : nullptr;
    auto SpawnMachine = [World](const FName Id, const ELBFactoryBuildMachineType Type, const FVector& Location)
    {
        ALBFactoryBuildMachine* Machine = World->SpawnActor<ALBFactoryBuildMachine>(
            ALBFactoryBuildMachine::StaticClass(), FTransform(Location));
        return Machine && Machine->Configure(Id, Type) ? Machine : nullptr;
    };
    ALBFactoryBuildMachine* Inbound = SpawnMachine(TEXT("INBOUND-001"),
        ELBFactoryBuildMachineType::InboundDeliveryDock, FVector(0.0f, -2500.0f, 0.0f));
    ALBFactoryBuildMachine* PR002 = SpawnMachine(TEXT("PR002-001"),
        ELBFactoryBuildMachineType::CoilWeighInspectionCell, FVector(0.0f, -2100.0f, 0.0f));
    ALBFactoryBuildMachine* Depack = SpawnMachine(TEXT("DEPACK-001"),
        ELBFactoryBuildMachineType::DepackagingRobot, FVector(0.0f, -900.0f, 0.0f));
    ALBFactoryBuildMachine* Decoiler = SpawnMachine(TEXT("DECOILER-001"),
        ELBFactoryBuildMachineType::DecoilerFeeder, FVector(0.0f, 300.0f, 0.0f));
    ALBFactoryBuildMachine* Inspection = SpawnMachine(TEXT("INSPECT-001"),
        ELBFactoryBuildMachineType::InspectionCell, FVector(0.0f, 8784.0f, 0.0f));
    ALBFactoryBuildMachine* Outbound = SpawnMachine(TEXT("OUTBOUND-001"),
        ELBFactoryBuildMachineType::OutboundPanelDock, FVector(0.0f, 11234.0f, 0.0f));
    ALBPressShopStorageZone* Coils = World->SpawnActor<ALBPressShopStorageZone>(
        ALBPressShopStorageZone::StaticClass(), FTransform(FVector(0.0f, -1700.0f, 0.0f)));
    ALBPressShopStorageZone* Blanks = World->SpawnActor<ALBPressShopStorageZone>(
        ALBPressShopStorageZone::StaticClass(), FTransform(FVector(0.0f, 1200.0f, 0.0f)));
    ALBPressShopStorageZone* Finished = World->SpawnActor<ALBPressShopStorageZone>(
        ALBPressShopStorageZone::StaticClass(), FTransform(FVector(0.0f, 10084.0f, 0.0f)));
    ALBPressShopStorageZone* EmptyStillages = World->SpawnActor<ALBPressShopStorageZone>(
        ALBPressShopStorageZone::StaticClass(), FTransform(FVector(1200.0f, 10084.0f, 0.0f)));
    ALBPressTrainAStation* Train = World->SpawnActor<ALBPressTrainAStation>(
        ALBPressTrainAStation::StaticClass(), FTransform(FVector(0.0f, 1500.0f, 0.0f)));
    TestTrue(TEXT("Traceable storage buffers configure"), Coils && Blanks && Finished && EmptyStillages
        && Coils->Configure(TEXT("SZ-COIL-001"), ELBPressShopStorageType::BareCoils, 12, FVector(300.0f))
        && Blanks->Configure(TEXT("SZ-BLANK-001"), ELBPressShopStorageType::PreparedBlanks, 12, FVector(300.0f))
        && Finished->Configure(TEXT("SZ-PANEL-001"), ELBPressShopStorageType::FinishedPanelStillages, 12, FVector(300.0f))
        && EmptyStillages->Configure(TEXT("SZ-EMPTY-STL-001"),
            ELBPressShopStorageType::EmptyPanelStillages, 4, FVector(300.0f))
        && EmptyStillages->TryStoreIdentifiedUnit(TEXT("EMPTY-STL-TEST-001")));
    TestNotNull(TEXT("Transactional player-built flow authority exists"), Flow);
    TestNotNull(TEXT("Native press train exists"), Train);
    if (!Connections || !Flow || !Inbound || !PR002 || !Depack || !Decoiler || !Inspection || !Outbound
        || !Coils || !Blanks || !Finished || !EmptyStillages || !Train)
    {
        if (World) World->DestroyWorld(false);
        return false;
    }

    auto Link = [this, Connections](ULBFactoryProcessPortComponent* Source,
        ULBFactoryProcessPortComponent* Target, const TCHAR* Description)
    {
        ALBFactoryTransportLink* Created = nullptr;
        FString Reason;
        TestTrue(Description, Connections->Connect(Source, Target, Created, Reason));
        return Created != nullptr;
    };
    TestTrue(TEXT("Every required player-built process stage is present exactly in order"),
        Inbound->OutputPort->ProcessStage == LBFactoryProcessStage::InboundUnloading
        && PR002->InputPort->ProcessStage == LBFactoryProcessStage::PR002WeighInspection
        && Coils->IngressPoint->ProcessStage == LBFactoryProcessStage::CoilStorage
        && Depack->InputPort->ProcessStage == LBFactoryProcessStage::DepackAndIdentify
        && Decoiler->InputPort->ProcessStage == LBFactoryProcessStage::DecoilerThreader
        && Blanks->IngressPoint->ProcessStage == LBFactoryProcessStage::PreparedBlankBuffer
        && Train->FactoryInputPort->ProcessStage == LBFactoryProcessStage::PressTrain
        && Inspection->InputPort->ProcessStage == LBFactoryProcessStage::Inspection
        && Finished->IngressPoint->ProcessStage == LBFactoryProcessStage::WIPPanelStillageBuffer
        && Outbound->InputPort->ProcessStage == LBFactoryProcessStage::WeldShopIntake
        && Inspection->OutputPort->MaterialClass == ELBFactoryMaterialClass::InspectedPanel
        && Finished->IngressPoint->MaterialClass == ELBFactoryMaterialClass::InspectedPanel
        && Finished->EgressPoint->MaterialClass == ELBFactoryMaterialClass::Stillage);
    TestTrue(TEXT("Empty stillage store is logistics-only exact inventory"),
        EmptyStillages->IngressPoint->ProcessStage == 0
        && EmptyStillages->EgressPoint->ProcessStage == 0
        && EmptyStillages->IngressPoint->MaterialClass == ELBFactoryMaterialClass::Stillage
        && EmptyStillages->GetOccupancy() == 1);
    TestTrue(TEXT("Complete ordered topology links"),
        Link(Inbound->OutputPort, PR002->InputPort, TEXT("Inbound links to PR002 weigh and inspection"))
        && Link(PR002->OutputPort, Coils->IngressPoint, TEXT("PR002 links to coil storage"))
        && Link(Coils->EgressPoint, Depack->InputPort, TEXT("Coil storage links to depackaging"))
        && Link(Depack->OutputPort, Decoiler->InputPort, TEXT("Depackaging links to decoiler"))
        && Link(Decoiler->OutputPort, Blanks->IngressPoint, TEXT("Decoiler links to blank buffer"))
        && Link(Blanks->EgressPoint, Train->FactoryInputPort, TEXT("Blank buffer links to native press"))
        && Link(Train->FactoryOutputPort, Inspection->InputPort, TEXT("Native press links to inspection"))
        && Link(Inspection->OutputPort, Finished->IngressPoint, TEXT("Inspection links to pressed-panel WIP stillages"))
        && Link(Finished->EgressPoint, Outbound->InputPort, TEXT("Ready WIP stillage links to weld shop intake")));

    FString Reason;
    FName ProcessedId;
    TestTrue(TEXT("Inbound lorry supplies identified coil"), Inbound->ReceiveDeliveredUnit(TEXT("COIL-HEAT-0001")));
    TestTrue(TEXT("Identified coil reaches PR002 before storage"),
        Flow->TransferMachineOutputToMachine(Inbound, PR002, Reason));
    TestTrue(TEXT("PR002 weighs and inspects without losing coil identity"),
        Flow->ProcessMachine(PR002, ProcessedId, Reason));
    TestEqual(TEXT("PR002 output identity is unchanged"), ProcessedId, FName(TEXT("COIL-HEAT-0001")));
    TestTrue(TEXT("Inspected coil enters coil storage"), Flow->TransferMachineOutputToStorage(PR002, Coils, Reason));
    TestEqual(TEXT("Coil storage retains exact identity"), Coils->GetIdentifiedUnitCount(), 1);
    TestTrue(TEXT("Stored coil transfers to depackaging"), Flow->TransferStorageToMachine(Coils, Depack, Reason));
    TestTrue(TEXT("Depackaging removes wrapping without losing coil identity"), Flow->ProcessMachine(Depack, ProcessedId, Reason));
    TestEqual(TEXT("Depackaging output identity is unchanged"), ProcessedId, FName(TEXT("COIL-HEAT-0001")));
    TestTrue(TEXT("Depackaged coil transfers to decoiler"), Flow->TransferMachineOutputToMachine(Depack, Decoiler, Reason));
    TestTrue(TEXT("Decoiler creates an identified blank lot"), Flow->ProcessMachine(Decoiler, ProcessedId, Reason));
    TestTrue(TEXT("Blank lot receives deterministic identity"), ProcessedId.ToString().StartsWith(TEXT("BLANK-")));
    const FName BlankId = ProcessedId;
    TestTrue(TEXT("Blank lot enters prepared storage"), Flow->TransferMachineOutputToStorage(Decoiler, Blanks, Reason));
    FLBVehiclePanelBatch DoorBatch;
    DoorBatch.OrderId = TEXT("ORDER-2040-FRONT-DOOR-L-001");
    DoorBatch.VehicleModelId = TEXT("CAIRNWELL_2040");
    DoorBatch.PanelTypeId = TEXT("DOOR_FRONT_LEFT");
    DoorBatch.RequestedQuantity = 1;
    TestTrue(TEXT("Approved Cairnwell 2040 panel order is queued before stamping"),
        Flow->QueuePanelBatch(DoorBatch, Reason));
    TestTrue(TEXT("Prepared blank enters native press reservation"), Flow->TransferBlankBufferToTrain(Blanks, Train, Reason));
    TestEqual(TEXT("Native press receives the exact generated blank"), Train->GetHMIStatus().OldestPendingBlankId, BlankId);
    TestEqual(TEXT("Gameplay handoff installs the ordered vehicle recipe"),
        Train->GetActiveVehicleModelId(), DoorBatch.VehicleModelId);
    TestEqual(TEXT("Gameplay handoff installs the ordered panel recipe"),
        Train->GetActivePanelTypeId(), DoorBatch.PanelTypeId);
    TestEqual(TEXT("Gameplay handoff installs a non-empty automatic die identity"),
        Train->GetActiveDieId(), FName(TEXT("AUTO_DOOR_FRONT_LEFT")));

    Train->SetAccessInterlocksClosed(true);
    Train->SetSafetyCircuitHealthy(true);
    Train->SetEmergencyStopActive(false);
    Train->SetDestackHealthy(true);
    Train->SetTransferHealthy(true);
    Train->SetHydraulicPressure(280.0f);
    Train->SetPressLoad(45.0f);
    Train->SetInspectionHealthy(true);
    Train->SetStillageOutputClear(true);
    TestTrue(TEXT("Native press powers on"), Train->ExecuteRemoteCommand(ELBPressTrainACommand::PowerOn,
        TEXT("MW.MCR.TRAIN_A.CONSOLE"), TEXT("CW.MW.CONTROL_ROOM")));
    TestTrue(TEXT("Native press starts its real seven-stage cycle"), Train->ExecuteRemoteCommand(
        ELBPressTrainACommand::Start, TEXT("MW.MCR.TRAIN_A.CONSOLE"), TEXT("CW.MW.CONTROL_ROOM")));
    Train->Tick(6.1f);
    TestEqual(TEXT("Native press produces one panel"), Train->GetHMIStatus().PendingPanelCount, 1);
    TestTrue(TEXT("Panel transfers to inspection"), Flow->TransferTrainPanelToInspection(Train, Inspection, Reason));
    TestTrue(TEXT("Inspection processes the identified panel"), Flow->ProcessMachine(Inspection, ProcessedId, Reason));
    const FName PanelId = ProcessedId;
    TestFalse(TEXT("Inspected panel identity is present"), PanelId.IsNone());
    const bool bPacked = Flow->TransferMachineOutputToStorage(Inspection, Finished, Reason);
    if (!bPacked) AddInfo(Reason);
    TestTrue(TEXT("Inspected panel is packed into a physical WIP stillage"), bPacked);
    const TArray<FLBPanelLineageRecord> Lineage = Flow->GetPanelLineage();
    const TArray<FLBPanelStillageLoad> Loads = Flow->GetPanelStillages();
    TestEqual(TEXT("One panel lineage record survives the full press path"), Lineage.Num(), 1);
    TestEqual(TEXT("One physical WIP stillage occupies one storage slot"), Finished->GetOccupancy(), 1);
    TestEqual(TEXT("Opening the load consumes the exact empty-stillage inventory"),
        EmptyStillages->GetOccupancy(), 0);
    TestEqual(TEXT("One WIP stillage manifest exists"), Loads.Num(), 1);
    if (Lineage.Num() == 1 && Loads.Num() == 1)
    {
        TestEqual(TEXT("Lineage preserves the identified pressed panel"), Lineage[0].PanelId, PanelId);
        TestEqual(TEXT("Lineage preserves its source blank"), Lineage[0].BlankId, BlankId);
        TestEqual(TEXT("Lineage is assigned to the physical stillage"),
            Lineage[0].StillageId, Loads[0].StillageId);
        TestEqual(TEXT("Flow reuses the supplied empty stillage rather than inventing one"),
            Loads[0].StillageId, FName(TEXT("EMPTY-STL-TEST-001")));
        TestTrue(TEXT("Stillage manifest contains the real panel ID"), Loads[0].PanelIds.Contains(PanelId));
        TestEqual(TEXT("Front-door stillage uses the approved gameplay capacity"), Loads[0].CapacityPanels, 20);
        TestTrue(TEXT("A final one-panel order closes as a ready partial stillage"), Loads[0].bReadyForWeld);
        TestNotEqual(TEXT("A stillage is not a renamed individual panel"), Loads[0].StillageId, PanelId);
    }
    const FName StillageId = Loads.Num() == 1 ? Loads[0].StillageId : NAME_None;
    TestTrue(TEXT("Only the ready WIP stillage transfers to weld-shop intake"),
        Flow->TransferStorageToMachine(Finished, Outbound, Reason));
    TestTrue(TEXT("Compatibility intake completes the stillage handoff"),
        Flow->ProcessMachine(Outbound, ProcessedId, Reason));
    TestEqual(TEXT("Weld intake preserves the physical stillage identity"), ProcessedId, StillageId);
    TestEqual(TEXT("One WIP stillage reaches weld-shop intake"), Outbound->GetCompletedUnitCount(), 1);
    const TArray<FLBPanelStillageLoad> DeliveredLoads = Flow->GetPanelStillages();
    if (DeliveredLoads.Num() == 1)
        TestTrue(TEXT("Manifest records delivery to body weld"), DeliveredLoads[0].bDeliveredToWeld);
    TestTrue(TEXT("Weld returns the same unloaded stillage to the empty store"),
        Flow->ReturnEmptyStillageFromWeld(StillageId, EmptyStillages, Reason));
    TestTrue(TEXT("Returned empty identity is physically back in inventory"),
        EmptyStillages->ContainsIdentifiedUnit(StillageId));
    const TArray<FLBPanelStillageLoad> ReturnedLoads = Flow->GetPanelStillages();
    if (ReturnedLoads.Num() == 1)
        TestTrue(TEXT("Manifest records the closed empty-stillage loop"), ReturnedLoads[0].bReturnedEmpty);

    World->DestroyWorld(false);
    return true;
}

IMPLEMENT_SIMPLE_AUTOMATION_TEST(FLBPlayerBuiltPhysicalStillageFLTHandoffTest,
    "LineBoss.FactoryBuilder.MaterialFlow.PhysicalStillageFLTExactHandoff",
    EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)

bool FLBPlayerBuiltPhysicalStillageFLTHandoffTest::RunTest(const FString& Parameters)
{
    UWorld* World = MakeInitialisedPhysicalFLTWorld(
        TEXT("LB_PhysicalStillageFLT_Handoff"));
    ULBFactoryConnectionSubsystem* Connections = World
        ? NewObject<ULBFactoryConnectionSubsystem>(World) : nullptr;
    ALBPlayerBuiltPressFlowController* Flow = World
        ? World->SpawnActor<ALBPlayerBuiltPressFlowController>() : nullptr;
    ALBPressShopStorageZone* FullStore = World
        ? World->SpawnActor<ALBPressShopStorageZone>(ALBPressShopStorageZone::StaticClass(),
            FVector::ZeroVector, FRotator::ZeroRotator) : nullptr;
    ALBFactoryBuildMachine* WeldIntake = World
        ? World->SpawnActor<ALBFactoryBuildMachine>(ALBFactoryBuildMachine::StaticClass(),
            FVector(0.0f, 2600.0f, 0.0f), FRotator::ZeroRotator) : nullptr;
    ALBStillageFLTFleetController* Fleet = World
        ? World->SpawnActor<ALBStillageFLTFleetController>(
            ALBStillageFLTFleetController::StaticClass(), FVector(-800.0f, 650.0f, 0.0f),
            FRotator::ZeroRotator) : nullptr;
    TestTrue(TEXT("Physical press-to-weld authorities configure"), Connections && Flow
        && FullStore && WeldIntake && Fleet
        && FullStore->Configure(TEXT("PRESS-FULL-WIP-PHYSICAL"),
            ELBPressShopStorageType::FinishedPanelStillages, 4,
            FVector(220.0f, 260.0f, 100.0f))
        && WeldIntake->Configure(TEXT("WELD-INTAKE-PHYSICAL"),
            ELBFactoryBuildMachineType::OutboundPanelDock));
    if (!Connections || !Flow || !FullStore || !WeldIntake || !Fleet)
    {
        DestroyInitialisedPhysicalFLTWorld(World);
        return false;
    }

    constexpr const TCHAR* StillageText = TEXT("EMPTY-STL-PHYSICAL-001");
    const FName StillageId(StillageText);
    FLBPlayerBuiltPressFlowSaveState FlowState;
    FLBVehiclePanelBatch& Batch = FlowState.PanelBatches.AddDefaulted_GetRef();
    Batch.OrderId = TEXT("ORDER-PHYSICAL-FLT-001");
    Batch.VehicleModelId = TEXT("CAIRNWELL_2040");
    Batch.PanelTypeId = TEXT("DOOR_FRONT_LEFT");
    Batch.RequestedQuantity = 1;
    Batch.DispatchedQuantity = 1;
    FLBPanelLineageRecord& Panel = FlowState.PanelLineage.AddDefaulted_GetRef();
    Panel.PanelId = TEXT("PTA-PANEL-CAIRNWELL_2040-DOOR_FRONT_LEFT-000001");
    Panel.BlankId = TEXT("BLANK-PHYSICAL-0001");
    Panel.OrderId = Batch.OrderId;
    Panel.VehicleModelId = Batch.VehicleModelId;
    Panel.PanelTypeId = Batch.PanelTypeId;
    Panel.StillageId = StillageId;
    Panel.Disposition = ELBPanelDisposition::Good;
    Panel.Stage = ELBPanelFlowStage::WIPStillage;
    FLBPanelStillageLoad& Load = FlowState.PanelStillages.AddDefaulted_GetRef();
    Load.StillageId = StillageId;
    Load.OrderId = Batch.OrderId;
    Load.VehicleModelId = Batch.VehicleModelId;
    Load.PanelTypeId = Batch.PanelTypeId;
    Load.CapacityPanels = 20;
    Load.PanelIds.Add(Panel.PanelId);
    Load.bReadyForWeld = true;
    TestTrue(TEXT("Ready full-stillage manifest restores"), Flow->RestoreSaveState(FlowState));
    TestTrue(TEXT("Full WIP store initially owns the exact physical ID"),
        FullStore->TryStoreIdentifiedUnit(StillageId));

    ALBFactoryTransportLink* Link = nullptr;
    FString Reason;
    TestTrue(TEXT("Full WIP store is linked to the authored weld intake"),
        Connections->Connect(FullStore->EgressPoint, WeldIntake->InputPort, Link, Reason));
    FString Summary;
    TestTrue(TEXT("Automatic flow dispatches one physical FLT job"),
        Flow->ExecuteAutomaticStep(Summary) >= 1);
    TestTrue(TEXT("Dispatch does not teleport inventory out of full WIP storage"),
        FullStore->ContainsIdentifiedUnit(StillageId));
    TestEqual(TEXT("Weld intake stays empty until the physical delivery event"),
        WeldIntake->GetInputUnitCount(), 0);
    const TArray<FLBPanelStillageLoad> DispatchedLoads = Flow->GetPanelStillages();
    TestTrue(TEXT("Manifest is not delivered merely because an FLT was dispatched"),
        DispatchedLoads.Num() == 1 && !DispatchedLoads[0].bDeliveredToWeld);

    FLBStillageFLTFleetSaveState FleetState;
    TestTrue(TEXT("Fleet exposes one exact traceable dispatch"), Fleet->CaptureSaveState(FleetState));
    TestEqual(TEXT("Only one physical job exists after the first scheduler pass"),
        FleetState.Jobs.Num(), 1);
    Flow->ExecuteAutomaticStep(Summary);
    TestTrue(TEXT("Repeated scheduler ticks still leave source ownership intact"),
        FullStore->ContainsIdentifiedUnit(StillageId));
    TestTrue(TEXT("Fleet state remains capturable after duplicate suppression"),
        Fleet->CaptureSaveState(FleetState));
    TestEqual(TEXT("The ready stillage cannot receive a duplicate outstanding job"),
        FleetState.Jobs.Num(), 1);

    const FLBPlayerBuiltPressFlowSaveState FlowCheckpoint = Flow->CaptureSaveState();
    TestTrue(TEXT("In-flight physical fleet claim restores"),
        Fleet->RestoreSaveState(FleetState));
    TestTrue(TEXT("Undelivered stillage manifest restores beside the fleet claim"),
        Flow->RestoreSaveState(FlowCheckpoint));
    Flow->ExecuteAutomaticStep(Summary);
    TestTrue(TEXT("Restored exact claim remains inspectable"),
        Fleet->CaptureSaveState(FleetState));
    TestEqual(TEXT("Save restore cannot duplicate an outstanding stillage job"),
        FleetState.Jobs.Num(), 1);
    TestTrue(TEXT("Save restore preserves full-store ownership until delivery"),
        FullStore->ContainsIdentifiedUnit(StillageId));

    ALBCompactStillageFLT* Unit = Fleet->GetUnitById(TEXT("LB-FLT-AGV-01"));
    bool bObservedPhysicalDelivery = false;
    for (int32 Step = 0; Unit && Step < 4000; ++Step)
    {
        Fleet->Tick(0.05f);
        Unit->Tick(0.05f);
        const TArray<FLBPanelStillageLoad> Loads = Flow->GetPanelStillages();
        if (Loads.Num() == 1 && Loads[0].bDeliveredToWeld)
        {
            bObservedPhysicalDelivery = true;
            break;
        }
    }
    if (!bObservedPhysicalDelivery && Unit)
    {
        FLBCompactStillageFLTSaveState UnitSnapshot;
        FLBStillageFLTJob JobSnapshot;
        const FName TraceJobId = FleetState.Jobs.IsEmpty()
            ? NAME_None : FleetState.Jobs[0].JobId;
        Unit->CaptureSaveState(UnitSnapshot);
        Fleet->GetJobSnapshot(TraceJobId, JobSnapshot);
        AddInfo(FString::Printf(
            TEXT("FLT trace: phase=%d fault=%d speed=%.2f lift=%.2f location=(%.1f,%.1f,%.1f) job_state=%d pickup=(%.1f,%.1f) dropoff=(%.1f,%.1f)"),
            static_cast<int32>(UnitSnapshot.Phase), static_cast<int32>(UnitSnapshot.Fault),
            UnitSnapshot.CurrentSpeedCmPerSecond, UnitSnapshot.CarriageLiftCm,
            UnitSnapshot.VehicleTransform.GetLocation().X,
            UnitSnapshot.VehicleTransform.GetLocation().Y,
            UnitSnapshot.VehicleTransform.GetLocation().Z,
            static_cast<int32>(JobSnapshot.State),
            JobSnapshot.PickupServicePoint.X, JobSnapshot.PickupServicePoint.Y,
            JobSnapshot.DropoffServicePoint.X, JobSnapshot.DropoffServicePoint.Y));
    }
    TestTrue(TEXT("Physical FLT drop-off emits the authoritative delivery event"),
        bObservedPhysicalDelivery);
    TestFalse(TEXT("Exact stillage leaves full WIP only at physical drop-off"),
        FullStore->ContainsIdentifiedUnit(StillageId));
    TestEqual(TEXT("Weld intake receives exactly one physical stillage"),
        WeldIntake->GetInputUnitCount(), 1);
    const FLBFactoryBuildMachineSaveState WeldState = WeldIntake->CaptureSaveState();
    TestTrue(TEXT("Weld intake receives the same exact stillage identity"),
        WeldState.InputUnitIds.Contains(StillageId));
    const TArray<FLBPanelStillageLoad> DeliveredLoads = Flow->GetPanelStillages();
    const TArray<FLBPanelLineageRecord> DeliveredLineage = Flow->GetPanelLineage();
    TestTrue(TEXT("Manifest commits delivery only after physical arrival"),
        DeliveredLoads.Num() == 1 && DeliveredLoads[0].bDeliveredToWeld);
    TestTrue(TEXT("Panel lineage advances to weld intake with its stillage"),
        DeliveredLineage.Num() == 1
        && DeliveredLineage[0].Stage == ELBPanelFlowStage::WeldShopIntake);

    DestroyInitialisedPhysicalFLTWorld(World);
    return true;
}

IMPLEMENT_SIMPLE_AUTOMATION_TEST(FLBPlayerBuiltAutomaticFlowAndBottleneckTest,
    "LineBoss.FactoryBuilder.MaterialFlow.AutomaticParallelBuffersAndVisibleBottlenecks",
    EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)

bool FLBPlayerBuiltAutomaticFlowAndBottleneckTest::RunTest(const FString& Parameters)
{
    UWorld* World = UWorld::CreateWorld(EWorldType::Game, false, TEXT("LB_AutomaticFlow_Bottlenecks"));
    ULBFactoryConnectionSubsystem* Connections = World ? NewObject<ULBFactoryConnectionSubsystem>(World) : nullptr;
    ALBPlayerBuiltPressFlowController* Flow = World ? World->SpawnActor<ALBPlayerBuiltPressFlowController>() : nullptr;
    ALBPressShopStorageZone* CoilBuffer = World ? World->SpawnActor<ALBPressShopStorageZone>() : nullptr;
    ALBFactoryBuildMachine* DepackA = World ? World->SpawnActor<ALBFactoryBuildMachine>() : nullptr;
    ALBFactoryBuildMachine* DepackB = World ? World->SpawnActor<ALBFactoryBuildMachine>() : nullptr;
    ALBFactoryBuildMachine* BlockedDecoiler = World ? World->SpawnActor<ALBFactoryBuildMachine>() : nullptr;
    TestTrue(TEXT("Automatic-flow authorities configure"), Connections && Flow && CoilBuffer && DepackA && DepackB
        && BlockedDecoiler
        && CoilBuffer->Configure(TEXT("SZ-COIL-AUTO-001"), ELBPressShopStorageType::BareCoils, 4, FVector(300.0f))
        && DepackA->Configure(TEXT("DEPACK-AUTO-A"), ELBFactoryBuildMachineType::DepackagingRobot)
        && DepackB->Configure(TEXT("DEPACK-AUTO-B"), ELBFactoryBuildMachineType::DepackagingRobot)
        && BlockedDecoiler->Configure(TEXT("DECOILER-BLOCK-001"), ELBFactoryBuildMachineType::DecoilerFeeder)
        && BlockedDecoiler->ConfigureGameplayBuffers(2, 1));
    if (!Connections || !Flow || !CoilBuffer || !DepackA || !DepackB || !BlockedDecoiler)
    {
        if (World) World->DestroyWorld(false);
        return false;
    }

    CoilBuffer->SetActorLocation(FVector::ZeroVector);
    DepackA->SetActorLocation(FVector(0.0f, 800.0f, 0.0f));
    DepackB->SetActorLocation(FVector(800.0f, 800.0f, 0.0f));
    TestTrue(TEXT("Two identified coils enter the shared buffer"),
        CoilBuffer->TryStoreIdentifiedUnit(TEXT("COIL-AUTO-0001"))
        && CoilBuffer->TryStoreIdentifiedUnit(TEXT("COIL-AUTO-0002")));
    auto Connect = [Connections](ULBFactoryProcessPortComponent* Source,
        ULBFactoryProcessPortComponent* Target)
    {
        ALBFactoryTransportLink* Link = nullptr;
        FString Reason;
        return Connections->Connect(Source, Target, Link, Reason) && Link;
    };
    TestTrue(TEXT("One buffer branches through real links to two parallel depackaging robots"),
        Connect(CoilBuffer->EgressPoint, DepackA->InputPort)
        && Connect(CoilBuffer->EgressPoint, DepackB->InputPort));

    FString Summary;
    TestTrue(TEXT("Automatic scheduler routes and starts parallel work"), Flow->ExecuteAutomaticStep(Summary) >= 4);
    TestEqual(TEXT("Depackaging requires visible gameplay progress"), DepackA->GetCompletedAutomaticProcessSteps(), 1);
    TestTrue(TEXT("Second scheduler step completes parallel work"), Flow->ExecuteAutomaticStep(Summary) >= 2);
    TestEqual(TEXT("Shared coil buffer is drained"), CoilBuffer->GetOccupancy(), 0);
    TestEqual(TEXT("Parallel robot A processes one coil"), DepackA->GetOutputUnitCount(), 1);
    TestEqual(TEXT("Parallel robot B processes one coil"), DepackB->GetOutputUnitCount(), 1);
    TestTrue(TEXT("Scheduler exposes visible operating summary"), Summary.Contains(TEXT("STARVED"))
        && Summary.Contains(TEXT("BLOCKED")));

    TestTrue(TEXT("Bottleneck machine accepts first unit"), BlockedDecoiler->AcceptInputUnit(TEXT("COIL-BLOCK-1")));
    TestTrue(TEXT("Bottleneck machine accepts second unit"), BlockedDecoiler->AcceptInputUnit(TEXT("COIL-BLOCK-2")));
    FName UnitId;
    TestTrue(TEXT("First unit fills the constrained output buffer"), BlockedDecoiler->ProcessNextUnit(UnitId));
    TestFalse(TEXT("Second unit cannot overwrite a full output buffer"), BlockedDecoiler->ProcessNextUnit(UnitId));
    TestEqual(TEXT("Machine reports a visible blocked state"), BlockedDecoiler->GetOperatingState(),
        ELBFactoryMachineOperatingState::Blocked);
    TestEqual(TEXT("Blocked reason is actionable"), BlockedDecoiler->GetOperatingReason(),
        FString(TEXT("OUTPUT BUFFER FULL")));

    const FLBFactoryBuildMachineSaveState Saved = BlockedDecoiler->CaptureSaveState();
    ALBFactoryBuildMachine* Restored = World->SpawnActor<ALBFactoryBuildMachine>();
    TestTrue(TEXT("Version-two machine state restores"), Restored && Restored->RestoreSaveState(Saved));
    if (Restored)
    {
        TestEqual(TEXT("Output capacity survives save restore"), Restored->GetMaximumOutputBuffer(), 1);
        TestEqual(TEXT("Gameplay process tuning survives save restore"),
            Restored->GetRequiredAutomaticProcessSteps(), 6);
        TestEqual(TEXT("Blocked state survives save restore"), Restored->GetOperatingState(),
            ELBFactoryMachineOperatingState::Blocked);
    }

    World->DestroyWorld(false);
    return true;
}

IMPLEMENT_SIMPLE_AUTOMATION_TEST(FLBPlayerBuiltVehiclePanelBatchTest,
    "LineBoss.FactoryBuilder.MaterialFlow.VehiclePanelBatchScheduling",
    EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)

bool FLBPlayerBuiltVehiclePanelBatchTest::RunTest(const FString& Parameters)
{
    UWorld* World = UWorld::CreateWorld(EWorldType::Game, false, TEXT("LB_VehiclePanelBatch"));
    ALBPlayerBuiltPressFlowController* Flow = World ? World->SpawnActor<ALBPlayerBuiltPressFlowController>() : nullptr;
    ALBPressTrainAStation* Train = World ? World->SpawnActor<ALBPressTrainAStation>() : nullptr;
    TestNotNull(TEXT("Batch scheduler exists"), Flow);
    TestNotNull(TEXT("Press train exists"), Train);
    if (!Flow || !Train)
    {
        if (World) World->DestroyWorld(false);
        return false;
    }

    FLBVehiclePanelBatch Batch;
    Batch.OrderId = TEXT("ORDER-2040-PREPROD-001");
    Batch.PanelTypeId = TEXT("QUARTER_PANEL_LEFT");
    Batch.RequestedQuantity = 10;
    TestEqual(TEXT("New panel orders default to the approved Cairnwell 2040 programme"),
        Batch.VehicleModelId, FName(TEXT("CAIRNWELL_2040")));
    FString Reason;
    TestTrue(TEXT("Player queues a ten-panel vehicle batch without selecting a die"),
        Flow->QueuePanelBatch(Batch, Reason));
    TestEqual(TEXT("Queued batch quantity is retained"), Flow->GetPanelBatches()[0].RequestedQuantity, 10);
    TestTrue(TEXT("Train accepts an automatic panel recipe"), Train->SetActiveProductionRecipe(
        Batch.VehicleModelId, Batch.PanelTypeId, TEXT("AUTO_QUARTER_PANEL_LEFT")));
    const FLBPressTrainASaveState Saved = Train->CaptureSaveState();
    TestEqual(TEXT("Vehicle model persists"), Saved.ActiveVehicleModelId, Batch.VehicleModelId);
    TestEqual(TEXT("Panel type persists"), Saved.ActivePanelTypeId, Batch.PanelTypeId);
    TestEqual(TEXT("Automatic tooling remains internal"), Saved.ActiveDieId, FName(TEXT("AUTO_QUARTER_PANEL_LEFT")));
    const FLBPlayerBuiltPressFlowSaveState FlowSaved = Flow->CaptureSaveState();
    ALBPlayerBuiltPressFlowController* ReloadedFlow = World->SpawnActor<ALBPlayerBuiltPressFlowController>();
    TestTrue(TEXT("Production orders restore"), ReloadedFlow && ReloadedFlow->RestoreSaveState(FlowSaved));
    if (ReloadedFlow)
    {
        TestEqual(TEXT("Restored order count"), ReloadedFlow->GetPanelBatches().Num(), 1);
        TestEqual(TEXT("Restored vehicle order identity"),
            ReloadedFlow->GetPanelBatches()[0].VehicleModelId, FName(TEXT("CAIRNWELL_2040")));
    }

    World->DestroyWorld(false);
    return true;
}

IMPLEMENT_SIMPLE_AUTOMATION_TEST(FLBPlayerBuiltRegisteredModelPanelBatchTest,
    "LineBoss.FactoryBuilder.MaterialFlow.RegisteredModelPanelBatchScheduling",
    EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)

bool FLBPlayerBuiltRegisteredModelPanelBatchTest::RunTest(const FString& Parameters)
{
    (void)Parameters;
    const FName ModelId(TEXT("NORTHSTAR_PRESS_DEVELOPMENT"));
    LBVehicleModelCatalog::UnregisterDevelopmentRecipe(ModelId);

    FLBVehicleModelRecipe Recipe;
    Recipe.ModelId = ModelId;
    Recipe.DisplayName = TEXT("Northstar press-development programme");
    Recipe.RecipeRevisionId = TEXT("NORTHSTAR_PRESS_RECIPE_V001");
    Recipe.PaintRouteProfileId = TEXT("PAINT_ROUTE_EDCOAT_VISIBLE_V001");
    Recipe.GeometryAuthorityId = TEXT("NorthstarGeometry_V001");
    Recipe.PanelGeometryAuthorityId = TEXT("NorthstarPanels_V001");
    Recipe.BaseKitTypeId = TEXT("NORTHSTAR_BIW_BASE_KIT");
    Recipe.bDevelopmentVisual = true;
    Recipe.bPanelGeometryValidated = true;
    Recipe.DefaultRevenuePence = 2500000;
    Recipe.RequiredPanels = {
        { TEXT("NORTHSTAR_HOOD"), TEXT("Northstar hood"),
            ELBPanelHandedness::None, 10, FVector(160.0f, 140.0f, 20.0f),
            NAME_None }
    };

    FString Reason;
    if (!TestTrue(TEXT("a second production-ready programme registers"),
        LBVehicleModelCatalog::RegisterDevelopmentRecipe(Recipe, Reason)))
    {
        return false;
    }

    UWorld* World = UWorld::CreateWorld(EWorldType::Game, false,
        TEXT("LBRegisteredModelPanelBatch"));
    ALBPlayerBuiltPressFlowController* Flow = World
        ? World->SpawnActor<ALBPlayerBuiltPressFlowController>() : nullptr;
    FLBVehiclePanelBatch Batch;
    Batch.OrderId = TEXT("NORTHSTAR-PRESS-ORDER-001");
    Batch.VehicleModelId = ModelId;
    Batch.PanelTypeId = TEXT("NORTHSTAR_HOOD");
    Batch.RequestedQuantity = 6;
    TestTrue(TEXT("the shared Press scheduler queues a selected model's own panel family"),
        Flow && Flow->QueuePanelBatch(Batch, Reason));
    if (Flow && Flow->GetPanelBatches().Num() == 1)
    {
        TestEqual(TEXT("the queued batch retains the selected model identity"),
            Flow->GetPanelBatches()[0].VehicleModelId, ModelId);
    }

    FLBBodyWeldBaseKitUnit BaseKit;
    BaseKit.KitId = TEXT("NORTHSTAR-BIW-000001");
    BaseKit.OrderId = Batch.OrderId;
    BaseKit.VehicleModelId = ModelId;
    BaseKit.KitTypeId = Recipe.BaseKitTypeId;
    TestTrue(TEXT("the Body/Weld delivery ledger accepts the selected model's base-kit family"),
        Flow && Flow->QueueBodyWeldBaseKitDelivery(BaseKit,
            TEXT("NORTHSTAR_STAGE9_ADAPTER"), TEXT("NORTHSTAR_WELD_LINE"),
            Reason));

    FLBVehicleModelRecipe NotReady = Recipe;
    NotReady.ModelId = TEXT("NORTHSTAR_UNVALIDATED");
    NotReady.bPanelGeometryValidated = false;
    TestTrue(TEXT("an unvalidated programme can exist as development data"),
        LBVehicleModelCatalog::RegisterDevelopmentRecipe(NotReady, Reason));
    Batch.VehicleModelId = NotReady.ModelId;
    TestFalse(TEXT("the Press refuses a programme without validated panels"),
        Flow && Flow->QueuePanelBatch(Batch, Reason));
    BaseKit.VehicleModelId = NotReady.ModelId;
    TestFalse(TEXT("the Body/Weld delivery ledger refuses an unvalidated model"),
        Flow && Flow->QueueBodyWeldBaseKitDelivery(BaseKit,
            TEXT("NORTHSTAR_STAGE9_ADAPTER"), TEXT("NORTHSTAR_WELD_LINE"),
            Reason));

    if (World) World->DestroyWorld(false);
    LBVehicleModelCatalog::UnregisterDevelopmentRecipe(ModelId);
    LBVehicleModelCatalog::UnregisterDevelopmentRecipe(NotReady.ModelId);
    return true;
}

IMPLEMENT_SIMPLE_AUTOMATION_TEST(FLBPlayerBuiltSharedIndependentLineRoutingTest,
    "LineBoss.FactoryBuilder.MaterialFlow.SharedAndIndependentPressLines",
    EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)

bool FLBPlayerBuiltSharedIndependentLineRoutingTest::RunTest(const FString& Parameters)
{
    UWorld* World = UWorld::CreateWorld(EWorldType::Game, false, TEXT("LB_SharedIndependentLines"));
    ULBFactoryConnectionSubsystem* Connections = World ? NewObject<ULBFactoryConnectionSubsystem>(World) : nullptr;
    ALBPlayerBuiltPressFlowController* Flow = World ? World->SpawnActor<ALBPlayerBuiltPressFlowController>() : nullptr;
    ALBPressShopStorageZone* Shared = World ? World->SpawnActor<ALBPressShopStorageZone>() : nullptr;
    ALBPressShopStorageZone* Independent = World ? World->SpawnActor<ALBPressShopStorageZone>() : nullptr;
    ALBPressTrainAStation* TrainA = World ? World->SpawnActor<ALBPressTrainAStation>() : nullptr;
    ALBPressTrainAStation* TrainB = World ? World->SpawnActor<ALBPressTrainAStation>() : nullptr;
    ALBPressTrainAStation* TrainC = World ? World->SpawnActor<ALBPressTrainAStation>() : nullptr;
    TestTrue(TEXT("Two line sources and three trains exist"), Connections && Flow && Shared && Independent
        && TrainA && TrainB && TrainC);
    if (!Connections || !Flow || !Shared || !Independent || !TrainA || !TrainB || !TrainC)
    {
        if (World) World->DestroyWorld(false);
        return false;
    }
    TestTrue(TEXT("Prepared-blank sources configure"),
        Shared->Configure(TEXT("LINE_SHARED"), ELBPressShopStorageType::PreparedBlanks, 8, FVector(250.0f))
        && Independent->Configure(TEXT("LINE_INDEPENDENT"), ELBPressShopStorageType::PreparedBlanks, 8, FVector(250.0f)));
    TestTrue(TEXT("Parallel trains receive identities"),
        TrainB->ConfigureTrainVariant(TEXT("TRAIN_B"), TEXT("TRAIN B"), TEXT("AUTO"), FLinearColor::Blue)
        && TrainC->ConfigureTrainVariant(TEXT("TRAIN_C"), TEXT("TRAIN C"), TEXT("AUTO"), FLinearColor::Red));
    auto Connect = [Connections](ULBFactoryProcessPortComponent* Source, ULBFactoryProcessPortComponent* Target)
    {
        ALBFactoryTransportLink* Link = nullptr;
        FString Reason;
        return Connections->Connect(Source, Target, Link, Reason);
    };
    TestTrue(TEXT("One source automatically fans out to two trains"),
        Connect(Shared->EgressPoint, TrainA->FactoryInputPort)
        && Connect(Shared->EgressPoint, TrainB->FactoryInputPort));
    TestTrue(TEXT("Second source remains an independent line"),
        Connect(Independent->EgressPoint, TrainC->FactoryInputPort));
    TestEqual(TEXT("Train A resolves shared line"), Flow->GetProductionLineIdForTrain(TrainA), FName(TEXT("LINE_SHARED")));
    TestEqual(TEXT("Train B resolves same shared line"), Flow->GetProductionLineIdForTrain(TrainB), FName(TEXT("LINE_SHARED")));
    TestEqual(TEXT("Train C resolves independent line"), Flow->GetProductionLineIdForTrain(TrainC), FName(TEXT("LINE_INDEPENDENT")));

    Shared->TryStoreIdentifiedUnit(TEXT("BLANK-SHARED-1"));
    Shared->TryStoreIdentifiedUnit(TEXT("BLANK-SHARED-2"));
    Independent->TryStoreIdentifiedUnit(TEXT("BLANK-INDEP-1"));
    FLBVehiclePanelBatch SharedBatch;
    SharedBatch.OrderId = TEXT("ORDER-SHARED");
    SharedBatch.VehicleModelId = TEXT("CAIRNWELL_2040");
    SharedBatch.PanelTypeId = TEXT("DOOR_FRONT_LEFT");
    SharedBatch.ProductionLineId = TEXT("LINE_SHARED");
    SharedBatch.RequestedQuantity = 2;
    FLBVehiclePanelBatch IndependentBatch;
    IndependentBatch.OrderId = TEXT("ORDER-INDEPENDENT");
    IndependentBatch.VehicleModelId = TEXT("CAIRNWELL_2040");
    IndependentBatch.PanelTypeId = TEXT("HOOD_PANEL");
    IndependentBatch.ProductionLineId = TEXT("LINE_INDEPENDENT");
    IndependentBatch.RequestedQuantity = 1;
    FString Reason;
    TestTrue(TEXT("Both line orders queue"), Flow->QueuePanelBatch(SharedBatch, Reason)
        && Flow->QueuePanelBatch(IndependentBatch, Reason));
    FString Summary;
    Flow->ExecuteAutomaticStep(Summary);
    TestEqual(TEXT("Shared source balances one blank to Train A"), TrainA->GetPendingBlankCount(), 1);
    TestEqual(TEXT("Shared source balances one blank to Train B"), TrainB->GetPendingBlankCount(), 1);
    TestEqual(TEXT("Independent source feeds only Train C"), TrainC->GetPendingBlankCount(), 1);
    TestEqual(TEXT("Shared trains receive the Cairnwell 2040 recipe"), TrainB->GetActiveVehicleModelId(), FName(TEXT("CAIRNWELL_2040")));
    TestEqual(TEXT("Independent train keeps its own Cairnwell panel family"), TrainC->GetActivePanelTypeId(), FName(TEXT("HOOD_PANEL")));

    World->DestroyWorld(false);
    return true;
}

IMPLEMENT_SIMPLE_AUTOMATION_TEST(FLBPlayerBuiltParallelRobotInspectionCapacityTest,
    "LineBoss.FactoryBuilder.MaterialFlow.ParallelRobotInspectionCapacity",
    EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)

bool FLBPlayerBuiltParallelRobotInspectionCapacityTest::RunTest(const FString& Parameters)
{
    UWorld* World = UWorld::CreateWorld(EWorldType::Game, false, TEXT("LB_ParallelRobotInspection"));
    ULBFactoryConnectionSubsystem* Connections = World ? NewObject<ULBFactoryConnectionSubsystem>(World) : nullptr;
    ALBPlayerBuiltPressFlowController* Flow = World ? World->SpawnActor<ALBPlayerBuiltPressFlowController>() : nullptr;
    ALBPressTrainAStation* TrainA = World ? World->SpawnActor<ALBPressTrainAStation>() : nullptr;
    ALBPressTrainAStation* TrainB = World ? World->SpawnActor<ALBPressTrainAStation>() : nullptr;
    ALBFactoryBuildMachine* RobotA = World ? World->SpawnActor<ALBFactoryBuildMachine>() : nullptr;
    ALBFactoryBuildMachine* RobotB = World ? World->SpawnActor<ALBFactoryBuildMachine>() : nullptr;
    TestTrue(TEXT("Two trains and two robotic unload cells exist"), Connections && Flow
        && TrainA && TrainB && RobotA && RobotB);
    if (!Connections || !Flow || !TrainA || !TrainB || !RobotA || !RobotB)
    {
        if (World) World->DestroyWorld(false);
        return false;
    }

    TestTrue(TEXT("Second train and both robotic cells configure"),
        TrainB->ConfigureTrainVariant(TEXT("TRAIN_B"), TEXT("TRAIN B"), TEXT("AUTO"), FLinearColor::Blue)
        && RobotA->Configure(TEXT("ROBOT-INSPECT-001"), ELBFactoryBuildMachineType::InspectionCell)
        && RobotB->Configure(TEXT("ROBOT-INSPECT-002"), ELBFactoryBuildMachineType::InspectionCell));
    // Put each unload cell at the real S07 end of its own parallel train so the
    // connection test also proves the normal automatic-link distance authority.
    TrainB->SetActorLocation(FVector(1000.0f, 0.0f, 0.0f));
    RobotA->SetActorLocation(FVector(0.0f, 7684.0f, 0.0f));
    RobotB->SetActorLocation(FVector(1000.0f, 7684.0f, 0.0f));
    FLBPressTrainASaveState TrainAState = TrainA->CaptureSaveState();
    FLBPressTrainASaveState TrainBState = TrainB->CaptureSaveState();
    TrainAState.PendingPanelIds = { TEXT("PANEL-A-0001") };
    TrainBState.PendingPanelIds = { TEXT("PANEL-B-0001") };
    TestTrue(TEXT("Both trains have a finished panel ready"),
        TrainA->RestoreSaveState(TrainAState) && TrainB->RestoreSaveState(TrainBState));

    auto Connect = [Connections](ULBFactoryProcessPortComponent* Source, ULBFactoryProcessPortComponent* Target)
    {
        ALBFactoryTransportLink* Link = nullptr;
        FString Reason;
        return Connections->Connect(Source, Target, Link, Reason);
    };
    TestTrue(TEXT("Automatic routing fans the train outputs across both robot cells"),
        Connect(TrainA->FactoryOutputPort, RobotA->InputPort)
        && Connect(TrainB->FactoryOutputPort, RobotB->InputPort));

    FString Summary;
    Flow->ExecuteAutomaticStep(Summary);
    TestEqual(TEXT("First robot receives and starts one panel"), RobotA->GetInputUnitCount(), 1);
    TestEqual(TEXT("Second robot adds real parallel capacity"), RobotB->GetInputUnitCount(), 1);
    TestEqual(TEXT("Both train outputs clear in the same automatic pass"),
        TrainA->GetHMIStatus().PendingPanelCount + TrainB->GetHMIStatus().PendingPanelCount, 0);
    TestTrue(TEXT("Both two-step cells advance together"),
        RobotA->GetCompletedAutomaticProcessSteps() == 1
        && RobotB->GetCompletedAutomaticProcessSteps() == 1);

    World->DestroyWorld(false);
    return true;
}

IMPLEMENT_SIMPLE_AUTOMATION_TEST(FLBPlayerBuiltBodyWeldSaveV4ValidationTest,
    "LineBoss.FactoryBuilder.MaterialFlow.BodyWeldSaveV4ValidationAndV3Migration",
    EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)

bool FLBPlayerBuiltBodyWeldSaveV4ValidationTest::RunTest(const FString& Parameters)
{
    const FName OrderId(TEXT("ORDER-WELD-SAVE-001"));
    const FName Family(TEXT("DOOR_FRONT_LEFT"));
    const FName StillageId(TEXT("WIP-STL-WELD-SAVE-001"));
    FLBPlayerBuiltPressFlowSaveState Valid = MakeBodyWeldFlowManifest(
        OrderId, Family, StillageId, 101, true, TEXT("BODY-WELD-SAVE-001"));
    FString Reason;
    TestTrue(TEXT("Public validator accepts complete v4 exact ownership"),
        ALBPlayerBuiltPressFlowController::ValidateSaveState(Valid, Reason));

    FLBBodyWeldBaseKitDeliveryRecord& Pending =
        Valid.PendingBaseKitDeliveries.AddDefaulted_GetRef();
    Pending.BaseKit.KitId = TEXT("BIW-BASE-KIT-SAVE-000001");
    Pending.BaseKit.OrderId = OrderId;
    Pending.BaseKit.DeliverySequence = Valid.NextBodyWeldDeliverySequence++;
    Pending.DeliveryAuthorityId = TEXT("BASE-KIT-ADAPTER-SAVE-001");
    Pending.TargetWeldLineId = TEXT("BODY-WELD-SAVE-001");
    TestTrue(TEXT("Finite pending base-kit authority and sequence validate"),
        ALBPlayerBuiltPressFlowController::ValidateSaveState(Valid, Reason));

    FLBPlayerBuiltPressFlowSaveState DuplicateKit = Valid;
    FLBBodyWeldBaseKitDeliveryRecord Duplicate = DuplicateKit.PendingBaseKitDeliveries[0];
    Duplicate.bTransferred = true;
    DuplicateKit.TransferredBaseKitDeliveries.Add(Duplicate);
    TestFalse(TEXT("One finite kit cannot exist in both ownership ledgers"),
        ALBPlayerBuiltPressFlowController::ValidateSaveState(DuplicateKit, Reason));

    FLBPlayerBuiltPressFlowSaveState BrokenAcceptance = Valid;
    BrokenAcceptance.PanelStillages[0].WeldLineId = NAME_None;
    TestFalse(TEXT("Accepted stillage without its exact weld LineId is rejected"),
        ALBPlayerBuiltPressFlowController::ValidateSaveState(BrokenAcceptance, Reason));

    FLBPlayerBuiltPressFlowSaveState LegacyV3;
    LegacyV3.Version = 3;
    TestTrue(TEXT("Legacy v3 with no smuggled weld ownership remains migratable"),
        ALBPlayerBuiltPressFlowController::ValidateSaveState(LegacyV3, Reason));
    UWorld* World = UWorld::CreateWorld(EWorldType::Game, false, TEXT("LB_Weld_SaveV4"));
    ALBPlayerBuiltPressFlowController* Flow = World
        ? World->SpawnActor<ALBPlayerBuiltPressFlowController>() : nullptr;
    TestTrue(TEXT("v3 restores through the v4 migration path"),
        Flow && Flow->RestoreSaveState(LegacyV3));
    const FLBPlayerBuiltPressFlowSaveState Migrated = Flow
        ? Flow->CaptureSaveState() : FLBPlayerBuiltPressFlowSaveState();
    TestEqual(TEXT("Capture emits v4 after legacy restore"), Migrated.Version, 4);
    TestEqual(TEXT("Migration creates no synthetic base kits"),
        Migrated.PendingBaseKitDeliveries.Num() + Migrated.TransferredBaseKitDeliveries.Num(), 0);

    const FLBPlayerBuiltPressFlowSaveState BeforeRejectedRestore = Flow
        ? Flow->CaptureSaveState() : FLBPlayerBuiltPressFlowSaveState();
    TestFalse(TEXT("Invalid restore fails before mutation"),
        Flow && Flow->RestoreSaveState(BrokenAcceptance));
    const FLBPlayerBuiltPressFlowSaveState AfterRejectedRestore = Flow
        ? Flow->CaptureSaveState() : FLBPlayerBuiltPressFlowSaveState();
    TestEqual(TEXT("Rejected restore retains the prior batch ledger"),
        AfterRejectedRestore.PanelBatches.Num(), BeforeRejectedRestore.PanelBatches.Num());
    TestEqual(TEXT("Rejected restore retains the prior sequence"),
        AfterRejectedRestore.NextBodyWeldDeliverySequence,
        BeforeRejectedRestore.NextBodyWeldDeliverySequence);
    if (World) World->DestroyWorld(false);
    return true;
}

IMPLEMENT_SIMPLE_AUTOMATION_TEST(FLBPlayerBuiltBodyWeldExactTransactionTest,
    "LineBoss.FactoryBuilder.MaterialFlow.BodyWeldExactStage9TransactionAndRollback",
    EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)

bool FLBPlayerBuiltBodyWeldExactTransactionTest::RunTest(const FString& Parameters)
{
    UWorld* World = UWorld::CreateWorld(EWorldType::Game, false, TEXT("LB_Weld_ExactTransaction"));
    ALBPlayerBuiltPressFlowController* Flow = World
        ? World->SpawnActor<ALBPlayerBuiltPressFlowController>() : nullptr;
    ALBFactoryBuildMachine* Dock = World ? World->SpawnActor<ALBFactoryBuildMachine>() : nullptr;
    ALBBodyWeldLineActor* Weld = World ? World->SpawnActor<ALBBodyWeldLineActor>() : nullptr;
    TestTrue(TEXT("Exact stage-9 and weld authorities configure"), Flow && Dock && Weld
        && Dock->Configure(TEXT("OUTBOUND-WELD-TX-001"),
            ELBFactoryBuildMachineType::OutboundPanelDock)
        && Weld->Configure(TEXT("BODY-WELD-TX-001")));
    if (!Flow || !Dock || !Weld)
    {
        if (World) World->DestroyWorld(false);
        return false;
    }
    const FName OrderId(TEXT("ORDER-WELD-TX-001"));
    const FName Family(TEXT("HOOD_PANEL"));
    const FName StillageId(TEXT("WIP-STL-WELD-TX-001"));
    FLBPlayerBuiltPressFlowSaveState FlowState = MakeBodyWeldFlowManifest(
        OrderId, Family, StillageId, 201);
    FLBFactoryBuildMachineSaveState DockState = Dock->CaptureSaveState();
    DockState.CompletedUnitIds.Add(StillageId);
    TestTrue(TEXT("Exact stage-9 prerequisite and manifest restore"),
        Flow->RestoreSaveState(FlowState) && Dock->RestoreSaveState(DockState));
    TestNotNull(TEXT("Only the exact stage-9-to-weld port link is accepted"),
        MakeBodyWeldFlowLink(World, Dock->OutputPort, Weld->GetStillageInputPort()));

    FString Summary;
    TestTrue(TEXT("No-fleet compatibility commits one exact stillage transaction"),
        Flow->ExecuteBodyWeldIntegrationStep(Summary) >= 1);
    TestFalse(TEXT("Stage-9 dock releases only that exact ID"),
        Dock->CaptureSaveState().CompletedUnitIds.Contains(StillageId));
    TestEqual(TEXT("Weld owns the exact panel after the commit"), Weld->GetAvailablePanelCount(), 1);
    const FLBPlayerBuiltPressFlowSaveState Committed = Flow->CaptureSaveState();
    TestTrue(TEXT("Manifest records exact weld owner and deterministic sequence"),
        Committed.PanelStillages.Num() == 1
        && Committed.PanelStillages[0].bAcceptedByBodyWeld
        && Committed.PanelStillages[0].WeldLineId == Weld->GetLineId()
        && Committed.PanelStillages[0].WeldDeliverySequence == 1
        && Committed.PanelLineage[0].Stage == ELBPanelFlowStage::BodyWeldInventory);
    const int32 AvailableAfterCommit = Weld->GetAvailablePanelCount();
    Flow->ExecuteBodyWeldIntegrationStep(Summary);
    TestEqual(TEXT("Restart/retry cannot duplicate accepted exact inventory"),
        Weld->GetAvailablePanelCount(), AvailableAfterCommit);

    ALBPlayerBuiltPressFlowController* RollbackFlow = World
        ? World->SpawnActor<ALBPlayerBuiltPressFlowController>() : nullptr;
    ALBFactoryBuildMachine* RollbackDock = World
        ? World->SpawnActor<ALBFactoryBuildMachine>() : nullptr;
    ALBBodyWeldLineActor* RollbackWeld = World
        ? World->SpawnActor<ALBBodyWeldLineActor>() : nullptr;
    TestTrue(TEXT("Rollback authorities configure"), RollbackFlow && RollbackDock && RollbackWeld
        && RollbackDock->Configure(TEXT("OUTBOUND-WELD-ROLLBACK-001"),
            ELBFactoryBuildMachineType::OutboundPanelDock)
        && RollbackWeld->Configure(TEXT("BODY-WELD-ROLLBACK-001"))
        && RollbackWeld->SetAssignedOrder(OrderId));
    const FName RollbackStillage(TEXT("WIP-STL-WELD-ROLLBACK-001"));
    FLBPlayerBuiltPressFlowSaveState RollbackState = MakeBodyWeldFlowManifest(
        OrderId, Family, RollbackStillage, 301);
    FLBFactoryBuildMachineSaveState RollbackDockState = RollbackDock->CaptureSaveState();
    RollbackDockState.CompletedUnitIds.Add(RollbackStillage);
    FString WeldReason;
    const FLBBodyWeldStillageInventory ExistingDuplicate = MakeBodyWeldFlowStillage(
        TEXT("WIP-STL-EXISTING-DUPLICATE"), OrderId, Family, 301, 1);
    TestTrue(TEXT("Weld is pre-seeded with the duplicate panel identity"),
        RollbackWeld->ReceivePanelStillage(ExistingDuplicate, WeldReason));
    TestTrue(TEXT("Rollback scenario restores without mutation"),
        RollbackFlow->RestoreSaveState(RollbackState)
        && RollbackDock->RestoreSaveState(RollbackDockState));
    TestNotNull(TEXT("Rollback scenario has an otherwise valid exact link"),
        MakeBodyWeldFlowLink(World, RollbackDock->OutputPort,
            RollbackWeld->GetStillageInputPort()));
    const FLBBodyWeldLineSaveState WeldBefore = RollbackWeld->CaptureSaveState();
    const FLBPlayerBuiltPressFlowSaveState FlowBefore = RollbackFlow->CaptureSaveState();
    TestEqual(TEXT("Duplicate identity makes the transaction report no action"),
        RollbackFlow->ExecuteBodyWeldIntegrationStep(Summary), 0);
    TestTrue(TEXT("Failed weld acceptance restores exact dock ownership"),
        RollbackDock->CaptureSaveState().CompletedUnitIds.Contains(RollbackStillage));
    const FLBBodyWeldLineSaveState WeldAfter = RollbackWeld->CaptureSaveState();
    const FLBPlayerBuiltPressFlowSaveState FlowAfter = RollbackFlow->CaptureSaveState();
    TestEqual(TEXT("Failed acceptance adds no weld stillage"),
        WeldAfter.Stillages.Num(), WeldBefore.Stillages.Num());
    TestEqual(TEXT("Failed acceptance consumes no delivery sequence"),
        FlowAfter.NextBodyWeldDeliverySequence, FlowBefore.NextBodyWeldDeliverySequence);
    TestFalse(TEXT("Failed acceptance does not advance manifest ownership"),
        FlowAfter.PanelStillages[0].bAcceptedByBodyWeld);
    if (World) World->DestroyWorld(false);
    return true;
}

IMPLEMENT_SIMPLE_AUTOMATION_TEST(FLBPlayerBuiltBodyWeldSchedulerIntegrationTest,
    "LineBoss.FactoryBuilder.MaterialFlow.BodyWeldFiniteKitEmptyReturnAndEDHandoff",
    EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)

bool FLBPlayerBuiltBodyWeldSchedulerIntegrationTest::RunTest(const FString& Parameters)
{
    UWorld* World = UWorld::CreateWorld(EWorldType::Game, false, TEXT("LB_Weld_Scheduler"));
    ALBPlayerBuiltPressFlowController* Flow = World
        ? World->SpawnActor<ALBPlayerBuiltPressFlowController>() : nullptr;
    ALBFactoryBuildMachine* Adapter = World ? World->SpawnActor<ALBFactoryBuildMachine>() : nullptr;
    ALBBodyWeldLineActor* Weld = World ? World->SpawnActor<ALBBodyWeldLineActor>() : nullptr;
    const FName OrderId(TEXT("ORDER-WELD-SCHEDULER-001"));
    const FName WeldLineId(TEXT("BODY-WELD-SCHEDULER-001"));
    TestTrue(TEXT("Finite-kit adapter and weld line configure"), Flow && Adapter && Weld
        && Adapter->Configure(TEXT("BASE-KIT-ADAPTER-001"),
            ELBFactoryBuildMachineType::OutboundPanelDock)
        && Weld->Configure(WeldLineId) && Weld->SetAssignedOrder(OrderId));
    if (!Flow || !Adapter || !Weld)
    {
        if (World) World->DestroyWorld(false);
        return false;
    }
    Adapter->OutputPort->MaterialClass = ELBFactoryMaterialClass::GeneralParts;
    Adapter->OutputPort->TransportKind = ELBFactoryTransportKind::AGVHandoff;
    Adapter->OutputPort->ProcessStage = LBFactoryProcessStage::WeldShopIntake;
    TestNotNull(TEXT("Finite base-kit uses an explicit saved stage-9 adapter link"),
        MakeBodyWeldFlowLink(World, Adapter->OutputPort, Weld->GetBaseKitInputPort()));

    FLBPlayerBuiltPressFlowSaveState FlowState;
    int32 Serial = 401;
    int64 DeliverySequence = 1;
    FString WeldReason;
    for (const FName Family : ALBBodyWeldLineActor::GetRequiredPanelFamilies())
    {
        const FName StillageId(*FString::Printf(TEXT("WIP-STL-SCHED-%03d"), Serial));
        FLBPlayerBuiltPressFlowSaveState One = MakeBodyWeldFlowManifest(
            OrderId, Family, StillageId, Serial, true, WeldLineId);
        One.PanelStillages[0].WeldDeliverySequence = DeliverySequence;
        FlowState.PanelBatches.Append(One.PanelBatches);
        FlowState.PanelLineage.Append(One.PanelLineage);
        FlowState.PanelStillages.Append(One.PanelStillages);
        TestTrue(TEXT("Weld receives each exact accepted panel stillage"),
            Weld->ReceivePanelStillage(MakeBodyWeldFlowStillage(
                StillageId, OrderId, Family, Serial, DeliverySequence), WeldReason));
        ++Serial;
        ++DeliverySequence;
    }
    FlowState.NextBodyWeldDeliverySequence = DeliverySequence;
    TestTrue(TEXT("Eleven-family exact manifest restores"), Flow->RestoreSaveState(FlowState));
    FLBBodyWeldBaseKitUnit Kit;
    Kit.KitId = TEXT("BIW-BASE-KIT-SCHEDULER-000001");
    Kit.OrderId = OrderId;
    FString Reason;
    TestTrue(TEXT("One finite kit enters the explicit pending-delivery ledger"),
        Flow->QueueBodyWeldBaseKitDelivery(Kit, Adapter->GetMachineId(), WeldLineId, Reason));
    FString Summary;
    TestTrue(TEXT("Scheduler transfers, reserves and commits the complete exact recipe"),
        Flow->ExecuteBodyWeldIntegrationStep(Summary) >= 3);
    TestEqual(TEXT("Finite kit leaves pending ownership exactly once"),
        Flow->GetPendingBodyWeldBaseKitDeliveries().Num(), 0);
    TestEqual(TEXT("Finite kit remains in the transferred audit ledger"),
        Flow->GetTransferredBodyWeldBaseKitDeliveries().Num(), 1);
    TestEqual(TEXT("Eleven exact empty stillages become returnable on consumption"),
        Weld->GetPendingEmptyReturnCount(), 11);

    ALBPressShopStorageZone* EmptyStore = World
        ? World->SpawnActor<ALBPressShopStorageZone>(ALBPressShopStorageZone::StaticClass(),
            FVector(2700.0f, 0.0f, 0.0f), FRotator::ZeroRotator) : nullptr;
    ALBStillageFLTFleetController* Fleet = World
        ? World->SpawnActor<ALBStillageFLTFleetController>(
            ALBStillageFLTFleetController::StaticClass(), FVector(-6500.0f, 1200.0f, 0.0f),
            FRotator::ZeroRotator) : nullptr;
    TestTrue(TEXT("Press empty-stillage destination configures"), EmptyStore && Fleet
        && EmptyStore->Configure(TEXT("PRESS-EMPTY-STILLAGES-SCHEDULER"),
            ELBPressShopStorageType::EmptyPanelStillages, 16, FVector(200.0f))
        && EmptyStore->ConfigureLayout(4, 4, FVector2D(75.0f, 75.0f), 0.0f));
    const FLBBodyWeldLineSaveState BeforeFailedEmptyDispatch = Weld->CaptureSaveState();
    const FLBPlayerBuiltPressFlowSaveState BeforeFailedEmptyFlow = Flow->CaptureSaveState();
    Flow->ExecuteBodyWeldIntegrationStep(Summary);
    const FLBBodyWeldLineSaveState AfterFailedEmptyDispatch = Weld->CaptureSaveState();
    const FLBPlayerBuiltPressFlowSaveState AfterFailedEmptyFlow = Flow->CaptureSaveState();
    TestEqual(TEXT("Failed FLT enqueue restores the popped weld return"),
        AfterFailedEmptyDispatch.PendingEmptyReturns.Num(),
        BeforeFailedEmptyDispatch.PendingEmptyReturns.Num());
    TestEqual(TEXT("Failed enqueue leaves all manifest job fields unchanged"),
        AfterFailedEmptyFlow.PanelStillages.FilterByPredicate(
            [](const FLBPanelStillageLoad& Load) { return Load.bEmptyReturnQueued; }).Num(),
        BeforeFailedEmptyFlow.PanelStillages.FilterByPredicate(
            [](const FLBPanelStillageLoad& Load) { return Load.bEmptyReturnQueued; }).Num());
    TestEqual(TEXT("Failed enqueue creates no physical fleet job"),
        Fleet->GetJobSnapshots().Num(), 0);

    EmptyStore->SetActorLocation(FVector(-5000.0f, 0.0f, 0.0f));
    TestTrue(TEXT("A physically valid route dispatches one exact empty stillage"),
        Flow->ExecuteBodyWeldIntegrationStep(Summary) >= 1);
    const TArray<FLBStillageFLTJob> EmptyJobs = Fleet->GetJobSnapshots();
    TestEqual(TEXT("Exactly one empty-return job is created in the bounded pass"),
        EmptyJobs.Num(), 1);
    TestTrue(TEXT("Configure-only empty store receives deterministic first-free floor address"),
        EmptyJobs.Num() == 1 && EmptyJobs[0].TargetStackTier == 1
        && EmptyJobs[0].TargetStackPadId
            == FName(TEXT("PRESS-EMPTY-STILLAGES-SCHEDULER-STACK-PAD-001")));
    const FLBPlayerBuiltPressFlowSaveState DispatchedFlow = Flow->CaptureSaveState();
    const FLBPanelStillageLoad* QueuedLoad = DispatchedFlow.PanelStillages.FindByPredicate(
        [](const FLBPanelStillageLoad& Load) { return Load.bEmptyReturnQueued; });
    TestTrue(TEXT("Fleet and manifest preserve the same stillage and exact job IDs"),
        QueuedLoad && EmptyJobs[0].JobType == ELBStillageFLTJobType::EmptyStillageToPress
        && EmptyJobs[0].StillageId == QueuedLoad->StillageId
        && EmptyJobs[0].JobId == QueuedLoad->EmptyReturnJobId
        && EmptyJobs[0].SourceAuthorityId == WeldLineId
        && EmptyJobs[0].TargetAuthorityId == EmptyStore->GetZoneId());

    FLBStillageFLTFleetSaveState FleetCheckpoint;
    const FLBBodyWeldLineSaveState WeldCheckpoint = Weld->CaptureSaveState();
    TestTrue(TEXT("In-flight exact empty-return checkpoint captures"),
        Fleet->CaptureSaveState(FleetCheckpoint));
    TestTrue(TEXT("All three authorities restore the in-flight ownership checkpoint"),
        Flow->RestoreSaveState(DispatchedFlow)
        && Weld->RestoreSaveState(WeldCheckpoint)
        && Fleet->RestoreSaveState(FleetCheckpoint));
    Flow->ExecuteBodyWeldIntegrationStep(Summary);
    int32 OriginalStillageJobCount = 0;
    for (const FLBStillageFLTJob& Job : Fleet->GetJobSnapshots())
        OriginalStillageJobCount += Job.StillageId == EmptyJobs[0].StillageId ? 1 : 0;
    TestEqual(TEXT("Restart reconciliation cannot duplicate the exact in-flight stillage"),
        OriginalStillageJobCount, 1);

    Weld->AdvanceSimulation(30.0f);
    FLBBodyInWhiteRecord OutputBody;
    TestTrue(TEXT("Deterministic weld cycle produces one good exact BIW"),
        Weld->GetOutputBody(OutputBody)
        && OutputBody.QualityState == ELBBodyWeldQualityState::Good);
    ALBECoatLineActor* ED = World ? World->SpawnActor<ALBECoatLineActor>() : nullptr;
    TestTrue(TEXT("ED line configures for exact BIW acceptance"),
        ED && ED->Configure(TEXT("ED-SCHEDULER-001")));
    TestNotNull(TEXT("BodyInWhite/PanelTransfer exact ED link exists"),
        ED ? MakeBodyWeldFlowLink(World, Weld->GetBIWOutputPort(), ED->GetInputPort()) : nullptr);
    const FName CarrierId(*FString::Printf(TEXT("EDC-%s"), *OutputBody.BodyId.ToString()));
    TestTrue(TEXT("Occupied deterministic carrier identity blocks handoff"),
        ED && ED->AddCarrier(CarrierId));
    Flow->ExecuteBodyWeldIntegrationStep(Summary);
    FLBBodyInWhiteRecord StillAtWeld;
    TestTrue(TEXT("Blocked ED carrier leaves BIW at weld"),
        Weld->GetOutputBody(StillAtWeld) && StillAtWeld.BodyId == OutputBody.BodyId);
    TestTrue(TEXT("Freeing the carrier identity permits exact atomic handoff"),
        ED && ED->RemoveCarrier(CarrierId));
    Flow->ExecuteBodyWeldIntegrationStep(Summary);
    FLBBodyInWhiteRecord AtED;
    TestTrue(TEXT("ED owns the acknowledged exact BIW lineage"),
        ED && ED->GetCarrierBodyInWhite(CarrierId, AtED)
        && AtED.BodyId == OutputBody.BodyId && AtED.bEDAccepted);
    TestFalse(TEXT("Acknowledged BIW no longer remains at weld output"),
        Weld->GetOutputBody(StillAtWeld));

    if (World) World->DestroyWorld(false);
    return true;
}

#endif
