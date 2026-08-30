// Spacecraft-era settings surface (owner 2026-08-26: "get the full
// unreal settings working"): DISPLAY (window mode, resolution, quality
// preset, vsync, frame cap, render scale - staged, applied through
// ULBGameUserSettings, with the confirmed-video-mode 15 s keep/revert
// contract), AUDIO (master volume, applied live), CAMERA (edge scroll,
// pan/zoom speed, zoom invert - applied live), CONTROLS (every
// FLBSpacecraftInputMap row, click-to-rebind, fail-closed collisions,
// reset to defaults). Native UMG, all player text LOCTEXT, options as
// CYCLE buttons (click steps to the next option) in the command
// panel's visual language.

#pragma once

#include "CoreMinimal.h"
#include "LBSpacecraftDifficulty.h"
#include "Blueprint/UserWidget.h"
#include "GameFramework/GameUserSettings.h"
#include "InputCoreTypes.h"
#include "LBSpacecraftSettingsWidget.generated.h"

class UBorder;
class UScrollBox;
class UTextBlock;
class UVerticalBox;
class ULBSpacecraftTaggedButton;
class ULBGameUserSettings;

UCLASS()
class LINEBOSSCARFACTORY_API ULBSpacecraftSettingsWidget : public UUserWidget
{
	GENERATED_BODY()

public:
	static constexpr float DisplayConfirmationSeconds = 15.f;

	DECLARE_DELEGATE(FLBSpacecraftSettingsClosed);
	FLBSpacecraftSettingsClosed OnCloseRequested;

	/** Frame-rate cap steps offered by the FRAME CAP cycle (0 = off). */
	static const TArray<float>& GetFrameCapOptions();

	/** Render-scale percent steps offered by the RENDER SCALE cycle. */
	static const TArray<float>& GetRenderScaleOptions();

	/** Camera speed-scale steps shared by PAN and ZOOM speed cycles. */
	static const TArray<float>& GetCameraScaleOptions();

	/** The next value in a cycle list after Current (wraps; tolerant of
	 *  a Current that is not in the list - returns the first entry). */
	static float NextOption(const TArray<float>& Options, float Current);

	/** Test seam; production resolves the engine singleton. */
	void SetSettingsAuthorityForTesting(ULBGameUserSettings* InSettings)
	{
		SettingsAuthorityOverride = InSettings;
	}

	bool IsListeningForRebind() const { return !ListeningRowId.IsNone(); }
	bool IsDisplayConfirmationActive() const
	{
		return bDisplayConfirmationActive;
	}

protected:
	virtual void NativeOnInitialized() override;
	virtual void NativeConstruct() override;
	virtual void NativeTick(const FGeometry& MyGeometry,
		float InDeltaTime) override;
	virtual FReply NativeOnKeyDown(const FGeometry& InGeometry,
		const FKeyEvent& InKeyEvent) override;
	virtual FReply NativeOnMouseButtonDown(const FGeometry& InGeometry,
		const FPointerEvent& InMouseEvent) override;

private:
	UPROPERTY(Transient)
	TObjectPtr<UVerticalBox> ContentBox;

	UPROPERTY(Transient)
	TObjectPtr<UTextBlock> StatusBlock;

	/** Row-id -> the button whose label renders that row's state. */
	UPROPERTY(Transient)
	TMap<FName, TObjectPtr<UTextBlock>> RowLabels;

	TWeakObjectPtr<ULBGameUserSettings> SettingsAuthorityOverride;

	/** Staged display choices (committed by APPLY DISPLAY). */
	FIntPoint StagedResolution = FIntPoint(1920, 1080);
	TEnumAsByte<EWindowMode::Type> StagedWindowMode = EWindowMode::Windowed;
	bool bStagedVSync = false;
	float StagedFrameCap = 0.f;

	/** Controls page rebind-listening state. */
	FName ListeningRowId;

	/** Confirmed-video-mode countdown. */
	bool bDisplayConfirmationActive = false;
	float DisplayConfirmationRemaining = 0.f;
	FIntPoint PreApplyResolution = FIntPoint(1920, 1080);
	TEnumAsByte<EWindowMode::Type> PreApplyWindowMode = EWindowMode::Windowed;

	ULBGameUserSettings* ResolveSettings() const;

	void BuildSection(const FText& Title);
	ULBSpacecraftTaggedButton* AddRowButton(FName Tag, const FText& Label,
		bool bEnabled = true);
	void SetRowLabel(FName Tag, const FText& Label);
	void SetStatus(const FText& Text, bool bWarn = false);

	void RefreshAllRows();
	FText DescribeDisplayRow(FName Tag) const;
	FText DescribeAudioCameraRow(FName Tag) const;

public:
	/** Pure: the next difficulty when the row is clicked. Wraps, like
	 *  every other cycled row on this page. */
	static ELBSpacecraftDifficulty NextDifficultyAfter(
		ELBSpacecraftDifficulty Current);

private:
	FText DescribeControlRow(FName RowId) const;

	void HandleRow(FName Tag);
	void HandleDisplayCycle(FName Tag);
	void HandleAudioCameraCycle(FName Tag);
	void ApplyStagedDisplay();
	void FinishDisplayConfirmation(bool bKeep);
	void BeginRebind(FName RowId);
	void CompleteRebind(const FKey& Key);
	void ResetControlsToDefaults();
	void PersistKeyBindings();
	void RequestClose();
};
