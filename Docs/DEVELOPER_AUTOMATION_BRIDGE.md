# Line Boss local developer automation bridge

The bridge lets a local development tool operate the real playable Line Boss world through
existing gameplay authorities. It is designed for repeatable packaged-build QA, screenshots
and direct Codex play sessions.

## Safety boundary

- Disabled by default.
- Starts only with the exact `-LineBossAutomationBridge` launch flag.
- `ALBGameMode` does not construct it in Shipping builds.
- Uses files beneath the project's own `Saved/AutomationBridge` directory.
- Opens no socket, web server or remote endpoint.
- Accepts no caller-selected output path.
- Processes commands on the Unreal game thread, in sequence, at most eight per pump.
- Repeated command IDs cannot repeat a gameplay side effect.

## Launch

Launch a Development Editor or packaged Development build with:

```powershell
LineBossCarFactory.exe -LineBossAutomationBridge -windowed -ResX=1920 -ResY=1080
```

When ready, the game atomically writes:

```text
Saved/AutomationBridge/session.ready
Saved/AutomationBridge/state.ready
```

`session.ready` identifies the current session-specific inbox, outbox and screenshot folders.
Each fresh run owns a fresh session, so commands from an earlier process cannot affect it.

## Simple client

`Tools/LineBossAutomation.ps1` reads the active session, allocates the next sequence, performs
an atomic command delivery and waits for its terminal reply.

```powershell
& .\Tools\LineBossAutomation.ps1 -Type ping

& .\Tools\LineBossAutomation.ps1 -Type open_ui `
  -ArgsJson '{"page":"production"}'

& .\Tools\LineBossAutomation.ps1 -Type place_machine `
  -ArgsJson '{"machine_type":"inbound_delivery_dock","x":-10000,"y":-1000,"yaw_degrees":-90}'

& .\Tools\LineBossAutomation.ps1 -Type queue_panel_batch `
  -ArgsJson '{"order_id":"DIRECT-001","vehicle_model_id":"LB-CAR-01","panel_type_id":"FRONT-DOOR-OUTER","quantity":20}'

& .\Tools\LineBossAutomation.ps1 -Type capture_screenshot `
  -ArgsJson '{"name":"direct_play_proof"}'
```

For an archived packaged build, pass its fixed bridge root:

```powershell
& .\Tools\LineBossAutomation.ps1 -BridgeRoot `
  '.\Builds\PlayerBuildable_v1026\Windows\LineBossCarFactory\Saved\AutomationBridge' `
  -Type get_state
```

## Protocol v1

The caller writes a UTF-8 JSON object to a temporary file, then atomically renames it to:

```text
<inbox>/<12-digit-sequence>_<safe-command-id>.ready
```

Envelope:

```json
{
  "protocol": "lineboss.automation",
  "version": 1,
  "kind": "command",
  "session_id": "value from session.ready",
  "command_id": "direct-001",
  "sequence": 1,
  "type": "ping",
  "args": {}
}
```

The game atomically writes one terminal response to:

```text
<outbox>/<12-digit-sequence>_<safe-command-id>.reply.ready
```

Every response carries `ok`, a structured `result`, a nullable structured `error`, completion
time and state snapshot ID. Malformed commands receive terminal errors and do not block the
following sequence. `.tmp` files are ignored.

## Commands

| Command | Main arguments | Effect |
|---|---|---|
| `ping` | none | Confirms the active session. |
| `get_state` | none | Returns machines, storage, production, support fleet, coil AGV, UI and camera state. |
| `open_ui` | `page`, optional `visible` | Opens/closes an exact management page. |
| `focus_factory` | none | Frames the currently built factory. |
| `set_camera` | optional `x`, `y`, `z`, `yaw_degrees`, `zoom_cm` | Applies a deterministic bounded management-camera pose. |
| `place_machine` | `machine_type`, `x`, `y`, optional `z`, `yaw_degrees` | Uses the real ordered builder and placement authority. |
| `place_storage` | `storage_type`, `x`, `y`, optional `z`, `yaw_degrees` | Uses authored defaults and real storage validation. |
| `queue_panel_batch` | order/model/panel IDs and `quantity` | Queues a real player production order. |
| `step_flow` | none | Runs one bounded automatic material-flow scheduler pass. |
| `support_robot` | `action`, `unit_id` | Safely dispatches or returns a known support robot. |
| `coil_agv` | `action`, action-specific IDs | Reads state, reloads, dispatches, confirms handoff or resets a proved fault. |
| `capture_screenshot` | safe `name` | Queues a rendered viewport capture under the session screenshot folder. |

Machine names: `inbound_delivery_dock`, `coil_weigh_inspection_cell`,
`depackaging_robot`, `decoiler_feeder`, `press_train`, `inspection_cell`,
`outbound_panel_dock`.

Storage names: `bare_coils`, `prepared_blanks`, `finished_panel_stillages`, `scrap`,
`maintenance_parts`, `quarantine`.
