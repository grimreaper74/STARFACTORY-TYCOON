#if WITH_DEV_AUTOMATION_TESTS

#include "LBSpacecraftGameMode.h"
#include "LBSpacecraftTopBarWidget.h"

#include "LBSpacecraftReputationAuthority.h"

#include "Engine/World.h"
#include "Misc/AutomationTest.h"

IMPLEMENT_SIMPLE_AUTOMATION_TEST(FLBSpacecraftHUDFormattingTest,
	"LineBoss.Spacecraft.HUD.FormattersAreExact",
	EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)

bool FLBSpacecraftHUDFormattingTest::RunTest(const FString& Parameters)
{
	(void)Parameters;
	TestEqual(TEXT("zero credits"),
		ULBSpacecraftTopBarWidget::FormatCurrency(0), TEXT("0 cr"));
	TestEqual(TEXT("50,000 credits"),
		ULBSpacecraftTopBarWidget::FormatCurrency(5000000),
		TEXT("50,000 cr"));
	TestEqual(TEXT("1,234,567 credits floors the hundredths"),
		ULBSpacecraftTopBarWidget::FormatCurrency(123456789),
		TEXT("1,234,567 cr"));
	TestEqual(TEXT("negative cash keeps the sign"),
		ULBSpacecraftTopBarWidget::FormatCurrency(-5000000),
		TEXT("-50,000 cr"));

	TestEqual(TEXT("zero clock"),
		ULBSpacecraftTopBarWidget::FormatSimClock(0.0), TEXT("00:00:00"));
	TestEqual(TEXT("1h 2m 5s"),
		ULBSpacecraftTopBarWidget::FormatSimClock(3725.0), TEXT("01:02:05"));
	TestEqual(TEXT("negative time clamps to zero"),
		ULBSpacecraftTopBarWidget::FormatSimClock(-9.0), TEXT("00:00:00"));
	return true;
}

IMPLEMENT_SIMPLE_AUTOMATION_TEST(FLBSpacecraftHUDSnapshotTest,
	"LineBoss.Spacecraft.HUD.SnapshotMirrorsAuthoritiesHonestly",
	EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)

bool FLBSpacecraftHUDSnapshotTest::RunTest(const FString& Parameters)
{
	(void)Parameters;
	// Null authorities: honest placeholders, never fabricated numbers.
	FLBSpacecraftHUDSnapshot Empty =
		ULBSpacecraftTopBarWidget::BuildSnapshot(nullptr, nullptr, nullptr);
	TestEqual(TEXT("no ledger -> no cash number"),
		Empty.CashText, TEXT("-- cr"));
	TestEqual(TEXT("no factory text"),
		Empty.LineStatusText, TEXT("NO FACTORY"));
	TestEqual(TEXT("no power authority -> honest placeholder"),
		Empty.PowerText, TEXT("PWR --"));
	TestEqual(TEXT("no research authority -> honest placeholder"),
		Empty.ResearchText, TEXT("RSC --"));

	UWorld* World = UWorld::CreateWorld(EWorldType::Game, false,
		FName(TEXT("LBSpacecraftHUDWorld")));
	ALBSpacecraftBuildAuthority* Build =
		World->SpawnActor<ALBSpacecraftBuildAuthority>();

		// EVERY factory is built INSIDE a ship factory (owner
		// 2026-08-28). The hall is the player's first move on the
		// world map, so the fixtures take it too.
		{
			FName SpacecraftTestHallId;
			FString SpacecraftTestHallReason;
			Build->PlaceStarterHall(SpacecraftTestHallId,
				SpacecraftTestHallReason);
		}
	ALBSpacecraftProductionAuthority* Production =
		World->SpawnActor<ALBSpacecraftProductionAuthority>();
	ALBSpacecraftRuntimeCoordinator* Coordinator =
		World->SpawnActor<ALBSpacecraftRuntimeCoordinator>();
	FString Reason;

	// Empty factory: the bar tells the player to build.
	FLBSpacecraftHUDSnapshot Fresh =
		ULBSpacecraftTopBarWidget::BuildSnapshot(Build, Production,
			Coordinator);
	TestEqual(TEXT("fresh factory prompts building"),
		Fresh.LineStatusText, TEXT("BUILD THE LINE"));
	TestEqual(TEXT("fresh cash is the provisional starting capital"),
		Fresh.CashText, TEXT("900,000 cr"));
	TestEqual(TEXT("no contract yet"), Fresh.ContractText,
		TEXT("NO CONTRACT"));

	// Built + contracted + running: live numbers.
	TestTrue(TEXT("line builds"),
		ALBSpacecraftGameMode::SetupCanonicalLine(*Build, Reason));
	TestTrue(TEXT("configured"),
		Coordinator->ConfigureFromAuthorities(Build, Production, Reason));
	TestTrue(TEXT("contract starts"),
		ALBSpacecraftGameMode::StartScoutContract(*Production, 2, Reason));
	for (int32 Tick = 0; Tick < 10; ++Tick)
	{
		TestTrue(TEXT("tick runs"),
			Coordinator->TickProduction(5.0, Reason));
	}
	FLBSpacecraftHUDSnapshot Running =
		ULBSpacecraftTopBarWidget::BuildSnapshot(Build, Production,
			Coordinator);
	TestEqual(TEXT("clock shows 50 sim seconds"),
		Running.ClockText, TEXT("00:00:50"));
	TestTrue(TEXT("contract shows progress 0/2"),
		Running.ContractText.Contains(TEXT("SCOUT-01"))
		&& Running.ContractText.Contains(TEXT("0/2")));
	TestTrue(TEXT("line shows running craft"),
		Running.LineStatusText.Contains(TEXT("LINE RUNNING")));

	// Run to completion: cash and contract flip to the settled state.
	int32 Guard = 0;
	while (Production->GetRevenuePence() < 30000000 && Guard++ < 600)
	{
		TestTrue(TEXT("tick runs"),
			Coordinator->TickProduction(5.0, Reason));
	}
	// Phase-2 readouts mirror the power and research authorities.
	ALBSpacecraftPowerAuthority* Power =
		World->SpawnActor<ALBSpacecraftPowerAuthority>();
	ALBSpacecraftResearchAuthority* Research =
		World->SpawnActor<ALBSpacecraftResearchAuthority>();
	TestTrue(TEXT("plant registers"),
		Power->RegisterSupply(FName(TEXT("Plant.01")), 1000, Reason));
	TestTrue(TEXT("load connects"),
		Power->ConnectLoad(FName(TEXT("Load.Dev")), 400, Reason));
	TestTrue(TEXT("points bank"), Research->AddPoints(25, Reason));
	TestTrue(TEXT("tier 1 unlocks"),
		Research->UnlockNode(FName(TEXT("Research.Mfg.T1")), Reason));
	FLBSpacecraftHUDSnapshot Phase2 =
		ULBSpacecraftTopBarWidget::BuildSnapshot(Build, Production,
			Coordinator, Power, Research);
	// FText number formatting groups digits per locale (en: 1,000).
	TestEqual(TEXT("power reads draw over supply"),
		Phase2.PowerText, // The mains feed rides on supply now (owner 2026-08-26: electricity
		// is bought until generation) - 1,000 own + 800 grid.
		TEXT("PWR 400/1,800 kW"));
	TestEqual(TEXT("research reads points and unlock count"),
		Phase2.ResearchText, TEXT("RSC 15 pts  1/12"));

	FLBSpacecraftHUDSnapshot Done =
		ULBSpacecraftTopBarWidget::BuildSnapshot(Build, Production,
			Coordinator);
	TestEqual(TEXT("cash is capital plus the settled revenue"),
		Done.CashText, TEXT("1,200,000 cr"));
	TestTrue(TEXT("contract reads complete"),
		Done.ContractText.Contains(TEXT("COMPLETE")));
	TestEqual(TEXT("line reads idle"),
		Done.LineStatusText, TEXT("LINE IDLE"));

	World->DestroyWorld(false);
	return true;
}

#endif // WITH_DEV_AUTOMATION_TESTS

IMPLEMENT_SIMPLE_AUTOMATION_TEST(FLBSpacecraftHUDQualityTest,
	"LineBoss.Spacecraft.HUD.WorkmanshipAndCareerAreVisible",
	EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)

bool FLBSpacecraftHUDQualityTest::RunTest(const FString& Parameters)
{
	(void)Parameters;
	using TopBar = ULBSpacecraftTopBarWidget;

	// A clean line says nothing about quality - no news is good news.
	bool bAlarm = true;
	TestTrue(TEXT("a clean craft reports nothing"),
		TopBar::FormatQualityText(0, 0.f, bAlarm).IsEmpty());
	TestFalse(TEXT("and does not alarm"), bAlarm);

	// One blemish is visible but survivable: the player should SEE
	// workmanship coming rather than be startled when it costs money.
	TestEqual(TEXT("one blemish is named"),
		TopBar::FormatQualityText(1, 0.f, bAlarm),
		FString(TEXT("DEFECTS 1")));
	TestFalse(TEXT("one blemish still flies, so no alarm"), bAlarm);

	// A load the hover test will reject alarms.
	TestEqual(TEXT("a failing load is named"),
		TopBar::FormatQualityText(3, 0.f, bAlarm),
		FString(TEXT("DEFECTS 3")));
	TestTrue(TEXT("a craft that will fail its test alarms"), bAlarm);

	// Rework outranks defects - it is the worse news on the floor.
	TestEqual(TEXT("rework wins the line"),
		TopBar::FormatQualityText(4, 90.f, bAlarm),
		FString(TEXT("REWORKING 90s")));
	TestTrue(TEXT("rework always alarms"), bAlarm);
	// Part-seconds round UP: 0.2 s left is still a second of rework,
	// never a silent "REWORKING 0s".
	TestEqual(TEXT("a fraction of a second still reads as one"),
		TopBar::FormatQualityText(0, 0.2f, bAlarm),
		FString(TEXT("REWORKING 1s")));

	// The career ladder must be visible; an absent authority reads as
	// unknown rather than as a fabricated tier zero.
	const FLBSpacecraftHUDSnapshot Empty =
		TopBar::BuildSnapshot(nullptr, nullptr, nullptr);
	TestEqual(TEXT("no reputation reads as unknown"),
		Empty.ReputationText, FString(TEXT("REP --")));

	UWorld* World = UWorld::CreateWorld(EWorldType::Game, false,
		FName(TEXT("LBSpacecraftHUDQualityWorld")));
	ALBSpacecraftReputationAuthority* Reputation =
		World->SpawnActor<ALBSpacecraftReputationAuthority>();
	const FLBSpacecraftHUDSnapshot WithRep =
		TopBar::BuildSnapshot(nullptr, nullptr, nullptr, nullptr, nullptr,
			Reputation);
	TestTrue(TEXT("the tier and points are both on the bar"),
		WithRep.ReputationText.Contains(TEXT("T1"))
		&& WithRep.ReputationText.Contains(TEXT("pts")));

	World->DestroyWorld(false);
	return true;
}
