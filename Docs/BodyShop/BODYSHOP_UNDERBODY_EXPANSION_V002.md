# Body Shop underbody expansion v002

Status: source-level process and topology contract. It is intentionally separate from the verified six-cell `Experimental_v001` runtime, map and save.

## Why this is separate

The first playable slice has one authoritative WIP, one runtime-owned stillage, six exact cells and a proven package/save/restart/load chain. Adding decorative stations or duplicate stillages to that graph would make the screenshot denser but make the manufacturing state untrue. The v001 cells, IDs, topology validator and save contract therefore remain unchanged.

The v002 chain starts with real material states, an explicit centre-structure architecture and an explicit quality branch. A station is not eligible for the expanded playable map until its runtime consumes and produces the exact material IDs below and its save reconstructs the same stage.

The station IDs end in `_V001` deliberately: they are revision 1 of each new station definition inside expansion contract v002. They do not identify or replace an `Experimental_v001` cell.

## Stable architecture choice

One expanded topology is configured as exactly one of:

- `CentreTunnel`, containing `UBC_CENTRE_TUNNEL` and excluding `UBC_EV_BATTERY_TRAY`.
- `EVBatteryTray`, containing `UBC_EV_BATTERY_TRAY` and excluding `UBC_CENTRE_TUNNEL`.

Every station in a topology carries the same architecture. The primary kit contains the floor pan, selected centre structure, both longitudinal rails, crossmembers, and the front/rear floor partitions. Side sills are not part of that material state: they enter once through the dedicated `SILL_KIT_IN` input at side-sill joining. Front/rear partitions are presented and then explicitly processed by main joining, so they cannot be counted and subsequently orphaned.

The station process-step arrays use only the existing stable IDs from `LBBodyShopUnderbodyProcess` and collectively cover every stable recipe step. Inspection owns both dimensional and weld-integrity steps; rework owns joining and deburr/finish steps; the pass buffer owns skid transfer and final release.

## Approved station chain

| Catalogue order | Stable station ID | Exact responsibility | Output material |
| --- | --- | --- | --- |
| 1 | `BWU000_COMPONENT_KIT_PRESENTATION_V001` | Present the architecture-specific primary kit; no side-sill ownership | `UBW_PRIMARY_KIT_PRESENTED` |
| 2 | `BWU001_RAIL_CROSSMEMBER_PREP_V001` | Prepare and locate both longitudinal rails and the crossmember set | `UBW_PRIMARY_STRUCTURE_PREPARED` |
| 3 | `BWU002_MAIN_UNDERBODY_JOIN_V001` | Join floor pan, selected centre, rails, crossmembers, and front/rear partitions | `UBW_PRIMARY_STRUCTURE_JOINED` |
| 4 | `BWU003_SIDE_SILL_ROCKER_JOIN_V001` | Consume the separate left/right side-sill kit and join it once | `UBW_SIDE_SILLS_JOINED` |
| 5 | `BWU004_DEBURR_FINISH_V001` | Deburr and finish the joined structure | `UBW_FINISH_CHECKED` |
| 6 | `BWU005_UNDERBODY_INSPECTION_V001` | Dimensional and weld-integrity inspection | pass: `BIW_UNDERBODY`; fail: `UBW_REWORK_HOLD` |
| 7 | `BWU006_UNDERBODY_REWORK_V001` | Correct failed joining/finish work and return it for inspection | `UBW_REINSPECT_READY` |
| 8 | `BWU007_PASS_BUFFER_V001` | Hold only inspection-passed underbodies | retained `BIW_UNDERBODY` |

The inventory contains seven stations on the main +X route and one adjacent rework station. The rework station sits beside inspection on the -Y side. `REWORK_OUT/REWORK_IN` and `REINSPECT_OUT/REINSPECT_IN` are distinct, exactly coincident and fully opposed port pairs; the rework route cannot bypass inspection.

The eight stable connection identities are `BWU_CONN_001` through `BWU_CONN_008` in numeric order. Approved validation compares every connection ID, source station/port and target station/port in that exact order, then validates the supplied station ports rather than substituting canonical port data.

## Layout, fences and shared envelopes

Physical station footprints do not overlap. Consecutive footprints meet at their exact conveyor connection plane, allowing one continuous skid route without a black fixture frame between stations.

Each maintenance envelope is 200 cm wider than the associated footprint in X and Y. The resulting 200 cm overlap between neighbouring envelopes is deliberate and denotes a shared guarded transfer/service interface, not space that two cells may independently occupy during simultaneous maintenance. Future runtime commissioning must interlock adjacent maintenance access across a shared interface. Fences and doors should surround the combined guarded zone and must not be placed through a coincident port plane. Because layout and station dimensions are exact canonical fields, arbitrary extra overlap fails validation.

## Parts containers and WIP truth

- The v001 pilot may show only its one runtime-owned live panel stillage. Dock capacity does not authorize extra copies.
- The validated panel-stillage asset remains the future production-container basis, but multiple full/empty stillages require v002 inventory identity and ownership.
- Licensed vendor pallet carts, open boxes, plastic pallets and small crates may be promoted as clearly empty service-apron props after an isolated visual/cook gate. They are not process WIP and cannot satisfy station material inputs.
- The rejected Meshy underbody split is not a station-parts source. Its branches are unrelated alternate generations with world-zero origins and no semantic names, LODs or collision.
- Semantic rail/crossmember/sill workpieces should be derived from the validated procedural underbody builder, preserving common coordinates, before the first two v002 stations are commissioned.

## Implementation order

1. Freeze and test this process/topology contract for both architectures.
2. Derive aligned semantic primary-kit meshes from the validated procedural underbody source.
3. Implement `BWU000` and `BWU001` with exact WIP consumption, architecture, progress and save reconstruction.
4. Add main joining and the separately supplied side-sill joining stage.
5. Add finish, inspection, pass buffer and conditional rework routing.
6. Only then create the expanded map and capture/package it. The verified v001 Early Access slice remains available throughout.

Source contract:

- `Source/LineBossCarFactory/LBBodyShopUnderbodyExpansionV2.h`
- `Source/LineBossCarFactory/LBBodyShopUnderbodyExpansionV2.cpp`
- `Source/LineBossCarFactory/LBBodyShopUnderbodyExpansionV2Tests.cpp`

Automation names:

- `LineBoss.BodyShop.Experimental.UnderbodyExpansionV2.StableCatalog`
- `LineBoss.BodyShop.Experimental.UnderbodyExpansionV2.ApprovedTopology`
- `LineBoss.BodyShop.Experimental.UnderbodyExpansionV2.FailClosed`
