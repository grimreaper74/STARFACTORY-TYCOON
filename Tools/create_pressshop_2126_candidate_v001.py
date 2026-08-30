"""Create an empty, candidate-only 2126 Press Shop map.

It deliberately does not duplicate, load, or alter any prior press-shop map.
"""
from pathlib import Path
import json
import unreal

PROJECT = Path(r"C:\Users\greg_\Projects\LineBossCarFactory_Unreal 5.8")
MAP = "/Game/LineBoss/Candidates/PressShop/PressShop2126_v001/Maps/LB_PressShop_2126_Steam_v001"
MAP_FILE = PROJECT / "Content" / "LineBoss" / "Candidates" / "PressShop" / "PressShop2126_v001" / "Maps" / "LB_PressShop_2126_Steam_v001.umap"
REPORT = PROJECT / "Saved" / "Audits" / "PressShopIntegration" / "pressshop_2126_map_creation_v001.json"

if unreal.EditorAssetLibrary.does_asset_exist(MAP) or MAP_FILE.exists():
    raise RuntimeError("PRESSSHOP_2126_CREATE_FAIL: target already exists; refusing to overwrite a candidate map")

MAP_FILE.parent.mkdir(parents=True, exist_ok=True)
if not unreal.EditorLevelLibrary.new_level(MAP):
    raise RuntimeError("PRESSSHOP_2126_CREATE_FAIL: Unreal could not create the new candidate level")

world = unreal.EditorLevelLibrary.get_editor_world()
if world is None or world.get_name() != "LB_PressShop_2126_Steam_v001":
    raise RuntimeError("PRESSSHOP_2126_CREATE_FAIL: new world was not made current")

if not unreal.EditorLevelLibrary.save_current_level():
    raise RuntimeError("PRESSSHOP_2126_CREATE_FAIL: Unreal could not save the empty candidate level")

REPORT.parent.mkdir(parents=True, exist_ok=True)
REPORT.write_text(json.dumps({
    "status": "PASS",
    "map": MAP,
    "purpose": "Fresh 2126 roofless Press Shop candidate; no existing map was cloned or modified.",
}, indent=2), encoding="utf-8")
unreal.log("PRESSSHOP_2126_CREATE_PASS: " + MAP)
