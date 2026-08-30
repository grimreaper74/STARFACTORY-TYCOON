"""Install the accepted detailed 2126 finished-panel hover-pallet sprite.

The three existing native carrier bases remain the collision and Sequencer
parents. Their low-detail visible components are hidden, and one detailed card
is attached to each base so motion remains native and synchronized.
"""
import hashlib
import json
import math
from pathlib import Path
import unreal

PROJECT = Path(r"C:\Users\greg_\Projects\LineBossCarFactory_Unreal 5.8")
MAP = "/Game/LineBoss/Candidates/PressShop/PressShop2126_FullHall_v001/Maps/LB_PressShop_2126_FullHall_v001"
ROOT = "/Game/LineBoss/Candidates/PressShop/PressShop2126_FullHall_v001/Sprites"
SOURCE = PROJECT / "SourceArt" / "PressShop2126" / "Sprites" / "T_CA_MW_2126_FinishedPanelHoverPallet_v001.png"
TEXTURE_NAME = "T_CA_MW_2126_FinishedPanelHoverPallet_v001"
MATERIAL_NAME = "M_CA_MW_2126_FinishedPanelHoverPallet_UnlitMasked_v001"
TEXTURE_PATH = ROOT + "/" + TEXTURE_NAME
MATERIAL_PATH = ROOT + "/" + MATERIAL_NAME
RECEIPT = PROJECT / "Saved" / "Audits" / "PressShop2126" / "detailed_hover_pallet_sprites_v001_receipt.json"
TAG = unreal.Name("LB.PressShop.2126.DetailedHoverPalletSprite.v001")
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
    return unit(unreal.Vector(v.x - normal.x * dot(v, normal),
                              v.y - normal.y * dot(v, normal),
                              v.z - normal.z * dot(v, normal)))

before = {str(path): digest(path) for path in PROTECTED}
for path, expected in PROTECTED.items():
    if before[str(path)] != expected:
        raise RuntimeError("protected map missing or changed: " + str(path))
if not SOURCE.is_file() or digest(SOURCE) != "a84a92e835f70af09de3b39fef965b05ba136c3746328432f524e5900d8e1b2f":
    raise RuntimeError("accepted hover-pallet sprite source missing or changed")
if unreal.EditorAssetLibrary.does_asset_exist(TEXTURE_PATH) or unreal.EditorAssetLibrary.does_asset_exist(MATERIAL_PATH):
    raise RuntimeError("hover-pallet sprite assets already exist; refusing overwrite")

task = unreal.AssetImportTask()
task.set_editor_properties({
    "filename": str(SOURCE), "destination_path": ROOT,
    "destination_name": TEXTURE_NAME, "automated": True,
    "replace_existing": False, "save": True,
})
unreal.AssetToolsHelpers.get_asset_tools().import_asset_tasks([task])
paths = list(task.get_editor_property("imported_object_paths") or [])
if len(paths) != 1:
    raise RuntimeError("hover-pallet texture import failed: " + repr(paths))
texture = unreal.load_asset(paths[0])
if not isinstance(texture, unreal.Texture2D):
    raise RuntimeError("hover-pallet PNG did not import as Texture2D")
texture.set_editor_properties({
    "srgb": True,
    "compression_settings": unreal.TextureCompressionSettings.TC_DEFAULT,
    "never_stream": True,
})
unreal.EditorAssetLibrary.save_loaded_asset(texture, only_if_is_dirty=False)

material = unreal.AssetToolsHelpers.get_asset_tools().create_asset(
    MATERIAL_NAME, ROOT, unreal.Material, unreal.MaterialFactoryNew())
if not isinstance(material, unreal.Material):
    raise RuntimeError("could not create hover-pallet sprite material")
material.set_editor_properties({
    "blend_mode": unreal.BlendMode.BLEND_MASKED,
    "shading_model": unreal.MaterialShadingModel.MSM_UNLIT,
    "two_sided": True,
    "opacity_mask_clip_value": 0.025,
})
mel = unreal.MaterialEditingLibrary
sample = mel.create_material_expression(material, unreal.MaterialExpressionTextureSample, -520, 0)
sample.set_editor_properties({"texture": texture, "sampler_type": unreal.MaterialSamplerType.SAMPLERTYPE_COLOR})
gain = mel.create_material_expression(material, unreal.MaterialExpressionConstant, -520, 180)
gain.set_editor_property("r", 0.55)
multiply = mel.create_material_expression(material, unreal.MaterialExpressionMultiply, -250, 0)
if not mel.connect_material_expressions(sample, "RGB", multiply, "A"):
    raise RuntimeError("could not connect hover-pallet colour")
if not mel.connect_material_expressions(gain, "", multiply, "B"):
    raise RuntimeError("could not connect hover-pallet gain")
if not mel.connect_material_property(multiply, "", unreal.MaterialProperty.MP_EMISSIVE_COLOR):
    raise RuntimeError("could not connect hover-pallet emissive")
if not mel.connect_material_property(sample, "A", unreal.MaterialProperty.MP_OPACITY_MASK):
    raise RuntimeError("could not connect hover-pallet alpha")
mel.recompile_material(material)
unreal.EditorAssetLibrary.save_loaded_asset(material, only_if_is_dirty=False)

if not unreal.EditorLoadingAndSavingUtils.load_map(MAP):
    raise RuntimeError("could not load isolated FullHall candidate")
actors = {actor.get_actor_label(): actor for actor in unreal.EditorLevelLibrary.get_all_level_actors()}
if any(TAG in actor.tags for actor in actors.values()):
    raise RuntimeError("detailed hover-pallet pass already tagged")
camera = actors.get("CAM | 2126 full hall fixed game view")
if not isinstance(camera, unreal.CameraActor):
    raise RuntimeError("fixed game camera missing")
camera_forward = unreal.MathLibrary.get_forward_vector(camera.get_actor_rotation())
flow_axis = projected(unreal.Vector(1.0, 0.0, 0.0), camera_forward)
card_rotation = unreal.MathLibrary.make_rot_from_zx(camera_forward, flow_axis)
plane = unreal.load_asset("/Engine/BasicShapes/Plane.Plane")
if not isinstance(plane, unreal.StaticMesh):
    raise RuntimeError("native plane missing")

cards = []
hidden_native = []
for slot in ("A", "B", "C"):
    base_label = f"2126 OUTBOUND | hover pallet {slot} collision base"
    base = actors.get(base_label)
    if not isinstance(base, unreal.StaticMeshActor):
        raise RuntimeError("hover-pallet collision base missing: " + base_label)
    native_labels = (
        base_label,
        f"2126 OUTBOUND | hover pallet {slot} safety rail north",
        f"2126 OUTBOUND | hover pallet {slot} safety rail south",
        f"2126 OUTBOUND | hover pallet {slot} status beacon",
        f"2126 OUTBOUND | finished-panel payload {slot}",
    )
    for label in native_labels:
        native = actors.get(label)
        if not isinstance(native, unreal.StaticMeshActor):
            raise RuntimeError("native pallet component missing: " + label)
        native.static_mesh_component.set_visibility(False, True)
        hidden_native.append(label)

    anchor = base.get_actor_location()
    anchor = unreal.Vector(anchor.x, anchor.y, 250.0)
    location = unreal.Vector(
        anchor.x - camera_forward.x * 85.0,
        anchor.y - camera_forward.y * 85.0,
        anchor.z - camera_forward.z * 85.0,
    )
    card = unreal.EditorLevelLibrary.spawn_actor_from_class(
        unreal.StaticMeshActor, location, card_rotation)
    if not isinstance(card, unreal.StaticMeshActor):
        raise RuntimeError("could not spawn detailed hover-pallet card")
    card.set_actor_label(f"2126 OUTBOUND | detailed finished-panel hover pallet sprite {slot}")
    card.tags = [TAG, unreal.Name("LB.PressShop.2126.Outbound"), unreal.Name("LB.Role.DetailedMovableVisual")]
    card.static_mesh_component.set_static_mesh(plane)
    card.static_mesh_component.set_material(0, material)
    card.static_mesh_component.set_collision_enabled(unreal.CollisionEnabled.NO_COLLISION)
    card.static_mesh_component.set_editor_property("cast_shadow", False)
    card.static_mesh_component.set_mobility(unreal.ComponentMobility.MOVABLE)
    card.set_actor_scale3d(unreal.Vector(7.0, 3.94, 1.0))
    if not card.attach_to_actor(
            base, unreal.Name(""), unreal.AttachmentRule.KEEP_WORLD,
            unreal.AttachmentRule.KEEP_WORLD, unreal.AttachmentRule.KEEP_WORLD, False):
        raise RuntimeError("could not attach detailed card to mover base " + slot)
    cards.append({
        "label": card.get_actor_label(),
        "parent": base.get_actor_label(),
        "world_location_cm": [location.x, location.y, location.z],
        "scale": [7.0, 3.94, 1.0],
    })

if not unreal.EditorLoadingAndSavingUtils.save_current_level():
    raise RuntimeError("detailed hover-pallet pass did not save")
unreal.EditorLoadingAndSavingUtils.save_dirty_packages(True, True)
after = {str(path): digest(path) for path in PROTECTED}
if after != before:
    raise RuntimeError("protected maps changed during detailed hover-pallet pass")

RECEIPT.parent.mkdir(parents=True, exist_ok=True)
RECEIPT.write_text(json.dumps({
    "status": "PASS__2126_DETAILED_HOVER_PALLET_SPRITES_INSTALLED_ON_NATIVE_MOVERS",
    "map": MAP,
    "source_png": str(SOURCE),
    "source_sha256": digest(SOURCE),
    "source_dimensions_px": [1672, 941],
    "source_has_true_alpha": True,
    "texture": texture.get_path_name(),
    "material": material.get_path_name(),
    "cards": cards,
    "native_visuals_hidden": hidden_native,
    "native_collision_bases_preserved": 3,
    "existing_sequence_bindings_preserved": True,
    "ordinary_wheels": 0,
    "protected_sha256_before": before,
    "protected_sha256_after": after,
}, indent=2, sort_keys=True) + "\n", encoding="utf-8")
unreal.log("PRESSSHOP_2126_DETAILED_HOVER_PALLET_PASS receipt=" + str(RECEIPT))
unreal.SystemLibrary.quit_editor()
