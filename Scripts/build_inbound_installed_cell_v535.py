"""Visual correction of v534: readable equipment, coils and aisle signage."""
from pathlib import Path
import unreal

root = Path(__file__).parent
source = (root / "build_inbound_installed_cell_v534.py").read_text(encoding="utf-8")
source = source.replace("v534", "v535").replace("V534", "V535").replace("V034_", "V035_")
exec(compile(source, str(root / "build_inbound_installed_cell_v534.py"), "exec"), globals(), globals())

actors = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
levels = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
tags = [unreal.Name("LB.Asset.ValidationOnly"), unreal.Name("LB.Asset.CandidateNotPromoted"),
        unreal.Name("LB.Engineering.Values.TBC"), unreal.Name("LB.Inbound.ProPack.20260807")]

for actor in actors.get_all_level_actors():
    if isinstance(actor, unreal.PostProcessVolume):
        settings = actor.settings
        settings.set_editor_property("auto_exposure_bias", 0.45)
        actor.settings = settings
    elif isinstance(actor, unreal.TextRenderActor) and actor.get_actor_label().startswith("LB_INBOUND_V035_"):
        actor.set_actor_rotation(unreal.Rotator(0, 0, 90), False)
        actor.text_render.set_editor_property("text_render_color", unreal.Color(238, 244, 238, 255))

# Soft aisle-side fill restores the silver coil and green vehicle read while
# keeping the crane cell's internal shadowing visible.
for i, x in enumerate((-3600, -1800, 0, 1800, 3600), 1):
    light = actors.spawn_actor_from_class(unreal.PointLight, unreal.Vector(x, 1650, 950), unreal.Rotator())
    light.set_actor_label(f"LB_INBOUND_V035_AisleFill_{i:02d}")
    light.point_light_component.set_editor_properties({"intensity": 1050.0, "attenuation_radius": 2500.0,
                                                        "source_radius": 180.0, "cast_shadows": False,
                                                        "light_color": unreal.Color(220, 232, 244, 255)})
    light.tags = tags

if not levels.save_current_level():
    raise RuntimeError("Failed saving v535 corrected inbound context")
unreal.log("LINE_BOSS_INBOUND_RELEASE_CONTEXT_V535_BUILD_PASS")
