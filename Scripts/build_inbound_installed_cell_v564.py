"""Compare controlled-PBR enclosure in retained detailed-lorry v561 context."""
from pathlib import Path
import unreal

root = Path(__file__).parent
source = (root / "build_inbound_installed_cell_v561.py").read_text(encoding="utf-8")
source = source.replace("v561", "v564").replace("V561", "V564").replace("V061_", "V064_")
exec(compile(source, str(root / "build_inbound_installed_cell_v561.py"), "exec"), globals(), globals())

library = unreal.EditorAssetLibrary
actors = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
levels = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
mesh = library.load_asset(
    "/Game/LineBoss/IndustrialKit/InboundCoilDelivery/EnclosureCandidate_v002/SM_CA_MW_Inbound_InstalledEnclosure_v002")
if not isinstance(mesh, unreal.StaticMesh):
    raise RuntimeError("Missing controlled-PBR protected enclosure v002")
enclosure = next(a for a in actors.get_all_level_actors()
                 if a.get_actor_label() == "LB_INBOUND_V064_PurposeBuiltInstalledEnclosure")
enclosure.static_mesh_component.set_static_mesh(mesh)
enclosure.tags = list(enclosure.tags) + [unreal.Name("LB.Visual.EnclosurePBR.v564")]
if not levels.save_current_level():
    raise RuntimeError("Failed saving v564 enclosure PBR comparison")
unreal.log("LINE_BOSS_INBOUND_ENCLOSURE_PBR_V564_BUILD_PASS")
