"""Build an isolated installed-hall/service-detail PR-008 candidate from retained v079."""

import json
from datetime import datetime, timezone
from pathlib import Path

import unreal


ROOT = Path(unreal.Paths.project_dir())
BASE = "/Game/LineBoss/Maps/LB_PressShop_PR008CalibratedLightingCandidate_v079"
MAP = "/Game/LineBoss/Maps/LB_PressShop_PR008InstalledHallCandidate_v080"
PREFIX = "LB_PR008_V080_"
DEST = "/Game/LineBoss/Stations/Press/PR008/InstalledHall_v080"
AUDIT = ROOT / "Saved/Audits/press_shop_pr008_installed_hall_candidate_v080.json"

library = unreal.EditorAssetLibrary
asset_tools = unreal.AssetToolsHelpers.get_asset_tools()
material_editing = unreal.MaterialEditingLibrary
levels = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
actors = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)

map_file = ROOT / "Content/LineBoss/Maps/LB_PressShop_PR008InstalledHallCandidate_v080.umap"
if not map_file.exists():
    if not library.duplicate_asset(BASE, MAP):
        raise RuntimeError("Could not duplicate retained v079 to isolated v080")
    if not library.save_asset(MAP, only_if_is_dirty=False):
        raise RuntimeError("Could not save prepared v080 map")
    unreal.log("LINE_BOSS_PR008_V080_PREPARE_PASS__RERUN_FOR_POPULATION")
    unreal.SystemLibrary.quit_editor()
    raise SystemExit

if not levels.load_level(MAP):
    raise RuntimeError(f"Could not load {MAP}")
for actor in list(actors.get_all_level_actors()):
    if actor.get_actor_label().startswith(PREFIX):
        actors.destroy_actor(actor)


def constant_material(name, colour, metallic, roughness):
    path = f"{DEST}/{name}"
    material = library.load_asset(path) if library.does_asset_exist(path) else asset_tools.create_asset(
        name, DEST, unreal.Material, unreal.MaterialFactoryNew())
    if material is None:
        raise RuntimeError(f"Could not create {path}")
    material_editing.delete_all_material_expressions(material)
    base = material_editing.create_material_expression(
        material, unreal.MaterialExpressionConstant3Vector, -300, -80)
    base.set_editor_property("constant", unreal.LinearColor(*colour, 1.0))
    metal = material_editing.create_material_expression(
        material, unreal.MaterialExpressionConstant, -300, 30)
    metal.set_editor_property("r", metallic)
    rough = material_editing.create_material_expression(
        material, unreal.MaterialExpressionConstant, -300, 120)
    rough.set_editor_property("r", roughness)
    material_editing.connect_material_property(base, "", unreal.MaterialProperty.MP_BASE_COLOR)
    material_editing.connect_material_property(metal, "", unreal.MaterialProperty.MP_METALLIC)
    material_editing.connect_material_property(rough, "", unreal.MaterialProperty.MP_ROUGHNESS)
    material_editing.recompile_material(material)
    library.save_loaded_asset(material, only_if_is_dirty=False)
    return material


materials = {
    "wall": constant_material("M_CA_MW_PR008_HallPanel_v080", (0.052, 0.064, 0.066), 0.18, 0.70),
    "seam": constant_material("M_CA_MW_PR008_HallSeam_v080", (0.012, 0.017, 0.018), 0.45, 0.48),
    "service": constant_material("M_CA_MW_PR008_ServiceSteel_v080", (0.32, 0.37, 0.40), 0.92, 0.27),
    "hydraulic": constant_material("M_CA_MW_PR008_HydraulicHeader_v080", (0.045, 0.16, 0.22), 0.72, 0.34),
    "air": constant_material("M_CA_MW_PR008_AirHeader_v080", (0.04, 0.25, 0.42), 0.66, 0.36),
    "sign": constant_material("M_CA_MW_PR008_CellSignBacking_v080", (0.004, 0.010, 0.010), 0.42, 0.40),
    "anchor": constant_material("M_CA_MW_PR008_AnchorSteel_v080", (0.24, 0.27, 0.28), 0.96, 0.30),
}


def mesh_actor(label, mesh_path, centre, scale, material, tags):
    actor = actors.spawn_actor_from_class(
        unreal.StaticMeshActor, unreal.Vector(*centre), unreal.Rotator())
    if actor is None:
        raise RuntimeError(f"Could not spawn {label}")
    actor.set_actor_label(PREFIX + label)
    actor.tags = [unreal.Name(value) for value in (
        "LB.Asset.Candidate.v080", "LB.Asset.CandidateNotPromoted", *tags)]
    component = actor.static_mesh_component
    component.set_static_mesh(library.load_asset(mesh_path))
    component.set_world_scale3d(unreal.Vector(*scale))
    component.set_material(0, material)
    component.set_collision_enabled(unreal.CollisionEnabled.NO_COLLISION)
    component.set_collision_profile_name(unreal.Name("NoCollision"))
    component.set_editor_property("can_ever_affect_navigation", False)
    return actor


def cube(label, centre, dimensions, material, tags):
    return mesh_actor(label, "/Engine/BasicShapes/Cube.Cube", centre,
                      (dimensions[0] / 100.0, dimensions[1] / 100.0, dimensions[2] / 100.0),
                      material, tags)


wall_panels = [
    cube(f"HallPanel_{index:02d}", (x, -1110.0, 330.0), (156.0, 12.0, 600.0),
         materials["wall"], ("LB.Environment.PR008.Wall", "LB.Navigation.Neutral"))
    for index, x in enumerate((-900.0, -740.0, -580.0, -420.0, -260.0, -100.0), start=1)
]
wall_seams = [
    cube(f"HallSeam_{index:02d}", (x, -1117.0, 330.0), (3.0, 3.0, 600.0),
         materials["seam"], ("LB.Environment.PR008.WallJoint", "LB.Navigation.Neutral"))
    for index, x in enumerate((-820.0, -660.0, -500.0, -340.0, -180.0), start=1)
]

cable_tray = [
    cube("CableTray_LeftRail", (-500.0, -1142.0, 610.0), (1000.0, 4.0, 10.0),
         materials["service"], ("LB.Service.PR008.CableTray", "LB.Navigation.Neutral")),
    cube("CableTray_RightRail", (-500.0, -1170.0, 610.0), (1000.0, 4.0, 10.0),
         materials["service"], ("LB.Service.PR008.CableTray", "LB.Navigation.Neutral")),
]
cable_tray.extend(
    cube(f"CableTray_Rung_{index:02d}", (x, -1156.0, 610.0), (4.0, 32.0, 4.0),
         materials["service"], ("LB.Service.PR008.CableTray", "LB.Navigation.Neutral"))
    for index, x in enumerate(range(-960, 1, 48), start=1)
)

service_headers = [
    cube("ServiceHeader_HydraulicPressure", (-500.0, -1132.0, 455.0), (1000.0, 7.0, 7.0),
         materials["hydraulic"], ("LB.Service.PR008.HydraulicPressure", "LB.Navigation.Neutral")),
    cube("ServiceHeader_HydraulicReturn", (-500.0, -1132.0, 430.0), (1000.0, 7.0, 7.0),
         materials["service"], ("LB.Service.PR008.HydraulicReturn", "LB.Navigation.Neutral")),
    cube("ServiceHeader_CompressedAir", (-500.0, -1132.0, 405.0), (1000.0, 6.0, 6.0),
         materials["air"], ("LB.Service.PR008.CompressedAir", "LB.Navigation.Neutral")),
]
service_drops = [
    cube("ServiceDrop_HPU", (-95.0, -1132.0, 300.0), (7.0, 7.0, 305.0),
         materials["hydraulic"], ("LB.Service.PR008.HPUConnection", "LB.Navigation.Neutral")),
    cube("ServiceDrop_Cabinets", (-785.0, -1142.0, 350.0), (12.0, 24.0, 500.0),
         materials["service"], ("LB.Service.PR008.CabinetDrop", "LB.Navigation.Neutral")),
]

sign = cube("CellIdentity_Backplate", (-500.0, -1128.0, 535.0), (460.0, 6.0, 74.0),
            materials["sign"], ("LB.Identity.PR008.CellHeader", "LB.Navigation.Neutral"))


def sign_text(label, value, x, z, size, colour):
    actor = actors.spawn_actor_from_class(
        unreal.TextRenderActor, unreal.Vector(x, -1132.0, z), unreal.Rotator(yaw=-90.0))
    actor.set_actor_label(PREFIX + "TEXT_" + label)
    actor.tags = [unreal.Name(value) for value in (
        "LB.Asset.Candidate.v080", "LB.Asset.CandidateNotPromoted",
        "LB.Identity.PR008.CellHeader", "LB.Identity.Diegetic")]
    component = actor.text_render
    component.set_text(value)
    component.set_world_size(size)
    component.set_text_render_color(colour)
    component.set_horizontal_alignment(unreal.HorizTextAligment.EHTA_CENTER)
    component.set_vertical_alignment(unreal.VerticalTextAligment.EVRTA_TEXT_CENTER)
    component.set_collision_enabled(unreal.CollisionEnabled.NO_COLLISION)
    component.set_editor_property("can_ever_affect_navigation", False)
    return actor


identity = [
    sign_text("Station", "PR-008  SERVO BLANKING", -500.0, 550.0, 10.0,
              unreal.Color(242, 195, 0, 255)),
    sign_text("Company", "CAIRNWELL AUTOMOTIVE  /  MOORCROSS WORKS", -500.0, 522.0, 7.0,
              unreal.Color(205, 229, 220, 255)),
]

anchor_positions = [(x, y) for x in (-900.0, -700.0, -500.0, -300.0, -100.0)
                    for y in (-2288.0, -1702.0)]
anchors = []
for index, (x, y) in enumerate(anchor_positions, start=1):
    anchors.append(cube(f"AnchorPlate_{index:02d}", (x, y, 6.6), (20.0, 20.0, 1.5),
                        materials["anchor"], ("LB.Foundation.PR008.Anchor", "LB.Navigation.Neutral")))
    anchors.append(mesh_actor(
        f"AnchorStud_{index:02d}", "/Engine/BasicShapes/Cylinder.Cylinder", (x, y, 10.0),
        (0.07, 0.07, 0.055), materials["anchor"],
        ("LB.Foundation.PR008.Anchor", "LB.Navigation.Neutral")))

column = next((actor for actor in actors.get_all_level_actors()
               if actor.get_actor_label() == "LB_PRESS_Column_0_-2250"), None)
if column is None or column.get_editor_property("hidden"):
    raise RuntimeError("The genuine hall column must remain present in v080")

if not levels.save_current_level():
    raise RuntimeError(f"Could not save {MAP}")
library.save_directory(DEST, only_if_is_dirty=False, recursive=True)

payload = {
    "$schema": "line-boss/audit/press-shop-pr008-installed-hall-candidate-v080/v1",
    "generated_utc": datetime.now(timezone.utc).isoformat(),
    "status": "REFERENCE_BACKED_INSTALLED_HALL_SERVICE_SPINE_IDENTITY_AND_ANCHOR_DETAIL_BUILT_FROM_RETAINED_V079__EARLY_CAMERA_GATE_REQUIRED__NOT_PROMOTED",
    "map": MAP,
    "base_map": BASE,
    "reference": "CAIRNWELL_PRESS_SHOP_REMAINING_MACHINERY_PACK_v1.0 Sheet 01 sections 1, 8 and 9",
    "wall_panel_count": len(wall_panels),
    "wall_seam_count": len(wall_seams),
    "cable_tray_actor_count": len(cable_tray),
    "service_header_count": len(service_headers),
    "service_drop_count": len(service_drops),
    "anchor_assembly_count": len(anchor_positions),
    "identity_text": [str(actor.text_render.text) for actor in identity],
    "line_boss_in_world": False,
    "new_dressing_collision": "NoCollision candidate dressing",
    "new_dressing_navigation": "neutral",
    "native_machine_geometry_modified": False,
    "native_motion_modified": False,
    "measured_datums_modified": False,
    "fixed_hall_column_preserved": column.get_actor_label(),
    "accepted_pr004_v006_preserved": True,
    "rejected_pr004_v007_v010_unchanged": True,
    "rejected_pr008_v076_v078_unchanged": True,
    "retained_v079_unchanged": True,
    "promotion_authorized": False,
}
AUDIT.parent.mkdir(parents=True, exist_ok=True)
AUDIT.write_text(json.dumps(payload, indent=2), encoding="utf-8")
unreal.log(
    f"LINE_BOSS_PR008_V080_INSTALLED_HALL_BUILD_PASS wall={len(wall_panels)} "
    f"tray={len(cable_tray)} anchors={len(anchor_positions)} identity={len(identity)}")
unreal.SystemLibrary.quit_editor()
