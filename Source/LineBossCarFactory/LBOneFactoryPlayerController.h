#pragma once

#include "CoreMinimal.h"
#include "GameFramework/PlayerController.h"
#include "LBOneFactoryPlayerController.generated.h"

/**
 * Player commands for Moorcross Works.
 *
 * Everything the factory can do was already reachable, but only through console
 * commands, which is why the whole shell stayed validation-only: nobody could
 * actually play it. This binds those same tested APIs to keys so a player can
 * commission the factory, put orders on the line, control the clock and resolve
 * quality holds without opening a console.
 *
 * Bindings are direct key binds rather than Enhanced Input actions so the shell
 * needs no new Content assets and works in a packaged build immediately. Moving
 * to Enhanced Input with authored actions and a rebindable mapping context is
 * the natural follow-up, not a blocker.
 */
UCLASS()
class LINEBOSSCARFACTORY_API ALBOneFactoryPlayerController : public APlayerController
{
    GENERATED_BODY()

public:
    ALBOneFactoryPlayerController();

    virtual void SetupInputComponent() override;

    /** Creates and commissions all four departments, then dresses the site. */
    UFUNCTION(BlueprintCallable, Exec, Category="Line Boss|OneFactory|Player")
    void CommissionFactory();

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

    /** Saves the whole factory - layouts, ledger and mid-cycle runtime state. */
    UFUNCTION(BlueprintCallable, Exec, Category="Line Boss|OneFactory|Player")
    void SaveFactory();

    /** Restores the last save, rebuilding presentation from the snapshot. */
    UFUNCTION(BlueprintCallable, Exec, Category="Line Boss|OneFactory|Player")
    void LoadFactory();

private:
    void ApplyTimeScale(float TimeScale);
    bool ResolveOldestHold(FName& OutUnitId, FString& OutReason) const;

    /**
     * Brings the site presentation up around a commissioned or restored
     * line: envelope, dressing, restored shop, roof state, dev lighting and
     * the WIP view. Idempotent - every step finds existing actors before
     * spawning and every builder rebuilds its own content.
     */
    void EnsureSitePresentation();

    /** Last speed used, so pause can restore what the player had chosen. */
    float LastRunningTimeScale = 1.0f;
    int32 QualityEvidenceCounter = 0;
};
