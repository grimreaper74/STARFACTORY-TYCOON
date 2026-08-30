"""Replace the incorrectly constructed camera so the fixed transform serializes."""
import hashlib
import json
from pathlib import Path
import unreal

PROJECT = Path(r"C:\Users\greg_\Projects\LineBossCarFactory_Unreal 5.8")
MAP = "/Game/LineBoss/Candidates/PressShop/PressShop2126_FullHall_v001/Maps/LB_PressShop_2126_FullHall_v001"
MAP_FILE = PROJECT / "Content" / "LineBoss" / "Candidates" / "PressShop" / "PressShop2126_FullHall_v001" / "Maps" / "LB_PressShop_2126_FullHall_v001.umap"
EXPECTED_SHA256 = "632b0cb86e98c1503e4f63f6e7db4c774f18a866458f6abcf4fc533900493ed2"
RECEIPT = PROJECT / "Saved" / "Audits" / "PressShop2126" / "replace_fullhall_camera_v003_receipt.json"


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest().lower()


if digest(MAP_FILE) != EXPECTED_SHA256:
    raise RuntimeError("candidate map changed before serialized camera replacement")
if not unreal.EditorLoadingAndSavingUtils.load_map(MAP):
    raise RuntimeError("could not load full-hall candidate")
old = next((a for a in unreal.EditorLevelLibrary.get_all_level_actors() if a.get_actor_label() == "CAM | 2126 full hall fixed game view"), None)
if not isinstance(old, unreal.CameraActor):
    raise RuntimeError("incorrect fixed camera missing")
old_rot = old.get_actor_rotation()
unreal.EditorLevelLibrary.destroy_actor(old)
camera = unreal.EditorLevelLibrary.spawn_actor_from_class(
    unreal.CameraActor,
    unreal.Vector(-8025.0, -13160.0, 25980.0),
    unreal.Rotator(pitch=-60.0, yaw=57.63, roll=0.0),
)
camera.set_actor_label("CAM | 2126 full hall fixed game view")
camera.camera_component.projection_mode = unreal.CameraProjectionMode.ORTHOGRAPHIC
camera.camera_component.ortho_width = 26000.0
camera.camera_component.constrain_aspect_ratio = True
camera.camera_component.aspect_ratio = 16.0 / 9.0
new_rot = camera.get_actor_rotation()
if abs(new_rot.pitch + 60.0) > 0.1 or abs(new_rot.yaw - 57.63) > 0.1:
    raise RuntimeError("replacement camera basis is wrong")
if not unreal.EditorLoadingAndSavingUtils.save_current_level():
    raise RuntimeError("replacement camera did not save")
new_sha = digest(MAP_FILE)
if new_sha == EXPECTED_SHA256:
    raise RuntimeError("map bytes did not change after replacing camera")
RECEIPT.parent.mkdir(parents=True, exist_ok=True)
RECEIPT.write_text(json.dumps({
    "status": "PASS__FIXED_CAMERA_REPLACED_AND_SERIALIZED",
    "old_rotation": [old_rot.pitch, old_rot.yaw, old_rot.roll],
    "new_rotation": [new_rot.pitch, new_rot.yaw, new_rot.roll],
    "candidate_sha256_after": new_sha,
}, indent=2, sort_keys=True) + "\n", encoding="utf-8")
unreal.log("PRESSSHOP_2126_FULLHALL_CAMERA_REPLACE_PASS {}".format(RECEIPT))
unreal.SystemLibrary.quit_editor()
