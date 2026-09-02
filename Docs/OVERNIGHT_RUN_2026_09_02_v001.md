# Overnight run, 2026-09-02 (the second night)

Owner, going to bed: "im off to bed what do you want to do, you have
the pc?" and "after your happy with this can you do the pulse line or
before if its better?" The plan I gave: finish the stranger's loop
through the real interface, then the pulse line, tonight.

## 1. The stranger's loop, closed through the real UI

The stranger playthrough (Docs/STRANGER_PLAYTHROUGH_REAL_UI_v001.md)
reached delivery at 02:58 with every step done through the game's own
interface, driven by synthetic Slate input from the editor toolset. The
frames are in the session scratchpad (`stranger/x*`, `y*`, `z*`).

What stood between the line and its first ship, in order found:

- **F32 (severe).** Bought parts never left the delivery dock: only a
  storage rack hosted a hauler drone, no screen ever named a rack, and
  the stall toast said "none in the factory; order more" over five
  components sitting at the dock. **Fixed:** the dock hosts a feed-only
  hauler; the shortfall text names dock-or-rack; FIRST STEPS says the
  dock's drone carries parts to the line. Pinned by
  `Logistics.ADeliveryDockCarriesBoughtPartsToTheLine`.
- **F34 (high) and F31.** The six ship components sat at the bottom of
  a ~100-row import list, and orders in flight were inserted ABOVE the
  list, so every order shifted the rows under the cursor. Five of the
  stranger's six first orders bought neighbouring rows. **Fixed:**
  components head the import section; ON ORDER lists after the
  buttons, with item names.
- **F35 (severe).** CONTRACTS YOU HOLD listed three contracts never
  accepted, as "Building 0/4 ... Late" - lapsed offers leaking into
  the held list. **Fixed:** filtered.
- **F30, F33 (low).** Order toast names the item and the wait; the top
  bar shows "SCOUT-01 LATE 0/1" instead of "No contract" beside a
  held late order.
- **F36 (low).** After the first delivery nothing suggested the next
  move. **Fixed** (last build of the night): the objectives panel says
  "NEXT: accept a contract - the line is idle" or "... N finished
  ship(s) sell the moment one is taken" whenever no accepted order is
  left to build.
- **F20 (med).** Four stations left 125,000 cr, not enough to crew
  them, and nothing warned. **Fixed** (last build): the placement toast
  names the station, the cash left and what two drones for it cost,
  and says NOT ENOUGH TO CREW IT when that is so.
- **Removal confirmation** (first wave's open list): removing a
  station is two clicks now, the first quoting the refund ("REMOVE
  Assembly station Mk1 5 - refunds 120,000 cr? CLICK REMOVE AGAIN TO
  CONFIRM"), with an eight-second window that re-arms if it lapses.
  Verified in PIE (`Saved/Audits/StrangerWave3_2026_09_02`); not in
  either package.
- **Open:** F5/F9/F12 (site hit-testing, door cue).

Two toolset additions made the run possible: `ProbePieWidgetAt(X,Y)`
reports the widget and label under a point before a click (a rendered
frame and the hit-test grid disagreed for one row, and probing before
clicking was the only reliable way through a long scrolled list), and
`GetSpacecraftFactoryStatus` now lists every store's contents.

Commits: `706e766` (dock haulers, F30), `54eefbc` (wave three).
Evidence: `Saved/Automation/DockHauler_2026_09_02` and
`Saved/Automation/StrangerWave3_2026_09_02`, 136/136 each.

## 2. The pulse line

Design: Docs/PULSE_LINE_DESIGN_v001.md. Built tonight:

- **Simulation.** The line is STOPPED or MOVING. A finished station
  holds its craft (`bStopComplete`); when every craft with a station
  ahead is finished, the cranes move them all together, tail-first,
  after a move phase of `ceil(craft / cranes) x CraneTripSeconds`. A
  craft the advance refuses (parts, rework, occupied) holds with its
  stop complete and rides the next pulse. The line's end is not a crane
  move: a finished craft climbs into its hover test and flies out on
  its own, every tick, as before. New craft enter an empty line at
  once, otherwise only at a pulse, so every stop starts together.
- **Cranes are bought.** `GantryCranes` on the layout (the hall comes
  with one), `BuyGantryCrane` capped at one per gap, a "THE LINE -
  GANTRY CRANES" row in the BUILD tab. The `LB.Spacecraft.CranePerGap`
  cvar is retired; the hall draws as many cranes as are owned.
- **Save schema v8.** Older saves are refused, as the schema rule says.
  The runtime validator checks the pulse fields.
- **Presentation.** The craft rides only during its own crane trip's
  window of the move phase; with one crane the craft go one after
  another, with a crane per gap they rise together.
- **HUD.** "Line running - 3 craft, 2 done and waiting for the pulse",
  "Line running - PULSE, cranes moving 2 craft", and a station row that
  says "Done - waiting for the pulse".
- **Tests.** `RuntimeCoordinator.PulseMovesCraftTogether` (a finished
  station holds; every move lands on a pulse tick; three craft deliver)
  and `RuntimeCoordinator.MoreCranesMakeAShorterPulse` (one crane per
  gap delivers sooner than one crane; the cap refuses one more).

**A placement fault, found and fixed the same night.** On the scripted
BuildLine layout every crane portal stood at the head end 4 m apart.
The status tool was taught to dump the track pieces, which showed the
dev command laying a legacy "show track" at X=2400 and attaching the
stations at X=0 to it; the hall's crane rails follow the laid pieces.
`LayLineTrack` now calls the same relay commissioning uses, and the
portals stand between the stations (`cranes_over_gaps.png` in the
audit folder). The player-built line was never affected - its track
was always relaid - so this was a dev-command fault that had been
misdiagnosed as a presenter one.

Seen in PIE (`Saved/Audits/PulseLine_2026_09_02`): the top bar reads
"Line running - 2 craft, 1 done and waiting for the pulse", then every
craft on the line changes station in the same status sample and a
new one enters at the head; `pulse_sheet.png` shows the four frames
around one pulse. A second commit (299d957) gives every crane its own
hoist so a crane-per-gap trip lifts its craft together.

## Status, honestly

- Stranger fixes: verified in PIE this session and green in the
  indexed suite; packaged in cycle 10 (see below) but not replayed
  there through the interface.
- Pulse line: indexed suite green four times over
  (`Saved/Automation/PulseLine3_2026_09_02` through
  `NightEnd_2026_09_02`, 138/138 each), seen in PIE frames
  (`Saved/Audits/PulseLine_2026_09_02`), and **packaged** in cycle 10
  (`Builds/Overnight_2026_09_02`, BUILD SUCCESSFUL 03:19): the headless
  journey in that exe delivered 2 of 3 craft through the pulse line in
  900 sim seconds (`packaged_journey.log` in the audit folder). The
  interface path was not replayed in the package; that is the one
  thing the stranger fixes still lack.
- Cycle 10 also carries every stranger fix of waves two and three.
- **Cycle 11** (`Builds/Overnight_2026_09_02b`, BUILD SUCCESSFUL ~03:30)
  adds the relayed dev track, so BuildLine in the exe stands its
  cranes between the stations. Its headless journey again delivered
  2 of 3 craft in 900 sim seconds. This is the build to open in the
  morning. The placement toast (F11/F20) came after it and is
  editor-validated only; the NEXT objective line (F36) is in both
  cycles.
- **The interface replay in the package did not happen.** Launching
  the cycle-11 exe with real input raised a Windows Firewall prompt
  ("allow public and private networks to access this app", publisher
  Line Boss) that sat over the game from its first frame; every
  scripted click and key went to that dialog. I did not answer it -
  a security prompt is yours to answer - and killed the game instead.
  When you first run the new build it will ask again; after that, the
  Win32 replay (`scratchpad/stranger/packaged_replay11.ps1`) can run.
  Two of those prompts (one per new package) are still open on the
  desktop as I write this; they are yours.
