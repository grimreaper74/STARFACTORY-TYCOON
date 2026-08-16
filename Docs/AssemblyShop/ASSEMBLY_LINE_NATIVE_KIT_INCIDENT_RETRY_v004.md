# Assembly Line Native Kit — chronology-safe retry v004

Static-only preparation is complete. Unreal, UBT, the importer, and every Content-writing API remained unused while preparing v004.

## Why v003 failed safely

The forward-slash command correction worked and Python executed. Validation then failed before loading any asset because the v003 runtime inherited `v002.verify_incident(baseline)`. That historical function correctly records the first two CaptureBridge additions, but it also compared those old hashes to the later UI v005 files. The failed v003 run `20260815T032759Z-6c42095d` contains five immutable evidence files and reports zero Content writes, imports, saves, reimports, or deletes.

## v004 separation

v004 verifies chronology and current state independently:

- The initial header/source hashes remain pinned inside the immutable v002 baseline and static authority.
- The live 278-file Source tree is checked only against the successor baseline and frozen UI v005 hashes: header `2C5442B15B94504CEA085A3F46F4740BCC4FD0A83CDE70DB37E3C7D0FC04673B`, source `849C7E1ACD6A02B27126831202E774E8C922E422050904EC3DF5349C6D01CA30`.
- Exact v002 and v003 failed-run evidence is checked before and after asset reload.
- The existing eight Assembly packages are fresh-loaded and checked for 24 authored LODs, exact triangles, one UV per LOD, bounds, pivots, materials, deterministic collision, manual screen sizes, Nanite off, and unchanged package hashes.
- The importer is absent. The sole Unreal process is a read-only validator and may write only its new v004 Saved evidence.

The validator path is normalized and checked against this exact control-character-free argument:

```text
-ExecutePythonScript="C:/Users/greg_/Projects/LineBossCarFactory_Unreal 5.8/Scripts/revalidate_assembly_line_native_kit_incident_v004.py"
```

## Exact one-use command

```powershell
powershell.exe -NoProfile -ExecutionPolicy Bypass -File "C:\Users\greg_\Projects\LineBossCarFactory_Unreal 5.8\Scripts\run_assembly_line_native_kit_incident_retry_v004.ps1" -Acknowledgement REVALIDATE_EXISTING_ASSEMBLY_NATIVE_KIT_V001_INCIDENT_V004_ONCE
```

The command is unconsumed. Any PASS or FAIL result permanently consumes v004.
