"""Prove audio-only v026 inherits v024 actors, transforms and physical policy exactly."""

import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
import unreal

root = Path(unreal.Paths.project_dir())
maps = {
    "v024": "/Game/LineBoss/Maps/LB_PressTrainAPhysicalGameplayCandidate_v024",
    "v026": "/Game/LineBoss/Maps/LB_PressTrainAAudioRuntimeCandidate_v026",
}
out = root / "Saved/Audits/PressTrains/press_train_a_audio_physical_inheritance_v026.json"
levels = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
actors_api = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)


def vec(value): return [round(value.x, 5), round(value.y, 5), round(value.z, 5)]
def rot(value): return [round(value.pitch, 5), round(value.yaw, 5), round(value.roll, 5)]
def filtered_tags(actor):
    return sorted(value for value in (str(tag) for tag in actor.tags)
                  if value not in {"LB.PressTrain.TrainA.AudioRuntime.v026", "LB.Asset.Candidate.v026"})
def simple_counts(mesh):
    if mesh is None: return None
    agg = mesh.get_editor_property("body_setup").get_editor_property("agg_geom")
    return {"box": len(agg.get_editor_property("box_elems")),
            "sphere": len(agg.get_editor_property("sphere_elems")),
            "capsule": len(agg.get_editor_property("sphyl_elems")),
            "convex": len(agg.get_editor_property("convex_elems"))}


def inventory(map_path):
    if not levels.load_level(map_path): raise RuntimeError(f"Could not load {map_path}")
    rows = {}
    for actor in actors_api.get_all_level_actors():
        transform = actor.get_actor_transform()
        row = {"class": actor.get_class().get_path_name(), "location_cm": vec(transform.translation),
               "rotation_degrees": rot(transform.rotation.rotator()), "scale": vec(transform.scale3d),
               "hidden_editor": bool(actor.is_hidden_ed()), "tags": filtered_tags(actor)}
        root_component = actor.get_editor_property("root_component")
        if root_component and isinstance(root_component, unreal.PrimitiveComponent):
            row["root_collision_enabled"] = str(root_component.get_collision_enabled())
            row["root_collision_profile"] = str(root_component.get_collision_profile_name())
            row["root_pawn_response"] = str(root_component.get_collision_response_to_channel(
                unreal.CollisionChannel.ECC_PAWN))
            row["root_can_affect_navigation"] = bool(root_component.get_editor_property("can_ever_affect_navigation"))
        if isinstance(actor, unreal.StaticMeshActor):
            component = actor.static_mesh_component
            mesh = component.get_editor_property("static_mesh")
            row["mesh"] = mesh.get_path_name() if mesh else None
            row["simple_collision"] = simple_counts(mesh)
        if isinstance(actor, unreal.RecastNavMesh):
            row["runtime_generation"] = str(actor.get_editor_property("runtime_generation"))
            row["can_be_main_nav_data"] = bool(actor.get_editor_property("can_be_main_nav_data"))
        rows[actor.get_actor_label()] = row
    settings = unreal.EditorLevelLibrary.get_editor_world().get_world_settings()
    game_mode = settings.get_editor_property("default_game_mode")
    nav_config = settings.get_editor_property("navigation_system_config")
    return {"actors": rows, "actor_count": len(rows),
            "game_mode": game_mode.get_path_name() if game_mode else None,
            "navigation_config_class": nav_config.get_class().get_path_name() if nav_config else None}


baseline = inventory(maps["v024"])
candidate = inventory(maps["v026"])
baseline_labels = set(baseline["actors"]); candidate_labels = set(candidate["actors"])
missing = sorted(baseline_labels - candidate_labels)
added = sorted(candidate_labels - baseline_labels)
changed = []
for label in sorted(baseline_labels & candidate_labels):
    if baseline["actors"][label] != candidate["actors"][label]:
        changed.append({"actor": label, "v024": baseline["actors"][label], "v026": candidate["actors"][label]})
failures = []
if missing: failures.append(f"actors missing from v026: {missing}")
if added: failures.append(f"actors added to v026: {added}")
if changed: failures.append(f"physical actor rows changed: {[row['actor'] for row in changed]}")
if baseline["game_mode"] != candidate["game_mode"]: failures.append("game mode changed")
if baseline["navigation_config_class"] != candidate["navigation_config_class"]: failures.append("navigation config changed")
files = {name: root / f"Content/LineBoss/Maps/{path.rsplit('/', 1)[-1]}.umap" for name, path in maps.items()}
report = {
    "$schema": "cairnwell/audit/press-train-a-audio-physical-inheritance-v026/v1",
    "generated_utc": datetime.now(timezone.utc).isoformat(),
    "status": "PASS__V026_AUDIO_ONLY_CHILD_EXACTLY_INHERITS_V024_ACTORS_TRANSFORMS_COLLISION_AND_NAV_CONFIG__NOT_PROMOTED"
              if not failures else "FAIL__V026_AUDIO_PHYSICAL_INHERITANCE__NOT_PROMOTED",
    "maps": maps, "map_sha256": {name: hashlib.sha256(path.read_bytes()).hexdigest().upper()
                                   for name, path in files.items()},
    "v024_actor_count": baseline["actor_count"], "v026_actor_count": candidate["actor_count"],
    "missing_actor_count": len(missing), "added_actor_count": len(added),
    "changed_physical_actor_count": len(changed), "changed_physical_actors": changed,
    "game_mode": candidate["game_mode"], "navigation_config_class": candidate["navigation_config_class"],
    "failures": failures, "production_map_changed": False, "promotion_authorized": False,
}
out.parent.mkdir(parents=True, exist_ok=True)
out.write_text(json.dumps(report, indent=2), encoding="utf-8")
print(json.dumps({"status": report["status"], "actors": candidate["actor_count"], "changed": len(changed)}, indent=2))
if failures: raise RuntimeError("; ".join(failures))
