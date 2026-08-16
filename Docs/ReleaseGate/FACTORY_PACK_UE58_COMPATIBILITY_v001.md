# Factory Environment Collection — UE 5.8 compatibility

Snapshot: **2026-08-16**. Found while packaging, not while importing: the pack
imports and renders cleanly in the editor, and only fails at cook. Companion to
[Third-party asset pack licensing](THIRD_PARTY_ASSET_PACK_LICENSING_v001.md).

## Position

**The static meshes are sound. The rigged content and two render-target
materials are not.** Everything Line Boss uses is a static mesh, so the pack is
usable — but anyone reaching for its forklift, loader, crane or robot animations
should expect to fix them first.

## What is broken

| Asset | Failure |
|---|---|
| `SK_ForkLift_Skeleton_AnimBlueprint` | `Failed to load Class /Script/PhysXVehicles.VehicleAnimInstance` |
| `SK_Loader_Skeleton_AnimBlueprint` | Same |
| `AB_IK_RobotArm` | `Can't connect pins ... invalid target type`, `Bad cast node`, missing variable `x0` |
| `SK_Loader` | Bad tangents; asset asks to be re-imported |
| `M_RenderTarget`, `M_Mirror_RenderTarget` | `Failed to compile Material for PCD3D_SM5 and SM6` |

`PhysXVehicles` was **removed in UE5** and replaced by Chaos Vehicles, so those
two anim blueprints cannot load at all. This is a UE4-era pack; the failures are
version drift, not corruption.

## What was done

The cook is configured to skip what is broken and unused, rather than the assets
being altered:

- Twelve skeletal families are in `DirectoriesToNeverCook`: `CargoCar`,
  `Clutch`, `Crane`, `Drone`, `FireBox`, `ForkLift`, `Loader`, `Mannequin`,
  `Robot`, `RobotLarge`, `ScissorsLift`, `Truck`. None is referenced by Line
  Boss, and excluding them also drops a large share of the 6 GB texture load.
- The two render-target materials are **moved, not deleted**, to
  `SourceAssets/Quarantine/FactoryPack_UE4Legacy_NotCookable/`. Nothing under
  `Source` references them and they do not compile, so nothing functional is
  lost. Moving them back restores the original pack state exactly.

## Why this only appeared at cook

Two traps worth remembering, because neither shows up in the editor:

1. **`StaticLoadObject` with a path string is invisible to the cooker.** The
   station dressing resolves pack meshes that way, so the first packaged build
   would have shipped with no machinery at all and looked like a regression
   rather than a missing cook rule. `/Game/Meshes`, `/Game/Materials`,
   `/Game/Textures` and `/Game/Fx` are now in `DirectoriesToAlwaysCook`.
2. **Broken blueprints cook-fail silently in the editor.** They load, they draw,
   they simply cannot be cooked. An editor-only workflow never discovers this.

## If the rigged content is wanted later

The forklift and loader need their vehicle animation rebuilt on Chaos Vehicles,
and `AB_IK_RobotArm` needs its cast nodes and variable bindings repaired against
the current Blueprint API. Neither is required for the current factory: the
dressing drives static meshes and the robots do not animate yet. Animating them
is a deliberate piece of work, not a fix.
