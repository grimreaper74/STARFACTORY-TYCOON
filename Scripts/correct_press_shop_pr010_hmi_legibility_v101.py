"""Correct v101 HMI text facing and refine the exact fixed evidence camera."""

import json
from datetime import datetime, timezone
from pathlib import Path

import unreal


ROOT = Path(unreal.Paths.project_dir())
MAP = "/Game/LineBoss/Maps/LB_PressShop_PR010ReleaseArtCandidate_v101"
OUT = ROOT / "Saved/Audits/PR010_ReleaseArt_v101/hmi_legibility_correction_v101.json"
levels = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
actors_api = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
if not levels.load_level(MAP): raise RuntimeError(MAP)
actors = list(actors_api.get_all_level_actors())
texts = [actor for actor in actors if actor.get_actor_label().startswith("LB_PR010_V101_TEXT_")]
text_styles = {
    "Corporation": (5.0, unreal.Color(245, 190, 45, 255)),
    "Site": (3.8, unreal.Color(235, 240, 235, 255)),
    "Station": (4.5, unreal.Color(8, 35, 32, 255)),
    "State": (3.8, unreal.Color(80, 230, 180, 255)),
    "Capacity": (3.1, unreal.Color(235, 240, 235, 255)),
}
for actor in texts:
    actor.set_actor_rotation(unreal.Rotator(yaw=180.0), False)
    key = actor.get_actor_label().rsplit("_", 1)[-1]
    if key in text_styles:
        size, colour = text_styles[key]
        actor.text_render.set_world_size(size)
        actor.text_render.set_text_render_color(colour)
camera = next((actor for actor in actors if actor.get_actor_label() == "LB_PR010_V098_CAM_ServiceHMI"), None)
if camera:
    camera.set_actor_location(unreal.Vector(680, -2645, 180), False, False)
    camera.set_actor_rotation(unreal.MathLibrary.find_look_at_rotation(camera.get_actor_location(), unreal.Vector(1025, -2645, 108)), False)
    camera.camera_component.set_editor_properties({"field_of_view": 43.0, "aspect_ratio": 16.0/9.0, "constrain_aspect_ratio": True})
failures = []
if len(texts) != 5: failures.append(f"expected five HMI texts, found {len(texts)}")
if camera is None: failures.append("missing ServiceHMI camera")
if not levels.save_current_level(): failures.append("could not save v101 HMI correction")
report = {"$schema": "cairnwell/audit/pr010-hmi-legibility-v101/v1", "generated_utc": datetime.now(timezone.utc).isoformat(),
    "status": "PASS__PR010_V101_HMI_TEXT_CAMERA_FACING_AND_EVIDENCE_CAMERA_REFRAMED__FRESH_IMAGE_REQUIRED__NOT_PROMOTED" if not failures else "FAIL__PR010_V101_HMI_CORRECTION__NOT_PROMOTED",
    "map": MAP, "text_actor_count": len(texts), "text_yaw_degrees": 180.0,
    "camera_location_cm": [680, -2645, 180], "camera_target_cm": [1025, -2645, 108],
    "failures": failures, "promotion_authorized": False}
OUT.parent.mkdir(parents=True, exist_ok=True); OUT.write_text(json.dumps(report, indent=2), encoding="utf-8")
print(json.dumps(report, indent=2))
if failures: raise RuntimeError("; ".join(failures))
