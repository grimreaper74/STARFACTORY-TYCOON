# Development Vertical Slice R5 — 21 August 2026

## Deliverable

Windows Development package:

`E:\LineBossValidationOutput\Builds\Development_20260821_vertical_slice_r5\Windows`

R5 packages the current OneFactory management loop, including registered
vehicle programmes, empty-line retooling, and immutable per-order recipe and
panel-BOM genealogy. Cairnwell remains a DEVELOPMENT, revisionable vehicle
authority rather than final-release car art.

## Build and boot evidence

`RunUAT BuildCookRun` completed successfully:

```text
BuildCookRun time: 108.16 s
BUILD SUCCESSFUL
AutomationTool exiting with ExitCode=0 (Success)
```

The packaged game executable was launched directly with `-nullrhi`,
`-unattended`, and `-ExecCmds=quit`; it loaded
`LB_MoorcrossWorks_OneFactory_v001`, reported the OneFactory bootstrap and
game mode ready, and exited with code `0`.

This is a boot smoke only. It is not a substitute for a filmed or interactive
end-to-end factory run.

## Cook-manifest checks

Source: `Manifest_UFSFiles_Win64.txt` in the R5 archive.

| Query | Count | Meaning |
| --- | ---: | --- |
| `Meshy` | 0 | No cooked path contains the retired Meshy token. |
| `UI/ProductionFlow/v003` | 0 | Retired imported production thumbnails are absent. |
| `Cairnwell2040PanelModules_v001` | 0 | Failed external panel-module root is absent. |
| `ScanKit_v001` | 2 | Scanner mesh closure is packaged. |
| `VehicleWIPNativeKit_v001` | 32 | Native WIP vehicle kit is packaged. |

These are package-path checks, not a clean-room provenance certificate for all
remaining candidate-path assets. A source-provenance migration/replacement
pass is still required before any release claim.

The reusable `Scripts/test_development_package_closure.ps1` gate was also run
against R5 and passed: five cooked containers, 7,141 manifest entries, no
forbidden path hits, and no missing live development authorities.

## Gameplay evidence carried into R5

Focused reports under `Saved/Automation/OneFactory` establish the current
development contract loop:

- `ProductionFlowContracts_20260821`: **13/13 success**.
- `RevisionSafeBOM_20260821`: **1/1 success**.
- `RevisionSafePlayerChangeover_20260821`: **1/1 success**.
- `ContractRestoreGate_20260821`: contract restoration rejects unknown model
  programmes rather than silently accepting invalid genealogy.

## Explicit status

R5 is the current **development vertical-slice package** for exercising the
factory-management loop. It does not promote the current car to final art,
does not prove every factory asset is provenance-clean, and does not yet prove
a sustained player-visible end-to-end automated run.
