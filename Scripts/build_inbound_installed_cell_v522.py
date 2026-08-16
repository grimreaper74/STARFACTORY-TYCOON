"""Fresh installed-hall validation child for the owner-approved inbound Pro pack.

This deliberately rebuilds from retained v520/v521 process geometry.  It does
not parent from or modify builder authority v438, and it does not claim any
unverified engineering value.
"""
from pathlib import Path
import json
import unreal

root = Path(__file__).parent
source = (root / "build_inbound_installed_cell_v521.py").read_text(encoding="utf-8")
source = source.replace("v521", "v522").replace("V521", "V522").replace("V021_", "V022_")
exec(compile(source, str(root / "build_inbound_installed_cell_v521.py"), "exec"), globals(), globals())

library = unreal.EditorAssetLibrary
actors = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
levels = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
project = Path(unreal.Paths.project_dir())
audit = project / "Saved/Audits/PressShopIntegration/inbound_hall_context_build_v522.json"

cube = library.load_asset("/Engine/BasicShapes/Cube.Cube")
materials = {
    "dark": library.load_asset("/Game/LineBoss/IndustrialKit/InboundCoilDelivery/Candidate_v001/Materials_v001/MI_CA_Inbound_Charcoal_v001"),
    "yellow": library.load_asset("/Game/LineBoss/IndustrialKit/InboundCoilDelivery/Candidate_v001/Materials_v001/MI_CA_Inbound_SafetyYellow_v001"),
    "route": library.load_asset("/Game/LineBoss/Candidates/PressShop/IntegratedEnvironment_v107/Materials/M_CA_MW_LogisticsRoute_v105"),
    "joint": library.load_asset("/Game/LineBoss/Candidates/PressShop/IntegratedEnvironment_v107/Materials/M_CA_MW_SlabJoint_v105"),
    "lens": library.load_asset("/Game/LineBoss/Candidates/PressShop/IntegratedEnvironment_v107/Materials/M_CA_MW_LuminaireLens_v105"),
}
if cube is None or any(value is None for value in materials.values()):
    raise RuntimeError("Missing retained hall-context source asset")

tags = [unreal.Name("LB.Asset.ValidationOnly"), unreal.Name("LB.Asset.CandidateNotPromoted"),
        unreal.Name("LB.Engineering.Values.TBC"), unreal.Name("LB.Inbound.ProPack.20260807")]

def mesh(label, location, scale, material, collision=False):
    actor = actors.spawn_actor_from_class(unreal.StaticMeshActor, unreal.Vector(*location), unreal.Rotator())
    actor.set_actor_label(label)
    actor.set_actor_scale3d(unreal.Vector(*scale))
    actor.static_mesh_component.set_static_mesh(cube)
    actor.static_mesh_component.set_material(0, material)
    actor.static_mesh_component.set_collision_enabled(
        unreal.CollisionEnabled.QUERY_AND_PHYSICS if collision else unreal.CollisionEnabled.NO_COLLISION)
    actor.static_mesh_component.set_editor_property("can_ever_affect_navigation", collision)
    actor.tags = tags
    return actor

# Remove the isolated-review wall and construct an open-sided installed hall.
for actor in list(actors.get_all_level_actors()):
    if actor.get_actor_label().endswith("RearFactoryWall"):
        actors.destroy_actor(actor)

hall = []
hall.append(mesh("LB_INBOUND_V022_HallFarWall", (0, 1650, 430), (25, .18, 8.6), materials["dark"], True))
hall.append(mesh("LB_INBOUND_V022_HallRoof", (0, 0, 1180), (25, 20, .18), materials["dark"], False))
for x in (-2350, 2350):
    for y in (-1450, 1450):
        hall.append(mesh(f"LB_INBOUND_V022_HallColumn_{x}_{y}", (x, y, 520), (.18, .18, 10.4), materials["dark"], True))
for y in (-1250, 0, 1250):
    hall.append(mesh(f"LB_INBOUND_V022_RoofBeam_{y}", (0, y, 1050), (25, .12, .18), materials["dark"], False))

# Floor language from Sheet 01: dedicated AGV route, pedestrian crossing,
# dock approach and crane no-entry envelope.  Dimensions are visual/TBC.
routes = [
    mesh("LB_INBOUND_V022_AGVRoute", (1100, 650, -8), (8.5, 4.2, .025), materials["route"]),
    mesh("LB_INBOUND_V022_DockApproach", (-1700, 0, -7), (6.5, 5.2, .026), materials["joint"]),
]
for i, y in enumerate(range(-800, 801, 160), 1):
    routes.append(mesh(f"LB_INBOUND_V022_PedCrossing_{i:02d}", (770, y, -5), (1.4, .48, .03), materials["lens"]))
for x in (-880, 880):
    routes.append(mesh(f"LB_INBOUND_V022_CraneEnvelope_X_{x}", (x, 0, -4), (.06, 14.0, .035), materials["yellow"]))
for y in (-1400, 1400):
    routes.append(mesh(f"LB_INBOUND_V022_CraneEnvelope_Y_{y}", (0, y, -4), (8.8, .06, .035), materials["yellow"]))

# Continuous high-bay luminaires with broad, restrained fill.
lights = []
for i, x in enumerate((-1800, -900, 0, 900, 1800), 1):
    mesh(f"LB_INBOUND_V022_Luminaire_{i:02d}", (x, -250, 1040), (6.0, .30, .06), materials["lens"])
    light = actors.spawn_actor_from_class(unreal.RectLight, unreal.Vector(x, -250, 1010), unreal.Rotator())
    light.set_actor_label(f"LB_INBOUND_V022_HighBay_{i:02d}")
    light.set_actor_rotation(unreal.Rotator(0, -90, 0), False)
    light.rect_light_component.set_editor_properties({"intensity": 520.0, "attenuation_radius": 2600.0,
        "source_width": 1050.0, "source_height": 95.0, "cast_shadows": False})
    light.tags = tags
    lights.append(light)

def camera(label, location, target, fov):
    cam = actors.spawn_actor_from_class(unreal.CameraActor, unreal.Vector(*location), unreal.Rotator())
    cam.set_actor_label(label)
    cam.set_actor_rotation(unreal.MathLibrary.find_look_at_rotation(cam.get_actor_location(), unreal.Vector(*target)), False)
    cam.camera_component.set_editor_properties({"field_of_view": fov, "aspect_ratio": 16/9,
                                                 "constrain_aspect_ratio": True})
    cam.tags = tags + [unreal.Name("LB.Camera.Fixed.InboundHall.v522")]
    return cam

# Remove inherited camera so capture selection is exact and deterministic.
for actor in list(actors.get_all_level_actors()):
    if isinstance(actor, unreal.CameraActor):
        actors.destroy_actor(actor)
cameras = [
    camera("LB_CAM_InboundHall_ProcessOverview_v522", (-3000, -3500, 1850), (0, 0, 245), 55.0),
    camera("LB_CAM_InboundHall_CraneHero_v522", (250, -2550, 1250), (150, 0, 335), 48.0),
]

unreal.AutomationUtilsBlueprintLibrary.finish_all_asset_compilation()
if not levels.save_current_level():
    raise RuntimeError("Failed saving v522 installed-hall validation child")
audit.parent.mkdir(parents=True, exist_ok=True)
audit.write_text(json.dumps({
    "$schema": "cairnwell/audit/inbound-hall-context-build-v522/v1",
    "status": "PASS__FRESH_HALL_CONTEXT_BUILT__VISUAL_GATE_REQUIRED__NOT_PROMOTED",
    "map": "/Game/LineBoss/Developer/Validation/LB_InboundCoilDeliveryInstalledCell_v522",
    "retained_layout_source": "v520/v521",
    "reference_pack": "SourceAssets/Reference/PressShop/InboundCoilDelivery/ProPack_v20260807",
    "exact_trailer_coil_count": 4,
    "process_order": ["lorry", "protected dock", "powered C-hook", "fixed receiving saddle", "coil AGV", "PR-003"],
    "hall_actor_count": len(hall), "route_actor_count": len(routes), "high_bay_light_count": len(lights),
    "fixed_cameras": [c.get_actor_label() for c in cameras],
    "engineering_values": "TBC", "builder_authority_v438_modified": False,
    "promotion_authorized": False, "press_shop_complete": False
}, indent=2), encoding="utf-8")
unreal.log("LINE_BOSS_INBOUND_HALL_CONTEXT_V522_BUILD_PASS")
