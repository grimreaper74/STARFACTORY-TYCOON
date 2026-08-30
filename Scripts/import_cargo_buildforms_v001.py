"""import_cargo_buildforms_v001.py - Cargo-01 build forms (owner's
morning drops 2026-08-26: text-to-3D ship + part segmentation). Six
FBX derivatives (Chassis/Airframe/Fitted x LOD0/LOD1, one shared
envelope-fit transform, nose local -X) into the craft-mesh content dir
beside the Scout's forms. Plain mesh import - the presenter owns craft
materials (hull + live paint). Bounds gate: every form must stay
inside the decided Cargo-01 envelope 21.0 x 11.2 x 5.8 m."""

import os
import unreal

FBX = (r"C:\Users\greg_\Projects\LineBossCarFactory_Unreal 5.8"
       r"\SourceAssets\Candidate\Spacecraft\Cargo01_RuntimeDerivative_v001"
       r"\FBX")
DEST = "/Game/LineBoss/Candidates/Spacecraft/SpacecraftTestBay_v001/Meshes"

NAMES = ["SM_LB_SC_Cargo01_%s_v001_LOD%d" % (form, lod)
         for form in ("Chassis", "Airframe", "Fitted") for lod in (0, 1)]

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
unreal.log("CARGO BUILD FORMS IMPORT DONE: %d meshes" % len(NAMES))
