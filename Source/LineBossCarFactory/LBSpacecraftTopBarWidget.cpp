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

UTextBlock* ULBSpacecraftTopBarWidget::MakeBarText(UHorizontalBox* Box,
	const FLinearColor& Colour, float LeftPadding)
{
	UTextBlock* Block = WidgetTree->ConstructWidget<UTextBlock>(
		UTextBlock::StaticClass());
	Block->SetColorAndOpacity(FSlateColor(Colour));
	FSlateFontInfo Font = Block->GetFont();
	Font.Size = 16;
	Block->SetFont(Font);
	if (UHorizontalBoxSlot* BoxSlot = Box->AddChildToHorizontalBox(Block))
	{
		BoxSlot->SetPadding(FMargin(LeftPadding, 6.f, 0.f, 6.f));
		BoxSlot->SetVerticalAlignment(VAlign_Center);
	}
	return Block;
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
		// A bar along the top, never a full-screen tint.
		BarCanvasSlot->SetAnchors(FAnchors(0.f, 0.f, 1.f, 0.f));
		BarCanvasSlot->SetOffsets(FMargin(0.f, 0.f, 0.f, 44.f));
	}

	UHorizontalBox* Box = WidgetTree->ConstructWidget<UHorizontalBox>(
		UHorizontalBox::StaticClass());
	Bar->SetContent(Box);
	if (UBorderSlot* BarSlot = Cast<UBorderSlot>(Box->Slot))
	{
		BarSlot->SetPadding(FMargin(18.f, 0.f));
	}

	// Sectioned readouts: credits lead larger; thin dividers separate
	// the groups the way the genre's status strips do.
	CashBlock = MakeBarText(Box, SpacecraftBarCash, 0.f);
	if (CashBlock != nullptr)
	{
		FSlateFontInfo CashFont = CashBlock->GetFont();
		CashFont.Size = 18;
		CashBlock->SetFont(CashFont);
	}
	MakeBarDivider(Box);
	ContractBlock = MakeBarText(Box, SpacecraftBarInfo, 0.f);
	ClockBlock = MakeBarText(Box, SpacecraftBarStatus, 24.f);
	MakeBarDivider(Box);
	LineBlock = MakeBarText(Box, SpacecraftBarInfo, 0.f);
	MakeBarDivider(Box);
	PowerBlock = MakeBarText(Box, SpacecraftBarStatus, 0.f);
	// The power GAUGE (owner 2026-08-26: "it has a gauge"): a slim
	// fill bar beside the readout, plus the buy/sell trade line.
	PowerGauge = WidgetTree->ConstructWidget<UProgressBar>(
		UProgressBar::StaticClass());
	PowerGauge->SetFillColorAndOpacity(SpacecraftBarInfo);
	USizeBox* GaugeSize = WidgetTree->ConstructWidget<USizeBox>(
		USizeBox::StaticClass());
	GaugeSize->SetWidthOverride(90.f);
	GaugeSize->SetHeightOverride(8.f);
	GaugeSize->AddChild(PowerGauge);
	if (UHorizontalBoxSlot* GaugeSlot =
		Box->AddChildToHorizontalBox(GaugeSize))
	{
		GaugeSlot->SetPadding(FMargin(10.f, 0.f, 0.f, 0.f));
		GaugeSlot->SetVerticalAlignment(VAlign_Center);
	}
	TradeBlock = MakeBarText(Box, SpacecraftBarStatus, 10.f);
	ResearchBlock = MakeBarText(Box, SpacecraftBarStatus, 24.f);
	ReputationBlock = MakeBarText(Box, SpacecraftBarStatus, 24.f);
	QualityBlock = MakeBarText(Box, SpacecraftBarStatus, 24.f);
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
		// The factory speed rides the clock (the Car Manufacture 1-4
		// row): "00:03:49" at 1x, "00:03:49  2x" / "PAUSED" otherwise.
		FString ClockWithSpeed = Snapshot.ClockText;
		if (const ALBSpacecraftGameMode* SpeedGameMode =
			ALBSpacecraftGameMode::FindInWorld(GetWorld()))
		{
			if (SpeedGameMode->GetSimSpeed() == 0.f)
			{
				ClockWithSpeed = SpeedGameMode->DescribeSimSpeed()
					.ToString();
			}
			else if (SpeedGameMode->GetSimSpeed() != 1.f)
			{
				ClockWithSpeed += TEXT("  ")
					+ SpeedGameMode->DescribeSimSpeed().ToString();
			}
			else
			{
				// The one place a waiting player looks. The stranger
				// playthrough (2026-09-02) found no way on screen to
				// learn that 1/2/4 set the factory speed.
				ClockWithSpeed += LOCTEXT("SpeedKeysHint",
					"  1x  (keys 1 / 2 / 4)").ToString();
			}
		}
		ClockBlock->SetText(FText::FromString(ClockWithSpeed));
	}
	if (LineBlock != nullptr)
	{
		LineBlock->SetText(FText::FromString(Snapshot.LineStatusText));
	}
	if (PowerBlock != nullptr)
	{
		PowerBlock->SetText(FText::FromString(Snapshot.PowerText));
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
		TradeBlock->SetText(FText::FromString(Snapshot.PowerTradeText));
		TradeBlock->SetColorAndOpacity(FSlateColor(
			Snapshot.PowerTradeText.StartsWith(TEXT("BUYING"))
				? SpacecraftBarWarn : SpacecraftBarInfo));
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
		ResearchBlock->SetText(FText::FromString(Snapshot.ResearchText));
	}
	if (ReputationBlock != nullptr)
	{
		ReputationBlock->SetText(
			FText::FromString(Snapshot.ReputationText));
	}
	if (QualityBlock != nullptr)
	{
		using namespace LBSpacecraftTopBarPrivate;
		QualityBlock->SetText(FText::FromString(Snapshot.QualityText));
		QualityBlock->SetColorAndOpacity(FSlateColor(
			Snapshot.bQualityAlarm ? SpacecraftBarWarn
				: SpacecraftBarInfo));
	}
}

#undef LOCTEXT_NAMESPACE
