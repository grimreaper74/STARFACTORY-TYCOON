#pragma once

#include "Blueprint/UserWidget.h"
#include "CoreMinimal.h"
#include "LBOneFactoryUITypes.h"
#include "LBOneFactoryTopBarWidget.generated.h"

class UButton;
class UTextBlock;

/**
 * UI v2 top bar (U2): brand, active-contract progress, cash coloured by
 * financial state, day clock with pause chip, reputation/wear, transport
 * buttons and the alert bell. Strictly read-only global state plus the
 * transport controls; native UMG built in code, all text localised.
 */
UCLASS()
class LINEBOSSCARFACTORY_API ULBOneFactoryTopBarWidget : public UUserWidget
{
    GENERATED_BODY()

public:
    virtual TSharedRef<SWidget> RebuildWidget() override;
    virtual void NativeConstruct() override;
    virtual void NativeTick(const FGeometry& MyGeometry,
        float InDeltaTime) override;

private:
    void BuildTree();
    void Refresh();
    bool SetSimulationRate(float Rate);

    UFUNCTION() void OnPauseClicked();
    UFUNCTION() void OnSpeed1Clicked();
    UFUNCTION() void OnSpeed2Clicked();
    UFUNCTION() void OnSpeed4Clicked();

    UPROPERTY() TObjectPtr<UTextBlock> ContractText;
    UPROPERTY() TObjectPtr<UTextBlock> CashText;
    UPROPERTY() TObjectPtr<UTextBlock> ClockText;
    UPROPERTY() TObjectPtr<UTextBlock> RepWearText;
    UPROPERTY() TObjectPtr<UTextBlock> AlertText;
    UPROPERTY() TObjectPtr<UButton> PauseButton;
    UPROPERTY() TObjectPtr<UButton> Speed1Button;
    UPROPERTY() TObjectPtr<UButton> Speed2Button;
    UPROPERTY() TObjectPtr<UButton> Speed4Button;
    UPROPERTY() TObjectPtr<UTextBlock> PauseLabel;
    UPROPERTY() TObjectPtr<UTextBlock> Speed1Label;
    UPROPERTY() TObjectPtr<UTextBlock> Speed2Label;
    UPROPERTY() TObjectPtr<UTextBlock> Speed4Label;

    float RefreshAccumulator = 0.0f;
};
