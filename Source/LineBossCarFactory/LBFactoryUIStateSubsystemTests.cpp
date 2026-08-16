#if WITH_DEV_AUTOMATION_TESTS

#include "Misc/AutomationTest.h"

#include "Engine/Engine.h"
#include "Engine/World.h"
#include "LBBodyWeldLineActor.h"
#include "LBCoilAGVController.h"
#include "LBECoatLineActor.h"
#include "LBFactoryBuildMachine.h"
#include "LBFactoryManagementSubsystem.h"
#include "LBFactoryUIStateSubsystem.h"
#include "LBManagementPawn.h"
#include "LBPlayerBuiltPressFlowController.h"
#include "LBPressShopStorageZone.h"
#include "LBPressTrainAStation.h"
#include "LBSupportRobot.h"

namespace
{
    ALBFactoryBuildMachine* SpawnMachineState(UWorld* World, const FName MachineId,
        const ELBFactoryBuildMachineType Type, const ELBFactoryMachineOperatingState State,
        const TCHAR* Reason, const FVector& Location)
    {
        ALBFactoryBuildMachine* Machine = World
            ? World->SpawnActor<ALBFactoryBuildMachine>(Location, FRotator::ZeroRotator) : nullptr;
        if (!Machine) return nullptr;
        FLBFactoryBuildMachineSaveState Save;
        Save.MachineId = MachineId;
        Save.MachineType = Type;
        Save.WorldTransform = FTransform(FRotator::ZeroRotator, Location);
        Save.OperatingState = State;
        Save.OperatingReason = Reason;
        return Machine->RestoreSaveState(Save) ? Machine : nullptr;
    }

    bool FeedBodyWeldUIRecipe(ALBBodyWeldLineActor* Line, const FName OrderId)
    {
        if (!Line) return false;
        FString Reason;
        int32 Serial = 1;
        for (const FName Family : ALBBodyWeldLineActor::GetRequiredPanelFamilies())
        {
            FLBBodyWeldStillageInventory Stillage;
            Stillage.StillageId = FName(*FString::Printf(TEXT("UI-STILLAGE-%s-%03d"),
                *Family.ToString(), Serial));
            Stillage.OrderId = OrderId;
            Stillage.VehicleModelId = TEXT("CAIRNWELL_2040");
            Stillage.PanelTypeId = Family;
            Stillage.DeliverySequence = Serial;
            Stillage.CapacityPanels = 1;
            FLBBodyWeldPanelUnit& Panel = Stillage.PanelUnits.AddDefaulted_GetRef();
            Panel.PanelId = FName(*FString::Printf(
                TEXT("PTA-PANEL-CAIRNWELL_2040-%s-%06d"), *Family.ToString(), Serial));
            Panel.OrderId = OrderId;
            Panel.VehicleModelId = Stillage.VehicleModelId;
            Panel.PanelTypeId = Family;
            Panel.StillageId = Stillage.StillageId;
            if (!Line->ReceivePanelStillage(Stillage, Reason)) return false;
            ++Serial;
        }
        FLBBodyWeldBaseKitUnit Kit;
        Kit.KitId = TEXT("UI-BIW-BASE-KIT-000001");
        Kit.OrderId = OrderId;
        Kit.DeliverySequence = 1;
        return Line->ReceiveBaseKit(Kit, Reason);
    }
}

IMPLEMENT_SIMPLE_AUTOMATION_TEST(
    FLBPersistentHUDOrderProgressAndAlertPriorityTest,
    "LineBoss.Management.PersistentHUD.OrderProgressAndAlertPriority",
    EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)

bool FLBPersistentHUDOrderProgressAndAlertPriorityTest::RunTest(const FString& Parameters)
{
    UWorld* World = UWorld::CreateWorld(EWorldType::Game, false,
        TEXT("LBPersistentHUDStateTestWorld"));
    TestNotNull(TEXT("Transient persistent-HUD world created"), World);
    if (!World) return false;

    FWorldContext& Context = GEngine->CreateNewWorldContext(EWorldType::Game);
    Context.SetCurrentWorld(World);
    World->InitializeActorsForPlay(FURL());

    ALBPlayerBuiltPressFlowController* Flow =
        World->SpawnActor<ALBPlayerBuiltPressFlowController>();
    FLBPlayerBuiltPressFlowSaveState FlowSave;
    FLBVehiclePanelBatch Batch;
    Batch.OrderId = TEXT("UX-ORDER-001");
    Batch.VehicleModelId = TEXT("CAIRNWELL_2040");
    Batch.PanelTypeId = TEXT("DOOR_FRONT_LEFT");
    Batch.RequestedQuantity = 40;
    Batch.DispatchedQuantity = 7;
    FlowSave.PanelBatches.Add(Batch);
    TestTrue(TEXT("Player-built order authority accepts an issued-progress snapshot"),
        Flow && Flow->RestoreSaveState(FlowSave));

    ALBFactoryBuildMachine* Starved = SpawnMachineState(World, TEXT("PR002-STARVED"),
        ELBFactoryBuildMachineType::CoilWeighInspectionCell,
        ELBFactoryMachineOperatingState::Starved, TEXT("NO WRAPPED COIL AT INPUT"),
        FVector(1000.0f, 0.0f, 100.0f));
    ALBFactoryBuildMachine* Blocked = SpawnMachineState(World, TEXT("PR004-BLOCKED"),
        ELBFactoryBuildMachineType::DepackagingRobot,
        ELBFactoryMachineOperatingState::Blocked, TEXT("OUTPUT BUFFER FULL"),
        FVector(2000.0f, 0.0f, 100.0f));
    ALBFactoryBuildMachine* Faulted = SpawnMachineState(World, TEXT("PR010-FAULT"),
        ELBFactoryBuildMachineType::InspectionCell,
        ELBFactoryMachineOperatingState::Fault, TEXT("VISION SENSOR LOST"),
        FVector(3000.0f, 0.0f, 100.0f));
    TestNotNull(TEXT("Starved machine fixture created"), Starved);
    TestNotNull(TEXT("Blocked machine fixture created"), Blocked);
    TestNotNull(TEXT("Faulted machine fixture created"), Faulted);

    World->BeginPlay();
    ULBFactoryUIStateSubsystem* UIState =
        World->GetSubsystem<ULBFactoryUIStateSubsystem>();
    TestNotNull(TEXT("Persistent factory UI-state subsystem created"), UIState);
    if (UIState)
    {
        const FLBFactoryUIStateSnapshot& Snapshot = UIState->GetSnapshot(true);
        TestTrue(TEXT("Active player-built order is surfaced"),
            Snapshot.Order.bHasActiveOrder);
        TestEqual(TEXT("Order identity is retained"), Snapshot.Order.OrderId,
            FName(TEXT("UX-ORDER-001")));
        TestEqual(TEXT("Persistent HUD snapshot retains the Cairnwell 2040 programme"),
            Snapshot.Order.VehicleModelId, FName(TEXT("CAIRNWELL_2040")));
        TestEqual(TEXT("Progress is truthfully labelled from issued quantity"),
            Snapshot.Order.IssuedQuantity, 7);
        TestEqual(TEXT("Requested quantity is retained"),
            Snapshot.Order.RequestedQuantity, 40);
        TestEqual(TEXT("All three operational conditions become alerts"),
            Snapshot.Alerts.Num(), 3);
        if (Snapshot.Alerts.Num() == 3)
        {
            TestEqual(TEXT("Critical fault outranks blocked and starvation alerts"),
                Snapshot.Alerts[0].EntityId, FName(TEXT("PR010-FAULT")));
            TestEqual(TEXT("Blocked warning ranks second"),
                Snapshot.Alerts[1].EntityId, FName(TEXT("PR004-BLOCKED")));
            TestEqual(TEXT("Order-gated starvation ranks after actionable warnings"),
                Snapshot.Alerts[2].EntityId, FName(TEXT("PR002-STARVED")));
            TestTrue(TEXT("Top alert retains an actor target for camera focus"),
                Snapshot.Alerts[0].TargetActor.Get() == Faulted);
            TestTrue(TEXT("Top alert marker is raised above its machine"),
                Snapshot.Alerts[0].MarkerWorldLocation.Z > Faulted->GetActorLocation().Z);
        }

        FLBFactoryUIInspectorSnapshot Inspector;
        TestTrue(TEXT("Faulted machine produces a usable inspector snapshot"),
            UIState->BuildInspectorSnapshot(Faulted, Inspector));
        TestEqual(TEXT("Inspector retains the selected machine id"),
            Inspector.EntityId, FName(TEXT("PR010-FAULT")));
        TestEqual(TEXT("Inspector exposes the operational state"),
            Inspector.State, FString(TEXT("FAULT")));
        TestTrue(TEXT("Inspector contains readable operating detail"),
            Inspector.DetailLines.Num() >= 4);
    }

    World->DestroyWorld(false);
    GEngine->DestroyWorldContext(World);
    return true;
}

IMPLEMENT_SIMPLE_AUTOMATION_TEST(
    FLBProductionFlowAwaitingBlanksPresentationTest,
    "LineBoss.Management.UIState.ProductionFlowAwaitingBlanksPresentation",
    EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)

bool FLBProductionFlowAwaitingBlanksPresentationTest::RunTest(const FString& Parameters)
{
    UWorld* World = UWorld::CreateWorld(EWorldType::Game, false,
        TEXT("LBProductionFlowAwaitingBlanksWorld"));
    TestNotNull(TEXT("Awaiting-blanks world created"), World);
    if (!World) return false;

    FWorldContext& Context = GEngine->CreateNewWorldContext(EWorldType::Game);
    Context.SetCurrentWorld(World);
    World->InitializeActorsForPlay(FURL());

    ALBPlayerBuiltPressFlowController* Flow =
        World->SpawnActor<ALBPlayerBuiltPressFlowController>();
    ALBPressTrainAStation* Press = World->SpawnActor<ALBPressTrainAStation>(
        FVector(1000.0f, 0.0f, 100.0f), FRotator::ZeroRotator);
    FLBVehiclePanelBatch Batch;
    Batch.OrderId = TEXT("AWAITING-BLANKS-ORDER-001");
    Batch.VehicleModelId = TEXT("CAIRNWELL_2040");
    Batch.PanelTypeId = TEXT("DOOR_FRONT_LEFT");
    Batch.RequestedQuantity = 10;
    FString QueueReason;
    TestTrue(TEXT("Real panel order queues"),
        Flow && Flow->QueuePanelBatch(Batch, QueueReason));
    TestNotNull(TEXT("Isolated press fixture created"), Press);

    World->BeginPlay();
    ULBFactoryUIStateSubsystem* UIState =
        World->GetSubsystem<ULBFactoryUIStateSubsystem>();
    TestNotNull(TEXT("UI-state authority created"), UIState);
    if (UIState)
    {
        const FLBFactoryUIStateSnapshot& Snapshot = UIState->GetSnapshot(true);
        const FLBFactoryUIProductionStageSnapshot* Stage =
            Snapshot.ProductionStages.FindByPredicate([](
                const FLBFactoryUIProductionStageSnapshot& Candidate)
            {
                return Candidate.StageId == TEXT("TRANSFER_PRESS");
            });
        TestNotNull(TEXT("Transfer press stage is present"), Stage);
        if (Stage)
        {
            TestEqual(TEXT("Order-gated empty press explains material state"),
                Stage->State, FString(TEXT("AWAITING BLANKS")));
            TestEqual(TEXT("Order-gated empty press gives the actual next step"),
                Stage->Detail, FString(TEXT("MATERIAL IS ROUTING TO THE PRESS")));
            TestTrue(TEXT("Material wait remains a waiting, not faulted, condition"),
                Stage->bWaiting && !Stage->bRunning && !Stage->bFaulted);
        }
    }

    World->DestroyWorld(false);
    GEngine->DestroyWorldContext(World);
    return true;
}

IMPLEMENT_SIMPLE_AUTOMATION_TEST(
    FLBPersistentHUDAssetCountObjectiveAndPressInspectorTest,
    "LineBoss.Management.PersistentHUD.AssetCountObjectiveAndPressInspector",
    EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)

bool FLBPersistentHUDAssetCountObjectiveAndPressInspectorTest::RunTest(
    const FString& Parameters)
{
    UWorld* World = UWorld::CreateWorld(EWorldType::Game, false,
        TEXT("LBPersistentHUDAssetSemanticsTestWorld"));
    TestNotNull(TEXT("Transient asset-semantics world created"), World);
    if (!World) return false;

    FWorldContext& Context = GEngine->CreateNewWorldContext(EWorldType::Game);
    Context.SetCurrentWorld(World);
    World->InitializeActorsForPlay(FURL());

    ULBFactoryUIStateSubsystem* UIState =
        World->GetSubsystem<ULBFactoryUIStateSubsystem>();
    TestNotNull(TEXT("Persistent factory UI-state subsystem created"), UIState);
    if (UIState)
    {
        const FLBFactoryUIStateSnapshot& EmptySnapshot = UIState->GetSnapshot(true);
        TestEqual(TEXT("Completely empty factory retains first-cell guidance"),
            EmptySnapshot.Order.Objective,
            FString(TEXT("BUILD THE FIRST PROCESS CELL")));
        TestEqual(TEXT("Completely empty factory has no operational assets"),
            EmptySnapshot.OperationalAssetCount, 0);
    }

    ALBFactoryBuildMachine* Machine = SpawnMachineState(World, TEXT("ASSET-MACHINE-001"),
        ELBFactoryBuildMachineType::InboundDeliveryDock,
        ELBFactoryMachineOperatingState::Idle, TEXT("READY FOR NEXT ORDER"),
        FVector(0.0f, 0.0f, 100.0f));
    ALBPressTrainAStation* Press = World->SpawnActor<ALBPressTrainAStation>(
        FVector(1000.0f, 0.0f, 100.0f), FRotator::ZeroRotator);
    ALBCoilAGVController* AGV = World->SpawnActor<ALBCoilAGVController>(
        FVector(2000.0f, 0.0f, 100.0f), FRotator::ZeroRotator);
    ALBSupportRobot* Robot = World->SpawnActor<ALBSupportRobot>(
        FVector(3000.0f, 0.0f, 100.0f), FRotator::ZeroRotator);
    TestNotNull(TEXT("Machine asset fixture created"), Machine);
    TestNotNull(TEXT("Press asset fixture created"), Press);
    TestNotNull(TEXT("Coil AGV asset fixture created"), AGV);
    TestNotNull(TEXT("Support robot asset fixture created"), Robot);

    World->BeginPlay();
    if (UIState)
    {
        const FLBFactoryUIStateSnapshot& Snapshot = UIState->GetSnapshot(true);
        TestEqual(TEXT("Machine count remains available for setup and automation logic"),
            Snapshot.MachineCount, 1);
        TestEqual(TEXT("Health total counts every operational actor category exactly once"),
            Snapshot.OperationalAssetCount, 4);
        TestFalse(TEXT("No production order is invented"), Snapshot.Order.bHasActiveOrder);
        TestEqual(TEXT("Built factory without an order asks for the next production batch"),
            Snapshot.Order.Objective,
            FString(TEXT("SCHEDULE THE NEXT PRODUCTION BATCH")));

        FLBFactoryUIInspectorSnapshot Inspector;
        TestTrue(TEXT("Isolated press produces a usable inspector snapshot"),
            UIState->BuildInspectorSnapshot(Press, Inspector));
        TestEqual(TEXT("Default isolated press reports its actual state"), Inspector.State,
            FString(TEXT("ISOLATED")));
        TestEqual(TEXT("Isolated press gives a corrective action instead of claiming online"),
            Inspector.Reason, FString(TEXT("POWER AND START THE ASSIGNED TRAIN")));
    }

    World->DestroyWorld(false);
    GEngine->DestroyWorldContext(World);
    return true;
}

IMPLEMENT_SIMPLE_AUTOMATION_TEST(
    FLBPersistentHUDMachineStorageSelectionTest,
    "LineBoss.Management.PersistentHUD.MachineStorageSelection",
    EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)

bool FLBPersistentHUDMachineStorageSelectionTest::RunTest(const FString& Parameters)
{
    UWorld* World = UWorld::CreateWorld(EWorldType::Game, false,
        TEXT("LBPersistentHUDSelectionTestWorld"));
    TestNotNull(TEXT("Transient selection world created"), World);
    if (!World) return false;
    FWorldContext& Context = GEngine->CreateNewWorldContext(EWorldType::Game);
    Context.SetCurrentWorld(World);
    World->InitializeActorsForPlay(FURL());
    ALBManagementPawn* Pawn = World->SpawnActor<ALBManagementPawn>();
    ALBFactoryBuildMachine* Machine = World->SpawnActor<ALBFactoryBuildMachine>(
        FVector(1200.0f, 500.0f, 100.0f), FRotator::ZeroRotator);
    ALBPressShopStorageZone* Storage = World->SpawnActor<ALBPressShopStorageZone>(
        FVector(3000.0f, 500.0f, 100.0f), FRotator::ZeroRotator);
    TestTrue(TEXT("Selectable machine configured"), Machine
        && Machine->Configure(TEXT("SELECT-MACHINE-001"),
            ELBFactoryBuildMachineType::DecoilerFeeder));
    TestTrue(TEXT("Selectable storage configured"), Storage
        && Storage->Configure(TEXT("SELECT-STORAGE-001"),
            ELBPressShopStorageType::PreparedBlanks, 24,
            FVector(600.0f, 450.0f, 100.0f)));
    World->BeginPlay();

    if (Pawn && Machine && Storage)
    {
        TestTrue(TEXT("Management selection accepts a factory machine"),
            Pawn->SelectFactoryActor(Machine, false));
        TestTrue(TEXT("Machine becomes the authoritative inspected actor"),
            Pawn->GetInspectedFactoryActor() == Machine);
        TestTrue(TEXT("Management selection switches to an empty storage footprint"),
            Pawn->SelectFactoryActor(Storage, false));
        TestTrue(TEXT("Storage becomes the authoritative inspected actor"),
            Pawn->GetInspectedFactoryActor() == Storage);
        TestTrue(TEXT("Selected storage can be framed by the management camera"),
            Pawn->FocusFactoryActor(Storage));
        Pawn->ClearFactoryActorSelection();
        TestNull(TEXT("Clear removes the inspected actor"),
            Pawn->GetInspectedFactoryActor());
    }

    World->DestroyWorld(false);
    GEngine->DestroyWorldContext(World);
    return true;
}

IMPLEMENT_SIMPLE_AUTOMATION_TEST(
    FLBPersistentHUDAlertFocusTest,
    "LineBoss.Management.PersistentHUD.AlertFocus",
    EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)

bool FLBPersistentHUDAlertFocusTest::RunTest(const FString& Parameters)
{
    UWorld* World = UWorld::CreateWorld(EWorldType::Game, false,
        TEXT("LBPersistentHUDAlertFocusTestWorld"));
    TestNotNull(TEXT("Transient alert-focus world created"), World);
    if (!World) return false;
    FWorldContext& Context = GEngine->CreateNewWorldContext(EWorldType::Game);
    Context.SetCurrentWorld(World);
    World->InitializeActorsForPlay(FURL());
    ALBManagementPawn* Pawn = World->SpawnActor<ALBManagementPawn>();
    ALBFactoryBuildMachine* Faulted = SpawnMachineState(World,
        TEXT("FOCUS-FAULT-001"), ELBFactoryBuildMachineType::InspectionCell,
        ELBFactoryMachineOperatingState::Fault, TEXT("VISION SENSOR LOST"),
        FVector(4200.0f, -900.0f, 100.0f));
    World->BeginPlay();

    if (Pawn && Faulted)
    {
        TestTrue(TEXT("Top-alert jump has a safe focus target"),
            Pawn->JumpToTopFactoryAlert());
        TestTrue(TEXT("Alert jump selects the affected actor"),
            Pawn->GetInspectedFactoryActor() == Faulted);
        // Transient automation worlds do not schedule unpossessed pawn ticks, so drive the
        // same public Tick path used by play to prove the smooth focus transition.
        for (int32 Step = 0; Step < 20; ++Step) Pawn->Tick(0.05f);
        TestTrue(TEXT("Camera moves toward the selected problem"),
            FVector::Dist2D(Pawn->GetActorLocation(), Faulted->GetActorLocation()) < 500.0f);
    }

    World->DestroyWorld(false);
    GEngine->DestroyWorldContext(World);
    return true;
}

IMPLEMENT_SIMPLE_AUTOMATION_TEST(
    FLBPersistentHUDECoatLineInspectorTest,
    "LineBoss.Management.PersistentHUD.ECoatLineInspectorAndAlert",
    EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)

bool FLBPersistentHUDECoatLineInspectorTest::RunTest(const FString& Parameters)
{
    UWorld* World = UWorld::CreateWorld(EWorldType::Game, false,
        TEXT("LBPersistentHUDECoatLineWorld"));
    TestNotNull(TEXT("Transient ED-line UI world created"), World);
    if (!World) return false;
    FWorldContext& Context = GEngine->CreateNewWorldContext(EWorldType::Game);
    Context.SetCurrentWorld(World);
    World->InitializeActorsForPlay(FURL());

    ALBECoatLineActor* Line = World->SpawnActor<ALBECoatLineActor>();
    ALBManagementPawn* Pawn = World->SpawnActor<ALBManagementPawn>();
    TestTrue(TEXT("Complete ED line configures with a persistent identity"),
        Line && Line->Configure(TEXT("ED-LINE-UI-01")));
    if (Line)
    {
        TestTrue(TEXT("UI fixture puts one carrier in the new 189 m exit bay"),
            Line->AddCarrier(TEXT("ED-UI-CARRIER-01"), 18450.0f));
        FLBECoatLineSaveState Faulted = Line->CaptureSaveState();
        TestEqual(TEXT("ED-line UI fixture captures the current v3 line contract"),
            Faulted.Version, 3);
        TestTrue(TEXT("ED-line UI fixture preserves its 184.5 m carrier position"),
            Faulted.Carriers.Num() == 1
            && FMath::IsNearlyEqual(Faulted.Carriers[0].DistanceCm, 18450.0f, 0.01f));
        Faulted.OperatingState = ELBECoatOperatingState::Faulted;
        Faulted.StateReason = TEXT("ED_TANK_CONDUCTIVITY_OUT_OF_RANGE");
        TestTrue(TEXT("Faulted ED-line fixture restores through its normal save contract"),
            Line->RestoreSaveState(Faulted));
    }

    World->BeginPlay();
    ULBFactoryUIStateSubsystem* UIState =
        World->GetSubsystem<ULBFactoryUIStateSubsystem>();
    TestNotNull(TEXT("Persistent UI-state subsystem created"), UIState);
    if (UIState && Line)
    {
        const FLBFactoryUIStateSnapshot& Snapshot = UIState->GetSnapshot(true);
        TestEqual(TEXT("ED line counts as one operational machine asset"),
            Snapshot.OperationalAssetCount, 1);
        TestEqual(TEXT("ED line participates in machine health totals"),
            Snapshot.MachineCount, 1);
        TestEqual(TEXT("Faulted ED line produces one critical fault"),
            Snapshot.FaultCount, 1);
        TestTrue(TEXT("Faulted ED line exposes an actionable actor alert"),
            Snapshot.Alerts.Num() == 1 && Snapshot.Alerts[0].EntityId == TEXT("ED-LINE-UI-01")
            && Snapshot.Alerts[0].TargetActor.Get() == Line);

        FLBFactoryUIInspectorSnapshot Inspector;
        TestTrue(TEXT("ED line produces a selectable inspector"),
            UIState->BuildInspectorSnapshot(Line, Inspector));
        TestEqual(TEXT("Inspector retains ED-line identity"),
            Inspector.EntityId, FName(TEXT("ED-LINE-UI-01")));
        TestEqual(TEXT("Inspector names the paint-shop asset truthfully"),
            Inspector.Kind, FString(TEXT("PAINT SHOP LINE")));
        TestEqual(TEXT("Inspector exposes complete line fault state"),
            Inspector.State, FString(TEXT("FAULT")));
        TestTrue(TEXT("Inspector reports tanks, oven, carriers and bay condition"),
            Inspector.DetailLines.Num() == 4);
        TestTrue(TEXT("Inspector states the six doubled treatment tanks truthfully"),
            Inspector.DetailLines.IsValidIndex(0)
            && Inspector.DetailLines[0].Contains(TEXT("6 x 18 m")));
        TestTrue(TEXT("Inspector states the complete 72 m oven truthfully"),
            Inspector.DetailLines.IsValidIndex(1)
            && Inspector.DetailLines[1].Contains(TEXT("72 m"))
            && Inspector.DetailLines[1].Contains(TEXT("6 BODIES")));
        TestTrue(TEXT("Inspector states the complete 189 m line truthfully"),
            Inspector.DetailLines.IsValidIndex(2)
            && Inspector.DetailLines[2].Contains(TEXT("TOTAL LINE  189 m")));
        TestTrue(TEXT("Automation identity lookup finds the ED line"),
            UIState->FindFactoryActorById(TEXT("ED-LINE-UI-01")) == Line);
        TestTrue(TEXT("Management camera accepts the complete ED line as one focus target"),
            Pawn && Pawn->FocusFactoryActor(Line));
        if (Pawn)
        {
            Pawn->Tick(1.0f);
            TestTrue(TEXT("Focused ED-line view backs out far enough to retain both 0 m and 189 m ports"),
                Pawn->GetManagementZoomDistance() >= 25000.0f
                && Pawn->GetManagementZoomDistance()
                    <= ALBManagementPawn::GetMaximumManagementZoomDistance());
        }
    }

    World->DestroyWorld(false);
    GEngine->DestroyWorldContext(World);
    return true;
}

IMPLEMENT_SIMPLE_AUTOMATION_TEST(
    FLBFactoryUIManagementProjectionTest,
    "LineBoss.Management.UIState.ExactManagementProjectionAndInspector",
    EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)

bool FLBFactoryUIManagementProjectionTest::RunTest(const FString& Parameters)
{
    UWorld* World = UWorld::CreateWorld(EWorldType::Game, false,
        TEXT("LBFactoryUIManagementProjectionWorld"));
    TestNotNull(TEXT("Management projection world created"), World);
    if (!World) return false;
    FWorldContext& Context = GEngine->CreateNewWorldContext(EWorldType::Game);
    Context.SetCurrentWorld(World);
    World->InitializeActorsForPlay(FURL());

    ALBFactoryBuildMachine* Machine = World->SpawnActor<ALBFactoryBuildMachine>();
    TestTrue(TEXT("Projected management machine configures"), Machine
        && Machine->Configure(TEXT("UI-MGMT-001"),
            ELBFactoryBuildMachineType::InboundDeliveryDock));
    ULBFactoryManagementSubsystem* Management =
        World->GetSubsystem<ULBFactoryManagementSubsystem>();
    TestNotNull(TEXT("Management authority exists"), Management);
    if (Management)
    {
        TestTrue(TEXT("Campaign management starts with exact cash and research"),
            Management->InitialiseNewCampaign(12345678, 25));
        TestTrue(TEXT("Maintainable asset is registered"), Management->RegisterMaintainableAsset(
            TEXT("REGISTER-UI-MGMT-001"), TEXT("UI-MGMT-001"), 1.0));
        TestTrue(TEXT("Deterministic use makes service due"), Management->RecordMaintenanceUsage(
            TEXT("WEAR-UI-MGMT-001"), TEXT("UI-MGMT-001"), 3600.0, 0.0, 1.0));
        TestTrue(TEXT("Exact fault is recorded"), Management->SetAssetFault(
            TEXT("FAULT-UI-MGMT-001"), TEXT("UI-MGMT-001"), TEXT("GUARD-INTERLOCK")));
        TestTrue(TEXT("Exact quality counts are recorded"), Management->RecordQualityCounts(
            TEXT("QUALITY-UI-MGMT-001"), TEXT("UI-MGMT-001"), 10, 10, 8, 2, 1, 1));
        TestTrue(TEXT("Research grant is recorded"), Management->GrantResearchPoints(
            TEXT("RP-UI-MGMT-001"), TEXT("ORDER-UI-MGMT-001"), 20));
        TestTrue(TEXT("Research unlock is purchased"), Management->TryUnlockResearch(
            TEXT("UNLOCK-EVENT-UI-MGMT-001"), TEXT("SERVO-UPGRADES"), 10));
        TestTrue(TEXT("Machine upgrade is purchased"), Management->TryPurchaseMachineUpgrade(
            TEXT("UPGRADE-TX-UI-MGMT-001"), TEXT("UI-MGMT-001"), TEXT("SERVO-PACK"),
            1, 10000, TEXT("SERVO-UPGRADES")));
    }

    World->BeginPlay();
    ULBFactoryUIStateSubsystem* UIState =
        World->GetSubsystem<ULBFactoryUIStateSubsystem>();
    TestNotNull(TEXT("UI projection authority exists"), UIState);
    if (UIState && Management && Machine)
    {
        const FLBFactoryUIStateSnapshot& Snapshot = UIState->GetSnapshot(true);
        TestTrue(TEXT("Projection explicitly reports initialised campaign management"),
            Snapshot.Management.bCampaignInitialised);
        TestEqual(TEXT("Cash projection uses exact pence after upgrade"),
            Snapshot.Management.CashBalancePence, static_cast<int64>(12335678));
        TestEqual(TEXT("Research projection reconciles opening, grant and spend"),
            Snapshot.Management.AvailableResearchPoints, static_cast<int64>(35));
        TestEqual(TEXT("Maintenance summary exposes one due faulted asset"),
            Snapshot.Management.ServiceDueCount, 1);
        TestEqual(TEXT("Management fault participates in headline fault health"),
            Snapshot.FaultCount, 1);
        TestTrue(TEXT("Management fault becomes an actionable critical alert"),
            !Snapshot.Alerts.IsEmpty()
            && Snapshot.Alerts[0].EntityId == TEXT("UI-MGMT-001")
            && Snapshot.Alerts[0].Severity == ELBFactoryUIAlertSeverity::Critical
            && Snapshot.Alerts[0].TargetActor.Get() == Machine);
        TestEqual(TEXT("Quality projection retains passed count"),
            Snapshot.Management.PassedCount, static_cast<int64>(8));
        TestEqual(TEXT("Upgrade projection retains exact row count"),
            Snapshot.Management.UpgradeCount, 1);

        FLBFactoryUIInspectorSnapshot Inspector;
        TestTrue(TEXT("Machine inspector builds with management data"),
            UIState->BuildInspectorSnapshot(Machine, Inspector));
        TestTrue(TEXT("Inspector exposes service due and exact wear"),
            Inspector.bHasMaintenance && Inspector.bServiceDue
            && FMath::IsNearlyEqual(Inspector.WearFraction, 1.0));
        TestTrue(TEXT("Inspector exposes management fault code"),
            Inspector.bManagementFaulted && Inspector.FaultCode == TEXT("GUARD-INTERLOCK"));
        TestTrue(TEXT("Inspector exposes quality outcome"),
            Inspector.bHasQuality && Inspector.PassedCount == 8 && Inspector.RejectedCount == 2);
        TestEqual(TEXT("Inspector exposes installed upgrade"), Inspector.UpgradeCount, 1);
        TestTrue(TEXT("Inspector provides readable management detail lines"),
            Inspector.DetailLines.ContainsByPredicate([](const FString& Line)
            {
                return Line.Contains(TEXT("WEAR"));
            }) && Inspector.DetailLines.ContainsByPredicate([](const FString& Line)
            {
                return Line.Contains(TEXT("QUALITY"));
            }) && Inspector.DetailLines.ContainsByPredicate([](const FString& Line)
            {
                return Line.Contains(TEXT("UPGRADE"));
            }));
    }

    World->DestroyWorld(false);
    GEngine->DestroyWorldContext(World);
    return true;
}

IMPLEMENT_SIMPLE_AUTOMATION_TEST(
    FLBFactoryUIBodyWeldSnapshotInspectorAlertTest,
    "LineBoss.Management.UIState.BodyWeldSnapshotInspectorAlertAndIdentity",
    EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)

bool FLBFactoryUIBodyWeldSnapshotInspectorAlertTest::RunTest(const FString& Parameters)
{
    UWorld* World = UWorld::CreateWorld(EWorldType::Game, false,
        TEXT("LBFactoryUIBodyWeldWorld"));
    TestNotNull(TEXT("Body Weld UI-state world created"), World);
    if (!World) return false;
    FWorldContext& Context = GEngine->CreateNewWorldContext(EWorldType::Game);
    Context.SetCurrentWorld(World);
    World->InitializeActorsForPlay(FURL());

    const FName LineId(TEXT("BODY-WELD-UI-01"));
    const FName OrderId(TEXT("ORDER-BODY-WELD-UI-01"));
    ALBBodyWeldLineActor* Line = World->SpawnActor<ALBBodyWeldLineActor>(
        FVector(4200.0f, -600.0f, 0.0f), FRotator::ZeroRotator);
    TestTrue(TEXT("Body Weld UI fixture configures and receives a complete exact recipe"),
        Line && Line->Configure(LineId) && Line->SetAssignedOrder(OrderId)
        && FeedBodyWeldUIRecipe(Line, OrderId));
    if (!Line)
    {
        World->DestroyWorld(false);
        GEngine->DestroyWorldContext(World);
        return false;
    }
    World->BeginPlay();
    Line->AdvanceSimulation(22.0f);

    ULBFactoryUIStateSubsystem* UIState =
        World->GetSubsystem<ULBFactoryUIStateSubsystem>();
    TestNotNull(TEXT("Body Weld UI-state authority exists"), UIState);
    if (UIState)
    {
        const FLBFactoryUIStateSnapshot& OutputSnapshot = UIState->GetSnapshot(true);
        TestEqual(TEXT("Composite Body Weld counts as one operational machine"),
            OutputSnapshot.OperationalAssetCount, 1);
        TestEqual(TEXT("One stable Body Weld line row is projected"),
            OutputSnapshot.BodyWeldLines.Num(), 1);
        if (OutputSnapshot.BodyWeldLines.Num() == 1)
        {
            const FLBFactoryUIBodyWeldLineSnapshot& Weld = OutputSnapshot.BodyWeldLines[0];
            TestEqual(TEXT("Projection uses stable LineId"), Weld.LineId, LineId);
            TestEqual(TEXT("Projection maps the blocked output state"), Weld.State,
                FString(TEXT("BLOCKED")));
            TestEqual(TEXT("Projection names the authored output-ready phase"), Weld.Phase,
                FString(TEXT("OUTPUT READY")));
            TestEqual(TEXT("Projection retains assigned order"), Weld.AssignedOrderId, OrderId);
            TestEqual(TEXT("Consumed recipe leaves no available panels"), Weld.AvailablePanelCount, 0);
            TestEqual(TEXT("Consumed recipe queues every exact empty stillage"),
                Weld.PendingEmptyReturnCount,
                ALBBodyWeldLineActor::GetRequiredPanelFamilies().Num());
            TestFalse(TEXT("Output slot exposes the exact BIW identity"), Weld.OutputBodyId.IsNone());
            TestTrue(TEXT("No rework body is invented for a good geometry result"),
                Weld.ReworkBodyId.IsNone());
            TestEqual(TEXT("Unacknowledged output is not yet completed"), Weld.CompletedBodyCount, 0);
        }
        TestTrue(TEXT("Blocked BIW output produces one focused operational alert"),
            OutputSnapshot.Alerts.Num() == 1
            && OutputSnapshot.Alerts[0].EntityId == LineId
            && OutputSnapshot.Alerts[0].Title == TEXT("BIW OUTPUT AWAITING ED")
            && OutputSnapshot.Alerts[0].TargetActor.Get() == Line);

        FLBFactoryUIInspectorSnapshot Inspector;
        TestTrue(TEXT("Composite Body Weld builds a selectable inspector"),
            UIState->BuildInspectorSnapshot(Line, Inspector));
        TestEqual(TEXT("Inspector exposes stable Body Weld identity"), Inspector.EntityId, LineId);
        TestEqual(TEXT("Inspector identifies the composite shop truthfully"), Inspector.Kind,
            FString(TEXT("BODY WELD LINE")));
        TestEqual(TEXT("Inspector reports phase/order/inventory/output/completion rows"),
            Inspector.DetailLines.Num(), 6);
        TestTrue(TEXT("Stable identity lookup finds Body Weld"),
            UIState->FindFactoryActorById(LineId) == Line);

        FLBBodyInWhiteRecord OutputBody;
        const bool bHasOutput = Line->GetOutputBody(OutputBody);
        Line->SetEDAvailable(true);
        TestTrue(TEXT("Good output can be acknowledged through the real exact-once seam"),
            bHasOutput && Line->IsEDAvailable());
        FLBBodyInWhiteRecord Accepted;
        TestTrue(TEXT("ED acknowledgement completes exactly one body"),
            Line->AcknowledgeEDTransfer(OutputBody.BodyId, Accepted));
        const FLBFactoryUIStateSnapshot& CompletedSnapshot = UIState->GetSnapshot(true);
        TestTrue(TEXT("Completed projection clears output and advances durable count"),
            CompletedSnapshot.BodyWeldLines.Num() == 1
            && CompletedSnapshot.BodyWeldLines[0].OutputBodyId.IsNone()
            && CompletedSnapshot.BodyWeldLines[0].CompletedBodyCount == 1);
    }

    World->DestroyWorld(false);
    GEngine->DestroyWorldContext(World);
    return true;
}

IMPLEMENT_SIMPLE_AUTOMATION_TEST(
    FLBFactoryUIProductionFlowSixStageProjectionTest,
    "LineBoss.Management.UIState.ProductionFlowSixStageTruthfulProjection",
    EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)

bool FLBFactoryUIProductionFlowSixStageProjectionTest::RunTest(
    const FString& Parameters)
{
    UWorld* World = UWorld::CreateWorld(EWorldType::Game, false,
        TEXT("LBFactoryUIProductionFlowWorld"));
    TestNotNull(TEXT("Production-flow projection world created"), World);
    if (!World) return false;
    FWorldContext& Context = GEngine->CreateNewWorldContext(EWorldType::Game);
    Context.SetCurrentWorld(World);
    World->InitializeActorsForPlay(FURL());

    ULBFactoryUIStateSubsystem* UIState =
        World->GetSubsystem<ULBFactoryUIStateSubsystem>();
    TestNotNull(TEXT("Production-flow projection authority exists"), UIState);
    if (!UIState)
    {
        World->DestroyWorld(false);
        GEngine->DestroyWorldContext(World);
        return false;
    }

    static const FName ExpectedIds[] = {
        TEXT("COIL_INTAKE"), TEXT("BLANK_BUFFER"), TEXT("TRANSFER_PRESS"),
        TEXT("PANEL_STILLAGES"), TEXT("BODY_WELD"), TEXT("ED_COAT")
    };
    static const FString ExpectedNames[] = {
        TEXT("Coil intake"), TEXT("Blank buffer"), TEXT("Transfer press"),
        TEXT("Panel stillages"), TEXT("Body weld"), TEXT("ED coat")
    };
    static const int32 ExpectedProcessOrder[] = {0, 35, 40, 70, 100, 110};
    static_assert(UE_ARRAY_COUNT(ExpectedIds) == 6);
    static_assert(UE_ARRAY_COUNT(ExpectedIds) == UE_ARRAY_COUNT(ExpectedNames));
    static_assert(UE_ARRAY_COUNT(ExpectedIds) == UE_ARRAY_COUNT(ExpectedProcessOrder));

    const auto VerifyStableOrder = [this](
        const FLBFactoryUIStateSnapshot& Snapshot, const TCHAR* Scenario)
    {
        TestEqual(FString::Printf(TEXT("%s always exposes exactly six process nodes"),
            Scenario), Snapshot.ProductionStages.Num(), 6);
        for (int32 Index = 0; Index < UE_ARRAY_COUNT(ExpectedIds); ++Index)
        {
            if (!Snapshot.ProductionStages.IsValidIndex(Index)) continue;
            const FLBFactoryUIProductionStageSnapshot& Stage =
                Snapshot.ProductionStages[Index];
            TestEqual(FString::Printf(TEXT("%s stage %d retains its stable id"),
                Scenario, Index), Stage.StageId, ExpectedIds[Index]);
            TestEqual(FString::Printf(TEXT("%s stage %d retains its player label"),
                Scenario, Index), Stage.DisplayName, ExpectedNames[Index]);
            TestEqual(FString::Printf(TEXT("%s stage %d retains process order"),
                Scenario, Index), Stage.ProcessOrder, ExpectedProcessOrder[Index]);
        }
    };

    const FLBFactoryUIStateSnapshot& EmptySnapshot = UIState->GetSnapshot(true);
    VerifyStableOrder(EmptySnapshot, TEXT("Empty campaign"));
    for (int32 Index = 0; Index < EmptySnapshot.ProductionStages.Num(); ++Index)
    {
        const FLBFactoryUIProductionStageSnapshot& Stage =
            EmptySnapshot.ProductionStages[Index];
        TestFalse(FString::Printf(TEXT("Empty stage %d never pretends to be installed"),
            Index), Stage.bInstalled);
        TestFalse(FString::Printf(TEXT("Empty stage %d never pretends to be running"),
            Index), Stage.bRunning);
        TestFalse(FString::Printf(TEXT("Empty stage %d never invents a wait state"),
            Index), Stage.bWaiting);
        TestFalse(FString::Printf(TEXT("Empty stage %d never invents a fault"),
            Index), Stage.bFaulted);
        TestEqual(FString::Printf(TEXT("Empty stage %d is labelled not installed"),
            Index), Stage.State, FString(TEXT("NOT INSTALLED")));
        TestEqual(FString::Printf(TEXT("Empty stage %d gives placement guidance"),
            Index), Stage.Detail, FString(TEXT("PLACE THIS PROCESS ASSET")));
        TestFalse(FString::Printf(TEXT("Empty stage %d has no false focus target"),
            Index), Stage.TargetActor.IsValid());
    }

    const FVector CoilLocation(1000.0f, 200.0f, 100.0f);
    ALBFactoryBuildMachine* CoilIntake = SpawnMachineState(World,
        TEXT("FLOW-COIL-INTAKE-001"),
        ELBFactoryBuildMachineType::InboundDeliveryDock,
        ELBFactoryMachineOperatingState::Idle, TEXT("READY FOR DELIVERY"),
        CoilLocation);
    ALBPressShopStorageZone* BlankBuffer =
        World->SpawnActor<ALBPressShopStorageZone>(
            FVector(2000.0f, 200.0f, 0.0f), FRotator::ZeroRotator);
    ALBPressTrainAStation* Press = World->SpawnActor<ALBPressTrainAStation>(
        FVector(3000.0f, 200.0f, 100.0f), FRotator::ZeroRotator);
    ALBPressShopStorageZone* PanelStillages =
        World->SpawnActor<ALBPressShopStorageZone>(
            FVector(4000.0f, 200.0f, 0.0f), FRotator::ZeroRotator);
    TestNotNull(TEXT("Coil-intake stage fixture created"), CoilIntake);
    TestTrue(TEXT("Blank-buffer stage fixture configures with live occupancy"),
        BlankBuffer && BlankBuffer->Configure(TEXT("FLOW-BLANK-BUFFER-001"),
            ELBPressShopStorageType::PreparedBlanks, 12,
            FVector(600.0f, 450.0f, 100.0f))
        && BlankBuffer->TryStore(3));
    TestNotNull(TEXT("Transfer-press stage fixture created"), Press);
    TestTrue(TEXT("Panel-stillage fixture configures as a genuinely full store"),
        PanelStillages && PanelStillages->Configure(TEXT("FLOW-PANEL-STILLAGES-001"),
            ELBPressShopStorageType::FinishedPanelStillages, 2,
            FVector(600.0f, 450.0f, 235.0f))
        && PanelStillages->TryStore(1)
        && PanelStillages->TryStore(1));

    World->BeginPlay();
    const FLBFactoryUIStateSnapshot& PartialSnapshot = UIState->GetSnapshot(true);
    VerifyStableOrder(PartialSnapshot, TEXT("Part-built campaign"));
    if (PartialSnapshot.ProductionStages.Num() == 6)
    {
        const FLBFactoryUIProductionStageSnapshot& Coil =
            PartialSnapshot.ProductionStages[0];
        TestTrue(TEXT("Installed coil intake exposes its real actor and location"),
            Coil.bInstalled && Coil.TargetActor.Get() == CoilIntake
            && Coil.WorldLocation.Equals(CoilLocation));
        TestTrue(TEXT("Idle coil intake remains truthful rather than running/waiting/faulted"),
            Coil.State == TEXT("IDLE") && !Coil.bRunning
            && !Coil.bWaiting && !Coil.bFaulted);
        TestTrue(TEXT("Coil-intake detail exposes live queue count"),
            Coil.Detail.Contains(TEXT("0 coils queued")));

        const FLBFactoryUIProductionStageSnapshot& Blanks =
            PartialSnapshot.ProductionStages[1];
        TestTrue(TEXT("Installed blank buffer exposes live occupancy"),
            Blanks.bInstalled && Blanks.TargetActor.Get() == BlankBuffer
            && Blanks.State == TEXT("READY")
            && Blanks.Detail.Contains(TEXT("3 / 12 blanks"))
            && !Blanks.bWaiting && !Blanks.bFaulted);

        const FLBFactoryUIProductionStageSnapshot& TransferPress =
            PartialSnapshot.ProductionStages[2];
        TestTrue(TEXT("Installed isolated press is shown as waiting, never running"),
            TransferPress.bInstalled && TransferPress.TargetActor.Get() == Press
            && TransferPress.State == TEXT("ISOLATED")
            && TransferPress.bWaiting && !TransferPress.bRunning
            && !TransferPress.bFaulted);
        TestTrue(TEXT("Press detail comes from its live strokes-per-minute authority"),
            TransferPress.Detail.Contains(TEXT("strokes/min")));

        const FLBFactoryUIProductionStageSnapshot& Stillages =
            PartialSnapshot.ProductionStages[3];
        TestTrue(TEXT("Full panel-stillage stage reports its real capacity state"),
            Stillages.bInstalled && Stillages.TargetActor.Get() == PanelStillages
            && Stillages.State == TEXT("FULL")
            && Stillages.Detail.Contains(TEXT("2 / 2 stillages"))
            && !Stillages.bRunning && !Stillages.bFaulted);

        for (int32 Index = 4; Index < 6; ++Index)
        {
            const FLBFactoryUIProductionStageSnapshot& LockedDownstream =
                PartialSnapshot.ProductionStages[Index];
            TestFalse(FString::Printf(TEXT("Unavailable downstream stage %d stays uninstalled"),
                Index), LockedDownstream.bInstalled);
            TestEqual(FString::Printf(TEXT("Unavailable downstream stage %d stays truthful"),
                Index), LockedDownstream.State, FString(TEXT("NOT INSTALLED")));
            TestFalse(FString::Printf(TEXT("Unavailable downstream stage %d has no false target"),
                Index), LockedDownstream.TargetActor.IsValid());
        }
    }

    World->DestroyWorld(false);
    GEngine->DestroyWorldContext(World);
    return true;
}

#endif
