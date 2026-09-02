# Stranger playthrough through the real UI, 2026-09-02

Owner's ask: "do the stranger playthrough through the real UI." Not the
scripted `LB.Spacecraft.BuildLine` path — the actual interface, clicked
the way a person who has never seen the game would click it, deciding
each move from the frame alone.

## How it was driven (so it can be repeated)

The first attempt used Win32 SendInput against the packaged window and
captured the owner's browser instead: he was home and using the
machine, and the OS cursor is his. So the input goes through the
engine: five new tools on `LineBossCarFactoryEditor.LBSpacecraftDevToolset`
(`StartPieFloating`, `GetPieViewportInfo`, `SimulatePieClick`,
`SimulatePieMouseMove`, `SimulatePieKey`, `SimulatePieWheel`) push
events into Slate's own routing, and VibeUE's `capture_image` returns
the frame. No OS cursor, no focus stealing; the owner kept his mouse
throughout. Two engine traps had to be worked around and are recorded
in the tool's own comments: Slate picks the window under the REAL
cursor for a press (so presses route to a hit-test path instead), and
Win32 revokes capture for a background window (so the Slate captor is
re-asserted from the press reply). Frames and log:
`scratchpad/stranger/s04…s24` for this session; the method is in the
tool source.

Coordinates: click at frame pixels ÷ the viewport's `dpiScale`
(3 on this machine) — `GetPieViewportInfo` reports it.

## What the stranger saw, in order

1. **Site map.** Every building wears a padlock; one wears a "+".
   Footer: "click a building to enter it". Nothing marks which
   building is mine.
2. Clicked the "+" building — **it bought a power plant for 200,000 cr.**
   No confirmation, no price, no toast. The badge glyph itself was not
   even the hit target; the building body was.
3. Clicked the big hall (roof): nothing. Clicked the parking lot:
   nothing. Both clicks deprojected to ground BEHIND the building —
   only a building's ground footprint counts, which nobody can know.
4. Clicked the big hall's base: the game composed "HEAVY SHIP FACTORY
   IS NOT IN THE GAME YET - IT IS DRAWN SO YOU CAN SEE WHERE IT WILL
   STAND" — exactly the sentence needed — **and showed it nowhere.**
   Every hub message went to the log only.
5. Noticed the only building with NO icon, clicked its base: "ENTERED
   SHIP FACTORY". The enterable building was the least-marked thing on
   screen.
6. Inside: a featureless pale box. BUILD tab: clear list, prices
   visible, but the header "CONVEYOR BELTS UNLOCKS AFTER DELI" clipped
   mid-word. Selected "Assembly station Mk1": a blue slab ghost and a
   good instruction toast — which said "PLACING AssemblyRobot".
7. Placed it. Toast prettified, money debited, objective ticked.
8. Clicked the same list row twice more for two more stations — **and
   bought two Delivery docks**, because arming a placement cleared the
   selection, the hall's rows vanished, and every row moved up under
   the cursor.
9. Clicked a dock to inspect it: the placement was still armed, so
   the click tried to place a third dock: "Envelope overlaps station
   Delivery dock 4".
10. Right-clicked to cancel, clicked the dock again: it selected the
    HALL (small stations are hard to hit). Panel showed "SHIP FACTORY
    1 … Remove station". Clicked Remove station — **it deleted the
    ship factory.** Refunded 125,000 cr, one click, no confirmation,
    the hall mesh still drawing, three stations on the floor of a
    building that no longer exists. Toast: "Removed ShipFactoryHall-001".
11. Commission the line: "The line has no spray booth - every craft
    leaves in the customer's livery and there is nowhere to paint it"
    — plain, specific, good.

Nineteen findings in full: `scratchpad/stranger/findings.md`
(copied below in short form).

## Findings

| # | Severity | Finding |
|---|---|---|
| F3 | severe | Site-map "+" buys a 200,000 cr building on one click, no price, no confirmation |
| F17 | severe | "Remove station" deletes the ship factory itself with one click |
| F4/F6 | high | Hub messages (what a place is, what you just bought) never reach the screen |
| F13 | high | Build list reflows after arming; second click buys the wrong item |
| F7 | high | The player's own factory is the only unmarked building on the site |
| F5 | med | Building roof/body clicks deproject behind the footprint; only the base works |
| F15 | med | Placement stays armed after a purchase with only a faint highlight as cue |
| F18 | med | Small stations are hard to select by clicking them |
| F2 | med | CONTRACTS tab opens on the raw-materials shop; offers are below the fold |
| F9/F12 | med | Empty hall gives no door/direction cue; ghost has no footprint or arrow |
| F11/F19 | low | Internal ids leak: "PLACING AssemblyRobot", "Removed ShipFactoryHall-001" |
| F10 | low | Section header clipped mid-word |
| F16 | low | "Envelope overlaps station X" — jargon |

## Fixed tonight (this commit)

- **F17**: `RemoveStationPowered` refuses the ship factory hall with a
  plain reason; the panel no longer offers "Remove station" for it.
- **F3**: the site hub quotes first ("BUY POWER PLANT FOR 200,000 CR?
  CLICK IT AGAIN TO CONFIRM") and buys on a second click within 8 s.
- **F4/F6**: every hub message now goes through the pawn toast the
  hall already uses.
- **F7**: the built, enterable place carries an "ENTER" caption; a
  buildable place carries "BUY  <price> cr" under its "+".
- **F13**: arming a placement no longer clears the selection, so the
  panel stops reflowing under the cursor.
- **F11/F19**: placement and removal toasts use display names.
- **F10**: section labels wrap instead of clipping.
- **F16**: "Too close to X - leave a gap".

## Not fixed tonight (next)

- F5 building hit-testing (roof clicks should count) — needs the hub
  rectangles to cover the sprite, or a screen-space pick.
- F15 persistent "PLACING … right-click cancels" indicator while armed.
- F18 click-to-select tolerance for small stations.
- F2 Contracts tab ordering (offers first).
- F9/F12 door/direction cue and a real footprint ghost.
- Confirmation for any refund-bearing removal (F17's cousin for
  ordinary stations).

## Re-run against the fixes (same tools, same session)

- Site map now shows "ENTER" on the ship factory and "BUY 200,000 cr"
  under the "+" (frame r02).
- First click on the "+" quotes in the toast and spends nothing;
  a second click 1.5 s later buys and says so (r08; cash 900,000 ->
  700,000 only on the second click).
- With the hall selected, the panel wraps its header and offers no
  "Remove station" (r06).
- Two placements from the same row bought the same item twice (r05).
- The hub's own pale status strip (which had been unreadable, then a
  duplicate of the toast) is hidden; the toast carries hub messages.

Status: the fixes are verified in PIE (this session) and the package
at Builds/Overnight_2026_09_01 was rebuilt with them (cycle 9, BUILD
SUCCESSFUL, 2026-09-02 01:33). The site-map path (quote, buy, enter)
was then replayed INSIDE that package with real OS input once the
owner went to bed (frames p02/p03/p04): the two-click purchase and the
ENTER caption behave in the shipped exe.

## Second wave (after midnight, owner asleep): the loop past the hall

Played on with the same tools through building, crewing, commissioning,
accepting and running. Findings F20-F28 (full text in the audit
folder), the severe ones first:

| # | Severity | Finding |
|---|---|---|
| F22 | severe | Commissioning half-succeeded: "Line idle" + ticked objective while the coordinator refused with "attach every line station to the track" - an action the auto-relay makes impossible |
| F28 | severe | The first contract (11 min) expired while the stranger learned, from a stall toast, that a ship needs a dock and parts |
| F27 | high | FIRST STEPS never mentions a delivery dock or ordering parts |
| F2b | high | 48 wheel notches down CONTRACTS still showed imports; offers unreachable |
| F18b | high | Clicking a station's own pad selected the hall around it (first-footprint pick) |
| F23 | med | Offer buttons clipped their price and deadline |
| F21 | med | "Hire drones at each station" ticked after one drone at one station |
| F20 | med | Four stations left 125,000 cr - not enough to crew them; nothing warned |
| F24/F26 | low | Ledger id in the accept toast; item id in the stall toast |
| F25 | low | Speed keys undiscoverable |
| F29 | severe | A first ship was unaffordable: components imported only in fives (598,000 cr for a set) against ~324,000 cr held, with fabrication locked until delivery 2 |
| F30 | low | Order toast: "ORDER ORD-0003 PLACED - ARRIVING SOON" - id, no item, no time |
| F31 | med | Content above the import list changes height after an order, so the rows shift ~25 px under the cursor and neighbouring clicks miss |
| F32 | severe | Bought parts never left the delivery dock: only a STORAGE RACK had a hauler drone, and nothing on screen had named a rack. The stall toast then said "none in the factory; order more" while five components sat 24 units deep at the dock |
| F33 | low | Top bar read "No contract" beside a held contract the panel marked Late |
| F34 | high | The six ship components sat at the bottom of a ~100-row import list (145 wheel notches down); the stranger's earlier five orders were all neighbouring rows of the ones meant |
| F35 | severe | CONTRACTS YOU HOLD listed three contracts the stranger never accepted, each "Building 0/4 ... Late": lapsed (Withdrawn) offers were not filtered out of the held list |
| F36 | low | After the first delivery the FIRST STEPS block disappears and nothing suggests the next move; "Line idle" plus the offer board carries it, but only just |

**The loop closed at 02:58.** With the dock hauling, the six components
ordered by probing each row's label first (the probe tool
`ProbePieWidgetAt` was added for exactly that), the ship went
MaterialIntake -> ComponentFabrication -> Testing -> Dispatched in
about ninety seconds at 4x, sat as "1 IN STOCK (accept a contract to
sell)" because the first contract had lapsed, and sold the moment a
fresh x1 offer was accepted: cash 95,593 -> 257,593, "Ships delivered:
1". Site map, hall, stations, crews, dock, commissioning, contract,
orders, build and sale were all done through the real interface.

F35 is fixed by filtering Withdrawn offers out of the held list. F36
is fixed by a NEXT line in the objectives panel whenever no accepted
order is left to build. F20 (and the placement toast's id leak, F11)
by the toast itself: "PLACED Assembly station Mk1 - THE LINE
CONNECTED ITSELF - 125,000 cr left; two drones for it cost 24,000",
with "NOT ENOUGH TO CREW IT" appended when the money is not there.
F34 and F31 are fixed together in the panel: the six ship components
now head the import section under their own label, sub-parts follow,
and orders in flight are listed AFTER the buttons (as "ON ORDER",
with item names) instead of being inserted above them, which is what
had been shifting the rows under the cursor. F33: the top bar shows
"SCOUT-01  LATE 0/1" for a missed order that still has ships owed.

F32 is the one that would have ended a stranger's evening: the loop
"build stations, dock, hire, commission, accept, order" was complete
and correct by every cue the game gave, and the ship still never
started. Fixed by giving the delivery dock a hauler of its own (it
feeds the line from what lands there and never collects machine
output into the dock), rewording the shortfall diagnosis for a
factory with neither dock nor rack, and saying on the FIRST STEPS
line that the dock's drone carries parts to the line. Pinned by
`LineBoss.Spacecraft.Logistics.ADeliveryDockCarriesBoughtPartsToTheLine`.
F30's toast now reads "Ordered 1x Hull Component - arrives in about
30 s". F31 stays open: the scroll offset is already preserved, it is
the content above the list changing height, and the honest fix is an
anchor row rather than an offset.

Fixed and verified in PIE this wave: F2b (offers first), F22
(commission fails closed and names the unreachable station), F18b
(smallest footprint wins), F15 (pinned PLACING line), F21, F23, F24,
F25, F26, F27, F28 (3x deadline until the first delivery). Open: F20
(a budget warning before the fourth station) and F5/F9/F12 from the
first wave.
