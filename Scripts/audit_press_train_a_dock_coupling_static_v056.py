"""Run the v048 exact-map gate on v056 and verify v003 endpoints/couplings."""

import json
from pathlib import Path

import unreal


ROOT = Path(unreal.Paths.project_dir())
base = Path(__file__).with_name("audit_press_train_a_crown_endpoint_static_v048.py")
code = base.read_text(encoding="utf-8")
code = code.replace(
    "LB_PressTrainACrownEndpointCandidate_v048",
    "LB_PressTrainADockCouplingEvidenceCandidate_v056",
)
code = code.replace("press_train_a_crown_endpoint_static_v048", "press_train_a_dock_coupling_static_v056")
code = code.replace("crown-endpoint-static-v048", "dock-coupling-static-v056")
code = code.replace("LB.Asset.Candidate.v048", "LB.Asset.Candidate.v056")
code = code.replace('"presentation": (len(presentation), 135)', '"presentation": (len(presentation), 140)')
code = code.replace(
    'code = code.replace("if len(scope) != 164:", "if len(scope) != 180:")',
    'code = code.replace("if len(scope) != 164:", "if len(scope) != 185:")',
)
code = code.replace(
    'code = code.replace("expected 164 scoped actors", "expected 180 scoped actors")',
    'code = code.replace("expected 164 scoped actors", "expected 185 scoped actors")',
)
code = code.replace("PRESS_TRAIN_A_V048", "PRESS_TRAIN_A_V056")
code = code.replace("V048", "V056").replace("v048", "v056")
exec(compile(code, str(base) + "::v056", "exec"), globals(), globals())

actors_api = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
expected_mesh = (
    "/Game/LineBoss/Candidates/PressTrains/Shared/DockCouplingEvidence_v001/"
    "SM_CA_MW_PT_DockCouplingEngaged_v001.SM_CA_MW_PT_DockCouplingEngaged_v001"
)
endpoint_root = "/Game/LineBoss/Candidates/PressTrains/Shared/CrownEndpointPresentation_v003"
endpoint_expected = {
    "HeavyCrown": f"{endpoint_root}/SM_CA_MW_PT_HeavyCrownMass_v003.SM_CA_MW_PT_HeavyCrownMass_v003",
    "S01": f"{endpoint_root}/SM_CA_MW_PT_S01VisibleBlankFeed_v003.SM_CA_MW_PT_S01VisibleBlankFeed_v003",
    "S07": f"{endpoint_root}/SM_CA_MW_PT_S07VisiblePanelDischarge_v003.SM_CA_MW_PT_S07VisiblePanelDischarge_v003",
}
endpoint_bindings = []
couplings = []
for actor in actors_api.get_all_level_actors():
    tags = {str(tag) for tag in actor.tags}
    if "LB.PressTrain.Fixed.CrownEndpointPresentation" in tags:
        if any(".HeavyCrown" in tag for tag in tags):
            key = "HeavyCrown"
        elif "LB.PressTrain.CrownEndpoint.S01.VisibleBlankFeed" in tags:
            key = "S01"
        elif "LB.PressTrain.CrownEndpoint.S07.VisiblePanelDischarge" in tags:
            key = "S07"
        else:
            failures.append(f"unrecognized v003 endpoint actor: {actor.get_actor_label()}")
            key = None
        mesh = actor.static_mesh_component.static_mesh
        path = mesh.get_path_name() if mesh else None
        endpoint_bindings.append({"actor": actor.get_actor_label(), "mesh": path, "role": key})
        if key and path != endpoint_expected[key]:
            failures.append(f"v003 endpoint mesh mismatch {actor.get_actor_label()}: {path}")
    if "LB.PressTrain.Fixed.DockCouplingEvidence" not in tags:
        continue
    mesh = actor.static_mesh_component.static_mesh
    path = mesh.get_path_name() if mesh else None
    stage_tags = sorted(tag for tag in tags if tag.startswith("LB.PressTrain.DockCoupling."))
    couplings.append({"actor": actor.get_actor_label(), "mesh": path, "stage_tags": stage_tags})
    if path != expected_mesh:
        failures.append(f"dock coupling mesh mismatch on {actor.get_actor_label()}: {path}")
    if len(stage_tags) != 1:
        failures.append(f"dock coupling stage tag mismatch on {actor.get_actor_label()}: {stage_tags}")
if len(couplings) != 5:
    failures.append(f"expected five engaged dock couplings, found {len(couplings)}")
if len(endpoint_bindings) != 7:
    failures.append(f"expected seven v003 endpoint bindings, found {len(endpoint_bindings)}")

report["v003_endpoint_bindings"] = endpoint_bindings
report["dock_couplings"] = couplings
report["failures"] = failures
report["status"] = (
    "PASS__PRESS_TRAIN_A_V056_EXACT_MAP_WARNING_CLEAN_ENDPOINTS_AND_FIVE_ENGAGED_DOCK_COUPLINGS__FRESH_PRO_VISUAL_GATE_REQUIRED__NOT_PROMOTED"
    if not failures else "FAIL__PRESS_TRAIN_A_V056_DOCK_COUPLING_STATIC_GATE__NOT_PROMOTED"
)
OUT.write_text(json.dumps(report, indent=2), encoding="utf-8")
print(json.dumps({"dock_couplings": len(couplings), "failures": failures}, indent=2))
if failures:
    raise RuntimeError("; ".join(failures))
