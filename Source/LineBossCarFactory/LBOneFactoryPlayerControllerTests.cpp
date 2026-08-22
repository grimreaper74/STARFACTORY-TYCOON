#if WITH_DEV_AUTOMATION_TESTS

#include "LBOneFactoryBootstrap.h"
#include "LBOneFactoryGameMode.h"
#include "LBOneFactoryPlayerBuilderSubsystem.h"
#include "LBOneFactoryPlayerController.h"
#include "LBOneFactoryProductionFlow.h"
#include "LBOneFactoryRuntimeCoordinator.h"
#include "LBManagementPawn.h"
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

        bool Create(const TCHAR* WorldName, FString& OutReason,
            const int32 InitialBuilderActions = 8)
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
            for (int32 Transition = 0; Transition < InitialBuilderActions;
                ++Transition)
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
    TestTrue(TEXT("keyboard 2 routes through the player controller"),
        Fixture.Controller->HandleKeyboardShortcut(EKeys::Two));
    TestEqual(TEXT("speed key sets the runtime scale"),
        Coordinator->GetRuntimeTimeScale(), 2.0f);

    TestTrue(TEXT("keyboard Space routes through the player controller"),
        Fixture.Controller->HandleKeyboardShortcut(EKeys::SpaceBar));
    TestTrue(TEXT("pause key sets the ledger's durable pause"),
        Fixture.Production->CaptureLedger().bLinePaused);

    int32 Processed = 0;
    FString TickReason;
    Coordinator->TickAutomaticFlow(1.0f, Processed, TickReason);
    TestEqual(TEXT("no unit advances while paused"), Processed, 0);

    TestTrue(TEXT("keyboard Space resumes through the player controller"),
        Fixture.Controller->HandleKeyboardShortcut(EKeys::SpaceBar));
    TestFalse(TEXT("second press resumes the ledger"),
        Fixture.Production->CaptureLedger().bLinePaused);
    TestEqual(TEXT("resume restores the player's chosen speed"),
        Coordinator->GetRuntimeTimeScale(), 2.0f);

    Fixture.Destroy();
    return true;
}

IMPLEMENT_SIMPLE_AUTOMATION_TEST(FLBOneFactoryPrebuiltPartialCompletionTest,
    "LineBoss.OneFactory.ActualPlayer.PreBuiltStartupCompletesPressOnlyFactory",
    EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)

bool FLBOneFactoryPrebuiltPartialCompletionTest::RunTest(
    const FString& Parameters)
{
    (void)Parameters;
    using namespace LBOneFactoryPlayerControllerTestsPrivate;

    FString Reason;
    FPlayerWorld Fixture;
    // Two UMG transitions produce and commission only the Press starter: the
    // exact partial state that used to be mistaken for a commissioned factory
    // in the player map.
    if (!TestTrue(Reason, Fixture.Create(TEXT("LBPrebuiltPartialWorld"),
            Reason, 2)))
    {
        Fixture.Destroy();
        return false;
    }

    TestFalse(TEXT("press-only factory cannot validate the full runtime"),
        Fixture.GameMode->GetOneFactoryRuntimeCoordinator()
            ->ValidateRuntimeFactory(Reason));

    TestTrue(TEXT("player startup completes the missing departments"),
        Fixture.Controller->ActivatePrebuiltFactory(Reason));
    TestTrue(TEXT("completed prebuilt factory validates the 57-station runtime"),
        Fixture.GameMode->GetOneFactoryRuntimeCoordinator()
            ->ValidateRuntimeFactory(Reason));

    Fixture.Destroy();
    return true;
}

IMPLEMENT_SIMPLE_AUTOMATION_TEST(FLBOneFactoryDirectKeyboardNavigationTest,
    "LineBoss.OneFactory.ActualPlayer.DirectKeyboardNavigationSurvivesUMGFocus",
    EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)

bool FLBOneFactoryDirectKeyboardNavigationTest::RunTest(
    const FString& Parameters)
{
    (void)Parameters;
    UWorld* World = UWorld::CreateWorld(EWorldType::Game, false,
        TEXT("LBDirectKeyboardNavigationWorld"));
    ALBManagementPawn* Pawn = World
        ? World->SpawnActor<ALBManagementPawn>() : nullptr;
    if (!TestNotNull(TEXT("management pawn exists"), Pawn))
    {
        if (World) World->DestroyWorld(false);
        return false;
    }

    const FVector Start = Pawn->GetActorLocation();
    TestTrue(TEXT("W is accepted by the direct UMG-proof navigation route"),
        Pawn->HandleDirectNavigationKey(EKeys::W, true));
    Pawn->Tick(0.25f);
    TestTrue(TEXT("held W moves the management camera pivot"),
        FVector::DistSquared2D(Start, Pawn->GetActorLocation()) > 1.0f);

    const FVector AfterMove = Pawn->GetActorLocation();
    TestTrue(TEXT("W release is accepted by the direct route"),
        Pawn->HandleDirectNavigationKey(EKeys::W, false));
    Pawn->Tick(0.25f);
    TestTrue(TEXT("released W stops camera pivot movement"),
        Pawn->GetActorLocation().Equals(AfterMove, 0.1f));
    const float ZoomBefore = Pawn->GetManagementZoomDistance();
    TestTrue(TEXT("mouse-wheel fallback accepts a non-zero wheel delta"),
        Pawn->HandleDirectZoomInput(1.0f));
    Pawn->Tick(0.25f);
    TestTrue(TEXT("mouse-wheel fallback changes the management zoom"),
        !FMath::IsNearlyEqual(ZoomBefore, Pawn->GetManagementZoomDistance()));
    TestTrue(TEXT("mouse-wheel fallback rejects a zero wheel delta"),
        !Pawn->HandleDirectZoomInput(0.0f));
    TestTrue(TEXT("non-navigation key is not consumed"),
        !Pawn->HandleDirectNavigationKey(EKeys::N, true));

    World->DestroyWorld(false);
    return true;
}

#endif
