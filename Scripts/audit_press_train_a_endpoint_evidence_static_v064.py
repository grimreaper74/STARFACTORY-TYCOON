"""Run the exact static/material/camera gate on isolated Train A v064."""

import json
from pathlib import Path

import unreal


base = Path(__file__).with_name("audit_press_train_a_industrial_readability_static_v063.py")
code = base.read_text(encoding="utf-8")
code = code.replace("Candidate_v063", "Candidate_v064")
code = code.replace("industrial_readability_static_v063", "endpoint_evidence_static_v064")
code = code.replace("industrial-readability-static-v063", "endpoint-evidence-static-v064")
code = code.replace('"scope": (len(scope), 187)', '"scope": (len(scope), 189)')
code = code.replace('"cameras": (len(cameras), 5)', '"cameras": (len(cameras), 7)')
code = code.replace("LB.Asset.Candidate.v063", "LB.Asset.Candidate.v064")
code = code.replace("PRESS_TRAIN_A_V063", "PRESS_TRAIN_A_V064")
code = code.replace("V063", "V064").replace("v063", "v064")
exec(compile(code, str(base) + "::v064", "exec"), globals(), globals())

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
    for label in ("CA_MW_PTA_S03_MaintenanceAccess_v064", "CA_MW_PTA_S05_MaintenanceAccess_v064"):
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
for label in ("CA_MW_PTA_CAM_S01FeedEvidence_v064", "CA_MW_PTA_CAM_S07DischargeEvidence_v064"):
    actor = by_label.get(label)
    if actor is None:
        failures.append(f"endpoint evidence camera missing: {label}")
        continue
    camera_checks.append({
        "actor": label,
        "fov": actor.camera_component.get_editor_property("field_of_view"),
        "tags": sorted(str(tag) for tag in actor.tags),
    })
    if "LB.PressTrain.EndpointEvidence.v064" not in {str(tag) for tag in actor.tags}:
        failures.append(f"endpoint evidence camera tag missing: {label}")

report["access_material_copy"] = material_checks
report["endpoint_evidence_cameras"] = camera_checks
report["failures"] = failures
report["status"] = (
    "PASS__PRESS_TRAIN_A_V064_EXACT_MAP_ACCESS_MATERIALS_ENDPOINT_CAMERAS_AND_WARNING_CLEAN_COUPLINGS__FRESH_PRO_VISUAL_GATE_REQUIRED__NOT_PROMOTED"
    if not failures else "FAIL__PRESS_TRAIN_A_V064_ENDPOINT_EVIDENCE_STATIC_GATE__NOT_PROMOTED"
)
OUT.write_text(json.dumps(report, indent=2), encoding="utf-8")
print(json.dumps({"material_checks": len(material_checks), "camera_checks": len(camera_checks), "failures": failures}, indent=2))
if failures:
    raise RuntimeError("; ".join(failures))
