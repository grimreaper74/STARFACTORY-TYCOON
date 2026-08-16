"""One-shot UE 5.8 HitResult API probe for the v087 physical validator."""
import json,time
from pathlib import Path
import unreal
unreal.EditorPythonScripting.set_keep_python_script_alive(True)
out=Path(unreal.Paths.project_saved_dir())/"Audits/PR009_InMap_v087/hit_result_api_probe.json"
unreal.get_editor_subsystem(unreal.LevelEditorSubsystem).load_level("/Game/LineBoss/Maps/LB_PressShop_PR009ReleaseCollisionCandidate_v087")
unreal.EditorLevelLibrary.editor_play_simulate(); started=time.monotonic(); handle=None
def tick(_):
    global handle
    if time.monotonic()-started<3:return
    world=unreal.EditorLevelLibrary.get_game_world()
    result=unreal.SystemLibrary.line_trace_single(world,unreal.Vector(600,-2320,110),unreal.Vector(600,-2190,110),unreal.TraceTypeQuery.TRACE_TYPE_QUERY1,False,[],unreal.DrawDebugTrace.NONE,True)
    row={"type":str(type(result)),"dir":dir(result),"str":str(result),"repr":repr(result)}
    for name in ("to_tuple","export_text","is_valid_blocking_hit","get_actor"):
        try: row[name]=str(getattr(result,name)())
        except Exception as exc: row[name+"_error"]=str(exc)
    out.parent.mkdir(parents=True,exist_ok=True);out.write_text(json.dumps(row,indent=2),encoding="utf-8")
    unreal.unregister_slate_post_tick_callback(handle);handle=None;unreal.EditorLevelLibrary.editor_end_play();unreal.EditorPythonScripting.set_keep_python_script_alive(False);unreal.SystemLibrary.quit_editor()
handle=unreal.register_slate_post_tick_callback(tick)
