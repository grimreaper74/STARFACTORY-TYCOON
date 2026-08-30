"""Add native transfer infrastructure and a continuous painted zone under the 2126 sprite train."""
import hashlib
import json
from pathlib import Path
import unreal

PROJECT = Path(r"C:\Users\greg_\Projects\LineBossCarFactory_Unreal 5.8")
MAP = "/Game/LineBoss/Candidates/PressShop/PressShop2126_FullHall_v001/Maps/LB_PressShop_2126_FullHall_v001"
RECEIPT = PROJECT / "Saved" / "Audits" / "PressShop2126" / "add_transfer_spine_floor_zone_v001_receipt.json"
TAG = unreal.Name("LB.PressShop.2126.TransferSpine.v001")
TRANSFER_RAIL = "/Game/LineBoss/Candidates/PressTrains/Shared/Presentation_v003/SM_CA_MW_PT_TransferRail_v003"
ZONE_MATERIAL = "/Game/LineBoss/Candidates/PressShop/PressShop2126_v003/Materials/M_LB_PS2126v003_PaleGreenZone"
YELLOW_MATERIAL = "/Game/LineBoss/Candidates/PressShop/PressShop2126_v003/Materials/M_LB_PS2126v003_SafetyYellow"
WARM_WHITE_MATERIAL = "/Game/LineBoss/Candidates/PressShop/PressShop2126_v003/Materials/M_LB_PS2126v003_WarmWhite"
PROTECTED = {
    PROJECT / "Content" / "LineBoss" / "Maps" / "LB_PressShop_BuilderAuthorityCandidate_v438.umap": "5029c9d827d9a1d72c12f27ee757c9bc1e47febd5006ce6d7ba319aad2e7fec8",
    PROJECT / "Content" / "LineBoss" / "Candidates" / "PressShop" / "PressShop2126_v002" / "Maps" / "LB_PressShop_2126_Steam_v002.umap": "cc09cf46d33e8a562d97f5a3bc35a5b42c9582d8e4650cf315694ebf340e4aa0",
}


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest().lower()


def spawn_mesh(label, mesh, location, scale, material=None):
    actor = unreal.EditorLevelLibrary.spawn_actor_from_class(unreal.StaticMeshActor, unreal.Vector(*location), unreal.Rotator(0.0, 0.0, 0.0))
    if actor is None:
        raise RuntimeError("could not spawn " + label)
    actor.set_actor_label(label)
    actor.tags = [TAG]
    actor.static_mesh_component.set_static_mesh(mesh)
    actor.set_actor_scale3d(unreal.Vector(*scale))
    actor.static_mesh_component.set_collision_enabled(unreal.CollisionEnabled.NO_COLLISION)
    if material is not None:
        actor.static_mesh_component.set_material(0, material)
    return actor


before = {str(path): digest(path) for path in PROTECTED}
for path, expected in PROTECTED.items():
    if before[str(path)] != expected:
        raise RuntimeError(f"protected map missing or changed: {path}")
if not unreal.EditorLoadingAndSavingUtils.load_map(MAP):
    raise RuntimeError("could not load isolated 2126 candidate")
actors = list(unreal.EditorLevelLibrary.get_all_level_actors())
if any(TAG in actor.tags for actor in actors):
    raise RuntimeError("transfer spine pass already exists")

rail = unreal.load_asset(TRANSFER_RAIL)
cube = unreal.load_asset("/Engine/BasicShapes/Cube.Cube")
zone_mat = unreal.load_asset(ZONE_MATERIAL)
yellow_mat = unreal.load_asset(YELLOW_MATERIAL)
white_mat = unreal.load_asset(WARM_WHITE_MATERIAL)
if not isinstance(rail, unreal.StaticMesh) or not isinstance(cube, unreal.StaticMesh):
    raise RuntimeError("required native/reused meshes missing")
if not all(isinstance(mat, unreal.MaterialInterface) for mat in (zone_mat, yellow_mat, white_mat)):
    raise RuntimeError("required brand materials missing")

# Remove four obsolete local task lights that created isolated white pools in the production lane.
removed_lights = []
for actor in actors:
    if not isinstance(actor, unreal.RectLight):
        continue
    loc = actor.get_actor_location()
    if -6500.0 <= loc.x <= -500.0 and -500.0 <= loc.y <= 6000.0:
        removed_lights.append(actor.get_actor_label())
        unreal.EditorLevelLibrary.destroy_actor(actor)

placed = []
# Large painted process zone plus cream operator lanes; broad shapes read at management scale.
placed.append(spawn_mesh("2126 FLOOR | continuous pale-green press zone", cube, (-3500.0, 1700.0, 3.0), (34.0, 82.0, 0.04), zone_mat).get_actor_label())
placed.append(spawn_mesh("2126 FLOOR | operator lane west", cube, (-5350.0, 1700.0, 7.0), (2.4, 82.0, 0.025), white_mat).get_actor_label())
placed.append(spawn_mesh("2126 FLOOR | service lane east", cube, (-1650.0, 1700.0, 7.0), (2.4, 82.0, 0.025), white_mat).get_actor_label())

# Two long verified transfer rails form one visible automation spine through all stations.
for side, x in (("operator", -4250.0), ("service", -2750.0)):
    placed.append(spawn_mesh(f"2126 TRANSFER | continuous rail {side}", rail, (x, 2600.0, 735.0), (1.0, 1.28, 1.0)).get_actor_label())

# Three native yellow shuttle carriers mark the controllable transfer pitches.
for index, y in enumerate((800.0, 2600.0, 4400.0), start=1):
    placed.append(spawn_mesh(f"2126 TRANSFER | magnetic shuttle {index}", cube, (-3500.0, y, 790.0), (4.2, 2.4, 0.75), yellow_mat).get_actor_label())

if not unreal.EditorLoadingAndSavingUtils.save_current_level():
    raise RuntimeError("transfer spine/floor pass did not save")
unreal.EditorLoadingAndSavingUtils.save_dirty_packages(True, True)
after = {str(path): digest(path) for path in PROTECTED}
if after != before:
    raise RuntimeError("protected maps changed during transfer spine pass")

RECEIPT.parent.mkdir(parents=True, exist_ok=True)
RECEIPT.write_text(json.dumps({
    "status": "PASS__2126_TRANSFER_SPINE_AND_PROCESS_ZONE_ADDED",
    "map": MAP,
    "placed": placed,
    "removed_local_rect_lights": removed_lights,
    "transfer_rail_asset": TRANSFER_RAIL,
    "transfer_rail_triangles_lod0": int(rail.get_num_triangles(0)),
    "gameplay_status": "visual transfer carriers are separate actors; motion/controller wiring pending",
    "protected_sha256_before": before,
    "protected_sha256_after": after,
}, indent=2, sort_keys=True) + "\n", encoding="utf-8")
unreal.log(f"PRESSSHOP_2126_TRANSFER_SPINE_FLOOR_PASS receipt={RECEIPT}")
unreal.SystemLibrary.quit_editor()
