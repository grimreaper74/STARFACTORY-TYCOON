"""Read-only fresh-process probe of RP01 Blueprint subobject handles."""

from pathlib import Path
import json

import unreal


BP_PATH = "/Game/LineBoss/Robots/Shared/RP01/Candidate_v001/Blueprints/BP_LB_RP01_MobileBase"
OUT = Path(unreal.Paths.project_saved_dir()) / "Audits/lb_rp01_subobjects_v001_probe.json"
blueprint = unreal.load_asset(BP_PATH)
if not isinstance(blueprint, unreal.Blueprint):
    raise RuntimeError(f"Missing Blueprint {BP_PATH}")
subsystem = unreal.get_engine_subsystem(unreal.SubobjectDataSubsystem)
data_lib = unreal.SubobjectDataBlueprintFunctionLibrary
rows = []
for handle in subsystem.k2_gather_subobject_data_for_blueprint(blueprint):
    data = subsystem.k2_find_subobject_data_from_handle(handle)
    obj = data_lib.get_object_for_blueprint(data, blueprint) or data_lib.get_object(data)
    parent_handle = data_lib.get_parent_handle(data)
    parent_name = None
    if data_lib.is_handle_valid(parent_handle):
        parent_data = subsystem.k2_find_subobject_data_from_handle(parent_handle)
        parent_name = str(data_lib.get_variable_name(parent_data))
    rows.append({
        "variable_name": str(data_lib.get_variable_name(data)),
        "display_name": str(data_lib.get_display_name(data)),
        "object_name": obj.get_name() if obj else None,
        "object_path": obj.get_path_name() if obj else None,
        "object_outer": obj.get_outer().get_path_name() if obj and obj.get_outer() else None,
        "object_class": obj.get_class().get_name() if obj else None,
        "parent_variable_name": parent_name,
        "is_component": bool(data_lib.is_component(data)),
        "is_scene_component": bool(data_lib.is_scene_component(data)),
        "is_default_scene_root": bool(data_lib.is_default_scene_root(data)),
        "is_inherited_component": bool(data_lib.is_inherited_component(data)),
        "can_edit": bool(data_lib.can_edit(data)),
        "can_reparent": bool(data_lib.can_reparent(data)),
    })
OUT.parent.mkdir(parents=True, exist_ok=True)
OUT.write_text(json.dumps({"blueprint": BP_PATH, "subobject_count": len(rows), "subobjects": rows}, indent=2) + "\n", encoding="utf-8")
unreal.log(f"LINE_BOSS_RP01_SUBOBJECT_PROBE_PASS count={len(rows)} audit={OUT}")
unreal.SystemLibrary.quit_editor()
