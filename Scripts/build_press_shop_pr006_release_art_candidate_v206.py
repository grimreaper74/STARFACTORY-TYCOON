"""Build isolated PR-006 release-art v206 from retained full-line v107."""

import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path

import unreal


ROOT = Path(unreal.Paths.project_dir())
SOURCE = ROOT / "SourceAssets/PR006/PrecisionCassetteLeveller/ReleaseDetail_v001"
MANIFEST = SOURCE / "pr006_release_detail_manifest_v001.json"
BASE = "/Game/LineBoss/Maps/LB_PressShop_IntegratedEnvironmentCandidate_v107"
MAP = "/Game/LineBoss/Maps/LB_PressShop_PR006ReleaseArtCandidate_v206"
DEST = "/Game/LineBoss/Stations/Press/PR006/ReleaseDetail_v001"
MAT_DEST = DEST + "/Materials"
OUT = ROOT / "Saved/Audits/PressShopIntegration/press_shop_pr006_release_art_build_v206.json"
DATUM = unreal.Vector(-1700.0, -2000.0, 0.0)
PREFIX = "LB_PR006_V206_"

library = unreal.EditorAssetLibrary
tools = unreal.AssetToolsHelpers.get_asset_tools()
levels = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
actors_api = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
mel = unreal.MaterialEditingLibrary

base_file = ROOT / "Content/LineBoss/Maps/LB_PressShop_IntegratedEnvironmentCandidate_v107.umap"
base_hash_before = hashlib.sha256(base_file.read_bytes()).hexdigest().upper()
if library.does_asset_exist(MAP):
    raise RuntimeError(f"refusing to overwrite preserved candidate {MAP}")
if not levels.new_level_from_template(MAP, BASE):
    raise RuntimeError("could not create isolated v206 from retained v107")


def make_material(name, colour, metallic, roughness, emissive=None):
    asset = tools.create_asset(name, MAT_DEST, unreal.Material, unreal.MaterialFactoryNew())
    if asset is None:
        raise RuntimeError(f"could not create material {name}")
    base = mel.create_material_expression(asset, unreal.MaterialExpressionConstant3Vector, -320, -80)
    base.set_editor_property("constant", unreal.LinearColor(*colour, 1.0))
    metal = mel.create_material_expression(asset, unreal.MaterialExpressionConstant, -320, 40)
    metal.set_editor_property("r", metallic)
    rough = mel.create_material_expression(asset, unreal.MaterialExpressionConstant, -320, 130)
    rough.set_editor_property("r", roughness)
    mel.connect_material_property(base, "", unreal.MaterialProperty.MP_BASE_COLOR)
    mel.connect_material_property(metal, "", unreal.MaterialProperty.MP_METALLIC)
    mel.connect_material_property(rough, "", unreal.MaterialProperty.MP_ROUGHNESS)
    if emissive is not None:
        emission = mel.create_material_expression(asset, unreal.MaterialExpressionConstant3Vector, -320, 220)
        emission.set_editor_property("constant", unreal.LinearColor(*emissive, 1.0))
        mel.connect_material_property(emission, "", unreal.MaterialProperty.MP_EMISSIVE_COLOR)
    mel.recompile_material(asset)
    library.save_loaded_asset(asset, only_if_is_dirty=False)
    return asset


materials = {
    "CA_Frame": make_material("M_PR006_V206_Frame", (0.035, 0.044, 0.049), 0.72, 0.45),
    "CA_Panel": make_material("M_PR006_V206_Panel", (0.17, 0.19, 0.19), 0.48, 0.54),
    "CA_Yellow": make_material("M_PR006_V206_SafetyYellow", (0.70, 0.36, 0.012), 0.30, 0.51),
    "CA_Steel": make_material("M_PR006_V206_WorkedSteel", (0.25, 0.28, 0.30), 0.88, 0.30),
    "CA_Blue": make_material("M_PR006_V206_HydraulicBlue", (0.018, 0.075, 0.15), 0.56, 0.44),
    "CA_Rubber": make_material("M_PR006_V206_Rubber", (0.012, 0.015, 0.016), 0.02, 0.88),
    "CA_White": make_material("M_PR006_V206_ServiceWhite", (0.58, 0.61, 0.60), 0.08, 0.63),
    "CA_Red": make_material("M_PR006_V206_EStopRed", (0.42, 0.006, 0.003), 0.14, 0.47),
    "CA_Concrete": make_material("M_PR006_V206_SealedConcrete", (0.085, 0.093, 0.094), 0.01, 0.93),
}
zone_material = make_material("M_PR006_V206_EquipmentZoneYellow", (0.62, 0.35, 0.012), 0.15, 0.72)
luminaire_material = make_material(
    "M_PR006_V206_LuminaireLens", (0.63, 0.69, 0.70), 0.05, 0.32, (0.78, 0.84, 0.85))

records = json.loads(MANIFEST.read_text(encoding="utf-8"))
tasks = []
for record in records:
    asset_path = f"{DEST}/SM_{record['name']}_v001"
    if library.does_asset_exist(asset_path):
        continue
    task = unreal.AssetImportTask()
    task.set_editor_properties({
        "filename": str(SOURCE / record["fbx"]),
        "destination_path": DEST,
        "destination_name": "SM_" + record["name"] + "_v001",
        "automated": True,
        "replace_existing": False,
        "replace_existing_settings": False,
        "save": True,
    })
    options = unreal.FbxImportUI()
    options.set_editor_properties({
        "import_mesh": True,
        "import_as_skeletal": False,
        "import_materials": False,
        "import_textures": False,
        "mesh_type_to_import": unreal.FBXImportType.FBXIT_STATIC_MESH,
    })
    data = options.get_editor_property("static_mesh_import_data")
    data.set_editor_properties({
        "combine_meshes": True,
        "convert_scene": True,
        "convert_scene_unit": True,
        "force_front_x_axis": False,
        "generate_lightmap_u_vs": True,
        "auto_generate_collision": False,
        "remove_degenerates": True,
    })
    task.set_editor_property("options", options)
    tasks.append(task)
tools.import_asset_tasks(tasks)


def assign_material_slots(component, mesh):
    slot_names = [str(value.get_editor_property("material_slot_name"))
                  for value in mesh.get_editor_property("static_materials")]
    for index, slot_name in enumerate(slot_names):
        clean = slot_name.split(".")[-1]
        match = materials.get(clean)
        if match is None:
            raise RuntimeError(f"unmapped material slot {slot_name} on {mesh.get_name()}")
        component.set_material(index, match)
    return slot_names


common_tags = [
    unreal.Name("LB.Asset.Candidate.v206"),
    unreal.Name("LB.Asset.CandidateNotPromoted"),
    unreal.Name("LB.Station.PR006"),
    unreal.Name("LB.ReleaseDetail.NoCollision"),
]
created = []
import_rows = []
for record in records:
    mesh_path = f"{DEST}/SM_{record['name']}_v001"
    mesh = library.load_asset(mesh_path)
    if not isinstance(mesh, unreal.StaticMesh):
        raise RuntimeError(f"missing imported mesh {mesh_path}")
    location = record["placement_m"]
    world = DATUM + unreal.Vector(location[0] * 100.0, location[1] * 100.0, location[2] * 100.0)
    actor = actors_api.spawn_actor_from_class(unreal.StaticMeshActor, world, unreal.Rotator())
    actor.set_actor_label(PREFIX + record["name"])
    actor.tags = common_tags + [unreal.Name("LB.Source.PR006.ReleaseDetail.v001")]
    component = actor.static_mesh_component
    component.set_static_mesh(mesh)
    slots = assign_material_slots(component, mesh)
    component.set_collision_enabled(unreal.CollisionEnabled.NO_COLLISION)
    component.set_editor_property("can_ever_affect_navigation", False)
    created.append(actor)
    import_rows.append({
        "actor": actor.get_actor_label(),
        "asset": mesh_path,
        "world_location_cm": [world.x, world.y, world.z],
        "source_dimensions_mm": record["dimensions_mm"],
        "material_slots": slots,
        "collision": "NoCollision",
        "navigation": False,
    })

# Replace the two hard, isolated task pools with restrained side accents.  The
# original actors remain present; only their exact light output changes here.
by_label = {actor.get_actor_label(): actor for actor in actors_api.get_all_level_actors()}
light_changes = {}
for label, intensity in (
    ("LB_PR006_V054_OperatorTaskLight", 180.0),
    ("LB_PR006_V054_DriveTaskLight", 145.0),
):
    light = by_label.get(label)
    if not isinstance(light, unreal.SpotLight):
        raise RuntimeError(f"missing inherited PR-006 light {label}")
    component = light.spot_light_component
    before = float(component.get_editor_property("intensity"))
    component.set_editor_properties({
        "intensity": intensity,
        "attenuation_radius": 1150.0,
        "inner_cone_angle": 38.0,
        "outer_cone_angle": 67.0,
        "source_radius": 85.0,
        "soft_source_radius": 150.0,
    })
    light.tags = list(light.tags) + [unreal.Name("LB.Lighting.Calibrated.PR006.v206")]
    light_changes[label] = {"before_cd": before, "after_cd": intensity}

# One broad linear fixture bridges the two inherited ambient rows over PR-006.
cube = library.load_asset("/Engine/BasicShapes/Cube.Cube")
if not isinstance(cube, unreal.StaticMesh):
    raise RuntimeError("missing Engine cube")
fixture = actors_api.spawn_actor_from_class(
    unreal.StaticMeshActor, unreal.Vector(-1700.0, -2000.0, 820.0), unreal.Rotator())
fixture.set_actor_label(PREFIX + "LinearTaskLuminaire")
fixture.tags = common_tags + [unreal.Name("LB.Lighting.PR006.LinearFixture")]
fixture.static_mesh_component.set_static_mesh(cube)
fixture.set_actor_scale3d(unreal.Vector(6.5, 1.1, 0.09))
fixture.static_mesh_component.set_material(0, luminaire_material)
fixture.static_mesh_component.set_collision_enabled(unreal.CollisionEnabled.NO_COLLISION)
fixture.static_mesh_component.set_editor_property("can_ever_affect_navigation", False)
fixture.static_mesh_component.set_editor_property("cast_shadow", False)

rect = actors_api.spawn_actor_from_class(
    unreal.RectLight, unreal.Vector(-1700.0, -2000.0, 805.0), unreal.Rotator(-90.0, 0.0, 0.0))
rect.set_actor_label(PREFIX + "LinearTaskRect")
rect.tags = common_tags + [unreal.Name("LB.Lighting.PR006.LinearFixture")]
rect_component = rect.get_component_by_class(unreal.RectLightComponent)
rect_component.set_editor_properties({
    "intensity": 9.0,
    "source_width": 650.0,
    "source_height": 110.0,
    "attenuation_radius": 1250.0,
    "cast_shadows": False,
    "light_color": unreal.Color(218, 228, 229, 255),
})

# A precise 50 mm equipment-zone perimeter sits above the 12 mm concrete inset.
zone_parts = []
for label, location, scale in (
    ("ZoneNorth", (-1700.0, -2267.5, 1.35), (8.2, 0.05, 0.018)),
    ("ZoneSouth", (-1700.0, -1732.5, 1.35), (8.2, 0.05, 0.018)),
    ("ZoneWest", (-2110.0, -2000.0, 1.35), (0.05, 5.35, 0.018)),
    ("ZoneEast", (-1290.0, -2000.0, 1.35), (0.05, 5.35, 0.018)),
):
    actor = actors_api.spawn_actor_from_class(unreal.StaticMeshActor, unreal.Vector(*location), unreal.Rotator())
    actor.set_actor_label(PREFIX + label)
    actor.tags = common_tags + [unreal.Name("LB.Environment.Floor.EquipmentZone")]
    actor.static_mesh_component.set_static_mesh(cube)
    actor.set_actor_scale3d(unreal.Vector(scale[0], scale[1], scale[2]))
    actor.static_mesh_component.set_material(0, zone_material)
    actor.static_mesh_component.set_collision_enabled(unreal.CollisionEnabled.NO_COLLISION)
    actor.static_mesh_component.set_editor_property("can_ever_affect_navigation", False)
    actor.static_mesh_component.set_editor_property("cast_shadow", False)
    zone_parts.append(actor)


def add_camera(label, location, target, fov):
    actor = actors_api.spawn_actor_from_class(unreal.CameraActor, unreal.Vector(*location), unreal.Rotator())
    actor.set_actor_label(PREFIX + "CAM_" + label)
    actor.tags = common_tags + [unreal.Name("LB.Camera.Fixed.PR006.v206")]
    actor.set_actor_rotation(
        unreal.MathLibrary.find_look_at_rotation(actor.get_actor_location(), unreal.Vector(*target)), False)
    actor.camera_component.set_editor_properties({
        "field_of_view": fov,
        "aspect_ratio": 16.0 / 9.0,
        "constrain_aspect_ratio": True,
    })
    return actor


cameras = [
    add_camera("OperatorRelease", (-1080, -2860, 285), (-1700, -2000, 142), 52.0),
    add_camera("DriveRelease", (-1080, -1140, 300), (-1700, -2000, 150), 52.0),
    add_camera("ConnectedRelease", (-620, -3300, 560), (-1700, -2000, 165), 58.0),
]

# Static authority check before saving.
all_actors = actors_api.get_all_level_actors()
stations = [actor for actor in all_actors if isinstance(actor, unreal.LBPR006Station)]
expected = {}
for index in range(1, 10):
    expected[f"LB_PR006_V054_PR006_LowerRoll_{index:02d}"] = f"PR006_LowerRollMover_{index:02d}"
for index in range(1, 11):
    expected[f"LB_PR006_V054_PR006_UpperRoll_{index:02d}"] = f"PR006_UpperRollMover_{index:02d}"
expected.update({
    "LB_PR006_V054_PR006_UpperCassette_Operator": "PR006_UpperCassetteMover",
    "LB_PR006_V054_PR006_UpperCassette_Drive": "PR006_UpperCassetteMover",
})
for index, suffix in enumerate(("-1_-1", "-1_+1", "+1_-1", "+1_+1"), 1):
    expected[f"LB_PR006_V054_PR006_GapCylinder_{suffix}"] = f"PR006_GapCylinderMover_{index:02d}"
for index in range(1, 4):
    expected[f"LB_PR006_V054_PR006_DriveMotor_{index:02d}"] = f"PR006_DriveMotorMover_{index:02d}"
by_label = {actor.get_actor_label(): actor for actor in all_actors}
binding_rows = []
for label, expected_parent in expected.items():
    actor = by_label.get(label)
    root = actor.static_mesh_component if isinstance(actor, unreal.StaticMeshActor) else None
    parent = root.get_attach_parent() if root else None
    binding_rows.append({
        "actor": label,
        "expected_parent": expected_parent,
        "actual_parent": parent.get_name() if parent else None,
    })

failures = []
if len(stations) != 1:
    failures.append(f"expected one PR-006 authority, found {len(stations)}")
if any(row["actual_parent"] != row["expected_parent"] for row in binding_rows):
    failures.append("one or more inherited PR-006 mover attachments changed")
if len(created) != 6:
    failures.append(f"expected six source modules, found {len(created)}")
if len(zone_parts) != 4 or len(cameras) != 3:
    failures.append("equipment-zone or fixed-camera count mismatch")
if not levels.save_current_level():
    failures.append("could not save v206")
library.save_directory(DEST, only_if_is_dirty=False, recursive=True)

base_hash_after = hashlib.sha256(base_file.read_bytes()).hexdigest().upper()
if base_hash_after != base_hash_before:
    failures.append("protected retained v107 parent hash changed")

map_file = ROOT / "Content/LineBoss/Maps/LB_PressShop_PR006ReleaseArtCandidate_v206.umap"
report = {
    "$schema": "cairnwell/audit/press-shop-pr006-release-art-build-v206/v1",
    "generated_utc": datetime.now(timezone.utc).isoformat(),
    "status": ("PR006_V206_SOURCE_DETAIL_AND_CALIBRATED_LIGHTING_BUILD_PASS__RUNTIME_AND_VISUAL_GATES_REQUIRED__NOT_PROMOTED"
               if not failures else "PR006_V206_BUILD_FAIL__NOT_PROMOTED"),
    "source_map": BASE,
    "map": MAP,
    "source_manifest": str(MANIFEST.relative_to(ROOT)).replace("\\", "/"),
    "source_module_count": len(created),
    "import_rows": import_rows,
    "equipment_zone_part_count": len(zone_parts),
    "fixed_cameras": [camera.get_actor_label() for camera in cameras],
    "light_changes": light_changes,
    "broad_rect_intensity": 9.0,
    "pr006_authority_count": len(stations),
    "pr006_mover_binding_count": len(binding_rows),
    "pr006_mover_bindings": binding_rows,
    "protected_v107_sha256_before": base_hash_before,
    "protected_v107_sha256_after": base_hash_after,
    "map_sha256": hashlib.sha256(map_file.read_bytes()).hexdigest().upper() if map_file.exists() else None,
    "datum_changed": False,
    "strip_or_transition_changed": False,
    "runtime_authority_changed": False,
    "promotion_authorized": False,
    "failures": failures,
}
OUT.parent.mkdir(parents=True, exist_ok=True)
OUT.write_text(json.dumps(report, indent=2), encoding="utf-8")
print(json.dumps(report, indent=2))
if failures:
    raise RuntimeError("; ".join(failures))
unreal.SystemLibrary.quit_editor()
