# OneFactory — unattended session handover, 2026-08-16

Written while the user was away. Captures in [`Captures/`](Captures), prefixed
`20260816_`. Everything below was verified, not assumed.

## Regression position

The full `LineBoss` automation suite is **275/275 green, zero failures**,
including all 63 OneFactory and BodyWeld tests. Nothing in this session's work —
the WIP presentation, station dressing, HUD, camera, motion, lighting, envelope,
or the pack import — broke an existing test.

The frozen presentation contracts are untouched. The Body/Weld 469-instance
count still holds, because every visual addition is a separate runtime actor
alongside the presentations rather than an edit to them.

## What changed

**Factory Environment Collection imported.** 869 meshes, 432 materials, 705
textures and the Fx set, copied at their original `/Game`-relative paths so
internal references resolve. Verified in the editor: sampled meshes load with
authored `MI_` materials and intact LOD chains, none falling back to a default.
Licensing position is recorded in
[Third-party asset pack licensing](../ReleaseGate/THIRD_PARTY_ASSET_PACK_LICENSING_v001.md).

**Station dressing composed per department**, so shops read as different places:

| Department | Composition |
|---|---|
| Press | Heavy press either side, material racking behind |
| Body/Weld | Mirrored six-axis robot pairs, as a real body shop |
| Paint | Enclosed booth modules, plus an oven at the cure stage |
| Assembly | One robot fitting parts, operator bench opposite, parts rack behind |

Common to all: control cabinet, side guarding with the ends left open, an
overhead light ramp at every quality gate, and conveyor sections laid between
consecutive stations so the line is physically continuous. Cell size and mesh
scale come from each station's nearest neighbour, so nothing straddles its
neighbour however the player spaces the line.

**Production-flow HUD.** Top bar and a seven-stage strip whose station counts
sum to exactly 57, matching the route topology. Throughput is the bottleneck
cycle of each group; occupancy and progress come from the ledger; alert text is
the coordinator's own reasons. Cash is deliberately absent rather than faked.

**Roof cut away for management views.** The authored roof sat between the camera
and the floor at any sensible pitch. `LB.OneFactory.Roof` hides components
sitting entirely above working height and remembers what it hid, so the toggle is
exactly reversible.

**Cars flow.** Over the last fifth of each cycle a unit eases to its next station
and turns to face travel. A unit held at a quality gate stays put until a result
is submitted.

## Two map findings worth acting on

1. **The authored floor is smaller than the configured route.** Stations at the
   far ends of Press and Assembly stand over void and rendered as black holes
   with machines apparently floating. The dev envelope now lays a floor slab over
   the whole routed footprint as a stopgap. The real fix is either extending the
   map's floor or constraining the starter layouts to the floored area.
2. **The map carries one RectLight** at the origin while the Management
   `PlayerStart` sits 280 m away. `LB.OneFactory.Light` compensates at runtime,
   but permanent lighting belongs in the map, calibrated to the documented
   standard: 5000 K fixtures, sun 0.30, sky 0.20, fixed exposure bias -0.50.

## Honest status

**Validation-only.** A real map, a real rendered session, real captures. Still
driven by developer console commands, still not a packaged build, and no player
can reach any of it through the interface. No claim is made about visual
acceptance, performance or accessibility.

## Reproducing the current look

```
LB.OneFactory.BuildWholeFactory
LB.OneFactory.Envelope 6000 1400
LB.OneFactory.Dressing
LB.OneFactory.Roof 1 900
LB.OneFactory.Light 9
LB.OneFactory.ShowWIP
LB.OneFactory.HUD
LB.OneFactory.StartProduction 1
LB.OneFactory.Run 50 2 1
LB.OneFactory.Tour Look 60 0
```

## Next, in order

1. **Drive this from the native UMG surface** so a player reaches it without
   console commands. This is the last thing between the current state and a
   playable build.
2. **Fix the floor and lighting in the map** rather than at runtime, to the
   documented standard.
3. **Adopt pack meshes into a versioned `v002` presentation** with an extended
   allowlist and regenerated instance counts, so the dressing stops being a
   runtime overlay and becomes the real presentation.
4. **Package a Development build** and run the finish checklist on it. Every
   claim above is Editor evidence until that happens.
