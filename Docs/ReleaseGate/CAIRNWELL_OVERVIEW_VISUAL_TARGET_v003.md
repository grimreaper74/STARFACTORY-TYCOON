# Cairnwell Overview Visual Target

**Baseline:** 2026-08-13  \n**Revision:** v003 — actual player-camera measurement and PR005 exterior-service exclusion  
**Status:** player-facing visual direction; not a runtime-asset authority by itself.  
**Reference supplied by owner:** $source  
**Reference SHA-256:** $hash

## Intended player view

The game is judged from the normal high oblique overview camera, with the production-flow UI covering the lower part of the factory. Assets must therefore read at overview distance, not merely in close-up source renders. The owner clarified that this is a medium-detail target: it should look polished and mechanically credible, but not overloaded with close-up-only detail.

## Required visual read

- A bright, clean, high-density automotive factory: light neutral concrete, realistic but uncluttered lighting, tidy green routes and restrained yellow safety markings.
- Each station reads as a complete industrial cell: process hardware remains visible, framed by credible guarding/enclosures and surrounded by role-correct conveyors, stillages, controls and services.\n- At normal camera distance, prioritise five-to-ten recognisable forms per cell (main body, process mechanism, feed/exit, guard, cabinet/HMI, beacon, rails) over micro-detail. Use detail only where it improves silhouette, material separation or function.\n- No unnecessary external cable tray. Keep services internal or use short, physically credible conduit only where it is visibly required.
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


## Camera-derived production rule

The actual management camera is a 48-degree high-oblique overview. The normal populated process view has a 4,200 cm minimum and the default management camera uses an 11,000 cm boom; the lower HUD masks a substantial part of the screen. Treat this as a **medium-detail strategy**, matching the supplied reference:

- approximately five to ten readable forms per station: main body, exposed process mechanism, feed/exit, guard, cabinet/HMI, beacon and a small number of service modules;
- colour blocks and silhouette must read first; 15--40 cm contrast features such as vents, doors, roll zones, guard posts, a console and beacons read at this distance;
- bolts, text, fine cables and close-up-only trim are optional supporting detail, never the design driver;
- reject broad flat-grey shells, but also reject dense micro-geometry that makes a machine noisy or expensive without improving the overview read.

## PR005 external-service hold

Do not use the historical exterior roof-height cable tray `CW_PR005_V014_UtilityTray` or its dependent exterior service hoses/glands. It is 5.75 m long at roof height and is not required by the functional machine. Preserve the low engineering hydraulic routing; if a visible service connection is needed later it must be short, inboard and panel-terminated.`r`n## Evidence rule

No candidate is an improvement until it has a before/current/after pair from the same real player overview camera, including the production-flow UI framing where applicable.



## Comparator evidence

Reviewed project comparators: Car Manufacture Saved/Audits/UIUX/20260811_persistent_hud_slice/comparators/car_manufacture_user/01-running-factory-hud.png; Production Line Saved/Audits/UIUX/20260811_persistent_hud_slice/comparators/production_line_user/01-production-line-persistent-hud.jpg. Both support a compact, medium-detail, overview-first station standard.
