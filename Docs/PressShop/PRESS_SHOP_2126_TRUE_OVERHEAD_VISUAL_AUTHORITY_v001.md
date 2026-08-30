# Cairnwell 2126 Press Shop — True-Overhead Visual Authority v001

Status: **candidate production authority for the 2126 Press Shop presentation lane**.  This document records the user-directed visual pivot without changing the simulation, protected authority maps, or release gates.

## Governing decision

The Press Shop remains the same management and production game.  Only its visual representation changes:

- Use separate, high-detail, true-overhead machine and cargo sprites in Unreal.
- Use an orthographic camera looking exactly down (`pitch -90°`) rather than the superseded oblique `-60° / 57.63°` candidate view.
- Preserve the real machine footprint, anchor, flow direction and station spacing.  Never enlarge one machine independently just to fill a screenshot.
- Keep machinery separable so presses, conveyors, robots, workpieces, beacons and effects can animate independently.
- Detail only surfaces visible from the game camera, but retain clear safety guards, motors, cable carriers, service panels and operator interfaces in the sprite art.
- The 2126 lane is roofless.  Roof geometry must not occlude the game camera.

This supersedes oblique-camera presentation rules for this candidate only.  It does not supersede gameplay authority, material-flow contracts or protected OneFactory maps.

## Camera and axis contract

- Projection: orthographic.
- Camera rotation: `(-90°, 0°, 0°)` in Unreal pitch/yaw/roll order.
- View direction: `-Z`.
- World `+Y`: inbound-to-outbound material flow and screen right.
- World `+X`: screen up.
- World `Z`: deterministic layer ordering only; sprites remain presentation-only and collision-free.
- All source sprite renders must use the same true-overhead view.  Perspective or three-quarter sprites are rejected.

The map may include several cameras, but changing camera width must not change actor transforms or physical dimensions.

## Scale and registration

- Each sprite plane is sized from its authored physical bounds, not by eye.
- Machine roots, cargo pivots and station centres must come from a manifest or an explicitly recorded candidate-integration decision.
- Moving cargo is authored as a separate layer with deterministic start/end transforms.
- Composite machine cards may animate internal state, but they cannot substitute for the independent wrapped coil, blank/panel, formed panel, hover pallet or outbound carrier required for material continuity.
- Adjacent sprite layers use small deterministic positive `Z` offsets only to establish render order.  The offsets do not represent physical height.

## Cairnwell 2126 palette

Structural colours are restricted to:

- Foundry Charcoal `#202428`
- Cairnwell Green `#1F4B44`
- Warm White `#F3F1E9`
- Safety Yellow `#F2C300`
- Steel Grey `#70777C`
- Signal Red `#C7352C`

Cyan is not a structural or painted-machine colour.  It is permitted only as a restrained, animated magnetic-transfer, scan or energy-flow effect that disappears when the mechanism is inactive.

## Saved-map composition

- Use a dark roofless factory deck, pale-green station zones, cream autonomous-flow lanes and safety-yellow station keys/arrows.
- Station labels must remain readable at the gameplay camera and identify inbound, coil preparation, S01–S07 and outbound flow.
- The complete material story must be visible: articulated carrier or AGV unload, wrapped-coil handling, storage, depack, preparation, press feed, S02–S06 forming, inspection, palletising and outbound panel pallets.
- Decorative support robots may use the autonomous lane, but cannot float off-route or replace production cargo.

## Shop and train scope

The immediate Steam candidate is one complete, playable, high-detail hero train from inbound coil to outbound panels.  It is the production template for the department.

The saved four-train department requirement remains open: the final full-shop composition must instance or author four readable train lanes (A–D), or receive an explicit user decision that a one-line shop is the final scope.  A single-line screenshot is not evidence that the full department is complete.

## Animation and effects

- Gameplay state comes only from the existing OneFactory ledger/coordinator.
- Required independent motion includes articulated vehicle steering, coil unload/transfer, strip or blank transfer, press states, formed-panel travel, robot pick/place, pallet accumulation and outbound carrier movement.
- Beacons and task lights use native Unreal components.
- Sprite-frame animation is appropriate for rollers, press contact, scans and robot poses.
- Effects must be state-driven and restrained: beacon glow, task-light pools, press-contact flash, scanner sweep and magnetic-transfer pulse.
- No presentation actor may own or duplicate WIP, inventory or production authority.

## Evidence gates

Source renders, Blender composites and transient Unreal show-only captures are art-direction evidence only.  Completion requires:

1. a saved isolated candidate map;
2. a deterministic PIE cycle from inbound coil through dispatched panel pallet;
3. visible independent cargo ownership and transforms throughout that cycle;
4. protected-map hash stability;
5. cold-load material correctness without manual material reassignment;
6. current Development and Shipping builds;
7. packaged 1920×1080 action screenshots and measured performance;
8. human visual approval of the final Steam evidence.

