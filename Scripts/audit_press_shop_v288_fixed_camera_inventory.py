"""Read-only inventory of exact v288 fixed-camera actors."""
import json
from pathlib import Path
import unreal

MAP = "/Game/LineBoss/Maps/LB_PressShop_PlayableManagementCandidate_v288"
OUT = Path(unreal.Paths.project_saved_dir()) / "Audits/PressShopIntegration/press_shop_v288_fixed_camera_inventory.json"
levels = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
actors_api = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
if not levels.load_level(MAP):
    raise RuntimeError(MAP)
cameras = []
for actor in actors_api.get_all_level_actors():
    if isinstance(actor, unreal.CameraActor):
        cameras.append({"label": actor.get_actor_label(), "name": actor.get_name()})
payload = {"map": MAP, "camera_count": len(cameras), "cameras": sorted(cameras, key=lambda item: item["label"])}
OUT.parent.mkdir(parents=True, exist_ok=True)
OUT.write_text(json.dumps(payload, indent=2), encoding="utf-8")
unreal.log(f"LB_V288_CAMERA_INVENTORY::{json.dumps(payload)}")
