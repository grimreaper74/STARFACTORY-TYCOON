#include "LBSpacecraftObjectivesWidget.h"

#include "Blueprint/WidgetTree.h"
#include "Components/Border.h"
#include "Components/BorderSlot.h"
#include "Components/CanvasPanel.h"
#include "Components/CanvasPanelSlot.h"
#include "Components/TextBlock.h"
#include "Components/VerticalBox.h"
#include "Components/VerticalBoxSlot.h"
#include "LBSpacecraftBuildAuthority.h"
#include "LBSpacecraftGameMode.h"
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
		SpacecraftObjectivesToken(TEXT("#918D8B"));   // Text.Dim
	const FLinearColor SpacecraftObjectiveDone =
		SpacecraftObjectivesToken(TEXT("#EDEDEC"));   // Text.Body
}

FString ULBSpacecraftObjectivesWidget::BuildObjectiveLine(
	int32 Delivered, int32 Needed, const FString& UnlockName)
{
	if (Delivered >= Needed)
	{
		return FString::Printf(TEXT("[DONE] %s"), *UnlockName);
	}
	return FString::Printf(TEXT("[%d/%d] %s"),
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
	Panel->SetBrushColor(SpacecraftObjectivesBackground);
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
		PadSlot->SetPadding(FMargin(14.f, 10.f));
	}
}

void ULBSpacecraftObjectivesWidget::AddLine(const FString& Text,
	bool bDone)
{
	using namespace LBSpacecraftObjectivesPrivate;
	UTextBlock* Block = WidgetTree->ConstructWidget<UTextBlock>(
		UTextBlock::StaticClass());
	Block->SetText(FText::FromString(Text));
	Block->SetColorAndOpacity(FSlateColor(bDone
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
		const bool bHasStation = GameMode->GetBuildAuthority() != nullptr
			&& GameMode->GetBuildAuthority()->GetStations().Num() > 0;
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
		AddLine(LOCTEXT("FirstSteps", "FIRST STEPS").ToString(), true);
		AddLine(LOCTEXT("StepStation",
			"Place assembly stations - the track connects them")
			.ToString(), bHasStation);
		AddLine(LOCTEXT("StepCommission", "Commission the factory")
			.ToString(), bCommissioned);
		AddLine(LOCTEXT("StepContract", "Accept a contract").ToString(),
			bHasAcceptedContract);
		AddLine(LOCTEXT("StepDeliver", "Deliver your first ship")
			.ToString(), false);
	}
	struct FLBSpacecraftObjectiveRow
	{
		int32 Needed;
		FText Name;
	};
	const FLBSpacecraftObjectiveRow Rows[] = {
		{ Progress->DeliveriesForBelts,
			LOCTEXT("UnlockBelts", "CONVEYOR BELTS") },
		{ Progress->DeliveriesForFabrication,
			LOCTEXT("UnlockFab", "ON-SITE FABRICATION") },
		{ Progress->DeliveriesForQuality,
			LOCTEXT("UnlockQA", "QUALITY CONTROL") } };
	for (const FLBSpacecraftObjectiveRow& Row : Rows)
	{
		AddLine(BuildObjectiveLine(Delivered, Row.Needed,
			Row.Name.ToString()), Delivered >= Row.Needed);
	}
	AddLine(FText::Format(LOCTEXT("Land", "LAND: {0} BAYS"),
		FText::AsNumber(Progress->GetOwnedBayCount()))
			.ToString(), false);
	AddLine(FText::Format(LOCTEXT("Delivered", "SHIPS DELIVERED: {0}"),
		FText::AsNumber(Delivered)).ToString(), Delivered > 0);
}

#undef LOCTEXT_NAMESPACE
