"""Build an isolated native-Unreal review level for the square Meshy press train.

This script creates a new candidate map only. It never opens, edits or saves an
existing factory level.
"""
import json
import math
from pathlib import Path

import unreal

PROJECT = Path(r"C:\Users\greg_\Projects\LineBossCarFactory_Unreal 5.8")
ROOT = "/Game/LineBoss/Candidates/PressShop/SquareMeshyPressTrain_v001"
MAP = ROOT + "/Maps/LB_SquareMeshyPressTrain_Review_v010"
REPORT = PROJECT / "Saved" / "Audits" / "PressShopIntegration" / "square_meshy_press_train_review_v010.json"
TAG = unreal.Name("LB.PressShop.SquareMeshy.V001.Review")
PRESS = {
    # +Y is material flow and -X is the operator facade.  The imported Meshy
    # sources had mixed native headings; these yaw values make the whole train
    # follow the project authority rather than simply looking aligned in one
    # preview camera.
    "S02 Draw/Form": (ROOT + "/SM_LB_PS_S02_DrawForm_MeshyClean_v001", (0.0, 1000.0, 0.0), 90.0),
    "S03 Trim": (ROOT + "/SM_LB_PS_S03_Trim_MeshyClean_v001", (0.0, 3600.0, 0.0), 180.0),
    "S04 Pierce": (ROOT + "/SM_LB_PS_S04_Pierce_MeshyClean_v001", (0.0, 5600.0, 0.0), 90.0),
    "S05 Flange/Hem": (ROOT + "/SM_LB_PS_S05_FlangeHem_MeshyClean_v001", (0.0, 7600.0, 0.0), 180.0),
    "S06 Vision/Outfeed": (ROOT + "/SM_LB_PS_S06_VisionOutfeed_MeshyClean_v001", (0.0, 9600.0, 0.0), 180.0),
}
COILS = {
    "Bare coil (project asset)": "/Game/LineBoss/IndustrialKit/MaterialHandling/BareCoil/Candidate_v021/SM_LB_BareMasterCoil_v021",
    "Wrapped coil (project asset)": "/Game/LineBoss/Candidates/PressShop/CleanRebuild_v20260809_v004/Inbound/SM_CA_MW_WrappedCoil_Repaired_v003",
}
CONVEYOR_FRAME = "/Game/LineBoss/Factory/OneFactory/v001/Native/Press/MaterialFlowPack_v002/Meshes/SM_CA_MW_PT_S07ExitConveyorFrame_v001"
CONVEYOR_BELT = "/Game/LineBoss/Factory/OneFactory/v001/Native/Press/MaterialFlowPack_v002/Meshes/SM_CA_MW_PT_S07ExitConveyorBelt_v001"
CONTEXT = {
    "S01 Decoiler base": "/Game/LineBoss/Factory/OneFactory/v001/Native/Press/MaterialFlowPack_v002/Meshes/SM_CA_MW_PT_S01DecoilerBase_v001",
    "S01 Decoiler spindle": "/Game/LineBoss/Factory/OneFactory/v001/Native/Press/MaterialFlowPack_v002/Meshes/SM_CA_MW_PT_S01DecoilerSpindle_v001",
    "S01 Straightener feed": "/Game/LineBoss/Factory/OneFactory/v001/Native/Press/MaterialFlowPack_v002/Meshes/SM_CA_MW_PT_S01StraightenerFeed_v001",
    "S01 Feed bridge": "/Game/LineBoss/Factory/OneFactory/v001/Native/Press/MaterialFlowPack_v002/Meshes/SM_CA_MW_PT_S01FeedBridge_v001",
    "S07 Inspection cell": "/Game/LineBoss/Factory/OneFactory/v001/Native/Press/MaterialFlowPack_v002/Meshes/SM_CA_MW_PT_S07InspectionCell_v001",
    "S07 Outbound dunnage": "/Game/LineBoss/Factory/OneFactory/v001/Native/Press/MaterialFlowPack_v002/Meshes/SM_CA_MW_PT_S07OutboundDunnage_v001",
    "Overhead crane": "/Game/Meshes/Crane/SM_Crane01",
}
MATERIAL_ROOT = ROOT + "/Materials"
ASSET_TOOLS = unreal.AssetToolsHelpers.get_asset_tools()
MEL = unreal.MaterialEditingLibrary


def fail(message):
    raise RuntimeError("SQUARE_MESHY_PRESS_REVIEW_MAP_FAIL: " + message)


def aim(source, target):
    dx, dy, dz = target.x - source.x, target.y - source.y, target.z - source.z
    horizontal = math.sqrt(dx * dx + dy * dy)
    return unreal.Rotator(
        pitch=math.degrees(math.atan2(dz, horizontal)),
        yaw=math.degrees(math.atan2(dy, dx)),
        roll=0.0,
    )


def make_material(name, rgb, roughness):
    path = MATERIAL_ROOT + "/" + name
    asset = unreal.load_asset(path) if unreal.EditorAssetLibrary.does_asset_exist(path) else None
    # Review materials were already authored on the first candidate pass.  Do
    # not rewrite them while creating a later map: every review map needs to be
    # independently reproducible and prior candidate evidence remains intact.
    if asset is not None:
        if not isinstance(asset, unreal.Material):
            fail("existing review material has the wrong type: " + name)
        return asset
    asset = ASSET_TOOLS.create_asset(name, MATERIAL_ROOT, unreal.Material, unreal.MaterialFactoryNew())
    if not isinstance(asset, unreal.Material):
        fail("could not create review material " + name)
    if hasattr(MEL, "delete_all_material_expressions"):
        MEL.delete_all_material_expressions(asset)
    colour = MEL.create_material_expression(asset, unreal.MaterialExpressionConstant3Vector, -300, -100)
    colour.set_editor_property("constant", unreal.LinearColor(rgb[0], rgb[1], rgb[2], 1.0))
    rough = MEL.create_material_expression(asset, unreal.MaterialExpressionConstant, -300, 60)
    rough.set_editor_property("r", roughness)
    MEL.connect_material_property(colour, "", unreal.MaterialProperty.MP_BASE_COLOR)
    MEL.connect_material_property(rough, "", unreal.MaterialProperty.MP_ROUGHNESS)
    MEL.recompile_material(asset)
    unreal.EditorAssetLibrary.save_loaded_asset(asset, only_if_is_dirty=False)
    return asset


def spawn(cls, location, label, rotation=None):
    actor = unreal.EditorLevelLibrary.spawn_actor_from_class(cls, unreal.Vector(*location), rotation or unreal.Rotator())
    if actor is None:
        fail("could not spawn " + label)
    actor.tags = [TAG, unreal.Name("LB.Environment.VisualOnly"), unreal.Name("LB.NotProcessWIP")]
    actor.set_actor_label(label)
    return actor


def mesh_actor(label, mesh, location, rotation=0.0, material=None, scale=None):
    actor = spawn(
        unreal.StaticMeshActor,
        location,
        label,
        unreal.Rotator(pitch=0.0, yaw=rotation, roll=0.0),
    )
    component = actor.static_mesh_component
    component.set_static_mesh(mesh)
    if material:
        component.set_material(0, material)
    if scale:
        component.set_world_scale3d(unreal.Vector(*scale))
    return actor


if unreal.EditorAssetLibrary.does_asset_exist(MAP):
    fail("review map already exists; refusing to overwrite it")
press_meshes = {label: unreal.load_asset(path) for label, (path, _, _) in PRESS.items()}
coil_meshes = {label: unreal.load_asset(path) for label, path in COILS.items()}
context_meshes = {label: unreal.load_asset(path) for label, path in CONTEXT.items()}
conveyor_frame = unreal.load_asset(CONVEYOR_FRAME)
conveyor_belt = unreal.load_asset(CONVEYOR_BELT)
plane = unreal.load_asset("/Engine/BasicShapes/Plane")
cube = unreal.load_asset("/Engine/BasicShapes/Cube")
if not isinstance(plane, unreal.StaticMesh) or not isinstance(cube, unreal.StaticMesh):
    fail("Engine basic shapes unavailable")
if any(not isinstance(mesh, unreal.StaticMesh) for mesh in press_meshes.values()):
    fail("one or more imported press meshes are unavailable")
if any(not isinstance(mesh, unreal.StaticMesh) for mesh in coil_meshes.values()):
    fail("approved bare/wrapped project coil assets are unavailable")
if any(not isinstance(mesh, unreal.StaticMesh) for mesh in context_meshes.values()):
    fail("one or more audited native press-context assets are unavailable")
if not isinstance(conveyor_frame, unreal.StaticMesh) or not isinstance(conveyor_belt, unreal.StaticMesh):
    fail("approved project exit-conveyor assets are unavailable")
if not unreal.EditorLevelLibrary.new_level(MAP):
    fail("could not create new review level")
world = unreal.EditorLevelLibrary.get_editor_world()
if world is None or world.get_name() != MAP.rsplit("/", 1)[-1]:
    fail("new review map did not become active")

floor_mat = make_material("M_LB_PS_ReviewFloor", (0.18, 0.20, 0.21), 0.64)
zone_mat = make_material("M_LB_PS_ReviewZone", (0.28, 0.43, 0.39), 0.62)
lane_mat = make_material("M_LB_PS_ReviewLane", (0.78, 0.74, 0.62), 0.55)
# A fresh, brighter review-only wall material is used here rather than mutating
# the v009 material, so earlier evidence stays reproducible.
wall_mat = make_material("M_LB_PS_ReviewWarmWall_v002", (0.72, 0.70, 0.64), 0.68)
green_mat = unreal.load_asset(MATERIAL_ROOT + "/M_LB_PS_CairnwellGreen")
charcoal_mat = unreal.load_asset(MATERIAL_ROOT + "/M_LB_PS_FoundryCharcoal")
steel_mat = unreal.load_asset(MATERIAL_ROOT + "/M_LB_PS_SteelGrey")
yellow_mat = unreal.load_asset(MATERIAL_ROOT + "/M_LB_PS_SafetyYellow")
if any(asset is None for asset in (green_mat, charcoal_mat, steel_mat, yellow_mat)):
    fail("native candidate palette is unavailable")
mesh_actor("SquareMeshyPressTrain_ReviewFloor", plane, (0.0, 5500.0, -1.0), material=floor_mat, scale=(90.0, 240.0, 1.0))

# The isolated review needs enough enclosing architecture to judge the art as
# a factory rather than objects floating in a black void. These deliberately
# plain, warm-white modular walls and roof are native Unreal cubes, created
# only in this candidate map; they do not alter any protected production level.
mesh_actor("Review hall service wall", cube, (3400.0, 5500.0, 900.0), material=wall_mat, scale=(0.20, 130.0, 9.0))
mesh_actor("Review hall inbound wall", cube, (0.0, -7500.0, 900.0), material=wall_mat, scale=(34.0, 0.20, 9.0))
mesh_actor("Review hall outbound wall", cube, (0.0, 18500.0, 900.0), material=wall_mat, scale=(34.0, 0.20, 9.0))
mesh_actor("Review hall roof", cube, (0.0, 5500.0, 1800.0), material=wall_mat, scale=(34.0, 130.0, 0.16))

# Large painted zones and cream lanes are deliberate visual-language elements,
# not texture detail. They are planes raised 1 cm above the review floor.
for index, (label, (_, location, _)) in enumerate(PRESS.items()):
    mesh_actor("Zone_" + label.replace("/", "_"), cube, (0.0, location[1], 1.0), material=zone_mat, scale=(7.2, 13.5, 0.012))
    mesh_actor("Lane_" + label.replace("/", "_"), cube, (-740.0, location[1], 2.5), material=lane_mat, scale=(0.16, 13.5, 0.016))

for label, (path, location, yaw) in PRESS.items():
    mesh_actor(label, press_meshes[label], location, yaw)

# Project-approved conveyor pieces replace any urge to make more raw-Meshy
# rollers.  The frame and belt remain two separate reusable static-mesh actors;
# their old blue slot is overridden per instance with Cairnwell green.
for index, y in enumerate((-250.0, 2300.0, 4600.0, 6600.0, 8600.0, 10800.0), start=1):
    frame = mesh_actor("Reused conveyor frame %02d" % index, conveyor_frame, (0.0, y, 0.0), 0.0, scale=(1.0, 1.35, 1.0))
    frame_component = frame.static_mesh_component
    for slot, material in enumerate((green_mat, charcoal_mat, steel_mat, steel_mat, yellow_mat, green_mat)):
        frame_component.set_material(slot, material)
    belt = mesh_actor("Reused conveyor belt %02d" % index, conveyor_belt, (0.0, y, 0.0), 0.0, material=charcoal_mat, scale=(1.0, 1.35, 1.0))

# Reuse only the approved project coil props, explicitly separate from the
# press meshes. The pair makes material intake readable without adding a coil
# to any generated machine.
mesh_actor("Bare project coil - separate actor", coil_meshes["Bare coil (project asset)"], (950.0, -3650.0, 0.0), 0.0)
mesh_actor("Wrapped project coil - separate actor", coil_meshes["Wrapped coil (project asset)"], (-1150.0, -4200.0, 0.0), 0.0)

# Reuse the audited upstream/downstream equipment whole, not a new generated
# approximation.  The coils above remain intentionally independent actors;
# they are not embedded in or welded onto the decoiler.
mesh_actor("S01 Decoiler base - reused", context_meshes["S01 Decoiler base"], (0.0, -3000.0, 0.0), 0.0)
mesh_actor("S01 Decoiler spindle - reused", context_meshes["S01 Decoiler spindle"], (0.0, -3000.0, 0.0), 0.0)
mesh_actor("S01 Straightener feed - reused", context_meshes["S01 Straightener feed"], (0.0, -1350.0, 0.0), 0.0)
mesh_actor("S01 Feed bridge - reused", context_meshes["S01 Feed bridge"], (0.0, -650.0, 0.0), 0.0)
mesh_actor("S07 Inspection cell - reused", context_meshes["S07 Inspection cell"], (0.0, 12100.0, 0.0), 0.0)
mesh_actor("S07 Outbound dunnage - reused", context_meshes["S07 Outbound dunnage"], (0.0, 14600.0, 0.0), 0.0)
crane = mesh_actor("Simplified overhead crane silhouette - reused", context_meshes["Overhead crane"], (0.0, 5600.0, 1360.0), 0.0, scale=(0.82, 3.0, 0.82))
crane.static_mesh_component.set_material(0, yellow_mat)
crane.static_mesh_component.set_material(1, charcoal_mat)

# The B_stylized reference establishes the colour temperature, sun/sky values
# and -0.50 exposure. Its literal six 1200-lumen fixtures serve an isolated
# test hall only.  This 240 x 90 m review bay needs density-scaled fixtures to
# be readable at the same locked exposure. Real-RHI tests at 20,000 and then
# 4,000 lm per fixture washed out the palette. This v007 candidate therefore
# uses the approved 1,200-lumen fixture value at 24 coverage locations. It
# retains the reference unit's approved value while adapting only its spatial
# density to the review bay. That is a measured correction, not a new art
# direction.
# All lights are movable so this candidate map never asks for a static-light
# build and its review status is obvious in a normal editor session.
sun = spawn(unreal.DirectionalLight, (0.0, 5500.0, 3000.0), "B_stylized_Sun")
sun.light_component.set_editor_property("intensity", 0.30)
sun.light_component.set_editor_property("mobility", unreal.ComponentMobility.MOVABLE)
sun.light_component.set_editor_property("use_temperature", True)
sun.light_component.set_editor_property("temperature", 5000.0)
sun.set_actor_rotation(unreal.Rotator(pitch=-35.0, yaw=-28.0, roll=0.0), False)
sun.light_component.set_editor_property("atmosphere_sun_light", True)
spawn(unreal.SkyAtmosphere, (0.0, 5500.0, 0.0), "B_stylized_SkyAtmosphere")
sky = spawn(unreal.SkyLight, (0.0, 5500.0, 2200.0), "B_stylized_Sky")
sky.light_component.set_editor_property("intensity", 0.20)
sky.light_component.set_editor_property("mobility", unreal.ComponentMobility.MOVABLE)
sky.light_component.set_editor_property("real_time_capture", True)
fixture_locations = []
# The train is authored along +Y.  Pair the 1,200-lumen fixtures across X and
# repeat their coverage down the material path, rather than carrying forward
# the temporary v007 X-row arrangement.
for y in (-5000.0, -3200.0, -1400.0, 400.0, 2200.0, 4000.0, 5800.0, 7600.0, 9400.0, 11200.0, 13000.0, 14800.0):
    for x in (-1200.0, 1200.0):
        fixture_locations.append((x, y))
for index, (x, y) in enumerate(fixture_locations, start=1):
    light = spawn(unreal.RectLight, (x, y, 1600.0), "B_stylized_CoverageFixture_%02d" % index)
    light.light_component.set_editor_property("mobility", unreal.ComponentMobility.MOVABLE)
    light.light_component.set_editor_property("intensity", 1200.0)
    light.light_component.set_editor_property("intensity_units", unreal.LightUnits.LUMENS)
    light.light_component.set_editor_property("source_width", 850.0)
    light.light_component.set_editor_property("source_height", 500.0)
    light.light_component.set_editor_property("use_temperature", True)
    light.light_component.set_editor_property("temperature", 5000.0)
    light.light_component.set_editor_property("attenuation_radius", 3000.0)
    light.set_actor_rotation(aim(light.get_actor_location(), unreal.Vector(0.0, y, 140.0)), False)

post = spawn(unreal.PostProcessVolume, (0.0, 5500.0, 300.0), "B_stylized_Exposure")
post.set_editor_property("unbound", True)
settings = post.get_editor_property("settings")
settings.override_auto_exposure_bias = True
settings.auto_exposure_bias = -0.50
post.set_editor_property("settings", settings)

overview_camera = spawn(unreal.CameraActor, (-15500.0, -8500.0, 8500.0), "SquareMeshyPressTrain_FlowOverviewCamera")
overview_camera.set_actor_rotation(aim(overview_camera.get_actor_location(), unreal.Vector(0.0, 5500.0, 350.0)), False)
overview_camera.camera_component.set_editor_property("field_of_view", 44.0)

# The hero frame is intentionally closer. It proves surface treatment,
# press-language, overhead handling and the operator-side facade; it is not a
# claim that one Steam screenshot should show the entire 190 m flow line.
camera = spawn(unreal.CameraActor, (-4000.0, 1500.0, 1100.0), "SquareMeshyPressTrain_ManagementHeroCamera")
camera.set_actor_rotation(aim(camera.get_actor_location(), unreal.Vector(0.0, 5800.0, 340.0)), False)
camera.camera_component.set_editor_property("field_of_view", 58.0)
unreal.EditorLevelLibrary.set_level_viewport_camera_info(camera.get_actor_location(), camera.get_actor_rotation())

unreal.EditorLevelLibrary.save_current_level()
report = {
    "status": "PASS__ISOLATED_NATIVE_UNREAL_REVIEW_LEVEL_CREATED__DYNAMIC_COVERAGE_LIGHTING",
    "map": MAP,
    "presses": {label: {"asset": path, "location_cm": location, "yaw": yaw} for label, (path, location, yaw) in PRESS.items()},
    "coils": {"bare": COILS["Bare coil (project asset)"], "wrapped": COILS["Wrapped coil (project asset)"], "attached_to_generated_press": False},
    "conveyors": {"frame": CONVEYOR_FRAME, "belt": CONVEYOR_BELT, "count": 6, "use": "separate project-native reused actors; no new roller mesh generated for the review line"},
    "orientation": {"material_flow": "+Y", "operator_facade": "-X", "press_heading_compensation": "per-source yaw values are applied only at placement so all five candidate machines follow the documented factory convention"},
    "context": {
        "assets": CONTEXT,
        "use": "existing native Unreal upstream, downstream and overhead assets are assembled whole in this candidate map; no replacement geometry was generated",
        "coil_agv": "excluded from this candidate review because the asset audit measured 1,984,003 triangles; retain as a visual reference pending a runtime-ready LOD profile",
    },
    "review_architecture": "candidate-only native Unreal cube walls and roof provide neutral warm-white factory context; production map and protected recovery map were not opened, altered, or saved",
    "cameras": {
        "flow_overview": "documents the whole +Y material path",
        "management_hero": "human-scale operator-side review shot focused on the central S03-S05 sequence, overhead crane and readable finish",
    },
    "lighting": {
        "profile": "B_stylized colour/exposure calibration with coverage-scaled movable fixtures",
        "reference_fixture_count": 6,
        "reference_fixture_lumens": 1200,
        "fixture_count": len(fixture_locations),
        "fixture_lumens": 1200,
        "fixture_temperature_kelvin": 5000,
        "all_lights_movable": True,
        "scaling_reason": "240 x 90 m review bay requires fixture density appropriate to its area and 15 m mount height while retaining the approved B_stylized sun, sky, temperature and exposure values",
        "sun": 0.30,
        "sky": 0.20,
        "exposure_bias": -0.50,
    },
    "map_isolation": "new candidate map only; no existing map was loaded, altered, or saved",
    "next_gate": "real-RHI visual capture and human approval before any production-map placement."
}
REPORT.parent.mkdir(parents=True, exist_ok=True)
REPORT.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
unreal.log("LINE_BOSS_SQUARE_MESHY_PRESS_REVIEW_LEVEL=" + json.dumps(report, sort_keys=True))
