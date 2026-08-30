"""Mount the complete individual-sprite Press Shop in the isolated v007 map."""
import hashlib
import json
import math
from pathlib import Path

import unreal

PROJECT = Path(r"C:\Users\greg_\Projects\LineBossCarFactory_Unreal 5.8")
MAP = "/Game/LineBoss/Candidates/PressShop/PressShopFactorio2p5D_IndividualSprites_v007/Maps/LB_PressShop_Factorio2p5D_IndividualSprites_v007"
SOURCE_V006 = PROJECT / "Content" / "LineBoss" / "Candidates" / "PressShop" / "PressShopFactorio2p5D_Full_v006_TopdownSprite" / "Maps" / "LB_PressShop_Factorio2p5D_Full_v006_TopdownSprite.umap"
TARGET_FILE = PROJECT / "Content" / "LineBoss" / "Candidates" / "PressShop" / "PressShopFactorio2p5D_IndividualSprites_v007" / "Maps" / "LB_PressShop_Factorio2p5D_IndividualSprites_v007.umap"
CAMERA_LABEL = "CAM | 2.5D full Press Shop overview"
S02_SPRITE_LABEL = "2.5D sprite art | S02 draw-form portal press"
PLANE = "/Engine/BasicShapes/Plane.Plane"
MATERIAL_ROOT = "/Game/LineBoss/Candidates/PressShop/PressShop2DSprites_v004/Materials/"
PROTECTED_MAPS = {
    PROJECT / "Content" / "LineBoss" / "Maps" / "LB_PressShop_BuilderAuthorityCandidate_v438.umap": "5029c9d827d9a1d72c12f27ee757c9bc1e47febd5006ce6d7ba319aad2e7fec8",
    PROJECT / "Content" / "LineBoss" / "Candidates" / "PressShop" / "PressShop2126_v002" / "Maps" / "LB_PressShop_2126_Steam_v002.umap": "cc09cf46d33e8a562d97f5a3bc35a5b42c9582d8e4650cf315694ebf340e4aa0",
}
REPORT = PROJECT / "Saved" / "Audits" / "PressShopIntegration" / "pressshop_individual_sprites_v007_mount.json"
TRAIN_WORLD_FLOW = unreal.Vector(1.0, 0.0, 0.0)
MACHINE_SPECS = (
    ("2.5D full | 01 | coil-free autonomous feeder", "2.5D sprite art | S01 straightener / servo feeder", "M_LB_PS_S01_StraightenerFeeder_Topdown_Unlit_v004", 1.78),
    ("2.5D full | 03 | trim press", "2.5D sprite art | S03 trim press", "M_LB_PS_S03_TrimPress_Topdown_Unlit_v004", 1.00),
    ("2.5D full | 04 | pierce press", "2.5D sprite art | S04 pierce press", "M_LB_PS_S04_PiercePress_Topdown_Unlit_v004", 1.00),
    ("2.5D full | 05 | flange / hem press", "2.5D sprite art | S05 flange / hem press", "M_LB_PS_S05_FlangeHem_Topdown_Unlit_v004", 1.00),
    ("2.5D full | 06 | vision / outfeed press", "2.5D sprite art | S06 vision / reject press", "M_LB_PS_S06_VisionUnload_Topdown_Unlit_v004", 1.50),
)
CONVEYOR_LABELS = tuple("2.5D full | transfer conveyor {:02d}".format(index) for index in range(1, 7))
GANTRY_PAIRS = (
    ("2.5D full | 02 | draw / form portal press", "2.5D full | 03 | trim press"),
    ("2.5D full | 03 | trim press", "2.5D full | 04 | pierce press"),
    ("2.5D full | 04 | pierce press", "2.5D full | 05 | flange / hem press"),
    ("2.5D full | 05 | flange / hem press", "2.5D full | 06 | vision / outfeed press"),
)


def fail(message):
    raise RuntimeError("PRESSSHOP_INDIVIDUAL_SPRITES_V007_MOUNT_FAIL: " + message)


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest().lower()


def dot(a, b):
    return a.x * b.x + a.y * b.y + a.z * b.z


def unit(vector):
    length = math.sqrt(dot(vector, vector))
    if length < 0.0001:
        fail("cannot normalize a zero-length vector")
    return unreal.Vector(vector.x / length, vector.y / length, vector.z / length)


def projected(vector, normal):
    return unit(unreal.Vector(
        vector.x - normal.x * dot(vector, normal),
        vector.y - normal.y * dot(vector, normal),
        vector.z - normal.z * dot(vector, normal),
    ))


def find_one(actors, label):
    matches = [actor for actor in actors if actor.get_actor_label() == label]
    if len(matches) != 1:
        fail("expected one actor {!r}, found {}".format(label, len(matches)))
    return matches[0]


def hide_proxy(actor):
    if not isinstance(actor, unreal.StaticMeshActor):
        fail("expected a StaticMeshActor proxy: {}".format(actor.get_actor_label()))
    actor.static_mesh_component.set_visibility(False, True)
    actor.static_mesh_component.set_editor_property("cast_shadow", False)
    actor.set_actor_hidden_in_game(True)


def width_from_proxy(actor):
    _, extent = actor.get_actor_bounds(False)
    width = max(2.0 * extent.x, 2.0 * extent.y) * 1.08
    if width < 100.0:
        fail("invalid bounds for {}".format(actor.get_actor_label()))
    return width


def spawn_card(label, material, anchor, width_cm, aspect, depth_cm):
    if any(actor.get_actor_label() == label for actor in unreal.EditorLevelLibrary.get_all_level_actors()):
        fail("sprite label already exists: {}".format(label))
    location = unreal.Vector(
        anchor.x - camera_forward.x * depth_cm,
        anchor.y - camera_forward.y * depth_cm,
        anchor.z - camera_forward.z * depth_cm,
    )
    actor = unreal.EditorLevelLibrary.spawn_actor_from_class(unreal.StaticMeshActor, location, card_rotation)
    if not isinstance(actor, unreal.StaticMeshActor):
        fail("could not spawn {}".format(label))
    actor.set_actor_label(label)
    component = actor.static_mesh_component
    component.set_static_mesh(plane_mesh)
    component.set_material(0, material)
    component.set_collision_enabled(unreal.CollisionEnabled.NO_COLLISION)
    component.set_editor_property("cast_shadow", False)
    component.set_visibility(True, True)
    actor.set_actor_hidden_in_game(False)
    actor.set_actor_scale3d(unreal.Vector(width_cm / 100.0, width_cm / (100.0 * aspect), 1.0))
    face_camera = dot(unreal.MathLibrary.get_up_vector(card_rotation), camera_forward)
    follow_train = dot(unreal.MathLibrary.get_forward_vector(card_rotation), projected_train_flow)
    if face_camera < 0.999 or follow_train < 0.999:
        fail("basis error for {}".format(label))
    return actor, location, face_camera, follow_train


if not TARGET_FILE.is_file() or not SOURCE_V006.is_file():
    fail("v006 source or v007 target map is missing")
for path, expected in PROTECTED_MAPS.items():
    if not path.is_file() or digest(path) != expected:
        fail("protected map missing or changed: {}".format(path))
before = {"v006_source": digest(SOURCE_V006)}
before.update({str(path): digest(path) for path in PROTECTED_MAPS})

if not unreal.EditorLoadingAndSavingUtils.load_map(MAP):
    fail("could not load v007 candidate")
actors = unreal.EditorLevelLibrary.get_all_level_actors()
camera = find_one(actors, CAMERA_LABEL)
if not isinstance(camera, unreal.CameraActor):
    fail("locked overview camera missing")
if abs(camera.get_actor_rotation().pitch + 60.0) > 0.2:
    fail("overview camera is no longer locked at -60 degrees")
plane_mesh = unreal.load_asset(PLANE)
if not isinstance(plane_mesh, unreal.StaticMesh):
    fail("engine plane mesh missing")
camera_forward = unreal.MathLibrary.get_forward_vector(camera.get_actor_rotation())
projected_train_flow = projected(TRAIN_WORLD_FLOW, camera_forward)
card_rotation = unreal.MathLibrary.make_rot_from_zx(camera_forward, projected_train_flow)

# Existing accepted S02 art remains visible; only its former 3D proxy is hidden.
s02_proxy = find_one(actors, "2.5D full | 02 | draw / form portal press")
s02_sprite = find_one(actors, S02_SPRITE_LABEL)
if not isinstance(s02_sprite, unreal.StaticMeshActor):
    fail("accepted S02 card is missing")
hide_proxy(s02_proxy)

records = []
for proxy_label, sprite_label, material_name, aspect in MACHINE_SPECS:
    proxy = find_one(actors, proxy_label)
    material = unreal.load_asset(MATERIAL_ROOT + material_name)
    if not isinstance(material, unreal.Material):
        fail("native material missing: {}".format(material_name))
    width = width_from_proxy(proxy)
    anchor = proxy.get_actor_location()
    hide_proxy(proxy)
    sprite, location, face_camera, follow_train = spawn_card(sprite_label, material, anchor, width, aspect, 40.0)
    records.append({"kind": "machine", "proxy": proxy_label, "sprite": sprite.get_actor_label(), "material": material.get_path_name(), "width_cm": round(width, 3), "aspect": aspect, "location_cm": [round(location.x, 3), round(location.y, 3), round(location.z, 3)], "face_camera": round(face_camera, 6), "local_x_to_train_flow": round(follow_train, 6)})

conveyor_material = unreal.load_asset(MATERIAL_ROOT + "M_LB_PS_TransferConveyor_Topdown_Unlit_v004")
if not isinstance(conveyor_material, unreal.Material):
    fail("native conveyor material missing")
for index, proxy_label in enumerate(CONVEYOR_LABELS, 1):
    proxy = find_one(actors, proxy_label)
    width = width_from_proxy(proxy)
    anchor = proxy.get_actor_location()
    hide_proxy(proxy)
    sprite, _, face_camera, follow_train = spawn_card("2.5D sprite art | transfer conveyor {:02d}".format(index), conveyor_material, anchor, width, 3.0, 52.0)
    records.append({"kind": "conveyor", "proxy": proxy_label, "sprite": sprite.get_actor_label(), "width_cm": round(width, 3), "face_camera": round(face_camera, 6), "local_x_to_train_flow": round(follow_train, 6)})

gantry_material = unreal.load_asset(MATERIAL_ROOT + "M_LB_PS_TransferGantry_Topdown_Unlit_v004")
if not isinstance(gantry_material, unreal.Material):
    fail("native transfer-gantry material missing")
for index, pair in enumerate(GANTRY_PAIRS, 1):
    left = find_one(actors, pair[0]).get_actor_location()
    right = find_one(actors, pair[1]).get_actor_location()
    gap = math.sqrt((right.x - left.x) ** 2 + (right.y - left.y) ** 2)
    anchor = unreal.Vector((left.x + right.x) * 0.5, (left.y + right.y) * 0.5, max(left.z, right.z) + 430.0)
    width = min(1650.0, max(1200.0, gap * 0.84))
    sprite, _, face_camera, follow_train = spawn_card("2.5D sprite art | overhead transfer gantry {:02d}".format(index), gantry_material, anchor, width, 3.0, 82.0)
    records.append({"kind": "transfer_robot", "between": list(pair), "sprite": sprite.get_actor_label(), "width_cm": round(width, 3), "face_camera": round(face_camera, 6), "local_x_to_train_flow": round(follow_train, 6)})

if not unreal.EditorLevelLibrary.save_current_level():
    fail("could not save v007")
after = {"v006_source": digest(SOURCE_V006)}
after.update({str(path): digest(path) for path in PROTECTED_MAPS})
if before != after:
    fail("v006 source or protected evidence changed")
record = {"status": "PASS__FULL_2126_INDIVIDUAL_SPRITE_PRESS_LINE_MOUNTED_IN_V007", "map": MAP, "camera": CAMERA_LABEL, "camera_rotation": [round(value, 3) for value in (camera.get_actor_rotation().pitch, camera.get_actor_rotation().yaw, camera.get_actor_rotation().roll)], "world_process_flow": [1.0, 0.0, 0.0], "accepted_s02_retained": s02_sprite.get_actor_label(), "records": records, "source_and_protected_unchanged_before_after": True, "target_sha256": digest(TARGET_FILE)}
REPORT.parent.mkdir(parents=True, exist_ok=True)
REPORT.write_text(json.dumps(record, indent=2, sort_keys=True) + "\n", encoding="utf-8")
unreal.log("PRESSSHOP_INDIVIDUAL_SPRITES_V007_MOUNT_PASS=" + json.dumps(record, sort_keys=True))
