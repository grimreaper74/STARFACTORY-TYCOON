"""edit_spacecraft_environment_v005.py - exposure balance. The Meshy
textures are genuinely dark-albedo (graphite-heavy), so at 10 lux they
read near-black while the constant light-grey floor reads bright. Raise
the key and fill so the machines carry the frame, and hand the floor
material the darker end of the range (v002 material's constants are
edited in place - it is a script-owned asset).

Run headless (editor closed):
  UnrealEditor-Cmd.exe <proj> -Unattended ... -ExecutePythonScript="<this>"
"""

import unreal

MAP_PATH = ("/Game/LineBoss/Candidates/Spacecraft/SpacecraftFactory_v001"
            "/Maps/LB_SpacecraftFactory_v001")
FLOOR_MAT = ("/Game/LineBoss/Candidates/Spacecraft/StationMeshes_v001"
             "/Materials/M_LB_FactoryFloor_v002")

les = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
if not les.load_level(MAP_PATH):
    raise RuntimeError("FAIL CLOSED: could not load " + MAP_PATH)

actor_sub = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
done = 0
for actor in actor_sub.get_all_level_actors():
    if isinstance(actor, unreal.DirectionalLight):
        comp = actor.get_component_by_class(
            unreal.DirectionalLightComponent)
        comp.set_editor_property("intensity", 22.0)
        done += 1
        unreal.log("SUN raised to 22 lux")
    elif isinstance(actor, unreal.SkyLight):
        comp = actor.get_component_by_class(unreal.SkyLightComponent)
        comp.set_editor_property("intensity", 6.0)
        done += 1
        unreal.log("SKYLIGHT fill raised to 6.0")
if done < 2:
    raise RuntimeError("FAIL CLOSED: lighting actors missing")
if not les.save_current_level():
    raise RuntimeError("FAIL CLOSED: could not save " + MAP_PATH)

mat = unreal.load_asset(FLOOR_MAT)
if mat is None:
    raise RuntimeError("FAIL CLOSED: floor material missing")
mel = unreal.MaterialEditingLibrary
lib = unreal.EditorAssetLibrary
changed = 0
for expr in mat.get_editor_property("expressions") \
        if hasattr(mat, "get_editor_property") else []:
    pass
# Constant3Vector values are baked in the node graph; walk and rewrite.
try:
    exprs = unreal.MaterialEditingLibrary.get_material_expressions(mat)
except Exception:
    exprs = []
for expr in exprs:
    if isinstance(expr, unreal.MaterialExpressionConstant3Vector):
        value = expr.get_editor_property("constant")
        if value.r > 0.45:  # the light panel tone
            expr.set_editor_property("constant",
                                     unreal.LinearColor(0.30, 0.31, 0.33))
            changed += 1
        elif value.r > 0.3:  # the grid line tone
            expr.set_editor_property("constant",
                                     unreal.LinearColor(0.20, 0.21, 0.23))
            changed += 1
if changed > 0:
    mel.recompile_material(mat)
    lib.save_asset(FLOOR_MAT)
unreal.log("ENVIRONMENT v005 DONE: exposure rebalanced, floor tones %d"
           % changed)
