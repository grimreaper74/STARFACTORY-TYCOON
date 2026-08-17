# Session handover — 2026-08-16 into 2026-08-17

Where the factory stands after the audit-and-fix session, what is proven, and
the decisions waiting on the owner. Companion to the per-shop audit notes.

## Where the game is

`PlayableShell_v009` is the current archived build
(`E:/LineBossValidationOutput/Builds/`). The packaged journey — commission →
order → 57 stations → quality hold → player decision → dispatch — runs green,
with the full-density press shop resolving **2,804 instances across 1,179
batches, 0 unresolved mesh paths from cooked content**. The automation suite
is **278/278** (up from 275; three new contract tests this session).

The factory is one continuous building, coils to finished car, at the restored
reference shop's detail standard. All four press trains stand on the reference
2200 cm row grid.

## What this session changed

**Press.** Rebuilt at full reference density (1,522 → 2,804 pieces) after the
owner rejected the earlier pass; six-dimension audit; train pitch corrected to
the reference grid; save-load presentation restore; camera-aware roof; lit
pass (floor-band luminance 18.2 → 37.4/255); outbound and service edges
dressed; Nanite on the 1.9M-triangle coil.

**Weld.** Six-dimension audit, then two versioned contract changes: **v002**
(robots moved from 1240 cm to the pack-validated ±300 cm contact positions
with FK poses from the pack's own validation, a tool on all 36 arms, authored
fixtures replacing engine-cube slabs, fail-closed visibility) and **v003**
(the PR004 dress pack on every robot at the measured 0.68 fit). Counts
re-frozen 469 → 489 → 597 with tests regenerated in the same commits.

**Paint and assembly.** Six-dimension audit found both shops' dressing
standing duplicate machines on top of their frozen presentations — the same
defect the weld pass caught for Body. Deduplicated; fail-closed visibility
guards added; cook-manifest contract tests added for both shops.

**Commissioned models.** Five built Blender-native to the family conventions
and imported with brand materials bound: the paint ED dip tunnel, the press
coil-scale platform and scrap baler, the weld closure turntable, and the
robot dress pack (reused from PR004 at the measured fit).

**Project-wide.** HUD localisation-ready (`LOCTEXT` with plural forms),
contact shadows grounding the machines, `/Engine/BasicShapes` and the
manifest's roots pinned in the cook list.

## Decisions waiting on the owner

1. **Paint presentation v002 — enclosure or open process?** The commissioned
   ED dip tunnel and the presentation's tracked open ED line (tanks, rails,
   immersed body) cannot share the ED coat station: the enclosure hides the
   line the contract exists to show. Both are legitimate; the choice is a
   product one. The dip tunnel is built, imported and cooked, waiting on this.
2. **Assembly furniture scope.** The audit flagged marriage/rolling-chassis
   visual identity and station feeds (seats, glazing, fluids, overhead
   conveyor) as a possible v002 — how far to take it is a design call.
3. **Progression and UX gate items.** Unlock/price/purchase wiring, controller
   parity and the alert inspector remain open checklist rows; these are
   gameplay design rather than defect fixes.

## Where the detail lives

- `PRESS_SHOP_RELEASE_AUDIT_2026-08-16.md` — press findings and fix ledger.
- `ONE_FACTORY_BODY_WELD_STARTER_INTEGRATION_v002.md` — weld v002 and v003
  contracts.
- `PAINT_ASSEMBLY_RELEASE_AUDIT_2026-08-16.md` — paint/assembly findings.
- `ONE_FACTORY_CONTINUOUS_BUILDING_DECISION_2026-08-16.md` — the architecture
  decision and why the reference map stays a read-only input.
- Captures: `Docs/OneFactory/Captures/20260816_*` and `20260817_*`.
- Full audit findings, including the minors not yet actioned, are in the
  workflow journals under `subagents/workflows/`.
