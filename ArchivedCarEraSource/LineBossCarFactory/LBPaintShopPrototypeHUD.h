#pragma once

#include "CoreMinimal.h"
#include "GameFramework/HUD.h"
#include "LBPaintShopPrototypeRuntime.h"
#include "LBPaintShopPrototypeWorldBootstrap.h"
#include "LBPaintShopPrototypeHUD.generated.h"

class ULBPaintShopPrototypeRootWidget;

/** Native UMG-only host for the isolated Paint Shop player shell. */
UCLASS()
class LINEBOSSCARFACTORY_API ALBPaintShopPrototypeHUD : public AHUD
{
    GENERATED_BODY()

public:
    ALBPaintShopPrototypeHUD();

    virtual void BeginPlay() override;
    virtual void Tick(float DeltaSeconds) override;
    virtual void EndPlay(const EEndPlayReason::Type EndPlayReason) override;

    UFUNCTION(BlueprintPure, Category="Line Boss|Paint Shop|Prototype|UI")
    bool IsPrototypeWidgetActive() const;

    UFUNCTION(BlueprintPure, Category="Line Boss|Paint Shop|Prototype|UI")
    ULBPaintShopPrototypeRootWidget* GetPrototypeRootWidget() const
    {
        return PrototypeRootWidget.Get();
    }

    static FString BuildIsolationReadout(int32 BootstrapCount,
        ELBPaintShopPrototypeBootstrapState BootstrapState,
        bool bCoherentReadyState, const FString& DetailReason);
    static FString BuildRuntimeStageReadout(ELBPaintShopPrototypePhase Phase,
        float PhaseProgress01, bool bPaused, bool bOutputBlocked,
        bool bFaulted, const FString& FaultReason);
    static FString GetCameraControlsReadout();
    static FString GetOperatorControlsReadout();
    static bool UsesCanvasRendering() { return false; }

private:
    UPROPERTY(Transient)
    TObjectPtr<ULBPaintShopPrototypeRootWidget> PrototypeRootWidget;

    bool EnsurePrototypeWidget();
};
