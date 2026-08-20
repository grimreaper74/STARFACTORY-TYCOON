#pragma once

#include "Blueprint/UserWidget.h"
#include "CoreMinimal.h"
#include "LBOneFactoryProductionHUD.h"
#include "LBOneFactoryAlertCenterWidget.generated.h"

class UBorder;
class UButton;
class UTextBlock;
class UVerticalBox;

/**
 * UI v2 alert centre (U5): the bell's inbox plus the world toast, both fed
 * by the same live alert list the cards use (one status model). Alerts are
 * stateful - they regenerate from the ledger, so a resolved hold vanishes
 * without an acknowledge step. Toast-severity alerts also surface as a
 * banner under the top bar while the inbox stays closed; clicking an inbox
 * row navigates to the group that raised it.
 */
UCLASS()
class LINEBOSSCARFACTORY_API ULBOneFactoryAlertCenterWidget
    : public UUserWidget
{
    GENERATED_BODY()

public:
    virtual TSharedRef<SWidget> RebuildWidget() override;
    virtual void NativeConstruct() override;
    virtual void NativeTick(const FGeometry& MyGeometry,
        float InDeltaTime) override;

    void ToggleInbox();
    void HideInbox();
    bool IsInboxOpen() const { return bInboxOpen; }

    /** Row clicks navigate through the flow strip's click path. */
    void SetFlowStrip(class ULBOneFactoryFlowStripWidget* Strip)
    {
        FlowStrip = Strip;
    }

    /** The inbox and the detail panel share the right rail; opening the
        inbox closes the panel. */
    void SetDetailPanel(class ULBOneFactoryDetailPanelWidget* Panel)
    {
        DetailPanel = Panel;
    }

private:
    static constexpr int32 MaxRows = 8;

    void BuildTree();
    void Refresh();
    void NavigateRow(int32 RowIndex);

    UFUNCTION() void OnRow0Clicked();
    UFUNCTION() void OnRow1Clicked();
    UFUNCTION() void OnRow2Clicked();
    UFUNCTION() void OnRow3Clicked();
    UFUNCTION() void OnRow4Clicked();
    UFUNCTION() void OnRow5Clicked();
    UFUNCTION() void OnRow6Clicked();
    UFUNCTION() void OnRow7Clicked();

    UPROPERTY() TObjectPtr<UBorder> ToastBorder;
    UPROPERTY() TObjectPtr<UTextBlock> ToastText;
    UPROPERTY() TObjectPtr<UBorder> InboxBorder;
    UPROPERTY() TObjectPtr<UTextBlock> InboxTitle;
    UPROPERTY() TObjectPtr<UTextBlock> EmptyText;
    UPROPERTY() TArray<TObjectPtr<UButton>> RowButtons;
    UPROPERTY() TArray<TObjectPtr<UTextBlock>> RowTexts;
    UPROPERTY() TObjectPtr<class ULBOneFactoryFlowStripWidget> FlowStrip;
    UPROPERTY()
    TObjectPtr<class ULBOneFactoryDetailPanelWidget> DetailPanel;

    /** Group index per visible row, so clicks know where to go. */
    TArray<int32> RowGroupIndices;

    /** One resolved alert kept for the inbox's RECENT section: live
        alerts vanish the moment their condition clears, so the inbox
        remembers what cleared and when (v2.1). */
    struct FLBOneFactoryAlertHistoryEntry
    {
        FText Message;
        ELBOneFactoryStationStatus Status =
            ELBOneFactoryStationStatus::Working;
        double SimClockSeconds = 0.0;
    };
    static constexpr int32 MaxHistory = 6;

    /** Diffs the live alert list against the previous refresh and moves
        anything that disappeared into History with the sim clock. */
    void CaptureHistory(bool bCollected,
        const TArray<FLBOneFactoryLiveAlert>& Alerts);

    TArray<FLBOneFactoryAlertHistoryEntry> History;
    TArray<FLBOneFactoryLiveAlert> PrevAlerts;
    UPROPERTY() TObjectPtr<UTextBlock> HistoryHeader;
    UPROPERTY() TArray<TObjectPtr<UTextBlock>> HistoryTexts;

    bool bInboxOpen = false;
    float RefreshAccumulator = 0.0f;
};
