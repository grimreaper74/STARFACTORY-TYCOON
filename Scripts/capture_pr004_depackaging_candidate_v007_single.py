"""Request one deterministic PR-004 Candidate_v007 screenshot per session."""

from pathlib import Path


source_path = Path(__file__).resolve().with_name("capture_pr004_depackaging_candidate_v004_single.py")
source = source_path.read_text(encoding="utf-8")
source = source.replace("Candidate_v004", "Candidate_v007")
source = source.replace("candidate_v004", "candidate_v007")
source = source.replace("_v004", "_v007")
source = source.replace("V004", "V007")

state_injection = r'''

# Candidate_v007 process-state isolation.  A real cell cannot display intact
# packaging, released packaging and completed waste simultaneously.  The
# screenshot camera chooses one deterministic state without saving it back to
# the map; runtime state logic remains a separate release gate.
def lb_set_visible(actor, value):
    component = actor.get_editor_property("static_mesh_component")
    component.set_editor_properties({"visible": value, "hidden_in_game": not value})


for lb_actor in actors.get_all_level_actors():
    lb_label = lb_actor.get_actor_label()
    if not isinstance(lb_actor, unreal.StaticMeshActor):
        continue
    if "LB_PR004_packaging_v004_" in lb_label:
        # Approved baseline: inbound coils are bare steel.  The inspection
        # evidence view may show transport bands, edge protectors and ID data,
        # but never the obsolete rigid film/paper shell.
        lb_show = "BARE-COIL" in lb_label
        if CAPTURE_ID == "packaging_close":
            lb_show = any(token in lb_label for token in (
                "BARE-COIL", "BAND-0", "PROTECTOR-", "IDENTITY-LABEL", "RFID",
            )) and "TAIL" not in lb_label
        lb_set_visible(lb_actor, lb_show)
    elif "LB_PR004_film_dewrap_v004_" in lb_label:
        # Full film dewrapping is no longer part of the required PR-004
        # baseline.  Keep the imported candidate assets available for a future
        # optional supplier-packaging module, but hide the entire system here.
        lb_set_visible(lb_actor, False)
'''

load_anchor = 'if not levels.load_level(MAP):\n    raise RuntimeError(f"Could not load {MAP}")\n'
if load_anchor not in source:
    raise RuntimeError("Could not inject Candidate_v007 deterministic process state")
source = source.replace(load_anchor, load_anchor + state_injection, 1)
exec(compile(source, str(source_path), "exec"), globals(), globals())
