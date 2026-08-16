# Press Shop engine and production-pipeline audit — 2026-08-10

## Decision

Keep Unreal Engine 5.8. Do not migrate the game to Godot or Unity.

The Meshy models are not intrinsically incompatible with Unreal. The isolated untouched S03 high-resolution source rendered correctly in Unreal, while the previously merged/reworked station showed visible large triangular facets. This proves the principal failure is asset selection, conversion, material/fallback configuration and uncontrolled revision ancestry—not the renderer.

Use a hybrid representation for detailed machinery:

1. `VisualMaster`: the untouched textured high-resolution static exterior.
2. `MotionProxy`: a small set of clean split parts for ram, die table, doors, transfer carriage and robot joints.
3. `CollisionProxy`: simple authored boxes/convex shapes, never complex Meshy collision.
4. `GameplayActor`: ports, capacity, state, animation and save identity; it does not depend on the visual mesh hierarchy.

Nanite is suitable for approved static visual masters. A non-Nanite fallback/LOD chain must exist for unsupported passes and moving/skeletal cases. Repeated floor, walkway, stand, barrier and route modules must use ISM/HISM rather than thousands of individual actors.

## Evidence from this project

- The player-buildable architecture already exists: press-train, storage, machine and infrastructure placement; 1 m/0.5 m grids; saved walkway and AGV-route segments; AGV route derivation from player-placed infrastructure; progression and campaign round-trip tests.
- Current project inventory is 526 map packages, 2,989 scripts, 152 candidate Blender files and 88 candidate GLBs. This revision volume makes accidental use of stale assets likely.
- The protected builder-authority map remains immutable. The active clean rebuild remains `/Game/LineBoss/Maps/LB_PressShop_RebuildFromLorry_v20260810_v913`.
- The untouched high-resolution S03 Walker renders smoothly in Unreal. The former merged/reworked press body is visibly faceted. Polygon reduction alone is not the complete cause; the bad source was already structurally altered.
- The new 105-part S03 split has no materials or UV layers. Transferring UVs across about two million polygons is slow and fragile. It is useful as a motion/pivot reference, not as the visual master.

## Evidence from installed factory games

Read-only inspection only; no code decompilation or proprietary asset extraction.

- `Car Manufacture` is a Unity game and uses Unity asset/addressable packaging.
- `Captain of Industry` is a Unity game and separates large asset bundles/maps from the executable.
- `Production Line` uses a lightweight data-driven presentation. Its installed data exposes simulation configuration separately from hundreds of DDS sprites and animation descriptors. This is consistent with a simulation that is not represented by one heavyweight animated 3D object per logical entity.
- The transferable lesson is engine-independent: simulation data, player layout and rendering are separate systems; repeated visuals are batched/instanced; visual motion can interpolate from lower-frequency simulation intent.

## Why the previous approach struggled

1. Map revision became asset authority. A visually newer map could silently contain older presses, robots or transforms.
2. Complete shop scenes were rebuilt before individual asset gates passed.
3. Textured and split Meshy outputs were treated as interchangeable, although split outputs often have no UV/material data.
4. High-poly visual geometry, animation parts and collision were expected to be the same object.
5. Automated reduction/merge steps destroyed silhouettes, normals or material boundaries without a compulsory side-by-side gate.
6. Lighting and exposure changes obscured geometry/material faults.
7. Too many presentation maps and scripts were retained as active candidates.

## Replacement workflow

### Gate A — reference

- Require consistent front, rear, left, right and elevated three-quarter views before any paid Meshy generation.
- Record intended real dimensions, material-flow axis, floor datum and moving groups.

### Gate B — source intake

- Preserve untouched generated/textured/split files with hashes.
- Audit bounds, triangle count, mesh count, UV layers, materials and packed images.
- Reject fused payloads, floating parts, melted silhouettes and contradictory views before Unreal.

### Gate C — Blender validation

- Render the untouched textured master in neutral lighting.
- Identify only the major moving groups from the split source.
- Author clean pivots and simple collision independently.
- Do not decimate the only retained visual source.

### Gate D — Unreal isolated proof

- Import into a fixed neutral comparison map.
- Test texture orientation, normals, Nanite on/off/fallback, scale, pivot and collision.
- Compare against the Blender authority before use in a train or shop.

### Gate E — gameplay package

- Bind approved visuals to a stable gameplay actor and catalogue entry.
- Prove placement, rotate, obstruction, connect, save, reload and delete/refund behavior.
- Press Train A is one placeable package assembled from S01-S07 and transfers; B-D are instances/configurations, not duplicated bespoke art.

### Gate F — clean-map integration

- Install only manifest-approved packages in the clean shell/example layout.
- Keep the release start state player-buildable; the populated shop is a tutorial/reference save, not baked authority.
- Run automated placement/route/save tests plus owner-visible screenshots from fixed cameras.

## Engine comparison

### Unreal Engine 5.8 — selected

- Best fit for retained high-resolution static machinery through Nanite and hybrid Nanite/non-Nanite workflows.
- Strong instancing, C++ gameplay, collision, automation and existing player-builder implementation.
- Migration cost is avoided; current placement, routing, progression and save tests remain usable.

### Godot 4.6 — useful comparator, not migration target

- Imports glTF/Blend scenes and creates automatic LODs; MultiMesh efficiently renders repeated objects.
- It has no direct Nanite-equivalent for retaining many unique two-million-triangle machines without an optimization plan.
- The same missing UVs, malformed geometry, bad pivots and over-complex animation hierarchy would still need repair.
- Use only for a small isolated visual comparison if an Unreal-specific material question remains after the neutral import gate.

### Unity 6 — capable, but no project advantage

- LOD Groups and GPU instancing are appropriate for factory games, as the installed Unity titles demonstrate.
- It still requires authored LODs/compatible meshes and would require rewriting the mature Unreal placement/save/routing code.
- Migration would delay the playable factory and would not repair source assets.

## Immediate production order

1. Freeze old presentation maps as evidence only.
2. Finalize the approved-asset manifest and reject ambiguous entries.
3. Complete one visually accepted, operational Press Train A package.
4. Prove Train A placement/save/connection in the clean shell.
5. Instance/configure B-D.
6. Populate and validate inbound lorry, unloading, stands/storage, prep cells and both AGV families.
7. Add player-painted walkways/routes and support robots/docks.
8. Package a vertical-slice build and profile it before expanding detail.

