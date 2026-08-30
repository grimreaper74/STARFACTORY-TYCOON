"""Tame the buildings' metallic response. Addendum to repair v001.

Measured, not guessed: the packed metallic-roughness maps average
METALLIC 0.72 / roughness 0.32. Glossy metal in a scene without
reflection captures renders near-black - the dark-grey buildings in the
sighted screenshots. Blender previewed them white because its preview
world gives metal something to reflect. The style is painted panels;
0.72 metal is the generator overclaiming.

The master gains a MetallicScale parameter multiplying the map's B
channel; every instance dials it to 0.25. The expression list is
protected in 5.8, so the graph is REBUILT deterministically rather than
introspected - instances key on parameter names and survive untouched.
"""

import json
from datetime import datetime, timezone
from pathlib import Path
import unreal

root = Path(unreal.Paths.project_dir())
TEX_ROOT = ("/Game/LineBoss/Candidates/Spacecraft/StationMeshes_v001/"
            "Meshes/BuildingTextures")
MASTER = "%s/M_LB_Building_Master" % TEX_ROOT
out = root / "Saved/Audits/Spacecraft/building_materials_repair_v002.json"
if out.exists():
    raise RuntimeError("Refusing to rerun: receipt exists. Author v003.")

library = unreal.EditorAssetLibrary
mat_lib = unreal.MaterialEditingLibrary

master = library.load_asset(MASTER)
if master is None:
    raise RuntimeError("master material missing - run repair v001 first")

mat_lib.delete_all_material_expressions(master)

base = mat_lib.create_material_expression(
    master, unreal.MaterialExpressionTextureSampleParameter2D, -600, -200)
base.set_editor_property("parameter_name", "BaseColor")
mat_lib.connect_material_property(base, "RGB",
                                  unreal.MaterialProperty.MP_BASE_COLOR)

mr_node = mat_lib.create_material_expression(
    master, unreal.MaterialExpressionTextureSampleParameter2D, -600, 100)
mr_node.set_editor_property("parameter_name", "MetallicRoughness")
mr_node.set_editor_property(
    "sampler_type", unreal.MaterialSamplerType.SAMPLERTYPE_LINEAR_COLOR)
mat_lib.connect_material_property(mr_node, "G",
                                  unreal.MaterialProperty.MP_ROUGHNESS)

normal = mat_lib.create_material_expression(
    master, unreal.MaterialExpressionTextureSampleParameter2D, -600, 400)
normal.set_editor_property("parameter_name", "Normal")
normal.set_editor_property(
    "sampler_type", unreal.MaterialSamplerType.SAMPLERTYPE_NORMAL)
mat_lib.connect_material_property(normal, "RGB",
                                  unreal.MaterialProperty.MP_NORMAL)

scale = mat_lib.create_material_expression(
    master, unreal.MaterialExpressionScalarParameter, -350, 250)
scale.set_editor_property("parameter_name", "MetallicScale")
scale.set_editor_property("default_value", 1.0)
multiply = mat_lib.create_material_expression(
    master, unreal.MaterialExpressionMultiply, -150, 200)
ok_a = mat_lib.connect_material_expressions(mr_node, "B", multiply, "A")
ok_b = mat_lib.connect_material_expressions(scale, "", multiply, "B")
ok_out = mat_lib.connect_material_property(
    multiply, "", unreal.MaterialProperty.MP_METALLIC)
if not (ok_a and ok_b and ok_out):
    raise RuntimeError("failed to wire the metallic scale")
mat_lib.recompile_material(master)
library.save_loaded_asset(master, only_if_is_dirty=False)

failures = []
rows = []
for asset in library.list_assets(TEX_ROOT, recursive=False):
    name = asset.split("/")[-1].split(".")[0]
    if not name.startswith("MI_"):
        continue
    instance = library.load_asset("%s/%s" % (TEX_ROOT, name))
    if instance is None:
        failures.append("instance %s failed to load" % name)
        continue
    mat_lib.set_material_instance_scalar_parameter_value(
        instance, "MetallicScale", 0.25)
    library.save_loaded_asset(instance, only_if_is_dirty=False)
    applied = mat_lib.get_material_instance_scalar_parameter_value(
        instance, "MetallicScale")
    ok = abs(applied - 0.25) < 0.001
    if not ok:
        failures.append("%s did not keep MetallicScale" % name)
    rows.append({"instance": name, "metallic_scale": applied, "ok": ok})

report = {
    "$schema": "lineboss/audit/building-materials-repair-v002/v1",
    "generated_utc": datetime.now(timezone.utc).isoformat(),
    "status": ("PASS__METALLIC_TAMED" if not failures and rows
               else "FAIL_CLOSED__METALLIC_REPAIR"),
    "measurement": ("PowerPlant metallic-roughness map: R 0.998, "
                    "G(roughness) 0.322, B(metallic) 0.723 - sampled in "
                    "Blender over 20k texels"),
    "instances": rows,
    "failures": failures,
}
out.parent.mkdir(parents=True, exist_ok=True)
out.write_text(json.dumps(report, indent=2), encoding="utf-8")
print(json.dumps({"status": report["status"], "instances": len(rows),
                  "failures": failures}, indent=2))
if failures or not rows:
    raise RuntimeError("; ".join(failures) if failures else "no instances")
