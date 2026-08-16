"""Add reusable Cairnwell packaged-coil dressing and worn PR-004 paint."""

import json
from datetime import datetime, timezone
from pathlib import Path

import unreal


MAP = "/Game/LineBoss/Maps/LB_PressShop_PR004PackagingPolishCandidate_v026"
DEST = "/Game/LineBoss/IndustrialKit/MaterialHandling/MasterCoil/Candidate_v026"
LABEL_SOURCE = str(Path(unreal.Paths.project_dir()) / "SourceAssets/Brand/Cairnwell/CoilPackaging/Candidate_v026/T_Cairnwell_CoilShippingLabel_v026.png")
LABEL_TEXTURE_PATH = f"{DEST}/T_Cairnwell_CoilShippingLabel_v026"
LABEL_MATERIAL_PATH = f"{DEST}/M_Cairnwell_CoilShippingLabel_v026"
WRAP_MASTER = "/Game/LineBoss/Stations/Press/PR004/Candidate_v003/MaterialsPBR_v003/M_LB_PR004_NonmetalPBR_Master_v003"
FLOOR_MASTER = "/Game/LineBoss/Materials/FrontEnd/M_LB_FrontEndPaintedConcrete_Master"
OUT = Path(unreal.Paths.project_saved_dir()) / "Audits/press_shop_pr004_packaging_polish_candidate_v026.json"

levels = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
actors = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
lib = unreal.EditorAssetLibrary
tools = unreal.AssetToolsHelpers.get_asset_tools()
mel = unreal.MaterialEditingLibrary

if not levels.load_level(MAP):
    raise RuntimeError(f"Could not load {MAP}")


def instance(name, parent_path, vectors, scalars):
    path = f"{DEST}/{name}"
    asset = lib.load_asset(path)
    if asset is None:
        asset = tools.create_asset(name, DEST, unreal.MaterialInstanceConstant, unreal.MaterialInstanceConstantFactoryNew())
    parent = lib.load_asset(parent_path)
    if asset is None or parent is None:
        raise RuntimeError(f"Could not build {path} from {parent_path}")
    asset.set_editor_property("parent", parent)
    for parameter, value in vectors.items():
        mel.set_material_instance_vector_parameter_value(asset, parameter, unreal.LinearColor(*value))
    for parameter, value in scalars.items():
        mel.set_material_instance_scalar_parameter_value(asset, parameter, value)
    mel.update_material_instance(asset)
    lib.save_loaded_asset(asset, only_if_is_dirty=False)
    return asset


wrap = instance("MI_LB_PackagedCoil_AgedWrap_v026", WRAP_MASTER,
    {"SurfaceTint": (0.62, 0.59, 0.50, 1.0)},
    {"TextureInfluence": 0.14, "TextureScale": 13.0, "BaseRoughness": 0.76,
     "RoughTextureInfluence": 0.18, "Metallic": 0.0, "NormalStrength": 0.08})
yellow = instance("MI_LB_PR004_SafetyYellow_Aged_v026", FLOOR_MASTER,
    {"ZoneTint": (1.0, 0.48, 0.018, 1.0)}, {"TintStrength": 0.78, "DetailNormalStrength": 0.08})
green = instance("MI_LB_PR004_OperatorGreen_Aged_v026", FLOOR_MASTER,
    {"ZoneTint": (0.025, 0.92, 0.23, 1.0)}, {"TintStrength": 0.88, "DetailNormalStrength": 0.08})

texture = lib.load_asset(LABEL_TEXTURE_PATH)
if texture is None:
    task = unreal.AssetImportTask()
    task.set_editor_properties({
        "filename": LABEL_SOURCE, "destination_path": DEST,
        "destination_name": "T_Cairnwell_CoilShippingLabel_v026",
        "automated": True, "replace_existing": True, "save": True,
    })
    tools.import_asset_tasks([task])
    texture = lib.load_asset(LABEL_TEXTURE_PATH)
if texture is None:
    raise RuntimeError("Could not import Cairnwell coil label texture")
texture.set_editor_property("compression_settings", unreal.TextureCompressionSettings.TC_DEFAULT)
texture.set_editor_property("srgb", True)
lib.save_loaded_asset(texture, only_if_is_dirty=False)

label_material = lib.load_asset(LABEL_MATERIAL_PATH)
if label_material is None:
    label_material = tools.create_asset("M_Cairnwell_CoilShippingLabel_v026", DEST, unreal.Material, unreal.MaterialFactoryNew())
if hasattr(mel, "delete_all_material_expressions"):
    mel.delete_all_material_expressions(label_material)
sample = mel.create_material_expression(label_material, unreal.MaterialExpressionTextureSample, -360, -40)
sample.set_editor_property("texture", texture)
rough = mel.create_material_expression(label_material, unreal.MaterialExpressionConstant, -360, 120)
rough.set_editor_property("r", 0.72)
mel.connect_material_property(sample, "RGB", unreal.MaterialProperty.MP_BASE_COLOR)
mel.connect_material_property(rough, "", unreal.MaterialProperty.MP_ROUGHNESS)
label_material.set_editor_property("two_sided", True)
mel.recompile_material(label_material)
lib.save_loaded_asset(label_material, only_if_is_dirty=False)

plane = lib.load_asset("/Engine/BasicShapes/Plane")
if plane is None:
    raise RuntimeError("Missing Engine plane mesh")

packaged = []
static_labels = []
station = None
for actor in actors.get_all_level_actors():
    if actor.get_actor_label() == "LB_INT_PR004_V024_InteractiveUnpackageStation":
        station = actor
    for component in actor.get_components_by_class(unreal.StaticMeshComponent):
        mesh = component.get_editor_property("static_mesh")
        if mesh is None or "SM_LB_MasterCoil_Candidate_v002" not in mesh.get_path_name():
            continue
        component.set_material(0, wrap)
        packaged.append({"actor": actor.get_actor_label(), "component": component.get_name()})
        if actor.get_actor_label() == "LB_INT_PR004_V024_InteractiveUnpackageStation":
            continue
        location = component.get_world_location()
        label = actors.spawn_actor_from_class(
            unreal.StaticMeshActor, unreal.Vector(location.x, location.y + 76.8, location.z + 29.0),
            unreal.Rotator(roll=90.0, pitch=0.0, yaw=0.0))
        label.set_actor_label(f"LB_COIL_LABEL_V026_{actor.get_actor_label()}")
        label.set_actor_scale3d(unreal.Vector(0.78, 0.38, 1.0))
        label.tags = [unreal.Name("LB.Asset.Candidate.v026"), unreal.Name("LB.Material.PackagedCoilLabel"), unreal.Name("LB.Asset.CandidateNotPromoted")]
        label_component = label.static_mesh_component
        label_component.set_static_mesh(plane)
        label_component.set_material(0, label_material)
        label_component.set_collision_enabled(unreal.CollisionEnabled.NO_COLLISION)
        label_component.set_editor_property("can_ever_affect_navigation", False)
        label_component.set_editor_property("cast_shadow", False)
        static_labels.append(label.get_actor_label())

if station is None:
    raise RuntimeError("Missing native PR-004 station")
components = {component.get_name(): component for component in station.get_components_by_class(unreal.StaticMeshComponent)}
wrapped = components.get("PR004_WrappedCoilVisual")
wrapped_label = components.get("PR004_WrappedCoilLabelVisual")
if wrapped is None or wrapped_label is None:
    raise RuntimeError(f"Missing reusable wrapped presentation components: {sorted(components)}")
wrapped_label.set_static_mesh(plane)
wrapped_label.set_material(0, label_material)
wrapped_location = wrapped.get_world_location()
wrapped_label.set_world_location(unreal.Vector(wrapped_location.x, wrapped_location.y + 76.8, wrapped_location.z + 29.0), False, False)
wrapped_label.set_world_rotation(unreal.Rotator(roll=90.0, pitch=0.0, yaw=0.0), False, False)
wrapped_label.set_world_scale3d(unreal.Vector(0.78, 0.38, 1.0))
wrapped_label.set_collision_enabled(unreal.CollisionEnabled.NO_COLLISION)
wrapped_label.set_editor_property("can_ever_affect_navigation", False)

painted = []
for actor in actors.get_all_level_actors():
    label = actor.get_actor_label()
    component = actor.get_component_by_class(unreal.StaticMeshComponent)
    if component is None:
        continue
    if label == "LB_PR004_V025_OperatorPad":
        component.set_material(0, green)
        painted.append({"actor": label, "material": green.get_path_name()})
    elif label.startswith("LB_PR004_V025_"):
        component.set_material(0, yellow)
        painted.append({"actor": label, "material": yellow.get_path_name()})

floor_text = actors.spawn_actor_from_class(unreal.TextRenderActor, unreal.Vector(-5360.0, -1490.0, 10.0), unreal.Rotator(roll=0.0, pitch=-90.0, yaw=-90.0))
floor_text.set_actor_label("LB_PR004_V026_FloorStencil")
floor_text.tags = [unreal.Name("LB.Asset.Candidate.v026"), unreal.Name("LB.PR004.FloorStencil"), unreal.Name("LB.Asset.CandidateNotPromoted")]
text_component = floor_text.get_editor_property("text_render")
text_component.set_text("PR-004  COIL PREPARATION")
text_component.set_world_size(34.0)
text_component.set_text_render_color(unreal.Color(224, 226, 210, 255))
text_component.set_horizontal_alignment(unreal.HorizTextAligment.EHTA_CENTER)
text_component.set_vertical_alignment(unreal.VerticalTextAligment.EVRTA_TEXT_CENTER)
text_component.set_collision_enabled(unreal.CollisionEnabled.NO_COLLISION)
text_component.set_editor_property("can_ever_affect_navigation", False)

if len(packaged) != 15 or len(static_labels) != 14 or len(painted) != 11:
    raise RuntimeError(f"Unexpected v026 counts packaged={len(packaged)} static_labels={len(static_labels)} painted={len(painted)}")
if not levels.save_current_level():
    raise RuntimeError("Could not save v026 map")

OUT.parent.mkdir(parents=True, exist_ok=True)
OUT.write_text(json.dumps({
    "$schema": "line-boss/audit/press-shop-pr004-packaging-polish-candidate-v026/v1",
    "generated_utc": datetime.now(timezone.utc).isoformat(),
    "status": "ISOLATED_PACKAGING_AND_LOCAL_PAINT_POLISH__NOT_PROMOTED",
    "source_map": "/Game/LineBoss/Maps/LB_PressShop_PR004InteractiveFloorCandidate_v025",
    "candidate_map": MAP,
    "packaged_component_count": len(packaged),
    "static_label_count": len(static_labels),
    "native_wrapped_label_component": wrapped_label.get_name(),
    "materials": {"wrap": wrap.get_path_name(), "label": label_material.get_path_name(), "yellow": yellow.get_path_name(), "operator_green": green.get_path_name()},
    "floor_stencil": "PR-004  COIL PREPARATION",
    "all_new_dressing_non_colliding": True,
    "all_new_dressing_navigation_irrelevant": True,
    "accepted_v006_preserved": True,
    "rejected_v007_v010_untouched": True,
    "fresh_fixed_camera_visual_gate": "OPEN",
    "promotion_authorized": False
}, indent=2), encoding="utf-8")
unreal.log(f"LINE_BOSS_PR004_PACKAGING_POLISH_V026_BUILD_PASS packaged={len(packaged)} labels={len(static_labels)+1} paint={len(painted)}")
unreal.SystemLibrary.quit_editor()
