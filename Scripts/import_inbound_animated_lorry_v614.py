"""Import the additive modular inbound lorry and four independently movable coils."""
from pathlib import Path
import hashlib
import json
import unreal

PROJECT = Path(unreal.Paths.project_dir())
SOURCE = PROJECT / "SourceAssets/Candidate/PressShop/InboundCoilDelivery/AnimatedLorry_v001/FBX"
DEST = "/Game/LineBoss/IndustrialKit/InboundCoilDelivery/AnimatedLorryCandidate_v001"
MAT = "/Game/LineBoss/IndustrialKit/InboundCoilDelivery/Candidate_v001/Materials_v001"
OUT = Path(unreal.Paths.project_saved_dir()) / "Audits/PressShopIntegration/inbound_animated_lorry_import_v614.json"
FILES = ["SM_CA_MW_Inbound_LorryChassis_v001"] + [
    f"SM_CA_MW_Inbound_TrailerCoil_{index:02d}_v001" for index in range(1, 5)
]


def sha256(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


library = unreal.EditorAssetLibrary
tools = unreal.AssetToolsHelpers.get_asset_tools()
unreal.SystemLibrary.execute_console_command(None, "Interchange.FeatureFlags.Import.FBX 0")
tasks = []
hashes = {}
for name in FILES:
    source = SOURCE / f"{name}.fbx"
    if not source.exists():
        raise RuntimeError(f"Missing animated-lorry source: {source}")
    hashes[name] = sha256(source)
    task = unreal.AssetImportTask()
    task.set_editor_properties({
        "filename": str(source),
        "destination_path": DEST,
        "destination_name": name,
        "automated": True,
        "replace_existing": False,
        "save": True,
    })
    options = unreal.FbxImportUI()
    options.set_editor_properties({
        "import_mesh": True,
        "import_as_skeletal": False,
        "import_materials": False,
        "import_textures": False,
        "mesh_type_to_import": unreal.FBXImportType.FBXIT_STATIC_MESH,
        "automated_import_should_detect_type": False,
    })
    options.static_mesh_import_data.set_editor_properties({
        "combine_meshes": True,
        "convert_scene": True,
        "convert_scene_unit": True,
        "generate_lightmap_u_vs": True,
        "auto_generate_collision": True,
        "remove_degenerates": True,
        "import_uniform_scale": 1.0,
    })
    task.options = options
    tasks.append(task)

tools.import_asset_tasks(tasks)
unreal.AutomationUtilsBlueprintLibrary.finish_all_asset_compilation()
rows = []
for name in FILES:
    asset_path = f"{DEST}/{name}"
    mesh = library.load_asset(asset_path)
    if not isinstance(mesh, unreal.StaticMesh):
        raise RuntimeError(f"Import did not create {asset_path}")
    size = mesh.get_bounds().box_extent * 2.0
    bounds = [float(size.x), float(size.y), float(size.z)]
    if min(bounds) <= 1.0:
        raise RuntimeError(f"Degenerate bounds on {name}: {bounds}")
    slots = []
    for index, entry in enumerate(mesh.get_editor_property("static_materials")):
        slot = str(entry.get_editor_property("material_slot_name"))
        material = library.load_asset(f"{MAT}/{slot}_v001")
        if material is not None:
            mesh.set_material(index, material)
        slots.append(slot)
    if mesh.get_editor_property("body_setup") is None:
        raise RuntimeError(f"No collision body setup on {name}")
    library.save_loaded_asset(mesh, only_if_is_dirty=False)
    rows.append({
        "asset": asset_path,
        "bounds_cm": [round(value, 3) for value in bounds],
        "material_slots": slots,
        "source_sha256": hashes[name],
    })

coil_rows = [row for row in rows if "TrailerCoil" in row["asset"]]
if len(coil_rows) != 4:
    raise RuntimeError(f"Expected exactly four independent coil assets, found {len(coil_rows)}")
OUT.parent.mkdir(parents=True, exist_ok=True)
OUT.write_text(json.dumps({
    "status": "PASS_ISOLATED_FUNCTIONAL_ASSET_INTAKE_NOT_PROMOTED",
    "candidate": "AnimatedLorryCandidate_v001",
    "parent_source": "InboundCoilDelivery_Modular_v005",
    "configuration": "one unloaded chassis plus exactly four independently movable labelled coils",
    "engineering_values": "TBC",
    "assets": rows,
}, indent=2), encoding="utf-8")
unreal.log("LINE_BOSS_INBOUND_ANIMATED_LORRY_V614_IMPORT_PASS")
