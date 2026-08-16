"""Place the validated modular enclosure around PR-009 for an early visual gate."""

import json
from datetime import datetime, timezone
from pathlib import Path

import unreal


ROOT = Path(unreal.Paths.project_dir())
PARENT_MAP = "/Game/LineBoss/Maps/LB_PressShop_PR009ServiceCameraCandidate_v090"
TARGET_MAP = "/Game/LineBoss/Maps/LB_PressShop_PR009EnclosurePilotCandidate_v094"
ASSET_DIR = "/Game/LineBoss/Candidates/PressShop/PR009/v094/Enclosure"
MAT_DIR = "/Game/LineBoss/Candidates/PressShop/PR009/v094/EnclosureMaterials"
OUT = ROOT / "Saved/Audits/PR009_InMap_v094/enclosure_build.json"
PREFIX = "LB_PR009_V094_ENC_"
DATUM = (600.0, -2000.0, 0.0)
YAW = -90.0

ASSETS = [
    "SM_CA_MW_ENC_PR009_Structure_02",
    "SM_CA_MW_ENC_PR009_PanelsRoof_02",
    "SM_CA_MW_ENC_PR009_Glazing_02",
    "SM_CA_MW_ENC_PR009_ServiceDoor_02",
    "SM_CA_MW_ENC_PR009_ServiceHardware_02",
    "SM_CA_MW_ENC_PR009_Utilities_02",
    "SM_CA_MW_ENC_PR009_RoofEquipment_02",
]

lib = unreal.EditorAssetLibrary
asset_tools = unreal.AssetToolsHelpers.get_asset_tools()
mel = unreal.MaterialEditingLibrary
levels = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
actors_api = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)

if not lib.does_asset_exist(TARGET_MAP):
    if not lib.duplicate_asset(PARENT_MAP, TARGET_MAP):
        raise RuntimeError(PARENT_MAP)
    if not lib.save_asset(TARGET_MAP, only_if_is_dirty=False):
        raise RuntimeError(TARGET_MAP)
    unreal.log("PR009_V094_MAP_DUPLICATED__RERUN_FOR_ENCLOSURE")
    unreal.SystemLibrary.quit_editor()
    raise SystemExit
if not levels.load_level(TARGET_MAP):
    raise RuntimeError(TARGET_MAP)

for actor in actors_api.get_all_level_actors():
    label = actor.get_actor_label()
    if "V090" in label:
        actor.set_actor_label(label.replace("V090", "V094"))
    actor.tags = [unreal.Name(str(tag).replace("v090", "v094")) for tag in actor.tags]
for actor in list(actors_api.get_all_level_actors()):
    if actor.get_actor_label().startswith(PREFIX):
        actors_api.destroy_actor(actor)


def load_material(name):
    path = f"/Game/LineBoss/Stations/Press/PR009/Presentation_v085/Materials/{name}"
    material = lib.load_asset(path)
    if material is None:
        raise RuntimeError(path)
    return material


materials = {
    "frame": load_material("M_CA_MW_PR009_LayeredFoundryCharcoal_v085"),
    "green": load_material("M_CA_MW_PR009_LayeredCairnwellGreen_v085"),
    "yellow": load_material("M_CA_MW_PR009_LayeredSafetyYellow_v085"),
    "grey": load_material("M_CA_MW_PR009_LayeredServiceGrey_v085"),
    "machined": load_material("M_CA_MW_PR009_MachinedSteel_v085"),
    "galv": load_material("M_CA_MW_PR009_GalvanisedMesh_v085"),
    "rubber": load_material("M_CA_MW_PR009_Rubber_v085"),
}

glass_path = MAT_DIR + "/M_CA_MW_ENC_InspectionGlass_v094"
glass = lib.load_asset(glass_path) if lib.does_asset_exist(glass_path) else asset_tools.create_asset(
    "M_CA_MW_ENC_InspectionGlass_v094", MAT_DIR, unreal.Material, unreal.MaterialFactoryNew())
if glass is None:
    raise RuntimeError(glass_path)
mel.delete_all_material_expressions(glass)
glass.set_editor_property("blend_mode", unreal.BlendMode.BLEND_TRANSLUCENT)
glass.set_editor_property("two_sided", True)
colour = mel.create_material_expression(glass, unreal.MaterialExpressionConstant3Vector, -260, -80)
colour.set_editor_property("constant", unreal.LinearColor(0.012, 0.080, 0.085, 1.0))
opacity = mel.create_material_expression(glass, unreal.MaterialExpressionConstant, -260, 20)
opacity.set_editor_property("r", 0.32)
rough = mel.create_material_expression(glass, unreal.MaterialExpressionConstant, -260, 100)
rough.set_editor_property("r", 0.16)
mel.connect_material_property(colour, "", unreal.MaterialProperty.MP_BASE_COLOR)
mel.connect_material_property(opacity, "", unreal.MaterialProperty.MP_OPACITY)
mel.connect_material_property(rough, "", unreal.MaterialProperty.MP_ROUGHNESS)
mel.recompile_material(glass)
lib.save_loaded_asset(glass, only_if_is_dirty=False)
materials["glass"] = glass


def role_for(slot_name):
    value = slot_name.upper()
    if "GLASS" in value:
        return "glass"
    if "GREEN" in value:
        return "green"
    if "YELLOW" in value:
        return "yellow"
    if "BRUSHED" in value:
        return "machined"
    if "GASKET" in value or "VENTBLACK" in value:
        return "rubber"
    if "SERVICEPANEL" in value:
        return "grey"
    if "ROOFCHARCOAL" in value or "FOUNDRYCHARCOAL" in value:
        return "frame"
    return "frame"


spawned = []
slot_assignments = []
for name in ASSETS:
    mesh = lib.load_asset(f"{ASSET_DIR}/{name}")
    if not isinstance(mesh, unreal.StaticMesh):
        raise RuntimeError(name)
    actor = actors_api.spawn_actor_from_class(unreal.StaticMeshActor, unreal.Vector(*DATUM), unreal.Rotator(yaw=YAW))
    actor.set_actor_label(PREFIX + name)
    actor.tags = [unreal.Name(tag) for tag in (
        "LB.Asset.Candidate.v094", "LB.Asset.CandidateNotPromoted",
        "LB.Station.PR009", "LB.Enclosure.AutomatedMachine.v002",
        "LB.Navigation.Neutral", "LB.Control.ControlRoomOnly")]
    component = actor.static_mesh_component
    component.set_static_mesh(mesh)
    component.set_world_scale3d(unreal.Vector(1.0, 1.0, 1.0))
    component.set_collision_enabled(unreal.CollisionEnabled.NO_COLLISION)
    component.set_collision_profile_name(unreal.Name("NoCollision"))
    component.set_editor_property("can_ever_affect_navigation", False)
    for index, slot in enumerate(mesh.get_editor_property("static_materials")):
        slot_name = str(slot.get_editor_property("imported_material_slot_name") or slot.get_editor_property("material_slot_name"))
        role = role_for(slot_name)
        component.set_material(index, materials[role])
        slot_assignments.append({"actor": actor.get_actor_label(), "slot": slot_name, "role": role})
    spawned.append(actor)

# The enclosure replaces only the authored perimeter GuardSet presentation.
# Preserve its proven collision during this early visual gate; internal drive
# guards, light curtains and controlled transfer barriers stay visible.
hidden_old_guard = []
for actor in actors_api.get_all_level_actors():
    if "SM_CA_MW_PR009_GuardSet_01" not in actor.get_actor_label():
        continue
    actor.set_actor_hidden_in_game(True)
    actor.set_is_temporarily_hidden_in_editor(True)
    hidden_old_guard.append(actor.get_actor_label())
if len(hidden_old_guard) != 1:
    raise RuntimeError(f"Expected exactly one old GuardSet actor, found {hidden_old_guard}")


def text(label, value, location, size, colour_value):
    actor = actors_api.spawn_actor_from_class(unreal.TextRenderActor, unreal.Vector(*location), unreal.Rotator(yaw=-90.0))
    actor.set_actor_label(PREFIX + "TEXT_" + label)
    actor.tags = [unreal.Name(tag) for tag in (
        "LB.Asset.Candidate.v094", "LB.Asset.CandidateNotPromoted",
        "LB.Identity.CairnwellMoorcross", "LB.Navigation.Neutral")]
    component = actor.text_render
    component.set_text(value)
    component.set_world_size(size)
    component.set_text_render_color(colour_value)
    component.set_horizontal_alignment(unreal.HorizTextAligment.EHTA_CENTER)
    component.set_vertical_alignment(unreal.VerticalTextAligment.EVRTA_TEXT_CENTER)
    component.set_collision_enabled(unreal.CollisionEnabled.NO_COLLISION)
    component.set_editor_property("can_ever_affect_navigation", False)
    spawned.append(actor)
    return actor


identity = [
    text("Corporation", "CAIRNWELL AUTOMOTIVE", (642.0, -2240.0, 294.0), 9.0, unreal.Color(70,220,165,255)),
    text("Site", "MOORCROSS WORKS", (642.0, -2240.0, 282.0), 7.6, unreal.Color(228,235,230,255)),
    text("Station", "PR-009  AUTOMATED BLANK STACKER", (642.0, -2240.0, 270.0), 5.6, unreal.Color(242,195,0,255)),
]

# Add a dedicated enclosure hero while retaining the v090 south service camera.
camera_location = unreal.Vector(-280.0, -2840.0, 630.0)
camera_target = unreal.Vector(615.0, -2000.0, 155.0)
camera = actors_api.spawn_actor_from_class(unreal.CameraActor, camera_location, unreal.Rotator())
camera.set_actor_label(PREFIX + "CAM_EnclosureHero")
camera.tags = [unreal.Name("LB.Asset.Candidate.v094"), unreal.Name("LB.Asset.CandidateNotPromoted"), unreal.Name("LB.Camera.Fixed.PR009.EnclosureHero")]
camera.set_actor_rotation(unreal.MathLibrary.find_look_at_rotation(camera_location, camera_target), False)
camera.camera_component.set_field_of_view(50.0)

flows = [a for a in actors_api.get_all_level_actors() if isinstance(a, unreal.LBPressShopMaterialFlowController)]
pr008 = [a for a in actors_api.get_all_level_actors() if isinstance(a, unreal.LBPR008Station)]
pr009 = [a for a in actors_api.get_all_level_actors() if isinstance(a, unreal.LBPR009Station)]
if len(flows) != 1 or len(pr008) != 1 or len(pr009) != 1:
    raise RuntimeError(f"Authority cardinality changed: flow={len(flows)} PR008={len(pr008)} PR009={len(pr009)}")
flows[0].bind_blank_stations(pr008[0], pr009[0])
if not levels.save_current_level():
    raise RuntimeError(TARGET_MAP)

actor_rows = []
for actor in spawned:
    origin, extent = actor.get_actor_bounds(False)
    actor_rows.append({
        "label": actor.get_actor_label(),
        "origin_cm": [origin.x, origin.y, origin.z],
        "extent_cm": [extent.x, extent.y, extent.z],
        "scale": [actor.get_actor_scale3d().x, actor.get_actor_scale3d().y, actor.get_actor_scale3d().z],
    })
OUT.parent.mkdir(parents=True, exist_ok=True)
OUT.write_text(json.dumps({
    "$schema": "cairnwell/audit/pr009-enclosure-pilot-build-v094/v1",
    "generated_utc": datetime.now(timezone.utc).isoformat(),
    "status": "V094_MODULAR_ENCLOSURE_PLACED_AT_PR009_DATUM__EARLY_VISUAL_GATE_REQUIRED__NOT_PROMOTED",
    "parent_map": PARENT_MAP,
    "target_map": TARGET_MAP,
    "datum_cm": DATUM,
    "yaw_degrees": YAW,
    "module_count": len(ASSETS),
    "actors": actor_rows,
    "slot_assignments": slot_assignments,
    "hidden_superseded_guard_visuals": hidden_old_guard,
    "old_guard_collision_preserved_for_early_gate": True,
    "new_enclosure_collision_authored": False,
    "process_geometry_changed": False,
    "runtime_authority_changed": False,
    "line_boss_in_world": False,
    "pr010_started": False,
    "robots_modified": False,
    "promotion_authorized": False,
}, indent=2), encoding="utf-8")
unreal.log(f"PR009_V094_ENCLOSURE_BUILD_PASS output={OUT}")
