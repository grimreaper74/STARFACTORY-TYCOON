# Cairnwell 2040 runtime recovery V012

V012 is a distinct, additive, validation-only recovery for the exact V009 Unreal import. It does not import, reimport, save, move, copy, delete, or rewrite any Content package. V011 and its consumed five-file failed run remain byte-for-byte chronology evidence and V011 must never be rerun.

## Why V012 exists

V011 completed the read-only Unreal asset checks with exit code 0, unchanged package/source/protected/lane evidence, natural editor shutdown, and no fatal, ensure, or UBT log token. Its offline expected receipt was nevertheless incomplete. The fresh Asset Registry correctly reported six persisted dependency lists that the fixture had left empty:

- body and rolling-gear materials each depend on the exact ordered BaseColor, MR/body-mask, and Normal texture packages;
- each of the four runtime meshes depends on its exact bound material package.

Those six lists are the only semantic difference. V012 freezes their exact paths and the corrected full-assets canonical hash `7E8A56991C48F8AEC017C0B4308E220729388A076ABC17C731F70405243B985B`. The 11 V009 package hashes remain the immutable runtime authority.

## AssetRegistry cache incident and guard

Although V011 did not mutate Content, UE 5.8 replaced the project `Intermediate/CachedAssetRegistry` cache and removed an orphan cache. V012 therefore freezes the current exact two-file cache snapshot, including paths, bytes, mtimes, and hashes. Its one validator process must receive `-NoAssetRegistryCacheWrite`; receipt, post-exit, and final verification require the cache snapshot before and after to be identical.

The guard is pinned to installed UE 5.8 `AssetDataGatherer.cpp` SHA-256 `9B62B0B7AFF852029CA82576570B5F9A9F3791E605667B1D20F0B7896511D6CC`: lines 201-212 parse the flag and disable gather-cache writes, while lines 238-249 force discovery-cache `NeverWrite`. Any cache-write or orphan-cleanup log token is fatal.

## Stable gameplay identity and revisionable art

The save/order/lineage ModelId is the stable `CAIRNWELL_2040`. It is not an asset path and does not contain a DEVELOPMENT or geometry revision. The current production recipe is separately identified as `CAIRNWELL_2040_DEVELOPMENT_RECIPE_V001`, and the current replaceable visual binding is separately identified as `Cairnwell2040Runtime_v001_V009ImportedGeometry`.

This model is approved for DEVELOPMENT game builds. It is explicitly revisionable and is not final-release art. Replacing the visual geometry later must create a new geometry authority/binding while preserving `CAIRNWELL_2040` save, order, and genealogy compatibility. The seam supports additional future vehicle ModelIds and production recipes without naming them around current package paths.

## Guarded topology

The offline contract reconstructs and validates its complete payload before any write. It pins:

- the exact V009 PASS import authority and 11 current package hashes;
- the immutable V010 stale pair and absent V010 result root;
- the immutable V011 contract/sidecar and exact consumed five-file failure run;
- the six exact persisted dependency lists;
- the exact two-file `Intermediate/CachedAssetRegistry` snapshot and installed engine source proof;
- the source, protected project, prepared-lane, and all-file destination closures.

The runner is Windows PowerShell 5.1 compatible and starts exactly one full `UnrealEditor.exe` validator on `/Engine/Maps/Entry`. It sets and restores `UE_SKIP_UBT_SDK_SETUP=1`, adds `-NoAssetRegistryCacheWrite`, rejects exact UBT command lines and fatal/cache-write log tokens, permits only the new Saved audit receipt/failure/log/summary files, and relies on the natural deferred `-ExecutePythonScript` exit. It launches no importer and performs no Content move.

The PASS marker is emitted only after environment restoration, zero-process/UBT gates, strict exit-zero and log checks, exact four-file post-validator closure, exact five-file final closure, exact receipt and summary binding, unchanged 11 package hashes, unchanged source/protected/lane evidence, and unchanged AssetRegistry cache.

## Offline-only preparation

No-write full candidate preflight:

```powershell
& 'C:\Program Files\Epic Games\UE_5.8\Engine\Binaries\ThirdParty\Python3\Win64\python.exe' -B 'C:\Users\greg_\Projects\LineBossCarFactory_Unreal 5.8\Scripts\prepare_cairnwell_2040_runtime_v001_recovery_v012.py' --dry-build
```

After an independent pre-cut audit returns GO, freeze the pair once:

```powershell
& 'C:\Program Files\Epic Games\UE_5.8\Engine\Binaries\ThirdParty\Python3\Win64\python.exe' -B 'C:\Users\greg_\Projects\LineBossCarFactory_Unreal 5.8\Scripts\prepare_cairnwell_2040_runtime_v001_recovery_v012.py' --acknowledgement FREEZE_CAIRNWELL_2040_RUNTIME_V001_RECOVERY_V012_ONCE
```

Contract creation authorizes no Unreal or UBT launch. The guarded validation command is one-use and must be executed only after a separate post-cut review confirms the exact frozen hashes, absent `Recovery_v012`, exact V011/current-package/cache closures, and zero Unreal/UBT processes:

```powershell
& 'C:\Users\greg_\Projects\LineBossCarFactory_Unreal 5.8\Scripts\run_cairnwell_2040_runtime_validation_recovery_v012.ps1' -Acknowledgement VALIDATE_CAIRNWELL_2040_RUNTIME_V001_V009_IMPORT_V012_ONCE
```
