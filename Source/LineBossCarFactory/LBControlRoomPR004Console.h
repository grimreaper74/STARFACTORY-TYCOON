#pragma once

#include "CoreMinimal.h"
#include "GameFramework/Actor.h"
#include "LBControlRoomPR004Console.generated.h"

class ALBPR004Station;
class ULBPR004HMIWidget;
class UBoxComponent;
class USceneComponent;
class UTextRenderComponent;
class UWidgetComponent;

/** World-space control-room terminal bound to authoritative PR-004 state. */
UCLASS()
class LINEBOSSCARFACTORY_API ALBControlRoomPR004Console : public AActor
{
    GENERATED_BODY()

public:
    ALBControlRoomPR004Console();
    virtual void BeginPlay() override;
    virtual void Tick(float DeltaSeconds) override;

    UFUNCTION(BlueprintCallable, Category = "Cairnwell|Control Room|PR-004")
    bool BindAvailableStation();

    UFUNCTION(BlueprintPure, Category = "Cairnwell|Control Room|PR-004")
    ALBPR004Station* GetBoundStation() const { return BoundStation.Get(); }

    /** Executes the selected screen's single approved player action. */
    UFUNCTION(BlueprintCallable, Category = "Cairnwell|Control Room|PR-004")
    bool TriggerPrimaryAction(FName EvidenceId = TEXT("CONTROL_ROOM_PR004_SCREEN"));

    /** Parameterless reflected entry point used by deterministic runtime validation. */
    UFUNCTION(BlueprintCallable, Category = "Cairnwell|Control Room|PR-004")
    bool ExecutePrimaryAction();

private:
    UPROPERTY(VisibleAnywhere, Category = "Cairnwell|Control Room|PR-004")
    TObjectPtr<USceneComponent> ConsoleRoot;

    UPROPERTY(VisibleAnywhere, Category = "Cairnwell|Control Room|PR-004")
    TObjectPtr<UWidgetComponent> OperatorScreen;

    UPROPERTY(VisibleAnywhere, Category = "Cairnwell|Control Room|PR-004")
    TObjectPtr<UBoxComponent> ScreenInteractionSurface;

    UPROPERTY(VisibleAnywhere, Category = "Cairnwell|Control Room|PR-004")
    TObjectPtr<UTextRenderComponent> HMIBrandText;

    UPROPERTY(VisibleAnywhere, Category = "Cairnwell|Control Room|PR-004")
    TObjectPtr<UTextRenderComponent> HMIStationText;

    UPROPERTY(VisibleAnywhere, Category = "Cairnwell|Control Room|PR-004")
    TObjectPtr<UTextRenderComponent> HMIStateText;

    UPROPERTY(VisibleAnywhere, Category = "Cairnwell|Control Room|PR-004")
    TObjectPtr<UTextRenderComponent> HMICoilText;

    UPROPERTY(VisibleAnywhere, Category = "Cairnwell|Control Room|PR-004")
    TObjectPtr<UTextRenderComponent> HMIRecipeText;

    UPROPERTY(VisibleAnywhere, Category = "Cairnwell|Control Room|PR-004")
    TObjectPtr<UTextRenderComponent> HMIChecklistText;

    UPROPERTY(VisibleAnywhere, Category = "Cairnwell|Control Room|PR-004")
    TObjectPtr<UTextRenderComponent> HMIActionText;

    UPROPERTY(EditAnywhere, Category = "Cairnwell|Control Room|PR-004")
    bool bSpawnAuthorityIfMissing = true;

    UPROPERTY(EditAnywhere, Category = "Cairnwell|Control Room|PR-004")
    bool bBootstrapReadyPackagedCoil = true;

    UPROPERTY(Transient)
    TWeakObjectPtr<ALBPR004Station> BoundStation;

    float HMIRefreshAccumulator = 0.0f;

    bool ConfigureCandidateAuthority(ALBPR004Station* Station) const;
    void UpdateHMITextPresentation();
};
