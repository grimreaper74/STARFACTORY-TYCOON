# OneFactory automatic runtime coordinator v001

## Release contract

`ALBOneFactoryRuntimeCoordinator` is the first presentation-free automatic
production authority for Moorcross Works. It resolves exactly one Press,
Body/Weld, Paint, Assembly and production-ledger authority and refuses to run
when any authority is missing or duplicated.

The configured physical route is always rebuilt from the live layout records:

- 7 Press responsibilities in the authored material-route order;
- 18 Body/Weld positions sorted by `LinePosition`;
- 8 Paint responsibilities in the authored skid-route order;
- 24 Assembly positions sorted by `LinePosition`.

That is exactly 57 occupied positions. Body programmes and Assembly operations
remain assignments, so a reassigned duty follows the station selected by the
player. An intentionally empty configurable position is still traversed as an
explicit pass-through rather than disappearing from the physical line.

## Durable state and save/load

The production ledger now persists, per `UnitId`:

- physical station cursor and completed-station count;
- elapsed and required deterministic cycle time;
- current station and configured assignment identity;
- the 57-position route topology fingerprint;
- explicit started/stopped state.

These are `SaveGame` fields in `FLBOneFactoryVehicleUnitState`. The existing
OneFactory save root therefore captures a mid-cycle vehicle without storing a
mesh, actor or visual WIP proxy. Runtime reservation changes deliberately do not
increment layout presentation revisions; presentation-only actors remain
coherent because WIP is not part of their visual contract.

On restore, station order, transforms, assignments, programmes and cycle times
must reproduce the saved topology fingerprint. Any drift fails closed before
elapsed time or reservations can move.

## Transaction and operating gates

Every transfer preflights candidate layout snapshots and the candidate ledger,
then moves the same `UnitId` from exactly one source reservation to one empty
target reservation. A failed layout or ledger commit restores all five prior
authority snapshots. Cross-department duplicate reservations, station
collisions, terminal WIP and a ledger/station disagreement are rejected.

Pause and department faults freeze elapsed time. An output block permits the
current station cycle to finish but holds the unit at its source reservation.
Uncommissioned or faulted target departments block handoff. Body, Paint and
end-of-line inspection positions hold at 100 percent until a quality result is
submitted. Rework resets the same inspection cycle to zero without changing
the `UnitId` or creating another WIP record.

Each completed physical station adds deterministic genealogy evidence tied to
the configured assignment. The coarse stages from inbound coil through
finished vehicle remain visible, and the final physical dispatch increments
completed and dispatched counts exactly once.

## Native UMG seam

The coordinator exposes create, start, per-unit tick, automatic all-unit tick,
quality, rework, route inspection, runtime validation and vehicle-status APIs.
`FLBOneFactoryRuntimeVehicleStatus` is sufficient for native UMG progress and
quality-hold controls and contains no presentation reference.

## Focused automation

`LBOneFactoryRuntimeCoordinatorTests.cpp` statically defines coverage for:

- all 57 physical stations and all 18 coarse semantic stages;
- a player-reassigned Assembly operation and its pass-through source;
- pause, fault and output-block behaviour;
- Body, Paint and EOL quality holds plus Body rework;
- completed/dispatched counters and genealogy evidence;
- mid-cycle whole-factory save-schema validation and restore;
- exactly one reservation after restore;
- duplicate-WIP, topology-drift, missing-authority and duplicate-authority
  rejection.

This tranche does not touch PlayerBuilder, HUD, GameMode, maps, Content,
Config, disk saves or any presentation actor.

