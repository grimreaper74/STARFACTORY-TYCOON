# Paint line native kit v001 — guarded Unreal intake

This lane imports the frozen, original-procedural Paint support kit into the
previously absent namespace:

`/Game/LineBoss/Candidates/PaintShop/PaintLineNativeKit_v001`

The lane is deliberately one-shot and fresh-only. It refuses a target namespace,
any previous v001 PASS or FAIL receipt, active Unreal/build processes, changed
source bytes, changed protected project bytes, or changed script/baseline hashes.
It never overwrites, reimports, deletes, loads/saves maps, or promotes assets.

## Exact asset contract

- 7 static meshes, each with authored LOD0, LOD1 and LOD2 (21 FBX sources).
- Strict triangle reduction and exactly one UV channel at every LOD.
- Floor-centred identity pivots, exact bounds, semantic native material bindings,
  manual screen sizes `[1.0, 0.45, 0.18]`, and Nanite disabled.
- Curing oven, pretreatment/wash, flash-off and quality-light tunnels use exact
  mesh collision so both longitudinal X-end portals remain open.
- The body skid uses exact mesh collision so its rails and wheel channels remain
  clear. The two compact service props use one deterministic box hull each.
- Source and visual receipts enforce the approved black-box direction: no spray
  robots, modeled process internals, windows, or side vehicle doors.

## Protected scope

The frozen baseline covers the project descriptor, complete `Source`, complete
`Config`, campaign `Saved/SaveGames`, all existing `Content` outside the new
target namespace, the five protected maps, the native Body robot/support kits,
the imported Assembly kit, and the SprayBoothRuntime_v002 namespace plus receipts.

## Execution

Only after the baseline and five script hashes are frozen, run exactly once from
Windows PowerShell 5.1:

```powershell
& 'C:\Users\greg_\Projects\LineBossCarFactory_Unreal 5.8\Scripts\run_paint_line_native_kit_unreal_import_lane_v001.ps1' -Acknowledgement 'IMPORT_FROZEN_PAINT_LINE_NATIVE_KIT_V001_BASELINE_V001_ONCE'
```

The runner performs a guarded NullRHI import process followed by a distinct,
read-only fresh-process reload validator. Any partial failure is preserved for
explicit review; there is no automatic cleanup or retry.

Before freezing, `freeze_paint_line_native_kit_unreal_import_baseline_v001.py
--check-only` executes the complete source/protected contract without writing the
baseline. After freezing, `--verify-only` rehashes the full baseline inventory.
