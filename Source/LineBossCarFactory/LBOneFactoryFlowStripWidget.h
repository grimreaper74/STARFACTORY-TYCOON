#pragma once

#include "Blueprint/UserWidget.h"
#include "CoreMinimal.h"
#include "LBOneFactoryProductionHUD.h"
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

    /** Drives the same path as a real card click; dev tooling and tests
        use it to prove the click-to-frame flow end to end. */
    bool SimulateCardClick(const int32 Index) { return FocusGroup(Index); }

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
    UPROPERTY() TObjectPtr<UHorizontalBox> CardsRow;
    UPROPERTY() TObjectPtr<UTextBlock> SummaryText;
    UPROPERTY() TArray<TObjectPtr<UButton>> CardButtons;
    UPROPERTY() TArray<TObjectPtr<UTextBlock>> CardNames;
    UPROPERTY() TArray<TObjectPtr<UTextBlock>> CardMeta;
    UPROPERTY() TArray<TObjectPtr<UProgressBar>> CardProgress;
    UPROPERTY() TArray<TObjectPtr<UTextBlock>> CardStatus;
    UPROPERTY() TArray<TObjectPtr<UTextBlock>> CardRate;

    /** Last collected groups, kept so clicks know where to fly. */
    TArray<FLBOneFactoryProcessGroup> CachedGroups;

    float RefreshAccumulator = 0.0f;
};
