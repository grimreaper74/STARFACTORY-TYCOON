#pragma once

#include "CoreMinimal.h"
#include "Subsystems/WorldSubsystem.h"
#include "LBFactoryManagementRuntimeSubsystem.generated.h"

class AActor;

/** Frozen evidence waiting for both maintenance and analytics commits. */
struct FLBFactoryManagementRuntimePendingBucket
{
    double BucketStartSimulationSeconds = 0.0;
    double ElapsedSeconds = 0.0;
    double RunningSeconds = 0.0;
    double StarvedSeconds = 0.0;
    double BlockedSeconds = 0.0;
    double FaultSeconds = 0.0;
    int64 ProducedCount = 0;
    int64 GoodCount = 0;
    FName MaintenanceEventId = NAME_None;
    FName AnalyticsEventId = NAME_None;
    FName BucketId = NAME_None;
    bool bMaintenanceRequired = false;
    bool bMaintenanceCommitted = false;
};

/**
 * Transient fixed-step evidence for one persistent factory asset. The management
 * authority owns every durable total; this cache only prevents a newly discovered
 * actor's existing lifetime counters being misreported as output from one minute.
 */
struct FLBFactoryManagementRuntimeAccumulator
{
    double ElapsedSeconds = 0.0;
    double RunningSeconds = 0.0;
    double StarvedSeconds = 0.0;
    double BlockedSeconds = 0.0;
    double FaultSeconds = 0.0;
    int64 ProducedInBucket = 0;
    int64 GoodInBucket = 0;
    int64 LastObservedProduced = 0;
    int64 LastObservedGood = 0;
    TWeakObjectPtr<AActor> LastObservedOutputActor;
    bool bOutputBaselineEstablished = false;

    int64 LastObservedQualityProduced = 0;
    int64 LastObservedQualityGood = 0;
    int64 LastObservedQualityRejected = 0;
    TWeakObjectPtr<AActor> LastObservedQualityActor;
    bool bQualityBaselineEstablished = false;

    FLBFactoryManagementRuntimePendingBucket PendingBucket;
    bool bHasPendingBucket = false;
};

/**
 * Read-only gameplay-to-management adapter.
 *
 * The subsystem discovers existing production authorities and submits their real,
 * public state to ULBFactoryManagementSubsystem. It never advances production,
 * changes a fault, or invents a random failure. Every durable write is idempotent:
 * durable quality targets identify counter events, while stable per-asset bucket
 * ordinals identify fixed-interval usage and analytics events across retries.
 */
UCLASS()
class LINEBOSSCARFACTORY_API ULBFactoryManagementRuntimeSubsystem
    : public UTickableWorldSubsystem
{
    GENERATED_BODY()

public:
    static constexpr double FixedSampleSeconds = 1.0;
    static constexpr double AnalyticsBucketSeconds = 10.0;
    static constexpr int64 DefaultPanelRevenuePence = 25000;
    static constexpr int64 DefaultFulfilmentResearchPoints = 5;

    virtual void Tick(float DeltaTime) override;
    virtual TStatId GetStatId() const override;

    /** Deterministic entry point shared by Tick and focused automation. */
    UFUNCTION(BlueprintCallable, Category="Line Boss|Management|Runtime")
    void AdvanceRuntimeBridge(float DeltaSeconds);

    UFUNCTION(BlueprintPure, Category="Line Boss|Management|Runtime")
    int32 GetTrackedAssetCount() const { return AssetAccumulators.Num(); }

protected:
    virtual bool DoesSupportWorldType(EWorldType::Type WorldType) const override;

private:
    double FixedStepAccumulatorSeconds = 0.0;
    TMap<FName, FLBFactoryManagementRuntimeAccumulator> AssetAccumulators;

    void SampleFixedInterval(double SampleSeconds);
};
