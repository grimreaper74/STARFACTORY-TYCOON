#include "LBOneFactoryProductionFlow.h"
#include "LBVehiclePanelCatalog.h"

#if WITH_DEV_AUTOMATION_TESTS

#include "Misc/AutomationTest.h"
#include "Engine/World.h"

namespace LBOneFactoryProductionFlowTestsPrivate
{
    UWorld* MakeWorld(const FName Name)
    {
        return UWorld::CreateWorld(EWorldType::Game, false, Name);
    }

    ALBOneFactoryProductionFlowAuthority* MakeAuthority(UWorld* World)
    {
        return World ? World->SpawnActor<ALBOneFactoryProductionFlowAuthority>() : nullptr;
    }

    void DestroyWorld(UWorld*& World)
    {
        if (!World) return;
        World->DestroyWorld(false);
        World = nullptr;
    }

    void CommissionAll(ALBOneFactoryProductionFlowAuthority& Authority,
        FString& Reason)
    {
        Authority.SetDepartmentCommissioned(ELBOneFactoryDepartment::Press, true, Reason);
        Authority.SetDepartmentCommissioned(ELBOneFactoryDepartment::Body, true, Reason);
        Authority.SetDepartmentCommissioned(ELBOneFactoryDepartment::Paint, true, Reason);
        Authority.SetDepartmentCommissioned(ELBOneFactoryDepartment::Assembly, true, Reason);
    }
}

IMPLEMENT_SIMPLE_AUTOMATION_TEST(FLBOneFactoryProductionEndToEndTest,
    "LineBoss.OneFactory.ProductionFlow.EndToEndGenealogyQualityAndDispatch",
    EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)

bool FLBOneFactoryProductionEndToEndTest::RunTest(const FString& Parameters)
{
    using namespace LBOneFactoryProductionFlowTestsPrivate;
    UWorld* World = MakeWorld(TEXT("LBOneFactoryProductionEndToEndTest"));
    ALBOneFactoryProductionFlowAuthority* Authority = MakeAuthority(World);
    TestNotNull(TEXT("Production authority exists"), Authority);
    if (!Authority) { DestroyWorld(World); return false; }

    FString Reason;
    CommissionAll(*Authority, Reason);
    FName UnitId;
    TestTrue(TEXT("Commissioned Press accepts one complete vehicle order"),
        Authority->CreateVehicleOrder(TEXT("ORDER-0001"), TEXT("CAIRNWELL_2040"),
            TEXT("PAINT-CAIRNWELL-TEAL"), TEXT("CAIRNWELL-TEAL"),
            TEXT("COIL-LOT-0001"), TEXT("PRESS-INBOUND"), UnitId, Reason));
    TestEqual(TEXT("First deterministic vehicle identity"), UnitId,
        FName(TEXT("CAIRNWELL_2040-000001")));

    int32 EvidenceSerial = 1;
    for (;;)
    {
        const FLBOneFactoryProductionLedgerState Before = Authority->CaptureLedger();
        const FLBOneFactoryVehicleUnitState* Unit = Before.Units.FindByPredicate(
            [UnitId](const FLBOneFactoryVehicleUnitState& Row)
            { return Row.UnitId == UnitId; });
        TestNotNull(TEXT("Vehicle remains present in genealogy"), Unit);
        if (!Unit || Unit->Stage == ELBOneFactoryVehicleStage::Dispatched) break;

        if (ULBOneFactoryProductionFlowLibrary::IsQualityGate(Unit->Stage))
        {
            const FName QualityEvidence(*FString::Printf(
                TEXT("QUALITY-%04d"), EvidenceSerial++));
            TestTrue(TEXT("Every inspection receives unique passing evidence"),
                Authority->SubmitQualityResult(UnitId,
                    ELBOneFactoryVehicleQualityState::Passed,
                    QualityEvidence, Reason));
        }
        const FName Station(*FString::Printf(TEXT("STATION-%04d"), EvidenceSerial));
        const FName Evidence(*FString::Printf(TEXT("PROCESS-%04d"), EvidenceSerial++));
        TestTrue(TEXT("Vehicle advances only through the canonical next stage"),
            Authority->AdvanceVehicle(UnitId, Station, Evidence, Reason));
    }

    const FLBOneFactoryProductionLedgerState Result = Authority->CaptureLedger();
    TestEqual(TEXT("Exactly one vehicle record"), Result.Units.Num(), 1);
    TestEqual(TEXT("Exactly one completed vehicle"), Result.CompletedVehicleCount, 1);
    TestEqual(TEXT("Exactly one dispatched vehicle"), Result.DispatchedVehicleCount, 1);
    TestEqual(TEXT("No active WIP after dispatch"), Authority->GetActiveWIPCount(), 0);
    TestTrue(TEXT("Dispatched unit retains complete material and process genealogy"),
        Result.Units[0].SourceMaterialUnitIds.Num() == 1
        && Result.Units[0].SourceMaterialUnitIds[0] == TEXT("COIL-LOT-0001")
        && Result.Units[0].RequiredPanelTypeIds.Num() == 11
        && Result.Units[0].PressedPanelTypeIds
            == Result.Units[0].RequiredPanelTypeIds
        && Result.Units[0].EvidenceIds.Num() == 33
        && Result.Units[0].bCompleted && Result.Units[0].bDispatched);
    TestTrue(TEXT("Final ledger validates"),
        ULBOneFactoryProductionFlowLibrary::ValidateLedger(Result, Reason));
    DestroyWorld(World);
    return true;
}

IMPLEMENT_SIMPLE_AUTOMATION_TEST(FLBOneFactoryRegisteredProgrammeOrderTest,
    "LineBoss.OneFactory.ProductionFlow.RegisteredProgrammeSeedsItsOwnPanelBOM",
    EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)

bool FLBOneFactoryRegisteredProgrammeOrderTest::RunTest(const FString& Parameters)
{
    using namespace LBOneFactoryProductionFlowTestsPrivate;
    const FName ProgrammeId(TEXT("NORTHSTAR_ORDER_DEVELOPMENT"));
    LBVehicleModelCatalog::UnregisterDevelopmentRecipe(ProgrammeId);

    FLBVehicleModelRecipe Programme;
    Programme.ModelId = ProgrammeId;
    Programme.DisplayName = TEXT("Northstar order-path development programme");
    Programme.RecipeRevisionId = TEXT("NORTHSTAR_ORDER_RECIPE_V001");
    Programme.PaintRouteProfileId = TEXT("PAINT_ROUTE_EDCOAT_VISIBLE_V001");
    Programme.GeometryAuthorityId = TEXT("NorthstarOrderGeometry_V001");
    Programme.PanelGeometryAuthorityId = TEXT("NorthstarOrderPanels_V001");
    Programme.BaseKitTypeId = TEXT("NORTHSTAR_ORDER_DEVELOPMENT_BIW_BASE_KIT");
    Programme.bDevelopmentVisual = true;
    Programme.bPanelGeometryValidated = true;
    Programme.DefaultRevenuePence = 2500000;
    Programme.RequiredPanels = {
        { TEXT("NORTHSTAR_ORDER_HOOD"), TEXT("Northstar order hood"), ELBPanelHandedness::None,
            10, FVector(160.0f, 140.0f, 20.0f), NAME_None },
        { TEXT("NORTHSTAR_ORDER_TAILGATE"), TEXT("Northstar order tailgate"), ELBPanelHandedness::None,
            10, FVector(145.0f, 22.0f, 108.0f), NAME_None }
    };

    FString Reason;
    if (!TestTrue(TEXT("programme registration succeeds before order creation"),
        LBVehicleModelCatalog::RegisterDevelopmentRecipe(Programme, Reason)))
    {
        return false;
    }

    UWorld* World = MakeWorld(TEXT("LBOneFactoryRegisteredProgrammeOrderTest"));
    ALBOneFactoryProductionFlowAuthority* Authority = MakeAuthority(World);
    if (!TestNotNull(TEXT("production authority exists"), Authority))
    {
        LBVehicleModelCatalog::UnregisterDevelopmentRecipe(ProgrammeId);
        DestroyWorld(World);
        return false;
    }

    Authority->SetDepartmentCommissioned(ELBOneFactoryDepartment::Press, true, Reason);
    FName UnitId;
    const bool bCreated = Authority->CreateVehicleOrder(TEXT("NORTHSTAR-ORDER-0001"), ProgrammeId,
        TEXT("PAINT-NORTHSTAR-DEV"), TEXT("NORTHSTAR-DEV"), TEXT("COIL-NORTHSTAR-0001"),
        TEXT("PRESS-INBOUND"), UnitId, Reason);
    TestTrue(TEXT("a registered additional programme can enter the shared production line"), bCreated);
    const FLBOneFactoryProductionLedgerState Ledger = Authority->CaptureLedger();
    const FLBOneFactoryVehicleUnitState* Unit = Ledger.Units.FindByPredicate([UnitId](const FLBOneFactoryVehicleUnitState& Row)
        { return Row.UnitId == UnitId; });
    TestNotNull(TEXT("the additional programme creates a unit"), Unit);
    if (Unit)
    {
        TestEqual(TEXT("the unit retains the programme identity"), Unit->VehicleModelId, ProgrammeId);
        TestEqual(TEXT("the unit freezes the programme recipe revision at order entry"),
            Unit->VehicleRecipeRevisionId, Programme.RecipeRevisionId);
        TestEqual(TEXT("the unit captures exactly the new programme BOM"), Unit->RequiredPanelTypeIds.Num(), 2);
        TestTrue(TEXT("the captured BOM contains the programme hood"),
            Unit->RequiredPanelTypeIds.Contains(TEXT("NORTHSTAR_ORDER_HOOD")));
        TestTrue(TEXT("the captured BOM contains the programme tailgate"),
            Unit->RequiredPanelTypeIds.Contains(TEXT("NORTHSTAR_ORDER_TAILGATE")));
    }

    // A later art/BOM revision is a new programme authority, not permission to
    // mutate vehicles that already entered the factory under V001.
    FLBVehicleModelRecipe RevisedProgramme = Programme;
    RevisedProgramme.RecipeRevisionId = TEXT("NORTHSTAR_ORDER_RECIPE_V002");
    RevisedProgramme.RequiredPanels = {
        { TEXT("NORTHSTAR_ORDER_V002_HOOD"), TEXT("Northstar revised hood"),
            ELBPanelHandedness::None, 10, FVector(160.0f, 140.0f, 20.0f), NAME_None }
    };
    TestTrue(TEXT("the original programme can be replaced by a later recipe revision"),
        LBVehicleModelCatalog::UnregisterDevelopmentRecipe(ProgrammeId));
    TestTrue(TEXT("the later recipe revision registers under the stable model ID"),
        LBVehicleModelCatalog::RegisterDevelopmentRecipe(RevisedProgramme, Reason));
    TestTrue(TEXT("the V001 vehicle ledger remains valid after the catalogue advances"),
        ULBOneFactoryProductionFlowLibrary::ValidateLedger(Ledger, Reason));

    LBVehicleModelCatalog::UnregisterDevelopmentRecipe(ProgrammeId);
    DestroyWorld(World);
    return bCreated && Unit != nullptr;
}

IMPLEMENT_SIMPLE_AUTOMATION_TEST(FLBOneFactoryProductionRuntimeGateTest,
    "LineBoss.OneFactory.ProductionFlow.CommissionPauseFaultOutputAndQualityGates",
    EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)

bool FLBOneFactoryProductionRuntimeGateTest::RunTest(const FString& Parameters)
{
    using namespace LBOneFactoryProductionFlowTestsPrivate;
    UWorld* World = MakeWorld(TEXT("LBOneFactoryProductionRuntimeGateTest"));
    ALBOneFactoryProductionFlowAuthority* Authority = MakeAuthority(World);
    TestNotNull(TEXT("Production authority exists"), Authority);
    if (!Authority) { DestroyWorld(World); return false; }
    FString Reason;
    FName UnitId;
    TestFalse(TEXT("Uncommissioned Press rejects orders"),
        Authority->CreateVehicleOrder(TEXT("ORDER-GATE"), TEXT("CAIRNWELL_2040"),
            TEXT("PAINT-RED"), TEXT("SIGNAL-RED"), TEXT("COIL-GATE"),
            TEXT("PRESS-INBOUND"), UnitId, Reason));

    Authority->SetDepartmentCommissioned(ELBOneFactoryDepartment::Press, true, Reason);
    TestTrue(TEXT("Commissioned Press accepts order"),
        Authority->CreateVehicleOrder(TEXT("ORDER-GATE"), TEXT("CAIRNWELL_2040"),
            TEXT("PAINT-RED"), TEXT("SIGNAL-RED"), TEXT("COIL-GATE"),
            TEXT("PRESS-INBOUND"), UnitId, Reason));
    Authority->SetLinePaused(true, Reason);
    const FLBOneFactoryProductionLedgerState Paused = Authority->CaptureLedger();
    TestFalse(TEXT("Pause blocks processing"),
        Authority->AdvanceVehicle(UnitId, TEXT("PRESS-BLANK"), TEXT("EV-PAUSE"), Reason));
    TestTrue(TEXT("Pause rejection preserves exact ledger"),
        Authority->CaptureLedger().Units[0].Stage == Paused.Units[0].Stage
        && Authority->CaptureLedger().Revision == Paused.Revision);

    Authority->SetLinePaused(false, Reason);
    Authority->SetDepartmentFaulted(ELBOneFactoryDepartment::Press, true, Reason);
    TestFalse(TEXT("Fault blocks processing"),
        Authority->AdvanceVehicle(UnitId, TEXT("PRESS-BLANK"), TEXT("EV-FAULT"), Reason));
    Authority->SetDepartmentFaulted(ELBOneFactoryDepartment::Press, false, Reason);
    Authority->SetDepartmentOutputBlocked(ELBOneFactoryDepartment::Press, true, Reason);
    TestFalse(TEXT("Output block blocks processing"),
        Authority->AdvanceVehicle(UnitId, TEXT("PRESS-BLANK"), TEXT("EV-BLOCK"), Reason));
    Authority->SetDepartmentOutputBlocked(ELBOneFactoryDepartment::Press, false, Reason);
    TestTrue(TEXT("Cleared gates allow processing"),
        Authority->AdvanceVehicle(UnitId, TEXT("PRESS-BLANK"), TEXT("EV-CLEAR"), Reason));
    TestFalse(TEXT("Active Press WIP prevents decommission"),
        Authority->SetDepartmentCommissioned(ELBOneFactoryDepartment::Press,
            false, Reason));

    DestroyWorld(World);
    return true;
}

IMPLEMENT_SIMPLE_AUTOMATION_TEST(FLBOneFactoryProductionSaveRollbackTest,
    "LineBoss.OneFactory.ProductionFlow.SaveRestoreNoDuplicateWIPAndRework",
    EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)

bool FLBOneFactoryProductionSaveRollbackTest::RunTest(const FString& Parameters)
{
    using namespace LBOneFactoryProductionFlowTestsPrivate;
    UWorld* World = MakeWorld(TEXT("LBOneFactoryProductionSaveRollbackTest"));
    ALBOneFactoryProductionFlowAuthority* Source = MakeAuthority(World);
    ALBOneFactoryProductionFlowAuthority* Restored = MakeAuthority(World);
    TestTrue(TEXT("Two authorities exist for memory save/restore proof"),
        Source && Restored);
    if (!Source || !Restored) { DestroyWorld(World); return false; }
    FString Reason;
    CommissionAll(*Source, Reason);
    FName UnitId;
    Source->CreateVehicleOrder(TEXT("ORDER-SAVE"), TEXT("CAIRNWELL_2040"),
        TEXT("PAINT-AURORA"), TEXT("AURORA-BLUE"), TEXT("COIL-SAVE"),
        TEXT("PRESS-INBOUND"), UnitId, Reason);
    for (int32 Step = 0; Step < 7; ++Step)
    {
        if (Source->CaptureLedger().Units[0].Stage
            == ELBOneFactoryVehicleStage::PressPanelInspection)
        {
            TestTrue(TEXT("Press panel inspection is passed before Body transfer"),
                Source->SubmitQualityResult(UnitId,
                    ELBOneFactoryVehicleQualityState::Passed,
                    TEXT("PRESS-PANEL-QUALITY-PASS"), Reason));
        }
        Source->AdvanceVehicle(UnitId,
            FName(*FString::Printf(TEXT("SAVE-STATION-%02d"), Step)),
            FName(*FString::Printf(TEXT("SAVE-EVIDENCE-%02d"), Step)), Reason);
    }
    TestTrue(TEXT("Unit reaches Body quality gate"),
        Source->CaptureLedger().Units[0].Stage
            == ELBOneFactoryVehicleStage::BodyQualityInspection);
    TestTrue(TEXT("Quality requests rework"),
        Source->SubmitQualityResult(UnitId,
            ELBOneFactoryVehicleQualityState::ReworkRequired,
            TEXT("BODY-QUALITY-REWORK"), Reason));
    TestFalse(TEXT("Rework unit cannot advance"),
        Source->AdvanceVehicle(UnitId, TEXT("PAINT-WASH"),
            TEXT("INVALID-ADVANCE"), Reason));
    TestTrue(TEXT("Rework completion resets inspection"),
        Source->ResetQualityAfterRework(UnitId, TEXT("BODY-REWORK-DONE"), Reason));

    const FLBOneFactoryProductionLedgerState Saved = Source->CaptureLedger();
    TestTrue(TEXT("Valid WIP ledger restores atomically"),
        Restored->RestoreLedger(Saved, Reason));
    TestEqual(TEXT("Restore keeps exactly one logical WIP"),
        Restored->GetActiveWIPCount(), 1);

    FLBOneFactoryProductionLedgerState Invalid = Saved;
    const FLBOneFactoryVehicleUnitState DuplicateUnit = Invalid.Units[0];
    Invalid.Units.Add(DuplicateUnit);
    const FLBOneFactoryProductionLedgerState BeforeRejected = Restored->CaptureLedger();
    TestFalse(TEXT("Duplicate WIP identity rejects before mutation"),
        Restored->RestoreLedger(Invalid, Reason));
    const FLBOneFactoryProductionLedgerState AfterRejected = Restored->CaptureLedger();
    TestTrue(TEXT("Rejected restore preserves exact live ledger"),
        AfterRejected.Revision == BeforeRejected.Revision
        && AfterRejected.Units.Num() == 1
        && AfterRejected.Units[0].UnitId == BeforeRejected.Units[0].UnitId
        && AfterRejected.Units[0].EvidenceIds == BeforeRejected.Units[0].EvidenceIds);

    DestroyWorld(World);
    return true;
}

IMPLEMENT_SIMPLE_AUTOMATION_TEST(FLBOneFactoryProductionRuntimeCursorContractTest,
    "LineBoss.OneFactory.ProductionFlow.RuntimeCursorPersistenceContract",
    EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)

bool FLBOneFactoryProductionRuntimeCursorContractTest::RunTest(
    const FString& Parameters)
{
    (void)Parameters;
    FLBOneFactoryProductionLedgerState Ledger =
        ULBOneFactoryProductionFlowLibrary::MakeEmptyLedger();
    FLBOneFactoryVehicleUnitState Unit;
    Unit.UnitId = TEXT("CAIRNWELL_2040-000001");
    Unit.BuildOrderId = TEXT("ORDER-RUNTIME-CURSOR");
    Unit.VehicleModelId = TEXT("CAIRNWELL_2040");
    Unit.PaintProgrammeId = TEXT("PAINT_CAIRNWELL_TEAL");
    Unit.PaintColourId = TEXT("CAIRNWELL_TEAL");
    Unit.CurrentStationId = TEXT("OF_PRESS_INBOUND_RECEIVING");
    Unit.SourceMaterialUnitIds.Add(TEXT("COIL-RUNTIME-CURSOR"));
    Unit.RuntimeStationCursor = 0;
    Unit.RuntimeCompletedStationCount = 0;
    Unit.RuntimeTotalStationCount = 57;
    Unit.RuntimeCycleElapsedSeconds = 4.0f;
    Unit.RuntimeCycleDurationSeconds = 8.0f;
    Unit.RuntimeTopologyId = TEXT("OF_RUNTIME_TOPOLOGY_DEADBEEF");
    Unit.RuntimeCurrentAssignmentId = TEXT("PRESS_ROLE_00");
    Unit.bRuntimeStarted = true;
    Ledger.Units.Add(Unit);
    Ledger.NextVehicleSerial = 2;

    FString Reason;
    TestTrue(TEXT("A complete mid-cycle runtime cursor is ledger-valid"),
        ULBOneFactoryProductionFlowLibrary::ValidateLedger(Ledger, Reason));
    Ledger.Units[0].RuntimeCompletedStationCount = 1;
    TestFalse(TEXT("Cursor/completed-count disagreement fails closed"),
        ULBOneFactoryProductionFlowLibrary::ValidateLedger(Ledger, Reason));
    Ledger.Units[0].RuntimeCompletedStationCount = 0;
    Ledger.Units[0].RuntimeCycleElapsedSeconds = 9.0f;
    TestFalse(TEXT("Elapsed time beyond the persisted cycle fails closed"),
        ULBOneFactoryProductionFlowLibrary::ValidateLedger(Ledger, Reason));
    return true;
}

#endif
