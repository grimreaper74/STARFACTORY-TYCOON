"""Read-only alignment/material diagnostic for rejected isolated v026 render."""
import json
from pathlib import Path
from datetime import datetime, timezone
import unreal

MAP = "/Game/LineBoss/Developer/Validation/LB_ServiceDockModularRuntime_v026"
OUT = Path(unreal.Paths.project_saved_dir()) / "Audits/SupportRobots/service_dock_modular_runtime_alignment_v026.json"
levels = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
actors = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
if not levels.load_level(MAP):
    raise RuntimeError(f"failed to load {MAP}")

actor_records = []
for actor in actors.get_all_level_actors():
    if not actor.get_actor_label().startswith("LB_DOCK_V026_"):
        continue
    components = []
    for comp in actor.get_components_by_class(unreal.StaticMeshComponent):
        mesh = comp.static_mesh
        if not mesh:
            continue
        world_location = comp.get_world_location()
        mesh_bounds = mesh.get_bounds()
        components.append({
            "component": comp.get_name(), "mesh": mesh.get_path_name(),
            "relative_location_cm": [round(v, 3) for v in (comp.relative_location.x, comp.relative_location.y, comp.relative_location.z)],
            "world_location_cm": [round(v, 3) for v in (world_location.x, world_location.y, world_location.z)],
            "mesh_local_bounds_origin_cm": [round(v, 3) for v in (mesh_bounds.origin.x, mesh_bounds.origin.y, mesh_bounds.origin.z)],
            "mesh_local_bounds_extent_cm": [round(v, 3) for v in (mesh_bounds.box_extent.x, mesh_bounds.box_extent.y, mesh_bounds.box_extent.z)],
            "material_slots": [
                {"slot": str(slot.material_slot_name), "material": comp.get_material(i).get_path_name() if comp.get_material(i) else None}
                for i, slot in enumerate(mesh.get_editor_property("static_materials"))
            ],
        })
    actor_records.append({"actor": actor.get_actor_label(), "components": components})

payload = {
    "$schema": "cairnwell/audit/service-dock-modular-runtime-alignment-v026/v1",
    "generated_utc": datetime.now(timezone.utc).isoformat(),
    "status": "REJECTED_VISUAL_DIAGNOSTIC__DO_NOT_INTEGRATE",
    "map": MAP,
    "actors": actor_records,
    "observations": [
        "Fresh fixed-camera render is materially overexposed",
        "MR01 moving components are visibly separated from the static dock body",
        "No Press Shop map or retained aggregate dock was changed",
    ],
    "promotion_authorized": False,
}
OUT.parent.mkdir(parents=True, exist_ok=True)
OUT.write_text(json.dumps(payload, indent=2), encoding="utf-8")
unreal.log("LINE_BOSS_SERVICE_DOCK_ALIGNMENT_AUDIT_V026_COMPLETE")
