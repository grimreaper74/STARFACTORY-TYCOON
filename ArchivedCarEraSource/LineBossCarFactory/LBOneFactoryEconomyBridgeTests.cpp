#if WITH_DEV_AUTOMATION_TESTS

#include "LBFactoryManagementSubsystem.h"
#include "LBOneFactoryBootstrap.h"
#include "LBOneFactoryBodyWeldStarterLayout.h"
#include "LBOneFactoryGameMode.h"
#include "LBOneFactoryPaintStarterLayout.h"
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
        ALBOneFactoryBodyWeldStarterLayoutAuthority* Body = nullptr;
        ALBOneFactoryPaintStarterLayoutAuthority* Paint = nullptr;
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
            for (TActorIterator<ALBOneFactoryBodyWeldStarterLayoutAuthority>
                It(World); It; ++It)
            {
                Body = *It;
                break;
            }
            for (TActorIterator<ALBOneFactoryPaintStarterLayoutAuthority>
                It(World); It; ++It)
            {
                Paint = *It;
                break;
            }
            if (!Production || !Body || !Paint)
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

    bool DriveUnitToDispatch(ALBOneFactoryRuntimeCoordinator* Coordinator,
        const FName UnitId, FString& OutReason)
    {
        if (!Coordinator || UnitId.IsNone())
        {
            OutReason = TEXT("ECONOMY DISPATCH DRIVER REQUIRES A COORDINATOR AND UNIT");
            return false;
        }
        for (int32 Guard = 0; Guard < 180; ++Guard)
        {
            FLBOneFactoryRuntimeVehicleStatus Status;
            if (!Coordinator->GetVehicleRuntimeStatus(UnitId, Status, OutReason))
            {
                return false;
            }
            if (Status.bDispatched)
            {
                OutReason = TEXT("ECONOMY DISPATCH DRIVER COMPLETE");
                return true;
            }
            if (Status.bAwaitingQualityResult)
            {
                const FName Evidence(*FString::Printf(
                    TEXT("ECONOMY_PASS_%d"), static_cast<int32>(Status.Stage)));
                if (!Coordinator->SubmitRuntimeQualityResult(UnitId,
                    ELBOneFactoryVehicleQualityState::Passed, Evidence, OutReason))
                {
                    return false;
                }
                continue;
            }
            if (!Coordinator->TickVehicle(UnitId, 1000.0f, OutReason))
            {
                return false;
            }
        }
        OutReason = TEXT("ECONOMY DISPATCH DRIVER EXHAUSTED ITS BOUNDED ROUTE");
        return false;
    }
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

IMPLEMENT_SIMPLE_AUTOMATION_TEST(FLBOneFactoryPlantMaintenanceEconomyTest,
    "LineBoss.OneFactory.RuntimeCoordinator.PlantMaintenanceChargesOnceAndResetsWear",
    EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)

bool FLBOneFactoryPlantMaintenanceEconomyTest::RunTest(const FString& Parameters)
{
    (void)Parameters;
    using namespace LBOneFactoryEconomyBridgeTestsPrivate;

    FString Reason;
    FEconomyWorld Fixture;
    if (!TestTrue(Reason, Fixture.Create(TEXT("LBPlantMaintenanceWorld"), Reason)))
    {
        Fixture.Destroy();
        return false;
    }
    ALBOneFactoryRuntimeCoordinator* Coordinator =
        Fixture.GameMode->GetOneFactoryRuntimeCoordinator();
    TestTrue(Reason, Fixture.Management->InitialiseNewCampaign(
        ULBFactoryManagementSubsystem::DefaultStartingCashPence, 0));

    FLBOneFactoryProductionLedgerState Ledger = Fixture.Production->CaptureLedger();
    Ledger.FleetWear01 = 0.35;
    TestTrue(Reason, Fixture.Production->RestoreLedger(Ledger, Reason));

    const int64 OpeningCash = Fixture.Management->GetCashBalancePence();
    TestTrue(Reason, Coordinator->PerformPlantMaintenance(Reason));
    const FLBOneFactoryProductionLedgerState Serviced =
        Fixture.Production->CaptureLedger();
    TestEqual(TEXT("maintenance resets actual accumulated fleet wear"),
        Serviced.FleetWear01, 0.0);
    TestEqual(TEXT("maintenance advances its persistent serial"),
        Serviced.MaintenanceSerial, 1);
    TestEqual(TEXT("maintenance posts exactly its ledger charge"),
        Fixture.Management->GetCashBalancePence(), OpeningCash - int64(2500000));

    TestTrue(Reason, Coordinator->PerformPlantMaintenance(Reason));
    TestEqual(TEXT("a clean plant does not incur a duplicate service fee"),
        Fixture.Management->GetCashBalancePence(), OpeningCash - int64(2500000));

    Fixture.Destroy();
    return true;
}

IMPLEMENT_SIMPLE_AUTOMATION_TEST(FLBOneFactoryVehicleDispatchRevenueTest,
    "LineBoss.OneFactory.RuntimeCoordinator.ContractedVehicleDispatchPostsRevenueExactlyOnce",
    EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)

bool FLBOneFactoryVehicleDispatchRevenueTest::RunTest(const FString& Parameters)
{
    (void)Parameters;
    using namespace LBOneFactoryEconomyBridgeTestsPrivate;

    FString Reason;
    FEconomyWorld Fixture;
    if (!TestTrue(TEXT("Revenue fixture commissions the actual player-built line"),
            Fixture.Create(TEXT("LBOneFactoryVehicleDispatchRevenue"), Reason)))
    {
        AddError(Reason);
        Fixture.Destroy();
        return false;
    }

    ALBOneFactoryRuntimeCoordinator* Coordinator =
        Fixture.GameMode->GetOneFactoryRuntimeCoordinator();
    const FName ModelId = Fixture.Body->CaptureLayout().VehicleModelId;
    const FName PaintProgrammeId = Fixture.Paint->CaptureLayout().PaintProgrammeId;
    // The player shell seeds introductory contracts.  This focused settlement
    // test needs one unambiguous buyer so it proves the quoted contract value,
    // rather than merely whichever starter offer happens to be oldest.
    FLBOneFactoryProductionLedgerState IsolatedLedger =
        Fixture.Production->CaptureLedger();
    IsolatedLedger.Contracts.Reset();
    TestTrue(TEXT("The revenue fixture isolates its explicit contract offer"),
        Fixture.Production->RestoreLedger(IsolatedLedger, Reason));
    FLBOneFactoryVehicleContract Contract;
    Contract.ContractId = TEXT("ECONOMY_VEHICLE_CONTRACT_001");
    Contract.VehicleModelId = ModelId;
    Contract.Quantity = 1;
    Contract.PricePerVehiclePence = 3500000;
    TestTrue(TEXT("A contracted vehicle programme is accepted"),
        Fixture.Production->AddVehicleContract(Contract, Reason));

    FName UnitId;
    TestTrue(TEXT("The contracted vehicle is created"),
        Coordinator->CreateRuntimeVehicleOrder(TEXT("ECONOMY_VEHICLE_ORDER_001"),
            ModelId, PaintProgrammeId, TEXT("CAIRNWELL_TEAL"),
            TEXT("ECONOMY_COIL_001"), UnitId, Reason));
    TestTrue(TEXT("The contracted vehicle starts"),
        Coordinator->StartVehicle(UnitId, Reason));
    TestTrue(TEXT("The vehicle traverses the live route and dispatches"),
        DriveUnitToDispatch(Coordinator, UnitId, Reason));

    const int64 OpeningCash = Fixture.Management->GetCashBalancePence();
    const int64 OpeningResearch = Fixture.Management->GetAvailableResearchPoints();
    TestTrue(TEXT("Dispatch reconciliation posts the contracted vehicle value"),
        Coordinator->ReconcileEconomy(Reason));
    TestEqual(TEXT("The full-car dispatch posts the contract price, not panel revenue"),
        Fixture.Management->GetCashBalancePence(),
        OpeningCash + Contract.PricePerVehiclePence);
    TestEqual(TEXT("A dispatched finished car also earns its progression reward"),
        Fixture.Management->GetAvailableResearchPoints(), OpeningResearch + int64(5));

    TestTrue(TEXT("Repeated reconciliation remains safe"),
        Coordinator->ReconcileEconomy(Reason));
    TestEqual(TEXT("The same dispatched unit cannot be paid twice"),
        Fixture.Management->GetCashBalancePence(),
        OpeningCash + Contract.PricePerVehiclePence);
    TestEqual(TEXT("Repeated reconciliation cannot farm dispatch research"),
        Fixture.Management->GetAvailableResearchPoints(), OpeningResearch + int64(5));

    Fixture.Destroy();
    return true;
}

#endif
