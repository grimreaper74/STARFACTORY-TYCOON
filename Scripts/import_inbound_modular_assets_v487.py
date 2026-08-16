"""Import the source-only inbound modules into an isolated Unreal candidate folder.

No map is loaded, saved or promoted. All dimensions are visual/TBC. This script owns
only Candidate_v001 and may replace assets in that folder during deterministic reruns.
"""

from pathlib import Path
import hashlib
import json
import unreal

PROJECT = Path(unreal.Paths.project_dir())
SOURCE = PROJECT / "SourceAssets/Candidate/PressShop/InboundCoilDelivery/Modular_v001/FBX"
DEST = "/Game/LineBoss/IndustrialKit/InboundCoilDelivery/Candidate_v001"
OUT = Path(unreal.Paths.project_saved_dir()) / "Audits/PressShopIntegration/inbound_modular_import_v487.json"

MODULES = {
    "SM_CA_MW_MOD_LorryCab_v001": ((200, 350), (200, 400), (200, 350)),
    "SM_CA_MW_MOD_CoilTrailer_v001": ((220, 300), (1000, 1200), (300, 450)),
    "SM_CA_MW_MOD_DockGuidesAndRestraint_v001": ((280, 380), (650, 750), (50, 100)),
    "SM_CA_MW_MOD_DockControlAndSignals_v001": ((100, 180), (30, 100), (240, 290)),
    "SM_CA_MW_MOD_ReceivingSaddle_v001": ((240, 300), (300, 370), (80, 130)),
    "SM_CA_MW_MOD_AGVHandoffGuides_v001": ((220, 280), (380, 450), (20, 60)),
    "SM_CA_MW_MOD_IdentityScanner_v001": ((25, 60), (20, 50), (160, 210)),
}


def sha256(path):
    value = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            value.update(chunk)
    return value.hexdigest()


unreal.SystemLibrary.execute_console_command(None, "Interchange.FeatureFlags.Import.FBX 0")
library = unreal.EditorAssetLibrary
tools = unreal.AssetToolsHelpers.get_asset_tools()
tasks = []
source_hashes = {}
for name in MODULES:
    fbx = SOURCE / f"{name}.fbx"
    if not fbx.is_file():
        raise RuntimeError(f"Missing inbound module source: {fbx}")
    source_hashes[name] = sha256(fbx)
    asset_path = f"{DEST}/{name}"
    if library.does_asset_exist(asset_path):
        if not library.delete_asset(asset_path):
            raise RuntimeError(f"Could not replace owned candidate asset {asset_path}")
    task = unreal.AssetImportTask()
    task.set_editor_properties({
        "filename": str(fbx), "destination_path": DEST, "destination_name": name,
        "automated": True, "replace_existing": True, "replace_existing_settings": True,
        "save": True,
    })
    options = unreal.FbxImportUI()
    options.set_editor_properties({
        "import_mesh": True, "import_as_skeletal": False, "import_materials": True,
        "import_textures": False, "mesh_type_to_import": unreal.FBXImportType.FBXIT_STATIC_MESH,
        "automated_import_should_detect_type": False,
    })
    options.static_mesh_import_data.set_editor_properties({
        "combine_meshes": True, "convert_scene": True, "convert_scene_unit": True,
        "generate_lightmap_u_vs": True, "auto_generate_collision": True,
        # Blender's FBX exporter already writes the centimetre conversion metadata;
        # convert_scene_unit applies it on import. A further 100x scale would create
        # a 245 m lorry and is deliberately rejected by the bounds gate below.
        "remove_degenerates": True, "import_uniform_scale": 1.0,
    })
    task.options = options
    tasks.append(task)

tools.import_asset_tasks(tasks)
unreal.AutomationUtilsBlueprintLibrary.finish_all_asset_compilation()

validated = []
for name, expected_axes in MODULES.items():
    asset_path = f"{DEST}/{name}"
    mesh = library.load_asset(asset_path)
    if mesh is None:
        raise RuntimeError(f"Inbound module import missing: {asset_path}")
    size = mesh.get_bounds().box_extent * 2.0
    actual = (float(size.x), float(size.y), float(size.z))
    for axis, value, expected in zip("XYZ", actual, expected_axes):
        if not expected[0] <= value <= expected[1]:
            raise RuntimeError(f"{name} {axis} bound {value:.2f} cm outside TBC visual gate {expected}")
    body_setup = mesh.get_editor_property("body_setup")
    validated.append({
        "asset": asset_path, "bounds_cm": [round(value, 3) for value in actual],
        "source_sha256": source_hashes[name], "has_body_setup": body_setup is not None,
    })
    library.save_loaded_asset(mesh, only_if_is_dirty=False)

OUT.parent.mkdir(parents=True, exist_ok=True)
OUT.write_text(json.dumps({
    "candidate": "InboundCoilDelivery_Candidate_v001",
    "evidence_version": 487,
    "status": "ISOLATED_IMPORT_ONLY_NOT_PROMOTED",
    "map_saved": False,
    "engineering_values": "TBC",
    "assets": validated,
}, indent=2), encoding="utf-8")
unreal.log(f"Inbound modular v487 import validated: {OUT}")
