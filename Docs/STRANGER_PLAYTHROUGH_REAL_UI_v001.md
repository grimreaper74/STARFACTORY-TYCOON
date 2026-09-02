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
SUCCESSFUL, 2026-09-02 01:33). The stranger path has not yet been
replayed inside that package - PIE is the evidence so far.
