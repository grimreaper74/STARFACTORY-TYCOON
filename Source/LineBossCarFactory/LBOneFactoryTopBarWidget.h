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
    virtual FReply NativeOnPreviewKeyDown(const FGeometry& InGeometry,
        const FKeyEvent& InKeyEvent) override;

    /** The bell toggles this alert centre's inbox. */
    void SetAlertCenter(class ULBOneFactoryAlertCenterWidget* Center)
    {
        AlertCenter = Center;
    }

private:
    void BuildTree();
    void Refresh();
    bool SetSimulationRate(float Rate);

    UFUNCTION() void OnOrdersClicked();
    UFUNCTION() void OnNewOrderClicked();
    UFUNCTION() void OnPauseClicked();
    UFUNCTION() void OnSpeed1Clicked();
    UFUNCTION() void OnSpeed2Clicked();
    UFUNCTION() void OnSpeed4Clicked();
    UFUNCTION() void OnAlertsClicked();

    UPROPERTY() TObjectPtr<UTextBlock> ContractText;
    /** v2.1 orders dropdown: the contract cell is a button; clicking it
        lists every contract with progress, time and state. */
    UPROPERTY() TObjectPtr<UButton> OrdersButton;
    /** Primary mouse-first production action for the prebuilt release demo. */
    UPROPERTY() TObjectPtr<UButton> NewOrderButton;
    UPROPERTY() TObjectPtr<class UBorder> OrdersBorder;
    UPROPERTY() TArray<TObjectPtr<UTextBlock>> OrderTexts;
    bool bOrdersOpen = false;

    /** v2.1 day summary: at each sim-day rollover a transient banner
        reports yesterday's dispatches and cash movement. */
    UPROPERTY() TObjectPtr<class UBorder> SummaryBorder;
    UPROPERTY() TObjectPtr<UTextBlock> SummaryText;
    int32 LastSimDay = -1;
    int64 DayStartCashPence = 0;
    int32 DayStartDispatched = 0;
    float SummarySecondsLeft = 0.0f;
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
    UPROPERTY() TObjectPtr<UButton> AlertButton;
    UPROPERTY()
    TObjectPtr<class ULBOneFactoryAlertCenterWidget> AlertCenter;

    float RefreshAccumulator = 0.0f;
};
