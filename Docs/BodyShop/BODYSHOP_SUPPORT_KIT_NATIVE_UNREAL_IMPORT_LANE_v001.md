# Body Shop native support kit v001 — guarded Unreal import lane

Status: `NOT_RUNNABLE__PROTECTED_BASELINE_NOT_CUT`

Checkpoint marker: `NO_SUPPORT_KIT_UNREAL_RUN_YET`

This lane is intentionally disabled until the native robot work has stopped
changing protected `Source` and `Content`. The baseline JSON does not exist and
all baseline pins are sixty-four zeroes. Therefore the importer, validator and
runner fail before Unreal mutation even if someone tries the final command.

## Frozen source authority

The source is the clean-room procedural candidate at
`SourceAssets/Candidate/WeldShop/BodyShopSupportKitNative_v001`:

| Authority | SHA-256 |
|---|---|
| `Audit/FROZEN_v001.json` | `A4E4BF52C46F93EF5A084A708D94A7B2B920ABDC702CF655B5A8569920A9AD6F` |
| `MANIFEST_v001.json` | `F0EFB621EC94C0D5E4806487576E1C6AE13EE8158A68A8D445052D6F33C700EC` |
| `Authority/LB_BodyShopSupportKitNative_v001.blend` | `5D69E9F6D4770475BC91AD1EAC61F528EEA3F7D8C4A3979BFF6F92B5ACC60F18` |
| `Audit/geometry_inventory_v001.json` | `1DC636BD128CC5CA37161638F92E63DA566BE7F14A293833280643F9A4441A67` |
| `Audit/roundtrip_validation_v001.json` | `8933C5A746070FEB6B628786E7BD52543D96D8162CCC3B27D2BF37618D098A4A` |
| `Audit/SHA256SUMS_v001.txt` | `FD78070F1E68950241035ED8B4AFDA79BD94E10F43759EBCB712AA674CB3A627` |

The source freeze proves exactly 12 assets, 36 LOD meshes, 72 FBX/GLB
round-trips, floor-centred pivots, identity transforms, clean-room provenance
and aggregate triangles of 20,408 / 7,580 / 1,780 for LOD0 / LOD1 / LOD2.

## Isolated destination and exact asset set

The only Content write root is:

`/Game/LineBoss/Candidates/WeldShop/BodyShopSupportKitNative_v001`

Exactly 12 StaticMesh packages are allowed, each assembled from exactly three
frozen FBXs (36 FBX bindings total):

- Logistics: empty/full panel stillages, empty-return cart, component-service
  pallet, open small-parts crate and open small-parts bin.
- Controls: electrical cabinet and HMI pedestal.
- Safety: 2 m guard panel and 2 m interlocked guard gate.
- Services: utility pedestal and weld-extraction pedestal.

No material, texture, map, Blueprint or runtime-binding package may be created.
The namespace must not exist before the lane. Replacement and retry are false;
any earlier PASS or FAIL receipt consumes v001.

## Unreal contract

- FBX conversion is metres to centimetres with scene/unit conversion enabled,
  vertex-to-absolute enabled and pivot baking disabled.
- Imported materials/textures, generated lightmap UVs, generated collision,
  degeneracy removal and Nanite are disabled.
- Every LOD retains one UV channel, exact triangle count, semantic section order,
  frozen dimensions, XY-centred footprint and floor Z=0 pivot.
- Manual screen sizes are `[1.0, 0.45, 0.18]`. They are written only after all
  LOD, material, collision and Nanite operations, saved/compiled, then reapplied
  and saved with no later build operation.
- Every non-enterable support prop receives one deterministic AABB box simple
  collision and `CTF_USE_DEFAULT`; a runtime gate actor must move/toggle its
  component collision when opened.
- Nine source semantic slots bind deterministically to the already promoted,
  protected Body Shop presentation-material v002 family. No copied materials
  are created in the candidate namespace.

## Protection and independent evidence

The final baseline will hash and inventory the project descriptor, complete
`Source`, complete `Config`, campaign saves, Press v913, the Body Shop map and
all existing `Content` except the brand-new support namespace. The importer
checks metadata for every protected file and hashes all critical code/config/
save/map/material authorities before and after import. A second, distinct
UnrealEditor process independently hashes every protected file and verifies all
12 freshly loaded packages without saving anything.

The PowerShell runner refuses active Unreal/build processes, uses no UBT, uses
`-NoCompile`, materialises `$Process.Handle`, flushes redirected streams,
refreshes the process object and fails if PowerShell 5.1 returns a null exit
code. Partial packages are preserved on failure for explicit recovery; there is
no automatic deletion.

## Provisional checkpoint hashes

These hashes describe the syntax-clean but deliberately disabled checkpoint:

| File | SHA-256 |
|---|---|
| `Scripts/freeze_body_shop_support_kit_native_unreal_import_baseline_v001.py` | `5F0783286A5F32E8740AE4BC0049021BAB73F41FCC1B7DD340ACE55BA2E1D27B` |
| `Scripts/import_body_shop_support_kit_native_v001.py` | `A911433021C50D78D2CDA26757468A3490A9CE0AAE43667446B124E13741147A` |
| `Scripts/validate_body_shop_support_kit_native_v001.py` | `9E6ECAE2B978686585CD1E5215957F2555181131C3ED36BFE56E75D63FAB8ADC` |
| `Scripts/run_body_shop_support_kit_native_unreal_import_lane_v001.ps1` | `F1E9DA58655345ABF65DFCAC5FCB764CE5855D8826BA2C064F145CDE5C5AF631` |
| `Scripts/tests/test_body_shop_support_kit_native_unreal_import_lane_v001.py` | `8171FDC3200D1C3F184C9BCB800F894B4B3BA5B95768790AC8685E7691574A74` |

## Finalisation after robot Content settles

1. Confirm no Unreal/build process and no prior support-kit result.
2. Run the offline freezer once with `--write` from the exact project root.
3. Pin that baseline SHA-256 in importer and validator.
4. Pin final baseline/freezer/importer/validator hashes in the runner.
5. Run the offline unit suite and PowerShell parser; update this document from
   provisional to frozen.
6. Root alone may then execute this exact one-shot command:

```powershell
& 'C:\Users\greg_\Projects\LineBossCarFactory_Unreal 5.8\Scripts\run_body_shop_support_kit_native_unreal_import_lane_v001.ps1' -Acknowledgement 'IMPORT_FROZEN_BODYSHOP_SUPPORT_KIT_NATIVE_V001_ONCE'
```

Do not run that command while this document says `NOT_RUNNABLE`.
