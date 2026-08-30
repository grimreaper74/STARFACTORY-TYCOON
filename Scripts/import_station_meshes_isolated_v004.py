"""import_station_meshes_isolated_v004.py - the owner's morning drops,
batch two: the drone ChargingDock (dock furniture, ~1.6 m, dresses the
presenter's dock pads) and the HullFabBay (HullFabricator catalogue
station, 16 x 12 m). Same fail-closed lane as v003: bounds gates,
correct colour-space flags, MI per model on the compiling
M_LB_MeshyPBR_v003 master, measured albedo boosts (both generations
measured bright: 1.00 - no lift needed), MI assigned to every slot.
"""

import os
import unreal

SRC = (r"C:\Users\greg_\Projects\LineBossCarFactory_Unreal 5.8"
       r"\SourceAssets\Candidate\Spacecraft\StationModels_MeshyIntake_v001")
FBX = SRC + r"\FBX"
ROOT = "/Game/LineBoss/Candidates/Spacecraft/StationMeshes_v001"
MAT_DIR = ROOT + "/Materials"
TEX_DIR = ROOT + "/Textures"
MASTER = MAT_DIR + "/M_LB_MeshyPBR_v003"

# (key, mesh base name, dest dir, max X cm, max Y cm, boost)
JOBS = [
    ("ChargingDock", "SM_LB_DR_ChargingDock", ROOT + "/Drones",
     160.0, 160.0, 1.00),
    ("HullFabBay", "SM_LB_ST_HullFabBay", ROOT + "/Meshes",
     1600.0, 1200.0, 1.00),
]

unreal.SystemLibrary.execute_console_command(
    None, "Interchange.FeatureFlags.Import.FBX 0")
lib = unreal.EditorAssetLibrary
tools = unreal.AssetToolsHelpers.get_asset_tools()
mel = unreal.MaterialEditingLibrary
master = unreal.load_asset(MASTER)
if master is None:
    raise RuntimeError("FAIL CLOSED: master v003 missing")
failures = []


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


for key, base, dest, max_x, max_y, boost in JOBS:
    meshes = []
    for lod in (0, 1):
        name = "%s_LOD%d" % (base, lod) if key != "ChargingDock" \
            else ("%s" % base if lod == 0 else "%s_LOD1" % base)
        # The dock's presenter soft path expects the plain name for
        # LOD0 (drone-family convention); stations keep _LOD0.
        fbx_name = "%s_LOD%d" % (base, lod)
        task = unreal.AssetImportTask()
        task.set_editor_properties({
            "filename": os.path.join(FBX, fbx_name + ".fbx"),
            "destination_path": dest, "destination_name": name,
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
        mesh = lib.load_asset("%s/%s" % (dest, name))
        if mesh is None:
            failures.append(name + ": IMPORT FAILED")
            continue
        ext = mesh.get_bounds().box_extent
        size = (ext.x * 2.0, ext.y * 2.0, ext.z * 2.0)
        fits = ((size[0] <= max_x * 1.05 and size[1] <= max_y * 1.05)
                or (size[0] <= max_y * 1.05 and size[1] <= max_x * 1.05))
        unreal.log("IMPORTED %s size_cm=(%.0f, %.0f, %.0f) fits=%s"
                   % (name, size[0], size[1], size[2], fits))
        if not fits:
            failures.append("%s: OVERRUNS ENVELOPE" % name)
        meshes.append(mesh)
    if failures:
        break
    bc = import_texture(key, "base_color.jpg",
                        "T_LB_%s_BaseColor" % key, True)
    lib.save_asset(TEX_DIR + "/T_LB_%s_BaseColor" % key)
    nm = import_texture(key, "normal.jpg", "T_LB_%s_Normal" % key, False)
    nm.set_editor_property(
        "compression_settings",
        unreal.TextureCompressionSettings.TC_NORMALMAP)
    nm.set_editor_property("flip_green_channel", True)
    lib.save_asset(TEX_DIR + "/T_LB_%s_Normal" % key)
    mr = import_texture(key, "metallic_roughness.jpg",
                        "T_LB_%s_MR" % key, False)
    lib.save_asset(TEX_DIR + "/T_LB_%s_MR" % key)
    mi_path = "%s/MI_LB_%s" % (MAT_DIR, key)
    mi = unreal.load_asset(mi_path)
    if mi is None:
        mi = tools.create_asset(
            "MI_LB_%s" % key, MAT_DIR, unreal.MaterialInstanceConstant,
            unreal.MaterialInstanceConstantFactoryNew())
    mel.set_material_instance_parent(mi, master)
    mel.set_material_instance_texture_parameter_value(mi, "BaseColor", bc)
    mel.set_material_instance_texture_parameter_value(mi, "Normal", nm)
    mel.set_material_instance_texture_parameter_value(
        mi, "MetallicRoughness", mr)
    mel.set_material_instance_scalar_parameter_value(
        mi, "BaseColorBoost", boost)
    mel.update_material_instance(mi)
    lib.save_asset(mi_path)
    for mesh in meshes:
        slots = mesh.get_editor_property("static_materials")
        for index in range(len(slots)):
            mesh.set_material(index, mi)
        lib.save_asset(mesh.get_path_name().split(".")[0])
    unreal.log("WIRED %s: %d meshes, boost %.2f" %
               (key, len(meshes), boost))

if failures:
    raise RuntimeError("FAILED CLOSED: " + "; ".join(failures))
unreal.log("BATCH TWO IMPORT DONE: ChargingDock + HullFabBay")
