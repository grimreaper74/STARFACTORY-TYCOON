"""Replace point-pool lighting with even, readable stylised material values.

The Meshy stations retain their genuine geometry and existing functional
details.  Candidate-local material overrides lift only the broad floor/zone
surfaces, while the ten temporary process/task lights are disabled; the six
common fixtures, sun and skylight remain.  This removes the white-pool artifact
without increasing the dynamic-light count.
"""
import hashlib
import json
from pathlib import Path

import unreal


PROJECT = Path(r"C:\Users\greg_\Projects\LineBossCarFactory_Unreal 5.8")
MAP = "/Game/LineBoss/Candidates/PressShop/PressShop2126_v002/Maps/LB_PressShop_2126_Steam_v002"
ROOT = "/Game/LineBoss/Candidates/PressShop/PressShop2126_v002/Materials"
PROTECTED = PROJECT / "Content" / "LineBoss" / "Maps" / "LB_PressShop_BuilderAuthorityCandidate_v438.umap"
REPORT = PROJECT / "Saved" / "Audits" / "PressShopIntegration" / "pressshop_2126_v002_even_readability_v015.json"
TAG = unreal.Name("LB.PressShop.2126.v002.EvenReadability.v015")


def digest(path):
    hasher = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            hasher.update(block)
    return hasher.hexdigest()


def make_surface(name, base_colour, emission_colour):
    path = ROOT + "/" + name
    material = unreal.load_asset(path) if unreal.EditorAssetLibrary.does_asset_exist(path) else None
    if material is None:
        material = unreal.AssetToolsHelpers.get_asset_tools().create_asset(
            name, ROOT, unreal.Material, unreal.MaterialFactoryNew())
    if not isinstance(material, unreal.Material):
        raise RuntimeError("Could not create stylised surface " + name)
    mel = unreal.MaterialEditingLibrary
    mel.delete_all_material_expressions(material)
    base = mel.create_material_expression(material, unreal.MaterialExpressionConstant3Vector, -420, -100)
    base.set_editor_property("constant", unreal.LinearColor(*base_colour, 1.0))
    rough = mel.create_material_expression(material, unreal.MaterialExpressionConstant, -420, 15)
    rough.set_editor_property("r", 0.82)
    emissive = mel.create_material_expression(material, unreal.MaterialExpressionConstant3Vector, -420, -170)
    emissive.set_editor_property("constant", unreal.LinearColor(*emission_colour, 1.0))
    mel.connect_material_property(base, "", unreal.MaterialProperty.MP_BASE_COLOR)
    mel.connect_material_property(rough, "", unreal.MaterialProperty.MP_ROUGHNESS)
    mel.connect_material_property(emissive, "", unreal.MaterialProperty.MP_EMISSIVE_COLOR)
    mel.recompile_material(material)
    unreal.EditorAssetLibrary.save_loaded_asset(material, only_if_is_dirty=False)
    return material


if not PROTECTED.is_file():
    raise RuntimeError("Protected v438 map missing")
before = digest(PROTECTED)
if not unreal.EditorLoadingAndSavingUtils.load_map(MAP):
    raise RuntimeError("Could not load candidate v002")
actors = {actor.get_actor_label(): actor for actor in unreal.EditorLevelLibrary.get_all_level_actors()}
if any(TAG in actor.tags for actor in actors.values()):
    raise RuntimeError("v015 even-readability pass already applied")

concrete = make_surface("M_LB_PS2126v002_WarmConcreteEven", (0.33, 0.30, 0.25), (0.17, 0.15, 0.12))
pale_green = make_surface("M_LB_PS2126v002_PaleGreenEven", (0.235, 0.480, 0.330), (0.090, 0.180, 0.120))
deck = actors.get("2126 v002 | charcoal factory deck")
if not isinstance(deck, unreal.StaticMeshActor):
    raise RuntimeError("Missing candidate deck")
deck.static_mesh_component.set_material(0, concrete)
deck.tags = list(deck.tags) + [TAG]

zones = []
for label, actor in actors.items():
    if not label.startswith("2126 v002 | pale-green process island"):
        continue
    if not isinstance(actor, unreal.StaticMeshActor):
        raise RuntimeError("Invalid process-island actor " + label)
    actor.static_mesh_component.set_material(0, pale_green)
    actor.tags = list(actor.tags) + [TAG]
    zones.append(label)
if len(zones) != 4:
    raise RuntimeError("Expected four process islands, found %d" % len(zones))

disabled = []
for label, actor in actors.items():
    if not isinstance(actor, unreal.RectLight):
        continue
    if label.startswith("2126 v002 | functional process light") or label.endswith("task light"):
        component = actor.light_component
        component.set_visibility(False, True)
        component.set_editor_property("affects_world", False)
        actor.set_actor_hidden_in_game(True)
        actor.set_is_temporarily_hidden_in_editor(True)
        actor.tags = list(actor.tags) + [TAG, unreal.Name("LB.Lighting.DisabledForEvenReview")]
        disabled.append(label)
if len(disabled) != 10:
    raise RuntimeError("Expected ten existing process/task lights, disabled %d" % len(disabled))

if not unreal.EditorLevelLibrary.save_current_level():
    raise RuntimeError("Could not save v015 even-readability pass")
after = digest(PROTECTED)
if before != after:
    raise RuntimeError("Protected v438 changed")
REPORT.parent.mkdir(parents=True, exist_ok=True)
REPORT.write_text(json.dumps({
    "status": "PASS__EVEN_STYLISED_READABILITY_APPLIED",
    "candidate_map": MAP,
    "floor_material": concrete.get_path_name(),
    "zone_material": pale_green.get_path_name(),
    "process_task_lights_disabled": disabled,
    "remaining_active_dynamic_lights": 8,
    "new_light_actors": 0,
    "roof_created": False,
    "protected_v438_sha256_before": before,
    "protected_v438_sha256_after": after,
}, indent=2), encoding="utf-8")
unreal.log("PRESSSHOP_2126_V002_EVEN_READABILITY_V015_PASS")
