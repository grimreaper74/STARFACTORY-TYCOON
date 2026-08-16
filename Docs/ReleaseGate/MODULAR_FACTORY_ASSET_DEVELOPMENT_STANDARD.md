# Modular factory asset development standard

**Status:** Development authority  
**Applies from:** 2026-08-13  
**Scope:** Robots, tools, fixtures, conveyors, process machines, WIP, factory
architecture and reusable dressing used by Line Boss.

This standard converts lessons from the current Line Boss pipeline and a
metadata-only review of a comparable factory-management game into a practical
release workflow. It does not approve an asset by itself or supersede the
promotion states in `ASSET_PROVENANCE_AND_PROMOTION.md`.

## 1. Decision

Line Boss will use **modular, functionally split factory assets assembled into
dense, coherent production cells**. Visual quality will come from silhouette,
materials, lighting, animation, process state and purposeful repetition rather
than raw triangle count.

The project will not:

- ship raw million-triangle generated meshes;
- merge functional movers into one static mesh;
- require unrestricted six-axis robot placement or path programming;
- create a unique material/texture set for every joint or repeated module;
- treat an import, isolated render or passing unit test as release approval;
- retain staging meshes, rejected branches and obsolete versions in a shipping
  cook merely because they exist in Content.

## 2. What changes and what remains

### Changes from this point

- Reviews prioritize the **game-camera result**, draw calls, materials, motion
  and cell composition before additional geometry.
- Repeated machinery receives an explicit **hero/focus tier** and
  **management-view tier** through authored LODs and screen-size policy.
- Restrained normal detail, roughness variation, readable joint contrast,
  protected safety colours and decals are part of the asset—not optional polish.
- Cells use shared guarding, controls, cabinets, services, platforms, lighting,
  conveyors and status equipment.
- Every moving assembly declares pivots, axes, limits, tool sockets and authored
  process poses before runtime selection.
- Triangle counts are recorded with material sections, component count, texture
  memory, collision policy and expected instance count.
- Runtime and package captures prove focused and normal management distances
  under intended factory lighting.

### Preserved decisions

- The current Body Shop robot pattern remains valid: rigid Base and J1-J5 meshes
  beneath authored pivot components, with an interchangeable tool flange and
  validated process poses.
- Fixture-based robotic cells remain the player-facing build unit. Players choose
  compatible robots, tools and authored mounting slots; they do not perform robot
  CAD or unrestricted path programming.
- Gameplay identities, ports, saves and working promoted assets are not changed
  merely to satisfy this art standard.
- Existing high-detail robot LOD0 geometry may remain as the focus-camera tier if
  it passes material, silhouette, draw-call and performance gates.

## 3. Evidence behind the decision

A read-only metadata review of a representative heavy handling robot in a
comparable game found a transform-driven assembly rather than a skeletal mesh:

- 28 transform objects;
- 13 rendered components using 9 unique rigid meshes;
- approximately 3,268 normally visible triangles;
- one material section per mesh and three shared materials;
- authored pickup, middle, neutral and job target transforms;
- a custom two-link procedural solver;
- no animation clips, detailed collision or LOD group on the inspected prefab.

Its presentation depends on clear pivots, shared 1K/2K PBR materials, readable
silhouette and dense cell context. No geometry, texture or proprietary artwork
was extracted or copied during this review.

The current Line Boss Body Shop arm is more capable and substantially heavier:

| Assembly | LOD0 | LOD1 | LOD2 | Sections |
|---|---:|---:|---:|---:|
| Robot Base and J1-J5 | 85,685 | 39,821 | 15,325 | 8 |
| Robot with 8-cup handling tool | 88,381 | 41,973 | 17,205 | about 12 |
| Robot with current C-gun | 105,572 | 48,538 | 18,866 | about 9 |

The hierarchy and LOD ratios are useful. The main weakness is that tens of
thousands of triangles currently resolve through broad cream/black material
regions, so much of that geometry does not improve the management-camera image.
The first response is better surface treatment, contrast and LOD use—not more
polygons.

## 4. Modular construction contract

### Robots

A configurable robot must be built from rigid semantic links:

```text
Actor root
|- Base presentation
`- J1 pivot
   |- J1 presentation
   `- J2 pivot
      |- J2 presentation
      `- ...
         `- Tool-flange pivot
            `- Interchangeable tool presentation
```

Each moving link must have:

- one authoritative local pivot and axis;
- minimum and maximum angle or travel;
- a stable semantic name;
- identity-relative presentation under its pivot wherever practical;
- no baked transform that silently changes the authored axis;
- explicit Home, Acquire, Process, Retract and Fault-safe poses as applicable;
- a stable tool-flange socket and payload datum;
- reach and sweep evidence for every permitted cell mounting slot.

Use rigid components and procedural interpolation for current factory robots.
Use a skeletal mesh only when deformation, animation tooling or component count
provides a measured benefit—not merely because it is a familiar workflow.

### Tools and fixtures

- Tools are separate assets attached at a stable flange; they are not fused into
  the reusable arm.
- Vacuum tools expose every cup contact socket and configurable arm pivot.
- Welding tools expose flange, electrode/contact and service datums.
- Fixtures separate functional movers: clamps, locators, slides, gates and
  replaceable tooling. Decorative fasteners do not become actors.
- A cell provides authored robot slots and process poses. Safety fencing,
  interlocks, controllers, cooling, extraction and standard services assemble
  automatically from the configuration.

### Repeated modules

Rollers, fence posts, lamps, rails, cable supports, fasteners and repeated service
parts use instancing or a deliberately batched assembly. Repetition is not hidden
by creating duplicate mesh packages.

## 5. Provisional performance budgets

These are review thresholds, not automatic approval. A measured exception must
state the player-visible benefit and representative-scale cost.

| Asset class | Suggested LOD0 | LOD1 | LOD2 | Typical sections |
|---|---:|---:|---:|---:|
| Small repeated prop | 250-5,000 | 40-60% | 10-25% | 1-2 |
| Conveyor/service module | 1,000-12,000 | 40-55% | 15-25% | 1-3 |
| Repeated/distant robot and tool | 15,000-30,000 | 40-50% | 15-25% | 2-6 |
| Focus-camera robot and tool | 60,000-110,000 | 35-50% | 15-25% | 4-12 |
| Fixture or process machine | 20,000-60,000 | 40-55% | 15-25% | 2-8 |
| Complete production cell | 60,000-150,000 | measured | measured | measured |
| Complete BIW/player WIP | 35,000-60,000 | 40-50% | 15-25% | 2-6 |

Additional rules:

- A repeated robot may retain a hero LOD0 but only at an inspection/focus screen
  size, not throughout the ordinary full-factory view.
- Draw calls and material sections are as important as triangles. Record both.
- Consider Nanite for suitable static structures only. Robots, tools, WIP and
  repeatedly changing components use measured conventional LODs unless a later
  engine test proves a better policy.
- Collision uses simple authored shapes or gameplay volumes. Presentation
  triangles do not become collision by default.

## 6. Materials and textures

- Use shared Line Boss masters and semantic instances for painted metal,
  graphite mechanisms, raw/machined steel, rubber, glass, safety yellow, warning
  lights and player livery.
- Most assets use 1K/2K textures, trim sheets, packed masks and decals. Unique 4K
  textures require a close-view benefit and memory evidence.
- Painted surfaces need enough normal/edge and roughness response to read under
  factory lighting. Flat colour on dense geometry is not a release material.
- Protect tools, cables, lenses, labels, hazard colours, emergency controls and
  bare functional metal from player-colour replacement.
- Prefer few stable material sections. Do not split a mesh for colour variation
  that a mask, vertex colour or decal can provide.
- Validate instanced-static-mesh material usage for HISM/ISM consumers; editor
  appearance alone is insufficient.

## 7. Generated-source policy

Meshy and other generated outputs are source authorities, not runtime assets.
Before Unreal selection they require:

1. immutable original, task/reference record and SHA-256;
2. role and visual review before further generation or credit spend;
3. scale, axes, floor datum and functional-envelope approval;
4. semantic split or clean modular derivative;
5. removal of fused unwanted subjects and unusable internal geometry;
6. asset-specific retopology/decimation rather than a blanket target;
7. UV/material cleanup and retained rights evidence;
8. pivots, sockets, collision policy and three LODs;
9. clean-scene FBX/GLB round-trip validation;
10. guarded import into a fresh candidate namespace.

Known failure patterns that must not recur:

- accepting a one- to three-million-triangle preview as runtime art;
- trusting automated segmentation when major functional groups remain fused;
- mixing geometry and textures from similar but non-matching branches;
- assuming FBX scale conversion without checking imported centimetre bounds;
- treating zero-area faces removed by Unreal as unexplained source drift;
- leaving partial or temporary LOD staging assets in a runtime namespace;
- importing WorldGrid/default materials and calling the geometry finished;
- repainting slot zero while other semantic slots retain fallbacks.

## 8. Cell composition and visual quality

A production cell is reviewed as a gameplay object, not a hero mesh on a blank
floor. It should normally include:

- one unmistakable process silhouette;
- appropriate robots/tools or process movers;
- fixture and WIP presentation;
- guarding and controlled openings;
- HMI/controller and status indication;
- believable services, extraction or utilities where relevant;
- entry/output handling and readable connection points;
- maintenance access and safety clearance;
- state-driven lighting, audio and movement.

The normal management-camera capture must show why the cell exists and what state
it is in. A close-up render cannot compensate for an unreadable factory view.

## 9. Promotion and validation workflow

Every family follows the existing promotion states:

`Authority preserved -> Source candidate -> Unreal candidate -> Runtime selected -> Packaged verified`

Minimum evidence:

1. **Source:** hashes, provenance, dimensions, semantic inventory, pivot/socket
   contract, budgets and clean round-trip.
2. **Unreal:** exact paths, bounds, LOD triangles, material slots, collision,
   Nanite policy and package inventory after fresh reload.
3. **Runtime:** no hidden primitive/default-material fallback; correct hierarchy,
   poses, tool assignment, feedback and collision/navigation policy.
4. **Visual:** focused and management-camera captures with actual floor, lighting,
   surrounding cells and UI; no capture hack presented as a runtime default.
5. **Performance:** representative cells/robots with CPU, GPU, memory, draw-call
   and texture-pool evidence.
6. **Package:** fresh package load, motion, interaction, save/reload and exact
   cooked-asset manifest.

An asset may be technically valid and still fail the visual gate. An attractive
Blender render does not prove Unreal materials, scale, LODs, runtime selection or
packaging.

## 10. Required handover

Each release candidate records:

- role and stable asset ID;
- source authority and rights evidence;
- exact source/export/Unreal paths and hashes;
- centimetre bounds, orientation and floor/root datum;
- hierarchy, axes, limits, sockets and authored poses;
- LOD triangle and section counts;
- materials, texture sizes and protected livery regions;
- collision/navigation/Nanite/instancing policy;
- expected maximum visible instance count;
- runtime binding and fallback behaviour;
- tests and visual/performance/package evidence;
- explicit remaining limitations.

Unknown fields are recorded as `TBC` and the asset stays below packaged verified.
Never infer completion from `Final`, `Approved`, `Production` or `Runtime` in a
filename.

## 11. Immediate application

- Keep the Body Shop Base/J1-J5/tool hierarchy and authored fixture-slot poses.
- Keep J4 locked until its mechanical seam and clearance are rebuilt and tested.
- Improve cream/black surface response, joint contrast and protected detail
  before adding geometry.
- Evaluate earlier LOD transitions for ordinary management views while retaining
  current LOD0 for focus views if performance passes.
- Remove duplicate skid/underbody presentation so static fixture scenery and live
  WIP cannot occupy the same transform.
- Apply the modular construction and promotion workflow to Paint, then Assembly,
  instead of creating new monolithic generated lines.
- Build a shipping manifest excluding rejected sources, historical versions,
  validation maps and temporary LOD staging packages.

This document changes the development and acceptance method. Individual assets
still require reviewed implementation and current evidence before any runtime or
release claim.
