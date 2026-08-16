#if WITH_DEV_AUTOMATION_TESTS

#include "Misc/AutomationTest.h"

#include "LBSupportRobot.h"
#include "LBSupportRobotServiceDock.h"
#include "Components/StaticMeshComponent.h"
#include "Engine/Engine.h"
#include "Engine/World.h"

IMPLEMENT_SIMPLE_AUTOMATION_TEST(
    FLBSupportRobotServiceDockRuntimeTest,
    "LineBoss.SupportRobots.ServiceDock.GuardedMechanismsAndSafeRestore",
    EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)

namespace
{
    UStaticMeshComponent* FindMesh(AActor* Actor, const TCHAR* Name)
    {
        TArray<UStaticMeshComponent*> Components;
        Actor->GetComponents(Components);
        for (UStaticMeshComponent* Component : Components)
        {
            if (Component && Component->GetName().Contains(Name))
            {
                return Component;
            }
        }
        return nullptr;
    }
}

bool FLBSupportRobotServiceDockRuntimeTest::RunTest(const FString& Parameters)
{
    UWorld* World = UWorld::CreateWorld(EWorldType::Game, false, FName(TEXT("LB_ServiceDock_RuntimeTest")));
    TestNotNull(TEXT("Transient runtime world created"), World);
    if (!World)
    {
        return false;
    }
    FWorldContext& WorldContext = GEngine->CreateNewWorldContext(EWorldType::Game);
    WorldContext.SetCurrentWorld(World);
    World->InitializeActorsForPlay(FURL());
    World->BeginPlay();

    ALBSupportRobot* Robot = World->SpawnActor<ALBSupportRobot>();
    ALBSupportRobotServiceDock* Dock = World->SpawnActor<ALBSupportRobotServiceDock>();
    TestNotNull(TEXT("Support robot spawns"), Robot);
    TestNotNull(TEXT("Service dock spawns"), Dock);
    if (!Robot || !Dock)
    {
        World->DestroyWorld(false);
        GEngine->DestroyWorldContext(World);
        return false;
    }

    const FName DockId(TEXT("LB-DOCK-MR01-TEST"));
    FLBSupportRobotSaveState RobotState;
    RobotState.UnitId = TEXT("LB-MR01-TEST");
    RobotState.VariantId = TEXT("LB-MR01");
    RobotState.State = ELBSupportRobotState::Docked;
    RobotState.Condition = ELBSupportRobotCondition::Commissioned;
    RobotState.BatteryStateOfChargePercent = 100.0f;
    RobotState.BatteryHealthPercent = 100.0f;
    RobotState.bCertified = true;
    RobotState.bDocked = true;
    RobotState.DockId = DockId;
    RobotState.SavedTransform = FTransform::Identity;
    TestTrue(TEXT("Compatible stopped MR01 restores docked"), Robot->RestoreCommonSaveState(RobotState));
    TestTrue(TEXT("Dock configures only while safely closed"), Dock->ConfigureDock(DockId, ELBServiceDockVariant::MR01_Maintenance));

    TestFalse(TEXT("Mechanisms reject service without permissives"), Dock->BeginServiceSequence());
    Dock->SetServicePermissives(true, true, true);
    TestTrue(TEXT("Correct docked MR01 and all permissives authorise opening"), Dock->BeginServiceSequence());
    TestEqual(TEXT("Dock enters opening state"), Dock->GetDockState(), ELBServiceDockState::Opening);
    Dock->Tick(2.5f);
    TestEqual(TEXT("Verified mechanism travel reaches service-ready"), Dock->GetDockState(), ELBServiceDockState::ServiceReady);

    UStaticMeshComponent* Probe = FindMesh(Dock, TEXT("CalibrationProbe"));
    UStaticMeshComponent* Door = FindMesh(Dock, TEXT("ToolRackDoor"));
    UStaticMeshComponent* Drawer = FindMesh(Dock, TEXT("WasteDrawer"));
    TestNotNull(TEXT("Calibration probe component exists"), Probe);
    TestNotNull(TEXT("Tool-rack door component exists"), Door);
    TestNotNull(TEXT("Waste drawer component exists"), Drawer);
    if (Probe && Door && Drawer)
    {
        TestEqual(TEXT("Probe uses authorised 180 mm X travel"), Probe->GetRelativeLocation().X, 18.0);
        TestEqual(TEXT("Tool door uses authorised 100 degree range"), Door->GetRelativeRotation().Yaw, 100.0);
        TestEqual(TEXT("Drawer uses authorised 450 mm withdrawal"), Drawer->GetRelativeLocation().Y, -45.0);
    }

    const FLBServiceDockSaveState OpenCapture = Dock->CaptureSaveState();
    TestEqual(TEXT("Powered/open state is absent from persistent payload"), OpenCapture.CompletedServiceCycles, 0);
    TestTrue(TEXT("Restore accepts exact dock identity"), Dock->RestoreSaveState(OpenCapture));
    TestEqual(TEXT("Restore is closed and de-energised"), Dock->GetDockState(), ELBServiceDockState::SafeClosed);
    if (Probe && Door && Drawer)
    {
        TestEqual(TEXT("Restored probe is retracted"), Probe->GetRelativeLocation().X, 0.0);
        TestEqual(TEXT("Restored tool door is shut"), Door->GetRelativeRotation().Yaw, 0.0);
        TestEqual(TEXT("Restored drawer is shut"), Drawer->GetRelativeLocation().Y, -90.0);
    }

    Dock->SetServicePermissives(true, true, true);
    TestTrue(TEXT("Second service sequence starts"), Dock->BeginServiceSequence());
    Dock->Tick(1.0f);
    Dock->SetServicePermissives(false, true, true);
    TestEqual(TEXT("Loss of safety zone forces a safety stop"), Dock->GetDockState(), ELBServiceDockState::SafetyStop);
    Dock->Tick(2.5f);
    TestEqual(TEXT("Safety stop physically returns closed"), Dock->GetDockState(), ELBServiceDockState::SafeClosed);

    FLBServiceDockSaveState WrongIdentity = Dock->CaptureSaveState();
    WrongIdentity.DockId = TEXT("OTHER-DOCK");
    TestFalse(TEXT("Cross-dock restore is rejected"), Dock->RestoreSaveState(WrongIdentity));

    World->DestroyWorld(false);
    GEngine->DestroyWorldContext(World);
    return true;
}

#endif
