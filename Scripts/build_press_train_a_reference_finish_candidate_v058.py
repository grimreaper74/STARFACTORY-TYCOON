"""Build isolated Train A v058 directly from retained v053.

The v057 fit correction is reused, but v057 is not used as a map parent. This
pass shifts the large stage/enclosure masses toward the charcoal worked-metal
language in Press Train Sheets 04/05 and restrains green to secondary identity.
"""

import json
from datetime import datetime, timezone
from pathlib import Path

import unreal


ROOT = Path(unreal.Paths.project_dir())
base = Path(__file__).with_name("import_build_press_train_a_dock_coupling_candidate_v057.py")
code = base.read_text(encoding="utf-8")
code = code.replace("Candidate_v057", "Candidate_v058")
code = code.replace("evidence_v057", "evidence_v058")
code = code.replace("candidate-v057", "reference-finish-v058")
code = code.replace("LB.Asset.Candidate.v057", "LB.Asset.Candidate.v058")
code = code.replace("PRESS_TRAIN_A_V057", "PRESS_TRAIN_A_V058")
code = code.replace("V057", "V058").replace("v057", "v058")
exec(compile(code, str(base) + "::v058", "exec"), globals(), globals())

TARGET = "/Game/LineBoss/Maps/LB_PressTrainADockCouplingEvidenceCandidate_v058"
OUT = ROOT / "Saved/Audits/PressTrains/press_train_a_reference_finish_v058.json"
MAT25 = "/Game/LineBoss/Candidates/PressTrains/Shared/Materials_v025"
library = unreal.EditorAssetLibrary
levels = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
actors_api = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)

charcoal = library.load_asset(f"{MAT25}/M_CA_MW_PT_FoundryCharcoalLayered_v025")
worked = library.load_asset(f"{MAT25}/M_CA_MW_PT_WorkedSteelLayered_v025")
if charcoal is None or worked is None:
    raise RuntimeError("reference-finish materials missing")

overrides = []
camera_biases = {
    "CA_MW_PTA_CAM_Hero": -0.25,
    "CA_MW_PTA_CAM_Overview": -0.35,
    "CA_MW_PTA_CAM_DrawStage": -0.20,
    "CA_MW_PTA_CAM_DieChangeService": 0.18,
    "CA_MW_PTA_CAM_DieCartDetail": 0.12,
}

for actor in actors_api.get_all_level_actors():
    tags = {str(tag) for tag in actor.tags}
    if "LB.PressTrain.TrainA.Isolated" not in tags:
        continue
    label = actor.get_actor_label()
    if label in camera_biases:
        settings = actor.camera_component.get_editor_property("post_process_settings")
        settings.set_editor_properties({
            "override_auto_exposure_method": True,
            "auto_exposure_method": unreal.AutoExposureMethod.AEM_BASIC,
            "override_auto_exposure_min_brightness": True,
            "override_auto_exposure_max_brightness": True,
            "auto_exposure_min_brightness": 1.0,
            "auto_exposure_max_brightness": 1.0,
            "override_auto_exposure_bias": True,
            "auto_exposure_bias": camera_biases[label],
        })
        actor.camera_component.set_editor_property("post_process_settings", settings)
        actor.camera_component.set_editor_property("post_process_blend_weight", 1.0)
    component = getattr(actor, "static_mesh_component", None)
    if component is None or component.static_mesh is None:
        continue
    is_primary_mass = (
        "LB.PressTrain.Fixed.EnclosedFacade" in tags
        or any(tag.startswith("LB.PressTrain.Stage.S") for tag in tags)
    )
    if not is_primary_mass:
        continue
    for index, slot_name in enumerate(component.get_material_slot_names()):
        slot = str(slot_name)
        if slot == "CA_MW_CairnwellGreen":
            component.set_material(index, charcoal)
            overrides.append({"actor": label, "slot": slot, "material": charcoal.get_path_name()})
        elif slot == "CA_MW_ServiceGrey" and "LB.PressTrain.Fixed.EnclosedFacade" in tags:
            component.set_material(index, worked)
            overrides.append({"actor": label, "slot": slot, "material": worked.get_path_name()})

failures = []
if len(overrides) < 14:
    failures.append(f"expected at least 14 primary-mass overrides, found {len(overrides)}")
if not levels.save_current_level():
    failures.append("could not save v058 reference-finish candidate")

report = {
    "$schema": "cairnwell/audit/press-train-a-reference-finish-v058/v1",
    "generated_utc": datetime.now(timezone.utc).isoformat(),
    "status": "PASS__PRESS_TRAIN_A_V058_REFERENCE_FINISH_BUILD__STATIC_AND_FRESH_PRO_VISUAL_GATES_REQUIRED__NOT_PROMOTED" if not failures else "FAIL__PRESS_TRAIN_A_V058_REFERENCE_FINISH_BUILD__NOT_PROMOTED",
    "source_map": "/Game/LineBoss/Maps/LB_PressTrainADieChangeLightingCalibrationCandidate_v053",
    "map": TARGET,
    "reused_result": "v057 coupling fit only; v057 map is not the parent",
    "material_overrides": overrides,
    "camera_exposure_biases": camera_biases,
    "world_placement": "TBC_NOT_INVENTED",
    "production_map_changed": False,
    "accepted_pr010_map_changed": False,
    "failures": failures,
    "promotion_authorized": False,
    "press_shop_complete": False,
}
OUT.write_text(json.dumps(report, indent=2), encoding="utf-8")
print(json.dumps({"map": TARGET, "overrides": len(overrides), "failures": failures}, indent=2))
if failures:
    raise RuntimeError("; ".join(failures))
