// Spacecraft-era WIP presentation: reconstructs visuals from the authorities
// and NEVER creates a second logical record. Stations render as placeholder
// footprint blocks until the approved station models land (they swap in as a
// pure visual replacement - the records don't change); craft render as a
// pale component crate before Assembly and as the Scout-01 mesh from
// Assembly onward, sliding toward the next station late in each cycle.

#pragma once

#include "CoreMinimal.h"
#include "GameFramework/Actor.h"
#include "LBSpacecraftBuildAuthority.h"
#include "LBSpacecraftProductionAuthority.h"
#include "LBSpacecraftRuntimeCoordinator.h"
#include "LBSpacecraftWIPPresentationActor.generated.h"

class UStaticMeshComponent;

/** A dispatched craft flying out of the factory (visual only). */
USTRUCT()
struct FLBSpacecraftDepartingVisual
{
	GENERATED_BODY()

	UPROPERTY()
	TObjectPtr<UStaticMeshComponent> Component = nullptr;

	UPROPERTY()
	FVector StartLocation = FVector::ZeroVector;

	UPROPERTY()
	float ElapsedSeconds = 0.f;

	/** Flame cones riding this departure (belly then mains). These were
	 *  plain pointers ("GC-referenced via the actor") - retention was
	 *  never the risk, DANGLING was: the packaged save/load soak
	 *  (2026-09-01) rolled the runtime back mid-session, the rebuilt
	 *  unit reused the same UnitId, the unit-keyed caches destroyed the
	 *  old components, and the departure's raw pointers crashed the
	 *  game in ApplyGearRetraction. TObjectPtr UPROPERTYs read null
	 *  once the component is gone. */
	TArray<TWeakObjectPtr<UStaticMeshComponent>> BellyFlames;
	TArray<TWeakObjectPtr<UStaticMeshComponent>> MainFlames;

	/** The five non-Hull assemblies of a six-part Scout (v002), riding
	 *  the departure as children of Component - they need no per-frame
	 *  handling of their own, only explicit destruction at the end,
	 *  same reason as the gear legs below. */
	UPROPERTY()
	TArray<TObjectPtr<UStaticMeshComponent>> ScoutParts;

	/** The three landing-gear legs, in nose/left/right order, each a
	 *  small tree of pieces attached to the craft. They ride the flight
	 *  so they can be seen to RETRACT: the craft leaves the line on its
	 *  wheels, taxis the chicane, and folds them away as it goes full
	 *  pelt (owner 2026-08-28: "needs to be on ship but disappears when
	 *  it takes off at the end"). Their anchor Z is kept alongside so
	 *  the retraction has somewhere to travel back from. */
	TArray<TWeakObjectPtr<UStaticMeshComponent>> GearLegs;
	TArray<float> GearAnchorZCm;

	/** How far a leg travels to fold away, in the CRAFT's local units.
	 *  Carried rather than recomputed because the craft component may
	 *  be scaled (a blockout hull is a scaled cube), and the travel has
	 *  to be in the same space the legs are placed in. */
	float GearRetractTravelCm = 0.f;
};

UCLASS()
class LINEBOSSCARFACTORY_API ALBSpacecraftWIPPresentationActor : public AActor
{
	GENERATED_BODY()

public:
	ALBSpacecraftWIPPresentationActor();

	/** The approved craft mesh (imported Scout-01 LOD0). If it cannot load,
	 *  the presenter draws the crate instead and logs - it draws less, never
	 *  more, and never invents records. */
	UPROPERTY(EditAnywhere, Category = "LineBoss")
	TSoftObjectPtr<UStaticMesh> CraftMesh;

	/** WIP build forms (owner, 2026-08-25): the ship assembles visually.
	 *  Crate -> Chassis (Hull Fabrication) -> Airframe (Component
	 *  Fabrication) -> Fitted, all but the canopy (Assembly Staging) ->
	 *  full craft (Assembly+). Every rung falls back DOWN the ladder,
	 *  ending at the honest crate. */
	UPROPERTY(EditAnywhere, Category = "LineBoss")
	TSoftObjectPtr<UStaticMesh> ChassisMesh;

	UPROPERTY(EditAnywhere, Category = "LineBoss")
	TSoftObjectPtr<UStaticMesh> AirframeMesh;

	UPROPERTY(EditAnywhere, Category = "LineBoss")
	TSoftObjectPtr<UStaticMesh> FittedMesh;

	/** THE SIX-ASSEMBLY SCOUT (v002, commissioned 2026-08-30). Loaded
	 *  and cached TOGETHER: if any of the six fails to load, the craft
	 *  falls back to the single CraftMesh blob entirely rather than
	 *  showing an incomplete ship - the same "fall down the ladder
	 *  honestly" rule ResolveBuildFormMesh already follows. Hull is
	 *  what the unit's PRIMARY visual component holds; the other five
	 *  attach to it as children (see ScoutV2Parts below). */
	bool ResolveScoutV2Parts(UStaticMesh*& OutHull,
		UStaticMesh*& OutPropulsion, UStaticMesh*& OutPower,
		UStaticMesh*& OutElectronics, UStaticMesh*& OutNavigation,
		UStaticMesh*& OutInterior);

	/** Fraction of the cycle after which a craft slides toward its next
	 *  station (matches the car-era presentation language). */
	UPROPERTY(EditAnywhere, Category = "LineBoss",
		meta = (ClampMin = "0.5", ClampMax = "0.99"))
	float SlideStartFraction = 0.8f;

	/** Hover-test presentation: the craft lifts off the rig and bobs while
	 *  the Testing stage runs - the visible version of the hover test. */
	UPROPERTY(EditAnywhere, Category = "LineBoss")
	float TestHoverLiftCm = 600.f;

	UPROPERTY(EditAnywhere, Category = "LineBoss")
	float HoverBobAmplitudeCm = 30.f;

	UPROPERTY(EditAnywhere, Category = "LineBoss")
	float HoverBobPeriodSeconds = 3.f;

	/** Dispatch presentation (owner, 2026-08-25): after the hover test the
	 *  craft flies a CHICANE (one S-weave), then goes full pelt down the
	 *  length of the factory (the line's -Y axis) and exits. */
	UPROPERTY(EditAnywhere, Category = "LineBoss")
	float ChicaneSeconds = 2.2f;

	UPROPERTY(EditAnywhere, Category = "LineBoss")
	float ChicaneWidthCm = 900.f;

	UPROPERTY(EditAnywhere, Category = "LineBoss")
	float SprintSeconds = 2.6f;

	UPROPERTY(EditAnywhere, Category = "LineBoss")
	float SprintDistanceCm = 26000.f;

	UPROPERTY(EditAnywhere, Category = "LineBoss")
	float DepartureClimbCm = 3500.f;

	/** How long the gear takes to fold away once the craft stops
	 *  taxiing and goes full pelt. Short: this is the moment the eye is
	 *  on the sprint, and gear that lingers reads as broken. */
	UPROPERTY(EditAnywhere, Category = "LineBoss")
	float GearRetractSeconds = 0.9f;

	/** How far the wheels hang below the hull. Sized against the rig:
	 *  the belly rides 100 cm over the station blocks, so gear this
	 *  long puts the craft VISIBLY ON ITS WHEELS rather than floating,
	 *  and leaves the ground crew a reason to be under there. */
	UPROPERTY(EditAnywhere, Category = "LineBoss")
	float GearHeightCm = 100.f;

	/** Runway dressing for the sprint corridor (owner, 2026-08-25): edge
	 *  and centreline paint plus red strobes chasing toward the exit,
	 *  laid down the line's -Y axis from every placed test rig. */
	UPROPERTY(EditAnywhere, Category = "LineBoss")
	float RunwayLengthCm = 10000.f;

	/** The permanent site runway: fixed strip the chicane swings each
	 *  departure onto; sprints -Y and exits the open south wall. */
	UPROPERTY(EditAnywhere, Category = "LineBoss")
	float SiteRunwayXCm = 3000.f;

	UPROPERTY(EditAnywhere, Category = "LineBoss")
	float SiteRunwayStartYCm = -3500.f;

	UPROPERTY(EditAnywhere, Category = "LineBoss")
	float RunwayWidthCm = 1200.f;

	UPROPERTY(EditAnywhere, Category = "LineBoss")
	int32 RunwayStrobePairs = 8;

	UPROPERTY(EditAnywhere, Category = "LineBoss")
	float RunwayStrobeChaseSeconds = 1.2f;

	/** Strobes ARM just before throttle-up (owner, 2026-08-25): they wake
	 *  this many seconds before the sprint begins, chase while a craft is
	 *  accelerating out, and go dark when the flight ends. */
	UPROPERTY(EditAnywhere, Category = "LineBoss")
	float RunwayStrobeLeadSeconds = 0.8f;

	/** Fitting drones (owner, 2026-08-25): every crafting station gets two
	 *  worker drones, each with its own charging dock at a station corner.
	 *  Drones fly a fitting orbit while the station has an active recipe
	 *  and land back on their docks when it idles; a charging dock pulses
	 *  warm while its drone sits on it. */
	UPROPERTY(EditAnywhere, Category = "LineBoss")
	float DroneHoverHeightCm = 420.f;

	UPROPERTY(EditAnywhere, Category = "LineBoss")
	float DroneTransitSeconds = 1.4f;

	/** ROTORS (owner 2026-08-26: "make the drone sounds that change
	 *  pitch as [rotors] speed up"). Until now the drones' fan pods
	 *  only leaned into motion - they never actually turned, so there
	 *  was no rotor speed for a sound to follow. These five numbers are
	 *  that missing model, and they drive the spin and the audio from
	 *  the same value so the two can never disagree.
	 *
	 *  Spool-up is fast and spool-down slow because that is what a
	 *  rotor does: motors accelerate it under torque, but nothing
	 *  brakes it - it coasts down on aerodynamic drag alone. That
	 *  asymmetry is the whole character of the sound, the reason a
	 *  drone landing sounds different from one taking off. All
	 *  PROVISIONAL pending the owner's audio pass. */
	UPROPERTY(EditAnywhere, Category = "LineBoss")
	float RotorSpoolUpSeconds = 0.55f;

	UPROPERTY(EditAnywhere, Category = "LineBoss")
	float RotorSpoolDownSeconds = 1.9f;

	/** Blade rotation at full load, degrees per second. Deliberately
	 *  NOT a real RPM: at 60 fps anything past ~2700 deg/s aliases into
	 *  a strobing backwards blur, so this is the fastest a rotor can
	 *  turn and still read as turning. */
	UPROPERTY(EditAnywhere, Category = "LineBoss")
	float RotorSpinDegPerSec = 2400.f;

	/** Playback pitch at zero and at full rotor speed. A blade-pass
	 *  tone is proportional to RPM, so the map between them is linear
	 *  rather than eased - easing it would make the drone sound like it
	 *  changes gear. */
	UPROPERTY(EditAnywhere, Category = "LineBoss")
	float RotorMinPitch = 0.55f;

	UPROPERTY(EditAnywhere, Category = "LineBoss")
	float RotorMaxPitch = 1.3f;

	/** How far a single drone carries. Kept short: a dozen drones on a
	 *  built-out floor would otherwise sum into a wall of buzz. */
	UPROPERTY(EditAnywhere, Category = "LineBoss")
	float RotorAudioRadiusCm = 900.f;

	UPROPERTY(EditAnywhere, Category = "LineBoss")
	float RotorAudioFalloffCm = 4200.f;

	/** The placeholder loop. Synthesised from harmonic partials so it
	 *  loops without a click (SourceAssets/.../make_rotor_loop_v001.py)
	 *  and is meant to be replaced, not shipped. Unset or unloadable,
	 *  the rotors still spin and simply make no sound - draws less,
	 *  never more. */
	UPROPERTY(EditAnywhere, Category = "LineBoss")
	TSoftObjectPtr<class USoundBase> RotorLoopSound;

	/** Real station meshes by definition id (the Meshy-derived runtime
	 *  derivatives). A missing or unloadable entry falls back to the
	 *  placeholder block with one log line - draws less, never more. */
	UPROPERTY(EditAnywhere, Category = "LineBoss")
	TMap<FName, TSoftObjectPtr<UStaticMesh>> StationMeshes;

	void BindAuthorities(ALBSpacecraftBuildAuthority* InBuild,
		ALBSpacecraftRuntimeCoordinator* InCoordinator,
		ALBSpacecraftProductionAuthority* InProduction);

	/** Optional: lets status beacons reflect REAL working state (a
	 *  station with an active recipe pulses; an idle one glows dim).
	 *  Unbound, every beacon reads idle - honest, never fabricated. */
	/** The stockpile ledger. Without it the presenter cannot see what
	 *  a station actually holds, which is why the parts visuals were
	 *  static for so long - not an oversight in the drawing, an absent
	 *  binding. */
	void BindInventory(class ALBSpacecraftInventoryAuthority* InInventory);

	void BindCrafting(class ALBSpacecraftCraftingAuthority* InCrafting);

	/** Optional: drone visuals mirror the REAL fleet (battery, flying) -
	 *  unbound, they fall back to selection-driven motion. */
	void BindDroneFleet(class ALBSpacecraftDroneFleetAuthority* InFleet);

	/** Belt routes mirror the transport authority when bound; without
	 *  it the stage-table auto lines stand in (draws less, never more). */
	void BindTransport(class ALBSpacecraftTransportAuthority* InTransport);

	/** The laid line track renders as pieces (owner 2026-08-26). */
	void BindTrack(class ALBSpacecraftTrackAuthority* InTrack);

	virtual void Tick(float DeltaSeconds) override;

	int32 GetStationVisualCount() const { return StationVisuals.Num(); }
	int32 GetStationAccentCount() const { return StationAccents.Num(); }

	/** How many bay-paint decals are live, and how many of them bound
	 *  a material whose domain is actually Deferred Decal. They differ
	 *  when a SURFACE material is handed to a decal: the engine keeps
	 *  it and silently renders the default decal instead, which is the
	 *  fault that left the first paint pass invisible. */
	int32 GetBayPaintDecalCount() const;
	int32 GetBayPaintedDecalCount() const;
	int32 GetRunwayCount() const { return Runways.Num(); }
	int32 GetRunwayPartCount(FName RigStationId) const;
	int32 GetDroneStationCount() const { return DroneVisuals.Num(); }

	/** How many gear legs are currently hung under craft on the line -
	 *  three per craft that has an undercarriage. */
	int32 GetLandingGearLegCount() const;

	/** Dev: logs every drone the presenter is actually drawing - kind,
	 *  ground/flier, where it is and how big its mesh is. Every visual
	 *  claim about the crew until now has been read off a screenshot
	 *  and guessed at; this reads the components themselves. */
	void LogDroneCrew() const;
	int32 GetUnitFlameCount(FName UnitId) const;
	int32 GetDepartingFlameCount() const;
	/** 0 = landed on the dock, 1 = fully out fitting parts. */
	float GetDroneWorkAlpha(FName StationId) const;

	/** Rotor speed 0..1 of one drone at a station, or 0 when there is
	 *  no such drone. This is the value the sound follows. */
	float GetDroneRotorSpeed01(FName StationId, int32 DroneIndex) const;

	/** How many drones currently have a live rotor sound - the count a
	 *  test can hold against the fleet without needing to hear it. */
	int32 GetRotorAudioCount() const;

	/** How hard the rotors are being asked to work, from what the drone
	 *  is doing. A loaded drone runs its motors hardest; a hovering one
	 *  only holds its own weight; a docked one shuts them off. This is
	 *  the reason the factory sounds busier when parts are moving. */
	static float ComputeRotorLoad01(bool bDocked, bool bCarrying,
		bool bFitting);

	/** One frame of spool. Approaches Target exponentially, using the
	 *  up constant when accelerating and the down constant when
	 *  coasting; a non-positive constant snaps rather than dividing. */
	static float ComputeRotorSpeed01(float Current, float Target,
		float DeltaSeconds, float SpoolUpSeconds, float SpoolDownSeconds);

	/** Playback pitch for a rotor speed - linear, see RotorMinPitch. */
	static float ComputeRotorPitch(float Speed01, float MinPitch,
		float MaxPitch);

	/** Playback volume for a rotor speed. Rises FASTER than linearly:
	 *  rotor noise scales with tip speed steeply, so a half-speed rotor
	 *  is much quieter than half as loud, which is what keeps a floor
	 *  of idling drones from droning. Reaches exactly 0 at rest so the
	 *  sound can be stopped rather than played silently. */
	static float ComputeRotorVolume01(float Speed01);

	/** Chasing red strobe: exactly one hot light at a time, advancing
	 *  toward higher indices (the exit) every ChasePeriod/LightCount
	 *  seconds; the rest idle dim. Pure and deterministic. */
	static float ComputeStrobeIntensity01(float ClockSeconds,
		int32 LightIndex, int32 LightCount, float ChasePeriodSeconds);

	/** Seconds since the strobes armed for a departing craft, or a
	 *  negative value while they stay dark. Arms LeadSeconds before the
	 *  sprint (throttle-up) and stays armed to the end of the flight. */
	static float ComputeStrobeArmClock(float DepartureElapsedSeconds,
		float InChicaneSeconds, float LeadSeconds);

	/** Thruster mix through a departure (owner, 2026-08-25): belly RCS
	 *  burn through hover/chicane, the MAINS spool just before throttle-
	 *  up, and as speed builds the belly fades until only the mains burn.
	 *  Both outputs 0..1. Pure and deterministic. */
	static void ComputeThrusterMix(float ElapsedSeconds,
		float InChicaneSeconds, float InSprintSeconds, float& OutBelly01,
		float& OutMain01);

	/** A fitting drone's offset from the station centre while working:
	 *  an orbit that periodically dips in toward the workpiece, with a
	 *  hover bob. DroneIndex staggers the two drones half a turn apart.
	 *  Pure and deterministic. */
	static FVector ComputeDroneWorkOffsetCm(float ClockSeconds,
		int32 DroneIndex, float OrbitRadiusCm, float HoverHeightCm);

	/** A GROUND crew drone's offset from the station centre while
	 *  working (owner 2026-08-28: three wheeled drones "for working
	 *  underneath the ship"). Wheeled crew neither orbit nor bob: they
	 *  shuttle along the craft's belly in their own lane, and Z is
	 *  always zero because their wheels are on the floor. DroneIndex
	 *  staggers the run and picks the lane side. Pure and
	 *  deterministic. */
	static FVector ComputeGroundDroneWorkOffsetCm(float ClockSeconds,
		int32 DroneIndex, float RunHalfLengthCm, float LaneOffsetCm);

	/** Which way a wheeled drone points: along its shuttle run, so it
	 *  drives nose-first and reverses out. Pure. */
	static float ComputeGroundDroneYawDeg(float ClockSeconds,
		int32 DroneIndex);

	/** The crew signature: the hired kinds in slot order, or the
	 *  ambient pair when nothing is hired. Pure. */
	static FString ComputeDroneCrewRevision(
		const TArray<FName>& InstalledKinds, int32 InstalledDrones);

	/** What a DroneBatch_v001 sub-part is for at runtime: Spinner and
	 *  Wheel get an animated pivot rotation every tick (see
	 *  ComputeRotatedPartRelativeLocation); Static is spawned so the
	 *  drone is not visually missing a part but never moves - true of
	 *  every arm joint, ram, jack, the winch drum/hook and the landing
	 *  legs, none of which have a reliable pivot at their bounds
	 *  centre the way a rotor or wheel does. */
	enum class ELBSpacecraftDronePartKind : uint8 { Spinner, Wheel, Static };

	struct FLBSpacecraftDronePartSpec
	{
		FString AssetPath;
		ELBSpacecraftDronePartKind Kind = ELBSpacecraftDronePartKind::Static;
	};

	/** The DroneBatch_v001 part list for one crew kind (e.g.
	 *  "CargoLift"): every sub-part beyond the body mesh, with its
	 *  animation kind. Empty for a crew with no DroneBatch entry (the
	 *  block fallback) or for ChargingDock (single mesh, no parts).
	 *  Pure aside from string construction. */
	static void GetDronePartsManifest(FName Crew,
		TArray<FLBSpacecraftDronePartSpec>& OutParts);

	/** The PalletLoads_v001 "Pallet.<stem>" keys that count as this BOM
	 *  component's kit content, in a fixed order. Hull and Propulsion
	 *  have more than one real ship section available (the hull is cut
	 *  into four, propulsion into three), so a station with several
	 *  Hull/Propulsion bays reads as carrying VARIETY rather than four
	 *  copies of one crate; components with a single pallet just return
	 *  that one. Empty for a component this batch does not cover. Pure
	 *  aside from string construction. */
	static void GetKitPalletCandidates(FName ComponentId,
		TArray<FName>& OutPalletKeys);

	/** Deterministic pick from a non-empty candidate list, keyed by
	 *  StationId and BayIndex so the same bay always shows the same
	 *  pallet (stable across ticks and saves) while different bays -
	 *  and different stations fitting the same component - are not all
	 *  forced onto the same one. Pure. */
	static int32 ComputeKitPalletCandidateIndex(FName StationId,
		int32 BayIndex, int32 CandidateCount);

	/** True when a component's kit candidates are SECTIONS of one
	 *  assembly (Hull: nose->fwd->mid->aft) that must all be spawned
	 *  together, in GetKitPalletCandidates' order, rather than one
	 *  being picked to stand in for the rest (owner, 2026-08-30: "the
	 *  hull parts need to be put together"). Pure. */
	static bool ShouldAssembleKitPalletsTogether(FName ComponentId);

	/** Local-Y centres for N pieces of the given lengths, laid end to
	 *  end and centred as a whole on 0 - shared by the kit dolly's
	 *  assembled-together bay and the stripped-hull-on-the-ship visual
	 *  (owner, 2026-08-30: "the hull ship needs to be striped down and
	 *  built live" - the loose sections ride the unit itself before
	 *  Hull is fitted, using the same real-length layout the dolly
	 *  bay uses). Pure. */
	static void ComputeSequentialLayoutCentresCm(
		const TArray<float>& LengthsCm, TArray<float>& OutCentresCm);

	/** ONE NAMED ATTACHMENT POINT on a ship recipe: where a part with
	 *  this NodeId sits, relative to the unit's own primary component
	 *  (owner, 2026-08-30: "make the ship into a node system where the
	 *  parts snap on"). A code-side table rather than mesh-authored
	 *  Unreal sockets - the parts in hand (the six-assembly Scout, the
	 *  PalletLoads_v001 cuts) are already modelled pre-aligned in a
	 *  shared coordinate space, so every current node is Identity; the
	 *  table exists so that stops being an assumption baked into each
	 *  attach call site and becomes one lookup a future part with its
	 *  own, non-aligned geometry can override without touching the
	 *  attach code at all. */
	struct FLBSpacecraftShipNode
	{
		FName NodeId;
		FTransform RelativeTransform = FTransform::Identity;
	};

	/** All named nodes for one ship recipe, in no particular order.
	 *  Empty for a recipe this table does not cover (callers fall back
	 *  to Identity, matching the pre-node-system behaviour exactly -
	 *  see FindShipNodeTransform). Pure aside from string construction. */
	static void GetShipNodes(FName RecipeId,
		TArray<FLBSpacecraftShipNode>& OutNodes);

	/** One node's transform by name. Returns false (OutTransform left
	 *  at Identity) for an unknown recipe or node - an honest miss, not
	 *  a silent wrong answer, though Identity is also the correct
	 *  fallback for every node this table currently defines. Pure. */
	static bool FindShipNodeTransform(FName RecipeId, FName NodeId,
		FTransform& OutTransform);

	/** Fan-pod tilt from horizontal velocity: pods lean into the motion
	 *  (pitch forward for +X, roll for +Y), clamped to MaxTiltDeg at
	 *  600 cm/s and above. Zero velocity means level pods. Pure. */
	static FRotator ComputeFanTiltDeg(const FVector& VelocityCmPerS,
		float MaxTiltDeg);

	/** Continuous rotor-spinner angle: DegPerSecond accumulated over
	 *  DeltaSeconds, wrapped to [0,360) so it never overflows across a
	 *  long session. Speed01 scales the rate (0 = stopped, 1 = full
	 *  spin) so idle/working states read without a separate branch.
	 *  Pure. */
	static float ComputeSpinnerAngleDeg(float PriorAngleDeg,
		float DeltaSeconds, float Speed01, float DegPerSecondAtFullSpeed);

	/** Wheel-hub roll angle from linear ground speed and wheel radius
	 *  (angle = distance / radius, in degrees), wrapped to [0,360).
	 *  Zero speed holds the wheel still rather than snapping - a
	 *  stationary ground drone must not visibly spin its wheels. Pure. */
	static float ComputeWheelRollDeg(float PriorAngleDeg,
		float DeltaSeconds, float SpeedCmPerS, float WheelRadiusCm);

	/** A rotating part's mesh-local pivot is its own bounding-box
	 *  centre. Processing bakes every DroneBatch_v001 part's FULL world
	 *  position into its vertex data (correct for static parts, wrong
	 *  for anything meant to spin: its own local origin ends up at the
	 *  drone's shared origin, not at the part's own hub/axle, so a naive
	 *  component rotation would swing it around the wrong point instead
	 *  of spinning it in place). This computes the counter-offset that
	 *  keeps the part visually anchored at PivotLocal while the
	 *  component's OWN rotation turns around that pivot: the maths is
	 *  RelativeLocation = Pivot - Rotation.RotateVector(Pivot), applied
	 *  every tick since it depends on the current spin angle. Pure. */
	static FVector ComputeRotatedPartRelativeLocation(
		const FVector& PivotLocal, const FRotator& SpinRotation);

	/** Weld-flash intensity: a deterministic flicker in [0,1] built
	 *  from overlapping sines - reads as arc welding, needs no RNG so
	 *  it stays testable and replay-stable. Pure. */
	static float ComputeWeldFlicker01(float ClockSeconds, int32 Seed);

	/** A spark's offset from the weld point: bursts of four sparks fly
	 *  out on deterministic headings and droop under gravity, recycling
	 *  every cycle. Returns the offset; OutAlive01 fades the spark over
	 *  its flight. Pure. */
	static FVector ComputeSparkOffsetCm(float ClockSeconds, int32 Index,
		float& OutAlive01);

	/** Chase-light intensity for guide stud Index of Count: a bright
	 *  pulse races index 0 -> Count-1 at StudsPerSecond, wrapping; the
	 *  rest hold a dim base glow. Pure. */
	static float ComputeChaseIntensity01(float ClockSeconds, int32 Index,
		int32 Count, float StudsPerSecond);

	/** A conveyor chevron's offset along its belt: chevron Index starts
	 *  SpacingCm behind the last, the whole train slides at SpeedCmPerS
	 *  and wraps at SpanCm. Always in [0, SpanCm). Pure. */
	static float ComputeConveyorChevronOffsetCm(float ClockSeconds,
		float SpeedCmPerS, float SpanCm, int32 Index, float SpacingCm);

	int32 GetConveyorCount() const { return Conveyors.Num(); }

	/** The first active departure's craft position and elapsed seconds,
	 *  for the launch camera director. False when nothing is flying. */
	bool GetActiveDeparture(FVector& OutShipCm,
		float& OutElapsedSeconds,
		float* OutCraftHalfLenCm = nullptr) const;

	/** Launch-camera pose: a low side chase during the chicane, a
	 *  trailing crane shot for the sprint, blended at the boundary.
	 *  Deterministic; the director only places what this returns. */
	static void ComputeLaunchCameraPose(float ElapsedSeconds,
		const FVector& ShipCm, float InChicaneSeconds,
		FVector& OutCameraCm, FVector& OutLookAtCm,
		float InCraftHalfLenCm = 700.f);

	/** Hover attitude wobble: two slow incommensurate sines, degrees.
	 *  Small enough to read as drift, big enough to justify the RCS
	 *  corrections. Pure. */
	static void ComputeHoverWobbleDeg(float ClockSeconds,
		float& OutPitchDeg, float& OutRollDeg);

	/** RCS stabilisation: a corner thruster fires in proportion to how
	 *  far ITS corner has dropped (plus a whisper of station-keeping
	 *  base). CornerIndex matches the belly flame order:
	 *  0=(+X,-Y) 1=(+X,+Y) 2=(-X,-Y) 3=(-X,+Y). Pure. */
	static float ComputeRCSCorrection01(float PitchDeg, float RollDeg,
		int32 CornerIndex);
	bool IsStationAccentActive(FName StationId) const
	{
		return ActiveAccents.Contains(StationId);
	}

	// ---- pure, testable animation maths ----
	/** Departure offset from the dispatch point at ElapsedSeconds:
	 *  X = a plain smoothed slide onto the runway centreline (no S-weave -
	 *  cut 2026-08-30, "not the cinematic"), Y = NEGATIVE distance down
	 *  the line (slow through the taxi, then a full-pelt quadratic
	 *  sprint), Z = climb. Clamped at the flight's end. */
	static FVector ComputeDepartureOffsetCm(float ElapsedSeconds,
		float InChicaneSeconds, float InChicaneWidthCm,
		float InSprintSeconds, float InSprintDistanceCm,
		float InClimbCm, float InLateralTargetCm = 0.f);
	/** TRICYCLE landing gear anchors in the craft's LOCAL frame, from
	 *  its mesh bounds: one nose leg well forward on the centreline and
	 *  two mains just aft of centre, all on the belly plane. Derived
	 *  from the hull rather than tabled per tier, because craft grow
	 *  with the ladder and a table would have to grow with them.
	 *  The craft's nose is local +X and its tail local -X. Pure. */
	static void ComputeTricycleGearAnchorsCm(const FVector& HullOriginCm,
		const FVector& HullHalfExtentCm, FVector& OutNoseCm,
		FVector& OutLeftMainCm, FVector& OutRightMainCm);

	/** How far the gear is retracted, 0 = down and locked, 1 = away.
	 *  Stays DOWN for the whole chicane - that leg of the departure is
	 *  a taxi onto the runway, and gear that vanished during it would
	 *  read as the craft dropping its wheels - then folds over
	 *  RetractSeconds from the moment the sprint begins. Eased, so the
	 *  legs start and finish gently. Pure. */
	static float ComputeGearRetraction01(float ElapsedSeconds,
		float InChicaneSeconds, float InRetractSeconds);

	/** HOW HIGH THE STATION HAS THE CRAFT LIFTED, in centimetres above
	 *  its parked height (owner 2026-08-28: "the station will have to
	 *  lift the ship up ... to be worked on").
	 *
	 *  The craft arrives on its landing gear, the four-post lift raises
	 *  it so the crew can get underneath, it is worked on, and it comes
	 *  back down before it moves on. Progress is the craft's progress
	 *  through this station's stop: it rises over the first stretch,
	 *  holds through the middle where the work happens, and lowers over
	 *  the last. Eased at both ends - a lift that snapped would read as
	 *  a teleport. Pure and deterministic. */
	/** How high the craft rides while the gantry crane carries it
	 *  between stations, in cm. Enough to clear the station cradles and
	 *  the parts bins it passes over, and to read as CARRIED rather
	 *  than as hovering. */
	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "LineBoss")
	float CraneCarryRiseCm = 260.f;

	/** How fast the gantry travels along the line, cm/s. A gantry runs
	 *  on rails, so this is the ONLY axis it moves on. */
	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "LineBoss")
	float CraneTravelSpeedCmS = 900.f;

	/** The carry height at a point in a station's cycle: zero while the
	 *  craft is parked, then rise, hold and set down across the slide
	 *  window. Pure so the choreography is testable without a world -
	 *  the same reason ComputeStationLiftCm is. */
	static float ComputeCraneCarryCm(float Progress01, float SlideStart,
		float CarryCm);

	/** Does this station's own shelf hold that component right now? */
	bool HasKitComponent(FName StationId, FName ComponentId) const;

	/** How many crates one component's bay carries on the dolly, taken
	 *  from its sub-assembly recipe's input count. */
	static int32 KitCrateCount(FName ComponentId);

	static float ComputeStationLiftCm(float Progress01, float RaisedCm,
		float RiseFraction);

	/** 0..1 pulse on a sine, PeriodSeconds per cycle, 0.5 at t=0. */
	static float ComputeAccentPulse01(float ClockSeconds,
		float PeriodSeconds);
	/** Energy-ring yaw in degrees, 24 deg/s, wrapped to [0, 360). */
	static float ComputeRingYawDeg(float ClockSeconds);
	int32 GetUnitVisualCount() const { return UnitVisuals.Num(); }
	int32 GetDepartingVisualCount() const { return Departing.Num(); }
	bool GetUnitVisualLocation(FName UnitId, FVector& OutLocation) const;

private:
	UPROPERTY()
	TObjectPtr<ALBSpacecraftBuildAuthority> BuildAuthority;

	UPROPERTY()
	TObjectPtr<ALBSpacecraftRuntimeCoordinator> Coordinator;

	UPROPERTY()
	TObjectPtr<ALBSpacecraftProductionAuthority> ProductionAuthority;

	TObjectPtr<class ALBSpacecraftInventoryAuthority> InventoryAuthority;

	UPROPERTY()
	TMap<FName, TObjectPtr<UStaticMeshComponent>> StationVisuals;

	UPROPERTY()
	TMap<FName, TObjectPtr<UStaticMeshComponent>> UnitVisuals;

	// UPROPERTY is load-bearing on every one of these caches: without
	// it the pointer is invisible to GC, and the packaged soak's
	// mid-session load purged the six Scout meshes the moment the
	// departed ship's components died - the latch then handed
	// RefreshUnits freed pointers and SetStaticMesh crashed the game
	// (2026-09-01). The older caches below always had it; these were
	// the stragglers.
	bool bScoutV2LoadAttempted = false;

	UPROPERTY()
	TObjectPtr<UStaticMesh> LoadedScoutV2Hull;

	UPROPERTY()
	TObjectPtr<UStaticMesh> LoadedScoutV2Propulsion;

	UPROPERTY()
	TObjectPtr<UStaticMesh> LoadedScoutV2Power;

	UPROPERTY()
	TObjectPtr<UStaticMesh> LoadedScoutV2Electronics;

	UPROPERTY()
	TObjectPtr<UStaticMesh> LoadedScoutV2Navigation;

	UPROPERTY()
	TObjectPtr<UStaticMesh> LoadedScoutV2Interior;

	/** The five non-Hull assemblies, attached as children of a Scout
	 *  unit's primary visual component (which holds the Hull). Every
	 *  place the primary is destroyed must destroy these explicitly
	 *  first - a parent's DestroyComponent() DETACHES children rather
	 *  than destroying them, the trap the landing gear legs and the
	 *  rotor voices already taught this file twice. */
	TMap<FName, TArray<TObjectPtr<UStaticMeshComponent>>> ScoutV2Parts;

	/** Which of the five non-Hull assemblies a Scout unit has actually
	 *  had FITTED so far (owner, 2026-08-30: "the hull parts need to be
	 *  put together" - the craft's own build-form ladder was gated on
	 *  Unit->Stage against thresholds authored for an 8-stage pipeline
	 *  the simplified 6-station route no longer reaches until very
	 *  late, so it sat as a bare crate almost the whole build regardless
	 *  of what was actually fitted. Reading Unit->ProducedComponents -
	 *  the real per-component ground truth - instead of Stage means a
	 *  part appears the moment it is genuinely fitted, and this set is
	 *  what stops it being re-attached every tick once it has. */
	TMap<FName, TSet<ELBSpacecraftComponent>> ScoutV2AttachedComponents;

	/** The four real hull-section pallets (nose/fwd/mid/aft), riding
	 *  loose on a Scout unit BEFORE Hull is fitted - "stripped down and
	 *  built live" (owner, 2026-08-30): the ship reads as its own real
	 *  parts not yet joined, rather than a featureless crate, and
	 *  disappears the instant Hull completes and the real assembled
	 *  mesh takes over. Attached as children of the unit's primary
	 *  visual component, so they ride every crane-carry/slide for free;
	 *  destroyed (never just detached) wherever the primary is. */
	TMap<FName, TArray<TObjectPtr<UStaticMeshComponent>>> StrippedHullSections;


	/** THE INSPECTION SWEEP (owner 2026-08-27). A bar of light that
	 *  travels the length of a craft during its Testing stage - the
	 *  60 s of "engine test and inspection" that used to show nothing
	 *  at all. Blue-white for a clean scan, shifting to warning orange
	 *  as the sweep turns faults up, so trouble is visible BEFORE the
	 *  hover test rules on it. A blockout: an engine cube on the shape
	 *  material until a real beam exists. */
	UPROPERTY()
	TObjectPtr<UStaticMeshComponent> InspectionSweepBar;

	UPROPERTY()
	TObjectPtr<UMaterialInstanceDynamic> InspectionSweepMID;

	void RefreshInspectionSweep();

public:
	/** Pure: the sweep bar's colour for a scan that has found this
	 *  many of this many faults. Clean reads blue-white; every fault
	 *  found pulls it toward warning orange. */
	static FLinearColor InspectionSweepColour(int32 DefectsFound,
		int32 DefectsTotal);

	/** Is the sweep on screen right now? */
	bool IsInspectionSweepLive() const
	{
		return InspectionSweepBar != nullptr;
	}

private:

	/** Live-paint state per Assembly-stage unit: the paint-front MID on
	 *  the craft, and the spray-drone pair with their mist puffs. The
	 *  front follows the REAL stage progress - the ship is exactly as
	 *  painted as the Assembly stage is complete. */
	UPROPERTY()
	TMap<FName, TObjectPtr<UMaterialInstanceDynamic>> UnitPaintMIDs;

	struct FLBSpacecraftSprayRig
	{
		TArray<UStaticMeshComponent*> Bodies;
		TArray<UStaticMeshComponent*> Mists;
	};
	TMap<FName, FLBSpacecraftSprayRig> UnitSprayRigs;

	void DestroySprayRig(FLBSpacecraftSprayRig& Rig);

	UPROPERTY()
	TObjectPtr<UStaticMesh> LoadedCraftMesh;

	UPROPERTY()
	TObjectPtr<UStaticMesh> LoadedChassisMesh;

	UPROPERTY()
	TObjectPtr<UStaticMesh> LoadedAirframeMesh;

	UPROPERTY()
	TObjectPtr<UStaticMesh> LoadedFittedMesh;

	bool bChassisMeshLoadAttempted = false;
	bool bAirframeMeshLoadAttempted = false;
	bool bFittedMeshLoadAttempted = false;

	UStaticMesh* ResolveChassisMesh();
	UStaticMesh* ResolveAirframeMesh();
	UStaticMesh* ResolveFittedMesh();

	/** Cargo-01 build forms (owner's morning drop 2026-08-26). Same
	 *  ladder as the Scout; a missing cargo form falls back to the
	 *  Scout form so the line never draws less. */
	TSoftObjectPtr<UStaticMesh> CargoCraftMesh;

	UPROPERTY()
	TObjectPtr<UStaticMesh> LoadedCargoCraftMesh;
	bool bCargoCraftLoadAttempted = false;
	UStaticMesh* ResolveCargoCraftMesh();
	TSoftObjectPtr<UStaticMesh> CargoChassisMesh;
	TSoftObjectPtr<UStaticMesh> CargoAirframeMesh;
	TSoftObjectPtr<UStaticMesh> CargoFittedMesh;

	UPROPERTY()
	TObjectPtr<UStaticMesh> LoadedCargoChassisMesh;

	UPROPERTY()
	TObjectPtr<UStaticMesh> LoadedCargoAirframeMesh;

	UPROPERTY()
	TObjectPtr<UStaticMesh> LoadedCargoFittedMesh;
	bool bCargoChassisLoadAttempted = false;
	bool bCargoAirframeLoadAttempted = false;
	bool bCargoFittedLoadAttempted = false;
	UStaticMesh* ResolveCargoChassisMesh();
	UStaticMesh* ResolveCargoAirframeMesh();
	UStaticMesh* ResolveCargoFittedMesh();

	/** The WIP mesh for a stage, falling DOWN the ladder to nullptr
	 *  (= the crate) when a form is unavailable. */
	UStaticMesh* ResolveBuildFormMesh(ELBSpacecraftStage Stage,
		FName RecipeId);

	UPROPERTY()
	TMap<FName, TObjectPtr<UStaticMesh>> LoadedStationMeshes;

	UPROPERTY()
	TObjectPtr<class ALBSpacecraftCraftingAuthority> CraftingAuthority;

	UPROPERTY()
	TObjectPtr<class ALBSpacecraftDroneFleetAuthority> DroneFleetAuthority;

	UPROPERTY()
	TObjectPtr<class ALBSpacecraftTransportAuthority> TransportAuthority;

	UPROPERTY()
	TMap<FName, TObjectPtr<UStaticMeshComponent>> StationAccents;

	UPROPERTY()
	TMap<FName, TObjectPtr<UMaterialInstanceDynamic>> StationAccentMIDs;

	TSet<FName> ActiveAccents;
	float AccentClockSeconds = 0.f;

	void TickStationAccents(float DeltaSeconds);

	/** One runway's parts. Components are GC-referenced through the
	 *  actor's owned-component set; MIDs through their components. */
	/** Flame cones attached to a craft: belly RCS + rear mains. */
	struct FLBSpacecraftFlameSet
	{
		// Weak: these caches outlived their components once (the
		// packaged save/load soak, 2026-09-01) and crashed the game
		// on dangling raw pointers. Weak pointers read invalid instead.
		TArray<TWeakObjectPtr<UStaticMeshComponent>> Belly;
		TArray<TWeakObjectPtr<UStaticMeshComponent>> Main;
	};
	TMap<FName, FLBSpacecraftFlameSet> UnitFlames;

	/** One craft's landing gear: the three legs and the belly-plane Z
	 *  each was hung at, so a retraction knows where it came from. */
	struct FLBSpacecraftGearSet
	{
		// Weak for the same reason as FLBSpacecraftFlameSet above.
		TArray<TWeakObjectPtr<UStaticMeshComponent>> Legs;
		TArray<float> AnchorZCm;
		/** Fold travel in the craft's local units - see the departing
		 *  visual's copy for why it is carried rather than recomputed. */
		float RetractTravelCm = 0.f;
	};
	TMap<FName, FLBSpacecraftGearSet> UnitGear;

	/** Builds the three gear legs under a craft mesh component. Draws
	 *  nothing at all if the primitives are unavailable - never a
	 *  half-built undercarriage. */
	FLBSpacecraftGearSet MakeGearSet(UStaticMeshComponent* CraftComponent,
		FName KeyBase);

	/** Applies a retraction 0..1 to a set of legs: they climb into the
	 *  belly and shrink away, and are hidden outright once folded. */
	static void ApplyGearRetraction(
		const TArray<TWeakObjectPtr<UStaticMeshComponent>>& Legs,
		const TArray<float>& AnchorZCm, float Retraction01,
		float RetractTravelCm);

	/** Builds the flame cones attached to a craft mesh component. */
	FLBSpacecraftFlameSet MakeFlameSet(UStaticMeshComponent* CraftComponent,
		FName KeyBase);
	static void ApplyFlameIntensity(
		const TArray<TWeakObjectPtr<UStaticMeshComponent>>& Flames,
		float Intensity01, float FlickerSeed);
	void DestroyFlameSet(FLBSpacecraftFlameSet& Flames);

public:
	/** Called after a save is restored mid-session. The rebuilt units
	 *  reuse their UnitIds, so every per-unit visual cache and any
	 *  in-flight departure animation refers to the OLD components -
	 *  the packaged soak (2026-09-01) crashed on exactly that. Drops
	 *  the departures outright; RefreshUnits rebuilds the rest from
	 *  restored state. */
	void OnRuntimeRestored();

private:

	struct FLBSpacecraftRunwayVisual
	{
		TArray<UStaticMeshComponent*> Parts;
		TArray<UMaterialInstanceDynamic*> StrobeMIDs;
		/** Blue guide studs inside the edges: dim breath at rest, a
		 *  racing chase toward the exit during launch (the Viper-tube
		 *  look, owner 2026-08-25). */
		TArray<UMaterialInstanceDynamic*> ChaseMIDs;
	};
	TMap<FName, FLBSpacecraftRunwayVisual> Runways;

	void TickRunways(float DeltaSeconds);

	/** One auto-connected belt between two consecutive route stations
	 *  (owner directive 2026-08-25: belts AUTO-connect; the player never
	 *  draws routing). Rebuilt whenever the route line-up changes. */
	struct FLBSpacecraftConveyorVisual
	{
		UStaticMeshComponent* Strip = nullptr;
		/** Rails, legs and drive caps: the premium belt furniture. */
		TArray<UStaticMeshComponent*> Furniture;
		TArray<UStaticMeshComponent*> Chevrons;
		FVector StartCm = FVector::ZeroVector;
		FVector EndCm = FVector::ZeroVector;
	};
	TArray<FLBSpacecraftConveyorVisual> Conveyors;
	FString ConveyorRevision;

	void TickConveyors(float DeltaSeconds);

	/** One crafting station's drones and docks (GC-referenced through the
	 *  actor's owned-component set; MIDs through their components). */
	struct FLBSpacecraftDroneVisual
	{
		TArray<UStaticMeshComponent*> Drones;
		/** True for a drone that WORKS ON THE FLOOR (the wheeled ground
		 *  crew) rather than in the air. One entry per drone; drives
		 *  placement, rotor spin and rotor voice together, so a wheeled
		 *  drone can never be heard or seen to fly. */
		TArray<bool> Ground;
		/** Fan pods, PodsPerDrone entries per drone, attached to the
		 *  drone body; empty when the real drone mesh is unavailable
		 *  (block fallback draws less, never more). */
		TArray<UStaticMeshComponent*> Pods;
		/** Slung payload crates, one per drone; visible only while the
		 *  drone is out working (the visible "carrying parts"). */
		TArray<UStaticMeshComponent*> Crates;
		/** Work-effect rig, one set per drone: cutting beam, weld
		 *  flash, four spark streaks. Visible only while working. */
		/** Nav strobes (2 per drone, blue-white, always blinking) and
		 *  the warm work light lit while the drone works - owner
		 *  2026-08-26: "the drones need lights, nav and work lights". */
		TArray<UStaticMeshComponent*> NavLights;
		TArray<UMaterialInstanceDynamic*> NavLightMIDs;
		TArray<UStaticMeshComponent*> WorkLights;
		TArray<UMaterialInstanceDynamic*> WorkLightMIDs;
		TArray<UStaticMeshComponent*> Beams;
		TArray<UStaticMeshComponent*> Flashes;
		TArray<UStaticMeshComponent*> Sparks;
		/** Rotor state, one entry per drone: current speed 0..1, the
		 *  blade angle it has accumulated, and the looping rotor voice
		 *  riding on the drone body. The audio components are owned by
		 *  the actor once registered, so GC holds them like the meshes. */
		TArray<float> RotorSpeeds;
		TArray<float> RotorAngles;
		TArray<class UAudioComponent*> RotorAudio;
		TArray<FVector> LastLocations;
		TArray<UStaticMeshComponent*> Docks;
		/** The real charging-dock models riding on the status pads;
		 *  empty when the dock mesh is unavailable. */
		TArray<UStaticMeshComponent*> DockModels;
		TArray<UMaterialInstanceDynamic*> DockMIDs;
		TArray<FVector> DockLocations;
		float WorkAlpha = 0.f;

		/** One entry per SPINNING part across every drone at this
		 *  station (rotor spinner blades) - continuous rotation while
		 *  the parent drone is flying, held still on the ground. Not
		 *  keyed per-drone like RotorSpeeds/Pods above: the DroneBatch_v001
		 *  meshes (2026-08-30) carry a variable part count per drone
		 *  kind (a hexacopter has 6, a quad has 4), so a flat list with
		 *  an owning drone index scales to any count without a second
		 *  set of per-kind fixed-size arrays. */
		TArray<UStaticMeshComponent*> Spinners;
		TArray<int32> SpinnerOwnerDroneIndex;
		TArray<float> SpinnerAngleDeg;
		TArray<FVector> SpinnerPivotLocal;

		/** One entry per ROLLING wheel (ground drones only) - angle
		 *  driven by the parent drone's travel speed and a fixed wheel
		 *  radius, never by a flat spin rate, so a stationary ground
		 *  drone's wheels visibly stop. */
		TArray<UStaticMeshComponent*> Wheels;
		TArray<int32> WheelOwnerDroneIndex;
		TArray<float> WheelAngleDeg;
		TArray<FVector> WheelPivotLocal;

		/** DroneBatch_v001 parts NOT yet driven by anything above:
		 *  landing legs, arm joints (elbow/wrist/gripper), the winch
		 *  drum and hook block, lift rams, outrigger jacks, the tool
		 *  carousel and turret. All are spawned as STATIC attached
		 *  children (correctly assembled, not missing from the drone)
		 *  but do not move - a leg's true hinge is not its bounds
		 *  centre the way a rotor's or wheel's is, so it needs a real
		 *  pivot source (unlike Spinners/Wheels above) before it can
		 *  animate correctly. Tracked here only so DestroyDroneVisual
		 *  can find and remove them. */
		TArray<UStaticMeshComponent*> StaticParts;
	};
	TMap<FName, FLBSpacecraftDroneVisual> DroneVisuals;

	/** The hired-crew signature each station's drone visual was built
	 *  for. When the player hires or dismisses, this stops matching and
	 *  the visual is rebuilt - otherwise the floor would keep showing
	 *  the crew they had before they chose (owner: what they pick is
	 *  what should stand there). */
	TMap<FName, FString> DroneVisualCrewRevisions;

	/** Tear one station's drones, docks, effects and rotor voices down.
	 *  Shared by the removed-station sweep and the crew rebuild. */
	void DestroyDroneVisual(FLBSpacecraftDroneVisual& Visual);


	void TickDrones(float DeltaSeconds);

	/** THE BUILDING-SHELL LAYER (owner 2026-08-27: "the map should be
	 *  the full building meshes"). On the site map the ship-factory
	 *  hangar STANDS OVER the line - roofs, not interiors - and lifts
	 *  when the player enters. Built once from the line stations'
	 *  bounds; visibility follows the pawn's site-map state. */
	void RefreshSiteShells();
	/** One shell per placed SITE BUILDING, keyed by station id: the
	 *  roofline the world map reads (owner 2026-08-28, three buildings
	 *  at one scale). Lifted when the player enters a building. */
	UPROPERTY()
	TMap<FName, TObjectPtr<UStaticMeshComponent>> SiteShells;

	/** THE SHIP FACTORY INTERIOR (owner 2026-08-28: "go back to the
	 *  ship factory and build anything you need from meshy"). The life
	 *  around the line - a parts stockpile beside every line station,
	 *  columns holding the hall up, a gantry crane over the line, and
	 *  the door a finished craft leaves by. Rebuilt when the line's
	 *  station count changes; hidden on the site map, because it is
	 *  the INSIDE of a building whose roof is on out there. */
	void RefreshHallInterior();
	UPROPERTY()
	TArray<TObjectPtr<UStaticMeshComponent>> HallInteriorPieces;

	/** THE HALL SHELL - walls, roof trusses and hanging lights. Kept
	 *  apart from HallInteriorPieces because the walls are INSTANCED: a
	 *  180 m perimeter is 120 six-metre bays, and 120 separate
	 *  components is 120 draw calls for a box with 84 triangles in it.
	 *  Rebuilt whenever the interior is. */
	TObjectPtr<class UInstancedStaticMeshComponent> HallWallInstances;
	TObjectPtr<class UInstancedStaticMeshComponent> HallTrussInstances;
	TObjectPtr<class UInstancedStaticMeshComponent> HallLightInstances;

	/** The gantry itself, held separately from the rest of the hall
	 *  furniture because it is the only piece that MOVES. */
	/** Every portal standing on the line's track. One per gap, or one
	 *  for the whole line - the count is switchable while the two are
	 *  compared in play (owner 2026-08-29, "will have to test each"). */
	TArray<TWeakObjectPtr<UStaticMeshComponent>> HallCranes;

	/** Idle post of each crane in HallCranes, index for index. */
	/** Per-crane park position and travel axis: cranes ride the rails
	 *  of the track LEG they serve (owner 2026-09-01: "if i place a
	 *  station at the top the crane isnt over it" - the old rig was a
	 *  single hall-centre column that ignored where the line ran). */
	TArray<FVector> HallCraneParkCm;
	TArray<bool> HallCraneAxisAlongY;

	/** The crane TickHallCrane is currently driving - the one nearest
	 *  the craft being carried. The hoist rig hangs off this one. */
	TWeakObjectPtr<UStaticMeshComponent> HallCrane;

	/** Hoist block and its two cables, made once and repositioned. */
	TArray<TObjectPtr<UStaticMeshComponent>> HallCraneHoist;

	/** Where the crane must be, published by RefreshUnits - the one
	 *  place that knows where a carried craft is. Deriving it a second
	 *  time in the crane tick would let the two disagree, and the crane
	 *  would drift off the thing it is supposed to be holding. */
	FVector CarriedCraftAtCm = FVector::ZeroVector;
	bool bCraftIsCarried = false;
	FVector HallCraneParkAtCm = FVector::ZeroVector;
	bool bHallCraneAxisAlongY = true;

	/** Moves the gantry along the line and hangs its hoist on whatever
	 *  craft is in transit. */
	void TickHallCrane(float DeltaSeconds);
	int32 HallInteriorStationCount = -1;

	/** THE SITE SCENERY (owner 2026-08-28: "see if there's any
	 *  sceneries or anything in fab or download... needs to be a full
	 *  site map like arms trade tycoon"). Judged and answered from the
	 *  project's OWN industrial kit under /Game/Meshes rather than
	 *  buying anything: background industry beyond the fence, yard
	 *  containers, and light masts along the ring road. Built once. */
	void RefreshSiteScenery();
	bool bSiteSceneryBuilt = false;

	/** THE ROADS (owner 2026-08-28: "can you place roads to where
	 *  doors are?"). A spine down the site's west side with a spur to
	 *  every placed building's door, rebuilt whenever the set of site
	 *  buildings changes. Blockout geometry: flat slabs, no traffic. */
	void RefreshSiteRoads();
	UPROPERTY()
	TArray<TObjectPtr<UStaticMeshComponent>> RoadPieces;
	int32 RoadBuildingCount = -1;
	UStaticMeshComponent* MakeRoadSlab(FName SlabName,
		const FVector& CentreCm, const FVector2D& SizeCm);
	TWeakObjectPtr<class ALBSpacecraftPlayerPawn> ShellViewPawn;

	/** Sub-assembly buffer crates beside each machine (mirrors the
	 *  crafting authority's buffer counts) and the heavy hauler's
	 *  machine -> storage flights (mirrors the fleet's haul states).
	 *  Draws less when an authority is unbound, never more. */
	void TickSubAssemblyLogistics(float DeltaSeconds);
	void TickTrack(float DeltaSeconds);

	/** Open line-station frame (owner 2026-08-26 evening, the Car
	 *  Manufacture line look: the ship rides the track THROUGH the
	 *  station): flank pads either side of a clear channel, columns
	 *  and crossbeams, and the visible 8-slot drone dock ring (lit
	 *  pads = installed drones). NO machinery - drones are the
	 *  workforce (owner 2026-08-26 evening). */
	struct FLBSpacecraftLineStationFrame
	{
		TArray<TObjectPtr<UStaticMeshComponent>> Parts;
		TArray<TObjectPtr<class ULightComponent>> Lights;
		int32 InstalledDrones = -1;
		/** What the dolly looked like last rebuild. The frame is many
		 *  components and must not churn per tick, but the dolly DOES
		 *  change as stock is consumed - so the guard has to include
		 *  the kit, or the crates would freeze at whatever they were
		 *  when the drone count last changed. */
		FString KitSignature;
	};
	TMap<FName, FLBSpacecraftLineStationFrame> LineStationFrames;

	/** ONE central lift ram per work station (owner 2026-08-28: "think
	 *  there should just be 1 in middle"). A single column under the
	 *  craft's centre is what leaves the whole underside clear for the
	 *  ground crew - four corner posts fenced them out of the very
	 *  place they were hired to work.
	 *
	 *  Held apart from the frame's other parts because it is the one
	 *  piece that MOVES: the frame rebuilds only when the crew changes,
	 *  while the ram travels with the craft every tick. */
	/** The ram's telescoping STAGES, outermost first. A piston rather
	 *  than a scissor because a scissor's linkage splays into exactly
	 *  the volume under the craft that the ground crew were hired to
	 *  work in - the same mistake the four corner posts made. */
	TMap<FName, TArray<TObjectPtr<UStaticMeshComponent>>> StationLiftRams;
	TMap<FName, TObjectPtr<UStaticMeshComponent>> StationLiftSaddles;

	/** Each ram stage's authored Z, recorded when it is built.
	 *
	 *  The stages are modelled EXTENDED, so their placed height IS the
	 *  fully-raised pose and retracting means sliding down from it. The
	 *  tick needs that origin to slide FROM; reading the live transform
	 *  instead would drift, because each frame would measure a position
	 *  the previous frame had already moved. */
	TMap<TObjectPtr<UStaticMeshComponent>, float> StationLiftRamRestZ;

	/** How many nested stages a lift ram has. Three reads as telescopic
	 *  at the play camera; one reads as a box being stretched. */
	static constexpr int32 SpacecraftLiftStages = 3;

	/** The hauler's under-slung component cargo, keyed like the body. */
	TMap<FName, TObjectPtr<UStaticMeshComponent>> HaulerCargos;

	/** The SITE DRESSING (owner 2026-08-26 night: "can we get the floor
	 *  and sides as good quality as the other games?"): the whole floor
	 *  tiled from the 10 m site tile and walled on all four sides with
	 *  the wall bay + pillars, all through instanced-mesh components so
	 *  hundreds of pieces cost a handful of draws. Built once. */
	UPROPERTY()
	TObjectPtr<class UInstancedStaticMeshComponent> SiteFloorTiles;

	/** The survey grid and boundary kerb - the line-work that makes
	 *  empty ground read as PREPARED rather than as an unfinished
	 *  level. Emptiness only reads as capacity if the ground is
	 *  visibly organised. */
	UPROPERTY()
	TObjectPtr<class UInstancedStaticMeshComponent> SiteGridLines;

	UPROPERTY()
	TObjectPtr<class UInstancedStaticMeshComponent> SiteWallPanels;

	UPROPERTY()
	TObjectPtr<class UInstancedStaticMeshComponent> SiteWallPillars;

	bool bSiteDressed = false;

	/** AUTO-PAINTED BAY MARKINGS (owner 2026-08-26 night: "use the
	 *  floor decals but how do we get them to auto paint as stations
	 *  are placed?"). Every placed station stamps a hazard border and
	 *  a wear patch onto the floor through decal components, sized to
	 *  ITS footprint and rotated with it; the paint is rebuilt only
	 *  when the station's placement actually changes, and lifts with
	 *  the station on removal. Materials are the project's own
	 *  decal-domain instances (MI_LB_BayHazard_v001 /
	 *  MI_LB_BayWear_v001). */
	struct FLBSpacecraftFloorPaint
	{
		TArray<TObjectPtr<class UDecalComponent>> Decals;
		FTransform PaintedAt = FTransform::Identity;
	};
	TMap<FName, FLBSpacecraftFloorPaint> StationFloorPaint;

	void RefreshStationFloorPaint(
		const struct FLBSpacecraftStationRecord& Record,
		const struct FLBSpacecraftStationDefinition& Definition);

	/** Puts the sun and sky under the palette instead of the map.
	 *  A warm key tints every albedo in the scene at once, so this is
	 *  the one colour decision that cannot be corrected downstream. */
	void ApplySceneLighting();

	void RefreshSiteDressing();

	/** In-hull fittings (owner 2026-08-26 night: "shove the bits in and
	 *  fill spaces with pipes and cables"): during the open-form middle
	 *  stages the six components appear at sockets inside the hull as
	 *  the craft progresses, then pipe/cable runs fill the gaps. The
	 *  parts attach to the unit component and ride with it. */
	struct FLBSpacecraftUnitFittings
	{
		TArray<TObjectPtr<UStaticMeshComponent>> Parts;
		int32 RevealedCount = -1;
	};
	TMap<FName, FLBSpacecraftUnitFittings> UnitFittings;

	void RefreshUnitFittings(FName UnitId,
		UStaticMeshComponent* UnitComponent, int32 RouteIndex,
		int32 RouteCount, bool bCargoRecipe);
	void ClearUnitFittings(FName UnitId);

	/** The opening beat (owner 2026-08-26 evening): a new craft does
	 *  not pop into existence - the HEAVY drone flies the bottom shell
	 *  (the recipe's chassis form) to the first station and drops it.
	 *  The unit visual stays hidden until the drop completes. */
	struct FLBSpacecraftShellDelivery
	{
		float Elapsed = 0.f;
		FVector StationLocation = FVector::ZeroVector;
		TObjectPtr<UStaticMeshComponent> DroneComp;
		TObjectPtr<UStaticMeshComponent> ShellComp;
	};
	TMap<FName, FLBSpacecraftShellDelivery> ShellDeliveries;
	TSet<FName> ShellDeliveredUnits;

	void BeginShellDelivery(FName UnitId, const FVector& StationLocation,
		class UStaticMesh* ShellMesh);
	void TickShellDeliveries(float DeltaSeconds);

	void RefreshLineStationFrame(
		const struct FLBSpacecraftStationRecord& Record,
		const struct FLBSpacecraftStationDefinition& Definition);
	void DestroyLineStationFrame(FLBSpacecraftLineStationFrame& Frame);

	/** RATE BADGE (research: every benchmark floats throughput over the
	 *  machine): a TextRender above each line station - its split index,
	 *  fit count and live state, all from GetFixingSplit and the
	 *  coordinator, never invented. */
	void RefreshStationBadge(
		const struct FLBSpacecraftStationRecord& Record,
		const struct FLBSpacecraftStationDefinition& Definition);

	/** VISIBLE STOCKPILE (research: benchmark machines show their
	 *  contents; ours shows real inventory): pallet stacks beside each
	 *  line station scaled to the station store's actual fill. */
	void RefreshStationStockpile(
		const struct FLBSpacecraftStationRecord& Record,
		const struct FLBSpacecraftStationDefinition& Definition);

	TMap<FName, TObjectPtr<class UTextRenderComponent>> StationBadges;
	TMap<FName, TArray<TObjectPtr<UStaticMeshComponent>>>
		StationStockStacks;

	/** A registered no-collision mesh component for a laid track piece. */
	class UStaticMeshComponent* MakeTrackPieceComponent(FName Key,
		class UStaticMesh* Mesh);

	/** Swaps the cap's orange accent slot for the Start-anchor blue. */
	void TintTrackCapForStart(class UStaticMeshComponent* CapComponent);

	/** ROLE LIGHT (audit 2026-09-01): one floor bar per line station,
	 *  working-blue with a craft in the bay, idle-grey without. */
	TMap<FName, TObjectPtr<UStaticMeshComponent>> StationIndicatorBars;

	/** FIT-MOMENT FEEDBACK (owner 2026-09-01 "its not actualy fitting
	 *  them"): per-unit fitted-count watermark, flash timer, and the
	 *  blooming ring component that announces an interior part
	 *  landing where the closed hull cannot show it. */
	TMap<FName, int32> UnitFittedSeen;
	TMap<FName, float> UnitFitFlash;
	TMap<FName, TObjectPtr<UStaticMeshComponent>> UnitFitFlashComps;

	/** THE BELT IS ONE OBJECT (owner 2026-09-01 "make better track"):
	 *  the whole chain renders as a single smooth spline with sleeper
	 *  rhythm and authored end caps, rebuilt only when the piece set
	 *  changes. */
	TObjectPtr<class USplineComponent> TrackSpline;
	TArray<TObjectPtr<class USplineMeshComponent>> TrackSplineMeshes;
	TObjectPtr<class UInstancedStaticMeshComponent> TrackSleepers;
	TArray<TObjectPtr<UStaticMeshComponent>> TrackCaps;
	FString TrackRenderSignature;
	UPROPERTY()
	TObjectPtr<class ALBSpacecraftTrackAuthority> TrackAuthority;
	TMap<FName, TArray<TObjectPtr<UStaticMeshComponent>>> BufferCrates;
	TMap<FName, TObjectPtr<UStaticMeshComponent>> HaulerBodies;
	TMap<FName, TObjectPtr<UStaticMeshComponent>> HaulerCrates;

	TSet<FName> StationMeshLoadFailed;

	/** The loaded real mesh for a definition, or nullptr (logged once). */
	UStaticMesh* TryGetStationMesh(FName DefinitionId);

	UPROPERTY()
	TArray<FLBSpacecraftDepartingVisual> Departing;

	bool bCraftMeshLoadAttempted = false;
	float VisualTimeSeconds = 0.f;

	void RefreshStations();
	void TickDepartures(float DeltaSeconds);
	void RefreshUnits();
	/** A small additive glow sphere riding a parent component - the
	 *  drones' nav strobes and work lights. */
	UStaticMeshComponent* MakeGlowSprite(const FString& Key,
		UStaticMeshComponent* AttachTo, const FVector& RelLocation,
		float SizeCm, const FLinearColor& Colour,
		UMaterialInstanceDynamic*& OutMID);

	UStaticMeshComponent* MakeBlockComponent(FName Key,
		const FLinearColor& Colour);
	UStaticMesh* ResolveCraftMesh();
};
