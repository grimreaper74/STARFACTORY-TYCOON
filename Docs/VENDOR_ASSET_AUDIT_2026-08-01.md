# Vendor asset audit — Factory Environment Collection

Date: 2026-08-01

## Decision

Use a tightly curated subset as a reusable background industrial kit. Do not use
vendor assets for Line Boss hero machinery, the shared HMI cabinet, coils, the
PR-004 padded C-hook, or process-defining PR-005 mechanisms.

The source pack remains in Epic VaultCache. Only selected assets and their
dependencies were migrated into the project, outside OneDrive, at:

`/Game/LineBoss/Vendor/FactoryEnvironment`

## Approved use tier

- Strong enough for production support geometry: pipes, cable runs, fence
  panels/posts, a generic platform/railing, beam, column, motor dressing and a
  generic industrial lamp.
- Best used at management-camera and normal operational distances.
- Materials and geometry read clearly after deterministic exposure was added.
- The assets are not sufficiently distinctive or accurate to replace custom
  process equipment at close range.

## Technical result

- 15 static meshes were curated with their material/texture dependencies.
- The contained vendor folder is approximately 482.5 MB and contains 84 assets.
- All 15 meshes loaded successfully in Unreal 5.8.
- Every curated mesh has at least one simple collision primitive. Complex items
  use up to four convex hulls; no collision was generated or altered during the
  audit.
- Useful LOD examples include cables (3,418 to 341 triangles), motor (2,540 to
  253), platform (484 to 242), column (5,104 to 510), and lamp (4,284 to 643).
- The 42,012-triangle assembly-line lamp and the pack's conventional crane hook
  were rejected for current production use.

Validation map:

`/Game/LineBoss/Developer/Validation/LB_FactoryPack_KitValidation`

Fixed-camera evidence:

`Saved/ValidationScreenshots/Vendor/factory_environment_shortlist_v001.png`

Audit evidence:

- `Saved/Audits/factory_pack_candidates_v001.json`
- `Saved/Audits/factory_pack_migration_v001.json`
- `Saved/Audits/factory_pack_collision_v001.json`

## Audio candidates

Six pack assets were migrated into:

`/Game/LineBoss/Vendor/FactoryEnvironment/Audio`

They remain candidates pending listening tests:

- `S_AssemblyLine`: 61.88 s stereo, possible distant hall ambience.
- `S_Motorized`: 2.01 s stereo, possible low-level machinery bed.
- `S_Ventilation`: 62.64 s stereo, possible HVAC zone ambience.
- `S_Welding`: 27.56 s stereo, reserved for the future Weld Shop.
- `Cue_AssemblyLine` and `Cue_Ventilation`: vendor cue structures for reference.

Machine actions will use custom state-driven layers. PR-005's sound contract is
`SourceAssets/PR005/pr005_audio_contract_v001.json`.

## Placement rule

Place these modules only after the authoritative machine footprint, maintenance
envelope, safety guarding, pedestrian route and interaction points are locked.
Vendor dressing must never obscure gameplay state or access.
