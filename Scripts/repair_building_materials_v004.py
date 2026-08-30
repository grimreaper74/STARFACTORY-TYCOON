"""Add a BaseColorBoost knob and lift the buildings against the floor.

Everything upstream is verified right - textures bound, sRGB on, metal
tamed - and the buildings still read charcoal because the camera meters
on a near-white floor and a 0.68-grey albedo sits far below it. That is
exposure, and it gets a KNOB, not a rewrite: the master gains
BaseColorBoost (default 1), instances go to 1.7. The owner tunes from
screenshots; the graph is rebuilt deterministically (expressions are
protected in 5.8)."""
import json
from datetime import datetime, timezone
from pathlib import Path
import unreal

root = Path(unreal.Paths.project_dir())
TEX_ROOT = ("/Game/LineBoss/Candidates/Spacecraft/StationMeshes_v001/"
            "Meshes/BuildingTextures")
MASTER = "%s/M_LB_Building_Master" % TEX_ROOT
out = root / "Saved/Audits/Spacecraft/building_materials_repair_v004.json"
if out.exists():
    raise RuntimeError("Receipt exists. Author v005.")
library = unreal.EditorAssetLibrary
mat_lib = unreal.MaterialEditingLibrary
master = library.load_asset(MASTER)
mat_lib.delete_all_material_expressions(master)

base = mat_lib.create_material_expression(
    master, unreal.MaterialExpressionTextureSampleParameter2D, -700, -250)
base.set_editor_property("parameter_name", "BaseColor")
boost = mat_lib.create_material_expression(
    master, unreal.MaterialExpressionScalarParameter, -700, -20)
boost.set_editor_property("parameter_name", "BaseColorBoost")
boost.set_editor_property("default_value", 1.0)
bmul = mat_lib.create_material_expression(
    master, unreal.MaterialExpressionMultiply, -420, -180)
assert mat_lib.connect_material_expressions(base, "RGB", bmul, "A")
assert mat_lib.connect_material_expressions(boost, "", bmul, "B")
assert mat_lib.connect_material_property(
    bmul, "", unreal.MaterialProperty.MP_BASE_COLOR)

mr = mat_lib.create_material_expression(
    master, unreal.MaterialExpressionTextureSampleParameter2D, -700, 150)
mr.set_editor_property("parameter_name", "MetallicRoughness")
mr.set_editor_property("sampler_type",
                       unreal.MaterialSamplerType.SAMPLERTYPE_LINEAR_COLOR)
assert mat_lib.connect_material_property(
    mr, "G", unreal.MaterialProperty.MP_ROUGHNESS)
scale = mat_lib.create_material_expression(
    master, unreal.MaterialExpressionScalarParameter, -420, 260)
scale.set_editor_property("parameter_name", "MetallicScale")
scale.set_editor_property("default_value", 1.0)
mmul = mat_lib.create_material_expression(
    master, unreal.MaterialExpressionMultiply, -200, 200)
assert mat_lib.connect_material_expressions(mr, "B", mmul, "A")
assert mat_lib.connect_material_expressions(scale, "", mmul, "B")
assert mat_lib.connect_material_property(
    mmul, "", unreal.MaterialProperty.MP_METALLIC)

normal = mat_lib.create_material_expression(
    master, unreal.MaterialExpressionTextureSampleParameter2D, -700, 480)
normal.set_editor_property("parameter_name", "Normal")
normal.set_editor_property("sampler_type",
                           unreal.MaterialSamplerType.SAMPLERTYPE_NORMAL)
assert mat_lib.connect_material_property(
    normal, "RGB", unreal.MaterialProperty.MP_NORMAL)
mat_lib.recompile_material(master)
library.save_loaded_asset(master, only_if_is_dirty=False)

rows = []
for asset in library.list_assets(TEX_ROOT, recursive=False):
    name = asset.split("/")[-1].split(".")[0]
    if not name.startswith("MI_"):
        continue
    mi = library.load_asset("%s/%s" % (TEX_ROOT, name))
    mat_lib.set_material_instance_scalar_parameter_value(
        mi, "BaseColorBoost", 1.7)
    mat_lib.set_material_instance_scalar_parameter_value(
        mi, "MetallicScale", 0.25)
    library.save_loaded_asset(mi, only_if_is_dirty=False)
    rows.append(name)
    print("boosted %s" % name)
out.write_text(json.dumps({
    "$schema": "lineboss/audit/building-materials-repair-v004/v1",
    "generated_utc": datetime.now(timezone.utc).isoformat(),
    "status": "PASS__BASECOLOR_BOOST_APPLIED",
    "boost": 1.7, "instances": rows}, indent=2), encoding="utf-8")
print("instances: %d" % len(rows))
