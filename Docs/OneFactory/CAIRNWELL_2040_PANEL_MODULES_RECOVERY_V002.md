# Cairnwell 2040 panel modules — validation-only Recovery v002

Status: offline-prepared and fail-closed. This lane must not be launched until
its contract pair has been frozen, independently reverified, and the exact
one-use command is separately authorized.

## Why this recovery exists

The preserved v001 panel run
`20260815T182842Z-0205ac3e` completed the physical creation/build/save of all
11 panel packages and 33 authored LODs. It did **not** complete strict asset
validation. UE 5.8 declares `AssetRegistry.get_dependencies` as returning an
optional array; the importer iterated a `None` result and emitted
`import_failure_v001.json`. The wrapper then observed
`CrashReportClientEditor:636` before its normal respawned monitor had finished
shutting down. The primary dependency-query failure and the secondary process
quiescence race are both immutable incident authority.

Recovery v002 never imports, reimports, saves, moves, copies, deletes, or
quarantines Content. It starts exactly one distinct fresh editor process to
read back the preserved packages. `None` is only normalized for a
non-persisted same-process inspection; the fresh persisted query fails closed
on `None` or an empty/mismatched dependency set. The dependency option vector
explicitly enables soft, hard, and game package references and disables editor
only, searchable-name, and management references.

## Frozen inputs and output boundary

- Panel contract SHA-256:
  `0EB0ED65D171A476D30F2F47BCEA9F63CF7CCE845369565AE6781ABE7CC35C2B`.
- Authoritative panel baseline v002 SHA-256:
  `1EFDB747E4B07BF4EC1FB6AB239D63D0FD83608926967B020D439D1C11CA2EAE`.
- The exact five-file v001 failure closure and all 11 current `.uasset` rows
  are embedded in the Recovery v002 contract.
- Recovery evidence may write only its one direct run folder under
  `Saved/Audits/OneFactory/Vehicles/Cairnwell2040PanelModules_v001/UnrealImportLane_v001/Recovery_v002`.
  The enumerated guarded engine-ephemera set comprises explicitly recorded
  mtime-only touches of the pinned ten-file closure and at most one exact
  normal Crash Reporter config file described below; it is not a claim about
  every possible non-authority ephemera surface. No second run, fallback run,
  latest-PASS search, or authority-surface write is allowed.

The original editor also touched ten project-local engine-ephemera files.
Recovery pins all ten paths, byte counts, hashes, and original mtimes. Their
path/byte/hash content must remain exact; any mtime-only touch is explicitly
recorded in the post-exit receipt/summary. Content changes, creations, or
deletions in that ten-file closure fail. A normal Crash Reporter launch may
add at most one new `UECC-Windows-<32 hex>/CrashReportClient.ini` with the
exact known 239-byte hash; every pre-existing Crash Reporter config row must
remain exact.

This is deliberately a narrow evidence boundary. Source, Config, Content,
SaveGames, the panel destination, runtime packages, prepared lane, asset-
registry cache, the ten known incident ephemera, and the Crash Reporter config
tree are guarded. The contract does not exhaustively snapshot every other
non-authority file under `Saved` or `Intermediate`, and therefore does not
claim zero untracked non-authority ephemera writes. The startup suppressors
below reduce that surface; any later promotion relies only on the exact guarded
authority and receipt claims, not on a broader whole-workspace no-write claim.

## Read-only and lifecycle guards

The guarded editor command uses `/Engine/Maps/Entry`, `-NullRHI`, `-nop4`,
`-NoCompile`, `-NoCompileEditor`, `-NoAutoSave`, `-NoSaveOnExit`,
`-NoLoadStartupPackages`, `-NoRestoreOpenAssetTabs`,
`-NoAssetRegistryCacheWrite`, and `-nowrite`. It also disables uncontrolled
changelist persistence and Python developer stub generation through exact ini
overrides. `UE_SKIP_UBT_SDK_SETUP=1` and `PYTHONDONTWRITEBYTECODE=1` are set
for the process and restored with PowerShell `NullString` semantics when they
were originally absent.

The Python scripts contain no explicit `quit_editor`; `-ExecutePythonScript`
owns natural editor shutdown. The runner rejects nonzero exit, fatal/ensure/
ModeManager signatures, UBT/AutoSDK signatures, cache writes/deletions, a
non-empty redirected stderr, missing natural-exit markers, and any package,
source, protected, prepared-lane, runtime, or cache drift.

After the editor exits, the runner polls through a 15-second bound and requires
a one-second zero-process stabilization window. It may wait only for
`CrashReportClient[Editor]` processes whose command line binds exactly to
`-MONITOR=<completed validator PID>`. PID, parent PID, creation time, command
line, and binding are recorded. A foreign reporter or a persistent reporter
fails; no reporter is killed.

## Required PASS closure

The one run must contain exactly six files:

1. `fresh_process_validation_receipt_recovery_v002.json`
2. `fresh_process_validation_recovery_v002.log`
3. `fresh_process_validation_recovery_v002.stdout.log`
4. empty `fresh_process_validation_recovery_v002.stderr.log`
5. `normal_crc_monitor_wait_recovery_v002.json`
6. `lane_summary_recovery_v002.json`

The receipt must prove 11 meshes, 33 authored LODs, exact one-UV/LOD/bounds/
collision/Nav/Nanite/material-slot rules, the exact persisted runtime material
dependency for each panel, unchanged 11 panel packages and 11 runtime
packages, and zero asset mutation. A failure receipt or partial closure is not
promotable and must remain preserved.

## Guarded command (do not run during offline preparation)

```powershell
powershell.exe -NoProfile -ExecutionPolicy Bypass -File "C:\Users\greg_\Projects\LineBossCarFactory_Unreal 5.8\Scripts\run_cairnwell_2040_panel_modules_recovery_v002.ps1" -Acknowledgement VALIDATE_CAIRNWELL_2040_PANEL_MODULES_RECOVERY_V002_ONCE
```

The current Cairnwell geometry is a DEVELOPMENT model: accepted for the game
build, stable behind ModelId/package contracts, revisionable for future model
catalogue entries, and not claimed as final-release visual art.
