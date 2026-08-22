#pragma once

#include "Blueprint/UserWidget.h"
#include "CoreMinimal.h"
#include "LBOneFactoryProductionHUD.h"
#include "Styling/SlateTypes.h"
#include "LBOneFactoryFlowStripWidget.generated.h"

class UBorder;
class UButton;
class UHorizontalBox;
class UProgressBar;
class UTextBlock;

/**
 * UI v2 flow strip (U3): one clickable card per coarse process group along
 * the bottom edge. Each card shows the group's status (colour + shape),
 * occupancy, mean cycle progress and rate; clicking a card frames that part
 * of the plant with the management camera. All data comes from
 * ALBOneFactoryProductionHUD::CollectGroups - nothing here is invented.
 */
UCLASS()
class LINEBOSSCARFACTORY_API ULBOneFactoryFlowStripWidget : public UUserWidget
{
    GENERATED_BODY()

public:
    virtual TSharedRef<SWidget> RebuildWidget() override;
    virtual void NativeConstruct() override;
    virtual void NativeTick(const FGeometry& MyGeometry,
        float InDeltaTime) override;
    virtual FReply NativeOnPreviewKeyDown(const FGeometry& InGeometry,
        const FKeyEvent& InKeyEvent) override;

    /** Drives the same path as a real card click; dev tooling and tests
        use it to prove the click-to-frame flow end to end. */
    bool SimulateCardClick(const int32 Index) { return FocusGroup(Index); }

    /** A card click also opens the detail panel, when one is wired. */
    void SetDetailPanel(class ULBOneFactoryDetailPanelWidget* Panel)
    {
        DetailPanel = Panel;
    }

    /** A card click closes the alert inbox - the panels share the rail. */
    void SetAlertCenter(class ULBOneFactoryAlertCenterWidget* Center)
    {
        AlertCenter = Center;
    }

    /**
     * Creates the first-session coaching line from live factory data.  This
     * stays public so the player-facing priority rule can be regression
     * tested without a viewport: an actionable alert beats a capacity
     * bottleneck, and neither is fabricated.
     */
    static FText BuildFirstSessionHint(
        const TArray<FLBOneFactoryProcessGroup>& Groups,
        const TArray<FLBOneFactoryLiveAlert>& Alerts,
        int32 BottleneckIndex);

private:
    /** The route is seven coarse groups; the handler table matches. */
    static constexpr int32 MaxCards = 7;

    void BuildTree();
    void EnsureCards(int32 Count);
    void Refresh();
    bool FocusGroup(int32 Index);

    UFUNCTION() void OnCard0Clicked();
    UFUNCTION() void OnCard1Clicked();
    UFUNCTION() void OnCard2Clicked();
    UFUNCTION() void OnCard3Clicked();
    UFUNCTION() void OnCard4Clicked();
    UFUNCTION() void OnCard5Clicked();
    UFUNCTION() void OnCard6Clicked();

    UPROPERTY() TObjectPtr<UBorder> StripBorder;
    UPROPERTY() TObjectPtr<UBorder> HintBorder;
    UPROPERTY() TObjectPtr<UTextBlock> HintText;
    UPROPERTY() TObjectPtr<UHorizontalBox> CardsRow;
    UPROPERTY() TObjectPtr<UTextBlock> SummaryText;
    UPROPERTY() TArray<TObjectPtr<UButton>> CardButtons;
    UPROPERTY() TArray<TObjectPtr<UTextBlock>> CardNames;
    UPROPERTY() TArray<TObjectPtr<UTextBlock>> CardCounts;
    UPROPERTY() TArray<TObjectPtr<UProgressBar>> CardProgress;
    UPROPERTY() TArray<TObjectPtr<UTextBlock>> CardStatus;
    UPROPERTY() TArray<TObjectPtr<UTextBlock>> CardRate;

    /** Rounded card faces; the selected card carries the emerald outline
        (target mockup, 2026-08-20). */
    FButtonStyle CardStyle;
    FButtonStyle SelectedCardStyle;

    /** Last collected groups, kept so clicks know where to fly. */
    TArray<FLBOneFactoryProcessGroup> CachedGroups;

    UPROPERTY()
    TObjectPtr<class ULBOneFactoryDetailPanelWidget> DetailPanel;
    UPROPERTY()
    TObjectPtr<class ULBOneFactoryAlertCenterWidget> AlertCenter;

    float RefreshAccumulator = 0.0f;
};
