"""Make the supplied Meshy machines readable through per-instance paint only.

The imported Meshy assets remain byte-untouched.  This candidate-local pass
overrides their six known material slots on map instances: the dominant
foundry-charcoal and green slots become a legible Cairnwell lacquer, while the
existing warm-white, red, yellow and steel details stay distinct.  It adds no
geometry, lights, roof, or wheels.
"""
import hashlib
import json
from pathlib import Path

import unreal


PROJECT = Path(r"C:\Users\greg_\Projects\LineBossCarFactory_Unreal 5.8")
MAP = "/Game/LineBoss/Candidates/PressShop/PressShop2126_v002/Maps/LB_PressShop_2126_Steam_v002"
ROOT = "/Game/LineBoss/Candidates/PressShop/PressShop2126_v002/Materials"
PROTECTED = PROJECT / "Content" / "LineBoss" / "Maps" / "LB_PressShop_BuilderAuthorityCandidate_v438.umap"
REPORT = PROJECT / "Saved" / "Audits" / "PressShopIntegration" / "pressshop_2126_v002_meshy_repaint_v010.json"
TAG = unreal.Name("LB.PressShop.2126.v002.MeshyPaint.v010")


def digest(path):
    hasher = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            hasher.update(block)
    return hasher.hexdigest()


def make_paint(name, colour, roughness, metallic, emissive_gain):
    path = ROOT + "/" + name
    material = unreal.load_asset(path) if unreal.EditorAssetLibrary.does_asset_exist(path) else None
    if material is None:
        material = unreal.AssetToolsHelpers.get_asset_tools().create_asset(
            name, ROOT, unreal.Material, unreal.MaterialFactoryNew())
    if not isinstance(material, unreal.Material):
        raise RuntimeError("Could not create candidate paint material " + name)
    mel = unreal.MaterialEditingLibrary
    mel.delete_all_material_expressions(material)
    base = mel.create_material_expression(material, unreal.MaterialExpressionConstant3Vector, -420, -100)
    base.set_editor_property("constant", unreal.LinearColor(*colour, 1.0))
    rough = mel.create_material_expression(material, unreal.MaterialExpressionConstant, -420, 15)
    rough.set_editor_property("r", roughness)
    metal = mel.create_material_expression(material, unreal.MaterialExpressionConstant, -420, 100)
    metal.set_editor_property("r", metallic)
    mel.connect_material_property(base, "", unreal.MaterialProperty.MP_BASE_COLOR)
    mel.connect_material_property(rough, "", unreal.MaterialProperty.MP_ROUGHNESS)
    mel.connect_material_property(metal, "", unreal.MaterialProperty.MP_METALLIC)
    if emissive_gain:
        gain = mel.create_material_expression(material, unreal.MaterialExpressionConstant, -420, -170)
        gain.set_editor_property("r", emissive_gain)
        output = mel.create_material_expression(material, unreal.MaterialExpressionMultiply, -150, -90)
        mel.connect_material_expressions(base, "", output, "A")
        mel.connect_material_expressions(gain, "", output, "B")
        mel.connect_material_property(output, "", unreal.MaterialProperty.MP_EMISSIVE_COLOR)
    mel.recompile_material(material)
    unreal.EditorAssetLibrary.save_loaded_asset(material, only_if_is_dirty=False)
    return material


if not PROTECTED.is_file():
    raise RuntimeError("Protected v438 map missing")
before = digest(PROTECTED)
if not unreal.EditorLoadingAndSavingUtils.load_map(MAP):
    raise RuntimeError("Could not load v002 candidate map")
actors = {actor.get_actor_label(): actor for actor in unreal.EditorLevelLibrary.get_all_level_actors()}
if any(TAG in actor.tags for actor in actors.values()):
    raise RuntimeError("v010 mesh paint is already applied")

# Exact brand green (#1F4B44) encoded in linear space.  A restrained emissive
# multiplier gives a matte painted surface a readable value in the roofless,
# low-light review scene; it is not a new light source.
green = make_paint("M_LB_PS2126v002_CairnwellLacquerReadable", (0.0126, 0.0697, 0.0574), 0.47, 0.08, 3.0)
steel = make_paint("M_LB_PS2126v002_AutomationSteelReadable", (0.1620, 0.1866, 0.2011), 0.38, 0.20, 0.45)
required = (
    "MESHY v002 | S02 Draw / form",
    "MESHY v002 | S03 Trim",
    "MESHY v002 | S04 Pierce",
    "MESHY v002 | S05 Flange / hem",
    "MESHY v002 | S06 Vision / outfeed",
)
changed = []
for label in required:
    actor = actors.get(label)
    if not isinstance(actor, unreal.StaticMeshActor):
        raise RuntimeError("Missing Meshy press actor " + label)
    component = actor.static_mesh_component
    materials = component.get_editor_property("static_mesh").get_editor_property("static_materials")
    if len(materials) != 6:
        raise RuntimeError("Unexpected Meshy material slot count for %s: %d" % (label, len(materials)))
    component.set_material(0, green)
    component.set_material(4, steel)
    component.set_material(5, green)
    for index, expected in ((0, green), (4, steel), (5, green)):
        actual = component.get_material(index)
        if actual.get_path_name() != expected.get_path_name():
            raise RuntimeError("Material override did not stick: %s slot %d" % (label, index))
    actor.tags = list(actor.tags) + [TAG, unreal.Name("LB.Meshy.PaintedInstance")]
    changed.append(label)

feeder = actors.get("S00 | Meshy coil-free autonomous feeder")
if not isinstance(feeder, unreal.StaticMeshActor):
    raise RuntimeError("Missing coil-free Meshy feeder")
if len(feeder.static_mesh_component.get_editor_property("static_mesh").get_editor_property("static_materials")) != 1:
    raise RuntimeError("Unexpected coil-free feeder material count")
feeder.static_mesh_component.set_material(0, green)
feeder.tags = list(feeder.tags) + [TAG, unreal.Name("LB.Meshy.PaintedInstance")]
changed.append(feeder.get_actor_label())

for label in (
    "ROBOT v002 | S01 laser-tend robot",
    "ROBOT v002 | S02 draw quality robot",
    "ROBOT v002 | S04 pierce handling robot",
    "ROBOT v002 | S06 vision stack robot",
):
    actor = actors.get(label)
    if not isinstance(actor, unreal.StaticMeshActor):
        raise RuntimeError("Missing automation robot " + label)
    actor.static_mesh_component.set_material(0, steel)
    actor.tags = list(actor.tags) + [TAG]

if not unreal.EditorLevelLibrary.save_current_level():
    raise RuntimeError("Could not save candidate v002 mesh paint")
after = digest(PROTECTED)
if before != after:
    raise RuntimeError("Protected v438 changed")

REPORT.parent.mkdir(parents=True, exist_ok=True)
REPORT.write_text(json.dumps({
    "status": "PASS__MESHY_INSTANCE_PAINT_REPAIRED",
    "candidate_map": MAP,
    "changed_meshy_instances": changed,
    "paint_overrides": {"body_slots": [0, 5], "steel_slot": 4, "feeder_slots": [0]},
    "new_dynamic_lights": 0,
    "new_geometry": 0,
    "roof_created": False,
    "protected_v438_sha256_before": before,
    "protected_v438_sha256_after": after,
}, indent=2), encoding="utf-8")
unreal.log("PRESSSHOP_2126_V002_MESHY_INSTANCE_PAINT_V010_PASS")
