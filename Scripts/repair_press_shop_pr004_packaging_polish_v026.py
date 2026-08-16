"""Repair v026 readability after rejecting the first dark/mirrored visual pass."""

import json
from datetime import datetime, timezone
from pathlib import Path

import unreal


MAP = "/Game/LineBoss/Maps/LB_PressShop_PR004PackagingPolishCandidate_v026"
DEST = "/Game/LineBoss/IndustrialKit/MaterialHandling/MasterCoil/Candidate_v026"
OUT = Path(unreal.Paths.project_saved_dir()) / "Audits/press_shop_pr004_packaging_polish_repair_v026.json"
levels = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
actors = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
lib = unreal.EditorAssetLibrary
tools = unreal.AssetToolsHelpers.get_asset_tools()
mel = unreal.MaterialEditingLibrary

if not levels.load_level(MAP):
    raise RuntimeError(f"Could not load {MAP}")


def constant_material(name, colour, roughness):
    path = f"{DEST}/{name}"
    material = lib.load_asset(path) if lib.does_asset_exist(path) else None
    if material is None:
        material = tools.create_asset(name, DEST, unreal.Material, unreal.MaterialFactoryNew())
    if hasattr(mel, "delete_all_material_expressions"):
        mel.delete_all_material_expressions(material)
    tint = mel.create_material_expression(material, unreal.MaterialExpressionConstant4Vector, -300, -50)
    tint.set_editor_property("constant", unreal.LinearColor(*colour))
    rough = mel.create_material_expression(material, unreal.MaterialExpressionConstant, -300, 90)
    rough.set_editor_property("r", roughness)
    mel.connect_material_property(tint, "", unreal.MaterialProperty.MP_BASE_COLOR)
    mel.connect_material_property(rough, "", unreal.MaterialProperty.MP_ROUGHNESS)
    material.set_editor_property("two_sided", True)
    mel.recompile_material(material)
    lib.save_loaded_asset(material, only_if_is_dirty=False)
    return material


wrap = constant_material("M_LB_PackagedCoil_AgedWrap_v026", (0.48, 0.44, 0.36, 1.0), 0.84)
paper = constant_material("M_LB_CoilLabelPaper_v026", (0.72, 0.69, 0.58, 1.0), 0.78)
yellow = constant_material("M_LB_PR004_SafetyYellow_v026", (0.78, 0.47, 0.012, 1.0), 0.74)
green = lib.load_asset("/Game/LineBoss/Materials/FrontEnd/MI_LB_Floor_Walkway_Green")
if green is None:
    green = constant_material("M_LB_PR004_OperatorGreen_v026", (0.018, 0.19, 0.085, 1.0), 0.86)

for actor in list(actors.get_all_level_actors()):
    if actor.get_actor_label().startswith("LB_COIL_TEXT_V026_") or actor.get_actor_label().startswith("LB_PR004_V026_HMI_"):
        actors.destroy_actor(actor)

packaged_count = 0
label_backings = []
station = None
for actor in actors.get_all_level_actors():
    if actor.get_actor_label() == "LB_INT_PR004_V024_InteractiveUnpackageStation":
        station = actor
    component = actor.get_component_by_class(unreal.StaticMeshComponent)
    if component is not None:
        mesh = component.get_editor_property("static_mesh")
        if mesh is not None and "SM_LB_MasterCoil_Candidate_v002" in mesh.get_path_name():
            component.set_material(0, wrap)
            packaged_count += 1
    if actor.get_actor_label().startswith("LB_COIL_LABEL_V026_"):
        backing = actor.get_component_by_class(unreal.StaticMeshComponent)
        backing.set_material(0, paper)
        label_backings.append(actor)


def text_actor(label, text, location, size, colour):
    actor = actors.spawn_actor_from_class(unreal.TextRenderActor, location, unreal.Rotator(roll=0.0, pitch=0.0, yaw=90.0))
    actor.set_actor_label(label)
    actor.tags = [unreal.Name("LB.Asset.Candidate.v026"), unreal.Name("LB.Material.PackagedCoilLabel"), unreal.Name("LB.Asset.CandidateNotPromoted")]
    component = actor.get_editor_property("text_render")
    component.set_text(text)
    component.set_world_size(size)
    component.set_text_render_color(colour)
    component.set_horizontal_alignment(unreal.HorizTextAligment.EHTA_CENTER)
    component.set_vertical_alignment(unreal.VerticalTextAligment.EVRTA_TEXT_CENTER)
    component.set_collision_enabled(unreal.CollisionEnabled.NO_COLLISION)
    component.set_editor_property("can_ever_affect_navigation", False)
    return actor


for index, backing in enumerate(label_backings, 1):
    location = backing.get_actor_location()
    text_actor(f"LB_COIL_TEXT_V026_{index:02d}_Heading", "CAIRNWELL AUTOMOTIVE",
               unreal.Vector(location.x, location.y + 0.45, location.z + 7.5), 6.2, unreal.Color(31, 75, 68, 255))
    text_actor(f"LB_COIL_TEXT_V026_{index:02d}_Detail", "MOORCROSS / U-SERIES  MCX-U",
               unreal.Vector(location.x, location.y + 0.46, location.z - 6.0), 4.2, unreal.Color(32, 36, 40, 255))

if station is None:
    raise RuntimeError("Missing native PR-004 station")
static_components = {component.get_name(): component for component in station.get_components_by_class(unreal.StaticMeshComponent)}
text_components = {component.get_name(): component for component in station.get_components_by_class(unreal.TextRenderComponent)}
wrapped = static_components.get("PR004_WrappedCoilVisual")
backing = static_components.get("PR004_WrappedCoilLabelVisual")
heading = text_components.get("PR004_WrappedCoilLabelHeading")
detail = text_components.get("PR004_WrappedCoilLabelDetail")
if any(component is None for component in (wrapped, backing, heading, detail)):
    raise RuntimeError(f"Missing native label presentation components static={sorted(static_components)} text={sorted(text_components)}")
backing.set_material(0, paper)
origin = wrapped.get_world_location()
for component, z, size in ((heading, 36.5, 6.2), (detail, 23.0, 4.2)):
    component.set_world_location(unreal.Vector(origin.x, origin.y + 77.25, origin.z + z), False, False)
    component.set_world_rotation(unreal.Rotator(roll=0.0, pitch=0.0, yaw=90.0), False, False)
    component.set_world_size(size)

painted = 0
for actor in actors.get_all_level_actors():
    label = actor.get_actor_label()
    component = actor.get_component_by_class(unreal.StaticMeshComponent)
    if component is None:
        continue
    if label == "LB_PR004_V025_OperatorPad":
        component.set_material(0, green)
        component.set_collision_profile_name("NoCollision")
        component.set_collision_enabled(unreal.CollisionEnabled.NO_COLLISION)
        component.set_editor_property("can_ever_affect_navigation", False)
        painted += 1
    elif label.startswith("LB_PR004_V025_"):
        component.set_material(0, yellow)
        component.set_collision_profile_name("NoCollision")
        component.set_collision_enabled(unreal.CollisionEnabled.NO_COLLISION)
        component.set_editor_property("can_ever_affect_navigation", False)
        painted += 1

# StaticMeshActor native component collision overrides were observed reverting
# after candidate-map reload. Recreate only the eleven thin zoning actors in
# this final candidate so NoCollision is authored on their current instances.
floor_specs = []
for actor in list(actors.get_all_level_actors()):
    if not actor.get_actor_label().startswith("LB_PR004_V025_"):
        continue
    component = actor.get_component_by_class(unreal.StaticMeshComponent)
    floor_specs.append({
        "label": actor.get_actor_label(),
        "location": actor.get_actor_location(),
        "rotation": actor.get_actor_rotation(),
        "scale": actor.get_actor_scale3d(),
        "tags": list(actor.tags),
        "mesh": component.get_editor_property("static_mesh"),
        "material": component.get_material(0),
    })
    actors.destroy_actor(actor)
for spec in floor_specs:
    replacement = actors.spawn_actor_from_class(unreal.StaticMeshActor, spec["location"], spec["rotation"])
    replacement.set_actor_label(spec["label"])
    replacement.set_actor_scale3d(spec["scale"])
    replacement.tags = spec["tags"]
    component = replacement.static_mesh_component
    component.set_static_mesh(spec["mesh"])
    component.set_material(0, spec["material"])
    component.set_collision_profile_name("NoCollision")
    component.set_collision_enabled(unreal.CollisionEnabled.NO_COLLISION)
    component.set_editor_property("can_ever_affect_navigation", False)
    component.set_editor_property("cast_shadow", False)
if len(floor_specs) != 11:
    raise RuntimeError(f"Expected 11 floor actors to re-author, found {len(floor_specs)}")

floor_text = next((actor for actor in actors.get_all_level_actors() if actor.get_actor_label() == "LB_PR004_V026_FloorStencil"), None)
if floor_text is None:
    raise RuntimeError("Missing v026 floor stencil")
floor_component = floor_text.get_editor_property("text_render")
floor_component.set_text("COIL PREPARATION")
floor_component.set_world_size(30.0)
floor_text.set_actor_rotation(unreal.Rotator(roll=0.0, pitch=90.0, yaw=90.0), False)

# PR-004 is the process/station code, not the public name of the floor zone.
# Keep it on the physical HMI only and use operational wording on the floor.
widget_components = {component.get_name(): component for component in station.get_components_by_class(unreal.WidgetComponent)}
operator_hmi = widget_components.get("PR004_OperatorHMI")
if operator_hmi is None:
    raise RuntimeError(f"Missing native PR-004 operator HMI: {sorted(widget_components)}")
operator_hmi.set_world_location(unreal.Vector(-5284.0, -1490.0, 148.0), False, False)
operator_hmi.set_world_rotation(unreal.Rotator(roll=0.0, pitch=0.0, yaw=0.0), False, False)
operator_hmi.set_world_scale3d(unreal.Vector(0.075, 0.075, 0.075))
operator_hmi.set_visibility(True, True)
operator_hmi.set_editor_property("hidden_in_game", False)
operator_hmi.set_editor_property("can_ever_affect_navigation", False)

# Native 3D text is the deterministic diegetic fallback and click-facing
# presentation for fixed-camera/runtime capture. The live Slate widget remains
# bound to the same station authority behind it.
hmi_text_components = {component.get_name(): component for component in station.get_components_by_class(unreal.TextRenderComponent)}
hmi_text_layout = {
    "PR004_HMI_BrandText": (171.0, 2.35),
    "PR004_HMI_StationText": (165.0, 2.45),
    "PR004_HMI_StateText": (157.0, 2.75),
    "PR004_HMI_CoilText": (149.0, 2.25),
    "PR004_HMI_RecipeText": (142.0, 2.0),
    "PR004_HMI_ChecklistText": (135.0, 1.35),
    "PR004_HMI_ActionText": (126.0, 3.0),
}
missing_hmi_text = sorted(set(hmi_text_layout) - set(hmi_text_components))
if missing_hmi_text:
    raise RuntimeError(f"Missing native PR-004 HMI text components: {missing_hmi_text}")
for name, (z, size) in hmi_text_layout.items():
    component = hmi_text_components[name]
    component.set_world_location(unreal.Vector(-5283.4, -1490.0, z), False, False)
    component.set_world_rotation(unreal.Rotator(roll=0.0, pitch=0.0, yaw=0.0), False, False)
    component.set_world_size(size)
    component.set_horizontal_alignment(unreal.HorizTextAligment.EHTA_CENTER)
    component.set_vertical_alignment(unreal.VerticalTextAligment.EVRTA_TEXT_CENTER)
    component.set_visibility(True, True)
    component.set_editor_property("hidden_in_game", False)
    component.set_collision_enabled(unreal.CollisionEnabled.NO_COLLISION)
    component.set_editor_property("can_ever_affect_navigation", False)

cube = lib.load_asset("/Engine/BasicShapes/Cube")
charcoal = lib.load_asset("/Game/LineBoss/Materials/M_LB_ShellCharcoal")
if cube is None or charcoal is None:
    raise RuntimeError("Missing cube or Cairnwell-compatible charcoal HMI material")


def hmi_support(label, location, dimensions, affects_navigation):
    support = actors.spawn_actor_from_class(unreal.StaticMeshActor, location, unreal.Rotator())
    support.set_actor_label(label)
    support.tags = [unreal.Name("LB.Asset.Candidate.v026"), unreal.Name("LB.PR004.OperatorHMI"),
                    unreal.Name("LB.Asset.CandidateNotPromoted")]
    support.set_actor_scale3d(unreal.Vector(dimensions[0] / 100.0, dimensions[1] / 100.0, dimensions[2] / 100.0))
    component = support.static_mesh_component
    component.set_static_mesh(cube)
    component.set_material(0, charcoal)
    component.set_collision_enabled(unreal.CollisionEnabled.QUERY_AND_PHYSICS)
    component.set_collision_profile_name("BlockAll")
    component.set_editor_property("can_ever_affect_navigation", affects_navigation)
    return support


hmi_support("LB_PR004_V026_HMI_Base", unreal.Vector(-5295.0, -1490.0, 14.0), (48.0, 54.0, 10.0), True)
hmi_support("LB_PR004_V026_HMI_Post", unreal.Vector(-5295.0, -1490.0, 78.0), (12.0, 12.0, 124.0), True)
hmi_support("LB_PR004_V026_HMI_Bezel", unreal.Vector(-5290.0, -1490.0, 148.0), (8.0, 84.0, 64.0), False)

if packaged_count != 15 or len(label_backings) != 14 or painted != 11:
    raise RuntimeError(f"Repair count mismatch packaged={packaged_count} backings={len(label_backings)} paint={painted}")
if not levels.save_current_level():
    raise RuntimeError("Could not save repaired v026 map")

OUT.parent.mkdir(parents=True, exist_ok=True)
OUT.write_text(json.dumps({
    "$schema": "line-boss/audit/press-shop-pr004-packaging-polish-repair-v026/v1",
    "generated_utc": datetime.now(timezone.utc).isoformat(),
    "status": "DARK_WRAP_BLACK_LABEL_MIRRORED_STENCIL_REPAIRED__VISUAL_REGATE_OPEN",
    "map": MAP,
    "rejected_first_pass": ["wrap_too_dark", "shipping_label_black", "floor_stencil_mirrored"],
    "packaged_component_count": packaged_count,
    "static_label_backing_count": len(label_backings),
    "static_label_text_component_count": len(label_backings) * 2,
    "native_label_components": [backing.get_name(), heading.get_name(), detail.get_name()],
    "floor_stencil_public_wording": "COIL PREPARATION",
    "station_code_policy": "PR-004 appears on HMI/records, not as the public floor-zone name",
    "operator_hmi_component": operator_hmi.get_name(),
    "operator_hmi_world_location_cm": [-5284.0, -1490.0, 148.0],
    "operator_hmi_support_actor_count": 3,
    "painted_actor_count": painted,
    "all_new_text_non_colliding": True,
    "promotion_authorized": False
}, indent=2), encoding="utf-8")
unreal.log("LINE_BOSS_PR004_PACKAGING_POLISH_V026_REPAIR_PASS")
unreal.SystemLibrary.quit_editor()
