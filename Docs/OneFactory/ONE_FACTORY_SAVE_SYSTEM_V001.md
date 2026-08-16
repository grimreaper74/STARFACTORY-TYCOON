# OneFactory isolated save system v001

## Boundary

`ULBOneFactorySaveSubsystem` is the single save/load transaction boundary for
Moorcross Works OneFactory. Its fixed disk slot is
`LB_ONE_FACTORY_ISOLATED_SAVE_V001` at user index `0`. It never reads, writes,
migrates or deletes the historic `LB_PRESS_SHOP_CAMPAIGN`, Body prototype or
Paint prototype slots.

The v001 payload identity is:

- schema version: `1`
- save format: `LB_ONE_FACTORY_SAVE_V001`
- factory: `MOORCROSS_WORKS_ONE_FACTORY`

## Persisted authority

One payload contains exactly five presentation-free authority snapshots:

1. Press starter layout
2. Body/Weld starter layout
3. Paint starter layout and colour programme
4. Assembly starter layout and operation assignments
5. OneFactory production ledger, vehicle genealogy and runtime gates

The save schema has no actor, component, presentation-item, mesh, HISM or visual
proxy field. Presentation is reconstructed from committed layout snapshots.

## Fail-closed restore

Before mutation the subsystem requires exactly one tagged data authority and one
tagged visual-only presentation actor for each department, plus exactly one
production-ledger authority. It then captures and validates the current state as
the rollback boundary, validates the entire incoming payload, validates every
deterministic presentation contract and resolves all presentation dependencies.

Only after all preflight checks pass are the five data authorities restored. The
four existing presentation actors are then rebuilt from those committed layout
snapshots. Failure in any data or presentation step restores all five prior data
snapshots and rebuilds all four prior presentations. A failed incoming preflight
performs no mutation.

## Integrity rules

- Department layout validators remain the source of truth for topology.
- The production ledger rejects duplicate vehicle, build-order, material and
  evidence identities.
- A station WIP ID may occur only once across the whole factory.
- Every station WIP ID must name a non-terminal ledger vehicle in the matching
  department.
- Press, Body/Weld, Paint and Assembly must agree on the Cairnwell vehicle model.
- Layout commissioning flags must exactly agree with the ledger commissioning
  record.
- Missing or duplicate data/presentation pairs reject capture and restore.

## Automation contracts

- `LineBoss.OneFactory.Save.SchemaIsolationAndDuplicateIdentityRejection`
- `LineBoss.OneFactory.Save.ExactAuthorityPresentationPairsAndCapture`
- `LineBoss.OneFactory.Save.InMemoryRestoreAndPostCommitRollback`

The third test deliberately fails after authority commit to prove that both data
and all presentation pairs return to the previous coherent snapshot.

