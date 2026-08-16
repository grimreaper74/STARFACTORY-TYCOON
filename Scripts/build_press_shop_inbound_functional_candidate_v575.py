"""Bind the installed inbound visuals to one persistent gameplay chain."""
import unreal

MAP = "/Game/LineBoss/Developer/Validation/LB_PressShop_InboundFunctionalCandidate_v575"
levels = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
actors = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
if not levels.load_level(MAP):
    raise RuntimeError("Could not load v575")

existing = actors.get_all_level_actors()
if any("LB.Inbound.Functional.v575" in {str(t) for t in a.tags} for a in existing):
    raise RuntimeError("Refusing duplicate inbound authority")
agvs = [a for a in existing if a.get_class().get_name() == "LBCoilAGVController"]
if len(agvs) != 1:
    raise RuntimeError(f"Expected one retained Coil AGV controller, found {len(agvs)}")

def spawn(cls, label, location):
    actor = actors.spawn_actor_from_class(cls, unreal.Vector(*location), unreal.Rotator())
    if not actor:
        raise RuntimeError(f"Could not spawn {label}")
    actor.set_actor_label(label)
    actor.tags = [unreal.Name("LB.Inbound.Functional.v575"), unreal.Name("LB.Authority.Gameplay")]
    actor.set_actor_hidden_in_game(True)
    root = actor.get_root_component()
    if root and hasattr(root, "set_visibility"):
        root.set_visibility(False, True)
    return actor

# Locations follow the fixed Pro visual stations: protected dock -> AGV handoff -> PR-003.
dock = spawn(unreal.LBFactoryBuildMachine, "LB_INBOUND_V575_DockAuthority", (-13100.0, -2000.0, 0.0))
if not dock.configure("INBOUND-001", unreal.LBFactoryBuildMachineType.INBOUND_DELIVERY_DOCK):
    raise RuntimeError("Could not configure inbound dock authority")

store = spawn(unreal.LBPressShopStorageZone, "LB_INBOUND_V575_PR003StoreAuthority", (-6500.0, -1500.0, 0.0))
if not store.configure("SZ-COIL-PR003", unreal.LBPressShopStorageType.BARE_COILS, 12,
                       unreal.Vector(650.0, 350.0, 160.0)):
    raise RuntimeError("Could not configure PR-003 storage authority")
if not store.configure_layout(6, 2, unreal.Vector2D(220.0, 600.0), 0.0):
    raise RuntimeError("Could not configure 6x2 PR-003 storage layout")
store.configure_replenishment(4, 4, 2)

link = spawn(unreal.LBFactoryTransportLink, "LB_INBOUND_V575_DockToPR003Link", (-9800.0, -1750.0, 0.0))
if not link.configure(dock.output_port, store.ingress_point):
    raise RuntimeError("Could not configure dock-to-store transport link")

delivery = spawn(unreal.LBInboundDeliveryController, "LB_INBOUND_V575_DeliveryAuthority", (0.0, 0.0, 0.0))
if not delivery.configure(dock, store, agvs[0]):
    raise RuntimeError("Could not bind inbound delivery controller")

if not levels.save_current_level():
    raise RuntimeError("Could not save functional v575")
unreal.log("LINE_BOSS_INBOUND_FUNCTIONAL_BUILD_V575_PASS")
