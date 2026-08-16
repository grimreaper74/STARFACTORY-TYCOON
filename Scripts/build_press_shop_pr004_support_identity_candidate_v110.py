"""Add readable two-sided CR-30-01 bridge identity in isolated v110."""
from pathlib import Path
from datetime import datetime, timezone
import json
import unreal

MAP = "/Game/LineBoss/Maps/LB_PressShop_PR004SupportIdentityCandidate_v110"
OUT = Path(unreal.Paths.project_saved_dir()) / "Audits/press_shop_pr004_support_identity_candidate_v110.json"
PREFIX = "LB_PR004_V110_"
levels = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
actors = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
lib = unreal.EditorAssetLibrary
if not levels.load_level(MAP):
    raise RuntimeError(f"Could not load {MAP}")
for actor in list(actors.get_all_level_actors()):
    if actor.get_actor_label().startswith(PREFIX):
        actors.destroy_actor(actor)

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
          "LB.Asset.Candidate.v110", "LB.Asset.CandidateNotPromoted")

def cube(label, location, dimensions, material):
    actor = actors.spawn_actor_from_class(unreal.StaticMeshActor, unreal.Vector(*location), unreal.Rotator())
    actor.set_actor_label(PREFIX + label)
    actor.tags = names(*common)
    actor.static_mesh_component.set_static_mesh(cube_mesh)
    actor.set_actor_scale3d(unreal.Vector(dimensions[0]/100.0, dimensions[1]/100.0, dimensions[2]/100.0))
    actor.static_mesh_component.set_material(0, material)
    actor.static_mesh_component.set_mobility(unreal.ComponentMobility.MOVABLE)
    actor.static_mesh_component.set_collision_enabled(unreal.CollisionEnabled.NO_COLLISION)
    actor.static_mesh_component.set_editor_property("can_ever_affect_navigation", False)
    return actor

def text(label, location, rotation, body, size, material):
    actor = actors.spawn_actor_from_class(unreal.TextRenderActor, unreal.Vector(*location), unreal.Rotator(*rotation))
    actor.set_actor_label(PREFIX + label)
    actor.tags = names(*common)
    actor.text_render.set_editor_properties({
        "text": body, "world_size": size,
        "horizontal_alignment": unreal.HorizTextAligment.EHTA_CENTER,
        "vertical_alignment": unreal.VerticalTextAligment.EVRTA_TEXT_CENTER
    })
    actor.text_render.set_material(0, material)
    actor.text_render.set_mobility(unreal.ComponentMobility.MOVABLE)
    actor.text_render.set_collision_enabled(unreal.CollisionEnabled.NO_COLLISION)
    actor.text_render.set_editor_property("can_ever_affect_navigation", False)
    return actor

created = []
for side, x, face_x, yaw in (("East", -9020.0, -9013.0, 0.0), ("West", -9180.0, -9187.0, 180.0)):
    created.append(cube(f"30T_{side}Identity_Back", (x, -2415.0, 1515.0), (7.0, 720.0, 122.0), dark))
    created.append(cube(f"30T_{side}Identity_GreenBand", (face_x, -2690.0, 1515.0), (3.0, 145.0, 104.0), green))
    for end_y in (-2748.0, -2082.0):
        created.append(cube(f"30T_{side}Identity_YellowEnd_{end_y}", (face_x, end_y, 1515.0), (3.0, 18.0, 112.0), yellow))
    created.append(text(f"30T_{side}Identity_Main", (face_x + (2.0 if side == "East" else -2.0), -2360.0, 1536.0),
                        (0.0, 0.0, yaw), "CAIRNWELL AUTOMOTIVE  |  CR-30-01  |  SWL 30 t", 30.0, ivory))
    created.append(text(f"30T_{side}Identity_Role", (face_x + (2.0 if side == "East" else -2.0), -2360.0, 1488.0),
                        (0.0, 0.0, yaw), "MAINTENANCE SUPPORT", 20.0, green))

camera = actors.spawn_actor_from_class(unreal.CameraActor, unreal.Vector(-6750.0, 120.0, 1080.0), unreal.Rotator())
camera.set_actor_label(PREFIX + "CAM_SupportFleetIdentityReadable")
camera.tags = names("LB.Camera.Validation", "LB.Camera.Fixed.SupportIdentity.v110",
                    "LB.Asset.Candidate.v110", "LB.Asset.CandidateNotPromoted")
camera.set_actor_rotation(unreal.MathLibrary.find_look_at_rotation(camera.get_actor_location(), unreal.Vector(-9070.0, -2450.0, 1480.0)), False)
camera.camera_component.set_editor_properties({"field_of_view": 42.0, "aspect_ratio": 16.0/9.0,
    "constrain_aspect_ratio": True, "post_process_blend_weight": 1.0})
settings = camera.camera_component.get_editor_property("post_process_settings")
settings.set_editor_properties({"override_auto_exposure_method": True,
    "auto_exposure_method": unreal.AutoExposureMethod.AEM_BASIC,
    "override_auto_exposure_min_brightness": True, "override_auto_exposure_max_brightness": True,
    "auto_exposure_min_brightness": 1.0, "auto_exposure_max_brightness": 1.0,
    "override_auto_exposure_bias": True, "auto_exposure_bias": 0.04})
camera.camera_component.set_editor_property("post_process_settings", settings)

if not levels.save_current_level():
    raise RuntimeError(f"Could not save {MAP}")
payload = {
    "$schema": "cairnwell/audit/press-shop-pr004-support-identity-candidate-v110/v1",
    "generated_utc": datetime.now(timezone.utc).isoformat(),
    "status": "READABLE_TWO_SIDED_IDENTITY_AUTHORED__RUNTIME_AND_FRESH_VISUAL_REGATES_REQUIRED__NOT_PROMOTED",
    "base_map": "/Game/LineBoss/Maps/LB_PressShop_PR004SupportHoistCandidate_v109",
    "map": MAP, "identity_actor_count": len(created),
    "identity_text": ["CAIRNWELL AUTOMOTIVE | CR-30-01 | SWL 30 t", "MAINTENANCE SUPPORT"],
    "moving_authority_tags": ["LB.Motion.CraneBridge", "LB.Crane.30T"],
    "fixed_camera": camera.get_actor_label(),
    "authority_changed": False, "production_map_changed": False,
    "promotion_authorized": False
}
OUT.parent.mkdir(parents=True, exist_ok=True)
OUT.write_text(json.dumps(payload, indent=2), encoding="utf-8")
unreal.log(f"CAIRNWELL_PR004_SUPPORT_IDENTITY_V110_BUILD_PASS actors={len(created)}")
unreal.SystemLibrary.quit_editor()
