"""List overhead structure actors (arches, gantries, beams, roof frames).

The owner reports arches out of position now the lighting no longer
hides them. Buildings are axis-aligned in world space, so any overhead
piece with a yaw far from a multiple of 90, or hanging outside its
shop's wall envelope, is misplaced. Report label, mesh, location, yaw
and z so the fix targets exactly the wrong ones.
"""
import json
import re

import unreal

TARGET = ("/Game/LineBoss/Factory/OneFactory/v001/Maps/"
          "LB_MoorcrossWorks_OneFactory_v001")
OUT = "C:/Temp/lb_overhead_frames.json"
PATTERN = re.compile(r"arch|gantry|beam|roof|frame|truss", re.IGNORECASE)

LEVEL_SUB = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
ACTOR_SUB = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
if not LEVEL_SUB.load_level(TARGET):
    raise RuntimeError("could not load target map")

rows = []
for actor in ACTOR_SUB.get_all_level_actors():
    label = actor.get_actor_label()
    mesh_names = []
    for component in actor.get_components_by_class(
            unreal.StaticMeshComponent):
        mesh = component.get_editor_property("static_mesh")
        if mesh:
            mesh_names.append(mesh.get_name())
    if not PATTERN.search(label) and not any(
            PATTERN.search(m) for m in mesh_names):
        continue
    where = actor.get_actor_location()
    yaw = actor.get_actor_rotation().yaw % 90.0
    off_grid = min(yaw, 90.0 - yaw)
    rows.append({
        "label": label,
        "meshes": sorted(set(mesh_names))[:2],
        "x": round(where.x, 0), "y": round(where.y, 0),
        "z": round(where.z, 0),
        "yaw": round(actor.get_actor_rotation().yaw, 1),
        "off_grid_deg": round(off_grid, 1),
        "tags": [str(t) for t in actor.tags],
    })

rows.sort(key=lambda r: -r["off_grid_deg"])
with open(OUT, "w") as handle:
    json.dump(rows, handle, indent=1)
unreal.log("LINE_BOSS_OVERHEAD_DUMP count={} out={}".format(len(rows), OUT))
