"""Repaint the eight separate 3D coils for the fixed 2.5D management view.

The approved ten-section master-coil geometry is unchanged.  Candidate-local
unlit materials make bare steel, grey wrap, straps and labels consistently
readable under the fixed B_stylized camera while preserving separate actors.
"""
import hashlib
import json
from pathlib import Path
import unreal

PROJECT = Path(r"C:\Users\greg_\Projects\LineBossCarFactory_Unreal 5.8")
MAP = "/Game/LineBoss/Candidates/PressShop/PressShop2126_FullHall_v001/Maps/LB_PressShop_2126_FullHall_v001"
MAT_ROOT = "/Game/LineBoss/Candidates/PressShop/PressShop2126_FullHall_v001/Materials"
RECEIPT = PROJECT / "Saved" / "Audits" / "PressShop2126" / "repaint_separate_coils_v001_receipt.json"
TAG = unreal.Name("LB.PressShop.2126.CoilRepaint.v001")
COILS = (
    ("2126 LOG | delivery coil 02 | approved packaged master coil", "wrapped"),
    ("2126 LOG | delivery coil 03 | approved packaged master coil", "bare"),
    ("2126 LOG | delivery coil 04 | approved packaged master coil", "wrapped"),
    ("2126 LOG | coil 01 mid-transfer under autonomous gantry", "bare"),
    ("2126 COIL | verification cell active load", "wrapped"),
    ("2126 COIL | magnetic buffer load A", "bare"),
    ("2126 COIL | magnetic buffer load C", "wrapped"),
    ("2126 FRONT END | active feed coil", "bare"),
)
COLORS = {
    "Galvanized": unreal.LinearColor(0.46, 0.49, 0.52, 1.0),
    "WrapGrey": unreal.LinearColor(0.30, 0.33, 0.35, 1.0),
    "Charcoal": unreal.LinearColor(0.08, 0.10, 0.11, 1.0),
    "WarmWhite": unreal.LinearColor(0.62, 0.60, 0.54, 1.0),
    "SafetyYellow": unreal.LinearColor(0.72, 0.54, 0.00, 1.0),
}
PROTECTED = {
    PROJECT / "Content" / "LineBoss" / "Maps" / "LB_PressShop_BuilderAuthorityCandidate_v438.umap": "5029c9d827d9a1d72c12f27ee757c9bc1e47febd5006ce6d7ba319aad2e7fec8",
    PROJECT / "Content" / "LineBoss" / "Candidates" / "PressShop" / "PressShop2126_v002" / "Maps" / "LB_PressShop_2126_Steam_v002.umap": "cc09cf46d33e8a562d97f5a3bc35a5b42c9582d8e4650cf315694ebf340e4aa0",
}


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest().lower()


def create_unlit(name, color):
    path = MAT_ROOT + "/M_CA_MW_2126_Coil" + name + "_Unlit_v001"
    if unreal.EditorAssetLibrary.does_asset_exist(path):
        raise RuntimeError("refusing to overwrite candidate coil material " + path)
    material = unreal.AssetToolsHelpers.get_asset_tools().create_asset(
        "M_CA_MW_2126_Coil" + name + "_Unlit_v001", MAT_ROOT, unreal.Material, unreal.MaterialFactoryNew())
    if not isinstance(material, unreal.Material):
        raise RuntimeError("could not create material " + name)
    material.set_editor_property("shading_model", unreal.MaterialShadingModel.MSM_UNLIT)
    constant = unreal.MaterialEditingLibrary.create_material_expression(material, unreal.MaterialExpressionConstant3Vector, -220, 0)
    constant.set_editor_property("constant", color)
    if not unreal.MaterialEditingLibrary.connect_material_property(constant, "", unreal.MaterialProperty.MP_EMISSIVE_COLOR):
        raise RuntimeError("could not connect material " + name)
    unreal.MaterialEditingLibrary.recompile_material(material)
    if not unreal.EditorAssetLibrary.save_loaded_asset(material, only_if_is_dirty=False):
        raise RuntimeError("could not save material " + name)
    return material


before = {str(path): digest(path) for path in PROTECTED}
for path, expected in PROTECTED.items():
    if before[str(path)] != expected:
        raise RuntimeError("protected map missing or changed: " + str(path))
materials = {name: create_unlit(name, color) for name, color in COLORS.items()}
if not unreal.EditorLoadingAndSavingUtils.load_map(MAP):
    raise RuntimeError("could not load isolated 2126 candidate")
actors = {actor.get_actor_label(): actor for actor in unreal.EditorLevelLibrary.get_all_level_actors()}
if any(TAG in actor.tags for actor in actors.values()):
    raise RuntimeError("coil repaint pass already tagged")

rows = []
for label, kind in COILS:
    actor = actors.get(label)
    if not isinstance(actor, unreal.StaticMeshActor):
        raise RuntimeError("separate coil missing: " + label)
    component = actor.static_mesh_component
    if component.get_num_materials() != 10:
        raise RuntimeError("master coil material contract changed on " + label)
    surface = materials["WrapGrey"] if kind == "wrapped" else materials["Galvanized"]
    overrides = (
        materials["Galvanized"], # 0 coil steel
        materials["Charcoal"],   # 1 structure
        surface,                   # 2 wrap/body
        surface,                   # 3 overlap
        surface,                   # 4 patch
        materials["SafetyYellow"],# 5 straps
        materials["Charcoal"],   # 6 fibre/inner
        materials["Charcoal"],   # 7 structure
        materials["WarmWhite"],  # 8 paper label
        materials["Charcoal"],   # 9 shell/end details
    )
    for index, material in enumerate(overrides):
        component.set_material(index, material)
    actor.tags = list(actor.tags) + [TAG, unreal.Name("LB.Coil." + kind.capitalize())]
    rows.append({"label": label, "finish": kind, "material_slots": len(overrides)})

if not unreal.EditorLoadingAndSavingUtils.save_current_level():
    raise RuntimeError("could not save separate coil repaint")
unreal.EditorLoadingAndSavingUtils.save_dirty_packages(True, True)
after = {str(path): digest(path) for path in PROTECTED}
if after != before:
    raise RuntimeError("protected maps changed during coil repaint")
RECEIPT.parent.mkdir(parents=True, exist_ok=True)
RECEIPT.write_text(json.dumps({
    "status": "PASS__2126_SEPARATE_COILS_READABLE_WRAPPED_AND_BARE",
    "map": MAP,
    "coil_count": len(rows),
    "wrapped_count": sum(1 for row in rows if row["finish"] == "wrapped"),
    "bare_count": sum(1 for row in rows if row["finish"] == "bare"),
    "coils": rows,
    "geometry_changed": False,
    "source_material_slots_preserved": 10,
    "created_materials": {name: material.get_path_name() for name, material in materials.items()},
    "protected_sha256_before": before,
    "protected_sha256_after": after,
}, indent=2, sort_keys=True) + "\n", encoding="utf-8")
unreal.log("PRESSSHOP_2126_COIL_REPAINT_PASS coils=%d" % len(rows))
unreal.SystemLibrary.quit_editor()
