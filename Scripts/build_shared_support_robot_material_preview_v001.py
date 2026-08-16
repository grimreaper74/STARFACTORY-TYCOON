"""Build an isolated fixed-light preview for support-robot material Candidate v001."""

from __future__ import annotations

from datetime import datetime, timezone
import json
from pathlib import Path

import unreal


ROOT = Path(unreal.Paths.project_dir())
MAP = "/Game/LineBoss/Developer/Validation/LB_SupportRobot_Materials_Candidate_v001"
DEST = "/Game/LineBoss/Robots/Shared/Materials/Candidate_v001"
AUDIT = ROOT / "Saved/Audits/lb_support_robot_shared_material_preview_v001.json"

MATERIALS = [
    ("BODY CHARCOAL", "MI_LB_Robot_BodyCharcoal_Restored_v001", "MI_LB_Robot_BodyCharcoal_Mothballed_v001"),
    ("SAFETY YELLOW", "MI_LB_Robot_SafetyYellow_Restored_v001", "MI_LB_Robot_SafetyYellow_Mothballed_v001"),
    ("CAIRNWELL GREEN", "MI_LB_Robot_CairnwellGreen_Restored_v001", "MI_LB_Robot_CairnwellGreen_Mothballed_v001"),
    ("SERVICE GREY", "MI_LB_Robot_ServiceGrey_Restored_v001", "MI_LB_Robot_ServiceGrey_Mothballed_v001"),
]

lib = unreal.EditorAssetLibrary
levels = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
actors = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)

if lib.does_asset_exist(MAP):
    raise RuntimeError(f"Refusing to overwrite preserved preview map {MAP}")
if not levels.new_level(MAP):
    raise RuntimeError(f"Could not create {MAP}")

sphere = unreal.load_asset("/Engine/BasicShapes/Sphere.Sphere")
cube = unreal.load_asset("/Engine/BasicShapes/Cube.Cube")
floor_material = unreal.load_asset("/Game/LineBoss/Materials/M_LB_FactoryConcrete.M_LB_FactoryConcrete")
wall_material = unreal.load_asset("/Game/LineBoss/Materials/M_LB_ShellCharcoal.M_LB_ShellCharcoal")
if not all((sphere, cube, floor_material, wall_material)):
    raise RuntimeError("Missing engine preview meshes or Line Boss neutral materials")


def spawn_mesh(label, mesh, location, scale, material=None):
    actor = actors.spawn_actor_from_class(unreal.StaticMeshActor, unreal.Vector(*location), unreal.Rotator())
    actor.set_actor_label(label)
    actor.set_actor_scale3d(unreal.Vector(*scale))
    component = actor.get_editor_property("static_mesh_component")
    component.set_static_mesh(mesh)
    if material is not None:
        component.set_material(0, material)
    actor.set_editor_property("tags", [unreal.Name("LB.Asset.CandidateNotPromoted"), unreal.Name("LB.Validation.SupportRobotMaterials.v001")])
    return actor


spawn_mesh("LB_MAT_V001_Floor", cube, (0, 30, -12), (4.2, 3.2, 0.12), floor_material)
spawn_mesh("LB_MAT_V001_Backdrop", cube, (0, 120, 180), (4.2, 0.12, 2.1), wall_material)

rows = []
x_positions = (-240.0, -80.0, 80.0, 240.0)
for column, (semantic, restored_name, mothballed_name) in enumerate(MATERIALS):
    for condition, name, z in (("RESTORED_WITH_RETAINED_AGE", restored_name, 78.0), ("MOTHBALLED_SEVEN_YEAR", mothballed_name, 230.0)):
        path = f"{DEST}/{name}"
        material = lib.load_asset(path)
        if not isinstance(material, unreal.MaterialInstanceConstant):
            raise RuntimeError(f"Missing preview material {path}")
        actor = spawn_mesh(f"LB_MAT_V001_{semantic}_{condition}", sphere, (x_positions[column], 0.0, z), (0.62, 0.62, 0.62), material)
        rows.append({"actor": actor.get_actor_label(), "semantic": semantic, "condition": condition, "material": path, "location_cm": [x_positions[column], 0.0, z]})

sun = actors.spawn_actor_from_class(unreal.DirectionalLight, unreal.Vector(0, -200, 500), unreal.Rotator(-42, -28, 0))
sun.set_actor_label("LB_MAT_V001_KeySun")
sun.get_editor_property("directional_light_component").set_editor_properties({"intensity": 2.2, "light_color": unreal.Color(255, 244, 225, 255)})
sky = actors.spawn_actor_from_class(unreal.SkyLight, unreal.Vector(0, 0, 350), unreal.Rotator())
sky.set_actor_label("LB_MAT_V001_Sky")
sky.get_editor_property("light_component").set_editor_property("intensity", 0.65)
for label, location, colour, intensity in (
    ("FillLeft", (-360, -250, 280), unreal.Color(190, 215, 255, 255), 650.0),
    ("FillRight", (360, -180, 190), unreal.Color(255, 220, 185, 255), 520.0),
):
    light = actors.spawn_actor_from_class(unreal.PointLight, unreal.Vector(*location), unreal.Rotator())
    light.set_actor_label(f"LB_MAT_V001_{label}")
    light.get_editor_property("point_light_component").set_editor_properties({"intensity": intensity, "attenuation_radius": 900.0, "light_color": colour})

camera_location = unreal.Vector(0.0, -900.0, 190.0)
camera_target = unreal.Vector(0.0, 0.0, 150.0)
camera = actors.spawn_actor_from_class(unreal.CameraActor, camera_location, unreal.Rotator())
camera.set_actor_label("LB_CAM_SupportRobot_MaterialPreview_v001")
camera.set_actor_rotation(unreal.MathLibrary.find_look_at_rotation(camera_location, camera_target), False)
camera.get_editor_property("camera_component").set_editor_property("field_of_view", 47.0)

if not levels.save_current_level():
    raise RuntimeError(f"Could not save {MAP}")

result = {
    "$schema": "line-boss/audit/lb-support-robot-shared-material-preview-v001",
    "generated_utc": datetime.now(timezone.utc).isoformat(),
    "status": "FIXED_LIGHT_PREVIEW_MAP_BUILT__FRESH_SCREENSHOT_REQUIRED__NOT_PROMOTED",
    "map": MAP,
    "camera": camera.get_actor_label(),
    "swatches": rows,
    "source_assets_modified": False,
    "promotion_authorized": False,
}
AUDIT.parent.mkdir(parents=True, exist_ok=True)
AUDIT.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
unreal.log(f"LINE_BOSS_SUPPORT_ROBOT_MATERIAL_PREVIEW_V001_BUILT swatches={len(rows)} audit={AUDIT}")
unreal.SystemLibrary.quit_editor()
