# Assembly Line Native Kit — guarded Unreal intake v001

Static-only preparation complete. No Unreal or UBT process was launched while creating or freezing this lane.

## Frozen scope

- Source authority: `SourceAssets/Candidate/AssemblyShop/AssemblyLineNativeKit_v001`
- Destination: `/Game/LineBoss/Candidates/AssemblyShop/AssemblyLineNativeKit_v001`
- Output: exactly 8 StaticMesh packages, with 24 authored LODs (8 × LOD0/1/2).
- Source gates: 8 original-procedural native assets, 24 strict monotonic LOD records, one UV channel per LOD, and all 48 FBX/GLB round-trips passing.
- Existing Body Shop presentation materials are bound by semantic slot name; the import creates no materials or textures.
- Nanite is disabled and manual screen sizes are `1.0 / 0.45 / 0.18`.

## Collision policy

Compact, non-enterable props receive one deterministic AABB box. Cockpit-install assist, marriage gantry, and EOL inspection arch retain their open working/vehicle portals through deterministic `Complex As Simple` collision. The fresh-process validator checks each asset against its frozen collision contract.

## Safety and proof

The lane requires both the destination namespace and every lane receipt to be absent. It refuses overwrite, reimport, deletion, map loading/saving, promotion, or runtime binding. A failed attempt preserves partial packages and evidence for explicit recovery and permanently consumes v001.

The baseline protects every existing Content file outside the new destination, the complete Source and Config trees, all campaign save games, and exact Press v913, restored Press, Body, Paint, and OneFactory maps. The validator runs in a second full UnrealEditor process, reloads all eight packages, checks triangles, UVs, bounds and pivots, material semantics, LOD screen sizes, collision, Nanite, package hashes, frozen source authorities, and a full protected-project hash inventory.

## Exact one-shot command

Run only after confirming no Unreal, ShaderCompileWorker, UBT, UAT, or packaging process is active:

```powershell
powershell.exe -NoProfile -ExecutionPolicy Bypass -File "C:\Users\greg_\Projects\LineBossCarFactory_Unreal 5.8\Scripts\run_assembly_line_native_kit_unreal_import_lane_v001.ps1" -Acknowledgement IMPORT_FROZEN_ASSEMBLY_LINE_NATIVE_KIT_V001_BASELINE_V001_ONCE
```

This command is intentionally not executed by the static preparation task. Once attempted, whether PASS or FAIL, do not run it again.
