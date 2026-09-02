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
