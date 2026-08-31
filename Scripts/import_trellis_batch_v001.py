"""Import the staged TRELLIS batch (2026-08-31) as verified StaticMeshes.

Runs INSIDE the editor (-ExecutePythonScript). Follows the proven FBX
lane (import_ground_drones_v001.py): FbxImportUI with combine_meshes,
no auto collision, no lightmap UVs, Nanite enabled and READ BACK, the
defining axis measured against the declared size at 3% tolerance, and
a fail-closed audit receipt under Saved/Audits/Spacecraft/.

Scale is already BAKED into the staged FBX by
Tools/trellis_prepare_import_v001.py - nothing here rescales.
"""
import json
import os
import unreal

RECEIPT_NAME = "trellis_batch_import_v001.json"
DEST_ROOT = "/Game/Spacecraft/Props"

# name -> (defining axis, declared cm). Must match the Blender prep run.
BATCH = {
    "line_station_v001": ("z", 800.0),
    "kit_dolly_v001": ("longest", 200.0),
    "gantry_crane_v001": ("longest", 1200.0),
    "lifter_drone_v001": ("longest", 200.0),
    "cargo_drone_v001": ("longest", 400.0),
    "scout_option3_hull_v001": ("longest", 1200.0),
}


def main():
    project = unreal.SystemLibrary.get_project_directory()
    stage = os.path.join(project, "Saved", "TrellisImportStage_v001")
    audit_dir = os.path.join(project, "Saved", "Audits", "Spacecraft")
    os.makedirs(audit_dir, exist_ok=True)
    receipt_path = os.path.join(audit_dir, RECEIPT_NAME)
    if os.path.exists(receipt_path):
        unreal.log_error(
            "RECEIPT EXISTS: %s - this lane refuses to rerun. Author "
            "v002 instead." % receipt_path)
        return

    results = []
    failures = 0
    for name, (axis, declared_cm) in BATCH.items():
        entry = {"asset": name, "definingAxis": axis,
                 "declaredCm": declared_cm}
        fbx = os.path.join(stage, name, "%s.fbx" % name)
        if not os.path.isfile(fbx):
            entry["status"] = "FAIL_CLOSED__FBX_MISSING"
            failures += 1
            results.append(entry)
            continue

        ui = unreal.FbxImportUI()
        ui.import_mesh = True
        ui.import_as_skeletal = False
        ui.import_animations = False
        ui.import_materials = True
        ui.import_textures = True
        ui.static_mesh_import_data.set_editor_property(
            "combine_meshes", True)
        ui.static_mesh_import_data.set_editor_property(
            "auto_generate_collision", False)
        ui.static_mesh_import_data.set_editor_property(
            "generate_lightmap_u_vs", False)
        ui.static_mesh_import_data.set_editor_property(
            "import_uniform_scale", 1.0)

        task = unreal.AssetImportTask()
        task.filename = fbx
        task.destination_path = "%s/%s" % (DEST_ROOT, name)
        task.automated = True
        task.replace_existing = True
        task.save = True
        task.options = ui
        unreal.AssetToolsHelpers.get_asset_tools().import_asset_tasks(
            [task])

        mesh = None
        for path in list(task.imported_object_paths or []):
            loaded = unreal.load_asset(path)
            if isinstance(loaded, unreal.StaticMesh):
                mesh = loaded
                entry["assetPath"] = path
                break
        if mesh is None:
            entry["status"] = "FAIL_CLOSED__NO_STATICMESH"
            failures += 1
            results.append(entry)
            continue

        # Nanite ON, then read back rather than trusted.
        nanite = mesh.get_editor_property("nanite_settings")
        if not nanite.enabled:
            nanite.enabled = True
            mesh.set_editor_property("nanite_settings", nanite)
        entry["naniteEnabled"] = bool(
            mesh.get_editor_property("nanite_settings").enabled)

        extent = mesh.get_bounds().box_extent
        size = {"x": extent.x * 2.0, "y": extent.y * 2.0,
                "z": extent.z * 2.0}
        entry["boundsCm"] = size
        measured = size[axis] if axis in size else max(size.values())
        entry["measuredCm"] = measured
        deviation = abs(measured - declared_cm) / declared_cm
        entry["deviationPct"] = round(deviation * 100.0, 2)
        if deviation <= 0.03:
            entry["status"] = "PASS__IMPORT_VERIFIED"
        else:
            entry["status"] = "FAIL_CLOSED__SIZE_MISMATCH"
            failures += 1

        unreal.EditorAssetLibrary.save_loaded_asset(mesh)
        results.append(entry)
        unreal.log("TRELLIS IMPORT %s: %s (%.0f cm on %s)" % (
            name, entry["status"], measured, axis))

    receipt = {
        "$schema": "lineboss/audit/trellis-batch-import/v1",
        "status": ("PASS__ALL_VERIFIED" if failures == 0
                   else "FAIL_CLOSED__%d_OF_%d" % (failures, len(BATCH))),
        "destinationRoot": DEST_ROOT,
        "assets": results,
    }
    with open(receipt_path, "w", encoding="utf-8") as handle:
        json.dump(receipt, handle, indent=2)
    unreal.log("TRELLIS BATCH IMPORT COMPLETE: %s (receipt: %s)" % (
        receipt["status"], receipt_path))


main()
