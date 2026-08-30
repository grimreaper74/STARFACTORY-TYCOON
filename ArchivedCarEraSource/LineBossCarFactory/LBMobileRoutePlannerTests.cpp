#if WITH_DEV_AUTOMATION_TESTS

#include "Misc/AutomationTest.h"

#include "LBFactoryBuildMachine.h"
#include "LBMobileRoutePlanner.h"
#include "LBPressShopStorageZone.h"
#include "LBSupportRobot.h"

#include "Components/BoxComponent.h"
#include "Engine/Engine.h"
#include "Engine/World.h"

IMPLEMENT_SIMPLE_AUTOMATION_TEST(
    FLBMobileRoutePlannerMachineStorageClearanceTest,
    "LineBoss.MobileRoutes.SupportRobots.PlayerBuiltEnvelopeClearance",
    EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)

IMPLEMENT_SIMPLE_AUTOMATION_TEST(
    FLBSupportRobotNaturalCorneringTest,
    "LineBoss.MobileRoutes.SupportRobots.NaturalCornering",
    EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)

namespace
{
    bool CommissionRobot(ALBSupportRobot* Robot, const FVector& Start)
    {
        if (!Robot)
        {
            return false;
        }
        FLBSupportRobotSaveState Saved;
        Saved.UnitId = TEXT("RP01-NATURAL-MOTION-TEST");
        Saved.VariantId = TEXT("LB-RP01");
        Saved.Condition = ELBSupportRobotCondition::Restored;
        Saved.State = ELBSupportRobotState::Certified;
        Saved.BatteryStateOfChargePercent = 100.0f;
        Saved.BatteryHealthPercent = 100.0f;
        Saved.bCertified = true;
        Saved.SavedTransform = FTransform(FRotator::ZeroRotator, Start);
        if (!Robot->RestoreCommonSaveState(Saved))
        {
            return false;
        }
        Robot->SetSafetyHealth(true, true);
        Robot->SetRouteEnvironment(true, false, false, false);
        return Robot->ClearCommonFault() && Robot->BeginRouteValidation() && Robot->CertifyRobot();
    }

    FLBSupportRobotRoute MakeRoute(const FName RouteId, const TArray<FVector>& Waypoints)
    {
        FLBSupportRobotRoute Route;
        Route.RouteId = RouteId;
        Route.Revision = 1;
        Route.bCertified = true;
        Route.SpeedClass = ELBRouteSpeedClass::NormalTransit;
        Route.Waypoints = Waypoints;
        return Route;
    }

    void DestroyTestWorld(UWorld* World)
    {
        if (!World)
        {
            return;
        }
        World->DestroyWorld(false);
        GEngine->DestroyWorldContext(World);
    }
}

bool FLBMobileRoutePlannerMachineStorageClearanceTest::RunTest(const FString& Parameters)
{
    UWorld* World = UWorld::CreateWorld(EWorldType::Game, false, TEXT("LB_MobileRoute_EnvelopeClearance"));
    TestNotNull(TEXT("Transient runtime world created"), World);
    if (!World)
    {
        return false;
    }
    FWorldContext& WorldContext = GEngine->CreateNewWorldContext(EWorldType::Game);
    WorldContext.SetCurrentWorld(World);
    World->InitializeActorsForPlay(FURL());
    World->BeginPlay();

    ALBFactoryBuildMachine* Machine = World->SpawnActor<ALBFactoryBuildMachine>(
        ALBFactoryBuildMachine::StaticClass(), FVector(700.0f, 0.0f, 182.0f), FRotator(0.0f, 18.0f, 0.0f));
    ALBPressShopStorageZone* Storage = World->SpawnActor<ALBPressShopStorageZone>(
        ALBPressShopStorageZone::StaticClass(), FVector(1325.0f, 0.0f, 100.0f), FRotator(0.0f, -12.0f, 0.0f));
    TestTrue(TEXT("Player-built machine fixture configures"), Machine
        && Machine->Configure(TEXT("PR002-ROUTE-TEST"), ELBFactoryBuildMachineType::CoilWeighInspectionCell));
    TestTrue(TEXT("Player-built storage fixture configures"), Storage
        && Storage->Configure(TEXT("STORAGE-ROUTE-TEST"), ELBPressShopStorageType::MaintenanceParts,
            4, FVector(170.0f, 190.0f, 100.0f)));

    const FVector Start(0.0f, 0.0f, 55.0f);
    const FVector Destination(2050.0f, 0.0f, 55.0f);
    LBMobileRoutePlanner::FSettings Settings;
    Settings.VehicleHalfExtentCm = FVector2D(76.0f, 46.5f);
    Settings.EnvelopeClearanceCm = 40.0f;
    Settings.CornerRadiusCm = 150.0f;
    Settings.MaximumCurveStepDegrees = 12.0f;
    TArray<FVector> PlannedPath;
    TestTrue(TEXT("Planner finds a path around both player-built envelopes"),
        LBMobileRoutePlanner::BuildClearanceAwarePath(World, Start, {Destination}, Settings, PlannedPath));
    TestTrue(TEXT("Blocked straight line expands into a curved multi-point route"), PlannedPath.Num() > 4);
    float MaximumLateralDetour = 0.0f;
    for (const FVector& Point : PlannedPath)
    {
        MaximumLateralDetour = FMath::Max(MaximumLateralDetour, FMath::Abs(Point.Y));
    }
    TestTrue(TEXT("Derived route visibly clears the machine/storage corridor"), MaximumLateralDetour > 350.0f);

    ALBSupportRobot* Robot = World->SpawnActor<ALBSupportRobot>(
        ALBSupportRobot::StaticClass(), Start, FRotator::ZeroRotator);
    TestTrue(TEXT("Support robot commissions"), CommissionRobot(Robot, Start));
    TestTrue(TEXT("Certified mission starts with runtime envelope avoidance"), Robot
        && Robot->BeginCertifiedRoute(MakeRoute(TEXT("RP01-PLAYER-BUILT-DETOUR"), {Destination}), false));
    TestTrue(TEXT("Runtime route retains generated curve samples"), Robot
        && Robot->GetActiveRuntimeRoutePointCount() > 4);

    float ObservedLateralTravel = 0.0f;
    float MaximumYawStep = 0.0f;
    float PreviousYaw = Robot ? Robot->GetActorRotation().Yaw : 0.0f;
    for (int32 Step = 0; Robot && Step < 1000 && Robot->HasRouteAuthority(); ++Step)
    {
        Robot->Tick(0.05f);
        ObservedLateralTravel = FMath::Max(ObservedLateralTravel, FMath::Abs(Robot->GetActorLocation().Y));
        const float CurrentYaw = Robot->GetActorRotation().Yaw;
        MaximumYawStep = FMath::Max(MaximumYawStep,
            FMath::Abs(FMath::FindDeltaAngleDegrees(PreviousYaw, CurrentYaw)));
        PreviousYaw = CurrentYaw;
    }
    TestTrue(TEXT("Robot physically follows the lateral detour instead of crossing the assets"),
        ObservedLateralTravel > 250.0f);
    TestTrue(TEXT("Steering rate remains continuous at generated corners"), MaximumYawStep <= 3.65f);
    TestFalse(TEXT("Robot completes without a collision safety stop"), Robot && Robot->HasRouteAuthority());
    TestEqual(TEXT("Completed clearance-aware mission returns robot to certified idle"),
        Robot ? Robot->GetRobotState() : ELBSupportRobotState::Fault, ELBSupportRobotState::Certified);
    TestTrue(TEXT("Robot arrives at the certified destination"), Robot
        && FVector::Dist2D(Robot->GetActorLocation(), Destination) <= 30.0f);

    DestroyTestWorld(World);
    return true;
}

bool FLBSupportRobotNaturalCorneringTest::RunTest(const FString& Parameters)
{
    UWorld* World = UWorld::CreateWorld(EWorldType::Game, false, TEXT("LB_SupportRobot_NaturalCornering"));
    TestNotNull(TEXT("Transient runtime world created"), World);
    if (!World)
    {
        return false;
    }
    FWorldContext& WorldContext = GEngine->CreateNewWorldContext(EWorldType::Game);
    WorldContext.SetCurrentWorld(World);
    World->InitializeActorsForPlay(FURL());
    World->BeginPlay();

    const FVector Start(0.0f, 0.0f, 55.0f);
    ALBSupportRobot* Robot = World->SpawnActor<ALBSupportRobot>(
        ALBSupportRobot::StaticClass(), Start, FRotator::ZeroRotator);
    TestTrue(TEXT("Support robot commissions"), CommissionRobot(Robot, Start));
    const TArray<FVector> CertifiedPoints = {
        FVector(500.0f, 0.0f, 55.0f),
        FVector(500.0f, 500.0f, 55.0f),
        FVector(1000.0f, 500.0f, 55.0f)};
    TestTrue(TEXT("Right-angle certified route starts"), Robot
        && Robot->BeginCertifiedRoute(MakeRoute(TEXT("RP01-SMOOTH-CORNERS"), CertifiedPoints), false));
    TestTrue(TEXT("Hard route vertices become sampled arcs"), Robot
        && Robot->GetActiveRuntimeRoutePointCount() > CertifiedPoints.Num());

    bool bTurnedBeforeHardVertex = false;
    bool bTranslatedWhileTurning = false;
    float MaximumYawStep = 0.0f;
    float MaximumSpeedIncrease = 0.0f;
    float MaximumSpeedDecrease = 0.0f;
    float PreviousYaw = 0.0f;
    float PreviousSpeed = 0.0f;
    for (int32 Step = 0; Robot && Step < 900 && Robot->HasRouteAuthority(); ++Step)
    {
        Robot->Tick(0.05f);
        const FVector Location = Robot->GetActorLocation();
        const float Yaw = Robot->GetActorRotation().Yaw;
        const float Speed = Robot->GetCurrentSpeedMetresPerSecond();
        bTurnedBeforeHardVertex |= Location.X < 500.0f && Location.X > 300.0f
            && FMath::Abs(Yaw) > 2.0f && FMath::Abs(Location.Y) > 1.0f;
        bTranslatedWhileTurning |= Speed > 0.10f && FMath::Abs(Yaw) > 8.0f && FMath::Abs(Yaw) < 82.0f;
        MaximumYawStep = FMath::Max(MaximumYawStep,
            FMath::Abs(FMath::FindDeltaAngleDegrees(PreviousYaw, Yaw)));
        MaximumSpeedIncrease = FMath::Max(MaximumSpeedIncrease, Speed - PreviousSpeed);
        MaximumSpeedDecrease = FMath::Max(MaximumSpeedDecrease, PreviousSpeed - Speed);
        PreviousYaw = Yaw;
        PreviousSpeed = Speed;
    }

    TestTrue(TEXT("Robot bends into the corner before the old 90-degree pivot point"), bTurnedBeforeHardVertex);
    TestTrue(TEXT("Robot traverses the corner instead of stopping for an instant pivot"), bTranslatedWhileTurning);
    TestTrue(TEXT("Yaw changes respect the continuous steering-rate cap"), MaximumYawStep <= 3.65f);
    TestTrue(TEXT("Acceleration is rate limited"), MaximumSpeedIncrease <= 0.041f);
    TestTrue(TEXT("Deceleration is rate limited"), MaximumSpeedDecrease <= 0.061f);
    TestEqual(TEXT("Curved route completes normally"),
        Robot ? Robot->GetRobotState() : ELBSupportRobotState::Fault, ELBSupportRobotState::Certified);
    TestTrue(TEXT("Robot reaches the final certified point"), Robot
        && FVector::Dist2D(Robot->GetActorLocation(), CertifiedPoints.Last()) <= 30.0f);

    DestroyTestWorld(World);
    return true;
}

#endif

