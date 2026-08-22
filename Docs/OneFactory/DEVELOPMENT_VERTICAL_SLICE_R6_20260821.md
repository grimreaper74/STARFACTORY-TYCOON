# Development Vertical Slice R6 — 21 August 2026

## Deliverable

Windows Development package:

`E:\LineBossValidationOutput\Builds\Development_20260821_vertical_slice_r6\Windows`

R6 supersedes R5 as the current package for exercising the OneFactory
management loop. It includes the current scanner/paint presentation, the
save-safe player quality evidence identity, and the central production-ready
vehicle recipe gate.

## Build and boot evidence

`RunUAT BuildCookRun` completed successfully on 21 August 2026:

```text
BUILD SUCCESSFUL
AutomationTool exiting with ExitCode=0 (Success)
```

The archived executable was launched directly with `-nullrhi`, `-unattended`,
`-nosound`, and `-ExecCmds=quit`. Its own log records both
`LINE_BOSS_ONEFACTORY_BOOTSTRAP_READY` and a valid OneFactory game mode with
exactly one production-flow authority and runtime coordinator, followed by a
clean exit request.

## Gameplay changes included

- Player quality-pass/rework evidence IDs are derived from the saved unit stage
  revision, rather than a controller-local counter.
- A vehicle recipe must have a revision, a separate panel authority, a validated
  panel set and a BOM before it can be contracted, manufactured or selected for
  factory changeover.
- Staged development recipes remain registerable for authoring but cannot be
  mistaken for production-ready vehicles.

## End-to-end player-loop evidence

The current editor build passed
`LineBoss.OneFactory.ActualPlayer.NativeUMGFull57StationQualityReworkLoop` on
21 August 2026. The test commissions the factory through its public UMG model,
traverses all 57 configured physical positions, clears the quality/rework loop
and dispatches the completed vehicle. The Automation report is under
`Saved/Automation/OneFactory/R6_Full57PlayerLoop_20260821`.

This is executable gameplay evidence, not a replacement for a captured visual
run demonstrating the ED immersion and scanner sweep.

The scanner actor also passed
`LineBoss.OneFactory.Presentation.InspectionScannerOwnsBeamAndSweeps`: it owns
the authored ScanKit beam, has no collision/navigation side effects, sweeps to
both ends and dwells before returning. A player-visible capture remains a
separate outstanding deliverable.

## Package closure

`Scripts/test_development_package_closure.ps1` passed against R6:

- 7,141 UFS manifest entries and 5 cooked containers;
- no `Meshy`, `UserMeshy`, `ExternalGenerated`, retired thumbnail or failed
  `Cairnwell2040PanelModules_v001` paths;
- required scanner, runtime car and native WIP roots present.

The failed external panel root is also explicitly listed in
`DirectoriesToNeverCook`, preventing a broad future cook root from bringing it
back accidentally.

R6 is intentionally a **development** package. The same closure script has a
`-ReleaseCandidate` mode that rejects the current revisionable Cairnwell
runtime/WIP authority and generic `/Candidates/` cook paths. Passing development
closure is not a clean-room release certificate, a final-car approval, or proof
of a sustained player-visible end-to-end factory run.
