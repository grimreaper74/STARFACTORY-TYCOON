"""Import the placeholder drone rotor loop as a looping Unreal SoundWave.

One-shot, fail-closed lane in the shape of the existing audio intakes:
it refuses to run if the destination already exists, verifies the source
against the manifest sha256 before importing, and writes a receipt.

The wave MUST end up looping. A rotor loop that plays once and stops is
worse than silence - the drone would buzz for four seconds and then fly
in silence, which reads as a bug rather than a placeholder.

Run headless with -ExecutePythonScript.
"""

import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
import unreal

root = Path(unreal.Paths.project_dir())
source_dir = root / "SourceAssets/Candidate/Spacecraft/Audio_v001"
manifest_path = source_dir / "spacecraft_audio_manifest_v001.json"
dest = "/Game/LineBoss/Audio/SFX"
out = root / "Saved/Audits/Spacecraft/spacecraft_drone_rotor_audio_import_v001.json"

manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
library = unreal.EditorAssetLibrary
tools = unreal.AssetToolsHelpers.get_asset_tools()

if out.exists():
    raise RuntimeError(
        "Refusing to rerun: a receipt for v001 already exists. Author v002.")

tasks = []
for row in manifest["assets"]:
    source = source_dir / row["file"]
    if not source.exists():
        raise RuntimeError(f"Missing source WAV: {source}")
    # Provenance is DECLARED AND VERIFIED, not assumed: a source that no
    # longer matches its manifest is a different asset.
    actual = hashlib.sha256(source.read_bytes()).hexdigest().upper()
    if actual != row["sha256"]:
        raise RuntimeError(
            f"{row['file']} does not match its manifest sha256 "
            f"(manifest {row['sha256'][:16]}..., file {actual[:16]}...)")
    if library.does_asset_exist(f"{dest}/{row['name']}"):
        raise RuntimeError(f"Refusing to overwrite {dest}/{row['name']}")
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
    # Read the flag BACK off the saved asset. Setting a property and
    # reporting success is how a silent failure gets a green receipt.
    looping = bool(asset.get_editor_property("looping"))
    if looping != bool(spec["loop"]):
        failures.append(f"{path} did not take looping={spec['loop']}")
    rows.append({
        "asset": asset.get_path_name(),
        "duration_seconds": asset.get_editor_property("duration"),
        "looping": looping,
        "source_sha256": spec["sha256"],
        "provenance": spec["provenance"],
    })

if len(rows) != len(manifest["assets"]):
    failures.append(
        f"expected {len(manifest['assets'])} sounds, found {len(rows)}")

report = {
    "$schema": "lineboss/audit/spacecraft-drone-rotor-audio-import-v001/v1",
    "generated_utc": datetime.now(timezone.utc).isoformat(),
    "status": (
        "PASS__DRONE_ROTOR_PLACEHOLDER_LOOP_IMPORTED__PLACEHOLDER_NOT_PROMOTED"
        if not failures
        else "FAIL_CLOSED__DRONE_ROTOR_AUDIO_IMPORT__NOT_PROMOTED"),
    "source_manifest": manifest_path.relative_to(root).as_posix(),
    "destination": dest,
    "assets": rows,
    "failures": failures,
    "promotion_authorized": False,
}
out.parent.mkdir(parents=True, exist_ok=True)
out.write_text(json.dumps(report, indent=2), encoding="utf-8")
print(json.dumps({"status": report["status"], "assets": len(rows)}, indent=2))
if failures:
    raise RuntimeError("; ".join(failures))
