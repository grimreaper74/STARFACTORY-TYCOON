"""Create a camera-only v143 successor after v142's cropped visual proof failed."""
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path

import unreal

BASE = "/Game/LineBoss/Maps/LB_PressShop_PR003PR004PoweredCHookVisualProofCandidate_v142"
MAP = "/Game/LineBoss/Maps/LB_PressShop_PR003PR004PoweredCHookVisualProofCandidate_v143"
ROOT = Path(unreal.Paths.project_dir())
PARENT_FILE = ROOT / "Content/LineBoss/Maps/LB_PressShop_PR003PR004PoweredCHookVisualProofCandidate_v142.umap"
OUT = ROOT / "Saved/Audits/press_shop_pr004_powered_chook_visual_proof_build_v143.json"
levels = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
actors = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)

def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

def camera(label, location, target, fov):
    actor = actors.spawn_actor_from_class(unreal.CameraActor, unreal.Vector(*location), unreal.Rotator())
    actor.set_actor_label("LB_PR004_V143_CAM_" + label)
    actor.set_actor_rotation(unreal.MathLibrary.find_look_at_rotation(actor.get_actor_location(), unreal.Vector(*target)), False)
    actor.camera_component.set_editor_properties({"field_of_view": fov, "aspect_ratio": 16/9, "constrain_aspect_ratio": True, "post_process_blend_weight": 1.0})
    pp = actor.camera_component.get_editor_property("post_process_settings")
    pp.set_editor_properties({"override_auto_exposure_bias": True, "auto_exposure_bias": 1.25})
    actor.camera_component.set_editor_property("post_process_settings", pp)
    return actor

before = digest(PARENT_FILE)
if unreal.EditorAssetLibrary.does_asset_exist(MAP):
    raise RuntimeError(f"Refusing to overwrite existing map {MAP}")
if not levels.new_level_from_template(MAP, BASE):
    raise RuntimeError(f"Could not create {MAP} from {BASE}")

cameras = [
    camera("PoweredCHookFullSide", (-6800, -430, 1160), (-5050, -2030, 760), 43.0),
    camera("PoweredCHookTrueBoreAxis", (-5050, 250, 760), (-5050, -2050, 750), 44.0),
    camera("PoweredCHookLoadArmOblique", (-6550, -650, 600), (-5050, -2020, 680), 45.0),
]
if not levels.save_current_level():
    raise RuntimeError(f"Could not save {MAP}")

after = digest(PARENT_FILE)
payload = {
    "$schema": "cairnwell/audit/press-shop-pr004-powered-chook-visual-proof-build-v143/v1",
    "generated_utc": datetime.now(timezone.utc).isoformat(),
    "status": "PASS__CAMERA_ONLY_VISUAL_PROOF_SUCCESSOR_BUILT__VISUAL_GATE_REQUIRED__NOT_PROMOTED",
    "source_map": BASE,
    "map": MAP,
    "geometry_changed": False,
    "materials_changed": False,
    "runtime_authority_changed": False,
    "v142_visual_status": "REJECT__CROPPED_FRAME_CANNOT_PROVE_LOAD_PATH",
    "fixed_cameras": [c.get_actor_label() for c in cameras],
    "protected_parent_sha256_before": before,
    "protected_parent_sha256_after": after,
    "promotion_authorized": False,
}
OUT.parent.mkdir(parents=True, exist_ok=True)
OUT.write_text(json.dumps(payload, indent=2), encoding="utf-8")
unreal.SystemLibrary.execute_console_command(None, "QUIT_EDITOR")
