"""Replace only the abstract press placeholders in the fresh 2126 candidate.

This is a non-destructive presentation correction: the original native-Unreal
blockouts are hidden and tagged as superseded rather than deleted.  The map is
still the fresh 2126 candidate; its open deck, project coils, laser blanker,
lighting and structural bay remain in place.  Five existing, cleaned Meshy
press assets become the visible manufacturing line.
"""
import json
import math
from pathlib import Path

import unreal

PROJECT = Path(r"C:\Users\greg_\Projects\LineBossCarFactory_Unreal 5.8")
MAP = "/Game/LineBoss/Candidates/PressShop/PressShop2126_v001/Maps/LB_PressShop_2126_Steam_v001"
ROOT = "/Game/LineBoss/Candidates/PressShop/SquareMeshyPressTrain_v001"
MATERIAL_ROOT = "/Game/LineBoss/Candidates/PressShop/PressShop2126_v001/Materials"
REPORT = PROJECT / "Saved" / "Audits" / "PressShopIntegration" / "pressshop_2126_meshy_replacement_v001.json"
BUILD_TAG = unreal.Name("LB.PressShop.2126.MeshyReplacement.v001")
REUSED_TAG = unreal.Name("LB.Asset.Reused.MeshyClean")
SUPERSEDED_TAG = unreal.Name("LB.PressShop.2126.NativeBlockout.Hidden")

PRESSES = (
    ("S02 Draw / form", "SM_LB_PS_S02_DrawForm_MeshyClean_v001", -2000.0, 0.0),
    ("S03 Trim", "SM_LB_PS_S03_Trim_MeshyClean_v001", 14000.0, 90.0),
    ("S04 Pierce", "SM_LB_PS_S04_Pierce_MeshyClean_v001", 28500.0, 0.0),
    ("S05 Flange / hem", "SM_LB_PS_S05_FlangeHem_MeshyClean_v001", 42500.0, 90.0),
    ("S06 Vision / outfeed", "SM_LB_PS_S06_VisionOutfeed_MeshyClean_v001", 56000.0, 90.0),
)

OLD_LABEL_PREFIXES = (
    "S02 Draw Nexus |", "S03 Trim Array |", "S04 Pierce Cell |", "S05 Edge Forge |",
    "S02 | Draw |", "S03 | Trim |", "S04 | Pierce |", "S05 | Edge |",
    "S06 | vision", "S06 | autonomous", "S06 | optical",
    "S02-S05 | overhead transfer", "transfer | ",
    "2126 | pale green process zone ", "2126 | cream operator avenue", "2126 | cream service avenue",
)


def fail(message):
    raise RuntimeError("PRESSSHOP_2126_MESHY_REPLACEMENT_FAIL: " + message)


def aim(source, target):
    dx, dy, dz = target.x - source.x, target.y - source.y, target.z - source.z
    flat = math.sqrt(dx * dx + dy * dy)
    return unreal.Rotator(
        pitch=math.degrees(math.atan2(dz, flat)),
        yaw=math.degrees(math.atan2(dy, dx)),
        roll=0.0,
    )


def bounds_dimensions(mesh):
    box = mesh.get_bounding_box()
    return box, (box.max.x - box.min.x, box.max.y - box.min.y, box.max.z - box.min.z)


def hide_placeholder(actor):
    """Preserve provenance while removing the abstract form from the review view."""
    actor.set_actor_hidden_in_game(True)
    actor.tags = list(actor.tags) + [SUPERSEDED_TAG]
    for component in actor.get_components_by_class(unreal.PrimitiveComponent):
        component.set_visibility(False, True)


def spawn_cube(label, location, dimensions, material, tags=()):
    cube = unreal.load_asset("/Engine/BasicShapes/Cube")
    if not isinstance(cube, unreal.StaticMesh):
        fail("native Unreal cube unavailable")
    actor = unreal.EditorLevelLibrary.spawn_actor_from_class(unreal.StaticMeshActor, unreal.Vector(*location), unreal.Rotator())
    if actor is None:
        fail("could not spawn " + label)
    actor.set_actor_label(label)
    actor.tags = [BUILD_TAG] + list(tags)
    component = actor.static_mesh_component
    component.set_static_mesh(cube)
    component.set_world_scale3d(unreal.Vector(dimensions[0] / 100.0, dimensions[1] / 100.0, dimensions[2] / 100.0))
    component.set_material(0, material)
    return actor


if not unreal.EditorAssetLibrary.does_asset_exist(MAP):
    fail("fresh 2126 candidate map is missing")
if not unreal.EditorLoadingAndSavingUtils.load_map(MAP):
    fail("could not load fresh 2126 candidate map")

actors = list(unreal.EditorLevelLibrary.get_all_level_actors())
if any(BUILD_TAG in actor.tags for actor in actors):
    fail("replacement tag already exists; refusing duplicate Meshy placements")

# Hide the deliberately abstract first-pass machinery. This avoids deleting
# user-visible candidate history and cleanly proves what replaced it.
hidden = []
for actor in actors:
    label = actor.get_actor_label()
    if any(label.startswith(prefix) for prefix in OLD_LABEL_PREFIXES):
        hide_placeholder(actor)
        hidden.append(label)

if not hidden:
    fail("could not find the primitive first-pass press actors to supersede")

floor = unreal.load_asset(MATERIAL_ROOT + "/M_LB_PS2126_Floor")
pale_green = unreal.load_asset(MATERIAL_ROOT + "/M_LB_PS2126_PaintedPaleGreen")
cream = unreal.load_asset(MATERIAL_ROOT + "/M_LB_PS2126_CreamLane")
steel = unreal.load_asset(MATERIAL_ROOT + "/M_LB_PS2126_SteelGrey")
yellow = unreal.load_asset(MATERIAL_ROOT + "/M_LB_PS2126_SafetyYellow")
if not all(isinstance(item, unreal.Material) for item in (floor, pale_green, cream, steel, yellow)):
    fail("the native materials created by the fresh candidate are unavailable")

# Extend the open deck, coloured work zones, access lanes and sparse roofless
# gantry so the real machines get credible working clearance instead of being
# squeezed into the smaller blockout pitch.
spawn_cube("2126 | Meshy line deck extension", (44500.0, 0.0, -80.0), (36000.0, 16800.0, 160.0), floor, (unreal.Name("LB.PressShop.DeckExtension"),))
spawn_cube("2126 | Meshy line operator avenue", (44500.0, -5200.0, 18.0), (36000.0, 1350.0, 36.0), cream, (unreal.Name("LB.PressShop.Access"),))
spawn_cube("2126 | Meshy line service avenue", (44500.0, 5200.0, 18.0), (36000.0, 1000.0, 36.0), cream, (unreal.Name("LB.PressShop.Access"),))
for label, _, x, _ in PRESSES:
    spawn_cube("2126 | Meshy process zone | " + label, (x, 0.0, 8.0), (11200.0, 7600.0, 28.0), pale_green, (unreal.Name("LB.PressShop.ProcessZone"),))
    spawn_cube("2126 | station slab | " + label, (x, -4300.0, 18.0), (4200.0, 460.0, 36.0), yellow, (unreal.Name("LB.PressShop.StationID"),))

for x in (30000.0, 36000.0, 42000.0, 48000.0, 54000.0, 60000.0):
    for y in (-7600.0, 7600.0):
        spawn_cube("2126 | Meshy line open-bay mast %.0f %.0f" % (x, y), (x, y, 4900.0), (340.0, 340.0, 9800.0), steel, (unreal.Name("LB.PressShop.OpenStructure"),))
        spawn_cube("2126 | Meshy line mast safety base %.0f %.0f" % (x, y), (x, y, 220.0), (620.0, 620.0, 180.0), yellow, (unreal.Name("LB.PressShop.OpenStructure"),))
for y in (-7600.0, 7600.0):
    spawn_cube("2126 | Meshy line gantry rail %.0f" % y, (44300.0, y, 9200.0), (37000.0, 260.0, 260.0), steel, (unreal.Name("LB.PressShop.OpenStructure"),))

placed = []
for label, asset_name, x, yaw in PRESSES:
    mesh = unreal.load_asset(ROOT + "/" + asset_name)
    if not isinstance(mesh, unreal.StaticMesh):
        fail("missing cleaned Meshy press " + asset_name)
    box, dimensions = bounds_dimensions(mesh)
    actor = unreal.EditorLevelLibrary.spawn_actor_from_class(
        unreal.StaticMeshActor, unreal.Vector(x, 0.0, -box.min.z), unreal.Rotator(pitch=0.0, yaw=yaw, roll=0.0))
    if actor is None:
        fail("could not place " + label)
    actor.set_actor_label("MESHY | " + label + " | reused press asset")
    actor.tags = [BUILD_TAG, REUSED_TAG, unreal.Name("LB.PressShop.2126." + label.replace(" ", ""))]
    component = actor.static_mesh_component
    component.set_static_mesh(mesh)
    component.set_mobility(unreal.ComponentMobility.STATIC)
    placed.append({
        "station": label,
        "asset": mesh.get_path_name(),
        "location_cm": [round(x, 2), 0.0, round(-box.min.z, 2)],
        "yaw": yaw,
        "dimensions_cm": [round(value, 2) for value in dimensions],
        "triangles_lod0": int(mesh.get_num_triangles(0)),
    })

# Native Unreal continues to do what it is best for here: controlled lighting,
# composition and a sparse future-factory envelope. No new Meshy generation or
# API spend has occurred in this correction.
for camera in unreal.EditorLevelLibrary.get_all_level_actors():
    label = camera.get_actor_label()
    if label == "CAM | 2126 Steam hero overview":
        location = unreal.Vector(17000.0, -30500.0, 13000.0)
        target = unreal.Vector(27500.0, 0.0, 2300.0)
        camera.set_actor_location(location, False, False)
        camera.set_actor_rotation(aim(location, target), False)
        camera.get_cine_camera_component().set_editor_property("current_focal_length", 34.0)
    elif label == "CAM | 2126 operator line":
        location = unreal.Vector(13500.0, -21500.0, 5700.0)
        target = unreal.Vector(22000.0, 0.0, 2400.0)
        camera.set_actor_location(location, False, False)
        camera.set_actor_rotation(aim(location, target), False)
        camera.get_cine_camera_component().set_editor_property("current_focal_length", 42.0)
    elif label == "CAM | 2126 draw nexus":
        location = unreal.Vector(-9500.0, -15000.0, 5000.0)
        target = unreal.Vector(-2000.0, 0.0, 2600.0)
        camera.set_actor_location(location, False, False)
        camera.set_actor_rotation(aim(location, target), False)
        camera.get_cine_camera_component().set_editor_property("current_focal_length", 45.0)

hero_location = unreal.Vector(13500.0, -21500.0, 5700.0)
hero_target = unreal.Vector(22000.0, 0.0, 2400.0)
unreal.EditorLevelLibrary.set_level_viewport_camera_info(hero_location, aim(hero_location, hero_target))

if not unreal.EditorLevelLibrary.save_current_level():
    fail("could not save the corrected 2126 candidate map")

REPORT.parent.mkdir(parents=True, exist_ok=True)
REPORT.write_text(json.dumps({
    "status": "PASS__FRESH_2126_CANDIDATE_NOW_USES_REUSED_CLEANED_MESHY_PRESS_ASSETS",
    "map": MAP,
    "candidate_only": True,
    "meshy_api_calls": 0,
    "meshy_policy": "Reused five existing cleaned Meshy assets already present in the project. No new generation, upload or API credit spend.",
    "native_unreal_role": "new-map layout, non-destructive placeholder hiding, materials, lighting envelope, camera framing and saved candidate-map integration",
    "hidden_not_deleted_first_pass_actor_count": len(hidden),
    "hidden_not_deleted_first_pass_labels": hidden,
    "reused_meshy_presses": placed,
    "no_embedded_coil_policy": "The imported asset receipt documents no coils in these press meshes; the project wrapped and bare coils remain separate actors.",
    "honest_status": "visual candidate map only; no gameplay, collision, navigation, packaged build, performance or Steam-release claim",
}, indent=2), encoding="utf-8")
unreal.log("PRESSSHOP_2126_MESHY_REPLACEMENT_PASS: hidden=%d reused=%d" % (len(hidden), len(placed)))
