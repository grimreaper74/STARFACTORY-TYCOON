#pragma once

#include "CoreMinimal.h"
#include "Blueprint/UserWidget.h"
#include "LBPaintShopPrototypeRootWidget.generated.h"

class ALBPaintShopPrototypeGameMode;
class UButton;
class UTextBlock;

/**
 * Native UMG operator shell for the isolated Paint ED-coat slice. It displays
 * authority-owned state and delegates controls to GameMode; it owns no process,
 * lineage, build or persistence state.
 */
UCLASS(BlueprintType)
class LINEBOSSCARFACTORY_API ULBPaintShopPrototypeRootWidget : public UUserWidget
{
    GENERATED_BODY()

public:
    static TArray<FName> GetCanonicalControlIds();

    UFUNCTION(BlueprintCallable, Category="Line Boss|Paint Shop|Prototype|UI")
    void RefreshFromRuntime();

    UFUNCTION(BlueprintPure, Category="Line Boss|Paint Shop|Prototype|UI")
    bool HasRenderableShell() const;

protected:
    virtual TSharedRef<SWidget> RebuildWidget() override;
    virtual void NativeOnInitialized() override;
    virtual void NativeConstruct() override;
    virtual void NativeTick(const FGeometry& MyGeometry, float InDeltaTime) override;

private:
    UPROPERTY(Transient) TObjectPtr<UTextBlock> IsolationLabel;
    UPROPERTY(Transient) TObjectPtr<UTextBlock> RuntimeLabel;
    UPROPERTY(Transient) TObjectPtr<UTextBlock> OperatorLabel;
    UPROPERTY(Transient) TObjectPtr<UTextBlock> CameraLabel;
    UPROPERTY(Transient) TObjectPtr<UTextBlock> PauseButtonLabel;
    UPROPERTY(Transient) TObjectPtr<UTextBlock> BlockButtonLabel;
    UPROPERTY(Transient) TObjectPtr<UButton> StartButton;
    UPROPERTY(Transient) TObjectPtr<UButton> PauseButton;
    UPROPERTY(Transient) TObjectPtr<UButton> BlockButton;
    UPROPERTY(Transient) TObjectPtr<UButton> ReleaseButton;
    UPROPERTY(Transient) TObjectPtr<UButton> SaveButton;
    UPROPERTY(Transient) TObjectPtr<UButton> LoadButton;

    float RefreshAccumulatorSeconds = 0.0f;

    void BuildShell();
    ALBPaintShopPrototypeGameMode* ResolveOperatorGameMode() const;

    UFUNCTION() void HandleStartClicked();
    UFUNCTION() void HandlePauseClicked();
    UFUNCTION() void HandleBlockClicked();
    UFUNCTION() void HandleReleaseClicked();
    UFUNCTION() void HandleSaveClicked();
    UFUNCTION() void HandleLoadClicked();
};
