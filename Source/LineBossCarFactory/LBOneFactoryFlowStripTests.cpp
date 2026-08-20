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
    TArray<FLBOneFactoryLiveAlert> Alerts;
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

IMPLEMENT_SIMPLE_AUTOMATION_TEST(FLBOneFactoryLiveAlertPlumbingTest,
    "LineBoss.OneFactory.UI.QualityHoldRaisesANavigableLiveAlert",
    EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)

bool FLBOneFactoryLiveAlertPlumbingTest::RunTest(const FString& Parameters)
{
    (void)Parameters;
    UWorld* World = UWorld::CreateWorld(EWorldType::Game, false,
        FName(TEXT("LBLiveAlertWorld")));
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

    FName UnitId;
    const FLBOneFactoryPaintStarterLayoutState PaintState =
        Paint->CaptureLayout();
    if (!TestTrue(Reason, Coordinator->CreateRuntimeVehicleOrder(
            TEXT("ORDER_ALERT_PLUMBING"),
            Body->CaptureLayout().VehicleModelId,
            PaintState.PaintProgrammeId, TEXT("CAIRNWELL_TEAL"),
            TEXT("COIL_ALERT_PLUMBING"), UnitId, Reason))
        || !TestTrue(Reason, Coordinator->StartVehicle(UnitId, Reason)))
    {
        World->DestroyWorld(false);
        return false;
    }

    // Tick station by station (one per call) until the first quality gate
    // holds the unit awaiting a result.
    bool bHeld = false;
    for (int32 Guard = 0; Guard < 80 && !bHeld; ++Guard)
    {
        if (!Coordinator->TickVehicle(UnitId, 1000.0f, Reason))
        {
            AddError(Reason);
            break;
        }
        FLBOneFactoryRuntimeVehicleStatus Status;
        if (Coordinator->GetVehicleRuntimeStatus(UnitId, Status, Reason))
        {
            bHeld = Status.bAwaitingQualityResult;
        }
    }
    TestTrue(TEXT("a quality gate eventually holds the unit"), bHeld);

    TArray<FLBOneFactoryProcessGroup> Groups;
    TArray<FLBOneFactoryLiveAlert> Alerts;
    int32 UnitsLive = 0;
    int32 Dispatched = 0;
    TestTrue(TEXT("groups collect while the unit is held"),
        ALBOneFactoryProductionHUD::CollectGroups(World, Groups, UnitsLive,
            Dispatched, Alerts));

    const FLBOneFactoryLiveAlert* Hold = Alerts.FindByPredicate(
        [](const FLBOneFactoryLiveAlert& Alert)
        {
            return Alert.Status == ELBOneFactoryStationStatus::QualityHold;
        });
    if (TestNotNull(TEXT("the hold raises a live alert"), Hold))
    {
        TestTrue(TEXT("the alert names its group for navigation"),
            Groups.IsValidIndex(Hold->GroupIndex));
        if (Groups.IsValidIndex(Hold->GroupIndex))
        {
            TestEqual(TEXT("the named group is in the hold state"),
                Groups[Hold->GroupIndex].State,
                ELBOneFactoryGroupState::Hold);
            TestTrue(TEXT("the named group has a camera anchor"),
                Groups[Hold->GroupIndex].WorldBounds.IsValid != 0);
        }
        TestTrue(TEXT("the alert message is written for the player"),
            !Hold->Message.IsEmpty());
    }

    World->DestroyWorld(false);
    return true;
}

#endif
