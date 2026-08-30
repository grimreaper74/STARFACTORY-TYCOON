"""Correct the fixed game camera using named Rotator fields."""
import hashlib
import json
from pathlib import Path
import unreal

PROJECT = Path(r"C:\Users\greg_\Projects\LineBossCarFactory_Unreal 5.8")
MAP = "/Game/LineBoss/Candidates/PressShop/PressShop2126_FullHall_v001/Maps/LB_PressShop_2126_FullHall_v001"
MAP_FILE = PROJECT / "Content" / "LineBoss" / "Candidates" / "PressShop" / "PressShop2126_FullHall_v001" / "Maps" / "LB_PressShop_2126_FullHall_v001.umap"
EXPECTED_SHA256 = "632b0cb86e98c1503e4f63f6e7db4c774f18a866458f6abcf4fc533900493ed2"
RECEIPT = PROJECT / "Saved" / "Audits" / "PressShop2126" / "fix_fullhall_camera_v002_receipt.json"


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest().lower()


if digest(MAP_FILE) != EXPECTED_SHA256:
    raise RuntimeError("candidate map changed before camera fix")
if not unreal.EditorLoadingAndSavingUtils.load_map(MAP):
    raise RuntimeError("could not load full-hall candidate")
camera = next((a for a in unreal.EditorLevelLibrary.get_all_level_actors() if a.get_actor_label() == "CAM | 2126 full hall fixed game view"), None)
if not isinstance(camera, unreal.CameraActor):
    raise RuntimeError("fixed game camera missing")
before_rotation = camera.get_actor_rotation()
camera.set_actor_rotation(unreal.Rotator(pitch=-60.0, yaw=57.63, roll=0.0), False)
camera.set_actor_location(unreal.Vector(-8025.0, -13160.0, 25980.0), False, False)
camera.camera_component.projection_mode = unreal.CameraProjectionMode.ORTHOGRAPHIC
camera.camera_component.ortho_width = 26000.0
if not unreal.EditorLoadingAndSavingUtils.save_current_level():
    raise RuntimeError("camera correction did not save")
after_rotation = camera.get_actor_rotation()
RECEIPT.parent.mkdir(parents=True, exist_ok=True)
RECEIPT.write_text(json.dumps({
    "status": "PASS__FIXED_CAMERA_CORRECTED",
    "before_rotation": [before_rotation.pitch, before_rotation.yaw, before_rotation.roll],
    "after_rotation": [after_rotation.pitch, after_rotation.yaw, after_rotation.roll],
    "camera_location_cm": [-8025.0, -13160.0, 25980.0],
    "orthographic_width_cm": 26000.0,
    "candidate_sha256_after": digest(MAP_FILE),
}, indent=2, sort_keys=True) + "\n", encoding="utf-8")
unreal.log("PRESSSHOP_2126_FULLHALL_CAMERA_FIX_PASS {}".format(RECEIPT))
unreal.SystemLibrary.quit_editor()
