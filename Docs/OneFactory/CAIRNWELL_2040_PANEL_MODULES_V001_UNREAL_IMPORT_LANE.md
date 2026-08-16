# Cairnwell 2040 panel modules: guarded Unreal import lane v001

This lane is prepared for a future, separately authorized one-use Unreal 5.8
import. Freezing the contract and baseline does not launch Unreal, import
panels, change maps, or promote the model into gameplay.

## Exact source authority

Only the approved clean source is accepted:

- root: SourceAssets/Candidate/Vehicles/Cairnwell2040/Cairnwell2040PanelModules_v002
- manifest: MANIFEST_Cairnwell2040PanelModules_v002.json
- manifest SHA-256: 2FF38357BEC9FB890B2DCCCBC4C5E1728AB35D5BCB772F08811522540F6DF6E8
- production-audit SHA-256: F7C9CF062DBC1E5A4B5CBFE8B71A9BD79E1536D0523802F8F118562E9CC24762
- freeze-receipt SHA-256: B31900FE90D237952E788361309B747B8C7D831536034CBD23894408E0925B3D

Rejected crumpled previews, v001 panel passes, loose Meshy substitutes, and any
implicit latest selection are excluded. Source v002 maps explicitly to the
stable Unreal destination v001:

    /Game/LineBoss/Factory/OneFactory/v001/Vehicles/Cairnwell2040PanelModules_v001

The 11 ordered gameplay roles are HOOD_PANEL, ROOF_PANEL,
DOOR_FRONT_LEFT, DOOR_FRONT_RIGHT, DOOR_REAR_LEFT, DOOR_REAR_RIGHT,
FENDER_FRONT_LEFT, FENDER_FRONT_RIGHT, QUARTER_PANEL_LEFT,
QUARTER_PANEL_RIGHT, and TAILGATE_PANEL.

Every role has authored LOD0/LOD1/LOD2: 33 authored panel LODs in total. Each
LOD is byte-pinned as FBX plus GLB evidence and must retain exactly one UV,
zero degenerates, zero duplicate triangles, zero zero-length edges, zero
non-manifold edges, strict descending triangle counts, and the shared full-car
zero origin. Parts are never recentered. Bounds remain inside the fitted
456 x 188 x 156 cm car envelope.

## Exact runtime dependency authority

The lane accepts only the definitive runtime validation:

- recovery contract: Scripts/cairnwell_2040_runtime_v001_recovery_v013_contract.json
- contract SHA-256: 5D2B1929086AD33A8354ED0759509BCC6AFFEF8CD4E5BDE77A54546B53E95F12
- exact run: Recovery_v013/20260815T172802Z-1389784f
- result root: Saved/Audits/OneFactory/Vehicles/Cairnwell2040Runtime_v001/UnrealImportLane_v001/Recovery_v013/20260815T172802Z-1389784f

That run must remain the exact five-file closure:

| File | SHA-256 |
| --- | --- |
| fresh_process_validation_receipt_recovery_v013.json | 54A332C47FE71CE975EE666331882369855770C13B81CE6C195488A957127E44 |
| fresh_process_validation_recovery_v013.log | 75D0C27913C1F9F384BAF0E51FC7DDEC048B5F5C6184348D70F93829A5D3E32C |
| fresh_process_validation_recovery_v013.stderr.log | E3B0C44298FC1C149AFBF4C8996FB92427AE41E4649B934CA495991B7852B855 |
| fresh_process_validation_recovery_v013.stdout.log | 238F34F429471415B746C0AB381A497E6F2B2E883E9188A5AFB5329EBB2C5B7E |
| lane_summary_recovery_v013.json | D24261F1929D3B44EBF6526C148E044A403006DB738F52257A1A16D9CB432488 |

The receipt, summary, and current disk must agree on the exact 11 runtime
packages. This is not a latest-PASS search. Any additional, missing, renamed,
or changed V013 evidence fails closed.

Panels reuse only the persisted BIW galvanised, ED-coat, and player-paint
material packages from that runtime closure. They create zero textures and zero
materials. Each panel has one VehiclePanelSurface slot. The default is the
solid player-colour material; production stages can switch to the exact
galvanised or ED material. Nanite, simple/convex collision, and navigation data
are off.

## DEVELOPMENT visual policy

The stable model identity is CAIRNWELL_2040, with development recipe
CAIRNWELL_2040_DEVELOPMENT_RECIPE_V001. The current geometry is approved for
the game build as a DEVELOPMENT model. It remains replaceable before final
release. Gameplay code must depend on the stable model/panel contracts, not
hard-code these revision-specific meshes. No final-release visual lock is
claimed.

## Frozen baseline and protected surfaces

The Source/protected/lane snapshots recorded inside the V013 runtime receipt are
historical validation evidence only. They prove what V013 validated; they do
not replace this panel lane's current-project authority. After V013, the
separately authorized Paint presentation Source evolution continued. This
bounded migration accepts that intervening work once, then freezes the current
full project state in the new panel baseline. That adjudication is not future
drift permission: any unrelated later drift, including further Source drift,
fails closed.

The first attempted baseline v001 is preserved byte-for-byte as failed incident
evidence. It captured the Paint presentation actor while that authorized Source
work was still moving, and its immediate re-verification failed. It is
unselectable and cannot authorize Unreal. The only executable authority is the
distinct baseline v002 pair, which exact-pins the failed baseline v001 pair,
the observed post-cut Paint source, and the complete now-quiescent project.

Before Unreal can run, the lane freezes and reverifies:

- all 111 approved source-authority rows;
- the exact V013 five-file authority and 11 runtime packages;
- all existing Content outside the absent panel destination;
- complete Source and Config trees, the project descriptor, and SaveGames;
- every panel-lane script, test, and this document;
- the exact two-file Intermediate/CachedAssetRegistry snapshot;
- case-insensitive absence of legacy Intermediate/CachedAssetRegistry.bin
  and Intermediate/CachedAssetRegistry_*.bin.

The importer is allowed to write only the fresh panel destination and its new
run root. It cannot overwrite, reimport, delete, move Content, save maps, alter
Source/Config/saves, or mutate runtime packages. Partial failure evidence and
partial packages are preserved for explicit incident review; there is no
automatic cleanup.

## Process lifecycle gates

A separately authorized run uses exactly two sequential, fresh
UnrealEditor.exe processes:

1. import the 11 LOD0 meshes, append the 22 authored custom LODs, configure and
   save the exact 11 packages;
2. reload the packages read-only and prove persisted material dependencies and
   unchanged panel/runtime hashes.

Both processes bootstrap only /Engine/Maps/Entry. Both require
-NoAssetRegistryCacheWrite, UE_SKIP_UBT_SDK_SETUP=1, mapless startup,
-NoCompile, and natural -ExecutePythonScript shutdown. There is no explicit
Python quit_editor() call.

The runner requires exit code zero, empty redirected stderr, exactly one PASS
marker and natural LogExit: Exiting. marker in both primary logs, and the exact
UE 5.8 PreLoad/PostWrite zero-deletion cache-cleanup topology. Fatal, assert,
ensure, ModeManager, UBT/ValidatePlatforms/AutoSDK, cache-write, orphan
deletion, delete-failure, or legacy-cleanup tokens fail closed. Process
environment variables are restored exactly, including null values via
[System.Management.Automation.Language.NullString]::Value.

PowerShell never parses package maps or full receipts. Strict duplicate-key
Python validators own receipt, package, cache, log, PID, and final nine-file
closure checks.

## Guarded one-use command

Do not run this merely to verify the freeze. When the panel import itself is
separately authorized and Unreal/build processes are confirmed absent, use:

    powershell.exe -NoProfile -ExecutionPolicy Bypass -File "C:\Users\greg_\Projects\LineBossCarFactory_Unreal 5.8\Scripts\run_cairnwell_2040_panel_modules_import_lane_v001.ps1" -Acknowledgement IMPORT_FROZEN_CAIRNWELL_2040_PANEL_MODULES_V001_ONCE

The runner refuses an existing destination or audit root. A successful run
ends only after the independent verifier accepts the exact final nine-file
result closure. The contract/baseline freeze step intentionally does not run
this command.
