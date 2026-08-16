"""Correct v015 shell from train centreline to the retained operator-face datum."""
import hashlib, json
from datetime import datetime, timezone
from pathlib import Path
import unreal
ROOT = Path(unreal.Paths.project_dir())
BASE = "/Game/LineBoss/Maps/LB_PressShop_TrainAFabricatedShellMaterialCandidate_v294"
MAP = "/Game/LineBoss/Maps/LB_PressShop_TrainAFabricatedShellOperatorFaceCandidate_v295"
BASE_FILE = ROOT / "Content/LineBoss/Maps/LB_PressShop_TrainAFabricatedShellMaterialCandidate_v294.umap"
MAP_FILE = ROOT / "Content/LineBoss/Maps/LB_PressShop_TrainAFabricatedShellOperatorFaceCandidate_v295.umap"
OUT = ROOT / "Saved/Audits/PressShopIntegration/press_shop_train_a_fabricated_shell_operator_face_build_v295.json"
CAMERAS = [("LB_V295_CAM_TrainAOperator", (5000, -5600, 650), (4000, -4742, 480), 54), ("LB_V295_CAM_TrainAFabrication", (3500, -5580, 560), (4100, -4742, 470), 49), ("LB_V295_CAM_TrainAOverview", (7000, -5700, 1350), (3800, -4742, 500), 57)]
lib = unreal.EditorAssetLibrary; levels = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem); api = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
def sha(path):
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024*1024), b""): digest.update(chunk)
    return digest.hexdigest().upper()
if lib.does_asset_exist(MAP) or OUT.exists(): raise RuntimeError("refusing to overwrite v295")
base_hash = sha(BASE_FILE)
if not levels.new_level_from_template(MAP, BASE): raise RuntimeError("fresh v294 child failed")
actors = api.get_all_level_actors(); shell = next((a for a in actors if a.get_actor_label() == "LB_V294_PTA_FABRICATED_SHELL_V015"), None)
if shell is None: raise RuntimeError("v294 shell missing")
shell.set_actor_label("LB_V295_PTA_FABRICATED_SHELL_V015"); shell.set_actor_location(unreal.Vector(1600, -5180, 0), False, False); shell.tags = [unreal.Name("LB.Asset.Candidate.v295") if str(t) == "LB.Asset.Candidate.v294" else t for t in shell.tags]
removed = []
for actor in list(api.get_all_level_actors()):
    if actor.get_actor_label().startswith("LB_V293_CAM_TrainA"):
        removed.append(actor.get_actor_label()); api.destroy_actor(actor)
for index, light in enumerate(sorted([a for a in api.get_all_level_actors() if a.get_actor_label().startswith("LB_V293_LIGHT_TrainA_TaskFill_")], key=lambda a: a.get_actor_label())):
    loc = light.get_actor_location(); light.set_actor_location(unreal.Vector(loc.x, -4680, loc.z), False, False); light.set_actor_label(f"LB_V295_LIGHT_TrainA_TaskFill_{index+1:02d}")
cameras = []
for label, location, target, fov in CAMERAS:
    camera = api.spawn_actor_from_class(unreal.CameraActor, unreal.Vector(*location), unreal.Rotator()); camera.set_actor_label(label); camera.set_actor_rotation(unreal.MathLibrary.find_look_at_rotation(camera.get_actor_location(), unreal.Vector(*target)), False); camera.camera_component.set_editor_properties({"field_of_view": float(fov), "aspect_ratio": 16/9, "constrain_aspect_ratio": True}); camera.tags = [unreal.Name("LB.Camera.Validation"), unreal.Name("LB.Camera.Fixed.TrainAShell.v295"), unreal.Name("LB.Asset.Candidate.v295"), unreal.Name("LB.Asset.CandidateNotPromoted")]; cameras.append(label)
origin, extent = shell.get_actor_bounds(False, False); bounds = {"min_cm": [origin.x-extent.x, origin.y-extent.y, origin.z-extent.z], "max_cm": [origin.x+extent.x, origin.y+extent.y, origin.z+extent.z]}
failures = []
if not (-4800 <= bounds["min_cm"][1] <= -4780 and -4710 <= bounds["max_cm"][1] <= -4690): failures.append(f"operator-face Y envelope invalid {bounds}")
if str(shell.static_mesh_component.get_collision_profile_name()) != "NoCollision" or shell.static_mesh_component.get_editor_property("can_ever_affect_navigation"): failures.append("collision/navigation changed")
if not levels.save_current_level(): failures.append("save failed")
if sha(BASE_FILE) != base_hash: failures.append("protected v294 changed")
payload = {"$schema": "cairnwell/audit/press-shop-train-a-fabricated-shell-operator-face-build-v295/v1", "generated_utc": datetime.now(timezone.utc).isoformat(), "status": "PASS__SHELL_AT_RETAINED_OPERATOR_FACE_DATUM__VISUAL_GATE_REQUIRED__NOT_PROMOTED" if not failures else "FAIL__V295_NOT_A_PARENT", "base": BASE, "map": MAP, "base_sha256": base_hash, "map_sha256": sha(MAP_FILE) if MAP_FILE.exists() else None, "shell_actor_location_cm": [1600, -5180, 0], "shell_world_bounds": bounds, "retained_operator_facade_reference_y_cm": -4680, "shell_face_centre_y_cm": origin.y, "removed_superseded_cameras": removed, "added_cameras": cameras, "task_light_y_cm": -4680, "promotion_authorized": False, "failures": failures}
OUT.parent.mkdir(parents=True, exist_ok=True); OUT.write_text(json.dumps(payload, indent=2), encoding="utf-8"); print(json.dumps(payload, indent=2))
if failures: raise RuntimeError("; ".join(failures))
unreal.SystemLibrary.quit_editor()
