# Original procedural spray booth runtime v002

Status: **EXACT UE INCIDENT DIAGNOSED — GUARDED FRESH RECOVERY FROZEN, NOT YET RUN**  
Date: 2026-08-15  
Destination: `/Game/LineBoss/Candidates/PaintShop/SprayBoothRuntime_v002`

## Outcome

The source asset remains valid and unchanged. Run `20260815T014836Z` imported
the original LOD0, appended the authored LOD1, saved a partial StaticMesh, then
failed on an incorrect collision assertion. The partial package is not an
accepted asset and must not be promoted or referenced.

The corrected lane and a one-use incident recovery are frozen offline. This
recovery work did not launch Unreal and did not change Content, Source, Config,
maps, saves, or the preserved failed-run evidence.

## Immutable incident evidence

| Evidence | Full path | Bytes | SHA-256 |
|---|---|---:|---|
| Partial package | `C:\Users\greg_\Projects\LineBossCarFactory_Unreal 5.8\Content\LineBoss\Candidates\PaintShop\SprayBoothRuntime_v002\SM_LB_PaintSprayBooth_Runtime_v002.uasset` | 112,825 | `B2EAC396E3C285750F10E2A57920C42D13FB80B1374DF3FB4AF537E581EEE0D8` |
| Failed import log | `C:\Users\greg_\Projects\LineBossCarFactory_Unreal 5.8\Saved\Audits\PaintShop\SprayBoothRuntime_v002\Runs\20260815T014836Z\import.log` | 653,696 | `AA2181E79CA8C7AAB14D3A0B92CB6E608A326887D10C6F7F69AD74D880806898` |
| First collision diagnostic | `C:\Users\greg_\Projects\LineBossCarFactory_Unreal 5.8\Saved\Logs\diagnose_spray_booth_runtime_v002_collision.log` | 319,681 | `9D7679D1CE949CBFC270B1F936E009442B99401DA5B5A45AF1F8B42B56A16C02` |
| Extended collision diagnostic | `C:\Users\greg_\Projects\LineBossCarFactory_Unreal 5.8\Saved\Logs\diagnose_spray_booth_runtime_v002_collision_v002.log` | 320,969 | `E99A176FB01D8DACC91303FE0FE5183F7AB86C2D10235D3069F56A01DCCA78DF` |
| Current read-only diagnostic script | `C:\Users\greg_\Projects\LineBossCarFactory_Unreal 5.8\Scripts\diagnose_spray_booth_runtime_v002_collision.py` | 2,383 | `6AD60E5F5254868A197B394BB64123BF584DF88C864B88FD70BE3FDBCD57509E` |

Neither stable receipt, a validation log, nor a run summary exists. The failed
run directory contains only its preserved `import.log`; the candidate namespace
contains only the partial mesh package.

## Definitive diagnosis

The failed log proves that all three named `UCX_` objects were imported and the
two LODs were saved before the old assertion failed. Both read-only diagnostics
prove the saved mesh has LOD triangles `(3804, 420)` and this exact reflected
collision inventory:

| `BodySetup.agg_geom` array | Required count |
|---|---:|
| `box_elems` | 0 |
| `sphere_elems` | 0 |
| `sphyl_elems` | 0 |
| `tapered_capsule_elems` | 0 |
| `convex_elems` | 3 |

UE 5.8's `StaticMeshEditorSubsystem.get_simple_collision_count()` returns `0`
because its installed C++ implementation sums only boxes, spheres, and sphyls.
It does not include convex hulls. `get_convex_collision_count()` independently
returns the `ConvexElems` count, but acceptance now reads the five exact arrays
directly through:

`StaticMesh.body_setup → BodySetup.agg_geom → KAggregateGeom`

The UE 5.8 Python stub reflects `convex_elems`, but `KConvexElem` reflects
neither `vertex_data` nor `elem_box`; its transform is protected. The extended
diagnostic confirms those limitations on all three hulls. Runtime vertex/bounds
claims would therefore be false. The unchanged source exporter remains the
authority for the three eight-vertex portal-safe hull bounds:

- side -Y: `[-560,-250,0]` to `[560,-230,380]` cm;
- side +Y: `[-560,230,0]` to `[560,250,380]` cm;
- roof: `[-560,-215,380]` to `[560,215,395]` cm.

The extended diagnostic also found that the partial mesh referenced six
material packages that were absent on disk. The corrected importer explicitly
saves every imported material package and the mesh. Its receipt hashes all
seven `.uasset` files, and the independent fresh process must find and re-hash
the same seven files before PASS.

Installed engine evidence:

- `C:\Program Files\Epic Games\UE_5.8\Engine\Source\Editor\StaticMeshEditor\Private\StaticMeshEditorSubsystem.cpp`,
  89,363 bytes, SHA-256
  `8C9E71501320F6EF9CB4A3D6AB668EEE6184230A2F85A8B9E3748E1831CA6760`;
  collision count implementations are at lines 1398–1423 and 1449–1470.
- `C:\Users\greg_\Projects\LineBossCarFactory_Unreal 5.8\Intermediate\PythonStub\unreal.py`,
  36,885,750 bytes, SHA-256
  `2056FB093DAE4E8C1A1BCF681B1DCC0D0BCF0BFD398758375783E64A2C77975F`.

## Source authority remains unchanged

Offline round-trip acceptance still proves:

- LOD0: 2,064 vertices and 3,804 triangles;
- independently authored LOD1: 272 vertices and 420 triangles;
- both LODs: 1200 × 500 × 450 cm, six material semantics, complete source UV
  coverage, and zero degenerate triangles;
- two open 430 × 335 cm X portals, solid long sides, three extraction housings,
  zero robots, and zero screens;
- three source UCX hulls: two long sides plus roof, leaving both portals clear.

| Source artifact | SHA-256 |
|---|---|
| Original v001 procedural generator | `A2C5ED68C267AC6F7A2898D9D6C6B180FC4E8EE1A0F9418971EAED5462C6505A` |
| LOD1 primitive generator | `B6B2C31EBDD4EED2149626A14696C800182DDA9F1914E27DE772363251F524C2` |
| LOD0 exporter and UCX author | `C969B3837A34D7386572913C3313A66779B183AA5064541262A70769E8F8E047` |
| LOD0 FBX | `E38464ED0BFD141E6D6F28B7EF24EA6DFBB45F4DCB3C7F67DF0FC3CEA3F30B97` |
| LOD1 FBX | `F55CB80FAD1F340FB97B928CC700807D2D82ADC282F16D2287CAE64B57D6CCFB` |
| v002 authority manifest | `003A69983AFD71A5D9636145C4A3D4049ADDBB9EE0DDE6D7CB8C92AAB82A7EE4` |
| Independent round-trip report | `068F4BCF63FB67B2017DD1DE4AE93D1B29C1C0560FBCE83FCE6B393207BDF251` |
| Independent offline audit | `A679B8A047DB02BF34D0E43F24FFB7C444F80498752ED6A8443CE5D399F606AA` |
| Successor incident/collision authority | `541A4F2DBD97A19106F932B39CF495A7FB7030371F7C7EDC18CE8D6CA4C73034` |

## Corrected tooling freeze

| Tool | SHA-256 |
|---|---|
| Unreal importer | `B23FF792228CC5198178CE99C6C8BFFD322FD9720424329FDBD01485F28399EF` |
| Independent Unreal validator | `2AC134AF9A91730186AEFA83F66B933FBFCD337BEBAE652F52BB124403962196` |
| Normal fresh-only runner | `432F6722293FA293A4CBEE6406CE984BD787C635A806AD697A04B5F95EB4CE8D` |
| Incident-bound recovery | `5726DA43D577B7A3E010C8EB6B6267A28C7FB6E7B6A6C8235889BF7B9868DA21` |
| Focused offline tests | `A8FC4FCA71A59F09E9AEB15B72154A9E1DCACBACC0F7F93ACABE0D52733FB3FB` |

The normal runner still uses two fresh UE processes: import, then independent
read-only validation. It protects existing Content outside the candidate
namespace, Config, and SaveGames. It runs no UBT and opens or saves no map.

## One-use recovery disposition

The recovery refuses any state except the exact package, failed-run log, two
diagnostics, frozen tooling, absent stable receipts, and an absent incident
archive. With Unreal closed, it then:

1. copies the failed log and both diagnostics without changing their originals;
2. copies the partial package byte-for-byte into the incident archive;
3. moves only the exact one-package candidate namespace into Saved quarantine;
4. proves the candidate destination is absent and protected files are unchanged;
5. writes a pre-retry receipt;
6. invokes the normal fresh-only lane exactly once;
7. re-proves both preserved package copies, the original failed log, both stable
   receipts, exactly one new run, and protected-file immutability.

The archive root will be:

`C:\Users\greg_\Projects\LineBossCarFactory_Unreal 5.8\Saved\Quarantine\PaintShop\SprayBoothRuntime_v002\Incident_20260815T014836Z`

No deletion or automatic cleanup is authorized. A failed retry remains
one-shot and auditable; the archive, quarantine, failed run, and any new failed
run are retained.

## Exact future command

Do not run the normal runner directly while the partial namespace exists. With
all Unreal and build processes closed, run the incident recovery exactly once:

```powershell
powershell.exe -NoProfile -ExecutionPolicy Bypass -File "C:\Users\greg_\Projects\LineBossCarFactory_Unreal 5.8\Scripts\recover_spray_booth_runtime_v002_collision_incident_20260815T014836Z_v003.ps1"
```

The command itself performs the single normal-lane invocation after preservation
and quarantine. It has not been executed by this offline recovery-tooling task.
