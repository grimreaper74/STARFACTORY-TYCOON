# Development Vertical Slice R10 — 21 August 2026

## Delivery

Current Windows Development package:

`E:\LineBossValidationOutput\Builds\Development_20260821_factory_r10_native_vehicle_authority\Windows`

R10 replaces R9 as the current playable development build. Its recipe metadata
and its cooked vehicle representation both identify the native WIP vehicle
authority:

`Cairnwell2040NativeWIPVehicleRepresentation_v001`

The retired imported full-car authority is source evidence only and is not
cooked.

## Package evidence

`RunUAT BuildCookRun` succeeded on 21 August 2026 in 106.06 seconds with exit
code 0.

`Scripts\test_development_package_closure.ps1` passed:

- UFS manifest SHA-256: `6671BF1C0B0C9902E2ACA17379D31A4423170B03DADDA3655484519D316B6496`;
- 7,123 UFS entries and five cooked containers;
- zero manifest hits for `Cairnwell2040Runtime_v001`, `Meshy`, `UserMeshy`,
  `Cairnwell2040PanelModules_v001`, and
  `LB_WeldRobot_SharedBase_LOD0_v001`;
- scanner and native WIP roots present.

The archived executable also completed a headless boot smoke with exit code
zero. It loaded the OneFactory map, emitted
`LINE_BOSS_ONEFACTORY_BOOTSTRAP_READY`, validated exactly one production-flow
authority and runtime coordinator, then shut down cleanly. The transcript is:

`E:\LineBossValidationOutput\Builds\Development_20260821_factory_r10_native_vehicle_authority\Smoke\boot_smoke_stdout.txt`

## Scope

R10 is a development vertical slice, not a final vehicle-art or release
candidate. The native WIP representation is intentionally temporary. Remaining
work includes a clean-room finished vehicle authority, a second model with its
own art and panels, fresh player-visible active-line/scanner/ED footage, and a
whole-factory performance and LOD gate.
