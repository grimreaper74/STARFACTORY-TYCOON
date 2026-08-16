"""Build v068 directly from v053 with correct endpoint flow and obsolete cell occluders removed."""

import json
from pathlib import Path

import unreal


base = Path(__file__).with_name("build_press_train_a_endpoint_evidence_candidate_v064.py")
code = base.read_text(encoding="utf-8")
code = code.replace("import_build_press_train_a_dock_coupling_candidate_v064.py", "import_build_press_train_a_dock_coupling_candidate_v068.py")
code = code.replace("CA_MW_PTA_CAM_S01FeedEvidence_v064", "CA_MW_PTA_CAM_S01FeedClear_v068")
code = code.replace("CA_MW_PTA_CAM_S07DischargeEvidence_v064", "CA_MW_PTA_CAM_S07DischargeClear_v068")
code = code.replace("unreal.Vector(-920.0, -520.0, 330.0)", "unreal.Vector(600.0, -1100.0, 850.0)")
code = code.replace("unreal.Vector(-190.0, 90.0, 150.0)", "unreal.Vector(0.0, -250.0, 120.0)")
code = code.replace("unreal.Vector(-940.0, 5120.0, 350.0)", "unreal.Vector(650.0, 6100.0, 900.0)")
code = code.replace("unreal.Vector(-300.0, 4230.0, 230.0)", "unreal.Vector(0.0, 5000.0, 160.0)")
code = code.replace("EndpointEvidence.v064", "EndpointClearance.v068")
code = code.replace("endpoint_evidence_v064", "endpoint_clearance_v068")
code = code.replace("endpoint-evidence-v064", "endpoint-clearance-v068")
code = code.replace("Candidate_v064", "Candidate_v068")
code = code.replace("LB.Asset.Candidate.v064", "LB.Asset.Candidate.v068")
code = code.replace("PRESS_TRAIN_A_V064", "PRESS_TRAIN_A_V068")
code = code.replace("V064", "V068").replace("v064", "v068")
exec(compile(code, str(base) + "::v068", "exec"), globals(), globals())

ROOT = Path(unreal.Paths.project_dir())
OUT = ROOT / "Saved/Audits/PressTrains/press_train_a_endpoint_clearance_v068.json"
levels = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
actors_api = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
actors = {actor.get_actor_label(): actor for actor in actors_api.get_all_level_actors()}
failures = []
corrections = []

for label, y_cm, stage_tag in (
    ("CA_MW_PTA_S01_VisibleBlankFeed_v048", -150.0, "LB.PressTrain.Stage.S01"),
    ("CA_MW_PTA_S07_VisiblePanelDischarge_v048", 4550.0, "LB.PressTrain.Stage.S07"),
):
    actor = actors.get(label)
    if actor is None:
        failures.append(f"endpoint actor missing: {label}")
        continue
    location = actor.get_actor_location()
    location.y = y_cm
    actor.set_actor_location(location, False, False)
    actor.set_actor_rotation(unreal.Rotator(0.0, 0.0, 0.0), False)
    tags = [str(tag) for tag in actor.tags]
    tags.extend(("LB.PressTrain.EndpointClearance.v068", stage_tag))
    actor.tags = [unreal.Name(tag) for tag in dict.fromkeys(tags)]
    origin, extent = actor.get_actor_bounds(False)
    corrections.append({
        "actor": label,
        "stage_tag": stage_tag,
        "yaw_deg": 0.0,
        "y_cm": y_cm,
        "bounds_y_min_cm": origin.y - extent.y,
        "bounds_y_max_cm": origin.y + extent.y,
    })

removed = []
for label in ("CA_MW_PTA_S01_DESTACK__LOAD", "CA_MW_PTA_S07_UNLOAD__INSPECT"):
    actor = actors.get(label)
    if actor is None:
        failures.append(f"obsolete coarse endpoint cell missing: {label}")
        continue
    if not actors_api.destroy_actor(actor):
        failures.append(f"could not remove obsolete coarse endpoint cell: {label}")
    else:
        removed.append(label)

for camera_label in ("CA_MW_PTA_CAM_S01FeedClear_v068", "CA_MW_PTA_CAM_S07DischargeClear_v068"):
    camera = actors.get(camera_label)
    if camera is None:
        failures.append(f"endpoint camera missing: {camera_label}")
        continue
    settings = camera.camera_component.get_editor_property("post_process_settings")
    settings.set_editor_properties({"override_auto_exposure_bias": True, "auto_exposure_bias": 1.0})
    camera.camera_component.set_editor_property("post_process_settings", settings)
    camera.camera_component.set_editor_property("field_of_view", 58.0)

if not levels.save_current_level():
    failures.append("could not save v068 endpoint-clearance candidate")
report = json.loads(OUT.read_text(encoding="utf-8"))
report["endpoint_flow_corrections"] = corrections
report["removed_obsolete_occluders"] = removed
report["retained_endpoint_enclosure"] = [
    "CA_MW_PTA_S01_EnclosedFacade",
    "CA_MW_PTA_S07_EnclosedFacade",
]
report["failures"] = failures
report["status"] = (
    "PASS__PRESS_TRAIN_A_V068_CORRECT_ENDPOINT_FLOW_AND_OBSOLETE_OCCLUDER_REMOVAL__STATIC_AND_FRESH_PRO_VISUAL_GATES_REQUIRED__NOT_PROMOTED"
    if not failures else "FAIL__PRESS_TRAIN_A_V068_ENDPOINT_CLEARANCE_BUILD__NOT_PROMOTED"
)
OUT.write_text(json.dumps(report, indent=2), encoding="utf-8")
print(json.dumps({"corrections": corrections, "removed": removed, "failures": failures}, indent=2))
if failures:
    raise RuntimeError("; ".join(failures))
