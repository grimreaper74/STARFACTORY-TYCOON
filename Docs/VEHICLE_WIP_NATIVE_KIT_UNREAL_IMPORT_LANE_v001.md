# VehicleWIPNativeKit_v001 — Guarded Unreal Import Lane

Status: **static/offline preparation complete; intentionally waiting for the shared OneFactory Paint integration and combined build to settle.**

No Unreal Editor, UnrealBuildTool, map, Content package, Source file, Config file or save-game mutation was performed while preparing this lane. No whole-project baseline has been cut yet.

## Frozen source

- Source kit: `SourceAssets/Candidate/Vehicles/Cairnwell2040/VehicleWIPNativeKit_v001`
- Provenance: affirmative clean-room allowlist; factory-empty Blender procedural primitives/mesh code only.
- Roles: 9 composable vehicle layers + 7 pressed-panel archetypes.
- Authored LODs: 48 (LOD0/LOD1/LOD2 for every role).
- Fresh source roundtrips: 96 (FBX and GLB for every role/LOD).
- Finished aggregate: 24,720 / 12,500 / 4,332 triangles; LOD1 50.5663%, LOD2 17.5243%.

## Deterministic destination

`/Game/LineBoss/Native/Vehicles/Cairnwell2040/VehicleWIPNativeKit_v001`

This is a new native namespace. The lane refuses to run if it exists, never overwrites/reimports/deletes, and explicitly forbids the existing `/Game/LineBoss/Candidates/Vehicles` Meshy-era namespace and related candidate proxy namespaces.

The expected result is exactly 16 StaticMesh packages, each with three authored LOD source models. FBX materials/textures are not imported. Exact semantic slot names are preserved for the later native runtime-material integration; no Meshy-era material path is allowed.

## Gates

- Frozen source inventory, manifest, geometry, provenance and FBX/GLB roundtrip hashes.
- Exact per-LOD triangle counts, one UV channel, zero degenerates, centimetre bounds and shared zero pivot.
- Exact semantic material slots and per-LOD section mapping.
- Strict descending LOD chains and manual screen sizes `1.0 / 0.35 / 0.12` with auto-compute off.
- Nanite off.
- Zero simple/convex collision for all moving WIP; presentation components must set `CanEverAffectNavigation=false` when integrated.
- Exact target registry/disk inventory: 16 packages and no extra material/texture assets.
- Whole Source, existing Content, Config, maps and save games protected by a baseline cut only after Paint settles.
- A second distinct Unreal process performs read-only fresh-load validation and proves package bytes/hashes do not change on reload.

## Deliberately deferred sequence

After the shared Paint integration and combined build settle, and only then:

1. Cut the one-shot project baseline offline:

   `python -B Scripts/prepare_vehicle_wip_native_kit_unreal_import_baseline_v001.py --acknowledgement FREEZE_VEHICLE_WIP_NATIVE_PROJECT_BASELINE_AFTER_PAINT_SETTLES_V001`

2. Review the generated baseline and sidecar. Do not edit them.
3. Run the guarded two-process import lane:

   `powershell -ExecutionPolicy Bypass -File Scripts/run_vehicle_wip_native_kit_unreal_import_lane_v001.ps1 -Acknowledgement IMPORT_FROZEN_VEHICLE_WIP_NATIVE_KIT_V001_BASELINE_V001_ONCE`

Any failure preserves partial target packages and audit evidence for explicit review; there is no automatic cleanup or deletion.

