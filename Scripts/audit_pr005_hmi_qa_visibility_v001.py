"""Read-only visibility audit for the disposable PR005 HMI QA level."""
import unreal

MAP = "/Game/LineBoss/Developer/Validation/LB_PR005_DetailedHMI_v001"
HMI_LABEL = "PR005_DetailedHMI_Meshy_v001_TexturePreservation"

levels = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
actors = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
if not levels.load_level(MAP):
    raise RuntimeError(MAP)
for actor in actors.get_all_level_actors():
    if actor.get_actor_label() != HMI_LABEL:
        continue
    component = actor.static_mesh_component
    mesh = component.get_editor_property("static_mesh")
    origin, extent = actor.get_actor_bounds(False)
    mesh_bounds = mesh.get_bounds() if mesh else None
    unreal.log(
        "LINE_BOSS_PR005_HMI_QA_VISIBILITY "
        f"actor={actor.get_name()} loc={actor.get_actor_location()} rot={actor.get_actor_rotation()} "
        f"scale={actor.get_actor_scale3d()} hidden={actor.get_editor_property('hidden')} "
        f"visible={component.is_visible()} mesh={mesh.get_path_name() if mesh else 'NONE'} "
        f"actor_bounds_origin={origin} actor_bounds_extent={extent} mesh_bounds={mesh_bounds} "
        f"materials={component.get_materials()}"
    )
    break
else:
    labels = [a.get_actor_label() for a in actors.get_all_level_actors()]
    raise RuntimeError(f"Missing HMI actor; level labels={labels}")
