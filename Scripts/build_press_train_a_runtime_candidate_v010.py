"""Create isolated Train A v010 by adding one native runtime authority to retained v009."""

import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path

import unreal


ROOT = Path(unreal.Paths.project_dir())
SOURCE_MAP = "/Game/LineBoss/Maps/LB_PressTrainAAssemblyStudyDetailCandidate_v009"
MAP = "/Game/LineBoss/Maps/LB_PressTrainARuntimeCandidate_v010"
OUT = ROOT / "Saved/Audits/PressTrains/press_train_a_runtime_build_v010.json"
SOURCE_MAP_FILE = ROOT / "Content/LineBoss/Maps/LB_PressTrainAAssemblyStudyDetailCandidate_v009.umap"
TARGET_MAP_FILE = ROOT / "Content/LineBoss/Maps/LB_PressTrainARuntimeCandidate_v010.umap"

library = unreal.EditorAssetLibrary
levels = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
actors = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
if library.does_asset_exist(MAP) or OUT.exists():
    raise RuntimeError("Refusing to overwrite Train A runtime v010")
if not levels.new_level_from_template(MAP, SOURCE_MAP):
    raise RuntimeError("Could not create v010 from retained v009")


def tag_strings(actor):
    return [str(value) for value in actor.tags]


def set_tags(actor, values):
    actor.set_editor_property("tags", [unreal.Name(value) for value in values])


presentation_count = 0
binding_counts = {"destack": 0, "transfer": 0, "unload_robot": 0, "formed_panel": 0}
for actor in actors.get_all_level_actors():
    values = [value for value in tag_strings(actor) if value != "LB.Runtime.Authority.NotImplemented"]
    for value in (
        "LB.PressTrain.TrainA.Runtime.v010",
        "LB.Asset.Candidate.v010",
        "LB.Asset.CandidateNotPromoted",
        "LB.Runtime.Authority.NativeImplemented",
        "LB.Authority.WorldPlacement.TBCNotInvented",
    ):
        if value not in values:
            values.append(value)
    set_tags(actor, values)
    roles = [value for value in values if value.startswith("LB.PressTrain.Role.")]
    if roles:
        presentation_count += 1
    if "LB.PressTrain.Role.destack_lift" in values:
        binding_counts["destack"] += 1
    if "LB.PressTrain.Role.transfer_crossbar" in values or "LB.PressTrain.Role.transfer_gripper" in values:
        binding_counts["transfer"] += 1
    if any(value in values for value in (
        "LB.PressTrain.Role.unload_robot_arm", "LB.PressTrain.Role.unload_robot_joint",
        "LB.PressTrain.Role.unload_robot_wrist", "LB.PressTrain.Role.unload_robot_gripper")):
        binding_counts["unload_robot"] += 1
    if "LB.PressTrain.Role.visible_formed_panel" in values or "LB.PressTrain.Role.formed_panel_positive_y_discharge" in values:
        binding_counts["formed_panel"] += 1

authority_class = unreal.load_class(None, "/Script/LineBossCarFactory.LBPressTrainAStation")
if not authority_class:
    raise RuntimeError("Native ALBPressTrainAStation class is unavailable")
authority = actors.spawn_actor_from_class(authority_class, unreal.Vector(), unreal.Rotator())
if not authority:
    raise RuntimeError("Could not spawn native Train A authority")
authority.set_actor_label("CA_MW_PTA_NativeAuthority_v010")
set_tags(authority, [
    "LB.PressTrain.TrainA.Runtime.v010", "LB.Asset.Candidate.v010", "LB.Asset.CandidateNotPromoted",
    "LB.PressTrain.Authority.Native", "LB.Runtime.Authority.NativeImplemented",
    "LB.Authority.Remote.CW.MW.CONTROL_ROOM", "LB.Authority.WorldPlacement.TBCNotInvented",
])

hmi = actors.spawn_actor_from_class(unreal.TextRenderActor, unreal.Vector(360.0, 2250.0, 260.0), unreal.Rotator(0.0, 180.0, 0.0))
if not hmi:
    raise RuntimeError("Could not spawn Train A live-state evidence text")
hmi.set_actor_label("CA_MW_PTA_HMI_LiveState_v010")
hmi.text_render.set_text("TRAIN A | ISOLATED | NATIVE AUTHORITY v010")
hmi.text_render.set_editor_property("world_size", 24.0)
hmi.text_render.set_editor_property("horizontal_alignment", unreal.HorizTextAligment.EHTA_CENTER)
hmi.text_render.set_text_render_color(unreal.Color(225, 166, 0, 255))
set_tags(hmi, [
    "LB.PressTrain.TrainA.Runtime.v010", "LB.Asset.Candidate.v010", "LB.Asset.CandidateNotPromoted",
    "LB.HMI.PressTrainA.LiveState", "LB.Validation.RuntimeEvidence",
    "LB.Authority.WorldPlacement.TBCNotInvented",
])

if not levels.save_current_level():
    raise RuntimeError("Could not save Train A runtime v010")
if not TARGET_MAP_FILE.exists():
    raise RuntimeError("Train A runtime v010 map file is missing after save")


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest().upper()


report = {
    "$schema": "cairnwell/audit/press-train-a-runtime-build-v010/v1",
    "generated_utc": datetime.now(timezone.utc).isoformat(),
    "status": "PASS__ISOLATED_NATIVE_TRAIN_A_AUTHORITY_ADDED__RUNTIME_STATIC_AND_VISUAL_GATES_REQUIRED__NOT_PROMOTED",
    "source_map": SOURCE_MAP,
    "source_map_sha256": sha(SOURCE_MAP_FILE),
    "map": MAP,
    "map_sha256": sha(TARGET_MAP_FILE),
    "native_authority_count": 1,
    "presentation_actor_count": presentation_count,
    "binding_role_counts": binding_counts,
    "live_hmi_evidence_count": 1,
    "save_root_format": 11,
    "world_placement": "TBC_NOT_INVENTED",
    "production_map_changed": False,
    "promotion_authorized": False,
}
OUT.parent.mkdir(parents=True, exist_ok=True)
OUT.write_text(json.dumps(report, indent=2), encoding="utf-8")
print(json.dumps(report, indent=2))

