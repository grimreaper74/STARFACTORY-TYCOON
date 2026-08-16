"""Exact-map static and authority gate for isolated Press Train A v001."""

import json
from datetime import datetime, timezone
from pathlib import Path

import unreal


ROOT = Path(unreal.Paths.project_dir())
MAP = "/Game/LineBoss/Maps/LB_PressTrainAIsolatedCandidate_v001"
DEST = "/Game/LineBoss/Candidates/PressTrains/Shared/Blockout_v001"
OUT = ROOT / "Saved/Audits/PressTrains/press_train_a_isolated_static_v001.json"
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
cameras = [actor for actor in scope if isinstance(actor, unreal.CameraActor) and "LB.Camera.Fixed" in tags(actor)]
texts = [actor for actor in scope if isinstance(actor, unreal.TextRenderActor)]
candidate_tags = sum(any(tag.startswith("LB.Asset.Candidate") for tag in tags(actor)) for actor in scope)
world_tbc_tags = sum("LB.Authority.WorldPlacement.TBCNotInvented" in tags(actor) for actor in scope)

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
if len(presentation) != 37:
    failures.append(f"expected 37 presentation mesh actors, found {len(presentation)}")
if len(stages) != 7:
    failures.append(f"expected seven stage shells, found {len(stages)}")
if len(movers) != 22:
    failures.append(f"expected 22 moving presentation actors, found {len(movers)}")
if len(tooling) != 5:
    failures.append(f"expected five recipe die actors, found {len(tooling)}")
if len(cameras) != 3:
    failures.append(f"expected three fixed cameras, found {len(cameras)}")
if len(texts) != 8:
    failures.append(f"expected eight identity text actors, found {len(texts)}")
if any(value > limit + 5 for value, limit in zip(aggregate_mm, (15000, 56000, 11500))):
    failures.append(f"aggregate visual bounds exceed shared train envelope: {aggregate_mm}")
if candidate_tags != len(scope):
    failures.append(f"candidate tag missing from {len(scope) - candidate_tags} scoped actors")
if world_tbc_tags != len(scope):
    failures.append(f"TBC world-placement authority tag missing from {len(scope) - world_tbc_tags} scoped actors")
text_values = [str(actor.text_render.get_editor_property("text")) for actor in texts]
if any("LINE BOSS" in value.upper() or "LINEBOSS" in value.upper() for value in text_values):
    failures.append("working-title branding found in visible Train A text")
if not any("CAIRNWELL AUTOMOTIVE" in value.upper() and "MOORCROSS WORKS" in value.upper() for value in text_values):
    failures.append("Cairnwell Automotive / Moorcross Works identity missing")
required_assets = [f"{DEST}/{name}" for name in (
    "SM_CA_MW_PT_CommonPlatform_v001", "SM_CA_MW_PT_CommonUtilitySpine_v001",
    "SM_CA_MW_PT_TransferRail_v001", "SM_CA_MW_PT_PressFrame_Draw_v001",
    "SM_CA_MW_PT_PressFrame_Form_v001", "SM_CA_MW_PT_PressFrame_Trim_v001",
    "SM_CA_MW_PT_PressFrame_Pierce_v001", "SM_CA_MW_PT_PressFrame_Flange_v001",
    "SM_CA_MW_PT_DestackLoadCell_v001", "SM_CA_MW_PT_UnloadInspectCell_v001",
    "SM_CA_MW_PT_PressSlide_v001", "SM_CA_MW_PT_MovingBolster_v001",
    "SM_CA_MW_PT_StageDieSet_v001", "SM_CA_MW_PT_DieCart_v001",
    "SM_CA_MW_PT_TransferCrossbar_v001", "SM_CA_MW_PT_DestackLift_v001")]
missing_assets = [path for path in required_assets if not library.does_asset_exist(path)]
if missing_assets:
    failures.append(f"missing imported assets: {missing_assets}")

report = {
    "$schema": "cairnwell/audit/press-train-a-isolated-static-v001/v1",
    "generated_utc": datetime.now(timezone.utc).isoformat(),
    "status": "PASS__PRESS_TRAIN_A_V001_EXACT_MAP_SEVEN_STAGES_MOVERS_TOOLING_ENVELOPE_BRANDING_TBC_AUTHORITY__VISUAL_RUNTIME_COLLISION_NAV_SAVE_GATES_REQUIRED__NOT_PROMOTED" if not failures else "FAIL__PRESS_TRAIN_A_V001_STATIC__NOT_PROMOTED",
    "map": MAP,
    "scope_actor_count": len(scope),
    "presentation_mesh_actor_count": len(presentation),
    "stage_shell_count": len(stages),
    "mover_count": len(movers),
    "tooling_count": len(tooling),
    "fixed_camera_count": len(cameras),
    "identity_text_count": len(texts),
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
