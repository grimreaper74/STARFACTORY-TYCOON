"""Promote the verified UE-native MaterialFlow v002 scratch into its final namespace.

The geometry is not reimported here: the preceding native legacy-FbxFactory
scratch receipt proved all ten meshes at exact bounds, pivots, UVs, slots and
3,792 triangles with the only viable UE recipe (absolute vertices on neutral
nodes).  This promotion moves those verified native meshes to stable semantic
paths, imports the four genuinely new texture families, binds native material
instances, and revalidates the complete 30-package closure.
"""

from __future__ import annotations

import hashlib
import json
import re
import traceback
from datetime import datetime, timezone
from pathlib import Path

import unreal


PROJECT = Path(unreal.Paths.project_dir()).resolve()
EXPECTED_PROJECT = Path(r"C:/Users/greg_/Projects/LineBossCarFactory_Unreal 5.8").resolve()
SOURCE_ART = PROJECT / "ArtSource/Claude_PressShop_MaterialFlowPack_v001"
SOURCE_PREP = PROJECT / "ArtSource/Claude_PressShop_MaterialFlowPack_RuntimePrep_v002"
STATS = SOURCE_PREP / "runtime_prep_stats_v002.json"
TEXTURE_MANIFEST = SOURCE_ART / "texture_material_manifest.json"
SCRATCH = (
    "/Game/LineBoss/Factory/OneFactory/v001/Native/Press/_Scratch/"
    "MaterialFlowPack_v002_LegacyAbsolutePivotProbe_v001"
)
DEST = "/Game/LineBoss/Factory/OneFactory/v001/Native/Press/MaterialFlowPack_v002"
MESH_DEST = DEST + "/Meshes"
TEXTURE_DEST = DEST + "/Textures"
MATERIAL_DEST = DEST + "/Materials"
DEST_DISK = PROJECT / "Content" / Path(DEST.removeprefix("/Game/"))
SCRATCH_DISK = PROJECT / "Content" / Path(SCRATCH.removeprefix("/Game/"))
AUDIT = PROJECT / "Saved/Audits/OneFactory/Press/MaterialFlowPackRuntimePrep_v002"
SCRATCH_RECEIPT = AUDIT / "legacy_fbx_factory_absolute_pivot_probe_v001.json"
RECEIPT = AUDIT / "promotion_from_absolute_pivot_scratch_v001.json"
FAILURE = AUDIT / "promotion_from_absolute_pivot_scratch_v001_failure.json"
STAGE_RECEIPT = PROJECT / "Saved/Audits/OneFactory/Press/S03S06StagePackRuntimePrep_v001/import_receipt.json"

SHARED_DEST = "/Game/LineBoss/Factory/OneFactory/v001/Native/Press/SharedTrainModules_v003"
MASTER_PATH = (SHARED_DEST + "/Materials/M_CA_MW_PT_StagePack_PBR_Master_v001."
               "M_CA_MW_PT_StagePack_PBR_Master_v001")
CHANNELS = ("BC", "N", "ORM", "MASK")
SHARED_FAMILIES = (
    "CairnwellGreen", "FoundryCharcoal", "ServiceGrey", "SafetyYellow", "WorkedSteel",
    "InspectionGlass", "TrainAAccent", "StatusGreen", "StatusAmber",
)
NEW_FAMILIES = ("GalvanizedCoil", "DarkRubber", "TaskLightGlass", "StampedPanel")
ALL_FAMILIES = SHARED_FAMILIES + NEW_FAMILIES
TEXTURE_PARAMETERS = {
    "BaseColorMap": "BC", "NormalMap": "N", "ORMMap": "ORM", "WearMaskMap": "MASK",
}
SLOT_SUFFIX = re.compile(r"\.\d{3}$")
TOLERANCE_CM = 0.25

LIBRARY = unreal.EditorAssetLibrary
ASSET_TOOLS = unreal.AssetToolsHelpers.get_asset_tools()
MESH_EDITOR = unreal.get_editor_subsystem(unreal.StaticMeshEditorSubsystem)


def now() -> str:
    return datetime.now(timezone.utc).isoformat()


def fail(message: str) -> None:
    raise RuntimeError("MATERIAL_FLOW_V002_NATIVE_PROMOTION_FAIL: " + message)


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def read_json(path: Path) -> dict:
    if not path.is_file():
        fail("required JSON is missing: " + str(path))
    return json.loads(path.read_text(encoding="utf-8"))


def write_once(path: Path, payload: dict) -> None:
    if path.exists():
        fail("refusing to overwrite evidence: " + str(path))
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def object_path(folder: str, name: str) -> str:
    return "{}/{}.{}".format(folder, name, name)


def asset_path(asset) -> str:
    return str(asset.get_path_name()) if asset else "none"


def texture_name(family: str, channel: str) -> str:
    return "T_CA_MW_PT_{}_{}".format(family, channel)


def material_name(family: str) -> str:
    return "MI_CA_MW_PT_{}_v001".format(family)


def semantic_slot(family: str) -> str:
    return "CA_MW_{}".format(family)


def normalize_slot(name: str) -> str:
    return SLOT_SUFFIX.sub("", str(name))


def vector(value) -> list[float]:
    return [round(float(value.x), 5), round(float(value.y), 5), round(float(value.z), 5)]


def content_fingerprint(excluded_roots: tuple[Path, ...]) -> dict[str, tuple[int, int]]:
    result = {}
    content = PROJECT / "Content"
    resolved_exclusions = tuple(root.resolve() for root in excluded_roots)
    for path in content.rglob("*"):
        if not path.is_file():
            continue
        if any(_inside(path.resolve(), root) for root in resolved_exclusions):
            continue
        stat = path.stat()
        result[str(path.relative_to(content)).replace("\\", "/")] = (
            int(stat.st_size), int(stat.st_mtime_ns)
        )
    return result


def _inside(path: Path, root: Path) -> bool:
    try:
        path.relative_to(root)
        return True
    except ValueError:
        return False


def lod0_bounds(mesh) -> dict:
    dynamic_mesh = unreal.DynamicMesh()
    copy_options = unreal.GeometryScriptCopyMeshFromAssetOptions()
    requested_lod = unreal.GeometryScriptMeshReadLOD()
    requested_lod.set_editor_properties({
        "lod_type": unreal.GeometryScriptLODType.SOURCE_MODEL,
        "lod_index": 0,
    })
    dynamic_mesh, outcome = unreal.GeometryScript_AssetUtils.copy_mesh_from_static_mesh_v2(
        mesh, dynamic_mesh, copy_options, requested_lod, False
    )
    if outcome != unreal.GeometryScriptOutcomePins.SUCCESS:
        fail("GeometryScript source LOD read failed for {}: {}".format(mesh.get_name(), outcome))
    box = dynamic_mesh.get_mesh_bounding_box()
    minimum, maximum = vector(box.min), vector(box.max)
    return {
        "min": minimum,
        "max": maximum,
        "dimensions": [round(maximum[index] - minimum[index], 5) for index in range(3)],
    }


def close(actual, expected) -> bool:
    return len(actual) == len(expected) and all(
        abs(float(actual[index]) - float(expected[index])) <= TOLERANCE_CM
        for index in range(len(expected))
    )


def source_contract() -> dict:
    if PROJECT != EXPECTED_PROJECT:
        fail("wrong project: " + str(PROJECT))
    if str(unreal.SystemLibrary.get_game_name()) != "LineBossCarFactory":
        fail("wrong game name")
    stats = read_json(STATS)
    textures = read_json(TEXTURE_MANIFEST)
    if stats.get("asset_pack") != "CA_PressShop_MaterialFlowPack_RuntimePrep_v002":
        fail("RuntimePrep v002 identity drift")
    if stats.get("totals") != {"modules": 6, "meshes": 10, "payload_triangles": 3792}:
        fail("RuntimePrep v002 totals drift")
    source_blend = Path(str(stats.get("source", {}).get("blend", "")))
    source_blend_hash = str(stats.get("source", {}).get("sha256", "")).lower()
    if (not source_blend.is_file() or not re.fullmatch(r"[0-9a-f]{64}", source_blend_hash)
            or sha256(source_blend) != source_blend_hash):
        fail("source MaterialFlow blend provenance drift")
    if textures.get("asset_pack") != "CA_PressShop_MaterialFlowPack_v001":
        fail("texture manifest identity drift")
    expected_families = set(ALL_FAMILIES)
    if set(textures.get("families", {})) != expected_families:
        fail("texture-family inventory drift")
    modules = stats.get("modules", {})
    if len(modules) != 6:
        fail("module inventory drift")
    specs = {}
    fbx_hashes = {}
    for module_name, module in sorted(modules.items()):
        fbx = SOURCE_PREP / str(module.get("file", ""))
        if not fbx.is_file():
            fail("missing source FBX for " + module_name)
        actual_hash = sha256(fbx)
        if actual_hash != module.get("fbx_sha256"):
            fail("source FBX hash drift for " + module_name)
        fbx_hashes[module_name] = actual_hash
        for semantic_name, spec in module.get("meshes", {}).items():
            if semantic_name in specs:
                fail("duplicate semantic mesh " + semantic_name)
            if int(spec.get("triangles", -1)) <= 0:
                fail("invalid source triangles: " + semantic_name)
            expected = spec.get("expected_ue_aabb_cm", {})
            if len(expected.get("min", ())) != 3 or len(expected.get("max", ())) != 3:
                fail("missing native bounds: " + semantic_name)
            if list(spec.get("uv_layers", ())) != ["UVMap", "UV_Unique"]:
                fail("source UV contract drift: " + semantic_name)
            specs[semantic_name] = {"module": module_name, **spec}
    if len(specs) != 10 or sum(int(row["triangles"]) for row in specs.values()) != 3792:
        fail("semantic mesh/triangle inventory drift")
    for fbx, report in stats.get("raw_fbx_verification", {}).items():
        for node_name, node in report.get("nodes", {}).items():
            neutral = (
                all(abs(float(value)) <= 1e-6 for value in node.get("Lcl Translation", ())) and
                all(abs(float(value)) <= 1e-6 for value in node.get("Lcl Rotation", ())) and
                all(abs(float(value) - 1.0) <= 1e-6 for value in node.get("Lcl Scaling", ())) and
                all(abs(float(value)) <= 1e-6 for value in node.get("GeometricTranslation", ())) and
                all(abs(float(value) - 1.0) <= 1e-6 for value in node.get("GeometricScaling", ()))
            )
            if not neutral:
                fail("v002 node is not neutral: {}:{}".format(fbx, node_name))
    texture_specs = {}
    for family in ALL_FAMILIES:
        family_row = textures["families"][family]
        if family_row.get("material_slot") != semantic_slot(family):
            fail("texture material slot drift: " + family)
        maps = family_row.get("maps", {})
        if set(maps) != set(CHANNELS):
            fail("texture map set drift: " + family)
        texture_specs[family] = {}
        for channel in CHANNELS:
            map_row = maps[channel]
            expected_filename = "Textures/{}.png".format(texture_name(family, channel))
            if map_row.get("file") != expected_filename:
                fail("texture path drift: {}:{}".format(family, channel))
            path = SOURCE_ART / expected_filename
            expected_hash = str(map_row.get("sha256", "")).lower()
            if not path.is_file() or sha256(path) != expected_hash:
                fail("texture source hash drift: {}:{}".format(family, channel))
            texture_specs[family][channel] = {
                "path": path, "sha256": expected_hash, "name": texture_name(family, channel),
            }
    return {
        "stats": stats,
        "specs": specs,
        "texture_specs": texture_specs,
        "source_fbx_hashes": fbx_hashes,
        "source_blend": str(source_blend),
        "source_blend_sha256": source_blend_hash,
        "stats_sha256": sha256(STATS),
        "texture_manifest_sha256": sha256(TEXTURE_MANIFEST),
    }


def scratch_contract(specs: dict) -> dict[str, str]:
    receipt = read_json(SCRATCH_RECEIPT)
    if receipt.get("status") != "PASS__MATERIAL_FLOW_V002_NATIVE_LEGACY_FBX_FACTORY_SCRATCH":
        fail("absolute-pivot scratch did not pass")
    if receipt.get("destination_namespace") != SCRATCH:
        fail("absolute-pivot scratch namespace drift")
    policy = receipt.get("import_policy", {})
    expected_policy = {
        "combine_meshes": False,
        "convert_scene": True,
        "convert_scene_unit": True,
        "transform_vertex_to_absolute": True,
        "bake_pivot_in_vertex": False,
        "auto_generate_collision": False,
        "remove_degenerates": False,
        "nanite": False,
        "imported_materials": False,
        "imported_textures": False,
    }
    if {key: policy.get(key) for key in expected_policy} != expected_policy:
        fail("absolute-pivot scratch policy drift: " + repr(policy))
    if receipt.get("native_mesh_count") != 10 or receipt.get("native_payload_triangles") != 3792:
        fail("absolute-pivot scratch geometry totals drift")
    if receipt.get("source_unchanged") is not True or receipt.get("content_outside_scratch_unchanged") is not True:
        fail("absolute-pivot scratch preservation guards did not pass")
    paths = {}
    for module in receipt.get("modules", {}).values():
        for row in module:
            semantic = row.get("semantic_mesh")
            if semantic not in specs or semantic in paths:
                fail("absolute-pivot scratch semantic mapping drift")
            bounds = row.get("source_lod0_bounds_cm", {})
            expected = specs[semantic]["expected_ue_aabb_cm"]
            if (int(row.get("triangles", -1)) != int(specs[semantic]["triangles"])
                    or not close(bounds.get("min", ()), expected["min"])
                    or not close(bounds.get("max", ()), expected["max"])
                    or row.get("uv_channels") != 2
                    or row.get("simple_collision_count") != 0
                    or row.get("convex_collision_count") != 0
                    or row.get("nanite_enabled") is not False):
                fail("absolute-pivot scratch result drift: " + semantic)
            import_data = row.get("legacy_import_data", {})
            if (import_data.get("class") != "FbxStaticMeshImportData"
                    or import_data.get("transform_vertex_to_absolute") is not True
                    or import_data.get("bake_pivot_in_vertex") is not False):
                fail("absolute-pivot native import-data drift: " + semantic)
            paths[semantic] = row.get("object_path")
    if set(paths) != set(specs):
        fail("absolute-pivot scratch does not contain all ten semantic assets")
    if not LIBRARY.does_directory_exist(SCRATCH) or not SCRATCH_DISK.exists():
        fail("absolute-pivot scratch assets are absent")
    actual = set(str(path) for path in LIBRARY.list_assets(SCRATCH, recursive=True, include_folder=False))
    if actual != set(paths.values()):
        fail("absolute-pivot scratch registry inventory drift")
    return paths


def shared_materials() -> tuple[object, dict[str, object], dict]:
    receipt = read_json(STAGE_RECEIPT)
    if receipt.get("status") != "PASS__TEXTURED_STAGEPACK_V001_IMPORTED_AT_RECEIPTED_UNREAL_SCALE":
        fail("StagePack native material receipt is not approved")
    if receipt.get("destination") != SHARED_DEST or receipt.get("material_master") != MASTER_PATH:
        fail("StagePack native material root drift")
    master = unreal.load_asset(MASTER_PATH)
    if not isinstance(master, unreal.Material):
        fail("shared StagePack master is unavailable")
    source_paths = receipt.get("materials_by_semantic_slot", {})
    if set(source_paths) != {semantic_slot(family) for family in SHARED_FAMILIES}:
        fail("StagePack shared MI closure drift")
    materials = {}
    for slot, path in source_paths.items():
        material = unreal.load_asset(path)
        if not isinstance(material, unreal.MaterialInstanceConstant):
            fail("shared MI unavailable: " + slot)
        if asset_path(material.get_editor_property("parent")) != MASTER_PATH:
            fail("shared MI parent drift: " + slot)
        materials[slot] = material
    return master, materials, {
        "stage_receipt": str(STAGE_RECEIPT),
        "stage_receipt_sha256": sha256(STAGE_RECEIPT),
        "master": MASTER_PATH,
        "materials_by_semantic_slot": {slot: asset_path(material) for slot, material in materials.items()},
    }


def texture_settings(texture, channel: str) -> dict:
    if not isinstance(texture, unreal.Texture):
        fail("imported texture does not resolve")
    expected_srgb = channel == "BC"
    expected_compression = {
        "BC": unreal.TextureCompressionSettings.TC_DEFAULT,
        "N": unreal.TextureCompressionSettings.TC_NORMALMAP,
        "ORM": unreal.TextureCompressionSettings.TC_MASKS,
        "MASK": unreal.TextureCompressionSettings.TC_MASKS,
    }[channel]
    if (bool(texture.get_editor_property("srgb")) != expected_srgb
            or texture.get_editor_property("compression_settings") != expected_compression
            or bool(texture.get_editor_property("flip_green_channel")) != (channel == "N")):
        fail("native texture setting drift: {}:{}".format(texture.get_name(), channel))
    return {
        "path": asset_path(texture),
        "srgb": expected_srgb,
        "compression": str(expected_compression),
        "flip_green_channel": channel == "N",
    }


def import_new_texture(spec: dict, channel: str):
    task = unreal.AssetImportTask()
    task.set_editor_properties({
        "filename": str(spec["path"]),
        "destination_path": TEXTURE_DEST,
        "destination_name": spec["name"],
        "automated": True,
        "async_": False,
        "replace_existing": False,
        "replace_existing_settings": False,
        "save": True,
    })
    ASSET_TOOLS.import_asset_tasks([task])
    paths = [str(path) for path in (task.get_editor_property("imported_object_paths") or [])]
    expected = object_path(TEXTURE_DEST, spec["name"])
    if paths != [expected]:
        fail("texture import result drift for {}: {}".format(spec["name"], paths))
    texture = unreal.load_asset(expected)
    texture.set_editor_property("srgb", channel == "BC")
    texture.set_editor_property("compression_settings", {
        "BC": unreal.TextureCompressionSettings.TC_DEFAULT,
        "N": unreal.TextureCompressionSettings.TC_NORMALMAP,
        "ORM": unreal.TextureCompressionSettings.TC_MASKS,
        "MASK": unreal.TextureCompressionSettings.TC_MASKS,
    }[channel])
    texture.set_editor_property("flip_green_channel", channel == "N")
    if not LIBRARY.save_loaded_asset(texture, only_if_is_dirty=False):
        fail("could not save texture " + spec["name"])
    return texture


def create_material(family: str, master, textures: dict[str, object]):
    name = material_name(family)
    expected = object_path(MATERIAL_DEST, name)
    if LIBRARY.does_asset_exist(expected):
        fail("new MI unexpectedly exists: " + expected)
    material = ASSET_TOOLS.create_asset(
        name, MATERIAL_DEST, unreal.MaterialInstanceConstant,
        unreal.MaterialInstanceConstantFactoryNew(),
    )
    if not isinstance(material, unreal.MaterialInstanceConstant) or asset_path(material) != expected:
        fail("could not create MI " + family)
    material.set_editor_property("parent", master)
    for parameter, channel in TEXTURE_PARAMETERS.items():
        unreal.MaterialEditingLibrary.set_material_instance_texture_parameter_value(
            material, parameter, textures[channel])
    unreal.MaterialEditingLibrary.set_material_instance_scalar_parameter_value(
        material, "RawDustStrength", 0.0)
    if not LIBRARY.save_loaded_asset(material, only_if_is_dirty=False):
        fail("could not save MI " + family)
    if asset_path(material.get_editor_property("parent")) != MASTER_PATH:
        fail("MI parent did not persist: " + family)
    for parameter, channel in TEXTURE_PARAMETERS.items():
        actual = unreal.MaterialEditingLibrary.get_material_instance_texture_parameter_value(material, parameter)
        if asset_path(actual) != asset_path(textures[channel]):
            fail("MI texture did not persist: {}:{}".format(family, parameter))
    return material


def move_verified_geometry(scratch_paths: dict[str, str]) -> dict[str, object]:
    operations = []
    raw_assets = {}
    for semantic in sorted(scratch_paths):
        asset = unreal.load_asset(scratch_paths[semantic])
        if not isinstance(asset, unreal.StaticMesh):
            fail("scratch mesh unavailable: " + semantic)
        raw_assets[semantic] = asset
        operations.append(unreal.AssetRenameData(asset, MESH_DEST, semantic))
    if not ASSET_TOOLS.rename_assets(operations):
        fail("could not promote verified geometry to semantic production paths")
    unreal.AutomationUtilsBlueprintLibrary.finish_all_asset_compilation()
    result = {}
    for semantic, old_path in scratch_paths.items():
        expected = object_path(MESH_DEST, semantic)
        if LIBRARY.does_asset_exist(old_path):
            fail("scratch source package remains after semantic promotion: " + old_path)
        mesh = unreal.load_asset(expected)
        if not isinstance(mesh, unreal.StaticMesh) or asset_path(mesh) != expected:
            fail("semantic production mesh missing after promotion: " + semantic)
        result[semantic] = mesh
    return result


def validate_and_bind_mesh(mesh, semantic: str, spec: dict, materials: dict[str, object]) -> dict:
    if int(mesh.get_num_lods()) != 1 or int(mesh.get_num_triangles(0)) != int(spec["triangles"]):
        fail("native LOD/triangle contract drift: " + semantic)
    if int(MESH_EDITOR.get_num_uv_channels(mesh, 0)) != 2:
        fail("native UV-channel contract drift: " + semantic)
    bounds = lod0_bounds(mesh)
    expected = spec["expected_ue_aabb_cm"]
    if not close(bounds["min"], expected["min"]) or not close(bounds["max"], expected["max"]):
        fail("native bounds/pivot contract drift: {} {} vs {}".format(semantic, bounds, expected))
    if (int(MESH_EDITOR.get_simple_collision_count(mesh)) != 0
            or int(MESH_EDITOR.get_convex_collision_count(mesh)) != 0):
        fail("unexpected collision on " + semantic)
    if bool(MESH_EDITOR.get_nanite_settings(mesh).get_editor_property("enabled")):
        fail("unexpected Nanite enablement on " + semantic)
    data = mesh.get_editor_property("asset_import_data")
    try:
        import_data = {
            "class": str(data.get_class().get_name()),
            "import_uniform_scale": float(data.get_editor_property("import_uniform_scale")),
            "convert_scene": bool(data.get_editor_property("convert_scene")),
            "convert_scene_unit": bool(data.get_editor_property("convert_scene_unit")),
            "force_front_x_axis": bool(data.get_editor_property("force_front_x_axis")),
            "transform_vertex_to_absolute": bool(data.get_editor_property("transform_vertex_to_absolute")),
            "bake_pivot_in_vertex": bool(data.get_editor_property("bake_pivot_in_vertex")),
            "auto_generate_collision": bool(data.get_editor_property("auto_generate_collision")),
            "remove_degenerates": bool(data.get_editor_property("remove_degenerates")),
        }
    except Exception as error:
        fail("legacy native import data unavailable: {}: {}".format(semantic, error))
    expected_import = {
        "class": "FbxStaticMeshImportData", "import_uniform_scale": 1.0,
        "convert_scene": True, "convert_scene_unit": True, "force_front_x_axis": False,
        "transform_vertex_to_absolute": True, "bake_pivot_in_vertex": False,
        "auto_generate_collision": False, "remove_degenerates": False,
    }
    if import_data != expected_import:
        fail("native import policy drift for {}: {}".format(semantic, import_data))
    static_materials = list(mesh.get_editor_property("static_materials"))
    expected_slots = list(spec["material_slots"])
    raw_slots = [str(slot.get_editor_property("material_slot_name")) for slot in static_materials]
    normalized = [normalize_slot(slot) for slot in raw_slots]
    if normalized != expected_slots:
        fail("native slot order drift for {}: {} vs {}".format(semantic, normalized, expected_slots))
    for index, slot_name in enumerate(expected_slots):
        material = materials.get(slot_name)
        if material is None:
            fail("missing semantic native material " + slot_name)
        static_materials[index].set_editor_property("material_slot_name", slot_name)
        static_materials[index].set_editor_property("material_interface", material)
        mesh.set_material(index, material)
    mesh.set_editor_property("static_materials", static_materials)
    mesh.set_editor_property("light_map_coordinate_index", 1)
    mesh.set_editor_property("light_map_resolution", 128)
    if not LIBRARY.save_loaded_asset(mesh, only_if_is_dirty=False):
        fail("could not save bound native mesh " + semantic)
    bound_slots = [str(slot.get_editor_property("material_slot_name"))
                   for slot in mesh.get_editor_property("static_materials")]
    bound_materials = [asset_path(slot.get_editor_property("material_interface"))
                       for slot in mesh.get_editor_property("static_materials")]
    expected_materials = [asset_path(materials[slot]) for slot in expected_slots]
    if bound_slots != expected_slots or bound_materials != expected_materials:
        fail("native material binding did not persist for " + semantic)
    return {
        "object_path": asset_path(mesh),
        "triangles": int(mesh.get_num_triangles(0)),
        "lods": int(mesh.get_num_lods()),
        "uv_channels": int(MESH_EDITOR.get_num_uv_channels(mesh, 0)),
        "native_aabb_cm": bounds,
        "expected_ue_aabb_cm": expected,
        "raw_slot_names": raw_slots,
        "semantic_slots": bound_slots,
        "materials": bound_materials,
        "light_map_coordinate_index": int(mesh.get_editor_property("light_map_coordinate_index")),
        "light_map_resolution": int(mesh.get_editor_property("light_map_resolution")),
        "simple_collision_count": 0,
        "convex_collision_count": 0,
        "nanite_enabled": False,
        "legacy_import_data": import_data,
        "mover": spec.get("mover"),
    }


def exact_production_inventory() -> list[str]:
    expected = {
        *{object_path(MESH_DEST, name) for name in SOURCE_SPECS},
        *{object_path(TEXTURE_DEST, texture_name(family, channel))
          for family in NEW_FAMILIES for channel in CHANNELS},
        *{object_path(MATERIAL_DEST, material_name(family)) for family in NEW_FAMILIES},
    }
    actual = set(str(path) for path in LIBRARY.list_assets(DEST, recursive=True, include_folder=False))
    if actual != expected:
        fail("production native package closure drift: {} assets, expected {}".format(len(actual), len(expected)))
    return sorted(actual)


SOURCE_SPECS: dict[str, dict] = {}


def main() -> dict:
    global SOURCE_SPECS
    if DEST_DISK.exists() or LIBRARY.does_directory_exist(DEST):
        fail("production destination already exists: " + DEST)
    if RECEIPT.exists() or FAILURE.exists():
        fail("production evidence already exists; use a new revision")
    content_before = content_fingerprint((DEST_DISK, SCRATCH_DISK))
    source = source_contract()
    SOURCE_SPECS = source["specs"]
    scratch_paths = scratch_contract(SOURCE_SPECS)
    master, materials, shared_evidence = shared_materials()

    new_texture_receipt = {}
    new_textures = {family: {} for family in NEW_FAMILIES}
    for family in NEW_FAMILIES:
        for channel in CHANNELS:
            spec = source["texture_specs"][family][channel]
            texture = import_new_texture(spec, channel)
            new_textures[family][channel] = texture
            new_texture_receipt[spec["name"]] = {
                "source_path": str(spec["path"]), "source_sha256": spec["sha256"],
                **texture_settings(texture, channel),
            }
    new_mi_receipt = {}
    for family in NEW_FAMILIES:
        material = create_material(family, master, new_textures[family])
        materials[semantic_slot(family)] = material
        new_mi_receipt[semantic_slot(family)] = {
            "path": asset_path(material), "parent": MASTER_PATH,
            "textures": {parameter: asset_path(new_textures[family][channel])
                         for parameter, channel in TEXTURE_PARAMETERS.items()},
            "RawDustStrength": 0.0,
        }
    if set(materials) != {semantic_slot(family) for family in ALL_FAMILIES}:
        fail("semantic material closure is incomplete")

    meshes = move_verified_geometry(scratch_paths)
    mesh_results = {}
    for semantic, spec in sorted(SOURCE_SPECS.items()):
        mesh_results[semantic] = validate_and_bind_mesh(meshes[semantic], semantic, spec, materials)
    if sum(row["triangles"] for row in mesh_results.values()) != 3792:
        fail("production native payload triangle total drift")
    if not LIBRARY.save_directory(DEST, only_if_is_dirty=False, recursive=True):
        fail("could not save production native directory")
    assets = exact_production_inventory()
    source_after = source_contract()
    content_after = content_fingerprint((DEST_DISK, SCRATCH_DISK))
    if (source_after["stats_sha256"] != source["stats_sha256"]
            or source_after["source_fbx_hashes"] != source["source_fbx_hashes"]
            or source_after["source_blend_sha256"] != source["source_blend_sha256"]
            or source_after["texture_manifest_sha256"] != source["texture_manifest_sha256"]):
        fail("source RuntimePrep v002 changed during production promotion")
    if content_after != content_before:
        changed = sorted(set(content_before) ^ set(content_after))
        changed.extend(sorted(key for key in set(content_before) & set(content_after)
                              if content_before[key] != content_after[key]))
        fail("content outside isolated scratch/production namespaces changed: " + repr(changed[:20]))
    output = {
        "$schema": "lineboss/onefactory/press/material-flow-runtimeprep-v002/native-promotion/v1",
        "generated_utc": now(),
        "status": "PASS__MATERIAL_FLOW_V002_NATIVE_PROMOTED_FROM_VERIFIED_LEGACY_SCRATCH",
        "destination": DEST,
        "source_runtimeprep": str(SOURCE_PREP),
        "source_runtimeprep_stats_sha256": source["stats_sha256"],
        "source_texture_manifest": str(TEXTURE_MANIFEST),
        "source_texture_manifest_sha256": source["texture_manifest_sha256"],
        "source_fbx_sha256": source["source_fbx_hashes"],
        "source_blend": source["source_blend"],
        "source_blend_sha256": source["source_blend_sha256"],
        "source_declared_recipe": source["stats"].get("ue_native_import_contract"),
        "native_recipe_used": {
            "importer": "Unreal 5.8 native legacy FbxFactory",
            "combine_meshes": False, "convert_scene": True, "convert_scene_unit": True,
            "force_front_x_axis": False, "transform_vertex_to_absolute": True,
            "bake_pivot_in_vertex": False, "auto_generate_collision": False,
            "remove_degenerates": False, "nanite": False,
            "rationale": "v002 raw nodes are all neutral; native UE scratch measured this as the only pivot-safe axis-correct recipe",
        },
        "verified_scratch_receipt": str(SCRATCH_RECEIPT),
        "verified_scratch_receipt_sha256": sha256(SCRATCH_RECEIPT),
        "geometry_promotion": "native AssetTools semantic rename from verified scratch; no FBX re-export or re-import",
        "source_payload_triangles": 3792,
        "native_payload_triangles": sum(row["triangles"] for row in mesh_results.values()),
        "native_mesh_count": len(mesh_results),
        "native_package_count": len(assets),
        "native_assets": assets,
        "meshes": mesh_results,
        "shared_stagepack_material_reuse": shared_evidence,
        "new_textures": new_texture_receipt,
        "new_material_instances": new_mi_receipt,
        "mover_pivot_contract": {
            name: SOURCE_SPECS[name].get("mover")
            for name in sorted(SOURCE_SPECS) if SOURCE_SPECS[name].get("mover")
        },
        "source_unchanged": True,
        "content_outside_isolated_namespaces_unchanged": True,
        "map_opened_by_script": False,
        "map_saved_by_script": False,
        "collision": "none authored/imported",
        "lods": "LOD0 only",
        "promotion_authorized": False,
        "next_gate": "runtime actor integration and in-engine visual evidence",
    }
    write_once(RECEIPT, output)
    return output


try:
    main()
    unreal.log("MATERIAL_FLOW_V002_NATIVE_PROMOTION_PASS=" + str(RECEIPT))
except Exception as error:
    payload = {
        "$schema": "lineboss/onefactory/press/material-flow-runtimeprep-v002/native-promotion/v1",
        "generated_utc": now(),
        "status": "FAIL__MATERIAL_FLOW_V002_NATIVE_PROMOTION",
        "error": str(error),
        "traceback": traceback.format_exc(),
        "destination": DEST,
        "scratch": SCRATCH,
        "map_opened_by_script": False,
        "map_saved_by_script": False,
    }
    try:
        if not FAILURE.exists():
            write_once(FAILURE, payload)
    finally:
        unreal.log_error("MATERIAL_FLOW_V002_NATIVE_PROMOTION_FAIL=" + str(error))
    raise
finally:
    unreal.SystemLibrary.quit_editor()
