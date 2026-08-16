"""Fresh isolated installed-cell visual successor using proven v511 geometry."""
from pathlib import Path
import unreal

source = (Path(__file__).parent / "build_inbound_operational_readability_v511.py").read_text(encoding="utf-8")
source = source.replace("OperationalReadability_v511", "InstalledCell_v512")
source = source.replace("LB_INBOUND_V011_", "LB_INBOUND_V012_")
source = source.replace("V511", "V512")
source = source.replace("unreal.Vector(2700, -2100, 1325)", "unreal.Vector(2550, -2350, 1280)")
source = source.replace("unreal.Vector(160, 260, 180)", "unreal.Vector(120, 300, 210)")
exec(compile(source, str(Path(__file__)), "exec"), globals(), globals())

library = unreal.EditorAssetLibrary
actors = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
levels = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
wrap = library.load_asset("/Game/LineBoss/Candidates/PressShop/PackagedCoilSurface_v232/Materials/MI_CA_MW_PaleSilverProtectiveWrap_v232")
coil_mesh = library.load_asset("/Game/LineBoss/IndustrialKit/MaterialHandling/MasterCoil/Candidate_v005/SM_LB_MasterCoil_Candidate_v005")
if wrap is None or not isinstance(coil_mesh, unreal.StaticMesh):
    raise RuntimeError("Missing retained wrapped coil assets")

# Candidate_v035 interface evidence: bore axis Y, load centre +150 cm and 59 cm below hook origin.
carried = actors.spawn_actor_from_class(unreal.StaticMeshActor, unreal.Vector(0, 690, 256), unreal.Rotator())
carried.set_actor_label("LB_INBOUND_V012_CHook_CarriedCoil")
carried.static_mesh_component.set_static_mesh(coil_mesh)
for index in range(carried.static_mesh_component.get_num_materials()):
    carried.static_mesh_component.set_material(index, wrap)
carried.tags = [unreal.Name(v) for v in ("LB.Asset.ValidationOnly", "LB.Asset.CandidateNotPromoted", "LB.Material.Coil", "LB.State.CHookCarried")]

# Lift the review out of crushed blacks while keeping industrial contrast.
for actor in actors.get_all_level_actors():
    if isinstance(actor, unreal.PostProcessVolume):
        settings = actor.settings
        settings.set_editor_property("auto_exposure_bias", -0.25)
        actor.settings = settings

def rect(label, location, target, intensity, width, height):
    light = actors.spawn_actor_from_class(unreal.RectLight, unreal.Vector(*location), unreal.Rotator())
    light.set_actor_label(label)
    light.set_actor_rotation(unreal.MathLibrary.find_look_at_rotation(light.get_actor_location(), unreal.Vector(*target)), False)
    light.rect_light_component.set_editor_properties({
        "intensity": intensity,
        "attenuation_radius": 4200.0,
        "source_width": width,
        "source_height": height,
    })
    light.tags = [unreal.Name("LB.Environment.ReviewOnly")]
    return light

rect("LB_INBOUND_V012_Light_DockFill", (1500, -650, 900), (150, -150, 180), 1150.0, 900.0, 500.0)
rect("LB_INBOUND_V012_Light_CraneFill", (-650, 1050, 1050), (0, 650, 300), 1500.0, 1000.0, 650.0)
rect("LB_INBOUND_V012_Light_AGVFill", (1500, 950, 700), (1180, 520, 170), 1050.0, 650.0, 400.0)

unreal.AutomationUtilsBlueprintLibrary.finish_all_asset_compilation()
if not levels.save_current_level():
    raise RuntimeError("Failed saving isolated v512 installed cell")
unreal.log("LINE_BOSS_INBOUND_INSTALLED_CELL_V512_BUILD_PASS")
