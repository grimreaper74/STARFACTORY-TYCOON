"""Rotate the S02 art within the fixed 60-degree camera plane to its real flow axis."""
import hashlib
import json
import math
from pathlib import Path
import unreal

PROJECT = Path(r"C:\Users\greg_\Projects\LineBossCarFactory_Unreal 5.8")
MAP = "/Game/LineBoss/Candidates/PressShop/PressShopFactorio2p5D_Full_v005_FlowAlignedSprites/Maps/LB_PressShop_Factorio2p5D_Full_v005_FlowAlignedSprites"
SOURCE_V004 = PROJECT / "Content" / "LineBoss" / "Candidates" / "PressShop" / "PressShopFactorio2p5D_Full_v004_CameraLockedSprites" / "Maps" / "LB_PressShop_Factorio2p5D_Full_v004_CameraLockedSprites.umap"
TARGET_FILE = PROJECT / "Content" / "LineBoss" / "Candidates" / "PressShop" / "PressShopFactorio2p5D_Full_v005_FlowAlignedSprites" / "Maps" / "LB_PressShop_Factorio2p5D_Full_v005_FlowAlignedSprites.umap"
CAMERA_LABEL = "CAM | 2.5D full Press Shop overview"
SPRITE_LABEL = "2.5D sprite art | S02 draw-form portal press"
PROXY_FRAGMENT = "draw / form portal press"
PROTECTED = {
    "v438": PROJECT / "Content" / "LineBoss" / "Maps" / "LB_PressShop_BuilderAuthorityCandidate_v438.umap",
    "steam_v002": PROJECT / "Content" / "LineBoss" / "Candidates" / "PressShop" / "PressShop2126_v002" / "Maps" / "LB_PressShop_2126_Steam_v002.umap",
}
REPORT = PROJECT / "Saved" / "Audits" / "PressShopIntegration" / "pressshop_s02_flow_alignment_mount_v005.json"

def fail(message):
    raise RuntimeError("PRESSSHOP_S02_FLOW_ALIGNMENT_MOUNT_FAIL: " + message)

def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest().lower()

def dot(a, b):
    return a.x * b.x + a.y * b.y + a.z * b.z

def unit(vector):
    length = math.sqrt(dot(vector, vector))
    if length < 0.0001:
        fail("cannot normalize a near-zero vector")
    return unreal.Vector(vector.x / length, vector.y / length, vector.z / length)

if not TARGET_FILE.is_file() or not SOURCE_V004.is_file() or any(not path.is_file() for path in PROTECTED.values()):
    fail("candidate, source or protected map missing")
before = {"source_v004": digest(SOURCE_V004)}
before.update({name: digest(path) for name, path in PROTECTED.items()})
if not unreal.EditorLoadingAndSavingUtils.load_map(MAP):
    fail("could not load v005 candidate")
actors = unreal.EditorLevelLibrary.get_all_level_actors()
camera = next((a for a in actors if a.get_actor_label() == CAMERA_LABEL), None)
sprite = next((a for a in actors if a.get_actor_label() == SPRITE_LABEL), None)
proxy = next((a for a in actors if PROXY_FRAGMENT in a.get_actor_label() and a.get_actor_label() != SPRITE_LABEL), None)
if not isinstance(camera, unreal.CameraActor) or not isinstance(sprite, unreal.StaticMeshActor) or not isinstance(proxy, unreal.StaticMeshActor):
    fail("required S02 actors are unavailable")
camera_rotation = camera.get_actor_rotation()
camera_forward = unreal.MathLibrary.get_forward_vector(camera_rotation)
flow_axis = unreal.MathLibrary.get_forward_vector(proxy.get_actor_rotation())
# Source-image +X is the press's long process axis. Project the proxy's actual
# +X flow direction into the camera plane and use that as the plane's local +X.
# This preserves the shared camera elevation and face direction, but makes the
# depicted machine connect to the diagonal production line instead of lying flat
# across the screen.
projected_flow = unit(unreal.Vector(
    flow_axis.x - camera_forward.x * dot(flow_axis, camera_forward),
    flow_axis.y - camera_forward.y * dot(flow_axis, camera_forward),
    flow_axis.z - camera_forward.z * dot(flow_axis, camera_forward),
))
sprite_rotation = unreal.MathLibrary.make_rot_from_zx(camera_forward, projected_flow)
source = proxy.get_actor_location()
sprite_location = unreal.Vector(
    source.x - camera_forward.x * 35.0,
    source.y - camera_forward.y * 35.0,
    source.z - camera_forward.z * 35.0,
)
sprite.set_actor_location(sprite_location, False, False)
sprite.set_actor_rotation(sprite_rotation, False)
sprite_x = unreal.MathLibrary.get_forward_vector(sprite_rotation)
sprite_normal = unreal.MathLibrary.get_up_vector(sprite_rotation)
alignment = {
    "local_x_to_projected_proxy_flow": dot(sprite_x, projected_flow),
    "local_x_to_camera_forward": dot(sprite_x, camera_forward),
    "local_z_to_camera_forward": dot(sprite_normal, camera_forward),
}
if alignment["local_x_to_projected_proxy_flow"] < 0.999:
    fail("image +X is not aligned to projected S02 flow: {}".format(alignment))
if abs(alignment["local_x_to_camera_forward"]) > 0.001:
    fail("image +X escaped the locked camera plane: {}".format(alignment))
if alignment["local_z_to_camera_forward"] < 0.999:
    fail("sprite face direction changed: {}".format(alignment))
if abs(camera_rotation.pitch + 60.0) > 0.2:
    fail("camera pitch is no longer the locked -60 degree view")
if not unreal.EditorLevelLibrary.save_current_level():
    fail("could not save v005 candidate")
after = {"source_v004": digest(SOURCE_V004)}
after.update({name: digest(path) for name, path in PROTECTED.items()})
if before != after:
    fail("source or protected evidence changed during S02 flow alignment")
record = {
    "status": "PASS__S02_ART_FLOW_ALIGNED_WITHIN_LOCKED_60_DEGREE_CAMERA",
    "map": MAP,
    "camera_rotation": [round(camera_rotation.pitch, 3), round(camera_rotation.yaw, 3), round(camera_rotation.roll, 3)],
    "proxy_world_flow_axis": [round(flow_axis.x, 6), round(flow_axis.y, 6), round(flow_axis.z, 6)],
    "projected_flow_axis": [round(projected_flow.x, 6), round(projected_flow.y, 6), round(projected_flow.z, 6)],
    "sprite_rotation": [round(sprite_rotation.pitch, 3), round(sprite_rotation.yaw, 3), round(sprite_rotation.roll, 3)],
    "alignment": {name: round(value, 6) for name, value in alignment.items()},
    "contract": "all masters share camera pitch; each directional machine is rotated solely from its declared process axis",
    "source_and_protected_before": before, "source_and_protected_after": after,
    "candidate_map_sha256": digest(TARGET_FILE),
}
REPORT.parent.mkdir(parents=True, exist_ok=True)
REPORT.write_text(json.dumps(record, indent=2, sort_keys=True) + "\n", encoding="utf-8")
unreal.log("PRESSSHOP_S02_FLOW_ALIGNMENT_MOUNT_PASS=" + json.dumps(record, sort_keys=True))

