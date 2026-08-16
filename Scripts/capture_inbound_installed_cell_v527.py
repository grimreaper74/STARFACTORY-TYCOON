from pathlib import Path
source=(Path(__file__).parent/'capture_inbound_installed_cell_v526.py').read_text(encoding='utf-8')
source=source.replace('v526','v527').replace('V526','V527')
exec(compile(source,str(Path(__file__)),'exec'),globals(),globals())
