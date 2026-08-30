"""Read-only orientation audit for the rejected first overhead sprite mount."""
import json
import math
from pathlib import Path

import unreal

PROJECT = Path(r"C:\Users\greg_\Projects\LineBossCarFactory_Unreal 5.8")
MAP = "/Game/LineBoss/Candidates/PressShop/PressShopFactorio2p5D_Full_v003_OverheadSprites/Maps/LB_PressShop_Factorio2p5D_Full_v003_OverheadSprites"
CAMERA_LABEL = "CAM | 2.5D full Press Shop overview"
SPRITE_LABEL = "2.5D sprite art | S02 draw-form portal press"
REPORT = PROJECT / "Saved" / "Audits" / "PressShopIntegration" / "pressshop_s02_sprite_orientation_audit_v001.json"

def dot(a, b):
    return a.x * b.x + a.y * b.y + a.z * b.z

def as_list(vector):
    return [round(vector.x, 6), round(vector.y, 6), round(vector.z, 6)]

def fail(message):
    raise RuntimeError("PRESSSHOP_S02_SPRITE_ORIENTATION_AUDIT_FAIL: " + message)

if not unreal.EditorLoadingAndSavingUtils.load_map(MAP):
    fail("could not load v003 overhead sprite candidate")
actors = unreal.EditorLevelLibrary.get_all_level_actors()
camera_matches = [actor for actor in actors if actor.get_actor_label() == CAMERA_LABEL]
sprite_matches = [actor for actor in actors if actor.get_actor_label() == SPRITE_LABEL]
if len(camera_matches) != 1 or len(sprite_matches) != 1:
    fail("expected one overview camera and one sprite actor")
camera = camera_matches[0]
sprite = sprite_matches[0]
camera_rotation = camera.get_actor_rotation()
sprite_rotation = sprite.get_actor_rotation()
camera_forward = unreal.MathLibrary.get_forward_vector(camera_rotation)
camera_right = unreal.MathLibrary.get_right_vector(camera_rotation)
camera_up = unreal.MathLibrary.get_up_vector(camera_rotation)
sprite_x = unreal.MathLibrary.get_forward_vector(sprite_rotation)
sprite_y = unreal.MathLibrary.get_right_vector(sprite_rotation)
sprite_normal = unreal.MathLibrary.get_up_vector(sprite_rotation)
expected_normal = unreal.Vector(-camera_forward.x, -camera_forward.y, -camera_forward.z)
report = {
    "status": "PASS__READ_ONLY_ORIENTATION_MEASUREMENT__NO_MAP_SAVE",
    "map": MAP,
    "camera_rotation": [round(camera_rotation.pitch, 3), round(camera_rotation.yaw, 3), round(camera_rotation.roll, 3)],
    "sprite_rotation": [round(sprite_rotation.pitch, 3), round(sprite_rotation.yaw, 3), round(sprite_rotation.roll, 3)],
    "camera_basis": {"forward": as_list(camera_forward), "right": as_list(camera_right), "up": as_list(camera_up)},
    "sprite_basis_assuming_basic_plane_normal_is_local_z": {"local_x": as_list(sprite_x), "local_y": as_list(sprite_y), "local_z_normal": as_list(sprite_normal)},
    "alignment_dot_products": {
        "plane_normal_to_camera": round(dot(sprite_normal, expected_normal), 6),
        "plane_local_x_to_camera_right": round(dot(sprite_x, camera_right), 6),
        "plane_local_y_to_camera_up": round(dot(sprite_y, camera_up), 6),
    },
    "interpretation": "A camera-facing sprite requires all three dot products to be near +1. The prior capture is visual evidence that this mount did not meet that contract.",
}
REPORT.parent.mkdir(parents=True, exist_ok=True)
REPORT.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
unreal.log("PRESSSHOP_S02_SPRITE_ORIENTATION_AUDIT=" + json.dumps(report, sort_keys=True))
unreal.SystemLibrary.quit_editor()

