"""Create a non-overwriting v227 lighting successor from retained playable v226."""

import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path

import unreal


ROOT = Path(unreal.Paths.project_dir())
BASE = "/Game/LineBoss/Maps/LB_PressShop_PlayableManagementCandidate_v226"
MAP = "/Game/LineBoss/Maps/LB_PressShop_PlayableManagementCandidate_v227"
OUT = ROOT / "Saved/Audits/PressShopIntegration/press_shop_playable_management_lighting_build_v227.json"
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
parent_file = ROOT / "Content/LineBoss/Maps/LB_PressShop_PlayableManagementCandidate_v226.umap"
parent_hash_before = sha256(parent_file)
if not levels.new_level_from_template(MAP, BASE):
    raise RuntimeError(f"could not derive {MAP} from {BASE}")

actors = actors_api.get_all_level_actors()
removed = []
for actor in actors:
    label = actor.get_actor_label()
    if label.startswith("LB_WHOLE_V224_LIGHT_TRAIN_"):
        removed.append(label)
        actors_api.destroy_actor(actor)

failures = []
if sorted(removed) != [
        "LB_WHOLE_V224_LIGHT_TRAIN_A", "LB_WHOLE_V224_LIGHT_TRAIN_B",
        "LB_WHOLE_V224_LIGHT_TRAIN_C", "LB_WHOLE_V224_LIGHT_TRAIN_D"]:
    failures.append(f"unexpected inherited train lights {removed}")

added = []
train_rows = {"A": -4300.0, "B": -2600.0, "C": -900.0, "D": 800.0}
for train_id, y_value in train_rows.items():
    for bay_id, x_value in (("WEST", 2500.0), ("EAST", 5200.0)):
        light = actors_api.spawn_actor_from_class(
            unreal.SpotLight,
            unreal.Vector(x_value, y_value, 1550.0),
            unreal.Rotator(pitch=-90.0, yaw=0.0, roll=0.0))
        if light is None:
            failures.append(f"could not spawn Train {train_id} {bay_id} downlight")
            continue
        label = f"LB_WHOLE_V227_LIGHT_TRAIN_{train_id}_{bay_id}"
        light.set_actor_label(label)
        light.spot_light_component.set_editor_properties({
            "intensity": 3200.0,
            "attenuation_radius": 1850.0,
            "inner_cone_angle": 38.0,
            "outer_cone_angle": 67.0,
            "light_color": unreal.Color(224, 234, 242, 255),
            "cast_shadows": False,
        })
        light.tags = [
            unreal.Name("LB.Lighting.IndustrialLED.Downlight"),
            unreal.Name("LB.Lighting.PreviewOnly.NoLuxAuthority"),
            unreal.Name("LB.Integration.WholeShopControlRoom.v227"),
            unreal.Name("LB.Asset.CandidateNotPromoted"),
        ]
        added.append(label)

control = next((actor for actor in actors_api.get_all_level_actors()
                if actor.get_actor_label() == "LB_WHOLE_V224_LIGHT_CONTROL"), None)
if isinstance(control, unreal.PointLight):
    control.point_light_component.set_editor_property("intensity", 900.0)
else:
    failures.append("inherited control-room preview light missing")

levels.save_current_level()
parent_hash_after = sha256(parent_file)
if parent_hash_after != parent_hash_before:
    failures.append("protected v226 parent changed")
map_file = ROOT / "Content/LineBoss/Maps/LB_PressShop_PlayableManagementCandidate_v227.umap"
payload = {
    "$schema": "cairnwell/audit/press-shop-playable-management-lighting-build-v227/v1",
    "generated_utc": datetime.now(timezone.utc).isoformat(),
    "status": "PASS__COLUMN_BLAST_POINT_LIGHTS_REPLACED_WITH_DOWNWARD_TRAIN_BAY_LIGHTING__VISUAL_GATE_REQUIRED__NOT_PROMOTED" if not failures else "FAIL__NOT_PROMOTED",
    "base": BASE,
    "map": MAP,
    "parent_hash_before": parent_hash_before,
    "parent_hash_after": parent_hash_after,
    "map_hash": sha256(map_file) if map_file.exists() else None,
    "removed_train_lights": sorted(removed),
    "added_downlights": added,
    "authority_or_machine_changes": 0,
    "promotion_authorized": False,
    "failures": failures,
}
OUT.parent.mkdir(parents=True, exist_ok=True)
OUT.write_text(json.dumps(payload, indent=2), encoding="utf-8")
if failures:
    raise RuntimeError("; ".join(failures))
unreal.log(f"LB_V227_LIGHT_BUILD::{json.dumps(payload)}")
unreal.SystemLibrary.quit_editor()
