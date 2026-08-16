"""Compare controlled-PBR crane frame/bridge in retained v564 context."""
from pathlib import Path
import unreal

root = Path(__file__).parent
source = (root / "build_inbound_installed_cell_v564.py").read_text(encoding="utf-8")
source = source.replace("v564", "v567").replace("V564", "V567").replace("V064_", "V067_")
exec(compile(source, str(root / "build_inbound_installed_cell_v564.py"), "exec"), globals(), globals())

library = unreal.EditorAssetLibrary
actors = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
levels = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
asset_root = "/Game/LineBoss/IndustrialKit/MaterialHandling/BridgeCrane/InboundInstalledCrane/Candidate_v002"
swaps = {
    "LB_INBOUND_V067_StaticRunwayFrame": f"{asset_root}/SM_CA_MW_InboundCrane_StaticRunwayFrame_v002",
    "LB_INBOUND_V067_MovingBridge": f"{asset_root}/SM_CA_MW_InboundCrane_MovingBridge_v002",
}
by_label = {a.get_actor_label(): a for a in actors.get_all_level_actors()}
for label, path in swaps.items():
    actor = by_label.get(label)
    mesh = library.load_asset(path)
    if actor is None or not isinstance(mesh, unreal.StaticMesh):
        raise RuntimeError(f"Missing crane swap input: {label} / {path}")
    actor.static_mesh_component.set_static_mesh(mesh)
    actor.tags = list(actor.tags) + [unreal.Name("LB.Visual.CranePBR.v567")]
if not levels.save_current_level():
    raise RuntimeError("Failed saving v567 crane PBR comparison")
unreal.log("LINE_BOSS_INBOUND_CRANE_PBR_V567_BUILD_PASS")
