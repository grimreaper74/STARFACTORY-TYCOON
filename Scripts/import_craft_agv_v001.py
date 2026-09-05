"""Import the CRAFT AGV v001 - the motorised carrier a craft rides down
the line, replacing the procedural stand blockout that stood in for it
since the gantry crane came off on 2026-09-03.

Provenance, recorded here rather than re-derived from a filename: owner
commissioned it through Meshy on 2026-09-04 against a brief written from
this project's own camera measurements (fixed -35 pitch, so top surface
and silhouette carry the read; no fine greebles, which are sub-pixel at
play distance) and its standing rule that nothing on this floor is
handled by people - so no cab, seat, handrails, steps or windows. The
returned drop was reviewed against that brief and accepted. Two GLBs
were delivered; this imports the plain generate. The part-segmentation
sibling is kept beside it in "assets downloads" for a later pass, where
splitting the wheel units out would let them turn.

Meshy normalises every result to a ~2 m box, so the real-world size was
imposed by Tools/export_meshy_glb_v001.py at 1500 cm on the longest
axis, which put the source's 1.900 x 0.449 x 0.256 m at 1500 x 355 x
202 cm and sat it on the ground. That is a metre longer than a Scout
hull (1400) and deliberately NARROWER than one (746): a fuselage
transporter is narrower than what it carries, and the craft overhangs
the sides exactly as it does on a real one.

Nanite static mesh, geometry only - materials are authored in Unreal,
wearing the same graphite surface the rest of the machinery does. Size
verified here within 3%. Refuses to overwrite, writes a receipt.
"""
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path

import unreal

root = Path(unreal.Paths.project_dir())
out = root / "Saved/Audits/Spacecraft/craft_agv_import_v001.json"
if out.exists():
    raise RuntimeError("Refusing to rerun: receipt exists. Author v002.")

NAME = "SM_LB_SC_CraftAGV_v001"
SOURCE_DIR = root / "SourceAssets/Spacecraft/CraftAGV_v001"
DEST = "/Game/LineBoss/Spacecraft/CraftAGV_v001"
DECLARED_CM = 1500.0
PALETTE = "/Game/LineBoss/Materials/Surfaces/MI_LB_Surface_Graphite"
# The GLB the FBX came from, for the provenance chain.
GLB = (root / "assets downloads/Meshy_CraftAGV_2026_09_04"
       / "CraftAGV_generate.glb")

library = unreal.EditorAssetLibrary
tools = unreal.AssetToolsHelpers.get_asset_tools()
failures = []

source = SOURCE_DIR / ("%s.fbx" % NAME)
if not source.exists():
    # The export tool names its output for the asset it was given.
    alt = SOURCE_DIR / "CraftAGV_v001.fbx"
    source = alt if alt.exists() else source
if not source.exists():
    raise RuntimeError("missing source FBX under %s" % SOURCE_DIR)

path = "%s/%s" % (DEST, NAME)
if library.does_asset_exist(path):
    raise RuntimeError("refusing to overwrite %s" % path)

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
task.set_editor_property("destination_path", DEST)
task.set_editor_property("destination_name", NAME)
task.set_editor_property("automated", True)
task.set_editor_property("replace_existing", False)
task.set_editor_property("save", True)
task.set_editor_property("options", options)
tools.import_asset_tasks([task])

asset = library.load_asset(path)
if asset is None or not isinstance(asset, unreal.StaticMesh):
    raise RuntimeError("import produced no StaticMesh at %s" % path)

# NANITE ON, like every other imported prop here.
try:
    settings = unreal.MeshNaniteSettings()
    settings.set_editor_property("enabled", True)
    asset.set_editor_property("nanite_settings", settings)
    asset.modify()
    library.save_loaded_asset(asset, only_if_is_dirty=False)
except Exception as exc:  # noqa: BLE001
    failures.append("could not take Nanite: %s" % exc)
nanite = None
try:
    nanite = bool(asset.get_editor_property(
        "nanite_settings").get_editor_property("enabled"))
except Exception:  # noqa: BLE001
    pass
if nanite is False:
    failures.append("did not take Nanite")

palette = library.load_asset(PALETTE)
if palette is None:
    failures.append("palette material missing: %s" % PALETTE)
else:
    for slot in range(len(asset.static_materials)):
        asset.set_material(slot, palette)
    asset.modify()
    library.save_loaded_asset(asset, only_if_is_dirty=False)

# MEASURE IT. A declared size nobody checks is a claim, not a fact -
# this project has been bitten by exactly that before.
bounds = asset.get_bounds()
extent = bounds.box_extent
measured = {"x": extent.x * 2.0, "y": extent.y * 2.0, "z": extent.z * 2.0}
longest = max(measured.values())
drift = abs(longest - DECLARED_CM) / DECLARED_CM * 100.0
if drift > 3.0:
    failures.append("size drift %.1f%% (declared %.0f, measured %.0f)"
                    % (drift, DECLARED_CM, longest))

tris = None
try:
    tris = asset.get_num_triangles(0)
except Exception:  # noqa: BLE001
    pass


def sha256(path_obj):
    if not path_obj.exists():
        return None
    digest = hashlib.sha256()
    with open(path_obj, "rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


receipt = {
    "generated_utc": datetime.now(timezone.utc).isoformat(),
    "script": "Scripts/import_craft_agv_v001.py",
    "asset": path,
    "subject": "craft AGV - the motorised carrier a craft rides",
    "replaces": "MakeUnitStand procedural blockout",
    "declared_longest_cm": DECLARED_CM,
    "measured_cm": measured,
    "measured_longest_cm": longest,
    "size_drift_percent": round(drift, 3),
    "triangles": tris,
    "nanite": nanite,
    "material": PALETTE,
    "source_fbx": str(source),
    "source_fbx_sha256": sha256(source),
    "source_glb": str(GLB),
    "source_glb_sha256": sha256(GLB),
    "provenance": "Meshy generate, owner-reviewed 2026-09-04; scale "
                  "imposed by Tools/export_meshy_glb_v001.py at 1500 cm "
                  "longest axis",
    "failures": failures,
    "status": "PASS" if not failures else "FAIL_CLOSED",
}
out.parent.mkdir(parents=True, exist_ok=True)
out.write_text(json.dumps(receipt, indent=2), encoding="utf-8")
unreal.log("CRAFT AGV IMPORT %s -> %s" % (receipt["status"], out))
if failures:
    raise RuntimeError("craft AGV import failed closed: %s" % failures)
