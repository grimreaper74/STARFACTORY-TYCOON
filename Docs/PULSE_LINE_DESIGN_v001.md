# The pulse line, v001 (2026-09-02)

Owner, 2026-09-01 evening: "after your happy with this can you do the
pulse line or before if its better?" This is the design that the
implementation follows. It rests on three decisions already taken:

- The line uses **military-aircraft PULSE mechanics** with Car
  Manufacture interaction (owner, 2026-08-28): a craft occupies a
  station, the work takes its stop time, and nothing releases work
  that is not finished.
- The craft is **lifted between stations by a portal gantry crane on
  full-length floor rails** (2026-08-28, orientation corrected
  2026-08-29). The conveyor is decoration.
- **How many cranes is OPEN** (owner, 2026-08-29: "1 crane does all
  work, will have to test each"). Both "one crane per gap" and "one
  crane for the line" must be playable so they can be compared.

## What the line does today, and why it is not a pulse line

`ALBSpacecraftRuntimeCoordinator::TickProduction` accrues a cycle
timer per unit and advances each unit **on its own clock** the moment
its stop is over and the next station is free (furthest-first). Up to
one craft per station can be mid-line, all moving independently.
There is no pulse, no crane in the simulation, and the presenter
slides each craft for the last 20% of *its own* cycle. The gantry
count is a console variable (`LB.Spacecraft.CranePerGap`) consumed
only by the hall decoration.

An independent-advance line is a continuously-moving car line with
the belt removed. The stop times are right; the release rule is not.

## The pulse

A **pulse** is the moment every craft on the line moves one station
forward together, and a fresh craft enters the head station.

1. Every occupied station runs its stop. A unit's `CycleElapsedSeconds`
   fills as now. A station whose unit is done **holds** its craft; it
   does not release it.
2. When **every** unit on the line has finished its stop (and any
   in-place rework is over), the line is *pulse-ready*. The slowest
   station sets the pace, which is exactly the aircraft rule.
3. The pulse is a **crane move phase** with a duration. The cranes
   carry craft from the tail backwards: the unit at the last station
   dispatches (or parks in Testing, as today), then each craft is
   lifted one station forward. A craft in the move phase is *in
   transit*: its station is the destination, its timer is zero, and
   the presenter draws it under the crane.
4. When the move phase ends, a new unit is admitted at the head if a
   contract demands one and the WIP cap allows, and every station's
   stop starts again.

Component consumption, defect accrual, rework and the hover test keep
their current places in `TryAdvanceAssignment`; only the *release*
rule changes from "my stop is over and the next station is free" to
"the line pulsed".

### The cranes are the pace of the pulse

The move phase lasts

    ceil(craft to move / cranes) x CraneTripSeconds

so one crane on a four-craft line makes four trips in series and the
pulse takes four times as long as with one crane per gap. That is the
throughput constraint the owner named as a real upgrade axis, and it
is what makes the comparison he asked for a matter of building
cranes rather than flipping a cvar:

- **Gantry crane** becomes a purchasable line item in the BUILD tab
  (`GantryCrane`, cost to be tuned, no floor footprint - it rides the
  rails that the hall already lays full-length). The count is capped
  at `stations - 1`; the first crane is part of commissioning a line
  (a line with no crane cannot pulse, and the refusal says so).
- `LB.Spacecraft.CranePerGap` is retired. The presenter spawns one
  crane mesh per crane owned and animates each along the rails during
  the move phase.

### What the player sees

- Top bar: `Line pulsing - 3 craft` during a stop, and `PULSE` with a
  progress bar during the move phase.
- Station panel: each line station shows `Done - waiting for the
  pulse` once its stop is over, so a player can see which station is
  the slow one and split its fitting order (the SPLIT the recipe
  already exposes).
- Crane row in BUILD: `Gantry crane (1 of 3)  +1 lets two craft move
  at once`.

## Simulation changes

`FLBSpacecraftRuntimeState` grows a line-level pulse record:

    ELBSpacecraftLinePhase Phase;        // Stopped, Moving
    float PhaseElapsedSeconds;           // move-phase progress
    int32 PulseCount;                    // for the HUD and tests

`FLBSpacecraftRuntimeAssignment` gains `bStopComplete` (the station
has finished and holds the craft). Save schema bumps to v8; a v7 save
is refused as today (no migration).

`ValidateRuntime` keeps "two units occupy one station" and adds:
`Phase == Moving` requires at least one assignment, and no
assignment may be `bStopComplete` while `Moving`.

`TickProduction` becomes:

    accrue every unit's stop; mark bStopComplete when full
    if Phase == Stopped and every unit is complete (rework done):
        Phase = Moving; PhaseElapsedSeconds = 0
    if Phase == Moving:
        PhaseElapsedSeconds += dt
        if PhaseElapsedSeconds >= MoveSeconds(cranes, units):
            advance every unit tail-first (TryAdvanceAssignment);
            a refusal (missing parts, occupied) holds THAT unit only
            and the pulse still completes for the rest
            admit a new unit at the head
            Phase = Stopped
    else (Stopped): nothing moves

A held unit whose refusal is "insufficient resources" is the same
starvation stall as today and reads the same way; the rest of the
line is not punished for it beyond waiting on the next pulse.

## Presentation

`RefreshUnits` stops sliding on per-unit `Progress01` and asks the
coordinator for the line phase. During `Moving`, unit k's carry
interval within the phase is

    [trip(k) * CraneTripSeconds, (trip(k) + 1) * CraneTripSeconds)
    where trip(k) = floor(order(k) / cranes), order tail-first

so with one crane the craft move one after another under the single
gantry, and with a crane per gap they all rise and travel together.
`TickHallCrane` drives every owned crane, each to its assigned craft.

## Tests (as written, which differ from the first list)

- `RuntimeCoordinator.PulseMovesCraftTogether`: three craft on the
  rig line; a finished station is seen holding its craft while
  another craft is mid-stop; every station change lands on a pulse
  tick; all three deliver.
- `RuntimeCoordinator.MoreCranesMakeAShorterPulse`: the same run with
  one crane and with a crane per gap (bought through BuyGantryCrane up
  to the cap, then refused with "one per gap"); the per-gap line
  delivers sooner. The pulse count is deliberately not pinned.
- `Logistics.ADeliveryDockCarriesBoughtPartsToTheLine` (same night,
  stranger F32) is unrelated to the pulse but shares the commit
  window.
- Not written: a dedicated starved-station test (the behaviour is
  covered by the existing starvation path in TryAdvanceAssignment and
  by PulseMovesCraftTogether not deadlocking), and a v8 save round
  trip beyond the existing `SaveLoad.MidFlightRoundTripRestoresExactly`,
  which now carries the pulse fields through `Runtime` wholesale.
- The existing `CraftFlowsOnCycleTimesToDispatch` "no station holds
  two units" pin and its "at least the summed cycle times" bound both
  still hold; `ManualHoverTestHoldsCraft` holds because the line's end
  is not a crane move.

## Order of work

1. Sim: phase record, `bStopComplete`, the new tick, crane count read
   from the build authority (a `GantryCrane` line item), schema v8,
   tests green.
2. HUD and panel text.
3. Presenter: shared-phase carry and per-crane animation.
4. Packaged run with both crane models captured on camera for the
   owner's comparison, recorded in an audit receipt.

## Status (updated the same night)

Built, in the order above, on 2026-09-02 between 03:20 and 04:30:
steps 1 to 3 as written (simulation with the line's end exempt from
the crane move, cranes bought in the BUILD tab up to one per gap, the
cvar retired, schema v8, HUD and panel wording, the carry driven by
the pulse phase, and the hall drawing as many cranes as are owned).
Departures from the design: pulse readiness ignores the last station
(a finished craft flies out under its own power, every tick), and the
pulse COUNT is not pinned across crane counts - a shorter move phase
shifts when the head admits the next craft.

Evidence: `Saved/Automation/PulseLine3_2026_09_02` (138/138), with
`RuntimeCoordinator.PulseMovesCraftTogether` and
`RuntimeCoordinator.MoreCranesMakeAShorterPulse` new. Seen in PIE at
commit 87e8edd (`Saved/Audits/PulseLine_2026_09_02`: the top bar reads
"1 done and waiting for the pulse", then every craft on the line
changes station in the same sample and a new one enters). Commit
299d957 then gave every crane its own hoist so a shared trip lifts
its craft together (`Saved/Automation/PulseCranes_2026_09_02`,
138/138). A third commit rebuilds the hall interior when the crane
count changes, so a bought crane appears at once. **Validation-only**
until the cycle-10 package lands; step 4 (both crane models on
camera, side by side) is still to do. A placement fault found on the
way - every crane portal at the head end 4 m apart on the scripted
line - turned out to be the dev command laying a legacy show track
away from the stations; it now relays through the stations like
commissioning does, and the portals stand between the stations.

## Addendum, 2026-09-03 evening: the crane is gone

Owner: "don't think we need the cranes and the whole [transfer] should
move with the ship stands so a new stand will appear in station one
after it's moved out in sync." The visible gantry - portal, trolley,
rails, hoist, and the `TickHallCrane` that drove them - is removed.
It never actually carried the craft: it was a mesh chasing a published
position (`CarriedCraftAtCm`) while the craft's own rise-carry-descend
arc ran as a completely separate, independently-driven system, only
choreographed to look connected. Both halves of that were decoration
around the one thing that actually moves a craft - the per-tick
position update in `RefreshUnits` - the same shape the original belt
turned out to be (see "The belt never moved anything" above).

**What changed and what did not.** The PULSE ITSELF - every station
finishing before anyone moves, then everyone advancing together - is
untouched; this addendum is about the visible carrying mechanism, not
the batch-movement decision this whole document is about. The
THROUGHPUT ECONOMY this fed is also untouched: `BuyGantryCrane`,
`GetCraneCount`, `GetMaxCraneCount` (one per gap), `CraneTripSeconds`
and the `GetMoveSeconds() = CraneTripSeconds * ceil(craft/N)` formula
are all exactly as tested - a real upgrade axis the owner asked for on
2026-08-29, and tonight's ask was about the mechanism on screen, not
that economy. Only the player-facing TEXT changed ("Transfer drive"
in the BUILD tab, "per transfer trip" in the tooltip and purchase
reason) - the internal field/function names (`GantryCranes`,
`GantryCraneCostPence`) stay as they are for save compatibility and
because renaming working, tested code for a cosmetic reason is not
free.

**What replaced the visual.** Every craft now travels on its own
stand - a flat platform (`MakeUnitStand`, hue-free blockout,
`LBSpacecraftPalette::StructureGraphite`) attached under its primary
visual component the moment it first takes on a real form, sized off
that mesh's own bounds so a blockout hull gets a stand that scales
with it. It rides with the craft through the station's OWN four-post
working lift (unchanged, unrelated - that still raises the craft, and
now its stand, for the ground crew) and every pulse's slide to the
next station, now at a CONSTANT rail height instead of rising -
`ComputeCraneCarryCm` is deleted outright along with its dedicated
test, not left calling into nothing. The stand is destroyed (not
carried into the departure flight, unlike landing gear - a stand is
part of the LINE, not the ship) the moment a unit departs. A fresh
craft admitted at the head of the line gets its own fresh stand the
moment it takes on a real form, which is what reads as "a new stand
appearing at station one" - no separate idle-prop bookkeeping needed
for an empty stand to sit and wait.

**Proven:** clean build; 117/117 across the full `LineBoss.Spacecraft`
suite (one fewer than before - the deleted `CraneCarry` test - no
other regressions, `MoreCranesMakeAShorterPulse` still green
unchanged); live PIE, a fresh editor launch, zero crane-related log
lines across two full pulse cycles (a Scout completed end to end, then
a second caught mid-line at three different stations) versus the
pre-existing "station mesh bound"-style confirmation lines for
everything else; frames at three stations show no crane, gantry, rail
or hoist anywhere in view. **Not strongly proven on a frame:** the
stand itself reads distinctly from directly overhead at gameplay zoom
- it sits mostly under the hull's own silhouette from that angle, by
design (90% of the hull's own footprint), so its presence is
functional (in code and in the object hierarchy) more than it is
visually striking yet. Worth a closer look once real stand geometry
replaces the blockout.
