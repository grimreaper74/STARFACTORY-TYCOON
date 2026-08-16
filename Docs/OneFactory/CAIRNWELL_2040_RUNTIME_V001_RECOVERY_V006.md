# Cairnwell2040Runtime_v001 incident recovery v006

Status: `OFFLINE_FROZEN__UNREAL_NOT_LAUNCHED__ONE_SHOT_RECOVERY_RESERVED`

This recovery exists only because the one authorized recovery-v005 import failed closed.
It preserves the complete v001-v005 failure chronology, every prior quarantine, the exact
current eleven-package namespace, the approved Meshy-derived v005 source authority, maps,
Config, saves, protected Content, and the disjoint panel lane. It does not authorize source
edits, semantic-gate relaxation, package deletion, overwrite, reimport, or a second attempt.

## Preserved v005 incident

- Run: `Recovery_v005/20260815T115847Z-92ea69dd`
- Failure receipt SHA-256:
  `435D82778C83CDACAA2E59F91E04273181BA710F5D0BAFFA719A15E04A9F48BB`
- Failure: `texture dimensions/colour/compression drift: base_color`
- v005 recovery contract SHA-256:
  `E5E9F4CF0E003C0B5936E0EED581D6E697E1C20AD0BC1B390E6FA7D3ADD2E239`
- Quarantine receipt SHA-256:
  `17CCF587D92D0FBE85E704112B70CA17937E047EB2F4BB3003C40EDB5DD9315E`
- Import PID `22444` exited zero with no fatal/ensure signature. Redirected log read-open
  attempts were exactly log/stdout/stderr `1/6/1` within the `15000 ms` bound. The failure
  receipt stopped the runner before fresh validation.

The current destination contains exactly the eleven v005 packages pinned by that failure
receipt (three textures, four materials, and four three-LOD meshes). Recovery v006 reserves
one recoverable whole-directory MOVE-only quarantine:

`Saved/Quarantine/OneFactory/Vehicles/Cairnwell2040Runtime_v001/Incident_20260815T115847Z-92ea69dd_v005`

No delete, overwrite, replace, cleanup, or second attempt is authorized.

## Exact texture and enum diagnosis

The serialized AssetRegistry tags and one separately authorized mapless read-only load prove
that all three textures are correct:

| Semantic | Dimensions | sRGB | Compression | Flip green |
|---|---:|---:|---|---:|
| `base_color` | 2048×2048 | true | `TC_DEFAULT` | false |
| `metallic_roughness` | 2048×2048 | false | `TC_MASKS` | false |
| `normal` | 2048×2048 | false | `TC_NORMALMAP` | true |

The successful diagnostic receipt is
`Recovery_v005_TextureForensics/Run_readonly_20260815T121015Z/texture_runtime_properties_read_only.json`,
SHA-256 `8476C9EF8CFE8A3E58C383FEC80085370F2554F91618569598FDE5D975E79A4A`.
It loaded only `/Engine/Maps/Entry.Entry`, authorized no package save, and proved all three
package hashes unchanged.

UE 5.8's Python enum wrapper formats `str(enum)` as `<Type.NAME: numeric_value>`. The old
suffix comparator therefore rejected correct values such as
`<TextureCompressionSettings.TC_DEFAULT: 0>`, because the string ends in `: 0>` rather than
`TC_DEFAULT`. Installed `PyWrapperEnum.cpp` lines `378-385` prove the representation and
lines `388-410` prove exact equality; the source SHA-256 is
`54488C18B0C2916E89BF416EAC8F008E79AF430AC2F4EA8299A603D5809693AA`.

Recovery v006 removes every enum-string suffix/substring seam and requires exact type/value identity
for texture compression, material samplers, clamp mode, collision trace, blend mode,
and material domain. It retains exact dimensions, sRGB, flip-green, socket/channel, graph,
collision, navigation, Nanite, LOD, UV, bounds, pivot, material, and dependency gates. Opaque
surface and `two_sided=false` are now explicitly revalidated.
Compound failures name every mismatched field and include exact expected and actual evidence.

## Guarded result topology

The reserved command creates one unique child of:

`Saved/Audits/OneFactory/Vehicles/Cairnwell2040Runtime_v001/UnrealImportLane_v001/Recovery_v006`

Expected PASS evidence is:

- `quarantine_receipt_v006.json`, schema
  `lineboss/audit/cairnwell-2040-runtime-v001/recovery-v006/quarantine/v6`
- `import_receipt_recovery_v006.json`, schema
  `lineboss/audit/cairnwell-2040-runtime-v001/recovery-v006/unreal-import/v6`
- `fresh_process_validation_receipt_recovery_v006.json`, schema
  `lineboss/audit/cairnwell-2040-runtime-v001/recovery-v006/fresh-process-validation/v6`
- `lane_summary_recovery_v006.json`, schema
  `lineboss/audit/cairnwell-2040-runtime-v001/recovery-v006/import-lane-summary/v6`

Every receipt binds the v001-v005 failure chain, recovery-contract SHA, recomputed incident
chain SHA, and quarantine receipt. Import pins `package_sha256`; a distinct fresh process pins
`package_sha256_before_loads` and `package_sha256_after_loads`; the runner independently
rehashes all eleven packages after both processes exit.

The runner permits one MOVE-only quarantine and exactly two sequential mapless full-editor
processes against `/Engine/Maps/Entry`. It requires zero exit codes, no fatal/assertion/
unhandled/ensure/ModeManager signature, no project-map load/save, and final offline
source/protected/lane/quarantine/package revalidation. It never invokes UBT.

## Offline freeze and reserved command

Freeze or verify the v006 recovery contract offline:

```powershell
& 'C:\Program Files\Epic Games\UE_5.8\Engine\Binaries\ThirdParty\Python3\Win64\python.exe' `
  'C:\Users\greg_\Projects\LineBossCarFactory_Unreal 5.8\Scripts\prepare_cairnwell_2040_runtime_v001_recovery_v006.py' `
  --acknowledgement FREEZE_CAIRNWELL_2040_RUNTIME_V001_RECOVERY_V006_ONCE
```

The reserved, unexecuted one-shot command is:

```powershell
& 'C:\Users\greg_\Projects\LineBossCarFactory_Unreal 5.8\Scripts\run_cairnwell_2040_runtime_import_lane_v001.ps1' `
  -Acknowledgement RECOVER_QUARANTINED_CAIRNWELL_2040_RUNTIME_V001_V006_ONCE
```

Freezing this offline contract does not authorize that command. Root review and explicit
launch coordination remain required.
