# Press Shop 2126 — Steam Candidate Plan

## Status and scope

This is the implementation plan for the isolated press-shop presentation
candidate. It is **not** a Steam-readiness claim and it is not permission to
alter the protected Builder Authority map.

- Protected: `LB_PressShop_BuilderAuthorityCandidate_v438.umap`.
- Active candidate: `/Game/LineBoss/Candidates/PressShop/PressShop2126_v003/Maps/LB_PressShop_2126_Steam_v003`.
- Direction: clean stylised 3D, near-future industrial forms, here extrapolated
  to 2126; robot-rich, automated, roofless, readable from a management camera.
- No wheeled cars, forklifts, or generic prop clutter. Materials arrive on
  coils; autonomous arms handle press tending and unloading.

The user-approved visual documents remain the authority:

1. `Docs/LINE_BOSS_FACTORY_VISUAL_STANDARD_v001.md`
2. `Docs/PressShop/PRESS_SHOP_QUIRKY_VISUAL_DIRECTION_v001.md`
3. `Docs/BRAND_IDENTITY_AUTHORITY.md`

## Process logic — credible now, extrapolated carefully

The 2126 line should make the existing real-world press-shop sequence more
legible rather than inventing science-fiction machinery with no process role.

1. **Coil reserve + active coil** — the user-approved bare and wrapped coil
   variants remain separate and visible.
2. **Autonomous straightening / feed** — use the supplied coil-free repaired
   Meshy feeder, leaving coils as separately placed project assets.
3. **Five distinct press stages** — draw/form, trim, pierce, flange/hem, and
   vision/outfeed. Each stage must have a clear colour and silhouette role.
4. **Robotic inter-press tending** — fixed-base robots communicate automated
   transfer without wheels or a forest of rails.
5. **Conveyor, inspection, stillage** — panels leave by powered outfeed,
   automated quality station, then organized stillage.

This ordering is grounded in current press automation: ABB describes an
end-to-end stack from front-of-line destacking through robot inter-press
automation, inspection, and racking; Schuler documents the same coil,
straightener, blank-loader and transfer sequence. The 2126 layer is an art
direction extrapolation, not a claim about future technology.

- <https://www.abb.com/global/en/areas/robotics/industries/automotive/press-automation>
- <https://www.schulergroup.com/INTERNET/major/download_center/broschueren_automation/download_automation/automation_dachbroschuere_e.pdf>
- <https://www.schulergroup.com/technologien/produkte/highlight_servopressenlinie/index.html?sLang=en>
- <https://www.siemens.com/en-gb/products/tecnomatix/>

## Asset strategy

### Use now

- Cleaned Meshy large forms only: `SquareMeshyPressTrain_v001` stages S02–S06
  and `MeshyCoilFeederNoCoil_v001`.
- Existing project coil variants and coil saddle.
- Existing verified powered conveyor, inspection cell, panel stillages and
  robot arm.
- Native Unreal only for broad architecture, painted floor zones, lighting,
  cameras, material overrides, and any future gameplay components.

### Do not add

- Another baked coil on a feeder.
- Placeholder cube machinery.
- Dense cables, railings, pipes, roof trusses, pendant controls, paper boards,
  forklifts, or wheeled vehicles.
- A giant overhead transfer rail until its silhouette and camera occlusion pass
  in-engine review. v030–v032 tested and rejected an obstructive version.

## Screenshot beats

The map is judged through four named in-engine cameras, not one broad overview.

| Beat | Camera | Must communicate |
|---|---|---|
| Whole line | `CAM v003 | compact whole-flow overview` | A compact, coherent press process from coil to output. |
| Press run | `CAM v003 | compact press hero` | The five different repaired Meshy press silhouettes and robotic automation. |
| Infeed | `CAM v003 | coil to first press story` | Bare active coil, wrapped reserve coil, feeder, first press. |
| Outfeed | `CAM v003 | inspection to stillage story` | Inspection, robot, reusable stillages, and completed-part destination. |

The first deliverable is an honest **in-engine review set**, not Steam artwork.
Each later pass should retain a separate receipt and image hashes; rejected
experiments remain disabled rather than being silently overwritten.

## Work sequence

1. **Stabilize the candidate map** — retain the v003 compact spacing; keep
   source Meshy/reused assets hash-unchanged; remove all rejected visual tests
   from current captures.
2. **Readability pass** — align every roller/input/output direction after a
   source-orientation audit, then tighten only gaps that do not break clear
   safety/service space.
3. **Machine identity pass** — use the exact Cairnwell green, warm white,
   steel grey, charcoal, safety yellow and status red roles. Avoid turning the
   full line one colour.
4. **Automation pass** — keep a small number of visible arms; add only one
   simple inter-press transfer silhouette if it remains clear in all four
   cameras.
5. **Environment pass** — roofless is accepted. Use wide painted zones,
   cream routes, an open horizon and distant, non-obstructive factory context.
   No new roof or truss forest.
6. **Native Unreal validation** — verify no WorldGrid material, collision/LOD
   state on accepted static meshes, candidate-only material overrides, no
   unbuilt-light warnings, and no regression to v438.
7. **Steam composition review** — select only the strongest three to five
   real in-engine shots after user review; run packaged and performance checks
   separately before any store claim.

## Lighting rule

Use the approved stylised palette and exposure as the visual reference, but do
not blindly spread the six-light calibration across a large open bay. A test
must use fixed exposure and visibly inspect coverage: prior high-output rect
light tests produced white pools and a D3D12 page fault. The current candidate
uses native open-air directional light plus skylight as a review rig only.

## Decisions already made

- **No Pro-generated map is a prerequisite.** The Unreal candidate can be
  built with the existing content and native tools. A professional concept
  sheet would be useful later for art direction, not required to continue.
- **No wheels.** Conveyors, fixed robots, coil storage, stillages and an
  automated line tell the production story more clearly for this space.
- **Do not chase micro-detail.** At the chosen camera distance, silhouette,
  colour grouping, process flow, light coverage and composition are the high
  value work.

## Acceptance gates

The candidate can advance only when all are true:

- Every screenshot is captured in Unreal from the candidate map.
- The line reads coil → feed → five presses → inspect → stillage without a
  legend.
- The actual repaired Meshy machines—not native substitute boxes—are visible.
- Bare and wrapped coils remain distinct and visible in the infeed beat.
- No roof, wheels, dense micro-clutter, WorldGrid material, or obstructive
  overhead silhouette appears in an accepted shot.
- Protected v438 and historical v002 hashes still match their recorded values.
- The user approves the art direction before work is described as Steam-ready.
