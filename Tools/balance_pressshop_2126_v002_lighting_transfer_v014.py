"""Balance the existing v002 light envelope and simplify transfer silhouettes.

No light actors are created.  Existing task lights are reduced to a practical
readability level after the Meshy body-paint fix, and the two existing transfer
rails are made Safety Yellow with no cast shadows so they read as one clean
overhead-handling language rather than black visual clutter.
"""
import hashlib
import json
from pathlib import Path

import unreal


PROJECT = Path(r"C:\Users\greg_\Projects\LineBossCarFactory_Unreal 5.8")
MAP = "/Game/LineBoss/Candidates/PressShop/PressShop2126_v002/Maps/LB_PressShop_2126_Steam_v002"
ROOT = "/Game/LineBoss/Candidates/PressShop/PressShop2126_v002/Materials"
PROTECTED = PROJECT / "Content" / "LineBoss" / "Maps" / "LB_PressShop_BuilderAuthorityCandidate_v438.umap"
REPORT = PROJECT / "Saved" / "Audits" / "PressShopIntegration" / "pressshop_2126_v002_lighting_transfer_balance_v014.json"
TAG = unreal.Name("LB.PressShop.2126.v002.LightingTransferBalance.v014")


def digest(path):
    hasher = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            hasher.update(block)
    return hasher.hexdigest()


if not PROTECTED.is_file():
    raise RuntimeError("Protected v438 map missing")
before = digest(PROTECTED)
if not unreal.EditorLoadingAndSavingUtils.load_map(MAP):
    raise RuntimeError("Could not load candidate v002")
actors = {actor.get_actor_label(): actor for actor in unreal.EditorLevelLibrary.get_all_level_actors()}
if any(TAG in actor.tags for actor in actors.values()):
    raise RuntimeError("v014 lighting/transfer balance already applied")

sun = actors.get("B_stylized | sun 0.30")
sky = actors.get("B_stylized | sky 0.20")
if not isinstance(sun, unreal.DirectionalLight) or not isinstance(sky, unreal.SkyLight):
    raise RuntimeError("Expected common sun and skylight")
sun.light_component.set_editor_property("intensity", 1.0)
sky.light_component.set_editor_property("intensity", 2.4)
sun.tags = list(sun.tags) + [TAG]
sky.tags = list(sky.tags) + [TAG]

changed_lights = []
for label, actor in actors.items():
    if not isinstance(actor, unreal.RectLight):
        continue
    if label.startswith("2126 v002 | functional process light"):
        actor.light_component.set_editor_property("intensity", 16000.0)
        actor.tags = list(actor.tags) + [TAG]
        changed_lights.append(label)
    elif label.endswith("task light"):
        actor.light_component.set_editor_property("intensity", 9000.0)
        actor.tags = list(actor.tags) + [TAG]
        changed_lights.append(label)
if len(changed_lights) != 10:
    raise RuntimeError("Expected ten existing functional lights, found %d" % len(changed_lights))

yellow = unreal.load_asset(ROOT + "/M_LB_PS2126v002_SafetyYellow")
if not isinstance(yellow, unreal.Material):
    raise RuntimeError("Candidate Safety Yellow material missing")
rails = []
for label in ("2126 v002 | transfer rail | operator", "2126 v002 | transfer rail | service"):
    actor = actors.get(label)
    if not isinstance(actor, unreal.StaticMeshActor):
        raise RuntimeError("Missing transfer rail " + label)
    component = actor.static_mesh_component
    component.set_material(0, yellow)
    component.set_cast_shadow(False)
    component.set_visibility(True, True)
    component.set_render_in_main_pass(True)
    actor.tags = list(actor.tags) + [TAG, unreal.Name("LB.Automation.TransferReadable")]
    rails.append(label)

if not unreal.EditorLevelLibrary.save_current_level():
    raise RuntimeError("Could not save v014 lighting balance")
after = digest(PROTECTED)
if before != after:
    raise RuntimeError("Protected v438 changed")
REPORT.parent.mkdir(parents=True, exist_ok=True)
REPORT.write_text(json.dumps({
    "status": "PASS__EXISTING_LIGHTS_BALANCED__TRANSFER_READABILITY_CORRECTED",
    "candidate_map": MAP,
    "new_light_actors": 0,
    "functional_lights_reduced": changed_lights,
    "sun_intensity": 1.0,
    "sky_intensity": 2.4,
    "transfer_rails": rails,
    "roof_created": False,
    "protected_v438_sha256_before": before,
    "protected_v438_sha256_after": after,
}, indent=2), encoding="utf-8")
unreal.log("PRESSSHOP_2126_V002_LIGHTING_TRANSFER_V014_PASS")
