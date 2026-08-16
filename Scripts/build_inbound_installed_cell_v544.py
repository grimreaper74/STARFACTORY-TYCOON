"""Visual comparison child of retained v540 using the additive PBR lorry."""
from pathlib import Path
import unreal

root = Path(__file__).parent
source = (root / "build_inbound_installed_cell_v540.py").read_text(encoding="utf-8")
source = source.replace("v540", "v544").replace("V540", "V544").replace("V040_", "V044_")
exec(compile(source, str(root / "build_inbound_installed_cell_v540.py"), "exec"), globals(), globals())

library = unreal.EditorAssetLibrary
actors = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
levels = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
lorry_mesh = library.load_asset(
    "/Game/LineBoss/IndustrialKit/InboundCoilDelivery/LorryAssemblyCandidate_v002/SM_CA_MW_Inbound_LorryFourCoil_v002")
if not isinstance(lorry_mesh, unreal.StaticMesh):
    raise RuntimeError("Missing additive PBR lorry candidate v002")
lorry = next(a for a in actors.get_all_level_actors() if a.get_actor_label() == "LB_INBOUND_V044_LorryFourCoil_Coherent")
lorry.static_mesh_component.set_static_mesh(lorry_mesh)
lorry.tags = list(lorry.tags) + [unreal.Name("LB.Visual.PBRCandidate.v543")]

if not levels.save_current_level():
    raise RuntimeError("Failed saving v544 PBR lorry comparison")
unreal.log("LINE_BOSS_INBOUND_LORRY_PBR_REVIEW_V544_BUILD_PASS")
