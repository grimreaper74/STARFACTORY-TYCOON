"""Install one registered four-station sprite master in the isolated 2126 map."""
import hashlib
import json
import math
from pathlib import Path
import unreal

PROJECT = Path(r"C:\Users\greg_\Projects\LineBossCarFactory_Unreal 5.8")
MAP = "/Game/LineBoss/Candidates/PressShop/PressShop2126_FullHall_v001/Maps/LB_PressShop_2126_FullHall_v001"
ROOT = "/Game/LineBoss/Candidates/PressShop/PressShop2126_FullHall_v001/Sprites"
SOURCE = PROJECT / "SourceArt" / "PressShop2126" / "Sprites" / "T_CA_MW_2126_RegisteredFourStationPressTrain_v001.png"
SOURCE_SHA256 = "7f54dd1f091ce3a5c54a7809a49fae1f3cebdf80e6068f95d91198282abcff35"
TEXTURE_NAME = "T_CA_MW_2126_RegisteredFourStationPressTrain_v001"
MATERIAL_NAME = "M_CA_MW_2126_RegisteredFourStationPressTrain_UnlitMasked_v001"
TEXTURE_PATH = ROOT + "/" + TEXTURE_NAME
MATERIAL_PATH = ROOT + "/" + MATERIAL_NAME
MASTER_LABEL = "2126 PRESS | registered continuous S01-S04 master sprite"
CAMERA_LABEL = "CAM | 2126 full hall fixed game view"
OUT = PROJECT / "Saved" / "Audits" / "PressShop2126" / "registered_master_train_v001_receipt.json"
TAG = unreal.Name("LB.PressShop.2126.RegisteredMasterTrain.v001")
PROTECTED = {
    PROJECT / "Content" / "LineBoss" / "Maps" / "LB_PressShop_BuilderAuthorityCandidate_v438.umap": "5029c9d827d9a1d72c12f27ee757c9bc1e47febd5006ce6d7ba319aad2e7fec8",
    PROJECT / "Content" / "LineBoss" / "Candidates" / "PressShop" / "PressShop2126_v002" / "Maps" / "LB_PressShop_2126_Steam_v002.umap": "cc09cf46d33e8a562d97f5a3bc35a5b42c9582d8e4650cf315694ebf340e4aa0",
}
OLD_STATIONS = (
    "2126 PRESS | S01 autonomous deep-draw servo press",
    "2126 PRESS | S02 autonomous redraw calibration press",
    "2126 PRESS | S03 autonomous trim pierce press",
    "2126 PRESS | S04 autonomous flange final-form press",
)
LEGACY_SERVICE_PROPS = (
    "BP_LB_CR01_CleaningAMR_v0640",
    "BP_LB_CR01_CleaningAMR_v0641",
    "LB-CR01-01",
    "LB-CR01-02",
    "LB-DOCK-CR01-01",
    "LB-DOCK-CR01-02",
)


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest().lower()


def dot(a, b):
    return a.x * b.x + a.y * b.y + a.z * b.z


def unit(vector):
    length = math.sqrt(dot(vector, vector))
    return unreal.Vector(vector.x / length, vector.y / length, vector.z / length)


def projected(vector, normal):
    return unit(unreal.Vector(
        vector.x - normal.x * dot(vector, normal),
        vector.y - normal.y * dot(vector, normal),
        vector.z - normal.z * dot(vector, normal),
    ))


before = {str(path): digest(path) for path in PROTECTED}
for path, expected in PROTECTED.items():
    if before[str(path)] != expected:
        raise RuntimeError("protected authority changed: " + str(path))
if not SOURCE.is_file() or digest(SOURCE) != SOURCE_SHA256:
    raise RuntimeError("registered master sprite source missing or changed")
if OUT.exists() or unreal.EditorAssetLibrary.does_asset_exist(TEXTURE_PATH) or unreal.EditorAssetLibrary.does_asset_exist(MATERIAL_PATH):
    raise RuntimeError("registered master pass already exists; refusing overwrite")

task = unreal.AssetImportTask()
task.set_editor_properties({
    "filename": str(SOURCE),
    "destination_path": ROOT,
    "destination_name": TEXTURE_NAME,
    "automated": True,
    "replace_existing": False,
    "save": True,
})
unreal.AssetToolsHelpers.get_asset_tools().import_asset_tasks([task])
paths = list(task.get_editor_property("imported_object_paths") or [])
if len(paths) != 1:
    raise RuntimeError("registered master texture import failed: " + repr(paths))
texture = unreal.load_asset(paths[0])
if not isinstance(texture, unreal.Texture2D):
    raise RuntimeError("registered master PNG did not import as Texture2D")
texture.set_editor_properties({
    "srgb": True,
    "compression_settings": unreal.TextureCompressionSettings.TC_DEFAULT,
    "never_stream": True,
})
unreal.EditorAssetLibrary.save_loaded_asset(texture, only_if_is_dirty=False)

material = unreal.AssetToolsHelpers.get_asset_tools().create_asset(
    MATERIAL_NAME, ROOT, unreal.Material, unreal.MaterialFactoryNew())
if not isinstance(material, unreal.Material):
    raise RuntimeError("registered master material creation failed")
material.set_editor_properties({
    "blend_mode": unreal.BlendMode.BLEND_MASKED,
    "shading_model": unreal.MaterialShadingModel.MSM_UNLIT,
    "two_sided": True,
    "opacity_mask_clip_value": 0.50,
})
mel = unreal.MaterialEditingLibrary
sample = mel.create_material_expression(material, unreal.MaterialExpressionTextureSample, -520, 0)
sample.set_editor_properties({"texture": texture, "sampler_type": unreal.MaterialSamplerType.SAMPLERTYPE_COLOR})
gain = mel.create_material_expression(material, unreal.MaterialExpressionConstant, -520, 180)
gain.set_editor_property("r", 0.55)
multiply = mel.create_material_expression(material, unreal.MaterialExpressionMultiply, -250, 0)
if not mel.connect_material_expressions(sample, "RGB", multiply, "A"):
    raise RuntimeError("registered master colour connection failed")
if not mel.connect_material_expressions(gain, "", multiply, "B"):
    raise RuntimeError("registered master gain connection failed")
if not mel.connect_material_property(multiply, "", unreal.MaterialProperty.MP_EMISSIVE_COLOR):
    raise RuntimeError("registered master emissive connection failed")
if not mel.connect_material_property(sample, "A", unreal.MaterialProperty.MP_OPACITY_MASK):
    raise RuntimeError("registered master alpha connection failed")
mel.recompile_material(material)
unreal.EditorAssetLibrary.save_loaded_asset(material, only_if_is_dirty=False)

if not unreal.EditorLoadingAndSavingUtils.load_map(MAP):
    raise RuntimeError("could not load isolated FullHall candidate")
actors = {actor.get_actor_label(): actor for actor in unreal.EditorLevelLibrary.get_all_level_actors()}
if MASTER_LABEL in actors or any(TAG in actor.tags for actor in actors.values()):
    raise RuntimeError("registered master actor already exists")
camera = actors.get(CAMERA_LABEL)
if not isinstance(camera, unreal.CameraActor):
    raise RuntimeError("fixed game camera missing")
camera_rotation = camera.get_actor_rotation()
if abs(camera_rotation.pitch + 60.0) > 0.2 or abs(camera_rotation.yaw - 57.63) > 0.2:
    raise RuntimeError("fixed sprite-camera contract changed")

hidden_station_cards = []
for label in OLD_STATIONS:
    actor = actors.get(label)
    if not isinstance(actor, unreal.StaticMeshActor):
        raise RuntimeError("old station reference card missing: " + label)
    actor.static_mesh_component.set_visibility(False, True)
    actor.set_actor_hidden_in_game(True)
    actor.tags = list(actor.tags) + [TAG, unreal.Name("LB.SupersededVisual.Hidden")]
    hidden_station_cards.append(label)

hidden_service_props = []
for label in LEGACY_SERVICE_PROPS:
    actor = actors.get(label)
    if actor is None:
        raise RuntimeError("audited service-lane prop missing: " + label)
    actor.set_actor_hidden_in_game(True)
    actor.set_is_temporarily_hidden_in_editor(True)
    for component in actor.get_components_by_class(unreal.PrimitiveComponent):
        component.set_visibility(False, True)
        component.set_collision_enabled(unreal.CollisionEnabled.NO_COLLISION)
    actor.tags = list(actor.tags) + [TAG, unreal.Name("LB.LegacyServiceProp.Hidden")]
    hidden_service_props.append(label)

# The master is registered to the same +Y flow centre and mean station height.
camera_forward = unreal.MathLibrary.get_forward_vector(camera_rotation)
flow_axis = projected(unreal.Vector(0.0, 1.0, 0.0), camera_forward)
card_rotation = unreal.MathLibrary.make_rot_from_zx(camera_forward, flow_axis)
anchor = unreal.Vector(-3500.0, 2550.0, 560.0)
location = unreal.Vector(
    anchor.x - camera_forward.x * 125.0,
    anchor.y - camera_forward.y * 125.0,
    anchor.z - camera_forward.z * 125.0,
)
plane = unreal.load_asset("/Engine/BasicShapes/Plane.Plane")
master = unreal.EditorLevelLibrary.spawn_actor_from_class(unreal.StaticMeshActor, location, card_rotation)
if not isinstance(master, unreal.StaticMeshActor):
    raise RuntimeError("could not spawn registered master card")
master.set_actor_label(MASTER_LABEL)
master.tags = [TAG, unreal.Name("LB.PressShop.2126.PressTrain"), unreal.Name("LB.Role.RegisteredSpriteMaster")]
component = master.static_mesh_component
component.set_static_mesh(plane)
component.set_material(0, material)
component.set_collision_profile_name("NoCollision")
component.set_collision_enabled(unreal.CollisionEnabled.NO_COLLISION)
component.set_editor_property("cast_shadow", False)
master.set_actor_scale3d(unreal.Vector(80.0, 51.43, 1.0))
if dot(unreal.MathLibrary.get_up_vector(card_rotation), camera_forward) < 0.999:
    raise RuntimeError("registered master does not face the fixed game camera")

# Correct the three detailed pallet cards to visual-only while the map is open.
pallet_collision = []
for slot in ("A", "B", "C"):
    label = f"2126 OUTBOUND | detailed finished-panel hover pallet sprite {slot}"
    actor = actors.get(label)
    if not isinstance(actor, unreal.StaticMeshActor):
        raise RuntimeError("detailed pallet card missing: " + label)
    card_component = actor.static_mesh_component
    before_state = str(card_component.get_collision_enabled())
    card_component.set_collision_profile_name("NoCollision")
    card_component.set_collision_enabled(unreal.CollisionEnabled.NO_COLLISION)
    after_state = str(card_component.get_collision_enabled())
    if "NO_COLLISION" not in after_state.upper():
        raise RuntimeError("pallet card collision did not disable: " + label)
    pallet_collision.append({"label": label, "before": before_state, "after": after_state})

if not unreal.EditorLoadingAndSavingUtils.save_current_level():
    raise RuntimeError("registered master pass did not save")
unreal.EditorLoadingAndSavingUtils.save_dirty_packages(True, True)
after = {str(path): digest(path) for path in PROTECTED}
if after != before:
    raise RuntimeError("protected maps changed during registered master installation")

OUT.parent.mkdir(parents=True, exist_ok=True)
OUT.write_text(json.dumps({
    "status": "PASS__REGISTERED_CONTINUOUS_S01_S04_MASTER_INSTALLED",
    "map": MAP,
    "source_png": str(SOURCE),
    "source_sha256": digest(SOURCE),
    "source_dimensions_px": [1792, 1152],
    "source_true_alpha": True,
    "texture": texture.get_path_name(),
    "material": material.get_path_name(),
    "master_actor": MASTER_LABEL,
    "master_anchor_cm": [anchor.x, anchor.y, anchor.z],
    "master_location_cm": [location.x, location.y, location.z],
    "master_scale": [80.0, 51.43, 1.0],
    "flow_axis": "+Y",
    "hidden_superseded_station_cards": hidden_station_cards,
    "hidden_legacy_service_props": hidden_service_props,
    "pallet_visual_collision": pallet_collision,
    "native_station_collision_proxies_preserved": 4,
    "native_transfer_shuttles_preserved": 3,
    "protected_sha256_before": before,
    "protected_sha256_after": after,
}, indent=2, sort_keys=True) + "\n", encoding="utf-8")
unreal.log("PRESSSHOP_2126_REGISTERED_MASTER_PASS receipt=" + str(OUT))
unreal.SystemLibrary.quit_editor()
