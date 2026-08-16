"""Create a fresh isolated v004 dock visual candidate with controlled Unreal PBR bindings."""
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path

import unreal


SOURCE_MAP = "/Game/LineBoss/Developer/Validation/LB_ServiceDockFamilyIntake_v003"
MAP = "/Game/LineBoss/Developer/Validation/LB_ServiceDockFamilyVisual_v004"
ROOT = Path(unreal.Paths.project_dir())
AUDIT = ROOT / "Saved/Audits/SupportRobots/service_dock_family_unreal_visual_build_v004.json"
V253 = ROOT / "Content/LineBoss/Maps/LB_PressShop_PlayableManagementCandidate_v253.umap"
lib = unreal.EditorAssetLibrary
levels = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
actors_api = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)


def sha256(path):
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest().upper()


def require(path, cls=unreal.MaterialInterface):
    asset = lib.load_asset(path)
    if asset is None or not isinstance(asset, cls):
        raise RuntimeError(f"Missing required {cls.__name__}: {path}")
    return asset


v253_before = sha256(V253)
if not lib.does_asset_exist(MAP):
    if not lib.duplicate_asset(SOURCE_MAP, MAP):
        raise RuntimeError(f"Could not duplicate {SOURCE_MAP} to {MAP}")
world = unreal.EditorLevelLibrary.get_editor_world()
current_map = world.get_outermost().get_name() if world is not None else ""
if current_map != MAP:
    raise RuntimeError(f"One-map rule violation: opened {current_map}, expected {MAP}")

materials = {
    "charcoal": require("/Game/LineBoss/Robots/Shared/Materials/Candidate_v002/MI_LB_Robot_BodyCharcoal_Restored_v002"),
    "yellow": require("/Game/LineBoss/Robots/Shared/Materials/Candidate_v002/MI_LB_Robot_SafetyYellow_Restored_v002"),
    "green": require("/Game/LineBoss/Robots/Shared/Materials/Candidate_v002/MI_LB_Robot_CairnwellGreen_Restored_v002"),
    "grey": require("/Game/LineBoss/Robots/Shared/Materials/Candidate_v002/MI_LB_Robot_ServiceGrey_Restored_v002"),
    "steel": require("/Game/LineBoss/Stations/Press/PR004/Candidate_v003/MaterialsPBR_v003/MI_LB_PR004_MachinedSteel_PBR_v003"),
    "rubber": require("/Game/LineBoss/Stations/Press/PR004/Candidate_v003/MaterialsPBR_v003/MI_LB_PR004_Rubber_PBR_v003"),
    "label": require("/Game/LineBoss/Stations/Press/PR004/Candidate_v003/MaterialsPBR_v003/MI_LB_PR004_ServiceLabel_PBR_v003"),
    "red": require("/Game/LineBoss/Stations/Press/PR004/Candidate_v003/MaterialsPBR_v003/MI_LB_PR004_WarningRed_PBR_v003"),
    "ready": require("/Game/LineBoss/Stations/Press/PR004/Candidate_v003/MaterialsPBR_v003/MI_LB_PR004_ReadyGreen_PBR_v003"),
    "blue": require("/Game/LineBoss/Stations/Press/PR004/Candidate_v003/MaterialsPBR_v003/MI_LB_PR004_SensorBlue_PBR_v003"),
    "orange": require("/Game/LineBoss/Stations/Press/PR004/Candidate_v003/MaterialsPBR_v003/MI_LB_PR004_MaintenanceOrange_PBR_v003"),
    "floor": require("/Game/LineBoss/Candidates/PressShop/PR004ConcreteFloor_v117/Materials/M_CA_MW_PR004_NeutralSealedConcrete_v117"),
}


def role_for(slot_name):
    name = slot_name.lower()
    if "safetyyellow" in name:
        return "yellow"
    if "cairnwellgreen" in name:
        return "green"
    if "estopred" in name:
        return "red"
    if "greenlens" in name:
        return "ready"
    if "amberlens" in name or "servicelamp" in name or "wasteorange" in name or "dockwaste" in name or "recovery" in name:
        return "orange"
    if "fluidblue" in name or "cleanwater" in name or "dockwater" in name:
        return "blue"
    if "rubber" in name or "hose" in name or "conduit" in name:
        return "rubber"
    if "label" in name:
        return "label"
    if "brushedsteel" in name or "toolsteel" in name or "docksteel" in name:
        return "steel"
    if "panel" in name:
        return "grey"
    if "charcoal" in name or "graphite" in name or "frame" in name:
        return "charcoal"
    return None


actors = {actor.get_actor_label(): actor for actor in actors_api.get_all_level_actors()}
bindings = []
unmapped = []
for label in ("LB_DOCK_INTAKE_MR01_v005", "LB_DOCK_INTAKE_CR01_v008"):
    actor = actors.get(label)
    if not isinstance(actor, unreal.StaticMeshActor):
        raise RuntimeError(f"Missing dock actor {label}")
    component = actor.static_mesh_component
    mesh = component.static_mesh
    for index, slot in enumerate(mesh.get_editor_property("static_materials")):
        slot_name = str(slot.get_editor_property("material_slot_name"))
        role = role_for(slot_name)
        if role is None:
            unmapped.append({"actor": label, "slot": index, "slot_name": slot_name})
            continue
        component.set_material(index, materials[role])
        bindings.append({"actor": label, "slot": index, "slot_name": slot_name, "role": role, "material": materials[role].get_path_name()})
if unmapped:
    raise RuntimeError(f"Unmapped dock material slots: {unmapped}")

floor = actors.get("LB_DOCK_INTAKE_Floor")
if not isinstance(floor, unreal.StaticMeshActor):
    raise RuntimeError("Missing intake floor")
floor.static_mesh_component.set_material(0, materials["floor"])

for actor in actors_api.get_all_level_actors():
    if isinstance(actor, unreal.SkyLight):
        actor.light_component.set_editor_property("intensity", 0.18)
    elif isinstance(actor, unreal.RectLight):
        actor.light_component.set_editor_property("intensity", 450.0 if actor.get_actor_label().endswith("01") else 320.0)

camera_specs = {
    "LB_DOCK_INTAKE_CAM_Family": ((-650.0, 700.0, 330.0), (0.0, 0.0, 75.0), 46.0),
    "LB_DOCK_INTAKE_CAM_MR01": ((-430.0, 120.0, 235.0), (0.0, -230.0, 78.0), 43.0),
    "LB_DOCK_INTAKE_CAM_CR01": ((-430.0, 570.0, 235.0), (0.0, 230.0, 78.0), 43.0),
}
for label, (location, target, fov) in camera_specs.items():
    camera = actors.get(label)
    if not isinstance(camera, unreal.CameraActor):
        raise RuntimeError(f"Missing camera {label}")
    camera.set_actor_location(unreal.Vector(*location), False, False)
    camera.set_actor_rotation(unreal.MathLibrary.find_look_at_rotation(camera.get_actor_location(), unreal.Vector(*target)), False)
    component = camera.camera_component
    component.set_editor_properties({"field_of_view": fov, "post_process_blend_weight": 1.0})
    settings = component.get_editor_property("post_process_settings")
    settings.set_editor_properties({
        "override_auto_exposure_method": True,
        "auto_exposure_method": unreal.AutoExposureMethod.AEM_BASIC,
        "override_auto_exposure_min_brightness": True,
        "override_auto_exposure_max_brightness": True,
        "auto_exposure_min_brightness": 1.0,
        "auto_exposure_max_brightness": 1.0,
        "override_auto_exposure_bias": True,
        "auto_exposure_bias": -2.25,
    })
    component.set_editor_property("post_process_settings", settings)

if not levels.save_current_level():
    raise RuntimeError(f"Could not save {MAP}")
map_file = ROOT / "Content/LineBoss/Developer/Validation/LB_ServiceDockFamilyVisual_v004.umap"
v253_after = sha256(V253)
if v253_before != v253_after:
    raise RuntimeError("Protected v253 changed during isolated visual build")
payload = {
    "$schema": "cairnwell/audit/service-dock-family-unreal-visual-build-v004/v1",
    "generated_utc": datetime.now(timezone.utc).isoformat(),
    "status": "PASS__ISOLATED_UNREAL_PBR_BINDINGS_AND_CONTROLLED_EXPOSURE__FRESH_VISUAL_GATE_REQUIRED__NOT_PROMOTED",
    "source_map": SOURCE_MAP,
    "map": MAP,
    "map_sha256": sha256(map_file),
    "binding_count": len(bindings),
    "bindings": bindings,
    "unmapped_slots": unmapped,
    "lighting": {"skylight_intensity": 0.18, "rect_light_intensity": [450.0, 320.0], "camera_exposure_bias": -2.25},
    "v253_sha256_before": v253_before,
    "v253_sha256_after": v253_after,
    "visual_gate_passed": False,
    "promotion_authorized": False,
}
AUDIT.parent.mkdir(parents=True, exist_ok=True)
AUDIT.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
unreal.log(f"LINE_BOSS_SERVICE_DOCK_VISUAL_V004_BUILD_PASS bindings={len(bindings)}")
