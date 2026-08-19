#if WITH_DEV_AUTOMATION_TESTS

#include "LBFactoryManagementSubsystem.h"
#include "LBOneFactoryBootstrap.h"
#include "LBOneFactoryGameMode.h"
#include "LBOneFactoryPlayerBuilderSubsystem.h"
#include "LBOneFactoryProductionFlow.h"
#include "LBOneFactoryRuntimeCoordinator.h"
#include "LBPressShopBuildAuthority.h"

#include "Engine/World.h"
#include "EngineUtils.h"
#include "Misc/AutomationTest.h"

namespace LBOneFactoryEconomyBridgeTestsPrivate
{
    struct FEconomyWorld
    {
        UWorld* World = nullptr;
        ALBOneFactoryGameMode* GameMode = nullptr;
        ALBOneFactoryProductionFlowAuthority* Production = nullptr;
        ULBFactoryManagementSubsystem* Management = nullptr;

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
                OutReason = TEXT("ECONOMY TEST SHELL CREATION FAILED");
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
                OutReason = TEXT("ECONOMY TEST GAMEMODE CREATION FAILED");
                return false;
            }
            GameMode->DispatchBeginPlay();
            ULBOneFactoryPlayerBuilderSubsystem* Builder =
                World->GetSubsystem<ULBOneFactoryPlayerBuilderSubsystem>();
            Management =
                World->GetSubsystem<ULBFactoryManagementSubsystem>();
            if (!GameMode->HasValidRuntimeBackbone() || !Builder
                || !Management)
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
            for (TActorIterator<ALBOneFactoryProductionFlowAuthority>
                It(World); It; ++It)
            {
                Production = *It;
                break;
            }
            if (!Production)
            {
                OutReason = TEXT("ECONOMY TEST LEDGER MISSING");
                return false;
            }
            OutReason = TEXT("ECONOMY TEST WORLD READY");
            return true;
        }

        void Destroy()
        {
            if (World)
            {
                World->DestroyWorld(false);
            }
            *this = FEconomyWorld();
        }
    };
}

IMPLEMENT_SIMPLE_AUTOMATION_TEST(FLBOneFactoryEconomyBridgeTest,
    "LineBoss.OneFactory.RuntimeCoordinator.EconomyBridgeChargesCompletedHoursIdempotently",
    EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)

bool FLBOneFactoryEconomyBridgeTest::RunTest(const FString& Parameters)
{
    (void)Parameters;
    using namespace LBOneFactoryEconomyBridgeTestsPrivate;

    FString Reason;
    FEconomyWorld Fixture;
    if (!TestTrue(Reason, Fixture.Create(TEXT("LBEconomyBridgeWorld"),
            Reason)))
    {
        Fixture.Destroy();
        return false;
    }
    ALBOneFactoryRuntimeCoordinator* Coordinator =
        Fixture.GameMode->GetOneFactoryRuntimeCoordinator();

    // 2.5 completed simulation hours -> the campaign self-initialises and
    // exactly two hourly operating charges land.
    TestTrue(Reason,
        Fixture.Production->AdvanceSimulationClock(9000.0f, Reason));
    TestTrue(Reason, Coordinator->ReconcileEconomy(Reason));
    TestTrue(TEXT("campaign initialised by the bridge"),
        Fixture.Management->IsCampaignInitialised());
    const int64 Expected =
        ULBFactoryManagementSubsystem::DefaultStartingCashPence
        - 2 * 150000;
    TestEqual(TEXT("two completed hours charged"),
        Fixture.Management->GetCashBalancePence(), Expected);

    // Replays are no-ops: same clock, same charges.
    TestTrue(Reason, Coordinator->ReconcileEconomy(Reason));
    TestEqual(TEXT("reconcile is idempotent"),
        Fixture.Management->GetCashBalancePence(), Expected);

    // A fresh coordinator session (transient hour cursor reset) must not
    // double-charge either - the ledger ids carry the idempotency.
    Coordinator->LastChargedOpexHour = -1;
    TestTrue(Reason, Coordinator->ReconcileEconomy(Reason));
    TestEqual(TEXT("session restart does not double-charge"),
        Fixture.Management->GetCashBalancePence(), Expected);

    Fixture.Destroy();
    return true;
}

#endif
