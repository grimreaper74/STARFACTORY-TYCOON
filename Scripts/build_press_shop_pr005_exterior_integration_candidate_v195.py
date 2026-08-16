"""Fit Candidate_v002 exterior shell to retained PR005 v053 without replacing runtime authority."""

import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path

import unreal


ROOT = Path(unreal.Paths.project_dir())
BASE = "/Game/LineBoss/Maps/LB_PressShop_PR005LogisticsCandidate_v053"
MAP = "/Game/LineBoss/Maps/LB_PressShop_PR005ExteriorIntegrationCandidate_v195"
BASE_PACKAGE = ROOT / "Content/LineBoss/Maps/LB_PressShop_PR005LogisticsCandidate_v053.umap"
MANIFEST_PATH = ROOT / "SourceAssets/Candidate/PressShop/PR005/UnrealDerived_v003/PR005_EXTERIOR_ENCLOSURE_UNREAL_DERIVED_MANIFEST_v003.json"
MESH_ROOT = "/Game/LineBoss/Candidates/PressShop/PR005/ExteriorEnclosure_v003/Meshes"
OUT = ROOT / "Saved/Audits/PressShopIntegration/press_shop_pr005_exterior_integration_build_v195.json"
DATUM = unreal.Vector(-4000.0, -2000.0, 0.0)
YAW = 90.0
INCLUDED = {
    "SM_CA_MW_PR005_EnclosureShell_Static_v003",
    "SM_CA_MW_PR005_ServiceDoorOperator_Mover_v003",
    "SM_CA_MW_PR005_ServiceDoorUtilities_Mover_v003",
}
EXCLUDED_PRESENTATION = {
    "SM_CA_MW_PR005_PinchRollLower_ReadabilityMover_v003",
    "SM_CA_MW_PR005_PinchRollUpper_ReadabilityMover_v003",
    "SM_CA_MW_PR005_ThreaderTable_ReadabilityMover_v003",
    "SM_CA_MW_PR005_StripPathReadability_v003",
}
library = unreal.EditorAssetLibrary
levels = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
actors_api = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)


def sha256(path):
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def source_pivot_to_world(pivot_m):
    # Derived FBXs preserve Blender +X and import Blender +Y as Unreal -Y.
    # Unreal yaw +90 maps imported -Y to world +X, matching retained PR005 flow.
    px, py, pz = [float(value) for value in pivot_m]
    imported = unreal.Vector(px * 100.0, -py * 100.0, pz * 100.0)
    rotated = unreal.MathLibrary.rotate_angle_axis(imported, YAW, unreal.Vector(0.0, 0.0, 1.0))
    return DATUM + rotated


if library.does_asset_exist(MAP):
    raise RuntimeError(f"refusing to overwrite {MAP}")
manifest = json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))
base_hash_before = sha256(BASE_PACKAGE)
if not levels.new_level_from_template(MAP, BASE):
    raise RuntimeError(f"could not clone {BASE}")

common_tags = [
    "LB.Asset.Candidate.v195",
    "LB.Asset.CandidateNotPromoted",
    "LB.PR005.ExteriorEnclosure.IntegrationStudy",
    "LB.Authority.PR005.NativeRuntimeUnchanged",
]
created = []
failures = []
for row in manifest["assets"]:
    name = row["asset_name"]
    if name not in INCLUDED:
        continue
    mesh = library.load_asset(f"{MESH_ROOT}/{name}")
    if not isinstance(mesh, unreal.StaticMesh):
        failures.append(f"missing mesh {name}")
        continue
    rotation = unreal.Rotator()
    rotation.set_editor_properties({"pitch": 0.0, "yaw": YAW, "roll": 0.0})
    actor = actors_api.spawn_actor_from_class(unreal.StaticMeshActor, source_pivot_to_world(row["pivot_m"]), rotation)
    actor.set_actor_label("LB_PR005_V195_" + name.replace("SM_CA_MW_PR005_", ""))
    actor.static_mesh_component.set_static_mesh(mesh)
    actor.static_mesh_component.set_mobility(unreal.ComponentMobility.STATIC)
    actor.static_mesh_component.set_collision_enabled(unreal.CollisionEnabled.NO_COLLISION)
    actor.static_mesh_component.set_collision_profile_name(unreal.Name("NoCollision"))
    actor.static_mesh_component.set_editor_property("can_ever_affect_navigation", False)
    actor.tags = [unreal.Name(value) for value in common_tags + ["LB.PR005.ExteriorModule.VisualFitOnly"]]
    created.append(actor)

# Restrained internal task lighting; inherited hall lighting remains authoritative.
lights = []
for index, x in enumerate((-4300.0, -4000.0, -3700.0), 1):
    light = actors_api.spawn_actor_from_class(unreal.RectLight, unreal.Vector(x, -2000.0, 315.0), unreal.Rotator(-90.0, 0.0, 0.0))
    light.set_actor_label(f"LB_PR005_V195_InternalTaskLED_{index:02d}")
    light.get_component_by_class(unreal.RectLightComponent).set_editor_properties({
        "intensity": 12.0,
        "source_width": 210.0,
        "source_height": 55.0,
        "attenuation_radius": 430.0,
        "cast_shadows": False,
        "light_color": unreal.Color(214, 224, 226, 255),
    })
    light.tags = [unreal.Name(value) for value in common_tags + ["LB.Environment.Light.InternalTask"]]
    lights.append(light)


def camera(label, location, target, fov):
    actor = actors_api.spawn_actor_from_class(unreal.CameraActor, unreal.Vector(*location), unreal.Rotator())
    actor.set_actor_label("LB_PR005_V195_CAM_" + label)
    actor.set_actor_rotation(unreal.MathLibrary.find_look_at_rotation(actor.get_actor_location(), unreal.Vector(*target)), False)
    actor.camera_component.set_editor_properties({"field_of_view": fov, "aspect_ratio": 16.0 / 9.0, "constrain_aspect_ratio": True})
    actor.tags = [unreal.Name(value) for value in common_tags + ["LB.Camera.Validation", "LB.Camera.Fixed.PR005Exterior.v195"]]
    return actor


cameras = [
    camera("OperatorPlayer", (-4550.0, -950.0, 245.0), (-3990.0, -2000.0, 140.0), 48.0),
    camera("OperatorElevated", (-4750.0, -760.0, 620.0), (-3975.0, -2000.0, 135.0), 52.0),
    camera("ServiceSide", (-3500.0, -3150.0, 285.0), (-3925.0, -2000.0, 145.0), 48.0),
    camera("ProcessFlow", (-5000.0, -900.0, 720.0), (-3980.0, -2000.0, 125.0), 56.0),
]

if len(created) != 3:
    failures.append(f"expected 3 exterior modules, found {len(created)}")
shell_actor = next((actor for actor in created if "EnclosureShell_Static" in actor.get_actor_label()), None)
if shell_actor is None:
    failures.append("shell actor missing")
else:
    origin, extent = shell_actor.get_actor_bounds(False)
    actual_min = origin - extent
    actual_max = origin + extent
    expected_min = unreal.Vector(-4518.0, -2289.35, 0.0)
    expected_max = unreal.Vector(-3482.0, -1713.05, 355.0)
    deltas = [
        actual_min.x - expected_min.x, actual_min.y - expected_min.y, actual_min.z - expected_min.z,
        actual_max.x - expected_max.x, actual_max.y - expected_max.y, actual_max.z - expected_max.z,
    ]
    if max(abs(value) for value in deltas) > 0.2:
        failures.append(f"upright flow-aligned shell bounds drift cm={deltas}")
if any(row["asset_name"] in EXCLUDED_PRESENTATION for row in manifest["assets"] if row["asset_name"] in INCLUDED):
    failures.append("presentation-only runtime witness included")
if not levels.save_current_level():
    failures.append("could not save v195")
base_hash_after = sha256(BASE_PACKAGE)
if base_hash_after != base_hash_before:
    failures.append("protected v053 package changed")

payload = {
    "$schema": "cairnwell/audit/press-shop-pr005-exterior-integration-build-v195/v1",
    "generated_utc": datetime.now(timezone.utc).isoformat(),
    "status": "PASS__V053_DERIVED_UPRIGHT_FLOW_ALIGNED_EXTERIOR_VISUAL_FIT_BUILT__FIXED_CAMERA_AND_RUNTIME_GATES_REQUIRED__NOT_PROMOTED" if not failures else "FAIL__PR005_V195_BUILD__NOT_PROMOTED",
    "base_map": BASE,
    "map": MAP,
    "protected_base_sha256_before": base_hash_before,
    "protected_base_sha256_after": base_hash_after,
    "native_pr005_datum_cm": list(DATUM.to_tuple()),
    "source_to_world_mapping": "Candidate source +Y material flow -> retained world +X; Candidate source +X across strip -> retained world +Y",
    "included_modules": [actor.get_actor_label() for actor in created],
    "excluded_modules": sorted({row["asset_name"] for row in manifest["assets"]} - INCLUDED),
    "presentation_only_movers_included": False,
    "duplicate_hmi_included": False,
    "native_runtime_authority_replaced": False,
    "collision_navigation_scope": "OPEN__VISUAL_FIT_ACTORS_NO_COLLISION_AND_NO_NAV_EFFECT",
    "internal_task_lights": [actor.get_actor_label() for actor in lights],
    "fixed_cameras": [actor.get_actor_label() for actor in cameras],
    "world_placement_basis": "DERIVED_FROM_RETAINED_V053_NATIVE_PR005_DATUM_AND_EXACT_CANDIDATE_PORT_ALIGNMENT",
    "planning_10400_versus_11500_relationship": "TBC_NOT_INVENTED",
    "promotion_authorized": False,
    "failures": failures,
}
OUT.parent.mkdir(parents=True, exist_ok=True)
OUT.write_text(json.dumps(payload, indent=2), encoding="utf-8")
print(json.dumps({"status": payload["status"], "created": payload["included_modules"], "failures": failures}, indent=2))
if failures:
    raise RuntimeError("; ".join(failures))
