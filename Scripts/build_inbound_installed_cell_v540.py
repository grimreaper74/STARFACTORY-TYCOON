"""Close the measured centre-wall gap left by v539's full-width cube scaling."""
from pathlib import Path
import unreal

root = Path(__file__).parent
source = (root / "build_inbound_installed_cell_v539.py").read_text(encoding="utf-8")
source = source.replace("v539", "v540").replace("V539", "V540").replace("V039_", "V040_")
exec(compile(source, str(root / "build_inbound_installed_cell_v539.py"), "exec"), globals(), globals())

library = unreal.EditorAssetLibrary
actors = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
levels = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
cube = library.load_asset("/Engine/BasicShapes/Cube.Cube")
mats = {
    "white": library.load_asset("/Game/LineBoss/IndustrialKit/InboundCoilDelivery/Candidate_v001/Materials_v001/MI_CA_Inbound_White_v001"),
    "dark": library.load_asset("/Game/LineBoss/IndustrialKit/InboundCoilDelivery/Candidate_v001/Materials_v001/MI_CA_Inbound_Charcoal_v001"),
    "glass": library.load_asset("/Game/LineBoss/IndustrialKit/InboundCoilDelivery/Candidate_v001/Materials_v001/MI_CA_Inbound_Glass_v001"),
}
if cube is None or any(v is None for v in mats.values()):
    raise RuntimeError("Missing v540 centre hall-context source")

tags = [unreal.Name("LB.Asset.ValidationOnly"), unreal.Name("LB.Asset.CandidateNotPromoted"),
        unreal.Name("LB.Engineering.Values.TBC"), unreal.Name("LB.Inbound.ProPack.20260807")]

def block(label, loc, scale, mat, collision=False):
    actor = actors.spawn_actor_from_class(unreal.StaticMeshActor, unreal.Vector(*loc), unreal.Rotator())
    actor.set_actor_label(label)
    actor.set_actor_scale3d(unreal.Vector(*scale))
    actor.static_mesh_component.set_static_mesh(cube)
    actor.static_mesh_component.set_material(0, mat)
    actor.static_mesh_component.set_collision_enabled(
        unreal.CollisionEnabled.QUERY_AND_PHYSICS if collision else unreal.CollisionEnabled.NO_COLLISION)
    actor.static_mesh_component.set_editor_property("can_ever_affect_navigation", collision)
    actor.tags = tags
    return actor

# Measured edges from the inherited 100 cm cube blocks are x=-2425 and x=150.
# A 2575 cm centre section closes only that backdrop gap.
block("LB_INBOUND_V040_CentreWallUpper", (-1137.5, -2050, 720), (25.75, .18, 8.6), mats["white"], True)
block("LB_INBOUND_V040_CentreWallLower", (-1137.5, -2025, 190), (25.75, .20, 2.0), mats["dark"], True)
block("LB_INBOUND_V040_CentreWindowBand", (-1137.5, -2000, 850), (25.75, .08, 1.65), mats["glass"], False)
for index, x in enumerate((-2200, -1800, -1400, -1000, -600, -200), 1):
    block(f"LB_INBOUND_V040_CentreMullion_{index:02d}", (x, -1945, 850), (.08, .10, 1.8), mats["dark"], False)

if not levels.save_current_level():
    raise RuntimeError("Failed saving v540 centre hall-context correction")
unreal.log("LINE_BOSS_INBOUND_DOCK_CONTEXT_V540_BUILD_PASS")
