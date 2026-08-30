// Spacecraft-era production vocabulary (vertical slice, serial line).
//
// Supersedes the car-era 18-stage ELBOneFactoryVehicleStage / four-department
// model for NEW spacecraft work. Nothing here edits or replaces the OneFactory
// types - per repo convention they stay as evidence and keep their tests.
//
// Design rules carried over from the pivot assessment:
//  * the stage graph is a DATA TABLE, not compile-time switch spread;
//  * the station/route count is derived from the table, never a constant;
//  * component completeness (the generalised panel-BOM) gates Assembly;
//  * everything fails closed: an invalid table, unknown recipe or skipped
//    stage is a rejection with a reason, never a fallback.

#pragma once

#include "CoreMinimal.h"
#include "LBSpacecraftProductionTypes.generated.h"

/** Serial production stages for the vertical slice. Order is meaningful and
 *  validated: a unit only ever advances to the next enumerator. */
UENUM(BlueprintType)
enum class ELBSpacecraftStage : uint8
{
	MaterialIntake = 0,
	MaterialProcessing,
	HullFabrication,
	ComponentFabrication,
	AssemblyStaging,
	Assembly,
	Testing,
	Dispatched
};

/** The six recipe components every spacecraft is built from. Piece-by-piece
 *  customisation is deliberately out of scope - recipes are fixed products. */
UENUM(BlueprintType)
enum class ELBSpacecraftComponent : uint8
{
	Hull = 0,
	Electronics,
	Power,
	Propulsion,
	Navigation,
	Interior
};

/** ONE ACCESS EDGE: fitting Blocker puts Blocked out of reach.
 *
 *  In real assembly the fixing order is a physical fact rather than a
 *  preference - once the cabin trim and panels are on, the harness
 *  behind them cannot be reached. Writing that down as edges is what
 *  makes deferring a fit genuinely expensive instead of merely late,
 *  and what turns the station split into a puzzle rather than a
 *  partition.
 *
 *  A flat array of these rather than TMap<Component, TArray<Component>>
 *  because UPROPERTY does not reflect nested containers. */
USTRUCT(BlueprintType)
struct LINEBOSSCARFACTORY_API FLBSpacecraftAccessEdge
{
	GENERATED_BODY()

	/** The component whose fitting closes the access. */
	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "LineBoss")
	ELBSpacecraftComponent Blocker = ELBSpacecraftComponent::Hull;

	/** The component that becomes unreachable, and must therefore be
	 *  fitted BEFORE the blocker. */
	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "LineBoss")
	ELBSpacecraftComponent Blocked = ELBSpacecraftComponent::Hull;
};

/** One row of the stage table. */
USTRUCT(BlueprintType)
struct LINEBOSSCARFACTORY_API FLBSpacecraftStageDescriptor
{
	GENERATED_BODY()

	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "LineBoss")
	ELBSpacecraftStage Stage = ELBSpacecraftStage::MaterialIntake;

	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "LineBoss")
	FString DisplayName;

	/** Which station family services this stage (slice: MaterialProcessor,
	 *  HullFabricator, ComponentFabricator, AssemblyRobot, TestingRig).
	 *  Terminal stages have none. */
	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "LineBoss")
	FName StationClassId;

	/** True when this stage is a quality gate (the slice's hover test). */
	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "LineBoss")
	bool bQualityGate = false;

	/** Components EARNED into the unit's BOM when this stage completes. */
	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "LineBoss")
	TArray<ELBSpacecraftComponent> ComponentsProduced;
};

/** A fixed spacecraft product recipe (tier). */
USTRUCT(BlueprintType)
struct LINEBOSSCARFACTORY_API FLBSpacecraftRecipe
{
	GENERATED_BODY()

	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "LineBoss")
	FName RecipeId;

	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "LineBoss")
	FString DisplayName;

	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "LineBoss")
	TArray<ELBSpacecraftComponent> RequiredComponents;

	/** THE FIXING ORDER: the sequence in which this craft's components go
	 *  on. Deliberately a SEPARATE list from RequiredComponents rather
	 *  than that list's order, because order-as-a-side-effect is a trap:
	 *  someone sorts the requirement list for a menu and silently changes
	 *  the assembly sequence, with nothing failing. Validation asserts the
	 *  two hold exactly the same components, so this can be reordered
	 *  freely and a mismatch is caught rather than shipped.
	 *
	 *  It is defined by the RECIPE, not chosen by the player. Ships are
	 *  defined product recipes and piece-by-piece craft customisation is a
	 *  named scope trap; what the player chooses is which STATION does
	 *  which slice of this sequence. */
	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "LineBoss")
	TArray<ELBSpacecraftComponent> FixingOrder;

	/** WHY the fixing order is what it is. Each edge says fitting one
	 *  component puts another out of reach, so the blocked one must go
	 *  on first. Validation enforces these against FixingOrder, so an
	 *  order that is physically impossible now fails at catalogue
	 *  validation instead of shipping.
	 *
	 *  May be empty: a recipe with no declared edges is simply one
	 *  whose order is free, and every order satisfies no constraints. */
	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "LineBoss")
	TArray<FLBSpacecraftAccessEdge> AccessBlocks;

	/** Nominal station cycle seconds per stage; missing stage = rejected by
	 *  validation, never defaulted. */
	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "LineBoss")
	/**
	 * HOW MANY of each component this craft actually carries. Absent
	 * means one, so every existing recipe keeps its behaviour.
	 *
	 * This is the missing half of the tier design. Internals are shared
	 * across tiers on purpose - every craft uses the same six
	 * components and the same sub-part catalogue - and the difference
	 * between tiers was always meant to be economic: more parts, longer
	 * stages, bigger stations. Only the last two were ever built, so
	 * measured against its own bill of materials a Cargo cost EXACTLY
	 * what a Scout cost, 28,485 cr, while selling for 2.4 times as
	 * much. The second tier was strictly better than the first at every
	 * scale, which is not a difficulty curve, it is a dominant strategy.
	 *
	 * Counted per FITTED INSTANCE, as the owner asked: a craft's bill
	 * should read like a real machine - twin engines with two nozzles,
	 * three gyroscopes for three axes - rather than one abstract kit
	 * standing in for a whole subsystem.
	 */
	TMap<ELBSpacecraftComponent, int32> ComponentCounts;

	TMap<ELBSpacecraftStage, float> NominalCycleSeconds;

	/** Baseline sale price in integer pence (the management ledger is pence). */
	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "LineBoss")
	int64 RevenuePence = 0;

	/** The finished craft's physical envelope in centimetres (L, W, H).
	 *  The Scout is the SMALLEST craft in the ladder - stations declare the
	 *  largest envelope they can service, and a line whose stations cannot
	 *  hold a recipe's craft refuses to build it (fail closed). */
	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "LineBoss")
	FVector CraftEnvelopeCm = FVector::ZeroVector;

	/** Reputation tier (1..4) required to ACCEPT contracts for this
	 *  recipe - the commercial ladder beside the research tree. */
	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "LineBoss")
	int32 MinReputationTier = 1;
};

/** Minimal per-unit state for the slice: identity, position in the flow and
 *  the earned component BOM. Genealogy/evidence integrate when the spacecraft
 *  production authority lands. */
USTRUCT(BlueprintType)
struct LINEBOSSCARFACTORY_API FLBSpacecraftUnitState
{
	GENERATED_BODY()

	UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category = "LineBoss", SaveGame)
	FName UnitId;

	UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category = "LineBoss", SaveGame)
	FName RecipeId;

	UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category = "LineBoss", SaveGame)
	ELBSpacecraftStage Stage = ELBSpacecraftStage::MaterialIntake;

	UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category = "LineBoss", SaveGame)
	TArray<ELBSpacecraftComponent> ProducedComponents;

	UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category = "LineBoss", SaveGame)
	bool bCompleted = false;

	/** TRIM PASSES already flown on the pad for this craft. Rotor track
	 *  and balance is iterative - run, measure, adjust, run again - so a
	 *  craft can be part-way through settling when the game is saved,
	 *  and losing the count would hand the player free pad time.
	 *
	 *  Only ever non-zero at the Testing stage; cleared with the rest of
	 *  the quality state when rework is paid for. */
	UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category = "LineBoss", SaveGame)
	int32 TrimPassesDone = 0;

	/** Quality-gate outcome, recorded at the Testing stage (the hover test).
	 *  A unit may not leave Testing without a recorded pass; a recorded fail
	 *  can be retested. */
	UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category = "LineBoss", SaveGame)
	bool bQualityRecorded = false;

	/** Failed hover tests on this unit - each one deducts from the
	 *  settlement (PROVISIONAL 10% per defect, capped at 30%). */
	UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category = "LineBoss", SaveGame)
	int32 FailedQualityTests = 0;

	UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category = "LineBoss", SaveGame)
	bool bQualityPassed = false;

	/** WORKMANSHIP DEFECTS accrued as the craft came down the line. A
	 *  station fits parts badly when it is short of drones, and the
	 *  hover test is where that shows up - the honest-machine-economy
	 *  pillar: the player can see the cause and fix it by crewing up. */
	UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category = "LineBoss", SaveGame)
	int32 DefectPoints = 0;

	/** Sim-seconds of rework still owed before this craft may retest.
	 *  Non-zero only for a craft that FAILED its hover test; without
	 *  this the failed craft would sit at the gate forever. */
	UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category = "LineBoss", SaveGame)
	float ReworkSecondsRemaining = 0.f;

	/** BUILT TO STOCK: finished, off the line, and not yet sold. A
	 *  craft whose contract expired while it was still being built
	 *  used to sit at the gate forever with nothing to settle against,
	 *  blocking everything behind it. It rolls off into stock instead
	 *  and waits for an order it fits. */
	UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category = "LineBoss", SaveGame)
	bool bAwaitingSale = false;

	/** CONCESSION GRANTED: this craft ships with a recorded deviation
	 *  instead of being put right. It is the player choosing to pay in
	 *  margin and reputation rather than in line time.
	 *
	 *  It substitutes for a quality PASS at the gate - that is the
	 *  whole point of the disposition - so anything that lets a craft
	 *  leave Testing must honour it, and anything that settles a craft
	 *  must charge for it. */
	UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category = "LineBoss", SaveGame)
	bool bConcessionGranted = false;

	/** The defect points AS THEY STOOD when the concession was signed.
	 *  Kept separately from DefectPoints because the deviation is a
	 *  record of what was actually waved through: the live count can
	 *  move afterwards, and a settlement that re-read it would charge
	 *  for something nobody agreed to. */
	UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category = "LineBoss", SaveGame)
	int32 ConcededDefectPoints = 0;

	/**
	 * THE HULL THIS CRAFT IS. None on a new build; on a refit it names
	 * the delivered unit whose physical ship has come back.
	 *
	 * This is also the discriminator - there is deliberately no
	 * separate "is a refit" flag, because two fields that must agree
	 * are two fields that can disagree, and then the disagreement needs
	 * its own invariant, its own refusal and its own test.
	 */
	UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category = "LineBoss", SaveGame)
	FName OriginUnitId;

	/** The rung this craft JOINED the ladder at. The first stage for a
	 *  new build, a later one for a refit. Kept on the unit so the
	 *  validator can check a craft never stands BELOW where it started
	 *  without first having to build a contract index. */
	UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category = "LineBoss", SaveGame)
	ELBSpacecraftStage EntryStage = ELBSpacecraftStage::MaterialIntake;

	/** The order this craft was taken in FOR. Set only on refits: a
	 *  refit is commissioned against one named order and must never
	 *  settle against another, whereas a new build is fungible and
	 *  keeps today's match-by-recipe behaviour. */
	UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category = "LineBoss", SaveGame)
	FName AssignedContractId;

	/** A refit is a craft coming back; a new build is not. */
	bool IsRefit() const { return !OriginUnitId.IsNone(); }
};

/** Static catalog + rules for the spacecraft production flow. Pure data and
 *  pure functions; owns no world state. */
class LINEBOSSCARFACTORY_API FLBSpacecraftProductionCatalog
{
public:
	/** The canonical serial stage table. */
	static const TArray<FLBSpacecraftStageDescriptor>& StageTable();

	/** Fail-closed structural validation of the stage table itself. */
	static bool ValidateStageTable(FString& OutError);

	static const FLBSpacecraftStageDescriptor* FindStage(ELBSpacecraftStage Stage);

	/** Next stage in the serial flow; false when Stage is terminal. */
	static bool NextStage(ELBSpacecraftStage Stage, ELBSpacecraftStage& OutNext);

	static bool IsQualityGate(ELBSpacecraftStage Stage);

	/** The PRODUCT stage a craft arrives in at station Index of a
	 *  StationCount-long line: station i covers stage rows [i*6/N..).
	 *  This is what lets one repeated station type drive the six-value
	 *  SaveGame stage ladder at ANY line length - stages describe the
	 *  craft, stations are however many the player placed, and this map
	 *  ties them together. Pure and monotonic; clamps into the
	 *  station-served rows. */
	static ELBSpacecraftStage StageForRouteIndex(int32 Index,
		int32 StationCount);

	/** Total nominal seconds of LINE work in a recipe - the sum of its
	 *  station-served stage cycle times, excluding the station-less
	 *  quality gate. */
	static float TotalLineSeconds(const FLBSpacecraftRecipe& Recipe);

	/** One station's share of a recipe's line work. Weighted by the
	 *  parts allocated there (+1 handling baseline, so an empty pass-
	 *  through station still takes real time): seconds = Total *
	 *  (Allocated+1) / (TotalAllocated+StationCount). Shares sum to the
	 *  total, so adding stations never changes the WORK - it pipelines
	 *  it, which is the throughput decision. */
	static float StationFitSeconds(const FLBSpacecraftRecipe& Recipe,
		int32 AllocatedCount, int32 TotalAllocatedCount,
		int32 StationCount);

	/** Where a component sits in a recipe's fixing order, or INDEX_NONE
	 *  when the recipe does not fit it at all. Takes the ITEM id (the
	 *  inventory name), because that is what allocation and the stores
	 *  speak; the recipe speaks component enums. */
	static int32 FixingIndexOf(const FLBSpacecraftRecipe& Recipe,
		FName ComponentItemId);

	/** A recipe's fixing order as inventory item ids, in order. */
	static TArray<FName> FixingSequenceItemIds(
		const FLBSpacecraftRecipe& Recipe);

	/** Fail-closed check that a recipe's fixing order is a faithful
	 *  ordering of its requirements: same members, no duplicates, none
	 *  missing, nothing extra - AND that it respects every declared
	 *  access edge. */
	static bool ValidateFixingOrder(const FLBSpacecraftRecipe& Recipe,
		FString& OutError);

	/** Pure: everything whose fitting would put Component out of reach.
	 *  Empty when nothing blocks it. */
	static TArray<ELBSpacecraftComponent> BlockersOf(
		const FLBSpacecraftRecipe& Recipe, ELBSpacecraftComponent Component);

	/** Pure: is Component still reachable once the line has fitted
	 *  everything up to and including FittedThroughIndex of the fixing
	 *  order?
	 *
	 *  This is the question traveled work has to ask. Deferring a fit is
	 *  merely late until a blocker lands on top of it; after that the
	 *  craft has to be opened up again, which is why real lines fight so
	 *  hard to keep work in station. A negative index means nothing has
	 *  been fitted yet, so everything is reachable. */
	static bool IsReachableAfter(const FLBSpacecraftRecipe& Recipe,
		ELBSpacecraftComponent Component, int32 FittedThroughIndex);

	/** Pure: workmanship defects a station contributes as a craft
	 *  leaves it. Nominal crew is two drones (the work-bonus curve's
	 *  1.0x point); every drone short of that is one defect, and a
	 *  station with no crew at all fits nothing properly. Stations
	 *  that host no drones (buildings, parts machines) never defect -
	 *  they are not where the craft is assembled. */
	/** Defect points a station's crew adds, TYPE-AWARE (owner
	 *  2026-08-28 endorsed the pulse-line model, where a station's own
	 *  work is inspected before the craft moves on). Crew SIZE still
	 *  sets the base - every drone short of nominal is a defect - and
	 *  the crew's average quality then moves it: a rough crew (winches)
	 *  adds one, a fine crew (sprays) takes one off. That is what makes
	 *  the hire menu a trade rather than a shopping list.
	 *
	 *  CrewQuality01 is the average QualityWeight of the drones that
	 *  stand there; 1.0 is nominal and is what an untyped crew reports,
	 *  so old saves keep their exact behaviour. */
	static int32 DefectPointsForCrewQuality(int32 InstalledDrones,
		int32 DroneSlotCount, float CrewQuality);

	/** Seconds of rework a station's OWN inspection opens for the
	 *  points it just caused. Per-station and small - this is a fitter
	 *  redoing a fitting, not the whole craft going back. */
	static float StationReworkSecondsFor(int32 PointsAtStation);

	static int32 DefectPointsForCrew(int32 InstalledDrones,
		int32 DroneSlotCount);

	/** Pure: the hover test's verdict for a defect load. One blemish
	 *  is survivable; a craft carrying more than that does not fly
	 *  clean and the self-start test catches it. */
	/** Pure: how many TRIM PASSES this craft needs on the pad before it
	 *  settles, or INDEX_NONE when it will never settle and must be
	 *  reworked.
	 *
	 *  Rotor track and balance is iterative: run it, measure, adjust,
	 *  run it again. A clean craft settles on the first pass; every
	 *  defect it collected coming down the line costs another.
	 *
	 *  Convergence honours the SAME tolerance the one-shot gate used,
	 *  so no difficulty tier changes its pass/fail outcome - only how
	 *  long the pad is occupied getting there. */
	static int32 TrimPassesRequired(int32 DefectPoints, int32 Tolerance);

	/** Pure: the attitude residual in degrees a craft still shows at the
	 *  start of a given pass. Decays geometrically as trim is taken out,
	 *  which is what the RCS thrusters are fed so an out-of-trim craft
	 *  visibly leans and burns harder than a settled one. */
	static float TrimResidualDeg(int32 DefectPoints, int32 PassIndex);

	/** THE BIGGEST CRAFT THIS FACTORY WILL EVER SERVICE, declared once.
	 *
	 *  The Scout is the SMALLEST craft in a six-tier ladder, and four of
	 *  those tiers have no dimensions yet - so the largest ship cannot
	 *  be read out of the catalogue, it has to be decided and then
	 *  enforced. Everything that must physically clear a craft - the
	 *  gantry span, the hall, the doors - derives from this rather than
	 *  from whatever the largest recipe happens to be today.
	 *
	 *  3600 x 2100 x 1050 is 1.5x the Mk2 station envelope, the same
	 *  growth step already approved for Scout to Cargo, applied once
	 *  more. It is a starting number and is meant to be edited; what
	 *  matters is that it is in ONE place and that exceeding it fails
	 *  loudly. */
	static FVector FactoryMaxCraftEnvelopeCm();

	/** Widest a line station may be across the track, in cm.
	 *
	 *  Declared here rather than read from the station catalogue because
	 *  that catalogue lives a layer above this one. It is not left to
	 *  trust: LineBoss.Spacecraft.Gantry.PortalClearsEveryLineStation
	 *  walks the real catalogue and fails if any station outgrows this
	 *  number, so adding a bigger mark breaks the build rather than the
	 *  crane.
	 *
	 *  Stations are placeable at any quarter turn and a rotated
	 *  footprint swaps its axes, so this is the LARGER of the two - the
	 *  crane has to clear whatever orientation the player chooses. */
	static float WidestLineStationAcrossCm();

	/** Clear distance the gantry's rails must stand apart, derived from
	 *  the factory envelope AND from the stations the portal travels
	 *  over, never hand-set.
	 *
	 *  TWO CONSTRAINTS, AND THE STATIONS ARE THE BIGGER ONE. This
	 *  returned the craft envelope plus working room and nothing else,
	 *  which is right for a crane that only has to HOLD a hull. This
	 *  portal also has to TRAVEL THE LINE: its legs run outboard of the
	 *  stations and the bridge passes over their tops. Sized against the
	 *  hull alone it came to 21.5 m and could not pass its own assembly
	 *  station Mk2, which is 27.0 m across.
	 *
	 *  Sizing a crane against the thing it LIFTS rather than the things
	 *  it PASSES OVER is the specific mistake this exists to stop. */
	static float GantryRailSpanCm();

	/** Fail-closed: does this recipe's craft fit the factory it is
	 *  built in? A craft larger than the declared envelope cannot be
	 *  carried between stations however big its stations are, so it is
	 *  refused at catalogue validation rather than discovered when a
	 *  ship will not pass under the crane. */
	static bool ValidateCraftFitsFactory(const FLBSpacecraftRecipe& Recipe,
		FString& OutError);

	static bool DefectsPassHoverTest(int32 DefectPoints);

	/** The same verdict at an explicit tolerance - how forgiving the
	 *  hover test is IS the difficulty setting's sharpest dial. */
	static bool DefectsPassHoverTestAt(int32 DefectPoints,
		int32 Tolerance);

	/** Pure: sim-seconds of rework a failed craft owes. Proportional
	 *  to the mess, with a floor so any failure costs real time. */
	static float ReworkSecondsFor(int32 DefectPoints);

	/**
	 * How many of a component a craft carries. ONE unless the recipe
	 * says otherwise, and never less than one - a required component
	 * with a count of zero would be a craft that needs a part it does
	 * not consume, which nothing downstream could make sense of.
	 */
	static int32 ComponentCountFor(const FLBSpacecraftRecipe& Recipe,
		ELBSpacecraftComponent Component);

	/** The same, by inventory item id, for the callers that only have
	 *  one of those. Returns 1 for anything not a known component. */
	static int32 ComponentCountForItem(const FLBSpacecraftRecipe& Recipe,
		FName ComponentItemId);

	// ---------------------------------------------------------------
	// REFIT: a delivered craft comes back for work
	// ---------------------------------------------------------------
	//
	// A refit re-enters the ladder at a rung and is placed at the
	// station whose ARRIVAL stage is that rung, so its stage and its
	// route index agree exactly. That is what lets every existing
	// invariant stand untouched - the serial-flow gate, the runtime's
	// stage/position equality check, and the assembly bill-of-materials
	// gate all see an ordinary unit standing in an ordinary place.
	//
	// The craft is a NEW unit that names the delivered one, never a
	// rewind of it. Rewinding would break the validated biconditional
	// that a completed craft is a dispatched one, and would carry the
	// original's failed-test deductions onto work the customer is
	// paying for separately.

	/** The components a craft has EARNED by the time it stands at
	 *  Stage: the union of what rows 0..Stage produce. A refit is
	 *  seeded with these, which is what gets it past the assembly
	 *  gate without walking the whole ladder. */
	static void ComponentsEarnedBy(ELBSpacecraftStage Stage,
		TArray<ELBSpacecraftComponent>& OutComponents);

	/** The components a refit entering at Stage will actually RE-FIT:
	 *  the union of what rows Stage..end produce. This is the work
	 *  being bought, and it is the only honest basis for a price. */
	static void ComponentsRefittedFrom(ELBSpacecraftStage Stage,
		TArray<ELBSpacecraftComponent>& OutComponents);

	/**
	 * What share of a whole craft's work a refit from Stage represents,
	 * measured in COMPONENTS RE-FITTED rather than in time spent.
	 *
	 * Pricing by time was the first design and it broke the game. The
	 * fixing order is expensive-first (hull, power, propulsion) while
	 * the cycle times are expensive-LAST (assembly is a third of the
	 * clock and fits nothing), so a time-priced refit was paid for the
	 * long end of the ladder while buying only the cheap end of the
	 * bill of materials. Worked through, the WORST refit out-earned the
	 * BEST new build by 15% and earned seven times as much per
	 * station-second, for a tenth of the materials. Nobody would ever
	 * have built a new craft again.
	 *
	 * Counting components ties the price to what is actually consumed,
	 * so a refit can never be more profitable per part than the build
	 * it is a subset of.
	 */
	static float RefitWorkFraction(ELBSpacecraftStage EntryStage);

	/**
	 * May a refit enter here, and if not, why not?
	 *
	 * Refuses a rung that re-fits NOTHING. Stages after component
	 * fabrication produce no components at all, so a craft entering
	 * there would be bought a price for standing still. That is not a
	 * refit, it is an inspection, and selling it as one is how the
	 * first design leaked money.
	 */
	static bool IsLegalRefitEntryStage(ELBSpacecraftStage EntryStage,
		FString& OutReason);

	// ---------------------------------------------------------------
	// THE MATERIAL REVIEW BOARD - what happens to a craft that failed
	// ---------------------------------------------------------------
	//
	// A failed craft could previously do exactly one thing: pay its
	// rework and retest. That is not a decision, it is a toll, and it
	// is not how the industry the research came from actually works.
	// A real board looks at a nonconforming article and picks one of
	// three dispositions - REWORK it, USE IT AS IS under a recorded
	// concession, or SCRAP it.
	//
	// Modelling all three turns a delay into a judgement call with the
	// player's money on it: pay TIME to put it right, pay MARGIN AND
	// REPUTATION to ship it anyway, or cut the loss on a craft that is
	// too far gone. That is the honest-machine-economy pillar applied
	// to quality rather than to power.

	/** The most defect points that may EVER be signed off on a
	 *  concession. Above this the craft must be reworked or scrapped:
	 *  a concession is a deviation a customer will tolerate, and past
	 *  some point no customer tolerates it. Without a ceiling the
	 *  mechanic degenerates - every failure becomes a small fee and
	 *  the quality gate stops meaning anything. */
	static int32 MaxConcedableDefectPoints();

	/** Percent of the contract price forfeited by shipping on a
	 *  concession. Scales with how much is being waved through. */
	static int32 ConcessionDeductionPercent(int32 DefectPoints);

	/** Reputation points a concession costs. Shipping known-deviant
	 *  work is remembered by customers even when they accept it. */
	static int32 ConcessionReputationCost(int32 DefectPoints);

	/** Pure: may this craft be conceded, and if not, why not? The
	 *  reason is player-facing, so it names the actual obstacle. */
	static bool CanConcede(const struct FLBSpacecraftUnitState& Unit,
		FString& OutReason);

	/** Pure: how many of a craft's defects the inspection sweep has
	 *  FOUND at this much progress. The Testing stage is 60 s of
	 *  "Engine test and inspection" that used to show nothing at all,
	 *  and the verdict landed out of nowhere at the end. Faults are
	 *  discovered as the scan passes over them instead, so a player
	 *  watching can see trouble coming. Rounds UP, so the first fault
	 *  shows the moment the sweep starts rather than half way. */
	static int32 DefectsFoundByScan(int32 DefectPoints, float Progress01);

	/** The defect load at or below which the hover test passes. */
	static constexpr int32 HoverTestDefectTolerance = 1;

	/** Count of stages that need a physical station (route length source -
	 *  derived from the table, never a constant). */
	static int32 StationStageCount();

	/** Can this unit enter the given stage? Fail closed: only the immediate
	 *  next stage is ever legal, and Assembly additionally requires the
	 *  unit's earned BOM to satisfy its recipe. */
	static bool CanEnterStage(const FLBSpacecraftUnitState& Unit,
		const FLBSpacecraftRecipe& Recipe, ELBSpacecraftStage Target,
		FString& OutReason);

	/** Advance the unit one stage, earning that stage's components. Returns
	 *  false (unit untouched) if the advance is illegal. */
	static bool AdvanceUnit(FLBSpacecraftUnitState& Unit,
		const FLBSpacecraftRecipe& Recipe, FString& OutReason);

	/** Fixed product recipes. Slice ships Scout-01 only; later tiers register
	 *  here rather than branching production code. */
	static const TArray<FLBSpacecraftRecipe>& CanonicalRecipes();

	static bool FindRecipe(FName RecipeId, FLBSpacecraftRecipe& OutRecipe);

	/** Recipe-level validation: every required component is produced by some
	 *  stage at or before Assembly, and every station stage has a cycle time. */
	static bool ValidateRecipe(const FLBSpacecraftRecipe& Recipe,
		FString& OutError);
};
