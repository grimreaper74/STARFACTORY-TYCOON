"""import_drone_whole_v001.py - the drones return to WHOLE meshes
(owner 2026-08-26: the carved fan pods were disfigured; and the Winch
master carried a slung panel baked in - now waist-cut away). Replaces
the four _Body assets with the v003 whole exports, reassigns their
MIs, and DELETES every pod asset; the presenter skips missing pod
soft paths by design. Fail-closed throughout."""

import os
import unreal

FBX = (r"C:\Users\greg_\Projects\LineBossCarFactory_Unreal 5.8"
       r"\SourceAssets\Candidate\Spacecraft\StationModels_MeshyIntake_v001"
       r"\FBX")
ROOT = "/Game/LineBoss/Candidates/Spacecraft/StationMeshes_v001"
DRONES = ROOT + "/Drones"
MAT_DIR = ROOT + "/Materials"

KEYS = ["Assembly", "CargoLift", "Spray", "Winch"]
POD_TAGS = ["FR", "BR", "BL", "FL", "MR", "ML"]

unreal.SystemLibrary.execute_console_command(
    None, "Interchange.FeatureFlags.Import.FBX 0")
lib = unreal.EditorAssetLibrary
tools = unreal.AssetToolsHelpers.get_asset_tools()
failures = []
for key in KEYS:
    name = "SM_LB_DR_%s_Body" % key
    task = unreal.AssetImportTask()
    task.set_editor_properties({
        "filename": os.path.join(FBX, name + ".fbx"),
        "destination_path": DRONES, "destination_name": name,
        "automated": True, "replace_existing": True,
        "replace_existing_settings": True, "save": True})
    ui = unreal.FbxImportUI()
    ui.set_editor_properties({
        "import_mesh": True, "import_as_skeletal": False,
        "import_materials": False, "import_textures": False,
        "mesh_type_to_import": unreal.FBXImportType.FBXIT_STATIC_MESH,
        "automated_import_should_detect_type": False})
    ui.static_mesh_import_data.set_editor_properties({
        "combine_meshes": True, "generate_lightmap_u_vs": False,
        "auto_generate_collision": True, "import_uniform_scale": 1.0,
        "convert_scene": True, "convert_scene_unit": True,
        "normal_import_method":
            unreal.FBXNormalImportMethod.FBXNIM_IMPORT_NORMALS_AND_TANGENTS})
    task.options = ui
    tools.import_asset_tasks([task])
    unreal.AutomationUtilsBlueprintLibrary.finish_all_asset_compilation()
    mesh = lib.load_asset("%s/%s" % (DRONES, name))
    if mesh is None:
        failures.append(name)
        continue
    mi = lib.load_asset("%s/MI_LB_Drone%s" % (MAT_DIR, key))
    if mi is None:
        failures.append(name + ": MI missing")
        continue
    slots = mesh.get_editor_property("static_materials")
    for index in range(len(slots)):
        mesh.set_material(index, mi)
    lib.save_asset("%s/%s" % (DRONES, name))
    unreal.log("WHOLE DRONE %s reimported" % name)
    for tag in POD_TAGS:
        pod = "%s/SM_LB_DR_%s_Pod%s" % (DRONES, key, tag)
        if lib.does_asset_exist(pod):
            if lib.delete_asset(pod):
                unreal.log("DELETED pod %s_Pod%s" % (key, tag))
            else:
                failures.append("pod %s_Pod%s undeletable" % (key, tag))
if failures:
    raise RuntimeError("FAIL CLOSED: " + "; ".join(failures))
unreal.log("WHOLE-DRONE IMPORT DONE")
