"""Build standalone local-origin PR-005 Candidate_v002 Unreal assembly study."""

import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path

import unreal


ROOT = Path(unreal.Paths.project_dir())
MAP = "/Game/LineBoss/Maps/LB_PressShop_PR005ExteriorEnclosureAssemblyCandidate_v003"
ROOT_ASSET = "/Game/LineBoss/Candidates/PressShop/PR005/ExteriorEnclosure_v003"
MESHES = ROOT_ASSET + "/Meshes"
MATERIALS = ROOT_ASSET + "/Materials"
MANIFEST_PATH = ROOT / "SourceAssets/Candidate/PressShop/PR005/UnrealDerived_v003/PR005_EXTERIOR_ENCLOSURE_UNREAL_DERIVED_MANIFEST_v003.json"
OUT = ROOT / "Saved/Audits/PressShopIntegration/press_shop_pr005_exterior_enclosure_assembly_build_v003.json"
manifest = json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))
library = unreal.EditorAssetLibrary
tools = unreal.AssetToolsHelpers.get_asset_tools()
materials_api = unreal.MaterialEditingLibrary
levels = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
actors_api = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)


def constant_material(name, colour, roughness, metallic=0.0, emissive=0.0, opacity=None):
    material = tools.create_asset(name, MATERIALS, unreal.Material, unreal.MaterialFactoryNew())
    if material is None:
        raise RuntimeError(f"could not create {name}")
    colour_node = materials_api.create_material_expression(material, unreal.MaterialExpressionConstant3Vector, -300, -60)
    colour_node.set_editor_property("constant", unreal.LinearColor(*colour, 1.0))
    rough = materials_api.create_material_expression(material, unreal.MaterialExpressionConstant, -300, 80)
    rough.set_editor_property("r", roughness)
    metal = materials_api.create_material_expression(material, unreal.MaterialExpressionConstant, -300, 145)
    metal.set_editor_property("r", metallic)
    materials_api.connect_material_property(colour_node, "", unreal.MaterialProperty.MP_BASE_COLOR)
    materials_api.connect_material_property(rough, "", unreal.MaterialProperty.MP_ROUGHNESS)
    materials_api.connect_material_property(metal, "", unreal.MaterialProperty.MP_METALLIC)
    if emissive > 0.0:
        multiply = materials_api.create_material_expression(material, unreal.MaterialExpressionMultiply, -80, -110)
        strength = materials_api.create_material_expression(material, unreal.MaterialExpressionConstant, -300, -150)
        strength.set_editor_property("r", emissive)
        materials_api.connect_material_expressions(colour_node, "", multiply, "A")
        materials_api.connect_material_expressions(strength, "", multiply, "B")
        materials_api.connect_material_property(multiply, "", unreal.MaterialProperty.MP_EMISSIVE_COLOR)
    if opacity is not None:
        material.set_editor_property("blend_mode", unreal.BlendMode.BLEND_TRANSLUCENT)
        opacity_node = materials_api.create_material_expression(material, unreal.MaterialExpressionConstant, -300, 215)
        opacity_node.set_editor_property("r", opacity)
        materials_api.connect_material_property(opacity_node, "", unreal.MaterialProperty.MP_OPACITY)
    materials_api.recompile_material(material)
    library.save_loaded_asset(material, only_if_is_dirty=False)
    return material


if library.does_asset_exist(MAP):
    raise RuntimeError(f"refusing to overwrite preserved validation map {MAP}")
if not levels.new_level(MAP):
    raise RuntimeError(f"could not create {MAP}")

materials = {
    "CA_MW_FoundryCharcoal": constant_material("M_CA_MW_PR005_FoundryCharcoal_v003", (0.025, 0.032, 0.038), 0.62, 0.18),
    "CA_MW_SafetyYellow": constant_material("M_CA_MW_PR005_SafetyYellow_v003", (0.60, 0.30, 0.012), 0.48, 0.08),
    "CA_MW_LaminatedInspectionGlass": constant_material("M_CA_MW_PR005_LaminatedInspectionGlass_v003", (0.025, 0.14, 0.13), 0.16, 0.05, opacity=0.32),
    "CA_MW_ServiceGrey": constant_material("M_CA_MW_PR005_ServiceGrey_v003", (0.24, 0.27, 0.29), 0.72, 0.12),
    "CA_MW_CairnwellGreen": constant_material("M_CA_MW_PR005_CairnwellGreen_v003", (0.008, 0.105, 0.072), 0.58, 0.10),
    "CA_MW_IdentityWhite": constant_material("M_CA_MW_PR005_IdentityWhite_v003", (0.72, 0.76, 0.77), 0.68),
    "CA_MW_WorkedSteel": constant_material("M_CA_MW_PR005_WorkedSteel_v003", (0.20, 0.22, 0.23), 0.32, 0.82),
    "CA_MW_StripSteel": constant_material("M_CA_MW_PR005_StripSteel_v003", (0.42, 0.46, 0.48), 0.22, 0.92),
    "CA_MW_HMIScreen": constant_material("M_CA_MW_PR005_HMIScreen_v003", (0.01, 0.22, 0.18), 0.24, 0.02, emissive=2.5),
    "CA_MW_EStopRed": constant_material("M_CA_MW_PR005_EStopRed_v003", (0.62, 0.008, 0.004), 0.38, 0.02),
    "floor": constant_material("M_CA_MW_PR005_ValidationFloor_v003", (0.115, 0.125, 0.132), 0.88),
}

common_tags = ["LB.Asset.Candidate.v003", "LB.Asset.CandidateNotPromoted", "LB.PR005.ExteriorEnclosure.AssemblyStudy"]
created = []
for row in manifest["assets"]:
    mesh = library.load_asset(f"{MESHES}/{row['asset_name']}")
    if not isinstance(mesh, unreal.StaticMesh):
        raise RuntimeError(f"missing validated mesh {row['asset_name']}")
    px, py, pz = row["pivot_m"]
    location = unreal.Vector(float(px) * 100.0, -float(py) * 100.0, float(pz) * 100.0)
    actor = actors_api.spawn_actor_from_class(unreal.StaticMeshActor, location, unreal.Rotator())
    actor.set_actor_label("LB_PR005_V003_" + row["asset_name"].replace("SM_CA_MW_PR005_", ""))
    actor.static_mesh_component.set_static_mesh(mesh)
    actor.static_mesh_component.set_collision_enabled(unreal.CollisionEnabled.NO_COLLISION)
    actor.static_mesh_component.set_mobility(
        unreal.ComponentMobility.STATIC if "EnclosureShell_Static" in row["asset_name"] else unreal.ComponentMobility.MOVABLE)
    for index, slot in enumerate(mesh.get_editor_property("static_materials")):
        role = str(slot.material_slot_name)
        if role not in materials:
            raise RuntimeError(f"unmapped material role {role} on {row['asset_name']}")
        actor.static_mesh_component.set_material(index, materials[role])
    actor.tags = [unreal.Name(value) for value in common_tags + [
        "LB.PR005.PresentationOnly.ReadabilityMover" if "ReadabilityMover" in row["asset_name"] else "LB.PR005.ExteriorModule",
        "LB.Authority.RuntimeMoverUnchanged",
    ]]
    created.append(actor)

cube = library.load_asset("/Engine/BasicShapes/Cube.Cube")
floor = actors_api.spawn_actor_from_class(unreal.StaticMeshActor, unreal.Vector(0.0, 0.0, -5.0), unreal.Rotator())
floor.set_actor_label("LB_PR005_V003_ValidationFloor")
floor.static_mesh_component.set_static_mesh(cube)
floor.set_actor_scale3d(unreal.Vector(18.0, 18.0, 0.10))
floor.static_mesh_component.set_material(0, materials["floor"])
floor.static_mesh_component.set_collision_profile_name(unreal.Name("BlockAll"))
floor.tags = [unreal.Name(value) for value in common_tags + ["LB.Validation.Floor"]]

for index, (x, y) in enumerate(((-260.0, -280.0), (260.0, -280.0), (-260.0, 280.0), (260.0, 280.0)), 1):
    light = actors_api.spawn_actor_from_class(unreal.RectLight, unreal.Vector(x, y, 520.0), unreal.Rotator(-90.0, 0.0, 0.0))
    light.set_actor_label(f"LB_PR005_V003_LinearLED_{index:02d}")
    light.get_component_by_class(unreal.RectLightComponent).set_editor_properties({
        "intensity": 52.0, "source_width": 520.0, "source_height": 90.0,
        "attenuation_radius": 900.0, "cast_shadows": True,
        "light_color": unreal.Color(220, 229, 230, 255),
    })
    light.tags = [unreal.Name(value) for value in common_tags + ["LB.Environment.Light.LinearLED"]]


def camera(label, location, target, fov):
    actor = actors_api.spawn_actor_from_class(unreal.CameraActor, unreal.Vector(*location), unreal.Rotator())
    actor.set_actor_label("LB_PR005_V003_CAM_" + label)
    actor.set_actor_rotation(unreal.MathLibrary.find_look_at_rotation(actor.get_actor_location(), unreal.Vector(*target)), False)
    actor.camera_component.set_editor_properties({"field_of_view": fov, "aspect_ratio": 16.0 / 9.0, "constrain_aspect_ratio": True})
    actor.tags = [unreal.Name(value) for value in common_tags + ["LB.Camera.Validation", "LB.Camera.Fixed.PR005Assembly.v003"]]
    return actor


cameras = [
    camera("OperatorThreeQuarter", (-780.0, 790.0, 430.0), (0.0, 0.0, 150.0), 48.0),
    camera("ProcessGlazing", (-610.0, -610.0, 255.0), (0.0, -285.0, 105.0), 46.0),
    camera("MaintenanceSide", (800.0, 520.0, 310.0), (80.0, -40.0, 145.0), 50.0),
    camera("ElevatedFlow", (-720.0, 900.0, 700.0), (0.0, 0.0, 120.0), 54.0),
]

mins, maxs = [1e9, 1e9, 1e9], [-1e9, -1e9, -1e9]
for actor in created:
    origin, extent = actor.get_actor_bounds(False, False)
    for i, value in enumerate((origin.x, origin.y, origin.z)):
        e = (extent.x, extent.y, extent.z)[i]
        mins[i] = min(mins[i], value - e)
        maxs[i] = max(maxs[i], value + e)
expected_min = [-365.0, -518.0, 0.0]
expected_max = [286.95, 518.0, 355.0]
bound_delta = [mins[i] - expected_min[i] for i in range(3)] + [maxs[i] - expected_max[i] for i in range(3)]
failures = []
if len(created) != 9 or len(cameras) != 4:
    failures.append("unexpected module or camera count")
if max(abs(value) for value in bound_delta) > 0.2:
    failures.append(f"assembly bounds drift cm={bound_delta}")
if not levels.save_current_level():
    failures.append("could not save validation map")
library.save_directory(ROOT_ASSET, only_if_is_dirty=False, recursive=True)

report = {
    "$schema": "cairnwell/audit/press-shop-pr005-exterior-enclosure-assembly-build-v003/v1",
    "generated_utc": datetime.now(timezone.utc).isoformat(),
    "status": "PASS__LOCAL_ORIGIN_NINE_MODULE_ASSEMBLY_WITH_CONTROLLED_MATERIALS_AND_FIXED_CAMERAS__VISUAL_GATE_REQUIRED__NOT_INTEGRATED_NOT_PROMOTED" if not failures else "FAIL__PR005_V003_ASSEMBLY_BUILD__NOT_INTEGRATED_NOT_PROMOTED",
    "map": MAP, "module_count": len(created),
    "assembly_bounds_min_cm": [round(v, 4) for v in mins],
    "assembly_bounds_max_cm": [round(v, 4) for v in maxs],
    "expected_bounds_min_cm": expected_min, "expected_bounds_max_cm": expected_max,
    "fixed_cameras": [actor.get_actor_label() for actor in cameras],
    "collision_scope": "validation floor only; production collision not authored",
    "world_placement": "LOCAL_ORIGIN_STUDY_ONLY__TBC_NOT_INVENTED",
    "runtime_movers_replaced": False, "v053_or_production_maps_changed": False,
    "promotion_authorized": False, "failures": failures,
}
OUT.parent.mkdir(parents=True, exist_ok=True)
OUT.write_text(json.dumps(report, indent=2), encoding="utf-8")
print(json.dumps({"status": report["status"], "bounds": [mins, maxs], "failures": failures}, indent=2))
if failures:
    raise RuntimeError("; ".join(failures))
