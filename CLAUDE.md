# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project

**STAR FACTORY TYCOON** — a PC-first 2.5D factory-management game about manufacturing
compact **spacecraft**, built on Unreal Engine 5.8 (C++, no Blueprint gameplay logic).
Windows-only workflow. The owner named it on 2026-08-28; earlier docs call it *Line Boss*,
which is the working title and now prior art. The module, target and `.uproject` keep the
`LineBossCarFactory` spelling deliberately — see below.

The player accepts a contract, builds a production line, manufactures components,
assembles and tests a craft, delivers it, then upgrades and researches. A full 3D
world (machines, robots, spacecraft) is viewed through an isometric-style
fixed/controlled-rotation camera with zoom and grid-based construction.

> **Read `Docs/SPACECRAFT_PIVOT_AUTHORITY_v001.md` first.** The project pivoted from
> a car-factory game on 2026-08-24. Anything in this repo that describes cars,
> Cairnwell 2040, or the coil→press→weld→paint→assembly journey is historical
> evidence and test fixtures, not direction. That document is the standing rules
> authority and wins over any older doc about *what the game is* or *what art is
> allowed*; older **release-gate and evidence** rules still stand.

- Engine: `C:\Program Files\Epic Games\UE_5.8`
- Project file: `LineBossCarFactory.uproject` (single runtime module `LineBossCarFactory`)
- **The module/target/project names keep the `LineBossCarFactory` spelling deliberately.**
  It is a build-system identifier the player never sees; it is written into the import
  table of ~17,600 `.uasset` and 712 `.umap` files as `/Script/LineBossCarFactory.<Class>`,
  and the project has **zero** CoreRedirects. Renaming it silently breaks every asset for
  no player-visible gain. The player-facing title lives in `Config/DefaultGame.ini`
  (`ProjectName`, `ProjectDisplayedTitle`, `Description`) — it still says CAR FACTORY and
  changes only when the owner picks a new title.
- The Godot project at `C:\Users\greg_\Projects\car factoy mayhem` is preserved
  simulation and asset reference from the car era. Read-only context, never a build input.

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

Narrow the `RunTests` argument to run one suite or one test. The run is only a
release-usable report if `<ReportExportPath>/index.json` exists; a directory name alone is
not a pass.

**Pass the project path ABSOLUTE, not `.\LineBossCarFactory.uproject`.** The relative form
works only when the spawned process inherits the project directory as its working directory,
and several shells here do not. When it fails the run does not error usefully: the editor
logs `Failed to open descriptor file`, exits 1, runs **zero** tests, and writes no report —
while `Saved/Logs/LineBossCarFactory.log` still holds the PREVIOUS run's output, which reads
like a clean pass with a full test tally. Two separate sessions have read a stale log as
evidence. Check the log's own `LogInit: Command Line:` line names the run you just made, and
treat a missing `index.json` as "did not run" rather than "export failed".

**`-ExecutePythonScript=` needs the same absolute-path treatment.** A relative script path
resolves against the ENGINE's own `Engine/Binaries/Win64/` directory, not the project — the
run exits 0, writes no receipt, and (without `-stdout -FullStdOutLogOutput` and an explicit
`-abslog=<absolute path>`) leaves no log at all to explain why, reading exactly like the
project-path failure above but with exit code 0 instead of 1. Always pass an absolute path to
`-ExecutePythonScript`.

Current top-level namespaces: `LineBoss.OneFactory`, `.Management`, `.BodyShop`, `.PaintShop`,
`.FactoryBuilder`, `.PressShop`, `.WeldShop`, `.BodyWeld`, `.Settings`, `.AutomationBridge`,
`.ControlRoom`, `.SupportRobots`, `.Environment`, `.Presentation`, `.MobileRoutes`,
`.FactoryBrand`, `.VisualTuning`. Most are named for car departments; they remain valid
until the spacecraft product types supersede them.

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

**`-ExecCmds` splits on COMMAS, not semicolons.** A semicolon-joined list parses as one command
whose name ends in `;` — it matches nothing, logs nothing, and never reaches the trailing
`Quit`, so the game runs forever and looks hung. Use:

```powershell
& 'C:\Program Files\Epic Games\UE_5.8\Engine\Binaries\Win64\UnrealEditor-Cmd.exe' `
  '.\LineBossCarFactory.uproject' -game `
  '-ExecCmds=LB.Spacecraft.BuildLine,LB.Spacecraft.Run 90 1.0,LB.Spacecraft.Status,Quit' `
  -unattended -nop4 -nosplash -nosound -NullRHI
```

That runs the whole journey and exits in about 12 seconds. The `; Quit` in the automation
command above is inert for the same reason — those runs exit on `-TestExit`, not on the `Quit`.
Harmless there, which is why it went unnoticed. See `Docs/HEADLESS_GAME_RUN_STALL_v001.md`.

### Editor Python scripts

`Scripts/*.py` (2700+) run **inside** the editor and import `unreal`. They are invoked headless:

```powershell
UnrealEditor.exe '<project>' /Engine/Maps/Entry -Unattended -nop4 -NoSplash -NoSound -NullRHI `
  -NoCompile -NoCompileEditor -NoAutoSave -NoSaveOnExit -NoAssetRegistryCacheWrite `
  -ExecutePythonScript="<script>" -abslog="<log>"
```

`Tools/*.py` are Blender scripts for the source-asset side, not Unreal scripts.

## Asset provenance — generated assets are ALLOWED

The former rule "no Meshy-provenance assets" is **retired** (owner, 2026-08-24). It traced
to an unverified claim that the models were "too big", contradicted by the project's own
receipts. The rule now is:

> Generated geometry is permitted as a master asset. What an asset must prove is not its
> birthplace but its **record**: a pinned source, a hash, a declared triangle budget, and —
> where it is claimed runtime-ready — a **measurement**.

- Provenance is still **declared and recorded** in a manifest with sha256, exactly as the
  existing intake lanes do.
- **Asset strategy is decided by measurement, not reflex.** No direction decision may rest
  on an unmeasured performance claim again.
- The code still contains six independent guards that reject assets **by name**
  (`Meshy`, `ExternalGenerated`, `OriginalHighPoly`). They are obsolete and must be lifted
  **together** — a partial lift leaves the ban intact and the failure is **silent** (the
  bootstrap rejects and the factory simply never commissions). See
  `Docs/MESHY_PROVENANCE_REVERSAL_PLAN_v001.md`.
- Guards that ban by **licence or working-state** (`/Downloads/`, `/Developer/Validation/`,
  `/Vendor/`) encode a real rule and are **kept**.

## Brand and colour — DECIDED

**A palette was adopted on 2026-08-29** — see `Docs/BRAND_PALETTE_ADOPTION_v001.md`. This
section previously said no brand colours existed; that is no longer true, and **art is graded
to the palette rather than picked by eye**. The wordmark is still open; the palette and type
hold either way.

The governing rule, which is what stops the interface and the factory ever landing on the same
colour:

> **No world surface may be both bright and saturated**, and only ONE of the interface and the
> machinery is allowed to have a hue at all.

The machinery carries the hue, so **the interface is hue-free**: `Panel.Bg #1B1B1B`,
`BgRaised #232322`, `Rule #363433`, heading `#A8A4A1`, body `#EDEDEC`, dim `#918D8B`.
**`#EC3013` is the only hue permitted in the interface and is reserved for refusal.**

World albedo: `Floor.Concrete #C9C5BE`, `Structure.Graphite #4A4D50`,
`Machine.Housing.Pale #D6D2CB`, `Machine.Amber #A87334` (arm segments and edge strips only —
**never** a whole machine body), `Crate.Tan #B39468`, hazard `#C9A21C` on `#23211F` for floor
infrastructure only, indicators working `#BFE4FF` / idle `#6E7C86` / fault `#E33A1C`.

`Docs/BRAND_IDENTITY_AUTHORITY.md` (Cairnwell Green, Foundry Charcoal; CAIRNWELL AUTOMOTIVE /
MOORCROSS WORKS / U-SERIES) describes the **car** game and remains prior art only — never cite
it as authority for spacecraft-era work.

Settled direction words: **clean futuristic industrial**, not grimy sci-fi — pale industrial
surfaces, graphite machinery, strong clean lighting, blue/white indicators, occasional warning
orange, clean floors, highly detailed machinery.

## Architecture

### Authority pattern

The codebase is organised around single-owner *authorities* rather than shared mutable state.
For any given concept exactly one class owns identity, state and mutation; everything else
reads. `ALBOneFactoryProductionFlowAuthority` owns WIP and genealogy and owns no
meshes; presentation actors reconstruct visuals from `UnitId + Stage + …` and must
never create a second logical record. Build authorities (`LBPressShopBuildAuthority`,
`LBBodyShopBuildAuthority`, `LBPaintShopBuildAuthority`) own placement legality.
`LBFactoryMachineBuilderSubsystem`, `LBFactoryConnectionSubsystem`,
`LBFactoryManagementSubsystem` and `LBFactoryUIStateSubsystem` are the world/game-instance
subsystems everything else routes through.

Authorities **fail closed**: an uncommissioned, paused, faulted or output-blocked department
rejects work rather than degrading. Save restore validates the entire snapshot — counters,
stage/department pairings, unique identities, genealogy, evidence IDs — *before* a single
mutation, so invalid data can never partly apply.

### Retargeting to spacecraft — where the real work is

The simulation core is product-agnostic in mechanism; the *vocabulary* is the domain lock.
Three contracts must be superseded together as v002 types:

- `ELBOneFactoryVehicleStage` (`LBOneFactoryProductionFlow.h`) — an 18-value car
  stamping-and-paint enum, SaveGame-serialised, with compile-time switch tables.
- `ELBOneFactoryDepartment` (`LBOneFactoryTypes.h`) — the four-department spine the runtime
  coordinator refuses to run without.
- The hard-coded **57-station** contract — enforced in three places including the
  pre-mutation save validator (`LBOneFactoryProductionFlow.cpp`), so a shorter route is
  rejected as corrupt until all three move together.

The grid construction the new direction wants already exists in `ALBBodyShopBuildAuthority`
(100 cm snap, 90° rotations, data-shaped cell definitions with ports and cycle times) — but it
is validation-only and not wired into the playable loop. Prefer generalising it over the
free-form Press builder or the fixed OneFactory starter layouts.

The 2.5D camera also already exists: `ALBManagementPawn` (pivot + spring arm, pitch −35,
**FOV 48 near-isometric perspective**, zoom clamps, WASD pan, tested framing contracts).
Keep perspective — every framing formula assumes FOV 48; do not switch to orthographic.

### OneFactory (`LB*OneFactory*`) — the current integration target

`LB_MoorcrossWorks_OneFactory_v001` is the single continuous map that unifies the four car
departments into one floor, one camera language and one genealogy (57 stations).
`ALBOneFactoryGameMode::SeedsProductionStations()` returns false by design and the bootstrap
contract requires it: the map opens ready but empty, and `ALBOneFactoryRuntimeCoordinator`
refuses to run until all departments are created and commissioned through the normal player
builder. **Do not "fix" this by seeding stations into the map package** — the premade factory
must be captured from the same build authorities the player uses. The principle is
domain-neutral and survives the pivot; only the department set changes.

`Config/DefaultEngine.ini` currently sets both `EditorStartupMap` and `GameDefaultMap` to the
OneFactory map. The isolated department maps (Press `v913`, Body Shop and Paint Shop
prototypes) remain deterministic test fixtures and must never be overwritten.

### Other major systems

- **Press Shop** (car-era, still the richest choreography reference): `LBPR004Station`–
  `LBPR010Station`, `LBPressShopMaterialFlowController`, `LBCoilAGVController`,
  `LBInboundDeliveryController`, `LBCompactStillageFLT`, `LBBridgeCraneController`.
- **Management layer**: `LBManagementPawn` / `LBManagementRootWidget` (native UMG, seven pages),
  `LBFactoryManagementRuntimeSubsystem` for finance/research/quality/maintenance/OEE. Contracts,
  money and the OEE pipeline are product-agnostic and carry over; **power and material
  quantity do not exist at all**, and the research tree has an API but no content.
- **Logistics**: `ALBStillageFLTFleetController` + `ALBCompactStillageFLT` (job queue, purchase
  economics, shared clearance-aware planner) are the reusable "automated carts";
  `ALBSupportRobot` / `ALBMaintenanceAMR` are the reusable maintenance robots.
  `Plugins/LineBossSupportRobotsRuntimeV002` is the *quarantined* v002 replacement —
  `EnabledByDefault: false`, absent from the `.uproject`, and it must stay that way until its
  gates pass. The v001 `Source/` files it supersedes are byte-frozen.
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

This is the repository's strongest convention and the easiest thing to get wrong. It is
**unchanged by the pivot**. `Docs/README.md` is the index; `Docs/ReleaseGate/` holds the
authority.

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
- `PROJECT_HANDOFF.md`, `NEW_CHAT_HANDOVER_*.md` and `CODEX_PROJECT_HANDOVER_2026-08-21.md` are
  historical context and must not overrule the release gate or the pivot authority.

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
