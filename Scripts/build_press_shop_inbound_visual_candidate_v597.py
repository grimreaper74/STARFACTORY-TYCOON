"""Corrected, restrained lighting successor to rejected overexposed v596."""
from pathlib import Path
source = (Path(__file__).parent / "build_press_shop_inbound_visual_candidate_v596.py").read_text(encoding="utf-8")
source = source.replace("v596", "v597").replace("V596", "V597")
source = source.replace('"intensity": 4200.0', '"intensity": 850.0')
source = source.replace('1700.0, 1500.0', '450.0, 1500.0')
source = source.replace('1500.0, 1400.0', '400.0, 1400.0')
source = source.replace('(-15000.0, 5200.0, 3600.0), (-1500.0, -1200.0, 250.0), 58.0',
                        '(-15000.0, 4300.0, 1500.0), (-2500.0, -1250.0, 250.0), 62.0')
exec(compile(source, str(Path(__file__).parent / "build_press_shop_inbound_visual_candidate_v596.py"), "exec"), globals(), globals())
