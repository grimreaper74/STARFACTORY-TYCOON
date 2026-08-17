"""Read-only probe of the real assets the authored site will use.

Measures every candidate mesh's bounding box so placement pitches come from the
asset instead of a guess, and lists the material parameters available on the
ground materials so tinted variants can be created without trial and error.
Places nothing and saves nothing.
"""
import io
import json
import os

import unreal

OUT = os.environ.get("LB_PROBE_OUT", "C:/Temp/lb_probe.json")
REPORT = {"meshes": [], "materials": []}

MESHES = [
    "/Game/LineBoss/Vendor/FactoryEnvironment/Meshes/SM_Fence_01",
    "/Game/LineBoss/Vendor/FactoryEnvironment/Meshes/SM_FencePart_01",
    "/Game/Meshes/SM_GateDoor01",
    "/Game/Meshes/SM_GateBorder01",
    "/Game/Meshes/SM_GateBorder02",
    "/Game/Meshes/SM_Container01_01",
    "/Game/Meshes/SM_Container01_02",
    "/Game/Meshes/SM_ContainerP4_01",
    "/Game/Meshes/SM_ConcreteWall",
    "/Game/Meshes/SM_ConcreteFloor_01",
    "/Game/Meshes/SM_ConcretePillar01",
    "/Game/Meshes/SM_FactoryFloorLarge01",
    "/Game/Meshes/SM_Floor2m",
    "/Game/Meshes/SM_FloorDrainage01",
    "/Game/Meshes/SM_Background2_Hangar",
    "/Game/Meshes/SM_Background2_BoxBuilding",
    "/Game/Meshes/SM_Background2_BoxBuildingBase",
    "/Game/Meshes/SM_Background2_Bridge",
    "/Game/Meshes/SM_Background1_Tower01",
    "/Game/Meshes/SM_Background1_Tower02",
    "/Game/Meshes/SM_Background1_Tower03",
    "/Game/Meshes/SM_Background1_Tower04",
    "/Game/Meshes/SM_Background1_AntennaTower",
    "/Game/Meshes/SM_CrashAreaSpotlight_01",
    "/Game/Meshes/SM_CargoCar/SM_CargoCart01",
    "/Game/LineBoss/Candidates/PressShop/CleanRebuild_v20260809_v004/Inbound/"
    "SM_CA_MW_InboundLorry_Approved_v006",
    "/Game/LineBoss/IndustrialKit/InboundCoilDelivery/Candidate_v005/"
    "SM_CA_MW_MOD_LorryCab_v005",
    "/Game/LineBoss/IndustrialKit/InboundCoilDelivery/Candidate_v005/"
    "SM_CA_MW_MOD_CoilTrailer_v005",
    "/Engine/BasicShapes/Plane",
]

MATERIALS = [
    "/Game/LineBoss/Materials/Environment/M_LB_SealedFactoryConcrete_World_v001",
    "/Game/LineBoss/Materials/Environment/MI_LB_SealedFactoryConcrete_Neutral_v001",
    "/Game/Materials/MI_FactoryConcreteFloor01",
    "/Game/Materials/MI_ConcreteFloor_02",
    "/Game/Materials/MI_ConcreteFloor_03",
    "/Game/LineBoss/Materials/FrontEnd/MI_LB_Floor_Neutral",
    "/Game/LineBoss/Materials/FrontEnd/MI_LB_Floor_Walkway_Green",
    "/Game/LineBoss/Materials/FrontEnd/M_LB_FrontEndPaintedConcrete_Master",
]


for path in MESHES:
    mesh = unreal.load_asset(path)
    if mesh is None:
        REPORT["meshes"].append({"path": path, "missing": True})
        continue
    box = mesh.get_bounding_box()
    size = box.max - box.min
    slots = mesh.static_materials if hasattr(mesh, "static_materials") else []
    REPORT["meshes"].append({
        "name": path.rsplit("/", 1)[-1],
        "path": path,
        "size": [round(size.x, 1), round(size.y, 1), round(size.z, 1)],
        "min": [round(box.min.x, 1), round(box.min.y, 1), round(box.min.z, 1)],
        "slots": len(slots),
    })

for path in MATERIALS:
    asset = unreal.load_asset(path)
    if asset is None:
        REPORT["materials"].append({"path": path, "missing": True})
        continue
    name = path.rsplit("/", 1)[-1]
    try:
        scalars = unreal.MaterialEditingLibrary.get_scalar_parameter_names(asset)
        vectors = unreal.MaterialEditingLibrary.get_vector_parameter_names(asset)
        textures = unreal.MaterialEditingLibrary.get_texture_parameter_names(asset)
    except Exception as error:  # noqa: BLE001 - report and continue probing
        REPORT["materials"].append({"name": name, "error": str(error)})
        continue
    parent = ""
    if isinstance(asset, unreal.MaterialInstance):
        parent_asset = asset.get_editor_property("parent")
        parent = parent_asset.get_name() if parent_asset else "<none>"
    REPORT["materials"].append({
        "name": name,
        "parent": parent,
        "scalars": [str(s) for s in scalars],
        "vectors": [str(v) for v in vectors],
        "textures": [str(t) for t in textures],
    })


with io.open(OUT, "w", encoding="utf-8") as handle:
    handle.write(json.dumps(REPORT, indent=1))
unreal.log("LINE_BOSS_PROBE wrote {} mesh and {} material records to {}".format(
    len(REPORT["meshes"]), len(REPORT["materials"]), OUT))
