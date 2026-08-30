"""import_components_v001.py - the six ship COMPONENTS plus the two
cockpit extracts (owner's 2026-08-26 batch; identities assigned by
inspection gallery). Sized to FIT IN THE SHIP (owner) - the export lane
already bounded every piece inside the Scout envelope; the gates here
re-prove it. Textured components get the full base/MR/normal set and an
MI on the M_LB_MeshyPBR_v003 master with measured albedo boosts; the
HULL master is an untextured clay generation and wears a flat cold-
steel material until the owner runs its Meshy texture stage; the seat
and dash share the Interior MI. Fails closed at every step."""

import os
import unreal

SRC = (r"C:\Users\greg_\Projects\LineBossCarFactory_Unreal 5.8"
       r"\SourceAssets\Candidate\Spacecraft\MeshyBatch_20260826_v001")
FBX = SRC + r"\FBX"
ROOT = "/Game/LineBoss/Candidates/Spacecraft/StationMeshes_v001"
MESH_DIR = ROOT + "/Meshes"
MAT_DIR = ROOT + "/Materials"
TEX_DIR = ROOT + "/Textures"
MASTER = MAT_DIR + "/M_LB_MeshyPBR_v003"

# (key, gate longest cm, boost, textured)
JOBS = [
    ("Hull", 273.0, 0.0, False),
    ("Electronics", 190.0, 4.50, True),
    ("Power", 231.0, 1.26, True),
    ("Propulsion", 252.0, 1.58, True),
    ("Navigation", 189.0, 3.50, True),
    ("Interior", 294.0, 1.96, True),
]
EXTRACTS = [("CockpitSeat", 294.0), ("CockpitDash", 231.0)]

unreal.SystemLibrary.execute_console_command(
    None, "Interchange.FeatureFlags.Import.FBX 0")
lib = unreal.EditorAssetLibrary
tools = unreal.AssetToolsHelpers.get_asset_tools()
mel = unreal.MaterialEditingLibrary


def import_mesh(name, gate_cm, lods):
    out = []
    for lod in lods:
        asset = "SM_LB_CP_%s%s" % (name, lod)
        task = unreal.AssetImportTask()
        task.set_editor_properties({
            "filename": os.path.join(FBX, asset + ".fbx"),
            "destination_path": MESH_DIR, "destination_name": asset,
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
        mesh = lib.load_asset("%s/%s" % (MESH_DIR, asset))
        if mesh is None:
            raise RuntimeError("FAIL CLOSED: %s import failed" % asset)
        ext = mesh.get_bounds().box_extent
        longest = max(ext.x, ext.y, ext.z) * 2.0
        if longest > gate_cm:
            raise RuntimeError(
                "FAIL CLOSED: %s longest %.0f cm exceeds ship-fit gate "
                "%.0f cm" % (asset, longest, gate_cm))
        unreal.log("COMPONENT IMPORTED %s longest=%.0f cm" %
                   (asset, longest))
        out.append(mesh)
    return out


def import_texture(key, fname, name, srgb):
    path = os.path.join(SRC, "TexturesByModel", key, fname)
    if not os.path.isfile(path):
        raise RuntimeError("FAIL CLOSED: %s missing on disk" % path)
    task = unreal.AssetImportTask()
    task.set_editor_properties({
        "filename": path, "destination_path": TEX_DIR,
        "destination_name": name, "automated": True,
        "replace_existing": True, "save": False})
    tools.import_asset_tasks([task])
    tex = unreal.load_asset("%s/%s" % (TEX_DIR, name))
    if tex is None:
        raise RuntimeError("FAIL CLOSED: %s import failed" % name)
    tex.set_editor_property("srgb", srgb)
    tex.set_editor_property("never_stream", True)
    return tex


def flat_material(name, rgb, rough, metal):
    path = "%s/%s" % (MAT_DIR, name)
    mat = unreal.load_asset(path)
    if mat is not None:
        return mat
    mat = tools.create_asset(name, MAT_DIR, unreal.Material,
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
    mel.recompile_material(mat)
    lib.save_asset(path)
    return mat


master = unreal.load_asset(MASTER)
if master is None:
    raise RuntimeError("FAIL CLOSED: master v003 missing")

interior_mi = None
for key, gate_cm, boost, textured in JOBS:
    meshes = import_mesh(key, gate_cm, ["_LOD0", "_LOD1"])
    if textured:
        bc = import_texture(key, "base_color.jpg",
                            "T_LB_CP_%s_BaseColor" % key, True)
        lib.save_asset(TEX_DIR + "/T_LB_CP_%s_BaseColor" % key)
        nm = import_texture(key, "normal.jpg", "T_LB_CP_%s_Normal" % key,
                            False)
        nm.set_editor_property("compression_settings",
            unreal.TextureCompressionSettings.TC_NORMALMAP)
        nm.set_editor_property("flip_green_channel", True)
        lib.save_asset(TEX_DIR + "/T_LB_CP_%s_Normal" % key)
        mr = import_texture(key, "metallic_roughness.jpg",
                            "T_LB_CP_%s_MR" % key, False)
        lib.save_asset(TEX_DIR + "/T_LB_CP_%s_MR" % key)
        mi_path = "%s/MI_LB_CP_%s" % (MAT_DIR, key)
        mi = unreal.load_asset(mi_path)
        if mi is None:
            mi = tools.create_asset("MI_LB_CP_%s" % key, MAT_DIR,
                unreal.MaterialInstanceConstant,
                unreal.MaterialInstanceConstantFactoryNew())
        mel.set_material_instance_parent(mi, master)
        mel.set_material_instance_texture_parameter_value(
            mi, "BaseColor", bc)
        mel.set_material_instance_texture_parameter_value(
            mi, "Normal", nm)
        mel.set_material_instance_texture_parameter_value(
            mi, "MetallicRoughness", mr)
        mel.set_material_instance_scalar_parameter_value(
            mi, "BaseColorBoost", boost)
        mel.update_material_instance(mi)
        lib.save_asset(mi_path)
        if key == "Interior":
            interior_mi = mi
        assign = mi
    else:
        # The clay hull wears flat cold steel until its texture stage
        # runs in Meshy (owner to generate; drop supersedes).
        assign = flat_material("M_LB_CP_HullClay",
                               (0.34, 0.36, 0.38), 0.45, 0.75)
    for mesh in meshes:
        slots = mesh.get_editor_property("static_materials")
        for index in range(len(slots)):
            mesh.set_material(index, assign)
        lib.save_asset(mesh.get_path_name().split(".")[0])

for name, gate_cm in EXTRACTS:
    meshes = import_mesh(name, gate_cm, [""])
    for mesh in meshes:
        slots = mesh.get_editor_property("static_materials")
        for index in range(len(slots)):
            if interior_mi is not None:
                mesh.set_material(index, interior_mi)
        lib.save_asset(mesh.get_path_name().split(".")[0])

unreal.log("COMPONENT SET IMPORT DONE: 6 components + 2 cockpit "
           "extracts")
