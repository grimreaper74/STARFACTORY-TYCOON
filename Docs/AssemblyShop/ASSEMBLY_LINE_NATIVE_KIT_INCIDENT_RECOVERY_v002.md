# Assembly Line Native Kit — incident recovery v002

Static-only preparation complete. No Unreal, importer, UBT, or Content-writing process was launched while preparing this successor lane.

## Incident boundary

The original one-shot run `20260815T025138Z-2b421583` produced a valid PASS import receipt and exactly eight finished StaticMesh packages. Its fresh validator then failed only because the complete Source inventory intentionally advanced from 276 to 278 files while that run was active.

The successor baseline accepts exactly these two additions and no others:

- `LBOneFactoryCaptureBridge.h` — `5D24296B0FF7239276793DCA0232DBFB239E6C393B0ED7EA2D767F15BFF7F8C8`
- `LBOneFactoryCaptureBridge.cpp` — `447C04E64A2F322754C6F78523A34A59D9E133B3D949B766064D9FD112F15ECD`

The original baseline, scripts, documentation, static receipt, run directory, PASS import receipt, failure receipt, logs, and all eight imported packages remain byte-for-byte preserved. Nothing is archived, moved, replaced, deleted, reimported, or overwritten.

## Recovery behavior

The one-use command launches exactly one new full UnrealEditor process. It never launches the importer and authorizes no Content writes or asset/map saves. The independent process fresh-loads the existing namespace and checks:

- exactly eight packages and 24 authored LODs;
- exact triangles, one UV channel, bounds and pivots for every LOD;
- semantic material slots/bindings, manual LOD screen sizes, per-asset collision, and Nanite disabled;
- exact package hashes from PASS receipt `C0E1F8D3E7B6EEBB2780067671AF408C53368DEA9370B3AA56B9F7F3AAFD49F7`;
- all 62 frozen original-procedural source-kit files;
- the settled 278-file Source tree, complete Config, saves, all current Content, exact department maps, and the complete original incident evidence.

Any PASS or FAIL receipt permanently consumes recovery v002. Failure evidence and the original imported packages must be preserved.

## Exact one-use command

```powershell
powershell.exe -NoProfile -ExecutionPolicy Bypass -File "C:\Users\greg_\Projects\LineBossCarFactory_Unreal 5.8\Scripts\run_assembly_line_native_kit_incident_recovery_v002.ps1" -Acknowledgement REVALIDATE_EXISTING_ASSEMBLY_NATIVE_KIT_V001_INCIDENT_V002_ONCE
```

This command remains unconsumed by the static preparation task.
