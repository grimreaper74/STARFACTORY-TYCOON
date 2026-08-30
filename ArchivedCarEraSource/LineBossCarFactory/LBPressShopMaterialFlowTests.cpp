#if WITH_DEV_AUTOMATION_TESTS

#include "Misc/AutomationTest.h"
#include "Engine/Engine.h"
#include "Engine/World.h"
#include "LBPR004Station.h"
#include "LBPR005Station.h"
#include "LBPR008Station.h"
#include "LBPR009Station.h"
#include "LBPR010Station.h"
#include "LBPressShopMaterialFlowController.h"
#include "LBPressShopSaveGame.h"
#include "Kismet/GameplayStatics.h"

IMPLEMENT_SIMPLE_AUTOMATION_TEST(
    FLBPressShopPR004ToPR005TraceableHandoffTest,
    "LineBoss.PressShop.MaterialFlow.PR004ToPR005TraceableHandoff",
    EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)

IMPLEMENT_SIMPLE_AUTOMATION_TEST(
    FLBPressShopPR004ToPR005DiskSlotReadbackTest,
    "LineBoss.PressShop.Save.PR004PR005DiskSlotReadback",
    EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)

IMPLEMENT_SIMPLE_AUTOMATION_TEST(
    FLBPressShopPR008ToPR009TraceableBlankHandoffTest,
    "LineBoss.PressShop.MaterialFlow.PR008ToPR009TraceableBlankHandoff",
    EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)

IMPLEMENT_SIMPLE_AUTOMATION_TEST(
    FLBPressShopPR009ToPR010TraceableStackHandoffTest,
    "LineBoss.PressShop.MaterialFlow.PR009ToPR010TraceableStackHandoff",
    EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)

namespace
{
    constexpr const TCHAR* HandoffSaveSlot = TEXT("LB_AUTOMATION_PR004_PR005_HANDOFF_V001");
}

bool FLBPressShopPR004ToPR005TraceableHandoffTest::RunTest(const FString& Parameters)
{
    UWorld* World = UWorld::CreateWorld(EWorldType::Game, false, TEXT("LB_PR004_PR005_HandoffTest"));
    TestNotNull(TEXT("Transient Press Shop world exists"), World);
    if (!World) return false;
    FWorldContext& Context = GEngine->CreateNewWorldContext(EWorldType::Game);
    Context.SetCurrentWorld(World);
    World->InitializeActorsForPlay(FURL());
    World->BeginPlay();

    ALBPR004Station* PR004 = World->SpawnActor<ALBPR004Station>();
    ALBPR005Station* PR005 = World->SpawnActor<ALBPR005Station>();
    ALBPR005Station* ReloadedPR005 = World->SpawnActor<ALBPR005Station>();
    ALBPressShopMaterialFlowController* Flow = World->SpawnActor<ALBPressShopMaterialFlowController>();
    TestNotNull(TEXT("PR-004 station spawns"), PR004);
    TestNotNull(TEXT("PR-005 station spawns"), PR005);
    TestNotNull(TEXT("Material-flow controller spawns"), Flow);
    if (!PR004 || !PR005 || !ReloadedPR005 || !Flow)
    {
        World->DestroyWorld(false);
        GEngine->DestroyWorldContext(World);
        return false;
    }

    const FString CoilId(TEXT("MCX-U-CS10-0001"));
    const FString HeatId(TEXT("HT-CW26-08417"));
    const FString SupplierLotId(TEXT("LOT-MCXU-260804-A"));
    const FString Barcode(TEXT("503184064100010"));

    TestTrue(TEXT("PR-004 control power enables"), PR004->SetControlPower(true));
    TestTrue(TEXT("PR-004 commissions"), PR004->SetCellCommissioned(true));
    TestTrue(TEXT("Traceable packaged coil loads"),
        PR004->LoadPackagedCoilWithTraceability(CoilId, HeatId, SupplierLotId, Barcode));
    TestTrue(TEXT("PR-004 recipe reserves the same coil"),
        PR004->SelectDepackRecipe(TEXT("PR004_DEPACK_STANDARD"), CoilId));
    TestTrue(TEXT("Preparation cradle locks"), PR004->SetCradleLocked(true));
    TestTrue(TEXT("C-hook withdraws"), PR004->SetCHookWithdrawn(true));
    TestTrue(TEXT("Player action changes only the selected coil to bare"),
        PR004->UnpackageCoil(TEXT("AUTOMATION_PLAYER_UNPACKAGE")));

    TestTrue(TEXT("PR-005 recipe selects the authored 1500 mm strip"),
        PR005->SelectRecipe(TEXT("U_SERIES_1500"), 1500.0f));
    Flow->BindStations(PR004, PR005);
    TArray<FText> Blockers;
    TestTrue(TEXT("Exact identified coil is ready for transactional handoff"),
        Flow->CanTransferReadyCoil(1500.0f, Blockers));
    TestEqual(TEXT("Handoff has no blockers"), Blockers.Num(), 0);
    TestTrue(TEXT("Transactional PR-004 to PR-005 handoff completes"),
        Flow->TransferReadyCoilToPR005(TEXT("TX-PR004-PR005-0001"), 1500.0f));

    TestEqual(TEXT("PR-004 releases ownership only after PR-005 acceptance"),
        PR004->GetProcessState(), ELBPR004State::AwaitingCoil);
    TestTrue(TEXT("PR-004 active coil identity clears"), PR004->GetCurrentCoilId().IsEmpty());
    TestEqual(TEXT("PR-005 owns the exact coil"), PR005->GetCurrentCoilId(), CoilId);
    TestEqual(TEXT("PR-005 preserves steel heat"), PR005->GetCurrentHeatId(), HeatId);
    TestEqual(TEXT("PR-005 preserves supplier lot"), PR005->GetCurrentSupplierLotId(), SupplierLotId);
    TestEqual(TEXT("PR-005 preserves barcode"), PR005->GetCurrentTraceabilityBarcode(), Barcode);
    TestEqual(TEXT("Accepted coil begins at the inbound coil-car presentation datum"),
        PR005->GetCoilLoadingPresentationProgress(), 0.0f);
    PR005->Tick(2.5f);
    TestTrue(TEXT("Coil-car loading presentation advances through a visible intermediate pose"),
        PR005->GetCoilLoadingPresentationProgress() > 0.45f
        && PR005->GetCoilLoadingPresentationProgress() < 0.55f);
    PR005->Tick(3.0f);
    TestEqual(TEXT("Coil-car loading presentation settles at the mandrel"),
        PR005->GetCoilLoadingPresentationProgress(), 1.0f);
    TestTrue(TEXT("Settled loading presentation proves coil-car positioning"),
        PR005->CaptureSaveState().Checklist.bCoilCarPositioned);

    ULBPressShopSaveGame* SaveRoot = NewObject<ULBPressShopSaveGame>();
    TestNotNull(TEXT("Versioned Press Shop save root exists"), SaveRoot);
    SaveRoot->PR005 = PR005->CaptureSaveState();
    TestTrue(TEXT("Transferred PR-004 empty state is stable and saveable"),
        PR004->GetStableSaveState(SaveRoot->PR004));
    TestEqual(TEXT("Factory save root is current format 18"), SaveRoot->SaveFormatVersion, 18);
    TestEqual(TEXT("PR-005 traceable save advances to version 2"), SaveRoot->PR005.Version, 2);
    TArray<uint8> SaveBytes;
    TestTrue(TEXT("Press Shop save root serializes to memory"),
        UGameplayStatics::SaveGameToMemory(SaveRoot, SaveBytes));
    ULBPressShopSaveGame* LoadedRoot = Cast<ULBPressShopSaveGame>(
        UGameplayStatics::LoadGameFromMemory(SaveBytes));
    TestNotNull(TEXT("Serialized Press Shop save root loads from memory"), LoadedRoot);
    if (LoadedRoot)
    {
        TestEqual(TEXT("Serialized root preserves save format"), LoadedRoot->SaveFormatVersion, 18);
        TestEqual(TEXT("Serialized root preserves PR-005 barcode"),
            LoadedRoot->PR005.TraceabilityBarcode, Barcode);
    }
    TestTrue(TEXT("Traceable production state writes to the named disk slot"),
        UGameplayStatics::SaveGameToSlot(SaveRoot, HandoffSaveSlot, 0));
    TestTrue(TEXT("Fresh PR-005 restores traceable handoff state"),
        ReloadedPR005->RestoreSaveState(LoadedRoot ? LoadedRoot->PR005 : SaveRoot->PR005));
    TestEqual(TEXT("Reload preserves coil identity"), ReloadedPR005->GetCurrentCoilId(), CoilId);
    TestEqual(TEXT("Reload preserves steel heat"), ReloadedPR005->GetCurrentHeatId(), HeatId);
    TestEqual(TEXT("Reload preserves supplier lot"), ReloadedPR005->GetCurrentSupplierLotId(), SupplierLotId);
    TestEqual(TEXT("Reload preserves barcode"), ReloadedPR005->GetCurrentTraceabilityBarcode(), Barcode);

    World->DestroyWorld(false);
    GEngine->DestroyWorldContext(World);
    return true;
}

bool FLBPressShopPR004ToPR005DiskSlotReadbackTest::RunTest(const FString& Parameters)
{
    TestTrue(TEXT("Writer process left the named handoff save slot"),
        UGameplayStatics::DoesSaveGameExist(HandoffSaveSlot, 0));
    ULBPressShopSaveGame* Loaded = Cast<ULBPressShopSaveGame>(
        UGameplayStatics::LoadGameFromSlot(HandoffSaveSlot, 0));
    TestNotNull(TEXT("Fresh process loads the Press Shop save root"), Loaded);
    if (Loaded)
    {
        TestEqual(TEXT("Disk slot preserves factory format"), Loaded->SaveFormatVersion, 18);
        TestEqual(TEXT("Disk slot preserves PR-004 released state"),
            Loaded->PR004.State, ELBPR004State::AwaitingCoil);
        TestTrue(TEXT("Disk slot preserves empty PR-004 ownership"), Loaded->PR004.CoilId.IsEmpty());
        TestEqual(TEXT("Disk slot preserves PR-005 snapshot version"), Loaded->PR005.Version, 2);
        TestEqual(TEXT("Disk slot preserves exact PR-005 coil"),
            Loaded->PR005.CoilId, FString(TEXT("MCX-U-CS10-0001")));
        TestEqual(TEXT("Disk slot preserves steel heat"),
            Loaded->PR005.HeatId, FString(TEXT("HT-CW26-08417")));
        TestEqual(TEXT("Disk slot preserves supplier lot"),
            Loaded->PR005.SupplierLotId, FString(TEXT("LOT-MCXU-260804-A")));
        TestEqual(TEXT("Disk slot preserves barcode"),
            Loaded->PR005.TraceabilityBarcode, FString(TEXT("503184064100010")));
    }
    TestTrue(TEXT("Named automation slot is removed after readback"),
        UGameplayStatics::DeleteGameInSlot(HandoffSaveSlot, 0));
    TestFalse(TEXT("No automation save slot remains"),
        UGameplayStatics::DoesSaveGameExist(HandoffSaveSlot, 0));
    return true;
}

bool FLBPressShopPR008ToPR009TraceableBlankHandoffTest::RunTest(const FString& Parameters)
{
    UWorld* World = UWorld::CreateWorld(EWorldType::Game, false, TEXT("LB_PR008_PR009_BlankHandoffTest"));
    TestNotNull(TEXT("Transient downstream material-flow world exists"), World);
    if (!World) return false;
    FWorldContext& Context = GEngine->CreateNewWorldContext(EWorldType::Game);
    Context.SetCurrentWorld(World);
    World->InitializeActorsForPlay(FURL());
    World->BeginPlay();

    ALBPR008Station* PR008 = World->SpawnActor<ALBPR008Station>();
    ALBPR009Station* PR009 = World->SpawnActor<ALBPR009Station>();
    ALBPR008Station* ReloadedPR008 = World->SpawnActor<ALBPR008Station>();
    ALBPR009Station* ReloadedPR009 = World->SpawnActor<ALBPR009Station>();
    ALBPressShopMaterialFlowController* Flow = World->SpawnActor<ALBPressShopMaterialFlowController>();
    TestNotNull(TEXT("PR-008 station spawns"), PR008);
    TestNotNull(TEXT("PR-009 station spawns"), PR009);
    TestNotNull(TEXT("Downstream material-flow controller spawns"), Flow);
    if (!PR008 || !PR009 || !ReloadedPR008 || !ReloadedPR009 || !Flow)
    {
        World->DestroyWorld(false);
        GEngine->DestroyWorldContext(World);
        return false;
    }

    const FName Authority(TEXT("CW.MW.CONTROL_ROOM"));
    const FName PR008Source(TEXT("MW.MCR.PR008.CONSOLE"));
    const FName PR009Source(TEXT("MW.MCR.PR009.CONSOLE"));
    PR008->SetGuardsClosed(true);
    PR008->SetStripAvailable(true);
    PR008->SetStripLoopPercent(50.0f);
    PR008->SetEdgeTrackingDeviation(0.0f);
    PR008->SetFeedPositionError(0.0f);
    PR008->SetFeedServoHealthy(true);
    PR008->SetPrePunchToolHealthy(true);
    PR008->SetPressShearLoad(45.0f);
    PR008->SetHydraulicPressure(215.0f);
    PR008->SetSlugChuteFill(12.0f);
    PR008->SetScrapBinFill(12.0f);
    PR008->SetBlankOutfeedClear(true);
    PR008->SetSafetyCircuitHealthy(true);
    PR008->SetEmergencyStopActive(false);
    PR008->SetBlankRecipe(1450.0f, 60.0f);
    PR008->SetMeasuredCutLength(1450.0f);
    TestTrue(TEXT("Authorised control room powers PR-008"),
        PR008->ExecuteRemoteCommand(ELBPR008Command::PowerOn, PR008Source, Authority));
    TestTrue(TEXT("Authorised control room starts PR-008"),
        PR008->ExecuteRemoteCommand(ELBPR008Command::Start, PR008Source, Authority));
    PR008->Tick(2.0f);
    TestTrue(TEXT("PR-008 produces an identified blank"), PR008->GetPendingBlankCount() > 0);
    const FName ProducedBlankId = PR008->GetOldestPendingBlankId();
    TestFalse(TEXT("Produced blank identity is non-empty"), ProducedBlankId.IsNone());

    PR009->ConfigureHealthyInputs(false);
    TestTrue(TEXT("Authorised control room powers PR-009"),
        PR009->ExecuteRemoteCommand(ELBPR009Command::PowerOn, PR009Source, Authority));
    Flow->BindBlankStations(PR008, PR009);
    TArray<FText> Blockers;
    TestTrue(TEXT("Exact PR-008 blank is ready for transactional handoff"),
        Flow->CanTransferProducedBlank(Blockers));
    TestEqual(TEXT("Blank handoff has no blockers"), Blockers.Num(), 0);
    const int32 PendingBefore = PR008->GetPendingBlankCount();
    TestTrue(TEXT("Transactional PR-008 to PR-009 blank handoff completes"),
        Flow->TransferProducedBlankToPR009(TEXT("TX-PR008-PR009-0001")));
    TestEqual(TEXT("PR-008 releases one blank only after PR-009 acceptance"),
        PR008->GetPendingBlankCount(), PendingBefore - 1);
    TestEqual(TEXT("PR-009 owns the exact semantic blank"),
        PR009->GetHMIStatus().CurrentBlankId, ProducedBlankId);
    TestTrue(TEXT("PR-009 exposes the accepted blank as available"),
        PR009->GetHMIStatus().bUpstreamBlankAvailable);

    ULBPressShopSaveGame* SaveRoot = NewObject<ULBPressShopSaveGame>();
    SaveRoot->PR008 = PR008->CaptureSaveState();
    SaveRoot->PR009 = PR009->CaptureSaveState();
    TArray<uint8> SaveBytes;
    TestTrue(TEXT("Traceable downstream state serializes"), UGameplayStatics::SaveGameToMemory(SaveRoot, SaveBytes));
    ULBPressShopSaveGame* LoadedRoot = Cast<ULBPressShopSaveGame>(UGameplayStatics::LoadGameFromMemory(SaveBytes));
    TestNotNull(TEXT("Traceable downstream state reloads"), LoadedRoot);
    TestTrue(TEXT("Fresh PR-008 restores its remaining buffer"),
        ReloadedPR008->RestoreSaveState(LoadedRoot ? LoadedRoot->PR008 : SaveRoot->PR008));
    TestTrue(TEXT("Fresh PR-009 restores accepted blank ownership"),
        ReloadedPR009->RestoreSaveState(LoadedRoot ? LoadedRoot->PR009 : SaveRoot->PR009));
    TestEqual(TEXT("Save/load preserves the exact PR-009 blank identity"),
        ReloadedPR009->GetHMIStatus().CurrentBlankId, ProducedBlankId);

    TestTrue(TEXT("PR-009 begins processing the accepted blank"),
        PR009->ExecuteRemoteCommand(ELBPR009Command::Start, PR009Source, Authority));
    PR009->Tick(1.1f);
    PR009->Tick(0.6f);
    PR009->Tick(0.8f);
    TestEqual(TEXT("Processed blank returns PR-009 to receiving"),
        PR009->GetHMIStatus().State, ELBPR009State::Receiving);
    TestFalse(TEXT("PR-009 does not invent the next upstream blank"),
        PR009->GetHMIStatus().bUpstreamBlankAvailable);
    PR009->Tick(3.0f);
    TestEqual(TEXT("Waiting for material is not falsely raised as a machine fault"),
        PR009->GetHMIStatus().ActiveFault, ELBPR009Fault::None);

    PR008->Tick(2.0f);
    TestTrue(TEXT("PR-008 buffers the next identified blank"), PR008->GetPendingBlankCount() > 0);
    const int32 BlockedPendingCount = PR008->GetPendingBlankCount();
    PR009->SetReceiverClear(false);
    Blockers.Reset();
    TestFalse(TEXT("Blocked PR-009 receiver prevents transfer"), Flow->CanTransferProducedBlank(Blockers));
    TestFalse(TEXT("Blocked transfer cannot consume a PR-008 blank"),
        Flow->TransferProducedBlankToPR009(TEXT("TX-PR008-PR009-BLOCKED")));
    TestEqual(TEXT("Rejected transaction preserves PR-008 ownership"),
        PR008->GetPendingBlankCount(), BlockedPendingCount);

    World->DestroyWorld(false);
    GEngine->DestroyWorldContext(World);
    return true;
}

bool FLBPressShopPR009ToPR010TraceableStackHandoffTest::RunTest(const FString& Parameters)
{
    UWorld* World = UWorld::CreateWorld(EWorldType::Game, false, TEXT("LB_PR009_PR010_StackHandoffTest"));
    TestNotNull(TEXT("Transient stack-flow world exists"), World);
    if (!World) return false;
    FWorldContext& Context = GEngine->CreateNewWorldContext(EWorldType::Game);
    Context.SetCurrentWorld(World);
    World->InitializeActorsForPlay(FURL());
    World->BeginPlay();

    ALBPR009Station* PR009 = World->SpawnActor<ALBPR009Station>();
    ALBPR010Station* PR010 = World->SpawnActor<ALBPR010Station>();
    ALBPR009Station* ReloadedPR009 = World->SpawnActor<ALBPR009Station>();
    ALBPR010Station* ReloadedPR010 = World->SpawnActor<ALBPR010Station>();
    ALBPressShopMaterialFlowController* Flow = World->SpawnActor<ALBPressShopMaterialFlowController>();
    TestNotNull(TEXT("PR-009 stacker spawns"), PR009);
    TestNotNull(TEXT("PR-010 buffer spawns"), PR010);
    TestNotNull(TEXT("Stack material-flow controller spawns"), Flow);
    if (!PR009 || !PR010 || !ReloadedPR009 || !ReloadedPR010 || !Flow)
    {
        World->DestroyWorld(false);
        GEngine->DestroyWorldContext(World);
        return false;
    }

    const FName Authority(TEXT("CW.MW.CONTROL_ROOM"));
    const FName PR009Source(TEXT("MW.MCR.PR009.CONSOLE"));
    const FName PR010Source(TEXT("MW.MCR.PR010.CONSOLE"));
    const TArray<FName> ExpectedBlankIds = {TEXT("PR008-BLANK-TRACE-0001"), TEXT("PR008-BLANK-TRACE-0002")};

    PR009->ConfigureHealthyInputs(false);
    PR009->SetStackRecipe(2, 0, 1.2f);
    TestTrue(TEXT("Control room powers PR-009 for stack traceability"),
        PR009->ExecuteRemoteCommand(ELBPR009Command::PowerOn, PR009Source, Authority));
    TestTrue(TEXT("Control room starts PR-009 for stack traceability"),
        PR009->ExecuteRemoteCommand(ELBPR009Command::Start, PR009Source, Authority));
    int32 NextBlankIndex = 0;
    for (int32 TickIndex = 0; TickIndex < 20 && PR009->GetHMIStatus().CarriersReleased == 0; ++TickIndex)
    {
        const FLBPR009HMIStatus Status = PR009->GetHMIStatus();
        if (Status.State == ELBPR009State::Receiving && !Status.bUpstreamBlankAvailable
            && ExpectedBlankIds.IsValidIndex(NextBlankIndex))
        {
            PR009->SetUpstreamBlankAvailable(true, ExpectedBlankIds[NextBlankIndex++]);
        }
        PR009->Tick(1.1f);
    }
    const FLBPR009HMIStatus Released = PR009->GetHMIStatus();
    TestEqual(TEXT("PR-009 releases exactly one test stack"), Released.CarriersReleased, 1);
    TestEqual(TEXT("Released stack manifest has both blanks"), Released.PendingReleasedBlankCount, 2);
    const FName ReleasedStackId = Released.PendingReleasedStackId;
    TestFalse(TEXT("Released stack has a semantic identity"), ReleasedStackId.IsNone());

    PR010->ConfigureHealthyInputs();
    TestTrue(TEXT("Control room powers PR-010 for stack receipt"),
        PR010->ExecuteRemoteCommand(ELBPR010Command::PowerOn, PR010Source, Authority));
    TestTrue(TEXT("Control room starts PR-010 for stack receipt"),
        PR010->ExecuteRemoteCommand(ELBPR010Command::Start, PR010Source, Authority));
    Flow->BindStackStations(PR009, PR010);
    TArray<FText> Blockers;
    TestTrue(TEXT("Traceable released stack is ready for PR-010"), Flow->CanTransferReleasedStack(Blockers));
    TestEqual(TEXT("Traceable stack handoff has no blockers"), Blockers.Num(), 0);
    TestTrue(TEXT("Transactional PR-009 to PR-010 stack handoff completes"),
        Flow->TransferReleasedStackToPR010(TEXT("TX-PR009-PR010-0001")));
    TestTrue(TEXT("PR-009 clears ownership only after PR-010 acceptance"),
        PR009->GetHMIStatus().PendingReleasedStackId.IsNone());
    TestEqual(TEXT("PR-010 owns the exact inbound stack"), PR010->GetHMIStatus().InboundStackId, ReleasedStackId);
    TArray<FName> ReceivedBlankIds;
    TestTrue(TEXT("PR-010 exposes the received stack manifest"), PR010->GetBlankIdsForStack(ReleasedStackId, ReceivedBlankIds));
    TestEqual(TEXT("PR-010 manifest retains exact blank count"), ReceivedBlankIds.Num(), ExpectedBlankIds.Num());
    TestEqual(TEXT("PR-010 manifest retains first blank identity"), ReceivedBlankIds[0], ExpectedBlankIds[0]);
    TestEqual(TEXT("PR-010 manifest retains second blank identity"), ReceivedBlankIds[1], ExpectedBlankIds[1]);

    ULBPressShopSaveGame* SaveRoot = NewObject<ULBPressShopSaveGame>();
    SaveRoot->PR009 = PR009->CaptureSaveState();
    SaveRoot->PR010 = PR010->CaptureSaveState();
    TestEqual(TEXT("Stack genealogy preserves factory root format eighteen"), SaveRoot->SaveFormatVersion, 18);
    TestEqual(TEXT("PR-009 stack genealogy snapshot is version two"), SaveRoot->PR009.Version, 2);
    TestEqual(TEXT("PR-010 stack genealogy snapshot is version two"), SaveRoot->PR010.Version, 2);
    TArray<uint8> SaveBytes;
    TestTrue(TEXT("Stack genealogy serializes"), UGameplayStatics::SaveGameToMemory(SaveRoot, SaveBytes));
    ULBPressShopSaveGame* Loaded = Cast<ULBPressShopSaveGame>(UGameplayStatics::LoadGameFromMemory(SaveBytes));
    TestNotNull(TEXT("Stack genealogy reloads"), Loaded);
    TestTrue(TEXT("Fresh PR-009 restores released ownership state"),
        ReloadedPR009->RestoreSaveState(Loaded ? Loaded->PR009 : SaveRoot->PR009));
    TestTrue(TEXT("Fresh PR-010 restores inbound stack genealogy"),
        ReloadedPR010->RestoreSaveState(Loaded ? Loaded->PR010 : SaveRoot->PR010));
    ReceivedBlankIds.Reset();
    TestTrue(TEXT("Reloaded PR-010 still resolves the stack manifest"),
        ReloadedPR010->GetBlankIdsForStack(ReleasedStackId, ReceivedBlankIds));
    TestEqual(TEXT("Reloaded manifest retains all blanks"), ReceivedBlankIds.Num(), 2);

    for (int32 TickIndex = 0; TickIndex < 12; ++TickIndex) PR010->Tick(0.5f);
    TestEqual(TEXT("PR-010 stores the exact received stack"), PR010->GetHMIStatus().TotalStacksStored, 1);
    ReceivedBlankIds.Reset();
    TestTrue(TEXT("Stored stack retains its blank genealogy"), PR010->GetBlankIdsForStack(ReleasedStackId, ReceivedBlankIds));
    TestEqual(TEXT("Stored stack still contains both exact blanks"), ReceivedBlankIds.Num(), 2);

    World->DestroyWorld(false);
    GEngine->DestroyWorldContext(World);
    return true;
}

#endif
