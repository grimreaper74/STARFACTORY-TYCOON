"""Install the four-station 2126 sprite press train in the isolated full-hall candidate."""
import hashlib
import json
import math
from pathlib import Path
import unreal

PROJECT = Path(r"C:\Users\greg_\Projects\LineBossCarFactory_Unreal 5.8")
MAP = "/Game/LineBoss/Candidates/PressShop/PressShop2126_FullHall_v001/Maps/LB_PressShop_2126_FullHall_v001"
ROOT = "/Game/LineBoss/Candidates/PressShop/PressShop2126_FullHall_v001/Sprites"
SOURCE_ROOT = PROJECT / "SourceArt" / "PressShop2126" / "Sprites"
RECEIPT = PROJECT / "Saved" / "Audits" / "PressShop2126" / "install_complete_press_train_v001_receipt.json"
CAMERA_LABEL = "CAM | 2126 full hall fixed game view"
PROTECTED = {
    PROJECT / "Content" / "LineBoss" / "Maps" / "LB_PressShop_BuilderAuthorityCandidate_v438.umap": "5029c9d827d9a1d72c12f27ee757c9bc1e47febd5006ce6d7ba319aad2e7fec8",
    PROJECT / "Content" / "LineBoss" / "Candidates" / "PressShop" / "PressShop2126_v002" / "Maps" / "LB_PressShop_2126_Steam_v002.umap": "cc09cf46d33e8a562d97f5a3bc35a5b42c9582d8e4650cf315694ebf340e4aa0",
}
STATIONS = [
    {
        "id": "S01",
        "label": "2126 PRESS | S01 autonomous deep-draw servo press",
        "texture": "T_CA_MW_2126_S01_DeepDrawServoPress_v001",
        "material": "M_CA_MW_2126_S01_DeepDrawServoPress_UnlitMasked_v001",
        "anchor": [-3500.0, 900.0, 500.0],
        "scale": [27.0, 18.0, 1.0],
        "existing": True,
    },
    {
        "id": "S02",
        "label": "2126 PRESS | S02 autonomous redraw calibration press",
        "texture": "T_CA_MW_2126_S02_RedrawCalibrationPress_v001",
        "material": "M_CA_MW_2126_S02_RedrawCalibrationPress_UnlitMasked_v001",
        "anchor": [-3500.0, 4000.0, 460.0],
        "scale": [27.0, 18.0, 1.0],
    },
    {
        "id": "S03",
        "label": "2126 PRESS | S03 autonomous trim pierce press",
        "texture": "T_CA_MW_2126_S03_TrimPiercePress_v001",
        "material": "M_CA_MW_2126_S03_TrimPiercePress_UnlitMasked_v001",
        "anchor": [-3500.0, 7100.0, 520.0],
        "scale": [25.0, 18.0, 1.0],
    },
    {
        "id": "S04",
        "label": "2126 PRESS | S04 autonomous flange final-form press",
        "texture": "T_CA_MW_2126_S04_FlangeFinalFormPress_v001",
        "material": "M_CA_MW_2126_S04_FlangeFinalFormPress_UnlitMasked_v001",
        "anchor": [-3500.0, 10200.0, 480.0],
        "scale": [25.0, 18.0, 1.0],
    },
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


def import_texture_and_material(station):
    source = SOURCE_ROOT / (station["texture"] + ".png")
    if not source.is_file():
        raise RuntimeError(f"missing station source: {source}")
    texture_path = ROOT + "/" + station["texture"]
    material_path = ROOT + "/" + station["material"]
    if unreal.EditorAssetLibrary.does_asset_exist(texture_path) or unreal.EditorAssetLibrary.does_asset_exist(material_path):
        raise RuntimeError(f"refusing to overwrite station assets: {station['id']}")
    task = unreal.AssetImportTask()
    task.set_editor_properties({
        "filename": str(source),
        "destination_path": ROOT,
        "destination_name": station["texture"],
        "automated": True,
        "replace_existing": False,
        "save": True,
    })
    unreal.AssetToolsHelpers.get_asset_tools().import_asset_tasks([task])
    paths = list(task.get_editor_property("imported_object_paths") or [])
    if len(paths) != 1:
        raise RuntimeError(f"texture import failed for {station['id']}: {paths}")
    texture = unreal.load_asset(paths[0])
    if not isinstance(texture, unreal.Texture2D):
        raise RuntimeError(f"PNG did not import as Texture2D: {station['id']}")
    texture.set_editor_properties({"srgb": True, "compression_settings": unreal.TextureCompressionSettings.TC_DEFAULT, "never_stream": True})
    unreal.EditorAssetLibrary.save_loaded_asset(texture, only_if_is_dirty=False)
    material = unreal.AssetToolsHelpers.get_asset_tools().create_asset(station["material"], ROOT, unreal.Material, unreal.MaterialFactoryNew())
    if not isinstance(material, unreal.Material):
        raise RuntimeError(f"material creation failed: {station['id']}")
    material.set_editor_properties({
        "blend_mode": unreal.BlendMode.BLEND_MASKED,
        "shading_model": unreal.MaterialShadingModel.MSM_UNLIT,
        "two_sided": True,
        "opacity_mask_clip_value": 0.025,
    })
    mel = unreal.MaterialEditingLibrary
    sample = mel.create_material_expression(material, unreal.MaterialExpressionTextureSample, -420, 0)
    sample.set_editor_properties({"texture": texture, "sampler_type": unreal.MaterialSamplerType.SAMPLERTYPE_COLOR})
    if not mel.connect_material_property(sample, "RGB", unreal.MaterialProperty.MP_EMISSIVE_COLOR):
        raise RuntimeError(f"colour connection failed: {station['id']}")
    if not mel.connect_material_property(sample, "A", unreal.MaterialProperty.MP_OPACITY_MASK):
        raise RuntimeError(f"alpha connection failed: {station['id']}")
    mel.recompile_material(material)
    unreal.EditorAssetLibrary.save_loaded_asset(material, only_if_is_dirty=False)
    return material, source


before = {str(path): digest(path) for path in PROTECTED}
for path, expected in PROTECTED.items():
    if before[str(path)] != expected:
        raise RuntimeError(f"protected map missing or changed: {path}")

imported = {}
for station in STATIONS:
    if station.get("existing"):
        material = unreal.load_asset(ROOT + "/" + station["material"])
        source = SOURCE_ROOT / (station["texture"] + ".png")
        if not isinstance(material, unreal.Material) or not source.is_file():
            raise RuntimeError("existing S01 assets are missing")
    else:
        material, source = import_texture_and_material(station)
    imported[station["id"]] = {"material": material, "source": source}

if not unreal.EditorLoadingAndSavingUtils.load_map(MAP):
    raise RuntimeError("could not load isolated 2126 candidate")
actors = list(unreal.EditorLevelLibrary.get_all_level_actors())
camera = next((a for a in actors if a.get_actor_label() == CAMERA_LABEL), None)
if not isinstance(camera, unreal.CameraActor):
    raise RuntimeError("fixed game camera missing")
rotation = camera.get_actor_rotation()
if abs(rotation.pitch + 60.0) > 0.2 or abs(rotation.yaw - 57.63) > 0.2:
    raise RuntimeError("fixed game camera basis changed")

# Roof-open candidate: remove only the old full-hall roof liner and repeated press columns.
removed_obstructions = []
for actor in actors:
    if not isinstance(actor, unreal.StaticMeshActor):
        continue
    label = actor.get_actor_label()
    if label.startswith("LB_PRESS_Column_") or label.startswith("LB_WHOLE_V235_RoofLiner_"):
        removed_obstructions.append(label)
        unreal.EditorLevelLibrary.destroy_actor(actor)

# Re-spawn S01 so its new station pitch persists in an OFPA map.
for actor in list(unreal.EditorLevelLibrary.get_all_level_actors()):
    if actor.get_actor_label() == STATIONS[0]["label"]:
        unreal.EditorLevelLibrary.destroy_actor(actor)

existing_labels = {a.get_actor_label() for a in unreal.EditorLevelLibrary.get_all_level_actors()}
for station in STATIONS[1:]:
    if station["label"] in existing_labels:
        raise RuntimeError(f"station already exists: {station['id']}")

camera_forward = unreal.MathLibrary.get_forward_vector(rotation)
flow_axis = projected(unreal.Vector(0.0, 1.0, 0.0), camera_forward)
card_rotation = unreal.MathLibrary.make_rot_from_zx(camera_forward, flow_axis)
plane = unreal.load_asset("/Engine/BasicShapes/Plane.Plane")
mounted = []
for station in STATIONS:
    anchor = unreal.Vector(*station["anchor"])
    location = unreal.Vector(anchor.x - camera_forward.x * 125.0, anchor.y - camera_forward.y * 125.0, anchor.z - camera_forward.z * 125.0)
    card = unreal.EditorLevelLibrary.spawn_actor_from_class(unreal.StaticMeshActor, location, card_rotation)
    card.set_actor_label(station["label"])
    card.static_mesh_component.set_static_mesh(plane)
    card.static_mesh_component.set_material(0, imported[station["id"]]["material"])
    card.static_mesh_component.set_collision_enabled(unreal.CollisionEnabled.NO_COLLISION)
    card.static_mesh_component.set_editor_property("cast_shadow", False)
    card.set_actor_scale3d(unreal.Vector(*station["scale"]))
    if dot(unreal.MathLibrary.get_up_vector(card_rotation), camera_forward) < 0.999:
        raise RuntimeError(f"station sprite does not face camera: {station['id']}")
    mounted.append({
        "id": station["id"],
        "label": station["label"],
        "source_sha256": digest(imported[station["id"]]["source"]),
        "location_cm": [round(location.x, 2), round(location.y, 2), round(location.z, 2)],
        "scale": station["scale"],
    })

if not unreal.EditorLoadingAndSavingUtils.save_current_level():
    raise RuntimeError("complete press train did not save")
unreal.EditorLoadingAndSavingUtils.save_dirty_packages(True, True)
after = {str(path): digest(path) for path in PROTECTED}
if after != before:
    raise RuntimeError("protected maps changed during train installation")

RECEIPT.parent.mkdir(parents=True, exist_ok=True)
RECEIPT.write_text(json.dumps({
    "status": "PASS__2126_FOUR_STATION_PRESS_TRAIN_INSTALLED",
    "map": MAP,
    "station_pitch_cm": 3100.0,
    "flow_axis": "+Y",
    "mounted_stations": mounted,
    "removed_roof_and_column_actor_count": len(removed_obstructions),
    "removed_roof_and_column_labels": sorted(removed_obstructions),
    "camera_contract": {"pitch": -60.0, "yaw": 57.63},
    "protected_sha256_before": before,
    "protected_sha256_after": after,
}, indent=2, sort_keys=True) + "\n", encoding="utf-8")
unreal.log(f"PRESSSHOP_2126_COMPLETE_PRESS_TRAIN_PASS receipt={RECEIPT}")
unreal.SystemLibrary.quit_editor()
