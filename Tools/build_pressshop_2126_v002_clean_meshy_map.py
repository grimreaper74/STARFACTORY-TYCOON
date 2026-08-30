"""Build a clean, roofless 2126 Press Shop v002 with real Meshy machinery.

Candidate-only native-Unreal assembly.  The five supplied/cleaned Meshy press
forms and the coil-free Meshy feeder are the only large machine forms.  Native
Unreal geometry is restricted to broad deck, facade, rail, lighting and
navigation composition, so a management screenshot reads the machines first.
"""

import hashlib
import json
import math
from pathlib import Path

import unreal


PROJECT = Path(r"C:\Users\greg_\Projects\LineBossCarFactory_Unreal 5.8")
MAP = "/Game/LineBoss/Candidates/PressShop/PressShop2126_v002/Maps/LB_PressShop_2126_Steam_v002"
ROOT = "/Game/LineBoss/Candidates/PressShop/PressShop2126_v002"
MATERIAL_ROOT = ROOT + "/Materials"
PROTECTED = PROJECT / "Content" / "LineBoss" / "Maps" / "LB_PressShop_BuilderAuthorityCandidate_v438.umap"
REPORT = PROJECT / "Saved" / "Audits" / "PressShopIntegration" / "pressshop_2126_v002_clean_meshy_build.json"
TAG = unreal.Name("LB.PressShop.2126.v002")
STYLE = unreal.Name("LB.Visual.2126")

PRESS_ROOT = "/Game/LineBoss/Candidates/PressShop/SquareMeshyPressTrain_v001"
PRESS_PATHS = (
    ("S02 Draw / form", PRESS_ROOT + "/SM_LB_PS_S02_DrawForm_MeshyClean_v001", (-4200.0, 0.0, 0.0), 0.0),
    ("S03 Trim", PRESS_ROOT + "/SM_LB_PS_S03_Trim_MeshyClean_v001", (-2100.0, 0.0, 0.0), 90.0),
    ("S04 Pierce", PRESS_ROOT + "/SM_LB_PS_S04_Pierce_MeshyClean_v001", (-200.0, 0.0, 0.0), 0.0),
    ("S05 Flange / hem", PRESS_ROOT + "/SM_LB_PS_S05_FlangeHem_MeshyClean_v001", (1600.0, 0.0, 0.0), 90.0),
    ("S06 Vision / outfeed", PRESS_ROOT + "/SM_LB_PS_S06_VisionOutfeed_MeshyClean_v001", (3500.0, 0.0, 0.0), 90.0),
)
FEEDER = "/Game/LineBoss/Candidates/PressShop/MeshyCoilFeederNoCoil_v001/SM_LB_PS_InfeedCoilFeeder_NoCoil_v001"
BARE_COIL = "/Game/LineBoss/IndustrialKit/MaterialHandling/BareCoil/Candidate_v021/SM_LB_BareMasterCoil_v021"
WRAPPED_COIL = "/Game/LineBoss/IndustrialKit/MaterialHandling/MasterCoil/Candidate_v005/SM_LB_MasterCoil_Candidate_v005"
COIL_SADDLE = "/Game/LineBoss/IndustrialKit/MaterialHandling/PR003Candidate_v011/SM_LB_CoilSaddle_Candidate_v002"
ROBOT = "/Game/Meshes/Robot/SM_RoboArm04"

# Exact authorised brand tokens expressed in linear colour space.
def srgb(hex_code):
    values = tuple(int(hex_code[index:index + 2], 16) / 255.0 for index in (1, 3, 5))
    return tuple(value ** 2.2 for value in values)


BRAND = {
    "charcoal": srgb("#202428"),
    "steel": srgb("#70777C"),
    "green": srgb("#1F4B44"),
    "yellow": srgb("#F2C300"),
    "red": srgb("#C7352C"),
    "warm_white": srgb("#F3F1E9"),
    "pale_green": srgb("#84B99A"),
}


def fail(message):
    raise RuntimeError("PRESSSHOP_2126_V002_BUILD_FAIL: " + message)


def digest(path):
    hasher = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            hasher.update(block)
    return hasher.hexdigest()


def aim(source, target):
    dx, dy, dz = target.x - source.x, target.y - source.y, target.z - source.z
    flat = math.sqrt(dx * dx + dy * dy)
    return unreal.Rotator(math.degrees(math.atan2(dz, flat)), math.degrees(math.atan2(dy, dx)), 0.0)


def make_material(name, colour, roughness, metallic=0.0, emissive=0.0):
    path = MATERIAL_ROOT + "/" + name
    material = unreal.load_asset(path) if unreal.EditorAssetLibrary.does_asset_exist(path) else None
    if material is None:
        material = unreal.AssetToolsHelpers.get_asset_tools().create_asset(
            name, MATERIAL_ROOT, unreal.Material, unreal.MaterialFactoryNew())
    if not isinstance(material, unreal.Material):
        fail("Could not create material " + name)
    mel = unreal.MaterialEditingLibrary
    mel.delete_all_material_expressions(material)
    base = mel.create_material_expression(material, unreal.MaterialExpressionConstant3Vector, -420, -100)
    base.set_editor_property("constant", unreal.LinearColor(*colour, 1.0))
    rough = mel.create_material_expression(material, unreal.MaterialExpressionConstant, -420, 20)
    rough.set_editor_property("r", roughness)
    metal = mel.create_material_expression(material, unreal.MaterialExpressionConstant, -420, 120)
    metal.set_editor_property("r", metallic)
    mel.connect_material_property(base, "", unreal.MaterialProperty.MP_BASE_COLOR)
    mel.connect_material_property(rough, "", unreal.MaterialProperty.MP_ROUGHNESS)
    mel.connect_material_property(metal, "", unreal.MaterialProperty.MP_METALLIC)
    if emissive > 0.0:
        gain = mel.create_material_expression(material, unreal.MaterialExpressionConstant, -420, -200)
        gain.set_editor_property("r", emissive)
        product = mel.create_material_expression(material, unreal.MaterialExpressionMultiply, -160, -90)
        mel.connect_material_expressions(base, "", product, "A")
        mel.connect_material_expressions(gain, "", product, "B")
        mel.connect_material_property(product, "", unreal.MaterialProperty.MP_EMISSIVE_COLOR)
    mel.recompile_material(material)
    unreal.EditorAssetLibrary.save_loaded_asset(material, only_if_is_dirty=False)
    return material


def spawn_mesh(label, mesh, location, scale=(1.0, 1.0, 1.0), rotation=None, materials=None, tags=()):
    actor = unreal.EditorLevelLibrary.spawn_actor_from_class(
        unreal.StaticMeshActor, unreal.Vector(*location), rotation or unreal.Rotator())
    if not isinstance(actor, unreal.StaticMeshActor):
        fail("Could not spawn " + label)
    actor.set_actor_label(label)
    actor.tags = [TAG, STYLE] + list(tags)
    component = actor.static_mesh_component
    component.set_static_mesh(mesh)
    component.set_world_scale3d(unreal.Vector(*scale))
    component.set_visibility(True, True)
    component.set_render_in_main_pass(True)
    if materials:
        for index, material in enumerate(materials):
            component.set_material(index, material)
    return actor


def cube(label, location, dimensions_cm, material, rotation=None, tags=()):
    return spawn_mesh(
        label, CUBE, location,
        tuple(dimension / 100.0 for dimension in dimensions_cm),
        rotation, (material,), tags)


def actor_record(actor, role, asset=None):
    position = actor.get_actor_location()
    rotation = actor.get_actor_rotation()
    return {
        "label": actor.get_actor_label(),
        "role": role,
        "asset": asset.get_path_name() if asset else None,
        "location_cm": [round(position.x, 1), round(position.y, 1), round(position.z, 1)],
        "yaw": round(rotation.yaw, 1),
    }


if not PROTECTED.is_file():
    fail("Protected v438 map is missing")
protected_before = digest(PROTECTED)
if not unreal.EditorAssetLibrary.does_asset_exist(MAP):
    fail("v002 map is missing; create it in a separate editor session first")
if not unreal.EditorLoadingAndSavingUtils.load_map(MAP):
    fail("Could not load v002 map")
if any(TAG in actor.tags for actor in unreal.EditorLevelLibrary.get_all_level_actors()):
    fail("v002 build tag is already present; refusing to duplicate the map")

CUBE = unreal.load_asset("/Engine/BasicShapes/Cube")
if not isinstance(CUBE, unreal.StaticMesh):
    fail("Native Unreal cube is unavailable")

assets = {}
for name, path, _location, _yaw in PRESS_PATHS:
    item = unreal.load_asset(path)
    if not isinstance(item, unreal.StaticMesh):
        fail("Missing Meshy press " + name)
    assets[name] = item
for name, path in (("Feeder", FEEDER), ("BareCoil", BARE_COIL), ("WrappedCoil", WRAPPED_COIL), ("Saddle", COIL_SADDLE), ("Robot", ROBOT)):
    item = unreal.load_asset(path)
    if not isinstance(item, unreal.StaticMesh):
        fail("Missing approved source asset " + name)
    assets[name] = item

mats = {
    "charcoal": make_material("M_LB_PS2126v002_FoundryCharcoal", BRAND["charcoal"], 0.52, 0.38),
    "steel": make_material("M_LB_PS2126v002_SteelGrey", BRAND["steel"], 0.42, 0.62),
    "green": make_material("M_LB_PS2126v002_CairnwellGreen", BRAND["green"], 0.47, 0.16),
    "yellow": make_material("M_LB_PS2126v002_SafetyYellow", BRAND["yellow"], 0.45, 0.10),
    "red": make_material("M_LB_PS2126v002_StatusRed", BRAND["red"], 0.40, 0.08, 1.2),
    "warm_white": make_material("M_LB_PS2126v002_WarmWhite", BRAND["warm_white"], 0.64, 0.04),
    "pale_green": make_material("M_LB_PS2126v002_PaleGreenZone", BRAND["pale_green"], 0.78),
    "amber": make_material("M_LB_PS2126v002_AmberData", BRAND["yellow"], 0.30, 0.08, 3.0),
}
press_slots = (mats["charcoal"], mats["warm_white"], mats["red"], mats["yellow"], mats["steel"], mats["green"])
records = []

# Broad roofless environment: colour is carried by the deck and facades, not
# texture noise. The two facade planes are walls, never a roof or canopy.
records.append(actor_record(cube("2126 v002 | charcoal factory deck", (-4200.0, 0.0, -90.0), (45000.0, 15000.0, 180.0), mats["charcoal"], tags=(unreal.Name("LB.Architecture.Deck"),)), "environment"))
for label, x, length in (
    ("inbound", -13200.0, 6200.0),
    ("press west", -4400.0, 5200.0),
    ("press east", 1200.0, 5200.0),
    ("outbound", 5600.0, 3600.0),
):
    records.append(actor_record(cube("2126 v002 | pale-green process island | " + label, (x, 0.0, 6.0), (length, 6100.0, 28.0), mats["pale_green"], tags=(unreal.Name("LB.Architecture.ProcessZone"),)), "environment"))
records.append(actor_record(cube("2126 v002 | wide cream operator avenue", (-4200.0, -4300.0, 16.0), (43000.0, 1250.0, 44.0), mats["warm_white"], tags=(unreal.Name("LB.Architecture.OperatorRoute"),)), "environment"))
records.append(actor_record(cube("2126 v002 | warm-white rear elevation", (-4200.0, 4400.0, 900.0), (42000.0, 55.0, 1800.0), mats["warm_white"], tags=(unreal.Name("LB.Architecture.RooflessFacade"),)), "environment"))
records.append(actor_record(cube("2126 v002 | Cairnwell supervision ribbon", (-4200.0, 4352.0, 1050.0), (42000.0, 45.0, 350.0), mats["green"], tags=(unreal.Name("LB.Architecture.RooflessFacade"),)), "environment"))
records.append(actor_record(cube("2126 v002 | safety-yellow process datum", (-4200.0, 4305.0, 1390.0), (42000.0, 45.0, 85.0), mats["yellow"], tags=(unreal.Name("LB.Architecture.RooflessFacade"),)), "environment"))

# Sparse vertical structure only. There are no crossbeams above the line and
# no roof mesh: it is explicitly an open-air future works, not a hall shell.
for x in (-15400.0, -8600.0, -1800.0, 5000.0, 11800.0):
    for y in (-6600.0, 6600.0):
        records.append(actor_record(cube("2126 v002 | open-air mast %.0f %.0f" % (x, y), (x, y, 3900.0), (260.0, 260.0, 7800.0), mats["steel"], tags=(unreal.Name("LB.Architecture.OpenAir"),)), "environment"))
        records.append(actor_record(cube("2126 v002 | mast safety foot %.0f %.0f" % (x, y), (x, y, 115.0), (480.0, 480.0, 120.0), mats["yellow"], tags=(unreal.Name("LB.Architecture.OpenAir"),)), "environment"))

# Real user/project coil story: a wrapped spare on a kit saddle, then a bare
# operational coil separately seated on the repaired coil-free Meshy feeder.
records.append(actor_record(spawn_mesh("S00 | wrapped master coil | project reuse", assets["WrappedCoil"], (-15800.0, 1700.0, 160.0), rotation=unreal.Rotator(0.0, 90.0, 0.0), tags=(unreal.Name("LB.Reused.ProjectCoil"),)), "wrapped_coil", assets["WrappedCoil"]))
records.append(actor_record(spawn_mesh("S00 | wrapped coil changeover saddle | kit reuse", assets["Saddle"], (-15800.0, 1700.0, 0.0), tags=(unreal.Name("LB.Reused.ProjectCoilSupport"),)), "coil_support", assets["Saddle"]))
records.append(actor_record(spawn_mesh("S00 | Meshy coil-free autonomous feeder", assets["Feeder"], (-12597.5, -81.3, 0.0), (0.85, 0.85, 0.85), tags=(unreal.Name("LB.Meshy.Repaired"),)), "meshy_feeder", assets["Feeder"]))
records.append(actor_record(spawn_mesh("S00 | bare master coil | project reuse", assets["BareCoil"], (-13200.0, 0.0, 216.1), rotation=unreal.Rotator(0.0, 90.0, 0.0), tags=(unreal.Name("LB.Reused.ProjectCoil"),)), "bare_coil", assets["BareCoil"]))

# The production centrepiece: actual cleaned Meshy assets, no native cube
# duplicates. Exact palette slots are per-instance overrides, keeping imported
# source assets unchanged while correcting the presentation drift.
for name, _path, location, yaw in PRESS_PATHS:
    actor = spawn_mesh("MESHY v002 | " + name, assets[name], location, rotation=unreal.Rotator(0.0, yaw, 0.0), materials=press_slots, tags=(unreal.Name("LB.Meshy.Press"),))
    records.append(actor_record(actor, "meshy_press", assets[name]))
    # One bold station identity badge, not a forest of micro-props.
    records.append(actor_record(cube("2126 v002 | " + name + " amber station beacon", (location[0], -2650.0, 650.0), (370.0, 90.0, 720.0), mats["amber"], tags=(unreal.Name("LB.Automation.Beacon"),)), "automation"))

# Four actual project robots make the 2126 automation obvious. They are visibly
# separated from presses and carry no invented wheeled transport.
for label, location, yaw, scale in (
    ("S01 laser-tend robot", (-8000.0, 2450.0, 0.0), -155.0, 1.10),
    ("S02 draw quality robot", (-4200.0, -2050.0, 0.0), 180.0, 1.00),
    ("S04 pierce handling robot", (-200.0, -2150.0, 0.0), 180.0, 1.00),
    ("S06 vision stack robot", (4450.0, -2100.0, 0.0), -20.0, 1.20),
):
    actor = spawn_mesh("ROBOT v002 | " + label, assets["Robot"], location, (scale, scale, scale), unreal.Rotator(0.0, yaw, 0.0), (mats["steel"],), (unreal.Name("LB.Automation.Robot"),))
    records.append(actor_record(actor, "automation_robot", assets["Robot"]))

# A single clearly readable overhead handling language: side rails and three
# amber carriages. It stays below the open sky, without spanning a roof.
for side, y in (("operator", -2200.0), ("service", 2200.0)):
    records.append(actor_record(cube("2126 v002 | transfer rail | " + side, (-200.0, y, 740.0), (16500.0, 100.0, 100.0), mats["steel"], tags=(unreal.Name("LB.Automation.Transfer"),)), "automation"))
for index, x in enumerate((-3300.0, -200.0, 2900.0), start=1):
    records.append(actor_record(cube("2126 v002 | transfer carriage %02d" % index, (x, 0.0, 660.0), (520.0, 480.0, 160.0), mats["yellow"], tags=(unreal.Name("LB.Automation.Transfer"),)), "automation"))

# Approved B_stylized calibration: exactly six movable 1200 lm fixtures,
# directional sun 0.30, skylight 0.20, and one manual exposure of -0.50.
sun = unreal.EditorLevelLibrary.spawn_actor_from_class(unreal.DirectionalLight, unreal.Vector(-3000.0, -3000.0, 10000.0), unreal.Rotator(-38.0, -28.0, 0.0))
sun.set_actor_label("B_stylized | sun 0.30")
sun.tags = [TAG, STYLE, unreal.Name("LB.Lighting.B_stylized")]
sun.light_component.set_editor_property("mobility", unreal.ComponentMobility.MOVABLE)
sun.light_component.set_editor_property("intensity", 0.30)
sun.light_component.set_editor_property("use_temperature", True)
sun.light_component.set_editor_property("temperature", 5000.0)
records.append(actor_record(sun, "lighting"))
sky = unreal.EditorLevelLibrary.spawn_actor_from_class(unreal.SkyLight, unreal.Vector(-3000.0, 0.0, 6000.0), unreal.Rotator())
sky.set_actor_label("B_stylized | sky 0.20")
sky.tags = [TAG, STYLE, unreal.Name("LB.Lighting.B_stylized")]
sky.light_component.set_editor_property("mobility", unreal.ComponentMobility.MOVABLE)
sky.light_component.set_editor_property("intensity", 0.20)
sky.light_component.set_editor_property("real_time_capture", True)
records.append(actor_record(sky, "lighting"))
for index, x in enumerate((-12500.0, -8500.0, -4500.0, -500.0, 3500.0, 7200.0), start=1):
    fixture = unreal.EditorLevelLibrary.spawn_actor_from_class(unreal.RectLight, unreal.Vector(x, -600.0, 8200.0), unreal.Rotator(-90.0, 0.0, 0.0))
    fixture.set_actor_label("B_stylized | 1200 lm fixture %02d" % index)
    fixture.tags = [TAG, STYLE, unreal.Name("LB.Lighting.B_stylized")]
    comp = fixture.light_component
    comp.set_editor_property("mobility", unreal.ComponentMobility.MOVABLE)
    comp.set_editor_property("intensity", 1200.0)
    comp.set_editor_property("intensity_units", unreal.LightUnits.LUMENS)
    comp.set_editor_property("source_width", 2600.0)
    comp.set_editor_property("source_height", 1200.0)
    comp.set_editor_property("use_temperature", True)
    comp.set_editor_property("temperature", 5000.0)
    records.append(actor_record(fixture, "lighting"))
post = unreal.EditorLevelLibrary.spawn_actor_from_class(unreal.PostProcessVolume, unreal.Vector(-3000.0, 0.0, 600.0), unreal.Rotator())
post.set_actor_label("B_stylized | fixed exposure -0.50")
post.tags = [TAG, STYLE, unreal.Name("LB.Lighting.B_stylized")]
post.set_editor_property("unbound", True)
settings = post.get_editor_property("settings")
settings.override_auto_exposure_bias = True
settings.auto_exposure_bias = -0.50
settings.override_white_temp = True
settings.white_temp = 6500.0
post.set_editor_property("settings", settings)
records.append(actor_record(post, "lighting"))

# Cameras crop the roofless scene against the warm facade so the image is
# materially different from the cyan/empty v001 views. All use the real assets.
for label, source, target, focal in (
    ("CAM v002 | steam hero press run", (-8500.0, -5300.0, 610.0), (-550.0, 0.0, 370.0), 68.0),
    ("CAM v002 | coil-to-press story", (-17800.0, -3300.0, 450.0), (-12000.0, 0.0, 360.0), 70.0),
    ("CAM v002 | draw plus robot", (-7800.0, -3600.0, 480.0), (-4200.0, -150.0, 330.0), 70.0),
    ("CAM v002 | press automation", (-2800.0, -4100.0, 500.0), (-200.0, -250.0, 320.0), 70.0),
):
    camera = unreal.EditorLevelLibrary.spawn_actor_from_class(unreal.CineCameraActor, unreal.Vector(*source), aim(unreal.Vector(*source), unreal.Vector(*target)))
    camera.set_actor_label(label)
    camera.tags = [TAG, STYLE, unreal.Name("LB.SteamReviewCamera")]
    camera.get_cine_camera_component().set_editor_property("current_focal_length", focal)
    records.append(actor_record(camera, "camera"))

hero = next(actor for actor in unreal.EditorLevelLibrary.get_all_level_actors() if actor.get_actor_label() == "CAM v002 | steam hero press run")
unreal.EditorLevelLibrary.set_level_viewport_camera_info(hero.get_actor_location(), hero.get_actor_rotation())

if not unreal.EditorLevelLibrary.save_current_level():
    fail("Could not save v002 candidate map")
protected_after = digest(PROTECTED)
if protected_before != protected_after:
    fail("Protected v438 map changed while v002 was built")

# Fail closed on the actual artistic contract, not an assumption about it.
all_actors = list(unreal.EditorLevelLibrary.get_all_level_actors())
meshy_labels = [actor.get_actor_label() for actor in all_actors if unreal.Name("LB.Meshy.Press") in actor.tags]
robot_labels = [actor.get_actor_label() for actor in all_actors if unreal.Name("LB.Automation.Robot") in actor.tags]
fixture_labels = [actor.get_actor_label() for actor in all_actors if actor.get_actor_label().startswith("B_stylized | 1200 lm fixture")]
if len(meshy_labels) != 5 or len(robot_labels) != 4 or len(fixture_labels) != 6:
    fail("Visual asset count gate failed: Meshy=%d robots=%d fixtures=%d" % (len(meshy_labels), len(robot_labels), len(fixture_labels)))
if any("roof" in actor.get_actor_label().lower() for actor in all_actors):
    fail("Roof-named actor gate failed")

REPORT.parent.mkdir(parents=True, exist_ok=True)
REPORT.write_text(json.dumps({
    "status": "PASS__CLEAN_ROOFLESS_2126_MESHY_CANDIDATE_BUILT",
    "candidate_map": MAP,
    "protected_v438_sha256_before": protected_before,
    "protected_v438_sha256_after": protected_after,
    "real_meshy_presses": meshy_labels,
    "real_meshy_coil_free_feeder": FEEDER,
    "separate_reused_project_coils": [BARE_COIL, WRAPPED_COIL],
    "embedded_meshy_coils": 0,
    "reused_project_robots": robot_labels,
    "native_geometry_scope": "broad deck, paint zones, two facade planes, sparse vertical masts and transfer rails only",
    "roof_created": False,
    "b_stylized": {"rect_fixtures": len(fixture_labels), "lumens_each": 1200, "sun": 0.30, "sky": 0.20, "exposure_bias": -0.50},
    "records": records,
}, indent=2), encoding="utf-8")
unreal.log("PRESSSHOP_2126_V002_CLEAN_MESHY_BUILD_PASS")
