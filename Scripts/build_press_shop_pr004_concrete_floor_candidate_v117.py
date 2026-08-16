"""Build isolated v117 to remove the teal/plank-like floor read from v116.

The functional v116 map remains unchanged.  This successor replaces only the
materials on broad floor/zone overlays with the previously proven sealed-
concrete family.  Safety markings and all collision/navigation settings remain
untouched.
"""

import json
from datetime import datetime, timezone
from pathlib import Path

import unreal


ROOT = Path(unreal.Paths.project_dir())
BASE = "/Game/LineBoss/Maps/LB_PressShop_PR004CarryContextCandidate_v116"
MAP = "/Game/LineBoss/Maps/LB_PressShop_PR004ConcreteFloorCandidate_v117"
DEST = "/Game/LineBoss/Candidates/PressShop/PR004ConcreteFloor_v117/Materials"
OUT = ROOT / "Saved/Audits/press_shop_pr004_concrete_floor_build_v117.json"

library = unreal.EditorAssetLibrary
levels = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
actors_api = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)

if library.does_asset_exist(MAP):
    raise RuntimeError(f"refusing to overwrite preserved candidate {MAP}")
if not levels.new_level_from_template(MAP, BASE):
    raise RuntimeError(f"could not create isolated v117 from {BASE}")

sources = {
    "neutral": "/Game/LineBoss/Candidates/PressShop/IntegratedEnvironment_v104/Materials/M_CA_MW_SealedFactoryConcrete_v104",
    "receiving": "/Game/LineBoss/Candidates/PressShop/IntegratedEnvironment_v104/Materials/M_CA_MW_ReceivingConcrete_v104",
    "inspection": "/Game/LineBoss/Candidates/PressShop/IntegratedEnvironment_v104/Materials/M_CA_MW_InspectionConcrete_v104",
    "store": "/Game/LineBoss/Candidates/PressShop/IntegratedEnvironment_v104/Materials/M_CA_MW_CoilStoreConcrete_v104",
    "hold": "/Game/LineBoss/Candidates/PressShop/IntegratedEnvironment_v104/Materials/M_CA_MW_HoldConcrete_v104",
    "walkway": "/Game/LineBoss/Candidates/PressShop/IntegratedEnvironment_v104/Materials/M_CA_MW_ProtectedWalkway_v104",
}
materials = {}
for role, source in sources.items():
    target = f"{DEST}/M_CA_MW_PR004_{role.title()}SealedConcrete_v117"
    if not library.does_asset_exist(source):
        raise RuntimeError(f"missing proven sealed-concrete source material {source}")
    if not library.duplicate_asset(source, target):
        raise RuntimeError(f"could not duplicate {source} to {target}")
    materials[role] = library.load_asset(target)

role_by_label = {
    "LB_PRESS_FinishedFloor": "neutral",
    "LB_INT_FRONT_Floor_PR001": "receiving",
    "LB_INT_FRONT_Floor_PR002": "inspection",
    "LB_INT_FRONT_Floor_PR003": "store",
    "LB_INT_FRONT_Floor_HOLD": "hold",
    "LB_INT_FRONT_PedestrianRoute": "walkway",
    "LB_PR004_V025_OperatorPad": "walkway",
}

changed = []
for actor in actors_api.get_all_level_actors():
    if not isinstance(actor, unreal.StaticMeshActor):
        continue
    label = actor.get_actor_label()
    role = role_by_label.get(label)
    if label.startswith("LB_ZONE_PRESS_"):
        role = "neutral"
    if role is None:
        continue
    component = actor.static_mesh_component
    before = []
    for index in range(max(1, component.get_num_materials())):
        old = component.get_material(index)
        before.append(old.get_path_name() if old else None)
        component.set_material(index, materials[role])
    prior_tags = [str(value) for value in actor.tags]
    actor.tags = [unreal.Name(value) for value in dict.fromkeys(prior_tags + [
        "LB.Asset.Candidate.v117",
        "LB.Environment.Floor.SealedConcrete",
        "LB.Environment.Floor.NoDirectionalPlankTexture",
        f"LB.Environment.Floor.Role.{role}",
    ])]
    changed.append({
        "actor": label,
        "role": role,
        "before": before,
        "after": materials[role].get_path_name(),
        "collision_unchanged": True,
        "navigation_unchanged": True,
    })

failures = []
expected = set(role_by_label) | {
    "LB_ZONE_PRESS_COIL_STORE", "LB_ZONE_PRESS_FRONT_END", "LB_ZONE_PRESS_LOGISTICS",
    "LB_ZONE_PRESS_RECEIVING", "LB_ZONE_PRESS_SUPPORT", "LB_ZONE_PRESS_TOOLING",
    "LB_ZONE_PRESS_TRAINS",
}
changed_labels = {row["actor"] for row in changed}
missing = sorted(expected - changed_labels)
if missing:
    failures.append(f"missing expected floor actors: {missing}")
if len(changed) != len(expected):
    failures.append(f"expected {len(expected)} exact floor bindings, changed {len(changed)}")
if not levels.save_current_level():
    failures.append("could not save isolated v117")
library.save_directory(DEST.rsplit("/", 1)[0], only_if_is_dirty=False, recursive=True)

report = {
    "$schema": "cairnwell/audit/press-shop-pr004-concrete-floor-build-v117/v1",
    "generated_utc": datetime.now(timezone.utc).isoformat(),
    "status": "PASS__ISOLATED_V117_TEAL_PLANK_FLOOR_REMOVED__VISUAL_AND_EXACT_RUNTIME_GATES_REQUIRED__NOT_PROMOTED" if not failures else "FAIL__V117_FLOOR_BUILD__NOT_PROMOTED",
    "source_map": BASE,
    "map": MAP,
    "changed_floor_count": len(changed),
    "changed_floors": sorted(changed, key=lambda row: row["actor"]),
    "safety_marking_geometry_changed": False,
    "collision_or_navigation_changed": False,
    "v116_changed": False,
    "promotion_authorized": False,
    "press_shop_complete": False,
    "failures": failures,
}
OUT.write_text(json.dumps(report, indent=2), encoding="utf-8")
print(json.dumps(report, indent=2))
if failures:
    raise RuntimeError("; ".join(failures))
