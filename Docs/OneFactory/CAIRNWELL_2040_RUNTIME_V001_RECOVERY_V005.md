# Cairnwell2040Runtime_v001 incident recovery v005

Status: `OFFLINE_FROZEN__UNREAL_NOT_LAUNCHED__ONE_SHOT_RECOVERY_RESERVED`

This recovery exists only because the one authorized recovery-v004 import failed closed. It
does not approve a source edit, a tolerance relaxation, a reimport, or deletion. Recovery
v005 preserves the v001, v002, v003, and v004 failed runs, all prior quarantines, the current
eleven-package v004 namespace, the approved Meshy-derived v005 source authority, protected
Content outside the exact destination, maps, Config, saves, and the separate panel lane.

## Preserved v004 incident

- Run: `Recovery_v004/20260815T112446Z-4e34bb5c`
- Failure receipt: `import_failure_recovery_v004.json`
- Failure SHA-256:
  `D5BFCA5C8C2380587ECADDE9C64455FFD60A282D54A6FF8E27CD2E7144B494DF`
- Failure: `BIW_UnderbodySubset:LOD0 bounds/shared-pivot drift: minimum_cm`
- v004 recovery contract SHA-256:
  `C52DE8F74018D03458A94946A0B1208322881F4C52E765B474B3DE56CF8052DA`
- Quarantine receipt SHA-256:
  `D5E09C0EEE23CF6FBCC914A00DD44F5CE3EA9EF33C9461E9E6B38EE98C1CF144`
- Import process exited zero and its strict fatal/ensure log pattern set was empty. The
  failure receipt then stopped the runner before fresh validation.

The current destination contains exactly the eleven v004 packages pinned by that failure
receipt. Recovery v005 reserves one recoverable whole-directory MOVE-only quarantine:

`Saved/Quarantine/OneFactory/Vehicles/Cairnwell2040Runtime_v001/Incident_20260815T112446Z-4e34bb5c_v004`

No delete, overwrite, replace, cleanup, or second attempt is authorized.

## Exact diagnosis

The approved manifest and frozen original contract retain Blender/source-space bounds. The
legacy UE 5.8 FBX importer transforms points to Unreal's left-handed coordinates as
`(X, -Y, Z)`. The exact runtime bounds rule is therefore:

- `min=(minX,-maxY,minZ)`
- `max=(maxX,-minY,maxZ)`

The preserved v004 Underbody LOD0 package serializes:

- bounds origin at byte `15767` (`0x3D97`):
  `(0.0123748779296875, 0.48571014404296875, 41.680776596069336)`
- box extent at byte `15840` (`0x3DE0`):
  `(226.0, 79.58294677734375, 33.06645393371582)`
- actual minimum:
  `(-225.9876251220703, -79.09723663330078, 8.614322662353516)`
- actual maximum:
  `(226.0123748779297, 80.06865692138672, 74.74723052978516)`
- pivot: `(0,0,0)`

The frozen source-space minimum-Y mismatch is `0.9714353667 cm`. X/Z deltas and the
post-conversion Y delta are ordinary float quantization below `0.00003 cm`; dimensions and
pivot are unchanged. This is deterministic coordinate handedness, not transform drift,
degenerate removal, or geometry sanitation.

Applying the same evidence-backed rule to all four modules and all three authored LODs is
required. The source-space endpoint mismatch magnitudes are:

| Role | LOD0 cm | LOD1 cm | LOD2 cm |
|---|---:|---:|---:|
| `BIW_AutomotiveSkeleton` | 0.014162 | 0.014162 | 0.014162 |
| `BIW_UnderbodySubset` | 0.971461 | 1.061064 | 1.164770 |
| `EmeraldBodyVisualAuthority` | 0.000012 | 0.000012 | 0.000012 |
| `EmeraldRollingGearVisualAuthority` | 0.297791 cm | 0.297797 | 0.297797 |

Underbody fails first; RollingGear would fail later if the rule were patched only for one
asset. Recovery v005 therefore preserves every frozen source-space row separately and
derives every runtime row with the same exact transformation. The comparison tolerance is
unchanged at `0.25 cm`.

Engine evidence is pinned by hash in the v005 contract:

- `FbxUtilsImport.cpp:63-71`: `FFbxDataConverter::ConvertPos` maps `X,-Y,Z`.
- `BoxSphereBounds.h:406-410`: `FBoxSphereBounds3d` serializes Origin then BoxExtent.

## Guarded result topology

The one-shot command, if separately authorized, creates one unique child of:

`Saved/Audits/OneFactory/Vehicles/Cairnwell2040Runtime_v001/UnrealImportLane_v001/Recovery_v005`

Expected PASS evidence is:

- `quarantine_receipt_v005.json`, schema
  `lineboss/audit/cairnwell-2040-runtime-v001/recovery-v005/quarantine/v5`
- `import_receipt_recovery_v005.json`, schema
  `lineboss/audit/cairnwell-2040-runtime-v001/recovery-v005/unreal-import/v5`
- `fresh_process_validation_receipt_recovery_v005.json`, schema
  `lineboss/audit/cairnwell-2040-runtime-v001/recovery-v005/fresh-process-validation/v5`
- `lane_summary_recovery_v005.json`, schema
  `lineboss/audit/cairnwell-2040-runtime-v001/recovery-v005/import-lane-summary/v5`

All receipts bind the v001-v004 failure chronology, v005 recovery-contract SHA, incident
chain SHA, and quarantine receipt. Import pins `package_sha256`; the distinct fresh process
pins `package_sha256_before_loads` and `package_sha256_after_loads`; the wrapper independently
rehashes all eleven packages after both processes exit.

The runner permits one MOVE-only quarantine and exactly two sequential mapless full-editor
processes against `/Engine/Maps/Entry`. It requires zero exit codes, no fatal/assertion/
unhandled/ensure/ModeManager signature, no project-map load/save, and a final offline
source/protected/lane/quarantine/package reverify. It never invokes UBT.

## Offline freeze and reserved command

Freeze or verify the recovery contract offline:

```powershell
& 'C:\Program Files\Epic Games\UE_5.8\Engine\Binaries\ThirdParty\Python3\Win64\python.exe' `
  'C:\Users\greg_\Projects\LineBossCarFactory_Unreal 5.8\Scripts\prepare_cairnwell_2040_runtime_v001_recovery_v005.py' `
  --acknowledgement FREEZE_CAIRNWELL_2040_RUNTIME_V001_RECOVERY_V005_ONCE
```

The reserved, unexecuted one-shot command is:

```powershell
& 'C:\Users\greg_\Projects\LineBossCarFactory_Unreal 5.8\Scripts\run_cairnwell_2040_runtime_import_lane_v001.ps1' `
  -Acknowledgement RECOVER_QUARANTINED_CAIRNWELL_2040_RUNTIME_V001_V005_ONCE
```

Freezing this offline contract does not authorize that command. A root review and explicit
launch coordination are still required.
