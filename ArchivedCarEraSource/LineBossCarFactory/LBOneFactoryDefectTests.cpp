#if WITH_DEV_AUTOMATION_TESTS

#include "LBOneFactoryProductionFlow.h"

#include "Engine/World.h"
#include "Misc/AutomationTest.h"

IMPLEMENT_SIMPLE_AUTOMATION_TEST(FLBOneFactoryDefectDeterminismTest,
    "LineBoss.OneFactory.ProductionFlow.DefectSuspicionIsDeterministicAndMaintenanceResets",
    EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)

bool FLBOneFactoryDefectDeterminismTest::RunTest(const FString& Parameters)
{
    (void)Parameters;

    // No wear never flags; full wear flags deterministically and
    // identically on every call.
    const FName UnitA(TEXT("C2040-000001"));
    TestFalse(TEXT("zero wear never suspects"),
        ULBOneFactoryProductionFlowLibrary::IsDefectSuspected(UnitA, 0.0));
    const bool FirstCall =
        ULBOneFactoryProductionFlowLibrary::IsDefectSuspected(UnitA, 1.0);
    for (int32 Repeat = 0; Repeat < 8; ++Repeat)
    {
        TestEqual(TEXT("suspicion is a pure function of id and wear"),
            ULBOneFactoryProductionFlowLibrary::IsDefectSuspected(UnitA, 1.0),
            FirstCall);
    }
    // At full wear roughly four in ten units flag: across a serial run of
    // ids, at least one flags and at least one does not.
    int32 Flagged = 0;
    for (int32 Serial = 0; Serial < 25; ++Serial)
    {
        const FName UnitId(*FString::Printf(TEXT("C2040-%06d"), Serial));
        if (ULBOneFactoryProductionFlowLibrary::IsDefectSuspected(UnitId, 1.0))
        {
            ++Flagged;
        }
    }
    TestTrue(TEXT("full wear flags some units"), Flagged > 0);
    TestTrue(TEXT("full wear does not flag every unit"), Flagged < 25);

    // Maintenance resets wear on the ledger and counts its service.
    UWorld* World = UWorld::CreateWorld(EWorldType::Game, false,
        FName(TEXT("LBDefectWorld")));
    ALBOneFactoryProductionFlowAuthority* Production =
        World->SpawnActor<ALBOneFactoryProductionFlowAuthority>();
    if (TestNotNull(TEXT("production authority spawns"), Production))
    {
        FString Reason;
        FLBOneFactoryProductionLedgerState Ledger =
            Production->CaptureLedger();
        Ledger.FleetWear01 = 0.6;
        ++Ledger.Revision;
        TestTrue(Reason, Production->RestoreLedger(Ledger, Reason));
        TestTrue(Reason, Production->PerformPlantMaintenance(Reason));
        const FLBOneFactoryProductionLedgerState After =
            Production->CaptureLedger();
        TestEqual(TEXT("maintenance resets wear"), After.FleetWear01, 0.0);
        TestEqual(TEXT("maintenance is counted"), After.MaintenanceSerial, 1);
    }
    World->DestroyWorld(false);
    return true;
}

#endif
