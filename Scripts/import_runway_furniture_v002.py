"""import_runway_furniture_v002.py - the runway strip section and
chicane pylon (owner's evening drops 2026-08-26, generated from the
LaunchRunway_v001 blockouts). Runway SITE FURNITURE, never
player-built. Strip measured 19.6 x 14.4 x 0.9 m (20 x 16 envelope,
albedo 0.242 -> boost 0.91); pylon 2.58 x 2.58 x 5.0 m (height-
governed, albedo 0.089 -> boost 2.48). Same lane as v001: bounds
gates, colour-space-correct textures, one MI per model on the
M_LB_MeshyPBR_v003 master, MI on every slot of both LODs. Fails
closed at every step.
"""

import os
import unreal

SRC = (r"C:\Users\greg_\Projects\LineBossCarFactory_Unreal 5.8"
       r"\SourceAssets\Candidate\Spacecraft\RunwayFurniture_MeshyIntake_v001")
FBX = SRC + r"\FBX"
ROOT = "/Game/LineBoss/Candidates/Spacecraft/StationMeshes_v001"
MESH_DIR = ROOT + "/Meshes"
MAT_DIR = ROOT + "/Materials"
TEX_DIR = ROOT + "/Textures"
MASTER = MAT_DIR + "/M_LB_MeshyPBR_v003"
JOBS2 = [
    ("RunwayStrip", 2000.0, 1600.0, 0.91),
    ("ChicanePylon", 300.0, 300.0, 2.48),
]

unreal.SystemLibrary.execute_console_command(
    None, "Interchange.FeatureFlags.Import.FBX 0")
lib = unreal.EditorAssetLibrary
tools = unreal.AssetToolsHelpers.get_asset_tools()
mel = unreal.MaterialEditingLibrary


def run_job(KEY, FOOT_X, FOOT_Y, BOOST):
    TEX_SRC = os.path.join(SRC, "TexturesByModel", KEY)
    failures = []
    meshes = []
    for lod in (0, 1):
        name = "SM_LB_RW_%s_LOD%d" % (KEY, lod)
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
            "auto_generate_collision": True, "import_uniform_scale": 1.0,
            "convert_scene": True, "convert_scene_unit": True,
            "normal_import_method":
                unreal.FBXNormalImportMethod.FBXNIM_IMPORT_NORMALS_AND_TANGENTS})
        task.options = ui
        tools.import_asset_tasks([task])
        unreal.AutomationUtilsBlueprintLibrary.finish_all_asset_compilation()
        mesh = lib.load_asset("%s/%s" % (MESH_DIR, name))
        if mesh is None:
            failures.append(name + ": IMPORT FAILED")
            continue
        ext = mesh.get_bounds().box_extent
        size = (ext.x * 2.0, ext.y * 2.0, ext.z * 2.0)
        fits = ((size[0] <= FOOT_X * 1.05 and size[1] <= FOOT_Y * 1.05)
                or (size[0] <= FOOT_Y * 1.05 and size[1] <= FOOT_X * 1.05))
        unreal.log("IMPORTED %s size_cm=(%.0f, %.0f, %.0f) fits=%s"
                   % (name, size[0], size[1], size[2], fits))
        if not fits:
            failures.append("%s: OVERRUNS FOOTPRINT" % name)
    meshes.append(mesh)
    if failures:
        raise RuntimeError("FAILED CLOSED: " + "; ".join(failures))


    def import_texture(fname, name, srgb):
        path = os.path.join(TEX_SRC, fname)
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


    bc = import_texture("base_color.jpg", "T_LB_%s_BaseColor" % KEY, True)
    lib.save_asset(TEX_DIR + "/T_LB_%s_BaseColor" % KEY)
    nm = import_texture("normal.jpg", "T_LB_%s_Normal" % KEY, False)
    nm.set_editor_property("compression_settings",
                           unreal.TextureCompressionSettings.TC_NORMALMAP)
    nm.set_editor_property("flip_green_channel", True)
    lib.save_asset(TEX_DIR + "/T_LB_%s_Normal" % KEY)
    mr = import_texture("metallic_roughness.jpg", "T_LB_%s_MR" % KEY, False)
    lib.save_asset(TEX_DIR + "/T_LB_%s_MR" % KEY)

    master = unreal.load_asset(MASTER)
    if master is None:
        raise RuntimeError("FAIL CLOSED: master v003 missing")
    mi_path = "%s/MI_LB_%s" % (MAT_DIR, KEY)
    mi = unreal.load_asset(mi_path)
    if mi is None:
        mi = tools.create_asset("MI_LB_%s" % KEY, MAT_DIR,
                                unreal.MaterialInstanceConstant,
                                unreal.MaterialInstanceConstantFactoryNew())
    mel.set_material_instance_parent(mi, master)
    mel.set_material_instance_texture_parameter_value(mi, "BaseColor", bc)
    mel.set_material_instance_texture_parameter_value(mi, "Normal", nm)
    mel.set_material_instance_texture_parameter_value(mi, "MetallicRoughness",
                                                      mr)
    mel.set_material_instance_scalar_parameter_value(mi, "BaseColorBoost",
                                                     BOOST)
    mel.update_material_instance(mi)
    lib.save_asset(mi_path)

    for mesh in meshes:
        slots = mesh.get_editor_property("static_materials")
        for index in range(len(slots)):
            mesh.set_material(index, mi)
        lib.save_asset(mesh.get_path_name().split(".")[0])
    unreal.log("%s IMPORT DONE: 2 LODs, MI on v003 master, boost %.2f"
               % (KEY, BOOST))


for job_key, job_fx, job_fy, job_boost in JOBS2:
    run_job(job_key, job_fx, job_fy, job_boost)
unreal.log("RUNWAY FURNITURE V002 IMPORT DONE")
