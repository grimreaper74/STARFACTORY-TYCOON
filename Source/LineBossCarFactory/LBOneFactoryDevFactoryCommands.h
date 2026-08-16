#pragma once

#include "CoreMinimal.h"
#include "Kismet/BlueprintFunctionLibrary.h"
#include "LBOneFactoryDevFactoryCommands.generated.h"

class ALBOneFactoryProductionFlowAuthority;
class ALBOneFactoryRuntimeCoordinator;

/**
 * Developer-only orchestration that drives the shipped OneFactory player
 * builder and runtime coordinator through a whole working factory in one step.
 *
 * ALBOneFactoryGameMode deliberately seeds nothing: SeedsProductionStations()
 * is false and ValidateBootstrapContract() rejects a shell that would seed. The
 * Moorcross Works map therefore always opens ready but empty, and the runtime
 * coordinator refuses to run until a player has created and commissioned all
 * four departments. That is correct for the shipped product, but it means the
 * 57-station loop had only ever been exercised by synthetic-world automation.
 *
 * Every function below calls the same public API a player action calls. It
 * creates no second authority, seeds no station into the map package, persists
 * nothing and owns no presentation. It is a way to *run* the existing factory,
 * not a new factory.
 */
UCLASS()
class LINEBOSSCARFACTORY_API ULBOneFactoryDevFactory :
    public UBlueprintFunctionLibrary
{
    GENERATED_BODY()

public:
    /**
     * Creates and commissions Press, Body/Weld, Paint and Assembly in the
     * contract's lifecycle order, then audits the resulting 57-station route.
     * Stops at the first failing step and reports which one failed.
     */
    UFUNCTION(BlueprintCallable, Category="Line Boss|OneFactory|Developer",
        meta=(WorldContext="WorldContextObject"))
    static bool BuildAndCommissionWholeFactory(UObject* WorldContextObject,
        FString& OutReason);

    /**
     * Creates VehicleCount build orders and releases each into processing.
     * Vehicle model and paint programme are read from the live committed
     * layouts rather than hard-coded, matching the automation setup.
     */
    UFUNCTION(BlueprintCallable, Category="Line Boss|OneFactory|Developer",
        meta=(WorldContext="WorldContextObject"))
    static bool StartDemoProduction(UObject* WorldContextObject,
        int32 VehicleCount, FString& OutReason);

    /**
     * Advances every started unit by DeltaSeconds. Body, Paint and end-of-line
     * inspections hold at 100 percent until a quality result is submitted; with
     * bAutoPassQualityGates the developer loop passes them so cars keep moving.
     */
    UFUNCTION(BlueprintCallable, Category="Line Boss|OneFactory|Developer",
        meta=(WorldContext="WorldContextObject"))
    static bool AdvanceFactory(UObject* WorldContextObject, float DeltaSeconds,
        bool bAutoPassQualityGates, int32& OutProcessedUnitCount,
        FString& OutReason);

    /**
     * Runs Iterations deterministic steps of StepSeconds each. Deterministic
     * stepping is used rather than wall-clock so an unattended run produces the
     * same result every time.
     */
    UFUNCTION(BlueprintCallable, Category="Line Boss|OneFactory|Developer",
        meta=(WorldContext="WorldContextObject"))
    static bool RunFactory(UObject* WorldContextObject, int32 Iterations,
        float StepSeconds, bool bAutoPassQualityGates, FString& OutReason);

    /** Route topology plus per-unit progress. Reads only; mutates nothing. */
    UFUNCTION(BlueprintCallable, Category="Line Boss|OneFactory|Developer",
        meta=(WorldContext="WorldContextObject"))
    static bool BuildFactoryStatusReport(UObject* WorldContextObject,
        FString& OutReport);

    /** Body/Weld slice: every unit currently standing in a Body station. */
    UFUNCTION(BlueprintCallable, Category="Line Boss|OneFactory|Developer",
        meta=(WorldContext="WorldContextObject"))
    static bool BuildBodyWeldReport(UObject* WorldContextObject,
        FString& OutReport);

    static ALBOneFactoryRuntimeCoordinator* FindCoordinator(const UWorld* World);
    static ALBOneFactoryProductionFlowAuthority* FindProductionFlow(
        const UWorld* World);
};
