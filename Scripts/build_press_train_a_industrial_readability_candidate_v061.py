"""Build Train A v061 directly from retained v053.

Reuse the warning-clean v003 coupling, reduce toy-like green repetition, expose
the existing measured maintenance-access kit, and make S01/S07 flow readable
from the operator-side fixed cameras.  This remains an isolated candidate.
"""

import json
from datetime import datetime, timezone
from pathlib import Path

import unreal


ROOT = Path(unreal.Paths.project_dir())
base = Path(__file__).with_name("build_press_train_a_reference_finish_candidate_v058.py")
code = base.read_text(encoding="utf-8")
code = code.replace(
    "import_build_press_train_a_dock_coupling_candidate_v057.py",
    "import_build_press_train_a_dock_coupling_candidate_v061.py",
)
code = code.replace("Candidate_v058", "Candidate_v061")
code = code.replace("reference_finish_v058", "reference_finish_v061")
code = code.replace("reference-finish-v058", "industrial-readability-v061")
code = code.replace("LB.Asset.Candidate.v058", "LB.Asset.Candidate.v061")
code = code.replace("PRESS_TRAIN_A_V058", "PRESS_TRAIN_A_V061")
code = code.replace("V058", "V061").replace("v058", "v061")
exec(compile(code, str(base) + "::v061", "exec"), globals(), globals())

TARGET = "/Game/LineBoss/Maps/LB_PressTrainADockCouplingEvidenceCandidate_v061"
OUT = ROOT / "Saved/Audits/PressTrains/press_train_a_industrial_readability_v061.json"
MAT25 = "/Game/LineBoss/Candidates/PressTrains/Shared/Materials_v025"
library = unreal.EditorAssetLibrary
levels = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
actors_api = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
charcoal = library.load_asset(f"{MAT25}/M_CA_MW_PT_FoundryCharcoalLayered_v025")
worked = library.load_asset(f"{MAT25}/M_CA_MW_PT_WorkedSteelLayered_v025")
if charcoal is None or worked is None:
    raise RuntimeError("v025 industrial materials missing")

actors = {actor.get_actor_label(): actor for actor in actors_api.get_all_level_actors()}
failures = []
changes = []

# Pull the two existing, measured maintenance-access modules clear of the
# facade skin, then reuse the same modular kit on S03 and S05.
access_template = actors.get("CA_MW_PTA_S02_MaintenanceAccess")
if access_template is None or access_template.static_mesh_component.static_mesh is None:
    failures.append("S02 maintenance-access template missing")
else:
    for stage in ("S02", "S06"):
        actor = actors.get(f"CA_MW_PTA_{stage}_MaintenanceAccess")
        if actor is None:
            failures.append(f"{stage} maintenance access missing")
            continue
        location = actor.get_actor_location()
        location.x = -130.0
        actor.set_actor_location(location, False, False)
        actor.tags = list(actor.tags) + [unreal.Name("LB.PressTrain.IndustrialReadability.v061")]
        changes.append({"actor": actor.get_actor_label(), "action": "facade_clearance", "x_cm": -130.0})
    for stage, y_cm in (("S03", 1500.0), ("S05", 3000.0)):
        actor = actors_api.spawn_actor_from_class(
            unreal.StaticMeshActor,
            unreal.Vector(-130.0, y_cm, 35.0),
            unreal.Rotator(0.0, 180.0, 0.0),
        )
        if actor is None:
            failures.append(f"could not spawn {stage} maintenance access")
            continue
        actor.static_mesh_component.set_static_mesh(access_template.static_mesh_component.static_mesh)
        actor.set_actor_label(f"CA_MW_PTA_{stage}_MaintenanceAccess_v061")
        actor.tags = [
            unreal.Name("LB.PressTrain.TrainA.Isolated"),
            unreal.Name("LB.PressTrain.SharedKit"),
            unreal.Name("LB.PressTrain.Fixed.ExteriorDetail"),
            unreal.Name(f"LB.PressTrain.ExteriorDetail.{stage}.MaintenanceAccess"),
            unreal.Name("LB.PressTrain.IndustrialReadability.v061"),
            unreal.Name("LB.Asset.Candidate.v061"),
            unreal.Name("LB.Asset.CandidateNotPromoted"),
            unreal.Name("LB.Authority.WorldPlacement.TBCNotInvented"),
        ]
        changes.append({"actor": actor.get_actor_label(), "action": "modular_access_reuse", "x_cm": -130.0, "y_cm": y_cm})

# Bring the physically-authored endpoint flow assets just ahead of the facade
# plane; no scale or process-axis change is introduced.
for label, x_cm in (
    ("CA_MW_PTA_S01_VisibleBlankFeed_v048", -190.0),
    ("CA_MW_PTA_S07_VisiblePanelDischarge_v048", -300.0),
):
    actor = actors.get(label)
    if actor is None:
        failures.append(f"endpoint actor missing: {label}")
        continue
    location = actor.get_actor_location()
    location.x = x_cm
    actor.set_actor_location(location, False, False)
    actor.tags = list(actor.tags) + [unreal.Name("LB.PressTrain.IndustrialReadability.v061")]
    changes.append({"actor": label, "action": "camera_readability_clearance", "x_cm": x_cm})

# Reserve Cairnwell green for identity/state cues. Large repeated cart,
# coupling and installed-service blocks become charcoal/steel.
restrained_materials = []
for actor in actors_api.get_all_level_actors():
    tags = {str(tag) for tag in actor.tags}
    if "LB.PressTrain.TrainA.Isolated" not in tags:
        continue
    label = actor.get_actor_label()
    component = getattr(actor, "static_mesh_component", None)
    if component is None or component.static_mesh is None:
        continue
    is_service_mass = (
        "DieCart" in label
        or "DockCoupling" in label
        or "InstalledServiceBank" in label
        or "ServiceDoorVentPack" in label
    )
    if not is_service_mass:
        continue
    for index, slot_name in enumerate(component.get_material_slot_names()):
        slot = str(slot_name)
        if slot == "CA_MW_CairnwellGreen":
            component.set_material(index, charcoal)
            restrained_materials.append({"actor": label, "slot": slot, "material": charcoal.get_path_name()})
        elif slot == "CA_MW_TrainAAccent" and "DockCoupling" in label:
            component.set_material(index, worked)
            restrained_materials.append({"actor": label, "slot": slot, "material": worked.get_path_name()})

camera_biases = {
    "CA_MW_PTA_CAM_Hero": 0.00,
    "CA_MW_PTA_CAM_Overview": -0.05,
    "CA_MW_PTA_CAM_DrawStage": 0.05,
    "CA_MW_PTA_CAM_DieChangeService": 0.10,
    "CA_MW_PTA_CAM_DieCartDetail": 0.05,
}
for label, bias in camera_biases.items():
    actor = actors.get(label)
    if actor is None:
        failures.append(f"camera missing: {label}")
        continue
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

if len(restrained_materials) < 10:
    failures.append(f"expected at least ten restrained service material overrides, found {len(restrained_materials)}")
if not levels.save_current_level():
    failures.append("could not save v061 industrial-readability candidate")

report = {
    "$schema": "cairnwell/audit/press-train-a-industrial-readability-v061/v1",
    "generated_utc": datetime.now(timezone.utc).isoformat(),
    "status": "PASS__PRESS_TRAIN_A_V061_INDUSTRIAL_READABILITY_BUILD__STATIC_AND_FRESH_PRO_VISUAL_GATES_REQUIRED__NOT_PROMOTED" if not failures else "FAIL__PRESS_TRAIN_A_V061_INDUSTRIAL_READABILITY_BUILD__NOT_PROMOTED",
    "source_map": "/Game/LineBoss/Maps/LB_PressTrainADieChangeLightingCalibrationCandidate_v053",
    "map": TARGET,
    "reused": ["DockCouplingEvidence_v003", "v058 charcoal/worked-metal policy", "AccessPlatformLadder_v002"],
    "layout_changes": changes,
    "restrained_material_overrides": restrained_materials,
    "camera_exposure_biases": camera_biases,
    "world_placement": "TBC_NOT_INVENTED",
    "production_map_changed": False,
    "failures": failures,
    "promotion_authorized": False,
    "press_shop_complete": False,
}
OUT.write_text(json.dumps(report, indent=2), encoding="utf-8")
print(json.dumps({"map": TARGET, "layout_changes": len(changes), "material_overrides": len(restrained_materials), "failures": failures}, indent=2))
if failures:
    raise RuntimeError("; ".join(failures))
