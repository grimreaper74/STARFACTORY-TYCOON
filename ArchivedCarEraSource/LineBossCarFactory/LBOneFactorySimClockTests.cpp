#if WITH_DEV_AUTOMATION_TESTS

#include "LBOneFactoryProductionFlow.h"

#include "Engine/World.h"
#include "Misc/AutomationTest.h"

IMPLEMENT_SIMPLE_AUTOMATION_TEST(FLBOneFactorySimClockTest,
    "LineBoss.OneFactory.ProductionFlow.SimClockAdvancesHoldsOnPauseAndStampsUnits",
    EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)

bool FLBOneFactorySimClockTest::RunTest(const FString& Parameters)
{
    (void)Parameters;
    UWorld* World = UWorld::CreateWorld(EWorldType::Game, false,
        FName(TEXT("LBSimClockWorld")));
    ALBOneFactoryProductionFlowAuthority* Production =
        World->SpawnActor<ALBOneFactoryProductionFlowAuthority>();
    if (!TestNotNull(TEXT("production authority spawns"), Production))
    {
        World->DestroyWorld(false);
        return false;
    }

    FString Reason;
    TestEqual(TEXT("clock starts at zero"),
        Production->CaptureLedger().SimClockSeconds, 0.0);
    TestFalse(TEXT("non-finite or non-positive deltas are rejected"),
        Production->AdvanceSimulationClock(-1.0f, Reason));

    TestTrue(Reason, Production->AdvanceSimulationClock(90.0f, Reason));
    TestEqual(TEXT("clock advances by the delta"),
        Production->CaptureLedger().SimClockSeconds, 90.0);

    // Pause freezes factory time by design: the call succeeds, time holds.
    TestTrue(Reason, Production->SetLinePaused(true, Reason));
    TestTrue(Reason, Production->AdvanceSimulationClock(30.0f, Reason));
    TestEqual(TEXT("a paused line holds the clock"),
        Production->CaptureLedger().SimClockSeconds, 90.0);
    TestTrue(Reason, Production->SetLinePaused(false, Reason));
    TestTrue(Reason, Production->AdvanceSimulationClock(10.0f, Reason));
    TestEqual(TEXT("resume lets time flow again"),
        Production->CaptureLedger().SimClockSeconds, 100.0);

    // New orders are stamped with the clock; dispatch stamp starts negative.
    TestTrue(Reason, Production->SetDepartmentCommissioned(
        ELBOneFactoryDepartment::Press, true, Reason));
    FName UnitId;
    TestTrue(Reason, Production->CreateVehicleOrder(
        FName(TEXT("ORDER_CLOCK_1")), FName(TEXT("CAIRNWELL_2040")),
        FName(TEXT("PP_STD")), FName(TEXT("EMERALD")),
        FName(TEXT("COIL_LOT_1")), FName(TEXT("OF_P01_INBOUND")),
        UnitId, Reason));
    const FLBOneFactoryProductionLedgerState Ledger =
        Production->CaptureLedger();
    const FLBOneFactoryVehicleUnitState* Unit = Ledger.Units.FindByPredicate(
        [UnitId](const FLBOneFactoryVehicleUnitState& Candidate)
        { return Candidate.UnitId == UnitId; });
    if (TestNotNull(TEXT("created unit is on the ledger"), Unit))
    {
        TestEqual(TEXT("unit carries its creation sim-time"),
            Unit->CreatedAtSimSeconds, 100.0);
        TestTrue(TEXT("dispatch stamp stays negative until dispatch"),
            Unit->DispatchedAtSimSeconds < 0.0);
    }

    // The stamps and clock survive a capture/restore round trip.
    ALBOneFactoryProductionFlowAuthority* Restored =
        World->SpawnActor<ALBOneFactoryProductionFlowAuthority>();
    if (TestNotNull(TEXT("second authority spawns"), Restored))
    {
        TestTrue(Reason, Restored->RestoreLedger(Ledger, Reason));
        TestEqual(TEXT("restored clock matches"),
            Restored->CaptureLedger().SimClockSeconds, 100.0);
    }

    World->DestroyWorld(false);
    return true;
}

#endif
