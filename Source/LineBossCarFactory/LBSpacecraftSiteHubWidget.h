// Copyright Epic Games, Inc. All Rights Reserved.

#pragma once

#include "CoreMinimal.h"
#include "Blueprint/UserWidget.h"
#include "LBSpacecraftSiteHubWidget.generated.h"

class UCanvasPanel;
class UImage;
class UTextBlock;
class UButton;
class ALBSpacecraftGameMode;
class ALBSpacecraftPlayerPawn;

/**
 * ONE PLACE ON THE HUB PICTURE.
 *
 * The rectangle is stored NORMALISED against the artwork, not in
 * pixels, so it survives the picture being replaced at a different
 * resolution and maps straight onto a canvas anchor. The numbers were
 * read off the labelled reference the artist supplied beside the clean
 * scene, then checked by drawing them back over the clean image - not
 * estimated from a description.
 */
USTRUCT()
struct FLBSpacecraftHubPlace
{
	GENERATED_BODY()

	/** Stable id for this place, used in logs and tests. */
	UPROPERTY()
	FName PlaceId;

	/** What the player is told they are looking at. */
	UPROPERTY()
	FText DisplayName;

	/** The build-catalogue definition this place stands for, if the game
	 *  has one yet. None means the place is drawn but not implemented -
	 *  it padlocks and says so honestly rather than pretending. */
	UPROPERTY()
	FName DefinitionId;

	/** The milestone this place waits on, if any. A place the player
	 *  cannot build YET must padlock rather than show a plus - a plus
	 *  invites a click that can only be refused, and the owner's rule
	 *  is that unavailable places padlock. -1 means no gate. */
	UPROPERTY()
	int32 RequiredUnlock = -1;

	/** WHERE THE BUILDING STANDS ON THE SITE, in world centimetres.
	 *  The hub is a fixed picture, so a place the player builds from it
	 *  has a fixed spot rather than a cursor to drop it with. Only the
	 *  places that can actually be built need one. */
	UPROPERTY()
	FVector2D SiteAtCm = FVector2D::ZeroVector;

	/** Normalised 0..1 rectangle over the artwork. */
	UPROPERTY()
	FVector2D Min = FVector2D::ZeroVector;

	UPROPERTY()
	FVector2D Max = FVector2D::ZeroVector;
};

/**
 * THE SITE HUB - the game's outer screen.
 *
 * One painted picture of the whole plant with clickable places over it
 * (owner 2026-08-29: "I thought it would just be a picture that you
 * could click on"). It replaces the 3D site view, which he judged had
 * "not had much luck... its been a mess".
 *
 * Places the player cannot use are shown DIMMED WITH A PADLOCK rather
 * than hidden. That is deliberately the opposite of the build menu,
 * which lists only what can be built right now: a menu is a list of
 * actions and offering an impossible one is a lie, while a map is a
 * picture of the world and a locked door on it is information. Actions
 * hide, places padlock.
 */
UCLASS()
class LINEBOSSCARFACTORY_API ULBSpacecraftSiteHubWidget : public UUserWidget
{
	GENERATED_BODY()

public:
	explicit ULBSpacecraftSiteHubWidget(
		const FObjectInitializer& ObjectInitializer);

	void BindGame(ALBSpacecraftGameMode* InGameMode);

	/** The twelve places, in the order the artwork lays them out.
	 *  Static so a test can check the table without a live widget -
	 *  overlapping or out-of-bounds rectangles are a bug a human will
	 *  never reliably spot by clicking. */
	static const TArray<FLBSpacecraftHubPlace>& Places();

	/** Which place a normalised point falls in, or None. The SMALLEST
	 *  containing rectangle wins, so a little building drawn in front of
	 *  a big one still takes its own clicks. */
	static FName PlaceAt(const FVector2D& NormalisedPoint);

	/** What a place can offer the player right now. */
	enum class EState : uint8
	{
		/** The building stands: click to go in. No badge. */
		Open,
		/** The game has this building and it is not built yet: click to
		 *  build it. Shows a PLUS, not a padlock - a padlock would say
		 *  "come back later" about something you can do this second. */
		Buildable,
		/** Drawn so the player can see where it will stand, but the
		 *  game does not have it yet. Padlocked, and says so plainly. */
		Locked
	};

	EState StateOf(FName PlaceId) const;

	/** True when the player may enter this place now - the building it
	 *  stands for exists on the site. */
	bool IsPlaceOpen(FName PlaceId) const;

	/** What clicking a place did, in plain words, for the status line
	 *  and for headless tests. */
	FString EnterPlace(FName PlaceId);

	virtual TSharedRef<SWidget> RebuildWidget() override;
	virtual void NativeTick(const FGeometry& MyGeometry,
		float InDeltaTime) override;

private:
	void RebuildContent();

	UPROPERTY()
	TObjectPtr<ALBSpacecraftGameMode> GameMode;

	UPROPERTY()
	TObjectPtr<UCanvasPanel> Root;

	UPROPERTY()
	TObjectPtr<UTextBlock> StatusText;

	/** Rebuilt when the set of open places changes, not every frame. */
	FString OpenSignature;

	/** Two-click purchase on the picture: the first click on a
	 *  buildable place quotes the price, the second within a few
	 *  seconds buys. A stranger's first click on the "+" (2026-09-02)
	 *  was an attempt to ENTER and cost 200,000 cr on the spot. */
	FName PendingBuyPlace;
	double PendingBuyStamp = 0.0;
};
