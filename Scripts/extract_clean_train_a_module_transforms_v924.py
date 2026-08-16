"""Read-only transform extraction from the approved modular v015 reference map."""
import json
from pathlib import Path
import unreal

MAP = "/Game/LineBoss/Maps/LB_PressShop_CleanApprovedTrainsPaint_v20260809_v015"
OUT = Path(unreal.Paths.project_saved_dir()) / "Audits/PressTrains/clean_train_a_module_transforms_v924.json"
levels = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
actors = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
if not levels.load_level(MAP): raise RuntimeError(MAP)
records=[]
selected=[]
for actor in actors.get_all_level_actors():
    if not isinstance(actor, unreal.StaticMeshActor): continue
    label=actor.get_actor_label()
    if not any(token in label for token in ("_S01_Destack", "_S07_UnloadRobot", "_Roller_", "_Press")): continue
    if "TrainA" not in label and "Train_A" not in label and not label.startswith("LB_CLEAN_TrainA"):
        continue
    selected.append(actor)
root_actor=next((a for a in selected if "_S01_Destack" in a.get_actor_label()),None)
if not root_actor: raise RuntimeError("Train A S01 root missing")
root_transform=root_actor.get_actor_transform()
for actor in selected:
    label=actor.get_actor_label(); tr=actor.get_actor_transform().make_relative(root_transform)
    loc=tr.translation; rot=tr.rotation.rotator(); scale=tr.scale3d
    mesh=actor.static_mesh_component.static_mesh
    records.append({"label":label,"mesh":mesh.get_path_name() if mesh else None,
        "location_cm":[loc.x,loc.y,loc.z],"rotation_deg":[rot.pitch,rot.yaw,rot.roll],
        "scale":[scale.x,scale.y,scale.z]})
records.sort(key=lambda x:x["label"])
OUT.parent.mkdir(parents=True,exist_ok=True)
OUT.write_text(json.dumps({"source_map":MAP,"read_only":True,"relative_root":root_actor.get_actor_label(),"count":len(records),"actors":records},indent=2),encoding="utf-8")
unreal.log(f"LINE_BOSS_TRAIN_A_TRANSFORMS_V924_PASS count={len(records)} out={OUT}")
unreal.SystemLibrary.quit_editor()
