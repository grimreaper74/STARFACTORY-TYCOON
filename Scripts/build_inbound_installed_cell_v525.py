"""Fresh v525 release-intent presentation successor of isolated v524.

Adds protected-cell language and readable process identity without modifying
builder authority v438.  Engineering dimensions remain visual/TBC.
"""
from pathlib import Path
import unreal

root = Path(__file__).parent
source = (root / "build_inbound_installed_cell_v524.py").read_text(encoding="utf-8")
source = source.replace("v524", "v525").replace("V524", "V525").replace("V024_", "V025_")
exec(compile(source, str(root / "build_inbound_installed_cell_v524.py"), "exec"), globals(), globals())

library = unreal.EditorAssetLibrary
actors = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
levels = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
cube = library.load_asset("/Engine/BasicShapes/Cube.Cube")
yellow = library.load_asset("/Game/LineBoss/IndustrialKit/InboundCoilDelivery/Candidate_v001/Materials_v001/MI_CA_Inbound_SafetyYellow_v001")
dark = library.load_asset("/Game/LineBoss/IndustrialKit/InboundCoilDelivery/Candidate_v001/Materials_v001/MI_CA_Inbound_Charcoal_v001")
green = library.load_asset("/Game/LineBoss/IndustrialKit/InboundCoilDelivery/Candidate_v001/Materials_v001/MI_CA_Inbound_CairnwellGreen_v001")
if not all((cube, yellow, dark, green)):
    raise RuntimeError("Missing retained v525 safety presentation materials")

tags = [unreal.Name("LB.Asset.ValidationOnly"), unreal.Name("LB.Asset.CandidateNotPromoted"),
        unreal.Name("LB.Engineering.Values.TBC"), unreal.Name("LB.Inbound.ProPack.20260807")]

def box(label, loc, scale, mat, collision=False):
    a = actors.spawn_actor_from_class(unreal.StaticMeshActor, unreal.Vector(*loc), unreal.Rotator())
    a.set_actor_label(label)
    a.set_actor_scale3d(unreal.Vector(*scale))
    a.static_mesh_component.set_static_mesh(cube)
    a.static_mesh_component.set_material(0, mat)
    a.static_mesh_component.set_collision_enabled(unreal.CollisionEnabled.QUERY_AND_PHYSICS if collision else unreal.CollisionEnabled.NO_COLLISION)
    a.static_mesh_component.set_editor_property("can_ever_affect_navigation", collision)
    a.tags = tags
    return a

# Protected crane cell: low, open rail construction so the process remains
# visible from the fixed review cameras.  The receiving/AGV end has a gate gap.
for y in (-1410, 1410):
    for x in (-900, -450, 0, 450, 900):
        box(f"LB_INBOUND_V025_GuardPost_{x}_{y}", (x, y, 120), (.05, .05, 2.4), yellow, True)
    for z in (55, 125, 205):
        box(f"LB_INBOUND_V025_GuardRail_{y}_{z}", (0, y, z), (9.0, .035, .035), yellow)
for x in (-900, 900):
    for y in (-1050, -650, -250, 250, 650, 1050):
        box(f"LB_INBOUND_V025_GuardEndPost_{x}_{y}", (x, y, 120), (.05, .05, 2.4), yellow, True)
    for z in (55, 125, 205):
        box(f"LB_INBOUND_V025_GuardEndRail_{x}_{z}", (x, 0, z), (.035, 10.8, .035), yellow)

# Dock-side bollards, control islands and visual gate pivots.
for x, y in ((-2360,-720),(-2360,720),(-1180,-720),(-1180,720),(1040,-720),(1040,720)):
    box(f"LB_INBOUND_V025_Bollard_{x}_{y}", (x, y, 55), (.07, .07, 1.1), yellow, True)
for x, y in ((-1080,-1410),(1080,-1410)):
    box(f"LB_INBOUND_V025_GatePier_{x}", (x, y, 135), (.11, .11, 2.7), dark, True)
    box(f"LB_INBOUND_V025_GateLamp_{x}", (x, y, 285), (.16, .16, .13), green)

# Large identity boards provide readable process zoning at overview distance.
for label, loc, scale in (
    ("LB_INBOUND_V025_Sign_InboundDelivery", (-1880, 1540, 610), (3.4,.06,.55)),
    ("LB_INBOUND_V025_Sign_CraneUnload", (0, 1540, 610), (3.1,.06,.55)),
    ("LB_INBOUND_V025_Sign_AGVHandoff", (1420, 1540, 610), (2.8,.06,.55)),
):
    box(label, loc, scale, green)

# Replace inherited framing with complete-chain review framing.
overview = next(a for a in actors.get_all_level_actors() if a.get_actor_label() == "LB_CAM_InboundHall_ProcessOverview_v525")
overview.set_actor_location(unreal.Vector(4700, -5550, 2400), False, False)
overview.set_actor_rotation(unreal.MathLibrary.find_look_at_rotation(overview.get_actor_location(), unreal.Vector(-250, 0, 250)), False)
overview.camera_component.set_editor_property("field_of_view", 64.0)

hero = next(a for a in actors.get_all_level_actors() if a.get_actor_label() == "LB_CAM_InboundHall_CraneHero_v525")
hero.set_actor_location(unreal.Vector(-850, -3500, 1550), False, False)
hero.set_actor_rotation(unreal.MathLibrary.find_look_at_rotation(hero.get_actor_location(), unreal.Vector(-100, 0, 340)), False)
hero.camera_component.set_editor_property("field_of_view", 58.0)

unreal.AutomationUtilsBlueprintLibrary.finish_all_asset_compilation()
if not levels.save_current_level():
    raise RuntimeError("Failed saving v525 release-intent inbound presentation")
unreal.log("LINE_BOSS_INBOUND_RELEASE_PRESENTATION_V525_BUILD_PASS")
