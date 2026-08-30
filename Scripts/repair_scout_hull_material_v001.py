"""Give the SCOUT its hull material. It has never had one.

The first launch ever photographed (2026-08-28) showed the craft as a
dark grey shape. The probe found why: every Scout mesh - chassis,
airframe, fitted, whole craft, both LODs - is assigned
/Engine/EngineMaterials/WorldGridMaterial, the engine's default. The
CARGO tier has a proper MI_LB_SC_Cargo01_Hull; the Scout was missed.

Its three maps were already in the project, imported and unused:
T_LB_SC_Scout01_BaseColor, _MR and _Normal. So this builds the sibling
instance the Cargo has - same master (M_LB_MeshyPBR_v004), same
parameter names - and assigns it to every Scout mesh.

This matters more than it sounds: the Scout is the craft in the game's
signature moment, the one the owner's wishlist clip is built around,
and it has been rendering as an untextured blob in every frame anyone
would have captured.

Fail-closed: refuses to rerun over its receipt, and reads every
assignment back off the saved asset rather than trusting the setter.
"""

import json
from datetime import datetime, timezone
from pathlib import Path
import unreal

root = Path(unreal.Paths.project_dir())
out = root / "Saved/Audits/Spacecraft/scout_hull_material_v001.json"
if out.exists():
    raise RuntimeError("Refusing to rerun: receipt exists. Author v002.")

SPACECRAFT = "/Game/LineBoss/Candidates/Spacecraft"
MASTER = "%s/StationMeshes_v001/Materials/M_LB_MeshyPBR_v004" % SPACECRAFT
MAT_DIR = "%s/StationMeshes_v001/Materials" % SPACECRAFT
TEX_DIR = "%s/SpacecraftTestBay_v001/Textures" % SPACECRAFT
INSTANCE = "MI_LB_SC_Scout01_Hull"

library = unreal.EditorAssetLibrary
tools = unreal.AssetToolsHelpers.get_asset_tools()
mat_lib = unreal.MaterialEditingLibrary
failures = []

master = library.load_asset(MASTER)
if master is None:
    raise RuntimeError("Meshy PBR master missing: %s" % MASTER)
maps = {
    "BaseColor": library.load_asset("%s/T_LB_SC_Scout01_BaseColor" % TEX_DIR),
    "MetallicRoughness": library.load_asset("%s/T_LB_SC_Scout01_MR" % TEX_DIR),
    "Normal": library.load_asset("%s/T_LB_SC_Scout01_Normal" % TEX_DIR),
}
for name, tex in maps.items():
    if tex is None:
        failures.append("Scout map %s missing" % name)
if failures:
    raise RuntimeError("; ".join(failures))

instance_path = "%s/%s" % (MAT_DIR, INSTANCE)
if library.does_asset_exist(instance_path):
    instance = library.load_asset(instance_path)
else:
    instance = tools.create_asset(
        INSTANCE, MAT_DIR, unreal.MaterialInstanceConstant,
        unreal.MaterialInstanceConstantFactoryNew())
mat_lib.set_material_instance_parent(instance, master)
for param, tex in maps.items():
    mat_lib.set_material_instance_texture_parameter_value(
        instance, param, tex)
mat_lib.set_material_instance_scalar_parameter_value(
    instance, "BaseColorBoost", 1.0)
library.save_loaded_asset(instance, only_if_is_dirty=False)

# Every Scout mesh: whole craft, build forms, LODs.
rows = []
for asset in library.list_assets(SPACECRAFT, recursive=True):
    name = asset.split("/")[-1].split(".")[0]
    if "Scout01" not in name or not name.startswith("SM_"):
        continue
    if "Canopy" in name:
        continue   # the canopy has its own glass material and keeps it
    mesh = library.load_asset(asset.split(".")[0])
    if not isinstance(mesh, unreal.StaticMesh):
        continue
    before = mesh.get_material(0)
    before_name = before.get_name() if before else "NONE"
    mesh.set_material(0, instance)
    library.save_loaded_asset(mesh, only_if_is_dirty=False)
    reloaded = library.load_asset(asset.split(".")[0])
    after = reloaded.get_material(0)
    applied = after is not None and after.get_name() == INSTANCE
    if not applied:
        failures.append("%s did not keep the hull instance" % name)
    rows.append({"mesh": name, "was": before_name, "applied": applied})

report = {
    "$schema": "lineboss/audit/scout-hull-material-v001/v1",
    "generated_utc": datetime.now(timezone.utc).isoformat(),
    "status": ("PASS__SCOUT_HULL_MATERIAL_APPLIED" if not failures
               else "FAIL_CLOSED__SCOUT_HULL_MATERIAL"),
    "why": ("Every Scout mesh wore /Engine/EngineMaterials/"
            "WorldGridMaterial - the engine default - while the Cargo "
            "tier had a real hull instance. Found by photographing the "
            "launch, which nobody had done before."),
    "instance": instance_path,
    "master": MASTER,
    "textures": {k: v.get_path_name() for k, v in maps.items()},
    "meshes": rows,
    "failures": failures,
    "not_proven": [
        "The look is unjudged: the maps are the ones shipped with the "
        "Scout, and nobody has said whether the craft should read this "
        "way. It is now TEXTURED rather than default - that is all "
        "this claims.",
    ],
}
out.parent.mkdir(parents=True, exist_ok=True)
out.write_text(json.dumps(report, indent=2), encoding="utf-8")
print(json.dumps({"status": report["status"], "meshes": len(rows),
                  "failures": failures}, indent=2))
if failures:
    raise RuntimeError("; ".join(failures))
