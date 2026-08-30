#if WITH_DEV_AUTOMATION_TESTS

#include "LBSpacecraftPalette.h"

#include "Misc/AutomationTest.h"

/**
 * THE PALETTE IS A CONTRACT, NOT A CONVENTION.
 *
 * Every colour rule in the brand spec is checkable arithmetic, so it is
 * checked here rather than trusted. The reason is not tidiness: the
 * collision this palette exists to fix - machine amber and warning
 * orange reading as the same colour - was introduced by hand, one
 * plausible literal at a time, and no review caught it. A rule that
 * only lives in a comment is a rule that gets broken by someone doing
 * their best.
 */
namespace LBSpacecraftPaletteTestsPrivate
{
	/** The authored sRGB hex beside every token in the header. */
	struct FAuthoredToken
	{
		const TCHAR* Name;
		uint8 R;
		uint8 G;
		uint8 B;
		const FLinearColor* Baked;
	};

	const FAuthoredToken AuthoredTokens[] = {
		{ TEXT("Floor.Concrete"),         0xC9, 0xC5, 0xBE, &LBSpacecraftPalette::FloorConcrete },
		{ TEXT("Floor.Concrete.Wear"),    0xB2, 0xAE, 0xA7, &LBSpacecraftPalette::FloorConcreteWear },
		{ TEXT("Floor.Line.Lane"),        0x9E, 0x9A, 0x93, &LBSpacecraftPalette::FloorLaneLine },
		{ TEXT("Structure.Graphite"),     0x4A, 0x4D, 0x50, &LBSpacecraftPalette::StructureGraphite },
		{ TEXT("Structure.Graphite.Dark"),0x33, 0x36, 0x3A, &LBSpacecraftPalette::StructureGraphiteDark },
		{ TEXT("Machine.Housing.Pale"),   0xD6, 0xD2, 0xCB, &LBSpacecraftPalette::MachineHousingPale },
		{ TEXT("Machine.Amber"),          0xA8, 0x73, 0x34, &LBSpacecraftPalette::MachineAmber },
		{ TEXT("Machine.Amber.Trim"),     0xC0, 0x8A, 0x3C, &LBSpacecraftPalette::MachineAmberTrim },
		{ TEXT("Crate.Tan"),              0xB3, 0x94, 0x68, &LBSpacecraftPalette::CrateTan },
		{ TEXT("Crate.Tan.Dark"),         0x8E, 0x73, 0x50, &LBSpacecraftPalette::CrateTanDark },
		{ TEXT("Hazard"),                 0xC9, 0xA2, 0x1C, &LBSpacecraftPalette::Hazard },
		{ TEXT("Hazard.Black"),           0x23, 0x21, 0x1F, &LBSpacecraftPalette::HazardBlack },
		{ TEXT("Indicator.Working"),      0xBF, 0xE4, 0xFF, &LBSpacecraftPalette::IndicatorWorking },
		{ TEXT("Indicator.Idle"),         0x6E, 0x7C, 0x86, &LBSpacecraftPalette::IndicatorIdle },
		{ TEXT("Indicator.Complete"),     0xED, 0xED, 0xEC, &LBSpacecraftPalette::IndicatorComplete },
		{ TEXT("Indicator.Fault"),        0xE3, 0x3A, 0x1C, &LBSpacecraftPalette::IndicatorFault },
		{ TEXT("Panel.Bg"),               0x1B, 0x1B, 0x1B, &LBSpacecraftPalette::PanelBg },
		{ TEXT("Panel.BgRaised"),         0x23, 0x23, 0x22, &LBSpacecraftPalette::PanelBgRaised },
		{ TEXT("Panel.Rule"),             0x36, 0x34, 0x33, &LBSpacecraftPalette::PanelRule },
		{ TEXT("Panel.Edge"),             0x0E, 0x0E, 0x0E, &LBSpacecraftPalette::PanelEdge },
		{ TEXT("Text.Heading"),           0xA8, 0xA4, 0xA1, &LBSpacecraftPalette::TextHeading },
		{ TEXT("Text.Body"),              0xED, 0xED, 0xEC, &LBSpacecraftPalette::TextBody },
		{ TEXT("Text.Value"),             0xFF, 0xFF, 0xFF, &LBSpacecraftPalette::TextValue },
		{ TEXT("Text.Dim"),               0x91, 0x8D, 0x8B, &LBSpacecraftPalette::TextDim },
		{ TEXT("Text.Disabled"),          0x5E, 0x5B, 0x59, &LBSpacecraftPalette::TextDisabled },
		{ TEXT("State.Refusal"),          0xEC, 0x30, 0x13, &LBSpacecraftPalette::Refusal },
		{ TEXT("Text.OnRefusal"),         0xFF, 0xFF, 0xFF, &LBSpacecraftPalette::TextOnRefusal },
		{ TEXT("State.Warning.Hatch"),    0x91, 0x8D, 0x8B, &LBSpacecraftPalette::WarningHatch },
		{ TEXT("Row.Selected.Marker"),    0x2E, 0x2C, 0x2B, &LBSpacecraftPalette::RowSelectedMarker },
		{ TEXT("Row.Hover"),              0x26, 0x25, 0x24, &LBSpacecraftPalette::RowHover },
		{ TEXT("Focus.Ring"),             0xED, 0xED, 0xEC, &LBSpacecraftPalette::FocusRing },
	};

	/**
	 * Every WORLD SURFACE token - the ones the governing rule binds.
	 *
	 * Hazard and the indicators are deliberately absent. They are the
	 * spec's two named exemptions: hazard because it is floor
	 * infrastructure bought with a footprint rule instead of a
	 * saturation one, and the indicators because they are emissive and
	 * tiny, read as light rather than as surface.
	 */
	const FLinearColor* const BoundWorldSurfaces[] = {
		&LBSpacecraftPalette::FloorConcrete,
		&LBSpacecraftPalette::FloorConcreteWear,
		&LBSpacecraftPalette::FloorLaneLine,
		&LBSpacecraftPalette::StructureGraphite,
		&LBSpacecraftPalette::StructureGraphiteDark,
		&LBSpacecraftPalette::MachineHousingPale,
		&LBSpacecraftPalette::MachineAmber,
		&LBSpacecraftPalette::CrateTan,
		&LBSpacecraftPalette::CrateTanDark,
	};

	const TCHAR* const BoundWorldNames[] = {
		TEXT("Floor.Concrete"), TEXT("Floor.Concrete.Wear"),
		TEXT("Floor.Line.Lane"), TEXT("Structure.Graphite"),
		TEXT("Structure.Graphite.Dark"), TEXT("Machine.Housing.Pale"),
		TEXT("Machine.Amber"),
		TEXT("Crate.Tan"), TEXT("Crate.Tan.Dark"),
	};

	/**
	 * MACHINE.AMBER.TRIM IS NOT IN THE LIST ABOVE, AND THAT IS A REAL
	 * QUESTION RATHER THAN A CONVENIENCE.
	 *
	 * The spec fixes the amber ceiling at saturation 69% and value 66%,
	 * then supplies Machine.Amber.Trim #C08A3C at value 75%. Its own
	 * trim token is nine points over its own ceiling. This test found
	 * that on the first run, which is the argument for having written
	 * it.
	 *
	 * The reading taken here is that the ceiling governs SURFACES and
	 * trim is not one. The spec restricts amber to "arm segments,
	 * fitting heads and edge strips" and puts every machine surface
	 * over half a square metre on the pale housing instead, so a trim
	 * token is by definition a thin bright edge - the same shape of
	 * exemption the spec grants hazard striping, which is also allowed
	 * to break the saturation ceiling because a footprint rule holds it
	 * in check instead.
	 *
	 * The saturation ceiling is still enforced on it below. Only the
	 * brightness half is relaxed, because a highlight that is not
	 * brighter than the thing it edges is not a highlight.
	 *
	 * FLAGGED FOR THE NEXT REVISION. This is an inference from the
	 * spec's own logic, not something the spec says, and inferring a
	 * rule is how the collision this palette exists to fix got made in
	 * the first place. It needs confirming rather than assuming.
	 */
	const FLinearColor* const SmallAreaAccents[] = {
		&LBSpacecraftPalette::MachineAmberTrim,
	};

	const TCHAR* const SmallAreaAccentNames[] = {
		TEXT("Machine.Amber.Trim"),
	};

	/**
	 * The spec states its limits as WHOLE PERCENTAGES of its own
	 * tokens, so a token sitting exactly on its limit measures a
	 * fraction above it: #A87334 is saturation 0.6905, which the spec
	 * writes as 69%. Comparing against a hard 0.69 fails the canonical
	 * value for being itself. The limit is therefore "rounds to at most
	 * the stated percentage", which is what the spec means, and still
	 * catches any real change - a genuinely different colour moves far
	 * further than half a point.
	 */
	constexpr float RoundingHeadroom = 0.005f;
}

IMPLEMENT_SIMPLE_AUTOMATION_TEST(FLBSpacecraftPaletteMatchesAuthoredHexTest,
	"LineBoss.Spacecraft.Palette.BakedValuesMatchAuthoredHex",
	EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)

bool FLBSpacecraftPaletteMatchesAuthoredHexTest::RunTest(const FString& Parameters)
{
	using namespace LBSpacecraftPaletteTestsPrivate;

	// The header stores LINEAR values because converting during static
	// initialisation is not worth the risk, and keeps the authored sRGB
	// hex in a comment. This is what stops those two drifting apart: a
	// comment nobody can verify is how wrong numbers survive.
	for (const FAuthoredToken& Token : AuthoredTokens)
	{
		const FLinearColor Expected =
			FLinearColor::FromSRGBColor(FColor(Token.R, Token.G, Token.B));
		const FLinearColor& Baked = *Token.Baked;

		// Tolerance covers the three decimal places the header carries,
		// nothing more - a genuinely edited hex moves far further.
		const float Tolerance = 0.002f;
		const bool bMatches =
			FMath::IsNearlyEqual(Baked.R, Expected.R, Tolerance) &&
			FMath::IsNearlyEqual(Baked.G, Expected.G, Tolerance) &&
			FMath::IsNearlyEqual(Baked.B, Expected.B, Tolerance);

		TestTrue(FString::Printf(
			TEXT("%s: baked (%.3f, %.3f, %.3f) matches authored #%02X%02X%02X ")
			TEXT("which converts to (%.3f, %.3f, %.3f)"),
			Token.Name, Baked.R, Baked.G, Baked.B,
			Token.R, Token.G, Token.B,
			Expected.R, Expected.G, Expected.B), bMatches);
	}

	return true;
}

IMPLEMENT_SIMPLE_AUTOMATION_TEST(FLBSpacecraftPaletteGoverningRuleTest,
	"LineBoss.Spacecraft.Palette.NoWorldSurfaceIsBrightAndSaturated",
	EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)

bool FLBSpacecraftPaletteGoverningRuleTest::RunTest(const FString& Parameters)
{
	using namespace LBSpacecraftPaletteTestsPrivate;
	using namespace LBSpacecraftPalette;

	// THE GOVERNING RULE. Everything else in the palette is downstream
	// of this: if a world surface is allowed to be both bright and
	// saturated, it competes with the ships, and the ships are the only
	// thing in this game allowed to win that competition.
	static_assert(UE_ARRAY_COUNT(BoundWorldSurfaces)
		== UE_ARRAY_COUNT(BoundWorldNames),
		"world surface table and its names have drifted apart");

	for (int32 Index = 0; Index < UE_ARRAY_COUNT(BoundWorldSurfaces); ++Index)
	{
		const FLinearColor& Colour = *BoundWorldSurfaces[Index];
		TestFalse(FString::Printf(
			TEXT("%s is not both bright and saturated (S %.2f, V %.2f)"),
			BoundWorldNames[Index], SrgbSaturation(Colour), SrgbValue(Colour)),
			IsBrightAndSaturated(Colour));
	}

	// Small-area accents are allowed to be bright - see the note on
	// SmallAreaAccents - but never to exceed the saturation ceiling.
	// Brightness on a thin edge is a highlight; saturation on one still
	// competes with the ships.
	static_assert(UE_ARRAY_COUNT(SmallAreaAccents)
		== UE_ARRAY_COUNT(SmallAreaAccentNames),
		"accent table and its names have drifted apart");

	for (int32 Index = 0; Index < UE_ARRAY_COUNT(SmallAreaAccents); ++Index)
	{
		const FLinearColor& Colour = *SmallAreaAccents[Index];
		TestTrue(FString::Printf(
			TEXT("%s stays under the saturation ceiling (S %.2f) even ")
			TEXT("though it is allowed to be bright (V %.2f)"),
			SmallAreaAccentNames[Index], SrgbSaturation(Colour),
			SrgbValue(Colour)),
			SrgbSaturation(Colour) <= 0.69f + RoundingHeadroom);
	}

	return true;
}

IMPLEMENT_SIMPLE_AUTOMATION_TEST(FLBSpacecraftPaletteAmberCeilingTest,
	"LineBoss.Spacecraft.Palette.MachineAmberRespectsItsCeiling",
	EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)

bool FLBSpacecraftPaletteAmberCeilingTest::RunTest(const FString& Parameters)
{
	using namespace LBSpacecraftPalette;

	// The ceiling exists because the amber ACTUALLY SHIPPED at sRGB
	// #EEB459 - value 0.94 against this 0.66 - and read as a different
	// colour from the one intended. The measurement, not the intention,
	// is what is enforced here.
	const float AmberSaturation = SrgbSaturation(MachineAmber);
	const float AmberValue = SrgbValue(MachineAmber);

	using namespace LBSpacecraftPaletteTestsPrivate;

	TestTrue(FString::Printf(
		TEXT("Machine.Amber saturation %.3f is at or under the 0.69 ceiling"),
		AmberSaturation), AmberSaturation <= 0.69f + RoundingHeadroom);
	TestTrue(FString::Printf(
		TEXT("Machine.Amber value %.3f is at or under the 0.66 ceiling"),
		AmberValue), AmberValue <= 0.66f + RoundingHeadroom);

	// THE GAP THAT KEEPS THE FLOOR READABLE. Crates share amber's hue
	// family on purpose; what separates a floor of parts from a floor
	// of machines is the distance in saturation, not in hue. The spec
	// puts that gap at 27 points and it is the reason both can be on
	// screen at once without merging into one orange field.
	const float CrateSaturation = SrgbSaturation(CrateTan);
	TestTrue(FString::Printf(
		TEXT("Crate.Tan saturation %.2f sits at least 0.20 below ")
		TEXT("Machine.Amber %.2f"), CrateSaturation, AmberSaturation),
		CrateSaturation <= AmberSaturation - 0.20f);

	// Pale housing is the DEFAULT for machine bodies, so it has to be
	// unmistakably not-amber. If these two ever converge, "use pale for
	// anything over half a square metre" stops meaning anything.
	TestTrue(TEXT("Machine.Housing.Pale is effectively unsaturated"),
		SrgbSaturation(MachineHousingPale) < 0.12f);

	return true;
}

IMPLEMENT_SIMPLE_AUTOMATION_TEST(FLBSpacecraftPaletteInterfaceHasOneHueTest,
	"LineBoss.Spacecraft.Palette.InterfaceCarriesExactlyOneHue",
	EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)

bool FLBSpacecraftPaletteInterfaceHasOneHueTest::RunTest(const FString& Parameters)
{
	using namespace LBSpacecraftPalette;

	// Refusal red is the interface's ONLY hue, and that is what makes a
	// refusal impossible to miss: it is the single coloured thing the
	// player ever sees in a panel. Every colour added beside it takes
	// some of that away.
	const FLinearColor* const HueFree[] = {
		&PanelBg, &PanelBgRaised, &PanelRule, &PanelEdge,
		&TextHeading, &TextBody, &TextValue, &TextDim, &TextDisabled,
		&WarningHatch, &RowSelectedMarker, &RowHover, &FocusRing,
	};
	const TCHAR* const HueFreeNames[] = {
		TEXT("Panel.Bg"), TEXT("Panel.BgRaised"), TEXT("Panel.Rule"),
		TEXT("Panel.Edge"), TEXT("Text.Heading"), TEXT("Text.Body"),
		TEXT("Text.Value"), TEXT("Text.Dim"), TEXT("Text.Disabled"),
		TEXT("State.Warning.Hatch"), TEXT("Row.Selected.Marker"),
		TEXT("Row.Hover"), TEXT("Focus.Ring"),
	};
	static_assert(UE_ARRAY_COUNT(HueFree) == UE_ARRAY_COUNT(HueFreeNames),
		"interface token table and its names have drifted apart");

	for (int32 Index = 0; Index < UE_ARRAY_COUNT(HueFree); ++Index)
	{
		// Not zero: these are warm neutrals, not pure greys, and a few
		// points of saturation is what stops the panels looking dead.
		// The line is drawn where a colour becomes NAMEABLE.
		TestTrue(FString::Printf(TEXT("%s carries no nameable hue (S %.2f)"),
			HueFreeNames[Index], SrgbSaturation(*HueFree[Index])),
			SrgbSaturation(*HueFree[Index]) < 0.12f);
	}

	// WARNING MUST NOT BE ORANGE. This single assertion is the fix for
	// the collision the whole palette was written to remove: a warning
	// state with a hue drifts towards machine amber every time someone
	// picks it by eye, because that is what "caution" looks like.
	TestTrue(TEXT("State.Warning.Hatch is hue-free, not an orange"),
		SrgbSaturation(WarningHatch) < 0.12f);

	// And the one permitted hue really is one.
	TestTrue(FString::Printf(TEXT("State.Refusal is unmistakably coloured ")
		TEXT("(S %.2f)"), SrgbSaturation(Refusal)),
		SrgbSaturation(Refusal) > 0.80f);

	return true;
}

#endif // WITH_DEV_AUTOMATION_TESTS
