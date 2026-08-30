"""import_track_pieces_v002.py - the WIDE-DECK conveyor track piece set
(owner-supplied generator, 2026-08-26: straight / symmetric quarter-turn /
cap built from pure bpy primitives, no Meshy, no third-party assets;
SourceAssets/Candidate/Spacecraft/TrackPieces_v001). Imports the three
FBX, creates five flat Cold Steel materials in-engine and assigns them by
SLOT NAME (the FBX carries M_LB_Track_* slot names), bounds-gated against
the 400 cm track cell. The extra AccentBlue material is the Start-anchor
tint the presenter swaps in (one cap mesh serves both ends)."""

import os
import unreal

FBX = (r"C:\Users\greg_\Projects\LineBossCarFactory_Unreal 5.8"
       r"\SourceAssets\Candidate\Spacecraft\TrackPieces_v001")
ROOT = "/Game/LineBoss/Candidates/Spacecraft/StationMeshes_v001"
MESH_DIR = ROOT + "/Meshes"
MAT_DIR = ROOT + "/Materials"

MATERIALS = {
    "LB_Track_Panel": ((0.090, 0.095, 0.100), 0.62, 0.15, False),
    "LB_Track_Trim": ((0.340, 0.360, 0.380), 0.38, 0.90, False),
    "LB_Track_Accent": ((0.720, 0.300, 0.050), 0.55, 0.05, False),
    "LB_Track_Glow": ((0.550, 0.680, 0.800), 0.30, 0.00, True),
    "LB_Track_AccentBlue": ((0.150, 0.420, 0.850), 0.55, 0.05, False),
}
# (name, footprint gate X, footprint gate Y) - the generator's manifest
# bounds, +5% tolerance applied below. The cell is 400 x 400.
JOBS = [("SM_LB_Track_Straight", 400.0, 620.0),
        ("SM_LB_Track_Turn", 620.0, 620.0),
        ("SM_LB_Track_Cap", 80.0, 620.0)]

lib = unreal.EditorAssetLibrary
tools = unreal.AssetToolsHelpers.get_asset_tools()
mel = unreal.MaterialEditingLibrary

mats = {}
for name, (rgb, rough, metal, glow) in MATERIALS.items():
    path = "%s/M_%s" % (MAT_DIR, name)
    mat = unreal.load_asset(path)
    if mat is None:
        mat = tools.create_asset("M_%s" % name, MAT_DIR, unreal.Material,
                                 unreal.MaterialFactoryNew())
        colour = mel.create_material_expression(mat,
            unreal.MaterialExpressionConstant3Vector, -400, -200)
        colour.set_editor_property("constant",
            unreal.LinearColor(rgb[0], rgb[1], rgb[2], 1.0))
        mel.connect_material_property(colour, "",
            unreal.MaterialProperty.MP_BASE_COLOR)
        r = mel.create_material_expression(mat,
            unreal.MaterialExpressionConstant, -400, 0)
        r.set_editor_property("r", rough)
        mel.connect_material_property(r, "",
            unreal.MaterialProperty.MP_ROUGHNESS)
        m = mel.create_material_expression(mat,
            unreal.MaterialExpressionConstant, -400, 120)
        m.set_editor_property("r", metal)
        mel.connect_material_property(m, "",
            unreal.MaterialProperty.MP_METALLIC)
        if glow:
            e = mel.create_material_expression(mat,
                unreal.MaterialExpressionConstant3Vector, -400, 260)
            e.set_editor_property("constant",
                unreal.LinearColor(rgb[0] * 4, rgb[1] * 4, rgb[2] * 4,
                                   1.0))
            mel.connect_material_property(e, "",
                unreal.MaterialProperty.MP_EMISSIVE_COLOR)
        mel.recompile_material(mat)
        lib.save_asset(path)
    mats[name] = mat

unreal.SystemLibrary.execute_console_command(
    None, "Interchange.FeatureFlags.Import.FBX 0")
failures = []
for name, foot_x, foot_y in JOBS:
    task = unreal.AssetImportTask()
    task.set_editor_properties({
        "filename": os.path.join(FBX, name + ".fbx"),
        "destination_path": MESH_DIR, "destination_name": name,
        "automated": True, "replace_existing": True,
        "replace_existing_settings": True, "save": True})
    ui = unreal.FbxImportUI()
    ui.set_editor_properties({
        "import_mesh": True, "import_as_skeletal": False,
        "import_materials": False, "import_textures": False,
        "mesh_type_to_import":
            unreal.FBXImportType.FBXIT_STATIC_MESH,
        "automated_import_should_detect_type": False})
    ui.static_mesh_import_data.set_editor_properties({
        "combine_meshes": True, "generate_lightmap_u_vs": False,
        "auto_generate_collision": False, "import_uniform_scale": 1.0,
        "convert_scene": True, "convert_scene_unit": True,
        "normal_import_method": unreal.FBXNormalImportMethod
            .FBXNIM_IMPORT_NORMALS_AND_TANGENTS})
    task.options = ui
    tools.import_asset_tasks([task])
    unreal.AutomationUtilsBlueprintLibrary \
        .finish_all_asset_compilation()
    mesh = lib.load_asset("%s/%s" % (MESH_DIR, name))
    if mesh is None:
        failures.append(name)
        continue
    ext = mesh.get_bounds().box_extent
    if ext.x * 2 > foot_x * 1.05 or ext.y * 2 > foot_y * 1.05:
        failures.append("%s: OVERRUNS FOOTPRINT (%.0f x %.0f)"
                        % (name, ext.x * 2, ext.y * 2))
        continue
    slots = mesh.get_editor_property("static_materials")
    for index, slot in enumerate(slots):
        slot_name = str(slot.get_editor_property("material_slot_name"))
        for mat_key, mat in mats.items():
            if mat_key in slot_name:
                mesh.set_material(index, mat)
                break
    lib.save_asset("%s/%s" % (MESH_DIR, name))
    unreal.log("TRACK PIECE IMPORTED %s (%.0f x %.0f x %.0f cm)"
               % (name, ext.x * 2, ext.y * 2, ext.z * 2))
if failures:
    raise RuntimeError("FAIL CLOSED: " + "; ".join(failures))
unreal.log("TRACK PIECES IMPORT DONE")
