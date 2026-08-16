"""Import/bind Modular_v004 to a new isolated Unreal candidate folder."""
from pathlib import Path
import hashlib
import json
import unreal

PROJECT = Path(unreal.Paths.project_dir())
SOURCE = PROJECT / "SourceAssets/Candidate/PressShop/InboundCoilDelivery/Modular_v004/FBX"
DEST = "/Game/LineBoss/IndustrialKit/InboundCoilDelivery/Candidate_v004"
MAT = "/Game/LineBoss/IndustrialKit/InboundCoilDelivery/Candidate_v001/Materials_v001"
OUT = Path(unreal.Paths.project_saved_dir()) / "Audits/PressShopIntegration/inbound_modular_import_v506.json"
MODULES = {
    "SM_CA_MW_MOD_LorryCab_v004": ((240, 300), (260, 340), (270, 340)),
    "SM_CA_MW_MOD_CoilTrailer_v004": ((220, 300), (1000, 1200), (300, 450)),
    "SM_CA_MW_MOD_DockGuidesAndRestraint_v004": ((280, 380), (650, 750), (50, 100)),
    "SM_CA_MW_MOD_DockControlAndSignals_v004": ((100, 180), (30, 100), (240, 290)),
    "SM_CA_MW_MOD_ReceivingSaddle_v004": ((280, 340), (350, 410), (110, 170)),
    "SM_CA_MW_MOD_AGVHandoffGuides_v004": ((300, 360), (430, 490), (50, 100)),
    "SM_CA_MW_MOD_IdentityScanner_v004": ((25, 60), (20, 50), (160, 210)),
    "SM_CA_MW_MOD_EntranceDockEnvelope_v004": ((550, 650), (80, 150), (450, 520)),
    "SM_CA_MW_MOD_CraneBayStructure_v004": ((650, 720), (620, 700), (620, 680)),
}

def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

library = unreal.EditorAssetLibrary
asset_tools = unreal.AssetToolsHelpers.get_asset_tools()
unreal.SystemLibrary.execute_console_command(None, "Interchange.FeatureFlags.Import.FBX 0")
tasks = []
hashes = {}
for name in MODULES:
    source_file = SOURCE / f"{name}.fbx"
    if not source_file.exists():
        raise RuntimeError(f"Missing v004 FBX {source_file}")
    hashes[name] = sha(source_file)
    task = unreal.AssetImportTask()
    task.set_editor_properties({
        "filename": str(source_file), "destination_path": DEST,
        "destination_name": name, "automated": True,
        "replace_existing": False, "save": True,
    })
    options = unreal.FbxImportUI()
    options.set_editor_properties({
        "import_mesh": True, "import_as_skeletal": False,
        "import_materials": False, "import_textures": False,
        "mesh_type_to_import": unreal.FBXImportType.FBXIT_STATIC_MESH,
        "automated_import_should_detect_type": False,
    })
    options.static_mesh_import_data.set_editor_properties({
        "combine_meshes": True, "convert_scene": True, "convert_scene_unit": True,
        "generate_lightmap_u_vs": True, "auto_generate_collision": True,
        "remove_degenerates": True, "import_uniform_scale": 1.0,
    })
    task.options = options
    tasks.append(task)

asset_tools.import_asset_tasks(tasks)
unreal.AutomationUtilsBlueprintLibrary.finish_all_asset_compilation()
rows = []
for name, gates in MODULES.items():
    asset_path = f"{DEST}/{name}"
    mesh = library.load_asset(asset_path)
    if not isinstance(mesh, unreal.StaticMesh):
        raise RuntimeError(f"Missing imported v004 mesh {asset_path}")
    size = mesh.get_bounds().box_extent * 2
    actual = (float(size.x), float(size.y), float(size.z))
    for axis, value, gate in zip("XYZ", actual, gates):
        if not gate[0] <= value <= gate[1]:
            raise RuntimeError(f"{name} {axis}={value:.2f} outside {gate}")
    slots = []
    for index, slot in enumerate(mesh.get_editor_property("static_materials")):
        slot_name = str(slot.get_editor_property("material_slot_name"))
        material = library.load_asset(f"{MAT}/{slot_name}_v001")
        if material is None:
            raise RuntimeError(f"Unknown v004 slot {slot_name} on {name}")
        mesh.set_material(index, material)
        slots.append(slot_name)
    library.save_loaded_asset(mesh, only_if_is_dirty=False)
    rows.append({
        "asset": asset_path, "bounds_cm": [round(v, 3) for v in actual],
        "slots": slots, "source_sha256": hashes[name],
        "has_body_setup": mesh.get_editor_property("body_setup") is not None,
    })
OUT.parent.mkdir(parents=True, exist_ok=True)
OUT.write_text(json.dumps({
    "candidate": "InboundCoilDelivery_Candidate_v004",
    "parent": "Modular_v003",
    "status": "PASS_ISOLATED_IMPORT_NOT_PROMOTED",
    "engineering": "TBC", "assets": rows,
}, indent=2), encoding="utf-8")
unreal.log("LINE_BOSS_INBOUND_IMPORT_V506_PASS " + str(OUT))
