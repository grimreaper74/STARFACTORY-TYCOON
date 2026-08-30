"""Give the imported buildings their real PBR materials.

The first sighted screenshot showed every building rendering dark. The
inspection found why, and both faults were the intake's:

  1. Every Meshy .blend names its one material "material", so each FBX
     import OVERWROTE the same material asset - ten buildings wearing
     whichever import ran last.
  2. No textures were imported at all. The unpacked PNGs stayed in
     SourceAssets; the shared material is an untextured phong. Dark.

This lane imports each building's three maps (base colour, packed
metallic-roughness, normal), builds ONE master PBR material with the
glTF channel convention (G = roughness, B = metallic), makes a material
instance per building, assigns it to slot 0 and saves. Fail-closed:
refuses to rerun over its receipt, and reads the assignment back.
"""

import json
from datetime import datetime, timezone
from pathlib import Path
import unreal

root = Path(unreal.Paths.project_dir())
MESH_ROOT = "/Game/LineBoss/Candidates/Spacecraft/StationMeshes_v001/Meshes"
TEX_ROOT = MESH_ROOT + "/BuildingTextures"
out = root / "Saved/Audits/Spacecraft/building_materials_repair_v001.json"

if out.exists():
    raise RuntimeError("Refusing to rerun: receipt exists. Author v002.")

# mesh asset name -> SourceAssets folder holding its Textures/
BUILDINGS = {
    "SM_LB_ST_Smelter": "Buildings_v001",
    "SM_LB_ST_SubAssemblyHall_v003": "Buildings_v002",
    "SM_LB_ST_PowerPlant_v002": "Buildings_v002",
    "SM_LB_ST_ShipFactoryHall_v002": "Buildings_v003",
    "SM_LB_ST_AssemblyStation_v001": "Buildings_v004",
    "SM_LB_ST_AssemblyStationMk2_v001": "Buildings_v004",
    "SM_LB_ST_StructureFab_v001": "Buildings_v004",
    "SM_LB_ST_FitOutFab_v001": "Buildings_v004",
    "SM_LB_ST_DeliveryDock_v001": "Buildings_v004",
    "SM_LB_ST_StorageSilo_v001": "Buildings_v004",
}

library = unreal.EditorAssetLibrary
tools = unreal.AssetToolsHelpers.get_asset_tools()
mat_lib = unreal.MaterialEditingLibrary

failures = []
rows = []


def import_texture(png_path, dest_name, is_normal, is_linear):
    task = unreal.AssetImportTask()
    task.set_editor_property("filename", str(png_path))
    task.set_editor_property("destination_path", TEX_ROOT)
    task.set_editor_property("destination_name", dest_name)
    task.set_editor_property("automated", True)
    task.set_editor_property("replace_existing", True)
    task.set_editor_property("save", True)
    tools.import_asset_tasks([task])
    tex = library.load_asset("%s/%s" % (TEX_ROOT, dest_name))
    if tex is None:
        failures.append("texture %s failed to import" % dest_name)
        return None
    if is_normal:
        tex.set_editor_property("compression_settings",
                                unreal.TextureCompressionSettings.TC_NORMALMAP)
        tex.set_editor_property("srgb", False)
        tex.set_editor_property("lod_group",
                                unreal.TextureGroup.TEXTUREGROUP_WORLD_NORMAL_MAP)
    elif is_linear:
        tex.set_editor_property("compression_settings",
                                unreal.TextureCompressionSettings.TC_MASKS)
        tex.set_editor_property("srgb", False)
    library.save_loaded_asset(tex, only_if_is_dirty=False)
    return tex


# ---- 1. the master material, built once ----
MASTER = "%s/M_LB_Building_Master" % TEX_ROOT
if library.does_asset_exist(MASTER):
    master = library.load_asset(MASTER)
else:
    master = tools.create_asset("M_LB_Building_Master", TEX_ROOT,
                                unreal.Material, unreal.MaterialFactoryNew())
    base = mat_lib.create_material_expression(
        master, unreal.MaterialExpressionTextureSampleParameter2D, -600, -200)
    base.set_editor_property("parameter_name", "BaseColor")
    mat_lib.connect_material_property(base, "RGB",
                                      unreal.MaterialProperty.MP_BASE_COLOR)
    mr = mat_lib.create_material_expression(
        master, unreal.MaterialExpressionTextureSampleParameter2D, -600, 100)
    mr.set_editor_property("parameter_name", "MetallicRoughness")
    mr.set_editor_property("sampler_type",
                           unreal.MaterialSamplerType.SAMPLERTYPE_LINEAR_COLOR)
    # glTF packing: G is roughness, B is metallic.
    mat_lib.connect_material_property(mr, "G",
                                      unreal.MaterialProperty.MP_ROUGHNESS)
    mat_lib.connect_material_property(mr, "B",
                                      unreal.MaterialProperty.MP_METALLIC)
    normal = mat_lib.create_material_expression(
        master, unreal.MaterialExpressionTextureSampleParameter2D, -600, 400)
    normal.set_editor_property("parameter_name", "Normal")
    normal.set_editor_property("sampler_type",
                               unreal.MaterialSamplerType.SAMPLERTYPE_NORMAL)
    mat_lib.connect_material_property(normal, "RGB",
                                      unreal.MaterialProperty.MP_NORMAL)
    mat_lib.recompile_material(master)
    library.save_loaded_asset(master, only_if_is_dirty=False)

# ---- 2. per building: textures, instance, assignment ----
for name, folder in BUILDINGS.items():
    tex_dir = root / "SourceAssets/Candidate/Spacecraft" / folder / "Textures"
    maps = {}
    for suffix, is_normal, is_linear in (
            ("base_color", False, False),
            ("metallic_roughness", False, True),
            ("normal", True, False)):
        png = tex_dir / ("%s_%s.png" % (name, suffix))
        if not png.exists():
            failures.append("missing source texture %s" % png)
            continue
        maps[suffix] = import_texture(png, "T_%s_%s" % (name, suffix),
                                      is_normal, is_linear)
    if len(maps) != 3 or any(v is None for v in maps.values()):
        continue

    instance_name = "MI_%s" % name
    instance_path = "%s/%s" % (TEX_ROOT, instance_name)
    if library.does_asset_exist(instance_path):
        instance = library.load_asset(instance_path)
    else:
        factory = unreal.MaterialInstanceConstantFactoryNew()
        instance = tools.create_asset(instance_name, TEX_ROOT,
                                      unreal.MaterialInstanceConstant,
                                      factory)
    mat_lib.set_material_instance_parent(instance, master)
    mat_lib.set_material_instance_texture_parameter_value(
        instance, "BaseColor", maps["base_color"])
    mat_lib.set_material_instance_texture_parameter_value(
        instance, "MetallicRoughness", maps["metallic_roughness"])
    mat_lib.set_material_instance_texture_parameter_value(
        instance, "Normal", maps["normal"])
    library.save_loaded_asset(instance, only_if_is_dirty=False)

    mesh = library.load_asset("%s/%s" % (MESH_ROOT, name))
    if mesh is None:
        failures.append("mesh %s missing" % name)
        continue
    mesh.set_material(0, instance)
    library.save_loaded_asset(mesh, only_if_is_dirty=False)

    # Read the assignment BACK - a set that silently failed to stick is
    # exactly the class of bug this lane exists to end.
    reloaded = library.load_asset("%s/%s" % (MESH_ROOT, name))
    applied = reloaded.get_material(0)
    ok = applied is not None and applied.get_name() == instance_name
    if not ok:
        failures.append("%s did not keep its instance" % name)
    rows.append({"mesh": name, "instance": instance_name, "applied": ok})

report = {
    "$schema": "lineboss/audit/building-materials-repair-v001/v1",
    "generated_utc": datetime.now(timezone.utc).isoformat(),
    "status": ("PASS__BUILDING_PBR_MATERIALS_APPLIED" if not failures
               else "FAIL_CLOSED__BUILDING_MATERIALS__PARTIAL"),
    "why": ("Every FBX import overwrote one shared material named "
            "'material', and no textures were ever imported - both "
            "faults of the intake, found by the first sighted "
            "screenshot."),
    "master_material": MASTER,
    "assets": rows,
    "failures": failures,
}
out.parent.mkdir(parents=True, exist_ok=True)
out.write_text(json.dumps(report, indent=2), encoding="utf-8")
print(json.dumps({"status": report["status"],
                  "repaired": len([r for r in rows if r["applied"]]),
                  "failures": failures}, indent=2))
if failures:
    raise RuntimeError("; ".join(failures))
