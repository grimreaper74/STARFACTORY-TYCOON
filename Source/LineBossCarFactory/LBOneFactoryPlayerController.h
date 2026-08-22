#pragma once

#include "CoreMinimal.h"
#include "GameFramework/PlayerController.h"
#include "LBOneFactoryPlayerController.generated.h"

class UInputAction;
class UInputMappingContext;

/**
 * Player commands for Moorcross Works.
 *
 * Everything the factory can do was already reachable, but only through console
 * commands, which is why the whole shell stayed validation-only: nobody could
 * actually play it. This binds those same tested APIs to keys so a player can
 * commission the factory, put orders on the line, control the clock and resolve
 * quality holds without opening a console.
 *
 * Commands are registered through a dedicated Enhanced Input mapping context.
 * The controller-bound focus route remains as a compatibility guard for native
 * UMG focus, which must never make advertised keyboard controls unreachable.
 */
UCLASS()
class LINEBOSSCARFACTORY_API ALBOneFactoryPlayerController : public APlayerController
{
    GENERATED_BODY()

public:
    ALBOneFactoryPlayerController();

    virtual void BeginPlay() override;
    virtual void SetupInputComponent() override;

    /**
     * Last-resort game input route. Native UMG controls can legitimately own
     * Slate focus after a mouse click; route supported factory shortcuts here
     * before PlayerInput dispatch so they stay usable without a controller.
     */
    virtual bool InputKey(const FInputKeyEventArgs& Params) override;

    /** Runs a player shortcut while a native UMG control owns keyboard focus. */
    bool HandleKeyboardShortcut(const FKey& Key);

    /** Creates and commissions all four departments, then dresses the site. */
    UFUNCTION(BlueprintCallable, Exec, Category="Line Boss|OneFactory|Player")
    void CommissionFactory();

    /**
     * Brings the shipped prebuilt factory online. This is also used by the
     * game mode at startup so release players begin with a working line,
     * rather than a construction-only empty site.
     */
    bool ActivatePrebuiltFactory(FString& OutReason);

    /** Puts one more vehicle order on the line. */
    UFUNCTION(BlueprintCallable, Exec, Category="Line Boss|OneFactory|Player")
    void PlaceOrder();

    /** Pauses or resumes the line. */
    UFUNCTION(BlueprintCallable, Exec, Category="Line Boss|OneFactory|Player")
    void TogglePause();

    UFUNCTION(BlueprintCallable, Exec, Category="Line Boss|OneFactory|Player")
    void SetSpeedNormal();

    UFUNCTION(BlueprintCallable, Exec, Category="Line Boss|OneFactory|Player")
    void SetSpeedFast();

    UFUNCTION(BlueprintCallable, Exec, Category="Line Boss|OneFactory|Player")
    void SetSpeedVeryFast();

    /** Passes the oldest unit currently held at a quality gate. */
    UFUNCTION(BlueprintCallable, Exec, Category="Line Boss|OneFactory|Player")
    void PassOldestQualityHold();

    /** Sends the oldest unit currently held at a quality gate for rework. */
    UFUNCTION(BlueprintCallable, Exec, Category="Line Boss|OneFactory|Player")
    void ReworkOldestQualityHold();

    /** Pays the maintenance fee and resets fleet wear. */
    UFUNCTION(BlueprintCallable, Exec, Category="Line Boss|OneFactory|Player")
    void ServicePlant();

    /** F1-F4 frame a shop and open its detail panel (locked grammar). */
    UFUNCTION(BlueprintCallable, Exec, Category="Line Boss|OneFactory|Player")
    void FocusPressShop();
    UFUNCTION(BlueprintCallable, Exec, Category="Line Boss|OneFactory|Player")
    void FocusBodyShop();
    UFUNCTION(BlueprintCallable, Exec, Category="Line Boss|OneFactory|Player")
    void FocusPaintShop();
    UFUNCTION(BlueprintCallable, Exec, Category="Line Boss|OneFactory|Player")
    void FocusAssemblyShop();

    /** Saves the whole factory - layouts, ledger and mid-cycle runtime state. */
    UFUNCTION(BlueprintCallable, Exec, Category="Line Boss|OneFactory|Player")
    void SaveFactory();

    /** Restores the last save, rebuilding presentation from the snapshot. */
    UFUNCTION(BlueprintCallable, Exec, Category="Line Boss|OneFactory|Player")
    void LoadFactory();

private:
    void InstallEnhancedInputMappings();
    void BindEnhancedInputActions();
    UInputAction* CreateCommandAction(FName ActionName);
    void MapCommand(UInputAction* Action, const FKey& Key);

    void ApplyTimeScale(float TimeScale);
    bool ResolveOldestHold(FName& OutUnitId, FString& OutReason) const;
    void FocusShopGroup(int32 GroupIndex);

    /**
     * Brings the site presentation up around a commissioned or restored
     * line: envelope, dressing, restored shop, roof state, dev lighting and
     * the WIP view. Idempotent - every step finds existing actors before
     * spawning and every builder rebuilds its own content.
     */
    void EnsureSitePresentation();

    /** Last speed used, so pause can restore what the player had chosen. */
    float LastRunningTimeScale = 1.0f;

    /** Runtime-created until these are promoted to rebindable authored assets. */
    UPROPERTY(Transient)
    TObjectPtr<UInputMappingContext> OneFactoryInputContext;

    UPROPERTY(Transient)
    bool bEnhancedInputContextInstalled = false;

    UPROPERTY(Transient)
    TObjectPtr<UInputAction> PlaceOrderInputAction;
    UPROPERTY(Transient)
    TObjectPtr<UInputAction> TogglePauseInputAction;
    UPROPERTY(Transient)
    TObjectPtr<UInputAction> SpeedNormalInputAction;
    UPROPERTY(Transient)
    TObjectPtr<UInputAction> SpeedFastInputAction;
    UPROPERTY(Transient)
    TObjectPtr<UInputAction> SpeedVeryFastInputAction;
    UPROPERTY(Transient)
    TObjectPtr<UInputAction> PassQualityInputAction;
    UPROPERTY(Transient)
    TObjectPtr<UInputAction> ReworkInputAction;
    UPROPERTY(Transient)
    TObjectPtr<UInputAction> ServiceInputAction;
    UPROPERTY(Transient)
    TObjectPtr<UInputAction> SaveInputAction;
    UPROPERTY(Transient)
    TObjectPtr<UInputAction> LoadInputAction;
    UPROPERTY(Transient)
    TObjectPtr<UInputAction> FocusPressInputAction;
    UPROPERTY(Transient)
    TObjectPtr<UInputAction> FocusBodyInputAction;
    UPROPERTY(Transient)
    TObjectPtr<UInputAction> FocusPaintInputAction;
    UPROPERTY(Transient)
    TObjectPtr<UInputAction> FocusAssemblyInputAction;
};
