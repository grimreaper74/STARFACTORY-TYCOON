"""Build v067 directly from v053 with corrected S01/S07 flow direction and endpoint CCTV."""

import json
from pathlib import Path

import unreal


base = Path(__file__).with_name("build_press_train_a_endpoint_evidence_candidate_v064.py")
code = base.read_text(encoding="utf-8")
code = code.replace("import_build_press_train_a_dock_coupling_candidate_v064.py", "import_build_press_train_a_dock_coupling_candidate_v067.py")
code = code.replace("CA_MW_PTA_CAM_S01FeedEvidence_v064", "CA_MW_PTA_CAM_S01FeedFlowCorrected_v067")
code = code.replace("CA_MW_PTA_CAM_S07DischargeEvidence_v064", "CA_MW_PTA_CAM_S07DischargeFlowCorrected_v067")
code = code.replace("unreal.Vector(-920.0, -520.0, 330.0)", "unreal.Vector(0.0, -650.0, 450.0)")
code = code.replace("unreal.Vector(-190.0, 90.0, 150.0)", "unreal.Vector(0.0, -275.0, 145.0)")
code = code.replace("unreal.Vector(-940.0, 5120.0, 350.0)", "unreal.Vector(0.0, 5350.0, 470.0)")
code = code.replace("unreal.Vector(-300.0, 4230.0, 230.0)", "unreal.Vector(0.0, 5000.0, 170.0)")
code = code.replace("EndpointEvidence.v064", "EndpointFlowDirection.v067")
code = code.replace("endpoint_evidence_v064", "endpoint_flow_direction_v067")
code = code.replace("endpoint-evidence-v064", "endpoint-flow-direction-v067")
code = code.replace("Candidate_v064", "Candidate_v067")
code = code.replace("LB.Asset.Candidate.v064", "LB.Asset.Candidate.v067")
code = code.replace("PRESS_TRAIN_A_V064", "PRESS_TRAIN_A_V067")
code = code.replace("V064", "V067").replace("v064", "v067")
exec(compile(code, str(base) + "::v067", "exec"), globals(), globals())

ROOT = Path(unreal.Paths.project_dir())
OUT = ROOT / "Saved/Audits/PressTrains/press_train_a_endpoint_flow_direction_v067.json"
levels = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
actors_api = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
actors = {actor.get_actor_label(): actor for actor in actors_api.get_all_level_actors()}
corrections = []
failures = []
for label, y_cm in (
    ("CA_MW_PTA_S01_VisibleBlankFeed_v048", -150.0),
    ("CA_MW_PTA_S07_VisiblePanelDischarge_v048", 4550.0),
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
    tags.append("LB.PressTrain.EndpointFlowDirection.v067")
    actor.tags = [unreal.Name(tag) for tag in dict.fromkeys(tags)]
    origin, extent = actor.get_actor_bounds(False)
    corrections.append({
        "actor": label,
        "yaw_deg": 0.0,
        "y_cm": y_cm,
        "bounds_y_min_cm": origin.y - extent.y,
        "bounds_y_max_cm": origin.y + extent.y,
    })

for camera_label in (
    "CA_MW_PTA_CAM_S01FeedFlowCorrected_v067",
    "CA_MW_PTA_CAM_S07DischargeFlowCorrected_v067",
):
    camera = actors.get(camera_label)
    if camera is None:
        failures.append(f"endpoint camera missing: {camera_label}")
        continue
    settings = camera.camera_component.get_editor_property("post_process_settings")
    settings.set_editor_properties({
        "override_auto_exposure_bias": True,
        "auto_exposure_bias": 0.6,
    })
    camera.camera_component.set_editor_property("post_process_settings", settings)
    camera.camera_component.set_editor_property("field_of_view", 58.0)

if not levels.save_current_level():
    failures.append("could not save v067 corrected endpoint-flow candidate")
report = json.loads(OUT.read_text(encoding="utf-8"))
report["endpoint_flow_corrections"] = corrections
report["failures"] = failures
report["status"] = (
    "PASS__PRESS_TRAIN_A_V067_ENDPOINT_FLOW_DIRECTION_BUILD__STATIC_AND_FRESH_PRO_VISUAL_GATES_REQUIRED__NOT_PROMOTED"
    if not failures else "FAIL__PRESS_TRAIN_A_V067_ENDPOINT_FLOW_DIRECTION_BUILD__NOT_PROMOTED"
)
OUT.write_text(json.dumps(report, indent=2), encoding="utf-8")
print(json.dumps({"corrections": corrections, "failures": failures}, indent=2))
if failures:
    raise RuntimeError("; ".join(failures))
