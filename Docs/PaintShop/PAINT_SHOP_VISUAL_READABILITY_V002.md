# Paint Shop visual readability v002

Status: tooling authored and statically checked; **not executed**. No Unreal
Editor, UBT, Content package, save, Config or Source mutation is claimed by this
document.

## Persisted target

The guarded patch persists the user-selected calibration `B_stylized` into the
existing isolated Paint prototype map:

- six existing RectLights: `12000 -> 1200 lm` each;
- existing DirectionalLight: `0.80 -> 0.30`;
- existing SkyLight: `0.80 -> 0.20`;
- existing fixed PostProcess exposure bias: `0.00 -> -0.50`.

Those are the complete nine-property allowlist. The repair may save only
`/Game/LineBoss/PaintShop/Experimental/v001/Maps/LB_PaintShop_Prototype_v001`.
It may not add/remove actors or change transforms, cameras, meshes, materials,
collision, Source, Config, saves, Press v913, Body Shop, campaign state or any
other shop map.

## One-factory lighting rationale and acceptance

Paint option B is the current master reference for the one continuous Line Boss
factory hall, not a separate Paint Shop art style. It is bound to the shared
factory visual standard. Every department should use the same fixed exposure,
5000 K nominal overhead-fixture colour, common sun/sky response and common
material-luminance targets. Fixture count/intensity may scale for covered area,
ceiling height and fixture density, and functional local task lights may vary;
those variations must not make each department look like a different building.

The frozen 1920x1080 calibration-B capture has SHA-256
`463F90CA7BA45EF45F4A0F594FBE429088813752CF3545976FBB7FB230041E58`.
A read-only 2x spatial sample of that reference measured approximate Rec.709
luma mean `0.40764`, black clipping (`Y <= 0.01`) `0.000291`, and white clipping
(`Y >= 0.99`) `0.000027`.

Fresh real-player captures remain mandatory before presentation approval. The
factory-hall acceptance envelope recorded by the patch is:

- mean Rec.709 luma: `0.35–0.48`;
- black-clipped pixels (`Y <= 0.01`): at most `1.0%`;
- white-clipped pixels (`Y >= 0.99`): at most `0.5%`;
- no unreadable dark roof void over gameplay-critical equipment;
- Cairnwell Green, Foundry Charcoal, Steel Grey, Warm White and Safety Yellow
  remain distinguishable at the management camera;
- robot envelopes, carrier route, guards, containers and process state remain
  readable without using per-shop exposure compensation.

The independent v002 validator proves the saved scalar and map-isolation
contract under a fresh process. It does not dishonestly call NullRHI validation
a fresh visual capture; a later real-RHI/player-view evidence run must apply the
capture gates above.

## Frozen authority chain

| Authority | SHA-256 |
|---|---|
| Paint v001 map pre-state | `2296FEE6FAF5AECB5B424E1E413B4324D1F9D3C4AF0172D7F83BC2440CE17069` |
| Map creation receipt | `4E65E671CB25D8615F3A775B1697E7D72C523D58FFA7481356A5BF8D5941AC09` |
| Independent map validation receipt | `B452A68FF04B89BF6D6FD43486230692C05B1338368794570174150DFC90F136` |
| Passing release summary | `660546CB5ABECB16A59C716F4D69DDAAE0DA143F70AA2685C43B9A4DB71AE1CB` |
| Passing actual-player PIE receipt | `8E01A7635D968C95A89B8F8371129869D5BC8BF8DE20F05C86396437E571E4D4` |
| 27-leaf automation index | `D9AB9A52221848CB9E7A75745F231A738A1EA2FA2F885EF9B717ED6B9A2B33BE` |
| Transient lighting calibration receipt | `1F287DD1D0758F37DD94F83737922B4282836E2BAB6506C27EED190E4117D766` |
| Factory visual standard v001 | `0E61306C437BCB587C82D6BF5609CAFDA1211E004CCFC86C6C4608CBA42A2971` |
| Protected Press v913 map | `26A901442CFA8415E3875BD998A2E3220045E296C17829335552D64837A190A6` |
| Protected Body Shop map | `8CB6976C532F5C06635ADC8ED00BB50CAF39FFCE2F15826C3456C6EDF4CACE8F` |

The release authority binds 27 exact Paint tests with zero failed/not-run tests,
the unchanged pre-patch map, and six actual-player PIE screenshots. The
calibration authority binds the unchanged map and the exact B values/capture.

## Guard and recovery design

The runner refuses to start while Unreal/build/shader processes are active. It
refuses any existing v002 receipt, log directory or backup, verifies every
frozen hash, and launches the repair and independent validator in separate
`UnrealEditor-Cmd -NullRHI` processes. No UBT is requested.

Before mutation the repair snapshots current Config, Source, all discovered
`.sav` files, Paint candidate/content files other than the target map, both
protected shop maps, the authority chain and the v002 scripts. It then creates a
byte-exact, non-overwriting backup at:

`Saved/Quarantine/PaintShop/VisualReadability_v002_PrePatch/Content/LineBoss/PaintShop/Experimental/v001/Maps/LB_PaintShop_Prototype_v001.umap`

with `MANIFEST.json`. If any post-save contract fails, do not rerun or delete
evidence; inspect the logs and restore only with Unreal closed after explicit
review.

Immutable receipts, when the runner succeeds, are written below
`Saved/Audits/PaintShop/Experimental_v001/VisualReadability_v002/`.

## Frozen tooling

| File | SHA-256 |
|---|---|
| `Scripts/repair_paint_shop_visual_readability_v002.py` | `2EA599FD11F804738943E39FABE6EFEBDD22830D773441E972B7AC7BEC7B7D10` |
| `Scripts/validate_paint_shop_visual_readability_v002.py` | `F9FCB6060D4D60DB985F0EAB3CB782E4AD75AB55845FCE25AE5CB450E1B1296B` |
| `Scripts/run_paint_shop_visual_readability_v002.ps1` | `DEAE81DE759DECC3FCC542FDEE165D0874773C964553843F352126110ABDCE76` |

## Exact run command

Run only with Unreal closed and after accepting the one-map mutation:

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File "C:\Users\greg_\Projects\LineBossCarFactory_Unreal 5.8\Scripts\run_paint_shop_visual_readability_v002.ps1"
```
