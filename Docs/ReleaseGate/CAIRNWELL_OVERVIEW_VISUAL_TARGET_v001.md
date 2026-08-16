# Cairnwell Overview Visual Target

**Baseline:** 2026-08-13  
**Status:** player-facing visual direction; not a runtime-asset authority by itself.  
**Reference supplied by owner:** $source  
**Reference SHA-256:** $hash

## Intended player view

The game is judged from the normal high oblique overview camera, with the production-flow UI covering the lower part of the factory. Assets must therefore read at overview distance, not merely in close-up source renders.

## Required visual read

- A bright, clean, high-density automotive factory: light neutral concrete, realistic but uncluttered lighting, tidy green routes and restrained yellow safety markings.
- Each station reads as a complete industrial cell: process hardware remains visible, framed by credible guarding/enclosures and surrounded by role-correct conveyors, stillages, controls and services.
- Palette hierarchy: warm-white fabricated bodies; graphite frames, motors and gearboxes; limited Cairnwell green service/ownership panels; yellow only for genuine guards/hazards; steel process contact; black hoses/cables.
- Machines need a strong silhouette and material separation from above. Tiny close-up-only detail is secondary to legible rollers, press tools, coil handling, robot cells, skids and flow direction.
- Status lights must be actual runtime-driven beacons, not only emissive pixels baked into a texture.
- Avoid flat-grey shells, toy-like all-over colour, random Meshy substitutions, unnecessary external cable trays, and clutter that does not read at normal overview zoom.

## Application order

1. Coil delivery / AGV / coil intake
2. PR005--PR010 press and blank flow
3. Conveyors, panel handling and stillages
4. Body weld
5. ED and remaining downstream work after press/weld

## Evidence rule

No candidate is an improvement until it has a before/current/after pair from the same real player overview camera, including the production-flow UI framing where applicable.
