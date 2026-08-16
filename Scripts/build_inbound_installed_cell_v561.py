"""Compare the detailed PBR four-coil lorry in the retained v558 context."""
from pathlib import Path
import unreal

root = Path(__file__).parent
source = (root / "build_inbound_installed_cell_v558.py").read_text(encoding="utf-8")
source = source.replace("v558", "v561").replace("V558", "V561").replace("V058_", "V061_")
exec(compile(source, str(root / "build_inbound_installed_cell_v558.py"), "exec"), globals(), globals())

library = unreal.EditorAssetLibrary
actors = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
levels = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
mesh = library.load_asset(
    "/Game/LineBoss/IndustrialKit/InboundCoilDelivery/LorryAssemblyCandidate_v005/SM_CA_MW_Inbound_LorryFourCoil_v005")
if not isinstance(mesh, unreal.StaticMesh):
    raise RuntimeError("Missing detailed PBR lorry v005")
lorry = next(a for a in actors.get_all_level_actors()
             if a.get_actor_label() == "LB_INBOUND_V061_LorryFourCoil_Coherent")
lorry.static_mesh_component.set_static_mesh(mesh)
lorry.tags = list(lorry.tags) + [unreal.Name("LB.Visual.DetailedLorry.v561")]
if not levels.save_current_level():
    raise RuntimeError("Failed saving v561 detailed-lorry comparison")
unreal.log("LINE_BOSS_INBOUND_DETAILED_LORRY_V561_BUILD_PASS")
