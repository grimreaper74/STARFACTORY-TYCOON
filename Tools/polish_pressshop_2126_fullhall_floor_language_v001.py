"""Add large, management-camera-readable process zoning to FullHall v001.

This is deliberately macro dressing: four painted process fields, clean yellow
edge datums and three directional magnetic-flow glyphs.  It avoids the dense
micro-railings/cable clutter rejected by the visual authority.
"""
import hashlib
import json
from pathlib import Path

import unreal


PROJECT = Path(r"C:\Users\greg_\Projects\LineBossCarFactory_Unreal 5.8")
MAP = "/Game/LineBoss/Candidates/PressShop/PressShop2126_FullHall_v001/Maps/LB_PressShop_2126_FullHall_v001"
RECEIPT = PROJECT / "Saved" / "Audits" / "PressShop2126" / "fullhall_floor_language_v001_receipt.json"
TAG = unreal.Name("LB.PressShop.2126.FloorLanguage.v001")
ZONE = "/Game/LineBoss/Candidates/PressShop/PressShop2126_v003/Materials/M_LB_PS2126v003_PaleGreenZone"
YELLOW = "/Game/LineBoss/Candidates/PressShop/PressShop2126_v003/Materials/M_LB_PS2126v003_SafetyYellow"
WARM_WHITE = "/Game/LineBoss/Candidates/PressShop/PressShop2126_v003/Materials/M_LB_PS2126v003_WarmWhite"
PROTECTED = {
    PROJECT / "Content" / "LineBoss" / "Maps" / "LB_PressShop_BuilderAuthorityCandidate_v438.umap": "5029c9d827d9a1d72c12f27ee757c9bc1e47febd5006ce6d7ba319aad2e7fec8",
    PROJECT / "Content" / "LineBoss" / "Candidates" / "PressShop" / "PressShop2126_v002" / "Maps" / "LB_PressShop_2126_Steam_v002.umap": "cc09cf46d33e8a562d97f5a3bc35a5b42c9582d8e4650cf315694ebf340e4aa0",
}


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest().lower()


def spawn(label, location, dimensions, material, yaw=0.0, role="ProcessZone"):
    actor = unreal.EditorLevelLibrary.spawn_actor_from_class(
        unreal.StaticMeshActor, unreal.Vector(*location), unreal.Rotator(0.0, yaw, 0.0))
    if actor is None:
        raise RuntimeError("could not spawn " + label)
    actor.set_actor_label(label)
    actor.tags = [TAG, unreal.Name("LB.PressShop.2126.Architecture"), unreal.Name("LB.Role." + role)]
    actor.static_mesh_component.set_static_mesh(cube)
    actor.set_actor_scale3d(unreal.Vector(
        dimensions[0] / 100.0, dimensions[1] / 100.0, dimensions[2] / 100.0))
    actor.static_mesh_component.set_material(0, material)
    actor.static_mesh_component.set_collision_enabled(unreal.CollisionEnabled.NO_COLLISION)
    actor.static_mesh_component.set_editor_property("cast_shadow", False)
    return actor


def outline(name, center, dimensions):
    x, y = center
    width, length = dimensions
    thickness = 18.0
    z = 8.0
    labels = []
    labels.append(spawn(f"2126 FLOOR | {name} yellow edge west", (x - width / 2, y, z),
                        (thickness, length, 3.0), yellow, role="SafetyDatum").get_actor_label())
    labels.append(spawn(f"2126 FLOOR | {name} yellow edge east", (x + width / 2, y, z),
                        (thickness, length, 3.0), yellow, role="SafetyDatum").get_actor_label())
    labels.append(spawn(f"2126 FLOOR | {name} yellow edge south", (x, y - length / 2, z),
                        (width, thickness, 3.0), yellow, role="SafetyDatum").get_actor_label())
    labels.append(spawn(f"2126 FLOOR | {name} yellow edge north", (x, y + length / 2, z),
                        (width, thickness, 3.0), yellow, role="SafetyDatum").get_actor_label())
    return labels


def arrow(name, center, direction):
    x, y = center
    z = 10.0
    labels = []
    if direction == "+Y":
        labels.append(spawn(f"2126 FLOOR | {name} flow arrow shaft", (x, y, z),
                            (30.0, 250.0, 2.0), warm_white, role="FlowGlyph").get_actor_label())
        labels.append(spawn(f"2126 FLOOR | {name} flow arrow head west", (x - 43.0, y + 112.0, z),
                            (24.0, 125.0, 2.0), warm_white, 45.0, "FlowGlyph").get_actor_label())
        labels.append(spawn(f"2126 FLOOR | {name} flow arrow head east", (x + 43.0, y + 112.0, z),
                            (24.0, 125.0, 2.0), warm_white, -45.0, "FlowGlyph").get_actor_label())
    elif direction == "+X":
        labels.append(spawn(f"2126 FLOOR | {name} flow arrow shaft", (x, y, z),
                            (250.0, 30.0, 2.0), warm_white, role="FlowGlyph").get_actor_label())
        labels.append(spawn(f"2126 FLOOR | {name} flow arrow head north", (x + 112.0, y + 43.0, z),
                            (125.0, 24.0, 2.0), warm_white, -45.0, "FlowGlyph").get_actor_label())
        labels.append(spawn(f"2126 FLOOR | {name} flow arrow head south", (x + 112.0, y - 43.0, z),
                            (125.0, 24.0, 2.0), warm_white, 45.0, "FlowGlyph").get_actor_label())
    else:
        raise RuntimeError("unsupported arrow direction")
    return labels


before = {str(path): digest(path) for path in PROTECTED}
for path, expected in PROTECTED.items():
    if before[str(path)] != expected:
        raise RuntimeError("protected map missing or changed: " + str(path))
if not unreal.EditorLoadingAndSavingUtils.load_map(MAP):
    raise RuntimeError("could not load isolated FullHall candidate")
actors = list(unreal.EditorLevelLibrary.get_all_level_actors())
if any(TAG in actor.tags for actor in actors):
    raise RuntimeError("floor-language pass already exists")

required = {
    "2126 LOG | autonomous coil delivery carrier",
    "2126 COIL | autonomous verification and de-banding cell",
    "2126 FRONT END | autonomous decoiler straightener and servo feed",
    "2126 PRESS | S01 autonomous deep-draw servo press",
    "2126 OUTBOUND | AI inspection and metrology cell",
    "2126 OUTBOUND | robotic finished-panel palletisation cell",
}
labels = {actor.get_actor_label() for actor in actors}
missing = sorted(required - labels)
if missing:
    raise RuntimeError("production flow incomplete; refusing cosmetic zoning: " + repr(missing))

cube = unreal.load_asset("/Engine/BasicShapes/Cube.Cube")
zone = unreal.load_asset(ZONE)
yellow = unreal.load_asset(YELLOW)
warm_white = unreal.load_asset(WARM_WHITE)
if not isinstance(cube, unreal.StaticMesh):
    raise RuntimeError("native cube missing")
if not all(isinstance(material, unreal.MaterialInterface) for material in (zone, yellow, warm_white)):
    raise RuntimeError("brand floor materials missing")

created = []
fields = [
    ("raw-coil receiving bay", (-8800.0, -2200.0), (2600.0, 3300.0)),
    ("coil verification buffer bay", (-6600.0, -2450.0), (1900.0, 3900.0)),
    ("servo feed bay", (-4550.0, -1900.0), (1900.0, 2200.0)),
    ("vision palletisation bay", (850.0, 4495.0), (4500.0, 2300.0)),
]
for name, center, dimensions in fields:
    created.append(spawn(f"2126 FLOOR | {name} pale-green field", (center[0], center[1], 3.0),
                         (dimensions[0], dimensions[1], 4.0), zone).get_actor_label())
    created.extend(outline(name, center, dimensions))

# Broad, repeated white flow glyphs read from the fixed management camera and
# make the 90-degree turn into dispatch unambiguous.
created.extend(arrow("inbound receiving", (-9800.0, -2900.0), "+Y"))
created.extend(arrow("press transfer", (-5350.0, 950.0), "+Y"))
created.extend(arrow("dispatch turn", (5200.0, 3600.0), "+X"))

if not unreal.EditorLoadingAndSavingUtils.save_current_level():
    raise RuntimeError("could not save floor-language pass")
unreal.EditorLoadingAndSavingUtils.save_dirty_packages(True, True)
after = {str(path): digest(path) for path in PROTECTED}
if after != before:
    raise RuntimeError("protected maps changed during floor-language pass")

RECEIPT.parent.mkdir(parents=True, exist_ok=True)
RECEIPT.write_text(json.dumps({
    "status": "PASS__2126_MACRO_PROCESS_ZONES_AND_FLOW_GLYPHS_ADDED",
    "map": MAP,
    "created_count": len(created),
    "created": created,
    "process_field_count": len(fields),
    "flow_arrow_count": 3,
    "roof_created": False,
    "micro_clutter_added": False,
    "protected_sha256_before": before,
    "protected_sha256_after": after,
}, indent=2, sort_keys=True) + "\n", encoding="utf-8")
unreal.log("PRESSSHOP_2126_FLOOR_LANGUAGE_PASS receipt=" + str(RECEIPT))
unreal.SystemLibrary.quit_editor()
