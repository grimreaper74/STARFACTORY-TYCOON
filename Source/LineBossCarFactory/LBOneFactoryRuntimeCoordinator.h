#pragma once

#include "CoreMinimal.h"
#include "GameFramework/Actor.h"
#include "LBOneFactoryAssemblyStarterLayout.h"
#include "LBOneFactoryBodyWeldStarterLayout.h"
#include "LBOneFactoryPaintStarterLayout.h"
#include "LBOneFactoryPressStarterLayout.h"
#include "LBOneFactoryProductionFlow.h"
#include "LBOneFactoryRuntimeCoordinator.generated.h"

/** One presentation-free physical step in the configured 57-station route. */
USTRUCT(BlueprintType)
struct LINEBOSSCARFACTORY_API FLBOneFactoryRuntimeStationStep
{
    GENERATED_BODY()

    UPROPERTY(BlueprintReadOnly, Category="Line Boss|OneFactory|Runtime")
    int32 RouteIndex = INDEX_NONE;

    UPROPERTY(BlueprintReadOnly, Category="Line Boss|OneFactory|Runtime")
    ELBOneFactoryDepartment Department = ELBOneFactoryDepartment::Press;

    UPROPERTY(BlueprintReadOnly, Category="Line Boss|OneFactory|Runtime")
    FName StationId = NAME_None;

    UPROPERTY(BlueprintReadOnly, Category="Line Boss|OneFactory|Runtime")
    FTransform WorldTransform = FTransform::Identity;

    /** Stable aggregate identity for every configured duty at this position. */
    UPROPERTY(BlueprintReadOnly, Category="Line Boss|OneFactory|Runtime")
    FName AssignmentId = NAME_None;

    /** Human/UI inspectable duties; an empty-capability station says PASS_THROUGH. */
    UPROPERTY(BlueprintReadOnly, Category="Line Boss|OneFactory|Runtime")
    TArray<FName> ConfiguredWorkIds;

    UPROPERTY(BlueprintReadOnly, Category="Line Boss|OneFactory|Runtime")
    float NominalCycleSeconds = 0.0f;

    UPROPERTY(BlueprintReadOnly, Category="Line Boss|OneFactory|Runtime")
    ELBOneFactoryVehicleStage SemanticStage =
        ELBOneFactoryVehicleStage::InboundCoil;

    UPROPERTY(BlueprintReadOnly, Category="Line Boss|OneFactory|Runtime")
    bool bQualityGate = false;
};

/** Native-UMG-safe status for one logical car; it contains no visual proxy. */
USTRUCT(BlueprintType)
struct LINEBOSSCARFACTORY_API FLBOneFactoryRuntimeVehicleStatus
{
    GENERATED_BODY()

    UPROPERTY(BlueprintReadOnly, Category="Line Boss|OneFactory|Runtime")
    FName UnitId = NAME_None;

    UPROPERTY(BlueprintReadOnly, Category="Line Boss|OneFactory|Runtime")
    FName CurrentStationId = NAME_None;

    UPROPERTY(BlueprintReadOnly, Category="Line Boss|OneFactory|Runtime")
    FName CurrentAssignmentId = NAME_None;

    UPROPERTY(BlueprintReadOnly, Category="Line Boss|OneFactory|Runtime")
    ELBOneFactoryDepartment Department = ELBOneFactoryDepartment::Press;

    UPROPERTY(BlueprintReadOnly, Category="Line Boss|OneFactory|Runtime")
    ELBOneFactoryVehicleStage Stage = ELBOneFactoryVehicleStage::InboundCoil;

    UPROPERTY(BlueprintReadOnly, Category="Line Boss|OneFactory|Runtime")
    ELBOneFactoryVehicleQualityState QualityState =
        ELBOneFactoryVehicleQualityState::NotInspected;

    UPROPERTY(BlueprintReadOnly, Category="Line Boss|OneFactory|Runtime")
    int32 StationCursor = INDEX_NONE;

    UPROPERTY(BlueprintReadOnly, Category="Line Boss|OneFactory|Runtime")
    int32 CompletedStationCount = 0;

    UPROPERTY(BlueprintReadOnly, Category="Line Boss|OneFactory|Runtime")
    int32 TotalStationCount = 0;

    UPROPERTY(BlueprintReadOnly, Category="Line Boss|OneFactory|Runtime")
    float CycleElapsedSeconds = 0.0f;

    UPROPERTY(BlueprintReadOnly, Category="Line Boss|OneFactory|Runtime")
    float CycleDurationSeconds = 0.0f;

    UPROPERTY(BlueprintReadOnly, Category="Line Boss|OneFactory|Runtime")
    float NormalizedCycleProgress = 0.0f;

    UPROPERTY(BlueprintReadOnly, Category="Line Boss|OneFactory|Runtime")
    bool bStarted = false;

    UPROPERTY(BlueprintReadOnly, Category="Line Boss|OneFactory|Runtime")
    bool bAtQualityGate = false;

    UPROPERTY(BlueprintReadOnly, Category="Line Boss|OneFactory|Runtime")
    bool bAwaitingQualityResult = false;

    UPROPERTY(BlueprintReadOnly, Category="Line Boss|OneFactory|Runtime")
    bool bCompleted = false;

    UPROPERTY(BlueprintReadOnly, Category="Line Boss|OneFactory|Runtime")
    bool bDispatched = false;
};

/**
 * Exact-one runtime coordinator for the unified factory.
 *
 * It advances logical UnitIds through the configured physical station chain,
 * owns no mesh or WIP actor, and commits station reservations plus genealogy as
 * one rollback-capable transaction.  Actor Tick is only a time source; all
 * durable progress lives in FLBOneFactoryProductionLedgerState.
 */
UCLASS(BlueprintType)
class LINEBOSSCARFACTORY_API ALBOneFactoryRuntimeCoordinator : public AActor
{
    GENERATED_BODY()

public:
    ALBOneFactoryRuntimeCoordinator();

    virtual void Tick(float DeltaSeconds) override;

    /** When enabled, every explicitly started UnitId receives deterministic time. */
    UPROPERTY(EditAnywhere, BlueprintReadWrite,
        Category="Line Boss|OneFactory|Runtime")
    bool bAdvanceStartedVehiclesOnActorTick = true;

    /**
     * Player-selected simulation multiplier. Pause remains durable ledger state;
     * this value only scales the coordinator's deterministic actor-tick source.
     */
    UPROPERTY(VisibleInstanceOnly, BlueprintReadOnly,
        Category="Line Boss|OneFactory|Runtime")
    float RuntimeTimeScale = 1.0f;

    UFUNCTION(BlueprintCallable, Category="Line Boss|OneFactory|Runtime")
    bool SetRuntimeTimeScale(float InTimeScale, FString& OutReason);

    /**
     * Posts dispatch revenue and completed-hour operating cost into the
     * management economy. Every transaction id is deterministic (unit id or
     * hour index), and the management ledger is idempotent by id, so replays
     * after a load are safe no-ops.
     */
    UFUNCTION(BlueprintCallable, Category="Line Boss|OneFactory|Runtime")
    bool ReconcileEconomy(FString& OutReason);

    /** Highest operating-cost hour already charged this session (transient). */
    int64 LastChargedOpexHour = -1;

    UFUNCTION(BlueprintPure, Category="Line Boss|OneFactory|Runtime")
    float GetRuntimeTimeScale() const { return RuntimeTimeScale; }

    UFUNCTION(BlueprintCallable, Category="Line Boss|OneFactory|Runtime")
    bool GetConfiguredStationRoute(
        TArray<FLBOneFactoryRuntimeStationStep>& OutRoute,
        FName& OutTopologyId, FString& OutReason) const;

    /** Structural, topology and exact-one-reservation audit; no mutation. */
    UFUNCTION(BlueprintCallable, Category="Line Boss|OneFactory|Runtime")
    bool ValidateRuntimeFactory(FString& OutReason) const;

    /** Creates one genealogy record and reserves the configured Press inbound. */
    UFUNCTION(BlueprintCallable, Category="Line Boss|OneFactory|Runtime")
    bool CreateRuntimeVehicleOrder(FName BuildOrderId, FName VehicleModelId,
        FName PaintProgrammeId, FName PaintColourId, FName SourceCoilLotId,
        FName& OutUnitId, FString& OutReason);

    /** Explicit release from inbound reservation into deterministic processing. */
    UFUNCTION(BlueprintCallable, Category="Line Boss|OneFactory|Runtime")
    bool StartVehicle(FName UnitId, FString& OutReason);

    /** Advances exactly one UnitId by DeltaSeconds, or holds it at a runtime gate. */
    UFUNCTION(BlueprintCallable, Category="Line Boss|OneFactory|Runtime")
    bool TickVehicle(FName UnitId, float DeltaSeconds, FString& OutReason);

    /** Native game-loop/UMG seam for all started units, ordered by UnitId. */
    UFUNCTION(BlueprintCallable, Category="Line Boss|OneFactory|Runtime")
    bool TickAutomaticFlow(float DeltaSeconds, int32& OutProcessedUnitCount,
        FString& OutReason);

    UFUNCTION(BlueprintCallable,
        Category="Line Boss|OneFactory|Runtime|Quality")
    bool SubmitRuntimeQualityResult(FName UnitId,
        ELBOneFactoryVehicleQualityState QualityState, FName EvidenceId,
        FString& OutReason);

    /** Repeats the current inspection cycle without changing UnitId or station. */
    UFUNCTION(BlueprintCallable,
        Category="Line Boss|OneFactory|Runtime|Quality")
    bool CompleteRuntimeRework(FName UnitId, FName EvidenceId,
        FString& OutReason);

    UFUNCTION(BlueprintCallable, Category="Line Boss|OneFactory|Runtime")
    bool GetVehicleRuntimeStatus(FName UnitId,
        FLBOneFactoryRuntimeVehicleStatus& OutStatus,
        FString& OutReason) const;

    static FName GetCoordinatorTag();
    static constexpr int32 RequiredPhysicalStationCount = 57;
};
