"""Import the TRICYCLE LANDING GEAR leg as a Nanite static mesh.

Same fail-closed shape as the buildings intake: sha256 recorded for
every source, refuses to overwrite an existing asset, sets Nanite and
reads it BACK, and measures the imported bounds against what the export
declared - a prop that imports at the wrong size is the fault this whole
pipeline exists to catch (Meshy normalises everything to a ~2 m box, so
size is imposed at export and must be verified at import).

ONE mesh, placed three times. The owner left the split to me ("up to
you if u do it in one and split or in 3"), and the answer was forced by
the generator: two attempts at a distinct NOSE leg both came back as
tripod lander stands with the wheel hung on them sideways, while the
MAIN leg came back correct first time - oleo strut, side stay, torque
link, wheel on a braked hub. Real tricycle legs do resemble each other,
so the nose leg is this mesh scaled down, and the meaningful difference
between nose and main lives where it matters: in the PARTS, where a
nose leg carries no brake unit.
"""

import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
import unreal

root = Path(unreal.Paths.project_dir())
source_dir = root / "SourceAssets/Candidate/Spacecraft/LandingGear_v006/export"
dest = "/Game/LineBoss/Candidates/Spacecraft/LandingGear_v001"
out = root / "Saved/Audits/Spacecraft/landing_gear_import_v001.json"
if out.exists():
    raise RuntimeError("Refusing to rerun: receipt exists. Author v002.")

# name -> the size the export DECLARED, on the axis that defines it.
EXPECTED = {
    "SM_LB_GEAR_MainLeg": ("z", 110),
}
# Materials are authored in Unreal now (owner 2026-08-28), so these
# take the project palette rather than any imported map.
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
    options.set_editor_property("import_textures", True)
    options.set_editor_property("import_materials", True)
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
        asset.set_material(0, palette)
        library.save_loaded_asset(asset, only_if_is_dirty=False)
    extent = asset.get_bounds().box_extent
    measured = {"x": extent.x * 2, "y": extent.y * 2, "z": extent.z * 2}[axis]
    # 3% tolerance: FBX round-trips are not bit-exact, but a prop that
    # imports at the wrong SIZE is the fault worth failing on.
    if abs(measured - target_cm) > target_cm * 0.03:
        failures.append("%s imported %.0f cm on %s, expected %d"
                        % (name, measured, axis, target_cm))
    source = source_dir / ("%s.fbx" % name)
    rows.append({
        "asset": path,
        "source_sha256": hashlib.sha256(
            source.read_bytes()).hexdigest().upper(),
        "provenance": "Meshy text-to-3D preview, generated 2026-08-28 "
                      "by Scripts/submit_meshy_landing_gear_v006.ps1",
        "defining_axis": axis,
        "declared_cm": target_cm,
        "measured_cm": round(measured),
        "imported_extent_cm": [round(extent.x * 2), round(extent.y * 2),
                               round(extent.z * 2)],
        "nanite_enabled": nanite,
    })

report = {
    "$schema": "lineboss/audit/landing-gear-import-v001/v1",
    "generated_utc": datetime.now(timezone.utc).isoformat(),
    "status": ("PASS__LANDING_GEAR_IMPORTED__NANITE_ON" if not failures
               else "FAIL_CLOSED__LANDING_GEAR_IMPORT"),
    "destination": dest,
    "assets": rows,
    "failures": failures,
    "not_proven": [
        "This is a Meshy PREVIEW mesh - untextured draft geometry. It carries no PBR maps; it takes the project's graphite palette instance, per the standing rule that materials are authored in Unreal.",
        "Nobody has seen it under a craft yet.",
        "ONE MESH, THREE LEGS. Two attempts at a distinct NOSE leg (v006, v007, 20 credits each) both returned a tripod lander stand with a wheel hung on it sideways; the generator reads 'spacecraft' plus 'leg' as a lander foot and neither naming an airliner nose wheel nor forbidding tripods pulled it back. The MAIN leg was correct first time. The nose leg is therefore this mesh scaled down, which real tricycle gear supports; the nose/main difference lives in the PARTS, where a nose leg carries no brake unit.",
    ],
}
out.parent.mkdir(parents=True, exist_ok=True)
out.write_text(json.dumps(report, indent=2), encoding="utf-8")
print(json.dumps({"status": report["status"], "assets": len(rows),
                  "failures": failures}, indent=2))
if failures:
    raise RuntimeError("; ".join(failures))
