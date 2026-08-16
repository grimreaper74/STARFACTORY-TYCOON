"""Build v064 directly from v053 with copied access materials and endpoint cameras."""

import json
from pathlib import Path

import unreal


base = Path(__file__).with_name("build_press_train_a_industrial_readability_candidate_v061.py")
code = base.read_text(encoding="utf-8")
code = code.replace("import_build_press_train_a_dock_coupling_candidate_v061.py", "import_build_press_train_a_dock_coupling_candidate_v064.py")
code = code.replace("unreal.Rotator(0.0, 180.0, 0.0)", "unreal.Rotator(0.0, 0.0, 180.0)")
code = code.replace(
    "actor.static_mesh_component.set_static_mesh(access_template.static_mesh_component.static_mesh)",
    "actor.static_mesh_component.set_static_mesh(access_template.static_mesh_component.static_mesh)\n"
    "        for material_index, _slot in enumerate(access_template.static_mesh_component.get_material_slot_names()):\n"
    "            actor.static_mesh_component.set_material(material_index, access_template.static_mesh_component.get_material(material_index))",
)
code = code.replace('"CA_MW_PTA_CAM_Hero": 0.00', '"CA_MW_PTA_CAM_Hero": 0.15')
code = code.replace('"CA_MW_PTA_CAM_Overview": -0.05', '"CA_MW_PTA_CAM_Overview": 0.10')
code = code.replace('"CA_MW_PTA_CAM_DrawStage": 0.05', '"CA_MW_PTA_CAM_DrawStage": 0.15')
code = code.replace('"CA_MW_PTA_CAM_DieChangeService": 0.10', '"CA_MW_PTA_CAM_DieChangeService": 0.15')
code = code.replace('"CA_MW_PTA_CAM_DieCartDetail": 0.05', '"CA_MW_PTA_CAM_DieCartDetail": 0.10')
code = code.replace("Candidate_v061", "Candidate_v064")
code = code.replace("industrial_readability_v061", "endpoint_evidence_v064")
code = code.replace("industrial-readability-v061", "endpoint-evidence-v064")
code = code.replace("IndustrialReadability.v061", "EndpointEvidence.v064")
code = code.replace("LB.Asset.Candidate.v061", "LB.Asset.Candidate.v064")
code = code.replace("PRESS_TRAIN_A_V061", "PRESS_TRAIN_A_V064")
code = code.replace("V061", "V064").replace("v061", "v064")
exec(compile(code, str(base) + "::v064", "exec"), globals(), globals())

ROOT = Path(unreal.Paths.project_dir())
OUT = ROOT / "Saved/Audits/PressTrains/press_train_a_endpoint_evidence_v064.json"
levels = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
actors_api = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)


def add_camera(label, location, target, bias):
    actor = actors_api.spawn_actor_from_class(unreal.CameraActor, location)
    if actor is None:
        raise RuntimeError(f"could not spawn {label}")
    actor.set_actor_label(label)
    actor.set_actor_rotation(unreal.MathLibrary.find_look_at_rotation(location, target), False)
    actor.tags = [
        unreal.Name("LB.PressTrain.TrainA.Isolated"),
        unreal.Name("LB.Camera.Fixed"),
        unreal.Name("LB.Camera.ManagementEvidence"),
        unreal.Name("LB.PressTrain.EndpointEvidence.v064"),
        unreal.Name("LB.Asset.Candidate.v064"),
        unreal.Name("LB.Asset.CandidateNotPromoted"),
        unreal.Name("LB.Authority.WorldPlacement.TBCNotInvented"),
    ]
    settings = actor.camera_component.get_editor_property("post_process_settings")
    settings.set_editor_properties({
        "override_auto_exposure_method": True,
        "auto_exposure_method": unreal.AutoExposureMethod.AEM_BASIC,
        "override_auto_exposure_min_brightness": True,
        "override_auto_exposure_max_brightness": True,
        "auto_exposure_min_brightness": 1.0,
        "auto_exposure_max_brightness": 1.0,
        "override_auto_exposure_bias": True,
        "auto_exposure_bias": bias,
    })
    actor.camera_component.set_editor_property("post_process_settings", settings)
    actor.camera_component.set_editor_property("post_process_blend_weight", 1.0)
    actor.camera_component.set_editor_property("field_of_view", 54.0)
    return {
        "actor": label,
        "location_cm": [location.x, location.y, location.z],
        "target_cm": [target.x, target.y, target.z],
        "exposure_bias": bias,
    }


endpoint_cameras = [
    add_camera(
        "CA_MW_PTA_CAM_S01FeedEvidence_v064",
        unreal.Vector(-920.0, -520.0, 330.0),
        unreal.Vector(-190.0, 90.0, 150.0),
        0.20,
    ),
    add_camera(
        "CA_MW_PTA_CAM_S07DischargeEvidence_v064",
        unreal.Vector(-940.0, 5120.0, 350.0),
        unreal.Vector(-300.0, 4230.0, 230.0),
        0.20,
    ),
]
if not levels.save_current_level():
    raise RuntimeError("could not save v064 endpoint-evidence cameras")

report = json.loads(OUT.read_text(encoding="utf-8"))
report["endpoint_cameras"] = endpoint_cameras
report["status"] = "PASS__PRESS_TRAIN_A_V064_ENDPOINT_EVIDENCE_BUILD__STATIC_AND_FRESH_PRO_VISUAL_GATES_REQUIRED__NOT_PROMOTED"
OUT.write_text(json.dumps(report, indent=2), encoding="utf-8")
print(json.dumps({"endpoint_cameras": endpoint_cameras}, indent=2))
