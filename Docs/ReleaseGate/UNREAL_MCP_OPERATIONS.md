# Unreal MCP editor operations

Status: **experimental developer tooling**. This uses the Epic-supplied UE 5.8
experimental MCP/toolset plugins to control a running Unreal Editor session. It
is not player-facing gameplay, a packaged-build
interface, a remote administration feature, or evidence that any feature works
in a shipped executable. The integration still depends on the GUI Editor: launch
it visible or minimized, not as an assumed unattended/headless service.

## Checked-in configuration

| Authority | Current setting |
|---|---|
| [`LineBossCarFactory.uproject`](../../LineBossCarFactory.uproject) | Enables the UE 5.8 experimental `ModelContextProtocol`, `ToolsetRegistry`, and `AllToolsets` plugins plus the audited editor capability set listed below. |
| [`Config/DefaultEditorPerProjectUserSettings.ini`](../../Config/DefaultEditorPerProjectUserSettings.ini) | Path `/mcp`, port `8000`, automatic server start, tool search enabled and no background CPU throttling for deliberate automation sessions. |
| [`Config/DefaultEngine.ini`](../../Config/DefaultEngine.ini) | Python developer mode is enabled, Python remote execution is disabled, the HTTP listener default is `localhost`, and Android File Server is disabled. |
| [`Config/DefaultGame.ini`](../../Config/DefaultGame.ini) | Adds an editor-only `GameFeatureData` Asset Manager scan rule required by the `AllToolsets` dependency chain. It removed the prior startup warning without adding runtime Game Features to packaged receipts. |
| [Project Codex config](../../.codex/config.toml) | Registers `unreal-mcp` at `http://127.0.0.1:8000/mcp`. |
| Global Codex config | `%USERPROFILE%\.codex\config.toml` contains the same local endpoint on this workstation. This machine-local entry is not repository authority. |

### Audited editor capability set

These plugins are enabled as Editor-only project capabilities where Unreal
supports a target allow-list:

- `PythonScriptPlugin`, `EditorScriptingUtilities` and `ModelContextProtocol`;
- `DataValidation`, `MaterialValidation` and `AssetReferenceRestrictions`;
- `FunctionalTestingEditor`;
- `GameplayInsights` and `SlateInsights`;
- `LiveCodingToolset`; and
- `AssetRegistryExport`.

This makes validation, profiling, scripting, asset-registry export, focused
functional testing and implementation-only Live Coding available to developers.
Enabling the plugins is not itself evidence that every asset has been validated
or that a performance capture has been completed.

The following broader or remote facilities remain deliberately disabled:
`RemoteControl`, `RemoteControlWebInterface`, `AutomationControllerRpc` and
`Gauntlet`. Python remote execution is off, Android File Server is off, and the
MCP/HTTP endpoint remains loopback-only. Do not turn these on merely to work
around a local client issue; approve and document a separate security boundary
first.

The initial verified editor log is
[`Saved/Logs/UnrealMCP.log`](../../Saved/Logs/UnrealMCP.log); repaired reruns are
in [`UnrealMCP_Rerun2.log`](../../Saved/Logs/UnrealMCP_Rerun2.log) and
[`UnrealMCP_Rerun3.log`](../../Saved/Logs/UnrealMCP_Rerun3.log). The final
capability/test logs are
[`UnrealCapabilityEnablement.log`](../../Saved/Logs/UnrealCapabilityEnablement.log)
and [`UnrealCapabilityFinal.log`](../../Saved/Logs/UnrealCapabilityFinal.log).
They record the server listening on `127.0.0.1:8000`, not on a LAN/public
interface. Keep it loopback-only. If the port changes, update the editor setting
and both applicable Codex configurations together.

## Verified 2026-08-12 session

The verified sessions record:

- server auto-start on port 8000 and an HTTP listener on `127.0.0.1:8000`;
- a real client handshake requesting `2025-03-26` and negotiating MCP protocol
  version `2025-11-25`;
- tool-search mode exposing three meta-tools (`list_toolsets`,
  `describe_toolset`, and `call_tool`), with 53 toolsets discoverable after
  delayed Python/toolset startup;
- current-level/read calls followed by an `/Script/Engine.Actor` create, find,
  remove, and final find probe; the final client result contained zero matching
  actors; and
- live Automation Test toolset discovery and execution.

A combined `LineBossCarFactoryEditor Win64 Development` build completed before
the final tiny test-only fixture adjustment: 13 actions in 52.12 seconds. The
fixture-only `.cpp` change then compiled successfully through
`LiveCodingToolset.CompileLiveCoding`, and the affected tests were rerun green.
This is successful Editor compilation only; no cook or packaged-build claim
follows from it.

```powershell
& 'C:\Program Files\Epic Games\UE_5.8\Engine\Build\BatchFiles\Build.bat' `
  LineBossCarFactoryEditor Win64 Development `
  'C:\Users\greg_\Projects\LineBossCarFactory_Unreal 5.8\LineBossCarFactory.uproject' `
  -WaitMutex -NoHotReloadFromIDE
```

The final Editor process was PID `2752`, its main window was responsive, and the
listener was verified on `127.0.0.1:8000`. The final startup log contains no
Game Features startup error. The Editor was deliberately left open with one
unsaved item; no automation saved or discarded it. Inspect that item before
closing the Editor.

The actor probe cleaned up its transient actor. The log shows the tool calls and
spawn/removal sequence; the zero-result assertion came from the live MCP client
response and should be captured explicitly again on every write probe.

## Normal operating sequence

1. Open this project in the matching UE 5.8 editor **visible or minimized** and
   wait for delayed plugin and Python initialization to finish. Do not use a
   fully hidden window for an unattended startup: Slate recovery or warning
   dialogs can block the request while the MCP endpoint itself appears idle.
2. Confirm the log contains `Starting MCP server on port 8000`, a listener on
   `127.0.0.1:8000`, and the final toolset count. The observed count is 53, but
   treat it as a session diagnostic rather than a permanent API guarantee.
3. Start/restart Codex from the project so [`.codex/config.toml`](../../.codex/config.toml)
   is loaded. The global entry is machine-local convenience and must not be the
   only setup documented for another developer.
4. Call `list_toolsets`, then `describe_toolset` for the smallest relevant
   toolset. Use `call_tool` only after inspecting that schema.
5. Prefer read-only inspection. Before any scene mutation, record the current
   level, use a unique probe name, and define the cleanup query.
6. After a mutation, remove the exact returned object, query again, require zero
   matches, and check that no unintended level/asset remains dirty before saving.
7. For automation, record the exact selected test paths, per-test results,
   warnings, engine/project revision, and log/report location.

### Live Coding boundary

Use the enabled `LiveCodingToolset` only for a small, implementation-only `.cpp`
change when the Editor is already healthy. After a successful compile, rerun the
smallest affected test first and then the broader subsystem selection.

Close the Editor and run the normal Unreal Build Tool command for any UHT-facing
header change, reflected type/property change, module or plugin change,
configuration/plugin enablement, uncertain dependency change, or when Live
Coding reports a reload/reinstancing problem. A Live Coding success never
replaces the clean-build, cook and package gates.

### Recovery-dialog safety

After an unclean Editor exit, UE displayed a `Restore Packages` modal. A launch
with a hidden window left the MCP request blocked until that dialog was exposed
and **Skip** was chosen. Treat this as a GUI recovery requirement, not an MCP
transport failure.

- Start recovery-sensitive sessions visible or minimized and inspect the Editor
  before diagnosing a timeout.
- Never auto-accept a package restore or overwrite. If the list may contain user
  work, stop automation, review it interactively, and preserve/copy the work
  before deciding whether to restore.
- Choose **Skip** only when the listed packages are known transient/abandoned
  recovery data and retaining them is not intended.
- After the dialog closes, wait for the loopback listener and final toolset
  registration, then begin MCP calls. Re-read the current level and dirty state
  before any write probe.

With tool search enabled, seeing only three top-level MCP tools is expected. The
domain tools sit behind the toolset discovery/dispatch layer. The verified
qualified scene toolset was `editor_toolset.toolsets.scene.SceneTools`; the
automation toolset was `AutomationTestToolset.AutomationTestToolset`.

## `SceneTools.find_actors` schema workaround

In this UE 5.8 experimental build, the described schema presents several filters
as optional, but the runtime call rejects an object that omits `name`, `tag`, or
`collision_channels`. Always send all three keys:

```json
{
  "name": "LB_MCP_TRANSIENT_PROBE",
  "tag": "",
  "collision_channels": []
}
```

Use the exact returned actor name for cleanup verification. An empty tag and
empty collision-channel array mean “no filter” while satisfying the runtime
validator. Do not remove those fields merely because a generated client marks
them optional; re-test this workaround after every engine update.

## Safe transient write probe

Use a disposable editor world or an unsaved transient actor whenever possible:

1. `SceneTools.get_current_level` and record the map.
2. `SceneTools.add_to_scene_from_class` with `/Script/Engine.Actor` and a unique
   label/name.
3. `SceneTools.find_actors` using the three-key workaround and require exactly
   one returned object.
4. `SceneTools.remove_from_scene` using that exact object/path.
5. Repeat `find_actors` and require zero results.
6. Do not save the map as part of the probe. If cleanup or the zero assertion
   fails, stop all further write calls and restore the editor state manually.

The verified session followed this create/find/delete/find shape and ended with
zero probe actors. That demonstrates basic editor mutation and cleanup only; it
does not authorize unattended content edits.

## Live automation evidence

The initial and repaired runs were issued through the MCP Automation Test
toolset. The earlier results are preserved in
[`UnrealMCP_Rerun2.log`](../../Saved/Logs/UnrealMCP_Rerun2.log) and
[`UnrealMCP_Rerun3.log`](../../Saved/Logs/UnrealMCP_Rerun3.log); the final
management/campaign and AGV/support selections are in
[`UnrealCapabilityEnablement.log`](../../Saved/Logs/UnrealCapabilityEnablement.log)
and [`UnrealCapabilityFinal.log`](../../Saved/Logs/UnrealCapabilityFinal.log):

| Selection | Live result | Release meaning |
|---|---:|---|
| Repaired press/stillage gate | **11 succeeded, 0 failed** | All six press-train tests, four stillage-FLT tests and the exact physical handoff passed. This supersedes the earlier live 11/13 failure for current source. |
| Management runtime bridge, initial | **1 succeeded, 1 failed** | The restore test caught a real rejected-panel validation defect: the production validator rejected a valid incomplete order containing rejected output. |
| Management runtime bridge, after validator repair | **2 succeeded, 0 failed** | Both exact-once restore and real-state quality/fault/wear bridge tests passed. |
| All 20 `LineBoss.Management` tests | **20 succeeded, 0 failed, 0 warnings/errors** | Focused editor evidence for the runtime bridge, management authority, seven-page layout/input parity, persistent HUD, console-free build catalogue, infrastructure editor and UI projection. The added runtime cases cover actor-replacement quality epochs and retry-safe failed-bucket evidence. |
| Campaign/material-flow selection | **5 succeeded, 0 failed, 0 warnings/errors** | Inbound flow, exact physical handoff, modular unload and both v17 campaign round trips passed together. |
| AGV/routes/save selection | **9 succeeded, 0 failed, 0 warnings/errors** | Automatic route generation/profile ownership, player placement/persistence, coil-AGV runtime/protected-route presentation and legacy restore passed after the repair described below. |
| Support robots/natural motion/docks | **6 succeeded, 0 failed, 0 warnings/errors** | Natural cornering, player-built clearance, automatic charging, CR01/MR01 runtime and guarded service-dock restore passed together. |

The earlier repaired 11/11 press/stillage gate emitted context-less
`UWorld::DestroyActor` teardown warnings while
`LineBoss.PressShop.PressTrains.Identity.NextAvailablePersistence` reported
`Success`. Preserve that as historical evidence for that older selection. The
four final selections above (20 + 5 + 9 + 6) were warning/error-clean.

### AGV automation repair

The first broad AGV attempt exposed a stale automation fixture. Its synthetic
world lacked a registered world context and build-floor authority; after PR002
placement failed, a null `CastChecked` crashed the Editor. The fixture now uses a
scoped RAII game-world context, a valid build authority and guarded cast/port
checks with early returns.

That test also exposed a production placement distinction. The public player
infrastructure path still rejects overlap with every machine and protected
envelope. A separate private automatic-placement path may ignore only the two
machine envelopes connected by the route endpoint, while retaining all other
floor, world, storage and unrelated-machine checks. After correcting the PR002
fixture distance to remain within its valid predecessor-link range,
`LineBoss.FactoryBuilder.AGVInfrastructure.AutomaticInboundRoute` passed, then
the full 9/9 AGV selection passed.

[`UnrealCapabilityFinal.log`](../../Saved/Logs/UnrealCapabilityFinal.log)
contains an intermediate pre-fix failure followed by the successful Live Coding
compile and final green runs. Read it chronologically; the earlier failure is
historical, not the final result.

These are live editor log results, not standalone `Saved/Automation/.../index.json`
reports. Archive indexed reruns and then run the applicable packaged journeys
before changing release status.

## Troubleshooting

| Symptom | Check / action |
|---|---|
| `unreal-mcp` is unavailable | Confirm both Codex configs, restart the project-scoped client, and verify that the editor is running. |
| Connection refused | Look for the loopback listener in `UnrealMCP.log`; check port 8000 for conflicts. Do not solve this by binding to an external interface. |
| Request hangs during Editor startup | Bring the Editor window to the foreground and check for `Restore Packages` or another Slate modal. Review recovery contents; choose **Skip** only for known disposable recovery data, then wait for listener/toolset readiness. |
| Hidden launch appears healthy but tools never respond | Relaunch visible or minimized. The MCP plugin controls the GUI Editor and cannot safely dismiss hidden recovery/confirmation dialogs. |
| Only three tools are listed | Expected with tool search. Call `list_toolsets`, `describe_toolset`, then `call_tool`. |
| Fewer toolsets than expected | Wait for delayed Python startup, then inspect plugin/toolset load errors. Fifty-three is the observed final session count, not a hard-coded release requirement. |
| `find_actors` reports missing arguments | Supply `name`, `tag: ""`, and `collision_channels: []` exactly as above. |
| `resources/templates/list` is unknown | This server logged that method as unsupported. Use MCP tool/toolset discovery; do not infer resource-template support. |
| A write probe cannot be found or removed | Stop mutations, inspect the Outliner by exact returned path/name, undo or remove it manually, and verify zero before continuing. |
| Tests ran but no indexed report exists | Treat the session as live diagnostic evidence only and rerun with an archived report bundle for a release gate. |

The plugin log warns that data sent to the connected LLM service is Unreal
Engine Licensed Technology subject to the UE EULA. Keep the endpoint local,
send only approved project data, and confirm provider/training terms before using
this path with proprietary content.

## MCP session closeout checklist

- [ ] The Editor was launched visible/minimized and no unresolved recovery/modal dialog remained.
- [ ] Listener remained loopback-only.
- [ ] Negotiated protocol version and toolset count were recorded.
- [ ] Every mutation had an exact cleanup call and a zero-result verification.
- [ ] No unintended map/asset was saved or left dirty.
- [ ] Selected automation paths, all results, warnings and failures were retained.
- [ ] An indexed report was produced for any result used by a release gate.
- [ ] Editor evidence was not presented as packaged gameplay proof.
