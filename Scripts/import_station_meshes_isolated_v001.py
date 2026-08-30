"""import_station_meshes_isolated_v001.py - isolated import of the Meshy
station runtime derivatives (RollingMill, PowerPlant, StorageRack; LOD0 +
LOD1 each) into /Game/LineBoss/Candidates/Spacecraft/StationMeshes_v001.

Materials and textures import WITH the mesh (the FBX embeds them). Bounds
are verified in-engine against the catalogue footprints - a mesh that
overruns its placement envelope fails the run rather than shipping.

Run headless (editor closed):
  UnrealEditor-Cmd.exe <proj> /Engine/Maps/Entry -Unattended ...
    -ExecutePythonScript="<this file>"
"""

import os
import unreal

SRC_FBX = (r"C:\Users\greg_\Projects\LineBossCarFactory_Unreal 5.8"
           r"\SourceAssets\Candidate\Spacecraft\StationModels_MeshyIntake_v001"
           r"\FBX")
DEST = "/Game/LineBoss/Candidates/Spacecraft/StationMeshes_v001/Meshes"

# (fbx base name, footprint X cm, footprint Y cm)
JOBS = [
    ("SM_LB_ST_RollingMill_LOD0", 1400.0, 900.0),
    ("SM_LB_ST_RollingMill_LOD1", 1400.0, 900.0),
    ("SM_LB_ST_PowerPlant_LOD0", 1600.0, 1600.0),
    ("SM_LB_ST_PowerPlant_LOD1", 1600.0, 1600.0),
    ("SM_LB_ST_StorageRack_LOD0", 1000.0, 600.0),
    ("SM_LB_ST_StorageRack_LOD1", 1000.0, 600.0),
    ("SM_LB_ST_CircuitFab_LOD0", 1000.0, 800.0),
    ("SM_LB_ST_CircuitFab_LOD1", 1000.0, 800.0),
    ("SM_LB_ST_PowerCellPlant_LOD0", 1200.0, 1000.0),
    ("SM_LB_ST_PowerCellPlant_LOD1", 1200.0, 1000.0),
    ("SM_LB_ST_PropulsionStation_LOD0", 1600.0, 1100.0),
    ("SM_LB_ST_PropulsionStation_LOD1", 1600.0, 1100.0),
    ("SM_LB_ST_SubAssemblyRobot_LOD0", 1800.0, 1300.0),
    ("SM_LB_ST_SubAssemblyRobot_LOD1", 1800.0, 1300.0),
]

unreal.SystemLibrary.execute_console_command(
    None, "Interchange.FeatureFlags.Import.FBX 0")
lib = unreal.EditorAssetLibrary
tools = unreal.AssetToolsHelpers.get_asset_tools()
if not lib.does_directory_exist(DEST):
    lib.make_directory(DEST)

failures = []
for name, foot_x, foot_y in JOBS:
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
        "auto_generate_collision": True, "import_uniform_scale": 1.0,
        "convert_scene": True, "convert_scene_unit": True,
        "normal_import_method":
            unreal.FBXNormalImportMethod.FBXNIM_IMPORT_NORMALS_AND_TANGENTS})
    task.options = ui
    tools.import_asset_tasks([task])
    unreal.AutomationUtilsBlueprintLibrary.finish_all_asset_compilation()
    mesh = lib.load_asset("%s/%s" % (DEST, name))
    if mesh is None:
        failures.append(name + ": IMPORT FAILED")
        continue
    bounds = mesh.get_bounds()
    ext = bounds.box_extent
    size = (ext.x * 2.0, ext.y * 2.0, ext.z * 2.0)
    # Uniform min-fit was baked with 2% margin; allow 5% slack here, and
    # the long axis may map to either footprint axis.
    fits = ((size[0] <= foot_x * 1.05 and size[1] <= foot_y * 1.05)
            or (size[0] <= foot_y * 1.05 and size[1] <= foot_x * 1.05))
    unreal.log("IMPORTED %s size_cm=(%.0f, %.0f, %.0f) fits=%s"
               % (name, size[0], size[1], size[2], fits))
    if not fits:
        failures.append("%s: OVERRUNS FOOTPRINT (%.0f x %.0f cm)"
                        % (name, size[0], size[1]))

if failures:
    raise RuntimeError("STATION IMPORT FAILED CLOSED: " + "; ".join(failures))
unreal.log("STATION MESH IMPORT DONE: %d assets" % len(JOBS))
