"""import_site_kit_v002.py - the FACTORY SITE KIT, UV-mapped and
wearing the PROJECT'S OWN industrial PBR library (owner 2026-08-26
night: "it should be downloaded" - the library is already in
Content/Materials from the car era: MI_FactoryConcreteFloor01,
MI_MetalWallPart_Painted_01, MI_ConcretePillar_Painted01, real
base-colour/normal/ORM maps). The kit's flat Cold Steel materials
stay on the trim/accent/glow slots; the big surfaces take the
textured library materials. Supersedes v001 (which shipped without
UVs, so tiling textures could not apply).

import_site_kit_v001.py - the FACTORY SITE KIT (owner 2026-08-26
night: "can we get the floor and sides as good quality as the other
games?"). Procedural, no Meshy, no third-party assets: a 10 m floor
tile, a 10 m x 8 m wall bay and a wall pillar, all tiling on the same
module. Creates four flat Cold Steel materials in-engine and binds
them by SLOT NAME (the FBX carries M_LB_Site_* names), bounds-gated
against the module. Nanite ON for tile and wall (they cover the whole
site); glow slots keep their emissive flat material."""

import os
import unreal

FBX = (r"C:\Users\greg_\Projects\LineBossCarFactory_Unreal 5.8"
       r"\SourceAssets\Candidate\Spacecraft\SiteKit_v001")
ROOT = "/Game/LineBoss/Candidates/Spacecraft/StationMeshes_v001"
MESH_DIR = ROOT + "/Meshes"
MAT_DIR = ROOT + "/Materials"

MATERIALS = {
    "LB_Site_Panel": ((0.560, 0.575, 0.600), 0.68, 0.05, False),
    "LB_Site_Trim": ((0.180, 0.190, 0.210), 0.45, 0.60, False),
    "LB_Site_Accent": ((0.720, 0.300, 0.050), 0.55, 0.05, False),
    "LB_Site_Glow": ((0.550, 0.680, 0.800), 0.30, 0.00, True),
}
# (name, gate X cm, gate Y cm, gate Z cm)
JOBS = [
    ("SM_LB_Site_FloorTile", 1000.0, 1000.0, 40.0),
    ("SM_LB_Site_WallPanel", 1000.0, 120.0, 850.0),
    ("SM_LB_Site_WallPillar", 200.0, 200.0, 850.0),
]

# The project's own industrial library (car era, Content/Materials).
SURFACE_LIBRARY = {
    "SM_LB_Site_FloorTile": "/Game/Materials/MI_FactoryConcreteFloor01",
    "SM_LB_Site_WallPanel": "/Game/Materials/MI_MetalWallPart_Painted_01",
    "SM_LB_Site_WallPillar": "/Game/Materials/MI_ConcretePillar_Painted01",
}

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
for name, gx, gy, gz in JOBS:
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
    size = (ext.x * 2.0, ext.y * 2.0, ext.z * 2.0)
    if (size[0] > gx * 1.05 or size[1] > gy * 1.05
            or size[2] > gz * 1.05):
        failures.append("%s: %.0f x %.0f x %.0f exceeds gate"
                        % (name, size[0], size[1], size[2]))
        continue
    slots = mesh.get_editor_property("static_materials")
    for index, slot in enumerate(slots):
        slot_name = str(slot.get_editor_property("material_slot_name"))
        assigned = None
        # The PANEL slot is the big visible surface: it takes the
        # project's textured library material where one is mapped.
        if "LB_Site_Panel" in slot_name and name in SURFACE_LIBRARY:
            assigned = unreal.load_asset(SURFACE_LIBRARY[name])
            if assigned is None:
                failures.append("%s: library material missing %s"
                                % (name, SURFACE_LIBRARY[name]))
                continue
        if assigned is None:
            for mat_key, mat in mats.items():
                if mat_key in slot_name:
                    assigned = mat
                    break
        if assigned is not None:
            mesh.set_material(index, assigned)
    nanite = mesh.get_editor_property("nanite_settings")
    if not nanite.get_editor_property("enabled"):
        nanite.set_editor_property("enabled", True)
        unreal.get_editor_subsystem(
            unreal.StaticMeshEditorSubsystem).set_nanite_settings(
                mesh, nanite, True)
    lib.save_asset("%s/%s" % (MESH_DIR, name))
    unreal.log("SITE PIECE IMPORTED %s (%.0f x %.0f x %.0f cm)"
               % (name, size[0], size[1], size[2]))
if failures:
    raise RuntimeError("FAIL CLOSED: " + "; ".join(failures))
unreal.log("SITE KIT IMPORT DONE")
