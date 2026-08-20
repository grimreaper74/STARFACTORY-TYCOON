#pragma once

#include "CoreMinimal.h"
#include "LBControlRoomHUD.h"
#include "LBOneFactoryProductionFlow.h"
#include "LBOneFactoryUITypes.h"
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

    /** World-space extent of the group's stations, so a card click can
        frame them with the management camera. */
    FBox WorldBounds = FBox(ForceInit);

    /** First member station's department; measured rates key off it. */
    ELBOneFactoryDepartment Department = ELBOneFactoryDepartment::Press;
    bool bHasDepartment = false;

    /** Completions actually recorded in the trailing sim hour (cars/hour). */
    float MeasuredRatePerHour = 0.0f;
};

/** One live alert: stateful, regenerated from the ledger every collection,
    so a resolved condition disappears by itself (UI research rule 3). */
struct FLBOneFactoryLiveAlert
{
    FText Message;
    ELBOneFactoryStationStatus Status =
        ELBOneFactoryStationStatus::QualityHold;
    /** Which process group raised it, so an alert row can navigate there. */
    int32 GroupIndex = INDEX_NONE;
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

    virtual void BeginPlay() override;
    virtual void DrawHUD() override;

    /** Build-your-own is deferred; the v2 HUD never boots into the legacy
        build catalogue. */
    virtual bool ShouldAutoOpenBuildCatalogue() const override
    {
        return false;
    }

    /** Canvas management band kept behind this toggle for debugging; the
        UMG top bar is the player surface. */
    UPROPERTY(EditAnywhere, Category="Line Boss|OneFactory|HUD")
    bool bUseCanvasManagementBand = false;

    /** Dev tooling reaches the strip to simulate card clicks. */
    class ULBOneFactoryFlowStripWidget* GetFlowStripWidget() const
    {
        return FlowStripWidget;
    }

    /** Dev tooling toggles the alert inbox for capture runs. */
    class ULBOneFactoryAlertCenterWidget* GetAlertCenterWidget() const
    {
        return AlertCenterWidget;
    }

    /** Builds the seven coarse groups from the live route and ledger. */
    static bool CollectGroups(const UWorld* World,
        TArray<FLBOneFactoryProcessGroup>& OutGroups, int32& OutUnitsLive,
        int32& OutDispatched, TArray<FLBOneFactoryLiveAlert>& OutAlerts);

    static ELBOneFactoryGroupState StateForStage(
        ELBOneFactoryVehicleStage Stage);

    /** Reads cash, clock, reputation, wear and contracts in one pass. */
    static bool CollectManagement(const UWorld* World,
        FLBOneFactoryManagementBand& OutBand);

    /** Trailing measured-rate samples for one coarse group, oldest
        first - the v2.1 detail-panel graph reads these. Null when the
        group has no samples yet. */
    const TArray<float>* GetRateHistory(int32 GroupIndex) const
    {
        return RateHistories.IsValidIndex(GroupIndex)
            ? &RateHistories[GroupIndex] : nullptr;
    }

private:
    /** Appends one rate sample per group every few seconds of play. */
    void SampleRateHistory(
        const TArray<FLBOneFactoryProcessGroup>& Groups);

    TArray<TArray<float>> RateHistories;
    double LastRateSampleTime = -1.0;

    void DrawFlowStrip(float Width, float Height, float Scale,
        const TArray<FLBOneFactoryProcessGroup>& Groups, int32 UnitsLive,
        int32 Dispatched, int32 AlertCount);
    void DrawAlertToast(float Width, float Height, float Scale,
        const TArray<FString>& Alerts);
    void DrawManagementBand(float Width, float Scale,
        const FLBOneFactoryManagementBand& Band);

    UPROPERTY() TObjectPtr<class ULBOneFactoryTopBarWidget> TopBarWidget;
    UPROPERTY()
    TObjectPtr<class ULBOneFactoryFlowStripWidget> FlowStripWidget;
    UPROPERTY()
    TObjectPtr<class ULBOneFactoryDetailPanelWidget> DetailPanelWidget;
    UPROPERTY()
    TObjectPtr<class ULBOneFactoryAlertCenterWidget> AlertCenterWidget;
};
