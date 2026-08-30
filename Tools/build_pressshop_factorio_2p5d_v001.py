"""Build an isolated Factorio-inspired 2.5D press-cell proof in Unreal.

This is deliberately *not* a conversion of the existing free-camera press
shop.  It is a clean, reversible candidate intended to answer one question:
can the new square S02 press, the separately-authored coils, and one simple
robotic flow read immediately from a fixed isometric gameplay camera?

Only the map and materials beneath the candidate root are created.  The
authoritative v438 map, the earlier v002 candidate, and all source meshes are
hashed before and after the build and must remain byte-identical.
"""
import hashlib
import json
import math
from pathlib import Path

import unreal


PROJECT = Path(r"C:\Users\greg_\Projects\LineBossCarFactory_Unreal 5.8")
ROOT = "/Game/LineBoss/Candidates/PressShop/PressShopFactorio2p5D_v003"
MAP = ROOT + "/Maps/LB_PressShop_Factorio2p5D_v003"
MATERIALS = ROOT + "/Materials"
REPORT = PROJECT / "Saved" / "Audits" / "PressShopIntegration" / "pressshop_factorio_2p5d_v003_build.json"
PROTECTED = PROJECT / "Content" / "LineBoss" / "Maps" / "LB_PressShop_BuilderAuthorityCandidate_v438.umap"
V002 = PROJECT / "Content" / "LineBoss" / "Candidates" / "PressShop" / "PressShop2126_v002" / "Maps" / "LB_PressShop_2126_Steam_v002.umap"
TAG = unreal.Name("LB.PressShop.Factorio2p5D.v003")

SOURCES = {
    "PortalPress": "/Game/LineBoss/Candidates/PressShop/S02PortalPressMeshyClean_v002/SM_LB_PS_S02_PortalPress_MeshyClean_v002",
    "Conveyor": "/Game/LineBoss/Developer/Validation/PressTrains/CompleteTrainA_v662/Supports/SM_CA_MW_PTA_S06S07_PoweredConveyor_SupportAsset_06_v661",
    "BareCoil": "/Game/LineBoss/IndustrialKit/MaterialHandling/BareCoil/Candidate_v021/SM_LB_BareMasterCoil_v021",
    "WrappedCoil": "/Game/LineBoss/IndustrialKit/MaterialHandling/MasterCoil/Candidate_v005/SM_LB_MasterCoil_Candidate_v005",
    "CoilSaddle": "/Game/LineBoss/IndustrialKit/MaterialHandling/PR003Candidate_v011/SM_LB_CoilSaddle_Candidate_v002",
    "Robot": "/Game/Meshes/Robot/SM_RoboArm04",
}


def fail(message):
    raise RuntimeError("PRESSSHOP_FACTORIO_2P5D_V001_FAIL: " + message)


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
    dx, dy, dz = target.x - source.x, target.y - source.y, target.z - source.z
    return unreal.Rotator(
        roll=0.0,
        pitch=math.degrees(math.atan2(dz, math.sqrt(dx * dx + dy * dy))),
        yaw=math.degrees(math.atan2(dy, dx)),
    )


def make_material(name, colour, roughness, metallic=0.0, emissive=None):
    material = unreal.AssetToolsHelpers.get_asset_tools().create_asset(
        name, MATERIALS, unreal.Material, unreal.MaterialFactoryNew())
    if not isinstance(material, unreal.Material):
        fail("could not create material " + name)
    library = unreal.MaterialEditingLibrary
    base = library.create_material_expression(material, unreal.MaterialExpressionConstant3Vector, -400, -120)
    base.set_editor_property("constant", unreal.LinearColor(*colour, 1.0))
    rough = library.create_material_expression(material, unreal.MaterialExpressionConstant, -400, -15)
    rough.set_editor_property("r", roughness)
    metal = library.create_material_expression(material, unreal.MaterialExpressionConstant, -400, 90)
    metal.set_editor_property("r", metallic)
    library.connect_material_property(base, "", unreal.MaterialProperty.MP_BASE_COLOR)
    library.connect_material_property(rough, "", unreal.MaterialProperty.MP_ROUGHNESS)
    library.connect_material_property(metal, "", unreal.MaterialProperty.MP_METALLIC)
    if emissive is not None:
        glow = library.create_material_expression(material, unreal.MaterialExpressionConstant3Vector, -400, -225)
        glow.set_editor_property("constant", unreal.LinearColor(*emissive, 1.0))
        library.connect_material_property(glow, "", unreal.MaterialProperty.MP_EMISSIVE_COLOR)
    library.recompile_material(material)
    unreal.EditorAssetLibrary.save_loaded_asset(material, only_if_is_dirty=False)
    return material


def spawn(label, mesh, location, scale=(1.0, 1.0, 1.0), yaw=0.0, materials=None, extra_tags=()):
    actor = unreal.EditorLevelLibrary.spawn_actor_from_class(
        unreal.StaticMeshActor, unreal.Vector(*location), unreal.Rotator(roll=0.0, pitch=0.0, yaw=yaw))
    if not isinstance(actor, unreal.StaticMeshActor):
        fail("could not spawn " + label)
    actor.set_actor_label(label)
    component = actor.static_mesh_component
    component.set_static_mesh(mesh)
    component.set_world_scale3d(unreal.Vector(*scale))
    if materials:
        for slot, material in enumerate(materials):
            component.set_material(slot, material)
    actor.tags = [TAG] + list(extra_tags)
    return actor


def floor_block(label, location, dimensions_cm, material, extra_tags=()):
    return spawn(
        label, cube_mesh, location,
        tuple(value / 100.0 for value in dimensions_cm),
        materials=(material,), extra_tags=extra_tags)


def base_z(mesh, scale=1.0):
    return mesh.get_bounds().box_extent.z * scale


if unreal.EditorAssetLibrary.does_asset_exist(MAP):
    fail("candidate already exists; refusing overwrite")
if not PROTECTED.is_file() or not V002.is_file():
    fail("protected map evidence is missing")
protected_before, v002_before = sha256(PROTECTED), sha256(V002)

assets = {}
source_hashes = {}
for role, path in SOURCES.items():
    asset = unreal.load_asset(path)
    if not isinstance(asset, unreal.StaticMesh):
        fail("required mesh is unavailable: " + role)
    source_path = uasset_file(path)
    if not source_path.is_file():
        fail("required source package is unavailable: " + str(source_path))
    assets[role] = asset
    source_hashes[path] = sha256(source_path)
cube_mesh = unreal.load_asset("/Engine/BasicShapes/Cube")
if not isinstance(cube_mesh, unreal.StaticMesh):
    fail("native Unreal cube is unavailable")

# A new map avoids inheriting the older, free-camera scene and gives this test
# a stable visual contract: broad floor zones, no roof, no columns, no stripe
# forests, no wheeled vehicles and no blue/cyan machine repaint.
if not unreal.EditorLevelLibrary.new_level(MAP):
    fail("could not create isolated candidate map")

# Exact brand palette entries from BRAND_IDENTITY_AUTHORITY; material swatches
# are readable even in a distant, fixed isometric gameplay view.
warm_white = make_material("M_PS2P5D_WarmWhite", srgb("#F3F1E9"), 0.68, 0.03)
charcoal = make_material("M_PS2P5D_FoundryCharcoal", srgb("#202428"), 0.53, 0.14)
steel = make_material("M_PS2P5D_SteelGrey", srgb("#70777C"), 0.38, 0.58)
green = make_material("M_PS2P5D_CairnwellGreen", srgb("#1F4B44"), 0.48, 0.10)
yellow = make_material("M_PS2P5D_SafetyYellow", srgb("#F2C300"), 0.44, 0.05)
red = make_material("M_PS2P5D_SignalRed", srgb("#C7352C"), 0.41, 0.06, (0.030, 0.004, 0.003))
deck = make_material("M_PS2P5D_WarmDeck", (0.255, 0.235, 0.205), 0.92)
zone = make_material("M_PS2P5D_PaleProcessZone", (0.18, 0.265, 0.22), 0.86)
bare_coil = make_material("M_PS2P5D_BareCoil", (0.51, 0.57, 0.61), 0.31, 0.76)
wrapped_coil = make_material("M_PS2P5D_WrappedCoil", (0.075, 0.085, 0.095), 0.74, 0.08)

# Architecture is paint and mass only.  The central green slab and cream
# avenue make the factory logic legible, replacing small repeated lane stripes.
floor_block("2.5D | warm factory deck", (0.0, 0.0, -110.0), (4600.0, 3300.0, 220.0), deck, (unreal.Name("LB.Architecture.Deck"),))
floor_block("2.5D | pale-green automated press zone", (0.0, 0.0, 6.0), (2900.0, 2100.0, 28.0), zone, (unreal.Name("LB.Process.Zone"),))
floor_block("2.5D | warm-white operator avenue", (0.0, -1250.0, 14.0), (4100.0, 470.0, 32.0), warm_white, (unreal.Name("LB.Operator.Route"),))
floor_block("2.5D | yellow safe-edge datum", (0.0, -980.0, 34.0), (3000.0, 56.0, 40.0), yellow, (unreal.Name("LB.Safety.Datum"),))

# A single, clear material route: active bare coil -> infeed conveyor -> press
# -> outfeed conveyor -> autonomous robot hand-off.  The Meshy press has no
# baked-in coil and no improvised rollers, so source coils remain their own,
# reusable gameplay objects.
press = spawn(
    "2.5D | S02 | square portal draw-form press",
    assets["PortalPress"], (0.0, 0.0, base_z(assets["PortalPress"])),
    extra_tags=(unreal.Name("LB.Process.S02"), unreal.Name("LB.Meshy.Repaired"), unreal.Name("LB.NoBakedCoil")))

conveyor_scale = (1.15, 0.82, 0.82)
conveyor_z = base_z(assets["Conveyor"], conveyor_scale[2])
spawn("2.5D | infeed | shared powered conveyor", assets["Conveyor"], (-740.0, 0.0, conveyor_z), conveyor_scale, extra_tags=(unreal.Name("LB.Process.Infeed"), unreal.Name("LB.Reused.Conveyor")))
spawn("2.5D | outfeed | shared powered conveyor", assets["Conveyor"], (740.0, 0.0, conveyor_z), conveyor_scale, 180.0, extra_tags=(unreal.Name("LB.Process.Outfeed"), unreal.Name("LB.Reused.Conveyor")))

bare_z = base_z(assets["BareCoil"], 1.55)
spawn("2.5D | active bare master coil", assets["BareCoil"], (-1450.0, 0.0, bare_z), (1.55, 1.55, 1.55), 90.0, (bare_coil,), (unreal.Name("LB.Material.BareCoil"),))
saddle_z = base_z(assets["CoilSaddle"])
spawn("2.5D | reserve coil saddle", assets["CoilSaddle"], (-1150.0, 660.0, saddle_z), extra_tags=(unreal.Name("LB.Material.CoilSupport"),))
reserve_z = saddle_z * 2.0 + base_z(assets["WrappedCoil"], 1.35)
spawn("2.5D | wrapped reserve coil", assets["WrappedCoil"], (-1150.0, 660.0, reserve_z), (1.35, 1.35, 1.35), 90.0, (wrapped_coil,), (unreal.Name("LB.Material.WrappedCoil"),))

spawn("2.5D | robotic press tender", assets["Robot"], (740.0, 590.0, 0.0), (1.28, 1.28, 1.28), -112.0, (steel,), (unreal.Name("LB.Automation.Robot"), unreal.Name("LB.NoWheels")))

# Tiny, flat status beacons are the only decorative geometry.  They provide a
# read of supervised automation without falling back to cable runs or clutter.
for index, x in enumerate((-380.0, 0.0, 380.0), start=1):
    floor_block("2.5D | status beacon %d" % index, (x, 825.0, 70.0), (70.0, 70.0, 140.0), red, (unreal.Name("LB.Automation.Status"),))

# Fixed 2.5D camera: gameplay composition is stable, not a cinematic hunt.
camera_location = unreal.Vector(-2350.0, -2750.0, 2500.0)
camera_target = unreal.Vector(0.0, 0.0, 210.0)
camera = unreal.EditorLevelLibrary.spawn_actor_from_class(unreal.CameraActor, camera_location, aim(camera_location, camera_target))
if not isinstance(camera, unreal.CameraActor):
    fail("could not create fixed isometric camera")
camera.set_actor_label("CAM | 2.5D fixed isometric press-cell proof")
camera.tags = [TAG, unreal.Name("LB.GameplayCamera.FixedIsometric")]
component = camera.get_editor_property("camera_component")
try:
    component.set_editor_property("projection_mode", unreal.CameraProjectionMode.ORTHOGRAPHIC)
    component.set_editor_property("ortho_width", 3900.0)
    camera_mode = "orthographic"
except Exception:
    # A fixed, narrow-FOV perspective is an honest fallback if a particular
    # UE build does not expose orthographic CameraActor properties to Python.
    component.set_editor_property("field_of_view", 26.0)
    camera_mode = "fixed_narrow_fov_perspective_fallback"

# Native Unreal lighting only.  It follows the approved B_stylized values but
# uses no roof mesh or visible fixture geometry; the fixed camera sees an open
# works deck rather than another enclosed, over-detailed hall.
sun = unreal.EditorLevelLibrary.spawn_actor_from_class(unreal.DirectionalLight, unreal.Vector(0.0, 0.0, 5000.0), unreal.Rotator(pitch=-43.0, yaw=-38.0, roll=0.0))
sun.set_actor_label("2.5D | B_stylized sun")
sun.light_component.set_editor_property("mobility", unreal.ComponentMobility.MOVABLE)
sun.light_component.set_editor_property("intensity", 0.30)
sun.tags = [TAG, unreal.Name("LB.Visual.B_stylized")]
sky = unreal.EditorLevelLibrary.spawn_actor_from_class(unreal.SkyLight, unreal.Vector(0.0, 0.0, 5000.0), unreal.Rotator())
sky.set_actor_label("2.5D | B_stylized sky")
sky.light_component.set_editor_property("mobility", unreal.ComponentMobility.MOVABLE)
sky.light_component.set_editor_property("intensity", 0.20)
sky.light_component.set_editor_property("real_time_capture", True)
sky.tags = [TAG, unreal.Name("LB.Visual.B_stylized")]
post = unreal.EditorLevelLibrary.spawn_actor_from_class(unreal.PostProcessVolume, unreal.Vector(), unreal.Rotator())
post.set_actor_label("2.5D | fixed B_stylized exposure")
post.set_editor_property("unbound", True)
settings = post.get_editor_property("settings")
settings.override_auto_exposure_bias = True
settings.auto_exposure_bias = -0.50
post.set_editor_property("settings", settings)
post.tags = [TAG, unreal.Name("LB.Visual.B_stylized")]

if any(unreal.Name("LB.Architecture.Roof") in actor.tags for actor in unreal.EditorLevelLibrary.get_all_level_actors()):
    fail("roof actor found in roofless 2.5D candidate")
if not unreal.EditorLevelLibrary.save_current_level():
    fail("could not save 2.5D candidate map")

for path, expected_hash in source_hashes.items():
    if sha256(uasset_file(path)) != expected_hash:
        fail("source mesh changed: " + path)
protected_after, v002_after = sha256(PROTECTED), sha256(V002)
if protected_after != protected_before or v002_after != v002_before:
    fail("protected map changed while candidate was built")

REPORT.parent.mkdir(parents=True, exist_ok=True)
REPORT.write_text(json.dumps({
    "status": "PASS__ISOLATED_FACTORIO_INSPIRED_2P5D_PRESS_CELL_PROOF_BUILT__V003",
    "candidate_map": MAP,
    "camera": {"label": camera.get_actor_label(), "mode": camera_mode, "fixed": True},
    "visual_contract": {
        "style": "fixed-camera 2.5D isometric factory proof",
        "large_machine_source": "new S02 portal press Meshy derivative v002",
        "separate_coils": True,
        "reused_conveyor": True,
        "native_geometry": "broad floor paint, safety datum, and status beacons only",
        "roof_created": False,
        "wheeled_vehicles_created": False,
        "blue_or_cyan_machine_repaint_created": False,
    },
    "source_uasset_sha256": source_hashes,
    "protected_v438_sha256_before": protected_before,
    "protected_v438_sha256_after": protected_after,
    "v002_sha256_before": v002_before,
    "v002_sha256_after": v002_after,
    "honest_status": "candidate map built; screenshot and playability review are still required",
}, indent=2, sort_keys=True) + "\n", encoding="utf-8")
unreal.log("PRESSSHOP_FACTORIO_2P5D_V003_PASS map=" + MAP + " camera=" + camera_mode)
