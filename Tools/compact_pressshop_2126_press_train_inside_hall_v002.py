"""Re-spawn the four 2126 press sprites on a dense pitch entirely inside the hall."""
import hashlib
import json
import math
from pathlib import Path
import unreal

PROJECT = Path(r"C:\Users\greg_\Projects\LineBossCarFactory_Unreal 5.8")
MAP = "/Game/LineBoss/Candidates/PressShop/PressShop2126_FullHall_v001/Maps/LB_PressShop_2126_FullHall_v001"
ROOT = "/Game/LineBoss/Candidates/PressShop/PressShop2126_FullHall_v001/Sprites"
RECEIPT = PROJECT / "Saved" / "Audits" / "PressShop2126" / "compact_press_train_inside_hall_v002_receipt.json"
PROTECTED = {
    PROJECT / "Content" / "LineBoss" / "Maps" / "LB_PressShop_BuilderAuthorityCandidate_v438.umap": "5029c9d827d9a1d72c12f27ee757c9bc1e47febd5006ce6d7ba319aad2e7fec8",
    PROJECT / "Content" / "LineBoss" / "Candidates" / "PressShop" / "PressShop2126_v002" / "Maps" / "LB_PressShop_2126_Steam_v002.umap": "cc09cf46d33e8a562d97f5a3bc35a5b42c9582d8e4650cf315694ebf340e4aa0",
}
STATIONS = [
    ("S01", "2126 PRESS | S01 autonomous deep-draw servo press", "M_CA_MW_2126_S01_DeepDrawServoPress_UnlitMasked_v001", [-3500.0, -100.0, 500.0], [28.0, 18.0, 1.0]),
    ("S02", "2126 PRESS | S02 autonomous redraw calibration press", "M_CA_MW_2126_S02_RedrawCalibrationPress_UnlitMasked_v001", [-3500.0, 1700.0, 460.0], [28.0, 18.0, 1.0]),
    ("S03", "2126 PRESS | S03 autonomous trim pierce press", "M_CA_MW_2126_S03_TrimPiercePress_UnlitMasked_v001", [-3500.0, 3500.0, 520.0], [26.0, 18.0, 1.0]),
    ("S04", "2126 PRESS | S04 autonomous flange final-form press", "M_CA_MW_2126_S04_FlangeFinalFormPress_UnlitMasked_v001", [-3500.0, 5300.0, 480.0], [26.0, 18.0, 1.0]),
]


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest().lower()


def dot(a, b):
    return a.x * b.x + a.y * b.y + a.z * b.z


def unit(v):
    length = math.sqrt(dot(v, v))
    return unreal.Vector(v.x / length, v.y / length, v.z / length)


def projected(v, normal):
    return unit(unreal.Vector(v.x - normal.x * dot(v, normal), v.y - normal.y * dot(v, normal), v.z - normal.z * dot(v, normal)))


before = {str(path): digest(path) for path in PROTECTED}
for path, expected in PROTECTED.items():
    if before[str(path)] != expected:
        raise RuntimeError(f"protected map missing or changed: {path}")
if not unreal.EditorLoadingAndSavingUtils.load_map(MAP):
    raise RuntimeError("could not load isolated 2126 candidate")
actors = list(unreal.EditorLevelLibrary.get_all_level_actors())
camera = next((a for a in actors if a.get_actor_label() == "CAM | 2126 full hall fixed game view"), None)
if not isinstance(camera, unreal.CameraActor):
    raise RuntimeError("fixed camera missing")
rotation = camera.get_actor_rotation()
if abs(rotation.pitch + 60.0) > 0.2 or abs(rotation.yaw - 57.63) > 0.2:
    raise RuntimeError("fixed camera contract changed")

labels = {row[1] for row in STATIONS}
found = []
for actor in actors:
    if actor.get_actor_label() in labels:
        found.append(actor.get_actor_label())
        unreal.EditorLevelLibrary.destroy_actor(actor)
if set(found) != labels:
    raise RuntimeError(f"not all four existing station actors were found: {sorted(found)}")

camera_forward = unreal.MathLibrary.get_forward_vector(rotation)
flow_axis = projected(unreal.Vector(0.0, 1.0, 0.0), camera_forward)
card_rotation = unreal.MathLibrary.make_rot_from_zx(camera_forward, flow_axis)
plane = unreal.load_asset("/Engine/BasicShapes/Plane.Plane")
mounted = []
for station_id, label, material_name, anchor_values, scale_values in STATIONS:
    material = unreal.load_asset(ROOT + "/" + material_name)
    if not isinstance(material, unreal.Material):
        raise RuntimeError(f"station material missing: {station_id}")
    anchor = unreal.Vector(*anchor_values)
    location = unreal.Vector(anchor.x - camera_forward.x * 125.0, anchor.y - camera_forward.y * 125.0, anchor.z - camera_forward.z * 125.0)
    card = unreal.EditorLevelLibrary.spawn_actor_from_class(unreal.StaticMeshActor, location, card_rotation)
    card.set_actor_label(label)
    card.static_mesh_component.set_static_mesh(plane)
    card.static_mesh_component.set_material(0, material)
    card.static_mesh_component.set_collision_enabled(unreal.CollisionEnabled.NO_COLLISION)
    card.static_mesh_component.set_editor_property("cast_shadow", False)
    card.set_actor_scale3d(unreal.Vector(*scale_values))
    mounted.append({"id": station_id, "label": label, "anchor_cm": anchor_values, "location_cm": [round(location.x, 2), round(location.y, 2), round(location.z, 2)], "scale": scale_values})

if not unreal.EditorLoadingAndSavingUtils.save_current_level():
    raise RuntimeError("compacted press train did not save")
unreal.EditorLoadingAndSavingUtils.save_dirty_packages(True, True)
after = {str(path): digest(path) for path in PROTECTED}
if after != before:
    raise RuntimeError("protected maps changed during train compaction")

RECEIPT.parent.mkdir(parents=True, exist_ok=True)
RECEIPT.write_text(json.dumps({
    "status": "PASS__2126_PRESS_TRAIN_COMPACTED_INSIDE_HALL",
    "map": MAP,
    "station_pitch_cm": 1800.0,
    "flow_axis": "+Y",
    "mounted_stations": mounted,
    "protected_sha256_before": before,
    "protected_sha256_after": after,
}, indent=2, sort_keys=True) + "\n", encoding="utf-8")
unreal.log(f"PRESSSHOP_2126_PRESS_TRAIN_COMPACTION_PASS receipt={RECEIPT}")
unreal.SystemLibrary.quit_editor()
