"""Add the missing 2126 outbound panel-pallet dispatch endpoint.

The visual carriers are deliberately simple, wheel-less native Unreal geometry.
Approved Press Shop dunnage supplies the finished-panel payload.  The low base
is also the gameplay collision proxy, so the endpoint is more than dressing.
Only the isolated FullHall candidate may be saved.
"""
import hashlib
import json
from pathlib import Path

import unreal


PROJECT = Path(r"C:\Users\greg_\Projects\LineBossCarFactory_Unreal 5.8")
MAP = "/Game/LineBoss/Candidates/PressShop/PressShop2126_FullHall_v001/Maps/LB_PressShop_2126_FullHall_v001"
RECEIPT = PROJECT / "Saved" / "Audits" / "PressShop2126" / "add_outbound_hover_pallets_v001_receipt.json"
TAG = unreal.Name("LB.PressShop.2126.OutboundHoverPallets.v001")
DUNNAGE = "/Game/LineBoss/Factory/OneFactory/v001/Native/Press/MaterialFlowPack_v002/Meshes/SM_CA_MW_PT_S07OutboundDunnage_v001"
GREEN = "/Game/LineBoss/Candidates/PressShop/PressShop2126_v003/Materials/M_LB_PS2126v003_CairnwellGreen"
YELLOW = "/Game/LineBoss/Candidates/PressShop/PressShop2126_v003/Materials/M_LB_PS2126v003_SafetyYellow"
RED = "/Game/LineBoss/Candidates/PressShop/PressShop2126_v003/Materials/M_LB_PS2126v003_StatusRed"
ZONE = "/Game/LineBoss/Candidates/PressShop/PressShop2126_v003/Materials/M_LB_PS2126v003_PaleGreenZone"
PROTECTED = {
    PROJECT / "Content" / "LineBoss" / "Maps" / "LB_PressShop_BuilderAuthorityCandidate_v438.umap": "5029c9d827d9a1d72c12f27ee757c9bc1e47febd5006ce6d7ba319aad2e7fec8",
    PROJECT / "Content" / "LineBoss" / "Candidates" / "PressShop" / "PressShop2126_v002" / "Maps" / "LB_PressShop_2126_Steam_v002.umap": "cc09cf46d33e8a562d97f5a3bc35a5b42c9582d8e4650cf315694ebf340e4aa0",
}


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest().lower()


def spawn(label, mesh, location, scale, material=None, collision=False, role="Visual"):
    actor = unreal.EditorLevelLibrary.spawn_actor_from_class(
        unreal.StaticMeshActor, unreal.Vector(*location), unreal.Rotator())
    if actor is None:
        raise RuntimeError("could not spawn " + label)
    actor.set_actor_label(label)
    actor.tags = [TAG, unreal.Name("LB.PressShop.2126.Outbound"), unreal.Name("LB.Role." + role)]
    actor.static_mesh_component.set_static_mesh(mesh)
    actor.set_actor_scale3d(unreal.Vector(*scale))
    if material is not None:
        actor.static_mesh_component.set_material(0, material)
    actor.static_mesh_component.set_collision_enabled(
        unreal.CollisionEnabled.QUERY_AND_PHYSICS if collision else unreal.CollisionEnabled.NO_COLLISION)
    actor.static_mesh_component.set_mobility(
        unreal.ComponentMobility.MOVABLE if collision else unreal.ComponentMobility.STATIC)
    return actor


before = {str(path): digest(path) for path in PROTECTED}
for path, expected in PROTECTED.items():
    if before[str(path)] != expected:
        raise RuntimeError("protected map missing or changed: " + str(path))
if not unreal.EditorLoadingAndSavingUtils.load_map(MAP):
    raise RuntimeError("could not load isolated 2126 candidate")
actors = list(unreal.EditorLevelLibrary.get_all_level_actors())
if any(TAG in actor.tags for actor in actors):
    raise RuntimeError("outbound hover-pallet pass already exists")
if not any(actor.get_actor_label() == "2126 OUTBOUND | robotic finished-panel palletisation cell" for actor in actors):
    raise RuntimeError("palletisation cell missing; refusing disconnected outbound endpoint")

cube = unreal.load_asset("/Engine/BasicShapes/Cube.Cube")
cylinder = unreal.load_asset("/Engine/BasicShapes/Cylinder.Cylinder")
dunnage = unreal.load_asset(DUNNAGE)
green = unreal.load_asset(GREEN)
yellow = unreal.load_asset(YELLOW)
red = unreal.load_asset(RED)
zone = unreal.load_asset(ZONE)
if not all(isinstance(mesh, unreal.StaticMesh) for mesh in (cube, cylinder, dunnage)):
    raise RuntimeError("native/reused outbound meshes missing")
if not all(isinstance(mat, unreal.MaterialInterface) for mat in (green, yellow, red, zone)):
    raise RuntimeError("brand materials missing")
if int(dunnage.get_num_triangles(0)) != 420:
    raise RuntimeError("approved outbound dunnage topology changed")

placed = []
# A broad painted lane links the palletiser to the dispatch door.  The long
# dimension is X because the endpoint turns 90 degrees after the +Y press flow.
placed.append(spawn(
    "2126 OUTBOUND | pale-green magnetic pallet dispatch lane", cube,
    (5000.0, 4495.0, 3.0), (60.0, 18.0, 0.04), zone, False, "FloorZone").get_actor_label())

stations = (("A", 3450.0), ("B", 5050.0), ("C", 6650.0))
dunnage_min_z = dunnage.get_bounding_box().min.z
for slot, x in stations:
    # 440 x 360 x 42 cm magnetic base.  This visible mesh is also a coarse,
    # honest collision proxy for selection, obstruction and future movement.
    placed.append(spawn(
        f"2126 OUTBOUND | hover pallet {slot} collision base", cube,
        (x, 4495.0, 38.0), (4.4, 3.6, 0.42), green, True, "MovableCollision").get_actor_label())
    for side, y in (("north", 4668.0), ("south", 4322.0)):
        placed.append(spawn(
            f"2126 OUTBOUND | hover pallet {slot} safety rail {side}", cube,
            (x, y, 67.0), (4.0, 0.09, 0.12), yellow, False, "SafetyAccent").get_actor_label())
    placed.append(spawn(
        f"2126 OUTBOUND | hover pallet {slot} status beacon", cylinder,
        (x + 185.0, 4640.0, 105.0), (0.18, 0.18, 0.42), red, False, "StatusBeacon").get_actor_label())
    payload_z = 92.0 - dunnage_min_z
    payload = spawn(
        f"2126 OUTBOUND | finished-panel payload {slot}", dunnage,
        (x, 4495.0, payload_z), (0.82, 0.82, 0.82), None, False, "FinishedPanels")
    placed.append(payload.get_actor_label())

if not unreal.EditorLoadingAndSavingUtils.save_current_level():
    raise RuntimeError("outbound hover-pallet pass did not save")
unreal.EditorLoadingAndSavingUtils.save_dirty_packages(True, True)
after = {str(path): digest(path) for path in PROTECTED}
if after != before:
    raise RuntimeError("protected maps changed during outbound pass")

RECEIPT.parent.mkdir(parents=True, exist_ok=True)
RECEIPT.write_text(json.dumps({
    "status": "PASS__2126_OUTBOUND_HOVER_PALLETS_ADDED",
    "map": MAP,
    "placed": placed,
    "carrier_count": len(stations),
    "wheel_count": 0,
    "finished_panel_payload_count": len(stations),
    "payload_asset": DUNNAGE,
    "payload_triangles_lod0": int(dunnage.get_num_triangles(0)),
    "collision": "each movable green carrier base has QueryAndPhysics collision",
    "motion_status": "movable actors and route are authored; runtime dispatch controller remains pending",
    "protected_sha256_before": before,
    "protected_sha256_after": after,
}, indent=2, sort_keys=True) + "\n", encoding="utf-8")
unreal.log("PRESSSHOP_2126_OUTBOUND_HOVER_PALLETS_PASS receipt=" + str(RECEIPT))
unreal.SystemLibrary.quit_editor()
