"""Fresh direct-v429 child with explicit, map-owned train build and utility authority."""
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
import unreal

ROOT = Path(unreal.Paths.project_dir())
BASE = "/Game/LineBoss/Maps/LB_PressShop_DynamicTrainIdentityCandidate_v429"
BASE_FILE = ROOT / "Content/LineBoss/Maps/LB_PressShop_DynamicTrainIdentityCandidate_v429.umap"
BASE_SHA = "6A715DDF9EE0AA6C1529103F2DE905E1DDD94C612D1462F899961D049B4414F0"
MAP = "/Game/LineBoss/Maps/LB_PressShop_BuilderAuthorityCandidate_v438"
MAP_FILE = ROOT / "Content/LineBoss/Maps/LB_PressShop_BuilderAuthorityCandidate_v438.umap"
OUT = ROOT / "Saved/Audits/PressShopIntegration/press_shop_builder_authority_build_v438.json"
TRAIN_X = 3850.0
TRAIN_ROWS = {"A": -4300.0, "B": -2100.0, "C": 100.0, "D": 2300.0}


def sha(path):
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1048576), b""):
            digest.update(chunk)
    return digest.hexdigest().upper()


lib = unreal.EditorAssetLibrary
levels = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
actors = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
if sha(BASE_FILE) != BASE_SHA:
    raise RuntimeError("retained v429 hash drift")
if lib.does_asset_exist(MAP) or OUT.exists():
    raise RuntimeError("refusing to overwrite v438")
if not levels.new_level_from_template(MAP, BASE):
    raise RuntimeError("fresh direct-v429 child failed")

authority = actors.spawn_actor_from_class(unreal.LBPressShopBuildAuthority, unreal.Vector(), unreal.Rotator())
if not authority:
    raise RuntimeError("native build authority did not spawn")
authority.set_actor_label("LB_PRESS_SHOP_BUILD_AUTHORITY_V438")
authority.tags = [unreal.Name(v) for v in (
    "LB.FactoryBuilder.Authority",
    "LB.PressShop.BuildBays.A-D",
    "LB.PressShop.Utilities.MapOwned",
    "LB.Asset.Candidate.v438",
    "LB.Asset.CandidateNotPromoted",
)]

bays = []
spines = []
for train, row_y in TRAIN_ROWS.items():
    bay = unreal.LBPressShopBuildBay()
    bay.set_editor_property("bay_id", unreal.Name(f"PRESS_TRAIN_{train}_BAY"))
    bay.set_editor_property("centre", unreal.Vector(TRAIN_X, row_y, 475.0))
    bay.set_editor_property("half_extent", unreal.Vector(2882.5, 750.0, 475.0))
    bays.append(bay)
    spine = unreal.LBPressShopUtilitySpine()
    spine.set_editor_property("spine_id", unreal.Name(f"PRESS_TRAIN_{train}_UTILITY"))
    spine.set_editor_property("start", unreal.Vector(TRAIN_X - 2882.5, row_y, 0.0))
    spine.set_editor_property("end", unreal.Vector(TRAIN_X + 2882.5, row_y, 0.0))
    spine.set_editor_property("maximum_connection_distance_cm", 750.0)
    spines.append(spine)
authority.set_editor_property("build_bays", bays)
authority.set_editor_property("protected_areas", [])
authority.set_editor_property("utility_spines", spines)

failures = []
all_actors = actors.get_all_level_actors()
authorities = [a for a in all_actors if a.get_class().get_name() == "LBPressShopBuildAuthority"]
if len(authorities) != 1:
    failures.append(f"build authority count {len(authorities)}")
train_counts = {}
for train in "ABCD":
    tag = f"LB.PressTrain.Installed.TRAIN_{train}"
    train_counts[train] = sum(tag in {str(t) for t in a.tags} for a in all_actors)
if train_counts != {"A": 338, "B": 338, "C": 338, "D": 338}:
    failures.append(f"train inventory drift {train_counts}")
if failures:
    raise RuntimeError("; ".join(failures))
if not levels.save_current_level():
    raise RuntimeError("v438 save failed")
if sha(BASE_FILE) != BASE_SHA:
    raise RuntimeError("v429 changed during v438 build")

payload = {
    "$schema": "cairnwell/audit/press-shop-builder-authority-build-v438/v1",
    "generated_utc": datetime.now(timezone.utc).isoformat(),
    "status": "PASS__EXACT_A_D_RECONSTRUCTION_BAYS_AND_MAP_OWNED_UTILITIES__PIE_GATES_REQUIRED__NOT_PROMOTED",
    "base": BASE,
    "base_sha256": BASE_SHA,
    "map": MAP,
    "map_sha256": sha(MAP_FILE),
    "authority_count": len(authorities),
    "train_actor_counts": train_counts,
    "train_datums_cm": {train: [TRAIN_X, y, 0.0] for train, y in TRAIN_ROWS.items()},
    "protected_envelope_cm": [5765.0, 1500.0, 950.0],
    "build_policy": "four exact retained reconstruction lanes; complete S01-S07 trains only",
    "utility_policy": "one explicit map-owned spine per retained train lane; 750 cm maximum connection reach",
    "new_capacity_policy": "additional player capacity requires a separately authored and verified factory expansion bay",
    "visual_geometry_changed": False,
    "promotion_authorized": False,
    "failures": failures,
}
OUT.parent.mkdir(parents=True, exist_ok=True)
OUT.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
print(json.dumps(payload, indent=2))
unreal.SystemLibrary.quit_editor()
