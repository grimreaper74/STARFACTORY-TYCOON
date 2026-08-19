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

#endif
