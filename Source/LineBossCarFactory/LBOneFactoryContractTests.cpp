#if WITH_DEV_AUTOMATION_TESTS

#include "LBOneFactoryProductionFlow.h"

#include "Engine/World.h"
#include "Misc/AutomationTest.h"

IMPLEMENT_SIMPLE_AUTOMATION_TEST(FLBOneFactoryContractLifecycleTest,
    "LineBoss.OneFactory.ProductionFlow.ContractSeedExpiryAndIdempotency",
    EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)

bool FLBOneFactoryContractLifecycleTest::RunTest(const FString& Parameters)
{
    (void)Parameters;
    UWorld* World = UWorld::CreateWorld(EWorldType::Game, false,
        FName(TEXT("LBContractWorld")));
    ALBOneFactoryProductionFlowAuthority* Production =
        World->SpawnActor<ALBOneFactoryProductionFlowAuthority>();
    if (!TestNotNull(TEXT("production authority spawns"), Production))
    {
        World->DestroyWorld(false);
        return false;
    }
    FString Reason;

    // Validation: no id, no quantity, no price -> rejected.
    FLBOneFactoryVehicleContract Bad;
    TestFalse(TEXT("an empty contract is rejected"),
        Production->AddVehicleContract(Bad, Reason));

    // The starter chain seeds once and is idempotent.
    TestTrue(Reason, Production->SeedStarterContracts(Reason));
    TestTrue(Reason, Production->SeedStarterContracts(Reason));
    FLBOneFactoryProductionLedgerState Ledger = Production->CaptureLedger();
    TestEqual(TEXT("three starter contracts, seeded once"),
        Ledger.Contracts.Num(), 3);
    TestEqual(TEXT("starter contracts open"),
        Ledger.Contracts[0].State, ELBOneFactoryContractState::Open);

    // Deadlines: the 4-hour contract expires when the clock passes it;
    // the 10 and 20 hour contracts stay open.
    TestTrue(Reason, Production->AdvanceSimulationClock(5.0f * 3600.0f,
        Reason));
    TestEqual(TEXT("exactly one contract expires at 5h"),
        Production->SweepContractDeadlines(Reason), 1);
    TestEqual(TEXT("sweep is idempotent"),
        Production->SweepContractDeadlines(Reason), 0);
    Ledger = Production->CaptureLedger();
    TestEqual(TEXT("first contract expired"),
        Ledger.Contracts[0].State, ELBOneFactoryContractState::Expired);
    TestEqual(TEXT("second contract still open"),
        Ledger.Contracts[1].State, ELBOneFactoryContractState::Open);

    // Contracts survive a capture/restore round trip.
    ALBOneFactoryProductionFlowAuthority* Restored =
        World->SpawnActor<ALBOneFactoryProductionFlowAuthority>();
    if (TestNotNull(TEXT("second authority spawns"), Restored))
    {
        TestTrue(Reason, Restored->RestoreLedger(Ledger, Reason));
        TestEqual(TEXT("restored contracts intact"),
            Restored->CaptureLedger().Contracts.Num(), 3);
    }

    World->DestroyWorld(false);
    return true;
}

IMPLEMENT_SIMPLE_AUTOMATION_TEST(FLBOneFactorySoftFailureTest,
    "LineBoss.OneFactory.ProductionFlow.SoftFailureWarnsRescuesAndCostsReputation",
    EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)

bool FLBOneFactorySoftFailureTest::RunTest(const FString& Parameters)
{
    (void)Parameters;
    UWorld* World = UWorld::CreateWorld(EWorldType::Game, false,
        FName(TEXT("LBSoftFailureWorld")));
    ALBOneFactoryProductionFlowAuthority* Production =
        World->SpawnActor<ALBOneFactoryProductionFlowAuthority>();
    if (!TestNotNull(TEXT("production authority spawns"), Production))
    {
        World->DestroyWorld(false);
        return false;
    }
    FString Reason;

    TestEqual(TEXT("reputation starts at 100"),
        Production->CaptureLedger().ReputationScore, 100);

    // Healthy -> Warning -> Emergency, all soft.
    TestTrue(Reason, Production->ApplyFinancialPolicy(100000000, Reason));
    TestEqual(TEXT("healthy above the floor"),
        Production->CaptureLedger().FinancialState,
        ELBOneFactoryFinancialState::Healthy);
    TestTrue(Reason, Production->ApplyFinancialPolicy(10000000, Reason));
    TestEqual(TEXT("warning below the floor"),
        Production->CaptureLedger().FinancialState,
        ELBOneFactoryFinancialState::Warning);

    TestTrue(Reason, Production->ApplyFinancialPolicy(-500000, Reason));
    FLBOneFactoryProductionLedgerState Ledger = Production->CaptureLedger();
    TestEqual(TEXT("emergency below zero"),
        Ledger.FinancialState, ELBOneFactoryFinancialState::Emergency);
    TestEqual(TEXT("one rescue contract offered"), Ledger.Contracts.Num(), 1);
    TestTrue(TEXT("rescue is flagged emergency"),
        Ledger.Contracts[0].bEmergency);
    TestEqual(TEXT("rescue costs ten reputation"),
        Ledger.ReputationScore, 90);

    // Still in crisis: the open rescue is not duplicated.
    TestTrue(Reason, Production->ApplyFinancialPolicy(-800000, Reason));
    Ledger = Production->CaptureLedger();
    TestEqual(TEXT("no second rescue while one is open"),
        Ledger.Contracts.Num(), 1);
    TestEqual(TEXT("reputation charged once"), Ledger.ReputationScore, 90);

    // Expiring the rescue costs standing and permits a fresh offer.
    TestTrue(Reason, Production->AdvanceSimulationClock(7.0f * 3600.0f,
        Reason));
    TestEqual(TEXT("rescue expires past its deadline"),
        Production->SweepContractDeadlines(Reason), 1);
    TestTrue(Reason, Production->ApplyFinancialPolicy(-800000, Reason));
    Ledger = Production->CaptureLedger();
    TestEqual(TEXT("a second rescue can then be offered"),
        Ledger.Contracts.Num(), 2);
    TestEqual(TEXT("expiry and second rescue both cost reputation"),
        Ledger.ReputationScore, 75);

    World->DestroyWorld(false);
    return true;
}

#endif
