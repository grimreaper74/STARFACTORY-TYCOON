"""Reserve the hall/coil-readability branch at v180 after cross-chat v141 collision."""

import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path

import unreal


ROOT = Path(unreal.Paths.project_dir())
BASE = "/Game/LineBoss/Maps/LB_PressShop_PR003PR004CoilReadabilityCandidate_v141"
MAP = "/Game/LineBoss/Maps/LB_PressShop_PR003PR004CoilReadabilityCandidate_v180"
OUT = ROOT / "Saved/Audits/PressShopIntegration/press_shop_pr003_pr004_coil_readability_rebase_v180.json"
BASE_PACKAGE = ROOT / "Content/LineBoss/Maps/LB_PressShop_PR003PR004CoilReadabilityCandidate_v141.umap"
library = unreal.EditorAssetLibrary
levels = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)


def sha256(path):
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


source_hash_before = sha256(BASE_PACKAGE)
if library.does_asset_exist(MAP):
    raise RuntimeError(f"refusing to overwrite preserved candidate {MAP}")
if not levels.new_level_from_template(MAP, BASE):
    raise RuntimeError(f"could not create {MAP}")
failures = []
if not levels.save_current_level():
    failures.append("could not save v180")
source_hash_after = sha256(BASE_PACKAGE)
if source_hash_after != source_hash_before:
    failures.append("source coil-readability v141 changed")
report = {
    "$schema": "cairnwell/audit/press-shop-pr003-pr004-coil-readability-rebase-v180/v1",
    "generated_utc": datetime.now(timezone.utc).isoformat(),
    "status": "PASS__IDENTICAL_ISOLATED_REBASE_TO_NON_CONFLICTING_V180__REGATES_REQUIRED__NOT_PROMOTED" if not failures else "FAIL__V180_REBASE__NOT_PROMOTED",
    "source_map": BASE,
    "map": MAP,
    "reason": "Cross-chat v141 was independently reserved for LB_PressShop_PR003PR004PoweredCHookCandidate_v141; validator identity must remain unambiguous.",
    "geometry_material_lighting_or_authority_changed": False,
    "protected_source_sha256_before": source_hash_before,
    "protected_source_sha256_after": source_hash_after,
    "promotion_authorized": False,
    "failures": failures,
}
OUT.parent.mkdir(parents=True, exist_ok=True)
OUT.write_text(json.dumps(report, indent=2), encoding="utf-8")
print(json.dumps(report, indent=2))
if failures:
    raise RuntimeError("; ".join(failures))
