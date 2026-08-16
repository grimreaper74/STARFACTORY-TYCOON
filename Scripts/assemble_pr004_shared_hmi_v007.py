"""Place the release-candidate shared HMI outside the PR-004 safety fence."""

import json
from pathlib import Path

import unreal


PROJECT = Path(unreal.Paths.project_dir()).resolve()
MAP = "/Game/LineBoss/Developer/Validation/PR004/LB_PR004_Depackaging_Candidate_v007"
HMI_ROOT = "/Game/LineBoss/Shared/HMI/IND_HMI_001_V004_Modeling003"
PREFIX = "LB_PR004_HMI04_"
AUDIT = PROJECT / "Saved/Audits/pr004_shared_hmi_candidate_v007.json"

# South of the operator gate, outside the y=620 cm perimeter.  The HMI model's
# operator face points +Y, leaving a clear standing position further south.
LOCATION = unreal.Vector(180.0, 735.0, 0.0)
ROTATION = unreal.Rotator(0.0, 0.0, 0.0)


levels = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
actors = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
assets = unreal.get_editor_subsystem(unreal.EditorAssetSubsystem)

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
    raise RuntimeError("Failed to save PR-004 map after HMI placement")

AUDIT.parent.mkdir(parents=True, exist_ok=True)
AUDIT.write_text(json.dumps({
    "$schema": "line-boss/audit/pr004-shared-hmi-candidate-v007/v1",
    "status": "CANDIDATE_ASSEMBLY_PASS__VISUAL_COLLISION_AND_INTERACTION_GATES_REQUIRED",
    "map": MAP,
    "hmi_root": HMI_ROOT,
    "location_cm": [LOCATION.x, LOCATION.y, LOCATION.z],
    "rotation_deg": [ROTATION.roll, ROTATION.pitch, ROTATION.yaw],
    "module_count": len(spawned),
    "modules": spawned,
    "promotion_supported": False,
    "remaining_gates": [
        "fixed-camera visual comparison",
        "simple release collision",
        "operator standing and approach clearance",
        "interactive screen and physical controls",
        "PR-004 state and alarm binding",
    ],
}, indent=2), encoding="utf-8")

unreal.log(f"LINE_BOSS_PR004_SHARED_HMI_V007_PASS modules={len(spawned)} audit={AUDIT}")
unreal.SystemLibrary.quit_editor()
