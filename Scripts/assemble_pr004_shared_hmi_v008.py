"""Place the shared Line Boss HMI at the authoritative PR-004 south operator point."""

import json
from pathlib import Path

import unreal


PROJECT = Path(unreal.Paths.project_dir()).resolve()
MAP = "/Game/LineBoss/Developer/Validation/PR004/LB_PR004_Inspection_Candidate_v008"
HMI_ROOT = "/Game/LineBoss/Shared/HMI/IND_HMI_001_V004_Modeling003"
PREFIX = "LB_PR004_HMI08_"
AUDIT = PROJECT / "Saved/Audits/pr004_shared_hmi_candidate_v008.json"

# South/outside the 22 x 12 m cell. The cabinet front faces the operator route.
LOCATION = unreal.Vector(0.0, -735.0, 0.0)
ROTATION = unreal.Rotator(0.0, 180.0, 0.0)

levels = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
actors = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
assets = unreal.get_editor_subsystem(unreal.EditorAssetSubsystem)

try:
    if not levels.load_level(MAP):
        raise RuntimeError(f"Could not load {MAP}")

    for actor in list(actors.get_all_level_actors()):
        if actor.get_actor_label().startswith(PREFIX):
            actors.destroy_actor(actor)

    spawned = []
    for asset_path in assets.list_assets(HMI_ROOT, recursive=True, include_folder=False):
        mesh = unreal.load_asset(asset_path)
        if not isinstance(mesh, unreal.StaticMesh):
            continue
        actor = actors.spawn_actor_from_class(unreal.StaticMeshActor, LOCATION, ROTATION)
        actor.set_actor_label(PREFIX + mesh.get_name())
        actor.static_mesh_component.set_static_mesh(mesh)
        actor.static_mesh_component.set_editor_property("mobility", unreal.ComponentMobility.STATIC)
        spawned.append({"actor": actor.get_actor_label(), "asset": mesh.get_path_name()})

    if not spawned:
        raise RuntimeError(f"No StaticMesh assets found below {HMI_ROOT}")
    if not levels.save_current_level():
        raise RuntimeError("Failed to save PR-004 v008 after HMI placement")

    AUDIT.parent.mkdir(parents=True, exist_ok=True)
    AUDIT.write_text(json.dumps({
        "$schema": "line-boss/audit/pr004-shared-hmi-candidate-v008/v1",
        "status": "CANDIDATE_ASSEMBLY_PASS__VISUAL_COLLISION_AND_INTERACTION_GATES_REQUIRED",
        "map": MAP,
        "hmi_root": HMI_ROOT,
        "location_cm": [LOCATION.x, LOCATION.y, LOCATION.z],
        "rotation_deg": [ROTATION.roll, ROTATION.pitch, ROTATION.yaw],
        "module_count": len(spawned),
        "modules": spawned,
        "promotion_supported": False,
    }, indent=2), encoding="utf-8")
    unreal.log(f"LINE_BOSS_PR004_SHARED_HMI_V008_PASS modules={len(spawned)} audit={AUDIT}")
finally:
    unreal.SystemLibrary.quit_editor()
