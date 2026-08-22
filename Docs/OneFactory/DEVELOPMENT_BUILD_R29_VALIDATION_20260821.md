# Development Build R29 Validation

Build root: `E:\LineBossValidationOutput\Builds\Development_20260821_factory_r29_validated_panels\Windows`

## Build result

`BuildCookRun` completed successfully on 2026-08-21. The staged package contains the
11 validated Cairnwell panel modules, with 22 manifest entries (package and bulk data).
The panels are development WIP: they use the local structure-steel material and do not
reference the retired imported full-car material closure.

## Clean-room package scan

The final UFS manifest was searched after staging:

| Token | Entries |
| --- | ---: |
| `Meshy` | 0 |
| `Cairnwell2040Runtime_v001` | 0 |
| `LB_WeldRobot_SharedBase_LOD0_v001` | 0 |

This evidence applies to R29 only. It does not make the revisionable development car
final art, nor does it supersede future provenance checks for new content.

## Player-facing scope

R29 includes the prebuilt factory, current keyboard focus handling, the press-to-stillage
panel flow, and Body/Weld closure cells for left/right doors and bonnet/tailgate assembly.
