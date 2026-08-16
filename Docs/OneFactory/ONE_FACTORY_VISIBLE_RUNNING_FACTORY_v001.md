# OneFactory — the running factory, on screen

Snapshot: **2026-08-16**. Captures in [`Captures/`](Captures). This supersedes the
visual claims in
[the weld vertical slice note](ONE_FACTORY_WELD_VERTICAL_SLICE_RUNNING_v001.md),
which proved the loop only under `-NullRHI` with nothing rendered.

## What is now visible

A rendered `-game` session on `LB_MoorcrossWorks_OneFactory_v001` shows the
commissioned factory with work in progress moving through it. In the captured
weld frame, three units stand in Body/Weld positions 01, 03 and 04 at
`BodyFraming`, with a body legible on its station platform.

`ALBOneFactoryWIPPresentationActor` reads `CaptureLedger()` plus the configured
route and draws one instance per live unit at its current station. It owns no
genealogy, allocates no `UnitId`, writes nothing back and is never saved, per the
production-flow contract. Six visual families track progress:

| Stage range | Family | Reads as |
|---|---|---|
| Inbound coil, blank preparation | Coil | Mill steel, lying across the line |
| Pressing, pressed-panel stillage | PanelStack | Flat stack of cut steel |
| Body framing to body inspection | BodyInWhite | Bare welded shell |
| Pretreatment, ED coat | PrimedBody | Dull e-coat grey |
| Colour coat to paint inspection | PaintedBody | Cairnwell teal |
| Trim to dispatch | FinishedCar | Brighter finished car |

Only the colour coat carries livery, so how far a body has travelled is legible
at a glance.

## Three defects that hid it

The presentation was correct from the first build. Three separate problems made
it invisible, and each is worth recording because none was in the logic.

1. **Framing.** Department views sat far enough back that a 4.4 m car covered a
   few pixels. Distances are now matched to the default 90-degree FOV, and
   `View WIP` frames a single live unit closely rather than averaging across
   departments hundreds of metres apart.
2. **Exposure.** The interior bay lights were roughly four times too strong,
   blowing the floor to flat white and crushing everything on it to silhouette.
   At 42000 the floor reads as concrete and machines, route markings and bodies
   separate.
3. **Component choice.** The batches were hierarchical ISM. HISM builds a
   cluster tree asynchronously and suits thousands of static instances; a handful
   of cars changing station every few seconds is its worst case. Plain ISM plus a
   signature guard that only rebuilds on an actual station change fixed it.

The diagnostic lesson repeats the panel-bounds one: the fail-fast log named the
symptom but no measurement. Logging each batch's instance count, mesh,
visibility, registration and bounds ended the guessing in one run.

## Site lighting

The shipped map carries a single RectLight at the origin while the Management
`PlayerStart` sits 280 m away, and the site is roofed, so whole bays rendered
black — the press shop entirely. `LB.OneFactory.Light` hangs a 7x7 grid of
interior fixtures derived from the live station route, plus a directional key and
sky fill. It is runtime-only and the protected map is untouched.

This is a development aid, not the shipping answer. Permanent lighting belongs in
the map or in an authored envelope.

## Status under the release vocabulary

**Validation-only.** A real map, a real rendered session, and captured evidence.
It is still driven by developer console commands, is not a packaged build, and no
player can reach any of it through the interface. It does not claim visual
acceptance, performance, or accessibility.

## What visual work needs a decision

Further improvement runs into three deliberate constraints, and each needs an
explicit call rather than a quiet change:

1. **No building envelope.** The site has roof beams and columns but no walls, so
   it fades to black at the edges. `LBFactoryEnvelopeShutterActor` exists but is
   legacy press-shop content, and the OneFactory bootstrap contract requires
   `SpawnsLegacyFactoryContent()` to stay false. Walls therefore belong in the
   map or a new OneFactory-native envelope, not in a runtime workaround.
2. **Flat materials.** Every machine uses `BasicShapeMaterial` with only a colour
   parameter, so nothing reads as metal. Proper metallic and roughness needs new
   material assets under `Content/`, which is currently unversioned.
3. **Frozen instance counts.** The starter presentations are pinned to exact
   counts, including the 469-instance Body/Weld contract. Improving machine
   geometry means a versioned `v002` presentation with regenerated counts and
   updated tests, following the supersede-rather-than-edit convention.

## Next

1. Decide between map-authored walls and an OneFactory-native envelope actor.
2. Put `Content/` under Git LFS before adding material assets.
3. Drive the build/run sequence from the native UMG surface so a player can reach
   it without console commands.
4. Import `VehicleWIPNativeKit_v001` and swap `BatchMeshPath`; the stage mapping,
   transforms and lifecycle need no change.
