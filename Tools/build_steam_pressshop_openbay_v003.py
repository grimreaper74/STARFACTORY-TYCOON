"""Populate the roofless Steam Press Shop v004 candidate from retained v551.

This is deliberately a candidate-only second pass. The companion
``clone_steam_pressshop_openbay_v004.py`` must have run in a *previous editor
session*, which avoids UE 5.8's duplicate-and-load UWorld leak. This script
then loads the existing clone exactly once and combines the proven lorry /
crane / coil hand-off from v551 with the cleaned, square repair-friendly press
assets and existing native Unreal material-flow pieces.

No roof sheet is created.  The bay keeps only a sparse gantry/rail silhouette
for lighting and overhead automation.  Existing project coils remain where
the story already requires them (lorry, C-hook, AGV); no coil is embedded in a
generated press or duplicated into the new line.
"""
import hashlib
import json
import math
from pathlib import Path

import unreal


PROJECT = Path(r"C:\Users\greg_\Projects\LineBossCarFactory_Unreal 5.8")
SOURCE = "/Game/LineBoss/Developer/Validation/LB_InboundCoilDeliveryInstalledCell_v551"
TARGET = "/Game/LineBoss/Candidates/PressShop/SquareMeshyPressTrain_v001/Maps/LB_PressShop_SteamOpenBay_v004"
SOURCE_FILE = PROJECT / "Content" / "LineBoss" / "Developer" / "Validation" / "LB_InboundCoilDeliveryInstalledCell_v551.umap"
TARGET_FILE = PROJECT / "Content" / "LineBoss" / "Candidates" / "PressShop" / "SquareMeshyPressTrain_v001" / "Maps" / "LB_PressShop_SteamOpenBay_v004.umap"
REPORT = PROJECT / "Saved" / "Audits" / "PressShopIntegration" / "steam_pressshop_openbay_v004.json"

ROOT = "/Game/LineBoss/Candidates/PressShop/SquareMeshyPressTrain_v001"
MATERIAL_ROOT = ROOT + "/Materials"
TAG = unreal.Name("LB.PressShop.SteamOpenBay.v004")
ASSET_TAG = unreal.Name("LB.Asset.Candidate")
VISUAL_TAG = unreal.Name("LB.Environment.VisualOnly")

PRESS = {
    # The original asset headings differ. These transforms retain the older
    # audited +X material-flow compensation while placing the new line after
    # v551's AGV hand-off.
    "S02 Draw / form": (ROOT + "/SM_LB_PS_S02_DrawForm_MeshyClean_v001", (6000.0, 0.0, 0.0), 0.0),
    "S03 Trim": (ROOT + "/SM_LB_PS_S03_Trim_MeshyClean_v001", (8100.0, 0.0, 0.0), 90.0),
    "S04 Pierce": (ROOT + "/SM_LB_PS_S04_Pierce_MeshyClean_v001", (10000.0, 0.0, 0.0), 0.0),
    "S05 Flange / hem": (ROOT + "/SM_LB_PS_S05_FlangeHem_MeshyClean_v001", (11800.0, 0.0, 0.0), 90.0),
    "S06 Vision / outfeed": (ROOT + "/SM_LB_PS_S06_VisionOutfeed_MeshyClean_v001", (13700.0, 0.0, 0.0), 90.0),
}
NATIVE = {
    "S01 decoiler base": "/Game/LineBoss/Factory/OneFactory/v001/Native/Press/MaterialFlowPack_v002/Meshes/SM_CA_MW_PT_S01DecoilerBase_v001",
    "S01 decoiler spindle": "/Game/LineBoss/Factory/OneFactory/v001/Native/Press/MaterialFlowPack_v002/Meshes/SM_CA_MW_PT_S01DecoilerSpindle_v001",
    "S01 straightener and feed": "/Game/LineBoss/Factory/OneFactory/v001/Native/Press/MaterialFlowPack_v002/Meshes/SM_CA_MW_PT_S01StraightenerFeed_v001",
    "S01 feed bridge": "/Game/LineBoss/Factory/OneFactory/v001/Native/Press/MaterialFlowPack_v002/Meshes/SM_CA_MW_PT_S01FeedBridge_v001",
    "S07 inspection": "/Game/LineBoss/Factory/OneFactory/v001/Native/Press/MaterialFlowPack_v002/Meshes/SM_CA_MW_PT_S07InspectionCell_v001",
    "S07 outbound dunnage": "/Game/LineBoss/Factory/OneFactory/v001/Native/Press/MaterialFlowPack_v002/Meshes/SM_CA_MW_PT_S07OutboundDunnage_v001",
    "transfer conveyor frame": "/Game/LineBoss/Factory/OneFactory/v001/Native/Press/MaterialFlowPack_v002/Meshes/SM_CA_MW_PT_S07ExitConveyorFrame_v001",
    "transfer conveyor belt": "/Game/LineBoss/Factory/OneFactory/v001/Native/Press/MaterialFlowPack_v002/Meshes/SM_CA_MW_PT_S07ExitConveyorBelt_v001",
}

# v551's named wall liners block a long open-bay view. They are only hidden in
# the duplicate; the source still keeps every one of them. Roof beams remain
# visible as structural members, but this script creates no roof surface.
HIDE_IN_CLONE = {
    "LB_INBOUND_V051_UpstreamWallLower",
    "LB_INBOUND_V051_UpstreamWallUpper",
    "LB_INBOUND_V051_UpstreamWindowBand",
    "LB_INBOUND_V051_CentreWallLower",
    "LB_INBOUND_V051_CentreWallUpper",
    "LB_INBOUND_V051_CentreWindowBand",
    "LB_INBOUND_V051_DownstreamWallLower",
    "LB_INBOUND_V051_DownstreamWallUpper",
    "LB_INBOUND_V051_DownstreamWindowBand",
    "LB_INBOUND_V051_CentreMullion_01",
    "LB_INBOUND_V051_CentreMullion_02",
    "LB_INBOUND_V051_CentreMullion_03",
    "LB_INBOUND_V051_CentreMullion_04",
    "LB_INBOUND_V051_CentreMullion_05",
    "LB_INBOUND_V051_CentreMullion_06",
    "LB_INBOUND_V051_DownstreamMullion_01",
    "LB_INBOUND_V051_DownstreamMullion_02",
    "LB_INBOUND_V051_DownstreamMullion_03",
    "LB_INBOUND_V051_DownstreamMullion_04",
    "LB_INBOUND_V051_DownstreamMullion_05",
    "LB_INBOUND_V051_DownstreamMullion_06",
    "LB_INBOUND_V051_DownstreamMullion_07",
}


def fail(message):
    raise RuntimeError("STEAM_OPEN_BAY_V004_FAIL: " + message)


def sha256(path):
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def aim(source, target):
    dx, dy, dz = target.x - source.x, target.y - source.y, target.z - source.z
    horizontal = math.sqrt(dx * dx + dy * dy)
    return unreal.Rotator(
        pitch=math.degrees(math.atan2(dz, horizontal)),
        yaw=math.degrees(math.atan2(dy, dx)),
        roll=0.0,
    )


def create_material(name, colour, roughness):
    path = MATERIAL_ROOT + "/" + name
    material = unreal.load_asset(path) if unreal.EditorAssetLibrary.does_asset_exist(path) else None
    if material is not None:
        if not isinstance(material, unreal.Material):
            fail("existing material is the wrong type: " + name)
        return material
    tools = unreal.AssetToolsHelpers.get_asset_tools()
    material = tools.create_asset(name, MATERIAL_ROOT, unreal.Material, unreal.MaterialFactoryNew())
    if not isinstance(material, unreal.Material):
        fail("could not create candidate-only material: " + name)
    mel = unreal.MaterialEditingLibrary
    mel.delete_all_material_expressions(material)
    base = mel.create_material_expression(material, unreal.MaterialExpressionConstant3Vector, -300, -80)
    base.set_editor_property("constant", unreal.LinearColor(colour[0], colour[1], colour[2], 1.0))
    rough = mel.create_material_expression(material, unreal.MaterialExpressionConstant, -300, 70)
    rough.set_editor_property("r", roughness)
    mel.connect_material_property(base, "", unreal.MaterialProperty.MP_BASE_COLOR)
    mel.connect_material_property(rough, "", unreal.MaterialProperty.MP_ROUGHNESS)
    mel.recompile_material(material)
    unreal.EditorAssetLibrary.save_loaded_asset(material, only_if_is_dirty=False)
    return material


def hide_actor(actor):
    actor.set_actor_hidden_in_game(True)
    actor.tags = list(actor.tags) + [unreal.Name("LB.PressShop.OpenBay.HiddenWallV004")]
    for component in actor.get_components_by_class(unreal.PrimitiveComponent):
        component.set_visibility(False, True)


def spawn(cls, label, location, rotation=None, extra_tags=()):
    actor = unreal.EditorLevelLibrary.spawn_actor_from_class(
        cls,
        unreal.Vector(*location),
        rotation or unreal.Rotator(),
    )
    if actor is None:
        fail("could not spawn " + label)
    actor.set_actor_label(label)
    actor.tags = [TAG, ASSET_TAG, VISUAL_TAG] + list(extra_tags)
    return actor


def mesh_actor(label, mesh, location, yaw=0.0, material=None, scale=None, extra_tags=()):
    actor = spawn(
        unreal.StaticMeshActor,
        label,
        location,
        unreal.Rotator(pitch=0.0, yaw=yaw, roll=0.0),
        extra_tags,
    )
    component = actor.static_mesh_component
    component.set_static_mesh(mesh)
    if material is not None:
        component.set_material(0, material)
    if scale is not None:
        component.set_world_scale3d(unreal.Vector(*scale))
    return actor


def set_palette_slots(actor, charcoal, steel, yellow, green):
    # The native conveyor carries several historical slots. Override only its
    # instance, so the reusable shared asset remains untouched.
    for index, material in enumerate((green, charcoal, steel, steel, yellow, green)):
        actor.static_mesh_component.set_material(index, material)


def record(actor, asset=None):
    location = actor.get_actor_location()
    rotation = actor.get_actor_rotation()
    return {
        "label": actor.get_actor_label(),
        "asset": asset.get_path_name() if asset else None,
        "location_cm": [round(location.x, 3), round(location.y, 3), round(location.z, 3)],
        "yaw": round(rotation.yaw, 3),
    }


if not SOURCE_FILE.is_file():
    fail("retained v551 source map is missing")
if not unreal.EditorAssetLibrary.does_asset_exist(TARGET) or not TARGET_FILE.exists():
    fail("v004 clone is missing; run clone_steam_pressshop_openbay_v004.py in a prior editor session first")

source_hash_before = sha256(SOURCE_FILE)
source_mtime_before = SOURCE_FILE.stat().st_mtime_ns

assets = {}
for label, (path, _, _) in PRESS.items():
    asset = unreal.load_asset(path)
    if not isinstance(asset, unreal.StaticMesh):
        fail("missing candidate press: " + label)
    assets[label] = asset
for label, path in NATIVE.items():
    asset = unreal.load_asset(path)
    if not isinstance(asset, unreal.StaticMesh):
        fail("missing approved native asset: " + label)
    assets[label] = asset
cube = unreal.load_asset("/Engine/BasicShapes/Cube")
if not isinstance(cube, unreal.StaticMesh):
    fail("native Unreal cube is unavailable")

if not unreal.EditorLoadingAndSavingUtils.load_map(TARGET):
    fail("could not load the pre-cloned v004 candidate map")

actors = list(unreal.EditorLevelLibrary.get_all_level_actors())
if any(TAG in actor.tags for actor in actors):
    fail("v004 candidate already contains this build tag; refusing duplicate placement")

hidden = []
for actor in actors:
    if actor.get_actor_label() in HIDE_IN_CLONE:
        hide_actor(actor)
        hidden.append(actor.get_actor_label())
if set(hidden) != HIDE_IN_CLONE:
    missing = sorted(HIDE_IN_CLONE - set(hidden))
    fail("v551 wall-liner labels changed; refusing partial open-bay conversion: " + ", ".join(missing))

# Candidate-only materials: broad readable zones rather than stripes or
# micro-detail. Values deliberately support the Cairnwell palette while still
# separating clean walkways from machinery at Steam thumbnail scale.
floor_mat = create_material("M_LB_PS_SteamOpenBayFloor_v004", (0.17, 0.19, 0.20), 0.70)
pale_green_mat = create_material("M_LB_PS_SteamPaleGreenZone_v004", (0.36, 0.58, 0.49), 0.76)
cream_mat = create_material("M_LB_PS_SteamCreamLane_v004", (0.78, 0.73, 0.60), 0.72)
charcoal_mat = create_material("M_LB_PS_SteamCharcoal_v004", (0.032, 0.036, 0.040), 0.62)
steel_mat = create_material("M_LB_PS_SteamSteel_v004", (0.16, 0.18, 0.20), 0.57)
yellow_mat = create_material("M_LB_PS_SteamSafetyYellow_v004", (0.90, 0.63, 0.015), 0.54)

placed = []

# Floor extension begins exactly after v551's existing foundation. It is a
# single broad native-Unreal slab, not another building shell.
placed.append(record(mesh_actor(
    "Open-bay press floor extension",
    cube,
    (10425.0, 0.0, -9.0),
    material=floor_mat,
    scale=(151.5, 50.0, 0.12),
    extra_tags=(unreal.Name("LB.PressShop.Floor"),),
)))

# The cream route is intentionally wide and short enough to be read in a
# screenshot. Green station islands give each automated station a clear role.
placed.append(record(mesh_actor(
    "Wide cream operator and service route",
    cube,
    (10425.0, -1850.0, 0.2),
    material=cream_mat,
    scale=(151.5, 8.0, 0.018),
    extra_tags=(unreal.Name("LB.PressShop.Walkway"),),
)))
for label, (_, location, _) in PRESS.items():
    placed.append(record(mesh_actor(
        "Large pale-green zone - " + label,
        cube,
        (location[0], 0.0, 0.1),
        material=pale_green_mat,
        scale=(13.0, 15.0, 0.017),
        extra_tags=(unreal.Name("LB.PressShop.StationZone"),),
    )))

# v551's coil AGV hands into these reused S01 pieces. No duplicate bare or
# wrapped coil is spawned: the lorry, hook and AGV already visibly establish
# the coil story before the decoiler.
for label, location, yaw in (
    ("S01 decoiler base - native reuse", (3500.0, 0.0, 0.0), 270.0),
    ("S01 decoiler spindle - native reuse", (3500.0, 0.0, 0.0), 270.0),
    ("S01 straightener and feed - native reuse", (4350.0, 0.0, 0.0), 270.0),
    ("S01 feed bridge - native reuse", (5000.0, 0.0, 0.0), 270.0),
):
    native_key = label.replace(" - native reuse", "")
    placed.append(record(mesh_actor(
        label,
        assets[native_key],
        location,
        yaw=yaw,
        extra_tags=(unreal.Name("LB.PressShop.NativeMaterialFlow"),),
    ), assets[native_key]))

for label, (_, location, yaw) in PRESS.items():
    placed.append(record(mesh_actor(
        label + " - clean square candidate",
        assets[label],
        location,
        yaw=yaw,
        extra_tags=(unreal.Name("LB.PressShop.MeshyCleanedCandidate"),),
    ), assets[label]))

# These project-native frame/belt pairs replace raw roller generation and
# create generous hand-off gaps for the adaptive transfer spine above.
for index, x in enumerate((5350.0, 7050.0, 9180.0, 10800.0, 12780.0, 14700.0), start=1):
    frame = mesh_actor(
        "Native transfer conveyor frame %02d" % index,
        assets["transfer conveyor frame"],
        (x, 0.0, 0.0),
        yaw=270.0,
        extra_tags=(unreal.Name("LB.PressShop.NativeMaterialFlow"),),
    )
    set_palette_slots(frame, charcoal_mat, steel_mat, yellow_mat, pale_green_mat)
    placed.append(record(frame, assets["transfer conveyor frame"]))
    belt = mesh_actor(
        "Native transfer conveyor belt %02d" % index,
        assets["transfer conveyor belt"],
        (x, 0.0, 0.0),
        yaw=270.0,
        material=charcoal_mat,
        extra_tags=(unreal.Name("LB.PressShop.NativeMaterialFlow"),),
    )
    placed.append(record(belt, assets["transfer conveyor belt"]))

for label, native_key, location, yaw in (
    ("S07 inspection cell - native reuse", "S07 inspection", (15350.0, 0.0, 0.0), 270.0),
    ("S07 outgoing dunnage - native reuse", "S07 outbound dunnage", (16600.0, 0.0, 0.0), 270.0),
):
    placed.append(record(mesh_actor(
        label,
        assets[native_key],
        location,
        yaw=yaw,
        extra_tags=(unreal.Name("LB.PressShop.NativeMaterialFlow"),),
    ), assets[native_key]))

# A sparse, repair-friendly overhead transfer spine says "automated 2126
# press shop" without turning into a roof, dense truss, or cable forest.
for index, x in enumerate((5000.0, 8200.0, 11400.0, 14600.0), start=1):
    for side, y in (("operator", -2150.0), ("service", 2150.0)):
        placed.append(record(mesh_actor(
            "Open-bay transfer gantry column %02d %s" % (index, side),
            cube,
            (x, y, 760.0),
            material=steel_mat,
            scale=(0.42, 0.42, 15.2),
            extra_tags=(unreal.Name("LB.PressShop.OpenGantry"),),
        )))
    placed.append(record(mesh_actor(
        "Open-bay transfer crossbeam %02d" % index,
        cube,
        (x, 0.0, 1500.0),
        material=yellow_mat,
        scale=(0.34, 43.0, 0.34),
        extra_tags=(unreal.Name("LB.PressShop.OpenGantry"),),
    )))
for side, y in (("operator", -2150.0), ("service", 2150.0)):
    placed.append(record(mesh_actor(
        "Open-bay continuous automation rail - " + side,
        cube,
        (9800.0, y, 1485.0),
        material=yellow_mat,
        scale=(101.0, 0.30, 0.26),
        extra_tags=(unreal.Name("LB.PressShop.OpenGantry"),),
    )))

# Native Unreal lighting only. A SkyAtmosphere resolves the existing v551
# real-time skylight warning; all fixtures are movable and attached visually
# to the open rail silhouette rather than a newly invented roof.
for actor in actors:
    if isinstance(actor, unreal.DirectionalLight):
        actor.light_component.set_editor_property("intensity", 0.30)
        actor.light_component.set_editor_property("mobility", unreal.ComponentMobility.MOVABLE)
        actor.light_component.set_editor_property("use_temperature", True)
        actor.light_component.set_editor_property("temperature", 5000.0)
    elif isinstance(actor, unreal.SkyLight):
        actor.light_component.set_editor_property("intensity", 0.20)
        actor.light_component.set_editor_property("mobility", unreal.ComponentMobility.MOVABLE)
        actor.light_component.set_editor_property("real_time_capture", True)
sky_atmosphere = spawn(unreal.SkyAtmosphere, "B_stylized SkyAtmosphere", (10425.0, 0.0, 0.0), extra_tags=(unreal.Name("LB.PressShop.Lighting"),))
placed.append(record(sky_atmosphere))

fixture_locations = []
for x in (4300.0, 6500.0, 8700.0, 10900.0, 13100.0, 15300.0):
    for y in (-1250.0, 1250.0):
        fixture_locations.append((x, y))
for index, (x, y) in enumerate(fixture_locations, start=1):
    light = spawn(
        unreal.RectLight,
        "B_stylized open-bay fixture %02d" % index,
        (x, y, 1420.0),
        extra_tags=(unreal.Name("LB.PressShop.Lighting"),),
    )
    light.light_component.set_editor_property("mobility", unreal.ComponentMobility.MOVABLE)
    light.light_component.set_editor_property("intensity", 1200.0)
    light.light_component.set_editor_property("intensity_units", unreal.LightUnits.LUMENS)
    light.light_component.set_editor_property("source_width", 650.0)
    light.light_component.set_editor_property("source_height", 160.0)
    light.light_component.set_editor_property("attenuation_radius", 2600.0)
    light.light_component.set_editor_property("use_temperature", True)
    light.light_component.set_editor_property("temperature", 5000.0)
    light.set_actor_rotation(aim(light.get_actor_location(), unreal.Vector(x, 0.0, 150.0)), False)
    placed.append(record(light))

post = spawn(unreal.PostProcessVolume, "B_stylized fixed exposure", (10425.0, 0.0, 300.0), extra_tags=(unreal.Name("LB.PressShop.Lighting"),))
post.set_editor_property("unbound", True)
settings = post.get_editor_property("settings")
settings.override_auto_exposure_bias = True
settings.auto_exposure_bias = -0.50
post.set_editor_property("settings", settings)
placed.append(record(post))

# Steam review cameras: one diagonal shows the complete material narrative;
# one closer frame sells the distinctive square presses, open gantry and zones.
overview = spawn(unreal.CameraActor, "Steam wishlist full-process overview", (7000.0, 8500.0, 5700.0), extra_tags=(unreal.Name("LB.PressShop.Camera"),))
overview.set_actor_rotation(aim(overview.get_actor_location(), unreal.Vector(7600.0, 0.0, 280.0)), False)
overview.camera_component.set_editor_property("field_of_view", 56.0)
placed.append(record(overview))

hero = spawn(unreal.CameraActor, "Steam wishlist press-line hero", (8900.0, -6500.0, 1900.0), extra_tags=(unreal.Name("LB.PressShop.Camera"),))
hero.set_actor_rotation(aim(hero.get_actor_location(), unreal.Vector(10400.0, 0.0, 420.0)), False)
hero.camera_component.set_editor_property("field_of_view", 54.0)
placed.append(record(hero))
unreal.EditorLevelLibrary.set_level_viewport_camera_info(hero.get_actor_location(), hero.get_actor_rotation())

if not unreal.EditorLevelLibrary.save_current_level():
    fail("could not save the open-bay Steam candidate")
if not TARGET_FILE.is_file():
    fail("candidate map file was not written")

source_hash_after = sha256(SOURCE_FILE)
source_mtime_after = SOURCE_FILE.stat().st_mtime_ns
if source_hash_before != source_hash_after or source_mtime_before != source_mtime_after:
    fail("retained v551 source changed during candidate-only build")

current = list(unreal.EditorLevelLibrary.get_all_level_actors())
tagged = [actor for actor in current if TAG in actor.tags]
expected_count = len(placed)
if len(tagged) != expected_count:
    fail("expected %d v004-tagged actors, found %d" % (expected_count, len(tagged)))

report = {
    "status": "PASS__ROOFLESS_STEAM_OPEN_BAY_V004_CANDIDATE_BUILT_FROM_RETAINED_V551_ONLY",
    "candidate_map": TARGET,
    "retained_source": SOURCE,
    "retained_source_sha256_before": source_hash_before,
    "retained_source_sha256_after": source_hash_after,
    "retained_source_mtime_ns_before": source_mtime_before,
    "retained_source_mtime_ns_after": source_mtime_after,
    "candidate_sha256": sha256(TARGET_FILE),
    "hidden_in_clone_not_deleted": sorted(hidden),
    "new_v004_actor_count": len(tagged),
    "new_v004_actors": placed,
    "material_flow": [
        "retained four-coil lorry",
        "retained bridge crane / C-hook / saddle / AGV",
        "reused decoiler and straightener",
        "S02 draw/form",
        "S03 trim",
        "S04 pierce",
        "S05 flange/hem",
        "S06 vision/outfeed",
        "reused inspection and dunnage",
    ],
    "coil_policy": "no new coils spawned; retained project coils remain separate lorry, hook and AGV actors and are not embedded in a generated press",
    "meshy_policy": "uses the five existing cleaned, repair-friendly candidate presses; no Meshy API credits spent because the asset audit found no current large-form gap",
    "open_bay_policy": "no roof mesh or roof sheet created; retained v551 roof beams are structural context only; v551 wall liners are hidden only in this duplicate",
    "lighting": {"profile": "B_stylized candidate calibration", "sun": 0.30, "sky": 0.20, "fixture_lumens": 1200, "fixture_temperature_kelvin": 5000, "exposure_bias": -0.50, "fixtures": len(fixture_locations), "all_new_fixtures_movable": True},
    "honest_status": "candidate presentation map only; no gameplay, release, collision, navigation, runtime optimisation, packaged build or Steam approval claim",
    "next_gate": "inspect both native Unreal camera views; correct composition and readability before generating or importing any additional Meshy asset",
}
REPORT.parent.mkdir(parents=True, exist_ok=True)
REPORT.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
unreal.log("STEAM_OPEN_BAY_V004=" + json.dumps({"actors": len(tagged), "map": TARGET}, sort_keys=True))
