"""Import and mount the 2126 coil verification cell and magnetic buffer shuttle."""
import hashlib
import json
import math
from pathlib import Path
import unreal

PROJECT = Path(r"C:\Users\greg_\Projects\LineBossCarFactory_Unreal 5.8")
MAP = "/Game/LineBoss/Candidates/PressShop/PressShop2126_FullHall_v001/Maps/LB_PressShop_2126_FullHall_v001"
ROOT = "/Game/LineBoss/Candidates/PressShop/PressShop2126_FullHall_v001/Sprites"
RECEIPT = PROJECT / "Saved" / "Audits" / "PressShop2126" / "import_mount_coil_verify_buffer_v001_receipt.json"
PROTECTED = {
    PROJECT / "Content" / "LineBoss" / "Maps" / "LB_PressShop_BuilderAuthorityCandidate_v438.umap": "5029c9d827d9a1d72c12f27ee757c9bc1e47febd5006ce6d7ba319aad2e7fec8",
    PROJECT / "Content" / "LineBoss" / "Candidates" / "PressShop" / "PressShop2126_v002" / "Maps" / "LB_PressShop_2126_Steam_v002.umap": "cc09cf46d33e8a562d97f5a3bc35a5b42c9582d8e4650cf315694ebf340e4aa0",
}
ASSETS = [
    {
        "source": PROJECT / "SourceArt" / "PressShop2126" / "Sprites" / "T_CA_MW_2126_CoilVerificationDebandCell_v001.png",
        "texture_name": "T_CA_MW_2126_CoilVerificationDebandCell_v001",
        "material_name": "M_CA_MW_2126_CoilVerificationDebandCell_UnlitMasked_v001",
        "actor_label": "2126 COIL | autonomous verification and de-banding cell",
        "anchor": (-7350.0, -3900.0, 310.0),
        "scale": (18.0, 12.0, 1.0),
    },
    {
        "source": PROJECT / "SourceArt" / "PressShop2126" / "Sprites" / "T_CA_MW_2126_MagneticCoilBufferShuttle_v001.png",
        "texture_name": "T_CA_MW_2126_MagneticCoilBufferShuttle_v001",
        "material_name": "M_CA_MW_2126_MagneticCoilBufferShuttle_UnlitMasked_v001",
        "actor_label": "2126 COIL | magnetic three-position buffer shuttle",
        "anchor": (-6450.0, -900.0, 260.0),
        "scale": (21.0, 14.0, 1.0),
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


def import_sprite(spec):
    texture_path = ROOT + "/" + spec["texture_name"]
    material_path = ROOT + "/" + spec["material_name"]
    if unreal.EditorAssetLibrary.does_asset_exist(texture_path) or unreal.EditorAssetLibrary.does_asset_exist(material_path):
        raise RuntimeError(f"refusing to overwrite existing sprite assets for {spec['actor_label']}")
    task = unreal.AssetImportTask()
    task.set_editor_properties({
        "filename": str(spec["source"]),
        "destination_path": ROOT,
        "destination_name": spec["texture_name"],
        "automated": True,
        "replace_existing": False,
        "save": True,
    })
    unreal.AssetToolsHelpers.get_asset_tools().import_asset_tasks([task])
    paths = list(task.get_editor_property("imported_object_paths") or [])
    if len(paths) != 1:
        raise RuntimeError(f"texture import failed for {spec['actor_label']}: {paths}")
    texture = unreal.load_asset(paths[0])
    if not isinstance(texture, unreal.Texture2D):
        raise RuntimeError("PNG did not import as Texture2D")
    texture.set_editor_properties({"srgb": True, "compression_settings": unreal.TextureCompressionSettings.TC_DEFAULT, "never_stream": True})
    unreal.EditorAssetLibrary.save_loaded_asset(texture, only_if_is_dirty=False)

    tools = unreal.AssetToolsHelpers.get_asset_tools()
    material = tools.create_asset(spec["material_name"], ROOT, unreal.Material, unreal.MaterialFactoryNew())
    if not isinstance(material, unreal.Material):
        raise RuntimeError(f"material creation failed for {spec['actor_label']}")
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
        raise RuntimeError("could not connect sprite colour")
    if not mel.connect_material_property(sample, "A", unreal.MaterialProperty.MP_OPACITY_MASK):
        raise RuntimeError("could not connect sprite alpha")
    mel.recompile_material(material)
    unreal.EditorAssetLibrary.save_loaded_asset(material, only_if_is_dirty=False)
    return texture, material


before = {str(path): digest(path) for path in PROTECTED}
for path, expected in PROTECTED.items():
    if before[str(path)] != expected:
        raise RuntimeError(f"protected map missing or changed: {path}")
for spec in ASSETS:
    if not spec["source"].is_file():
        raise RuntimeError(f"source sprite missing: {spec['source']}")

imported = []
for spec in ASSETS:
    texture, material = import_sprite(spec)
    imported.append((spec, texture, material))

if not unreal.EditorLoadingAndSavingUtils.load_map(MAP):
    raise RuntimeError("could not load isolated full-hall candidate")
actors = list(unreal.EditorLevelLibrary.get_all_level_actors())
labels = {a.get_actor_label() for a in actors}
for spec, _, _ in imported:
    if spec["actor_label"] in labels:
        raise RuntimeError(f"sprite actor already mounted: {spec['actor_label']}")

camera = next((a for a in actors if a.get_actor_label() == "CAM | 2126 full hall fixed game view"), None)
if not isinstance(camera, unreal.CameraActor):
    raise RuntimeError("fixed game camera missing")
rotation = camera.get_actor_rotation()
if abs(rotation.pitch + 60.0) > 0.2 or abs(rotation.yaw - 57.63) > 0.2:
    raise RuntimeError("fixed game camera basis changed")
camera_forward = unreal.MathLibrary.get_forward_vector(rotation)
delivery_axis = projected(unreal.Vector(0.0, 1.0, 0.0), camera_forward)
card_rotation = unreal.MathLibrary.make_rot_from_zx(camera_forward, delivery_axis)
plane = unreal.load_asset("/Engine/BasicShapes/Plane.Plane")
mounted = []
for spec, texture, material in imported:
    anchor = unreal.Vector(*spec["anchor"])
    location = unreal.Vector(anchor.x - camera_forward.x * 100.0, anchor.y - camera_forward.y * 100.0, anchor.z - camera_forward.z * 100.0)
    card = unreal.EditorLevelLibrary.spawn_actor_from_class(unreal.StaticMeshActor, location, card_rotation)
    card.set_actor_label(spec["actor_label"])
    card.static_mesh_component.set_static_mesh(plane)
    card.static_mesh_component.set_material(0, material)
    card.static_mesh_component.set_collision_enabled(unreal.CollisionEnabled.NO_COLLISION)
    card.static_mesh_component.set_editor_property("cast_shadow", False)
    card.set_actor_scale3d(unreal.Vector(*spec["scale"]))
    if dot(unreal.MathLibrary.get_up_vector(card_rotation), camera_forward) < 0.999:
        raise RuntimeError(f"sprite card does not face fixed camera: {spec['actor_label']}")
    mounted.append({
        "label": spec["actor_label"],
        "location_cm": [round(location.x, 2), round(location.y, 2), round(location.z, 2)],
        "scale": list(spec["scale"]),
        "texture": texture.get_path_name(),
        "material": material.get_path_name(),
        "source_png": str(spec["source"]),
        "source_sha256": digest(spec["source"]),
    })

coil_source = next((a for a in actors if isinstance(a, unreal.StaticMeshActor) and "packagedmastercoil" in a.get_actor_label().lower()), None)
if coil_source is None or coil_source.static_mesh_component.static_mesh is None:
    raise RuntimeError("approved packaged master-coil exemplar missing")
coil_mesh = coil_source.static_mesh_component.static_mesh
coil_rotation = coil_source.get_actor_rotation()
coil_scale = coil_source.get_actor_scale3d()
coil_specs = [
    ("2126 COIL | verification cell active load", -7350.0, -3900.0, 185.0),
    ("2126 COIL | magnetic buffer load A", -6450.0, -1750.0, 175.0),
    ("2126 COIL | magnetic buffer load C", -6450.0, -50.0, 175.0),
]
coils = []
for label, x, y, z in coil_specs:
    if label in labels:
        raise RuntimeError(f"coil actor already exists: {label}")
    coil = unreal.EditorLevelLibrary.spawn_actor_from_class(unreal.StaticMeshActor, unreal.Vector(x, y, z), coil_rotation)
    coil.set_actor_label(label)
    coil.static_mesh_component.set_static_mesh(coil_mesh)
    coil.set_actor_scale3d(coil_scale)
    coil.static_mesh_component.set_collision_enabled(unreal.CollisionEnabled.QUERY_ONLY)
    coils.append({"label": label, "location_cm": [x, y, z]})

if not unreal.EditorLoadingAndSavingUtils.save_current_level():
    raise RuntimeError("verification/buffer integration did not save")
unreal.EditorLoadingAndSavingUtils.save_dirty_packages(True, True)
after = {str(path): digest(path) for path in PROTECTED}
if after != before:
    raise RuntimeError("protected maps changed during verification/buffer integration")

RECEIPT.parent.mkdir(parents=True, exist_ok=True)
RECEIPT.write_text(json.dumps({
    "status": "PASS__2126_COIL_VERIFICATION_AND_BUFFER_MOUNTED",
    "map": MAP,
    "mounted_sprites": mounted,
    "separate_reused_coils": coils,
    "coil_mesh_reused": coil_mesh.get_path_name(),
    "camera_contract": {"pitch": -60.0, "yaw": 57.63},
    "protected_sha256_before": before,
    "protected_sha256_after": after,
}, indent=2, sort_keys=True) + "\n", encoding="utf-8")
unreal.log(f"PRESSSHOP_2126_VERIFY_BUFFER_MOUNT_PASS receipt={RECEIPT}")
unreal.SystemLibrary.quit_editor()
