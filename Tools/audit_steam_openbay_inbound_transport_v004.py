"""Read-only transport audit for the roofless Steam Press Shop candidate.

This is deliberately an inventory only: it neither creates, hides nor saves
anything.  It identifies the retained road-vehicle / coil-handling actors in
v004 so a future-facing guided carrier can be added or substituted only where
the current composition actually needs it.
"""
import json
from pathlib import Path

import unreal


PROJECT = Path(r"C:\\Users\\greg_\\Projects\\LineBossCarFactory_Unreal 5.8")
OUT = PROJECT / "Saved" / "Audits" / "PressShopIntegration" / "steam_openbay_v004_inbound_transport_audit.json"
TERMS = ("lorry", "truck", "vehicle", "agv", "coil", "saddle", "hook", "crane", "dock", "handoff", "inbound")


def text_of(value):
    return str(value) if value is not None else ""


def mesh_path(actor):
    for component in actor.get_components_by_class(unreal.StaticMeshComponent):
        try:
            mesh = component.get_editor_property("static_mesh")
        except Exception:
            mesh = None
        if mesh is not None:
            return mesh.get_path_name()
    return None


records = []
for actor in unreal.EditorLevelLibrary.get_all_level_actors():
    label = actor.get_actor_label()
    tags = [text_of(tag) for tag in actor.tags]
    mesh = mesh_path(actor)
    haystack = " ".join((label, actor.get_name(), mesh or "", " ".join(tags))).lower()
    if not any(term in haystack for term in TERMS):
        continue
    loc = actor.get_actor_location()
    rotation = actor.get_actor_rotation()
    records.append({
        "label": label,
        "object_name": actor.get_name(),
        "class": actor.get_class().get_name(),
        "mesh": mesh,
        "tags": tags,
        "location_cm": [round(loc.x, 2), round(loc.y, 2), round(loc.z, 2)],
        "rotation": [round(rotation.pitch, 2), round(rotation.yaw, 2), round(rotation.roll, 2)],
        "hidden_in_game": bool(actor.get_editor_property("bHidden")),
    })

records.sort(key=lambda record: (record["location_cm"][0], record["location_cm"][1], record["label"]))
payload = {
    "status": "PASS__READ_ONLY_TRANSPORT_AUDIT",
    "map": unreal.EditorLevelLibrary.get_editor_world().get_path_name(),
    "candidate_policy": "No actor was created, hidden, deleted, moved or saved by this audit.",
    "matched_actor_count": len(records),
    "actors": records,
}
OUT.parent.mkdir(parents=True, exist_ok=True)
OUT.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
unreal.log("STEAM_OPENBAY_INBOUND_TRANSPORT_AUDIT=" + json.dumps({"count": len(records), "out": str(OUT)}))
