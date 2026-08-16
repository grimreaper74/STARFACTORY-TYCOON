"""Import original PR-005 WAV candidates and verify their technical contract."""

import json
from pathlib import Path

import unreal


SOURCE = Path(unreal.Paths.project_dir()) / "SourceAssets/Audio/PR005/Candidate_v001"
MANIFEST_PATH = SOURCE / "audio_manifest_v001.json"
DESTINATION = "/Game/LineBoss/Stations/Press/PR005/Candidate_v001/Audio"
AUDIT = Path(unreal.Paths.project_saved_dir()) / "Audits/pr005_audio_import_v001.json"

manifest = json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))
tools = unreal.AssetToolsHelpers.get_asset_tools()
tasks = []
for record in manifest["assets"]:
    source = SOURCE / record["file"]
    if not source.exists():
        raise RuntimeError(f"Missing PR-005 source audio {source}")
    task = unreal.AssetImportTask()
    task.set_editor_properties({
        "filename": str(source),
        "destination_path": DESTINATION,
        "destination_name": source.stem,
        "automated": True,
        "replace_existing": True,
        "save": True,
    })
    tasks.append(task)
tools.import_asset_tasks(tasks)

records = []
errors = []
by_name = {Path(value["file"]).stem: value for value in manifest["assets"]}
for name, expected in by_name.items():
    path = f"{DESTINATION}/{name}.{name}"
    asset = unreal.load_asset(path)
    if not isinstance(asset, unreal.SoundWave):
        errors.append(f"missing SoundWave {path}")
        continue
    duration = float(asset.get_editor_property("duration"))
    channels = int(asset.get_editor_property("num_channels"))
    sample_rate = int(asset.get_editor_property("sample_rate"))
    if abs(duration - float(expected["duration_seconds"])) > 0.02:
        errors.append(f"duration mismatch {name}: {duration}")
    if channels != 2:
        errors.append(f"channel mismatch {name}: {channels}")
    if sample_rate != 48_000:
        errors.append(f"sample-rate mismatch {name}: {sample_rate}")
    records.append({
        "asset": path,
        "duration_seconds": duration,
        "channels": channels,
        "sample_rate": sample_rate,
        "loop_candidate": bool(expected["loop"]),
        "status": "CANDIDATE_NOT_PROMOTED",
    })

AUDIT.parent.mkdir(parents=True, exist_ok=True)
AUDIT.write_text(json.dumps({"errors": errors, "assets": records}, indent=2), encoding="utf-8")
if errors:
    raise RuntimeError("LINE_BOSS_PR005_AUDIO_IMPORT_FAIL " + "; ".join(errors))
unreal.log(f"LINE_BOSS_PR005_AUDIO_IMPORT_PASS assets={len(records)} output={AUDIT}")
