"""Correct the v006 local light colour after verifying Unreal's BGRA binding."""

import json
import math
from pathlib import Path

import unreal


MAP = "/Game/LineBoss/Maps/LB_PressShop_PR004LightingCandidate_v006"
AUDIT = Path(unreal.Paths.project_saved_dir()) / "Audits/press_shop_pr004_lighting_v006.json"
CENTRE = unreal.Vector(-5050.0, -2000.0, 0.0)
WARM_SERVICE = unreal.Color(155, 205, 255, 255)  # BGRA -> RGB 255,205,155

levels = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
actors = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
if not levels.load_level(MAP):
    raise RuntimeError(f"Could not load {MAP}")

changes = []
for actor in actors.get_all_level_actors():
    component = None
    cap = None
    if isinstance(actor, unreal.PointLight):
        component, cap = actor.get_editor_property("point_light_component"), 240.0
    elif isinstance(actor, unreal.SpotLight):
        component, cap = actor.get_editor_property("spot_light_component"), 450.0
    elif isinstance(actor, unreal.RectLight):
        component, cap = actor.get_editor_property("rect_light_component"), 350.0
    if component is None:
        continue
    p = actor.get_actor_location()
    distance = math.hypot(p.x - CENTRE.x, p.y - CENTRE.y)
    if distance > 1800.0:
        continue
    before = component.get_editor_property("light_color")
    before_rgba = [before.r, before.g, before.b, before.a]
    old_intensity = float(component.get_editor_property("intensity"))
    component.set_editor_property("light_color", WARM_SERVICE)
    component.set_editor_property("intensity", min(old_intensity, cap))
    verified = component.get_editor_property("light_color")
    changes.append({
        "actor": actor.get_actor_label(),
        "distance_from_pr004_cm": round(distance, 2),
        "before_unreal_rgba": before_rgba,
        "after_unreal_rgba": [verified.r, verified.g, verified.b, verified.a],
        "intended_display_rgb": [255, 205, 155],
        "intensity": min(old_intensity, cap),
    })

if len(changes) != 6:
    raise RuntimeError(f"Expected the six previously audited local lights, found {len(changes)}")
if not levels.save_current_level():
    raise RuntimeError(f"Could not save {MAP}")
AUDIT.write_text(json.dumps({
    "$schema": "line-boss/audit/press-shop-pr004-lighting/v1",
    "status": "CANDIDATE_NOT_PROMOTED__VISUAL_REVIEW_REQUIRED",
    "map": MAP,
    "equipment_coordinates_modified": False,
    "binding_note": "Unreal Python Color constructor verified as BGRA; intended display colour is warm RGB 255,205,155.",
    "changed_light_count": len(changes),
    "changes": changes,
    "promotion_supported": False,
}, indent=2), encoding="utf-8")
unreal.log(f"LINE_BOSS_PRESS_PR004_LIGHTING_V006_CORRECTION_PASS lights={len(changes)}")
unreal.SystemLibrary.quit_editor()
