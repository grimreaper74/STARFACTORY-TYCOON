"""Calibrate only the v015 shell materials in a fresh v293 child."""
import hashlib, json
from datetime import datetime, timezone
from pathlib import Path
import unreal

ROOT = Path(unreal.Paths.project_dir())
BASE = "/Game/LineBoss/Maps/LB_PressShop_TrainAFabricatedShellCandidate_v293"
MAP = "/Game/LineBoss/Maps/LB_PressShop_TrainAFabricatedShellMaterialCandidate_v294"
BASE_FILE = ROOT / "Content/LineBoss/Maps/LB_PressShop_TrainAFabricatedShellCandidate_v293.umap"
MAP_FILE = ROOT / "Content/LineBoss/Maps/LB_PressShop_TrainAFabricatedShellMaterialCandidate_v294.umap"
OUT = ROOT / "Saved/Audits/PressShopIntegration/press_shop_train_a_fabricated_shell_material_build_v294.json"
MAT_DIR = "/Game/LineBoss/Candidates/PressTrains/TrainA/FabricatedShell_v294/Materials"
PALETTE = {
    "green": ("M_CA_MW_PTA_FabricatedGreen_v294", (0.030, 0.120, 0.085), 0.26, 0.55, 0.30),
    "graphite": ("M_CA_MW_PTA_FabricatedGraphite_v294", (0.075, 0.088, 0.098), 0.32, 0.60, 0.28),
    "dark": ("M_CA_MW_PTA_FabricatedDarkSteel_v294", (0.115, 0.130, 0.140), 0.55, 0.48, 0.34),
    "steel": ("M_CA_MW_PTA_FabricatedMachinedSteel_v294", (0.170, 0.190, 0.205), 0.64, 0.44, 0.38),
    "yellow": ("M_CA_MW_PTA_FabricatedSafetyYellow_v294", (0.62, 0.30, 0.010), 0.12, 0.54, 0.28),
}
lib = unreal.EditorAssetLibrary; levels = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem); api = unreal.get_editor_subsystem(unreal.EditorActorSubsystem); mel = unreal.MaterialEditingLibrary; tools = unreal.AssetToolsHelpers.get_asset_tools()
def sha(path):
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024*1024), b""): digest.update(chunk)
    return digest.hexdigest().upper()
def make(spec):
    name, colour, metallic, roughness, specular = spec; path = f"{MAT_DIR}/{name}"
    if lib.does_asset_exist(path): raise RuntimeError(f"refusing to overwrite {path}")
    mat = tools.create_asset(name, MAT_DIR, unreal.Material, unreal.MaterialFactoryNew())
    base = mel.create_material_expression(mat, unreal.MaterialExpressionConstant3Vector, -420, -100); base.set_editor_property("constant", unreal.LinearColor(*colour, 1)); mel.connect_material_property(base, "", unreal.MaterialProperty.MP_BASE_COLOR)
    for value, prop, y in ((metallic, unreal.MaterialProperty.MP_METALLIC, 40), (roughness, unreal.MaterialProperty.MP_ROUGHNESS, 145), (specular, unreal.MaterialProperty.MP_SPECULAR, 250)):
        node = mel.create_material_expression(mat, unreal.MaterialExpressionConstant, -420, y); node.set_editor_property("r", value); mel.connect_material_property(node, "", prop)
    errors = [str(x) for x in mel.recompile_material(mat)]
    if errors: raise RuntimeError(f"compile {path}: {errors}")
    lib.save_loaded_asset(mat, only_if_is_dirty=False); return mat
if lib.does_asset_exist(MAP) or OUT.exists(): raise RuntimeError("refusing to overwrite v294")
base_hash = sha(BASE_FILE)
if not levels.new_level_from_template(MAP, BASE): raise RuntimeError("fresh v293 child failed")
materials = {key: make(spec) for key, spec in PALETTE.items()}
shell = next((a for a in api.get_all_level_actors() if a.get_actor_label() == "LB_V293_PTA_FABRICATED_SHELL_V015"), None)
if shell is None: raise RuntimeError("v293 shell missing")
shell.set_actor_label("LB_V294_PTA_FABRICATED_SHELL_V015")
shell.tags = [unreal.Name("LB.Asset.Candidate.v294") if str(t) == "LB.Asset.Candidate.v293" else t for t in shell.tags]
component = shell.static_mesh_component; bindings = []; failures = []
for index in range(component.get_num_materials()):
    current = component.get_material(index); name = current.get_name().lower() if current else ""
    key = "green" if "green" in name else "yellow" if "yellow" in name else "graphite" if "graphite" in name else "dark" if "dark" in name else "steel" if "steel" in name else None
    if key is None: failures.append(f"unmapped slot {index}:{name}"); continue
    component.set_material(index, materials[key]); bindings.append({"index": index, "source": current.get_path_name(), "replacement": materials[key].get_path_name(), "role": key})
if len(bindings) != 5: failures.append(f"bindings {len(bindings)}/5")
if str(component.get_collision_profile_name()) != "NoCollision" or component.get_editor_property("can_ever_affect_navigation"): failures.append("shell collision/navigation changed")
if not levels.save_current_level(): failures.append("save failed")
if sha(BASE_FILE) != base_hash: failures.append("protected v293 changed")
payload = {"$schema": "cairnwell/audit/press-shop-train-a-fabricated-shell-material-build-v294/v1", "generated_utc": datetime.now(timezone.utc).isoformat(), "status": "PASS__SHELL_ONLY_MATERIAL_CALIBRATION__VISUAL_GATE_REQUIRED__NOT_PROMOTED" if not failures else "FAIL__V294_NOT_A_PARENT", "base": BASE, "map": MAP, "base_sha256": base_hash, "map_sha256": sha(MAP_FILE) if MAP_FILE.exists() else None, "bindings": bindings, "calibrations": PALETTE, "unchanged_contracts": ["geometry", "transform", "installed Train A actors", "collision", "navigation", "runtime", "audio", "save authority", "v288 lineage"], "promotion_authorized": False, "failures": failures}
OUT.parent.mkdir(parents=True, exist_ok=True); OUT.write_text(json.dumps(payload, indent=2), encoding="utf-8"); print(json.dumps(payload, indent=2))
if failures: raise RuntimeError("; ".join(failures))
unreal.SystemLibrary.quit_editor()
