"""Build v092 directly from v090 with identity on the measured service fascia."""

from pathlib import Path


base = Path(__file__).with_name("build_press_shop_pr009_service_identity_candidate_v091.py")
code = base.read_text(encoding="utf-8")
code = code.replace("v091", "v092").replace("V091", "V092")
code = code.replace("LB_PressShop_PR009ServiceIdentityCandidate_v092", "LB_PressShop_PR009ServiceFasciaIdentityCandidate_v092")
replacements = {
    "CCTV-legible south-facing identity to the existing PR-009 guard panel":
        "CCTV-legible identity to the measured PR-009 south service fascia",
    "# Existing panel centre is (600,-1738.5,165), size 210x3x58 cm.  The south\n# face is near y=-1740; place text just outside it to avoid z-fighting.":
        "# The authored PR-009 interaction-hardware fascia bounds are centred near\n# (602,-2240.875,151) cm with its south face at y=-2258.75 cm.  Place the\n# identity 0.85 cm outside that measured face; all rows stay inside its z span.",
    "(600.0, -1741.2, 180.0), 8.2": "(602.0, -2259.6, 176.0), 12.0",
    "(600.0, -1741.2, 165.0), 7.0": "(602.0, -2259.6, 155.0), 10.0",
    "(600.0, -1741.2, 150.0), 5.4": "(602.0, -2259.6, 134.0), 7.5",
    "V092_TWO_SIDED_CCTV_LEGIBLE_CAIRNWELL_MOORCROSS_IDENTITY_BUILT__EARLY_VISUAL_GATE_REQUIRED__NOT_PROMOTED":
        "V092_MEASURED_SERVICE_FASCIA_CCTV_LEGIBLE_CAIRNWELL_MOORCROSS_IDENTITY_BUILT__EARLY_VISUAL_GATE_REQUIRED__NOT_PROMOTED",
    '"existing_panel_reused": True': '"existing_service_fascia_reused": True',
}
for old, new in replacements.items():
    if old not in code:
        raise RuntimeError(f"v092 adapter source token missing: {old}")
    code = code.replace(old, new)

exec(compile(code, str(base) + "::v092-service-fascia-identity", "exec"), globals(), globals())
