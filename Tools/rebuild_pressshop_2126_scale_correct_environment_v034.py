"""Replace the oversized candidate architecture with a scale-correct open bay.

The Meshy presses are about 5.4 m tall, while the earlier candidate back wall
and crane rail were authored at 68 m and 63 m.  Those values flatten every
camera shot.  This candidate-only pass hides that prior environment and adds
one 9 m facade, one 9 m autonomous rail silhouette and six still-approved
B_stylized fixtures at a credible 8.5 m service height.  No roof is created.
"""

import hashlib
import json
from pathlib import Path

import unreal


PROJECT = Path(r"C:\Users\greg_\Projects\LineBossCarFactory_Unreal 5.8")
MAP = "/Game/LineBoss/Candidates/PressShop/PressShop2126_v001/Maps/LB_PressShop_2126_Steam_v001"
PROTECTED = PROJECT / "Content" / "LineBoss" / "Maps" / "LB_PressShop_BuilderAuthorityCandidate_v438.umap"
MATERIAL_ROOT = "/Game/LineBoss/Candidates/PressShop/PressShop2126_v001/Materials"
REPORT = PROJECT / "Saved" / "Audits" / "PressShopIntegration" / "pressshop_2126_scale_correct_environment_v034.json"
TAG = unreal.Name("LB.PressShop.2126.ScaleCorrectEnvironment.v034")
CUBE = "/Engine/BasicShapes/Cube"

HIDE_LABELS = (
    "S00 | warm-white open-air infeed back wall",
    "S00 | Cairnwell-green infeed supervision band",
    "2126 | warm-white press hall back wall | open-air",
    "2126 | Cairnwell-green press hall supervision band",
    "2126 | warm-white outbound back wall | open-air",
    "2126 | Cairnwell-green outbound supervision band",
    "2126 | autonomous overhead rail left endpoint",
    "2126 | autonomous overhead rail right endpoint",
    "2126 | autonomous overhead handling rail | open-air",
    "2126 | autonomous overhead rail carriage | parked",
)
ROBOT_LABELS = (
    "ROBOT | S01 | laser tend robot",
    "ROBOT | S02 | draw quality robot",
    "ROBOT | S04 | pierce handling robot",
    "ROBOT | S06 | vision stack robot",
)
FIXTURES = tuple("2126 | B_stylized 5000K fixture " + str(index) for index in range(1, 7))
FIXTURE_X = (-12500.0, -7500.0, -2500.0, 2500.0, 7500.0, 11500.0)


def sha256(path):
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def hide(actor):
    actor.set_actor_hidden_in_game(True)
    actor.set_is_temporarily_hidden_in_editor(True)
    for component in actor.get_components_by_class(unreal.PrimitiveComponent):
        component.set_visibility(False, True)


def make_box(label, location, dimensions, material, semantic):
    cube = unreal.load_asset(CUBE)
    if not isinstance(cube, unreal.StaticMesh):
        raise RuntimeError("Native architectural cube unavailable")
    actor = unreal.EditorLevelLibrary.spawn_actor_from_class(unreal.StaticMeshActor, unreal.Vector(*location), unreal.Rotator())
    if not isinstance(actor, unreal.StaticMeshActor):
        raise RuntimeError("Could not create " + label)
    actor.set_actor_label(label)
    actor.static_mesh_component.set_static_mesh(cube)
    actor.static_mesh_component.set_world_scale3d(unreal.Vector(dimensions[0] / 100.0, dimensions[1] / 100.0, dimensions[2] / 100.0))
    actor.static_mesh_component.set_material(0, material)
    actor.tags = [TAG, unreal.Name("LB.Architecture.OpenAir"), unreal.Name(semantic)]
    return actor


protected_before = sha256(PROTECTED)
if not unreal.EditorLoadingAndSavingUtils.load_map(MAP):
    raise RuntimeError("Could not load candidate")
actors = {actor.get_actor_label(): actor for actor in unreal.EditorLevelLibrary.get_all_level_actors()}
if any(TAG in actor.tags for actor in actors.values()):
    raise RuntimeError("Scale-correct environment v034 already exists")

hidden = []
for label in HIDE_LABELS:
    actor = actors.get(label)
    if actor is None:
        raise RuntimeError("Expected prior environment actor missing: " + label)
    hide(actor)
    actor.tags = list(actor.tags) + [TAG]
    hidden.append(label)

materials = {}
for name in ("M_LB_PS2126_WarmWhite", "M_LB_PS2126_CairnwellGreen", "M_LB_PS2126_SafetyYellow", "M_LB_PS2126_SteelGrey"):
    value = unreal.load_asset(MATERIAL_ROOT + "/" + name)
    if not isinstance(value, unreal.Material):
        raise RuntimeError("Missing candidate material: " + name)
    materials[name] = value

# A consistent human-scale backdrop: no roof, no forest of columns.
new_architecture = []
for row in (
    ("2126 | scale-correct warm-white process facade", (-1500.0, 1600.0, 450.0), (27000.0, 30.0, 900.0), materials["M_LB_PS2126_WarmWhite"], "LB.Architecture.Backdrop"),
    ("2126 | scale-correct Cairnwell supervision band", (-1500.0, 1575.0, 640.0), (26800.0, 20.0, 230.0), materials["M_LB_PS2126_CairnwellGreen"], "LB.Architecture.Backdrop"),
    ("2126 | scale-correct yellow process datum", (-1500.0, 1550.0, 805.0), (26800.0, 15.0, 24.0), materials["M_LB_PS2126_SafetyYellow"], "LB.Architecture.Backdrop"),
    ("2126 | autonomous rail terminal west | scale-correct", (-12000.0, 900.0, 450.0), (80.0, 90.0, 900.0), materials["M_LB_PS2126_SteelGrey"], "LB.Architecture.OverheadHandling"),
    ("2126 | autonomous rail terminal east | scale-correct", (9000.0, 900.0, 450.0), (80.0, 90.0, 900.0), materials["M_LB_PS2126_SteelGrey"], "LB.Architecture.OverheadHandling"),
    ("2126 | autonomous overhead transfer rail | scale-correct", (-1500.0, 900.0, 860.0), (21100.0, 90.0, 60.0), materials["M_LB_PS2126_SteelGrey"], "LB.Architecture.OverheadHandling"),
    ("2126 | autonomous rail carriage | scale-correct", (-2500.0, 900.0, 780.0), (520.0, 130.0, 120.0), materials["M_LB_PS2126_SafetyYellow"], "LB.Architecture.OverheadHandling"),
):
    new_architecture.append(make_box(*row).get_actor_label())

# The B_stylized luminance/temperature contract remains intact; only fixture
# location moves from the old 14 m blockout elevation to a 8.5 m service rail.
fixture_rows = []
for label, x in zip(FIXTURES, FIXTURE_X):
    actor = actors.get(label)
    if not isinstance(actor, unreal.RectLight):
        raise RuntimeError("B_stylized fixture missing: " + label)
    component = actor.get_component_by_class(unreal.RectLightComponent)
    if component is None or float(component.get_editor_property("intensity")) != 1200.0 or not component.get_editor_property("use_temperature") or float(component.get_editor_property("temperature")) != 5000.0:
        raise RuntimeError("B_stylized invariant changed before relocation: " + label)
    actor.set_actor_location(unreal.Vector(x, 0.0, 850.0), False, False)
    actor.set_actor_rotation(unreal.Rotator(pitch=-90.0, yaw=0.0, roll=0.0), False)
    fixture_rows.append({"label": label, "location_cm": [x, 0.0, 850.0], "lumens": 1200, "kelvin": 5000})

# Repainting at component level preserves the reusable source mesh.  The four
# genuine robot tenders become readable service machines rather than black
# silhouettes; their scale and transform remain untouched.
robots = []
for label in ROBOT_LABELS:
    actor = actors.get(label)
    if not isinstance(actor, unreal.StaticMeshActor):
        raise RuntimeError("Reused robotic tender missing: " + label)
    component = actor.static_mesh_component
    mesh = component.get_editor_property("static_mesh")
    if not isinstance(mesh, unreal.StaticMesh):
        raise RuntimeError("Reused robotic tender lacks mesh: " + label)
    count = component.get_num_materials()
    if count < 1:
        raise RuntimeError("Reused robotic tender lacks material slot: " + label)
    for index in range(count):
        component.set_material(index, materials["M_LB_PS2126_SteelGrey"])
    actor.tags = list(actor.tags) + [TAG, unreal.Name("LB.PressShop.Automation.Repainted")]
    robots.append({"label": label, "asset": mesh.get_path_name(), "material_slots_repainted": count, "transform_unchanged": True})

if not unreal.EditorLevelLibrary.save_current_level():
    raise RuntimeError("Could not save candidate")
protected_after = sha256(PROTECTED)
if protected_before != protected_after:
    raise RuntimeError("Protected v438 changed")
REPORT.parent.mkdir(parents=True, exist_ok=True)
REPORT.write_text(json.dumps({
    "status": "PASS__OVERSIZED_ARCHITECTURE_REPLACED_BY_SCALE_CORRECT_ROOFLESS_ENVIRONMENT",
    "hidden_prior_candidate_architecture": hidden,
    "new_scale_correct_architecture": new_architecture,
    "b_stylized_fixture_invariants": fixture_rows,
    "reused_robot_tenders_component_repaint": robots,
    "new_machine_geometry": False,
    "roof_created": False,
    "protected_v438_sha256_before": protected_before,
    "protected_v438_sha256_after": protected_after,
}, indent=2), encoding="utf-8")
unreal.log("PRESSSHOP_2126_SCALE_CORRECT_ENVIRONMENT_V034_PASS")
