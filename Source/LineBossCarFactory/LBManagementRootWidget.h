#pragma once

#include "CoreMinimal.h"
#include "Components/Button.h"
#include "Blueprint/UserWidget.h"
#include "Input/Reply.h"
#include "UObject/SoftObjectPtr.h"
#include "LBFactoryUIStateSubsystem.h"
#include "LBManagementRootWidget.generated.h"

class UBorder;
class UButton;
class UCanvasPanel;
class UHorizontalBox;
class UImage;
class UOverlay;
class UProgressBar;
class UScaleBox;
class USizeBox;
class UTextBlock;
class UTexture2D;
class UVerticalBox;

/** Stable geometry contract used by the viewport integration and automation. */
USTRUCT(BlueprintType)
struct LINEBOSSCARFACTORY_API FLBManagementShellLayoutMetrics
{
    GENERATED_BODY()

    UPROPERTY(BlueprintReadOnly, Category="Line Boss|Management UI")
    FVector2D ViewportSize = FVector2D(1920.0f, 1080.0f);

    UPROPERTY(BlueprintReadOnly, Category="Line Boss|Management UI")
    float UIScale = 1.0f;

    UPROPERTY(BlueprintReadOnly, Category="Line Boss|Management UI")
    float TopStripHeight = 72.0f;

    UPROPERTY(BlueprintReadOnly, Category="Line Boss|Management UI")
    float FlowTrayHeight = 344.0f;

    UPROPERTY(BlueprintReadOnly, Category="Line Boss|Management UI")
    float OuterMargin = 32.0f;

    UPROPERTY(BlueprintReadOnly, Category="Line Boss|Management UI")
    float DetailWidth = 354.0f;

    UPROPERTY(BlueprintReadOnly, Category="Line Boss|Management UI")
    float FlowTrayBottomMargin = 40.0f;

    UPROPERTY(BlueprintReadOnly, Category="Line Boss|Management UI")
    float SurfaceCornerRadius = 12.0f;

    UPROPERTY(BlueprintReadOnly, Category="Line Boss|Management UI")
    bool bCompact = false;
};

/** One canonical production-flow card. Art is optional, state is never invented. */
USTRUCT(BlueprintType)
struct LINEBOSSCARFACTORY_API FLBManagementStagePresentation
{
    GENERATED_BODY()

    UPROPERTY(BlueprintReadOnly, Category="Line Boss|Management UI")
    FName StageId = NAME_None;

    UPROPERTY(BlueprintReadOnly, Category="Line Boss|Management UI")
    FText DisplayName;

    UPROPERTY(BlueprintReadOnly, Category="Line Boss|Management UI")
    TSoftObjectPtr<UTexture2D> Thumbnail;

    UPROPERTY(BlueprintReadOnly, Category="Line Boss|Management UI")
    FText StateText;

    UPROPERTY(BlueprintReadOnly, Category="Line Boss|Management UI")
    FText DetailText;

    UPROPERTY(BlueprintReadOnly, Category="Line Boss|Management UI")
    bool bInstalled = false;

    UPROPERTY(BlueprintReadOnly, Category="Line Boss|Management UI")
    bool bRunning = false;

    UPROPERTY(BlueprintReadOnly, Category="Line Boss|Management UI")
    bool bWaiting = false;

    UPROPERTY(BlueprintReadOnly, Category="Line Boss|Management UI")
    bool bFaulted = false;

    UPROPERTY(BlueprintReadOnly, Category="Line Boss|Management UI")
    bool bThumbnailAvailable = false;
};

DECLARE_DYNAMIC_MULTICAST_DELEGATE_OneParam(
    FLBManagementDestinationRequested, FName, DestinationId);
DECLARE_DYNAMIC_MULTICAST_DELEGATE_OneParam(
    FLBManagementStageActionRequested, FName, StageId);
DECLARE_DYNAMIC_MULTICAST_DELEGATE_OneParam(
    FLBManagementSimulationRateRequested, float, RequestedRate);
DECLARE_DYNAMIC_MULTICAST_DELEGATE_OneParam(
    FLBManagementContextActionRequested, int32, ActionIndex);

/** One existing gameplay action presented by the shared UMG management surface. */
USTRUCT(BlueprintType)
struct LINEBOSSCARFACTORY_API FLBManagementContextActionPresentation
{
    GENERATED_BODY()

    UPROPERTY(BlueprintReadOnly, Category="Line Boss|Management UI")
    int32 ActionIndex = INDEX_NONE;

    UPROPERTY(BlueprintReadOnly, Category="Line Boss|Management UI")
    FText Title;

    UPROPERTY(BlueprintReadOnly, Category="Line Boss|Management UI")
    FText Detail;

    UPROPERTY(BlueprintReadOnly, Category="Line Boss|Management UI")
    bool bEnabled = false;
};

/**
 * Responsive UMG management shell matching the selected Cairnwell factory-view
 * target. This widget is presentation-only: it consumes the existing factory
 * UI projection and asks the owning controller/HUD to perform actions through
 * delegates. It never owns a second simulation.
 *
 * CommonUI seam: if that plugin is enabled later, derive a Blueprint wrapper
 * from UCommonActivatableWidget and host this class as its content. All focus,
 * navigation, actions and snapshot inputs are already explicit here.
 */
UCLASS(BlueprintType, Blueprintable)
class LINEBOSSCARFACTORY_API ULBManagementRootWidget : public UUserWidget
{
    GENERATED_BODY()

public:
    static constexpr int32 ProductionStageCount = 6;
    static constexpr int32 ProductionConnectorCount = ProductionStageCount - 1;
    static constexpr int32 ManagementDestinationCount = 7;
    static constexpr float DesignFlowTrayBottomMargin = 40.0f;
    static constexpr float DesignSurfaceCornerRadius = 12.0f;
    static constexpr float DesignDetailDividerWidth = 1.0f;

    UPROPERTY(BlueprintAssignable, Category="Line Boss|Management UI|Events")
    FLBManagementDestinationRequested OnDestinationRequested;

    UPROPERTY(BlueprintAssignable, Category="Line Boss|Management UI|Events")
    FLBManagementStageActionRequested OnStageActionRequested;

    /** Selection is separate from activation so a card click never starts placement. */
    UPROPERTY(BlueprintAssignable, Category="Line Boss|Management UI|Events")
    FLBManagementStageActionRequested OnStageSelectionChanged;

    UPROPERTY(BlueprintAssignable, Category="Line Boss|Management UI|Events")
    FLBManagementSimulationRateRequested OnSimulationRateRequested;

    /** The HUD keeps gameplay authority; this delegate only requests an existing action. */
    UPROPERTY(BlueprintAssignable, Category="Line Boss|Management UI|Events")
    FLBManagementContextActionRequested OnContextActionRequested;

    /** Builds a truthful presentation from a supplied UI-state projection. */
    void ApplyFactorySnapshot(const FLBFactoryUIStateSnapshot& Snapshot);

    /** Pulls the current world subsystem projection and refreshes the shell. */
    UFUNCTION(BlueprintCallable, Category="Line Boss|Management UI")
    void RefreshFromFactoryState(bool bForceRefresh = false);

    /** Reuses the modern surface for Build, Orders, Assets, Maintenance, Research and Analytics. */
    void SetManagementContext(FName PageId, const FString& Heading,
        const FString& Summary,
        const TArray<FLBManagementContextActionPresentation>& Actions);

    UFUNCTION(BlueprintCallable, Category="Line Boss|Management UI")
    void SelectProductionStage(int32 StageIndex, bool bMoveKeyboardFocus = false);

    UFUNCTION(BlueprintCallable, Category="Line Boss|Management UI")
    void SelectRelativeProductionStage(int32 Direction, bool bMoveKeyboardFocus = true);

    UFUNCTION(BlueprintCallable, Category="Line Boss|Management UI")
    void ActivateSelectedStage();

    /** Rechecks strict v003 soft references after a UI art import completes. */
    UFUNCTION(BlueprintCallable, Category="Line Boss|Management UI")
    void ReloadStageThumbnails();

    UFUNCTION(BlueprintPure, Category="Line Boss|Management UI")
    int32 GetSelectedProductionStage() const { return SelectedStageIndex; }

    UFUNCTION(BlueprintPure, Category="Line Boss|Management UI")
    const TArray<FLBManagementStagePresentation>& GetPresentedStages() const
    {
        return PresentedStages;
    }

    UFUNCTION(BlueprintPure, Category="Line Boss|Management UI")
    bool HasCompleteThumbnailSet() const;

    /** True only when the authored design tree has a live Slate counterpart. */
    bool HasRenderableShell() const;

    UFUNCTION(BlueprintPure, Category="Line Boss|Management UI")
    static FLBManagementShellLayoutMetrics CalculateLayoutMetrics(
        FVector2D ViewportSize);

    UFUNCTION(BlueprintPure, Category="Line Boss|Management UI")
    static TArray<FName> GetCanonicalProductionStageIds();

    UFUNCTION(BlueprintPure, Category="Line Boss|Management UI")
    static TArray<FName> GetCanonicalManagementDestinationIds();

    UFUNCTION(BlueprintPure, Category="Line Boss|Management UI")
    static FSoftObjectPath GetStageThumbnailPath(FName StageId);

    UFUNCTION(BlueprintPure, Category="Line Boss|Management UI")
    static FSoftObjectPath GetBrandLogoPath();

    /** A dot is status telemetry, so it is absent until the process exists. */
    UFUNCTION(BlueprintPure, Category="Line Boss|Management UI")
    static bool ShouldShowStageStatusDot(
        const FLBManagementStagePresentation& Stage);

    /** A highlighted connector means both adjacent process assets really exist. */
    UFUNCTION(BlueprintPure, Category="Line Boss|Management UI")
    static bool ShouldHighlightStageConnector(
        const FLBManagementStagePresentation& Upstream,
        const FLBManagementStagePresentation& Downstream);

    /** Zero is not presented as throughput: it is indistinguishable from no sample. */
    UFUNCTION(BlueprintPure, Category="Line Boss|Management UI")
    static bool HasTruthfulThroughput(double GoodUnitsPerHour);

    /** Inputs owned by the factory camera/simulation, never by HUD navigation. */
    static bool IsReservedGameplayKey(const FKey& Key);

protected:
    virtual TSharedRef<SWidget> RebuildWidget() override;
    virtual void NativeOnInitialized() override;
    virtual void NativeConstruct() override;
    virtual void NativeTick(const FGeometry& MyGeometry,
        float InDeltaTime) override;
    virtual FReply NativeOnKeyDown(const FGeometry& InGeometry,
        const FKeyEvent& InKeyEvent) override;

private:
    UPROPERTY(Transient)
    TArray<FLBManagementStagePresentation> PresentedStages;

    UPROPERTY(Transient)
    TArray<TObjectPtr<UButton>> StageButtons;

    UPROPERTY(Transient)
    TArray<TObjectPtr<UBorder>> StageCardBorders;

    UPROPERTY(Transient)
    TArray<TObjectPtr<UBorder>> StageStatusDots;

    UPROPERTY(Transient)
    TArray<TObjectPtr<UBorder>> StageConnectorLines;

    UPROPERTY(Transient)
    TArray<TObjectPtr<UImage>> StageImages;

    UPROPERTY(Transient)
    TArray<TObjectPtr<UTextBlock>> StageStateLabels;

    UPROPERTY(Transient)
    TArray<TObjectPtr<UTextBlock>> StageArtStatusLabels;

    UPROPERTY(Transient)
    TObjectPtr<UCanvasPanel> RootCanvas;

    /** Scales the exact 1920 x 1080 design canvas uniformly into the live viewport. */
    UPROPERTY(Transient)
    TObjectPtr<UScaleBox> ShellScaleBox;

    UPROPERTY(Transient)
    TObjectPtr<UCanvasPanel> DesignCanvas;

    UPROPERTY(Transient)
    TObjectPtr<USizeBox> TopStripSizeBox;

    UPROPERTY(Transient)
    TObjectPtr<USizeBox> FlowTraySizeBox;

    UPROPERTY(Transient)
    TObjectPtr<UBorder> FlowTrayBorder;

    UPROPERTY(Transient)
    TObjectPtr<UHorizontalBox> StageRow;

    UPROPERTY(Transient)
    TObjectPtr<UBorder> DetailBorder;

    UPROPERTY(Transient)
    TObjectPtr<UTextBlock> FactoryNameLabel;

    UPROPERTY(Transient)
    TObjectPtr<UImage> BrandLogoImage;

    UPROPERTY(Transient)
    TObjectPtr<UTextBlock> OrderLabel;

    UPROPERTY(Transient)
    TObjectPtr<UTextBlock> CashLabel;

    UPROPERTY(Transient)
    TObjectPtr<UTextBlock> AlertLabel;

    /** Pointer/controller-reachable management destinations in visual order. */
    UPROPERTY(Transient)
    TArray<TObjectPtr<UButton>> TopDestinationButtons;

    /** Pause, play and fast-forward controls in visual order. */
    UPROPERTY(Transient)
    TArray<TObjectPtr<UButton>> SimulationRateButtons;

    UPROPERTY(Transient)
    TObjectPtr<UTextBlock> DetailTitleLabel;

    UPROPERTY(Transient)
    TObjectPtr<UTextBlock> DetailStateLabel;

    UPROPERTY(Transient)
    TObjectPtr<UTextBlock> DetailDescriptionLabel;

    UPROPERTY(Transient)
    TObjectPtr<UTextBlock> DetailOrderLabel;

    UPROPERTY(Transient)
    TObjectPtr<UTextBlock> DetailThroughputLabel;

    UPROPERTY(Transient)
    TObjectPtr<UProgressBar> DetailOrderProgress;

    UPROPERTY(Transient)
    TObjectPtr<UButton> PrimaryActionButton;

    UPROPERTY(Transient)
    TObjectPtr<UTextBlock> PrimaryActionLabel;

    UPROPERTY(Transient)
    TObjectPtr<UTextBlock> FlowTitleLabel;

    UPROPERTY(Transient)
    TObjectPtr<UBorder> ContextBorder;

    UPROPERTY(Transient)
    TObjectPtr<UTextBlock> ContextTitleLabel;

    UPROPERTY(Transient)
    TObjectPtr<UTextBlock> ContextSummaryLabel;

    UPROPERTY(Transient)
    TArray<TObjectPtr<UButton>> ContextActionButtons;

    UPROPERTY(Transient)
    TArray<TObjectPtr<UTextBlock>> ContextActionTitles;

    UPROPERTY(Transient)
    TArray<TObjectPtr<UTextBlock>> ContextActionDetails;

    TArray<int32> ContextActionIndices;

    int32 SelectedStageIndex = 2;
    float RefreshAccumulator = 0.0f;
    static constexpr float RefreshPeriodSeconds = 0.25f;
    FVector2D LastViewportSize = FVector2D::ZeroVector;
    FLBFactoryUIStateSnapshot LastSnapshot;

    void BuildShell();
    void BuildTopCommandStrip(UCanvasPanel* Canvas);
    void BuildProductionFlow(UCanvasPanel* Canvas);
    void BuildManagementContext(UCanvasPanel* Canvas);
    void BuildStageCard(int32 StageIndex, UHorizontalBox* Row);
    void BuildStageConnector(int32 UpstreamStageIndex, UHorizontalBox* Row);
    void BuildDetailPanel(UHorizontalBox* TrayContent);
    void BuildCanonicalPresentations();
    void UpdateResponsiveLayout(FVector2D ViewportSize);
    void RefreshPresentation();
    void RefreshStageCard(int32 StageIndex);
    void RefreshStageConnector(int32 UpstreamStageIndex);
    void ResolveThumbnail(int32 StageIndex, bool bForceSynchronousLoad);
    void RefreshDetailPanel();
    void ConfigureFocusNavigation();
    void RequestDestination(FName DestinationId);
    void RequestSimulationRate(float Rate);
    void HandleStageClicked(int32 StageIndex);

    UFUNCTION() void OnStage0Clicked();
    UFUNCTION() void OnStage1Clicked();
    UFUNCTION() void OnStage2Clicked();
    UFUNCTION() void OnStage3Clicked();
    UFUNCTION() void OnStage4Clicked();
    UFUNCTION() void OnStage5Clicked();
    UFUNCTION() void OnPrimaryActionClicked();
    UFUNCTION() void OnFactoryDestinationClicked();
    UFUNCTION() void OnBuildDestinationClicked();
    UFUNCTION() void OnOrdersDestinationClicked();
    UFUNCTION() void OnAssetsDestinationClicked();
    UFUNCTION() void OnMaintenanceDestinationClicked();
    UFUNCTION() void OnResearchDestinationClicked();
    UFUNCTION() void OnAnalyticsDestinationClicked();
    UFUNCTION() void OnSettingsDestinationClicked();
    UFUNCTION() void OnPauseClicked();
    UFUNCTION() void OnPlayClicked();
    UFUNCTION() void OnFastForwardClicked();
    UFUNCTION() void OnContextAction0Clicked();
    UFUNCTION() void OnContextAction1Clicked();
    UFUNCTION() void OnContextAction2Clicked();
    UFUNCTION() void OnContextAction3Clicked();
    UFUNCTION() void OnContextAction4Clicked();
};
