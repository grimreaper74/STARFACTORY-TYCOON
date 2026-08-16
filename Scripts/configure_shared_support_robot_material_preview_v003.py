"""Bind corrected v002 materials and neutral fixed lighting in preview v003."""

from datetime import datetime, timezone
import json
from pathlib import Path

import unreal


MAP = "/Game/LineBoss/Developer/Validation/LB_SupportRobot_Materials_Candidate_v003"
MATERIAL_ROOT = "/Game/LineBoss/Robots/Shared/Materials/Candidate_v002"
ROOT = Path(unreal.Paths.project_dir())
AUDIT = ROOT / "Saved/Audits/lb_support_robot_shared_material_preview_v003.json"
actors = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
levels = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
lib = unreal.EditorAssetLibrary

world = unreal.EditorLevelLibrary.get_editor_world()
current_package = world.get_outermost().get_name() if world is not None else ""
if current_package != MAP:
    raise RuntimeError(f"One-map rule violation: opened {current_package}, expected {MAP}")

semantic_names = {
    "BODY CHARCOAL": "BodyCharcoal",
    "SAFETY YELLOW": "SafetyYellow",
    "CAIRNWELL GREEN": "CairnwellGreen",
    "SERVICE GREY": "ServiceGrey",
}
bindings = []
for actor in actors.get_all_level_actors():
    label = actor.get_actor_label()
    semantic = next((key for key in semantic_names if key in label), None)
    if semantic is None or not isinstance(actor, unreal.StaticMeshActor):
        continue
    condition = "Mothballed" if "MOTHBALLED" in label else "Restored"
    material_path = f"{MATERIAL_ROOT}/MI_LB_Robot_{semantic_names[semantic]}_{condition}_v002"
    material = lib.load_asset(material_path)
    if not isinstance(material, unreal.MaterialInstanceConstant):
        raise RuntimeError(f"Missing corrected material {material_path}")
    actor.get_editor_property("static_mesh_component").set_material(0, material)
    bindings.append({"actor": label, "material": material_path})

if len(bindings) != 8:
    raise RuntimeError(f"Expected 8 corrected material bindings, found {len(bindings)}")

camera = next((actor for actor in actors.get_all_level_actors() if actor.get_actor_label() == "LB_CAM_SupportRobot_MaterialPreview_v002"), None)
if camera is None:
    raise RuntimeError("Missing inherited v002 camera")
camera.set_actor_label("LB_CAM_SupportRobot_MaterialPreview_v003")
settings = camera.get_editor_property("camera_component").get_editor_property("post_process_settings")
settings.set_editor_properties({
    "override_auto_exposure_method": True,
    "auto_exposure_method": unreal.AutoExposureMethod.AEM_BASIC,
    "override_auto_exposure_min_brightness": True,
    "override_auto_exposure_max_brightness": True,
    "auto_exposure_min_brightness": 1.0,
    "auto_exposure_max_brightness": 1.0,
    "override_auto_exposure_bias": True,
    "auto_exposure_bias": -0.4,
})

light_changes = []
for actor in actors.get_all_level_actors():
    label = actor.get_actor_label()
    if label == "LB_MAT_V001_KeySun":
        component = actor.get_editor_property("directional_light_component")
        component.set_editor_properties({"intensity": 2.0, "light_color": unreal.Color(255, 255, 255, 255)})
        light_changes.append({"actor": label, "intensity": 2.0, "colour": "neutral"})
    elif label == "LB_MAT_V001_FillLeft":
        component = actor.get_editor_property("point_light_component")
        component.set_editor_properties({"intensity": 260.0, "light_color": unreal.Color(255, 255, 255, 255)})
        light_changes.append({"actor": label, "intensity": 260.0, "colour": "neutral"})
    elif label == "LB_MAT_V001_FillRight":
        component = actor.get_editor_property("point_light_component")
        component.set_editor_properties({"intensity": 220.0, "light_color": unreal.Color(255, 255, 255, 255)})
        light_changes.append({"actor": label, "intensity": 220.0, "colour": "neutral"})

if not levels.save_current_level():
    raise RuntimeError(f"Could not save {MAP}")
result = {
    "$schema": "line-boss/audit/lb-support-robot-shared-material-preview-v003",
    "generated_utc": datetime.now(timezone.utc).isoformat(),
    "status": "CORRECTED_MATERIALS_BOUND__FRESH_SCREENSHOT_REQUIRED__NOT_PROMOTED",
    "map": MAP,
    "material_candidate": MATERIAL_ROOT,
    "camera": camera.get_actor_label(),
    "exposure": {"method": "AEM_BASIC", "min": 1.0, "max": 1.0, "bias": -0.4},
    "bindings": sorted(bindings, key=lambda row: row["actor"]),
    "light_changes": light_changes,
    "promotion_authorized": False,
}
AUDIT.parent.mkdir(parents=True, exist_ok=True)
AUDIT.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
unreal.log(f"LINE_BOSS_SUPPORT_ROBOT_MATERIAL_PREVIEW_V003_CONFIGURED bindings={len(bindings)} audit={AUDIT}")
unreal.SystemLibrary.quit_editor()
