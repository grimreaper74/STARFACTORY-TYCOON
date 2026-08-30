"""build_station_materials_v001.py - deterministic materials for the
Meshy station and drone meshes. Three FBX import runs proved the legacy
importer silently drops Meshy's extension-less textures, so this pass
stops trusting it: import the .fbm textures explicitly, build ONE master
PBR material, instance it per model, assign to every slot of every LOD,
and fail closed if anything is missing.

Run headless (editor closed):
  UnrealEditor-Cmd.exe <proj> /Engine/Maps/Entry -Unattended ...
    -ExecutePythonScript="<this file>"
"""

import os
import shutil
import unreal

FBX_DIR = (r"C:\Users\greg_\Projects\LineBossCarFactory_Unreal 5.8"
           r"\SourceAssets\Candidate\Spacecraft"
           r"\StationModels_MeshyIntake_v001\FBX")
ROOT = "/Game/LineBoss/Candidates/Spacecraft/StationMeshes_v001"
MESH_DIR = ROOT + "/Meshes"
DRONE_DIR = ROOT + "/Drones"
MAT_DIR = ROOT + "/Materials"
TEX_DIR = ROOT + "/Textures"

# (key, fbm source base, mesh assets that wear it)
STATION_SETS = [
    ("RollingMill", "SM_LB_ST_RollingMill_LOD0",
     [MESH_DIR + "/SM_LB_ST_RollingMill_LOD0",
      MESH_DIR + "/SM_LB_ST_RollingMill_LOD1"]),
    ("PowerPlant", "SM_LB_ST_PowerPlant_LOD0",
     [MESH_DIR + "/SM_LB_ST_PowerPlant_LOD0",
      MESH_DIR + "/SM_LB_ST_PowerPlant_LOD1"]),
    ("StorageRack", "SM_LB_ST_StorageRack_LOD0",
     [MESH_DIR + "/SM_LB_ST_StorageRack_LOD0",
      MESH_DIR + "/SM_LB_ST_StorageRack_LOD1"]),
    ("CircuitFab", "SM_LB_ST_CircuitFab_LOD0",
     [MESH_DIR + "/SM_LB_ST_CircuitFab_LOD0",
      MESH_DIR + "/SM_LB_ST_CircuitFab_LOD1"]),
    ("PowerCellPlant", "SM_LB_ST_PowerCellPlant_LOD0",
     [MESH_DIR + "/SM_LB_ST_PowerCellPlant_LOD0",
      MESH_DIR + "/SM_LB_ST_PowerCellPlant_LOD1"]),
    ("PropulsionStation", "SM_LB_ST_PropulsionStation_LOD0",
     [MESH_DIR + "/SM_LB_ST_PropulsionStation_LOD0",
      MESH_DIR + "/SM_LB_ST_PropulsionStation_LOD1"]),
    ("SubAssemblyRobot", "SM_LB_ST_SubAssemblyRobot_LOD0",
     [MESH_DIR + "/SM_LB_ST_SubAssemblyRobot_LOD0",
      MESH_DIR + "/SM_LB_ST_SubAssemblyRobot_LOD1"]),
]
DRONE_SETS = [
    ("DroneAssembly", "SM_LB_DR_Assembly_Body",
     [DRONE_DIR + "/SM_LB_DR_Assembly_Body"]
     + [DRONE_DIR + "/SM_LB_DR_Assembly_Pod" + t
        for t in ("FR", "BR", "BL", "FL")]),
    ("DroneCargoLift", "SM_LB_DR_CargoLift_Body",
     [DRONE_DIR + "/SM_LB_DR_CargoLift_Body"]
     + [DRONE_DIR + "/SM_LB_DR_CargoLift_Pod" + t
        for t in ("FR", "BR", "BL", "FL", "MR", "ML")]),
    ("DroneSpray", "SM_LB_DR_Spray_Body",
     [DRONE_DIR + "/SM_LB_DR_Spray_Body"]
     + [DRONE_DIR + "/SM_LB_DR_Spray_Pod" + t
        for t in ("FR", "BR", "BL", "FL")]),
    ("DroneWinch", "SM_LB_DR_Winch_Body",
     [DRONE_DIR + "/SM_LB_DR_Winch_Body"]
     + [DRONE_DIR + "/SM_LB_DR_Winch_Pod" + t
        for t in ("FR", "BR", "BL", "FL")]),
]

lib = unreal.EditorAssetLibrary
tools = unreal.AssetToolsHelpers.get_asset_tools()
mel = unreal.MaterialEditingLibrary
for d in (MAT_DIR, TEX_DIR):
    if not lib.does_directory_exist(d):
        lib.make_directory(d)

failures = []


def ensure_jpg(fbm_base, stem):
    """Meshy textures are extension-less; give the importer a .jpg."""
    fbm = os.path.join(FBX_DIR, fbm_base + ".fbm")
    bare = os.path.join(fbm, stem)
    jpg = os.path.join(fbm, stem + ".jpg")
    if not os.path.isfile(jpg):
        if not os.path.isfile(bare):
            return None
        shutil.copyfile(bare, jpg)
    return jpg


def import_texture(path, name):
    task = unreal.AssetImportTask()
    task.set_editor_properties({
        "filename": path, "destination_path": TEX_DIR,
        "destination_name": name, "automated": True,
        "replace_existing": True, "save": True})
    tools.import_asset_tasks([task])
    return unreal.load_asset("%s/%s" % (TEX_DIR, name))


# ---- master material -------------------------------------------------
MASTER = MAT_DIR + "/M_LB_MeshyPBR_v001"
master = unreal.load_asset(MASTER)
if master is None:
    master = tools.create_asset("M_LB_MeshyPBR_v001", MAT_DIR,
                                unreal.Material,
                                unreal.MaterialFactoryNew())
    base = mel.create_material_expression(
        master, unreal.MaterialExpressionTextureSampleParameter2D,
        -500, -300)
    base.set_editor_property("parameter_name", "BaseColor")
    mel.connect_material_property(base, "RGB",
                                  unreal.MaterialProperty.MP_BASE_COLOR)
    norm = mel.create_material_expression(
        master, unreal.MaterialExpressionTextureSampleParameter2D,
        -500, 100)
    norm.set_editor_property("parameter_name", "Normal")
    norm.set_editor_property(
        "sampler_type", unreal.MaterialSamplerType.SAMPLERTYPE_NORMAL)
    flat = unreal.load_asset("/Engine/EngineMaterials/FlatNormal")
    if flat is None:
        flat = unreal.load_asset("/Engine/EngineMaterials/DefaultNormal")
    if flat is not None:
        norm.set_editor_property("texture", flat)
    mel.connect_material_property(norm, "RGB",
                                  unreal.MaterialProperty.MP_NORMAL)
    rough = mel.create_material_expression(
        master, unreal.MaterialExpressionScalarParameter, -500, 350)
    rough.set_editor_property("parameter_name", "Roughness")
    rough.set_editor_property("default_value", 0.6)
    mel.connect_material_property(rough, "",
                                  unreal.MaterialProperty.MP_ROUGHNESS)
    metal = mel.create_material_expression(
        master, unreal.MaterialExpressionScalarParameter, -500, 500)
    metal.set_editor_property("parameter_name", "Metallic")
    metal.set_editor_property("default_value", 0.25)
    mel.connect_material_property(metal, "",
                                  unreal.MaterialProperty.MP_METALLIC)
    mel.recompile_material(master)
    lib.save_asset(MASTER)
    unreal.log("MASTER MATERIAL created")

# ---- per-model instance + assignment ---------------------------------
applied = 0
for key, fbm_base, mesh_paths in STATION_SETS + DRONE_SETS:
    bc_path = ensure_jpg(fbm_base, "base_color")
    nm_path = ensure_jpg(fbm_base, "normal")
    if bc_path is None:
        failures.append(key + ": base_color texture missing on disk")
        continue
    bc_tex = import_texture(bc_path, "T_LB_%s_BaseColor" % key)
    nm_tex = import_texture(nm_path, "T_LB_%s_Normal" % key) \
        if nm_path else None
    if bc_tex is None:
        failures.append(key + ": base_color import failed")
        continue
    if nm_tex is not None:
        nm_tex.set_editor_property(
            "compression_settings",
            unreal.TextureCompressionSettings.TC_NORMALMAP)
        nm_tex.set_editor_property("srgb", False)
        nm_tex.set_editor_property("flip_green_channel", True)
        lib.save_asset(TEX_DIR + "/T_LB_%s_Normal" % key)

    mi_path = "%s/MI_LB_%s" % (MAT_DIR, key)
    mi = unreal.load_asset(mi_path)
    if mi is None:
        mi = tools.create_asset(
            "MI_LB_%s" % key, MAT_DIR, unreal.MaterialInstanceConstant,
            unreal.MaterialInstanceConstantFactoryNew())
    mel.set_material_instance_parent(mi, master)
    mel.set_material_instance_texture_parameter_value(
        mi, "BaseColor", bc_tex)
    if nm_tex is not None:
        mel.set_material_instance_texture_parameter_value(
            mi, "Normal", nm_tex)
    lib.save_asset(mi_path)

    for mesh_path in mesh_paths:
        mesh = unreal.load_asset(mesh_path)
        if mesh is None:
            failures.append(key + ": mesh missing " + mesh_path)
            continue
        slots = mesh.get_editor_property("static_materials")
        for index in range(len(slots)):
            mesh.set_material(index, mi)
        lib.save_asset(mesh_path)
        applied += 1
    unreal.log("MATERIALS APPLIED %s -> %d meshes" %
               (key, len(mesh_paths)))

if failures:
    raise RuntimeError(
        "MATERIAL PASS FAILED CLOSED: " + "; ".join(failures))
unreal.log("STATION MATERIALS DONE: %d mesh assignments" % applied)
