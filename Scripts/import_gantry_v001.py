"""Import the gantry crane and its rails as two separate assets.

THE RAILS ARE A SEPARATE ASSET BECAUSE THE CRANE MOVES AND THE TRACK
DOES NOT (owner, 2026-08-29: "take the rails off and use in the map").
Meshy modelled them as one object; left that way the rails would travel
down the hall with the gantry, which is exactly backwards.

PROVENANCE
  source  Meshy_AI_Industrial_Gantry_Cra_0829100622_part-segmentation.blend
  route   drawn orthographic reference -> Meshy image-to-3D, after two
          text-prompted attempts came back with handrails and a push
          handle on machines that nothing human ever touches
  budget  2,153,579 triangles as delivered. High by design and NOT an
          automatic rejection: the standing decision is that generated
          geometry is kept as a master asset with Nanite, and that
          direction calls are made on measurement rather than reflex.

SCALED FROM THE CLEAR SPAN, not the overall width. What has to fit
under a portal is the craft plus its working room - GantryRailSpanCm -
and that is the opening between the legs, not the outside of the
machine. Measured at 0.1598 m as delivered, so x143.9.
"""
import unreal

SOURCE_DIR = (r"C:\Users\greg_\Projects\LineBossCarFactory_Unreal 5.8"
              r"\SourceAssets\Spacecraft\Gantry_v001")
DEST = "/Game/LineBoss/Candidates/Spacecraft/Gantry_v001"

DROPS = [
    ("LB_GantryCrane_v001.glb", "Crane"),
    ("LB_GantryRails_v001.glb", "Rails"),
]


def fail(reason):
    unreal.log_error("GANTRY IMPORT REFUSED: %s" % reason)
    raise SystemExit(1)


if unreal.EditorAssetLibrary.does_directory_exist(DEST):
    unreal.log("GANTRY: clearing the previous import at %s" % DEST)
    unreal.EditorAssetLibrary.delete_directory(DEST)

for filename, label in DROPS:
    path = "%s\\%s" % (SOURCE_DIR, filename)
    if not unreal.Paths.file_exists(path):
        fail("source missing: %s" % path)
    task = unreal.AssetImportTask()
    task.filename = path
    task.destination_path = "%s/%s" % (DEST, label)
    task.automated = True
    task.replace_existing = True
    task.save = True
    unreal.AssetToolsHelpers.get_asset_tools().import_asset_tasks([task])
    unreal.log("GANTRY: imported %s" % label)

registry = unreal.AssetRegistryHelpers.get_asset_registry()
meshes = []
for data in registry.get_assets_by_path(DEST, recursive=True):
    asset = data.get_asset()
    if isinstance(asset, unreal.StaticMesh):
        meshes.append(asset)

if not meshes:
    fail("no static mesh under %s after import" % DEST)

for mesh in sorted(meshes, key=lambda m: m.get_name()):
    bounds = mesh.get_bounds().box_extent
    nanite = mesh.get_editor_property("nanite_settings").enabled
    slots = [str(s.material_slot_name) for s in mesh.static_materials]
    unreal.log(
        "GANTRY MESH %-30s %8d fallback tris  %6.2f x %6.2f x %6.2f m  "
        "nanite=%s  slots=%s"
        % (mesh.get_name(), mesh.get_num_triangles(0),
           bounds.x * 2 / 100.0, bounds.y * 2 / 100.0,
           bounds.z * 2 / 100.0, nanite, ",".join(slots)))
    if not nanite:
        # Said out loud rather than assumed. At two million triangles a
        # non-Nanite import would be a real cost, and the fallback
        # triangle count above looks identical either way - the flag is
        # what tells them apart.
        unreal.log_warning(
            "GANTRY: %s imported WITHOUT Nanite at this triangle count"
            % mesh.get_name())

unreal.log("GANTRY: %d meshes under %s" % (len(meshes), DEST))
