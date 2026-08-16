"""Read-only inventory of native gameplay authorities in retained v213."""

import json
from pathlib import Path

import unreal


MAP = "/Game/LineBoss/Maps/LB_PressShop_CumulativeReleaseCandidate_v213"
ROOT = Path(unreal.Paths.project_dir())
OUT = ROOT / "Saved/Audits/PressShopIntegration/press_shop_runtime_authority_donor_v213.json"
levels = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
actors_api = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)

if not levels.load_level(MAP):
    raise RuntimeError(MAP)

rows = []
for actor in actors_api.get_all_level_actors():
    class_name = actor.get_class().get_name()
    if not (class_name.startswith("LBPR") or class_name in {
            "LBPressShopMaterialFlowController", "LBControlRoomOperationsConsole",
            "PlayerStart", "LBPressShopNavigationBootstrap"}):
        continue
    location = actor.get_actor_location()
    rotation = actor.get_actor_rotation()
    rows.append({
        "class": class_name,
        "label": actor.get_actor_label(),
        "location_cm": [location.x, location.y, location.z],
        "rotation_deg": [rotation.pitch, rotation.yaw, rotation.roll],
        "scale": [actor.get_actor_scale3d().x, actor.get_actor_scale3d().y, actor.get_actor_scale3d().z],
        "tags": sorted(str(tag) for tag in actor.tags),
    })

payload = {"map": MAP, "read_only": True, "authorities": rows}
OUT.parent.mkdir(parents=True, exist_ok=True)
OUT.write_text(json.dumps(payload, indent=2), encoding="utf-8")
unreal.log(f"LB_V213_RUNTIME_AUTHORITY_AUDIT::{json.dumps(payload)}")

