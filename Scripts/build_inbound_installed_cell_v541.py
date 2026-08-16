"""Release-intent presentation successor: roof plane, restrained exposure and tighter cameras."""
from pathlib import Path
import unreal

root = Path(__file__).parent
source = (root / "build_inbound_installed_cell_v540.py").read_text(encoding="utf-8")
source = source.replace("v540", "v541").replace("V540", "V541").replace("V040_", "V041_")
exec(compile(source, str(root / "build_inbound_installed_cell_v540.py"), "exec"), globals(), globals())

library = unreal.EditorAssetLibrary
actors = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
levels = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
cube = library.load_asset("/Engine/BasicShapes/Cube.Cube")
dark = library.load_asset("/Game/LineBoss/IndustrialKit/InboundCoilDelivery/Candidate_v001/Materials_v001/MI_CA_Inbound_Charcoal_v001")
white = library.load_asset("/Game/LineBoss/IndustrialKit/InboundCoilDelivery/Candidate_v001/Materials_v001/MI_CA_Inbound_White_v001")
if cube is None or dark is None or white is None:
    raise RuntimeError("Missing v541 presentation materials")

tags = [unreal.Name("LB.Asset.ValidationOnly"), unreal.Name("LB.Asset.CandidateNotPromoted"),
        unreal.Name("LB.Engineering.Values.TBC"), unreal.Name("LB.Inbound.ProPack.20260807")]

def block(label, loc, scale, mat):
    actor = actors.spawn_actor_from_class(unreal.StaticMeshActor, unreal.Vector(*loc), unreal.Rotator())
    actor.set_actor_label(label)
    actor.set_actor_scale3d(unreal.Vector(*scale))
    actor.static_mesh_component.set_static_mesh(cube)
    actor.static_mesh_component.set_material(0, mat)
    actor.static_mesh_component.set_collision_enabled(unreal.CollisionEnabled.NO_COLLISION)
    actor.static_mesh_component.set_editor_property("can_ever_affect_navigation", False)
    actor.tags = tags
    return actor

# A shallow insulated roof and transverse steel ribs replace the remaining
# validation-stage void while staying above the retained crane envelope.
block("LB_INBOUND_V041_RoofPlane", (-500, 800, 1900), (110, 74, .18), white)
for index, y in enumerate((-2200, -1000, 200, 1400, 2600, 3800), 1):
    block(f"LB_INBOUND_V041_RoofRib_{index:02d}", (-500, y, 1870), (110, .16, .25), dark)

# Restrain the inherited fill and exposure so silver coils keep curvature and
# the crane retains shadow separation instead of clipping to white.
for actor in actors.get_all_level_actors():
    if isinstance(actor, unreal.PostProcessVolume):
        settings = actor.settings
        settings.set_editor_property("auto_exposure_bias", 0.05)
        actor.settings = settings
    elif isinstance(actor, unreal.PointLight) and "AisleFill" in actor.get_actor_label():
        actor.point_light_component.set_editor_property("intensity", 700.0)
    elif isinstance(actor, unreal.RectLight) and "HighBay" in actor.get_actor_label():
        actor.rect_light_component.set_editor_property("intensity", 260.0)

overview = next(a for a in actors.get_all_level_actors() if a.get_actor_label() == "LB_CAM_InboundHall_ProcessOverview_v541")
overview.set_actor_location(unreal.Vector(-500, 6500, 1750), False, False)
overview.set_actor_rotation(unreal.MathLibrary.find_look_at_rotation(overview.get_actor_location(), unreal.Vector(-650, -100, 360)), False)
overview.camera_component.set_editor_property("field_of_view", 48.0)
hero = next(a for a in actors.get_all_level_actors() if a.get_actor_label() == "LB_CAM_InboundHall_CraneHero_v541")
hero.set_actor_location(unreal.Vector(1450, 4050, 1450), False, False)
hero.set_actor_rotation(unreal.MathLibrary.find_look_at_rotation(hero.get_actor_location(), unreal.Vector(-350, -100, 390)), False)
hero.camera_component.set_editor_property("field_of_view", 52.0)

if not levels.save_current_level():
    raise RuntimeError("Failed saving v541 release-intent presentation")
unreal.log("LINE_BOSS_INBOUND_PRESENTATION_V541_BUILD_PASS")
