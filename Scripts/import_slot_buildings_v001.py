"""import_slot_buildings_v001.py - the two PROCEDURAL slot buildings
(owner approved 2026-08-26: architectural models built in Blender, no
Meshy needed, no third-party assets). Imports both LOD sets, creates
four flat Cold Steel materials in-engine and assigns them by SLOT
NAME (the FBX carries LB_Building_* slot names), bounds-gated against
the catalogue footprints."""

import os
import unreal

FBX = (r"C:\Users\greg_\Projects\LineBossCarFactory_Unreal 5.8"
       r"\SourceAssets\Candidate\Spacecraft\SlotBuildings_v001\FBX")
ROOT = "/Game/LineBoss/Candidates/Spacecraft/StationMeshes_v001"
MESH_DIR = ROOT + "/Meshes"
MAT_DIR = ROOT + "/Materials"

MATERIALS = {
    "LB_Building_Panel": ((0.68, 0.70, 0.74), 0.55, 0.15, False),
    "LB_Building_Trim": ((0.16, 0.17, 0.20), 0.45, 0.55, False),
    "LB_Building_Accent": ((0.85, 0.38, 0.06), 0.5, 0.1, False),
    "LB_Building_Glow": ((0.55, 0.75, 1.0), 0.3, 0.0, True),
}
JOBS = [("PowerStation", 2400.0, 2400.0), ("SubAssemblyHall", 3000.0, 2200.0)]

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
for key, foot_x, foot_y in JOBS:
    for lod in (0, 1):
        name = "SM_LB_ST_%s_LOD%d" % (key, lod)
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
            "auto_generate_collision": True, "import_uniform_scale": 1.0,
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
            failures.append(name + ": OVERRUNS FOOTPRINT")
            continue
        slots = mesh.get_editor_property("static_materials")
        for index, slot in enumerate(slots):
            slot_name = str(slot.get_editor_property(
                "material_slot_name"))
            for mat_key, mat in mats.items():
                if mat_key in slot_name:
                    mesh.set_material(index, mat)
                    break
        lib.save_asset("%s/%s" % (MESH_DIR, name))
        unreal.log("BUILDING IMPORTED %s (%.0f x %.0f cm)"
                   % (name, ext.x * 2, ext.y * 2))
if failures:
    raise RuntimeError("FAIL CLOSED: " + "; ".join(failures))
unreal.log("SLOT BUILDINGS IMPORT DONE")
