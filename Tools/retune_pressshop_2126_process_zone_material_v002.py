"""Retune the candidate-local process-zone material after visual capture QA."""
import hashlib
import json
from pathlib import Path
import unreal

PROJECT = Path(r"C:\Users\greg_\Projects\LineBossCarFactory_Unreal 5.8")
MAP_FILE = PROJECT / "Content" / "LineBoss" / "Candidates" / "PressShop" / "PressShop2126_FullHall_v001" / "Maps" / "LB_PressShop_2126_FullHall_v001.umap"
MAT = "/Game/LineBoss/Candidates/PressShop/PressShop2126_FullHall_v001/Materials/M_CA_MW_2126_ProcessZonePaleGreen_Unlit_v001"
RECEIPT = PROJECT / "Saved" / "Audits" / "PressShop2126" / "process_zone_material_v002_receipt.json"
PROTECTED = {
    PROJECT / "Content" / "LineBoss" / "Maps" / "LB_PressShop_BuilderAuthorityCandidate_v438.umap": "5029c9d827d9a1d72c12f27ee757c9bc1e47febd5006ce6d7ba319aad2e7fec8",
    PROJECT / "Content" / "LineBoss" / "Candidates" / "PressShop" / "PressShop2126_v002" / "Maps" / "LB_PressShop_2126_Steam_v002.umap": "cc09cf46d33e8a562d97f5a3bc35a5b42c9582d8e4650cf315694ebf340e4aa0",
}

def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest().lower()

before = {str(path): digest(path) for path in PROTECTED}
map_before = digest(MAP_FILE)
material = unreal.load_asset(MAT)
if not isinstance(material, unreal.Material):
    raise RuntimeError("candidate-local process-zone material missing")
expressions = list(unreal.MaterialEditingLibrary.get_material_expressions(material))
constants = [expr for expr in expressions if isinstance(expr, unreal.MaterialExpressionConstant3Vector)]
if len(constants) != 1 or len(expressions) != 1:
    raise RuntimeError("process-zone material graph no longer matches the authored one-node contract")

# The v001 value was visually rejected as near-white under B_stylized exposure.
# This lower linear value retains green separation without competing with the
# warm-white machinery cards.
new_linear = [0.055, 0.100, 0.073]
constants[0].set_editor_property("constant", unreal.LinearColor(*new_linear, 1.0))
unreal.MaterialEditingLibrary.recompile_material(material)
if not unreal.EditorAssetLibrary.save_loaded_asset(material, only_if_is_dirty=False):
    raise RuntimeError("retuned process-zone material did not save")

after = {str(path): digest(path) for path in PROTECTED}
if after != before:
    raise RuntimeError("protected maps changed during material-only retune")
if digest(MAP_FILE) != map_before:
    raise RuntimeError("material-only retune unexpectedly changed candidate map")
RECEIPT.parent.mkdir(parents=True, exist_ok=True)
RECEIPT.write_text(json.dumps({
    "status": "PASS__2126_PROCESS_ZONE_MATERIAL_RETUNED_AFTER_VISUAL_QA",
    "material": material.get_path_name(),
    "rejected_v001_linear_rgb": [0.296, 0.418, 0.352],
    "accepted_candidate_v002_linear_rgb": new_linear,
    "candidate_map_changed": False,
    "protected_sha256_before": before,
    "protected_sha256_after": after,
}, indent=2, sort_keys=True) + "\n", encoding="utf-8")
unreal.log("PRESSSHOP_2126_PROCESS_ZONE_MATERIAL_V002_PASS receipt=" + str(RECEIPT))
unreal.SystemLibrary.quit_editor()
