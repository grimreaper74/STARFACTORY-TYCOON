# Gameplay v1 implementation plan (2026-08-19)

Builds the loop the owner accepted on 2026-08-19 (see
GAMEPLAY_RESEARCH_2026-08-19.md DECISIONS): sandbox spine with
contract-driven goals, flagship-contract finish line with post-win
escalation, soft failure, minimal defects v1, pause as a first-class
build mode. Grounded in a full survey of the runtime (this date): the
57-station runtime coordinator advances units via TickAutomaticFlow with
a durable ledger (LBOneFactoryProductionFlow.h); a complete double-entry
economy exists in ULBFactoryManagementSubsystem (integer pence,
idempotent Try* mutations) but nothing in OneFactory calls it; there is
no vehicle order/contract entity, no simulation clock, and the
player-facing pause key is dead.

Sequence - each phase is a small, testable, committable piece; the suite
must stay green after each:

- **P0 - Make pause real (bug fix).** ALBOneFactoryPlayerController::
  TogglePause calls ApplyTimeScale(0), which SetRuntimeTimeScale rejects
  (clamp [0.25, 4.0]); it never reaches the ledger's bLinePaused. Route
  ApplyTimeScale through ULBOneFactoryOperationsSubsystem::
  SetSimulationRate (rate 0 = durable pause; >0 = scale + unpause), and
  read pause state from the ledger, not the time scale. Test in the
  LineBoss.OneFactory.ActualPlayer bucket.
- **P1 - Simulation clock and timestamps.** Add SimClockSeconds to
  FLBOneFactoryProductionLedgerState (SaveGame), advanced once per
  TickAutomaticFlow call by the scaled delta; stamp units with
  CreatedAtSimSeconds / DispatchedAtSimSeconds. Everything later
  (deadlines, per-hour operating cost, KPIs) hangs off this. Ledger is
  versioned; bump and migrate.
- **P2 - Economy bridge.** On unit dispatch, OneFactory records revenue
  into ULBFactoryManagementSubsystem (TryRecordOrderRevenue keyed by
  UnitId - idempotent by design); a fixed operating cost per sim-hour
  charges via TryChargeOperatingCost. Embed FLBFactoryManagementSaveState
  into FLBOneFactorySaveState (schema bump v2) so money survives the
  OneFactory slot. The management subsystem is deliberately reused, not
  reinvented - it is tested and integer-exact.
- **P3 - Vehicle contracts.** New FLBOneFactoryVehicleContract
  {ContractId, VehicleModelId, Quantity, PricePerVehiclePence,
  DeadlineSimSeconds, MinimumQuality, State} stored on the production
  ledger; dispatch settles the oldest open contract; completion pays
  through the P2 bridge; a starter chain of 3 contracts seeds the
  sandbox. Flagship contract + escalation chain follow as data, not code.
- **P4 - Soft failure.** Cash-floor warning thresholds surface as HUD
  alerts; below zero offers an emergency contract (price penalty) rather
  than game over; hardcore toggle deferred.
- **P5 - Defects v1.** Decay Condition01 on commissioned robots per
  completed cycle (the field exists and is save-backed but never
  decays); worn robots raise defect probability at the two quality
  gates; rework path already exists in the runtime (ReworkRequired /
  rework stage).
- **P6 - HUD strip v2.** Cash, sim clock, active contract
  (progress/deadline), and pause state on ALBOneFactoryProductionHUD -
  data all available from P1-P3.

Out of scope for v1: multiple vehicle models, research tree, staffing
(lights-out), map expansion, the frozen-presentation re-version
(documented debt).
