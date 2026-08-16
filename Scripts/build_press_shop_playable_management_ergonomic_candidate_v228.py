"""Create a v228 operator-start ergonomics child from retained v227."""

import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path

import unreal


ROOT = Path(unreal.Paths.project_dir())
BASE = "/Game/LineBoss/Maps/LB_PressShop_PlayableManagementCandidate_v227"
MAP = "/Game/LineBoss/Maps/LB_PressShop_PlayableManagementCandidate_v228"
OUT = ROOT / "Saved/Audits/ControlRoom/control_room_walk_up_ergonomic_build_v228.json"
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
parent_file = ROOT / "Content/LineBoss/Maps/LB_PressShop_PlayableManagementCandidate_v227.umap"
parent_hash_before = sha256(parent_file)
if not levels.new_level_from_template(MAP, BASE):
    raise RuntimeError(f"could not derive {MAP} from {BASE}")

actors = actors_api.get_all_level_actors()
starts = [actor for actor in actors if isinstance(actor, unreal.PlayerStart)]
cameras = [actor for actor in actors if actor.get_actor_label() == "LB_WHOLE_V224_CAM_ControlRoomWalkUp"]
failures = []
changes = []
if len(starts) != 1:
    failures.append(f"expected one PlayerStart, found {len(starts)}")
else:
    start = starts[0]
    before = start.get_actor_location()
    after = unreal.Vector(before.x, before.y + 115.0, before.z)
    start.set_actor_location(after, False, False)
    changes.append({"actor": start.get_actor_label(), "before_cm": str(before), "after_cm": str(after)})
if len(cameras) != 1:
    failures.append(f"expected one control-room walk-up camera, found {len(cameras)}")
else:
    camera = cameras[0]
    before = camera.get_actor_location()
    after = unreal.Vector(before.x, before.y + 115.0, before.z)
    camera.set_actor_location(after, False, False)
    changes.append({"actor": camera.get_actor_label(), "before_cm": str(before), "after_cm": str(after)})

levels.save_current_level()
parent_hash_after = sha256(parent_file)
if parent_hash_after != parent_hash_before:
    failures.append("protected v227 parent changed")
map_file = ROOT / "Content/LineBoss/Maps/LB_PressShop_PlayableManagementCandidate_v228.umap"
payload = {
    "$schema": "cairnwell/audit/control-room-walk-up-ergonomic-build-v228/v1",
    "generated_utc": datetime.now(timezone.utc).isoformat(),
    "status": "PASS__PLAYERSTART_AND_EVIDENCE_CAMERA_MOVED_115CM_CLOSER__FRESH_RUNTIME_AND_VISUAL_GATES_REQUIRED__NOT_PROMOTED" if not failures else "FAIL__NOT_PROMOTED",
    "base": BASE,
    "map": MAP,
    "parent_hash_before": parent_hash_before,
    "parent_hash_after": parent_hash_after,
    "map_hash": sha256(map_file) if map_file.exists() else None,
    "changes": changes,
    "machine_or_authority_changes": 0,
    "promotion_authorized": False,
    "failures": failures,
}
OUT.parent.mkdir(parents=True, exist_ok=True)
OUT.write_text(json.dumps(payload, indent=2), encoding="utf-8")
if failures:
    raise RuntimeError("; ".join(failures))
unreal.log(f"LB_V228_ERGONOMIC_BUILD::{json.dumps(payload)}")
unreal.SystemLibrary.quit_editor()
