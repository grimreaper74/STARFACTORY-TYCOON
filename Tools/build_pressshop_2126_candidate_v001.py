"""Build the fresh roofless 2126 Press Shop candidate using native Unreal forms.

This is intentionally a new map, not a clone of a prior press layout.  The
layout turns proven near-future production concepts into a readable 2126 game
space: coil staging -> adaptive laser blanking -> four open servo presses ->
vision/stacking.  It creates no roof surfaces and no wall liners.
"""
from pathlib import Path
import json
import math
import unreal

PROJECT = Path(r"C:\Users\greg_\Projects\LineBossCarFactory_Unreal 5.8")
MAP = "/Game/LineBoss/Candidates/PressShop/PressShop2126_v001/Maps/LB_PressShop_2126_Steam_v001"
ROOT = "/Game/LineBoss/Candidates/PressShop/PressShop2126_v001"
MATERIAL_ROOT = ROOT + "/Materials"
REPORT = PROJECT / "Saved" / "Audits" / "PressShopIntegration" / "pressshop_2126_build_v001.json"
TAG = unreal.Name("LB.PressShop.2126.v001")
ASSET_TAG = unreal.Name("LB.Asset.Candidate")
STYLE_TAG = unreal.Name("LB.Visual.2126")

BRAND = {
    "foundry": (0.015, 0.017, 0.021),       # #202428 in linear-ish authored values
    "steel": (0.162, 0.184, 0.205),          # #70777C readable in the viewport
    "green": (0.014, 0.070, 0.057),          # Cairnwell Green #1F4B44
    "yellow": (0.887, 0.547, 0.0),           # Safety Yellow #F2C300
    "red": (0.571, 0.036, 0.025),            # Signal Red #C7352C
    "cream": (0.896, 0.880, 0.806),          # Warm White #F3F1E9
    "pale_green": (0.220, 0.430, 0.310),
    "cyan": (0.015, 0.280, 0.410),
}


def fail(message):
    raise RuntimeError("PRESSSHOP_2126_BUILD_FAIL: " + message)


def aim(source, target):
    dx, dy, dz = target.x - source.x, target.y - source.y, target.z - source.z
    flat = math.sqrt(dx * dx + dy * dy)
    return unreal.Rotator(
        pitch=math.degrees(math.atan2(dz, flat)),
        yaw=math.degrees(math.atan2(dy, dx)),
        roll=0.0,
    )


def create_material(name, colour, roughness=0.55, metallic=0.0, emissive=0.0):
    path = MATERIAL_ROOT + "/" + name
    material = unreal.load_asset(path) if unreal.EditorAssetLibrary.does_asset_exist(path) else None
    if material is None:
        material = unreal.AssetToolsHelpers.get_asset_tools().create_asset(
            name, MATERIAL_ROOT, unreal.Material, unreal.MaterialFactoryNew())
    if not isinstance(material, unreal.Material):
        fail("could not make material " + name)
    mel = unreal.MaterialEditingLibrary
    mel.delete_all_material_expressions(material)
    base = mel.create_material_expression(material, unreal.MaterialExpressionConstant3Vector, -360, -140)
    base.set_editor_property("constant", unreal.LinearColor(colour[0], colour[1], colour[2], 1.0))
    rough = mel.create_material_expression(material, unreal.MaterialExpressionConstant, -360, -40)
    rough.set_editor_property("r", roughness)
    metal = mel.create_material_expression(material, unreal.MaterialExpressionConstant, -360, 60)
    metal.set_editor_property("r", metallic)
    mel.connect_material_property(base, "", unreal.MaterialProperty.MP_BASE_COLOR)
    mel.connect_material_property(rough, "", unreal.MaterialProperty.MP_ROUGHNESS)
    mel.connect_material_property(metal, "", unreal.MaterialProperty.MP_METALLIC)
    if emissive > 0.0:
        emit = mel.create_material_expression(material, unreal.MaterialExpressionMultiply, -130, -140)
        power = mel.create_material_expression(material, unreal.MaterialExpressionConstant, -360, -220)
        power.set_editor_property("r", emissive)
        mel.connect_material_expressions(base, "", emit, "A")
        mel.connect_material_expressions(power, "", emit, "B")
        mel.connect_material_property(emit, "", unreal.MaterialProperty.MP_EMISSIVE_COLOR)
    mel.recompile_material(material)
    unreal.EditorAssetLibrary.save_loaded_asset(material, only_if_is_dirty=False)
    return material


def spawn_mesh(label, mesh, location, scale=(1.0, 1.0, 1.0), material=None, rotation=None, tags=()):
    actor = unreal.EditorLevelLibrary.spawn_actor_from_class(
        unreal.StaticMeshActor, unreal.Vector(*location), rotation or unreal.Rotator())
    if actor is None:
        fail("could not spawn " + label)
    actor.set_actor_label(label)
    actor.tags = [TAG, ASSET_TAG, STYLE_TAG] + list(tags)
    comp = actor.static_mesh_component
    comp.set_static_mesh(mesh)
    comp.set_world_scale3d(unreal.Vector(*scale))
    if material is not None:
        comp.set_material(0, material)
    return actor


def box(label, loc, dims, material, yaw=0.0, tags=()):
    return spawn_mesh(label, CUBE, loc, tuple(value / 100.0 for value in dims), material,
                      unreal.Rotator(pitch=0.0, yaw=yaw, roll=0.0), tags)


def cylinder(label, loc, dims, material, pitch=0.0, yaw=0.0, tags=()):
    return spawn_mesh(label, CYLINDER, loc, tuple(value / 100.0 for value in dims), material,
                      unreal.Rotator(pitch=pitch, yaw=yaw, roll=0.0), tags)


def collect(actor, role):
    location = actor.get_actor_location()
    result = {
        "label": actor.get_actor_label(),
        "role": role,
        "location_cm": [round(location.x), round(location.y), round(location.z)],
    }
    RECORDS.append(result)
    return actor


def press(station, x, height, width, depth, identity):
    """Build one distinct open-sided servo press around a large visible die bay."""
    root = unreal.Name("LB.PressShop.2126." + station)
    base_h = 360.0
    col_w = 360.0
    # Wide, positive painted base with four distinct bodies above it.
    collect(box(station + " | low plinth", (x, 0, base_h / 2), (depth, width, base_h), mats["charcoal"], tags=(root,)), station)
    collect(box(station + " | cream service deck", (x, 0, base_h + 42), (depth * .87, width * .83, 84), mats["cream"], tags=(root,)), station)
    # Columns sit on the flow axis: viewed from the operator side (-Y), they
    # frame rather than wall off the die aperture.
    for side in (-1, 1):
        collect(box(station + " | open portal column " + str(side),
                    (x + side * (depth / 2 - col_w / 2), 0, (height + base_h) / 2),
                    (col_w, width * .72, height - base_h), mats["green"], tags=(root,)), station)
        collect(box(station + " | yellow column spine " + str(side),
                    (x + side * (depth / 2 - col_w / 2) - side * 198, -width * .39, (height + base_h) / 2),
                    (70, 90, height - base_h - 240), mats["yellow"], tags=(root,)), station)
    collect(box(station + " | cream crown", (x, 0, height - 340), (depth + 260, width, 680), mats["cream"], tags=(root,)), station)
    collect(box(station + " | green crown band", (x, -width * .38, height - 750), (depth + 160, 180, 280), mats["green"], tags=(root,)), station)
    collect(box(station + " | servo ram", (x, 0, height - 1150), (depth * .42, width * .48, 430), mats["steel"], tags=(root,)), station)
    collect(box(station + " | visible die", (x, 0, 740), (depth * .54, width * .50, 210), mats["steel"], tags=(root,)), station)
    collect(box(station + " | die halo", (x, -width * .30, 810), (depth * .60, 56, 240), mats["yellow"], tags=(root,)), station)
    # Big semantic status slab: intentionally readable at management camera.
    collect(box(station + " | digital status slab", (x - depth * .34, -width * .48, height * .64),
                (280, 52, 520), mats["data"], tags=(root,)), station)

    if identity == "twin":
        # Tallest: two obvious accumulator towers.
        for side in (-1, 1):
            collect(cylinder(station + " | twin accumulator " + str(side),
                             (x + side * (depth * .28), width * .30, height + 720),
                             (410, 410, 1420), mats["green"], tags=(root,)), station)
            collect(cylinder(station + " | accumulator cap " + str(side),
                             (x + side * (depth * .28), width * .30, height + 1450),
                             (450, 450, 80), mats["yellow"], tags=(root,)), station)
    elif identity == "canopy":
        # Low/wide trim array: a single clearly overhanging canopy.
        collect(box(station + " | broad trim canopy", (x, -width * .07, height + 120),
                    (depth + 1000, width + 920, 310), mats["yellow"], tags=(root,)), station)
        collect(box(station + " | scrap skirt", (x + depth * .43, 0, 770),
                    (140, width * .92, 630), mats["charcoal"], tags=(root,)), station)
    elif identity == "spine":
        # Tall/narrow pierce cell: one vertical servo/control spine.
        collect(box(station + " | top servo spine", (x, 0, height + 1250),
                    (520, 1040, 2500), mats["green"], tags=(root,)), station)
        collect(box(station + " | servo spine cap", (x, 0, height + 2580),
                    (700, 1220, 190), mats["yellow"], tags=(root,)), station)
    elif identity == "bridge":
        # Wide split press: two outward-facing edge-form arms.
        for side in (-1, 1):
            collect(box(station + " | edge form arm " + str(side),
                        (x + side * (depth * .62), 0, height * .43),
                        (600, width * .70, 380), mats["yellow"], tags=(root,)), station)
            collect(cylinder(station + " | edge servo " + str(side),
                             (x + side * (depth * .72), 0, height * .43),
                             (520, 520, 760), mats["steel"], pitch=0.0, tags=(root,)), station)


def station_marker(label, x, y, colour):
    collect(box(label + " | floor identifier", (x, y, 18), (3000, 420, 30), colour), label)
    collect(box(label + " | data pylon", (x, y, 850), (230, 230, 1640), mats["data"]), label)


if not unreal.EditorAssetLibrary.does_asset_exist(MAP):
    fail("fresh map missing; run create_pressshop_2126_candidate_v001.py first")
if not unreal.EditorLoadingAndSavingUtils.load_map(MAP):
    fail("could not load fresh 2126 candidate map")
if any(TAG in actor.tags for actor in unreal.EditorLevelLibrary.get_all_level_actors()):
    fail("build tag already present; refusing to duplicate the 2126 layout")

CUBE = unreal.load_asset("/Engine/BasicShapes/Cube")
CYLINDER = unreal.load_asset("/Engine/BasicShapes/Cylinder")
if not isinstance(CUBE, unreal.StaticMesh) or not isinstance(CYLINDER, unreal.StaticMesh):
    fail("native Unreal basic-shape meshes are unavailable")

coil_wrapped = unreal.load_asset("/Game/LineBoss/IndustrialKit/MaterialHandling/MasterCoil/Candidate_v005/SM_LB_MasterCoil_Candidate_v005")
coil_bare = unreal.load_asset("/Game/LineBoss/IndustrialKit/MaterialHandling/BareCoil/Candidate_v021/SM_LB_BareMasterCoil_v021")
if not isinstance(coil_wrapped, unreal.StaticMesh) or not isinstance(coil_bare, unreal.StaticMesh):
    fail("the approved project coil meshes are unavailable")

mats = {
    "floor": create_material("M_LB_PS2126_Floor", BRAND["foundry"], 0.72),
    "green": create_material("M_LB_PS2126_CairnwellGreen", BRAND["green"], 0.48, .18),
    "yellow": create_material("M_LB_PS2126_SafetyYellow", BRAND["yellow"], 0.44, .10),
    "cream": create_material("M_LB_PS2126_WarmWhite", BRAND["cream"], 0.62, .04),
    "steel": create_material("M_LB_PS2126_SteelGrey", BRAND["steel"], 0.38, .62),
    "charcoal": create_material("M_LB_PS2126_FoundryCharcoal", BRAND["foundry"], 0.46, .38),
    "pale_green": create_material("M_LB_PS2126_PaintedPaleGreen", BRAND["pale_green"], 0.78),
    "lane": create_material("M_LB_PS2126_CreamLane", BRAND["cream"], 0.70),
    "data": create_material("M_LB_PS2126_OpticalCyan", BRAND["cyan"], 0.25, .10, 4.5),
    "red": create_material("M_LB_PS2126_StatusRed", BRAND["red"], 0.38, .10, 2.5),
}
RECORDS = []

# A large open deck: important visual read is broad colour blocks, not a forest
# of yellow micro-stripes.  It has no exterior wall/roof geometry.
collect(box("2126 | continuous open factory deck", (3100, 0, -80), (47000, 16800, 160), mats["floor"]), "floor")
for x, length in ((-12400, 6600), (-4000, 5800), (2600, 5600), (9100, 6000), (16000, 5200)):
    collect(box("2126 | pale green process zone " + str(x), (x, 0, 8), (length, 6800, 28), mats["pale_green"]), "floor_zone")
collect(box("2126 | cream operator avenue", (3100, -5200, 18), (46000, 1350, 36), mats["lane"]), "floor_lane")
collect(box("2126 | cream service avenue", (3100, 5200, 18), (46000, 1000, 36), mats["lane"]), "floor_lane")

# Sparse roofless portal structure: edge columns and longitudinal rail only.
# There are deliberately no cross-beams or surface panels over the machines.
for x in (-17600, -12200, -6800, -1400, 4000, 9400, 14800, 20200, 24800):
    for y in (-7600, 7600):
        collect(box("2126 | open-bay structural mast %.0f %.0f" % (x, y), (x, y, 4900),
                    (340, 340, 9800), mats["steel"]), "open_structure")
        collect(box("2126 | mast safety base %.0f %.0f" % (x, y), (x, y, 220),
                    (620, 620, 180), mats["yellow"]), "open_structure")
for y in (-7600, 7600):
    collect(box("2126 | open-bay longitudinal gantry rail " + str(y), (3500, y, 9200),
                (44000, 260, 260), mats["steel"]), "open_structure")

# INBOUND: visible project coil assets sit on simple induction carriers.  No
# generated machine duplicates their geometry and no wheels are invented.
for idx, (x, mesh, name) in enumerate(((-15400, coil_wrapped, "wrapped master coil"), (-13200, coil_bare, "bare master coil"))):
    collect(box("S00 | guided induction carrier " + str(idx), (x, 0, 260), (2200, 3600, 500), mats["green"]), "coil_carrier")
    collect(box("S00 | carrier warm-white lift pad " + str(idx), (x, 0, 540), (1320, 2380, 90), mats["cream"]), "coil_carrier")
    collect(cylinder("S00 | field pad left " + str(idx), (x, -1180, 610), (440, 440, 170), mats["data"]), "coil_carrier")
    collect(cylinder("S00 | field pad right " + str(idx), (x, 1180, 610), (440, 440, 170), mats["data"]), "coil_carrier")
    collect(spawn_mesh("S00 | approved " + name, mesh, (x, 0, 850), (1.0, 1.0, 1.0), None,
                        unreal.Rotator(pitch=0.0, yaw=90.0, roll=0.0), (unreal.Name("LB.Reused.ProjectCoil"),)), "project_coil")

# Laser blanking / conditioning portal (informed by Schuler's modular direct
# coil-to-blank work). It is intentionally a large readable square portal.
laser_x = -9300
collect(box("S01 | laser blanking base", (laser_x, 0, 260), (3600, 5300, 520), mats["charcoal"]), "laser_blank")
for side in (-1, 1):
    collect(box("S01 | laser portal leg " + str(side), (laser_x, side * 2150, 2500),
                (620, 520, 4500), mats["cream"]), "laser_blank")
collect(box("S01 | laser blanking optical gantry", (laser_x, 0, 4620), (4100, 5000, 650), mats["green"]), "laser_blank")
collect(box("S01 | laser blanking cyan aperture", (laser_x, -2510, 4200), (2750, 70, 260), mats["data"]), "laser_blank")
for y in (-1150, 1150):
    collect(box("S01 | laser head " + str(y), (laser_x, y, 3700), (300, 360, 540), mats["yellow"]), "laser_blank")
collect(box("S01 | flat stock bridge", (-6500, 0, 820), (2300, 1650, 300), mats["steel"]), "laser_blank")
station_marker("S01 | adaptive laser blanking", laser_x, -4150, mats["yellow"])

# THE LINE: each press has a deliberately different macro silhouette, while
# preserving a shared open die-window language and a single flow direction.
press("S02 Draw Nexus", -3000, 7000, 5100, 3500, "twin")
press("S03 Trim Array", 2600, 5200, 6100, 4000, "canopy")
press("S04 Pierce Cell", 8500, 7100, 4600, 3300, "spine")
press("S05 Edge Forge", 14500, 5650, 6200, 3900, "bridge")
for station, x in (("S02 | Draw", -3000), ("S03 | Trim", 2600), ("S04 | Pierce", 8500), ("S05 | Edge", 14500)):
    station_marker(station, x, -4100, mats["yellow"])

# A simple overhead crossbar spine replaces the generic roller-bed language:
# open, visible, compact, and plausibly evolved from current Crossbar Feeder
# technology. It is transfer-only, not an invented enclosed roof.
collect(box("S02-S05 | overhead transfer spine A", (5600, -1250, 8400), (19200, 240, 240), mats["steel"]), "transfer")
collect(box("S02-S05 | overhead transfer spine B", (5600, 1250, 8400), (19200, 240, 240), mats["steel"]), "transfer")
for x in (-400, 5200, 10900):
    collect(box("transfer | crossbar bridge " + str(x), (x, 0, 8200), (290, 3900, 250), mats["cream"]), "transfer")
    collect(box("transfer | optical pickup " + str(x), (x, 0, 7420), (520, 420, 480), mats["data"]), "transfer")

# OUTBOUND: Vision Stack portal and compact autonomous stacking. This mirrors
# camera/inspection cells already common now, presented as an open 2126 gate.
vision_x = 20400
collect(box("S06 | vision stack deck", (vision_x, 0, 230), (3900, 5700, 460), mats["charcoal"]), "vision_stack")
for side in (-1, 1):
    collect(box("S06 | vision arch leg " + str(side), (vision_x, side * 2150, 2700), (660, 600, 4900), mats["cream"]), "vision_stack")
collect(box("S06 | vision arch crown", (vision_x, 0, 5120), (700, 5000, 680), mats["green"]), "vision_stack")
collect(box("S06 | optical scan plane", (vision_x, -2525, 3760), (2900, 60, 350), mats["data"]), "vision_stack")
collect(box("S06 | autonomous stack cradle", (vision_x + 3900, 0, 530), (3300, 3600, 900), mats["green"]), "vision_stack")
collect(box("S06 | warm-white stack", (vision_x + 3900, 0, 1120), (2300, 2400, 320), mats["cream"]), "vision_stack")
station_marker("S06 | vision and autonomous stack", vision_x, -4150, mats["yellow"])

# Lighting is entirely native and movable; no light build is required before
# review. Broad overhead sources create a readable Steam-camera composition.
sky = unreal.EditorLevelLibrary.spawn_actor_from_class(unreal.SkyLight, unreal.Vector(0, 0, 9000), unreal.Rotator())
sky.set_actor_label("2126 | native skylight")
sky.tags = [TAG, ASSET_TAG, STYLE_TAG]
sky_comp = sky.get_component_by_class(unreal.SkyLightComponent)
sky_comp.set_editor_property("intensity", 1.4)
sky_comp.set_editor_property("mobility", unreal.ComponentMobility.MOVABLE)

sun = unreal.EditorLevelLibrary.spawn_actor_from_class(unreal.DirectionalLight, unreal.Vector(0, 0, 12000), unreal.Rotator(pitch=-38, yaw=-28, roll=0))
sun.set_actor_label("2126 | warm directional sun")
sun.tags = [TAG, ASSET_TAG, STYLE_TAG]
sun_comp = sun.get_component_by_class(unreal.DirectionalLightComponent)
sun_comp.set_editor_property("intensity", 6.0)
sun_comp.set_editor_property("light_color", unreal.Color(255, 219, 171, 255))
sun_comp.set_editor_property("mobility", unreal.ComponentMobility.MOVABLE)

for index, x in enumerate((-12200, -3500, 4500, 12500, 20400)):
    light = unreal.EditorLevelLibrary.spawn_actor_from_class(unreal.RectLight, unreal.Vector(x, -1800, 8200), unreal.Rotator(pitch=-90, yaw=0, roll=0))
    light.set_actor_label("2126 | native softbox " + str(index + 1))
    light.tags = [TAG, ASSET_TAG, STYLE_TAG]
    comp = light.get_component_by_class(unreal.RectLightComponent)
    comp.set_editor_property("intensity", 24000.0)
    comp.set_editor_property("source_width", 3400.0)
    comp.set_editor_property("source_height", 1800.0)
    comp.set_editor_property("light_color", unreal.Color(217, 235, 255, 255))
    comp.set_editor_property("mobility", unreal.ComponentMobility.MOVABLE)

post = unreal.EditorLevelLibrary.spawn_actor_from_class(unreal.PostProcessVolume, unreal.Vector(3000, 0, 2000), unreal.Rotator())
post.set_actor_label("2126 | fixed Steam exposure")
post.tags = [TAG, ASSET_TAG, STYLE_TAG]

# Named review cameras make the three screenshot intents reproducible.
for label, location, target, fov in (
    ("CAM | 2126 Steam hero overview", (-14600, -17600, 7900), (4600, 0, 2600), 56.0),
    ("CAM | 2126 operator line", (-8800, -10200, 3500), (4300, -350, 2500), 48.0),
    ("CAM | 2126 draw nexus", (-6900, -6300, 2900), (-3000, 0, 2700), 52.0),
):
    camera = unreal.EditorLevelLibrary.spawn_actor_from_class(unreal.CineCameraActor, unreal.Vector(*location), aim(unreal.Vector(*location), unreal.Vector(*target)))
    camera.set_actor_label(label)
    camera.tags = [TAG, ASSET_TAG, STYLE_TAG, unreal.Name("LB.SteamReviewCamera")]
    camera.get_cine_camera_component().set_editor_property("current_focal_length", fov)

hero_location = unreal.Vector(-14600, -17600, 7900)
unreal.EditorLevelLibrary.set_level_viewport_camera_info(hero_location, aim(hero_location, unreal.Vector(4600, 0, 2600)))

if not unreal.EditorLevelLibrary.save_current_level():
    fail("Unreal could not save the finished 2126 candidate map")

REPORT.parent.mkdir(parents=True, exist_ok=True)
REPORT.write_text(json.dumps({
    "status": "PASS",
    "map": MAP,
    "candidate_only": True,
    "prior_maps_reused_or_modified": False,
    "meshy_used": False,
    "art_direction": "Open roofless 2126 press foundry; no walls or roof surfaces; native Unreal geometry and lights.",
    "research_basis": [
        {"topic": "direct coil-to-blank laser blanking", "source": "https://laserblanking.schulergroup.com/en/"},
        {"topic": "compact servo press line / automatic tool change", "source": "https://www.schulergroup.com/technologien/produkte/pressenlinien_servo/index.html?sLang=en"},
        {"topic": "open, compact crossbar transfer", "source": "https://www.schulergroup.com/technologien/produkte/verkettung_crossbar_feeder/index.html?sLang=en"},
        {"topic": "digital-twin industrial supervision", "source": "https://www.siemens.com/en-gb/company/digital-twin/comprehensive-digital-twin-for-industry/"}
    ],
    "sequence": ["S00 project coils on guided induction carriers", "S01 laser blanking", "S02 draw", "S03 trim", "S04 pierce", "S05 edge form", "S06 vision and stack"],
    "created_actors": len(RECORDS),
    "records": RECORDS,
}, indent=2), encoding="utf-8")
unreal.log("PRESSSHOP_2126_BUILD_PASS: %d authored forms in %s" % (len(RECORDS), MAP))
