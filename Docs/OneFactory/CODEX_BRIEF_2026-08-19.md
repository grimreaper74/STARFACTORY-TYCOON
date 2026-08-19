# Codex commission brief (2026-08-19)

Jobs where Codex's high-fidelity art authoring beats the pipeline work
Claude is doing. Claude holds the C++/runtime, placement pipelines,
tests and docs; nothing here touches Source/ or the placement scripts,
so both can work in parallel without collisions.

## Conventions (unchanged from Codex's own kits)

- Blender-native, metres, floor pivot at origin, FBX with
  FBX_SCALE_UNITS + bake_space_transform, SM_LB_* naming, separate
  brand-material slots.
- Palette variant D is now canonical (owner, 2026-08-19): emerald
  2F6E5F, graphite 3B4148, steel 8A9198, cream F3F1E9, safety yellow
  functional-only, signal red alarms-only. Tools/lb_model_kit.py has the
  exact values.
- Sources under SourceAssets/Candidate/<area>; Claude imports and
  places from there with the usual suite gates.

## Job 1 - Vegetation set (the known gap, highest value)

No tree, hedge or grass mesh exists in the project or the owned packs.
Wanted: SM_LB_Site_Tree_v001 (x3 variants), SM_LB_Site_Hedge_2000_v001,
SM_LB_Site_GrassPatch_v001. Stylised to sit with the flat-shaded brand
look, not photoreal foliage. Perimeter planting for a 740 x 400 m site.

## Job 2 - Texture/material upgrade pass over the authored machine fleet

Claude's 77 machines (SourceAssets/Candidate, WeldShop/PaintShop/
AssemblyShop/Site) are correct in form but flat palette colour. Codex's
press trains show the target: subtle wear, panel-line normal detail,
decals. Priority order: the ED line (dip tanks, PF track, carriers,
oven), the paint booths, the weld hemming/framing kit, the site pieces.

## Job 3 - Cairnwell 2040 colourways

The runtime supports PaintColourId per order; only Emerald visual
authority meshes exist (SM_LB_C2040_Emerald*VisualAuthority_v001).
Wanted: 3-4 more colourways of the body authority mesh (suggest: Alpine
White, Graphite, Signal Orange, Deep Blue) so contracts can demand
colours the player sees moving through the plant.

## Job 4 - Car transporter lorry

Dispatch compound shows finished cars leaving; wanted an articulated
car-transporter (tractor + twin-deck trailer, SM_LB_Site_Transporter_
v001) matching the approved inbound lorry's fidelity. Two will be staged
in the dispatch lanes.

## Job 5 - Machine animation rigs (stretch)

The press trains and the six-axis robots are static per-unit today.
Wanted where cheap: separated ram/slide meshes on one press train and a
spindle mesh on the sander/polisher heads so runtime motion can be added
later without re-authoring. Claude will wire any provided articulation.

## Explicitly NOT for Codex right now

Gameplay C++ (contracts/economy/save), placement scripts, tests, site
layout - all in-flight with Claude and collision-prone.
