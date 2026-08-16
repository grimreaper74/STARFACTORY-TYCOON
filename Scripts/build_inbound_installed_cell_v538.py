"""Correct v537 with segmented downstream hall context around the new dock."""
from pathlib import Path
import unreal

root = Path(__file__).parent
source = (root / "build_inbound_installed_cell_v537.py").read_text(encoding="utf-8")
source = source.replace("v537", "v538").replace("V537", "V538").replace("V037_", "V038_")
exec(compile(source, str(root / "build_inbound_installed_cell_v537.py"), "exec"), globals(), globals())

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
    raise RuntimeError("Missing v538 downstream context source")
tags = [unreal.Name("LB.Asset.ValidationOnly"), unreal.Name("LB.Asset.CandidateNotPromoted"),
        unreal.Name("LB.Engineering.Values.TBC"), unreal.Name("LB.Inbound.ProPack.20260807")]

def block(label, loc, scale, mat, collision=False):
    a = actors.spawn_actor_from_class(unreal.StaticMeshActor, unreal.Vector(*loc), unreal.Rotator())
    a.set_actor_label(label); a.set_actor_scale3d(unreal.Vector(*scale))
    a.static_mesh_component.set_static_mesh(cube); a.static_mesh_component.set_material(0, mat)
    a.static_mesh_component.set_collision_enabled(unreal.CollisionEnabled.QUERY_AND_PHYSICS if collision else unreal.CollisionEnabled.NO_COLLISION)
    a.static_mesh_component.set_editor_property("can_ever_affect_navigation", collision); a.tags = tags
    return a

# Segment begins downstream of the dock portal, so the reverse-in approach and
# door remain visible while the process gains a credible installed backdrop.
block("LB_INBOUND_V038_DownstreamWallUpper", (1900, -2050, 720), (35, .18, 8.6), mats["white"], True)
block("LB_INBOUND_V038_DownstreamWallLower", (1900, -2025, 190), (35, .20, 2.0), mats["dark"], True)
block("LB_INBOUND_V038_DownstreamWindowBand", (1900, -2000, 850), (31, .08, 1.65), mats["glass"], False)
for i, x in enumerate(range(-1000, 5001, 1000), 1):
    block(f"LB_INBOUND_V038_DownstreamMullion_{i:02d}", (x, -1945, 850), (.08, .10, 1.8), mats["dark"], False)

overview = next(a for a in actors.get_all_level_actors() if a.get_actor_label() == "LB_CAM_InboundHall_ProcessOverview_v538")
overview.set_actor_location(unreal.Vector(-500, 6800, 2200), False, False)
overview.set_actor_rotation(unreal.MathLibrary.find_look_at_rotation(overview.get_actor_location(), unreal.Vector(-650, -100, 320)), False)
overview.camera_component.set_editor_property("field_of_view", 51.0)

if not levels.save_current_level():
    raise RuntimeError("Failed saving v538 dock/context correction")
unreal.log("LINE_BOSS_INBOUND_DOCK_CONTEXT_V538_BUILD_PASS")
