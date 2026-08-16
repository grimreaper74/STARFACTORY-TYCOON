"""Calibrate v225 preview task lights in a fresh immutable child."""

import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path

import unreal


ROOT = Path(unreal.Paths.project_dir())
BASE = "/Game/LineBoss/Maps/LB_PressShop_PlayableManagementCandidate_v225"
MAP = "/Game/LineBoss/Maps/LB_PressShop_PlayableManagementCandidate_v226"
OUT = ROOT / "Saved/Audits/PressShopIntegration/press_shop_playable_management_lighting_build_v226.json"
library = unreal.EditorAssetLibrary
levels = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
actors_api = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)


def sha256(path):
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest().upper()


if library.does_asset_exist(MAP):
    raise RuntimeError(f"refusing to overwrite {MAP}")
parent_file = ROOT / "Content/LineBoss/Maps/LB_PressShop_PlayableManagementCandidate_v225.umap"
parent_hash_before = sha256(parent_file)
if not levels.new_level_from_template(MAP, BASE):
    raise RuntimeError(f"could not derive {MAP} from {BASE}")

targets = {
    "LB_WHOLE_V224_LIGHT_TRAIN_A": 2500.0,
    "LB_WHOLE_V224_LIGHT_TRAIN_B": 2500.0,
    "LB_WHOLE_V224_LIGHT_TRAIN_C": 2500.0,
    "LB_WHOLE_V224_LIGHT_TRAIN_D": 2500.0,
    "LB_WHOLE_V224_LIGHT_CONTROL": 1400.0,
}
changed = []
by_label = {actor.get_actor_label(): actor for actor in actors_api.get_all_level_actors()}
for label, intensity in targets.items():
    actor = by_label.get(label)
    if not isinstance(actor, unreal.PointLight):
        raise RuntimeError(f"missing preview light {label}")
    actor.point_light_component.set_editor_property("intensity", intensity)
    actor.tags = list(actor.tags) + [unreal.Name("LB.Lighting.CalibratedPreview.v226")]
    changed.append({"label": label, "intensity": intensity})

levels.save_current_level()
parent_hash_after = sha256(parent_file)
failures = [] if parent_hash_after == parent_hash_before else ["protected v225 parent changed"]
map_file = ROOT / "Content/LineBoss/Maps/LB_PressShop_PlayableManagementCandidate_v226.umap"
payload = {
    "$schema": "cairnwell/audit/press-shop-playable-management-lighting-build-v226/v1",
    "generated_utc": datetime.now(timezone.utc).isoformat(),
    "status": "PASS__PREVIEW_TASK_LIGHTS_REDUCED__FRESH_VISUAL_GATE_REQUIRED__NOT_PROMOTED" if not failures else "FAIL__NOT_PROMOTED",
    "base": BASE,
    "map": MAP,
    "parent_hash_before": parent_hash_before,
    "parent_hash_after": parent_hash_after,
    "map_hash": sha256(map_file) if map_file.exists() else None,
    "changed_lights": changed,
    "promotion_authorized": False,
    "failures": failures,
}
OUT.parent.mkdir(parents=True, exist_ok=True)
OUT.write_text(json.dumps(payload, indent=2), encoding="utf-8")
if failures:
    raise RuntimeError("; ".join(failures))
unreal.log(f"LB_V226_LIGHT_BUILD::{json.dumps(payload)}")

