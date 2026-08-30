# How Car Manufacture builds stations and conveyors — mined reference v001

Status: research reference (owner asked 2026-08-26: "did you get
anything from car manufacturer on how stations and conveyors are
made?"). Source: identifier mining of the installed Assembly-CSharp.dll
(read-only). This maps their construction model onto Line Boss.

## Their model, from the code names

1. **Conveyors are laid from typed ELEMENTS via a factory**:
   `ConveyorElementStart / End / Line / TurnLeft / TurnRight /
   CrossInput / CrossOutput`, built by `ConveyorElementsFactory`. The
   player lays track piece by piece - a start cap, straights, turns,
   crossings, an end cap.
2. **Pieces stick and segments merge**: `TryToStickToConveyorSegment`,
   `CreateConveyorSegment`, `MergeConveyorSegment` - placing a piece
   against an existing run absorbs it into one segment; the walkable
   path is derived (`CalculateAndSetConveyorPath`,
   `ConveyorPathService` with waypoint DTOs).
3. **Stations are NODES attached TO the conveyor**:
   `AssemblyConveyorNode`, `AddConveyorNode`,
   `AddConveyorNodesAsInput/AsOutput`. A conveyor has a MAX STATION
   COUNT that is itself upgradeable
   (`ChangeConveyorMaxStationsCountGameAction`), and node work scopes
   hang off the node (`ChangeAssemblyConveyorNodeWorkScope`).
4. **Products ride the path**: `ConveyorProduct` moves along the
   conveyor, raising `ProductEnteredNodeEvent` /
   `ProductEnteredCenterOfNodeEvent`; movement can pause/block/resume
   (station work holds the product at the node).
5. **Problems are surfaced, not silent**: `CONVEYOR_END_NOT_SET`,
   `ConveyorOutputNotSetProblemSystem` - an unfinished conveyor is a
   named problem the player must fix (our fail-closed toast language).
6. **Speed is upgradeable** (`ChangeConveyorMaxSpeedGameAction`), and
   placement has a live GHOST (`ConveyorPreviewService`,
   `ConveyorLinkPointView` showing valid link points).

## Mapping to Line Boss (proposed build experience v2)

- The production line becomes a LAID TRACK: grid-snapped conveyor
  elements (start / straight / turn / end), adjacent pieces
  auto-merging into one line; the ship's route IS the track path
  (replacing the derived stage-order route).
- Line stations ATTACH to the track as nodes (drag a station onto the
  run; it claims a track span). Max-nodes-per-line as an upgrade.
- Ships are the conveyor products: they move along the path and hold
  at nodes while the station's drones (worker slots, already built)
  do the fitted work (allocation, already built).
- An incomplete track (no end at the runway) is a named problem, not
  a silent no-op; the ghost preview shows valid link points.
- Belt speed research upgrades the line's travel speed (the belt Mk2
  research content slot already reserved).

## Fit with what already exists

Already aligned: grid snap, ghost with verdict tint, fail-closed
refusals, supply belts as auto-routed cost-per-metre runs, premium
belt furniture visuals, drone slots + allocation on stations. The NEW
work is the element-based track authority (lay/merge/path-derive) and
routing ships along it. Recommended as its own milestone after
allocation-driven consumption.
