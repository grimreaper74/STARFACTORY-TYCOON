# Kit dolly v002 — intake record

**Date:** 2026-08-29
**Status:** Validation-only — in engine, visible in captured frames; no
packaged journey.

## Provenance

| | |
|---|---|
| source | `SourceAssets/Spacecraft/KitDolly_v002/LB_KitDolly_v002.glb` |
| sha256 | `022ded33452a534d5039745a2fd109ae14acf0aaf7a1ce7f39f39e797fa2147b` |
| origin | commissioned 3D drop, 2026-08-29 |
| asset | `/Game/LineBoss/Candidates/Spacecraft/KitDolly_v002/LB_KitDolly_v002_joined/StaticMeshes/SM_LB_KitDolly_v002` |
| budget | **11,812 triangles**, declared and measured before import |
| size | 3.06 × 1.56 × 0.98 m, sitting on z = 0 |
| materials | `housing_pale`, `graphite_steel`, `amber_accent`, `brushed_aluminium`, `rubber_pad` |
| textures | none — nothing can carry baked text |

## Why this drop matters beyond the model

Meshy had been the only source of 3D, and it ignored the same written
instruction twice: told there are no humans on this factory floor, it
returned a kit dolly with a **push handle** and a gantry with
**handrails**. This drop was briefed with the same constraint and came
back with none of them — no handle, no steps, no ladder, no seats — and
every briefed feature present: four grapple hardpoints, a central lift
eye, corner guide notches, skid feet.

So the pipeline now has a second source that is **better at following
instructions**, which was the failure that cost those two drops.

## Two things that nearly went wrong quietly

**The import produced 122 separate static meshes.** The drop is
authored one object per bolt, strap and label — good authoring, and
unusable at runtime: 122 components per dolly, one dolly per station
per craft. Interchange was asked to combine and did not. The join now
happens in Blender first, where it is verified: triangles and all five
material slots were checked unchanged across it.

**The imported mesh reports 1,983 triangles, not 11,812.** That looks
exactly like an 83% geometry loss and is not one — Nanite is enabled,
and `get_num_triangles(0)` reports the *fallback* mesh while Nanite
holds the full detail. The import script's budget check originally
tested only for going OVER budget, so a genuine collapse would have
printed "WITHIN BUDGET" and been believed. It now checks both
directions and distinguishes the two cases by the Nanite flag, because
from the outside they are identical.

## What it replaced, and what that cost

The blockout it supersedes was a deck on **four wheels with a
drawbar** — the wheeled-cart idiom the owner corrected on 2026-08-28
("its a drone dolly thing"). Nothing here is handled by a person, so a
tow bar was wrong twice over.

**The cost is real and should not be forgotten:** the blockout sized
itself from the recipe, so a station fitting more parts grew a longer
dolly. The mesh carries its own crates, so that signal is lost until
the crates are either split out of the model or driven by per-instance
data. One mesh is placed per allocated component rather than one
stretched to fit, which keeps the count visible but not the size.

## Measured on the floor

At working distance the skids read as parts containers rather than
boxes. The chroma acceptance pass on the interior frame gives **3.55%
of frame above 60% saturation against an 8% limit** — a pass.

**The gantry crane fails it.** Sampled off the leg: `#B39927`, **S 0.78
/ V 0.70**, over the machine-amber ceiling of S 0.69 / V 0.66 on both
axes, on the largest machine in the hall. It is the one object on that
floor still painted by hand rather than from the palette, and once
craft carry customer liveries it is what they will be competing with.

## Not proven

No packaged journey. No ship was in frame, so the *"most saturated
pixel belongs to a hull"* half of the acceptance test could not be
evaluated. A Virtual Shadow Map warning — *non-Nanite marking job queue
overflow* — appears at close zoom; the owner confirmed it is triggered
by zooming rather than standing. It names non-Nanite meshes, so the
blockout geometry is the cause and each real imported asset reduces it.
