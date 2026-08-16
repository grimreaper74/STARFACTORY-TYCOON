# Cairnwell PR-010 implementation authority

Status: active implementation interpretation, 2026-08-04.

## Authority order

1. Current owner decisions: fully automated Press Shop, control-room-only player, no worker NPC requirement, enclosed automated-machine presentation.
2. `Docs/MACHINE_ENCLOSURE_DESIGN_AUTHORITY.md`.
3. Remaining Machinery Pack `data/authority_and_assumptions.json` and CSV schedules.
4. Pack engineering specification.
5. Pro Sheet 03 visual reference.

Numeric authority overrides the visual sheet. The sheet defines intended exterior character and process readability, not permission to infer missing datums or certify real machinery.

## Fixed PR-010 facts

- World datum: `(1350, -2000, 0)` Unreal centimetres.
- Station local axes: `+X` across the four lanes, `+Y` along material flow and `+Z` up. Accepted rotation is yaw `-90 degrees`: local `+Y` maps to increasing world X. The fixed infeed shuttle centre at local Y `-3300 mm` therefore lands at world X `1020 cm`, matching the corrected PR-009 output side.
- Exactly four lane centres at local X `-4500, -1500, +1500, +4500 mm`; pitch `3000 mm`.
- PR-009 supplies identified blank stacks/carriers. PR-010 reserves, stores and routes those stacks to Press Trains A-D.
- The four train world datums remain TBC. PR-010 may terminate in a controlled vehicle-handoff apron and stable reservation interface, but must not invent press-train placement.

## Automated-gameplay interpretation

- Normal movement is by the infeed shuttle, carrier rollers and autonomous logistics vehicle/automated carrier handoff. A visible worker-driven forklift and pedestrian population are not required.
- The Pro `AGV/FLT` interface is implemented as an autonomous AGV-compatible controlled handoff. Exceptional forklift recovery is abstracted as an offline logistics action unless later owner authority explicitly introduces a visible vehicle.
- The recommended 1400 mm protected walkway is retained as a certified service/robot-access corridor and emergency-access allowance. It is not a player-walking route or a worker-NPC requirement.
- The controlled crossing is normally closed. It may open only with all four lanes and the infeed shuttle stopped, reservations locked and the crossing state proven clear.
- The player operates PR-010 through control-room HMI and fixed CCTV. Local HMI/identity remains physically present for believable machinery and camera evidence.

## Exterior and enclosure rule

PR-010 is not a clone of the compact PR-009 shell and is not wrapped in a redundant full perimeter cage. It is a four-lane connected storage/feed installation:

- Enclose the high-energy infeed shuttle, distribution drive and upper utility spine with the reusable Cairnwell modular enclosure language.
- Keep each carrier lane externally readable through controlled apertures, glazing and approved open-mesh side/end protection.
- Preserve clear stack identity pylons, reservation states, lane A-D colour/status hierarchy, external coordination HMI, E-stops, safety scanners, physical stops and recovery tow points.
- The outside silhouette and material-flow story must read from management CCTV while deliberate internal cameras show shuttle, rollers, stops and carrier transfer.
- Use Cairnwell Automotive / Moorcross Works / PR-010 identity only. Line Boss is prohibited in-world.

## First blockout gate

Before detailed geometry or native runtime work:

1. Preserve the measured yaw `-90 degrees` rotation and corrected PR-009-to-PR-010 handoff direction.
2. Build isolated dimensioned Blender/FBX blockout source with identity scale and semantic names.
3. Prove the four fixed lane centres, overall EST `14000 W x 8400 L x 3600 H mm` envelope, two stack positions per lane, infeed shuttle range and clear handoff apron.
4. Keep the quality-hold spur, HMI and service corridor outside moving/vehicle sweeps.
5. Import into an isolated Unreal candidate map parented from accepted PR-009 v096.
6. Capture fixed overview, infeed, lane/handoff and elevated views and inspect against Pro Sheet 03 before authoring detailed machinery.

No PR-010 asset is promoted by this authority document.
