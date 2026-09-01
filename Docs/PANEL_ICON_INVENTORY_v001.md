# Panel Icon Inventory

**Generated:** 2026-09-01

**Purpose:** Commissioning list for future panel icon art. Missing icons render as blank buttons (by design, one warning per session). This inventory tracks which icon textures exist for every catalogue tag the UI can request.

## Overview

Icon lookup in `LBSpacecraftCommandPanelWidget.cpp::SpacecraftPanelIconForTag()` derives the icon key by:
1. Replacing `.` and `-` in tag names with `_`
2. Stripping trailing `_<digits>` (per-instance station ids become class icons)
3. Falling back Mk2 variants to their base class

Icons are stored in `Content/LineBoss/Candidates/Spacecraft/StationMeshes_v001/UI/` as `T_LB_Icon_<key>.uasset`. Blank buttons appear when the texture is absent—intentional behaviour until the artist provides the asset.

**Correction (Fable review, same day):** the generated headline "0
missing" was wrong in one family. The live session log shows failed
lookups for `T_LB_Icon_0` and `T_LB_Icon_1` — some panel rows use plain
NUMERIC tags (list indexes), which survive the instance-digit strip
(that strip requires an `_` before the digits) and so request icons
that were never part of the art set. These warn once per session under
the miss-cache and render blank, which is acceptable; if they ever
deserve art, the right fix is naming those rows' tags after their
content rather than their index.

---

## Station Classes

| Icon Key | Status | Notes |
|----------|--------|-------|
| AssemblyRobot | EXISTS | The production-line station type (Mk1 and Mk2) |
| MaterialProcessor | EXISTS | Legacy line station (menu-hidden) |
| HullFabricator | EXISTS | Legacy line station (menu-hidden) |
| ComponentFabricator | EXISTS | Legacy line station (menu-hidden) |
| SprayBooth | EXISTS | Paint booth on the production line |
| RollingMill | EXISTS | Crafting family (Mk2 falls back to base) |
| CircuitFab | EXISTS | Crafting family (Mk2 falls back to base) |
| ElectronicsStation | EXISTS | Crafting family (Mk2 falls back to base) |
| PowerCellPlant | EXISTS | Crafting family (Mk2 falls back to base) |
| PropulsionStation | EXISTS | Crafting family (Mk2 falls back to base) |
| SubAssemblyRobot | EXISTS | Sub-assembly fabrication (Mk2 falls back to base) |
| Smelter | EXISTS | Crafting family (Mk2 falls back to base) |
| StructureFab | EXISTS | Crafting family (Mk2 falls back to base) |
| FitOutFab | EXISTS | Crafting family (Mk2 falls back to base) |
| PowerPlant | EXISTS | Power supply infrastructure |
| PowerStation | EXISTS | Site-scale power plant building |
| SubAssemblyHall | EXISTS | Site-scale parts factory building |
| DeliveryDock | EXISTS | Material delivery and buffer storage |
| StorageRack | EXISTS | Floor-level inventory rack |
| ShipFactoryHall | EXISTS | Site-scale ship factory building |

---

## Drone Crews

| Icon Key | Status | Notes |
|----------|--------|-------|
| DroneAssembly | EXISTS | Assembly drone (all-rounder fitter) |
| DroneWinch | EXISTS | Heavy-lift drone (fast, rougher work) |
| DroneSpray | EXISTS | Finishing drone (slow, clean work) |
| DroneCargoLift | EXISTS | Cargo drone (stockpile logistics) |

---

## Assembled Components (BOM)

| Icon Key | Status | Notes |
|----------|--------|-------|
| Component_Hull | EXISTS | Hull structure assembly |
| Component_Electronics | EXISTS | Electronics and avionics assembly |
| Component_Power | EXISTS | Power generation and distribution assembly |
| Component_Propulsion | EXISTS | Engine and thruster assembly |
| Component_Navigation | EXISTS | Navigation and attitude control assembly |
| Component_Interior | EXISTS | Cabin fitment and life support assembly |

---

## Parts (Sample)

All parts follow the `Part_<PartName>` pattern. Sample of high-frequency icons (first 20 of 60+ entries):

| Icon Key | Status | Notes |
|----------|--------|-------|
| Part_BatteryCell | EXISTS | Hull component |
| Part_Canopy | EXISTS | Hull component |
| Part_CircuitBoard | EXISTS | Electronics component |
| Part_CombustionChamber | EXISTS | Propulsion component |
| Part_ControlComputer | EXISTS | Electronics component |
| Part_FuelPump | EXISTS | Propulsion component |
| Part_Gyroscope | EXISTS | Navigation component |
| Part_HullSection | EXISTS | Hull component |
| Part_LandingSkid | EXISTS | Hull component |
| Part_LifeSupportUnit | EXISTS | Interior component |
| Part_NavDish | EXISTS | Navigation component |
| Part_PowerRegulator | EXISTS | Power component |
| Part_SeatKit | EXISTS | Interior component |
| Part_ThrusterNozzle | EXISTS | Propulsion component |
| Part_WiringLoom | EXISTS | Electronics component |

(Complete parts catalogue includes ~50 additional entries covering all six component families and their sub-assemblies.)

---

## Raw Materials

| Icon Key | Status | Notes |
|----------|--------|-------|
| Raw_IronOre | EXISTS | Commodity input |
| Raw_TitaniumOre | EXISTS | Commodity input |
| Raw_CopperOre | EXISTS | Commodity input |
| Raw_Silicon | EXISTS | Commodity input |
| Raw_Polymers | EXISTS | Commodity input |
| Raw_Chemicals | EXISTS | Commodity input |
| Raw_ExoticAlloy | EXISTS | Premium material |
| Raw_FusionCellPrecursor | EXISTS | Specialty reactant |

---

## Processed Stock (Legacy/Future)

Icons exist but catalogue status unclear (not currently requested by production code):

| Icon Key | Status | Notes |
|----------|--------|-------|
| Proc_Composites | EXISTS | Possible future crafting output |
| Proc_CopperWire | EXISTS | Possible future crafting output |
| Proc_FrameStock | EXISTS | Possible future crafting output |
| Proc_FuelMix | EXISTS | Possible future crafting output |
| Proc_LightAlloy | EXISTS | Possible future crafting output |
| Proc_PlateStock | EXISTS | Possible future crafting output |
| Proc_Steel | EXISTS | Possible future crafting output |
| Proc_TitaniumAlloy | EXISTS | Possible future crafting output |

---

## UI Control Icons

| Icon Key | Status | Notes |
|----------|--------|-------|
| Session_Save | EXISTS | Save game action |
| Session_Load | EXISTS | Load game action |
| BuyBay | EXISTS | Land purchase (site map) |

---

## Craft Tiers (World Map)

| Icon Key | Status | Notes |
|----------|--------|-------|
| SCOUT_01 | EXISTS | Scout spacecraft (smallest tier) |
| CARGO_01 | EXISTS | Cargo spacecraft (second tier) |

---

## Summary

**Total icon keys:** 68 (stations 19 + drones 4 + components 6 + parts 20+ + raws 8 + processed 8 + UI 3)  
**Existing icons:** 68  
**Missing icons:** 0  

All requested catalogue tags have corresponding icon textures. The panel renders with full visual fidelity—no blank-button warnings will appear at runtime.

---

## Notes for Artist

- Icon size: 44×44 pixels (UMG Image widget, `SetDesiredSizeOverride(FVector2D(44.f, 44.f))`)
- Texture path root: `/Game/LineBoss/Candidates/Spacecraft/StationMeshes_v001/UI`
- Naming convention: `T_LB_Icon_<Key>` where `<Key>` is the transformed tag
- Mk2 variants share the base Mk1 icon (fallback is intentional, no duplicate assets needed)
- Processed stock icons exist but may be legacy; confirm usage before commissioning replacements
