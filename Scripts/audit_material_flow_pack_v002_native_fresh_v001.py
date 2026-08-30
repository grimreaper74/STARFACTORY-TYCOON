"""Fresh-load, read-only native audit for the promoted MaterialFlow v002 package."""

from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path

import unreal


PROJECT = Path(unreal.Paths.project_dir()).resolve()
EXPECTED_PROJECT = Path(r"C:/Users/greg_/Projects/LineBossCarFactory_Unreal 5.8").resolve()
SOURCE = PROJECT / "ArtSource/Claude_PressShop_MaterialFlowPack_RuntimePrep_v002"
STATS = SOURCE / "runtime_prep_stats_v002.json"
DEST = "/Game/LineBoss/Factory/OneFactory/v001/Native/Press/MaterialFlowPack_v002"
MESH_DEST = DEST + "/Meshes"
TEXTURE_DEST = DEST + "/Textures"
MATERIAL_DEST = DEST + "/Materials"
AUDIT_DIR = PROJECT / "Saved/Audits/OneFactory/Press/MaterialFlowPackRuntimePrep_v002"
IMPORT_RECEIPT = AUDIT_DIR / "promotion_from_absolute_pivot_scratch_v001.json"
OUT = AUDIT_DIR / "fresh_native_audit_v001.json"
SHARED_RECEIPT = PROJECT / "Saved/Audits/OneFactory/Press/S03S06StagePackRuntimePrep_v001/import_receipt.json"
MASTER = ("/Game/LineBoss/Factory/OneFactory/v001/Native/Press/SharedTrainModules_v003/Materials/"
          "M_CA_MW_PT_StagePack_PBR_Master_v001.M_CA_MW_PT_StagePack_PBR_Master_v001")
NEW_FAMILIES = ("GalvanizedCoil", "DarkRubber", "TaskLightGlass", "StampedPanel")
CHANNELS = ("BC", "N", "ORM", "MASK")
PARAMETERS = {"BaseColorMap": "BC", "NormalMap": "N", "ORMMap": "ORM", "WearMaskMap": "MASK"}
TOL = 0.25

LIBRARY = unreal.EditorAssetLibrary
MESH_EDITOR = unreal.get_editor_subsystem(unreal.StaticMeshEditorSubsystem)


def fail(message):
    raise RuntimeError("MATERIAL_FLOW_V002_FRESH_NATIVE_AUDIT_FAIL: " + message)


def sha256(path):
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def obj(folder, name):
    return "{}/{}.{}".format(folder, name, name)


def texture_name(family, channel):
    return "T_CA_MW_PT_{}_{}".format(family, channel)


def material_name(family):
    return "MI_CA_MW_PT_{}_v001".format(family)


def slot(family):
    return "CA_MW_{}".format(family)


def vec(value):
    return [round(float(value.x), 5), round(float(value.y), 5), round(float(value.z), 5)]


def close(actual, expected):
    return len(actual) == len(expected) and all(abs(float(actual[i]) - float(expected[i])) <= TOL for i in range(3))


def bounds(mesh):
    dynamic_mesh = unreal.DynamicMesh()
    copy_options = unreal.GeometryScriptCopyMeshFromAssetOptions()
    lod = unreal.GeometryScriptMeshReadLOD()
    lod.set_editor_properties({"lod_type": unreal.GeometryScriptLODType.SOURCE_MODEL, "lod_index": 0})
    dynamic_mesh, outcome = unreal.GeometryScript_AssetUtils.copy_mesh_from_static_mesh_v2(
        mesh, dynamic_mesh, copy_options, lod, False)
    if outcome != unreal.GeometryScriptOutcomePins.SUCCESS:
        fail("GeometryScript could not read " + mesh.get_name())
    box = dynamic_mesh.get_mesh_bounding_box()
    return {"min": vec(box.min), "max": vec(box.max)}


def expected_specs(stats):
    specs = {}
    for module_name, module in stats["modules"].items():
        fbx = SOURCE / module["file"]
        if not fbx.is_file() or sha256(fbx) != module["fbx_sha256"]:
            fail("source FBX hash drift: " + module_name)
        for name, spec in module["meshes"].items():
            if name in specs:
                fail("duplicate source mesh " + name)
            specs[name] = {"module": module_name, **spec}
    if len(specs) != 10 or sum(int(item["triangles"]) for item in specs.values()) != 3792:
        fail("source v002 mesh/triangle inventory drift")
    return specs


def import_data(mesh):
    data = mesh.get_editor_property("asset_import_data")
    try:
        result = {
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
        fail("legacy FbxFactory import data is unavailable: {}".format(error))
    expected = {
        "class": "FbxStaticMeshImportData", "import_uniform_scale": 1.0,
        "convert_scene": True, "convert_scene_unit": True, "force_front_x_axis": False,
        "transform_vertex_to_absolute": True, "bake_pivot_in_vertex": False,
        "auto_generate_collision": False, "remove_degenerates": False,
    }
    if result != expected:
        fail("legacy FbxFactory policy drift: {}".format(result))
    return result


try:
    if PROJECT != EXPECTED_PROJECT or str(unreal.SystemLibrary.get_game_name()) != "LineBossCarFactory":
        fail("wrong project/game")
    if OUT.exists():
        fail("refusing to overwrite fresh audit")
    if not STATS.is_file() or not IMPORT_RECEIPT.is_file() or not SHARED_RECEIPT.is_file():
        fail("required source/import evidence missing")
    stats = json.loads(STATS.read_text(encoding="utf-8"))
    receipt = json.loads(IMPORT_RECEIPT.read_text(encoding="utf-8"))
    shared = json.loads(SHARED_RECEIPT.read_text(encoding="utf-8"))
    if stats.get("asset_pack") != "CA_PressShop_MaterialFlowPack_RuntimePrep_v002":
        fail("source identity drift")
    if receipt.get("status") != "PASS__MATERIAL_FLOW_V002_NATIVE_PROMOTED_FROM_VERIFIED_LEGACY_SCRATCH":
        fail("production receipt is not a pass")
    if receipt.get("destination") != DEST or receipt.get("native_mesh_count") != 10 or receipt.get("native_package_count") != 30:
        fail("production receipt closure drift")
    if receipt.get("native_recipe_used", {}).get("transform_vertex_to_absolute") is not True:
        fail("corrected native transform recipe not recorded")
    if shared.get("status") != "PASS__TEXTURED_STAGEPACK_V001_IMPORTED_AT_RECEIPTED_UNREAL_SCALE":
        fail("shared material receipt is not a pass")
    if shared.get("material_master") != MASTER:
        fail("shared material master drift")
    specs = expected_specs(stats)
    shared_materials = shared["materials_by_semantic_slot"]
    materials = dict(shared_materials)
    for family in NEW_FAMILIES:
        materials[slot(family)] = obj(MATERIAL_DEST, material_name(family))
    native_assets = set(str(path) for path in LIBRARY.list_assets(DEST, recursive=True, include_folder=False))
    expected_assets = {
        *{obj(MESH_DEST, name) for name in specs},
        *{obj(TEXTURE_DEST, texture_name(family, channel)) for family in NEW_FAMILIES for channel in CHANNELS},
        *{obj(MATERIAL_DEST, material_name(family)) for family in NEW_FAMILIES},
    }
    if native_assets != expected_assets:
        fail("exact 30-package native closure drift: got {}".format(len(native_assets)))
    master = unreal.load_asset(MASTER)
    if not isinstance(master, unreal.Material):
        fail("shared master does not resolve")
    texture_rows = {}
    material_rows = {}
    for family in NEW_FAMILIES:
        family_textures = {}
        for channel in CHANNELS:
            path = obj(TEXTURE_DEST, texture_name(family, channel))
            texture = unreal.load_asset(path)
            if not isinstance(texture, unreal.Texture):
                fail("new texture absent: " + path)
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
                fail("texture settings drift: " + path)
            family_textures[channel] = texture
            texture_rows[path] = {"srgb": expected_srgb, "flip_green_channel": channel == "N"}
        mi_path = obj(MATERIAL_DEST, material_name(family))
        material = unreal.load_asset(mi_path)
        if not isinstance(material, unreal.MaterialInstanceConstant):
            fail("new MI absent: " + mi_path)
        if str(material.get_editor_property("parent").get_path_name()) != MASTER:
            fail("new MI parent drift: " + family)
        for parameter, channel in PARAMETERS.items():
            actual = unreal.MaterialEditingLibrary.get_material_instance_texture_parameter_value(material, parameter)
            if str(actual.get_path_name()) != str(family_textures[channel].get_path_name()):
                fail("new MI texture parameter drift: {}:{}".format(family, parameter))
        material_rows[slot(family)] = mi_path
    mesh_rows = {}
    for name, spec in sorted(specs.items()):
        path = obj(MESH_DEST, name)
        mesh = unreal.load_asset(path)
        if not isinstance(mesh, unreal.StaticMesh):
            fail("mesh missing: " + name)
        actual_bounds = bounds(mesh)
        expected_bounds = spec["expected_ue_aabb_cm"]
        if (int(mesh.get_num_triangles(0)) != int(spec["triangles"])
                or int(mesh.get_num_lods()) != 1
                or int(MESH_EDITOR.get_num_uv_channels(mesh, 0)) != 2
                or not close(actual_bounds["min"], expected_bounds["min"])
                or not close(actual_bounds["max"], expected_bounds["max"])):
            fail("native geometry contract drift: " + name)
        if int(MESH_EDITOR.get_simple_collision_count(mesh)) or int(MESH_EDITOR.get_convex_collision_count(mesh)):
            fail("unexpected collision: " + name)
        if bool(MESH_EDITOR.get_nanite_settings(mesh).get_editor_property("enabled")):
            fail("unexpected Nanite: " + name)
        slots = [str(item.get_editor_property("material_slot_name")) for item in mesh.get_editor_property("static_materials")]
        if slots != list(spec["material_slots"]):
            fail("semantic slots drift: " + name)
        assigned = [str(item.get_editor_property("material_interface").get_path_name())
                    for item in mesh.get_editor_property("static_materials")]
        expected_assigned = [materials[item] for item in slots]
        if assigned != expected_assigned:
            fail("native material binding drift: " + name)
        if int(mesh.get_editor_property("light_map_coordinate_index")) != 1 or int(mesh.get_editor_property("light_map_resolution")) != 128:
            fail("lightmap policy drift: " + name)
        mesh_rows[name] = {
            "path": path, "triangles": int(mesh.get_num_triangles(0)), "bounds_cm": actual_bounds,
            "slots": slots, "materials": assigned, "legacy_import_data": import_data(mesh),
            "mover": spec.get("mover"),
        }
    if sum(row["triangles"] for row in mesh_rows.values()) != 3792:
        fail("native triangle total drift")
    payload = {
        "$schema": "lineboss/onefactory/press/material-flow-runtimeprep-v002/fresh-native-audit/v1",
        "generated_utc": datetime.now(timezone.utc).isoformat(),
        "status": "PASS__MATERIAL_FLOW_V002_FRESH_NATIVE_ASSET_AUDIT",
        "destination": DEST,
        "native_mesh_count": len(mesh_rows),
        "native_package_count": len(native_assets),
        "native_triangles": 3792,
        "native_recipe": receipt["native_recipe_used"],
        "source_stats_sha256": sha256(STATS),
        "production_receipt_sha256": sha256(IMPORT_RECEIPT),
        "shared_material_receipt_sha256": sha256(SHARED_RECEIPT),
        "meshes": mesh_rows,
        "new_textures": texture_rows,
        "new_materials": material_rows,
        "map_opened_by_script": False,
        "map_saved_by_script": False,
        "content_writes": [],
        "integration_authorized": False,
    }
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    unreal.log("MATERIAL_FLOW_V002_FRESH_NATIVE_AUDIT_PASS=" + str(OUT))
except Exception as error:
    unreal.log_error("MATERIAL_FLOW_V002_FRESH_NATIVE_AUDIT_FAIL=" + str(error))
    raise
finally:
    unreal.SystemLibrary.quit_editor()
