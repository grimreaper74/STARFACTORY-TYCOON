from pathlib import Path
source = (Path(__file__).parent / "prepare_press_shop_inbound_integration_candidate_v568.py").read_text(encoding="utf-8")
source = source.replace("v568", "v570").replace("V568", "V570")
exec(compile(source, str(Path(__file__).parent / "prepare_press_shop_inbound_integration_candidate_v568.py"), "exec"), globals(), globals())
