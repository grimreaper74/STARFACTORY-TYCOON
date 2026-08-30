#include "LBOneFactoryRuntimeCoordinator.h"

#if WITH_DEV_AUTOMATION_TESTS

#include "Engine/World.h"
#include "Kismet/GameplayStatics.h"
#include "LBOneFactorySaveGame.h"
#include "Misc/AutomationTest.h"
#include "Misc/Crc.h"

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

    /** Reconstructs the exact topology id serialized before the V002 gate. */
    FName MakeLegacyV001TopologyId(
        TArray<FLBOneFactoryRuntimeStationStep> Route)
    {
        check(Route.IsValidIndex(5));
        Route[5].SemanticStage = ELBOneFactoryVehicleStage::Pressing;
        Route[5].bQualityGate = false;
        FString Contract(TEXT("ONEFACTORY_RUNTIME_ROUTE_V001"));
        for (const FLBOneFactoryRuntimeStationStep& Step : Route)
        {
            const FVector Location = Step.WorldTransform.GetLocation();
            const FRotator Rotation = Step.WorldTransform.Rotator();
            Contract += FString::Printf(
                TEXT("|%02d|%d|%s|%s|%.3f|%d|%d|%.3f,%.3f,%.3f|%.3f"),
                Step.RouteIndex, static_cast<int32>(Step.Department),
                *Step.StationId.ToString(), *Step.AssignmentId.ToString(),
                Step.NominalCycleSeconds,
                static_cast<int32>(Step.SemanticStage),
                Step.bQualityGate ? 1 : 0, Location.X, Location.Y, Location.Z,
                Rotation.Yaw);
        }
        return FName(*FString::Printf(TEXT("OF_RUNTIME_TOPOLOGY_V001_%08X"),
            FCrc::StrCrc32(*Contract)));
    }

    FName FrozenPersistedV001TopologyAlias()
    {
        return TEXT("OF_RUNTIME_TOPOLOGY_V001_C9F61F4B");
    }
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

    FLBOneFactoryVehicleContract Contract;
    Contract.ContractId = TEXT("CON_RUNTIME_FULL");
    Contract.VehicleModelId = Fixture.Body->CaptureLayout().VehicleModelId;
    Contract.Quantity = 1;
    Contract.PricePerVehiclePence = 3500000;
    TestTrue(TEXT("A matching contract is available before the runtime route starts"),
        Fixture.Production->AddVehicleContract(Contract, Reason));

    TArray<FLBOneFactoryRuntimeStationStep> Route;
    FName TopologyId;
    TestTrue(TEXT("Configured physical route resolves"),
        Fixture.Coordinator->GetConfiguredStationRoute(
            Route, TopologyId, Reason));
    TestEqual(TEXT("Press 7 + Body 18 + Paint 8 + Assembly 24"),
        Route.Num(), ALBOneFactoryRuntimeCoordinator::RequiredPhysicalStationCount);
    TestTrue(TEXT("Route has a persisted topology identity"),
        !TopologyId.IsNone());
    TestTrue(TEXT("An empty line selects the versioned V002 route profile"),
        TopologyId.ToString().StartsWith(TEXT("OF_RUNTIME_TOPOLOGY_V002_")));
    TestEqual(TEXT("The sixth Press position is panel inspection"),
        Route[5].StationId, LBOneFactoryPressStarterIds::PanelInspection());
    TestEqual(TEXT("Panel inspection has its own append-only semantic stage"),
        Route[5].SemanticStage,
        ELBOneFactoryVehicleStage::PressPanelInspection);
    TestTrue(TEXT("Panel inspection is a genuine quality-decision gate"),
        Route[5].bQualityGate);
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
    TestEqual(TEXT("Press, Body, Paint and EOL all produced visible quality holds"),
        QualityHoldStages.Num(), 4);
    TestTrue(TEXT("Body rework path was exercised"), bBodyReworkProved);
    TestEqual(TEXT("All 19 coarse semantic stages remain observable"),
        VisitedStages.Num(), 19);
    TestEqual(TEXT("No station WIP remains after dispatch"),
        Fixture.CountReservations(), 0);

    const FLBOneFactoryProductionLedgerState Ledger =
        Fixture.Production->CaptureLedger();
    TestEqual(TEXT("Exactly one completed car"),
        Ledger.CompletedVehicleCount, 1);
    TestEqual(TEXT("Exactly one dispatched car"),
        Ledger.DispatchedVehicleCount, 1);
    TestTrue(TEXT("Every automatic station completion accumulates serviceable fleet wear"),
        Ledger.FleetWear01 > 0.0);
    TestEqual(TEXT("Physical dispatch settles the matching contract"),
        Ledger.Contracts[0].DispatchedCount, 1);
    TestEqual(TEXT("Physical dispatch completes a one-car contract"),
        Ledger.Contracts[0].State, ELBOneFactoryContractState::Complete);
    TestEqual(TEXT("Dispatched unit records the settled contract identity"),
        Ledger.Units[0].FulfilledContractId, Contract.ContractId);
    TestEqual(TEXT("One press programme stamps the complete 11-panel model BOM"),
        Ledger.Units[0].PressedPanelTypeIds.Num(), 11);
    TestTrue(TEXT("The stamped BOM stays bound to the order recipe"),
        Ledger.Units[0].PressedPanelTypeIds == Ledger.Units[0].RequiredPanelTypeIds);
    TestEqual(TEXT("The saved cursor records all 57 completed positions"),
        Ledger.Units[0].RuntimeCompletedStationCount, 57);
    TestTrue(TEXT("Physical work, four quality gates and dispatch evidence survives"),
        Ledger.Units[0].EvidenceIds.Num() >= 63);
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
    if (Duplicate)
    {
        Duplicate->Destroy();
    }
    // The same closed-fail applies per department: a duplicate Body/Weld
    // authority must be rejected with its exact count, mirroring the
    // production-authority check above.
    ALBOneFactoryBodyWeldStarterLayoutAuthority* DuplicateWeld =
        Fixture.World->SpawnActor<ALBOneFactoryBodyWeldStarterLayoutAuthority>();
    TestNotNull(TEXT("Duplicate Body/Weld authority fixture exists"),
        DuplicateWeld);
    TestFalse(TEXT("Duplicate Body/Weld authority fails closed"),
        Fixture.Coordinator->ValidateRuntimeFactory(Reason));
    TestTrue(TEXT("Body/Weld duplicate rejection is explicit"),
        Reason.Contains(TEXT("BODY")) && Reason.Contains(TEXT("FOUND 2")));
    if (DuplicateWeld)
    {
        DuplicateWeld->Destroy();
    }
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

IMPLEMENT_SIMPLE_AUTOMATION_TEST(FLBOneFactoryRuntimeRouteProfileMigrationTest,
    "LineBoss.OneFactory.RuntimeCoordinator.V001SaveDrainsBeforeV002PressInspectionAdmission",
    EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)

bool FLBOneFactoryRuntimeRouteProfileMigrationTest::RunTest(
    const FString& Parameters)
{
    (void)Parameters;
    using namespace LBOneFactoryRuntimeCoordinatorTestsPrivate;
    FString Reason;
    FFactoryFixture Fixture;
    if (!TestTrue(TEXT("Route-profile fixture commissions"),
            Fixture.Create(TEXT("LBOneFactoryRuntimeRouteProfileMigration"),
                Reason)))
    {
        AddError(Reason);
        Fixture.Destroy();
        return false;
    }

    TArray<FLBOneFactoryRuntimeStationStep> CurrentRoute;
    FName CurrentTopologyId;
    TestTrue(TEXT("Current route resolves before legacy save construction"),
        Fixture.Coordinator->GetConfiguredStationRoute(
            CurrentRoute, CurrentTopologyId, Reason));
    const FName ComputedLegacyTopologyId =
        MakeLegacyV001TopologyId(CurrentRoute);
    const FName FrozenLegacyTopologyAlias =
        FrozenPersistedV001TopologyAlias();
    TestEqual(TEXT("Current relocated physical route computes its real V001 companion"),
        ComputedLegacyTopologyId,
        FName(TEXT("OF_RUNTIME_TOPOLOGY_V001_E287C325")));
    TestNotEqual(TEXT("Frozen persisted V001 identity is a migration alias, not the computed route"),
        FrozenLegacyTopologyAlias, ComputedLegacyTopologyId);
    TestTrue(TEXT("V001 and V002 topology identities are explicit and distinct"),
        ComputedLegacyTopologyId.ToString().StartsWith(
            TEXT("OF_RUNTIME_TOPOLOGY_V001_"))
        && CurrentTopologyId.ToString().StartsWith(
            TEXT("OF_RUNTIME_TOPOLOGY_V002_"))
        && ComputedLegacyTopologyId != CurrentTopologyId);

    FName LegacyUnitId;
    TestTrue(TEXT("A unit is created before simulating its serialized V001 identity"),
        Fixture.CreateAndStart(TEXT("ORDER_ROUTE_V001"), LegacyUnitId,
            Reason));
    FLBOneFactoryProductionLedgerState LegacyLedger =
        Fixture.Production->CaptureLedger();
    FLBOneFactoryVehicleUnitState* LegacyUnit =
        LegacyLedger.Units.FindByPredicate([LegacyUnitId](
            const FLBOneFactoryVehicleUnitState& Unit)
            { return Unit.UnitId == LegacyUnitId; });
    TestNotNull(TEXT("Serialized legacy unit exists"), LegacyUnit);
    if (!LegacyUnit)
    {
        Fixture.Destroy();
        return false;
    }
    LegacyUnit->RuntimeTopologyId = FrozenLegacyTopologyAlias;
    LegacyUnit->RouteProfileVersion =
        ULBOneFactoryProductionFlowLibrary::UnversionedRouteProfile;
    FLBOneFactoryProductionLedgerState UnknownLegacyLedger = LegacyLedger;
    UnknownLegacyLedger.Units[0].RuntimeTopologyId =
        TEXT("OF_RUNTIME_TOPOLOGY_V001_DEADBEEF");
    TestTrue(TEXT("structural ledger restore does not guess physical topology aliases"),
        Fixture.Production->RestoreLedger(UnknownLegacyLedger, Reason));
    TestFalse(TEXT("an unknown V001-looking topology remains fail-closed"),
        Fixture.Coordinator->ValidateRuntimeFactory(Reason));
    TestTrue(TEXT("unknown legacy topology rejection reports topology drift"),
        Reason.Contains(TEXT("TOPOLOGY DRIFTED")));
    TestTrue(TEXT("The frozen V001 alias restores under save schema V001"),
        Fixture.Production->RestoreLedger(LegacyLedger, Reason));

    FLBOneFactorySaveState LegacySave =
        ULBOneFactorySaveGame::MakeCanonicalEmptyState();
    LegacySave.PressLayout = Fixture.Press->CaptureLayout();
    LegacySave.BodyWeldLayout = Fixture.Body->CaptureLayout();
    LegacySave.PaintLayout = Fixture.Paint->CaptureLayout();
    LegacySave.AssemblyLayout = Fixture.Assembly->CaptureLayout();
    LegacySave.ProductionLedger = Fixture.Production->CaptureLedger();
    LegacySave.PayloadRevision = LegacySave.ProductionLedger.Revision;
    LegacySave.CapturedAtUtc = FDateTime::UtcNow();
    TestTrue(TEXT("An active V001 runtime save validates without schema rewrite"),
        ULBOneFactorySaveGame::ValidateState(LegacySave, Reason));

    ULBOneFactorySaveGame* SaveRoot = NewObject<ULBOneFactorySaveGame>();
    SaveRoot->FactoryState = LegacySave;
    TArray<uint8> SerializedSave;
    TestTrue(TEXT("V001 compatibility fixture serializes through USaveGame"),
        UGameplayStatics::SaveGameToMemory(SaveRoot, SerializedSave));
    ULBOneFactorySaveGame* LoadedSave = Cast<ULBOneFactorySaveGame>(
        UGameplayStatics::LoadGameFromMemory(SerializedSave));
    TestNotNull(TEXT("Serialized V001 fixture loads as the real save class"),
        LoadedSave);
    TestTrue(TEXT("Loaded V001 fixture retains a valid complete save state"),
        LoadedSave
        && ULBOneFactorySaveGame::ValidateState(
            LoadedSave->FactoryState, Reason));
    const FLBOneFactoryVehicleUnitState* LoadedLegacyUnit = LoadedSave
        ? LoadedSave->FactoryState.ProductionLedger.Units.FindByPredicate(
            [LegacyUnitId](const FLBOneFactoryVehicleUnitState& Unit)
            { return Unit.UnitId == LegacyUnitId; })
        : nullptr;
    TestTrue(TEXT("Old additive profile default and V001 topology survive serialization"),
        LoadedLegacyUnit
        && LoadedLegacyUnit->RouteProfileVersion ==
            ULBOneFactoryProductionFlowLibrary::UnversionedRouteProfile
        && LoadedLegacyUnit->RuntimeTopologyId ==
            FrozenLegacyTopologyAlias);
    TestTrue(TEXT("Coordinator selects V001 semantics for active restored WIP"),
        Fixture.Coordinator->ValidateRuntimeFactory(Reason));

    TArray<FLBOneFactoryRuntimeStationStep> SelectedLegacyRoute;
    FName SelectedLegacyTopologyId;
    TestTrue(TEXT("Active V001 WIP selects the exact legacy route"),
        Fixture.Coordinator->GetConfiguredStationRoute(
            SelectedLegacyRoute, SelectedLegacyTopologyId, Reason));
    TestEqual(TEXT("Selected V001 topology remains the computed current companion"),
        SelectedLegacyTopologyId, ComputedLegacyTopologyId);
    TestEqual(TEXT("V001 inspection position retains its historic Pressing stage"),
        SelectedLegacyRoute[5].SemanticStage,
        ELBOneFactoryVehicleStage::Pressing);
    TestFalse(TEXT("V001 inspection position is not retroactively made a gate"),
        SelectedLegacyRoute[5].bQualityGate);

    const FLBOneFactoryPaintStarterLayoutState PaintState =
        Fixture.Paint->CaptureLayout();
    FName BlockedUnitId;
    TestFalse(TEXT("New admissions cannot prolong an active V001 route"),
        Fixture.Coordinator->CreateRuntimeVehicleOrder(
            TEXT("ORDER_BLOCKED_DURING_V001"),
            Fixture.Body->CaptureLayout().VehicleModelId,
            PaintState.PaintProgrammeId, TEXT("CAIRNWELL_TEAL"),
            TEXT("COIL_BLOCKED_DURING_V001"), BlockedUnitId, Reason));
    TestTrue(TEXT("V001 admission fence explains the required drain"),
        Reason.Contains(TEXT("V001 ROUTE WIP MUST DRAIN")));
    FName AutoBlockedUnitId;
    TestTrue(TEXT("Automatic dispatch treats the V001 drain as a soft hold"),
        Fixture.Coordinator->DispatchNextOpenContract(
            AutoBlockedUnitId, Reason));
    TestTrue(TEXT("Automatic dispatch admits nothing while V001 drains"),
        AutoBlockedUnitId.IsNone()
        && Reason.Contains(TEXT("HOLDS NEW ADMISSION")));

    const int32 PreMigrationRevision =
        Fixture.Production->CaptureLedger().Revision;
    TestTrue(TEXT("first successful aliased V001 tick commits atomically"),
        Fixture.Coordinator->TickVehicle(LegacyUnitId, 1.0f, Reason));
    const FLBOneFactoryProductionLedgerState MigratedLegacyLedger =
        Fixture.Production->CaptureLedger();
    const FLBOneFactoryVehicleUnitState* MigratedLegacyUnit =
        MigratedLegacyLedger.Units.FindByPredicate([LegacyUnitId](
            const FLBOneFactoryVehicleUnitState& Unit)
            { return Unit.UnitId == LegacyUnitId; });
    TestTrue(TEXT("first successful tick restamps only to the computed V001 companion"),
        MigratedLegacyUnit
        && MigratedLegacyUnit->RuntimeTopologyId == ComputedLegacyTopologyId
        && MigratedLegacyUnit->RouteProfileVersion ==
            ULBOneFactoryProductionFlowLibrary::LegacyRouteProfileV001
        && MigratedLegacyLedger.Revision == PreMigrationRevision + 1);
    TestTrue(TEXT("restamped V001 runtime remains composite-valid"),
        Fixture.Coordinator->ValidateRuntimeFactory(Reason));

    bool bLegacyDispatched = false;
    int32 QualityEvidenceSerial = 0;
    for (int32 Guard = 0; Guard < 180; ++Guard)
    {
        FLBOneFactoryRuntimeVehicleStatus Before;
        if (!Fixture.Coordinator->GetVehicleRuntimeStatus(
                LegacyUnitId, Before, Reason))
        {
            AddError(Reason);
            break;
        }
        if (Before.bDispatched)
        {
            bLegacyDispatched = true;
            break;
        }
        if (!Fixture.Coordinator->TickVehicle(
                LegacyUnitId, 1000.0f, Reason))
        {
            AddError(Reason);
            break;
        }
        FLBOneFactoryRuntimeVehicleStatus After;
        if (!Fixture.Coordinator->GetVehicleRuntimeStatus(
                LegacyUnitId, After, Reason))
        {
            AddError(Reason);
            break;
        }
        if (After.bAwaitingQualityResult)
        {
            const FName Evidence(*FString::Printf(
                TEXT("V001_DRAIN_QUALITY_PASS_%02d"),
                ++QualityEvidenceSerial));
            if (!Fixture.Coordinator->SubmitRuntimeQualityResult(
                    LegacyUnitId,
                    ELBOneFactoryVehicleQualityState::Passed,
                    Evidence, Reason))
            {
                AddError(Reason);
                break;
            }
        }
    }
    TestTrue(TEXT("The exact V001 unit drains and dispatches without genealogy loss"),
        bLegacyDispatched);
    const FLBOneFactoryProductionLedgerState DrainedLegacyLedger =
        Fixture.Production->CaptureLedger();
    const FLBOneFactoryVehicleUnitState* DrainedLegacyUnit =
        DrainedLegacyLedger.Units.FindByPredicate([LegacyUnitId](
            const FLBOneFactoryVehicleUnitState& Unit)
            { return Unit.UnitId == LegacyUnitId; });
    TestTrue(TEXT("first committed V001 runtime mutation persists its profile"),
        DrainedLegacyUnit && DrainedLegacyUnit->RouteProfileVersion ==
            ULBOneFactoryProductionFlowLibrary::LegacyRouteProfileV001
        && DrainedLegacyUnit->RuntimeTopologyId == ComputedLegacyTopologyId);
    TestTrue(TEXT("Terminal V001 genealogy validates after line activation moves to V002"),
        Fixture.Coordinator->ValidateRuntimeFactory(Reason));

    FLBOneFactoryProductionLedgerState TerminalAliasLedger =
        Fixture.Production->CaptureLedger();
    FLBOneFactoryVehicleUnitState* TerminalAliasUnit =
        TerminalAliasLedger.Units.FindByPredicate([LegacyUnitId](
            const FLBOneFactoryVehicleUnitState& Unit)
            { return Unit.UnitId == LegacyUnitId; });
    TestNotNull(TEXT("terminal V001 unit exists for frozen-alias compatibility"),
        TerminalAliasUnit);
    if (TerminalAliasUnit)
    {
        TerminalAliasUnit->RuntimeTopologyId = FrozenLegacyTopologyAlias;
    }
    TestTrue(TEXT("terminal frozen V001 alias restores without genealogy loss"),
        TerminalAliasUnit
        && Fixture.Production->RestoreLedger(TerminalAliasLedger, Reason));
    TestTrue(TEXT("terminal frozen V001 alias validates beside the current route"),
        Fixture.Coordinator->ValidateRuntimeFactory(Reason));

    TArray<FLBOneFactoryRuntimeStationStep> ActivatedRoute;
    FName ActivatedTopologyId;
    TestTrue(TEXT("An empty drained line activates the V002 route"),
        Fixture.Coordinator->GetConfiguredStationRoute(
            ActivatedRoute, ActivatedTopologyId, Reason));
    TestEqual(TEXT("Activated topology returns to the original V002 identity"),
        ActivatedTopologyId, CurrentTopologyId);
    TestEqual(TEXT("V002 panel inspection owns the new semantic stage"),
        ActivatedRoute[5].SemanticStage,
        ELBOneFactoryVehicleStage::PressPanelInspection);
    TestTrue(TEXT("V002 panel inspection now holds for a quality decision"),
        ActivatedRoute[5].bQualityGate);

    FName V002UnitId;
    TestTrue(TEXT("New work is admitted after the V001 route drains"),
        Fixture.CreateAndStart(TEXT("ORDER_ROUTE_V002"), V002UnitId,
            Reason));
    const FLBOneFactoryProductionLedgerState MixedHistory =
        Fixture.Production->CaptureLedger();
    const FLBOneFactoryVehicleUnitState* V002Unit =
        MixedHistory.Units.FindByPredicate([V002UnitId](
            const FLBOneFactoryVehicleUnitState& Unit)
            { return Unit.UnitId == V002UnitId; });
    TestNotNull(TEXT("V002 unit exists beside terminal V001 genealogy"), V002Unit);
    TestTrue(TEXT("New active work persists the V002 topology identity"),
        V002Unit && V002Unit->RuntimeTopologyId == CurrentTopologyId);
    const FLBOneFactoryVehicleUnitState* TerminalAliasAfterV002 =
        MixedHistory.Units.FindByPredicate([LegacyUnitId](
            const FLBOneFactoryVehicleUnitState& Unit)
            { return Unit.UnitId == LegacyUnitId; });
    TestTrue(TEXT("V002 admission neither rewrites nor adopts the terminal V001 alias"),
        TerminalAliasAfterV002
        && TerminalAliasAfterV002->RuntimeTopologyId ==
            FrozenLegacyTopologyAlias);
    TestTrue(TEXT("Mixed terminal-V001/active-V002 history remains coherent"),
        Fixture.Coordinator->ValidateRuntimeFactory(Reason));

    Fixture.Destroy();
    return true;
}

IMPLEMENT_SIMPLE_AUTOMATION_TEST(FLBOneFactoryManualRouteProfileMigrationTest,
    "LineBoss.OneFactory.RuntimeCoordinator.UnversionedManualWIPDrainsAsV001BeforeV002Admission",
    EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)

bool FLBOneFactoryManualRouteProfileMigrationTest::RunTest(
    const FString& Parameters)
{
    (void)Parameters;
    using namespace LBOneFactoryRuntimeCoordinatorTestsPrivate;
    FString Reason;
    FFactoryFixture Fixture;
    if (!TestTrue(TEXT("manual-profile fixture commissions"),
            Fixture.Create(TEXT("LBOneFactoryManualRouteProfileMigration"),
                Reason)))
    {
        AddError(Reason);
        Fixture.Destroy();
        return false;
    }

    TArray<FLBOneFactoryRuntimeStationStep> CurrentRoute;
    FName CurrentTopologyId;
    TestTrue(TEXT("empty fixture begins on V002"),
        Fixture.Coordinator->GetConfiguredStationRoute(
            CurrentRoute, CurrentTopologyId, Reason));
    const FName LegacyTopologyId = MakeLegacyV001TopologyId(CurrentRoute);
    TestEqual(TEXT("manual migration uses the computed relocated V001 companion"),
        LegacyTopologyId,
        FName(TEXT("OF_RUNTIME_TOPOLOGY_V001_E287C325")));

    const FLBOneFactoryPaintStarterLayoutState PaintState =
        Fixture.Paint->CaptureLayout();
    const FName ModelId = Fixture.Body->CaptureLayout().VehicleModelId;
    FName LegacyManualId;
    TestTrue(TEXT("manual fixture unit is initially admitted as new V002 work"),
        Fixture.Production->CreateVehicleOrder(
            TEXT("ORDER_MANUAL_LEGACY"), ModelId,
            PaintState.PaintProgrammeId, TEXT("CAIRNWELL_TEAL"),
            TEXT("COIL_MANUAL_LEGACY"), TEXT("MANUAL_PRESSING"),
            LegacyManualId, Reason));

    FLBOneFactoryProductionLedgerState LegacyManualLedger =
        Fixture.Production->CaptureLedger();
    FLBOneFactoryVehicleUnitState* LegacyManual =
        LegacyManualLedger.Units.FindByPredicate([LegacyManualId](
            const FLBOneFactoryVehicleUnitState& Unit)
            { return Unit.UnitId == LegacyManualId; });
    TestNotNull(TEXT("manual legacy fixture unit exists"), LegacyManual);
    if (!LegacyManual)
    {
        Fixture.Destroy();
        return false;
    }
    LegacyManual->Stage = ELBOneFactoryVehicleStage::Pressing;
    LegacyManual->Department = ELBOneFactoryDepartment::Press;
    LegacyManual->CurrentStationId = TEXT("MANUAL_PRESSING");
    LegacyManual->RouteProfileVersion =
        ULBOneFactoryProductionFlowLibrary::UnversionedRouteProfile;
    TestTrue(TEXT("cursor -1 pre-V002 manual genealogy restores unchanged"),
        Fixture.Production->RestoreLedger(LegacyManualLedger, Reason));

    FLBOneFactorySaveState ManualSave =
        ULBOneFactorySaveGame::MakeCanonicalEmptyState();
    ManualSave.PressLayout = Fixture.Press->CaptureLayout();
    ManualSave.BodyWeldLayout = Fixture.Body->CaptureLayout();
    ManualSave.PaintLayout = Fixture.Paint->CaptureLayout();
    ManualSave.AssemblyLayout = Fixture.Assembly->CaptureLayout();
    ManualSave.ProductionLedger = Fixture.Production->CaptureLedger();
    ManualSave.PayloadRevision = ManualSave.ProductionLedger.Revision;
    ManualSave.CapturedAtUtc = FDateTime::UtcNow();
    TestTrue(TEXT("active cursor -1 legacy/manual save validates"),
        ULBOneFactorySaveGame::ValidateState(ManualSave, Reason));
    ULBOneFactorySaveGame* ManualSaveRoot =
        NewObject<ULBOneFactorySaveGame>();
    ManualSaveRoot->FactoryState = ManualSave;
    TArray<uint8> ManualBytes;
    TestTrue(TEXT("active cursor -1 legacy/manual save serializes"),
        UGameplayStatics::SaveGameToMemory(ManualSaveRoot, ManualBytes));
    ULBOneFactorySaveGame* LoadedManual = Cast<ULBOneFactorySaveGame>(
        UGameplayStatics::LoadGameFromMemory(ManualBytes));
    const FLBOneFactoryVehicleUnitState* LoadedManualUnit = LoadedManual
        ? LoadedManual->FactoryState.ProductionLedger.Units.FindByPredicate(
            [LegacyManualId](const FLBOneFactoryVehicleUnitState& Unit)
            { return Unit.UnitId == LegacyManualId; })
        : nullptr;
    TestTrue(TEXT("load preserves cursor -1 and the additive unversioned default"),
        LoadedManualUnit && LoadedManualUnit->RuntimeStationCursor == -1
        && LoadedManualUnit->RouteProfileVersion ==
            ULBOneFactoryProductionFlowLibrary::UnversionedRouteProfile);

    TArray<FLBOneFactoryRuntimeStationStep> SelectedRoute;
    FName SelectedTopologyId;
    TestTrue(TEXT("active unversioned manual WIP selects legacy route semantics"),
        Fixture.Coordinator->GetConfiguredStationRoute(
            SelectedRoute, SelectedTopologyId, Reason));
    TestTrue(TEXT("composite runtime validation accepts unreserved cursor -1 V001 WIP"),
        Fixture.Coordinator->ValidateRuntimeFactory(Reason));
    TestEqual(TEXT("manual WIP selects the canonical V001 topology"),
        SelectedTopologyId, LegacyTopologyId);
    TestFalse(TEXT("manual V001 inspection position is not a quality gate"),
        SelectedRoute[5].bQualityGate);

    FName BlockedUnitId;
    TestFalse(TEXT("runtime admission is fenced by active cursor -1 V001 WIP"),
        Fixture.Coordinator->CreateRuntimeVehicleOrder(
            TEXT("ORDER_BLOCKED_BY_MANUAL_V001"), ModelId,
            PaintState.PaintProgrammeId, TEXT("CAIRNWELL_TEAL"),
            TEXT("COIL_BLOCKED_BY_MANUAL_V001"), BlockedUnitId, Reason));
    TestTrue(TEXT("manual runtime fence names the required drain"),
        Reason.Contains(TEXT("V001 ROUTE WIP MUST DRAIN")));
    TestFalse(TEXT("direct manual admission cannot bypass the same fence"),
        Fixture.Production->CreateVehicleOrder(
            TEXT("ORDER_DIRECT_BLOCKED_BY_MANUAL_V001"), ModelId,
            PaintState.PaintProgrammeId, TEXT("CAIRNWELL_TEAL"),
            TEXT("COIL_DIRECT_BLOCKED"), TEXT("MANUAL_INBOUND"),
            BlockedUnitId, Reason));
    TestTrue(TEXT("direct fence identifies unversioned WIP"),
        Reason.Contains(TEXT("UNVERSIONED WIP MUST DRAIN")));

    FLBOneFactoryProductionLedgerState MixedProfiles =
        Fixture.Production->CaptureLedger();
    FLBOneFactoryVehicleUnitState SyntheticV002 = MixedProfiles.Units[0];
    SyntheticV002.UnitId = TEXT("CAIRNWELL_2040-000002");
    SyntheticV002.BuildOrderId = TEXT("ORDER_SYNTHETIC_V002");
    SyntheticV002.SourceMaterialUnitIds = {TEXT("COIL_SYNTHETIC_V002")};
    SyntheticV002.PressedPanelTypeIds.Reset();
    SyntheticV002.EvidenceIds.Reset();
    SyntheticV002.Stage = ELBOneFactoryVehicleStage::InboundCoil;
    SyntheticV002.Department = ELBOneFactoryDepartment::Press;
    SyntheticV002.CurrentStationId = TEXT("MANUAL_V002_INBOUND");
    SyntheticV002.QualityState =
        ELBOneFactoryVehicleQualityState::NotInspected;
    SyntheticV002.StageRevision = 0;
    SyntheticV002.RouteProfileVersion = ULBOneFactoryProductionFlowLibrary::
        PressInspectionRouteProfileV002;
    MixedProfiles.Units.Add(SyntheticV002);
    MixedProfiles.NextVehicleSerial = 3;
    TestFalse(TEXT("ledger rejects simultaneous active manual V001 and V002 semantics"),
        ULBOneFactoryProductionFlowLibrary::ValidateLedger(
            MixedProfiles, Reason));
    TestTrue(TEXT("mixed-profile rejection is explicit"),
        Reason.Contains(TEXT("CANNOT MIX ACTIVE V001 AND V002")));

    TestTrue(TEXT("legacy manual Pressing advances directly to stillage"),
        Fixture.Production->AdvanceVehicle(LegacyManualId,
            TEXT("MANUAL_PANEL_STILLAGE"),
            TEXT("MANUAL_V001_PRESS_COMPLETE"), Reason));
    FLBOneFactoryProductionLedgerState DownstreamLedger =
        Fixture.Production->CaptureLedger();
    const FLBOneFactoryVehicleUnitState* DownstreamManual =
        DownstreamLedger.Units.FindByPredicate([LegacyManualId](
            const FLBOneFactoryVehicleUnitState& Unit)
            { return Unit.UnitId == LegacyManualId; });
    TestTrue(TEXT("manual V001 skips the new gate, stamps BOM, and persists V001"),
        DownstreamManual
        && DownstreamManual->Stage ==
            ELBOneFactoryVehicleStage::PressedPanelStillage
        && DownstreamManual->PressedPanelTypeIds ==
            DownstreamManual->RequiredPanelTypeIds
        && DownstreamManual->RouteProfileVersion ==
            ULBOneFactoryProductionFlowLibrary::LegacyRouteProfileV001);
    TestTrue(TEXT("downstream cursor -1 V001 WIP remains composite-valid"),
        Fixture.Coordinator->ValidateRuntimeFactory(Reason));
    TestFalse(TEXT("downstream active V001 manual genealogy still fences admission"),
        Fixture.Production->CreateVehicleOrder(
            TEXT("ORDER_BLOCKED_DOWNSTREAM_V001"), ModelId,
            PaintState.PaintProgrammeId, TEXT("CAIRNWELL_TEAL"),
            TEXT("COIL_BLOCKED_DOWNSTREAM"), TEXT("MANUAL_INBOUND"),
            BlockedUnitId, Reason));

    bool bManualDispatched = false;
    int32 EvidenceSerial = 0;
    for (int32 Guard = 0; Guard < 40; ++Guard)
    {
        const FLBOneFactoryProductionLedgerState Ledger =
            Fixture.Production->CaptureLedger();
        const FLBOneFactoryVehicleUnitState* Unit =
            Ledger.Units.FindByPredicate([LegacyManualId](
                const FLBOneFactoryVehicleUnitState& Candidate)
                { return Candidate.UnitId == LegacyManualId; });
        if (!Unit)
        {
            AddError(TEXT("manual drain lost its UnitId"));
            break;
        }
        if (Unit->bDispatched)
        {
            bManualDispatched = true;
            break;
        }
        const FName Evidence(*FString::Printf(TEXT("MANUAL_DRAIN_%02d"),
            ++EvidenceSerial));
        if (Unit->QualityState == ELBOneFactoryVehicleQualityState::Pending)
        {
            if (!Fixture.Production->SubmitQualityResult(LegacyManualId,
                    ELBOneFactoryVehicleQualityState::Passed,
                    Evidence, Reason))
            {
                AddError(Reason);
                break;
            }
        }
        else if (!Fixture.Production->AdvanceVehicle(LegacyManualId,
                FName(*FString::Printf(TEXT("MANUAL_STAGE_%02d"),
                    EvidenceSerial)), Evidence, Reason))
        {
            AddError(Reason);
            break;
        }
    }
    TestTrue(TEXT("legacy manual unit drains to terminal without adopting V002"),
        bManualDispatched);
    TestTrue(TEXT("terminal manual V001 genealogy no longer fences V002"),
        Fixture.Coordinator->GetConfiguredStationRoute(
            SelectedRoute, SelectedTopologyId, Reason)
        && SelectedTopologyId == CurrentTopologyId);

    FName NewV002ManualId;
    TestTrue(TEXT("new manual V002 work is admitted after legacy manual drain"),
        Fixture.Production->CreateVehicleOrder(
            TEXT("ORDER_MANUAL_V002_AFTER_DRAIN"), ModelId,
            PaintState.PaintProgrammeId, TEXT("CAIRNWELL_TEAL"),
            TEXT("COIL_MANUAL_V002_AFTER_DRAIN"), TEXT("MANUAL_INBOUND"),
            NewV002ManualId, Reason));
    const FLBOneFactoryProductionLedgerState FinalLedger =
        Fixture.Production->CaptureLedger();
    const FLBOneFactoryVehicleUnitState* NewV002Manual =
        FinalLedger.Units.FindByPredicate([NewV002ManualId](
            const FLBOneFactoryVehicleUnitState& Unit)
            { return Unit.UnitId == NewV002ManualId; });
    TestTrue(TEXT("post-drain manual work persists explicit V002 semantics"),
        NewV002Manual && NewV002Manual->RouteProfileVersion ==
            ULBOneFactoryProductionFlowLibrary::
                PressInspectionRouteProfileV002);

    Fixture.Destroy();
    return !HasAnyErrors();
}

IMPLEMENT_SIMPLE_AUTOMATION_TEST(FLBOneFactoryManualRoutedModeExclusionTest,
    "LineBoss.OneFactory.RuntimeCoordinator.ManualAndRoutedActiveWIPAreMutuallyExclusive",
    EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)

bool FLBOneFactoryManualRoutedModeExclusionTest::RunTest(
    const FString& Parameters)
{
    (void)Parameters;
    using namespace LBOneFactoryRuntimeCoordinatorTestsPrivate;
    FString Reason;

    FFactoryFixture RoutedFixture;
    if (!TestTrue(TEXT("routed exclusion fixture commissions"),
            RoutedFixture.Create(TEXT("LBOneFactoryRoutedModeExclusion"),
                Reason)))
    {
        AddError(Reason);
        RoutedFixture.Destroy();
        return false;
    }

    const FLBOneFactoryPaintStarterLayoutState RoutedPaint =
        RoutedFixture.Paint->CaptureLayout();
    const FName RoutedModelId =
        RoutedFixture.Body->CaptureLayout().VehicleModelId;
    FName RoutedUnitId;
    TestTrue(TEXT("V002 routed WIP starts before direct-admission check"),
        RoutedFixture.CreateAndStart(TEXT("ORDER_ROUTED_V002_ACTIVE"),
            RoutedUnitId, Reason));

    FName BlockedManualId;
    TestFalse(TEXT("direct manual admission is blocked by active routed V002 WIP"),
        RoutedFixture.Production->CreateVehicleOrder(
            TEXT("ORDER_MANUAL_BLOCKED_BY_ROUTED_V002"), RoutedModelId,
            RoutedPaint.PaintProgrammeId, TEXT("CAIRNWELL_TEAL"),
            TEXT("COIL_MANUAL_BLOCKED_BY_ROUTED_V002"),
            TEXT("MANUAL_V002_INBOUND"), BlockedManualId, Reason));
    TestTrue(TEXT("manual rejection names the active routed drain"),
        Reason.Contains(TEXT("ACTIVE ROUTED WIP MUST DRAIN")));

    const FLBOneFactoryProductionLedgerState RoutedLedger =
        RoutedFixture.Production->CaptureLedger();
    const FLBOneFactoryVehicleUnitState* RoutedUnit =
        RoutedLedger.Units.FindByPredicate([RoutedUnitId](
            const FLBOneFactoryVehicleUnitState& Unit)
            { return Unit.UnitId == RoutedUnitId; });
    TestNotNull(TEXT("routed unit exists for same-profile ledger probe"),
        RoutedUnit);
    if (RoutedUnit)
    {
        FLBOneFactoryProductionLedgerState SameProfileMixedLedger =
            RoutedLedger;
        FLBOneFactoryVehicleUnitState ManualV002 = *RoutedUnit;
        ManualV002.UnitId = TEXT("CAIRNWELL_2040-000002");
        ManualV002.BuildOrderId = TEXT("ORDER_SYNTHETIC_MANUAL_V002");
        ManualV002.SourceMaterialUnitIds = {
            TEXT("COIL_SYNTHETIC_MANUAL_V002")};
        ManualV002.EvidenceIds.Reset();
        ManualV002.PressedPanelTypeIds.Reset();
        ManualV002.Stage = ELBOneFactoryVehicleStage::InboundCoil;
        ManualV002.Department = ELBOneFactoryDepartment::Press;
        ManualV002.CurrentStationId = TEXT("MANUAL_V002_INBOUND");
        ManualV002.QualityState =
            ELBOneFactoryVehicleQualityState::NotInspected;
        ManualV002.StageRevision = 0;
        ManualV002.RouteProfileVersion =
            ULBOneFactoryProductionFlowLibrary::
                PressInspectionRouteProfileV002;
        ManualV002.RuntimeStationCursor = -1;
        ManualV002.RuntimeCompletedStationCount = 0;
        ManualV002.RuntimeTotalStationCount = 0;
        ManualV002.RuntimeCycleElapsedSeconds = 0.0f;
        ManualV002.RuntimeCycleDurationSeconds = 0.0f;
        ManualV002.RuntimeTopologyId = NAME_None;
        ManualV002.RuntimeCurrentAssignmentId = NAME_None;
        ManualV002.bRuntimeStarted = false;
        ManualV002.bCompleted = false;
        ManualV002.bDispatched = false;
        ManualV002.FulfilledContractId = NAME_None;
        ManualV002.DispatchedAtSimSeconds = -1.0;
        SameProfileMixedLedger.Units.Add(ManualV002);
        SameProfileMixedLedger.NextVehicleSerial = 3;

        TestFalse(TEXT("same-profile active manual and routed WIP is rejected"),
            ULBOneFactoryProductionFlowLibrary::ValidateLedger(
                SameProfileMixedLedger, Reason));
        TestTrue(TEXT("same-profile rejection identifies mixed active modes"),
            Reason.Contains(TEXT("CANNOT MIX ACTIVE MANUAL AND ROUTED WIP")));
        TestFalse(TEXT("restore cannot install a same-profile mixed-mode ledger"),
            RoutedFixture.Production->RestoreLedger(
                SameProfileMixedLedger, Reason));
        TestEqual(TEXT("failed mixed-mode restore preserves routed ledger"),
            RoutedFixture.Production->CaptureLedger().Units.Num(), 1);
    }
    RoutedFixture.Destroy();

    FFactoryFixture ManualFixture;
    if (!TestTrue(TEXT("manual exclusion fixture commissions"),
            ManualFixture.Create(TEXT("LBOneFactoryManualModeExclusion"),
                Reason)))
    {
        AddError(Reason);
        ManualFixture.Destroy();
        return false;
    }

    const FLBOneFactoryPaintStarterLayoutState ManualPaint =
        ManualFixture.Paint->CaptureLayout();
    const FName ManualModelId =
        ManualFixture.Body->CaptureLayout().VehicleModelId;
    FName ManualUnitId;
    TestTrue(TEXT("direct manual V002 WIP is admitted on an empty line"),
        ManualFixture.Production->CreateVehicleOrder(
            TEXT("ORDER_MANUAL_V002_ACTIVE"), ManualModelId,
            ManualPaint.PaintProgrammeId, TEXT("CAIRNWELL_TEAL"),
            TEXT("COIL_MANUAL_V002_ACTIVE"), TEXT("MANUAL_V002_INBOUND"),
            ManualUnitId, Reason));
    const FLBOneFactoryProductionLedgerState ManualLedger =
        ManualFixture.Production->CaptureLedger();
    const FLBOneFactoryVehicleUnitState* ManualUnit =
        ManualLedger.Units.FindByPredicate([ManualUnitId](
            const FLBOneFactoryVehicleUnitState& Unit)
            { return Unit.UnitId == ManualUnitId; });
    TestTrue(TEXT("manual-only active V002 genealogy is valid"),
        ManualUnit && ManualUnit->RuntimeStationCursor == -1
        && ManualUnit->RouteProfileVersion ==
            ULBOneFactoryProductionFlowLibrary::
                PressInspectionRouteProfileV002
        && ManualFixture.Coordinator->ValidateRuntimeFactory(Reason));

    FName BlockedRoutedId;
    TestFalse(TEXT("new routed admission is blocked by active manual V002 WIP"),
        ManualFixture.Coordinator->CreateRuntimeVehicleOrder(
            TEXT("ORDER_ROUTED_BLOCKED_BY_MANUAL_V002"), ManualModelId,
            ManualPaint.PaintProgrammeId, TEXT("CAIRNWELL_TEAL"),
            TEXT("COIL_ROUTED_BLOCKED_BY_MANUAL_V002"),
            BlockedRoutedId, Reason));
    TestTrue(TEXT("routed rejection names the active manual drain"),
        Reason.Contains(TEXT("ACTIVE MANUAL WIP MUST DRAIN")));

    ManualFixture.Destroy();
    return !HasAnyErrors();
}

#endif
