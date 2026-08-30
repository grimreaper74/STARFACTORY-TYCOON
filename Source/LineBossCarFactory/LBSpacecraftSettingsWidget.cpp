#include "LBSpacecraftSettingsWidget.h"

#include "Blueprint/WidgetTree.h"
#include "Components/Border.h"
#include "Components/BorderSlot.h"
#include "Components/CanvasPanel.h"
#include "Components/CanvasPanelSlot.h"
#include "Components/ScrollBox.h"
#include "Components/TextBlock.h"
#include "Components/VerticalBox.h"
#include "Components/VerticalBoxSlot.h"
#include "GameFramework/InputSettings.h"
#include "Kismet/KismetSystemLibrary.h"
#include "LBGameUserSettings.h"
#include "LBSpacecraftDifficulty.h"
#include "LBSpacecraftCommandPanelWidget.h"
#include "LBSpacecraftInputMap.h"

#define LOCTEXT_NAMESPACE "LBSpacecraftSettings"

namespace LBSpacecraftSettingsPrivate
{
	// Unity-build safety: helpers qualified by subject. Provisional
	// indicator colours only - no brand exists yet.
	const FLinearColor SpacecraftSettingsDim(0.01f, 0.012f, 0.016f, 0.82f);
	const FLinearColor SpacecraftSettingsPanel(0.05f, 0.06f, 0.075f, 0.97f);
	const FLinearColor SpacecraftSettingsTitle(0.62f, 0.75f, 0.92f);
	const FLinearColor SpacecraftSettingsText(0.82f, 0.86f, 0.92f);
	const FLinearColor SpacecraftSettingsWarn(1.f, 0.62f, 0.18f);
	const FLinearColor SpacecraftSettingsLocked(0.45f, 0.48f, 0.55f);

	const TCHAR* SpacecraftDisplayRowTags[] = {
		TEXT("WindowMode"), TEXT("Resolution"), TEXT("Quality"),
		TEXT("VSync"), TEXT("FrameCap"), TEXT("RenderScale") };
	const TCHAR* SpacecraftAudioCameraRowTags[] = {
		TEXT("Difficulty"),
		TEXT("MasterVolume"), TEXT("EdgeScroll"), TEXT("PanSpeed"),
		TEXT("ZoomSpeed"), TEXT("InvertZoom") };

	bool SpacecraftIsDisplayRow(FName Tag)
	{
		for (const TCHAR* Row : SpacecraftDisplayRowTags)
		{
			if (Tag == FName(Row))
			{
				return true;
			}
		}
		return false;
	}

	bool SpacecraftIsAudioCameraRow(FName Tag)
	{
		for (const TCHAR* Row : SpacecraftAudioCameraRowTags)
		{
			if (Tag == FName(Row))
			{
				return true;
			}
		}
		return false;
	}

	FText SpacecraftWindowModeText(EWindowMode::Type Mode)
	{
		switch (Mode)
		{
		case EWindowMode::Fullscreen:
			return LOCTEXT("ModeFullscreen", "FULLSCREEN");
		case EWindowMode::WindowedFullscreen:
			return LOCTEXT("ModeBorderless", "BORDERLESS");
		default:
			return LOCTEXT("ModeWindowed", "WINDOWED");
		}
	}

	FText SpacecraftPresetText(ELBGraphicsPreset Preset)
	{
		switch (Preset)
		{
		case ELBGraphicsPreset::Low:
			return LOCTEXT("PresetLow", "LOW");
		case ELBGraphicsPreset::Medium:
			return LOCTEXT("PresetMedium", "MEDIUM");
		case ELBGraphicsPreset::High:
			return LOCTEXT("PresetHigh", "HIGH");
		case ELBGraphicsPreset::Epic:
			return LOCTEXT("PresetEpic", "EPIC");
		case ELBGraphicsPreset::Custom:
			return LOCTEXT("PresetCustom", "CUSTOM");
		default:
			return LOCTEXT("PresetAuto", "AUTO");
		}
	}

	const TArray<FIntPoint>& SpacecraftResolutionOptions()
	{
		static TArray<FIntPoint> Options;
		if (Options.Num() == 0)
		{
			TArray<FIntPoint> Supported;
			if (UKismetSystemLibrary::GetSupportedFullscreenResolutions(
				Supported))
			{
				for (const FIntPoint& Resolution : Supported)
				{
					if (Resolution.X >= 1280)
					{
						Options.AddUnique(Resolution);
					}
				}
			}
			if (Options.Num() == 0)
			{
				Options = { FIntPoint(1280, 720), FIntPoint(1600, 900),
					FIntPoint(1920, 1080), FIntPoint(2560, 1440),
					FIntPoint(3840, 2160) };
			}
		}
		return Options;
	}
}

const TArray<float>& ULBSpacecraftSettingsWidget::GetFrameCapOptions()
{
	static const TArray<float> Options = { 0.f, 30.f, 60.f, 120.f, 144.f,
		240.f };
	return Options;
}

const TArray<float>& ULBSpacecraftSettingsWidget::GetRenderScaleOptions()
{
	static const TArray<float> Options = { 50.f, 66.f, 75.f, 83.f, 100.f };
	return Options;
}

const TArray<float>& ULBSpacecraftSettingsWidget::GetCameraScaleOptions()
{
	static const TArray<float> Options = { 0.25f, 0.5f, 0.75f, 1.f, 1.25f,
		1.5f, 2.f };
	return Options;
}

float ULBSpacecraftSettingsWidget::NextOption(const TArray<float>& Options,
	const float Current)
{
	if (Options.Num() == 0)
	{
		return Current;
	}
	for (int32 Index = 0; Index < Options.Num(); ++Index)
	{
		if (FMath::IsNearlyEqual(Options[Index], Current, 0.01f))
		{
			return Options[(Index + 1) % Options.Num()];
		}
	}
	return Options[0];
}

ULBGameUserSettings* ULBSpacecraftSettingsWidget::ResolveSettings() const
{
	if (SettingsAuthorityOverride.IsValid())
	{
		return SettingsAuthorityOverride.Get();
	}
	return ULBGameUserSettings::GetLineBossGameUserSettings();
}

void ULBSpacecraftSettingsWidget::NativeOnInitialized()
{
	Super::NativeOnInitialized();
	using namespace LBSpacecraftSettingsPrivate;

	SetIsFocusable(true);

	UCanvasPanel* Canvas = WidgetTree->ConstructWidget<UCanvasPanel>(
		UCanvasPanel::StaticClass(), TEXT("SettingsCanvas"));
	WidgetTree->RootWidget = Canvas;

	UBorder* Dim = WidgetTree->ConstructWidget<UBorder>(
		UBorder::StaticClass(), TEXT("SettingsDim"));
	Dim->SetBrushColor(SpacecraftSettingsDim);
	if (UCanvasPanelSlot* DimSlot = Canvas->AddChildToCanvas(Dim))
	{
		DimSlot->SetAnchors(FAnchors(0.f, 0.f, 1.f, 1.f));
		DimSlot->SetOffsets(FMargin(0.f));
	}

	UBorder* Panel = WidgetTree->ConstructWidget<UBorder>(
		UBorder::StaticClass(), TEXT("SettingsPanel"));
	Panel->SetBrushColor(SpacecraftSettingsPanel);
	if (UCanvasPanelSlot* PanelSlot = Canvas->AddChildToCanvas(Panel))
	{
		PanelSlot->SetAnchors(FAnchors(0.5f, 0.f, 0.5f, 1.f));
		PanelSlot->SetAlignment(FVector2D(0.5f, 0.f));
		PanelSlot->SetOffsets(FMargin(0.f, 40.f, 0.f, 40.f));
		PanelSlot->SetSize(FVector2D(560.f, 0.f));
	}

	UVerticalBox* Outer = WidgetTree->ConstructWidget<UVerticalBox>(
		UVerticalBox::StaticClass());
	Panel->SetContent(Outer);
	if (UBorderSlot* PadSlot = Cast<UBorderSlot>(Outer->Slot))
	{
		PadSlot->SetPadding(FMargin(20.f));
	}

	UTextBlock* Title = WidgetTree->ConstructWidget<UTextBlock>(
		UTextBlock::StaticClass());
	Title->SetText(LOCTEXT("SettingsTitle", "SETTINGS"));
	Title->SetColorAndOpacity(FSlateColor(SpacecraftSettingsTitle));
	FSlateFontInfo TitleFont = Title->GetFont();
	TitleFont.Size = 20;
	Title->SetFont(TitleFont);
	if (UVerticalBoxSlot* TitleSlot = Outer->AddChildToVerticalBox(Title))
	{
		TitleSlot->SetPadding(FMargin(0.f, 0.f, 0.f, 10.f));
		TitleSlot->SetHorizontalAlignment(HAlign_Center);
	}

	UScrollBox* Scroll = WidgetTree->ConstructWidget<UScrollBox>(
		UScrollBox::StaticClass());
	if (UVerticalBoxSlot* ScrollSlot = Outer->AddChildToVerticalBox(Scroll))
	{
		ScrollSlot->SetSize(FSlateChildSize(ESlateSizeRule::Fill));
	}
	ContentBox = WidgetTree->ConstructWidget<UVerticalBox>(
		UVerticalBox::StaticClass());
	Scroll->AddChild(ContentBox);

	StatusBlock = WidgetTree->ConstructWidget<UTextBlock>(
		UTextBlock::StaticClass());
	StatusBlock->SetText(FText::GetEmpty());
	StatusBlock->SetAutoWrapText(true);
	StatusBlock->SetColorAndOpacity(FSlateColor(SpacecraftSettingsText));
	FSlateFontInfo StatusFont = StatusBlock->GetFont();
	StatusFont.Size = 12;
	StatusBlock->SetFont(StatusFont);
	if (UVerticalBoxSlot* StatusSlot =
		Outer->AddChildToVerticalBox(StatusBlock))
	{
		StatusSlot->SetPadding(FMargin(0.f, 8.f, 0.f, 0.f));
	}

	// DISPLAY - staged, committed by APPLY DISPLAY.
	BuildSection(LOCTEXT("SectionDisplay", "DISPLAY"));
	for (const TCHAR* Tag : SpacecraftDisplayRowTags)
	{
		AddRowButton(FName(Tag), FText::GetEmpty());
	}
	AddRowButton(FName(TEXT("ApplyDisplay")),
		LOCTEXT("ApplyDisplay", "APPLY DISPLAY CHANGES"));

	// GAME - difficulty. Unreal has no such setting of its own, so it
	// sits here with the rest of the player's choices.
	BuildSection(LOCTEXT("SectionGame", "GAME"));
	AddRowButton(FName(TEXT("Difficulty")), FText::GetEmpty());

	// AUDIO + CAMERA - applied and saved on click.
	BuildSection(LOCTEXT("SectionAudio", "AUDIO"));
	AddRowButton(FName(TEXT("MasterVolume")), FText::GetEmpty());
	BuildSection(LOCTEXT("SectionCamera", "CAMERA"));
	AddRowButton(FName(TEXT("EdgeScroll")), FText::GetEmpty());
	AddRowButton(FName(TEXT("PanSpeed")), FText::GetEmpty());
	AddRowButton(FName(TEXT("ZoomSpeed")), FText::GetEmpty());
	AddRowButton(FName(TEXT("InvertZoom")), FText::GetEmpty());

	// CONTROLS - the input map, one row each, click to rebind.
	BuildSection(LOCTEXT("SectionControls", "CONTROLS"));
	for (const FLBSpacecraftInputRow& Row : FLBSpacecraftInputMap::GetRows())
	{
		AddRowButton(Row.RowId, FText::GetEmpty(), Row.bRebindable);
	}
	AddRowButton(FName(TEXT("ResetControls")),
		LOCTEXT("ResetControls", "RESET CONTROLS TO DEFAULTS"));

	AddRowButton(FName(TEXT("Close")), LOCTEXT("Close", "CLOSE"));
}

void ULBSpacecraftSettingsWidget::NativeConstruct()
{
	Super::NativeConstruct();
	// Stage from the live authority so the first APPLY changes nothing
	// the player did not touch.
	if (const ULBGameUserSettings* Settings = ResolveSettings())
	{
		StagedResolution = Settings->GetScreenResolution();
		StagedWindowMode = Settings->GetFullscreenMode();
		bStagedVSync = Settings->IsVSyncEnabled();
		StagedFrameCap = Settings->GetFrameRateLimit();
	}
	RefreshAllRows();
	SetUserFocus(GetOwningPlayer());
}

void ULBSpacecraftSettingsWidget::BuildSection(const FText& Title)
{
	using namespace LBSpacecraftSettingsPrivate;
	UTextBlock* Label = WidgetTree->ConstructWidget<UTextBlock>(
		UTextBlock::StaticClass());
	Label->SetText(Title);
	Label->SetColorAndOpacity(FSlateColor(SpacecraftSettingsTitle));
	FSlateFontInfo Font = Label->GetFont();
	Font.Size = 14;
	Label->SetFont(Font);
	if (UVerticalBoxSlot* LabelSlot = ContentBox->AddChildToVerticalBox(Label))
	{
		LabelSlot->SetPadding(FMargin(2.f, 14.f, 0.f, 4.f));
	}
}

ULBSpacecraftTaggedButton* ULBSpacecraftSettingsWidget::AddRowButton(
	FName Tag, const FText& Label, const bool bEnabled)
{
	using namespace LBSpacecraftSettingsPrivate;
	ULBSpacecraftTaggedButton* Button =
		WidgetTree->ConstructWidget<ULBSpacecraftTaggedButton>(
			ULBSpacecraftTaggedButton::StaticClass());
	Button->Tag = Tag;
	Button->OnTagClicked = [this](FName InTag) { HandleRow(InTag); };
	Button->Arm();
	Button->SetIsEnabled(bEnabled);
	UTextBlock* Text = WidgetTree->ConstructWidget<UTextBlock>(
		UTextBlock::StaticClass());
	Text->SetText(Label);
	Text->SetColorAndOpacity(FSlateColor(
		bEnabled ? SpacecraftSettingsText : SpacecraftSettingsLocked));
	FSlateFontInfo Font = Text->GetFont();
	Font.Size = 13;
	Text->SetFont(Font);
	Button->AddChild(Text);
	if (UVerticalBoxSlot* ButtonSlot =
		ContentBox->AddChildToVerticalBox(Button))
	{
		ButtonSlot->SetPadding(FMargin(0.f, 2.f, 0.f, 0.f));
	}
	RowLabels.Add(Tag, Text);
	return Button;
}

void ULBSpacecraftSettingsWidget::SetRowLabel(FName Tag, const FText& Label)
{
	if (TObjectPtr<UTextBlock>* Found = RowLabels.Find(Tag))
	{
		if (*Found != nullptr)
		{
			(*Found)->SetText(Label);
		}
	}
}

void ULBSpacecraftSettingsWidget::SetStatus(const FText& Text,
	const bool bWarn)
{
	using namespace LBSpacecraftSettingsPrivate;
	if (StatusBlock != nullptr)
	{
		StatusBlock->SetText(Text);
		StatusBlock->SetColorAndOpacity(FSlateColor(
			bWarn ? SpacecraftSettingsWarn : SpacecraftSettingsText));
	}
}

FText ULBSpacecraftSettingsWidget::DescribeDisplayRow(FName Tag) const
{
	using namespace LBSpacecraftSettingsPrivate;
	const ULBGameUserSettings* Settings = ResolveSettings();
	if (Tag == FName(TEXT("WindowMode")))
	{
		return FText::Format(LOCTEXT("RowWindowMode", "WINDOW MODE: {0}"),
			SpacecraftWindowModeText(StagedWindowMode));
	}
	if (Tag == FName(TEXT("Resolution")))
	{
		return FText::Format(LOCTEXT("RowResolution", "RESOLUTION: {0} x {1}"),
			StagedResolution.X, StagedResolution.Y);
	}
	if (Tag == FName(TEXT("Quality")))
	{
		return FText::Format(LOCTEXT("RowQuality", "QUALITY: {0}"),
			SpacecraftPresetText(Settings != nullptr
				? Settings->GetGraphicsPreset() : ELBGraphicsPreset::Auto));
	}
	if (Tag == FName(TEXT("VSync")))
	{
		return bStagedVSync
			? LOCTEXT("RowVSyncOn", "VSYNC: ON")
			: LOCTEXT("RowVSyncOff", "VSYNC: OFF");
	}
	if (Tag == FName(TEXT("FrameCap")))
	{
		return StagedFrameCap <= 0.f
			? LOCTEXT("RowFrameCapOff", "FRAME CAP: OFF")
			: FText::Format(LOCTEXT("RowFrameCap", "FRAME CAP: {0} FPS"),
				FMath::RoundToInt(StagedFrameCap));
	}
	if (Tag == FName(TEXT("RenderScale")))
	{
		// The engine reports 0 while resolution quality is unset - that
		// IS native rendering, so the row says 100%.
		const float Scale = Settings != nullptr
			? Settings->GetLineBossRenderScale() : 100.f;
		return FText::Format(LOCTEXT("RowRenderScale", "RENDER SCALE: {0}%"),
			FMath::RoundToInt(Scale <= 0.f ? 100.f : Scale));
	}
	return FText::GetEmpty();
}

ELBSpacecraftDifficulty ULBSpacecraftSettingsWidget::NextDifficultyAfter(
	ELBSpacecraftDifficulty Current)
{
	const TArray<ELBSpacecraftDifficulty>& Order =
		FLBSpacecraftDifficulty::All();
	const int32 Index = Order.IndexOfByKey(Current);
	// Wraps, like every other cycled row on this page.
	return Order[(FMath::Max(Index, 0) + 1) % Order.Num()];
}

FText ULBSpacecraftSettingsWidget::DescribeAudioCameraRow(FName Tag) const
{
	const ULBGameUserSettings* Settings = ResolveSettings();
	if (Settings == nullptr)
	{
		return FText::GetEmpty();
	}
	if (Tag == FName(TEXT("Difficulty")))
	{
		return FText::Format(LOCTEXT("RowDifficulty", "DIFFICULTY: {0}"),
			FLBSpacecraftDifficulty::DisplayName(
				Settings->GetSpacecraftDifficulty()));
	}
	if (Tag == FName(TEXT("MasterVolume")))
	{
		return FText::Format(LOCTEXT("RowMasterVolume", "MASTER VOLUME: {0}%"),
			FMath::RoundToInt(Settings->GetMasterVolume() * 100.f));
	}
	if (Tag == FName(TEXT("EdgeScroll")))
	{
		return Settings->IsEdgeScrollEnabled()
			? LOCTEXT("RowEdgeOn", "EDGE SCROLL: ON")
			: LOCTEXT("RowEdgeOff", "EDGE SCROLL: OFF");
	}
	if (Tag == FName(TEXT("PanSpeed")))
	{
		return FText::Format(LOCTEXT("RowPanSpeed", "PAN SPEED: {0}%"),
			FMath::RoundToInt(Settings->GetCameraPanSpeedScale() * 100.f));
	}
	if (Tag == FName(TEXT("ZoomSpeed")))
	{
		return FText::Format(LOCTEXT("RowZoomSpeed", "ZOOM SPEED: {0}%"),
			FMath::RoundToInt(Settings->GetCameraZoomSpeedScale() * 100.f));
	}
	if (Tag == FName(TEXT("InvertZoom")))
	{
		return Settings->IsZoomInverted()
			? LOCTEXT("RowInvertOn", "INVERT ZOOM: ON")
			: LOCTEXT("RowInvertOff", "INVERT ZOOM: OFF");
	}
	return FText::GetEmpty();
}

FText ULBSpacecraftSettingsWidget::DescribeControlRow(FName RowId) const
{
	const FLBSpacecraftInputRow* Row = FLBSpacecraftInputMap::FindRow(RowId);
	if (Row == nullptr)
	{
		return FText::GetEmpty();
	}
	if (ListeningRowId == RowId)
	{
		return FText::Format(LOCTEXT("RowListening",
			"{0}:  PRESS A KEY - ESC CANCELS"), Row->DisplayName);
	}
	const UInputSettings* Settings = GetDefault<UInputSettings>();
	bool bShift = false;
	const FKey Key = Settings != nullptr
		? FLBSpacecraftInputMap::GetPrimaryKey(*Settings, *Row, bShift)
		: Row->DefaultKey;
	FText KeyText = Key.IsValid()
		? Key.GetDisplayName()
		: LOCTEXT("RowUnbound", "UNBOUND");
	if (bShift)
	{
		KeyText = FText::Format(LOCTEXT("RowShiftKey", "SHIFT + {0}"),
			KeyText);
	}
	return FText::Format(LOCTEXT("RowControl", "{0}:  {1}"),
		Row->DisplayName, KeyText);
}

void ULBSpacecraftSettingsWidget::RefreshAllRows()
{
	using namespace LBSpacecraftSettingsPrivate;
	for (const TCHAR* Tag : SpacecraftDisplayRowTags)
	{
		SetRowLabel(FName(Tag), DescribeDisplayRow(FName(Tag)));
	}
	for (const TCHAR* Tag : SpacecraftAudioCameraRowTags)
	{
		SetRowLabel(FName(Tag), DescribeAudioCameraRow(FName(Tag)));
	}
	for (const FLBSpacecraftInputRow& Row : FLBSpacecraftInputMap::GetRows())
	{
		SetRowLabel(Row.RowId, DescribeControlRow(Row.RowId));
	}
}

void ULBSpacecraftSettingsWidget::HandleRow(FName Tag)
{
	using namespace LBSpacecraftSettingsPrivate;
	if (bDisplayConfirmationActive)
	{
		// The countdown owns the screen: any row click keeps the new
		// display (the explicit escape hatch is waiting out the timer).
		FinishDisplayConfirmation(true);
		return;
	}
	if (IsListeningForRebind())
	{
		return;
	}
	if (Tag == FName(TEXT("Close")))
	{
		RequestClose();
		return;
	}
	if (Tag == FName(TEXT("ApplyDisplay")))
	{
		ApplyStagedDisplay();
		return;
	}
	if (Tag == FName(TEXT("ResetControls")))
	{
		ResetControlsToDefaults();
		return;
	}
	if (SpacecraftIsDisplayRow(Tag))
	{
		HandleDisplayCycle(Tag);
		return;
	}
	if (SpacecraftIsAudioCameraRow(Tag))
	{
		HandleAudioCameraCycle(Tag);
		return;
	}
	if (FLBSpacecraftInputMap::FindRow(Tag) != nullptr)
	{
		BeginRebind(Tag);
	}
}

void ULBSpacecraftSettingsWidget::HandleDisplayCycle(FName Tag)
{
	using namespace LBSpacecraftSettingsPrivate;
	ULBGameUserSettings* Settings = ResolveSettings();
	if (Tag == FName(TEXT("WindowMode")))
	{
		StagedWindowMode =
			StagedWindowMode == EWindowMode::Fullscreen
				? EWindowMode::WindowedFullscreen
				: StagedWindowMode == EWindowMode::WindowedFullscreen
					? EWindowMode::Windowed
					: EWindowMode::Fullscreen;
	}
	else if (Tag == FName(TEXT("Resolution")))
	{
		const TArray<FIntPoint>& Options = SpacecraftResolutionOptions();
		int32 Index = Options.IndexOfByKey(StagedResolution);
		Index = (Index + 1) % Options.Num();
		StagedResolution = Options[Index];
	}
	else if (Tag == FName(TEXT("Quality")))
	{
		if (Settings != nullptr)
		{
			// AUTO is first-run policy, CUSTOM is a derived state - the
			// cycle walks the four explicit tiers.
			ELBGraphicsPreset Next = ELBGraphicsPreset::Low;
			switch (Settings->GetGraphicsPreset())
			{
			case ELBGraphicsPreset::Low:
				Next = ELBGraphicsPreset::Medium;
				break;
			case ELBGraphicsPreset::Medium:
				Next = ELBGraphicsPreset::High;
				break;
			case ELBGraphicsPreset::High:
				Next = ELBGraphicsPreset::Epic;
				break;
			default:
				Next = ELBGraphicsPreset::Low;
				break;
			}
			Settings->SetGraphicsPreset(Next);
			Settings->ApplyAndSaveLineBossSettings();
		}
	}
	else if (Tag == FName(TEXT("VSync")))
	{
		bStagedVSync = !bStagedVSync;
	}
	else if (Tag == FName(TEXT("FrameCap")))
	{
		StagedFrameCap = NextOption(GetFrameCapOptions(), StagedFrameCap);
	}
	else if (Tag == FName(TEXT("RenderScale")))
	{
		if (Settings != nullptr)
		{
			const float Current = Settings->GetLineBossRenderScale();
			Settings->SetLineBossRenderScale(NextOption(
				GetRenderScaleOptions(),
				Current <= 0.f ? 100.f : Current));
			Settings->ApplyAndSaveLineBossSettings();
		}
	}
	RefreshAllRows();
}

void ULBSpacecraftSettingsWidget::HandleAudioCameraCycle(FName Tag)
{
	ULBGameUserSettings* Settings = ResolveSettings();
	if (Settings == nullptr)
	{
		return;
	}
	if (Tag == FName(TEXT("Difficulty")))
	{
		Settings->SetSpacecraftDifficulty(NextDifficultyAfter(
			Settings->GetSpacecraftDifficulty()));
	}
	else if (Tag == FName(TEXT("MasterVolume")))
	{
		// 0..100 in ten steps, wrapping - and audible immediately.
		const float Next = Settings->GetMasterVolume() >= 0.99f
			? 0.f : Settings->GetMasterVolume() + 0.1f;
		Settings->SetMasterVolume(Next);
		Settings->ApplyMasterVolumeToWorld(GetWorld());
	}
	else if (Tag == FName(TEXT("EdgeScroll")))
	{
		Settings->SetEdgeScrollEnabled(!Settings->IsEdgeScrollEnabled());
	}
	else if (Tag == FName(TEXT("PanSpeed")))
	{
		Settings->SetCameraPanSpeedScale(NextOption(
			GetCameraScaleOptions(), Settings->GetCameraPanSpeedScale()));
	}
	else if (Tag == FName(TEXT("ZoomSpeed")))
	{
		Settings->SetCameraZoomSpeedScale(NextOption(
			GetCameraScaleOptions(), Settings->GetCameraZoomSpeedScale()));
	}
	else if (Tag == FName(TEXT("InvertZoom")))
	{
		Settings->SetZoomInverted(!Settings->IsZoomInverted());
	}
	Settings->SaveSettings();
	RefreshAllRows();
}

void ULBSpacecraftSettingsWidget::ApplyStagedDisplay()
{
	ULBGameUserSettings* Settings = ResolveSettings();
	if (Settings == nullptr)
	{
		return;
	}
	PreApplyResolution = Settings->GetScreenResolution();
	PreApplyWindowMode = Settings->GetFullscreenMode();
	const bool bDisplayChanged = PreApplyResolution != StagedResolution
		|| PreApplyWindowMode != StagedWindowMode;
	Settings->SetLineBossScreenResolution(StagedResolution);
	Settings->SetLineBossWindowMode(StagedWindowMode);
	Settings->SetLineBossVSyncEnabled(bStagedVSync);
	Settings->SetLineBossFrameRateLimit(StagedFrameCap);
	Settings->ApplyAndSaveLineBossSettings();
	if (bDisplayChanged)
	{
		// The confirmed-video-mode contract: an unreadable screen must
		// never strand the player - silence reverts.
		bDisplayConfirmationActive = true;
		DisplayConfirmationRemaining = DisplayConfirmationSeconds;
	}
	else
	{
		SetStatus(LOCTEXT("DisplayApplied", "DISPLAY SETTINGS APPLIED"));
	}
	RefreshAllRows();
}

void ULBSpacecraftSettingsWidget::FinishDisplayConfirmation(const bool bKeep)
{
	bDisplayConfirmationActive = false;
	DisplayConfirmationRemaining = 0.f;
	ULBGameUserSettings* Settings = ResolveSettings();
	if (Settings == nullptr)
	{
		return;
	}
	if (bKeep)
	{
		Settings->ConfirmVideoMode();
		Settings->SaveSettings();
		SetStatus(LOCTEXT("DisplayKept", "DISPLAY SETTINGS KEPT"));
	}
	else
	{
		Settings->RevertVideoMode();
		StagedResolution = PreApplyResolution;
		StagedWindowMode = PreApplyWindowMode;
		Settings->SetLineBossScreenResolution(PreApplyResolution);
		Settings->SetLineBossWindowMode(PreApplyWindowMode);
		Settings->ApplyAndSaveLineBossSettings();
		SetStatus(LOCTEXT("DisplayReverted",
			"DISPLAY REVERTED - NOTHING WAS CONFIRMED"), true);
	}
	RefreshAllRows();
}

void ULBSpacecraftSettingsWidget::BeginRebind(FName RowId)
{
	const FLBSpacecraftInputRow* Row = FLBSpacecraftInputMap::FindRow(RowId);
	if (Row == nullptr || !Row->bRebindable)
	{
		return;
	}
	ListeningRowId = RowId;
	SetStatus(LOCTEXT("ListeningStatus",
		"PRESS THE NEW KEY - ESCAPE CANCELS"));
	SetUserFocus(GetOwningPlayer());
	RefreshAllRows();
}

void ULBSpacecraftSettingsWidget::CompleteRebind(const FKey& Key)
{
	const FName RowId = ListeningRowId;
	ListeningRowId = NAME_None;
	if (RowId.IsNone())
	{
		return;
	}
	UInputSettings* Settings = UInputSettings::GetInputSettings();
	if (Settings == nullptr)
	{
		return;
	}
	FString Reason;
	const bool bBound = FLBSpacecraftInputMap::RebindRow(*Settings, RowId,
		Key, Reason);
	if (bBound)
	{
		PersistKeyBindings();
	}
	// The fail-closed reason IS the player feedback, bound or refused.
	SetStatus(FText::FromString(Reason), !bBound);
	RefreshAllRows();
}

void ULBSpacecraftSettingsWidget::ResetControlsToDefaults()
{
	UInputSettings* Settings = UInputSettings::GetInputSettings();
	if (Settings == nullptr)
	{
		return;
	}
	FLBSpacecraftInputMap::ResetSpacecraftBindings(*Settings);
	PersistKeyBindings();
	SetStatus(LOCTEXT("ControlsReset", "CONTROLS RESET TO DEFAULTS"));
	RefreshAllRows();
}

void ULBSpacecraftSettingsWidget::PersistKeyBindings()
{
	if (UInputSettings* Settings = UInputSettings::GetInputSettings())
	{
		Settings->SaveKeyMappings();
	}
	if (APlayerController* PlayerController = GetOwningPlayer())
	{
		if (PlayerController->PlayerInput != nullptr)
		{
			PlayerController->PlayerInput->ForceRebuildingKeyMaps(true);
		}
	}
}

void ULBSpacecraftSettingsWidget::RequestClose()
{
	if (IsListeningForRebind())
	{
		ListeningRowId = NAME_None;
		RefreshAllRows();
	}
	OnCloseRequested.ExecuteIfBound();
}

void ULBSpacecraftSettingsWidget::NativeTick(const FGeometry& MyGeometry,
	const float InDeltaTime)
{
	Super::NativeTick(MyGeometry, InDeltaTime);
	if (bDisplayConfirmationActive)
	{
		DisplayConfirmationRemaining -= InDeltaTime;
		SetStatus(FText::Format(LOCTEXT("ConfirmCountdown",
			"KEEP THIS DISPLAY? CLICK ANYWHERE TO KEEP - REVERTING IN {0} S"),
			FMath::Max(0, FMath::CeilToInt(DisplayConfirmationRemaining))),
			true);
		if (DisplayConfirmationRemaining <= 0.f)
		{
			FinishDisplayConfirmation(false);
		}
	}
}

FReply ULBSpacecraftSettingsWidget::NativeOnKeyDown(
	const FGeometry& InGeometry, const FKeyEvent& InKeyEvent)
{
	if (IsListeningForRebind())
	{
		if (InKeyEvent.GetKey() == EKeys::Escape)
		{
			ListeningRowId = NAME_None;
			SetStatus(LOCTEXT("RebindCancelled", "REBIND CANCELLED"));
			RefreshAllRows();
		}
		else
		{
			CompleteRebind(InKeyEvent.GetKey());
		}
		return FReply::Handled();
	}
	if (InKeyEvent.GetKey() == EKeys::Escape)
	{
		RequestClose();
		return FReply::Handled();
	}
	return Super::NativeOnKeyDown(InGeometry, InKeyEvent);
}

FReply ULBSpacecraftSettingsWidget::NativeOnMouseButtonDown(
	const FGeometry& InGeometry, const FPointerEvent& InMouseEvent)
{
	if (IsListeningForRebind())
	{
		CompleteRebind(InMouseEvent.GetEffectingButton());
		return FReply::Handled();
	}
	return Super::NativeOnMouseButtonDown(InGeometry, InMouseEvent);
}

#undef LOCTEXT_NAMESPACE
