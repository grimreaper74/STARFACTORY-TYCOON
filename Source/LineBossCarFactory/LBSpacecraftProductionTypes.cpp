#include "LBSpacecraftProductionTypes.h"
// For the component -> inventory item id mapping the fixing order needs.
#include "LBSpacecraftInventoryAuthority.h"

namespace LBSpacecraftProductionTypesPrivate
{
	// Unity-build safety: helpers are qualified by subject (the documented
	// IsFiniteVector collision lesson).
	FLBSpacecraftStageDescriptor MakeSpacecraftStage(ELBSpacecraftStage Stage,
		const TCHAR* DisplayName, FName StationClassId, bool bQualityGate,
		std::initializer_list<ELBSpacecraftComponent> Produced)
	{
		FLBSpacecraftStageDescriptor Row;
		Row.Stage = Stage;
		Row.DisplayName = DisplayName;
		Row.StationClassId = StationClassId;
		Row.bQualityGate = bQualityGate;
		Row.ComponentsProduced = Produced;
		return Row;
	}

	const TCHAR* SpacecraftStageName(ELBSpacecraftStage Stage)
	{
		switch (Stage)
		{
		case ELBSpacecraftStage::MaterialIntake: return TEXT("MaterialIntake");
		case ELBSpacecraftStage::MaterialProcessing: return TEXT("MaterialProcessing");
		case ELBSpacecraftStage::HullFabrication: return TEXT("HullFabrication");
		case ELBSpacecraftStage::ComponentFabrication: return TEXT("ComponentFabrication");
		case ELBSpacecraftStage::AssemblyStaging: return TEXT("AssemblyStaging");
		case ELBSpacecraftStage::Assembly: return TEXT("Assembly");
		case ELBSpacecraftStage::Testing: return TEXT("Testing");
		case ELBSpacecraftStage::Dispatched: return TEXT("Dispatched");
		default: return TEXT("INVALID");
		}
	}
}

const TArray<FLBSpacecraftStageDescriptor>& FLBSpacecraftProductionCatalog::StageTable()
{
	using namespace LBSpacecraftProductionTypesPrivate;
	// ONE station class serves every line stage since 2026-08-27 (owner:
	// "one station type like car manufacturer... but with our drones
	// instead of robots"). The stages remain the PRODUCT's ladder - what
	// has happened to the craft - while the stations are however many
	// the player placed; the route maps one onto the other.
	static const TArray<FLBSpacecraftStageDescriptor> Table = {
		// Raw material arrives; no station of its own in the slice - the
		// MaterialProcessor's input buffer services it.
		MakeSpacecraftStage(ELBSpacecraftStage::MaterialIntake,
			TEXT("Material intake"), FName(TEXT("LineStation")), false, {}),
		MakeSpacecraftStage(ELBSpacecraftStage::MaterialProcessing,
			TEXT("Material processing"), FName(TEXT("LineStation")), false, {}),
		MakeSpacecraftStage(ELBSpacecraftStage::HullFabrication,
			TEXT("Hull fabrication"), FName(TEXT("LineStation")), false,
			{ ELBSpacecraftComponent::Hull }),
		// One component station in the 5-station slice produces the five
		// non-hull components; later tiers split this into parallel lines.
		MakeSpacecraftStage(ELBSpacecraftStage::ComponentFabrication,
			TEXT("Component fabrication"), FName(TEXT("LineStation")), false,
			{ ELBSpacecraftComponent::Electronics, ELBSpacecraftComponent::Power,
			  ELBSpacecraftComponent::Propulsion, ELBSpacecraftComponent::Navigation,
			  ELBSpacecraftComponent::Interior }),
		MakeSpacecraftStage(ELBSpacecraftStage::AssemblyStaging,
			TEXT("Assembly staging"), FName(TEXT("LineStation")), false, {}),
		MakeSpacecraftStage(ELBSpacecraftStage::Assembly,
			TEXT("Assembly"), FName(TEXT("LineStation")), false, {}),
		// The hover test - the slice's quality gate.
		MakeSpacecraftStage(ELBSpacecraftStage::Testing,
			TEXT("Engine test and inspection"), NAME_None, true, {}),
			// Station-less (owner 2026-08-26): the self-start hover AT
			// the end of the line IS the test - no test-bay station.
		MakeSpacecraftStage(ELBSpacecraftStage::Dispatched,
			TEXT("Dispatched"), NAME_None, false, {}),
	};
	return Table;
}

bool FLBSpacecraftProductionCatalog::ValidateStageTable(FString& OutError)
{
	using namespace LBSpacecraftProductionTypesPrivate;
	const TArray<FLBSpacecraftStageDescriptor>& Table = StageTable();
	if (Table.Num() == 0)
	{
		OutError = TEXT("SPACECRAFT STAGE TABLE IS EMPTY");
		return false;
	}

	TSet<ELBSpacecraftStage> Seen;
	TSet<ELBSpacecraftComponent> Produced;
	bool bSawQualityGate = false;
	for (int32 Index = 0; Index < Table.Num(); ++Index)
	{
		const FLBSpacecraftStageDescriptor& Row = Table[Index];
		if (static_cast<int32>(Row.Stage) != Index)
		{
			OutError = FString::Printf(
				TEXT("STAGE TABLE ROW %d IS OUT OF ORDER (%s)"), Index,
				SpacecraftStageName(Row.Stage));
			return false;
		}
		bool bAlready = false;
		Seen.Add(Row.Stage, &bAlready);
		if (bAlready)
		{
			OutError = FString::Printf(TEXT("DUPLICATE STAGE %s"),
				SpacecraftStageName(Row.Stage));
			return false;
		}
		if (Row.DisplayName.IsEmpty())
		{
			OutError = FString::Printf(TEXT("STAGE %s HAS NO DISPLAY NAME"),
				SpacecraftStageName(Row.Stage));
			return false;
		}
		const bool bTerminal = Index == Table.Num() - 1;
		// A station-less mid-route stage is legal ONLY as the quality
		// gate: the self-start test happens in place at the end of the
		// line (owner 2026-08-26). Anything else with no station is
		// still a table defect.
		if (!bTerminal && Row.StationClassId.IsNone()
			&& !Row.bQualityGate)
		{
			OutError = FString::Printf(
				TEXT("NON-TERMINAL STAGE %s HAS NO STATION CLASS"),
				SpacecraftStageName(Row.Stage));
			return false;
		}
		if (bTerminal && !Row.StationClassId.IsNone())
		{
			OutError = TEXT("TERMINAL STAGE MUST NOT CLAIM A STATION CLASS");
			return false;
		}
		bSawQualityGate |= Row.bQualityGate;
		for (ELBSpacecraftComponent Component : Row.ComponentsProduced)
		{
			if (Row.Stage >= ELBSpacecraftStage::Assembly)
			{
				OutError = FString::Printf(
					TEXT("STAGE %s PRODUCES COMPONENTS AT OR AFTER ASSEMBLY"),
					SpacecraftStageName(Row.Stage));
				return false;
			}
			bool bComponentAlready = false;
			Produced.Add(Component, &bComponentAlready);
			if (bComponentAlready)
			{
				OutError = TEXT("A COMPONENT IS PRODUCED BY TWO STAGES");
				return false;
			}
		}
	}
	if (!bSawQualityGate)
	{
		OutError = TEXT("STAGE TABLE HAS NO QUALITY GATE");
		return false;
	}
	OutError.Reset();
	return true;
}

const FLBSpacecraftStageDescriptor* FLBSpacecraftProductionCatalog::FindStage(
	ELBSpacecraftStage Stage)
{
	const TArray<FLBSpacecraftStageDescriptor>& Table = StageTable();
	const int32 Index = static_cast<int32>(Stage);
	return Table.IsValidIndex(Index) ? &Table[Index] : nullptr;
}

bool FLBSpacecraftProductionCatalog::NextStage(ELBSpacecraftStage Stage,
	ELBSpacecraftStage& OutNext)
{
	const TArray<FLBSpacecraftStageDescriptor>& Table = StageTable();
	const int32 Index = static_cast<int32>(Stage);
	if (!Table.IsValidIndex(Index + 1))
	{
		return false;
	}
	OutNext = Table[Index + 1].Stage;
	return true;
}

bool FLBSpacecraftProductionCatalog::IsQualityGate(ELBSpacecraftStage Stage)
{
	const FLBSpacecraftStageDescriptor* Row = FindStage(Stage);
	return Row != nullptr && Row->bQualityGate;
}

int32 FLBSpacecraftProductionCatalog::DefectPointsForCrewQuality(
	int32 InstalledDrones, int32 DroneSlotCount, float CrewQuality)
{
	int32 Points = DefectPointsForCrew(InstalledDrones, DroneSlotCount);
	if (DroneSlotCount <= 0)
	{
		return 0;   // a machine or a building never touches the craft
	}
	// A ROUGH crew bodges one fitting a stop; a FINE crew saves one.
	// The thresholds sit either side of nominal (1.0) so a mixed crew
	// changes nothing and only a committed choice moves the number -
	// the player should be able to feel the decision they made.
	if (CrewQuality < 0.9f)
	{
		++Points;
	}
	else if (CrewQuality > 1.3f)
	{
		Points = FMath::Max(Points - 1, 0);
	}
	return Points;
}

float FLBSpacecraftProductionCatalog::StationReworkSecondsFor(
	int32 PointsAtStation)
{
	// PROVISIONAL: 20 s a point. Long enough that a badly crewed line
	// visibly stutters, short enough that one bad fitting is not a
	// catastrophe.
	return 20.f * static_cast<float>(FMath::Max(PointsAtStation, 0));
}

int32 FLBSpacecraftProductionCatalog::DefectPointsForCrew(
	int32 InstalledDrones, int32 DroneSlotCount)
{
	// Only crewed stations can do bad work. A parts machine or a
	// building has no drone slots and never touches the craft, so it
	// contributes nothing either way.
	if (DroneSlotCount <= 0)
	{
		return 0;
	}
	// Two drones is nominal (ComputeDroneWorkBonus reaches 1.0x there).
	// Every drone short of nominal is one defect: a lone drone rushes
	// the fit, an empty station bodges it entirely.
	constexpr int32 NominalCrew = 2;
	const int32 Shortfall = NominalCrew - FMath::Max(InstalledDrones, 0);
	return FMath::Max(Shortfall, 0);
}

int32 FLBSpacecraftProductionCatalog::DefectsFoundByScan(int32 DefectPoints,
	float Progress01)
{
	const int32 Total = FMath::Max(DefectPoints, 0);
	if (Total == 0)
	{
		return 0;
	}
	const float Clamped = FMath::Clamp(Progress01, 0.f, 1.f);
	return FMath::Clamp(FMath::CeilToInt(Total * Clamped), 0, Total);
}

bool FLBSpacecraftProductionCatalog::DefectsPassHoverTestAt(
	int32 DefectPoints, int32 Tolerance)
{
	return DefectPoints <= FMath::Max(Tolerance, 0);
}

int32 FLBSpacecraftProductionCatalog::TrimPassesRequired(
	int32 DefectPoints, int32 Tolerance)
{
	const int32 Defects = FMath::Max(DefectPoints, 0);
	// Deliberately the SAME test the one-shot gate applied, so this
	// changes how long the pad is busy and never who passes.
	if (!DefectsPassHoverTestAt(Defects, Tolerance))
	{
		return INDEX_NONE;   // will not settle; it owes rework
	}
	// A clean craft settles on the first pass. Each defect it is
	// carrying - within tolerance, so still airworthy - costs one more
	// run-measure-adjust cycle before the residual is inside limits.
	return 1 + Defects;
}

float FLBSpacecraftProductionCatalog::TrimResidualDeg(
	int32 DefectPoints, int32 PassIndex)
{
	const int32 Defects = FMath::Max(DefectPoints, 0);
	if (Defects <= 0)
	{
		return 0.f;   // dead level, and the thrusters have nothing to do
	}
	// Geometric decay: each pass takes out most of what is left, which
	// is how a real track-and-balance session converges - big first
	// correction, diminishing trims after it.
	constexpr float BaseDegPerDefect = 0.45f;
	constexpr float PassGain = 0.4f;
	const float Passes = static_cast<float>(FMath::Max(PassIndex, 0));
	return BaseDegPerDefect * static_cast<float>(Defects)
		* FMath::Pow(PassGain, Passes);
}

FVector FLBSpacecraftProductionCatalog::FactoryMaxCraftEnvelopeCm()
{
	// ONE PLACE. Change it here and the gantry, the validation and
	// anything else that must clear a craft all move together.
	//
	// SIZED FOR WHAT EARLY ACCESS SHIPS (owner: "we're aiming at 2 tier
	// for early access but as big as we can go after") - Scout at 14 m
	// and Cargo at 21 m, and this is the Mk2 station envelope that
	// already holds them both.
	//
	// It was 3600 x 2100 x 1050, a guess at a tier six that has no
	// dimensions yet, and over-building has a measured cost: the hall
	// had to be 180 m square to suit it, which left the entire starting
	// line occupying 3.9% of the floor. A factory built for ships that
	// do not exist looks empty, and no amount of props fixes a floor
	// that is 96% bare by design.
	//
	// THIS NUMBER IS EXPECTED TO RISE. Post-EA craft get bigger, and
	// when they do this moves with the hall and gantry marks that admit
	// them - the same way a Mk1 station refuses a Cargo craft today and
	// names the bigger mark. It is a design ceiling for the current
	// build, not a promise about the ladder.
	//
	// LOWERED 2026-08-29 TO WHAT THE LINE CAN ACTUALLY DELIVER. It read
	// 2400 x 1400 x 700, matching the Mk2 line stations - but the SPRAY
	// BOOTH tops out at 2200 x 1250 x 700 and has no larger mark, so a
	// craft between those two sizes passed this check, was told the
	// factory was built for it, and was then refused at the booth.
	//
	// Both refusals were misleading in that band: this one says "NO
	// STATION MARK CAN HELP" when a mark would have, and the station
	// check says "A LARGER STATION MARK IS REQUIRED" for a station that
	// has none. A ceiling that overstates the line is worse than a low
	// one, because it turns a clear refusal into a contradiction.
	//
	// The booth's own envelope is NOT the mistake - it was sized
	// deliberately so the first booth still admits a Cargo at 1.5x the
	// Scout. The mistake was this constant drifting above it. Raise
	// them together, or not at all.
	// The spray booth's envelope, because the booth is the tightest
	// station on the route and the ceiling may never claim more than
	// the narrowest thing a craft has to pass through.
	return FVector(2200.f, 1250.f, 700.f);
}

float FLBSpacecraftProductionCatalog::WidestLineStationAcrossCm()
{
	// Assembly station Mk2, whose footprint is 2700 x 2100. The larger
	// axis, because a station placed at a quarter turn swaps them and
	// the portal has to clear either choice.
	return 2700.f;
}

float FLBSpacecraftProductionCatalog::GantryRailSpanCm()
{
	// Working room BOTH SIDES, not just enough to squeeze past: drones
	// fit parts alongside a craft that the gantry is holding, and a
	// portal sized to the hull exactly would put its legs where the
	// drones work.
	constexpr float ClearanceEachSideCm = 450.f;
	const float ForTheCraft =
		FactoryMaxCraftEnvelopeCm().Y + ClearanceEachSideCm * 2.f;

	// AND the stations it drives over. The legs stand outboard of the
	// widest station with enough room that they do not clip its corner
	// as the portal travels past.
	constexpr float LegClearanceEachSideCm = 150.f;
	const float ForTheStations =
		WidestLineStationAcrossCm() + LegClearanceEachSideCm * 2.f;

	return FMath::Max(ForTheCraft, ForTheStations);
}

bool FLBSpacecraftProductionCatalog::ValidateCraftFitsFactory(
	const FLBSpacecraftRecipe& Recipe, FString& OutError)
{
	const FVector Limit = FactoryMaxCraftEnvelopeCm();
	const FVector& Craft = Recipe.CraftEnvelopeCm;
	if (Craft.X > Limit.X || Craft.Y > Limit.Y || Craft.Z > Limit.Z)
	{
		OutError = FString::Printf(
			TEXT("%s IS %.0fx%.0fx%.0f CM, LARGER THAN THE FACTORY IS ")
			TEXT("BUILT FOR (%.0fx%.0fx%.0f CM). NO STATION MARK CAN ")
			TEXT("HELP - THE GANTRY COULD NOT CARRY IT BETWEEN STATIONS"),
			*Recipe.RecipeId.ToString(), Craft.X, Craft.Y, Craft.Z,
			Limit.X, Limit.Y, Limit.Z);
		return false;
	}
	return true;
}

bool FLBSpacecraftProductionCatalog::DefectsPassHoverTest(int32 DefectPoints)
{
	// The shipped tolerance. The coordinator asks with the
	// difficulty's tolerance instead; this stays for callers that
	// mean "the default rule".
	return DefectsPassHoverTestAt(DefectPoints,
		HoverTestDefectTolerance);
}

float FLBSpacecraftProductionCatalog::ReworkSecondsFor(int32 DefectPoints)
{
	// PROVISIONAL, pending the owner's economy tuning: 90 s a defect
	// with a 120 s floor, so a failure always costs real line time and
	// a badly-crewed craft costs proportionally more.
	const float Owed = 90.f * static_cast<float>(FMath::Max(DefectPoints, 0));
	return FMath::Max(Owed, 120.f);
}

int32 FLBSpacecraftProductionCatalog::ComponentCountFor(
	const FLBSpacecraftRecipe& Recipe, ELBSpacecraftComponent Component)
{
	const int32* Count = Recipe.ComponentCounts.Find(Component);
	// Absent means one, so every recipe written before counts existed
	// keeps exactly the behaviour it had. Floored at one because a
	// required component nobody consumes is a contradiction the rest of
	// the line cannot express.
	return Count != nullptr ? FMath::Max(*Count, 1) : 1;
}

int32 FLBSpacecraftProductionCatalog::ComponentCountForItem(
	const FLBSpacecraftRecipe& Recipe, FName ComponentItemId)
{
	for (ELBSpacecraftComponent Component : Recipe.RequiredComponents)
	{
		if (FLBSpacecraftItemCatalogue::GetAssembledComponentItemId(
			static_cast<uint8>(Component)) == ComponentItemId)
		{
			return ComponentCountFor(Recipe, Component);
		}
	}
	// Not a component of this craft: one, so a caller holding an
	// unrelated item id gets the old behaviour rather than a zero that
	// would silently make it free.
	return 1;
}

void FLBSpacecraftProductionCatalog::ComponentsEarnedBy(
	ELBSpacecraftStage Stage, TArray<ELBSpacecraftComponent>& OutComponents)
{
	OutComponents.Reset();
	const TArray<FLBSpacecraftStageDescriptor>& Table = StageTable();
	const int32 Last = FMath::Min(static_cast<int32>(Stage),
		Table.Num() - 1);
	// INCLUSIVE of the entry row. AdvanceUnit applies a row's output on
	// ENTERING it, and a unit CREATED at that row never enters it - so
	// a craft standing at row k has already been credited with row k's
	// output. Getting this bound wrong by one silently hands the player
	// a free component or charges them for one they never received.
	for (int32 Index = 0; Index <= Last; ++Index)
	{
		for (ELBSpacecraftComponent Component :
			Table[Index].ComponentsProduced)
		{
			OutComponents.AddUnique(Component);
		}
	}
}

void FLBSpacecraftProductionCatalog::ComponentsRefittedFrom(
	ELBSpacecraftStage Stage, TArray<ELBSpacecraftComponent>& OutComponents)
{
	OutComponents.Reset();
	const TArray<FLBSpacecraftStageDescriptor>& Table = StageTable();
	const int32 First = FMath::Max(static_cast<int32>(Stage), 0);
	// EXCLUSIVE of the entry row, which is the mirror of the rule
	// above: the craft arrives already credited with row k, so row k is
	// work it is NOT paying to have done again.
	for (int32 Index = First + 1; Index < Table.Num(); ++Index)
	{
		for (ELBSpacecraftComponent Component :
			Table[Index].ComponentsProduced)
		{
			OutComponents.AddUnique(Component);
		}
	}
}

float FLBSpacecraftProductionCatalog::RefitWorkFraction(
	ELBSpacecraftStage EntryStage)
{
	TArray<ELBSpacecraftComponent> Refitted;
	ComponentsRefittedFrom(EntryStage, Refitted);

	// The whole-craft total is counted DIRECTLY rather than by asking
	// ComponentsRefittedFrom for a stage before the first one. That
	// trick works only while row 0 happens to produce nothing, which is
	// true today and is not a property anybody promised.
	TArray<ELBSpacecraftComponent> Whole;
	for (const FLBSpacecraftStageDescriptor& Row : StageTable())
	{
		for (ELBSpacecraftComponent Component : Row.ComponentsProduced)
		{
			Whole.AddUnique(Component);
		}
	}
	if (Whole.Num() <= 0)
	{
		return 0.f;
	}
	return static_cast<float>(Refitted.Num())
		/ static_cast<float>(Whole.Num());
}

bool FLBSpacecraftProductionCatalog::IsLegalRefitEntryStage(
	ELBSpacecraftStage EntryStage, FString& OutReason)
{
	const TArray<FLBSpacecraftStageDescriptor>& Table = StageTable();
	const int32 Index = static_cast<int32>(EntryStage);
	if (Index < 0 || Index >= Table.Num())
	{
		OutReason = TEXT("THAT IS NOT A STAGE ON THE LADDER");
		return false;
	}
	if (IsQualityGate(EntryStage) || EntryStage == ELBSpacecraftStage::Dispatched)
	{
		// The hover test is not work anyone buys, and a craft cannot
		// re-enter at the exit.
		OutReason = TEXT(
			"A REFIT CANNOT START AT THE TEST GATE OR AT DISPATCH");
		return false;
	}
	TArray<ELBSpacecraftComponent> Refitted;
	ComponentsRefittedFrom(EntryStage, Refitted);
	if (Refitted.Num() <= 0)
	{
		// The refusal names the fix rather than the rule: stages past
		// component fabrication fit nothing, so entering there buys a
		// price for standing still.
		// FindStage rather than the file-local terse name: this
		// refusal is shown to the player, so it wants the display
		// name, and the helper is out of scope here anyway.
		const FLBSpacecraftStageDescriptor* Row = FindStage(EntryStage);
		OutReason = FString::Printf(
			TEXT("NOTHING IS REFITTED FROM %s - START THE REFIT EARLIER"),
			Row != nullptr ? *Row->DisplayName : TEXT("THAT STAGE"));
		return false;
	}
	OutReason.Reset();
	return true;
}

int32 FLBSpacecraftProductionCatalog::MaxConcedableDefectPoints()
{
	// PROVISIONAL, pending the owner's economy tuning. Set against the
	// hover test's own tolerance so the two dials stay related: a
	// concession covers a craft that is OVER the line but not far over.
	// Past this the board has no discretion and the craft is reworked
	// or scrapped, which is what stops a concession from becoming a
	// flat fee that retires the quality gate.
	return 6;
}

int32 FLBSpacecraftProductionCatalog::ConcessionDeductionPercent(
	int32 DefectPoints)
{
	// PROVISIONAL. Deliberately steeper per defect than the 10% a
	// failed test costs, because a concession buys back the REWORK
	// TIME as well - if it were cheaper than reworking on both counts
	// nobody would ever rework, and the disposition would stop being a
	// decision. Capped so a concession never costs more than the craft
	// earns; a negative settlement would be a bug wearing a mechanic's
	// coat.
	const int32 Owed = 8 + 6 * FMath::Max(DefectPoints, 0);
	return FMath::Clamp(Owed, 8, 45);
}

int32 FLBSpacecraftProductionCatalog::ConcessionReputationCost(
	int32 DefectPoints)
{
	// PROVISIONAL. Small but never zero: shipping known-deviant work
	// is remembered even when it is accepted, and a reputation cost is
	// what stops concessions being a pure cash trade the player can
	// grind. It scales, so waving through more costs more.
	return 1 + FMath::Max(DefectPoints, 0) / 2;
}

bool FLBSpacecraftProductionCatalog::CanConcede(
	const FLBSpacecraftUnitState& Unit, FString& OutReason)
{
	// Every refusal below names the actual obstacle rather than saying
	// no: the fail-closed toasts are this game's tutorial, and a
	// refusal the player cannot act on teaches nothing.
	if (!IsQualityGate(Unit.Stage))
	{
		OutReason = TEXT(
			"A CONCESSION IS SIGNED AT THE TESTING GATE ONLY");
		return false;
	}
	if (Unit.bConcessionGranted)
	{
		// Not idempotent on purpose. A concession costs margin and
		// reputation, so silently accepting a second one would charge
		// twice for one decision.
		OutReason = TEXT("THIS CRAFT ALREADY SHIPS ON A CONCESSION");
		return false;
	}
	if (!Unit.bQualityRecorded)
	{
		OutReason = TEXT("NOTHING TO CONCEDE - THE CRAFT IS UNTESTED");
		return false;
	}
	if (Unit.bQualityPassed)
	{
		// Refused rather than ignored: a player conceding a craft that
		// passed has misread the panel, and charging them for it would
		// be the panel's fault, not theirs.
		OutReason = TEXT("NOTHING TO CONCEDE - THE CRAFT PASSED");
		return false;
	}
	if (Unit.DefectPoints > MaxConcedableDefectPoints())
	{
		OutReason = FString::Printf(
			TEXT("TOO FAR OUT TO SIGN OFF - %d DEFECT POINTS AGAINST A ")
			TEXT("LIMIT OF %d"),
			Unit.DefectPoints, MaxConcedableDefectPoints());
		return false;
	}
	OutReason.Reset();
	return true;
}

ELBSpacecraftStage FLBSpacecraftProductionCatalog::StageForRouteIndex(
	int32 Index, int32 StationCount)
{
	const int32 Rows = StationStageCount();
	if (StationCount <= 0 || Rows <= 0)
	{
		return ELBSpacecraftStage::MaterialIntake;
	}
	const int32 Clamped = FMath::Clamp(Index, 0, StationCount - 1);
	const int32 Row = FMath::Min((Clamped * Rows) / StationCount, Rows - 1);
	return static_cast<ELBSpacecraftStage>(Row);
}

float FLBSpacecraftProductionCatalog::TotalLineSeconds(
	const FLBSpacecraftRecipe& Recipe)
{
	float Total = 0.f;
	for (const FLBSpacecraftStageDescriptor& Row : StageTable())
	{
		if (Row.StationClassId.IsNone())
		{
			continue;
		}
		const float* Seconds = Recipe.NominalCycleSeconds.Find(Row.Stage);
		if (Seconds != nullptr && *Seconds > 0.f)
		{
			Total += *Seconds;
		}
	}
	return Total;
}

float FLBSpacecraftProductionCatalog::StationFitSeconds(
	const FLBSpacecraftRecipe& Recipe, int32 AllocatedCount,
	int32 TotalAllocatedCount, int32 StationCount)
{
	if (StationCount <= 0)
	{
		return -1.f;
	}
	const int32 Allocated = FMath::Max(AllocatedCount, 0);
	const int32 TotalAllocated = FMath::Max(TotalAllocatedCount, Allocated);
	// (+1 per station) keeps an empty station's stop honest - the craft
	// still docks, aligns and undocks - while the denominator keeps the
	// shares summing exactly to the recipe's total line work.
	return TotalLineSeconds(Recipe)
		* static_cast<float>(Allocated + 1)
		/ static_cast<float>(TotalAllocated + StationCount);
}

int32 FLBSpacecraftProductionCatalog::StationStageCount()
{
	int32 Count = 0;
	for (const FLBSpacecraftStageDescriptor& Row : StageTable())
	{
		Count += Row.StationClassId.IsNone() ? 0 : 1;
	}
	return Count;
}

bool FLBSpacecraftProductionCatalog::CanEnterStage(
	const FLBSpacecraftUnitState& Unit, const FLBSpacecraftRecipe& Recipe,
	ELBSpacecraftStage Target, FString& OutReason)
{
	using namespace LBSpacecraftProductionTypesPrivate;
	ELBSpacecraftStage Expected = ELBSpacecraftStage::MaterialIntake;
	if (!NextStage(Unit.Stage, Expected))
	{
		OutReason = TEXT("UNIT IS AT THE TERMINAL STAGE");
		return false;
	}
	if (Target != Expected)
	{
		OutReason = FString::Printf(
			TEXT("SERIAL FLOW ONLY: %s MAY ONLY ADVANCE TO %s, NOT %s"),
			SpacecraftStageName(Unit.Stage), SpacecraftStageName(Expected),
			SpacecraftStageName(Target));
		return false;
	}
	if (Unit.RecipeId != Recipe.RecipeId)
	{
		OutReason = TEXT("UNIT AND RECIPE DO NOT MATCH");
		return false;
	}
	if (Target == ELBSpacecraftStage::Assembly)
	{
		for (ELBSpacecraftComponent Component : Recipe.RequiredComponents)
		{
			if (!Unit.ProducedComponents.Contains(Component))
			{
				OutReason = FString::Printf(
					TEXT("ASSEMBLY REQUIRES A COMPLETE COMPONENT SET; ")
					TEXT("COMPONENT %d IS MISSING"),
					static_cast<int32>(Component));
				return false;
			}
		}
	}
	OutReason.Reset();
	return true;
}

bool FLBSpacecraftProductionCatalog::AdvanceUnit(FLBSpacecraftUnitState& Unit,
	const FLBSpacecraftRecipe& Recipe, FString& OutReason)
{
	ELBSpacecraftStage Target = Unit.Stage;
	if (!NextStage(Unit.Stage, Target))
	{
		OutReason = TEXT("UNIT IS AT THE TERMINAL STAGE");
		return false;
	}
	if (!CanEnterStage(Unit, Recipe, Target, OutReason))
	{
		return false;
	}
	Unit.Stage = Target;
	if (const FLBSpacecraftStageDescriptor* Row = FindStage(Target))
	{
		for (ELBSpacecraftComponent Component : Row->ComponentsProduced)
		{
			Unit.ProducedComponents.AddUnique(Component);
		}
	}
	Unit.bCompleted = Unit.Stage == ELBSpacecraftStage::Dispatched;
	OutReason.Reset();
	return true;
}

const TArray<FLBSpacecraftRecipe>& FLBSpacecraftProductionCatalog::CanonicalRecipes()
{
	static const TArray<FLBSpacecraftRecipe> Recipes = []()
	{
		TArray<FLBSpacecraftRecipe> Out;

		// THE FIXING ORDER, declared ONCE and shared, because internals
		// are shared across craft tiers: a tier differs in quantities
		// and stage times, never in how it goes together.
		//
		// Read it as a build sequence, because that is what it is: the
		// shell first, then the powerplant everything else needs, then
		// the engines it feeds, then the wiring, then the avionics that
		// ride on the wiring, and the cabin last - you do not fit the
		// seats and then climb over them to reach the loom. PROVISIONAL:
		// reorder this one list and the whole line re-sequences.
		//
		// Declared up here rather than copied from Scout because Scout is
		// MoveTemp'd into the array before Cargo is built, and reading a
		// field off a moved-from object compiles clean and yields an
		// empty list. It did exactly that; the fixing-order validator
		// caught it, which is the argument for validating it.
		const TArray<ELBSpacecraftComponent> SharedFixingOrder = {
			ELBSpacecraftComponent::Hull, ELBSpacecraftComponent::Power,
			ELBSpacecraftComponent::Propulsion,
			ELBSpacecraftComponent::Electronics,
			ELBSpacecraftComponent::Navigation,
			ELBSpacecraftComponent::Interior };
		// WHY that order. These edges are the physical reason, and they
		// are deliberately few - only the ones that are actually true of
		// a small crewed craft. The shared order above already satisfies
		// all three, so this DESCRIBES the existing sequence rather than
		// changing it; what it adds is that a future reorder into
		// something impossible now fails validation instead of shipping.
		auto Edge = [](ELBSpacecraftComponent Blocker,
			ELBSpacecraftComponent Blocked)
		{
			FLBSpacecraftAccessEdge Made;
			Made.Blocker = Blocker;
			Made.Blocked = Blocked;
			return Made;
		};
		const TArray<FLBSpacecraftAccessEdge> SharedAccessBlocks = {
			// Cabin trim covers the harness runs behind the panels.
			Edge(ELBSpacecraftComponent::Interior,
				ELBSpacecraftComponent::Electronics),
			// The dash closes over the nav computer.
			Edge(ELBSpacecraftComponent::Interior,
				ELBSpacecraftComponent::Navigation),
			// The engine bay closes over the power bus.
			Edge(ELBSpacecraftComponent::Propulsion,
				ELBSpacecraftComponent::Power) };

		FLBSpacecraftRecipe Scout;
		Scout.RecipeId = FName(TEXT("SCOUT-01"));
		Scout.DisplayName = TEXT("Scout-01");
		Scout.RequiredComponents = {
			ELBSpacecraftComponent::Hull, ELBSpacecraftComponent::Electronics,
			ELBSpacecraftComponent::Power, ELBSpacecraftComponent::Propulsion,
			ELBSpacecraftComponent::Navigation, ELBSpacecraftComponent::Interior };
		Scout.FixingOrder = SharedFixingOrder;
		Scout.AccessBlocks = SharedAccessBlocks;
		Scout.NominalCycleSeconds = {
			{ ELBSpacecraftStage::MaterialIntake, 20.f },
			{ ELBSpacecraftStage::MaterialProcessing, 45.f },
			{ ELBSpacecraftStage::HullFabrication, 90.f },
			{ ELBSpacecraftStage::ComponentFabrication, 75.f },
			{ ELBSpacecraftStage::AssemblyStaging, 30.f },
			{ ELBSpacecraftStage::Assembly, 120.f },
			{ ELBSpacecraftStage::Testing, 60.f } };
		// RETUNED 2026-08-27 with the hundred-part catalogue. Parts are
		// counted per fitted instance now (owner: "car manufacturer has
		// each light and each seat"), so a Scout's bill of materials
		// tripled: importing all six components costs about 119,600 cr.
		// At the old 50,000 the craft sold for less than half its own
		// parts and every delivery lost money - the economy was upside
		// down, not merely mistuned. 150,000 leaves importing everything
		// a thin ~25% margin, which is the documented intent (importing
		// stays a real choice; fabricating is where the money is).
		// PROVISIONAL like every other number here.
		Scout.RevenuePence = 15000000; // 150,000 cr baseline sale price
		// Measured from the imported Scout-01 mesh (14.00 x 7.46 x 3.87 m).
		Scout.CraftEnvelopeCm = FVector(1400.f, 746.f, 387.f);
		Out.Add(MoveTemp(Scout));

		// Cargo-01 - the second tier (EA scope). DELIBERATELY larger than
		// every Mk1 station envelope: the capacity law refuses it on the
		// starter line ("LARGER STATION MARK REQUIRED") until Mk2 marks
		// are placed. Size is 1.5x Scout (owner-approved, 2026-08-25).
		FLBSpacecraftRecipe Cargo;
		Cargo.RecipeId = FName(TEXT("CARGO-01"));
		Cargo.DisplayName = TEXT("Cargo-01");
		Cargo.RequiredComponents = {
			ELBSpacecraftComponent::Hull, ELBSpacecraftComponent::Electronics,
			ELBSpacecraftComponent::Power, ELBSpacecraftComponent::Propulsion,
			ELBSpacecraftComponent::Navigation, ELBSpacecraftComponent::Interior };
		// WHAT MAKES IT A BIGGER CRAFT RATHER THAN A DEARER ONE.
		//
		// Measured against its own bill of materials, a Cargo cost
		// exactly what a Scout cost - 28,485 cr - while selling for
		// 2.4 times as much. Same six components, same quantities, so
		// the second tier was strictly better than the first at every
		// scale. Internals being SHARED across tiers is deliberate;
		// the quantities being shared was simply never implemented.
		//
		// Counted per fitted instance, as a real machine would be: a
		// hauler carries more structure, more generation and a third
		// engine, and doubles the avionics it cannot fly without. That
		// brings materials to roughly 21% of its price against the
		// Scout's measured 19%, so neither tier dominates and the
		// bigger craft is slightly the hungrier to feed.
		Cargo.ComponentCounts = {
			{ ELBSpacecraftComponent::Hull, 3 },
			{ ELBSpacecraftComponent::Power, 3 },
			{ ELBSpacecraftComponent::Propulsion, 3 },
			{ ELBSpacecraftComponent::Electronics, 2 },
			{ ELBSpacecraftComponent::Navigation, 2 },
			{ ELBSpacecraftComponent::Interior, 2 } };
		Cargo.FixingOrder = SharedFixingOrder;
		Cargo.AccessBlocks = SharedAccessBlocks;
		Cargo.NominalCycleSeconds = {
			{ ELBSpacecraftStage::MaterialIntake, 30.f },
			{ ELBSpacecraftStage::MaterialProcessing, 70.f },
			{ ELBSpacecraftStage::HullFabrication, 140.f },
			{ ELBSpacecraftStage::ComponentFabrication, 110.f },
			{ ELBSpacecraftStage::AssemblyStaging, 45.f },
			{ ELBSpacecraftStage::Assembly, 180.f },
			{ ELBSpacecraftStage::Testing, 90.f } };
		Cargo.RevenuePence = 36000000; // 360,000 cr (same 3x retune)
		Cargo.CraftEnvelopeCm = FVector(2100.f, 1119.f, 580.f);
		// Bigger craft need a NAME: reputation tier 2 (PROVISIONAL).
		Cargo.MinReputationTier = 2;
		Out.Add(MoveTemp(Cargo));
		return Out;
	}();
	return Recipes;
}

bool FLBSpacecraftProductionCatalog::FindRecipe(FName RecipeId,
	FLBSpacecraftRecipe& OutRecipe)
{
	for (const FLBSpacecraftRecipe& Recipe : CanonicalRecipes())
	{
		if (Recipe.RecipeId == RecipeId)
		{
			OutRecipe = Recipe;
			return true;
		}
	}
	return false;
}

int32 FLBSpacecraftProductionCatalog::FixingIndexOf(
	const FLBSpacecraftRecipe& Recipe, FName ComponentItemId)
{
	for (int32 Index = 0; Index < Recipe.FixingOrder.Num(); ++Index)
	{
		if (FLBSpacecraftItemCatalogue::GetAssembledComponentItemId(
			static_cast<uint8>(Recipe.FixingOrder[Index]))
				== ComponentItemId)
		{
			return Index;
		}
	}
	return INDEX_NONE;
}

TArray<FName> FLBSpacecraftProductionCatalog::FixingSequenceItemIds(
	const FLBSpacecraftRecipe& Recipe)
{
	TArray<FName> Sequence;
	Sequence.Reserve(Recipe.FixingOrder.Num());
	for (ELBSpacecraftComponent Component : Recipe.FixingOrder)
	{
		const FName ItemId =
			FLBSpacecraftItemCatalogue::GetAssembledComponentItemId(
				static_cast<uint8>(Component));
		if (!ItemId.IsNone())
		{
			Sequence.Add(ItemId);
		}
	}
	return Sequence;
}

bool FLBSpacecraftProductionCatalog::ValidateFixingOrder(
	const FLBSpacecraftRecipe& Recipe, FString& OutError)
{
	if (Recipe.FixingOrder.Num() == 0)
	{
		OutError = TEXT("RECIPE HAS NO FIXING ORDER - THE LINE WOULD NOT ")
			TEXT("KNOW WHAT GOES ON FIRST");
		return false;
	}
	// Same members, no duplicates, none missing, nothing extra. Checked
	// both ways round on purpose: a fixing order that omits a required
	// part would silently never fit it, and one that names a part the
	// recipe does not use would allocate a part that never arrives.
	TSet<ELBSpacecraftComponent> Seen;
	for (ELBSpacecraftComponent Component : Recipe.FixingOrder)
	{
		bool bAlready = false;
		Seen.Add(Component, &bAlready);
		if (bAlready)
		{
			OutError = FString::Printf(
				TEXT("FIXING ORDER FITS COMPONENT %d TWICE"),
				static_cast<int32>(Component));
			return false;
		}
		if (!Recipe.RequiredComponents.Contains(Component))
		{
			OutError = FString::Printf(
				TEXT("FIXING ORDER FITS COMPONENT %d, WHICH THE RECIPE ")
				TEXT("DOES NOT REQUIRE"), static_cast<int32>(Component));
			return false;
		}
	}
	for (ELBSpacecraftComponent Component : Recipe.RequiredComponents)
	{
		if (!Seen.Contains(Component))
		{
			OutError = FString::Printf(
				TEXT("FIXING ORDER NEVER FITS REQUIRED COMPONENT %d"),
				static_cast<int32>(Component));
			return false;
		}
	}
	// ACCESS EDGES. A blocked component must be fitted BEFORE the thing
	// that closes over it, or the order describes an assembly nobody
	// could physically perform. Checked here rather than trusted,
	// because the fixing order is hand-authored and the whole value of
	// writing the edges down is that they are enforced.
	for (const FLBSpacecraftAccessEdge& Block : Recipe.AccessBlocks)
	{
		if (Block.Blocker == Block.Blocked)
		{
			OutError = FString::Printf(
				TEXT("COMPONENT %d IS DECLARED TO BLOCK ITSELF"),
				static_cast<int32>(Block.Blocker));
			return false;
		}
		const int32 BlockerAt = Recipe.FixingOrder.IndexOfByKey(Block.Blocker);
		const int32 BlockedAt = Recipe.FixingOrder.IndexOfByKey(Block.Blocked);
		if (BlockerAt == INDEX_NONE || BlockedAt == INDEX_NONE)
		{
			OutError = FString::Printf(
				TEXT("ACCESS EDGE NAMES COMPONENT %d OR %d, WHICH THIS ")
				TEXT("RECIPE DOES NOT FIT"),
				static_cast<int32>(Block.Blocker),
				static_cast<int32>(Block.Blocked));
			return false;
		}
		if (BlockedAt > BlockerAt)
		{
			OutError = FString::Printf(
				TEXT("FIXING ORDER FITS COMPONENT %d BEFORE COMPONENT %d, ")
				TEXT("BUT %d CLOSES OVER %d - IT COULD NEVER BE REACHED"),
				static_cast<int32>(Block.Blocker),
				static_cast<int32>(Block.Blocked),
				static_cast<int32>(Block.Blocker),
				static_cast<int32>(Block.Blocked));
			return false;
		}
	}
	return true;
}

TArray<ELBSpacecraftComponent> FLBSpacecraftProductionCatalog::BlockersOf(
	const FLBSpacecraftRecipe& Recipe, ELBSpacecraftComponent Component)
{
	TArray<ELBSpacecraftComponent> Blockers;
	for (const FLBSpacecraftAccessEdge& Block : Recipe.AccessBlocks)
	{
		if (Block.Blocked == Component)
		{
			Blockers.AddUnique(Block.Blocker);
		}
	}
	return Blockers;
}

bool FLBSpacecraftProductionCatalog::IsReachableAfter(
	const FLBSpacecraftRecipe& Recipe, ELBSpacecraftComponent Component,
	int32 FittedThroughIndex)
{
	// Nothing fitted yet: the craft is open and everything is reachable.
	if (FittedThroughIndex < 0)
	{
		return true;
	}
	for (const ELBSpacecraftComponent Blocker : BlockersOf(Recipe, Component))
	{
		const int32 BlockerAt = Recipe.FixingOrder.IndexOfByKey(Blocker);
		// An unknown blocker cannot be shown to have closed, and this is
		// a query rather than a gate - ValidateFixingOrder is where a
		// malformed edge is refused. Reporting "unreachable" here on
		// bad data would stop a line for a catalogue typo.
		if (BlockerAt != INDEX_NONE && BlockerAt <= FittedThroughIndex)
		{
			return false;
		}
	}
	return true;
}

bool FLBSpacecraftProductionCatalog::ValidateRecipe(
	const FLBSpacecraftRecipe& Recipe, FString& OutError)
{
	using namespace LBSpacecraftProductionTypesPrivate;
	if (Recipe.RecipeId.IsNone() || Recipe.DisplayName.IsEmpty())
	{
		OutError = TEXT("RECIPE NEEDS AN ID AND A DISPLAY NAME");
		return false;
	}
	if (Recipe.RequiredComponents.Num() == 0)
	{
		OutError = TEXT("RECIPE REQUIRES AT LEAST ONE COMPONENT");
		return false;
	}
	if (Recipe.RevenuePence <= 0)
	{
		OutError = TEXT("RECIPE NEEDS A POSITIVE REVENUE");
		return false;
	}
	if (Recipe.CraftEnvelopeCm.X <= 0.f || Recipe.CraftEnvelopeCm.Y <= 0.f
		|| Recipe.CraftEnvelopeCm.Z <= 0.f)
	{
		OutError = TEXT("RECIPE NEEDS A POSITIVE CRAFT ENVELOPE");
		return false;
	}

	// Every required component must be produced by some pre-Assembly stage.
	TSet<ELBSpacecraftComponent> Producible;
	for (const FLBSpacecraftStageDescriptor& Row : StageTable())
	{
		for (ELBSpacecraftComponent Component : Row.ComponentsProduced)
		{
			Producible.Add(Component);
		}
	}
	for (ELBSpacecraftComponent Component : Recipe.RequiredComponents)
	{
		if (!Producible.Contains(Component))
		{
			OutError = FString::Printf(
				TEXT("NO STAGE PRODUCES REQUIRED COMPONENT %d"),
				static_cast<int32>(Component));
			return false;
		}
	}

	// The fixing order must be a faithful ordering of the requirements.
	// A craft bigger than the factory can carry is refused here, with
	// the rest of the recipe's contracts, rather than being found when
	// a gantry will not pass over it.
	if (!ValidateCraftFitsFactory(Recipe, OutError))
	{
		return false;
	}
	if (!ValidateFixingOrder(Recipe, OutError))
	{
		return false;
	}

	// Every station stage - AND the station-less quality gate, which
	// still takes real time at the end of the line - needs an explicit
	// cycle time. No defaults.
	for (const FLBSpacecraftStageDescriptor& Row : StageTable())
	{
		if (Row.StationClassId.IsNone() && !Row.bQualityGate)
		{
			continue;
		}
		const float* Cycle = Recipe.NominalCycleSeconds.Find(Row.Stage);
		if (Cycle == nullptr || *Cycle <= 0.f)
		{
			OutError = FString::Printf(
				TEXT("RECIPE HAS NO CYCLE TIME FOR STAGE %s"),
				SpacecraftStageName(Row.Stage));
			return false;
		}
	}
	OutError.Reset();
	return true;
}
