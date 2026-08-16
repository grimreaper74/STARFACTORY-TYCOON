#pragma once

#include "CoreMinimal.h"
#include "Subsystems/WorldSubsystem.h"
#include "LBOneFactoryPlayerBuilderSubsystem.h"
#include "LBOneFactoryRuntimeCoordinator.h"
#include "LBOneFactoryOperationsSubsystem.generated.h"

class ALBOneFactoryProductionFlowAuthority;

/**
 * Actual-player operations seam for the dedicated OneFactory map.
 *
 * It projects the presentation-free runtime coordinator into the existing five
 * native-UMG action slots. It owns no station, WIP, presentation or save data.
 */
UCLASS()
class LINEBOSSCARFACTORY_API ULBOneFactoryOperationsSubsystem :
    public UWorldSubsystem
{
    GENERATED_BODY()

public:
    static constexpr int32 UMGActionCount = 5;

    UFUNCTION(BlueprintPure, Category="Line Boss|OneFactory|Operations")
    bool IsOneFactoryOperationsWorld() const;

    UFUNCTION(BlueprintPure, Category="Line Boss|OneFactory|Operations|UMG")
    TArray<FLBOneFactoryBuilderUMGAction> GetUMGActions() const;

    UFUNCTION(BlueprintPure, Category="Line Boss|OneFactory|Operations|UMG")
    FString GetUMGSummary() const;

    UFUNCTION(BlueprintCallable, Category="Line Boss|OneFactory|Operations|UMG")
    bool ExecuteUMGAction(int32 ActionIndex, FString& OutReason);

    /** 0 pauses the durable line; positive values select 1x/2x runtime time. */
    UFUNCTION(BlueprintCallable, Category="Line Boss|OneFactory|Operations|UMG")
    bool SetSimulationRate(float RequestedRate, FString& OutReason);

    UFUNCTION(BlueprintPure, Category="Line Boss|OneFactory|Operations")
    FName GetSelectedUnitId() const { return SelectedUnitId; }

    UFUNCTION(BlueprintPure, Category="Line Boss|OneFactory|Operations")
    FString GetLastActionReason() const { return LastActionReason; }

private:
    bool ResolveRuntime(ALBOneFactoryProductionFlowAuthority*& OutProduction,
        ALBOneFactoryRuntimeCoordinator*& OutCoordinator,
        FString& OutReason) const;
    bool ResolveEffectiveUnit(FName& OutUnitId,
        FLBOneFactoryRuntimeVehicleStatus& OutStatus,
        FString& OutReason) const;
    bool CreateConfiguredVehicle(FString& OutReason);
    bool SelectNextVehicle(FString& OutReason);
    bool StartOrAdvanceSelectedVehicle(FString& OutReason);
    bool PassSelectedQualityGate(FString& OutReason);
    bool RequestOrCompleteSelectedRework(FString& OutReason);
    void SetLastResult(bool bSucceeded, const FString& Reason,
        FString& OutReason);

    UPROPERTY(Transient)
    FName SelectedUnitId = NAME_None;

    UPROPERTY(Transient)
    FString LastActionReason = TEXT("NO ONEFACTORY VEHICLE ACTION THIS SESSION");

    UPROPERTY(Transient)
    bool bLastActionSucceeded = true;
};

