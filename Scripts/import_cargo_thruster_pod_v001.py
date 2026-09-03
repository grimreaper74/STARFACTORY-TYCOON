"""Import the CARGO'S THRUSTER POD (owner's own GPT reference image,
2026-09-03, generated to a real-world .blend through Meshy's
image-to-3D and exported at 180 cm on its longest axis) as a Nanite
static mesh, size verified here within 3%. Refuses to overwrite,
writes a receipt. Geometry only - materials are authored in Unreal.
"""
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path

import unreal

root = Path(unreal.Paths.project_dir())
source_dir = root / "SourceAssets/Candidate/Spacecraft/CargoParts_v004/export"
dest = "/Game/LineBoss/Candidates/Spacecraft/CargoParts_v001"
out = root / "Saved/Audits/Spacecraft/cargo_thruster_pod_import_v001.json"
if out.exists():
    raise RuntimeError("Refusing to rerun: receipt exists. Author v002.")
# name -> (defining axis, declared cm)
EXPECTED = {
    "SM_LB_SC_ThrusterPod_v001": ("longest", 180),
}
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
    asset_path = "%s/%s" % (dest, name)
    asset = library.load_asset(asset_path)
    if asset is None:
        failures.append("%s did not import" % name)
        continue
    nanite = None
    try:
        settings = unreal.MeshNaniteSettings()
        settings.set_editor_property("enabled", True)
        asset.set_editor_property("nanite_settings", settings)
        unreal.EditorAssetLibrary.save_loaded_asset(asset)
        nanite = bool(asset.get_editor_property(
            "nanite_settings").get_editor_property("enabled"))
    except Exception as exc:  # noqa: BLE001
        failures.append("%s could not take Nanite: %s" % (name, exc))
    if nanite is False:
        failures.append("%s did not take Nanite" % name)

    bounds = asset.get_bounding_box()
    extent = bounds.max - bounds.min
    measured = {"x": extent.x, "y": extent.y, "z": extent.z,
                "longest": max(extent.x, extent.y, extent.z)}[axis]
    if abs(measured - target_cm) > target_cm * 0.03:
        failures.append("%s measured %.1f cm on %s axis, declared %.1f" %
                         (name, measured, axis, target_cm))

    source = source_dir / ("%s.fbx" % name)
    sha256 = hashlib.sha256(source.read_bytes()).hexdigest()
    rows.append({
        "asset": asset_path,
        "source_sha256": sha256.upper(),
        "provenance": "GPT reference image, generated to a real-world "
            ".blend by the owner via Meshy's image-to-3D (Meshy_AI_Ion_"
            "Thruster_Core_0903092943_generate.blend), exported by "
            "Tools/export_meshy_blend_axis_v001.py",
        "defining_axis": axis,
        "declared_cm": target_cm,
        "measured_cm": round(measured, 1),
        "imported_extent_cm": [round(extent.x, 1), round(extent.y, 1),
                                round(extent.z, 1)],
        "nanite_enabled": nanite,
    })

out.parent.mkdir(parents=True, exist_ok=True)
receipt = {
    "$schema": "lineboss/audit/cargo-thruster-pod-import-v001/v1",
    "generated_utc": datetime.now(timezone.utc).isoformat(),
    "status": "PASS__CARGO_THRUSTER_POD_IMPORTED" if not failures
        else "FAIL_CLOSED__CARGO_THRUSTER_POD_IMPORT",
    "destination": dest,
    "assets": rows,
    "failures": failures,
    "not_proven": [
        "Import proves size and Nanite only. How it reads on the hull "
        "is judged on a rendered frame once wired into the presenter.",
    ],
}
out.write_text(json.dumps(receipt, indent=2), encoding="utf-8")
print(json.dumps(receipt, indent=2))
if failures:
    raise RuntimeError("Import failed closed: %s" % failures)
