"""Re-import Codex detail-uplift drops over the existing assets.

Scans SourceAssets/Candidate/DetailUplift_v001 for model folders whose
FBX matches an existing /Game/LineBoss static mesh by name, and imports
each over the original package path so every placed instance updates in
place. Slot materials are recorded before import and reapplied by slot
name after, so reworked meshes keep their bound brand materials. Reports
per model: old/new triangle counts, footprint delta, slots rebound.
Safe to rerun as drops accumulate. Run with -ExecutePythonScript.
"""
import json
import os

import unreal

SRC = (r"C:/Users/greg_/Projects/LineBossCarFactory_Unreal 5.8"
       r"/SourceAssets/Candidate/DetailUplift_v001")
OUT = "C:/Temp/lb_detail_uplift.json"

registry = unreal.AssetRegistryHelpers.get_asset_registry()
filt = unreal.ARFilter(
    class_paths=[unreal.TopLevelAssetPath("/Script/Engine", "StaticMesh")],
    package_paths=["/Game/LineBoss"], recursive_paths=True)
PACKAGES = {}
for data in registry.get_assets(filt):
    PACKAGES[str(data.asset_name)] = str(data.package_name)

tools = unreal.AssetToolsHelpers.get_asset_tools()
REPORT = {"updated": {}, "skipped": []}

# Codex drops occasionally drift from the original names; map them back.
ALIASES = {
    "LB_WeldRobot_SharedBase_LOD0_v001": "SM_LB_WeldRobot_SharedBase_v001",
    "LB_WeldTool_MIG_LOD0_v001": "SM_LB_WeldTool_MIG_v001",
    "LB_WeldTool_PanelPick_LOD0_v001": "SM_LB_WeldTool_PanelPick_v001",
    "LB_WeldTool_SpotGun_LOD0_v001": "SM_LB_WeldTool_SpotGun_v001",
    "SM_LB_Conveyor_SkilletDeckPlate_v001":
        "SM_LB_Assembly_SkilletDeckPlate_v001",
}

for folder in sorted(os.listdir(SRC)):
    fbx = os.path.join(SRC, folder, folder + ".fbx")
    if not os.path.isfile(fbx):
        REPORT["skipped"].append(folder + " (no fbx)")
        continue
    target = ALIASES.get(folder, folder)
    package = PACKAGES.get(target)
    if package is None:
        REPORT["skipped"].append(folder + " (no existing asset)")
        continue
    mesh = unreal.load_asset(package)
    if mesh is None:
        REPORT["skipped"].append(folder + " (asset failed to load)")
        continue

    old_box = mesh.get_bounding_box()
    old_size = old_box.max - old_box.min
    old_tris = mesh.get_num_triangles(0)
    saved_slots = {}
    for entry in mesh.get_editor_property("static_materials"):
        slot = str(entry.get_editor_property("material_slot_name"))
        saved_slots[slot] = entry.get_editor_property("material_interface")

    options = unreal.FbxImportUI()
    options.set_editor_property("import_mesh", True)
    options.set_editor_property("import_materials", False)
    options.set_editor_property("import_textures", False)
    options.set_editor_property("import_as_skeletal", False)
    options.static_mesh_import_data.set_editor_property(
        "combine_meshes", True)
    task = unreal.AssetImportTask()
    task.set_editor_property("filename", fbx)
    task.set_editor_property("destination_path",
                             package.rsplit("/", 1)[0])
    task.set_editor_property("destination_name", target)
    task.set_editor_property("automated", True)
    task.set_editor_property("replace_existing", True)
    task.set_editor_property("save", False)
    task.set_editor_property("options", options)
    tools.import_asset_tasks([task])

    mesh = unreal.load_asset(package)
    if mesh is None:
        REPORT["skipped"].append(folder + " (reimport failed)")
        continue
    materials = list(mesh.get_editor_property("static_materials"))
    rebound = 0
    for entry in materials:
        slot = str(entry.get_editor_property("material_slot_name"))
        if slot in saved_slots and saved_slots[slot] is not None:
            entry.set_editor_property("material_interface",
                                      saved_slots[slot])
            rebound += 1
    mesh.set_editor_property("static_materials", materials)
    unreal.EditorAssetLibrary.save_loaded_asset(mesh, False)

    new_box = mesh.get_bounding_box()
    new_size = new_box.max - new_box.min
    REPORT["updated"][folder] = {
        "tris": [old_tris, mesh.get_num_triangles(0)],
        "size_delta_pct": [
            round(100.0 * (new_size.x - old_size.x)
                  / max(old_size.x, 1.0), 1),
            round(100.0 * (new_size.y - old_size.y)
                  / max(old_size.y, 1.0), 1),
            round(100.0 * (new_size.z - old_size.z)
                  / max(old_size.z, 1.0), 1)],
        "slots_rebound": rebound,
    }

with open(OUT, "w") as handle:
    json.dump(REPORT, handle, indent=1)
unreal.log("LINE_BOSS_DETAIL_UPLIFT updated={} skipped={}".format(
    len(REPORT["updated"]), len(REPORT["skipped"])))
