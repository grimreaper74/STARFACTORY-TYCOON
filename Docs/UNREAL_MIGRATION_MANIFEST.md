# Line Boss Unreal migration manifest

Updated: 2026-08-01

## Repository boundary

- Production Unreal project: `C:\Users\greg_\Projects\LineBossCarFactory_Unreal 5.8`
- Reference Godot project: `C:\Users\greg_\Projects\car factoy mayhem`
- OneDrive is prohibited for generated Unreal project/cache content.

## Current migrated content

| Area | Unreal path | Status | Evidence |
|---|---|---|---|
| Press Shop shell | `/Game/LineBoss/Maps/LB_PressShop_Foundation` | Functional foundation | 220 m x 120 m; 112 actors |
| Shared HMI v004 | `/Game/LineBoss/Shared/HMI/IND_HMI_001_V004_Modeling003` | Candidate, preferred geometry | HMI validation assets |
| Shared HMI v005 | `/Game/LineBoss/Developer/Validation/LB_HMI05_UnrealNativeValidation` | Rejected as production geometry | Native A/B candidate retained |
| PR-005 modules | `/Game/LineBoss/Stations/Press/PR005/Candidate_v001` | Candidate, modular import passed | 13 manifests; 59 meshes; 140/140 material slots bound |
| PR-005 validation | `/Game/LineBoss/Developer/Validation/LB_PR005_ModularValidation` | Working fixed-camera test level | Overview, process and top screenshots |
| PR-005 motion | `/Game/LineBoss/Stations/Press/PR005/Candidate_v001/Sequences/LS_PR005_OperationalCycle_v001` | Animation proof, not gameplay logic | 25 animated semantic movers |

## PR-005 source modules

The generated FBX and JSON handoff files are under
`SourceAssets/PR005/<module>/`. Current module IDs are:

- Headstock
- Mandrel
- CoilCar
- PayoffCoil
- KeeperSnubber
- PeelerThreader
- CropShear
- ContinuousStrip
- GuardingHMI
- HydraulicPowerUnit
- HydraulicRouting
- FloorZoning
- ServiceLabels

Every module manifest records source object names, material slots, dimensions,
triangle counts and mover pivots. None is promoted merely because it imports.

## Rebuild scripts

- `Scripts/export_pr005_module_for_unreal.py`
- `Scripts/import_pr005_vertical_slice.py`
- `Scripts/tune_pr005_validation.py`
- `Scripts/build_pr005_operational_sequence.py`
- `Scripts/capture_pr005_vertical_slice.py`
- `Scripts/audit_pr005_materials.py`
- `Scripts/audit_pr005_unreal_level.py`

## Promotion gates still required

1. Correct PR-005 silhouette and dimensions against the supplied PDF/reference sheets.
2. Factory-context PBR materials and lighting rather than validation-only constants.
3. Collision and access envelopes.
4. Gameplay-driven commissioning, interlocks, faults and HMI controls.
5. Continuous strip width/path verification and believable coil edge profile.
6. Fresh fixed-camera comparison after every visual change.
