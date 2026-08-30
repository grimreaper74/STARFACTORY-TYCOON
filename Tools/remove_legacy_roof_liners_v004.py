import json
from pathlib import Path
import unreal

# Candidate-only correction: the user's selected direction is an open factory
# bay.  This removes opaque legacy roof-liner components in v004 without
# deleting an actor or changing v551.
EXPECTED_MAP_SUFFIX = "LB_PressShop_SteamOpenBay_v004"
REPORT = Path(r"C:\Users\greg_\Projects\LineBossCarFactory_Unreal 5.8\Saved\Audits\PressShopIntegration\steam_openbay_v004_roofliner_removal.json")
world = unreal.EditorLevelLibrary.get_editor_world()
if world is None or not world.get_path_name().endswith(EXPECTED_MAP_SUFFIX):
    raise RuntimeError("Refusing roof-liner removal outside " + EXPECTED_MAP_SUFFIX)

hidden = []
for actor in unreal.EditorLevelLibrary.get_all_level_actors():
    label = actor.get_actor_label()
    mesh_path = ""
    if isinstance(actor, unreal.StaticMeshActor):
        mesh = actor.static_mesh_component.get_editor_property("static_mesh")
        mesh_path = mesh.get_path_name() if mesh else ""
    if "roofliner" in (label + " " + mesh_path).lower():
        actor.set_actor_hidden_in_game(True)
        actor.tags = list(actor.tags) + [unreal.Name("LB.PressShop.OpenBay.HiddenRoofLinerV004")]
        for component in actor.get_components_by_class(unreal.PrimitiveComponent):
            component.set_visibility(False, True)
        hidden.append({"label": label, "mesh": mesh_path})

if not hidden:
    raise RuntimeError("No opaque legacy roof-liner actors found; refusing a no-op claim")
if not unreal.EditorLevelLibrary.save_current_level():
    raise RuntimeError("Could not save candidate roof-liner correction")
REPORT.parent.mkdir(parents=True, exist_ok=True)
REPORT.write_text(json.dumps({"status": "PASS__V004_LEGACY_ROOF_LINERS_HIDDEN_ONLY", "hidden_in_candidate_not_deleted": hidden}, indent=2) + "\n", encoding="utf-8")
unreal.log("PRESS_SHOP_V004_ROOFLINER_REMOVAL_PASS count={}".format(len(hidden)))
