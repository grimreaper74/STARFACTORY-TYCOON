# OneFactory visual readability and navigation successor v002

Status: **offline tooling frozen; not executed**. No Unreal Editor, UBT or
gameplay process was launched while preparing this tranche. No existing
Content package, Source file, Config file, map or save was changed, and the
reserved destination remains absent.

## Decision

The genuine v001 actual-player evidence fails both presentation and runtime
navigation. The correct repair is a fresh, non-overwriting OneFactory
successor, not an edit to the protected v001 package:

- immutable source:
  `/Game/LineBoss/Factory/OneFactory/v001/Maps/LB_MoorcrossWorks_OneFactory_v001`
  (`750FB6C93BBE8220467F5BF9656C4017F0D9E2706B35C413460AF20CEB9EB682`);
- reserved destination:
  `/Game/LineBoss/Factory/OneFactory/v002/Maps/LB_MoorcrossWorks_OneFactory_v002`;
- overwrite policy: refuse if the destination asset, file, screenshots, logs,
  success receipt or failure receipt already exists.

The guarded builder duplicates exact v001, removes its one hall-sized
RectLight, installs the common Cairnwell lighting response, makes only the
existing base-floor HISM navigation-generating, explicitly runs
`RebuildNavigation` before saving, then performs a fresh unload/reload audit.

## Genuine 1920 x 1080 diagnosis

The retained actual-player run is
`Saved/Audits/OneFactory/v001/ActualPlayerPIE/Runs/20260815T035404438Z`.
All four PNGs are genuine 1920 x 1080 captures. Metrics below use the same
dependency-free PNG decoder frozen into the v002 contract: a deterministic 2x
spatial sample for Rec.709 luma and a full-resolution `640 x 160` top-left red
warning scan.

| Capture | SHA-256 | Mean luma | Black clip | Warning-red pixels |
|---|---|---:|---:|---:|
| empty factory overview | `C7CC1C28095CC83279D7F764999E18B58B3DAC60B9010E98BDF1567C4A8E5637` | 0.163652 | 52.8524% | 0 |
| populated Press overview | `7645637C24E077BF6B0F61BAEC1C70A15467913EA0882ACE27D7C23532AEC1FA` | 0.174236 | 49.4309% | 0 |
| Press/AGV close view | `943BCE49E04D3F1B56E6727C8F43210197FBFA5E563E87B96CDDD6818C487D65` | 0.190913 | 4.9176% | 0 |
| populated Press with native UMG | `430182F1D00D1D2E882BC76BC61CA0B3A39DA665F8A31B9506BDE7B190207580` | 0.213874 | 19.0862% | 511 |

The first two frames are materially below the common Paint-B factory envelope
of mean luma `0.35–0.48` and black clipping at most `1.0%`. In the native-UMG
frame the red `NAVMESH NEEDS TO BE REBUILT` message is visible at the upper
left. The same run log independently records two
`Unable to find RecastNavMesh instance` warnings.

The source package does contain a bounds volume and an editor-generated Recast
actor, but every v001 shell HISM was authored with
`can_ever_affect_navigation = false`. The runtime evidence therefore cannot be
treated as a harmless display artifact. The lighting diagnosis is also based
on the player pixels, not property values alone: one movable 800,000 lm
RectLight uses a `60000 x 29000 cm` emitting face and `45000 cm` attenuation
radius, but it still leaves approximately half of the wide Press image clipped
black. The inference is that one enormous source provides neither useful
fixture rhythm nor sufficiently local coverage across the 620 m x 310 m hall.

## Frozen v002 visual contract

The replacement is one coherent factory-wide system:

- 32 no-shadow movable RectLights in an eight-column by four-row grid;
- grid coordinates X `-26250..26250 cm`, Y `-10500..10500 cm`, Z `2700 cm`;
- each fixture: `48000 lm`, `5000 K`, `6000 cm` attenuation,
  `4200 x 700 cm` source face;
- fixture shadows, translucent-lighting contribution and volumetric scattering
  disabled to bound stylised management-view cost;
- common movable DirectionalLight intensity `0.30` and SkyLight intensity
  `0.20`, matching the approved Paint-B factory reference;
- one unbound fixed `AEM_BASIC` exposure authority, min/max `1.0`, bias `-0.50`.

This is not accepted from scalar properties alone. The independent real-RHI
validator must capture:

1. empty whole-factory overview;
2. transiently populated native Press bay;
3. Body bay;
4. Paint bay;
5. Assembly bay;
6. populated Press view with the real native UMG.

Every scene frame must be exactly 1920 x 1080, at least 500,000 bytes, mean
Rec.709 luma `0.35–0.48`, black clipping at most `1.0%`, and white clipping at
most `0.5%`. The five scene means may differ by at most `0.08`. The UI frame
must contain at most 25 warning-red pixels in the top-left diagnostic region.
The validator and runner additionally reject the old navigation warning
signatures in runtime/log evidence.

## Frozen v002 navigation contract

The shell remains structurally exact while repairing the missing substrate:

- the same ten HISM actors and all 1,194 ordered instances, transforms,
  materials, collision profiles and shadows are retained;
- only `LB_OF_ENV_HISM_FloorSlabs_v001` changes its navigation relevance to
  true; all nine other HISM components remain navigation-neutral;
- the same single NavMeshBoundsVolume remains at the exact factory envelope;
- the world uses `NavigationSystemV1`, auto-spawns missing nav data into the
  bounds level and is not strictly static;
- exactly one unowned `RecastNavMesh-Default` is main nav data, uses Dynamic
  runtime generation and carries `LB.OneFactory.Navigation.Built.v002`;
- the builder updates the bounds and calls `RebuildNavigation` twice before
  the first and only target-map save;
- the builder's pre-save world and the actual PIE world must be quiescent and
  pass full non-partial paths along the logistics spine, service spine, Press
  to Body, Body to Paint, and Paint to Assembly; independent fresh reloads
  separately prove the serialized actor/config contract before and after PIE.

The real-RHI validator waits up to 90 seconds for PIE navigation to settle. It
does not hide screen messages. The clean native-UMG capture, five successful
paths, live Recast contract and absence of the two v001 log signatures are the
combined proof needed to remove the red warning.

## Structure and state preserved

The successor has exactly 59 non-foundation actors: the 23 unchanged v001 core
actors (ten HISM owners, all canonical datums, camera, PlayerStart, nav bounds,
bootstrap and Press authority), 32 high bays, common sun, common sky, fixed
exposure and one Recast actor. Exact safeguards preserve:

- one unowned native `LBOneFactoryBootstrap` and one unowned map-authored
  `LBPressShopBuildAuthority` in the same persistent level;
- the four canonical build bays, both protected areas, service/logistics
  spines, empty storage-bay array and all datum transforms/tags;
- exact map-local `LBOneFactoryGameMode`;
- zero saved production actors, machines, stations, robots, vehicles or WIP;
- zero Meshy or external-generated identity/reference.

The validator creates the existing native Press starter only inside PIE to
measure the previously dark gameplay case. After ending PIE it unloads and
fresh-reloads v002, proves the starter pair count is zero, proves the target map
bytes are unchanged, and never calls a map-save API.

## Guarded mutation envelope

At run time, the runner snapshots every existing file below `Content`
(excluding only the absent/new v002 map), `Source`, `Config`, and every
`Saved/SaveGames/**/*.sav`. It compares that snapshot after the builder and
again after the independent validator. The source v001 map, protected Press
v913, restored Press, visual standard and v001 validator have frozen hashes.
Body, Paint, all other Content, Source, Config and saves are protected by the
run-start snapshot so the shared Paint integration may settle before this lane
is executed without weakening isolation.

The runner starts no UBT, Build.bat, UAT or Source build. It requires already
compiled OneFactory classes, runs the builder in NullRHI, then launches the
validator in a separate fresh real-RHI offscreen process at 1920 x 1080. Any
failure leaves its new destination/evidence in place and forbids an automatic
rerun or overwrite; inspect before any manual recovery.

## Frozen tooling

| File | SHA-256 |
|---|---|
| `Scripts/one_factory_visual_navigation_v002_contract.py` | `AF463353CC94988F5B1E413E84898077EB587CF81A4E69A940B006D216EF4DA9` |
| `Scripts/one_factory_visual_navigation_v002_unreal.py` | `5F385670623D485F1716C459484A601105DFE7F6EA70E6793FD978272E357F81` |
| `Scripts/build_one_factory_visual_navigation_v002.py` | `A89E7C2BCA312581567488A9321A91D808733B7DBAB15BEEE61002F9F7801F5C` |
| `Scripts/validate_one_factory_visual_navigation_v002.py` | `5752E46164EEAF122B1773CC870ED8358C2C994CD6A34BAF58D834844980967D` |
| `Scripts/run_one_factory_visual_navigation_v002.ps1` | `61DF0116E0BD819C44571C42DFF5BF79A85B8D593FABF2288980C5E5B997B0B4` |
| `Scripts/tests/test_one_factory_visual_navigation_v002.py` | `5E48AFCABEDB50C14A07CAF1A22CF6313E1480E3A08C10E7E74938259CADA789` |
| `Docs/OneFactory/ONE_FACTORY_VISUAL_NAVIGATION_V002.md` | recorded in the static freeze manifest (self-hash omitted here) |

Static freeze:
`Scripts/one_factory_visual_navigation_v002_static_freeze.json` and its
`.sha256` sidecar. The freeze records the exact documentation hash as well as
every script/test hash.

## Exact deferred command

Run only after the shared Paint integration and combined native build have
settled, with Unreal/UBT/shader workers closed:

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File "C:\Users\greg_\Projects\LineBossCarFactory_Unreal 5.8\Scripts\run_one_factory_visual_navigation_v002.ps1"
```
