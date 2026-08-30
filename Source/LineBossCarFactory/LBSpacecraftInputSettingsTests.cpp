// Spacecraft input map + player-preference contracts: the Car
// Manufacture-adopted scheme's table invariants, ensure/reset/rebind
// against a scratch UInputSettings, preference clamps, cycle helpers,
// sim-speed vocabulary and the pawn's pure camera seams.

#if WITH_DEV_AUTOMATION_TESTS

#include "GameFramework/InputSettings.h"
#include "LBGameUserSettings.h"
#include "LBSpacecraftGameMode.h"
#include "LBSpacecraftInputMap.h"
#include "LBSpacecraftPlayerPawn.h"
#include "LBSpacecraftSettingsWidget.h"
#include "LBSpacecraftDifficulty.h"
#include "LBSpacecraftProductionTypes.h"

#include "Misc/AutomationTest.h"

#include <limits>

IMPLEMENT_SIMPLE_AUTOMATION_TEST(FLBSpacecraftInputMapContractTest,
	"LineBoss.Spacecraft.Settings.InputMapContract",
	EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)

bool FLBSpacecraftInputMapContractTest::RunTest(const FString& Parameters)
{
	(void)Parameters;
	const TArray<FLBSpacecraftInputRow>& Rows =
		FLBSpacecraftInputMap::GetRows();
	TestTrue(TEXT("the scheme is substantial"), Rows.Num() >= 20);

	TSet<FName> RowIds;
	TSet<FString> DefaultChords;
	for (const FLBSpacecraftInputRow& Row : Rows)
	{
		TestFalse(TEXT("row ids are unique"), RowIds.Contains(Row.RowId));
		RowIds.Add(Row.RowId);
		TestTrue(TEXT("every row has a display name"),
			!Row.DisplayName.IsEmpty());
		TestTrue(TEXT("every default key is valid"),
			Row.DefaultKey.IsValid());
		TestTrue(TEXT("mapping names carry the spacecraft prefix"),
			Row.MappingName.ToString().StartsWith(TEXT("LB_SC_")));
		// A (key, shift) chord may serve exactly one row - the whole
		// point of adopting one coherent scheme.
		const FString Chord = FString::Printf(TEXT("%s|%d"),
			*Row.DefaultKey.ToString(), Row.bDefaultShift ? 1 : 0);
		TestFalse(FString::Printf(
			TEXT("default %s serves only one row"), *Chord),
			DefaultChords.Contains(Chord));
		DefaultChords.Add(Chord);
		if (Row.Kind == ELBSpacecraftInputRowKind::AxisKey)
		{
			TestTrue(TEXT("axis rows declare a signed scale"),
				!FMath::IsNearlyZero(Row.AxisScale));
		}
	}
	// The extras (ghost rotation's R and F) must not shadow any row's
	// primary default.
	for (const FLBSpacecraftInputRow& Row : Rows)
	{
		for (const FKey& Extra :
			{ Row.ExtraDefaultKey1, Row.ExtraDefaultKey2 })
		{
			if (!Extra.IsValid())
			{
				continue;
			}
			const FString Chord = FString::Printf(TEXT("%s|0"),
				*Extra.ToString());
			TestFalse(FString::Printf(
				TEXT("extra %s shadows no primary"), *Chord),
				DefaultChords.Contains(Chord));
		}
	}

	// The fixed anchors of the scheme stay locked.
	for (const TCHAR* Locked : { TEXT("Confirm"), TEXT("Menu"),
		TEXT("ZoomWheel") })
	{
		const FLBSpacecraftInputRow* Row =
			FLBSpacecraftInputMap::FindRow(FName(Locked));
		TestNotNull(TEXT("locked row exists"), Row);
		if (Row != nullptr)
		{
			TestFalse(TEXT("locked row refuses rebinding"),
				Row->bRebindable);
		}
	}

	// The Car Manufacture adoption itself: the recovered defaults.
	struct FExpectedDefault
	{
		const TCHAR* RowId;
		FKey Key;
	};
	const FExpectedDefault Expected[] = {
		{ TEXT("PanForward"), EKeys::W }, { TEXT("PanBack"), EKeys::S },
		{ TEXT("PanLeft"), EKeys::A }, { TEXT("PanRight"), EKeys::D },
		{ TEXT("RotateLeft"), EKeys::Q }, { TEXT("RotateRight"), EKeys::E },
		{ TEXT("ZoomIn"), EKeys::V }, { TEXT("ZoomOut"), EKeys::C },
		{ TEXT("RotateGhost"), EKeys::X },
		{ TEXT("RotateGhostBack"), EKeys::Z },
		{ TEXT("PauseSim"), EKeys::One },
		{ TEXT("SpeedNormal"), EKeys::Two },
		{ TEXT("SpeedFast"), EKeys::Three },
		{ TEXT("SpeedFastest"), EKeys::Four },
		{ TEXT("PanelNext"), EKeys::Tab },
		{ TEXT("QuickSave"), EKeys::F5 },
		{ TEXT("Cancel"), EKeys::RightMouseButton },
		{ TEXT("Confirm"), EKeys::LeftMouseButton },
		{ TEXT("Menu"), EKeys::Escape } };
	for (const FExpectedDefault& Case : Expected)
	{
		const FLBSpacecraftInputRow* Row =
			FLBSpacecraftInputMap::FindRow(FName(Case.RowId));
		TestNotNull(Case.RowId, Row);
		if (Row != nullptr)
		{
			TestEqual(Case.RowId, Row->DefaultKey, Case.Key);
		}
	}
	return true;
}


IMPLEMENT_SIMPLE_AUTOMATION_TEST(FLBSpacecraftInputRebindTest,
	"LineBoss.Spacecraft.Settings.EnsureRebindAndResetFailClosed",
	EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)

bool FLBSpacecraftInputRebindTest::RunTest(const FString& Parameters)
{
	(void)Parameters;
	// A scratch instance copies the config-loaded defaults; strip two
	// mappings to prove Ensure backfills exactly what is missing.
	UInputSettings* Settings = NewObject<UInputSettings>();
	TestNotNull(TEXT("scratch input settings"), Settings);
	if (Settings == nullptr)
	{
		return false;
	}
	const FLBSpacecraftInputRow* RotateGhost =
		FLBSpacecraftInputMap::FindRow(FName(TEXT("RotateGhost")));
	const FLBSpacecraftInputRow* PanForward =
		FLBSpacecraftInputMap::FindRow(FName(TEXT("PanForward")));
	TestNotNull(TEXT("rotate row"), RotateGhost);
	TestNotNull(TEXT("pan row"), PanForward);
	if (RotateGhost == nullptr || PanForward == nullptr)
	{
		return false;
	}

	// Strip the ghost-rotate action entirely (a stale Saved/Input.ini
	// predating the action) - Ensure must restore the default trio.
	TArray<FInputActionKeyMapping> Mappings;
	Settings->GetActionMappingByName(RotateGhost->MappingName, Mappings);
	for (const FInputActionKeyMapping& Mapping : Mappings)
	{
		Settings->RemoveActionMapping(Mapping, false);
	}
	bool bShift = false;
	TestFalse(TEXT("stripped row reads unbound"),
		FLBSpacecraftInputMap::GetPrimaryKey(*Settings, *RotateGhost,
			bShift).IsValid());
	TestTrue(TEXT("ensure backfills the stripped mapping"),
		FLBSpacecraftInputMap::EnsureSpacecraftBindings(*Settings) > 0);
	TestEqual(TEXT("the default returns"),
		FLBSpacecraftInputMap::GetPrimaryKey(*Settings, *RotateGhost,
			bShift), RotateGhost->DefaultKey);
	TestEqual(TEXT("ensure is idempotent"),
		FLBSpacecraftInputMap::EnsureSpacecraftBindings(*Settings), 0);

	// Fail-closed rebinds: collisions and locked anchors refuse, named.
	FString Reason;
	TestTrue(TEXT("a free key rebinds"),
		FLBSpacecraftInputMap::RebindRow(*Settings,
			RotateGhost->RowId, EKeys::B, Reason));
	TestEqual(TEXT("the rebind took"),
		FLBSpacecraftInputMap::GetPrimaryKey(*Settings, *RotateGhost,
			bShift), EKeys::B);
	TestFalse(TEXT("a taken key refuses"),
		FLBSpacecraftInputMap::RebindRow(*Settings,
			PanForward->RowId, EKeys::B, Reason));
	TestTrue(TEXT("the refusal names the holder"),
		Reason.Contains(TEXT("ALREADY USED BY RotateGhost")));
	TestFalse(TEXT("the locked menu row refuses"),
		FLBSpacecraftInputMap::RebindRow(*Settings,
			FName(TEXT("Menu")), EKeys::P, Reason));
	TestFalse(TEXT("escape refuses as a target"),
		FLBSpacecraftInputMap::RebindRow(*Settings,
			RotateGhost->RowId, EKeys::Escape, Reason));
	TestFalse(TEXT("a gamepad key refuses as a target"),
		FLBSpacecraftInputMap::RebindRow(*Settings,
			RotateGhost->RowId, EKeys::Gamepad_FaceButton_Bottom, Reason));
	TestFalse(TEXT("an unknown row refuses"),
		FLBSpacecraftInputMap::RebindRow(*Settings,
			FName(TEXT("NoSuchRow")), EKeys::B, Reason));

	// Reset restores the adopted defaults including the R/F extras.
	FLBSpacecraftInputMap::ResetSpacecraftBindings(*Settings);
	TestEqual(TEXT("reset restores the CM default"),
		FLBSpacecraftInputMap::GetPrimaryKey(*Settings, *RotateGhost,
			bShift), RotateGhost->DefaultKey);
	Settings->GetActionMappingByName(RotateGhost->MappingName, Mappings);
	bool bHasR = false;
	bool bHasF = false;
	for (const FInputActionKeyMapping& Mapping : Mappings)
	{
		bHasR |= Mapping.Key == EKeys::R;
		bHasF |= Mapping.Key == EKeys::F;
	}
	TestTrue(TEXT("reset restores the R extra"), bHasR);
	TestTrue(TEXT("reset restores the F extra"), bHasF);
	return true;
}


IMPLEMENT_SIMPLE_AUTOMATION_TEST(FLBSpacecraftPreferenceClampTest,
	"LineBoss.Spacecraft.Settings.PreferenceClampsAndDefaults",
	EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)

bool FLBSpacecraftPreferenceClampTest::RunTest(const FString& Parameters)
{
	(void)Parameters;
	ULBGameUserSettings* Settings = NewObject<ULBGameUserSettings>();
	TestNotNull(TEXT("settings authority"), Settings);
	if (Settings == nullptr)
	{
		return false;
	}
	Settings->SetToDefaults();
	TestEqual(TEXT("volume defaults full"),
		Settings->GetMasterVolume(), 1.f);
	TestFalse(TEXT("edge scroll defaults OFF (the genre reference ships without it)"),
		Settings->IsEdgeScrollEnabled());
	TestFalse(TEXT("zoom defaults uninverted"), Settings->IsZoomInverted());
	TestEqual(TEXT("pan scale defaults 1"),
		Settings->GetCameraPanSpeedScale(), 1.f);

	Settings->SetMasterVolume(1.7f);
	TestEqual(TEXT("volume clamps high"), Settings->GetMasterVolume(), 1.f);
	Settings->SetMasterVolume(-0.4f);
	TestEqual(TEXT("volume clamps low"), Settings->GetMasterVolume(), 0.f);
	Settings->SetCameraPanSpeedScale(9.f);
	TestEqual(TEXT("pan scale clamps high"),
		Settings->GetCameraPanSpeedScale(),
		ULBGameUserSettings::MaxCameraSpeedScale);
	Settings->SetCameraZoomSpeedScale(0.01f);
	TestEqual(TEXT("zoom scale clamps low"),
		Settings->GetCameraZoomSpeedScale(),
		ULBGameUserSettings::MinCameraSpeedScale);
	TestEqual(TEXT("NaN volume falls back to full"),
		ULBGameUserSettings::ClampMasterVolume01(
			std::numeric_limits<float>::quiet_NaN()), 1.f);

	// Cycle helpers wrap and tolerate off-list values.
	const TArray<float>& Caps =
		ULBSpacecraftSettingsWidget::GetFrameCapOptions();
	TestEqual(TEXT("frame caps start uncapped"), Caps[0], 0.f);
	TestEqual(TEXT("cycle advances"),
		ULBSpacecraftSettingsWidget::NextOption(Caps, 0.f), 30.f);
	TestEqual(TEXT("cycle wraps"),
		ULBSpacecraftSettingsWidget::NextOption(Caps, 240.f), 0.f);
	TestEqual(TEXT("off-list values restart the cycle"),
		ULBSpacecraftSettingsWidget::NextOption(Caps, 37.f), 0.f);

	// The factory speed vocabulary is exactly four steps.
	TestTrue(TEXT("0 is a speed"),
		ALBSpacecraftGameMode::IsKnownSimSpeed(0.f));
	TestTrue(TEXT("1 is a speed"),
		ALBSpacecraftGameMode::IsKnownSimSpeed(1.f));
	TestTrue(TEXT("2 is a speed"),
		ALBSpacecraftGameMode::IsKnownSimSpeed(2.f));
	TestTrue(TEXT("4 is a speed"),
		ALBSpacecraftGameMode::IsKnownSimSpeed(4.f));
	TestFalse(TEXT("3 is the KEY, not the scale"),
		ALBSpacecraftGameMode::IsKnownSimSpeed(3.f));
	return true;
}


IMPLEMENT_SIMPLE_AUTOMATION_TEST(FLBSpacecraftSiteMapFramingTest,
	"LineBoss.Spacecraft.Settings.SiteMapFramingContract",
	EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)

bool FLBSpacecraftSiteMapFramingTest::RunTest(const FString& Parameters)
{
	(void)Parameters;
	// The site map (owner 2026-08-27: "it's just a map and you click on
	// building to enter"). Framing is a pure function so it can be held
	// to a contract without a viewport: bigger things frame from
	// further out, the answer is always a legal zoom, and margins mean
	// what they say.
	using Pawn = ALBSpacecraftPlayerPawn;
	const float MinZoom = 2500.f;
	const float MaxZoom = 16000.f;

	const float Hall = Pawn::ComputeFramingZoomCm(
		FVector2D(3000.f, 2200.f), 2.6f, MinZoom, MaxZoom);
	const float Silo = Pawn::ComputeFramingZoomCm(
		FVector2D(1000.f, 600.f), 2.6f, MinZoom, MaxZoom);
	TestTrue(TEXT("a bigger building frames from further out"),
		Hall > Silo);
	TestTrue(TEXT("framing is always a legal zoom"),
		Hall >= MinZoom && Hall <= MaxZoom
			&& Silo >= MinZoom && Silo <= MaxZoom);

	// The whole site frames wider than any one building in it.
	const float Site = Pawn::ComputeFramingZoomCm(
		FVector2D(9000.f, 12000.f), 1.5f, MinZoom, MaxZoom);
	TestTrue(TEXT("the site frames wider than a building"), Site > Hall);
	TestEqual(TEXT("a vast site clamps to the zoom ceiling"),
		Pawn::ComputeFramingZoomCm(FVector2D(90000.f, 90000.f), 1.5f,
			MinZoom, MaxZoom), MaxZoom);
	TestEqual(TEXT("a degenerate footprint clamps to the floor"),
		Pawn::ComputeFramingZoomCm(FVector2D(0.f, 0.f), 2.6f,
			MinZoom, MaxZoom), MinZoom);
	// More margin means further out, footprint held equal.
	TestTrue(TEXT("margin buys distance"),
		Pawn::ComputeFramingZoomCm(FVector2D(3000.f, 2200.f), 3.5f,
			MinZoom, MaxZoom) > Hall);

	// And the key exists: M is the site map, in the camera family,
	// rebindable like everything else.
	bool bFound = false;
	for (const FLBSpacecraftInputRow& Row :
		FLBSpacecraftInputMap::GetRows())
	{
		if (Row.RowId == FName(TEXT("SiteMap")))
		{
			bFound = true;
			TestEqual(TEXT("the site map rides M"),
				Row.DefaultKey, EKeys::M);
			TestEqual(TEXT("in the camera family"),
				Row.Category, ELBSpacecraftInputCategory::Camera);
		}
	}
	TestTrue(TEXT("the site map action exists"), bFound);
	return true;
}

IMPLEMENT_SIMPLE_AUTOMATION_TEST(FLBSpacecraftEdgeScrollSeamTest,
	"LineBoss.Spacecraft.Settings.EdgeScrollAndFramingSeams",
	EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)

bool FLBSpacecraftEdgeScrollSeamTest::RunTest(const FString& Parameters)
{
	(void)Parameters;
	const FVector2D Viewport(1920.f, 1080.f);
	const float Margin = 12.f;
	TestEqual(TEXT("centre scrolls nothing"),
		ALBSpacecraftPlayerPawn::ComputeEdgeScrollDirection(
			FVector2D(960.f, 540.f), Viewport, Margin),
		FIntPoint::ZeroValue);
	TestEqual(TEXT("left edge scrolls left"),
		ALBSpacecraftPlayerPawn::ComputeEdgeScrollDirection(
			FVector2D(4.f, 540.f), Viewport, Margin), FIntPoint(-1, 0));
	TestEqual(TEXT("bottom-right corner scrolls diagonally"),
		ALBSpacecraftPlayerPawn::ComputeEdgeScrollDirection(
			FVector2D(1918.f, 1078.f), Viewport, Margin), FIntPoint(1, 1));
	TestEqual(TEXT("top edge scrolls up"),
		ALBSpacecraftPlayerPawn::ComputeEdgeScrollDirection(
			FVector2D(960.f, 2.f), Viewport, Margin), FIntPoint(0, -1));
	TestEqual(TEXT("an off-viewport cursor never creeps (windowed play)"),
		ALBSpacecraftPlayerPawn::ComputeEdgeScrollDirection(
			FVector2D(-50.f, 540.f), Viewport, Margin),
		FIntPoint::ZeroValue);
	TestEqual(TEXT("a degenerate viewport scrolls nothing"),
		ALBSpacecraftPlayerPawn::ComputeEdgeScrollDirection(
			FVector2D(5.f, 5.f), FVector2D(20.f, 20.f), Margin),
		FIntPoint::ZeroValue);

	// The boot framing contract stays inside the zoom clamps.
	TestTrue(TEXT("boot zoom is a sane arm length"),
		ALBSpacecraftPlayerPawn::GetBootFramingZoomCm() >= 2500.f
		&& ALBSpacecraftPlayerPawn::GetBootFramingZoomCm() <= 16000.f);
	return true;
}

#endif // WITH_DEV_AUTOMATION_TESTS

IMPLEMENT_SIMPLE_AUTOMATION_TEST(FLBSpacecraftDifficultyTest,
	"LineBoss.Spacecraft.Settings.DifficultyChangesTheGameNotJustALabel",
	EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)

bool FLBSpacecraftDifficultyTest::RunTest(const FString& Parameters)
{
	(void)Parameters;
	using Difficulty = FLBSpacecraftDifficulty;
	using Settings = ULBSpacecraftSettingsWidget;
	const ELBSpacecraftDifficulty Restore = Difficulty::GetCurrent();

	// Unreal has no difficulty of its own, so every dial here is ours.
	const FLBSpacecraftDifficultyRules Easy =
		Difficulty::RulesFor(ELBSpacecraftDifficulty::Relaxed);
	const FLBSpacecraftDifficultyRules Norm =
		Difficulty::RulesFor(ELBSpacecraftDifficulty::Standard);
	const FLBSpacecraftDifficultyRules Hard =
		Difficulty::RulesFor(ELBSpacecraftDifficulty::Demanding);

	// STANDARD is the game as tuned, not a modifier applied to it.
	TestEqual(TEXT("standard leaves the deadline alone"),
		Norm.DeadlineScale, 1.f);
	TestEqual(TEXT("standard leaves the price alone"),
		Norm.ContractPriceScale, 1.f);
	TestEqual(TEXT("standard leaves the penalty alone"),
		Norm.LatePenaltyScale, 1.f);

	// Every dial moves the right way, together.
	TestTrue(TEXT("relaxed starts you richer"),
		Easy.StartingCapitalPence > Norm.StartingCapitalPence);
	TestTrue(TEXT("demanding starts you poorer"),
		Hard.StartingCapitalPence < Norm.StartingCapitalPence);
	TestTrue(TEXT("relaxed gives you longer"),
		Easy.DeadlineScale > Hard.DeadlineScale);
	TestTrue(TEXT("relaxed forgives more workmanship"),
		Easy.HoverTestDefectTolerance > Hard.HoverTestDefectTolerance);
	TestEqual(TEXT("demanding passes only clean work"),
		Hard.HoverTestDefectTolerance, 0);
	TestTrue(TEXT("demanding punishes lateness harder"),
		Hard.LatePenaltyScale > Easy.LatePenaltyScale);
	TestTrue(TEXT("and pays less for the work"),
		Hard.ContractPriceScale < Easy.ContractPriceScale);

	// The hover test really judges at the chosen tolerance - this is
	// the dial the player feels most.
	TestTrue(TEXT("a blemished craft flies on relaxed"),
		FLBSpacecraftProductionCatalog::DefectsPassHoverTestAt(2,
			Easy.HoverTestDefectTolerance));
	TestFalse(TEXT("the same craft is rejected on demanding"),
		FLBSpacecraftProductionCatalog::DefectsPassHoverTestAt(2,
			Hard.HoverTestDefectTolerance));
	TestTrue(TEXT("a clean craft always flies"),
		FLBSpacecraftProductionCatalog::DefectsPassHoverTestAt(0,
			Hard.HoverTestDefectTolerance));

	// The settings row cycles through every difficulty and wraps.
	TSet<ELBSpacecraftDifficulty> Seen;
	ELBSpacecraftDifficulty Walk = ELBSpacecraftDifficulty::Relaxed;
	for (int32 Step = 0; Step < Difficulty::All().Num(); ++Step)
	{
		Seen.Add(Walk);
		Walk = Settings::NextDifficultyAfter(Walk);
	}
	TestEqual(TEXT("cycling reaches every difficulty"),
		Seen.Num(), Difficulty::All().Num());
	TestEqual(TEXT("and wraps back to where it started"),
		Walk, ELBSpacecraftDifficulty::Relaxed);

	// Each one is nameable, for the row label.
	for (ELBSpacecraftDifficulty Option : Difficulty::All())
	{
		TestFalse(TEXT("every difficulty has a name"),
			Difficulty::DisplayName(Option).IsEmpty());
	}

	// Setting it takes hold at once.
	Difficulty::SetCurrent(ELBSpacecraftDifficulty::Demanding);
	TestEqual(TEXT("the chosen rules are the ones in force"),
		Difficulty::Current().HoverTestDefectTolerance, 0);
	Difficulty::SetCurrent(Restore);
	return true;
}
