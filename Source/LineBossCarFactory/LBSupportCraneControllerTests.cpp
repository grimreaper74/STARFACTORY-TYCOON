#if WITH_DEV_AUTOMATION_TESTS

#include "Misc/AutomationTest.h"

#include "LBSupportCraneController.h"
#include "Engine/Engine.h"
#include "Engine/StaticMeshActor.h"
#include "Engine/World.h"

IMPLEMENT_SIMPLE_AUTOMATION_TEST(
    FLBFrontEndSupportCraneTest,
    "LineBoss.PressShop.FrontEnd.SupportCraneRuntime",
    EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)

namespace
{
    struct FLBTransientSupportCraneWorld
    {
        UWorld* World = nullptr;

        FLBTransientSupportCraneWorld()
        {
            World = UWorld::CreateWorld(EWorldType::Game, false, TEXT("LB_SupportCraneTest"));
            if (World)
            {
                FWorldContext& Context = GEngine->CreateNewWorldContext(EWorldType::Game);
                Context.SetCurrentWorld(World);
                World->InitializeActorsForPlay(FURL());
                World->BeginPlay();
            }
        }

        ~FLBTransientSupportCraneWorld()
        {
            if (World)
            {
                World->DestroyWorld(false);
                GEngine->DestroyWorldContext(World);
            }
        }

        AStaticMeshActor* SpawnTagged(const FVector& Location,
            std::initializer_list<FName> Tags) const
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

bool FLBFrontEndSupportCraneTest::RunTest(const FString& Parameters)
{
    FLBTransientSupportCraneWorld TestWorld;
    TestNotNull(TEXT("Transient support crane world exists"), TestWorld.World);
    if (!TestWorld.World)
    {
        return false;
    }

    const FName CraneTag(TEXT("LB.Crane.30T"));
    TestNotNull(TEXT("Support bridge actor spawns"), TestWorld.SpawnTagged(
        FVector(-9100.0f, -4700.0f, 1500.0f), {CraneTag, TEXT("LB.Motion.CraneBridge")}));
    TestNotNull(TEXT("Support trolley actor spawns"), TestWorld.SpawnTagged(
        FVector(-9100.0f, -4700.0f, 1600.0f), {CraneTag, TEXT("LB.Motion.CraneTrolley")}));
    TestNotNull(TEXT("Support hoist actor spawns"), TestWorld.SpawnTagged(
        FVector(-9100.0f, -4700.0f, 1120.0f), {CraneTag, TEXT("LB.Motion.Hoist")}));
    AStaticMeshActor* Hook = TestWorld.SpawnTagged(
        FVector(-9100.0f, -4700.0f, 1010.0f), {CraneTag, TEXT("LB.Motion.CHook")});
    TestNotNull(TEXT("Support hook actor spawns"), Hook);
    TestNotNull(TEXT("Approved maintenance support point spawns"), TestWorld.SpawnTagged(
        FVector(-7600.0f, -3300.0f, 760.0f), {TEXT("LB.Crane.SupportPoint.FrontEndMaintenance")}));
    TestNotNull(TEXT("Unrelated master coil may exist without becoming support-crane material"),
        TestWorld.SpawnTagged(FVector(-6500.0f, -1800.0f, 146.0f), {TEXT("LB.CoilSlot.CS-10")}));

    ALBSupportCraneController* Crane = TestWorld.World->SpawnActor<ALBSupportCraneController>(
        ALBSupportCraneController::StaticClass(), FVector::ZeroVector, FRotator::ZeroRotator);
    TestNotNull(TEXT("Support crane controller spawns"), Crane);
    TestTrue(TEXT("Controller binds only the tagged 30 t assembly and approved service point"),
        Crane && Crane->DiscoverAndBind());
    TestFalse(TEXT("30 t support crane cannot claim master-coil authority"),
        Crane && Crane->CanHandleMasterCoils());

    TestFalse(TEXT("Dispatch is rejected without a maintenance permit"),
        Crane && Crane->DispatchToConfiguredServicePoint());
    TestEqual(TEXT("Missing permit latches an explicit fault"), Crane->GetFault(),
        ELBSupportCraneFault::MaintenancePermitMissing);
    TestTrue(TEXT("Permit and reserved zone inputs are accepted"),
        Crane->SetSafetyInputs(true, true, true, true));
    TestTrue(TEXT("Named evidence clears the permit fault"), Crane->ResetFault(TEXT("EVID_PERMIT_204")));
    TestTrue(TEXT("Approved maintenance dispatch starts"), Crane->DispatchToConfiguredServicePoint());

    for (int32 Step = 0; Step < 50; ++Step)
    {
        Crane->Tick(0.1f);
    }
    FLBSupportCraneSaveState MovingState;
    TestTrue(TEXT("Moving support crane state is captured"), Crane->GetSaveState(MovingState));
    TestFalse(TEXT("Moving support crane save is marked unstable"), MovingState.bStableState);

    TestTrue(TEXT("40 t swept-zone conflict input fail-stops the support crane"),
        Crane->SetPrimaryCraneClear(false));
    TestEqual(TEXT("Primary-crane conflict is explicit"), Crane->GetFault(),
        ELBSupportCraneFault::PrimaryCraneConflict);
    const FVector StoppedHook = Hook->GetActorLocation();
    Crane->Tick(1.0f);
    TestTrue(TEXT("Support hook does not drift while conflict-faulted"),
        Hook->GetActorLocation().Equals(StoppedHook, 0.01f));
    TestFalse(TEXT("Conflict cannot reset while the 40 t swept zone is occupied"),
        Crane->ResetFault(TEXT("EVID_CONFLICT_ACTIVE")));
    TestTrue(TEXT("40 t separation can be proved clear"), Crane->SetPrimaryCraneClear(true));
    TestTrue(TEXT("Named separation evidence resumes dispatch"),
        Crane->ResetFault(TEXT("EVID_40T_CLEAR")));

    for (int32 Step = 0; Step < 400 && !Crane->IsAtServicePoint(); ++Step)
    {
        Crane->Tick(0.1f);
    }
    TestTrue(TEXT("Support crane reaches the approved maintenance point"), Crane->IsAtServicePoint());
    TestTrue(TEXT("Support bridge reaches its approved X datum"),
        FMath::IsNearlyEqual(Crane->GetBridgeX(), -7600.0f, 0.1f));
    TestTrue(TEXT("Support trolley reaches its approved Y datum"),
        FMath::IsNearlyEqual(Crane->GetTrolleyY(), -3300.0f, 0.1f));
    TestTrue(TEXT("Support hook reaches its approved service height"),
        FMath::IsNearlyEqual(Crane->GetHookZ(), 760.0f, 0.1f));

    FLBSupportCraneSaveState StableServiceState;
    TestTrue(TEXT("On-station support state is saveable"), Crane->GetSaveState(StableServiceState));
    TestTrue(TEXT("On-station save is explicitly stable"), StableServiceState.bStableState);
    TestTrue(TEXT("Stable on-station save restores directly"), Crane->RestoreSaveState(StableServiceState));
    TestTrue(TEXT("Stable restore remains on station"), Crane->IsAtServicePoint());

    TestTrue(TEXT("Cleared support crane can return to park"), Crane->ReturnToPark());
    for (int32 Step = 0; Step < 500 && !Crane->IsParked(); ++Step)
    {
        Crane->Tick(0.1f);
    }
    TestTrue(TEXT("Support crane completes the cycle in its parked state"), Crane->IsParked());
    TestTrue(TEXT("Parked bridge returns to authored v035 X datum"),
        FMath::IsNearlyEqual(Crane->GetBridgeX(), -9100.0f, 0.1f));
    TestTrue(TEXT("Parked trolley returns to authored v035 Y datum"),
        FMath::IsNearlyEqual(Crane->GetTrolleyY(), -4700.0f, 0.1f));
    TestTrue(TEXT("Parked hook returns to authored v035 stow height"),
        FMath::IsNearlyEqual(Crane->GetHookZ(), 1010.0f, 0.1f));

    TestTrue(TEXT("Earlier moving save restores as a fail-stopped pose"),
        Crane->RestoreSaveState(MovingState));
    TestEqual(TEXT("Moving restore cannot resume unattended"), Crane->GetPhase(),
        ELBSupportCranePhase::Fault);
    TestEqual(TEXT("Moving restore reports the recovery interlock"), Crane->GetFault(),
        ELBSupportCraneFault::RestoreInterlockStop);
    TestTrue(TEXT("Named recovery may resume only after all safety proofs remain healthy"),
        Crane->ResetFault(TEXT("EVID_RESTORE_REVIEWED")));
    return true;
}

#endif
