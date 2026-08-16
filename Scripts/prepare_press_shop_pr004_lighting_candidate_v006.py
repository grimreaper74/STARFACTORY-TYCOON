"""Create a preserved Press Shop derivative with credible dormant PR-004 lighting.

The accepted PR-004 equipment coordinates are not touched.  This pass only
normalises local full-map lights whose saturated blue cast obscured material
and safety-colour judgement in the v004/v005 evidence.
"""

import json
import math
from pathlib import Path

import unreal


BASE = "/Game/LineBoss/Maps/LB_PressShop_SupportRobotsCandidate_v005"
DEST = "/Game/LineBoss/Maps/LB_PressShop_PR004LightingCandidate_v006"
AUDIT = Path(unreal.Paths.project_saved_dir()) / "Audits/press_shop_pr004_lighting_v006.json"
PR004_CENTRE = unreal.Vector(-5050.0, -2000.0, 0.0)
MAX_DISTANCE_CM = 1800.0
# Unreal Python's Color constructor is exposed in BGRA argument order.
# These values therefore produce the intended warm RGB (255, 205, 155).
WARM_SERVICE = unreal.Color(155, 205, 255, 255)

levels = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
actor_system = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)

levels.load_level("/Game/LineBoss/Maps/LB_PressShop_Foundation")
if unreal.EditorAssetLibrary.does_asset_exist(DEST):
    raise RuntimeError(f"Refusing to overwrite preserved candidate {DEST}")
if not unreal.EditorAssetLibrary.duplicate_asset(BASE, DEST):
    raise RuntimeError(f"Could not duplicate {BASE} to {DEST}")
if not levels.load_level(DEST):
    raise RuntimeError(f"Could not load {DEST}")

changes = []
for actor in actor_system.get_all_level_actors():
    component = None
    intensity_cap = None
    if isinstance(actor, unreal.PointLight):
        component = actor.get_editor_property("point_light_component")
        intensity_cap = 240.0
    elif isinstance(actor, unreal.SpotLight):
        component = actor.get_editor_property("spot_light_component")
        intensity_cap = 450.0
    elif isinstance(actor, unreal.RectLight):
        component = actor.get_editor_property("rect_light_component")
        intensity_cap = 350.0
    if component is None:
        continue
    location = actor.get_actor_location()
    distance = math.hypot(location.x - PR004_CENTRE.x, location.y - PR004_CENTRE.y)
    if distance > MAX_DISTANCE_CM:
        continue
    before_colour = component.get_editor_property("light_color")
    before_rgba = [before_colour.r, before_colour.g, before_colour.b, before_colour.a]
    before_intensity = float(component.get_editor_property("intensity"))
    after_intensity = min(before_intensity, intensity_cap)
    component.set_editor_property("light_color", WARM_SERVICE)
    component.set_editor_property("intensity", after_intensity)
    changes.append({
        "actor": actor.get_actor_label(),
        "distance_from_pr004_cm": round(distance, 2),
        "before_colour_rgba": before_rgba,
        "after_colour_rgba": [WARM_SERVICE.r, WARM_SERVICE.g, WARM_SERVICE.b, WARM_SERVICE.a],
        "before_intensity": before_intensity,
        "after_intensity": after_intensity,
    })

if not changes:
    raise RuntimeError("No local PR-004 lights found; refusing an unevidenced derivative")
if not levels.save_current_level():
    raise RuntimeError(f"Could not save {DEST}")

AUDIT.parent.mkdir(parents=True, exist_ok=True)
AUDIT.write_text(json.dumps({
    "$schema": "line-boss/audit/press-shop-pr004-lighting/v1",
    "status": "CANDIDATE_NOT_PROMOTED__VISUAL_REVIEW_REQUIRED",
    "base_map": BASE,
    "map": DEST,
    "pr004_centre_cm": [PR004_CENTRE.x, PR004_CENTRE.y, PR004_CENTRE.z],
    "equipment_coordinates_modified": False,
    "changed_light_count": len(changes),
    "changes": changes,
    "promotion_supported": False,
}, indent=2), encoding="utf-8")
unreal.log(f"LINE_BOSS_PRESS_PR004_LIGHTING_V006_PASS lights={len(changes)} audit={AUDIT}")
unreal.SystemLibrary.quit_editor()
