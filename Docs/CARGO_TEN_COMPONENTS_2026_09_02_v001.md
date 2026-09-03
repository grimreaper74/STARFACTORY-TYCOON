# The Cargo carries ten component kinds: the line grows by components per craft

**Date:** 2026-09-02, late. **Status:** validation-only (indexed suite plus
PIE frames; no fresh packaged journey). **Owner direction:** asked whether
"loads of small parts" meant more stations, agreed that small parts stay
off the line in the fabricator cells and that what lengthens the line is
components per craft (Mk2 about ten, the Cargo-size roles fourteen plus),
then "ok do it".

## What the second tier is here

The craft ladder in the catalogue is Scout-01 (tier 1, six component
kinds) and Cargo-01 (tier 2, reputation tier 2, needs Mk2 station marks).
Before this pass the Cargo differed from the Scout only in INSTANCE counts
of the same six kinds (three hulls, three power, three engines, two of
the rest), stage times and price. Ten kinds, as agreed, means the Cargo
gets four kinds of its own.

## The four, each backed by real parts

| Kind | On the hull | Sub-assembly recipe (Sub-Assembly Robot) | Import price |
|---|---|---|---|
| Cargo Bay | the hold under the belly | 6 bulkhead panels, 4 floor pans, 2 hull sections, 2 access hatches, 2 pressure doors | 11,940 cr |
| Docking Collar | on top, amidships | 2 pressure doors, 1 access hatch, 4 connector blocks, 4 frame ribs, 1 ranging laser, 2 beacon lights | 6,660 cr |
| Thruster Pods (a pair) | aft, one each flank | 8 RCS thrusters, 4 valve blocks, 6 fuel lines, 4 gimbal actuators, 2 fuel tanks | 14,770 cr each |
| Shielding | low along both sides | 24 heat-shield tiles, 4 radiator panels, 2 bulkhead panels, 4 frame ribs | 14,950 cr |

Import prices are the part basket at import prices plus 15%, the rule the
other six follow, computed from the catalogue when they were added. Every
input is a part the catalogue already priced; no new sub-parts.

## What changed

- `ELBSpacecraftComponent` gains `CargoBay`, `DockingCollar`,
  `ThrusterPods`, `Shielding`, appended so saved component bytes keep
  their meaning; `LBSpacecraftComponentKindCount` (10) replaces the
  literal six in the item-table mirror check and the BOM count check.
- Item rows, import prices and the enum-to-item mapping for the four;
  four `Recipe.Component.*` sub-assembly recipes on the Sub-Assembly
  Robot.
- The component fabrication stage produces the four (a recipe that does
  not require them never produces them).
- Cargo-01: ten required kinds; its OWN fixing order (shell, powerplant,
  engines, bay, collar, pods, wiring, avionics, cabin, plating last) with
  three new access edges (the plating closes over the bay, the collar and
  the pods); pods counted as a pair; staging 45 to 60 s and assembly 180 to
  240 s; price 360,000 to 440,000 cr so importing all ten kinds (about
  375,000 cr with the instance counts) keeps the thin margin the Scout's
  price follows. The Scout is untouched.
- The starting loadout stocks the Scout's kinds, read from its recipe,
  instead of every kind there is.
- Presenter: the fitting reveal is recipe-driven (kinds plus the canopy)
  in the recipe's fixing order, and the four new kinds appear as
  hull-relative blockouts (a bay under the belly, a collar on top, twin
  pods aft, plating low along both sides), hue-free so the livery stays
  the only colour on the craft, to be replaced by real parts when
  modelled. Kit dollies show the crate fallback for them.
- Dev: `LB.Spacecraft.BuildLine mk2` places the Mk2 marks (research
  permitting) so the Cargo can be run from the console.

## Evidence

- Suite `LineBoss.Spacecraft`: see the status line at the end of this
  document for the indexed report. New test
  `Production.TheCargoCarriesTenKindsEachBackedByRealParts` (ten kinds,
  item rows, prices, a recipe that makes each, the fixing order
  validating with the plating last, the Scout untouched at six). The
  refit-pricing test now checks both tiers (the Scout's six and five,
  the Cargo's ten and nine).
- PIE (`Saved/Audits/CargoTen_2026_09_02/`): `LB.Spacecraft.BuildLine mk2`
  placed five Mk2 marks and the booth, the line commissioned, a forced
  Cargo contract was accepted at 440,000 cr (`c1_parts_a_panel.png` shows
  the held contract and the first of the ten part tiles, "Cargo Bay"
  among them; `c1_split_a_panel.png` the Build tab with the heavy
  marks), and the craft walked the ladder: `run8.log` shows
  HullFabrication with one kind produced, then ComponentFabrication
  with TEN - the four new kinds are produced, consumed and fitted by the
  same machinery as the six.

## What the suite caught on the way

The stage table lists every kind the fabrication stage can produce, and
the first cut let every recipe produce all of them - a Scout left
fabrication carrying the Cargo's bay and collar, and the refit pricing
helpers priced a Scout refit for nine kinds. Both now filter by the
recipe's required kinds (`AdvanceUnit`, `ComponentsEarnedBy`,
`ComponentsRefittedFrom`, `RefitWorkFraction`), with the callers passing
the recipe they have.

## Mk2 soak, 2026-09-03: five Cargo ships, one-part-per-trip, no haul stall

A fresh Mk2 line (dock, rack, a 20-unit float of every kind in the yard)
took a forced five-unit Cargo contract and ran unattended at 4x for
about 30 real minutes (~1800 sim seconds). All five ships reached
`Dispatched` with all ten kinds produced; the WIP cap (3) held the
whole time, cycling a new unit in as each one cleared a stage; station
shelves for all five Mk2 marks stayed fed throughout (`run12b.log`,
`run13_continue.log`). In that whole run the only hold was
"Holding: station SprayBooth-007 occupied", twice, both self-resolving
- a single-craft paint booth queuing behind Assembly's faster throughput
is the ordinary shape of that hold, not a fault. No haul-shortage alert
("insufficient resources", "nothing can carry them") appeared even once
across five ships' worth of ten-kind, one-part-per-trip hauling.

One real cost this exposed: the five-quantity contract's OWN deadline
(sized from nominal per-unit time × quantity) is tighter than five
ships actually take once the WIP cap and real haul time are accounted
for - it expired with four of five sold and the fifth finished but
unsold, and the existing "finished ships wait in stock and sell when
you next accept a contract" rule (built 2026-09-01) caught it cleanly:
cash kept arriving, nothing stuck. This is a property of a single large
forced quantity, which a real player rarely takes in one contract (the
board offers 1-4 at a time); noted, not changed - the safety net it
exercised already does its job.

A test artifact worth naming so it is not mistaken for a game bug: this
soak's `LB.Spacecraft.Start ... force` contracts, like every dev-forced
contract, carry no customer, and the panel's "Ships delivered" objective
counter stayed at 0 across all five real dispatches even though cash was
paid each time - only the delivery-count counter, not the sale. Not
chased down: `force` is a testing shortcut that already skips the
reputation gate by design, and this looks like the same category of
gap, on a path a real player accepting a real board contract does not
take. First frame `Saved/Audits/CargoCraft_v001_2026_09_03/s_final2.png`
shows the settled state: 2,604,422 cr, one Cargo in stock, line idle.

## Not proven

- **The four new kinds on the Cargo's hull.** The Cargo's craft forms
  (chassis, airframe, fitted - the assets exist under
  `SpacecraftTestBay_v001/Meshes`) are still behind the presenter's
  `bBlockoutMeshyContent` switch, so a Cargo on the line draws as the
  crate form with landing gear, and the fitting pass that would attach
  the bay, collar, pods and plating runs only on a real build form
  (`c2_st005_zoom.png`). The blockouts are written and recipe-driven;
  they will show the moment the Cargo forms are allowed through, which
  is the Meshy-provenance lift the standing plan already calls for
  (`Docs/MESHY_PROVENANCE_REVERSAL_PLAN_v001.md`), and not a partial
  lift to be done here.
- No packaged build.
- No model for any of the four: blockouts on the hull, crates on the
  dolly, until they are commissioned.
- A saved Cargo line from before this pass carries a six-kind fixing
  split; re-commissioning re-splits it. No such save exists in the
  project's records.

**Status line.** Suite `LineBoss.Spacecraft`: 142 of 142 Success, indexed
at `Saved/Automation/CargoTen3_2026_09_02/index.json` (the two earlier
runs of the evening, `CargoTen_2026_09_02` and `CargoTen2_2026_09_02`,
are the failing runs that caught the two filtering bugs above and the
six tests that had pinned "six"; kept as evidence).

## Addendum, 2026-09-03: the owner chose A, and it is in the game

The owner answered "a" to the contact sheet. The blunt freighter's
preview geometry went through the lane as it stands (materials are
authored in Unreal, so the textured refine was not bought):
`Tools/export_meshy_glb_v001.py` imposed 2100 cm on its longest axis
(source bounds 1.90 x 1.21 x 0.65 m, scale 11.04, base on the ground);
`Scripts/import_cargo_craft_v001.py` imported it as
`/Game/LineBoss/Candidates/Spacecraft/CargoCraft_v001/SM_LB_SC_Cargo01_Craft_v001`,
Nanite on, measured 2100 cm against 2100 declared, extent 2100 x 1335 x
712 cm, source sha256 recorded (`Saved/Audits/Spacecraft/cargo_craft_import_v001.json`;
its schema, status and provenance labels were corrected after the run,
the lane having been copied from the station-dress importer). The folder
is in `DirectoriesToAlwaysCook`.

In the presenter it is registered as `Craft.Cargo01`, promoted under the
`Craft.` prefix, and a Cargo unit wears it from the moment its hull is
produced; the Scout stand-in at 1.5x and its four blockouts now apply
only if this mesh fails to resolve. One mesh, bay, collar, pods and
plating sculpted into it: a Cargo therefore shows whole from its hull
stage on, and the per-kind fitting moments the Scout has come only when
this model is split into fitted parts in Blender, which is the next
modelling step. The mesh is 1335 cm wide and 712 tall against the
recipe's declared 1119 x 580 envelope; the capacity law reads the
recipe, so this is a cosmetic mismatch to settle when the model is
split.

**Evidence for the model in the game** (`Saved/Audits/CargoCraft_v001_2026_09_03/`):
`run10.log` - an Mk2 line built from the console, a forced Cargo
contract, the log line "station mesh bound for Craft.Cargo01", the craft
walking the ladder to Testing; `c4_st005.png` - the freighter on its Mk2
station at hull stage (the real mesh, close); `c4_booth_wide.png` - the
craft in its hover test over the spray booth; the contract then settled
at 440,000 cr ("CARGO-01 Complete", "Ships delivered: 1", `c5_depart_3.png`
the runway after departure). Not proven: a wide, unobstructed frame of the
finished Cargo on the line (closed by `cargo_real_station5.png` the same
night), the departure itself on a frame, and the fitted-part moments,
which need the model split.

**Checked, 2026-09-03: the livery paint reaches the real mesh, unmodified.**
The primer/paint code in `TickSubAssemblyLogistics` is generic - it keys
only on `Assignment.UnitId`/`Unit->RecipeId`, never on which mesh the
unit's component currently holds - so it was never expected to need
Cargo-specific work, and a live check confirms it: the Cargo unit's
material slot 0 is `MID_M_LB_ShipPaint_v001_0`, the same dynamic paint
instance every craft wears. Every frame captured of it tonight was
white because it was filmed under `LB.Spacecraft.Start ... force`, the
dev console's contract path, which - like every dev-forced contract
before it - never attaches a customer, so `LiveryForRecipe` falls back
to white (confirmed in `StartRecipeContract`, unchanged by this work).
The REAL offer board (`RefreshOfferBoard`) sets a customer and a real
livery colour for any recipe the player's reputation tier allows,
Cargo included, through the same `FLBSpacecraftCustomerCatalogue` the
Scout uses - there is no special case that would treat it differently.
Not proven on a frame: an actual customer-coloured Cargo, which needs
reputation tier 2 reached through real deliveries rather than the dev
console.

**Later the same night:** the wide frame came (`cargo_real_station5.png`,
`c8_sheet.png`): a fresh Mk2 line with a delivery dock, every part of a
Cargo ordered through the console and hauled to the shelves one component
at a time by the dock's drone, the freighter standing whole on its fifth
Mk2 station under the crane at component fabrication with ten kinds
produced. Also found and fixed on the way: the dev `StockComponents`
command stocked a flat four of each allocated kind and only the Scout's
six into the yard, which filled a Cargo head station's shelf with kinds
it had plenty of and left no room for the hulls it was short of - it
follows the recipe's kinds and counts now. Still not proven: the
departure on a frame, and the fitted-part moments.

## Addendum, 2026-09-03: the owner's own thruster pod is in the game

The owner's own GPT reference image (see the chat record) went through
Meshy's image-to-3D as a `.blend` drop - the first attempt at this part
that actually reads as a thruster on the render: a plain cylinder, a
bolted mounting collar at the front, and at the rear a nozzle that
genuinely flares outward, unlike either of the two text-to-3D tries
(`CargoParts_v001`, `CargoParts_v003`) that came before it. 14,008
clean triangles, no materials packed. `Tools/export_meshy_blend_axis_v001.py`
(new - the .blend counterpart to `export_meshy_glb_v001.py`'s single-axis
sizing, since the existing `export_meshy_blend_v001.py` sizes by a two-axis
footprint for buildings, not a part's one defining length) imposed 180 cm
on its longest axis; `Scripts/import_cargo_thruster_pod_v001.py` imported
it Nanite-on with the size measured at 180.0 against 180 declared
(`Saved/Audits/Spacecraft/cargo_thruster_pod_import_v001.json`).

Registered as `Pallet.pallet-thrusterpod` and wired into
`GetKitPalletCandidates` for `Component.ThrusterPods`, which is the one
place both the kit dolly's pallet load AND the hauler's carried cargo
already resolve from - the same mechanism the Scout's six real
components use. Not yet wired: attaching it directly onto the Cargo
hull as a fitted part, which needs the hull split (see below).

Proven on a frame (`Saved/Audits/CargoParts_v001_2026_09_03/pod_carry_hero.png`):
a cargo-lift drone carrying the real pod, slung under its claw, on a
flight out of the delivery dock - confirming the same registration that
feeds the kit dolly also feeds the hauler, live, in PIE. Not proven:
the same pod actually sitting in a station's own kit bay on a frame -
the five stations checked that same run did not happen to have it in
view at the zoom used.

## Addendum, 2026-09-03 (same night): the bay door, collar and plating land

The owner's three remaining GPT reference images, run through the same
image-to-3D lane as the thruster pod, all read clean on an isolated
render before anything was imported: a bay door (200 cm longest axis),
a docking collar (180 cm) and a plating strip. The plating's size was
the one real judgement call - an earlier session's blockout fraction
implied something nearer 11.5 m for this slot, but tonight's own Meshy
prompt anchored it at "about as long as a car", so 460 cm (the
prompt-consistent figure) was declared rather than the older, larger
number; covering the hull's full length is a later tiling decision on
the smaller asset, not a reason to inflate the source part itself.

`Scripts/import_cargo_parts_v005.py` imported all three Nanite-on, sizes
verified within 3% (`Saved/Audits/Spacecraft/cargo_parts_v005_import_v001.json`),
registered in `CargoOwnPallets` alongside the thruster pod. All four of
the Cargo's own kinds now resolve to real meshes through
`GetKitPalletCandidates`, the same mechanism proven live for the
thruster pod above.

## Addendum, 2026-09-03 (later): the hull is split for real, from the owner's own model

The owner had a "better Cargo" made and asked Meshy to split it -
`Meshy_AI__0903101341_part-segmentation.blend`, the first genuine
multi-object drop of the night (7 separate mesh objects, not one fused
mesh scored into islands). Isolated renders of all seven identified a
real kit: two engine nacelles (independent geometry, not a mirrored
pair - 85,785 and 54,537 triangles), two landing legs, a boarding ramp,
and two overlapping slices of the hull body itself (both carrying the
same distinctive octagonal hatch - the tell that these were two cuts of
one volume, not two adjacent parts).

The kit arrived in an exploded pose. Every part except the hull pair
snapped cleanly onto an anchor (`model_part3`) by sliding it back along
its own explosion vector until its surface (sampled vertex clouds, not
just bounding boxes - a corner-touch pass first, then a stricter
nearest-surface pass) met the growing assembly; both passes converged
on the same visible gap between the two hull slices, which is what
confirmed they do not mate as adjacent pieces. Owner's call: "just fuse
part 2 and part 3 together." Pushed further along the same vector, the
two slices' surface-containment fraction peaked at 71% (from 0%),
proof of real volumetric overlap - genuine duplicate coverage of one
body, not two complementary halves - so a real Boolean union was run
rather than a plain join (252,936 tris, no fallback needed; the source
cut geometry was non-manifold at the seam - 67/71,850 and 436/403,150
non-manifold edges - but the solver handled it). The two landing legs
and the ramp were joined onto the fused hull as fixed furniture (owner:
they are not drone-fitted components, this is not a new pair of
component kinds - keeps `LBSpacecraftComponentKindCount` at ten). All
three final pieces were decimated after a render check held up the
panel detail (hull 282,747 -> 38,940 tris; engines 85,785 -> 14,999 and
54,537 -> 11,999) and exported at declared real-world sizes on the same
axis convention every part in this doc uses: the hull at 2100 cm
longest axis (matching the live v001 craft, so it drops in without
retuning anything downstream), each engine at 180 cm (matching the
already-verified standalone thruster pod, so it sits right at the
already-tuned socket).

`Scripts/import_cargo_craft_v002.py` imported all three - hull, engine
A, engine B - Nanite-on, sizes verified exactly on declared
(`Saved/Audits/Spacecraft/cargo_craft_import_v002.json`). `Craft.Cargo01`
now points at the v002 hull; v001 is left on disk, untouched, as
evidence. The two engines are registered as `Pallet.pallet-thrusterpod-a/-b`
and wired into `RefreshUnitFittings`'s `Component.ThrusterPods` handling
as a special case: when BOTH resolve, they replace the two-block
blockout at the same two hull-relative fractional sockets that blockout
already used (`(-0.30, ±0.48, 0.05)`) rather than one of the two ever
appearing alone; if either is missing it falls through to the existing
generic single-mesh path and, from there, to blockout - never a
half-fitted pair. The older generic `Pallet.pallet-thrusterpod` stays
registered for the kit-dolly/hauler display, which wants one
representative mesh, not a pair.

**Proven:** the import (measured sizes and triangle counts, Nanite on,
all in the receipt); the build (clean compile); the wiring, functionally
- across this session's testing, nine Cargo units were started and at
least five completed the full pipeline end to end (fabrication through
dispatch) with the new hull and the new ThrusterPods branch live, zero
crashes or errors. My own Blender renders of the fused, decimated kit
(`Saved/Audits/...` scratch renders, not yet moved into the repo) show
the assembled result matching intent: twin engines flanking the hull,
legs and ramp in place, the hull seam essentially invisible after the
Boolean fuse.

**Not proven:** a clean in-game screenshot of the mounted engines on a
live unit. Extensive attempts this session to catch a unit at its
Assembly-stage station via the dev camera (`LB.Spacecraft.Watch`) and
`capture_image` kept missing - the craft moves through each station
faster than a Watch-then-capture round trip can reliably land on, and
partial glimpses at station edges were consistent with, but did not
conclusively confirm, the new grey/graphite parts in position. This is
a tooling/timing gap in how this session drove the camera, not a
red flag about the underlying wiring - the pipeline itself ran clean
across many full cycles - but it should be looked at on an actual frame
before calling the visual result decided, per house rule.

**Separate finding, not fixed tonight:** a contract accepted for exactly
as many units as were force-started can leave an orphaned unit stuck at
`MaterialIntake` forever. `TryStartUnit`'s own demand scan
(`LBSpacecraftRuntimeCoordinator.cpp`) only checks
`Contract.DispatchedCount >= Contract.Quantity`, but `CreateUnit`'s
`UnclaimedDemand` check (`LBSpacecraftProductionAuthority.cpp`)
apparently also counts in-flight, undispatched units against that same
quantity - so a unit that never got a runtime assignment (seen once
this session, cause not isolated) permanently eats one unit of demand
against its contract with no way to cancel or clear it. Reproduced
directly: `LB.Spacecraft.Start 1 CARGO-01 force` before a `DeliveryDock`
existed left a unit sitting at `MaterialIntake` for over 700 sim-seconds
with `simAlert: "No accepted contract demand for this recipe"` even
though nothing else was in flight; a fresh, larger-quantity contract
worked around it, unclaimed demand never returned to true zero. Worth a
look on its own - a single-ship contract is an entirely normal thing
for a real player to accept.
