"""Finalize the pre-created PR-003 v011 map in a clean Unreal process."""

import json
from pathlib import Path
import unreal

ROOT = Path(unreal.Paths.project_dir())
MAP = "/Game/LineBoss/Maps/LB_PressShop_PR003StorageCandidate_v014"
AUDIT = ROOT / "Saved/Audits/press_shop_pr003_storage_candidate_v014.json"
ASSETS = {
    "coil": ("LB.Material.MasterCoil", "/Game/LineBoss/IndustrialKit/MaterialHandling/PR003Candidate_v011/SM_LB_MasterCoil_Candidate_v003"),
    "saddle": ("LB.Module.CoilSaddle", "/Game/LineBoss/IndustrialKit/MaterialHandling/PR003Candidate_v011/SM_LB_CoilSaddle_Candidate_v002"),
}
levels = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
actors = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
if not levels.load_level(MAP): raise RuntimeError(f"Could not load {MAP}")
meshes = {key: unreal.load_asset(path) for key, (_tag, path) in ASSETS.items()}
if not all(isinstance(mesh, unreal.StaticMesh) for mesh in meshes.values()):
    raise RuntimeError(f"Missing imported meshes {meshes}")
replaced = {"coil": [], "saddle": []}
for actor in actors.get_all_level_actors():
    if not isinstance(actor, unreal.StaticMeshActor): continue
    tags = {str(tag) for tag in actor.tags}
    kind = next((key for key, (tag, _path) in ASSETS.items() if tag in tags), None)
    if kind is None: continue
    component = actor.get_editor_property("static_mesh_component")
    before = component.get_editor_property("static_mesh")
    component.set_editor_property("static_mesh", meshes[kind])
    replaced[kind].append({
        "actor": actor.get_actor_label(), "before": before.get_path_name() if before else None,
        "after": meshes[kind].get_path_name(), "location_cm": list(actor.get_actor_location().to_tuple()),
        "rotation_deg": list(actor.get_actor_rotation().to_tuple()), "tags": sorted(tags),
    })
counts = {key: len(value) for key, value in replaced.items()}
if counts != {"coil": 15, "saddle": 16}: raise RuntimeError(f"Unexpected replacement counts {counts}")
if not levels.save_current_level(): raise RuntimeError(f"Could not save {MAP}")
imports = {}
for key, mesh in meshes.items():
    box = mesh.get_bounding_box()
    imports[key] = {
        "asset": mesh.get_path_name(),
        "bounds_cm": [box.max.x-box.min.x, box.max.y-box.min.y, box.max.z-box.min.z],
        "material_slots": [str(slot.get_editor_property("imported_material_slot_name") or slot.get_editor_property("material_slot_name")) for slot in mesh.get_editor_property("static_materials")],
        "simple_collision_primitive_count": int(mesh.get_editor_property("body_setup").get_agg_geom().get_element_count()),
    }
result = {
    "$schema": "line-boss/audit/press-shop-pr003-storage-candidate/v1",
    "status": "CANDIDATE_NOT_PROMOTED__FRESH_VISUAL_REVIEW_REQUIRED",
    "base_map": "/Game/LineBoss/Maps/LB_PressShop_PR004LightingCandidate_v006", "map": MAP,
    "station_anchors_modified": False, "actor_transforms_modified": False,
    "replacement_counts": counts, "imports": imports, "replaced": replaced,
    "known_import_warning": "Saddle FBX reported degenerate tangent bases/nearly-zero binormals; visual inspection required and release promotion blocked until corrected or proven harmless.",
    "promotion_supported": False,
}
AUDIT.parent.mkdir(parents=True, exist_ok=True)
AUDIT.write_text(json.dumps(result, indent=2), encoding="utf-8")
unreal.log(f"LINE_BOSS_PR003_STORAGE_V011_FINALIZE_PASS counts={counts}")
unreal.SystemLibrary.quit_editor()
