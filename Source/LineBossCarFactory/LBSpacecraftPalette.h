#pragma once

#include "CoreMinimal.h"

/**
 * THE PALETTE - one place where every colour in the game is decided.
 *
 * Adopted from the Star Factory Tycoon brand implementation spec
 * (2026-08-29). Before this header the presenter carried SIXTY-FOUR
 * ad-hoc FLinearColor literals with no shared vocabulary, which is how
 * two of them - machine amber and warning orange - ended up close
 * enough to be mistaken for each other on screen.
 *
 * THE GOVERNING RULE, and the reason everything here is restrained:
 *
 *     No world surface may be both BRIGHT and SATURATED, and only one
 *     of the interface and the machinery is allowed to carry a hue at
 *     all.
 *
 * The point of that restraint is a single promise: COLOUR BELONGS TO
 * THE SHIPS. A craft wears its customer's livery, and it can only be
 * the most colourful thing on screen if nothing else competes. The
 * factory is deliberately the quiet backdrop that makes it read.
 *
 * The spec states the check as arithmetic rather than taste:
 *
 *     At whole-bay zoom, non-ship pixels above 60% saturation stay
 *     under 8% of the frame, and the single most saturated pixel in
 *     frame always belongs to a hull.
 *
 * Tools/chroma_acceptance_v001.py runs exactly that on a screenshot.
 * When a frame fails it, the spec is explicit about which way to fix
 * it: LOWER THE MACHINERY, NEVER RAISE THE LIVERY.
 *
 * WHY THE VALUES ARE BAKED RATHER THAN CONVERTED HERE. Every token is
 * authored as an sRGB hex - that is the language the spec, the design
 * tool and every colour picker speak - but a material vector parameter
 * is LINEAR, so the two differ by the sRGB transfer curve. Converting
 * at startup would mean running FLinearColor::FromSRGBColor during
 * static initialisation, whose ordering against the engine's own
 * tables is not worth betting a launch on. So the linear value is
 * baked and the authored hex kept beside it in the comment.
 *
 * That trade would normally risk the two drifting apart silently.
 * They cannot: LBSpacecraftPaletteTests re-derives every token from
 * its hex at test time and fails if a baked constant no longer
 * matches. The comment is therefore load-bearing, not decoration -
 * edit the hex and the test tells you the number underneath is stale.
 */
namespace LBSpacecraftPalette
{
	// ---------------------------------------------------------------
	// THE WORLD
	// ---------------------------------------------------------------

	/** Poured interior slab. The floor a building brings with it. */
	inline constexpr FLinearColor FloorConcrete        (0.584f, 0.558f, 0.515f); // #C9C5BE
	/** Traffic wear, spills, the tracked-in grime of a working floor. */
	inline constexpr FLinearColor FloorConcreteWear    (0.445f, 0.423f, 0.386f); // #B2AEA7
	/** Painted lane edges. Reads as paint, never as light. */
	inline constexpr FLinearColor FloorLaneLine        (0.342f, 0.323f, 0.292f); // #9E9A93

	/** Structure: columns, gantry legs, rails, roof trusses. */
	inline constexpr FLinearColor StructureGraphite    (0.068f, 0.074f, 0.080f); // #4A4D50
	inline constexpr FLinearColor StructureGraphiteDark(0.033f, 0.037f, 0.042f); // #33363A

	/**
	 * THE DEFAULT FOR MACHINERY, and the token most likely to be
	 * reached for wrongly. The spec is blunt about it: every machine
	 * surface over half a square metre is THIS, not amber. Amber is
	 * for arm segments, fitting heads and edge strips - the small,
	 * moving, look-here parts. A machine with an amber body is wrong
	 * however good it looks alone, because a floor of them becomes one
	 * orange mass from above and the ships stop reading.
	 */
	inline constexpr FLinearColor MachineHousingPale   (0.672f, 0.644f, 0.597f); // #D6D2CB

	/**
	 * Machine accent. HARD CEILING: saturation 69%, value 66% in sRGB.
	 * The ceiling is the whole point - it is what keeps amber from
	 * colliding with warning states and with the ships.
	 */
	inline constexpr FLinearColor MachineAmber         (0.392f, 0.171f, 0.034f); // #A87334
	inline constexpr FLinearColor MachineAmberTrim     (0.527f, 0.254f, 0.045f); // #C08A3C

	/**
	 * Crates and dollies. Deliberately the SAME HUE FAMILY as amber but
	 * 27 saturation points below it. That gap is not a style choice -
	 * it is what stops a floor of parts and a floor of machines
	 * merging into a single orange field when seen from the height the
	 * game is actually played at.
	 */
	inline constexpr FLinearColor CrateTan             (0.451f, 0.296f, 0.138f); // #B39468
	inline constexpr FLinearColor CrateTanDark         (0.270f, 0.171f, 0.080f); // #8E7350

	/**
	 * Hazard striping. EXEMPT from the saturation ceiling, and the only
	 * world token that is - bought with a strict footprint rule
	 * instead: floor infrastructure only, always paired with the black,
	 * at a fixed 200 mm world pitch so it never changes density with
	 * the size of the thing it edges. Never on machine bodies, robot
	 * arms, crates, hulls, the interface, icons or the wordmark.
	 */
	inline constexpr FLinearColor Hazard               (0.584f, 0.361f, 0.012f); // #C9A21C
	inline constexpr FLinearColor HazardBlack          (0.017f, 0.015f, 0.014f); // #23211F

	/**
	 * Status lights. These are EMISSIVE - exempt from the ceiling
	 * because they read as light rather than as surface, and because
	 * they are small. Treat them as such: an indicator the size of a
	 * machine panel is no longer an indicator.
	 */
	inline constexpr FLinearColor IndicatorWorking     (0.521f, 0.776f, 1.000f); // #BFE4FF
	inline constexpr FLinearColor IndicatorIdle        (0.156f, 0.202f, 0.238f); // #6E7C86
	inline constexpr FLinearColor IndicatorComplete    (0.847f, 0.847f, 0.839f); // #EDEDEC
	inline constexpr FLinearColor IndicatorFault       (0.768f, 0.042f, 0.012f); // #E33A1C

	// ---------------------------------------------------------------
	// THE SITE - 600 x 600 m, and the first thing the player sees
	// ---------------------------------------------------------------
	//
	// The world tokens above are INTERIOR tokens. Outside had no spec
	// at all and was running on a hardstand tone invented by hand,
	// which is why the opening screen read as a sand flat.

	/**
	 * Graded hardstand inside the claimed plot. Deliberately the same
	 * hue as the interior slab and only three points below it in value,
	 * so inside and outside read as one material family rather than as
	 * two different games.
	 */
	inline constexpr FLinearColor GroundPrepared     (0.539f, 0.509f, 0.456f); // #C2BDB4

	/**
	 * Native ground beyond the built area. The 15-point value drop from
	 * prepared ground IS the plot boundary seen from altitude - it is
	 * what lets the claimed rectangle read without a fence around it.
	 */
	inline constexpr FLinearColor LandUnclaimed      (0.332f, 0.301f, 0.235f); // #9C9585

	/** Roads and delivery aprons. Told apart from ground by KERBS, not tone. */
	inline constexpr FLinearColor RoadApron          (0.468f, 0.445f, 0.407f); // #B6B2AB

	/** Runway and chicane: a shade darker so the strip reads as one band. */
	inline constexpr FLinearColor RunwaySurface      (0.418f, 0.397f, 0.366f); // #ADA9A3

	/**
	 * Centreline, thresholds, chicane gates, pad ring. The brightest
	 * non-emissive surface in the game: THE RUNWAY IS LEGIBLE BY VALUE,
	 * NEVER BY HUE. The 23-point gap against the surface is the whole
	 * mechanism - under about 20 the strip disappears at site zoom.
	 */
	inline constexpr FLinearColor RunwayMarking      (0.807f, 0.784f, 0.738f); // #E8E5DF
	/** Scuffing in the touchdown and chicane zones. Never on the centreline. */
	inline constexpr FLinearColor RunwayMarkingWorn  (0.624f, 0.591f, 0.539f); // #CFCAC2

	/**
	 * Hover pad deck - graphite family, so the pad reads as engineered
	 * equipment rather than as ground, and gives a bright hull the
	 * darkest backdrop on the site to depart against.
	 */
	inline constexpr FLinearColor PadSurface         (0.076f, 0.082f, 0.089f); // #4E5154

	/**
	 * Kerbs, plot edging, drainage channels, survey stakes. This is the
	 * line-work that makes empty ground read as PREPARED rather than as
	 * an unfinished level - the difference between a business on its
	 * first day and a level that was never built.
	 */
	inline constexpr FLinearColor SiteKerb           (0.270f, 0.254f, 0.231f); // #8E8A84

	/** Cool sky fill against warm ground bounce - the pair is what keeps
	 *  a pale hull separable from pale ground. */
	inline constexpr FLinearColor SkyAmbient         (0.723f, 0.768f, 0.807f); // #DDE3E8

	// ---------------------------------------------------------------
	// HULLS - the only things allowed to carry real colour
	// ---------------------------------------------------------------

	/**
	 * Unpainted structure, the first half of the line. COOL AND MID,
	 * not pale, and both properties are load-bearing: it separates from
	 * Machine.Housing.Pale by 25 points of value AND by temperature
	 * (206 degrees against 38). Machinery is warm and light; product is
	 * cool and mid. A warm or bright bare hull reads as a machine
	 * housing, and then the player cannot tell how far along any of
	 * four hulls on the line actually is.
	 */
	inline constexpr FLinearColor HullBare           (0.262f, 0.283f, 0.305f); // #8C9196
	inline constexpr FLinearColor HullBareDark       (0.144f, 0.159f, 0.175f); // #6A6F74

	/**
	 * Livery markings - hue-free by rule, chosen by the base colour's
	 * value: V >= 85 takes the dark, V < 85 takes the light. Geometry
	 * only. NO numerals, letters or logos, ever - the game ships
	 * translated and baked text cannot localise.
	 */
	inline constexpr FLinearColor HullMarkingLight   (0.839f, 0.823f, 0.791f); // #ECEAE6
	inline constexpr FLinearColor HullMarkingDark    (0.017f, 0.015f, 0.014f); // #23211F

	// ---------------------------------------------------------------
	// THE INTERFACE - hue-free, with exactly one exception
	// ---------------------------------------------------------------
	//
	// Nothing in this block carries a hue except Refusal. That is what
	// guarantees a panel and a machine can never land on the same
	// colour: only one of them is allowed to have one. It is also why
	// the WARNING state has no colour at all - a hue-free hatch or
	// dashed border instead. Warning orange is what collided with
	// machine amber in the first place, and removing the hue removes
	// the collision at its source rather than negotiating around it.

	inline constexpr FLinearColor PanelBg              (0.011f, 0.011f, 0.011f); // #1B1B1B
	inline constexpr FLinearColor PanelBgRaised        (0.017f, 0.017f, 0.016f); // #232322
	inline constexpr FLinearColor PanelRule            (0.037f, 0.034f, 0.033f); // #363433
	inline constexpr FLinearColor PanelEdge            (0.004f, 0.004f, 0.004f); // #0E0E0E

	inline constexpr FLinearColor TextHeading          (0.392f, 0.371f, 0.356f); // #A8A4A1
	inline constexpr FLinearColor TextBody             (0.847f, 0.847f, 0.839f); // #EDEDEC
	/** NUMERALS ONLY. Pure white is reserved so figures read first. */
	inline constexpr FLinearColor TextValue            (1.000f, 1.000f, 1.000f); // #FFFFFF
	inline constexpr FLinearColor TextDim              (0.283f, 0.266f, 0.258f); // #918D8B
	inline constexpr FLinearColor TextDisabled         (0.112f, 0.105f, 0.100f); // #5E5B59

	/** The ONLY hue in the interface. Reserved for refusal. */
	inline constexpr FLinearColor Refusal              (0.839f, 0.030f, 0.007f); // #EC3013
	inline constexpr FLinearColor TextOnRefusal        (1.000f, 1.000f, 1.000f); // #FFFFFF
	/** Warning carries NO hue - this is a hatch tone, not a colour. */
	inline constexpr FLinearColor WarningHatch         (0.283f, 0.266f, 0.258f); // #918D8B

	inline constexpr FLinearColor RowSelectedMarker    (0.027f, 0.025f, 0.024f); // #2E2C2B
	inline constexpr FLinearColor RowHover             (0.019f, 0.019f, 0.018f); // #262524
	inline constexpr FLinearColor FocusRing            (0.847f, 0.847f, 0.839f); // #EDEDEC

	// ---------------------------------------------------------------
	// MEASUREMENT
	// ---------------------------------------------------------------
	//
	// The spec's limits are stated in the HSV of the AUTHORED sRGB
	// value, not of the linear one, so anything checking a rule has to
	// convert back before it measures. Getting that backwards makes
	// every dark surface look far more saturated than the eye finds it,
	// and the ceiling stops meaning anything.

	/** Linear -> sRGB, the standard transfer curve. */
	inline float ToSrgbChannel(float Linear)
	{
		Linear = FMath::Clamp(Linear, 0.f, 1.f);
		return Linear <= 0.0031308f
			? Linear * 12.92f
			: 1.055f * FMath::Pow(Linear, 1.f / 2.4f) - 0.055f;
	}

	/** HSV saturation of a token, measured where the spec states it. */
	inline float SrgbSaturation(const FLinearColor& Colour)
	{
		const float R = ToSrgbChannel(Colour.R);
		const float G = ToSrgbChannel(Colour.G);
		const float B = ToSrgbChannel(Colour.B);
		const float Hi = FMath::Max3(R, G, B);
		const float Lo = FMath::Min3(R, G, B);
		return Hi <= 0.f ? 0.f : (Hi - Lo) / Hi;
	}

	/** HSV value of a token, measured where the spec states it. */
	inline float SrgbValue(const FLinearColor& Colour)
	{
		return FMath::Max3(ToSrgbChannel(Colour.R),
			ToSrgbChannel(Colour.G), ToSrgbChannel(Colour.B));
	}

	/** The governing rule, as a predicate. */
	inline bool IsBrightAndSaturated(const FLinearColor& Colour)
	{
		return SrgbValue(Colour) > 0.70f && SrgbSaturation(Colour) > 0.50f;
	}
}
