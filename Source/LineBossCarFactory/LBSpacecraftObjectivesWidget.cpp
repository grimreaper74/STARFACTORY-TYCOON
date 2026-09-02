#include "LBSpacecraftObjectivesWidget.h"

#include "Blueprint/WidgetTree.h"
#include "Brushes/SlateRoundedBoxBrush.h"
#include "Components/Border.h"
#include "Components/BorderSlot.h"
#include "Components/CanvasPanel.h"
#include "Components/CanvasPanelSlot.h"
#include "Components/TextBlock.h"
#include "Components/VerticalBox.h"
#include "Components/VerticalBoxSlot.h"
#include "LBSpacecraftBuildAuthority.h"
#include "LBSpacecraftGameMode.h"
#include "LBSpacecraftPlayerPawn.h"
#include "LBSpacecraftInventoryAuthority.h"
#include "LBSpacecraftProductionAuthority.h"
#include "LBSpacecraftProgressionAuthority.h"
#include "LBSpacecraftTrackAuthority.h"

#define LOCTEXT_NAMESPACE "LBSpacecraftObjectives"

namespace LBSpacecraftObjectivesPrivate
{
	// GRADED TO THE ADOPTED PALETTE (2026-08-29). The comment here used
	// to cite "Cold Steel law" and call these provisional; a palette
	// exists now and the interface carries no hue at all.
	//
	// DONE is not a colour change. Every other game would tick these
	// green, but green is a hue and the interface has none - so a
	// finished objective goes to full body white and an unfinished one
	// sits at dim. The palette makes the same point about positives
	// elsewhere: a light chip with dark text, never a green one.
	inline FLinearColor SpacecraftObjectivesToken(const TCHAR* Hex,
		float Alpha = 1.f)
	{
		FLinearColor Out = FLinearColor(FColor::FromHex(Hex));
		Out.A = Alpha;
		return Out;
	}
	const FLinearColor SpacecraftObjectivesBackground =
		SpacecraftObjectivesToken(TEXT("#1B1B1B"), 0.94f);
	const FLinearColor SpacecraftObjectiveOpen =
		SpacecraftObjectivesToken(TEXT("#EDEDEC"));   // Text.Body - to do
	const FLinearColor SpacecraftObjectiveDone =
		SpacecraftObjectivesToken(TEXT("#918D8B"));   // Text.Dim - done
}

FString ULBSpacecraftObjectivesWidget::BuildObjectiveLine(
	int32 Delivered, int32 Needed, const FString& UnlockName)
{
	if (Delivered >= Needed)
	{
		return FString::Printf(TEXT("\u2713 %s"), *UnlockName);
	}
	return FString::Printf(TEXT("%d/%d · %s"),
		FMath::Clamp(Delivered, 0, Needed), Needed, *UnlockName);
}

void ULBSpacecraftObjectivesWidget::BindGame(
	ALBSpacecraftGameMode* InGameMode)
{
	GameMode = InGameMode;
}

void ULBSpacecraftObjectivesWidget::NativeOnInitialized()
{
	Super::NativeOnInitialized();
	using namespace LBSpacecraftObjectivesPrivate;

	UCanvasPanel* Canvas = WidgetTree->ConstructWidget<UCanvasPanel>(
		UCanvasPanel::StaticClass(), TEXT("ObjectivesCanvas"));
	WidgetTree->RootWidget = Canvas;

	UBorder* Panel = WidgetTree->ConstructWidget<UBorder>(
		UBorder::StaticClass(), TEXT("ObjectivesRoot"));
	Panel->SetBrush(FSlateRoundedBoxBrush(SpacecraftObjectivesBackground, 6.f));
	if (UCanvasPanelSlot* PanelSlot = Canvas->AddChildToCanvas(Panel))
	{
		PanelSlot->SetAnchors(FAnchors(1.f, 0.f, 1.f, 0.f));
		PanelSlot->SetAlignment(FVector2D(1.f, 0.f));
		PanelSlot->SetPosition(FVector2D(-12.f, 56.f));
		PanelSlot->SetSize(FVector2D(320.f, 0.f));
		PanelSlot->SetAutoSize(true);
	}
	LadderBox = WidgetTree->ConstructWidget<UVerticalBox>(
		UVerticalBox::StaticClass());
	Panel->SetContent(LadderBox);
	if (UBorderSlot* PadSlot = Cast<UBorderSlot>(LadderBox->Slot))
	{
		PadSlot->SetPadding(FMargin(16.f, 12.f));
	}
}

void ULBSpacecraftObjectivesWidget::AddLine(const FString& Text,
	bool bDone)
{
	using namespace LBSpacecraftObjectivesPrivate;
	UTextBlock* Block = WidgetTree->ConstructWidget<UTextBlock>(
		UTextBlock::StaticClass());
	// A DONE STEP WEARS A TICK. Bright-versus-dim alone was decoded
	// both ways by twelve auditing readers of the packaged frames
	// (2026-09-02): the bright lines looked like open tasks. Headings
	// (the FIRST STEPS label, the tier names) pass bDone=true too, so
	// only lines that read as a task get the glyph.
	// FString's != ignores case, so "Place" != "PLACE" is FALSE and
	// every line read as a heading (nothing ticked, first try).
	const bool bTaskLine = !Text.IsEmpty()
		&& !Text.Equals(Text.ToUpper(), ESearchCase::CaseSensitive);
	Block->SetText(FText::FromString(bDone && bTaskLine
		? FString(TEXT("\u2713 ")) + Text : Text));
	// And the brightness is a TO-DO list: an open step is bright (the
	// thing to do next), a done step is dim and ticked; headings stay
	// bright. It used to be the other way round.
	Block->SetColorAndOpacity(FSlateColor(bDone && bTaskLine
		? SpacecraftObjectiveDone : SpacecraftObjectiveOpen));
	FSlateFontInfo Font = Block->GetFont();
	Font.Size = 13;
	Block->SetFont(Font);
	if (UVerticalBoxSlot* LineSlot =
		LadderBox->AddChildToVerticalBox(Block))
	{
		LineSlot->SetPadding(FMargin(0.f, 2.f, 0.f, 0.f));
	}
}

void ULBSpacecraftObjectivesWidget::NativeTick(
	const FGeometry& MyGeometry, float InDeltaTime)
{
	Super::NativeTick(MyGeometry, InDeltaTime);
	if (GameMode == nullptr || LadderBox == nullptr)
	{
		return;
	}
	FString Revision;
	if (ALBSpacecraftProgressionAuthority* Progress =
		GameMode->GetProgression())
	{
		Revision = FString::Printf(TEXT("%d/%d"),
			Progress->GetCreditedDeliveries(),
			Progress->GetOwnedBayCount());
	}
	bool bHasAcceptedContract = false;
	if (ALBSpacecraftProductionAuthority* Ledger =
		GameMode->GetProductionAuthority())
	{
		for (const FLBSpacecraftContract& Contract : Ledger->GetContracts())
		{
			if (Contract.State == ELBSpacecraftContractState::Accepted)
			{
				bHasAcceptedContract = true;
				break;
			}
		}
		Revision += FString::Printf(TEXT(";%d;%d"),
			Ledger->GetContracts().Num(), bHasAcceptedContract ? 1 : 0);
	}
	if (ALBSpacecraftBuildAuthority* Build = GameMode->GetBuildAuthority())
	{
		Revision += FString::Printf(TEXT(";%d;%d"),
			Build->GetStations().Num(), Build->IsCommissioned() ? 1 : 0);
	}
	if (ALBSpacecraftTrackAuthority* TrackAuthority =
		GameMode->GetTrackAuthority())
	{
		Revision += FString::Printf(TEXT(";t%d"),
			TrackAuthority->GetPieces().Num());
	}
	// The view is part of the revision: the site-map step below is
	// shown or hidden by where the player is, and a rebuild keyed on
	// authorities alone never noticed the pawn leave or enter the map.
	if (const ALBSpacecraftPlayerPawn* ViewPawn =
		Cast<ALBSpacecraftPlayerPawn>(GetOwningPlayerPawn()))
	{
		Revision += FString::Printf(TEXT(";v%d"),
			ViewPawn->IsSiteMapView() ? 1 : 0);
	}
	if (Revision == LastRevision)
	{
		return;
	}
	LastRevision = Revision;
	Rebuild();
}

void ULBSpacecraftObjectivesWidget::Rebuild()
{
	LadderBox->ClearChildren();
	AddLine(LOCTEXT("Title", "OBJECTIVES").ToString(), true);
	ALBSpacecraftProgressionAuthority* Progress =
		GameMode->GetProgression();
	if (Progress == nullptr)
	{
		return;
	}
	const int32 Delivered = Progress->GetCreditedDeliveries();

	// FIRST STEPS (2026-08-31, research doc: "no modal tutorial - a
	// rewarded objectives panel... retires permanently after contract
	// 1"). The unlock ladder below assumes the player already knows
	// what a station or a delivery IS; nothing told a brand-new player
	// what to click first. This block names the four concrete actions
	// that get a stranger to their first delivered ship, then vanishes
	// for good the moment that ship lands - it never reappears even if
	// the player later has zero stations or contracts again.
	if (Delivered <= 0)
	{
		// LINE stations only. The ship factory hall is a station record
		// too, so a fresh site with its pre-placed hall counted as
		// "stations placed", which hid the enter-the-factory step and
		// ticked the first step before the player had done anything
		// (packaged-frame audit, 2026-09-02).
		bool bHasStation = false;
		if (GameMode->GetBuildAuthority() != nullptr)
		{
			for (const FLBSpacecraftStationRecord& Record :
				GameMode->GetBuildAuthority()->GetStations())
			{
				const FLBSpacecraftStationDefinition* Definition =
					ALBSpacecraftBuildAuthority::FindDefinition(
						Record.DefinitionId);
				if (Definition != nullptr
					&& Definition->StageClassId == FName(TEXT("LineStation")))
				{
					bHasStation = true;
					break;
				}
			}
		}
		const bool bCommissioned = GameMode->GetBuildAuthority() != nullptr
			&& GameMode->GetBuildAuthority()->IsCommissioned();
		bool bHasAcceptedContract = false;
		if (ALBSpacecraftProductionAuthority* Ledger =
			GameMode->GetProductionAuthority())
		{
			for (const FLBSpacecraftContract& Contract :
				Ledger->GetContracts())
			{
				if (Contract.State == ELBSpacecraftContractState::Accepted)
				{
					bHasAcceptedContract = true;
					break;
				}
			}
		}
		// STATIONS ARE THE ONLY STEP (owner 2026-09-01: "cant we just
		// have the track autamaticly connect between stations?"). The
		// track step is gone because the track is no longer a player
		// action - the relayer routes it on every placement.
		// HIRE DRONES IS A TAUGHT STEP (overnight stranger run,
		// 2026-09-01): nothing told a new player that uncrewed
		// stations build dirty, and their first ship paid for it with
		// a nine-minute rework hold at the end of the line.
		// EVERY line station crewed, not any station (the step ticked
		// after one drone at one station, 2026-09-02); plus the two
		// steps a first ship actually needs that nothing named: a
		// delivery dock, and parts ordered in. The stranger lost the
		// first contract to the clock learning both from a stall toast.
		bool bAllLineCrewed = false;
		bool bHasDock = false;
		// THE BOOTH IS A TAUGHT STEP (stranger run through the real
		// panel, 2026-09-02): three crewed stations and a dock ticked
		// every line here, and "Commission the factory" refused with
		// "The line has no spray booth". The list had set the player
		// up to fail the step it was pointing at.
		bool bHasBooth = false;
		if (GameMode->GetBuildAuthority() != nullptr)
		{
			int32 LineStations = 0;
			int32 Uncrewed = 0;
			for (const FLBSpacecraftStationRecord& Record :
				GameMode->GetBuildAuthority()->GetStations())
			{
				const FLBSpacecraftStationDefinition* Definition =
					ALBSpacecraftBuildAuthority::FindDefinition(
						Record.DefinitionId);
				if (Definition == nullptr)
				{
					continue;
				}
				if (Definition->StageClassId == FName(TEXT("LineStation")))
				{
					++LineStations;
					if (Record.InstalledDroneTypes.Num() == 0)
					{
						++Uncrewed;
					}
				}
				bHasDock |= Record.DefinitionId
					== FName(TEXT("DeliveryDock"));
				bHasBooth |= !Definition->StageClassId.IsNone()
					&& Definition->bProcessStation;
			}
			bAllLineCrewed = LineStations > 0 && Uncrewed == 0;
		}
		const bool bHasParts = GameMode->GetInventoryAuthority() != nullptr
			&& GameMode->GetInventoryAuthority()->HasAnyStock();
		const bool bHasAnyDrone = bAllLineCrewed;
		AddLine(LOCTEXT("FirstSteps", "FIRST STEPS").ToString(), true);
		// ON THE SITE MAP the first thing to do is go inside. The bold
		// step read "Place assembly stations" on a screen where nothing
		// can be placed, and the only cue was the footer (packaged-frame
		// audit, 2026-09-02, F37). This line stands until the player
		// has entered the hall once and placed a station.
		const ALBSpacecraftPlayerPawn* ViewPawn =
			Cast<ALBSpacecraftPlayerPawn>(GetOwningPlayerPawn());
		if (ViewPawn != nullptr && ViewPawn->IsSiteMapView()
			&& !bHasStation)
		{
			AddLine(LOCTEXT("StepEnter",
				"Enter the ship factory - click it on the map")
				.ToString(), false);
		}
		AddLine(LOCTEXT("StepStation",
			"Place assembly stations - the track connects them")
			.ToString(), bHasStation);
		AddLine(LOCTEXT("StepBooth",
			"Add a spray booth to the line - every craft leaves in the customer's livery")
			.ToString(), bHasBooth);
		AddLine(LOCTEXT("StepCrew",
			"Hire drones at every station - uncrewed work is dirty")
			.ToString(), bHasAnyDrone);
		AddLine(LOCTEXT("StepDock",
			"Build a delivery dock - parts land there and its drone carries them to the line").ToString(),
			bHasDock);
		AddLine(LOCTEXT("StepCommission", "Commission the factory")
			.ToString(), bCommissioned);
		AddLine(LOCTEXT("StepContract", "Accept a contract").ToString(),
			bHasAcceptedContract);
		AddLine(LOCTEXT("StepParts",
			"Order the ship's parts (Contracts tab, imports)").ToString(),
			bHasParts);
		AddLine(LOCTEXT("StepDeliver", "Deliver your first ship")
			.ToString(), false);
	}
	// AFTER THE FIRST SHIP the steps retire, and the stranger run
	// (2026-09-02, F36) found nothing then named the next move while
	// the line sat idle with the offer board below the fold. One line,
	// only while it applies: no accepted order left to build.
	if (Delivered > 0 && GameMode->GetProductionAuthority() != nullptr)
	{
		const ALBSpacecraftProductionAuthority* Ledger =
			GameMode->GetProductionAuthority();
		bool bAnyOpenOrder = false;
		for (const FLBSpacecraftContract& Contract : Ledger->GetContracts())
		{
			if (Contract.State == ELBSpacecraftContractState::Accepted
				&& Contract.DispatchedCount < Contract.Quantity)
			{
				bAnyOpenOrder = true;
				break;
			}
		}
		if (!bAnyOpenOrder)
		{
			const int32 Stock = Ledger->GetStockedCraftCount();
			AddLine(Stock > 0
				? FText::Format(LOCTEXT("NextSellStock",
					"NEXT: accept a contract - {0} finished ship(s) sell the moment one is taken"),
					Stock).ToString()
				: LOCTEXT("NextAccept",
					"NEXT: accept a contract - the line is idle (Contracts tab)")
					.ToString(), false);
		}
	}
	struct FLBSpacecraftObjectiveRow
	{
		int32 Needed;
		FText Name;
	};
	const FLBSpacecraftObjectiveRow Rows[] = {
		{ Progress->DeliveriesForBelts,
			LOCTEXT("UnlockBelts", "Conveyor belts") },
		{ Progress->DeliveriesForFabrication,
			LOCTEXT("UnlockFab", "On-site fabrication") },
		{ Progress->DeliveriesForQuality,
			LOCTEXT("UnlockQA", "Quality control") } };
	for (const FLBSpacecraftObjectiveRow& Row : Rows)
	{
		AddLine(BuildObjectiveLine(Delivered, Row.Needed,
			Row.Name.ToString()), Delivered >= Row.Needed);
	}
	AddLine(FText::Format(LOCTEXT("Land", "Land: {0} bays"),
		FText::AsNumber(Progress->GetOwnedBayCount()))
			.ToString(), false);
	AddLine(FText::Format(LOCTEXT("Delivered", "Ships delivered: {0}"),
		FText::AsNumber(Delivered)).ToString(), Delivered > 0);
}

#undef LOCTEXT_NAMESPACE
