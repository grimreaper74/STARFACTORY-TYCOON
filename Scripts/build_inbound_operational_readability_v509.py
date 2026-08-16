"""Build fresh isolated v509; never modifies rejected v508 or retained v438."""
from pathlib import Path
import unreal

source = (Path(__file__).parent / "build_inbound_operational_readability_v508.py").read_text(encoding="utf-8")
source = source.replace("OperationalReadability_v508", "OperationalReadability_v509")
source = source.replace("LB_INBOUND_V008_", "LB_INBOUND_V009_")
source = source.replace("OperationalReadability_v508", "OperationalReadability_v509")
source = source.replace("V508", "V509")

# Put the handoff lane beside the trailer/crane line, not behind it from the review camera.
source = source.replace("(650, 410, 37)", "(760, 260, 37)")
source = source.replace("(650, 410, 45)", "(760, 260, 45)")
source = source.replace("(650, 410, 83)", "(760, 260, 83)")
source = source.replace("(650, 410, 185)", "(760, 260, 185)")

# Higher, wider three-quarter view keeps cab, four trailer coils, saddle and loaded AGV visible.
source = source.replace("unreal.Vector(-2050, -2300, 1160)", "unreal.Vector(-2350, -2700, 1450)")
source = source.replace("unreal.Vector(85, 260, 190)", "unreal.Vector(100, 230, 170)")
source = source.replace('"field_of_view": 53.0', '"field_of_view": 56.0')

exec(compile(source, str(Path(__file__)), "exec"), globals(), globals())

# Use the retained pale protective-wrap material only on authored steel/coil slots.
wrap = unreal.EditorAssetLibrary.load_asset(
    "/Game/LineBoss/Candidates/PressShop/PackagedCoilSurface_v232/Materials/MI_CA_MW_PaleSilverProtectiveWrap_v232"
)
if wrap is None:
    raise RuntimeError("Missing retained pale protective-wrap material")

for actor in unreal.get_editor_subsystem(unreal.EditorActorSubsystem).get_all_level_actors():
    label = actor.get_actor_label()
    if label not in ("LB_INBOUND_V009_CoilTrailer", "LB_INBOUND_V009_AGV_LoadedCoil"):
        continue
    component = actor.static_mesh_component
    slot_names = [str(name) for name in component.get_material_slot_names()]
    changed = 0
    for index, slot_name in enumerate(slot_names):
        lowered = slot_name.lower()
        if label.endswith("AGV_LoadedCoil") or "steel" in lowered or "coil" in lowered:
            component.set_material(index, wrap)
            changed += 1
    if changed == 0:
        raise RuntimeError(f"No coil/steel material slots found for {label}: {slot_names}")

unreal.AutomationUtilsBlueprintLibrary.finish_all_asset_compilation()
if not unreal.get_editor_subsystem(unreal.LevelEditorSubsystem).save_current_level():
    raise RuntimeError("Failed saving v509 material/readability successor")
unreal.log("LINE_BOSS_INBOUND_OPERATIONAL_READABILITY_V509_FINAL_PASS")
