"""Re-spawn movable coil actors at sprite control points so OFPA positions persist."""
import hashlib
import json
from pathlib import Path
import unreal

PROJECT = Path(r"C:\Users\greg_\Projects\LineBossCarFactory_Unreal 5.8")
MAP = "/Game/LineBoss/Candidates/PressShop/PressShop2126_FullHall_v001/Maps/LB_PressShop_2126_FullHall_v001"
RECEIPT = PROJECT / "Saved" / "Audits" / "PressShop2126" / "replace_aligned_coils_v002_receipt.json"
PROTECTED = {
    PROJECT / "Content" / "LineBoss" / "Maps" / "LB_PressShop_BuilderAuthorityCandidate_v438.umap": "5029c9d827d9a1d72c12f27ee757c9bc1e47febd5006ce6d7ba319aad2e7fec8",
    PROJECT / "Content" / "LineBoss" / "Candidates" / "PressShop" / "PressShop2126_v002" / "Maps" / "LB_PressShop_2126_Steam_v002.umap": "cc09cf46d33e8a562d97f5a3bc35a5b42c9582d8e4650cf315694ebf340e4aa0",
}


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest().lower()


before = {str(path): digest(path) for path in PROTECTED}
for path, expected in PROTECTED.items():
    if before[str(path)] != expected:
        raise RuntimeError(f"protected map missing or changed: {path}")
if not unreal.EditorLoadingAndSavingUtils.load_map(MAP):
    raise RuntimeError("could not load isolated 2126 candidate")

actors = {actor.get_actor_label(): actor for actor in unreal.EditorLevelLibrary.get_all_level_actors()}
specs = [
    ("2126 COIL | verification cell active load", (-7456.09, -4163.15, 175.0)),
    ("2126 COIL | magnetic buffer load A", (-6549.37, -1249.65, 175.0)),
    ("2126 COIL | magnetic buffer load C", (-6253.09, -555.62, 175.0)),
    ("2126 FRONT END | active feed coil", (-3776.89, -2763.78, 175.0)),
]
records = []
for label, location_tuple in specs:
    old = actors.get(label)
    if not isinstance(old, unreal.StaticMeshActor) or old.static_mesh_component.static_mesh is None:
        raise RuntimeError(f"movable coil unavailable: {label}")
    mesh = old.static_mesh_component.static_mesh
    rotation = old.get_actor_rotation()
    scale = old.get_actor_scale3d()
    previous = old.get_actor_location()
    if not unreal.EditorLevelLibrary.destroy_actor(old):
        raise RuntimeError(f"failed to remove old coil actor: {label}")
    location = unreal.Vector(*location_tuple)
    replacement = unreal.EditorLevelLibrary.spawn_actor_from_class(unreal.StaticMeshActor, location, rotation)
    replacement.set_actor_label(label)
    replacement.static_mesh_component.set_static_mesh(mesh)
    replacement.set_actor_scale3d(scale)
    replacement.static_mesh_component.set_collision_enabled(unreal.CollisionEnabled.QUERY_ONLY)
    records.append({
        "label": label,
        "before_location_cm": [round(previous.x, 2), round(previous.y, 2), round(previous.z, 2)],
        "after_location_cm": list(location_tuple),
        "mesh": mesh.get_path_name(),
    })

if not unreal.EditorLoadingAndSavingUtils.save_current_level():
    raise RuntimeError("failed to save replacement coil actors")
unreal.EditorLoadingAndSavingUtils.save_dirty_packages(True, True)

current = {a.get_actor_label(): a for a in unreal.EditorLevelLibrary.get_all_level_actors()}
for label, location_tuple in specs:
    actor = current.get(label)
    if not isinstance(actor, unreal.StaticMeshActor):
        raise RuntimeError(f"replacement coil missing: {label}")
    loc = actor.get_actor_location()
    if max(abs(loc.x - location_tuple[0]), abs(loc.y - location_tuple[1]), abs(loc.z - location_tuple[2])) > 0.1:
        raise RuntimeError(f"replacement coil position mismatch: {label}")
after = {str(path): digest(path) for path in PROTECTED}
if after != before:
    raise RuntimeError("a protected map changed")

RECEIPT.parent.mkdir(parents=True, exist_ok=True)
RECEIPT.write_text(json.dumps({
    "status": "PASS__ALIGNED_COILS_RESPAWNED_FOR_OFPA_PERSISTENCE",
    "candidate_map": MAP,
    "replacement_count": len(records),
    "replacements": records,
    "protected_sha256_before": before,
    "protected_sha256_after": after,
}, indent=2, sort_keys=True) + "\n", encoding="utf-8")
unreal.log(f"PRESSSHOP_2126_ALIGNED_COIL_REPLACE_PASS count={len(records)} receipt={RECEIPT}")
unreal.SystemLibrary.quit_editor()
