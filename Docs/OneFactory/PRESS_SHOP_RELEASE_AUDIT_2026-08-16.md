# Press shop release audit — 2026-08-16 (night)

Owner request: *"can you do a full audit on the press shop and fix it to
release quality?"* A six-dimension multi-agent audit (reference parity, visual
evidence, code correctness, release gate, cook coverage, runtime contracts)
produced ~45 findings; every serious finding was adversarially re-verified
against the actual files, and the survivors were synthesised into a 28-item
dependency-ordered fix list. This note tracks execution.

## Landed this session (verified, suite 275/275 after each tranche)

1. **Train pitch corrected to the reference 2200 cm** (was 2251 with no
   provenance). Identity-plate drift is now 0 cm on all four rows, and the
   whole row-keyed manifest grid re-registers with the trains.
2. **Row-B/PR-010 interpenetration resolved by the pitch fix**: the blank
   supermarket's bounding-box overlap with train B is the reference's own
   authored interlock (lanes feed the S01 destacker end); on-grid trains mesh
   with it as authored. Verified in the 45° aerial.
3. **Save-load presentation restore + idempotent commissioning**:
   `EnsureSitePresentation()` (find-existing before spawn, every builder
   rebuilds its own content) runs from B — including after a restore or
   console build, when `BuildAndCommissionWholeFactory` reports already-built
   — and from a successful F9 load.
4. **Dressing rebuild safety**: per-build components (trains, apron, flow
   route) are tracked and destroyed on rebuild; no more NewObject over live
   registered components on the console rebuild path.
5. **Roof state is per world** (PIE/editor/reload no longer share or corrupt
   one static set), and a rebuilt envelope re-applies the current roof state
   to its fresh deck. `IsRoofHidden` exposes the state.
6. **Envelope default height unified at 2200 cm** (console default was 1800,
   which sliced the deck through the truss chords).
7. **Dev camera and tour lifecycles**: one camera per world (was leaking one
   per framing), the tour actor destroys itself when finished, and the line
   advances exactly once per stop at the promised simulated seconds (was
   advancing every tick, ~39× faster).
8. **Destacker clearance guard** tests in the datum's local frame against all
   four rows at 2200 pitch (was world-axis, row A only).
9. **Blank buffer and panel inspection dressed** (stillages/racks; bench +
   light ramp keyed by station id — the press `bQualityGate` flag is never
   true, so the ramp had been dead code).
10. **Press WIP stands on the outfeed side** (±900 cm across the line, clear
    of the train's ±678 cm body), and transfers into the train aim at the same
    point, so units no longer render inside the press for most of the cycle.
11. **Wide-span trusses read dark**: `CA_MW_StructuralSteel_DarkGrey_TBC` is
    authored 0.8-white despite its name; the manifest now overrides the 12
    trusses to `M_LB_ShellCharcoal` through the existing authored-override
    path.
12. **Clip finding resolved by analysis, no change**: the audit's press-bay
    rectangle predates the one-continuous-building decision. The manifest maps
    the full 220×120 m reference facility (ref X −15850..6650, Y −1590..9607)
    and all of it lands inside the Moorcross envelope.

Captures: `Captures/20260816_21_AuditFix*`.

13. **Lit pass landed** (second tranche follow-on): the skylight was set to
    `SLS_SpecifiedCubemap` with no cubemap — contributing nothing — and now
    captures the scene; the single 7×7 route-union lamp grid became
    per-department grids (~one lamp per 18 m bay, 68 000 intensity); the
    reference's 28 authored `SM_Lamp01` fixtures each carry a real point
    light. Floor-band luminance at the `Press@0p16~10` camera: 18.2 → 37.4
    /255 (audit target 40; the shortfall is the intentionally dark deck band
    and charcoal machine faces), dark fraction 68.4% → 39.2%, aerial 87.6.
    Exposure bias stays −0.50 per the standard. Captures:
    `Captures/20260816_22_LitPassB_*`.

14. **Outbound and service edges dressed** (fixes 14–16, 20): PR-043
    marshalling lanes, PR-044 dispatch lorry, PR-040 quarantine pen, PR-039
    first-off scan cell, PR-041 scrap row and baler, the PR-004 cell robot
    and tool rack, and the PR-002 coil-scale position — datum-keyed kit
    placements, packaged in v006.
15. **PlayableShell_v006 packaged and proven** (fix 21, milestone build): the
    first attempt omitted `-map` and the map never cooked — the repack with
    `-map` passed. Packaged journey: 2,804 restored-shop instances, 1,178
    batches with authored overrides, **0 unresolved from cooked content**;
    1,335 dressing instances; commission → order → run → tour green.
    Archive: `E:/LineBossValidationOutput/Builds/PlayableShell_v006`.
16. **Conveyors follow the painted Manhattan legs** (fix 19): long
    inter-department runs no longer cut diagonals; suite green.
17. **Engine basic shapes pinned in the cook list** (fix 10):
    `/Engine/BasicShapes` is now an explicit always-cook root instead of a
    side effect of unrelated ConstructorHelpers.

## Remaining from the fix list (open, in dependency order)

- **East-end dressing** (PR-039 first-off scan, PR-040 quarantine, PR-043
  marshalling lanes, PR-044 FLT dispatch), **PR-041 scrap/baler bay**,
  **PR-004 cell robot**, **PR-002 coil scale**, head-cluster reskin.
- **Conveyor Manhattan routing** at the Body→Paint and Paint→Assembly runs.
- **v449 promotion into the owned root + versioned aggregate/provenance
  contracts** (test regeneration).
- **Panel-inspection quality-gate decision** (versioned contract change).
- **Progression/UX gate items** (unlock/price wiring, controller parity,
  inspector), **HUD FText localization**, **coil LODs + performance budget**,
  **engine-asset cook pinning**.
- **Package PlayableShell_v006** from the final revision with the full
  evidence set, then **reconcile the gate ledger and obtain owner
  acceptance** — the release-quality claim stays open until the owner accepts.
