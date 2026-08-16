"""Read-only transform/bounds inventory for v135 crane hook replacement."""

from pathlib import Path
import json
import unreal

MAP="/Game/LineBoss/Maps/LB_PressShop_PR003PR004CoilAGVRuntimeCandidate_v135"
OUT=Path(unreal.Paths.project_saved_dir())/"Audits/press_shop_pr004_crane_hook_fit_inputs_v135.json"
levels=unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
actors_api=unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
if not levels.load_level(MAP): raise RuntimeError(MAP)
rows=[]
for actor in actors_api.get_all_level_actors():
    tagset={str(tag) for tag in actor.tags}
    if not ({"LB.Motion.CHook","LB.Motion.Hoist","LB.Motion.Reeving"} & tagset or "40T" in actor.get_actor_label() and any(token in actor.get_actor_label() for token in ("Hook","Hoist","Reeving"))):
        continue
    loc=actor.get_actor_location(); rot=actor.get_actor_rotation(); origin,extent=actor.get_actor_bounds(False,False)
    rows.append({"label":actor.get_actor_label(),"class":actor.get_class().get_name(),"location_cm":[loc.x,loc.y,loc.z],"rotation_deg":[rot.roll,rot.pitch,rot.yaw],
                 "bounds_min_cm":[origin.x-extent.x,origin.y-extent.y,origin.z-extent.z],"bounds_max_cm":[origin.x+extent.x,origin.y+extent.y,origin.z+extent.z],"tags":sorted(tagset),
                 "mesh":actor.static_mesh_component.static_mesh.get_path_name() if isinstance(actor,unreal.StaticMeshActor) and actor.static_mesh_component.static_mesh else None})
OUT.write_text(json.dumps({"map":MAP,"status":"READ_ONLY","actors":rows,"promotion_authorized":False},indent=2),encoding="utf-8")
print(json.dumps(rows,indent=2))
