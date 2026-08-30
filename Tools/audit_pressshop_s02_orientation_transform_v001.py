"""Read-only transform audit for the S02 proxy and its camera-locked sprite."""
import json
from pathlib import Path
import unreal

MAP = "/Game/LineBoss/Candidates/PressShop/PressShopFactorio2p5D_Full_v004_CameraLockedSprites/Maps/LB_PressShop_Factorio2p5D_Full_v004_CameraLockedSprites"
CAMERA_LABEL = "CAM | 2.5D full Press Shop overview"
SPRITE_LABEL = "2.5D sprite art | S02 draw-form portal press"
PROXY_FRAGMENT = "draw / form portal press"
if not unreal.EditorLoadingAndSavingUtils.load_map(MAP):
    raise RuntimeError("could not load map")
actors = unreal.EditorLevelLibrary.get_all_level_actors()
camera = next(a for a in actors if a.get_actor_label() == CAMERA_LABEL)
sprite = next(a for a in actors if a.get_actor_label() == SPRITE_LABEL)
proxy = next(a for a in actors if PROXY_FRAGMENT in a.get_actor_label() and a.get_actor_label() != SPRITE_LABEL)
def transform(actor):
    rot = actor.get_actor_rotation()
    return {
        "label": actor.get_actor_label(),
        "location": [round(v, 3) for v in (actor.get_actor_location().x, actor.get_actor_location().y, actor.get_actor_location().z)],
        "rotation": [round(v, 3) for v in (rot.pitch, rot.yaw, rot.roll)],
        "forward": [round(v, 6) for v in (unreal.MathLibrary.get_forward_vector(rot).x, unreal.MathLibrary.get_forward_vector(rot).y, unreal.MathLibrary.get_forward_vector(rot).z)],
        "right": [round(v, 6) for v in (unreal.MathLibrary.get_right_vector(rot).x, unreal.MathLibrary.get_right_vector(rot).y, unreal.MathLibrary.get_right_vector(rot).z)],
    }
record = {"camera": transform(camera), "sprite": transform(sprite), "proxy": transform(proxy)}
path = Path(unreal.Paths.project_saved_dir()) / "Audits" / "PressShopIntegration" / "pressshop_s02_orientation_transform_audit_v001.json"
path.write_text(json.dumps(record, indent=2) + "\n", encoding="utf-8")
unreal.log("PRESSSHOP_S02_ORIENTATION_TRANSFORM_AUDIT=" + json.dumps(record, sort_keys=True))
unreal.EditorPythonScripting.set_keep_python_script_alive(False)
unreal.SystemLibrary.quit_editor()

