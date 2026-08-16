"""Record Unreal 5.8 Python exposure for production UMG authoring."""

from pathlib import Path
import json
import unreal

names = [
    "WidgetBlueprintFactory", "WidgetBlueprint", "WidgetTree", "UserWidget",
    "BlueprintEditorLibrary", "KismetEditorUtilities", "K2Node_CallFunction",
    "WidgetComponent", "EditorAssetLibrary", "AssetToolsHelpers"
]
report = {"engine": unreal.SystemLibrary.get_engine_version(), "types": {}}
for name in names:
    value = getattr(unreal, name, None)
    report["types"][name] = {
        "available": value is not None,
        "members": sorted(x for x in dir(value) if not x.startswith("__"))[:250] if value is not None else []
    }
out = Path(unreal.Paths.project_saved_dir()) / "Audits/umg_authoring_api_probe_2026-08-02.json"
out.parent.mkdir(parents=True, exist_ok=True)
out.write_text(json.dumps(report, indent=2), encoding="utf-8")
unreal.log(f"LINE_BOSS_UMG_API_PROBE_PASS {out}")
