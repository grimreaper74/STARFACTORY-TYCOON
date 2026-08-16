"""Compare controlled-PBR dock v003 in the direct-v551 installed review lineage."""
from pathlib import Path
import unreal

root = Path(__file__).parent
source = (root / "build_inbound_installed_cell_v554.py").read_text(encoding="utf-8")
source = source.replace("v554", "v557").replace("V554", "V557").replace("V054_", "V057_")
exec(compile(source, str(root / "build_inbound_installed_cell_v554.py"), "exec"), globals(), globals())

library = unreal.EditorAssetLibrary
actors = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
levels = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
mesh = library.load_asset("/Game/LineBoss/IndustrialKit/InboundCoilDelivery/DockArchitectureCandidate_v003/SM_CA_MW_Inbound_DockArchitecture_v003")
if not isinstance(mesh, unreal.StaticMesh):
    raise RuntimeError("Missing isolated PBR dock v003")
installed = next(a for a in actors.get_all_level_actors() if a.get_actor_label() == "LB_INBOUND_V057_PurposeBuiltDockArchitecture")
installed.static_mesh_component.set_static_mesh(mesh)
installed.tags = list(installed.tags) + [unreal.Name("LB.Visual.DockArchitecture.PBR.v003")]
if not levels.save_current_level():
    raise RuntimeError("Failed saving v557 dock PBR review")
unreal.log("LINE_BOSS_INBOUND_DOCK_PBR_REVIEW_V557_BUILD_PASS")
