#pragma once

#include "CoreMinimal.h"
#include "GameFramework/HUD.h"
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

/**
 * The production-flow overlay for Moorcross Works.
 *
 * Everything drawn here is read from the runtime coordinator and the production
 * ledger. Nothing is invented: station counts come from the configured route,
 * throughput from the authored cycle times, occupancy and progress from the
 * ledger, and alert text from the coordinator's own reasons.
 *
 * Deliberately a separate HUD rather than a change to ALBControlRoomHUD, because
 * the OneFactory player-shell contract test asserts the game mode's default
 * classes. Swap it in at runtime with LB.OneFactory.HUD.
 */
UCLASS()
class LINEBOSSCARFACTORY_API ALBOneFactoryProductionHUD : public AHUD
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

private:
    void DrawTopBar(float Width, float Height, float Scale, int32 UnitsLive,
        int32 Dispatched, const TArray<FString>& Alerts);
    void DrawFlowStrip(float Width, float Height, float Scale,
        const TArray<FLBOneFactoryProcessGroup>& Groups);
    void DrawAlertToast(float Width, float Height, float Scale,
        const TArray<FString>& Alerts);
};
