"""import_chassis_mesh_isolated_v001.py - isolated import of the Scout-01
chassis derivative (bottom skin, WIP mid-stage visual) into the ship's
mesh folder. Bounds are verified fail-closed."""
import os
import unreal

SRC = (r"C:\Users\greg_\Projects\LineBossCarFactory_Unreal 5.8"
       r"\SourceAssets\Candidate\Spacecraft\Scout01_RuntimeDerivative_v001"
       r"\FBX")
DEST = "/Game/LineBoss/Candidates/Spacecraft/SpacecraftTestBay_v001/Meshes"
JOBS = ["SM_LB_SC_Scout01_Chassis_v001_LOD0",
        "SM_LB_SC_Scout01_Chassis_v001_LOD1",
        "SM_LB_SC_Scout01_Airframe_v001_LOD0",
        "SM_LB_SC_Scout01_Airframe_v001_LOD1",
        "SM_LB_SC_Scout01_Fitted_v001_LOD0",
        "SM_LB_SC_Scout01_Fitted_v001_LOD1"]

unreal.SystemLibrary.execute_console_command(
    None, "Interchange.FeatureFlags.Import.FBX 0")
lib = unreal.EditorAssetLibrary
tools = unreal.AssetToolsHelpers.get_asset_tools()
failures = []
for name in JOBS:
    task = unreal.AssetImportTask()
    task.set_editor_properties({
        "filename": os.path.join(SRC, name + ".fbx"),
        "destination_path": DEST, "destination_name": name,
        "automated": True, "replace_existing": True,
        "replace_existing_settings": True, "save": True})
    ui = unreal.FbxImportUI()
    ui.set_editor_properties({
        "import_mesh": True, "import_as_skeletal": False,
        "import_materials": False, "import_textures": False,
        "mesh_type_to_import": unreal.FBXImportType.FBXIT_STATIC_MESH,
        "automated_import_should_detect_type": False})
    ui.static_mesh_import_data.set_editor_properties({
        "combine_meshes": False, "generate_lightmap_u_vs": False,
        "auto_generate_collision": False, "import_uniform_scale": 1.0,
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
    ext = mesh.get_bounds().box_extent
    size = (ext.x * 2.0, ext.y * 2.0, ext.z * 2.0)
    # 425: v002 airframe is 4.05 m (skids dip below the hull line;
    # sanity ceiling, not a placement contract).
    max_z = 200.0 if "Chassis" in name else 425.0
    fits = size[0] < 1450.0 and size[1] < 800.0 and size[2] < max_z
    unreal.log("IMPORTED %s size_cm=(%.0f, %.0f, %.0f) fits=%s"
               % (name, size[0], size[1], size[2], fits))
    if not fits:
        failures.append("%s: UNEXPECTED BOUNDS" % name)
if failures:
    raise RuntimeError("CHASSIS IMPORT FAILED CLOSED: " + "; ".join(failures))
unreal.log("CHASSIS IMPORT DONE")
