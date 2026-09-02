#include "LBSpacecraftCommandPanelWidget.h"

#include "Blueprint/WidgetTree.h"
#include "Components/Border.h"
#include "Components/BorderSlot.h"
#include "Components/CanvasPanel.h"
#include "Components/CanvasPanelSlot.h"
#include "Components/HorizontalBox.h"
#include "Components/HorizontalBoxSlot.h"
#include "Components/ScrollBox.h"
#include "Components/TextBlock.h"
#include "Components/VerticalBox.h"
#include "Components/VerticalBoxSlot.h"
#include "LBSpacecraftCraftingAuthority.h"
#include "LBSpacecraftInventoryAuthority.h"
#include "LBSpacecraftGameMode.h"
#include "LBSpacecraftTransportAuthority.h"
#include "LBSpacecraftTrackAuthority.h"
#include "LBSpacecraftProgressionAuthority.h"
#include "LBSpacecraftProductionAuthority.h"
#include "LBSpacecraftProductionTypes.h"
#include "LBSpacecraftPlayerPawn.h"
#include "LBSpacecraftTopBarWidget.h"
#include "Brushes/SlateRoundedBoxBrush.h"
#include "Components/Image.h"
#include "Engine/Texture2D.h"
#include "Styling/SlateTypes.h"

#define LOCTEXT_NAMESPACE "LBSpacecraftPanel"

namespace LBSpacecraftCommandPanelPrivate
{
	// GRADED TO THE ADOPTED PALETTE. The comment here used to say "no
	// brand exists yet" and the colours were blue - a blue-tinted
	// panel, blue-grey sub-text and a light blue accent. A brand was
	// adopted on 2026-08-29 and it makes those wrong on purpose:
	//
	//   "No world surface may be both bright and saturated, and only
	//    ONE of the interface and the machinery is allowed to have a
	//    hue at all."
	//
	// The machinery has the hue - amber housings, cool working
	// indicators - so the interface has none. #EC3013 is the single
	// exception and it is reserved for refusal, which is the one thing
	// in this game that must never be mistaken for anything else.
	//
	// Written as sRGB hex and converted, rather than as hand-computed
	// linear floats, so these read as the same values the palette
	// document states and cannot drift from it by arithmetic.
	auto Token = [](const TCHAR* Hex, float Alpha = 1.f)
	{
		FLinearColor Out = FLinearColor(FColor::FromHex(Hex));
		Out.A = Alpha;
		return Out;
	};
	const FLinearColor SpacecraftPanelBackground =
		Token(TEXT("#1B1B1B"), 0.94f);              // Panel.Bg
	const FLinearColor SpacecraftPanelText =
		Token(TEXT("#EDEDEC"));                     // Text.Body
	const FLinearColor SpacecraftPanelSubText =
		Token(TEXT("#918D8B"));                     // Text.Dim
	const FLinearColor SpacecraftPanelAccent =
		Token(TEXT("#A8A4A1"));                     // Text.Heading
	// REFUSAL, the only hue the interface is allowed.
	const FLinearColor SpacecraftPanelWarn = Token(TEXT("#EC3013"));
	const FLinearColor SpacecraftPanelToast = Token(TEXT("#EDEDEC"));
	const FLinearColor SpacecraftPanelButton =
		Token(TEXT("#232322"));                     // Panel.BgRaised
	const FLinearColor SpacecraftPanelButtonHover =
		Token(TEXT("#363433"));                     // Panel.Rule
	const FLinearColor SpacecraftPanelButtonPress =
		Token(TEXT("#4A4744"));
	const FLinearColor SpacecraftPanelButtonArmed =
		Token(TEXT("#363433"));

	const TCHAR* SpacecraftPanelIconRoot = TEXT(
		"/Game/LineBoss/Candidates/Spacecraft/StationMeshes_v001/UI");

	/** Icon texture for a catalogue tag: model renders for stations,
	 *  drones and craft, badge monograms for chain items. Nullptr when
	 *  the icon asset is absent - the button simply has no image. */
	UTexture2D* SpacecraftPanelIconForTag(FName InTag)
	{
		if (InTag.IsNone())
		{
			return nullptr;
		}
		FString Key = InTag.ToString();
		Key.ReplaceInline(TEXT("."), TEXT("_"));
		Key.ReplaceInline(TEXT("-"), TEXT("_"));
		// STATION INSTANCES SHARE THEIR CLASS ICON: AssemblyRobot_002
		// draws with the AssemblyRobot artwork. Without this strip,
		// every PLACED station tried a per-instance texture and logged
		// a failed load on every panel rebuild (owner's log flooded,
		// 2026-09-01).
		int32 DigitsEnd = Key.Len();
		while (DigitsEnd > 0 && FChar::IsDigit(Key[DigitsEnd - 1]))
		{
			--DigitsEnd;
		}
		if (DigitsEnd < Key.Len() && DigitsEnd > 0
			&& Key[DigitsEnd - 1] == TEXT('_'))
		{
			Key = Key.Left(DigitsEnd - 1);
		}
		if (Key.IsEmpty())
		{
			return nullptr;
		}
		// A missing icon costs ONE warning per session, not one per
		// rebuild: misses are remembered and never re-tried.
		static TSet<FString> SpacecraftPanelIconMisses;
		if (SpacecraftPanelIconMisses.Contains(Key))
		{
			return nullptr;
		}
		auto LoadIcon = [](const FString& ForKey) -> UTexture2D*
		{
			return LoadObject<UTexture2D>(nullptr, *FString::Printf(
				TEXT("%s/T_LB_Icon_%s.T_LB_Icon_%s"),
				SpacecraftPanelIconRoot, *ForKey, *ForKey));
		};
		if (UTexture2D* Exact = LoadIcon(Key))
		{
			return Exact;
		}
		// A MARK FALLS BACK TO ITS BASE. Eleven of the catalogue's
		// missing icons were Mk2 marks whose Mk1 icon already existed,
		// so the build menu drew blank buttons for machines it had
		// perfectly good artwork for. A mark is the same machine built
		// bigger - it does not need its own drawing, and drawing one
		// per mark would double the icon set every time a mark is
		// added.
		//
		// Deliberately only ONE step: AssemblyRobotMk2 falls back to
		// AssemblyRobot, and stops. Chaining would let an unrelated key
		// resolve to something misleading, and a wrong icon is worse
		// than none - a blank button says "not drawn yet" honestly.
		if (Key.EndsWith(TEXT("Mk2"), ESearchCase::CaseSensitive))
		{
			const FString BaseKey = Key.LeftChop(3);
			if (!BaseKey.IsEmpty())
			{
				return LoadIcon(BaseKey);
			}
		}
		return nullptr;
	}

	/** THE PLAYER NEVER READS AN INTERNAL ID (owner 2026-09-01: "the
	 *  ui has got to be really easy to use"). Any station id inside a
	 *  player-facing string becomes its display name plus number -
	 *  "AssemblyRobot-002" reads as "Assembly station Mk1 2". Applied
	 *  at the display chokepoints, so every authority keeps precise
	 *  ids internally and refusal strings stay grep-able in logs. */
	FString SpacecraftPrettifyStationIds(const FString& In,
		const ALBSpacecraftBuildAuthority* Build)
	{
		if (Build == nullptr || In.IsEmpty())
		{
			return In;
		}
		FString Out = In;
		for (const FLBSpacecraftStationRecord& Record :
			Build->GetStations())
		{
			const FString Id = Record.StationId.ToString();
			if (!Out.Contains(Id))
			{
				continue;
			}
			const FLBSpacecraftStationDefinition* Definition =
				ALBSpacecraftBuildAuthority::FindDefinition(
					Record.DefinitionId);
			FString Friendly = Definition != nullptr
				? Definition->DisplayName
				: Record.DefinitionId.ToString();
			int32 DashAt = INDEX_NONE;
			if (Id.FindLastChar(TEXT('-'), DashAt)
				&& DashAt + 1 < Id.Len())
			{
				const int32 AsNumber = FCString::Atoi(*Id.Mid(DashAt + 1));
				if (AsNumber > 0)
				{
					Friendly = FString::Printf(TEXT("%s %d"), *Friendly,
						AsNumber);
				}
			}
			Out.ReplaceInline(*Id, *Friendly);
		}
		return Out;
	}

	/** Graphite rounded button; the armed variant carries the blue
	 *  working-indicator fill (selected tab, armed placement). */
	FButtonStyle SpacecraftPanelButtonStyle(bool bArmed)
	{
		FButtonStyle Style;
		const FLinearColor Base =
			bArmed ? SpacecraftPanelButtonArmed : SpacecraftPanelButton;
		Style.SetNormal(FSlateRoundedBoxBrush(Base, 4.f));
		Style.SetHovered(
			FSlateRoundedBoxBrush(SpacecraftPanelButtonHover, 4.f));
		Style.SetPressed(
			FSlateRoundedBoxBrush(SpacecraftPanelButtonPress, 4.f));
		Style.SetDisabled(FSlateRoundedBoxBrush(
			FLinearColor(0.06f, 0.065f, 0.075f), 4.f));
		Style.SetNormalPadding(FMargin(10.f, 6.f));
		Style.SetPressedPadding(FMargin(10.f, 7.f, 10.f, 5.f));
		return Style;
	}
}

void ULBSpacecraftCommandPanelWidget::BindGame(
	ALBSpacecraftGameMode* InGameMode, ALBSpacecraftPlayerPawn* InPawn)
{
	GameMode = InGameMode;
	Pawn = InPawn;
	LastRevision.Reset();
}

FString ULBSpacecraftCommandPanelWidget::BuildStationButtonLabel(
	FName DefinitionId)
{
	const FLBSpacecraftStationDefinition* Definition =
		ALBSpacecraftBuildAuthority::FindDefinition(DefinitionId);
	if (Definition == nullptr)
	{
		return FString();
	}
	FString Label = FString::Printf(TEXT("%s  %s"),
		*Definition->DisplayName,
		*ULBSpacecraftTopBarWidget::FormatCurrency(
			Definition->CostPence));
	if (Definition->PowerDrawKw > 0)
	{
		Label += FString::Printf(TEXT("  %d kW"), Definition->PowerDrawKw);
	}
	if (Definition->PowerSupplyKw > 0)
	{
		Label += FString::Printf(TEXT("  +%d kW"),
			Definition->PowerSupplyKw);
	}
	return Label;
}

FString ULBSpacecraftCommandPanelWidget::FormatTimeRemaining(
	double SecondsRemaining)
{
	if (SecondsRemaining <= 0.0)
	{
		return LOCTEXT("ContractLate", "Late").ToString();
	}
	const int32 Whole = FMath::FloorToInt(SecondsRemaining);
	const int32 Hours = Whole / 3600;
	const int32 Minutes = (Whole % 3600) / 60;
	return Hours > 0
		? FText::Format(LOCTEXT("ContractHoursLeft", "{0}h {1}m left"),
			Hours, Minutes).ToString()
		: FText::Format(LOCTEXT("ContractMinutesLeft", "{0}m left"),
			FMath::Max(Minutes, 1)).ToString();
}

FString ULBSpacecraftCommandPanelWidget::BuildHeldContractLine(
	const FLBSpacecraftContract& Contract, double SimSeconds)
{
	const FText State =
		Contract.State == ELBSpacecraftContractState::Expired
			? LOCTEXT("HeldExpired", "Late")
			: (Contract.State == ELBSpacecraftContractState::Offered
				? LOCTEXT("HeldOffered", "Offered")
				: LOCTEXT("HeldBuilding", "Building"));
	// The clock, when there is one to show.
	FString Clock;
	if (Contract.DeadlineSimSeconds > 0.0
		&& Contract.State != ELBSpacecraftContractState::Expired)
	{
		Clock = FString(TEXT("  "))
			+ FormatTimeRemaining(Contract.DeadlineSimSeconds - SimSeconds);
	}
	const FLBSpacecraftCustomer* Buyer =
		FLBSpacecraftCustomerCatalogue::FindCustomer(Contract.CustomerId);
	const FString Who = Buyer != nullptr
		? Buyer->DisplayName + TEXT(" - ") : FString();
	return FText::Format(
		LOCTEXT("HeldContractLine", "{6}{0}  {1}  {2}/{3}  {4} each{5}"),
		FText::FromName(Contract.RecipeId), State,
		Contract.DispatchedCount, Contract.Quantity,
		FText::FromString(ULBSpacecraftTopBarWidget::FormatCurrency(
			Contract.PricePerUnitPence)),
		FText::FromString(Clock),
		FText::FromString(Who)).ToString();
}

FString ULBSpacecraftCommandPanelWidget::BuildFinishedStockLine(
	FName RecipeId, int32 Count)
{
	if (Count <= 0)
	{
		return FString();
	}
	return FText::Format(
		LOCTEXT("FinishedStockLine", "{0}  x{1}  built, ready to sell"),
		FText::FromName(RecipeId), Count).ToString();
}

int32 ULBSpacecraftCommandPanelWidget::BuildMenuGroupFor(
	const FLBSpacecraftStationDefinition& Definition)
{
	// SITE BUILDINGS are the world map's own catalogue and never mix
	// with the factory's (owner 2026-08-28).
	if (Definition.bSiteBuilding)
	{
		return 4;
	}
	// A BIGGER MARK of anything is a heavy mark: it points at the mark
	// below it, or its id says so for the route stations.
	const bool bHeavyMark = !Definition.RecipeClassId.IsNone()
		|| Definition.DefinitionId.ToString().EndsWith(TEXT("Mk2"));
	if (bHeavyMark)
	{
		return 1;
	}
	// A ROUTE station services a production stage.
	if (!Definition.StageClassId.IsNone())
	{
		return 0;
	}
	// A PARTS MACHINE is one that actually crafts something.
	if (FLBSpacecraftRecipeCatalogue::GetRecipesForStationClass(
		Definition.GetRecipeClassId()).Num() > 0)
	{
		return 2;
	}
	// Everything else - generators, their halls, storage, the delivery
	// dock - is infrastructure.
	return 3;
}

FString ULBSpacecraftCommandPanelWidget::BuildResearchButtonLabel(
	FName NodeId, bool bUnlocked)
{
	const FLBSpacecraftResearchNode* Node =
		FLBSpacecraftResearchCatalogue::FindNode(NodeId);
	if (Node == nullptr)
	{
		return FString();
	}
	// Catalogue display names localize in a later string-table pass.
	return bUnlocked
		? FText::Format(LOCTEXT("ResearchUnlocked", "{0}  unlocked"),
			FText::FromString(Node->DisplayName)).ToString()
		: FText::Format(LOCTEXT("ResearchCost", "{0}  ({1} pts)"),
			FText::FromString(Node->DisplayName),
			Node->CostPoints).ToString();
}

void ULBSpacecraftCommandPanelWidget::NativeOnInitialized()
{
	Super::NativeOnInitialized();
	using namespace LBSpacecraftCommandPanelPrivate;

	UCanvasPanel* Canvas = WidgetTree->ConstructWidget<UCanvasPanel>(
		UCanvasPanel::StaticClass(), TEXT("PanelCanvas"));
	WidgetTree->RootWidget = Canvas;

	UBorder* Panel = WidgetTree->ConstructWidget<UBorder>(
		UBorder::StaticClass(), TEXT("PanelRoot"));
	Panel->SetBrushColor(SpacecraftPanelBackground);
	if (UCanvasPanelSlot* PanelSlot = Canvas->AddChildToCanvas(Panel))
	{
		PanelSlot->SetAnchors(FAnchors(0.f, 0.f, 0.f, 1.f));
		PanelSlot->SetOffsets(FMargin(12.f, 56.f, 0.f, 12.f));
		PanelSlot->SetSize(FVector2D(400.f, 0.f));
		PanelSlot->SetAlignment(FVector2D(0.f, 0.f));
	}

	UVerticalBox* Outer = WidgetTree->ConstructWidget<UVerticalBox>(
		UVerticalBox::StaticClass());
	Panel->SetContent(Outer);
	if (UBorderSlot* PadSlot = Cast<UBorderSlot>(Outer->Slot))
	{
		PadSlot->SetPadding(FMargin(10.f));
	}

	// Tab row.
	UHorizontalBox* Tabs = WidgetTree->ConstructWidget<UHorizontalBox>(
		UHorizontalBox::StaticClass());
	Outer->AddChildToVerticalBox(Tabs);
	// Internal tags stay stable FNames; only the labels localize.
	const TPair<const TCHAR*, FText> TabDefs[] = {
		{ TEXT("BUILD"), LOCTEXT("TabBuild", "BUILD") },
		{ TEXT("CONTRACTS"), LOCTEXT("TabContracts", "CONTRACTS") },
		{ TEXT("RESEARCH"), LOCTEXT("TabResearch", "RESEARCH") } };
	for (const TPair<const TCHAR*, FText>& TabDef : TabDefs)
	{
		ULBSpacecraftTaggedButton* TabButton =
			WidgetTree->ConstructWidget<ULBSpacecraftTaggedButton>(
				ULBSpacecraftTaggedButton::StaticClass());
		TabButton->Tag = FName(TabDef.Key);
		TabButton->OnTagClicked =
			[this](FName InTag) { HandleTab(InTag); };
		TabButton->Arm();
		TabButton->SetStyle(SpacecraftPanelButtonStyle(false));
		UTextBlock* TabText = WidgetTree->ConstructWidget<UTextBlock>(
			UTextBlock::StaticClass());
		TabText->SetText(TabDef.Value);
		TabText->SetColorAndOpacity(FSlateColor(SpacecraftPanelSubText));
		FSlateFontInfo TabFont = TabText->GetFont();
		TabFont.Size = 15;
		TabText->SetFont(TabFont);
		TabButton->AddChild(TabText);
		if (UHorizontalBoxSlot* TabSlot =
			Tabs->AddChildToHorizontalBox(TabButton))
		{
			TabSlot->SetPadding(FMargin(0.f, 0.f, 6.f, 8.f));
		}
		TabButtons.Add(TabButton);
		TabTexts.Add(TabText);
	}
	RefreshTabStyles();

	UScrollBox* Scroll = WidgetTree->ConstructWidget<UScrollBox>(
		UScrollBox::StaticClass());
	if (UVerticalBoxSlot* ScrollSlot =
		Outer->AddChildToVerticalBox(Scroll))
	{
		ScrollSlot->SetSize(FSlateChildSize(ESlateSizeRule::Fill));
	}
	ContentScroll = Scroll;
	ContentBox = WidgetTree->ConstructWidget<UVerticalBox>(
		UVerticalBox::StaticClass());
	Scroll->AddChild(ContentBox);

	// The refusal toast is the tutorial: it gets a designed box with a
	// warm keyline, not a bare floating string.
	ToastBorder = WidgetTree->ConstructWidget<UBorder>(
		UBorder::StaticClass());
	ToastBorder->SetBrushColor(FLinearColor(0.07f, 0.055f, 0.03f, 0.95f));
	ToastBorder->SetPadding(FMargin(10.f, 8.f));
	ToastBorder->SetVisibility(ESlateVisibility::Collapsed);
	ToastBlock = WidgetTree->ConstructWidget<UTextBlock>(
		UTextBlock::StaticClass());
	ToastBlock->SetColorAndOpacity(FSlateColor(SpacecraftPanelToast));
	ToastBlock->SetAutoWrapText(true);
	FSlateFontInfo ToastFont = ToastBlock->GetFont();
	ToastFont.Size = 13;
	ToastBlock->SetFont(ToastFont);
	ToastBorder->SetContent(ToastBlock);
	if (UVerticalBoxSlot* ToastSlot =
		Outer->AddChildToVerticalBox(ToastBorder))
	{
		ToastSlot->SetPadding(FMargin(0.f, 8.f, 0.f, 0.f));
	}
}

void ULBSpacecraftCommandPanelWidget::AddSectionLabel(const FString& Text)
{
	using namespace LBSpacecraftCommandPanelPrivate;
	UTextBlock* Label = WidgetTree->ConstructWidget<UTextBlock>(
		UTextBlock::StaticClass());
	Label->SetText(FText::FromString(Text));
	// Wrap rather than clip: "CONVEYOR BELTS UNLOCKS AFTER DELI" was
	// what a stranger read at panel width (2026-09-02).
	Label->SetAutoWrapText(true);
	Label->SetColorAndOpacity(FSlateColor(SpacecraftPanelAccent));
	FSlateFontInfo Font = Label->GetFont();
	Font.Size = 15;
	Label->SetFont(Font);
	if (UVerticalBoxSlot* LabelSlot =
		ContentBox->AddChildToVerticalBox(Label))
	{
		LabelSlot->SetPadding(FMargin(2.f, 14.f, 0.f, 2.f));
	}
	// A thin rule under every section header - the panel reads as
	// designed sections, not a flat list.
	UBorder* Rule = WidgetTree->ConstructWidget<UBorder>(
		UBorder::StaticClass());
	Rule->SetBrushColor(FLinearColor(
		SpacecraftPanelAccent.R, SpacecraftPanelAccent.G,
		SpacecraftPanelAccent.B, 0.35f));
	if (UVerticalBoxSlot* RuleSlot =
		ContentBox->AddChildToVerticalBox(Rule))
	{
		RuleSlot->SetPadding(FMargin(2.f, 0.f, 2.f, 6.f));
	}
	// A content-less border with 1px vertical padding renders as a rule.
	Rule->SetPadding(FMargin(0.f, 1.f));
}

ULBSpacecraftTaggedButton* ULBSpacecraftCommandPanelWidget::AddTaggedButton(
	const FString& Label, FName InTag, TFunction<void(FName)> Handler,
	const FString& SubLabel, bool bSubWarn, bool bArmed)
{
	using namespace LBSpacecraftCommandPanelPrivate;
	ULBSpacecraftTaggedButton* Button =
		WidgetTree->ConstructWidget<ULBSpacecraftTaggedButton>(
			ULBSpacecraftTaggedButton::StaticClass());
	Button->Tag = InTag;
	Button->OnTagClicked = MoveTemp(Handler);
	Button->Arm();
	Button->SetStyle(SpacecraftPanelButtonStyle(bArmed));
	UHorizontalBox* Row = WidgetTree->ConstructWidget<UHorizontalBox>(
		UHorizontalBox::StaticClass());
	if (UTexture2D* Icon = SpacecraftPanelIconForTag(InTag))
	{
		UImage* IconImage = WidgetTree->ConstructWidget<UImage>(
			UImage::StaticClass());
		IconImage->SetBrushFromTexture(Icon);
		IconImage->SetDesiredSizeOverride(FVector2D(44.f, 44.f));
		if (UHorizontalBoxSlot* IconSlot =
			Row->AddChildToHorizontalBox(IconImage))
		{
			IconSlot->SetPadding(FMargin(0.f, 0.f, 10.f, 0.f));
			IconSlot->SetVerticalAlignment(VAlign_Center);
		}
	}
	UVerticalBox* Lines = WidgetTree->ConstructWidget<UVerticalBox>(
		UVerticalBox::StaticClass());
	UTextBlock* Text = WidgetTree->ConstructWidget<UTextBlock>(
		UTextBlock::StaticClass());
	Text->SetText(FText::FromString(Label));
	Text->SetColorAndOpacity(FSlateColor(SpacecraftPanelText));
	FSlateFontInfo Font = Text->GetFont();
	Font.Size = 14;
	Text->SetFont(Font);
	Lines->AddChildToVerticalBox(Text);
	if (!SubLabel.IsEmpty())
	{
		// Second line: cost and power, dim - warning orange when the
		// player cannot afford it (the click still fires and shows the
		// plain-words refusal; the colour is the early warning).
		UTextBlock* Sub = WidgetTree->ConstructWidget<UTextBlock>(
			UTextBlock::StaticClass());
		Sub->SetText(FText::FromString(SubLabel));
		Sub->SetColorAndOpacity(FSlateColor(
			bSubWarn ? SpacecraftPanelWarn : SpacecraftPanelSubText));
		FSlateFontInfo SubFont = Sub->GetFont();
		SubFont.Size = 11;
		Sub->SetFont(SubFont);
		Lines->AddChildToVerticalBox(Sub);
	}
	if (UHorizontalBoxSlot* LinesSlot =
		Row->AddChildToHorizontalBox(Lines))
	{
		LinesSlot->SetVerticalAlignment(VAlign_Center);
	}
	Button->AddChild(Row);
	if (UVerticalBoxSlot* ButtonSlot =
		ContentBox->AddChildToVerticalBox(Button))
	{
		ButtonSlot->SetPadding(FMargin(0.f, 3.f, 0.f, 0.f));
	}
	return Button;
}

void ULBSpacecraftCommandPanelWidget::RefreshTabStyles()
{
	using namespace LBSpacecraftCommandPanelPrivate;
	for (int32 Index = 0; Index < TabButtons.Num(); ++Index)
	{
		const bool bActive = Index == static_cast<int32>(ActiveTab);
		if (TabButtons[Index] != nullptr)
		{
			TabButtons[Index]->SetStyle(
				SpacecraftPanelButtonStyle(bActive));
		}
		if (TabTexts.IsValidIndex(Index) && TabTexts[Index] != nullptr)
		{
			TabTexts[Index]->SetColorAndOpacity(FSlateColor(bActive
				? SpacecraftPanelText : SpacecraftPanelSubText));
		}
	}
}

FString ULBSpacecraftCommandPanelWidget::ComputeRevision() const
{
	FString Revision = FString::Printf(TEXT("tab=%d;"),
		static_cast<int32>(ActiveTab));
	if (GameMode == nullptr)
	{
		return Revision;
	}
	if (ALBSpacecraftResearchAuthority* Research =
		GameMode->GetResearchAuthority())
	{
		Revision += FString::Printf(TEXT("rsc=%d/%d;"),
			Research->GetPoints(), Research->GetUnlockedNodeCount());
	}
	if (ALBSpacecraftTransportAuthority* Transport =
		GameMode->GetTransportAuthority())
	{
		Revision += FString::Printf(TEXT("belts=%d;"),
			Transport->GetRoutes().Num());
	if (ALBSpacecraftInventoryAuthority* InventoryClock =
		GameMode->GetInventoryAuthority())
	{
		// Review fix: countdown labels re-render as the order clock
		// advances (5 s buckets - cheap, visibly ticking).
		Revision += FString::Printf(TEXT("oclk=%d;"),
			static_cast<int32>(
				InventoryClock->GetOrderClockSeconds() / 5.0));
	}
	}
	if (ALBSpacecraftTrackAuthority* TrackRevision =
		GameMode->GetTrackAuthority())
	{
		Revision += FString::Printf(TEXT("trk=%d/%d;"),
			TrackRevision->GetPieces().Num(),
			TrackRevision->GetNodeStationsInOrder().Num());
	}
	if (ALBSpacecraftProgressionAuthority* Progress =
		GameMode->GetProgression())
	{
		Revision += FString::Printf(TEXT("prog=%d/%d;"),
			Progress->GetCreditedDeliveries(),
			Progress->GetOwnedBayCount());
	}
	if (ALBSpacecraftBuildAuthority* Build = GameMode->GetBuildAuthority())
	{
		Revision += FString::Printf(TEXT("st=%d/%d;"),
			Build->GetStations().Num(), Build->IsCommissioned() ? 1 : 0);
		if (Pawn != nullptr && !Pawn->GetSelectedStation().IsNone())
		{
			for (const FLBSpacecraftStationRecord& Record :
				Build->GetStations())
			{
				if (Record.StationId == Pawn->GetSelectedStation())
				{
					Revision += FString::Printf(TEXT("dr=%d/%d;"),
						Record.InstalledDrones,
						Record.AllocatedComponents.Num());
					break;
				}
			}
		}
	}
	if (ALBSpacecraftProductionAuthority* Production =
		GameMode->GetProductionAuthority())
	{
		// Affordability FLAGS ride the revision, never the raw balance:
		// under the metered mains the balance moves every sim tick, and
		// a raw cash field rebuilt the whole panel every frame - Slate
		// never settled a layout and the catalogue painted as a garbled
		// strip. Flags flip only when an affordability actually changes.
		const int64 Cash = Production->GetCashPence();
		Revision += FString::Printf(TEXT("ct=%d;aff="),
			Production->GetContracts().Num());
		for (const FLBSpacecraftStationDefinition& Definition :
			ALBSpacecraftBuildAuthority::StationCatalogue())
		{
			Revision += Definition.CostPence <= Cash
				? TEXT("1") : TEXT("0");
		}
		if (ALBSpacecraftProgressionAuthority* LandAff =
			GameMode->GetProgression())
		{
			Revision += LandAff->BayCostPence <= Cash
				? TEXT("B") : TEXT("b");
		}
		if (ALBSpacecraftTrackAuthority* TrackAff =
			GameMode->GetTrackAuthority())
		{
			Revision += TrackAff->PieceCostPence <= Cash
				? TEXT("T") : TEXT("t");
		}
		if (ALBSpacecraftBuildAuthority* BuildAff =
			GameMode->GetBuildAuthority())
		{
			Revision += BuildAff->DroneUnitCostPence <= Cash
				? TEXT("D") : TEXT("d");
		}
		Revision += TEXT(";");
	}
	if (ALBSpacecraftInventoryAuthority* Inventory =
		GameMode->GetInventoryAuthority())
	{
		Revision += FString::Printf(TEXT("ord=%d;"),
			Inventory->GetPendingOrders().Num());
	}
	if (ALBSpacecraftCraftingAuthority* Orders =
		GameMode->GetCraftingAuthority())
	{
		if (Pawn != nullptr && !Pawn->GetSelectedStation().IsNone())
		{
			Revision += FString::Printf(TEXT("ord2=%d;"),
				Orders->GetOrderRemaining(Pawn->GetSelectedStation()));
		}
	}
	if (Pawn != nullptr)
	{
		Revision += FString::Printf(TEXT("sel=%s;arm=%s;"),
			*Pawn->GetSelectedStation().ToString(),
			*Pawn->GetPlacementDefinition().ToString());
	}
	// Live fitting rows re-render on ~10% progress steps and when the
	// hold text changes - not every tick (the churn lesson).
	if (GameMode != nullptr && GameMode->GetCoordinator() != nullptr)
	{
		const ALBSpacecraftRuntimeCoordinator* LiveCoordinator =
			GameMode->GetCoordinator();
		for (const FLBSpacecraftRuntimeAssignment& Assignment :
			LiveCoordinator->GetAssignments())
		{
			float Progress = 0.f;
			LiveCoordinator->GetUnitCycleProgress(Assignment.UnitId,
				Progress);
			Revision += FString::Printf(TEXT("|u%d:%d"),
				Assignment.RouteIndex,
				static_cast<int32>(Progress * 10.f));
		}
		// NOT the hold reason: its text flaps per tick while a craft
		// is mid-cycle, and a per-frame revision change turns the 4 Hz
		// rebuild throttle into a rebuild storm - which is exactly the
		// garbled never-settled layout the throttle comment warns
		// about, and exactly what the first live capture showed. The
		// 10% buckets above re-render the row when the hold appears
		// (progress hits the last bucket), which is all the UI needs.
	}
	// The split list re-renders when the counts move.
	if (GameMode != nullptr && GameMode->GetBuildAuthority() != nullptr
		&& GameMode->GetBuildAuthority()->IsCommissioned())
	{
		TArray<FName> SplitStations;
		TArray<int32> SplitCounts;
		FString SplitReason;
		if (GameMode->GetBuildAuthority()->GetFixingSplit(
			LineRecipeId(), SplitStations, SplitCounts,
			SplitReason))
		{
			for (int32 Count : SplitCounts)
			{
				Revision += FString::Printf(TEXT("|s%d"), Count);
			}
		}
	}
	return Revision;
}

void ULBSpacecraftCommandPanelWidget::RebuildContent()
{
	if (ContentBox == nullptr || GameMode == nullptr)
	{
		return;
	}
	ContentBox->ClearChildren();
	ALBSpacecraftResearchAuthority* Research =
		GameMode->GetResearchAuthority();
	switch (ActiveTab)
	{
	case ELBSpacecraftPanelTab::Build:
	{
		// THE CLICKED STATION COMES FIRST (owner 2026-08-28: "clicking
		// on it should bring up a build menu like car manufacturer").
		// It used to render BELOW the whole catalogue and the split
		// list, which on a built line put it off the bottom of the
		// panel - the page existed and could not be seen. What you
		// clicked is what you want to read.
		const FName Selected =
			Pawn != nullptr ? Pawn->GetSelectedStation() : NAME_None;
		if (!Selected.IsNone()
			&& GameMode->GetBuildAuthority() != nullptr)
		{
			// The friendly name already says what it is - "Assembly
			// station Mk1 2" needs no STATION prefix shouting over it.
			AddSectionLabel(LBSpacecraftCommandPanelPrivate
				::SpacecraftPrettifyStationIds(Selected.ToString(),
					GameMode->GetBuildAuthority()).ToUpper());
			for (const FLBSpacecraftStationRecord& Record :
				GameMode->GetBuildAuthority()->GetStations())
			{
				if (Record.StationId != Selected)
				{
					continue;
				}
				// Made to order (owner 2026-08-26): pick the recipe,
				// then ORDER a batch - the machine builds exactly that
				// many and idles.
				if (GameMode->GetCraftingAuthority() != nullptr)
				{
					const int32 Remaining = GameMode
						->GetCraftingAuthority()
						->GetOrderRemaining(Selected);
					if (Remaining > 0)
					{
						AddSectionLabel(FText::Format(
							LOCTEXT("OpenOrder", "Open order: {0} to go"),
							Remaining).ToString());
					}
				}
				// A bigger mark offers the SAME recipes as the mark
				// below it, so ask the recipe class, not the id.
				const FLBSpacecraftStationDefinition* RecipeDef =
					ALBSpacecraftBuildAuthority::FindDefinition(
						Record.DefinitionId);
				for (const FName& RecipeId :
					FLBSpacecraftRecipeCatalogue::GetRecipesForStationClass(
						RecipeDef != nullptr ? RecipeDef->GetRecipeClassId()
							: Record.DefinitionId))
				{
					const FLBSpacecraftItemRecipe* Recipe =
						FLBSpacecraftRecipeCatalogue::FindRecipe(RecipeId);
					AddTaggedButton(Recipe != nullptr
							? Recipe->DisplayName : RecipeId.ToString(),
						RecipeId,
						[this](FName InTag) { HandleSelectRecipe(InTag); });
				}
				if (GameMode->GetCraftingAuthority() != nullptr
					&& GameMode->GetCraftingAuthority()
						->GetSelectedRecipe(Selected) != nullptr)
				{
					AddTaggedButton(
						LOCTEXT("OrderFive", "Order 5 cycles").ToString(),
						Selected,
						[this](FName InTag) { HandleOrderParts(InTag); });
				}
				// Supply belt: auto-routed to the floor store, priced
				// by distance, one per station (research doc v001).
				if (ALBSpacecraftTransportAuthority* Transport =
					GameMode->GetTransportAuthority())
				{
					ALBSpacecraftProgressionAuthority* Progress =
						GameMode->GetProgression();
					const bool bBeltsOpen = Progress == nullptr
						|| Progress->IsUnlocked(
							ELBSpacecraftUnlock::Belts);
					const FLBSpacecraftBeltRoute* Route =
						Transport->FindRouteForStation(Selected);
					if (!bBeltsOpen)
					{
						AddSectionLabel(Progress->DescribeLock(
							ELBSpacecraftUnlock::Belts));
					}
					else if (Route == nullptr)
					{
						const int64 BeltCost =
							Transport->ComputeBeltCostPence(
								ALBSpacecraftTransportAuthority::
									ComputeBeltPathCm(
										Record.WorldTransform.GetLocation(),
										FVector(-9900.f, 0.f, 0.f)));
						AddTaggedButton(FText::Format(
							LOCTEXT("ConnectBelt",
								"Connect supply belt  ({0})"),
							FText::FromString(
								ULBSpacecraftTopBarWidget::FormatCurrency(
									BeltCost))).ToString(),
							Selected,
							[this](FName InTag) { HandleBelt(InTag); });
					}
					else
					{
						AddTaggedButton(FText::Format(
							LOCTEXT("RemoveBelt",
								"Remove belt {0}"),
							FText::FromName(Route->RouteId)).ToString(),
							Route->RouteId,
							[this](FName InTag) { HandleRemoveBelt(InTag); });
					}
				}
				// Slot buildings grow by installing units (owner
				// 2026-08-26): one INSTALL button per legal unit class.
				if (const FLBSpacecraftStationDefinition* HostDef =
					ALBSpacecraftBuildAuthority::FindDefinition(
						Record.DefinitionId))
				{
					if (HostDef->SlotCount > 0)
					{
						AddSectionLabel(FText::Format(
							LOCTEXT("SectionSlots", "SLOTS {0}/{1}"),
							GameMode->GetBuildAuthority()
								->GetHostedCount(Selected),
							HostDef->SlotCount).ToString());
						for (const FLBSpacecraftStationDefinition& Unit :
							ALBSpacecraftBuildAuthority::StationCatalogue())
						{
							const bool bLegal =
								HostDef->SlotUnitClass == Unit.DefinitionId
								|| (HostDef->SlotUnitClass
										== FName(TEXT("AnyCraftingMachine"))
									&& FLBSpacecraftRecipeCatalogue
										::GetRecipesForStationClass(
											Unit.GetRecipeClassId()).Num()
												> 0);
							if (!bLegal)
							{
								continue;
							}
							AddTaggedButton(FText::Format(
								LOCTEXT("InstallUnit", "Install {0}"),
								FText::FromString(Unit.DisplayName))
									.ToString(),
								Unit.DefinitionId,
								[this](FName InTag)
								{ HandleInstallUnit(InTag); },
								ULBSpacecraftTopBarWidget::FormatCurrency(
									Unit.CostPence),
								GameMode->GetProductionAuthority() != nullptr
								&& GameMode->GetProductionAuthority()
									->GetCashPence() < Unit.CostPence);
						}
					}
				}
				// Line stations: drone slots + fit allocation (owner
				// 2026-08-26, the Car Manufacture worker-slot model).
				if (const FLBSpacecraftStationDefinition* LineDef =
					ALBSpacecraftBuildAuthority::FindDefinition(
						Record.DefinitionId))
				{
					if (LineDef->DroneSlotCount > 0)
					{
						AddSectionLabel(FText::Format(
							LOCTEXT("DroneSlots", "DRONE SLOTS {0}/{1}"),
							Record.InstalledDrones,
							LineDef->DroneSlotCount).ToString());
						// THE CREW YOU CHOOSE (owner 2026-08-28:
						// "clicking on it should bring up a build menu
						// like car manufacturer so you can pick what
						// drones you want"). One row per kind, its job
						// in plain words underneath, and the crew that
						// stands there listed below so a station's
						// character is readable at a glance rather
						// than being a number.
						const int32 Free = LineDef->DroneSlotCount
							- Record.InstalledDrones;
						for (const FLBSpacecraftDroneKind& Kind :
							ALBSpacecraftBuildAuthority::DroneKinds())
						{
							const bool bPoor =
								GameMode->GetProductionAuthority() != nullptr
								&& GameMode->GetProductionAuthority()
									->GetCashPence() < Kind.CostPence;
							AddTaggedButton(
								Free > 0
									? FText::Format(
										LOCTEXT("HireDrone", "Hire {0}"),
										FText::FromString(
											Kind.DisplayName))
										.ToString()
									: FText::Format(
										LOCTEXT("SlotsFull",
											"{0} - slots full"),
										FText::FromString(
											Kind.DisplayName))
										.ToString(),
								Kind.KindId,
								[this](FName InTag)
								{ HandleInstallDroneKind(InTag); },
								FString::Printf(TEXT("%s   %s"),
									*ULBSpacecraftTopBarWidget
										::FormatCurrency(Kind.CostPence),
									*Kind.Role),
								bPoor);
						}
						if (Record.InstalledDroneTypes.Num() > 0)
						{
							AddSectionLabel(LOCTEXT("CrewHere",
								"CREW AT THIS STATION").ToString());
							// CrewSlot, not Slot: UUserWidget has a Slot
							// member and the shadow is a compile error.
							for (int32 CrewSlot = 0;
								CrewSlot < Record.InstalledDroneTypes.Num();
								++CrewSlot)
							{
								const FLBSpacecraftDroneKind* Kind =
									ALBSpacecraftBuildAuthority
										::FindDroneKind(
											Record.InstalledDroneTypes[
												CrewSlot]);
								AddTaggedButton(
									FText::Format(
										LOCTEXT("DismissDrone",
											"{0}. {1}  -  dismiss"),
										FText::AsNumber(CrewSlot + 1),
										FText::FromString(Kind != nullptr
											? Kind->DisplayName
											: TEXT("Drone")))
										.ToString(),
									FName(*FString::FromInt(CrewSlot)),
									[this](FName InTag)
									{ HandleDismissDrone(InTag); });
							}
						}
						AddSectionLabel(LOCTEXT("FitAllocation",
							"FITTED AT THIS STATION").ToString());
						for (uint8 Component = 0; Component < 6;
							++Component)
						{
							const FName ItemId = FLBSpacecraftItemCatalogue
								::GetAssembledComponentItemId(Component);
							if (ItemId.IsNone())
							{
								continue;
							}
							const bool bOn =
								Record.AllocatedComponents.Contains(
									ItemId);
							const FLBSpacecraftItemDefinition* Item =
								FLBSpacecraftItemCatalogue::FindItem(
									ItemId);
							AddTaggedButton(Item != nullptr
									? Item->DisplayName
									: ItemId.ToString(),
								ItemId,
								[this](FName InTag)
								{ HandleToggleAllocation(InTag); },
								bOn ? LOCTEXT("Fitted", "Fitted")
										.ToString()
									: LOCTEXT("NotFitted", "Off")
										.ToString(),
								false, bOn);
						}
					}
				}
				// ATTACH TO THE LINE is gone with the manual track
				// (owner 2026-09-01): the relayer attaches every
				// station on placement and removal.
				// The hall is the site, not a station to sell: no button
				// (the authority refuses too - belt and braces after the
				// stranger playthrough deleted it with one click).
				bool bSelectedIsHall = false;
				if (GameMode->GetBuildAuthority() != nullptr)
				{
					for (const FLBSpacecraftStationRecord& HallProbe :
						GameMode->GetBuildAuthority()->GetStations())
					{
						if (HallProbe.StationId == Selected
							&& HallProbe.DefinitionId
								== FName(TEXT("ShipFactoryHall")))
						{
							bSelectedIsHall = true;
						}
					}
				}
				if (!bSelectedIsHall)
				{
					AddTaggedButton(
						LOCTEXT("RemoveStation", "Remove station").ToString(),
						Selected,
						[this](FName InTag) { HandleRemoveStation(InTag); });
				}
			}
		}
		// The catalogue reads as GROUPS, the way the genre expects:
		// the line's four classes, their heavy marks, the crafting
		// chain, then infrastructure.
		const int64 Cash = GameMode->GetProductionAuthority() != nullptr
			? GameMode->GetProductionAuthority()->GetCashPence() : 0;
		const FName Armed = Pawn != nullptr
			? Pawn->GetPlacementDefinition() : NAME_None;
		struct FLBSpacecraftBuildGroup
		{
			FText Title;
			TArray<const FLBSpacecraftStationDefinition*> Entries;
		};
		// The owner's own framing (2026-08-27): "so basically they build
		// a ship factory and a parts factory". Two factories, and the
		// menu should say which is which - a player who reads "LINE
		// STATIONS" next to "CRAFTING CHAIN" has to work out that the
		// second one is a different building, and reasonably does not.
		FLBSpacecraftBuildGroup Groups[] = {
			{ LOCTEXT("GroupLine", "SHIP FACTORY - THE LINE"), {} },
			{ LOCTEXT("GroupMarks", "SHIP FACTORY - HEAVY MARKS"), {} },
			{ LOCTEXT("GroupCrafting", "PARTS FACTORY - MACHINES"), {} },
			{ LOCTEXT("GroupInfra", "INFRASTRUCTURE"), {} },
			{ LOCTEXT("GroupSite", "THE SITE - BUILDINGS"), {} } };
		// OUTSIDE vs INSIDE (owner 2026-08-28, the world-map opening).
		// On the world map the menu offers SITE BUILDINGS only; step
		// inside one and it offers the factory catalogue only. The two
		// never mix, so "only able to pick the ship factory" holds on
		// a bare site without a special case for it.
		const bool bOnSiteMap = Pawn != nullptr && Pawn->IsSiteMapView();
		// ONLY WHAT IS AVAILABLE (owner 2026-08-28: "only need to be
		// able to build whats available"). Two rules decide a listing:
		//
		// SLOT UNITS never appear here. Parts machines and power plants
		// install into a host building's slots through that building's
		// own panel; the fresh-start menu used to offer Smelters that
		// can only ever refuse on the open floor.
		TSet<FName> SlotUnitIds;
		for (const FLBSpacecraftStationDefinition& Host :
			ALBSpacecraftBuildAuthority::StationCatalogue())
		{
			if (Host.SlotCount <= 0)
			{
				continue;
			}
			if (Host.SlotUnitClass != FName(TEXT("AnyCraftingMachine")))
			{
				SlotUnitIds.Add(Host.SlotUnitClass);
				continue;
			}
			for (const FLBSpacecraftStationDefinition& Unit :
				ALBSpacecraftBuildAuthority::StationCatalogue())
			{
				if (Unit.SlotCount == 0
					&& FLBSpacecraftRecipeCatalogue
						::GetRecipesForStationClass(
							Unit.GetRecipeClassId()).Num() > 0)
				{
					SlotUnitIds.Add(Unit.DefinitionId);
				}
			}
		}
		// Everything else is asked of the PLACEMENT GATE itself -
		// research, prior-ownership and delivery-milestone locks in one
		// answer - so the menu can never dangle a building the click
		// would refuse. Affordability stays visible (warning-orange
		// price), because "you cannot afford it yet" is information
		// and "you cannot build this" is noise.
		TFunction<bool(FName, FString&)> PlacementGate;
		if (GameMode->GetBuildAuthority() != nullptr)
		{
			PlacementGate =
				GameMode->GetBuildAuthority()->GetPlacementGate();
		}
		for (const FLBSpacecraftStationDefinition& Definition :
			ALBSpacecraftBuildAuthority::StationCatalogue())
		{
			// Legacy line-station ids exist only so old saves resolve;
			// the menu offers the ONE station type, not its ancestors.
			if (Definition.bLegacyHidden)
			{
				continue;
			}
			if (SlotUnitIds.Contains(Definition.DefinitionId))
			{
				continue;
			}
			if (Definition.bSiteBuilding != bOnSiteMap)
			{
				continue;
			}
			FString GateReason;
			if (PlacementGate
				&& !PlacementGate(Definition.DefinitionId, GateReason))
			{
				continue;
			}
			if (Research != nullptr && !Research->IsStationClassUnlocked(
				Definition.DefinitionId))
			{
				continue; // locked families never render as buildable
			}
			Groups[BuildMenuGroupFor(Definition)].Entries.Add(&Definition);
		}
		for (const FLBSpacecraftBuildGroup& Group : Groups)
		{
			if (Group.Entries.Num() == 0)
			{
				continue;
			}
			AddSectionLabel(Group.Title.ToString());
			for (const FLBSpacecraftStationDefinition* Definition :
				Group.Entries)
			{
				FString Sub = ULBSpacecraftTopBarWidget::FormatCurrency(
					Definition->CostPence);
				if (Definition->PowerDrawKw > 0)
				{
					Sub += FString::Printf(TEXT("   %d kW"),
						Definition->PowerDrawKw);
				}
				if (Definition->PowerSupplyKw > 0)
				{
					Sub += FString::Printf(TEXT("   +%d kW"),
						Definition->PowerSupplyKw);
				}
				AddTaggedButton(Definition->DisplayName,
					Definition->DefinitionId,
					[this](FName InTag) { HandleBuildStation(InTag); },
					Sub, Definition->CostPence > Cash,
					Definition->DefinitionId == Armed);
			}
		}
		// THE FIXING SPLIT (owner: "get the ui right"). The engine has
		// carried the split-the-sequence model for days with no face on
		// it: who fits what, in line order, with the boundary moved one
		// part at a time. Every row is honest data from GetFixingSplit;
		// every move goes through SetFixingSplit and can refuse with a
		// named reason, which lands in the action line like everything
		// else.
		// INSIDE ONLY. The fixing split describes a production line, and
		// on the world map there is no line to describe - a screenshot
		// of the opening site showed "THE LINE - WHO FITS WHAT" and its
		// take/give buttons sitting under a menu of site buildings.
		//
		// The catalogue above already splits outside from inside; these
		// sections were simply never asked. That is the same shape of
		// fault as the one that made the game unplayable: a view-mode
		// gate applied in one place and assumed everywhere.
		if (ALBSpacecraftBuildAuthority* SplitBuild =
			SectionBelongsInView(EBuildSection::FixingSplit, bOnSiteMap)
				? GameMode->GetBuildAuthority() : nullptr)
		{
			TArray<FName> SplitStations;
			TArray<int32> SplitCounts;
			FString SplitReason;
			if (SplitBuild->IsCommissioned()
				&& SplitBuild->GetFixingSplit(LineRecipeId(),
					SplitStations, SplitCounts, SplitReason))
			{
				AddSectionLabel(LOCTEXT("SectionSplit",
					"THE LINE - WHO FITS WHAT").ToString());
				FLBSpacecraftRecipe SplitRecipe;
				const bool bRecipe =
					FLBSpacecraftProductionCatalog::FindRecipe(
						LineRecipeId(), SplitRecipe);
				const TArray<FName> Sequence = bRecipe
					? FLBSpacecraftProductionCatalog::
						FixingSequenceItemIds(SplitRecipe)
					: TArray<FName>();
				int32 SliceCursor = 0;
				int32 TotalAllocated = 0;
				for (int32 Count : SplitCounts)
				{
					TotalAllocated += Count;
				}
				for (int32 Index = 0; Index < SplitStations.Num();
					++Index)
				{
					// The slice this station fits, named.
					FString Parts;
					for (int32 Part = 0; Part < SplitCounts[Index];
						++Part)
					{
						const FLBSpacecraftItemDefinition* Item =
							Sequence.IsValidIndex(SliceCursor + Part)
								? FLBSpacecraftItemCatalogue::FindItem(
									Sequence[SliceCursor + Part])
								: nullptr;
						if (Item != nullptr)
						{
							if (!Parts.IsEmpty())
							{
								Parts += TEXT(" > ");
							}
							// Data display names ("Hull Component");
							// the trailing word is noise at row width.
							FString Short = Item->DisplayName;
							Short.RemoveFromEnd(TEXT(" Component"));
							Parts += Short;
						}
					}
					SliceCursor += SplitCounts[Index];
					if (Parts.IsEmpty())
					{
						Parts = LOCTEXT("SplitPassThrough",
							"Pass-through").ToString();
					}
					const float StopSeconds = bRecipe
						? FLBSpacecraftProductionCatalog::
							StationFitSeconds(SplitRecipe,
								SplitCounts[Index], TotalAllocated,
								SplitStations.Num())
						: 0.f;
					// LIVE FITTING PROGRESS: when a craft stands at
					// this station, the row says which part of the
					// slice is going on and how far through the stop
					// it is - the planned seconds above become work
					// you can watch. A finished cycle that has not
					// moved on is a HOLD, and the hold's named reason
					// belongs on the row where the craft is stuck.
					FString Live;
					if (const ALBSpacecraftRuntimeCoordinator*
						LiveCoordinator = GameMode->GetCoordinator())
					{
						for (const FLBSpacecraftRuntimeAssignment&
							Assignment :
							LiveCoordinator->GetAssignments())
						{
							if (Assignment.StationId
								!= SplitStations[Index])
							{
								continue;
							}
							float Progress = 0.f;
							LiveCoordinator->GetUnitCycleProgress(
								Assignment.UnitId, Progress);
							if (Progress >= 1.f)
							{
								Live = LiveCoordinator
									->GetLastHoldReason();
								if (Live.IsEmpty())
								{
									Live = LOCTEXT("SplitDeparting",
										"Departing").ToString();
								}
							}
							else
							{
								const int32 Fitting = FMath::Clamp(
									static_cast<int32>(Progress
										* SplitCounts[Index]),
									0, SplitCounts[Index] - 1);
								const FLBSpacecraftItemDefinition*
									LiveItem = Sequence.IsValidIndex(
										SliceCursor
										- SplitCounts[Index] + Fitting)
									? FLBSpacecraftItemCatalogue::
										FindItem(Sequence[SliceCursor
											- SplitCounts[Index]
											+ Fitting])
									: nullptr;
								FString LiveName = LiveItem != nullptr
									? LiveItem->DisplayName
									: FString();
								LiveName.RemoveFromEnd(
									TEXT(" Component"));
								Live = FText::Format(
									LOCTEXT("SplitFitting",
										"Fitting {0}  {1}%"),
									FText::FromString(LiveName),
									FText::AsNumber(FMath::RoundToInt(
										Progress * 100.f)))
									.ToString();
							}
							break;
						}
					}
					AddTaggedButton((Live.IsEmpty()
						? FText::Format(
							LOCTEXT("SplitRow",
								"{0}. Fits {1}  (~{2} s stop)"),
							FText::AsNumber(Index + 1),
							FText::AsNumber(SplitCounts[Index]),
							FText::AsNumber(FMath::RoundToInt(
								StopSeconds)))
						: FText::Format(
							LOCTEXT("SplitRowLive",
								"{0}. Fits {1}  -  {2}"),
							FText::AsNumber(Index + 1),
							FText::AsNumber(SplitCounts[Index]),
							FText::FromString(Live))).ToString(),
						SplitStations[Index],
						[this](FName InTag)
						{
							// Clicking the row selects that station.
							if (Pawn != nullptr)
							{
								Pawn->SetSelectedStation(InTag);
							}
						}, Parts);
					if (Index < SplitStations.Num() - 1)
					{
						// Real glyphs, sentence case (owner 2026-09-01:
						// "the ui has got to be really easy to use" -
						// caret characters read as a debug overlay).
						AddTaggedButton(LOCTEXT("SplitTake",
							"   ▲ Take one from the next station")
							.ToString(),
							SplitStations[Index],
							[this](FName InTag)
							{ HandleSplitTake(InTag); });
						AddTaggedButton(LOCTEXT("SplitGive",
							"   ▼ Give one to the next station")
							.ToString(),
							SplitStations[Index],
							[this](FName InTag)
							{ HandleSplitGive(InTag); });
					}
				}
			}
		}
		// OUTSIDE ONLY - the opposite gate to the two above, and worth
		// stating rather than leaving to look like an oversight. A bay
		// is SITE land: it is bought by adjacency to land already owned
		// and refused when it belongs to the launch corridor. Buying it
		// from inside a building, where the plot is not on screen, is
		// asking the player to choose a square they cannot see.
		if (ALBSpacecraftProgressionAuthority* Land =
			SectionBelongsInView(EBuildSection::Land, bOnSiteMap)
				? GameMode->GetProgression() : nullptr)
		{
			AddSectionLabel(FText::Format(
				LOCTEXT("SectionLand", "LAND - {0} BAYS OWNED"),
				FText::AsNumber(Land->GetOwnedBayCount())).ToString());
			AddTaggedButton(FText::Format(
				LOCTEXT("BuyBay", "Buy adjacent bay  ({0})"),
				FText::FromString(
					ULBSpacecraftTopBarWidget::FormatCurrency(
						Land->BayCostPence))).ToString(),
				FName(TEXT("BuyBay")),
				[this](FName InTag) { HandleBuyBay(InTag); });
		}
		// ---- THE BOARD ----
		//
		// A craft that failed its hover test used to have exactly one
		// future: pay the rework and retest. That is a toll, not a
		// decision. This is where the other two dispositions live, and
		// it only appears when there is actually a craft to decide
		// about - a permanent empty section would be furniture.
		if (ALBSpacecraftProductionAuthority* Board =
			SectionBelongsInView(EBuildSection::MaterialReview, bOnSiteMap)
				? GameMode->GetProductionAuthority() : nullptr)
		{
			TArray<FName> Failed;
			for (const FLBSpacecraftUnitState& Unit : Board->GetUnits())
			{
				if (FLBSpacecraftProductionCatalog::IsQualityGate(Unit.Stage)
					&& Unit.bQualityRecorded && !Unit.bQualityPassed
					&& !Unit.bConcessionGranted)
				{
					Failed.Add(Unit.UnitId);
				}
			}
			if (Failed.Num() > 0)
			{
				AddSectionLabel(FText::Format(
					LOCTEXT("SectionBoard",
						"THE BOARD - {0} CRAFT FAILED THE TEST"),
					FText::AsNumber(Failed.Num())).ToString());
			}
			for (const FName& UnitId : Failed)
			{
				const FLBSpacecraftUnitState* Unit = Board->FindUnit(UnitId);
				if (Unit == nullptr)
				{
					continue;
				}
				AddSectionLabel(FString::Printf(
					TEXT("%s - %d defect points, %.0f s rework owed"),
					*UnitId.ToString(), Unit->DefectPoints,
					Unit->ReworkSecondsRemaining));

				// The button states the PRICE, not just the action.
				// The whole point of the disposition is that the
				// player is trading margin and reputation against line
				// time, and a choice whose cost is hidden until after
				// it is made is not a choice.
				FString WhyNot;
				if (FLBSpacecraftProductionCatalog::CanConcede(
					*Unit, WhyNot))
				{
					AddTaggedButton(FText::Format(
						LOCTEXT("Concede",
							"   Ship on concession  (-{0}% , -{1} rep)"),
						FText::AsNumber(FLBSpacecraftProductionCatalog
							::ConcessionDeductionPercent(
								Unit->DefectPoints)),
						FText::AsNumber(FLBSpacecraftProductionCatalog
							::ConcessionReputationCost(
								Unit->DefectPoints))).ToString(),
						UnitId,
						[this](FName InTag) { HandleConcede(InTag); });
				}
				else
				{
					// Shown, not hidden. A missing button teaches
					// nothing; the named reason is how the player
					// learns the ceiling exists at all.
					AddSectionLabel(FString::Printf(
						TEXT("   No concession: %s"), *WhyNot));
				}
				AddTaggedButton(LOCTEXT("Scrap",
					"   Scrap the craft").ToString(), UnitId,
					[this](FName InTag) { HandleScrap(InTag); });
			}
		}

		// THE TRACK HAS NO BUTTONS ANY MORE (owner 2026-09-01: "cant
		// we just have the track autamaticly connect between
		// stations?"). Stations are the decision; the relayer routes
		// the line through them on every placement and removal. The
		// section survives only as a status line while incomplete.
		if (ALBSpacecraftTrackAuthority* TrackAuthority =
			SectionBelongsInView(EBuildSection::Track, bOnSiteMap)
				? GameMode->GetTrackAuthority() : nullptr)
		{
			const FString Problem = TrackAuthority->DescribeProblem();
			if (!Problem.IsEmpty() && TrackAuthority->GetPieces().Num() > 0)
			{
				AddSectionLabel(Problem);
			}
		}

		// SESSION - the save system existed and was tested long before
		// it had a button. A player could not stop and come back, which
		// for a game where a single craft takes 440 seconds is not a
		// missing convenience but a missing game.
		if (SectionBelongsInView(EBuildSection::Session, bOnSiteMap))
		{
			AddSectionLabel(
				LOCTEXT("SectionSession", "SESSION").ToString());
			AddTaggedButton(
				LOCTEXT("SaveGame", "Save game").ToString(),
				FName(TEXT("Session.Save")),
				[this](FName) { HandleQuickSave(); });
			AddTaggedButton(
				LOCTEXT("LoadGame", "Load game").ToString(),
				FName(TEXT("Session.Load")),
				[this](FName) { HandleQuickLoad(); });
		}

		break;
	}
	case ELBSpacecraftPanelTab::Contracts:
	{
		AddSectionLabel(LOCTEXT("SectionLine", "LINE").ToString());
		AddTaggedButton(LOCTEXT("CommissionLine",
				"Commission the line").ToString(), NAME_None,
			[this](FName InTag) { HandleCommission(InTag); });
		AddSectionLabel(
			LOCTEXT("SectionSupply", "SUPPLY - BUY RAW MATERIALS")
				.ToString());
		// ONE CLICK, ANY QUANTITY. Every order button multiplies by
		// this, so stocking up for a long production run does not mean
		// twenty clicks per item.
		AddTaggedButton(FText::Format(
			LOCTEXT("BuyMultiplier", "Buy quantity  x{0}"),
			FText::AsNumber(BuyMultiplier)).ToString(), NAME_None,
			[this](FName InTag) { HandleCycleBuyMultiplier(InTag); },
			LOCTEXT("BuyMultiplierHint",
				"click to cycle 1 / 5 / 20").ToString());
		for (const FLBSpacecraftItemDefinition& Item :
			FLBSpacecraftItemCatalogue::GetItemTable())
		{
			const int64 UnitPrice =
				FLBSpacecraftItemCatalogue::GetRawItemPricePence(
					Item.ItemId);
			if (UnitPrice <= 0)
			{
				continue;
			}
			const int32 Lot = 10 * BuyMultiplier;
			AddTaggedButton(FText::Format(
				LOCTEXT("OrderButton", "Order {0}x {1}  ({2})"),
				FText::AsNumber(Lot),
				FText::FromString(Item.DisplayName),
				FText::FromString(
					ULBSpacecraftTopBarWidget::FormatCurrency(
						UnitPrice * Lot))).ToString(), Item.ItemId,
				[this](FName InTag) { HandleOrder(InTag); });
		}
		if (GameMode->GetInventoryAuthority() != nullptr)
		{
			for (const FLBSpacecraftResourceOrder& Order :
				GameMode->GetInventoryAuthority()->GetPendingOrders())
			{
				const double Remaining = Order.ArrivesAtSeconds
					- GameMode->GetInventoryAuthority()
						->GetOrderClockSeconds();
				AddSectionLabel(FText::Format(
					LOCTEXT("PendingOrder", "{0} x{1} - arriving in {2}s"),
					FText::FromName(Order.ItemId), Order.Count,
					FMath::Max(0,
						static_cast<int32>(Remaining))).ToString());
			}
		}
		AddSectionLabel(LOCTEXT("SectionImport",
			"IMPORT PARTS (MAKE-VS-BUY)").ToString());
		for (const FLBSpacecraftItemDefinition& Item :
			FLBSpacecraftItemCatalogue::GetItemTable())
		{
			const int64 ImportPrice =
				FLBSpacecraftItemCatalogue::GetItemImportPricePence(
					Item.ItemId);
			if (ImportPrice <= 0)
			{
				continue;
			}
			AddTaggedButton(FText::Format(
				LOCTEXT("ImportButton", "Import 5x {0}  ({1})"),
				FText::FromString(Item.DisplayName),
				FText::FromString(
					ULBSpacecraftTopBarWidget::FormatCurrency(
						ImportPrice * 5))).ToString(), Item.ItemId,
				[this](FName InTag) { HandleImport(InTag); });
		}
		// WHAT IS ALREADY BUILT. Craft that rolled off the line with
		// no order to fill fill one the instant it is taken, so this
		// is the difference between an offer being work and an offer
		// being free money.
		if (ALBSpacecraftProductionAuthority* StockLedger =
			GameMode != nullptr ? GameMode->GetProductionAuthority()
				: nullptr)
		{
			TMap<FName, int32> Stock;
			for (const FLBSpacecraftUnitState& Unit :
				StockLedger->GetUnits())
			{
				if (Unit.bAwaitingSale)
				{
					++Stock.FindOrAdd(Unit.RecipeId);
				}
			}
			if (Stock.Num() > 0)
			{
				AddSectionLabel(LOCTEXT("SectionStock",
					"FINISHED STOCK").ToString());
				for (const TPair<FName, int32>& Row : Stock)
				{
					AddSectionLabel(BuildFinishedStockLine(Row.Key,
						Row.Value));
				}
			}
		}

		// THE WORK YOU HAVE TAKEN ON. The tab used to show offers,
		// material orders and imports, but never the contracts the
		// player was actually committed to - so the one thing the
		// factory exists to satisfy was the one thing not on screen.
		ALBSpacecraftProductionAuthority* HeldLedger =
			GameMode != nullptr ? GameMode->GetProductionAuthority()
				: nullptr;
		if (HeldLedger != nullptr)
		{
			bool bAnyHeld = false;
			for (const FLBSpacecraftContract& Held :
				HeldLedger->GetContracts())
			{
				// Offered contracts belong to the board below, not
				// to the work you have taken on.
				if (Held.State == ELBSpacecraftContractState::Complete
					|| Held.State == ELBSpacecraftContractState::Offered)
				{
					continue;
				}
				if (!bAnyHeld)
				{
					AddSectionLabel(LOCTEXT("SectionHeld",
						"CONTRACTS YOU HOLD").ToString());
					bAnyHeld = true;
				}
				AddSectionLabel(BuildHeldContractLine(Held,
					HeldLedger->GetSimSeconds()));
			}
		}
		// ---- REFIT WORK ----
		//
		// Sits between the orders you hold and the offer board because
		// that is what it is: work you can put ON the board, generated
		// from your own delivery history rather than from a spawn
		// table. A craft you shipped is a customer you can go back to.
		if (HeldLedger != nullptr)
		{
			// A refit already accepted is waiting to be started, and
			// that is the more urgent thing, so it is listed first.
			bool bAnyRefit = false;
			for (const FLBSpacecraftContract& Refit :
				HeldLedger->GetContracts())
			{
				if (!Refit.IsRefit()
					|| Refit.State != ELBSpacecraftContractState::Accepted)
				{
					continue;
				}
				// Already on the line? Then there is nothing to press.
				bool bOnLine = false;
				for (const FLBSpacecraftUnitState& Unit :
					HeldLedger->GetUnits())
				{
					if (Unit.AssignedContractId == Refit.ContractId)
					{
						bOnLine = true;
						break;
					}
				}
				if (bOnLine)
				{
					continue;
				}
				if (!bAnyRefit)
				{
					AddSectionLabel(LOCTEXT("SectionRefitTaken",
						"REFITS TAKEN - PUT THEM ON THE LINE").ToString());
					bAnyRefit = true;
				}
				AddTaggedButton(FText::Format(
					LOCTEXT("StartRefit", "Bring {0} in  ({1})"),
					FText::FromName(Refit.RefitOriginUnitId),
					FText::FromString(
						ULBSpacecraftTopBarWidget::FormatCurrency(
							Refit.PricePerUnitPence))).ToString(),
					Refit.ContractId,
					[this](FName InTag) { HandleStartRefit(InTag); });
			}

			// Then the craft that COULD come back. Only ones actually
			// delivered, and only where no order already wants them -
			// the authority refuses both cases anyway, and a button
			// that can only refuse teaches the player nothing.
			bool bAnyCandidate = false;
			for (const FLBSpacecraftUnitState& Unit : HeldLedger->GetUnits())
			{
				if (!Unit.bCompleted
					|| Unit.Stage != ELBSpacecraftStage::Dispatched)
				{
					continue;
				}
				bool bSpokenFor = false;
				for (const FLBSpacecraftContract& Other :
					HeldLedger->GetContracts())
				{
					const bool bLive = Other.State
							== ELBSpacecraftContractState::Offered
						|| Other.State
							== ELBSpacecraftContractState::Accepted;
					if (bLive && Other.IsRefit()
						&& Other.RefitOriginUnitId == Unit.UnitId)
					{
						bSpokenFor = true;
						break;
					}
				}
				for (const FLBSpacecraftUnitState& Other :
					HeldLedger->GetUnits())
				{
					if (Other.IsRefit()
						&& Other.OriginUnitId == Unit.UnitId
						&& Other.Stage != ELBSpacecraftStage::Dispatched)
					{
						bSpokenFor = true;
						break;
					}
				}
				if (bSpokenFor)
				{
					continue;
				}
				if (!bAnyCandidate)
				{
					AddSectionLabel(LOCTEXT("SectionRefitCandidates",
						"CRAFT YOU COULD BRING BACK").ToString());
					bAnyCandidate = true;
				}
				// The button states the SCOPE, because that is the
				// decision: a refit from hull fabrication re-fits five
				// components and is priced accordingly, while a later
				// one is worth less and is refused outright once it
				// re-fits nothing at all.
				AddTaggedButton(FText::Format(
					LOCTEXT("OfferRefit", "Offer a refit on {0}"),
					FText::FromName(Unit.UnitId)).ToString(),
					Unit.UnitId,
					[this](FName InTag) { HandleOfferRefit(InTag); },
					LOCTEXT("RefitScope",
						"from hull fabrication - refits everything but the hull")
						.ToString());
			}
		}

		AddSectionLabel(
			LOCTEXT("SectionOffers", "CONTRACT OFFERS").ToString());
		// The OFFER BOARD: real standing offers with real terms, minted
		// by the game mode and accepted by id. This used to be two
		// hard-coded buttons, always x1 at the catalogue price, that
		// minted and accepted a contract in one go - so the Offered
		// state never existed and there was no choice to make.
		if (HeldLedger != nullptr)
		{
			bool bAnyOffer = false;
			for (const FLBSpacecraftContract& Offer :
				HeldLedger->GetContracts())
			{
				if (Offer.State != ELBSpacecraftContractState::Offered)
				{
					continue;
				}
				bAnyOffer = true;
				AddTaggedButton(BuildOfferButtonLabel(Offer,
					HeldLedger->GetSimSeconds()),
					Offer.ContractId,
					[this](FName InTag) { HandleAcceptOffer(InTag); });
			}
			if (!bAnyOffer)
			{
				AddSectionLabel(LOCTEXT("NoOffers",
					"No offers on the board").ToString());
			}
		}
		break;
	}
	case ELBSpacecraftPanelTab::Research:
	{
		AddSectionLabel(Research != nullptr
			? FText::Format(LOCTEXT("SectionResearchPts",
					"RESEARCH  {0} pts banked"),
				Research->GetPoints()).ToString()
			: LOCTEXT("SectionResearch", "RESEARCH").ToString());
		const int32 Banked =
			Research != nullptr ? Research->GetPoints() : 0;
		for (const FLBSpacecraftResearchNode& Node :
			FLBSpacecraftResearchCatalogue::GetNodeTable())
		{
			const bool bUnlocked = Research != nullptr
				&& Research->IsNodeUnlocked(Node.NodeId);
			const FString Sub = bUnlocked
				? LOCTEXT("ResearchDone", "Unlocked").ToString()
				: FText::Format(LOCTEXT("ResearchPts", "{0} pts"),
					Node.CostPoints).ToString();
			ULBSpacecraftTaggedButton* Button = AddTaggedButton(
				Node.DisplayName, Node.NodeId,
				[this](FName InTag) { HandleResearch(InTag); },
				Sub, !bUnlocked && Node.CostPoints > Banked, bUnlocked);
			Button->SetIsEnabled(!bUnlocked);
		}
		break;
	}
	}
}

void ULBSpacecraftCommandPanelWidget::CycleTab(const int32 Direction)
{
	// Tab / Shift+Tab - the Car Manufacture section-change pair mapped
	// onto the panel's three tabs, wrapping both ways.
	const int32 TabCount = 3;
	const int32 Next = (static_cast<int32>(ActiveTab)
		+ (Direction >= 0 ? 1 : TabCount - 1)) % TabCount;
	ActiveTab = static_cast<ELBSpacecraftPanelTab>(Next);
	ScrollContentToTop();
	RefreshTabStyles();
}

void ULBSpacecraftCommandPanelWidget::HandleTab(FName TabTag)
{
	if (TabTag == FName(TEXT("BUILD")))
	{
		ActiveTab = ELBSpacecraftPanelTab::Build;
	}
	else if (TabTag == FName(TEXT("CONTRACTS")))
	{
		ActiveTab = ELBSpacecraftPanelTab::Contracts;
	}
	else
	{
		ActiveTab = ELBSpacecraftPanelTab::Research;
	}
	ScrollContentToTop();
	RefreshTabStyles();
}

void ULBSpacecraftCommandPanelWidget::ScrollContentToFraction(
	float Fraction)
{
	if (ContentScroll == nullptr)
	{
		return;
	}
	// The scroll box only knows its extent once it has been laid out,
	// so this is asked for AFTER a rebuild rather than during one.
	const float Extent = ContentScroll->GetScrollOffsetOfEnd();
	ContentScroll->SetScrollOffset(
		FMath::Clamp(Fraction, 0.f, 1.f) * Extent);
}

void ULBSpacecraftCommandPanelWidget::ScrollContentToTop()
{
	// On TAB CHANGE only. Doing it every refresh would drag the list out
	// from under a player mid-scroll, which is worse than opening low.
	if (ContentScroll != nullptr)
	{
		ContentScroll->ScrollToStart();
	}
}

void ULBSpacecraftCommandPanelWidget::HandleBuildStation(FName DefinitionId)
{
	if (Pawn != nullptr)
	{
		Pawn->SetPlacementDefinition(DefinitionId);
	}
}

void ULBSpacecraftCommandPanelWidget::HandleSelectRecipe(FName RecipeId)
{
	if (GameMode == nullptr || Pawn == nullptr
		|| GameMode->GetBuildAuthority() == nullptr
		|| GameMode->GetCraftingAuthority() == nullptr
		|| GameMode->GetResearchAuthority() == nullptr)
	{
		return;
	}
	FString Reason;
	if (ALBSpacecraftGameMode::SelectStationRecipe(
		*GameMode->GetBuildAuthority(), *GameMode->GetCraftingAuthority(),
		*GameMode->GetResearchAuthority(), Pawn->GetSelectedStation(),
		RecipeId, Reason))
	{
		PanelActionText = FText::Format(
			LOCTEXT("RecipeSelected", "Recipe {0} selected"),
			FText::FromName(RecipeId)).ToString();
	}
	else
	{
		PanelActionText = Reason;
	}
}

bool ULBSpacecraftCommandPanelWidget::SectionBelongsInView(
	EBuildSection Section, bool bOnSiteMap)
{
	switch (Section)
	{
	case EBuildSection::Catalogue:
		// Both views own a catalogue; they simply hold different
		// things, and the definitions themselves say which.
		return true;

	case EBuildSection::Session:
		// Saving is not a place, it is a moment. Wherever the player
		// happens to be standing when they need to stop, the button
		// has to be there.
		return true;

	case EBuildSection::FixingSplit:
	case EBuildSection::Track:
	case EBuildSection::MaterialReview:
		// A production line only exists INSIDE a building. On the
		// world map there is no line to split, no floor to lay track
		// across, and no craft standing on a test pad to make a
		// disposition about.
		return !bOnSiteMap;

	case EBuildSection::Land:
		// A bay is site land - bought by adjacency, refused when it
		// belongs to the launch corridor. Choosing one from inside a
		// building means choosing a square that is not on screen.
		return bOnSiteMap;
	}
	// Unreachable for the enumerators above, and deliberately FALSE:
	// a section nobody has classified should stay hidden until someone
	// decides where it belongs, rather than appear in both views.
	return false;
}

TArray<int32> ULBSpacecraftCommandPanelWidget::ComputeSplitShift(
	const TArray<int32>& Counts, int32 FromIndex, int32 ToIndex)
{
	// One part across one boundary, or nothing: a move that would take
	// from an empty slice, or reach off the line, returns empty and the
	// caller treats it as a refusal. Never a clamp - a clamped move
	// LOOKS like it worked.
	if (!Counts.IsValidIndex(FromIndex) || !Counts.IsValidIndex(ToIndex)
		|| FMath::Abs(FromIndex - ToIndex) != 1
		|| Counts[FromIndex] <= 0)
	{
		return TArray<int32>();
	}
	TArray<int32> Adjusted = Counts;
	--Adjusted[FromIndex];
	++Adjusted[ToIndex];
	return Adjusted;
}

void ULBSpacecraftCommandPanelWidget::HandleSplitTake(FName StationId)
{
	// "Take one from the next station": the part moves next -> here.
	ALBSpacecraftBuildAuthority* Build = GameMode != nullptr
		? GameMode->GetBuildAuthority() : nullptr;
	if (Build == nullptr)
	{
		return;
	}
	TArray<FName> Stations;
	TArray<int32> Counts;
	FString Reason;
	if (!Build->GetFixingSplit(LineRecipeId(), Stations, Counts,
		Reason))
	{
		PanelActionText = Reason;
		return;
	}
	const int32 Index = Stations.IndexOfByKey(StationId);
	const TArray<int32> Adjusted =
		ComputeSplitShift(Counts, Index + 1, Index);
	if (Adjusted.Num() == 0)
	{
		PanelActionText = LOCTEXT("SplitTakeRefused",
			"The next station has nothing to give").ToString();
		return;
	}
	// WRITES to the craft on the line, not to the Scout. Taking a
	// part from one station and giving it to the next while a
	// Cargo was being built used to edit the SCOUT's split - a
	// silent no-op on screen and a change to a craft nobody was
	// looking at.
	Build->SetFixingSplit(LineRecipeId(), Adjusted, Reason);
	PanelActionText = Reason;
}

void ULBSpacecraftCommandPanelWidget::HandleSplitGive(FName StationId)
{
	ALBSpacecraftBuildAuthority* Build = GameMode != nullptr
		? GameMode->GetBuildAuthority() : nullptr;
	if (Build == nullptr)
	{
		return;
	}
	TArray<FName> Stations;
	TArray<int32> Counts;
	FString Reason;
	if (!Build->GetFixingSplit(LineRecipeId(), Stations, Counts,
		Reason))
	{
		PanelActionText = Reason;
		return;
	}
	const int32 Index = Stations.IndexOfByKey(StationId);
	const TArray<int32> Adjusted =
		ComputeSplitShift(Counts, Index, Index + 1);
	if (Adjusted.Num() == 0)
	{
		PanelActionText = LOCTEXT("SplitGiveRefused",
			"This station has nothing to give").ToString();
		return;
	}
	// WRITES to the craft on the line, not to the Scout. Taking a
	// part from one station and giving it to the next while a
	// Cargo was being built used to edit the SCOUT's split - a
	// silent no-op on screen and a change to a craft nobody was
	// looking at.
	Build->SetFixingSplit(LineRecipeId(), Adjusted, Reason);
	PanelActionText = Reason;
}

FName ULBSpacecraftCommandPanelWidget::LineRecipeId() const
{
	const ALBSpacecraftProductionAuthority* Production =
		GameMode != nullptr ? GameMode->GetProductionAuthority() : nullptr;
	if (Production != nullptr)
	{
		// A craft ON THE LINE is what the stations are stocked for, so
		// it is the split the player needs to see. A refit counts: it
		// occupies stations and consumes their parts exactly as a new
		// build does.
		for (const FLBSpacecraftUnitState& Unit : Production->GetUnits())
		{
			if (Unit.Stage != ELBSpacecraftStage::Dispatched)
			{
				return Unit.RecipeId;
			}
		}
		// Nothing in flight: the oldest accepted order is what the line
		// will be stocked for next, which is more useful than showing
		// the split for a craft nobody has ordered.
		for (const FLBSpacecraftContract& Contract :
			Production->GetContracts())
		{
			if (Contract.State == ELBSpacecraftContractState::Accepted
				&& Contract.DispatchedCount < Contract.Quantity)
			{
				return Contract.RecipeId;
			}
		}
	}
	// An empty yard still has to render something, and the first tier
	// is the honest default - it is what an unconfigured line builds.
	return FName(TEXT("SCOUT-01"));
}

void ULBSpacecraftCommandPanelWidget::HandleOfferRefit(FName UnitId)
{
	if (GameMode == nullptr
		|| GameMode->GetProductionAuthority() == nullptr)
	{
		return;
	}
	FString Reason;
	FName ContractId;
	// HULL FABRICATION is the scope offered from the panel: it is the
	// earliest rung that leaves the returning craft its own hull, so it
	// re-fits everything else and is the fullest job a refit can be.
	// Narrower scopes exist in the authority and will want a picker
	// once there is more than one worth choosing between.
	if (GameMode->GetProductionAuthority()->OfferRefit(UnitId,
		ELBSpacecraftStage::HullFabrication, 0.0, ContractId, Reason))
	{
		Reason = FString::Printf(
			TEXT("%s is offered a refit - take it on the board"),
			*UnitId.ToString());
	}
	PanelActionText = Reason;
}

void ULBSpacecraftCommandPanelWidget::HandleStartRefit(FName ContractId)
{
	if (GameMode == nullptr
		|| GameMode->GetProductionAuthority() == nullptr)
	{
		return;
	}
	FString Reason;
	FName UnitId;
	if (GameMode->GetProductionAuthority()->CreateRefitUnit(
		ContractId, UnitId, Reason))
	{
		Reason = FString::Printf(TEXT("%s is back on the line"),
			*UnitId.ToString());
	}
	PanelActionText = Reason;
}

void ULBSpacecraftCommandPanelWidget::HandleConcede(FName UnitId)
{
	if (GameMode == nullptr
		|| GameMode->GetProductionAuthority() == nullptr)
	{
		return;
	}
	FString Reason;
	if (GameMode->GetProductionAuthority()->GrantConcession(UnitId, Reason))
	{
		// Says what was agreed, not merely that something happened. A
		// concession is the player signing for a deviation, and the
		// confirmation should read like a record of it.
		Reason = FString::Printf(
			TEXT("%s ships on a recorded concession"), *UnitId.ToString());
	}
	PanelActionText = Reason;
}

void ULBSpacecraftCommandPanelWidget::HandleScrap(FName UnitId)
{
	if (GameMode == nullptr
		|| GameMode->GetProductionAuthority() == nullptr)
	{
		return;
	}
	FString Reason;
	if (GameMode->GetProductionAuthority()->ScrapUnit(UnitId, Reason))
	{
		Reason = FString::Printf(TEXT("%s scrapped - the pad is clear"),
			*UnitId.ToString());
	}
	PanelActionText = Reason;
}

void ULBSpacecraftCommandPanelWidget::HandleBuyBay(FName Unused)
{
	(void)Unused;
	if (GameMode == nullptr || GameMode->GetProgression() == nullptr)
	{
		return;
	}
	ALBSpacecraftProgressionAuthority* Land = GameMode->GetProgression();
	// Deterministic pick: the first legal neighbour of owned land.
	static const FIntPoint Sides[] = {
		FIntPoint(1, 0), FIntPoint(0, 1),
		FIntPoint(0, -1), FIntPoint(-1, 0) };
	FString Reason = TEXT("No legal adjacent bay");
	const TArray<FIntPoint> Owned = Land->CaptureSnapshot().OwnedBays;
	bool bBought = false;
	for (int32 Bay = 0; Bay < Owned.Num() && !bBought; ++Bay)
	{
		for (const FIntPoint& Side : Sides)
		{
			if (!Land->IsBayOwned(Owned[Bay] + Side)
				&& Land->PurchaseBay(Owned[Bay] + Side,
					GameMode->GetProductionAuthority(), Reason))
			{
				bBought = true;
				break;
			}
		}
	}
	PanelActionText = Reason;
}

void ULBSpacecraftCommandPanelWidget::HandleImport(FName ItemId)
{
	if (GameMode == nullptr || GameMode->GetInventoryAuthority() == nullptr
		|| GameMode->GetProductionAuthority() == nullptr)
	{
		return;
	}
	// Goods land at a DELIVERY DOCK now - nothing teleports onto the
	// floor. No dock, or every dock backed up, refuses the order in
	// plain words.
	FString DockReason;
	const FName DeliveryStore = ALBSpacecraftGameMode::FindDeliveryStore(
		*GameMode->GetBuildAuthority(), *GameMode->GetInventoryAuthority(),
		ItemId, 5 * BuyMultiplier, DockReason);
	if (DeliveryStore.IsNone())
	{
		PanelActionText = DockReason;
		return;
	}
	FString Reason;
	ALBSpacecraftGameMode::PlaceResourceOrder(
		*GameMode->GetInventoryAuthority(),
		*GameMode->GetProductionAuthority(), ItemId, 5 * BuyMultiplier,
		DeliveryStore, Reason);
	PanelActionText = Reason;
}

void ULBSpacecraftCommandPanelWidget::HandleBelt(FName StationId)
{
	if (GameMode == nullptr
		|| GameMode->GetTransportAuthority() == nullptr
		|| GameMode->GetBuildAuthority() == nullptr
		|| GameMode->GetInventoryAuthority() == nullptr)
	{
		return;
	}
	FName RouteId;
	FString Reason;
	GameMode->GetTransportAuthority()->ConnectSupplyBelt(
		*GameMode->GetBuildAuthority(),
		*GameMode->GetInventoryAuthority(),
		GameMode->GetProductionAuthority(), StationId,
		FName(TEXT("Store.Floor")), RouteId, Reason,
		GameMode->GetProgression());
	PanelActionText = Reason;
}

void ULBSpacecraftCommandPanelWidget::HandleRemoveBelt(FName RouteId)
{
	if (GameMode == nullptr
		|| GameMode->GetTransportAuthority() == nullptr)
	{
		return;
	}
	FString Reason;
	GameMode->GetTransportAuthority()->DisconnectBelt(
		GameMode->GetProductionAuthority(), RouteId, Reason);
	PanelActionText = Reason;
}

void ULBSpacecraftCommandPanelWidget::HandleQuickSave()
{
	if (GameMode == nullptr)
	{
		return;
	}
	// THE REASON IS SHOWN EITHER WAY. A save that silently fails is
	// worse than no save at all - the player walks away believing their
	// factory is safe. QuickSave fills OutReason on success too, so the
	// same line reports both outcomes honestly.
	FString Reason;
	GameMode->QuickSave(Reason);
	PanelActionText = Reason;
	RebuildContent();
}

void ULBSpacecraftCommandPanelWidget::HandleQuickLoad()
{
	if (GameMode == nullptr)
	{
		return;
	}
	FString Reason;
	GameMode->QuickLoad(Reason);
	PanelActionText = Reason;
	if (Pawn != nullptr)
	{
		// Whatever was selected belonged to the factory that has just
		// been replaced, and a stale selection would point the panel at
		// a station that no longer exists.
		Pawn->ClearSelectedStation();
	}
	RebuildContent();
}

void ULBSpacecraftCommandPanelWidget::HandleRemoveStation(FName StationId)
{
	if (GameMode == nullptr || GameMode->GetBuildAuthority() == nullptr
		|| GameMode->GetPowerAuthority() == nullptr
		|| GameMode->GetInventoryAuthority() == nullptr)
	{
		return;
	}
	// Name it BEFORE it is gone: the toast prettifies ids against the
	// live station list, and a removed station is no longer in it -
	// "Removed ShipFactoryHall-001" was what the stranger read.
	const FString Shown =
		LBSpacecraftCommandPanelPrivate::SpacecraftPrettifyStationIds(
			StationId.ToString(), GameMode->GetBuildAuthority());
	FString Reason;
	if (ALBSpacecraftGameMode::RemoveStationPowered(
		*GameMode->GetBuildAuthority(), *GameMode->GetPowerAuthority(),
		*GameMode->GetInventoryAuthority(),
		GameMode->GetCraftingAuthority(), StationId, Reason,
		GameMode->GetProductionAuthority(), GameMode->GetCoordinator(),
		GameMode->GetTrackAuthority()))
	{
		PanelActionText = FText::Format(
			LOCTEXT("StationRemoved", "Removed {0}"),
			FText::FromString(Shown)).ToString();
		if (Pawn != nullptr)
		{
			Pawn->ClearSelectedStation();
		}
		// The line re-routes around the gap (owner 2026-09-01: the
		// track connects itself). A relay refusal is reported but the
		// removal stands - the station is already gone.
		if (GameMode->GetTrackAuthority() != nullptr)
		{
			FString RelayReason;
			if (!ALBSpacecraftGameMode::RelayTrackThroughStations(
				*GameMode->GetBuildAuthority(),
				*GameMode->GetTrackAuthority(), GameMode->GetCoordinator(),
				GameMode->GetProductionAuthority(), RelayReason))
			{
				PanelActionText = RelayReason;
			}
		}
	}
	else
	{
		PanelActionText = Reason;
	}
}

void ULBSpacecraftCommandPanelWidget::HandleCommission(FName Unused)
{
	(void)Unused;
	if (GameMode == nullptr || GameMode->GetBuildAuthority() == nullptr
		|| GameMode->GetCoordinator() == nullptr)
	{
		return;
	}
	FString Reason;
	if (GameMode->GetBuildAuthority()->CommissionFactory(Reason)
		&& GameMode->GetCoordinator()->ConfigureFromAuthorities(
			GameMode->GetBuildAuthority(),
			GameMode->GetProductionAuthority(), Reason,
			GameMode->GetTrackAuthority()))
	{
		PanelActionText = LOCTEXT("LineCommissioned",
			"Line commissioned and configured").ToString();
	}
	else
	{
		PanelActionText = Reason;
	}
}

FString ULBSpacecraftCommandPanelWidget::BuildOfferButtonLabel(
	const FLBSpacecraftContract& Offer, double SimSeconds)
{
	const int64 Whole = Offer.PricePerUnitPence
		* static_cast<int64>(FMath::Max(Offer.Quantity, 0));
	const FString Clock = Offer.DeadlineSimSeconds > 0.0
		? FString(TEXT(", "))
			+ FormatTimeRemaining(Offer.DeadlineSimSeconds - SimSeconds)
		: FString();
	const FLBSpacecraftCustomer* Customer =
		FLBSpacecraftCustomerCatalogue::FindCustomer(Offer.CustomerId);
	const FString Who = Customer != nullptr
		? Customer->DisplayName + TEXT(": ") : FString();
	return FText::Format(
		LOCTEXT("OfferButton",
			"{5}Accept {0} x{1}  ({2} each, {3} total{4})"),
		FText::FromName(Offer.RecipeId), Offer.Quantity,
		FText::FromString(ULBSpacecraftTopBarWidget::FormatCurrency(
			Offer.PricePerUnitPence)),
		FText::FromString(ULBSpacecraftTopBarWidget::FormatCurrency(
			Whole)),
		FText::FromString(Clock),
		FText::FromString(Who)).ToString();
}

void ULBSpacecraftCommandPanelWidget::HandleAcceptOffer(FName ContractId)
{
	if (GameMode == nullptr
		|| GameMode->GetProductionAuthority() == nullptr)
	{
		return;
	}
	FString Reason;
	if (GameMode->GetProductionAuthority()->AcceptContract(ContractId,
		Reason))
	{
		PanelActionText = FText::Format(
			LOCTEXT("OfferAccepted", "Contract accepted: {0}"),
			FText::FromName(ContractId)).ToString();
	}
	else
	{
		PanelActionText = Reason;
	}
}

void ULBSpacecraftCommandPanelWidget::HandleContract(FName RecipeId)
{
	if (GameMode == nullptr
		|| GameMode->GetProductionAuthority() == nullptr)
	{
		return;
	}
	FString Reason;
	if (ALBSpacecraftGameMode::StartRecipeContract(
		*GameMode->GetProductionAuthority(), RecipeId, 1, Reason,
		GameMode->GetReputation()))
	{
		PanelActionText = FText::Format(
			LOCTEXT("ContractAccepted", "Contract accepted: {0} x1"),
			FText::FromName(RecipeId)).ToString();
	}
	else
	{
		PanelActionText = Reason;
	}
}

void ULBSpacecraftCommandPanelWidget::HandleCycleBuyMultiplier(
	FName Unused)
{
	(void)Unused;
	BuyMultiplier = BuyMultiplier >= 20 ? 1
		: (BuyMultiplier >= 5 ? 20 : 5);
	// The labels carry the quantity and the price, so they have to be
	// rebuilt for the change to mean anything.
	RebuildContent();
}

void ULBSpacecraftCommandPanelWidget::HandleOrder(FName ItemId)
{
	if (GameMode == nullptr || GameMode->GetInventoryAuthority() == nullptr
		|| GameMode->GetProductionAuthority() == nullptr)
	{
		return;
	}
	// Raw materials land at a DELIVERY DOCK, like everything else the
	// player buys in.
	FString DockReason;
	const FName DeliveryStore = ALBSpacecraftGameMode::FindDeliveryStore(
		*GameMode->GetBuildAuthority(), *GameMode->GetInventoryAuthority(),
		ItemId, 10 * BuyMultiplier, DockReason);
	if (DeliveryStore.IsNone())
	{
		PanelActionText = DockReason;
		return;
	}
	FString Reason;
	ALBSpacecraftGameMode::PlaceResourceOrder(
		*GameMode->GetInventoryAuthority(),
		*GameMode->GetProductionAuthority(), ItemId, 10 * BuyMultiplier,
		DeliveryStore, Reason);
	PanelActionText = Reason;
}

// HandleLayTrack and HandleAttachNode are gone with the manual track
// (owner 2026-09-01): RelayTrackThroughStations lays and attaches.

void ULBSpacecraftCommandPanelWidget::HandleInstallDrone(FName StationId)
{
	if (GameMode == nullptr || GameMode->GetBuildAuthority() == nullptr)
	{
		return;
	}
	FString Reason;
	// The player's own crew purchase is the one the QUALITY CONTROL
	// milestone gates; the starter spine staffs itself unguarded.
	ALBSpacecraftGameMode::InstallStationDronePowered(
		*GameMode->GetBuildAuthority(), StationId, Reason,
		GameMode->GetProductionAuthority(), GameMode->GetProgression());
	PanelActionText = Reason;
}

void ULBSpacecraftCommandPanelWidget::HandleInstallDroneKind(FName KindId)
{
	if (GameMode == nullptr || Pawn == nullptr
		|| GameMode->GetBuildAuthority() == nullptr)
	{
		return;
	}
	FString Reason;
	ALBSpacecraftGameMode::InstallStationDronePowered(
		*GameMode->GetBuildAuthority(), Pawn->GetSelectedStation(), Reason,
		GameMode->GetProductionAuthority(), GameMode->GetProgression(),
		KindId);
	PanelActionText = Reason;
	// The fleet mirrors the station records, so a new crew member has
	// to be told about or it never appears on the floor.
	if (GameMode->GetDroneFleet() != nullptr)
	{
		GameMode->GetDroneFleet()->SyncFromBuild(
			GameMode->GetBuildAuthority(), GameMode->GetPowerAuthority());
	}
}

void ULBSpacecraftCommandPanelWidget::HandleDismissDrone(FName SlotTag)
{
	if (GameMode == nullptr || Pawn == nullptr
		|| GameMode->GetBuildAuthority() == nullptr)
	{
		return;
	}
	FString Reason;
	ALBSpacecraftGameMode::DismissStationDronePowered(
		*GameMode->GetBuildAuthority(), Pawn->GetSelectedStation(),
		FCString::Atoi(*SlotTag.ToString()), Reason,
		GameMode->GetProductionAuthority());
	PanelActionText = Reason;
	if (GameMode->GetDroneFleet() != nullptr)
	{
		GameMode->GetDroneFleet()->SyncFromBuild(
			GameMode->GetBuildAuthority(), GameMode->GetPowerAuthority());
	}
}

void ULBSpacecraftCommandPanelWidget::HandleToggleAllocation(
	FName ComponentItemId)
{
	if (GameMode == nullptr || Pawn == nullptr
		|| GameMode->GetBuildAuthority() == nullptr)
	{
		return;
	}
	const FName Selected = Pawn->GetSelectedStation();
	bool bCurrentlyOn = false;
	for (const FLBSpacecraftStationRecord& Record :
		GameMode->GetBuildAuthority()->GetStations())
	{
		if (Record.StationId == Selected)
		{
			bCurrentlyOn =
				Record.AllocatedComponents.Contains(ComponentItemId);
			break;
		}
	}
	FString Reason;
	GameMode->GetBuildAuthority()->SetComponentAllocated(Selected,
		ComponentItemId, !bCurrentlyOn, Reason);
	PanelActionText = Reason;
}

void ULBSpacecraftCommandPanelWidget::HandleOrderParts(FName StationId)
{
	if (GameMode == nullptr
		|| GameMode->GetCraftingAuthority() == nullptr)
	{
		return;
	}
	FString Reason;
	GameMode->GetCraftingAuthority()->AddOrder(StationId,
		5 * BuyMultiplier, Reason);
	PanelActionText = Reason;
}

void ULBSpacecraftCommandPanelWidget::HandleInstallUnit(
	FName UnitDefinitionId)
{
	if (GameMode == nullptr || Pawn == nullptr
		|| GameMode->GetBuildAuthority() == nullptr
		|| GameMode->GetPowerAuthority() == nullptr)
	{
		return;
	}
	FName UnitId;
	FString Reason;
	if (ALBSpacecraftGameMode::InstallInSlotPowered(
		*GameMode->GetBuildAuthority(), *GameMode->GetPowerAuthority(),
		Pawn->GetSelectedStation(), UnitDefinitionId, UnitId, Reason,
		GameMode->GetProductionAuthority(),
		GameMode->GetInventoryAuthority()))
	{
		PanelActionText = FText::Format(
			LOCTEXT("UnitInstalled", "Installed {0}"),
			FText::FromName(UnitId)).ToString();
	}
	else
	{
		PanelActionText = Reason;
	}
}

void ULBSpacecraftCommandPanelWidget::HandleResearch(FName NodeId)
{
	if (GameMode == nullptr || GameMode->GetResearchAuthority() == nullptr)
	{
		return;
	}
	FString Reason;
	GameMode->GetResearchAuthority()->UnlockNode(NodeId, Reason);
	PanelActionText = Reason;
}

void ULBSpacecraftCommandPanelWidget::NativeTick(const FGeometry& MyGeometry,
	float InDeltaTime)
{
	Super::NativeTick(MyGeometry, InDeltaTime);
	if (Pawn == nullptr)
	{
		Pawn = Cast<ALBSpacecraftPlayerPawn>(GetOwningPlayerPawn());
	}
	SecondsSinceRebuild += InDeltaTime;
	const FString Revision = ComputeRevision();
	// The throttle is churn insurance: even if a future revision field
	// churns per-frame, the panel never rebuilds faster than 4 Hz, so
	// a churn bug degrades to slight staleness instead of the garbled
	// never-settled layout the captures showed.
	if (Revision != LastRevision && SecondsSinceRebuild >= 0.25f)
	{
		LastRevision = Revision;
		SecondsSinceRebuild = 0.f;
		RebuildContent();
		// The rebuild frame PAINTS before Slate has measured the new
		// widgets, so for exactly one frame the whole panel renders as
		// an overlapped clump at the top. Invisible at the keyboard -
		// but the order clock's 5 s revision bucket puts rebuilds on
		// exact 5-second boundaries, and any screenshot armed with a
		// whole multiple of 5 lands on that same frame EVERY run (two
		// "garbled UI" captures in a row were this aliasing, proven by
		// a 26/28/30 s burst: clean, clean, garbled). Forcing the
		// prepass here means paint never sees unmeasured widgets.
		ForceLayoutPrepass();
	}
	if (ToastBlock != nullptr)
	{
		const FString PawnText =
			Pawn != nullptr ? Pawn->GetLastActionText() : FString();
		// The running factory's own complaints, shown when the player
		// has not just done something themselves. Without this a
		// machine could stall forever in silence.
		const FString SimAlert = GameMode != nullptr
			? GameMode->GetSimAlert() : FString();
		FString Combined = PanelActionText;
		if (!PawnText.IsEmpty())
		{
			if (!Combined.IsEmpty())
			{
				Combined += LINE_TERMINATOR;
			}
			Combined += PawnText;
		}
		// ACTION TEXT AGES OUT (audit 2026-09-01): neither action
		// string is ever cleared, so after the player's first click of
		// a session the sim's own complaints - resource stalls, start
		// refusals - were masked for good and the factory could sit
		// frozen in silence, defeating the channel built to prevent
		// exactly that. A read message is a read message: once the
		// same action text has stood for a few seconds, a live sim
		// alert outranks it.
		const double ToastNow = FPlatformTime::Seconds();
		if (Combined != ToastLastComposed)
		{
			ToastLastComposed = Combined;
			ToastComposedAt = ToastNow;
		}
		if (!SimAlert.IsEmpty()
			&& (Combined.IsEmpty() || ToastNow - ToastComposedAt > 8.0))
		{
			Combined = SimAlert;
		}
		ToastBlock->SetText(FText::FromString(
			LBSpacecraftCommandPanelPrivate::SpacecraftPrettifyStationIds(
				Combined, GameMode != nullptr
					? GameMode->GetBuildAuthority() : nullptr)));
		if (ToastBorder != nullptr)
		{
			ToastBorder->SetVisibility(Combined.IsEmpty()
				? ESlateVisibility::Collapsed
				: ESlateVisibility::HitTestInvisible);
		}
	}
}

#undef LOCTEXT_NAMESPACE
