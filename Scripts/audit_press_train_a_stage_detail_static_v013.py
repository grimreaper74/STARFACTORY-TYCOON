"""Exact-map static/authority gate for isolated Train A v013."""

import json
from datetime import datetime, timezone
from pathlib import Path

import unreal


ROOT = Path(unreal.Paths.project_dir())
MAP = "/Game/LineBoss/Maps/LB_PressTrainAStageDetailCandidate_v013"
PRESENTATION = "/Game/LineBoss/Candidates/PressTrains/Shared/Presentation_v003"
MECHANICAL = "/Game/LineBoss/Candidates/PressTrains/Shared/MechanicalBay_v001/SM_CA_MW_PT_MechanicalBayDress_v001"
DETAIL = "/Game/LineBoss/Candidates/PressTrains/Shared/StageDetail_v001"
OUT = ROOT / "Saved/Audits/PressTrains/press_train_a_stage_detail_static_v013.json"
levels = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
actors_api = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
library = unreal.EditorAssetLibrary
if not levels.load_level(MAP):
    raise RuntimeError(MAP)
actors = list(actors_api.get_all_level_actors())


def tags(actor):
    return {str(tag) for tag in actor.tags}


scope = [actor for actor in actors if "LB.PressTrain.TrainA.Isolated" in tags(actor)]
presentation = [actor for actor in scope if isinstance(actor, unreal.StaticMeshActor) and "LB.Validation.Environment" not in tags(actor)]
stages = [actor for actor in presentation if any(tag.startswith("LB.PressTrain.Stage.S") for tag in tags(actor))]
movers = [actor for actor in presentation if any(tag.startswith("LB.PressTrain.Mover.") for tag in tags(actor))]
tooling = [actor for actor in presentation if any(tag.startswith("LB.PressTrain.Tooling.") for tag in tags(actor))]
mechanical_bays = [actor for actor in presentation if "LB.PressTrain.Fixed.MechanicalBay" in tags(actor)]
details = [actor for actor in presentation if "LB.PressTrain.Fixed.StageDetail" in tags(actor)]
service = [actor for actor in details if any("RemoteService" in tag for tag in tags(actor))]
endpoints = [actor for actor in details if any(tag.endswith("Destack") or tag.endswith("UnloadInspect") for tag in tags(actor))]
process = [actor for actor in details if any(tag.endswith("ProcessService") for tag in tags(actor))]
cameras = [actor for actor in scope if isinstance(actor, unreal.CameraActor) and "LB.Camera.Fixed" in tags(actor)]
texts = [actor for actor in scope if isinstance(actor, unreal.TextRenderActor)]
candidate_v013 = sum("LB.Asset.Candidate.v013" in tags(actor) for actor in scope)
world_tbc = sum("LB.Authority.WorldPlacement.TBCNotInvented" in tags(actor) for actor in scope)

minimum = unreal.Vector(1e12, 1e12, 1e12)
maximum = unreal.Vector(-1e12, -1e12, -1e12)
for actor in presentation:
    origin, extent = actor.get_actor_bounds(False, False)
    minimum.x = min(minimum.x, origin.x - extent.x)
    minimum.y = min(minimum.y, origin.y - extent.y)
    minimum.z = min(minimum.z, origin.z - extent.z)
    maximum.x = max(maximum.x, origin.x + extent.x)
    maximum.y = max(maximum.y, origin.y + extent.y)
    maximum.z = max(maximum.z, origin.z + extent.z)
aggregate_mm = [round((maximum.x - minimum.x) * 10, 3), round((maximum.y - minimum.y) * 10, 3), round((maximum.z - minimum.z) * 10, 3)]

failures = []
expected = {
    "presentation": (len(presentation), 53), "stages": (len(stages), 7),
    "movers": (len(movers), 22), "tooling": (len(tooling), 5),
    "mechanical_bays": (len(mechanical_bays), 5), "details": (len(details), 11),
    "service": (len(service), 7), "endpoints": (len(endpoints), 2),
    "process": (len(process), 2), "cameras": (len(cameras), 3), "texts": (len(texts), 8),
}
for name, (actual, wanted) in expected.items():
    if actual != wanted:
        failures.append(f"expected {wanted} {name}, found {actual}")
if any(value > limit + 5 for value, limit in zip(aggregate_mm, (15000, 56000, 11500))):
    failures.append(f"aggregate visual bounds exceed shared train envelope: {aggregate_mm}")
if candidate_v013 != len(scope):
    failures.append(f"v013 candidate tag missing from {len(scope) - candidate_v013} scoped actors")
if world_tbc != len(scope):
    failures.append(f"TBC world authority missing from {len(scope) - world_tbc} scoped actors")
text_values = [str(actor.text_render.get_editor_property("text")) for actor in texts]
if any("LINE BOSS" in value.upper() or "LINEBOSS" in value.upper() for value in text_values):
    failures.append("working-title branding found in visible Train A text")
if not any("CAIRNWELL AUTOMOTIVE" in value.upper() and "MOORCROSS WORKS" in value.upper() for value in text_values):
    failures.append("Cairnwell Automotive / Moorcross Works identity missing")
required_assets = [MECHANICAL] + [f"{DETAIL}/{name}" for name in (
    "SM_CA_MW_PT_StageServicePack_v001", "SM_CA_MW_PT_S01DestackDetail_v001",
    "SM_CA_MW_PT_S07UnloadInspectDetail_v001", "SM_CA_MW_PT_MidTrainProcessService_v001")]
required_assets += [f"{PRESENTATION}/{name}" for name in (
    "SM_CA_MW_PT_CommonPlatform_v003", "SM_CA_MW_PT_CommonUtilitySpine_v003",
    "SM_CA_MW_PT_TransferRail_v003", "SM_CA_MW_PT_PressFrame_Draw_v003",
    "SM_CA_MW_PT_PressFrame_Form_v003", "SM_CA_MW_PT_PressFrame_Trim_v003",
    "SM_CA_MW_PT_PressFrame_Pierce_v003", "SM_CA_MW_PT_PressFrame_Flange_v003",
    "SM_CA_MW_PT_DestackLoadCell_v003", "SM_CA_MW_PT_UnloadInspectCell_v003",
    "SM_CA_MW_PT_PressSlide_v003", "SM_CA_MW_PT_MovingBolster_v003",
    "SM_CA_MW_PT_StageDieSet_v003", "SM_CA_MW_PT_DieCart_v003",
    "SM_CA_MW_PT_TransferCrossbar_v003", "SM_CA_MW_PT_DestackLift_v003")]
missing_assets = [path for path in required_assets if not library.does_asset_exist(path)]
if missing_assets:
    failures.append(f"missing imported assets: {missing_assets}")

report = {
    "$schema": "cairnwell/audit/press-train-a-stage-detail-static-v013/v1",
    "generated_utc": datetime.now(timezone.utc).isoformat(),
    "status": "PASS__PRESS_TRAIN_A_V013_EXACT_MAP_SEVEN_STAGES_MOVERS_TOOLING_MECHANICS_STAGE_DETAIL_ENVELOPE_BRANDING_TBC_AUTHORITY__FRESH_VISUAL_GATE_REQUIRED__NOT_PROMOTED" if not failures else "FAIL__PRESS_TRAIN_A_V013_STATIC__NOT_PROMOTED",
    "map": MAP,
    "counts": {name: actual for name, (actual, _wanted) in expected.items()},
    "scope_actor_count": len(scope),
    "aggregate_visual_bounds_mm": aggregate_mm,
    "world_placement": "TBC_NOT_INVENTED",
    "missing_assets": missing_assets,
    "failures": failures,
    "promotion_authorized": False,
    "press_shop_complete": False,
}
OUT.parent.mkdir(parents=True, exist_ok=True)
OUT.write_text(json.dumps(report, indent=2), encoding="utf-8")
print(json.dumps(report, indent=2))
if failures:
    raise RuntimeError("; ".join(failures))
