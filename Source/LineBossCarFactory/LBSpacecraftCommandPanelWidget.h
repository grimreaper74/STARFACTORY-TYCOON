// Spacecraft-era command panel: the player-facing UI for building the
// factory, picking recipes, accepting contracts and unlocking research.
// Native UMG, code-only, provisional indicator colours (no brand). A thin
// projection over the SAME authority calls the console commands use -
// every fail-closed refusal string is shown to the player verbatim.

#pragma once

#include "CoreMinimal.h"
#include "Blueprint/UserWidget.h"
#include "Components/Button.h"
#include "LBSpacecraftCommandPanelWidget.generated.h"

class UTextBlock;
class UVerticalBox;
class ALBSpacecraftGameMode;
class ALBSpacecraftPlayerPawn;

/** A button carrying a payload tag, forwarding clicks natively. */
UCLASS()
class LINEBOSSCARFACTORY_API ULBSpacecraftTaggedButton : public UButton
{
	GENERATED_BODY()

public:
	FName Tag;
	TFunction<void(FName)> OnTagClicked;

	void Arm()
	{
		OnClicked.AddUniqueDynamic(this,
			&ULBSpacecraftTaggedButton::HandleClicked);
	}

private:
	UFUNCTION()
	void HandleClicked()
	{
		if (OnTagClicked)
		{
			OnTagClicked(Tag);
		}
	}
};

UENUM()
enum class ELBSpacecraftPanelTab : uint8
{
	Build,
	Contracts,
	Research
};

UCLASS()
class LINEBOSSCARFACTORY_API ULBSpacecraftCommandPanelWidget
	: public UUserWidget
{
	GENERATED_BODY()

public:
	/** Cycles BUILD/CONTRACTS/RESEARCH (Tab / Shift+Tab). */
	void CycleTab(int32 Direction);

	/** Scrolls the panel by a fraction of its length, 0 top to 1
	 *  bottom. The build and contracts tabs are far longer than the
	 *  viewport, so a capture of anything below the fold - the refit
	 *  sections among them - is otherwise impossible to take. */
	void ScrollContentToFraction(float Fraction);

	/** Which tab is showing, as the word the player sees. Public so a
	 *  headless capture can steer to one without reaching into the
	 *  widget's state. */
	FString GetActiveTabName() const
	{
		switch (ActiveTab)
		{
		case ELBSpacecraftPanelTab::Build: return TEXT("BUILD");
		case ELBSpacecraftPanelTab::Contracts: return TEXT("CONTRACTS");
		default: return TEXT("RESEARCH");
		}
	}

	void BindGame(ALBSpacecraftGameMode* InGameMode,
		ALBSpacecraftPlayerPawn* InPawn);

	// ---- pure, testable label builders ----
	/** "Rolling mill Mk1  £60,000  400 kW" from a catalogue definition. */
	static FString BuildStationButtonLabel(FName DefinitionId);

	/** "Heavy Station Marks  (60 pts)" or "... UNLOCKED". */
	/** Which build-menu group a station belongs in, DERIVED from what
	 *  the definition is rather than from a list of names. The list
	 *  rotted the moment new buildings appeared: the delivery dock,
	 *  the power station and the sub-assembly hall all silently filed
	 *  themselves under CRAFTING CHAIN, where nobody would look for
	 *  them. 0 production line, 1 heavy marks, 2 crafting chain,
	 *  3 infrastructure. */
	/** Pure: the line describing craft standing in finished stock -
	 *  built, unsold, and ready to fill an order the moment one is
	 *  taken. Empty when there is none. Without it the player has
	 *  stock and no way to know, which makes an offer they could fill
	 *  instantly look like work. */
	static FString BuildFinishedStockLine(FName RecipeId, int32 Count);

	static int32 BuildMenuGroupFor(
		const struct FLBSpacecraftStationDefinition& Definition);

	static FString BuildResearchButtonLabel(FName NodeId, bool bUnlocked);

	/** Pure: one line describing a contract you hold - what it is, how
	 *  much of it is delivered, and what it pays. Until this existed
	 *  the Contracts tab showed offers and orders but never the work
	 *  you had actually taken on. */
	static FString BuildHeldContractLine(const struct FLBSpacecraftContract&
		Contract, double SimSeconds = 0.0);

	/** Pure: the label for an offer on the board - craft, quantity,
	 *  unit price and what the whole order is worth. */
	static FString BuildOfferButtonLabel(const struct FLBSpacecraftContract&
		Offer, double SimSeconds = 0.0);

	/** Pure: "4h 12m" of sim time left, or "LATE". A deadline nobody
	 *  can see is an ambush, not a decision. */
	static FString FormatTimeRemaining(double SecondsRemaining);

protected:
	virtual void NativeOnInitialized() override;
	virtual void NativeTick(const FGeometry& MyGeometry,
		float InDeltaTime) override;

private:
	UPROPERTY()
	TObjectPtr<ALBSpacecraftGameMode> GameMode;

	UPROPERTY()
	TObjectPtr<ALBSpacecraftPlayerPawn> Pawn;

	UPROPERTY()
	TObjectPtr<UVerticalBox> ContentBox;

	/** The panel's scroller. Held so switching tabs can return it to the
	 *  top: the box is built once and only its CONTENTS are rebuilt, so
	 *  the offset survives a refresh and a tab can open part-scrolled -
	 *  which hid the "SHIP FACTORY" heading and the first station on it. */
	UPROPERTY(Transient)
	TObjectPtr<class UScrollBox> ContentScroll;

	UPROPERTY()
	TObjectPtr<UTextBlock> ToastBlock;

	UPROPERTY()
	TObjectPtr<class UBorder> ToastBorder;

	UPROPERTY()
	TArray<TObjectPtr<ULBSpacecraftTaggedButton>> TabButtons;

	UPROPERTY()
	TArray<TObjectPtr<UTextBlock>> TabTexts;

	ELBSpacecraftPanelTab ActiveTab = ELBSpacecraftPanelTab::Build;
	FString LastRevision;

	/** Rebuild throttle (see NativeTick): churn insurance only. */
	float SecondsSinceRebuild = 1.f;
	FString PanelActionText;

	/** Toast aging (audit 2026-09-01): action text that has stood
	 *  unchanged for a few seconds yields the toast to a live sim
	 *  alert - the strings themselves are never cleared, and the
	 *  empty-only gate masked every stall alert for good. */
	FString ToastLastComposed;
	double ToastComposedAt = 0.0;

	/** A small fingerprint of everything the lists render; a change
	 *  triggers a rebuild (buttons are not thrashed every frame). */
	FString ComputeRevision() const;
	void RebuildContent();
	void AddSectionLabel(const FString& Text);
	ULBSpacecraftTaggedButton* AddTaggedButton(const FString& Label,
		FName InTag, TFunction<void(FName)> Handler,
		const FString& SubLabel = FString(), bool bSubWarn = false,
		bool bArmed = false);
	void RefreshTabStyles();

	void HandleTab(FName TabTag);
	void ScrollContentToTop();

	void HandleBuildStation(FName DefinitionId);
	void HandleSelectRecipe(FName RecipeId);
	void HandleRemoveStation(FName StationId);
	void HandleBelt(FName StationId);
	/** THE BOARD's two dispositions. The third - rework - needs no
	 *  button: it is what happens when the player does nothing. */
	/** REFIT: offer work on a craft this yard delivered, and put an
	 *  accepted refit back on the line. */
	/**
	 * Which craft the line is actually working to.
	 *
	 * The fixing split is PER RECIPE - which station fits what depends
	 * entirely on the craft - and three call sites asked for SCOUT-01
	 * by name. With two tiers shipped that already showed the wrong
	 * split whenever a Cargo was on the line, and under a ladder of
	 * eight roles it would have been wrong most of the time.
	 *
	 * The craft in flight wins, because that is the one the stations
	 * are holding parts for; failing that the oldest accepted order,
	 * which is what they will be holding parts for next.
	 */
	FName LineRecipeId() const;

	void HandleOfferRefit(FName UnitId);
	void HandleStartRefit(FName ContractId);

	void HandleConcede(FName UnitId);
	void HandleScrap(FName UnitId);

	void HandleBuyBay(FName Unused);
	void HandleSplitTake(FName StationId);
	void HandleSplitGive(FName StationId);

public:
	/** The sections the BUILD tab can draw. */
	enum class EBuildSection : uint8
	{
		/** Placeable buildings or stations, whichever the view owns. */
		Catalogue,
		/** THE LINE - which station fits which parts. */
		FixingSplit,
		/** LAND - bays owned, and buying the next one. */
		Land,
		/** LINE TRACK - laying and removing track pieces. */
		Track,
		/** THE BOARD - what to do with a craft that failed its test. */
		MaterialReview,
		/** SESSION - saving and resuming. Belongs in BOTH views: a
		 *  player standing on the world map must be able to stop just
		 *  as much as one on the factory floor, and a save button that
		 *  is only reachable from one screen is a save button people
		 *  fail to find. */
		Session,
	};

	/**
	 * Does this section belong in this view?
	 *
	 * OUTSIDE and INSIDE are different games and their menus never mix.
	 * That rule was being applied to the catalogue alone and assumed
	 * everywhere else, so the world map drew "THE LINE - WHO FITS WHAT"
	 * and a track-laying menu over a site with no factory entered - and
	 * a factory interior offered to sell land the player could not see.
	 *
	 * The same shape of fault - a view gate applied in one place and
	 * assumed in the rest - is what shipped a build that could not be
	 * started at all. Stating the rule ONCE, as a pure function the
	 * tests can reach without a widget, is the cheapest defence against
	 * it happening a third time.
	 */
	static bool SectionBelongsInView(EBuildSection Section, bool bOnSiteMap);

	/** Move one part across the boundary between station FromIndex and
	 *  its neighbour: the counts array adjusted, or empty when the move
	 *  is impossible (source empty, index off the line). Pure and
	 *  PUBLIC so the split arithmetic is testable without a widget. */
	static TArray<int32> ComputeSplitShift(const TArray<int32>& Counts,
		int32 FromIndex, int32 ToIndex);

private:
	void HandleImport(FName ItemId);
	void HandleRemoveBelt(FName RouteId);
	void HandleCommission(FName Unused);
	void HandleContract(FName RecipeId);
	void HandleAcceptOffer(FName ContractId);
	void HandleOrder(FName ItemId);
	/** Cycles the buy quantity 1 -> 5 -> 20 -> 1. Every order button
	 *  multiplies by it, so stocking up for a long run is one click per
	 *  item instead of twenty (owner 2026-08-29: "you couldn't just buy
	 *  parts for 20 ships in one click"). */
	void HandleCycleBuyMultiplier(FName Unused);

	/** How many lots each order button buys. Not saved: it is a
	 *  shopping convenience, not game state. */
	int32 BuyMultiplier = 1;
	void HandleResearch(FName NodeId);
	void HandleInstallUnit(FName UnitDefinitionId);
	void HandleOrderParts(FName StationId);
	void HandleInstallDrone(FName StationId);
	/** Hires one drone OF A CHOSEN KIND into the selected station
	 *  (owner 2026-08-28: pick what drones you want). */
	void HandleInstallDroneKind(FName KindId);
	/** Dismisses the drone in a slot, refunding half. */
	void HandleDismissDrone(FName SlotTag);
	void HandleToggleAllocation(FName ComponentItemId);

	/** SAVE GAME - writes layout, ledger and runtime to slot 1.
	 *
	 *  The pipeline behind this has been built and tested for a long
	 *  time; it simply had no button, so a player could not stop and
	 *  come back. */
	void HandleQuickSave();

	/** LOAD GAME - restores slot 1.
	 *
	 *  Restore validates the WHOLE snapshot before mutating anything, so
	 *  a corrupt or stale save is refused with a reason rather than
	 *  half-applied over a working factory. */
	void HandleQuickLoad();
};
