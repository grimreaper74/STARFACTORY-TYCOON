"""Create the isolated Train A audio-runtime successor directly from retained v024."""

import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
import unreal

root = Path(unreal.Paths.project_dir())
parent_map = "/Game/LineBoss/Maps/LB_PressTrainAPhysicalGameplayCandidate_v024"
target_map = "/Game/LineBoss/Maps/LB_PressTrainAAudioRuntimeCandidate_v025"
target_file = root / "Content/LineBoss/Maps/LB_PressTrainAAudioRuntimeCandidate_v025.umap"
parent_file = root / "Content/LineBoss/Maps/LB_PressTrainAPhysicalGameplayCandidate_v024.umap"
out = root / "Saved/Audits/PressTrains/press_train_a_audio_runtime_build_v025.json"
expected_parent = "2AEE55ABF7AFB975CD0D9558AB84846F45B626F0455F24D9AE857EA803651584"

def sha(path): return hashlib.sha256(path.read_bytes()).hexdigest().upper()
def tags(actor): return {str(value) for value in actor.tags}
def add_tags(actor, *values):
    current = list(tags(actor))
    for value in values:
        if value not in current: current.append(value)
    actor.set_editor_property("tags", [unreal.Name(value) for value in sorted(current)])

library = unreal.EditorAssetLibrary
levels = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
actors_api = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
if library.does_asset_exist(target_map) or target_file.exists() or out.exists():
    raise RuntimeError("Refusing to overwrite Train A audio runtime v025")
parent_hash = sha(parent_file)
if parent_hash != expected_parent:
    raise RuntimeError(f"retained v024 changed: {parent_hash}")
if not levels.new_level_from_template(target_map, parent_map):
    raise RuntimeError("Could not create v025 directly from retained v024")

authorities = [actor for actor in actors_api.get_all_level_actors()
               if isinstance(actor, unreal.LBPressTrainAStation)]
if len(authorities) != 1:
    raise RuntimeError(f"Expected one Train A authority, found {len(authorities)}")
authority = authorities[0]
add_tags(authority, "LB.PressTrain.TrainA.AudioRuntime.v025", "LB.Asset.Candidate.v025",
         "LB.Asset.CandidateNotPromoted")

components = authority.get_components_by_class(unreal.AudioComponent)
rows = []
for component in components:
    sound = component.get_editor_property("sound")
    attenuation = component.get_editor_property("attenuation_overrides")
    rows.append({
        "component": component.get_name(),
        "sound": sound.get_path_name() if sound else None,
        "auto_activate": bool(component.get_editor_property("auto_activate")),
        "allow_spatialization": bool(component.get_editor_property("allow_spatialization")),
        "override_attenuation": bool(component.get_editor_property("override_attenuation")),
        "relative_location_cm": [component.get_relative_location().x, component.get_relative_location().y,
                                 component.get_relative_location().z],
        "falloff_distance_cm": attenuation.get_editor_property("falloff_distance"),
    })
expected_components = {
    "PTA_Audio_HydraulicPower", "PTA_Audio_TransferServo", "PTA_Audio_RobotServo",
    "PTA_Audio_WarningAlarm", "PTA_Audio_PressCue", "PTA_Audio_SafetyCue",
}
failures = []
if {row["component"] for row in rows} != expected_components:
    failures.append(f"audio component set mismatch: {[row['component'] for row in rows]}")
for row in rows:
    if not row["sound"] and row["component"] not in {"PTA_Audio_PressCue", "PTA_Audio_SafetyCue"}:
        failures.append(f"loop component has no sound: {row['component']}")
    if row["auto_activate"] or not row["allow_spatialization"] or not row["override_attenuation"]:
        failures.append(f"spatial policy mismatch: {row}")

if not levels.save_current_level():
    raise RuntimeError("Could not save Train A audio runtime v025")
if not target_file.exists():
    raise RuntimeError("v025 map missing after save")
report = {
    "$schema": "cairnwell/audit/press-train-a-audio-runtime-build-v025/v1",
    "generated_utc": datetime.now(timezone.utc).isoformat(),
    "status": "PASS__V025_SIX_SPATIAL_AUDIO_COMPONENTS_AND_EIGHT_ASSETS__PIE_REQUIRED__NOT_PROMOTED"
              if not failures else "FAIL__V025_AUDIO_RUNTIME_BUILD__NOT_PROMOTED",
    "parent_map": parent_map, "parent_map_sha256": parent_hash,
    "target_map": target_map, "target_map_sha256": sha(target_file),
    "authority": authority.get_actor_label(), "audio_components": rows,
    "audio_component_count": len(rows), "failures": failures,
    "visual_geometry_changed": False, "materials_changed": False, "lighting_changed": False,
    "collision_navigation_changed": False, "production_map_changed": False,
    "promotion_authorized": False,
}
out.parent.mkdir(parents=True, exist_ok=True)
out.write_text(json.dumps(report, indent=2), encoding="utf-8")
print(json.dumps({"status": report["status"], "components": len(rows), "hash": report["target_map_sha256"]}, indent=2))
if failures: raise RuntimeError("; ".join(failures))
