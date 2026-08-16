"""Correct only the rejected v270 review camera; dock geometry remains untouched."""
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
import unreal

MAP = "/Game/LineBoss/Maps/LB_PressShop_PlayableManagementCandidate_v270"
CAMERA = "LB_DOCK_V270_CAM_MR01_PAIR_COMPARISON"
levels = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
actors = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
if not levels.load_level(MAP):
    raise RuntimeError(f"failed to load {MAP}")
camera = next((a for a in actors.get_all_level_actors() if isinstance(a, unreal.CameraActor) and a.get_actor_label() == CAMERA), None)
if camera is None:
    raise RuntimeError(f"missing camera {CAMERA}")
camera.set_actor_location(unreal.Vector(-5795, 3000, 430), False, False)
camera.set_actor_rotation(unreal.MathLibrary.find_look_at_rotation(camera.get_actor_location(), unreal.Vector(-5795, 5160, 90)), False)
camera.camera_component.set_editor_properties({"field_of_view": 48.0, "aspect_ratio": 16.0/9.0, "constrain_aspect_ratio": True})
if not levels.save_current_level():
    raise RuntimeError("failed to save camera correction")
project = Path(unreal.Paths.project_dir()).resolve()
map_file = project / "Content/LineBoss/Maps/LB_PressShop_PlayableManagementCandidate_v270.umap"
digest = hashlib.sha256(map_file.read_bytes()).hexdigest().upper()
audit = Path(unreal.Paths.project_saved_dir()).resolve() / "Audits/SupportRobots/press_shop_mr01_modular_dock_comparison_camera_v270.json"
audit.parent.mkdir(parents=True, exist_ok=True)
audit.write_text(json.dumps({
    "$schema": "cairnwell/audit/press-shop-mr01-modular-dock-comparison-camera-v270/v1",
    "generated_utc": datetime.now(timezone.utc).isoformat(),
    "status": "PASS__REJECTED_CLOSE_CAMERA_REPLACED__VISUAL_GATE_OPEN__NOT_PROMOTED",
    "map": MAP,
    "map_sha256_after": digest,
    "camera": CAMERA,
    "location_cm": [-5795, 3000, 430],
    "target_cm": [-5795, 5160, 90],
    "dock_geometry_changed": False,
    "promotion_authorized": False
}, indent=2), encoding="utf-8")
unreal.log("LINE_BOSS_PRESS_SHOP_MR01_DOCK_COMPARISON_CAMERA_V270_PASS")
