#if WITH_DEV_AUTOMATION_TESTS

#include "LBOneFactoryBootstrap.h"
#include "LBOneFactoryGameMode.h"
#include "LBOneFactoryPlayerBuilderSubsystem.h"
#include "LBOneFactoryPlayerController.h"
#include "LBOneFactoryProductionFlow.h"
#include "LBOneFactoryRuntimeCoordinator.h"
#include "LBPressShopBuildAuthority.h"

#include "Engine/World.h"
#include "EngineUtils.h"
#include "Misc/AutomationTest.h"

namespace LBOneFactoryPlayerControllerTestsPrivate
{
    struct FPlayerWorld
    {
        UWorld* World = nullptr;
        ALBOneFactoryGameMode* GameMode = nullptr;
        ALBOneFactoryPlayerController* Controller = nullptr;
        ALBOneFactoryProductionFlowAuthority* Production = nullptr;

        bool Create(const TCHAR* WorldName, FString& OutReason)
        {
            World = UWorld::CreateWorld(EWorldType::Game, false,
                FName(WorldName));
            ALBOneFactoryBootstrap* Bootstrap = World
                ? World->SpawnActor<ALBOneFactoryBootstrap>() : nullptr;
            ALBPressShopBuildAuthority* MapAuthority = World
                ? World->SpawnActor<ALBPressShopBuildAuthority>() : nullptr;
            if (!World || !Bootstrap || !MapAuthority)
            {
                OutReason = TEXT("PLAYER TEST SHELL CREATION FAILED");
                return false;
            }
            const FLBOneFactoryLayoutDefinition Layout =
                ULBOneFactoryLayoutLibrary::MakeMoorcrossWorksShellLayout();
            ULBOneFactoryLayoutLibrary::BuildExpectedPressAuthorityContract(
                Layout, MapAuthority->BuildBays, MapAuthority->ProtectedAreas,
                MapAuthority->UtilitySpines, MapAuthority->LogisticsSpines);
            MapAuthority->StorageBays.Reset();
            MapAuthority->SetActorTransform(FTransform::Identity);
            MapAuthority->Tags.AddUnique(
                ALBOneFactoryBootstrap::GetPressBuildAuthorityTag());
            MapAuthority->Tags.AddUnique(
                ALBOneFactoryBootstrap::GetNativeOnlyTag());
            Bootstrap->DispatchBeginPlay();
            GameMode = World->SpawnActor<ALBOneFactoryGameMode>();
            if (!GameMode)
            {
                OutReason = TEXT("PLAYER TEST GAMEMODE CREATION FAILED");
                return false;
            }
            GameMode->DispatchBeginPlay();
            ULBOneFactoryPlayerBuilderSubsystem* Builder =
                World->GetSubsystem<ULBOneFactoryPlayerBuilderSubsystem>();
            if (!GameMode->HasValidRuntimeBackbone() || !Builder)
            {
                OutReason = GameMode->GetOneFactoryStartupStatus();
                return false;
            }
            GameMode->GetOneFactoryRuntimeCoordinator()
                ->bAdvanceStartedVehiclesOnActorTick = false;
            for (int32 Transition = 0; Transition < 8; ++Transition)
            {
                if (!Builder->ExecuteUMGAction(0, OutReason))
                {
                    return false;
                }
            }
            Controller = World->SpawnActor<ALBOneFactoryPlayerController>();
            for (TActorIterator<ALBOneFactoryProductionFlowAuthority>
                It(World); It; ++It)
            {
                Production = *It;
                break;
            }
            if (!Controller || !Production)
            {
                OutReason = TEXT("PLAYER TEST CONTROLLER OR LEDGER MISSING");
                return false;
            }
            OutReason = TEXT("PLAYER TEST WORLD READY");
            return true;
        }

        void Destroy()
        {
            if (World)
            {
                World->DestroyWorld(false);
            }
            *this = FPlayerWorld();
        }
    };
}

IMPLEMENT_SIMPLE_AUTOMATION_TEST(FLBOneFactoryPlayerPauseKeyTest,
    "LineBoss.OneFactory.ActualPlayer.PauseKeyDrivesDurableLedgerPause",
    EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)

bool FLBOneFactoryPlayerPauseKeyTest::RunTest(const FString& Parameters)
{
    (void)Parameters;
    using namespace LBOneFactoryPlayerControllerTestsPrivate;

    FString Reason;
    FPlayerWorld Fixture;
    if (!TestTrue(Reason, Fixture.Create(TEXT("LBPlayerPauseKeyWorld"),
            Reason)))
    {
        Fixture.Destroy();
        return false;
    }

    ALBOneFactoryRuntimeCoordinator* Coordinator =
        Fixture.GameMode->GetOneFactoryRuntimeCoordinator();
    TestFalse(TEXT("line starts unpaused"),
        Fixture.Production->CaptureLedger().bLinePaused);

    // The player picks 2x, then pauses: the pause must land on the durable
    // ledger flag (the coordinator scale cannot express 0), and resuming
    // must restore the chosen speed rather than resetting to 1x.
    Fixture.Controller->SetSpeedFast();
    TestEqual(TEXT("speed key sets the runtime scale"),
        Coordinator->GetRuntimeTimeScale(), 2.0f);

    Fixture.Controller->TogglePause();
    TestTrue(TEXT("pause key sets the ledger's durable pause"),
        Fixture.Production->CaptureLedger().bLinePaused);

    int32 Processed = 0;
    FString TickReason;
    Coordinator->TickAutomaticFlow(1.0f, Processed, TickReason);
    TestEqual(TEXT("no unit advances while paused"), Processed, 0);

    Fixture.Controller->TogglePause();
    TestFalse(TEXT("second press resumes the ledger"),
        Fixture.Production->CaptureLedger().bLinePaused);
    TestEqual(TEXT("resume restores the player's chosen speed"),
        Coordinator->GetRuntimeTimeScale(), 2.0f);

    Fixture.Destroy();
    return true;
}

#endif
