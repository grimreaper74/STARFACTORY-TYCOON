"""Extend v538 hall context behind the docked lorry without changing process geometry."""
from pathlib import Path
import unreal

root = Path(__file__).parent
source = (root / "build_inbound_installed_cell_v538.py").read_text(encoding="utf-8")
source = source.replace("v538", "v539").replace("V538", "V539").replace("V038_", "V039_")
exec(compile(source, str(root / "build_inbound_installed_cell_v538.py"), "exec"), globals(), globals())

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
    raise RuntimeError("Missing v539 upstream hall-context source")

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

# Continue the v538 rear wall from its x=-1600 edge to x=-4900.  This sits
# behind the dock architecture and lorry, so the open door and approach remain
# physically clear while the validation-stage void is removed.
block("LB_INBOUND_V039_UpstreamWallUpper", (-3250, -2050, 720), (16.5, .18, 8.6), mats["white"], True)
block("LB_INBOUND_V039_UpstreamWallLower", (-3250, -2025, 190), (16.5, .20, 2.0), mats["dark"], True)
block("LB_INBOUND_V039_UpstreamWindowBand", (-3250, -2000, 850), (16.5, .08, 1.65), mats["glass"], False)
for index, x in enumerate((-4800, -4200, -3600, -3000, -2400, -1800), 1):
    block(f"LB_INBOUND_V039_UpstreamMullion_{index:02d}", (x, -1945, 850), (.08, .10, 1.8), mats["dark"], False)

if not levels.save_current_level():
    raise RuntimeError("Failed saving v539 upstream hall-context correction")
unreal.log("LINE_BOSS_INBOUND_DOCK_CONTEXT_V539_BUILD_PASS")
