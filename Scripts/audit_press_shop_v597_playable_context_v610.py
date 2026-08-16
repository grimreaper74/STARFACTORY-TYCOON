"""Read-only playable-context audit of the retained inbound v597 map."""

from pathlib import Path
import hashlib
import json

import unreal


MAP = "/Game/LineBoss/Developer/Validation/LB_PressShop_InboundReleaseCandidate_v597"
ROOT = Path(unreal.Paths.project_dir())
MAP_FILE = ROOT / "Content/LineBoss/Developer/Validation/LB_PressShop_InboundReleaseCandidate_v597.umap"
PROTECTED_FILE = ROOT / "Content/LineBoss/Maps/LB_PressShop_BuilderAuthorityCandidate_v438.umap"
OUT = ROOT / "Saved/Audits/PressShopIntegration/press_shop_v597_playable_context_v610.json"
EXPECTED_V438 = "5029C9D827D9A1D72C12F27EE757C9BC1E47FEBD5006CE6D7BA319AAD2E7FEC8"


def transform_row(actor):
    location = actor.get_actor_location()
    rotation = actor.get_actor_rotation()
    scale = actor.get_actor_scale3d()
    return {
        "class": actor.get_class().get_name(),
        "label": actor.get_actor_label(),
        "location_cm": [location.x, location.y, location.z],
        "rotation_deg": [rotation.pitch, rotation.yaw, rotation.roll],
        "scale": [scale.x, scale.y, scale.z],
        "tags": sorted(str(tag) for tag in actor.tags),
    }


levels = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
actors_api = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
if not levels.load_level(MAP):
    raise RuntimeError(f"Could not load {MAP}")

world = unreal.EditorLevelLibrary.get_editor_world()
settings = world.get_world_settings()
game_mode = settings.get_editor_property("default_game_mode")
game_mode_path = game_mode.get_path_name() if game_mode else None

interesting = []
class_counts = {}
for actor in actors_api.get_all_level_actors():
    class_name = actor.get_class().get_name()
    label_lower = actor.get_actor_label().lower()
    class_counts[class_name] = class_counts.get(class_name, 0) + 1
    if (
        class_name in {
            "PlayerStart",
            "LBControlRoomOperationsConsole",
            "LBPressShopBuildAuthority",
            "LBPressTrainAStation",
            "LBPressShopCampaignController",
            "LBPressShopMaterialFlowController",
            "LBInboundDeliveryController",
            "LBCoilAGVController",
        }
        or "controlroom" in label_lower
        or "control_room" in label_lower
        or "operationsconsole" in label_lower
        or "playerstart" in label_lower
    ):
        interesting.append(transform_row(actor))

v438_hash = hashlib.sha256(PROTECTED_FILE.read_bytes()).hexdigest().upper()
v597_hash = hashlib.sha256(MAP_FILE.read_bytes()).hexdigest().upper()
payload = {
    "status": "PASS" if v438_hash == EXPECTED_V438 else "FAIL",
    "read_only": True,
    "map": MAP,
    "default_game_mode": game_mode_path,
    "interesting_actors": sorted(interesting, key=lambda row: (row["class"], row["label"])),
    "key_class_counts": {
        key: class_counts.get(key, 0)
        for key in sorted({row["class"] for row in interesting})
    },
    "protected_v438_sha256": v438_hash,
    "v597_sha256": v597_hash,
    "promotion_authorized": False,
}
OUT.parent.mkdir(parents=True, exist_ok=True)
OUT.write_text(json.dumps(payload, indent=2), encoding="utf-8")
unreal.log(f"LB_V597_PLAYABLE_CONTEXT_AUDIT::{json.dumps(payload)}")
if payload["status"] != "PASS":
    raise RuntimeError("Protected v438 hash changed")

