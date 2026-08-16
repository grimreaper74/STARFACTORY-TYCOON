"""Adapt the proven transition/guard assembly to Pro entry-loop candidate v063."""
from pathlib import Path

base = Path(__file__).with_name("build_press_shop_pr008_transition_guard_candidate_v059.py")
code = base.read_text(encoding="utf-8")
replacements = (
    ("SourceAssets/PR008/StripTransition/Candidate_v001", "SourceAssets/PR008/StripTransition/ProEntryLoop_v002"),
    ("pr008_strip_transition_module_manifest_v001.json", "pr008_strip_transition_module_manifest_v002.json"),
    ("/Game/LineBoss/Maps/LB_PressShop_PR008ServoBlankingCandidate_v058", "/Game/LineBoss/Maps/LB_PressShop_PR008ProEnvelopeCandidate_v062"),
    ("/Game/LineBoss/Maps/LB_PressShop_PR008TransitionGuardCandidate_v059", "/Game/LineBoss/Maps/LB_PressShop_PR008ProEntryLoopCandidate_v063"),
    ("/Game/LineBoss/Stations/Press/PR008/StripTransition/Candidate_v001", "/Game/LineBoss/Stations/Press/PR008/StripTransition/ProEntryLoop_v002"),
    ("LB_PR008_V059_", "LB_PR008_V063_"),
    ("press_shop_pr008_transition_guard_candidate_v059.json", "press_shop_pr008_pro_entry_loop_candidate_v063.json"),
    ("LB_PressShop_PR008TransitionGuardCandidate_v059.umap", "LB_PressShop_PR008ProEntryLoopCandidate_v063.umap"),
    ("LB.Asset.Candidate.v059", "LB.Asset.Candidate.v063"),
    ("LB.Camera.Fixed.PR008.v059", "LB.Camera.Fixed.PR008.v063"),
    ("LINE_BOSS_PR008_V059_PREPARE_PASS", "LINE_BOSS_PR008_V063_PREPARE_PASS"),
    ("LINE_BOSS_PR008_V059_BUILD_PASS", "LINE_BOSS_PR008_V063_BUILD_PASS"),
    ("press-shop-pr008-transition-guard-candidate-v059", "press-shop-pr008-pro-entry-loop-candidate-v063"),
    ("vertical_fall_cm\": 2.5", "vertical_fall_cm\": 25.5"),
    ("DIMENSIONED_STRIP_TRANSITION_AND_LOCAL_OPEN_MESH_GUARD_ASSEMBLY_PASS", "PRO_ENTRY_LOOP_AND_LOCAL_OPEN_MESH_GUARD_ASSEMBLY_PASS"),
)
for old, new in replacements:
    code = code.replace(old, new)
exec(compile(code, str(base) + "::pro-entry-loop-v063", "exec"), globals(), globals())
