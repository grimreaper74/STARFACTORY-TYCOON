# Cairnwell 2040 runtime recovery V013

V013 is a distinct, additive, validation-only successor for the exact V009 Unreal import. It never imports, reimports, saves, moves, copies, deletes, or rewrites a Content package. The consumed V012 contract, sidecar, PASS receipt, three logs, and failed wrapper summary remain byte-for-byte chronology evidence; V012 is never rerun or rewritten.

## Why V013 exists

The V012 Unreal validator completed its fresh read-only checks, wrote an internally valid PASS receipt, exited 0 naturally, and preserved all 11 package hashes, source, protected project, prepared lane, namespace, registry, and cache evidence. Its PowerShell wrapper nevertheless failed for two separate reasons:

- it classified the informational `CleanupOrphanedCacheFiles (PostWrite)` label as fatal even though the immediately adjacent result reported one referenced binary kept, zero orphans deleted, and zero orphans locked;
- PowerShell coerced a null argument passed to `SetEnvironmentVariable` into an empty string, so an originally absent process environment value did not restore to true absence.

V013 does not retroactively call the V012 wrapper a PASS. It pins the exact failed wrapper history and performs one new read-only validator run with corrected evidence and restoration gates.

## Exact cache adjudication

V013 retains `-NoAssetRegistryCacheWrite` and the exact two-file `Intermediate/CachedAssetRegistry` snapshot. In each primary Unreal log it requires exactly one PreLoad cleanup line and exactly one PostWrite cleanup line. Each phase line must be followed immediately by the exact result stating one referenced binary kept, zero old-style files, zero orphans deleted, and zero orphans locked; that result must occur exactly twice. Validator stderr must be exactly empty.

The installed UE 5.8 `AssetDataGatherer.cpp` authority is SHA-256 `9B62B0B7AFF852029CA82576570B5F9A9F3791E605667B1D20F0B7896511D6CC`. Its no-write flag disables gather and discovery cache writes, while cache cleanup can still run for a read-enabled cache. Therefore the phase label alone is not mutation proof. Actual cache-write, orphan-deletion, failed-deletion, and legacy-cleanup tokens remain fatal, and the full cache snapshot must be identical after natural editor exit.

UE cleanup can silently remove temporary files and the old `Intermediate/CachedAssetRegistry.bin` or `Intermediate/CachedAssetRegistry_*.bin` forms. V013 therefore also freezes their exact pre-validation absence and proves the same absence in the receipt, post-exit summary, and final verifier. This is separate from the current two-file sharded-cache closure.

## Exact environment restoration

The runner saves all three process-scoped values: the run-root acknowledgement variables and `UE_SKIP_UBT_SDK_SETUP`. A previously absent value is restored with `[System.Management.Automation.Language.NullString]::Value`; a present value is restored as its exact ordinal string. All three are reread and compared after the validator even on failure. A restoration error prevents PASS, and every late failure rewrites the summary to FAIL_CLOSED before rethrowing.

## Stable model identity and revisionable art

The gameplay/save/order/genealogy ModelId remains the stable `CAIRNWELL_2040`. The DEVELOPMENT recipe `CAIRNWELL_2040_DEVELOPMENT_RECIPE_V001` and replaceable geometry authority `Cairnwell2040Runtime_v001_V009ImportedGeometry` are separate fields. The current car is approved for DEVELOPMENT game builds and remains revisionable, not final-release art. Future visual replacement must preserve the ModelId seam and may introduce new recipes or geometry authorities without renaming current package paths around the gameplay identity.

## Guarded topology

The offline contract reconstructs and validates its full 69-file prepared-lane payload before any write. It pins the exact V009 PASS import, immutable stale V010 pair, consumed V011 failure, consumed V012 wrapper failure and PASS receipt, the six exact persisted dependency lists, the 11 package hashes, cache and legacy-cache absence, installed engine authority, source/protected/lane inventories, and exact result topology.

The Windows PowerShell 5.1-compatible runner starts exactly one full `UnrealEditor.exe` validator on `/Engine/Maps/Entry`. It launches no importer, performs no Content move, sets `UE_SKIP_UBT_SDK_SETUP=1`, rejects live UBT command lines, uses natural deferred `-ExecutePythonScript` exit, and writes only a new V013 Saved audit root. PASS is emitted only after exact four-file post-validator closure, exact five-file final closure, strict duplicate-safe receipt and summary validation, cache and package invariance, environment restoration, zero real cleanup mutation, and zero Unreal/UBT processes.

## Offline preparation

No-write full candidate preflight:

```powershell
& 'C:\Program Files\Epic Games\UE_5.8\Engine\Binaries\ThirdParty\Python3\Win64\python.exe' -B 'C:\Users\greg_\Projects\LineBossCarFactory_Unreal 5.8\Scripts\prepare_cairnwell_2040_runtime_v001_recovery_v013.py' --dry-build
```

After an independent pre-cut audit returns GO, freeze the pair once:

```powershell
& 'C:\Program Files\Epic Games\UE_5.8\Engine\Binaries\ThirdParty\Python3\Win64\python.exe' -B 'C:\Users\greg_\Projects\LineBossCarFactory_Unreal 5.8\Scripts\prepare_cairnwell_2040_runtime_v001_recovery_v013.py' --acknowledgement FREEZE_CAIRNWELL_2040_RUNTIME_V001_RECOVERY_V013_ONCE
```

Contract creation authorizes no Unreal or UBT launch. The guarded one-use command may run only after a separate post-cut review confirms exact frozen hashes, absent `Recovery_v013`, the immutable V012 run, exact package/cache/legacy-absence closures, and zero Unreal/UBT processes:

```powershell
& 'C:\Users\greg_\Projects\LineBossCarFactory_Unreal 5.8\Scripts\run_cairnwell_2040_runtime_validation_recovery_v013.ps1' -Acknowledgement VALIDATE_CAIRNWELL_2040_RUNTIME_V001_V009_IMPORT_V013_ONCE
```
