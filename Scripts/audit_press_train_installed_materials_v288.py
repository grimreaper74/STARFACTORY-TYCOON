"""Read-only material inventory for all installed press trains in v288."""

import hashlib
import json
from collections import Counter
from pathlib import Path

import unreal


MAP = "/Game/LineBoss/Maps/LB_PressShop_PlayableManagementCandidate_v288"
ROOT = Path(unreal.Paths.project_dir())
MAP_FILE = ROOT / "Content/LineBoss/Maps/LB_PressShop_PlayableManagementCandidate_v288.umap"
OUT = ROOT / "Saved/Audits/PressShopIntegration/press_train_installed_materials_v288.json"


def sha256(path):
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest().upper()


before = sha256(MAP_FILE)
levels = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
actors_api = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
if not levels.load_level(MAP):
    raise RuntimeError(MAP)

usage = Counter()
per_train = {key: Counter() for key in "ABCD"}
train_actor_counts = Counter()
samples = {}
for actor in actors_api.get_all_level_actors():
    tags = {str(tag) for tag in actor.tags}
    train_tag = next((tag for tag in tags if tag.startswith("LB.PressTrain.Installed.TRAIN_")), None)
    if train_tag is None:
        continue
    train_id = train_tag.rsplit("_", 1)[-1]
    train_actor_counts[train_id] += 1
    component = actor.get_component_by_class(unreal.StaticMeshComponent)
    if component is None or component.static_mesh is None:
        continue
    for index in range(component.get_num_materials()):
        material = component.get_material(index)
        path = material.get_path_name() if material else "NONE"
        usage[path] += 1
        if train_id in per_train:
            per_train[train_id][path] += 1
        samples.setdefault(path, []).append(actor.get_actor_label())

after = sha256(MAP_FILE)
payload = {
    "$schema": "cairnwell/audit/press-train-installed-materials-v288/v1",
    "map": MAP,
    "read_only": True,
    "map_sha256_before": before,
    "map_sha256_after": after,
    "map_unchanged": before == after,
    "train_actor_counts": dict(train_actor_counts),
    "material_slot_usage": dict(usage.most_common()),
    "material_slot_usage_by_train": {
        train: dict(counter.most_common()) for train, counter in per_train.items()
    },
    "sample_actors_by_material": {key: value[:8] for key, value in samples.items()},
}
OUT.parent.mkdir(parents=True, exist_ok=True)
OUT.write_text(json.dumps(payload, indent=2), encoding="utf-8")
print(json.dumps(payload, indent=2))
unreal.SystemLibrary.quit_editor()
