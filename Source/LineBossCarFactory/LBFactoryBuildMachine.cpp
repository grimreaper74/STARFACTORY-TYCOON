#include "LBFactoryBuildMachine.h"
#include "Components/BoxComponent.h"
#include "Components/SceneComponent.h"
#include "Components/StaticMeshComponent.h"
#include "Engine/StaticMesh.h"
#include "Materials/MaterialInterface.h"
#include "UObject/ConstructorHelpers.h"
#include "LBFactoryFloorMarkingComponent.h"
#include "LBMachineLiveryComponent.h"
#include "LBStatusBeaconComponent.h"

namespace
{
enum class ECoilPreparationStation : uint8
{
    PR005,
    PR006,
    PR007,
    PR008,
    PR009,
    PR010
};

struct FCoilPreparationVisualSpec
{
    ECoilPreparationStation Station;
    const TCHAR* AssetPath;
    FVector StationLocationCm;
};

struct FCoilPreparationStationLayout
{
    ECoilPreparationStation Station;
    const TCHAR* StationId;
    int32 FirstAssetIndex;
    int32 AssetCount;
    FVector PackageLocationCm;
    float PackageYawDegrees;
    float UniformScale;
};

struct FCoilPreparationPaletteSpec
{
    uint8 StationMask;
    const TCHAR* Key;
    const TCHAR* AssetPath;
};

constexpr uint8 StationBit(const ECoilPreparationStation Station)
{
    return 1u << static_cast<uint8>(Station);
}

// Every entry below is a concrete Content asset from an accepted or station-authorized
// donor. Deliberately excluded: PR006/7 ReleaseDetail overlays, PR008 ProEnvelope,
// PR009/10 raw Meshy/OriginalHighPoly assets, and PR005 FloorZoning.
static const FCoilPreparationVisualSpec GCoilPreparationVisualSpecs[] =
{
    {ECoilPreparationStation::PR005, TEXT("/Game/LineBoss/Stations/Press/PR005/Candidate_v001/CoilCar/SM_CoilCar_Static.SM_CoilCar_Static"), FVector::ZeroVector},
    {ECoilPreparationStation::PR005, TEXT("/Game/LineBoss/Stations/Press/PR005/Candidate_v001/ContinuousStrip/SM_ContinuousStrip_Static.SM_ContinuousStrip_Static"), FVector::ZeroVector},
    {ECoilPreparationStation::PR005, TEXT("/Game/LineBoss/Stations/Press/PR005/Candidate_v001/CropShear/SM_CropShear_Static.SM_CropShear_Static"), FVector::ZeroVector},
    {ECoilPreparationStation::PR005, TEXT("/Game/LineBoss/Stations/Press/PR005/Candidate_v001/GuardingHMI/SM_GuardingHMI_Static.SM_GuardingHMI_Static"), FVector::ZeroVector},
    {ECoilPreparationStation::PR005, TEXT("/Game/LineBoss/Stations/Press/PR005/Candidate_v001/Headstock/SM_Headstock_Static.SM_Headstock_Static"), FVector::ZeroVector},
    {ECoilPreparationStation::PR005, TEXT("/Game/LineBoss/Stations/Press/PR005/Candidate_v001/HydraulicPowerUnit/SM_HydraulicPowerUnit_Static.SM_HydraulicPowerUnit_Static"), FVector::ZeroVector},
    {ECoilPreparationStation::PR005, TEXT("/Game/LineBoss/Stations/Press/PR005/Candidate_v001/HydraulicRouting/SM_HydraulicRouting_Static.SM_HydraulicRouting_Static"), FVector::ZeroVector},
    {ECoilPreparationStation::PR005, TEXT("/Game/LineBoss/Stations/Press/PR005/Candidate_v001/KeeperSnubber/SM_KeeperSnubber_Static.SM_KeeperSnubber_Static"), FVector::ZeroVector},
    {ECoilPreparationStation::PR005, TEXT("/Game/LineBoss/Stations/Press/PR005/Candidate_v001/PeelerThreader/SM_PeelerThreader_Static.SM_PeelerThreader_Static"), FVector::ZeroVector},
    {ECoilPreparationStation::PR005, TEXT("/Game/LineBoss/Stations/Press/PR005/Candidate_v001/ServiceLabels/SM_ServiceLabels_Static.SM_ServiceLabels_Static"), FVector::ZeroVector},

    {ECoilPreparationStation::PR006, TEXT("/Game/LineBoss/Stations/Press/PR006/Candidate_v001/SM_PR006_BaseSkid.SM_PR006_BaseSkid"), FVector(0, 0, 14)},
    {ECoilPreparationStation::PR006, TEXT("/Game/LineBoss/Stations/Press/PR006/Candidate_v001/SM_PR006_InfeedBridge.SM_PR006_InfeedBridge"), FVector(-302, 0, 70)},
    {ECoilPreparationStation::PR006, TEXT("/Game/LineBoss/Stations/Press/PR006/Candidate_v001/SM_PR006_OutfeedBridge.SM_PR006_OutfeedBridge"), FVector(302, 0, 70)},
    {ECoilPreparationStation::PR006, TEXT("/Game/LineBoss/Stations/Press/PR006/Candidate_v001/SM_PR006_FrameOperator.SM_PR006_FrameOperator"), FVector(0, -152, 148)},
    {ECoilPreparationStation::PR006, TEXT("/Game/LineBoss/Stations/Press/PR006/Candidate_v001/SM_PR006_FrameDrive.SM_PR006_FrameDrive"), FVector(0, 148, 148)},
    {ECoilPreparationStation::PR006, TEXT("/Game/LineBoss/Stations/Press/PR006/Candidate_v001/SM_PR006_TopCrossmember.SM_PR006_TopCrossmember"), FVector(0, 0, 278)},
    {ECoilPreparationStation::PR006, TEXT("/Game/LineBoss/Stations/Press/PR006/Candidate_v001/SM_PR006_LowerCassette_Operator.SM_PR006_LowerCassette_Operator"), FVector(0, -102, 103)},
    {ECoilPreparationStation::PR006, TEXT("/Game/LineBoss/Stations/Press/PR006/Candidate_v001/SM_PR006_UpperCassette_Operator.SM_PR006_UpperCassette_Operator"), FVector(0, -102, 142)},
    {ECoilPreparationStation::PR006, TEXT("/Game/LineBoss/Stations/Press/PR006/Candidate_v001/SM_PR006_LowerCassette_Drive.SM_PR006_LowerCassette_Drive"), FVector(0, 102, 103)},
    {ECoilPreparationStation::PR006, TEXT("/Game/LineBoss/Stations/Press/PR006/Candidate_v001/SM_PR006_UpperCassette_Drive.SM_PR006_UpperCassette_Drive"), FVector(0, 102, 142)},
    {ECoilPreparationStation::PR006, TEXT("/Game/LineBoss/Stations/Press/PR006/Candidate_v001/SM_PR006_MainGearbox.SM_PR006_MainGearbox"), FVector(-75, 200, 132)},
    {ECoilPreparationStation::PR006, TEXT("/Game/LineBoss/Stations/Press/PR006/Candidate_v001/SM_PR006_Identity.SM_PR006_Identity"), FVector(88, -180, 178)},

    {ECoilPreparationStation::PR007, TEXT("/Game/LineBoss/Stations/Press/PR007/Candidate_v001/SM_PR007_BaseSkid.SM_PR007_BaseSkid"), FVector(0, 0, 14)},
    {ECoilPreparationStation::PR007, TEXT("/Game/LineBoss/Stations/Press/PR007/Candidate_v001/SM_PR007_ChamberOperator.SM_PR007_ChamberOperator"), FVector(0, -146, 162)},
    {ECoilPreparationStation::PR007, TEXT("/Game/LineBoss/Stations/Press/PR007/Candidate_v001/SM_PR007_ChamberDrive.SM_PR007_ChamberDrive"), FVector(0, 146, 162)},
    {ECoilPreparationStation::PR007, TEXT("/Game/LineBoss/Stations/Press/PR007/Candidate_v001/SM_PR007_HoodWash.SM_PR007_HoodWash"), FVector(-111, 0, 282)},
    {ECoilPreparationStation::PR007, TEXT("/Game/LineBoss/Stations/Press/PR007/Candidate_v001/SM_PR007_HoodLube.SM_PR007_HoodLube"), FVector(111, 0, 282)},
    {ECoilPreparationStation::PR007, TEXT("/Game/LineBoss/Stations/Press/PR007/Candidate_v001/SM_PR007_InfeedVestibule.SM_PR007_InfeedVestibule"), FVector(-272, 0, 140)},
    {ECoilPreparationStation::PR007, TEXT("/Game/LineBoss/Stations/Press/PR007/Candidate_v001/SM_PR007_OutfeedVestibule.SM_PR007_OutfeedVestibule"), FVector(272, 0, 140)},
    {ECoilPreparationStation::PR007, TEXT("/Game/LineBoss/Stations/Press/PR007/Candidate_v001/SM_PR007_MistPlenum.SM_PR007_MistPlenum"), FVector(0, 0, 320)},
    {ECoilPreparationStation::PR007, TEXT("/Game/LineBoss/Stations/Press/PR007/Candidate_v001/SM_PR007_WashTank.SM_PR007_WashTank"), FVector(-135, 198, 68)},
    {ECoilPreparationStation::PR007, TEXT("/Game/LineBoss/Stations/Press/PR007/Candidate_v001/SM_PR007_LubeTank.SM_PR007_LubeTank"), FVector(135, 198, 68)},
    {ECoilPreparationStation::PR007, TEXT("/Game/LineBoss/Stations/Press/PR007/Candidate_v001/SM_PR007_MistDuct.SM_PR007_MistDuct"), FVector(0, 35, 372)},
    {ECoilPreparationStation::PR007, TEXT("/Game/LineBoss/Stations/Press/PR007/Candidate_v001/SM_PR007_IdentityPlate.SM_PR007_IdentityPlate"), FVector(90, -172, 234)},

    {ECoilPreparationStation::PR008, TEXT("/Game/LineBoss/Stations/Press/PR008/Detailed_v001/Module01/SM_CA_MW_PR008_EntryLoop_Frame_01.SM_CA_MW_PR008_EntryLoop_Frame_01"), FVector(0, -445, 95)},
    {ECoilPreparationStation::PR008, TEXT("/Game/LineBoss/Stations/Press/PR008/Detailed_v001/Module01/SM_CA_MW_PR008_LoopSensorBridge_01.SM_CA_MW_PR008_LoopSensorBridge_01"), FVector(0, -434, 135)},
    {ECoilPreparationStation::PR008, TEXT("/Game/LineBoss/Stations/Press/PR008/Detailed_v001/Module02/SM_CA_MW_PR008_EdgeTrackFrame_01.SM_CA_MW_PR008_EdgeTrackFrame_01"), FVector(0, -345, 95)},
    {ECoilPreparationStation::PR008, TEXT("/Game/LineBoss/Stations/Press/PR008/Detailed_v001/Module03/SM_CA_MW_PR008_ServoFeedFrame_01.SM_CA_MW_PR008_ServoFeedFrame_01"), FVector(0, -250, 95)},
    {ECoilPreparationStation::PR008, TEXT("/Game/LineBoss/Stations/Press/PR008/Detailed_v001/Module03/SM_CA_MW_PR008_ServoFeedRoll_Lower_01.SM_CA_MW_PR008_ServoFeedRoll_Lower_01"), FVector(0, -250, 84)},
    {ECoilPreparationStation::PR008, TEXT("/Game/LineBoss/Stations/Press/PR008/Detailed_v001/Module03/SM_CA_MW_PR008_ServoFeedRoll_Upper_01.SM_CA_MW_PR008_ServoFeedRoll_Upper_01"), FVector(0, -250, 106)},
    {ECoilPreparationStation::PR008, TEXT("/Game/LineBoss/Stations/Press/PR008/Detailed_v001/Module04/SM_CA_MW_PR008_TelescopeBaseFrame_01.SM_CA_MW_PR008_TelescopeBaseFrame_01"), FVector(0, -85, 90)},
    {ECoilPreparationStation::PR008, TEXT("/Game/LineBoss/Stations/Press/PR008/Detailed_v001/Module04/SM_CA_MW_PR008_TelescopeGuideBed_01.SM_CA_MW_PR008_TelescopeGuideBed_01"), FVector(0, -85, 78)},
    {ECoilPreparationStation::PR008, TEXT("/Game/LineBoss/Stations/Press/PR008/Detailed_v001/Module05/SM_CA_MW_PR008_PrePunchFrame_01.SM_CA_MW_PR008_PrePunchFrame_01"), FVector(0, 90, 90)},
    {ECoilPreparationStation::PR008, TEXT("/Game/LineBoss/Stations/Press/PR008/Detailed_v001/Module05/SM_CA_MW_PR008_PrePunchLowerCassette_01.SM_CA_MW_PR008_PrePunchLowerCassette_01"), FVector(0, 90, 74)},
    {ECoilPreparationStation::PR008, TEXT("/Game/LineBoss/Stations/Press/PR008/Detailed_v001/Module06/SM_CA_MW_PR008_ShearFrame_01.SM_CA_MW_PR008_ShearFrame_01"), FVector(0, 245, 90)},
    {ECoilPreparationStation::PR008, TEXT("/Game/LineBoss/Stations/Press/PR008/Detailed_v001/Module06/SM_CA_MW_PR008_ShearLowerKnifeCassette_01.SM_CA_MW_PR008_ShearLowerKnifeCassette_01"), FVector(0, 245, 72)},
    {ECoilPreparationStation::PR008, TEXT("/Game/LineBoss/Stations/Press/PR008/Detailed_v001/Module07/SM_CA_MW_PR008_DischargeFrame_01.SM_CA_MW_PR008_DischargeFrame_01"), FVector(0, 395, 90)},
    {ECoilPreparationStation::PR008, TEXT("/Game/LineBoss/Stations/Press/PR008/Detailed_v001/Module07/SM_CA_MW_PR008_DischargeBlank_01.SM_CA_MW_PR008_DischargeBlank_01"), FVector(0, 405, 107.5)},
    {ECoilPreparationStation::PR008, TEXT("/Game/LineBoss/Stations/Press/PR008/Detailed_v001/Module08/SM_CA_MW_PR008_HPU_BundSkid_01.SM_CA_MW_PR008_HPU_BundSkid_01"), FVector(-205, 405, 14)},
    {ECoilPreparationStation::PR008, TEXT("/Game/LineBoss/Stations/Press/PR008/Detailed_v001/Module08/SM_CA_MW_PR008_HPU_Reservoir_01.SM_CA_MW_PR008_HPU_Reservoir_01"), FVector(-206.125, 403, 70.5)},

    {ECoilPreparationStation::PR009, TEXT("/Game/LineBoss/Candidates/PressShop/PR009/v087/ReleaseCollision/Static/SM_CA_MW_PR009_BaseFrame_01_v087.SM_CA_MW_PR009_BaseFrame_01_v087"), FVector::ZeroVector},
    {ECoilPreparationStation::PR009, TEXT("/Game/LineBoss/Candidates/PressShop/PR009/v087/ReleaseCollision/Static/SM_CA_MW_PR009_Carrier_01_v087.SM_CA_MW_PR009_Carrier_01_v087"), FVector::ZeroVector},
    {ECoilPreparationStation::PR009, TEXT("/Game/LineBoss/Candidates/PressShop/PR009/v087/ReleaseCollision/Static/SM_CA_MW_PR009_ElectricalCabinet_01_v087.SM_CA_MW_PR009_ElectricalCabinet_01_v087"), FVector::ZeroVector},
    {ECoilPreparationStation::PR009, TEXT("/Game/LineBoss/Candidates/PressShop/PR009/v087/ReleaseCollision/Static/SM_CA_MW_PR009_GuardSet_01_v087.SM_CA_MW_PR009_GuardSet_01_v087"), FVector::ZeroVector},
    {ECoilPreparationStation::PR009, TEXT("/Game/LineBoss/Candidates/PressShop/PR009/v087/ReleaseCollision/Static/SM_CA_MW_PR009_HMI_01_v087.SM_CA_MW_PR009_HMI_01_v087"), FVector::ZeroVector},
    {ECoilPreparationStation::PR009, TEXT("/Game/LineBoss/Candidates/PressShop/PR009/v087/ReleaseCollision/Static/SM_CA_MW_PR009_InspectionHardware_01_v087.SM_CA_MW_PR009_InspectionHardware_01_v087"), FVector::ZeroVector},
    {ECoilPreparationStation::PR009, TEXT("/Game/LineBoss/Candidates/PressShop/PR009/v087/ReleaseCollision/Static/SM_CA_MW_PR009_InteractionHardware_01_v087.SM_CA_MW_PR009_InteractionHardware_01_v087"), FVector::ZeroVector},
    {ECoilPreparationStation::PR009, TEXT("/Game/LineBoss/Candidates/PressShop/PR009/v087/ReleaseCollision/Static/SM_CA_MW_PR009_ServiceSystems_01_v087.SM_CA_MW_PR009_ServiceSystems_01_v087"), FVector::ZeroVector},
    {ECoilPreparationStation::PR009, TEXT("/Game/LineBoss/Candidates/PressShop/PR009/v087/ReleaseCollision/Static/SM_CA_MW_PR009_TracePortal_01_v087.SM_CA_MW_PR009_TracePortal_01_v087"), FVector::ZeroVector},
    {ECoilPreparationStation::PR009, TEXT("/Game/LineBoss/Candidates/PressShop/PR009/v087/ReleaseCollision/Static/SM_CA_MW_PR009_VisionCentre_01_v087.SM_CA_MW_PR009_VisionCentre_01_v087"), FVector::ZeroVector},

    {ECoilPreparationStation::PR010, TEXT("/Game/LineBoss/Candidates/PressShop/PR010/Blockout_v001/SM_CA_MW_PR010_Deck.SM_CA_MW_PR010_Deck"), FVector(0, 0, 4)},
    {ECoilPreparationStation::PR010, TEXT("/Game/LineBoss/Candidates/PressShop/PR010/Blockout_v001/SM_CA_MW_PR010_ShuttleBed.SM_CA_MW_PR010_ShuttleBed"), FVector(0, -330, 35)},
    {ECoilPreparationStation::PR010, TEXT("/Game/LineBoss/Candidates/PressShop/PR010/Blockout_v001/SM_CA_MW_PR010_LaneBed.SM_CA_MW_PR010_LaneBed"), FVector(-450, 0, 30)},
    {ECoilPreparationStation::PR010, TEXT("/Game/LineBoss/Candidates/PressShop/PR010/Blockout_v001/SM_CA_MW_PR010_LaneBed.SM_CA_MW_PR010_LaneBed"), FVector(-150, 0, 30)},
    {ECoilPreparationStation::PR010, TEXT("/Game/LineBoss/Candidates/PressShop/PR010/Blockout_v001/SM_CA_MW_PR010_LaneBed.SM_CA_MW_PR010_LaneBed"), FVector(150, 0, 30)},
    {ECoilPreparationStation::PR010, TEXT("/Game/LineBoss/Candidates/PressShop/PR010/Blockout_v001/SM_CA_MW_PR010_LaneBed.SM_CA_MW_PR010_LaneBed"), FVector(450, 0, 30)},
    {ECoilPreparationStation::PR010, TEXT("/Game/LineBoss/Candidates/PressShop/PR010/ReleaseArt_v101/SM_CA_MW_PR010_CarrierPallet_v101.SM_CA_MW_PR010_CarrierPallet_v101"), FVector(-450, -180, 60)},
    {ECoilPreparationStation::PR010, TEXT("/Game/LineBoss/Candidates/PressShop/PR010/ReleaseArt_v101/SM_CA_MW_PR010_CarrierPallet_v101.SM_CA_MW_PR010_CarrierPallet_v101"), FVector(-150, -180, 60)},
    {ECoilPreparationStation::PR010, TEXT("/Game/LineBoss/Candidates/PressShop/PR010/ReleaseArt_v101/SM_CA_MW_PR010_CarrierPallet_v101.SM_CA_MW_PR010_CarrierPallet_v101"), FVector(150, -180, 60)},
    {ECoilPreparationStation::PR010, TEXT("/Game/LineBoss/Candidates/PressShop/PR010/ReleaseArt_v101/SM_CA_MW_PR010_CarrierPallet_v101.SM_CA_MW_PR010_CarrierPallet_v101"), FVector(450, -180, 60)},
    {ECoilPreparationStation::PR010, TEXT("/Game/LineBoss/Candidates/PressShop/PR010/ReleaseArt_v101/SM_CA_MW_PR010_BlankStack_Layered_v101.SM_CA_MW_PR010_BlankStack_Layered_v101"), FVector(-450, -180, 78)},
    {ECoilPreparationStation::PR010, TEXT("/Game/LineBoss/Candidates/PressShop/PR010/ReleaseArt_v101/SM_CA_MW_PR010_BlankStack_Layered_v101.SM_CA_MW_PR010_BlankStack_Layered_v101"), FVector(-150, -180, 78)},
    {ECoilPreparationStation::PR010, TEXT("/Game/LineBoss/Candidates/PressShop/PR010/ReleaseArt_v101/SM_CA_MW_PR010_BlankStack_Layered_v101.SM_CA_MW_PR010_BlankStack_Layered_v101"), FVector(150, -180, 78)},
    {ECoilPreparationStation::PR010, TEXT("/Game/LineBoss/Candidates/PressShop/PR010/ReleaseArt_v101/SM_CA_MW_PR010_BlankStack_Layered_v101.SM_CA_MW_PR010_BlankStack_Layered_v101"), FVector(450, -180, 78)},
    {ECoilPreparationStation::PR010, TEXT("/Game/LineBoss/Candidates/PressShop/PR010/ReleaseArt_v100/SM_CA_MW_PR010_RemoteHMIHousing_v100.SM_CA_MW_PR010_RemoteHMIHousing_v100"), FVector(645, -325, 0)}
};

static const FCoilPreparationStationLayout GCoilPreparationStationLayouts[] =
{
    {ECoilPreparationStation::PR005, TEXT("PR005"), 0, 10, FVector(0, -1000, -350), 0.0f, 0.48f},
    {ECoilPreparationStation::PR006, TEXT("PR006"), 10, 12, FVector(0, -620, -350), 90.0f, 0.48f},
    {ECoilPreparationStation::PR007, TEXT("PR007"), 22, 12, FVector(0, -260, -350), 90.0f, 0.48f},
    {ECoilPreparationStation::PR008, TEXT("PR008"), 34, 16, FVector(0, 170, -350), 0.0f, 0.48f},
    {ECoilPreparationStation::PR009, TEXT("PR009"), 50, 10, FVector(0, 650, -350), 0.0f, 0.48f},
    {ECoilPreparationStation::PR010, TEXT("PR010"), 60, 15, FVector(0, 1050, -350), 0.0f, 0.42f}
};

static const FCoilPreparationPaletteSpec GCoilPreparationPaletteSpecs[] =
{
    {StationBit(ECoilPreparationStation::PR006), TEXT("PR006.Frame"), TEXT("/Game/LineBoss/Stations/Press/PR006/Candidate_v001/Materials/M_PR006_CharcoalFrame_v001.M_PR006_CharcoalFrame_v001")},
    {StationBit(ECoilPreparationStation::PR006), TEXT("PR006.Panel"), TEXT("/Game/LineBoss/Stations/Press/PR006/Candidate_v001/Materials/M_PR006_WarmGreyPanel_v001.M_PR006_WarmGreyPanel_v001")},
    {StationBit(ECoilPreparationStation::PR006), TEXT("PR006.Yellow"), TEXT("/Game/LineBoss/Stations/Press/PR006/Candidate_v001/Materials/M_PR006_SafetyYellow_v001.M_PR006_SafetyYellow_v001")},
    {StationBit(ECoilPreparationStation::PR006), TEXT("PR006.Steel"), TEXT("/Game/LineBoss/Stations/Press/PR006/Candidate_v001/Materials/M_PR006_RollSteel_v001.M_PR006_RollSteel_v001")},
    {StationBit(ECoilPreparationStation::PR006), TEXT("PR006.Blue"), TEXT("/Game/LineBoss/Stations/Press/PR006/Candidate_v001/Materials/M_PR006_HydraulicBlue_v001.M_PR006_HydraulicBlue_v001")},
    {StationBit(ECoilPreparationStation::PR006), TEXT("PR006.White"), TEXT("/Game/LineBoss/Stations/Press/PR006/Candidate_v001/Materials/M_PR006_ServiceWhite_v001.M_PR006_ServiceWhite_v001")},
    {StationBit(ECoilPreparationStation::PR006), TEXT("PR006.Red"), TEXT("/Game/LineBoss/Stations/Press/PR006/Candidate_v001/Materials/M_PR006_EStopRed_v001.M_PR006_EStopRed_v001")},

    {StationBit(ECoilPreparationStation::PR007), TEXT("PR007.Frame"), TEXT("/Game/LineBoss/Stations/Press/PR007/Candidate_v001/Materials/M_PR007_CharcoalFrame_v001.M_PR007_CharcoalFrame_v001")},
    {StationBit(ECoilPreparationStation::PR007), TEXT("PR007.Stainless"), TEXT("/Game/LineBoss/Stations/Press/PR007/Candidate_v001/Materials/M_PR007_Stainless_v001.M_PR007_Stainless_v001")},
    {StationBit(ECoilPreparationStation::PR007), TEXT("PR007.Panel"), TEXT("/Game/LineBoss/Stations/Press/PR007/Candidate_v001/Materials/M_PR007_ServicePanel_v001.M_PR007_ServicePanel_v001")},
    {StationBit(ECoilPreparationStation::PR007), TEXT("PR007.Yellow"), TEXT("/Game/LineBoss/Stations/Press/PR007/Candidate_v001/Materials/M_PR007_SafetyYellow_v001.M_PR007_SafetyYellow_v001")},
    {StationBit(ECoilPreparationStation::PR007), TEXT("PR007.Blue"), TEXT("/Game/LineBoss/Stations/Press/PR007/Candidate_v001/Materials/M_PR007_WashBlue_v001.M_PR007_WashBlue_v001")},
    {StationBit(ECoilPreparationStation::PR007), TEXT("PR007.Green"), TEXT("/Game/LineBoss/Stations/Press/PR007/Candidate_v001/Materials/M_PR007_LubeGreen_v001.M_PR007_LubeGreen_v001")},
    {StationBit(ECoilPreparationStation::PR007), TEXT("PR007.Window"), TEXT("/Game/LineBoss/Stations/Press/PR007/Candidate_v001/Materials/M_PR007_Window_v001.M_PR007_Window_v001")},
    {StationBit(ECoilPreparationStation::PR007), TEXT("PR007.Steel"), TEXT("/Game/LineBoss/Stations/Press/PR007/Candidate_v001/Materials/M_PR007_RollSteel_v001.M_PR007_RollSteel_v001")},
    {StationBit(ECoilPreparationStation::PR007), TEXT("PR007.White"), TEXT("/Game/LineBoss/Stations/Press/PR007/Candidate_v001/Materials/M_PR007_Label_v001.M_PR007_Label_v001")},
    {StationBit(ECoilPreparationStation::PR007), TEXT("PR007.Red"), TEXT("/Game/LineBoss/Stations/Press/PR007/Candidate_v001/Materials/M_PR007_EStop_v001.M_PR007_EStop_v001")},

    {StationBit(ECoilPreparationStation::PR008), TEXT("PR008.Frame"), TEXT("/Game/LineBoss/Stations/Press/PR008/Detailed_v001/Materials/M_CA_MW_PR008_FoundryCharcoal_v001.M_CA_MW_PR008_FoundryCharcoal_v001")},
    {StationBit(ECoilPreparationStation::PR008), TEXT("PR008.Green"), TEXT("/Game/LineBoss/Stations/Press/PR008/Detailed_v001/Materials/M_CA_MW_PR008_CairnwellGreen_v001.M_CA_MW_PR008_CairnwellGreen_v001")},
    {StationBit(ECoilPreparationStation::PR008), TEXT("PR008.Yellow"), TEXT("/Game/LineBoss/Stations/Press/PR008/Detailed_v001/Materials/M_CA_MW_PR008_SafetyYellow_v001.M_CA_MW_PR008_SafetyYellow_v001")},
    {StationBit(ECoilPreparationStation::PR008), TEXT("PR008.Steel"), TEXT("/Game/LineBoss/Stations/Press/PR008/Detailed_v001/Materials/M_CA_MW_PR008_GroundSteel_v001.M_CA_MW_PR008_GroundSteel_v001")},
    {StationBit(ECoilPreparationStation::PR008), TEXT("PR008.Galvanised"), TEXT("/Game/LineBoss/Stations/Press/PR008/Detailed_v001/Materials/M_CA_MW_PR008_Galvanised_v001.M_CA_MW_PR008_Galvanised_v001")},
    {StationBit(ECoilPreparationStation::PR008), TEXT("PR008.Rubber"), TEXT("/Game/LineBoss/Stations/Press/PR008/Detailed_v001/Materials/M_CA_MW_PR008_Rubber_v001.M_CA_MW_PR008_Rubber_v001")},
    {StationBit(ECoilPreparationStation::PR008), TEXT("PR008.Glass"), TEXT("/Game/LineBoss/Stations/Press/PR008/Detailed_v001/Materials/M_CA_MW_PR008_SensorGlass_v001.M_CA_MW_PR008_SensorGlass_v001")},
    {StationBit(ECoilPreparationStation::PR008), TEXT("PR008.White"), TEXT("/Game/LineBoss/Stations/Press/PR008/Detailed_v001/Materials/M_CA_MW_PR008_LabelPlate_v001.M_CA_MW_PR008_LabelPlate_v001")},
    {StationBit(ECoilPreparationStation::PR008), TEXT("PR008.Red"), TEXT("/Game/LineBoss/Stations/Press/PR008/Detailed_v001/Materials/M_CA_MW_PR008_EStopRed_v001.M_CA_MW_PR008_EStopRed_v001")},
    {StationBit(ECoilPreparationStation::PR008), TEXT("PR008.Blue"), TEXT("/Game/LineBoss/Stations/Press/PR008/Detailed_v001/Materials/M_CA_MW_PR008_DriveBlue_v001.M_CA_MW_PR008_DriveBlue_v001")},
    {StationBit(ECoilPreparationStation::PR008), TEXT("PR008.Grey"), TEXT("/Game/LineBoss/Stations/Press/PR008/Detailed_v001/Materials/M_CA_MW_PR008_LightGrey_v001.M_CA_MW_PR008_LightGrey_v001")},

    // PR009 v096 promoted the v086 palette; PR010 v103 intentionally retained the v085
    // palette for its accepted baseline/release-art actors. Keep those authorities distinct.
    {StationBit(ECoilPreparationStation::PR009), TEXT("PR009.Frame"), TEXT("/Game/LineBoss/Stations/Press/PR009/Presentation_v086/Materials/M_CA_MW_PR009_LayeredFoundryCharcoal_v086.M_CA_MW_PR009_LayeredFoundryCharcoal_v086")},
    {StationBit(ECoilPreparationStation::PR009), TEXT("PR009.Green"), TEXT("/Game/LineBoss/Stations/Press/PR009/Presentation_v086/Materials/M_CA_MW_PR009_LayeredCairnwellGreen_v086.M_CA_MW_PR009_LayeredCairnwellGreen_v086")},
    {StationBit(ECoilPreparationStation::PR009), TEXT("PR009.Yellow"), TEXT("/Game/LineBoss/Stations/Press/PR009/Presentation_v086/Materials/M_CA_MW_PR009_LayeredSafetyYellow_v086.M_CA_MW_PR009_LayeredSafetyYellow_v086")},
    {StationBit(ECoilPreparationStation::PR009), TEXT("PR009.Grey"), TEXT("/Game/LineBoss/Stations/Press/PR009/Presentation_v086/Materials/M_CA_MW_PR009_LayeredServiceGrey_v086.M_CA_MW_PR009_LayeredServiceGrey_v086")},
    {StationBit(ECoilPreparationStation::PR009), TEXT("PR009.Structural"), TEXT("/Game/LineBoss/Stations/Press/PR009/Presentation_v086/Materials/M_CA_MW_PR009_StructuralSteel_v086.M_CA_MW_PR009_StructuralSteel_v086")},
    {StationBit(ECoilPreparationStation::PR009), TEXT("PR009.Machined"), TEXT("/Game/LineBoss/Stations/Press/PR009/Presentation_v086/Materials/M_CA_MW_PR009_MachinedSteel_v086.M_CA_MW_PR009_MachinedSteel_v086")},
    {StationBit(ECoilPreparationStation::PR009), TEXT("PR009.Blank"), TEXT("/Game/LineBoss/Stations/Press/PR009/Presentation_v086/Materials/M_CA_MW_PR009_OiledBlankSteel_v086.M_CA_MW_PR009_OiledBlankSteel_v086")},
    {StationBit(ECoilPreparationStation::PR009), TEXT("PR009.Galvanised"), TEXT("/Game/LineBoss/Stations/Press/PR009/Presentation_v086/Materials/M_CA_MW_PR009_GalvanisedMesh_v086.M_CA_MW_PR009_GalvanisedMesh_v086")},
    {StationBit(ECoilPreparationStation::PR009), TEXT("PR009.Rubber"), TEXT("/Game/LineBoss/Stations/Press/PR009/Presentation_v086/Materials/M_CA_MW_PR009_Rubber_v086.M_CA_MW_PR009_Rubber_v086")},
    {StationBit(ECoilPreparationStation::PR009), TEXT("PR009.Glass"), TEXT("/Game/LineBoss/Stations/Press/PR009/Presentation_v086/Materials/M_CA_MW_PR009_SensorGlass_v086.M_CA_MW_PR009_SensorGlass_v086")},
    {StationBit(ECoilPreparationStation::PR009), TEXT("PR009.Screen"), TEXT("/Game/LineBoss/Stations/Press/PR009/Presentation_v086/Materials/M_CA_MW_PR009_HMIScreenOnline_v086.M_CA_MW_PR009_HMIScreenOnline_v086")},
    {StationBit(ECoilPreparationStation::PR009), TEXT("PR009.Red"), TEXT("/Game/LineBoss/Stations/Press/PR009/Presentation_v086/Materials/M_CA_MW_PR009_EStopRed_v086.M_CA_MW_PR009_EStopRed_v086")},
    {StationBit(ECoilPreparationStation::PR009), TEXT("PR009.Amber"), TEXT("/Game/LineBoss/Stations/Press/PR009/Presentation_v086/Materials/M_CA_MW_PR009_AmberSafetyActive_v086.M_CA_MW_PR009_AmberSafetyActive_v086")},
    {StationBit(ECoilPreparationStation::PR009), TEXT("PR009.White"), TEXT("/Game/LineBoss/Stations/Press/PR009/Presentation_v086/Materials/M_CA_MW_PR009_LabelWhite_v086.M_CA_MW_PR009_LabelWhite_v086")},
    {StationBit(ECoilPreparationStation::PR009), TEXT("PR009.Blue"), TEXT("/Game/LineBoss/Stations/Press/PR009/Presentation_v086/Materials/M_CA_MW_PR009_DriveBlue_v086.M_CA_MW_PR009_DriveBlue_v086")},

    {StationBit(ECoilPreparationStation::PR010), TEXT("PR010.Frame"), TEXT("/Game/LineBoss/Stations/Press/PR009/Presentation_v085/Materials/M_CA_MW_PR009_LayeredFoundryCharcoal_v085.M_CA_MW_PR009_LayeredFoundryCharcoal_v085")},
    {StationBit(ECoilPreparationStation::PR010), TEXT("PR010.Green"), TEXT("/Game/LineBoss/Stations/Press/PR009/Presentation_v085/Materials/M_CA_MW_PR009_LayeredCairnwellGreen_v085.M_CA_MW_PR009_LayeredCairnwellGreen_v085")},
    {StationBit(ECoilPreparationStation::PR010), TEXT("PR010.Yellow"), TEXT("/Game/LineBoss/Stations/Press/PR009/Presentation_v085/Materials/M_CA_MW_PR009_LayeredSafetyYellow_v085.M_CA_MW_PR009_LayeredSafetyYellow_v085")},
    {StationBit(ECoilPreparationStation::PR010), TEXT("PR010.Grey"), TEXT("/Game/LineBoss/Stations/Press/PR009/Presentation_v085/Materials/M_CA_MW_PR009_LayeredServiceGrey_v085.M_CA_MW_PR009_LayeredServiceGrey_v085")},
    {StationBit(ECoilPreparationStation::PR010), TEXT("PR010.Structural"), TEXT("/Game/LineBoss/Stations/Press/PR009/Presentation_v085/Materials/M_CA_MW_PR009_StructuralSteel_v085.M_CA_MW_PR009_StructuralSteel_v085")},
    {StationBit(ECoilPreparationStation::PR010), TEXT("PR010.Machined"), TEXT("/Game/LineBoss/Stations/Press/PR009/Presentation_v085/Materials/M_CA_MW_PR009_MachinedSteel_v085.M_CA_MW_PR009_MachinedSteel_v085")},
    {StationBit(ECoilPreparationStation::PR010), TEXT("PR010.Blank"), TEXT("/Game/LineBoss/Stations/Press/PR009/Presentation_v085/Materials/M_CA_MW_PR009_OiledBlankSteel_v085.M_CA_MW_PR009_OiledBlankSteel_v085")},
    {StationBit(ECoilPreparationStation::PR010), TEXT("PR010.Galvanised"), TEXT("/Game/LineBoss/Stations/Press/PR009/Presentation_v085/Materials/M_CA_MW_PR009_GalvanisedMesh_v085.M_CA_MW_PR009_GalvanisedMesh_v085")},
    {StationBit(ECoilPreparationStation::PR010), TEXT("PR010.Rubber"), TEXT("/Game/LineBoss/Stations/Press/PR009/Presentation_v085/Materials/M_CA_MW_PR009_Rubber_v085.M_CA_MW_PR009_Rubber_v085")},
    {StationBit(ECoilPreparationStation::PR010), TEXT("PR010.Glass"), TEXT("/Game/LineBoss/Stations/Press/PR009/Presentation_v085/Materials/M_CA_MW_PR009_SensorGlass_v085.M_CA_MW_PR009_SensorGlass_v085")},
    {StationBit(ECoilPreparationStation::PR010), TEXT("PR010.Screen"), TEXT("/Game/LineBoss/Stations/Press/PR009/Presentation_v085/Materials/M_CA_MW_PR009_HMIScreenOnline_v085.M_CA_MW_PR009_HMIScreenOnline_v085")},
    {StationBit(ECoilPreparationStation::PR010), TEXT("PR010.Red"), TEXT("/Game/LineBoss/Stations/Press/PR009/Presentation_v085/Materials/M_CA_MW_PR009_EStopRed_v085.M_CA_MW_PR009_EStopRed_v085")},
    {StationBit(ECoilPreparationStation::PR010), TEXT("PR010.Amber"), TEXT("/Game/LineBoss/Stations/Press/PR009/Presentation_v085/Materials/M_CA_MW_PR009_AmberSafetyActive_v085.M_CA_MW_PR009_AmberSafetyActive_v085")},
    {StationBit(ECoilPreparationStation::PR010), TEXT("PR010.White"), TEXT("/Game/LineBoss/Stations/Press/PR009/Presentation_v085/Materials/M_CA_MW_PR009_LabelWhite_v085.M_CA_MW_PR009_LabelWhite_v085")},
    {StationBit(ECoilPreparationStation::PR010), TEXT("PR010.Blue"), TEXT("/Game/LineBoss/Stations/Press/PR009/Presentation_v085/Materials/M_CA_MW_PR009_DriveBlue_v085.M_CA_MW_PR009_DriveBlue_v085")}
};

FName SelectCoilPreparationMaterialKey(const ECoilPreparationStation Station,
    const FString& MeshPath, const FName SlotName, const int32 SlotIndex)
{
    const FString MeshToken = MeshPath.ToUpper();
    const FString SlotToken = SlotName.ToString().ToUpper();
    const auto MeshHas = [&MeshToken](const TCHAR* Text) { return MeshToken.Contains(Text); };
    const auto SlotHas = [&SlotToken](const TCHAR* Text) { return SlotToken.Contains(Text); };
    const TCHAR* Prefix = Station == ECoilPreparationStation::PR006 ? TEXT("PR006.")
        : Station == ECoilPreparationStation::PR007 ? TEXT("PR007.")
        : Station == ECoilPreparationStation::PR008 ? TEXT("PR008.")
        : Station == ECoilPreparationStation::PR009 ? TEXT("PR009.") : TEXT("PR010.");
    auto Key = [Prefix](const TCHAR* Role) { return FName(*(FString(Prefix) + Role)); };

    // PR010's baseline assets have deliberately generic import slot names. The accepted
    // v103 donor therefore remains the exact slot-order authority for these six meshes.
    if (Station == ECoilPreparationStation::PR010)
    {
        if (MeshHas(TEXT("CARRIERPALLET")))
            return SlotIndex == 0 ? Key(TEXT("Yellow"))
                : SlotIndex == 1 ? Key(TEXT("Frame")) : Key(TEXT("Machined"));
        if (MeshHas(TEXT("BLANKSTACK_LAYERED")))
            return SlotIndex == 0 ? Key(TEXT("Blank"))
                : SlotIndex == 1 ? Key(TEXT("Frame")) : Key(TEXT("Grey"));
        if (MeshHas(TEXT("REMOTEHMIHOUSING")))
        {
            static const TCHAR* Roles[] = {TEXT("Frame"), TEXT("Grey"), TEXT("Screen"),
                TEXT("Green"), TEXT("Yellow"), TEXT("Glass")};
            return Key(Roles[FMath::Clamp(SlotIndex, 0, UE_ARRAY_COUNT(Roles) - 1)]);
        }
        if (MeshHas(TEXT("SHUTTLEBED"))) return Key(TEXT("Machined"));
        if (MeshHas(TEXT("DECK")) || MeshHas(TEXT("LANEBED"))) return Key(TEXT("Frame"));
    }

    // PR008 and PR009 preserve semantic material slot names in the mesh. Reading the slot
    // before the mesh name prevents FrameDrive, for example, being painted motor blue.
    if (SlotHas(TEXT("ESTOP")) || SlotHas(TEXT("_RED"))) return Key(TEXT("Red"));
    if (SlotHas(TEXT("SCREEN")) || SlotHas(TEXT("DISPLAY"))) return Key(TEXT("Screen"));
    if (SlotHas(TEXT("WINDOW"))) return Station == ECoilPreparationStation::PR007
        ? Key(TEXT("Window")) : Key(TEXT("Glass"));
    if (SlotHas(TEXT("SENSOR")) || SlotHas(TEXT("GLASS"))) return Key(TEXT("Glass"));
    if (SlotHas(TEXT("AMBER")) || SlotHas(TEXT("STATUS"))) return Key(TEXT("Amber"));
    if (SlotHas(TEXT("YELLOW")) || SlotHas(TEXT("SAFETY"))) return Key(TEXT("Yellow"));
    if (SlotHas(TEXT("GREEN")) || SlotHas(TEXT("LUBE"))) return Key(TEXT("Green"));
    if (SlotHas(TEXT("GALV")) || SlotHas(TEXT("MESH"))) return Key(TEXT("Galvanised"));
    if (SlotHas(TEXT("RUBBER")) || SlotHas(TEXT("TYRE"))) return Key(TEXT("Rubber"));
    if (SlotHas(TEXT("BLUE")) || SlotHas(TEXT("MOTOR"))) return Key(TEXT("Blue"));
    if (SlotHas(TEXT("LABEL")) || SlotHas(TEXT("IDENTITY")) || SlotHas(TEXT("WHITE"))) return Key(TEXT("White"));
    if (SlotHas(TEXT("BLANK"))) return Key(TEXT("Blank"));
    if (SlotHas(TEXT("MACHIN"))) return Key(TEXT("Machined"));
    if (SlotHas(TEXT("LIGHT_GREY")) || SlotHas(TEXT("SERVICEGREY")) || SlotHas(TEXT("SERVICE_GREY")))
        return Key(TEXT("Grey"));
    if (SlotHas(TEXT("STEEL")))
        return Station == ECoilPreparationStation::PR009 || Station == ECoilPreparationStation::PR010
            ? Key(TEXT("Structural")) : Key(TEXT("Steel"));
    if (SlotHas(TEXT("GREY")) || SlotHas(TEXT("PANEL"))) return Key(TEXT("Grey"));
    if (SlotHas(TEXT("FRAME")) || SlotHas(TEXT("CHARCOAL"))) return Key(TEXT("Frame"));

    // PR006/PR007 use one authored slot per selected major module. These object-role
    // mappings reproduce the accepted donor materials rather than guessing from colour.
    if (Station == ECoilPreparationStation::PR006)
    {
        if (MeshHas(TEXT("FRAMEOPERATOR")) || MeshHas(TEXT("FRAMEDRIVE"))) return Key(TEXT("Panel"));
        if (MeshHas(TEXT("UPPERCASSETTE"))) return Key(TEXT("Yellow"));
        if (MeshHas(TEXT("LOWERCASSETTE")) || MeshHas(TEXT("MAINGEARBOX"))) return Key(TEXT("Steel"));
        return Key(TEXT("Frame"));
    }
    if (Station == ECoilPreparationStation::PR007)
    {
        if (MeshHas(TEXT("CHAMBER"))) return Key(TEXT("Panel"));
        if (MeshHas(TEXT("IDENTITYPLATE"))) return Key(TEXT("White"));
        if (MeshHas(TEXT("HOOD")) || MeshHas(TEXT("TANK")) || MeshHas(TEXT("MISTDUCT")))
            return Key(TEXT("Stainless"));
        return Key(TEXT("Frame"));
    }
    if (Station == ECoilPreparationStation::PR008 && MeshHas(TEXT("DISCHARGEBLANK")))
        return Key(TEXT("Steel"));
    return Key(TEXT("Frame"));
}
}

ALBFactoryBuildMachine::ALBFactoryBuildMachine()
{
    PrimaryActorTick.bCanEverTick = false;
    SceneRoot = CreateDefaultSubobject<USceneComponent>(TEXT("SceneRoot"));
    SetRootComponent(SceneRoot);
    FloorMarkings = CreateDefaultSubobject<ULBFactoryFloorMarkingComponent>(TEXT("PlacementFloorMarkings"));
    FloorMarkings->SetupAttachment(SceneRoot);
    MachineLivery = CreateDefaultSubobject<ULBMachineLiveryComponent>(TEXT("MachineLivery"));
    MachineBase = CreateDefaultSubobject<UStaticMeshComponent>(TEXT("MachineBase"));
    MachineBase->SetupAttachment(SceneRoot);
    MachineBase->SetCollisionEnabled(ECollisionEnabled::QueryAndPhysics);
    MachineBase->SetCollisionResponseToAllChannels(ECR_Block);
    MachineBody = CreateDefaultSubobject<UStaticMeshComponent>(TEXT("MachineBody"));
    MachineBody->SetupAttachment(SceneRoot);
    MachineBody->SetCollisionEnabled(ECollisionEnabled::QueryAndPhysics);
    MachineBody->SetCollisionResponseToAllChannels(ECR_Block);
    ApprovedVisual = CreateDefaultSubobject<UStaticMeshComponent>(TEXT("ApprovedVisual"));
    ApprovedVisual->SetupAttachment(SceneRoot);
    ApprovedVisual->SetVisibility(false);
    ApprovedVisual->SetCollisionEnabled(ECollisionEnabled::NoCollision);
    ApprovedVisual->SetCollisionResponseToAllChannels(ECR_Block);
    for (int32 Index = 0; Index < 8; ++Index)
    {
        UStaticMeshComponent* Stand = CreateDefaultSubobject<UStaticMeshComponent>(
            *FString::Printf(TEXT("TrailerStandVisual_%02d"), Index + 1));
        Stand->SetupAttachment(SceneRoot);
        Stand->SetVisibility(false);
        Stand->SetCollisionEnabled(ECollisionEnabled::NoCollision);
        Stand->SetCollisionResponseToAllChannels(ECR_Block);
        TrailerStandVisuals.Add(Stand);
    }
    for (int32 Index = 0; Index < 4; ++Index)
    {
        UStaticMeshComponent* Coil = CreateDefaultSubobject<UStaticMeshComponent>(
            *FString::Printf(TEXT("TrailerCoilVisual_%02d"), Index + 1));
        Coil->SetupAttachment(SceneRoot);
        Coil->SetVisibility(false);
        Coil->SetCollisionEnabled(ECollisionEnabled::NoCollision);
        Coil->SetCollisionResponseToAllChannels(ECR_Block);
        TrailerCoilVisuals.Add(Coil);
    }
    auto CreateInboundCranePart = [this](const TCHAR* Name)
    {
        UStaticMeshComponent* Part = CreateDefaultSubobject<UStaticMeshComponent>(Name);
        Part->SetupAttachment(SceneRoot);
        Part->SetVisibility(false);
        Part->SetCollisionEnabled(ECollisionEnabled::NoCollision);
        Part->SetCollisionResponseToAllChannels(ECR_Block);
        return Part;
    };
    InboundCraneRunwayVisual = CreateInboundCranePart(TEXT("InboundCraneRunwayVisual"));
    InboundCraneBridgeVisual = CreateInboundCranePart(TEXT("InboundCraneBridgeVisual"));
    InboundCraneTrolleyVisual = CreateInboundCranePart(TEXT("InboundCraneTrolleyVisual"));
    InboundCraneHoistVisual = CreateInboundCranePart(TEXT("InboundCraneHoistVisual"));
    InboundCHookVisual = CreateInboundCranePart(TEXT("InboundCHookVisual"));
    InboundCoilHandlerFixedFrontAxleRoot = CreateDefaultSubobject<USceneComponent>(
        TEXT("CHF01_FIXED_FRONT_LOAD_AXLE"));
    InboundCoilHandlerFixedFrontAxleRoot->SetupAttachment(InboundCraneRunwayVisual);
    // CHF01 local -X is the mast/load end. Keep those wheels fixed.
    InboundCoilHandlerFixedFrontAxleRoot->SetRelativeLocation(FVector(-130.0f, 0.0f, -45.0f));
    InboundCoilHandlerRearSteeringRoot = CreateDefaultSubobject<USceneComponent>(
        TEXT("CHF01_PIVOT_REAR_STEER_Z"));
    InboundCoilHandlerRearSteeringRoot->SetupAttachment(InboundCraneRunwayVisual);
    // The counterweight axle is 3.00 m behind the load axle in the approved 4.8 m body.
    InboundCoilHandlerRearSteeringRoot->SetRelativeLocation(FVector(170.0f, 0.0f, -45.0f));
    ReceivingSaddleRailAVisual = CreateInboundCranePart(TEXT("ReceivingSaddleRailAVisual"));
    ReceivingSaddleRailBVisual = CreateInboundCranePart(TEXT("ReceivingSaddleRailBVisual"));
    PR002StationVisual = CreateInboundCranePart(TEXT("PR002StationVisual"));
    PR002PayloadVisual = CreateInboundCranePart(TEXT("PR002PayloadVisual"));
    PR005DetailedHMIVisual = CreateInboundCranePart(TEXT("PR005DetailedHMIVisual"));
    PR005DetailedHMIVisual->SetCanEverAffectNavigation(false);
    PR005DetailedHMIVisual->SetGenerateOverlapEvents(false);
    // The largest imported compact package uses 75 visible modules. Five spare slots keep
    // this shared presentation pool useful to the other provisional machine types.
    for (int32 Index = 0; Index < 80; ++Index)
    {
        UStaticMeshComponent* Part = CreateDefaultSubobject<UStaticMeshComponent>(
            *FString::Printf(TEXT("ProvisionalModule_%02d"), Index + 1));
        Part->SetupAttachment(SceneRoot);
        Part->SetVisibility(false);
        Part->SetCollisionEnabled(ECollisionEnabled::NoCollision);
        Part->SetCollisionResponseToAllChannels(ECR_Block);
        // The protected machine envelope is the placement/selection authority. These
        // replaceable presentation modules must not add donor collision or nav geometry.
        Part->SetCanEverAffectNavigation(false);
        Part->SetGenerateOverlapEvents(false);
        PlaceholderParts.Add(Part);
    }
    CoilPreparationVisualAssets.Reserve(UE_ARRAY_COUNT(GCoilPreparationVisualSpecs));
    for (const FCoilPreparationVisualSpec& Spec : GCoilPreparationVisualSpecs)
    {
        CoilPreparationVisualAssets.Add(TSoftObjectPtr<UStaticMesh>(FSoftObjectPath(Spec.AssetPath)));
    }
    for (const FCoilPreparationPaletteSpec& Palette : GCoilPreparationPaletteSpecs)
    {
        CoilPreparationPaletteMaterials.Add(FName(Palette.Key),
            TSoftObjectPtr<UMaterialInterface>(FSoftObjectPath(Palette.AssetPath)));
    }
    ProtectedEnvelope = CreateDefaultSubobject<UBoxComponent>(TEXT("ProtectedEnvelope"));
    ProtectedEnvelope->SetupAttachment(SceneRoot);
    ProtectedEnvelope->SetCollisionEnabled(ECollisionEnabled::QueryOnly);
    ProtectedEnvelope->SetCollisionResponseToAllChannels(ECR_Overlap);
    InputPort = CreateDefaultSubobject<ULBFactoryProcessPortComponent>(TEXT("InputPort"));
    InputPort->SetupAttachment(SceneRoot);
    InputPort->Direction = ELBFactoryPortDirection::Input;
    OutputPort = CreateDefaultSubobject<ULBFactoryProcessPortComponent>(TEXT("OutputPort"));
    OutputPort->SetupAttachment(SceneRoot);
    OutputPort->Direction = ELBFactoryPortDirection::Output;
    OutputPort->MaximumConnections = 4;
    StatusBeacon = CreateDefaultSubobject<ULBStatusBeaconComponent>(TEXT("FactoryMachine_RuntimeStatusBeacon"));
    StatusBeacon->SetupAttachment(SceneRoot);
    StatusBeacon->SetRelativeScale3D(FVector(0.75f));
    StatusBeacon->SetStatus(ELBStatusBeaconState::Idle);

    static ConstructorHelpers::FObjectFinder<UStaticMesh> CubeMesh(TEXT("/Engine/BasicShapes/Cube.Cube"));
    if (CubeMesh.Succeeded())
    {
        PlaceholderCubeMesh = CubeMesh.Object;
        MachineBase->SetStaticMesh(CubeMesh.Object);
        MachineBody->SetStaticMesh(CubeMesh.Object);
    }
    static ConstructorHelpers::FObjectFinder<UStaticMesh> CylinderMesh(TEXT("/Engine/BasicShapes/Cylinder.Cylinder"));
    if (CylinderMesh.Succeeded()) PlaceholderCylinderMesh = CylinderMesh.Object;
    static ConstructorHelpers::FObjectFinder<UMaterialInterface> GreenMaterial(
        TEXT("/Game/LineBoss/Candidates/ControlRoom/MainControlRoom_v002/Materials/M_CA_CairnwellGreen_R_v002.M_CA_CairnwellGreen_R_v002"));
    static ConstructorHelpers::FObjectFinder<UMaterialInterface> CharcoalMaterial(
        TEXT("/Game/LineBoss/Candidates/ControlRoom/MainControlRoom_v002/Materials/M_CA_FoundryCharcoal_R_v002.M_CA_FoundryCharcoal_R_v002"));
    static ConstructorHelpers::FObjectFinder<UMaterialInterface> YellowMaterial(
        TEXT("/Game/LineBoss/Candidates/ControlRoom/MainControlRoom_v002/Materials/M_CA_SafetyYellow_R_v002.M_CA_SafetyYellow_R_v002"));
    static ConstructorHelpers::FObjectFinder<UMaterialInterface> SteelMaterial(
        TEXT("/Game/LineBoss/Candidates/ControlRoom/MainControlRoom_v002/Materials/M_CA_BrushedSteel_R_v002.M_CA_BrushedSteel_R_v002"));
    if (GreenMaterial.Succeeded()) PlaceholderGreenMaterial = GreenMaterial.Object;
    if (CharcoalMaterial.Succeeded()) PlaceholderCharcoalMaterial = CharcoalMaterial.Object;
    if (YellowMaterial.Succeeded()) PlaceholderYellowMaterial = YellowMaterial.Object;
    if (SteelMaterial.Succeeded()) PlaceholderSteelMaterial = SteelMaterial.Object;
    static ConstructorHelpers::FObjectFinder<UMaterialInterface> GenericTintableMaterial(
        TEXT("/Engine/BasicShapes/BasicShapeMaterial.BasicShapeMaterial"));
    if (GenericTintableMaterial.Succeeded()) GenericLiveryMaterialParent = GenericTintableMaterial.Object;
    static ConstructorHelpers::FObjectFinder<UStaticMesh> ApprovedInboundLorry(
        TEXT("/Game/LineBoss/Candidates/PressShop/CleanRebuild_v20260809_v004/Inbound/SM_CA_MW_InboundLorry_Approved_v006.SM_CA_MW_InboundLorry_Approved_v006"));
    if (ApprovedInboundLorry.Succeeded()) ApprovedInboundLorryMesh = ApprovedInboundLorry.Object;
    static ConstructorHelpers::FObjectFinder<UStaticMesh> ApprovedCoilHandlerBody(
        TEXT("/Game/LineBoss/Runtime/PressShop/CoilHandlerAGV_v999/SM_Cairnwell_AGV_CHF01_StaticBody_v999.SM_Cairnwell_AGV_CHF01_StaticBody_v999"));
    if (ApprovedCoilHandlerBody.Succeeded()) ApprovedCoilHandlerBodyMesh = ApprovedCoilHandlerBody.Object;
    static ConstructorHelpers::FObjectFinder<UStaticMesh> ApprovedCoilHandlerLift(
        TEXT("/Game/LineBoss/Runtime/PressShop/CoilHandlerAGV_v999/SM_Cairnwell_AGV_CHF01_LiftAssembly_v999.SM_Cairnwell_AGV_CHF01_LiftAssembly_v999"));
    if (ApprovedCoilHandlerLift.Succeeded()) ApprovedCoilHandlerLiftMesh = ApprovedCoilHandlerLift.Object;
    static ConstructorHelpers::FObjectFinder<UStaticMesh> ApprovedPR004CompleteCell(
        TEXT("/Game/LineBoss/Runtime/PressShop/PR004_v997/SM_Cairnwell_PR004_CompleteCell_Runtime_v997.SM_Cairnwell_PR004_CompleteCell_Runtime_v997"));
    if (ApprovedPR004CompleteCell.Succeeded()) ApprovedPR004CompleteCellMesh = ApprovedPR004CompleteCell.Object;
    static ConstructorHelpers::FObjectFinder<UStaticMesh> ApprovedCoilSaddle(
        TEXT("/Game/LineBoss/Runtime/PressShop/PR004_v997/SM_Cairnwell_AdjustableCoilSaddle_Runtime_v997.SM_Cairnwell_AdjustableCoilSaddle_Runtime_v997"));
    if (ApprovedCoilSaddle.Succeeded()) ApprovedCoilSaddleMesh = ApprovedCoilSaddle.Object;
    static ConstructorHelpers::FObjectFinder<UStaticMesh> ApprovedTrailerStand(
        TEXT("/Game/LineBoss/Candidates/PressShop/CleanRebuild_v20260809_v004/Inbound/SM_CA_MW_AdjustableCoilStand_Approved_v005.SM_CA_MW_AdjustableCoilStand_Approved_v005"));
    static ConstructorHelpers::FObjectFinder<UStaticMesh> ApprovedWrappedCoil(
        TEXT("/Game/LineBoss/Candidates/PressShop/CleanRebuild_v20260809_v004/Inbound/SM_CA_MW_WrappedCoil_Repaired_v003.SM_CA_MW_WrappedCoil_Repaired_v003"));
    for (UStaticMeshComponent* Stand : TrailerStandVisuals)
    {
        if (ApprovedTrailerStand.Succeeded()) Stand->SetStaticMesh(ApprovedTrailerStand.Object);
    }
    if (ApprovedTrailerStand.Succeeded())
    {
        ReceivingSaddleRailAVisual->SetStaticMesh(ApprovedTrailerStand.Object);
        ReceivingSaddleRailBVisual->SetStaticMesh(ApprovedTrailerStand.Object);
    }
    for (UStaticMeshComponent* Coil : TrailerCoilVisuals)
    {
        if (ApprovedWrappedCoil.Succeeded()) Coil->SetStaticMesh(ApprovedWrappedCoil.Object);
    }
    static ConstructorHelpers::FObjectFinder<UStaticMesh> InboundCraneRunway(
        TEXT("/Game/LineBoss/IndustrialKit/MaterialHandling/BridgeCrane/InboundInstalledCrane/Candidate_v001/SM_CA_MW_InboundCrane_StaticRunwayFrame_v001.SM_CA_MW_InboundCrane_StaticRunwayFrame_v001"));
    static ConstructorHelpers::FObjectFinder<UStaticMesh> InboundCraneBridge(
        TEXT("/Game/LineBoss/IndustrialKit/MaterialHandling/BridgeCrane/InboundInstalledCrane/Candidate_v001/SM_CA_MW_InboundCrane_MovingBridge_v001.SM_CA_MW_InboundCrane_MovingBridge_v001"));
    static ConstructorHelpers::FObjectFinder<UStaticMesh> InboundCraneTrolley(
        TEXT("/Game/LineBoss/IndustrialKit/MaterialHandling/BridgeCrane/SM_LB_Crane_Trolley_v001.SM_LB_Crane_Trolley_v001"));
    static ConstructorHelpers::FObjectFinder<UStaticMesh> InboundCraneHoist(
        TEXT("/Game/LineBoss/IndustrialKit/MaterialHandling/BridgeCrane/SM_LB_Crane_HoistBlock_v001.SM_LB_Crane_HoistBlock_v001"));
    static ConstructorHelpers::FObjectFinder<UStaticMesh> InboundCHook(
        TEXT("/Game/LineBoss/IndustrialKit/MaterialHandling/BridgeCrane/PoweredCHook/Candidate_v035/SM_LB_Crane_PoweredCHook_Candidate_v035.SM_LB_Crane_PoweredCHook_Candidate_v035"));
    if (InboundCraneRunway.Succeeded()) InboundCraneRunwayVisual->SetStaticMesh(InboundCraneRunway.Object);
    if (InboundCraneBridge.Succeeded()) InboundCraneBridgeVisual->SetStaticMesh(InboundCraneBridge.Object);
    if (InboundCraneTrolley.Succeeded()) InboundCraneTrolleyVisual->SetStaticMesh(InboundCraneTrolley.Object);
    if (InboundCraneHoist.Succeeded()) InboundCraneHoistVisual->SetStaticMesh(InboundCraneHoist.Object);
    if (InboundCHook.Succeeded()) InboundCHookVisual->SetStaticMesh(InboundCHook.Object);
    static ConstructorHelpers::FObjectFinder<UStaticMesh> PR002Station(TEXT("/Game/LineBoss/Candidates/PressShop/PR002/RuntimeGLB_v922/SM_CA_MW_PR002_ScannerWeighCell_v922/StaticMeshes/SM_CA_MW_PR002_ScannerWeighCell_v922.SM_CA_MW_PR002_ScannerWeighCell_v922"));
    static ConstructorHelpers::FObjectFinder<UStaticMesh> PR002Payload(TEXT("/Game/LineBoss/Candidates/PressShop/PR002/RuntimeGLB_v922/SM_CA_MW_PR002_RemovableWrappedCoil_v922/StaticMeshes/SM_CA_MW_PR002_RemovableWrappedCoil_v922.SM_CA_MW_PR002_RemovableWrappedCoil_v922"));
    if (PR002Station.Succeeded()) PR002StationVisual->SetStaticMesh(PR002Station.Object);
    if (PR002Payload.Succeeded()) PR002PayloadVisual->SetStaticMesh(PR002Payload.Object);
    static ConstructorHelpers::FObjectFinder<UStaticMesh> PR005DetailedHMI(TEXT("/Game/LineBoss/Stations/Press/PR005/Candidate_v001/ArtDerivatives/HMI_v001/SM_CA_Factory_OperatorHMI_MeshyMaster_v632/StaticMeshes/SM_CA_MW_PR005_dHMI_Meshy_v001.SM_CA_MW_PR005_dHMI_Meshy_v001"));
    if (PR005DetailedHMI.Succeeded())
    {
        PR005DetailedHMIMesh = PR005DetailedHMI.Object;
        PR005DetailedHMIVisual->SetStaticMesh(PR005DetailedHMIMesh);
    }
}

bool ALBFactoryBuildMachine::Configure(FName InMachineId, ELBFactoryBuildMachineType InMachineType)
{
    if (InMachineId.IsNone()) return false;
    bUsingNativeAGVArrivalPresentation = false;
    Tags.Remove(FName(TEXT("LB.Inbound.Source.NativeAGVArrival")));
    if (MachineLivery) MachineLivery->ClearMaterialBindings();
    MachineId = InMachineId;
    MachineType = InMachineType;
    ResolvedCoilPreparationStationCount = 0;
    ApprovedVisual->SetStaticMesh(nullptr);
    if (MachineType == ELBFactoryBuildMachineType::InboundDeliveryDock)
        ApprovedVisual->SetStaticMesh(ApprovedInboundLorryMesh);
    else if (MachineType == ELBFactoryBuildMachineType::DepackagingRobot)
        ApprovedVisual->SetStaticMesh(ApprovedPR004CompleteCellMesh);
    InputPort->PortId = FName(*FString::Printf(TEXT("%s-IN"), *MachineId.ToString()));
    OutputPort->PortId = FName(*FString::Printf(TEXT("%s-OUT"), *MachineId.ToString()));
    InputPort->MaximumAutomaticLinkDistanceCm = 2500.0f;
    OutputPort->MaximumAutomaticLinkDistanceCm = 2500.0f;
    InputPort->MaximumConnections = 1;
    OutputPort->MaximumConnections = 4;
    ApprovedVisual->SetVisibility(false);
    ApprovedVisual->SetCollisionEnabled(ECollisionEnabled::NoCollision);
    MachineBase->SetVisibility(true);
    MachineBase->SetCollisionEnabled(ECollisionEnabled::QueryAndPhysics);
    MachineBody->SetVisibility(true);
    MachineBody->SetCollisionEnabled(ECollisionEnabled::QueryAndPhysics);
    ApprovedVisual->SetRelativeTransform(FTransform::Identity);
    for (UStaticMeshComponent* Stand : TrailerStandVisuals)
    {
        Stand->SetVisibility(false);
        Stand->SetCollisionEnabled(ECollisionEnabled::NoCollision);
    }
    for (UStaticMeshComponent* Coil : TrailerCoilVisuals)
    {
        Coil->SetVisibility(false);
        Coil->SetCollisionEnabled(ECollisionEnabled::NoCollision);
    }
    for (UStaticMeshComponent* CranePart : {InboundCraneRunwayVisual.Get(), InboundCraneBridgeVisual.Get(),
        InboundCraneTrolleyVisual.Get(), InboundCraneHoistVisual.Get(), InboundCHookVisual.Get(),
        ReceivingSaddleRailAVisual.Get(), ReceivingSaddleRailBVisual.Get()})
    {
        CranePart->SetVisibility(false);
        CranePart->SetCollisionEnabled(ECollisionEnabled::NoCollision);
        CranePart->SetRelativeTransform(FTransform::Identity);
    }
    PR002StationVisual->SetVisibility(false); PR002PayloadVisual->SetVisibility(false);
    PR002StationVisual->SetCollisionEnabled(ECollisionEnabled::NoCollision);
    PR002PayloadVisual->SetCollisionEnabled(ECollisionEnabled::NoCollision);
    PR002StationVisual->SetRelativeTransform(FTransform::Identity); PR002PayloadVisual->SetRelativeTransform(FTransform::Identity);
    PR005DetailedHMIVisual->SetVisibility(false);
    PR005DetailedHMIVisual->SetCollisionEnabled(ECollisionEnabled::NoCollision);
    PR005DetailedHMIVisual->SetGenerateOverlapEvents(false);
    PR005DetailedHMIVisual->SetCanEverAffectNavigation(false);
    PR005DetailedHMIVisual->SetRelativeTransform(FTransform::Identity);
    for (UStaticMeshComponent* Part : PlaceholderParts)
    {
        Part->SetVisibility(false);
        Part->SetCollisionEnabled(ECollisionEnabled::NoCollision);
        Part->SetRelativeTransform(FTransform::Identity);
        Part->EmptyOverrideMaterials();
        Part->SetStaticMesh(nullptr);
    }
    const auto SetPlaceholderPart = [this](const int32 Index, UStaticMesh* Mesh,
        const FVector& Location, const FVector& SizeCm, UMaterialInterface* Material,
        const FRotator& Rotation = FRotator::ZeroRotator)
    {
        if (!PlaceholderParts.IsValidIndex(Index) || !Mesh) return;
        UStaticMeshComponent* Part = PlaceholderParts[Index];
        Part->SetStaticMesh(Mesh);
        Part->SetRelativeLocation(Location);
        Part->SetRelativeRotation(Rotation);
        // Both engine primitives have a 100 cm authored envelope on each axis.
        Part->SetRelativeScale3D(SizeCm / 100.0f);
        if (Material) Part->SetMaterial(0, Material);
        Part->SetVisibility(true);
        if (MachineLivery && GenericLiveryMaterialParent)
        {
            if (Material == PlaceholderGreenMaterial)
                MachineLivery->RegisterGenericMaterialBinding(Part, 0,
                    ELBMachineLiveryRole::PrimaryBody, GenericLiveryMaterialParent);
            else if (Material == PlaceholderCharcoalMaterial)
                MachineLivery->RegisterGenericMaterialBinding(Part, 0,
                    ELBMachineLiveryRole::SecondaryFrame, GenericLiveryMaterialParent);
        }
    };
    FVector ProtectedEnvelopeHalfExtent = FVector::ZeroVector;
    FVector ProtectedEnvelopeRelativeCentre = FVector::ZeroVector;

    switch (MachineType)
    {
    case ELBFactoryBuildMachineType::InboundDeliveryDock:
        RequiredAutomaticProcessSteps = 1;
        // The approved loaded lorry is 16.50 x 2.55 x 4.00 m. The gameplay flow axis is local Y,
        // so rotate the source's local-X vehicle length by 90 degrees rather than squashing it.
        MachineHalfExtent = FVector(160.0f, 850.0f, 225.0f);
        // The actor pivot is the lorry/crane floor datum. Asset-bound audit v979 proves the
        // complete installed package spans local X -602.5..362.5, Y -944.5..825 and
        // Z 0..797 cm. Reserve that package, plus 25 cm lateral placement clearance.
        PlacementRootHeightCm = 0.0f;
        ProtectedEnvelopeRelativeCentre = FVector(64.0f, -59.75f, 398.5f);
        ProtectedEnvelopeHalfExtent = FVector(716.0f, 909.75f, 398.5f);
        if (ApprovedVisual->GetStaticMesh())
        {
            ApprovedVisual->SetVisibility(true);
            ApprovedVisual->SetRelativeRotation(FRotator(0.0f, 90.0f, 0.0f));
            MachineBase->SetVisibility(false);
            MachineBody->SetVisibility(false);
            // Four independent wrapped coils on two adjustable support rails each. These are
            // deliberately separate from the lorry so a delivery can unload them one by one.
            constexpr float CoilPitchCm = 300.0f;
            constexpr float FirstCoilY = -250.0f;
            for (int32 CoilIndex = 0; CoilIndex < TrailerCoilVisuals.Num(); ++CoilIndex)
            {
                const float CoilY = FirstCoilY + CoilIndex * CoilPitchCm;
                // The repaired coil pivot is at its bottom face, not at its centre. Seat that
                // face directly on the measured 132.8 cm top of the two trailer support rails.
                TrailerCoilVisuals[CoilIndex]->SetRelativeLocation(FVector(0.0f, CoilY, 132.8f));
                // The wrapped-coil source axis is local Y. Rotate it onto trailer local X so
                // the bore faces both trailer sides and the side-entry handler ram can pass
                // through it. A zero yaw incorrectly points every bore along the lorry.
                TrailerCoilVisuals[CoilIndex]->SetRelativeRotation(FRotator(0.0f, 90.0f, 0.0f));
                TrailerCoilVisuals[CoilIndex]->SetVisibility(true);
                for (int32 Rail = 0; Rail < 2; ++Rail)
                {
                    const int32 StandIndex = CoilIndex * 2 + Rail;
                    TrailerStandVisuals[StandIndex]->SetRelativeLocation(
                        FVector(0.0f, CoilY + (Rail == 0 ? -60.0f : 60.0f), 111.0f));
                    TrailerStandVisuals[StandIndex]->SetRelativeRotation(FRotator::ZeroRotator);
                    TrailerStandVisuals[StandIndex]->SetVisibility(true);
                }
            }
            // Driverless 30 t coil handler. The approved Meshy chassis keeps its detailed
            // fixed mast; the separately built lift/backrest/bore-ram mesh is the only
            // visible lifting component. Legacy crane-named slots remain only for save
            // compatibility and as invisible transform followers.
            InboundCraneRunwayVisual->SetStaticMesh(ApprovedCoilHandlerBodyMesh);
            InboundCraneBridgeVisual->SetStaticMesh(nullptr);
            InboundCraneTrolleyVisual->SetStaticMesh(nullptr);
            InboundCraneHoistVisual->SetStaticMesh(nullptr);
            InboundCHookVisual->SetStaticMesh(ApprovedCoilHandlerLiftMesh);
            constexpr float HandlerStartX = 400.0f;
            const FTransform HandlerStart(FRotator::ZeroRotator,
                // FBX bound audit v999: body minimum Z is -69.5503 cm.
                FVector(HandlerStartX, FirstCoilY, 69.5503f), FVector::OneVector);
            InboundCraneRunwayVisual->SetRelativeTransform(HandlerStart);
            InboundCraneBridgeVisual->SetRelativeTransform(HandlerStart);
            InboundCraneTrolleyVisual->SetRelativeTransform(HandlerStart);
            InboundCraneHoistVisual->SetRelativeTransform(HandlerStart);
            InboundCHookVisual->SetRelativeTransform(HandlerStart);
            ReceivingSaddleRailAVisual->SetStaticMesh(ApprovedCoilSaddleMesh);
            // Keep the receiving saddle on the handler side of the trailer. The chassis
            // remains outside the trailer envelope; only the telescopic bore ram crosses
            // the deck to retrieve a coil and then retracts onto this saddle.
            ReceivingSaddleRailAVisual->SetRelativeLocation(FVector(400.0f, 0.0f, 0.0f));
            ReceivingSaddleRailBVisual->SetStaticMesh(nullptr);
            for (UStaticMeshComponent* HandlerPart : {InboundCraneRunwayVisual.Get(), InboundCraneBridgeVisual.Get(),
                InboundCraneTrolleyVisual.Get(), InboundCraneHoistVisual.Get(), InboundCHookVisual.Get(),
                ReceivingSaddleRailAVisual.Get()})
                HandlerPart->SetVisibility(HandlerPart->GetStaticMesh() != nullptr);
        }
        InputPort->ProcessStage = OutputPort->ProcessStage = LBFactoryProcessStage::InboundUnloading;
        InputPort->MaterialClass = OutputPort->MaterialClass = ELBFactoryMaterialClass::Coil;
        InputPort->TransportKind = OutputPort->TransportKind = ELBFactoryTransportKind::AGVHandoff;
        break;
    case ELBFactoryBuildMachineType::DepackagingRobot:
        RequiredAutomaticProcessSteps = 2;
        MachineHalfExtent = FVector(330.0f, 230.0f, 100.0f);
        MachineBase->SetVisibility(false);
        MachineBody->SetVisibility(false);
        if (ApprovedVisual->GetStaticMesh())
        {
            ApprovedVisual->SetRelativeLocation(FVector(0.0f, 0.0f, -MachineHalfExtent.Z));
            ApprovedVisual->SetVisibility(true);
        }
        InputPort->ProcessStage = OutputPort->ProcessStage = LBFactoryProcessStage::DepackAndIdentify;
        InputPort->MaterialClass = OutputPort->MaterialClass = ELBFactoryMaterialClass::Coil;
        InputPort->TransportKind = OutputPort->TransportKind = ELBFactoryTransportKind::AGVHandoff;
        break;
    case ELBFactoryBuildMachineType::CoilWeighInspectionCell:
        RequiredAutomaticProcessSteps = 2;
        MachineHalfExtent = FVector(190.0f, 195.0f, 182.0f);
        InputPort->ProcessStage = OutputPort->ProcessStage = LBFactoryProcessStage::PR002WeighInspection;
        InputPort->MaterialClass = OutputPort->MaterialClass = ELBFactoryMaterialClass::Coil;
        InputPort->TransportKind = OutputPort->TransportKind = ELBFactoryTransportKind::AGVHandoff;
        if (PR002StationVisual->GetStaticMesh())
        {
            MachineBase->SetVisibility(false); MachineBody->SetVisibility(false);
            PR002StationVisual->SetRelativeLocation(FVector(0,0,-MachineHalfExtent.Z));
            PR002PayloadVisual->SetRelativeLocation(FVector(0,0,-MachineHalfExtent.Z));
            PR002StationVisual->SetVisibility(true); PR002PayloadVisual->SetVisibility(false);
        }
        break;
    case ELBFactoryBuildMachineType::DecoilerFeeder:
    {
        // Save-compatible complete coil-preparation package. The historical enum name is
        // retained so v984 machine records and links continue to restore unchanged.
        RequiredAutomaticProcessSteps = 6;
        MachineHalfExtent = FVector(750.0f, 1300.0f, 350.0f);
        MachineBase->SetVisibility(false);
        MachineBody->SetVisibility(false);
        // Fallbacks occupy only their station's reserved range. This guarantees that one
        // broken donor never creates a half-real/half-proxy station and never suppresses a
        // healthy neighbouring station.
        const auto BuildStationFallback = [&SetPlaceholderPart, this](
            const ECoilPreparationStation Station, const int32 BaseIndex)
        {
            switch (Station)
            {
            case ECoilPreparationStation::PR005:
                SetPlaceholderPart(BaseIndex + 0, PlaceholderCubeMesh, FVector(-300,-1050,-40), FVector(70,70,620), PlaceholderGreenMaterial);
                SetPlaceholderPart(BaseIndex + 1, PlaceholderCubeMesh, FVector(300,-1050,-40), FVector(70,70,620), PlaceholderGreenMaterial);
                SetPlaceholderPart(BaseIndex + 2, PlaceholderCubeMesh, FVector(0,-1050,235), FVector(670,70,70), PlaceholderGreenMaterial);
                SetPlaceholderPart(BaseIndex + 3, PlaceholderCylinderMesh, FVector(0,-1050,-35), FVector(330,330,190), PlaceholderSteelMaterial, FRotator(90,0,0));
                SetPlaceholderPart(BaseIndex + 4, PlaceholderCylinderMesh, FVector(0,-1050,-35), FVector(90,90,250), PlaceholderCharcoalMaterial, FRotator(90,0,0));
                break;
            case ECoilPreparationStation::PR006:
                SetPlaceholderPart(BaseIndex, PlaceholderCubeMesh, FVector(0,-650,-210), FVector(620,500,45), PlaceholderCharcoalMaterial);
                for (int32 Roller = 0; Roller < 5; ++Roller)
                    SetPlaceholderPart(BaseIndex + 1 + Roller, PlaceholderCylinderMesh,
                        FVector(0,-810 + Roller * 80,-165), FVector(45,45,560), PlaceholderSteelMaterial, FRotator(0,90,0));
                break;
            case ECoilPreparationStation::PR007:
                SetPlaceholderPart(BaseIndex + 0, PlaceholderCubeMesh, FVector(-360,-260,-70), FVector(55,360,420), PlaceholderGreenMaterial);
                SetPlaceholderPart(BaseIndex + 1, PlaceholderCubeMesh, FVector(360,-260,-70), FVector(55,360,420), PlaceholderGreenMaterial);
                SetPlaceholderPart(BaseIndex + 2, PlaceholderCubeMesh, FVector(0,-260,115), FVector(775,360,55), PlaceholderGreenMaterial);
                SetPlaceholderPart(BaseIndex + 3, PlaceholderCubeMesh, FVector(0,-260,-205), FVector(650,360,45), PlaceholderCharcoalMaterial);
                break;
            case ECoilPreparationStation::PR008:
                SetPlaceholderPart(BaseIndex + 0, PlaceholderCubeMesh, FVector(-390,170,-65), FVector(65,65,500), PlaceholderGreenMaterial);
                SetPlaceholderPart(BaseIndex + 1, PlaceholderCubeMesh, FVector(390,170,-65), FVector(65,65,500), PlaceholderGreenMaterial);
                SetPlaceholderPart(BaseIndex + 2, PlaceholderCubeMesh, FVector(0,170,150), FVector(845,65,70), PlaceholderGreenMaterial);
                SetPlaceholderPart(BaseIndex + 3, PlaceholderCubeMesh, FVector(0,170,-65), FVector(560,120,70), PlaceholderSteelMaterial);
                for (int32 Roller = 0; Roller < 3; ++Roller)
                    SetPlaceholderPart(BaseIndex + 4 + Roller, PlaceholderCylinderMesh,
                        FVector(0,20 + Roller * 95,-165), FVector(45,45,580), PlaceholderSteelMaterial, FRotator(0,90,0));
                break;
            case ECoilPreparationStation::PR009:
                for (int32 Corner = 0; Corner < 4; ++Corner)
                {
                    const float X = Corner < 2 ? -330.0f : 330.0f;
                    const float Y = (Corner % 2) == 0 ? 480.0f : 790.0f;
                    SetPlaceholderPart(BaseIndex + Corner, PlaceholderCubeMesh, FVector(X,Y,-55),
                        FVector(55,55,520), PlaceholderGreenMaterial);
                }
                SetPlaceholderPart(BaseIndex + 4, PlaceholderCubeMesh, FVector(0,635,175), FVector(715,365,55), PlaceholderGreenMaterial);
                SetPlaceholderPart(BaseIndex + 5, PlaceholderCubeMesh, FVector(0,635,-170), FVector(560,310,45), PlaceholderSteelMaterial);
                break;
            case ECoilPreparationStation::PR010:
                SetPlaceholderPart(BaseIndex + 0, PlaceholderCubeMesh, FVector(-225,1050,-215), FVector(370,420,35), PlaceholderCharcoalMaterial);
                SetPlaceholderPart(BaseIndex + 1, PlaceholderCubeMesh, FVector(225,1050,-215), FVector(370,420,35), PlaceholderCharcoalMaterial);
                SetPlaceholderPart(BaseIndex + 2, PlaceholderCubeMesh, FVector(-420,1050,-135), FVector(45,420,190), PlaceholderYellowMaterial);
                SetPlaceholderPart(BaseIndex + 3, PlaceholderCubeMesh, FVector(420,1050,-135), FVector(45,420,190), PlaceholderYellowMaterial);
                SetPlaceholderPart(BaseIndex + 4, PlaceholderCubeMesh, FVector(0,1260,-130), FVector(180,70,280), PlaceholderSteelMaterial);
                SetPlaceholderPart(BaseIndex + 5, PlaceholderCubeMesh, FVector(-560,-250,-120), FVector(130,150,390), PlaceholderSteelMaterial);
                SetPlaceholderPart(BaseIndex + 6, PlaceholderCubeMesh, FVector(560,650,-155), FVector(80,640,280), PlaceholderYellowMaterial);
                break;
            }
        };

        for (const FCoilPreparationStationLayout& Layout : GCoilPreparationStationLayouts)
        {
            TArray<UStaticMesh*> ResolvedMeshes;
            ResolvedMeshes.Reserve(Layout.AssetCount);
            FString FailureDetail;
            for (int32 Offset = 0; Offset < Layout.AssetCount; ++Offset)
            {
                const int32 AssetIndex = Layout.FirstAssetIndex + Offset;
                if (!CoilPreparationVisualAssets.IsValidIndex(AssetIndex)
                    || !PlaceholderParts.IsValidIndex(AssetIndex)
                    || GCoilPreparationVisualSpecs[AssetIndex].Station != Layout.Station)
                {
                    FailureDetail = TEXT("native station asset contract is inconsistent");
                    break;
                }
                UStaticMesh* Mesh = CoilPreparationVisualAssets[AssetIndex].LoadSynchronous();
                if (!Mesh)
                {
                    FailureDetail = CoilPreparationVisualAssets[AssetIndex].ToSoftObjectPath().ToString();
                    break;
                }
                ResolvedMeshes.Add(Mesh);
            }

            TMap<FName, UMaterialInterface*> ResolvedPalette;
            const uint8 LayoutBit = StationBit(Layout.Station);
            if (FailureDetail.IsEmpty())
            {
                for (const FCoilPreparationPaletteSpec& Palette : GCoilPreparationPaletteSpecs)
                {
                    if ((Palette.StationMask & LayoutBit) == 0) continue;
                    const FName Key(Palette.Key);
                    const TSoftObjectPtr<UMaterialInterface>* Reference = CoilPreparationPaletteMaterials.Find(Key);
                    UMaterialInterface* Material = Reference ? Reference->LoadSynchronous() : nullptr;
                    if (!Material)
                    {
                        FailureDetail = Reference ? Reference->ToSoftObjectPath().ToString() : FString(Palette.AssetPath);
                        break;
                    }
                    ResolvedPalette.Add(Key, Material);
                }
            }

            if (!FailureDetail.IsEmpty())
            {
                UE_LOG(LogTemp, Warning,
                    TEXT("Coil preparation %s art failed closed; using station-local primitive fallback. Missing: %s"),
                    Layout.StationId, *FailureDetail);
                BuildStationFallback(Layout.Station, Layout.FirstAssetIndex);
                continue;
            }

            const FQuat PackageRotation = FRotator(0.0f, Layout.PackageYawDegrees, 0.0f).Quaternion();
            for (int32 Offset = 0; Offset < Layout.AssetCount; ++Offset)
            {
                const int32 AssetIndex = Layout.FirstAssetIndex + Offset;
                const FCoilPreparationVisualSpec& Spec = GCoilPreparationVisualSpecs[AssetIndex];
                UStaticMeshComponent* Part = PlaceholderParts[AssetIndex];
                UStaticMesh* Mesh = ResolvedMeshes[Offset];
                Part->SetStaticMesh(Mesh);
                Part->SetRelativeLocation(Layout.PackageLocationCm
                    + PackageRotation.RotateVector(Spec.StationLocationCm * Layout.UniformScale));
                Part->SetRelativeRotation(PackageRotation);
                // Uniform compactization preserves the donor geometry and station proportions.
                Part->SetRelativeScale3D(FVector(Layout.UniformScale));
                Part->SetVisibility(true);

                // PR005 static groups carry their audited authored materials. PR006-PR010
                // were accepted with component-level overrides, which are reproduced here.
                if (Layout.Station != ECoilPreparationStation::PR005)
                {
                    const TArray<FStaticMaterial>& StaticMaterials = Mesh->GetStaticMaterials();
                    for (int32 SlotIndex = 0; SlotIndex < FMath::Max(1, StaticMaterials.Num()); ++SlotIndex)
                    {
                        const FName SlotName = StaticMaterials.IsValidIndex(SlotIndex)
                            ? StaticMaterials[SlotIndex].MaterialSlotName : NAME_None;
                        FName MaterialKey = SelectCoilPreparationMaterialKey(Layout.Station,
                            CoilPreparationVisualAssets[AssetIndex].ToSoftObjectPath().ToString(),
                            SlotName, SlotIndex);
                        UMaterialInterface* Material = ResolvedPalette.FindRef(MaterialKey);
                        if (!Material)
                        {
                            MaterialKey = Layout.Station == ECoilPreparationStation::PR006 ? FName(TEXT("PR006.Frame"))
                                : Layout.Station == ECoilPreparationStation::PR007 ? FName(TEXT("PR007.Frame"))
                                : Layout.Station == ECoilPreparationStation::PR008 ? FName(TEXT("PR008.Frame"))
                                : Layout.Station == ECoilPreparationStation::PR009 ? FName(TEXT("PR009.Frame"))
                                : FName(TEXT("PR010.Frame"));
                            Material = ResolvedPalette.FindRef(MaterialKey);
                        }
                        if (Material) Part->SetMaterial(SlotIndex, Material);
                    }
                }
            }
            ++ResolvedCoilPreparationStationCount;
        }
        InputPort->ProcessStage = OutputPort->ProcessStage = LBFactoryProcessStage::DecoilerThreader;
        InputPort->MaterialClass = ELBFactoryMaterialClass::Coil;
        InputPort->TransportKind = ELBFactoryTransportKind::AGVHandoff;
        OutputPort->MaterialClass = ELBFactoryMaterialClass::Blank;
        OutputPort->TransportKind = ELBFactoryTransportKind::RollerConveyor;
        // Preserve the detailed Meshy master exactly as imported. This is a separate
        // visual-only component at the approved PR005 operator datum; gameplay still
        // owns the existing interaction target and status beacon.
        if (PR005DetailedHMIMesh)
        {
            PR005DetailedHMIVisual->SetRelativeLocation(FVector(-115.68f, -856.0f, -350.0f));
            PR005DetailedHMIVisual->SetRelativeRotation(FRotator(0.0f, 180.0f, 0.0f));
            PR005DetailedHMIVisual->SetRelativeScale3D(FVector(0.48f));
            PR005DetailedHMIVisual->SetVisibility(true);
        }
        // Multiple parallel PR004 robots may merge into one preparation package.
        InputPort->MaximumConnections = 4;
        break;
    }
    case ELBFactoryBuildMachineType::PressTrain:
        RequiredAutomaticProcessSteps = 1;
        // Match the compact complete train's asymmetric S01-to-S07 envelope. The actor
        // root is its infeed datum, so the preview centre is 28.92 m downstream.
        MachineHalfExtent = FVector(750.0f, 3642.0f, 475.0f);
        PlacementRootHeightCm = 0.0f;
        ProtectedEnvelopeRelativeCentre = FVector(0.0f, 2892.0f, 475.0f);
        ProtectedEnvelopeHalfExtent = MachineHalfExtent;
        InputPort->ProcessStage = OutputPort->ProcessStage = LBFactoryProcessStage::PressTrain;
        InputPort->MaterialClass = ELBFactoryMaterialClass::Blank;
        InputPort->TransportKind = ELBFactoryTransportKind::RollerConveyor;
        OutputPort->MaterialClass = ELBFactoryMaterialClass::FormedPanel;
        OutputPort->TransportKind = ELBFactoryTransportKind::PanelTransfer;
        break;
    case ELBFactoryBuildMachineType::InspectionCell:
        RequiredAutomaticProcessSteps = 2;
        MachineHalfExtent = FVector(600.0f, 500.0f, 300.0f);
        MachineBase->SetVisibility(false);
        MachineBody->SetVisibility(false);
        // Panel inspection portal with a continuous transfer bed; it never blocks the
        // formed-panel path and reads distinctly from the press/unload portal.
        SetPlaceholderPart(0, PlaceholderCubeMesh, FVector(-430,0,-35), FVector(65,65,530), PlaceholderGreenMaterial);
        SetPlaceholderPart(1, PlaceholderCubeMesh, FVector(430,0,-35), FVector(65,65,530), PlaceholderGreenMaterial);
        SetPlaceholderPart(2, PlaceholderCubeMesh, FVector(0,0,200), FVector(925,65,65), PlaceholderGreenMaterial);
        SetPlaceholderPart(3, PlaceholderCubeMesh, FVector(0,0,-205), FVector(760,760,45), PlaceholderCharcoalMaterial);
        for (int32 Roller = 0; Roller < 7; ++Roller)
        {
            SetPlaceholderPart(4 + Roller, PlaceholderCylinderMesh,
                FVector(0,-300 + Roller * 100,-165), FVector(55,55,720), PlaceholderSteelMaterial,
                FRotator(0,90,0));
        }
        SetPlaceholderPart(11, PlaceholderCubeMesh, FVector(-310,0,95), FVector(80,380,55), PlaceholderYellowMaterial,
            FRotator(0,0,-18));
        SetPlaceholderPart(12, PlaceholderCubeMesh, FVector(310,0,95), FVector(80,380,55), PlaceholderYellowMaterial,
            FRotator(0,0,18));
        SetPlaceholderPart(13, PlaceholderCubeMesh, FVector(485,250,-135), FVector(115,125,330), PlaceholderSteelMaterial);
        InputPort->ProcessStage = OutputPort->ProcessStage = LBFactoryProcessStage::Inspection;
        InputPort->MaterialClass = ELBFactoryMaterialClass::FormedPanel;
        InputPort->TransportKind = ELBFactoryTransportKind::PanelTransfer;
        OutputPort->MaterialClass = ELBFactoryMaterialClass::InspectedPanel;
        OutputPort->TransportKind = ELBFactoryTransportKind::PanelTransfer;
        // The common inspection cell accepts formed panels from Press Trains A-D.
        InputPort->MaximumConnections = 4;
        break;
    case ELBFactoryBuildMachineType::OutboundPanelDock:
        RequiredAutomaticProcessSteps = 1;
        MachineHalfExtent = FVector(450.0f, 350.0f, 250.0f);
        MachineBase->SetVisibility(false);
        MachineBody->SetVisibility(false);
        // Outbound stillage dock: low AGV-accessible deck, locator rails and four corner
        // posts. Empty geometry stays readable until finished panels arrive.
        SetPlaceholderPart(0, PlaceholderCubeMesh, FVector(0,0,-220), FVector(760,560,45), PlaceholderCharcoalMaterial);
        SetPlaceholderPart(1, PlaceholderCubeMesh, FVector(-300,0,-170), FVector(35,500,55), PlaceholderYellowMaterial);
        SetPlaceholderPart(2, PlaceholderCubeMesh, FVector(300,0,-170), FVector(35,500,55), PlaceholderYellowMaterial);
        for (int32 Corner = 0; Corner < 4; ++Corner)
        {
            const float X = Corner < 2 ? -325.0f : 325.0f;
            const float Y = (Corner % 2) == 0 ? -225.0f : 225.0f;
            SetPlaceholderPart(3 + Corner, PlaceholderCubeMesh, FVector(X,Y,-45),
                FVector(45,45,360), PlaceholderGreenMaterial);
        }
        SetPlaceholderPart(7, PlaceholderCubeMesh, FVector(365,0,-40), FVector(70,500,55), PlaceholderGreenMaterial);
        SetPlaceholderPart(8, PlaceholderCubeMesh, FVector(-365,0,-40), FVector(70,500,55), PlaceholderGreenMaterial);
        SetPlaceholderPart(9, PlaceholderCubeMesh, FVector(0,285,-120), FVector(210,70,260), PlaceholderSteelMaterial);
        InputPort->ProcessStage = OutputPort->ProcessStage = LBFactoryProcessStage::WeldShopIntake;
        InputPort->MaterialClass = OutputPort->MaterialClass = ELBFactoryMaterialClass::Stillage;
        InputPort->TransportKind = OutputPort->TransportKind = ELBFactoryTransportKind::AGVHandoff;
        InputPort->MaximumConnections = 4;
        break;
    default:
        return false;
    }

    if (ProtectedEnvelopeHalfExtent.IsNearlyZero())
    {
        PlacementRootHeightCm = MachineType == ELBFactoryBuildMachineType::PressTrain
            ? 0.0f : MachineHalfExtent.Z;
        ProtectedEnvelopeHalfExtent = MachineHalfExtent;
    }
    ProtectedEnvelope->SetRelativeLocation(ProtectedEnvelopeRelativeCentre);
    ProtectedEnvelope->SetBoxExtent(ProtectedEnvelopeHalfExtent);
    RebuildFloorMarkings();
    StatusBeacon->SetRelativeLocation(FVector(
        ProtectedEnvelopeRelativeCentre.X + ProtectedEnvelopeHalfExtent.X - 45.0f,
        ProtectedEnvelopeRelativeCentre.Y - ProtectedEnvelopeHalfExtent.Y + 45.0f,
        // The 0.75-scale stack rises 23.25 cm above its mount. Keep every visible
        // lamp inside the same protected player-placement envelope as its machine.
        ProtectedEnvelopeRelativeCentre.Z + ProtectedEnvelopeHalfExtent.Z - 24.0f));
    MachineBase->SetRelativeLocation(FVector(0.0f, 0.0f, -MachineHalfExtent.Z + 15.0f));
    MachineBase->SetRelativeScale3D(FVector(
        MachineHalfExtent.X / 50.0f, MachineHalfExtent.Y / 50.0f, 0.3f));
    MachineBody->SetRelativeLocation(FVector(0.0f, 0.0f, -MachineHalfExtent.Z * 0.2f));
    MachineBody->SetRelativeScale3D(FVector(
        MachineHalfExtent.X / 65.0f, MachineHalfExtent.Y / 65.0f, MachineHalfExtent.Z / 65.0f));
    if (MachineLivery && GenericLiveryMaterialParent)
    {
        if (MachineBody->IsVisible())
            MachineLivery->RegisterGenericMaterialBinding(MachineBody, 0,
                ELBMachineLiveryRole::PrimaryBody, GenericLiveryMaterialParent);
        if (MachineBase->IsVisible())
            MachineLivery->RegisterGenericMaterialBinding(MachineBase, 0,
                ELBMachineLiveryRole::SecondaryFrame, GenericLiveryMaterialParent);
    }

    // This actor reuses a large pool of alternative presentation components. A hidden
    // component must never retain physical authority from an earlier Configure call:
    // otherwise an invisible lorry crane, payload, or provisional module can block an
    // AGV/FLT route after the same actor is reconfigured as another machine type.
    const auto SyncPresentationCollision = [](UStaticMeshComponent* Visual)
    {
        if (!Visual) return;
        const bool bActive = Visual->IsVisible() && Visual->GetStaticMesh() != nullptr;
        Visual->SetCollisionEnabled(bActive
            ? ECollisionEnabled::QueryAndPhysics : ECollisionEnabled::NoCollision);
    };
    SyncPresentationCollision(MachineBase);
    SyncPresentationCollision(MachineBody);
    SyncPresentationCollision(ApprovedVisual);
    for (UStaticMeshComponent* Stand : TrailerStandVisuals) SyncPresentationCollision(Stand);
    for (UStaticMeshComponent* Coil : TrailerCoilVisuals) SyncPresentationCollision(Coil);
    for (UStaticMeshComponent* CranePart : {InboundCraneRunwayVisual.Get(), InboundCraneBridgeVisual.Get(),
        InboundCraneTrolleyVisual.Get(), InboundCraneHoistVisual.Get(), InboundCHookVisual.Get(),
        ReceivingSaddleRailAVisual.Get(), ReceivingSaddleRailBVisual.Get()})
        SyncPresentationCollision(CranePart);
    SyncPresentationCollision(PR002StationVisual);
    SyncPresentationCollision(PR002PayloadVisual);
    // This is add-on art only. Do not allow a detailed imported console to acquire
    // collision authority when the generic presentation sync runs.
    PR005DetailedHMIVisual->SetCollisionEnabled(ECollisionEnabled::NoCollision);
    PR005DetailedHMIVisual->SetGenerateOverlapEvents(false);
    PR005DetailedHMIVisual->SetCanEverAffectNavigation(false);
    for (UStaticMeshComponent* Part : PlaceholderParts)
    {
        if (MachineType == ELBFactoryBuildMachineType::DecoilerFeeder)
        {
            // The compact preparation package can contain dozens of imported donor
            // meshes. Keep both real modules and station-local fallbacks presentation-
            // only so their source collision cannot block generated AGV routes.
            Part->SetCollisionEnabled(ECollisionEnabled::NoCollision);
            Part->SetGenerateOverlapEvents(false);
            Part->SetCanEverAffectNavigation(false);
        }
        else
        {
            SyncPresentationCollision(Part);
        }
    }

    InputPort->SetRelativeLocation(FVector(0.0f, -MachineHalfExtent.Y, 0.0f));
    OutputPort->SetRelativeLocation(FVector(0.0f, MachineHalfExtent.Y, 0.0f));
    Tags.AddUnique(TEXT("LB.FactoryBuilder.Machine"));
    Tags.AddUnique(FName(*FString::Printf(TEXT("LB.Machine.%s"), *MachineId.ToString())));
#if WITH_EDITOR
    SetActorLabel(MachineId.ToString());
#endif
    UpdateStatusBeacon();
    return true;
}

void ALBFactoryBuildMachine::RebuildFloorMarkings()
{
    if (!FloorMarkings || !ProtectedEnvelope) return;
    FloorMarkings->ClearMarkings();
    const FVector Centre3D = GetProtectedEnvelopeRelativeCentre();
    const FVector Extent3D = GetProtectedEnvelopeHalfExtent();
    if (Extent3D.X <= 0.0f || Extent3D.Y <= 0.0f || Extent3D.Z <= 0.0f) return;

    const FVector2D Centre(Centre3D.X, Centre3D.Y);
    const FVector2D Extent(Extent3D.X, Extent3D.Y);
    const float FloorZ = Centre3D.Z - Extent3D.Z;
    const bool bKeepClearDock = MachineType == ELBFactoryBuildMachineType::InboundDeliveryDock
        || MachineType == ELBFactoryBuildMachineType::OutboundPanelDock;

    if (bKeepClearDock)
    {
        // Unloading and stillage handoff areas are exclusive vehicle work zones. Red
        // hatch is clipped to the validated placement envelope, below the yellow edge.
        const FVector2D HatchExtent(FMath::Max(20.0f, Extent.X - 28.0f),
            FMath::Max(20.0f, Extent.Y - 28.0f));
        FloorMarkings->AddDiagonalHatching(Centre, HatchExtent, FloorZ + 0.15f,
            18.0f, 78.0f, ELBFactoryFloorMarkingSemantic::KeepClearHatch, 0.8f);

        // Two dashed blue wheel-lane guides keep AGV/FLT approaches readable through
        // the red bay without creating any collision or navigation surface.
        const float GuideOffsetX = FMath::Min(Extent.X * 0.55f, 240.0f);
        const FVector2D LaneStartA(Centre.X - GuideOffsetX, Centre.Y - Extent.Y + 35.0f);
        const FVector2D LaneEndA(Centre.X - GuideOffsetX, Centre.Y + Extent.Y - 35.0f);
        const FVector2D LaneStartB(Centre.X + GuideOffsetX, Centre.Y - Extent.Y + 35.0f);
        const FVector2D LaneEndB(Centre.X + GuideOffsetX, Centre.Y + Extent.Y - 35.0f);
        FloorMarkings->AddDashedLine(LaneStartA, LaneEndA, FloorZ + 0.35f,
            10.0f, 65.0f, 50.0f, ELBFactoryFloorMarkingSemantic::VehicleLane, 0.8f);
        FloorMarkings->AddDashedLine(LaneStartB, LaneEndB, FloorZ + 0.35f,
            10.0f, 65.0f, 50.0f, ELBFactoryFloorMarkingSemantic::VehicleLane, 0.8f);
    }

    // Yellow is reserved for the service/exclusion envelope on every machine. The
    // hierarchy stays consistent regardless of which replaceable 3D asset is fitted.
    FloorMarkings->AddRectangleOutline(Centre, Extent, FloorZ + 0.45f, 18.0f,
        ELBFactoryFloorMarkingSemantic::ServiceEnvelope, 1.0f);
}

FVector ALBFactoryBuildMachine::GetProtectedEnvelopeHalfExtent() const
{
    return ProtectedEnvelope ? ProtectedEnvelope->GetUnscaledBoxExtent() : MachineHalfExtent;
}

FVector ALBFactoryBuildMachine::GetProtectedEnvelopeRelativeCentre() const
{
    return ProtectedEnvelope ? ProtectedEnvelope->GetRelativeLocation() : FVector::ZeroVector;
}

void ALBFactoryBuildMachine::SetInboundCoilHandlerRearSteerAngleDegrees(
    const float AngleDegrees)
{
    // The front/load axle is deliberately invariant. Only the rear binding root yaws.
    if (InboundCoilHandlerFixedFrontAxleRoot)
        InboundCoilHandlerFixedFrontAxleRoot->SetRelativeRotation(FRotator::ZeroRotator);
    if (InboundCoilHandlerRearSteeringRoot)
        InboundCoilHandlerRearSteeringRoot->SetRelativeRotation(
            FRotator(0.0f, AngleDegrees, 0.0f));
}

int32 ALBFactoryBuildMachine::GetVisibleTrailerCoilCount() const
{
    int32 Count = 0;
    for (const UStaticMeshComponent* Coil : TrailerCoilVisuals)
    {
        if (Coil && Coil->IsVisible()) ++Count;
    }
    return Count;
}

bool ALBFactoryBuildMachine::ConfigureNativeAGVArrivalPresentation(FString& OutReason)
{
    OutReason.Reset();
    if (MachineType != ELBFactoryBuildMachineType::InboundDeliveryDock)
    {
        OutReason = TEXT("NATIVE AGV ARRIVAL PRESENTATION REQUIRES AN INBOUND DELIVERY DOCK");
        return false;
    }
    if (!InputUnitIds.IsEmpty() || !OutputUnitIds.IsEmpty() || !CompletedUnitIds.IsEmpty())
    {
        OutReason = TEXT("NATIVE AGV ARRIVAL PRESENTATION CANNOT CHANGE WHILE THE DOCK OWNS WIP");
        return false;
    }

    ApprovedVisual->SetVisibility(false);
    ApprovedVisual->SetCollisionEnabled(ECollisionEnabled::NoCollision);
    for (UStaticMeshComponent* Stand : TrailerStandVisuals)
    {
        if (!Stand) continue;
        Stand->SetVisibility(false);
        Stand->SetCollisionEnabled(ECollisionEnabled::NoCollision);
    }
    for (UStaticMeshComponent* Coil : TrailerCoilVisuals)
    {
        if (!Coil) continue;
        Coil->SetVisibility(false);
        Coil->SetCollisionEnabled(ECollisionEnabled::NoCollision);
    }
    for (UStaticMeshComponent* LegacyHandlerPart : {
        InboundCraneRunwayVisual.Get(), InboundCraneBridgeVisual.Get(),
        InboundCraneTrolleyVisual.Get(), InboundCraneHoistVisual.Get(),
        InboundCHookVisual.Get(), ReceivingSaddleRailAVisual.Get(),
        ReceivingSaddleRailBVisual.Get()})
    {
        if (!LegacyHandlerPart) continue;
        LegacyHandlerPart->SetVisibility(false);
        LegacyHandlerPart->SetCollisionEnabled(ECollisionEnabled::NoCollision);
    }
    // Keep only the low native dock datum and the existing authored keep-clear paint.
    // The separately owned ALBCoilAGVController supplies the visible vehicle and load.
    MachineBase->SetVisibility(true);
    MachineBase->SetCollisionEnabled(ECollisionEnabled::QueryAndPhysics);
    MachineBody->SetVisibility(false);
    MachineBody->SetCollisionEnabled(ECollisionEnabled::NoCollision);
    bUsingNativeAGVArrivalPresentation = true;
    Tags.AddUnique(TEXT("LB.Inbound.Source.NativeAGVArrival"));
    OutReason = TEXT("NATIVE AGV ARRIVAL DOCK READY; LEGACY LORRY AND COIL HANDLER HIDDEN");
    return true;
}

int32 ALBFactoryBuildMachine::GetVisiblePlaceholderPartCount() const
{
    int32 Count = 0;
    for (const UStaticMeshComponent* Part : PlaceholderParts)
    {
        if (Part && Part->IsVisible() && Part->GetStaticMesh()
            && Part->GetStaticMesh()->GetPathName().StartsWith(TEXT("/Engine/BasicShapes/")))
            ++Count;
    }
    return Count;
}

int32 ALBFactoryBuildMachine::GetVisibleCoilPreparationArtPartCount() const
{
    int32 Count = 0;
    for (const UStaticMeshComponent* Part : PlaceholderParts)
    {
        if (Part && Part->IsVisible() && Part->GetStaticMesh()
            && !Part->GetStaticMesh()->GetPathName().StartsWith(TEXT("/Engine/BasicShapes/")))
            ++Count;
    }
    return Count;
}

bool ALBFactoryBuildMachine::SetTrailerCoilVisible(const int32 CoilIndex, const bool bVisible)
{
    if (MachineType != ELBFactoryBuildMachineType::InboundDeliveryDock
        || !TrailerCoilVisuals.IsValidIndex(CoilIndex)) return false;
    UStaticMeshComponent* Coil = TrailerCoilVisuals[CoilIndex];
    Coil->SetVisibility(bVisible);
    Coil->SetCollisionEnabled(bVisible && Coil->GetStaticMesh()
        ? ECollisionEnabled::QueryAndPhysics : ECollisionEnabled::NoCollision);
    return true;
}

UStaticMeshComponent* ALBFactoryBuildMachine::GetTrailerCoilComponent(const int32 CoilIndex) const
{
    return TrailerCoilVisuals.IsValidIndex(CoilIndex) ? TrailerCoilVisuals[CoilIndex].Get() : nullptr;
}

FVector ALBFactoryBuildMachine::GetReceivingSaddleLoadPoint() const
{
    // The v997 V-block contact band is approximately 41 cm above its floor datum; the
    // repaired wrapped-coil pivot is its lowest bound and seats directly at that band.
    return GetActorTransform().TransformPosition(FVector(400.0f, 0.0f, 41.0f));
}

FLBFactoryBuildMachineSaveState ALBFactoryBuildMachine::CaptureSaveState() const
{
    FLBFactoryBuildMachineSaveState State;
    State.MachineId = MachineId;
    State.MachineType = MachineType;
    State.WorldTransform = GetActorTransform();
    State.InputUnitIds = InputUnitIds;
    State.OutputUnitIds = OutputUnitIds;
    State.CompletedUnitIds = CompletedUnitIds;
    State.NextOutputSerial = NextOutputSerial;
    State.MaximumInputBuffer = MaximumInputBuffer;
    State.MaximumOutputBuffer = MaximumOutputBuffer;
    State.OperatingState = OperatingState;
    State.OperatingReason = OperatingReason;
    State.RequiredAutomaticProcessSteps = RequiredAutomaticProcessSteps;
    State.CompletedAutomaticProcessSteps = CompletedAutomaticProcessSteps;
    return State;
}

bool ALBFactoryBuildMachine::RestoreSaveState(const FLBFactoryBuildMachineSaveState& State)
{
    if ((State.Version != 1 && State.Version != 2) || State.MachineId.IsNone() || !State.WorldTransform.IsValid()) return false;
    if (State.NextOutputSerial < 1) return false;
    if (State.Version >= 2 && (State.MaximumInputBuffer < 1 || State.MaximumOutputBuffer < 1
        || State.RequiredAutomaticProcessSteps < 1 || State.CompletedAutomaticProcessSteps < 0
        || State.CompletedAutomaticProcessSteps >= State.RequiredAutomaticProcessSteps)) return false;
    TSet<FName> UniqueIds;
    for (const TArray<FName>* Units : {&State.InputUnitIds, &State.OutputUnitIds, &State.CompletedUnitIds})
        for (const FName UnitId : *Units)
            if (UnitId.IsNone() || UniqueIds.Contains(UnitId)) return false; else UniqueIds.Add(UnitId);
    SetActorTransform(State.WorldTransform);
    if (!Configure(State.MachineId, State.MachineType)) return false;
    InputUnitIds = State.InputUnitIds;
    OutputUnitIds = State.OutputUnitIds;
    CompletedUnitIds = State.CompletedUnitIds;
    NextOutputSerial = State.NextOutputSerial;
    if (State.Version >= 2)
    {
        MaximumInputBuffer = State.MaximumInputBuffer;
        MaximumOutputBuffer = State.MaximumOutputBuffer;
        OperatingState = State.OperatingState;
        OperatingReason = State.OperatingReason;
        RequiredAutomaticProcessSteps = State.RequiredAutomaticProcessSteps;
        CompletedAutomaticProcessSteps = State.CompletedAutomaticProcessSteps;
        UpdateStatusBeacon();
    }
    else
    {
        MaximumInputBuffer = 32;
        MaximumOutputBuffer = 32;
        RefreshOperatingState();
    }
    return true;
}

bool ALBFactoryBuildMachine::ConfigureGameplayBuffers(
    const int32 InMaximumInputBuffer, const int32 InMaximumOutputBuffer)
{
    if (InMaximumInputBuffer < 1 || InMaximumOutputBuffer < 1
        || InputUnitIds.Num() > InMaximumInputBuffer || OutputUnitIds.Num() > InMaximumOutputBuffer)
        return false;
    MaximumInputBuffer = InMaximumInputBuffer;
    MaximumOutputBuffer = InMaximumOutputBuffer;
    RefreshOperatingState();
    return true;
}

bool ALBFactoryBuildMachine::ConfigureGameplayProcessSteps(const int32 InRequiredSteps)
{
    if (InRequiredSteps < 1 || CompletedAutomaticProcessSteps >= InRequiredSteps) return false;
    RequiredAutomaticProcessSteps = InRequiredSteps;
    RefreshOperatingState();
    return true;
}

bool ALBFactoryBuildMachine::AdvanceAutomaticProcess(FName& OutUnitId, bool& bOutCompleted)
{
    OutUnitId = NAME_None;
    bOutCompleted = false;
    if (MachineType == ELBFactoryBuildMachineType::InboundDeliveryDock || InputUnitIds.IsEmpty()
        || (MachineType != ELBFactoryBuildMachineType::OutboundPanelDock
            && OutputUnitIds.Num() >= MaximumOutputBuffer))
    {
        RefreshOperatingState();
        return false;
    }
    ++CompletedAutomaticProcessSteps;
    if (CompletedAutomaticProcessSteps < RequiredAutomaticProcessSteps)
    {
        OperatingState = ELBFactoryMachineOperatingState::Processing;
        OperatingReason = FString::Printf(TEXT("PROCESSING %d/%d"),
            CompletedAutomaticProcessSteps, RequiredAutomaticProcessSteps);
        UpdateStatusBeacon();
        return true;
    }
    CompletedAutomaticProcessSteps = 0;
    bOutCompleted = ProcessNextUnit(OutUnitId);
    return bOutCompleted;
}

void ALBFactoryBuildMachine::RefreshOperatingState()
{
    if (MachineType == ELBFactoryBuildMachineType::InboundDeliveryDock)
    {
        OperatingState = OutputUnitIds.Num() >= MaximumOutputBuffer
            ? ELBFactoryMachineOperatingState::Blocked : ELBFactoryMachineOperatingState::Idle;
        OperatingReason = OperatingState == ELBFactoryMachineOperatingState::Blocked
            ? TEXT("INBOUND OUTPUT BUFFER FULL") : TEXT("AWAITING DELIVERY");
        UpdateStatusBeacon();
        return;
    }
    if (InputUnitIds.IsEmpty())
    {
        CompletedAutomaticProcessSteps = 0;
        OperatingState = ELBFactoryMachineOperatingState::Starved;
        OperatingReason = TEXT("AWAITING MATERIAL");
    }
    else if (MachineType != ELBFactoryBuildMachineType::OutboundPanelDock
        && OutputUnitIds.Num() >= MaximumOutputBuffer)
    {
        OperatingState = ELBFactoryMachineOperatingState::Blocked;
        OperatingReason = TEXT("OUTPUT BUFFER FULL");
    }
    else
    {
        OperatingState = ELBFactoryMachineOperatingState::Ready;
        OperatingReason = TEXT("READY");
    }
    UpdateStatusBeacon();
}

void ALBFactoryBuildMachine::UpdateStatusBeacon()
{
    if (!StatusBeacon) return;
    switch (OperatingState)
    {
    case ELBFactoryMachineOperatingState::Ready:
        StatusBeacon->SetStatus(ELBStatusBeaconState::Ready);
        break;
    case ELBFactoryMachineOperatingState::Processing:
        StatusBeacon->SetStatus(ELBStatusBeaconState::Running);
        break;
    case ELBFactoryMachineOperatingState::Idle:
        StatusBeacon->SetStatus(ELBStatusBeaconState::Idle);
        break;
    case ELBFactoryMachineOperatingState::Starved:
        StatusBeacon->SetStatus(ELBStatusBeaconState::Waiting);
        break;
    case ELBFactoryMachineOperatingState::Blocked:
        StatusBeacon->SetStatus(ELBStatusBeaconState::Stopped);
        break;
    case ELBFactoryMachineOperatingState::Fault:
    default:
        StatusBeacon->SetStatus(ELBStatusBeaconState::Fault);
        break;
    }
}

bool ALBFactoryBuildMachine::ReceiveDeliveredUnit(const FName UnitId)
{
    if (MachineType != ELBFactoryBuildMachineType::InboundDeliveryDock || UnitId.IsNone()
        || OutputUnitIds.Num() >= MaximumOutputBuffer || InputUnitIds.Contains(UnitId) || OutputUnitIds.Contains(UnitId) || CompletedUnitIds.Contains(UnitId)) return false;
    OutputUnitIds.Add(UnitId);
    RefreshOperatingState();
    return true;
}

bool ALBFactoryBuildMachine::IsPR002PayloadVisible() const
{
    return MachineType == ELBFactoryBuildMachineType::CoilWeighInspectionCell
        && IsValid(PR002PayloadVisual) && PR002PayloadVisual->IsVisible();
}

bool ALBFactoryBuildMachine::SetPR002PayloadVisible(const bool bVisible)
{
    if (MachineType != ELBFactoryBuildMachineType::CoilWeighInspectionCell
        || !IsValid(PR002PayloadVisual) || !PR002PayloadVisual->GetStaticMesh()) return false;
    PR002PayloadVisual->SetVisibility(bVisible, true);
    PR002PayloadVisual->SetCollisionEnabled(bVisible
        ? ECollisionEnabled::QueryAndPhysics : ECollisionEnabled::NoCollision);
    return true;
}

bool ALBFactoryBuildMachine::AcceptInputUnit(const FName UnitId)
{
    if (MachineType == ELBFactoryBuildMachineType::InboundDeliveryDock || UnitId.IsNone()
        || InputUnitIds.Num() >= MaximumInputBuffer || InputUnitIds.Contains(UnitId)
        || OutputUnitIds.Contains(UnitId) || CompletedUnitIds.Contains(UnitId)) return false;
    InputUnitIds.Add(UnitId);
    if (MachineType == ELBFactoryBuildMachineType::CoilWeighInspectionCell)
        SetPR002PayloadVisible(true);
    RefreshOperatingState();
    return true;
}

bool ALBFactoryBuildMachine::ProcessNextUnit(FName& OutUnitId)
{
    OutUnitId = NAME_None;
    if (MachineType == ELBFactoryBuildMachineType::InboundDeliveryDock || InputUnitIds.IsEmpty()
        || (MachineType != ELBFactoryBuildMachineType::OutboundPanelDock
            && OutputUnitIds.Num() >= MaximumOutputBuffer))
    {
        RefreshOperatingState();
        return false;
    }
    OperatingState = ELBFactoryMachineOperatingState::Processing;
    OperatingReason = TEXT("PROCESSING");
    const FName InputId = InputUnitIds[0];
    InputUnitIds.RemoveAt(0);
    if (MachineType == ELBFactoryBuildMachineType::CoilWeighInspectionCell)
        SetPR002PayloadVisible(false);
    if (MachineType == ELBFactoryBuildMachineType::OutboundPanelDock)
    {
        CompletedUnitIds.Add(InputId);
        OutUnitId = InputId;
        RefreshOperatingState();
        return true;
    }
    if (MachineType == ELBFactoryBuildMachineType::DecoilerFeeder)
        OutUnitId = FName(*FString::Printf(TEXT("BLANK-%06d"), NextOutputSerial++));
    else
        OutUnitId = InputId;
    OutputUnitIds.Add(OutUnitId);
    CompletedAutomaticProcessSteps = 0;
    RefreshOperatingState();
    return true;
}

bool ALBFactoryBuildMachine::ReleaseOutputUnit(FName& OutUnitId)
{
    OutUnitId = NAME_None;
    if (OutputUnitIds.IsEmpty()) return false;
    OutUnitId = OutputUnitIds[0];
    OutputUnitIds.RemoveAt(0);
    RefreshOperatingState();
    return true;
}
