# Cook crash: site paint MIs over a dead car-era master (2026-09-01)

## Symptom

Every `BuildCookRun`/`-run=Cook` of the full content set died with:

```
Assertion failed: (Index >= 0) & (Index < ArrayNum) [Containers\Array.h:1339]
Array index out of bounds: 2 into an array of size 1
```

Engine-only callstack (Core → Engine → CoreUObject → UnrealEd), no
script frames, ~19s in on a warm DDC. PIE and the editor never showed
anything — the game played fine all day while the package lane was
hard-broken.

## Wrong turns, recorded so they are not repeated

- **M_LB_ConceptGraded_v001 was the prime suspect for five runs** — its
  PCD3D_SM5 compile was the last log line before the assert in three
  consecutive cooks. That correlation was scheduling noise: the ~20
  Props/StationMeshes material compiles are async stragglers that log
  while the cooker has already moved on to the real killer. Deleting and
  recreating the asset fresh (Scripts/rebuild_concept_graded_v005.py)
  changed nothing. Verified innocent via `-CookSinglePackageNorefs`.
- The SM5-vs-SM6 framing was also wrong. The second probe run proved the
  SM5 shadermap had landed in DDC (no recompile) and the crash still
  fired. BaseEngine.ini does append `PCD3D_SM5` to
  `D3D12TargetedShaderFormats` (the project's `+PCD3D_SM6` joins it
  rather than replacing it), so cooks build both formats — that is a
  cook-time cost question, not this bug.
- Mesh section→slot integrity across /Game/Spacecraft: all clean.

## The find

Config bisection of `+DirectoriesToAlwaysCook` in DefaultGame.ini
(halving, full cook per round, ~70 s/round on warm DDC) landed on
`/Game/LineBoss/Site/Materials_v001`; per-asset single-package cooks
then isolated exactly two crashers, each fatal alone:

- `MI_LB_Site_PaintWhite_v001`
- `MI_LB_Site_PaintYellow_v001`

Both were parented to the car-era
`/Game/LineBoss/Materials/FrontEnd/M_LB_FrontEndPaintedConcrete_Master`,
whose **five TextureSample nodes are all null** — its
`T_ConcretePillar01_BC/_N/_ORM` source textures were deleted from
`Content/LineBoss/Vendor/FactoryEnvironment/Textures/` at some point
(the cook logged the dangling dependencies as warnings every run). The
editor substitutes defaults for null samplers and renders on; the
cooker's material-instance expression indexing asserts.

## The fix (Scripts/repair_site_paint_master_v001.py)

New texture-free master
`/Game/LineBoss/Site/Materials_v001/M_LB_SitePaint_Master_v001`
(ZoneTint × TintStrength → BaseColor, Roughness scalar — parameter
names identical to the old master so the MIs' stored overrides keep
applying by name), and both MIs re-parented onto it. The FrontEnd
master is untouched car-era prior art; nothing in the cook set
references it any more.

Verified: both MIs cook clean singly; full 1273-package cook passes
(see the session's cook logs; final proof is the packaged journey run).

## Rules this reinforces

- A cook assert's "last logged asset" is NOT the crashing asset. Async
  compile/build log lines interleave freely with the save queue. Config
  bisection + `-CookSinglePackage` is cheap (warm DDC makes a full-cook
  probe ~1 min) and names the package with certainty.
- Deleting content out of `Content/` leaves live references behind and
  `git status` shows nothing (Content is gitignored). The editor keeps
  rendering; only the cook lane finds the corpse. After any Content
  deletion sweep, run a cook.
- The diagnostic probes `M_LB_SM5Probe_{TwoTone,Detail,Accent}` under
  /Game/Spacecraft/Props MUST be deleted before packaging — that path
  is in DirectoriesToAlwaysCook, so leftovers ship.
