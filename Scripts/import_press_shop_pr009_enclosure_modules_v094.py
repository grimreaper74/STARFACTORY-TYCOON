"""Import the seven validated PR-009 enclosure groups without placing a map."""

import json
from datetime import datetime, timezone
from pathlib import Path

import unreal


ROOT = Path(unreal.Paths.project_dir())
SOURCE = ROOT / "SourceAssets/SharedSystems/AutomatedMachineEnclosure/Candidate_v002/ModularExports"
DEST = "/Game/LineBoss/Candidates/PressShop/PR009/v094/Enclosure"
OUT = ROOT / "Saved/Audits/PR009_InMap_v094/enclosure_import.json"
FILES = sorted(SOURCE.glob("*.fbx"))

if len(FILES) != 7:
    raise RuntimeError(f"Expected seven enclosure FBXs, found {len(FILES)}")

asset_tools = unreal.AssetToolsHelpers.get_asset_tools()
library = unreal.EditorAssetLibrary

tasks = []
for path in FILES:
    options = unreal.FbxImportUI()
    options.set_editor_property("import_mesh", True)
    options.set_editor_property("import_as_skeletal", False)
    options.set_editor_property("import_materials", False)
    options.set_editor_property("import_textures", False)
    options.set_editor_property("mesh_type_to_import", unreal.FBXImportType.FBXIT_STATIC_MESH)
    data = options.static_mesh_import_data
    data.set_editor_property("combine_meshes", True)
    data.set_editor_property("generate_lightmap_u_vs", True)
    data.set_editor_property("auto_generate_collision", False)
    data.set_editor_property("convert_scene", True)
    data.set_editor_property("convert_scene_unit", True)
    data.set_editor_property("import_uniform_scale", 1.0)

    task = unreal.AssetImportTask()
    task.set_editor_property("automated", True)
    task.set_editor_property("filename", str(path))
    task.set_editor_property("destination_path", DEST)
    task.set_editor_property("destination_name", path.stem)
    task.set_editor_property("replace_existing", True)
    task.set_editor_property("replace_existing_settings", True)
    task.set_editor_property("save", True)
    task.set_editor_property("options", options)
    tasks.append(task)

asset_tools.import_asset_tasks(tasks)

records = []
for task in tasks:
    expected = f"{DEST}/{Path(task.filename).stem}"
    if not library.does_asset_exist(expected):
        raise RuntimeError(f"Imported enclosure asset missing: {expected}; imported={list(task.imported_object_paths)}")
    mesh = library.load_asset(expected)
    if not isinstance(mesh, unreal.StaticMesh):
        raise RuntimeError(expected)
    bounds = mesh.get_bounds()
    slots = []
    for slot in mesh.get_editor_property("static_materials"):
        slots.append(str(slot.get_editor_property("imported_material_slot_name") or slot.get_editor_property("material_slot_name")))
    body = mesh.get_editor_property("body_setup")
    body.set_editor_property("collision_trace_flag", unreal.CollisionTraceFlag.CTF_USE_DEFAULT)
    body.set_editor_property("agg_geom", unreal.KAggregateGeom())
    body.modify()
    mesh.modify()
    library.save_loaded_asset(mesh, only_if_is_dirty=False)
    aggregate = body.get_editor_property("agg_geom")
    simple_count = sum(len(aggregate.get_editor_property(name)) for name in (
        "box_elems", "sphere_elems", "sphyl_elems", "convex_elems"))
    records.append({
        "asset": expected,
        "bounds_origin_cm": [bounds.origin.x, bounds.origin.y, bounds.origin.z],
        "bounds_extent_cm": [bounds.box_extent.x, bounds.box_extent.y, bounds.box_extent.z],
        "bounds_size_cm": [2*bounds.box_extent.x, 2*bounds.box_extent.y, 2*bounds.box_extent.z],
        "material_slots": slots,
        "lod0_vertices": mesh.get_num_vertices(0),
        "simple_collision_elements": simple_count,
        "collision_trace_flag": str(body.get_editor_property("collision_trace_flag")),
    })

OUT.parent.mkdir(parents=True, exist_ok=True)
OUT.write_text(json.dumps({
    "$schema": "cairnwell/audit/pr009-enclosure-modular-import-v094/v1",
    "generated_utc": datetime.now(timezone.utc).isoformat(),
    "status": "SEVEN_ENCLOSURE_MODULES_IMPORTED_FOR_BOUNDS_AND_SLOT_INSPECTION__NO_MAP_PLACEMENT__NOT_PROMOTED",
    "source": str(SOURCE),
    "destination": DEST,
    "asset_count": len(records),
    "assets": records,
    "map_placed": False,
    "collision_authored": False,
    "pr010_started": False,
    "robots_modified": False,
    "promotion_authorized": False,
}, indent=2), encoding="utf-8")
unreal.log(f"PR009_V094_ENCLOSURE_IMPORT_PASS output={OUT}")
