"""Make the approved architecture master readable from the factory interior."""
import json
import os
from datetime import datetime, timezone

import unreal

ROOT = os.path.normpath(os.path.join(os.path.dirname(__file__), ".."))
MASTER = "/Game/LineBoss/Candidates/Architecture/FactoryEnvelopeKitRuntime_v001/Materials/M_LB_Architecture_Surface_Master_v001"
INSTANCES = [
    "/Game/LineBoss/Candidates/Architecture/FactoryEnvelopeKitRuntime_v001/Materials/MI_LB_Architecture_WarmOffWhite_v001",
    "/Game/LineBoss/Candidates/Architecture/FactoryEnvelopeKitRuntime_v001/Materials/MI_LB_Architecture_Graphite_v001",
]
AUDIT = os.path.join(ROOT, "Saved", "Audits", "Architecture", "factory_envelope_two_sided_v001.json")

master = unreal.EditorAssetLibrary.load_asset(MASTER)
if not isinstance(master, unreal.Material):
    raise RuntimeError("Approved architecture master is missing or is not a Material")

before = bool(master.get_editor_property("two_sided"))
master.set_editor_property("two_sided", True)
unreal.MaterialEditingLibrary.recompile_material(master)
if not unreal.EditorAssetLibrary.save_loaded_asset(master, False):
    raise RuntimeError("Could not save approved architecture master")

reloaded = unreal.EditorAssetLibrary.load_asset(MASTER)
after = bool(reloaded.get_editor_property("two_sided"))
parents = {}
for path in INSTANCES:
    instance = unreal.EditorAssetLibrary.load_asset(path)
    if not isinstance(instance, unreal.MaterialInstanceConstant):
        raise RuntimeError("Required architecture material instance is missing: " + path)
    parent = instance.get_editor_property("parent")
    parents[path] = parent.get_path_name() if parent else ""

if not after or any(parent not in (MASTER, MASTER + ".M_LB_Architecture_Surface_Master_v001")
                    for parent in parents.values()):
    raise RuntimeError("Two-sided architecture material verification failed")

os.makedirs(os.path.dirname(AUDIT), exist_ok=True)
with open(AUDIT, "w", encoding="utf-8") as handle:
    json.dump({
        "generated_utc": datetime.now(timezone.utc).isoformat(),
        "status": "PASS__APPROVED_FACTORY_ENVELOPE_MASTER_TWO_SIDED",
        "master": MASTER,
        "two_sided_before": before,
        "two_sided_after": after,
        "instance_parents": parents,
    }, handle, indent=2)
unreal.log("LINE_BOSS_FACTORY_ENVELOPE_TWO_SIDED_PASS")
