import json
import os
from datetime import datetime, timezone

import unreal


PROJECT_DIR = unreal.Paths.convert_relative_path_to_full(unreal.Paths.project_dir())
OUT_PATH = os.path.join(
    PROJECT_DIR,
    "Saved",
    "Audits",
    "CAD",
    "datasmith_cad_importer_verification_v001.json",
)


def main():
    os.makedirs(os.path.dirname(OUT_PATH), exist_ok=True)
    plugin_names = []
    if hasattr(unreal, "PluginBlueprintLibrary"):
        try:
            plugin_names = list(unreal.PluginBlueprintLibrary.get_enabled_plugin_names())
        except Exception as exc:
            unreal.log_warning("Could not enumerate enabled plugins: {}".format(exc))

    evidence = {
        "schema": "lineboss.datasmith_cad_importer_verification.v1",
        "utc": datetime.now(timezone.utc).isoformat(),
        "project": unreal.Paths.get_project_file_path(),
        "enabled_plugin_names": sorted(str(name) for name in plugin_names),
        "datasmith_cad_importer_enabled": "DatasmithCADImporter" in plugin_names,
        "datasmith_importer_enabled": "DatasmithImporter" in plugin_names,
        "python_datasmith_scene_api_available": hasattr(unreal, "DatasmithSceneElement"),
        "scope": "Editor import capability only; no manufacturer CAD file was imported.",
    }
    evidence["status"] = (
        "PASS"
        if evidence["datasmith_cad_importer_enabled"]
        and evidence["datasmith_importer_enabled"]
        else "HOLD"
    )
    with open(OUT_PATH, "w", encoding="utf-8") as handle:
        json.dump(evidence, handle, indent=2)
        handle.write("\n")
    unreal.log("DATASMITH_CAD_IMPORTER_VERIFY {} {}".format(evidence["status"], OUT_PATH))


main()
