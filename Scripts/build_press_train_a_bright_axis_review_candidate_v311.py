"""Create a bright, geometry-identical review successor from upright Train A v310."""
import hashlib, json
from datetime import datetime, timezone
from pathlib import Path
import unreal

ROOT = Path(unreal.Paths.project_dir())
BASE = "/Game/LineBoss/Maps/LB_PressTrainA_LitAxisReviewCandidate_v310"
MAP = "/Game/LineBoss/Maps/LB_PressTrainA_BrightAxisReviewCandidate_v311"
BASE_FILE = ROOT / "Content/LineBoss/Maps/LB_PressTrainA_LitAxisReviewCandidate_v310.umap"
MAP_FILE = ROOT / "Content/LineBoss/Maps/LB_PressTrainA_BrightAxisReviewCandidate_v311.umap"
BASE_SHA = "956ABE0A32BF0674D137D8F54D1F5BC7258077E4E84C158990990AB7782B3E71"
OUT = ROOT / "Saved/Audits/PressTrains/press_train_a_bright_axis_review_build_v311.json"

def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest().upper()

if sha(BASE_FILE) != BASE_SHA:
    raise RuntimeError("v310 hash drift")
lib = unreal.EditorAssetLibrary
levels = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
api = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
if lib.does_asset_exist(MAP) or OUT.exists():
    raise RuntimeError("refusing to overwrite v311")
if not levels.new_level_from_template(MAP, BASE):
    raise RuntimeError("fresh v310 child failed")

candidate = next((a for a in api.get_all_level_actors()
                  if "LB.PressTrain.TrainA.ModularSource.v037" in {str(t) for t in a.tags}), None)
if candidate is None:
    raise RuntimeError("candidate missing")
origin, extent = candidate.get_actor_bounds(False)

# Broad shadowless task lighting. These actors are review-only and carry no runtime authority.
added = []
for i, x in enumerate((origin.x - 2200, origin.x - 750, origin.x + 750, origin.x + 2200), 1):
    for side, y in (("front", origin.y - 1050), ("rear", origin.y + 1050)):
        light = api.spawn_actor_from_class(unreal.PointLight, unreal.Vector(x, y, origin.z + 760), unreal.Rotator())
        light.set_actor_label(f"LB_V311_BRIGHT_{side.upper()}_{i:02d}")
        light.point_light_component.set_editor_properties({
            "intensity": 240000.0,
            "attenuation_radius": 3400.0,
            "source_radius": 220.0,
            "soft_source_radius": 420.0,
            "cast_shadows": False,
            "light_color": unreal.Color(245, 248, 255, 255),
        })
        added.append(light.get_actor_label())

sky = api.spawn_actor_from_class(unreal.SkyLight, unreal.Vector(origin.x, origin.y, origin.z + 1200), unreal.Rotator())
sky.set_actor_label("LB_V311_SKYLIGHT")
sky.sky_light_component.set_editor_properties({"intensity": 3.0, "cast_shadows": False, "real_time_capture": True})
added.append(sky.get_actor_label())

failures = []
if len(added) != 9:
    failures.append(f"review actor count {len(added)}")
if not levels.save_current_level():
    failures.append("save failed")
if sha(BASE_FILE) != BASE_SHA:
    failures.append("v310 changed")

payload = {
    "$schema": "cairnwell/audit/press-train-a-bright-axis-review-v311/v1",
    "generated_utc": datetime.now(timezone.utc).isoformat(),
    "status": "PASS__UPRIGHT_BRIGHT_REVIEW_READY__NOT_PROMOTED" if not failures else "FAIL__V311_NOT_EVIDENCE",
    "base": BASE,
    "base_sha256": BASE_SHA,
    "map": MAP,
    "map_sha256": sha(MAP_FILE) if MAP_FILE.exists() else None,
    "review_lighting": added,
    "geometry_changed": False,
    "runtime_authority_changed": False,
    "promotion_authorized": False,
    "failures": failures,
}
OUT.parent.mkdir(parents=True, exist_ok=True)
OUT.write_text(json.dumps(payload, indent=2), encoding="utf-8")
print(json.dumps(payload, indent=2))
if failures:
    raise RuntimeError("; ".join(failures))
unreal.SystemLibrary.quit_editor()
