"""Fresh v524 hall review using the additive Modular_v005 source intake."""
from pathlib import Path
import unreal

root = Path(__file__).parent
source = (root / "build_inbound_installed_cell_v523.py").read_text(encoding="utf-8")
source = source.replace("v523", "v524").replace("V523", "V524").replace("V023_", "V024_")
exec(compile(source, str(root / "build_inbound_installed_cell_v523.py"), "exec"), globals(), globals())

library = unreal.EditorAssetLibrary
actors = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
levels = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
modules = (
    "LorryCab", "CoilTrailer", "DockGuidesAndRestraint", "DockControlAndSignals",
    "ReceivingSaddle", "AGVHandoffGuides", "IdentityScanner", "EntranceDockEnvelope",
)
changed = []
for name in modules:
    actor = next((a for a in actors.get_all_level_actors()
                  if isinstance(a, unreal.StaticMeshActor) and a.get_actor_label().endswith(name)), None)
    mesh = library.load_asset(
        f"/Game/LineBoss/IndustrialKit/InboundCoilDelivery/Candidate_v005/SM_CA_MW_MOD_{name}_v005")
    if actor is None or not isinstance(mesh, unreal.StaticMesh):
        raise RuntimeError(f"Missing v524 module actor/mesh {name}")
    actor.static_mesh_component.set_static_mesh(mesh)
    actor.set_actor_label(actor.get_actor_label().replace("V023", "V024"))
    changed.append(name)

# Release-comparison camera: pull back enough to include the complete cab and
# the AGV handoff while preserving readable equipment scale.
overview = next(a for a in actors.get_all_level_actors()
                if a.get_actor_label() == "LB_CAM_InboundHall_ProcessOverview_v524")
overview.set_actor_location(unreal.Vector(3500, -4200, 1950), False, False)
overview.set_actor_rotation(unreal.MathLibrary.find_look_at_rotation(
    overview.get_actor_location(), unreal.Vector(0, 0, 230)), False)
overview.camera_component.set_editor_property("field_of_view", 61.0)

unreal.AutomationUtilsBlueprintLibrary.finish_all_asset_compilation()
if not levels.save_current_level():
    raise RuntimeError("Failed saving v524 detailed inbound hall review")
unreal.log("LINE_BOSS_INBOUND_HALL_DETAILED_V524_BUILD_PASS " + ",".join(changed))
