"""Release-intent signage, aisle control and process-zone successor of retained v548."""
from pathlib import Path
import unreal

root = Path(__file__).parent
source = (root / "build_inbound_installed_cell_v548.py").read_text(encoding="utf-8")
source = source.replace("v548", "v550").replace("V548", "V550").replace("V048_", "V050_")
exec(compile(source, str(root / "build_inbound_installed_cell_v548.py"), "exec"), globals(), globals())

library = unreal.EditorAssetLibrary
actors = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
levels = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
cube = library.load_asset("/Engine/BasicShapes/Cube.Cube")
mats = {
    "green": library.load_asset("/Game/LineBoss/IndustrialKit/InboundCoilDelivery/Candidate_v001/Materials_v001/MI_CA_Inbound_CairnwellGreen_v001"),
    "yellow": library.load_asset("/Game/LineBoss/IndustrialKit/InboundCoilDelivery/Candidate_v001/Materials_v001/MI_CA_Inbound_SafetyYellow_v001"),
    "charcoal": library.load_asset("/Game/LineBoss/IndustrialKit/InboundCoilDelivery/Candidate_v001/Materials_v001/MI_CA_Inbound_Charcoal_v001"),
}
if cube is None or any(v is None for v in mats.values()):
    raise RuntimeError("Missing v550 signage materials")

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

def sign(label, text, loc, width_scale, size):
    block(label + "Board", loc, (width_scale, .12, 1.05), mats["green"])
    actor = actors.spawn_actor_from_class(unreal.TextRenderActor, unreal.Vector(loc[0], loc[1] + 85, loc[2]), unreal.Rotator())
    actor.set_actor_label(label + "Text")
    actor.set_actor_rotation(unreal.Rotator(0, 0, 90), False)
    actor.text_render.set_editor_properties({
        "text": text,
        "horizontal_alignment": unreal.HorizTextAligment.EHTA_CENTER,
        "vertical_alignment": unreal.VerticalTextAligment.EVRTA_TEXT_CENTER,
        "world_size": size,
        "text_render_color": unreal.Color(238, 244, 238, 255),
    })
    actor.tags = tags

# Three readable process identities follow the owner-sheet left-to-right flow.
sign("LB_INBOUND_V050_DockIdentity", "INBOUND COIL DELIVERY", (-3350, -1900, 1210), 7.5, 48.0)
sign("LB_INBOUND_V050_CraneIdentity", "PROTECTED CRANE UNLOAD", (-450, -1900, 1210), 7.5, 45.0)

# Keep the existing PR-003 sign but reduce its text slightly and move it inside
# the fixed-camera frame instead of duplicating the identity authority.
pr_board = next(a for a in actors.get_all_level_actors() if a.get_actor_label() == "LB_INBOUND_V050_PR003IdentitySign")
pr_text = next(a for a in actors.get_all_level_actors() if a.get_actor_label() == "LB_INBOUND_V050_PR003SignText")
pr_board.set_actor_location(unreal.Vector(3150, -1900, 1210), False, False)
pr_text.set_actor_location(unreal.Vector(3150, -1815, 1210), False, False)
pr_text.text_render.set_editor_property("world_size", 48.0)

# Place a second instance of the existing dock-control assembly on the protected
# aisle side, matching the Pro sheet's external operator-control relationship.
source_control = next(a for a in actors.get_all_level_actors() if a.get_actor_label() == "LB_INBOUND_V050_DockControlAndSignals")
control_mesh = source_control.static_mesh_component.get_editor_property("static_mesh")
aisle_control = actors.spawn_actor_from_class(unreal.StaticMeshActor, unreal.Vector(-2850, 720, 0), unreal.Rotator(0, 0, -90))
aisle_control.set_actor_label("LB_INBOUND_V050_AisleDockControlAndSignals")
aisle_control.static_mesh_component.set_static_mesh(control_mesh)
aisle_control.static_mesh_component.set_collision_enabled(unreal.CollisionEnabled.QUERY_AND_PHYSICS)
aisle_control.static_mesh_component.set_editor_property("can_ever_affect_navigation", True)
aisle_control.tags = tags

# Thin protected-zone stripes improve process separation without becoming
# collision or claiming an engineering clearance.
for index, x in enumerate((-1800, 900, 1900), 1):
    block(f"LB_INBOUND_V050_ProcessBoundary_{index:02d}", (x, 100, 2.0), (.06, 22.0, .025), mats["yellow"])

overview = next(a for a in actors.get_all_level_actors() if a.get_actor_label() == "LB_CAM_InboundHall_ProcessOverview_v550")
overview.set_actor_location(unreal.Vector(-500, 7200, 2250), False, False)
overview.set_actor_rotation(unreal.MathLibrary.find_look_at_rotation(overview.get_actor_location(), unreal.Vector(-500, -100, 420)), False)
overview.camera_component.set_editor_property("field_of_view", 53.0)

if not levels.save_current_level():
    raise RuntimeError("Failed saving v550 release-intent signage review")
unreal.log("LINE_BOSS_INBOUND_SIGNAGE_CONTROLS_V550_BUILD_PASS")
