#if WITH_DEV_AUTOMATION_TESTS

#include "LBControlRoomHUD.h"
#include "LBOneFactoryBootstrap.h"
#include "LBOneFactoryAssemblyStarterLayout.h"
#include "LBOneFactoryAssemblyStarterPresentationActor.h"
#include "LBOneFactoryBodyWeldStarterLayout.h"
#include "LBOneFactoryBodyWeldStarterPresentationActor.h"
#include "LBOneFactoryGameMode.h"
#include "LBOneFactoryOperationsSubsystem.h"
#include "LBOneFactoryPaintStarterLayout.h"
#include "LBOneFactoryPaintStarterPresentationActor.h"
#include "LBOneFactoryPlayerBuilderSubsystem.h"
#include "LBOneFactoryPressStarterLayout.h"
#include "LBOneFactoryPressStarterPresentationActor.h"
#include "LBOneFactoryProductionFlow.h"
#include "LBOneFactorySaveSubsystem.h"
#include "LBPressShopBuildAuthority.h"

#include "Engine/World.h"
#include "EngineUtils.h"
#include "Misc/AutomationTest.h"

namespace LBOneFactoryActualPlayerIntegrationTestsPrivate
{
    template<typename ActorType>
    int32 CountLiveActors(UWorld* World)
    {
        int32 Count = 0;
        if (!World) return Count;
        for (TActorIterator<ActorType> It(World); It; ++It)
            if (IsValid(*It) && !It->IsActorBeingDestroyed()) ++Count;
        return Count;
    }

    void ConfigureCanonicalAuthority(ALBPressShopBuildAuthority& Authority)
    {
        const FLBOneFactoryLayoutDefinition Layout =
            ULBOneFactoryLayoutLibrary::MakeMoorcrossWorksShellLayout();
        ULBOneFactoryLayoutLibrary::BuildExpectedPressAuthorityContract(Layout,
            Authority.BuildBays, Authority.ProtectedAreas,
            Authority.UtilitySpines, Authority.LogisticsSpines);
        Authority.StorageBays.Reset();
        Authority.SetActorTransform(FTransform::Identity);
        Authority.Tags.AddUnique(
            ALBOneFactoryBootstrap::GetPressBuildAuthorityTag());
        Authority.Tags.AddUnique(ALBOneFactoryBootstrap::GetNativeOnlyTag());
    }

    struct FActualPlayerWorld
    {
        UWorld* World = nullptr;
        ALBOneFactoryBootstrap* Bootstrap = nullptr;
        ALBPressShopBuildAuthority* MapBuildAuthority = nullptr;
        ALBOneFactoryGameMode* GameMode = nullptr;
        ULBOneFactoryPlayerBuilderSubsystem* Builder = nullptr;
        ULBOneFactoryOperationsSubsystem* Operations = nullptr;
        ULBOneFactorySaveSubsystem* Save = nullptr;

        bool CreateShell(const TCHAR* WorldName, FString& OutReason)
        {
            World = UWorld::CreateWorld(EWorldType::Game, false,
                FName(WorldName));
            Bootstrap = World
                ? World->SpawnActor<ALBOneFactoryBootstrap>() : nullptr;
            MapBuildAuthority = World
                ? World->SpawnActor<ALBPressShopBuildAuthority>() : nullptr;
            if (!World || !Bootstrap || !MapBuildAuthority)
            {
                OutReason = TEXT("ACTUAL-PLAYER TEST SHELL CREATION FAILED");
                return false;
            }
            ConfigureCanonicalAuthority(*MapBuildAuthority);
            Bootstrap->DispatchBeginPlay();
            GameMode = World->SpawnActor<ALBOneFactoryGameMode>();
            if (!GameMode)
            {
                OutReason = TEXT("ACTUAL-PLAYER TEST GAMEMODE CREATION FAILED");
                return false;
            }
            GameMode->DispatchBeginPlay();
            Builder = World->GetSubsystem<
                ULBOneFactoryPlayerBuilderSubsystem>();
            Operations = World->GetSubsystem<
                ULBOneFactoryOperationsSubsystem>();
            Save = World->GetSubsystem<ULBOneFactorySaveSubsystem>();
            if (!Bootstrap->HasValidShell()
                || !GameMode->HasValidOneFactoryShell()
                || !GameMode->HasValidRuntimeBackbone()
                || !Builder || !Operations || !Save)
            {
                OutReason = GameMode->GetOneFactoryStartupStatus();
                return false;
            }
            GameMode->GetOneFactoryRuntimeCoordinator()
                ->bAdvanceStartedVehiclesOnActorTick = false;
            OutReason = TEXT("ACTUAL-PLAYER ONEFACTORY SHELL READY");
            return true;
        }

        bool BuildAndCommissionThroughUMGModel(FString& OutReason)
        {
            if (!Builder)
            {
                OutReason = TEXT("ACTUAL-PLAYER BUILDER IS UNAVAILABLE");
                return false;
            }
            // One stable native-UMG lifecycle button: create/commission each of
            // Press, Body/Weld, Paint and Assembly in dependency order.
            for (int32 Transition = 0; Transition < 8; ++Transition)
                if (!Builder->ExecuteUMGAction(0, OutReason)) return false;
            return GameMode->GetOneFactoryRuntimeCoordinator()
                ->ValidateRuntimeFactory(OutReason);
        }

        ALBControlRoomHUD* CreateHUD()
        {
            return World ? World->SpawnActor<ALBControlRoomHUD>() : nullptr;
        }

        void Destroy()
        {
            if (World) World->DestroyWorld(false);
            *this = FActualPlayerWorld();
        }
    };
}

IMPLEMENT_SIMPLE_AUTOMATION_TEST(
    FLBOneFactoryActualPlayerHUDVehicleLoopTest,
    "LineBoss.OneFactory.ActualPlayer.NativeUMGFull57StationQualityReworkLoop",
    EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)

bool FLBOneFactoryActualPlayerHUDVehicleLoopTest::RunTest(
    const FString& Parameters)
{
    (void)Parameters;
    using namespace LBOneFactoryActualPlayerIntegrationTestsPrivate;
    FString Reason;
    FActualPlayerWorld Fixture;
    if (!TestTrue(TEXT("Real GameMode creates the actual-player shell/backbone"),
            Fixture.CreateShell(TEXT("LBOneFactoryActualPlayerHUDLoop"), Reason))
        || !TestTrue(TEXT("The public builder UMG model commissions all 57 positions"),
            Fixture.BuildAndCommissionThroughUMGModel(Reason)))
    {
        AddError(Reason);
        Fixture.Destroy();
        return false;
    }

    TArray<FLBOneFactoryRuntimeStationStep> Route;
    FName TopologyId;
    TestTrue(TEXT("Configured physical route resolves after the player lifecycle"),
        Fixture.GameMode->GetOneFactoryRuntimeCoordinator()
            ->GetConfiguredStationRoute(Route, TopologyId, Reason));
    TestEqual(TEXT("The player-built factory exposes exactly 57 positions"),
        Route.Num(), ALBOneFactoryRuntimeCoordinator::RequiredPhysicalStationCount);

    ALBControlRoomHUD* HUD = Fixture.CreateHUD();
    if (!TestNotNull(TEXT("Actual-player native management HUD exists"), HUD))
    {
        Fixture.Destroy();
        return false;
    }
    HUD->OpenManagementPage(ELBManagementPage::Production);
    TestEqual(TEXT("OneFactory Production keeps the existing five UMG slots"),
        HUD->GetManagementActionCount(),
        ULBOneFactoryOperationsSubsystem::UMGActionCount);
    TestTrue(TEXT("HUD action creates one configured logical vehicle"),
        HUD->ActivateManagementAction(0));
    const FName UnitId = Fixture.Operations->GetSelectedUnitId();
    TestFalse(TEXT("Create action selects a stable UnitId"), UnitId.IsNone());
    TestTrue(TEXT("HUD action explicitly starts the selected vehicle"),
        HUD->ActivateManagementAction(2));

    bool bExercisedRework = false;
    bool bDispatched = false;
    for (int32 Guard = 0; Guard < 180 && !bDispatched; ++Guard)
    {
        FLBOneFactoryRuntimeVehicleStatus Status;
        if (!Fixture.GameMode->GetOneFactoryRuntimeCoordinator()
                ->GetVehicleRuntimeStatus(UnitId, Status, Reason))
        {
            AddError(Reason);
            break;
        }
        if (Status.bDispatched)
        {
            bDispatched = true;
            break;
        }
        if (Status.bAwaitingQualityResult)
        {
            if (!bExercisedRework)
            {
                TestTrue(TEXT("HUD requests rework at a completed quality gate"),
                    HUD->ActivateManagementAction(4));
                TestTrue(TEXT("The same HUD slot records completion of rework"),
                    HUD->ActivateManagementAction(4));
                TestTrue(TEXT("HUD reruns the reset inspection cycle"),
                    HUD->ActivateManagementAction(2));
                bExercisedRework = true;
            }
            TestTrue(TEXT("HUD records a passing quality decision"),
                HUD->ActivateManagementAction(3));
        }
        else
        {
            TestTrue(TEXT("HUD advances one deterministic station cycle"),
                HUD->ActivateManagementAction(2));
        }
    }

    TestTrue(TEXT("The actual-player path exercises quality rework"),
        bExercisedRework);
    TestTrue(TEXT("The same UnitId completes and dispatches all 57 positions"),
        bDispatched);
    const FLBOneFactoryProductionLedgerState Ledger =
        Fixture.GameMode->GetOneFactoryProductionFlow()->CaptureLedger();
    TestEqual(TEXT("Exactly one vehicle is completed"),
        Ledger.CompletedVehicleCount, 1);
    TestEqual(TEXT("Exactly one vehicle is dispatched"),
        Ledger.DispatchedVehicleCount, 1);
    Fixture.Destroy();
    return true;
}

IMPLEMENT_SIMPLE_AUTOMATION_TEST(
    FLBOneFactoryTwoWorldFreshRestoreTest,
    "LineBoss.OneFactory.ActualPlayer.TwoWorldFreshSessionRestoreAndHUDContinue",
    EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)

bool FLBOneFactoryTwoWorldFreshRestoreTest::RunTest(
    const FString& Parameters)
{
    (void)Parameters;
    using namespace LBOneFactoryActualPlayerIntegrationTestsPrivate;
    FString Reason;
    FLBOneFactorySaveState SavedState;
    FName UnitId = NAME_None;
    FLBOneFactoryRuntimeVehicleStatus Before;

    FActualPlayerWorld SessionA;
    if (!TestTrue(TEXT("Session A starts through the real GameMode"),
            SessionA.CreateShell(TEXT("LBOneFactoryTwoWorldSessionA"), Reason))
        || !TestTrue(TEXT("Session A builds through the public UMG lifecycle"),
            SessionA.BuildAndCommissionThroughUMGModel(Reason)))
    {
        AddError(Reason);
        SessionA.Destroy();
        return false;
    }
    ALBControlRoomHUD* HUDA = SessionA.CreateHUD();
    if (!TestNotNull(TEXT("Session A public HUD exists"), HUDA))
    {
        SessionA.Destroy();
        return false;
    }
    HUDA->OpenManagementPage(ELBManagementPage::Production);
    TestTrue(TEXT("Session A creates a vehicle through HUD"),
        HUDA->ActivateManagementAction(0));
    UnitId = SessionA.Operations->GetSelectedUnitId();
    TestTrue(TEXT("Session A starts through HUD"),
        HUDA->ActivateManagementAction(2));
    TestTrue(TEXT("Session A advances through HUD"),
        HUDA->ActivateManagementAction(2));
    TestTrue(TEXT("Session A status is readable before save"),
        SessionA.GameMode->GetOneFactoryRuntimeCoordinator()
            ->GetVehicleRuntimeStatus(UnitId, Before, Reason));
    TestTrue(TEXT("Session A captures the complete save payload"),
        SessionA.Save->CaptureCurrentFactory(SavedState, Reason));
    SessionA.Destroy();

    FActualPlayerWorld SessionB;
    if (!TestTrue(TEXT("Session B starts as a genuinely empty shell"),
            SessionB.CreateShell(TEXT("LBOneFactoryTwoWorldSessionB"), Reason)))
    {
        AddError(Reason);
        SessionB.Destroy();
        return false;
    }
    TestEqual(TEXT("Fresh Session B initially has no starter actors"),
        CountLiveActors<ALBOneFactoryPressStarterLayoutAuthority>(
            SessionB.World), 0);
    if (!TestTrue(TEXT("Fresh restore materialises saved actors transactionally"),
            SessionB.Save->RestoreFactoryState(SavedState, Reason)))
    {
        AddError(Reason);
        SessionB.Destroy();
        return false;
    }
    TestEqual(TEXT("Fresh restore creates exactly one Press data authority"),
        CountLiveActors<ALBOneFactoryPressStarterLayoutAuthority>(
            SessionB.World), 1);
    TestEqual(TEXT("Fresh restore creates exactly one Body data authority"),
        CountLiveActors<ALBOneFactoryBodyWeldStarterLayoutAuthority>(
            SessionB.World), 1);
    TestEqual(TEXT("Fresh restore creates exactly one Paint data authority"),
        CountLiveActors<ALBOneFactoryPaintStarterLayoutAuthority>(
            SessionB.World), 1);
    TestEqual(TEXT("Fresh restore creates exactly one Assembly data authority"),
        CountLiveActors<ALBOneFactoryAssemblyStarterLayoutAuthority>(
            SessionB.World), 1);

    FLBOneFactoryRuntimeVehicleStatus After;
    TestTrue(TEXT("Session B restores the same UnitId into the coordinator"),
        SessionB.GameMode->GetOneFactoryRuntimeCoordinator()
            ->GetVehicleRuntimeStatus(UnitId, After, Reason));
    TestEqual(TEXT("Fresh restore preserves the physical station cursor"),
        After.StationCursor, Before.StationCursor);
    TestEqual(TEXT("Fresh restore preserves completed-station progress"),
        After.CompletedStationCount, Before.CompletedStationCount);
    TestEqual(TEXT("Fresh restore preserves explicit started state"),
        After.bStarted, Before.bStarted);

    ALBControlRoomHUD* HUDB = SessionB.CreateHUD();
    if (!TestNotNull(TEXT("Session B public HUD exists"), HUDB))
    {
        SessionB.Destroy();
        return false;
    }
    HUDB->OpenManagementPage(ELBManagementPage::Production);
    TestEqual(TEXT("Restored session remains on the five-action OneFactory route"),
        HUDB->GetManagementActionCount(),
        ULBOneFactoryOperationsSubsystem::UMGActionCount);
    TestTrue(TEXT("Restored WIP continues through the public HUD action"),
        HUDB->ActivateManagementAction(2));
    FLBOneFactoryRuntimeVehicleStatus Continued;
    TestTrue(TEXT("Continued restored WIP remains coherent"),
        SessionB.GameMode->GetOneFactoryRuntimeCoordinator()
            ->GetVehicleRuntimeStatus(UnitId, Continued, Reason));
    TestTrue(TEXT("Continuation advances beyond the saved cursor"),
        Continued.StationCursor > After.StationCursor
            || Continued.CycleElapsedSeconds > After.CycleElapsedSeconds);
    HUDB->OpenManagementPage(ELBManagementPage::Analytics);
    TestEqual(TEXT("Restored OneFactory routes Analytics to isolated save/load"),
        HUDB->GetManagementActionCount(), 2);
    SessionB.Destroy();
    return true;
}

IMPLEMENT_SIMPLE_AUTOMATION_TEST(
    FLBOneFactoryFreshRestoreRollbackTest,
    "LineBoss.OneFactory.ActualPlayer.FreshRestoreFailureDestroysOnlyMaterialisedActors",
    EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)

bool FLBOneFactoryFreshRestoreRollbackTest::RunTest(
    const FString& Parameters)
{
    (void)Parameters;
    using namespace LBOneFactoryActualPlayerIntegrationTestsPrivate;
    FString Reason;
    FLBOneFactorySaveState SavedState;

    FActualPlayerWorld SourceSession;
    if (!TestTrue(TEXT("Rollback source session starts"),
            SourceSession.CreateShell(
                TEXT("LBOneFactoryFreshRollbackSource"), Reason))
        || !TestTrue(TEXT("Rollback source session builds through UMG"),
            SourceSession.BuildAndCommissionThroughUMGModel(Reason))
        || !TestTrue(TEXT("Rollback source state captures"),
            SourceSession.Save->CaptureCurrentFactory(SavedState, Reason)))
    {
        AddError(Reason);
        SourceSession.Destroy();
        return false;
    }
    SourceSession.Destroy();

    FActualPlayerWorld FreshSession;
    if (!TestTrue(TEXT("Rollback target starts as a fresh GameMode shell"),
            FreshSession.CreateShell(
                TEXT("LBOneFactoryFreshRollbackTarget"), Reason)))
    {
        AddError(Reason);
        FreshSession.Destroy();
        return false;
    }
    FreshSession.Save->SetForcePresentationFailureForTests(true);
    TestFalse(TEXT("Injected post-materialisation failure rejects restore"),
        FreshSession.Save->RestoreFactoryState(SavedState, Reason));
    FreshSession.Save->SetForcePresentationFailureForTests(false);
    TestTrue(TEXT("Failure reports fresh-shell transactional rollback"),
        Reason.Contains(TEXT("FRESH RESTORE ROLLED BACK")));
    TestEqual(TEXT("Rollback removes the newly materialised Press data actor"),
        CountLiveActors<ALBOneFactoryPressStarterLayoutAuthority>(
            FreshSession.World), 0);
    TestEqual(TEXT("Rollback removes the newly materialised Press presentation"),
        CountLiveActors<ALBOneFactoryPressStarterPresentationActor>(
            FreshSession.World), 0);
    TestEqual(TEXT("Rollback removes the newly materialised Body data actor"),
        CountLiveActors<ALBOneFactoryBodyWeldStarterLayoutAuthority>(
            FreshSession.World), 0);
    TestEqual(TEXT("Rollback removes the newly materialised Body presentation"),
        CountLiveActors<ALBOneFactoryBodyWeldStarterPresentationActor>(
            FreshSession.World), 0);
    TestEqual(TEXT("Rollback removes the newly materialised Paint data actor"),
        CountLiveActors<ALBOneFactoryPaintStarterLayoutAuthority>(
            FreshSession.World), 0);
    TestEqual(TEXT("Rollback removes the newly materialised Paint presentation"),
        CountLiveActors<ALBOneFactoryPaintStarterPresentationActor>(
            FreshSession.World), 0);
    TestEqual(TEXT("Rollback removes the newly materialised Assembly data actor"),
        CountLiveActors<ALBOneFactoryAssemblyStarterLayoutAuthority>(
            FreshSession.World), 0);
    TestEqual(TEXT("Rollback removes the newly materialised Assembly presentation"),
        CountLiveActors<ALBOneFactoryAssemblyStarterPresentationActor>(
            FreshSession.World), 0);
    const FLBOneFactoryProductionLedgerState RolledBackLedger =
        FreshSession.GameMode->GetOneFactoryProductionFlow()->CaptureLedger();
    TestTrue(TEXT("Rollback restores the fresh empty production ledger"),
        RolledBackLedger.Units.IsEmpty()
            && !RolledBackLedger.Commissioning.bPressCommissioned
            && !RolledBackLedger.Commissioning.bBodyCommissioned
            && !RolledBackLedger.Commissioning.bPaintCommissioned
            && !RolledBackLedger.Commissioning.bAssemblyCommissioned);
    TestEqual(TEXT("Rollback leaves no stale player-builder selection"),
        FreshSession.Builder->GetSelectedTargetKind(),
        ELBOneFactoryBuilderTargetKind::None);
    FreshSession.Destroy();
    return true;
}

#endif
