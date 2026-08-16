"""Reversible seven-year mothballed lighting and floor dressing pass."""

import json
from pathlib import Path
import unreal

MAP = "/Game/LineBoss/Maps/LB_PressShop_MothballedCandidate_v004"
AUDIT = Path(unreal.Paths.project_saved_dir()) / "Audits/press_shop_mothballed_v004.json"

levels = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
actors = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
levels.load_level(MAP)

light_changes = []
for actor in actors.get_all_level_actors():
    component = None
    factor = 1.0
    if isinstance(actor, unreal.DirectionalLight):
        component = actor.get_editor_property("directional_light_component")
        factor = 0.28
    elif isinstance(actor, unreal.PointLight):
        component = actor.get_editor_property("point_light_component")
        factor = 0.18
    elif isinstance(actor, unreal.SpotLight):
        component = actor.get_editor_property("spot_light_component")
        factor = 0.22
    elif isinstance(actor, unreal.RectLight):
        component = actor.get_editor_property("rect_light_component")
        factor = 0.16
    if component is not None:
        before = float(component.get_editor_property("intensity"))
        component.set_editor_property("intensity", max(before * factor, 0.02))
        light_changes.append({"actor": actor.get_actor_label(), "before": before, "after": max(before * factor, 0.02)})

cylinder = unreal.load_asset("/Engine/BasicShapes/Cylinder.Cylinder")
dark = unreal.load_asset("/Game/LineBoss/Materials/M_LB_ShellCharcoal.M_LB_ShellCharcoal")
concrete = unreal.load_asset("/Game/LineBoss/Materials/M_LB_FactoryConcrete.M_LB_FactoryConcrete")
if cylinder is None or dark is None:
    raise RuntimeError("Missing engine cylinder or mothballed dressing material")

# Broad, low-profile accumulated grime and old oil staining. Every actor is removable by prefix.
patches = (
    ("PR001_OldOil", -9200, 2600, 1150, 420, 8),
    ("PR002_HydraulicStain", -7200, 1800, 760, 310, -14),
    ("PR003_TrackGrimeA", -4700, 2500, 1250, 210, 3),
    ("PR003_TrackGrimeB", -3900, 250, 980, 180, -5),
    ("PR004_ServiceOil", -5050, -2000, 620, 260, 18),
    ("PR005_DriveStain", -1200, -850, 720, 260, -11),
    ("TrainA_PitGrime", 2500, 3000, 1550, 170, 0),
    ("TrainB_PitGrime", 2500, 900, 1500, 170, 0),
    ("TrainC_PitGrime", 2500, -1200, 1550, 170, 0),
    ("TrainD_PitGrime", 2500, -3300, 1500, 170, 0),
    ("SouthRoad_OldLeak", 5100, -5000, 650, 240, 21),
)
created = []
for name, x, y, sx, sy, yaw in patches:
    actor = actors.spawn_actor_from_class(unreal.StaticMeshActor, unreal.Vector(x, y, 1.2), unreal.Rotator(0, yaw, 0))
    actor.set_actor_label(f"LB_MOTH_V004_{name}")
    component = actor.get_editor_property("static_mesh_component")
    component.set_editor_property("static_mesh", cylinder)
    component.set_material(0, dark if "Oil" in name or "Stain" in name or "Leak" in name else concrete)
    actor.set_actor_scale3d(unreal.Vector(sx / 100.0, sy / 100.0, 0.012))
    created.append(actor.get_actor_label())

# Local emergency/service pools keep the shell readable without implying restored production lighting.
for index, location in enumerate((unreal.Vector(-9600, 4200, 450), unreal.Vector(-5050, -2000, 520), unreal.Vector(6500, -4200, 450))):
    light = actors.spawn_actor_from_class(unreal.PointLight, location, unreal.Rotator())
    light.set_actor_label(f"LB_MOTH_V004_EmergencyPool_{index+1:02d}")
    component = light.get_editor_property("point_light_component")
    component.set_editor_property("intensity", 420.0)
    component.set_editor_property("attenuation_radius", 1350.0)
    component.set_editor_property("light_color", unreal.Color(255, 150, 70, 255))
    created.append(light.get_actor_label())

if not levels.save_current_level():
    raise RuntimeError("Could not save mothballed v004 map")
AUDIT.parent.mkdir(parents=True, exist_ok=True)
AUDIT.write_text(json.dumps({"map": MAP, "status": "CANDIDATE_NOT_PROMOTED", "light_changes": light_changes, "dressing_actors": created}, indent=2), encoding="utf-8")
unreal.log(f"LINE_BOSS_PRESS_SHOP_V004_DRESS_PASS actors={len(created)} lights={len(light_changes)}")

