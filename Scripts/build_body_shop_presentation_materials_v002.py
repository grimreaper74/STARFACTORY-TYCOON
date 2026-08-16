"""Build and bind the isolated Body Shop Presentation/Materials_v002 pack.

Run only after the independent environment/LOD v001 validation passes.  The
script refuses overwrite, preflights every mutable mesh, protects the C-gun,
shared v002 source and prototype map by hash, and records every package delta.
"""
from __future__ import annotations

from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import shutil

import unreal


PROJECT = Path(unreal.Paths.project_dir()).resolve()
EXPECTED_PROJECT = Path(r"C:\Users\greg_\Projects\LineBossCarFactory_Unreal 5.8").resolve()
DEST = "/Game/LineBoss/BodyShop/Experimental/v001/Presentation/Materials_v002"
LAYERED_SOURCE = "/Game/LineBoss/Robots/Shared/Materials/Candidate_v002/M_LB_SupportRobot_LayeredPaint_v002"
LAYERED_MASTER = DEST + "/M_LB_BodyShop_LayeredPaint_Master_v002"
FUNCTIONAL_MASTER = DEST + "/M_LB_BodyShop_Functional_Master_v002"
MAP_FILE = PROJECT / "Content/LineBoss/BodyShop/Experimental/v001/Maps/LB_BodyShop_Prototype_v001.umap"
PATCH_RECEIPT = PROJECT / "Saved/Audits/BodyShop/Experimental_v001/environment_lod_release_candidate_patch_v001.json"
ENV_VALIDATION = PROJECT / "Saved/Audits/BodyShop/Experimental_v001/environment_lod_release_candidate_validation_v001.json"
SOURCE_AUDIT = PROJECT / "Saved/Audits/lb_support_robot_shared_materials_candidate_v002.json"
AUDIT = PROJECT / "Saved/Audits/BodyShop/Experimental_v001/presentation_materials_v002_build.json"
BACKUP_ROOT = PROJECT / "Saved/Quarantine/BodyShop/PresentationMaterials_v002_PreBind"
TARGET_SCREENS = [1.0, 0.55, 0.25]
WORLD_GRID = "/Engine/EngineMaterials/WorldGridMaterial.WorldGridMaterial"

SOURCE_HASHES = {
    PROJECT / "Content/LineBoss/Robots/Shared/Materials/Candidate_v002/M_LB_SupportRobot_LayeredPaint_v002.uasset":
        "F98F5DDE21E2A24FA38E22DBBD5B8123FFE86D9C71FB93065F770994F19FC832",
    PROJECT / "Content/Surface_Forge/Textures/Metal_Paint_Chips/T_Base_Color_Metal_Paint_Chips.uasset":
        "2AC6A5A9DF127571AA2313526248F66292E60706308963EB5DC8311F4EF206D9",
    PROJECT / "Content/Surface_Forge/Textures/Metal_Paint_Chips/T_Normal_Metal_Paint_Chips.uasset":
        "05F32BB657FA26693CC458C947BEE21B186AD99515B83625B9EDF3324E415EDB",
    PROJECT / "Content/Surface_Forge/Textures/Metal_Paint_Chips/T_ORD_Metal_Paint_Chips.uasset":
        "3DCA161FEDCBC6E1C1E522AEF9CB386EED0F0BA6EEB4B4D69C67BEB114CC77C1",
}
SOURCE_AUDIT_SHA256 = "3D2B614AAC901659868AB7117C02D4AA4701F28527502CBE4AAF8D94A77881C8"
CGUN = "/Game/LineBoss/Candidates/WeldShop/Robots/WeldRobotRuntime_v001/Tools/SpotGun/SM_LB_WeldTool_SpotGun_v001"
CGUN_FILE = PROJECT / "Content/LineBoss/Candidates/WeldShop/Robots/WeldRobotRuntime_v001/Tools/SpotGun/SM_LB_WeldTool_SpotGun_v001.uasset"
CGUN_HASH = "79DAA22563EE54BC1F3C04C98B9CAEC7E22A1F01F7E65E9E76B147B4ABBC27BC"
CGUN_MATERIAL = "/Game/LineBoss/Candidates/WeldShop/Robots/WeldRobotRuntime_v001/Materials/M_LB_WeldTool_SpotGun_PBR_v001.M_LB_WeldTool_SpotGun_PBR_v001"

MESHES = {
    "SM_LB_BodyShop_UnderbodyFixture_v001": ("/Game/LineBoss/Candidates/WeldShop/BodyShopUnderbodySlice_v001/Fixture/SM_LB_BodyShop_UnderbodyFixture_v001", [6528, 4398, 2570], ["M_LB_BS_GraphiteTooling", "M_LB_BS_StructuralLightGrey"]),
    "SM_LB_BodyShopRobot_Base_v001": ("/Game/LineBoss/Candidates/WeldShop/BodyShopUnderbodySlice_v001/Robot/SM_LB_BodyShopRobot_Base_v001", [20558, 9544, 3670], ["M_LB_BS_CreamPaint"]),
    "SM_LB_BodyShopRobot_J1_v001": ("/Game/LineBoss/Candidates/WeldShop/BodyShopUnderbodySlice_v001/Robot/SM_LB_BodyShopRobot_J1_v001", [21818, 10130, 3894], ["M_LB_BS_CreamPaint"]),
    "SM_LB_BodyShopRobot_J2_v001": ("/Game/LineBoss/Candidates/WeldShop/BodyShopUnderbodySlice_v001/Robot/SM_LB_BodyShopRobot_J2_v001", [16337, 7597, 2923], ["M_LB_BS_CreamPaint", "M_LB_BS_BlackMotor"]),
    "SM_LB_BodyShopRobot_J3_v001": ("/Game/LineBoss/Candidates/WeldShop/BodyShopUnderbodySlice_v001/Robot/SM_LB_BodyShopRobot_J3_v001", [17138, 7968, 3068], ["M_LB_BS_CreamPaint", "M_LB_BS_BlackMotor"]),
    "SM_LB_BodyShopRobot_J4_v001": ("/Game/LineBoss/Candidates/WeldShop/BodyShopUnderbodySlice_v001/Robot/SM_LB_BodyShopRobot_J4_v001", [9758, 4530, 1742], ["M_LB_BS_BlackMotor"]),
    "SM_LB_BodyShopRobot_J5_v001": ("/Game/LineBoss/Candidates/WeldShop/BodyShopUnderbodySlice_v001/Robot/SM_LB_BodyShopRobot_J5_v001", [76, 52, 28], ["M_LB_BS_BlackMotor"]),
    "SM_LB_BodyShopTool_PanelPick8Cup_v001": ("/Game/LineBoss/Candidates/WeldShop/BodyShopUnderbodySlice_v001/Tools/SM_LB_BodyShopTool_PanelPick8Cup_v001", [2696, 2152, 1880], ["M_LB_BS_BrushedSteel", "M_LB_BS_CreamPaint", "M_LB_BS_BlackMotor", "M_LB_BS_VacuumRubber"]),
    "SM_LB_BodyShop_VisionGate_v001": ("/Game/LineBoss/Candidates/WeldShop/BodyShopUnderbodySlice_v001/Vision/SM_LB_BodyShop_VisionGate_v001", [1728, 1584, 1440], ["M_LB_BS_StructuralLightGrey", "M_LB_BS_GraphiteTooling", "M_LB_BS_ScannerLens", "M_LB_BS_SafetyYellow", "M_LB_BS_StatusGreen", "M_LB_BS_StatusAmber", "M_LB_BS_StatusRed"]),
}

# Values are linear RGB. Cream/black retain the corrected shared-v002 Surface
# Forge normal/ORD/paint-chip parameter family; the other ten use the local
# restrained world-space functional master.
PALETTE = {
    "M_LB_BS_CreamPaint": ("MI_LB_BodyShop_CreamPaint_v002", "layered", (0.637596874, 0.571124829, 0.381326011), 0.18, 0.54, 0.28, (0, 0, 0), 0.0),
    "M_LB_BS_BlackMotor": ("MI_LB_BodyShop_BlackMotor_v002", "layered", (0.014443844, 0.017641954, 0.021219010), 0.25, 0.56, 0.28, (0, 0, 0), 0.0),
    "M_LB_BS_StructuralLightGrey": ("MI_LB_BodyShop_StructuralLightGrey_v002", "functional", (0.318546778, 0.391572478, 0.450785783), 0.65, 0.32, 0.035, (0, 0, 0), 0.0),
    "M_LB_BS_BrushedSteel": ("MI_LB_BodyShop_BrushedSteel_v002", "functional", (0.147027266, 0.194617830, 0.234550582), 0.82, 0.27, 0.045, (0, 0, 0), 0.0),
    "M_LB_BS_GraphiteTooling": ("MI_LB_BodyShop_GraphiteTooling_v002", "functional", (0.010960094, 0.018500220, 0.024157632), 0.62, 0.34, 0.030, (0, 0, 0), 0.0),
    "M_LB_BS_EmeraldPanel": ("MI_LB_BodyShop_EmeraldPanel_v002", "functional", (0.003035270, 0.194617830, 0.086500462), 0.28, 0.34, 0.025, (0, 0, 0), 0.0),
    "M_LB_BS_SafetyYellow": ("MI_LB_BodyShop_SafetyYellow_v002", "functional", (0.887923118, 0.396755231, 0.0), 0.22, 0.36, 0.025, (0, 0, 0), 0.0),
    "M_LB_BS_VacuumRubber": ("MI_LB_BodyShop_VacuumRubber_v002", "functional", (0.003346536, 0.004776953, 0.006048833), 0.02, 0.74, 0.018, (0, 0, 0), 0.0),
    "M_LB_BS_ScannerLens": ("MI_LB_BodyShop_ScannerLens_v002", "functional", (0.002731743, 0.144128471, 0.262250658), 0.15, 0.22, 0.015, (0.0, 0.35, 0.65), 0.22),
    "M_LB_BS_StatusGreen": ("MI_LB_BodyShop_StatusGreen_v002", "functional", (0.015996293, 0.644479682, 0.212230757), 0.05, 0.24, 0.010, (0.015996293, 0.644479682, 0.212230757), 3.0),
    "M_LB_BS_StatusAmber": ("MI_LB_BodyShop_StatusAmber_v002", "functional", (1.0, 0.337163615, 0.009721217), 0.05, 0.24, 0.010, (1.0, 0.337163615, 0.009721217), 3.0),
    "M_LB_BS_StatusRed": ("MI_LB_BodyShop_StatusRed_v002", "functional", (0.745404210, 0.026241222, 0.048171824), 0.05, 0.24, 0.010, (0.745404210, 0.026241222, 0.048171824), 3.0),
}

lib = unreal.EditorAssetLibrary
tools = unreal.AssetToolsHelpers.get_asset_tools()
mel = unreal.MaterialEditingLibrary
USAGE_PROPERTY = "used_with_instanced_static_meshes"


def fail(message: str) -> None:
    raise RuntimeError("BODYSHOP_PRESENTATION_MATERIALS_V002_FAIL: " + message)


def digest(path: Path) -> str:
    value = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            value.update(block)
    return value.hexdigest().upper()


def package_file(asset: str) -> Path:
    return PROJECT / "Content" / Path(asset.removeprefix("/Game/")).with_suffix(".uasset")


def load_json(path: Path) -> dict:
    if not path.is_file():
        fail("missing prerequisite receipt: " + str(path))
    return json.loads(path.read_text(encoding="utf-8"))


def expr(material, cls, x, y):
    return mel.create_material_expression(material, cls, x, y)


def connect_required(source, source_output, target, target_input, label):
    if not mel.connect_material_expressions(source, source_output, target, target_input):
        fail("functional-master graph connection failed: " + label)


def connect_property_required(source, source_output, material_property, label):
    if not mel.connect_material_property(source, source_output, material_property):
        fail("functional-master output connection failed: " + label)


def colour(values):
    return unreal.LinearColor(float(values[0]), float(values[1]), float(values[2]), 1.0)


def instanced_static_mesh_usage():
    """Resolve the one approved usage enum across UE 5.8 Python spellings."""
    preferred = "MATUSAGE_INSTANCED_STATIC_MESHES"
    if hasattr(unreal.MaterialUsage, preferred):
        return getattr(unreal.MaterialUsage, preferred)
    candidates = [name for name in dir(unreal.MaterialUsage)
                  if "INSTANCED" in name.upper()
                  and "STATIC" in name.upper()
                  and "MESH" in name.upper()
                  and "SKINNED" not in name.upper()]
    if len(candidates) != 1:
        fail("could not resolve MATUSAGE_InstancedStaticMeshes: " + str(candidates))
    return getattr(unreal.MaterialUsage, candidates[0])


def preflight(subsystem):
    if PROJECT != EXPECTED_PROJECT or str(unreal.SystemLibrary.get_game_name()) != "LineBossCarFactory":
        fail("project identity drift")
    patch = load_json(PATCH_RECEIPT)
    validation = load_json(ENV_VALIDATION)
    if patch.get("$schema") != "lineboss/audit/bodyshop/environment-lod-release-candidate-patch-v001/v1" or patch.get("status") != "PASS__ISOLATED_BODYSHOP_ENVIRONMENT_AND_LOD_RELEASE_CANDIDATE_V001":
        fail("environment/LOD patch gate has not passed")
    if validation.get("$schema") != "lineboss/audit/bodyshop/environment-lod-release-candidate-validation-v001/v1" or validation.get("status") != "PASS__EXACT_BODYSHOP_ENVIRONMENT_LIGHTING_CAMERAS_GRID_AND_LOD_VALIDATION_V001":
        fail("independent environment/LOD validation gate has not passed")
    if not MAP_FILE.is_file() or digest(MAP_FILE) != patch.get("map_sha256_after") or validation.get("map_sha256") != patch.get("map_sha256_after"):
        fail("isolated Body Shop map hash drift")
    if digest(SOURCE_AUDIT) != SOURCE_AUDIT_SHA256:
        fail("shared v002 source audit hash drift")
    for path, expected in SOURCE_HASHES.items():
        if not path.is_file() or digest(path) != expected:
            fail("approved shared-v002/Surface Forge source drift: " + str(path))
    targets = [LAYERED_MASTER, FUNCTIONAL_MASTER] + [DEST + "/" + row[0] for row in PALETTE.values()]
    existing = [path for path in targets if lib.does_asset_exist(path)]
    if existing:
        fail("refusing to overwrite Materials_v002 assets: " + str(existing))
    if lib.does_directory_exist(DEST) and lib.list_assets(DEST, recursive=True, include_folder=False):
        fail("Materials_v002 namespace is not empty")

    cgun = lib.load_asset(CGUN)
    if (not isinstance(cgun, unreal.StaticMesh) or not CGUN_FILE.is_file()
            or digest(CGUN_FILE) != CGUN_HASH
            or len(cgun.get_editor_property("static_materials")) != 1
            or cgun.get_material(0) is None or cgun.get_material(0).get_path_name() != CGUN_MATERIAL):
        fail("protected C-gun PBR contract drift")

    meshes, rows = {}, {}
    patch_rows = patch.get("mesh_fingerprints_after", {})
    validation_rows = validation.get("meshes", {})
    for name, (asset, triangles, slots) in MESHES.items():
        mesh = lib.load_asset(asset)
        if not isinstance(mesh, unreal.StaticMesh) or mesh.get_path_name() != asset + "." + name:
            fail("final mesh identity drift: " + name)
        actual_slots = [str(row.get_editor_property("material_slot_name")) for row in mesh.get_editor_property("static_materials")]
        actual_triangles = [int(mesh.get_num_triangles(i)) for i in range(mesh.get_num_lods())]
        screens = [round(float(v), 4) for v in subsystem.get_lod_screen_sizes(mesh)]
        materials = [mesh.get_material(i).get_path_name() if mesh.get_material(i) else None for i in range(len(actual_slots))]
        if actual_slots != slots or actual_triangles != triangles or screens != TARGET_SCREENS:
            fail("geometry/LOD/semantic-slot contract drift: " + name)
        if materials != [WORLD_GRID] * len(slots):
            fail("final mesh is not at the exact WorldGrid replacement precondition: " + name)
        if (int(subsystem.get_simple_collision_count(mesh)) != 0
                or int(subsystem.get_convex_collision_count(mesh)) != 0
                or bool(subsystem.get_nanite_settings(mesh).get_editor_property("enabled"))):
            fail("collision/Nanite contract drift: " + name)
        for recorded in (patch_rows.get(name, {}), validation_rows.get(name, {})):
            if (recorded.get("triangles") != triangles
                    or recorded.get("lod_screen_sizes") != TARGET_SCREENS
                    or [row.get("slot") for row in recorded.get("materials", [])] != slots):
                fail("environment receipt mesh contract drift: " + name)
        path = package_file(asset)
        if digest(path) != patch.get("final_package_hashes_after", {}).get(asset):
            fail("post-environment final package hash drift: " + name)
        body = mesh.get_editor_property("body_setup")
        if (body is None
                or str(body.get_editor_property("collision_trace_flag"))
                != patch_rows[name].get("collision_trace_flag")):
            fail("collision trace contract drift: " + name)
        meshes[name] = mesh
        rows[name] = {"asset": asset, "sha256_before": digest(path), "triangles": triangles,
                      "lod_screen_sizes": screens, "slots": slots,
                      "lod_bounds_from_environment_patch": patch_rows[name].get("lod_bounds_cm")}
    return patch, validation, meshes, rows


def backup_meshes(rows):
    if BACKUP_ROOT.exists():
        fail("refusing to overwrite existing pre-bind backup: " + str(BACKUP_ROOT))
    files = {}
    for row in rows.values():
        source = package_file(row["asset"])
        target = BACKUP_ROOT / source.relative_to(PROJECT)
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source, target)
        if digest(source) != digest(target):
            fail("pre-bind backup hash mismatch: " + row["asset"])
        files[row["asset"]] = {"backup": str(target), "sha256": digest(target)}
    return files


def build_functional_master():
    material = tools.create_asset(FUNCTIONAL_MASTER.rsplit("/", 1)[-1], DEST,
                                  unreal.Material, unreal.MaterialFactoryNew())
    if not isinstance(material, unreal.Material):
        fail("could not create functional master")
    material.set_editor_properties({"two_sided": False, "blend_mode": unreal.BlendMode.BLEND_OPAQUE})
    # The fixture, handling EOAT and vision gate are presented through HISM
    # components at runtime.  Persist the required shader permutation on the
    # project-owned functional master before any MICs are created.
    usage = instanced_static_mesh_usage()
    mel.set_base_material_usage(material, usage, True)
    if not bool(material.get_editor_property(USAGE_PROPERTY)):
        fail("functional master rejected MATUSAGE_InstancedStaticMeshes")
    base = expr(material, unreal.MaterialExpressionVectorParameter, -700, -420)
    base.set_editor_properties({"parameter_name": "BaseColour", "default_value": colour((0.3, 0.3, 0.3))})
    connect_property_required(base, "", unreal.MaterialProperty.MP_BASE_COLOR, "BaseColour")
    metallic = expr(material, unreal.MaterialExpressionScalarParameter, -700, -180)
    metallic.set_editor_properties({"parameter_name": "Metallic", "default_value": 0.2})
    connect_property_required(metallic, "", unreal.MaterialProperty.MP_METALLIC, "Metallic")
    world = expr(material, unreal.MaterialExpressionWorldPosition, -1150, 80)
    axis = expr(material, unreal.MaterialExpressionConstant3Vector, -1150, 180)
    axis.set_editor_property("constant", unreal.LinearColor(0.0041, 0.0053, 0.0037, 1.0))
    dot = expr(material, unreal.MaterialExpressionDotProduct, -920, 100)
    connect_required(world, "", dot, "A", "WorldPosition -> Dot.A")
    connect_required(axis, "", dot, "B", "Axis -> Dot.B")
    wave = expr(material, unreal.MaterialExpressionSine, -700, 100)
    # UE 5.8 exposes Sine's only input as an unnamed pin.  "Input" silently
    # fails and produces a default-material fallback, so require the exact pin.
    connect_required(dot, "", wave, "", "Dot -> Sine")
    variation = expr(material, unreal.MaterialExpressionScalarParameter, -700, 220)
    variation.set_editor_properties({"parameter_name": "RoughnessVariation", "default_value": 0.025})
    varied = expr(material, unreal.MaterialExpressionMultiply, -470, 120)
    connect_required(wave, "", varied, "A", "Sine -> Variation.A")
    connect_required(variation, "", varied, "B", "Variation -> Variation.B")
    roughness = expr(material, unreal.MaterialExpressionScalarParameter, -470, 250)
    roughness.set_editor_properties({"parameter_name": "Roughness", "default_value": 0.4})
    rough_sum = expr(material, unreal.MaterialExpressionAdd, -240, 170)
    connect_required(roughness, "", rough_sum, "A", "Roughness -> Sum.A")
    connect_required(varied, "", rough_sum, "B", "Variation -> Sum.B")
    rough_sat = expr(material, unreal.MaterialExpressionSaturate, -20, 170)
    connect_required(rough_sum, "", rough_sat, "", "Sum -> Saturate")
    connect_property_required(rough_sat, "", unreal.MaterialProperty.MP_ROUGHNESS, "Roughness")
    emissive = expr(material, unreal.MaterialExpressionVectorParameter, -470, 430)
    emissive.set_editor_properties({"parameter_name": "EmissiveColour", "default_value": unreal.LinearColor(0, 0, 0, 1)})
    strength = expr(material, unreal.MaterialExpressionScalarParameter, -470, 550)
    strength.set_editor_properties({"parameter_name": "EmissiveStrength", "default_value": 0.0})
    emissive_out = expr(material, unreal.MaterialExpressionMultiply, -220, 470)
    connect_required(emissive, "", emissive_out, "A", "EmissiveColour -> Multiply.A")
    connect_required(strength, "", emissive_out, "B", "EmissiveStrength -> Multiply.B")
    connect_property_required(emissive_out, "", unreal.MaterialProperty.MP_EMISSIVE_COLOR, "Emissive")
    mel.recompile_material(material)
    if not lib.save_loaded_asset(material, only_if_is_dirty=False):
        fail("functional master save failed")
    if not bool(material.get_editor_property(USAGE_PROPERTY)):
        fail("functional master lost MATUSAGE_InstancedStaticMeshes after save")
    return material


def make_instances(layered, functional):
    result = {}
    for slot, (name, family, base, metallic, roughness, rough_var, emissive, strength) in PALETTE.items():
        instance = tools.create_asset(name, DEST, unreal.MaterialInstanceConstant,
                                      unreal.MaterialInstanceConstantFactoryNew())
        if not isinstance(instance, unreal.MaterialInstanceConstant):
            fail("could not create MIC: " + name)
        instance.set_editor_property("parent", layered if family == "layered" else functional)
        if family == "layered":
            mel.set_material_instance_vector_parameter_value(instance, "PaintColour", colour(base))
            mel.set_material_instance_vector_parameter_value(instance, "ExposedMetalColour", colour((0.0185, 0.0232, 0.0262)))
            mel.set_material_instance_vector_parameter_value(instance, "DustColour", colour((0.1441, 0.1221, 0.0865)))
            # Body Shop links use normalized-per-primitive UVs.  The audited
            # conservative values keep chips fine and suppress the coarse,
            # blocky normal/dust response seen with shared preview defaults.
            scalars = {"TextureScale": 18.0, "WearContrast": 2.45,
                       "PaintCoverageBias": 0.93,
                       "DustAmount": 0.035, "NormalStrength": 0.05,
                       "BaseRoughness": roughness, "RoughnessVariation": rough_var,
                       "DustRoughness": 0.88, "ExposedMetallic": 0.72}
        else:
            mel.set_material_instance_vector_parameter_value(instance, "BaseColour", colour(base))
            mel.set_material_instance_vector_parameter_value(instance, "EmissiveColour", colour(emissive))
            scalars = {"Metallic": metallic, "Roughness": roughness,
                       "RoughnessVariation": rough_var, "EmissiveStrength": strength}
        for parameter, value in scalars.items():
            mel.set_material_instance_scalar_parameter_value(instance, parameter, float(value))
        mel.update_material_instance(instance)
        if not lib.save_loaded_asset(instance, only_if_is_dirty=False):
            fail("MIC save failed: " + name)
        result[slot] = instance
    return result


def main():
    subsystem = unreal.get_editor_subsystem(unreal.StaticMeshEditorSubsystem)
    if subsystem is None:
        fail("StaticMeshEditorSubsystem unavailable")
    patch, validation, meshes, mesh_rows = preflight(subsystem)
    map_before = digest(MAP_FILE)
    cgun_before = digest(CGUN_FILE)
    sources_before = {str(path): digest(path) for path in SOURCE_HASHES}
    backups = backup_meshes(mesh_rows)

    layered = lib.duplicate_asset(LAYERED_SOURCE, LAYERED_MASTER)
    if not isinstance(layered, unreal.Material):
        fail("local corrected shared-v002 master duplication failed")
    if not lib.save_loaded_asset(layered, only_if_is_dirty=False):
        fail("local corrected shared-v002 master save failed")
    functional = build_functional_master()
    instances = make_instances(layered, functional)
    binding_rows = {}
    for name, mesh in meshes.items():
        assignments = []
        for index, slot_row in enumerate(mesh.get_editor_property("static_materials")):
            slot = str(slot_row.get_editor_property("material_slot_name"))
            material = instances.get(slot)
            if material is None:
                fail("unmapped slot after preflight: " + name + ":" + slot)
            mesh.set_material(index, material)
            assignments.append({"index": index, "slot": slot, "material": material.get_path_name()})
        if not lib.save_loaded_asset(mesh, only_if_is_dirty=False):
            fail("mesh material save failed: " + name)
        binding_rows[name] = assignments
    unreal.AutomationUtilsBlueprintLibrary.finish_all_asset_compilation()

    if digest(MAP_FILE) != map_before or digest(CGUN_FILE) != cgun_before:
        fail("protected map or C-gun changed")
    if {str(path): digest(path) for path in SOURCE_HASHES} != sources_before:
        fail("shared v002 source or Surface Forge texture changed")
    for name, mesh in meshes.items():
        _, triangles, slots = MESHES[name]
        if ([int(mesh.get_num_triangles(i)) for i in range(mesh.get_num_lods())] != triangles
                or [round(float(v), 4) for v in subsystem.get_lod_screen_sizes(mesh)] != TARGET_SCREENS
                or [str(row.get_editor_property("material_slot_name")) for row in mesh.get_editor_property("static_materials")] != slots):
            fail("post-bind geometry/LOD/slot drift: " + name)
        expected = [instances[slot].get_path_name() for slot in slots]
        actual = [mesh.get_material(i).get_path_name() if mesh.get_material(i) else None for i in range(len(slots))]
        if actual != expected or any("WorldGrid" in value for value in actual):
            fail("post-bind semantic material drift: " + name)
        mesh_rows[name]["sha256_after"] = digest(package_file(MESHES[name][0]))
        mesh_rows[name]["assignments"] = binding_rows[name]

    asset_paths = sorted({path.split(".", 1)[0] for path in lib.list_assets(DEST, recursive=True, include_folder=False)})
    expected_paths = sorted([LAYERED_MASTER, FUNCTIONAL_MASTER] + [DEST + "/" + row[0] for row in PALETTE.values()])
    if asset_paths != expected_paths:
        fail("exact Materials_v002 asset inventory drift: " + str(asset_paths))
    payload = {
        "$schema": "lineboss/audit/bodyshop/presentation-materials-v002-build/v1",
        "generated_utc": datetime.now(timezone.utc).isoformat(),
        "status": "PASS__ISOLATED_BODYSHOP_PRESENTATION_MATERIALS_V002_BUILT_AND_BOUND",
        "namespace": DEST, "asset_count": len(asset_paths), "assets": asset_paths,
        "environment_patch_receipt_sha256": digest(PATCH_RECEIPT),
        "environment_validation_receipt_sha256": digest(ENV_VALIDATION),
        "map_sha256_before_and_after": map_before,
        "source_hashes_before_and_after": sources_before,
        "protected_cgun": {"mesh": CGUN, "sha256_before_and_after": cgun_before,
                           "material": CGUN_MATERIAL},
        "mesh_packages": mesh_rows, "recoverable_prebind_backups": backups,
        "shared_candidate_v004_used": False, "source_assets_modified": False,
        "maps_modified": False, "meshy_credits_used_by_codex": 0,
        "functional_compile_contract": {
            "all_graph_connections_checked": True,
            "sine_input_pin": "unnamed",
            "layered_master_explicitly_saved": True,
            "usage_enum": str(instanced_static_mesh_usage()),
            "used_with_instanced_static_meshes": True},
        "promotion_authorized": False, "failures": []}
    AUDIT.parent.mkdir(parents=True, exist_ok=True)
    AUDIT.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    unreal.log("LINE_BOSS_BODYSHOP_PRESENTATION_MATERIALS_V002_BUILD_PASS")
    print(json.dumps(payload, indent=2))


if __name__ == "__main__":
    main()
