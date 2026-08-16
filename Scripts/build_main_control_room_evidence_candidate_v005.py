"""Derive v005 from v004 and correct the elevated fixed-camera envelope."""

import json
from datetime import datetime, timezone
from pathlib import Path

import unreal


ROOT = Path(unreal.Paths.project_dir())
BASE = "/Game/LineBoss/Maps/LB_MainControlRoom_SeatedCompositionCandidate_v004"
MAP = "/Game/LineBoss/Maps/LB_MainControlRoom_EvidenceCandidate_v005"
OUT = ROOT / "Saved/Audits/ControlRoom/main_control_room_evidence_build_v005.json"

library = unreal.EditorAssetLibrary
levels = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
actors_api = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
if library.does_asset_exist(MAP):
    raise RuntimeError(f"refusing to overwrite {MAP}")
if not levels.new_level_from_template(MAP, BASE):
    raise RuntimeError(f"could not derive {MAP}")

actors = {actor.get_actor_label(): actor for actor in actors_api.get_all_level_actors()}
failures = []
camera = actors.get("LB_MCR_V004_CAM_Elevated")
if camera is None:
    failures.append("missing v004 elevated camera")
else:
    # Architecture half-width is 390 cm on the short axis; both camera axes
    # are now inside the room and below its 360 cm clear ceiling.
    location = unreal.Vector(500, 300, 290)
    target = unreal.Vector(0, -55, 120)
    camera.set_actor_label("LB_MCR_V005_CAM_Elevated")
    camera.set_actor_location(location, False, False)
    camera.set_actor_rotation(unreal.MathLibrary.find_look_at_rotation(location, target), False)
    camera.camera_component.set_editor_properties({"field_of_view": 76.0, "aspect_ratio": 16.0 / 9.0, "constrain_aspect_ratio": True})
    camera.tags = [unreal.Name("LB.ControlRoom.v005"), unreal.Name("LB.ControlRoom.Camera.Elevated"), unreal.Name("LB.Asset.CandidateNotPromoted")]

for name in ("SeatedPlayer", "Front", "SystemsWall"):
    actor = actors.get(f"LB_MCR_V004_CAM_{name}")
    if actor is None:
        failures.append(f"missing v004 camera: {name}")
        continue
    actor.set_actor_label(f"LB_MCR_V005_CAM_{name}")
    actor.tags = [unreal.Name("LB.ControlRoom.v005"), unreal.Name(f"LB.ControlRoom.Camera.{name}"), unreal.Name("LB.Asset.CandidateNotPromoted")]

for actor in actors_api.get_all_level_actors():
    if any(str(tag) == "LB.ControlRoom.v004" for tag in actor.tags):
        actor.tags = [unreal.Name("LB.ControlRoom.v005" if str(tag) == "LB.ControlRoom.v004" else str(tag)) for tag in actor.tags]

levels.save_current_level()
payload = {
    "$schema": "cairnwell/audit/main-control-room-evidence-build-v005/v1",
    "generated_utc": datetime.now(timezone.utc).isoformat(),
    "status": "PASS__ALL_FIXED_CAMERAS_INSIDE_AUTHORED_ROOM_ENVELOPE__VISUAL_GATE_REQUIRED__NOT_PROMOTED" if not failures else "FAIL__CONTROL_ROOM_V005_BUILD__NOT_PROMOTED",
    "source_map": BASE,
    "map": MAP,
    "elevated_camera_location_cm": [500, 300, 290],
    "room_short_axis_half_extent_cm": 390,
    "room_clear_height_cm": 360,
    "promotion_authorized": False,
    "gameplay_wired": False,
    "failures": failures,
}
OUT.parent.mkdir(parents=True, exist_ok=True)
OUT.write_text(json.dumps(payload, indent=2), encoding="utf-8")
print(json.dumps({"status": payload["status"], "failures": failures, "audit": str(OUT)}, indent=2))

