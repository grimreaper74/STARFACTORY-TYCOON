"""Add a non-gameplay floor to the readable v684 visual-review map."""
from pathlib import Path
from datetime import datetime, timezone
import json
import unreal

ROOT = Path(unreal.Paths.project_dir())
BASE = "/Game/LineBoss/Developer/Validation/PressTrains/LB_PressTrainA_VisualReview_v684"
MAP = "/Game/LineBoss/Developer/Validation/PressTrains/LB_PressTrainA_VisualReviewFloor_v686"
OUT = ROOT / r"Saved\Audits\PressTrains\complete_train_a_floor_visual_review_build_v686.json"
levels = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
actors = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
library = unreal.EditorAssetLibrary
if library.does_asset_exist(MAP) or OUT.exists():
    raise RuntimeError("Refusing to overwrite v686")
if not levels.new_level_from_template(MAP, BASE):
    raise RuntimeError("Could not derive v686")

for actor in actors.get_all_level_actors():
    label = actor.get_actor_label()
    if label.startswith("LB_CAM_TrainA_") and label.endswith("_v684"):
        actor.set_actor_label(label.replace("_v684", "_v686"))

cube = unreal.load_asset("/Engine/BasicShapes/Cube.Cube")
if not cube:
    raise RuntimeError("Engine cube unavailable")
floor = actors.spawn_actor_from_object(
    cube, unreal.Vector(0, 2100, -12), unreal.Rotator())
floor.set_actor_label("LB_TrainA_ReviewFloor_v686")
floor.set_actor_scale3d(unreal.Vector(34.0, 72.0, 0.12))
floor.tags = [
    unreal.Name("LB.VisualGate.ReviewFloor"),
    unreal.Name("LB.Asset.ValidationOnly"),
    unreal.Name("LB.Asset.CandidateNotPromoted"),
]
component = floor.get_component_by_class(unreal.StaticMeshComponent)
component.set_collision_enabled(unreal.CollisionEnabled.NO_COLLISION)
material = unreal.load_asset("/Engine/BasicShapes/BasicShapeMaterial.BasicShapeMaterial")
if material:
    component.set_material(0, material)

unreal.AutomationUtilsBlueprintLibrary.finish_all_asset_compilation()
if not levels.save_current_level():
    raise RuntimeError("Failed saving v686")
OUT.parent.mkdir(parents=True, exist_ok=True)
OUT.write_text(json.dumps({
    "revision": "v686",
    "generated_utc": datetime.now(timezone.utc).isoformat(),
    "status": "PASS__READABLE_REVIEW_MAP_WITH_NON_GAMEPLAY_FLOOR__CAPTURE_PENDING",
    "map": MAP,
    "source": BASE,
    "review_floor_cm": [3400, 7200, 12],
    "review_floor_collision": "NO_COLLISION",
    "gameplay_collision_unchanged": True,
    "protected_map_modified": False,
    "promotion_authorized": False,
}, indent=2), encoding="utf-8")
unreal.log("LINE_BOSS_COMPLETE_TRAIN_A_FLOOR_VISUAL_BUILD_V686_PASS")
