"""import_cargo_materials_v001.py - the Cargo-01 hull look. The form
meshes imported bare (the Scout's craft mesh carries materials in its
FBX; the cargo forms did not), so the first cargo showcase rendered an
untextured pale hull. Same deterministic pipeline as the stations:
import the three cargo textures, one MI on the compiling
M_LB_MeshyPBR_v003 master, assigned to every slot of all six form
meshes. Boost 1.0 (measured bright)."""

import os
import unreal

TEX_SRC = (r"C:\Users\greg_\Projects\LineBossCarFactory_Unreal 5.8"
           r"\SourceAssets\Candidate\Spacecraft"
           r"\StationModels_MeshyIntake_v001\TexturesByModel\Cargo01")
ROOT = "/Game/LineBoss/Candidates/Spacecraft/StationMeshes_v001"
MAT_DIR = ROOT + "/Materials"
TEX_DIR = ROOT + "/Textures"
MASTER = MAT_DIR + "/M_LB_MeshyPBR_v003"
MESH_DIR = ("/Game/LineBoss/Candidates/Spacecraft/SpacecraftTestBay_v001"
            "/Meshes")

lib = unreal.EditorAssetLibrary
tools = unreal.AssetToolsHelpers.get_asset_tools()
mel = unreal.MaterialEditingLibrary
master = unreal.load_asset(MASTER)
if master is None:
    raise RuntimeError("FAIL CLOSED: master v003 missing")


def import_texture(fname, name, srgb):
    path = os.path.join(TEX_SRC, fname)
    if not os.path.isfile(path):
        raise RuntimeError("FAIL CLOSED: %s missing" % path)
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
    lib.save_asset("%s/%s" % (TEX_DIR, name))
    return tex


bc = import_texture("base_color.jpg", "T_LB_SC_Cargo01_BaseColor", True)
nm = import_texture("normal.jpg", "T_LB_SC_Cargo01_Normal", False)
nm.set_editor_property("compression_settings",
                       unreal.TextureCompressionSettings.TC_NORMALMAP)
nm.set_editor_property("flip_green_channel", True)
lib.save_asset(TEX_DIR + "/T_LB_SC_Cargo01_Normal")
mr = import_texture("metallic_roughness.jpg", "T_LB_SC_Cargo01_MR", False)

MI_PATH = MAT_DIR + "/MI_LB_SC_Cargo01_Hull"
mi = unreal.load_asset(MI_PATH)
if mi is None:
    mi = tools.create_asset("MI_LB_SC_Cargo01_Hull", MAT_DIR,
                            unreal.MaterialInstanceConstant,
                            unreal.MaterialInstanceConstantFactoryNew())
mel.set_material_instance_parent(mi, master)
mel.set_material_instance_texture_parameter_value(mi, "BaseColor", bc)
mel.set_material_instance_texture_parameter_value(mi, "Normal", nm)
mel.set_material_instance_texture_parameter_value(mi, "MetallicRoughness",
                                                  mr)
mel.set_material_instance_scalar_parameter_value(mi, "BaseColorBoost", 1.0)
mel.update_material_instance(mi)
lib.save_asset(MI_PATH)

count = 0
for form in ("Chassis", "Airframe", "Fitted"):
    for lod in (0, 1):
        path = "%s/SM_LB_SC_Cargo01_%s_v001_LOD%d" % (MESH_DIR, form, lod)
        mesh = unreal.load_asset(path)
        if mesh is None:
            raise RuntimeError("FAIL CLOSED: %s missing" % path)
        slots = mesh.get_editor_property("static_materials")
        for index in range(len(slots)):
            mesh.set_material(index, mi)
        lib.save_asset(path)
        count += 1
unreal.log("CARGO HULL MATERIAL DONE: MI on %d meshes" % count)
