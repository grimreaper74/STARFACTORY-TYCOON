"""import_canopy_v001.py - the canopy glass cut (owner 2026-08-26
night: "the glass will be one of last things fitted"). Imports per
craft the Canopy piece and the AirframeOpen variant (airframe minus
glass; Cargo cut geometrically, Scout by texture-guided region - both
verified by render). Creates M_LB_SC_CanopyGlass (translucent
blue-white, two-sided) and assigns it to the canopy meshes; the open
airframes carry no materials - the presenter dresses them with the
recipe hull material exactly like the closed forms. Fails closed."""

import os
import unreal

SCOUT = (r"C:\Users\greg_\Projects\LineBossCarFactory_Unreal 5.8"
         r"\SourceAssets\Candidate\Spacecraft\Scout01_RuntimeDerivative_v001\FBX")
CARGO = (r"C:\Users\greg_\Projects\LineBossCarFactory_Unreal 5.8"
         r"\SourceAssets\Candidate\Spacecraft\Cargo01_RuntimeDerivative_v001\FBX")
ROOT = "/Game/LineBoss/Candidates/Spacecraft/SpacecraftTestBay_v001"
STRAY_ROOT = "/Game/LineBoss/Candidates/Spacecraft/SpacecraftFactory_v001"
MESH_DIR = ROOT + "/Meshes"
MAT_DIR = ROOT + "/Materials"

JOBS = [
    (SCOUT, "SM_LB_SC_Scout01_Canopy_v001", True, 420.0),
    (SCOUT, "SM_LB_SC_Scout01_AirframeOpen_v001", False, 1450.0),
    (CARGO, "SM_LB_SC_Cargo01_Canopy_v001", True, 520.0),
    (CARGO, "SM_LB_SC_Cargo01_AirframeOpen_v001", False, 1800.0),
]

unreal.SystemLibrary.execute_console_command(
    None, "Interchange.FeatureFlags.Import.FBX 0")
lib = unreal.EditorAssetLibrary
tools = unreal.AssetToolsHelpers.get_asset_tools()
mel = unreal.MaterialEditingLibrary

glass_path = MAT_DIR + "/M_LB_SC_CanopyGlass"
glass = unreal.load_asset(glass_path)
if glass is None:
    glass = tools.create_asset("M_LB_SC_CanopyGlass", MAT_DIR,
                               unreal.Material,
                               unreal.MaterialFactoryNew())
    glass.set_editor_property("blend_mode",
                              unreal.BlendMode.BLEND_TRANSLUCENT)
    glass.set_editor_property("two_sided", True)
    colour = mel.create_material_expression(glass,
        unreal.MaterialExpressionConstant3Vector, -400, -200)
    colour.set_editor_property("constant",
        unreal.LinearColor(0.45, 0.62, 0.80, 1.0))
    mel.connect_material_property(colour, "",
        unreal.MaterialProperty.MP_BASE_COLOR)
    opacity = mel.create_material_expression(glass,
        unreal.MaterialExpressionConstant, -400, 0)
    opacity.set_editor_property("r", 0.38)
    mel.connect_material_property(opacity, "",
        unreal.MaterialProperty.MP_OPACITY)
    rough = mel.create_material_expression(glass,
        unreal.MaterialExpressionConstant, -400, 120)
    rough.set_editor_property("r", 0.08)
    mel.connect_material_property(rough, "",
        unreal.MaterialProperty.MP_ROUGHNESS)
    mel.recompile_material(glass)
    lib.save_asset(glass_path)

failures = []
for fbx_dir, name, is_glass, gate_cm in JOBS:
    task = unreal.AssetImportTask()
    task.set_editor_properties({
        "filename": os.path.join(fbx_dir, name + ".fbx"),
        "destination_path": MESH_DIR, "destination_name": name,
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
        "auto_generate_collision": False, "import_uniform_scale": 1.0,
        "convert_scene": True, "convert_scene_unit": True,
        "normal_import_method": unreal.FBXNormalImportMethod
            .FBXNIM_IMPORT_NORMALS_AND_TANGENTS})
    task.options = ui
    tools.import_asset_tasks([task])
    unreal.AutomationUtilsBlueprintLibrary.finish_all_asset_compilation()
    mesh = lib.load_asset("%s/%s" % (MESH_DIR, name))
    if mesh is None:
        failures.append(name + ": IMPORT FAILED")
        continue
    ext = mesh.get_bounds().box_extent
    longest = max(ext.x, ext.y, ext.z) * 2.0
    if longest > gate_cm * 1.05:
        failures.append("%s: %.0f cm exceeds gate %.0f"
                        % (name, longest, gate_cm))
        continue
    if is_glass:
        slots = mesh.get_editor_property("static_materials")
        for index in range(len(slots)):
            mesh.set_material(index, glass)
    lib.save_asset("%s/%s" % (MESH_DIR, name))
    unreal.log("CANOPY IMPORTED %s longest=%.0f cm glass=%s"
               % (name, longest, is_glass))
if failures:
    raise RuntimeError("FAIL CLOSED: " + "; ".join(failures))
# Remove the first-pass strays imported into the wrong root.
for stray in ("Meshes/SM_LB_SC_Scout01_Canopy_v001",
              "Meshes/SM_LB_SC_Scout01_AirframeOpen_v001",
              "Meshes/SM_LB_SC_Cargo01_Canopy_v001",
              "Meshes/SM_LB_SC_Cargo01_AirframeOpen_v001",
              "Materials/M_LB_SC_CanopyGlass"):
    stray_path = "%s/%s" % (STRAY_ROOT, stray)
    if lib.does_asset_exist(stray_path):
        lib.delete_asset(stray_path)
        unreal.log("CANOPY STRAY REMOVED " + stray_path)
unreal.log("CANOPY IMPORT DONE")
