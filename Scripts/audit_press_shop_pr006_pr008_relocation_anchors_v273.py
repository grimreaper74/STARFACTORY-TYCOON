"""Measure donor-to-v273 transforms from exact common release-art anchors."""
import json
from pathlib import Path
import unreal

ROOT = Path(unreal.Paths.project_dir())
TARGET = "/Game/LineBoss/Maps/LB_PressShop_PlayableManagementCandidate_v273"
SPECS = {
    "PR006": ("/Game/LineBoss/Maps/LB_PressShop_PR006ReleaseArtCandidate_v208", "LB_PR006_V208_PR006_CrownFabricationPack"),
    "PR007": ("/Game/LineBoss/Maps/LB_PressShop_PR007ReleaseArtCandidate_v209", "LB_PR007_V209_PR007_MistExtractionFabricationPack"),
    "PR008": ("/Game/LineBoss/Maps/LB_PressShop_PR008AuthoredAnchorCandidate_v210", "LB_PR008_V210_PR008_ServoFeed_AuthoredAnchorModule"),
}
OUT = ROOT / "Saved/Audits/PressShopIntegration/press_shop_pr006_pr008_relocation_anchors_v273.json"
levels = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
actors_api = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)


def record(actor):
    location = actor.get_actor_location()
    rotation = actor.get_actor_rotation()
    scale = actor.get_actor_scale3d()
    return {"location": [location.x, location.y, location.z],
            "rotation": [rotation.pitch, rotation.yaw, rotation.roll],
            "scale": [scale.x, scale.y, scale.z]}


donor = {}
for family, (map_path, anchor_label) in SPECS.items():
    if not levels.load_level(map_path):
        raise RuntimeError(map_path)
    matches = [actor for actor in actors_api.get_all_level_actors() if actor.get_actor_label() == anchor_label]
    if len(matches) != 1:
        raise RuntimeError(f"donor anchor {family}:{anchor_label} count={len(matches)}")
    donor[family] = record(matches[0])

if not levels.load_level(TARGET):
    raise RuntimeError(TARGET)
target = {}
for family, (_, anchor_label) in SPECS.items():
    matches = [actor for actor in actors_api.get_all_level_actors() if actor.get_actor_label() == anchor_label]
    if len(matches) != 1:
        raise RuntimeError(f"target anchor {family}:{anchor_label} count={len(matches)}")
    target[family] = record(matches[0])

payload = {"target_map": TARGET, "anchors": {family: {
    "label": SPECS[family][1], "donor": donor[family], "target": target[family],
    "translation_delta_cm": [target[family]["location"][i] - donor[family]["location"][i] for i in range(3)],
    "rotation_delta_deg": [target[family]["rotation"][i] - donor[family]["rotation"][i] for i in range(3)],
} for family in SPECS}}
OUT.parent.mkdir(parents=True, exist_ok=True)
OUT.write_text(json.dumps(payload, indent=2), encoding="utf-8")
unreal.SystemLibrary.quit_editor()
