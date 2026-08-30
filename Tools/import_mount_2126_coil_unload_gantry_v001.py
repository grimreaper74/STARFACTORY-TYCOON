"""Import the 2126 unload gantry sprite and pose one approved coil mid-transfer."""
import hashlib
import json
import math
from pathlib import Path
import unreal

PROJECT = Path(r"C:\Users\greg_\Projects\LineBossCarFactory_Unreal 5.8")
MAP = "/Game/LineBoss/Candidates/PressShop/PressShop2126_FullHall_v001/Maps/LB_PressShop_2126_FullHall_v001"
MAP_FILE = PROJECT / "Content" / "LineBoss" / "Candidates" / "PressShop" / "PressShop2126_FullHall_v001" / "Maps" / "LB_PressShop_2126_FullHall_v001.umap"
EXPECTED_MAP_SHA256 = "c365a3961a9da8a0cb5899c7cb93f1d043981e69067dd3e80e1982ed718dfc13"
SOURCE = PROJECT / "SourceArt" / "PressShop2126" / "Sprites" / "T_CA_MW_2126_AutonomousCoilUnloadGantry_v001.png"
ROOT = "/Game/LineBoss/Candidates/PressShop/PressShop2126_FullHall_v001/Sprites"
TEXTURE_PATH = ROOT + "/T_CA_MW_2126_AutonomousCoilUnloadGantry_v001"
RECEIPT = PROJECT / "Saved" / "Audits" / "PressShop2126" / "import_mount_coil_unload_gantry_v001_receipt.json"
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
    raise RuntimeError("candidate changed before unload-gantry mount")
if not SOURCE.is_file() or unreal.EditorAssetLibrary.does_asset_exist(TEXTURE_PATH):
    raise RuntimeError("gantry source missing or destination already exists")

tools = unreal.AssetToolsHelpers.get_asset_tools()
task = unreal.AssetImportTask()
task.set_editor_properties({"filename": str(SOURCE), "destination_path": ROOT, "destination_name": "T_CA_MW_2126_AutonomousCoilUnloadGantry_v001", "automated": True, "replace_existing": False, "save": True})
tools.import_asset_tasks([task])
paths = list(task.get_editor_property("imported_object_paths") or [])
if len(paths) != 1:
    raise RuntimeError("gantry texture import failed")
texture = unreal.load_asset(paths[0])
texture.set_editor_properties({"srgb": True, "compression_settings": unreal.TextureCompressionSettings.TC_DEFAULT, "never_stream": True})
unreal.EditorAssetLibrary.save_loaded_asset(texture, only_if_is_dirty=False)

material = tools.create_asset("M_CA_MW_2126_AutonomousCoilUnloadGantry_UnlitMasked_v001", ROOT, unreal.Material, unreal.MaterialFactoryNew())
material.set_editor_properties({"blend_mode": unreal.BlendMode.BLEND_MASKED, "shading_model": unreal.MaterialShadingModel.MSM_UNLIT, "two_sided": True, "opacity_mask_clip_value": 0.025})
mel = unreal.MaterialEditingLibrary
sample = mel.create_material_expression(material, unreal.MaterialExpressionTextureSample, -420, 0)
sample.set_editor_properties({"texture": texture, "sampler_type": unreal.MaterialSamplerType.SAMPLERTYPE_COLOR})
mel.connect_material_property(sample, "RGB", unreal.MaterialProperty.MP_EMISSIVE_COLOR)
mel.connect_material_property(sample, "A", unreal.MaterialProperty.MP_OPACITY_MASK)
mel.recompile_material(material)
unreal.EditorAssetLibrary.save_loaded_asset(material, only_if_is_dirty=False)

if not unreal.EditorLoadingAndSavingUtils.load_map(MAP):
    raise RuntimeError("could not load full-hall candidate")
actors = list(unreal.EditorLevelLibrary.get_all_level_actors())
camera = next((a for a in actors if a.get_actor_label() == "CAM | 2126 full hall fixed game view"), None)
coil = next((a for a in actors if a.get_actor_label() == "2126 LOG | delivery coil 01 | approved packaged master coil"), None)
if not isinstance(camera, unreal.CameraActor) or not isinstance(coil, unreal.StaticMeshActor):
    raise RuntimeError("fixed camera or delivery coil missing")
camera_forward = unreal.MathLibrary.get_forward_vector(camera.get_actor_rotation())
gantry_axis = projected(unreal.Vector(0.0, 1.0, 0.0), camera_forward)
card_rotation = unreal.MathLibrary.make_rot_from_zx(camera_forward, gantry_axis)
anchor = unreal.Vector(-8500.0, -2350.0, 900.0)
location = unreal.Vector(anchor.x - camera_forward.x * 170.0, anchor.y - camera_forward.y * 170.0, anchor.z - camera_forward.z * 170.0)
card = unreal.EditorLevelLibrary.spawn_actor_from_class(unreal.StaticMeshActor, location, card_rotation)
card.set_actor_label("2126 LOG | autonomous coil unload gantry")
card.static_mesh_component.set_static_mesh(unreal.load_asset("/Engine/BasicShapes/Plane.Plane"))
card.static_mesh_component.set_material(0, material)
card.static_mesh_component.set_collision_enabled(unreal.CollisionEnabled.NO_COLLISION)
card.static_mesh_component.set_editor_property("cast_shadow", False)
card.set_actor_scale3d(unreal.Vector(28.0, 18.667, 1.0))
if dot(unreal.MathLibrary.get_up_vector(card_rotation), camera_forward) < 0.999:
    raise RuntimeError("gantry card does not face fixed camera")

coil.set_actor_location(unreal.Vector(-8200.0, -2350.0, 720.0), False, False)
coil.set_actor_label("2126 LOG | coil 01 mid-transfer under autonomous gantry")
if not unreal.EditorLoadingAndSavingUtils.save_current_level():
    raise RuntimeError("unload-gantry integration did not save")
after = {str(path): digest(path) for path in PROTECTED}
if after != before:
    raise RuntimeError("protected maps changed during unload-gantry integration")
RECEIPT.parent.mkdir(parents=True, exist_ok=True)
RECEIPT.write_text(json.dumps({
    "status": "PASS__2126_AUTONOMOUS_UNLOAD_GANTRY_MOUNTED_WITH_COIL_MID_TRANSFER",
    "map_sha256_after": digest(MAP_FILE),
    "source_png": str(SOURCE),
    "source_sha256": digest(SOURCE),
    "gantry_location_cm": [round(location.x, 2), round(location.y, 2), round(location.z, 2)],
    "gantry_width_cm": 2800.0,
    "mid_transfer_coil_location_cm": [-8200.0, -2350.0, 720.0],
    "protected_sha256_before": before,
    "protected_sha256_after": after,
}, indent=2, sort_keys=True) + "\n", encoding="utf-8")
unreal.log("PRESSSHOP_2126_UNLOAD_GANTRY_MOUNT_PASS {}".format(RECEIPT))
unreal.SystemLibrary.quit_editor()
