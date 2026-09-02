"""Import the STATION DRESS (look plan phases C and E) as Nanite static
meshes: the fitting station's tool tower, a wall storage rack, a ceiling
light bar and a low tool cabinet, generated 2026-09-02 through the Meshy
API by Scripts/submit_meshy_station_dress_v010.ps1 (owner, leaving for
work: "use meshy api if you need anything making that you cant do
yourself").

Same fail-closed shape as the line hardware intake: sha256 recorded for
every source, refuses to overwrite an existing asset, sets Nanite and
reads it BACK, and measures the imported bounds against what the export
declared - Meshy normalises everything to a ~2 m box, so size is imposed
at export (Tools/export_meshy_glb_v001.py) and must be verified here.

GEOMETRY ONLY: every mesh takes the project's graphite surface at
import; the presenter re-dresses per role (housing pale, cap amber).
"""
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path

import unreal

root = Path(unreal.Paths.project_dir())
source_dir = root / "SourceAssets/Candidate/Spacecraft/StationDress_v010/export"
dest = "/Game/LineBoss/Candidates/Spacecraft/StationDress_v001"
out = root / "Saved/Audits/Spacecraft/station_dress_import_v001.json"
if out.exists():
    raise RuntimeError("Refusing to rerun: receipt exists. Author v002.")

# name -> (defining axis, declared cm)
EXPECTED = {
    "SM_LB_ST_ToolTower_v001": ("z", 560),
    "SM_LB_ST_WallRack_v001": ("longest", 600),
    "SM_LB_ST_LightBar_v001": ("longest", 400),
    "SM_LB_ST_ToolCabinet_v001": ("z", 120),
}
PALETTE = "/Game/LineBoss/Materials/Surfaces/MI_LB_Surface_Graphite"

library = unreal.EditorAssetLibrary
tools = unreal.AssetToolsHelpers.get_asset_tools()
failures = []
rows = []
tasks = []
for name in sorted(EXPECTED):
    source = source_dir / ("%s.fbx" % name)
    if not source.exists():
        failures.append("missing source %s" % source)
        continue
    if library.does_asset_exist("%s/%s" % (dest, name)):
        failures.append("refusing to overwrite %s/%s" % (dest, name))
        continue
    options = unreal.FbxImportUI()
    options.set_editor_property("import_mesh", True)
    options.set_editor_property("import_textures", False)
    options.set_editor_property("import_materials", False)
    options.set_editor_property("import_as_skeletal", False)
    options.set_editor_property("mesh_type_to_import",
                                unreal.FBXImportType.FBXIT_STATIC_MESH)
    static_data = options.static_mesh_import_data
    static_data.set_editor_property("combine_meshes", True)
    static_data.set_editor_property("generate_lightmap_u_vs", False)
    static_data.set_editor_property("auto_generate_collision", False)
    static_data.set_editor_property("import_uniform_scale", 1.0)
    task = unreal.AssetImportTask()
    task.set_editor_property("filename", str(source))
    task.set_editor_property("destination_path", dest)
    task.set_editor_property("destination_name", name)
    task.set_editor_property("automated", True)
    task.set_editor_property("replace_existing", False)
    task.set_editor_property("save", True)
    task.set_editor_property("options", options)
    tasks.append(task)
if tasks:
    tools.import_asset_tasks(tasks)

for name, (axis, target_cm) in sorted(EXPECTED.items()):
    path = "%s/%s" % (dest, name)
    asset = library.load_asset(path)
    if asset is None or not isinstance(asset, unreal.StaticMesh):
        failures.append("missing StaticMesh %s" % path)
        continue
    try:
        settings = unreal.MeshNaniteSettings()
        settings.set_editor_property("enabled", True)
        asset.set_editor_property("nanite_settings", settings)
        asset.modify()
        library.save_loaded_asset(asset, only_if_is_dirty=False)
    except Exception as exc:  # noqa: BLE001
        failures.append("%s could not take Nanite: %s" % (name, exc))
    nanite = None
    try:
        nanite = bool(asset.get_editor_property(
            "nanite_settings").get_editor_property("enabled"))
    except Exception:  # noqa: BLE001
        pass
    if nanite is False:
        failures.append("%s did not take Nanite" % name)
    palette = library.load_asset(PALETTE)
    if palette is None:
        failures.append("palette material missing: %s" % PALETTE)
    else:
        for slot in range(len(asset.static_materials)):
            asset.set_material(slot, palette)
        library.save_loaded_asset(asset, only_if_is_dirty=False)
    extent = asset.get_bounds().box_extent
    dims = {"x": extent.x * 2, "y": extent.y * 2, "z": extent.z * 2}
    measured = max(dims.values()) if axis == "longest" else dims[axis]
    if abs(measured - target_cm) > target_cm * 0.03:
        failures.append("%s imported %.0f cm on %s, expected %d"
                        % (name, measured, axis, target_cm))
    source = source_dir / ("%s.fbx" % name)
    rows.append({
        "asset": path,
        "source_sha256": hashlib.sha256(
            source.read_bytes()).hexdigest().upper(),
        "provenance": "Meshy text-to-3D preview, generated 2026-09-02 "
                      "by Scripts/submit_meshy_station_dress_v010.ps1",
        "defining_axis": axis,
        "declared_cm": target_cm,
        "measured_cm": round(measured),
        "imported_extent_cm": [round(dims["x"]), round(dims["y"]),
                               round(dims["z"])],
        "nanite_enabled": nanite,
    })

report = {
    "$schema": "lineboss/audit/station-dress-import-v001/v1",
    "generated_utc": datetime.now(timezone.utc).isoformat(),
    "status": "PASS__STATION_DRESS_IMPORTED" if not failures
              else "FAIL_CLOSED__STATION_DRESS_IMPORT",
    "destination": dest,
    "assets": rows,
    "failures": failures,
    "not_proven": [
        "Import proves size and Nanite only. How each piece reads on the "
        "floor is judged on a rendered frame after the presenter dresses it.",
    ],
}
out.parent.mkdir(parents=True, exist_ok=True)
out.write_text(json.dumps(report, indent=2), encoding="utf-8")
unreal.log("STATION DRESS IMPORT %s: %d assets, %d failures"
           % (report["status"], len(rows), len(failures)))
for failure in failures:
    unreal.log_warning(failure)
