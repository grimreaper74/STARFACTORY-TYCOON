"""Install one authoritative inbound delivery chain on clean visual map v770."""
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
import unreal

SRC = "/Game/LineBoss/Maps/LB_PressShop_Trains_InboundVisual_v770"
MAP = "/Game/LineBoss/Maps/LB_PressShop_Trains_InboundRuntime_v772"
PROJECT = Path(unreal.Paths.project_dir()).resolve()
PROTECTED = PROJECT / "Content/LineBoss/Maps/LB_PressShop_BuilderAuthorityCandidate_v438.umap"
EXPECTED = "5029C9D827D9A1D72C12F27EE757C9BC1E47FEBD5006CE6D7BA319AAD2E7FEC8"
OUT = Path(unreal.Paths.project_saved_dir()) / "Audits/PressShopIntegration/clean_press_shop_inbound_runtime_v772.json"

def sha256(path): return hashlib.sha256(Path(path).read_bytes()).hexdigest().upper()
lib = unreal.EditorAssetLibrary
levels = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
actors = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
before = sha256(PROTECTED)
if before != EXPECTED: raise RuntimeError(f"Protected v438 mismatch: {before}")
if lib.does_asset_exist(MAP): raise RuntimeError(f"Fresh-map invariant failed: {MAP}")
if not levels.new_level_from_template(MAP, SRC): raise RuntimeError("Could not create v772")

all_actors = actors.get_all_level_actors()
by_label = {a.get_actor_label(): a for a in all_actors}
visual_tags = {
    "LB_INBOUND_V770_LorryFourCoil": "LB.Inbound.Visual.Lorry",
    "LB_INBOUND_V770_CraneBridge": "LB.Inbound.Visual.CraneBridge",
    "LB_INBOUND_V770_CraneTrolley": "LB.Inbound.Visual.CraneTrolley",
    "LB_INBOUND_V770_HoistBlock": "LB.Inbound.Visual.Hoist",
    "LB_INBOUND_V770_PoweredCHook": "LB.Inbound.Visual.Hook",
    "LB_INBOUND_V770_ReceivingSaddle": "LB.Inbound.Visual.Saddle",
}
for label, tag in visual_tags.items():
    actor = by_label.get(label)
    if actor is None: raise RuntimeError(f"Missing visual sequence actor {label}")
    actor.tags = list(actor.tags) + [unreal.Name(tag)]

mesh_specs = [
    ("LB_INBOUND_V772_AGV_Chassis", "/Game/LineBoss/IndustrialKit/MaterialHandling/CoilAGV/Candidate_v001/SM_LB_CoilAGV_Chassis_Candidate_v001", (-6200,-2000,45), ["LB.Vehicle.CoilAGV"]),
    ("LB_INBOUND_V772_AGV_LiftDeck", "/Game/LineBoss/IndustrialKit/MaterialHandling/CoilAGV/Candidate_v001/SM_LB_CoilAGV_LiftDeck_Candidate_v001", (-6200,-2000,83), ["LB.Vehicle.CoilAGV.LiftDeck"]),
    ("LB_INBOUND_V772_AGV_LoadedCoil", "/Game/LineBoss/IndustrialKit/MaterialHandling/MasterCoil/Candidate_v005/SM_LB_MasterCoil_Candidate_v005", (-6200,-2000,185), ["LB.Inventory.InTransfer", "LB.Vehicle.CoilAGV.Payload"]),
    ("LB_INBOUND_V772_CHook_CarriedCoil", "/Game/LineBoss/IndustrialKit/MaterialHandling/MasterCoil/Candidate_v005/SM_LB_MasterCoil_Candidate_v005", (-12000,-2050,256), ["LB.Inbound.Visual.HookCarriedCoil"]),
]
spawned_meshes=[]
for label,path,loc,tags in mesh_specs:
    mesh=lib.load_asset(path)
    if not isinstance(mesh,unreal.StaticMesh): raise RuntimeError(f"Missing {path}")
    actor=actors.spawn_actor_from_class(unreal.StaticMeshActor,unreal.Vector(*loc),unreal.Rotator())
    actor.set_actor_label(label); actor.static_mesh_component.set_static_mesh(mesh)
    actor.static_mesh_component.set_editor_property("mobility",unreal.ComponentMobility.MOVABLE)
    actor.tags=[unreal.Name("LB.Inbound.Runtime.v772"),unreal.Name("LB.Authority.Gameplay")]+[unreal.Name(t) for t in tags]
    spawned_meshes.append(label)

# Physical route marking: thin, non-blocking centre lane between store and dock.
cube=lib.load_asset("/Engine/BasicShapes/Cube.Cube")
route=actors.spawn_actor_from_class(unreal.StaticMeshActor,unreal.Vector(-8425,-2000,-8),unreal.Rotator())
route.set_actor_label("LB_INBOUND_V772_AGVRouteMarking")
route.static_mesh_component.set_static_mesh(cube)
route.set_actor_scale3d(unreal.Vector(44.5,2.4,0.025))
route.static_mesh_component.set_collision_enabled(unreal.CollisionEnabled.NO_COLLISION)
route.tags=[unreal.Name("LB.Inbound.Route.Marking"),unreal.Name("LB.Engineering.Values.TBC")]

# One machine authority, one storage authority, one AGV controller, one link,
# and one delivery coordinator. These are the same proven runtime classes used
# by v597, but with a route matching the clean expanded layout.
dock=actors.spawn_actor_from_class(unreal.LBFactoryBuildMachine,unreal.Vector(-11250,-2000,0),unreal.Rotator())
dock.set_actor_label("LB_INBOUND_V772_DockAuthority")
dock.tags=[unreal.Name("LB.Inbound.Runtime.v772"),unreal.Name("LB.Authority.Gameplay")]
if not dock.configure("INBOUND-001",unreal.LBFactoryBuildMachineType.INBOUND_DELIVERY_DOCK): raise RuntimeError("Dock configure failed")

store=actors.spawn_actor_from_class(unreal.LBPressShopStorageZone,unreal.Vector(-4500,-2000,0),unreal.Rotator())
store.set_actor_label("LB_INBOUND_V772_CoilStoreAuthority")
store.tags=[unreal.Name("LB.Inbound.Runtime.v772"),unreal.Name("LB.Authority.Gameplay")]
if not store.configure("SZ-COIL-PRESS",unreal.LBPressShopStorageType.BARE_COILS,12,unreal.Vector(650,600,160)): raise RuntimeError("Store configure failed")
if not store.configure_layout(6,2,unreal.Vector2D(220,600),0): raise RuntimeError("Store layout failed")
store.configure_replenishment(4,4,2)

link=actors.spawn_actor_from_class(unreal.LBFactoryTransportLink,unreal.Vector(-7875,-1750,0),unreal.Rotator())
link.set_actor_label("LB_INBOUND_V772_DockToStoreLink")
link.tags=[unreal.Name("LB.Inbound.Runtime.v772"),unreal.Name("LB.Authority.Gameplay")]
if not link.configure(dock.output_port,store.ingress_point): raise RuntimeError("Transport link configure failed")

agv=actors.spawn_actor_from_class(unreal.LBCoilAGVController,unreal.Vector(-6200,-2000,45),unreal.Rotator())
agv.set_actor_label("LB_INBOUND_V772_CoilAGVAuthority")
agv.tags=[unreal.Name("LB.Inbound.Runtime.v772"),unreal.Name("LB.Authority.Gameplay")]
if not agv.configure_route(unreal.Vector(-6200,-2000,45),unreal.Vector(-8400,-2000,45),unreal.Vector(-10650,-2000,45)): raise RuntimeError("AGV route configure failed")
if not agv.discover_and_bind(): raise RuntimeError("AGV visual binding failed")

delivery=actors.spawn_actor_from_class(unreal.LBInboundDeliveryController,unreal.Vector(0,0,0),unreal.Rotator())
delivery.set_actor_label("LB_INBOUND_V772_DeliveryAuthority")
delivery.tags=[unreal.Name("LB.Inbound.Runtime.v772"),unreal.Name("LB.Authority.Gameplay")]
if not delivery.configure(dock,store,agv): raise RuntimeError("Delivery authority configure failed")
trailer_coils=[by_label.get(f"LB_INBOUND_V770_TrailerWrappedCoil_{i:02d}") for i in range(1,5)]
if any(c is None for c in trailer_coils): raise RuntimeError("Four trailer coils not found")
if not delivery.configure_visual_sequence(
    by_label["LB_INBOUND_V770_LorryFourCoil"],by_label["LB_INBOUND_V770_CraneBridge"],
    by_label["LB_INBOUND_V770_CraneTrolley"],by_label["LB_INBOUND_V770_HoistBlock"],
    by_label["LB_INBOUND_V770_PoweredCHook"],by_label["LB_INBOUND_V770_ReceivingSaddle"],
    trailer_coils,unreal.Vector(-13700,-2000,0),unreal.Vector(-14200,-2000,0)):
    raise RuntimeError("Visual sequence binding failed")

unreal.AutomationUtilsBlueprintLibrary.finish_all_asset_compilation()
if not levels.save_current_level(): raise RuntimeError("Could not save v772")
after=sha256(PROTECTED)
if after!=before: raise RuntimeError("Protected v438 changed")
map_file=PROJECT/"Content/LineBoss/Maps/LB_PressShop_Trains_InboundRuntime_v772.umap"
payload={
    "$schema":"cairnwell/audit/clean-press-shop-inbound-runtime-v772/v1",
    "generated_utc":datetime.now(timezone.utc).isoformat(),
    "status":"PASS__ONE_CLEAN_INBOUND_RUNTIME_CHAIN_BOUND__PIE_AND_NAV_GATES_OPEN__NOT_PROMOTED",
    "source_map":SRC,"candidate_map":MAP,"map_sha256":sha256(map_file),
    "runtime_counts":{"dock_authority":1,"coil_store":1,"transport_link":1,"coil_agv_controller":1,"delivery_controller":1,"trailer_coils":4},
    "agv_route_cm":{"staged":[-6200,-2000,45],"turn":[-8400,-2000,45],"dock":[-10650,-2000,45]},
    "visual_sequence_bound":True,"spawned_runtime_meshes":spawned_meshes,
    "legacy_press_actors_imported":False,"legacy_unload_robot_imported":False,"meshy_credits_used":0,
    "protected_v438_sha256_before":before,"protected_v438_sha256_after":after,"promotion_authorized":False,
}
OUT.parent.mkdir(parents=True,exist_ok=True);OUT.write_text(json.dumps(payload,indent=2),encoding="utf-8")
unreal.log("LINE_BOSS_CLEAN_PRESS_SHOP_INBOUND_RUNTIME_V772_PASS")
