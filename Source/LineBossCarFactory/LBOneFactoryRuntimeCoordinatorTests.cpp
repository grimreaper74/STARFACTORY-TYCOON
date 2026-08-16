#include "LBOneFactoryRuntimeCoordinator.h"

#if WITH_DEV_AUTOMATION_TESTS

#include "Engine/World.h"
#include "LBOneFactorySaveGame.h"
#include "Misc/AutomationTest.h"

namespace LBOneFactoryRuntimeCoordinatorTestsPrivate
{
    struct FFactoryFixture
    {
        UWorld* World = nullptr;
        ALBOneFactoryPressStarterLayoutAuthority* Press = nullptr;
        ALBOneFactoryBodyWeldStarterLayoutAuthority* Body = nullptr;
        ALBOneFactoryPaintStarterLayoutAuthority* Paint = nullptr;
        ALBOneFactoryAssemblyStarterLayoutAuthority* Assembly = nullptr;
        ALBOneFactoryProductionFlowAuthority* Production = nullptr;
        ALBOneFactoryRuntimeCoordinator* Coordinator = nullptr;

        bool Create(const TCHAR* WorldName, FString& OutReason,
            const bool bMoveConfigurableAssemblyOperation = false)
        {
            World = UWorld::CreateWorld(EWorldType::Game, false,
                FName(WorldName));
            if (!World)
            {
                OutReason = TEXT("RUNTIME TEST WORLD FAILED");
                return false;
            }
            Press = World->SpawnActor<
                ALBOneFactoryPressStarterLayoutAuthority>();
            Body = World->SpawnActor<
                ALBOneFactoryBodyWeldStarterLayoutAuthority>();
            Paint = World->SpawnActor<
                ALBOneFactoryPaintStarterLayoutAuthority>();
            Assembly = World->SpawnActor<
                ALBOneFactoryAssemblyStarterLayoutAuthority>();
            Production = World->SpawnActor<
                ALBOneFactoryProductionFlowAuthority>();
            Coordinator = World->SpawnActor<ALBOneFactoryRuntimeCoordinator>();
            if (!Press || !Body || !Paint || !Assembly || !Production
                || !Coordinator)
            {
                OutReason = TEXT("RUNTIME TEST AUTHORITIES FAILED");
                return false;
            }
            Coordinator->bAdvanceStartedVehiclesOnActorTick = false;
            if (bMoveConfigurableAssemblyOperation
                && !Assembly->AssignOperation(
                    ELBOneFactoryAssemblyOperation::Closures,
                    LBOneFactoryAssemblyStarterIds::Station(9), OutReason))
                return false;
            if (!Press->Commission(OutReason)
                || !Body->Commission(OutReason)
                || !Paint->Commission(OutReason)
                || !Assembly->Commission(OutReason))
                return false;
            for (int32 DepartmentIndex = 0; DepartmentIndex < 4;
                ++DepartmentIndex)
            {
                if (!Production->SetDepartmentCommissioned(
                        static_cast<ELBOneFactoryDepartment>(DepartmentIndex),
                        true, OutReason))
                    return false;
            }
            return Coordinator->ValidateRuntimeFactory(OutReason);
        }

        bool CreateAndStart(FName BuildOrderId, FName& OutUnitId,
            FString& OutReason)
        {
            const FLBOneFactoryPaintStarterLayoutState PaintState =
                Paint->CaptureLayout();
            if (!Coordinator->CreateRuntimeVehicleOrder(BuildOrderId,
                    Body->CaptureLayout().VehicleModelId,
                    PaintState.PaintProgrammeId, TEXT("CAIRNWELL_TEAL"),
                    FName(*FString::Printf(TEXT("COIL_%s"),
                        *BuildOrderId.ToString())), OutUnitId, OutReason))
                return false;
            return Coordinator->StartVehicle(OutUnitId, OutReason);
        }

        int32 CountReservations() const
        {
            int32 Count = 0;
            for (const FLBOneFactoryPressStarterStationState& Station :
                Press->CaptureLayout().Stations)
                Count += Station.ActiveOrReservedUnitIds.Num();
            for (const FLBOneFactoryBodyWeldStationState& Station :
                Body->CaptureLayout().Stations)
                Count += Station.ActiveOrReservedUnitIds.Num();
            for (const FLBOneFactoryPaintStarterStationState& Station :
                Paint->CaptureLayout().Stations)
                Count += Station.ActiveOrReservedUnitIds.Num();
            for (const FLBOneFactoryAssemblyStationState& Station :
                Assembly->CaptureLayout().Stations)
                Count += Station.ActiveOrReservedUnitIds.Num();
            return Count;
        }

        void Destroy()
        {
            if (World) World->DestroyWorld(false);
            *this = FFactoryFixture();
        }
    };
}

IMPLEMENT_SIMPLE_AUTOMATION_TEST(FLBOneFactoryRuntimeFullTraversalTest,
    "LineBoss.OneFactory.RuntimeCoordinator.Full57StationConfiguredTraversalQualityReworkDispatch",
    EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)

bool FLBOneFactoryRuntimeFullTraversalTest::RunTest(
    const FString& Parameters)
{
    (void)Parameters;
    using namespace LBOneFactoryRuntimeCoordinatorTestsPrivate;
    FString Reason;
    FFactoryFixture Fixture;
    if (!TestTrue(TEXT("Configured runtime fixture commissions"),
            Fixture.Create(TEXT("LBOneFactoryRuntimeFullTraversalTest"),
                Reason, true)))
    {
        AddError(Reason);
        Fixture.Destroy();
        return false;
    }

    TArray<FLBOneFactoryRuntimeStationStep> Route;
    FName TopologyId;
    TestTrue(TEXT("Configured physical route resolves"),
        Fixture.Coordinator->GetConfiguredStationRoute(
            Route, TopologyId, Reason));
    TestEqual(TEXT("Press 7 + Body 18 + Paint 8 + Assembly 24"),
        Route.Num(), ALBOneFactoryRuntimeCoordinator::RequiredPhysicalStationCount);
    TestTrue(TEXT("Route has a persisted topology identity"),
        !TopologyId.IsNone());
    TestEqual(TEXT("Body begins after seven Press positions"),
        Route[7].StationId, LBOneFactoryBodyWeldStarterIds::Station(1));
    TestEqual(TEXT("Paint begins after 25 physical positions"),
        Route[25].StationId, LBOneFactoryPaintStarterIds::Station(
            ELBOneFactoryPaintStarterRole::BodySkidReceiving));
    TestEqual(TEXT("Assembly begins after 33 physical positions"),
        Route[33].StationId, LBOneFactoryAssemblyStarterIds::Station(1));
    TestTrue(TEXT("Reassigned Assembly source remains a physical pass-through"),
        Route[40].ConfiguredWorkIds.Contains(
            FName(TEXT("ASSEMBLY_PASS_THROUGH"))));
    TestTrue(TEXT("Target station honours the reassigned Closures operation"),
        Route[41].ConfiguredWorkIds.Contains(
            FName(TEXT("ASSEMBLY_OPERATION_07")))
        && Route[41].ConfiguredWorkIds.Contains(
            FName(TEXT("ASSEMBLY_OPERATION_08"))));

    FName UnitId;
    TestTrue(TEXT("One configured vehicle is created and started"),
        Fixture.CreateAndStart(TEXT("ORDER_RUNTIME_FULL"), UnitId, Reason));
    TestEqual(TEXT("Creation owns exactly one logical reservation"),
        Fixture.CountReservations(), 1);

    TSet<FName> VisitedStations;
    TSet<ELBOneFactoryVehicleStage> VisitedStages;
    TSet<ELBOneFactoryVehicleStage> QualityHoldStages;
    bool bBodyReworkProved = false;
    for (int32 Guard = 0; Guard < 160; ++Guard)
    {
        FLBOneFactoryRuntimeVehicleStatus Before;
        if (!TestTrue(TEXT("Runtime status remains coherent"),
                Fixture.Coordinator->GetVehicleRuntimeStatus(
                    UnitId, Before, Reason)))
        {
            AddError(Reason);
            break;
        }
        VisitedStages.Add(Before.Stage);
        if (!Before.bDispatched) VisitedStations.Add(Before.CurrentStationId);
        if (Before.bDispatched) break;

        if (!TestTrue(TEXT("A deterministic large tick completes at most one station"),
                Fixture.Coordinator->TickVehicle(UnitId, 1000.0f, Reason)))
        {
            AddError(Reason);
            break;
        }
        TestTrue(TEXT("Every live tick preserves exact-one WIP"),
            Fixture.Coordinator->ValidateRuntimeFactory(Reason));

        FLBOneFactoryRuntimeVehicleStatus After;
        Fixture.Coordinator->GetVehicleRuntimeStatus(UnitId, After, Reason);
        TestEqual(TEXT("Reservation count follows active/terminal state exactly"),
            Fixture.CountReservations(), After.bDispatched ? 0 : 1);
        if (After.bAwaitingQualityResult)
        {
            QualityHoldStages.Add(After.Stage);
            if (After.Stage
                    == ELBOneFactoryVehicleStage::BodyQualityInspection
                && !bBodyReworkProved)
            {
                TestTrue(TEXT("Body inspection can request rework"),
                    Fixture.Coordinator->SubmitRuntimeQualityResult(UnitId,
                        ELBOneFactoryVehicleQualityState::ReworkRequired,
                        TEXT("RUNTIME_BODY_REWORK_REQUEST"), Reason));
                const int32 HeldCursor = After.StationCursor;
                TestTrue(TEXT("Rework-required unit remains held"),
                    Fixture.Coordinator->TickVehicle(
                        UnitId, 1000.0f, Reason));
                FLBOneFactoryRuntimeVehicleStatus Held;
                Fixture.Coordinator->GetVehicleRuntimeStatus(
                    UnitId, Held, Reason);
                TestEqual(TEXT("Rework cannot bypass the quality station"),
                    Held.StationCursor, HeldCursor);
                TestTrue(TEXT("Rework completion resets the same inspection cycle"),
                    Fixture.Coordinator->CompleteRuntimeRework(UnitId,
                        TEXT("RUNTIME_BODY_REWORK_COMPLETE"), Reason));
                Fixture.Coordinator->GetVehicleRuntimeStatus(
                    UnitId, Held, Reason);
                TestEqual(TEXT("Reinspection restarts at zero deterministic time"),
                    Held.CycleElapsedSeconds, 0.0f);
                bBodyReworkProved = true;
            }
            else
            {
                const FName Evidence(*FString::Printf(
                    TEXT("RUNTIME_QUALITY_PASS_%d"),
                    static_cast<int32>(After.Stage)));
                TestTrue(TEXT("Completed inspection accepts unique passing evidence"),
                    Fixture.Coordinator->SubmitRuntimeQualityResult(UnitId,
                        ELBOneFactoryVehicleQualityState::Passed,
                        Evidence, Reason));
            }
        }
    }

    FLBOneFactoryRuntimeVehicleStatus Final;
    TestTrue(TEXT("Dispatched vehicle retains queryable runtime status"),
        Fixture.Coordinator->GetVehicleRuntimeStatus(UnitId, Final, Reason));
    VisitedStages.Add(Final.Stage);
    TestTrue(TEXT("The same UnitId reaches dispatch"), Final.bDispatched);
    TestEqual(TEXT("All 57 physical positions were visited exactly by identity"),
        VisitedStations.Num(),
        ALBOneFactoryRuntimeCoordinator::RequiredPhysicalStationCount);
    TestEqual(TEXT("Body, Paint and EOL all produced visible quality holds"),
        QualityHoldStages.Num(), 3);
    TestTrue(TEXT("Body rework path was exercised"), bBodyReworkProved);
    TestEqual(TEXT("All 18 coarse semantic stages remain observable"),
        VisitedStages.Num(), 18);
    TestEqual(TEXT("No station WIP remains after dispatch"),
        Fixture.CountReservations(), 0);

    const FLBOneFactoryProductionLedgerState Ledger =
        Fixture.Production->CaptureLedger();
    TestEqual(TEXT("Exactly one completed car"),
        Ledger.CompletedVehicleCount, 1);
    TestEqual(TEXT("Exactly one dispatched car"),
        Ledger.DispatchedVehicleCount, 1);
    TestEqual(TEXT("The saved cursor records all 57 completed positions"),
        Ledger.Units[0].RuntimeCompletedStationCount, 57);
    TestTrue(TEXT("Physical work, quality and dispatch evidence survives"),
        Ledger.Units[0].EvidenceIds.Num() >= 62);
    TestTrue(TEXT("Final runtime ledger validates"),
        ULBOneFactoryProductionFlowLibrary::ValidateLedger(Ledger, Reason));
    Fixture.Destroy();
    return true;
}

IMPLEMENT_SIMPLE_AUTOMATION_TEST(FLBOneFactoryRuntimeOperationalGatesTest,
    "LineBoss.OneFactory.RuntimeCoordinator.PauseFaultOutputAndExactAuthorityGates",
    EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)

bool FLBOneFactoryRuntimeOperationalGatesTest::RunTest(
    const FString& Parameters)
{
    (void)Parameters;
    using namespace LBOneFactoryRuntimeCoordinatorTestsPrivate;
    FString Reason;
    FFactoryFixture Fixture;
    if (!TestTrue(TEXT("Gate fixture commissions"),
            Fixture.Create(TEXT("LBOneFactoryRuntimeGateTest"), Reason)))
    {
        AddError(Reason);
        Fixture.Destroy();
        return false;
    }
    FName UnitId;
    TestTrue(TEXT("Gate unit starts"), Fixture.CreateAndStart(
        TEXT("ORDER_RUNTIME_GATES"), UnitId, Reason));
    TestTrue(TEXT("Initial partial cycle progresses"),
        Fixture.Coordinator->TickVehicle(UnitId, 1.0f, Reason));
    FLBOneFactoryRuntimeVehicleStatus Baseline;
    Fixture.Coordinator->GetVehicleRuntimeStatus(UnitId, Baseline, Reason);

    Fixture.Production->SetLinePaused(true, Reason);
    TestTrue(TEXT("Pause creates an operational hold, not corruption"),
        Fixture.Coordinator->TickVehicle(UnitId, 10.0f, Reason));
    FLBOneFactoryRuntimeVehicleStatus Held;
    Fixture.Coordinator->GetVehicleRuntimeStatus(UnitId, Held, Reason);
    TestEqual(TEXT("Pause freezes deterministic elapsed time"),
        Held.CycleElapsedSeconds, Baseline.CycleElapsedSeconds);
    Fixture.Production->SetLinePaused(false, Reason);

    Fixture.Production->SetDepartmentFaulted(
        ELBOneFactoryDepartment::Press, true, Reason);
    Fixture.Coordinator->TickVehicle(UnitId, 10.0f, Reason);
    Fixture.Coordinator->GetVehicleRuntimeStatus(UnitId, Held, Reason);
    TestEqual(TEXT("Department fault freezes deterministic elapsed time"),
        Held.CycleElapsedSeconds, Baseline.CycleElapsedSeconds);
    Fixture.Production->SetDepartmentFaulted(
        ELBOneFactoryDepartment::Press, false, Reason);

    Fixture.Production->SetDepartmentOutputBlocked(
        ELBOneFactoryDepartment::Press, true, Reason);
    TestTrue(TEXT("Output block allows cycle finish but prevents transfer"),
        Fixture.Coordinator->TickVehicle(UnitId, 1000.0f, Reason));
    Fixture.Coordinator->GetVehicleRuntimeStatus(UnitId, Held, Reason);
    TestEqual(TEXT("Output block keeps the source station cursor"),
        Held.StationCursor, 0);
    TestEqual(TEXT("Blocked output parks at complete cycle progress"),
        Held.NormalizedCycleProgress, 1.0f);
    Fixture.Production->SetDepartmentOutputBlocked(
        ELBOneFactoryDepartment::Press, false, Reason);
    TestTrue(TEXT("Cleared output transfers without duplicate reservation"),
        Fixture.Coordinator->TickVehicle(UnitId, 0.1f, Reason));
    Fixture.Coordinator->GetVehicleRuntimeStatus(UnitId, Held, Reason);
    TestEqual(TEXT("Unit advances to the second physical position"),
        Held.StationCursor, 1);
    TestEqual(TEXT("Transfer still owns exactly one reservation"),
        Fixture.CountReservations(), 1);

    ALBOneFactoryProductionFlowAuthority* Duplicate =
        Fixture.World->SpawnActor<ALBOneFactoryProductionFlowAuthority>();
    TestNotNull(TEXT("Duplicate authority fixture exists"), Duplicate);
    TestFalse(TEXT("Duplicate production authority fails closed"),
        Fixture.Coordinator->ValidateRuntimeFactory(Reason));
    TestTrue(TEXT("Exact authority rejection reports the duplicate count"),
        Reason.Contains(TEXT("EXACTLY ONE PRODUCTION"))
        && Reason.Contains(TEXT("FOUND 2")));
    Fixture.Destroy();

    UWorld* MissingWorld = UWorld::CreateWorld(EWorldType::Game, false,
        TEXT("LBOneFactoryRuntimeMissingAuthorityTest"));
    ALBOneFactoryRuntimeCoordinator* MissingCoordinator = MissingWorld
        ? MissingWorld->SpawnActor<ALBOneFactoryRuntimeCoordinator>() : nullptr;
    if (MissingWorld)
    {
        MissingWorld->SpawnActor<ALBOneFactoryPressStarterLayoutAuthority>();
        MissingWorld->SpawnActor<ALBOneFactoryBodyWeldStarterLayoutAuthority>();
        MissingWorld->SpawnActor<ALBOneFactoryPaintStarterLayoutAuthority>();
        MissingWorld->SpawnActor<ALBOneFactoryProductionFlowAuthority>();
    }
    TestNotNull(TEXT("Missing-authority coordinator exists"),
        MissingCoordinator);
    if (MissingCoordinator)
    {
        MissingCoordinator->bAdvanceStartedVehiclesOnActorTick = false;
        TestFalse(TEXT("Missing Assembly authority fails closed"),
            MissingCoordinator->ValidateRuntimeFactory(Reason));
        TestTrue(TEXT("Missing authority count is explicit"),
            Reason.Contains(TEXT("ASSEMBLY"))
            && Reason.Contains(TEXT("FOUND 0")));
    }
    if (MissingWorld) MissingWorld->DestroyWorld(false);
    return true;
}

IMPLEMENT_SIMPLE_AUTOMATION_TEST(FLBOneFactoryRuntimeSaveRestoreTest,
    "LineBoss.OneFactory.RuntimeCoordinator.MidCycleSaveRestoreTopologyDriftAndNoDuplicateWIP",
    EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)

bool FLBOneFactoryRuntimeSaveRestoreTest::RunTest(
    const FString& Parameters)
{
    (void)Parameters;
    using namespace LBOneFactoryRuntimeCoordinatorTestsPrivate;
    FString Reason;
    FFactoryFixture Source;
    if (!TestTrue(TEXT("Save source fixture commissions"),
            Source.Create(TEXT("LBOneFactoryRuntimeSaveSource"), Reason, true)))
    {
        AddError(Reason);
        Source.Destroy();
        return false;
    }
    FName UnitId;
    TestTrue(TEXT("Save source unit starts"), Source.CreateAndStart(
        TEXT("ORDER_RUNTIME_SAVE"), UnitId, Reason));
    TestTrue(TEXT("Source reaches a real mid-cycle cursor"),
        Source.Coordinator->TickVehicle(UnitId, 3.5f, Reason));

    FLBOneFactorySaveState Saved = ULBOneFactorySaveGame::MakeCanonicalEmptyState();
    Saved.PressLayout = Source.Press->CaptureLayout();
    Saved.BodyWeldLayout = Source.Body->CaptureLayout();
    Saved.PaintLayout = Source.Paint->CaptureLayout();
    Saved.AssemblyLayout = Source.Assembly->CaptureLayout();
    Saved.ProductionLedger = Source.Production->CaptureLedger();
    Saved.PayloadRevision = Saved.ProductionLedger.Revision;
    Saved.CapturedAtUtc = FDateTime::UtcNow();
    TestTrue(TEXT("Whole-factory save schema accepts the mid-cycle cursor"),
        ULBOneFactorySaveGame::ValidateState(Saved, Reason));
    TestEqual(TEXT("Saved factory has exactly one station reservation"),
        Source.CountReservations(), 1);
    Source.Destroy();

    FFactoryFixture Restored;
    if (!TestTrue(TEXT("Restore destination fixture commissions"),
            Restored.Create(TEXT("LBOneFactoryRuntimeSaveDestination"),
                Reason, true)))
    {
        AddError(Reason);
        Restored.Destroy();
        return false;
    }
    TestTrue(TEXT("Press WIP snapshot restores"),
        Restored.Press->RestoreLayout(Saved.PressLayout, Reason));
    TestTrue(TEXT("Body WIP snapshot restores"),
        Restored.Body->RestoreLayout(Saved.BodyWeldLayout, Reason));
    TestTrue(TEXT("Paint WIP snapshot restores"),
        Restored.Paint->RestoreLayout(Saved.PaintLayout, Reason));
    TestTrue(TEXT("Assembly WIP snapshot restores"),
        Restored.Assembly->RestoreLayout(Saved.AssemblyLayout, Reason));
    TestTrue(TEXT("Production cursor ledger restores"),
        Restored.Production->RestoreLedger(Saved.ProductionLedger, Reason));
    TestTrue(TEXT("Restored runtime topology and reservation validate"),
        Restored.Coordinator->ValidateRuntimeFactory(Reason));
    FLBOneFactoryRuntimeVehicleStatus Status;
    Restored.Coordinator->GetVehicleRuntimeStatus(UnitId, Status, Reason);
    TestEqual(TEXT("Exact mid-cycle elapsed time survives restore"),
        Status.CycleElapsedSeconds, 3.5f);
    TestEqual(TEXT("Restore has exactly one reservation"),
        Restored.CountReservations(), 1);

    const FLBOneFactoryBodyWeldLayoutState CleanBody =
        Restored.Body->CaptureLayout();
    FLBOneFactoryBodyWeldLayoutState DuplicatedBody = CleanBody;
    DuplicatedBody.Stations[0].ActiveOrReservedUnitIds.Add(UnitId);
    TestTrue(TEXT("An isolated department snapshot can expose cross-authority duplication"),
        Restored.Body->RestoreLayout(DuplicatedBody, Reason));
    TestFalse(TEXT("Runtime composite rejects duplicated cross-department WIP"),
        Restored.Coordinator->ValidateRuntimeFactory(Reason));
    TestTrue(TEXT("Duplicate WIP failure is explicit"),
        Reason.Contains(TEXT("RESERVED MORE THAN ONCE")));
    TestFalse(TEXT("Tick also fails closed while WIP is duplicated"),
        Restored.Coordinator->TickVehicle(UnitId, 1.0f, Reason));
    TestTrue(TEXT("Clean Body reservation snapshot restores"),
        Restored.Body->RestoreLayout(CleanBody, Reason));

    const FLBOneFactoryPaintStarterLayoutState CleanPaint =
        Restored.Paint->CaptureLayout();
    TestTrue(TEXT("Idle downstream Paint can be player-reprogrammed"),
        Restored.Paint->SetStationPaintProgramme(
            LBOneFactoryPaintStarterIds::Station(
                ELBOneFactoryPaintStarterRole::EDCoatLogicalProcess),
            ELBOneFactoryPaintColour::SignalRed, Reason));
    TestFalse(TEXT("Active saved UnitId fails closed on topology drift"),
        Restored.Coordinator->ValidateRuntimeFactory(Reason));
    TestTrue(TEXT("Topology drift is called out explicitly"),
        Reason.Contains(TEXT("TOPOLOGY DRIFTED")));
    TestTrue(TEXT("Original Paint topology can be transactionally restored"),
        Restored.Paint->RestoreLayout(CleanPaint, Reason));
    TestTrue(TEXT("Restored topology resumes as one coherent unit"),
        Restored.Coordinator->ValidateRuntimeFactory(Reason));
    TestTrue(TEXT("Saved partial cycle can finish and transfer"),
        Restored.Coordinator->TickVehicle(UnitId, 4.5f, Reason));
    Restored.Coordinator->GetVehicleRuntimeStatus(UnitId, Status, Reason);
    TestEqual(TEXT("Resumed UnitId reaches physical position two"),
        Status.StationCursor, 1);
    TestEqual(TEXT("Resume still has exactly one reservation"),
        Restored.CountReservations(), 1);
    Restored.Destroy();
    return true;
}

#endif
