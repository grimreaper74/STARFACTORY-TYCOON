# Cairnwell 2040 runtime v001 incident recovery v009

Status: offline candidate-payload preflight and freeze lane only. Unreal execution is not authorized by the freeze.

## Preserved chronology

Recovery v006 failed closed only because UE 5.8 reports the unnamed Clamp input as literal Python `str` `None`. The importer’s empty destination input is correct. The validator now first requires exact raw type and class-specific order, then maps only literal `None` to the logical empty graph key. Duplicate canonical names, raw empty reflected names, and raw `None` in canonical graph evidence are rejected.

V007 encoded that fix but lacked exact extra-file rejection for every older evidence directory. V008 added that closure, then its first post-freeze pre-quarantine verifier stopped before any move because an offline Python module constant was addressed through the wrong module. Both v007 and v008 contract/sidecar pairs remain byte-exact, stale, unexecuted chronology evidence. They are not overwritten or deleted.

V009 pins:

- exact v001–v006 failed-run roots and all-file counts `5, 6, 6, 6, 6, 6`;
- exact q1–q5 quarantine roots and all-file counts `4, 7, 11, 11, 11`;
- every row, byte count, mtime, and SHA-256 inside those eleven roots;
- the v007 pair (`7271F549...F7698F` / `ECC793B9...508F`);
- the v008 pair (`6E8E2D0...E5E49BD` / `D082F35B...A054F`);
- all original and earlier recovery contracts/sidecars, v005 texture-forensics files and receipt, fourteen distinct installed UE 5.8 source authorities, and the exact current eleven v006 packages;
- absence of `Recovery_v007`, `Recovery_v008`, `Recovery_v009`, and q6 before any move.

## Required no-write preflight

Before the v009 contract may be written, this command constructs the entire candidate payload in memory, validates it with the same authority function used by contract creation and frozen loading, JSON round-trips it, and computes its candidate hash and byte count without writing any file:

```powershell
python -B 'C:\Users\greg_\Projects\LineBossCarFactory_Unreal 5.8\Scripts\prepare_cairnwell_2040_runtime_v001_recovery_v009.py' --dry-build
```

The dry build exercises every v001–v006 failure hash, exact incident/quarantine root and count, stale-pair row, inherited material/UV/bounds/enum authority, active 41-file lane row, result topology, policy, package row, and absence gate. Its generated timestamp is deterministically derived from the newest exact lane-input mtime, so an unchanged dry build and freeze construct byte-identical payloads. Contract creation calls that same full-payload validator again before its only two writes. Frozen loading reconstructs the expected payload from independent authorities and requires exact equality.

## Recovery operation and runner

The only Content mutation is one recoverable `MOVE_DIRECTORY_ONLY__NO_DELETE` of the current exact eleven-file namespace to `Saved/Quarantine/OneFactory/Vehicles/Cairnwell2040Runtime_v001/Incident_20260815T124823Z-67c989ee_v006`. Delete, overwrite, implicit replacement, reimport, and rerun after any result remain forbidden.

The guarded runner requires zero Unreal Editor and Unreal build processes, re-runs the offline pre-quarantine verifier, moves the whole directory once, and starts two distinct full-editor processes on `/Engine/Maps/Entry`. Both scripts use the natural deferred `-ExecutePythonScript` exit. Exit code must be zero; fatal, assertion, ensure, `ModeManager`, shutdown, and unhandled-exception signatures are rejected. After process B exits, the runner requires exact all-file and hash closure for the eleven expected packages.

The open user Unreal Editor means execution is currently blocked by design. Do not execute until all Unreal/UBT processes have exited and root explicitly coordinates the one shot.

Exact guarded command after separate authorization:

```powershell
& 'C:\Users\greg_\Projects\LineBossCarFactory_Unreal 5.8\Scripts\run_cairnwell_2040_runtime_import_lane_v001.ps1' `
  -Acknowledgement RECOVER_QUARANTINED_CAIRNWELL_2040_RUNTIME_V001_V009_ONCE
```

The offline freeze acknowledgement is `FREEZE_CAIRNWELL_2040_RUNTIME_V001_RECOVERY_V009_ONCE`. The freeze and dry build do not launch UE/UBT, move Content, or write Source, Config, maps, saves, or the separate 11-panel namespace.
