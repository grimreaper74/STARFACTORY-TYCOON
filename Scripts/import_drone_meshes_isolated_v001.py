"""import_drone_meshes_isolated_v001.py - isolated import of the drone
runtime derivatives (body + tiltable fan pods per drone) into
/Game/LineBoss/Candidates/Spacecraft/StationMeshes_v001/Drones.

Materials and textures import WITH the mesh (the FBX embeds them). Body
bounds are verified in-engine against the PROVISIONAL drone envelopes -
a body that overruns its envelope fails the run rather than shipping.
Pods are small tilt components and get a sanity ceiling instead.

Run headless (editor closed):
  UnrealEditor-Cmd.exe <proj> /Engine/Maps/Entry -Unattended ...
    -ExecutePythonScript="<this file>"
"""

import os
import unreal

SRC_FBX = (r"C:\Users\greg_\Projects\LineBossCarFactory_Unreal 5.8"
           r"\SourceAssets\Candidate\Spacecraft\StationModels_MeshyIntake_v001"
           r"\FBX")
DEST = "/Game/LineBoss/Candidates/Spacecraft/StationMeshes_v001/Drones"

# (drone key, PROVISIONAL envelope cm, pod tags)
DRONES = [
    ("Assembly", 180.0, ["FR", "BR", "BL", "FL"]),
    ("CargoLift", 420.0, ["FR", "BR", "BL", "FL", "MR", "ML"]),
    ("Spray", 180.0, ["FR", "BR", "BL", "FL"]),
    ("Winch", 220.0, ["FR", "BR", "BL", "FL"]),
]

unreal.SystemLibrary.execute_console_command(
    None, "Interchange.FeatureFlags.Import.FBX 0")
lib = unreal.EditorAssetLibrary
tools = unreal.AssetToolsHelpers.get_asset_tools()
if not lib.does_directory_exist(DEST):
    lib.make_directory(DEST)


def import_one(name, max_cm):
    task = unreal.AssetImportTask()
    task.set_editor_properties({
        "filename": os.path.join(SRC_FBX, name + ".fbx"),
        "destination_path": DEST, "destination_name": name,
        "automated": True, "replace_existing": True,
        "replace_existing_settings": True, "save": True})
    ui = unreal.FbxImportUI()
    ui.set_editor_properties({
        "import_mesh": True, "import_as_skeletal": False,
        "import_materials": True, "import_textures": True,
        "mesh_type_to_import": unreal.FBXImportType.FBXIT_STATIC_MESH,
        "automated_import_should_detect_type": False})
    ui.static_mesh_import_data.set_editor_properties({
        "combine_meshes": True, "generate_lightmap_u_vs": False,
        "auto_generate_collision": False, "import_uniform_scale": 1.0,
        "convert_scene": True, "convert_scene_unit": True,
        "normal_import_method":
            unreal.FBXNormalImportMethod.FBXNIM_IMPORT_NORMALS_AND_TANGENTS})
    task.options = ui
    tools.import_asset_tasks([task])
    unreal.AutomationUtilsBlueprintLibrary.finish_all_asset_compilation()
    mesh = lib.load_asset("%s/%s" % (DEST, name))
    if mesh is None:
        return name + ": IMPORT FAILED"
    ext = mesh.get_bounds().box_extent
    size = (ext.x * 2.0, ext.y * 2.0, ext.z * 2.0)
    fits = max(size[0], size[1]) <= max_cm * 1.05
    unreal.log("IMPORTED %s size_cm=(%.0f, %.0f, %.0f) fits=%s"
               % (name, size[0], size[1], size[2], fits))
    if not fits:
        return "%s: OVERRUNS ENVELOPE (%.0f x %.0f cm)" % (
            name, size[0], size[1])
    return None


failures = []
count = 0
for key, envelope, tags in DRONES:
    err = import_one("SM_LB_DR_%s_Body" % key, envelope)
    if err:
        failures.append(err)
    count += 1
    for tag in tags:
        # Pods are fragments of the same envelope; ceiling only.
        err = import_one("SM_LB_DR_%s_Pod%s" % (key, tag), envelope)
        if err:
            failures.append(err)
        count += 1

if failures:
    raise RuntimeError("DRONE IMPORT FAILED CLOSED: " + "; ".join(failures))
unreal.log("DRONE MESH IMPORT DONE: %d assets" % count)
