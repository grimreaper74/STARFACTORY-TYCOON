"""Metal-readability successor of v544 using restrained ambient and local reflections."""
from pathlib import Path
import unreal

root = Path(__file__).parent
source = (root / "build_inbound_installed_cell_v544.py").read_text(encoding="utf-8")
source = source.replace("v544", "v545").replace("V544", "V545").replace("V044_", "V045_")
exec(compile(source, str(root / "build_inbound_installed_cell_v544.py"), "exec"), globals(), globals())

actors = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
levels = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
tags = [unreal.Name("LB.Asset.ValidationOnly"), unreal.Name("LB.Asset.CandidateNotPromoted"),
        unreal.Name("LB.Engineering.Values.TBC"), unreal.Name("LB.Inbound.ProPack.20260807")]

sky = actors.spawn_actor_from_class(unreal.SkyLight, unreal.Vector(0, 0, 900), unreal.Rotator())
sky.set_actor_label("LB_INBOUND_V045_MetalReadabilitySky")
sky.get_component_by_class(unreal.SkyLightComponent).set_editor_properties({
    "intensity": 0.35,
    "real_time_capture": True,
    "lower_hemisphere_is_black": False,
})
sky.tags = tags

key = actors.spawn_actor_from_class(unreal.DirectionalLight, unreal.Vector(), unreal.Rotator(-52, 132, 0))
key.set_actor_label("LB_INBOUND_V045_MetalReadabilityKey")
key.get_component_by_class(unreal.DirectionalLightComponent).set_editor_properties({
    "intensity": 0.65,
    "light_color": unreal.Color(232, 240, 255, 255),
    "cast_shadows": True,
})
key.tags = tags

for index, location in enumerate(((-2800, 0, 450), (0, 0, 500), (2800, 0, 400)), 1):
    capture = actors.spawn_actor_from_class(unreal.SphereReflectionCapture, unreal.Vector(*location), unreal.Rotator())
    capture.set_actor_label(f"LB_INBOUND_V045_Reflection_{index:02d}")
    capture.get_component_by_class(unreal.SphereReflectionCaptureComponent).set_editor_property("influence_radius", 2600.0)
    capture.tags = tags

if not levels.save_current_level():
    raise RuntimeError("Failed saving v545 metal-readability review")
unreal.log("LINE_BOSS_INBOUND_METAL_READABILITY_V545_BUILD_PASS")
