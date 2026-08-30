"""Build the compact, roofless v003 Steam-review candidate from real assets.

No protected source map or source mesh is modified.  The only large machine
forms are the supplied cleaned Meshy presses/feeder plus verified in-project
outfeed assets.  Native primitives are broad floor-paint composition only.
"""
import hashlib
import json
import math
from pathlib import Path

import unreal

PROJECT = Path(r"C:\Users\greg_\Projects\LineBossCarFactory_Unreal 5.8")
MAP = "/Game/LineBoss/Candidates/PressShop/PressShop2126_v003/Maps/LB_PressShop_2126_Steam_v003"
ROOT = "/Game/LineBoss/Candidates/PressShop/PressShop2126_v003"
MATERIALS = ROOT + "/Materials"
PROTECTED = PROJECT / "Content" / "LineBoss" / "Maps" / "LB_PressShop_BuilderAuthorityCandidate_v438.umap"
V002 = PROJECT / "Content" / "LineBoss" / "Candidates" / "PressShop" / "PressShop2126_v002" / "Maps" / "LB_PressShop_2126_Steam_v002.umap"
REPORT = PROJECT / "Saved" / "Audits" / "PressShopIntegration" / "pressshop_2126_v003_compact_flow_build.json"
TAG = unreal.Name("LB.PressShop.2126.v003")

MESHY_ROOT = "/Game/LineBoss/Candidates/PressShop/SquareMeshyPressTrain_v001"
SOURCES = {
    "Feeder": "/Game/LineBoss/Candidates/PressShop/MeshyCoilFeederNoCoil_v001/SM_LB_PS_InfeedCoilFeeder_NoCoil_v001",
    "BareCoil": "/Game/LineBoss/IndustrialKit/MaterialHandling/BareCoil/Candidate_v021/SM_LB_BareMasterCoil_v021",
    "WrappedCoil": "/Game/LineBoss/IndustrialKit/MaterialHandling/MasterCoil/Candidate_v005/SM_LB_MasterCoil_Candidate_v005",
    "CoilSaddle": "/Game/LineBoss/IndustrialKit/MaterialHandling/PR003Candidate_v011/SM_LB_CoilSaddle_Candidate_v002",
    "S02": MESHY_ROOT + "/SM_LB_PS_S02_DrawForm_MeshyClean_v001",
    "S03": MESHY_ROOT + "/SM_LB_PS_S03_Trim_MeshyClean_v001",
    "S04": MESHY_ROOT + "/SM_LB_PS_S04_Pierce_MeshyClean_v001",
    "S05": MESHY_ROOT + "/SM_LB_PS_S05_FlangeHem_MeshyClean_v001",
    "S06": MESHY_ROOT + "/SM_LB_PS_S06_VisionOutfeed_MeshyClean_v001",
    "Conveyor": "/Game/LineBoss/Developer/Validation/PressTrains/CompleteTrainA_v662/Supports/SM_CA_MW_PTA_S06S07_PoweredConveyor_SupportAsset_06_v661",
    "Inspection": "/Game/LineBoss/Developer/Validation/PressTrains/CompleteTrainA_v662/Supports/SM_CA_MW_PTA_S07_InspectUnload_SupportAsset_11_v661",
    "Stillage": "/Game/LineBoss/Developer/Validation/PressTrains/CompleteTrainA_v662/Supports/SM_CA_MW_PTA_S07_FlatPanelStillage_SupportAsset_05_v661",
    "Robot": "/Game/Meshes/Robot/SM_RoboArm04",
}
PRESS_SEQUENCE = (("S02", 0.0, "draw / form"), ("S03", 90.0, "trim"), ("S04", 0.0, "pierce"), ("S05", 90.0, "flange / hem"), ("S06", 90.0, "vision / outfeed"))


def digest(path):
    hasher = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            hasher.update(block)
    return hasher.hexdigest()


def source_uasset(path):
    return PROJECT / "Content" / (path.removeprefix("/Game/").replace("/", "\\") + ".uasset")


def srgb(hex_code):
    values = tuple(int(hex_code[index:index + 2], 16) / 255.0 for index in (1, 3, 5))
    return tuple(value ** 2.2 for value in values)


def aim(source, target):
    dx, dy, dz = target.x - source.x, target.y - source.y, target.z - source.z
    return unreal.Rotator(roll=0.0, pitch=math.degrees(math.atan2(dz, math.sqrt(dx * dx + dy * dy))), yaw=math.degrees(math.atan2(dy, dx)))


def make_material(name, colour, roughness, metallic=0.0, emissive=None):
    path = MATERIALS + "/" + name
    material = unreal.AssetToolsHelpers.get_asset_tools().create_asset(name, MATERIALS, unreal.Material, unreal.MaterialFactoryNew())
    if not isinstance(material, unreal.Material):
        raise RuntimeError("Could not create candidate material " + name)
    mel = unreal.MaterialEditingLibrary
    base = mel.create_material_expression(material, unreal.MaterialExpressionConstant3Vector, -420, -100)
    base.set_editor_property("constant", unreal.LinearColor(*colour, 1.0))
    rough = mel.create_material_expression(material, unreal.MaterialExpressionConstant, -420, 10)
    rough.set_editor_property("r", roughness)
    metal = mel.create_material_expression(material, unreal.MaterialExpressionConstant, -420, 100)
    metal.set_editor_property("r", metallic)
    mel.connect_material_property(base, "", unreal.MaterialProperty.MP_BASE_COLOR)
    mel.connect_material_property(rough, "", unreal.MaterialProperty.MP_ROUGHNESS)
    mel.connect_material_property(metal, "", unreal.MaterialProperty.MP_METALLIC)
    if emissive is not None:
        glow = mel.create_material_expression(material, unreal.MaterialExpressionConstant3Vector, -420, -170)
        glow.set_editor_property("constant", unreal.LinearColor(*emissive, 1.0))
        mel.connect_material_property(glow, "", unreal.MaterialProperty.MP_EMISSIVE_COLOR)
    mel.recompile_material(material)
    unreal.EditorAssetLibrary.save_loaded_asset(material, only_if_is_dirty=False)
    return material


def spawn_mesh(label, mesh, location, scale=(1.0, 1.0, 1.0), yaw=0.0, materials=None, tags=()):
    actor = unreal.EditorLevelLibrary.spawn_actor_from_class(unreal.StaticMeshActor, unreal.Vector(*location), unreal.Rotator(roll=0.0, pitch=0.0, yaw=yaw))
    if not isinstance(actor, unreal.StaticMeshActor):
        raise RuntimeError("Could not spawn " + label)
    actor.set_actor_label(label)
    actor.static_mesh_component.set_static_mesh(mesh)
    actor.static_mesh_component.set_world_scale3d(unreal.Vector(*scale))
    actor.static_mesh_component.set_visibility(True, True)
    actor.static_mesh_component.set_render_in_main_pass(True)
    if materials:
        for slot, material in enumerate(materials):
            actor.static_mesh_component.set_material(slot, material)
    actor.tags = [TAG] + list(tags)
    return actor


def cube(label, location, dimensions_cm, material, tags=()):
    return spawn_mesh(label, cube_mesh, location, tuple(value / 100.0 for value in dimensions_cm), 0.0, (material,), tags)


def projected_extent(mesh, yaw, scale=1.0):
    bounds = mesh.get_bounds().box_extent
    if int(abs(yaw)) % 180 == 90:
        return bounds.y * scale, bounds.x * scale, bounds.z * scale
    return bounds.x * scale, bounds.y * scale, bounds.z * scale


if not PROTECTED.is_file() or not V002.is_file():
    raise RuntimeError("Protected evidence map missing")
protected_before, v002_before = digest(PROTECTED), digest(V002)
if not unreal.EditorLoadingAndSavingUtils.load_map(MAP):
    raise RuntimeError("Could not load isolated v003 map")
if any(TAG in actor.tags for actor in unreal.EditorLevelLibrary.get_all_level_actors()):
    raise RuntimeError("v003 compact build already applied")

assets, source_hashes = {}, {}
for role, path in SOURCES.items():
    mesh = unreal.load_asset(path)
    if not isinstance(mesh, unreal.StaticMesh):
        raise RuntimeError("Required asset unavailable: " + role)
    disk = source_uasset(path)
    if not disk.is_file():
        raise RuntimeError("Source package unavailable: " + str(disk))
    assets[role] = mesh
    source_hashes[path] = digest(disk)
cube_mesh = unreal.load_asset("/Engine/BasicShapes/Cube")
if not isinstance(cube_mesh, unreal.StaticMesh):
    raise RuntimeError("Native Unreal cube unavailable")

# Candidate-only materials, based exactly on the in-repo brand palette.
charcoal = make_material("M_LB_PS2126v003_FoundryCharcoal", srgb("#202428"), 0.52, 0.15, (0.010, 0.012, 0.015))
warm_white = make_material("M_LB_PS2126v003_WarmWhite", srgb("#F3F1E9"), 0.66, 0.04)
red = make_material("M_LB_PS2126v003_StatusRed", srgb("#C7352C"), 0.42, 0.06, (0.030, 0.004, 0.003))
yellow = make_material("M_LB_PS2126v003_SafetyYellow", srgb("#F2C300"), 0.45, 0.06)
steel = make_material("M_LB_PS2126v003_SteelGrey", srgb("#70777C"), 0.38, 0.55)
green = make_material("M_LB_PS2126v003_CairnwellGreen", srgb("#1F4B44"), 0.48, 0.10, (0.004, 0.018, 0.014))
concrete = make_material("M_LB_PS2126v003_WarmConcrete", (0.25, 0.23, 0.20), 0.90)
zone = make_material("M_LB_PS2126v003_PaleGreenZone", (0.20, 0.24, 0.21), 0.86)
bare_coil = make_material("M_LB_PS2126v003_BareGalvanized", (0.52, 0.58, 0.62), 0.34, 0.70)
wrapped_coil = make_material("M_LB_PS2126v003_WrappedGraphite", (0.09, 0.105, 0.115), 0.72, 0.08, (0.015, 0.018, 0.020))
press_materials = (charcoal, warm_white, red, yellow, steel, green)

# Build a genuinely compact flow.  The prior map left 60–80m display gaps;
# here positions are derived from actual mesh bounds with 2.5m transfer gaps.
sequence = [("Feeder", 0.0, 0.85, "coil-free autonomous feeder")]
sequence.extend((role, yaw, 1.0, text) for role, yaw, text in PRESS_SEQUENCE)
sequence.extend((("Conveyor", 0.0, 1.0, "powered outfeed conveyor"), ("Inspection", 0.0, 1.0, "inspection unload cell")))
gap = 250.0
widths = [projected_extent(assets[role], yaw, scale)[0] for role, yaw, scale, _text in sequence]
total_length = sum(width * 2.0 for width in widths) + gap * (len(widths) - 1)
cursor = -total_length / 2.0
placed = []
line_positions = {}
for index, ((role, yaw, scale, text), half_width) in enumerate(zip(sequence, widths)):
    center_x = cursor + half_width
    extent_z = projected_extent(assets[role], yaw, scale)[2]
    z = max(extent_z, 0.0)
    label = "2126 v003 | %02d | %s" % (index + 1, text)
    mats = press_materials if role.startswith("S0") else ((warm_white,) if role == "Feeder" else None)
    actor = spawn_mesh(label, assets[role], (center_x, 0.0, z), (scale, scale, scale), yaw, mats, (unreal.Name("LB.Process.Flow"), unreal.Name("LB.Meshy.Repaired") if role in ("Feeder", "S02", "S03", "S04", "S05", "S06") else unreal.Name("LB.Reused.VerifiedSupport"),))
    line_positions[role] = (center_x, z, half_width)
    placed.append({"role": role, "actor": label, "location_cm": [round(center_x, 2), 0.0, round(z, 2)], "yaw": yaw})
    cursor = center_x + half_width + gap

# The separate source coils make the materials story visible without accepting
# the duplicate coil baked into the generated feeder.  Bare = active, wrapped
# = reserve on a reused saddle.  No wheels are introduced.
feeder_x, feeder_z, feeder_half = line_positions["Feeder"]
bare_half_z = assets["BareCoil"].get_bounds().box_extent.z * 2.0
wrapped_half_z = assets["WrappedCoil"].get_bounds().box_extent.z * 2.0
bare = spawn_mesh("2126 v003 | active bare galvanized coil", assets["BareCoil"], (feeder_x - feeder_half * 0.18, -1650.0, bare_half_z), (2.0, 2.0, 2.0), 90.0, (bare_coil,), (unreal.Name("LB.Reused.ProjectCoil"),))
saddle_z = assets["CoilSaddle"].get_bounds().box_extent.z
saddle = spawn_mesh("2126 v003 | wrapped reserve coil saddle", assets["CoilSaddle"], (feeder_x - feeder_half * 0.80, 2550.0, saddle_z), (1.0, 1.0, 1.0), 0.0, None, (unreal.Name("LB.Reused.ProjectCoilSupport"),))
wrapped = spawn_mesh("2126 v003 | wrapped graphite reserve coil", assets["WrappedCoil"], (feeder_x - feeder_half * 0.80, 2550.0, wrapped_half_z + saddle_z * 2.0), (2.0, 2.0, 2.0), 90.0, (wrapped_coil,), (unreal.Name("LB.Reused.ProjectCoil"),))
placed.extend(({"role": "bare_active_coil", "actor": bare.get_actor_label()}, {"role": "wrapped_reserve_coil", "actor": wrapped.get_actor_label()}, {"role": "reserve_saddle", "actor": saddle.get_actor_label()}))

# Two staged stillages complete the outfeed, deliberately without forklifts or
# wheeled carts; automation robots flank the stations instead.
inspection_x, inspection_z, inspection_half = line_positions["Inspection"]
stillage_half_z = assets["Stillage"].get_bounds().box_extent.z
for index, y in enumerate((2100.0, -2100.0), start=1):
    actor = spawn_mesh("2126 v003 | finished-panel stillage %02d" % index, assets["Stillage"], (inspection_x + inspection_half + 450.0, y, stillage_half_z), (1.0, 1.0, 1.0), 0.0, None, (unreal.Name("LB.Process.Outfeed"), unreal.Name("LB.Reused.VerifiedSupport")))
    placed.append({"role": "panel_stillage", "actor": actor.get_actor_label()})

for index, (role, _yaw, _scale, _text) in enumerate(sequence[1:6], start=1):
    station_x, _station_z, station_half = line_positions[role]
    side = 3150.0 if index % 2 else -3150.0
    robot = spawn_mesh("2126 v003 | autonomous tend robot %02d" % index, assets["Robot"], (station_x, side, 0.0), (1.35, 1.35, 1.35), -90.0 if side > 0 else 90.0, (steel,), (unreal.Name("LB.Automation.Robot"),))
    placed.append({"role": "tend_robot", "actor": robot.get_actor_label()})

# Only broad, intentionally painted architecture: no roof, no beams, no tiny
# props.  The cream lane gives a human-readable service path; the central zone
# makes the automated process legible from a management camera.
deck_length = total_length + 11000.0
cube("2126 v003 | warm concrete works deck", (0.0, 0.0, -90.0), (deck_length, 13500.0, 180.0), concrete, (unreal.Name("LB.Architecture.Deck"),))
cube("2126 v003 | pale-green production zone", (0.0, 0.0, 8.0), (total_length + 2600.0, 7800.0, 22.0), zone, (unreal.Name("LB.Architecture.ProcessZone"),))
cube("2126 v003 | cream operator avenue", (0.0, -4700.0, 20.0), (total_length + 8000.0, 1450.0, 40.0), warm_white, (unreal.Name("LB.Architecture.OperatorRoute"),))
cube("2126 v003 | safety flow datum operator", (0.0, -3850.0, 42.0), (total_length + 1600.0, 80.0, 44.0), yellow, (unreal.Name("LB.Architecture.SafetyDatum"),))
cube("2126 v003 | safety flow datum service", (0.0, 3850.0, 42.0), (total_length + 1600.0, 80.0, 44.0), yellow, (unreal.Name("LB.Architecture.SafetyDatum"),))

# Native Unreal open-air lighting; rect fixtures are deliberately absent so
# there are no white pools.  This is candidate review lighting, not a release
# lighting calibration claim.
sun = unreal.EditorLevelLibrary.spawn_actor_from_class(unreal.DirectionalLight, unreal.Vector(0.0, 0.0, 9000.0), unreal.Rotator(roll=0.0, pitch=-42.0, yaw=-28.0))
sun.set_actor_label("2126 v003 | open-air directional sun")
sun.light_component.set_editor_property("mobility", unreal.ComponentMobility.MOVABLE)
sun.light_component.set_editor_property("intensity", 8.0)
sun.light_component.set_editor_property("use_temperature", True)
sun.light_component.set_editor_property("temperature", 5600.0)
sun.light_component.set_editor_property("atmosphere_sun_light", True)
sun.light_component.set_editor_property("atmosphere_sun_light_index", 0)
sun.tags = [TAG, unreal.Name("LB.Lighting.OpenAir")]
sky = unreal.EditorLevelLibrary.spawn_actor_from_class(unreal.SkyLight, unreal.Vector(0.0, 0.0, 8000.0), unreal.Rotator())
sky.set_actor_label("2126 v003 | open-air skylight")
sky.light_component.set_editor_property("mobility", unreal.ComponentMobility.MOVABLE)
sky.light_component.set_editor_property("intensity", 5.0)
sky.light_component.set_editor_property("real_time_capture", True)
sky.tags = [TAG, unreal.Name("LB.Lighting.OpenAir")]
atmosphere = unreal.EditorLevelLibrary.spawn_actor_from_class(unreal.SkyAtmosphere, unreal.Vector(), unreal.Rotator())
atmosphere.set_actor_label("2126 v003 | native sky atmosphere")
atmosphere.tags = [TAG, unreal.Name("LB.Architecture.OpenSky")]
post = unreal.EditorLevelLibrary.spawn_actor_from_class(unreal.PostProcessVolume, unreal.Vector(), unreal.Rotator())
post.set_actor_label("2126 v003 | neutral management exposure")
post.set_editor_property("unbound", True)
settings = post.get_editor_property("settings")
settings.override_auto_exposure_bias = True
settings.auto_exposure_bias = 0.0
settings.override_white_temp = True
settings.white_temp = 6500.0
post.set_editor_property("settings", settings)
post.tags = [TAG, unreal.Name("LB.Lighting.OpenAir")]

# Capture cameras are deliberately framed from the actual compact bounds.
overview_source = unreal.Vector(-total_length * 0.58, -total_length * 0.52, total_length * 0.34)
overview_target = unreal.Vector(0.0, 0.0, 350.0)
overview = unreal.EditorLevelLibrary.spawn_actor_from_class(unreal.CineCameraActor, overview_source, aim(overview_source, overview_target))
overview.set_actor_label("CAM v003 | compact whole-flow overview")
overview.get_cine_camera_component().set_editor_property("current_focal_length", 42.0)
overview.tags = [TAG, unreal.Name("LB.ManagementCamera.WholeFlow")]
hero_source = unreal.Vector(-total_length * 0.18, -10500.0, 5200.0)
hero_target = unreal.Vector(total_length * 0.10, 0.0, 380.0)
hero = unreal.EditorLevelLibrary.spawn_actor_from_class(unreal.CineCameraActor, hero_source, aim(hero_source, hero_target))
hero.set_actor_label("CAM v003 | compact press hero")
hero.get_cine_camera_component().set_editor_property("current_focal_length", 54.0)
hero.tags = [TAG, unreal.Name("LB.ManagementCamera.Hero")]
unreal.EditorLevelLibrary.set_level_viewport_camera_info(hero_source, hero.get_actor_rotation())

if any("roof" in actor.get_actor_label().lower() for actor in unreal.EditorLevelLibrary.get_all_level_actors()):
    raise RuntimeError("Roof actor found in explicitly roofless v003 candidate")
if not unreal.EditorLevelLibrary.save_current_level():
    raise RuntimeError("Could not save compact v003 candidate")
for path, expected in source_hashes.items():
    if digest(source_uasset(path)) != expected:
        raise RuntimeError("Source asset mutated: " + path)
protected_after, v002_after = digest(PROTECTED), digest(V002)
if protected_before != protected_after or v002_before != v002_after:
    raise RuntimeError("Protected evidence map changed during v003 build")
REPORT.parent.mkdir(parents=True, exist_ok=True)
REPORT.write_text(json.dumps({
    "status": "PASS__COMPACT_REAL_MESHY_AND_REUSED_SUPPORT_FLOW_BUILT",
    "candidate_map": MAP,
    "source_meshes_modified": False,
    "source_uasset_sha256": source_hashes,
    "compact_flow_length_cm": round(total_length, 2),
    "transfer_gap_cm": gap,
    "placed": placed,
    "new_large_machine_geometry": 0,
    "native_geometry_scope": "deck, painted zone, avenue and two safety datums only",
    "active_rect_lights": 0,
    "roof_created": False,
    "v002_sha256_before": v002_before,
    "v002_sha256_after": v002_after,
    "protected_v438_sha256_before": protected_before,
    "protected_v438_sha256_after": protected_after,
}, indent=2), encoding="utf-8")
unreal.log("PRESSSHOP_2126_V003_COMPACT_FLOW_BUILD_PASS")
