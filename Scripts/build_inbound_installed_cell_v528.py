"""Fresh v528: coherent four-coil lorry on the retained compact linear cell."""
from pathlib import Path
import unreal

root = Path(__file__).parent
source = (root / "build_inbound_installed_cell_v527.py").read_text(encoding="utf-8")
source = source.replace("v527", "v528").replace("V527", "V528").replace("V027_", "V028_")
exec(compile(source, str(root / "build_inbound_installed_cell_v527.py"), "exec"), globals(), globals())

library = unreal.EditorAssetLibrary
actors = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
levels = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)

# Separate cab/trailer actors were useful modular evidence, but their FBX
# origins make the installed parked vehicle read as detached. Replace only in
# this isolated successor with the coherent presentation mesh.
for actor in list(actors.get_all_level_actors()):
    if actor.get_actor_label().endswith("LorryCab") or actor.get_actor_label().endswith("CoilTrailer"):
        actors.destroy_actor(actor)

mesh = library.load_asset(
    "/Game/LineBoss/IndustrialKit/InboundCoilDelivery/LorryAssemblyCandidate_v001/SM_CA_MW_Inbound_LorryFourCoil_v001")
if not isinstance(mesh, unreal.StaticMesh):
    raise RuntimeError("Missing imported coherent four-coil lorry")
lorry = actors.spawn_actor_from_class(
    unreal.StaticMeshActor, unreal.Vector(-500, 0, 0), unreal.Rotator(0, 0, -90))
lorry.set_actor_label("LB_INBOUND_V028_LorryFourCoil_Coherent")
lorry.static_mesh_component.set_static_mesh(mesh)
lorry.static_mesh_component.set_collision_enabled(unreal.CollisionEnabled.QUERY_AND_PHYSICS)
lorry.static_mesh_component.set_editor_property("can_ever_affect_navigation", True)
lorry.tags = [
    unreal.Name("LB.Asset.ValidationOnly"),
    unreal.Name("LB.Asset.CandidateNotPromoted"),
    unreal.Name("LB.Inbound.ExactFourCoils"),
    unreal.Name("LB.Engineering.Values.TBC"),
]

overview = next(a for a in actors.get_all_level_actors()
                if a.get_actor_label() == "LB_CAM_InboundHall_ProcessOverview_v528")
overview.set_actor_location(unreal.Vector(0, -5200, 1500), False, False)
overview.set_actor_rotation(unreal.MathLibrary.find_look_at_rotation(
    overview.get_actor_location(), unreal.Vector(0, 0, 260)), False)
overview.camera_component.set_editor_property("field_of_view", 48.0)

hero = next(a for a in actors.get_all_level_actors()
            if a.get_actor_label() == "LB_CAM_InboundHall_CraneHero_v528")
hero.set_actor_location(unreal.Vector(200, -3200, 1180), False, False)
hero.set_actor_rotation(unreal.MathLibrary.find_look_at_rotation(
    hero.get_actor_location(), unreal.Vector(200, 0, 310)), False)
hero.camera_component.set_editor_property("field_of_view", 50.0)

unreal.AutomationUtilsBlueprintLibrary.finish_all_asset_compilation()
if not levels.save_current_level():
    raise RuntimeError("Failed saving v528 coherent inbound cell")
unreal.log("LINE_BOSS_INBOUND_COHERENT_LORRY_V528_BUILD_PASS")
