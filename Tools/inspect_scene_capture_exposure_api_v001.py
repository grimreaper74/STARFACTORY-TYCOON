"""Read-only Unreal Python API probe for native scene-capture exposure controls."""
import json
from pathlib import Path
import unreal

out = Path(unreal.Paths.project_saved_dir()) / "Audits" / "PressShopIntegration" / "scene_capture_exposure_api_v001.json"
settings = unreal.PostProcessSettings()
out.parent.mkdir(parents=True, exist_ok=True)
out.write_text(json.dumps({
    "post_process_properties": [name for name in dir(settings) if "exposure" in name.lower()],
    "exposure_enums": [name for name in dir(unreal) if "Exposure" in name],
}, indent=2), encoding="utf-8")
unreal.SystemLibrary.quit_editor()
