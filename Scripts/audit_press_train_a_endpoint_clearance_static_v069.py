"""Standalone exact static/material/flow-clearance gate for isolated Train A v069."""

import json
from pathlib import Path

import unreal


base = Path(__file__).with_name("audit_press_train_a_industrial_readability_static_v063.py")
code = base.read_text(encoding="utf-8")
code = code.replace("Candidate_v063", "Candidate_v069")
code = code.replace("industrial_readability_static_v063", "endpoint_clearance_static_v069")
code = code.replace("industrial-readability-static-v063", "endpoint-clearance-static-v069")
code = code.replace('"scope": (len(scope), 187)', '"scope": (len(scope), 187)')
code = code.replace('"presentation": (len(presentation), 142)', '"presentation": (len(presentation), 140)')
code = code.replace('"cameras": (len(cameras), 5)', '"cameras": (len(cameras), 7)')
code = code.replace("LB.Asset.Candidate.v063", "LB.Asset.Candidate.v069")
code = code.replace("PRESS_TRAIN_A_V063", "PRESS_TRAIN_A_V069")
code = code.replace("V063", "V069").replace("v063", "v069")
exec(compile(code, str(base) + "::v069", "exec"), globals(), globals())

by_label = {actor.get_actor_label(): actor for actor in actors_api.get_all_level_actors()}

template = by_label.get("CA_MW_PTA_S02_MaintenanceAccess")
material_checks = []
if template is None:
    failures.append("S02 maintenance access template missing")
else:
    template_materials = [
        template.static_mesh_component.get_material(index).get_path_name()
        if template.static_mesh_component.get_material(index) else None
        for index, _slot in enumerate(template.static_mesh_component.get_material_slot_names())
    ]
    for label in ("CA_MW_PTA_S03_MaintenanceAccess_v069", "CA_MW_PTA_S05_MaintenanceAccess_v069"):
        actor = by_label.get(label)
        if actor is None:
            failures.append(f"material-copy actor missing: {label}")
            continue
        materials = [
            actor.static_mesh_component.get_material(index).get_path_name()
            if actor.static_mesh_component.get_material(index) else None
            for index, _slot in enumerate(actor.static_mesh_component.get_material_slot_names())
        ]
        material_checks.append({"actor": label, "materials": materials})
        if materials != template_materials:
            failures.append(f"maintenance access material override mismatch: {label}")

camera_checks = []
for label in ("CA_MW_PTA_CAM_S01FeedClear_v069", "CA_MW_PTA_CAM_S07DischargeClear_v069"):
    actor = by_label.get(label)
    if actor is None:
        failures.append(f"endpoint camera missing: {label}")
        continue
    actor_tags = {str(tag) for tag in actor.tags}
    camera_checks.append({
        "actor": label,
        "fov": actor.camera_component.get_editor_property("field_of_view"),
        "tags": sorted(actor_tags),
    })
    if "LB.PressTrain.EndpointClearance.v069" not in actor_tags:
        failures.append(f"endpoint camera tag missing: {label}")

flow_checks = []
for label, expected_y, stage_tag, minimum_y, maximum_y in (
    ("CA_MW_PTA_S01_VisibleBlankFeed_v048", -150.0, "LB.PressTrain.Stage.S01", -470.1, -59.9),
    ("CA_MW_PTA_S07_VisiblePanelDischarge_v048", 4460.0, "LB.PressTrain.Stage.S07", 4479.9, 5050.1),
):
    actor = by_label.get(label)
    if actor is None:
        failures.append(f"corrected endpoint missing: {label}")
        continue
    location = actor.get_actor_location()
    rotation = actor.get_actor_rotation()
    origin, extent = actor.get_actor_bounds(False)
    y_min = origin.y - extent.y
    y_max = origin.y + extent.y
    actor_tags = {str(tag) for tag in actor.tags}
    flow_checks.append({
        "actor": label,
        "y_cm": location.y,
        "yaw_deg": rotation.yaw,
        "bounds_y_cm": [y_min, y_max],
        "stage_tag": stage_tag,
    })
    if abs(location.y - expected_y) > 0.1 or abs(rotation.yaw) > 0.1:
        failures.append(f"endpoint flow transform mismatch: {label}")
    if y_min < minimum_y or y_max > maximum_y:
        failures.append(f"endpoint flow bounds mismatch: {label} [{y_min}, {y_max}]")
    if stage_tag not in actor_tags or "LB.PressTrain.EndpointClearance.v069" not in actor_tags:
        failures.append(f"endpoint stage/clearance tag missing: {label}")

removed_checks = []
for label in ("CA_MW_PTA_S01_DESTACK__LOAD", "CA_MW_PTA_S07_UNLOAD__INSPECT"):
    absent = label not in by_label
    removed_checks.append({"actor": label, "absent": absent})
    if not absent:
        failures.append(f"obsolete endpoint occluder retained: {label}")

report["access_material_copy"] = material_checks
report["endpoint_clearance_cameras"] = camera_checks
report["endpoint_flow_checks"] = flow_checks
report["removed_obsolete_occluders"] = removed_checks
report["failures"] = failures
report["status"] = (
    "PASS__PRESS_TRAIN_A_V069_EXACT_MAP_CORRECT_ENDPOINT_FLOW_CLEARANCE_ACCESS_MATERIALS_AND_WARNING_CLEAN_COUPLINGS__FRESH_PRO_VISUAL_GATE_REQUIRED__NOT_PROMOTED"
    if not failures else "FAIL__PRESS_TRAIN_A_V069_ENDPOINT_CLEARANCE_STATIC_GATE__NOT_PROMOTED"
)
OUT.write_text(json.dumps(report, indent=2), encoding="utf-8")
print(json.dumps({"flow_checks": flow_checks, "removed_checks": removed_checks, "failures": failures}, indent=2))
if failures:
    raise RuntimeError("; ".join(failures))
