# Cairnwell2040Runtime_v001 incident recovery v002

Status: `OFFLINE_FROZEN__UNREAL_NOT_LAUNCHED`

This is a one-use, incident-bound recovery for failed v001 run
`20260815T094919Z-7dfb3c0a`. It does not replace or edit that run. The failed
run remains under
`Saved/Audits/OneFactory/Vehicles/Cairnwell2040Runtime_v001/UnrealImportLane_v001/20260815T094919Z-7dfb3c0a`.
Its `import_failure_v001.json` SHA-256 is
`05F204CDE09BD22BED823101525C82F64E18F8EE56BC6004C9E0979AA73CFC2D`.
The old v001 fresh-process PASS receipt remains absent.

## Root cause and smallest correction

The material graph failed while connecting normalized luminance to the Clamp
expression's semantic `Input`. Installed UE 5.8 source
`MaterialGraphNode.cpp:597-613` proves that
`UMaterialGraphNode::GetShortenPinName` maps `MaterialPinNames::Input` to
`NAME_None`. Therefore `MaterialEditingLibrary.connect_material_expressions`
must receive an empty `ToInputName` (an empty destination input name) for this
first Clamp input. The
importer now connects `normalized_luminance -> detail_clamp` with `""`, and the
fresh validator expects Clamp input names `{"", "Min", "Max"}`.

The shutdown fatal was secondary. Installed
`EditorPythonExecuter.cpp:47,125` says `-ExecutePythonScript` needs a full tick
before close and defers `QUIT_EDITOR` itself. Both Python scripts have therefore
removed explicit same-frame `unreal.SystemLibrary.quit_editor()` calls. The
runner still requires process exit code 0 and rejects any fatal/crash; a PASS
receipt cannot excuse a non-zero exit.

Engine-source evidence inspected read-only:

- `MaterialGraphNode.cpp` SHA-256
  `026D9A5C896AF1E590E4BD8E42F1EC4788C8210198007D79C5051F8792716DD9`.
- `EditorPythonExecuter.cpp` SHA-256
  `AB9EB8F439AAD66A18C632E8CDA227A2252F737A9E4BE8150407F9C6BEFCA8B2`.

## Preserved partial closure and quarantine

The failed run produced exactly three textures and one galvanized-BIW material.
Their exact bytes, mtimes, and SHA-256 values are pinned by
`Scripts/cairnwell_2040_runtime_v001_recovery_v002_contract.json` and must match
the immutable v001 failure receipt. Recovery performs exactly one recoverable
directory move:

`Content/LineBoss/Factory/OneFactory/v001/Vehicles/Cairnwell2040Runtime_v001`

to

`Saved/Quarantine/OneFactory/Vehicles/Cairnwell2040Runtime_v001/Incident_20260815T094919Z-7dfb3c0a_v001`.

There is no delete, overwrite, reimport, or automatic cleanup. The destination
and quarantine paths are checked exactly before the move, and all four files are
re-hashed after it. Any result or pre-existing quarantine makes v002 refuse a
rerun; further recovery would require a separately reviewed v003.

## Exact recovery receipt topology

Each run is under
`Saved/Audits/OneFactory/Vehicles/Cairnwell2040Runtime_v001/UnrealImportLane_v001/Recovery_v002/<UTC>-<GUID8>`.

- `quarantine_receipt_v002.json` uses schema
  `lineboss/audit/cairnwell-2040-runtime-v001/recovery-v002/quarantine/v2` and
  PASS status
  `PASS__CAIRNWELL_2040_RUNTIME_V001_RECOVERY_V002_PARTIALS_QUARANTINED`.
- `import_receipt_recovery_v002.json` uses schema
  `lineboss/audit/cairnwell-2040-runtime-v001/recovery-v002/unreal-import/v2` and
  records all 11 hashes in `package_sha256`.
- `fresh_process_validation_receipt_recovery_v002.json` uses schema
  `lineboss/audit/cairnwell-2040-runtime-v001/recovery-v002/fresh-process-validation/v2`
  and records the same 11 hashes in `package_sha256_before_loads` and
  `package_sha256_after_loads`.
- `lane_summary_recovery_v002.json` uses schema
  `lineboss/audit/cairnwell-2040-runtime-v001/recovery-v002/import-lane-summary/v2`
  and PASS status
  `PASS__CAIRNWELL_2040_RUNTIME_V001_RECOVERY_V002_GUARDED_IMPORT_AND_DISTINCT_READ_ONLY_RELOAD`.

Every recovery receipt binds `recovery_contract_sha256`, `failed_run_id`,
`failed_import_failure_sha256`, `incident_binding_sha256`, and the exact
`quarantine_receipt`. The separate 11-panel namespace is outside this lane and
is neither moved nor imported.

## Guarded execution (not performed by the offline freeze)

Only the exact runner may perform the move and two sequential Unreal processes:

```powershell
& 'C:\Users\greg_\Projects\LineBossCarFactory_Unreal 5.8\Scripts\run_cairnwell_2040_runtime_import_lane_v001.ps1' -Acknowledgement RECOVER_QUARANTINED_CAIRNWELL_2040_RUNTIME_V001_V002_ONCE
```

Both processes use `/Engine/Maps/Entry`, `LoadLevelAtStartup=None`, `-NoCompile`,
`-NoAutoSave`, and `-NoSaveOnExit`. No UBT/build command, project map, Source,
Config, save game, runtime binding, or panel package is authorized.
