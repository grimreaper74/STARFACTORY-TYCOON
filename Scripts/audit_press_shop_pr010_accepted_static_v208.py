"""Prove immutable accepted PR-010 scope remains intact inside v208."""

from pathlib import Path

source = Path(__file__).with_name("audit_press_shop_pr010_accepted_static_v103.py")
code = source.read_text(encoding="utf-8")
code = code.replace(
    "/Game/LineBoss/Maps/LB_PressShop_PR010Accepted_v103",
    "/Game/LineBoss/Maps/LB_PressShop_PR006ReleaseArtCandidate_v208",
)
code = code.replace(
    "Saved/Audits/PR010_Accepted_v103/accepted_static_audit.json",
    "Saved/Audits/PressShopIntegration/pr010_accepted_static_inherited_v208.json",
)
code = code.replace("pr010-accepted-static-v103", "pr010-accepted-static-inherited-v208")
exec(compile(code, str(source) + "::v208", "exec"), globals(), globals())
