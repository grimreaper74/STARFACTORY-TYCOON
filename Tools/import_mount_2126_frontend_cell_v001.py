"""Import and mount the coherent 2126 decoiler/straightener/servo-feed front-end cell."""
import hashlib
import json
import math
from pathlib import Path
import unreal

PROJECT = Path(r"C:\Users\greg_\Projects\LineBossCarFactory_Unreal 5.8")
MAP = "/Game/LineBoss/Candidates/PressShop/PressShop2126_FullHall_v001/Maps/LB_PressShop_2126_FullHall_v001"
ROOT = "/Game/LineBoss/Candidates/PressShop/PressShop2126_FullHall_v001/Sprites"
SOURCE = PROJECT / "SourceArt" / "PressShop2126" / "Sprites" / "T_CA_MW_2126_DecoilStraightenServoCell_v001.png"
TEXTURE_NAME = "T_CA_MW_2126_DecoilStraightenServoCell_v001"
MATERIAL_NAME = "M_CA_MW_2126_DecoilStraightenServoCell_UnlitMasked_v001"
ACTOR_LABEL = "2126 FRONT END | autonomous decoiler straightener and servo feed"
COIL_LABEL = "2126 FRONT END | active feed coil"
RECEIPT = PROJECT / "Saved" / "Audits" / "PressShop2126" / "import_mount_frontend_cell_v001_receipt.json"
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
for path, expected in PROTECTED.items():
    if before[str(path)] != expected:
        raise RuntimeError(f"protected map missing or changed: {path}")
if not SOURCE.is_file():
    raise RuntimeError("front-end source sprite missing")

texture_path = ROOT + "/" + TEXTURE_NAME
material_path = ROOT + "/" + MATERIAL_NAME
if unreal.EditorAssetLibrary.does_asset_exist(texture_path) or unreal.EditorAssetLibrary.does_asset_exist(material_path):
    raise RuntimeError("refusing to overwrite existing front-end sprite assets")
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
    raise RuntimeError(f"front-end texture import failed: {paths}")
texture = unreal.load_asset(paths[0])
if not isinstance(texture, unreal.Texture2D):
    raise RuntimeError("front-end PNG did not import as Texture2D")
texture.set_editor_properties({"srgb": True, "compression_settings": unreal.TextureCompressionSettings.TC_DEFAULT, "never_stream": True})
unreal.EditorAssetLibrary.save_loaded_asset(texture, only_if_is_dirty=False)

tools = unreal.AssetToolsHelpers.get_asset_tools()
material = tools.create_asset(MATERIAL_NAME, ROOT, unreal.Material, unreal.MaterialFactoryNew())
if not isinstance(material, unreal.Material):
    raise RuntimeError("could not create front-end material")
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
    raise RuntimeError("could not connect front-end colour")
if not mel.connect_material_property(sample, "A", unreal.MaterialProperty.MP_OPACITY_MASK):
    raise RuntimeError("could not connect front-end alpha")
mel.recompile_material(material)
unreal.EditorAssetLibrary.save_loaded_asset(material, only_if_is_dirty=False)

if not unreal.EditorLoadingAndSavingUtils.load_map(MAP):
    raise RuntimeError("could not load isolated 2126 candidate")
actors = list(unreal.EditorLevelLibrary.get_all_level_actors())
labels = {a.get_actor_label() for a in actors}
if ACTOR_LABEL in labels or COIL_LABEL in labels:
    raise RuntimeError("front-end cell or active coil already mounted")
camera = next((a for a in actors if a.get_actor_label() == "CAM | 2126 full hall fixed game view"), None)
if not isinstance(camera, unreal.CameraActor):
    raise RuntimeError("fixed game camera missing")
rotation = camera.get_actor_rotation()
if abs(rotation.pitch + 60.0) > 0.2 or abs(rotation.yaw - 57.63) > 0.2:
    raise RuntimeError("fixed game camera basis changed")
camera_forward = unreal.MathLibrary.get_forward_vector(rotation)
flow_axis = projected(unreal.Vector(0.0, 1.0, 0.0), camera_forward)
card_rotation = unreal.MathLibrary.make_rot_from_zx(camera_forward, flow_axis)
anchor = unreal.Vector(-3500.0, -2000.0, 330.0)
location = unreal.Vector(anchor.x - camera_forward.x * 105.0, anchor.y - camera_forward.y * 105.0, anchor.z - camera_forward.z * 105.0)
plane = unreal.load_asset("/Engine/BasicShapes/Plane.Plane")
card = unreal.EditorLevelLibrary.spawn_actor_from_class(unreal.StaticMeshActor, location, card_rotation)
card.set_actor_label(ACTOR_LABEL)
card.static_mesh_component.set_static_mesh(plane)
card.static_mesh_component.set_material(0, material)
card.static_mesh_component.set_collision_enabled(unreal.CollisionEnabled.NO_COLLISION)
card.static_mesh_component.set_editor_property("cast_shadow", False)
card.set_actor_scale3d(unreal.Vector(24.0, 16.0, 1.0))
if dot(unreal.MathLibrary.get_up_vector(card_rotation), camera_forward) < 0.999:
    raise RuntimeError("front-end sprite does not face fixed camera")

coil_source = next((a for a in actors if isinstance(a, unreal.StaticMeshActor) and "packagedmastercoil" in a.get_actor_label().lower()), None)
if coil_source is None or coil_source.static_mesh_component.static_mesh is None:
    coil_source = next((a for a in actors if isinstance(a, unreal.StaticMeshActor) and a.get_actor_label() == "2126 COIL | verification cell active load"), None)
if coil_source is None or coil_source.static_mesh_component.static_mesh is None:
    raise RuntimeError("approved master-coil mesh exemplar missing")
coil = unreal.EditorLevelLibrary.spawn_actor_from_class(unreal.StaticMeshActor, unreal.Vector(-3500.0, -3050.0, 175.0), coil_source.get_actor_rotation())
coil.set_actor_label(COIL_LABEL)
coil.static_mesh_component.set_static_mesh(coil_source.static_mesh_component.static_mesh)
coil.set_actor_scale3d(coil_source.get_actor_scale3d())
coil.static_mesh_component.set_collision_enabled(unreal.CollisionEnabled.QUERY_ONLY)

if not unreal.EditorLoadingAndSavingUtils.save_current_level():
    raise RuntimeError("front-end integration did not save")
unreal.EditorLoadingAndSavingUtils.save_dirty_packages(True, True)
after = {str(path): digest(path) for path in PROTECTED}
if after != before:
    raise RuntimeError("protected maps changed during front-end integration")

RECEIPT.parent.mkdir(parents=True, exist_ok=True)
RECEIPT.write_text(json.dumps({
    "status": "PASS__2126_FRONTEND_CELL_MOUNTED",
    "map": MAP,
    "source_png": str(SOURCE),
    "source_sha256": digest(SOURCE),
    "texture": texture.get_path_name(),
    "material": material.get_path_name(),
    "actor_label": ACTOR_LABEL,
    "actor_location_cm": [round(location.x, 2), round(location.y, 2), round(location.z, 2)],
    "active_coil_label": COIL_LABEL,
    "active_coil_location_cm": [-3500.0, -3050.0, 175.0],
    "camera_contract": {"pitch": -60.0, "yaw": 57.63},
    "protected_sha256_before": before,
    "protected_sha256_after": after,
}, indent=2, sort_keys=True) + "\n", encoding="utf-8")
unreal.log(f"PRESSSHOP_2126_FRONTEND_MOUNT_PASS receipt={RECEIPT}")
unreal.SystemLibrary.quit_editor()
