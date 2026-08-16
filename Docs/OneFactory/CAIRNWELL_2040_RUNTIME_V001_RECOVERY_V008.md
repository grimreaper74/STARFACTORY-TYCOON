# Cairnwell 2040 runtime v001 incident recovery v008

Status: offline-frozen recovery design only. Unreal execution is not authorized by the freeze step.

## Why v008 exists

Recovery v006 imported the exact eleven expected packages and exited through the strict process/log gate, then failed closed during same-process material validation. UE 5.8 reflected the Clamp first input as the literal Python string `None`. The failed validator expected the logical unnamed key as an empty string. The Clamp mode and its minimum/maximum defaults were correct, so this is a deterministic reflected-name validation defect, not an asset or connection defect.

The provisional v007 contract corrected that reflected-name interpretation but did not prove the absence of extra files in every older incident and quarantine directory before the move. Its contract and sidecar are preserved byte-exact as stale, unexecuted chronology evidence. Recovery v008 supersedes v007 without deleting or overwriting it.

## Exact material-input rule

The importer continues to connect the Clamp first input with the empty destination name required by `MaterialEditingLibrary`.

The validator first requires each reflected name to be an exact Python `str` and requires the exact class-specific order:

- `MaterialExpressionLinearInterpolate`: `A`, `B`, `Alpha`
- both `MaterialExpressionMultiply` nodes: `A`, `B`
- `MaterialExpressionClamp`: `None`, `Min`, `Max`
- `MaterialExpressionDotProduct`: `A`, `B`

Only after that exact raw gate, literal `None` is mapped to logical empty string for graph-link evidence. Raw empty input names are rejected, duplicate canonical names are rejected, and raw `None` cannot leak into canonical graph evidence. No semantic material gate is relaxed.

The frozen proof chain pins the installed UE 5.8 sources for material input enumeration, pin shortening, `FName::ToString`, Python `FString` conversion, input iteration, and the exact Clamp/Lerp/Multiply/Dot declarations.

## Preserved chronology and exact closures

V008 preserves the original contract and baseline, the v001 through v006 failed runs, the q1 through q5 quarantines, the v005 texture-forensics evidence, all recovery contracts and sidecars, and the current exact eleven v006 packages.

Before any move, the offline verifier requires all-file path-set equality, exact file counts, bytes, mtimes, and hashes for:

- incident roots v001–v006 with exact counts `5, 6, 6, 6, 6, 6`;
- quarantine roots q1–q5 with exact counts `4, 7, 11, 11, 11`;
- the stale v007 contract (`7271F549...F7698F`) and sidecar (`ECC793B9...508F`) at their exact paths;
- the absent `Recovery_v007` result root and absent q6 quarantine at freeze time;
- the current destination as exactly eleven files and no sidecars or bulk-data extras.

The v008 quarantine is one recoverable whole-directory move (`MOVE_DIRECTORY_ONLY__NO_DELETE`) to `Saved/Quarantine/OneFactory/Vehicles/Cairnwell2040Runtime_v001/Incident_20260815T124823Z-67c989ee_v006`. Delete, overwrite, reimport, and implicit replacement remain forbidden.

## Guarded execution contract

The runner remains one-use and fail-closed. It requires no Unreal Editor or Unreal build process at start, moves the current namespace only after the complete offline preflight, runs import and fresh validation in two distinct full-editor processes, uses `/Engine/Maps/Entry`, permits natural `-ExecutePythonScript` exit only, requires exit code zero, rejects fatal/assert/ensure/ModeManager/shutdown signatures, and performs a final exact all-file eleven-package/hash closure after process B exits.

The current open user Unreal Editor means the runner process guard must fail closed. Do not execute until every Unreal Editor and UBT/build process has exited and root explicitly coordinates the one shot.

Exact guarded command after that separate authorization:

```powershell
& 'C:\Users\greg_\Projects\LineBossCarFactory_Unreal 5.8\Scripts\run_cairnwell_2040_runtime_import_lane_v001.ps1' `
  -Acknowledgement RECOVER_QUARANTINED_CAIRNWELL_2040_RUNTIME_V001_V008_ONCE
```

The offline contract freeze uses `FREEZE_CAIRNWELL_2040_RUNTIME_V001_RECOVERY_V008_ONCE`. It does not launch Unreal, invoke UBT, move Content, or write maps, Config, Source, saves, or the separate panel namespace.
