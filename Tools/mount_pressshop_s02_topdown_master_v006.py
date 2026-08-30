"""Mount the genuine-alpha top-down S02 master in the isolated v006 candidate."""
import hashlib
import json
from pathlib import Path
import unreal

PROJECT = Path(r"C:\Users\greg_\Projects\LineBossCarFactory_Unreal 5.8")
MAP = "/Game/LineBoss/Candidates/PressShop/PressShopFactorio2p5D_Full_v006_TopdownSprite/Maps/LB_PressShop_Factorio2p5D_Full_v006_TopdownSprite"
SOURCE_V005 = PROJECT / "Content" / "LineBoss" / "Candidates" / "PressShop" / "PressShopFactorio2p5D_Full_v005_FlowAlignedSprites" / "Maps" / "LB_PressShop_Factorio2p5D_Full_v005_FlowAlignedSprites.umap"
TARGET_FILE = PROJECT / "Content" / "LineBoss" / "Candidates" / "PressShop" / "PressShopFactorio2p5D_Full_v006_TopdownSprite" / "Maps" / "LB_PressShop_Factorio2p5D_Full_v006_TopdownSprite.umap"
MATERIAL = "/Game/LineBoss/Candidates/PressShop/PressShop2DSprites_v003/Materials/M_LB_PS_S02_DrawForm_SpriteMasterTopdown_Unlit_v003"
CAMERA_LABEL = "CAM | 2.5D full Press Shop overview"
SPRITE_LABEL = "2.5D sprite art | S02 draw-form portal press"
PROXY_FRAGMENT = "draw / form portal press"
PROTECTED = {
    "v438": PROJECT / "Content" / "LineBoss" / "Maps" / "LB_PressShop_BuilderAuthorityCandidate_v438.umap",
    "steam_v002": PROJECT / "Content" / "LineBoss" / "Candidates" / "PressShop" / "PressShop2126_v002" / "Maps" / "LB_PressShop_2126_Steam_v002.umap",
}
REPORT = PROJECT / "Saved" / "Audits" / "PressShopIntegration" / "pressshop_s02_topdown_master_mount_v006.json"

def fail(message):
    raise RuntimeError("PRESSSHOP_S02_TOPDOWN_MASTER_MOUNT_FAIL: " + message)

def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest().lower()

def dot(a, b):
    return a.x * b.x + a.y * b.y + a.z * b.z

if not TARGET_FILE.is_file() or not SOURCE_V005.is_file() or any(not path.is_file() for path in PROTECTED.values()):
    fail("candidate, source or protected map missing")
material = unreal.load_asset(MATERIAL)
if not isinstance(material, unreal.Material):
    fail("genuine-alpha S02 material missing")
before = {"source_v005": digest(SOURCE_V005)}
before.update({name: digest(path) for name, path in PROTECTED.items()})
if not unreal.EditorLoadingAndSavingUtils.load_map(MAP):
    fail("could not load v006 candidate")
actors = unreal.EditorLevelLibrary.get_all_level_actors()
camera = next((a for a in actors if a.get_actor_label() == CAMERA_LABEL), None)
sprite = next((a for a in actors if a.get_actor_label() == SPRITE_LABEL), None)
proxy = next((a for a in actors if PROXY_FRAGMENT in a.get_actor_label() and a.get_actor_label() != SPRITE_LABEL), None)
if not isinstance(camera, unreal.CameraActor) or not isinstance(sprite, unreal.StaticMeshActor) or not isinstance(proxy, unreal.StaticMeshActor):
    fail("required v006 actors unavailable")
component = sprite.static_mesh_component
component.set_material(0, material)
component.set_editor_property("cast_shadow", False)
component.set_collision_enabled(unreal.CollisionEnabled.NO_COLLISION)
component.set_visibility(True, True)
rotation = sprite.get_actor_rotation()
camera_forward = unreal.MathLibrary.get_forward_vector(camera.get_actor_rotation())
face_alignment = dot(unreal.MathLibrary.get_up_vector(rotation), camera_forward)
if face_alignment < 0.999:
    fail("sprite did not retain its locked camera-facing basis")
if not unreal.EditorLevelLibrary.save_current_level():
    fail("could not save v006 top-down candidate")
after = {"source_v005": digest(SOURCE_V005)}
after.update({name: digest(path) for name, path in PROTECTED.items()})
if before != after:
    fail("source or protected evidence changed during mount")
record = {
    "status": "PASS__S02_GENUINE_ALPHA_TOPDOWN_MASTER_MOUNTED_IN_V006",
    "map": MAP, "material": material.get_path_name(),
    "camera_rotation": [round(v, 3) for v in (camera.get_actor_rotation().pitch, camera.get_actor_rotation().yaw, camera.get_actor_rotation().roll)],
    "sprite_rotation": [round(v, 3) for v in (rotation.pitch, rotation.yaw, rotation.roll)],
    "sprite_face_to_locked_camera": round(face_alignment, 6),
    "camera_rule": "true overhead source art; same fixed actual game camera; world-flow placement retained from v005",
    "source_and_protected_before": before, "source_and_protected_after": after,
    "candidate_map_sha256": digest(TARGET_FILE),
}
REPORT.parent.mkdir(parents=True, exist_ok=True)
REPORT.write_text(json.dumps(record, indent=2, sort_keys=True) + "\n", encoding="utf-8")
unreal.log("PRESSSHOP_S02_TOPDOWN_MASTER_MOUNT_PASS=" + json.dumps(record, sort_keys=True))

