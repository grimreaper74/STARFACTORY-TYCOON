"""v103 exact-map adapter for retained map-bound live-HMI proof."""

from pathlib import Path

base = Path(__file__).with_name("validate_press_shop_pr010_live_hmi_pie_v102.py")
code = base.read_text(encoding="utf-8")
code = code.replace("/Game/LineBoss/Maps/LB_PressShop_PR010ReleaseArtCandidate_v102", "/Game/LineBoss/Maps/LB_PressShop_PR010ReleaseArtCandidate_v103")
code = code.replace("Saved/Audits/PR010_ReleaseArt_v102/live_hmi_pie_audit_v102.json", "Saved/Audits/PR010_ReleaseArt_v103/live_hmi_pie_audit_v103.json")
code = code.replace("pr010-live-hmi-pie-v102", "pr010-live-hmi-pie-v103")
code = code.replace("PR010_V102", "PR010_V103").replace("V102", "V103")
exec(compile(code, str(base) + "::v103", "exec"), globals(), globals())
