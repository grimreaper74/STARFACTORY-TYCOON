"""Install additive dock architecture v002 into a direct visual child of v551."""
from pathlib import Path
import unreal

root = Path(__file__).parent
source = (root / "build_inbound_installed_cell_v551.py").read_text(encoding="utf-8")
source = source.replace("v551", "v554").replace("V551", "V554").replace("V051_", "V054_")
exec(compile(source, str(root / "build_inbound_installed_cell_v551.py"), "exec"), globals(), globals())

library = unreal.EditorAssetLibrary
actors = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
levels = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
dock = library.load_asset("/Game/LineBoss/IndustrialKit/InboundCoilDelivery/DockArchitectureCandidate_v002/SM_CA_MW_Inbound_DockArchitecture_v002")
if not isinstance(dock, unreal.StaticMesh):
    raise RuntimeError("Missing isolated dock architecture v002")
installed = next(a for a in actors.get_all_level_actors() if a.get_actor_label() == "LB_INBOUND_V054_PurposeBuiltDockArchitecture")
installed.static_mesh_component.set_static_mesh(dock)
installed.tags = list(installed.tags) + [unreal.Name("LB.Visual.DockArchitecture.v002")]

tags = [unreal.Name("LB.Asset.ValidationOnly"), unreal.Name("LB.Asset.CandidateNotPromoted"),
        unreal.Name("LB.Engineering.Values.TBC"), unreal.Name("LB.Inbound.ProPack.20260807")]
def camera(label, location, target, fov):
    actor = actors.spawn_actor_from_class(unreal.CameraActor, unreal.Vector(*location), unreal.Rotator())
    actor.set_actor_label(label)
    actor.set_actor_rotation(unreal.MathLibrary.find_look_at_rotation(actor.get_actor_location(), unreal.Vector(*target)), False)
    actor.camera_component.set_editor_property("field_of_view", fov)
    actor.tags = tags

camera("LB_CAM_InboundHall_DockDetail_v554", (-1450, 2500, 920), (-2550, 0, 230), 50.0)
camera("LB_CAM_InboundHall_HandoffDetail_v554", (2050, 2450, 880), (950, 0, 170), 48.0)

if not levels.save_current_level():
    raise RuntimeError("Failed saving v554 installed dock-detail review")
unreal.log("LINE_BOSS_INBOUND_DOCK_V002_REVIEW_V554_BUILD_PASS")
