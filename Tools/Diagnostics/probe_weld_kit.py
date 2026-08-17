"""Measure the weld fabric kit before placing any of it.

The plant plan specifies platform, gantry, glazing and racking sizes from process
reasoning rather than from asset bounds, and flags that as uncertainty U-2: "every
vendor mesh in this plan needs one calibration pass before placement counts are
trusted." Pitching a mezzanine or a gantry run off a guessed length produces either
gaps or overlaps across a 165 m hall, so measure once here.
"""
import io
import json
import os

import unreal

OUT = os.environ.get("LB_WELD_KIT_OUT", "C:/Temp/lb_weld_kit.json")

MESHES = [
    # Mezzanine over the central service aisle - none exists anywhere in the project.
    "/Game/LineBoss/Vendor/FactoryEnvironment/Meshes/SM_IndustrialPlatform01",
    "/Game/LineBoss/Vendor/FactoryEnvironment/Meshes/SM_PlatformRailing_01",
    "/Game/Meshes/SM_IndustrialPlatform02",
    "/Game/Meshes/SM_IndustrialPlatform03",
    "/Game/Meshes/SM_PlatformGrill_01",
    "/Game/Meshes/SM_PlatformPillar_01",
    "/Game/Meshes/SM_FloorStairs01",
    # Shop-scale gantries over runs A and B.
    "/Game/Meshes/SM_HeavyArch01",
    "/Game/Meshes/SM_HeavyArch02",
    "/Game/Meshes/SM_LampArch01",
    # Clerestory glazing, currently a tinted opaque cube band.
    "/Game/Meshes/SM_LargeWindowFramed",
    "/Game/Meshes/SM_LargeWindowFramed_02",
    # Marshalling racks: only the Bottom piece is wired today.
    "/Game/Meshes/SM_StorageShelvesBottom01",
    "/Game/Meshes/SM_StorageShelvesMiddle01",
    "/Game/Meshes/SM_StorageShelvesTop01",
    # South switchroom line.
    "/Game/Meshes/SM_ElectricalPanel_01",
    "/Game/Meshes/SM_ElectricalSupply_Switchboard01",
    # Authored Cairnwell closures to hang on the closure line.
    "/Game/LineBoss/Factory/OneFactory/v001/Vehicles/Cairnwell2040PanelModules_v001/"
    "Meshes/SM_LB_C2040_DOOR_FRONT_LEFT_v001",
    "/Game/LineBoss/Factory/OneFactory/v001/Vehicles/Cairnwell2040PanelModules_v001/"
    "Meshes/SM_LB_C2040_ROOF_PANEL_v001",
    "/Game/LineBoss/Candidates/WeldShop/ClosureTurntable_v001/"
    "SM_LB_BodyShop_ClosureTurntable_v001",
    "/Game/LineBoss/Candidates/WeldShop/BodyShopUnderbodySlice_v001/Vision/"
    "SM_LB_BodyShop_VisionGate_v001",
    "/Game/LineBoss/Candidates/Vehicles/Cairnwell2040/BIWBaseKitRuntime_v001/Carrier/"
    "SM_LB_C2040_BIWBaseSkid_v001",
]

report = []
for path in MESHES:
    mesh = unreal.load_asset(path)
    if mesh is None:
        report.append({"name": path.rsplit("/", 1)[-1], "missing": True})
        continue
    box = mesh.get_bounding_box()
    size = box.max - box.min
    report.append({
        "name": path.rsplit("/", 1)[-1],
        "path": path,
        "size_cm": [round(size.x, 1), round(size.y, 1), round(size.z, 1)],
        "min_z": round(box.min.z, 1),
        "slots": len(mesh.static_materials),
    })

with io.open(OUT, "w", encoding="utf-8") as handle:
    handle.write(json.dumps(report, indent=1))
unreal.log("LINE_BOSS_WELD_KIT measured {} of {} -> {}".format(
    sum(1 for r in report if not r.get("missing")), len(MESHES), OUT))
