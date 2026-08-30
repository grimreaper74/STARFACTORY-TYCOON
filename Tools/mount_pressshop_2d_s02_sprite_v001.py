"""Mount the generated S02 art on a fixed-camera plane in the v002 candidate."""
import hashlib
import json
import math
from pathlib import Path

import unreal

PROJECT = Path(r"C:\Users\greg_\Projects\LineBossCarFactory_Unreal 5.8")
MAP = "/Game/LineBoss/Candidates/PressShop/PressShopFactorio2p5D_Full_v002_SpriteArt/Maps/LB_PressShop_Factorio2p5D_Full_v002_SpriteArt"
V001_FILE = PROJECT / "Content" / "LineBoss" / "Candidates" / "PressShop" / "PressShopFactorio2p5D_Full_v001" / "Maps" / "LB_PressShop_Factorio2p5D_Full_v001.umap"
TARGET_FILE = PROJECT / "Content" / "LineBoss" / "Candidates" / "PressShop" / "PressShopFactorio2p5D_Full_v002_SpriteArt" / "Maps" / "LB_PressShop_Factorio2p5D_Full_v002_SpriteArt.umap"
MATERIAL = "/Game/LineBoss/Candidates/PressShop/PressShop2DSprites_v001/Materials/M_LB_PS_S02_DrawForm_Sprite_Unlit_v001"
CAMERA_LABEL = "CAM | 2.5D full Press Shop overview"
SPRITE_LABEL = "2.5D sprite art | S02 draw-form portal press"
TAG = unreal.Name("LB.PressShop.Factorio2p5D.Full.v002.SpriteArt")
PROTECTED = {
    "v438": PROJECT / "Content" / "LineBoss" / "Maps" / "LB_PressShop_BuilderAuthorityCandidate_v438.umap",
    "steam_v002": PROJECT / "Content" / "LineBoss" / "Candidates" / "PressShop" / "PressShop2126_v002" / "Maps" / "LB_PressShop_2126_Steam_v002.umap",
}
REPORT = PROJECT / "Saved" / "Audits" / "PressShopIntegration" / "pressshop_2d_sprite_s02_mount_v001.json"

def fail(message):
    raise RuntimeError("PRESSSHOP_2D_S02_SPRITE_MOUNT_FAIL: " + message)

def sha256(path):
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()

def one(actors, predicate, label):
    matches = [actor for actor in actors if predicate(actor)]
    if len(matches) != 1:
        fail("expected one {} but found {}".format(label, len(matches)))
    return matches[0]

if not TARGET_FILE.is_file() or not unreal.EditorAssetLibrary.does_asset_exist(MAP):
    fail("cloned sprite-art candidate is missing")
if not V001_FILE.is_file() or any(not path.is_file() for path in PROTECTED.values()):
    fail("a protected baseline is missing")
if not unreal.EditorLoadingAndSavingUtils.load_map(MAP):
    fail("could not load the v002 sprite-art map")
material = unreal.load_asset(MATERIAL)
plane = unreal.load_asset("/Engine/BasicShapes/Plane")
if not isinstance(material, unreal.Material) or not isinstance(plane, unreal.StaticMesh):
    fail("native sprite material or plane is unavailable")
actors = unreal.EditorLevelLibrary.get_all_level_actors()
if any(actor.get_actor_label() == SPRITE_LABEL for actor in actors):
    fail("the S02 sprite actor already exists")
before = {"v001_source": sha256(V001_FILE)}
before.update({name: sha256(path) for name, path in PROTECTED.items()})
camera = one(actors, lambda actor: actor.get_actor_label() == CAMERA_LABEL, "overview camera")
s02 = one(actors, lambda actor: "draw / form portal press" in actor.get_actor_label(), "S02 process mesh")
if not isinstance(camera, unreal.CameraActor) or not isinstance(s02, unreal.StaticMeshActor):
    fail("candidate has unexpected S02 or overview camera classes")
cam = camera.get_actor_location()
source = s02.get_actor_location()
dx, dy, dz = cam.x - source.x, cam.y - source.y, cam.z - source.z
distance = math.sqrt(dx * dx + dy * dy + dz * dz)
if distance <= 1.0:
    fail("S02 and camera share an invalid position")
normal = unreal.Vector(dx / distance, dy / distance, dz / distance)
horizontal = math.sqrt(normal.x * normal.x + normal.y * normal.y)
if horizontal <= 0.001:
    fail("camera vector is unexpectedly vertical")
screen_right = unreal.Vector(-normal.y / horizontal, normal.x / horizontal, 0.0)
rotation = unreal.MathLibrary.make_rot_from_zx(normal, screen_right)
height_cm = 1050.0
width_cm = height_cm * (1312.0 / 1199.0)
location = unreal.Vector(source.x + normal.x * 35.0, source.y + normal.y * 35.0, source.z + normal.z * 35.0)
sprite = unreal.EditorLevelLibrary.spawn_actor_from_class(unreal.StaticMeshActor, location, rotation)
if not isinstance(sprite, unreal.StaticMeshActor):
    fail("could not spawn S02 visible-art plane")
sprite.set_actor_label(SPRITE_LABEL)
sprite.tags = [TAG, unreal.Name("LB.VisibleArt.Sprite"), unreal.Name("LB.Process.S02"), unreal.Name("LB.NoCollision")]
component = sprite.static_mesh_component
component.set_static_mesh(plane)
component.set_material(0, material)
component.set_world_scale3d(unreal.Vector(width_cm / 100.0, height_cm / 100.0, 1.0))
component.set_editor_property("cast_shadow", False)
component.set_collision_enabled(unreal.CollisionEnabled.NO_COLLISION)
component.set_visibility(True, True)
s02.set_actor_hidden_in_game(True)
s02.static_mesh_component.set_visibility(False, True)
s02.tags = list(s02.tags) + [unreal.Name("LB.Process.Proxy.HiddenForSpriteArt")]
if not unreal.EditorLevelLibrary.save_current_level():
    fail("could not save the sprite-art candidate")
after = {"v001_source": sha256(V001_FILE)}
after.update({name: sha256(path) for name, path in PROTECTED.items()})
if before != after:
    fail("protected evidence changed during sprite mount")
report = {
    "status": "PASS__S02_SPRITE_ART_MOUNTED_IN_ISOLATED_V002_CANDIDATE",
    "map": MAP,
    "sprite_actor": sprite.get_actor_label(),
    "sprite_material": material.get_path_name(),
    "sprite_plane_cm": {"width": round(width_cm, 3), "height": height_cm},
    "sprite_location_cm": [round(location.x, 3), round(location.y, 3), round(location.z, 3)],
    "sprite_rotation": [round(rotation.pitch, 3), round(rotation.yaw, 3), round(rotation.roll, 3)],
    "s02_proxy": {"actor": s02.get_actor_label(), "hidden_visual": True, "retained_for": "process transform and future collision"},
    "protected_hashes_before": before,
    "protected_hashes_after": after,
    "candidate_map_sha256": sha256(TARGET_FILE),
    "next_gate": "native fixed-overview scene capture and direct image review",
}
REPORT.parent.mkdir(parents=True, exist_ok=True)
REPORT.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
unreal.log("PRESSSHOP_2D_S02_SPRITE_MOUNT_PASS=" + json.dumps(report, sort_keys=True))
