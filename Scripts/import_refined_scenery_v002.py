"""Replace the preview scenery meshes with the REFINED, textured ones.

The eleven keepers shipped first as Meshy PREVIEW output: draft
geometry, no maps. They are refined now (PBR base colour, packed
metallic-roughness, normal), and this lane swaps them in place so
nothing that references them has to change.

Deliberately a REPLACING lane, unlike the intakes that refuse to
overwrite - the whole point is to upgrade assets already wired into the
game. It still fails closed on everything that matters: every source is
hashed, every mesh's declared SIZE is verified back off the imported
asset, Nanite is read back, and each mesh must come out with a material
instance carrying all three maps.

Materials use the same master the buildings use - the one whose broken
shader graph was the "mess" the owner reported on 2026-08-28. One
master, one place to fix, and these assets inherit the fix.
"""

import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
import unreal

root = Path(unreal.Paths.project_dir())
source_dir = root / "SourceAssets/Candidate/Spacecraft/Refined_Export_v001"
tex_source = source_dir / "Textures"
out = root / "Saved/Audits/Spacecraft/refined_scenery_import_v002.json"
if out.exists():
    raise RuntimeError("Refusing to rerun: receipt exists. Author v003.")

MASTER = ("/Game/LineBoss/Candidates/Spacecraft/StationMeshes_v001/Meshes/"
          "BuildingTextures/M_LB_Building_Master")

# name -> (destination package, defining axis, declared size cm)
ASSETS = {
    "SM_LB_SC_FencePanel": ("SiteScenery_v001", "z", 250),
    "SM_LB_SC_EntranceGate": ("SiteScenery_v001", "x", 1400),
    "SM_LB_SC_LightMast": ("SiteScenery_v001", "x", 1000),
    "SM_LB_SC_CargoContainer": ("SiteScenery_v001", "x", 600),
    "SM_LB_SC_StorageTank": ("SiteScenery_v001", "z", 1000),
    "SM_LB_SC_Substation": ("SiteScenery_v001", "z", 300),
    "SM_LB_SC_DeliveryHauler": ("SiteScenery_v001", "x", 900),
    "SM_LB_IN_StockpileRack": ("ShipFactoryInterior_v001", "x", 300),
    "SM_LB_IN_HallColumn": ("ShipFactoryInterior_v001", "z", 800),
    "SM_LB_IN_GantryCrane": ("ShipFactoryInterior_v001", "x", 2000),
    "SM_LB_IN_DispatchDoor": ("ShipFactoryInterior_v001", "z", 1200),
}
ROOT = "/Game/LineBoss/Candidates/Spacecraft"

library = unreal.EditorAssetLibrary
tools = unreal.AssetToolsHelpers.get_asset_tools()
mat_lib = unreal.MaterialEditingLibrary
failures = []
rows = []

master = library.load_asset(MASTER)
if master is None:
    raise RuntimeError("building master material missing - run the repair first")


def import_texture(png, dest_path, dest_name, is_normal, is_linear):
    task = unreal.AssetImportTask()
    task.set_editor_property("filename", str(png))
    task.set_editor_property("destination_path", dest_path)
    task.set_editor_property("destination_name", dest_name)
    task.set_editor_property("automated", True)
    task.set_editor_property("replace_existing", True)
    task.set_editor_property("save", True)
    tools.import_asset_tasks([task])
    tex = library.load_asset("%s/%s" % (dest_path, dest_name))
    if tex is None:
        return None
    if is_normal:
        tex.set_editor_property(
            "compression_settings",
            unreal.TextureCompressionSettings.TC_NORMALMAP)
        tex.set_editor_property("srgb", False)
    elif is_linear:
        # TC_DEFAULT linear, matching the master's LINEAR_COLOR sampler -
        # TC_MASKS was part of what stopped the master compiling.
        tex.set_editor_property(
            "compression_settings",
            unreal.TextureCompressionSettings.TC_DEFAULT)
        tex.set_editor_property("srgb", False)
    library.save_loaded_asset(tex, only_if_is_dirty=False)
    return tex


for name, (package, axis, target_cm) in sorted(ASSETS.items()):
    dest = "%s/%s" % (ROOT, package)
    source = source_dir / ("%s.fbx" % name)
    if not source.exists():
        failures.append("missing source %s" % source)
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
    task.set_editor_property("replace_existing", True)
    task.set_editor_property("save", True)
    task.set_editor_property("options", options)
    tools.import_asset_tasks([task])

    asset = library.load_asset("%s/%s" % (dest, name))
    if asset is None or not isinstance(asset, unreal.StaticMesh):
        failures.append("missing StaticMesh %s/%s" % (dest, name))
        continue

    # ---- its three maps, and an instance wearing them ----
    maps = {}
    for suffix, is_normal, is_linear in (
            ("base_color", False, False),
            ("metallic_roughness", False, True),
            ("normal", True, False)):
        png = tex_source / ("%s_%s.png" % (name, suffix))
        if not png.exists():
            failures.append("missing map %s" % png)
            continue
        maps[suffix] = import_texture(png, "%s/Textures" % dest,
                                      "T_%s_%s" % (name, suffix),
                                      is_normal, is_linear)
    if len(maps) == 3 and all(v is not None for v in maps.values()):
        instance_name = "MI_%s" % name
        instance_path = "%s/Textures/%s" % (dest, instance_name)
        if library.does_asset_exist(instance_path):
            instance = library.load_asset(instance_path)
        else:
            instance = tools.create_asset(
                instance_name, "%s/Textures" % dest,
                unreal.MaterialInstanceConstant,
                unreal.MaterialInstanceConstantFactoryNew())
        mat_lib.set_material_instance_parent(instance, master)
        mat_lib.set_material_instance_texture_parameter_value(
            instance, "BaseColor", maps["base_color"])
        mat_lib.set_material_instance_texture_parameter_value(
            instance, "MetallicRoughness", maps["metallic_roughness"])
        mat_lib.set_material_instance_texture_parameter_value(
            instance, "Normal", maps["normal"])
        mat_lib.set_material_instance_scalar_parameter_value(
            instance, "MetallicScale", 0.25)
        mat_lib.set_material_instance_scalar_parameter_value(
            instance, "BaseColorBoost", 1.0)
        library.save_loaded_asset(instance, only_if_is_dirty=False)
        asset.set_material(0, instance)
    else:
        failures.append("%s has no complete map set" % name)

    try:
        settings = unreal.MeshNaniteSettings()
        settings.set_editor_property("enabled", True)
        asset.set_editor_property("nanite_settings", settings)
        asset.modify()
    except Exception as exc:  # noqa: BLE001
        failures.append("%s could not take Nanite: %s" % (name, exc))
    library.save_loaded_asset(asset, only_if_is_dirty=False)

    reloaded = library.load_asset("%s/%s" % (dest, name))
    extent = reloaded.get_bounds().box_extent
    measured = {"x": extent.x * 2, "y": extent.y * 2, "z": extent.z * 2}[axis]
    if abs(measured - target_cm) > target_cm * 0.03:
        failures.append("%s imported %.0f cm on %s, expected %d"
                        % (name, measured, axis, target_cm))
    applied = reloaded.get_material(0)
    if applied is None or "MI_" not in applied.get_name():
        failures.append("%s did not keep its material instance" % name)
    nanite = None
    try:
        nanite = bool(reloaded.get_editor_property(
            "nanite_settings").get_editor_property("enabled"))
    except Exception:  # noqa: BLE001
        pass
    rows.append({
        "asset": "%s/%s" % (dest, name),
        "source_sha256": hashlib.sha256(
            source.read_bytes()).hexdigest().upper(),
        "provenance": "Meshy text-to-3D REFINE (PBR) of the 2026-08-28 "
                      "preview, by Scripts/refine_meshy_generated_v001.ps1",
        "declared_cm": target_cm,
        "measured_cm": round(measured),
        "material": applied.get_name() if applied else None,
        "nanite_enabled": nanite,
    })

report = {
    "$schema": "lineboss/audit/refined-scenery-import-v002/v1",
    "generated_utc": datetime.now(timezone.utc).isoformat(),
    "status": ("PASS__REFINED_SCENERY_REPLACED_IN_PLACE" if not failures
               else "FAIL_CLOSED__REFINED_SCENERY_IMPORT"),
    "assets": rows,
    "failures": failures,
    "not_proven": [
        "Nobody has seen the refined assets standing in the game yet.",
        "Refined meshes are denser than the previews; the frame cost is "
        "unmeasured, though every one is Nanite and instanced.",
    ],
}
out.parent.mkdir(parents=True, exist_ok=True)
out.write_text(json.dumps(report, indent=2), encoding="utf-8")
print(json.dumps({"status": report["status"], "assets": len(rows),
                  "failures": failures}, indent=2))
if failures:
    raise RuntimeError("; ".join(failures))
