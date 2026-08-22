# Development Vertical Slice R8 — 21 August 2026

## Delivery

Windows Development package:

`E:\LineBossValidationOutput\Builds\Development_20260821_factory_r8_cleaner_pr005\Windows`

R8 is a development follow-up to R7.  It narrows the packaged legacy Press
candidate closure; it does not turn the current development car into a
release-approved vehicle.

## Cook closure improvement

The project no longer cooks the obsolete PR005 HMI derivative root:

`/Game/LineBoss/Stations/Press/PR005/Candidate_v001/ArtDerivatives/HMI_v001`

The archived R8 UFS manifest was directly scanned for the four known unwanted
identifiers.  It contains none of:

- `Meshy`;
- `UserMeshy`;
- `Cairnwell2040PanelModules_v001`;
- `LB_WeldRobot_SharedBase_LOD0_v001`.

This is a targeted development-package reduction only.  A release candidate
still requires the broader clean-room asset replacement and allow-list work.

## Follow-up cook policy

The imported `Cairnwell2040Runtime_v001` full-car root is now excluded from
future development cooks. The playable factory continues to use the native WIP
vehicle kit for press racks, Body/Weld and the visible ED immersion. This is
intentionally a development representation; a future approved vehicle must
arrive as its own clean-room visual authority rather than re-enabling the old
imported root.

## Current playable-flow evidence

On the current source revision, the native player loop completed through the
real GameMode and public UMG controls:

- all 57 factory stations commissioned;
- a vehicle created and started;
- two quality/rework decisions exercised;
- the same vehicle dispatched after the final pass.

Focused automation:

`LineBoss.OneFactory.ActualPlayer.NativeUMGFull57StationQualityReworkLoop`

Report:

`Saved\Automation\OneFactory\Current_Full57StationPlayerLoop_20260821`

The run also confirmed one production-flow authority and one runtime
coordinator.  This is functional automation evidence, not a substitute for
fresh player-visible footage, whole-factory performance proof, or a final art
review.

## Vehicle-model boundary

Production recipe parsing is now registry-driven rather than Cairnwell-only.
The WIP presenter deliberately withholds units whose model has no registered
visual authority; it must never render an unknown model using Cairnwell parts.

Current state: `CAIRNWELL_2040` remains the only visually authorised
development model.  Adding another production model requires its own approved
recipe, panels, BIW/body/rolling visual authority and materials.
