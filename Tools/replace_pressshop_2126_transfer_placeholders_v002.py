"""Replace transfer debug blocks with detailed shuttle sprites and lower rails to the floor."""
import hashlib
import json
import math
from pathlib import Path
import unreal

PROJECT = Path(r"C:\Users\greg_\Projects\LineBossCarFactory_Unreal 5.8")
MAP = "/Game/LineBoss/Candidates/PressShop/PressShop2126_FullHall_v001/Maps/LB_PressShop_2126_FullHall_v001"
ROOT = "/Game/LineBoss/Candidates/PressShop/PressShop2126_FullHall_v001/Sprites"
SOURCE = PROJECT / "SourceArt" / "PressShop2126" / "Sprites" / "T_CA_MW_2126_MagneticPanelTransferShuttle_v001.png"
TEXTURE_NAME = "T_CA_MW_2126_MagneticPanelTransferShuttle_v001"
MATERIAL_NAME = "M_CA_MW_2126_MagneticPanelTransferShuttle_UnlitMasked_v001"
TRANSFER_RAIL = "/Game/LineBoss/Candidates/PressTrains/Shared/Presentation_v003/SM_CA_MW_PT_TransferRail_v003"
RECEIPT = PROJECT / "Saved" / "Audits" / "PressShop2126" / "replace_transfer_placeholders_v002_receipt.json"
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
    raise RuntimeError("transfer shuttle source missing")

texture_path = ROOT + "/" + TEXTURE_NAME
material_path = ROOT + "/" + MATERIAL_NAME
if unreal.EditorAssetLibrary.does_asset_exist(texture_path) or unreal.EditorAssetLibrary.does_asset_exist(material_path):
    raise RuntimeError("refusing to overwrite existing shuttle sprite assets")
task = unreal.AssetImportTask()
task.set_editor_properties({"filename": str(SOURCE), "destination_path": ROOT, "destination_name": TEXTURE_NAME, "automated": True, "replace_existing": False, "save": True})
unreal.AssetToolsHelpers.get_asset_tools().import_asset_tasks([task])
paths = list(task.get_editor_property("imported_object_paths") or [])
if len(paths) != 1:
    raise RuntimeError(f"shuttle texture import failed: {paths}")
texture = unreal.load_asset(paths[0])
if not isinstance(texture, unreal.Texture2D):
    raise RuntimeError("shuttle PNG did not import as Texture2D")
texture.set_editor_properties({"srgb": True, "compression_settings": unreal.TextureCompressionSettings.TC_DEFAULT, "never_stream": True})
unreal.EditorAssetLibrary.save_loaded_asset(texture, only_if_is_dirty=False)

material = unreal.AssetToolsHelpers.get_asset_tools().create_asset(MATERIAL_NAME, ROOT, unreal.Material, unreal.MaterialFactoryNew())
if not isinstance(material, unreal.Material):
    raise RuntimeError("could not create shuttle material")
material.set_editor_properties({"blend_mode": unreal.BlendMode.BLEND_MASKED, "shading_model": unreal.MaterialShadingModel.MSM_UNLIT, "two_sided": True, "opacity_mask_clip_value": 0.025})
mel = unreal.MaterialEditingLibrary
sample = mel.create_material_expression(material, unreal.MaterialExpressionTextureSample, -420, 0)
sample.set_editor_properties({"texture": texture, "sampler_type": unreal.MaterialSamplerType.SAMPLERTYPE_COLOR})
if not mel.connect_material_property(sample, "RGB", unreal.MaterialProperty.MP_EMISSIVE_COLOR):
    raise RuntimeError("shuttle colour connection failed")
if not mel.connect_material_property(sample, "A", unreal.MaterialProperty.MP_OPACITY_MASK):
    raise RuntimeError("shuttle alpha connection failed")
mel.recompile_material(material)
unreal.EditorAssetLibrary.save_loaded_asset(material, only_if_is_dirty=False)

if not unreal.EditorLoadingAndSavingUtils.load_map(MAP):
    raise RuntimeError("could not load isolated 2126 candidate")
actors = list(unreal.EditorLevelLibrary.get_all_level_actors())
removed = []
for actor in actors:
    label = actor.get_actor_label()
    if label.startswith("2126 TRANSFER | continuous rail ") or label in (
        "2126 TRANSFER | magnetic shuttle 1",
        "2126 TRANSFER | magnetic shuttle 2",
        "2126 TRANSFER | magnetic shuttle 3",
    ):
        removed.append(label)
        unreal.EditorLevelLibrary.destroy_actor(actor)
if len(removed) != 5:
    raise RuntimeError(f"expected five transfer placeholders, found {sorted(removed)}")

camera = next((a for a in unreal.EditorLevelLibrary.get_all_level_actors() if a.get_actor_label() == "CAM | 2126 full hall fixed game view"), None)
if not isinstance(camera, unreal.CameraActor):
    raise RuntimeError("fixed camera missing")
rotation = camera.get_actor_rotation()
camera_forward = unreal.MathLibrary.get_forward_vector(rotation)
flow_axis = projected(unreal.Vector(0.0, 1.0, 0.0), camera_forward)
card_rotation = unreal.MathLibrary.make_rot_from_zx(camera_forward, flow_axis)

rail = unreal.load_asset(TRANSFER_RAIL)
plane = unreal.load_asset("/Engine/BasicShapes/Plane.Plane")
if not isinstance(rail, unreal.StaticMesh) or not isinstance(plane, unreal.StaticMesh):
    raise RuntimeError("rail or plane asset missing")
placed = []
for side, x in (("operator", -4250.0), ("service", -2750.0)):
    actor = unreal.EditorLevelLibrary.spawn_actor_from_class(unreal.StaticMeshActor, unreal.Vector(x, 2600.0, 24.0), unreal.Rotator(0.0, 0.0, 0.0))
    actor.set_actor_label(f"2126 TRANSFER | floor guide rail {side}")
    actor.static_mesh_component.set_static_mesh(rail)
    actor.set_actor_scale3d(unreal.Vector(1.0, 1.28, 1.0))
    actor.static_mesh_component.set_collision_enabled(unreal.CollisionEnabled.NO_COLLISION)
    placed.append(actor.get_actor_label())

for index, y in enumerate((800.0, 2600.0, 4400.0), start=1):
    anchor = unreal.Vector(-3500.0, y, 690.0)
    location = unreal.Vector(anchor.x - camera_forward.x * 145.0, anchor.y - camera_forward.y * 145.0, anchor.z - camera_forward.z * 145.0)
    card = unreal.EditorLevelLibrary.spawn_actor_from_class(unreal.StaticMeshActor, location, card_rotation)
    card.set_actor_label(f"2126 TRANSFER | magnetic panel shuttle sprite {index}")
    card.static_mesh_component.set_static_mesh(plane)
    card.static_mesh_component.set_material(0, material)
    card.static_mesh_component.set_collision_enabled(unreal.CollisionEnabled.NO_COLLISION)
    card.static_mesh_component.set_editor_property("cast_shadow", False)
    card.set_actor_scale3d(unreal.Vector(9.0, 6.0, 1.0))
    placed.append(card.get_actor_label())

if not unreal.EditorLoadingAndSavingUtils.save_current_level():
    raise RuntimeError("shuttle replacement did not save")
unreal.EditorLoadingAndSavingUtils.save_dirty_packages(True, True)
after = {str(path): digest(path) for path in PROTECTED}
if after != before:
    raise RuntimeError("protected maps changed during shuttle replacement")

RECEIPT.parent.mkdir(parents=True, exist_ok=True)
RECEIPT.write_text(json.dumps({
    "status": "PASS__2126_DETAILED_TRANSFER_SHUTTLES_REPLACED_DEBUG_BLOCKS",
    "map": MAP,
    "source_png": str(SOURCE),
    "source_sha256": digest(SOURCE),
    "texture": texture.get_path_name(),
    "material": material.get_path_name(),
    "removed": sorted(removed),
    "placed": placed,
    "guide_rail_z_cm": 24.0,
    "gameplay_status": "three separate shuttle actors ready for a later +Y pitch controller",
    "protected_sha256_before": before,
    "protected_sha256_after": after,
}, indent=2, sort_keys=True) + "\n", encoding="utf-8")
unreal.log(f"PRESSSHOP_2126_TRANSFER_SHUTTLE_REPLACEMENT_PASS receipt={RECEIPT}")
unreal.SystemLibrary.quit_editor()
