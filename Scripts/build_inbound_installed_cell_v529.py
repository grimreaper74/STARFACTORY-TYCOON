"""Fresh v529: owner-sheet linear sequence with a clear crane envelope."""
from pathlib import Path
import unreal

root = Path(__file__).parent
source = (root / "build_inbound_installed_cell_v528.py").read_text(encoding="utf-8")
source = source.replace("v528", "v529").replace("V528", "V529").replace("V028_", "V029_")
exec(compile(source, str(root / "build_inbound_installed_cell_v528.py"), "exec"), globals(), globals())

actors = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
levels = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)

def find(suffix):
    return next((a for a in actors.get_all_level_actors()
                 if a.get_actor_label().endswith(suffix)), None)

def place(suffix, location, yaw=None):
    actor = find(suffix)
    if actor is None:
        raise RuntimeError(f"Missing v529 actor: {suffix}")
    actor.set_actor_location(unreal.Vector(*location), False, False)
    if yaw is not None:
        actor.set_actor_rotation(unreal.Rotator(0, 0, yaw), False)
    return actor

# Upstream docked lorry. Its combined source origin keeps the cab and trailer
# coherent; the dock modules align to the trailer/cab rather than the crane.
place("LorryFourCoil_Coherent", (-1200, 0, 0), -90)
place("DockGuidesAndRestraint", (-1350, 0, 35), -90)
place("EntranceDockEnvelope", (-2050, 0, 244), -90)
place("DockControlAndSignals", (-1650, -350, 125), -90)

# Protected crane operating cell. Keep the powered hook and carried coil in a
# visibly empty lift envelope, not over the AGV and not intersecting the lorry.
for suffix, location, yaw in (
    ("StaticRunwayFrame", (0, 0, 0), 0),
    ("MovingBridge", (0, 0, 652), 0),
    ("CraneTrolley", (0, 0, 715), 0),
    ("HoistBlock", (0, 0, 500), 0),
    ("PoweredCHook", (0, 0, 315), 90),
    ("CHook_CarriedCoil", (0, -50, 256), 0),
    ("PurposeBuiltInstalledEnclosure", (0, 0, 0), 0),
):
    place(suffix, location, yaw)

# Downstream fixed set-down saddle, identity point and separate AGV handoff.
for suffix, location, yaw in (
    ("ReceivingSaddle", (750, 0, 70), 0),
    ("IdentityScanner", (750, -260, 93), 0),
    ("AGVHandoffGuides", (1350, 0, 37), 0),
    ("AGV_Chassis", (1350, 0, 45), 0),
    ("AGV_Deck", (1350, 0, 83), 0),
    ("AGV_LoadedCoil", (1350, 0, 185), 0),
):
    place(suffix, location, yaw)

overview = next(a for a in actors.get_all_level_actors()
                if a.get_actor_label() == "LB_CAM_InboundHall_ProcessOverview_v529")
overview.set_actor_location(unreal.Vector(-300, -6200, 2050), False, False)
overview.set_actor_rotation(unreal.MathLibrary.find_look_at_rotation(
    overview.get_actor_location(), unreal.Vector(-300, 0, 260)), False)
overview.camera_component.set_editor_property("field_of_view", 46.0)

hero = next(a for a in actors.get_all_level_actors()
            if a.get_actor_label() == "LB_CAM_InboundHall_CraneHero_v529")
hero.set_actor_location(unreal.Vector(1400, -3900, 1650), False, False)
hero.set_actor_rotation(unreal.MathLibrary.find_look_at_rotation(
    hero.get_actor_location(), unreal.Vector(0, 0, 310)), False)
hero.camera_component.set_editor_property("field_of_view", 51.0)

unreal.AutomationUtilsBlueprintLibrary.finish_all_asset_compilation()
if not levels.save_current_level():
    raise RuntimeError("Failed saving v529 owner-sequence inbound cell")
unreal.log("LINE_BOSS_INBOUND_OWNER_SEQUENCE_V529_BUILD_PASS")
