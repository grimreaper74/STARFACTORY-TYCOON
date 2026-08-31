#if WITH_DEV_AUTOMATION_TESTS

#include "LBSpacecraftGameMode.h"
#include "LBSpacecraftWIPPresentationActor.h"
#include "LBSpacecraftSaveGame.h"
#include "LBSpacecraftTrackAuthority.h"
#include "LBSpacecraftTransportAuthority.h"
#include "LBSpacecraftProgressionAuthority.h"

#include "Engine/World.h"
#include "Kismet/GameplayStatics.h"
#include "Misc/AutomationTest.h"

namespace LBSpacecraftVisualCountPrivate
{
	/** Stations that get a MACHINE VISUAL: everything except the site
	 *  buildings, which the shell layer draws (owner 2026-08-28).
	 *  Qualified by file (2026-08-30): an identical helper of the same
	 *  name exists in LBSpacecraftGameModeTests.cpp's copy of this same
	 *  namespace - harmless across separate translation units, but
	 *  unity build can merge both into one, where a second definition
	 *  of the same name is a hard redefinition error regardless of the
	 *  bodies matching. */
	inline int32 SpacecraftMachineStationCountPhase2(
		const ALBSpacecraftBuildAuthority& InBuild)
	{
		int32 Count = 0;
		for (const FLBSpacecraftStationRecord& Record :
			InBuild.GetStations())
		{
			const FLBSpacecraftStationDefinition* Definition =
				ALBSpacecraftBuildAuthority::FindDefinition(
					Record.DefinitionId);
			if (Definition != nullptr && !Definition->bSiteBuilding)
			{
				++Count;
			}
		}
		return Count;
	}
}

namespace LBSpacecraftPhase2IntegrationTestsPrivate
{
	struct FLBSpacecraftPhase2Rig
	{
		UWorld* World = nullptr;
		ALBSpacecraftBuildAuthority* Build = nullptr;
		ALBSpacecraftProductionAuthority* Production = nullptr;
		ALBSpacecraftRuntimeCoordinator* Coordinator = nullptr;
		ALBSpacecraftInventoryAuthority* Inventory = nullptr;
		ALBSpacecraftCraftingAuthority* Crafting = nullptr;
		ALBSpacecraftPowerAuthority* Power = nullptr;
		ALBSpacecraftResearchAuthority* Research = nullptr;
		ALBSpacecraftDroneFleetAuthority* DroneFleet = nullptr;
		ALBSpacecraftReputationAuthority* Reputation = nullptr;
		ALBSpacecraftTransportAuthority* Transport = nullptr;
		ALBSpacecraftProgressionAuthority* Progression = nullptr;
		ALBSpacecraftTrackAuthority* Track = nullptr;

		FLBSpacecraftSaveContext Context() const
		{
			FLBSpacecraftSaveContext Out;
			Out.Build = Build;
			Out.Production = Production;
			Out.Coordinator = Coordinator;
			Out.Inventory = Inventory;
			Out.Crafting = Crafting;
			Out.Power = Power;
			Out.Research = Research;
			Out.DroneFleet = DroneFleet;
			Out.Reputation = Reputation;
			Out.Transport = Transport;
			Out.Progression = Progression;
			Out.Track = Track;
			return Out;
		}
	};

	FLBSpacecraftPhase2Rig MakeSpacecraftPhase2Rig()
	{
		FLBSpacecraftPhase2Rig Rig;
		Rig.World = UWorld::CreateWorld(EWorldType::Game, false,
			FName(TEXT("LBSpacecraftPhase2World")));
		Rig.Build = Rig.World->SpawnActor<ALBSpacecraftBuildAuthority>();

		// EVERY factory is built INSIDE a ship factory (owner
		// 2026-08-28). The hall is the player's first move on the
		// world map, so the fixtures take it too.
		{
			FName SpacecraftTestHallId;
			FString SpacecraftTestHallReason;
			Rig.Build->PlaceStarterHall(SpacecraftTestHallId,
				SpacecraftTestHallReason);
		}
		Rig.Production =
			Rig.World->SpawnActor<ALBSpacecraftProductionAuthority>();
		Rig.Coordinator =
			Rig.World->SpawnActor<ALBSpacecraftRuntimeCoordinator>();
		Rig.Inventory =
			Rig.World->SpawnActor<ALBSpacecraftInventoryAuthority>();
		Rig.Crafting =
			Rig.World->SpawnActor<ALBSpacecraftCraftingAuthority>();
		Rig.Power = Rig.World->SpawnActor<ALBSpacecraftPowerAuthority>();
		Rig.Research =
			Rig.World->SpawnActor<ALBSpacecraftResearchAuthority>();
		Rig.DroneFleet =
			Rig.World->SpawnActor<ALBSpacecraftDroneFleetAuthority>();
		Rig.Reputation =
			Rig.World->SpawnActor<ALBSpacecraftReputationAuthority>();
		Rig.Transport =
			Rig.World->SpawnActor<ALBSpacecraftTransportAuthority>();
		Rig.Progression =
			Rig.World->SpawnActor<ALBSpacecraftProgressionAuthority>();
		Rig.Track =
			Rig.World->SpawnActor<ALBSpacecraftTrackAuthority>();
		// Mirror the game mode's research gate on the build authority.
		ALBSpacecraftResearchAuthority* Research = Rig.Research;
		Rig.Build->SetPlacementGate(
			[Research](FName DefinitionId, FString& GateReason)
		{
			if (!Research->IsStationClassUnlocked(DefinitionId))
			{
				GateReason = FString::Printf(
					TEXT("%s IS LOCKED - RESEARCH IT FIRST"),
					*DefinitionId.ToString());
				return false;
			}
			return true;
		});
		return Rig;
	}

	/** THE SPRAY BOOTH a line cannot commission without (owner
	 *  2026-08-28), placed then commissioned in one call.
	 *
	 *  Every rig in this file builds its line by hand at its own
	 *  coordinates, so the booth hunts for a legal spot downstream
	 *  rather than assuming one: the overlap gate and the owned-land
	 *  gate are the authorities on where it may stand, and a fixture
	 *  that guessed would fail somewhere unrelated to what it tests. */
	bool EnsureSprayBoothAndCommission(FLBSpacecraftPhase2Rig& Rig,
		FString& OutReason)
	{
		bool bHasBooth = false;
		for (const FLBSpacecraftStationRecord& Record :
			Rig.Build->GetStations())
		{
			const FLBSpacecraftStationDefinition* Definition =
				ALBSpacecraftBuildAuthority::FindDefinition(
					Record.DefinitionId);
			bHasBooth = bHasBooth
				|| (Definition != nullptr && Definition->bProcessStation);
		}
		if (!bHasBooth)
		{
			for (float Y = 6000.f; Y <= 8400.f && !bHasBooth; Y += 1200.f)
			{
				for (float X = 0.f; X <= 4000.f && !bHasBooth; X += 2000.f)
				{
					FName BoothId;
					FString BoothReason;
					bHasBooth = Rig.Build->PlaceStation(
						FName(TEXT("SprayBooth")),
						FTransform(FRotator::ZeroRotator,
							FVector(X, Y, 0.f)), BoothId, BoothReason);
					// CREWED, like the fitting stations these rigs
					// crew: an empty booth sprays badly and drags the
					// craft's quality, which would colour every
					// revenue assertion in this file with a defect
					// these tests are not about.
					for (int32 Crew = 0; bHasBooth && Crew < 2; ++Crew)
					{
						FString CrewReason;
						Rig.Build->InstallStationDrone(BoothId,
							CrewReason, FName(TEXT("Spray")));
					}
				}
			}
		}
		return Rig.Build->CommissionFactory(OutReason);
	}
}

IMPLEMENT_SIMPLE_AUTOMATION_TEST(FLBSpacecraftTrimLoopTest,
	"LineBoss.Spacecraft.Production.TrimLoop",
	EAutomationTestFlags::EditorContext
		| EAutomationTestFlags::EngineFilter)

bool FLBSpacecraftTrimLoopTest::RunTest(const FString& Parameters)
{
	(void)Parameters;
	using Catalog = FLBSpacecraftProductionCatalog;

	// THE BALANCE GUARANTEE, and the reason this test exists. The trim
	// loop changes how long the pad is occupied, never who passes. If
	// this ever fails, a difficulty tier has silently moved and the
	// loop has stopped being a presentation change.
	for (int32 Tolerance = 0; Tolerance <= 4; ++Tolerance)
	{
		for (int32 Defects = 0; Defects <= 12; ++Defects)
		{
			const bool bOldGate =
				Catalog::DefectsPassHoverTestAt(Defects, Tolerance);
			const bool bConverges =
				Catalog::TrimPassesRequired(Defects, Tolerance)
					!= INDEX_NONE;
			TestEqual(FString::Printf(
				TEXT("tolerance %d, %d defects: the loop agrees with the ")
				TEXT("old one-shot gate"), Tolerance, Defects),
				bConverges, bOldGate);
		}
	}

	// A CLEAN CRAFT SETTLES FIRST TIME. This is the common case and the
	// one the player sees most, so a regression here is a regression in
	// the game's signature moment.
	TestEqual(TEXT("a clean craft needs exactly one pass"),
		Catalog::TrimPassesRequired(0, 1), 1);
	TestEqual(TEXT("and shows no residual at all"),
		Catalog::TrimResidualDeg(0, 0), 0.f);

	// Each defect inside tolerance costs one more run-measure-adjust.
	TestEqual(TEXT("one defect costs a second pass"),
		Catalog::TrimPassesRequired(1, 1), 2);
	TestEqual(TEXT("three defects on a relaxed tier cost four"),
		Catalog::TrimPassesRequired(3, 3), 4);

	// Beyond tolerance it never settles, and says so with INDEX_NONE
	// rather than a large number - "will not converge" and "takes ages"
	// are different states and the gate routes them differently.
	TestEqual(TEXT("beyond tolerance it will not settle"),
		Catalog::TrimPassesRequired(2, 1), INDEX_NONE);

	// THE RESIDUAL DECAYS, strictly, pass over pass - that is what makes
	// it converge rather than wander. Stepped forward in time only.
	{
		float Previous = Catalog::TrimResidualDeg(3, 0);
		TestTrue(TEXT("a defective craft starts out of trim"),
			Previous > 0.f);
		for (int32 Pass = 1; Pass <= 6; ++Pass)
		{
			const float Now = Catalog::TrimResidualDeg(3, Pass);
			TestTrue(TEXT("each pass takes trim out, never adds it"),
				Now < Previous);
			TestTrue(TEXT("and the residual never goes negative"),
				Now >= 0.f);
			Previous = Now;
		}
	}

	// More defects is always worse at the same point in the session -
	// otherwise a dirtier craft could read as better trimmed.
	for (int32 Pass = 0; Pass <= 3; ++Pass)
	{
		TestTrue(TEXT("more defects always reads further out of trim"),
			Catalog::TrimResidualDeg(4, Pass)
				> Catalog::TrimResidualDeg(2, Pass));
	}

	// Nonsense input must not produce nonsense state. These are
	// reachable: DefectPoints is an int32 on a SaveGame struct and a
	// restored save is not trusted until validated.
	TestEqual(TEXT("negative defects are treated as none"),
		Catalog::TrimResidualDeg(-5, 0), 0.f);
	TestTrue(TEXT("a negative pass index does not explode"),
		Catalog::TrimResidualDeg(2, -3) > 0.f);

	return true;
}

IMPLEMENT_SIMPLE_AUTOMATION_TEST(FLBSpacecraftFactoryEnvelopeTest,
	"LineBoss.Spacecraft.Production.FactoryEnvelope",
	EAutomationTestFlags::EditorContext
		| EAutomationTestFlags::EngineFilter)

bool FLBSpacecraftFactoryEnvelopeTest::RunTest(const FString& Parameters)
{
	(void)Parameters;
	using Catalog = FLBSpacecraftProductionCatalog;
	const FVector Envelope = Catalog::FactoryMaxCraftEnvelopeCm();

	// THE POINT OF THE WHOLE FEATURE (owner: "the tracks for gantry
	// crane needs to be big enough for the biggest ship the factory
	// will make"). The span is checked against the DECLARED envelope,
	// not against the largest recipe that happens to ship today -
	// checking it against Cargo would pass while missing the point
	// entirely, which is the mistake this exists to prevent.
	const float Span = Catalog::GantryRailSpanCm();
	TestTrue(TEXT("the gantry spans the widest craft the factory allows"),
		Span > Envelope.Y);
	TestTrue(TEXT("with real working room either side, not a squeeze"),
		Span - Envelope.Y >= 600.f);

	// The envelope must clear the BIGGEST craft this build ships, with
	// room to spare - not merely the Scout, which is the smallest of the
	// ladder and the thing it is easiest to accidentally size against.
	// Checked against the catalogue rather than a literal, so adding a
	// bigger recipe moves the test with it.
	float WidestShipped = 0.f;
	for (const FLBSpacecraftRecipe& Recipe : Catalog::CanonicalRecipes())
	{
		WidestShipped = FMath::Max(WidestShipped, Recipe.CraftEnvelopeCm.Y);
	}
	TestTrue(TEXT("the envelope clears the widest craft that ships"),
		Envelope.Y > WidestShipped);
	TestTrue(TEXT("and is not merely sized to the smallest craft"),
		Envelope.Y > 746.f * 1.5f);

	// Every shipped recipe must fit the factory it is built in.
	for (const FLBSpacecraftRecipe& Recipe : Catalog::CanonicalRecipes())
	{
		FString Error;
		TestTrue(FString::Printf(TEXT("%s fits the factory envelope"),
			*Recipe.RecipeId.ToString()),
			Catalog::ValidateCraftFitsFactory(Recipe, Error));
	}

	// AND A CRAFT THAT DOES NOT FIT IS REFUSED, with a reason that says
	// a bigger station will not save it - because it will not.
	{
		FLBSpacecraftRecipe TooBig = Catalog::CanonicalRecipes()[0];
		TooBig.CraftEnvelopeCm = FVector(Envelope.X + 1.f, Envelope.Y,
			Envelope.Z);
		FString Error;
		TestFalse(TEXT("a craft longer than the factory is refused"),
			Catalog::ValidateCraftFitsFactory(TooBig, Error));
		TestTrue(TEXT("and the refusal says no station mark can help"),
			Error.Contains(TEXT("NO STATION MARK CAN HELP")));

		// Width and height are checked too - only length was tested
		// above, and an envelope check that only guards one axis is the
		// kind of half-check that passes review and ships.
		FLBSpacecraftRecipe TooWide = Catalog::CanonicalRecipes()[0];
		TooWide.CraftEnvelopeCm = FVector(Envelope.X, Envelope.Y + 1.f,
			Envelope.Z);
		TestFalse(TEXT("a craft wider than the factory is refused"),
			Catalog::ValidateCraftFitsFactory(TooWide, Error));

		FLBSpacecraftRecipe TooTall = Catalog::CanonicalRecipes()[0];
		TooTall.CraftEnvelopeCm = FVector(Envelope.X, Envelope.Y,
			Envelope.Z + 1.f);
		TestFalse(TEXT("a craft taller than the factory is refused"),
			Catalog::ValidateCraftFitsFactory(TooTall, Error));
	}

	// The full recipe validator must carry the check, or a future tier
	// could be added straight to the catalogue and never meet it.
	{
		FLBSpacecraftRecipe TooBig = Catalog::CanonicalRecipes()[0];
		TooBig.CraftEnvelopeCm = FVector(Envelope.X * 2.f, Envelope.Y,
			Envelope.Z);
		FString Error;
		TestFalse(TEXT("ValidateRecipe rejects an oversized craft too"),
			Catalog::ValidateRecipe(TooBig, Error));
	}
	return true;
}

IMPLEMENT_SIMPLE_AUTOMATION_TEST(FLBSpacecraftAccessGraphTest,
	"LineBoss.Spacecraft.Production.AccessGraph",
	EAutomationTestFlags::EditorContext
		| EAutomationTestFlags::EngineFilter)

bool FLBSpacecraftAccessGraphTest::RunTest(const FString& Parameters)
{
	(void)Parameters;
	// The fixing order is a physical fact, not a preference: once the
	// cabin trim is on you cannot reach the harness behind it. The edges
	// write that down, and the whole point of writing it down is that a
	// future reorder into something impossible FAILS rather than ships.
	const TArray<FLBSpacecraftRecipe>& Recipes =
		FLBSpacecraftProductionCatalog::CanonicalRecipes();
	TestTrue(TEXT("there is at least one recipe to check"),
		Recipes.Num() > 0);

	for (const FLBSpacecraftRecipe& Recipe : Recipes)
	{
		FString Error;
		TestTrue(FString::Printf(TEXT("%s ships a valid fixing order"),
			*Recipe.RecipeId.ToString()),
			FLBSpacecraftProductionCatalog::ValidateFixingOrder(
				Recipe, Error));

		// Every declared edge must genuinely be satisfied by the order as
		// shipped. The edges DESCRIBE the sequence, so if the two ever
		// disagree then one of them is wrong and both are suspect.
		for (const FLBSpacecraftAccessEdge& Block : Recipe.AccessBlocks)
		{
			const int32 BlockerAt =
				Recipe.FixingOrder.IndexOfByKey(Block.Blocker);
			const int32 BlockedAt =
				Recipe.FixingOrder.IndexOfByKey(Block.Blocked);
			TestTrue(TEXT("a blocked component is fitted before its blocker"),
				BlockedAt != INDEX_NONE && BlockerAt != INDEX_NONE
					&& BlockedAt < BlockerAt);
		}
	}

	// An IMPOSSIBLE order must be refused. Built by reversing a real
	// recipe rather than hand-written, so the case cannot drift away
	// from the shipped data.
	{
		FLBSpacecraftRecipe Broken = Recipes[0];
		TArray<ELBSpacecraftComponent> Reversed;
		Reversed.Reserve(Broken.FixingOrder.Num());
		for (int32 Index = Broken.FixingOrder.Num() - 1; Index >= 0; --Index)
		{
			Reversed.Add(Broken.FixingOrder[Index]);
		}
		Broken.FixingOrder = Reversed;
		FString Error;
		TestFalse(TEXT("a reversed fixing order is refused"),
			FLBSpacecraftProductionCatalog::ValidateFixingOrder(
				Broken, Error));
		TestTrue(TEXT("and the refusal names the access it breaks"),
			Error.Contains(TEXT("COULD NEVER BE REACHED")));
	}

	// A component blocking ITSELF is nonsense and must not pass.
	{
		FLBSpacecraftRecipe Silly = Recipes[0];
		FLBSpacecraftAccessEdge SelfEdge;
		SelfEdge.Blocker = ELBSpacecraftComponent::Hull;
		SelfEdge.Blocked = ELBSpacecraftComponent::Hull;
		Silly.AccessBlocks.Add(SelfEdge);
		FString Error;
		TestFalse(TEXT("a self-blocking edge is refused"),
			FLBSpacecraftProductionCatalog::ValidateFixingOrder(
				Silly, Error));
	}

	// REACHABILITY - the question traveled work has to ask.
	{
		const FLBSpacecraftRecipe& Recipe = Recipes[0];
		const int32 InteriorAt = Recipe.FixingOrder.IndexOfByKey(
			ELBSpacecraftComponent::Interior);
		TestTrue(TEXT("the interior is in the fixing order at all"),
			InteriorAt != INDEX_NONE);
		TestTrue(TEXT("everything is reachable on an unstarted craft"),
			FLBSpacecraftProductionCatalog::IsReachableAfter(
				Recipe, ELBSpacecraftComponent::Electronics, -1));
		TestTrue(TEXT("the harness is still reachable before the trim"),
			FLBSpacecraftProductionCatalog::IsReachableAfter(
				Recipe, ELBSpacecraftComponent::Electronics,
				InteriorAt - 1));
		TestFalse(TEXT("and is shut in once the trim is on"),
			FLBSpacecraftProductionCatalog::IsReachableAfter(
				Recipe, ELBSpacecraftComponent::Electronics, InteriorAt));
		// The hull is nobody's blocked component, so it never becomes
		// unreachable however far the build has gone.
		TestTrue(TEXT("an unblocked component is always reachable"),
			FLBSpacecraftProductionCatalog::IsReachableAfter(
				Recipe, ELBSpacecraftComponent::Hull,
				Recipe.FixingOrder.Num() - 1));
	}
	return true;
}

IMPLEMENT_SIMPLE_AUTOMATION_TEST(FLBSpacecraftCraneCarryTest,
	"LineBoss.Spacecraft.Presentation.CraneCarry",
	EAutomationTestFlags::EditorContext
		| EAutomationTestFlags::EngineFilter)

bool FLBSpacecraftCraneCarryTest::RunTest(const FString& Parameters)
{
	(void)Parameters;
	// The gantry carries the craft between stations (owner 2026-08-28,
	// choosing crane plus rail over the conveyor). The craft must be
	// DOWN on its cradle for the whole working stop, ride clear in the
	// middle of the move, and be DOWN again before the next stop - a
	// craft still in the air when the station lift comes up would be
	// jacked into its own hoist.
	const float Slide = 0.8f;
	const float Carry = 260.f;
	auto At = [Slide, Carry](float Progress)
	{
		return ALBSpacecraftWIPPresentationActor::ComputeCraneCarryCm(
			Progress, Slide, Carry);
	};

	// PARKED for the whole working stop, right up to the slide.
	TestTrue(TEXT("on the cradle at the start of the stop"),
		FMath::IsNearlyZero(At(0.f)));
	TestTrue(TEXT("still on the cradle mid-stop"),
		FMath::IsNearlyZero(At(0.5f)));
	TestTrue(TEXT("still on the cradle at the moment the slide begins"),
		FMath::IsNearlyZero(At(Slide)));

	// CARRIED across the middle of the move.
	TestTrue(TEXT("fully carried halfway between stations"),
		FMath::IsNearlyEqual(At(0.9f), Carry));

	// SET DOWN by the end, so the next stop starts on the cradle.
	TestTrue(TEXT("set down before the next station"),
		FMath::IsNearlyZero(At(1.f)));

	// MONOTONIC on each leg, stepped strictly FORWARD in time. The last
	// lift test I wrote walked its descent backwards and then blamed
	// the code for the result, so each loop here only ever increases
	// Progress and each leg is asserted in its own direction.
	float Previous = At(Slide);
	for (int32 Step = 1; Step <= 20; ++Step)
	{
		// Slide start -> the top of the rise (a quarter of the window).
		const float Progress = Slide
			+ (1.f - Slide) * 0.25f * (static_cast<float>(Step) / 20.f);
		const float Now = At(Progress);
		TestTrue(TEXT("the craft only ever rises on the way up"),
			Now >= Previous - KINDA_SMALL_NUMBER);
		Previous = Now;
	}
	Previous = At(Slide + (1.f - Slide) * 0.75f);
	for (int32 Step = 1; Step <= 20; ++Step)
	{
		// The last quarter of the window: it must only ever come down.
		const float Progress = Slide + (1.f - Slide)
			* (0.75f + 0.25f * (static_cast<float>(Step) / 20.f));
		const float Now = At(Progress);
		TestTrue(TEXT("the craft only ever descends on the way down"),
			Now <= Previous + KINDA_SMALL_NUMBER);
		Previous = Now;
	}

	// It must never exceed the carry height - the hoist cables are
	// drawn from the beam DOWN to the load, and a craft above the beam
	// would invert them.
	for (int32 Step = 0; Step <= 50; ++Step)
	{
		const float Progress = static_cast<float>(Step) / 50.f;
		TestTrue(TEXT("never carried above the beam clearance"),
			At(Progress) <= Carry + KINDA_SMALL_NUMBER);
		TestTrue(TEXT("never carried below the cradle"),
			At(Progress) >= -KINDA_SMALL_NUMBER);
	}

	// A degenerate slide window must not divide by zero or fling the
	// craft - the presenter's tunables are EditAnywhere, so a nonsense
	// value is reachable from the details panel.
	TestTrue(TEXT("a zero-width slide window is survivable"),
		ALBSpacecraftWIPPresentationActor::ComputeCraneCarryCm(
			1.f, 1.f, Carry) <= Carry + KINDA_SMALL_NUMBER);

	return true;
}

IMPLEMENT_SIMPLE_AUTOMATION_TEST(FLBSpacecraftPhase2CatalogueTest,
	"LineBoss.Spacecraft.Phase2.CatalogueSplitsRouteAndCraftingFamilies",
	EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)

bool FLBSpacecraftPhase2CatalogueTest::RunTest(const FString& Parameters)
{
	(void)Parameters;
	int32 RouteCount = 0;
	int32 CraftingCount = 0;
	int32 SiteCount = 0;
	for (const FLBSpacecraftStationDefinition& Definition :
		ALBSpacecraftBuildAuthority::StationCatalogue())
	{
		if (Definition.bRouteRequired)
		{
			++RouteCount;
			TestEqual(TEXT("slice route families stay self-powered"),
				Definition.PowerDrawKw, 0);
		}
		else if (Definition.PowerSupplyKw > 0
			|| Definition.StorageCapacityUnits > 0)
		{
			// Infrastructure: supplies or stores, never crafts.
			TestTrue(TEXT("infrastructure families need no research"),
				FLBSpacecraftResearchCatalogue::GetDefaultStationClasses()
					.Contains(Definition.DefinitionId));
			TestEqual(TEXT("infrastructure families craft nothing"),
				FLBSpacecraftRecipeCatalogue::GetRecipesForStationClass(
					Definition.DefinitionId).Num(), 0);
		}
		else if (Definition.bSiteBuilding)
		{
			// A SITE BUILDING is the world map's own kind (owner
			// 2026-08-28): it holds a floor rather than machinery, so
			// it neither crafts nor draws.
			++SiteCount;
			// A site building either offers a FLOOR to build on (the
			// ship factory) or SLOTS to install into (the parts
			// factory, the power plant) - never neither, or entering
			// it would do nothing.
			TestTrue(TEXT("site buildings offer a floor or slots"),
				!Definition.InteriorFloorCm.IsNearlyZero()
				|| Definition.SlotCount > 0);
			TestEqual(TEXT("site buildings craft nothing"),
				FLBSpacecraftRecipeCatalogue::GetRecipesForStationClass(
					Definition.DefinitionId).Num(), 0);
		}
		else if (Definition.SlotCount > 0)
		{
			// Dedicated slot buildings (owner 2026-08-26) are unit
			// CONTAINERS: they neither craft nor draw - their hosted
			// units do both.
			TestTrue(TEXT("slot buildings name their unit class"),
				!Definition.SlotUnitClass.IsNone());
		}
		else
		{
			++CraftingCount;
			TestTrue(TEXT("crafting families draw real power"),
				Definition.PowerDrawKw > 0);
			// Ask the RECIPE class: a Mk2 mark runs the recipes of the
			// mark below it rather than carrying a duplicate table.
			TestTrue(TEXT("crafting families offer recipes"),
				FLBSpacecraftRecipeCatalogue::GetRecipesForStationClass(
					Definition.GetRecipeClassId()).Num() > 0);
		}
	}
	// 8 after the test bay retired (owner 2026-08-26): 4 classes x
	// Mk1+Mk2; the self-start hover at the line end is the test now.
	// NINE since 2026-08-28: the SPRAY BOOTH joined the route as the
	// line's one PROCESS station - the craft passes through it rather
	// than having parts fitted at it, which is what lets it exist
	// without reopening the one-repeated-fitting-station rule.
	TestEqual(TEXT("nine route definitions (4 classes x Mk1+Mk2, ")
		TEXT("plus the spray booth)"), RouteCount, 9);
	// 12 = six families x Mk1+Mk2, the parts line's own upgrade path.
	// NINE crafting families since 2026-08-27: the Smelter, Structure
	// fab and Fit-out fab were added to take the fabrication that had
	// been standing on the LINE. Owner's rule: anything that makes
	// parts is sub-assembly and goes in a different building.
	TestEqual(TEXT("eighteen crafting definitions (9 families x Mk1+Mk2)"),
		CraftingCount, 18);
	// THREE world-map buildings at one scale (owner 2026-08-28): the
	// ship factory, the parts factory and the power plant.
	TestEqual(TEXT("three site buildings"), SiteCount, 3);
	TestEqual(TEXT("thirty-three families (9 route + 18 craft + 3 infra ")
		TEXT("+ 3 site)"),
		ALBSpacecraftBuildAuthority::StationCatalogue().Num(), 33);

	// The canonical slice line still commissions with route families only.
	UWorld* World = UWorld::CreateWorld(EWorldType::Game, false,
		FName(TEXT("LBSpacecraftPhase2CatalogueWorld")));
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
	FString Reason;
	TestTrue(TEXT("slice line commissions without crafting families"),
		ALBSpacecraftGameMode::SetupCanonicalLine(*Build, Reason));
	World->DestroyWorld(false);
	return true;
}

IMPLEMENT_SIMPLE_AUTOMATION_TEST(FLBSpacecraftPhase2GateTest,
	"LineBoss.Spacecraft.Phase2.ResearchAndPowerGatePlacement",
	EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)

bool FLBSpacecraftPhase2GateTest::RunTest(const FString& Parameters)
{
	(void)Parameters;
	using namespace LBSpacecraftPhase2IntegrationTestsPrivate;
	FLBSpacecraftPhase2Rig Rig = MakeSpacecraftPhase2Rig();
	FString Reason;
	FName StationId;
	const FTransform Spot(FRotator::ZeroRotator,
		FVector(3000.f, 3000.f, 0.f));

	// Locked family: the build authority itself refuses.
	TestFalse(TEXT("an unresearched rolling mill is refused"),
		Rig.Build->PlaceStation(FName(TEXT("RollingMill")), Spot, StationId,
			Reason));
	TestTrue(TEXT("the refusal names the lock"),
		Reason.Contains(TEXT("LOCKED")));
	TestTrue(TEXT("a slice family passes the gate"),
		Rig.Build->PlaceStation(FName(TEXT("MaterialProcessor")),
			FTransform(FRotator::ZeroRotator,
				FVector(-3000.f, -3000.f, 0.f)),
			StationId, Reason));

	// Research opens the family; the powered placement path then demands
	// headroom and rolls the station back when the grid cannot carry it.
	TestTrue(TEXT("points bank"), Rig.Research->AddPoints(10, Reason));
	TestTrue(TEXT("tier 1 unlocks"),
		Rig.Research->UnlockNode(FName(TEXT("Research.Mfg.T1")), Reason));
	// The researched family is installed in its hall, not dropped on
	// the floor (owner 2026-08-26: parts live in their own building).
	FName FamilyHallId;
	TestTrue(TEXT("a sub-assembly hall places"),
		// The parts factory is a WORLD-MAP building now (owner
		// 2026-08-28): it stands on open ground beside the ship
		// factory, not on the spot a machine would take inside it.
		Rig.Build->PlaceStation(FName(TEXT("SubAssemblyHall")),
			FTransform(FRotator::ZeroRotator,
				FVector(16000.f, 0.f, 0.f)),
			FamilyHallId, Reason));
	TestTrue(TEXT("the researched family now installs"),
		Rig.Build->InstallInSlot(FamilyHallId, FName(TEXT("RollingMill")),
			StationId, Reason));
	const FLBSpacecraftStationDefinition* Mill =
		ALBSpacecraftBuildAuthority::FindDefinition(
			FName(TEXT("RollingMill")));
	TestNotNull(TEXT("mill definition exists"), Mill);
	if (Mill != nullptr)
	{
		// With the mains feed off, the raw budget gate still refuses a
		// dark grid - the mains policy is covered by its own case.
		Rig.Power->GridFeedKw = 0;
		TestFalse(TEXT("a dark grid refuses the mill's power draw"),
			Rig.Power->ConnectLoad(StationId, Mill->PowerDrawKw, Reason));
		TestTrue(TEXT("a plant carries it"),
			Rig.Power->RegisterSupply(FName(TEXT("Plant.01")), 1000, Reason)
			&& Rig.Power->ConnectLoad(StationId, Mill->PowerDrawKw, Reason));
		TestEqual(TEXT("the draw is registered"),
			Rig.Power->GetTotalDrawKw(), Mill->PowerDrawKw);
	}

	Rig.World->DestroyWorld(false);
	return true;
}

IMPLEMENT_SIMPLE_AUTOMATION_TEST(FLBSpacecraftPhase2SaveTest,
	"LineBoss.Spacecraft.Phase2.SaveV2CarriesAllSevenSnapshots",
	EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)

bool FLBSpacecraftPhase2SaveTest::RunTest(const FString& Parameters)
{
	(void)Parameters;
	using namespace LBSpacecraftPhase2IntegrationTestsPrivate;
	const TCHAR* Slot = TEXT("LBSpacecraftPhase2TestSlot");
	FLBSpacecraftPhase2Rig Rig = MakeSpacecraftPhase2Rig();
	FString Reason;

	// Build real state in every Phase-2 authority.
	TestTrue(TEXT("line commissions"),
		ALBSpacecraftGameMode::SetupCanonicalLine(*Rig.Build, Reason));
	// A commissioned factory is always configured (BuildLine does both);
	// the runtime snapshot's route CRC depends on it.
	TestTrue(TEXT("coordinator configures"),
		Rig.Coordinator->ConfigureFromAuthorities(Rig.Build, Rig.Production,
			Reason));
	TestTrue(TEXT("store registers"),
		Rig.Inventory->RegisterStore(FName(TEXT("Store.Floor")), 500,
			Reason));
	TestTrue(TEXT("ore deposits"),
		Rig.Inventory->Deposit(FName(TEXT("Store.Floor")),
			FName(TEXT("Raw.IronOre")), 20, Reason));
	TestTrue(TEXT("recipe selects"),
		Rig.Crafting->SelectRecipe(FName(TEXT("St.MP")),
			FName(TEXT("Smelter")), FName(TEXT("Recipe.Steel")),
			Reason));
	TestTrue(TEXT("plant registers"),
		Rig.Power->RegisterSupply(FName(TEXT("Plant.01")), 500, Reason));
	TestTrue(TEXT("load connects"),
		Rig.Power->ConnectLoad(FName(TEXT("Load.Dev")), 200, Reason));
	TestTrue(TEXT("points bank"), Rig.Research->AddPoints(15, Reason));
	TestTrue(TEXT("tier 1 unlocks"),
		Rig.Research->UnlockNode(FName(TEXT("Research.Mfg.T1")), Reason));

	TestTrue(TEXT("v2 save succeeds"),
		FLBSpacecraftSavePipeline::SaveToSlot(Rig.Context(), Slot, Reason));

	// Diverge everything, then load back.
	TestTrue(TEXT("more ore deposits"),
		Rig.Inventory->Deposit(FName(TEXT("Store.Floor")),
			FName(TEXT("Raw.IronOre")), 30, Reason));
	TestTrue(TEXT("selection clears"),
		Rig.Crafting->ClearSelection(FName(TEXT("St.MP")), Reason));
	TestTrue(TEXT("extra load connects"),
		Rig.Power->ConnectLoad(FName(TEXT("Load.Extra")), 100, Reason));
	TestTrue(TEXT("more points bank"), Rig.Research->AddPoints(99, Reason));

	TestTrue(TEXT("v2 load succeeds"),
		FLBSpacecraftSavePipeline::LoadFromSlot(Rig.Context(), Slot,
			Reason));
	TestEqual(TEXT("inventory rewound"),
		Rig.Inventory->GetQuantity(FName(TEXT("Store.Floor")),
			FName(TEXT("Raw.IronOre"))), 20);
	TestNotNull(TEXT("crafting selection rewound"),
		Rig.Crafting->GetSelectedRecipe(FName(TEXT("St.MP"))));
	TestEqual(TEXT("power rewound"), Rig.Power->GetTotalDrawKw(), 200);
	TestEqual(TEXT("research points rewound"), Rig.Research->GetPoints(), 5);
	TestTrue(TEXT("the unlock survived"),
		Rig.Research->IsNodeUnlocked(FName(TEXT("Research.Mfg.T1"))));

	// A save context missing an authority is refused outright.
	FLBSpacecraftSaveContext Partial = Rig.Context();
	Partial.Research = nullptr;
	TestFalse(TEXT("an incomplete context refuses to save"),
		FLBSpacecraftSavePipeline::SaveToSlot(Partial, Slot, Reason));
	TestFalse(TEXT("an incomplete context refuses to load"),
		FLBSpacecraftSavePipeline::LoadFromSlot(Partial, Slot, Reason));

	UGameplayStatics::DeleteGameInSlot(Slot, 0);
	Rig.World->DestroyWorld(false);
	return true;
}

IMPLEMENT_SIMPLE_AUTOMATION_TEST(FLBSpacecraftPhase2CargoTierTest,
	"LineBoss.Spacecraft.Phase2.CargoTierRefusedUntilBiggerMarks",
	EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)

bool FLBSpacecraftPhase2CargoTierTest::RunTest(const FString& Parameters)
{
	(void)Parameters;
	// The Cargo-01 recipe exists in the catalogue and validates - but the
	// Mk1 line CANNOT service it (the Scout is the smallest craft; bigger
	// tiers need bigger station marks). That refusal is the honest EA
	// state until Mk2 marks ship.
	FLBSpacecraftRecipe Cargo;
	FString Reason;
	TestTrue(TEXT("Cargo-01 is in the catalogue"),
		FLBSpacecraftProductionCatalog::FindRecipe(FName(TEXT("CARGO-01")),
			Cargo));
	TestTrue(TEXT("Cargo-01 is strictly larger than the Scout"),
		Cargo.CraftEnvelopeCm.X > 1400.f);

	UWorld* World = UWorld::CreateWorld(EWorldType::Game, false,
		FName(TEXT("LBSpacecraftPhase2CargoWorld")));
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
	TestTrue(TEXT("Mk1 line commissions"),
		ALBSpacecraftGameMode::SetupCanonicalLine(*Build, Reason));
	TArray<FLBSpacecraftRouteStep> Route;
	TestTrue(TEXT("route derives"), Build->BuildRoute(Route, Reason));
	TestFalse(TEXT("the Mk1 route refuses the Cargo-01 envelope"),
		ALBSpacecraftBuildAuthority::RouteCanServiceRecipe(Route, Cargo,
			Reason));
	TestTrue(TEXT("the refusal demands a larger mark"),
		Reason.Contains(TEXT("LARGER STATION MARK")));

	World->DestroyWorld(false);
	return true;
}

IMPLEMENT_SIMPLE_AUTOMATION_TEST(FLBSpacecraftPhase2InfraTest,
	"LineBoss.Spacecraft.Phase2.InfrastructureWiresAndUnwindsFailClosed",
	EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)

bool FLBSpacecraftPhase2InfraTest::RunTest(const FString& Parameters)
{
	(void)Parameters;
	using namespace LBSpacecraftPhase2IntegrationTestsPrivate;
	FLBSpacecraftPhase2Rig Rig = MakeSpacecraftPhase2Rig();
	FString Reason;
	FName PlantId;
	FName RackId;
	FName MillId;

	// There is no dead grid any more (owner 2026-08-26: the mains feed
	// carries the floor until the player builds generation): a mill's
	// 400 kW connects on grid credit alone - metered, not refused.
	TestTrue(TEXT("points bank"), Rig.Research->AddPoints(10, Reason));
	TestTrue(TEXT("tier 1 unlocks"),
		Rig.Research->UnlockNode(FName(TEXT("Research.Mfg.T1")), Reason));
	// One hall holds the mills; each install draws on the mains.
	FName MainsHallId;
	TestTrue(TEXT("a sub-assembly hall places"),
		ALBSpacecraftGameMode::PlaceStationPowered(*Rig.Build, *Rig.Power,
			*Rig.Inventory, FName(TEXT("SubAssemblyHall")),
			FTransform(FRotator::ZeroRotator, FVector(16000.f, 0.f, 0.f)),
			MainsHallId, Reason));
	TestTrue(TEXT("a mill runs on the mains feed"),
		ALBSpacecraftGameMode::InstallInSlotPowered(*Rig.Build, *Rig.Power,
			MainsHallId, FName(TEXT("RollingMill")), MillId, Reason));
	TestEqual(TEXT("the whole draw is metered from the grid"),
		Rig.Power->GetGridUseKw(), 400);
	// The FEED IS CAPPED: draw beyond it still refuses whole and
	// unwinds - generation is how the factory scales.
	FName SecondMillId;
	TestTrue(TEXT("a second mill fills the feed"),
		ALBSpacecraftGameMode::InstallInSlotPowered(*Rig.Build, *Rig.Power,
			MainsHallId, FName(TEXT("RollingMill")), SecondMillId, Reason));
	FName ThirdMillId;
	TestFalse(TEXT("the feed cap refuses the third mill whole"),
		ALBSpacecraftGameMode::InstallInSlotPowered(*Rig.Build, *Rig.Power,
			MainsHallId, FName(TEXT("RollingMill")), ThirdMillId, Reason));
	// 3 = the hall plus its two installed mills; the refused third
	// left nothing behind.
	TestEqual(TEXT("the refused mill left no station behind"),
		// +1 for the ship factory every interior building stands in.
		Rig.Build->GetStations().Num(), 4);
	// Clear the cap-check mills so the wiring flow below starts clean.
	TestTrue(TEXT("cap-check mill one removes"),
		ALBSpacecraftGameMode::RemoveStationPowered(*Rig.Build, *Rig.Power,
			*Rig.Inventory, Rig.Crafting, MillId, Reason));
	TestTrue(TEXT("cap-check mill two removes"),
		ALBSpacecraftGameMode::RemoveStationPowered(*Rig.Build, *Rig.Power,
			*Rig.Inventory, Rig.Crafting, SecondMillId, Reason));

	// A PowerPlant registers its supply under its station id.
	FName PowerHallId;
	TestTrue(TEXT("power hall places"),
		ALBSpacecraftGameMode::PlaceStationPowered(*Rig.Build, *Rig.Power, *Rig.Inventory, FName(TEXT("PowerStation")), FTransform(FRotator::ZeroRotator, FVector(-16000.f, 0.f, 0.f)), PowerHallId, Reason));
	// The generator lives INSIDE its hall (owner
	// 2026-08-26): free placement is refused now.
	TestTrue(TEXT("plant installs in the hall"),
		ALBSpacecraftGameMode::InstallInSlotPowered(*Rig.Build, *Rig.Power, PowerHallId,
			FName(TEXT("PowerPlant")), PlantId, Reason));
	TestEqual(TEXT("the plant registers its OWN generation"),
		Rig.Power->GetOwnSupplyKw(), 1500);

	// A StorageRack registers its ledger store.
	TestTrue(TEXT("rack places"),
		ALBSpacecraftGameMode::PlaceStationPowered(*Rig.Build, *Rig.Power,
			*Rig.Inventory, FName(TEXT("StorageRack")),
			FTransform(FRotator::ZeroRotator, FVector(-3000.f, -3000.f, 0.f)),
			RackId, Reason));
	const FName RackStore(*FString::Printf(TEXT("Store.%s"),
		*RackId.ToString()));
	TestTrue(TEXT("the rack's store exists"),
		Rig.Inventory->HasStore(RackStore));
	TestEqual(TEXT("the store carries the catalogue capacity"),
		Rig.Inventory->GetCapacityUnits(RackStore), 2000);

	// Now the mill powers up, drawing from the plant.
	// Parts machines live in the sub-assembly hall (owner
	// 2026-08-26), so the mill is installed, not placed.
	// The mains hall from the cap check is still standing (only its
	// mills were shed), so the grid mill moves back into it.
	const FName GridHallId = MainsHallId;
	TestTrue(TEXT("the mill installs on the live grid"),
		ALBSpacecraftGameMode::InstallInSlotPowered(*Rig.Build, *Rig.Power,
			GridHallId, FName(TEXT("RollingMill")), MillId, Reason));
	TestEqual(TEXT("the mill draws its catalogue kW"),
		Rig.Power->GetTotalDrawKw(), 400);

	// Removal law under the mains feed (owner 2026-08-26): the plant
	// MAY retire while the mill runs - the load falls back to metered
	// grid credit, honestly costlier, never stranded.
	TestTrue(TEXT("the loaded plant retires onto the mains"),
		ALBSpacecraftGameMode::RemoveStationPowered(*Rig.Build, *Rig.Power,
			*Rig.Inventory, Rig.Crafting, PlantId, Reason));
	TestEqual(TEXT("the mill's draw shifted to the meter"),
		Rig.Power->GetGridUseKw(), 400);
	// A stocked rack cannot be removed either.
	TestTrue(TEXT("stock deposits into the rack"),
		Rig.Inventory->Deposit(RackStore, FName(TEXT("Raw.IronOre")), 5,
			Reason));
	TestFalse(TEXT("removing the stocked rack is refused"),
		ALBSpacecraftGameMode::RemoveStationPowered(*Rig.Build, *Rig.Power,
			*Rig.Inventory, Rig.Crafting, RackId, Reason));
	TestTrue(TEXT("the refusal says empty it first"),
		Reason.Contains(TEXT("EMPTY IT FIRST")));
	// Empty the rack, shed the mill, and both removals go through.
	TestTrue(TEXT("stock withdraws"),
		Rig.Inventory->Withdraw(RackStore, FName(TEXT("Raw.IronOre")), 5,
			Reason));
	TestTrue(TEXT("the emptied rack removes"),
		ALBSpacecraftGameMode::RemoveStationPowered(*Rig.Build, *Rig.Power,
			*Rig.Inventory, Rig.Crafting, RackId, Reason));
	TestFalse(TEXT("the rack's store is gone"),
		Rig.Inventory->HasStore(RackStore));
	TestTrue(TEXT("the mill removes and frees its draw"),
		ALBSpacecraftGameMode::RemoveStationPowered(*Rig.Build, *Rig.Power,
			*Rig.Inventory, Rig.Crafting, MillId, Reason));
	TestEqual(TEXT("no draw remains"), Rig.Power->GetTotalDrawKw(), 0);
	// The emptied hall retires last (its generator already went).
	TestTrue(TEXT("the empty power hall removes"),
		ALBSpacecraftGameMode::RemoveStationPowered(*Rig.Build, *Rig.Power,
			*Rig.Inventory, Rig.Crafting, PowerHallId, Reason));
	TestTrue(TEXT("the empty parts hall removes"),
		ALBSpacecraftGameMode::RemoveStationPowered(*Rig.Build, *Rig.Power,
			*Rig.Inventory, Rig.Crafting, GridHallId, Reason));
	// The hall itself remains: removing machines never demolishes the
	// building they stood in.
	TestEqual(TEXT("the floor is clear"), Rig.Build->GetStations().Num(), 1);

	Rig.World->DestroyWorld(false);
	return true;
}

IMPLEMENT_SIMPLE_AUTOMATION_TEST(FLBSpacecraftPhase2TickedCraftingTest,
	"LineBoss.Spacecraft.Phase2.PlacedStationsCraftOnTheSimClock",
	EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)

bool FLBSpacecraftPhase2TickedCraftingTest::RunTest(const FString& Parameters)
{
	(void)Parameters;
	using namespace LBSpacecraftPhase2IntegrationTestsPrivate;
	FLBSpacecraftPhase2Rig Rig = MakeSpacecraftPhase2Rig();
	FString Reason;
	FName PlantId;
	FName MillId;
	FName MpId;

	// Power, research, then a processor (free family) and a mill.
	FName PowerHallId;
	TestTrue(TEXT("power hall places"),
		ALBSpacecraftGameMode::PlaceStationPowered(*Rig.Build, *Rig.Power, *Rig.Inventory, FName(TEXT("PowerStation")), FTransform(FRotator::ZeroRotator, FVector(-16000.f, 0.f, 0.f)), PowerHallId, Reason));
	// The generator lives INSIDE its hall (owner
	// 2026-08-26): free placement is refused now.
	TestTrue(TEXT("plant installs in the hall"),
		ALBSpacecraftGameMode::InstallInSlotPowered(*Rig.Build, *Rig.Power, PowerHallId,
			FName(TEXT("PowerPlant")), PlantId, Reason));
	TestTrue(TEXT("points bank"), Rig.Research->AddPoints(10, Reason));
	TestTrue(TEXT("tier 1 unlocks"),
		Rig.Research->UnlockNode(FName(TEXT("Research.Mfg.T1")), Reason));
	// Parts machines live in the sub-assembly hall (owner 2026-08-26),
	// so they are INSTALLED, not placed. Smelting moved here on
	// 2026-08-27 with the rest of the fabrication: the material
	// processor is a LINE station, and "anything that makes parts is
	// sub assembly which goes in a different building" (owner). This
	// test used to smelt steel on the line station, which is exactly
	// the arrangement the rule forbids.
	FName MillHallId;
	TestTrue(TEXT("a sub-assembly hall places"),
		ALBSpacecraftGameMode::PlaceStationPowered(*Rig.Build, *Rig.Power,
			*Rig.Inventory, FName(TEXT("SubAssemblyHall")),
			FTransform(FRotator::ZeroRotator, FVector(16000.f, 0.f, 0.f)),
			MillHallId, Reason));
	TestTrue(TEXT("the smelter installs in the hall"),
		ALBSpacecraftGameMode::InstallInSlotPowered(*Rig.Build, *Rig.Power,
			MillHallId, FName(TEXT("Smelter")), MpId, Reason));
	TestTrue(TEXT("mill installs in the hall"),
		ALBSpacecraftGameMode::InstallInSlotPowered(*Rig.Build, *Rig.Power,
			MillHallId, FName(TEXT("RollingMill")), MillId, Reason));

	// Recipe selection is class-derived from the RECORD and gated.
	TestFalse(TEXT("a wrong-family recipe is refused on the record"),
		ALBSpacecraftGameMode::SelectStationRecipe(*Rig.Build, *Rig.Crafting,
			*Rig.Research, MpId, FName(TEXT("Recipe.PlateStock")), Reason));
	TestTrue(TEXT("the processor selects steel"),
		ALBSpacecraftGameMode::SelectStationRecipe(*Rig.Build, *Rig.Crafting,
			*Rig.Research, MpId, FName(TEXT("Recipe.Steel")), Reason));
	TestTrue(TEXT("a standing order opens"),
		Rig.Crafting->AddOrder(MpId, 99, Reason));
	TestTrue(TEXT("the mill selects plate"),
		ALBSpacecraftGameMode::SelectStationRecipe(*Rig.Build, *Rig.Crafting,
			*Rig.Research, MillId, FName(TEXT("Recipe.PlateStock")), Reason));
	TestTrue(TEXT("a standing order opens"),
		Rig.Crafting->AddOrder(MillId, 99, Reason));

	// Ore in; tick the whole floor on the sim clock. Steel (8 s) feeds
	// plate (10 s) through the shared floor store.
	// Goods live AT the station that uses them now (owner 2026-08-27,
	// the Production Line model), so the ore goes into the processor's
	// own stockpile rather than a shared floor store. The yard is
	// still registered as the site overflow the haulers spill into.
	TestTrue(TEXT("the site overflow yard registers"),
		Rig.Inventory->RegisterStore(
			ALBSpacecraftGameMode::SiteOverflowStoreId(), 5000, Reason));
	ALBSpacecraftGameMode::SyncStationStores(*Rig.Build, *Rig.Inventory,
		Rig.Crafting);
	TestTrue(TEXT("ore deposits into the processor's stockpile"),
		Rig.Inventory->Deposit(
			FName(*FString::Printf(TEXT("Store.%s"),
				*MpId.ToString())),
			FName(TEXT("Raw.IronOre")), 8, Reason));
	// Sub-assembly rule (owner 2026-08-26): outputs buffer at each
	// machine and the heavy hauler moves them - the chain flows only
	// through the physical haul, so the loop runs BOTH ticks.
	ALBSpacecraftDroneFleetAuthority* HaulFleet =
		Rig.World->SpawnActor<ALBSpacecraftDroneFleetAuthority>();
	FName HaulRackId;
	TestTrue(TEXT("haul rack places"),
		Rig.Build->PlaceStation(FName(TEXT("StorageRack")),
			FTransform(FRotator::ZeroRotator,
				FVector(-4400.f, 2500.f, 0.f)), HaulRackId, Reason));
	HaulFleet->SyncFromBuild(Rig.Build, nullptr);
	int32 Cycles = 0;
	for (int32 Tick = 0; Tick < 24; ++Tick)
	{
		ALBSpacecraftGameMode::SyncStationStores(*Rig.Build,
			*Rig.Inventory, Rig.Crafting);
		Cycles += ALBSpacecraftGameMode::TickCraftingStations(*Rig.Build,
			*Rig.Crafting, *Rig.Inventory, 5.0);
		HaulFleet->TickHauls(5.0, Rig.Crafting, Rig.Inventory, Rig.Build);
	}
	// 120 sim s: the processor smelts (buffering), the hauler lands
	// steel on the floor, the mill rolls plate, the hauler lands that
	// too - the chain is the physical journey now.
	TestEqual(TEXT("all ore was smelted"),
		Rig.Inventory->GetQuantity(
			FName(*FString::Printf(TEXT("Store.%s"),
				*MpId.ToString())),
			FName(TEXT("Raw.IronOre"))), 0);
	// The steel the processor made was hauled to the rack, delivered
	// on to the mill, rolled into plate and hauled back - so the plate
	// is wherever the haulers put it down.
	const FName HaulRackStore(*FString::Printf(TEXT("Store.%s"),
		*HaulRackId.ToString()));
	TestTrue(TEXT("plate stock exists from the chained stations"),
		Rig.Inventory->GetQuantity(HaulRackStore,
			FName(TEXT("Proc.PlateStock")))
		+ Rig.Inventory->GetQuantity(
			ALBSpacecraftGameMode::SiteOverflowStoreId(),
			FName(TEXT("Proc.PlateStock"))) > 0);
	TestTrue(TEXT("cycles completed on the clock"), Cycles >= 5);

	// The presenter mirrors the crafting stations like any other record.
	ALBSpacecraftWIPPresentationActor* Presenter =
		Rig.World->SpawnActor<ALBSpacecraftWIPPresentationActor>();
	Presenter->BindAuthorities(Rig.Build, Rig.Coordinator, Rig.Production);
	Presenter->Tick(0.1f);
	TestEqual(TEXT("one visual per placed station, crafting included"),
		Presenter->GetStationVisualCount(),
		LBSpacecraftVisualCountPrivate::SpacecraftMachineStationCountPhase2(
			*Rig.Build));

	Rig.World->DestroyWorld(false);
	return true;
}

IMPLEMENT_SIMPLE_AUTOMATION_TEST(FLBSpacecraftMk2LineTest,
	"LineBoss.Spacecraft.Phase2.Mk2LineServicesCargoAndScout",
	EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)

bool FLBSpacecraftMk2LineTest::RunTest(const FString& Parameters)
{
	(void)Parameters;
	using namespace LBSpacecraftPhase2IntegrationTestsPrivate;
	FLBSpacecraftPhase2Rig Rig = MakeSpacecraftPhase2Rig();
	FString Reason;
	FName StationId;

	// Mk2 marks are research-gated: T1 -> T2 -> Mk2.
	TestFalse(TEXT("an unresearched Mk2 mark is refused"),
		Rig.Build->PlaceStation(FName(TEXT("MaterialProcessorMk2")),
			FTransform(FRotator::ZeroRotator, FVector(-3000.f, -4000.f, 0.f)),
			StationId, Reason));
	TestTrue(TEXT("points bank"), Rig.Research->AddPoints(95, Reason));
	TestTrue(TEXT("T1 unlocks"),
		Rig.Research->UnlockNode(FName(TEXT("Research.Mfg.T1")), Reason));
	TestTrue(TEXT("T2 unlocks"),
		Rig.Research->UnlockNode(FName(TEXT("Research.Mfg.T2")), Reason));
	TestTrue(TEXT("Mk2 unlocks"),
		Rig.Research->UnlockNode(FName(TEXT("Research.Mfg.Mk2")), Reason));

	// An ALL-Mk2 line commissions: any mark of a class services its stage.
	struct FLBSpacecraftMk2Placement
	{
		const TCHAR* Id;
		FVector Location;
	};
	const FLBSpacecraftMk2Placement Placements[] = {
		{ TEXT("MaterialProcessorMk2"), FVector(-3000.f, -4000.f, 0.f) },
		{ TEXT("HullFabricatorMk2"), FVector(-3000.f, 0.f, 0.f) },
		{ TEXT("ComponentFabricatorMk2"), FVector(-3000.f, 4000.f, 0.f) },
		{ TEXT("AssemblyRobotMk2"), FVector(3000.f, -4000.f, 0.f) },
	};
	for (const FLBSpacecraftMk2Placement& Placement : Placements)
	{
		TestTrue(FString::Printf(TEXT("%s places"), Placement.Id),
			Rig.Build->PlaceStation(FName(Placement.Id),
				FTransform(FRotator::ZeroRotator, Placement.Location),
				StationId, Reason));
	}
	TestTrue(TEXT("the all-Mk2 line commissions"),
		EnsureSprayBoothAndCommission(Rig, Reason));
	TArray<FLBSpacecraftRouteStep> Route;
	TestTrue(TEXT("the route derives across marks"),
		Rig.Build->BuildRoute(Route, Reason));

	// The Mk2 line holds BOTH tiers; the capacity law reads the placed
	// mark, not the base class.
	FLBSpacecraftRecipe Cargo;
	FLBSpacecraftRecipe Scout;
	TestTrue(TEXT("Cargo-01 resolves"),
		FLBSpacecraftProductionCatalog::FindRecipe(FName(TEXT("CARGO-01")),
			Cargo));
	TestTrue(TEXT("Scout-01 resolves"),
		FLBSpacecraftProductionCatalog::FindRecipe(FName(TEXT("SCOUT-01")),
			Scout));
	TestTrue(TEXT("the Mk2 route accepts Cargo-01"),
		ALBSpacecraftBuildAuthority::RouteCanServiceRecipe(Route, Cargo,
			Reason));
	TestTrue(TEXT("the Mk2 route still accepts Scout-01"),
		ALBSpacecraftBuildAuthority::RouteCanServiceRecipe(Route, Scout,
			Reason));

	Rig.World->DestroyWorld(false);
	return true;
}

IMPLEMENT_SIMPLE_AUTOMATION_TEST(FLBSpacecraftCargoDemandTest,
	"LineBoss.Spacecraft.Phase2.DemandPicksTheRecipeAndFailsClosed",
	EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)

bool FLBSpacecraftCargoDemandTest::RunTest(const FString& Parameters)
{
	(void)Parameters;
	using namespace LBSpacecraftPhase2IntegrationTestsPrivate;
	FString Reason;

	// A Cargo contract on the Mk1 line NEVER spawns a unit - and never
	// halts the line either. The refusal lives in the spawn attempt.
	{
		FLBSpacecraftPhase2Rig Rig = MakeSpacecraftPhase2Rig();
		TestTrue(TEXT("Mk1 line commissions"),
			ALBSpacecraftGameMode::SetupCanonicalLine(*Rig.Build, Reason));
		TestTrue(TEXT("coordinator configures"),
			Rig.Coordinator->ConfigureFromAuthorities(Rig.Build,
				Rig.Production, Reason));
		TestTrue(TEXT("a Cargo contract accepts"),
			ALBSpacecraftGameMode::StartRecipeContract(*Rig.Production,
				FName(TEXT("CARGO-01")), 1, Reason));
		for (int32 Tick = 0; Tick < 20; ++Tick)
		{
			TestTrue(TEXT("the line ticks without halting"),
				Rig.Coordinator->TickProduction(5.0, Reason));
		}
		TestEqual(TEXT("no Cargo unit ever spawned on Mk1"),
			Rig.Production->GetUnits().Num(), 0);
		Rig.World->DestroyWorld(false);
	}

	// On an all-Mk2 line the same contract flows to a dispatched craft
	// paid at the CARGO price.
	{
		FLBSpacecraftPhase2Rig Rig = MakeSpacecraftPhase2Rig();
		FName StationId;
		TestTrue(TEXT("points bank"), Rig.Research->AddPoints(95, Reason));
		TestTrue(TEXT("T1"), Rig.Research->UnlockNode(
			FName(TEXT("Research.Mfg.T1")), Reason));
		TestTrue(TEXT("T2"), Rig.Research->UnlockNode(
			FName(TEXT("Research.Mfg.T2")), Reason));
		TestTrue(TEXT("Mk2"), Rig.Research->UnlockNode(
			FName(TEXT("Research.Mfg.Mk2")), Reason));
		const TCHAR* Ids[] = { TEXT("MaterialProcessorMk2"),
			TEXT("HullFabricatorMk2"), TEXT("ComponentFabricatorMk2"),
			TEXT("AssemblyRobotMk2") };
		const FVector Spots[] = {
			FVector(-3000.f, -4000.f, 0.f), FVector(-3000.f, 0.f, 0.f),
			FVector(-3000.f, 4000.f, 0.f),
			FVector(3000.f, -4000.f, 0.f) };
		for (int32 Index = 0; Index < UE_ARRAY_COUNT(Ids); ++Index)
		{
			TestTrue(TEXT("Mk2 station places"),
				Rig.Build->PlaceStation(FName(Ids[Index]),
					FTransform(FRotator::ZeroRotator, Spots[Index]),
					StationId, Reason));
			// Crewed to nominal so the Cargo craft passes its hover
			// test on workmanship; the defective path is tested
			// deliberately elsewhere.
			for (int32 Crew = 0; Crew < 2; ++Crew)
			{
				TestTrue(TEXT("Mk2 station crews"),
					Rig.Build->InstallStationDrone(StationId, Reason));
			}
		}
		TestTrue(TEXT("Mk2 line commissions"),
			EnsureSprayBoothAndCommission(Rig, Reason));
		TestTrue(TEXT("coordinator configures"),
			Rig.Coordinator->ConfigureFromAuthorities(Rig.Build,
				Rig.Production, Reason));
		TestTrue(TEXT("a Cargo contract accepts"),
			ALBSpacecraftGameMode::StartRecipeContract(*Rig.Production,
				FName(TEXT("CARGO-01")), 1, Reason));
		int32 Guard = 0;
		while (Rig.Production->GetRevenuePence() < 36000000 && Guard++ < 400)
		{
			TestTrue(TEXT("tick runs"),
				Rig.Coordinator->TickProduction(5.0, Reason));
		}
		TestEqual(TEXT("the Cargo craft settled at the Cargo price"),
			Rig.Production->GetRevenuePence(), (int64)36000000);
		TestTrue(TEXT("a CARGO unit was built"),
			Rig.Production->GetUnits().Num() > 0
			&& Rig.Production->GetUnits()[0].RecipeId
				== FName(TEXT("CARGO-01")));
		Rig.World->DestroyWorld(false);
	}
	return true;
}

IMPLEMENT_SIMPLE_AUTOMATION_TEST(FLBSpacecraftStationAccentTest,
	"LineBoss.Spacecraft.Presentation.StationAccentsReflectRealState",
	EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)

bool FLBSpacecraftStationAccentTest::RunTest(const FString& Parameters)
{
	(void)Parameters;
	using namespace LBSpacecraftPhase2IntegrationTestsPrivate;

	// Pure animation maths first: deterministic, no world needed.
	TestEqual(TEXT("pulse is 0.5 at t=0"),
		ALBSpacecraftWIPPresentationActor::ComputeAccentPulse01(0.f, 2.4f),
		0.5f);
	TestTrue(TEXT("pulse peaks a quarter period in"),
		ALBSpacecraftWIPPresentationActor::ComputeAccentPulse01(0.6f, 2.4f)
			> 0.99f);
	TestTrue(TEXT("ring yaw advances and wraps"),
		ALBSpacecraftWIPPresentationActor::ComputeRingYawDeg(1.f) == 24.f
		&& ALBSpacecraftWIPPresentationActor::ComputeRingYawDeg(20.f)
			< 360.f);

	FLBSpacecraftPhase2Rig Rig = MakeSpacecraftPhase2Rig();
	FString Reason;
	FName PlantId;
	FName MillId;
	FName PowerHallId;
	TestTrue(TEXT("power hall places"),
		ALBSpacecraftGameMode::PlaceStationPowered(*Rig.Build, *Rig.Power, *Rig.Inventory, FName(TEXT("PowerStation")), FTransform(FRotator::ZeroRotator, FVector(-16000.f, 0.f, 0.f)), PowerHallId, Reason));
	// The generator lives INSIDE its hall (owner
	// 2026-08-26): free placement is refused now.
	TestTrue(TEXT("plant installs in the hall"),
		ALBSpacecraftGameMode::InstallInSlotPowered(*Rig.Build, *Rig.Power, PowerHallId,
			FName(TEXT("PowerPlant")), PlantId, Reason));
	TestTrue(TEXT("points bank"), Rig.Research->AddPoints(10, Reason));
	TestTrue(TEXT("T1 unlocks"),
		Rig.Research->UnlockNode(FName(TEXT("Research.Mfg.T1")), Reason));
	// Parts machines live in the sub-assembly hall (owner
	// 2026-08-26), so the mill is installed, not placed.
	FName MillHallId;
	TestTrue(TEXT("a sub-assembly hall places"),
		ALBSpacecraftGameMode::PlaceStationPowered(*Rig.Build, *Rig.Power,
			*Rig.Inventory, FName(TEXT("SubAssemblyHall")),
			FTransform(FRotator::ZeroRotator, FVector(16000.f, 0.f, 0.f)),
			MillHallId, Reason));
	TestTrue(TEXT("mill installs in the hall"),
		ALBSpacecraftGameMode::InstallInSlotPowered(*Rig.Build, *Rig.Power,
			MillHallId, FName(TEXT("RollingMill")), MillId, Reason));

	ALBSpacecraftWIPPresentationActor* Presenter =
		Rig.World->SpawnActor<ALBSpacecraftWIPPresentationActor>();
	Presenter->BindAuthorities(Rig.Build, Rig.Coordinator, Rig.Production);
	Presenter->BindCrafting(Rig.Crafting);
	Presenter->Tick(0.1f);

	// Accents exist only where a REAL mesh bound (editor context loads
	// the imported derivatives; if they were absent this would honestly
	// show zero accents - the count below guards the whole chain).
	// 4 = the two buildings plus the two units housed in them; a hall
	// is a station in its own right now that plant and mill live
	// indoors (owner 2026-08-26).
	TestEqual(TEXT("every real-mesh station grew an accent"),
		// 2 since 2026-08-28: the parts factory and the power plant
		// became world-map BUILDINGS, drawn by the shell layer, so
		// only the machines inside them carry accents.
		Presenter->GetStationAccentCount(), 2);
	// The bay paint must actually BIND its material. A non-decal
	// material is refused by SetDecalMaterial in SILENCE, which is
	// exactly how the first paint pass came out invisible: live
	// components, nothing drawn. Counting bound decals is the guard.
	TestTrue(TEXT("the placed stations stamped bay paint"),
		Presenter->GetBayPaintDecalCount() > 0);
	TestEqual(TEXT("every bay decal bound a decal-domain material"),
		Presenter->GetBayPaintedDecalCount(),
		Presenter->GetBayPaintDecalCount());

	TestTrue(TEXT("the plant ring always runs"),
		Presenter->IsStationAccentActive(PlantId));
	TestFalse(TEXT("an idle mill beacon reads idle"),
		Presenter->IsStationAccentActive(MillId));

	// Select a recipe: the beacon flips to working on the next tick.
	TestTrue(TEXT("mill selects plate"),
		ALBSpacecraftGameMode::SelectStationRecipe(*Rig.Build,
			*Rig.Crafting, *Rig.Research, MillId,
			FName(TEXT("Recipe.PlateStock")), Reason));
	Presenter->Tick(0.1f);
	TestTrue(TEXT("a working mill pulses"),
		Presenter->IsStationAccentActive(MillId));

	// Removal sweeps the accent with the station.
	TestTrue(TEXT("mill removes"),
		ALBSpacecraftGameMode::RemoveStationPowered(*Rig.Build, *Rig.Power,
			*Rig.Inventory, Rig.Crafting, MillId, Reason));
	Presenter->Tick(0.1f);
	TestEqual(TEXT("the plant keeps its accent"),
		Presenter->GetStationAccentCount(), 1);

	Rig.World->DestroyWorld(false);
	return true;
}

IMPLEMENT_SIMPLE_AUTOMATION_TEST(FLBSpacecraftRunwayTest,
	"LineBoss.Spacecraft.Presentation.RunwayPaintAndStrobesFollowTheRig",
	EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)

bool FLBSpacecraftRunwayTest::RunTest(const FString& Parameters)
{
	(void)Parameters;
	using namespace LBSpacecraftPhase2IntegrationTestsPrivate;

	// Pure strobe maths: exactly one hot light, chasing toward the exit.
	for (float Clock : {0.05f, 0.5f, 1.0f})
	{
		int32 Hot = 0;
		for (int32 Index = 0; Index < 8; ++Index)
		{
			Hot += ALBSpacecraftWIPPresentationActor::
				ComputeStrobeIntensity01(Clock, Index, 8, 1.2f) > 0.5f
				? 1 : 0;
		}
		TestEqual(TEXT("exactly one strobe is hot"), Hot, 1);
	}
	TestTrue(TEXT("the hot strobe advances toward the exit"),
		ALBSpacecraftWIPPresentationActor::ComputeStrobeIntensity01(
			0.05f, 0, 8, 1.2f) > 0.5f
		&& ALBSpacecraftWIPPresentationActor::ComputeStrobeIntensity01(
			0.35f, 2, 8, 1.2f) > 0.5f);

	// Arming (owner, 2026-08-25): dark through most of the chicane, armed
	// from LeadSeconds before throttle-up onward. Chicane 2.2 s, lead 0.8:
	// arm point is t = 1.4.
	TestTrue(TEXT("strobes stay dark early in the chicane"),
		ALBSpacecraftWIPPresentationActor::ComputeStrobeArmClock(
			1.0f, 2.2f, 0.8f) < 0.f);
	TestTrue(TEXT("strobes arm just before throttle-up"),
		ALBSpacecraftWIPPresentationActor::ComputeStrobeArmClock(
			1.5f, 2.2f, 0.8f) >= 0.f);
	TestTrue(TEXT("the arm clock runs from the arm point"),
		FMath::IsNearlyEqual(
			ALBSpacecraftWIPPresentationActor::ComputeStrobeArmClock(
				2.4f, 2.2f, 0.8f), 1.0f, 0.001f));

	FLBSpacecraftPhase2Rig Rig = MakeSpacecraftPhase2Rig();
	FString Reason;
	TestTrue(TEXT("line commissions"),
		ALBSpacecraftGameMode::SetupCanonicalLine(*Rig.Build, Reason));
	ALBSpacecraftWIPPresentationActor* Presenter =
		Rig.World->SpawnActor<ALBSpacecraftWIPPresentationActor>();
	Presenter->BindAuthorities(Rig.Build, Rig.Coordinator, Rig.Production);
	Presenter->Tick(0.1f);

	// The runway is permanent site furniture (owner 2026-08-26): one
	// strip, keyed Site.Runway, present regardless of stations, and it
	// SURVIVES station removal.
	TestEqual(TEXT("one permanent site runway"),
		Presenter->GetRunwayCount(), 1);
	const FName RigId(TEXT("Site.Runway"));
	TestEqual(TEXT("the runway carries paint, threshold, strobes and "
			"the launch tube"),
		// 46 legacy parts + launch tube: 5 ribs x4 + 40 chase studs
		// + 1 centre guide.
		// 85 = the legacy pinned set plus hover pad (108) minus the 30
		// painted edge/dash/threshold parts the authored deck replaces,
		// plus 5 strip sections and 2 chicane gate pylons (owner's
		// evening drops 2026-08-26).
		Presenter->GetRunwayPartCount(RigId), 85);
	Presenter->Tick(0.1f);
	TestEqual(TEXT("site furniture survives every station"),
		Presenter->GetRunwayCount(), 1);

	Rig.World->DestroyWorld(false);
	return true;
}

IMPLEMENT_SIMPLE_AUTOMATION_TEST(FLBSpacecraftRotorAudioTest,
	"LineBoss.Spacecraft.Presentation.RotorSpeedDrivesSpinAndPitch",
	EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)

bool FLBSpacecraftRotorAudioTest::RunTest(const FString& Parameters)
{
	(void)Parameters;
	using Presenter = ALBSpacecraftWIPPresentationActor;

	// Load reads what the drone is DOING. A carrying drone must work
	// its motors harder than an empty one, or the floor would not sound
	// busier when parts are actually moving - the point of the feature.
	const float Docked = Presenter::ComputeRotorLoad01(true, false, false);
	const float Transit = Presenter::ComputeRotorLoad01(false, false, false);
	const float Fitting = Presenter::ComputeRotorLoad01(false, false, true);
	const float Carrying = Presenter::ComputeRotorLoad01(false, true, false);
	TestEqual(TEXT("a docked drone runs its motors not at all"),
		Docked, 0.f);
	TestTrue(TEXT("carrying a part is the hardest work"),
		Carrying > Fitting && Fitting > Transit && Transit > Docked);
	TestTrue(TEXT("load never exceeds full"), Carrying <= 1.f);
	TestEqual(TEXT("docked beats every other flag"),
		Presenter::ComputeRotorLoad01(true, true, true), 0.f);

	// Spool is ASYMMETRIC: motors accelerate a rotor, but only drag
	// slows it. Same elapsed time, and the climb must beat the coast.
	const float SpoolUp = 0.55f;
	const float SpoolDown = 1.9f;
	const float Climbed = Presenter::ComputeRotorSpeed01(
		0.f, 1.f, 0.3f, SpoolUp, SpoolDown);
	const float Coasted = Presenter::ComputeRotorSpeed01(
		1.f, 0.f, 0.3f, SpoolUp, SpoolDown);
	TestTrue(TEXT("rotors spool up faster than they coast down"),
		Climbed > (1.f - Coasted));
	TestTrue(TEXT("a spool step stays inside the range"),
		Climbed > 0.f && Climbed < 1.f);

	// Frame-rate independence: one long step and many short ones over
	// the same wall-clock second must land in the same place, or the
	// drones would sound different on a faster machine.
	float Stepped = 0.f;
	for (int32 Frame = 0; Frame < 100; ++Frame)
	{
		Stepped = Presenter::ComputeRotorSpeed01(
			Stepped, 1.f, 0.01f, SpoolUp, SpoolDown);
	}
	const float OneStep = Presenter::ComputeRotorSpeed01(
		0.f, 1.f, 1.f, SpoolUp, SpoolDown);
	TestTrue(TEXT("spool takes the same time at any frame rate"),
		FMath::Abs(Stepped - OneStep) < 0.01f);

	// Degenerate inputs refuse rather than produce an infinity that
	// would ride straight into the pitch multiplier.
	TestEqual(TEXT("a zero time constant snaps"),
		Presenter::ComputeRotorSpeed01(0.f, 1.f, 0.1f, 0.f, 0.f), 1.f);
	TestEqual(TEXT("a zero frame changes nothing"),
		Presenter::ComputeRotorSpeed01(0.4f, 1.f, 0.f, SpoolUp,
			SpoolDown), 0.4f);

	// Pitch tracks speed LINEARLY - a blade-pass tone is proportional
	// to RPM, and easing it would sound like a gear change.
	TestEqual(TEXT("pitch bottoms out at rest"),
		Presenter::ComputeRotorPitch(0.f, 0.55f, 1.3f), 0.55f);
	TestEqual(TEXT("pitch tops out at full speed"),
		Presenter::ComputeRotorPitch(1.f, 0.55f, 1.3f), 1.3f);
	TestTrue(TEXT("half speed is half way up the pitch range"),
		FMath::IsNearlyEqual(
			Presenter::ComputeRotorPitch(0.5f, 0.55f, 1.3f), 0.925f,
			0.001f));
	TestEqual(TEXT("pitch clamps past full speed"),
		Presenter::ComputeRotorPitch(4.f, 0.55f, 1.3f), 1.3f);

	// Volume rises faster than linearly and reaches exactly zero, so a
	// spooled-down rotor can be stopped rather than played silent.
	TestEqual(TEXT("a stopped rotor is silent"),
		Presenter::ComputeRotorVolume01(0.f), 0.f);
	TestEqual(TEXT("a full rotor is at full volume"),
		Presenter::ComputeRotorVolume01(1.f), 1.f);
	TestTrue(TEXT("a half-speed rotor is much quieter than half"),
		Presenter::ComputeRotorVolume01(0.5f) < 0.3f);
	float Previous = -1.f;
	for (int32 Step = 0; Step <= 10; ++Step)
	{
		const float Volume = Presenter::ComputeRotorVolume01(Step / 10.f);
		TestTrue(TEXT("volume never falls as speed rises"),
			Volume > Previous);
		Previous = Volume;
	}

	return true;
}

IMPLEMENT_SIMPLE_AUTOMATION_TEST(FLBSpacecraftStartingLoadoutTest,
	"LineBoss.Spacecraft.Build.ShipFactoryStartsWithOneStationAndACrew",
	EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)

bool FLBSpacecraftStartingLoadoutTest::RunTest(const FString& Parameters)
{
	(void)Parameters;
	using namespace LBSpacecraftPhase2IntegrationTestsPrivate;

	// Owner 2026-08-28: "in ship factory player should start with 1
	// assembly station and 1 of each drone and the test and departure
	// and do the full build in that station."

	// --- ONE STATION COVERS THE WHOLE FIXING SEQUENCE ---
	// This is the property the whole request rests on: with a single
	// line station the route is one step, and that step must still be
	// the start of the sequence rather than some middle stage.
	TestEqual(TEXT("a one-station line starts at the first stage"),
		static_cast<int32>(
			FLBSpacecraftProductionCatalog::StageForRouteIndex(0, 1)),
		static_cast<int32>(ELBSpacecraftStage::MaterialIntake));
	// And every longer line still starts there, so adding stations
	// splits the sequence rather than skipping the front of it.
	for (int32 Stations = 1; Stations <= 8; ++Stations)
	{
		TestEqual(FString::Printf(
			TEXT("a %d-station line starts at the first stage"), Stations),
			static_cast<int32>(
				FLBSpacecraftProductionCatalog::StageForRouteIndex(
					0, Stations)),
			static_cast<int32>(ELBSpacecraftStage::MaterialIntake));
	}
	// More stations must mean a FINER split, never a coarser one: the
	// last station of a longer line sits later in the sequence.
	const int32 OneStationLast =
		static_cast<int32>(
			FLBSpacecraftProductionCatalog::StageForRouteIndex(0, 1));
	const int32 SixStationLast =
		static_cast<int32>(
			FLBSpacecraftProductionCatalog::StageForRouteIndex(5, 6));
	TestTrue(TEXT("a longer line splits the sequence more finely"),
		SixStationLast > OneStationLast);

	// --- PLACING THE HALL SEEDS THE LOADOUT ---
	FLBSpacecraftPhase2Rig Rig = MakeSpacecraftPhase2Rig();
	FString Reason;
	// Starting land first: the game seeds a plot at BeginPlay, and
	// without it every placement is refused for want of a bay.
	if (Rig.Progression != nullptr)
	{
		FString LandReason;
		Rig.Progression->SeedStartingBays(LandReason);
	}
	FName HallId;
	if (!Rig.Build->PlaceStarterHall(HallId, Reason))
	{
		AddError(FString::Printf(TEXT("the hall did not place: %s"),
			*Reason));
		return false;
	}
	TestTrue(FString::Printf(TEXT("the loadout seeds: %s"), *Reason),
		ALBSpacecraftGameMode::SeedShipFactoryLoadout(*Rig.Build,
			*Rig.Power, *Rig.Inventory, HallId, Reason,
			Rig.Progression, Rig.Coordinator, Rig.Production,
			Rig.Track));

	int32 FittingStations = 0;
	int32 Booths = 0;
	const FLBSpacecraftStationRecord* Seeded = nullptr;
	const FLBSpacecraftStationRecord* Booth = nullptr;
	for (const FLBSpacecraftStationRecord& Record :
		Rig.Build->GetStations())
	{
		const FLBSpacecraftStationDefinition* Definition =
			ALBSpacecraftBuildAuthority::FindDefinition(
				Record.DefinitionId);
		if (Definition == nullptr || Definition->StageClassId.IsNone())
		{
			continue;
		}
		if (Definition->bProcessStation)
		{
			++Booths;
			Booth = &Record;
		}
		else
		{
			++FittingStations;
			Seeded = &Record;
		}
	}
	TestEqual(TEXT("exactly ONE fitting station is seeded"),
		FittingStations, 1);
	// The booth is REQUIRED (owner 2026-08-28), so a loadout without one
	// would hand the player a factory that cannot commission.
	TestEqual(TEXT("and exactly one spray booth"), Booths, 1);
	if (Seeded == nullptr || Booth == nullptr)
	{
		return false;
	}
	TestEqual(TEXT("the fitting station is the assembly station"),
		Seeded->DefinitionId, FName(TEXT("AssemblyRobot")));
	// Downstream: a craft painted before its parts go on would have them
	// bolted onto a wet finish.
	TestTrue(TEXT("the booth sits downstream of the fitting station"),
		Booth->WorldTransform.GetLocation().Y
			> Seeded->WorldTransform.GetLocation().Y);
	// NOTHING IS FITTED IN A PAINT BOOTH. This is the pinned trap in a
	// new costume: the booth is a line station, and a split that walked
	// "every line station" would hand it part of the fixing sequence.
	TestFalse(TEXT("the booth is not a fitting station"),
		Rig.Build->IsFittingStation(Booth->StationId));
	TestEqual(TEXT("and it is allocated no parts at all"),
		Booth->AllocatedComponents.Num(), 0);
	TestTrue(TEXT("while the fitting station carries the sequence"),
		Seeded->AllocatedComponents.Num() > 0);

	// --- ONE OF EACH DRONE ---
	const int32 Kinds = ALBSpacecraftBuildAuthority::DroneKinds().Num();
	TestEqual(TEXT("one drone of every kind is crewed"),
		Seeded->InstalledDrones, Kinds);
	for (const FLBSpacecraftDroneKind& Kind :
		ALBSpacecraftBuildAuthority::DroneKinds())
	{
		TestTrue(FString::Printf(TEXT("%s is on the crew"),
			*Kind.KindId.ToString()),
			Seeded->InstalledDroneTypes.Contains(Kind.KindId));
	}

	// --- THE TEST AND DEPARTURE ARE AVAILABLE ---
	// An uncommissioned factory refuses to route, so a player whose
	// first craft cannot leave has not seen the game.
	TArray<FLBSpacecraftRouteStep> Route;
	TestTrue(FString::Printf(TEXT("the route builds: %s"), *Reason),
		Rig.Build->BuildRoute(Route, Reason));
	// Two steps: build at the station, then through the booth.
	TestEqual(TEXT("the route is the station then the booth"),
		Route.Num(), 2);
	if (Route.Num() == 2)
	{
		TestEqual(TEXT("the craft starts its build at the station"),
			static_cast<int32>(Route[0].Stage),
			static_cast<int32>(ELBSpacecraftStage::MaterialIntake));
		TestEqual(TEXT("and the booth is the last thing before test"),
			Route[1].StationId, Booth->StationId);
	}

	// --- AND IT CAN ACTUALLY BUILD SOMETHING ---
	// Measured, not assumed: without a starting kit the first craft
	// holds at stage 0 on INSUFFICIENT RESOURCES with an empty shelf,
	// no dock to order from and no storage to order into. A loadout
	// that cannot build the thing it is for is a dead end.
	const FName Shelf(*FString::Printf(TEXT("Store.%s"),
		*Seeded->StationId.ToString()));
	for (uint8 Component = 0;
		Component <= static_cast<uint8>(ELBSpacecraftComponent::Interior);
		++Component)
	{
		const FName ItemId =
			FLBSpacecraftItemCatalogue::GetAssembledComponentItemId(
				Component);
		TestTrue(FString::Printf(
			TEXT("the starting shelf holds a %s"), *ItemId.ToString()),
			Rig.Inventory->GetQuantity(Shelf, ItemId) >= 1);
	}

	// Commissioned is not enough - the coordinator must be CONFIGURED,
	// or the player's first START answers "COORDINATOR IS NOT
	// CONFIGURED" and the opening experience is a refusal.
	TestTrue(TEXT("the coordinator is configured, not just commissioned"),
		Rig.Coordinator->IsConfigured());

	// --- NO BOOTH, NO LINE ---
	// Removing the booth must DE-COMMISSION and refuse, naming the
	// reason: every craft leaves in the customer's livery and there is
	// nowhere else to put it on.
	TestTrue(TEXT("the booth removes"),
		Rig.Build->RemoveStation(Booth->StationId, Reason));
	FString BoothlessReason;
	TestFalse(TEXT("a line with no spray booth refuses to commission"),
		Rig.Build->CommissionFactory(BoothlessReason));
	TestTrue(FString::Printf(
		TEXT("and says why: %s"), *BoothlessReason),
		BoothlessReason.Contains(TEXT("SPRAY BOOTH")));

	// --- IT IS A GIFT, NOT A PURCHASE, AND IT HAPPENS ONCE ---
	TestTrue(TEXT("a second call is refused"),
		!ALBSpacecraftGameMode::SeedShipFactoryLoadout(*Rig.Build,
			*Rig.Power, *Rig.Inventory, HallId, Reason,
			Rig.Progression, Rig.Coordinator, Rig.Production,
			Rig.Track));

	Rig.World->DestroyWorld(false);
	return true;
}

IMPLEMENT_SIMPLE_AUTOMATION_TEST(FLBSpacecraftLiveryTest,
	"LineBoss.Spacecraft.Production.CraftWearTheirCustomersColours",
	EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)

bool FLBSpacecraftLiveryTest::RunTest(const FString& Parameters)
{
	(void)Parameters;

	// Owner: colour belongs to the SHIPS - the factory stays neutral
	// cold steel and each contract paints the craft in its customer's
	// livery. The customers have carried a LiveryColour since they were
	// written; nothing ever read it.

	// Every customer must be visibly distinguishable, or "painted in
	// the customer's colours" means nothing on screen.
	const TArray<FLBSpacecraftCustomer>& Customers =
		FLBSpacecraftCustomerCatalogue::GetCustomers();
	TestTrue(TEXT("there are customers to paint for"), Customers.Num() > 1);
	for (int32 A = 0; A < Customers.Num(); ++A)
	{
		for (int32 B = A + 1; B < Customers.Num(); ++B)
		{
			const FLinearColor& One = Customers[A].LiveryColour;
			const FLinearColor& Two = Customers[B].LiveryColour;
			const float Apart = FMath::Abs(One.R - Two.R)
				+ FMath::Abs(One.G - Two.G) + FMath::Abs(One.B - Two.B);
			TestTrue(FString::Printf(
				TEXT("%s and %s are told apart by colour"),
				*Customers[A].DisplayName, *Customers[B].DisplayName),
				Apart > 0.15f);
		}
	}

	const FName Scout(TEXT("SCOUT-01"));
	auto MakeContract = [](FName ContractId, FName RecipeId,
		ELBSpacecraftContractState State, int32 Quantity,
		int32 Dispatched, double Deadline, const FLinearColor& Colour)
	{
		FLBSpacecraftContract Contract;
		Contract.ContractId = ContractId;
		Contract.RecipeId = RecipeId;
		Contract.State = State;
		Contract.Quantity = Quantity;
		Contract.DispatchedCount = Dispatched;
		Contract.DeadlineSimSeconds = Deadline;
		Contract.LiveryColour = Colour;
		return Contract;
	};

	// No contract at all: WHITE, which reads as unpainted primer rather
	// than as some other customer's colour.
	TestEqual(TEXT("with no contract the craft stays in primer"),
		FLBSpacecraftCustomerCatalogue::LiveryForRecipe({}, Scout),
		FLinearColor::White);

	// An OFFERED contract is not being built - it must not paint.
	TArray<FLBSpacecraftContract> OfferedOnly;
	OfferedOnly.Add(MakeContract(FName(TEXT("C-OFFER")), Scout,
		ELBSpacecraftContractState::Offered, 1, 0, 100.0,
		FLinearColor::Red));
	TestEqual(TEXT("an offered contract paints nothing"),
		FLBSpacecraftCustomerCatalogue::LiveryForRecipe(OfferedOnly, Scout),
		FLinearColor::White);

	// A FULFILLED contract is finished with - it must not paint either.
	TArray<FLBSpacecraftContract> Done;
	Done.Add(MakeContract(FName(TEXT("C-DONE")), Scout,
		ELBSpacecraftContractState::Accepted, 2, 2, 100.0,
		FLinearColor::Red));
	TestEqual(TEXT("a contract with nothing left to build paints nothing"),
		FLBSpacecraftCustomerCatalogue::LiveryForRecipe(Done, Scout),
		FLinearColor::White);

	// The live one paints.
	const FLinearColor Blue(0.1f, 0.3f, 0.8f, 1.f);
	TArray<FLBSpacecraftContract> Live;
	Live.Add(MakeContract(FName(TEXT("C-LIVE")), Scout,
		ELBSpacecraftContractState::Accepted, 2, 1, 500.0, Blue));
	TestEqual(TEXT("an accepted contract still owing craft paints them"),
		FLBSpacecraftCustomerCatalogue::LiveryForRecipe(Live, Scout), Blue);

	// A contract for a DIFFERENT craft must not paint this one.
	TestEqual(TEXT("another recipe's contract paints nothing here"),
		FLBSpacecraftCustomerCatalogue::LiveryForRecipe(Live,
			FName(TEXT("CARGO-01"))), FLinearColor::White);

	// TWO open contracts: the EARLIEST DEADLINE wins, because that is
	// the one the floor is working to. Order in the array must not
	// decide it, or the craft would change colour on a reorder.
	const FLinearColor Green(0.1f, 0.7f, 0.2f, 1.f);
	TArray<FLBSpacecraftContract> Two;
	Two.Add(MakeContract(FName(TEXT("C-LATE")), Scout,
		ELBSpacecraftContractState::Accepted, 1, 0, 900.0, Blue));
	Two.Add(MakeContract(FName(TEXT("C-SOON")), Scout,
		ELBSpacecraftContractState::Accepted, 1, 0, 300.0, Green));
	TestEqual(TEXT("the nearest deadline sets the colour"),
		FLBSpacecraftCustomerCatalogue::LiveryForRecipe(Two, Scout), Green);
	TArray<FLBSpacecraftContract> Reversed;
	Reversed.Add(Two[1]);
	Reversed.Add(Two[0]);
	TestEqual(TEXT("and array order does not change it"),
		FLBSpacecraftCustomerCatalogue::LiveryForRecipe(Reversed, Scout),
		Green);

	// A deadline-less contract never displaces one with a clock running.
	TArray<FLBSpacecraftContract> Mixed;
	Mixed.Add(MakeContract(FName(TEXT("C-OPEN")), Scout,
		ELBSpacecraftContractState::Accepted, 1, 0, 0.0, Blue));
	Mixed.Add(MakeContract(FName(TEXT("C-CLOCK")), Scout,
		ELBSpacecraftContractState::Accepted, 1, 0, 700.0, Green));
	TestEqual(TEXT("a running clock beats an open-ended order"),
		FLBSpacecraftCustomerCatalogue::LiveryForRecipe(Mixed, Scout),
		Green);
	return true;
}

IMPLEMENT_SIMPLE_AUTOMATION_TEST(FLBSpacecraftGearPartsTest,
	"LineBoss.Spacecraft.Production.LandingGearIsMadeOfRealParts",
	EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)

bool FLBSpacecraftGearPartsTest::RunTest(const FString& Parameters)
{
	(void)Parameters;

	// Owner 2026-08-28: "the gear parts can be wired into the parts
	// system." The undercarriage the player sees must be the
	// undercarriage the craft was built from - not decoration.

	// --- the parts exist, and the skids they replaced are gone ---
	const TCHAR* GearParts[] = {
		TEXT("Part.GearOleoStrut"), TEXT("Part.GearWheel"),
		TEXT("Part.GearBrakeUnit"), TEXT("Part.GearRetractActuator"),
		TEXT("Part.NoseGearLeg"), TEXT("Part.MainGearLeg") };
	for (const TCHAR* PartId : GearParts)
	{
		const FLBSpacecraftItemDefinition* Item =
			FLBSpacecraftItemCatalogue::FindItem(FName(PartId));
		if (Item == nullptr)
		{
			AddError(FString::Printf(
				TEXT("gear part %s is not in the catalogue"), PartId));
			continue;
		}
		TestEqual(FString::Printf(TEXT("%s is a sub-part"), PartId),
			static_cast<int32>(Item->Category),
			static_cast<int32>(ELBSpacecraftItemCategory::SubPart));
		TestTrue(FString::Printf(TEXT("%s has a name"), PartId),
			!Item->DisplayName.IsEmpty());
		// Every part must be BUYABLE, or a player who has not unlocked
		// fabrication can never fit an undercarriage at all.
		TestTrue(FString::Printf(TEXT("%s can be imported"), PartId),
			FLBSpacecraftItemCatalogue::GetItemImportPricePence(
				FName(PartId)) > 0);
	}
	TestNull(TEXT("the landing skid is superseded"),
		FLBSpacecraftItemCatalogue::FindItem(
			FName(TEXT("Part.LandingSkid"))));
	TestNull(TEXT("the skid damper is superseded"),
		FLBSpacecraftItemCatalogue::FindItem(
			FName(TEXT("Part.SkidDamper"))));

	// --- the bill of materials is a TRICYCLE: one nose, two mains ---
	const FLBSpacecraftItemRecipe* Set =
		FLBSpacecraftRecipeCatalogue::FindRecipe(
			FName(TEXT("Recipe.LandingSet")));
	if (Set == nullptr)
	{
		AddError(TEXT("the landing set has no recipe"));
		return false;
	}
	auto CountIn = [](const TArray<FLBSpacecraftItemStack>& Stacks,
		const TCHAR* ItemId)
	{
		for (const FLBSpacecraftItemStack& Stack : Stacks)
		{
			if (Stack.ItemId == FName(ItemId)) { return Stack.Count; }
		}
		return 0;
	};
	TestEqual(TEXT("the landing set takes ONE nose leg"),
		CountIn(Set->Inputs, TEXT("Part.NoseGearLeg")), 1);
	TestEqual(TEXT("the landing set takes TWO main legs"),
		CountIn(Set->Inputs, TEXT("Part.MainGearLeg")), 2);

	// --- a nose wheel does not brake, and that is why there are two
	// leg types rather than one repeated three times ---
	const FLBSpacecraftItemRecipe* Nose =
		FLBSpacecraftRecipeCatalogue::FindRecipe(
			FName(TEXT("Recipe.NoseGearLeg")));
	const FLBSpacecraftItemRecipe* Main =
		FLBSpacecraftRecipeCatalogue::FindRecipe(
			FName(TEXT("Recipe.MainGearLeg")));
	if (Nose == nullptr || Main == nullptr)
	{
		AddError(TEXT("a gear leg has no recipe"));
		return false;
	}
	TestEqual(TEXT("the nose leg carries no brake"),
		CountIn(Nose->Inputs, TEXT("Part.GearBrakeUnit")), 0);
	TestEqual(TEXT("a main leg carries a brake"),
		CountIn(Main->Inputs, TEXT("Part.GearBrakeUnit")), 1);
	// Every leg rolls and every leg retracts.
	TestEqual(TEXT("the nose leg has a wheel"),
		CountIn(Nose->Inputs, TEXT("Part.GearWheel")), 1);
	TestEqual(TEXT("a main leg has a wheel"),
		CountIn(Main->Inputs, TEXT("Part.GearWheel")), 1);
	TestEqual(TEXT("the nose leg retracts"),
		CountIn(Nose->Inputs, TEXT("Part.GearRetractActuator")), 1);
	TestEqual(TEXT("a main leg retracts"),
		CountIn(Main->Inputs, TEXT("Part.GearRetractActuator")), 1);

	// --- and the whole chain still validates: every gear part has a
	// recipe that makes it, or the table is broken, not the player ---
	FString Reason;
	TestTrue(FString::Printf(
		TEXT("the item table still validates: %s"), *Reason),
		FLBSpacecraftItemCatalogue::ValidateItemTable(Reason));
	TestTrue(FString::Printf(
		TEXT("the recipe chain is still complete: %s"), *Reason),
		FLBSpacecraftRecipeCatalogue::ValidateRecipeTable(Reason));
	return true;
}

IMPLEMENT_SIMPLE_AUTOMATION_TEST(FLBSpacecraftStationLiftTest,
	"LineBoss.Spacecraft.Presentation.TheStationLiftsTheShipToBeWorkedOn",
	EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)

bool FLBSpacecraftStationLiftTest::RunTest(const FString& Parameters)
{
	(void)Parameters;

	// Owner 2026-08-28: "the station will have to lift the ship up ...
	// to be worked on." The craft arrives on its landing gear, the
	// four-post lift raises it so the crew can get underneath, and it
	// comes down before it moves on.
	const float Raised = 340.f;
	const float Rise = 0.12f;
	auto Lift = [Raised, Rise](float Progress)
	{
		return ALBSpacecraftWIPPresentationActor::ComputeStationLiftCm(
			Progress, Raised, Rise);
	};

	// DOWN on arrival and DOWN on departure - a craft that left still
	// jacked up would be dragged off its own lift.
	TestTrue(TEXT("the craft arrives down on its gear"),
		FMath::IsNearlyZero(Lift(0.f)));
	TestTrue(TEXT("and is back down before it moves on"),
		FMath::IsNearlyZero(Lift(1.f)));

	// UP for the middle of the stop, which is when the work happens.
	TestTrue(TEXT("it is fully up while being worked on"),
		FMath::IsNearlyEqual(Lift(0.5f), Raised));
	TestTrue(TEXT("still up at the end of the rise"),
		FMath::IsNearlyEqual(Lift(Rise), Raised));

	// The rise is real travel, not a snap: partway up is partway up.
	const float Halfway = Lift(Rise * 0.5f);
	TestTrue(TEXT("the lift travels rather than snapping"),
		Halfway > 1.f && Halfway < Raised - 1.f);

	// Monotonic up then monotonic down - a lift that bobbed mid-stop
	// would read as a fault.
	float Previous = -1.f;
	for (int32 Step = 0; Step <= 12; ++Step)
	{
		const float Now = Lift(Step * Rise / 12.f);
		TestTrue(TEXT("the lift only rises on the way up"),
			Now >= Previous - KINDA_SMALL_NUMBER);
		Previous = Now;
	}
	// Forwards through the descent, not backwards through it: walking
	// progress from 1.0 down to (1 - Rise) is walking back in TIME, and
	// of course the lift rises when you play it in reverse.
	Previous = Raised + 1.f;
	for (int32 Step = 0; Step <= 12; ++Step)
	{
		const float Now = Lift(1.f - Rise + Step * Rise / 12.f);
		TestTrue(TEXT("the lift only falls on the way down"),
			Now <= Previous + KINDA_SMALL_NUMBER);
		Previous = Now;
	}

	// Out-of-range progress is clamped, never extrapolated into a
	// craft sinking through the floor or flying off the lift.
	TestTrue(TEXT("progress below zero is clamped"),
		FMath::IsNearlyZero(Lift(-5.f)));
	TestTrue(TEXT("progress beyond one is clamped"),
		FMath::IsNearlyZero(Lift(5.f)));
	return true;
}

IMPLEMENT_SIMPLE_AUTOMATION_TEST(FLBSpacecraftLandingGearTest,
	"LineBoss.Spacecraft.Presentation.LandingGearIsDownThenFoldsAway",
	EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)

bool FLBSpacecraftLandingGearTest::RunTest(const FString& Parameters)
{
	(void)Parameters;

	// Owner 2026-08-28: "we also need tricycle landing gear ... also
	// needs to be on ship but disappears when it takes off at the end."

	// --- the geometry is TRICYCLE, derived from the hull ---
	// A Scout-shaped hull: 14.0 x 7.46 x 3.87 m, grounded at Z = 0, so
	// its bounds origin sits half a hull-height up.
	const FVector Extent(700.f, 373.f, 193.5f);
	const FVector Origin(0.f, 0.f, 193.5f);
	FVector Nose;
	FVector Left;
	FVector Right;
	ALBSpacecraftWIPPresentationActor::ComputeTricycleGearAnchorsCm(
		Origin, Extent, Nose, Left, Right);

	TestTrue(TEXT("the nose leg is forward of both mains"),
		Nose.X > Left.X && Nose.X > Right.X);
	TestTrue(TEXT("the nose leg is on the centreline"),
		FMath::IsNearlyEqual(Nose.Y, Origin.Y, 0.01f));
	TestTrue(TEXT("the mains straddle the centreline"),
		Left.Y < Origin.Y && Right.Y > Origin.Y);
	TestTrue(TEXT("the mains are symmetric"),
		FMath::IsNearlyEqual(Left.Y - Origin.Y, Origin.Y - Right.Y, 0.01f)
			&& FMath::IsNearlyEqual(Left.X, Right.X, 0.01f));
	// The mains carry the weight, so they must sit BEHIND the hull
	// centre - forward of it and the craft tips onto its tail.
	TestTrue(TEXT("the mains sit aft of the hull centre"),
		Left.X < Origin.X);
	// Nothing may stick out past the hull, or the gear would clip the
	// station rig and read as broken.
	TestTrue(TEXT("every leg stays within the hull footprint"),
		Nose.X <= Origin.X + Extent.X && Left.X >= Origin.X - Extent.X
			&& FMath::Abs(Left.Y - Origin.Y) < Extent.Y
			&& FMath::Abs(Right.Y - Origin.Y) < Extent.Y);
	// All three hang from the belly plane, which for a mesh grounded at
	// Z = 0 is Z = 0.
	TestTrue(TEXT("all three legs hang from the belly plane"),
		FMath::IsNearlyZero(Nose.Z) && FMath::IsNearlyZero(Left.Z)
			&& FMath::IsNearlyZero(Right.Z));

	// --- it scales with the craft, because later tiers are bigger ---
	// (owner: the Scout is the SMALLEST craft.) A Cargo-01 at 1.5x must
	// get a wider track and a longer wheelbase with no new code.
	FVector BigNose;
	FVector BigLeft;
	FVector BigRight;
	ALBSpacecraftWIPPresentationActor::ComputeTricycleGearAnchorsCm(
		Origin * 1.5f, Extent * 1.5f, BigNose, BigLeft, BigRight);
	TestTrue(TEXT("a bigger craft gets a longer wheelbase"),
		BigNose.X - BigLeft.X > Nose.X - Left.X);
	TestTrue(TEXT("a bigger craft gets a wider track"),
		BigRight.Y - BigLeft.Y > Right.Y - Left.Y);

	// --- the retraction: down for the taxi, away on the sprint ---
	const float Chicane = 2.2f;
	const float Retract = 0.9f;
	TestTrue(TEXT("gear is down as the craft leaves the line"),
		FMath::IsNearlyZero(
			ALBSpacecraftWIPPresentationActor::ComputeGearRetraction01(
				0.f, Chicane, Retract)));
	TestTrue(TEXT("gear is still down all through the chicane taxi"),
		FMath::IsNearlyZero(
			ALBSpacecraftWIPPresentationActor::ComputeGearRetraction01(
				Chicane, Chicane, Retract)));
	const float Folding =
		ALBSpacecraftWIPPresentationActor::ComputeGearRetraction01(
			Chicane + Retract * 0.5f, Chicane, Retract);
	TestTrue(TEXT("gear is part way up mid-sprint"),
		Folding > 0.1f && Folding < 0.9f);
	TestTrue(TEXT("gear is fully away once the fold completes"),
		FMath::IsNearlyEqual(
			ALBSpacecraftWIPPresentationActor::ComputeGearRetraction01(
				Chicane + Retract, Chicane, Retract), 1.f));
	TestTrue(TEXT("and stays away for the rest of the flight"),
		FMath::IsNearlyEqual(
			ALBSpacecraftWIPPresentationActor::ComputeGearRetraction01(
				Chicane + Retract * 40.f, Chicane, Retract), 1.f));
	// Monotonic: a leg that ever came back down mid-flight would read
	// as a fault rather than a retraction.
	float Previous = -1.f;
	for (int32 Step = 0; Step <= 40; ++Step)
	{
		const float Now =
			ALBSpacecraftWIPPresentationActor::ComputeGearRetraction01(
				Step * 0.2f, Chicane, Retract);
		TestTrue(TEXT("the gear never drops back down"), Now >= Previous);
		Previous = Now;
	}
	return true;
}

IMPLEMENT_SIMPLE_AUTOMATION_TEST(FLBSpacecraftGroundCrewTest,
	"LineBoss.Spacecraft.Presentation.GroundCrewWorksOnTheFloor",
	EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)

bool FLBSpacecraftGroundCrewTest::RunTest(const FString& Parameters)
{
	(void)Parameters;

	// Owner 2026-08-28: "we also need 3 ground drones ... for working
	// underneath the ship, a lifter, assembly and sprayer." The three
	// kinds must be hireable, and must be marked as GROUND crew - the
	// flag is what stops the presenter flying them.
	const TCHAR* GroundKinds[] = {
		TEXT("GroundLifter"), TEXT("GroundAssembly"),
		TEXT("GroundSprayer") };
	for (const TCHAR* KindId : GroundKinds)
	{
		const FLBSpacecraftDroneKind* Kind =
			ALBSpacecraftBuildAuthority::FindDroneKind(FName(KindId));
		if (Kind == nullptr)
		{
			AddError(FString::Printf(
				TEXT("ground drone kind %s is not hireable"), KindId));
			continue;
		}
		TestTrue(FString::Printf(TEXT("%s is ground crew"), KindId),
			Kind->bGroundCrew);
		TestTrue(FString::Printf(TEXT("%s costs something"), KindId),
			Kind->CostPence > 0);
	}
	// The fliers must NOT be ground crew, or every drone would be
	// pinned to the floor.
	for (const TCHAR* KindId : { TEXT("Assembly"), TEXT("Winch"),
		TEXT("Spray"), TEXT("CargoLift") })
	{
		const FLBSpacecraftDroneKind* Kind =
			ALBSpacecraftBuildAuthority::FindDroneKind(FName(KindId));
		if (Kind != nullptr)
		{
			TestFalse(FString::Printf(TEXT("%s still flies"), KindId),
				Kind->bGroundCrew);
		}
	}

	// The drive path: on the floor at every moment of the run, working
	// under the craft rather than orbiting it, and moving with time.
	float MinAlong = TNumericLimits<float>::Max();
	float MaxAlong = -TNumericLimits<float>::Max();
	for (int32 Step = 0; Step < 64; ++Step)
	{
		const float Clock = Step * 0.4f;
		const FVector Where = ALBSpacecraftWIPPresentationActor::
			ComputeGroundDroneWorkOffsetCm(Clock, 0, 600.f, 260.f);
		TestTrue(TEXT("a wheeled drone never leaves the floor"),
			FMath::IsNearlyZero(Where.Z));
		MinAlong = FMath::Min(MinAlong, Where.X);
		MaxAlong = FMath::Max(MaxAlong, Where.X);
	}
	TestTrue(TEXT("the ground drone shuttles the length of the belly"),
		MaxAlong - MinAlong > 900.f);

	// Two ground drones keep to opposite lanes, so they do not drive
	// through one another under the craft.
	const FVector LaneA = ALBSpacecraftWIPPresentationActor::
		ComputeGroundDroneWorkOffsetCm(1.f, 0, 600.f, 260.f);
	const FVector LaneB = ALBSpacecraftWIPPresentationActor::
		ComputeGroundDroneWorkOffsetCm(1.f, 1, 600.f, 260.f);
	TestTrue(TEXT("ground drones keep to their own lanes"),
		FMath::Abs(LaneA.Y - LaneB.Y) > 400.f);

	// Facing follows the run: nose-first out, reversed on the way back,
	// and it must actually change over a cycle.
	const float YawOut =
		ALBSpacecraftWIPPresentationActor::ComputeGroundDroneYawDeg(
			0.f, 0);
	const float YawBack =
		ALBSpacecraftWIPPresentationActor::ComputeGroundDroneYawDeg(
			6.f, 0);
	TestTrue(TEXT("the drone drives out nose-first"),
		FMath::IsNearlyZero(YawOut));
	TestTrue(TEXT("and reverses its facing on the way back"),
		FMath::IsNearlyEqual(YawBack, 180.f));

	// The crew signature: hiring a different kind into a slot must
	// produce a different signature, or the floor would keep showing
	// the crew the player had before they chose.
	const FString Pair = ALBSpacecraftWIPPresentationActor::
		ComputeDroneCrewRevision({ FName(TEXT("Assembly")),
			FName(TEXT("GroundLifter")) }, 2);
	const FString Swapped = ALBSpacecraftWIPPresentationActor::
		ComputeDroneCrewRevision({ FName(TEXT("Assembly")),
			FName(TEXT("GroundSprayer")) }, 2);
	const FString Same = ALBSpacecraftWIPPresentationActor::
		ComputeDroneCrewRevision({ FName(TEXT("Assembly")),
			FName(TEXT("GroundLifter")) }, 2);
	TestNotEqual(TEXT("swapping a hired kind rebuilds the crew"),
		Pair, Swapped);
	TestEqual(TEXT("an unchanged crew does not churn"), Pair, Same);
	TestNotEqual(TEXT("a legacy crew with no kinds still grows"),
		ALBSpacecraftWIPPresentationActor::ComputeDroneCrewRevision(
			{}, 1),
		ALBSpacecraftWIPPresentationActor::ComputeDroneCrewRevision(
			{}, 2));
	return true;
}

IMPLEMENT_SIMPLE_AUTOMATION_TEST(FLBSpacecraftDroneTest,
	"LineBoss.Spacecraft.Presentation.FittingDronesFlyOnlyWhileWorking",
	EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)

bool FLBSpacecraftDroneTest::RunTest(const FString& Parameters)
{
	(void)Parameters;
	using namespace LBSpacecraftPhase2IntegrationTestsPrivate;

	// Pure orbit maths: the two drones fly half a turn apart, the orbit
	// breathes (radius changes), and the bob moves them vertically.
	const FVector D0 =
		ALBSpacecraftWIPPresentationActor::ComputeDroneWorkOffsetCm(
			1.f, 0, 600.f, 420.f);
	const FVector D1 =
		ALBSpacecraftWIPPresentationActor::ComputeDroneWorkOffsetCm(
			1.f, 1, 600.f, 420.f);
	const FVector D0Later =
		ALBSpacecraftWIPPresentationActor::ComputeDroneWorkOffsetCm(
			2.5f, 0, 600.f, 420.f);
	TestTrue(TEXT("the two drones fly apart"),
		FVector::Dist(D0, D1) > 300.f);
	TestTrue(TEXT("a drone moves along its orbit"),
		FVector::Dist(D0, D0Later) > 100.f);
	TestTrue(TEXT("drones fly at hover height"),
		D0.Z > 300.f && D1.Z > 300.f);

	// Pure fan-pod tilt: level at rest, leaning into the motion, and
	// clamped at speed (never past the max tilt).
	const FRotator Rest =
		ALBSpacecraftWIPPresentationActor::ComputeFanTiltDeg(
			FVector::ZeroVector, 18.f);
	TestTrue(TEXT("pods are level at rest"),
		Rest.IsNearlyZero());
	const FRotator Forward =
		ALBSpacecraftWIPPresentationActor::ComputeFanTiltDeg(
			FVector(300.f, 0.f, 0.f), 18.f);
	TestTrue(TEXT("forward flight pitches the pods nose-down"),
		Forward.Pitch < -1.f && FMath::IsNearlyZero(Forward.Roll));
	const FRotator Fast =
		ALBSpacecraftWIPPresentationActor::ComputeFanTiltDeg(
			FVector(5000.f, 5000.f, 0.f), 18.f);
	TestTrue(TEXT("tilt clamps at the maximum"),
		FMath::Abs(Fast.Pitch) <= 18.01f
			&& FMath::Abs(Fast.Roll) <= 18.01f);

	// Pure conveyor chevron maths: stays on the belt, spaces the train,
	// and advances with the clock.
	const float ChevA =
		ALBSpacecraftWIPPresentationActor::ComputeConveyorChevronOffsetCm(
			1.f, 250.f, 3000.f, 0, 400.f);
	const float ChevB =
		ALBSpacecraftWIPPresentationActor::ComputeConveyorChevronOffsetCm(
			1.f, 250.f, 3000.f, 1, 400.f);
	const float ChevLater =
		ALBSpacecraftWIPPresentationActor::ComputeConveyorChevronOffsetCm(
			2.f, 250.f, 3000.f, 0, 400.f);
	TestTrue(TEXT("chevron stays on the belt"),
		ChevA >= 0.f && ChevA < 3000.f);
	TestEqual(TEXT("train spacing holds"), ChevB - ChevA, 400.f);
	TestEqual(TEXT("the train advances with the clock"),
		ChevLater - ChevA, 250.f);

	// Launch camera pose: the chicane chase and the sprint crane are
	// distinct shots, and both keep eyes on the ship.
	const FVector Ship(1000.f, -5000.f, 150.f);
	FVector ChaseCam, ChaseLook, CraneCam, CraneLook;
	ALBSpacecraftWIPPresentationActor::ComputeLaunchCameraPose(
		0.5f, Ship, 2.2f, ChaseCam, ChaseLook);
	ALBSpacecraftWIPPresentationActor::ComputeLaunchCameraPose(
		6.f, Ship, 2.2f, CraneCam, CraneLook);
	TestTrue(TEXT("chase and crane are different shots"),
		FVector::Dist(ChaseCam, CraneCam) > 1000.f);
	TestTrue(TEXT("the chase flies low"), ChaseCam.Z < CraneCam.Z);
	TestTrue(TEXT("both shots look at the ship"),
		FVector::Dist(ChaseLook, Ship) < 200.f
			&& FVector::Dist(CraneLook, Ship) < 200.f);

	// RCS stabilisation: the dropped corner fires hardest, the risen
	// corner idles near the station-keeping whisper.
	float WobblePitch = 0.f;
	float WobbleRoll = 0.f;
	ALBSpacecraftWIPPresentationActor::ComputeHoverWobbleDeg(
		1.7f, WobblePitch, WobbleRoll);
	TestTrue(TEXT("wobble stays subtle"),
		FMath::Abs(WobblePitch) < 3.f && FMath::Abs(WobbleRoll) < 3.f);
	const float NoseDownAft =
		ALBSpacecraftWIPPresentationActor::ComputeRCSCorrection01(
			2.f, 0.f, 2); // -X corner with the nose UP: dropped
	const float NoseDownFore =
		ALBSpacecraftWIPPresentationActor::ComputeRCSCorrection01(
			2.f, 0.f, 0); // +X corner: risen
	TestTrue(TEXT("the dropped corner fires hardest"),
		NoseDownAft > NoseDownFore + 0.3f);
	TestTrue(TEXT("corrections stay in range"),
		NoseDownAft <= 1.f && NoseDownFore >= 0.05f);

	FLBSpacecraftPhase2Rig Rig = MakeSpacecraftPhase2Rig();
	FString Reason;
	FName PlantId;
	FName MillId;
	FName PowerHallId;
	TestTrue(TEXT("power hall places"),
		ALBSpacecraftGameMode::PlaceStationPowered(*Rig.Build, *Rig.Power, *Rig.Inventory, FName(TEXT("PowerStation")), FTransform(FRotator::ZeroRotator, FVector(-16000.f, 0.f, 0.f)), PowerHallId, Reason));
	// The generator lives INSIDE its hall (owner
	// 2026-08-26): free placement is refused now.
	TestTrue(TEXT("plant installs in the hall"),
		ALBSpacecraftGameMode::InstallInSlotPowered(*Rig.Build, *Rig.Power, PowerHallId,
			FName(TEXT("PowerPlant")), PlantId, Reason));
	TestTrue(TEXT("points bank"), Rig.Research->AddPoints(10, Reason));
	TestTrue(TEXT("T1 unlocks"),
		Rig.Research->UnlockNode(FName(TEXT("Research.Mfg.T1")), Reason));
	// Parts machines live in the sub-assembly hall (owner
	// 2026-08-26), so the mill is installed, not placed.
	FName MillHallId;
	TestTrue(TEXT("a sub-assembly hall places"),
		ALBSpacecraftGameMode::PlaceStationPowered(*Rig.Build, *Rig.Power,
			*Rig.Inventory, FName(TEXT("SubAssemblyHall")),
			FTransform(FRotator::ZeroRotator, FVector(16000.f, 0.f, 0.f)),
			MillHallId, Reason));
	TestTrue(TEXT("mill installs in the hall"),
		ALBSpacecraftGameMode::InstallInSlotPowered(*Rig.Build, *Rig.Power,
			MillHallId, FName(TEXT("RollingMill")), MillId, Reason));

	ALBSpacecraftWIPPresentationActor* Presenter =
		Rig.World->SpawnActor<ALBSpacecraftWIPPresentationActor>();
	Presenter->BindAuthorities(Rig.Build, Rig.Coordinator, Rig.Production);
	Presenter->BindCrafting(Rig.Crafting);
	Presenter->Tick(0.1f);

	// Owner decision 2026-08-25 refined 2026-08-26: production
	// stations host fitting drones, POWER runs unmanned - so only the
	// mill is crewed here.
	TestEqual(TEXT("only the production station grew drones"),
		Presenter->GetDroneStationCount(), 1);
	TestEqual(TEXT("idle drones sit on their docks"),
		Presenter->GetDroneWorkAlpha(MillId), 0.f);

	// A working mill sends its drones out; an idled one recalls them.
	TestTrue(TEXT("mill selects plate"),
		ALBSpacecraftGameMode::SelectStationRecipe(*Rig.Build,
			*Rig.Crafting, *Rig.Research, MillId,
			FName(TEXT("Recipe.PlateStock")), Reason));
	for (int32 Tick = 0; Tick < 20; ++Tick)
	{
		Presenter->Tick(0.1f);
	}
	TestTrue(TEXT("working drones are fully out"),
		Presenter->GetDroneWorkAlpha(MillId) > 0.99f);
	// Rotors, live: they spool UP as the drone goes to work.
	const float FlyingRotors = Presenter->GetDroneRotorSpeed01(MillId, 0);
	TestTrue(TEXT("working drones have their rotors up"),
		FlyingRotors > 0.7f);
	// Each drone gets its own voice - but only when the placeholder loop
	// is actually present. Content is gitignored, so asserting the count
	// unconditionally would fail on a content-less checkout for a reason
	// that has nothing to do with the code. Asserting it CONDITIONALLY
	// still catches the wiring being wrong, which is the point; a bare
	// "expect 0 after removal" would pass even if no voice ever existed.
	const bool bRotorLoopPresent =
		Presenter->RotorLoopSound.LoadSynchronous() != nullptr;
	if (bRotorLoopPresent)
	{
		TestEqual(TEXT("every drone gets its own rotor voice"),
			Presenter->GetRotorAudioCount(), 2);
	}
	else
	{
		AddInfo(TEXT("rotor loop absent: voices skipped, rotors silent"));
	}
	TestTrue(TEXT("selection clears"),
		Rig.Crafting->ClearSelection(MillId, Reason));
	for (int32 Tick = 0; Tick < 20; ++Tick)
	{
		Presenter->Tick(0.1f);
	}
	TestTrue(TEXT("idled drones land back on their docks"),
		Presenter->GetDroneWorkAlpha(MillId) < 0.01f);
	// ...and COAST down. Two seconds after being recalled the rotors
	// are well below flying speed but have not stopped dead, which is
	// the asymmetry the whole model exists for: nothing brakes a rotor.
	const float LandedRotors = Presenter->GetDroneRotorSpeed01(MillId, 0);
	TestTrue(TEXT("landed rotors have wound down"),
		LandedRotors < FlyingRotors * 0.8f);
	TestTrue(TEXT("landed rotors coast rather than stopping dead"),
		LandedRotors > 0.f);

	// Removal takes drones and docks with the station; nothing is left
	// crewed because power infrastructure never had any.
	TestTrue(TEXT("mill removes"),
		ALBSpacecraftGameMode::RemoveStationPowered(*Rig.Build, *Rig.Power,
			*Rig.Inventory, Rig.Crafting, MillId, Reason));
	Presenter->Tick(0.1f);
	TestEqual(TEXT("no crewed station remains"),
		Presenter->GetDroneStationCount(), 0);
	// A removed station leaves no rotors behind. Left un-torn-down the
	// audio component would outlive its drone - attached children are
	// detached, not destroyed - and buzz over an empty slab.
	TestEqual(TEXT("removal leaves no rotors turning"),
		Presenter->GetDroneRotorSpeed01(MillId, 0), 0.f);
	TestEqual(TEXT("removal leaves no rotor voices"),
		Presenter->GetRotorAudioCount(), 0);

	Rig.World->DestroyWorld(false);
	return true;
}

IMPLEMENT_SIMPLE_AUTOMATION_TEST(FLBSpacecraftMoneyLoopTest,
	"LineBoss.Spacecraft.Phase2.PlacementChargesCashFailClosed",
	EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)

bool FLBSpacecraftMoneyLoopTest::RunTest(const FString& Parameters)
{
	(void)Parameters;
	using namespace LBSpacecraftPhase2IntegrationTestsPrivate;
	FLBSpacecraftPhase2Rig Rig = MakeSpacecraftPhase2Rig();
	FString Reason;
	FName PlantId;

	const int64 Capital = Rig.Production->GetCashPence();
	TestEqual(TEXT("the provisional starting capital is banked"),
		Capital, ALBSpacecraftProductionAuthority::
			ProvisionalStartingCapitalPence);

	// A ledger-backed placement charges the catalogue price.
	FName PowerHallId;
	TestTrue(TEXT("power hall places"),
		ALBSpacecraftGameMode::PlaceStationPowered(*Rig.Build, *Rig.Power, *Rig.Inventory, FName(TEXT("PowerStation")), FTransform(FRotator::ZeroRotator, FVector(-16000.f, 0.f, 0.f)), PowerHallId, Reason, Rig.Production));
	// The generator lives INSIDE its hall (owner
	// 2026-08-26): free placement is refused now.
	TestTrue(TEXT("plant installs in the hall"),
		ALBSpacecraftGameMode::InstallInSlotPowered(*Rig.Build, *Rig.Power, PowerHallId,
			FName(TEXT("PowerPlant")), PlantId, Reason, Rig.Production));
	// Both prices leave: the hall (20,000,000) and the generator
	// installed in its slot (15,000,000).
	TestEqual(TEXT("hall and plant prices left the account"),
		Rig.Production->GetCashPence(), Capital - 35000000);

	// A refused placement (research lock) refunds WHOLE.
	FName MillId;
	TestFalse(TEXT("a locked mill still refuses"),
		ALBSpacecraftGameMode::PlaceStationPowered(*Rig.Build, *Rig.Power,
			*Rig.Inventory, FName(TEXT("RollingMill")),
			FTransform(FRotator::ZeroRotator, FVector(4000.f, 0.f, 0.f)),
			MillId, Reason, Rig.Production));
	TestEqual(TEXT("the refused placement cost nothing"),
		Rig.Production->GetCashPence(), Capital - 35000000);

	// Too poor: the charge itself refuses before anything happens.
	FString Drain;
	TestTrue(TEXT("drain the account"),
		Rig.Production->SpendPence(Rig.Production->GetCashPence() - 100,
			Drain));
	FName RackId;
	TestFalse(TEXT("an unaffordable rack refuses whole"),
		ALBSpacecraftGameMode::PlaceStationPowered(*Rig.Build, *Rig.Power,
			*Rig.Inventory, FName(TEXT("StorageRack")),
			FTransform(FRotator::ZeroRotator, FVector(0.f, 4000.f, 0.f)),
			RackId, Reason, Rig.Production));
	TestTrue(TEXT("the refusal names the shortfall"),
		Reason.Contains(TEXT("INSUFFICIENT FUNDS")));
	// 2 = the power hall and the generator inside it; the refused
	// rack added nothing.
	TestEqual(TEXT("no rack was placed"),
		// 3 = the ship factory, the power hall and its generator.
		Rig.Build->GetStations().Num(), 3);

	// Removal refunds the provisional half.
	TestTrue(TEXT("plant removes"),
		ALBSpacecraftGameMode::RemoveStationPowered(*Rig.Build, *Rig.Power,
			*Rig.Inventory, Rig.Crafting, PlantId, Reason,
			Rig.Production));
	TestEqual(TEXT("half the plant price came back"),
		Rig.Production->GetCashPence(), (int64)100 + 7500000);

	Rig.World->DestroyWorld(false);
	return true;
}

IMPLEMENT_SIMPLE_AUTOMATION_TEST(FLBSpacecraftReputationTest,
	"LineBoss.Spacecraft.Phase2.ReputationTiersGateTheContractLadder",
	EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)

bool FLBSpacecraftReputationTest::RunTest(const FString& Parameters)
{
	(void)Parameters;
	using namespace LBSpacecraftPhase2IntegrationTestsPrivate;

	// Pure tier thresholds (PROVISIONAL 0/10/25/50).
	TestEqual(TEXT("0 points is tier 1"),
		ALBSpacecraftReputationAuthority::TierForPoints(0), 1);
	TestEqual(TEXT("10 points is tier 2"),
		ALBSpacecraftReputationAuthority::TierForPoints(10), 2);
	TestEqual(TEXT("49 points is tier 3"),
		ALBSpacecraftReputationAuthority::TierForPoints(49), 3);
	TestEqual(TEXT("50 points is tier 4"),
		ALBSpacecraftReputationAuthority::TierForPoints(50), 4);

	FLBSpacecraftPhase2Rig Rig = MakeSpacecraftPhase2Rig();
	FString Reason;

	// A tier-1 name cannot take a Cargo contract; the refusal explains.
	TestFalse(TEXT("Cargo refuses at tier 1"),
		ALBSpacecraftGameMode::StartRecipeContract(*Rig.Production,
			FName(TEXT("CARGO-01")), 1, Reason, Rig.Reputation));
	TestTrue(TEXT("the refusal names the tier and the remedy"),
		Reason.Contains(TEXT("REPUTATION TIER 2 REQUIRED"))
		&& Reason.Contains(TEXT("DELIVER CONTRACTS")));
	// Scout is a tier-1 recipe: it accepts.
	TestTrue(TEXT("Scout accepts at tier 1"),
		ALBSpacecraftGameMode::StartRecipeContract(*Rig.Production,
			FName(TEXT("SCOUT-01")), 1, Reason, Rig.Reputation));

	// Completing the contract credits reputation EXACTLY once.
	TestTrue(TEXT("line commissions"),
		ALBSpacecraftGameMode::SetupCanonicalLine(*Rig.Build, Reason));
	TestTrue(TEXT("coordinator configures"),
		Rig.Coordinator->ConfigureFromAuthorities(Rig.Build, Rig.Production,
			Reason));
	int32 Guard = 0;
	while (Rig.Production->GetRevenuePence() < 15000000 && Guard++ < 400)
	{
		TestTrue(TEXT("tick runs"),
			Rig.Coordinator->TickProduction(5.0, Reason));
	}
	Rig.Reputation->SyncFromLedger(Rig.Production);
	TestEqual(TEXT("one completed contract pays two points"),
		Rig.Reputation->GetPoints(), 2);
	Rig.Reputation->SyncFromLedger(Rig.Production);
	TestEqual(TEXT("resyncing never double-credits"),
		Rig.Reputation->GetPoints(), 2);

	// Snapshot: a double-credited contract is refused before mutation.
	FLBSpacecraftReputationSnapshot Snapshot =
		Rig.Reputation->CaptureSnapshot();
	TestTrue(TEXT("live snapshot validates"),
		ALBSpacecraftReputationAuthority::ValidateSnapshot(Snapshot,
			Reason));
	// Credit is tracked per DELIVERY now, so that is where a corrupt
	// double entry has to be caught.
	FLBSpacecraftReputationSnapshot Doubled = Snapshot;
	TestTrue(TEXT("the snapshot carries delivery credit to corrupt"),
		Doubled.DeliveryCredits.Num() > 0);
	if (Doubled.DeliveryCredits.Num() > 0)
	{
		// Copy first: adding an element that lives INSIDE the array
		// aliases it, and TArray asserts on exactly that.
		const FLBSpacecraftDeliveryCredit First = Doubled.DeliveryCredits[0];
		Doubled.DeliveryCredits.Add(First);
	}
	TestFalse(TEXT("a double credit refuses to restore"),
		Rig.Reputation->RestoreSnapshot(Doubled, Reason));

	Rig.World->DestroyWorld(false);
	return true;
}

IMPLEMENT_SIMPLE_AUTOMATION_TEST(FLBSpacecraftResourceOrderTest,
	"LineBoss.Spacecraft.Phase2.ResourceOrdersChargeCashAndArrive",
	EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)

bool FLBSpacecraftResourceOrderTest::RunTest(const FString& Parameters)
{
	(void)Parameters;
	using namespace LBSpacecraftPhase2IntegrationTestsPrivate;
	FLBSpacecraftPhase2Rig Rig = MakeSpacecraftPhase2Rig();
	FString Reason;
	TestTrue(TEXT("floor store registers"),
		Rig.Inventory->RegisterStore(FName(TEXT("Store.Floor")), 500,
			Reason));
	const int64 Capital = Rig.Production->GetCashPence();

	// An order charges cash up front (10 iron at 4,000 pence each).
	TestTrue(TEXT("iron order places"),
		ALBSpacecraftGameMode::PlaceResourceOrder(*Rig.Inventory,
			*Rig.Production, FName(TEXT("Raw.IronOre")), 10,
			FName(TEXT("Store.Floor")), Reason));
	TestEqual(TEXT("the order price left the account"),
		Rig.Production->GetCashPence(), Capital - 40000);
	TestEqual(TEXT("nothing arrives before the lead time"),
		Rig.Inventory->GetQuantity(FName(TEXT("Store.Floor")),
			FName(TEXT("Raw.IronOre"))), 0);

	// Refined goods cannot be bought; a broken order costs nothing.
	TestFalse(TEXT("steel is not purchasable"),
		ALBSpacecraftGameMode::PlaceResourceOrder(*Rig.Inventory,
			*Rig.Production, FName(TEXT("Proc.Steel")), 10,
			FName(TEXT("Store.Floor")), Reason));
	TestFalse(TEXT("an unknown store refunds whole"),
		ALBSpacecraftGameMode::PlaceResourceOrder(*Rig.Inventory,
			*Rig.Production, FName(TEXT("Raw.IronOre")), 10,
			FName(TEXT("Store.Nowhere")), Reason));
	TestEqual(TEXT("failed orders cost nothing"),
		Rig.Production->GetCashPence(), Capital - 40000);

	// Lead time (30 + 2 s for 10 units): the delivery lands on the clock.
	Rig.Inventory->TickOrders(20.0);
	TestEqual(TEXT("still in transit at 20 s"),
		Rig.Inventory->GetQuantity(FName(TEXT("Store.Floor")),
			FName(TEXT("Raw.IronOre"))), 0);
	Rig.Inventory->TickOrders(15.0);
	TestEqual(TEXT("the iron arrived at 35 s"),
		Rig.Inventory->GetQuantity(FName(TEXT("Store.Floor")),
			FName(TEXT("Raw.IronOre"))), 10);
	TestEqual(TEXT("the order book is clear"),
		Rig.Inventory->GetPendingOrders().Num(), 0);

	// A full store HOLDS a delivery; it lands when space frees.
	TestTrue(TEXT("tiny store registers"),
		Rig.Inventory->RegisterStore(FName(TEXT("Store.Tiny")), 5,
			Reason));
	TestTrue(TEXT("filler deposits"),
		Rig.Inventory->Deposit(FName(TEXT("Store.Tiny")),
			FName(TEXT("Raw.Silicon")), 5, Reason));
	TestTrue(TEXT("order to the full store places"),
		ALBSpacecraftGameMode::PlaceResourceOrder(*Rig.Inventory,
			*Rig.Production, FName(TEXT("Raw.IronOre")), 3,
			FName(TEXT("Store.Tiny")), Reason));
	Rig.Inventory->TickOrders(60.0);
	TestEqual(TEXT("the held delivery has not vanished"),
		Rig.Inventory->GetPendingOrders().Num(), 1);
	TestTrue(TEXT("space frees"),
		Rig.Inventory->Withdraw(FName(TEXT("Store.Tiny")),
			FName(TEXT("Raw.Silicon")), 5, Reason));
	Rig.Inventory->TickOrders(1.0);
	TestEqual(TEXT("the held delivery lands once there is room"),
		Rig.Inventory->GetQuantity(FName(TEXT("Store.Tiny")),
			FName(TEXT("Raw.IronOre"))), 3);

	Rig.World->DestroyWorld(false);
	return true;
}

#endif // WITH_DEV_AUTOMATION_TESTS

IMPLEMENT_SIMPLE_AUTOMATION_TEST(FLBSpacecraftCraftCostsItsPartsTest,
	"LineBoss.Spacecraft.Phase2.ACraftCostsTheComponentsItIsMadeOf",
	EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)

bool FLBSpacecraftCraftCostsItsPartsTest::RunTest(const FString& Parameters)
{
	(void)Parameters;
	using namespace LBSpacecraftPhase2IntegrationTestsPrivate;
	FLBSpacecraftPhase2Rig Rig = MakeSpacecraftPhase2Rig();
	FString Reason;

	const TCHAR* Classes[] = {
		TEXT("MaterialProcessor"), TEXT("HullFabricator"),
		TEXT("ComponentFabricator"), TEXT("AssemblyRobot") };
	float Y = -4000.f;
	for (const TCHAR* ClassId : Classes)
	{
		FName StationId;
		TestTrue(TEXT("line station places"),
			Rig.Build->PlaceStation(FName(ClassId),
				FTransform(FRotator::ZeroRotator, FVector(0.f, Y, 0.f)),
				StationId, Reason));
		for (int32 Crew = 0; Crew < 2; ++Crew)
		{
			TestTrue(TEXT("crewed to nominal"),
				Rig.Build->InstallStationDrone(StationId, Reason));
		}
		Y += 2200.f;
	}
	TestTrue(TEXT("the line commissions"),
		EnsureSprayBoothAndCommission(Rig, Reason));

	// COMMISSIONING FITS OUT THE LINE: the stations that assemble
	// components have those components allocated by default, which is
	// what gives a craft a marginal cost at all.
	int32 Allocated = 0;
	for (const FLBSpacecraftStationRecord& Record : Rig.Build->GetStations())
	{
		for (const FName& Component : Record.AllocatedComponents)
		{
			TestTrue(TEXT("only assembled components are allocated"),
				Component.ToString().StartsWith(TEXT("Component.")));
			++Allocated;
		}
	}
	TestEqual(TEXT("all six components are fitted somewhere on the line"),
		Allocated, 6);

	const FName Floor = ALBSpacecraftGameMode::SiteOverflowStoreId();
	TestTrue(TEXT("the site overflow yard exists"),
		Rig.Inventory->RegisterStore(Floor, 5000, Reason));
	// Components are fitted from the stockpile AT each station now, so
	// the rig gives every station its shelf. Haulage has its own test;
	// this one is about a craft costing what it is made of.
	ALBSpacecraftGameMode::SyncStationStores(*Rig.Build, *Rig.Inventory,
		Rig.Crafting);
	Rig.Coordinator->BindInventory(Rig.Inventory);
	TestTrue(TEXT("the coordinator configures"),
		Rig.Coordinator->ConfigureFromAuthorities(Rig.Build, Rig.Production,
			Reason));

	FLBSpacecraftContract Contract;
	Contract.ContractId = FName(TEXT("C-COST"));
	Contract.RecipeId = FName(TEXT("SCOUT-01"));
	Contract.Quantity = 1;
	Contract.PricePerUnitPence = 15000000;
	TestTrue(TEXT("contract offered"),
		Rig.Production->OfferContract(Contract, Reason));
	TestTrue(TEXT("contract accepted"),
		Rig.Production->AcceptContract(Contract.ContractId, Reason));

	// EMPTY STORE: the line starts a craft and then HOLDS. It must not
	// quietly build a free spacecraft out of nothing.
	for (int32 Tick = 0; Tick < 200; ++Tick)
	{
		Rig.Coordinator->TickProduction(5.0, Reason);
	}
	TestEqual(TEXT("no components, no delivery"),
		Rig.Production->GetRevenuePence(), static_cast<int64>(0));

	// Stock the six components - bought or fabricated, the line does
	// not care - and the same craft finishes.
	// Put two of every component on the shelf of whichever station
	// fits it - that is where the line reaches for them.
	for (const FLBSpacecraftStationRecord& Record : Rig.Build->GetStations())
	{
		const FName Stockpile(*FString::Printf(TEXT("Store.%s"),
			*Record.StationId.ToString()));
		for (const FName& Component : Record.AllocatedComponents)
		{
			TestTrue(TEXT("component stocks at the station that fits it"),
				Rig.Inventory->Deposit(Stockpile, Component, 2, Reason));
		}
	}
	for (int32 Tick = 0; Tick < 400
		&& Rig.Production->GetRevenuePence() == 0; ++Tick)
	{
		Rig.Coordinator->TickProduction(5.0, Reason);
	}
	TestEqual(TEXT("stocked, the craft delivers"),
		Rig.Production->GetRevenuePence(), static_cast<int64>(15000000));

	// And the components were really spent, not merely checked.
	int32 Remaining = 0;
	for (const FLBSpacecraftStationRecord& Record : Rig.Build->GetStations())
	{
		const FName Stockpile(*FString::Printf(TEXT("Store.%s"),
			*Record.StationId.ToString()));
		for (const FName& Component : Record.AllocatedComponents)
		{
			Remaining += Rig.Inventory->GetQuantity(Stockpile, Component);
		}
	}
	TestEqual(TEXT("one of each component was consumed"), Remaining, 6);

	Rig.World->DestroyWorld(false);
	return true;
}

IMPLEMENT_SIMPLE_AUTOMATION_TEST(FLBSpacecraftRawToDeliveryTest,
	"LineBoss.Spacecraft.Phase2.RawMaterialsBecomeADeliveredCraft",
	EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)

bool FLBSpacecraftRawToDeliveryTest::RunTest(const FString& Parameters)
{
	(void)Parameters;
	using namespace LBSpacecraftPhase2IntegrationTestsPrivate;
	// THE WHOLE ECONOMY IN ONE PROPERTY: raw materials become the six
	// assembled components through the parts factory's executed recipe
	// chains, those exact components stock the line, and the line turns
	// them into a paid craft with nothing left over.
	//
	// Every link has its own narrower test, but only the hull's chain
	// had ever been EXECUTED end to end - the other five components
	// were checked for a maker recipe existing, which a dead end two
	// levels down would pass. And every line test stocks components by
	// deposit, conjured from nowhere. This is the first proof that the
	// two factories actually compose: the parts factory's real output
	// is sufficient input for the ship factory's real consumption.
	FLBSpacecraftPhase2Rig Rig = MakeSpacecraftPhase2Rig();
	FString Reason;
	const FName Floor(TEXT("Store.PartsFactoryFloor"));
	TestTrue(TEXT("the parts-factory floor registers"),
		Rig.Inventory->RegisterStore(Floor, 1000000, Reason));

	// --- plan all six components at once ---
	TMap<FName, int32> Targets;
	for (uint8 Index = 0; Index < 6; ++Index)
	{
		Targets.Add(
			FLBSpacecraftItemCatalogue::GetAssembledComponentItemId(Index),
			1);
	}
	TArray<FLBSpacecraftPlannedRun> Plan;
	TMap<FName, int32> RawNeed;
	TestTrue(TEXT("the catalogue plans a whole craft's parts"),
		FLBSpacecraftRecipeCatalogue::PlanBuild(Targets, Plan, RawNeed,
			Reason));
	TestTrue(TEXT("six components pull a deep combined chain"),
		Plan.Num() > 40);

	// EXACT raw stock, no headroom: if the planner's arithmetic is off
	// by one anywhere in the chain, some cycle refuses and names the
	// step, which is precisely the failure this test exists to catch.
	for (const TPair<FName, int32>& Want : RawNeed)
	{
		TestTrue(*FString::Printf(TEXT("%s stocks exactly"),
				*Want.Key.ToString()),
			Rig.Inventory->Deposit(Floor, Want.Key, Want.Value, Reason));
	}

	// --- execute the plan, deepest first ---
	for (int32 Index = Plan.Num() - 1; Index >= 0; --Index)
	{
		const FLBSpacecraftPlannedRun& Run = Plan[Index];
		const FName StationId(*FString::Printf(TEXT("St.%s"),
			*Run.RecipeId.ToString()));
		FString Step;
		if (!TestTrue(*FString::Printf(TEXT("%s selects"),
				*Run.RecipeId.ToString()),
			Rig.Crafting->SelectRecipe(StationId, Run.StationClassId,
				Run.RecipeId, Step)))
		{
			continue;
		}
		TestTrue(*FString::Printf(TEXT("%s orders %d"),
				*Run.RecipeId.ToString(), Run.Cycles),
			Rig.Crafting->AddOrder(StationId, Run.Cycles, Step));
		for (int32 Cycle = 0; Cycle < Run.Cycles; ++Cycle)
		{
			if (!Rig.Crafting->ExecuteCraftCycle(StationId, *Rig.Inventory,
				Floor, Floor, Step))
			{
				AddError(FString::Printf(TEXT("%s cycle %d refused: %s"),
					*Run.RecipeId.ToString(), Cycle, *Step));
				break;
			}
			int32 Moved = 0;
			Rig.Crafting->TransferBufferToStore(StationId, *Rig.Inventory,
				Floor, 99, Moved, Step);
		}
	}
	for (const TPair<FName, int32>& Target : Targets)
	{
		TestTrue(*FString::Printf(TEXT("the parts factory made %s"),
				*Target.Key.ToString()),
			Rig.Inventory->GetQuantity(Floor, Target.Key) >= 1);
	}

	// --- the ship factory: one line, commissioned the player's way ---
	float Y = -4000.f;
	for (int32 Station = 0; Station < 4; ++Station)
	{
		FName StationId;
		TestTrue(TEXT("line station places"),
			Rig.Build->PlaceStation(FName(TEXT("AssemblyRobot")),
				FTransform(FRotator::ZeroRotator, FVector(0.f, Y, 0.f)),
				StationId, Reason));
		for (int32 Crew = 0; Crew < 2; ++Crew)
		{
			TestTrue(TEXT("crewed"),
				Rig.Build->InstallStationDrone(StationId, Reason));
		}
		Y += 2200.f;
	}
	TestTrue(TEXT("the line commissions"),
		EnsureSprayBoothAndCommission(Rig, Reason));
	ALBSpacecraftGameMode::SyncStationStores(*Rig.Build, *Rig.Inventory,
		Rig.Crafting);
	Rig.Coordinator->BindInventory(Rig.Inventory);
	TestTrue(TEXT("the coordinator configures"),
		Rig.Coordinator->ConfigureFromAuthorities(Rig.Build,
			Rig.Production, Reason));

	// The haul, by hand (haulage has its own tests): ONE of each
	// component moves from the parts-factory floor to the shelf of the
	// station that fits it. A withdraw that refuses here means the
	// parts factory did not actually make what the line needs.
	for (const FLBSpacecraftStationRecord& Record : Rig.Build->GetStations())
	{
		const FName Stockpile(*FString::Printf(TEXT("Store.%s"),
			*Record.StationId.ToString()));
		for (const FName& Component : Record.AllocatedComponents)
		{
			TestTrue(*FString::Printf(TEXT("%s hauls to its station"),
					*Component.ToString()),
				Rig.Inventory->Withdraw(Floor, Component, 1, Reason)
				&& Rig.Inventory->Deposit(Stockpile, Component, 1,
					Reason));
		}
	}

	FLBSpacecraftContract Contract;
	Contract.ContractId = FName(TEXT("C-RAW"));
	Contract.RecipeId = FName(TEXT("SCOUT-01"));
	Contract.Quantity = 1;
	Contract.PricePerUnitPence = 15000000;
	TestTrue(TEXT("contract offered"),
		Rig.Production->OfferContract(Contract, Reason));
	TestTrue(TEXT("contract accepted"),
		Rig.Production->AcceptContract(Contract.ContractId, Reason));
	for (int32 Tick = 0; Tick < 400
		&& Rig.Production->GetRevenuePence() == 0; ++Tick)
	{
		Rig.Coordinator->TickProduction(5.0, Reason);
	}
	TestEqual(TEXT("raw materials became a paid spacecraft"),
		Rig.Production->GetRevenuePence(), static_cast<int64>(15000000));

	// Nothing left over, nothing conjured: the craft consumed exactly
	// the six components the parts factory made.
	for (const FLBSpacecraftStationRecord& Record : Rig.Build->GetStations())
	{
		const FName Stockpile(*FString::Printf(TEXT("Store.%s"),
			*Record.StationId.ToString()));
		for (const FName& Component : Record.AllocatedComponents)
		{
			TestEqual(*FString::Printf(TEXT("%s shelf is empty again"),
					*Component.ToString()),
				Rig.Inventory->GetQuantity(Stockpile, Component), 0);
		}
	}
	for (const TPair<FName, int32>& Target : Targets)
	{
		TestEqual(*FString::Printf(TEXT("no spare %s on the floor"),
				*Target.Key.ToString()),
			Rig.Inventory->GetQuantity(Floor, Target.Key), 0);
	}

	Rig.World->DestroyWorld(false);
	return true;
}

IMPLEMENT_SIMPLE_AUTOMATION_TEST(FLBSpacecraftSelfFeedingFactoryTest,
	"LineBoss.Spacecraft.Phase2.TheFactoryFeedsItselfToDelivery",
	EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)

bool FLBSpacecraftSelfFeedingFactoryTest::RunTest(const FString& Parameters)
{
	(void)Parameters;
	using namespace LBSpacecraftPhase2IntegrationTestsPrivate;
	// The RawMaterialsBecomeADeliveredCraft test executes the plan BY
	// HAND - it proves the data closes, not that the running factory
	// closes it. This one hands everything to the sim: SetupEconomy
	// builds the parts factory the way a player save would have it,
	// raw materials arrive through the order pipeline, machines stall
	// and start on their own clocks, the haulers move every item, and
	// the ONLY thing the test does afterwards is tick and wait. Not
	// one Deposit call. If any link of the loop cannot actually feed
	// the next at runtime - order lead times, buffer sizes, hauler
	// priorities, stockpile targets - this is the test that starves.
	FLBSpacecraftPhase2Rig Rig = MakeSpacecraftPhase2Rig();
	FString Reason;
	TestTrue(TEXT("the line commissions"),
		ALBSpacecraftGameMode::SetupCanonicalLine(*Rig.Build, Reason));
	Rig.Coordinator->BindInventory(Rig.Inventory);
	TestTrue(TEXT("the coordinator configures"),
		Rig.Coordinator->ConfigureFromAuthorities(Rig.Build,
			Rig.Production, Reason));

	// The game-mode tick, mirrored: orders land, machines craft,
	// haulers move, the line consumes. 5 s steps, generous guard - the
	// whole chain plus lead times plus the line's own cycle.
	int32 CraftCycles = 0;
	int32 Ticks = 0;
	auto DeliverContract = [&](const TCHAR* ContractId,
		int64 ExpectTotalRevenue)
	{
		FLBSpacecraftContract Contract;
		Contract.ContractId = FName(ContractId);
		Contract.RecipeId = FName(TEXT("SCOUT-01"));
		Contract.Quantity = 1;
		Contract.PricePerUnitPence = 15000000;
		FString Local;
		TestTrue(TEXT("contract offered"),
			Rig.Production->OfferContract(Contract, Local));
		TestTrue(TEXT("contract accepted"),
			Rig.Production->AcceptContract(Contract.ContractId, Local));
		for (; Ticks < 8000 && Rig.Production->GetRevenuePence()
			< ExpectTotalRevenue; ++Ticks)
		{
			Rig.Inventory->TickOrders(5.0);
			CraftCycles += ALBSpacecraftGameMode::TickCraftingStations(
				*Rig.Build, *Rig.Crafting, *Rig.Inventory, 5.0);
			Rig.DroneFleet->TickHauls(5.0, Rig.Crafting, Rig.Inventory,
				Rig.Build);
			Rig.Coordinator->TickProduction(5.0, Local);
		}
	};

	// THE ARC, as the player lives it: fabrication is a delivery
	// milestone, so the first SetupEconomy builds the IMPORT economy -
	// two contracts assembled from bought components earn the unlock -
	// and the second call builds the hull fabrication chain.
	TestTrue(TEXT("the import economy builds"),
		ALBSpacecraftGameMode::SetupEconomy(*Rig.Build, *Rig.Power,
			*Rig.Inventory, *Rig.Crafting, *Rig.Research, *Rig.Production,
			Rig.Progression, 2, Reason));
	TestTrue(TEXT("the first economy is the import economy"),
		Reason.Contains(TEXT("ALL IMPORTED")));
	Rig.DroneFleet->SyncFromBuild(Rig.Build, Rig.Power);
	DeliverContract(TEXT("C-SELF-1"), 15000000);
	DeliverContract(TEXT("C-SELF-2"), 30000000);
	TestEqual(TEXT("two imported craft delivered"),
		Rig.Production->GetRevenuePence(),
		static_cast<int64>(30000000));

	TestTrue(TEXT("the earned economy builds"),
		ALBSpacecraftGameMode::SetupEconomy(*Rig.Build, *Rig.Power,
			*Rig.Inventory, *Rig.Crafting, *Rig.Research, *Rig.Production,
			Rig.Progression, 1, Reason));
	AddInfo(Reason);
	TestTrue(TEXT("delivering twice earned the parts factory"),
		Reason.Contains(TEXT("HULL FABRICATED")));
	Rig.DroneFleet->SyncFromBuild(Rig.Build, Rig.Power);
	const int64 CashAfterOrders = Rig.Production->GetCashPence();
	DeliverContract(TEXT("C-SELF-3"), 45000000);
	if (Rig.Production->GetRevenuePence() < 45000000)
	{
		// Where did the bill of materials actually end up? The answer
		// names the broken link; without it every starvation looks
		// alike.
		for (uint8 Index = 0; Index < 6; ++Index)
		{
			const FName Item =
				FLBSpacecraftItemCatalogue::GetAssembledComponentItemId(
					Index);
			FString Holdings;
			for (const FLBSpacecraftStationRecord& Record :
				Rig.Build->GetStations())
			{
				const FName Store(*FString::Printf(TEXT("Store.%s"),
					*Record.StationId.ToString()));
				const int32 Count = Rig.Inventory->GetQuantity(Store,
					Item);
				if (Count > 0)
				{
					Holdings += FString::Printf(TEXT(" %s=%d"),
						*Record.StationId.ToString(), Count);
				}
			}
			AddInfo(FString::Printf(TEXT("%s holdings:%s (pending "
				"orders %d)"), *Item.ToString(),
				Holdings.IsEmpty() ? TEXT(" NOWHERE") : *Holdings,
				Rig.Inventory->GetPendingOrders().Num()));
		}
		AddInfo(FString::Printf(TEXT("last coordinator hold: %s"),
			*Rig.Coordinator->GetLastHoldReason()));
		// Which machines still owe cycles, and what starves them.
		int32 Dumped = 0;
		for (const FLBSpacecraftStationRecord& Record :
			Rig.Build->GetStations())
		{
			const FLBSpacecraftItemRecipe* Recipe =
				Rig.Crafting->GetSelectedRecipe(Record.StationId);
			const int32 Remaining =
				Rig.Crafting->GetOrderRemaining(Record.StationId);
			if (Recipe == nullptr || Remaining <= 0 || Dumped >= 15)
			{
				continue;
			}
			const FName Shelf(*FString::Printf(TEXT("Store.%s"),
				*Record.StationId.ToString()));
			FString Inputs;
			for (const FLBSpacecraftItemStack& Input : Recipe->Inputs)
			{
				Inputs += FString::Printf(TEXT(" %s %d/%d"),
					*Input.ItemId.ToString(),
					Rig.Inventory->GetQuantity(Shelf, Input.ItemId),
					Input.Count);
			}
			AddInfo(FString::Printf(
				TEXT("STUCK %s %s owes %d, buffer %d, shelf:%s"),
				*Record.StationId.ToString(),
				*Recipe->RecipeId.ToString(), Remaining,
				Rig.Crafting->GetBufferCount(Record.StationId),
				*Inputs));
			++Dumped;
		}
		// Whole-site material balance for the contested intermediates:
		// the starved shelf says WHO is short, only the site total says
		// whether the material was never made, is stranded on a
		// finished machine's shelf, or sits in a rack no hauler will
		// draw from.
		const TCHAR* Contested[] = { TEXT("Proc.LightAlloy"),
			TEXT("Proc.Steel"), TEXT("Proc.FrameStock"),
			TEXT("Proc.Composites"), TEXT("Proc.Fasteners"),
			TEXT("Proc.PlateStock") };
		for (const TCHAR* ItemName : Contested)
		{
			const FName Item(ItemName);
			FString Where;
			int32 Total = 0;
			for (const FLBSpacecraftStationRecord& Record :
				Rig.Build->GetStations())
			{
				const FName Store(*FString::Printf(TEXT("Store.%s"),
					*Record.StationId.ToString()));
				const int32 Count = Rig.Inventory->GetQuantity(Store,
					Item);
				if (Count > 0)
				{
					Where += FString::Printf(TEXT(" %s=%d"),
						*Record.StationId.ToString(), Count);
					Total += Count;
				}
			}
			const int32 Overflow = Rig.Inventory->GetQuantity(
				ALBSpacecraftGameMode::SiteOverflowStoreId(), Item);
			Total += Overflow;
			AddInfo(FString::Printf(TEXT("BALANCE %s site total %d "
				"(overflow %d):%s"), ItemName, Total, Overflow,
				Where.IsEmpty() ? TEXT(" none") : *Where));
		}
	}
	TestEqual(TEXT("the self-feeding factory delivered all three"),
		Rig.Production->GetRevenuePence(),
		static_cast<int64>(45000000));
	TestTrue(TEXT("the parts factory really ran"), CraftCycles > 40);
	// Feedstock was paid for through the ledger - the margin is real:
	// the fabricated craft's price beat what its ore and imports cost.
	TestTrue(TEXT("the fabricated craft turned a profit"),
		Rig.Production->GetCashPence() > CashAfterOrders);
	AddInfo(FString::Printf(
		TEXT("delivered after %d ticks (%.0f sim s), %d craft cycles, ")
		TEXT("cash %lld -> %lld hundredths"),
		Ticks, Ticks * 5.0, CraftCycles, CashAfterOrders,
		Rig.Production->GetCashPence()));

	Rig.World->DestroyWorld(false);
	return true;
}

IMPLEMENT_SIMPLE_AUTOMATION_TEST(FLBSpacecraftDroneDeliveryTest,
	"LineBoss.Spacecraft.Logistics.DronesCarryGoodsToTheStationsThatNeedThem",
	EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)

bool FLBSpacecraftDroneDeliveryTest::RunTest(const FString& Parameters)
{
	(void)Parameters;
	using namespace LBSpacecraftPhase2IntegrationTestsPrivate;
	FLBSpacecraftPhase2Rig Rig = MakeSpacecraftPhase2Rig();
	FString Reason;

	// A line, crewed and commissioned, plus the storage rack that a
	// heavy hauler belongs to.
	const TCHAR* Classes[] = {
		TEXT("MaterialProcessor"), TEXT("HullFabricator"),
		TEXT("ComponentFabricator"), TEXT("AssemblyRobot") };
	float Y = -4000.f;
	for (const TCHAR* ClassId : Classes)
	{
		FName StationId;
		TestTrue(TEXT("line station places"),
			Rig.Build->PlaceStation(FName(ClassId),
				FTransform(FRotator::ZeroRotator, FVector(0.f, Y, 0.f)),
				StationId, Reason));
		Y += 2200.f;
	}
	FName RackId;
	TestTrue(TEXT("a storage rack places"),
		Rig.Build->PlaceStation(FName(TEXT("StorageRack")),
			FTransform(FRotator::ZeroRotator, FVector(-4000.f, 0.f, 0.f)),
			RackId, Reason));
	TestTrue(TEXT("the line commissions"),
		EnsureSprayBoothAndCommission(Rig, Reason));

	// The site overflow yard, holding a delivery that has landed but
	// has not been carried anywhere yet.
	const FName Yard = ALBSpacecraftGameMode::SiteOverflowStoreId();
	TestTrue(TEXT("the yard registers"),
		Rig.Inventory->RegisterStore(Yard, 5000, Reason));
	ALBSpacecraftGameMode::SyncStationStores(*Rig.Build, *Rig.Inventory,
		Rig.Crafting);

	// Find a station that actually fits something, and stock the yard
	// with what it needs.
	FName Consumer;
	FName Wanted;
	for (const FLBSpacecraftStationRecord& Record : Rig.Build->GetStations())
	{
		if (Record.AllocatedComponents.Num() > 0)
		{
			Consumer = Record.StationId;
			Wanted = Record.AllocatedComponents[0];
			break;
		}
	}
	TestFalse(TEXT("commissioning gave some station work to do"),
		Consumer.IsNone());
	TestTrue(TEXT("the delivery lands in the yard"),
		Rig.Inventory->Deposit(Yard, Wanted, 4, Reason));

	const FName Stockpile(*FString::Printf(TEXT("Store.%s"),
		*Consumer.ToString()));
	TestEqual(TEXT("the station starts with an empty shelf"),
		Rig.Inventory->GetQuantity(Stockpile, Wanted), 0);

	// Now run the haulers. Nothing else moves goods: if the drone does
	// not carry it, it does not arrive.
	ALBSpacecraftDroneFleetAuthority* Fleet =
		Rig.World->SpawnActor<ALBSpacecraftDroneFleetAuthority>();
	Fleet->SyncFromBuild(Rig.Build, nullptr);
	TestEqual(TEXT("the rack has a hauler"), Fleet->GetHauls().Num(), 1);
	bool bSawDelivering = false;
	for (int32 Tick = 0; Tick < 40; ++Tick)
	{
		Fleet->TickHauls(2.0, Rig.Crafting, Rig.Inventory, Rig.Build);
		for (const FLBSpacecraftHaulState& Haul : Fleet->GetHauls())
		{
			if (Haul.Job == ELBSpacecraftHaulJob::DeliverInput
				&& Haul.Phase != ELBSpacecraftHaulPhase::Idle)
			{
				bSawDelivering = true;
			}
		}
	}
	TestTrue(TEXT("a hauler took the delivery run"), bSawDelivering);

	// A hauler must bring the SHORTFALL, never a full load regardless.
	// Carrying more than the station wants overshoots the top-up
	// target, and a shelf sized to hold the target of everything then
	// fills with whatever was fetched first - leaving no room for the
	// one part the station is waiting on. That deadlocked a real run
	// after five craft, so it is pinned here.
	TestTrue(TEXT("a delivery never overshoots the top-up target"),
		Rig.Inventory->GetQuantity(Stockpile, Wanted)
			<= Fleet->StockpileTopUpUnits);
	TestTrue(TEXT("the goods arrived at the station that needed them"),
		Rig.Inventory->GetQuantity(Stockpile, Wanted) > 0);
	TestTrue(TEXT("and left the yard"),
		Rig.Inventory->GetQuantity(Yard, Wanted) < 4);

	// EVERY required part gets a share of the shelf. Stock the yard
	// with the whole set a station fits and run the haulers: none of
	// them may be starved out by another hogging the room.
	FName Busiest;
	int32 MostParts = 0;
	for (const FLBSpacecraftStationRecord& Record : Rig.Build->GetStations())
	{
		if (Record.AllocatedComponents.Num() > MostParts)
		{
			MostParts = Record.AllocatedComponents.Num();
			Busiest = Record.StationId;
		}
	}
	if (MostParts > 1)
	{
		const FLBSpacecraftStationRecord* Busy =
			Rig.Build->FindStation(Busiest);
		const FName BusyStock(*FString::Printf(TEXT("Store.%s"),
			*Busiest.ToString()));
		for (const FName& Part : Busy->AllocatedComponents)
		{
			TestTrue(TEXT("the yard carries the whole set"),
				Rig.Inventory->Deposit(Yard, Part, 8, Reason));
		}
		for (int32 Tick = 0; Tick < 200; ++Tick)
		{
			Fleet->TickHauls(2.0, Rig.Crafting, Rig.Inventory, Rig.Build);
		}
		for (const FName& Part : Busy->AllocatedComponents)
		{
			TestTrue(TEXT("no required part is starved off the shelf"),
				Rig.Inventory->GetQuantity(BusyStock, Part) > 0);
		}
	}

	// The shelf is sized from the PARTS, not a flat guess: a component
	// is several units, so a station fitting several needs a bigger
	// shelf than one fitting a single part.
	TArray<FName> One;
	One.Add(Wanted);
	TArray<FName> Three = One;
	Three.Add(FName(TEXT("Component.Power")));
	Three.Add(FName(TEXT("Component.Navigation")));
	TestTrue(TEXT("more parts need a bigger shelf"),
		ALBSpacecraftGameMode::StockpileUnitsForItems(Three, 4, 1)
			> ALBSpacecraftGameMode::StockpileUnitsForItems(One, 4, 1));
	TestTrue(TEXT("a bulky part needs more room than a small one"),
		ALBSpacecraftGameMode::StockpileUnitsForItems(One, 4, 1)
			> ALBSpacecraftGameMode::StockpileUnitsForItems(
				{FName(TEXT("Raw.IronOre"))}, 4, 1));

	Rig.World->DestroyWorld(false);
	return true;
}

IMPLEMENT_SIMPLE_AUTOMATION_TEST(FLBSpacecraftMk2UpgradePathTest,
	"LineBoss.Spacecraft.Phase2.AnUpgradedLineCanBuildTheBiggerCraft",
	EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)

bool FLBSpacecraftMk2UpgradePathTest::RunTest(const FString& Parameters)
{
	(void)Parameters;
	using namespace LBSpacecraftPhase2IntegrationTestsPrivate;
	FLBSpacecraftPhase2Rig Rig = MakeSpacecraftPhase2Rig();
	FString Reason;

	// A Mk1 line, as every player starts with.
	const TCHAR* Mk1[] = {
		TEXT("MaterialProcessor"), TEXT("HullFabricator"),
		TEXT("ComponentFabricator"), TEXT("AssemblyRobot") };
	float Y = -4000.f;
	for (const TCHAR* ClassId : Mk1)
	{
		FName StationId;
		TestTrue(TEXT("Mk1 station places"),
			Rig.Build->PlaceStation(FName(ClassId),
				FTransform(FRotator::ZeroRotator, FVector(0.f, Y, 0.f)),
				StationId, Reason));
		Y += 2200.f;
	}
	TestTrue(TEXT("the Mk1 line commissions"),
		EnsureSprayBoothAndCommission(Rig, Reason));

	FLBSpacecraftRecipe Cargo;
	TestTrue(TEXT("the cargo recipe exists"),
		FLBSpacecraftProductionCatalog::FindRecipe(FName(TEXT("CARGO-01")),
			Cargo));
	TArray<FLBSpacecraftRouteStep> Route;
	TestTrue(TEXT("the Mk1 line routes"), Rig.Build->BuildRoute(Route, Reason));
	TestFalse(TEXT("a Mk1 line rightly refuses the bigger craft"),
		ALBSpacecraftBuildAuthority::RouteCanServiceRecipe(Route, Cargo,
			Reason));

	// The player earns the Mk2 marks first - the same tree a real run
	// pays for out of deliveries.
	TestTrue(TEXT("points bank"), Rig.Research->AddPoints(100, Reason));
	for (const TCHAR* NodeId : { TEXT("Research.Mfg.T1"),
		TEXT("Research.Mfg.T2"), TEXT("Research.Mfg.Mk2") })
	{
		TestTrue(TEXT("the mark research unlocks"),
			Rig.Research->UnlockNode(FName(NodeId), Reason));
	}

	// Now the player buys the Mk2 marks and puts them up ALONGSIDE the
	// Mk1 line, which is the only way to upgrade - there is no in-place
	// upgrade, so both marks stand on the floor at once.
	const TCHAR* Mk2[] = {
		TEXT("MaterialProcessorMk2"), TEXT("HullFabricatorMk2"),
		TEXT("ComponentFabricatorMk2"), TEXT("AssemblyRobotMk2") };
	Y = -4000.f;
	for (const TCHAR* ClassId : Mk2)
	{
		FName StationId;
		if (!Rig.Build->PlaceStation(FName(ClassId),
			FTransform(FRotator::ZeroRotator, FVector(6000.f, Y, 0.f)),
			StationId, Reason))
		{
			AddError(FString::Printf(TEXT("Mk2 %s refused: %s"),
				ClassId, *Reason));
		}
		Y += 3200.f;
	}
	TestTrue(TEXT("the upgraded floor commissions"),
		EnsureSprayBoothAndCommission(Rig, Reason));

	// The route is EVERY line station now (one repeated type, Car
	// Manufacture style), so with both marks standing the craft would
	// pass through the Mk1s too - and a Mk1 cannot hold a Cargo. The
	// refusal must NAME the blocking station, and clearing the old
	// marks is the upgrade path: remove the Mk1s, the line is Mk2.
	TestTrue(TEXT("the mixed floor routes"),
		Rig.Build->BuildRoute(Route, Reason));
	TestFalse(TEXT("a mixed line still refuses the bigger craft"),
		ALBSpacecraftBuildAuthority::RouteCanServiceRecipe(Route, Cargo,
			Reason));
	TestTrue(TEXT("and the refusal names a station"),
		Reason.Contains(TEXT("CANNOT HOLD")));
	TArray<FName> Mk1Stations;
	for (const FLBSpacecraftStationRecord& Record :
		Rig.Build->GetStations())
	{
		const FString Id = Record.DefinitionId.ToString();
		const FLBSpacecraftStationDefinition* Definition =
			ALBSpacecraftBuildAuthority::FindDefinition(
				Record.DefinitionId);
		// The spray booth is a line station and has no Mk2, so it would
		// be swept up by a name test. It is excluded by what it IS -
		// a process station - which is the same lesson as the fixing
		// split: ask what a station does, never what it is called.
		if (Definition != nullptr && !Definition->StageClassId.IsNone()
			&& !Definition->bProcessStation
			&& !Id.EndsWith(TEXT("Mk2")))
		{
			Mk1Stations.Add(Record.StationId);
		}
	}
	TestEqual(TEXT("four Mk1 stations to clear"), Mk1Stations.Num(), 4);
	for (const FName& StationId : Mk1Stations)
	{
		TestTrue(TEXT("the old mark removes"),
			Rig.Build->RemoveStation(StationId, Reason));
	}
	TestTrue(TEXT("the cleared floor commissions"),
		EnsureSprayBoothAndCommission(Rig, Reason));
	TestTrue(TEXT("the upgraded floor routes"),
		Rig.Build->BuildRoute(Route, Reason));
	const bool bCanBuildCargo =
		ALBSpacecraftBuildAuthority::RouteCanServiceRecipe(Route, Cargo,
			Reason);
	TestTrue(TEXT("an upgraded line can build the bigger craft"),
		bCanBuildCargo);
	if (!bCanBuildCargo)
	{
		AddInfo(FString::Printf(
			TEXT("route refused the cargo craft: %s"), *Reason));
	}

	Rig.World->DestroyWorld(false);
	return true;
}

IMPLEMENT_SIMPLE_AUTOMATION_TEST(FLBSpacecraftDeliveryDockTest,
	"LineBoss.Spacecraft.Logistics.GoodsArriveAtADockOrNotAtAll",
	EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)

bool FLBSpacecraftDeliveryDockTest::RunTest(const FString& Parameters)
{
	(void)Parameters;
	using namespace LBSpacecraftPhase2IntegrationTestsPrivate;
	FLBSpacecraftPhase2Rig Rig = MakeSpacecraftPhase2Rig();
	FString Reason;
	const FName Ore(TEXT("Raw.IronOre"));

	// NO DOCK: bought goods have nowhere to arrive, and the refusal
	// says so plainly instead of teleporting them onto the floor.
	FName Store = ALBSpacecraftGameMode::FindDeliveryStore(*Rig.Build,
		*Rig.Inventory, Ore, 10, Reason);
	TestTrue(TEXT("without a dock there is nowhere to deliver"),
		Store.IsNone());
	TestTrue(TEXT("and the refusal names the cure"),
		Reason.Contains(TEXT("BUILD ONE")));

	// Build a dock and the same order finds its home.
	FName DockId;
	TestTrue(TEXT("a delivery dock places"),
		Rig.Build->PlaceStation(FName(TEXT("DeliveryDock")),
			FTransform(FRotator::ZeroRotator, FVector(-4000.f, 3000.f, 0.f)),
			DockId, Reason));
	ALBSpacecraftGameMode::SyncStationStores(*Rig.Build, *Rig.Inventory,
		Rig.Crafting);
	Store = ALBSpacecraftGameMode::FindDeliveryStore(*Rig.Build,
		*Rig.Inventory, Ore, 10, Reason);
	TestFalse(TEXT("with a dock the delivery has somewhere to land"),
		Store.IsNone());
	TestEqual(TEXT("and it lands AT THE DOCK"), Store,
		FName(*FString::Printf(TEXT("Store.%s"), *DockId.ToString())));

	// A BACKED-UP DOCK refuses more. That is the pressure that makes
	// storage and haulers worth buying - not a soft failure that
	// quietly drops goods somewhere else.
	const int32 Room = Rig.Inventory->GetRoomForItems(Store, Ore);
	TestTrue(TEXT("the dock has a finite hold"), Room > 0);
	TestTrue(TEXT("fill it"),
		Rig.Inventory->Deposit(Store, Ore, Room, Reason));
	const FName WhenFull = ALBSpacecraftGameMode::FindDeliveryStore(
		*Rig.Build, *Rig.Inventory, Ore, 10, Reason);
	TestTrue(TEXT("a full dock takes no more"), WhenFull.IsNone());
	TestTrue(TEXT("and says why, in plain words"),
		Reason.Contains(TEXT("BACKED UP")));

	// A second dock takes the overflow, which is the player's answer.
	FName SecondDockId;
	TestTrue(TEXT("a second dock places"),
		Rig.Build->PlaceStation(FName(TEXT("DeliveryDock")),
			FTransform(FRotator::ZeroRotator, FVector(-4000.f, 4400.f, 0.f)),
			SecondDockId, Reason));
	ALBSpacecraftGameMode::SyncStationStores(*Rig.Build, *Rig.Inventory,
		Rig.Crafting);
	TestFalse(TEXT("building another dock reopens deliveries"),
		ALBSpacecraftGameMode::FindDeliveryStore(*Rig.Build, *Rig.Inventory,
			Ore, 10, Reason).IsNone());

	Rig.World->DestroyWorld(false);
	return true;
}

IMPLEMENT_SIMPLE_AUTOMATION_TEST(FLBSpacecraftCargoDeliversTest,
	"LineBoss.Spacecraft.Phase2.TheSecondCraftTierBuildsAndPays",
	EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)

bool FLBSpacecraftCargoDeliversTest::RunTest(const FString& Parameters)
{
	(void)Parameters;
	using namespace LBSpacecraftPhase2IntegrationTestsPrivate;
	FLBSpacecraftPhase2Rig Rig = MakeSpacecraftPhase2Rig();
	FString Reason;

	// The Mk2 marks, earned and standing. A player reaches this after
	// roughly 25-30 Scout deliveries; the economics of getting here are
	// proven by journey, and what this test pins is that the craft then
	// actually BUILDS - the thing a long run kept running out of money
	// before reaching.
	TestTrue(TEXT("points bank"), Rig.Research->AddPoints(100, Reason));
	for (const TCHAR* NodeId : { TEXT("Research.Mfg.T1"),
		TEXT("Research.Mfg.T2"), TEXT("Research.Mfg.Mk2") })
	{
		TestTrue(TEXT("the mark research unlocks"),
			Rig.Research->UnlockNode(FName(NodeId), Reason));
	}
	const TCHAR* Mk2[] = {
		TEXT("MaterialProcessorMk2"), TEXT("HullFabricatorMk2"),
		TEXT("ComponentFabricatorMk2"), TEXT("AssemblyRobotMk2") };
	float Y = -4000.f;
	for (const TCHAR* ClassId : Mk2)
	{
		FName StationId;
		TestTrue(TEXT("Mk2 station places"),
			Rig.Build->PlaceStation(FName(ClassId),
				FTransform(FRotator::ZeroRotator, FVector(0.f, Y, 0.f)),
				StationId, Reason));
		for (int32 Crew = 0; Crew < 2; ++Crew)
		{
			TestTrue(TEXT("crewed to nominal"),
				Rig.Build->InstallStationDrone(StationId, Reason));
		}
		Y += 3400.f;
	}
	TestTrue(TEXT("the Mk2 line commissions"),
		EnsureSprayBoothAndCommission(Rig, Reason));

	// Stock every station's shelf with what it fits - haulage has its
	// own tests; this one is about the bigger craft.
	ALBSpacecraftGameMode::SyncStationStores(*Rig.Build, *Rig.Inventory,
		Rig.Crafting);
	for (const FLBSpacecraftStationRecord& Record : Rig.Build->GetStations())
	{
		const FName Stockpile(*FString::Printf(TEXT("Store.%s"),
			*Record.StationId.ToString()));
		for (const FName& Component : Record.AllocatedComponents)
		{
			// STOCKED TO WHAT THE RECIPE ASKS FOR, not to a flat two.
			// A Cargo carries three hulls, three powerplants and three
			// engines where a Scout carries one of each, so a fixed
			// figure here silently under-stocks the very tier this test
			// exists to prove - and would need editing again the next
			// time a count moves.
			FLBSpacecraftRecipe Wanted;
			int32 Needed = 2;
			if (FLBSpacecraftProductionCatalog::FindRecipe(
				FName(TEXT("CARGO-01")), Wanted))
			{
				Needed = FMath::Max(2, FLBSpacecraftProductionCatalog
					::ComponentCountForItem(Wanted, Component));
			}
			TestTrue(TEXT("the shelf is stocked"),
				Rig.Inventory->Deposit(Stockpile, Component, Needed,
					Reason));
		}
	}
	Rig.Coordinator->BindInventory(Rig.Inventory);
	TestTrue(TEXT("the coordinator configures"),
		Rig.Coordinator->ConfigureFromAuthorities(Rig.Build, Rig.Production,
			Reason));

	// A CARGO order - the second tier, which a Mk1 line refuses.
	FLBSpacecraftContract Cargo;
	Cargo.ContractId = FName(TEXT("C-CARGO-RUN"));
	Cargo.RecipeId = FName(TEXT("CARGO-01"));
	Cargo.Quantity = 1;
	Cargo.PricePerUnitPence = 20000000; // deliberately != the
	// recipe baseline (36,000,000), so this proves the settle pays
	// the CONTRACT price rather than the catalogue's.
	TestTrue(TEXT("the cargo order is offered"),
		Rig.Production->OfferContract(Cargo, Reason));
	TestTrue(TEXT("and accepted"),
		Rig.Production->AcceptContract(Cargo.ContractId, Reason));

	for (int32 Tick = 0; Tick < 600
		&& Rig.Production->GetRevenuePence() == 0; ++Tick)
	{
		Rig.Coordinator->TickProduction(10.0, Reason);
	}

	// THE CLAIM: the second craft tier is not just acceptable and
	// routable - it is buildable, and it pays.
	TestEqual(TEXT("the cargo craft was delivered and paid"),
		Rig.Production->GetRevenuePence(), static_cast<int64>(20000000));
	if (Rig.Production->GetRevenuePence() == 0)
	{
		AddInfo(FString::Printf(TEXT("line held: %s"),
			*Rig.Coordinator->GetLastHoldReason()));
	}
	const FLBSpacecraftContract* Settled =
		Rig.Production->FindContract(Cargo.ContractId);
	TestNotNull(TEXT("the contract survives"), Settled);
	if (Settled != nullptr)
	{
		TestEqual(TEXT("and completed"), Settled->State,
			ELBSpacecraftContractState::Complete);
	}

	Rig.World->DestroyWorld(false);
	return true;
}

IMPLEMENT_SIMPLE_AUTOMATION_TEST(FLBSpacecraftMilestonesBiteTest,
	"LineBoss.Spacecraft.Phase2.TheObjectivesLadderActuallyGatesThings",
	EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)

bool FLBSpacecraftMilestonesBiteTest::RunTest(const FString& Parameters)
{
	(void)Parameters;
	using namespace LBSpacecraftPhase2IntegrationTestsPrivate;
	FLBSpacecraftPhase2Rig Rig = MakeSpacecraftPhase2Rig();
	FString Reason;

	// The ladder shown to the player promises three unlocks. Two of
	// them used to gate nothing at all, which made the ladder a
	// promise the game did not keep.
	ALBSpacecraftProgressionAuthority* Progress =
		Rig.World->SpawnActor<ALBSpacecraftProgressionAuthority>();
	TestFalse(TEXT("fabrication starts locked"),
		Progress->IsUnlocked(ELBSpacecraftUnlock::Fabrication));
	TestFalse(TEXT("quality control starts locked"),
		Progress->IsUnlocked(ELBSpacecraftUnlock::QualityControl));
	TestTrue(TEXT("and the lock says how to open it"),
		Progress->DescribeLock(ELBSpacecraftUnlock::Fabrication)
			.Contains(TEXT("FABRICATION")));

	// QUALITY CONTROL: crew to nominal is always allowed, so nobody is
	// forced to build defective craft; the milestone opens crewing
	// BEYOND nominal.
	FName LineId;
	TestTrue(TEXT("a line station places"),
		Rig.Build->PlaceStation(FName(TEXT("MaterialProcessor")),
			FTransform(FRotator::ZeroRotator, FVector(0.f, 0.f, 0.f)),
			LineId, Reason));
	for (int32 Crew = 0; Crew < ALBSpacecraftGameMode::NominalStationCrew();
		++Crew)
	{
		TestTrue(TEXT("crewing to nominal is always allowed"),
			ALBSpacecraftGameMode::InstallStationDronePowered(*Rig.Build,
				LineId, Reason, nullptr, Progress));
	}
	TestFalse(TEXT("crewing beyond nominal waits on the milestone"),
		ALBSpacecraftGameMode::InstallStationDronePowered(*Rig.Build,
			LineId, Reason, nullptr, Progress));
	TestTrue(TEXT("and the refusal names the milestone"),
		Reason.Contains(TEXT("QUALITY CONTROL")));
	TestTrue(TEXT("and says the station is already at nominal"),
		Reason.Contains(TEXT("NOMINAL CREW")));

	// Deliver enough craft and both open.
	FLBSpacecraftProductionLedgerState Ledger = Rig.Production->CaptureLedger();
	for (int32 Index = 0; Index < 4; ++Index)
	{
		FLBSpacecraftContract Done;
		Done.ContractId = FName(*FString::Printf(TEXT("C-M%d"), Index));
		Done.RecipeId = FName(TEXT("SCOUT-01"));
		Done.Quantity = 1;
		Done.DispatchedCount = 1;
		Done.PricePerUnitPence = 15000000;
		Done.State = ELBSpacecraftContractState::Complete;
		Ledger.Contracts.Add(Done);
	}
	TestTrue(TEXT("the deliveries land on the ledger"),
		Rig.Production->RestoreLedger(Ledger, Reason));
	Progress->SyncFromLedger(Rig.Production);
	TestTrue(TEXT("fabrication opens"),
		Progress->IsUnlocked(ELBSpacecraftUnlock::Fabrication));
	TestTrue(TEXT("quality control opens"),
		Progress->IsUnlocked(ELBSpacecraftUnlock::QualityControl));
	TestTrue(TEXT("and the extra crew can now be bought"),
		ALBSpacecraftGameMode::InstallStationDronePowered(*Rig.Build,
			LineId, Reason, nullptr, Progress));

	Rig.World->DestroyWorld(false);
	return true;
}

IMPLEMENT_SIMPLE_AUTOMATION_TEST(FLBSpacecraftInspectionSweepTest,
	"LineBoss.Spacecraft.Presentation.TheInspectionSweepFindsFaultsAsItGoes",
	EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)

bool FLBSpacecraftInspectionSweepTest::RunTest(const FString& Parameters)
{
	(void)Parameters;
	using Catalog = FLBSpacecraftProductionCatalog;
	using Presenter = ALBSpacecraftWIPPresentationActor;

	// Faults are FOUND as the sweep passes over them, not announced at
	// the end. Rounding up means the first one shows the moment the
	// scan starts rather than half way through.
	TestEqual(TEXT("a clean craft has nothing to find"),
		Catalog::DefectsFoundByScan(0, 0.5f), 0);
	TestEqual(TEXT("nothing is found before the sweep starts"),
		Catalog::DefectsFoundByScan(4, 0.f), 0);
	TestEqual(TEXT("the first fault shows early"),
		Catalog::DefectsFoundByScan(4, 0.01f), 1);
	TestEqual(TEXT("half way finds half"),
		Catalog::DefectsFoundByScan(4, 0.5f), 2);
	TestEqual(TEXT("a finished sweep has found them all"),
		Catalog::DefectsFoundByScan(4, 1.f), 4);
	TestEqual(TEXT("and never more than there are"),
		Catalog::DefectsFoundByScan(4, 9.f), 4);

	// The bar reads the owner's palette: blue-white clean, warning
	// orange as faults mount. Never a colour invented for the moment.
	const FLinearColor Clean = Presenter::InspectionSweepColour(0, 4);
	const FLinearColor Bad = Presenter::InspectionSweepColour(4, 4);
	TestTrue(TEXT("a clean scan reads blue-white"),
		Clean.B > Clean.R);
	TestTrue(TEXT("a faulty scan turns warning orange"),
		Bad.R > Bad.B);
	const FLinearColor Half = Presenter::InspectionSweepColour(2, 4);
	TestTrue(TEXT("and it shifts as faults are found, not all at once"),
		Half.R > Clean.R && Half.R < Bad.R);
	// Degenerate inputs must not produce a black bar.
	const FLinearColor NoneOfNone = Presenter::InspectionSweepColour(0, 0);
	TestTrue(TEXT("an empty scan still shows a colour"),
		NoneOfNone.B > 0.f);
	return true;
}

IMPLEMENT_SIMPLE_AUTOMATION_TEST(FLBSpacecraftPartsMarkTest,
	"LineBoss.Spacecraft.Phase2.ABiggerPartsMarkRunsTheSameRecipesFaster",
	EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)

bool FLBSpacecraftPartsMarkTest::RunTest(const FString& Parameters)
{
	(void)Parameters;
	using Build = ALBSpacecraftBuildAuthority;

	const FLBSpacecraftStationDefinition* Mk1 =
		Build::FindDefinition(FName(TEXT("RollingMill")));
	const FLBSpacecraftStationDefinition* Mk2 =
		Build::FindDefinition(FName(TEXT("RollingMillMk2")));
	TestNotNull(TEXT("the mill exists"), Mk1);
	TestNotNull(TEXT("and so does its bigger mark"), Mk2);
	if (Mk1 == nullptr || Mk2 == nullptr)
	{
		return false;
	}

	// A bigger mark runs the SAME recipes - it points at the mark below
	// it rather than carrying a duplicate table, which is what stops
	// the recipe list, the hall's "is this a machine" test and the
	// research validator all disagreeing about what it is.
	TestEqual(TEXT("the mark below it owns the recipes"),
		Mk2->GetRecipeClassId(), Mk1->DefinitionId);
	TestEqual(TEXT("a Mk1 answers for itself"),
		Mk1->GetRecipeClassId(), Mk1->DefinitionId);
	TestTrue(TEXT("and those recipes really exist"),
		FLBSpacecraftRecipeCatalogue::GetRecipesForStationClass(
			Mk2->GetRecipeClassId()).Num() > 0);

	// It is an UPGRADE: faster, roomier, dearer, hungrier.
	TestTrue(TEXT("the bigger mark works faster"),
		Mk2->CraftSpeedMultiplier > Mk1->CraftSpeedMultiplier);
	TestTrue(TEXT("holds more feedstock"),
		Mk2->InputStockpileUnits > Mk1->InputStockpileUnits);
	TestTrue(TEXT("costs more"), Mk2->CostPence > Mk1->CostPence);
	TestTrue(TEXT("and draws more for it"),
		Mk2->PowerDrawKw > Mk1->PowerDrawKw);
	TestTrue(TEXT("it is still a parts machine, not a route mark"),
		Mk2->StageClassId.IsNone());

	// Every family got one, and each points at its own Mk1.
	int32 Marks = 0;
	for (const FLBSpacecraftStationDefinition& Definition :
		Build::StationCatalogue())
	{
		if (Definition.RecipeClassId.IsNone())
		{
			continue;
		}
		++Marks;
		TestNotNull(TEXT("a mark's recipe class is a real family"),
			Build::FindDefinition(Definition.RecipeClassId));
		TestTrue(TEXT("and that family really crafts"),
			FLBSpacecraftRecipeCatalogue::GetRecipesForStationClass(
				Definition.RecipeClassId).Num() > 0);
	}
	TestEqual(TEXT("all nine families have a bigger mark"), Marks, 9);

	// The upgrade is EARNED, at the end of the tree.
	const FLBSpacecraftResearchNode* Node =
		FLBSpacecraftResearchCatalogue::FindNode(
			FName(TEXT("Research.Mfg.PartsMk2")));
	TestNotNull(TEXT("the parts upgrade is a research node"), Node);
	if (Node != nullptr)
	{
		TestEqual(TEXT("it opens all nine marks"),
			Node->UnlockedStationClasses.Num(), 9);
		TestTrue(TEXT("and sits behind the last tier"),
			Node->Prerequisites.Contains(FName(TEXT("Research.Mfg.T4"))));
	}
	return true;
}

IMPLEMENT_SIMPLE_AUTOMATION_TEST(FLBSpacecraftStrandedCraftTest,
	"LineBoss.Spacecraft.Phase2.AFinishedCraftIsNeverStrandedOnTheLine",
	EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)

bool FLBSpacecraftStrandedCraftTest::RunTest(const FString& Parameters)
{
	(void)Parameters;
	using namespace LBSpacecraftPhase2IntegrationTestsPrivate;
	FLBSpacecraftPhase2Rig Rig = MakeSpacecraftPhase2Rig();
	FString Reason;

	// A crewed line, stocked, building one craft against one order.
	const TCHAR* Classes[] = {
		TEXT("MaterialProcessor"), TEXT("HullFabricator"),
		TEXT("ComponentFabricator"), TEXT("AssemblyRobot") };
	float Y = -4000.f;
	for (const TCHAR* ClassId : Classes)
	{
		FName StationId;
		TestTrue(TEXT("line station places"),
			Rig.Build->PlaceStation(FName(ClassId),
				FTransform(FRotator::ZeroRotator, FVector(0.f, Y, 0.f)),
				StationId, Reason));
		for (int32 Crew = 0; Crew < 2; ++Crew)
		{
			TestTrue(TEXT("crewed"),
				Rig.Build->InstallStationDrone(StationId, Reason));
		}
		Y += 2200.f;
	}
	TestTrue(TEXT("the line commissions"),
		EnsureSprayBoothAndCommission(Rig, Reason));
	ALBSpacecraftGameMode::SyncStationStores(*Rig.Build, *Rig.Inventory,
		Rig.Crafting);
	for (const FLBSpacecraftStationRecord& Record : Rig.Build->GetStations())
	{
		const FName Stockpile(*FString::Printf(TEXT("Store.%s"),
			*Record.StationId.ToString()));
		for (const FName& Component : Record.AllocatedComponents)
		{
			Rig.Inventory->Deposit(Stockpile, Component, 2, Reason);
		}
	}
	Rig.Coordinator->BindInventory(Rig.Inventory);
	TestTrue(TEXT("configured"),
		Rig.Coordinator->ConfigureFromAuthorities(Rig.Build, Rig.Production,
			Reason));

	FLBSpacecraftContract Order;
	Order.ContractId = FName(TEXT("C-DOOMED"));
	Order.RecipeId = FName(TEXT("SCOUT-01"));
	Order.Quantity = 1;
	Order.PricePerUnitPence = 15000000;
	// A deadline it will miss WHILE THE CRAFT IS STILL ON THE LINE -
	// deadlines are new, and this is the case they create.
	Order.DeadlineSimSeconds = 400.0;
	TestTrue(TEXT("offered"), Rig.Production->OfferContract(Order, Reason));
	TestTrue(TEXT("accepted"),
		Rig.Production->AcceptContract(Order.ContractId, Reason));

	// Run long past the deadline. The order expires mid-build and the
	// craft finishes with nothing to settle against.
	for (int32 Tick = 0; Tick < 400; ++Tick)
	{
		Rig.Coordinator->TickProduction(10.0, Reason);
	}

	// THE CLAIM: a finished craft is never stranded. Either it was
	// delivered, or it is off the line and waiting to be sold - what it
	// must NOT be is parked at the last station forever, blocking
	// everything behind it with no way out.
	int32 OnTheLine = 0;
	for (const FLBSpacecraftRuntimeAssignment& Assignment :
		Rig.Coordinator->GetAssignments())
	{
		const FLBSpacecraftUnitState* Unit =
			Rig.Production->FindUnit(Assignment.UnitId);
		if (Unit != nullptr && Unit->Stage == ELBSpacecraftStage::Testing)
		{
			++OnTheLine;
		}
	}
	if (OnTheLine > 0)
	{
		AddInfo(FString::Printf(TEXT("line held: %s"),
			*Rig.Coordinator->GetLastHoldReason()));
	}
	TestEqual(TEXT("no finished craft is stuck at the gate"), OnTheLine, 0);

	// It rolled off into STOCK: built, unsold, and out of everyone's
	// way. That is the whole point - the line keeps moving.
	TestEqual(TEXT("the craft is standing in finished stock"),
		Rig.Production->GetStockedCraftCount(), 1);
	TestEqual(TEXT("and was not paid for, because nobody bought it"),
		Rig.Production->GetRevenuePence(), static_cast<int64>(0));

	// A later order buys it off the shelf, on the clock, with no
	// rebuilding.
	FLBSpacecraftContract Buyer;
	Buyer.ContractId = FName(TEXT("C-BUYER"));
	Buyer.RecipeId = FName(TEXT("SCOUT-01"));
	Buyer.Quantity = 1;
	Buyer.PricePerUnitPence = 15000000;
	TestTrue(TEXT("a new order arrives"),
		Rig.Production->OfferContract(Buyer, Reason));
	TestTrue(TEXT("and is accepted"),
		Rig.Production->AcceptContract(Buyer.ContractId, Reason));
	TestTrue(TEXT("the clock turns"),
		Rig.Production->AdvanceSimSeconds(1.0, Reason));

	TestEqual(TEXT("the craft sold out of stock"),
		Rig.Production->GetStockedCraftCount(), 0);
	TestTrue(TEXT("and was paid for"),
		Rig.Production->GetRevenuePence() > 0);
	const FLBSpacecraftContract* Settled =
		Rig.Production->FindContract(Buyer.ContractId);
	TestNotNull(TEXT("the order survives"), Settled);
	if (Settled != nullptr)
	{
		TestEqual(TEXT("and completed from stock"), Settled->State,
			ELBSpacecraftContractState::Complete);
	}

	Rig.World->DestroyWorld(false);
	return true;
}

/**
 * THE ASSEMBLED SIM STEP, not its parts.
 *
 * Both faults of 2026-08-29 lived in TickWholeSimStep - the clock behind
 * LB.Spacecraft.Run, .Jump and .AutoPlay. It did not tick the drone haulers,
 * and it did not sync station stores; both ran only from the actor tick. A
 * headed session was perfect and every console-driven run starved at the head
 * of the line on a hull whose parts sat in the delivery dock.
 *
 * 130 tests passed throughout, because every one of them hand-called
 * SyncStationStores, TickCraftingStations and TickHauls in sequence. They
 * proved each part worked. Nothing proved the assembled step called them.
 *
 * So this test calls the step and NOTHING else. If an authority is dropped
 * from it again, this fails.
 */
IMPLEMENT_SIMPLE_AUTOMATION_TEST(
	FLBSpacecraftSimStepFeedsTheLineTest,
	"LineBoss.Spacecraft.SimClock.TheStepFeedsTheLineByItself",
	EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)

bool FLBSpacecraftSimStepFeedsTheLineTest::RunTest(const FString& Parameters)
{
	(void)Parameters;
	using namespace LBSpacecraftPhase2IntegrationTestsPrivate;
	FLBSpacecraftPhase2Rig Rig = MakeSpacecraftPhase2Rig();
	FString Reason;

	FName RackId;
	TestTrue(TEXT("a storage rack places"),
		Rig.Build->PlaceStation(FName(TEXT("StorageRack")),
			FTransform(FRotator::ZeroRotator,
				FVector(-4400.f, 2500.f, 0.f)), RackId, Reason));
	FName StationId;
	TestTrue(TEXT("a fitting station places"),
		Rig.Build->PlaceStation(FName(TEXT("AssemblyRobot")),
			FTransform(FRotator::ZeroRotator,
				FVector(0.f, 0.f, 0.f)), StationId, Reason));
	for (int32 Crew = 0; Crew < 2; ++Crew)
	{
		TestTrue(TEXT("the station is crewed"),
			Rig.Build->InstallStationDrone(StationId, Reason));
	}
	TestTrue(TEXT("the factory commissions"),
		EnsureSprayBoothAndCommission(Rig, Reason));
	TestTrue(TEXT("the coordinator configures"),
		Rig.Coordinator->ConfigureFromAuthorities(Rig.Build,
			Rig.Production, Reason));

	// A STATION PLACED AND NEVER TOUCHED BY THE ACTOR TICK. This is the
	// console player's situation exactly, and it is where the second
	// fault lived: the station carried a fitting allocation with
	// nowhere to hold parts.
	const FName Stockpile(*FString::Printf(TEXT("Store.%s"),
		*StationId.ToString()));
	TestFalse(TEXT("the station starts with no stockpile"),
		Rig.Inventory->HasStore(Stockpile));

	const FLBSpacecraftSaveContext Context = Rig.Context();
	int32 Cycles = 0;
	FString StepReason;
	TestTrue(TEXT("one whole sim step runs"),
		ALBSpacecraftGameMode::TickWholeSimStep(Context, 1.0, StepReason,
			Cycles));

	// FAULT TWO: the step must give the station its stockpile.
	TestTrue(TEXT("the step gave the station its stockpile"),
		Rig.Inventory->HasStore(Stockpile));

	// FAULT ONE: the step must move the haulers. Stock a component in
	// the rack that the station is allocated to fit, then run the step
	// long enough to cover a haul, and it must arrive.
	const FLBSpacecraftStationRecord* Record =
		Rig.Build->FindStation(StationId);
	TestNotNull(TEXT("the station record survives"), Record);
	if (Record == nullptr || Record->AllocatedComponents.Num() == 0)
	{
		AddError(TEXT("the commissioned station fits nothing, so this "
			"test cannot tell a stalled hauler from an idle one"));
		Rig.World->DestroyWorld(false);
		return false;
	}
	const FName Wanted = Record->AllocatedComponents[0];
	const FName RackStore(*FString::Printf(TEXT("Store.%s"),
		*RackId.ToString()));
	Rig.Inventory->Deposit(RackStore, Wanted, 4, Reason);
	TestEqual(TEXT("the part starts in the rack"),
		Rig.Inventory->GetQuantity(RackStore, Wanted), 4);

	for (int32 Step = 0; Step < 120; ++Step)
	{
		ALBSpacecraftGameMode::TickWholeSimStep(Context, 1.0, StepReason,
			Cycles);
	}

	// The hauler had 120 sim seconds against a travel time measured in
	// tens. Before the fix it got none of them, because the step never
	// called TickHauls at all.
	TestTrue(TEXT("a hauler carried the part to the station"),
		Rig.Inventory->GetQuantity(Stockpile, Wanted) > 0);

	Rig.World->DestroyWorld(false);
	return true;
}
