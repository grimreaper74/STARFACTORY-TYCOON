#pragma once

#include "CoreMinimal.h"
#include "LBControlRoomHUD.h"
#include "LBOneFactoryProductionFlow.h"
#include "LBOneFactoryProductionHUD.generated.h"

class ALBOneFactoryProductionFlowAuthority;
class ALBOneFactoryRuntimeCoordinator;

/** How a process group is behaving right now. Colour follows the brand rules. */
UENUM(BlueprintType)
enum class ELBOneFactoryGroupState : uint8
{
    /** No unit present. */
    Idle,
    /** At least one unit cycling normally. */
    Running,
    /** A unit finished its cycle but cannot move on. */
    Waiting,
    /** A unit is held at a quality gate awaiting a result. */
    Hold
};

/** One card in the production-flow strip: a coarse stage of the car's journey. */
USTRUCT()
struct FLBOneFactoryProcessGroup
{
    GENERATED_BODY()

    FString Label;
    int32 StationCount = 0;
    int32 UnitCount = 0;
    float MeanProgress = 0.0f;
    float ThroughputPerHour = 0.0f;
    bool bHasQualityGate = false;
    ELBOneFactoryGroupState State = ELBOneFactoryGroupState::Idle;
};

/** One contract row for the HUD panel. */
struct FLBOneFactoryContractRow
{
    FString ContractId;
    int32 DispatchedCount = 0;
    int32 Quantity = 0;
    double SecondsRemaining = 0.0;
    ELBOneFactoryContractState State = ELBOneFactoryContractState::Open;
    bool bEmergency = false;
};

/** Everything the management band needs, read in one pass. */
struct FLBOneFactoryManagementBand
{
    bool bHasCash = false;
    int64 CashPence = 0;
    double SimClockSeconds = 0.0;
    bool bPaused = false;
    int32 Reputation = 100;
    double FleetWear01 = 0.0;
    ELBOneFactoryFinancialState FinancialState =
        ELBOneFactoryFinancialState::Healthy;
    TArray<FLBOneFactoryContractRow> Contracts;
};

/**
 * The production-flow overlay for Moorcross Works.
 *
 * Everything drawn here is read from the runtime coordinator and the production
 * ledger. Nothing is invented: station counts come from the configured route,
 * throughput from the authored cycle times, occupancy and progress from the
 * ledger, and alert text from the coordinator's own reasons.
 *
 * Derives from ALBControlRoomHUD rather than replacing it, so every surface the
 * ControlRoom HUD already draws is preserved and this only adds the production
 * flow strip and alert toasts beneath it. The game mode installs this directly,
 * so no console swap is needed; LB.OneFactory.HUD remains for editor sessions
 * started another way.
 */
UCLASS()
class LINEBOSSCARFACTORY_API ALBOneFactoryProductionHUD :
    public ALBControlRoomHUD
{
    GENERATED_BODY()

public:
    ALBOneFactoryProductionHUD();

    virtual void DrawHUD() override;

    /** Builds the seven coarse groups from the live route and ledger. */
    static bool CollectGroups(const UWorld* World,
        TArray<FLBOneFactoryProcessGroup>& OutGroups, int32& OutUnitsLive,
        int32& OutDispatched, TArray<FString>& OutAlerts);

    static ELBOneFactoryGroupState StateForStage(
        ELBOneFactoryVehicleStage Stage);

    /** Reads cash, clock, reputation, wear and contracts in one pass. */
    static bool CollectManagement(const UWorld* World,
        FLBOneFactoryManagementBand& OutBand);

private:
    void DrawFlowStrip(float Width, float Height, float Scale,
        const TArray<FLBOneFactoryProcessGroup>& Groups, int32 UnitsLive,
        int32 Dispatched, int32 AlertCount);
    void DrawAlertToast(float Width, float Height, float Scale,
        const TArray<FString>& Alerts);
    void DrawManagementBand(float Width, float Scale,
        const FLBOneFactoryManagementBand& Band);
};
