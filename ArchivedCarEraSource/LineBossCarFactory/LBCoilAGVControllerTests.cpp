#if WITH_DEV_AUTOMATION_TESTS

#include "Misc/AutomationTest.h"
#include "LBCoilAGVController.h"
#include "LBFactoryAGVInfrastructure.h"
#include "LBFactoryBuildMachine.h"
#include "LBFactoryProcessPortComponent.h"
#include "Engine/Engine.h"
#include "Engine/StaticMeshActor.h"
#include "Engine/World.h"
#include "Components/BoxComponent.h"
#include "Components/StaticMeshComponent.h"

IMPLEMENT_SIMPLE_AUTOMATION_TEST(FLBCoilAGVRuntimeTest,
    "LineBoss.PressShop.PR003PR004.CoilAGVRuntime",
    EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)

IMPLEMENT_SIMPLE_AUTOMATION_TEST(FLBPlayerBuiltApprovedCoilAGVPresentationTest,
    "LineBoss.PressShop.PlayerBuilt.ApprovedCoilAGVPresentation",
    EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)

IMPLEMENT_SIMPLE_AUTOMATION_TEST(FLBCoilAGVProtectedRouteTest,
    "LineBoss.PressShop.PR003PR004.CoilAGVProtectedRoute",
    EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)

IMPLEMENT_SIMPLE_AUTOMATION_TEST(FLBLegacyInboundFreshWorldRestoreTest,
    "LineBoss.PressShop.Save.LegacyV2InboundAGVFreshWorldRestore",
    EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)

namespace
{
    struct FLBTransientAGVWorld
    {
        UWorld* World = nullptr;
        FLBTransientAGVWorld()
        {
            World = UWorld::CreateWorld(EWorldType::Game, false, TEXT("LB_CoilAGVTest"));
            if (World)
            {
                FWorldContext& Context = GEngine->CreateNewWorldContext(EWorldType::Game);
                Context.SetCurrentWorld(World);
                World->InitializeActorsForPlay(FURL());
                World->BeginPlay();
            }
        }
        ~FLBTransientAGVWorld()
        {
            if (World)
            {
                World->DestroyWorld(false);
                GEngine->DestroyWorldContext(World);
            }
        }
        AStaticMeshActor* SpawnTagged(const FVector& Location, std::initializer_list<FName> Tags) const
        {
            AStaticMeshActor* Actor = World->SpawnActor<AStaticMeshActor>(AStaticMeshActor::StaticClass(), Location, FRotator::ZeroRotator);
            if (Actor)
            {
                Actor->GetStaticMeshComponent()->SetMobility(EComponentMobility::Movable);
                for (const FName Tag : Tags) Actor->Tags.Add(Tag);
            }
            return Actor;
        }
    };
}

bool FLBCoilAGVRuntimeTest::RunTest(const FString& Parameters)
{
    FLBTransientAGVWorld TestWorld;
    TestNotNull(TEXT("Transient AGV world exists"), TestWorld.World);
    if (!TestWorld.World) return false;
    AStaticMeshActor* Chassis = TestWorld.SpawnTagged(FVector(0,0,29), {TEXT("LB.Vehicle.CoilAGV")});
    AStaticMeshActor* Deck = TestWorld.SpawnTagged(FVector(0,0,64), {TEXT("LB.Vehicle.CoilAGV.LiftDeck")});
    AStaticMeshActor* Load = TestWorld.SpawnTagged(FVector(0,0,156), {TEXT("LB.Inventory.InTransfer")});
    TestNotNull(TEXT("Tagged chassis exists"), Chassis);
    TestNotNull(TEXT("Tagged lift deck exists"), Deck);
    TestNotNull(TEXT("Tagged physical coil exists"), Load);
    ALBCoilAGVController* AGV = TestWorld.World->SpawnActor<ALBCoilAGVController>(ALBCoilAGVController::StaticClass(), FVector::ZeroVector, FRotator::ZeroRotator);
    TestNotNull(TEXT("Reusable AGV authority spawns"), AGV);
    TestTrue(TEXT("AGV binds chassis, deck and real load"), AGV && AGV->DiscoverAndBind());
    TestTrue(TEXT("Test route configures while idle"), AGV->ConfigureRoute(FVector(0,0,29),FVector(400,0,29),FVector(400,300,29)));
    TestEqual(TEXT("Direct route configuration has explicit manual ownership"),
        AGV->GetRouteProfile(), ELBCoilAGVRouteProfile::ManualOrUnassigned);
    FLBCoilAGVSaveState InitialIdle;
    TestTrue(TEXT("Initial loaded idle state is saveable before a coil identity is assigned"),
        AGV->GetSaveState(InitialIdle));
    TestTrue(TEXT("Initial loaded idle state round-trips with an intentionally empty coil identity"),
        AGV->RestoreSaveState(InitialIdle));
    TestTrue(TEXT("Initial idle round-trip retains all three route points"),
        InitialIdle.RouteStagedPoint.Equals(FVector(0,0,29), 0.01f)
        && InitialIdle.RouteTurnPoint.Equals(FVector(400,0,29), 0.01f)
        && InitialIdle.RouteDockPoint.Equals(FVector(400,300,29), 0.01f));
    FLBCoilAGVSaveState UndergroundManualRoute = InitialIdle;
    UndergroundManualRoute.RouteStagedPoint.Z -= 100.0f;
    UndergroundManualRoute.RouteTurnPoint.Z -= 100.0f;
    UndergroundManualRoute.RouteDockPoint.Z -= 100.0f;
    UndergroundManualRoute.VehicleLocation.Z -= 100.0f;
    TestFalse(TEXT("Even a coherent manual save cannot move the whole route below the live factory floor datum"),
        AGV->RestoreSaveState(UndergroundManualRoute));
    TestTrue(TEXT("Rejected underground manual restore leaves the live route at floor height"),
        AGV->GetConfiguredDockPoint().Equals(FVector(400,300,29), 0.01f));
    TestTrue(TEXT("Safe loaded dispatch starts"), AGV->StartDispatch(TEXT("MCX-U-CS06-TEST")));

    const FVector ChassisStart = Chassis ? Chassis->GetActorLocation() : FVector::ZeroVector;
    const FVector DeckToChassisStart = Chassis && Deck
        ? Deck->GetActorLocation() - Chassis->GetActorLocation() : FVector::ZeroVector;
    FVector PreviousCornerLocation = AGV->GetVehicleLocation();
    float PreviousCornerYaw = AGV->GetVehicleYawDegrees();
    float MaximumCornerYawStep = 0.0f;
    bool bObservedMovingCorner = false;
    bool bChassisFollowedEveryTick = true;
    bool bDeckStayedLocallyRegisteredInTravel = true;
    for (int32 Step=0; Step<150 && AGV->GetPhase()!=ELBCoilAGVPhase::TravelToDock; ++Step)
    {
        const bool bWasInCorner = AGV->GetPhase() == ELBCoilAGVPhase::RotateForDock;
        AGV->Tick(0.1f);
        bChassisFollowedEveryTick &= Chassis
            && Chassis->GetActorLocation().Equals(AGV->GetVehicleLocation(), 0.1f);
        if (Chassis && Deck)
        {
            bDeckStayedLocallyRegisteredInTravel &= (Deck->GetActorLocation()
                - Chassis->GetActorLocation()).Equals(DeckToChassisStart, 0.1f);
        }
        if (bWasInCorner || AGV->GetPhase() == ELBCoilAGVPhase::RotateForDock)
        {
            const FVector CornerLocation = AGV->GetVehicleLocation();
            bObservedMovingCorner |= FVector::Dist2D(CornerLocation, PreviousCornerLocation) > 0.1f;
            MaximumCornerYawStep = FMath::Max(MaximumCornerYawStep,
                FMath::Abs(FMath::FindDeltaAngleDegrees(PreviousCornerYaw, AGV->GetVehicleYawDegrees())));
            PreviousCornerLocation = CornerLocation;
            PreviousCornerYaw = AGV->GetVehicleYawDegrees();
        }
    }
    TestEqual(TEXT("AGV flows out of the rounded corner toward the dock"), AGV->GetPhase(), ELBCoilAGVPhase::TravelToDock);
    TestTrue(TEXT("Tagged chassis follows the route authority every tick"), bChassisFollowedEveryTick);
    TestTrue(TEXT("Whole chassis actually leaves its staged point"), Chassis
        && FVector::Dist2D(ChassisStart, Chassis->GetActorLocation()) > 100.0f);
    TestTrue(TEXT("Deck stays a local vehicle articulation during travel"), bDeckStayedLocallyRegisteredInTravel);
    TestTrue(TEXT("Corner translates instead of rotating in place"), bObservedMovingCorner);
    TestTrue(TEXT("Corner heading changes in smooth frame-sized increments"), MaximumCornerYawStep <= 10.0f);
    const FVector StoppedPosition = AGV->GetVehicleLocation();
    TestTrue(TEXT("Scanner obstruction fail-stops motion"), AGV->SetSafetyInputs(true,true,false,true,true,true,true));
    TestEqual(TEXT("Scanner fault is explicit"), AGV->GetFault(), ELBCoilAGVFault::ScannerObstructed);
    AGV->Tick(1.0f);
    TestTrue(TEXT("Faulted AGV and load do not drift"), AGV->GetVehicleLocation().Equals(StoppedPosition,0.01f));
    TestFalse(TEXT("Unsafe scanner cannot be reset"), AGV->ResetFault(TEXT("EVID_SCANNER_BLOCKED")));
    TestTrue(TEXT("Clear scanner input is accepted"), AGV->SetSafetyInputs(true,true,true,true,true,true,true));
    TestTrue(TEXT("Named recovery resumes interrupted travel"), AGV->ResetFault(TEXT("EVID_SCANNER_CLEAR")));
    TestEqual(TEXT("Recovery resumes exact phase"), AGV->GetPhase(), ELBCoilAGVPhase::TravelToDock);

    FLBCoilAGVSaveState InFlight;
    TestTrue(TEXT("In-flight AGV state is saveable"), AGV->GetSaveState(InFlight));
    TestEqual(TEXT("Coil AGV save schema includes route ownership"), InFlight.SaveVersion, 3);
    TestEqual(TEXT("Manual route ownership enters save state"),
        InFlight.RouteProfile, ELBCoilAGVRouteProfile::ManualOrUnassigned);
    for (int32 Step=0; Step<5; ++Step) AGV->Tick(0.1f);
    TestTrue(TEXT("Stable travel phase restores"), AGV->RestoreSaveState(InFlight));
    TestEqual(TEXT("Restore preserves phase"), AGV->GetPhase(), InFlight.Phase);
    TestTrue(TEXT("Restore preserves location"), AGV->GetVehicleLocation().Equals(InFlight.VehicleLocation,0.01f));
    FLBCoilAGVSaveState LegacyV2 = InFlight;
    LegacyV2.SaveVersion = 2;
    LegacyV2.RouteProfile = ELBCoilAGVRouteProfile::PressTrainHandoff;
    LegacyV2.AssignedRouteTrainIndex = 2;
    TestTrue(TEXT("Legacy v2 state remains load compatible"), AGV->RestoreSaveState(LegacyV2));
    TestEqual(TEXT("Legacy saves preserve the controller's already configured route ownership"),
        AGV->GetRouteProfile(), ELBCoilAGVRouteProfile::ManualOrUnassigned);

    for (int32 Step=0; Step<300 && !AGV->IsHandoffReady(); ++Step) AGV->Tick(0.1f);
    TestTrue(TEXT("AGV reaches proved PR004 handoff-ready state"), AGV->IsHandoffReady());
    TestTrue(TEXT("AGV ends at dock"), AGV->GetVehicleLocation().Equals(FVector(400,300,29),0.1f));
    TestTrue(TEXT("AGV rotates 90 degrees into dock"), FMath::IsNearlyEqual(AGV->GetVehicleYawDegrees(),90.0f,0.1f));
    TestTrue(TEXT("Transfer deck raises only the candidate 80 mm"), FMath::IsNearlyEqual(AGV->GetLiftHeightCm(),8.0f,0.01f));
    TestTrue(TEXT("Physical load remains rigidly registered"), AGV->GetMaxLoadFollowErrorCm() <= 0.1f);
    TestTrue(TEXT("Deck follows vehicle"), Deck && Deck->GetActorLocation().Z > 64.0f);
    TestTrue(TEXT("Deck lift remains local to the moved chassis"), Chassis && Deck
        && FMath::IsNearlyEqual((Deck->GetActorLocation() - Chassis->GetActorLocation()).Z,
            DeckToChassisStart.Z + 8.0f, 0.1f));
    FString HandedOffCoil;
    TestTrue(TEXT("Proved receiver accepts exact carried coil"), AGV->ConfirmHandoff(HandedOffCoil));
    TestEqual(TEXT("Handoff preserves coil identity"), HandedOffCoil, FString(TEXT("MCX-U-CS06-TEST")));
    TestFalse(TEXT("Empty AGV no longer owns the transferred coil"), AGV->OwnsLoad());
    TestTrue(TEXT("Transferred physical load leaves AGV presentation"), Load && Load->IsHidden());
    for (int32 Step=0; Step<300 && !AGV->IsAwaitingReload(); ++Step) AGV->Tick(0.1f);
    TestTrue(TEXT("Empty AGV returns to its staged point"), AGV->IsAwaitingReload());
    TestTrue(TEXT("Returned AGV faces its original route"), FMath::IsNearlyZero(AGV->GetVehicleYawDegrees(),0.1f));
    FLBCoilAGVSaveState EmptyReturned;
    TestTrue(TEXT("Returned empty AGV state is saveable"), AGV->GetSaveState(EmptyReturned));
    TestTrue(TEXT("Returned empty AGV state restores"), AGV->RestoreSaveState(EmptyReturned));
    TestTrue(TEXT("Next identified coil reloads only at staged point"), AGV->ReloadAtStagedPoint(TEXT("MCX-U-CS07-TEST")));
    TestTrue(TEXT("Reloaded AGV owns its next physical load"), AGV->OwnsLoad());
    TestFalse(TEXT("Reloaded physical coil is visible"), Load && Load->IsHidden());
    TestTrue(TEXT("Second dispatch can start"), AGV->StartDispatch(TEXT("MCX-U-CS07-TEST")));
    return true;
}

bool FLBPlayerBuiltApprovedCoilAGVPresentationTest::RunTest(const FString& Parameters)
{
    FLBTransientAGVWorld TestWorld;
    ALBCoilAGVController* AGV = TestWorld.World
        ? TestWorld.World->SpawnActor<ALBCoilAGVController>() : nullptr;
    TestNotNull(TEXT("Player-built AGV authority spawns without map fixtures"), AGV);
    TestTrue(TEXT("Approved untouched chassis and identified load self-bind"), AGV && AGV->DiscoverAndBind());
    TestTrue(TEXT("Controller reports approved player-built presentation"), AGV && AGV->IsUsingApprovedPlayerBuiltPresentation());
    UStaticMeshComponent* ChassisVisual = AGV ? AGV->GetApprovedChassisVisual() : nullptr;
    UStaticMeshComponent* LiftProxy = AGV ? AGV->GetApprovedLiftDeckVisual() : nullptr;
    UStaticMeshComponent* LoadVisual = AGV ? AGV->GetApprovedLoadVisual() : nullptr;
    UBoxComponent* CollisionProxy = AGV ? AGV->GetCollisionProxy() : nullptr;
    TestNotNull(TEXT("Untouched controlled-paint chassis component exists"), ChassisVisual);
    TestNotNull(TEXT("Hidden lift transform exists"), LiftProxy);
    TestNotNull(TEXT("Identified wrapped load component exists"), LoadVisual);
    TestNotNull(TEXT("Simple AGV collision proxy exists"), CollisionProxy);
    if (ChassisVisual && ChassisVisual->GetStaticMesh())
    {
        TestEqual(TEXT("Runtime uses the untouched full-detail AGV mesh"),
            ChassisVisual->GetStaticMesh()->GetPathName(),
            FString(TEXT("/Game/LineBoss/Runtime/PressShop/CoilAGV/UntouchedControlled_v20260810/SM_Cairnwell_CoilAGV_UntouchedControlled_v20260810.SM_Cairnwell_CoilAGV_UntouchedControlled_v20260810")));
        TestTrue(TEXT("Untouched AGV retains its audited full-size bounds"),
            ChassisVisual->GetStaticMesh()->GetBoundingBox().GetSize().Equals(
                FVector(145.9682f, 190.1947f, 57.0366f), 0.05f));
        TestTrue(TEXT("Appearance yaw maps source nose to route +X"),
            FMath::IsNearlyEqual(ChassisVisual->GetRelativeRotation().Yaw, 90.0f, 0.01f));
        TestEqual(TEXT("High-resolution appearance never owns gameplay collision"),
            ChassisVisual->GetCollisionEnabled(), ECollisionEnabled::NoCollision);
    }
    if (LiftProxy)
    {
        TestNull(TEXT("No old split deck mesh remains in the player-built AGV"), LiftProxy->GetStaticMesh());
        TestFalse(TEXT("Meshless lift transform is never rendered"), LiftProxy->IsVisible());
        TestTrue(TEXT("Lifted coil retains the untouched cradle orientation"),
            FMath::IsNearlyEqual(LiftProxy->GetRelativeRotation().Yaw, 90.0f, 0.01f));
    }
    if (LoadVisual)
    {
        TestTrue(TEXT("Wrapped coil stays on the Blender-audited cradle datum"),
            LoadVisual->GetRelativeLocation().Equals(FVector(0.0f, 0.0f, 12.5f), 0.01f));
        if (LoadVisual->GetStaticMesh())
        {
            TestEqual(TEXT("AGV load uses the controlled full-detail wrapped-coil mesh"),
                LoadVisual->GetStaticMesh()->GetPathName(),
                FString(TEXT("/Game/LineBoss/Runtime/PressShop/WrappedCoil/Controlled_v20260810/SM_Cairnwell_WrappedCoil_Controlled_v20260810.SM_Cairnwell_WrappedCoil_Controlled_v20260810")));
            TestTrue(TEXT("Controlled coil retains its audited industrial envelope"),
                LoadVisual->GetStaticMesh()->GetBoundingBox().GetSize().Equals(
                    FVector(181.0503f, 150.0f, 178.9497f), 0.05f));
            TestNotNull(TEXT("Controlled packaging material remains assigned"),
                LoadVisual->GetStaticMesh()->GetMaterial(0));
            TestNotNull(TEXT("Controlled solid-core material remains assigned"),
                LoadVisual->GetStaticMesh()->GetMaterial(1));
            if (LoadVisual->GetStaticMesh()->GetMaterial(0))
                TestEqual(TEXT("AGV load rejects the clipping Meshy material graph"),
                    LoadVisual->GetStaticMesh()->GetMaterial(0)->GetPathName(),
                    FString(TEXT("/Game/LineBoss/Runtime/PressShop/WrappedCoil/Controlled_v20260810/Materials/M_Cairnwell_WrappedCoil_ControlledPackaging_R2_v20260810.M_Cairnwell_WrappedCoil_ControlledPackaging_R2_v20260810")));
        }
    }
    if (CollisionProxy)
    {
        TestTrue(TEXT("Proxy extents match the rotated untouched master"),
            CollisionProxy->GetUnscaledBoxExtent().Equals(FVector(95.0974f, 72.9841f, 28.5183f), 0.01f));
        TestEqual(TEXT("Player-built AGV enables only simple proxy collision"),
            CollisionProxy->GetCollisionEnabled(), ECollisionEnabled::QueryAndPhysics);
    }
    auto PlaceInfrastructure = [&](const TCHAR* Id, ELBFactoryAGVInfrastructureType Type,
        const FVector Location, const int32 TrainIndex = INDEX_NONE,
        const FRotator Rotation = FRotator::ZeroRotator)
    {
        ALBFactoryAGVInfrastructure* Item = TestWorld.World->SpawnActor<ALBFactoryAGVInfrastructure>(
            ALBFactoryAGVInfrastructure::StaticClass(), FTransform(Rotation, Location));
        return Item && Item->Configure(FName(Id), Type, TrainIndex);
    };
    TestTrue(TEXT("Player wait point placed"), PlaceInfrastructure(TEXT("WAIT-A"), ELBFactoryAGVInfrastructureType::WaitPoint, FVector(0,0,10)));
    TestTrue(TEXT("Player route waypoint placed"), PlaceInfrastructure(TEXT("TURN-A"), ELBFactoryAGVInfrastructureType::RouteWaypoint, FVector(500,0,5)));
    TestTrue(TEXT("Player train handoff placed"), PlaceInfrastructure(TEXT("HANDOFF-A"), ELBFactoryAGVInfrastructureType::PressTrainHandoff, FVector(500,500,10),0));
    TestTrue(TEXT("First player route segment placed"), PlaceInfrastructure(TEXT("ROUTE-1"), ELBFactoryAGVInfrastructureType::AGVRouteSegment, FVector(250,0,2)));
    TestTrue(TEXT("Second player route segment placed"), PlaceInfrastructure(TEXT("ROUTE-2"),
        ELBFactoryAGVInfrastructureType::AGVRouteSegment, FVector(500,250,2), INDEX_NONE,
        FRotator(0,90,0)));
    TestTrue(TEXT("AGV derives route from player-built infrastructure"), AGV && AGV->ConfigureFromPlayerBuiltInfrastructure(0));
    TestEqual(TEXT("Train handoff route records explicit ownership"),
        AGV ? AGV->GetRouteProfile() : ELBCoilAGVRouteProfile::ManualOrUnassigned,
        ELBCoilAGVRouteProfile::PressTrainHandoff);
    TestEqual(TEXT("Train handoff route records its exact train index"),
        AGV ? AGV->GetAssignedRouteTrainIndex() : INDEX_NONE, 0);
    TestTrue(TEXT("Identified wrapped coil dispatch starts"), AGV && AGV->StartDispatch(TEXT("PLAYER-COIL-001")));
    for (int32 Step = 0; Step < 5 && AGV; ++Step) AGV->Tick(0.1f);
    FLBCoilAGVSaveState TrainRouteSave;
    TestTrue(TEXT("In-flight train-owned route captures exact geometry and ownership"),
        AGV && AGV->GetSaveState(TrainRouteSave));
    FLBCoilAGVSaveState LegacyTrainRouteSave = TrainRouteSave;
    LegacyTrainRouteSave.SaveVersion = 2;
    LegacyTrainRouteSave.RouteProfile = ELBCoilAGVRouteProfile::ManualOrUnassigned;
    LegacyTrainRouteSave.AssignedRouteTrainIndex = INDEX_NONE;
    TestTrue(TEXT("Legacy v2 motion restores over an already configured train route"),
        AGV && AGV->RestoreSaveState(LegacyTrainRouteSave));
    TestTrue(TEXT("Legacy v2 restore preserves the runtime train route assignment"), AGV
        && AGV->GetRouteProfile() == ELBCoilAGVRouteProfile::PressTrainHandoff
        && AGV->GetAssignedRouteTrainIndex() == 0);

    {
        FLBTransientAGVWorld ReloadWorld;
        const auto PlaceReloadInfrastructure = [&ReloadWorld](const TCHAR* Id,
            const ELBFactoryAGVInfrastructureType Type, const FVector& Location,
            const int32 TrainIndex = INDEX_NONE,
            const FRotator Rotation = FRotator::ZeroRotator)
        {
            ALBFactoryAGVInfrastructure* Item = ReloadWorld.World
                ? ReloadWorld.World->SpawnActor<ALBFactoryAGVInfrastructure>(
                    ALBFactoryAGVInfrastructure::StaticClass(), FTransform(Rotation, Location)) : nullptr;
            return Item && Item->Configure(FName(Id), Type, TrainIndex);
        };
        TestTrue(TEXT("Fresh world recreates the saved train route authority"),
            PlaceReloadInfrastructure(TEXT("WAIT-A"), ELBFactoryAGVInfrastructureType::WaitPoint,
                FVector(0,0,10))
            && PlaceReloadInfrastructure(TEXT("TURN-A"), ELBFactoryAGVInfrastructureType::RouteWaypoint,
                FVector(500,0,5))
            && PlaceReloadInfrastructure(TEXT("HANDOFF-A"), ELBFactoryAGVInfrastructureType::PressTrainHandoff,
                FVector(500,500,10), 0)
            && PlaceReloadInfrastructure(TEXT("ROUTE-1"), ELBFactoryAGVInfrastructureType::AGVRouteSegment,
                FVector(250,0,2))
            && PlaceReloadInfrastructure(TEXT("ROUTE-2"), ELBFactoryAGVInfrastructureType::AGVRouteSegment,
                FVector(500,250,2), INDEX_NONE, FRotator(0,90,0)));
        ALBCoilAGVController* ReloadedAGV = ReloadWorld.World
            ? ReloadWorld.World->SpawnActor<ALBCoilAGVController>() : nullptr;
        TestTrue(TEXT("Fresh AGV binds before route-state restore"),
            ReloadedAGV && ReloadedAGV->DiscoverAndBind());
        TestTrue(TEXT("Fresh AGV restores only after revalidating its painted train route"),
            ReloadedAGV && ReloadedAGV->RestoreSaveState(TrainRouteSave));
        FLBCoilAGVSaveState RoundTrippedRoute;
        TestTrue(TEXT("Fresh restored AGV can recapture its route state"),
            ReloadedAGV && ReloadedAGV->GetSaveState(RoundTrippedRoute));
        TestTrue(TEXT("Fresh-world route-state round-trip preserves all three route points"),
            RoundTrippedRoute.RouteStagedPoint.Equals(TrainRouteSave.RouteStagedPoint, 0.01f)
            && RoundTrippedRoute.RouteTurnPoint.Equals(TrainRouteSave.RouteTurnPoint, 0.01f)
            && RoundTrippedRoute.RouteDockPoint.Equals(TrainRouteSave.RouteDockPoint, 0.01f));
        TestTrue(TEXT("Fresh-world route-state round-trip preserves profile and train index"),
            RoundTrippedRoute.RouteProfile == ELBCoilAGVRouteProfile::PressTrainHandoff
            && RoundTrippedRoute.AssignedRouteTrainIndex == 0);
        FLBCoilAGVSaveState CorruptRouteHeight = TrainRouteSave;
        CorruptRouteHeight.RouteTurnPoint.Z += 5.0f;
        TestFalse(TEXT("Restore rejects route points that leave the chassis travel datum"),
            ReloadedAGV && ReloadedAGV->RestoreSaveState(CorruptRouteHeight));
        FLBCoilAGVSaveState CorruptVehicleHeight = TrainRouteSave;
        CorruptVehicleHeight.VehicleLocation.Z -= 5.0f;
        TestFalse(TEXT("Restore rejects a vehicle location below its certified route datum"),
            ReloadedAGV && ReloadedAGV->RestoreSaveState(CorruptVehicleHeight));
        TestTrue(TEXT("Corrupt-height restores leave the certified route unchanged"), ReloadedAGV
            && ReloadedAGV->GetConfiguredDockPoint().Equals(TrainRouteSave.RouteDockPoint, 0.01f)
            && ReloadedAGV->GetRouteProfile() == ELBCoilAGVRouteProfile::PressTrainHandoff);

        const FVector PreFailureDock(900.0f, 900.0f, TrainRouteSave.RouteDockPoint.Z);
        ALBCoilAGVController* FailureAGV = ReloadWorld.World
            ? ReloadWorld.World->SpawnActor<ALBCoilAGVController>() : nullptr;
        TestTrue(TEXT("Independent failure-path AGV binds"),
            FailureAGV && FailureAGV->DiscoverAndBind());
        TestTrue(TEXT("Fresh AGV can hold an unrelated safe route before a rejected restore"),
            FailureAGV && FailureAGV->ConfigureRoute(
                FVector(700.0f, 600.0f, PreFailureDock.Z),
                FVector(900.0f, 600.0f, PreFailureDock.Z), PreFailureDock));
        ALBFactoryBuildMachine* Obstacle = ReloadWorld.World
            ? ReloadWorld.World->SpawnActor<ALBFactoryBuildMachine>(
                ALBFactoryBuildMachine::StaticClass(), FTransform(FVector(250.0f, 0.0f, 0.0f))) : nullptr;
        TestTrue(TEXT("A restored-route protected obstacle configures"), Obstacle && Obstacle->Configure(
            TEXT("RESTORE-ROUTE-OBSTACLE"), ELBFactoryBuildMachineType::DepackagingRobot));
        TestFalse(TEXT("Protected obstacle rejects the automatic route restore"),
            FailureAGV && FailureAGV->RestoreSaveState(TrainRouteSave));
        TestTrue(TEXT("Failed restore atomically preserves the pre-existing route and ownership"),
            FailureAGV && FailureAGV->GetConfiguredDockPoint().Equals(PreFailureDock, 0.01f)
            && FailureAGV->GetRouteProfile() == ELBCoilAGVRouteProfile::ManualOrUnassigned
            && FailureAGV->GetAssignedRouteTrainIndex() == INDEX_NONE);
    }
    const float StagedLoadWorldZ = LoadVisual ? LoadVisual->GetComponentLocation().Z : 0.0f;
    for (int32 Step=0; Step<400 && AGV && !AGV->IsHandoffReady(); ++Step) AGV->Tick(0.1f);
    TestTrue(TEXT("Approved player-built AGV reaches raised handoff"), AGV && AGV->IsHandoffReady());
    TestTrue(TEXT("Hidden load lift transform raises 80 mm"), AGV && FMath::IsNearlyEqual(AGV->GetLiftHeightCm(),8.0f,0.01f));
    TestTrue(TEXT("Wrapped load follows the hidden lift transform"), AGV && AGV->GetApprovedLiftDeckVisual()
        && FMath::IsNearlyEqual(AGV->GetApprovedLiftDeckVisual()->GetRelativeLocation().Z, 8.0f, 0.01f));
    TestTrue(TEXT("Actual wrapped load rises exactly 80 mm at handoff"), LoadVisual
        && FMath::IsNearlyEqual(LoadVisual->GetComponentLocation().Z - StagedLoadWorldZ, 8.0f, 0.01f));
    return true;
}

bool FLBCoilAGVProtectedRouteTest::RunTest(const FString& Parameters)
{
    FLBTransientAGVWorld TestWorld;
    ALBCoilAGVController* AGV = TestWorld.World
        ? TestWorld.World->SpawnActor<ALBCoilAGVController>() : nullptr;
    TestTrue(TEXT("Protected-route AGV self-binds"), AGV && AGV->DiscoverAndBind());
    if (!AGV) return false;
    const auto PlaceInfrastructure = [&](const TCHAR* Id,
        const ELBFactoryAGVInfrastructureType Type, const FVector& Location,
        const FRotator& Rotation = FRotator::ZeroRotator, const int32 TrainIndex = INDEX_NONE)
    {
        ALBFactoryAGVInfrastructure* Item = TestWorld.World->SpawnActor<ALBFactoryAGVInfrastructure>(
            ALBFactoryAGVInfrastructure::StaticClass(), FTransform(Rotation, Location));
        return Item && Item->Configure(FName(Id), Type, TrainIndex);
    };
    TestTrue(TEXT("Protected route has a wait point"), PlaceInfrastructure(TEXT("WAIT-SAFE"),
        ELBFactoryAGVInfrastructureType::WaitPoint, FVector(0,0,0)));
    TestTrue(TEXT("Protected route has a rounded waypoint"), PlaceInfrastructure(TEXT("TURN-SAFE"),
        ELBFactoryAGVInfrastructureType::RouteWaypoint, FVector(1000,0,0)));
    TestTrue(TEXT("Protected route has a handoff"), PlaceInfrastructure(TEXT("HANDOFF-SAFE"),
        ELBFactoryAGVInfrastructureType::PressTrainHandoff, FVector(1000,1000,0),
        FRotator::ZeroRotator, 0));
    TestTrue(TEXT("Protected route first leg is continuously painted"),
        PlaceInfrastructure(TEXT("ROUTE-SAFE-1"), ELBFactoryAGVInfrastructureType::AGVRouteSegment,
            FVector(250,0,2))
        && PlaceInfrastructure(TEXT("ROUTE-SAFE-2"), ELBFactoryAGVInfrastructureType::AGVRouteSegment,
            FVector(750,0,2)));
    TestTrue(TEXT("Protected route second leg is continuously painted"),
        PlaceInfrastructure(TEXT("ROUTE-SAFE-3"), ELBFactoryAGVInfrastructureType::AGVRouteSegment,
            FVector(1000,250,2), FRotator(0,90,0))
        && PlaceInfrastructure(TEXT("ROUTE-SAFE-4"), ELBFactoryAGVInfrastructureType::AGVRouteSegment,
            FVector(1000,750,2), FRotator(0,90,0)));

    ALBFactoryBuildMachine* Obstacle = TestWorld.World->SpawnActor<ALBFactoryBuildMachine>(
        ALBFactoryBuildMachine::StaticClass(), FTransform(FVector(500,0,0)));
    TestTrue(TEXT("A protected machine obstacle configures"), Obstacle && Obstacle->Configure(
        TEXT("ROUTE-OBSTACLE"), ELBFactoryBuildMachineType::DepackagingRobot));
    TestFalse(TEXT("A route through a machine protected envelope is rejected"),
        AGV->ConfigureFromPlayerBuiltInfrastructure(0));

    Obstacle->SetActorLocation(FVector(2500,2500,0));
    TestTrue(TEXT("The same painted route configures once its machine envelope is clear"),
        AGV->ConfigureFromPlayerBuiltInfrastructure(0));
    TestTrue(TEXT("Dispatch starts on the proved clear route"), AGV->StartDispatch(TEXT("COIL-SAFE-001")));
    // Simulate a machine being placed or expanded after route authority was granted.
    Obstacle->SetActorLocation(FVector(700,0,0));
    for (int32 Step = 0; Step < 300 && AGV->GetPhase() != ELBCoilAGVPhase::Fault; ++Step)
        AGV->Tick(0.05f);
    TestEqual(TEXT("A new protected-envelope obstruction fail-stops the AGV"),
        AGV->GetFault(), ELBCoilAGVFault::RouteObstructed);
    TestTrue(TEXT("The chassis stops before entering the protected machine clearance"),
        AGV->GetVehicleLocation().X < 240.0f);
    return true;
}

bool FLBLegacyInboundFreshWorldRestoreTest::RunTest(const FString& Parameters)
{
    struct FInboundFixture
    {
        ALBFactoryBuildMachine* Inbound = nullptr;
        ALBFactoryBuildMachine* PR002 = nullptr;
        FVector Start = FVector::ZeroVector;
        FVector Turn = FVector::ZeroVector;
        FVector Dock = FVector::ZeroVector;
    };
    const auto BuildInboundFixture = [](UWorld* World, FInboundFixture& Out)
    {
        if (!World) return false;
        Out.Inbound = World->SpawnActor<ALBFactoryBuildMachine>(
            ALBFactoryBuildMachine::StaticClass(), FTransform(FVector(-1000.0f, -500.0f, 0.0f)));
        Out.PR002 = World->SpawnActor<ALBFactoryBuildMachine>(
            ALBFactoryBuildMachine::StaticClass(), FTransform(FVector(1000.0f, 1000.0f, 0.0f)));
        if (!Out.Inbound || !Out.PR002
            || !Out.Inbound->Configure(TEXT("LEGACY-INBOUND-001"),
                ELBFactoryBuildMachineType::InboundDeliveryDock)
            || !Out.PR002->Configure(TEXT("LEGACY-PR002-001"),
                ELBFactoryBuildMachineType::CoilWeighInspectionCell)
            || !Out.Inbound->OutputPort || !Out.PR002->InputPort)
        {
            return false;
        }
        Out.Start = Out.Inbound->OutputPort->GetComponentLocation();
        Out.Dock = Out.PR002->InputPort->GetComponentLocation();
        Out.Start.Z = Out.Dock.Z = 0.0f;
        Out.Turn = FVector(Out.Dock.X, Out.Start.Y, 0.0f);
        if (FVector::Dist2D(Out.Start, Out.Turn) < 50.0f
            || FVector::Dist2D(Out.Turn, Out.Dock) < 50.0f)
        {
            Out.Turn = FMath::Lerp(Out.Start, Out.Dock, 0.5f);
        }
        int32 Sequence = 1;
        const auto Place = [World, &Sequence](const ELBFactoryAGVInfrastructureType Type,
            const FVector& Location, const FRotator& Rotation = FRotator::ZeroRotator)
        {
            ALBFactoryAGVInfrastructure* Item = World->SpawnActor<ALBFactoryAGVInfrastructure>(
                ALBFactoryAGVInfrastructure::StaticClass(), FTransform(Rotation, Location));
            const FName Id(*FString::Printf(TEXT("LEGACY-INBOUND-INFRA-%02d"), Sequence++));
            return Item && Item->Configure(Id, Type);
        };
        if (!Place(ELBFactoryAGVInfrastructureType::WaitPoint, Out.Start)
            || !Place(ELBFactoryAGVInfrastructureType::RouteWaypoint, Out.Turn)) return false;
        const auto PaintLeg = [&Place](const FVector& A, const FVector& B)
        {
            const float Length = FVector::Dist2D(A, B);
            const int32 Count = FMath::Max(1, FMath::CeilToInt(Length / 400.0f));
            const FRotator Rotation(0.0f, (B - A).Rotation().Yaw, 0.0f);
            for (int32 Index = 0; Index < Count; ++Index)
            {
                const float Alpha = (static_cast<float>(Index) + 0.5f) / static_cast<float>(Count);
                if (!Place(ELBFactoryAGVInfrastructureType::AGVRouteSegment,
                    FMath::Lerp(A, B, Alpha), Rotation)) return false;
            }
            return true;
        };
        return PaintLeg(Out.Start, Out.Turn) && PaintLeg(Out.Turn, Out.Dock);
    };

    FLBCoilAGVSaveState LegacyV2;
    {
        FLBTransientAGVWorld SourceWorld;
        FInboundFixture SourceFixture;
        ALBCoilAGVController* SourceAGV = SourceWorld.World
            ? SourceWorld.World->SpawnActor<ALBCoilAGVController>() : nullptr;
        TestTrue(TEXT("Source campaign has one certified inbound route"),
            BuildInboundFixture(SourceWorld.World, SourceFixture)
            && SourceAGV && SourceAGV->DiscoverAndBind()
            && SourceAGV->ConfigureInboundRouteFromPlayerBuiltInfrastructure(
                SourceFixture.Inbound, SourceFixture.PR002));
        TestTrue(TEXT("Source inbound AGV starts a moving legacy snapshot"),
            SourceAGV && SourceAGV->StartDispatch(TEXT("LEGACY-INBOUND-COIL-001")));
        for (int32 Step = 0; Step < 10 && SourceAGV; ++Step) SourceAGV->Tick(0.1f);
        TestTrue(TEXT("Source inbound motion captures"), SourceAGV && SourceAGV->GetSaveState(LegacyV2));
        LegacyV2.SaveVersion = 2;
        LegacyV2.RouteProfile = ELBCoilAGVRouteProfile::ManualOrUnassigned;
        LegacyV2.AssignedRouteTrainIndex = INDEX_NONE;
    }

    FLBTransientAGVWorld FreshWorld;
    FInboundFixture FreshFixture;
    ALBCoilAGVController* FreshAGV = FreshWorld.World
        ? FreshWorld.World->SpawnActor<ALBCoilAGVController>() : nullptr;
    TestTrue(TEXT("Fresh campaign world recreates machines and painted route before AGV state"),
        BuildInboundFixture(FreshWorld.World, FreshFixture) && FreshAGV && FreshAGV->DiscoverAndBind());
    TestEqual(TEXT("Fresh controller begins with no automatic route ownership"),
        FreshAGV ? FreshAGV->GetRouteProfile() : ELBCoilAGVRouteProfile::InboundPR002,
        ELBCoilAGVRouteProfile::ManualOrUnassigned);
    TestTrue(TEXT("Legacy campaign restore atomically derives inbound route then resumes motion"),
        FreshAGV && FreshAGV->RestoreInboundSaveState(
            LegacyV2, FreshFixture.Inbound, FreshFixture.PR002));
    TestTrue(TEXT("Fresh legacy restore owns the certified inbound route"), FreshAGV
        && FreshAGV->GetRouteProfile() == ELBCoilAGVRouteProfile::InboundPR002
        && FreshAGV->GetAssignedRouteTrainIndex() == INDEX_NONE);
    TestTrue(TEXT("Fresh legacy restore preserves the moving snapshot"), FreshAGV
        && FreshAGV->GetPhase() == LegacyV2.Phase
        && FreshAGV->GetVehicleLocation().Equals(LegacyV2.VehicleLocation, 0.01f));
    FVector ExpectedDock = FreshFixture.Dock;
    ExpectedDock.Z = LegacyV2.VehicleLocation.Z;
    TestTrue(TEXT("Fresh legacy restore uses restored PR002 geometry, never the default manual dock"),
        FreshAGV && FreshAGV->GetConfiguredDockPoint().Equals(ExpectedDock, 0.01f));

    ALBCoilAGVController* FailureAGV = FreshWorld.World
        ? FreshWorld.World->SpawnActor<ALBCoilAGVController>() : nullptr;
    const FVector ManualDock(4500.0f, 4500.0f, LegacyV2.VehicleLocation.Z);
    TestTrue(TEXT("Failure-path controller owns a distinct pre-existing manual route"), FailureAGV
        && FailureAGV->DiscoverAndBind()
        && FailureAGV->ConfigureRoute(FVector(4000.0f, 4000.0f, ManualDock.Z),
            FVector(4500.0f, 4000.0f, ManualDock.Z), ManualDock));
    FLBCoilAGVSaveState OffRouteLegacy = LegacyV2;
    OffRouteLegacy.VehicleLocation += FVector(10000.0f, 10000.0f, 0.0f);
    TestFalse(TEXT("Legacy motion outside the restored painted route is rejected"), FailureAGV
        && FailureAGV->RestoreInboundSaveState(
            OffRouteLegacy, FreshFixture.Inbound, FreshFixture.PR002));
    TestTrue(TEXT("Rejected legacy restore preserves the complete prior route ownership"), FailureAGV
        && FailureAGV->GetRouteProfile() == ELBCoilAGVRouteProfile::ManualOrUnassigned
        && FailureAGV->GetConfiguredDockPoint().Equals(ManualDock, 0.01f));
    return true;
}

#endif
