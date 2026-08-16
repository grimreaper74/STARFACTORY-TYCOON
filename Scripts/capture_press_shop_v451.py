"""Capture verified v438 press-shop views without saving or modifying the source map."""
from pathlib import Path
import unreal

ROOT = Path(unreal.Paths.project_dir())
MAP = "/Game/LineBoss/Maps/LB_PressShop_BuilderAuthorityCandidate_v438"
OUT_DIR = ROOT / "Saved/Screenshots/WindowsEditor"
OUT_DIR.mkdir(parents=True, exist_ok=True)

SHOTS = [
    ("PressShop_v451_WholeShop.png", unreal.Vector(10000.0, -9000.0, 1600.0), unreal.Rotator(0.0, -8.0, 128.0)),
    ("PressShop_v451_TrainDetail.png", unreal.Vector(8500.0, -6500.0, 1000.0), unreal.Rotator(0.0, -6.0, 132.0)),
]

unreal.EditorLoadingAndSavingUtils.load_map(MAP)
actor_api = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
camera = actor_api.spawn_actor_from_class(unreal.CineCameraActor, SHOTS[0][1], SHOTS[0][2])
camera.set_actor_label("TEMP_PressShopCaptureCamera_v451")
state = {"index": 0, "requested": False, "settle": 90}


def tick(delta_seconds):
    if state["settle"] > 0:
        state["settle"] -= 1
        return True
    index = state["index"]
    if index >= len(SHOTS):
        unreal.SystemLibrary.quit_editor()
        return False
    filename, location, rotation = SHOTS[index]
    output = OUT_DIR / filename
    if not state["requested"]:
        camera.set_actor_location_and_rotation(location, rotation, False, False)
        unreal.AutomationLibrary.take_high_res_screenshot(1920, 1080, str(output), camera=camera)
        state["requested"] = True
        return True
    if output.exists() and output.stat().st_size > 10000:
        state["index"] += 1
        state["requested"] = False
        state["settle"] = 45
    return True


unreal.register_slate_post_tick_callback(tick)
