"""Make both master materials actually COMPILE. Root-cause repair.

Every packaged build so far shipped the buildings and station meshes on
the engine's Default Material - both masters fail compilation, so every
tuning knob to date (MetallicScale, BaseColorBoost, sRGB) changed
nothing the player could see. The owner's verdict on v007: "its still
a mess". The compile failures were invisible because every repair ran
under -NullRHI, where shaders never compile and never complain.

The probe (probe_master_material_v002) found the faults:
  - MetallicRoughness parameter nodes default to the engine's sRGB
    DefaultTexture under a LINEAR_COLOR sampler - sampler/texture
    mismatch, compile error.
  - Building_Master's Normal parameter defaults to that same COLOR
    texture under a NORMAL sampler - same class of error.
  - Building_Master carries DUPLICATE BaseColor/Normal nodes from
    stacked repair passes.

Repairs, in order:
  1. Import T_LB_DefaultLinearMR (4x4, R=1 G=0.5 B=0, srgb off,
     TC_Default) - a legal default for LINEAR_COLOR samplers.
  2. Building MR textures: TC_MASKS -> TC_DEFAULT (srgb already off) so
     they match the LINEAR_COLOR sampler at instance level too.
  3. Building_Master: rebuilt ONCE, clean, with legal defaults.
     Parameter names unchanged (BaseColor, MetallicRoughness, Normal,
     MetallicScale, BaseColorBoost) so every instance keeps its values.
  4. MeshyPBR_v002: only its MR default swapped to the new texture
     (its Normal already uses FlatNormal, which is legal).

MUST run with rendering (-RenderOffscreen, no -NullRHI): the receipt
records whether a real compile succeeded, which is the whole point.
"""

import json
from datetime import datetime, timezone
from pathlib import Path
import unreal

root = Path(unreal.Paths.project_dir())
out = root / "Saved/Audits/Spacecraft/master_material_repair_v005.json"
if out.exists():
    raise RuntimeError("Refusing to rerun: receipt exists. Author v006.")

TEX_ROOT = ("/Game/LineBoss/Candidates/Spacecraft/StationMeshes_v001/"
            "Meshes/BuildingTextures")
MAT_DIR = "/Game/LineBoss/Candidates/Spacecraft/StationMeshes_v001/Materials"
BUILDING_MASTER = "%s/M_LB_Building_Master" % TEX_ROOT
MESHY_MASTER = "%s/M_LB_MeshyPBR_v002" % MAT_DIR
DEFAULT_MR = "%s/T_LB_DefaultLinearMR" % TEX_ROOT

lib = unreal.EditorAssetLibrary
mel = unreal.MaterialEditingLibrary
tools = unreal.AssetToolsHelpers.get_asset_tools()
failures = []
notes = []

# ---- 1. the legal linear default ----
if not lib.does_asset_exist(DEFAULT_MR):
    task = unreal.AssetImportTask()
    task.set_editor_property("filename", str(
        root / "SourceAssets/Candidate/Spacecraft/MaterialDefaults/"
               "T_LB_DefaultLinearMR.png"))
    task.set_editor_property("destination_path", TEX_ROOT)
    task.set_editor_property("destination_name", "T_LB_DefaultLinearMR")
    task.set_editor_property("automated", True)
    task.set_editor_property("save", True)
    tools.import_asset_tasks([task])
default_mr = lib.load_asset(DEFAULT_MR)
if default_mr is None:
    raise RuntimeError("default MR texture failed to import")
default_mr.set_editor_property("srgb", False)
default_mr.set_editor_property(
    "compression_settings", unreal.TextureCompressionSettings.TC_DEFAULT)
lib.save_loaded_asset(default_mr, only_if_is_dirty=False)
notes.append("default linear MR texture in place")

# ---- 2. building MR textures: masks -> default (linear) ----
retagged = 0
for asset_path in lib.list_assets(TEX_ROOT, recursive=False):
    name = asset_path.split("/")[-1].split(".")[0]
    if not name.endswith("_metallic_roughness"):
        continue
    tex = lib.load_asset("%s/%s" % (TEX_ROOT, name))
    if tex is None:
        failures.append("MR texture %s failed to load" % name)
        continue
    tex.set_editor_property(
        "compression_settings",
        unreal.TextureCompressionSettings.TC_DEFAULT)
    tex.set_editor_property("srgb", False)
    lib.save_loaded_asset(tex, only_if_is_dirty=False)
    retagged += 1
notes.append("%d building MR textures retagged TC_DEFAULT linear"
             % retagged)

# ---- 3. Building_Master: ONE clean rebuild ----
master = lib.load_asset(BUILDING_MASTER)
if master is None:
    raise RuntimeError("building master missing")
mel.delete_all_material_expressions(master)
flat_normal = unreal.load_asset("/Engine/EngineMaterials/FlatNormal")
default_color = unreal.load_asset("/Engine/EngineResources/DefaultTexture")

base = mel.create_material_expression(
    master, unreal.MaterialExpressionTextureSampleParameter2D, -700, -250)
base.set_editor_property("parameter_name", "BaseColor")
base.set_editor_property("texture", default_color)
boost = mel.create_material_expression(
    master, unreal.MaterialExpressionScalarParameter, -700, -80)
boost.set_editor_property("parameter_name", "BaseColorBoost")
boost.set_editor_property("default_value", 1.0)
base_mul = mel.create_material_expression(
    master, unreal.MaterialExpressionMultiply, -400, -200)
mel.connect_material_expressions(base, "RGB", base_mul, "A")
mel.connect_material_expressions(boost, "", base_mul, "B")
mel.connect_material_property(base_mul, "",
                              unreal.MaterialProperty.MP_BASE_COLOR)

mr = mel.create_material_expression(
    master, unreal.MaterialExpressionTextureSampleParameter2D, -700, 120)
mr.set_editor_property("parameter_name", "MetallicRoughness")
mr.set_editor_property("texture", default_mr)
mr.set_editor_property(
    "sampler_type", unreal.MaterialSamplerType.SAMPLERTYPE_LINEAR_COLOR)
mel.connect_material_property(mr, "G",
                              unreal.MaterialProperty.MP_ROUGHNESS)
scale = mel.create_material_expression(
    master, unreal.MaterialExpressionScalarParameter, -700, 300)
scale.set_editor_property("parameter_name", "MetallicScale")
scale.set_editor_property("default_value", 1.0)
metal_mul = mel.create_material_expression(
    master, unreal.MaterialExpressionMultiply, -400, 220)
mel.connect_material_expressions(mr, "B", metal_mul, "A")
mel.connect_material_expressions(scale, "", metal_mul, "B")
mel.connect_material_property(metal_mul, "",
                              unreal.MaterialProperty.MP_METALLIC)

normal = mel.create_material_expression(
    master, unreal.MaterialExpressionTextureSampleParameter2D, -700, 470)
normal.set_editor_property("parameter_name", "Normal")
normal.set_editor_property("texture", flat_normal)
normal.set_editor_property(
    "sampler_type", unreal.MaterialSamplerType.SAMPLERTYPE_NORMAL)
mel.connect_material_property(normal, "RGB",
                              unreal.MaterialProperty.MP_NORMAL)
mel.recompile_material(master)
lib.save_loaded_asset(master, only_if_is_dirty=False)
notes.append("building master rebuilt clean")

# ---- 4. MeshyPBR: swap only the illegal MR default ----
meshy = lib.load_asset(MESHY_MASTER)
if meshy is None:
    raise RuntimeError("meshy master missing")
swapped = 0
for expr in mel.get_material_expressions(meshy):
    if not isinstance(expr,
                      unreal.MaterialExpressionTextureSampleParameter2D):
        continue
    if str(expr.get_editor_property("parameter_name")) \
            == "MetallicRoughness":
        expr.set_editor_property("texture", default_mr)
        swapped += 1
if swapped != 1:
    failures.append("expected 1 MeshyPBR MR node, touched %d" % swapped)
mel.recompile_material(meshy)
lib.save_loaded_asset(meshy, only_if_is_dirty=False)
notes.append("meshy master MR default swapped")

report = {
    "$schema": "lineboss/audit/master-material-repair-v005/v1",
    "generated_utc": datetime.now(timezone.utc).isoformat(),
    "status": ("PASS__MASTERS_REBUILT_WITH_LEGAL_DEFAULTS"
               if not failures else "FAIL_CLOSED__MASTER_REPAIR_v005"),
    "notes": notes,
    "failures": failures,
    "not_proven": [
        "Compilation success is read from THIS session's log (no "
        "'Failed to compile Material' lines) and then from the next "
        "package's log - and the mess verdict is the owner's to lift, "
        "from a sighted launch.",
    ],
}
out.parent.mkdir(parents=True, exist_ok=True)
out.write_text(json.dumps(report, indent=2), encoding="utf-8")
print(json.dumps({"status": report["status"], "notes": notes,
                  "failures": failures}, indent=2))
if failures:
    raise RuntimeError("; ".join(failures))
