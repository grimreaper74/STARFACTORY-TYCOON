"""Read-only inventory for the latest retained Press Shop visual baseline."""

import json
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

import unreal


MAP = "/Game/LineBoss/Maps/LB_PressShop_PlayableManagementCandidate_v228"
OUT = Path(unreal.Paths.project_saved_dir()) / "Audits/PressShopIntegration/press_shop_visual_completion_audit_v228.json"
levels = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
actors_api = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
if not levels.load_level(MAP):
    raise RuntimeError(MAP)

actors = actors_api.get_all_level_actors()
class_counts = Counter(actor.get_class().get_name() for actor in actors)
tag_counts = Counter(str(tag) for actor in actors for tag in actor.tags)

def actor_record(actor):
    location = actor.get_actor_location()
    rotation = actor.get_actor_rotation()
    return {
        "label": actor.get_actor_label(),
        "class": actor.get_class().get_name(),
        "location_cm": [round(location.x, 1), round(location.y, 1), round(location.z, 1)],
        "rotation_deg": [round(rotation.pitch, 1), round(rotation.yaw, 1), round(rotation.roll, 1)],
        "tags": [str(tag) for tag in actor.tags],
    }

lights = [actor_record(actor) for actor in actors if actor.get_class().get_name() in {
    "DirectionalLight", "SkyLight", "PointLight", "RectLight", "SpotLight", "PostProcessVolume"
}]
cameras = [actor_record(actor) for actor in actors if actor.get_class().get_name() == "CameraActor"
           and ("LB_WHOLE" in actor.get_actor_label() or "LB_ENV" in actor.get_actor_label())]
authorities = [actor_record(actor) for actor in actors if actor.get_class().get_name() in {
    "LBPR004Station", "LBPR005Station", "LBPR006Station", "LBPR007Station", "LBPR008Station",
    "LBPR009Station", "LBPR010Station", "LBPressTrainAStation", "LBCoilAGVController",
    "LBBridgeCraneController", "LBSupportCraneController", "LBSupportRobot"
}]

payload = {
    "$schema": "cairnwell/audit/press-shop-visual-completion-v228/v1",
    "generated_utc": datetime.now(timezone.utc).isoformat(),
    "map": MAP,
    "read_only": True,
    "actor_count": len(actors),
    "class_counts": dict(sorted(class_counts.items())),
    "important_tag_counts": {key: value for key, value in sorted(tag_counts.items()) if
                             key.startswith("LB.Station") or key.startswith("LB.PressTrain.Installed")
                             or key.startswith("LB.Support") or key.startswith("LB.Asset")},
    "lights": lights,
    "evidence_cameras": cameras,
    "native_authorities": authorities,
    "status": "READ_ONLY_BASELINE__NO_PROMOTION_DECISION",
}
OUT.parent.mkdir(parents=True, exist_ok=True)
OUT.write_text(json.dumps(payload, indent=2), encoding="utf-8")
unreal.log(f"LB_VISUAL_AUDIT_V228::{OUT}")
unreal.SystemLibrary.quit_editor()
