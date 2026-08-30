"""import_cargo_craft_v001.py - the FINISHED Cargo-01 craft meshes
from the textured master (the segmentation forms have no UVs; the
craft visual needs the texture master's UVs). Imported PLAIN and
dressed with MI_LB_SC_Cargo01_Hull - the MI's textures were extracted
from this same master, so its UVs fit; embedded-FBX texture import is
never trusted (the extension-less Meshy texture lesson)."""

import os
import unreal

FBX = (r"C:\Users\greg_\Projects\LineBossCarFactory_Unreal 5.8"
       r"\SourceAssets\Candidate\Spacecraft\Cargo01_RuntimeDerivative_v001"
       r"\FBX")
DEST = "/Game/LineBoss/Candidates/Spacecraft/SpacecraftTestBay_v001/Meshes"

NAMES = ["SM_LB_SC_Cargo01_v001_LOD0", "SM_LB_SC_Cargo01_v001_LOD1"]
MI_PATH = ("/Game/LineBoss/Candidates/Spacecraft/StationMeshes_v001"
           "/Materials/MI_LB_SC_Cargo01_Hull")

unreal.SystemLibrary.execute_console_command(
    None, "Interchange.FeatureFlags.Import.FBX 0")
lib = unreal.EditorAssetLibrary
tools = unreal.AssetToolsHelpers.get_asset_tools()
failures = []
for name in NAMES:
    task = unreal.AssetImportTask()
    task.set_editor_properties({
        "filename": os.path.join(FBX, name + ".fbx"),
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
    ext = mesh.get_bounds().box_extent
    size = (ext.x * 2.0, ext.y * 2.0, ext.z * 2.0)
    fits = (size[0] <= 2100.0 * 1.02 and size[1] <= 1120.0 * 1.02
            and size[2] <= 580.0 * 1.05)
    unreal.log("IMPORTED %s size_cm=(%.0f, %.0f, %.0f) fits=%s"
               % (name, size[0], size[1], size[2], fits))
    if not fits:
        failures.append(name + ": OVERRUNS ENVELOPE")
if failures:
    raise RuntimeError("FAILED CLOSED: " + "; ".join(failures))
mi = lib.load_asset(MI_PATH)
if mi is None:
    raise RuntimeError("FAIL CLOSED: cargo hull MI missing")
for name in NAMES:
    mesh = lib.load_asset("%s/%s" % (DEST, name))
    slots = mesh.get_editor_property("static_materials")
    for index in range(len(slots)):
        mesh.set_material(index, mi)
    lib.save_asset("%s/%s" % (DEST, name))
unreal.log("CARGO CRAFT IMPORT DONE: %d meshes wearing the cargo hull MI"
           % len(NAMES))
