"""Read-only exact-v438 validation of all retained build/utility datums."""
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
import unreal

ROOT = Path(unreal.Paths.project_dir())
MAP = "/Game/LineBoss/Maps/LB_PressShop_BuilderAuthorityCandidate_v438"
MAP_FILE = ROOT / "Content/LineBoss/Maps/LB_PressShop_BuilderAuthorityCandidate_v438.umap"
MAP_SHA = "5029C9D827D9A1D72C12F27EE757C9BC1E47FEBD5006CE6D7BA319AAD2E7FEC8"
OUT = ROOT / "Saved/Audits/PressShopIntegration/press_shop_builder_authority_exact_v441.json"
ROWS = {"A": -4300.0, "B": -2100.0, "C": 100.0, "D": 2300.0}


def sha(path):
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1048576), b""):
            digest.update(chunk)
    return digest.hexdigest().upper()


if sha(MAP_FILE) != MAP_SHA:
    raise RuntimeError("v438 hash drift before read-only authority validation")
unreal.EditorLoadingAndSavingUtils.load_map(MAP)
api = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
authorities = [a for a in api.get_all_level_actors() if a.get_class().get_name() == "LBPressShopBuildAuthority"]
failures = []
results = {}
if len(authorities) != 1:
    failures.append(f"authority count {len(authorities)}")
else:
    authority = authorities[0]
    bays = authority.get_editor_property("build_bays")
    spines = authority.get_editor_property("utility_spines")
    protected = authority.get_editor_property("protected_areas")
    if len(bays) != 4: failures.append(f"bay count {len(bays)}")
    if len(spines) != 4: failures.append(f"utility count {len(spines)}")
    if len(protected) != 0: failures.append(f"unexpected protected area count {len(protected)}")
    for train, y in ROWS.items():
        transform = unreal.Transform(
            location=unreal.Vector(3850.0, y, 0.0),
            rotation=unreal.Rotator(0.0, 90.0, 0.0),
            scale=unreal.Vector(1.0, 1.0, 1.0))
        response = authority.evaluate_train_transform(transform)
        valid, reason = response if isinstance(response, tuple) else (bool(response), "")
        results[train] = {"valid": valid, "reason": str(reason)}
        if not valid: failures.append(f"{train} rejected: {reason}")
    outside = unreal.Transform(
        location=unreal.Vector(9000.0, 5000.0, 0.0),
        rotation=unreal.Rotator(0.0, 90.0, 0.0),
        scale=unreal.Vector(1.0, 1.0, 1.0))
    response = authority.evaluate_train_transform(outside)
    outside_valid, outside_reason = response if isinstance(response, tuple) else (bool(response), "")
    if outside_valid or "OUTSIDE" not in str(outside_reason):
        failures.append(f"outside placement did not fail explicitly: {response}")
    results["OUTSIDE_CONTROL"] = {"valid": outside_valid, "reason": str(outside_reason)}

payload = {
    "$schema": "cairnwell/audit/press-shop-builder-authority-exact-v441/v1",
    "generated_utc": datetime.now(timezone.utc).isoformat(),
    "status": "PASS__EXACT_A_D_BUILD_AND_UTILITY_DATUMS_VALID__OUTSIDE_CONTROL_REJECTED__NOT_PROMOTED" if not failures else "FAIL__V438_AUTHORITY_NOT_RETAINABLE",
    "map": MAP,
    "map_sha256": sha(MAP_FILE),
    "map_saved": False,
    "results": results,
    "failures": failures,
    "promotion_authorized": False,
}
OUT.parent.mkdir(parents=True, exist_ok=True)
OUT.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
print(json.dumps(payload, indent=2))
if failures:
    raise RuntimeError("; ".join(failures))
unreal.SystemLibrary.quit_editor()
