# Paint and assembly release audit — 2026-08-16 (night)

Owner request: *"can you audit paint and assembly and fix release quality?"*
Six-dimension multi-agent audit per department (reference parity, visual
evidence, code correctness, release gate, cook coverage, runtime contracts),
every serious finding adversarially re-verified against the files. 50 of 53
agents completed; the synthesis and two verifiers hit the session limit, so
this note records the confirmed findings and the fixes executed directly.

## The headline defect: dressing overlaying frozen presentations

Both shops carried the **same defect the weld pass had already fixed for
Body** — the dev dressing standing a second copy of release content at the
identical canonical station transforms.

**Paint (critical, confirmed).** The frozen paint starter presentation stands
its 113-instance contract at the paint stations; the dressing placed the
native kit at the same transforms:

- Cure: dressing `CuringOvenTunnel` at scale 1.0 exactly co-located with the
  presentation's identity-local cure oven — same mesh, same transform, total
  z-fight. Quality light tunnel: the same exact duplicate.
- Colour coat: a second spray booth at ~0.80 scale *inside* the
  presentation's full-scale booth, plus duplicate extraction and service sets.
- Pretreatment: an enclosed 852 cm wash tunnel over the presentation's four
  open treatment tanks, whose outer tanks at ±486 straddle its ±426 end walls.
- ED coat: the commissioned dip tunnel **enclosing** the tracked ED line —
  open tanks, 20 profiled rails and the immersed body — defeating the
  contract's own `LB.Paint.TrackedEDLineVisible` /
  `LB.Paint.OpenTreatmentVisible` tags.

**Assembly (critical, confirmed).** The presentation stands a skillet carrier
at all 24 positions plus the per-operation fixtures. The dressing added a
second skillet at 11 trim stations (identical mesh and transform), an
ergonomic lift platform through the carrier at 10 rolling-chassis stations, a
**second** marriage gantry at the marriage station, and the alignment bed
through the carrier at end-of-line.

### Fix applied

The Body-branch precedent, both branches:

- **Paint dressing is now a no-op.** The presentation owns the process
  modules. Standing the commissioned `SM_LB_Paint_EDDipTunnel_v001` as real
  content belongs in a versioned **paint presentation v002**, following the
  weld v002/v003 template — not as an overlay that hides the tracked line.
- **Assembly dressing keeps only what the contract lacks**, and never at the
  station centre: robot, bench and parts cart at trim; bench at marriage; the
  lift platform moved beside the line with the wheel racks; the alignment bed
  off-line with the arch spanning downstream.

Verified in the tour: zero `Dress_Paint*` placements remain, assembly places
no skillet and no second gantry (parts carts 11, lift platforms 10, wheel
racks 20, arch 1, bed 1), and the paint line renders unchanged — proof the
presentation was standing all of it and the dressing copies were pure
duplication. Captures: `Captures/20260817_01_Dedupe_*`.

## Open, in dependency order

- **Paint presentation v002**: stand the commissioned ED dip tunnel and the
  native kit as contract content with counts re-frozen and tests regenerated
  in the same commit (weld v002/v003 template). Decide there whether the ED
  station shows the enclosure or the tracked open line — they are mutually
  exclusive at one station.
- **Assembly presentation review**: the audit flagged marriage/rolling-chassis
  visual identity and station furniture gaps (seat/glazing feeds, fluid fill,
  overhead conveyor) as a possible v002.
- **Fail-closed visibility parity**: the weld pass added `IsHidden` guards to
  the builder pair check and save preflight; the audit asks whether paint and
  assembly need the same (their contract counts are equally vacuous while
  hidden).
- **Cook-manifest contract tests** for both shops, mirroring
  `FLBOneFactoryBodyWeldCookManifestContractTest`.
- Remaining minor/polish findings are recorded in the workflow journal at
  `subagents/workflows/wf_c9114080-07b/journal.jsonl`.
