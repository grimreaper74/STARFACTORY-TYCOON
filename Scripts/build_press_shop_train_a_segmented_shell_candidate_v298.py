"""Replace only the v015 shell with isolated-v041 v016 in a fresh v295 child."""

import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
import unreal

ROOT = Path(unreal.Paths.project_dir())
BASE = "/Game/LineBoss/Maps/LB_PressShop_TrainAFabricatedShellOperatorFaceCandidate_v295"
MAP = "/Game/LineBoss/Maps/LB_PressShop_TrainASegmentedShellCandidate_v298"
ASSET = "/Game/LineBoss/Candidates/PressTrains/TrainA/FabricatedShell_v041/SM_CA_MW_PTA_PresentationShell_v016"
BASE_FILE = ROOT / "Content/LineBoss/Maps/LB_PressShop_TrainAFabricatedShellOperatorFaceCandidate_v295.umap"
MAP_FILE = ROOT / "Content/LineBoss/Maps/LB_PressShop_TrainASegmentedShellCandidate_v298.umap"
OUT = ROOT / "Saved/Audits/PressShopIntegration/press_shop_train_a_segmented_shell_build_v298.json"
lib = unreal.EditorAssetLibrary
levels = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
api = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)

def sha(path):
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest().upper()

if lib.does_asset_exist(MAP) or OUT.exists():
    raise RuntimeError("refusing to overwrite v298")
mesh = lib.load_asset(ASSET)
if not isinstance(mesh, unreal.StaticMesh):
    raise RuntimeError(ASSET)
base_hash = sha(BASE_FILE)
if not levels.new_level_from_template(MAP, BASE):
    raise RuntimeError("fresh direct-v295 child failed")
actors = api.get_all_level_actors()
shell = next((actor for actor in actors if actor.get_actor_label() == "LB_V295_PTA_FABRICATED_SHELL_V015"), None)
if shell is None:
    raise RuntimeError("v295 shell actor missing")
train_before = [actor for actor in actors if "LB.PressTrain.Installed.TRAIN_A" in {str(tag) for tag in actor.tags}]
component = shell.static_mesh_component
if not component.set_static_mesh(mesh):
    raise RuntimeError("v016 mesh assignment failed")
bindings = []
for index, slot in enumerate(mesh.get_editor_property("static_materials")):
    material = slot.material_interface
    component.set_material(index, material)
    bindings.append({"index": index, "slot": str(slot.material_slot_name), "material": material.get_path_name() if material else None})
shell.set_actor_label("LB_V298_PTA_SEGMENTED_SHELL_V016")
shell.tags = [unreal.Name("LB.Asset.Candidate.v298") if str(tag) == "LB.Asset.Candidate.v295" else tag for tag in shell.tags]
shell.tags = [unreal.Name("LB.PressTrain.PresentationShell.TrainA.v016") if str(tag).startswith("LB.PressTrain.PresentationShell.TrainA") else tag for tag in shell.tags]
component.set_collision_profile_name(unreal.Name("NoCollision"), True)
component.set_collision_enabled(unreal.CollisionEnabled.NO_COLLISION)
component.set_editor_property("generate_overlap_events", False)
component.set_editor_property("can_ever_affect_navigation", False)
origin, extent = shell.get_actor_bounds(False, False)
bounds = {"min_cm": [origin.x-extent.x, origin.y-extent.y, origin.z-extent.z], "max_cm": [origin.x+extent.x, origin.y+extent.y, origin.z+extent.z]}
train_after = [actor for actor in api.get_all_level_actors() if "LB.PressTrain.Installed.TRAIN_A" in {str(tag) for tag in actor.tags}]
failures = []
if len(train_before) != 338 or len(train_after) != 338:
    failures.append(f"installed Train A contract changed {len(train_before)}->{len(train_after)}")
if len(bindings) != 5 or any(row["material"] is None for row in bindings):
    failures.append(f"material binding contract invalid {bindings}")
if str(component.get_collision_profile_name()) != "NoCollision" or component.get_editor_property("can_ever_affect_navigation"):
    failures.append("collision/navigation contract changed")
if not (2000 <= bounds["min_cm"][0] <= 2020 and 5595 <= bounds["max_cm"][0] <= 5620 and -4800 <= bounds["min_cm"][1] <= -4780 and -4710 <= bounds["max_cm"][1] <= -4690 and 0 <= bounds["min_cm"][2] <= 40 and 1060 <= bounds["max_cm"][2] <= 1080):
    failures.append(f"operator-face envelope changed {bounds}")
if not levels.save_current_level():
    failures.append("save failed")
if sha(BASE_FILE) != base_hash:
    failures.append("protected v295 changed")
payload = {
    "$schema": "cairnwell/audit/press-shop-train-a-segmented-shell-build-v298/v1",
    "generated_utc": datetime.now(timezone.utc).isoformat(),
    "status": "PASS__V016_SEGMENTED_SHELL_AT_RETAINED_OPERATOR_FACE__VISUAL_AND_EXACT_RUNTIME_GATES_REQUIRED__NOT_PROMOTED" if not failures else "FAIL__V298_NOT_A_PARENT",
    "base": BASE, "map": MAP, "base_sha256": base_hash,
    "map_sha256": sha(MAP_FILE) if MAP_FILE.exists() else None,
    "shell_asset": ASSET, "shell_world_bounds": bounds,
    "material_bindings": bindings,
    "installed_train_a_actor_count_before": len(train_before),
    "installed_train_a_actor_count_after": len(train_after),
    "shell_collision": "NoCollision", "shell_affects_navigation": False,
    "promotion_authorized": False, "failures": failures,
}
OUT.parent.mkdir(parents=True, exist_ok=True)
OUT.write_text(json.dumps(payload, indent=2), encoding="utf-8")
print(json.dumps(payload, indent=2))
if failures:
    raise RuntimeError("; ".join(failures))
unreal.SystemLibrary.quit_editor()
