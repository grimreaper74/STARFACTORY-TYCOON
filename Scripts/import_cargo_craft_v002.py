"""Import the CARGO-01 v002 kit: a real fused hull (from the owner's
Meshy part-segmentation drop, 2026-09-03) plus its two separable engine
nacelles, replacing the single-mesh v001 craft. v001 stays on disk as
evidence, untouched.

Provenance chain, recorded here rather than re-derived from a filename:
the source was Meshy's part-segmentation export of the Cargo-01 concept,
delivered as 7 objects. Two (the landing legs) and one (the ramp) were
identified by isolated render and joined as fixed hull furniture. Two
(the hull body slices) shared the same distinctive hatch cutout in their
own isolated renders - evidence they were overlapping slices of one
volume, not two adjacent parts - so they were pushed into the position
that maximised their surface-point containment inside each other
(peaked at 71% before falling off, confirming the overlap) and merged
with a real Boolean union (252,936 tris, not a fallback join). The
remaining two (the engine nacelles) read as a genuine left/right pair
and stayed separate, sized to the same 180 cm already verified for the
standalone thruster pod so they sit right at the existing, already-
tuned ThrusterPods socket. All three were decimated (hull 282,747 ->
38,940; engines 85,785 -> 14,999 and 54,537 -> 11,999) after a render
check showed the panel detail held up.

Nanite static meshes, geometry only - materials are authored in Unreal,
the same graphite surface the v001 craft wears. Sizes verified here
within 3%. Refuses to overwrite, writes a receipt.
"""
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path

import unreal

root = Path(unreal.Paths.project_dir())
out = root / "Saved/Audits/Spacecraft/cargo_craft_import_v002.json"
if out.exists():
    raise RuntimeError("Refusing to rerun: receipt exists. Author v003.")

# name -> (source_dir, dest_path, axis, declared_cm, label)
EXPECTED = {
    "SM_LB_SC_Cargo01_Craft_v002": (
        root / "SourceAssets/Candidate/Spacecraft/CargoCraft_v002/export",
        "/Game/LineBoss/Candidates/Spacecraft/CargoCraft_v002",
        "longest", 2100, "fused hull (body + landing legs + ramp)"),
    "SM_LB_SC_Cargo01_ThrusterA_v001": (
        root / "SourceAssets/Candidate/Spacecraft/CargoParts_v006/export",
        "/Game/LineBoss/Candidates/Spacecraft/CargoParts_v001",
        "longest", 180, "engine nacelle A"),
    "SM_LB_SC_Cargo01_ThrusterB_v001": (
        root / "SourceAssets/Candidate/Spacecraft/CargoParts_v006/export",
        "/Game/LineBoss/Candidates/Spacecraft/CargoParts_v001",
        "longest", 180, "engine nacelle B"),
}
PALETTE = "/Game/LineBoss/Materials/Surfaces/MI_LB_Surface_Graphite"

library = unreal.EditorAssetLibrary
tools = unreal.AssetToolsHelpers.get_asset_tools()
failures = []
rows = []
tasks = []
for name, (source_dir, dest, axis, target_cm, label) in sorted(EXPECTED.items()):
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

for name, (source_dir, dest, axis, target_cm, label) in sorted(EXPECTED.items()):
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
    triangle_count = None
    try:
        triangle_count = asset.get_num_triangles(0)
    except Exception:  # noqa: BLE001
        pass
    source = source_dir / ("%s.fbx" % name)
    rows.append({
        "asset": path,
        "label": label,
        "source_sha256": hashlib.sha256(
            source.read_bytes()).hexdigest().upper(),
        "provenance": "Owner's Meshy part-segmentation drop of the "
            "Cargo-01 concept, 2026-09-03 (Meshy_AI__0903101341_"
            "part-segmentation.blend) - reassembled, fused and "
            "decimated in Blender per this script's module docstring; "
            "identified by isolated render, not filename",
        "defining_axis": axis,
        "declared_cm": target_cm,
        "measured_cm": round(measured),
        "imported_extent_cm": [round(dims["x"]), round(dims["y"]),
                               round(dims["z"])],
        "nanite_enabled": nanite,
        "triangle_count": triangle_count,
    })

report = {
    "$schema": "lineboss/audit/cargo-craft-import-v002/v1",
    "generated_utc": datetime.now(timezone.utc).isoformat(),
    "status": "PASS__CARGO_CRAFT_V2_IMPORTED" if not failures
              else "FAIL_CLOSED__CARGO_CRAFT_V2_IMPORT",
    "assets": rows,
    "failures": failures,
    "supersedes": "/Game/LineBoss/Candidates/Spacecraft/CargoCraft_v001/"
        "SM_LB_SC_Cargo01_Craft_v001 (left on disk as evidence, unused "
        "once the C++ registration is repointed at v002)",
    "not_proven": [
        "Import proves size, Nanite and triangle count only. Whether the "
        "hull's fused seam reads clean at gameplay camera distance, and "
        "whether the two engines sit right at the ThrusterPods socket, "
        "is judged on a rendered PIE frame once wired into the presenter.",
    ],
}
out.parent.mkdir(parents=True, exist_ok=True)
out.write_text(json.dumps(report, indent=2), encoding="utf-8")
unreal.log("CARGO CRAFT V2 IMPORT %s: %d assets, %d failures"
           % (report["status"], len(rows), len(failures)))
for failure in failures:
    unreal.log_warning(failure)
