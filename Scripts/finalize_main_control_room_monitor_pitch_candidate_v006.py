"""Finish the partial v006 map after resolving inherited v002 actor labels."""

import json
from datetime import datetime, timezone
from pathlib import Path

import unreal


ROOT = Path(unreal.Paths.project_dir())
MAP = "/Game/LineBoss/Maps/LB_MainControlRoom_MonitorPitchCandidate_v006"
DEST = "/Game/LineBoss/Candidates/ControlRoom/MainControlRoom_v006/Meshes"
OUT = ROOT / "Saved/Audits/ControlRoom/main_control_room_monitor_pitch_import_build_v006.json"

library = unreal.EditorAssetLibrary
levels = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
actors_api = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
if not library.does_asset_exist(MAP):
    raise RuntimeError(f"missing partial v006 map: {MAP}")
levels.load_level(MAP)
actors = {actor.get_actor_label(): actor for actor in actors_api.get_all_level_actors()}
failures = []
replaced = []

for category in ("Interaction", "State_Mothballed"):
    actor = actors.get(f"LB_MCR_V002_{category}") or actors.get(f"LB_MCR_V006_{category}")
    mesh = library.load_asset(f"{DEST}/SM_CA_MW_MCR_{category}_v006")
    if actor is None or not isinstance(mesh, unreal.StaticMesh):
        failures.append(f"missing inherited actor or corrected mesh: {category}")
        continue
    actor.static_mesh_component.set_editor_property("static_mesh", mesh)
    actor.set_actor_label(f"LB_MCR_V006_{category}")
    actor.tags = [unreal.Name("LB.ControlRoom.v006"), unreal.Name(f"LB.ControlRoom.Category.{category}"), unreal.Name("LB.Asset.CandidateNotPromoted")]
    replaced.append(category)

# Normalize inherited category labels so fixed-camera audit output is unambiguous.
for actor in actors_api.get_all_level_actors():
    label = actor.get_actor_label()
    if label.startswith("LB_MCR_V002_"):
        actor.set_actor_label(label.replace("V002", "V006"))
    if any(str(tag) in {"LB.ControlRoom.v002", "LB.ControlRoom.v003", "LB.ControlRoom.v004"} for tag in actor.tags):
        actor.tags = [unreal.Name("LB.ControlRoom.v006" if str(tag) in {"LB.ControlRoom.v002", "LB.ControlRoom.v003", "LB.ControlRoom.v004"} else str(tag)) for tag in actor.tags]

levels.save_current_level()
payload = json.loads(OUT.read_text(encoding="utf-8")) if OUT.is_file() else {}
payload.update({
    "generated_utc": datetime.now(timezone.utc).isoformat(),
    "status": "PASS__TWELVE_DEGREE_CONSOLE_MONITOR_SOURCE_IMPORTED__FIXED_CAMERA_VISUAL_GATE_REQUIRED__NOT_PROMOTED" if not failures else "FAIL__CONTROL_ROOM_V006_FINALIZE__NOT_PROMOTED",
    "inherited_actor_label_resolution": "v004 map retained v002 category labels; finalize resolved and normalized them",
    "replaced_categories": sorted(replaced),
    "promotion_authorized": False,
    "gameplay_wired": False,
    "failures": failures,
})
OUT.write_text(json.dumps(payload, indent=2), encoding="utf-8")
print(json.dumps({"status": payload["status"], "failures": failures, "audit": str(OUT)}, indent=2))

