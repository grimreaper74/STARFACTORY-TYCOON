#pragma once

#include "CoreMinimal.h"
#include "GameFramework/HUD.h"
#include "LBControlRoomHUD.generated.h"

class UTextureRenderTarget2D;
class ULBManagementRootWidget;
class ULBSettingsRootWidget;
class ALBControlRoomOperationsConsole;
class ALBPlayerBuiltPressFlowController;
class ALBPressShopCampaignController;
struct FKey;

/**
 * One resolution-aware contract shared by Canvas drawing, hit testing and HUD
 * automation. Values are authored against a 1280 x 720 reference canvas and
 * grow with the render canvas so high-DPI PIE does not downsample the HUD into
 * illegibility. Interactive rows retain a 44 px reference-height minimum.
 */
struct LINEBOSSCARFACTORY_API FLBHUDReadabilityContract
{
    bool bCompactMode = false;
    float LayoutScale = 1.0f;
    float NormalTextScale = 1.34f;
    float DetailTextScale = 1.16f;
    float HeadingTextScale = 0.92f;
    float ExpectedNormalTextPixelHeight = 16.0f;
    float ExpectedDetailTextPixelHeight = 14.0f;
    float ExpectedHeadingTextPixelHeight = 24.0f;
    float MinimumInteractiveHeight = 44.0f;
    float PersistentHUDHeight = 65.0f;
    FBox2D PersistentBounds = FBox2D(ForceInit);
    FBox2D ManagementBounds = FBox2D(ForceInit);
    FBox2D FactoryBuildBounds = FBox2D(ForceInit);
    FBox2D FactoryBrandBounds = FBox2D(ForceInit);
};

/** Exact responsive geometry for the selected modern production-flow HUD. */
struct LINEBOSSCARFACTORY_API FLBProductionFlowHUDLayout
{
    FBox2D TopBarBounds = FBox2D(ForceInit);
    FBox2D FlowCanvasBounds = FBox2D(ForceInit);
    FBox2D StageLaneBounds = FBox2D(ForceInit);
    FBox2D DetailBounds = FBox2D(ForceInit);
    FBox2D PrimaryActionBounds = FBox2D(ForceInit);
    TArray<FBox2D> StageCardBounds;
};

/**
 * Truthful, source-derived facts shown before a player commits to a factory asset.
 * ThumbnailAsset is deliberately optional: authored icons can be supplied later without
 * changing catalogue identity or input mapping; PreviewKind drives today's Canvas silhouette.
 */
USTRUCT(BlueprintType)
struct LINEBOSSCARFACTORY_API FLBFactoryCatalogueDecisionFacts
{
    GENERATED_BODY()

    UPROPERTY(BlueprintReadOnly) FString DisplayName;
    UPROPERTY(BlueprintReadOnly) FString ProcessStage;
    UPROPERTY(BlueprintReadOnly) FString Purpose;
    UPROPERTY(BlueprintReadOnly) FString InputFlow;
    UPROPERTY(BlueprintReadOnly) FString OutputFlow;
    UPROPERTY(BlueprintReadOnly) FString FootprintAndServiceEnvelope;
    UPROPERTY(BlueprintReadOnly) FString RouteAndClearance;
    UPROPERTY(BlueprintReadOnly) FString LockReason;
    UPROPERTY(BlueprintReadOnly) FString PreviewKind;
    UPROPERTY(BlueprintReadOnly) FSoftObjectPath ThumbnailAsset;
    UPROPERTY(BlueprintReadOnly) bool bLocked = false;
};

UENUM(BlueprintType)
enum class ELBManagementPage : uint8
{
    Overview = 0,
    /** Ordinal 1 retained for saved Blueprint/input compatibility; player label is Build. */
    FactoryBuild = 1,
    /** Ordinal 2 retained; player label is Orders. */
    Production = 2,
    /** Ordinal 3 retained; player label is Assets. */
    PressTrains = 3,
    /** Ordinal 4 retained; player label is Maintenance. */
    SupportFleet = 4,
    Research = 5,
    Analytics = 6,
    PageCount = 7 UMETA(Hidden)
};

/** Selected-feed HUD for the seated Moorcross Works control room. */
UCLASS()
class LINEBOSSCARFACTORY_API ALBControlRoomHUD : public AHUD
{
    GENERATED_BODY()

public:
    virtual void BeginPlay() override;
    virtual void EndPlay(const EEndPlayReason::Type EndPlayReason) override;
    virtual void DrawHUD() override;

    UFUNCTION(BlueprintCallable, Category = "Cairnwell|Control Room|CCTV")
    void ShowCCTVFeed(UTextureRenderTarget2D* InFeed);

    UFUNCTION(BlueprintCallable, Category = "Cairnwell|Control Room|CCTV")
    void HideCCTVFeed();

    UFUNCTION(BlueprintPure, Category = "Cairnwell|Control Room|CCTV")
    bool IsCCTVFeedVisible() const { return bCCTVFeedVisible && Feed.IsValid(); }

    UFUNCTION(BlueprintCallable, Category = "Cairnwell|Management") void ToggleManagement();
    /** Opens the player-build catalogue directly. This path never requires a control-room console. */
    UFUNCTION(BlueprintCallable, Category = "Cairnwell|Management") void OpenFactoryBuild();
    /** Opens an exact management page for local developer automation and accessible direct navigation. */
    UFUNCTION(BlueprintCallable, Category = "Cairnwell|Management") void OpenManagementPage(ELBManagementPage Page);
    UFUNCTION(BlueprintCallable, Category = "Cairnwell|Management") void CloseManagement();
    UFUNCTION(BlueprintCallable, Category = "Cairnwell|Management") void NextManagementPage();
    UFUNCTION(BlueprintCallable, Category = "Cairnwell|Management") void PreviousManagementPage();
    UFUNCTION(BlueprintCallable, Category = "Cairnwell|Management") void NextManagementAction();
    UFUNCTION(BlueprintCallable, Category = "Cairnwell|Management") void PreviousManagementAction();
    UFUNCTION(BlueprintCallable, Category = "Cairnwell|Management") bool ConfirmManagementAction();
    /** Compatibility input seam; live management pointer input is routed by UMG. */
    UFUNCTION(BlueprintCallable, Category = "Cairnwell|Management") bool HandleManagementClick(float ScreenX, float ScreenY);
    /** Viewport-explicit management hit testing shared by live mouse input and automation. */
    bool HandleManagementClickForViewport(float ScreenX, float ScreenY,
        float ViewWidth, float ViewHeight);
    /** Viewport-explicit profile hit testing shared by live mouse input and focused automation. */
    bool HandleFactoryBrandEditorClick(float ScreenX, float ScreenY, float ViewWidth, float ViewHeight);
    /** Centres generated from the same responsive rectangles used for drawing and mouse input. */
    bool GetManagementTabHitTarget(ELBManagementPage Page, float ViewWidth,
        float ViewHeight, FVector2D& OutScreenPosition) const;
    bool GetManagementActionHitTarget(int32 ActionIndex, float ViewWidth,
        float ViewHeight, FVector2D& OutScreenPosition) const;
    UFUNCTION(BlueprintCallable, Category = "Cairnwell|Management") bool ActivateManagementAction(int32 ActionIndex);
    UFUNCTION(BlueprintPure, Category = "Cairnwell|Management") bool IsManagementVisible() const { return bManagementVisible; }
    UFUNCTION(BlueprintPure, Category = "Cairnwell|Management") ELBManagementPage GetManagementPage() const { return ManagementPage; }
    UFUNCTION(BlueprintPure, Category = "Cairnwell|Management") int32 GetSelectedManagementAction() const { return SelectedManagementAction; }
    /** Pure state policy for the UMG Overview; independent of viewport availability. */
    bool IsModernOverviewActive() const;
    /** UMG owns every management page and all player-facing HUD surfaces. */
    bool IsModernManagementActive() const;
    /** Routes one canonical top-strip destination through the existing page authority. */
    bool HandleModernManagementDestination(FName DestinationId);
    /** Routes one canonical stage action through the existing focus/build authority. */
    bool HandleModernProductionStageAction(FName StageId);
    UFUNCTION(BlueprintPure, Category = "Cairnwell|Management") int32 GetManagementActionCount() const;
    /** Stable model identity used by the console-free production-order editor. */
    UFUNCTION(BlueprintPure, Category = "Cairnwell|Management") FName GetSelectedVehicleModelId() const;
    /** Player-facing programme label; it deliberately does not imply a final production BOM. */
    UFUNCTION(BlueprintPure, Category = "Cairnwell|Management") FString GetSelectedVehicleDisplayName() const;
    /** Number of machine catalogue cards currently visible, including the disabled ED-line milestone. */
    UFUNCTION(BlueprintPure, Category = "Cairnwell|Management") int32 GetVisibleFactoryMachineCardCount() const;
    /** True only for the visible, progression-locked ED-line milestone card. */
    UFUNCTION(BlueprintPure, Category = "Cairnwell|Management") bool IsFactoryMachineCardLocked(int32 CardIndex) const;
    /** Resolves a visible machine card to its stable keyboard/controller action, or INDEX_NONE while locked. */
    UFUNCTION(BlueprintPure, Category = "Cairnwell|Management") int32 GetFactoryMachineCardActionIndex(int32 CardIndex) const;
    /** Activates a visible machine card through the same action authority as keyboard/controller confirm. */
    UFUNCTION(BlueprintCallable, Category = "Cairnwell|Management") bool ActivateFactoryMachineCard(int32 CardIndex);
    /** Current five-card catalogue page; paging never changes the stable action index. */
    UFUNCTION(BlueprintPure, Category = "Cairnwell|Management") int32 GetFactoryCataloguePage() const { return FactoryCataloguePage; }
    UFUNCTION(BlueprintPure, Category = "Cairnwell|Management") int32 GetFactoryCataloguePageCount() const;
    UFUNCTION(BlueprintCallable, Category = "Cairnwell|Management") void NextFactoryCataloguePage();
    UFUNCTION(BlueprintCallable, Category = "Cairnwell|Management") void PreviousFactoryCataloguePage();
    /** Filter tab shared by mouse/controller-accessible catalogue navigation and automation. */
    UFUNCTION(BlueprintCallable, Category = "Cairnwell|Management") bool SelectFactoryBuildCategory(int32 CategoryIndex);
    /** Decision facts and optional future thumbnail path for a visible machine card. */
    UFUNCTION(BlueprintPure, Category = "Cairnwell|Management")
    bool GetFactoryMachineCardDecisionFacts(int32 CardIndex,
        FLBFactoryCatalogueDecisionFacts& OutFacts) const;
    /** Exact visible-card geometry used by drawing, mouse input and safe-area automation. */
    bool GetFactoryCatalogueCardHitRect(int32 CardIndex, float ViewWidth,
        float ViewHeight, FBox2D& OutScreenRect) const;
    bool GetFactoryCataloguePageButtonHitRect(bool bNext, float ViewWidth,
        float ViewHeight, FBox2D& OutScreenRect) const;
    UFUNCTION(BlueprintPure, Category = "Cairnwell|Management") bool HasOperationsAuthority() const { return FindOperationsConsole() != nullptr; }
    /** Chooses light or dark HUD ink for the strongest contrast against a solid fill. */
    static FLinearColor ChooseReadableTextColour(const FLinearColor& Background);
    /** Public audit surface for the exact 720p/1080p text, target and panel contract. */
    static FLBHUDReadabilityContract GetReadabilityContract(float ViewWidth, float ViewHeight);
    static FLBProductionFlowHUDLayout GetProductionFlowLayout(float ViewWidth, float ViewHeight);
    /** Stable 0..5 stage selection used by mouse/controller and the detail card. */
    int32 GetSelectedProductionFlowStage() const { return SelectedProductionFlowStage; }
    bool GetProductionFlowStageHitRect(int32 StageIndex, float ViewWidth,
        float ViewHeight, FBox2D& OutScreenRect) const;
    bool GetProductionFlowPrimaryActionHitRect(float ViewWidth, float ViewHeight,
        FBox2D& OutScreenRect) const;
    /** Legacy geometry contract retained for non-visual automation compatibility. */
    bool GetManagementTabHitRect(ELBManagementPage Page, float ViewWidth,
        float ViewHeight, FBox2D& OutScreenRect) const;
    bool GetManagementActionHitRect(int32 ActionIndex, float ViewWidth,
        float ViewHeight, FBox2D& OutScreenRect) const;
    bool GetFactoryBrandControlHitRect(int32 ControlIndex, float ViewWidth,
        float ViewHeight, FBox2D& OutScreenRect) const;
    /** Last explicit save/load result shown on Analytics; no autosave is implied. */
    FString GetCampaignPersistenceFeedback() const { return CampaignPersistenceFeedback; }
    bool IsCampaignLoadConfirmationArmed() const { return bCampaignLoadConfirmationArmed; }
    /** Explicit settings entry point for the optional company name and machine livery editor. */
    UFUNCTION(BlueprintCallable, Category = "Line Boss|Settings|Appearance") void OpenFactoryAppearanceSettings();
    /** Opens the native graphics/display settings overlay without changing the current management page. */
    UFUNCTION(BlueprintCallable, Category = "Line Boss|Settings") void OpenSettings();
    UFUNCTION(BlueprintCallable, Category = "Line Boss|Settings") void CloseSettings();
    UFUNCTION(BlueprintPure, Category = "Line Boss|Settings") bool IsSettingsVisible() const { return bSettingsVisible; }
    /** Compatibility alias for existing Blueprint and automation callers. */
    UFUNCTION(BlueprintCallable, Category = "Line Boss|Factory Brand",
        meta=(DeprecatedFunction, DeprecationMessage="Use OpenFactoryAppearanceSettings."))
    void OpenFactoryProfile();
    /** True whenever the profile editor owns input above the ordinary management UI. */
    UFUNCTION(BlueprintPure, Category = "Line Boss|Factory Brand") bool IsFactoryBrandEditorVisible() const { return bBrandEditorVisible; }
    /** Legacy query retained for callers; factory appearance no longer blocks startup. */
    UFUNCTION(BlueprintPure, Category = "Line Boss|Factory Brand") bool IsMandatoryFactorySetupActive() const;
    /** True while ordinary keyboard presses are being captured as the player's factory name. */
    UFUNCTION(BlueprintPure, Category = "Line Boss|Factory Brand") bool IsBrandingNameEditActive() const { return bBrandEditorVisible && bEditingFactoryName; }
    /** Text-entry/virtual-keyboard authority; committing still occurs only through Continue/Save. */
    UFUNCTION(BlueprintCallable, Category = "Line Boss|Factory Brand") void SetFactoryNameDraft(const FString& NewName);
    /** Mouse/controller swatches share this exact draft-selection path. */
    UFUNCTION(BlueprintCallable, Category = "Line Boss|Factory Brand") bool SelectFactoryLiverySwatch(bool bPrimary, int32 SwatchIndex);
    /** Applies the optional factory name and both machine-livery colours. */
    UFUNCTION(BlueprintCallable, Category = "Line Boss|Factory Brand") bool SubmitFactoryBrandEditor();
    UFUNCTION(BlueprintPure, Category = "Line Boss|Factory Brand") FString GetFactoryBrandValidationReason() const { return FactoryBrandValidationReason; }
    UFUNCTION(BlueprintPure, Category = "Line Boss|Factory Brand") FString GetFactoryNameDraft() const { return FactoryNameEditBuffer; }
    UFUNCTION(BlueprintPure, Category = "Line Boss|Factory Brand") FLinearColor GetDraftPrimaryMachineColour() const { return DraftPrimaryMachineColour; }
    UFUNCTION(BlueprintPure, Category = "Line Boss|Factory Brand") FLinearColor GetDraftSecondaryMachineColour() const { return DraftSecondaryMachineColour; }
    UFUNCTION(BlueprintPure, Category = "Line Boss|Factory Brand") int32 GetSelectedBrandEditorControl() const { return SelectedBrandEditorControl; }
    bool HandleBrandingKey(const FKey& Key);

private:
    UPROPERTY(Transient)
    TObjectPtr<ULBManagementRootWidget> ManagementRootWidget;

    UPROPERTY(Transient)
    TObjectPtr<ULBSettingsRootWidget> SettingsRootWidget;

    UPROPERTY(Transient)
    TWeakObjectPtr<UTextureRenderTarget2D> Feed;

    bool bCCTVFeedVisible = false;
    bool bManagementVisible = false;
    bool bSettingsVisible = false;
    bool bManagementWasVisibleBeforeSettings = false;
    ELBManagementPage ManagementPage = ELBManagementPage::Overview;
    int32 SelectedManagementAction = 0;
    /** 0 machines, 1 storage, 2 logistics, 3 safety. */
    int32 SelectedBuildCategory = 0;
    /** Presentation-only page. Action indices remain absolute and save/input compatible. */
    int32 FactoryCataloguePage = 0;
    int32 SelectedVehicleModel = 0;
    int32 SelectedPanelType = 0;
    int32 PlayerBatchQuantity = 10;
    int32 SelectedProductionFlowStage = 2;
    bool bBrandEditorVisible = false;
    bool bEditingFactoryName = false;
    FString FactoryNameEditBuffer;
    FLinearColor DraftPrimaryMachineColour = FLinearColor(0.035f, 0.36f, 0.16f, 1.0f);
    FLinearColor DraftSecondaryMachineColour = FLinearColor(0.055f, 0.07f, 0.075f, 1.0f);
    FString FactoryBrandValidationReason;
    FString CampaignPersistenceFeedback = TEXT("NO MANUAL SAVE OR LOAD THIS SESSION");
    bool bCampaignPersistenceSucceeded = true;
    bool bCampaignPersistenceAttempted = false;
    bool bCampaignLoadConfirmationArmed = false;
    /** 0 name, 1 primary, 2 secondary, 3 continue/save. */
    int32 SelectedBrandEditorControl = 0;
    int32 SelectedPrimarySwatch = 0;
    int32 SelectedSecondarySwatch = 6;

    bool bModernOverviewWasActive = false;
    /** Factory top-nav toggles between dense production and wide planning framing. */
    bool bWholeFactoryCameraSelected = false;

    ALBControlRoomOperationsConsole* FindOperationsConsole() const;
    ALBPlayerBuiltPressFlowController* FindPlayerFlow() const;
    ALBPressShopCampaignController* FindCampaignController() const;
    bool EnsureModernOverviewWidget();
    bool EnsureSettingsWidget();
    void SyncModernOverviewWidget();
    bool IsModernOverviewRendered() const;
    bool IsModernManagementRendered() const;
    void RefreshModernManagementContext();
    bool SelectModernProductionStage(FName StageId);
    UFUNCTION() void HandleModernManagementDestinationRequested(FName DestinationId);
    UFUNCTION() void HandleModernProductionStageSelectionRequested(FName StageId);
    UFUNCTION() void HandleModernProductionStageActionRequested(FName StageId);
    UFUNCTION() void HandleModernContextActionRequested(int32 ActionIndex);
    UFUNCTION() void HandleModernSimulationRateRequested(float RequestedRate);
    UFUNCTION() void HandleSettingsCloseRequested();
    UFUNCTION() void HandleSettingsAppearanceRequested();
    void DisarmCampaignLoadConfirmation();
    float GetPersistentHUDHeight() const;
    bool HandleProductionFlowClick(float ScreenX, float ScreenY,
        float ViewWidth, float ViewHeight);
    bool ActivateProductionFlowPrimaryAction();
    int32 GetManagementInformationLineCount() const;
    void EnsureMandatoryFactorySetup();
    void InitialiseFactoryBrandDraft();
    void RefreshFactoryBrandValidation();
    void AdjustSelectedFactoryLiverySwatch(int32 Direction);
    bool ActivateSelectedBrandEditorControl();
    int32 GetFactoryCatalogueItemCount() const;
    void SyncFactoryCataloguePageToSelection();
};
