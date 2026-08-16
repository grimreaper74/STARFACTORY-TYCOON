"""Compare the lorry-only bright wrapped-steel candidate in retained v540 context."""
from pathlib import Path
import unreal

root = Path(__file__).parent
source = (root / "build_inbound_installed_cell_v540.py").read_text(encoding="utf-8")
source = source.replace("v540", "v548").replace("V540", "V548").replace("V040_", "V048_")
exec(compile(source, str(root / "build_inbound_installed_cell_v540.py"), "exec"), globals(), globals())

library = unreal.EditorAssetLibrary
actors = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
levels = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
mesh = library.load_asset(
    "/Game/LineBoss/IndustrialKit/InboundCoilDelivery/LorryAssemblyCandidate_v003/SM_CA_MW_Inbound_LorryFourCoil_v003")
if not isinstance(mesh, unreal.StaticMesh):
    raise RuntimeError("Missing bright-wrap lorry candidate v003")
lorry = next(a for a in actors.get_all_level_actors() if a.get_actor_label() == "LB_INBOUND_V048_LorryFourCoil_Coherent")
lorry.static_mesh_component.set_static_mesh(mesh)
lorry.tags = list(lorry.tags) + [unreal.Name("LB.Visual.BrightWrappedSteel.v547")]
if not levels.save_current_level():
    raise RuntimeError("Failed saving v548 bright-wrap comparison")
unreal.log("LINE_BOSS_INBOUND_LORRY_BRIGHT_WRAP_REVIEW_V548_BUILD_PASS")
