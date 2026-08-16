# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project

**Line Boss: Car Factory** — a PC-first modular automotive factory management game built on
Unreal Engine 5.8 (C++, no Blueprint gameplay logic). Windows-only workflow.

- Engine: `C:\Program Files\Epic Games\UE_5.8`
- Project file: `LineBossCarFactory.uproject` (single runtime module `LineBossCarFactory`)
- The Godot project at `C:\Users\greg_\Projects\car factoy mayhem` is the preserved simulation
  and asset reference. It is read-only context, never a build input.

### What is and is not in git

`Content/` (~7 GB of `.uasset`/`.umap`) and `SourceAssets/` (~50 GB of DCC source) are
deliberately gitignored, as are `Saved/`, `Builds/`, `Binaries/`, `Intermediate/`. Git holds
only `Source/`, `Plugins/`, `Scripts/`, `Tools/`, `Config/` and `Docs/`. A change that touches
content is therefore invisible to `git status` — record it through an audit receipt under
`Saved/Audits/...` and a doc under `Docs/` instead.

## Commands

All commands assume the project root `C:\Users\greg_\Projects\LineBossCarFactory_Unreal 5.8`.
Close the Editor first; the scripted lanes refuse to run while `UnrealEditor`,
`UnrealEditor-Cmd`, `UnrealBuildTool`, `AutomationTool`, `RunUAT` or `ShaderCompileWorker`
processes are alive.

### Build

```powershell
& 'C:\Program Files\Epic Games\UE_5.8\Engine\Build\BatchFiles\Build.bat' `
  LineBossCarFactoryEditor Win64 Development `
  '.\LineBossCarFactory.uproject' -WaitMutex -NoHotReloadFromIDE
```

Use `LineBossCarFactory` (not `...Editor`) for the game target. Live Coding via the MCP
`LiveCodingToolset` is allowed only for a small implementation-only `.cpp` change in an already
healthy Editor; any header, reflected type, module, plugin or config change needs the full UBT
build above.

### C++ automation tests

Tests live beside their subject as `*Tests.cpp` guarded by `#if WITH_DEV_AUTOMATION_TESTS` and
use `IMPLEMENT_SIMPLE_AUTOMATION_TEST` with a `LineBoss.<Area>.<Group>.<Case>` path.

```powershell
& 'C:\Program Files\Epic Games\UE_5.8\Engine\Binaries\Win64\UnrealEditor-Cmd.exe' `
  '.\LineBossCarFactory.uproject' `
  '-ExecCmds=Automation RunTests LineBoss.OneFactory; Quit' `
  "-ReportExportPath=$PWD\Saved\Automation\<RunName>" `
  '-TestExit=Automation Test Queue Empty' `
  -unattended -nop4 -nosplash -nosound -NullRHI -stdout -FullStdOutLogOutput
```

Narrow the `RunTests` argument to run one suite or one test — e.g.
`LineBoss.Management.HUD.ResponsiveReadability720p1080p`. The run is only a release-usable
report if `<ReportExportPath>/index.json` exists; a directory name alone is not a pass.

Current top-level namespaces: `LineBoss.OneFactory`, `.Management`, `.BodyShop`, `.PaintShop`,
`.FactoryBuilder`, `.PressShop`, `.WeldShop`, `.BodyWeld`, `.Settings`, `.AutomationBridge`,
`.ControlRoom`, `.SupportRobots`, `.Environment`, `.Presentation`, `.MobileRoutes`,
`.FactoryBrand`, `.VisualTuning`.

### Python contract tests

`Scripts/tests/*.py` are plain stdlib `unittest` and need no Unreal — they stub the `unreal`
module and exec the editor script under test to assert its constants and contracts.

```powershell
& 'C:\Program Files\Epic Games\UE_5.8\Engine\Binaries\ThirdParty\Python3\Win64\python.exe' `
  -m unittest discover -s Scripts\tests -p 'test_*.py'
```

### Running the game headlessly

Developer console commands drive the built factory without a player journey (see
`LBOneFactoryDevFactoryCommands.h`): `LB.OneFactory.BuildWholeFactory`,
`LB.OneFactory.StartProduction [n]`, `LB.OneFactory.Run [iters] [step] [autoQA]`,
`LB.OneFactory.BodyWeld`, `LB.OneFactory.Status`. They are registered as console commands, not
exec functions, so they work identically in the editor, in `-game`, and under `-ExecCmds` in an
unattended `-NullRHI` run.

### Editor Python scripts

`Scripts/*.py` (2700+) run **inside** the editor and import `unreal`. They are invoked headless:

```powershell
UnrealEditor.exe '<project>' /Engine/Maps/Entry -Unattended -nop4 -NoSplash -NoSound -NullRHI `
  -NoCompile -NoCompileEditor -NoAutoSave -NoSaveOnExit -NoAssetRegistryCacheWrite `
  -ExecutePythonScript="<script>" -abslog="<log>"
```

`Tools/*.py` are Blender scripts for the source-asset side, not Unreal scripts.

## Architecture

### Authority pattern

The codebase is organised around single-owner *authorities* rather than shared mutable state.
For any given concept exactly one class owns identity, state and mutation; everything else
reads. `ALBOneFactoryProductionFlowAuthority` owns vehicle WIP and genealogy and owns no
meshes; presentation actors reconstruct visuals from `UnitId + Stage + PaintColourId` and must
never create a second logical record. Build authorities (`LBPressShopBuildAuthority`,
`LBBodyShopBuildAuthority`, `LBPaintShopBuildAuthority`) own placement legality.
`LBFactoryMachineBuilderSubsystem`, `LBFactoryConnectionSubsystem`,
`LBFactoryManagementSubsystem` and `LBFactoryUIStateSubsystem` are the world/game-instance
subsystems everything else routes through.

Authorities **fail closed**: an uncommissioned, paused, faulted or output-blocked department
rejects work rather than degrading. Save restore validates the entire snapshot — counters,
stage/department pairings, unique identities, genealogy, evidence IDs — *before* a single
mutation, so invalid data can never partly apply.

### OneFactory (`LB*OneFactory*`) — the current integration target

`LB_MoorcrossWorks_OneFactory_v001` is the single continuous Moorcross Works map that unifies
Press, Body/Weld, Paint and Assembly into one floor, one camera language and one vehicle
genealogy (57 stations, 18 of them Body/Weld). `ALBOneFactoryGameMode::SeedsProductionStations()
returns false by design and the bootstrap contract requires it: the map opens ready but empty,
and `ALBOneFactoryRuntimeCoordinator` refuses to run until all four departments are created and
commissioned through the normal player builder. Do not "fix" this by seeding stations into the
map package — the premade factory must be captured from the same build authorities the player
uses, so every station stays movable, replaceable and save-backed.

The isolated department maps (Press `v913`, Body Shop and Paint Shop prototypes) remain as
deterministic test fixtures and must never be overwritten. `Config/DefaultEngine.ini` keeps the
global default map on Press `v913`; the OneFactory map applies its game mode as a local
`WorldSettings` override only.

### Other major systems

- **Press Shop**: `LBPR004Station`–`LBPR010Station`, `LBPressTrainAStation`,
  `LBPressShopMaterialFlowController`, `LBCoilAGVController`, `LBInboundDeliveryController`,
  `LBCompactStillageFLT`, `LBBridgeCraneController`.
- **Management layer**: `LBManagementPawn` / `LBManagementRootWidget` (native UMG, seven pages),
  `LBFactoryManagementRuntimeSubsystem` for finance/research/quality/maintenance/OEE.
- **Support robots**: `LBSupportRobot`, `LBCleaningAMR`, `LBMaintenanceAMR`,
  `LBSupportRobotServiceDock`. `Plugins/LineBossSupportRobotsRuntimeV002` is the *quarantined*
  v002 replacement — `EnabledByDefault: false`, absent from the `.uproject`, and it must stay
  that way until its gates pass. The v001 `Source/` files it supersedes are byte-frozen.
- **Developer automation bridge** (`LBDeveloperAutomationBridge`): file-based command protocol
  under `Saved/AutomationBridge`, off unless launched with `-LineBossAutomationBridge`, never
  constructed in Shipping, opens no socket. Client: `Tools/LineBossAutomation.ps1`. Documented
  in `Docs/DEVELOPER_AUTOMATION_BRIDGE.md`.

### Scripts as one-shot "import lanes"

`Scripts/run_*.ps1` are not general utilities. Each is a one-shot, fail-closed lane bound to a
frozen `*_contract.json` plus a `.sha256` sidecar, gated behind a mandatory `-Acknowledgement`
string, refusing to run if a result root already exists or if any Unreal/build process is live.
They snapshot protected files before and after, write a receipt under `Saved/Audits/...`, and
emit a `PASS__...` / `FAIL_CLOSED__...` marker. When a lane fails, the convention is to author
the *next* version (`_v011` → `_v012`) and keep the failed evidence rather than rerun in place.
Follow that shape when adding one; do not loosen a guard to make a run succeed.

## Release-gate discipline

This is the repository's strongest convention and the easiest thing to get wrong.
`Docs/README.md` is the index; `Docs/ReleaseGate/` holds the authority.

Status vocabulary — never upgrade a claim without the matching artifact:

| Status | Meaning |
|---|---|
| Packaged playable | The named journey ran in the named packaged build, that revision only. |
| Validation-only | Code exists with editor/source evidence; no fresh packaged journey. |
| Source candidate | Editable source/export exists; not an approved Unreal runtime asset. |
| Planned | Direction or contract only. |

- A green component test never overrides a red downstream journey; the strongest (and latest
  failing) evidence wins.
- A live MCP editor log is diagnostic evidence, not a release gate, until it becomes an indexed
  `Saved/Automation/.../index.json` report.
- Editor compilation, cook success and package success each prove only themselves.
- Folder names (`Approved`, `Production`, `Final`, `Runtime`) are not promotion evidence; assets
  progress through the states in `Docs/ReleaseGate/ASSET_PROVENANCE_AND_PROMOTION.md`.
- `Docs/ReleaseGate/FEATURE_FINISH_CHECKLIST.md` is the definition of done; use `N/A — reason`
  rather than silently dropping a gate.
- `PROJECT_HANDOFF.md` and `NEW_CHAT_HANDOVER_*.md` are historical context and must not
  overrule the release gate.

When reporting work, state what the evidence actually covers and what it does not — the docs in
this repo consistently do, and match that tone.

## Editor MCP integration

UE 5.8's experimental `ModelContextProtocol`/`ToolsetRegistry`/`AllToolsets` plugins expose a
loopback-only server on `127.0.0.1:8000`, registered for Codex in `.codex/config.toml`. It is
experimental developer tooling only. `RemoteControl`, `AutomationControllerRpc`, `Gauntlet` and
Python remote execution stay disabled — do not enable them or bind to a non-loopback interface
to work around a client problem. With tool search on, only `list_toolsets`, `describe_toolset`
and `call_tool` are visible; that is expected. `SceneTools.find_actors` rejects calls that omit
`name`, `tag` or `collision_channels` despite the schema marking them optional — always send all
three. Prefer read-only inspection; every mutation needs an exact cleanup call and a zero-result
verification. Full procedure in `Docs/ReleaseGate/UNREAL_MCP_OPERATIONS.md`.

## Conventions and gotchas

- All gameplay types are prefixed `LB` and live flat in `Source/LineBossCarFactory/`.
- Content, scripts and docs are versioned in the filename (`_v001`, `_v002`, …); supersede
  rather than edit in place, and keep the superseded artifact as evidence.
- The module uses unity builds: a helper in an anonymous namespace can silently collide with an
  identically named helper in another `.cpp` once a new file reshuffles the grouping (this bit
  `IsFiniteVector` in `LBCoilAGVController.cpp` and `LBCompactStillageFLT.cpp`). Give file-local
  helpers a name qualified by their subject.
- PowerShell here is Windows PowerShell 5.1: no `&&`/`||`, no ternary, no null-coalescing.
- Player-facing text is currently hard-coded English; there is no voice acting. Do not claim
  localization or language support.
