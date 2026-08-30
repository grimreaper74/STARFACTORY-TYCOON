"""Import and mount the first 2126 logistics sprite with separate approved coils."""
import hashlib
import json
import math
from pathlib import Path
import unreal

PROJECT = Path(r"C:\Users\greg_\Projects\LineBossCarFactory_Unreal 5.8")
MAP = "/Game/LineBoss/Candidates/PressShop/PressShop2126_FullHall_v001/Maps/LB_PressShop_2126_FullHall_v001"
MAP_FILE = PROJECT / "Content" / "LineBoss" / "Candidates" / "PressShop" / "PressShop2126_FullHall_v001" / "Maps" / "LB_PressShop_2126_FullHall_v001.umap"
EXPECTED_MAP_SHA256 = "f914cecde394da62b1734374a7dfb5d05babbf7b6bd4d33be980d271b9541cef"
SOURCE = PROJECT / "SourceArt" / "PressShop2126" / "Sprites" / "T_CA_MW_2126_AutonomousCoilCarrier_v001.png"
ROOT = "/Game/LineBoss/Candidates/PressShop/PressShop2126_FullHall_v001/Sprites"
TEXTURE_PATH = ROOT + "/T_CA_MW_2126_AutonomousCoilCarrier_v001"
MATERIAL_PATH = ROOT + "/M_CA_MW_2126_AutonomousCoilCarrier_UnlitMasked_v001"
RECEIPT = PROJECT / "Saved" / "Audits" / "PressShop2126" / "import_mount_coil_carrier_v001_receipt.json"
PROTECTED = {
    PROJECT / "Content" / "LineBoss" / "Maps" / "LB_PressShop_BuilderAuthorityCandidate_v438.umap": "5029c9d827d9a1d72c12f27ee757c9bc1e47febd5006ce6d7ba319aad2e7fec8",
    PROJECT / "Content" / "LineBoss" / "Candidates" / "PressShop" / "PressShop2126_v002" / "Maps" / "LB_PressShop_2126_Steam_v002.umap": "cc09cf46d33e8a562d97f5a3bc35a5b42c9582d8e4650cf315694ebf340e4aa0",
}


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
if digest(MAP_FILE) != EXPECTED_MAP_SHA256:
    raise RuntimeError("full-hall candidate changed before coil-carrier mount")
if not SOURCE.is_file():
    raise RuntimeError("coil-carrier source PNG missing")

tools = unreal.AssetToolsHelpers.get_asset_tools()
if unreal.EditorAssetLibrary.does_asset_exist(TEXTURE_PATH):
    raise RuntimeError("refusing to overwrite existing coil-carrier texture")
task = unreal.AssetImportTask()
task.set_editor_properties({"filename": str(SOURCE), "destination_path": ROOT, "destination_name": "T_CA_MW_2126_AutonomousCoilCarrier_v001", "automated": True, "replace_existing": False, "save": True})
tools.import_asset_tasks([task])
paths = list(task.get_editor_property("imported_object_paths") or [])
if len(paths) != 1:
    raise RuntimeError("coil-carrier texture import failed: {}".format(paths))
texture = unreal.load_asset(paths[0])
if not isinstance(texture, unreal.Texture2D):
    raise RuntimeError("coil-carrier PNG did not import as Texture2D")
texture.set_editor_properties({"srgb": True, "compression_settings": unreal.TextureCompressionSettings.TC_DEFAULT, "never_stream": True})
unreal.EditorAssetLibrary.save_loaded_asset(texture, only_if_is_dirty=False)

material = tools.create_asset("M_CA_MW_2126_AutonomousCoilCarrier_UnlitMasked_v001", ROOT, unreal.Material, unreal.MaterialFactoryNew())
if not isinstance(material, unreal.Material):
    raise RuntimeError("could not create masked coil-carrier material")
mel = unreal.MaterialEditingLibrary
material.set_editor_properties({"blend_mode": unreal.BlendMode.BLEND_MASKED, "shading_model": unreal.MaterialShadingModel.MSM_UNLIT, "two_sided": True, "opacity_mask_clip_value": 0.025})
sample = mel.create_material_expression(material, unreal.MaterialExpressionTextureSample, -420, 0)
sample.set_editor_properties({"texture": texture, "sampler_type": unreal.MaterialSamplerType.SAMPLERTYPE_COLOR})
if not mel.connect_material_property(sample, "RGB", unreal.MaterialProperty.MP_EMISSIVE_COLOR):
    raise RuntimeError("could not connect carrier colour")
if not mel.connect_material_property(sample, "A", unreal.MaterialProperty.MP_OPACITY_MASK):
    raise RuntimeError("could not connect carrier alpha")
mel.recompile_material(material)
unreal.EditorAssetLibrary.save_loaded_asset(material, only_if_is_dirty=False)

if not unreal.EditorLoadingAndSavingUtils.load_map(MAP):
    raise RuntimeError("could not load full-hall candidate")
actors = list(unreal.EditorLevelLibrary.get_all_level_actors())
if any(a.get_actor_label() == "2126 LOG | autonomous coil delivery carrier" for a in actors):
    raise RuntimeError("coil carrier already mounted")
camera = next((a for a in actors if a.get_actor_label() == "CAM | 2126 full hall fixed game view"), None)
if not isinstance(camera, unreal.CameraActor):
    raise RuntimeError("fixed game camera missing")
rotation = camera.get_actor_rotation()
if abs(rotation.pitch + 60.0) > 0.2 or abs(rotation.yaw - 57.63) > 0.2:
    raise RuntimeError("fixed game camera basis changed")
camera_forward = unreal.MathLibrary.get_forward_vector(rotation)
delivery_axis = projected(unreal.Vector(0.0, 1.0, 0.0), camera_forward)
card_rotation = unreal.MathLibrary.make_rot_from_zx(camera_forward, delivery_axis)
anchor = unreal.Vector(-9100.0, -2350.0, 260.0)
location = unreal.Vector(anchor.x - camera_forward.x * 90.0, anchor.y - camera_forward.y * 90.0, anchor.z - camera_forward.z * 90.0)
plane = unreal.load_asset("/Engine/BasicShapes/Plane.Plane")
card = unreal.EditorLevelLibrary.spawn_actor_from_class(unreal.StaticMeshActor, location, card_rotation)
card.set_actor_label("2126 LOG | autonomous coil delivery carrier")
card.static_mesh_component.set_static_mesh(plane)
card.static_mesh_component.set_material(0, material)
card.static_mesh_component.set_collision_enabled(unreal.CollisionEnabled.NO_COLLISION)
card.static_mesh_component.set_editor_property("cast_shadow", False)
card.set_actor_scale3d(unreal.Vector(24.0, 16.0, 1.0))
if dot(unreal.MathLibrary.get_up_vector(card_rotation), camera_forward) < 0.999:
    raise RuntimeError("carrier card does not face fixed camera")

coil_source = next((a for a in actors if isinstance(a, unreal.StaticMeshActor) and "packagedmastercoil" in a.get_actor_label().lower()), None)
if coil_source is None or coil_source.static_mesh_component.static_mesh is None:
    raise RuntimeError("approved packaged master-coil exemplar missing")
coil_mesh = coil_source.static_mesh_component.static_mesh
coil_rotation = coil_source.get_actor_rotation()
coil_scale = coil_source.get_actor_scale3d()
coil_records = []
for index, y in enumerate((-4150.0, -2950.0, -1750.0, -550.0), 1):
    coil = unreal.EditorLevelLibrary.spawn_actor_from_class(unreal.StaticMeshActor, unreal.Vector(-9100.0, y, 175.0), coil_rotation)
    coil.set_actor_label("2126 LOG | delivery coil {:02d} | approved packaged master coil".format(index))
    coil.static_mesh_component.set_static_mesh(coil_mesh)
    coil.set_actor_scale3d(coil_scale)
    coil.static_mesh_component.set_collision_enabled(unreal.CollisionEnabled.QUERY_ONLY)
    coil_records.append({"label": coil.get_actor_label(), "location_cm": [-9100.0, y, 175.0]})

if not unreal.EditorLoadingAndSavingUtils.save_current_level():
    raise RuntimeError("coil-carrier integration did not save")
after = {str(path): digest(path) for path in PROTECTED}
if after != before:
    raise RuntimeError("protected maps changed during coil-carrier integration")
RECEIPT.parent.mkdir(parents=True, exist_ok=True)
RECEIPT.write_text(json.dumps({
    "status": "PASS__2126_COIL_CARRIER_AND_SEPARATE_APPROVED_COILS_MOUNTED",
    "map": MAP,
    "map_sha256_after": digest(MAP_FILE),
    "source_png": str(SOURCE),
    "source_sha256": digest(SOURCE),
    "texture": texture.get_path_name(),
    "material": material.get_path_name(),
    "carrier_location_cm": [round(location.x, 2), round(location.y, 2), round(location.z, 2)],
    "carrier_width_cm": 2400.0,
    "coil_mesh_reused": coil_mesh.get_path_name(),
    "separate_movable_coils": coil_records,
    "camera_contract": {"pitch": -60.0, "yaw": 57.63},
    "protected_sha256_before": before,
    "protected_sha256_after": after,
}, indent=2, sort_keys=True) + "\n", encoding="utf-8")
unreal.log("PRESSSHOP_2126_COIL_CARRIER_MOUNT_PASS {}".format(RECEIPT))
unreal.SystemLibrary.quit_editor()
