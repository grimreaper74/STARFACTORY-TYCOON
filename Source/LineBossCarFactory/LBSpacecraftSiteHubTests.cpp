// Copyright Epic Games, Inc. All Rights Reserved.

#include "Misc/AutomationTest.h"

#if WITH_DEV_AUTOMATION_TESTS

#include "LBSpacecraftSiteHubWidget.h"

/**
 * THE HUB'S CLICKABLE PLACES ARE DATA MEASURED OFF A PICTURE, so every
 * way they can be wrong is a way a human has to notice by eye - and the
 * ones below were all missed by eye at least once.
 */
IMPLEMENT_SIMPLE_AUTOMATION_TEST(FLBSpacecraftHubPlacesAreReachableTest,
	"LineBoss.Spacecraft.SiteHub.EveryPlaceIsReachableAndUnambiguous",
	EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)

bool FLBSpacecraftHubPlacesAreReachableTest::RunTest(const FString& Parameters)
{
	(void)Parameters;
	const TArray<FLBSpacecraftHubPlace>& Places =
		ULBSpacecraftSiteHubWidget::Places();
	TestEqual(TEXT("the site has twelve places"), Places.Num(), 12);

	// THE BUILD PANEL COVERS THE LEFT EDGE. A place drawn entirely
	// behind it cannot be clicked at all, and that is invisible in the
	// artwork - it only appears once the game is running with its
	// interface over the picture. The research lab was drawn fully
	// behind the panel in one revision of the site and nothing but a
	// screenshot said so.
	constexpr float PanelRight = 0.22f;
	// The objectives box sits in the top-right corner.
	constexpr float ObjectivesLeft = 0.855f;
	constexpr float ObjectivesBottom = 0.20f;

	TSet<FName> Seen;
	for (const FLBSpacecraftHubPlace& Place : Places)
	{
		const FString Id = Place.PlaceId.ToString();
		TestFalse(*FString::Printf(TEXT("%s is named once"), *Id),
			Seen.Contains(Place.PlaceId));
		Seen.Add(Place.PlaceId);

		TestTrue(*FString::Printf(TEXT("%s has a real rectangle"), *Id),
			Place.Max.X > Place.Min.X && Place.Max.Y > Place.Min.Y);
		TestTrue(*FString::Printf(TEXT("%s is inside the picture"), *Id),
			Place.Min.X >= 0.f && Place.Min.Y >= 0.f
			&& Place.Max.X <= 1.f && Place.Max.Y <= 1.f);

		TestTrue(*FString::Printf(
			TEXT("%s is not entirely behind the build panel"), *Id),
			Place.Max.X > PanelRight);
		const bool bUnderObjectives = Place.Min.X > ObjectivesLeft
			&& Place.Max.Y < ObjectivesBottom;
		TestFalse(*FString::Printf(
			TEXT("%s is not entirely behind the objectives box"), *Id),
			bUnderObjectives);

		// A place must be clickable at its own centre. Overlapping
		// rectangles are allowed - buildings are drawn in front of one
		// another - but a place whose CENTRE resolves to a different
		// place is one the player can never reach.
		const FVector2D Centre = (Place.Min + Place.Max) * 0.5f;
		TestEqual(*FString::Printf(
			TEXT("%s answers a click at its own centre"), *Id),
			ULBSpacecraftSiteHubWidget::PlaceAt(Centre), Place.PlaceId);
	}

	// Nothing outside the site answers.
	TestTrue(TEXT("empty ground answers nothing"),
		ULBSpacecraftSiteHubWidget::PlaceAt(
			FVector2D(0.5f, 0.995f)).IsNone());
	return true;
}

#endif // WITH_DEV_AUTOMATION_TESTS
