# Line Boss one-factory integration plan v001

Status: architectural direction approved by the user; implementation follows the verified vertical slices.

## Outcome

The release game presents Moorcross Works as one continuous, larger-than-typical automotive factory. Press, Body/Weld, Paint and Assembly remain modular gameplay authorities, but the player experiences one connected floor, one camera language, one lighting system and one vehicle genealogy from raw steel to finished car.

## Preservation boundary

- Never overwrite Press Shop v913, the recovered full-factory reference, isolated Body/Paint validation maps, campaign saves or promoted assets.
- Build the combined factory into a new namespace and map.
- Keep the isolated maps as deterministic test fixtures for department-level automation and visual regression.
- A department enters the combined factory only after its own gameplay, save/reload, visual, LOD, performance and packaged gates pass.

## Premade and build-your-own contract

The campaign starts with a complete, functioning Moorcross Works layout so the player can operate a whole factory immediately. That premade factory is not fixed scenery or a second implementation path. It must be captured from the same build authorities, stable cell definitions, ports, recipes, logistics routes and save records available to the player.

- Every premade station remains movable, replaceable and upgradeable through normal player tools.
- Conveyors, buffers, robots, storage and AGV routes can be extended or rerouted without a map-specific process shortcut.
- Removing a premade station must affect flow exactly as removing a player-placed station would.
- The player can expand into reserved floor space, add parallel capacity and create a different valid layout.
- Save/reload stores the customised factory state, not merely the original map arrangement.
- A separate clean or lightly seeded sandbox start may reuse the same combined-factory shell and authorities.

The saved map may provide the hall, shared services and a validated starter layout. It may not own duplicate machine state, invisible production actors or decorative WIP that bypasses the build-and-save architecture.

## Configurable station assignments

The starter factory is planned around approximately 18 Body/Weld and 24 General Assembly process positions, but those numbers describe installed capacity rather than 42 permanently hard-coded operations. A production order owns an ordered operation plan; the player allocates compatible operations across the available stations on each line.

- A station exposes stable capabilities, tooling, input/output material families, capacity, cycle-time and quality limits rather than one immutable task name.
- Compatible assignments are selectable at runtime: for example, the same six-axis resistance-weld cell can perform sill weld, roof weld or respot work when its fixture, gun and recipe support that operation.
- Incompatible assignments fail before mutation: a paint booth cannot install wheels, a light inspection gate cannot perform structural welding, and a manual trim bench cannot accept a high-payload marriage operation.
- One station may receive several operations from the same vehicle plan when tooling and takt time allow it. Players may split a bottleneck operation across parallel stations or consolidate low-volume work into fewer stations.
- Changing an assignment recalculates required parts, tools, robots, staff, utilities, cycle time, upstream supply and downstream material state. It never silently skips a required operation.
- The premade Moorcross layout ships with a valid balanced assignment set, but every assignment is stored in the same save authority and remains editable through the normal management UI.
- Vehicle variants share compatible cells while retaining their exact bill of process, genealogy and quality evidence. A car leaves a department only after every required operation has been completed exactly once.

Station configuration therefore provides the player-facing depth; the visible station actor, ports, WIP ownership and save identity remain stable while its approved operation assignment changes.

Paint is intentionally the simpler exception. Its enclosed wet-process blocks, booths and ovens are black-box transformation stations: a body enters with an authoritative material/colour state and exits after the validated recipe timer with the next state. The player manages colour selection and batching, route capacity, recipe compatibility, changeover/cleaning cost, oven energy, filter/maintenance condition, defects and rework. There are no hidden decorative spray robots and no requirement to manipulate an invisible interior process. The starter Paint route may therefore use a compact pretreatment/ED block, sealer/primer block, colour booth, curing oven and inspection/rework loop while still providing meaningful throughput and quality decisions.

## Shared factory services

The combined map owns only factory-wide presentation and navigation services:

- the common hall shell, floor, roof and 5000 K lighting grid;
- the management camera and department navigation;
- main logistics aisles, AGV routes and service corridors;
- global signage, utilities and shared audio ambience;
- handoff boundaries between department authorities.

It does not duplicate machine process state or WIP ownership. Each department authority remains the single owner of its cells, queues, faults, process timing and local save state.

## Connected production route

1. Coil unloading and buffer using the Line Boss unloading area and procedural Coil AGV.
2. Press preparation, forming, inspection and panel stillages.
3. Body/Weld underbody, framing, closures and BIW inspection.
4. Paint pretreatment/ED coat, ovens, booths, curing and inspection.
5. General assembly, fluids, software, wheel alignment and end-of-line test.
6. Finished-vehicle dispatch.

Every transfer carries the exact authoritative vehicle/order/material/genealogy record. A visual car or container may exist only when the corresponding department or handoff authority owns it.

## Integration order

1. Finish and package the Body/Weld vertical slice with the procedural native robot and credible contact.
2. Finish and package the Paint ED-coat slice with player controls and the shared lighting standard.
3. Create a protected empty combined-factory shell in a new namespace.
4. Insert one verified department at a time through its build authority; do not copy transient map actors by hand.
5. Add exact cross-department handoff adapters and save migration tests.
6. Add shared logistics routes and procedural support vehicles.
7. Capture full-route packaged evidence from coil arrival to finished vehicle.

## Acceptance

The one-factory build is not accepted until a packaged Development run proves:

- no visible lighting or material jump between departments;
- one continuous player camera/navigation experience;
- exact WIP ownership at every handoff and no duplicate vehicles;
- starvation, blocked output, quality/rework and recovery across department boundaries;
- save, exit, restart and load reproduce the same full-factory state;
- management-view LOD/performance budgets pass with multiple simultaneous vehicles;
- Press v913 and every protected fixture remain byte-identical.
