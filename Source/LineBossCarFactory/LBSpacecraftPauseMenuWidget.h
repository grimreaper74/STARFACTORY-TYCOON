// Spacecraft-era pause menu (owner request 2026-08-25: "how do I
// restart, settings doesn't work"). Native UMG, code-only: Resume,
// Restart (reloads the level fresh), Quit. Opened with Escape; the game
// mode owns show/hide and the pause state.

#pragma once

#include "CoreMinimal.h"
#include "Blueprint/UserWidget.h"
#include "LBSpacecraftPauseMenuWidget.generated.h"

class ALBSpacecraftGameMode;
class UVerticalBox;

UCLASS()
class LINEBOSSCARFACTORY_API ULBSpacecraftPauseMenuWidget
	: public UUserWidget
{
	GENERATED_BODY()

public:
	void BindGame(ALBSpacecraftGameMode* InGameMode);

protected:
	virtual void NativeOnInitialized() override;

private:
	UPROPERTY()
	TObjectPtr<ALBSpacecraftGameMode> GameMode;

	UPROPERTY()
	TObjectPtr<UVerticalBox> MenuBox;

	/** The line under the buttons that reports what just happened.
	 *
	 *  Save and load both report through here, success as well as
	 *  failure. A save that silently fails is worse than no save at
	 *  all: the player closes the game believing their factory is
	 *  safe. */
	UPROPERTY()
	TObjectPtr<class UTextBlock> StatusText;

	void SetStatusText(const FText& Text);
	void AddMenuButton(const FText& Label, FName Tag);
	void HandleAction(FName Tag);
};
