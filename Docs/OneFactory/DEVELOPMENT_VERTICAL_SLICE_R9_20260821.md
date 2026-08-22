# Development Vertical Slice R9 — 21 August 2026

## Delivery

Windows Development package:

`E:\LineBossValidationOutput\Builds\Development_20260821_factory_r9_native_vehicle_only\Windows`

R9 is the current playable development package. It replaces the R8 cook
policy: the imported full-car authority is not staged; the native WIP vehicle
kit remains the active factory representation.

## Build and packaged boot

`RunUAT BuildCookRun` completed successfully on 21 August 2026 in 143.86
seconds with exit code 0.

The archived executable was then run headlessly with `-nullrhi`,
`-unattended`, `-nosound` and `-ExecCmds=quit`. It exited 0 after loading:

`/Game/LineBoss/Factory/OneFactory/v001/Maps/LB_MoorcrossWorks_OneFactory_v001`

The smoke transcript confirms `LINE_BOSS_ONEFACTORY_BOOTSTRAP_READY` and a
valid `LBOneFactoryGameMode` with exactly one production-flow authority and
one runtime coordinator:

`E:\LineBossValidationOutput\Builds\Development_20260821_factory_r9_native_vehicle_only\Smoke\boot_smoke_stdout.txt`

## Package closure

`Scripts\test_development_package_closure.ps1` passed against R9:

- manifest SHA-256: `4DEF56C72EA7172E7A07DD90CF9BE5F0D32ACE2F3F410213A03395504A1E1DC9`;
- 7,123 UFS entries and five cooked containers;
- zero hits for `Cairnwell2040Runtime_v001`, `Meshy`, `UserMeshy`,
  `Cairnwell2040PanelModules_v001`, and
  `LB_WeldRobot_SharedBase_LOD0_v001`;
- required native WIP and scanner roots present.

## Scope and remaining release work

R9 is still a development vertical slice. Its native WIP vehicle is a
temporary clean representation, not the final car. A release candidate still
needs an approved clean-room vehicle art authority, a second model authority,
fresh player-visible active-line evidence, and whole-factory performance/LOD
validation.
