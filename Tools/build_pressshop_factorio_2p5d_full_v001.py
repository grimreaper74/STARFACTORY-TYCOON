"""Build the complete Factorio-inspired 2.5D Press Shop as an isolated map.

The map is a fixed-camera game space, not a free-camera industrial showroom.
Every large machine comes from an existing verified asset: the new S02 portal
press, the previously cleaned S03--S06 presses, coil feeder, conveyors,
inspection cell, stillages, coils and robot.  New geometry is intentionally
limited to broad painted floor zones and compact status markers.
"""
import hashlib
import json
import math
from pathlib import Path

import unreal

PROJECT = Path(r"C:\Users\greg_\Projects\LineBossCarFactory_Unreal 5.8")
ROOT = "/Game/LineBoss/Candidates/PressShop/PressShopFactorio2p5D_Full_v001"
MAP = ROOT + "/Maps/LB_PressShop_Factorio2p5D_Full_v001"
MATERIALS = ROOT + "/Materials"
REPORT = PROJECT / "Saved" / "Audits" / "PressShopIntegration" / "pressshop_factorio_2p5d_full_v001_build.json"
PROTECTED = PROJECT / "Content" / "LineBoss" / "Maps" / "LB_PressShop_BuilderAuthorityCandidate_v438.umap"
V002 = PROJECT / "Content" / "LineBoss" / "Candidates" / "PressShop" / "PressShop2126_v002" / "Maps" / "LB_PressShop_2126_Steam_v002.umap"
TAG = unreal.Name("LB.PressShop.Factorio2p5D.Full.v001")

SOURCES = {
    "S01": "/Game/LineBoss/Candidates/PressShop/MeshyCoilFeederNoCoil_v001/SM_LB_PS_InfeedCoilFeeder_NoCoil_v001",
    "S02": "/Game/LineBoss/Candidates/PressShop/S02PortalPressMeshyClean_v002/SM_LB_PS_S02_PortalPress_MeshyClean_v002",
    "S03": "/Game/LineBoss/Candidates/PressShop/SquareMeshyPressTrain_v001/SM_LB_PS_S03_Trim_MeshyClean_v001",
    "S04": "/Game/LineBoss/Candidates/PressShop/SquareMeshyPressTrain_v001/SM_LB_PS_S04_Pierce_MeshyClean_v001",
    "S05": "/Game/LineBoss/Candidates/PressShop/SquareMeshyPressTrain_v001/SM_LB_PS_S05_FlangeHem_MeshyClean_v001",
    "S06": "/Game/LineBoss/Candidates/PressShop/SquareMeshyPressTrain_v001/SM_LB_PS_S06_VisionOutfeed_MeshyClean_v001",
    "Conveyor": "/Game/LineBoss/Developer/Validation/PressTrains/CompleteTrainA_v662/Supports/SM_CA_MW_PTA_S06S07_PoweredConveyor_SupportAsset_06_v661",
    "Inspection": "/Game/LineBoss/Developer/Validation/PressTrains/CompleteTrainA_v662/Supports/SM_CA_MW_PTA_S07_InspectUnload_SupportAsset_11_v661",
    "Stillage": "/Game/LineBoss/Developer/Validation/PressTrains/CompleteTrainA_v662/Supports/SM_CA_MW_PTA_S07_FlatPanelStillage_SupportAsset_05_v661",
    "BareCoil": "/Game/LineBoss/IndustrialKit/MaterialHandling/BareCoil/Candidate_v021/SM_LB_BareMasterCoil_v021",
    "WrappedCoil": "/Game/LineBoss/IndustrialKit/MaterialHandling/MasterCoil/Candidate_v005/SM_LB_MasterCoil_Candidate_v005",
    "CoilSaddle": "/Game/LineBoss/IndustrialKit/MaterialHandling/PR003Candidate_v011/SM_LB_CoilSaddle_Candidate_v002",
    "Robot": "/Game/Meshes/Robot/SM_RoboArm04",
}
PROCESS = (
    ("S01", 0.0, "coil-free autonomous feeder"),
    ("S02", 0.0, "draw / form portal press"),
    ("S03", 90.0, "trim press"),
    ("S04", 0.0, "pierce press"),
    ("S05", 90.0, "flange / hem press"),
    ("S06", 90.0, "vision / outfeed press"),
    ("Inspection", 0.0, "inspection / unload cell"),
)


def fail(message):
    raise RuntimeError("PRESSSHOP_FACTORIO_2P5D_FULL_V001_FAIL: " + message)


def sha256(path):
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def uasset_file(path):
    return PROJECT / "Content" / (path.removeprefix("/Game/").replace("/", "\\") + ".uasset")


def srgb(hex_code):
    return tuple((int(hex_code[index:index + 2], 16) / 255.0) ** 2.2 for index in (1, 3, 5))


def aim(source, target):
    delta = target - source
    return unreal.Rotator(
        pitch=math.degrees(math.atan2(delta.z, math.sqrt(delta.x * delta.x + delta.y * delta.y))),
        yaw=math.degrees(math.atan2(delta.y, delta.x)),
        roll=0.0,
    )


def make_material(name, colour, roughness, metallic=0.0, emissive=None):
    material = unreal.AssetToolsHelpers.get_asset_tools().create_asset(name, MATERIALS, unreal.Material, unreal.MaterialFactoryNew())
    if not isinstance(material, unreal.Material):
        fail("could not create " + name)
    library = unreal.MaterialEditingLibrary
    base = library.create_material_expression(material, unreal.MaterialExpressionConstant3Vector, -380, -100)
    base.set_editor_property("constant", unreal.LinearColor(*colour, 1.0))
    rough = library.create_material_expression(material, unreal.MaterialExpressionConstant, -380, 0)
    rough.set_editor_property("r", roughness)
    metal = library.create_material_expression(material, unreal.MaterialExpressionConstant, -380, 100)
    metal.set_editor_property("r", metallic)
    library.connect_material_property(base, "", unreal.MaterialProperty.MP_BASE_COLOR)
    library.connect_material_property(rough, "", unreal.MaterialProperty.MP_ROUGHNESS)
    library.connect_material_property(metal, "", unreal.MaterialProperty.MP_METALLIC)
    if emissive is not None:
        glow = library.create_material_expression(material, unreal.MaterialExpressionConstant3Vector, -380, -195)
        glow.set_editor_property("constant", unreal.LinearColor(*emissive, 1.0))
        library.connect_material_property(glow, "", unreal.MaterialProperty.MP_EMISSIVE_COLOR)
    library.recompile_material(material)
    unreal.EditorAssetLibrary.save_loaded_asset(material, only_if_is_dirty=False)
    return material


def spawn(label, mesh, location, scale=(1.0, 1.0, 1.0), yaw=0.0, materials=None, tags=()):
    actor = unreal.EditorLevelLibrary.spawn_actor_from_class(
        unreal.StaticMeshActor, unreal.Vector(*location), unreal.Rotator(pitch=0.0, yaw=yaw, roll=0.0))
    if not isinstance(actor, unreal.StaticMeshActor):
        fail("could not spawn " + label)
    actor.set_actor_label(label)
    component = actor.static_mesh_component
    component.set_static_mesh(mesh)
    component.set_world_scale3d(unreal.Vector(*scale))
    if materials:
        for slot, material in enumerate(materials):
            component.set_material(slot, material)
    actor.tags = [TAG] + list(tags)
    return actor


def floor(label, location, dimensions, material, tags=()):
    return spawn(label, cube_mesh, location, tuple(value / 100.0 for value in dimensions), materials=(material,), tags=tags)


def projected_half_extents(mesh, yaw, scale=1.0):
    bounds = mesh.get_bounds().box_extent
    if int(abs(yaw)) % 180 == 90:
        return bounds.y * scale, bounds.x * scale, bounds.z * scale
    return bounds.x * scale, bounds.y * scale, bounds.z * scale


if unreal.EditorAssetLibrary.does_asset_exist(MAP):
    fail("target candidate already exists; refusing overwrite")
if not PROTECTED.is_file() or not V002.is_file():
    fail("protected evidence maps are missing")
protected_before = {"v438": sha256(PROTECTED), "v002": sha256(V002)}
assets, source_hashes = {}, {}
for key, path in SOURCES.items():
    asset = unreal.load_asset(path)
    if not isinstance(asset, unreal.StaticMesh):
        fail("missing required mesh " + key)
    disk = uasset_file(path)
    if not disk.is_file():
        fail("missing source package " + key)
    assets[key] = asset
    source_hashes[path] = sha256(disk)
cube_mesh = unreal.load_asset("/Engine/BasicShapes/Cube")
if not isinstance(cube_mesh, unreal.StaticMesh):
    fail("native Unreal cube is unavailable")
if not unreal.EditorLevelLibrary.new_level(MAP):
    fail("could not create the isolated full 2.5D map")

# Brand-exact broad surfaces; they are deliberately not fine stripe patterns.
warm_white = make_material("M_PS2P5DFull_WarmWhite", srgb("#F3F1E9"), 0.68, 0.03)
yellow = make_material("M_PS2P5DFull_SafetyYellow", srgb("#F2C300"), 0.44, 0.05)
red = make_material("M_PS2P5DFull_SignalRed", srgb("#C7352C"), 0.41, 0.06, (0.030, 0.004, 0.003))
steel = make_material("M_PS2P5DFull_SteelGrey", srgb("#70777C"), 0.38, 0.58)
deck = make_material("M_PS2P5DFull_WarmDeck", (0.255, 0.235, 0.205), 0.92)
zone = make_material("M_PS2P5DFull_PaleProcessZone", (0.18, 0.265, 0.22), 0.86)
bare_coil = make_material("M_PS2P5DFull_BareCoil", (0.51, 0.57, 0.61), 0.31, 0.76)
wrapped_coil = make_material("M_PS2P5DFull_WrappedCoil", (0.075, 0.085, 0.095), 0.74, 0.08)

# Place each machine from measured bounds, horizontally across the fixed view.
# The generous 7m transfer gaps make each production step readable and contain
# one reused powered conveyor without inventing filler machines.
gap = 700.0
half_x = [projected_half_extents(assets[key], yaw)[0] for key, yaw, _label in PROCESS]
line_length = sum(value * 2.0 for value in half_x) + gap * (len(PROCESS) - 1)
cursor = -line_length / 2.0
stations = []
station_data = {}
for index, ((key, yaw, display), extent_x) in enumerate(zip(PROCESS, half_x), start=1):
    x = cursor + extent_x
    extent_z = projected_half_extents(assets[key], yaw)[2]
    label = "2.5D full | %02d | %s" % (index, display)
    actor = spawn(label, assets[key], (x, 0.0, extent_z), yaw=yaw, tags=(unreal.Name("LB.Process.Flow"), unreal.Name("LB.Reused.VerifiedAsset")))
    station_data[key] = {"x": x, "half_x": extent_x, "half_z": extent_z, "label": label}
    stations.append({"role": key, "actor": label, "location_cm": [round(x, 2), 0.0, round(extent_z, 2)], "yaw": yaw})
    cursor = x + extent_x + gap

# Exact half-width arithmetic keeps the reused conveyors in the deliberate
# transfer gaps.  There is one at every stage boundary, not a forest of rails.
conveyor_z = assets["Conveyor"].get_bounds().box_extent.z
for index, ((left_key, _left_yaw, _), (right_key, _right_yaw, _)) in enumerate(zip(PROCESS, PROCESS[1:]), start=1):
    left, right = station_data[left_key], station_data[right_key]
    x = (left["x"] + left["half_x"] + right["x"] - right["half_x"]) / 2.0
    actor = spawn("2.5D full | transfer conveyor %02d" % index, assets["Conveyor"], (x, 0.0, conveyor_z), (1.16, 0.82, 0.82), tags=(unreal.Name("LB.Process.Transfer"), unreal.Name("LB.Reused.Conveyor")))
    stations.append({"role": "transfer_conveyor", "actor": actor.get_actor_label(), "location_cm": [round(x, 2), 0.0, round(conveyor_z, 2)]})

# Material supply is intentionally a visible system, but coils remain their
# own assets rather than being duplicated inside a generated press or feeder.
feeder = station_data["S01"]
bare_scale = 1.65
bare_z = assets["BareCoil"].get_bounds().box_extent.z * bare_scale
spawn("2.5D full | active bare master coil", assets["BareCoil"], (feeder["x"] - feeder["half_x"] - 430.0, 0.0, bare_z), (bare_scale, bare_scale, bare_scale), 90.0, (bare_coil,), (unreal.Name("LB.Material.ActiveCoil"),))
saddle_z = assets["CoilSaddle"].get_bounds().box_extent.z
reserve_x = feeder["x"] - feeder["half_x"] + 320.0
spawn("2.5D full | wrapped reserve coil saddle", assets["CoilSaddle"], (reserve_x, 1550.0, saddle_z), tags=(unreal.Name("LB.Material.CoilReserve"),))
reserve_scale = 1.42
reserve_z = saddle_z * 2.0 + assets["WrappedCoil"].get_bounds().box_extent.z * reserve_scale
spawn("2.5D full | wrapped reserve coil", assets["WrappedCoil"], (reserve_x, 1550.0, reserve_z), (reserve_scale, reserve_scale, reserve_scale), 90.0, (wrapped_coil,), (unreal.Name("LB.Material.CoilReserve"),))

# Robots show the future automation story.  They are fixed plant arms, not
# forklifts, AGVs or any wheeled vehicle.
for index, key in enumerate(("S02", "S03", "S04", "S05", "S06"), start=1):
    station = station_data[key]
    side = 1800.0 if index % 2 else -1800.0
    actor = spawn("2.5D full | robotic tender %02d" % index, assets["Robot"], (station["x"], side, 0.0), (1.35, 1.35, 1.35), -90.0 if side > 0 else 90.0, (steel,), (unreal.Name("LB.Automation.Robot"), unreal.Name("LB.NoWheels")))
    stations.append({"role": "robot_tender", "actor": actor.get_actor_label()})

# Inspection output has two staged panel stillages, visible from the overview.
inspection = station_data["Inspection"]
stillage_z = assets["Stillage"].get_bounds().box_extent.z
for index, y in enumerate((-1500.0, 1500.0), start=1):
    spawn("2.5D full | finished panel stillage %02d" % index, assets["Stillage"], (inspection["x"] + inspection["half_x"] + 430.0, y, stillage_z), tags=(unreal.Name("LB.Process.FinishedParts"), unreal.Name("LB.Reused.Stillage")))

# Broad colour blocks turn the line into an immediately readable factory map.
deck_length = line_length + 4200.0
floor("2.5D full | warm works deck", (0.0, 0.0, -100.0), (deck_length, 4700.0, 200.0), deck, (unreal.Name("LB.Architecture.Deck"),))
floor("2.5D full | pale-green automation zone", (0.0, 0.0, 8.0), (line_length + 2300.0, 3200.0, 30.0), zone, (unreal.Name("LB.Process.Zone"),))
floor("2.5D full | cream operator avenue", (0.0, -1900.0, 16.0), (deck_length - 700.0, 540.0, 34.0), warm_white, (unreal.Name("LB.Operator.Route"),))
floor("2.5D full | safety datum", (0.0, -1580.0, 36.0), (line_length + 2200.0, 70.0, 42.0), yellow, (unreal.Name("LB.Safety.Datum"),))

# One status marker per process station keeps progress-state information clear
# at game scale without adding signage, wires, hose runs or micro-railings.
for index, key in enumerate(("S01", "S02", "S03", "S04", "S05", "S06", "Inspection"), start=1):
    x = station_data[key]["x"]
    floor("2.5D full | status beacon %02d" % index, (x, 1250.0, 80.0), (82.0, 82.0, 160.0), red, (unreal.Name("LB.Automation.Status"),))

# The main game camera is genuinely orthographic.  A closer camera exists for
# UI/inspection use but the world is designed to succeed from the overview.
overview_source = unreal.Vector(-line_length * 0.57, -10500.0, 12600.0)
overview_target = unreal.Vector(0.0, 0.0, 180.0)
overview = unreal.EditorLevelLibrary.spawn_actor_from_class(unreal.CameraActor, overview_source, aim(overview_source, overview_target))
if not isinstance(overview, unreal.CameraActor):
    fail("could not create overview camera")
overview.set_actor_label("CAM | 2.5D full Press Shop overview")
overview_component = overview.get_editor_property("camera_component")
overview_component.set_editor_property("projection_mode", unreal.CameraProjectionMode.ORTHOGRAPHIC)
overview_component.set_editor_property("ortho_width", deck_length + 1200.0)
overview.tags = [TAG, unreal.Name("LB.GameplayCamera.FixedIsometric"), unreal.Name("LB.SteamReviewCamera")]

s02_x = station_data["S02"]["x"]
detail_source = unreal.Vector(s02_x - 3300.0, -5600.0, 5200.0)
detail_target = unreal.Vector(s02_x, 0.0, 260.0)
detail = unreal.EditorLevelLibrary.spawn_actor_from_class(unreal.CameraActor, detail_source, aim(detail_source, detail_target))
if not isinstance(detail, unreal.CameraActor):
    fail("could not create S02 camera")
detail.set_actor_label("CAM | 2.5D draw-form and coil detail")
detail_component = detail.get_editor_property("camera_component")
detail_component.set_editor_property("projection_mode", unreal.CameraProjectionMode.ORTHOGRAPHIC)
detail_component.set_editor_property("ortho_width", 4800.0)
detail.tags = [TAG, unreal.Name("LB.GameplayCamera.FixedIsometric"), unreal.Name("LB.SteamReviewCamera")]

# Simple, non-geometric high-key lighting: no roof/ceiling grid is introduced.
# This is the presentation calibration for the new 2.5D direction, distinct
# from the old free-camera open-air B_stylized candidate.
sun = unreal.EditorLevelLibrary.spawn_actor_from_class(unreal.DirectionalLight, unreal.Vector(0.0, 0.0, 12000.0), unreal.Rotator(pitch=-48.0, yaw=-35.0, roll=0.0))
sun.set_actor_label("2.5D full | broad key sun")
sun.light_component.set_editor_property("mobility", unreal.ComponentMobility.MOVABLE)
sun.light_component.set_editor_property("intensity", 4.5)
sun.light_component.set_editor_property("use_temperature", True)
sun.light_component.set_editor_property("temperature", 5300.0)
sun.tags = [TAG, unreal.Name("LB.Visual.2P5D")]
sky = unreal.EditorLevelLibrary.spawn_actor_from_class(unreal.SkyLight, unreal.Vector(0.0, 0.0, 12000.0), unreal.Rotator())
sky.set_actor_label("2.5D full | broad fill sky")
sky.light_component.set_editor_property("mobility", unreal.ComponentMobility.MOVABLE)
sky.light_component.set_editor_property("intensity", 3.0)
sky.light_component.set_editor_property("real_time_capture", True)
sky.tags = [TAG, unreal.Name("LB.Visual.2P5D")]
post = unreal.EditorLevelLibrary.spawn_actor_from_class(unreal.PostProcessVolume, unreal.Vector(), unreal.Rotator())
post.set_actor_label("2.5D full | fixed readable exposure")
post.set_editor_property("unbound", True)
settings = post.get_editor_property("settings")
settings.override_auto_exposure_bias = True
settings.auto_exposure_bias = 0.0
post.set_editor_property("settings", settings)
post.tags = [TAG, unreal.Name("LB.Visual.2P5D")]

if any(unreal.Name("LB.Architecture.Roof") in actor.tags for actor in unreal.EditorLevelLibrary.get_all_level_actors()):
    fail("roof actor found in explicitly roofless full 2.5D candidate")
if not unreal.EditorLevelLibrary.save_current_level():
    fail("could not save complete 2.5D candidate")
for path, expected in source_hashes.items():
    if sha256(uasset_file(path)) != expected:
        fail("source asset changed during candidate build: " + path)
protected_after = {"v438": sha256(PROTECTED), "v002": sha256(V002)}
if protected_after != protected_before:
    fail("a protected map changed during candidate build")

REPORT.parent.mkdir(parents=True, exist_ok=True)
REPORT.write_text(json.dumps({
    "status": "PASS__COMPLETE_FACTORIO_INSPIRED_2P5D_PRESS_SHOP_CANDIDATE_BUILT",
    "candidate_map": MAP,
    "camera_mode": "orthographic fixed isometric",
    "process_sequence": [display for _key, _yaw, display in PROCESS],
    "line_length_cm": round(line_length, 2),
    "transfer_gap_cm": gap,
    "placed": stations,
    "new_large_machine_geometry": 0,
    "new_native_geometry_scope": "broad deck, broad zones, operator avenue, safety datum, status markers only",
    "roof_created": False,
    "wheeled_vehicles_created": False,
    "source_uasset_sha256": source_hashes,
    "protected_hashes_before": protected_before,
    "protected_hashes_after": protected_after,
    "honest_status": "candidate assembled and source-validated; full-line screenshot review remains required",
}, indent=2, sort_keys=True) + "\n", encoding="utf-8")
unreal.log("PRESSSHOP_FACTORIO_2P5D_FULL_V001_PASS map=" + MAP)
