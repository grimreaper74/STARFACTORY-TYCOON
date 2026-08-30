"""Read-only comparison of approved StagePack and unapproved MaterialFlow imports.

This diagnostic exists solely to establish how UE 5.8 persisted the FBX
transform/pivot options.  It changes no assets, maps, or source files.
"""

from __future__ import annotations

import json
from pathlib import Path

import unreal


PROJECT_ROOT = Path(r"C:/Users/greg_/Projects/LineBossCarFactory_Unreal 5.8")
OUT = (PROJECT_ROOT / "Saved/Audits/OneFactory/Press/MaterialFlowPackRuntimePrep_v001/"
       "fbx_transform_probe_v001.json")
ASSETS = {
    "approved_stage_s03_frame": (
        "/Game/LineBoss/Factory/OneFactory/v001/Native/Press/"
        "SharedTrainModules_v003/Meshes/"
        "SM_CA_MW_PT_S03_Frame_Form_LOD0_v001."
        "SM_CA_MW_PT_S03_Frame_Form_LOD0_v001"
    ),
    "unapproved_materialflow_coil_cart": (
        "/Game/LineBoss/Factory/OneFactory/v001/Native/Press/"
        "MaterialFlowPack_v001/Meshes/SM_CA_MW_PT_S01CoilCart_v001."
        "SM_CA_MW_PT_S01CoilCart_v001"
    ),
}
PROPERTIES = (
    "import_uniform_scale",
    "convert_scene",
    "convert_scene_unit",
    "force_front_x_axis",
    "transform_vertex_to_absolute",
    "bake_pivot_in_vertex",
    "generate_lightmap_u_vs",
    "auto_generate_collision",
    "remove_degenerates",
)


def vector(value):
    return [round(float(value.x), 6), round(float(value.y), 6), round(float(value.z), 6)]


rows = {}
for label, object_path in ASSETS.items():
    asset = unreal.load_asset(object_path)
    if asset is None or not isinstance(asset, unreal.StaticMesh):
        rows[label] = {"object_path": object_path, "status": "MISSING"}
        continue
    import_data = asset.get_editor_property("asset_import_data")
    settings = {}
    for name in PROPERTIES:
        try:
            settings[name] = import_data.get_editor_property(name)
        except Exception as error:
            settings[name] = "UNAVAILABLE: {}".format(error)
    bounds = asset.get_bounding_box()
    rows[label] = {
        "object_path": object_path,
        "status": "PRESENT",
        "bounds": {"min": vector(bounds.min), "max": vector(bounds.max)},
        "dimensions": vector(bounds.max - bounds.min),
        "import_settings": settings,
    }

OUT.parent.mkdir(parents=True, exist_ok=True)
OUT.write_text(json.dumps({
    "$schema": "lineboss/onefactory/press/fbx-transform-probe/v1",
    "status": "PASS__READ_ONLY_DIAGNOSTIC",
    "map_opened_by_script": False,
    "map_saved_by_script": False,
    "assets": rows,
}, indent=2, sort_keys=True) + "\n", encoding="utf-8")
unreal.log("LINE_BOSS_PRESS_FBX_TRANSFORM_PROBE_PASS")
unreal.SystemLibrary.quit_editor()
