#pragma once

#include "CoreMinimal.h"
#include "GameFramework/Actor.h"
#include "Kismet/BlueprintFunctionLibrary.h"
#include "LBOneFactoryTypes.h"
#include "LBOneFactoryProductionFlow.generated.h"

/** One logical vehicle identity from allocated coil through customer dispatch. */
UENUM(BlueprintType)
enum class ELBOneFactoryVehicleStage : uint8
{
    InboundCoil,
    BlankPreparation,
    Pressing,
    PressedPanelStillage,
    BodyFraming,
    BodyInWhite,
    BodyQualityInspection,
    Pretreatment,
    EDCoat,
    ColourCoat,
    Cure,
    PaintQualityInspection,
    GeneralAssemblyTrim,
    PowertrainMarriage,
    RollingChassis,
    EndOfLineInspection,
    FinishedVehicle,
    Dispatched
};

/** Current decision at the active quality gate. Prior evidence remains in the ledger. */
UENUM(BlueprintType)
enum class ELBOneFactoryVehicleQualityState : uint8
{
    NotInspected,
    Pending,
    Passed,
    ReworkRequired,
    Rejected,
    Scrapped
};

/** Commission state is persisted with the production ledger, never inferred on load. */
USTRUCT(BlueprintType)
struct LINEBOSSCARFACTORY_API FLBOneFactoryDepartmentCommissioningState
{
    GENERATED_BODY()

    UPROPERTY(EditAnywhere, BlueprintReadWrite, SaveGame)
    bool bPressCommissioned = false;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, SaveGame)
    bool bBodyCommissioned = false;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, SaveGame)
    bool bPaintCommissioned = false;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, SaveGame)
    bool bAssemblyCommissioned = false;
};

/** One exact, presentation-free vehicle genealogy and WIP record. */
USTRUCT(BlueprintType)
struct LINEBOSSCARFACTORY_API FLBOneFactoryVehicleUnitState
{
    GENERATED_BODY()

    UPROPERTY(EditAnywhere, BlueprintReadWrite, SaveGame)
    int32 Version = 1;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, SaveGame)
    FName UnitId = NAME_None;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, SaveGame)
    FName BuildOrderId = NAME_None;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, SaveGame)
    FName VehicleModelId = NAME_None;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, SaveGame)
    FName PaintProgrammeId = NAME_None;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, SaveGame)
    FName PaintColourId = NAME_None;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, SaveGame)
    ELBOneFactoryVehicleStage Stage = ELBOneFactoryVehicleStage::InboundCoil;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, SaveGame)
    ELBOneFactoryDepartment Department = ELBOneFactoryDepartment::Press;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, SaveGame)
    FName CurrentStationId = NAME_None;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, SaveGame)
    ELBOneFactoryVehicleQualityState QualityState =
        ELBOneFactoryVehicleQualityState::NotInspected;

    /** Raw-material lots and pressed-panel batches allocated to this exact vehicle. */
    UPROPERTY(EditAnywhere, BlueprintReadWrite, SaveGame)
    TArray<FName> SourceMaterialUnitIds;

    /** Immutable process, transfer and inspection evidence in chronological order. */
    UPROPERTY(EditAnywhere, BlueprintReadWrite, SaveGame)
    TArray<FName> EvidenceIds;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, SaveGame)
    int32 StageRevision = 0;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, SaveGame)
    bool bCompleted = false;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, SaveGame)
    bool bDispatched = false;

    /**
     * Presentation-free automatic-line cursor.  A value of -1 identifies a
     * legacy/manual genealogy record which has not joined the 57-position
     * OneFactory runtime route.  Values 0..56 identify an occupied station and
     * 57 identifies a successfully dispatched route.
     */
    UPROPERTY(EditAnywhere, BlueprintReadWrite, SaveGame)
    int32 RuntimeStationCursor = -1;

    /** Number of physical stations completed by this exact UnitId. */
    UPROPERTY(EditAnywhere, BlueprintReadWrite, SaveGame)
    int32 RuntimeCompletedStationCount = 0;

    /** Frozen route cardinality for the first unified factory. */
    UPROPERTY(EditAnywhere, BlueprintReadWrite, SaveGame)
    int32 RuntimeTotalStationCount = 0;

    /** Deterministic elapsed time at CurrentStationId; never wall-clock time. */
    UPROPERTY(EditAnywhere, BlueprintReadWrite, SaveGame)
    float RuntimeCycleElapsedSeconds = 0.0f;

    /** Persisted station duration protects save/load from cycle-time drift. */
    UPROPERTY(EditAnywhere, BlueprintReadWrite, SaveGame)
    float RuntimeCycleDurationSeconds = 0.0f;

    /** Hash of station order, assignments, programmes and nominal cycles. */
    UPROPERTY(EditAnywhere, BlueprintReadWrite, SaveGame)
    FName RuntimeTopologyId = NAME_None;

    /** Exact configured work assignment at the occupied physical position. */
    UPROPERTY(EditAnywhere, BlueprintReadWrite, SaveGame)
    FName RuntimeCurrentAssignmentId = NAME_None;

    /** Start/stop is explicit so a newly reserved inbound unit is saveable. */
    UPROPERTY(EditAnywhere, BlueprintReadWrite, SaveGame)
    bool bRuntimeStarted = false;

    /** Ledger sim-clock when the order was created; never wall-clock time. */
    UPROPERTY(EditAnywhere, BlueprintReadWrite, SaveGame)
    double CreatedAtSimSeconds = 0.0;

    /** Ledger sim-clock at dispatch; negative until the unit dispatches. */
    UPROPERTY(EditAnywhere, BlueprintReadWrite, SaveGame)
    double DispatchedAtSimSeconds = -1.0;

    /** Contract this dispatched unit settled against, if any. */
    UPROPERTY(EditAnywhere, BlueprintReadWrite, SaveGame)
    FName FulfilledContractId = NAME_None;
};

UENUM(BlueprintType)
enum class ELBOneFactoryContractState : uint8
{
    Open,
    Complete,
    Expired
};

UENUM(BlueprintType)
enum class ELBOneFactoryFinancialState : uint8
{
    Healthy,
    Warning,
    Emergency
};

/**
 * One customer order for vehicles: the pacing backbone of the v1 loop.
 * Soft failure by design - an expired contract stops paying but never
 * ends the game.
 */
USTRUCT(BlueprintType)
struct LINEBOSSCARFACTORY_API FLBOneFactoryVehicleContract
{
    GENERATED_BODY()

    UPROPERTY(EditAnywhere, BlueprintReadWrite, SaveGame)
    FName ContractId = NAME_None;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, SaveGame)
    FName VehicleModelId = NAME_None;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, SaveGame)
    int32 Quantity = 0;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, SaveGame)
    int64 PricePerVehiclePence = 0;

    /** Ledger sim-clock deadline; non-positive means no deadline. */
    UPROPERTY(EditAnywhere, BlueprintReadWrite, SaveGame)
    double DeadlineSimSeconds = 0.0;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, SaveGame)
    int32 DispatchedCount = 0;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, SaveGame)
    ELBOneFactoryContractState State = ELBOneFactoryContractState::Open;

    /** Rescue work taken in crisis; it paid well and cost reputation. */
    UPROPERTY(EditAnywhere, BlueprintReadWrite, SaveGame)
    bool bEmergency = false;
};

/** Complete versioned cross-department production and runtime gate snapshot. */
USTRUCT(BlueprintType)
struct LINEBOSSCARFACTORY_API FLBOneFactoryProductionLedgerState
{
    GENERATED_BODY()

    UPROPERTY(EditAnywhere, BlueprintReadWrite, SaveGame)
    int32 Version = 1;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, SaveGame)
    FName LedgerId = NAME_None;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, SaveGame)
    int32 Revision = 0;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, SaveGame)
    int32 NextVehicleSerial = 1;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, SaveGame)
    int32 MaximumConcurrentWIP = 8;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, SaveGame)
    int32 CompletedVehicleCount = 0;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, SaveGame)
    int32 DispatchedVehicleCount = 0;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, SaveGame)
    bool bLinePaused = false;

    /**
     * The deterministic simulation clock every deadline, cost bucket and
     * timestamp hangs off. Advanced only by AdvanceSimulationClock while the
     * line is unpaused; pause freezes factory time by design.
     */
    UPROPERTY(EditAnywhere, BlueprintReadWrite, SaveGame)
    double SimClockSeconds = 0.0;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, SaveGame)
    FLBOneFactoryDepartmentCommissioningState Commissioning;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, SaveGame)
    TArray<ELBOneFactoryDepartment> FaultedDepartments;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, SaveGame)
    TArray<ELBOneFactoryDepartment> OutputBlockedDepartments;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, SaveGame)
    TArray<FLBOneFactoryVehicleUnitState> Units;

    /** Customer contracts in creation order; oldest open settles first. */
    UPROPERTY(EditAnywhere, BlueprintReadWrite, SaveGame)
    TArray<FLBOneFactoryVehicleContract> Contracts;

    /** Soft-failure currency: expiries and rescues spend it, never end it. */
    UPROPERTY(EditAnywhere, BlueprintReadWrite, SaveGame)
    int32 ReputationScore = 100;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, SaveGame)
    int32 EmergencyContractSerial = 0;

    /** Derived from cash each economy tick; stored so the HUD reads state. */
    UPROPERTY(EditAnywhere, BlueprintReadWrite, SaveGame)
    ELBOneFactoryFinancialState FinancialState =
        ELBOneFactoryFinancialState::Healthy;
};

UCLASS()
class LINEBOSSCARFACTORY_API ULBOneFactoryProductionFlowLibrary :
    public UBlueprintFunctionLibrary
{
    GENERATED_BODY()

public:
    UFUNCTION(BlueprintPure, Category="Line Boss|OneFactory|Production")
    static FLBOneFactoryProductionLedgerState MakeEmptyLedger();

    UFUNCTION(BlueprintPure, Category="Line Boss|OneFactory|Production")
    static bool ValidateLedger(const FLBOneFactoryProductionLedgerState& State,
        FString& OutReason);

    UFUNCTION(BlueprintPure, Category="Line Boss|OneFactory|Production")
    static ELBOneFactoryDepartment GetDepartmentForStage(
        ELBOneFactoryVehicleStage InStage);

    UFUNCTION(BlueprintPure, Category="Line Boss|OneFactory|Production")
    static bool GetNextStage(ELBOneFactoryVehicleStage InStage,
        ELBOneFactoryVehicleStage& OutStage);

    UFUNCTION(BlueprintPure, Category="Line Boss|OneFactory|Production")
    static bool IsQualityGate(ELBOneFactoryVehicleStage InStage);
};

/**
 * Single logical WIP/genealogy authority for the unified factory. It owns no
 * meshes, station layouts or presentation and never spawns actors by itself.
 */
UCLASS(BlueprintType)
class LINEBOSSCARFACTORY_API ALBOneFactoryProductionFlowAuthority : public AActor
{
    GENERATED_BODY()

public:
    ALBOneFactoryProductionFlowAuthority();

    UFUNCTION(BlueprintPure, Category="Line Boss|OneFactory|Production|Save")
    FLBOneFactoryProductionLedgerState CaptureLedger() const
    { return CurrentState; }

    /** Full validation precedes the single assignment commit. */
    UFUNCTION(BlueprintCallable, Category="Line Boss|OneFactory|Production|Save")
    bool RestoreLedger(const FLBOneFactoryProductionLedgerState& State,
        FString& OutReason);

    UFUNCTION(BlueprintCallable, Category="Line Boss|OneFactory|Production")
    bool SetDepartmentCommissioned(ELBOneFactoryDepartment InDepartment,
        bool bCommissioned, FString& OutReason);

    UFUNCTION(BlueprintCallable, Category="Line Boss|OneFactory|Production")
    bool SetLinePaused(bool bPaused, FString& OutReason);

    /** Advances SimClockSeconds; a paused line holds factory time still. */
    UFUNCTION(BlueprintCallable, Category="Line Boss|OneFactory|Production")
    bool AdvanceSimulationClock(float DeltaSeconds, FString& OutReason);

    /** Adds one open contract; idempotent by ContractId. */
    UFUNCTION(BlueprintCallable, Category="Line Boss|OneFactory|Production")
    bool AddVehicleContract(const FLBOneFactoryVehicleContract& Contract,
        FString& OutReason);

    /** Expires open contracts past their deadline; returns how many. */
    UFUNCTION(BlueprintCallable, Category="Line Boss|OneFactory|Production")
    int32 SweepContractDeadlines(FString& OutReason);

    /** Seeds the sandbox's starter contract chain once; idempotent. */
    UFUNCTION(BlueprintCallable, Category="Line Boss|OneFactory|Production")
    bool SeedStarterContracts(FString& OutReason);

    /**
     * Soft failure: derives the financial state from the cash balance and,
     * in emergency, offers rescue work - one open emergency contract at a
     * premium price and a reputation cost. Never ends the game.
     */
    UFUNCTION(BlueprintCallable, Category="Line Boss|OneFactory|Production")
    bool ApplyFinancialPolicy(int64 CashBalancePence, FString& OutReason);

    UFUNCTION(BlueprintCallable, Category="Line Boss|OneFactory|Production")
    bool SetDepartmentFaulted(ELBOneFactoryDepartment InDepartment,
        bool bFaulted, FString& OutReason);

    UFUNCTION(BlueprintCallable, Category="Line Boss|OneFactory|Production")
    bool SetDepartmentOutputBlocked(ELBOneFactoryDepartment InDepartment,
        bool bBlocked, FString& OutReason);

    /** Creates exactly one logical car identity at the Press inbound boundary. */
    UFUNCTION(BlueprintCallable, Category="Line Boss|OneFactory|Production")
    bool CreateVehicleOrder(FName BuildOrderId, FName VehicleModelId,
        FName PaintProgrammeId, FName PaintColourId, FName SourceCoilLotId,
        FName InboundStationId, FName& OutUnitId, FString& OutReason);

    /** Advances only to the exact next stage and records one unique evidence ID. */
    UFUNCTION(BlueprintCallable, Category="Line Boss|OneFactory|Production")
    bool AdvanceVehicle(FName UnitId, FName TargetStationId, FName EvidenceId,
        FString& OutReason);

    UFUNCTION(BlueprintCallable, Category="Line Boss|OneFactory|Production|Quality")
    bool SubmitQualityResult(FName UnitId,
        ELBOneFactoryVehicleQualityState InQualityState, FName EvidenceId,
        FString& OutReason);

    UFUNCTION(BlueprintCallable, Category="Line Boss|OneFactory|Production|Quality")
    bool ResetQualityAfterRework(FName UnitId, FName EvidenceId,
        FString& OutReason);

    UFUNCTION(BlueprintPure, Category="Line Boss|OneFactory|Production")
    int32 GetActiveWIPCount() const;

    static FName GetAuthorityTag();

private:
    UPROPERTY(VisibleInstanceOnly, SaveGame,
        Category="Line Boss|OneFactory|Production")
    FLBOneFactoryProductionLedgerState CurrentState;

    FLBOneFactoryVehicleUnitState* FindUnit(FName UnitId);
    const FLBOneFactoryVehicleUnitState* FindUnit(FName UnitId) const;
    bool IsDepartmentCommissioned(ELBOneFactoryDepartment InDepartment) const;
    bool HasActiveWIPInDepartment(ELBOneFactoryDepartment InDepartment) const;
    bool EvidenceIdExists(FName EvidenceId) const;
};
