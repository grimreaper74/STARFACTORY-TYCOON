"""Add fabricated hook/reeving detail and balanced hall lighting to isolated v032."""

import json
from datetime import datetime, timezone
from pathlib import Path

import unreal


BASE = "/Game/LineBoss/Maps/LB_PressShop_PR004CraneFabricationCandidate_v031"
MAP = "/Game/LineBoss/Maps/LB_PressShop_PR004CraneLiftingCandidate_v032"
OUT = Path(unreal.Paths.project_saved_dir()) / "Audits/press_shop_pr004_crane_lifting_candidate_v032.json"
PREFIX = "LB_PR004_V032_"
levels = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
actors = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
library = unreal.EditorAssetLibrary
CUBE = unreal.load_asset("/Engine/BasicShapes/Cube")
CYLINDER = unreal.load_asset("/Engine/BasicShapes/Cylinder")
YELLOW = library.load_asset("/Game/LineBoss/IndustrialKit/MaterialHandling/BridgeCrane/Candidate_v031/MI_LB_Crane_RAL1023_Aged_v031")
DARK = library.load_asset("/Game/LineBoss/IndustrialKit/MaterialHandling/BridgeCrane/Candidate_v031/MI_LB_Crane_DarkSteel_v031")
STEEL = library.load_asset("/Game/LineBoss/IndustrialKit/MaterialHandling/BridgeCrane/Candidate_v031/MI_LB_Crane_ExposedSteel_v031")
RUBBER = library.load_asset("/Game/LineBoss/Stations/Press/PR005/Candidate_v001/Materials/M_PR005_Rubber")
if not levels.load_level(MAP):
    raise RuntimeError(f"Could not load {MAP}")
if any(asset is None for asset in (CUBE, CYLINDER, YELLOW, DARK, STEEL, RUBBER)):
    raise RuntimeError("Missing v032 fabrication dependency")
for actor in list(actors.get_all_level_actors()):
    if actor.get_actor_label().startswith(PREFIX):
        actors.destroy_actor(actor)


def tag_list(*values):
    return [unreal.Name(value) for value in values]


def configure(actor, mesh, material, tags):
    actor.tags = tag_list(*tags, "LB.Asset.Candidate.v032", "LB.Asset.CandidateNotPromoted")
    component = actor.static_mesh_component
    component.set_static_mesh(mesh)
    component.set_material(0, material)
    component.set_mobility(unreal.ComponentMobility.MOVABLE)
    component.set_collision_enabled(unreal.CollisionEnabled.NO_COLLISION)
    component.set_collision_profile_name(unreal.Name("NoCollision"))
    component.set_editor_property("can_ever_affect_navigation", False)
    return actor


def cube(label, location, dimensions, material, tags):
    actor = actors.spawn_actor_from_class(unreal.StaticMeshActor, unreal.Vector(*location), unreal.Rotator())
    actor.set_actor_label(PREFIX + label)
    actor.set_actor_scale3d(unreal.Vector(*(value / 100.0 for value in dimensions)))
    return configure(actor, CUBE, material, tags)


def cylinder_between(label, start, end, radius, material, tags):
    a, b = unreal.Vector(*start), unreal.Vector(*end)
    delta = b - a
    actor = actors.spawn_actor_from_class(unreal.StaticMeshActor, (a + b) * 0.5, unreal.Rotator())
    actor.set_actor_label(PREFIX + label)
    actor.set_actor_rotation(unreal.MathLibrary.make_rot_from_z(delta), False)
    actor.set_actor_scale3d(unreal.Vector(radius / 50.0, radius / 50.0, delta.length() / 100.0))
    return configure(actor, CYLINDER, material, tags)


hook_tags = ("LB.Motion.CHook", "LB.Crane.40T", "LB.Module.CHookFabrication")
hoist_tags = ("LB.Motion.Hoist", "LB.Crane.40T", "LB.Module.HoistFabrication")
reeving_tags = ("LB.Motion.Hoist", "LB.Crane.40T", "LB.Module.HoistReeving")

# Keep the audited hook datum at Z=820 and load centre at Z=761. These pieces
# dress that authority without changing its physical pickup/drop relationship.
hook_parts = []
for side, y in (("W", -2041.0), ("E", -1959.0)):
    hook_parts.append(cube(f"40T_YokeCheek_{side}", (-5050.0, y, 910.0),
                           (92.0, 9.0, 172.0), DARK, hook_tags))
hook_parts.extend([
    cube("40T_YokeGusset_W", (-5050.0, -2036.0, 831.0), (72.0, 10.0, 42.0), YELLOW, hook_tags),
    cube("40T_YokeGusset_E", (-5050.0, -1964.0, 831.0), (72.0, 10.0, 42.0), YELLOW, hook_tags),
    cylinder_between("40T_YokeUpperPin", (-5050.0, -2054.0, 966.0), (-5050.0, -1946.0, 966.0), 13.0, STEEL, hook_tags),
    cylinder_between("40T_YokeLowerPin", (-5050.0, -2054.0, 850.0), (-5050.0, -1946.0, 850.0), 12.0, STEEL, hook_tags),
    cylinder_between("40T_YokeSheave", (-5050.0, -2037.0, 934.0), (-5050.0, -1963.0, 934.0), 38.0, STEEL, hook_tags),
    cube("40T_YokeCrown", (-5050.0, -2000.0, 1003.0), (96.0, 96.0, 28.0), YELLOW, hook_tags),
    # These low-centred pieces follow the same hoist delta but deliberately do
    # not carry LB.Motion.CHook: native discovery defines the hook datum as the
    # lowest CHook-tagged actor origin, which must remain the original Z=820.
    cylinder_between("40T_BoreLanceSteel", (-5158.0, -2000.0, 761.0), (-4950.0, -2000.0, 761.0), 20.0, STEEL, hoist_tags),
    cylinder_between("40T_BoreLancePad", (-5142.0, -2000.0, 761.0), (-4965.0, -2000.0, 761.0), 25.0, RUBBER, hoist_tags),
    cylinder_between("40T_BoreLanceNose", (-5165.0, -2000.0, 761.0), (-5142.0, -2000.0, 761.0), 22.0, YELLOW, hoist_tags),
])

# Four separated wire-rope falls make the lifting path readable. Reeving-tagged
# cylinders retain a fixed top and change length through native crane authority.
reeving_parts = []
for index, (x, y) in enumerate(((-5084.0, -2024.0), (-5016.0, -2024.0),
                                (-5084.0, -1976.0), (-5016.0, -1976.0)), 1):
    reeving_parts.append(cylinder_between(
        f"40T_ReevingFall_{index}", (x, y, 1005.0), (x, y, 1565.0),
        1.8, DARK, reeving_tags))

# Refinish inherited working hook and hoist materials without altering assets.
for actor in actors.get_all_level_actors():
    label = actor.get_actor_label()
    component = actor.get_component_by_class(unreal.StaticMeshComponent)
    if component is None:
        continue
    if label == "LB_INT_FRONT_40T_CHook":
        for index, material in enumerate((YELLOW, RUBBER, DARK, STEEL, YELLOW)):
            component.set_material(index, material)
    elif label == "LB_INT_FRONT_40T_HoistBlock":
        for index, material in enumerate((YELLOW, DARK, STEEL)):
            component.set_material(index, material)

# Restore useful mid-level illumination after v031 removed the clipped hot pool.
light_changes = []
for actor in actors.get_all_level_actors():
    label = actor.get_actor_label()
    light = actor.get_component_by_class(unreal.LightComponent)
    if light is None or not label.startswith("LB_INT_FRONT_FactoryFill_"):
        continue
    old = float(light.get_editor_property("intensity"))
    number = int(label.rsplit("_", 1)[-1])
    new = 820.0 if number in (10, 11, 12) else 560.0
    light.set_editor_property("intensity", new)
    light_changes.append({"actor": label, "old": old, "new": new})

for index, (location, target, intensity) in enumerate((
    ((-6800.0, -2600.0, 1280.0), (-6800.0, -2600.0, 250.0), 750.0),
    ((-5050.0, -2550.0, 1260.0), (-5050.0, -2000.0, 300.0), 1100.0),
    ((-3500.0, -2100.0, 1250.0), (-4450.0, -1900.0, 260.0), 700.0),
), 1):
    light = actors.spawn_actor_from_class(unreal.SpotLight, unreal.Vector(*location), unreal.Rotator())
    light.set_actor_label(PREFIX + f"HallTaskFill_{index:02d}")
    light.tags = tag_list("LB.Lighting.Candidate", "LB.Asset.Candidate.v032", "LB.Asset.CandidateNotPromoted")
    light.set_actor_rotation(unreal.MathLibrary.find_look_at_rotation(light.get_actor_location(), unreal.Vector(*target)), False)
    light.spot_light_component.set_editor_properties({
        "intensity": intensity, "attenuation_radius": 3200.0,
        "inner_cone_angle": 42.0, "outer_cone_angle": 78.0,
        "source_radius": 80.0, "soft_source_radius": 140.0,
        "cast_shadows": False, "light_color": unreal.Color(220, 231, 242, 255),
    })

for actor in list(actors.get_all_level_actors()):
    if actor.get_actor_label().startswith(PREFIX + "CAM_"):
        actors.destroy_actor(actor)


def camera(label, location, target, fov, bias):
    actor = actors.spawn_actor_from_class(unreal.CameraActor, unreal.Vector(*location), unreal.Rotator())
    actor.set_actor_label(PREFIX + "CAM_" + label)
    actor.tags = tag_list("LB.Camera.Validation", "LB.Camera.Fixed.PR004Crane.v032",
                          "LB.Asset.Candidate.v032", "LB.Asset.CandidateNotPromoted")
    actor.set_actor_rotation(unreal.MathLibrary.find_look_at_rotation(actor.get_actor_location(), unreal.Vector(*target)), False)
    component = actor.camera_component
    component.set_editor_properties({"field_of_view": fov, "aspect_ratio": 16.0 / 9.0,
                                     "constrain_aspect_ratio": True, "post_process_blend_weight": 1.0})
    settings = component.get_editor_property("post_process_settings")
    settings.set_editor_properties({
        "override_auto_exposure_method": True, "auto_exposure_method": unreal.AutoExposureMethod.AEM_BASIC,
        "override_auto_exposure_min_brightness": True, "override_auto_exposure_max_brightness": True,
        "auto_exposure_min_brightness": 1.0, "auto_exposure_max_brightness": 1.0,
        "override_auto_exposure_bias": True, "auto_exposure_bias": bias,
    })
    component.set_editor_property("post_process_settings", settings)
    return actor


cameras = [
    camera("CraneFullSpanEast", (-2300.0, -3000.0, 1040.0), (-5050.0, -2415.0, 1450.0), 70.0, -0.10),
    camera("CHookFabrication", (-4100.0, -900.0, 910.0), (-5050.0, -1850.0, 790.0), 36.0, 0.15),
    camera("PR004Deposit", (-5850.0, -330.0, 720.0), (-5050.0, -2000.0, 210.0), 44.0, 0.05),
]

if not levels.save_current_level():
    raise RuntimeError(f"Could not save {MAP}")
payload = {
    "$schema": "line-boss/audit/press-shop-pr004-crane-lifting-candidate-v032/v1",
    "generated_utc": datetime.now(timezone.utc).isoformat(),
    "status": "HOOK_REEVING_LIGHTING_REWORK_BUILT__REGATES_REQUIRED__NOT_PROMOTED",
    "base_map": BASE, "map": MAP, "hook_fabrication_actor_count": len(hook_parts),
    "new_reeving_fall_count": len(reeving_parts), "light_changes": light_changes,
    "task_fill_count": 3, "fixed_cameras": [actor.get_actor_label() for actor in cameras],
    "bridge_span_cm_unchanged": 6210.0, "hook_datum_z_cm_unchanged": 820.0,
    "load_centre_below_hook_cm_unchanged": 59.0, "promotion_authorized": False,
}
OUT.parent.mkdir(parents=True, exist_ok=True)
OUT.write_text(json.dumps(payload, indent=2), encoding="utf-8")
unreal.log(f"LINE_BOSS_PR004_CRANE_V032_BUILD_PASS hook_parts={len(hook_parts)} reeving={len(reeving_parts)} map={MAP}")
unreal.SystemLibrary.quit_editor()
