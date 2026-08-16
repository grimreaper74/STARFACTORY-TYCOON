"""Add restrained diegetic lorry identity treatment to retained isolated v557."""
from pathlib import Path
import unreal

root = Path(__file__).parent
source = (root / "build_inbound_installed_cell_v557.py").read_text(encoding="utf-8")
source = source.replace("v557", "v558").replace("V557", "V558").replace("V057_", "V058_")
exec(compile(source, str(root / "build_inbound_installed_cell_v557.py"), "exec"), globals(), globals())

library = unreal.EditorAssetLibrary
actors = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
levels = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
cube = library.load_asset("/Engine/BasicShapes/Cube.Cube")
green = library.load_asset("/Game/LineBoss/IndustrialKit/InboundCoilDelivery/Candidate_v001/Materials_v001/MI_CA_Inbound_CairnwellGreen_v001")
if cube is None or green is None:
    raise RuntimeError("Missing v558 identity-strip inputs")
tags = [unreal.Name("LB.Asset.ValidationOnly"), unreal.Name("LB.Asset.CandidateNotPromoted"),
        unreal.Name("LB.Engineering.Values.TBC"), unreal.Name("LB.Inbound.ProPack.20260807")]

# A slim removable identity rail avoids turning the open curtain-side trailer
# back into a closed box and preserves direct visibility of all four coils.
board = actors.spawn_actor_from_class(unreal.StaticMeshActor, unreal.Vector(-2500, 150, 355), unreal.Rotator())
board.set_actor_label("LB_INBOUND_V058_LorryIdentityRail")
board.set_actor_scale3d(unreal.Vector(8.2, .025, .26))
board.static_mesh_component.set_static_mesh(cube)
board.static_mesh_component.set_material(0, green)
board.static_mesh_component.set_collision_enabled(unreal.CollisionEnabled.NO_COLLISION)
board.static_mesh_component.set_editor_property("can_ever_affect_navigation", False)
board.tags = tags

text = actors.spawn_actor_from_class(unreal.TextRenderActor, unreal.Vector(-2500, 158, 355), unreal.Rotator())
text.set_actor_label("LB_INBOUND_V058_LorryIdentityText")
text.set_actor_rotation(unreal.Rotator(0, 0, 90), False)
text.text_render.set_editor_properties({
    "text": "CAIRNWELL AUTOMOTIVE  |  INBOUND COILS",
    "horizontal_alignment": unreal.HorizTextAligment.EHTA_CENTER,
    "vertical_alignment": unreal.VerticalTextAligment.EVRTA_TEXT_CENTER,
    "world_size": 24.0,
    "text_render_color": unreal.Color(238, 244, 238, 255),
})
text.tags = tags

if not levels.save_current_level():
    raise RuntimeError("Failed saving v558 lorry identity review")
unreal.log("LINE_BOSS_INBOUND_LORRY_IDENTITY_V558_BUILD_PASS")
