#include "LBSpacecraftPauseMenuWidget.h"

#include "Blueprint/WidgetTree.h"
#include "Components/Border.h"
#include "Components/BorderSlot.h"
#include "Components/CanvasPanel.h"
#include "Components/CanvasPanelSlot.h"
#include "Components/TextBlock.h"
#include "Components/VerticalBox.h"
#include "Components/VerticalBoxSlot.h"
#include "Kismet/GameplayStatics.h"
#include "Kismet/KismetSystemLibrary.h"
#include "LBSpacecraftCommandPanelWidget.h"
#include "LBSpacecraftGameMode.h"

#define LOCTEXT_NAMESPACE "LBSpacecraftPause"

namespace LBSpacecraftPauseMenuPrivate
{
	// GRADED TO THE ADOPTED PALETTE (2026-08-29). Written as sRGB hex
	// and converted, so these read as the values the palette document
	// states. The interface carries NO hue - the machinery has it -
	// and #EC3013 is the single exception, reserved for refusal.
	inline FLinearColor SpacecraftUiToken(const TCHAR* Hex, float Alpha = 1.f)
	{
		FLinearColor Out = FLinearColor(FColor::FromHex(Hex));
		Out.A = Alpha;
		return Out;
	}
	// Unity-build safety: helpers qualified by subject. Provisional
	// indicator colours only - no brand exists yet.
	const FLinearColor SpacecraftPauseDim =
		SpacecraftUiToken(TEXT("#0E0E0E"), 0.80f);   // Panel.Edge
	const FLinearColor SpacecraftPausePanel =
		SpacecraftUiToken(TEXT("#1B1B1B"), 0.97f);   // Panel.Bg
	const FLinearColor SpacecraftPauseTitle =
		SpacecraftUiToken(TEXT("#A8A4A1"));          // Text.Heading
	const FLinearColor SpacecraftPauseButtonText =
		SpacecraftUiToken(TEXT("#1B1B1B"));
}

void ULBSpacecraftPauseMenuWidget::BindGame(
	ALBSpacecraftGameMode* InGameMode)
{
	GameMode = InGameMode;
}

void ULBSpacecraftPauseMenuWidget::NativeOnInitialized()
{
	Super::NativeOnInitialized();
	using namespace LBSpacecraftPauseMenuPrivate;

	UCanvasPanel* Canvas = WidgetTree->ConstructWidget<UCanvasPanel>(
		UCanvasPanel::StaticClass(), TEXT("PauseCanvas"));
	WidgetTree->RootWidget = Canvas;

	// Full-screen dim so the factory reads as paused.
	UBorder* Dim = WidgetTree->ConstructWidget<UBorder>(
		UBorder::StaticClass(), TEXT("PauseDim"));
	Dim->SetBrushColor(SpacecraftPauseDim);
	if (UCanvasPanelSlot* DimSlot = Canvas->AddChildToCanvas(Dim))
	{
		DimSlot->SetAnchors(FAnchors(0.f, 0.f, 1.f, 1.f));
		DimSlot->SetOffsets(FMargin(0.f));
	}

	UBorder* Panel = WidgetTree->ConstructWidget<UBorder>(
		UBorder::StaticClass(), TEXT("PausePanel"));
	Panel->SetBrushColor(SpacecraftPausePanel);
	if (UCanvasPanelSlot* PanelSlot = Canvas->AddChildToCanvas(Panel))
	{
		PanelSlot->SetAnchors(FAnchors(0.5f, 0.5f, 0.5f, 0.5f));
		PanelSlot->SetAlignment(FVector2D(0.5f, 0.5f));
		// Taller than it was: two more buttons and a status line.
		PanelSlot->SetSize(FVector2D(360.f, 420.f));
	}

	MenuBox = WidgetTree->ConstructWidget<UVerticalBox>(
		UVerticalBox::StaticClass());
	Panel->SetContent(MenuBox);
	if (UBorderSlot* PadSlot = Cast<UBorderSlot>(MenuBox->Slot))
	{
		PadSlot->SetPadding(FMargin(24.f));
	}

	UTextBlock* Title = WidgetTree->ConstructWidget<UTextBlock>(
		UTextBlock::StaticClass());
	Title->SetText(LOCTEXT("PausedTitle", "PAUSED"));
	Title->SetColorAndOpacity(FSlateColor(SpacecraftPauseTitle));
	FSlateFontInfo TitleFont = Title->GetFont();
	TitleFont.Size = 22;
	Title->SetFont(TitleFont);
	if (UVerticalBoxSlot* TitleSlot =
		MenuBox->AddChildToVerticalBox(Title))
	{
		TitleSlot->SetPadding(FMargin(0.f, 0.f, 0.f, 16.f));
		TitleSlot->SetHorizontalAlignment(HAlign_Center);
	}

	AddMenuButton(LOCTEXT("Resume", "RESUME"), FName(TEXT("Resume")));
	// SAVE AND LOAD BELONG HERE, above the destructive pair. This menu
	// offered RESTART FACTORY and QUIT TO DESKTOP and no way to save -
	// the two buttons that throw a factory away sat where a player
	// looks when they want to stop, with nothing beside them to keep
	// it. The save pipeline was written and tested long ago; it simply
	// had no button anywhere.
	AddMenuButton(LOCTEXT("SaveGame", "SAVE GAME"),
		FName(TEXT("Save")));
	AddMenuButton(LOCTEXT("LoadGame", "LOAD GAME"),
		FName(TEXT("Load")));
	AddMenuButton(LOCTEXT("Settings", "SETTINGS"),
		FName(TEXT("Settings")));
	AddMenuButton(LOCTEXT("Restart", "RESTART FACTORY"),
		FName(TEXT("Restart")));
	AddMenuButton(LOCTEXT("Quit", "QUIT TO DESKTOP"),
		FName(TEXT("Quit")));

	StatusText = WidgetTree->ConstructWidget<UTextBlock>(
		UTextBlock::StaticClass());
	StatusText->SetText(FText::GetEmpty());
	StatusText->SetColorAndOpacity(FSlateColor(SpacecraftPauseTitle));
	FSlateFontInfo StatusFont = StatusText->GetFont();
	StatusFont.Size = 11;
	StatusText->SetFont(StatusFont);
	StatusText->SetAutoWrapText(true);
	if (UVerticalBoxSlot* StatusSlot =
		MenuBox->AddChildToVerticalBox(StatusText))
	{
		StatusSlot->SetPadding(FMargin(0.f, 14.f, 0.f, 0.f));
		StatusSlot->SetHorizontalAlignment(HAlign_Center);
	}
}

void ULBSpacecraftPauseMenuWidget::SetStatusText(const FText& Text)
{
	if (StatusText != nullptr)
	{
		StatusText->SetText(Text);
	}
}

void ULBSpacecraftPauseMenuWidget::AddMenuButton(const FText& Label,
	FName Tag)
{
	using namespace LBSpacecraftPauseMenuPrivate;
	ULBSpacecraftTaggedButton* Button =
		WidgetTree->ConstructWidget<ULBSpacecraftTaggedButton>(
			ULBSpacecraftTaggedButton::StaticClass());
	Button->Tag = Tag;
	Button->OnTagClicked = [this](FName InTag) { HandleAction(InTag); };
	Button->Arm();
	UTextBlock* Text = WidgetTree->ConstructWidget<UTextBlock>(
		UTextBlock::StaticClass());
	Text->SetText(Label);
	Text->SetColorAndOpacity(FSlateColor(SpacecraftPauseButtonText));
	FSlateFontInfo Font = Text->GetFont();
	Font.Size = 16;
	Text->SetFont(Font);
	Button->AddChild(Text);
	if (UVerticalBoxSlot* ButtonSlot =
		MenuBox->AddChildToVerticalBox(Button))
	{
		ButtonSlot->SetPadding(FMargin(0.f, 6.f, 0.f, 0.f));
		ButtonSlot->SetHorizontalAlignment(HAlign_Fill);
	}
}

void ULBSpacecraftPauseMenuWidget::HandleAction(FName Tag)
{
	if (Tag == FName(TEXT("Resume")))
	{
		if (GameMode != nullptr)
		{
			GameMode->TogglePauseMenu();
		}
		return;
	}
	if (Tag == FName(TEXT("Save")))
	{
		if (GameMode != nullptr)
		{
			// The outcome is SHOWN, not assumed. A save that silently
			// fails is worse than none - the player closes the game
			// believing their factory is safe.
			FString Reason;
			GameMode->QuickSave(Reason);
			SetStatusText(FText::FromString(Reason));
		}
		return;
	}
	if (Tag == FName(TEXT("Load")))
	{
		if (GameMode != nullptr)
		{
			FString Reason;
			const bool bLoaded = GameMode->QuickLoad(Reason);
			SetStatusText(FText::FromString(Reason));
			if (bLoaded)
			{
				// Back to the restored factory rather than leaving the
				// player staring at a menu over a world that has just
				// been replaced underneath it.
				GameMode->TogglePauseMenu();
			}
		}
		return;
	}
	if (Tag == FName(TEXT("Settings")))
	{
		if (GameMode != nullptr)
		{
			GameMode->OpenSettingsMenu();
		}
		return;
	}
	if (Tag == FName(TEXT("Restart")))
	{
		// Fresh level load: every authority reconstructs from scratch,
		// exactly like the first launch.
		UGameplayStatics::OpenLevel(this,
			FName(*UGameplayStatics::GetCurrentLevelName(this)));
		return;
	}
	if (Tag == FName(TEXT("Quit")))
	{
		UKismetSystemLibrary::QuitGame(GetWorld(),
			GetOwningPlayer(), EQuitPreference::Quit, false);
	}
}

#undef LOCTEXT_NAMESPACE
