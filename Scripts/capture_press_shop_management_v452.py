"""Capture roof-cutaway management views of retained v438 without saving it."""
from pathlib import Path
import unreal

ROOT = Path(unreal.Paths.project_dir())
MAP = "/Game/LineBoss/Maps/LB_PressShop_BuilderAuthorityCandidate_v438"
OUT_DIR = ROOT / "Saved/Screenshots/WindowsEditor"
OUT_DIR.mkdir(parents=True, exist_ok=True)

# The installed train zone is centred near X=3850, Y=1750. Cameras remain
# inside the hall envelope while the roof/upper liner is transiently hidden.
SHOTS = [
    ("PressShop_v452_ManagementWholeShop.png", unreal.Vector(3850.0, 1750.0, 7600.0), unreal.Rotator(0.0, -90.0, 0.0), 28.0),
    ("PressShop_v452_TrainArea.png", unreal.Vector(3850.0, 1750.0, 3900.0), unreal.Rotator(0.0, -90.0, 0.0), 30.0),
]

unreal.EditorLoadingAndSavingUtils.load_map(MAP)
actor_api = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
for actor in actor_api.get_all_level_actors():
    label = actor.get_actor_label().lower()
    tags = {str(tag).lower() for tag in actor.tags}
    is_roof = (
        "roofliner" in label
        or "roofbeam" in label
        or "ceilingpanel" in label
        or "lb.module.factoryroofliner" in tags
    )
    if is_roof:
        actor.set_actor_hidden_in_game(True)
        actor.set_is_temporarily_hidden_in_editor(True)

camera = actor_api.spawn_actor_from_class(unreal.CineCameraActor, SHOTS[0][1], SHOTS[0][2])
camera.set_actor_label("TEMP_PressShopManagementCamera_v452")
camera_component = camera.get_cine_camera_component()
state = {"index": 0, "requested": False, "settle": 120}


def tick(delta_seconds):
    if state["settle"] > 0:
        state["settle"] -= 1
        return True
    index = state["index"]
    if index >= len(SHOTS):
        unreal.SystemLibrary.quit_editor()
        return False
    filename, location, rotation, focal_length = SHOTS[index]
    output = OUT_DIR / filename
    if not state["requested"]:
        camera.set_actor_location_and_rotation(location, rotation, False, False)
        camera_component.set_current_focal_length(focal_length)
        unreal.AutomationLibrary.take_high_res_screenshot(1920, 1080, str(output), camera=camera)
        state["requested"] = True
        return True
    if output.exists() and output.stat().st_size > 10000:
        state["index"] += 1
        state["requested"] = False
        state["settle"] = 60
    return True


unreal.register_slate_post_tick_callback(tick)
