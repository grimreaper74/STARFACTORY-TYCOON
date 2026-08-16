"""Release-intent visual successor for the retained v532 inbound sequence.

Adds a readable installed factory backdrop and dock identity without changing
the retained process transforms or claiming unverified engineering values.
"""
from pathlib import Path
import json
import unreal

root = Path(__file__).parent
source = (root / "build_inbound_installed_cell_v532.py").read_text(encoding="utf-8")
source = source.replace("v532", "v534").replace("V532", "V534").replace("V032_", "V034_")
exec(compile(source, str(root / "build_inbound_installed_cell_v532.py"), "exec"), globals(), globals())

library = unreal.EditorAssetLibrary
actors = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
levels = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
project = Path(unreal.Paths.project_dir())
cube = library.load_asset("/Engine/BasicShapes/Cube.Cube")

mats = {
    "white": library.load_asset("/Game/LineBoss/IndustrialKit/InboundCoilDelivery/Candidate_v001/Materials_v001/MI_CA_Inbound_White_v001"),
    "dark": library.load_asset("/Game/LineBoss/IndustrialKit/InboundCoilDelivery/Candidate_v001/Materials_v001/MI_CA_Inbound_Charcoal_v001"),
    "green": library.load_asset("/Game/LineBoss/IndustrialKit/InboundCoilDelivery/Candidate_v001/Materials_v001/MI_CA_Inbound_CairnwellGreen_v001"),
    "glass": library.load_asset("/Game/LineBoss/IndustrialKit/InboundCoilDelivery/Candidate_v001/Materials_v001/MI_CA_Inbound_Glass_v001"),
    "yellow": library.load_asset("/Game/LineBoss/IndustrialKit/InboundCoilDelivery/Candidate_v001/Materials_v001/MI_CA_Inbound_SafetyYellow_v001"),
    "floor": library.load_asset("/Game/LineBoss/Candidates/PressShop/IntegratedEnvironment_v107/Materials/M_CA_MW_SlabJoint_v105"),
}
if cube is None or any(v is None for v in mats.values()):
    raise RuntimeError("Missing retained material for v534 factory context")

tags = [unreal.Name("LB.Asset.ValidationOnly"), unreal.Name("LB.Asset.CandidateNotPromoted"),
        unreal.Name("LB.Engineering.Values.TBC"), unreal.Name("LB.Inbound.ProPack.20260807")]

def block(label, loc, scale, mat, collision=False):
    a = actors.spawn_actor_from_class(unreal.StaticMeshActor, unreal.Vector(*loc), unreal.Rotator())
    a.set_actor_label(label)
    a.set_actor_scale3d(unreal.Vector(*scale))
    a.static_mesh_component.set_static_mesh(cube)
    a.static_mesh_component.set_material(0, mat)
    a.static_mesh_component.set_collision_enabled(
        unreal.CollisionEnabled.QUERY_AND_PHYSICS if collision else unreal.CollisionEnabled.NO_COLLISION)
    a.static_mesh_component.set_editor_property("can_ever_affect_navigation", collision)
    a.tags = tags
    return a

# Replace the black review-stage floor finish with the retained sealed-concrete language.
floor = next(a for a in actors.get_all_level_actors() if a.get_actor_label().endswith("Floor"))
floor.static_mesh_component.set_material(0, mats["floor"])

# Roof-off Pro-style installed backdrop, positioned behind the process from the
# retained owner-direction camera.  Dimensions and spacing remain visual/TBC.
context = []
context.append(block("LB_INBOUND_V034_BackWall_Upper", (-500, -2050, 720), (62, .18, 8.6), mats["white"], True))
context.append(block("LB_INBOUND_V034_BackWall_Lower", (-500, -2025, 190), (62, .20, 2.0), mats["dark"], True))
context.append(block("LB_INBOUND_V034_WindowBand", (-500, -2000, 850), (54, .08, 1.65), mats["glass"], False))
for i, x in enumerate(range(-5000, 5001, 1000), 1):
    context.append(block(f"LB_INBOUND_V034_WallMullion_{i:02d}", (x, -1945, 850), (.08, .10, 1.8), mats["dark"], False))
for i, x in enumerate(range(-5000, 5001, 1250), 1):
    context.append(block(f"LB_INBOUND_V034_HallColumn_{i:02d}", (x, -1750, 650), (.16, .16, 13.0), mats["dark"], True))
context.append(block("LB_INBOUND_V034_DockIdentitySign", (-3650, -1900, 1210), (8.5, .12, 1.15), mats["green"], False))
context.append(block("LB_INBOUND_V034_PR003IdentitySign", (3300, -1900, 1210), (8.0, .12, 1.15), mats["green"], False))

def sign(label, text, loc, size=72.0):
    a = actors.spawn_actor_from_class(unreal.TextRenderActor, unreal.Vector(*loc), unreal.Rotator(0, 0, 0))
    a.set_actor_label(label)
    a.text_render.set_editor_properties({"text": text, "horizontal_alignment": unreal.HorizTextAligment.EHTA_CENTER,
                                         "world_size": size, "text_render_color": unreal.Color(235, 242, 235, 255)})
    a.set_actor_rotation(unreal.Rotator(0, 0, 0), False)
    a.tags = tags
    return a

sign("LB_INBOUND_V034_DockSignText", "INBOUND COIL DELIVERY", (-3650, -1815, 1210), 64)
sign("LB_INBOUND_V034_PR003SignText", "TO PR-003  BARE COIL STORE", (3300, -1815, 1210), 56)

# Restrained high-bay fill: readable steel and silver coils without flattening shadows.
lights = []
for i, x in enumerate((-4200, -2800, -1400, 0, 1400, 2800, 4200), 1):
    light = actors.spawn_actor_from_class(unreal.RectLight, unreal.Vector(x, 250, 1450), unreal.Rotator(0, -90, 0))
    light.set_actor_label(f"LB_INBOUND_V034_HighBay_{i:02d}")
    light.rect_light_component.set_editor_properties({"intensity": 190.0, "attenuation_radius": 2600.0,
                                                       "source_width": 950.0, "source_height": 90.0,
                                                       "cast_shadows": False})
    light.tags = tags
    lights.append(light)

for actor in actors.get_all_level_actors():
    if isinstance(actor, unreal.PostProcessVolume):
        settings = actor.settings
        settings.set_editor_property("auto_exposure_bias", -0.35)
        actor.settings = settings

overview = next(a for a in actors.get_all_level_actors() if a.get_actor_label() == "LB_CAM_InboundHall_ProcessOverview_v534")
overview.set_actor_location(unreal.Vector(-750, 6500, 2150), False, False)
overview.set_actor_rotation(unreal.MathLibrary.find_look_at_rotation(overview.get_actor_location(), unreal.Vector(-650, -150, 300)), False)
overview.camera_component.set_editor_property("field_of_view", 49.0)
hero = next(a for a in actors.get_all_level_actors() if a.get_actor_label() == "LB_CAM_InboundHall_CraneHero_v534")
hero.set_actor_location(unreal.Vector(1500, 4200, 1650), False, False)
hero.set_actor_rotation(unreal.MathLibrary.find_look_at_rotation(hero.get_actor_location(), unreal.Vector(-250, -100, 340)), False)
hero.camera_component.set_editor_property("field_of_view", 55.0)

unreal.AutomationUtilsBlueprintLibrary.finish_all_asset_compilation()
if not levels.save_current_level():
    raise RuntimeError("Failed saving v534 release-intent inbound review")

audit = project / "Saved/Audits/PressShopIntegration/inbound_release_context_build_v534.json"
audit.parent.mkdir(parents=True, exist_ok=True)
audit.write_text(json.dumps({
    "status": "PASS__ISOLATED_RELEASE_INTENT_CONTEXT_BUILT__VISUAL_GATE_REQUIRED__NOT_PROMOTED",
    "map": "/Game/LineBoss/Developer/Validation/LB_InboundCoilDeliveryInstalledCell_v534",
    "retained_process_layout": "v532",
    "reference_pack": "SourceAssets/Reference/PressShop/InboundCoilDelivery/ProPack_v20260807",
    "context_actor_count": len(context), "high_bay_light_count": len(lights),
    "process_order": ["four-coil lorry", "protected crane and powered C-hook", "fixed receiving saddle", "loaded Coil AGV", "PR-003"],
    "engineering_values": "TBC", "promotion_authorized": False,
    "builder_authority_v438_modified": False
}, indent=2), encoding="utf-8")
unreal.log("LINE_BOSS_INBOUND_RELEASE_CONTEXT_V534_BUILD_PASS")
