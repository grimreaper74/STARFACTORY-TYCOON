#if WITH_DEV_AUTOMATION_TESTS

#include "Misc/AutomationTest.h"

#include "Engine/Engine.h"
#include "Engine/World.h"
#include "Kismet/GameplayStatics.h"
#include "LBControlRoomOperationsConsole.h"
#include "LBPR005Station.h"
#include "LBPR006Station.h"
#include "LBPR007Station.h"
#include "LBPR008Station.h"
#include "LBPR009Station.h"
#include "LBPR010Station.h"
#include "LBPressShopMaterialFlowController.h"
#include "LBPressShopSaveGame.h"
#include "LBPressTrainAStation.h"

IMPLEMENT_SIMPLE_AUTOMATION_TEST(
    FLBControlRoomOperationsOrderSaveTest,
    "LineBoss.ControlRoom.OperationsConsole.OrderAndSave",
    EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)

IMPLEMENT_SIMPLE_AUTOMATION_TEST(
    FLBControlRoomWholeLineOrchestrationTest,
    "LineBoss.ControlRoom.OperationsConsole.WholeLineStartAndFaultRollback",
    EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)

bool FLBControlRoomOperationsOrderSaveTest::RunTest(const FString& Parameters)
{
    UWorld* World = UWorld::CreateWorld(EWorldType::Game, false, TEXT("LBOperationsConsoleTestWorld"));
    TestNotNull(TEXT("Transient operations world created"), World);
    if (!World) return false;
    FWorldContext& Context = GEngine->CreateNewWorldContext(EWorldType::Game);
    Context.SetCurrentWorld(World);
    World->InitializeActorsForPlay(FURL());
    World->SpawnActor<ALBPR005Station>();
    World->SpawnActor<ALBPR006Station>();
    World->SpawnActor<ALBPR007Station>();
    World->SpawnActor<ALBPR008Station>();
    World->SpawnActor<ALBPR009Station>();
    World->SpawnActor<ALBPR010Station>();
    ALBControlRoomOperationsConsole* Console = World->SpawnActor<ALBControlRoomOperationsConsole>();
    TestNotNull(TEXT("Operations console spawned"), Console);
    World->BeginPlay();
    if (Console && !Console->HasActorBegunPlay()) Console->DispatchBeginPlay();

    if (Console)
    {
        TestNotNull(TEXT("PR-005 authority is bound"), Console->GetBoundPR005Station());
        TestNotNull(TEXT("PR-006 live state is bound"), Console->GetBoundPR006Station());
        TestNotNull(TEXT("PR-007 live state is bound"), Console->GetBoundPR007Station());
        TestNotNull(TEXT("PR-008 live state is bound"), Console->GetBoundPR008Station());
        TestNotNull(TEXT("PR-009 live state is bound"), Console->GetBoundPR009Station());
        TestNotNull(TEXT("PR-010 live state is bound"), Console->GetBoundPR010Station());
        TestFalse(TEXT("Zero-quantity order is rejected safely"), Console->CreateProductionOrder());
        Console->IncreaseQuantity();
        Console->IncreaseQuantity();
        Console->CyclePriority();
        Console->ToggleOperatingMode();
        TestTrue(TEXT("Planning order is created without inventing machine authority"), Console->CreateProductionOrder());
        TestFalse(TEXT("Start remains interlocked without recipe and PR-005 authority"), Console->StartOrResumeOrder());
        TestFalse(TEXT("Coil selection remains honest without inventory authority"), Console->SelectAvailableCoil());

        ULBPressShopSaveGame* Save = Cast<ULBPressShopSaveGame>(
            UGameplayStatics::CreateSaveGameObject(ULBPressShopSaveGame::StaticClass()));
        TestNotNull(TEXT("Press Shop save root created"), Save);
        if (Save)
        {
            Save->ControlRoomOperations = Console->CaptureSaveState();
            TArray<uint8> Bytes;
            TestTrue(TEXT("Control-room order serializes through Press Shop save root"),
                UGameplayStatics::SaveGameToMemory(Save, Bytes));
            ULBPressShopSaveGame* Loaded = Cast<ULBPressShopSaveGame>(UGameplayStatics::LoadGameFromMemory(Bytes));
            TestNotNull(TEXT("Control-room order reloads"), Loaded);
            ALBControlRoomOperationsConsole* Reloaded = World->SpawnActor<ALBControlRoomOperationsConsole>();
            TestTrue(TEXT("Reloaded console accepts versioned order state"),
                Reloaded && Loaded && Reloaded->RestoreSaveState(Loaded->ControlRoomOperations));
            if (Reloaded && Loaded)
            {
                const FLBControlRoomOperationsSaveState State = Reloaded->CaptureSaveState();
                TestEqual(TEXT("Requested quantity persists"), State.RequestedQuantity, 200);
                TestEqual(TEXT("Priority persists"), State.Priority, ELBControlRoomOrderPriority::High);
                TestEqual(TEXT("Assisted Manual mode persists"), State.OperatingMode,
                    ELBControlRoomOperatingMode::AssistedManual);
            }
        }
    }
    World->DestroyWorld(false);
    GEngine->DestroyWorldContext(World);
    return true;
}

bool FLBControlRoomWholeLineOrchestrationTest::RunTest(const FString& Parameters)
{
    UWorld* World = UWorld::CreateWorld(EWorldType::Game, false, TEXT("LBWholeLineOrchestrationTestWorld"));
    TestNotNull(TEXT("Whole-line orchestration world created"), World);
    if (!World) return false;
    FWorldContext& Context = GEngine->CreateNewWorldContext(EWorldType::Game);
    Context.SetCurrentWorld(World);
    World->InitializeActorsForPlay(FURL());

    ALBPR005Station* PR005 = World->SpawnActor<ALBPR005Station>();
    ALBPR006Station* PR006 = World->SpawnActor<ALBPR006Station>();
    ALBPR007Station* PR007 = World->SpawnActor<ALBPR007Station>();
    ALBPR008Station* PR008 = World->SpawnActor<ALBPR008Station>();
    ALBPR009Station* PR009 = World->SpawnActor<ALBPR009Station>();
    ALBPR010Station* PR010 = World->SpawnActor<ALBPR010Station>();
    ALBPressTrainAStation* Train = World->SpawnActor<ALBPressTrainAStation>();
    ALBPressShopMaterialFlowController* Flow = World->SpawnActor<ALBPressShopMaterialFlowController>();
    ALBControlRoomOperationsConsole* Console = World->SpawnActor<ALBControlRoomOperationsConsole>();
    if (!PR005 || !PR006 || !PR007 || !PR008 || !PR009 || !PR010 || !Train || !Flow || !Console)
    {
        AddError(TEXT("A required whole-line authority failed to spawn"));
        World->DestroyWorld(false);
        GEngine->DestroyWorldContext(World);
        return false;
    }

    FLBPR005SaveState PR005Ready;
    PR005Ready.MachineState = ELBStationState::Idle;
    PR005Ready.ControlMode = ELBPR005ControlMode::Manual;
    PR005Ready.CoilId = TEXT("MCX-U-CS10-ORDER-0001");
    PR005Ready.HeatId = TEXT("HT-CW26-ORDER-0001");
    PR005Ready.SupplierLotId = TEXT("LOT-CW26-ORDER-0001");
    PR005Ready.TraceabilityBarcode = TEXT("503184064199901");
    PR005Ready.ActiveRecipeId = TEXT("U_SERIES_1500");
    PR005Ready.CoilWidthMillimetres = 1500.0f;
    PR005Ready.RequiredStripWidthMillimetres = 1500.0f;
    PR005Ready.bControlPowerOn = true;
    PR005Ready.bCertifiedForProduction = true;
    PR005Ready.Checklist.bUtilitiesAvailable = true;
    PR005Ready.Checklist.bCorrectCoilIdentified = true;
    PR005Ready.Checklist.bRecipeSelected = true;
    PR005Ready.Checklist.bCoilCarPositioned = true;
    PR005Ready.Checklist.bMandrelExpanded = true;
    PR005Ready.Checklist.bKeeperEngaged = true;
    PR005Ready.Checklist.bSnubberEngaged = true;
    PR005Ready.Checklist.bGuardsClosed = true;
    PR005Ready.Checklist.bSafetyCircuitReset = true;
    PR005Ready.Checklist.bStripPeeledAndThreaded = true;
    PR005Ready.Checklist.bDryCycleComplete = true;
    PR005Ready.Checklist.bFirstOffProduced = true;
    PR005Ready.Checklist.bQualityApproved = true;
    TestTrue(TEXT("Certified PR-005 authority restores"), PR005->RestoreSaveState(PR005Ready));

    PR006->SetGuardsClosed(true); PR006->SetStripAvailable(true); PR006->SetCassetteLocked(true);
    PR006->SetDrivesHealthy(true); PR006->SetLevellerRecipe(TEXT("L-1500-A"), 1.2f, 1.15f, 16.0f);
    PR007->SetGuardsClosed(true); PR007->SetStripThreaded(true); PR007->SetMistExtractionHealthy(true);
    PR007->SetFluidLevels(80.0f, 75.0f); PR007->SetFilterDifferential(0.3f);
    PR008->SetGuardsClosed(true); PR008->SetStripAvailable(true); PR008->SetStripLoopPercent(50.0f);
    PR008->SetEdgeTrackingDeviation(0.0f); PR008->SetFeedPositionError(0.0f);
    PR008->SetFeedServoHealthy(true); PR008->SetPrePunchToolHealthy(true);
    PR008->SetPressShearLoad(45.0f); PR008->SetHydraulicPressure(215.0f);
    PR008->SetSlugChuteFill(12.0f); PR008->SetScrapBinFill(12.0f);
    PR008->SetBlankOutfeedClear(true); PR008->SetSafetyCircuitHealthy(true);
    PR008->SetEmergencyStopActive(false); PR008->SetBlankRecipe(1450.0f, 6.0f);
    PR008->SetMeasuredCutLength(1450.0f);
    PR009->ConfigureHealthyInputs(false);
    PR009->SetStackRecipe(1, 1, 1.2f);
    PR010->ConfigureHealthyInputs();
    Train->SetAccessInterlocksClosed(true); Train->SetSafetyCircuitHealthy(true);
    Train->SetEmergencyStopActive(false); Train->SetDestackHealthy(true); Train->SetTransferHealthy(true);
    Train->SetHydraulicPressure(280.0f); Train->SetPressLoad(45.0f);
    Train->SetInspectionHealthy(true); Train->SetStillageOutputClear(true);
    TestTrue(TEXT("Selected train has an installed approved Cairnwell roof-panel die"),
        Train->SetActiveProductionRecipe(
            TEXT("CAIRNWELL_2040"), TEXT("ROOF_PANEL"), TEXT("DIE_ROOF_2040")));

    World->BeginPlay();
    if (!Flow->HasActorBegunPlay()) Flow->DispatchBeginPlay();
    if (!Console->HasActorBegunPlay()) Console->DispatchBeginPlay();
    Console->RefreshForEditorEvidence();
    TestNotNull(TEXT("Console binds transactional material-flow authority"), Console->GetBoundMaterialFlow());
    TestTrue(TEXT("Control room binds the selected train by immutable GUID"),
        Console->CaptureSaveState().AssignedTrainGuid == Train->GetPersistentTrainGuid());
    TestEqual(TEXT("Control-room identity-aware planning record is version two"),
        Console->CaptureSaveState().Version, 2);
    Console->IncreaseQuantity();
    TestTrue(TEXT("Authoritative recipe resolves"), Console->ResolveRecipeAuthority(TEXT("U_SERIES_1500"), 1500.0f));
    TestTrue(TEXT("Whole-line order is created"), Console->CreateProductionOrder());
    FLBControlRoomOperationsSaveState OnePanelOrder = Console->CaptureSaveState();
    OnePanelOrder.RequestedQuantity = 1;
    TestTrue(TEXT("Validation order restores with one requested panel"), Console->RestoreSaveState(OnePanelOrder));
    TestTrue(TEXT("Recipe authority is deliberately re-established after restore"),
        Console->ResolveRecipeAuthority(TEXT("U_SERIES_1500"), 1500.0f));
    TestTrue(TEXT("Control room accepts complete automatic line start"), Console->StartOrResumeOrder());
    TestEqual(TEXT("PR-005 begins production start"), PR005->GetMachineState(), ELBStationState::Starting);
    TestEqual(TEXT("PR-006 begins calibration"), PR006->GetHMIStatus().State, ELBPR006State::Calibrating);
    TestEqual(TEXT("PR-007 begins priming"), PR007->GetHMIStatus().State, ELBPR007State::Priming);
    TestEqual(TEXT("PR-008 begins threading"), PR008->GetHMIStatus().State, ELBPR008State::Threading);
    TestEqual(TEXT("PR-009 waits powered for a traceable blank"), PR009->GetHMIStatus().State, ELBPR009State::Ready);
    TestEqual(TEXT("PR-010 waits for a traceable stack"), PR010->GetHMIStatus().State, ELBPR010State::ReservationWait);
    TestEqual(TEXT("Train remains safely isolated until PR-010 reserves material"),
        Train->GetHMIStatus().State, ELBPressTrainAState::Isolated);

    PR007->SetGuardsClosed(false);
    Console->Tick(0.3f);
    const FLBControlRoomOperationsSaveState Held = Console->CaptureSaveState();
    TestEqual(TEXT("Downstream fault holds the production order"), Held.OrderState, ELBControlRoomOrderState::Held);
    TestTrue(TEXT("Hold identifies PR-007 authority"), Held.LastAlarm.Contains(TEXT("PR-007")));
    TestEqual(TEXT("Fault rollback requests PR-005 controlled stop"),
        PR005->GetMachineState(), ELBStationState::Stopping);

    PR007->SetGuardsClosed(true);
    TestTrue(TEXT("Corrected PR-007 guard fault resets"), PR007->ResetFault());
    PR005->Tick(2.0f); PR006->Tick(2.0f); PR007->Tick(2.0f);
    PR008->Tick(2.0f); PR009->Tick(2.0f); PR010->Tick(2.0f);
    const bool bResumed = Console->StartOrResumeOrder();
    TestTrue(FString::Printf(TEXT("Held order explicitly resumes after corrected fault: %s"),
        *Console->CaptureSaveState().LastAlarm), bResumed);

    PR005->Tick(3.0f); PR006->Tick(3.0f); PR007->Tick(3.0f); PR008->Tick(22.0f);
    TestTrue(TEXT("PR-008 creates an identified production blank"), PR008->GetHMIStatus().PendingBlankCount > 0);
    Console->Tick(0.3f);
    TestTrue(TEXT("Console transaction transfers the identified blank to PR-009"),
        PR009->GetHMIStatus().State != ELBPR009State::Ready);
    for (int32 Index = 0; Index < 12 && PR009->GetHMIStatus().CarriersReleased == 0; ++Index)
        PR009->Tick(1.1f);
    TestEqual(TEXT("One-blank validation recipe releases one traced carrier"),
        PR009->GetHMIStatus().PendingReleasedBlankCount, 1);
    Console->Tick(0.3f);
    for (int32 Index = 0; Index < 12; ++Index) PR010->Tick(0.5f);
    TestEqual(TEXT("PR-010 stores the transferred stack"), PR010->GetHMIStatus().TotalStacksStored, 1);
    Console->Tick(0.3f);
    for (int32 Index = 0; Index < 12; ++Index) PR010->Tick(0.5f);
    TestEqual(TEXT("PR-010 dispatches the reserved traced stack"), PR010->GetHMIStatus().TotalStacksDispatched, 1);
    Console->Tick(0.3f);
    TestTrue(TEXT("Released PR-010 blank reaches the selected train"),
        Train->GetHMIStatus().State == ELBPressTrainAState::Cycling
        || Train->GetHMIStatus().PendingBlankCount > 0);
    Train->Tick(6.1f);
    Console->Tick(0.3f);
    TestEqual(TEXT("Authoritative finished panel advances the control-room order"),
        Console->CaptureSaveState().GoodPanels, 1);
    TestEqual(TEXT("Requested good-panel quantity completes the production order"),
        Console->CaptureSaveState().OrderState, ELBControlRoomOrderState::Completed);
    TestTrue(TEXT("Unknown remaining coil length remains an honest authority hold"),
        Console->CaptureSaveState().RemainingMaterialMetres < 0.0f);

    ULBPressShopSaveGame* CompletedSave = Cast<ULBPressShopSaveGame>(
        UGameplayStatics::CreateSaveGameObject(ULBPressShopSaveGame::StaticClass()));
    CompletedSave->ControlRoomOperations = Console->CaptureSaveState();
    TArray<uint8> CompletedBytes;
    TestTrue(TEXT("Completed orchestrated order serializes through the campaign root"),
        UGameplayStatics::SaveGameToMemory(CompletedSave, CompletedBytes));
    ULBPressShopSaveGame* CompletedLoaded = Cast<ULBPressShopSaveGame>(
        UGameplayStatics::LoadGameFromMemory(CompletedBytes));
    ALBControlRoomOperationsConsole* ReloadedConsole = World->SpawnActor<ALBControlRoomOperationsConsole>();
    TestTrue(TEXT("Completed orchestrated order restores"), ReloadedConsole && CompletedLoaded
        && ReloadedConsole->RestoreSaveState(CompletedLoaded->ControlRoomOperations));
    if (ReloadedConsole)
    {
        const FLBControlRoomOperationsSaveState ReloadedState = ReloadedConsole->CaptureSaveState();
        TestEqual(TEXT("Completion state persists"), ReloadedState.OrderState, ELBControlRoomOrderState::Completed);
        TestEqual(TEXT("Authoritative good-panel count persists"), ReloadedState.GoodPanels, 1);
        TestTrue(TEXT("PR-010 released stack genealogy persists in order orchestration"),
            !ReloadedState.ActiveReleasedStackId.IsNone());
        TestTrue(TEXT("Transaction sequence remains monotonic after load"),
            ReloadedState.NextOrchestrationTransactionSerial > 1);
    }

    World->DestroyWorld(false);
    GEngine->DestroyWorldContext(World);
    return true;
}

#endif
