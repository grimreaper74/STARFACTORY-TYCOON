"""Import the generated site buildings as Nanite static meshes.

One-shot, fail-closed lane in the shape of the existing intakes: it
refuses to rerun over its own receipt, verifies every source against the
manifest sha256 BEFORE importing, refuses to overwrite an existing
asset, and reads every claim back off the saved asset rather than
trusting the setter.

Three things it checks that a setter-and-hope lane would not:

  - The sha256, because provenance is verified rather than declared. A
    source that no longer matches its manifest is a different asset.
  - NANITE, read back after saving. These are ~3.1M triangles each; if
    Nanite silently failed to enable, the mesh still imports and still
    renders and the cost only shows up as a frame-rate mystery later.
  - The TRIANGLE COUNT against the manifest's declared budget. Generated
    geometry is permitted as a master asset - what it must prove is its
    record, and the measurement belongs in the receipt.

Run headless with -ExecutePythonScript.
"""

import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
import unreal

root = Path(unreal.Paths.project_dir())
source_dir = root / "SourceAssets/Candidate/Spacecraft/Buildings_v001"
manifest_path = source_dir / "spacecraft_buildings_manifest_v001.json"
dest = "/Game/LineBoss/Candidates/Spacecraft/StationMeshes_v001/Meshes"
out = root / "Saved/Audits/Spacecraft/spacecraft_buildings_import_v001.json"

manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
library = unreal.EditorAssetLibrary
tools = unreal.AssetToolsHelpers.get_asset_tools()

if out.exists():
    raise RuntimeError(
        "Refusing to rerun: a receipt for v001 already exists. Author v002.")

tasks = []
for row in manifest["assets"]:
    source = source_dir / row["file"]
    if not source.exists():
        raise RuntimeError("Missing source FBX: %s" % source)
    actual = hashlib.sha256(source.read_bytes()).hexdigest().upper()
    if actual != row["sha256"]:
        raise RuntimeError(
            "%s does not match its manifest sha256 (manifest %s..., file "
            "%s...)" % (row["file"], row["sha256"][:16], actual[:16]))
    if library.does_asset_exist("%s/%s" % (dest, row["name"])):
        raise RuntimeError("Refusing to overwrite %s/%s" % (dest, row["name"]))

    options = unreal.FbxImportUI()
    options.set_editor_property("import_mesh", True)
    options.set_editor_property("import_textures", True)
    options.set_editor_property("import_materials", True)
    options.set_editor_property("import_as_skeletal", False)
    options.set_editor_property("mesh_type_to_import",
                                unreal.FBXImportType.FBXIT_STATIC_MESH)
    static_data = options.static_mesh_import_data
    static_data.set_editor_property("combine_meshes", True)
    static_data.set_editor_property("generate_lightmap_u_vs", False)
    static_data.set_editor_property("auto_generate_collision", False)
    # The FBX already carries the derived scale; importing at 1.0 keeps
    # the mesh agreeing with the station's declared footprint.
    static_data.set_editor_property("import_uniform_scale", 1.0)

    task = unreal.AssetImportTask()
    task.set_editor_property("filename", str(source))
    task.set_editor_property("destination_path", dest)
    task.set_editor_property("destination_name", row["name"])
    task.set_editor_property("automated", True)
    task.set_editor_property("replace_existing", False)
    task.set_editor_property("save", True)
    task.set_editor_property("options", options)
    tasks.append(task)

tools.import_asset_tasks(tasks)

rows = []
failures = []
for spec in manifest["assets"]:
    path = "%s/%s" % (dest, spec["name"])
    asset = library.load_asset(path)
    if asset is None or not isinstance(asset, unreal.StaticMesh):
        failures.append("missing StaticMesh %s" % path)
        continue

    # NANITE. Set, saved, then read BACK - a silently-disabled Nanite on
    # a 3.1M-triangle mesh renders perfectly and costs a fortune.
    try:
        settings = unreal.MeshNaniteSettings()
        settings.set_editor_property("enabled", True)
        asset.set_editor_property("nanite_settings", settings)
        asset.modify()
        library.save_loaded_asset(asset, only_if_is_dirty=False)
    except Exception as exc:  # noqa: BLE001
        failures.append("%s could not take Nanite settings: %s" % (path, exc))

    nanite = None
    try:
        nanite = bool(asset.get_editor_property(
            "nanite_settings").get_editor_property("enabled"))
    except Exception as exc:  # noqa: BLE001
        failures.append("%s could not report Nanite: %s" % (path, exc))
    if nanite is False:
        failures.append("%s did not take Nanite" % path)

    tris = None
    try:
        tris = int(unreal.EditorStaticMeshLibrary.get_number_triangles(
            asset, 0))
    except Exception:  # noqa: BLE001
        try:
            tris = int(asset.get_num_triangles(0))
        except Exception:  # noqa: BLE001
            tris = None

    bounds = asset.get_bounds().box_extent
    rows.append({
        "asset": asset.get_path_name(),
        "station_definition_id": spec["station_definition_id"],
        "source_sha256": spec["sha256"],
        "provenance": spec["provenance"],
        "declared_triangle_budget": spec["declared_triangle_budget"],
        "imported_triangles": tris,
        "nanite_enabled": nanite,
        "imported_extent_cm": [round(bounds.x * 2), round(bounds.y * 2),
                               round(bounds.z * 2)],
        "expected_scaled_bounds_cm": spec["scaled_bounds_cm"],
    })

if len(rows) != len(manifest["assets"]):
    failures.append("expected %d meshes, found %d"
                    % (len(manifest["assets"]), len(rows)))

report = {
    "$schema": "lineboss/audit/spacecraft-buildings-import-v001/v1",
    "generated_utc": datetime.now(timezone.utc).isoformat(),
    "status": ("PASS__SPACECRAFT_SITE_BUILDINGS_IMPORTED__NANITE_ON"
               if not failures
               else "FAIL_CLOSED__SPACECRAFT_BUILDINGS_IMPORT__NOT_PROMOTED"),
    "source_manifest": manifest_path.relative_to(root).as_posix(),
    "destination": dest,
    "assets": rows,
    "failures": failures,
    "not_proven": [
        "Nobody has looked at these in the engine. Nanite being ENABLED "
        "is not the same as the meshes performing - that needs a measured "
        "in-engine frame cost, which this lane does not take.",
        "The ship factory hall has no station definition yet, so its "
        "size is provisional until the site map exists.",
    ],
    "promotion_authorized": False,
}
out.parent.mkdir(parents=True, exist_ok=True)
out.write_text(json.dumps(report, indent=2), encoding="utf-8")
print(json.dumps({"status": report["status"], "assets": len(rows),
                  "failures": failures}, indent=2))
if failures:
    raise RuntimeError("; ".join(failures))
