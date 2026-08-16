"""Install the four retained support-robot berths in a fresh direct child of v253.

The protected v253 package is never opened for writing.  Dock visuals use their
retained material overrides but not their consolidated intake collision.  Simple
non-visible side/rear collision proxies preserve the open portal and are tagged
as provisional pending detailed modular collision authoring.
"""

from datetime import datetime, timezone
import hashlib
import json
import math
from pathlib import Path

import unreal


ROOT = Path(unreal.Paths.project_dir())
BASE = "/Game/LineBoss/Maps/LB_PressShop_PlayableManagementCandidate_v253"
MAP = "/Game/LineBoss/Maps/LB_PressShop_PlayableManagementCandidate_v254"
BASE_FILE = ROOT / "Content/LineBoss/Maps/LB_PressShop_PlayableManagementCandidate_v253.umap"
MAP_FILE = ROOT / "Content/LineBoss/Maps/LB_PressShop_PlayableManagementCandidate_v254.umap"
OUT = ROOT / "Saved/Audits/SupportRobots/press_shop_support_fleet_build_v254.json"
DOCK_INVENTORY = ROOT / "Saved/Audits/SupportRobots/service_dock_actor_assets_v024.json"

MR_BP = "/Game/LineBoss/Robots/Maintenance/MR01/Candidate_v022/Blueprints/BP_LB_MR01_MaintenanceAMR_v022"
CR_BP = "/Game/LineBoss/Robots/Cleaning/CR01/Candidate_v065/Blueprints/BP_LB_CR01_CleaningAMR_v065"
CUBE = "/Engine/BasicShapes/Cube"

BERTHS = (
    {"family": "MR01", "index": 1, "root": (-6495.0, 5160.0), "robot_z": 62.5},
    {"family": "MR01", "index": 2, "root": (-5095.0, 5160.0), "robot_z": 62.5},
    {"family": "CR01", "index": 1, "root": (-1495.0, 5160.0), "robot_z": 56.0},
    {"family": "CR01", "index": 2, "root": (-295.0, 5160.0), "robot_z": 56.0},
)

LIB = unreal.EditorAssetLibrary
BLUEPRINTS = unreal.BlueprintEditorLibrary
LEVELS = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
ACTORS = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)


def sha256(path):
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest().upper()


def xyz(value):
    return [round(value.x, 4), round(value.y, 4), round(value.z, 4)]


def magnitude(value):
    return math.sqrt(value.x * value.x + value.y * value.y + value.z * value.z)


def generated_class(path):
    blueprint = LIB.load_asset(path)
    if not isinstance(blueprint, unreal.Blueprint):
        raise RuntimeError(f"Missing retained robot Blueprint {path}")
    result = BLUEPRINTS.generated_class(blueprint)
    if result is None:
        raise RuntimeError(f"Generated class unavailable {path}")
    return result


def named_component(actor, name):
    for component in actor.get_components_by_class(unreal.SceneComponent):
        if component.get_name() == name:
            return component
    raise RuntimeError(f"{actor.get_actor_label()} missing component {name}")


def restore_cr01(authority):
    mounts = authority.get_components_by_class(unreal.ChildActorComponent)
    if len(mounts) != 1:
        raise RuntimeError(f"CR01 presentation mount count is {len(mounts)}")
    child = mounts[0].get_editor_property("child_actor")
    if child is None:
        raise RuntimeError("CR01 presentation child unavailable")
    changed = 0
    for mesh_component in child.get_components_by_class(unreal.StaticMeshComponent):
        name = mesh_component.get_name()
        for suffix in ("_GEN_VARIABLE", "_0"):
            if name.endswith(suffix):
                name = name[:-len(suffix)]
        if name.startswith("Condition_Mothballed"):
            mesh_component.set_visibility(False, True)
            mesh_component.set_hidden_in_game(True, True)
            changed += 1
        elif name.startswith("Condition_Restored"):
            mesh_component.set_visibility(True, True)
            mesh_component.set_hidden_in_game(False, True)
            changed += 1
    return changed


def camera(label, location, target, fov):
    position = unreal.Vector(*location)
    actor = ACTORS.spawn_actor_from_class(unreal.CameraActor, position, unreal.Rotator())
    if actor is None:
        raise RuntimeError(f"Could not spawn {label}")
    actor.set_actor_label(label)
    actor.set_actor_rotation(
        unreal.MathLibrary.find_look_at_rotation(position, unreal.Vector(*target)), False)
    actor.camera_component.set_editor_properties({
        "field_of_view": fov,
        "aspect_ratio": 16.0 / 9.0,
        "constrain_aspect_ratio": True,
    })
    settings = actor.camera_component.get_editor_property("post_process_settings")
    settings.set_editor_properties({
        "override_auto_exposure_method": True,
        "auto_exposure_method": unreal.AutoExposureMethod.AEM_BASIC,
        "override_auto_exposure_min_brightness": True,
        "override_auto_exposure_max_brightness": True,
        "auto_exposure_min_brightness": 1.0,
        "auto_exposure_max_brightness": 1.0,
        "override_auto_exposure_bias": True,
        "auto_exposure_bias": -0.35,
    })
    actor.camera_component.set_editor_property("post_process_settings", settings)
    actor.tags = [
        unreal.Name("LB.Asset.CandidateNotPromoted"),
        unreal.Name("LB.Camera.Fixed.SupportFleet.v254"),
    ]
    return actor


if LIB.does_asset_exist(MAP):
    raise RuntimeError(f"Refusing to overwrite preserved candidate {MAP}")
if not DOCK_INVENTORY.exists():
    raise RuntimeError(f"Missing retained dock inventory {DOCK_INVENTORY}")

base_hash_before = sha256(BASE_FILE)
if not LEVELS.new_level_from_template(MAP, BASE):
    raise RuntimeError(f"Could not derive {MAP} from {BASE}")

inventory = json.loads(DOCK_INVENTORY.read_text(encoding="utf-8"))
inventory_by_family = {}
for row in inventory["actors"]:
    family = "MR01" if "MR01" in row["label"] else "CR01"
    inventory_by_family[family] = row
if set(inventory_by_family) != {"MR01", "CR01"}:
    raise RuntimeError("Retained dock inventory does not contain both families")

cube_mesh = LIB.load_asset(CUBE)
if not isinstance(cube_mesh, unreal.StaticMesh):
    raise RuntimeError("Missing engine cube for provisional collision proxies")

robot_classes = {"MR01": generated_class(MR_BP), "CR01": generated_class(CR_BP)}
rows = []
max_contact_error = 0.0
cr_restored_count = 0

for berth in BERTHS:
    family = berth["family"]
    index = berth["index"]
    root_x, root_y = berth["root"]
    unit_id = f"LB-{family}-{index:02d}"
    dock_id = f"LB-DOCK-{family}-{index:02d}"
    lineage = inventory_by_family[family]

    dock_mesh = LIB.load_asset(lineage["mesh"])
    if not isinstance(dock_mesh, unreal.StaticMesh):
        raise RuntimeError(f"Missing retained {family} dock mesh {lineage['mesh']}")
    dock = ACTORS.spawn_actor_from_class(
        unreal.StaticMeshActor, unreal.Vector(root_x, root_y, 0.0), unreal.Rotator())
    if dock is None:
        raise RuntimeError(f"Could not spawn {dock_id}")
    dock.set_actor_label(dock_id)
    dock.static_mesh_component.set_static_mesh(dock_mesh)
    for material_index, material_path in enumerate(lineage["materials"]):
        material = LIB.load_asset(material_path)
        if not isinstance(material, unreal.MaterialInterface):
            raise RuntimeError(f"Missing retained dock material {material_path}")
        dock.static_mesh_component.set_material(material_index, material)
    # Consolidated intake collision blocks its own portal; use open-portal proxies below.
    dock.static_mesh_component.set_collision_enabled(unreal.CollisionEnabled.NO_COLLISION)
    dock.static_mesh_component.set_editor_property("can_ever_affect_navigation", False)
    dock.tags = [
        unreal.Name("LB.Asset.CandidateNotPromoted"),
        unreal.Name(f"LB.SupportRobot.Dock.{family}"),
        unreal.Name(f"LB.SupportRobot.DockId.{dock_id}"),
        unreal.Name("LB.Dock.Visual.RetainedProSource"),
        unreal.Name("LB.Collision.ConsolidatedIntakeDisabled"),
    ]

    proxy_rows = []
    proxy_specs = (
        ("WestSide", -96.5, 141.5, 85.5, 67.0, 145.0, 171.0),
        ("EastSide", 96.5, 141.5, 85.5, 67.0, 145.0, 171.0),
        ("Rear", 0.0, 204.0, 85.5, 126.0, 20.0, 171.0),
    )
    for role, dx, dy, z, sx, sy, sz in proxy_specs:
        proxy = ACTORS.spawn_actor_from_class(
            unreal.StaticMeshActor, unreal.Vector(root_x + dx, root_y + dy, z), unreal.Rotator())
        if proxy is None:
            raise RuntimeError(f"Could not spawn collision proxy {dock_id}/{role}")
        proxy.set_actor_label(f"{dock_id}_Collision_{role}")
        proxy.set_actor_scale3d(unreal.Vector(sx / 100.0, sy / 100.0, sz / 100.0))
        proxy.static_mesh_component.set_static_mesh(cube_mesh)
        proxy.static_mesh_component.set_collision_enabled(unreal.CollisionEnabled.QUERY_AND_PHYSICS)
        proxy.static_mesh_component.set_collision_profile_name(unreal.Name("BlockAll"))
        proxy.static_mesh_component.set_editor_property("can_ever_affect_navigation", True)
        proxy.static_mesh_component.set_visibility(False, True)
        proxy.static_mesh_component.set_hidden_in_game(True, True)
        proxy.tags = [
            unreal.Name("LB.Asset.CandidateNotPromoted"),
            unreal.Name(f"LB.SupportRobot.DockId.{dock_id}"),
            unreal.Name("LB.Collision.Proxy.Provisional"),
            unreal.Name("LB.Navigation.Blocker"),
        ]
        proxy_rows.append({"actor": proxy.get_actor_label(), "size_cm": [sx, sy, sz]})

    robot = ACTORS.spawn_actor_from_class(
        robot_classes[family],
        unreal.Vector(root_x, root_y, berth["robot_z"]),
        unreal.Rotator(0.0, 0.0, -90.0),
    )
    if robot is None:
        raise RuntimeError(f"Could not spawn {unit_id}")
    robot.set_actor_label(unit_id)
    robot.modify()
    if not robot.configure_identity(unreal.Name(unit_id), unreal.Name(f"LB-{family}")):
        raise RuntimeError(f"Could not configure unique identity {unit_id}")
    if not robot.confirm_docked(unreal.Name(dock_id)):
        raise RuntimeError(f"Could not establish dock authority {unit_id} -> {dock_id}")
    restored_count = restore_cr01(robot) if family == "CR01" else 0
    cr_restored_count += restored_count
    robot.tags = [
        unreal.Name("LB.Asset.CandidateNotPromoted"),
        unreal.Name(f"LB.SupportRobot.{family}"),
        unreal.Name(f"LB.SupportRobot.UnitId.{unit_id}"),
        unreal.Name(f"LB.SupportRobot.DockId.{dock_id}"),
        unreal.Name("LB.Runtime.Authority.RetainedActualRobot"),
    ]

    contact_names = (
        ("left", "PVT_DockCharge_L" if family == "MR01" else "PVT_DockChargeContact_L", -12.0),
        ("right", "PVT_DockCharge_R" if family == "MR01" else "PVT_DockChargeContact_R", 12.0),
    )
    contacts = []
    for side, component_name, dx in contact_names:
        expected = unreal.Vector(root_x + dx, root_y + 73.5, 34.0)
        actual = named_component(robot, component_name).get_world_location()
        error = actual - expected
        error_cm = magnitude(error)
        max_contact_error = max(max_contact_error, error_cm)
        contacts.append({
            "side": side,
            "component": component_name,
            "expected_world_cm": xyz(expected),
            "actual_world_cm": xyz(actual),
            "error_magnitude_cm": round(error_cm, 5),
        })

    origin, extent = robot.get_actor_bounds(False)
    rows.append({
        "family": family,
        "unit_id": unit_id,
        "dock_id": dock_id,
        "root_cm": [root_x, root_y, berth["robot_z"]],
        "orientation": "straight reverse / rear-first; robot front faces world -Y",
        "identity_configured": True,
        "docked_authority_established": True,
        "robot_bounds_origin_cm": xyz(origin),
        "robot_bounds_size_cm": xyz(extent * 2.0),
        "contact_alignment": contacts,
        "collision_proxies": proxy_rows,
    })

cameras = [
    camera("LB_SUPPORT_FLEET_CAM_MR01_v254", (-7600.0, 3600.0, 520.0), (-5800.0, 5160.0, 85.0), 52.0),
    camera("LB_SUPPORT_FLEET_CAM_CR01_v254", (-2600.0, 3600.0, 520.0), (-900.0, 5160.0, 80.0), 52.0),
    camera("LB_SUPPORT_FLEET_CAM_OVERVIEW_v254", (-3650.0, 2750.0, 1550.0), (-3300.0, 5000.0, 30.0), 62.0),
]

unreal.AutomationUtilsBlueprintLibrary.finish_all_asset_compilation()
if not LEVELS.save_current_level():
    raise RuntimeError(f"Could not save {MAP}")

base_hash_after = sha256(BASE_FILE)
if base_hash_before != base_hash_after:
    raise RuntimeError("Protected v253 changed while building v254")
if max_contact_error > 0.1:
    raise RuntimeError(f"Dock contact alignment failed: {max_contact_error:.5f} cm")

payload = {
    "$schema": "cairnwell/audit/press-shop-support-fleet-build-v254/v1",
    "generated_utc": datetime.now(timezone.utc).isoformat(),
    "status": "PASS__FOUR_INDEPENDENT_RETAINED_ROBOTS_AND_BERTHS_INSTALLED__FRESH_COLLISION_NAV_RUNTIME_VISUAL_GATES_REQUIRED__NOT_PROMOTED",
    "base": BASE,
    "map": MAP,
    "base_sha256_before": base_hash_before,
    "base_sha256_after": base_hash_after,
    "map_sha256": sha256(MAP_FILE),
    "fleet": {"MR01": 2, "CR01": 2},
    "berths": {"MR01": 2, "CR01": 2},
    "robots": rows,
    "maximum_contact_error_cm": round(max_contact_error, 5),
    "cr01_restored_condition_component_count": cr_restored_count,
    "fixed_cameras": [actor.get_actor_label() for actor in cameras],
    "collision_strategy": "Retained dock visual has no consolidated intake collision; three hidden open-portal BlockAll proxies per berth are provisional and navigation-affecting.",
    "holds": [
        "Detailed door, drawer, probe and tool-rack service sweeps remain open.",
        "Provisional dock collision proxies require collision/nav regression before retention.",
        "The four robots are docked installation authorities, not yet certified dispatch routes.",
        "Fresh unobstructed fixed-camera review is required before retention or promotion.",
    ],
    "promotion_authorized": False,
}
OUT.parent.mkdir(parents=True, exist_ok=True)
OUT.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
unreal.log("LINE_BOSS_PRESS_SHOP_SUPPORT_FLEET_V254_BUILD_PASS")
unreal.SystemLibrary.quit_editor()
