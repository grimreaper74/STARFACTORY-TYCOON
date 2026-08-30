"""Redistribute the six approved fixtures across the complete 2126 flow."""
import hashlib
import json
import math
from pathlib import Path
import unreal

PROJECT = Path(r"C:\Users\greg_\Projects\LineBossCarFactory_Unreal 5.8")
MAP = "/Game/LineBoss/Candidates/PressShop/PressShop2126_FullHall_v001/Maps/LB_PressShop_2126_FullHall_v001"
RECEIPT = PROJECT / "Saved" / "Audits" / "PressShop2126" / "redistribute_bstylized_fixtures_v002_receipt.json"
TAG = unreal.Name("LB.PressShop.2126.BStylizedCoverage.v002")
POSITIONS = (
    (-8500.0, -2800.0, 3000.0),
    (-6500.0, -1800.0, 3000.0),
    (-3500.0, -1800.0, 3000.0),
    (-3500.0, 1200.0, 3000.0),
    (-3500.0, 4200.0, 3000.0),
    (3500.0, 4500.0, 3000.0),
)
PROTECTED = {
    PROJECT / "Content" / "LineBoss" / "Maps" / "LB_PressShop_BuilderAuthorityCandidate_v438.umap": "5029c9d827d9a1d72c12f27ee757c9bc1e47febd5006ce6d7ba319aad2e7fec8",
    PROJECT / "Content" / "LineBoss" / "Candidates" / "PressShop" / "PressShop2126_v002" / "Maps" / "LB_PressShop_2126_Steam_v002.umap": "cc09cf46d33e8a562d97f5a3bc35a5b42c9582d8e4650cf315694ebf340e4aa0",
}


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest().lower()


before = {str(path): digest(path) for path in PROTECTED}
for path, expected in PROTECTED.items():
    if before[str(path)] != expected:
        raise RuntimeError("protected map missing or changed: " + str(path))
if not unreal.EditorLoadingAndSavingUtils.load_map(MAP):
    raise RuntimeError("could not load isolated 2126 candidate")
actors = list(unreal.EditorLevelLibrary.get_all_level_actors())
if any(TAG in actor.tags for actor in actors):
    raise RuntimeError("fixture coverage v002 already applied")
fixtures = sorted(
    [actor for actor in actors if actor.get_actor_label().startswith("2126 LIGHT | B_stylized fixture ")],
    key=lambda actor: actor.get_actor_label())
if len(fixtures) != 6:
    raise RuntimeError("expected exactly six approved fixtures, found %d" % len(fixtures))

rows = []
for actor, position in zip(fixtures, POSITIONS):
    component = actor.get_component_by_class(unreal.RectLightComponent)
    if component is None:
        raise RuntimeError("fixture component missing: " + actor.get_actor_label())
    if not math.isclose(float(component.get_editor_property("intensity")), 1200.0, abs_tol=0.01):
        raise RuntimeError("fixture lumens changed: " + actor.get_actor_label())
    if not component.get_editor_property("use_temperature") or not math.isclose(float(component.get_editor_property("temperature")), 5000.0, abs_tol=0.01):
        raise RuntimeError("fixture temperature changed: " + actor.get_actor_label())
    old = actor.get_actor_location()
    actor.set_actor_location(unreal.Vector(*position), False, False)
    actor.tags = list(actor.tags) + [TAG]
    rows.append({
        "label": actor.get_actor_label(),
        "old_location_cm": [round(old.x, 2), round(old.y, 2), round(old.z, 2)],
        "new_location_cm": list(position),
        "lumens": 1200.0,
        "kelvin": 5000.0,
    })

if not unreal.EditorLoadingAndSavingUtils.save_current_level():
    raise RuntimeError("could not save redistributed fixture coverage")
unreal.EditorLoadingAndSavingUtils.save_dirty_packages(True, True)
after = {str(path): digest(path) for path in PROTECTED}
if after != before:
    raise RuntimeError("protected maps changed during fixture redistribution")
RECEIPT.parent.mkdir(parents=True, exist_ok=True)
RECEIPT.write_text(json.dumps({
    "status": "PASS__2126_B_STYLIZED_FIXTURES_COVER_COMPLETE_FLOW",
    "map": MAP,
    "fixtures": rows,
    "unchanged_contract": {"count": 6, "lumens_each": 1200, "kelvin": 5000, "sun": 0.30, "sky": 0.20, "exposure": -0.50},
    "protected_sha256_before": before,
    "protected_sha256_after": after,
}, indent=2, sort_keys=True) + "\n", encoding="utf-8")
unreal.log("PRESSSHOP_2126_B_STYLIZED_COVERAGE_V002_PASS")
unreal.SystemLibrary.quit_editor()
