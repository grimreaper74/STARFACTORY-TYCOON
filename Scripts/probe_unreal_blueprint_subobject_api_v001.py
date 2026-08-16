"""Record the UE 5.8 Blueprint/subobject Python surface before authoring assets."""

import json
from pathlib import Path

import unreal


root = Path(unreal.Paths.project_dir())
names = [
    "BlueprintFactory", "SubobjectDataSubsystem", "SubobjectDataBlueprintFunctionLibrary",
    "AddNewSubobjectParams", "SceneComponent", "StaticMeshComponent", "ChildActorComponent",
    "BlueprintEditorLibrary", "KismetEditorUtilities",
]
payload = {}
for name in names:
    value = getattr(unreal, name, None)
    payload[name] = sorted(item for item in dir(value) if not item.startswith("__")) if value else None
out = root / "Saved/Audits/unreal_blueprint_subobject_api_probe_v001.json"
out.parent.mkdir(parents=True, exist_ok=True)
out.write_text(json.dumps(payload, indent=2), encoding="utf-8")
unreal.log(f"LINE_BOSS_BLUEPRINT_SUBOBJECT_API_PROBE_PASS audit={out}")
unreal.SystemLibrary.quit_editor()
