#pragma once

#include "CoreMinimal.h"
#include "Blueprint/UserWidget.h"
#include "Components/ComboBoxString.h"
#include "Input/Reply.h"
#include "LBGameUserSettings.h"
#include "LBSettingsRootWidget.generated.h"

class UBorder;
class UButton;
class UOverlay;
class UTextBlock;
class UVerticalBox;
class UWidget;
struct FKey;

DECLARE_DYNAMIC_MULTICAST_DELEGATE(FLBSettingsCloseRequested);
DECLARE_DYNAMIC_MULTICAST_DELEGATE(FLBSettingsAppearanceRequested);

/**
 * Native, controller-first settings surface for the factory view.
 *
 * The widget stages player choices locally and writes only through
 * ULBGameUserSettings when Apply is pressed. Resolution and window-mode
 * changes use Unreal's confirmed-video-mode authority and automatically
 * revert if the player does not accept the new display within 15 seconds.
 */
UCLASS(BlueprintType, Blueprintable)
class LINEBOSSCARFACTORY_API ULBSettingsRootWidget : public UUserWidget
{
    GENERATED_BODY()

public:
    static constexpr float DisplayConfirmationSeconds = 15.0f;
    static constexpr int32 MainControllerControlCount = 11;

    UPROPERTY(BlueprintAssignable, Category="Line Boss|Settings|Events")
    FLBSettingsCloseRequested OnCloseRequested;

    UPROPERTY(BlueprintAssignable, Category="Line Boss|Settings|Events")
    FLBSettingsAppearanceRequested OnAppearanceRequested;

    /** Reloads every staged control from the current settings authority. */
    UFUNCTION(BlueprintCallable, Category="Line Boss|Settings")
    void RefreshFromSettings();

    /** Places keyboard/gamepad focus on the first functional selector. */
    UFUNCTION(BlueprintCallable, Category="Line Boss|Settings")
    void FocusInitialControl();

    /** Safe close hook: never leaves an unconfirmed display mode stranded. */
    UFUNCTION(BlueprintCallable, Category="Line Boss|Settings")
    void CancelAndRevertPendingDisplayChange();

    /** True only when the complete authored native tree has a Slate counterpart. */
    bool HasRenderableSettingsShell() const;

    /** Public audit seam for the explicit wraparound controller focus graph. */
    bool HasCompleteControllerFocusGraph() const;

    UFUNCTION(BlueprintPure, Category="Line Boss|Settings")
    bool IsDisplayConfirmationActive() const { return bDisplayConfirmationActive; }

    UFUNCTION(BlueprintPure, Category="Line Boss|Settings")
    float GetDisplayConfirmationTimeRemaining() const
    {
        return DisplayConfirmationTimeRemaining;
    }

    /** Stable option contracts shared by UI automation and controller tests. */
    static TArray<FString> GetGraphicsPresetOptions();
    /** Stable player-facing livery choices. Safety yellow remains reserved. */
    static TArray<FString> GetFactoryLiveryOptions();
    static TArray<FName> GetCanonicalControllerControlIds();
    static TArray<FName> GetDisplayConfirmationControlIds();
    static bool TryParseResolutionOption(const FString& Option, FIntPoint& OutResolution);
    static bool TryParseGraphicsPresetOption(const FString& Option, ELBGraphicsPreset& OutPreset);
    static bool TryGetFactoryLiveryColour(const FString& Option,
        FLinearColor& OutColour);
    static bool IsBackInputKey(const FKey& Key);

    /** Test seam; production always resolves the configured engine singleton. */
    void SetSettingsAuthorityForTesting(ULBGameUserSettings* InSettings);

protected:
    virtual TSharedRef<SWidget> RebuildWidget() override;
    virtual void NativeOnInitialized() override;
    virtual void NativeConstruct() override;
    virtual void NativeTick(const FGeometry& MyGeometry, float InDeltaTime) override;
    virtual FReply NativeOnKeyDown(const FGeometry& InGeometry,
        const FKeyEvent& InKeyEvent) override;

private:
    UPROPERTY(Transient)
    TObjectPtr<UOverlay> RootOverlay;

    UPROPERTY(Transient)
    TObjectPtr<UBorder> SettingsPanel;

    UPROPERTY(Transient)
    TObjectPtr<UComboBoxString> PresetCombo;

    UPROPERTY(Transient)
    TObjectPtr<UComboBoxString> ResolutionCombo;

    UPROPERTY(Transient)
    TObjectPtr<UComboBoxString> WindowModeCombo;

    UPROPERTY(Transient)
    TObjectPtr<UComboBoxString> VSyncCombo;

    UPROPERTY(Transient)
    TObjectPtr<UComboBoxString> FrameCapCombo;

    UPROPERTY(Transient)
    TObjectPtr<UComboBoxString> RenderScaleCombo;

    UPROPERTY(Transient)
    TObjectPtr<UComboBoxString> PrimaryLiveryCombo;

    UPROPERTY(Transient)
    TObjectPtr<UComboBoxString> SecondaryLiveryCombo;

    UPROPERTY(Transient)
    TObjectPtr<UButton> AppearanceButton;

    UPROPERTY(Transient)
    TObjectPtr<UButton> AutoDetectButton;

    UPROPERTY(Transient)
    TObjectPtr<UButton> CancelButton;

    UPROPERTY(Transient)
    TObjectPtr<UButton> ApplyButton;

    UPROPERTY(Transient)
    TObjectPtr<UTextBlock> StatusLabel;

    UPROPERTY(Transient)
    TObjectPtr<UOverlay> DisplayConfirmationOverlay;

    UPROPERTY(Transient)
    TObjectPtr<UTextBlock> DisplayConfirmationLabel;

    UPROPERTY(Transient)
    TObjectPtr<UButton> RevertDisplayButton;

    UPROPERTY(Transient)
    TObjectPtr<UButton> KeepDisplayButton;

    UPROPERTY(Transient)
    TArray<TObjectPtr<UWidget>> MainFocusOrder;

    TWeakObjectPtr<ULBGameUserSettings> SettingsAuthorityOverride;
    bool bControllerNavigationConfigured = false;
    bool bDisplayConfirmationActive = false;
    float DisplayConfirmationTimeRemaining = 0.0f;

    void BuildShell();
    UComboBoxString* BuildSettingCombo(UVerticalBox* Column, FName Name,
        const FString& Label, const FString& SupportingText,
        const TArray<FString>& Options);
    UButton* BuildActionButton(FName Name, const FString& Label,
        bool bPrimaryAction = false);
    void ConfigureControllerNavigation();
    ULBGameUserSettings* ResolveSettings() const;
    void BeginDisplayConfirmation();
    void FinishDisplayConfirmation(bool bKeepChanges);
    void SetStatus(const FString& Message, bool bError = false);
    bool ApplyStagedSettings();

    UFUNCTION() void HandleApplyClicked();
    UFUNCTION() void HandleCancelClicked();
    UFUNCTION() void HandleAutoDetectClicked();
    UFUNCTION() void HandleAppearanceClicked();
    UFUNCTION() void HandleKeepDisplayClicked();
    UFUNCTION() void HandleRevertDisplayClicked();
    UFUNCTION() void HandleRenderScaleChanged(FString SelectedItem,
        ESelectInfo::Type SelectionType);
};
