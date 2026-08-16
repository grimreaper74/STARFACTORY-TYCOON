"""Build PR005 v196 from retained v053 using the native cage as authority."""

import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path

import unreal


ROOT = Path(unreal.Paths.project_dir())
BASE = "/Game/LineBoss/Maps/LB_PressShop_PR005LogisticsCandidate_v053"
MAP = "/Game/LineBoss/Maps/LB_PressShop_PR005RuntimeCageInfillCandidate_v196"
BASE_PACKAGE = ROOT / "Content/LineBoss/Maps/LB_PressShop_PR005LogisticsCandidate_v053.umap"
MESH_PATH = "/Game/LineBoss/Candidates/PressShop/PR005/RuntimeCageInfill_v005/Meshes/SM_CA_MW_PR005_RuntimeCageInfill_Static_v005"
OUT = ROOT / "Saved/Audits/PressShopIntegration/press_shop_pr005_runtime_cage_infill_build_v196.json"
DATUM = unreal.Vector(-4000.0, -2000.0, 0.0)
library = unreal.EditorAssetLibrary
levels = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
actors_api = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)


def sha256(path):
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def bounds(actor):
    origin, extent = actor.get_actor_bounds(False)
    return origin - extent, origin + extent


def overlaps(a_min, a_max, b_min, b_max):
    return all((a_min[i] < b_max[i] and a_max[i] > b_min[i]) for i in range(3))


if library.does_asset_exist(MAP):
    raise RuntimeError(f"refusing to overwrite {MAP}")
mesh = library.load_asset(MESH_PATH)
if not isinstance(mesh, unreal.StaticMesh):
    raise RuntimeError(f"missing {MESH_PATH}")
base_hash_before = sha256(BASE_PACKAGE)
if not levels.new_level_from_template(MAP, BASE):
    raise RuntimeError(f"could not clone {BASE}")

all_before = actors_api.get_all_level_actors()
guard_labels = {
    "LB_INT_PR005_GuardingHMI_Static",
    "LB_INT_PR005_GuardingHMI_PR-005_MaintenanceSlidingGateMover",
    "LB_INT_PR005_GuardingHMI_PR-005_OperatorGateMover",
    "LB_INT_PR005_GuardingHMI_PR-005_HMIRearServiceDoorMover",
}
guards = {actor.get_actor_label(): actor for actor in all_before if actor.get_actor_label() in guard_labels}
failures = []
if set(guards) != guard_labels:
    failures.append(f"missing native guard actors {sorted(guard_labels - set(guards))}")

# Map established source +Y flow to retained world +X.
rotation = unreal.Rotator()
rotation.set_editor_properties({"pitch": 0.0, "yaw": 90.0, "roll": 0.0})
infill = actors_api.spawn_actor_from_class(unreal.StaticMeshActor, DATUM, rotation)
infill.set_actor_label("LB_PR005_V196_RuntimeCageInfill_Static_v005")
infill.static_mesh_component.set_static_mesh(mesh)
infill.static_mesh_component.set_mobility(unreal.ComponentMobility.STATIC)
infill.static_mesh_component.set_collision_enabled(unreal.CollisionEnabled.NO_COLLISION)
infill.static_mesh_component.set_collision_profile_name(unreal.Name("NoCollision"))
infill.static_mesh_component.set_editor_property("can_ever_affect_navigation", False)
infill.tags = [unreal.Name(value) for value in (
    "LB.Asset.Candidate.v196", "LB.Asset.CandidateNotPromoted",
    "LB.Station.PR-005", "LB.PR005.RuntimeCage.VisualInfill",
    "LB.Authority.PR005.NativeRuntimeUnchanged", "LB.Placement.DerivedFromRetainedV053Datum",
)]

# Reuse the already audited v003 material response; do not generate duplicate materials.
material_map = {
    "CA_MW_FoundryCharcoal": "/Game/LineBoss/Candidates/PressShop/PR005/ExteriorEnclosure_v003/Materials/M_CA_MW_PR005_FoundryCharcoal_v003",
    "CA_MW_ServiceGrey": "/Game/LineBoss/Candidates/PressShop/PR005/ExteriorEnclosure_v003/Materials/M_CA_MW_PR005_ServiceGrey_v003",
    "CA_MW_LaminatedInspectionGlass": "/Game/LineBoss/Candidates/PressShop/PR005/ExteriorEnclosure_v003/Materials/M_CA_MW_PR005_LaminatedInspectionGlass_v003",
    "CA_MW_CairnwellGreen": "/Game/LineBoss/Candidates/PressShop/PR005/ExteriorEnclosure_v003/Materials/M_CA_MW_PR005_CairnwellGreen_v003",
    "CA_MW_SafetyYellow": "/Game/LineBoss/Candidates/PressShop/PR005/ExteriorEnclosure_v003/Materials/M_CA_MW_PR005_SafetyYellow_v003",
    "CA_MW_IdentityWhite": "/Game/LineBoss/Candidates/PressShop/PR005/ExteriorEnclosure_v003/Materials/M_CA_MW_PR005_IdentityWhite_v003",
}
assigned_materials = []
for index, slot in enumerate(mesh.get_editor_property("static_materials")):
    slot_name = str(slot.material_slot_name)
    path = material_map.get(slot_name)
    material = library.load_asset(path) if path else None
    if material is None:
        failures.append(f"material missing for slot {slot_name}")
    else:
        infill.static_mesh_component.set_material(index, material)
        assigned_materials.append({"slot": slot_name, "material": path})

# Restrained process task lights attached to the enclosed portion only.
common_tags = ["LB.Asset.Candidate.v196", "LB.Asset.CandidateNotPromoted", "LB.Lighting.PR005.Task"]
lights = []
for index, x in enumerate((-4000.0, -3775.0, -3550.0), 1):
    light = actors_api.spawn_actor_from_class(unreal.RectLight, unreal.Vector(x, -1955.0, 232.0), unreal.Rotator(-90.0, 0.0, 0.0))
    light.set_actor_label(f"LB_PR005_V196_ProcessTaskLED_{index:02d}")
    light.get_component_by_class(unreal.RectLightComponent).set_editor_properties({
        "intensity": 5.0,
        "source_width": 150.0,
        "source_height": 35.0,
        "attenuation_radius": 340.0,
        "cast_shadows": False,
        "light_color": unreal.Color(204, 218, 220, 255),
    })
    light.tags = [unreal.Name(value) for value in common_tags]
    lights.append(light)


def camera(label, location, target, fov):
    actor = actors_api.spawn_actor_from_class(unreal.CameraActor, unreal.Vector(*location), unreal.Rotator())
    actor.set_actor_label("LB_PR005_V196_CAM_" + label)
    actor.set_actor_rotation(unreal.MathLibrary.find_look_at_rotation(actor.get_actor_location(), unreal.Vector(*target)), False)
    actor.camera_component.set_editor_properties({"field_of_view": fov, "aspect_ratio": 16.0 / 9.0, "constrain_aspect_ratio": True})
    actor.tags = [unreal.Name(value) for value in ("LB.Asset.Candidate.v196", "LB.Asset.CandidateNotPromoted", "LB.Camera.Fixed.PR005.v196")]
    return actor


cameras = [
    camera("OperatorPlayer", (-4560.0, -1040.0, 215.0), (-3870.0, -1950.0, 125.0), 48.0),
    camera("OperatorElevated", (-4680.0, -900.0, 480.0), (-3860.0, -1960.0, 125.0), 53.0),
    camera("ServiceSide", (-3400.0, -3010.0, 270.0), (-3850.0, -2040.0, 120.0), 50.0),
    camera("ProcessFlow", (-4720.0, -1080.0, 620.0), (-3840.0, -1960.0, 110.0), 55.0),
]

actual_min, actual_max = bounds(infill)
expected_min = unreal.Vector(-4094.0, -2209.05, 4.0)
expected_max = unreal.Vector(-3516.75, -1696.8, 256.0)
bound_deltas = [
    actual_min.x - expected_min.x, actual_min.y - expected_min.y, actual_min.z - expected_min.z,
    actual_max.x - expected_max.x, actual_max.y - expected_max.y, actual_max.z - expected_max.z,
]
if max(abs(value) for value in bound_deltas) > 0.2:
    failures.append(f"world bounds drift cm={bound_deltas}")

column = next((actor for actor in all_before if actor.get_actor_label() == "LB_PRESS_Column_-4000_-2250"), None)
column_overlap = None
column_bounds = None
if column is None:
    failures.append("retained structural column missing")
else:
    column_min, column_max = bounds(column)
    column_overlap = overlaps(actual_min, actual_max, column_min, column_max)
    column_bounds = {"min_cm": list(column_min.to_tuple()), "max_cm": list(column_max.to_tuple())}
    if column_overlap:
        failures.append("runtime-cage infill overlaps retained structural column")

guard_evidence = []
for label, actor in guards.items():
    component = actor.get_component_by_class(unreal.StaticMeshComponent)
    guard_evidence.append({
        "label": label,
        "collision_enabled": str(component.get_collision_enabled()) if component else None,
        "collision_profile": str(component.get_collision_profile_name()) if component else None,
        "can_affect_navigation": bool(component.get_editor_property("can_ever_affect_navigation")) if component else None,
    })
    if component is None or component.get_collision_enabled() == unreal.CollisionEnabled.NO_COLLISION:
        failures.append(f"native guard collision authority missing {label}")
    if component is not None and not bool(component.get_editor_property("can_ever_affect_navigation")):
        failures.append(f"native guard navigation authority missing {label}")

if not levels.save_current_level():
    failures.append("could not save v196")
base_hash_after = sha256(BASE_PACKAGE)
if base_hash_after != base_hash_before:
    failures.append("protected v053 package changed")

payload = {
    "$schema": "cairnwell/audit/press-shop-pr005-runtime-cage-infill-build-v196/v1",
    "generated_utc": datetime.now(timezone.utc).isoformat(),
    "status": "PASS__V053_DERIVED_NATIVE_CAGE_AUTHORITY_PRESERVED_COLUMN_CLEAR_VISUAL_SUCCESSOR_BUILT__FIXED_CAMERA_AND_RUNTIME_GATES_REQUIRED__NOT_PROMOTED" if not failures else "FAIL__PR005_V196_BUILD__NOT_PROMOTED",
    "base_map": BASE,
    "map": MAP,
    "protected_base_sha256_before": base_hash_before,
    "protected_base_sha256_after": base_hash_after,
    "infill_actor": infill.get_actor_label(),
    "infill_world_bounds_cm": {"min": list(actual_min.to_tuple()), "max": list(actual_max.to_tuple())},
    "expected_world_bounds_cm": {"min": list(expected_min.to_tuple()), "max": list(expected_max.to_tuple())},
    "world_bound_delta_cm": bound_deltas,
    "column": column_bounds,
    "column_overlap": column_overlap,
    "native_guard_authority": guard_evidence,
    "new_collision": "NoCollision",
    "new_navigation_effect": False,
    "native_doors_replaced": False,
    "duplicate_hmi_added": False,
    "assigned_materials": assigned_materials,
    "task_lights": [actor.get_actor_label() for actor in lights],
    "fixed_cameras": [actor.get_actor_label() for actor in cameras],
    "planning_10400_vs_11500": "TBC_NOT_INVENTED",
    "promotion_authorized": False,
    "failures": failures,
}
OUT.parent.mkdir(parents=True, exist_ok=True)
OUT.write_text(json.dumps(payload, indent=2), encoding="utf-8")
print(json.dumps({"status": payload["status"], "column_overlap": column_overlap, "failures": failures}, indent=2))
if failures:
    raise RuntimeError("; ".join(failures))

