#if WITH_DEV_AUTOMATION_TESTS

#include "Misc/AutomationTest.h"

#include "LBCleaningAMR.h"
#include "LBMaintenanceAMR.h"
#include "Components/BoxComponent.h"
#include "Components/ChildActorComponent.h"
#include "Components/PoseableMeshComponent.h"
#include "Components/PrimitiveComponent.h"
#include "Components/SceneComponent.h"
#include "Components/SpotLightComponent.h"
#include "Engine/Engine.h"
#include "Engine/World.h"

IMPLEMENT_SIMPLE_AUTOMATION_TEST(
    FLBCR01FunctionalRuntimeTest,
    "LineBoss.SupportRobots.CR01.FunctionalRuntime",
    EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)

IMPLEMENT_SIMPLE_AUTOMATION_TEST(
    FLBMR01FunctionalRuntimeTest,
    "LineBoss.SupportRobots.MR01.FunctionalRuntime",
    EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)

IMPLEMENT_SIMPLE_AUTOMATION_TEST(
    FLBSupportRobotAutomaticChargingTest,
    "LineBoss.SupportRobots.Common.AutomaticCharging",
    EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)

namespace
{
    FString NormalizedComponentName(const UObject* Object)
    {
        FString Name = Object ? Object->GetName() : FString();
        Name.RemoveFromEnd(TEXT("_0"));
        Name.RemoveFromEnd(TEXT("_GEN_VARIABLE"));
        return Name;
    }

    USceneComponent* FindSceneComponent(AActor* Actor, const TCHAR* Name)
    {
        if (!Actor)
        {
            return nullptr;
        }
        TArray<USceneComponent*> Components;
        Actor->GetComponents(Components);
        for (USceneComponent* Component : Components)
        {
            if (NormalizedComponentName(Component).Contains(Name))
            {
                return Component;
            }
        }
        return nullptr;
    }

    bool CommissionForTest(ALBCleaningAMR* Robot, const FVector& Start)
    {
        FLBCleaningAMRSaveState Saved;
        Saved.Common.UnitId = TEXT("CR-01 001");
        Saved.Common.VariantId = TEXT("LB-CR01");
        Saved.Common.Condition = ELBSupportRobotCondition::Restored;
        Saved.Common.State = ELBSupportRobotState::Certified;
        Saved.Common.BatteryStateOfChargePercent = 100.0f;
        Saved.Common.BatteryHealthPercent = 100.0f;
        Saved.Common.bCertified = true;
        Saved.Common.SavedTransform = FTransform(FRotator::ZeroRotator, Start);
        Saved.CleanWaterLitres = 100.0f;
        Saved.RecoveryWaterLitres = 0.0f;
        Saved.HopperLoadLitres = 0.0f;
        if (!Robot->RestoreSaveState(Saved))
        {
            return false;
        }
        Robot->SetSafetyHealth(true, true);
        Robot->SetRouteEnvironment(true, false, false, false);
        Robot->SetSensorCoverageCertified(true);
        return Robot->ClearCommonFault() && Robot->BeginRouteValidation() && Robot->CertifyRobot();
    }

    FLBSupportRobotRoute MakeRoute(FName Id, const FVector& Target)
    {
        FLBSupportRobotRoute Route;
        Route.RouteId = Id;
        Route.Revision = 1;
        Route.bCertified = true;
        Route.SpeedClass = ELBRouteSpeedClass::NormalTransit;
        Route.Waypoints.Add(Target);
        return Route;
    }

    bool CommissionForTest(ALBMaintenanceAMR* Robot, const FVector& Start)
    {
        FLBMaintenanceAMRSaveState Saved;
        Saved.Common.UnitId = TEXT("MR-01 001");
        Saved.Common.VariantId = TEXT("LB-MR01");
        Saved.Common.Condition = ELBSupportRobotCondition::Restored;
        Saved.Common.State = ELBSupportRobotState::Certified;
        Saved.Common.BatteryStateOfChargePercent = 100.0f;
        Saved.Common.BatteryHealthPercent = 100.0f;
        Saved.Common.bCertified = true;
        Saved.Common.SavedTransform = FTransform(FRotator::ZeroRotator, Start);
        Saved.ArmJointDegrees = {180.0f, -75.0f, 150.0f, 0.0f, 120.0f, 0.0f};
        Saved.ToolRackInventory = {
            ELBMaintenanceTool::T1_InspectionHead, ELBMaintenanceTool::T2_ConditionProbe,
            ELBMaintenanceTool::T3_Lubrication, ELBMaintenanceTool::T4_Cleaning,
            ELBMaintenanceTool::T5_ServiceGripper, ELBMaintenanceTool::T6_TorqueTool,
            ELBMaintenanceTool::T7_FluidLeak, ELBMaintenanceTool::T8_ModuleExchange};
        Saved.bArmParked = true;
        Saved.bMastStowed = true;
        Saved.bDoorsClosed = true;
        Saved.bPartsDrawerClosed = true;
        Saved.bPayloadSecured = true;
        if (!Robot->RestoreSaveState(Saved))
        {
            return false;
        }
        Robot->SetSafetyHealth(true, true);
        Robot->SetRouteEnvironment(true, false, false, false);
        return Robot->ClearCommonFault() && Robot->BeginRouteValidation() && Robot->CertifyRobot();
    }

    UStaticMeshComponent* FindTaggedStatic(AActor* Actor, const FName Tag)
    {
        TArray<UStaticMeshComponent*> Components;
        Actor->GetComponents(Components);
        for (UStaticMeshComponent* Component : Components)
        {
            if (Component && Component->ComponentHasTag(Tag))
            {
                return Component;
            }
        }
        return nullptr;
    }
}

bool FLBSupportRobotAutomaticChargingTest::RunTest(const FString& Parameters)
{
    UWorld* World = UWorld::CreateWorld(EWorldType::Game, false, FName(TEXT("LB_RP01_AutomaticChargingTest")));
    TestNotNull(TEXT("Transient runtime world created"), World);
    if (!World)
    {
        return false;
    }
    FWorldContext& WorldContext = GEngine->CreateNewWorldContext(EWorldType::Game);
    WorldContext.SetCurrentWorld(World);
    World->InitializeActorsForPlay(FURL());
    World->BeginPlay();

    ALBSupportRobot* Robot = World->SpawnActor<ALBSupportRobot>(
        ALBSupportRobot::StaticClass(), FVector(0.0f, 0.0f, 55.0f), FRotator::ZeroRotator);
    TestNotNull(TEXT("Common support robot spawns"), Robot);
    if (!Robot)
    {
        World->DestroyWorld(false);
        GEngine->DestroyWorldContext(World);
        return false;
    }

    FLBSupportRobotSaveState Saved;
    Saved.UnitId = TEXT("RP01-CHARGE-TEST");
    Saved.VariantId = TEXT("LB-RP01");
    Saved.Condition = ELBSupportRobotCondition::Restored;
    Saved.State = ELBSupportRobotState::Certified;
    Saved.BatteryStateOfChargePercent = 25.0f;
    Saved.BatteryHealthPercent = 100.0f;
    Saved.bCertified = true;
    Saved.SavedTransform = FTransform(FRotator::ZeroRotator, FVector(0.0f, 0.0f, 55.0f));
    TestTrue(TEXT("Low-charge safe state restores"), Robot->RestoreCommonSaveState(Saved));
    Robot->SetSafetyHealth(true, true);
    Robot->SetRouteEnvironment(true, false, false, true);
    TestTrue(TEXT("Restore fault clears"), Robot->ClearCommonFault());
    TestTrue(TEXT("Route validation begins"), Robot->BeginRouteValidation());
    TestTrue(TEXT("Robot recertifies"), Robot->CertifyRobot());

    FLBSupportRobotRoute ChargeRoute;
    ChargeRoute.RouteId = TEXT("RP01_AUTO_RETURN_DOCK_A");
    ChargeRoute.Revision = 1;
    ChargeRoute.bCertified = true;
    ChargeRoute.SpeedClass = ELBRouteSpeedClass::Docking;
    ChargeRoute.Waypoints.Add(FVector(120.0f, 0.0f, 55.0f));
    ChargeRoute.DestinationDockId = TEXT("RP01_DOCK_A");
    TestTrue(TEXT("Certified automatic charge route configures"),
        Robot->ConfigureAutomaticChargingRoute(ChargeRoute, 30.0f));

    Robot->Tick(0.05f);
    TestEqual(TEXT("Reserve charge starts autonomous return"),
        Robot->GetRobotState(), ELBSupportRobotState::Returning);
    for (int32 Step = 0; Step < 400 && !Robot->IsDocked(); ++Step)
    {
        Robot->Tick(0.05f);
    }
    TestTrue(TEXT("Robot reaches charging dock autonomously"), Robot->IsDocked());
    TestEqual(TEXT("Correct destination dock is retained"), Robot->GetDockId(), FName(TEXT("RP01_DOCK_A")));

    const float ChargeBefore = Robot->GetBatteryStateOfChargePercent();
    Robot->Tick(10.0f);
    TestTrue(TEXT("Docked battery charge increases"), Robot->GetBatteryStateOfChargePercent() > ChargeBefore);
    Robot->Tick(500.0f);
    TestEqual(TEXT("Automatic charging reaches full state"), Robot->GetBatteryStateOfChargePercent(), 100.0f);
    TestEqual(TEXT("Fully charged robot remains docked and available"),
        Robot->GetRobotState(), ELBSupportRobotState::Docked);

    World->DestroyWorld(false);
    GEngine->DestroyWorldContext(World);
    return true;
}

bool FLBCR01FunctionalRuntimeTest::RunTest(const FString& Parameters)
{
    UWorld* World = UWorld::CreateWorld(EWorldType::Game, false, FName(TEXT("LB_CR01_FunctionalRuntimeTest")));
    TestNotNull(TEXT("Transient runtime world created"), World);
    if (!World)
    {
        return false;
    }
    FWorldContext& WorldContext = GEngine->CreateNewWorldContext(EWorldType::Game);
    WorldContext.SetCurrentWorld(World);
    World->InitializeActorsForPlay(FURL());
    World->BeginPlay();

    UClass* CandidateClass = LoadClass<ALBCleaningAMR>(
        nullptr,
        TEXT("/Game/LineBoss/Robots/Cleaning/CR01/Candidate_v065/Blueprints/BP_LB_CR01_CleaningAMR_v065.BP_LB_CR01_CleaningAMR_v065_C"));
    TestNotNull(TEXT("v065 generated class loads"), CandidateClass);

    ALBCleaningAMR* Robot = CandidateClass
        ? World->SpawnActor<ALBCleaningAMR>(CandidateClass, FVector(0.0f, 0.0f, 56.0f), FRotator::ZeroRotator)
        : nullptr;
    TestNotNull(TEXT("v065 spawns in game world"), Robot);
    if (!Robot)
    {
        World->DestroyWorld(false);
        GEngine->DestroyWorldContext(World);
        return false;
    }
    TestTrue(TEXT("CR01 commissions from a safe restored state"), CommissionForTest(Robot, FVector(0.0f, 0.0f, 56.0f)));
    TestNotNull(TEXT("CR01 has a real left forward work light"), Robot->GetLeftForwardWorkLight());
    TestNotNull(TEXT("CR01 has a real right forward work light"), Robot->GetRightForwardWorkLight());
    TestNotNull(TEXT("CR01 has a real cleaning-deck work light"), Robot->GetCleaningDeckWorkLight());
    TestFalse(TEXT("CR01 forward lights are off while certified and parked"),
        Robot->GetLeftForwardWorkLight() && Robot->GetLeftForwardWorkLight()->IsVisible());

    UChildActorComponent* Presentation = Robot->FindComponentByClass<UChildActorComponent>();
    TestNotNull(TEXT("v056 presentation mount exists"), Presentation);
    AActor* PresentationActor = Presentation ? Presentation->GetChildActor() : nullptr;
    TestNotNull(TEXT("v056 presentation actor is instantiated"), PresentationActor);
    Robot->Tick(0.01f);
    int32 PresentationBlockersFound = 0;
    int32 EnabledPresentationBlockers = 0;
    if (PresentationActor)
    {
        TArray<UPrimitiveComponent*> Primitives;
        PresentationActor->GetComponents(Primitives);
        for (UPrimitiveComponent* Primitive : Primitives)
        {
            if (NormalizedComponentName(Primitive).Contains(TEXT("Collision_CR01_"))
                || Primitive->ComponentHasTag(TEXT("LB.CR01.Collision.Body")))
            {
                ++PresentationBlockersFound;
                if (Primitive->GetCollisionEnabled() != ECollisionEnabled::NoCollision)
                {
                    ++EnabledPresentationBlockers;
                }
            }
        }
    }
    AddInfo(FString::Printf(TEXT("Presentation blockers found=%d enabled=%d"),
        PresentationBlockersFound, EnabledPresentationBlockers));
    TestEqual(TEXT("presentation contributes no enabled blocking collision"), EnabledPresentationBlockers, 0);

    AActor* Obstacle = World->SpawnActor<AActor>(AActor::StaticClass(), FVector(260.0f, 0.0f, 56.0f), FRotator::ZeroRotator);
    UBoxComponent* ObstacleCollision = NewObject<UBoxComponent>(Obstacle, TEXT("CR01_TestObstacleCollision"));
    Obstacle->SetRootComponent(ObstacleCollision);
    Obstacle->AddInstanceComponent(ObstacleCollision);
    ObstacleCollision->SetBoxExtent(FVector(40.0f, 120.0f, 100.0f));
    ObstacleCollision->SetCollisionProfileName(TEXT("BlockAllDynamic"));
    ObstacleCollision->RegisterComponent();
    Obstacle->SetActorLocation(FVector(260.0f, 0.0f, 56.0f), false, nullptr, ETeleportType::TeleportPhysics);
    ObstacleCollision->SetWorldLocation(FVector(260.0f, 0.0f, 56.0f), false, nullptr, ETeleportType::TeleportPhysics);
    AddInfo(FString::Printf(TEXT("Authority root=%s enabled=%d robot=%s obstacle=%s"),
        *Robot->GetRootComponent()->GetName(),
        static_cast<int32>(Robot->GetRootComponent()->GetCollisionEnabled()),
        *Robot->GetActorLocation().ToString(), *ObstacleCollision->GetComponentLocation().ToString()));
    TestEqual(TEXT("authority collision blocks world dynamic"),
        Robot->GetRootComponent()->GetCollisionResponseToChannel(ECC_WorldDynamic), ECR_Block);
    TestEqual(TEXT("obstacle blocks pawn channel"),
        ObstacleCollision->GetCollisionResponseToChannel(ECC_Pawn), ECR_Block);

    TestTrue(TEXT("certified route starts"), Robot->BeginCertifiedRoute(MakeRoute(TEXT("CR01_TEST_BLOCKED"), FVector(600.0f, 0.0f, 56.0f)), false));
    for (int32 Step = 0; Step < 160 && Robot->GetRobotState() != ELBSupportRobotState::Blocked; ++Step)
    {
        Robot->Tick(0.05f);
    }
    AddInfo(FString::Printf(TEXT("After obstacle route state=%d location=%s authority=%d"),
        static_cast<int32>(Robot->GetRobotState()), *Robot->GetActorLocation().ToString(), Robot->HasRouteAuthority() ? 1 : 0));
    TestEqual(TEXT("swept collision produces blocked state"), Robot->GetRobotState(), ELBSupportRobotState::Blocked);
    TestFalse(TEXT("blocked collision revokes route authority"), Robot->HasRouteAuthority());
    TestTrue(TEXT("robot does not tunnel through obstacle"), Robot->GetActorLocation().X < 220.0f);

    Obstacle->Destroy();
    TestTrue(TEXT("blocked robot recommissions"), CommissionForTest(Robot, FVector(0.0f, 0.0f, 56.0f)));
    TestTrue(TEXT("cleaning route starts"), Robot->BeginCertifiedRoute(MakeRoute(TEXT("CR01_TEST_CLEAN"), FVector(1200.0f, 0.0f, 56.0f)), false));
    TestTrue(TEXT("CR01 forward lamps illuminate while travelling"),
        Robot->GetLeftForwardWorkLight() && Robot->GetLeftForwardWorkLight()->IsVisible()
        && Robot->GetRightForwardWorkLight() && Robot->GetRightForwardWorkLight()->IsVisible());
    TestTrue(TEXT("cleaning task starts"), Robot->StartCleaningTask(TEXT("CLEAN_TEST_001"), TEXT("ZONE_TEST_001")));
    TestTrue(TEXT("CR01 deck flood illuminates during active cleaning"),
        Robot->GetCleaningDeckWorkLight() && Robot->GetCleaningDeckWorkLight()->IsVisible());
    for (int32 Step = 0; Step < 30; ++Step)
    {
        Robot->Tick(0.05f);
    }
    USceneComponent* SideBrushArm = FindSceneComponent(PresentationActor, TEXT("PVT_SideBrushArm_L"));
    USceneComponent* ScrubDeck = FindSceneComponent(PresentationActor, TEXT("PVT_ScrubDeckLift"));
    TestNotNull(TEXT("presentation side-brush pivot is bound"), SideBrushArm);
    TestNotNull(TEXT("presentation scrub-deck pivot is bound"), ScrubDeck);
    if (SideBrushArm)
    {
        TestTrue(TEXT("visible side brush deploys"), SideBrushArm->GetRelativeRotation().Yaw < -60.0f);
    }
    if (ScrubDeck)
    {
        TestTrue(TEXT("visible scrub deck lowers"), ScrubDeck->GetRelativeLocation().Z < 20.0f);
    }

    const FLBCleaningAMRSaveState SavedWhileCleaning = Robot->CaptureSaveState();
    ALBCleaningAMR* Reloaded = World->SpawnActor<ALBCleaningAMR>(CandidateClass, FVector(0.0f, 300.0f, 56.0f), FRotator::ZeroRotator);
    TestNotNull(TEXT("reload target spawns"), Reloaded);
    if (Reloaded)
    {
        TestTrue(TEXT("cleaning save state restores"), Reloaded->RestoreSaveState(SavedWhileCleaning));
        TestFalse(TEXT("save reload never restores route authority"), Reloaded->HasRouteAuthority());
        TestEqual(TEXT("save reload returns to safety stop"), Reloaded->GetRobotState(), ELBSupportRobotState::SafetyStop);
        TestEqual(TEXT("save reload restores stopped speed"), Reloaded->GetCurrentSpeedMetresPerSecond(), 0.0f);
        TestFalse(TEXT("save reload cannot silently resume cleaning"), Reloaded->StartCleaningTask(TEXT("ILLEGAL_RESUME"), TEXT("ZONE_TEST_001")));
    }

    World->DestroyWorld(false);
    GEngine->DestroyWorldContext(World);
    return true;
}

bool FLBMR01FunctionalRuntimeTest::RunTest(const FString& Parameters)
{
    UWorld* World = UWorld::CreateWorld(EWorldType::Game, false, FName(TEXT("LB_MR01_FunctionalRuntimeTest")));
    TestNotNull(TEXT("Transient MR01 runtime world created"), World);
    if (!World)
    {
        return false;
    }
    FWorldContext& WorldContext = GEngine->CreateNewWorldContext(EWorldType::Game);
    WorldContext.SetCurrentWorld(World);
    World->InitializeActorsForPlay(FURL());
    World->BeginPlay();

    UClass* CandidateClass = LoadClass<ALBMaintenanceAMR>(
        nullptr,
        TEXT("/Game/LineBoss/Robots/Maintenance/MR01/Candidate_v022/Blueprints/BP_LB_MR01_MaintenanceAMR_v022.BP_LB_MR01_MaintenanceAMR_v022_C"));
    TestNotNull(TEXT("v022 straight-dock generated class fresh-loads"), CandidateClass);
    ALBMaintenanceAMR* Robot = CandidateClass
        ? World->SpawnActor<ALBMaintenanceAMR>(CandidateClass, FVector(0.0f, 0.0f, 62.5f), FRotator::ZeroRotator)
        : nullptr;
    TestNotNull(TEXT("v022 straight-dock candidate spawns in a game world"), Robot);
    if (!Robot)
    {
        World->DestroyWorld(false);
        GEngine->DestroyWorldContext(World);
        return false;
    }

    UPoseableMeshComponent* Arm = nullptr;
    TArray<UPoseableMeshComponent*> Poseables;
    Robot->GetComponents(Poseables);
    for (UPoseableMeshComponent* Component : Poseables)
    {
        if (Component && Component->ComponentHasTag(TEXT("LB.MR01.ArmPoseable")))
        {
            Arm = Component;
            break;
        }
    }
    UStaticMeshComponent* Sleeve = FindTaggedStatic(Robot, TEXT("LB.MR01.ArmLiftSleeve"));
    UStaticMeshComponent* Carriage = FindTaggedStatic(Robot, TEXT("LB.MR01.ArmLiftCarriage"));
    UStaticMeshComponent* StoredT6 = FindTaggedStatic(Robot, TEXT("LB.MR01.Tool.T6.Stored"));
    UStaticMeshComponent* EquippedT6 = FindTaggedStatic(Robot, TEXT("LB.MR01.Tool.T6.Equipped"));
    TestNotNull(TEXT("ten-bone poseable arm presentation exists"), Arm);
    TestNotNull(TEXT("connected half-stroke sleeve exists"), Sleeve);
    TestNotNull(TEXT("connected full-stroke carriage exists"), Carriage);
    TestNotNull(TEXT("stored T6 visual exists"), StoredT6);
    TestNotNull(TEXT("equipped T6 visual exists"), EquippedT6);
    AddInfo(FString::Printf(TEXT("MR01 actor begun-play=%d"), Robot->HasActorBegunPlay() ? 1 : 0));
    Robot->Tick(0.001f);
    if (Arm)
    {
        const FVector ParkedShoulder = Arm->GetBoneTransformByName(
            TEXT("j2_shoulder"), EBoneSpaces::ComponentSpace).GetLocation();
        const FVector ParkedElbow = Arm->GetBoneTransformByName(
            TEXT("j3_elbow"), EBoneSpaces::ComponentSpace).GetLocation();
        const FVector ParkedTcp = Arm->GetBoneTransformByName(
            TEXT("tcp"), EBoneSpaces::ComponentSpace).GetLocation();
        TestTrue(TEXT("corrected shoulder axis folds parked elbow upward"),
            ParkedElbow.Z > ParkedShoulder.Z + 40.0f);
        TestTrue(TEXT("compact parked chain returns TCP below raised elbow"),
            ParkedTcp.Z < ParkedElbow.Z - 40.0f);
    }
    const FLBMaintenanceAMRSaveState InitialParkedState = Robot->CaptureSaveState();
    TestTrue(TEXT("MR01 begins with exact compact six-axis parked authority"),
        InitialParkedState.bArmParked
        && InitialParkedState.ArmJointDegrees.Num() == 6
        && FMath::IsNearlyEqual(InitialParkedState.ArmJointDegrees[0], 180.0f)
        && FMath::IsNearlyEqual(InitialParkedState.ArmJointDegrees[1], -75.0f)
        && FMath::IsNearlyEqual(InitialParkedState.ArmJointDegrees[2], 150.0f)
        && FMath::IsNearlyEqual(InitialParkedState.ArmJointDegrees[4], 120.0f));

    int32 WheelVisuals = 0;
    int32 WheelVisualsOnNativePivots = 0;
    TArray<UStaticMeshComponent*> Statics;
    Robot->GetComponents(Statics);
    for (UStaticMeshComponent* Component : Statics)
    {
        if (!Component)
        {
            continue;
        }
        bool bWheelVisual = false;
        for (const FName Tag : Component->ComponentTags)
        {
            if (Tag.ToString().StartsWith(TEXT("LB.MR01.WheelRole.")))
            {
                bWheelVisual = true;
                break;
            }
        }
        if (bWheelVisual)
        {
            ++WheelVisuals;
            if (Component->GetAttachParent() && Component->GetAttachParent()->GetName().Contains(TEXT("PVT_Wheel_")))
            {
                ++WheelVisualsOnNativePivots;
            }
        }
    }
    TestEqual(TEXT("exactly sixteen shared wheel/rim/hub/bearing visuals"), WheelVisuals, 16);
    TestEqual(TEXT("all wheel visuals attach to native corner pivots"), WheelVisualsOnNativePivots, 16);
    TestTrue(TEXT("MR01 commissions from a safe restored state"), CommissionForTest(Robot, FVector(0.0f, 0.0f, 62.5f)));
    TestNotNull(TEXT("MR01 has a real left forward work light"), Robot->GetLeftForwardWorkLight());
    TestNotNull(TEXT("MR01 has a real right forward work light"), Robot->GetRightForwardWorkLight());
    TestNotNull(TEXT("MR01 has a real upper-body task light"), Robot->GetToolTaskWorkLight());
    TestFalse(TEXT("MR01 task light is off while certified and parked"),
        Robot->GetToolTaskWorkLight() && Robot->GetToolTaskWorkLight()->IsVisible());

    Robot->SetWorkPermissives(TEXT("PR004_MAINT_01"), TEXT("PERMIT_MR01_T6_001"),
        true, true, true, true, true, true, false);
    TestTrue(TEXT("four proved outriggers deploy"), Robot->SetOutriggersDeployed(true, {100.0f, 100.0f, 100.0f, 100.0f}));
    TestTrue(TEXT("T6 tool change begins from indexed rack slot six"), Robot->BeginToolChange(6, ELBMaintenanceTool::T6_TorqueTool));
    TestTrue(TEXT("T6 tool identity, presence, lock and withdrawal prove"),
        Robot->CompleteToolChange(6, ELBMaintenanceTool::T6_TorqueTool, true, true, 350.0f));
    TestTrue(TEXT("stored T6 becomes hidden"), StoredT6 && !StoredT6->IsVisible() && StoredT6->bHiddenInGame);
    TestTrue(TEXT("equipped T6 becomes visible"), EquippedT6 && EquippedT6->IsVisible() && !EquippedT6->bHiddenInGame);
    TestTrue(TEXT("equipped T6 remains parented to poseable arm"), EquippedT6 && EquippedT6->GetAttachParent() == Arm);
    TestEqual(TEXT("equipped T6 uses authored tool coupler bone"), EquippedT6 ? EquippedT6->GetAttachSocketName() : NAME_None, FName(TEXT("tool_coupler")));

    TestTrue(TEXT("approved fastener task begins with T6"),
        Robot->BeginMaintenanceTask(ELBMaintenanceTask::ApprovedFastenerService, TEXT("MR01_FASTENER_001"), false));
    TestTrue(TEXT("MR01 forward lamps illuminate during approved work"),
        Robot->GetLeftForwardWorkLight() && Robot->GetLeftForwardWorkLight()->IsVisible()
        && Robot->GetRightForwardWorkLight() && Robot->GetRightForwardWorkLight()->IsVisible());
    TestTrue(TEXT("MR01 task lamp illuminates during approved work"),
        Robot->GetToolTaskWorkLight() && Robot->GetToolTaskWorkLight()->IsVisible());
    const FVector InitialLiftBone = Arm
        ? Arm->GetBoneTransformByName(TEXT("lift"), EBoneSpaces::ComponentSpace).GetLocation()
        : FVector::ZeroVector;
    TestTrue(TEXT("400 mm machine-reach pose command accepted"),
        Robot->CommandArmPose(400.0f, {170.0f, 0.0f, 0.0f, 0.0f, 0.0f, 0.0f}));
    for (int32 Step = 0; Step < 180; ++Step)
    {
        Robot->Tick(0.05f);
    }

    const FLBMaintenanceAMRSaveState WorkingState = Robot->CaptureSaveState();
    const FVector RaisedLiftBone = Arm
        ? Arm->GetBoneTransformByName(TEXT("lift"), EBoneSpaces::ComponentSpace).GetLocation()
        : FVector::ZeroVector;
    AddInfo(FString::Printf(TEXT("MR01 lift evidence authority=%.3f bone_initial=%s bone_raised=%s sleeve=%s carriage=%s"),
        WorkingState.ArmLiftMillimetres, *InitialLiftBone.ToString(), *RaisedLiftBone.ToString(),
        Sleeve ? *Sleeve->GetRelativeLocation().ToString() : TEXT("missing"),
        Carriage ? *Carriage->GetRelativeLocation().ToString() : TEXT("missing")));
    TestTrue(TEXT("authority reaches full 400 mm lift"), FMath::IsNearlyEqual(WorkingState.ArmLiftMillimetres, 400.0f, 0.2f));
    TestTrue(TEXT("poseable lift bone rises 400 mm"), FMath::IsNearlyEqual(RaisedLiftBone.Z - InitialLiftBone.Z, 40.0f, 0.2f));
    TestTrue(TEXT("nested sleeve rises half stroke"), Sleeve && FMath::IsNearlyEqual(Sleeve->GetRelativeLocation().Z, 20.0f, 0.2f));
    TestTrue(TEXT("connected carriage rises full stroke"), Carriage && FMath::IsNearlyEqual(Carriage->GetRelativeLocation().Z, 40.0f, 0.2f));
    TestEqual(TEXT("working state retains T6 identity"), WorkingState.ActiveTool, ELBMaintenanceTool::T6_TorqueTool);

    ALBMaintenanceAMR* Reloaded = World->SpawnActor<ALBMaintenanceAMR>(CandidateClass, FVector(0.0f, 300.0f, 62.5f), FRotator::ZeroRotator);
    TestNotNull(TEXT("MR01 save reload target spawns"), Reloaded);
    if (Reloaded)
    {
        TestTrue(TEXT("MR01 working save state restores"), Reloaded->RestoreSaveState(WorkingState));
        const FLBMaintenanceAMRSaveState Restored = Reloaded->CaptureSaveState();
        TestEqual(TEXT("save reload restores T6 identity"), Restored.ActiveTool, ELBMaintenanceTool::T6_TorqueTool);
        TestTrue(TEXT("save reload restores 400 mm lift"), FMath::IsNearlyEqual(Restored.ArmLiftMillimetres, 400.0f, 0.2f));
        TestFalse(TEXT("save reload never restores route authority"), Reloaded->HasRouteAuthority());
        TestEqual(TEXT("save reload returns to safety stop"), Reloaded->GetRobotState(), ELBSupportRobotState::SafetyStop);
        UStaticMeshComponent* ReloadedStoredT6 = FindTaggedStatic(Reloaded, TEXT("LB.MR01.Tool.T6.Stored"));
        UStaticMeshComponent* ReloadedEquippedT6 = FindTaggedStatic(Reloaded, TEXT("LB.MR01.Tool.T6.Equipped"));
        TestTrue(TEXT("save reload keeps rack T6 hidden"), ReloadedStoredT6 && !ReloadedStoredT6->IsVisible());
        TestTrue(TEXT("save reload keeps coupler T6 visible"), ReloadedEquippedT6 && ReloadedEquippedT6->IsVisible());
    }

    ALBMaintenanceAMR* RouteRobot = World->SpawnActor<ALBMaintenanceAMR>(
        CandidateClass, FVector(0.0f, -300.0f, 62.5f), FRotator::ZeroRotator);
    TestNotNull(TEXT("MR01 collision/navigation instance spawns"), RouteRobot);
    if (RouteRobot)
    {
        RouteRobot->Tick(0.001f);
        UBoxComponent* AuthorityCollision = Cast<UBoxComponent>(RouteRobot->GetRootComponent());
        TestNotNull(TEXT("MR01 authority uses one box collision root"), AuthorityCollision);
        if (AuthorityCollision)
        {
            TestTrue(TEXT("MR01 collision envelope matches 1550x930x1250 mm contract"),
                AuthorityCollision->GetUnscaledBoxExtent().Equals(FVector(77.5f, 46.5f, 62.5f), 0.01f));
            TestEqual(TEXT("MR01 authority collision blocks dynamic factory obstacles"),
                AuthorityCollision->GetCollisionResponseToChannel(ECC_WorldDynamic), ECR_Block);
            TestTrue(TEXT("MR01 authority collision participates in navigation updates"),
                AuthorityCollision->CanEverAffectNavigation());
        }

        int32 EnabledPresentationCollision = 0;
        TArray<UPrimitiveComponent*> Primitives;
        RouteRobot->GetComponents(Primitives);
        for (UPrimitiveComponent* Primitive : Primitives)
        {
            if (Primitive && Primitive != AuthorityCollision
                && Primitive->GetCollisionEnabled() != ECollisionEnabled::NoCollision)
            {
                ++EnabledPresentationCollision;
            }
        }
        TestEqual(TEXT("MR01 presentation contributes no duplicate blocking collision"), EnabledPresentationCollision, 0);
        TestTrue(TEXT("MR01 route instance commissions"),
            CommissionForTest(RouteRobot, FVector(0.0f, -300.0f, 62.5f)));

        AActor* Obstacle = World->SpawnActor<AActor>(
            AActor::StaticClass(), FVector(260.0f, -300.0f, 62.5f), FRotator::ZeroRotator);
        UBoxComponent* ObstacleCollision = NewObject<UBoxComponent>(Obstacle, TEXT("MR01_TestObstacleCollision"));
        Obstacle->SetRootComponent(ObstacleCollision);
        Obstacle->AddInstanceComponent(ObstacleCollision);
        ObstacleCollision->SetBoxExtent(FVector(40.0f, 120.0f, 100.0f));
        ObstacleCollision->SetCollisionProfileName(TEXT("BlockAllDynamic"));
        ObstacleCollision->RegisterComponent();
        ObstacleCollision->SetWorldLocation(FVector(260.0f, -300.0f, 62.5f), false, nullptr, ETeleportType::TeleportPhysics);

        TestTrue(TEXT("MR01 certified route begins"), RouteRobot->BeginCertifiedRoute(
            MakeRoute(TEXT("MR01_TEST_BLOCKED"), FVector(600.0f, -300.0f, 62.5f)), false));
        for (int32 Step = 0; Step < 160 && RouteRobot->GetRobotState() != ELBSupportRobotState::Blocked; ++Step)
        {
            RouteRobot->Tick(0.05f);
        }
        TestEqual(TEXT("MR01 swept route collision enters blocked state"),
            RouteRobot->GetRobotState(), ELBSupportRobotState::Blocked);
        TestFalse(TEXT("MR01 blocked collision revokes route authority"), RouteRobot->HasRouteAuthority());
        TestTrue(TEXT("MR01 cannot tunnel through a factory obstacle"), RouteRobot->GetActorLocation().X < 220.0f);
    }

    World->DestroyWorld(false);
    GEngine->DestroyWorldContext(World);
    return true;
}

#endif
