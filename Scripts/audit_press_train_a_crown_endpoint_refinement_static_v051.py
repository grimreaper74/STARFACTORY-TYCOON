"""Use v050's exact gate against refined crown/endpoint map v051."""

from pathlib import Path

import json
import unreal

base = Path(__file__).with_name("audit_press_train_a_crown_endpoint_calibration_static_v050.py")
code = base.read_text(encoding="utf-8")
code = code.replace("LB_PressTrainACrownEndpointCalibrationCandidate_v050", "LB_PressTrainACrownEndpointRefinementCandidate_v051")
code = code.replace("press_train_a_crown_endpoint_calibration_static_v050", "press_train_a_crown_endpoint_refinement_static_v051")
code = code.replace("crown-endpoint-calibration-static-v050", "crown-endpoint-refinement-static-v051")
code = code.replace("LB.Asset.Candidate.v050", "LB.Asset.Candidate.v051")
code = code.replace("CrownEndpointPresentation_v001", "CrownEndpointPresentation_v002")
code = code.replace("_v001", "_v002")
code = code.replace("PRESS_TRAIN_A_V050", "PRESS_TRAIN_A_V051")
code = code.replace("V050", "V051").replace("v050", "v051")
exec(compile(code, str(base) + "::v051", "exec"), globals(), globals())

actors_api = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
library = unreal.EditorAssetLibrary
root = "/Game/LineBoss/Candidates/PressTrains/Shared/CrownEndpointPresentation_v002"
expected_assets = {
    "HeavyCrown": f"{root}/SM_CA_MW_PT_HeavyCrownMass_v002.SM_CA_MW_PT_HeavyCrownMass_v002",
    "S01": f"{root}/SM_CA_MW_PT_S01VisibleBlankFeed_v002.SM_CA_MW_PT_S01VisibleBlankFeed_v002",
    "S07": f"{root}/SM_CA_MW_PT_S07VisiblePanelDischarge_v002.SM_CA_MW_PT_S07VisiblePanelDischarge_v002",
}
verified = []
for actor in actors_api.get_all_level_actors():
    tags = {str(tag) for tag in actor.tags}
    if "LB.PressTrain.Fixed.CrownEndpointPresentation" not in tags:
        continue
    if any(".HeavyCrown" in tag for tag in tags):
        key = "HeavyCrown"
    elif "LB.PressTrain.CrownEndpoint.S01.VisibleBlankFeed" in tags:
        key = "S01"
    elif "LB.PressTrain.CrownEndpoint.S07.VisiblePanelDischarge" in tags:
        key = "S07"
    else:
        failures.append(f"unrecognized v051 crown/endpoint actor: {actor.get_actor_label()}")
        continue
    mesh = actor.static_mesh_component.static_mesh
    path = mesh.get_path_name() if mesh else None
    verified.append({"actor": actor.get_actor_label(), "mesh": path})
    if path != expected_assets[key]:
        failures.append(f"v051 mesh mismatch {actor.get_actor_label()}: {path} != {expected_assets[key]}")
missing_v002 = [path.split(".")[0] for path in expected_assets.values() if not library.does_asset_exist(path.split(".")[0])]
if missing_v002:
    failures.append(f"missing v002 crown/endpoint assets: {missing_v002}")
report["crown_endpoint_assets"] = [path.split(".")[0] for path in expected_assets.values()]
report["v002_mesh_bindings"] = verified
report["missing_assets"] = sorted(set(report.get("missing_assets", []) + missing_v002))
report["failures"] = failures
report["status"] = (
    "PASS__PRESS_TRAIN_A_V051_EXACT_MAP_RECESSED_V002_CROWNS_VISIBLE_ENDPOINT_FLOW_AND_SEGMENTED_IDENTITIES__FRESH_PRO_VISUAL_GATE_REQUIRED__NOT_PROMOTED"
    if not failures else "FAIL__PRESS_TRAIN_A_V051_CROWN_ENDPOINT_REFINEMENT_STATIC_GATE__NOT_PROMOTED"
)
OUT.write_text(json.dumps(report, indent=2), encoding="utf-8")
print(json.dumps({"v051_v002_bindings": len(verified), "failures": failures}, indent=2))
if failures:
    raise RuntimeError("; ".join(failures))
