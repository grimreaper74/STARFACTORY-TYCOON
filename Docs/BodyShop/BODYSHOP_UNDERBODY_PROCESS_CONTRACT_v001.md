# Body Shop underbody process contract v001

Status: frozen first-slice data contract. This document does not claim that every future joining process has a commissioned machine in the current map.

## Product identity

One pilot genealogy unit remains `BIW_UNDERBODY` from component-kit presentation through output-buffer release. Components and completed process steps are recipe detail, not separate saved WIP objects. This preserves the existing experimental save v1 shape and does not touch campaign v18.

## Stable component IDs

| ID | Rule |
| --- | --- |
| `UBC_FLOOR_PAN` | required |
| `UBC_CENTRE_TUNNEL` | exactly one centre-structure choice |
| `UBC_EV_BATTERY_TRAY` | exactly one centre-structure choice |
| `UBC_LONGITUDINAL_RAIL_LEFT` | required |
| `UBC_LONGITUDINAL_RAIL_RIGHT` | required |
| `UBC_CROSSMEMBERS` | required crossmember set |
| `UBC_SIDE_SILL_LEFT` | required |
| `UBC_SIDE_SILL_RIGHT` | required |
| `UBC_FRONT_FLOOR_PARTITION` | optional |
| `UBC_REAR_FLOOR_PARTITION` | optional |

The centre choice group is `UB_ALT_CENTRE_STRUCTURE`. A valid kit contains either the centre tunnel or EV battery tray, never neither or both. The canonical first slice omits the optional partitions; adding either or both remains valid.

Canonical recipe IDs are `UBR_UNDERBODY_TUNNEL_PILOT_V001` and `UBR_UNDERBODY_EV_TRAY_PILOT_V001`. Both release the same `BIW_UNDERBODY` material identity.

## Joining and inspection

The commissioned first-slice cell requires `UBJ_RESISTANCE_SPOT_WELD`, matching its two spot-welding robots and C-guns.

The stable catalogue also reserves authored fixture variants for `UBJ_LASER_WELD_OR_BRAZE`, `UBJ_MIG_MAG_WELD` and `UBJ_ADHESIVE_BOND`. `UBJ_SELF_PIERCING_RIVET` is an optional material-specific operation. These IDs do not imply that the current pilot owns laser, MIG/MAG, adhesive-dispensing or riveting equipment.

Every released pilot underbody must pass:

1. `UBQ_DEBURR_AND_FINISH`
2. `UBQ_DIMENSIONAL_ALIGNMENT`
3. `UBQ_WELD_INTEGRITY`

An EV battery-tray leak test belongs to a later equipped recipe and is not silently simulated by the current basic vision gate.

## First-slice process order

| Order | Stable step ID | First-slice cell responsibility |
| --- | --- | --- |
| 1 | `UB_STEP_PRESENT_COMPONENT_KIT` | full-stillage dock and panel presentation/destacking cell |
| 2 | `UB_STEP_LOCATE_IN_FIXTURE` | underbody fixture |
| 3 | `UB_STEP_JOIN_PRIMARY_STRUCTURE` | underbody fixture with two C-gun robot slots |
| 4 | `UB_STEP_TRANSFER_ON_SKID` | straight skid conveyor |
| 5 | `UB_STEP_DEBURR_AND_FINISH_CHECK` | collapsed pilot quality check |
| 6 | `UB_STEP_DIMENSIONAL_CHECK` | basic vision gate |
| 7 | `UB_STEP_WELD_INTEGRITY_CHECK` | collapsed pilot quality check |
| 8 | `UB_STEP_RELEASE_BIW_UNDERBODY` | output buffer |

The present visual may use one consolidated underbody mesh, but the recipe contract treats it as a kit assembled into one persistent WIP identity. A later art pass may split that mesh into the stable component IDs without changing genealogy or saves.

## Player and robot boundary

The player places and connects fixture cells, conveyors, stillage docks and buffers. Within a cell the player chooses from validated robot slots, roles and tools and can inspect reach/sweep overlays. Safety fencing, interlocked gates and basic services remain automatic cell dressing. The contract rejects unrestricted six-axis robot placement or path programming.

Robot motion should be authored by role and slot: the handling robot presents the kit, while the two welding robots use separate, coordinated fixture poses. The shared robot actor may supply mechanics, but every robot should not repeat the same rear-bin-to-car animation.

## Code and tests

Definitions and pure validation live in:

- `Source/LineBossCarFactory/LBBodyShopUnderbodyProcess.h`
- `Source/LineBossCarFactory/LBBodyShopUnderbodyProcess.cpp`

Focused automation tests live in `Source/LineBossCarFactory/LBBodyShopUnderbodyProcessTests.cpp`:

- `LineBoss.BodyShop.Experimental.UnderbodyProcess.StableCatalogV1`
- `LineBoss.BodyShop.Experimental.UnderbodyProcess.KitSelectionV1`
- `LineBoss.BodyShop.Experimental.UnderbodyProcess.FixtureProcessV1`

These files are Body-Shop-only and non-persistent. They do not modify the experimental save schema, campaign saves, Press Shop, legacy Body Weld composite, maps, Content or Config.
