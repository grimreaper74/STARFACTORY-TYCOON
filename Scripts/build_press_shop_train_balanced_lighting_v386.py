"""Fresh v383 child with broad, preview-only industrial fill over all four trains."""
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import unreal

ROOT = Path(unreal.Paths.project_dir())
BASE = "/Game/LineBoss/Maps/LB_PressShop_TrainPBRNormalizationCandidate_v383"
BASE_FILE = ROOT / "Content/LineBoss/Maps/LB_PressShop_TrainPBRNormalizationCandidate_v383.umap"
BASE_SHA = "232F29AFE9BE394CAEF06E908D2510D86E4753321BAD3628504643A508225DD2"
MAP = "/Game/LineBoss/Maps/LB_PressShop_TrainBalancedLightingCandidate_v386"
MAP_FILE = ROOT / "Content/LineBoss/Maps/LB_PressShop_TrainBalancedLightingCandidate_v386.umap"
OUT = ROOT / "Saved/Audits/PressShopIntegration/press_shop_train_balanced_lighting_build_v386.json"
TRAIN_ROWS = {"A": -4300.0, "B": -2100.0, "C": 100.0, "D": 2300.0}
X_POSITIONS = (2500.0, 4500.0, 6500.0)

def sha(path):
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest().upper()

library = unreal.EditorAssetLibrary
levels = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
actors = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
if sha(BASE_FILE) != BASE_SHA:
    raise RuntimeError("protected v383 base drift")
if library.does_asset_exist(MAP) or OUT.exists():
    raise RuntimeError("refusing to overwrite preserved v386")
if not levels.new_level_from_template(MAP, BASE):
    raise RuntimeError("fresh v383 child failed")

added = []
for train, y_value in TRAIN_ROWS.items():
    for bay, x_value in enumerate(X_POSITIONS, 1):
        label = f"LB_V386_LIGHT_TRAIN_{train}_BROAD_FILL_{bay:02d}"
        light = actors.spawn_actor_from_class(unreal.RectLight, unreal.Vector(x_value, y_value, 1125.0), unreal.Rotator(-90.0, 0.0, 0.0))
        if light is None:
            raise RuntimeError(f"could not spawn {label}")
        light.set_actor_label(label)
        component = light.get_component_by_class(unreal.RectLightComponent)
        component.set_mobility(unreal.ComponentMobility.MOVABLE)
        component.set_editor_properties({
            "intensity": 165.0,
            "attenuation_radius": 1350.0,
            "source_width": 900.0,
            "source_height": 480.0,
            "light_color": unreal.Color(214, 224, 230, 255),
            "cast_shadows": False,
        })
        light.tags = [
            unreal.Name(f"LB.Lighting.IndustrialLED.Train{train}.BroadFill"),
            unreal.Name("LB.Lighting.PreviewOnly.NoLuxAuthority"),
            unreal.Name("LB.Asset.Candidate.v386"),
            unreal.Name("LB.Asset.CandidateNotPromoted"),
        ]
        added.append({"label": label, "train": train, "location_cm": [x_value, y_value, 1125.0], "intensity_preview_only": 165.0})

train_counts = {key: sum(1 for actor in actors.get_all_level_actors() if f"LB.PressTrain.Installed.TRAIN_{key}" in {str(tag) for tag in actor.tags}) for key in "ABCD"}
failures = []
if len(added) != 12:
    failures.append(f"expected 12 fills, added {len(added)}")
if train_counts != {"A": 338, "B": 338, "C": 338, "D": 338}:
    failures.append(f"train actor contract changed: {train_counts}")
if not levels.save_current_level():
    failures.append("could not save v386")
if sha(BASE_FILE) != BASE_SHA:
    failures.append("protected v383 changed")

payload = {
    "$schema": "cairnwell/audit/press-shop-train-balanced-lighting-build-v386/v1",
    "generated_utc": datetime.now(timezone.utc).isoformat(),
    "status": "PASS__FOUR_TRAIN_BROAD_FILL_CANDIDATE__FRESH_VISUAL_AND_RUNTIME_GATES_REQUIRED__NOT_PROMOTED" if not failures else "FAIL__V386_NOT_A_PARENT",
    "base": BASE,
    "base_sha256": BASE_SHA,
    "map": MAP,
    "map_sha256": sha(MAP_FILE) if MAP_FILE.exists() else None,
    "added_preview_only_lights": added,
    "train_actor_counts": train_counts,
    "unchanged_contracts": ["materials", "geometry", "transforms", "collision", "navigation", "runtime authority", "production state", "save authority"],
    "promotion_authorized": False,
    "failures": failures,
}
OUT.parent.mkdir(parents=True, exist_ok=True)
OUT.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
print(json.dumps(payload, indent=2))
if failures:
    raise RuntimeError("; ".join(failures))
unreal.SystemLibrary.quit_editor()
