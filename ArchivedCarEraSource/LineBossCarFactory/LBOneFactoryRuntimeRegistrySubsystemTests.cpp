#include "LBOneFactoryRuntimeRegistrySubsystem.h"

#if WITH_DEV_AUTOMATION_TESTS

#include "Engine/World.h"
#include "LBOneFactoryProductionFlow.h"
#include "LBOneFactoryRuntimeCoordinator.h"
#include "Misc/AutomationTest.h"

IMPLEMENT_SIMPLE_AUTOMATION_TEST(FLBOneFactoryRuntimeRegistryExactBackboneTest,
    "LineBoss.OneFactory.RuntimeRegistry.ExactBackboneAndSpawnInvalidation",
    EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)

bool FLBOneFactoryRuntimeRegistryExactBackboneTest::RunTest(
    const FString& Parameters)
{
    UWorld* World = UWorld::CreateWorld(EWorldType::Game, false,
        TEXT("LBOneFactoryRuntimeRegistryExactBackboneTest"));
    TestNotNull(TEXT("Registry test world exists"), World);
    if (!World)
    {
        return false;
    }

    ULBOneFactoryRuntimeRegistrySubsystem* Registry =
        World->GetSubsystem<ULBOneFactoryRuntimeRegistrySubsystem>();
    TestNotNull(TEXT("World owns the runtime registry"), Registry);
    ALBOneFactoryProductionFlowAuthority* Production =
        World->SpawnActor<ALBOneFactoryProductionFlowAuthority>();
    ALBOneFactoryRuntimeCoordinator* Coordinator =
        World->SpawnActor<ALBOneFactoryRuntimeCoordinator>();
    TestNotNull(TEXT("One production authority exists"), Production);
    TestNotNull(TEXT("One coordinator exists"), Coordinator);

    FString Reason;
    ALBOneFactoryProductionFlowAuthority* ResolvedProduction = nullptr;
    ALBOneFactoryRuntimeCoordinator* ResolvedCoordinator = nullptr;
    if (Registry && Production && Coordinator)
    {
        TestTrue(TEXT("Registry resolves the exact runtime backbone"),
            Registry->ResolveRuntimeBackbone(ResolvedProduction,
                ResolvedCoordinator, Reason));
        TestEqual(TEXT("Registry returns the production authority"),
            ResolvedProduction, Production);
        TestEqual(TEXT("Registry returns the runtime coordinator"),
            ResolvedCoordinator, Coordinator);

        ALBOneFactoryProductionFlowAuthority* Duplicate =
            World->SpawnActor<ALBOneFactoryProductionFlowAuthority>();
        TestNotNull(TEXT("Duplicate authority spawns for negative test"),
            Duplicate);
        TestFalse(TEXT("A later duplicate invalidates the cached backbone"),
            Registry->ResolveRuntimeBackbone(ResolvedProduction,
                ResolvedCoordinator, Reason));
        TestTrue(TEXT("Duplicate failure explains the exact-one contract"),
            Reason.Contains(TEXT("EXACTLY ONE PRODUCTION FLOW AUTHORITY")));
    }

    World->DestroyWorld(false);
    return true;
}

#endif
