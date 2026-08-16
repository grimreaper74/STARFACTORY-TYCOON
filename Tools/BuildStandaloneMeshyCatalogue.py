"""Create intact standalone Meshy machine/module candidate catalogue.

No model is copied, changed, or disassembled. Classification is filename and
geometry-audit based and expressly does not grant runtime or art approval.
"""
import csv,json,os,re
PROJECT=r"C:\\Users\\greg_\\Projects\\LineBossCarFactory_Unreal 5.8"
audit=os.path.join(PROJECT,'Saved','ValidationScreenshots','IndustrialDetailLibrary_Intake','all_meshy_model_audit.tsv')
out=os.path.join(PROJECT,'SourceAssets','Shared','CairnwellIndustrialDetailLibrary_v001','standalone_meshy_module_catalogue_v001.json')
rows=[]
with open(audit,encoding='utf-8-sig',errors='surrogateescape',newline='') as f:
 for r in csv.DictReader(f,delimiter='\t'):
  if r['kind']=='split':continue
  low=r['source'].lower();base=os.path.basename(r['source'])
  role='unclassified intact master'
  if any(x in low for x in ('cabinet','hmi','console','electrical','servicebox','service_box','control')):role='standalone cabinet, HMI or electrical/service enclosure'
  elif any(x in low for x in ('conveyor','roller_conv')):role='transport/conveyor module'
  elif any(x in low for x in ('coil','winder','cradle','v_block','film_winding')):role='coil or winding process module'
  elif any(x in low for x in ('gantry','rail_oven','treatment','facade','wall_panel','loading_ba','warehouse','green_door')):role='factory envelope or plant module'
  elif any(x in low for x in ('vision_gat','precision_assembly','adjustable','vacuum_lif')):role='body-weld fixture or tooling module'
  elif any(x in low for x in ('robotic_arm','robotic','spot_weldi')):role='robot or role-specific tool (whole model only)'
  elif any(x in low for x in ('forklift','agv','coil_hand')):role='logistics vehicle/module'
  elif any(x in low for x in ('automotive','car','vehicle','bumper','fender','door_','hood_','chassis')):role='vehicle component/visual; excluded from factory-machine reuse'
  elif any(x in low for x in ('industrial_', 'manufacturi')):role='industrial standalone machine/module'
  eligible=not any(x in low for x in ('robotic_arm','spot_weldi','automotive','bumper','fender','door_','hood_','finished_car','vehicle'))
  rows.append({'source_path':r['source'],'file_kind':r['kind'],'filename':base,'proven_role':role,'reuse_rule':'whole intact model only; never extract without a split source','candidate_status':'role-match validation required' if eligible else 'catalogued; excluded from common machine-skin reuse','audit_summary':r['summary']})
payload={'catalogue':'Cairnwell Standalone Meshy Module Catalogue v001','scope':'Every non-split Meshy master. Intact module candidates are a separate tier from small reusable details.','counts':{'total':len(rows),'whole-module-candidates':sum('excluded' not in r['candidate_status'] for r in rows),'excluded_vehicle_or_robot':sum('excluded' in r['candidate_status'] for r in rows)},'modules':rows}
cabinet_master=os.path.join(PROJECT,'SourceAssets','Shared','FactoryAssetLibrary','MeshyCabinetHMI_v632','CA_Factory_Cabinet_HMI_MeshyMasters_v632.blend')
payload['explicit_standalone_modules']=[
 {'name':'CW_Module_ElectricalCabinet_MeshyMaster_v632','source_path':cabinet_master,'source_object':'SM_CA_Factory_ElectricalCabinet_MeshyMaster_v632','dimensions_m':[.996,.777,1.899],'role':'full electrical/service cabinet','status':'source-reusable candidate; retain whole'},
 {'name':'CW_Module_OperatorHMI_MeshyMaster_v632','source_path':cabinet_master,'source_object':'SM_CA_Factory_OperatorHMI_MeshyMaster_v632','dimensions_m':[.522,.733,1.212],'role':'full operator HMI console','status':'source-reusable candidate; retain whole'}]
with open(out,'w',encoding='utf-8') as f:json.dump(payload,f,indent=2)
print('CATALOGUE|'+out);print('COUNT|'+str(len(rows)))
