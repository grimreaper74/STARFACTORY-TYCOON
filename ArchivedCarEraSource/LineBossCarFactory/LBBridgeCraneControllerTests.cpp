#if WITH_DEV_AUTOMATION_TESTS

#include "Misc/AutomationTest.h"

#include "LBBridgeCraneController.h"
#include "LBPR004Station.h"
#include "Engine/Engine.h"
#include "Engine/StaticMeshActor.h"
#include "Engine/World.h"

IMPLEMENT_SIMPLE_AUTOMATION_TEST(
    FLBPR004BridgeCraneTransferTest,
    "LineBoss.PressShop.PR004.BridgeCraneTransferRuntime",
    EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)

namespace
{
    struct FLBTransientCraneWorld
    {
        UWorld* World = nullptr;

        FLBTransientCraneWorld()
        {
            World = UWorld::CreateWorld(EWorldType::Game, false, TEXT("LB_PR004_BridgeCraneTest"));
            if (World)
            {
                FWorldContext& Context = GEngine->CreateNewWorldContext(EWorldType::Game);
                Context.SetCurrentWorld(World);
                World->InitializeActorsForPlay(FURL());
                World->BeginPlay();
            }
        }

        ~FLBTransientCraneWorld()
        {
            if (World)
            {
                World->DestroyWorld(false);
                GEngine->DestroyWorldContext(World);
            }
        }

        AStaticMeshActor* SpawnTagged(const FVector& Location, std::initializer_list<FName> Tags) const
        {
            AStaticMeshActor* Actor = World->SpawnActor<AStaticMeshActor>(
                AStaticMeshActor::StaticClass(), Location, FRotator::ZeroRotator);
            if (Actor)
            {
                Actor->GetStaticMeshComponent()->SetMobility(EComponentMobility::Movable);
                for (const FName Tag : Tags)
                {
                    Actor->Tags.Add(Tag);
                }
            }
            return Actor;
        }
    };
}

bool FLBPR004BridgeCraneTransferTest::RunTest(const FString& Parameters)
{
    FLBTransientCraneWorld TestWorld;
    TestNotNull(TEXT("Transient crane runtime world exists"), TestWorld.World);
    if (!TestWorld.World)
    {
        return false;
    }

    ALBPR004Station* Station = TestWorld.World->SpawnActor<ALBPR004Station>(
        ALBPR004Station::StaticClass(), FVector(1000.0f, -200.0f, 135.0f), FRotator::ZeroRotator);
    TestNotNull(TEXT("PR-004 receiving station spawns"), Station);
    TestTrue(TEXT("PR-004 control power is available"), Station && Station->SetControlPower(true));
    TestTrue(TEXT("PR-004 is commissioned and awaits a crane coil"), Station && Station->SetCellCommissioned(true));
    TestEqual(TEXT("PR-004 begins awaiting a coil"), Station->GetProcessState(), ELBPR004State::AwaitingCoil);

    const FName CraneTag(TEXT("LB.Crane.40T"));
    TestNotNull(TEXT("Bridge motion actor spawns"), TestWorld.SpawnTagged(
        FVector(0.0f, 0.0f, 1500.0f), {CraneTag, TEXT("LB.Motion.CraneBridge")}));
    TestNotNull(TEXT("Trolley motion actor spawns"), TestWorld.SpawnTagged(
        FVector(0.0f, 0.0f, 1600.0f), {CraneTag, TEXT("LB.Motion.CraneTrolley")}));
    TestNotNull(TEXT("Hoist motion actor spawns"), TestWorld.SpawnTagged(
        FVector(0.0f, 0.0f, 1120.0f), {CraneTag, TEXT("LB.Motion.Hoist")}));
    AStaticMeshActor* CHook = TestWorld.SpawnTagged(
        FVector(0.0f, 0.0f, 820.0f), {CraneTag, TEXT("LB.Motion.CHook")});
    TestNotNull(TEXT("C-hook motion actor spawns"), CHook);
    AStaticMeshActor* SourceCoil = TestWorld.SpawnTagged(
        FVector(-1000.0f, 200.0f, 146.0f), {TEXT("LB.CoilSlot.CS-10")});
    TestNotNull(TEXT("Packaged source coil spawns"), SourceCoil);

    ALBBridgeCraneController* Crane = TestWorld.World->SpawnActor<ALBBridgeCraneController>(
        ALBBridgeCraneController::StaticClass(), FVector::ZeroVector, FRotator::ZeroRotator);
    TestNotNull(TEXT("Reusable crane controller spawns"), Crane);
    TestTrue(TEXT("Controller binds tagged modular crane and PR-004"), Crane && Crane->DiscoverAndBind());
    TestTrue(TEXT("Configured packaged-coil transfer starts"), Crane && Crane->StartTransfer(TEXT("MCX-U-CS10-TEST")));

    // Reach the carried-load portion, then prove a safety input stops motion
    // and a named recovery returns to the exact interrupted phase.
    for (int32 Step = 0; Step < 300 && Crane->GetPhase() != ELBBridgeCranePhase::RaisingLoad; ++Step)
    {
        Crane->Tick(0.1f);
    }
    TestEqual(TEXT("Crane secures the real source coil before travel"),
        Crane->GetPhase(), ELBBridgeCranePhase::RaisingLoad);
    TestTrue(TEXT("Source coil is now physically carried"), Crane->IsCarryingCoil());
    TestTrue(TEXT("C-hook padded lower arm remains centred through the coil bore"),
        CHook && FMath::IsNearlyEqual(
            CHook->GetActorLocation().Z - SourceCoil->GetActorLocation().Z,
            Crane->GetLoadCentreBelowHookCm(), 0.1f));

    FLBBridgeCraneSaveState InFlightState;
    TestTrue(TEXT("In-flight crane production state is saveable"), Crane->GetSaveState(InFlightState));
    TestTrue(TEXT("In-flight save records material ownership"), InFlightState.bCarryingCoil);
    TestEqual(TEXT("In-flight save records the coil identity"), InFlightState.CoilId, FString(TEXT("MCX-U-CS10-TEST")));

    const FVector PositionBeforeStop = SourceCoil->GetActorLocation();
    TestTrue(TEXT("Unsafe personnel input is accepted and fail-stops motion"), Crane->SetSafetyInputs(true, false, true));
    TestEqual(TEXT("Unsafe route latches a crane fault"), Crane->GetPhase(), ELBBridgeCranePhase::Fault);
    TestEqual(TEXT("Crane reports route/personnel fault"), Crane->GetFault(), ELBBridgeCraneFault::RouteOrPersonnelUnsafe);
    Crane->Tick(1.0f);
    TestTrue(TEXT("Suspended load does not drift while faulted"), SourceCoil->GetActorLocation().Equals(PositionBeforeStop, 0.01f));
    TestFalse(TEXT("Fault cannot reset while personnel input is unsafe"), Crane->ResetFault(TEXT("EVID_UNSAFE")));
    TestTrue(TEXT("Proved clear route restores safety inputs"), Crane->SetSafetyInputs(true, true, true));
    TestTrue(TEXT("Named recovery resumes the interrupted lift"), Crane->ResetFault(TEXT("EVID_ROUTE_CLEAR")));
    TestEqual(TEXT("Recovery resumes raising the load"), Crane->GetPhase(), ELBBridgeCranePhase::RaisingLoad);

    // Exercise restoration while the crane owns the material.
    for (int32 Step = 0; Step < 5; ++Step)
    {
        Crane->Tick(0.1f);
    }
    TestTrue(TEXT("Earlier in-flight state restores coherently"), Crane->RestoreSaveState(InFlightState));
    TestEqual(TEXT("Restore preserves the saved lift phase"), Crane->GetPhase(), InFlightState.Phase);
    TestTrue(TEXT("Restore preserves crane material ownership"), Crane->IsCarryingCoil());
    TestTrue(TEXT("Restore returns the saved hook height"), FMath::IsNearlyEqual(Crane->GetHookZ(), InFlightState.HookZ, 0.01f));

    for (int32 Step = 0; Step < 800 && !Crane->IsTransferComplete(); ++Step)
    {
        Crane->Tick(0.1f);
    }
    TestTrue(TEXT("Crane completes pickup, safe travel, deposit and withdrawal"), Crane->IsTransferComplete());
    TestFalse(TEXT("Crane releases material ownership after deposit"), Crane->IsCarryingCoil());
    TestTrue(TEXT("Consumed source visual is removed from its store slot"), SourceCoil->IsHidden());
    TestEqual(TEXT("PR-004 receives the exact transferred coil"), Station->GetCurrentCoilId(), FString(TEXT("MCX-U-CS10-TEST")));
    TestEqual(TEXT("PR-004 receives the configured steel heat"), Station->GetCurrentHeatId(), FString(TEXT("HT-CW26-08417")));
    TestEqual(TEXT("PR-004 receives the configured supplier lot"), Station->GetCurrentSupplierLotId(), FString(TEXT("LOT-MCXU-260804-A")));
    TestEqual(TEXT("PR-004 receives the configured traceability barcode"), Station->GetCurrentTraceabilityBarcode(), FString(TEXT("503184064100010")));
    TestEqual(TEXT("PR-004 owns a packaged coil after crane deposit"), Station->GetProcessState(), ELBPR004State::CoilLoaded);
    TestTrue(TEXT("Hook withdraws to its safe travel height"), FMath::IsNearlyEqual(Crane->GetHookZ(), 820.0f, 0.1f));
    TestTrue(TEXT("Native load remains rigidly registered to the C-hook datum"),
        Crane->GetMaxLoadFollowErrorCm() <= 0.1f);
    TestTrue(TEXT("Cairnwell label attachments remain rigidly registered to the packaged coil"),
        Crane->GetMaxAttachmentFollowErrorCm() <= 0.1f);

    FLBBridgeCraneSaveState CompletedState;
    TestTrue(TEXT("Completed transfer state is saveable"), Crane->GetSaveState(CompletedState));
    TestTrue(TEXT("Completed save records consumed source inventory"), CompletedState.bSourceCoilConsumed);
    TestEqual(TEXT("Completed save records terminal phase"), CompletedState.Phase, ELBBridgeCranePhase::Complete);
    return true;
}

#endif
