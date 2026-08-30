"""Read-only material/slot audit of the separate 2126 master-coil actors."""
import json
from pathlib import Path
import unreal

PROJECT = Path(r"C:\Users\greg_\Projects\LineBossCarFactory_Unreal 5.8")
MAP = "/Game/LineBoss/Candidates/PressShop/PressShop2126_FullHall_v001/Maps/LB_PressShop_2126_FullHall_v001"
REPORT = PROJECT / "Saved" / "Audits" / "PressShop2126" / "coil_material_audit_v001.json"
LABELS = (
    "2126 LOG | delivery coil 02 | approved packaged master coil",
    "2126 LOG | delivery coil 03 | approved packaged master coil",
    "2126 LOG | delivery coil 04 | approved packaged master coil",
    "2126 LOG | coil 01 mid-transfer under autonomous gantry",
    "2126 COIL | verification cell active load",
    "2126 COIL | magnetic buffer load A",
    "2126 COIL | magnetic buffer load C",
    "2126 FRONT END | active feed coil",
)

if not unreal.EditorLoadingAndSavingUtils.load_map(MAP):
    raise RuntimeError("could not load candidate")
actors = {actor.get_actor_label(): actor for actor in unreal.EditorLevelLibrary.get_all_level_actors()}
rows = []
for label in LABELS:
    actor = actors.get(label)
    if not isinstance(actor, unreal.StaticMeshActor):
        raise RuntimeError("expected separate coil actor missing: " + label)
    component = actor.static_mesh_component
    mesh = component.static_mesh
    rows.append({
        "label": label,
        "mesh": mesh.get_path_name() if mesh else None,
        "material_slot_count": component.get_num_materials(),
        "materials": [component.get_material(index).get_path_name() if component.get_material(index) else None for index in range(component.get_num_materials())],
        "location_cm": [round(value, 2) for value in (actor.get_actor_location().x, actor.get_actor_location().y, actor.get_actor_location().z)],
        "scale": [round(value, 3) for value in (actor.get_actor_scale3d().x, actor.get_actor_scale3d().y, actor.get_actor_scale3d().z)],
    })
REPORT.parent.mkdir(parents=True, exist_ok=True)
REPORT.write_text(json.dumps({"status": "PASS_READ_ONLY", "coil_count": len(rows), "coils": rows}, indent=2, sort_keys=True) + "\n", encoding="utf-8")
unreal.log("PRESSSHOP_2126_COIL_MATERIAL_AUDIT_PASS coils=%d" % len(rows))
unreal.SystemLibrary.quit_editor()
