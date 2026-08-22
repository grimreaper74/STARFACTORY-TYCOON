# Development Vertical Slice R7 — 21 August 2026

## Deliverable

Windows Development package:

`E:\LineBossValidationOutput\Builds\Development_20260821_factory_r7\Windows`

R7 supersedes R6 as the current playable development build. It contains the
current OneFactory code and the tracked ED/e-coat presentation rather than the
older package that pre-dated those updates.

## Build and boot evidence

`RunUAT BuildCookRun` completed successfully on 21 August 2026:

```text
BUILD SUCCESSFUL
AutomationTool exiting with ExitCode=0 (Success)
```

The archived executable was then launched directly with `-nullrhi`,
`-unattended`, `-nosound` and `-ExecCmds=quit`. It mounted the package,
loaded `/Game/LineBoss/Factory/OneFactory/v001/Maps/LB_MoorcrossWorks_OneFactory_v001`,
reported `LINE_BOSS_ONEFACTORY_BOOTSTRAP_READY`, and reported a valid game mode
with exactly one production-flow authority and one runtime coordinator before a
clean exit (process exit code 0). The smoke transcript is at:

`E:\LineBossValidationOutput\Builds\Development_20260821_factory_r7\Smoke\boot_smoke.txt`

## Current factory evidence

The current source compiles cleanly. Focused editor automation passed on the
same source revision:

- `LineBoss.OneFactory.Presentation` — scanner sweep and stamped-panel rack
  presentation (2 tests);
- `LineBoss.OneFactory.PaintStarter` — tracked ED presentation, native asset
  resolution, rollback and cook binding coverage (7 tests);
- `LineBoss.PaintShop.EDLine` — 15-bay line layout, smooth carrier motion and
  interlocks, operations/persistence, and exact-once Body Weld handoff (4
  tests).

Reports are under `Saved/Automation/OneFactory/Current_Presentation_20260821`,
`Current_TrackedED_20260821`, and `Current_EDLineFlow_20260821`.

## Package closure

`Scripts/test_development_package_closure.ps1` passed against R7:

- manifest SHA-256: `DECED22E47A855E07C6564F1022590C267F515DC1467F81A50D0EC000A47AFB1`;
- 7,141 UFS manifest entries and 5 cooked containers;
- no forbidden development provenance paths;
- all required scanner, runtime-car and native-WIP roots present.

R7 remains a **development** package. It is not a clean-room release candidate,
a final-car approval, or proof of a filmed player-visible factory run. The
release-candidate closure mode intentionally rejects the current revisionable
development car/WIP authority and broad candidate roots.
