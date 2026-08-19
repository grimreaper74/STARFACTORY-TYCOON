"""Site batch 01: the perimeter fence with two gate openings, per
SITE_PLAN_2026-08-19. Fence rectangle 740 x 400 m centred (0, 500):
x -37000..37000, y -19500..20500. Main gate on the east fence at
y 15200 (opening 24 m); west service gate at y 500 (opening 24 m).

Vendor fence meshes are discovered from the registry and measured, so
spacing always matches the real asset. Idempotent via LB.Site01.
Run with -ExecutePythonScript.
"""
import io
import json

import unreal

TARGET = ("/Game/LineBoss/Factory/OneFactory/v001/Maps/"
          "LB_MoorcrossWorks_OneFactory_v001")
OUT = "C:/Temp/lb_site01.json"
TAG = "LB.Site01"

X_MIN, X_MAX = -37000.0, 37000.0
Y_MIN, Y_MAX = -19500.0, 20500.0
GATES = [
    {"edge": "east", "centre": 15200.0, "half": 1200.0},
    {"edge": "west", "centre": 500.0, "half": 1200.0},
]

registry = unreal.AssetRegistryHelpers.get_asset_registry()
report = {"fence_mesh": None, "gate_meshes": [], "placed": 0, "cleared": 0,
          "gate_leaves": 0}

# Explicit asset choices: the chainlink security fence and the real gate
# leaves. Blind discovery picked SM_Fence04, a 1.1 m barrier rail.
def find_mesh(preferred_names):
    for asset in unreal.EditorAssetLibrary.list_assets("/Game/Meshes",
                                                       recursive=True):
        name = asset.split(".")[-1] if "." in asset else asset.rsplit(
            "/", 1)[-1]
        if name in preferred_names:
            loaded = unreal.load_asset(asset.split(".")[0])
            if isinstance(loaded, unreal.StaticMesh):
                return loaded, name
    return None, None


# Probe the whole fence family and take the tallest panel; a site
# security fence must read ~2.4 m, and the vendor pieces vary.
best = (None, None, 0.0)
for asset in unreal.EditorAssetLibrary.list_assets("/Game/Meshes",
                                                   recursive=True):
    name = asset.split(".")[-1] if "." in asset else asset.rsplit("/", 1)[-1]
    if "fence" not in name.lower():
        continue
    loaded = unreal.load_asset(asset.split(".")[0])
    if not isinstance(loaded, unreal.StaticMesh):
        continue
    box = loaded.get_bounding_box()
    height = box.max.z - box.min.z
    report.setdefault("fence_family", {})[name] = round(height, 1)
    if height > best[2]:
        best = (loaded, name, height)
fence_mesh, fence_name, fence_height = best
# Scale up to security height when even the tallest panel is short.
FENCE_Z_SCALE = 1.0 if fence_height >= 180.0 else max(
    1.0, 240.0 / max(fence_height, 1.0))
report["fence_z_scale"] = round(FENCE_Z_SCALE, 2)
leaf_left, leaf_left_name = find_mesh(("SM_GateLeft02", "SM_GateDoor01"))
leaf_right, leaf_right_name = find_mesh(("SM_GateRight02", "SM_GateDoor01"))
report["fence_mesh"] = fence_name
report["gate_meshes"] = [leaf_left_name, leaf_right_name]
gate_candidates = [m for m in (leaf_left, leaf_right) if m]
if fence_mesh is None:
    with io.open(OUT, "w", encoding="utf-8") as handle:
        handle.write(json.dumps(report))
    raise RuntimeError("no vendor fence mesh found under /Game/Meshes")

bounds = fence_mesh.get_bounding_box()
span = bounds.max - bounds.min
length = max(span.x, span.y)
report["fence_piece_cm"] = [round(span.x, 1), round(span.y, 1),
                            round(span.z, 1)]

LEVEL_SUB = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
ACTOR_SUB = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
if not LEVEL_SUB.load_level(TARGET):
    raise RuntimeError("could not load target map")
w = unreal.EditorLevelLibrary.get_editor_world()
if w is None or TARGET.rsplit("/", 1)[-1] != w.get_name():
    raise RuntimeError("wrong world; use -ExecutePythonScript")
for a in ACTOR_SUB.get_all_level_actors():
    if a and unreal.Name(TAG) in a.tags:
        ACTOR_SUB.destroy_actor(a)
        report["cleared"] += 1


def spawn(mesh, x, y, yaw, label, z_scale=1.0):
    actor = ACTOR_SUB.spawn_actor_from_object(
        mesh, unreal.Vector(x, y, 0.0), unreal.Rotator(0.0, yaw, 0.0))
    if actor is None:
        return None
    if z_scale != 1.0:
        actor.set_actor_scale3d(unreal.Vector(1.0, 1.0, z_scale))
    actor.tags = [unreal.Name(TAG), unreal.Name("LB.Environment.VisualOnly"),
                  unreal.Name("LB.NotProcessWIP")]
    actor.set_actor_label(label)
    return actor


def in_gate(edge, coord):
    for gate in GATES:
        if gate["edge"] == edge and abs(coord - gate["centre"]) < gate["half"]:
            return True
    return False


count = 0
# North and south runs (along X, yaw 0 assumed to run the piece along X).
x = X_MIN + length / 2
while x < X_MAX:
    for y, edge in ((Y_MAX, "north"), (Y_MIN, "south")):
        if not in_gate(edge, x):
            if spawn(fence_mesh, x, y, 0.0, "Site_Fence_{}_{:d}".format(
                    edge, count), FENCE_Z_SCALE):
                count += 1
    x += length
# East and west runs (along Y, yaw 90).
y = Y_MIN + length / 2
while y < Y_MAX:
    for x_, edge in ((X_MAX, "east"), (X_MIN, "west")):
        if not in_gate(edge, y):
            if spawn(fence_mesh, x_, y, 90.0, "Site_Fence_{}_{:d}".format(
                    edge, count), FENCE_Z_SCALE):
                count += 1
    y += length
report["placed"] = count

# A left/right leaf pair at each opening.
if len(gate_candidates) == 2:
    for gate in GATES:
        gx = X_MAX if gate["edge"] == "east" else X_MIN
        pair = ((gate_candidates[0], -1.0, "left"),
                (gate_candidates[1], 1.0, "right"))
        for leaf, side, tag_ in pair:
            if spawn(leaf, gx, gate["centre"] + side * gate["half"] * 0.5,
                     90.0, "Site_GateLeaf_{}_{}".format(gate["edge"], tag_)):
                report["gate_leaves"] += 1

LEVEL_SUB.save_current_level()
with io.open(OUT, "w", encoding="utf-8") as handle:
    handle.write(json.dumps(report, indent=1, sort_keys=True))
unreal.log("LINE_BOSS_SITE01 {}".format(json.dumps(
    {k: report[k] for k in ("fence_mesh", "placed", "gate_leaves")})))
