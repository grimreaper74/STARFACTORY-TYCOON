"""Add simple invisible Unreal collision proxies beneath all major 2126 sprites."""
import hashlib
import json
from pathlib import Path
import unreal

PROJECT = Path(r"C:\Users\greg_\Projects\LineBossCarFactory_Unreal 5.8")
MAP = "/Game/LineBoss/Candidates/PressShop/PressShop2126_FullHall_v001/Maps/LB_PressShop_2126_FullHall_v001"
RECEIPT = PROJECT / "Saved" / "Audits" / "PressShop2126" / "sprite_collision_proxies_v001_receipt.json"
TAG = unreal.Name("LB.PressShop.2126.SpriteCollision.v001")
PROTECTED = {
    PROJECT / "Content" / "LineBoss" / "Maps" / "LB_PressShop_BuilderAuthorityCandidate_v438.umap": "5029c9d827d9a1d72c12f27ee757c9bc1e47febd5006ce6d7ba319aad2e7fec8",
    PROJECT / "Content" / "LineBoss" / "Candidates" / "PressShop" / "PressShop2126_v002" / "Maps" / "LB_PressShop_2126_Steam_v002.umap": "cc09cf46d33e8a562d97f5a3bc35a5b42c9582d8e4650cf315694ebf340e4aa0",
}
PROXIES = (
    ("coil delivery carrier", (-9100.0, -2350.0, 170.0), (2400.0, 2200.0, 340.0)),
    ("autonomous unload gantry", (-8500.0, -2400.0, 600.0), (2800.0, 1600.0, 1200.0)),
    ("verification deband cell", (-7350.0, -3900.0, 450.0), (1800.0, 1200.0, 900.0)),
    ("magnetic coil buffer", (-6450.0, -900.0, 330.0), (2100.0, 1400.0, 660.0)),
    ("decoiler straightener feed", (-3500.0, -2000.0, 460.0), (3000.0, 2000.0, 920.0)),
    ("S01 deep draw", (-3500.0, -150.0, 600.0), (2800.0, 1800.0, 1200.0)),
    ("S02 redraw calibration", (-3500.0, 1650.0, 575.0), (2800.0, 1800.0, 1150.0)),
    ("S03 trim pierce", (-3500.0, 3450.0, 625.0), (2600.0, 1800.0, 1250.0)),
    ("S04 flange final form", (-3500.0, 5250.0, 600.0), (2600.0, 1800.0, 1200.0)),
    ("AI inspection metrology", (-600.0, 4495.0, 600.0), (2700.0, 1800.0, 1200.0)),
    ("robotic panel palletisation", (2215.0, 4495.0, 550.0), (2800.0, 1800.0, 1100.0)),
)


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest().lower()


before = {str(path): digest(path) for path in PROTECTED}
for path, expected in PROTECTED.items():
    if before[str(path)] != expected:
        raise RuntimeError("protected map missing or changed: " + str(path))
if not unreal.EditorLoadingAndSavingUtils.load_map(MAP):
    raise RuntimeError("could not load isolated 2126 candidate")
actors = list(unreal.EditorLevelLibrary.get_all_level_actors())
if any(TAG in actor.tags for actor in actors):
    raise RuntimeError("sprite collision pass already exists")
cube = unreal.load_asset("/Engine/BasicShapes/Cube.Cube")
if not isinstance(cube, unreal.StaticMesh):
    raise RuntimeError("native cube missing")

placed = []
for role, location, dimensions in PROXIES:
    actor = unreal.EditorLevelLibrary.spawn_actor_from_class(
        unreal.StaticMeshActor, unreal.Vector(*location), unreal.Rotator())
    if actor is None:
        raise RuntimeError("could not spawn collision proxy for " + role)
    actor.set_actor_label("2126 COLLISION | " + role)
    actor.tags = [TAG, unreal.Name("LB.Collision.GameplayProxy"), unreal.Name("LB.PressShop.2126")]
    component = actor.static_mesh_component
    component.set_static_mesh(cube)
    actor.set_actor_scale3d(unreal.Vector(dimensions[0] / 100.0, dimensions[1] / 100.0, dimensions[2] / 100.0))
    component.set_collision_enabled(unreal.CollisionEnabled.QUERY_AND_PHYSICS)
    component.set_collision_profile_name("BlockAll")
    component.set_visibility(False, True)
    component.set_editor_property("cast_shadow", False)
    actor.set_actor_hidden_in_game(True)
    placed.append({"label": actor.get_actor_label(), "location_cm": location, "dimensions_cm": dimensions})

if not unreal.EditorLoadingAndSavingUtils.save_current_level():
    raise RuntimeError("could not save sprite collision proxies")
unreal.EditorLoadingAndSavingUtils.save_dirty_packages(True, True)
after = {str(path): digest(path) for path in PROTECTED}
if after != before:
    raise RuntimeError("protected maps changed during collision proxy pass")

RECEIPT.parent.mkdir(parents=True, exist_ok=True)
RECEIPT.write_text(json.dumps({
    "status": "PASS__2126_MAJOR_SPRITES_HAVE_NATIVE_COLLISION_PROXIES",
    "map": MAP,
    "proxy_count": len(placed),
    "collision_profile": "BlockAll / QueryAndPhysics",
    "render_visibility": False,
    "proxies": placed,
    "protected_sha256_before": before,
    "protected_sha256_after": after,
}, indent=2, sort_keys=True) + "\n", encoding="utf-8")
unreal.log("PRESSSHOP_2126_SPRITE_COLLISION_PASS proxies=%d" % len(placed))
unreal.SystemLibrary.quit_editor()
