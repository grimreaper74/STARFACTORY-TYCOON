# Press shop polish pass — 2026-08-16 (evening)

Owner direction: *"can you stop on press shop and polish the models"*, with the
Cairnwell/Moorcross design sheets supplied in chat as the bar (local copies
under `SourceAssets/Reference/` and `Docs/References/`). Close-up evidence was
gathered first — the new tour close-up syntax (`Press@0.16~10` = 16% of the
solved distance, 10° pitch) shot the trains from management height down to
floor level before anything was changed.

## What the evidence showed

The v449 trains themselves already meet the sheets at close range: Cairnwell
green press bodies, charcoal crowns, station badges, stack lights, guarding.
The gaps were around the machines, not in them:

1. **Materials lost in extraction.** The restored-shop manifest carried mesh +
   transform only; the reference map authors per-actor overrides on 811
   real-mesh actors (crane girders in aged RAL1023 with dark/exposed steel,
   guard posts in smooth safety yellow/charcoal, the layered brand set across
   PR-008/PR-009 kit).
2. **Black void above the trusses.** The restored shop's wide-span trusses
   hang at 1740 cm with top chords near 2000; the envelope's 1400 cm walls and
   deliberately-missing ceiling left the whole roof zone floating on black.
3. **No production-flow routes** on the floor, which the approved mockup
   paints in green.

## What changed

- **Override fidelity restored.** `extract_shop_mats.py` (read-only, scratchpad
  + `Tools/Diagnostics`) recorded slot-by-slot override materials; all 811
  joined the manifest by (mesh, datum-relative location) — the 756 unmatched
  entries are exactly the dropped engine primitives. The materialiser now
  batches per (mesh, override signature) and applies the authored materials:
  1,522 instances across 723 batches, 582 with authored overrides, 0
  unresolved. A pixel diff against the pre-override captures confirmed the
  change landed (4.2% of the close-up frame, all in the machinery band).
- **Roof follows the camera.** `SetRoofHidden` now exempts the restored shop
  (the owner asked for the cranes — they are release content, and previously
  survived hiding only through an ISM stale-bounds accident), and
  `FrameProductionLine` toggles roof visibility by camera height: above 900 cm
  it hides the roof zone, below it restores it. The envelope grew to 2200 cm
  eaves with a dark roof deck on its own untagged actor, so floor-level views
  read as an enclosed hall — deck, silhouetted trusses, lamp rows — while
  management views still look straight in.
- **Flow routes painted.** The dressing pass draws the whole 57-station route
  in brand green (#2F8A5F), Manhattan-routed with joined corners, aprons and
  authored floors untouched.

## Evidence

- Captures: `Captures/20260816_16_PolishA_*` (before) through
  `20260816_17_PolishF_*` (after); the before/after pair for the void is
  `PolishB_04` vs `PolishD_04`, for the routes `PolishE_01` vs `PolishF_01`.
- Suite: 275/275 after the materialiser change; re-run after the
  roof/deck/route work recorded in the session log.

## Still open (flagged, not smuggled)

- Booth/oven and assembly native-kit swaps (paint/assembly polish) —
  unchanged, tasks #18/#19.
- Packaging the polish (v006) needs the manifest's 720 mesh paths and 125
  override materials cooked; the cook-list additions are not yet made.
- Conveyor dressing still runs diagonal between stations; the flow routes are
  orthogonal but the pack conveyors are not.
- The close-up lighting is dev lighting; a lit pass against the fixed exposure
  standard remains for the release gate.
