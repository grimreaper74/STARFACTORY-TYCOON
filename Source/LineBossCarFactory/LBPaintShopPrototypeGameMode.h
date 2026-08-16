#pragma once

#include "CoreMinimal.h"
#include "GameFramework/GameModeBase.h"
#include "LBPaintShopPrototypeWorldBootstrap.h"
#include "TimerManager.h"
#include "LBPaintShopPrototypeGameMode.generated.h"

class ALBPaintShopBuildAuthority;
class ALBBodyWeldLineActor;
class ALBPaintShopPrototypeRuntime;
class APlayerController;

/**
 * Paint-only player shell. The map must contain exactly one bootstrap; this mode
 * validates its already-created authority/runtime pair and never spawns either one.
 */
UCLASS()
class LINEBOSSCARFACTORY_API ALBPaintShopPrototypeGameMode : public AGameModeBase
{
    GENERATED_BODY()

public:
    ALBPaintShopPrototypeGameMode();

    virtual void BeginPlay() override;
    virtual void EndPlay(const EEndPlayReason::Type EndPlayReason) override;
    virtual void HandleStartingNewPlayer_Implementation(
        APlayerController* NewPlayer) override;

    UFUNCTION(BlueprintPure, Category="Line Boss|Paint Shop|Prototype")
    ALBPaintShopPrototypeWorldBootstrap* GetPrototypeBootstrap() const
    {
        return PrototypeBootstrap.Get();
    }

    UFUNCTION(BlueprintPure, Category="Line Boss|Paint Shop|Prototype")
    bool HasValidPrototypeBootstrap() const { return bPrototypeBootstrapValid; }

    UFUNCTION(BlueprintPure, Category="Line Boss|Paint Shop|Prototype")
    bool HasFocusedManagementCamera() const { return bManagementCameraFocused; }

    UFUNCTION(BlueprintPure, Category="Line Boss|Paint Shop|Prototype")
    FString GetPrototypeShellStatus() const { return PrototypeShellStatus; }

    /** Re-runs the live cardinality/ownership contract without creating any actor. */
    UFUNCTION(BlueprintCallable, Category="Line Boss|Paint Shop|Prototype")
    bool ValidatePrototypeShellNow(APlayerController* PreferredController);

    /** Manufactures one complete canonical BIW through Weld and atomically hands it to Paint. */
    UFUNCTION(BlueprintCallable, Category="Line Boss|Paint Shop|Prototype|Operator")
    bool StartCanonicalWeldHandoff(FString& OutReason);

    UFUNCTION(BlueprintCallable, Category="Line Boss|Paint Shop|Prototype|Operator")
    bool ToggleProcessPause(FString& OutReason);

    UFUNCTION(BlueprintCallable, Category="Line Boss|Paint Shop|Prototype|Operator")
    bool ToggleOutputBlock(FString& OutReason);

    UFUNCTION(BlueprintCallable, Category="Line Boss|Paint Shop|Prototype|Operator")
    bool ReleasePaintOutput(FString& OutReason);

    UFUNCTION(BlueprintCallable, Category="Line Boss|Paint Shop|Prototype|Operator")
    bool SavePaintState(FString& OutReason);

    UFUNCTION(BlueprintCallable, Category="Line Boss|Paint Shop|Prototype|Operator")
    bool LoadPaintState(FString& OutReason);

    UFUNCTION(BlueprintPure, Category="Line Boss|Paint Shop|Prototype|Operator")
    FString GetLastOperatorActionStatus() const { return LastOperatorActionStatus; }

    UFUNCTION(BlueprintPure, Category="Line Boss|Paint Shop|Prototype|Operator")
    bool WasLastOperatorActionSuccessful() const { return bLastOperatorActionSuccessful; }

#if WITH_DEV_AUTOMATION_TESTS
    bool SavePaintStateToAutomationSlot(const FString& SlotName, FString& OutReason);
    bool LoadPaintStateFromAutomationSlot(const FString& SlotName, FString& OutReason);
    ALBBodyWeldLineActor* GetOperatorWeldSourceForTests() const
    {
        return OperatorWeldSource.Get();
    }
#endif

    /** Pure fail-closed cardinality/readiness contract used by automation. */
    static bool ValidateBootstrapContract(int32 BootstrapCount,
        int32 BuildAuthorityCount, int32 RuntimeCount,
        ELBPaintShopPrototypeBootstrapState BootstrapState,
        bool bHasBuildAuthority, bool bHasRuntime, bool bRuntimeInitialized,
        bool bRuntimeBoundToAuthority, bool bHasApprovedEDCoatCell,
        FString& OutReason);

private:
    UPROPERTY(Transient)
    TWeakObjectPtr<ALBPaintShopPrototypeWorldBootstrap> PrototypeBootstrap;

    UPROPERTY(Transient)
    TWeakObjectPtr<APlayerController> FocusedManagementController;

    /** Hidden transient provenance source only; it never owns Paint process state. */
    UPROPERTY(Transient)
    TObjectPtr<ALBBodyWeldLineActor> OperatorWeldSource;

    bool bPrototypeBootstrapValid = false;
    bool bManagementCameraFocused = false;
    bool bLastOperatorActionSuccessful = true;
    FString PrototypeShellStatus = TEXT("PAINT SHOP PLAYER SHELL WAITING FOR BOOTSTRAP");
    FString LastOperatorActionStatus = TEXT("OPERATOR: READY - START A CANONICAL WELD HANDOFF");
    int32 DeferredValidationAttemptsRemaining = 0;
    FTimerHandle IntegrityValidationTimer;

    void RunDeferredStartupValidation();
    void MonitorPrototypeShellIntegrity();
    bool FocusManagementPawn(APlayerController* Controller);
    ALBPaintShopPrototypeRuntime* ResolveOperatorRuntime(FString& OutReason);
    bool BuildCanonicalWeldOutput(int32 IdentitySerial,
        ALBBodyWeldLineActor*& OutSource, FName& OutBodyId,
        FName& OutCarrierId, FString& OutReason);
    void EnforceOperatorWeldSourceIsolation(ALBBodyWeldLineActor* Source) const;
    void DestroyOperatorWeldSource();
    bool FinishOperatorAction(const TCHAR* Action, bool bSuccess,
        const FString& Detail, FString& OutReason);
};
