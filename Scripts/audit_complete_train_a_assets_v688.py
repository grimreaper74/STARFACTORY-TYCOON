"""Read-only asset, instance, Nanite, collision and material audit for Train A."""
from pathlib import Path
from datetime import datetime, timezone
from collections import defaultdict
import json
import unreal

ROOT = Path(unreal.Paths.project_dir())
MAP = "/Game/LineBoss/Developer/Validation/PressTrains/LB_PressTrainA_RuntimeNav_v673"
OUT = ROOT / r"Saved\Audits\PressTrains\complete_train_a_asset_performance_v688.json"
levels = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
actors = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
if OUT.exists():
    raise RuntimeError("Refusing to overwrite v688")
if not levels.load_level(MAP):
    raise RuntimeError("Could not load v673")
unreal.AutomationUtilsBlueprintLibrary.finish_all_asset_compilation()

assets = defaultdict(lambda: {
    "instances": 0,
    "visual_instances": 0,
    "collision_proxy_instances": 0,
    "triangles_lod0": None,
    "vertices_lod0": None,
    "nanite_enabled": None,
    "material_slots": 0,
    "missing_material_slots": 0,
    "collision_modes": set(),
    "actor_labels": [],
})
component_count = 0
visual_component_count = 0
proxy_component_count = 0
for actor in actors.get_all_level_actors():
    is_proxy = unreal.Name("LB.Collision.Proxy") in actor.tags
    components = actor.get_components_by_class(unreal.StaticMeshComponent)
    for component in components:
        mesh = component.get_editor_property("static_mesh")
        if not mesh:
            continue
        component_count += 1
        path = mesh.get_path_name()
        row = assets[path]
        row["instances"] += 1
        if is_proxy:
            row["collision_proxy_instances"] += 1
            proxy_component_count += 1
        else:
            row["visual_instances"] += 1
            visual_component_count += 1
        if len(row["actor_labels"]) < 12:
            row["actor_labels"].append(actor.get_actor_label())
        try:
            row["collision_modes"].add(str(component.get_editor_property("collision_enabled")))
        except Exception:
            row["collision_modes"].add("UNAVAILABLE")
        if row["triangles_lod0"] is None:
            try:
                row["triangles_lod0"] = mesh.get_num_triangles(0)
                row["vertices_lod0"] = mesh.get_num_vertices(0)
            except Exception:
                row["triangles_lod0"] = -1
                row["vertices_lod0"] = -1
            try:
                row["nanite_enabled"] = bool(mesh.get_editor_property("nanite_settings").enabled)
            except Exception:
                row["nanite_enabled"] = False
            slots = mesh.get_editor_property("static_materials")
            row["material_slots"] = len(slots)
            row["missing_material_slots"] = sum(
                1 for slot in slots if not slot.get_editor_property("material_interface"))

serial_assets = []
for path, row in sorted(assets.items()):
    row["collision_modes"] = sorted(row["collision_modes"])
    serial_assets.append({"asset": path, **row})

candidate_assets = [row for row in serial_assets if row["asset"].startswith("/Game/LineBoss/")]
visual_candidates = [row for row in candidate_assets if row["visual_instances"] > 0]
nanite_candidates = [row for row in visual_candidates if row["nanite_enabled"]]
missing_material_assets = [row for row in visual_candidates if row["missing_material_slots"] > 0]
total_unique_triangles = sum(max(0, row["triangles_lod0"] or 0) for row in visual_candidates)
total_instanced_triangles = sum(
    max(0, row["triangles_lod0"] or 0) * row["visual_instances"]
    for row in visual_candidates)

failures = []
if len(visual_candidates) > 30:
    failures.append(f"unique visual candidate mesh count {len(visual_candidates)} exceeds 30")
if visual_component_count < 75:
    failures.append(f"visual component count {visual_component_count} below expected complete-line minimum 75")
if len(nanite_candidates) < 12:
    failures.append(f"Nanite candidate count {len(nanite_candidates)} below 12")
if missing_material_assets:
    failures.append(f"{len(missing_material_assets)} visual assets have missing material slots")

status = "PASS__MODULAR_INSTANCE_NANITE_AND_MATERIAL_GATE" if not failures else "FAIL__REPAIR_REQUIRED__NOT_PROMOTED"
OUT.parent.mkdir(parents=True, exist_ok=True)
OUT.write_text(json.dumps({
    "revision": "v688",
    "generated_utc": datetime.now(timezone.utc).isoformat(),
    "status": status,
    "map": MAP,
    "summary": {
        "static_mesh_components": component_count,
        "visual_components": visual_component_count,
        "collision_proxy_components": proxy_component_count,
        "unique_meshes_all": len(serial_assets),
        "unique_visual_candidate_meshes": len(visual_candidates),
        "nanite_visual_candidate_meshes": len(nanite_candidates),
        "visual_assets_with_missing_material_slots": len(missing_material_assets),
        "unique_visual_triangles_lod0": total_unique_triangles,
        "instanced_visual_triangles_lod0": total_instanced_triangles,
    },
    "thresholds": {
        "max_unique_visual_candidate_meshes": 30,
        "min_visual_components": 75,
        "min_nanite_visual_candidate_meshes": 12,
        "missing_material_assets": 0,
    },
    "failures": failures,
    "assets": serial_assets,
    "protected_map_modified": False,
    "promotion_authorized": False,
}, indent=2), encoding="utf-8")
(unreal.log if not failures else unreal.log_error)(
    "LINE_BOSS_COMPLETE_TRAIN_A_ASSET_PERFORMANCE_V688_" + ("PASS" if not failures else "FAIL"))
