"""Read-only effective material comparison for v273 native docks and retained sources."""
import json
from datetime import datetime, timezone
from pathlib import Path
import unreal

MAP = "/Game/LineBoss/Maps/LB_PressShop_PlayableManagementCandidate_v273"
OUT = Path(unreal.Paths.project_saved_dir()).resolve() / "Audits/SupportRobots/press_shop_native_service_dock_materials_v274.json"
levels = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
actors = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
if not levels.load_level(MAP):
    raise RuntimeError(MAP)
records = []
for actor in actors.get_all_level_actors():
    if actor.get_actor_label() not in {"LB-DOCK-MR01-01", "LB-DOCK-MR01-02", "LB-DOCK-CR01-01", "LB-DOCK-CR01-02"}:
        continue
    components = []
    for comp in actor.get_components_by_class(unreal.StaticMeshComponent):
        mesh = comp.static_mesh
        if not mesh:
            continue
        slots = []
        for index, slot in enumerate(mesh.get_editor_property("static_materials")):
            effective = comp.get_material(index)
            slots.append({"index": index, "slot": str(slot.material_slot_name), "effective": effective.get_path_name() if effective else None})
        components.append({"name": comp.get_name(), "mesh": mesh.get_path_name(), "slots": slots})
    records.append({"actor": actor.get_actor_label(), "class": actor.get_class().get_path_name(), "components": components})

payload = {
    "$schema": "cairnwell/audit/press-shop-native-service-dock-materials-v274/v1",
    "generated_utc": datetime.now(timezone.utc).isoformat(),
    "status": "READ_ONLY__VISUAL_FAILURE_DIAGNOSTIC__NOT_PROMOTED",
    "map": MAP,
    "records": sorted(records, key=lambda row: row["actor"]),
    "promotion_authorized": False
}
OUT.parent.mkdir(parents=True, exist_ok=True)
OUT.write_text(json.dumps(payload, indent=2), encoding="utf-8")
unreal.log("LINE_BOSS_NATIVE_DOCK_MATERIALS_V274_PASS")
