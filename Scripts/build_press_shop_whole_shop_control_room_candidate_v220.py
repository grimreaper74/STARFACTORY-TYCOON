"""Add a walk-up Press Shop operations console to v219 without mutating it.

The control-room and press-train transforms remain EST-P reference-only.  This
candidate is for owner interaction and exact-map runtime validation, not layout
promotion.
"""

import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path

import unreal


ROOT = Path(unreal.Paths.project_dir())
BASE = "/Game/LineBoss/Maps/LB_PressShop_WholeShopAutomationPreviewCandidate_v219"
MAP = "/Game/LineBoss/Maps/LB_PressShop_WholeShopControlRoomCandidate_v221"
OUT = ROOT / "Saved/Audits/PressShopIntegration/press_shop_whole_shop_control_room_build_v221.json"

library = unreal.EditorAssetLibrary
levels = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
actors_api = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)


def sha256(path):
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest().upper()


if library.does_asset_exist(MAP):
    raise RuntimeError(f"refusing to overwrite {MAP}")

base_file = ROOT / "Content/LineBoss/Maps/LB_PressShop_WholeShopAutomationPreviewCandidate_v219.umap"
base_hash_before = sha256(base_file)
if not levels.new_level_from_template(MAP, BASE):
    raise RuntimeError(f"could not derive {MAP} from {BASE}")

failures = []
world = unreal.EditorLevelLibrary.get_editor_world()
game_mode_class = unreal.load_class(None, "/Script/LineBossCarFactory.LBControlRoomGameMode")
console_class = unreal.load_class(None, "/Script/LineBossCarFactory.LBControlRoomOperationsConsole")
if game_mode_class is None or console_class is None:
    raise RuntimeError("compiled control-room classes unavailable")
world.get_world_settings().set_editor_property("default_game_mode", game_mode_class)

# CTRL EST-P anchor is (2200, 4500, 0) cm.  The console front faces south into
# the permitted operator area; its centre height follows the validated v042
# native console presentation.
console_location = unreal.Vector(2200.0, 4500.0, 150.0)
console_rotation = unreal.Rotator()
console_rotation.yaw = -90.0
console = actors_api.spawn_actor_from_class(console_class, console_location, console_rotation)
if console is None:
    raise RuntimeError("could not spawn operations console")
console.set_actor_label("LB_WHOLE_V221_PRESS_SHOP_OPERATIONS_CONSOLE")
console.tags = [
    unreal.Name("LB.ControlRoom.PressShopOperations"),
    unreal.Name("LB.ControlRoom.WalkUp"),
    unreal.Name("LB.LayoutAuthority.EST-P.ReferenceOnly"),
    unreal.Name("LB.Integration.WholeShopControlRoom.v221"),
    unreal.Name("LB.Asset.Candidate.v221"),
    unreal.Name("LB.Asset.CandidateNotPromoted"),
]

screen_material = library.load_asset(
    "/Game/LineBoss/Candidates/ControlRoom/MainControlRoom_v002/Materials/M_CA_ScreenDark_R_v002")
screen_back = console.get_editor_property("screen_back")
if screen_material is None or screen_back is None:
    failures.append("screen material or native screen-back component unavailable")
else:
    screen_back.set_material(0, screen_material)

player_location = unreal.Vector(2200.0, 4125.0, 92.0)
player_rotation = unreal.Rotator()
player_rotation.yaw = 90.0
player = actors_api.spawn_actor_from_class(unreal.PlayerStart, player_location, player_rotation)
if player is None:
    raise RuntimeError("could not spawn control-room PlayerStart")
player.set_actor_label("LB_WHOLE_V221_CONTROL_ROOM_PLAYER_START")
player.tags = [
    unreal.Name("LB.ControlRoom.PlayerStart"),
    unreal.Name("LB.LayoutAuthority.EST-P.ReferenceOnly"),
    unreal.Name("LB.Integration.WholeShopControlRoom.v221"),
    unreal.Name("LB.Asset.CandidateNotPromoted"),
]

camera_location = unreal.Vector(2200.0, 4075.0, 175.0)
camera = actors_api.spawn_actor_from_class(unreal.CameraActor, camera_location, unreal.Rotator())
if camera is None:
    failures.append("could not spawn control-room evidence camera")
else:
    camera.set_actor_label("LB_WHOLE_V221_CAM_ControlRoomWalkUp")
    camera.set_actor_rotation(
        unreal.MathLibrary.find_look_at_rotation(camera_location, console_location), False)
    camera.camera_component.set_editor_property("field_of_view", 64.0)
    camera.tags = [
        unreal.Name("LB.ControlRoom.Camera.WalkUp"),
        unreal.Name("LB.Integration.WholeShopControlRoom.v221"),
        unreal.Name("LB.Asset.CandidateNotPromoted"),
    ]

actors = actors_api.get_all_level_actors()
consoles = [a for a in actors if a.get_class().get_name() == "LBControlRoomOperationsConsole"]
starts = [a for a in actors if a.get_class().get_name() == "PlayerStart"]
trains = [a for a in actors if a.get_class().get_name() == "LBPressTrainAStation"]
if len(consoles) != 1:
    failures.append(f"expected one operations console, found {len(consoles)}")
if len(starts) != 1:
    failures.append(f"expected one PlayerStart, found {len(starts)}")
if len(trains) != 4:
    failures.append(f"expected four train authorities, found {len(trains)}")

levels.save_current_level()
base_hash_after = sha256(base_file)
if base_hash_after != base_hash_before:
    failures.append("protected v219 parent hash changed")

map_file = ROOT / "Content/LineBoss/Maps/LB_PressShop_WholeShopControlRoomCandidate_v221.umap"
payload = {
    "$schema": "cairnwell/audit/press-shop-whole-shop-control-room-build-v221/v1",
    "generated_utc": datetime.now(timezone.utc).isoformat(),
    "status": "PASS__WALK_UP_CONSOLE_INSTALLED__EXACT_MAP_RUNTIME_AND_VISUAL_GATES_REQUIRED__NOT_PROMOTED" if not failures else "FAIL__NOT_PROMOTED",
    "base": BASE,
    "map": MAP,
    "parent_hash_before": base_hash_before,
    "parent_hash_after": base_hash_after,
    "map_hash": sha256(map_file) if map_file.exists() else None,
    "control_room_console_count": len(consoles),
    "player_start_count": len(starts),
    "press_train_authority_count": len(trains),
    "console_location_cm": [console_location.x, console_location.y, console_location.z],
    "console_rotation_deg": [console_rotation.pitch, console_rotation.yaw, console_rotation.roll],
    "player_location_cm": [player_location.x, player_location.y, player_location.z],
    "game_mode": "/Script/LineBossCarFactory.LBControlRoomGameMode",
    "layout_authority": "EST-P_REFERENCE_ONLY",
    "promotion_authorized": False,
    "failures": failures,
}
OUT.parent.mkdir(parents=True, exist_ok=True)
OUT.write_text(json.dumps(payload, indent=2), encoding="utf-8")
if failures:
    raise RuntimeError("; ".join(failures))
unreal.log(f"LB_V221_BUILD::{json.dumps(payload)}")
