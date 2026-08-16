#pragma once

#include "CoreMinimal.h"
#include "Subsystems/WorldSubsystem.h"
#include "LBFactoryUIStateSubsystem.generated.h"

class AActor;

enum class ELBFactoryUIAlertSeverity : uint8
{
    Information,
    Warning,
    Critical
};

struct FLBFactoryUIOrderSnapshot
{
    bool bHasActiveOrder = false;
    FName OrderId = NAME_None;
    FName VehicleModelId = NAME_None;
    FName PanelTypeId = NAME_None;
    int32 IssuedQuantity = 0;
    int32 RequestedQuantity = 0;
    FString Objective = TEXT("BUILD THE FIRST PROCESS CELL");
};

struct FLBFactoryUIAlertSnapshot
{
    ELBFactoryUIAlertSeverity Severity = ELBFactoryUIAlertSeverity::Information;
    FName EntityId = NAME_None;
    FString Title;
    FString Detail;
    FVector MarkerWorldLocation = FVector::ZeroVector;
    TWeakObjectPtr<AActor> TargetActor;
    int32 ProcessOrder = MAX_int32;
};

struct FLBFactoryUIInspectorSnapshot
{
    bool bValid = false;
    FName EntityId = NAME_None;
    FString Kind;
    FString DisplayName;
    FString State;
    FString Reason;
    TArray<FString> DetailLines;
    FVector WorldLocation = FVector::ZeroVector;
    bool bHasMaintenance = false;
    bool bServiceDue = false;
    bool bServicePlanned = false;
    bool bManagementFaulted = false;
    FName FaultCode = NAME_None;
    double WearFraction = 0.0;
    bool bHasQuality = false;
    int64 ProducedCount = 0;
    int64 PassedCount = 0;
    int64 RejectedCount = 0;
    int64 ReworkedCount = 0;
    int64 ScrappedCount = 0;
    int32 UpgradeCount = 0;
    TArray<FString> UpgradeLines;
};

/** One stable, read-only management row shared by Assets and Maintenance. */
struct FLBFactoryUIManagementAssetSnapshot
{
    FName AssetId = NAME_None;
    bool bHasMaintenance = false;
    bool bServiceDue = false;
    bool bServicePlanned = false;
    bool bFaulted = false;
    FName FaultCode = NAME_None;
    double WearFraction = 0.0;
    bool bHasQuality = false;
    int64 ProducedCount = 0;
    int64 PassedCount = 0;
    int64 RejectedCount = 0;
    int64 ReworkedCount = 0;
    int64 ScrappedCount = 0;
    int32 UpgradeCount = 0;
};

/** Presentation-safe projection of the deterministic management authority. */
struct FLBFactoryUIManagementSnapshot
{
    bool bCampaignInitialised = false;
    int64 Revision = 0;
    int64 CashBalancePence = 0;
    int64 AvailableResearchPoints = 0;
    int64 TotalResearchEarnedPoints = 0;
    int64 TotalResearchSpentPoints = 0;
    int64 CapitalSpendPence = 0;
    int64 OperatingSpendPence = 0;
    int64 MaintenanceSpendPence = 0;
    int64 UpgradeSpendPence = 0;
    int64 OrderRevenuePence = 0;
    int32 CapitalAssetCount = 0;
    int32 UpgradeCount = 0;
    int32 TrackedMaintenanceAssetCount = 0;
    int32 ServiceDueCount = 0;
    int32 PlannedServiceCount = 0;
    int32 ManagementFaultCount = 0;
    int32 AnalyticsBucketCount = 0;
    int64 ProducedCount = 0;
    int64 InspectedCount = 0;
    int64 PassedCount = 0;
    int64 RejectedCount = 0;
    int64 ReworkedCount = 0;
    int64 ScrappedCount = 0;
    double ThroughputGoodUnitsPerHour = 0.0;
    double StarvationRatio = 0.0;
    double BlockingRatio = 0.0;
    double FaultDowntimeRatio = 0.0;
    double UtilisationRatio = 0.0;
    double AvailabilityRatio = 0.0;
    double PerformanceRatio = 0.0;
    double QualityRatio = 0.0;
    double OEE = 0.0;
    TArray<FName> ResearchUnlockIds;
    TArray<FLBFactoryUIManagementAssetSnapshot> Assets;
};

/** Truthful read-only projection of one composite Body Weld / BIW line. */
struct FLBFactoryUIBodyWeldLineSnapshot
{
    FName LineId = NAME_None;
    FString State;
    FString Phase;
    FString Reason;
    float PhaseProgress01 = 0.0f;
    FName AssignedOrderId = NAME_None;
    int32 AvailablePanelCount = 0;
    int32 ReservedPanelCount = 0;
    int32 AvailableBaseKitCount = 0;
    int32 PendingEmptyReturnCount = 0;
    FName OutputBodyId = NAME_None;
    FName ReworkBodyId = NAME_None;
    int32 CompletedBodyCount = 0;
    bool bEDAvailable = false;
    FVector WorldLocation = FVector::ZeroVector;
    TWeakObjectPtr<AActor> TargetActor;
};

/**
 * One truthful node in the modern production-flow canvas. The presentation
 * order is stable (coil, blanks, press, stillages, body weld, ED) while the
 * values remain projections of live gameplay authorities rather than a second
 * simulation owned by the HUD.
 */
struct FLBFactoryUIProductionStageSnapshot
{
    FName StageId = NAME_None;
    FString DisplayName;
    FString State = TEXT("NOT INSTALLED");
    FString Detail = TEXT("PLACE THIS PROCESS ASSET");
    int32 ProcessOrder = MAX_int32;
    bool bInstalled = false;
    bool bRunning = false;
    bool bWaiting = false;
    bool bFaulted = false;
    FVector WorldLocation = FVector::ZeroVector;
    TWeakObjectPtr<AActor> TargetActor;
};

struct FLBFactoryUIStateSnapshot
{
    FLBFactoryUIOrderSnapshot Order;
    float EffectiveSimulationRate = 1.0f;
    float TargetStrokesPerMinute = 0.0f;
    /** Machines, press trains, coil AGVs and support robots; storage is not an active asset. */
    int32 OperationalAssetCount = 0;
    int32 MachineCount = 0;
    int32 RunningCount = 0;
    int32 WaitingCount = 0;
    int32 FaultCount = 0;
    FLBFactoryUIManagementSnapshot Management;
    TArray<FLBFactoryUIProductionStageSnapshot> ProductionStages;
    TArray<FLBFactoryUIBodyWeldLineSnapshot> BodyWeldLines;
    TArray<FLBFactoryUIAlertSnapshot> Alerts;

    const FLBFactoryUIAlertSnapshot* GetTopAlert() const
    {
        return Alerts.IsEmpty() ? nullptr : &Alerts[0];
    }
};

/**
 * Read-only presentation authority for the persistent factory HUD, alert jump and inspectors.
 * Gameplay actors remain authoritative; this subsystem only aggregates their public state.
 */
UCLASS()
class LINEBOSSCARFACTORY_API ULBFactoryUIStateSubsystem : public UWorldSubsystem
{
    GENERATED_BODY()

public:
    const FLBFactoryUIStateSnapshot& GetSnapshot(bool bForceRefresh = false);
    void ForceRefresh();

    bool BuildInspectorSnapshot(const AActor* Actor, FLBFactoryUIInspectorSnapshot& OutSnapshot) const;
    AActor* FindFactoryActorById(FName EntityId) const;

private:
    void RefreshSnapshot();
    void AddAlert(ELBFactoryUIAlertSeverity Severity, FName EntityId,
        const FString& Title, const FString& Detail, AActor* TargetActor, int32 ProcessOrder);
    void AppendManagementInspectorData(FName EntityId,
        FLBFactoryUIInspectorSnapshot& InOutSnapshot) const;

    FLBFactoryUIStateSnapshot CachedSnapshot;
    double LastRefreshWorldSeconds = -1.0;
};
