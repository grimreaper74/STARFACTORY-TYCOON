"""Inspect v038 package and live-label transforms before the v039 trace panel."""

import json
from pathlib import Path
import unreal

MAP = "/Game/LineBoss/Maps/LB_PressShop_PR004SupportHookCandidate_v038"
OUT = Path(unreal.Paths.project_saved_dir()) / "Audits/press_shop_pr004_label_inventory_v038.json"
levels = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
actors = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
if not levels.load_level(MAP):
    raise RuntimeError(MAP)
rows = []
for actor in actors.get_all_level_actors():
    label = actor.get_actor_label()
    package = False
    for component in actor.get_components_by_class(unreal.StaticMeshComponent):
        mesh = component.get_editor_property("static_mesh")
        if mesh and "SM_LB_MasterCoil_Candidate_v004" in mesh.get_path_name():
            package = True
            break
    if not package and not label.startswith(("LB_COIL_LABEL_V026_", "LB_COIL_TEXT_V026_")):
        continue
    rows.append({
        "label": label, "package": package,
        "location_cm": list(actor.get_actor_location().to_tuple()),
        "rotation": list(actor.get_actor_rotation().to_tuple()),
        "scale": list(actor.get_actor_scale3d().to_tuple()),
        "tags": [str(tag) for tag in actor.tags],
    })
OUT.parent.mkdir(parents=True, exist_ok=True)
OUT.write_text(json.dumps(rows, indent=2), encoding="utf-8")
unreal.log(f"LINE_BOSS_PR004_LABEL_INVENTORY_V038_PASS rows={len(rows)}")
unreal.SystemLibrary.quit_editor()
