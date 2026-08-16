# Line Boss factory visual standard v001

Status: user-approved direction for new production work.

## One factory

Line Boss is one large, continuous automotive factory in the spirit of a readable factory-management game. Press, Body/Weld, Paint and Assembly are connected departments in the same building, not separate visual worlds.

Isolated prototype maps remain development and validation fixtures. They must emulate the common factory environment so that approved cells can later move into the combined factory without a visible change in lighting, scale, materials or camera language.

## Graphic direction

- The factory is a near-future 2040 facility: robot-rich, highly automated and digitally supervised. Stylised does not mean retro or primitive.
- Clean, stylised, low-poly industrial forms with slightly exaggerated silhouettes.
- Larger and more complete production scope takes priority over photoreal micro-detail.
- Every station, buffer, container, vehicle and process state must read at management-camera distance.
- Depth comes from production flow, logistics, faults, staffing, maintenance, quality, upgrades and the visible car journey.
- Use Cairnwell Green, Foundry Charcoal, Steel Grey, Warm White and functional Safety Yellow from `Docs/BRAND_IDENTITY_AUTHORITY.md`.
- Avoid dense decorative pipes, tiny fasteners, cable clutter, repeated micro-railings, dark roof voids and geometry that cannot be read during play.
- Keep fences, guards, doors, lights, controls and containers when they communicate gameplay or safety.
- Use articulated robots, AGVs, smart conveyors, vision gates, automated process equipment, maintenance/cleaning robots and readable digital HMIs to carry the futuristic identity.

## Factory-wide lighting

- One fixed exposure and colour-response standard across every department.
- Nominal overhead fixture temperature: 5000 K.
- Common sun, sky, tone mapping and material-luminance targets.
- Fixture intensity may scale only for ceiling height, covered area and fixture density; it must not create a different artistic look for each shop.
- Local process/task lights are allowed where their real function is readable, but they do not replace the common hall lighting.
- The approved Paint calibration `B_stylized` is the current master visual reference: six 1200 lm fixtures, sun 0.30, sky 0.20 and fixed exposure bias -0.50 in its isolated test hall.
- A lighting change is not accepted from property values alone. Fresh player-view captures must pass luminance, highlight-clipping, dark-void and material-readability gates.

## Asset policy

- Prefer deterministic procedural or hand-built modular assets in the established Line Boss style.
- Reuse the existing procedural Coil AGV authority at `SourceAssets/IndustrialKit/MaterialHandling/CoilAGV/Candidate_v001/` as a core material-handling style reference; do not replace it with a Meshy alternative.
- The active coil-inbound presentation uses the Line Boss unloading area and procedural Coil AGV. The detailed Coil FLT and lorry candidates are retired from the release path and retained only as archive/reference evidence.
- Meshy files may be retained as reference or archive evidence, but are not the production visual authority unless separately and explicitly approved.
- Production assets require stable pivots, semantic material slots, simple collision where gameplay needs it, management-view LODs and provenance records.
- Reuse modules such as conveyors, ovens, booths, guards and containers when their dimensions and gameplay role are truthful.
- Do not add inert production equipment merely to fill space. Visible WIP and containers must represent authoritative inventory or process state.

## World and camera composition

- Preserve long, readable process lines and the visible route from raw steel to finished car.
- Use floor paint, department bands, lighting and spacing to identify zones inside the shared hall.
- Keep the main car route, robot work envelope and important state changes visible from the management camera.
- Prefer a few strong silhouettes over many small repeated props.

## Release acceptance

A department is presentation-ready only when fresh real-player evidence proves:

1. It matches this shared visual and lighting standard.
2. Its gameplay-relevant stations and WIP are readable at management scale.
3. Process motion and state changes are visibly truthful.
4. LOD, collision and performance gates pass in a packaged Development build.
5. Save/reload reproduces the same authoritative production state without duplicate WIP.
6. Protected Press v913, campaign saves and already promoted assets remain unchanged.
