"""build_station_materials_v002.py - supersedes v001's constant
metallic/roughness ("models aren't rendering full detail" - owner,
2026-08-25). Wires the true Meshy metallic_roughness maps (extracted
per-model by extract_mr_textures_v001.py; glTF convention: metallic=B,
roughness=G), pins every model texture to full resolution
(never-stream), and gives the factory floor a procedural panel grid so
the empty floor reads as a floor, not a void. Re-parents the existing
material instances; meshes keep their slots.

Run headless (editor closed):
  UnrealEditor-Cmd.exe <proj> -Unattended ... -ExecutePythonScript="<this>"
"""

import os
import unreal

TEX_SRC = (r"C:\Users\greg_\Projects\LineBossCarFactory_Unreal 5.8"
           r"\SourceAssets\Candidate\Spacecraft"
           r"\StationModels_MeshyIntake_v001\TexturesByModel")
ROOT = "/Game/LineBoss/Candidates/Spacecraft/StationMeshes_v001"
MAT_DIR = ROOT + "/Materials"
TEX_DIR = ROOT + "/Textures"
MAP_PATH = ("/Game/LineBoss/Candidates/Spacecraft/SpacecraftFactory_v001"
            "/Maps/LB_SpacecraftFactory_v001")

KEYS = ["RollingMill", "PowerPlant", "StorageRack", "CircuitFab",
        "PowerCellPlant", "PropulsionStation", "SubAssemblyRobot",
        "DroneAssembly", "DroneCargoLift", "DroneSpray", "DroneWinch"]

lib = unreal.EditorAssetLibrary
tools = unreal.AssetToolsHelpers.get_asset_tools()
mel = unreal.MaterialEditingLibrary
failures = []

# ---- master material v002: full PBR from the three Meshy maps -------
MASTER = MAT_DIR + "/M_LB_MeshyPBR_v002"
master = unreal.load_asset(MASTER)
if master is None:
    master = tools.create_asset("M_LB_MeshyPBR_v002", MAT_DIR,
                                unreal.Material,
                                unreal.MaterialFactoryNew())
    base = mel.create_material_expression(
        master, unreal.MaterialExpressionTextureSampleParameter2D,
        -600, -300)
    base.set_editor_property("parameter_name", "BaseColor")
    mel.connect_material_property(base, "RGB",
                                  unreal.MaterialProperty.MP_BASE_COLOR)
    norm = mel.create_material_expression(
        master, unreal.MaterialExpressionTextureSampleParameter2D,
        -600, 60)
    norm.set_editor_property("parameter_name", "Normal")
    norm.set_editor_property(
        "sampler_type", unreal.MaterialSamplerType.SAMPLERTYPE_NORMAL)
    flat = unreal.load_asset("/Engine/EngineMaterials/FlatNormal")
    if flat is not None:
        norm.set_editor_property("texture", flat)
    mel.connect_material_property(norm, "RGB",
                                  unreal.MaterialProperty.MP_NORMAL)
    mr = mel.create_material_expression(
        master, unreal.MaterialExpressionTextureSampleParameter2D,
        -600, 420)
    mr.set_editor_property("parameter_name", "MetallicRoughness")
    mr.set_editor_property(
        "sampler_type",
        unreal.MaterialSamplerType.SAMPLERTYPE_LINEAR_COLOR)
    # glTF: metallic rides BLUE, roughness rides GREEN.
    mel.connect_material_property(mr, "B",
                                  unreal.MaterialProperty.MP_METALLIC)
    mel.connect_material_property(mr, "G",
                                  unreal.MaterialProperty.MP_ROUGHNESS)
    mel.recompile_material(master)
    lib.save_asset(MASTER)
    unreal.log("MASTER v002 created")


def import_texture(path, name, srgb):
    task = unreal.AssetImportTask()
    task.set_editor_properties({
        "filename": path, "destination_path": TEX_DIR,
        "destination_name": name, "automated": True,
        "replace_existing": True, "save": False})
    tools.import_asset_tasks([task])
    tex = unreal.load_asset("%s/%s" % (TEX_DIR, name))
    if tex is not None:
        tex.set_editor_property("srgb", srgb)
        tex.set_editor_property("never_stream", True)
        lib.save_asset("%s/%s" % (TEX_DIR, name))
    return tex


for key in KEYS:
    mi = unreal.load_asset("%s/MI_LB_%s" % (MAT_DIR, key))
    if mi is None:
        failures.append(key + ": material instance missing")
        continue
    mel.set_material_instance_parent(mi, master)
    mr_path = os.path.join(TEX_SRC, key, "metallic_roughness.jpg")
    if os.path.isfile(mr_path):
        mr_tex = import_texture(mr_path, "T_LB_%s_MR" % key, False)
        if mr_tex is not None:
            mel.set_material_instance_texture_parameter_value(
                mi, "MetallicRoughness", mr_tex)
            unreal.log("MR WIRED %s" % key)
        else:
            failures.append(key + ": MR import failed")
    else:
        unreal.log("MR MISSING on disk for %s - constants remain" % key)
    lib.save_asset("%s/MI_LB_%s" % (MAT_DIR, key))
    # Pin the v001 textures to full resolution too.
    for suffix in ("BaseColor", "Normal"):
        tex = unreal.load_asset("%s/T_LB_%s_%s" % (TEX_DIR, key, suffix))
        if tex is not None:
            tex.set_editor_property("never_stream", True)
            lib.save_asset("%s/T_LB_%s_%s" % (TEX_DIR, key, suffix))

# ---- floor v002: procedural panel grid ------------------------------
FLOOR = MAT_DIR + "/M_LB_FactoryFloor_v002"
floor_mat = unreal.load_asset(FLOOR)
if floor_mat is None:
    floor_mat = tools.create_asset("M_LB_FactoryFloor_v002", MAT_DIR,
                                   unreal.Material,
                                   unreal.MaterialFactoryNew())
    wp = mel.create_material_expression(
        floor_mat, unreal.MaterialExpressionWorldPosition, -1100, 0)
    mask = mel.create_material_expression(
        floor_mat, unreal.MaterialExpressionComponentMask, -950, 0)
    mask.set_editor_property("r", True)
    mask.set_editor_property("g", True)
    mask.set_editor_property("b", False)
    mask.set_editor_property("a", False)
    mel.connect_material_expressions(wp, "", mask, "")
    scale = mel.create_material_expression(
        floor_mat, unreal.MaterialExpressionDivide, -800, 0)
    tile = mel.create_material_expression(
        floor_mat, unreal.MaterialExpressionConstant, -950, 140)
    tile.set_editor_property("r", 1000.0)  # 10 m panels
    mel.connect_material_expressions(mask, "", scale, "A")
    mel.connect_material_expressions(tile, "", scale, "B")
    frac = mel.create_material_expression(
        floor_mat, unreal.MaterialExpressionFrac, -650, 0)
    mel.connect_material_expressions(scale, "", frac, "")
    # Distance from panel centre: |frac - 0.5| * 2 per axis, take max.
    half = mel.create_material_expression(
        floor_mat, unreal.MaterialExpressionConstant, -650, 140)
    half.set_editor_property("r", 0.5)
    sub = mel.create_material_expression(
        floor_mat, unreal.MaterialExpressionSubtract, -500, 0)
    mel.connect_material_expressions(frac, "", sub, "A")
    mel.connect_material_expressions(half, "", sub, "B")
    ab = mel.create_material_expression(
        floor_mat, unreal.MaterialExpressionAbs, -380, 0)
    mel.connect_material_expressions(sub, "", ab, "")
    maskr = mel.create_material_expression(
        floor_mat, unreal.MaterialExpressionComponentMask, -260, -40)
    maskr.set_editor_property("r", True)
    maskr.set_editor_property("g", False)
    maskg = mel.create_material_expression(
        floor_mat, unreal.MaterialExpressionComponentMask, -260, 60)
    maskg.set_editor_property("r", False)
    maskg.set_editor_property("g", True)
    mel.connect_material_expressions(ab, "", maskr, "")
    mel.connect_material_expressions(ab, "", maskg, "")
    mx = mel.create_material_expression(
        floor_mat, unreal.MaterialExpressionMax, -140, 0)
    mel.connect_material_expressions(maskr, "", mx, "A")
    mel.connect_material_expressions(maskg, "", mx, "B")
    # Line where near the panel edge (>0.48 of half-width).
    edge = mel.create_material_expression(
        floor_mat, unreal.MaterialExpressionConstant, -140, 140)
    edge.set_editor_property("r", 0.482)
    step = mel.create_material_expression(
        floor_mat, unreal.MaterialExpressionStep, -20, 0)
    mel.connect_material_expressions(edge, "", step, "Y")
    mel.connect_material_expressions(mx, "", step, "X")
    light = mel.create_material_expression(
        floor_mat, unreal.MaterialExpressionConstant3Vector, -20, -160)
    light.set_editor_property("constant",
                              unreal.LinearColor(0.5, 0.51, 0.53))
    dark = mel.create_material_expression(
        floor_mat, unreal.MaterialExpressionConstant3Vector, -20, 160)
    dark.set_editor_property("constant",
                             unreal.LinearColor(0.38, 0.39, 0.41))
    lerp = mel.create_material_expression(
        floor_mat, unreal.MaterialExpressionLinearInterpolate, 140, 0)
    mel.connect_material_expressions(light, "", lerp, "A")
    mel.connect_material_expressions(dark, "", lerp, "B")
    mel.connect_material_expressions(step, "", lerp, "Alpha")
    mel.connect_material_property(lerp, "",
                                  unreal.MaterialProperty.MP_BASE_COLOR)
    rough = mel.create_material_expression(
        floor_mat, unreal.MaterialExpressionConstant, 140, 200)
    rough.set_editor_property("r", 0.5)
    mel.connect_material_property(rough, "",
                                  unreal.MaterialProperty.MP_ROUGHNESS)
    mel.recompile_material(floor_mat)
    lib.save_asset(FLOOR)
    unreal.log("FLOOR v002 material created")

les = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
if not les.load_level(MAP_PATH):
    raise RuntimeError("FAIL CLOSED: could not load " + MAP_PATH)
actor_sub = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
floored = 0
for actor in actor_sub.get_all_level_actors():
    if isinstance(actor, unreal.StaticMeshActor) \
            and not actor.get_actor_label().startswith("LB_SC_Env_"):
        origin, extent = actor.get_actor_bounds(False)
        if extent.x > 3000 and extent.y > 3000 and extent.z < 200:
            comp = actor.get_component_by_class(
                unreal.StaticMeshComponent)
            comp.set_material(0, floor_mat)
            floored += 1
if floored == 0:
    raise RuntimeError("FAIL CLOSED: floor not found for v002 material")
if not les.save_current_level():
    raise RuntimeError("FAIL CLOSED: could not save map")

if failures:
    raise RuntimeError("MATERIAL v002 FAILED CLOSED: "
                       + "; ".join(failures))
unreal.log("MATERIALS v002 DONE: %d MIs on true PBR, floor gridded"
           % len(KEYS))
