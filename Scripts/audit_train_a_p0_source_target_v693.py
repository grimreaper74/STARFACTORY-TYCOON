"""Read-only source/target transform inventory for P0 motion separation."""
from pathlib import Path
from datetime import datetime, timezone
import json
import unreal

ROOT = Path(unreal.Paths.project_dir())
SOURCE_MAP = "/Game/LineBoss/Maps/LB_PressTrainAPhysicalGameplayCandidate_v024"
TARGET_MAP = "/Game/LineBoss/Developer/Validation/PressTrains/LB_PressTrainA_RuntimeNav_v673"
OUT = ROOT / r"Saved\Audits\PressTrains\complete_train_a_p0_source_target_v693.json"
levels = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
actors = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
if OUT.exists():
    raise RuntimeError("Refusing to overwrite v693")

def actor_row(actor):
    component = actor.get_component_by_class(unreal.StaticMeshComponent)
    mesh = component.get_editor_property("static_mesh") if component else None
    origin, extent = actor.get_actor_bounds(False, False)
    transform = actor.get_actor_transform()
    return {
        "label": actor.get_actor_label(),
        "tags": [str(tag) for tag in actor.tags],
        "mesh": mesh.get_path_name() if mesh else None,
        "location_cm": [transform.translation.x, transform.translation.y, transform.translation.z],
        "rotation_deg": [transform.rotation.rotator().roll, transform.rotation.rotator().pitch, transform.rotation.rotator().yaw],
        "scale": [transform.scale3d.x, transform.scale3d.y, transform.scale3d.z],
        "bounds_origin_cm": [origin.x, origin.y, origin.z],
        "bounds_extent_cm": [extent.x, extent.y, extent.z],
    }

if not levels.load_level(SOURCE_MAP):
    raise RuntimeError("Could not load source v024")
source_rows = []
source_tokens = (
    "LB.PressTrain.Role.destack_lift",
    "LB.PressTrain.Role.destack_head",
    "LB.PressTrain.Role.transfer_crossbar",
    "LB.PressTrain.Role.unload_robot_",
    "LB.PressTrain.Role.unload_robot_arm",
    "LB.PressTrain.Role.unload_robot_joint",
    "LB.PressTrain.Role.unload_robot_wrist",
    "LB.PressTrain.Role.unload_robot_gripper",
)
for actor in actors.get_all_level_actors():
    tag_text = " ".join(str(tag) for tag in actor.tags)
    if any(token in tag_text for token in source_tokens):
        source_rows.append(actor_row(actor))

if not levels.load_level(TARGET_MAP):
    raise RuntimeError("Could not load target v673")
target_rows = []
for actor in actors.get_all_level_actors():
    label = actor.get_actor_label()
    if any(token in label for token in ("DestackBlankFeed", "TR_Transfer", "InspectUnload")):
        target_rows.append(actor_row(actor))

OUT.parent.mkdir(parents=True, exist_ok=True)
OUT.write_text(json.dumps({
    "revision": "v693",
    "generated_utc": datetime.now(timezone.utc).isoformat(),
    "status": "PASS__READ_ONLY_P0_SOURCE_TARGET_INVENTORY",
    "source_map": SOURCE_MAP,
    "target_map": TARGET_MAP,
    "source_rows": source_rows,
    "target_rows": target_rows,
    "protected_map_modified": False,
}, indent=2), encoding="utf-8")
unreal.log("LINE_BOSS_COMPLETE_TRAIN_A_P0_SOURCE_TARGET_V693_PASS")
