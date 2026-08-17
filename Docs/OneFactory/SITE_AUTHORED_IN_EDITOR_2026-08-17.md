# Moorcross Works full site, authored in the editor — 2026-08-17

## What changed and why

The site around the four shop buildings was going to be generated at runtime
from scaled `/Engine/BasicShapes/Cube` instances. The owner rejected that
approach — *"can you not edit in unreal, like put trees etc in?"* — so the site
is now **real assets placed as saved actors in the level**, authored by
`Tools/build_site_authored.py`.

The runtime primitive actor (`LBOneFactoryDevSiteActor.h/.cpp`) was written and
then **deleted**; do not resurrect it. The shop envelopes
(`LBOneFactoryDevEnvelopeActor`) are still runtime primitives and are unchanged.

## Result

5,049 actors placed, zero spawn failures, saved into
`/Game/LineBoss/Factory/OneFactory/v001/Maps/LB_MoorcrossWorks_OneFactory_v001`.

| Element | Count | Asset used |
| --- | --- | --- |
| Chainlink fence panels | 2,693 | `SM_Fence_01` (measured 128.2 cm) |
| Fence straining posts | 338 | `SM_FencePart_01` |
| Road and bay paint | 1,616 | scaled `Plane` + painted-concrete instance |
| Future-plot kerbs | 288 | `SM_ConcreteWall` laid flat |
| Yard light masts | 28 | `SM_CrashAreaSpotlight_01` |
| Marshalling containers | 23 | `SM_Container01_01/02`, `SM_ContainerP4_01` |
| Skyline structures | 12 | `SM_Background1_Tower01-04`, `AntennaTower` |
| Support blocks | 10 | `SM_Background2_Hangar`, `BoxBuilding`, `BoxBuildingBase` |
| Road surfaces | 10 | scaled `Plane` + asphalt instance |
| Inbound / dispatch artics | 9 | `SM_CA_MW_InboundLorry_Approved_v006` |
| Gate leaves and borders | 8 | `SM_GateDoor01`, `SM_GateBorder01` |
| Marked car-park spaces | 370 | paint only |

Site is **1008 × 728 m** inside the fence. Geometry is derived from the
authored department bays, so it cannot drift from the buildings:

- shops envelope `X -30900..30900, Y -13900..14900`
- hardstanding apron `X -42900..41900, Y -28900..27900`
- ring-road centreline `X -47100..46100, Y -33100..32100`
- fence line `X -50900..49900, Y -36900..35900`
- spine yard at `Y = -1000`, computed as the gap between the two shop rows

Circulation: perimeter ring road, the central spine road through the yard the
production route already crosses, north and south service roads, and two
north–south yard roads in the open yards beyond the end walls. There is
deliberately **no road through the middle of the works** — the alley between the
press and assembly bays is two metres wide by authorship.

## New material instances

Created under `/Game/LineBoss/Site/Materials_v001`, all instances of the
project's own masters rather than new art:

- `MI_LB_Site_Asphalt_v001`, `MI_LB_Site_Concrete_v001` — instances of
  `M_LB_SealedFactoryConcrete_World_v001`. That master is **world-aligned**, so a
  yard hundreds of metres across tiles correctly instead of stretching.
- `MI_LB_Site_PaintWhite_v001`, `MI_LB_Site_PaintYellow_v001` — instances of
  `M_LB_FrontEndPaintedConcrete_Master`.
- `MI_LB_Site_GrassStandIn_v001` — **a stand-in, not final art.** See below.

`/Game/LineBoss/Site/Materials_v001` still needs adding to
`DirectoriesToAlwaysCook` in `Config/DefaultGame.ini` before packaging.

## The one genuine asset gap: vegetation

The project contains **no tree, bush, hedge or grass mesh or material** — not in
`Content/`, not in any of the seven owned Fab packs. Grass is currently a tinted
concrete instance, which is honest-looking at distance and wrong up close.

Free vegetation is available and should be added: Quixel **Megaplants** are free
under the Fab Standard License, and Megascans tree collections (European
Broadleaf Forest, Baltic Pine Saplings, European Beech, Common Hazel) are free
for Unreal use. Adding a pack needs the owner's own Fab account, so it cannot be
done autonomously. A grass/asphalt **ground surface** from Megascans matters more
than the trees, because it replaces the stand-in above.

## The provenance regression this caused, and the fix

The first version of this site **locked the game out of commissioning a factory
at all**, and the test suite did not notice.

`ALBOneFactoryBootstrap::ActorUsesForbiddenProvenance` rejects any actor whose
name, tags, mesh path or **any bound material path** contains `Meshy` or
`ExternalGenerated`. The nine dock artics were placed as
`SM_CA_MW_InboundLorry_Approved_v006`, whose only material is
`M_CA_MW_Lorry_MeshyPBR_v006`. That produced:

```
LINE_BOSS_ONEFACTORY_BOOTSTRAP_REJECTED reason=ONEFACTORY FOUND 9 NON-NATIVE PRESENTATION ACTORS
LINE_BOSS_DEV_BUILD_WHOLE_FACTORY ok=0 NEW FACTORY IS LOCKED UNTIL BOOTSTRAP READY
```

The mesh name is clean — only the material trips it — so this is invisible to
asset-name inspection. `Tools/Diagnostics/probe_lorry_provenance.py` measures
every candidate vehicle's bound materials and found the approved lorry is the
only unsafe asset among everything the site places.

Fixed by switching to `SM_CA_MW_Inbound_LorryFourCoil_v005`, a Blender-native
assembled four-coil artic with clean provenance, positioned from its measured
bounds rather than a hardcoded length. The script now also **refuses to save**
a world where any placed actor trips the rule, so this cannot land silently
again.

**The 278-test suite passed 278/278 both before and after this regression.** It
does not cover bootstrap world-provenance, which is worth a contract test.

## Verification status

- Placement: 5,049 placed, 5,049 cleared on re-run (idempotent), **0 failures**,
  provenance self-check passed, level saved. Verified.
- Test suite: **278/278** — 255 clean, 23 succeeded-with-warnings, 0 failed,
  0 notRun, 0 inProcess. Verified after the map write.
- Bootstrap and commissioning: `LINE_BOSS_ONEFACTORY_BOOTSTRAP_READY`, then
  `LINE_BOSS_DEV_BUILD_WHOLE_FACTORY ok=1 WHOLE FACTORY CREATED, COMMISSIONED
  AND VALIDATED`, envelope 2,261 pieces across four shops. Verified.
- Tour framed all 57 stations across three stops. Captures
  `SiteFixed_01_All@2p6~42`, `_02_All@1p8~30`, `_03_Press@1p2~28`.

## Sun and sky — landed

`Tools/build_site_lighting.py` authors 4 actors into the level, tagged
`LB.Site.Lighting` and cleared on re-run so the sun can be re-calibrated without
touching the 5,049 site actors: a DirectionalLight sun (5800 K, pitch −42°,
yaw −35°, 4 shadow cascades reaching 900 m so the far fence still shadows), a
SkyAtmosphere, a real-time-capture SkyLight, and an ExponentialHeightFog.

Two authorities found by `Tools/Diagnostics/probe_map_lighting.py` and
deliberately left alone — the script asserts both are still intact and refuses to
save otherwise:

- `LB_OF_ENV_FixedExposureAuthority_v001` pins auto-exposure min **and** max to
  1.0. Exposure is fixed on purpose, so the sun is calibrated to sit at that
  exposure rather than relying on adaptation.
- `LB_OF_ENV_LightingAuthority_5000K_v001`, the existing 800,000-lumen overhead
  RectLight, is the only light the map shipped with.

Sun intensity was calibrated by capture: **6.0 lux** blew the ground to white,
**1.0** read as dusk under a black sky, **2.2** holds both. The 28 yard masts are
placed as geometry but their spot lights are **off by default**
(`LB_MAST_INTENSITY=0`) — lit at midday they read as an airport runway. Set that
env var to enable them for a dusk look.

Also fixed while lighting: the ground field ran only 12 m past the fence, so the
site read as a slab floating in the sky and the skyline towers stood in void. It
now extends 1.5 km past the fence and the fog takes over before its edge.

### Ground material is still wrong, and tinting cannot fix it

The undeveloped ground was first a green "grass stand-in". With the tint
**verified by readback** as green (0.052, 0.095, 0.036) it still rendered
grey-brown, because `ConcreteTint` modulates a concrete base rather than
replacing it. It is now tinted as levelled hardcore instead, which is at least
honest for undeveloped industrial land — but even at 0.042 albedo it renders pale.

Conclusion: **a real ground material is needed**, and this is the highest-value
free download. Quixel Megascans ground surfaces (grass, asphalt, gravel) and
Megaplants vegetation are free under the Fab Standard License but need the
owner's own Fab account.

## Direction change, 2026-08-17: repopulate from empty, press first

Looking at the works from the air the owner said *"the buildings arnt set out
correctly"*, *"there should be alot more stations in each"*, and *"can you start
from scratch with empty buildinds and start populating starting with press"*.
That supersedes further site polish. Two separate problems, both measured:

**1. Station density is far too low.** Measured per-department station extents:

| Department | Stations | Footprint |
| --- | --- | --- |
| Press | 7 | 260 × 90 m |
| Body/weld | 18 | 160 × 56 m |
| Paint | 8 | 118 × 0 m (a dead-straight line) |
| Assembly | 24 | 242 × 60 m |

57 stations across a 562 × 233 m works leaves every shop floor an near-empty
rectangle, which is exactly what the aerial captures show. The press station
catalogue in code only runs PR002–PR010, so the *station* abstraction itself is
too coarse to fill a shop — filling it means many more machines per department,
with the restored reference map (2,804 pieces) as the density authority.

**2. The set-out does not match the master plan.** The four departments sit in a
2 × 2 serpentine — press NW, weld SW, paint SE, assembly NE — with every
production line running east–west. The owner's master plan has four **long
north–south shops side by side in a west-to-east row** in line order
(press 350 × 130, weld 400 × 225, paint 400 × 100, assembly 450 × 200 m).
Separately, east–west neighbours are only **2 m apart** after their 4 m skirts,
which is why the shops merge into one mass with no service yards.

Reconciling the two means new station transforms, so the frozen presentation
contracts will need re-versioning rather than preserving. **Do not delete
authored assets to do it** — create a new versioned layout and leave the existing
presentations intact.

**3. My earlier captures understated the content, and the restored press shop
looks rotated out of its building.** Two corrections to the assessment above:

- Every capture before `Full_*` omitted `LB.OneFactory.RestoredShop` and
  `LB.OneFactory.Dressing` from its `-ExecCmds`. Those add **2,804 restored
  instances across 1,179 batches** and **960 dressing instances across 34 mesh
  families**. The "empty shop floors" in the earlier shots were partly my
  capture's fault. Always include both when judging density.
- Even with them on, `Full_02_Press@0p9~26` shows only **four press trains** in a
  320 × 130 m hall with most of the floor bare, and visible machinery **outside**
  the south shop wall. `LBOneFactoryDevRestoredShopActor` anchors the manifest to
  the ConfigurablePressTrain station's transform with a **+90° datum-local yaw**
  (see the comment at line ~109 and the instance placement at ~232). The
  reference shop measures **225 × 112 m**; yawed 90° that becomes 112 × 225 m,
  against a press bay only **130 m deep in Y** — so roughly **95 m of restored
  content is pushed outside the building**. That is consistent with what the
  capture shows and would explain both the sparse hall and the stray machinery.
  Confirm by dumping restored instance world bounds and comparing against the
  press bay rect before changing anything.

### Superseded

The captures show the shop roofs and the lit aprons, but the yards, roads,
fence, car park and skyline are in darkness. `LB.OneFactory.DevLighting` builds
per-department interior lamp grids and a `SLS_CapturedScene` skylight — there is
**no directional sun**, which was fine when nothing existed outside the
buildings. The site cannot be visually judged until an exterior lighting pass
exists. This is the next piece of work, and it needs a decision: adding a sun
will change how the shop interiors read too, and those were tuned deliberately.

## Rollback

The pre-site map is backed up to
`E:\LineBossValidationOutput\MapBackups\LB_MoorcrossWorks_OneFactory_v001.pre-site.umap`.
`Content/` is not in git, so that copy is the only rollback path — keep it until
the suite is green.

Re-running `Tools/build_site_authored.py` is idempotent: it destroys every actor
tagged `LB.Site.Authored` before placing, so the site never doubles up.

## Note for future runs

Level editing from Python **must** use `-ExecutePythonScript`, not
`-run=pythonscript`. Under the commandlet there is no editor world, so
`load_level` and every `spawn_actor_from_object` silently return nothing and the
script still reports success — the first run placed 0 actors and exited 0. The
script now checks the loaded world's identity up front and raises instead.
Related: `Tools/Diagnostics/probe_site_assets.py` measures real asset bounds so
placement pitches come from the asset rather than a guess.
