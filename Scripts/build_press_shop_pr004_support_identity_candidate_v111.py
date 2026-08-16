"""Author a compact, legible two-sided CR-30-01 bridge identity in isolated v111."""
from pathlib import Path
from datetime import datetime, timezone
import json
import os
import unreal

VERSION = os.environ.get("LB_PR004_SUPPORT_IDENTITY_VERSION", "v111").lower()
if VERSION not in ("v111", "v112", "v113"):
    raise RuntimeError(f"Unsupported identity version {VERSION}")
MAP = f"/Game/LineBoss/Maps/LB_PressShop_PR004SupportIdentityCandidate_{VERSION}"
OUT = Path(unreal.Paths.project_saved_dir()) / f"Audits/press_shop_pr004_support_identity_candidate_{VERSION}.json"
PREFIX = f"LB_PR004_{VERSION.upper()}_"
levels = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
actors = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
lib = unreal.EditorAssetLibrary
if not levels.load_level(MAP):
    raise RuntimeError(f"Could not load {MAP}")

cube_mesh = lib.load_asset("/Engine/BasicShapes/Cube")
dark = lib.load_asset("/Game/LineBoss/IndustrialKit/MaterialHandling/BridgeCrane/Candidate_v031/MI_LB_Crane_DarkSteel_v031")
yellow = lib.load_asset("/Game/LineBoss/IndustrialKit/MaterialHandling/BridgeCrane/Candidate_v031/MI_LB_Crane_RAL1023_Aged_v031")
green = lib.load_asset("/Game/LineBoss/Robots/Shared/Materials/Candidate_v004/MI_LB_Robot_CairnwellGreen_Restored_v004")
ivory = lib.load_asset("/Game/LineBoss/IndustrialKit/MaterialHandling/MasterCoil/Candidate_v029/MI_LB_MasterCoil_LabelPaper_v029")
if any(x is None for x in (cube_mesh, dark, yellow, green, ivory)):
    raise RuntimeError("Missing controlled identity materials")

def names(*values):
    return [unreal.Name(value) for value in values]

common = ("LB.Motion.CraneBridge", "LB.Crane.30T", "LB.Module.CraneIdentity",
          "LB.Identity.CR-30-01", "LB.Operations.MaintenanceOnly",
          f"LB.Asset.Candidate.{VERSION}", "LB.Asset.CandidateNotPromoted")

def cube(label, location, dimensions, material):
    actor = actors.spawn_actor_from_class(unreal.StaticMeshActor, unreal.Vector(*location), unreal.Rotator())
    actor.set_actor_label(PREFIX + label)
    actor.tags = names(*common)
    actor.static_mesh_component.set_static_mesh(cube_mesh)
    actor.set_actor_scale3d(unreal.Vector(dimensions[0] / 100.0, dimensions[1] / 100.0, dimensions[2] / 100.0))
    actor.static_mesh_component.set_material(0, material)
    actor.static_mesh_component.set_mobility(unreal.ComponentMobility.MOVABLE)
    actor.static_mesh_component.set_collision_enabled(unreal.CollisionEnabled.NO_COLLISION)
    actor.static_mesh_component.set_editor_property("can_ever_affect_navigation", False)
    return actor

def text(label, location, yaw, body, size):
    actor = actors.spawn_actor_from_class(
        unreal.TextRenderActor, unreal.Vector(*location), unreal.Rotator(pitch=0.0, yaw=yaw, roll=0.0))
    actor.set_actor_label(PREFIX + label)
    actor.tags = names(*common)
    actor.text_render.set_text(body)
    actor.text_render.set_world_size(size)
    actor.text_render.set_horizontal_alignment(unreal.HorizTextAligment.EHTA_CENTER)
    actor.text_render.set_vertical_alignment(unreal.VerticalTextAligment.EVRTA_TEXT_CENTER)
    actor.text_render.set_text_render_color(unreal.Color(235, 238, 226, 255))
    actor.text_render.set_mobility(unreal.ComponentMobility.MOVABLE)
    actor.text_render.set_collision_enabled(unreal.CollisionEnabled.NO_COLLISION)
    actor.text_render.set_editor_property("can_ever_affect_navigation", False)
    return actor

created = []
panel_z, field_z, rule_z, primary_z, secondary_z = (
    (1430.0, 1433.0, 1357.0, 1465.0, 1405.0)
    if VERSION == "v113" else
    (1505.0, 1508.0, 1432.0, 1540.0, 1480.0))
for side, panel_x, face_x, yaw, text_offset in (
        ("East", -9020.0, -9013.0, 0.0, 3.0),
        ("West", -9180.0, -9187.0, 180.0, -3.0)):
    created.append(cube(f"30T_{side}_Back", (panel_x, -2415.0, panel_z), (7.0, 820.0, 170.0), dark))
    created.append(cube(f"30T_{side}_GreenField", (face_x, -2415.0, field_z), (3.0, 780.0, 138.0), green))
    created.append(cube(f"30T_{side}_YellowRule", (face_x, -2415.0, rule_z), (3.0, 790.0, 12.0), yellow))
    for end_y in (-2814.0, -2016.0):
        created.append(cube(f"30T_{side}_End_{end_y}", (face_x, end_y, panel_z), (3.0, 14.0, 162.0), yellow))
    created.append(text(f"30T_{side}_Primary", (face_x + text_offset, -2415.0, primary_z), yaw,
                        "CR-30-01     SWL 30 t", 52.0))
    created.append(text(f"30T_{side}_Secondary", (face_x + text_offset, -2415.0, secondary_z), yaw,
                        "CAIRNWELL AUTOMOTIVE  |  MAINTENANCE SUPPORT", 27.0))

camera = actors.spawn_actor_from_class(unreal.CameraActor, unreal.Vector(-6500.0, 150.0, 1190.0), unreal.Rotator())
camera.set_actor_label(PREFIX + "CAM_SupportFleetIdentityReadable")
camera.tags = names("LB.Camera.Validation", f"LB.Camera.Fixed.SupportIdentity.{VERSION}",
                    f"LB.Asset.Candidate.{VERSION}", "LB.Asset.CandidateNotPromoted")
camera.set_actor_rotation(unreal.MathLibrary.find_look_at_rotation(
    camera.get_actor_location(), unreal.Vector(-9010.0, -2415.0, panel_z)), False)
camera.camera_component.set_editor_properties({"field_of_view": 32.0, "aspect_ratio": 16.0 / 9.0,
    "constrain_aspect_ratio": True, "post_process_blend_weight": 1.0})
settings = camera.camera_component.get_editor_property("post_process_settings")
settings.set_editor_properties({"override_auto_exposure_method": True,
    "auto_exposure_method": unreal.AutoExposureMethod.AEM_BASIC,
    "override_auto_exposure_min_brightness": True, "override_auto_exposure_max_brightness": True,
    "auto_exposure_min_brightness": 1.0, "auto_exposure_max_brightness": 1.0,
    "override_auto_exposure_bias": True, "auto_exposure_bias": 0.12})
camera.camera_component.set_editor_property("post_process_settings", settings)

if not levels.save_current_level():
    raise RuntimeError(f"Could not save {MAP}")
OUT.parent.mkdir(parents=True, exist_ok=True)
OUT.write_text(json.dumps({
    "$schema": f"cairnwell/audit/press-shop-pr004-support-identity-candidate-{VERSION}/v1",
    "generated_utc": datetime.now(timezone.utc).isoformat(),
    "status": "COMPACT_TWO_SIDED_IDENTITY_AUTHORED__RUNTIME_AND_FRESH_VISUAL_REGATES_REQUIRED__NOT_PROMOTED",
    "base_map": "/Game/LineBoss/Maps/LB_PressShop_PR004SupportHoistCandidate_v109",
    "map": MAP, "identity_actor_count": len(created),
    "identity_text": ["CR-30-01 | SWL 30 t", "CAIRNWELL AUTOMOTIVE | MAINTENANCE SUPPORT"],
    "moving_authority_tags": ["LB.Motion.CraneBridge", "LB.Crane.30T"],
    "fixed_camera": camera.get_actor_label(), "authority_changed": False,
    "production_map_changed": False, "promotion_authorized": False
}, indent=2), encoding="utf-8")
unreal.log(f"CAIRNWELL_PR004_SUPPORT_IDENTITY_{VERSION.upper()}_BUILD_PASS actors={len(created)}")
unreal.SystemLibrary.quit_editor()
