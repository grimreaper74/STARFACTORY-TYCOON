"""Use the v001 source gate against crown/endpoint presentation v002."""

from pathlib import Path

base = Path(__file__).with_name("audit_press_train_crown_endpoint_presentation_source_v001.py")
code = base.read_text(encoding="utf-8")
code = code.replace("CrownEndpointPresentation_v001", "CrownEndpointPresentation_v002")
code = code.replace("CROWN_ENDPOINT_PRESENTATION_MANIFEST_v001", "CROWN_ENDPOINT_PRESENTATION_MANIFEST_v002")
code = code.replace("crown-endpoint-presentation-v001", "crown-endpoint-presentation-v002")
code = code.replace("crown-endpoint-presentation-source-v001", "crown-endpoint-presentation-source-v002")
code = code.replace("CROWN_ENDPOINT_PRESENTATION_V001", "CROWN_ENDPOINT_PRESENTATION_V002")
code = code.replace("_v001", "_v002")
exec(compile(code, str(base) + "::v002", "exec"), globals(), globals())
