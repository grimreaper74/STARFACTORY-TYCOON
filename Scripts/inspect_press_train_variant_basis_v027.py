"""Inventory variant-relevant actors in retained Train A v027 without changing it."""

import json
from pathlib import Path
import unreal

root = Path(unreal.Paths.project_dir())
levels = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
actors_api = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
map_path = "/Game/LineBoss/Maps/LB_PressTrainAAudioRuntimeCandidate_v027"
out = root / "Saved/Audits/PressTrains/press_train_variant_basis_inventory_v027.json"
if not levels.load_level(map_path):
    raise RuntimeError(map_path)

tokens = ("identity", "stage", "die", "tool", "gripper", "scrap", "inspection", "hmi", "accent", "robot", "cam")
rows = []
for actor in actors_api.get_all_level_actors():
    tags = sorted(str(tag) for tag in actor.tags)
    label = actor.get_actor_label()
    haystack = (label + " " + " ".join(tags)).lower()
    if not any(token in haystack for token in tokens):
        continue
    row = {"actor": label, "class": actor.get_class().get_path_name(), "tags": tags}
    if isinstance(actor, unreal.StaticMeshActor):
        component = actor.static_mesh_component
        row["materials"] = [component.get_material(index).get_path_name() if component.get_material(index) else None
                            for index in range(component.get_num_materials())]
    if isinstance(actor, unreal.TextRenderActor):
        row["text"] = str(actor.text_render.get_editor_property("text"))
    rows.append(row)

out.parent.mkdir(parents=True, exist_ok=True)
out.write_text(json.dumps({"map": map_path, "rows": rows}, indent=2), encoding="utf-8")
print(json.dumps({"rows": len(rows), "output": str(out)}, indent=2))
