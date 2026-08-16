# Body Shop native support kit v001 — guarded Unreal import lane v002

Status: `FROZEN__STATICALLY_VALIDATED__READY_FOR_ROOT_ONE_SHOT_UNREAL_EXECUTION`

Finalisation marker: `NO_UNREAL_OR_UBT_EXECUTED_DURING_V002_FINALISATION`

This v002 authority supersedes the disabled provisional checkpoint without
rewriting history: the v001 provisional lane remains byte-for-byte preserved,
its baseline remains absent, and its zero pins still make it non-runnable.

## Frozen source and exact output

The clean-room procedural source remains
`SourceAssets/Candidate/WeldShop/BodyShopSupportKitNative_v001`. Its immutable
authorities prove exactly 12 support assets, 36 LOD meshes, 72/72 FBX/GLB
round-trips, one `UVMap` per LOD, identity transforms, floor-centred pivots and
aggregate triangles of 20,408 / 7,580 / 1,780 for LOD0 / LOD1 / LOD2.

| Authority | SHA-256 |
|---|---|
| `Audit/FROZEN_v001.json` | `A4E4BF52C46F93EF5A084A708D94A7B2B920ABDC702CF655B5A8569920A9AD6F` |
| `MANIFEST_v001.json` | `F0EFB621EC94C0D5E4806487576E1C6AE13EE8158A68A8D445052D6F33C700EC` |
| `Authority/LB_BodyShopSupportKitNative_v001.blend` | `5D69E9F6D4770475BC91AD1EAC61F528EEA3F7D8C4A3979BFF6F92B5ACC60F18` |
| `Audit/geometry_inventory_v001.json` | `1DC636BD128CC5CA37161638F92E63DA566BE7F14A293833280643F9A4441A67` |
| `Audit/roundtrip_validation_v001.json` | `8933C5A746070FEB6B628786E7BD52543D96D8162CCC3B27D2BF37618D098A4A` |
| `Audit/SHA256SUMS_v001.txt` | `FD78070F1E68950241035ED8B4AFDA79BD94E10F43759EBCB712AA674CB3A627` |

The only authorised Content write root is:

`/Game/LineBoss/Candidates/WeldShop/BodyShopSupportKitNative_v001`

It must be absent before execution and may contain exactly 12 StaticMesh
packages afterwards, each assembled from exactly three frozen FBXs (36 FBX
bindings total):

- Logistics: empty/full panel stillages, empty-return cart, component-service
  pallet, open small-parts crate and open small-parts bin.
- Controls: electrical cabinet and HMI pedestal.
- Safety: 2 m guard panel and 2 m interlocked guard gate.
- Services: utility pedestal and weld-extraction pedestal.

Every asset independently satisfies `LOD0 > LOD1 > LOD2 > 0`; importing exact
triangle counts therefore also proves strict per-part monotonic reduction.

## Fresh protected baseline

The v002 baseline inventories and SHA-256 protects the project descriptor,
complete `Source`, complete `Config`, campaign saves, and all pre-existing
`Content` outside the new namespace. It additionally names and pins these
critical authorities:

| Protected authority | SHA-256 |
|---|---|
| Press v913 | `26A901442CFA8415E3875BD998A2E3220045E296C17829335552D64837A190A6` |
| restored full Press map | `D3F8652AA45E7C2FCEE5AF1971F6AA78A3F027E60E361B039D14DAD5806C74A5` |
| Body Shop map | `8CB6976C532F5C06635ADC8ED00BB50CAF39FFCE2F15826C3456C6EDF4CACE8F` |

The exact eight current native robot packages are also individually pinned:
Base, J1–J6 and Open C-gun. Their package inventory may neither gain nor lose a
file and every size/hash must match before the lane can create a run folder.

## Unreal import and validation contract

- LOD0 uses an explicit legacy `FbxFactory`; replacement, imported materials,
  imported textures, generated lightmap UVs, generated collision, degeneracy
  removal and Nanite are disabled.
- `Interchange.FeatureFlags.Import.FBX` is set to `0` only while the 24 custom
  LOD1/LOD2 sources are appended, and its original value is restored in a
  `finally` block and rechecked.
- Each loaded LOD must retain exactly one UV channel, the frozen material
  section order, dimensions within 0.5 cm, an XY-centred footprint and floor
  Z=0 pivot within 0.1 cm.
- Nine semantic slots bind only to the already-promoted, hash-protected Body
  Shop presentation-material v002 family. No material or texture is created.
- Every support prop receives one deterministic AABB simple box, zero convex
  hulls and `CTF_USE_DEFAULT`; Nanite remains disabled.
- Manual LOD screens are exactly `[1.0, 0.45, 0.18]`, auto-compute is disabled,
  and a second distinct fresh UnrealEditor process proves persistence without
  saving any asset or map.
- Both Unreal processes independently verify the frozen source and protected
  state. The fresh validator hashes every protected file and verifies that
  loading the 12 target packages changes no target package byte or timestamp.

The runner launches exactly two hidden full `UnrealEditor.exe` processes with
`-NoCompile`; it never invokes UBT, AutomationTool or `UnrealEditor-Cmd`. It
refuses active Unreal/build/shader processes, any pre-existing destination, any
earlier v002 PASS or FAIL result, and every input hash drift. Partial packages
are preserved on failure for explicit review—there is no automatic cleanup or
retry.

## Frozen lane hashes

The final SHA-256 values are recorded after the baseline and all code pins are
cut. The PowerShell runner independently enforces the baseline, freezer,
importer and validator hashes before creating its audit run directory.

| File | SHA-256 |
|---|---|
| `Scripts/body_shop_support_kit_native_unreal_import_baseline_v002.json` | `E563879DC47887E5F99C9E7DD5D77308F080E6B0A7ECA2C185439669376A5915` |
| `Scripts/freeze_body_shop_support_kit_native_unreal_import_baseline_v002.py` | `7D0CD8FD35637CB3528FC13A5DF138731FFB3883FBCBE777D6E237E365F08E9E` |
| `Scripts/import_body_shop_support_kit_native_v001_lane_v002.py` | `810007BC43A8C854DD4497571DA37D2A5462031EEF0C28F97327095D82344841` |
| `Scripts/validate_body_shop_support_kit_native_v001_lane_v002.py` | `D5F6BD6C997DA860BA19E08EB70234DDF3E1F7BA21162B236E02071572652072` |
| `Scripts/run_body_shop_support_kit_native_unreal_import_lane_v002.ps1` | `EEFA741FB0EFE088D4E22CE2A2A46CACB2706821CF696927C5B4168082475BE9` |
| `Scripts/tests/test_body_shop_support_kit_native_unreal_import_lane_v002.py` | `79709D7C5E60B5EBED76DDBD745F61874D325A8DDF1FF6CDC265C43BF263787D` |

## Exact guarded one-shot command

Root may execute only this command, once, after confirming the v002 finalisation
marker above and the static test receipt:

```powershell
& 'C:\Users\greg_\Projects\LineBossCarFactory_Unreal 5.8\Scripts\run_body_shop_support_kit_native_unreal_import_lane_v002.ps1' -Acknowledgement 'IMPORT_FROZEN_BODYSHOP_SUPPORT_KIT_NATIVE_V001_BASELINE_V002_ONCE'
```

Do not run the disabled v001 command. Do not manually create, delete, move,
replace or promote anything under the destination before or after this lane.
