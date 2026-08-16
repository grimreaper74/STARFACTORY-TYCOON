"""Run exact Train A static gates plus v048 crown/endpoint requirements."""

import json
from pathlib import Path

import unreal


base = Path(__file__).with_name("audit_press_train_a_stage_exterior_cues_static_v037.py")
code = base.read_text(encoding="utf-8")
code = code.replace("LB_PressTrainAStageExteriorCuesCandidate_v037", "LB_PressTrainACrownEndpointCandidate_v048")
code = code.replace("press_train_a_stage_exterior_cues_static_v037", "press_train_a_crown_endpoint_static_v048")
code = code.replace("stage-exterior-cues-static-v037", "crown-endpoint-static-v048")
code = code.replace("LB.Asset.Candidate.v037", "LB.Asset.Candidate.v048")
code = code.replace("PRESS_TRAIN_A_V037", "PRESS_TRAIN_A_V048")
code = code.replace('"presentation": (len(presentation), 121)', '"presentation": (len(presentation), 135)')
code = code.replace(
    'code = code.replace("if len(scope) != 164:", "if len(scope) != 173:")',
    'code = code.replace("if len(scope) != 164:", "if len(scope) != 180:")',
)
code = code.replace(
    'code = code.replace("expected 164 scoped actors", "expected 173 scoped actors")',
    'code = code.replace("expected 164 scoped actors", "expected 180 scoped actors")',
)
code = code.replace(
    'exec(compile(code, str(base) + "::v037", "exec"), globals(), globals())',
    'code = code.replace(\'"texts": (len(texts), 13)\', \'"texts": (len(texts), 6)\')\n'
    'code = code.replace(\'"integrated_ids": (len(integrated_ids), 7)\', \'"integrated_ids": (len(integrated_ids), 0)\')\n'
    'exec(compile(code, str(base) + "::v048", "exec"), globals(), globals())',
)
code = code.replace("V037", "V048").replace("v037", "v048")
exec(compile(code, str(base) + "::v048", "exec"), globals(), globals())

actors_api = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
library = unreal.EditorAssetLibrary
presentation_actors = [
    actor for actor in actors_api.get_all_level_actors()
    if "LB.PressTrain.Fixed.CrownEndpointPresentation" in {str(tag) for tag in actor.tags}
]
asset_names = (
    "SM_CA_MW_PT_HeavyCrownMass_v001",
    "SM_CA_MW_PT_S01VisibleBlankFeed_v001",
    "SM_CA_MW_PT_S07VisiblePanelDischarge_v001",
)
asset_paths = [
    f"/Game/LineBoss/Candidates/PressTrains/Shared/CrownEndpointPresentation_v001/{name}"
    for name in asset_names
]
heavy_crowns = [
    actor for actor in presentation_actors
    if any(".HeavyCrown" in str(tag) for tag in actor.tags)
]
if len(presentation_actors) != 7:
    failures.append(f"expected seven crown/endpoint actors, got {len(presentation_actors)}")
if len(heavy_crowns) != 5:
    failures.append(f"expected five heavy crown actors, got {len(heavy_crowns)}")
for semantic in (
    "LB.PressTrain.CrownEndpoint.S01.VisibleBlankFeed",
    "LB.PressTrain.CrownEndpoint.S07.VisiblePanelDischarge",
):
    if not any(semantic in {str(tag) for tag in actor.tags} for actor in presentation_actors):
        failures.append(f"missing endpoint presentation: {semantic}")
missing_assets = [path for path in asset_paths if not library.does_asset_exist(path)]
if missing_assets:
    failures.append(f"missing crown/endpoint assets: {missing_assets}")
report["counts"]["crown_endpoint_presentation"] = len(presentation_actors)
report["counts"]["heavy_crowns"] = len(heavy_crowns)
report["crown_endpoint_assets"] = asset_paths
report["missing_assets"] = sorted(set(report.get("missing_assets", []) + missing_assets))
report["failures"] = failures
report["status"] = (
    "PASS__PRESS_TRAIN_A_V048_EXACT_MAP_SEGMENTED_IDENTITIES_HEAVY_CROWNS_AND_VISIBLE_ENDPOINT_FLOW__FRESH_PRO_VISUAL_GATE_REQUIRED__NOT_PROMOTED"
    if not failures else "FAIL__PRESS_TRAIN_A_V048_CROWN_ENDPOINT_STATIC_GATE__NOT_PROMOTED"
)
OUT.write_text(json.dumps(report, indent=2), encoding="utf-8")
print(json.dumps({"v048_crown_endpoint_count": len(presentation_actors), "failures": failures}, indent=2))
if failures:
    raise RuntimeError("; ".join(failures))
