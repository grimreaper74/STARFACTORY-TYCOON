"""Apply the actual 60-degree game camera and its exact screen basis to S02."""
import hashlib
import json
import math
from pathlib import Path

import unreal

PROJECT = Path(r"C:\Users\greg_\Projects\LineBossCarFactory_Unreal 5.8")
MAP = "/Game/LineBoss/Candidates/PressShop/PressShopFactorio2p5D_Full_v004_CameraLockedSprites/Maps/LB_PressShop_Factorio2p5D_Full_v004_CameraLockedSprites"
SOURCE_V003 = PROJECT / "Content" / "LineBoss" / "Candidates" / "PressShop" / "PressShopFactorio2p5D_Full_v003_OverheadSprites" / "Maps" / "LB_PressShop_Factorio2p5D_Full_v003_OverheadSprites.umap"
TARGET_FILE = PROJECT / "Content" / "LineBoss" / "Candidates" / "PressShop" / "PressShopFactorio2p5D_Full_v004_CameraLockedSprites" / "Maps" / "LB_PressShop_Factorio2p5D_Full_v004_CameraLockedSprites.umap"
MATERIAL = "/Game/LineBoss/Candidates/PressShop/PressShop2DSprites_v002/Materials/M_LB_PS_S02_DrawForm_SpriteMasterOverhead_Keyed_Unlit_v002"
CAMERA_LABEL = "CAM | 2.5D full Press Shop overview"
SPRITE_LABEL = "2.5D sprite art | S02 draw-form portal press"
S02_LABEL_FRAGMENT = "draw / form portal press"
PROTECTED = {
    "v438": PROJECT / "Content" / "LineBoss" / "Maps" / "LB_PressShop_BuilderAuthorityCandidate_v438.umap",
    "steam_v002": PROJECT / "Content" / "LineBoss" / "Candidates" / "PressShop" / "PressShop2126_v002" / "Maps" / "LB_PressShop_2126_Steam_v002.umap",
}
REPORT = PROJECT / "Saved" / "Audits" / "PressShopIntegration" / "pressshop_2d_s02_camera_locked_mount_v004.json"

def fail(message):
    raise RuntimeError("PRESSSHOP_2D_S02_CAMERA_LOCKED_MOUNT_FAIL: " + message)

def sha256(path):
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()

def dot(a, b):
    return a.x * b.x + a.y * b.y + a.z * b.z

if not TARGET_FILE.is_file() or not SOURCE_V003.is_file() or any(not path.is_file() for path in PROTECTED.values()):
    fail("candidate, source or protected evidence is missing")
material = unreal.load_asset(MATERIAL)
if not isinstance(material, unreal.Material):
    fail("corrected overhead material is missing")
before = {"source_v003": sha256(SOURCE_V003)}
before.update({name: sha256(path) for name, path in PROTECTED.items()})
if not unreal.EditorLoadingAndSavingUtils.load_map(MAP):
    fail("could not load v004 camera-locked candidate")
actors = unreal.EditorLevelLibrary.get_all_level_actors()
camera_matches = [actor for actor in actors if actor.get_actor_label() == CAMERA_LABEL]
sprite_matches = [actor for actor in actors if actor.get_actor_label() == SPRITE_LABEL]
s02_matches = [actor for actor in actors if S02_LABEL_FRAGMENT in actor.get_actor_label() and actor.get_actor_label() != SPRITE_LABEL]
if len(camera_matches) != 1 or len(sprite_matches) != 1 or len(s02_matches) != 1:
    fail("expected one overview camera, S02 sprite and hidden S02 process proxy")
camera, sprite, s02 = camera_matches[0], sprite_matches[0], s02_matches[0]
if not isinstance(camera, unreal.CameraActor) or not isinstance(sprite, unreal.StaticMeshActor) or not isinstance(s02, unreal.StaticMeshActor):
    fail("required actors have unexpected classes")
target = unreal.Vector(0.0, 0.0, 180.0)
old_camera = camera.get_actor_location()
horizontal = math.sqrt((old_camera.x - target.x) ** 2 + (old_camera.y - target.y) ** 2)
new_camera = unreal.Vector(old_camera.x, old_camera.y, target.z + horizontal * math.tan(math.radians(60.0)))
new_rotation = unreal.MathLibrary.find_look_at_rotation(new_camera, target)
camera.set_actor_location(new_camera, False, False)
camera.set_actor_rotation(new_rotation, False)
camera_forward = unreal.MathLibrary.get_forward_vector(new_rotation)
camera_right = unreal.MathLibrary.get_right_vector(new_rotation)
camera_up = unreal.MathLibrary.get_up_vector(new_rotation)
# BasicShapes/Plane's local axes are X/U, Y/V and +Z normal.  The normal is
# intentionally away from the camera so two-sided material displays the back,
# preserving +X screen-right and +Y screen-up without a mirrored sprite.
sprite_rotation = unreal.MathLibrary.make_rot_from_zx(camera_forward, camera_right)
source = s02.get_actor_location()
sprite_location = unreal.Vector(
    source.x - camera_forward.x * 35.0,
    source.y - camera_forward.y * 35.0,
    source.z - camera_forward.z * 35.0,
)
sprite.set_actor_location(sprite_location, False, False)
sprite.set_actor_rotation(sprite_rotation, False)
component = sprite.static_mesh_component
component.set_material(0, material)
component.set_world_scale3d(unreal.Vector(11.0, 11.0, 1.0))
component.set_editor_property("cast_shadow", False)
component.set_collision_enabled(unreal.CollisionEnabled.NO_COLLISION)
component.set_visibility(True, True)
sprite_x = unreal.MathLibrary.get_forward_vector(sprite_rotation)
sprite_y = unreal.MathLibrary.get_right_vector(sprite_rotation)
sprite_normal = unreal.MathLibrary.get_up_vector(sprite_rotation)
alignment = {
    "local_x_to_camera_right": dot(sprite_x, camera_right),
    "local_y_to_camera_up": dot(sprite_y, camera_up),
    "local_z_to_camera_forward": dot(sprite_normal, camera_forward),
}
if any(value < 0.999 for value in alignment.values()):
    fail("sprite plane does not match the actual game camera basis: {}".format(alignment))
if abs(new_rotation.pitch + 60.0) > 0.2:
    fail("overview camera pitch {} is not the locked -60 degree overhead view".format(new_rotation.pitch))
if not unreal.EditorLevelLibrary.save_current_level():
    fail("could not save v004 camera-locked sprite candidate")
after = {"source_v003": sha256(SOURCE_V003)}
after.update({name: sha256(path) for name, path in PROTECTED.items()})
if before != after:
    fail("source candidate or protected evidence changed during camera lock")
report = {
    "status": "PASS__S02_SPRITE_LOCKED_TO_ACTUAL_60_DEGREE_GAME_CAMERA_IN_V004",
    "map": MAP, "material": material.get_path_name(),
    "camera_location_cm": [round(new_camera.x, 3), round(new_camera.y, 3), round(new_camera.z, 3)],
    "camera_rotation": [round(new_rotation.pitch, 3), round(new_rotation.yaw, 3), round(new_rotation.roll, 3)],
    "sprite_rotation": [round(sprite_rotation.pitch, 3), round(sprite_rotation.yaw, 3), round(sprite_rotation.roll, 3)],
    "basis_alignment": {key: round(value, 6) for key, value in alignment.items()},
    "sprite_contract": "same actual -60-degree player camera basis, no arbitrary art-card yaw, no mirroring",
    "source_and_protected_before": before, "source_and_protected_after": after,
    "candidate_map_sha256": sha256(TARGET_FILE),
}
REPORT.parent.mkdir(parents=True, exist_ok=True)
REPORT.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
unreal.log("PRESSSHOP_2D_S02_CAMERA_LOCKED_MOUNT_PASS=" + json.dumps(report, sort_keys=True))

