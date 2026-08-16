"""Add separated, already-owned P0 mover presentations to the passing v673 Train A map."""
from pathlib import Path
from datetime import datetime, timezone
import json
import unreal

ROOT = Path(unreal.Paths.project_dir())
BASE = "/Game/LineBoss/Developer/Validation/PressTrains/LB_PressTrainA_RuntimeNav_v673"
MAP = "/Game/LineBoss/Developer/Validation/PressTrains/LB_PressTrainA_RuntimeP0_v694"
OUT = ROOT / r"Saved\Audits\PressTrains\complete_train_a_p0_motion_build_v694.json"
SOURCE_INVENTORY = ROOT / r"Saved\Audits\PressTrains\complete_train_a_p0_source_target_v693.json"
PHYSICAL_AUDIT = ROOT / r"Saved\Audits\PressTrains\press_train_a_physical_gameplay_build_v024.json"
levels = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
actors = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
library = unreal.EditorAssetLibrary
if library.does_asset_exist(MAP) or OUT.exists():
    raise RuntimeError("Refusing to overwrite v694")
if not levels.new_level_from_template(MAP, BASE):
    raise RuntimeError("Could not derive v694")

source = json.loads(SOURCE_INVENTORY.read_text(encoding="utf-8"))
physical = json.loads(PHYSICAL_AUDIT.read_text(encoding="utf-8"))
source_mesh_by_label = {row["actor"]: row["source_mesh"] for row in physical["actors"]}
source_rows = {row["label"]: row for row in source["source_rows"]}
target_rows = {row["label"]: row for row in source["target_rows"]}
spawned = []

def spawn(label, mesh_path, location, role, stage, rotation=unreal.Rotator()):
    mesh = unreal.load_asset(mesh_path)
    if not isinstance(mesh, unreal.StaticMesh):
        raise RuntimeError(f"Missing separated P0 mesh {mesh_path}")
    actor = actors.spawn_actor_from_object(mesh, unreal.Vector(*location), rotation)
    actor.set_actor_label(label)
    actor.tags = [
        unreal.Name("LB.PressTrain.Installed.TRAIN_A"),
        unreal.Name("LB.PressTrain.ProcessDirection.PositiveY"),
        unreal.Name(f"LB.PressTrain.Stage.{stage}"),
        unreal.Name(f"LB.PressTrain.Role.{role}"),
        unreal.Name("LB.Presentation.VisualOnly"),
        unreal.Name("LB.P0.SeparatedPresentation.v694"),
        unreal.Name("LB.Asset.ReusedOwnedSource"),
        unreal.Name("LB.Asset.CandidateNotPromoted"),
    ]
    component = actor.get_component_by_class(unreal.StaticMeshComponent)
    component.set_collision_enabled(unreal.CollisionEnabled.NO_COLLISION)
    component.set_editor_property("can_ever_affect_navigation", False)
    spawned.append({
        "label": label,
        "mesh": mesh_path,
        "role": role,
        "stage": stage,
        "location_cm": list(location),
    })
    return actor

# The retained combined meshes remain static background detail. Remove only the
# misleading pending tag; their collision remains the already-passing proxy set.
for actor in actors.get_all_level_actors():
    if any(token in actor.get_actor_label() for token in ("DestackBlankFeed", "TR_Transfer", "InspectUnload")):
        actor.tags = [tag for tag in actor.tags if str(tag) != "LB.RuntimeMovingPartSeparation.Pending"]
        actor.tags.append(unreal.Name("LB.P0.CombinedBackgroundStatic.v694"))

# Destack lift components are translated so their source lift centre coincides
# exactly with the retained combined destacker's actor origin.
destack_target = target_rows["SM_CA_MW_PTA_S01_DestackBlankFeed_v662"]["location_cm"]
destack_offset = [destack_target[0], destack_target[1] + 320.0, 0.0]
for label in (
    "PTA_S01_LiftColumn_-1200_UEv024",
    "PTA_S01_LiftColumn_1200_UEv024",
    "PTA_S01_LiftTable_UEv024",
):
    row = source_rows[label]
    location = [row["location_cm"][i] + destack_offset[i] for i in range(3)]
    spawn(label.replace("UEv024", "P0v694"), source_mesh_by_label[label], location,
          "destack_lift", "S01")

# One isolated crossbar per inter-press gap, aligned to each retained transfer frame.
crossbar_mesh = source_mesh_by_label["PTA_S02_TransferCrossbar_v002_UEv024"]
for index, target_label in enumerate((
    "SM_CA_MW_PTA_TR_Transfer_01_v662",
    "SM_CA_MW_PTA_TR_Transfer_02_v662",
    "SM_CA_MW_PTA_TR_Transfer_03_v662",
    "SM_CA_MW_PTA_TR_Transfer_04_v662",
), 2):
    target = target_rows[target_label]["location_cm"]
    spawn(f"PTA_S{index:02d}_TransferCrossbar_P0v694", crossbar_mesh,
          [target[0], target[1], 195.0], "transfer_crossbar", f"S{index:02d}")

# Reuse the previously authored articulated unload robot. Preserve the source
# pose, translate it onto the v662 unload cell, and attach all moving links to
# the tagged shoulder root so native authority rotates the complete hierarchy.
robot_labels = (
    "PTA_S07_RuntimeRobotBase_v003_UEv024",
    "PTA_S07_RuntimeRobotShoulder_v003_UEv024",
    "PTA_S07_RuntimeRobotUpperArm_v003_UEv024",
    "PTA_S07_RuntimeRobotElbow_v003_UEv024",
    "PTA_S07_RuntimeRobotForearm_v003_UEv024",
    "PTA_S07_RuntimeRobotWrist_v003_UEv024",
    "PTA_S07_RuntimeRobotGripper_v003_UEv024",
    "PTA_S07_RuntimeVacuumCup_-600_v003_UEv024",
    "PTA_S07_RuntimeVacuumCup_600_v003_UEv024",
)
role_by_label = {
    "Base": "unload_robot_base_runtime",
    "Shoulder": "unload_robot_shoulder_runtime",
    "UpperArm": "unload_robot_upper_arm_runtime",
    "Elbow": "unload_robot_elbow_runtime",
    "Forearm": "unload_robot_forearm_runtime",
    "Wrist": "unload_robot_wrist_runtime",
    "Gripper": "unload_robot_gripper_runtime",
    "VacuumCup": "unload_robot_tool_runtime",
}
unload_target = target_rows["SM_CA_MW_PTA_S07_InspectUnload_v662"]["location_cm"]
robot_offset = [0.0, unload_target[1] - 4720.0001, 0.0]
robot_actors = {}
for label in robot_labels:
    row = source_rows[label]
    location = [row["location_cm"][i] + robot_offset[i] for i in range(3)]
    role = next(value for token, value in role_by_label.items() if token in label)
    robot_actors[label] = spawn(label.replace("UEv024", "P0v694"),
                                source_mesh_by_label[label], location, role, "S07")
shoulder = robot_actors["PTA_S07_RuntimeRobotShoulder_v003_UEv024"]
for label, actor in robot_actors.items():
    if actor == shoulder or "Base" in label:
        continue
    if not actor.attach_to_actor(
            shoulder, unreal.Name(), unreal.AttachmentRule.KEEP_WORLD,
            unreal.AttachmentRule.KEEP_WORLD, unreal.AttachmentRule.KEEP_WORLD, False):
        raise RuntimeError(f"Could not attach unload hierarchy actor {label}")

unreal.AutomationUtilsBlueprintLibrary.finish_all_asset_compilation()
if not levels.save_current_level():
    raise RuntimeError("Failed saving v694")
OUT.parent.mkdir(parents=True, exist_ok=True)
OUT.write_text(json.dumps({
    "revision": "v694",
    "generated_utc": datetime.now(timezone.utc).isoformat(),
    "status": "PASS__SEPARATED_P0_PRESENTATIONS_BOUND__PIE_PENDING",
    "map": MAP,
    "source_map": BASE,
    "spawned_actor_count": len(spawned),
    "role_counts": {
        role: sum(1 for row in spawned if row["role"] == role)
        for role in sorted(set(row["role"] for row in spawned))
    },
    "spawned": spawned,
    "combined_sources_retained_static": True,
    "gameplay_collision_unchanged": True,
    "navigation_geometry_unchanged": True,
    "meshy_credits_used": 0,
    "protected_map_modified": False,
    "promotion_authorized": False,
}, indent=2), encoding="utf-8")
unreal.log("LINE_BOSS_COMPLETE_TRAIN_A_P0_MOTION_BUILD_V694_PASS")
