"""Camera-only detail-review successor of retained isolated inbound v551."""
from pathlib import Path
import unreal

root = Path(__file__).parent
source = (root / "build_inbound_installed_cell_v551.py").read_text(encoding="utf-8")
source = source.replace("v551", "v552").replace("V551", "V552").replace("V051_", "V052_")
exec(compile(source, str(root / "build_inbound_installed_cell_v551.py"), "exec"), globals(), globals())

actors = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
levels = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
tags = [unreal.Name("LB.Asset.ValidationOnly"), unreal.Name("LB.Asset.CandidateNotPromoted"),
        unreal.Name("LB.Engineering.Values.TBC"), unreal.Name("LB.Inbound.ProPack.20260807")]

def camera(label, location, target, fov):
    actor = actors.spawn_actor_from_class(unreal.CameraActor, unreal.Vector(*location), unreal.Rotator())
    actor.set_actor_label(label)
    actor.set_actor_rotation(unreal.MathLibrary.find_look_at_rotation(actor.get_actor_location(), unreal.Vector(*target)), False)
    actor.camera_component.set_editor_property("field_of_view", fov)
    actor.tags = tags
    return actor

# Evidence-only views expose the imported modular hardware already present in
# v551; they do not change equipment placement or claim operational clearance.
camera("LB_CAM_InboundHall_DockDetail_v552", (-1450, 2500, 920), (-2550, 0, 230), 50.0)
camera("LB_CAM_InboundHall_HandoffDetail_v552", (2050, 2450, 880), (950, 0, 170), 48.0)

if not levels.save_current_level():
    raise RuntimeError("Failed saving v552 detail-review successor")
unreal.log("LINE_BOSS_INBOUND_DETAIL_CAMERAS_V552_BUILD_PASS")
