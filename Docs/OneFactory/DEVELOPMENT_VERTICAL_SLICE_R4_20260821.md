# Development Vertical Slice R4 — 21 August 2026

## Deliverable

Windows Development package:

`E:\LineBossValidationOutput\Builds\Development_20260821_vertical_slice_r4\Windows`

The package was built from the current OneFactory source after the following
vertical-slice work:

- native schematic production-flow cards rather than the retired imported
  thumbnail family;
- native WIP panel rack presentation rather than the failed external panel
  module root;
- visible paint treatment/ED tank presentation and inspection scan-kit;
- data-driven model contracts, empty-line all-shop retooling, and immutable
  order model/recipe/BOM genealogy.

## Build evidence

`RunUAT BuildCookRun` completed successfully on 21 August 2026:

```text
BuildCookRun time: 135.61 s
BUILD SUCCESSFUL
AutomationTool exiting with ExitCode=0 (Success)
```

The packaged executable completed a null-RHI unattended boot smoke with exit
code `0`.

## Cook-manifest checks

Source: `Manifest_UFSFiles_Win64.txt` in the R4 archive.

| Query | Count | Meaning |
| --- | ---: | --- |
| `Meshy` | 0 | No cooked path contains the retired Meshy token. |
| `UI/ProductionFlow/v003` | 0 | Retired imported production thumbnails are absent. |
| `Cairnwell2040PanelModules_v001` | 0 | Failed external panel-module root is absent. |
| `ScanKit_v001` | 2 | The scanner mesh closure is present. |
| `VehicleWIPNativeKit_v001` | 32 | Native WIP vehicle kit is present. |

These are package-path checks, not a blanket provenance certification for every
remaining candidate-path asset. Candidate assets still need a separate source
provenance replacement/migration pass before any release claim.

## Gameplay evidence

Focused Automation reports saved under `Saved/Automation/OneFactory`:

- `ProductionFlowContracts_20260821`: **13/13 success**. Covers contracts,
  model registration, starter and emergency contract rotation, WIP, quality,
  dispatch and persistence.
- `RevisionSafeBOM_20260821`: **1/1 success**. A vehicle captures its model,
  recipe revision and BOM at order entry; replacing a future recipe does not
  invalidate that vehicle's ledger.
- `RevisionSafePlayerChangeover_20260821`: **1/1 success**. A player-built,
  empty four-shop factory changes to a registered programme; a subsequent WIP
  unit retains that programme and its own BOM.

## Explicit status

R4 is a **development vertical-slice package**. Cairnwell is still explicitly
development/revisionable vehicle art; this package is not evidence that the
car or every remaining factory asset is final-release clean-room art. It is the
current stable build for testing the factory-management loop while those art
authorities are replaced.
