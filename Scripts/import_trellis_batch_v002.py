"""Import TRELLIS batch 2 (2026-09-01) + the three regenerated UI icons.

Same lane shape as import_trellis_batch_v001.py (which is spent - its
receipt exists and that lane refuses to rerun): staged FBX with scale
baked in Blender, FbxImportUI combine, Nanite read back, defining axis
verified at 3%, fail-closed receipt.

Additionally imports three UI icon PNGs the car-era content clear-out
took (T_LB_Icon_BuyBay, T_LB_Icon_Session_Save, T_LB_Icon_Session_Load)
into the surviving UI folder so the buy-bay and session buttons stop
rendering blank.
"""
import json
import os
import unreal

RECEIPT_NAME = "trellis_batch_import_v002.json"
DEST_ROOT = "/Game/Spacecraft/Props"
ICON_DEST = "/Game/LineBoss/Candidates/Spacecraft/StationMeshes_v001/UI"

BATCH = {
    "delivery_dock_v001": ("longest", 1000.0),
    "power_station_v001": ("z", 600.0),
    "assembly_drone_v001": ("longest", 150.0),
    "fabricator_cell_v003": ("longest", 400.0),
    "charging_dock_v002": ("longest", 400.0),
}

ICON_SOURCE_DIR = (
    "C:/Users/greg_/AppData/Local/Temp/claude/"
    "C--Users-greg--Projects-LineBossCarFactory-Unreal-5-8/"
    "908db2d8-20d0-49c5-84e0-90e9b899c4dc/scratchpad/icons")
ICONS = ["T_LB_Icon_BuyBay", "T_LB_Icon_Session_Save",
         "T_LB_Icon_Session_Load"]


def import_meshes(stage, results):
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
    return failures


def import_icons(results):
    failures = 0
    for icon in ICONS:
        entry = {"asset": icon, "kind": "ui_icon"}
        png = os.path.join(ICON_SOURCE_DIR, "%s.png" % icon)
        if not os.path.isfile(png):
            entry["status"] = "FAIL_CLOSED__PNG_MISSING"
            failures += 1
            results.append(entry)
            continue
        task = unreal.AssetImportTask()
        task.filename = png
        task.destination_path = ICON_DEST
        task.automated = True
        task.replace_existing = True
        task.save = True
        unreal.AssetToolsHelpers.get_asset_tools().import_asset_tasks(
            [task])
        imported = list(task.imported_object_paths or [])
        if imported:
            entry["assetPath"] = imported[0]
            entry["status"] = "PASS__IMPORTED"
            unreal.log("ICON IMPORT %s -> %s" % (icon, imported[0]))
        else:
            entry["status"] = "FAIL_CLOSED__IMPORT_FAILED"
            failures += 1
        results.append(entry)
    return failures


def main():
    project = unreal.SystemLibrary.get_project_directory()
    stage = os.path.join(project, "Saved", "TrellisImportStage_v001")
    audit_dir = os.path.join(project, "Saved", "Audits", "Spacecraft")
    os.makedirs(audit_dir, exist_ok=True)
    receipt_path = os.path.join(audit_dir, RECEIPT_NAME)
    if os.path.exists(receipt_path):
        unreal.log_error(
            "RECEIPT EXISTS: %s - refusing rerun; author v003." %
            receipt_path)
        return

    results = []
    failures = import_meshes(stage, results)
    failures += import_icons(results)

    receipt = {
        "$schema": "lineboss/audit/trellis-batch-import/v1",
        "status": ("PASS__ALL_VERIFIED" if failures == 0
                   else "FAIL_CLOSED__%d_FAILURES" % failures),
        "destinationRoot": DEST_ROOT,
        "assets": results,
    }
    with open(receipt_path, "w", encoding="utf-8") as handle:
        json.dump(receipt, handle, indent=2)
    unreal.log("TRELLIS BATCH 2 COMPLETE: %s (receipt: %s)" % (
        receipt["status"], receipt_path))


main()
