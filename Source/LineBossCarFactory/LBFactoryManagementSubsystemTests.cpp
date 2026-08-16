#include "LBFactoryManagementSubsystem.h"

#include "Engine/World.h"
#include "Misc/AutomationTest.h"

#if WITH_DEV_AUTOMATION_TESTS

namespace
{
    ULBFactoryManagementSubsystem* NewManagementAuthority(UWorld*& OutWorld, const TCHAR* Name)
    {
        OutWorld = UWorld::CreateWorld(EWorldType::Game, false, FName(Name));
        return OutWorld ? NewObject<ULBFactoryManagementSubsystem>(OutWorld) : nullptr;
    }

    void DestroyManagementWorld(UWorld* World)
    {
        if (World) World->DestroyWorld(false);
    }
}

IMPLEMENT_SIMPLE_AUTOMATION_TEST(FLBManagementFinanceResearchUpgradeTest,
    "LineBoss.Management.Authority.FinanceResearchUpgradeAtomicity",
    EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)

bool FLBManagementFinanceResearchUpgradeTest::RunTest(const FString& Parameters)
{
    UWorld* World = nullptr;
    ULBFactoryManagementSubsystem* Management = NewManagementAuthority(
        World, TEXT("LB_ManagementFinanceResearch"));
    TestNotNull(TEXT("Persistent management authority exists"), Management);
    if (!Management) { DestroyManagementWorld(World); return false; }

    int32 ChangeNotifications = 0;
    int32 LedgerNotifications = 0;
    FName LastCause = NAME_None;
    Management->OnManagementChanged().AddLambda(
        [&ChangeNotifications, &LastCause](const FLBFactoryManagementSnapshot&, const FName Cause)
        {
            ++ChangeNotifications;
            LastCause = Cause;
        });
    Management->OnFinancialTransactionCommitted().AddLambda(
        [&LedgerNotifications](const FLBManagementLedgerEntry&) { ++LedgerNotifications; });

    TestTrue(TEXT("New campaign receives an exact opening balance and research allocation"),
        Management->InitialiseNewCampaign(1000000, 100));
    TestEqual(TEXT("Opening cash is integer pence"), Management->GetCashBalancePence(), int64(1000000));
    TestTrue(TEXT("Capital purchase commits only when the exact asset is affordable"),
        Management->TryPurchaseCapitalAsset(TEXT("TX-CAP-001"), TEXT("PRESS-01"), 200000));
    TestTrue(TEXT("Operating cost posts against an exact cost centre"),
        Management->TryChargeOperatingCost(TEXT("TX-OPEX-001"), TEXT("ENERGY-PRESS"), 50000));
    TestTrue(TEXT("Completed order revenue posts against an exact order"),
        Management->TryRecordOrderRevenue(TEXT("TX-REV-001"), TEXT("ORDER-2040-001"), 125000));
    TestEqual(TEXT("Ledger reconciles purchases, operating cost and revenue"),
        Management->GetCashBalancePence(), int64(875000));

    const int64 RevisionBeforeDuplicate = Management->GetSnapshot().Revision;
    TestFalse(TEXT("Duplicate transaction ID cannot charge twice"),
        Management->TryChargeOperatingCost(TEXT("TX-OPEX-001"), TEXT("ENERGY-PRESS"), 50000));
    TestEqual(TEXT("Duplicate financial rejection is atomic"),
        Management->GetCashBalancePence(), int64(875000));
    TestEqual(TEXT("Rejected duplicate does not advance authority revision"),
        Management->GetSnapshot().Revision, RevisionBeforeDuplicate);
    TestFalse(TEXT("The same capital asset cannot be purchased under another transaction"),
        Management->TryPurchaseCapitalAsset(TEXT("TX-CAP-002"), TEXT("PRESS-01"), 100000));
    TestFalse(TEXT("Whitespace makes an integration identity invalid"),
        Management->TryRecordOrderRevenue(TEXT("BAD EVENT"), TEXT("ORDER-2"), 1));

    TestTrue(TEXT("Research grant is an exact idempotent event"),
        Management->GrantResearchPoints(TEXT("RP-GRANT-001"), TEXT("ORDER-2040-001"), 40));
    TestTrue(TEXT("Research can unlock a named production technology"),
        Management->TryUnlockResearch(TEXT("RP-UNLOCK-001"), TEXT("SERVO-PRESS-II"), 60));
    TestTrue(TEXT("Unlock is queryable by the immutable technology ID"),
        Management->HasResearchUnlock(TEXT("SERVO-PRESS-II")));
    TestEqual(TEXT("Research opening, earned and spent totals reconcile"),
        Management->GetAvailableResearchPoints(), int64(80));

    TestTrue(TEXT("Unlocked machine upgrade purchases exactly the next level"),
        Management->TryPurchaseMachineUpgrade(TEXT("TX-UPG-001"), TEXT("PRESS-01"),
            TEXT("SERVO-DRIVE"), 1, 300000, TEXT("SERVO-PRESS-II")));
    TestEqual(TEXT("Purchased upgrade exposes its exact level"),
        Management->GetMachineUpgradeLevel(TEXT("PRESS-01"), TEXT("SERVO-DRIVE")), 1);
    TestTrue(TEXT("A second purchase advances the same upgrade by exactly one level"),
        Management->TryPurchaseMachineUpgrade(TEXT("TX-UPG-002"), TEXT("PRESS-01"),
            TEXT("SERVO-DRIVE"), 2, 100000, TEXT("SERVO-PRESS-II")));
    TestEqual(TEXT("Second upgrade level is exact"),
        Management->GetMachineUpgradeLevel(TEXT("PRESS-01"), TEXT("SERVO-DRIVE")), 2);
    const int64 CashBeforeRejectedUpgrade = Management->GetCashBalancePence();
    const int64 RevisionBeforeRejectedUpgrade = Management->GetSnapshot().Revision;
    TestFalse(TEXT("Upgrade levels cannot be skipped"),
        Management->TryPurchaseMachineUpgrade(TEXT("TX-UPG-003"), TEXT("PRESS-01"),
            TEXT("SERVO-DRIVE"), 4, 1, TEXT("SERVO-PRESS-II")));
    TestFalse(TEXT("Unaffordable upgrade cannot partially change a machine"),
        Management->TryPurchaseMachineUpgrade(TEXT("TX-UPG-004"), TEXT("PRESS-01"),
            TEXT("SERVO-DRIVE"), 3, 900000, TEXT("SERVO-PRESS-II")));
    TestEqual(TEXT("Rejected upgrades preserve level"),
        Management->GetMachineUpgradeLevel(TEXT("PRESS-01"), TEXT("SERVO-DRIVE")), 2);
    TestEqual(TEXT("Rejected upgrades preserve cash"),
        Management->GetCashBalancePence(), CashBeforeRejectedUpgrade);
    TestEqual(TEXT("Rejected upgrades preserve revision"),
        Management->GetSnapshot().Revision, RevisionBeforeRejectedUpgrade);

    const FLBFactoryManagementSnapshot& Snapshot = Management->GetSnapshot();
    TestEqual(TEXT("Snapshot separates capital expenditure"), Snapshot.CapitalSpendPence, int64(200000));
    TestEqual(TEXT("Snapshot separates operating expenditure"), Snapshot.OperatingSpendPence, int64(50000));
    TestEqual(TEXT("Snapshot separates upgrade expenditure"), Snapshot.UpgradeSpendPence, int64(400000));
    TestEqual(TEXT("Snapshot reports order revenue"), Snapshot.OrderRevenuePence, int64(125000));
    TestEqual(TEXT("Only committed financial events notify ledger consumers"), LedgerNotifications, 5);
    TestEqual(TEXT("Last successful mutation retains its exact cause ID"), LastCause, FName(TEXT("TX-UPG-002")));
    TestTrue(TEXT("Every successful mutation emits a coherent snapshot"), ChangeNotifications >= 8);

    FString SaveReason;
    TestTrue(TEXT("Fresh authority state passes strict self-validation"),
        ULBFactoryManagementSubsystem::ValidateSaveState(Management->CaptureSaveState(), SaveReason));
    TestTrue(TEXT("Valid state has no rejection reason"), SaveReason.IsEmpty());
    DestroyManagementWorld(World);
    return true;
}

IMPLEMENT_SIMPLE_AUTOMATION_TEST(FLBManagementQualityMaintenanceAnalyticsTest,
    "LineBoss.Management.Authority.QualityMaintenanceAndOEE",
    EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)

bool FLBManagementQualityMaintenanceAnalyticsTest::RunTest(const FString& Parameters)
{
    UWorld* World = nullptr;
    ULBFactoryManagementSubsystem* Management = NewManagementAuthority(
        World, TEXT("LB_ManagementQualityMaintenance"));
    TestNotNull(TEXT("Management authority exists for operational evidence"), Management);
    if (!Management) { DestroyManagementWorld(World); return false; }
    TestTrue(TEXT("Operational fixture starts with exact funds"),
        Management->InitialiseNewCampaign(100000, 0));

    TestTrue(TEXT("Quality event records produced, inspected and disposition counts"),
        Management->RecordQualityCounts(TEXT("QLT-001"), TEXT("WELD-LINE-01"),
            100, 100, 90, 10, 6, 4));
    FLBManagementQualityRecord Quality;
    TestTrue(TEXT("Per-asset quality record is queryable"),
        Management->GetQualityRecord(TEXT("WELD-LINE-01"), Quality));
    TestEqual(TEXT("Quality record preserves passed units"), Quality.PassedCount, int64(90));
    TestEqual(TEXT("Quality record preserves rejects"), Quality.RejectedCount, int64(10));
    TestEqual(TEXT("Quality record distinguishes rework"), Quality.ReworkedCount, int64(6));
    TestEqual(TEXT("Quality record distinguishes scrap"), Quality.ScrappedCount, int64(4));
    const int64 RevisionBeforeInvalidQuality = Management->GetSnapshot().Revision;
    TestFalse(TEXT("Pass count cannot exceed inspected count"),
        Management->RecordQualityCounts(TEXT("QLT-INVALID"), TEXT("WELD-LINE-01"),
            0, 0, 1, 0, 0, 0));
    TestFalse(TEXT("Rejected quality event is not consumed"),
        Management->IsEventApplied(TEXT("QLT-INVALID")));
    TestEqual(TEXT("Invalid quality event leaves revision untouched"),
        Management->GetSnapshot().Revision, RevisionBeforeInvalidQuality);

    TestTrue(TEXT("Machine enters deterministic maintenance register"),
        Management->RegisterMaintainableAsset(TEXT("MNT-REG-001"), TEXT("WELD-LINE-01"), 1.0));
    TestTrue(TEXT("Runtime, downtime and wear are supplied by exact gameplay evidence"),
        Management->RecordMaintenanceUsage(TEXT("MNT-USE-001"), TEXT("WELD-LINE-01"),
            3600.0, 120.0, 1.0));
    FLBManagementMaintenanceRecord Maintenance;
    TestTrue(TEXT("Maintenance record is queryable"),
        Management->GetMaintenanceRecord(TEXT("WELD-LINE-01"), Maintenance));
    TestTrue(TEXT("Wear/service interval makes service due deterministically"),
        Maintenance.IsServiceDue());
    TestFalse(TEXT("Wear never invents a random machine fault"), Maintenance.bFaulted);
    TestTrue(TEXT("Player can schedule planned maintenance"),
        Management->SetMaintenancePlanned(TEXT("MNT-PLAN-001"), TEXT("WELD-LINE-01"), true));
    TestTrue(TEXT("A real machine integration can report an exact fault"),
        Management->SetAssetFault(TEXT("MNT-FAULT-001"), TEXT("WELD-LINE-01"),
            TEXT("WELD-TIP-OVERHEAT")));
    TestTrue(TEXT("Planned or corrective service commits atomically with its cost"),
        Management->TryCompleteMaintenanceService(TEXT("TX-MNT-001"),
            TEXT("WELD-LINE-01"), 10000));
    TestTrue(TEXT("Serviced maintenance state remains queryable"),
        Management->GetMaintenanceRecord(TEXT("WELD-LINE-01"), Maintenance));
    TestFalse(TEXT("Completed service clears explicit fault"), Maintenance.bFaulted);
    TestFalse(TEXT("Completed service clears planned work"), Maintenance.bPlannedService);
    TestTrue(TEXT("Completed service resets wear"), FMath::IsNearlyZero(Maintenance.WearFraction));
    TestEqual(TEXT("Completed service increments exact count"), Maintenance.CompletedServiceCount, 1);
    TestEqual(TEXT("Service cost leaves exact cash balance"),
        Management->GetCashBalancePence(), int64(90000));

    FLBManagementTimeBucketSample Sample;
    Sample.BucketStartSimulationSeconds = 0.0;
    Sample.BucketDurationSeconds = 60.0;
    Sample.PlannedProductionSeconds = 60.0;
    Sample.RunningSeconds = 45.0;
    Sample.StarvedSeconds = 5.0;
    Sample.BlockedSeconds = 4.0;
    Sample.FaultDowntimeSeconds = 6.0;
    Sample.IdealUnitCapacity = 10.0;
    Sample.ProducedCount = 9;
    Sample.GoodCount = 8;
    TestTrue(TEXT("Exact minute bucket enters analytics authority"),
        Management->RecordTimeBucket(TEXT("KPI-EVENT-001"), TEXT("MINUTE-0001"),
            TEXT("WELD-LINE-01"), Sample));
    const FLBFactoryManagementSnapshot& Snapshot = Management->GetSnapshot();
    TestEqual(TEXT("One exact asset bucket is exposed"), Snapshot.AnalyticsBuckets.Num(), 1);
    if (Snapshot.AnalyticsBuckets.Num() == 1)
    {
        const FLBManagementKPIValues& KPI = Snapshot.AnalyticsBuckets[0].KPIs;
        TestTrue(TEXT("Throughput is good units per hour"),
            FMath::IsNearlyEqual(KPI.ThroughputGoodUnitsPerHour, 480.0, 0.001));
        TestTrue(TEXT("Starvation ratio is time-backed"),
            FMath::IsNearlyEqual(KPI.StarvationRatio, 5.0 / 60.0, 0.0001));
        TestTrue(TEXT("Blocking ratio is time-backed"),
            FMath::IsNearlyEqual(KPI.BlockingRatio, 4.0 / 60.0, 0.0001));
        TestTrue(TEXT("Fault downtime ratio is time-backed"),
            FMath::IsNearlyEqual(KPI.FaultDowntimeRatio, 6.0 / 60.0, 0.0001));
        TestTrue(TEXT("Utilisation uses bucket duration"),
            FMath::IsNearlyEqual(KPI.UtilisationRatio, 0.75, 0.0001));
        TestTrue(TEXT("OEE availability uses planned time"),
            FMath::IsNearlyEqual(KPI.AvailabilityRatio, 0.75, 0.0001));
        TestTrue(TEXT("OEE performance uses ideal capacity"),
            FMath::IsNearlyEqual(KPI.PerformanceRatio, 0.9, 0.0001));
        TestTrue(TEXT("OEE quality uses good versus produced"),
            FMath::IsNearlyEqual(KPI.QualityRatio, 8.0 / 9.0, 0.0001));
        TestTrue(TEXT("OEE multiplies availability, performance and quality"),
            FMath::IsNearlyEqual(KPI.OEE, 0.6, 0.0001));
    }
    TestFalse(TEXT("Duplicate analytics event cannot double count"),
        Management->RecordTimeBucket(TEXT("KPI-EVENT-001"), TEXT("MINUTE-0001"),
            TEXT("WELD-LINE-01"), Sample));
    TestFalse(TEXT("A different event cannot overwrite the same asset bucket"),
        Management->RecordTimeBucket(TEXT("KPI-EVENT-002"), TEXT("MINUTE-0001"),
            TEXT("WELD-LINE-01"), Sample));
    TestFalse(TEXT("Rejected overwrite event remains available to its caller"),
        Management->IsEventApplied(TEXT("KPI-EVENT-002")));
    Sample.BlockedSeconds = 20.0;
    TestFalse(TEXT("Overlapping state durations cannot exceed planned time"),
        Management->RecordTimeBucket(TEXT("KPI-EVENT-INVALID"), TEXT("MINUTE-0002"),
            TEXT("WELD-LINE-01"), Sample));

    FString SaveReason;
    TestTrue(TEXT("Combined quality, maintenance and analytics state self-validates"),
        ULBFactoryManagementSubsystem::ValidateSaveState(
            Management->CaptureSaveState(), SaveReason));

    DestroyManagementWorld(World);
    return true;
}

IMPLEMENT_SIMPLE_AUTOMATION_TEST(FLBManagementSaveValidationMigrationTest,
    "LineBoss.Management.Authority.VersionedSaveValidationAndMigration",
    EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)

bool FLBManagementSaveValidationMigrationTest::RunTest(const FString& Parameters)
{
    UWorld* World = nullptr;
    ULBFactoryManagementSubsystem* Source = NewManagementAuthority(
        World, TEXT("LB_ManagementSave"));
    TestNotNull(TEXT("Save source authority exists"), Source);
    if (!Source) { DestroyManagementWorld(World); return false; }
    TestTrue(TEXT("Save source initialises"), Source->InitialiseNewCampaign(500000, 25));
    TestTrue(TEXT("Save source purchases exact asset"),
        Source->TryPurchaseCapitalAsset(TEXT("TX-CAP-SAVE"), TEXT("AGV-01"), 100000));
    TestTrue(TEXT("Save source earns research"),
        Source->GrantResearchPoints(TEXT("RP-SAVE"), TEXT("MILESTONE-01"), 10));
    TestTrue(TEXT("Save source records quality"),
        Source->RecordQualityCounts(TEXT("QLT-SAVE"), TEXT("PRESS-01"), 10, 8, 7, 1, 1, 0));
    const FLBFactoryManagementSaveState Saved = Source->CaptureSaveState();
    TestEqual(TEXT("Captured management state uses current version"), Saved.Version, 2);

    ULBFactoryManagementSubsystem* Restored = NewObject<ULBFactoryManagementSubsystem>(World);
    TestTrue(TEXT("Validated current management state restores"),
        Restored && Restored->RestoreSaveState(Saved));
    TestEqual(TEXT("Cash survives management restore"),
        Restored ? Restored->GetCashBalancePence() : int64(0), int64(400000));
    TestEqual(TEXT("Research survives management restore"),
        Restored ? Restored->GetAvailableResearchPoints() : int64(0), int64(35));
    TestTrue(TEXT("Event idempotency survives restore"),
        Restored && Restored->IsEventApplied(TEXT("TX-CAP-SAVE")));

    FLBFactoryManagementSaveState TamperedCash = Saved;
    ++TamperedCash.CashBalancePence;
    const int64 RestoredRevision = Restored ? Restored->GetSnapshot().Revision : 0;
    TestFalse(TEXT("Cash that does not reconcile with ledger is rejected"),
        Restored && Restored->RestoreSaveState(TamperedCash));
    TestEqual(TEXT("Rejected restore leaves live cash unchanged"),
        Restored ? Restored->GetCashBalancePence() : int64(0), int64(400000));
    TestEqual(TEXT("Rejected restore leaves live revision unchanged"),
        Restored ? Restored->GetSnapshot().Revision : int64(0), RestoredRevision);

    FLBFactoryManagementSaveState DuplicateEvent = Saved;
    DuplicateEvent.AppliedEventIds.Add(TEXT("TX-CAP-SAVE"));
    FString Reason;
    TestFalse(TEXT("Duplicate persisted event IDs are rejected"),
        ULBFactoryManagementSubsystem::ValidateSaveState(DuplicateEvent, Reason));
    TestTrue(TEXT("Duplicate rejection is actionable"), Reason.Contains(TEXT("DUPLICATE")));

    FLBFactoryManagementSaveState Legacy;
    Legacy.Version = 1;
    Legacy.CashBalancePence = 7654321;
    Legacy.AvailableResearchPoints = 77;
    Legacy.Revision = 4;
    ULBFactoryManagementSubsystem* Migrated = NewObject<ULBFactoryManagementSubsystem>(World);
    TestTrue(TEXT("Cash/research-only version one state migrates safely"),
        Migrated && Migrated->RestoreSaveState(Legacy));
    const FLBFactoryManagementSaveState MigratedState = Migrated
        ? Migrated->CaptureSaveState() : FLBFactoryManagementSaveState();
    TestEqual(TEXT("Legacy state upgrades to version two"), MigratedState.Version, 2);
    TestEqual(TEXT("Legacy cash becomes reconciled opening cash"),
        MigratedState.OpeningCashPence, int64(7654321));
    TestEqual(TEXT("Legacy current cash is preserved"),
        MigratedState.CashBalancePence, int64(7654321));
    TestEqual(TEXT("Legacy research becomes reconciled opening research"),
        MigratedState.OpeningResearchPoints, int64(77));
    TestTrue(TEXT("New management collections default empty for legacy campaigns"),
        MigratedState.LedgerEntries.IsEmpty() && MigratedState.MachineUpgrades.IsEmpty()
        && MigratedState.MaintenanceRecords.IsEmpty() && MigratedState.AnalyticsBuckets.IsEmpty());

    FLBFactoryManagementSaveState Unsupported = Saved;
    Unsupported.Version = 99;
    TestFalse(TEXT("Unknown future management save version is rejected"),
        Migrated && Migrated->RestoreSaveState(Unsupported));
    TestEqual(TEXT("Unknown-version rejection preserves migrated balance"),
        Migrated ? Migrated->GetCashBalancePence() : int64(0), int64(7654321));

    DestroyManagementWorld(World);
    return true;
}

#endif
