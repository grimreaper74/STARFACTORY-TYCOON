#include "LBOneFactoryProductionHUD.h"

#if WITH_DEV_AUTOMATION_TESTS

#include "Engine/World.h"
#include "LBOneFactoryBodyWeldStarterLayout.h"
#include "LBOneFactoryPaintStarterLayout.h"
#include "LBOneFactoryPressStarterLayout.h"
#include "LBOneFactoryAssemblyStarterLayout.h"
#include "LBOneFactoryProductionFlow.h"
#include "LBOneFactoryRuntimeCoordinator.h"
#include "Misc/AutomationTest.h"

IMPLEMENT_SIMPLE_AUTOMATION_TEST(FLBOneFactoryFlowStripGroupsTest,
    "LineBoss.OneFactory.UI.FlowStripGroupsCarryAnchorsAndHonestRates",
    EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)

bool FLBOneFactoryFlowStripGroupsTest::RunTest(const FString& Parameters)
{
    (void)Parameters;
    UWorld* World = UWorld::CreateWorld(EWorldType::Game, false,
        FName(TEXT("LBFlowStripWorld")));
    if (!TestNotNull(TEXT("world"), World))
    {
        return false;
    }
    auto* Press =
        World->SpawnActor<ALBOneFactoryPressStarterLayoutAuthority>();
    auto* Body =
        World->SpawnActor<ALBOneFactoryBodyWeldStarterLayoutAuthority>();
    auto* Paint =
        World->SpawnActor<ALBOneFactoryPaintStarterLayoutAuthority>();
    auto* Assembly =
        World->SpawnActor<ALBOneFactoryAssemblyStarterLayoutAuthority>();
    auto* Production =
        World->SpawnActor<ALBOneFactoryProductionFlowAuthority>();
    auto* Coordinator = World->SpawnActor<ALBOneFactoryRuntimeCoordinator>();
    FString Reason;
    if (!Press || !Body || !Paint || !Assembly || !Production || !Coordinator
        || !Press->Commission(Reason) || !Body->Commission(Reason)
        || !Paint->Commission(Reason) || !Assembly->Commission(Reason))
    {
        AddError(FString::Printf(TEXT("fixture failed: %s"), *Reason));
        World->DestroyWorld(false);
        return false;
    }
    for (int32 DepartmentIndex = 0; DepartmentIndex < 4; ++DepartmentIndex)
    {
        if (!Production->SetDepartmentCommissioned(
                static_cast<ELBOneFactoryDepartment>(DepartmentIndex), true,
                Reason))
        {
            AddError(Reason);
            World->DestroyWorld(false);
            return false;
        }
    }
    TestTrue(Reason, Coordinator->ValidateRuntimeFactory(Reason));

    TArray<FLBOneFactoryProcessGroup> Groups;
    TArray<FString> Alerts;
    int32 UnitsLive = 0;
    int32 Dispatched = 0;
    TestTrue(TEXT("groups collect from a commissioned factory"),
        ALBOneFactoryProductionHUD::CollectGroups(World, Groups, UnitsLive,
            Dispatched, Alerts));
    TestEqual(TEXT("seven coarse groups"), Groups.Num(), 7);

    for (const FLBOneFactoryProcessGroup& Group : Groups)
    {
        if (Group.StationCount <= 0)
        {
            continue;
        }
        TestTrue(FString::Printf(
                TEXT("%s carries a world anchor for the card click"),
                *Group.Label), Group.WorldBounds.IsValid != 0);
        TestTrue(FString::Printf(TEXT("%s knows its department"),
                *Group.Label), Group.bHasDepartment);
        // No unit has completed a station yet, so an honest measured rate
        // must be exactly zero - never the route capacity.
        TestEqual(FString::Printf(TEXT("%s measured rate starts at zero"),
                *Group.Label), Group.MeasuredRatePerHour, 0.0f);
    }

    World->DestroyWorld(false);
    return true;
}

#endif
