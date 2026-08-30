import math
import unreal

# Adds two candidate-only Steam viewpoints around the existing hero camera:
# one proves the lorry-to-coil handoff, the other proves inspection/dunnage.
EXPECTED_MAP_SUFFIX = "LB_PressShop_SteamOpenBay_v004"
TAG = unreal.Name("LB.PressShop.SteamOpenBay.v004")
CAMERA_TAG = unreal.Name("LB.PressShop.Camera")


def aim(source, target):
    dx, dy, dz = target.x - source.x, target.y - source.y, target.z - source.z
    return unreal.Rotator(
        pitch=math.degrees(math.atan2(dz, math.sqrt(dx * dx + dy * dy))),
        yaw=math.degrees(math.atan2(dy, dx)),
        roll=0.0,
    )


world = unreal.EditorLevelLibrary.get_editor_world()
if world is None or not world.get_path_name().endswith(EXPECTED_MAP_SUFFIX):
    raise RuntimeError("Refusing candidate camera pass outside " + EXPECTED_MAP_SUFFIX)

specifications = (
    (
        "Steam wishlist inbound coil handoff",
        unreal.Vector(-900.0, -5800.0, 1500.0),
        unreal.Vector(-250.0, 0.0, 360.0),
        50.0,
    ),
    (
        "Steam wishlist inspection and dunnage",
        unreal.Vector(15100.0, -4400.0, 1350.0),
        unreal.Vector(15500.0, 0.0, 400.0),
        48.0,
    ),
)
actors = list(unreal.EditorLevelLibrary.get_all_level_actors())
labels = {actor.get_actor_label() for actor in actors}
duplicate_labels = [label for label, *_ in specifications if label in labels]
if duplicate_labels:
    raise RuntimeError("Candidate story camera already exists: " + ", ".join(duplicate_labels))

for label, location, target, field_of_view in specifications:
    camera = unreal.EditorLevelLibrary.spawn_actor_from_class(unreal.CameraActor, location)
    if camera is None:
        raise RuntimeError("Could not create camera: " + label)
    camera.set_actor_label(label)
    camera.tags = [TAG, CAMERA_TAG]
    camera.set_actor_rotation(aim(location, target), False)
    camera.camera_component.set_editor_property("field_of_view", field_of_view)

if not unreal.EditorLevelLibrary.save_current_level():
    raise RuntimeError("Could not save candidate story cameras")
unreal.log("PRESS_SHOP_V004_STORY_CAMERAS_PASS labels={}".format([spec[0] for spec in specifications]))
