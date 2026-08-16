#pragma once

#include "CoreMinimal.h"
#include "Subsystems/WorldSubsystem.h"
#include "LBFactoryManagementSubsystem.generated.h"

UENUM(BlueprintType)
enum class ELBManagementLedgerCategory : uint8
{
    CapitalPurchase,
    OperatingCost,
    OrderRevenue,
    MaintenanceService,
    MachineUpgrade
};

USTRUCT(BlueprintType)
struct FLBManagementLedgerEntry
{
    GENERATED_BODY()

    UPROPERTY(EditAnywhere, BlueprintReadWrite, SaveGame)
    int64 Sequence = 0;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, SaveGame)
    FName TransactionId = NAME_None;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, SaveGame)
    ELBManagementLedgerCategory Category = ELBManagementLedgerCategory::OperatingCost;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, SaveGame)
    FName SubjectId = NAME_None;

    /** Optional exact sub-item, used to distinguish several upgrade families on one machine. */
    UPROPERTY(EditAnywhere, BlueprintReadWrite, SaveGame)
    FName LineItemId = NAME_None;

    /** Positive for income, negative for expenditure. Money is always stored as integer pence. */
    UPROPERTY(EditAnywhere, BlueprintReadWrite, SaveGame)
    int64 SignedAmountPence = 0;
};

USTRUCT(BlueprintType)
struct FLBManagementResearchGrant
{
    GENERATED_BODY()

    UPROPERTY(EditAnywhere, BlueprintReadWrite, SaveGame)
    FName EventId = NAME_None;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, SaveGame)
    FName SourceId = NAME_None;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, SaveGame)
    int64 Points = 0;
};

USTRUCT(BlueprintType)
struct FLBManagementCapitalAsset
{
    GENERATED_BODY()

    UPROPERTY(EditAnywhere, BlueprintReadWrite, SaveGame)
    FName AssetId = NAME_None;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, SaveGame)
    FName PurchaseTransactionId = NAME_None;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, SaveGame)
    int64 PurchaseCostPence = 0;
};

USTRUCT(BlueprintType)
struct FLBManagementResearchUnlock
{
    GENERATED_BODY()

    UPROPERTY(EditAnywhere, BlueprintReadWrite, SaveGame)
    FName UnlockId = NAME_None;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, SaveGame)
    FName EventId = NAME_None;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, SaveGame)
    int64 ResearchPointCost = 0;
};

USTRUCT(BlueprintType)
struct FLBManagementMachineUpgrade
{
    GENERATED_BODY()

    UPROPERTY(EditAnywhere, BlueprintReadWrite, SaveGame)
    FName MachineId = NAME_None;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, SaveGame)
    FName UpgradeId = NAME_None;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, SaveGame)
    FName RequiredUnlockId = NAME_None;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, SaveGame)
    int32 Level = 0;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, SaveGame)
    int64 TotalInvestedPence = 0;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, SaveGame)
    FName LastTransactionId = NAME_None;
};

USTRUCT(BlueprintType)
struct FLBManagementQualityRecord
{
    GENERATED_BODY()

    UPROPERTY(EditAnywhere, BlueprintReadWrite, SaveGame)
    FName AssetId = NAME_None;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, SaveGame)
    int64 ProducedCount = 0;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, SaveGame)
    int64 InspectedCount = 0;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, SaveGame)
    int64 PassedCount = 0;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, SaveGame)
    int64 RejectedCount = 0;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, SaveGame)
    int64 ReworkedCount = 0;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, SaveGame)
    int64 ScrappedCount = 0;
};

USTRUCT(BlueprintType)
struct FLBManagementMaintenanceRecord
{
    GENERATED_BODY()

    UPROPERTY(EditAnywhere, BlueprintReadWrite, SaveGame)
    FName AssetId = NAME_None;

    /** Normalised deterministic wear. Reaching 1.0 makes service due but never creates a random fault. */
    UPROPERTY(EditAnywhere, BlueprintReadWrite, SaveGame)
    double WearFraction = 0.0;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, SaveGame)
    double OperatingSecondsSinceService = 0.0;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, SaveGame)
    double ServiceIntervalOperatingHours = 250.0;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, SaveGame)
    double CumulativeDowntimeSeconds = 0.0;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, SaveGame)
    bool bPlannedService = false;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, SaveGame)
    bool bFaulted = false;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, SaveGame)
    FName FaultCode = NAME_None;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, SaveGame)
    int32 CompletedServiceCount = 0;

    bool IsServiceDue() const
    {
        return WearFraction >= 1.0
            || OperatingSecondsSinceService >= ServiceIntervalOperatingHours * 3600.0;
    }
};

/** Raw mutually-exclusive time-state and output sample for one asset in one analytics bucket. */
USTRUCT(BlueprintType)
struct FLBManagementTimeBucketSample
{
    GENERATED_BODY()

    UPROPERTY(EditAnywhere, BlueprintReadWrite, SaveGame)
    double BucketStartSimulationSeconds = 0.0;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, SaveGame)
    double BucketDurationSeconds = 60.0;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, SaveGame)
    double PlannedProductionSeconds = 60.0;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, SaveGame)
    double RunningSeconds = 0.0;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, SaveGame)
    double StarvedSeconds = 0.0;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, SaveGame)
    double BlockedSeconds = 0.0;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, SaveGame)
    double FaultDowntimeSeconds = 0.0;

    /** Maximum output possible during RunningSeconds at the configured ideal cycle time. */
    UPROPERTY(EditAnywhere, BlueprintReadWrite, SaveGame)
    double IdealUnitCapacity = 0.0;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, SaveGame)
    int64 ProducedCount = 0;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, SaveGame)
    int64 GoodCount = 0;
};

USTRUCT(BlueprintType)
struct FLBManagementTimeBucketRecord
{
    GENERATED_BODY()

    UPROPERTY(EditAnywhere, BlueprintReadWrite, SaveGame)
    FName EventId = NAME_None;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, SaveGame)
    FName BucketId = NAME_None;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, SaveGame)
    FName AssetId = NAME_None;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, SaveGame)
    FLBManagementTimeBucketSample Sample;
};

USTRUCT(BlueprintType)
struct FLBManagementKPIValues
{
    GENERATED_BODY()

    UPROPERTY(VisibleAnywhere, BlueprintReadOnly)
    double ThroughputGoodUnitsPerHour = 0.0;

    UPROPERTY(VisibleAnywhere, BlueprintReadOnly)
    double StarvationRatio = 0.0;

    UPROPERTY(VisibleAnywhere, BlueprintReadOnly)
    double BlockingRatio = 0.0;

    UPROPERTY(VisibleAnywhere, BlueprintReadOnly)
    double FaultDowntimeRatio = 0.0;

    UPROPERTY(VisibleAnywhere, BlueprintReadOnly)
    double UtilisationRatio = 0.0;

    UPROPERTY(VisibleAnywhere, BlueprintReadOnly)
    double AvailabilityRatio = 0.0;

    UPROPERTY(VisibleAnywhere, BlueprintReadOnly)
    double PerformanceRatio = 0.0;

    UPROPERTY(VisibleAnywhere, BlueprintReadOnly)
    double QualityRatio = 0.0;

    UPROPERTY(VisibleAnywhere, BlueprintReadOnly)
    double OEE = 0.0;
};

USTRUCT(BlueprintType)
struct FLBManagementAnalyticsSnapshot
{
    GENERATED_BODY()

    UPROPERTY(VisibleAnywhere, BlueprintReadOnly)
    FName BucketId = NAME_None;

    UPROPERTY(VisibleAnywhere, BlueprintReadOnly)
    FName AssetId = NAME_None;

    UPROPERTY(VisibleAnywhere, BlueprintReadOnly)
    FLBManagementTimeBucketSample Raw;

    UPROPERTY(VisibleAnywhere, BlueprintReadOnly)
    FLBManagementKPIValues KPIs;
};

USTRUCT(BlueprintType)
struct FLBFactoryManagementSnapshot
{
    GENERATED_BODY()

    UPROPERTY(VisibleAnywhere, BlueprintReadOnly)
    int64 Revision = 0;

    UPROPERTY(VisibleAnywhere, BlueprintReadOnly)
    int64 CashBalancePence = 0;

    UPROPERTY(VisibleAnywhere, BlueprintReadOnly)
    int64 CapitalSpendPence = 0;

    UPROPERTY(VisibleAnywhere, BlueprintReadOnly)
    int64 OperatingSpendPence = 0;

    UPROPERTY(VisibleAnywhere, BlueprintReadOnly)
    int64 MaintenanceSpendPence = 0;

    UPROPERTY(VisibleAnywhere, BlueprintReadOnly)
    int64 UpgradeSpendPence = 0;

    UPROPERTY(VisibleAnywhere, BlueprintReadOnly)
    int64 OrderRevenuePence = 0;

    UPROPERTY(VisibleAnywhere, BlueprintReadOnly)
    TArray<FLBManagementLedgerEntry> LedgerEntries;

    UPROPERTY(VisibleAnywhere, BlueprintReadOnly)
    TArray<FLBManagementCapitalAsset> CapitalAssets;

    UPROPERTY(VisibleAnywhere, BlueprintReadOnly)
    int64 AvailableResearchPoints = 0;

    UPROPERTY(VisibleAnywhere, BlueprintReadOnly)
    int64 TotalResearchEarnedPoints = 0;

    UPROPERTY(VisibleAnywhere, BlueprintReadOnly)
    int64 TotalResearchSpentPoints = 0;

    UPROPERTY(VisibleAnywhere, BlueprintReadOnly)
    TArray<FName> ResearchUnlockIds;

    UPROPERTY(VisibleAnywhere, BlueprintReadOnly)
    TArray<FLBManagementMachineUpgrade> MachineUpgrades;

    UPROPERTY(VisibleAnywhere, BlueprintReadOnly)
    FLBManagementQualityRecord FactoryQualityTotals;

    UPROPERTY(VisibleAnywhere, BlueprintReadOnly)
    TArray<FLBManagementQualityRecord> QualityByAsset;

    UPROPERTY(VisibleAnywhere, BlueprintReadOnly)
    TArray<FLBManagementMaintenanceRecord> MaintenanceByAsset;

    UPROPERTY(VisibleAnywhere, BlueprintReadOnly)
    TArray<FLBManagementAnalyticsSnapshot> AnalyticsBuckets;

    UPROPERTY(VisibleAnywhere, BlueprintReadOnly)
    FLBManagementKPIValues LifetimeKPIs;
};

/** Self-contained authority state. Version one was a cash/research-only prototype. */
USTRUCT(BlueprintType)
struct FLBFactoryManagementSaveState
{
    GENERATED_BODY()

    UPROPERTY(EditAnywhere, BlueprintReadWrite, SaveGame)
    int32 Version = 2;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, SaveGame)
    bool bCampaignInitialised = false;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, SaveGame)
    int64 Revision = 0;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, SaveGame)
    int64 OpeningCashPence = 250000000;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, SaveGame)
    int64 CashBalancePence = 250000000;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, SaveGame)
    int64 OpeningResearchPoints = 0;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, SaveGame)
    int64 AvailableResearchPoints = 0;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, SaveGame)
    int64 TotalResearchEarnedPoints = 0;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, SaveGame)
    int64 TotalResearchSpentPoints = 0;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, SaveGame)
    int64 NextLedgerSequence = 1;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, SaveGame)
    TArray<FLBManagementLedgerEntry> LedgerEntries;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, SaveGame)
    TArray<FLBManagementCapitalAsset> CapitalAssets;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, SaveGame)
    TArray<FLBManagementResearchGrant> ResearchGrants;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, SaveGame)
    TArray<FLBManagementResearchUnlock> ResearchUnlocks;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, SaveGame)
    TArray<FLBManagementMachineUpgrade> MachineUpgrades;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, SaveGame)
    TArray<FLBManagementQualityRecord> QualityRecords;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, SaveGame)
    TArray<FLBManagementMaintenanceRecord> MaintenanceRecords;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, SaveGame)
    TArray<FLBManagementTimeBucketRecord> AnalyticsBuckets;

    /** Global idempotency namespace shared by financial and operational events. */
    UPROPERTY(EditAnywhere, BlueprintReadWrite, SaveGame)
    TArray<FName> AppliedEventIds;
};

DECLARE_MULTICAST_DELEGATE_TwoParams(FLBFactoryManagementChanged,
    const FLBFactoryManagementSnapshot&, FName);
DECLARE_MULTICAST_DELEGATE_OneParam(FLBFactoryFinancialTransactionCommitted,
    const FLBManagementLedgerEntry&);

/**
 * Persistent, deterministic management authority. It has no Tick and never invents
 * failures: gameplay systems submit exact, idempotent events at their integration seams.
 */
UCLASS()
class LINEBOSSCARFACTORY_API ULBFactoryManagementSubsystem : public UWorldSubsystem
{
    GENERATED_BODY()

public:
    static constexpr int32 CurrentSaveVersion = 2;
    static constexpr int64 DefaultStartingCashPence = 250000000;

    /** May run once before any event; all amounts use pence/whole research points. */
    UFUNCTION(BlueprintCallable, Category="Line Boss|Management|Campaign")
    bool InitialiseNewCampaign(int64 OpeningCashPence, int64 OpeningResearchPoints);

    UFUNCTION(BlueprintCallable, Category="Line Boss|Management|Finance")
    bool TryPurchaseCapitalAsset(FName TransactionId, FName AssetId, int64 CostPence);

    UFUNCTION(BlueprintCallable, Category="Line Boss|Management|Finance")
    bool TryChargeOperatingCost(FName TransactionId, FName CostCentreId, int64 CostPence);

    UFUNCTION(BlueprintCallable, Category="Line Boss|Management|Finance")
    bool TryRecordOrderRevenue(FName TransactionId, FName OrderId, int64 RevenuePence);

    UFUNCTION(BlueprintCallable, Category="Line Boss|Management|Research")
    bool GrantResearchPoints(FName EventId, FName SourceId, int64 Points);

    UFUNCTION(BlueprintCallable, Category="Line Boss|Management|Research")
    bool TryUnlockResearch(FName EventId, FName UnlockId, int64 PointCost);

    UFUNCTION(BlueprintCallable, Category="Line Boss|Management|Upgrades")
    bool TryPurchaseMachineUpgrade(FName TransactionId, FName MachineId,
        FName UpgradeId, int32 TargetLevel, int64 CostPence, FName RequiredUnlockId);

    UFUNCTION(BlueprintCallable, Category="Line Boss|Management|Quality")
    bool RecordQualityCounts(FName EventId, FName AssetId, int64 ProducedDelta,
        int64 InspectedDelta, int64 PassedDelta, int64 RejectedDelta,
        int64 ReworkedDelta, int64 ScrappedDelta);

    UFUNCTION(BlueprintCallable, Category="Line Boss|Management|Maintenance")
    bool RegisterMaintainableAsset(FName EventId, FName AssetId,
        double ServiceIntervalOperatingHours);

    UFUNCTION(BlueprintCallable, Category="Line Boss|Management|Maintenance")
    bool RecordMaintenanceUsage(FName EventId, FName AssetId,
        double OperatingSeconds, double FaultDowntimeSeconds, double WearIncrease);

    UFUNCTION(BlueprintCallable, Category="Line Boss|Management|Maintenance")
    bool SetMaintenancePlanned(FName EventId, FName AssetId, bool bPlanned);

    UFUNCTION(BlueprintCallable, Category="Line Boss|Management|Maintenance")
    bool SetAssetFault(FName EventId, FName AssetId, FName FaultCode);

    UFUNCTION(BlueprintCallable, Category="Line Boss|Management|Maintenance")
    bool ClearAssetFault(FName EventId, FName AssetId);

    UFUNCTION(BlueprintCallable, Category="Line Boss|Management|Maintenance")
    bool TryCompleteMaintenanceService(FName TransactionId, FName AssetId,
        int64 CostPence);

    UFUNCTION(BlueprintCallable, Category="Line Boss|Management|Analytics")
    bool RecordTimeBucket(FName EventId, FName BucketId, FName AssetId,
        const FLBManagementTimeBucketSample& Sample);

    UFUNCTION(BlueprintPure, Category="Line Boss|Management|Finance")
    int64 GetCashBalancePence() const { return State.CashBalancePence; }

    UFUNCTION(BlueprintPure, Category="Line Boss|Management|Research")
    int64 GetAvailableResearchPoints() const { return State.AvailableResearchPoints; }

    /** Cheap runtime guard; does not copy the potentially large save-state arrays. */
    UFUNCTION(BlueprintPure, Category="Line Boss|Management|Campaign")
    bool IsCampaignInitialised() const { return State.bCampaignInitialised; }

    UFUNCTION(BlueprintPure, Category="Line Boss|Management|Research")
    bool HasResearchUnlock(FName UnlockId) const;

    UFUNCTION(BlueprintPure, Category="Line Boss|Management|Upgrades")
    int32 GetMachineUpgradeLevel(FName MachineId, FName UpgradeId) const;

    UFUNCTION(BlueprintPure, Category="Line Boss|Management|Maintenance")
    bool GetMaintenanceRecord(FName AssetId, FLBManagementMaintenanceRecord& OutRecord) const;

    UFUNCTION(BlueprintPure, Category="Line Boss|Management|Quality")
    bool GetQualityRecord(FName AssetId, FLBManagementQualityRecord& OutRecord) const;

    bool IsEventApplied(FName EventId) const;
    const FLBFactoryManagementSnapshot& GetSnapshot() const;

    UFUNCTION(BlueprintPure, Category="Line Boss|Management")
    FLBFactoryManagementSnapshot GetManagementSnapshot() const { return GetSnapshot(); }

    UFUNCTION(BlueprintPure, Category="Line Boss|Management|Save")
    FLBFactoryManagementSaveState CaptureSaveState() const { return State; }

    UFUNCTION(BlueprintCallable, Category="Line Boss|Management|Save")
    bool RestoreSaveState(const FLBFactoryManagementSaveState& SavedState);

    static bool ValidateSaveState(const FLBFactoryManagementSaveState& SavedState,
        FString& OutReason);
    static bool IsStrictId(FName Id);

    FLBFactoryManagementChanged& OnManagementChanged() { return ManagementChanged; }
    FLBFactoryFinancialTransactionCommitted& OnFinancialTransactionCommitted()
    {
        return FinancialTransactionCommitted;
    }

private:
    UPROPERTY(Transient)
    FLBFactoryManagementSaveState State;

    TSet<FName> AppliedEventSet;
    mutable FLBFactoryManagementSnapshot CachedSnapshot;
    mutable bool bSnapshotDirty = true;
    FLBFactoryManagementChanged ManagementChanged;
    FLBFactoryFinancialTransactionCommitted FinancialTransactionCommitted;

    bool CanStartMutation(FName EventId) const;
    bool CanApplyMoneyDelta(int64 SignedDeltaPence) const;
    void AddAppliedEventNoBroadcast(FName EventId);
    FLBManagementLedgerEntry AddLedgerEntryNoBroadcast(FName TransactionId,
        ELBManagementLedgerCategory Category, FName SubjectId, int64 SignedAmountPence,
        FName LineItemId = NAME_None);
    void CommitMutation(FName CauseId, const FLBManagementLedgerEntry* LedgerEntry = nullptr);
    void RebuildRuntimeCaches();
    void RebuildSnapshot() const;
    static bool ValidateQualityRecord(const FLBManagementQualityRecord& Record);
    static bool ValidateMaintenanceRecord(const FLBManagementMaintenanceRecord& Record);
    static bool ValidateTimeBucketSample(const FLBManagementTimeBucketSample& Sample);
    static FLBManagementKPIValues CalculateKPIs(
        const TArray<FLBManagementTimeBucketRecord>& Records);
};
