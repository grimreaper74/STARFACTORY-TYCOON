import unreal
paths=['/Game/LineBoss/IndustrialKit/InboundCoilDelivery/LorryAssemblyCandidate_v004/SM_CA_MW_Inbound_LorryFourCoil_v004','/Game/LineBoss/Candidates/PressShop/CleanRebuild_v20260809_v004/Inbound/SM_CA_MW_InboundLorry_Approved_v006','/Game/LineBoss/Candidates/PressShop/CleanRebuild_v20260809_v004/Inbound/SM_CA_MW_AdjustableCoilStand_Approved_v005']
for p in paths:
 m=unreal.load_asset(p);unreal.log('MAT_AUDIT '+p+' '+str([x.material_interface.get_path_name() if x.material_interface else None for x in m.static_materials]) if m else 'MISSING')
