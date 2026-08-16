"""Create the non-destructive all-Meshy provenance catalogue for the detail library."""
import csv,json,os
PROJECT=r"C:\\Users\\greg_\\Projects\\LineBossCarFactory_Unreal 5.8"
audit=os.path.join(PROJECT,'Saved','ValidationScreenshots','IndustrialDetailLibrary_Intake','all_meshy_model_audit.tsv')
out=os.path.join(PROJECT,'SourceAssets','Shared','CairnwellIndustrialDetailLibrary_v001','all_meshy_source_catalogue_v001.json')
rows=[]
with open(audit,encoding='utf-8-sig',errors='surrogateescape',newline='') as f:
 for row in csv.DictReader(f,delimiter='\t'):
  items=(row['summary'] or '').split('|')
  source=row['source'];kind=row['kind']
  # This is a capability classification, not an approval claim.
  if kind=='split': state='component-extraction-authority-candidate'
  elif kind in ('generate','texture'): state='whole-model-reference; no proven component separation'
  else: state='retained-master/reference; no automatic extraction'
  low=source.lower()
  exclusion=[]
  if any(w in low for w in ('robotic_arm','robot_', 'spot_weldi','vacuum_lif','tooling','e.oat')): exclusion.append('role-specific robot/tooling: do not extract wholesale')
  if any(w in low for w in ('automotive_', 'door_front','door_rear','bumper_', 'fender_', 'hood_', 'finished_car','vehicle','chassis')): exclusion.append('vehicle geometry: not industrial detail source')
  rows.append({'source_path':source,'file_kind':kind,'mesh_parts':int(items[0]) if items else 0,'vertices':int(items[1]) if len(items)>1 else 0,'polygons':int(items[2]) if len(items)>2 else 0,'bounds_m':[float(v) for v in items[3:6]] if len(items)>5 else [],'extraction_state':state,'exclusion_notes':exclusion})
payload={'catalogue':'Cairnwell Industrial Detail Library - all Meshy source catalogue v001','scope':'Every Meshy .blend discovered in workspace and Downloads. Catalogue does not modify source files.','counts':{'total':len(rows),'split':sum(r['file_kind']=='split' for r in rows),'generate':sum(r['file_kind']=='generate' for r in rows),'texture':sum(r['file_kind']=='texture' for r in rows),'other':sum(r['file_kind']=='other' for r in rows)},'sources':rows}
with open(out,'w',encoding='utf-8') as f:json.dump(payload,f,indent=2)
print('CATALOGUE|'+out);print('COUNT|'+str(len(rows)))
