"""Run the exact v033+ static gate and add the four v037 stage-cue requirements."""

import json
from pathlib import Path

import unreal


base = Path(__file__).with_name("audit_press_train_a_enclosed_facade_static_v033.py")
code = base.read_text(encoding="utf-8")
code = code.replace("LB_PressTrainAEnclosedFacadeCandidate_v033", "LB_PressTrainAStageExteriorCuesCandidate_v037")
code = code.replace("press_train_a_enclosed_facade_static_v033.json", "press_train_a_stage_exterior_cues_static_v037.json")
code = code.replace("enclosed-facade-static-v033", "stage-exterior-cues-static-v037")
code = code.replace("PRESS_TRAIN_A_V033", "PRESS_TRAIN_A_V037")
code = code.replace("LB.Asset.Candidate.v033", "LB.Asset.Candidate.v037")
code = code.replace('"presentation": (len(presentation), 117)', '"presentation": (len(presentation), 121)')
code = code.replace("if len(scope) != 164:", "if len(scope) != 173:")
code = code.replace("expected 164 scoped actors", "expected 173 scoped actors")
exec(compile(code, str(base) + "::v037", "exec"), globals(), globals())

actors_api = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
library = unreal.EditorAssetLibrary
cue_actors = [
    actor for actor in actors_api.get_all_level_actors()
    if "LB.PressTrain.Fixed.StageExteriorCue" in {str(tag) for tag in actor.tags}
]
cue_assets = [
    f"/Game/LineBoss/Candidates/PressTrains/Shared/StageExteriorCues_v001/{name}"
    for name in (
        "SM_CA_MW_PT_S03SecondaryFormExteriorCue_v001",
        "SM_CA_MW_PT_S04TrimScrapExteriorCue_v001",
        "SM_CA_MW_PT_S05PierceSlugExteriorCue_v001",
        "SM_CA_MW_PT_S06RestrikeQualityExteriorCue_v001",
    )
]
if len(cue_actors) != 4:
    failures.append(f"expected four stage exterior cues, got {len(cue_actors)}")
for stage in ("S03", "S04", "S05", "S06"):
    if not any(f"LB.PressTrain.StageExteriorCue.{stage}" in {str(tag) for tag in actor.tags} for actor in cue_actors):
        failures.append(f"missing unique {stage} exterior cue")
missing_cue_assets = [path for path in cue_assets if not library.does_asset_exist(path)]
if missing_cue_assets:
    failures.append(f"missing stage cue assets: {missing_cue_assets}")
report["counts"]["stage_exterior_cues"] = len(cue_actors)
report["stage_exterior_cue_assets"] = cue_assets
report["missing_assets"] = sorted(set(report.get("missing_assets", []) + missing_cue_assets))
report["failures"] = failures
report["status"] = (
    "PASS__PRESS_TRAIN_A_V037_EXACT_MAP_RELEASE_CARTS_ENCLOSED_FACADES_AND_FOUR_DISTINCT_STAGE_EXTERIOR_CUES__FRESH_PRO_VISUAL_GATE_REQUIRED__NOT_PROMOTED"
    if not failures else "FAIL__PRESS_TRAIN_A_V037_STAGE_EXTERIOR_CUE_STATIC_GATE__NOT_PROMOTED"
)
OUT.write_text(json.dumps(report, indent=2), encoding="utf-8")
print(json.dumps({"v037_stage_cue_count": len(cue_actors), "failures": failures}, indent=2))
if failures:
    raise RuntimeError("; ".join(failures))
