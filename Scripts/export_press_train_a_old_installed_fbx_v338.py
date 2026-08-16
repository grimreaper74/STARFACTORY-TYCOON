"""Read-only FBX export of the actual retained v301 installed Train A actors."""
from __future__ import annotations

import hashlib
import json
import os
from datetime import datetime, timezone
from pathlib import Path

import unreal


MAP = "/Game/LineBoss/Maps/LB_PressShop_TrainAWideSpanClearanceCandidate_v301"
TRAIN_TAG = "LB.PressTrain.Installed.TRAIN_A"
TRAIN_PREFIX = "LB_INST_PTA_"
OUT_REL = "SourceAssets/Reference/PressTrains/TrainA/InstalledRetained_v301/FBX/SM_CA_MW_PressTrainA_InstalledRetained_v301.fbx"
AUDIT_REL = "Saved/Audits/PressTrains/press_train_a_installed_retained_export_v338.json"


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest().upper()


def main() -> None:
    project = Path(unreal.Paths.project_dir())
    output = project / OUT_REL
    audit = project / AUDIT_REL
    if output.exists() or audit.exists():
        raise RuntimeError("Refusing to overwrite retained v338 export evidence")
    output.parent.mkdir(parents=True, exist_ok=True)
    audit.parent.mkdir(parents=True, exist_ok=True)

    levels = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
    actors_api = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
    if not levels.load_level(MAP):
        raise RuntimeError(f"Could not load {MAP}")
    world = unreal.EditorLevelLibrary.get_editor_world()
    selected = []
    for actor in actors_api.get_all_level_actors():
        tags = {str(tag) for tag in actor.tags}
        if TRAIN_TAG in tags or actor.get_actor_label().upper().startswith(TRAIN_PREFIX):
            selected.append(actor)
    if not selected:
        raise RuntimeError("No retained Train A actors found")
    actors_api.set_selected_level_actors(selected)

    options = unreal.FbxExportOption()
    options.set_editor_property("ascii", False)
    options.set_editor_property("collision", False)
    options.set_editor_property("level_of_detail", False)
    options.set_editor_property("vertex_color", True)

    task = unreal.AssetExportTask()
    task.set_editor_property("object", world)
    task.set_editor_property("filename", str(output))
    task.set_editor_property("automated", True)
    task.set_editor_property("prompt", False)
    task.set_editor_property("replace_identical", False)
    task.set_editor_property("selected", True)
    task.set_editor_property("options", options)
    if not unreal.Exporter.run_asset_export_task(task) or not output.is_file():
        raise RuntimeError("Selected Train A FBX export failed")

    payload = {
        "$schema": "cairnwell/audit/press-train-a-installed-retained-export-v338/v1",
        "generated_utc": datetime.now(timezone.utc).isoformat(),
        "status": "PASS__READ_ONLY_SELECTED_ACTOR_EXPORT__REFERENCE_ONLY",
        "source_map": MAP,
        "selected_actor_count": len(selected),
        "selected_actor_labels": sorted(actor.get_actor_label() for actor in selected),
        "output_fbx": str(output),
        "output_fbx_sha256": sha256(output),
        "protected_map_saved_or_modified": False,
        "reference_only": True,
        "promotion_authorized": False,
    }
    audit.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    unreal.log(f"LB_TRAIN_A_RETAINED_EXPORT_PASS actors={len(selected)} output={output}")
    if os.environ.get("LB_CAPTURE_EXIT_WHEN_DONE", "0") == "1":
        unreal.SystemLibrary.execute_console_command(world, "QUIT_EDITOR")


if __name__ == "__main__":
    main()
