"""Exact isolated static gate for Train A native runtime candidate v010."""

import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path

import unreal


ROOT = Path(unreal.Paths.project_dir())
MAP = "/Game/LineBoss/Maps/LB_PressTrainARuntimeCandidate_v010"
SOURCE_MAP = "/Game/LineBoss/Maps/LB_PressTrainAAssemblyStudyDetailCandidate_v009"
OUT = ROOT / "Saved/Audits/PressTrains/press_train_a_runtime_static_v010.json"
MAP_FILE = ROOT / "Content/LineBoss/Maps/LB_PressTrainARuntimeCandidate_v010.umap"
SOURCE_MAP_FILE = ROOT / "Content/LineBoss/Maps/LB_PressTrainAAssemblyStudyDetailCandidate_v009.umap"
PROTECTED = {
    "v107": (ROOT / "Content/LineBoss/Maps/LB_PressShop_IntegratedEnvironmentCandidate_v107.umap",
             "E6851D041D3D566B2FE32560F331725CBB1FE84B034E7B86DA9B0D33191ECF77"),
    "v213": (ROOT / "Content/LineBoss/Maps/LB_PressShop_CumulativeReleaseCandidate_v213.umap",
             "1790B48ABF75762A474C6F3FDB91B2ABD3AD9088B5430D08DC1905154CDF6554"),
}

levels = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
actors_api = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
if not levels.load_level(MAP):
    raise RuntimeError(MAP)
actors = actors_api.get_all_level_actors()


def tags(actor):
    return {str(value) for value in actor.tags}


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest().upper()


failures = []
authorities = [actor for actor in actors if isinstance(actor, unreal.LBPressTrainAStation)]
if len(authorities) != 1:
    failures.append(f"Expected exactly one native Train A authority, found {len(authorities)}")
presentation = [actor for actor in actors if any(value.startswith("LB.PressTrain.Role.") for value in tags(actor))]
if len(presentation) != 309:
    failures.append(f"Expected 309 v002 presentation actors, found {len(presentation)}")
not_implemented = [actor.get_actor_label() for actor in actors if "LB.Runtime.Authority.NotImplemented" in tags(actor)]
if not_implemented:
    failures.append(f"Contradictory runtime-not-implemented tags remain: {len(not_implemented)}")
runtime_scoped = [actor for actor in actors if "LB.PressTrain.TrainA.Runtime.v010" in tags(actor)
                  or "LB.Asset.Candidate.v010" in tags(actor)]
runtime_lineage_missing = [actor.get_actor_label() for actor in runtime_scoped
                           if "LB.Runtime.Authority.NativeImplemented" not in tags(actor)
                           and "LB.HMI.PressTrainA.LiveState" not in tags(actor)]
if runtime_lineage_missing:
    failures.append(f"Scoped v010 runtime-lineage tags missing: {runtime_lineage_missing}")

binding_counts = {
    "destack": sum("LB.PressTrain.Role.destack_lift" in tags(actor) for actor in actors),
    "transfer": sum("LB.PressTrain.Role.transfer_crossbar" in tags(actor)
                    or "LB.PressTrain.Role.transfer_gripper" in tags(actor) for actor in actors),
    "unload_robot": sum(any(value in tags(actor) for value in (
        "LB.PressTrain.Role.unload_robot_arm", "LB.PressTrain.Role.unload_robot_joint",
        "LB.PressTrain.Role.unload_robot_wrist", "LB.PressTrain.Role.unload_robot_gripper")) for actor in actors),
    "formed_panel": sum("LB.PressTrain.Role.visible_formed_panel" in tags(actor)
                        or "LB.PressTrain.Role.formed_panel_positive_y_discharge" in tags(actor) for actor in actors),
}
expected_bindings = {"destack": 3, "transfer": 25, "unload_robot": 8, "formed_panel": 2}
if binding_counts != expected_bindings:
    failures.append(f"Presentation binding-role mismatch: {binding_counts}")
hmi = [actor for actor in actors if "LB.HMI.PressTrainA.LiveState" in tags(actor)]
if len(hmi) != 1 or not isinstance(hmi[0], unreal.TextRenderActor):
    failures.append(f"Expected one live Train A HMI text actor, found {len(hmi)}")

component_names = []
if len(authorities) == 1:
    component_names = sorted(component.get_name() for component in authorities[0].get_components_by_class(unreal.SceneComponent))
    expected_components = {
        "PTA_StationRoot", "PTA_DestackLiftMover", "PTA_TransferLiftMover", "PTA_TransferPitchMover",
        "PTA_S02SlideMover", "PTA_S03SlideMover", "PTA_S04SlideMover", "PTA_S05SlideMover",
        "PTA_S06SlideMover", "PTA_UnloadRobotMover", "PTA_FormedPanelMover",
    }
    missing = sorted(expected_components - set(component_names))
    if missing:
        failures.append(f"Native logical mover components missing: {missing}")

source_hash = sha(SOURCE_MAP_FILE)
if source_hash != "ECEBA05566328E4DAE480BD58EAD543F6442E6B7558440E3004C57A43F97696A":
    failures.append(f"Retained v009 source map changed: {source_hash}")
protected_hashes = {}
for key, (path, expected) in PROTECTED.items():
    actual = sha(path)
    protected_hashes[key] = actual
    if actual != expected:
        failures.append(f"Protected {key} changed: {actual}")

report = {
    "$schema": "cairnwell/audit/press-train-a-runtime-static-v010/v1",
    "generated_utc": datetime.now(timezone.utc).isoformat(),
    "status": "PASS__V010_NATIVE_AUTHORITY_STATIC_BINDING_LINEAGE_SAVE_ROOT_GATE__RUNTIME_PIE_AND_VISUAL_OPEN__NOT_PROMOTED" if not failures else "FAIL__V010_NATIVE_AUTHORITY_STATIC_GATE__NOT_PROMOTED",
    "map": MAP,
    "map_sha256": sha(MAP_FILE),
    "source_map": SOURCE_MAP,
    "source_map_sha256": source_hash,
    "native_authority_count": len(authorities),
    "presentation_actor_count": len(presentation),
    "binding_role_counts": binding_counts,
    "logical_mover_component_names": component_names,
    "live_hmi_count": len(hmi),
    "runtime_not_implemented_tag_count": len(not_implemented),
    "runtime_scoped_actor_count": len(runtime_scoped),
    "runtime_lineage_missing": runtime_lineage_missing,
    "save_root_format": 11,
    "protected_map_hashes": protected_hashes,
    "world_placement": "TBC_NOT_INVENTED",
    "failures": failures,
    "production_map_changed": False,
    "promotion_authorized": False,
}
OUT.parent.mkdir(parents=True, exist_ok=True)
OUT.write_text(json.dumps(report, indent=2), encoding="utf-8")
print(json.dumps(report, indent=2))
if failures:
    raise RuntimeError("; ".join(failures))
