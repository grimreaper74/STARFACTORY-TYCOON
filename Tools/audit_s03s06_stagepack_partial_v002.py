"""Read-only forensic report for the intentionally preserved failed v002 intake."""

import io
import json
import os

import unreal


PROJECT_ROOT = r"C:/Users/greg_/Projects/LineBossCarFactory_Unreal 5.8"
DESTINATION = (
    "/Game/LineBoss/Factory/OneFactory/v001/Native/Press/"
    "SharedTrainModules_v002"
)
OUTPUT = (
    PROJECT_ROOT + "/Saved/Audits/OneFactory/Press/"
    "S03S06StagePackRuntimePrep_v001/partial_v002_geometry_audit.json"
)


def mesh_row(mesh, mesh_editor):
    bounds = mesh.get_bounding_box()
    size = bounds.max - bounds.min
    lod_count = int(mesh.get_num_lods())
    row = {
        "object_path": mesh.get_path_name(),
        "lod_count": lod_count,
        "triangles_by_lod": [int(mesh.get_num_triangles(index)) for index in range(lod_count)],
        "vertices_by_lod": [int(mesh.get_num_vertices(index)) for index in range(lod_count)],
        "uv_channels_by_lod": [
            int(mesh_editor.get_num_uv_channels(mesh, index))
            for index in range(lod_count)
        ],
        "bounds_cm": [round(size.x, 3), round(size.y, 3), round(size.z, 3)],
        "static_material_slots": [str(slot.material_slot_name) for slot in mesh.static_materials],
        "light_map_coordinate_index": int(mesh.get_editor_property("light_map_coordinate_index")),
        "light_map_resolution": int(mesh.get_editor_property("light_map_resolution")),
        "nanite_enabled": bool(mesh.get_editor_property("nanite_settings").enabled),
    }
    if hasattr(mesh_editor, "get_num_sections"):
        row["sections_by_lod"] = [
            int(mesh_editor.get_num_sections(mesh, index))
            for index in range(lod_count)
        ]
    return row


if os.path.exists(OUTPUT):
    raise RuntimeError("refusing to overwrite forensic report: {}".format(OUTPUT))
if not unreal.EditorAssetLibrary.does_directory_exist(DESTINATION):
    raise RuntimeError("preserved partial destination is absent: {}".format(DESTINATION))
unreal.AutomationUtilsBlueprintLibrary.finish_all_asset_compilation()
mesh_editor = unreal.get_editor_subsystem(unreal.StaticMeshEditorSubsystem)
if mesh_editor is None or not hasattr(mesh_editor, "get_num_uv_channels"):
    raise RuntimeError("StaticMeshEditorSubsystem UV introspection is unavailable")

rows = []
for asset_path in unreal.EditorAssetLibrary.list_assets(
        DESTINATION, recursive=True, include_folder=False):
    asset = unreal.load_asset(asset_path)
    if isinstance(asset, unreal.StaticMesh):
        rows.append(mesh_row(asset, mesh_editor))
rows.sort(key=lambda row: row["object_path"])
os.makedirs(os.path.dirname(OUTPUT), exist_ok=True)
with io.open(OUTPUT, "w", encoding="utf-8") as handle:
    handle.write(json.dumps({
        "schema": "lineboss/onefactory/press/s03s06-stagepack-partial-v002-forensic/v1",
        "status": "FORENSIC__READ_ONLY_PARTIAL_IMPORT_GEOMETRY_MEASURED",
        "destination": DESTINATION,
        "mutated_content": False,
        "meshes": rows,
    }, indent=2, sort_keys=True) + "\n")
unreal.log("LINE_BOSS_S03S06_PARTIAL_V002_FORENSIC=" + OUTPUT)
