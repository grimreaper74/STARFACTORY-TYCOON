"""Inventory the exact inherited 30 t moving assembly before v037 rework."""

import json
from pathlib import Path
import unreal

MAP = "/Game/LineBoss/Maps/LB_PressShop_PR004SupportCraneCandidate_v036"
OUT = Path(unreal.Paths.project_saved_dir()) / "Audits/press_shop_pr004_support_crane_inventory_v036.json"
levels = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
actors = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
if not levels.load_level(MAP):
    raise RuntimeError(MAP)
rows = []
for actor in actors.get_all_level_actors():
    tags = [str(tag) for tag in actor.tags]
    if "LB.Crane.30T" not in tags:
        continue
    mesh = actor.get_component_by_class(unreal.StaticMeshComponent)
    rows.append({
        "label": actor.get_actor_label(),
        "class": actor.get_class().get_name(),
        "location_cm": list(actor.get_actor_location().to_tuple()),
        "rotation": list(actor.get_actor_rotation().to_tuple()),
        "scale": list(actor.get_actor_scale3d().to_tuple()),
        "tags": tags,
        "mesh": (mesh.get_editor_property("static_mesh").get_path_name()
                 if mesh and mesh.get_editor_property("static_mesh") else None),
    })
OUT.parent.mkdir(parents=True, exist_ok=True)
OUT.write_text(json.dumps(rows, indent=2), encoding="utf-8")
unreal.log(f"LINE_BOSS_SUPPORT_CRANE_V036_INVENTORY_PASS actors={len(rows)}")
unreal.SystemLibrary.quit_editor()
