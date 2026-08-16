#if WITH_DEV_AUTOMATION_TESTS

#include "Misc/AutomationTest.h"

#include "LBCoilAGVController.h"
#include "LBFactoryBuildMachine.h"
#include "LBPressTrainAStation.h"
#include "LBStatusBeaconComponent.h"
#include "LBSupportRobot.h"
#include "Components/PointLightComponent.h"
#include "Engine/World.h"

IMPLEMENT_SIMPLE_AUTOMATION_TEST(
    FLBStatusBeaconVisualContractTest,
    "LineBoss.Presentation.StatusBeacons.VisualContract",
    EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)

IMPLEMENT_SIMPLE_AUTOMATION_TEST(
    FLBStatusBeaconAuthorityMappingTest,
    "LineBoss.Presentation.StatusBeacons.AuthorityMapping",
    EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)

namespace
{
    ULBStatusBeaconComponent* FirstBeacon(AActor* Actor)
    {
        return Actor ? Actor->FindComponentByClass<ULBStatusBeaconComponent>() : nullptr;
    }
}

bool FLBStatusBeaconVisualContractTest::RunTest(const FString& Parameters)
{
    UWorld* World = UWorld::CreateWorld(EWorldType::Game, false, TEXT("LB_StatusBeacon_VisualContract"));
    ALBFactoryBuildMachine* Host = World ? World->SpawnActor<ALBFactoryBuildMachine>() : nullptr;
    ULBStatusBeaconComponent* Beacon = FirstBeacon(Host);
    TestNotNull(TEXT("Factory authority owns a reusable status beacon"), Beacon);
    if (!Beacon)
    {
        if (World) World->DestroyWorld(false);
        return false;
    }

    Beacon->SetStatus(ELBStatusBeaconState::Ready);
    TestTrue(TEXT("Ready is green"), Beacon->IsGreenLampLit());
    TestFalse(TEXT("Ready is not amber"), Beacon->IsAmberLampLit());
    TestFalse(TEXT("Ready is not red"), Beacon->IsRedLampLit());
    TestTrue(TEXT("Green state enables a real light component"),
        Beacon->GetGreenLight() && Beacon->GetGreenLight()->IsVisible()
            && Beacon->GetGreenLight()->Intensity > 0.0f);
    TestTrue(TEXT("Real status light is registered with the world"),
        Beacon->GetGreenLight() && Beacon->GetGreenLight()->IsRegistered());

    Beacon->SetStatus(ELBStatusBeaconState::Idle);
    TestTrue(TEXT("Idle is steady amber"), Beacon->IsAmberLampLit() && !Beacon->IsFlashing());

    Beacon->SetStatus(ELBStatusBeaconState::Moving);
    TestTrue(TEXT("Moving begins with amber beacon on"),
        Beacon->IsFlashing() && Beacon->IsAmberLampLit());
    Beacon->TickComponent(0.41f, LEVELTICK_All, nullptr);
    TestFalse(TEXT("Moving amber beacon enters its off half-cycle"), Beacon->IsAmberLampLit());
    TestFalse(TEXT("Moving beacon off phase disables the real amber light"),
        Beacon->GetAmberLight() && Beacon->GetAmberLight()->IsVisible());

    Beacon->SetStatus(ELBStatusBeaconState::Fault);
    TestTrue(TEXT("Fault is steady red"), Beacon->IsRedLampLit() && !Beacon->IsFlashing());
    Beacon->SetStatus(ELBStatusBeaconState::Emergency);
    TestTrue(TEXT("Emergency is flashing red"), Beacon->IsRedLampLit() && Beacon->IsFlashing());
    Beacon->TickComponent(0.41f, LEVELTICK_All, nullptr);
    TestFalse(TEXT("Emergency red beacon enters its off half-cycle"), Beacon->IsRedLampLit());

    World->DestroyWorld(false);
    return true;
}

bool FLBStatusBeaconAuthorityMappingTest::RunTest(const FString& Parameters)
{
    UWorld* World = UWorld::CreateWorld(EWorldType::Game, false, TEXT("LB_StatusBeacon_AuthorityMapping"));
    ALBFactoryBuildMachine* Machine = World ? World->SpawnActor<ALBFactoryBuildMachine>() : nullptr;
    ALBSupportRobot* Robot = World ? World->SpawnActor<ALBSupportRobot>() : nullptr;
    ALBCoilAGVController* AGV = World ? World->SpawnActor<ALBCoilAGVController>() : nullptr;
    ALBPressTrainAStation* Train = World ? World->SpawnActor<ALBPressTrainAStation>() : nullptr;
    TestNotNull(TEXT("Machine spawns"), Machine);
    TestNotNull(TEXT("Support robot spawns"), Robot);
    TestNotNull(TEXT("Coil AGV spawns"), AGV);
    TestNotNull(TEXT("Press train spawns"), Train);
    if (!Machine || !Robot || !AGV || !Train)
    {
        if (World) World->DestroyWorld(false);
        return false;
    }

    TestTrue(TEXT("Player-built machine configures"), Machine->Configure(
        TEXT("BEACON-PR004"), ELBFactoryBuildMachineType::DepackagingRobot));
    ULBStatusBeaconComponent* MachineBeacon = FirstBeacon(Machine);
    TestTrue(TEXT("Idle player-built machine is amber"),
        MachineBeacon && MachineBeacon->GetStatus() == ELBStatusBeaconState::Idle);
    TestTrue(TEXT("Player-built machine accepts identified input"),
        Machine->AcceptInputUnit(TEXT("COIL-BEACON-001")));
    TestTrue(TEXT("Ready player-built machine is green"),
        MachineBeacon && MachineBeacon->GetStatus() == ELBStatusBeaconState::Ready);
    TestTrue(TEXT("Two-step process contract configures"), Machine->ConfigureGameplayProcessSteps(2));
    FName OutUnit;
    bool bCompleted = false;
    TestTrue(TEXT("First automatic step begins processing"),
        Machine->AdvanceAutomaticProcess(OutUnit, bCompleted));
    TestTrue(TEXT("Processing player-built machine stays green"),
        MachineBeacon && MachineBeacon->GetStatus() == ELBStatusBeaconState::Running);

    FLBSupportRobotSaveState DockedRobot;
    DockedRobot.UnitId = TEXT("LB-CR01-BEACON");
    DockedRobot.VariantId = TEXT("LB-CR01");
    DockedRobot.State = ELBSupportRobotState::Docked;
    DockedRobot.Condition = ELBSupportRobotCondition::Commissioned;
    DockedRobot.BatteryStateOfChargePercent = 100.0f;
    DockedRobot.BatteryHealthPercent = 100.0f;
    DockedRobot.bCertified = true;
    DockedRobot.bDocked = true;
    DockedRobot.DockId = TEXT("LB-DOCK-CR01-BEACON");
    DockedRobot.SavedTransform = FTransform::Identity;
    TestTrue(TEXT("Support robot restores safely docked"), Robot->RestoreCommonSaveState(DockedRobot));
    ULBStatusBeaconComponent* RobotBeacon = FirstBeacon(Robot);
    TestTrue(TEXT("Docked support robot is amber"),
        RobotBeacon && RobotBeacon->GetStatus() == ELBStatusBeaconState::Waiting);
    Robot->RaiseCommonFault(ELBSupportRobotFault::SafetyNetworkUnhealthy,
        TEXT("Beacon contract fault"));
    TestTrue(TEXT("Support robot fault is red"),
        RobotBeacon && RobotBeacon->GetStatus() == ELBStatusBeaconState::Fault);

    TestTrue(TEXT("Coil AGV binds its owned presentation"), AGV->DiscoverAndBind());
    ULBStatusBeaconComponent* AGVBeacon = FirstBeacon(AGV);
    TestTrue(TEXT("Loaded stationary AGV is amber"),
        AGVBeacon && AGVBeacon->GetStatus() == ELBStatusBeaconState::Idle);
    TestTrue(TEXT("Coil AGV dispatch starts"), AGV->StartDispatch(TEXT("COIL-BEACON-002")));
    TestTrue(TEXT("Moving AGV uses flashing amber"),
        AGVBeacon && AGVBeacon->GetStatus() == ELBStatusBeaconState::Moving
            && AGVBeacon->IsFlashing());
    AGV->SetSafetyInputs(true, true, true, true, true, true, false);
    TestTrue(TEXT("AGV emergency-circuit fault uses flashing red"),
        AGVBeacon && AGVBeacon->GetStatus() == ELBStatusBeaconState::Emergency
            && AGVBeacon->IsFlashing());

    TArray<ULBStatusBeaconComponent*> TrainBeacons;
    Train->GetComponents(TrainBeacons);
    TestEqual(TEXT("Press train has a working stack at all seven cells"), TrainBeacons.Num(), 7);
    Train->SetControlPower(true);
    bool bAllTrainReady = TrainBeacons.Num() == 7;
    for (const ULBStatusBeaconComponent* Beacon : TrainBeacons)
        bAllTrainReady &= Beacon && Beacon->GetStatus() == ELBStatusBeaconState::Ready;
    TestTrue(TEXT("Powered ready press train makes every cell green"), bAllTrainReady);
    Train->SetEmergencyStopActive(true);
    bool bAllTrainEmergency = TrainBeacons.Num() == 7;
    for (const ULBStatusBeaconComponent* Beacon : TrainBeacons)
        bAllTrainEmergency &= Beacon && Beacon->GetStatus() == ELBStatusBeaconState::Emergency
            && Beacon->IsFlashing();
    TestTrue(TEXT("Emergency stop makes every press-cell beacon flash red"), bAllTrainEmergency);

    World->DestroyWorld(false);
    return true;
}

#endif
