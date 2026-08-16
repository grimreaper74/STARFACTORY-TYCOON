"""Import the original Train A WAV source set as isolated Unreal SoundWave assets."""

import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
import unreal

root = Path(unreal.Paths.project_dir())
source_dir = root / "SourceAssets/Candidate/PressTrains/TrainA/Audio_v001"
manifest_path = source_dir / "press_train_a_audio_manifest_v001.json"
dest = "/Game/LineBoss/PressTrains/TrainA/Audio/Candidate_v001"
out = root / "Saved/Audits/PressTrains/press_train_a_audio_import_v001.json"
manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
library = unreal.EditorAssetLibrary
tools = unreal.AssetToolsHelpers.get_asset_tools()

if library.does_directory_exist(dest) or out.exists():
    raise RuntimeError("Refusing to overwrite Train A audio Candidate_v001")

tasks = []
for row in manifest["assets"]:
    source = source_dir / row["file"]
    if not source.exists():
        raise RuntimeError(f"Missing source WAV: {source}")
    task = unreal.AssetImportTask()
    task.set_editor_property("filename", str(source))
    task.set_editor_property("destination_path", dest)
    task.set_editor_property("destination_name", row["name"])
    task.set_editor_property("automated", True)
    task.set_editor_property("replace_existing", False)
    task.set_editor_property("save", True)
    tasks.append(task)
tools.import_asset_tasks(tasks)

rows = []
failures = []
for spec, task in zip(manifest["assets"], tasks):
    path = f"{dest}/{spec['name']}"
    asset = library.load_asset(path)
    if asset is None or not isinstance(asset, unreal.SoundWave):
        failures.append(f"missing SoundWave {path}")
        continue
    asset.set_editor_property("looping", bool(spec["loop"]))
    asset.modify()
    library.save_loaded_asset(asset, only_if_is_dirty=False)
    rows.append({
        "asset": asset.get_path_name(), "duration_seconds": asset.get_editor_property("duration"),
        "looping": bool(asset.get_editor_property("looping")),
        "source_sha256": hashlib.sha256((source_dir / spec["file"]).read_bytes()).hexdigest().upper(),
    })

if len(rows) != len(manifest["assets"]):
    failures.append(f"expected {len(manifest['assets'])} imported sounds, found {len(rows)}")
report = {
    "$schema": "cairnwell/audit/press-train-a-audio-import-v001/v1",
    "generated_utc": datetime.now(timezone.utc).isoformat(),
    "status": "PASS__TRAIN_A_ORIGINAL_SPATIAL_AUDIO_ASSETS_IMPORTED__NATIVE_INTEGRATION_REQUIRED__NOT_PROMOTED"
              if not failures else "FAIL__TRAIN_A_AUDIO_IMPORT__NOT_PROMOTED",
    "source_manifest": manifest_path.relative_to(root).as_posix(),
    "destination": dest, "assets": rows, "failures": failures,
    "production_map_changed": False, "promotion_authorized": False,
}
out.parent.mkdir(parents=True, exist_ok=True)
out.write_text(json.dumps(report, indent=2), encoding="utf-8")
print(json.dumps({"status": report["status"], "assets": len(rows)}, indent=2))
if failures:
    raise RuntimeError("; ".join(failures))
