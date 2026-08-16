# Controls and management UI

Current bindings come from
[`Config/DefaultInput.ini`](../../Config/DefaultInput.ini) and the management
pawn bindings in
[`LBManagementPawn.cpp`](../../Source/LineBossCarFactory/LBManagementPawn.cpp).

## Management/factory view

| Action | Keyboard/mouse | Controller |
|---|---|---|
| Pan camera | `W A S D` | Left stick |
| Rotate camera | `Q / E` | Current config has no dedicated management right-stick axis |
| Zoom | Mouse wheel | Left/right triggers |
| Reset camera | `Home` | Face button right; context may also cancel placement |
| Select / interact / confirm placement | Left click or `F` | Face button bottom through contextual confirm |
| Toggle management | `M` | Special-left/menu |
| Previous / next management page | `[` / `]` | Left/right shoulder |
| Previous / next action | Up/down arrows | D-pad up/down |
| Confirm management action | `Enter` | Face button bottom |
| Direct press-train placement shortcut | `B` | No dedicated binding |
| Rotate placement | `R` | Right shoulder |
| Cancel placement/editor | `Escape` | Face button right |
| Contextual builder/seat shortcut | `V` | Face button top |

Placement UI currently advertises a 1 m machine/storage grid and 0.5 m
infrastructure grid. The world authority, not the HUD hint, decides whether a
placement is legal. Automatic routes, connections, walkways and safety markings
must remain editable after generation; successful auto-generation is not a
license to overlap machine access or logistics envelopes.

## Control-room context

| Action | Keyboard/mouse | Controller |
|---|---|---|
| Look | Arrow keys | Right stick |
| Interact | Left click or `F` | Face button bottom |
| Focus selected CCTV | `C` | Left shoulder |
| Sit/stand | `V` | Face button top |
| Capture operator evidence | `F10` | No default controller binding |

## Current source UI versus release proof

The checked-in HUD source now exposes seven player-facing pages in
[`LBControlRoomHUD.h`](../../Source/LineBossCarFactory/LBControlRoomHUD.h). The
old enum ordinals are deliberately retained for Blueprint/input compatibility:
`FactoryBuild` is labelled Build, `Production` is labelled Orders,
`PressTrains` is labelled Assets, and `SupportFleet` is labelled Maintenance.
Research and Analytics occupy the new ordinals 5 and 6.

The seven source pages are:

1. **Overview** — cash, research points, throughput, top constraints and alerts.
2. **Build** — machines, storage, logistics and safety with price/requirement
   preview before placement.
3. **Orders** — model/panel/BOM demand, quantity, priority, due state and terminal
   outcome.
4. **Assets** — machines, press trains, AGVs/FLTs and support robots with state,
   capacity and upgrades.
5. **Maintenance** — deterministic wear, service due, planned holds, parts and
   service history; no random nuisance breakdowns.
6. **Research** — exact unlock costs, dependencies and benefits.
7. **Analytics** — throughput, starved/blocked/fault time, quality and OEE with
   raw-period definitions.

The implementation projects the management snapshot into cash, research,
quality, maintenance and analytics readouts. The latest broad live Unreal MCP
run passed all 24 `LineBoss.Management` tests, including responsive
720p/1080p readability, manual campaign save/load double confirmation, all four
runtime-bridge tests and `SevenPageLayoutMouseControllerParity`; see
[validation evidence](VALIDATION_EVIDENCE.md). The current revision is compiled
and archived in v1031 Shipping, but the seven-page mouse/keyboard/controller
journey has not yet been completed in that package. Therefore it is
**package-present, interaction acceptance pending**, not packaged-playable.
The persistent strip is intended to keep cash, research points, order state and
the top actionable alert visible.

Before long multi-year sessions are treated as scale-proved, analytics history
needs retention/rollup; the current store is append-only and its history queries
are linear.

## Interaction and readability gates

The five current 1280x672 live PIE captures under
[`Saved/Audits/UIUX/20260812_live_pie_successor_v002`](../../Saved/Audits/UIUX/20260812_live_pie_successor_v002)
show that the factory identity/livery modal and persistent HUD are materially
more readable. Placement now presents footprint/hatch/envelope and IN/OUT
geometry; an invalid preview names the obstructing actor/component and gives a
move/rotate recovery action, and returning to valid placement immediately clears
the stale warning. These are validated source behaviours, not packaged proof.

Those captures predate the now-tested authorised-bay first framing,
hierarchy-based recognisable placement ghosts and rich decision cards. The open
gate is to accept those later source changes in v1031 Shipping and validate
populated-factory lighting; final authored thumbnail art remains optional polish.

- Every essential action must be reachable by mouse, keyboard and controller.
- Focus state, hover state, disabled reason and destructive confirmation must be
  visually distinct; colour alone is insufficient.
- Alerts must jump to and frame the exact actor without changing simulation
  authority.
- The inspector is read-only unless an explicit action is selected.
- Text must remain readable at 1280x720, 1920x1080 and 4K UI scale; no status may
  be conveyed solely by a beacon colour.
- Branding setup must not allow player colours to recolour safety yellow/red,
  lenses, raw steel, tools, cables, labels or emergency controls.
- Input hints must be generated from active bindings before release; the current
  hard-coded hints can drift from config.
