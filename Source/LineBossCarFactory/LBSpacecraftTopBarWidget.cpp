#include "LBSpacecraftTopBarWidget.h"

#include "LBSpacecraftGameMode.h"

#include "Blueprint/WidgetTree.h"
#include "Components/Border.h"
#include "Components/BorderSlot.h"
#include "Components/CanvasPanel.h"
#include "Components/CanvasPanelSlot.h"
#include "Components/HorizontalBox.h"
#include "Components/HorizontalBoxSlot.h"
#include "Components/ProgressBar.h"
#include "Components/SizeBox.h"
#include "Components/TextBlock.h"
#include "Components/VerticalBox.h"
#include "Components/VerticalBoxSlot.h"
#include "LBSpacecraftCommandPanelWidget.h"
#include "LBSpacecraftPlayerPawn.h"
#include "LBSpacecraftDifficulty.h"

#define LOCTEXT_NAMESPACE "LBSpacecraftHUD"

namespace LBSpacecraftTopBarPrivate
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
	// Unity-build safety: helpers qualified by subject. Colours are the
	// PROVISIONAL indicator language (blue/white); no brand colours exist.
	const FLinearColor SpacecraftBarBackground =
		SpacecraftUiToken(TEXT("#1B1B1B"), 0.94f);   // Panel.Bg
	// Cash is a NUMERAL, and numerals are the one thing the palette
	// gives pure white to.
	const FLinearColor SpacecraftBarCash =
		SpacecraftUiToken(TEXT("#FFFFFF"));          // Text.Value
	const FLinearColor SpacecraftBarInfo =
		SpacecraftUiToken(TEXT("#A8A4A1"));          // Text.Heading
	const FLinearColor SpacecraftBarStatus =
		SpacecraftUiToken(TEXT("#EDEDEC"));          // Text.Body
	const FLinearColor SpacecraftBarWarn =
		SpacecraftUiToken(TEXT("#EC3013"));          // refusal
	const FLinearColor SpacecraftBarDivider =
		SpacecraftUiToken(TEXT("#363433"), 0.85f);   // Panel.Rule
	const FLinearColor SpacecraftBarChip =
		SpacecraftUiToken(TEXT("#232322"));          // Panel.BgRaised
	const FLinearColor SpacecraftBarChipLive =
		SpacecraftUiToken(TEXT("#4A4D50"));          // Structure.Graphite
	const FLinearColor SpacecraftBarChipHover =
		SpacecraftUiToken(TEXT("#363433"));

	/** The snapshot texts carry their own three-letter labels for the
	 *  tests and the log; the gauge cell already says the word, so the
	 *  bar shows the number alone. */
	FString SpacecraftBarStripPrefix(const FString& Text, const TCHAR* Prefix)
	{
		return Text.StartsWith(Prefix) ? Text.Mid(FCString::Strlen(Prefix))
			: Text;
	}

	/** A gauge with nothing to say hides its word too: "GRID" over a
	 *  blank read as a broken readout (frame audit, 2026-09-02). */
	void SpacecraftBarShowGauge(UTextBlock* Block, const FString& Text)
	{
		if (Block == nullptr)
		{
			return;
		}
		Block->SetText(FText::FromString(Text));
		if (UWidget* Cell = Block->GetParent())
		{
			Cell->SetVisibility(Text.IsEmpty()
				? ESlateVisibility::Collapsed
				: ESlateVisibility::SelfHitTestInvisible);
		}
	}

	FButtonStyle SpacecraftBarChipStyle(bool bLive)
	{
		FButtonStyle Style;
		Style.SetNormal(FSlateRoundedBoxBrush(
			bLive ? SpacecraftBarChipLive : SpacecraftBarChip, 3.f));
		Style.SetHovered(FSlateRoundedBoxBrush(SpacecraftBarChipHover, 3.f));
		Style.SetPressed(FSlateRoundedBoxBrush(SpacecraftBarChipLive, 3.f));
		Style.SetNormalPadding(FMargin(7.f, 1.f));
		Style.SetPressedPadding(FMargin(7.f, 2.f, 7.f, 0.f));
		return Style;
	}
}

FString ULBSpacecraftTopBarWidget::FormatCurrency(int64 Hundredths)
{
	const bool bNegative = Hundredths < 0;
	int64 Credits = FMath::Abs(Hundredths) / 100;
	FString Digits = FString::Printf(TEXT("%lld"), Credits);
	FString Grouped;
	int32 Count = 0;
	for (int32 Index = Digits.Len() - 1; Index >= 0; --Index)
	{
		Grouped.InsertAt(0, Digits[Index]);
		if (++Count % 3 == 0 && Index > 0)
		{
			Grouped.InsertAt(0, TEXT(","));
		}
	}
	// Suffix unit, locale-neutral (owner: Credits, never £/GBP).
	return FString::Printf(TEXT("%s%s cr"),
		bNegative ? TEXT("-") : TEXT(""), *Grouped);
}

FString ULBSpacecraftTopBarWidget::FormatSimClock(double SimSeconds)
{
	const int64 Total = FMath::Max<int64>(0,
		static_cast<int64>(SimSeconds));
	return FString::Printf(TEXT("%02lld:%02lld:%02lld"),
		Total / 3600, (Total / 60) % 60, Total % 60);
}

FString ULBSpacecraftTopBarWidget::FormatQualityText(int32 DefectPoints,
	float ReworkSecondsRemaining, bool& bOutAlarm)
{
	bOutAlarm = false;
	if (ReworkSecondsRemaining > 0.f)
	{
		bOutAlarm = true;
		return FText::Format(LOCTEXT("QualityRework", "Reworking {0}s"),
			FMath::CeilToInt(ReworkSecondsRemaining)).ToString();
	}
	if (DefectPoints > 0)
	{
		// The DIFFICULTY'S tolerance, not the hard-coded one. This called
		// DefectsPassHoverTest, which bakes in a tolerance of 1, while
		// the gate that actually fires calls DefectsPassHoverTestAt with
		// the difficulty's value - so on Relaxed (3) or Demanding (0)
		// the HUD alarm disagreed with the test that decides.
		bOutAlarm = !FLBSpacecraftProductionCatalog::DefectsPassHoverTestAt(
			DefectPoints,
			FLBSpacecraftDifficulty::Current().HoverTestDefectTolerance);
		return FText::Format(LOCTEXT("QualityDefects", "Defects {0}"),
			DefectPoints).ToString();
	}
	return FString();
}

FLBSpacecraftHUDSnapshot ULBSpacecraftTopBarWidget::BuildSnapshot(
	const ALBSpacecraftBuildAuthority* InBuild,
	const ALBSpacecraftProductionAuthority* InProduction,
	const ALBSpacecraftRuntimeCoordinator* InCoordinator,
	const ALBSpacecraftPowerAuthority* InPower,
	const ALBSpacecraftResearchAuthority* InResearch,
	const ALBSpacecraftReputationAuthority* InReputation)
{
	FLBSpacecraftHUDSnapshot Snapshot;
	// Honest empty states - never fabricated numbers. All display text is
	// localization-ready (owner, 2026-08-25: the game ships translated).
	Snapshot.CashText = TEXT("-- cr");
	Snapshot.ContractText =
		LOCTEXT("NoContract", "No contract").ToString();
	Snapshot.ClockText = TEXT("--:--:--");
	Snapshot.LineStatusText =
		LOCTEXT("NoFactory", "No factory").ToString();
	Snapshot.PowerText = LOCTEXT("PowerUnknown", "PWR --").ToString();
	Snapshot.ResearchText =
		LOCTEXT("ResearchUnknown", "RSC --").ToString();
	Snapshot.ReputationText =
		LOCTEXT("ReputationUnknown", "REP --").ToString();
	if (InPower != nullptr)
	{
		Snapshot.PowerText = FText::Format(
			LOCTEXT("PowerReadout", "PWR {0}/{1} kW"),
			InPower->GetTotalDrawKw(),
			InPower->GetTotalSupplyKw()).ToString();
		// The gauge and the trade line (Car Manufacture model): buying
		// warns, selling earns, both named in kilowatts.
		if (InPower->GetGridUseKw() > 0)
		{
			Snapshot.PowerTradeText = FText::Format(
				LOCTEXT("PowerBuying", "Buying {0} kW"),
				InPower->GetGridUseKw()).ToString();
		}
		else if (InPower->GetGridExportKw() > 0)
		{
			Snapshot.PowerTradeText = FText::Format(
				LOCTEXT("PowerSelling", "Selling {0} kW"),
				InPower->GetGridExportKw()).ToString();
		}
		Snapshot.PowerLoad01 = InPower->GetTotalSupplyKw() > 0
			? FMath::Clamp(
				static_cast<float>(InPower->GetTotalDrawKw())
				/ static_cast<float>(InPower->GetTotalSupplyKw()),
				0.f, 1.f)
			: 0.f;
	}
	if (InResearch != nullptr)
	{
		Snapshot.ResearchText = FText::Format(
			LOCTEXT("ResearchReadout", "RSC {0} pts  {1}/{2}"),
			InResearch->GetPoints(), InResearch->GetUnlockedNodeCount(),
			FLBSpacecraftResearchCatalogue::GetNodeTable().Num())
			.ToString();
	}
	if (InReputation != nullptr)
	{
		Snapshot.ReputationText = FText::Format(
			LOCTEXT("ReputationReadout", "REP T{0}  {1} pts"),
			InReputation->GetTier(), InReputation->GetPoints()).ToString();
	}
	if (InProduction != nullptr)
	{
		// WORKMANSHIP, shown before it costs money. The worst news on
		// the floor wins the line: a craft in rework outranks one
		// merely carrying defects.
		float WorstRework = 0.f;
		int32 WorstDefects = 0;
		for (const FLBSpacecraftUnitState& Unit : InProduction->GetUnits())
		{
			if (Unit.bCompleted)
			{
				continue;
			}
			WorstRework = FMath::Max(WorstRework,
				Unit.ReworkSecondsRemaining);
			WorstDefects = FMath::Max(WorstDefects, Unit.DefectPoints);
		}
		Snapshot.QualityText = FormatQualityText(WorstDefects,
			WorstRework, Snapshot.bQualityAlarm);
		Snapshot.CashText = FormatCurrency(
			InProduction->GetCashPence());
		Snapshot.ClockText = FormatSimClock(InProduction->GetSimSeconds());

		// The oldest accepted contract with demand left is "the" contract;
		// otherwise the newest completed one is shown as done.
		const FLBSpacecraftContract* Active = nullptr;
		const FLBSpacecraftContract* Late = nullptr;
		const FLBSpacecraftContract* LastComplete = nullptr;
		for (const FLBSpacecraftContract& Contract :
			InProduction->GetContracts())
		{
			if (Contract.State == ELBSpacecraftContractState::Accepted
				&& Contract.DispatchedCount < Contract.Quantity
				&& Active == nullptr)
			{
				Active = &Contract;
			}
			// An order taken on and missed still shows - "No contract"
			// beside a held contract marked Late read as a contradiction
			// (stranger playthrough, 2026-09-02).
			if (Contract.State == ELBSpacecraftContractState::Expired
				&& Contract.DispatchedCount < Contract.Quantity
				&& Late == nullptr)
			{
				Late = &Contract;
			}
			if (Contract.State == ELBSpacecraftContractState::Complete)
			{
				LastComplete = &Contract;
			}
		}
		if (Active != nullptr)
		{
			Snapshot.ContractText = FText::Format(
				LOCTEXT("ContractProgress", "{0}  {1}/{2}"),
				FText::FromName(Active->RecipeId),
				Active->DispatchedCount, Active->Quantity).ToString();
		}
		else if (Late != nullptr)
		{
			Snapshot.ContractText = FText::Format(
				LOCTEXT("ContractLate", "{0}  LATE {1}/{2}"),
				FText::FromName(Late->RecipeId),
				Late->DispatchedCount, Late->Quantity).ToString();
		}
		else if (LastComplete != nullptr)
		{
			Snapshot.ContractText = FText::Format(
				LOCTEXT("ContractComplete", "{0}  Complete"),
				FText::FromName(LastComplete->RecipeId)).ToString();
		}
	}
	if (InBuild != nullptr)
	{
		if (!InBuild->IsCommissioned())
		{
			// The count is the FACTORY's stations. The ship factory
			// building itself is not one of them - a player who has
			// just placed their hall on the world map is still being
			// told to build the line, which is exactly right.
			int32 Machines = 0;
			for (const FLBSpacecraftStationRecord& Record :
				InBuild->GetStations())
			{
				const FLBSpacecraftStationDefinition* Definition =
					ALBSpacecraftBuildAuthority::FindDefinition(
						Record.DefinitionId);
				if (Definition != nullptr && !Definition->bSiteBuilding)
				{
					++Machines;
				}
			}
			Snapshot.LineStatusText = Machines == 0
				? LOCTEXT("BuildTheLine", "Build the line").ToString()
				: FText::Format(LOCTEXT("NotCommissioned",
						"{0} stations - not commissioned"),
					Machines).ToString();
		}
		else
		{
			int32 InFlight = 0;
			int32 Waiting = 0;
			bool bMoving = false;
			if (InCoordinator != nullptr)
			{
				InFlight = InCoordinator->GetAssignments().Num();
				Waiting = InCoordinator->CountStopComplete();
				bMoving = InCoordinator->GetLinePhase()
					== ELBSpacecraftLinePhase::Moving;
			}
			// THE PULSE, said plainly (PULSE_LINE_DESIGN_v001): the
			// cranes are moving, or the line is stopped with some
			// stations done and holding for the rest.
			if (InFlight > 0 && bMoving)
			{
				Snapshot.LineStatusText = FText::Format(LOCTEXT(
					"LinePulsing",
					"Line running - PULSE, cranes moving {0} craft"),
					Waiting).ToString();
			}
			else if (InFlight > 0 && Waiting > 0)
			{
				Snapshot.LineStatusText = FText::Format(LOCTEXT(
					"LineWaiting",
					"Line running - {0} craft, {1} done and waiting for the pulse"),
					InFlight, Waiting).ToString();
			}
			else
			{
				Snapshot.LineStatusText = InFlight > 0
					? FText::Format(LOCTEXT("LineRunning",
							"Line running - {0} craft"), InFlight).ToString()
					: LOCTEXT("LineIdle", "Line idle").ToString();
			}
			// A SHIP IN STOCK IS NEVER INVISIBLE (overnight stranger
			// run, 2026-09-01: the first ship finished after its
			// contract expired, sold to nobody, and simply vanished
			// from every readout - the player's whole output looked
			// lost). Stock self-sells the moment a matching contract
			// is accepted, and this line is what says so.
			if (InProduction != nullptr
				&& InProduction->GetStockedCraftCount() > 0)
			{
				Snapshot.LineStatusText += FText::Format(LOCTEXT(
					"StockedCraft",
					" - {0} IN STOCK (accept a contract to sell)"),
					InProduction->GetStockedCraftCount()).ToString();
			}
		}
	}
	return Snapshot;
}

void ULBSpacecraftTopBarWidget::BindAuthorities(
	ALBSpacecraftBuildAuthority* InBuild,
	ALBSpacecraftProductionAuthority* InProduction,
	ALBSpacecraftRuntimeCoordinator* InCoordinator,
	ALBSpacecraftPowerAuthority* InPower,
	ALBSpacecraftResearchAuthority* InResearch,
	ALBSpacecraftReputationAuthority* InReputation)
{
	BuildAuthority = InBuild;
	ProductionAuthority = InProduction;
	Coordinator = InCoordinator;
	PowerAuthority = InPower;
	ResearchAuthority = InResearch;
	ReputationAuthority = InReputation;
}

UTextBlock* ULBSpacecraftTopBarWidget::MakeBarGauge(UHorizontalBox* Box,
	const FText& Label, const FLinearColor& Colour, float LeftPadding,
	UProgressBar** OutMeter)
{
	using namespace LBSpacecraftTopBarPrivate;
	UVerticalBox* Cell = WidgetTree->ConstructWidget<UVerticalBox>(
		UVerticalBox::StaticClass());
	// The word: small caps, heading grey, spaced.
	UTextBlock* Word = WidgetTree->ConstructWidget<UTextBlock>(
		UTextBlock::StaticClass());
	Word->SetText(FText::FromString(Label.ToString().ToUpper()));
	Word->SetColorAndOpacity(FSlateColor(SpacecraftBarInfo));
	FSlateFontInfo WordFont = Word->GetFont();
	WordFont.Size = 9;
	WordFont.LetterSpacing = 140;
	Word->SetFont(WordFont);
	Cell->AddChildToVerticalBox(Word);
	// The number.
	UTextBlock* Block = WidgetTree->ConstructWidget<UTextBlock>(
		UTextBlock::StaticClass());
	Block->SetColorAndOpacity(FSlateColor(Colour));
	FSlateFontInfo Font = Block->GetFont();
	Font.Size = 16;
	Block->SetFont(Font);
	if (UVerticalBoxSlot* BlockSlot = Cell->AddChildToVerticalBox(Block))
	{
		BlockSlot->SetPadding(FMargin(0.f, 1.f, 0.f, 0.f));
	}
	// The meter, when the gauge has one.
	if (OutMeter != nullptr)
	{
		UProgressBar* Meter = WidgetTree->ConstructWidget<UProgressBar>(
			UProgressBar::StaticClass());
		Meter->SetFillColorAndOpacity(SpacecraftBarInfo);
		USizeBox* MeterSize = WidgetTree->ConstructWidget<USizeBox>(
			USizeBox::StaticClass());
		MeterSize->SetHeightOverride(5.f);
		MeterSize->AddChild(Meter);
		if (UVerticalBoxSlot* MeterSlot =
			Cell->AddChildToVerticalBox(MeterSize))
		{
			MeterSlot->SetPadding(FMargin(0.f, 3.f, 0.f, 0.f));
		}
		*OutMeter = Meter;
	}
	if (UHorizontalBoxSlot* BoxSlot = Box->AddChildToHorizontalBox(Cell))
	{
		BoxSlot->SetPadding(FMargin(LeftPadding, 5.f, 0.f, 5.f));
		BoxSlot->SetVerticalAlignment(VAlign_Center);
	}
	return Block;
}

void ULBSpacecraftTopBarWidget::MakeSpeedChips(UHorizontalBox* Box)
{
	using namespace LBSpacecraftTopBarPrivate;
	// SPEED AS BUTTONS (UI direction step 4): pause, 1x, 2x, 4x as four
	// chips, the live one filled. The keys still work; the chips are
	// how a stranger finds out they exist.
	UVerticalBox* Cell = WidgetTree->ConstructWidget<UVerticalBox>(
		UVerticalBox::StaticClass());
	UTextBlock* Word = WidgetTree->ConstructWidget<UTextBlock>(
		UTextBlock::StaticClass());
	Word->SetText(LOCTEXT("SpeedWord", "SPEED   KEYS 1 2 4"));
	Word->SetColorAndOpacity(FSlateColor(SpacecraftBarInfo));
	FSlateFontInfo WordFont = Word->GetFont();
	WordFont.Size = 9;
	WordFont.LetterSpacing = 140;
	Word->SetFont(WordFont);
	Cell->AddChildToVerticalBox(Word);
	UHorizontalBox* Chips = WidgetTree->ConstructWidget<UHorizontalBox>(
		UHorizontalBox::StaticClass());
	struct FChip { const TCHAR* Tag; FText Label; };
	const FChip ChipDefs[] = {
		{ TEXT("0"), LOCTEXT("ChipPause", "II") },
		{ TEXT("1"), LOCTEXT("Chip1", "1x") },
		{ TEXT("2"), LOCTEXT("Chip2", "2x") },
		{ TEXT("4"), LOCTEXT("Chip4", "4x") } };
	for (const FChip& Def : ChipDefs)
	{
		ULBSpacecraftTaggedButton* Chip =
			WidgetTree->ConstructWidget<ULBSpacecraftTaggedButton>(
				ULBSpacecraftTaggedButton::StaticClass());
		Chip->Tag = FName(Def.Tag);
		Chip->OnTagClicked = [this](FName InTag) { HandleSpeedChip(InTag); };
		Chip->Arm();
		Chip->SetStyle(SpacecraftBarChipStyle(false));
		UTextBlock* Text = WidgetTree->ConstructWidget<UTextBlock>(
			UTextBlock::StaticClass());
		Text->SetText(Def.Label);
		Text->SetColorAndOpacity(FSlateColor(SpacecraftBarStatus));
		FSlateFontInfo Font = Text->GetFont();
		Font.Size = 12;
		Text->SetFont(Font);
		Chip->AddChild(Text);
		if (UHorizontalBoxSlot* ChipSlot = Chips->AddChildToHorizontalBox(Chip))
		{
			ChipSlot->SetPadding(FMargin(0.f, 2.f, 4.f, 0.f));
		}
		SpeedChips.Add(Chip);
	}
	Cell->AddChildToVerticalBox(Chips);
	if (UHorizontalBoxSlot* BoxSlot = Box->AddChildToHorizontalBox(Cell))
	{
		BoxSlot->SetPadding(FMargin(18.f, 5.f, 0.f, 5.f));
		BoxSlot->SetVerticalAlignment(VAlign_Center);
	}
}

void ULBSpacecraftTopBarWidget::HandleSpeedChip(FName Tag)
{
	if (ALBSpacecraftPlayerPawn* Pawn =
		Cast<ALBSpacecraftPlayerPawn>(GetOwningPlayerPawn()))
	{
		Pawn->SetSimSpeedWithToast(FCString::Atof(*Tag.ToString()));
	}
}

void ULBSpacecraftTopBarWidget::NativeOnInitialized()
{
	Super::NativeOnInitialized();
	using namespace LBSpacecraftTopBarPrivate;

	UCanvasPanel* Canvas = WidgetTree->ConstructWidget<UCanvasPanel>(
		UCanvasPanel::StaticClass(), TEXT("TopBarCanvas"));
	WidgetTree->RootWidget = Canvas;
	UBorder* Bar = WidgetTree->ConstructWidget<UBorder>(
		UBorder::StaticClass(), TEXT("TopBarRoot"));
	Bar->SetBrushColor(SpacecraftBarBackground);
	if (UCanvasPanelSlot* BarCanvasSlot = Canvas->AddChildToCanvas(Bar))
	{
		// A bar along the top, never a full-screen tint. Two lines
		// tall now that every readout is a word over a number.
		BarCanvasSlot->SetAnchors(FAnchors(0.f, 0.f, 1.f, 0.f));
		BarCanvasSlot->SetOffsets(FMargin(0.f, 0.f, 0.f, 56.f));
	}

	UHorizontalBox* Box = WidgetTree->ConstructWidget<UHorizontalBox>(
		UHorizontalBox::StaticClass());
	Bar->SetContent(Box);
	if (UBorderSlot* BarSlot = Cast<UBorderSlot>(Box->Slot))
	{
		BarSlot->SetPadding(FMargin(18.f, 0.f));
	}

	// LABELLED GAUGES (UI direction step 4, 2026-09-02): each readout
	// is a word over a number, the power one with a meter, the speed
	// as buttons. Credits lead larger; thin rules separate the groups.
	CashBlock = MakeBarGauge(Box, LOCTEXT("GaugeCredits", "Credits"),
		SpacecraftBarCash, 0.f);
	if (CashBlock != nullptr)
	{
		FSlateFontInfo CashFont = CashBlock->GetFont();
		CashFont.Size = 18;
		CashBlock->SetFont(CashFont);
	}
	MakeBarDivider(Box);
	ContractBlock = MakeBarGauge(Box, LOCTEXT("GaugeContract", "Contract"),
		SpacecraftBarStatus, 0.f);
	ClockBlock = MakeBarGauge(Box, LOCTEXT("GaugeClock", "Clock"),
		SpacecraftBarStatus, 24.f);
	MakeSpeedChips(Box);
	MakeBarDivider(Box);
	LineBlock = MakeBarGauge(Box, LOCTEXT("GaugeLine", "Line"),
		SpacecraftBarStatus, 0.f);
	MakeBarDivider(Box);
	UProgressBar* Meter = nullptr;
	PowerBlock = MakeBarGauge(Box, LOCTEXT("GaugePower", "Power"),
		SpacecraftBarStatus, 0.f, &Meter);
	PowerGauge = Meter;
	TradeBlock = MakeBarGauge(Box, LOCTEXT("GaugeGrid", "Grid"),
		SpacecraftBarStatus, 18.f);
	ResearchBlock = MakeBarGauge(Box, LOCTEXT("GaugeResearch", "Research"),
		SpacecraftBarStatus, 24.f);
	ReputationBlock = MakeBarGauge(Box,
		LOCTEXT("GaugeReputation", "Reputation"), SpacecraftBarStatus, 24.f);
	QualityBlock = MakeBarGauge(Box, LOCTEXT("GaugeQuality", "Quality"),
		SpacecraftBarStatus, 24.f);
}

void ULBSpacecraftTopBarWidget::MakeBarDivider(UHorizontalBox* Box)
{
	using namespace LBSpacecraftTopBarPrivate;
	UBorder* Divider = WidgetTree->ConstructWidget<UBorder>(
		UBorder::StaticClass());
	Divider->SetBrushColor(SpacecraftBarDivider);
	Divider->SetPadding(FMargin(0.5f, 0.f));
	if (UHorizontalBoxSlot* DividerSlot =
		Box->AddChildToHorizontalBox(Divider))
	{
		DividerSlot->SetPadding(FMargin(20.f, 10.f, 20.f, 10.f));
	}
}

void ULBSpacecraftTopBarWidget::NativeTick(const FGeometry& MyGeometry,
	float InDeltaTime)
{
	Super::NativeTick(MyGeometry, InDeltaTime);
	using namespace LBSpacecraftTopBarPrivate;
	const FLBSpacecraftHUDSnapshot Snapshot = BuildSnapshot(
		BuildAuthority, ProductionAuthority, Coordinator, PowerAuthority,
		ResearchAuthority, ReputationAuthority);
	if (CashBlock != nullptr)
	{
		CashBlock->SetText(FText::FromString(Snapshot.CashText));
	}
	if (ContractBlock != nullptr)
	{
		ContractBlock->SetText(FText::FromString(Snapshot.ContractText));
	}
	if (ClockBlock != nullptr)
	{
		ClockBlock->SetText(FText::FromString(Snapshot.ClockText));
	}
	if (const ALBSpacecraftGameMode* SpeedGameMode =
		ALBSpacecraftGameMode::FindInWorld(GetWorld()))
	{
		// The live speed chip is the filled one.
		using namespace LBSpacecraftTopBarPrivate;
		const float Speed = SpeedGameMode->GetSimSpeed();
		for (ULBSpacecraftTaggedButton* Chip : SpeedChips)
		{
			if (Chip != nullptr)
			{
				Chip->SetStyle(SpacecraftBarChipStyle(FMath::IsNearlyEqual(
					FCString::Atof(*Chip->Tag.ToString()), Speed)));
			}
		}
	}
	if (LineBlock != nullptr)
	{
		LineBlock->SetText(FText::FromString(Snapshot.LineStatusText));
	}
	if (PowerBlock != nullptr)
	{
		PowerBlock->SetText(FText::FromString(SpacecraftBarStripPrefix(
			Snapshot.PowerText, TEXT("PWR "))));
		// Power reads warning-orange when the budget is nearly spent
		// and stays status-grey otherwise - the honest early warning.
		using namespace LBSpacecraftTopBarPrivate;
		FLinearColor PowerColour = SpacecraftBarStatus;
		if (PowerAuthority != nullptr
			&& PowerAuthority->GetTotalSupplyKw() > 0
			&& PowerAuthority->GetTotalDrawKw() * 100
				>= PowerAuthority->GetTotalSupplyKw() * 85)
		{
			PowerColour = SpacecraftBarWarn;
		}
		PowerBlock->SetColorAndOpacity(FSlateColor(PowerColour));
	}
	if (TradeBlock != nullptr)
	{
		using namespace LBSpacecraftTopBarPrivate;
		SpacecraftBarShowGauge(TradeBlock, Snapshot.PowerTradeText);
		// Buying grid power is a cost, not a refusal: the palette keeps
		// #EC3013 for refusals alone, and red here read as an error on
		// a line that was running normally (audit, 2026-09-02).
		TradeBlock->SetColorAndOpacity(FSlateColor(
			Snapshot.PowerTradeText.StartsWith(TEXT("BUYING"))
				? SpacecraftBarStatus : SpacecraftBarInfo));
	}
	if (PowerGauge != nullptr)
	{
		PowerGauge->SetPercent(Snapshot.PowerLoad01);
		using namespace LBSpacecraftTopBarPrivate;
		PowerGauge->SetFillColorAndOpacity(Snapshot.PowerLoad01 > 0.85f
			? SpacecraftBarWarn : SpacecraftBarInfo);
	}
	if (ResearchBlock != nullptr)
	{
		ResearchBlock->SetText(FText::FromString(SpacecraftBarStripPrefix(
			Snapshot.ResearchText, TEXT("RSC "))));
	}
	if (ReputationBlock != nullptr)
	{
		ReputationBlock->SetText(FText::FromString(SpacecraftBarStripPrefix(
			Snapshot.ReputationText, TEXT("REP "))));
	}
	if (QualityBlock != nullptr)
	{
		using namespace LBSpacecraftTopBarPrivate;
		SpacecraftBarShowGauge(QualityBlock, Snapshot.QualityText);
		QualityBlock->SetColorAndOpacity(FSlateColor(
			Snapshot.bQualityAlarm ? SpacecraftBarWarn
				: SpacecraftBarInfo));
	}
}

#undef LOCTEXT_NAMESPACE
