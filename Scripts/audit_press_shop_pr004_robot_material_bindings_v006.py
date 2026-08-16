"""Audit integrated PR004 robot material slot bindings against imported source slots."""
import json
from pathlib import Path
import unreal
MAP="/Game/LineBoss/Maps/LB_PressShop_PR004LightingCandidate_v006"; PREFIX="LB_INT_PR004_V009_robot_v002_"
root=Path(unreal.Paths.project_dir()); source=json.loads((root/"Saved/Audits/pr004_unreal_import_candidate_v003.json").read_text(encoding="utf-8"))
records={r["asset"].rsplit("/",1)[-1].split(".",1)[0]:r for r in source["imported_assets"] if r["family"]=="robot_v002"}
levels=unreal.get_editor_subsystem(unreal.LevelEditorSubsystem); actors=unreal.get_editor_subsystem(unreal.EditorActorSubsystem);levels.load_level(MAP)
rows=[]
for actor in actors.get_all_level_actors():
    if not actor.get_actor_label().startswith(PREFIX):continue
    c=actor.get_component_by_class(unreal.StaticMeshComponent); record=records[c.static_mesh.get_name()]
    slots=[]
    for i,a in enumerate(record["opaque_material_assignments"]):
        material=c.get_material(i)
        slots.append({"index":i,"source_slot":a["slot"],"expected_key":a["material_key"],"bound_material":material.get_path_name() if material else None})
    rows.append({"actor":actor.get_actor_label(),"mesh":c.static_mesh.get_path_name(),"slots":slots})
out=root/"Saved/Audits/press_shop_pr004_robot_material_bindings_v006.json";out.write_text(json.dumps({"map":MAP,"actors":rows},indent=2),encoding="utf-8")
unreal.log(f"LINE_BOSS_PR004_BINDING_AUDIT_PASS actors={len(rows)}");unreal.SystemLibrary.quit_editor()
