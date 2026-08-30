"""Guarded UE 5.8 native intake for the pivot-safe Press Shop hero-detail pack.

This creates a fresh, isolated native namespace only.  It preserves the source
FBXs byte-for-byte, does not open a map, and deliberately leaves partial output
in place if a source or native-contract gate fails so the failure is inspectable.
"""

from __future__ import annotations

import hashlib
import json
import traceback
from datetime import datetime, timezone
from pathlib import Path

import unreal


PROJECT = Path(unreal.Paths.project_dir()).resolve()
EXPECTED_PROJECT = Path(r"C:/Users/greg_/Projects/LineBossCarFactory_Unreal 5.8").resolve()
SOURCE = PROJECT / "ArtSource/Claude_PressShop_SteamHeroDetailPack_RuntimePrep_v002"
STATS = SOURCE / "runtime_prep_stats_v002.json"
TEXTURE_MANIFEST = (PROJECT / "ArtSource/Claude_PressShop_SteamHeroDetailPack_v001"
                    / "texture_statusred_manifest.json")
DEST = "/Game/LineBoss/Factory/OneFactory/v001/Native/Press/SteamHeroDetailPack_v003"
MESH_DEST = DEST + "/Meshes"
TEXTURE_DEST = DEST + "/Textures"
MATERIAL_DEST = DEST + "/Materials"
# The legacy FBX importer derives a package name from its source-file stem
# whenever a single FBX contains several meshes.  Import into this private
# staging folder first, validate its exact raw result, then let AssetTools do
# a semantic native rename into Meshes/.  That avoids accepting accidental
# filename prefixes as stable gameplay/content identifiers.
SCRATCH_MESH_DEST = DEST + "/_ImportScratch"
AUDIT_DIR = PROJECT / "Saved/Audits/OneFactory/Press/SteamHeroDetailPackNative_v003"
RECEIPT = AUDIT_DIR / "native_import_receipt_v003.json"
FAILURE = AUDIT_DIR / "native_import_failure_v003.json"
AXIS_PROBE = (PROJECT / "Saved/Audits/OneFactory/Press/"
              "SteamHeroDetailPackRuntimePrep_v002/axis_probe_v002.json")
SHARED_STAGE_RECEIPT = (PROJECT / "Saved/Audits/OneFactory/Press/"
                        "S03S06StagePackRuntimePrep_v001/import_receipt.json")
MASTER_PATH = ("/Game/LineBoss/Factory/OneFactory/v001/Native/Press/"
               "SharedTrainModules_v003/Materials/"
               "M_CA_MW_PT_StagePack_PBR_Master_v001."
               "M_CA_MW_PT_StagePack_PBR_Master_v001")
# These four semantics are intentionally owned by the already-receipted
# MaterialFlow native pack rather than SharedTrainModules.  Hero dressing
# reuses those exact Material Instances; it does not clone materials or maps.
MATERIALFLOW_MATERIAL_PATHS = {
    "CA_MW_DarkRubber": (
        "/Game/LineBoss/Factory/OneFactory/v001/Native/Press/"
        "MaterialFlowPack_v002/Materials/MI_CA_MW_PT_DarkRubber_v001."
        "MI_CA_MW_PT_DarkRubber_v001"),
    "CA_MW_GalvanizedCoil": (
        "/Game/LineBoss/Factory/OneFactory/v001/Native/Press/"
        "MaterialFlowPack_v002/Materials/MI_CA_MW_PT_GalvanizedCoil_v001."
        "MI_CA_MW_PT_GalvanizedCoil_v001"),
    "CA_MW_TaskLightGlass": (
        "/Game/LineBoss/Factory/OneFactory/v001/Native/Press/"
        "MaterialFlowPack_v002/Materials/MI_CA_MW_PT_TaskLightGlass_v001."
        "MI_CA_MW_PT_TaskLightGlass_v001"),
    "CA_MW_StampedPanel": (
        "/Game/LineBoss/Factory/OneFactory/v001/Native/Press/"
        "MaterialFlowPack_v002/Materials/MI_CA_MW_PT_StampedPanel_v001."
        "MI_CA_MW_PT_StampedPanel_v001"),
}
STATUS_RED = "CA_MW_StatusRed"
STATUS_RED_MATERIAL_NAME = "MI_CA_MW_PT_StatusRed_v001"
CHANNELS = ("BC", "N", "ORM", "MASK")
PARAMETERS = {
    "BaseColorMap": "BC",
    "NormalMap": "N",
    "ORMMap": "ORM",
    "WearMaskMap": "MASK",
}
TOLERANCE_CM = 0.5

LIBRARY = unreal.EditorAssetLibrary
ASSET_TOOLS = unreal.AssetToolsHelpers.get_asset_tools()
MESH_EDITOR = unreal.get_editor_subsystem(unreal.StaticMeshEditorSubsystem)


def fail(message):
    raise RuntimeError("STEAM_HERO_DETAIL_NATIVE_IMPORT_V003_FAIL: " + message)


def utc_now():
    return datetime.now(timezone.utc).isoformat()


def sha256(path):
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def object_path(folder, name):
    return "{0}/{1}.{1}".format(folder, name)


def vector_list(value):
    return [round(float(value.x), 5), round(float(value.y), 5), round(float(value.z), 5)]


def bounds_cm(mesh):
    dynamic_mesh = unreal.DynamicMesh()
    options = unreal.GeometryScriptCopyMeshFromAssetOptions()
    lod = unreal.GeometryScriptMeshReadLOD()
    lod.set_editor_properties({
        "lod_type": unreal.GeometryScriptLODType.SOURCE_MODEL,
        "lod_index": 0,
    })
    dynamic_mesh, outcome = unreal.GeometryScript_AssetUtils.copy_mesh_from_static_mesh_v2(
        mesh, dynamic_mesh, options, lod, False)
    if outcome != unreal.GeometryScriptOutcomePins.SUCCESS:
        fail("GeometryScript bounds read failed for " + mesh.get_name())
    box = dynamic_mesh.get_mesh_bounding_box()
    return {"min": vector_list(box.min), "max": vector_list(box.max)}


def dimensions(box):
    return [float(box["max"][index]) - float(box["min"][index])
            for index in range(3)]


def source_contract():
    if PROJECT != EXPECTED_PROJECT:
        fail("wrong project path")
    if str(unreal.SystemLibrary.get_game_name()) != "LineBossCarFactory":
        fail("wrong game")
    if (not STATS.is_file() or not TEXTURE_MANIFEST.is_file()
            or not SHARED_STAGE_RECEIPT.is_file() or not AXIS_PROBE.is_file()):
        fail("required source or shared material receipt is absent")
    stats = json.loads(STATS.read_text(encoding="utf-8"))
    status_red = json.loads(TEXTURE_MANIFEST.read_text(encoding="utf-8"))
    shared = json.loads(SHARED_STAGE_RECEIPT.read_text(encoding="utf-8"))
    axis_probe = json.loads(AXIS_PROBE.read_text(encoding="utf-8"))
    if stats.get("asset_pack") != "CA_PressShop_SteamHeroDetailPack_RuntimePrep_v002":
        fail("source asset identity drift")
    if stats.get("totals", {}).get("modules") != 7:
        fail("source module inventory drift")
    if (int(stats.get("totals", {}).get("base_topology_triangles", -1)) != 11116
            or int(stats.get("totals", {}).get("evaluated_export_triangles", -1)) != 12652):
        fail("source evaluated-payload accounting drift")
    if shared.get("status") != "PASS__TEXTURED_STAGEPACK_V001_IMPORTED_AT_RECEIPTED_UNREAL_SCALE":
        fail("shared material receipt is not an approved pass")
    if shared.get("material_master") != MASTER_PATH:
        fail("shared material master identity drift")
    die_cart_probe = axis_probe.get("variants", {}).get(
        "absolute_convert_scene", {}).get(
        "CA_PTA_Hero_ReusedKitProps_LOD0_SM_CA_MW_PT_DieCart_v002", {})
    if (axis_probe.get("status") != "PASS__DISPOSABLE_STEAMHERO_FBX_AXIS_PROBE"
            or die_cart_probe.get("bounds_cm") != {
                "min": [-225.0, -275.0, -64.0], "max": [225.0, 275.0, 31.0]}
            or die_cart_probe.get("legacy_import_data", {}).get(
                "transform_vertex_to_absolute") is not True):
        fail("native axis-probe prerequisite does not prove the chosen recipe")
    family = status_red.get("families", {}).get("StatusRed", {})
    if family.get("material_slot") != STATUS_RED or set(family.get("maps", {})) != set(CHANNELS):
        fail("StatusRed texture manifest inventory drift")

    specs = {}
    fbx_rows = {}
    for module_name, module in stats.get("modules", {}).items():
        fbx = SOURCE / module.get("file", "")
        expected_hash = module.get("fbx_sha256")
        if not fbx.is_file() or sha256(fbx) != expected_hash:
            fail("source FBX hash drift: " + module_name)
        fbx_rows[module_name] = {"path": str(fbx), "sha256": expected_hash}
        for mesh_name, mesh_spec in module.get("meshes", {}).items():
            if mesh_name in specs:
                fail("duplicate mesh name in source: " + mesh_name)
            if list(mesh_spec.get("uv_layers", [])) != ["UVMap", "UV_Unique"]:
                fail("source UV contract drift: " + mesh_name)
            specs[mesh_name] = {"module": module_name, **mesh_spec}
    if (len(specs) != 24
            or sum(int(spec["evaluated_export_triangles"]) for spec in specs.values()) != 12652):
        fail("source 24-mesh evaluated-payload inventory drift")

    textures = {}
    for channel, item in family["maps"].items():
        source = TEXTURE_MANIFEST.parent / item["file"]
        if not source.is_file() or sha256(source) != item["sha256"]:
            fail("StatusRed texture hash drift: " + channel)
        textures[channel] = {"source": source, "sha256": item["sha256"]}

    materials = dict(shared.get("materials_by_semantic_slot", {}))
    materials.update(MATERIALFLOW_MATERIAL_PATHS)
    required_shared = set()
    for spec in specs.values():
        required_shared.update(spec.get("material_slots", []))
    required_shared.discard(STATUS_RED)
    if set(materials) < required_shared:
        fail("shared semantic material mapping does not cover hero slots")
    for slot, path in materials.items():
        asset = unreal.load_asset(path)
        if asset is None or not isinstance(asset, unreal.MaterialInterface):
            fail("shared native material does not resolve: " + slot)
    master = unreal.load_asset(MASTER_PATH)
    if not isinstance(master, unreal.Material):
        fail("shared PBR master does not resolve")
    return stats, specs, textures, materials, fbx_rows, master


def mesh_task(source):
    task = unreal.AssetImportTask()
    task.set_editor_properties({
        "filename": str(source),
        "destination_path": SCRATCH_MESH_DEST,
        "automated": True,
        "async_": False,
        "replace_existing": False,
        "replace_existing_settings": False,
        "save": False,
    })
    options = unreal.FbxImportUI()
    options.set_editor_properties({
        "import_mesh": True,
        "import_as_skeletal": False,
        "import_materials": False,
        "import_textures": False,
        "import_animations": False,
        "automated_import_should_detect_type": False,
        "create_physics_asset": False,
        "mesh_type_to_import": unreal.FBXImportType.FBXIT_STATIC_MESH,
    })
    static = options.get_editor_property("static_mesh_import_data")
    static.set_editor_properties({
        "combine_meshes": False,
        "convert_scene": True,
        "convert_scene_unit": True,
        "force_front_x_axis": False,
        # The v002 node correction makes this pivot-safe.  A disposable UE
        # 5.8 probe measured absolute conversion as the one variant whose
        # vertices match the source's recorded expected_ue_aabb_cm; the
        # otherwise tempting relative variant swaps the Y/Z dimensions.
        "transform_vertex_to_absolute": True,
        "bake_pivot_in_vertex": False,
        "generate_lightmap_u_vs": False,
        "auto_generate_collision": False,
        "remove_degenerates": False,
        "import_uniform_scale": 1.0,
        "build_nanite": False,
    })
    factory = unreal.FbxFactory()
    factory.set_editor_property("asset_import_task", task)
    task.factory = factory
    task.options = options
    return task


def texture_task(channel, texture):
    name = "T_CA_MW_PT_StatusRed_" + channel
    task = unreal.AssetImportTask()
    task.set_editor_properties({
        "filename": str(texture["source"]),
        "destination_path": TEXTURE_DEST,
        "destination_name": name,
        "automated": True,
        "async_": False,
        "replace_existing": False,
        "replace_existing_settings": False,
        "save": False,
    })
    return task


def configure_textures(textures):
    tasks = [(channel, texture_task(channel, spec))
             for channel, spec in sorted(textures.items())]
    ASSET_TOOLS.import_asset_tasks([task for _, task in tasks])
    unreal.AutomationUtilsBlueprintLibrary.finish_all_asset_compilation()
    output = {}
    for channel, task in tasks:
        name = "T_CA_MW_PT_StatusRed_" + channel
        expected = object_path(TEXTURE_DEST, name)
        imported = [str(value) for value in task.get_editor_property("imported_object_paths")]
        if imported != [expected]:
            fail("native texture import identity drift: {0}: {1}".format(channel, imported))
        texture = unreal.load_asset(expected)
        if not isinstance(texture, unreal.Texture2D):
            fail("native texture does not resolve as Texture2D: " + channel)
        texture.set_editor_properties({
            "srgb": channel == "BC",
            "compression_settings": {
                "BC": unreal.TextureCompressionSettings.TC_DEFAULT,
                "N": unreal.TextureCompressionSettings.TC_NORMALMAP,
                "ORM": unreal.TextureCompressionSettings.TC_MASKS,
                "MASK": unreal.TextureCompressionSettings.TC_MASKS,
            }[channel],
            "flip_green_channel": channel == "N",
            "never_stream": False,
        })
        if not LIBRARY.save_loaded_asset(texture, only_if_is_dirty=False):
            fail("native texture save failed: " + channel)
        output[channel] = texture
    return output


def load_and_configure_textures():
    """Resume a failed isolated import without re-importing source PNGs."""
    output = {}
    for channel in CHANNELS:
        name = "T_CA_MW_PT_StatusRed_" + channel
        path = object_path(TEXTURE_DEST, name)
        texture = unreal.load_asset(path)
        if not isinstance(texture, unreal.Texture2D):
            fail("recovery texture does not resolve as Texture2D: " + channel)
        texture.set_editor_properties({
            "srgb": channel == "BC",
            "compression_settings": {
                "BC": unreal.TextureCompressionSettings.TC_DEFAULT,
                "N": unreal.TextureCompressionSettings.TC_NORMALMAP,
                "ORM": unreal.TextureCompressionSettings.TC_MASKS,
                "MASK": unreal.TextureCompressionSettings.TC_MASKS,
            }[channel],
            "flip_green_channel": channel == "N",
            "never_stream": False,
        })
        if not LIBRARY.save_loaded_asset(texture, only_if_is_dirty=False):
            fail("recovery texture save failed: " + channel)
        output[channel] = texture
    return output


def create_status_red_material(master, textures):
    path = object_path(MATERIAL_DEST, STATUS_RED_MATERIAL_NAME)
    material = (unreal.load_asset(path) if LIBRARY.does_asset_exist(path)
                else ASSET_TOOLS.create_asset(
                    STATUS_RED_MATERIAL_NAME, MATERIAL_DEST,
                    unreal.MaterialInstanceConstant,
                    unreal.MaterialInstanceConstantFactoryNew()))
    if not isinstance(material, unreal.MaterialInstanceConstant) or material.get_path_name() != path:
        fail("StatusRed material creation identity drift")
    material.set_editor_property("parent", master)
    for parameter, channel in PARAMETERS.items():
        # UE's Python binding is a void Blueprint utility function; it
        # returns None both on success and failure.  Bind first, then prove
        # the resulting parameter value rather than treating None as false.
        unreal.MaterialEditingLibrary.set_material_instance_texture_parameter_value(
            material, parameter, textures[channel])
        actual = unreal.MaterialEditingLibrary.get_material_instance_texture_parameter_value(
            material, parameter)
        if actual is None or actual.get_path_name() != textures[channel].get_path_name():
            fail("StatusRed parameter bind verification failed: " + parameter)
    if not LIBRARY.save_loaded_asset(material, only_if_is_dirty=False):
        fail("StatusRed material save failed")
    return material


def import_meshes(fbx_rows, specs):
    tasks = [(name, mesh_task(Path(row["path"]))) for name, row in sorted(fbx_rows.items())]
    ASSET_TOOLS.import_asset_tasks([task for _, task in tasks])
    unreal.AutomationUtilsBlueprintLibrary.finish_all_asset_compilation()
    raw_paths_by_name = {}
    for module_name, task in tasks:
        source_stem = Path(fbx_rows[module_name]["path"]).stem
        expected = {
            object_path(SCRATCH_MESH_DEST, source_stem + "_" + mesh_name)
            for mesh_name, spec in specs.items() if spec["module"] == module_name
        }
        paths = {str(value) for value in task.get_editor_property("imported_object_paths")}
        if paths != expected:
            fail("native mesh raw-import identity drift: {}: {}".format(
                module_name, sorted(paths)))
        for mesh_name, spec in specs.items():
            if spec["module"] == module_name:
                raw_paths_by_name[mesh_name] = object_path(
                    SCRATCH_MESH_DEST, source_stem + "_" + mesh_name)
    if set(raw_paths_by_name) != set(specs):
        fail("native mesh raw-import closure drift")
    raw_meshes = {}
    for mesh_name, raw_path in raw_paths_by_name.items():
        mesh = unreal.load_asset(raw_path)
        if not isinstance(mesh, unreal.StaticMesh):
            fail("native mesh raw-import did not resolve: " + mesh_name)
        raw_meshes[mesh_name] = mesh

    renames = [unreal.AssetRenameData(raw_meshes[mesh_name], MESH_DEST, mesh_name)
               for mesh_name in sorted(raw_meshes)]
    if not ASSET_TOOLS.rename_assets(renames):
        fail("native semantic mesh rename failed")
    unreal.AutomationUtilsBlueprintLibrary.finish_all_asset_compilation()
    scratch_leftovers = list(LIBRARY.list_assets(
        SCRATCH_MESH_DEST, recursive=True, include_folder=False))
    if scratch_leftovers:
        fail("native mesh scratch packages remain after semantic rename")
    result = {name: unreal.load_asset(object_path(MESH_DEST, name)) for name in specs}
    if not all(isinstance(mesh, unreal.StaticMesh) for mesh in result.values()):
        fail("native semantic mesh package resolution drift")
    return result


def configure_and_verify_meshes(meshes, specs, materials):
    expected_material_paths = dict(materials)
    result = {}
    for name, spec in sorted(specs.items()):
        mesh = meshes.get(name)
        if not isinstance(mesh, unreal.StaticMesh):
            fail("native mesh does not resolve: " + name)
        if mesh.get_path_name() != object_path(MESH_DEST, name):
            fail("native mesh path drift: " + name)
        if (int(mesh.get_num_lods()) != 1
                or int(mesh.get_num_triangles(0)) != int(spec["evaluated_export_triangles"])):
            fail("native payload triangle/LOD drift: " + name)
        if int(MESH_EDITOR.get_num_uv_channels(mesh, 0)) != 2:
            fail("native UV-channel drift: " + name)
        if int(MESH_EDITOR.get_simple_collision_count(mesh)) or int(MESH_EDITOR.get_convex_collision_count(mesh)):
            fail("native collision unexpectedly exists: " + name)
        if bool(MESH_EDITOR.get_nanite_settings(mesh).get_editor_property("enabled")):
            fail("native Nanite unexpectedly enabled: " + name)
        actual = bounds_cm(mesh)
        expected = spec["expected_ue_aabb_cm"]
        actual_dimensions = dimensions(actual)
        expected_dimensions = dimensions(expected)
        if any(abs(actual_dimensions[index] - expected_dimensions[index]) > TOLERANCE_CM
               for index in range(3)):
            fail("native scale/axis dimensions drift: {0}: {1} vs {2}".format(
                name, actual_dimensions, expected_dimensions))
        slots = list(mesh.get_editor_property("static_materials"))
        slot_names = [str(slot.get_editor_property("material_slot_name")) for slot in slots]
        if slot_names != list(spec["material_slots"]):
            fail("native semantic material slot drift: " + name)
        for index, slot_name in enumerate(slot_names):
            target_path = expected_material_paths.get(slot_name)
            if target_path is None:
                fail("no native material target for slot {} on {}".format(slot_name, name))
            target = unreal.load_asset(target_path)
            if not isinstance(target, unreal.MaterialInterface):
                fail("native material target does not resolve: {}".format(slot_name))
            mesh.set_material(index, target)
        mesh.set_editor_properties({
            "light_map_coordinate_index": 1,
            "light_map_resolution": 128,
        })
        if not LIBRARY.save_loaded_asset(mesh, only_if_is_dirty=False):
            fail("native mesh save failed: " + name)
        import_data = mesh.get_editor_property("asset_import_data")
        policy = {
            "import_uniform_scale": float(import_data.get_editor_property("import_uniform_scale")),
            "convert_scene": bool(import_data.get_editor_property("convert_scene")),
            "convert_scene_unit": bool(import_data.get_editor_property("convert_scene_unit")),
            "force_front_x_axis": bool(import_data.get_editor_property("force_front_x_axis")),
            "transform_vertex_to_absolute": bool(import_data.get_editor_property("transform_vertex_to_absolute")),
            "bake_pivot_in_vertex": bool(import_data.get_editor_property("bake_pivot_in_vertex")),
            "auto_generate_collision": bool(import_data.get_editor_property("auto_generate_collision")),
            "remove_degenerates": bool(import_data.get_editor_property("remove_degenerates")),
        }
        expected_policy = {
            "import_uniform_scale": 1.0, "convert_scene": True, "convert_scene_unit": True,
            "force_front_x_axis": False, "transform_vertex_to_absolute": True,
            "bake_pivot_in_vertex": False, "auto_generate_collision": False,
            "remove_degenerates": False,
        }
        if policy != expected_policy:
            fail("native legacy FBX import policy drift: " + name)
        assigned = []
        for index in range(len(slots)):
            value = mesh.get_material(index)
            if value is None:
                fail("native material assignment missing: " + name)
            assigned.append(value.get_path_name())
        expected_assigned = [expected_material_paths[slot] for slot in slot_names]
        if assigned != expected_assigned:
            fail("native material assignment drift: " + name)
        result[name] = {
            "path": mesh.get_path_name(),
            "module": spec["module"],
            "triangles": int(mesh.get_num_triangles(0)),
            "bounds_cm": actual,
            "expected_dimensions_cm": expected_dimensions,
            "material_slots": slot_names,
            "materials": assigned,
            "uv_channels": int(MESH_EDITOR.get_num_uv_channels(mesh, 0)),
            "legacy_import_data": policy,
        }
    return result


def main():
    evidence = {
        "$schema": "lineboss/onefactory/press/steam-hero-detail-runtimeprep-v002/native-import-v003/v1",
        "generated_utc": utc_now(),
        "destination": DEST,
        "map_opened_by_script": False,
        "map_saved_by_script": False,
        "source_assets_mutated": False,
        "content_writes": [DEST],
        "no_geometry_reexport": True,
    }
    try:
        stats, specs, texture_specs, shared_materials, fbx_rows, master = source_contract()
        evidence.update({
            "source_stats_sha256": sha256(STATS),
            "statusred_manifest_sha256": sha256(TEXTURE_MANIFEST),
            "shared_stage_receipt_sha256": sha256(SHARED_STAGE_RECEIPT),
            "native_axis_probe_sha256": sha256(AXIS_PROBE),
            "source_fbx": fbx_rows,
        })
        if RECEIPT.exists():
            fail("prior successful receipt exists; refusing overwrite")
        expected_mesh_paths = {object_path(MESH_DEST, name) for name in specs}
        existing_mesh_paths = {
            path for path in expected_mesh_paths if LIBRARY.does_asset_exist(path)
        }
        existing_texture_paths = {
            object_path(TEXTURE_DEST, "T_CA_MW_PT_StatusRed_" + channel)
            for channel in CHANNELS
            if LIBRARY.does_asset_exist(object_path(
                TEXTURE_DEST, "T_CA_MW_PT_StatusRed_" + channel))
        }
        if existing_mesh_paths:
            # A previous fail-closed run may have completed a native semantic
            # rename and texture intake before encountering a later material
            # gate.  Resume only if the isolated namespace is complete enough
            # to prove it is exactly that known state; never blend two partial
            # or arbitrary imports together.
            if (existing_mesh_paths != expected_mesh_paths
                    or len(existing_texture_paths) != len(CHANNELS)
                    or LIBRARY.does_directory_exist(SCRATCH_MESH_DEST)):
                fail("isolated recovery namespace is incomplete or ambiguous")
            meshes = {name: unreal.load_asset(object_path(MESH_DEST, name))
                      for name in specs}
            textures = load_and_configure_textures()
            evidence["recovered_from_fail_closed_native_intake"] = True
        else:
            if LIBRARY.does_directory_exist(DEST) or existing_texture_paths:
                fail("fresh destination namespace already exists")
            meshes = import_meshes(fbx_rows, specs)
            textures = configure_textures(texture_specs)
            evidence["recovered_from_fail_closed_native_intake"] = False
        status_red = create_status_red_material(master, textures)
        all_materials = dict(shared_materials)
        all_materials[STATUS_RED] = status_red.get_path_name()
        mesh_rows = configure_and_verify_meshes(meshes, specs, all_materials)
        unreal.AutomationUtilsBlueprintLibrary.finish_all_asset_compilation()
        registry = set(str(item) for item in LIBRARY.list_assets(
            DEST, recursive=True, include_folder=False))
        expected_registry = {
            *{object_path(MESH_DEST, name) for name in specs},
            *{object_path(TEXTURE_DEST, "T_CA_MW_PT_StatusRed_" + channel)
              for channel in CHANNELS},
            object_path(MATERIAL_DEST, STATUS_RED_MATERIAL_NAME),
        }
        if registry != expected_registry:
            fail("native package closure drift: {} vs {}".format(len(registry), len(expected_registry)))
        if sum(row["triangles"] for row in mesh_rows.values()) != 12652:
            fail("native evaluated payload total drift")
        evidence.update({
            "status": "PASS__STEAM_HERO_DETAIL_V002_NATIVE_IMPORT_V003",
            "native_mesh_count": len(mesh_rows),
            "native_payload_triangles": 12652,
            "native_package_count": len(registry),
            "native_recipe": {
                "importer": "Unreal 5.8 legacy FbxFactory",
                "combine_meshes": False,
                "convert_scene": True,
                "convert_scene_unit": True,
                "transform_vertex_to_absolute": True,
                "import_uniform_scale": 1.0,
                "generate_lightmap_uvs": False,
                "light_map_coordinate_index": 1,
                "light_map_resolution": 128,
                "collision": "none authored/imported",
                "nanite": False,
            },
            "statusred_native_material": status_red.get_path_name(),
            "meshes": mesh_rows,
            "native_assets": sorted(registry),
            "integration_authorized": False,
        })
        AUDIT_DIR.mkdir(parents=True, exist_ok=True)
        RECEIPT.write_text(json.dumps(evidence, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        unreal.log("STEAM_HERO_DETAIL_NATIVE_IMPORT_V003_PASS=" + str(RECEIPT))
    except Exception as error:
        AUDIT_DIR.mkdir(parents=True, exist_ok=True)
        failure = {
            **evidence,
            "status": "FAIL_CLOSED__STEAM_HERO_DETAIL_V003_NATIVE_IMPORT",
            "error": str(error),
            "traceback": traceback.format_exc(),
            "partial_native_assets_preserved": list(LIBRARY.list_assets(
                DEST, recursive=True, include_folder=False)) if LIBRARY.does_directory_exist(DEST) else [],
        }
        FAILURE.write_text(json.dumps(failure, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        unreal.log_error("STEAM_HERO_DETAIL_NATIVE_IMPORT_V003_FAIL=" + str(error))
        raise
    finally:
        unreal.SystemLibrary.quit_editor()


if __name__ == "__main__":
    main()
