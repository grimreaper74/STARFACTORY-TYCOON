"""Read back effective component materials from corrected v027 stage."""
import json
from pathlib import Path
import unreal

MAP = "/Game/LineBoss/Developer/Validation/LB_ServiceDockModularRuntime_v027"
OUT = Path(unreal.Paths.project_saved_dir()) / "Audits/SupportRobots/service_dock_modular_effective_materials_v028.json"
levels = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
actors = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
if not levels.load_level(MAP):
    raise RuntimeError(f"failed to load {MAP}")
records = []
for actor in actors.get_all_level_actors():
    if actor.get_actor_label() not in {"LB_DOCK_V027_MR01_RUNTIME", "LB_DOCK_V027_CR01_RUNTIME"}:
        continue
    components = []
    for comp in actor.get_components_by_class(unreal.StaticMeshComponent):
        if not comp.static_mesh:
            continue
        slots = []
        for index, slot in enumerate(comp.static_mesh.get_editor_property("static_materials")):
            effective = comp.get_material(index)
            slots.append({"slot": str(slot.material_slot_name), "effective": effective.get_path_name() if effective else None})
        components.append({"name": comp.get_name(), "mesh": comp.static_mesh.get_path_name(), "slots": slots})
    records.append({"actor": actor.get_actor_label(), "components": components})
missing = [f"{record['actor']}:{component['name']}:{slot['slot']}" for record in records for component in record["components"] for slot in component["slots"] if slot["effective"] is None]
payload = {"status": "PASS" if not missing else "FAIL", "map": MAP, "records": records, "missing_effective_materials": missing, "promotion_authorized": False}
OUT.parent.mkdir(parents=True, exist_ok=True)
OUT.write_text(json.dumps(payload, indent=2), encoding="utf-8")
if missing:
    raise RuntimeError(f"missing effective materials: {missing}")
unreal.log("LINE_BOSS_SERVICE_DOCK_EFFECTIVE_MATERIALS_V028_PASS")
