# OneFactory — audit and the switch to real assets, 2026-08-16

Written during the autonomous session, after the first packaged journeys.

## The packaged milestone, first

Packaged build `PlayableShell_v002` (E:, 4.7 GB, Development) ran the complete
player journey outside the editor:

```
LINE_BOSS_PLAYER_COMMISSION  WHOLE FACTORY CREATED, COMMISSIONED AND VALIDATED
CAIRNWELL_2040-000001  Body/BodyQualityInspection  OF_BODY_WELD_POS_16  [AWAITING QA]
LINE_BOSS_PLAYER_QUALITY_PASS ok=1 ... RECORDED WITHOUT DUPLICATING WIP
CAIRNWELL_2040-000001  Paint/ColourCoat  OF_PAINT_SPRAY_BOOTH_001  29/57
```

All eight commission steps green, a car held at the weld quality gate, a player
decision released it into paint. Under the release vocabulary this makes the
OneFactory shell journey **packaged playable** for the exercised path, with
visual acceptance, real-input QA and performance still open.

## What the audit found

The central finding repeats the session's theme: **the work already existed and
was not connected.**

1. **The WIP chain's real assets were already imported.** The guarded lanes of
   2026-08-15 delivered the Cairnwell 2040 BIW skeleton and Emerald body visual
   authorities with authored PBR materials, the runtime panel stillage, and the
   repaired wrapped coil. The WIP presentation was drawing tinted engine
   primitives while real car bodies sat unused in Content.
2. **26 soft-referenced content paths were invisible to the cooker.**
   Presentations resolve meshes by path string, which the cooker cannot trace.
   The packaged Paint starter rolled back for a missing kit, and Assembly would
   have followed. Five runtime-critical paths are now in
   `DirectoriesToAlwaysCook`; the rest are validation content that should stay
   uncooked.
3. **The Factory pack's rigged content is UE4-era and cannot cook** — recorded
   in [the pack compatibility note](../ReleaseGate/FACTORY_PACK_UE58_COMPATIBILITY_v001.md).
   Static meshes are sound; twelve skeletal families are excluded and two
   render-target materials quarantined.
4. **The fail-closed contracts earned their keep in package.** The paint
   starter's atomic rollback caught the missing-content defect cleanly - data
   and presentation rolled back together, one legible error line.

## What changed

The moving WIP now renders the real assets at true scale, authored materials
kept:

| Stages | Asset |
|---|---|
| Inbound coil, blank prep | `SM_CA_MW_WrappedCoil_Repaired_v003` |
| Pressing, stillage | `SM_LB_PanelStillage_Runtime_v001` |
| Body framing to inspection | `SM_LB_C2040_BIW_AutomotiveSkeleton_v001` (galvanized) |
| Pretreatment, ED coat | same skeleton with authored `M_LB_C2040_EDCoat_v001` |
| Colour coat to dispatch | `SM_LB_C2040_EmeraldBodyVisualAuthority_v001` (paint-tint PBR) |

Verified live: a stillage-stage unit renders the welded stillage frame; four BIW
shells occupied weld positions 04–09; no mesh resolution failures.

## Flags for the ledger

- The repaired coil is **1.9M triangles, one LOD**. Fine for the one or two
  inbound units on screen; wants LODs before any performance pass.
- The packaged keyboard bindings (B/N/Space/1-3/Q/R) are exercised via their
  Exec handlers, which proves the logic but not the physical key path. The game
  window is a loose exe the desktop-automation allowlist cannot resolve by
  name, so real-key QA remains a manual item.
- `GameDefaultMap` still points at the press-shop map, so the packaged exe must
  be launched with the Moorcross map argument. Deciding the shipped default map
  is a product decision, not a code one.

## Next

1. Decide the packaged default map and set it deliberately.
2. Run the finish checklist on `PlayableShell_v003` (real-car build).
3. LODs for the coil; then the performance capture the gate requires.
4. Manual pass on the physical keys in the packaged build.
