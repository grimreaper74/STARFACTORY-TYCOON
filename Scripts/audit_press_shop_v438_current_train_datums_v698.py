"""Read-only extraction of the latest A-D train datums and envelopes from protected v438."""
from pathlib import Path
from datetime import datetime, timezone
import hashlib
import json
import unreal

ROOT = Path(unreal.Paths.project_dir())
MAP = "/Game/LineBoss/Maps/LB_PressShop_BuilderAuthorityCandidate_v438"
FILE = ROOT / "Content/LineBoss/Maps/LB_PressShop_BuilderAuthorityCandidate_v438.umap"
EXPECTED = "5029C9D827D9A1D72C12F27EE757C9BC1E47FEBD5006CE6D7BA319AAD2E7FEC8"
OUT = ROOT / "Saved/Audits/PressShopIntegration/press_shop_v438_current_train_datums_v698.json"
levels = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
actors_api = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
def sha(): return hashlib.sha256(FILE.read_bytes()).hexdigest().upper()
if OUT.exists(): raise RuntimeError("Refusing to overwrite v698")
if sha() != EXPECTED: raise RuntimeError("Protected v438 hash mismatch before audit")
if not levels.load_level(MAP): raise RuntimeError("Could not load protected v438")

def union(rows):
    lo = [float("inf")] * 3; hi = [float("-inf")] * 3; used = 0
    for actor in rows:
        origin, extent = actor.get_actor_bounds(False, False)
        if max(extent.x, extent.y, extent.z) <= 0: continue
        used += 1
        for i, (o, e) in enumerate(zip(origin.to_tuple(), extent.to_tuple())):
            lo[i] = min(lo[i], o-e); hi[i] = max(hi[i], o+e)
    if not used: return {"bounded_actor_count": 0}
    return {"bounded_actor_count": used, "min_cm": lo, "max_cm": hi,
            "centre_cm": [(a+b)/2 for a,b in zip(lo,hi)], "size_cm": [b-a for a,b in zip(lo,hi)]}

all_actors = actors_api.get_all_level_actors()
payload = {"revision":"v698", "generated_utc":datetime.now(timezone.utc).isoformat(),
           "status":"PASS__READ_ONLY_CURRENT_V438_TRAIN_DATUM_AUDIT", "map":MAP, "trains":{}}
for letter in "ABCD":
    scope = f"LB.PressTrain.Installed.TRAIN_{letter}"
    members = [a for a in all_actors if scope in {str(t) for t in a.tags}]
    authorities = [a for a in members if isinstance(a, unreal.LBPressTrainAStation)]
    large = []
    for actor in members:
        origin, extent = actor.get_actor_bounds(False, False)
        if max(extent.x, extent.y, extent.z) >= 400:
            large.append({"label":actor.get_actor_label(), "class":actor.get_class().get_name(),
                          "location_cm":list(actor.get_actor_location().to_tuple()),
                          "rotation_deg":list(actor.get_actor_rotation().to_tuple()),
                          "bounds_origin_cm":list(origin.to_tuple()), "bounds_extent_cm":list(extent.to_tuple())})
    payload["trains"][letter] = {
        "scope":scope, "actor_count":len(members), "envelope":union(members),
        "authorities":[{"label":a.get_actor_label(), "location_cm":list(a.get_actor_location().to_tuple()),
                        "rotation_deg":list(a.get_actor_rotation().to_tuple())} for a in authorities],
        "large_datum_candidates":large,
    }
centres = {k:v["envelope"].get("centre_cm") for k,v in payload["trains"].items()}
payload["centre_separations_cm"] = {
    f"{a}_{b}":[centres[b][i]-centres[a][i] for i in range(3)]
    for a,b in zip("ABC","BCD") if centres[a] and centres[b]
}
payload["protected_hash_after"] = sha(); payload["protected_map_modified"] = False
if payload["protected_hash_after"] != EXPECTED: raise RuntimeError("Protected v438 changed during read-only audit")
OUT.parent.mkdir(parents=True, exist_ok=True); OUT.write_text(json.dumps(payload,indent=2),encoding="utf-8")
unreal.log("LINE_BOSS_PRESS_SHOP_V438_CURRENT_TRAIN_DATUMS_V698_PASS")
unreal.SystemLibrary.quit_editor()
