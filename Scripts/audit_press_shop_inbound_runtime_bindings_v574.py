"""Read-only inventory of inbound gameplay authorities on exact v570 candidate."""
from pathlib import Path
import json
import unreal

MAP = "/Game/LineBoss/Developer/Validation/LB_PressShop_InboundIntegrationCandidate_v570"
OUT = Path(unreal.Paths.project_saved_dir()) / "Audits/PressShopIntegration/inbound_runtime_bindings_v574.json"

levels = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
actors = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
if not levels.load_level(MAP):
    raise RuntimeError("Could not load v570")

records = []
for actor in actors.get_all_level_actors():
    cls = actor.get_class().get_name()
    if cls not in ("LBFactoryBuildMachine", "LBPressShopStorageZone", "LBFactoryTransportLink",
                   "LBCoilAGVController", "LBInboundDeliveryController", "LBPressShopBuildAuthority"):
        continue
    rec = {
        "label": actor.get_actor_label(),
        "class": cls,
        "location": [actor.get_actor_location().x, actor.get_actor_location().y, actor.get_actor_location().z],
        "tags": sorted(str(tag) for tag in actor.tags),
    }
    for method, key in (("get_machine_id", "machine_id"), ("get_machine_type", "machine_type"),
                        ("get_zone_id", "zone_id"), ("get_zone_type", "zone_type"),
                        ("get_source_port", "source_port"), ("get_target_port", "target_port"),
                        ("get_inbound_dock_id", "inbound_dock_id"),
                        ("get_coil_store_id", "coil_store_id")):
        fn = getattr(actor, method, None)
        if not fn:
            continue
        try:
            value = fn()
            if value is None:
                rec[key] = None
            elif hasattr(value, "get_owner"):
                owner = value.get_owner()
                rec[key] = owner.get_actor_label() if owner else None
            else:
                rec[key] = str(value)
        except Exception as exc:
            rec[key] = "ERROR: " + str(exc)
    records.append(rec)

OUT.parent.mkdir(parents=True, exist_ok=True)
OUT.write_text(json.dumps({"map": MAP, "actors": records}, indent=2), encoding="utf-8")
unreal.log("LINE_BOSS_INBOUND_RUNTIME_BINDINGS_V574_COMPLETE")
